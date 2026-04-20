from app.models import Asset
from app.classification_engine import classify_asset_detailed, classify_asset

def get_asset_overlap_penalty(asset: Asset, assets: list[Asset]) -> int:
    penalty = 0

    for other in assets:
        if other is asset:
            continue

        overlap = detect_overlap_between_assets(asset, other)
        if not overlap:
            continue

        if overlap["severity"] == "high":
            penalty += 25
        elif overlap["severity"] == "medium":
            penalty += 15
        else:
            penalty += 5

    return penalty


def get_most_overlapped_assets(assets: list[Asset]) -> dict[str, int]:
    penalty_map = {}

    for asset in assets:
        penalty_map[asset.instrument.asset_name] = get_asset_overlap_penalty(asset, assets)

    return penalty_map
def normalize_text(value: str) -> str:
    return (value or "").strip().lower()


def get_asset_signature(asset: Asset) -> dict:
    asset_name = normalize_text(asset.instrument.asset_name)
    asset_type = normalize_text(asset.instrument.asset_type)
    classification = normalize_text(asset.instrument.classification)

    detailed_category = classify_asset_detailed(asset)

    return {
        "name": asset_name,
        "type": asset_type,
        "classification": classification,
        "category": detailed_category,
        "equity_exposure": asset.analytics.equity_exposure,
        "fx_exposure": asset.analytics.fx_exposure,
        "management_fee": asset.analytics.management_fee,
    }


def text_similarity_hint(name_a: str, name_b: str) -> bool:
    keywords = [
        "s&p",
        "s&p500",
        "sp500",
        "nasdaq",
        "תא",
        "ta35",
        "index",
        "index_fund",
        "bond",
        "אגח",
        "reit",
        "global",
        "world",
        "emerging",
    ]

    for keyword in keywords:
        if keyword in name_a and keyword in name_b:
            return True

    return False


def detect_overlap_between_assets(asset_a: Asset, asset_b: Asset) -> dict | None:
    sig_a = get_asset_signature(asset_a)
    sig_b = get_asset_signature(asset_b)

    same_category = sig_a["category"] == sig_b["category"]
    same_classification = sig_a["classification"] and sig_a["classification"] == sig_b["classification"]

    equity_gap = abs(sig_a["equity_exposure"] - sig_b["equity_exposure"])
    fx_gap = abs(sig_a["fx_exposure"] - sig_b["fx_exposure"])

    similar_exposure = equity_gap <= 0.15 and fx_gap <= 0.20
    similar_name = text_similarity_hint(sig_a["name"], sig_b["name"])

    score = 0

    if same_category:
        score += 30

    if same_classification:
        score += 30

    if similar_exposure:
        score += 25

    if similar_name:
        score += 15

    if score < 40:
        return None

    if score >= 80:
        severity = "high"
        explanation = "קיימת סבירות גבוהה לכפילות או חפיפה חזקה בין שני הנכסים."
    elif score >= 60:
        severity = "medium"
        explanation = "נראה שיש חפיפה משמעותית בין שני הנכסים."
    else:
        severity = "low"
        explanation = "ייתכן שקיימת חפיפה חלקית בין שני הנכסים."

    return {
        "asset_1": asset_a.instrument.asset_name,
        "asset_2": asset_b.instrument.asset_name,
        "category_1": sig_a["category"],
        "category_2": sig_b["category"],
        "classification_1": sig_a["classification"],
        "classification_2": sig_b["classification"],
        "equity_gap": round(equity_gap, 4),
        "fx_gap": round(fx_gap, 4),
        "score": score,
        "severity": severity,
        "explanation": explanation,
    }


def detect_portfolio_overlaps(assets: list[Asset]) -> list[dict]:
    overlaps = []

    for i in range(len(assets)):
        for j in range(i + 1, len(assets)):
            overlap = detect_overlap_between_assets(assets[i], assets[j])
            if overlap:
                overlaps.append(overlap)

    overlaps.sort(key=lambda item: item["score"], reverse=True)
    return overlaps