import json

from app.models import Asset, InvestorProfile
from app.portfolio_engine import (
    calculate_total_value,
    calculate_asset_weight,
    calculate_profit_loss,
    calculate_profit_loss_percent,
    calculate_total_equity_exposure,
    calculate_total_fx_exposure,
)
from app.recommendation_engine import (
    get_target_allocation,
    calculate_current_allocation,
    recommend_new_cash_allocation,
    recommend_specific_assets,
    generate_hold_reduce_recommendations,
    classify_asset_detailed,
)

from app.recommendation_engine import classify_asset_detailed

from app.risk_engine import assess_portfolio_risk_level

def load_portfolio(path: str) -> list[Asset]:
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)
    return [Asset(**item) for item in data]


def load_investor_profile(path: str) -> InvestorProfile:
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)
    return InvestorProfile(**data)

def main():
    assets = load_portfolio("data/portfolio.json")
    investor = load_investor_profile("data/investor_profile.json")

    total_value = calculate_total_value(assets)
    total_equity_exposure = calculate_total_equity_exposure(assets, total_value)
    total_fx_exposure = calculate_total_fx_exposure(assets, total_value)

    target_allocation = get_target_allocation(
        investor.risk_level,
        investor.investment_horizon_years,
        investor,
    )
    current_allocation = calculate_current_allocation(assets)
    new_cash_recommendation = recommend_new_cash_allocation(assets, investor)
    specific_recommendations = recommend_specific_assets(assets, investor)
    hold_reduce_recommendations = generate_hold_reduce_recommendations(assets, investor)
    risk_report = assess_portfolio_risk_level(assets, investor)

    print("------ Portfolio Summary ------")
    print(f"Risk Level: {investor.risk_level}")
    print(f"Investment Horizon: {investor.investment_horizon_years} years")
    print(f"Monthly New Cash: {investor.monthly_new_cash:,.2f} {investor.base_currency}")
    print(f"Total Portfolio Value: {total_value:,.2f} {investor.base_currency}")
    print(f"Total Equity Exposure: {total_equity_exposure:.2%}")
    print(f"Total FX Exposure: {total_fx_exposure:.2%}")
    print()

    print("------ Risk Report ------")
    print(f"Overall Risk Score: {risk_report['overall_risk_score']}")
    print(f"Overall Risk Label: {risk_report['overall_risk_label']}")
    print(f"Equity Exposure: {risk_report['metrics']['equity_exposure']:.2%}")
    print(f"FX Exposure: {risk_report['metrics']['fx_exposure']:.2%}")
    print(f"Weighted Std Dev: {risk_report['metrics']['weighted_std_dev']:.2%}")
    print(f"Weighted Sharpe: {risk_report['metrics']['weighted_sharpe']:.2f}")
    print(f"Cash Ratio: {risk_report['metrics']['cash_ratio']:.2%}")
    print(f"Largest Position Weight: {risk_report['metrics']['largest_position_weight']:.2%}")
    print()

    print("Warnings:")
    if risk_report["warnings"]:
        for warning in risk_report["warnings"]:
            print(f"- {warning}")
    else:
        print("- אין אזהרות מיוחדות.")
    print()

    print("Strengths:")
    if risk_report["strengths"]:
        for strength in risk_report["strengths"]:
            print(f"- {strength}")
    else:
        print("- אין נקודות חוזק מיוחדות.")
    print()

    print("------ Allocation ------")
    print(f"Target Allocation: {target_allocation}")
    print(f"Current Allocation: {current_allocation}")
    print()

    print("------ New Cash Recommendation ------")
    for category, amount in new_cash_recommendation.items():
        print(f"{category}: {amount:,.2f} {investor.base_currency}")
    print()

    print("------ Specific Asset Recommendations ------")
    for recommendation in specific_recommendations:
        action = recommendation["action"]
        category = recommendation["category"]
        asset_name = recommendation["asset_name"]
        amount = recommendation["amount"]
        score = recommendation["score"]
        reason = recommendation["reason"]

        print(f"Action: {action}")
        print(f"Category: {category}")
        if asset_name:
            print(f"Asset Name: {asset_name}")
        print(f"Amount: {amount:,.2f} {investor.base_currency}")
        if score is not None:
            print(f"Score: {score}")
        print(f"Reason: {reason}")
        print("-" * 30)

    print("------ Hold / Reduce Recommendations ------")
    for recommendation in hold_reduce_recommendations:
        action = recommendation["action"]
        category = recommendation["category"]
        asset_name = recommendation["asset_name"]
        amount = recommendation["amount"]
        score = recommendation["score"]
        reason = recommendation["reason"]

        print(f"Action: {action}")
        print(f"Category: {category}")
        print(f"Asset Name: {asset_name}")
        if amount > 0:
            print(f"Suggested Reduce Amount: {amount:,.2f} {investor.base_currency}")
        if score is not None:
            print(f"Score: {score}")
        print(f"Reason: {reason}")
        print("-" * 30)

    print("------ Assets ------")
    for asset in assets:
        weight = calculate_asset_weight(asset, total_value)
        profit_loss = calculate_profit_loss(asset)
        profit_loss_percent = calculate_profit_loss_percent(asset)

        detailed_category = classify_asset_detailed(asset)

        print(f"Name: {asset.instrument.asset_name}")
        print(f"Type: {asset.instrument.asset_type}")
        print(f"Detailed Category: {detailed_category}")
        print(f"Current Value: {asset.position.current_value:,.2f} {asset.instrument.currency}")
        print(f"Weight in Portfolio: {weight:.2%}")
        print(f"Profit / Loss: {profit_loss:,.2f} {asset.instrument.currency}")
        print(f"Profit / Loss %: {profit_loss_percent:.2%}")
        print("-" * 30)

    print("------ Investor Constraints ------")
    print(f"Allow Equity: {investor.allow_equity}")
    print(f"Allow Bond: {investor.allow_bond}")
    print(f"Allow Cash: {investor.allow_cash}")
    print(f"Allow Crypto: {investor.allow_crypto}")
    print(f"Allow Real Estate: {investor.allow_real_estate}")
    print(f"Prefers Passive Funds: {investor.prefers_passive_funds}")
    print()

if __name__ == "__main__":
    main()