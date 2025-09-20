"""Centralized selectors and textual anchors for Instagram post scraping.

Selectors are conservative with text fallbacks because Instagram's DOM evolves.
Prefer role/text-based queries where possible; keep a small set of well-known
anchors and complement with regex text matching in the scraper.
"""

# Profile grid items (links to posts/reels)
GRID_POST_LINKS = "a[href*='/p/'], a[href*='/reel/']"

# Post dialog root
POST_DIALOG = "div[role='dialog']"

# Within dialog/article
POST_TIME = "time[datetime]"
POST_LOCATION_LINK = "a[href^='/explore/locations/']"

# Caption container candidates (order matters)
CAPTION_PRIMARY = "div[role='dialog'] ul li div div span"
CAPTION_FALLBACK = "div[role='dialog'] h1, div[role='dialog'] span"

# Paid partnership textual anchors (case-insensitive checks in scraper)
PAID_PARTNERSHIP_TEXTS = (
    "Paid partnership",
    "Paid partnership with",
    "Paid Partnership",
)

# UI controls
NEXT_BUTTON = "button[aria-label='Next']"
CLOSE_BUTTON = "div[role='dialog'] svg[aria-label='Close']"

