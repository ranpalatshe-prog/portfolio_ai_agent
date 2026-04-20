def calculate_recommendation_confidence(recommendation: dict) -> dict:
    action = recommendation.get("action", "")
    score = recommendation.get("score", 0) or 0
    overlap_penalty = recommendation.get("overlap_penalty", 0) or 0
    diversification_penalty = recommendation.get("diversification_penalty", 0) or 0
    data_quality_penalty = recommendation.get("data_quality_penalty", 0) or 0

    confidence_score = 50

    # איכות בסיסית
    if score >= 15:
        confidence_score += 25
    elif score >= 5:
        confidence_score += 10
    else:
        confidence_score -= 10

    # קנסות
    confidence_score -= min(overlap_penalty, 30)
    confidence_score -= min(diversification_penalty, 25)
    confidence_score -= min(data_quality_penalty, 30)

    # סוג פעולה
    if action == "buy":
        confidence_score += 5
    elif action == "hold":
        confidence_score += 10
    elif action == "reduce":
        confidence_score -= 5
    elif action == "add_new_asset":
        confidence_score -= 10

    # תחימה
    confidence_score = max(0, min(100, confidence_score))

    # תווית
    if confidence_score >= 75:
        confidence_label = "high"
    elif confidence_score >= 45:
        confidence_label = "medium"
    else:
        confidence_label = "low"

    # הסבר
    reasons = []

    if score >= 15:
        reasons.append("ציון האיכות של ההמלצה גבוה יחסית.")
    elif score >= 5:
        reasons.append("ציון האיכות של ההמלצה בינוני.")
    else:
        reasons.append("ציון האיכות של ההמלצה נמוך יחסית.")

    if overlap_penalty >= 25:
        reasons.append("קיימת חפיפה גבוהה עם נכסים אחרים, ולכן רמת הביטחון יורדת.")
    elif overlap_penalty >= 10:
        reasons.append("קיימת חפיפה מסוימת עם נכסים אחרים.")
    else:
        reasons.append("לא זוהתה חפיפה מהותית שמחלישה את ההמלצה.")

    if diversification_penalty >= 20:
        reasons.append("הנכס שייך לקבוצה צפופה ולכן תרומתו לפיזור מוגבלת.")
    elif diversification_penalty >= 10:
        reasons.append("הנכס שייך לקבוצת חשיפה בינונית בגודלה.")
    else:
        reasons.append("הנכס אינו פוגע בצורה מהותית בפיזור הכולל.")

    if action == "add_new_asset":
        reasons.append("מאחר שלא נמצא נכס קיים מתאים, נדרשת הערכה נוספת לפני פעולה.")
    elif action == "reduce":
        reasons.append("המלצת צמצום דורשת זהירות גבוהה יותר ולכן רמת הביטחון שמרנית יותר.")

    if data_quality_penalty >= 20:
        reasons.append("איכות הנתונים של הנכס חלשה יחסית ולכן רמת הביטחון יורדת.")
    elif data_quality_penalty >= 10:
        reasons.append("זוהו מספר בעיות איכות נתונים מתונות בנכס.")
    else:
        reasons.append("לא זוהו בעיות איכות נתונים מהותיות.")

    return {
        "confidence_score": confidence_score,
        "confidence_label": confidence_label,
        "confidence_reason": " ".join(reasons),
    }