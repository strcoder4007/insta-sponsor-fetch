# Instagram Sponsored Hotel Stay Scraper

Identify sponsored hotel stays from Instagram creators and extract hotel contact details (website, email, address) for outreach. Uses Playwright to browse public creator profiles, collect post metadata, detect sponsorship, and enrich hotel info.

> Note: This tool interacts with Instagram via a real browser (Playwright). Use responsibly and in accordance with Instagram’s Terms and applicable laws. Avoid heavy automated scraping.

## Features
- Extracts post URL, caption, date, hashtags/mentions, location
- Sponsored detection via banner text, keywords, and tagged hotel heuristics
- Hotel enrichment from Instagram bio and website crawl; optional Google Places
- Writes a single aggregated output (JSON or NDJSON) and appends incrementally
- Resumable: skips profiles already present in the aggregate file

## Prerequisites
- Python 3.10
- pip (to install Python dependencies)
- Playwright browsers (install after pip step below)

## Setup
```bash
# 1) Create and activate a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2) Install dependencies
pip install -r requirements.txt

# 3) Install the Playwright browser binaries (Chromium)
python -m playwright install chromium
```

## Run
The simplest way to run the CLI from the repo (writes to `outputs/all.json`):
```bash
PYTHONPATH=src python -m instagram_sponsor.cli --csv creators.csv
```

On first run, do not use `--headless` so you can sign in when prompted. A Chromium window opens; sign in to Instagram, then return to the terminal and press Enter when instructed.

### CLI Usage
```text
--csv                 Path to input CSV (must include Instagram profile URLs)
--url-column          CSV column containing the profile URLs (default: "Instagram Url")
--out                 Output directory (parent of aggregated file; default: outputs)
--limit               Max posts per profile to collect (default: 6)
--headless            Run browser headless (first run should be non-headless to login)
--user-data-dir       Persistent Chromium user data directory (default: .pw_instagram)
--out-file            Path to aggregated output file (default: outputs/all.json)
--aggregate-format    Format for aggregated file: "json" | "ndjson" (default: json)
--google-places-key   Google Places API key (env: GOOGLE_PLACES_API_KEY). Optional
```

### Examples
- Minimal run (non-headless first time to sign in):
```bash
PYTHONPATH=src python -m instagram_sponsor.cli --csv creators.csv
# Writes/updates outputs/all.json by default
```

- Headless after you’ve already logged in previously:
```bash
PYTHONPATH=src python -m instagram_sponsor.cli --csv creators.csv --headless
```

- Write newline-delimited JSON (one profile object per line):
```bash
PYTHONPATH=src python -m instagram_sponsor.cli --csv creators.csv \
  --out-file outputs/all.ndjson --aggregate-format ndjson
```

## Input CSV
- The CSV must contain a column with Instagram profile URLs (e.g., `https://www.instagram.com/handle/`).
- You can set a custom column name via `--url-column` (default: `Instagram Url`).

## Output Format

Aggregated output (default behavior):
- `json` (default): a single JSON object with a `profiles` array
```json
{
  "profiles": [
    { "profile_url": "https://www.instagram.com/user1/", "posts": [ ... ] },
    { "profile_url": "https://www.instagram.com/user2/", "posts": [ ... ] }
  ]
}
```

- `ndjson`: one JSON object per line (each object corresponds to a profile)
```text
{"profile_url":"https://www.instagram.com/user1/","posts":[...]}
{"profile_url":"https://www.instagram.com/user2/","posts":[...]}
```

### Post object fields
- `post_url`, `date_iso`, `caption`, `hashtags[]`, `mentions[]`, `tagged_accounts[]`, `location_name`
- `sponsored` (bool), `sponsored_reasons[]` (one or more of: banner, keyword, tagged_hotel)
- `hotel` object: `name`, `instagram_handle`, `website`, `email`, `address`, `phone`, `enrichment_source`

## Config
See `configs/instagram.yaml` for default keywords and terms. The scraper ships with defaults; YAML is optional.
Set `GOOGLE_PLACES_API_KEY` in your environment to enable Places enrichment.

## Export CSV
After scraping, export a spreadsheet-friendly CSV summarizing hotel contacts:
```bash
python scripts/export_hotels_csv.py --input outputs/all.json --output outputs/hotels.csv
```

Output columns: Creator Profile, Post URL, Post Date, Sponsored, Reason, Hotel Name, Hotel Instagram, Website, Email, Address, Phone, Enrichment Source.

## Legal & Ethical
Scraping may be subject to the website’s Terms of Service and local regulations. Use responsibly. Do not share credentials or commit secrets/data to the repository.
