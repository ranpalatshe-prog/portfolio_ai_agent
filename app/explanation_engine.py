def get_risk_profile_text(risk_level: str) -> str:
    if risk_level == "low":
        return "רמת סיכון נמוכה"
    if risk_level == "medium":
        return "רמת סיכון בינונית"
    if risk_level == "high":
        return "רמת סיכון גבוהה"
    return "רמת סיכון לא ידועה"


def get_horizon_text(years: int) -> str:
    if years <= 3:
        return f"אופק השקעה קצר יחסית של {years} שנים"
    if years <= 10:
        return f"אופק השקעה בינוני של {years} שנים"
    return f"אופק השקעה ארוך של {years} שנים"


def generate_portfolio_explanation(
    investor: dict,
    risk_report: dict,
    diversification: dict,
    overlaps: list[dict],
    specific_recommendations: list[dict],
    hold_reduce_recommendations: list[dict],
) -> dict:
    summary_parts = []
    action_parts = []

    risk_level = investor.get("risk_level", "unknown")
    horizon_years = investor.get("investment_horizon_years", 0)
    monthly_new_cash = investor.get("monthly_new_cash", 0)

    risk_profile_text = get_risk_profile_text(risk_level)
    horizon_text = get_horizon_text(horizon_years)

    risk_label = risk_report.get("overall_risk_label", "unknown")
    risk_score = risk_report.get("overall_risk_score", 0)
    warnings = risk_report.get("warnings", [])

    num_assets = diversification.get("num_assets", 0)
    num_groups = diversification.get("num_groups", 0)
    diversification_warnings = diversification.get("warnings", [])

    high_overlap_count = sum(1 for item in overlaps if item.get("severity") == "high")

    buy_recs = [rec for rec in specific_recommendations if rec.get("action") == "buy"]
    add_new_recs = [rec for rec in specific_recommendations if rec.get("action") == "add_new_asset"]
    reduce_recs = [rec for rec in hold_reduce_recommendations if rec.get("action") == "reduce"]

    # סיכום אישי
    summary_parts.append(
        f"בהתאם לפרופיל שבחרת, הכולל {risk_profile_text} ו-{horizon_text}, התיק נבחן גם מבחינת סיכון וגם מבחינת פיזור."
    )

    summary_parts.append(
        f"התיק כולל {num_assets} נכסים, אך בפועל זוהו {num_groups} קבוצות חשיפה עיקריות."
    )

    if risk_label == "high":
        summary_parts.append(
            f"רמת הסיכון בפועל גבוהה יחסית מהותית, עם ציון סיכון {risk_score}."
        )
    elif risk_label == "medium":
        summary_parts.append(
            f"רמת הסיכון בפועל בינונית, עם ציון סיכון {risk_score}."
        )
    else:
        summary_parts.append(
            f"רמת הסיכון בפועל נמוכה יחסית, עם ציון סיכון {risk_score}."
        )

    if diversification_warnings:
        summary_parts.append(
            "למרות מספר הנכסים בתיק, חלק מהחשיפות דומות זו לזו ולכן הפיזור בפועל נמוך יותר ממה שנראה במבט ראשון."
        )
    else:
        summary_parts.append(
            "מבנה הפיזור בתיק נראה סביר, ואין כרגע סימן חזק לכך שמספר הנכסים יוצר אשליית פיזור."
        )

    if high_overlap_count > 0:
        summary_parts.append(
            f"זוהו {high_overlap_count} חפיפות חזקות בין נכסים, ולכן חלק מהתיק חשוף למעשה לאותם מוקדי סיכון."
        )
    elif overlaps:
        summary_parts.append(
            "זוהו חפיפות חלקיות בין חלק מהנכסים, אך לא ברמה הקיצונית ביותר."
        )
    else:
        summary_parts.append(
            "לא זוהו כרגע חפיפות משמעותיות בין הנכסים בתיק."
        )

    # הסבר סיכון
    risk_explanation_parts = [
        f"המשתמש הגדיר {risk_profile_text}, בעוד שבפועל התיק מסווג כרגע ברמת סיכון {risk_label}.",
    ]

    if warnings:
        risk_explanation_parts.append("נקודות הסיכון המרכזיות שזוהו הן:")
        risk_explanation_parts.extend(warnings)
    else:
        risk_explanation_parts.append("לא זוהו כרגע אזהרות סיכון חריגות.")

    # הסבר פיזור
    diversification_parts = [
        f"אופק ההשקעה שנבחר הוא {horizon_text}.",
        f"מספר הנכסים בתיק הוא {num_assets}, אך מספר קבוצות החשיפה האמיתיות הוא {num_groups}.",
    ]

    if diversification_warnings:
        diversification_parts.append("האזהרות המרכזיות בתחום הפיזור הן:")
        diversification_parts.extend(diversification_warnings)
    else:
        diversification_parts.append("לא זוהו סימנים חזקים לפיזור מדומה.")

    # הסבר פעולות
    if buy_recs:
        buy_names = [rec["asset_name"] for rec in buy_recs if rec.get("asset_name")]
        if buy_names:
            action_parts.append(
                f"כאשר יש לך {monthly_new_cash:,.0f} כסף חדש להשקעה, המערכת מעדיפה להפנות אותו לנכסים שנראים איכותיים יותר ושאינם מחמירים את בעיית החפיפה, כגון: "
                + ", ".join(buy_names) + "."
            )

    if add_new_recs:
        categories = [rec["category"] for rec in add_new_recs if rec.get("category")]
        if categories:
            action_parts.append(
                "בנוסף, נראה שיש חוסרים בקטגוריות מסוימות בתיק, ולכן ייתכן שכדאי לשקול הוספת נכס חדש מסוג: "
                + ", ".join(categories) + "."
            )

    if reduce_recs:
        reduce_names = [rec["asset_name"] for rec in reduce_recs if rec.get("asset_name")]
        if reduce_names:
            action_parts.append(
                "בחלק מהנכסים קיימת אינדיקציה לצמצום, בעיקר כאשר אותו נכס נמצא בקטגוריה בעודף או בתוך קבוצת חפיפה צפופה, כגון: "
                + ", ".join(reduce_names) + "."
            )
    else:
        action_parts.append(
            "כרגע לא זוהתה המלצת צמצום חזקה שמחייבת פעולה מיידית, ולכן ניתן להתמקד בעיקר בשיפור ההקצאה של כסף חדש."
        )

    # מסקנה
    if diversification_warnings or high_overlap_count > 0:
        conclusion = (
            "המסקנה המרכזית היא שהתיק נראה מגוון יותר מכפי שהוא באמת, ולכן ההחלטה החשובה כרגע אינה רק לבחור נכסים טובים, אלא גם להימנע מהעמקת הריכוז באותן חשיפות."
        )
    else:
        conclusion = (
            "המסקנה המרכזית היא שהתיק בנוי בצורה יחסית מאוזנת, ולכן ההמשך צריך להתמקד בעיקר בהתאמה שוטפת לרמת הסיכון ולטווח ההשקעה שלך."
        )

    return {
        "summary": " ".join(summary_parts),
        "risk_explanation": " ".join(risk_explanation_parts),
        "diversification_explanation": " ".join(diversification_parts),
        "action_explanation": " ".join(action_parts),
        "conclusion": conclusion,
    }