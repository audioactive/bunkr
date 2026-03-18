from fastapi import FastAPI, Query, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os

from database import init_db, search_albums, count_albums, insert_album, upsert_album, delete_album, get_stats
from scraper import scrape_album, scrape_many

app = FastAPI(title="Bunkr Search API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

# ─── Models ───────────────────────────────────────────────────────────────────

class AddAlbumRequest(BaseModel):
    url: str

class AddManyRequest(BaseModel):
    urls: list[str]

# ─── API Routes ───────────────────────────────────────────────────────────────

@app.get("/api/search")
def search(
    q: str = Query(default="", description="Suchbegriff"),
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    sort: str = Query(default="newest", pattern="^(newest|oldest|most_files|az)$"),
):
    results = search_albums(q, limit, offset, sort)
    total = count_albums(q)
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "results": results,
    }


@app.get("/api/stats")
def stats():
    return get_stats()


@app.post("/api/albums")
async def add_album(req: AddAlbumRequest, background_tasks: BackgroundTasks):
    """Scrape and add a single album URL."""
    def _scrape_and_save():
        album = scrape_album(req.url)
        if album:
            upsert_album(album)

    background_tasks.add_task(_scrape_and_save)
    return {"message": "Album wird im Hintergrund gescraped.", "url": req.url}


@app.post("/api/albums/bulk")
async def add_many(req: AddManyRequest, background_tasks: BackgroundTasks):
    """Scrape and add multiple album URLs in the background."""
    if len(req.urls) > 500:
        raise HTTPException(status_code=400, detail="Maximal 500 URLs auf einmal.")

    def _bulk():
        albums = scrape_many(req.urls, delay=1.5)
        for album in albums:
            upsert_album(album)
        print(f"Bulk-Import fertig: {len(albums)}/{len(req.urls)} erfolgreich.")

    background_tasks.add_task(_bulk)
    return {"message": f"{len(req.urls)} URLs werden gescraped.", "urls": req.urls}


@app.delete("/api/albums")
def remove_album(url: str = Query(...)):
    delete_album(url)
    return {"message": "Gelöscht.", "url": url}


# ─── Serve Frontend ───────────────────────────────────────────────────────────

frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
