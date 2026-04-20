def explain_single_recommendation(recommendation: dict) -> str:
    action = recommendation.get("action", "")
    category = recommendation.get("category", "")
    score = recommendation.get("score")
    overlap_penalty = recommendation.get("overlap_penalty", 0)
    diversification_penalty = recommendation.get("diversification_penalty", 0)

    score_text = ""
    if score is not None:
        if score >= 15:
            score_text = "הנכס קיבל ציון איכות גבוה יחסית."
        elif score >= 5:
            score_text = "הנכס קיבל ציון בינוני."
        else:
            score_text = "הנכס קיבל ציון חלש יחסית."

    overlap_text = ""
    if overlap_penalty >= 25:
        overlap_text = "קיימת חפיפה גבוהה עם נכסים אחרים בתיק."
    elif overlap_penalty >= 10:
        overlap_text = "קיימת חפיפה מסוימת עם נכסים אחרים."
    else:
        overlap_text = "לא זוהתה חפיפה מהותית עם נכסים אחרים."

    diversification_text = ""
    if diversification_penalty >= 20:
        diversification_text = "הנכס שייך לקבוצת חשיפה צפופה ולכן מוסיף מעט לפיזור האמיתי."
    elif diversification_penalty >= 10:
        diversification_text = "הנכס שייך לקבוצת חשיפה בינונית בגודלה."
    else:
        diversification_text = "הנכס תורם בצורה סבירה לפיזור הכולל."

    if action == "buy":
        return " ".join([
            f"הנכס הועדף לקנייה בקטגוריית {category}.",
            score_text,
            overlap_text,
            diversification_text,
            "המטרה היא להפנות כסף חדש לנכס שמתאים להקצאה הרצויה בלי להחמיר ריכוזיות מיותרת."
        ])

    if action == "reduce":
        return " ".join([
            f"הנכס סומן כמועמד לצמצום בקטגוריית {category}.",
            score_text,
            overlap_text,
            diversification_text,
            "הסיבה העיקרית היא שהמשך הגדלת החשיפה אליו או השארתו במשקל גבוה עלולים להכביד על איזון התיק."
        ])

    if action == "hold":
        return " ".join([
            f"הנכס סומן כהחזקה בקטגוריית {category}.",
            score_text,
            overlap_text,
            diversification_text,
            "כרגע אין אינדיקציה חזקה שמחייבת שינוי מיידי."
        ])

    if action == "add_new_asset":
        return " ".join([
            f"כרגע אין בתיק נכס מתאים בקטגוריית {category}.",
            "לכן המערכת מציעה לשקול הוספת נכס חדש בקטגוריה הזו כדי לשפר את האיזון והפיזור."
        ])

    return "לא נוצר הסבר מפורט להמלצה זו."