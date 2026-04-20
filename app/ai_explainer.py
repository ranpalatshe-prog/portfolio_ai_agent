import json
import os

api_key = os.environ.get("OPENAI_API_KEY")

client = None
if api_key:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
    except Exception:
        client = None


def build_ai_explanation_payload(result: dict) -> dict:
    return {
        "client_report": result.get("client_report", {}),
        "risk_report": result.get("risk_report", {}),
        "diversification": result.get("diversification", {}),
        "data_quality": result.get("data_quality", {}),
        "specific_asset_recommendations": result.get("specific_asset_recommendations", []),
        "hold_reduce_recommendations": result.get("hold_reduce_recommendations", []),
    }


def generate_ai_client_summary(result: dict) -> dict:
    if client is None:
        return {"message": "AI לא זמין כרגע"}

    payload = build_ai_explanation_payload(result)

    prompt = f"""
אתה מסביר השקעות בשפה פשוטה, זהירה, ולא יוצר המלצות חדשות.
אתה חייב להסתמך רק על הנתונים שקיבלת.
אל תשנה את ההמלצות. אל תוסיף פעולות שלא הופיעו.
החזר JSON בלבד בפורמט:
{{
  "short_summary": "...",
  "client_friendly_summary": "...",
  "top_risks": ["...", "..."],
  "top_actions": ["...", "..."],
  "disclaimer": "..."
}}

הנתונים:
{json.dumps(payload, ensure_ascii=False)}
"""

    response = client.responses.create(
        model="gpt-5.4-mini",
        input=prompt,
    )

    text = response.output_text
    return json.loads(text)
