# Khabar Farsi Scraper

Utilities for collecting search results from [khabarfarsi.com](https://khabarfarsi.com).

## Prerequisites

1. Python 3.12 (a virtual environment is recommended).
2. Install dependencies:

```powershell
& ".venv/Scripts/python.exe" -m pip install -r requirements.txt
```

> Replace the interpreter path if you are using a different environment.

## Scripts

### `scrape_petro.py`
Fetches cached search results for the phrase «پتروشیمی» and writes them to `petro_search.json`. The script falls back to `petro_search.html` if the live request is blocked.

```powershell
& ".venv/Scripts/python.exe" scrape_petro.py
```

### `search_khabarfarsi.py`
Queries arbitrary search phrases (one or more) and saves the top results to JSON. Raw HTML responses are cached so reruns can operate offline when necessary.

Basic example:

```powershell
& ".venv/Scripts/python.exe" search_khabarfarsi.py "پتروشیمی" "بورس"
```

Options:

- `--limit` – cap the number of results per phrase (default `50`).
- `--output-dir` – directory for JSON exports (default `outputs`).
- `--cache-dir` – directory for cached HTML (default `cache`).
- `--combined-output` – optional JSON file summarising all query runs.

Example with custom directories:

```powershell
& ".venv/Scripts/python.exe" search_khabarfarsi.py "بورس" --limit 20 --output-dir data/json --cache-dir data/html --combined-output data/summary.json
```

## Notes

- The site sits behind Cloudflare. The new script uses `cloudscraper` to emulate a real browser session; cached HTML can serve as a fallback when the network challenge cannot be bypassed.
- Cached HTML files are named after the search phrase (slugified) inside the cache directory.
