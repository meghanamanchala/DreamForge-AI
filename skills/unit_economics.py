def calculate_ltv_cac_ratio(pricing_point, variable_cost_margin, monthly_churn_rate, target_cac):
    """
    Decoupled business skill to compute customer lifetime value and acquisition boundaries.
    - Monthly Gross Margin = Pricing Point * (1 - Variable Cost Margin)
    - Customer LTV = Monthly Gross Margin / Monthly Churn Rate
    - LTV/CAC Ratio = LTV / Target CAC
    """
    try:
        price = float(pricing_point)
        v_margin = float(variable_cost_margin)
        churn = float(monthly_churn_rate)
        cac = float(target_cac)
    except (ValueError, TypeError):
        return {"error": "Invalid numerical parameters."}

    monthly_margin = price * (1 - v_margin)
    
    # Avoid division by zero
    if churn <= 0:
        churn = 0.01  # assume baseline 1% churn
        
    ltv = monthly_margin / churn
    
    if cac <= 0:
        ratio = 0.0
    else:
        ratio = ltv / cac

    return {
        "monthly_gross_margin": round(monthly_margin, 2),
        "ltv": round(ltv, 2),
        "ltv_cac_ratio": round(ratio, 2),
        "is_healthy": ratio >= 3.0
    }
