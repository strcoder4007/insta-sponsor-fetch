from __future__ import annotations

import re
from typing import Dict, List, Tuple


DEFAULT_SPONSOR_KEYWORDS = [
    "#ad",
    "#sponsored",
    "#partner",
    "#paidpartnership",
    "paid partnership",
    "partnered",
    "gifted",
    "gifted stay",
]

HOTEL_TERMS = [
    "hotel",
    "resort",
    "inn",
    "lodge",
    "spa",
    "boutique",
    "suites",
]


def sponsored_flags(
    caption: str,
    paid_banner_present: bool,
    tagged_accounts: List[str],
    sponsor_keywords: List[str] | None = None,
) -> Tuple[bool, List[str]]:
    reasons: List[str] = []
    kws = [k.lower() for k in (sponsor_keywords or DEFAULT_SPONSOR_KEYWORDS)]
    text = (caption or "").lower()
    if paid_banner_present:
        reasons.append("banner")
    if any(k in text for k in kws):
        reasons.append("keyword")
    # Tagged hotel heuristic (account contains hotel term)
    for t in tagged_accounts or []:
        handle = t.lower()
        if any(term in handle for term in HOTEL_TERMS):
            reasons.append("tagged_hotel")
            break
    return (len(reasons) > 0, reasons)


def find_hotel_candidates(
    caption: str,
    hashtags: List[str],
    mentions: List[str],
    tagged_accounts: List[str],
    location_name: str,
) -> List[Dict[str, str]]:
    candidates: List[Dict[str, str]] = []
    text = (caption or "").lower()
    # From location name
    if location_name:
        ln = location_name.strip()
        if any(term in ln.lower() for term in HOTEL_TERMS):
            candidates.append({"name": ln, "instagram_handle": ""})

    # From tagged accounts / mentions
    for acc in list(dict.fromkeys((tagged_accounts or []) + (mentions or []))):
        h = acc.strip().lstrip("@")
        if not h:
            continue
        if any(term in h.lower() for term in HOTEL_TERMS):
            candidates.append({"name": "", "instagram_handle": h})

    # From caption fuzzy (look for hotel term followed by words)
    m = re.search(r"\b(" + "|".join(map(re.escape, HOTEL_TERMS)) + r")\b.*", text)
    if m:
        frag = text[m.start(): m.end()]
        candidates.append({"name": frag[:80].strip(), "instagram_handle": ""})

    # Deduplicate by (name, handle)
    seen = set()
    uniq: List[Dict[str, str]] = []
    for c in candidates:
        key = (c.get("name", "").lower(), c.get("instagram_handle", "").lower())
        if key in seen:
            continue
        seen.add(key)
        uniq.append(c)
    return uniq

