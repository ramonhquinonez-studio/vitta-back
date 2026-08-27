"""Syncs the platform-curated ("Biblioteca nutricional") article library from
MedlinePlus's free, keyless Web service (NIH / National Library of Medicine)
into the `content_articles` collection, upserted with `owner_id: None` — the
same platform marker `content_library` already uses (see
`seed_content_library.py`). Idempotent: re-running upserts every article by a
stable `_id` derived from its MedlinePlus URL slug, so it never duplicates.

No API key, no signup, no cost — MedlinePlus's Web service ("does not require
registration or licensing") is queried directly. Rate limit: max 85
requests/minute per IP; this script makes one request per synced group, far
under that. Attribution required by their terms ("please indicate that the
information is from MedlinePlus.gov"; no logo use, no implied endorsement) —
every synced article's body ends with a "Fuente: MedlinePlus.gov" line.

Requires nothing in `.env`. Invoke manually:
    python -m app.scripts.sync_medlineplus_content_library
"""
import asyncio
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

import requests

from app.core.config import settings
from app.db.mongo import close_mongo_connection, connect_to_mongo, get_db

_BASE_URL = "https://wsearch.nlm.nih.gov/ws/query"

# MedlinePlus "groupName" categories to pull (each confirmed live, and
# sampled for actual on-topic relevance, before adding it here — broader
# clinical groups like "Sangre, corazón y circulación", "Sistema digestivo",
# and "Embarazo" were tried and rejected: mostly general disease/clinical
# content, not nutrition-relevant, and would dilute the library).
_GROUPS = {
    "Alimentos y nutrición": "🥗",
    "Bienestar y estilo de vida": "💪",
    "Diabetes mellitus": "🩸",
    "Aptitud física y ejercicio": "🏃",
}


def _strip_tags(value: str) -> str:
    return re.sub(r"<[^>]+>", "", value or "").strip()


class _SummaryParser(HTMLParser):
    """Extracts plain paragraph text and bullet-list items from a
    MedlinePlus `FullSummary` HTML blob (observed shape: a run of `<p>`
    tags, sometimes one `<ul><li>...</li></ul>` block)."""

    def __init__(self):
        super().__init__()
        self.paragraphs: list[str] = []
        self.bullets: list[str] = []
        self._buffer: list[str] = []
        self._in_li = False

    def handle_starttag(self, tag, attrs):
        if tag == "li":
            self._in_li = True
            self._buffer = []

    def handle_endtag(self, tag):
        if tag == "p":
            text = "".join(self._buffer).strip()
            self._buffer = []
            if text:
                self.paragraphs.append(text)
        elif tag == "li":
            self._in_li = False
            text = "".join(self._buffer).strip()
            if text:
                self.bullets.append(text)
            self._buffer = []

    def handle_data(self, data):
        self._buffer.append(data)


def _parse_section(summary_html: str) -> dict | None:
    parser = _SummaryParser()
    parser.feed(summary_html or "")
    if not parser.paragraphs:
        return None
    text = "\n\n".join(parser.paragraphs) + "\n\nFuente: MedlinePlus.gov"
    return {"title": "", "text": text, "bullets": parser.bullets or None}


def _slug_from_url(url: str) -> str:
    return url.rstrip("/").rsplit("/", 1)[-1].replace(".html", "")


def _estimate_read_time(paragraph_text: str) -> str:
    minutes = max(1, round(len(paragraph_text.split()) / 200))
    return f"{minutes} min"


def _fetch_group(group_name: str, retmax: int = 100) -> list[dict]:
    response = requests.get(
        _BASE_URL,
        params={"db": "healthTopicsSpanish", "term": f'group:"{group_name}"', "retmax": retmax},
        timeout=30,
    )
    response.raise_for_status()
    root = ET.fromstring(response.content)
    documents = []
    for doc in root.findall(".//document"):
        fields = {c.get("name"): "".join(c.itertext()) for c in doc.findall("content")}
        documents.append({
            "url": doc.get("url", ""),
            "title": fields.get("title", ""),
            "summary_html": fields.get("FullSummary", ""),
        })
    return documents


async def sync() -> int:
    db = get_db()
    synced = 0
    order = 100  # after the 5 hand-curated seed articles (order 1-5)
    for group_name, emoji in _GROUPS.items():
        for raw in _fetch_group(group_name):
            title = _strip_tags(raw["title"])
            if not title or not raw["url"]:
                continue
            section = _parse_section(raw["summary_html"])
            if section is None:
                continue
            description = section["text"][:200].rsplit(" ", 1)[0] + "…"
            doc = {
                "_id": f"medlineplus-{_slug_from_url(raw['url'])}",
                "owner_id": None,
                "category": group_name,
                "title": title,
                "description": description,
                "read_time": _estimate_read_time(section["text"]),
                "emoji": emoji,
                "order": order,
                "sections": [section],
                "video_url": None,
                "source_url": raw["url"],
            }
            await db.content_articles.update_one({"_id": doc["_id"]}, {"$set": doc}, upsert=True)
            synced += 1
            order += 1
    return synced


async def main() -> None:
    await connect_to_mongo(settings.MONGO_URI, settings.MONGO_DB)
    try:
        count = await sync()
        print(f"Synced {count} platform articles from MedlinePlus.")
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())
