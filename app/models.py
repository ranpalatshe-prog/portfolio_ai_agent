from pydantic import BaseModel


class Position(BaseModel):
    quantity: float
    current_price: float
    current_value: float
    avg_buy_price: float
    cost_basis: float


class Instrument(BaseModel):
    asset_name: str
    asset_type: str
    security_number: str
    exchange: str
    currency: str
    classification: str = ""


class Analytics(BaseModel):
    equity_exposure: float
    fx_exposure: float
    std_dev_12m: float
    sharpe_ratio: float
    return_12m: float
    return_3y: float
    management_fee: float


class Asset(BaseModel):
    position: Position
    instrument: Instrument
    analytics: Analytics


class InvestorProfile(BaseModel):
    risk_level: str
    investment_horizon_years: int
    monthly_new_cash: float
    tax_sensitive: bool
    base_currency: str

    allow_equity: bool = True
    allow_bond: bool = True
    allow_cash: bool = True
    allow_crypto: bool = False
    allow_real_estate: bool = False
    prefers_passive_funds: bool = True

class PortfolioRequest(BaseModel):
    assets: list[Asset]
    investor: InvestorProfile