from app.models import Asset


def calculate_total_value(assets: list[Asset]) -> float:
    return sum(asset.position.current_value for asset in assets)


def calculate_asset_weight(asset: Asset, total_value: float) -> float:
    if total_value == 0:
        return 0
    return asset.position.current_value / total_value


def calculate_profit_loss(asset: Asset) -> float:
    return asset.position.current_value - asset.position.cost_basis


def calculate_profit_loss_percent(asset: Asset) -> float:
    if asset.position.cost_basis == 0:
        return 0
    return (asset.position.current_value - asset.position.cost_basis) / asset.position.cost_basis


def calculate_total_equity_exposure(assets: list[Asset], total_value: float) -> float:
    if total_value == 0:
        return 0

    total_equity = 0
    for asset in assets:
        asset_weight = asset.position.current_value / total_value
        total_equity += asset_weight * asset.analytics.equity_exposure

    return total_equity


def calculate_total_fx_exposure(assets: list[Asset], total_value: float) -> float:
    if total_value == 0:
        return 0

    total_fx = 0
    for asset in assets:
        asset_weight = asset.position.current_value / total_value
        total_fx += asset_weight * asset.analytics.fx_exposure

    return total_fx