import re
from typing import Optional

import httpx
from bs4 import BeautifulSoup


def _extract_number(text: str) -> Optional[float]:
    if not text:
        return None

    cleaned = text.replace(",", "").replace("%", "").strip()
    match = re.search(r"-?\d+(?:\.\d+)?", cleaned)
    if not match:
        return None

    try:
        return float(match.group(0))
    except ValueError:
        return None


def _clean_asset_name(asset_name: Optional[str]) -> Optional[str]:
    if not asset_name:
        return None

    if "|" in asset_name:
        asset_name = asset_name.split("|")[0]

    stop_words = [
        "ביזפורטל",
        "דף",
        "לתפריט",
        "לתקנון",
        "ותנאי",
        "שימוש",
        "נתוני מסחר",
        "פרטיות",
    ]

    for word in stop_words:
        if word in asset_name:
            asset_name = asset_name.split(word)[0]
            break

    asset_name = re.sub(r"\s+", " ", asset_name).strip()

    return asset_name or None


async def fetch_market_data_from_bizportal(security_number: str) -> Optional[dict]:
    url = f"https://www.bizportal.co.il/mutualfunds/quote/generalview/{security_number}"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "he-IL,he;q=0.9,en;q=0.8",
    }

    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        response = await client.get(url, headers=headers)

    if response.status_code != 200:
        return None

    html = response.text
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)

    # שם הנכס
    asset_name = None

    # קודם מנסים לחלץ שם שמתחיל ב-MTF וכולל גם מקפים ומספרים
    match = re.search(
        r"(MTF[\u0590-\u05FFA-Za-z0-9\s\-\"'/]*?\d+(?:-\d+)?)",
        text
    )
    if match:
        asset_name = match.group(1).strip()

    # fallback לכותרת הדף - בלי לחתוך לפי מקף
    if not asset_name:
        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        if title:
            asset_name = title.strip()

    # fallback נוסף
    if not asset_name:
        name_match = re.search(r"^\s*(.*?)\s+מחיר פדיון", text)
        if name_match:
            asset_name = name_match.group(1).strip()

    asset_name = _clean_asset_name(asset_name)

    # מחיר נוכחי
    price_match = re.search(r"מחיר פדיון\s+([0-9\.,]+)", text)
    current_price = _extract_number(price_match.group(1)) if price_match else None

    if current_price is None:
        price_match = re.search(r"מחיר קנייה\s+([0-9\.,]+)", text)
        current_price = _extract_number(price_match.group(1)) if price_match else None

    # שינוי יומי באחוזים
    change_match = re.search(r"מחיר קנייה\s+[0-9\.,]+\s+([+\-]?[0-9\.,]+%)", text)
    daily_change_percent = _extract_number(change_match.group(1)) if change_match else None

    if daily_change_percent is None:
        percent_match = re.search(r"\b([+\-]?[0-9\.,]+%)\b", text)
        daily_change_percent = _extract_number(percent_match.group(1)) if percent_match else None

    if current_price is None:
        return None

    previous_price = None
    if daily_change_percent is not None:
        try:
            previous_price = current_price / (1 + (daily_change_percent / 100))
        except ZeroDivisionError:
            previous_price = None

    return {
        "security_number": security_number,
        "asset_name": asset_name,
        "current_price": current_price,
        "previous_price": round(previous_price, 4) if previous_price is not None else None,
        "daily_change_percent": daily_change_percent,
        "source": "bizportal",
    }


async def fetch_market_data(security_number: str) -> Optional[dict]:
    security_number = (security_number or "").strip()
    if not security_number:
        return None

    data = await fetch_market_data_from_bizportal(security_number)
    return data