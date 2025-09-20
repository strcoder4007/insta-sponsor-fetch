from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List


DEF_INPUT = "outputs/all.json"
DEF_OUTPUT = "outputs/hotels.csv"


def load_aggregate(path: str) -> Dict[str, Any]:
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def export_csv(payload: Dict[str, Any], out_path: str) -> None:
    profiles = payload.get("profiles") or []
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "Creator Profile",
            "Post URL",
            "Post Date",
            "Sponsored",
            "Reason",
            "Hotel Name",
            "Hotel Instagram",
            "Hotel Website",
            "Hotel Email",
            "Hotel Address",
            "Hotel Phone",
            "Enrichment Source",
        ])
        for prof in profiles:
            profile_url = prof.get("profile_url", "")
            posts = prof.get("posts") or []
            for post in posts:
                hotel = post.get("hotel") or {}
                w.writerow([
                    profile_url,
                    post.get("post_url", ""),
                    post.get("date_iso", ""),
                    post.get("sponsored", False),
                    ",".join(post.get("sponsored_reasons", [])),
                    hotel.get("name") or "",
                    hotel.get("instagram_handle") or "",
                    hotel.get("website") or "",
                    hotel.get("email") or "",
                    hotel.get("address") or "",
                    hotel.get("phone") or "",
                    hotel.get("enrichment_source") or "",
                ])


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Export hotels CSV from aggregated JSON produced by instagram_sponsor scraper",
    )
    ap.add_argument("--input", "-i", default=DEF_INPUT, help="Path to aggregated JSON (default outputs/all.json)")
    ap.add_argument("--output", "-o", default=DEF_OUTPUT, help="Path to write CSV (default outputs/hotels.csv)")
    return ap.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    ns = parse_args(argv)
    payload = load_aggregate(ns.input)
    export_csv(payload, ns.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

