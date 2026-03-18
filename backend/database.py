import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", "albums.db")


def get_con() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    return con


def init_db():
    with get_con() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS albums (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                url        TEXT    UNIQUE NOT NULL,
                title      TEXT    NOT NULL DEFAULT '',
                file_count INTEGER NOT NULL DEFAULT 0,
                thumbnail  TEXT,
                size       TEXT,
                added_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Full-text search index
        con.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS albums_fts
            USING fts5(title, content='albums', content_rowid='id')
        """)
        # Keep FTS in sync
        con.execute("""
            CREATE TRIGGER IF NOT EXISTS albums_ai AFTER INSERT ON albums BEGIN
                INSERT INTO albums_fts(rowid, title) VALUES (new.id, new.title);
            END
        """)
        con.execute("""
            CREATE TRIGGER IF NOT EXISTS albums_ad AFTER DELETE ON albums BEGIN
                INSERT INTO albums_fts(albums_fts, rowid, title)
                VALUES ('delete', old.id, old.title);
            END
        """)
        con.execute("""
            CREATE TRIGGER IF NOT EXISTS albums_au AFTER UPDATE ON albums BEGIN
                INSERT INTO albums_fts(albums_fts, rowid, title)
                VALUES ('delete', old.id, old.title);
                INSERT INTO albums_fts(rowid, title) VALUES (new.id, new.title);
            END
        """)
        con.commit()


def insert_album(album: dict) -> bool:
    """Insert an album. Returns True if inserted, False if it already existed."""
    try:
        with get_con() as con:
            con.execute("""
                INSERT OR IGNORE INTO albums (url, title, file_count, thumbnail, size)
                VALUES (:url, :title, :file_count, :thumbnail, :size)
            """, album)
            con.commit()
            return con.execute("SELECT changes()").fetchone()[0] == 1
    except Exception as e:
        print(f"DB insert error: {e}")
        return False


def upsert_album(album: dict):
    """Insert or update an album."""
    with get_con() as con:
        con.execute("""
            INSERT INTO albums (url, title, file_count, thumbnail, size)
            VALUES (:url, :title, :file_count, :thumbnail, :size)
            ON CONFLICT(url) DO UPDATE SET
                title      = excluded.title,
                file_count = excluded.file_count,
                thumbnail  = excluded.thumbnail,
                size       = excluded.size
        """, album)
        con.commit()


def search_albums(
    query: str = "",
    limit: int = 20,
    offset: int = 0,
    sort: str = "newest",
) -> list[dict]:
    sort_map = {
        "newest":    "added_at DESC",
        "oldest":    "added_at ASC",
        "most_files": "file_count DESC",
        "az":        "title ASC",
    }
    order = sort_map.get(sort, "added_at DESC")

    with get_con() as con:
        if query.strip():
            # Use FTS for fast full-text search
            rows = con.execute(f"""
                SELECT a.*
                FROM albums a
                JOIN albums_fts f ON f.rowid = a.id
                WHERE albums_fts MATCH ?
                ORDER BY {order}
                LIMIT ? OFFSET ?
            """, (query + "*", limit, offset)).fetchall()
        else:
            rows = con.execute(f"""
                SELECT * FROM albums
                ORDER BY {order}
                LIMIT ? OFFSET ?
            """, (limit, offset)).fetchall()
    return [dict(r) for r in rows]


def count_albums(query: str = "") -> int:
    with get_con() as con:
        if query.strip():
            row = con.execute("""
                SELECT COUNT(*) FROM albums a
                JOIN albums_fts f ON f.rowid = a.id
                WHERE albums_fts MATCH ?
            """, (query + "*",)).fetchone()
        else:
            row = con.execute("SELECT COUNT(*) FROM albums").fetchone()
    return row[0]


def delete_album(url: str):
    with get_con() as con:
        con.execute("DELETE FROM albums WHERE url = ?", (url,))
        con.commit()


def get_stats() -> dict:
    with get_con() as con:
        total = con.execute("SELECT COUNT(*) FROM albums").fetchone()[0]
        total_files = con.execute("SELECT SUM(file_count) FROM albums").fetchone()[0] or 0
        latest = con.execute(
            "SELECT title, added_at FROM albums ORDER BY added_at DESC LIMIT 1"
        ).fetchone()
    return {
        "total_albums": total,
        "total_files": total_files,
        "latest": dict(latest) if latest else None,
    }
