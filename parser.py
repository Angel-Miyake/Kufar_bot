import re
import json
import os
import sys
import shutil
import subprocess
import hashlib
from playwright.async_api import async_playwright

BASE_DOMAIN = "https://www.kufar.by"

ANCHOR_FILE = "anchors.json"


def _url_key(url: str):
    return hashlib.md5(url.encode()).hexdigest()


def load_anchors():
    if not os.path.exists(ANCHOR_FILE):
        return {}
    with open(ANCHOR_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_anchors(data):
    with open(ANCHOR_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)


def get_anchor(url):
    return load_anchors().get(_url_key(url))


def set_anchor(url, anchor):
    data = load_anchors()
    data[_url_key(url)] = anchor
    save_anchors(data)


def extract_id(link: str):
    if not link:
        return None
    m = re.search(r"/(?:item|vi)/(\d+)", link)
    return m.group(1) if m else None


def build_link(item_id):
    return f"{BASE_DOMAIN}/item/{item_id}"


def parse_price(text: str):
    if not text:
        return None

    text = text.lower()

    if any(x in text for x in ["договор", "free", "бесплат", "обмен"]):
        return None

    compact = re.sub(r"(?<=[\d])[ \u00a0](?=[\d])", "", text)

    nums = re.findall(r"\d[\d ]*\d|\d", compact)
    values = []
    for n in nums:
        n = n.replace(" ", "").replace("\u00a0", "")
        try:
            v = float(n)
            if 10 <= v <= 10000000:
                values.append(v)
        except:
            pass

    if not values:
        return None

    return max(values)


async def get_price(el):
    try:
        txt = await el.inner_text()
        return parse_price(txt)
    except:
        return None


async def fetch_ads_playwright(url: str):

    ads = []

    last_anchor = get_anchor(url)
    new_anchor = None

    async with async_playwright() as p:

        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            await page.goto(url, timeout=30000)
            await page.wait_for_timeout(2000)

            for _ in range(3):
                await page.mouse.wheel(0, 3000)
                await page.wait_for_timeout(500)

            elements = await page.query_selector_all(
                "a[href*='/item/'], a[href*='/vi/']"
            )

            seen = set()
            clean = []

            for el in elements:
                href = await el.get_attribute("href")
                item_id = extract_id(href)

                if not item_id or item_id in seen:
                    continue

                seen.add(item_id)
                clean.append((el, item_id))

            clean = clean[:20]

            if not clean:
                return []

            for i, (el, item_id) in enumerate(clean):

                if last_anchor is not None and item_id == last_anchor:
                    break

                if i == 0:
                    new_anchor = item_id

                text = (await el.inner_text()).strip()
                if not text:
                    continue

                price = await get_price(el)

                ads.append({
                    "id": item_id,
                    "text": text,
                    "link": build_link(item_id),
                    "price": price
                })

        finally:
            await browser.close()

    if new_anchor:
        set_anchor(url, new_anchor)

    return ads


def ensure_browser():
    possible_dirs = [
        os.path.join(os.path.expanduser("~"), ".cache", "ms-playwright"),
        os.path.join(os.path.expandvars("%LOCALAPPDATA%"), "ms-playwright"),
    ]
    chromium_present = False
    for cache_dir in possible_dirs:
        if os.path.isdir(cache_dir):
            for name in os.listdir(cache_dir):
                if name.startswith("chromium"):
                    chromium_present = True
                    break
        if chromium_present:
            break
    if not chromium_present:
        if shutil.which("playwright"):
            subprocess.run(["playwright", "install", "chromium"], check=False)
        else:
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=False)
