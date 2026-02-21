# insta-sponsor-fetch - Project Handoff

## 1. Project Overview

**insta-sponsor-fetch** is a web scraping tool that identifies sponsored hotel stays from Instagram creators. It extracts post metadata, detects sponsorship, and enriches hotel contact information for outreach.

### Key Features
- Scrapes Instagram creator profiles using Playwright
- Extracts post URL, caption, date, hashtags, location
- Sponsored content detection (banner text, keywords, tagged hotels)
- Hotel enrichment via bio/website crawling + Google Places (optional)
- Resumable - skips already processed profiles

---

## 2. Tech Stack

| Layer | Technology |
|-------|------------|
| **Scraping** | Playwright (Chromium) |
| **Language** | Python 3.10+ |
| **Data** | CSV input, JSON/NDJSON output |
| **Optional** | Google Places API |

---

## 3. File Structure

```
insta-sponsor-fetch/
├── src/                  # Python source code
│   └── instagram_sponsor/
│       └── cli.py       # Main CLI entry point
├── configs/             # Configuration files
├── scripts/             # Utility scripts
├── outputs/             # Scraped data output
├── data.csv             # Input CSV with creator URLs
├── requirements.txt     # Python dependencies
├── .env                 # API keys (gitignored)
├── .env.example         # Template
└── README.md
```

---

## 4. Setup & Running

### Prerequisites
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```

### Run
```bash
# Basic usage (first run - login required)
PYTHONPATH=src python -m instagram_sponsor.cli --csv creators.csv

# Headless mode (after first login)
PYTHONPATH=src python -m instagram_sponsor.cli --csv creators.csv --headless
```

### CLI Options
- `--csv` - Input CSV with Instagram profile URLs
- `--url-column` - Column name for profile URLs (default: "Instagram Url")
- `--out` - Output directory
- `--limit` - Max posts per profile (default: 6)
- `--headless` - Run browser headless
- `--user-data-dir` - Persistent Chromium user data
- `--out-file` - Output file path
- `--google-places-key` - Google Places API key (optional)

---

## 5. Output

Results written to `outputs/all.json` with fields:
- Post URL, caption, date
- Hashtags/mentions
- Location
- Sponsorship detection flags
- Enriched hotel info (website, email, address)

---

## 6. Important Notes

- ⚠️ Use responsibly - follows Instagram's Terms of Service
- First run requires manual Instagram login (non-headless)
- Creates `.pw_instagram` directory for browser session persistence
- Appends incrementally - resumes from last processed profile

---

## 7. What a New Agent Needs to Know

- Main logic: `src/instagram_sponsor/cli.py`
- Check `configs/` for any configuration
- Input CSV format: needs "Instagram Url" column or specify with `--url-column`

---

*Generated: February 21, 2026*
