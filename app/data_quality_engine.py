from app.models import Asset


def check_asset_data_quality(asset: Asset) -> dict:
    flags = []
    penalty = 0

    name = asset.instrument.asset_name

    quantity = asset.position.quantity
    current_price = asset.position.current_price
    current_value = asset.position.current_value
    avg_buy_price = asset.position.avg_buy_price
    cost_basis = asset.position.cost_basis

    equity_exposure = asset.analytics.equity_exposure
    fx_exposure = asset.analytics.fx_exposure
    std_dev = asset.analytics.std_dev_12m
    sharpe = asset.analytics.sharpe_ratio
    return_12m = asset.analytics.return_12m
    return_3y = asset.analytics.return_3y
    management_fee = asset.analytics.management_fee

    # שדות חסרים / ריקים
    if not asset.instrument.asset_name.strip():
        flags.append("חסר שם נכס.")
        penalty += 20

    if not asset.instrument.asset_type.strip():
        flags.append("חסר סוג נכס.")
        penalty += 15

    # ערכים שליליים
    if quantity < 0 or current_price < 0 or current_value < 0 or avg_buy_price < 0 or cost_basis < 0:
        flags.append("יש ערך שלילי בשדות הפוזיציה.")
        penalty += 25

    # התאמת שווי נוכחי
    expected_current_value = quantity * current_price
    if abs(current_value - expected_current_value) > max(1.0, expected_current_value * 0.03):
        flags.append("השווי הנוכחי אינו תואם בקירוב לכמות כפול מחיר נוכחי.")
        penalty += 10

    # התאמת בסיס עלות
    expected_cost_basis = quantity * avg_buy_price
    if abs(cost_basis - expected_cost_basis) > max(1.0, expected_cost_basis * 0.03):
        flags.append("בסיס העלות אינו תואם בקירוב לכמות כפול מחיר קנייה ממוצע.")
        penalty += 10

    # טווחי חשיפה
    if not (0 <= equity_exposure <= 1):
        flags.append("חשיפה למניות אינה בטווח 0 עד 1.")
        penalty += 15

    if not (0 <= fx_exposure <= 1):
        flags.append("חשיפה למט\"ח אינה בטווח 0 עד 1.")
        penalty += 15

    # מדדי סיכון/ביצועים חריגים
    if std_dev < 0 or std_dev > 1.5:
        flags.append("סטיית התקן נראית חריגה.")
        penalty += 10

    if sharpe < -5 or sharpe > 5:
        flags.append("מדד שארפ נראה חריג.")
        penalty += 10

    if return_12m < -1 or return_12m > 5:
        flags.append("תשואת 12 חודשים נראית חריגה.")
        penalty += 10

    if return_3y < -1 or return_3y > 10:
        flags.append("תשואת 3 שנים נראית חריגה.")
        penalty += 10

    if management_fee < 0 or management_fee > 0.1:
        flags.append("דמי הניהול נראים חריגים.")
        penalty += 10

    return {
        "asset_name": name,
        "flags": flags,
        "penalty": penalty,
        "is_clean": len(flags) == 0,
    }


def evaluate_portfolio_data_quality(assets: list[Asset]) -> dict:
    asset_reports = [check_asset_data_quality(asset) for asset in assets]

    total_flags = sum(len(report["flags"]) for report in asset_reports)
    total_penalty = sum(report["penalty"] for report in asset_reports)

    warnings = []
    if total_flags == 0:
        warnings.append("לא זוהו בעיות איכות נתונים מהותיות בתיק.")
    else:
        warnings.append(f"זוהו {total_flags} דגלי איכות נתונים בכלל התיק.")

    if total_penalty >= 40:
        quality_label = "low"
    elif total_penalty >= 15:
        quality_label = "medium"
    else:
        quality_label = "high"

    return {
        "quality_label": quality_label,
        "total_flags": total_flags,
        "total_penalty": total_penalty,
        "warnings": warnings,
        "assets": asset_reports,
    }


def get_asset_data_quality_penalty(asset_name: str, data_quality_report: dict) -> int:
    for item in data_quality_report.get("assets", []):
        if item.get("asset_name") == asset_name:
            return item.get("penalty", 0)
    return 0


def get_asset_data_quality_flags(asset_name: str, data_quality_report: dict) -> list[str]:
    for item in data_quality_report.get("assets", []):
        if item.get("asset_name") == asset_name:
            return item.get("flags", [])
    return []