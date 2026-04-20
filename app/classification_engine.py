from app.models import Asset


def classify_asset_detailed(asset: Asset) -> str:
    asset_type = asset.instrument.asset_type.lower()
    asset_name = asset.instrument.asset_name.lower()
    classification = asset.instrument.classification.lower()

    equity_exposure = asset.analytics.equity_exposure
    fx_exposure = asset.analytics.fx_exposure

    if "crypto" in asset_type or "crypto" in classification:
        return "crypto"

    if "real_estate" in asset_type or "reit" in asset_type or "real_estate" in classification:
        return "real_estate"

    if "cash" in asset_type or "money_market" in classification:
        return "cash"

    if "bond" in asset_type or "אג" in asset_name or "bond" in classification:
        if equity_exposure <= 0.20:
            return "bond"
        return "mixed"

    if asset_type in ["stock", "equity", "etf"]:
        if equity_exposure >= 0.80:
            return "equity"
        elif equity_exposure >= 0.30:
            return "mixed"
        else:
            return "bond"

    if asset_type in ["mutual_fund", "fund"]:
        if equity_exposure >= 0.80:
            return "equity"
        elif equity_exposure >= 0.30:
            return "mixed"
        elif equity_exposure > 0:
            return "bond"
        else:
            return "cash"

    if equity_exposure >= 0.80:
        return "equity"
    elif equity_exposure >= 0.30:
        return "mixed"
    elif equity_exposure > 0:
        return "bond"

    if fx_exposure == 0 and asset.analytics.std_dev_12m < 0.02:
        return "cash"

    return "equity"


def classify_asset(asset: Asset) -> str:
    detailed_category = classify_asset_detailed(asset)

    if detailed_category == "mixed":
        if asset.analytics.equity_exposure >= 0.50:
            return "equity"
        return "bond"

    if detailed_category in ["crypto", "real_estate"]:
        return "equity"

    return detailed_category