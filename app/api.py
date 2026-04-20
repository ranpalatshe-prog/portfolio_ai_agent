from fastapi import FastAPI
from fastapi.responses import FileResponse
from app.overlap_engine import detect_portfolio_overlaps
from app.diversification_engine import detect_fake_diversification
from app.explanation_engine import generate_portfolio_explanation
from app.recommendation_explainer import explain_single_recommendation
from app.confidence_engine import calculate_recommendation_confidence
from app.data_quality_engine import evaluate_portfolio_data_quality, get_asset_data_quality_penalty, get_asset_data_quality_flags
from copy import deepcopy
from fastapi import FastAPI, Body, Query
from app.client_report_engine import build_client_report
from app.ai_explainer import generate_ai_client_summary
from app.fx_service import get_fx_rate_to_ils
from app.market_data_service import fetch_market_data
from fastapi import HTTPException
import os
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import secrets

from app.models import PortfolioRequest
from app.portfolio_engine import (
    calculate_total_value,
    calculate_total_equity_exposure,
    calculate_total_fx_exposure,
    calculate_asset_weight,
    calculate_profit_loss,
    calculate_profit_loss_percent,
)
from app.recommendation_engine import (
    get_target_allocation,
    calculate_current_allocation,
    recommend_new_cash_allocation,
    recommend_specific_assets,
    generate_hold_reduce_recommendations,
)
from app.classification_engine import classify_asset_detailed

from app.risk_engine import assess_portfolio_risk_level

app = FastAPI(title="Portfolio AI Agent")

import os

USERS = {
    os.getenv("ranpalatshe@gmail.com", "").lower(): {
        "password": os.getenv("Rd!0507821117", ""),
        "name": os.getenv("Ran", "User 1"),
    },
    os.getenv("dafyshay@gmail.com", "").lower(): {
        "password": os.getenv("Rd!0507821117", ""),
        "name": os.getenv("Dafy", "User 2"),
    },
}

ACTIVE_TOKENS = {}

class LoginRequest(BaseModel):
    email: str
    password: str

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5500")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        FRONTEND_URL,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return FileResponse("frontend/index.html")


@app.get("/health")
def health():
    return {"message": "Portfolio AI Agent is running"}

@app.get("/fx-rate")
async def fx_rate(currency: str = Query(...)):
    rate = await get_fx_rate_to_ils(currency)
    return {
        "currency": currency.upper(),
        "base_currency": "ILS",
        "rate": rate
    }

@app.get("/market-data")
async def market_data(security_number: str = Query(...)):
    data = await fetch_market_data(security_number)

    if not data:
        raise HTTPException(status_code=404, detail="לא נמצאו נתוני שוק עבור מספר הנייר")

    return data

@app.post("/login")
async def login(payload: LoginRequest):
    email = payload.email.strip().lower()
    password = payload.password

    user = USERS.get(email)
    if not user or user["password"] != password:
        raise HTTPException(status_code=401, detail="אימייל או סיסמה שגויים")

    token = secrets.token_hex(24)
    ACTIVE_TOKENS[token] = {
        "email": email,
        "name": user["name"]
    }

    return {
        "token": token,
        "user": {
            "email": email,
            "name": user["name"]
        }
    }

@app.get("/me")
async def me(token: str = Query(...)):
    user = ACTIVE_TOKENS.get(token)
    if not user:
        raise HTTPException(status_code=401, detail="Token לא תקין")

    return {
        "authenticated": True,
        "user": user
    }

@app.post("/analyze")
def analyze_portfolio(request: PortfolioRequest):
    assets = request.assets
    investor = request.investor

    total_value = calculate_total_value(assets)
    total_equity_exposure = calculate_total_equity_exposure(assets, total_value)
    total_fx_exposure = calculate_total_fx_exposure(assets, total_value)
    current_allocation = calculate_current_allocation(assets)
    risk_report = assess_portfolio_risk_level(assets, investor)
    overlaps = detect_portfolio_overlaps(assets)
    diversification = detect_fake_diversification(assets)
    data_quality = evaluate_portfolio_data_quality(assets)    

    asset_summaries = []
    for asset in assets:
        weight = calculate_asset_weight(asset, total_value)
        profit_loss = calculate_profit_loss(asset)
        profit_loss_percent = calculate_profit_loss_percent(asset)
        detailed_category = classify_asset_detailed(asset)

        asset_summaries.append({
            "asset_name": asset.instrument.asset_name,
            "asset_type": asset.instrument.asset_type,
            "detailed_category": detailed_category,
            "current_value": asset.position.current_value,
            "weight": round(weight, 4),
            "profit_loss": round(profit_loss, 2),
            "profit_loss_percent": round(profit_loss_percent, 4),
        })

    return {
        "portfolio_summary": {
            "risk_level": investor.risk_level,
            "investment_horizon_years": investor.investment_horizon_years,
            "monthly_new_cash": investor.monthly_new_cash,
            "base_currency": investor.base_currency,
            "total_value": round(total_value, 2),
            "total_equity_exposure": round(total_equity_exposure, 4),
            "total_fx_exposure": round(total_fx_exposure, 4),
            "current_allocation": current_allocation,
        },
        "risk_report": risk_report,
        "assets": asset_summaries,
        "overlaps": overlaps,
        "diversification": diversification,
        "data_quality": data_quality,        
    }


def build_recommendation_response(request: PortfolioRequest):
    assets = request.assets
    investor = request.investor

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
    overlaps = detect_portfolio_overlaps(assets)
    diversification = detect_fake_diversification(assets)
    data_quality = evaluate_portfolio_data_quality(assets)

    for recommendation in specific_recommendations:
        recommendation["explanation_text"] = explain_single_recommendation(recommendation)

        asset_name = recommendation.get("asset_name")
        data_quality_penalty = get_asset_data_quality_penalty(asset_name, data_quality) if asset_name else 0
        data_quality_flags = get_asset_data_quality_flags(asset_name, data_quality) if asset_name else []

        recommendation["data_quality_penalty"] = data_quality_penalty
        recommendation["data_quality_flags"] = data_quality_flags

        confidence = calculate_recommendation_confidence(recommendation)
        recommendation.update(confidence)

    for recommendation in hold_reduce_recommendations:
        recommendation["explanation_text"] = explain_single_recommendation(recommendation)

        asset_name = recommendation.get("asset_name")
        data_quality_penalty = get_asset_data_quality_penalty(asset_name, data_quality) if asset_name else 0
        data_quality_flags = get_asset_data_quality_flags(asset_name, data_quality) if asset_name else []

        recommendation["data_quality_penalty"] = data_quality_penalty
        recommendation["data_quality_flags"] = data_quality_flags

        confidence = calculate_recommendation_confidence(recommendation)
        recommendation.update(confidence)

    explanation = generate_portfolio_explanation(
        investor=investor.model_dump(),
        risk_report=risk_report,
        diversification=diversification,
        overlaps=overlaps,
        specific_recommendations=specific_recommendations,
        hold_reduce_recommendations=hold_reduce_recommendations,
    )

    client_report = build_client_report(
        investor=investor.model_dump(),
        risk_report=risk_report,
        diversification=diversification,
        overlaps=overlaps,
        specific_recommendations=specific_recommendations,
        hold_reduce_recommendations=hold_reduce_recommendations,
        explanation=explanation,
    )

    ai_explainer_output = None
    try:
        ai_explainer_output = generate_ai_client_summary({
            "client_report": client_report,
            "risk_report": risk_report,
            "diversification": diversification,
            "data_quality": data_quality,
            "specific_asset_recommendations": specific_recommendations,
            "hold_reduce_recommendations": hold_reduce_recommendations,
        })
    except Exception as e:
        ai_explainer_output = {
            "error": str(e)
        }

    return {
        "target_allocation": target_allocation,
        "current_allocation": current_allocation,
        "new_cash_recommendation": new_cash_recommendation,
        "specific_asset_recommendations": specific_recommendations,
        "hold_reduce_recommendations": hold_reduce_recommendations,
        "risk_report": risk_report,
        "overlaps": overlaps,
        "diversification": diversification,
        "explanation": explanation,
        "data_quality": data_quality,
        "client_report": client_report,
        "ai_explainer_output": ai_explainer_output,
    }

@app.post("/recommend")
def recommend_portfolio_actions(request: PortfolioRequest):
    return build_recommendation_response(request)

@app.post("/scenario")
def run_scenario(payload: dict = Body(...)):
    portfolio = payload.get("portfolio", {})
    scenario = payload.get("scenario", {})

    assets = portfolio.get("assets", [])
    investor = portfolio.get("investor", {})

    if not assets or not investor:
        return {"error": "Missing portfolio assets or investor profile"}

    # before
    before_request = PortfolioRequest(**portfolio)
    before_assets = before_request.assets
    before_investor = before_request.investor

    before_result = build_recommendation_response(before_request)

    # copy for simulation
    scenario_portfolio = deepcopy(portfolio)

    scenario_type = scenario.get("type")

    if scenario_type == "add_cash_to_asset":
        target_asset_name = scenario.get("asset_name")
        amount = float(scenario.get("amount", 0))

        for asset in scenario_portfolio["assets"]:
            if asset["instrument"]["asset_name"] == target_asset_name:
                asset["position"]["current_value"] += amount
                asset["position"]["cost_basis"] += amount
                break

    elif scenario_type == "reduce_asset":
        target_asset_name = scenario.get("asset_name")
        percent = float(scenario.get("percent", 0))

        for asset in scenario_portfolio["assets"]:
            if asset["instrument"]["asset_name"] == target_asset_name:
                factor = max(0.0, 1 - percent / 100.0)
                asset["position"]["quantity"] *= factor
                asset["position"]["current_value"] *= factor
                asset["position"]["cost_basis"] *= factor
                break

    elif scenario_type == "change_risk_level":
        new_risk_level = scenario.get("risk_level")
        if new_risk_level:
            scenario_portfolio["investor"]["risk_level"] = new_risk_level

    else:
        return {"error": "Unsupported scenario type"}

    after_request = PortfolioRequest(**scenario_portfolio)
    after_result = build_recommendation_response(after_request)

    return {
        "scenario": scenario,
        "before": before_result,
        "after": after_result,
        "scenario_portfolio": scenario_portfolio,
    }

def suggest_smart_scenario(request: PortfolioRequest, goal: str) -> dict:
    assets = request.assets
    investor = request.investor

    recommendation_result = build_recommendation_response(request)

    specific_recommendations = recommendation_result.get("specific_asset_recommendations", [])
    hold_reduce_recommendations = recommendation_result.get("hold_reduce_recommendations", [])
    overlaps = recommendation_result.get("overlaps", [])
    diversification = recommendation_result.get("diversification", {})

    if goal == "improve_diversification":
        for rec in specific_recommendations:
            if rec.get("action") == "buy" and rec.get("diversification_penalty", 0) <= 10:
                return {
                    "type": "add_cash_to_asset",
                    "asset_name": rec.get("asset_name"),
                    "amount": investor.monthly_new_cash,
                    "reason": "המערכת מציעה להפנות כסף חדש לנכס שמוסיף פחות חפיפה ועשוי לשפר את הפיזור."
                }

    if goal == "reduce_risk":
        reduce_candidates = [
            rec for rec in hold_reduce_recommendations
            if rec.get("action") == "reduce"
        ]
        if reduce_candidates:
            chosen = max(
                reduce_candidates,
                key=lambda r: (
                    r.get("overlap_penalty", 0) +
                    r.get("diversification_penalty", 0) +
                    max(0, 10 - (r.get("score") or 0))
                )
            )
            return {
                "type": "reduce_asset",
                "asset_name": chosen.get("asset_name"),
                "percent": 15,
                "reason": "המערכת מציעה לצמצם נכס שנראה תורם לעודף סיכון, חפיפה או פיזור מדומה."
            }

    if goal == "reduce_overlap":
        if overlaps:
            highest_overlap = overlaps[0]
            asset_name = highest_overlap.get("asset_2")
            return {
                "type": "reduce_asset",
                "asset_name": asset_name,
                "percent": 15,
                "reason": "המערכת מציעה לצמצם נכס שנמצא בחפיפה גבוהה עם נכס אחר בתיק."
            }

    if specific_recommendations:
        fallback = specific_recommendations[0]
        return {
            "type": "add_cash_to_asset",
            "asset_name": fallback.get("asset_name"),
            "amount": investor.monthly_new_cash,
            "reason": "לא נמצאה הזדמנות מובהקת, ולכן מוצע תרחיש שמבוסס על המלצת הקנייה המובילה."
        }

    return {
        "type": "change_risk_level",
        "risk_level": investor.risk_level,
        "reason": "לא נמצא כרגע תרחיש חכם ברור לשינוי."
    }

def score_scenario_result(before: dict, after: dict, goal: str) -> float:
    before_risk = before.get("risk_report", {})
    after_risk = after.get("risk_report", {})

    before_div = before.get("diversification", {})
    after_div = after.get("diversification", {})

    before_overlaps = len(before.get("overlaps", []))
    after_overlaps = len(after.get("overlaps", []))

    before_risk_score = before_risk.get("overall_risk_score", 0) or 0
    after_risk_score = after_risk.get("overall_risk_score", 0) or 0

    before_groups = before_div.get("num_groups", 0) or 0
    after_groups = after_div.get("num_groups", 0) or 0

    score = 0.0

    if goal == "reduce_risk":
        score += (before_risk_score - after_risk_score) * 3
        score += (after_groups - before_groups) * 5
        score += (before_overlaps - after_overlaps) * 2

    elif goal == "improve_diversification":
        score += (after_groups - before_groups) * 10
        score += (before_overlaps - after_overlaps) * 5
        score += (before_risk_score - after_risk_score) * 1

    elif goal == "reduce_overlap":
        score += (before_overlaps - after_overlaps) * 10
        score += (after_groups - before_groups) * 4
        score += (before_risk_score - after_risk_score) * 1

    else:
        score += (before_risk_score - after_risk_score)
        score += (after_groups - before_groups) * 2
        score += (before_overlaps - after_overlaps) * 2

    return round(score, 2)


def apply_scenario_to_portfolio(portfolio: dict, scenario: dict) -> dict:
    from copy import deepcopy

    scenario_portfolio = deepcopy(portfolio)
    scenario_type = scenario.get("type")

    if scenario_type == "add_cash_to_asset":
        target_asset_name = scenario.get("asset_name")
        amount = float(scenario.get("amount", 0))

        for asset in scenario_portfolio["assets"]:
            if asset["instrument"]["asset_name"] == target_asset_name:
                asset["position"]["current_value"] += amount
                asset["position"]["cost_basis"] += amount
                break

    elif scenario_type == "reduce_asset":
        target_asset_name = scenario.get("asset_name")
        percent = float(scenario.get("percent", 0))

        for asset in scenario_portfolio["assets"]:
            if asset["instrument"]["asset_name"] == target_asset_name:
                factor = max(0.0, 1 - percent / 100.0)
                asset["position"]["quantity"] *= factor
                asset["position"]["current_value"] *= factor
                asset["position"]["cost_basis"] *= factor
                break

    elif scenario_type == "change_risk_level":
        new_risk_level = scenario.get("risk_level")
        if new_risk_level:
            scenario_portfolio["investor"]["risk_level"] = new_risk_level

    return scenario_portfolio


def generate_candidate_scenarios(request: PortfolioRequest, goal: str) -> list[dict]:
    assets = request.assets
    investor = request.investor

    recommendation_result = build_recommendation_response(request)

    specific_recommendations = recommendation_result.get("specific_asset_recommendations", [])
    hold_reduce_recommendations = recommendation_result.get("hold_reduce_recommendations", [])
    overlaps = recommendation_result.get("overlaps", [])

    candidates = []

    # מועמדי buy
    for rec in specific_recommendations:
        if rec.get("action") == "buy" and rec.get("asset_name"):
            candidates.append({
                "type": "add_cash_to_asset",
                "asset_name": rec.get("asset_name"),
                "amount": investor.monthly_new_cash,
                "reason": "הוספת כסף חדש לנכס מומלץ קיים."
            })

    # מועמדי reduce
    for rec in hold_reduce_recommendations:
        if rec.get("action") == "reduce" and rec.get("asset_name"):
            candidates.append({
                "type": "reduce_asset",
                "asset_name": rec.get("asset_name"),
                "percent": 15,
                "reason": "צמצום נכס שסומן כמועמד להפחתה."
            })

    # מועמדי overlap
    for overlap in overlaps[:3]:
        asset_name = overlap.get("asset_2")
        if asset_name:
            candidates.append({
                "type": "reduce_asset",
                "asset_name": asset_name,
                "percent": 15,
                "reason": "צמצום נכס מתוך זוג חופף."
            })

    # מועמדי שינוי סיכון
    for level in ["low", "medium", "high"]:
        if level != investor.risk_level:
            candidates.append({
                "type": "change_risk_level",
                "risk_level": level,
                "reason": "בדיקת התאמה תחת רמת סיכון אחרת."
            })

    # הסרת כפילויות פשוטה
    unique = []
    seen = set()

    for candidate in candidates:
        key = (
            candidate.get("type"),
            candidate.get("asset_name"),
            candidate.get("amount"),
            candidate.get("percent"),
            candidate.get("risk_level"),
        )
        if key not in seen:
            seen.add(key)
            unique.append(candidate)

    return unique

@app.post("/smart-scenario")
def run_smart_scenario(payload: dict = Body(...)):
    portfolio = payload.get("portfolio", {})
    goal = payload.get("goal", "improve_diversification")

    if not portfolio:
        return {"error": "Missing portfolio"}

    request = PortfolioRequest(**portfolio)
    smart_scenario = suggest_smart_scenario(request, goal)

    scenario_payload = {
        "portfolio": portfolio,
        "scenario": smart_scenario,
    }

    return run_scenario(scenario_payload)

@app.post("/smart-scenarios")
def run_top_smart_scenarios(payload: dict = Body(...)):
    portfolio = payload.get("portfolio", {})
    goal = payload.get("goal", "improve_diversification")

    if not portfolio:
        return {"error": "Missing portfolio"}

    request = PortfolioRequest(**portfolio)
    before_result = build_recommendation_response(request)

    candidates = generate_candidate_scenarios(request, goal)
    evaluated = []

    for scenario in candidates:
        scenario_portfolio = apply_scenario_to_portfolio(portfolio, scenario)
        after_request = PortfolioRequest(**scenario_portfolio)
        after_result = build_recommendation_response(after_request)

        scenario_score = score_scenario_result(before_result, after_result, goal)

        evaluated.append({
            "scenario": scenario,
            "score": scenario_score,
            "before": before_result,
            "after": after_result,
        })

    evaluated.sort(key=lambda item: item["score"], reverse=True)

    return {
        "goal": goal,
        "top_scenarios": evaluated[:3],
    }