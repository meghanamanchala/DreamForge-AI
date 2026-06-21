from agents.base import BaseAgent
from pydantic import BaseModel, Field
from typing import List
from tools.calculator import run_financial_simulation

class FinanceParamsSchema(BaseModel):
    pricing_model: str = Field(
        description="Must be one of: 'subscription', 'one_time', 'transactional', 'freemium'."
    )
    pricing_point: float = Field(description="Estimated price charged per unit/user in USD.")
    fixed_monthly_costs: float = Field(description="Estimated monthly operating expenses (salaries, hosting, office, marketing).")
    variable_cost_margin: float = Field(description="Percentage (0.0 to 1.0) of revenue spent on delivery/COGS (e.g. 0.15 for 15%).")
    estimated_growth_rate: float = Field(description="MoM customer growth rate as decimal (e.g. 0.08 for 8%).")
    initial_investment: float = Field(description="Initial capital required to start operations in USD.")
    starting_customers: int = Field(description="Number of target customers in month 1.")

class FinanceOutputSchema(BaseModel):
    revenue_model_description: str = Field(
        description="Detailed description of the pricing tiers, billing frequency, and value extraction methods."
    )
    pricing_model_selected: str = Field(description="The chosen model label (e.g., subscription).")
    pricing_point: float = Field(description="Primary pricing target.")
    fixed_monthly_costs: float = Field(description="Total monthly operating expenses (OPEX).")
    break_even_month: str = Field(description="Detailed timeline when monthly profitability is reached.")
    initial_funding_required: str = Field(description="Amount of startup capital needed and clear allocation (e.g., development, hiring, advertising).")
    year_1_revenue: float = Field(description="Year 1 total revenue projected.")
    year_1_profit: float = Field(description="Year 1 net profit projected.")
    year_2_revenue: float = Field(description="Year 2 total revenue projected.")
    year_2_profit: float = Field(description="Year 2 net profit projected.")
    year_3_revenue: float = Field(description="Year 3 total revenue projected.")
    year_3_profit: float = Field(description="Year 3 net profit projected.")
    unit_economics: str = Field(
        description="Analysis of Customer Acquisition Cost (CAC) thresholds, estimated Lifetime Value (LTV), and gross margins."
    )

class FinanceAgent(BaseAgent):
    def __init__(self, client, model="gemini-flash-latest"):
        super().__init__(client, model)
        self.system_instruction = (
            "You are the Chief Financial Officer (CFO) of DreamForge AI.\n"
            "Your job is to model the financial sustainability and pricing strategy of the startup.\n"
            "You calculate unit economics, project cash flow, determine capital requirements, "
            "and utilize programmatic financial calculations for precision."
        )

    def generate_projections(self, idea, planner_instructions, research_data=None):
        """
        Runs the full finance sequence using native Gemini tool usage.
        """
        tools_list = [run_financial_simulation]
        tools_map = {
            "run_financial_simulation": run_financial_simulation
        }

        user_content = (
            f"Startup Idea: {idea}\n"
            f"Planner Instructions: {planner_instructions}\n"
            f"Research Insights: {str(research_data) if research_data else 'None'}\n\n"
            "Analyze the business concept and design the pricing structure. "
            "Execute the financial simulation tool with appropriate parameters for pricing points, growth, and expenses "
            "to calculate a 36-month projection, and return the complete draft."
        )

        # Step 1: Execute tool loop natively
        draft_response = self.generate_text_with_tools(
            system_instruction=self.system_instruction,
            user_content=user_content,
            tools_list=tools_list,
            tools_map=tools_map
        )

        # Step 2: Compile the structured JSON output from the draft
        synthesis_prompt = (
            f"Draft financial summary:\n{draft_response.text}\n\n"
            "Compile the complete Financial Projections module conforming to the schema."
        )

        report = self.generate_structured(
            system_instruction=self.system_instruction,
            user_content=synthesis_prompt,
            response_schema=FinanceOutputSchema
        )
        
        return report
