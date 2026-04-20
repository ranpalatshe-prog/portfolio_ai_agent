from app.models import Asset, InvestorProfile
from app.overlap_engine import get_asset_overlap_penalty
from app.diversification_engine import get_asset_diversification_penalty
from app.classification_engine import classify_asset, classify_asset_detailed

def get_allowed_categories(investor: InvestorProfile) -> dict[str, bool]:
    return {
        "equity": investor.allow_equity,
        "bond": investor.allow_bond,
        "cash": investor.allow_cash,
        "crypto": investor.allow_crypto,
        "real_estate": investor.allow_real_estate,
    }

def get_target_allocation(
    risk_level: str,
    investment_horizon_years: int,
    investor: InvestorProfile,
) -> dict[str, float]:
    if risk_level == "low":
        allocation = {
            "equity": 0.30,
            "bond": 0.50,
            "cash": 0.20,
        }
    elif risk_level == "medium":
        allocation = {
            "equity": 0.60,
            "bond": 0.30,
            "cash": 0.10,
        }
    elif risk_level == "high":
        allocation = {
            "equity": 0.80,
            "bond": 0.15,
            "cash": 0.05,
        }
    else:
        allocation = {
            "equity": 0.60,
            "bond": 0.30,
            "cash": 0.10,
        }

    if investment_horizon_years <= 3:
        allocation["equity"] -= 0.20
        allocation["bond"] += 0.10
        allocation["cash"] += 0.10
    elif investment_horizon_years <= 7:
        allocation["equity"] -= 0.10
        allocation["bond"] += 0.05
        allocation["cash"] += 0.05
    elif investment_horizon_years >= 15:
        allocation["equity"] += 0.10
        allocation["bond"] -= 0.05
        allocation["cash"] -= 0.05

    for key in allocation:
        if allocation[key] < 0:
            allocation[key] = 0

    allowed_categories = get_allowed_categories(investor)

    for category in list(allocation.keys()):
        if not allowed_categories.get(category, False):
            allocation[category] = 0

    total = sum(allocation.values())
    if total > 0:
        for key in allocation:
            allocation[key] = allocation[key] / total

    return allocation

    # תיקון כדי שלא יהיו ערכים שליליים
    for key in allocation:
        if allocation[key] < 0:
            allocation[key] = 0

    # נרמול כדי שהסכום יהיה 1.0
    total = sum(allocation.values())
    if total > 0:
        for key in allocation:
            allocation[key] = allocation[key] / total

    return allocation

def calculate_current_allocation(assets: list[Asset]) -> dict[str, float]:
    total_value = sum(asset.position.current_value for asset in assets)

    if total_value == 0:
        return {"equity": 0, "bond": 0, "cash": 0}

    allocation = {"equity": 0, "bond": 0, "cash": 0}

    for asset in assets:
        category = classify_asset(asset)
        allocation[category] += asset.position.current_value / total_value

    return allocation


def calculate_asset_weight(asset: Asset, assets: list[Asset]) -> float:
    total_value = sum(item.position.current_value for item in assets)
    if total_value == 0:
        return 0
    return asset.position.current_value / total_value


def recommend_new_cash_allocation(
    assets: list[Asset],
    investor: InvestorProfile,
) -> dict[str, float]:
    target = get_target_allocation(
        investor.risk_level,
        investor.investment_horizon_years,
        investor,
    )
    current = calculate_current_allocation(assets)

    gaps = {}
    for category in target:
        gaps[category] = max(target[category] - current.get(category, 0), 0)

    total_gap = sum(gaps.values())

    if total_gap == 0:
        return {"equity": 0, "bond": 0, "cash": 0}

    recommendations = {}
    for category, gap in gaps.items():
        recommendations[category] = (gap / total_gap) * investor.monthly_new_cash

    return recommendations


def find_assets_by_category(assets: list[Asset], category: str) -> list[Asset]:
    matching_assets = []

    for asset in assets:
        if classify_asset(asset) == category:
            matching_assets.append(asset)

    return matching_assets


def score_asset(asset: Asset, all_assets: list[Asset] | None = None) -> float:
    score = 0.0

    score += asset.analytics.return_3y * 40
    score += asset.analytics.return_12m * 20
    score += asset.analytics.sharpe_ratio * 25
    score -= asset.analytics.std_dev_12m * 15
    score -= asset.analytics.management_fee * 100

    if all_assets is not None:
        overlap_penalty = get_asset_overlap_penalty(asset, all_assets)
        diversification_penalty = get_asset_diversification_penalty(asset, all_assets)

        score -= overlap_penalty
        score -= diversification_penalty

    return score

def choose_best_asset(candidate_assets: list[Asset], all_assets: list[Asset]) -> Asset:
    return max(candidate_assets, key=lambda asset: score_asset(asset, all_assets))

def recommend_specific_assets(
    assets: list[Asset],
    investor: InvestorProfile,
) -> list[dict]:
    category_recommendations = recommend_new_cash_allocation(assets, investor)
    recommendations = []

    for category, amount in category_recommendations.items():
        if amount <= 0:
            continue

        matching_assets = find_assets_by_category(assets, category)

        if matching_assets:
            chosen_asset = choose_best_asset(matching_assets, assets)
            asset_score = score_asset(chosen_asset, assets)
            overlap_penalty = get_asset_overlap_penalty(chosen_asset, assets)
            diversification_penalty = get_asset_diversification_penalty(chosen_asset, assets)

            recommendations.append({
                "action": "buy",
                "category": category,
                "asset_name": chosen_asset.instrument.asset_name,
                "amount": round(amount, 2),
                "score": round(asset_score, 2),
                "overlap_penalty": overlap_penalty,
                "diversification_penalty": diversification_penalty,
                "reason": f"הנכס נבחר בקטגוריית {category} לפי איכות, חפיפה, ופיזור אמיתי בתיק."
            })
        else:
            recommendations.append({
                "action": "add_new_asset",
                "category": category,
                "asset_name": None,
                "amount": round(amount, 2),
                "score": None,
                "reason": f"אין כרגע נכס מסוג {category} בתיק, ולכן צריך להוסיף נכס חדש."
            })

    return recommendations


def generate_hold_reduce_recommendations(
    assets: list[Asset],
    investor: InvestorProfile,
) -> list[dict]:
    recommendations = []

    target_allocation = get_target_allocation(
        investor.risk_level,
        investor.investment_horizon_years,
        investor,
    )
    current_allocation = calculate_current_allocation(assets)

    for asset in assets:
        category = classify_asset(asset)
        asset_weight = calculate_asset_weight(asset, assets)
        asset_score = score_asset(asset, assets)
        overlap_penalty = get_asset_overlap_penalty(asset, assets)
        diversification_penalty = get_asset_diversification_penalty(asset, assets)
        

        category_target = target_allocation.get(category, 0)
        category_current = current_allocation.get(category, 0)

        is_category_overweight = category_current > category_target + 0.10
        is_asset_too_large = asset_weight > 0.40
        is_low_quality = asset_score < 5
        has_high_overlap = overlap_penalty >= 25
        has_fake_diversification_signal = diversification_penalty >= 20

        if is_category_overweight and is_asset_too_large:
            recommendations.append({
                "action": "reduce",
                "category": category,
                "asset_name": asset.instrument.asset_name,
                "amount": round(asset.position.current_value * 0.10, 2),
                "score": round(asset_score, 2),
                "overlap_penalty": overlap_penalty,
                "diversification_penalty": diversification_penalty,
                "reason": "הנכס מהווה משקל גבוה מדי בתיק, הקטגוריה שלו בעודף, ונלקחו בחשבון גם חפיפה ופיזור מדומה."
            })
        elif (
            (is_low_quality and is_category_overweight)
            or (has_high_overlap and is_category_overweight)
            or (has_fake_diversification_signal and is_category_overweight)
        ):
            recommendations.append({
                "action": "reduce",
                "category": category,
                "asset_name": asset.instrument.asset_name,
                "amount": round(asset.position.current_value * 0.05, 2),
                "score": round(asset_score, 2),
                "overlap_penalty": overlap_penalty,
                "diversification_penalty": diversification_penalty,
                "reason": "הנכס מקבל ציון נמוך יחסית, או חופף לנכסים אחרים, או יוצר פיזור מדומה בתוך קטגוריה שנמצאת בעודף."
            })
            recommendations.append({
                "action": "hold",
                "category": category,
                "asset_name": asset.instrument.asset_name,
                "amount": 0,
                "score": round(asset_score, 2),
                "overlap_penalty": overlap_penalty,
                "diversification_penalty": diversification_penalty,
                "reason": "הנכס מתאים כרגע להחזקה, לאחר שקלול איכות, חפיפה ופיזור אמיתי."
            })

    return recommendations