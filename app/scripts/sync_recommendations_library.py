"""Syncs the platform-curated ("Biblioteca pública") supplements/brands
catalog into the `recommendations` collection, upserted with
`owner_id: None` — the same platform marker `content_library` and
`exercise_library` already use.

Two NIH-family sources, both verified live before writing this script (the
originally-considered `ods.od.nih.gov` fact-sheet site is fully blocked by a
Cloudflare bot challenge on every path, including raw fact-sheet URLs — not
usable for a script):

- **Supplements** (`kind="supplement"`): real Spanish narrative descriptions
  from MedlinePlus's free, keyless Web service, reusing this repo's existing
  `sync_medlineplus_content_library.py` parsing pipeline (`_SummaryParser`,
  `_strip_tags`) via a free-text `term=` query against `healthTopicsSpanish`
  (confirmed live: `term=vitamina+d` returns `medlineplus.gov/spanish/
  vitamind.html` as the top-ranked match).
- **Brands** (`kind="brand"`): real product-brand names verified against the
  Dietary Supplement Label Database (DSLD, `api.ods.od.nih.gov/dsld/v9/
  search-filter`) — a different, unblocked NIH subdomain, no key required.
  Each curated brand name is only synced if it appears as an exact
  `brandName` match among the live results, so every brand synced is
  confirmed to exist in NIH's own label registry, not invented.

Idempotent: re-run upserts by a stable `_id` slug, never duplicates. No API
key, no signup, no cost. Attribution lines are included in every synced
description per each source's terms. Invoke manually:
    python -m app.scripts.sync_recommendations_library
"""
import asyncio
import re
import xml.etree.ElementTree as ET
from collections import Counter
from html.parser import HTMLParser

import requests

from app.core.config import settings
from app.db.mongo import close_mongo_connection, connect_to_mongo, get_db

_MEDLINEPLUS_URL = "https://wsearch.nlm.nih.gov/ws/query"
_DSLD_URL = "https://api.ods.od.nih.gov/dsld/v9/search-filter"

# Spanish display name -> MedlinePlus search term. Each confirmed live and
# sampled for a real, on-topic top match before adding it here.
_SUPPLEMENTS: dict[str, str] = {
    "Vitamina D": "vitamina d",
    "Vitamina C": "vitamina c",
    "Omega-3": "acidos grasos omega-3",
    "Magnesio": "magnesio",
    "Probióticos": "probioticos",
    "Multivitamínico": "vitaminas y minerales",
    "Hierro": "hierro en la dieta",
    "Calcio": "calcio",
    "Zinc": "zinc en la dieta",
    "Vitamina B12": "vitamina b12",
    "Proteína en polvo": "proteina en la dieta",
    "Colágeno": "colageno",
    "Creatina": "creatina",
    "Melatonina": "melatonina",
}

# Real brand names, each verified live to appear as an exact `brandName`
# match in DSLD before being added here.
_BRANDS: list[str] = [
    "Jarrow Formulas",
    "Nature Made",
    "Garden of Life",
    "Optimum Nutrition",
    "Nature's Bounty",
    "Solgar",
    "Thorne",
    "Life Extension",
    "Centrum",
    "Kirkland Signature",
]

_EMOJI_BY_KIND = {"supplement": "💊", "brand": "🏷️"}


def _strip_tags(value: str) -> str:
    return re.sub(r"<[^>]+>", "", value or "").strip()


class _SummaryParser(HTMLParser):
    """Extracts plain paragraph text and bullet-list items from a
    MedlinePlus `FullSummary` HTML blob (same shape as
    `sync_medlineplus_content_library.py`'s parser)."""

    def __init__(self):
        super().__init__()
        self.paragraphs: list[str] = []
        self.bullets: list[str] = []
        self._buffer: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "li":
            self._buffer = []

    def handle_endtag(self, tag):
        if tag == "p":
            text = "".join(self._buffer).strip()
            self._buffer = []
            if text:
                self.paragraphs.append(text)
        elif tag == "li":
            text = "".join(self._buffer).strip()
            if text:
                self.bullets.append(text)
            self._buffer = []

    def handle_data(self, data):
        self._buffer.append(data)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug


def _fetch_medlineplus_top_match(term: str) -> dict | None:
    response = requests.get(
        _MEDLINEPLUS_URL,
        params={"db": "healthTopicsSpanish", "term": term, "retmax": 1},
        timeout=30,
    )
    response.raise_for_status()
    root = ET.fromstring(response.content)
    doc = root.find(".//document")
    if doc is None:
        return None
    fields = {c.get("name"): "".join(c.itertext()) for c in doc.findall("content")}
    return {"url": doc.get("url", ""), "summary_html": fields.get("FullSummary", "")}


def _build_supplement_doc(name: str, term: str) -> dict | None:
    match = _fetch_medlineplus_top_match(term)
    if match is None or not match["url"]:
        return None
    parser = _SummaryParser()
    parser.feed(match["summary_html"] or "")
    if not parser.paragraphs:
        return None
    description = "\n\n".join(parser.paragraphs) + "\n\nFuente: MedlinePlus.gov"
    return {
        "_id": f"recommendation-supplement-{_slugify(name)}",
        "owner_id": None,
        "kind": "supplement",
        "title": name,
        "subtitle": None,
        "category": None,
        "brand": None,
        "description": description[:2000],
        "benefits": parser.bullets[:6],
        "usage": None,
        "notes": f"Fuente: {match['url']}",
        "price": None,
        "rating": None,
        "emoji": _EMOJI_BY_KIND["supplement"],
    }


def _fetch_dsld_hits(query: str, size: int = 25) -> list[dict]:
    response = requests.get(_DSLD_URL, params={"q": query, "size": size}, timeout=30)
    response.raise_for_status()
    return response.json().get("hits", [])


def _build_brand_doc(brand: str) -> dict | None:
    # DSLD's full-text search sometimes mis-ranks a brand's own apostrophe
    # ("Nature's Bounty" as a query returns unrelated results — confirmed
    # live), so the apostrophe is stripped only from the outgoing query;
    # the exact-match check below still requires the real brandName
    # (apostrophe included) to come back from DSLD.
    hits = _fetch_dsld_hits(brand.replace("'", ""))
    exact = [
        hit["_source"]
        for hit in hits
        if (hit.get("_source") or {}).get("brandName", "").strip().lower() == brand.lower()
    ]
    if not exact:
        return None
    categories = Counter(
        source["productType"]["langualCodeDescription"]
        for source in exact
        if source.get("productType", {}).get("langualCodeDescription")
    )
    top_categories = [name for name, _ in categories.most_common(4)]
    description = (
        f"{brand} es una marca de suplementos verificada en el registro "
        f"oficial de etiquetas de la FDA/NIH, con productos en categorías "
        f"como {', '.join(top_categories) or 'suplementos dietéticos'}.\n\n"
        "Fuente: NIH Dietary Supplement Label Database (dsld.od.nih.gov)"
    )
    return {
        "_id": f"recommendation-brand-{_slugify(brand)}",
        "owner_id": None,
        "kind": "brand",
        "title": brand,
        "subtitle": top_categories[0] if top_categories else None,
        "category": ", ".join(top_categories) or None,
        "brand": brand,
        "description": description,
        "benefits": [],
        "usage": None,
        "notes": "Fuente: dsld.od.nih.gov",
        "price": None,
        "rating": None,
        "emoji": _EMOJI_BY_KIND["brand"],
    }


async def sync(*, limit: int | None = None) -> int:
    db = get_db()
    synced = 0

    supplement_items = list(_SUPPLEMENTS.items())
    if limit:
        supplement_items = supplement_items[:limit]
    for name, term in supplement_items:
        doc = _build_supplement_doc(name, term)
        if doc is None:
            continue
        await db.recommendations.update_one({"_id": doc["_id"]}, {"$set": doc}, upsert=True)
        synced += 1

    brand_items = _BRANDS[:limit] if limit else _BRANDS
    for brand in brand_items:
        doc = _build_brand_doc(brand)
        if doc is None:
            continue
        await db.recommendations.update_one({"_id": doc["_id"]}, {"$set": doc}, upsert=True)
        synced += 1

    return synced


async def main() -> None:
    await connect_to_mongo(settings.MONGO_URI, settings.MONGO_DB)
    try:
        count = await sync()
        print(f"Synced {count} platform recommendations (supplements + brands).")
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())
