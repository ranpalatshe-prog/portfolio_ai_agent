def get_action_priority(recommendation: dict) -> str:
    action = recommendation.get("action")
    confidence_score = recommendation.get("confidence_score", 0) or 0
    overlap_penalty = recommendation.get("overlap_penalty", 0) or 0
    diversification_penalty = recommendation.get("diversification_penalty", 0) or 0

    if action == "reduce":
        if confidence_score >= 70 and (overlap_penalty >= 20 or diversification_penalty >= 20):
            return "high"
        return "medium"

    if action == "buy":
        if confidence_score >= 70:
            return "high"
        return "medium"

    if action == "add_new_asset":
        return "medium"

    return "low"


def build_manual_action_from_recommendation(recommendation: dict) -> dict:
    action = recommendation.get("action")
    asset_name = recommendation.get("asset_name")
    category = recommendation.get("category")
    amount = recommendation.get("amount", 0)
    confidence_label = recommendation.get("confidence_label", "unknown")
    confidence_score = recommendation.get("confidence_score", 0)
    explanation_text = recommendation.get("explanation_text", "")
    priority = get_action_priority(recommendation)

    checks = []

    if action == "buy":
        title = f"שקול לרכוש/לחזק את {asset_name}"
        description = (
            f"המערכת ממליצה לשקול הפניית כ-{amount:,.0f} ל-{asset_name} "
            f"כדי לשפר את ההקצאה בקטגוריית {category}."
        )
        checks = [
            "בדוק שהנכס עדיין מתאים ליעד ההשקעה שלך בנקודת הזמן הנוכחית.",
            "בדוק עלויות קנייה/מכירה ודמי ניהול.",
            "בדוק שאין שינוי חיצוני מהותי שלא משתקף עדיין בנתונים."
        ]

    elif action == "reduce":
        title = f"שקול לצמצם את {asset_name}"
        description = (
            f"המערכת מסמנת את {asset_name} כמועמד לצמצום ידני "
            f"בהיקף משוער של כ-{amount:,.0f}."
        )
        checks = [
            "בדוק האם קיימים שיקולי מס לפני מכירה או צמצום.",
            "בדוק האם הצמצום אכן מקטין חפיפה או עודף חשיפה.",
            "בדוק שאין לנכס סיבה אסטרטגית מיוחדת להישאר במשקל הנוכחי."
        ]

    elif action == "add_new_asset":
        title = f"שקול להוסיף נכס חדש בקטגוריית {category}"
        description = (
            f"המערכת מזהה שחסר בתיק נכס מתאים בקטגוריית {category}, "
            f"ולכן ייתכן שכדאי להוסיף נכס חדש במקום להגדיל נכסים קיימים."
        )
        checks = [
            "בדוק אילו נכסים זמינים בפועל בקטגוריה הזו.",
            "בדוק התאמה לדמי ניהול, נזילות ומטבע.",
            "בדוק שהנכס החדש לא יוצר חפיפה דומה לנכסים קיימים."
        ]

    else:
        title = f"השאר את {asset_name} בהחזקה"
        description = "כרגע לא זוהתה אינדיקציה חזקה לשינוי מיידי בנכס הזה."
        checks = [
            "עקוב אחר ביצועי הנכס וההתאמה שלו לתיק.",
            "בדוק מחדש בניתוח הבא אם חל שינוי מהותי."
        ]

    return {
        "title": title,
        "description": description,
        "priority": priority,
        "confidence_label": confidence_label,
        "confidence_score": confidence_score,
        "why": explanation_text,
        "manual_checks": checks,
    }


def build_client_report(
    investor: dict,
    risk_report: dict,
    diversification: dict,
    overlaps: list[dict],
    specific_recommendations: list[dict],
    hold_reduce_recommendations: list[dict],
    explanation: dict,
) -> dict:
    risk_level = investor.get("risk_level", "unknown")
    horizon = investor.get("investment_horizon_years", 0)
    monthly_new_cash = investor.get("monthly_new_cash", 0)
    overlap_count = len(overlaps or [])

    top_actions = []

    merged = []
    merged.extend(specific_recommendations)
    merged.extend([rec for rec in hold_reduce_recommendations if rec.get("action") == "reduce"])

    merged.sort(
        key=lambda rec: (
            0 if get_action_priority(rec) == "high" else 1 if get_action_priority(rec) == "medium" else 2,
            -(rec.get("confidence_score", 0) or 0),
        )
    )

    for recommendation in merged[:3]:
        top_actions.append(build_manual_action_from_recommendation(recommendation))

    executive_summary = (
        f"נכון לעכשיו, התיק נבחן עבור משקיע עם רמת סיכון {risk_level} "
        f"ואופק השקעה של {horizon} שנים. "
        f"המערכת מעריכה את מצב התיק, את רמת הסיכון, את הפיזור בפועל ואת החפיפות בין הנכסים, "
        f"ומציעה פעולות ידניות בלבד — ללא ביצוע אוטומטי. "
        f"זוהו {overlap_count} חפיפות בין נכסים בתיק. "
        f"כסף חדש להשקעה שנלקח בחשבון בניתוח: {monthly_new_cash:,.0f}."
    )

    caution_statement = (
        "הדוח נועד לסייע בקבלת החלטות ואינו מבצע שינויים בפועל בתיק. "
        "לפני כל פעולה בפועל יש לבדוק שיקולי מס, עלויות מסחר, התאמה אישית, "
        "ושינויים עדכניים בשוק שאינם בהכרח משתקפים במלואם בנתונים שהוזנו."
    )

    return {
        "executive_summary": executive_summary,
        "summary_text": explanation.get("summary", ""),
        "main_conclusion": explanation.get("conclusion", ""),
        "top_actions": top_actions,
        "caution_statement": caution_statement,
    }