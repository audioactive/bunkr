import httpx
from bs4 import BeautifulSoup
import time
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

BUNKR_DOMAINS = [
    "bunkr.si", "bunkr.ru", "bunkr.is", "bunkr.black",
    "bunkr.cat", "bunkr.ac", "bunkr.media",
]


def normalize_url(url: str) -> str:
    """Ensure URL uses a valid bunkr domain."""
    for domain in BUNKR_DOMAINS:
        if domain in url:
            return url
    return url


def scrape_album(url: str) -> dict | None:
    url = normalize_url(url)
    try:
        r = httpx.get(url, headers=HEADERS, timeout=15, follow_redirects=True)
        if r.status_code != 200:
            print(f"  ✗ HTTP {r.status_code}: {url}")
            return None

        soup = BeautifulSoup(r.text, "html.parser")

        # Title
        title_tag = soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else "Unknown"

        # Thumbnail (og:image meta tag)
        og_image = soup.find("meta", property="og:image")
        thumbnail = og_image["content"] if og_image else None

        # File count — look for file links or a count element
        file_links = soup.select("a[href*='/f/']")
        file_count = len(file_links)

        # Try to get count from page text (e.g. "42 files")
        count_match = re.search(r"(\d+)\s+files?", r.text, re.IGNORECASE)
        if count_match:
            file_count = int(count_match.group(1))

        # Size info
        size_match = re.search(r"([\d.]+\s*[KMGT]?B)", r.text)
        size = size_match.group(1) if size_match else None

        return {
            "url": str(r.url),
            "title": title,
            "file_count": file_count,
            "thumbnail": thumbnail,
            "size": size,
        }
    except httpx.TimeoutException:
        print(f"  ✗ Timeout: {url}")
        return None
    except Exception as e:
        print(f"  ✗ Fehler bei {url}: {e}")
        return None


def scrape_many(urls: list[str], delay: float = 1.5) -> list[dict]:
    """Scrape multiple album URLs with a polite delay."""
    results = []
    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] Scraping: {url}")
        album = scrape_album(url)
        if album:
            results.append(album)
            print(f"  ✓ {album['title']!r} — {album['file_count']} Dateien")
        time.sleep(delay)
    return results
