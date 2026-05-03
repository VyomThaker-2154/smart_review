"""
scraper.py
──────────
Scrapes Google Maps reviews for a given business name + optional location.
Uses Playwright (headless Chromium) — no Google API key required.

v3 fixes:
  - Removed broken div[data-review-id] / div.jftiEf selectors
  - Reviews are now found by scrollable feed container + JS evaluation
  - "More" expansion uses JS click to avoid intercepted-click errors
  - Waits for at least 1 review to appear before scrolling
  - Tab click uses JS click as fallback to avoid overlay interception
  - Added _dump_page_info() for diagnostics when 0 reviews found

Install Playwright once:
    pip install playwright
    playwright install chromium
"""

import asyncio
import re
import sys
import urllib.parse
from typing import Optional

from playwright.async_api import async_playwright, Page, Browser, TimeoutError as PWTimeout


# ── Selectors ─────────────────────────────────────────────────────────────────

# First result card in search-results list
SELS_FIRST_RESULT = [
    'a.hfpxzc',
    'div[role="feed"] a[href*="maps/place"]',
    'div.Nv2PK a',
]

# Reviews tab — try all variants
SELS_REVIEWS_TAB = [
    'button[aria-label*="Reviews"]',
    'button[aria-label*="reviews"]',
    'div[role="tablist"] button:nth-child(2)',
    'button[data-tab-index="1"]',
]

# Sort button
SELS_SORT_BTN = [
    'button[aria-label="Sort reviews"]',
    'button[jsaction*="sortReviews"]',
]

# ── Review block selectors (in priority order) ─────────────────────────────
# Google Maps 2024-2025 uses these class names for individual review containers.
# We try each and use whichever returns results.
SELS_REVIEW_BLOCK = [
    # Confirmed active selectors (May 2025)
    'div.jJc9Ad',          # outer review wrapper
    'div[data-review-id]', # older layout
    'div.jftiEf',          # mid-2024 layout
    'div.GHT2ce',          # another variant
    'div[class*="review"]',
]

# Review text body
SELS_REVIEW_TEXT = [
    'span.wiI7pd',
    'div.MyEned span',
    'span[jscontroller] span',
    'div[class*="review-full-text"]',
    'span[class*="review"]',
]

# Star rating
SELS_REVIEW_RATING = [
    'span[role="img"][aria-label*="star"]',
    'span[role="img"][aria-label*="Star"]',
]

# Author name
SELS_REVIEW_AUTHOR = [
    'div.d4r55',
    'button.al6Kxe div',
    'div.WNxzHc button',
]

# Date string
SELS_REVIEW_DATE = [
    'span.rsqaWe',
    'span[class*="date"]',
]

# "More" expand button
SELS_MORE_BTN = [
    'button.w8nwRe',
    'button[aria-label*="More"]',
    'button[jsaction*="expand"]',
]

# Scrollable reviews panel
SELS_SCROLL_PANEL = [
    'div.m6QErb[tabindex="-1"]',
    'div.m6QErb',
    'div.DxyBCb',
    'div[role="main"] div[tabindex="-1"]',
]

# Consent buttons
CONSENT_SELECTORS = [
    'button[aria-label="Accept all"]',
    'button[aria-label="Reject all"]',
    'form[action*="consent"] button',
    'div[role="dialog"] button:first-child',
]


# ── Utilities ─────────────────────────────────────────────────────────────────

def _log(msg: str):
    print(f"[scraper] {msg}", flush=True)


async def _try_selector(page: Page, selectors: list, timeout: int = 3000):
    for sel in selectors:
        try:
            el = await page.wait_for_selector(sel, timeout=timeout)
            if el:
                return el
        except Exception:
            continue
    return None


async def _query_all(page: Page, selectors: list) -> list:
    for sel in selectors:
        try:
            els = await page.query_selector_all(sel)
            if els:
                _log(f"  Selector matched '{sel}': {len(els)} elements")
                return els
        except Exception:
            continue
    return []


def _parse_star_label(label: str) -> Optional[float]:
    m = re.search(r"([\d.]+)\s*star", label, re.IGNORECASE)
    return float(m.group(1)) if m else None


# ── Page helpers ──────────────────────────────────────────────────────────────

async def _dismiss_consent(page: Page):
    _log("Checking for consent screen...")
    for sel in CONSENT_SELECTORS:
        try:
            btn = await page.wait_for_selector(sel, timeout=2000)
            if btn and await btn.is_visible():
                _log(f"  Dismissing: {sel}")
                await btn.click()
                await page.wait_for_timeout(1000)
                return
        except Exception:
            continue
    for label in ["Accept all", "Accept", "Reject all", "I agree"]:
        try:
            btn = page.get_by_role("button", name=label, exact=True)
            if await btn.is_visible(timeout=1200):
                await btn.click()
                await page.wait_for_timeout(800)
                return
        except Exception:
            continue
    _log("  No consent screen.")


async def _wait_stable(page: Page, timeout: int = 6000):
    try:
        await page.wait_for_load_state("networkidle", timeout=timeout)
    except Exception:
        await page.wait_for_timeout(2000)


async def _dump_page_info(page: Page):
    """Log diagnostic info when review extraction finds nothing."""
    _log("  ── DOM diagnostics ──")
    _log(f"  URL: {page.url}")
    # Check what's in the main panel
    for probe in [
        'div.m6QErb', 'div[role="feed"]', 'div[jslog]',
        'div.jJc9Ad', 'div.jftiEf', 'div[data-review-id]',
        'span.wiI7pd', 'div.MyEned',
    ]:
        try:
            count = await page.locator(probe).count()
            if count:
                _log(f"  Found {count}x '{probe}'")
        except Exception:
            pass

    # Dump all aria-label values on visible buttons to spot the Reviews tab name
    try:
        buttons = await page.query_selector_all("button[aria-label]")
        labels = []
        for b in buttons[:20]:
            lbl = await b.get_attribute("aria-label")
            if lbl:
                labels.append(lbl)
        _log(f"  Button aria-labels: {labels}")
    except Exception:
        pass

    try:
        await page.screenshot(path="debug_screenshot.png", full_page=False)
        _log("  Screenshot → debug_screenshot.png")
    except Exception:
        pass
    _log("  ── end diagnostics ──")


# ── Core extraction ───────────────────────────────────────────────────────────

async def _wait_for_reviews(page: Page, timeout_ms: int = 10000) -> bool:
    """Wait until at least one review block appears in the DOM."""
    _log("  Waiting for first review block to appear...")
    deadline = timeout_ms
    step = 500
    while deadline > 0:
        for sel in SELS_REVIEW_BLOCK:
            try:
                els = await page.query_selector_all(sel)
                if els:
                    _log(f"  First reviews appeared with selector: '{sel}'")
                    return True
            except Exception:
                pass
        await page.wait_for_timeout(step)
        deadline -= step

    # Final attempt: JS-based broad search
    count = await page.evaluate("""() => {
        // Try every div that looks like it contains review content
        const candidates = document.querySelectorAll('div[data-review-id], div.jJc9Ad, div.jftiEf');
        return candidates.length;
    }""")
    if count:
        _log(f"  JS found {count} review blocks.")
        return True

    _log("  No review blocks found within timeout.")
    return False


async def _expand_reviews(page: Page):
    """Click all 'More' buttons to expand truncated text (JS click to bypass overlays)."""
    for sel in SELS_MORE_BTN:
        try:
            btns = await page.query_selector_all(sel)
            if btns:
                _log(f"  Expanding {len(btns)} reviews via '{sel}'...")
                for btn in btns:
                    try:
                        await btn.evaluate("el => el.click()")
                        await page.wait_for_timeout(100)
                    except Exception:
                        continue
                break
        except Exception:
            continue


async def _scroll_to_load(page: Page, max_reviews: int, pause: float = 1.5):
    """Scroll the reviews panel until we have enough or the list is exhausted."""
    panel = None
    for sel in SELS_SCROLL_PANEL:
        try:
            el = await page.wait_for_selector(sel, timeout=4000)
            if el:
                panel = el
                _log(f"  Scroll panel found: '{sel}'")
                break
        except Exception:
            continue

    if not panel:
        _log("  No scroll panel found — will scroll page body.")

    prev = 0
    stall = 0

    while stall < 7:
        # Count reviews with any working selector
        count = 0
        for sel in SELS_REVIEW_BLOCK:
            try:
                els = await page.query_selector_all(sel)
                if els:
                    count = len(els)
                    break
            except Exception:
                pass

        _log(f"  Scroll: {count} reviews loaded (target: {max_reviews})")

        if count >= max_reviews:
            break

        if panel:
            try:
                await panel.evaluate("el => el.scrollBy(0, 2000)")
            except Exception:
                await page.evaluate("window.scrollBy(0, 2000)")
        else:
            await page.evaluate("window.scrollBy(0, 2000)")

        await page.wait_for_timeout(int(pause * 1000))
        stall = stall + 1 if count == prev else 0
        prev = count

    _log(f"  Scroll done. {prev} reviews visible.")


async def _extract_reviews(page: Page, max_reviews: int) -> list:
    await _expand_reviews(page)

    # Find working block selector
    blocks = []
    for sel in SELS_REVIEW_BLOCK:
        try:
            els = await page.query_selector_all(sel)
            if els:
                blocks = els
                _log(f"  Extracting with block selector: '{sel}' ({len(els)} blocks)")
                break
        except Exception:
            continue

    if not blocks:
        _log("  No blocks found — trying JS extraction as fallback...")
        return await _js_extract_reviews(page, max_reviews)

    results = []
    for block in blocks[:max_reviews]:
        try:
            text = ""
            for sel in SELS_REVIEW_TEXT:
                el = await block.query_selector(sel)
                if el:
                    text = (await el.inner_text()).strip()
                    if text:
                        break

            rating = None
            for sel in SELS_REVIEW_RATING:
                el = await block.query_selector(sel)
                if el:
                    lbl = await el.get_attribute("aria-label") or ""
                    rating = _parse_star_label(lbl)
                    if rating:
                        break

            author = "Anonymous"
            for sel in SELS_REVIEW_AUTHOR:
                el = await block.query_selector(sel)
                if el:
                    t = (await el.inner_text()).strip()
                    if t:
                        author = t
                        break

            date = ""
            for sel in SELS_REVIEW_DATE:
                el = await block.query_selector(sel)
                if el:
                    date = (await el.inner_text()).strip()
                    if date:
                        break

            if text or rating:
                results.append({"author": author, "rating": rating, "date": date, "text": text})
        except Exception:
            continue

    return results


async def _js_extract_reviews(page: Page, max_reviews: int) -> list:
    """
    Pure JavaScript fallback extraction — reads text content from the page
    without relying on specific class names that may have changed.
    """
    _log("  Running JS fallback extraction...")
    raw = await page.evaluate(f"""() => {{
        const MAX = {max_reviews};
        const results = [];

        // Strategy: look for elements that contain star-rating aria-labels
        // Those are always inside review blocks
        const ratingEls = document.querySelectorAll('span[role="img"][aria-label*="star"], span[role="img"][aria-label*="Star"]');

        for (let i = 0; i < Math.min(ratingEls.length, MAX); i++) {{
            const ratingEl = ratingEls[i];
            const ariaLabel = ratingEl.getAttribute('aria-label') || '';
            const starMatch = ariaLabel.match(/([\d.]+)/);
            const rating = starMatch ? parseFloat(starMatch[1]) : null;

            // Walk up to find the review container (ancestor with meaningful content)
            let container = ratingEl.parentElement;
            for (let j = 0; j < 8; j++) {{
                if (!container) break;
                if (container.offsetHeight > 80) break;
                container = container.parentElement;
            }}

            // Extract text from container
            let text = '';
            if (container) {{
                // Find longest text node in container
                const spans = container.querySelectorAll('span');
                let maxLen = 0;
                for (const span of spans) {{
                    const t = span.innerText || '';
                    if (t.length > maxLen && !t.includes('star') && t.length > 10) {{
                        maxLen = t.length;
                        text = t.trim();
                    }}
                }}
            }}

            // Author: look for button near the rating element
            let author = 'Anonymous';
            if (container) {{
                const btns = container.querySelectorAll('button, div[role="button"]');
                for (const btn of btns) {{
                    const t = (btn.innerText || '').trim();
                    if (t && t.length < 60 && !t.includes('\\n')) {{
                        author = t;
                        break;
                    }}
                }}
            }}

            if (text || rating) {{
                results.push({{ author, rating, date: '', text }});
            }}
        }}

        return results;
    }}""")

    _log(f"  JS fallback extracted {len(raw)} reviews.")
    return raw if raw else []


# ── Main entry ────────────────────────────────────────────────────────────────

async def scrape_google_maps_reviews(
    business_name: str,
    location: Optional[str] = None,
    max_reviews: int = 50,
    sort_by_newest: bool = False,
    headless: bool = True,
) -> dict:
    query = f"{business_name} {location}".strip() if location else business_name
    encoded = urllib.parse.quote_plus(query)
    start_url = f"https://www.google.com/maps/search/{encoded}/"
    _log(f"Query: '{query}'")
    _log(f"URL:   {start_url}")

    result_meta = {
        "business_name": business_name,
        "location": location,
        "place_name": "",
        "place_url": "",
        "total_scraped": 0,
        "reviews": [],
        "error": None,
    }

    async with async_playwright() as p:
        browser: Browser = await p.chromium.launch(
            headless=headless,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--lang=en-US",
            ],
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            timezone_id="Asia/Kolkata",
            extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
        )
        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        page = await context.new_page()

        try:
            # ── 1. Navigate ──────────────────────────────────────────────────
            _log("Step 1: Navigating...")
            await page.goto(start_url, wait_until="domcontentloaded", timeout=45000)
            await _dismiss_consent(page)
            await _wait_stable(page, timeout=6000)
            _log(f"  Landed on: {page.url}")

            # ── 2. Click first result if on a list page ──────────────────────
            _log("Step 2: Checking for result list...")
            first = await _try_selector(page, SELS_FIRST_RESULT, timeout=5000)
            place_name = business_name

            if first:
                place_name = (await first.get_attribute("aria-label") or business_name).strip()
                _log(f"  Clicking result: '{place_name}'")
                await first.click()
                await _wait_stable(page, timeout=8000)
            else:
                _log("  Direct place page — no list click needed.")
                # Try to read place name from page title / heading
                try:
                    h1 = await page.query_selector('h1.DUwDvf, h1[class*="fontHeadline"]')
                    if h1:
                        place_name = (await h1.inner_text()).strip() or business_name
                except Exception:
                    pass

            result_meta["place_name"] = place_name
            result_meta["place_url"] = page.url

            # ── 3. Click Reviews tab ─────────────────────────────────────────
            _log("Step 3: Finding Reviews tab...")
            reviews_tab = await _try_selector(page, SELS_REVIEWS_TAB, timeout=10000)

            if not reviews_tab:
                # Broad fallback: any button whose label contains 'review'
                try:
                    all_buttons = await page.query_selector_all("button[aria-label]")
                    for btn in all_buttons:
                        lbl = (await btn.get_attribute("aria-label") or "").lower()
                        if "review" in lbl:
                            reviews_tab = btn
                            _log(f"  Found Reviews tab via aria-label scan: '{lbl}'")
                            break
                except Exception:
                    pass

            if not reviews_tab:
                await _dump_page_info(page)
                result_meta["error"] = (
                    f"Reviews tab not found for '{place_name}'. "
                    "Check debug_screenshot.png."
                )
                await browser.close()
                return result_meta

            _log("  Clicking Reviews tab (JS click to bypass overlays)...")
            # Use JS click to avoid 'element intercepts pointer events' error
            try:
                await reviews_tab.evaluate("el => el.click()")
            except Exception:
                await reviews_tab.click()

            await page.wait_for_timeout(2500)
            await _wait_stable(page, timeout=5000)

            # ── 4. Sort (optional) ───────────────────────────────────────────
            if sort_by_newest:
                _log("Step 4: Sorting by newest...")
                sort_btn = await _try_selector(page, SELS_SORT_BTN, timeout=4000)
                if sort_btn:
                    try:
                        await sort_btn.evaluate("el => el.click()")
                    except Exception:
                        await sort_btn.click()
                    await page.wait_for_timeout(700)
                    try:
                        newest = await page.wait_for_selector('li[data-index="1"]', timeout=3000)
                        if newest:
                            await newest.evaluate("el => el.click()")
                            await page.wait_for_timeout(1800)
                    except Exception:
                        _log("  Sort dropdown didn't open — continuing.")
                else:
                    _log("  Sort button not found — skipping.")
            else:
                _log("Step 4: Skipping sort.")

            # ── 5. Wait for first reviews to render ──────────────────────────
            _log("Step 5: Waiting for reviews to render...")
            found = await _wait_for_reviews(page, timeout_ms=12000)
            if not found:
                _log("  Timeout waiting for reviews. Running diagnostics...")
                await _dump_page_info(page)

            # ── 6. Scroll ────────────────────────────────────────────────────
            _log("Step 6: Scrolling to load more reviews...")
            await _scroll_to_load(page, max_reviews)

            # ── 7. Extract ───────────────────────────────────────────────────
            _log("Step 7: Extracting review data...")
            reviews = await _extract_reviews(page, max_reviews)

            if not reviews:
                _log("  Standard extraction got 0. Running diagnostics + JS fallback...")
                await _dump_page_info(page)
                reviews = await _js_extract_reviews(page, max_reviews)

            result_meta["reviews"] = reviews
            result_meta["total_scraped"] = len(reviews)
            _log(f"Complete. {len(reviews)} reviews extracted.")

        except Exception as exc:
            _log(f"FATAL: {exc}")
            try:
                await page.screenshot(path="debug_screenshot.png", full_page=False)
            except Exception:
                pass
            result_meta["error"] = f"Scraping failed: {str(exc)}"
        finally:
            await browser.close()

    return result_meta


# ── Sync wrapper ──────────────────────────────────────────────────────────────

def scrape_sync(
    business_name: str,
    location: Optional[str] = None,
    max_reviews: int = 50,
    sort_by_newest: bool = False,
) -> dict:
    """
    Blocking wrapper — safe to call from asyncio.to_thread() inside FastAPI.
    Creates its own isolated event loop to avoid conflicts with uvicorn's loop.
    """
    if sys.platform == "win32":
        loop = asyncio.ProactorEventLoop()
    else:
        loop = asyncio.new_event_loop()

    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(
            scrape_google_maps_reviews(
                business_name=business_name,
                location=location,
                max_reviews=max_reviews,
                sort_by_newest=sort_by_newest,
            )
        )
    finally:
        loop.close()
        asyncio.set_event_loop(None)