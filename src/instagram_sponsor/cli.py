from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .scraper import run
from .utils import read_profile_urls


def parse_args(argv: list[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        prog="instagram-sponsor",
        description=(
            "Iterate CSV Instagram profile URLs, open profiles, and capture posts "
            "with metadata to detect sponsored hotel stays and enrich hotel contacts."
        ),
    )
    ap.add_argument("--csv", required=True, help="Path to input CSV (must include Instagram profile URL column)")
    ap.add_argument("--url-column", default="Instagram Url", help="CSV column containing profile URLs")
    ap.add_argument("--out", default="outputs", help="Output directory (parent of aggregated file)")
    ap.add_argument(
        "--limit",
        type=int,
        default=6,
        help="Max posts per profile to collect (default 6)",
    )
    ap.add_argument(
        "--headless", action="store_true", help="Run browser headless (first run should be non-headless to login)"
    )
    ap.add_argument("--user-data-dir", default=".pw_instagram", help="Persistent Chromium user data dir for session reuse")
    ap.add_argument(
        "--out-file",
        default="outputs/all.json",
        help=(
            "Path to the single aggregated output file (default: outputs/all.json). "
            "If the file exists, profiles already present are skipped."
        ),
    )
    ap.add_argument(
        "--aggregate-format",
        choices=["json", "ndjson"],
        default="json",
        help=(
            "Format for the aggregated file: 'json' writes a JSON array of profile objects; 'ndjson' writes one JSON object per line."
        ),
    )
    ap.add_argument(
        "--google-places-key",
        default=os.environ.get("GOOGLE_PLACES_API_KEY", ""),
        help="Google Places API key (env: GOOGLE_PLACES_API_KEY). Optional.",
    )
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    ns = parse_args(argv or sys.argv[1:])
    urls = read_profile_urls(ns.csv, ns.url_column)
    if not urls:
        print("No profile URLs found.")
        return 1
    Path(ns.out).mkdir(parents=True, exist_ok=True)
    run(
        urls,
        out_dir=ns.out,
        limit=ns.limit,
        headless=ns.headless,
        user_data_dir=ns.user_data_dir,
        out_file=ns.out_file,
        aggregate_format=ns.aggregate_format,
        google_places_api_key=(ns.google_places_key or None),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

