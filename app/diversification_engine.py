from app.models import Asset
from app.overlap_engine import detect_overlap_between_assets
from app.classification_engine import classify_asset_detailed


def group_assets_by_similarity(assets: list[Asset]) -> list[list[Asset]]:
    groups = []

    for asset in assets:
        placed = False

        for group in groups:
            for member in group:
                overlap = detect_overlap_between_assets(asset, member)

                if overlap and overlap["score"] >= 60:
                    group.append(asset)
                    placed = True
                    break

            if placed:
                break

        if not placed:
            groups.append([asset])

    return groups


def summarize_groups(groups: list[list[Asset]]) -> list[dict]:
    summary = []

    for group in groups:
        total_value = sum(a.position.current_value for a in group)

        categories = list(set(
            classify_asset_detailed(a) for a in group
        ))

        summary.append({
            "size": len(group),
            "total_value": round(total_value, 2),
            "assets": [a.instrument.asset_name for a in group],
            "categories": categories,
        })

    summary.sort(key=lambda g: g["total_value"], reverse=True)
    return summary


def detect_fake_diversification(assets: list[Asset]) -> dict:
    if not assets:
        return {
            "num_assets": 0,
            "num_groups": 0,
            "groups": [],
            "warnings": [],
        }

    total_value = sum(a.position.current_value for a in assets)

    groups = group_assets_by_similarity(assets)
    group_summary = summarize_groups(groups)

    num_assets = len(assets)
    num_groups = len(groups)

    warnings = []

    # ⚠️ פיזור מדומה
    if num_assets >= 4 and num_groups <= 2:
        warnings.append("התיק כולל מספר נכסים אך בפועל יש מעט קבוצות חשיפה — פיזור מדומה.")

    # ⚠️ קבוצה דומיננטית
    largest_group_value = group_summary[0]["total_value"] if group_summary else 0
    largest_group_ratio = largest_group_value / total_value if total_value > 0 else 0

    if largest_group_ratio >= 0.60:
        warnings.append("רוב התיק מרוכז בקבוצת נכסים דומה — ריכוזיות גבוהה.")

    return {
        "num_assets": num_assets,
        "num_groups": num_groups,
        "groups": group_summary,
        "warnings": warnings,
    }

def get_asset_group_size(asset: Asset, assets: list[Asset]) -> int:
    groups = group_assets_by_similarity(assets)

    for group in groups:
        if asset in group:
            return len(group)

    return 1


def get_asset_diversification_penalty(asset: Asset, assets: list[Asset]) -> int:
    group_size = get_asset_group_size(asset, assets)

    if group_size >= 4:
        return 30
    elif group_size == 3:
        return 20
    elif group_size == 2:
        return 10
    return 0


def get_largest_group_ratio(assets: list[Asset]) -> float:
    if not assets:
        return 0.0

    total_value = sum(a.position.current_value for a in assets)
    if total_value == 0:
        return 0.0

    groups = group_assets_by_similarity(assets)
    largest_group_value = 0.0

    for group in groups:
        group_value = sum(a.position.current_value for a in group)
        if group_value > largest_group_value:
            largest_group_value = group_value

    return largest_group_value / total_value