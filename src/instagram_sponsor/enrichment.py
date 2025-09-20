from __future__ import annotations

import json
import re
import sys
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlencode
from urllib.request import Request, urlopen


UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0 Safari/537.36"
)


def _http_get(url: str, timeout: int = 20) -> str:
    req = Request(url, headers={"User-Agent": UA})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


_MAIL_RE = re.compile(r"mailto:([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)")
_PHONE_RE = re.compile(r"\+?\d[\d\s().-]{7,}\d")


def parse_contact_from_html(html: str) -> Tuple[Optional[str], Optional[str]]:
    email = None
    phone = None
    m = _MAIL_RE.search(html)
    if m:
        email = m.group(1)
    m2 = _PHONE_RE.search(html)
    if m2:
        phone = m2.group(0)
    return email, phone


def enrich_from_instagram_bio_html(html: str) -> Tuple[Optional[str], Optional[str]]:
    # Find external website link in bio (first http(s) link)
    website = None
    m = re.search(r"href=\"(https?://[^\"]+)\"", html)
    if m:
        website = m.group(1)
    email, _ = parse_contact_from_html(html)
    return website, email


def query_google_places(name: str, api_key: Optional[str]) -> Dict[str, Optional[str]]:
    if not api_key or not name:
        return {"website": None, "address": None, "phone": None}
    try:
        q = urlencode({"query": name, "key": api_key})
        url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?{q}"
        raw = _http_get(url)
        obj = json.loads(raw)
        results = obj.get("results") or []
        if not results:
            return {"website": None, "address": None, "phone": None}
        place_id = results[0].get("place_id")
        if not place_id:
            return {"website": None, "address": None, "phone": None}
        q2 = urlencode({"place_id": place_id, "key": api_key, "fields": "formatted_address,formatted_phone_number,website"})
        url2 = f"https://maps.googleapis.com/maps/api/place/details/json?{q2}"
        raw2 = _http_get(url2)
        obj2 = json.loads(raw2)
        res = obj2.get("result") or {}
        return {
            "website": res.get("website"),
            "address": res.get("formatted_address"),
            "phone": res.get("formatted_phone_number"),
        }
    except Exception as e:
        print(f"[places] error: {e}", file=sys.stderr)
        return {"website": None, "address": None, "phone": None}


def enrich_hotel_candidate(
    candidate: Dict[str, str],
    google_places_api_key: Optional[str] = None,
) -> Dict[str, Optional[str]]:
    # Priority: instagram bio website/email -> crawl -> google places
    website: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    source = "none"

    # If we have an Instagram handle, try to fetch profile HTML (public only)
    handle = (candidate.get("instagram_handle") or "").strip().lstrip("@")
    if handle:
        try:
            html = _http_get(f"https://www.instagram.com/{handle}/")
            w, e = enrich_from_instagram_bio_html(html)
            if w or e:
                website, email = w, e
                source = "instagram_bio"
        except Exception:
            pass

    # Crawl website home/contact if we have a website
    if website and source == "instagram_bio":
        try:
            home = _http_get(website)
            e2, p2 = parse_contact_from_html(home)
            email = email or e2
            phone = phone or p2
            # Try a naive contact/about link
            m = re.search(r"href=\"(https?://[^\"]*(contact|about)[^\"]*)\"", home, re.I)
            if m:
                cont = _http_get(m.group(1))
                e3, p3 = parse_contact_from_html(cont)
                email = email or e3
                phone = phone or p3
                source = "website_crawl"
        except Exception:
            pass

    # Google Places fallback
    if (not website or not email) and (candidate.get("name") or "") and google_places_api_key:
        res = query_google_places(candidate.get("name") or "", google_places_api_key)
        website = website or res.get("website")
        address = address or res.get("address")
        phone = phone or res.get("phone")
        if res.get("website") or res.get("address") or res.get("phone"):
            source = "google_places"

    return {
        "website": website,
        "email": email,
        "address": address,
        "phone": phone,
        "enrichment_source": source,
    }

