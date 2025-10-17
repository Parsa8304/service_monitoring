from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import quote, urljoin

import cloudscraper
from bs4 import BeautifulSoup

BASE_URL = "https://khabarfarsi.com"
SEARCH_ENDPOINT = f"{BASE_URL}/search"
DEFAULT_LIMIT = 50

COMMON_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/127.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"  # noqa: E501
        "image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "max-age=0",
    "Upgrade-Insecure-Requests": "1",
    "Sec-CH-UA": '"Chromium";v="127", "Not;A=Brand";v="24", "Google Chrome";v="127"',
    "Sec-CH-UA-Mobile": "?0",
    "Sec-CH-UA-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
}


def slugify(value: str) -> str:
    value = value.strip()
    if not value:
        return "query"
    value = re.sub(r"\s+", "_", value)
    value = re.sub(r"[^0-9A-Za-z_\-\u0600-\u06FF]", "", value)
    return value[:80]


def normalise_whitespace(text: str) -> str:
    return " ".join(text.split())


def create_scraper() -> cloudscraper.CloudScraper:
    return cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "mobile": False}
    )


def get_form_build_id(scraper: cloudscraper.CloudScraper) -> str:
    response = scraper.get(SEARCH_ENDPOINT, headers=COMMON_HEADERS, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")
    form = soup.select_one("form#se-srch-search-form")
    if not form:
        raise RuntimeError("Search form not found on the page")

    token_input = form.select_one("input[name=form_build_id]")
    if not token_input or not token_input.get("value"):
        raise RuntimeError("form_build_id token is missing from the search form")

    return token_input["value"]


def fetch_search_results(scraper: cloudscraper.CloudScraper, query: str) -> str:
    token = get_form_build_id(scraper)

    payload = {
        "all_words": query,
        "phrase": "",
        "not": "",
        "form_build_id": token,
        "form_id": "se_srch_search_form",
        "op": "جستجو",
    }

    headers = {
        **COMMON_HEADERS,
        "Referer": SEARCH_ENDPOINT,
        "Origin": BASE_URL,
        "Content-Type": "application/x-www-form-urlencoded",
    }

    slug = quote(query)
    response = scraper.post(
        f"{SEARCH_ENDPOINT}/{slug}",
        data=payload,
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()
    return response.text


def parse_results(html: str) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(html, "lxml")
    items: List[Dict[str, Any]] = []

    for wrapper in soup.select("#search_results_wrapper .top_item_wrapper"):
        title_anchor = wrapper.select_one("h2 a.ntitle")
        if not title_anchor:
            continue

        title = normalise_whitespace(title_anchor.get_text(strip=True))
        relative_url = title_anchor.get("href", "")
        url = urljoin(BASE_URL, relative_url)

        source_anchor = wrapper.select_one(".nmeta a")
        source = source_anchor.get_text(strip=True) if source_anchor else None

        time_badge = wrapper.select_one(".nmeta .semelapsed")
        relative_time = time_badge.get_text(strip=True) if time_badge else None

        snippet_block = wrapper.select_one(".nbody")
        snippet = normalise_whitespace(snippet_block.get_text(" ", strip=True)) if snippet_block else None

        image_tag = wrapper.select_one(".hidden_imageinmobile img, .hidden_imageindesktop img")
        if image_tag and image_tag.get("src"):
            image_src = image_tag["src"].strip()
            if image_src.startswith("//"):
                image_url = f"https:{image_src}"
            else:
                image_url = urljoin(BASE_URL, image_src)
        else:
            image_url = None

        similar_links = []
        for link in wrapper.select(".similar-meta a.similar-link.ntitle"):
            similar_links.append(
                {
                    "title": normalise_whitespace(link.get_text(strip=True)),
                    "url": urljoin(BASE_URL, link.get("href", "")),
                }
            )

        items.append(
            {
                "title": title,
                "url": url,
                "source": source,
                "relative_time": relative_time,
                "snippet": snippet,
                "image_url": image_url,
                "similar_sources": similar_links or None,
            }
        )

    return items


def save_json(results: List[Dict[str, Any]], query: str, output_path: Path) -> None:
    payload: Dict[str, Any] = {
        "query": query,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "result_count": len(results),
        "results": results,
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def run_search_for_query(
    scraper: cloudscraper.CloudScraper,
    query: str,
    limit: int,
    output_dir: Path,
    cache_dir: Path,
) -> Dict[str, Any]:
    slug = slugify(query)
    cache_path = cache_dir / f"{slug}.html"
    ensure_directory(cache_dir)
    ensure_directory(output_dir)

    try:
        html = fetch_search_results(scraper, query)
        cache_path.write_text(html, encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        if cache_path.exists():
            print(f"⚠️  {query!r}: network failed ({exc}); falling back to cached HTML")
            html = cache_path.read_text(encoding="utf-8")
        else:
            raise RuntimeError(f"Failed to fetch results for {query!r}: {exc}") from exc

    results = parse_results(html)[:limit]
    output_path = output_dir / f"{slug}.json"
    save_json(results, query, output_path)
    print(f"✅ Saved {len(results)} results to {output_path}")

    return {
        "query": query,
        "output": str(output_path),
        "html_cache": str(cache_path),
        "count": len(results),
    }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Search khabarfarsi.com for one or more phrases and export the top "
            "results to JSON files."
        )
    )
    parser.add_argument("phrases", nargs="+", help="One or more search phrases to query.")
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help="Maximum number of results to keep per query (default: 50).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs"),
        help="Directory where JSON files will be written (default: ./outputs).",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("cache"),
        help="Directory where raw HTML responses are cached (default: ./cache).",
    )
    parser.add_argument(
        "--combined-output",
        type=Path,
        help="Optional path to write a combined JSON file summarising all queries.",
    )
    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    if args.limit <= 0:
        parser.error("--limit must be a positive integer")

    summaries: List[Dict[str, Any]] = []
    ensure_directory(args.output_dir)
    ensure_directory(args.cache_dir)

    with create_scraper() as scraper:
        scraper.headers.update(COMMON_HEADERS)
        for phrase in args.phrases:
            summary = run_search_for_query(
                scraper=scraper,
                query=phrase,
                limit=args.limit,
                output_dir=args.output_dir,
                cache_dir=args.cache_dir,
            )
            summaries.append(summary)

    if args.combined_output:
        combined_payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "queries": summaries,
        }
        args.combined_output.write_text(
            json.dumps(combined_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"📦 Combined summary written to {args.combined_output}")


if __name__ == "__main__":
    main()