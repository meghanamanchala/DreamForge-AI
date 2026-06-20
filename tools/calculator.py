from tools.mcp_registry import mcp_registry
from pydantic import BaseModel, Field

class FinancialSimInputs(BaseModel):
    pricing_model: str = Field(default="subscription", description="Billing model: subscription, one_time, transactional, freemium.")
    pricing_point: float = Field(default=29.0, description="The price target unit cost.")
    fixed_monthly_costs: float = Field(default=5000.0, description="Operating costs per month.")
    variable_cost_margin: float = Field(default=0.15, description="Variable cost percentage margin (0.0 to 1.0).")
    estimated_growth_rate: float = Field(default=0.08, description="MoM customer growth rate (0.0 to 1.0).")
    initial_investment: float = Field(default=25000.0, description="Starting cash capital.")
    starting_customers: int = Field(default=50, description="Customer volume at launch month.")

@mcp_registry.register(
    name="run_financial_simulation",
    description="Simulates a 3-year (36-month) operational cash ledger showing yearly summaries and break-even targets.",
    input_schema=FinancialSimInputs
)
def run_financial_simulation(
    pricing_model="subscription",
    pricing_point=29.0,
    fixed_monthly_costs=5000.0,
    variable_cost_margin=0.15,
    estimated_growth_rate=0.08,
    initial_investment=25000.0,
    starting_customers=50
):
    """
    Computes a rigorous 36-month startup cash trajectory and business P&L sheet.
    Returns: Dict containing summary metrics, yearly aggregated tables, and full monthly projections.
    """
    # Ensure inputs are valid numbers
    try:
        pricing_point = float(pricing_point)
        fixed_monthly_costs = float(fixed_monthly_costs)
        variable_cost_margin = float(variable_cost_margin)
        estimated_growth_rate = float(estimated_growth_rate)
        initial_investment = float(initial_investment)
        starting_customers = int(starting_customers)
    except (ValueError, TypeError):
        return {"error": "Invalid financial inputs. All parameters must be numbers."}

    monthly_records = []
    current_customers = starting_customers
    current_cash = initial_investment
    break_even_month = -1
    
    for month in range(1, 37):
        # Customer growth (only grows if positive growth rate)
        if month > 1:
            current_customers = int(current_customers * (1 + estimated_growth_rate))
            
        # Revenue calculations based on models
        if pricing_model == "subscription":
            revenue = current_customers * pricing_point
        elif pricing_model == "one_time":
            # Assume customer count represents new transactions each month
            revenue = current_customers * pricing_point
        elif pricing_model == "transactional":
            # Assume customer count represents transactions, pricing_point is cut
            revenue = current_customers * pricing_point
        elif pricing_model == "freemium":
            # Assume 5% conversion rate to premium pricing point
            revenue = (current_customers * 0.05) * pricing_point
        else:
            revenue = current_customers * pricing_point

        # Expenses
        v_expenses = revenue * variable_cost_margin
        monthly_expenses = fixed_monthly_costs + v_expenses
        net_profit = revenue - monthly_expenses
        current_cash += net_profit
        
        # Check break-even month (first month where profit is positive)
        if net_profit > 0 and break_even_month == -1:
            break_even_month = month
            
        monthly_records.append({
            "month": month,
            "customers": current_customers,
            "revenue": round(revenue, 2),
            "fixed_costs": round(fixed_monthly_costs, 2),
            "variable_costs": round(v_expenses, 2),
            "total_expenses": round(monthly_expenses, 2),
            "net_profit": round(net_profit, 2),
            "ending_cash": round(current_cash, 2)
        })

    # Aggregate by Year
    yearly_data = {
        "Year 1": {"revenue": 0.0, "expenses": 0.0, "profit": 0.0},
        "Year 2": {"revenue": 0.0, "expenses": 0.0, "profit": 0.0},
        "Year 3": {"revenue": 0.0, "expenses": 0.0, "profit": 0.0}
    }
    
    for r in monthly_records:
        m = r["month"]
        if 1 <= m <= 12:
            year = "Year 1"
        elif 13 <= m <= 24:
            year = "Year 2"
        else:
            year = "Year 3"
            
        yearly_data[year]["revenue"] += r["revenue"]
        yearly_data[year]["expenses"] += r["total_expenses"]
        yearly_data[year]["profit"] += r["net_profit"]

    # Round aggregated data
    for year in yearly_data:
        yearly_data[year]["revenue"] = round(yearly_data[year]["revenue"], 2)
        yearly_data[year]["expenses"] = round(yearly_data[year]["expenses"], 2)
        yearly_data[year]["profit"] = round(yearly_data[year]["profit"], 2)

    # Determine final metrics
    break_even_desc = f"Month {break_even_month}" if break_even_month > 0 else "Not achieved within 36 months"
    total_revenue = sum(r["revenue"] for r in monthly_records)
    total_expenses = sum(r["total_expenses"] for r in monthly_records)
    total_profit = total_revenue - total_expenses

    return {
        "summary": {
            "total_revenue": round(total_revenue, 2),
            "total_expenses": round(total_expenses, 2),
            "total_profit": round(total_profit, 2),
            "break_even_month": break_even_desc,
            "final_cash_balance": round(current_cash, 2),
            "ending_customer_count": current_customers
        },
        "yearly_projections": yearly_data,
        "monthly_details": monthly_records
    }
