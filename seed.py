"""
seed.py – Importiere Bunkr-Album-URLs aus einer Textdatei in die Datenbank.

Verwendung:
    python seed.py urls.txt

urls.txt: Eine URL pro Zeile, z.B.:
    https://bunkr.si/a/abc123
    https://bunkr.si/a/xyz456
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from database import init_db, upsert_album
from scraper import scrape_many


def load_urls(path: str) -> list[str]:
    with open(path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return lines


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    url_file = sys.argv[1]
    if not os.path.exists(url_file):
        print(f"Datei nicht gefunden: {url_file}")
        sys.exit(1)

    urls = load_urls(url_file)
    print(f"Gefunden: {len(urls)} URLs")

    init_db()
    albums = scrape_many(urls, delay=1.5)

    saved = 0
    for album in albums:
        upsert_album(album)
        saved += 1

    print(f"\n✓ Fertig! {saved}/{len(urls)} Alben gespeichert.")


if __name__ == "__main__":
    main()
