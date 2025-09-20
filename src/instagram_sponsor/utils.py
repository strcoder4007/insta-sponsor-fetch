from __future__ import annotations

import csv
import json
import os
import random
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse


@dataclass
class Post:
    post_url: str
    date_iso: str
    caption: str
    hashtags: List[str]
    mentions: List[str]
    tagged_accounts: List[str]
    location_name: str


def _normalize_header(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace("\ufeff", "").strip().lower())


def _find_column(fieldnames: Optional[List[str]], target: str) -> Optional[str]:
    if not fieldnames:
        return None
    norm_target = _normalize_header(target)
    for name in fieldnames:
        if _normalize_header(name) == norm_target:
            return name
    # Loose contains match as fallback
    for name in fieldnames:
        if norm_target in _normalize_header(name):
            return name
    return None


def read_profile_urls(csv_path: str, url_column: str) -> List[str]:
    urls: List[str] = []
    tried: List[str] = []
    for enc in ("utf-8", "utf-8-sig", "utf-16", "utf-16le", "utf-16be", "latin-1"):
        try:
            with open(csv_path, newline="", encoding=enc, errors="strict") as f:
                reader = csv.DictReader(f)
                actual_col = _find_column(reader.fieldnames, url_column)  # type: ignore[arg-type]
                if not actual_col:
                    tried.append(f"{enc} (no matching column)")
                    continue
                for row in reader:  # type: ignore[assignment]
                    raw = (row.get(actual_col) or "").strip()
                    if not raw:
                        continue
                    urls.append(normalize_profile_url(raw))
                break
        except UnicodeDecodeError:
            tried.append(f"{enc} (decode error)")
            continue
    else:
        raise UnicodeDecodeError("csv", b"", 0, 1, f"Unable to decode CSV. Tried encodings: {', '.join(tried)}")

    # Deduplicate preserving order
    seen = set()
    deduped = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            deduped.append(u)
    return deduped


def normalize_profile_url(url: str) -> str:
    u = url.strip()
    if not u:
        return u
    # Handle bare handles like @name or name
    if not u.startswith("http"):
        u = u.lstrip("@/")
        return f"https://www.instagram.com/{u}/"
    parsed = urlparse(u)
    netloc = parsed.netloc or "www.instagram.com"
    path = parsed.path
    if not path or path == "/":
        return f"https://{netloc}/"
    # Ensure trailing slash on profile URLs
    clean = f"https://{netloc}{path}"
    if not clean.endswith("/"):
        clean += "/"
    return clean


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def write_json(path: str | Path, obj: Dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def jitter_sleep(min_s: float = 0.4, max_s: float = 1.2) -> None:
    time.sleep(random.uniform(min_s, max_s))


_HASHTAG_RE = re.compile(r"(?<!\w)#([\w_]{1,100})")
_MENTION_RE = re.compile(r"(?<!\w)@([\w_.]{1,100})")


def extract_hashtags(text: str) -> List[str]:
    return list(dict.fromkeys([m.group(1) for m in _HASHTAG_RE.finditer(text or "")]))


def extract_mentions(text: str) -> List[str]:
    return list(dict.fromkeys([m.group(1) for m in _MENTION_RE.finditer(text or "")]))

