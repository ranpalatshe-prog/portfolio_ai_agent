from app.models import Asset, InvestorProfile
from app.recommendation_engine import calculate_current_allocation
from app.classification_engine import classify_asset

def calculate_total_portfolio_value(assets: list[Asset]) -> float:
    return sum(asset.position.current_value for asset in assets)


def calculate_asset_weight(asset: Asset, total_value: float) -> float:
    if total_value == 0:
        return 0.0
    return asset.position.current_value / total_value


def calculate_portfolio_risk_metrics(assets: list[Asset]) -> dict[str, float]:
    total_value = calculate_total_portfolio_value(assets)

    if total_value == 0:
        return {
            "equity_exposure": 0.0,
            "fx_exposure": 0.0,
            "weighted_std_dev": 0.0,
            "weighted_sharpe": 0.0,
            "cash_ratio": 0.0,
            "largest_position_weight": 0.0,
        }

    total_equity_exposure = 0.0
    total_fx_exposure = 0.0
    weighted_std_dev = 0.0
    weighted_sharpe = 0.0
    largest_position_weight = 0.0
    cash_ratio = 0.0

    for asset in assets:
        weight = calculate_asset_weight(asset, total_value)

        total_equity_exposure += weight * asset.analytics.equity_exposure
        total_fx_exposure += weight * asset.analytics.fx_exposure
        weighted_std_dev += weight * asset.analytics.std_dev_12m
        weighted_sharpe += weight * asset.analytics.sharpe_ratio

        if weight > largest_position_weight:
            largest_position_weight = weight

        if classify_asset(asset) == "cash":
            cash_ratio += weight

    return {
        "equity_exposure": total_equity_exposure,
        "fx_exposure": total_fx_exposure,
        "weighted_std_dev": weighted_std_dev,
        "weighted_sharpe": weighted_sharpe,
        "cash_ratio": cash_ratio,
        "largest_position_weight": largest_position_weight,
    }


def assess_portfolio_risk_level(
    assets: list[Asset],
    investor: InvestorProfile,
) -> dict:
    metrics = calculate_portfolio_risk_metrics(assets)
    current_allocation = calculate_current_allocation(assets)

    warnings = []
    strengths = []

    if metrics["equity_exposure"] > 0.75:
        warnings.append("חשיפה מנייתית גבוהה מאוד בתיק.")
    elif metrics["equity_exposure"] < 0.30:
        warnings.append("חשיפה מנייתית נמוכה יחסית, ייתכן שהתיק שמרני מדי.")

    if metrics["cash_ratio"] < 0.05:
        warnings.append("רכיב המזומן נמוך מאוד.")
    elif metrics["cash_ratio"] >= 0.10:
        strengths.append("יש בתיק כרית מזומן סבירה.")

    if metrics["largest_position_weight"] > 0.40:
        warnings.append("יש נכס בודד שתופס משקל גבוה מאוד בתיק.")
    elif metrics["largest_position_weight"] < 0.20:
        strengths.append("אין ריכוזיות גבוהה בנכס בודד.")

    if metrics["weighted_std_dev"] > 0.14:
        warnings.append("סטיית התקן המשוקללת של התיק גבוהה יחסית.")
    elif metrics["weighted_std_dev"] < 0.08:
        strengths.append("סטיית התקן המשוקללת של התיק יחסית נמוכה.")

    if metrics["weighted_sharpe"] > 0.75:
        strengths.append("יחס שארפ משוקלל טוב יחסית.")
    elif metrics["weighted_sharpe"] < 0.30:
        warnings.append("יחס שארפ משוקלל נמוך יחסית.")

    overall_risk_score = 0

    overall_risk_score += metrics["equity_exposure"] * 40
    overall_risk_score += metrics["weighted_std_dev"] * 100
    overall_risk_score += metrics["largest_position_weight"] * 30
    overall_risk_score += metrics["fx_exposure"] * 10
    overall_risk_score -= metrics["cash_ratio"] * 15
    overall_risk_score -= metrics["weighted_sharpe"] * 10

    if overall_risk_score < 20:
        overall_risk_label = "low"
    elif overall_risk_score < 35:
        overall_risk_label = "medium"
    else:
        overall_risk_label = "high"

    return {
        "metrics": metrics,
        "current_allocation": current_allocation,
        "overall_risk_score": round(overall_risk_score, 2),
        "overall_risk_label": overall_risk_label,
        "warnings": warnings,
        "strengths": strengths,
    }