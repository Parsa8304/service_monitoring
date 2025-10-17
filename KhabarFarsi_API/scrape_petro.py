from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://khabarfarsi.com"
SEARCH_ENDPOINT = f"{BASE_URL}/search"
DEFAULT_QUERY = "پتروشیمی"
OUTPUT_FILE = Path("petro_search.json")

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
}


def get_form_build_id(session: requests.Session) -> str:
    """Fetch the search page and extract the current form_build_id."""
    response = session.get(SEARCH_ENDPOINT, headers=COMMON_HEADERS, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")
    form = soup.select_one("form#se-srch-search-form")
    if not form:
        raise RuntimeError("Search form not found on the page")

    token_input = form.select_one("input[name=form_build_id]")
    if not token_input or not token_input.get("value"):
        raise RuntimeError("form_build_id token is missing from the search form")

    return token_input["value"]


def fetch_search_results(session: requests.Session, query: str) -> str:
    """Submit the search form for the given query and return the HTML response."""
    token = get_form_build_id(session)

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

    # The site expects the query slug to be part of the URL.
    response = session.post(
        f"{SEARCH_ENDPOINT}/{query}",
        data=payload,
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()
    return response.text


def normalise_whitespace(text: str) -> str:
    return " ".join(text.split())


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


def save_results(results: List[Dict[str, Any]], query: str, output_file: Path = OUTPUT_FILE) -> None:
    output: Dict[str, Any] = {
        "query": query,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "result_count": len(results),
        "results": results,
    }

    output_file.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")


def main(query: str = DEFAULT_QUERY) -> None:
    with requests.Session() as session:
        try:
            html = fetch_search_results(session, query)
            Path("petro_search.html").write_text(html, encoding="utf-8")
        except requests.RequestException as exc:
            cached_file = Path("petro_search.html")
            if cached_file.exists():
                print(
                    "Network request failed (" + str(exc) + ") – using cached HTML."
                )
                html = cached_file.read_text(encoding="utf-8")
            else:
                raise
    results = parse_results(html)
    save_results(results, query)
    print(f"Saved {len(results)} results to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()