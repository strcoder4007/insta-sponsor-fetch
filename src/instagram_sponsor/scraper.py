from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from playwright.sync_api import TimeoutError, sync_playwright
from tqdm import tqdm

from .selectors import (
    GRID_POST_LINKS,
    POST_DIALOG,
    POST_TIME,
    POST_LOCATION_LINK,
    CAPTION_PRIMARY,
    CAPTION_FALLBACK,
    PAID_PARTNERSHIP_TEXTS,
    CLOSE_BUTTON,
)
from .utils import (
    ensure_dir,
    jitter_sleep,
    write_json,
    extract_hashtags,
    extract_mentions,
)
from .detection import sponsored_flags, find_hotel_candidates
from .enrichment import enrich_hotel_candidate


def _ensure_logged_in(page, headless: bool) -> None:
    page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
    is_login = False
    try:
        is_login = page.locator("input[name='username']").count() > 0
    except Exception:
        pass
    if is_login and not headless:
        print("Sign in to Instagram in the opened browser, then press Enter here…", file=sys.stderr)
        try:
            input()
        except EOFError:
            pass


def _open_first_n_posts(page, n: int) -> List[str]:
    # Ensure enough posts are present
    for _ in range(8):
        links = page.locator(GRID_POST_LINKS)
        if links.count() >= n:
            break
        page.mouse.wheel(0, 2000)
        jitter_sleep(0.6, 1.0)

    links = page.locator(GRID_POST_LINKS)
    count = min(links.count(), n)
    hrefs: List[str] = []
    for i in range(count):
        try:
            link = links.nth(i)
            href = link.get_attribute("href") or ""
            hrefs.append(href)
        except Exception:
            continue
    return hrefs


def _extract_from_dialog(page) -> Tuple[str, str, str, List[str], List[str], List[str], str, bool]:
    # Returns: (post_url, date_iso, caption, hashtags, mentions, tagged_accounts, location_name, paid_banner)
    dialog = page.locator(POST_DIALOG)
    if not dialog.count():
        return "", "", "", [], [], [], "", False

    # URL via timestamp anchor or page.url change
    post_url = ""
    try:
        time_el = dialog.locator(POST_TIME).first
        anchor = time_el.locator("xpath=ancestor::a[1]")
        if anchor.count():
            href = anchor.first.get_attribute("href")
            if href:
                post_url = href
    except Exception:
        pass
    if not post_url:
        try:
            post_url = page.url
        except Exception:
            post_url = ""

    # Date
    date_iso = ""
    try:
        date_iso = dialog.locator(POST_TIME).first.get_attribute("datetime") or ""
    except Exception:
        pass

    # Caption
    caption = ""
    for sel in (CAPTION_PRIMARY, CAPTION_FALLBACK):
        loc = dialog.locator(sel)
        if loc.count():
            try:
                caption = loc.first.inner_text(timeout=3000).strip()
                if caption:
                    break
            except Exception:
                continue

    hashtags = extract_hashtags(caption)
    mentions = extract_mentions(caption)

    # Tagged accounts (basic: use mentions as fallback)
    tagged_accounts: List[str] = list(mentions)

    # Location name
    location_name = ""
    try:
        loc_link = dialog.locator(POST_LOCATION_LINK)
        if loc_link.count():
            location_name = (loc_link.first.inner_text(timeout=2000) or "").strip()
    except Exception:
        pass

    # Paid partnership banner detection (textual)
    paid_banner = False
    try:
        dialog_text = (dialog.inner_text(timeout=2000) or "").lower()
        paid_banner = any(s.lower() in dialog_text for s in PAID_PARTNERSHIP_TEXTS)
    except Exception:
        pass

    return post_url, date_iso, caption, hashtags, mentions, tagged_accounts, location_name, paid_banner


def scrape_profile(page, profile_url: str, limit: int, google_places_api_key: str | None) -> Dict:
    page.goto(profile_url, wait_until="domcontentloaded")
    try:
        page.wait_for_selector(GRID_POST_LINKS, state="visible", timeout=8000)
    except TimeoutError:
        return {"profile_url": profile_url, "posts": []}

    hrefs = _open_first_n_posts(page, n=limit)
    posts: List[Dict] = []

    for href in hrefs:
        try:
            # Open dialog by clicking the link element matching href
            page.locator(f"a[href='{href}']").first.click(timeout=3000)
        except Exception:
            continue

        try:
            page.locator(POST_DIALOG).first.wait_for(state="visible", timeout=6000)
        except TimeoutError:
            continue

        post_url, date_iso, caption, hashtags, mentions, tagged_accounts, location_name, paid_banner = _extract_from_dialog(page)

        sponsored, reasons = sponsored_flags(
            caption=caption,
            paid_banner_present=paid_banner,
            tagged_accounts=tagged_accounts,
        )

        hotel_info = {
            "name": None,
            "instagram_handle": None,
            "website": None,
            "email": None,
            "address": None,
            "phone": None,
            "enrichment_source": None,
        }

        if sponsored:
            candidates = find_hotel_candidates(caption, hashtags, mentions, tagged_accounts, location_name)
            # Enrich the first plausible candidate
            if candidates:
                c = candidates[0]
                enriched = enrich_hotel_candidate(c, google_places_api_key)
                hotel_info.update({
                    "name": c.get("name") or None,
                    "instagram_handle": (c.get("instagram_handle") or None),
                    **enriched,
                })

        posts.append({
            "post_url": post_url,
            "date_iso": date_iso,
            "caption": caption,
            "hashtags": hashtags,
            "mentions": mentions,
            "tagged_accounts": tagged_accounts,
            "location_name": location_name,
            "sponsored": sponsored,
            "sponsored_reasons": reasons,
            "hotel": hotel_info,
        })

        # Close dialog
        try:
            page.locator(CLOSE_BUTTON).first.click(timeout=2000)
        except Exception:
            # Fallback: press Escape
            try:
                page.keyboard.press("Escape")
            except Exception:
                pass
        jitter_sleep(0.4, 0.8)

    return {"profile_url": profile_url, "posts": posts}


def run(
    profile_urls: List[str],
    out_dir: str,
    limit: int = 6,
    headless: bool = False,
    user_data_dir: str = ".pw_instagram",
    out_file: str | None = None,
    aggregate_format: str = "json",
    google_places_api_key: str | None = None,
) -> None:
    ensure_dir(out_dir)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=headless,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        # Clipboard not required for Instagram flow, but safe defaults
        page = context.new_page()

        _ensure_logged_in(page, headless=headless)

        agg_path = Path(out_file) if out_file else Path(out_dir) / "all.json"
        processed_urls: set[str] = set()
        all_payloads: list[dict] = []
        if agg_path.exists():
            try:
                if aggregate_format == "ndjson":
                    with agg_path.open("r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            obj = json.loads(line)
                            url = (obj.get("profile_url") or "").strip()
                            if url:
                                processed_urls.add(url)
                else:
                    with agg_path.open("r", encoding="utf-8") as f:
                        obj = json.load(f)
                    profiles = obj.get("profiles") if isinstance(obj, dict) else None
                    if isinstance(profiles, list):
                        for item in profiles:
                            if isinstance(item, dict):
                                url = (item.get("profile_url") or "").strip()
                                if url:
                                    processed_urls.add(url)
                        all_payloads = list(profiles)
            except Exception:
                processed_urls = set()
                all_payloads = []

        total = len(profile_urls)
        for idx, url in enumerate(tqdm(profile_urls, desc="Profiles", unit="profile"), start=1):
            if url in processed_urls:
                tqdm.write(f"[{idx}/{total}] Skipping already scraped: {url}")
                continue
            tqdm.write(f"[{idx}/{total}] {url} → {agg_path}")

            payload = scrape_profile(page, url, limit=limit, google_places_api_key=google_places_api_key)
            all_payloads.append(payload)

            jitter_sleep(1.0, 2.0)

            agg_path.parent.mkdir(parents=True, exist_ok=True)
            if aggregate_format == "ndjson":
                mode = "a" if agg_path.exists() else "w"
                with agg_path.open(mode, encoding="utf-8") as f:
                    f.write(json.dumps(payload, ensure_ascii=False) + "\n")
            else:
                write_json(agg_path, {"profiles": all_payloads})

        context.close()

