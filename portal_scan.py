#!/usr/bin/env python3
"""portal_scan.py — elenca i dataset di un portale open data dal suo sitemap.

Serve a confrontare il portale *diretto* di un ente con il catalogo nazionale
(dati.gov.it), che spesso è un harvest parziale e non aggiornato. Il portale
diretto è la fonte di verità su cosa l'ente pubblica davvero.

Uso:
  python portal_scan.py <sitemap-index-or-sitemap-url>
  python portal_scan.py <sitemap> --json
  python portal_scan.py <sitemap> --match posti-letto
  python portal_scan.py <sitemap> --catalog ministero-della-salute
"""

from __future__ import annotations

import argparse
import json
import re
import urllib.request
from collections import Counter

UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120 Safari/537.36"
)
DATI_GOV_IT = "https://dati.gov.it/opendata/api/3/action/package_search"


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:  # noqa: S310
        return r.read().decode("utf-8", "replace")


def _locs(xml: str) -> list[str]:
    return re.findall(r"<loc>\s*([^<]+?)\s*</loc>", xml)


def discover_sitemaps(index_url: str) -> list[str]:
    """Da un sitemap-index (o da un sitemap diretto) all'elenco dei sitemap."""
    xml = fetch(index_url)
    if "<sitemapindex" in xml:
        return _locs(xml)
    return [index_url]


def dataset_urls(sitemap_url: str, path_filter: str = "/dataset/") -> list[str]:
    return [u for u in _locs(fetch(sitemap_url)) if path_filter in u]


def slug_of(url: str) -> str:
    return url.rstrip("/").rsplit("/", 1)[-1]


def year_of(slug: str) -> int | None:
    years = re.findall(r"(?:19|20)\d{2}", slug)
    return int(years[-1]) if years else None


def catalog(org: str, rows: int = 200) -> dict:
    """Conta i dataset di un'organizzazione sul catalogo nazionale."""
    data = json.loads(fetch(f"{DATI_GOV_IT}?fq=organization:{org}&rows={rows}"))
    res = data.get("result", {})
    items = res.get("results", [])
    return {
        "count": res.get("count", len(items)),
        "titles": [p.get("title", "") for p in items],
        "formats": Counter(
            r.get("format", "?") for p in items for r in p.get("resources", [])
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Elenco dataset dal sitemap di un portale")
    p.add_argument("sitemap", help="URL del sitemap-index o del sitemap")
    p.add_argument("--json", action="store_true", help="output JSON")
    p.add_argument("--match", help="filtra gli slug che contengono questa stringa")
    p.add_argument("--catalog", help="org su dati.gov.it da confrontare (es. ministero-della-salute)")
    p.add_argument("--path", default="/dataset/", help="filtro di path (default /dataset/)")
    args = p.parse_args()

    urls: list[str] = []
    for sm in discover_sitemaps(args.sitemap):
        urls += dataset_urls(sm, args.path)

    items = [{"slug": slug_of(u), "year": year_of(slug_of(u)), "url": u} for u in urls]
    items.sort(key=lambda x: x["slug"])

    if args.match:
        items = [i for i in items if args.match in i["slug"]]

    years = Counter(i["year"] for i in items if i["year"])

    if args.json:
        print(json.dumps({"total": len(items), "years": dict(sorted(years.items())), "items": items},
                         ensure_ascii=False, indent=2))
    else:
        print(f"Portale: {len(items)} dataset")
        if years:
            print("Anni (dallo slug):", dict(sorted(years.items())))
        for i in items:
            y = f"  [{i['year']}]" if i["year"] else ""
            print(f"  {i['slug']}{y}")

    if args.catalog:
        cat = catalog(args.catalog)
        print(f"\nCatalogo nazionale dati.gov.it (organization:{args.catalog}): {cat['count']} dataset")
        print("Formati:", dict(cat["formats"]))


if __name__ == "__main__":
    main()
