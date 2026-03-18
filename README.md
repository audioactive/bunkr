# 🔍 Bunkr Search

Eine lokale Suchmaschine für Bunkr-Alben – gebaut mit Python (FastAPI) und Vanilla JS.

## Projektstruktur

```
bunkr-search/
├── backend/
│   ├── main.py          ← FastAPI Server + API Endpunkte
│   ├── scraper.py       ← Bunkr-Scraper (httpx + BeautifulSoup)
│   ├── database.py      ← SQLite + FTS5 Volltext-Suche
│   └── requirements.txt
├── frontend/
│   └── index.html       ← Such-UI (Dark Mode, Pagination, Modal)
├── seed.py              ← Import-Skript für URL-Listen
└── urls.txt             ← Deine Album-URLs (eine pro Zeile)
```

## Schnellstart

### 1. Abhängigkeiten installieren

```bash
cd backend
pip install -r requirements.txt
```

### 2. URLs eintragen

Trage deine Bunkr-Album-URLs in `urls.txt` ein (eine pro Zeile):

```
https://bunkr.si/a/ALBUMID1
https://bunkr.si/a/ALBUMID2
```

### 3. Datenbank befüllen

```bash
python seed.py urls.txt
```

### 4. Server starten

```bash
cd backend
uvicorn main:app --reload --port 8000
```

Öffne dann: **http://localhost:8000**

---

## API-Endpunkte

| Methode | URL | Beschreibung |
|---------|-----|--------------|
| `GET`   | `/api/search?q=...&sort=newest&limit=20&offset=0` | Alben suchen |
| `GET`   | `/api/stats` | Statistiken |
| `POST`  | `/api/albums` | Ein Album hinzufügen |
| `POST`  | `/api/albums/bulk` | Mehrere URLs auf einmal |
| `DELETE`| `/api/albums?url=...` | Album löschen |

### Beispiel: Album per API hinzufügen

```bash
curl -X POST http://localhost:8000/api/albums \
  -H "Content-Type: application/json" \
  -d '{"url": "https://bunkr.si/a/abc123"}'
```

### Beispiel: Suche

```bash
curl "http://localhost:8000/api/search?q=beach&sort=most_files&limit=10"
```

---

## Deployment auf Railway (kostenfrei)

1. Konto erstellen auf [railway.app](https://railway.app)
2. Neues Projekt → "Deploy from GitHub Repo"
3. Start-Command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
4. Fertig! Railway gibt dir eine öffentliche URL.

## Deployment auf Render (kostenfrei)

1. Konto auf [render.com](https://render.com)
2. New → Web Service → GitHub verbinden
3. Build Command: `pip install -r backend/requirements.txt`
4. Start Command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
