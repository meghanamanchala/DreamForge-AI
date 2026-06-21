from agents.base import BaseAgent
from pydantic import BaseModel, Field
from typing import List

class GrowthChannel(BaseModel):
    channel_name: str = Field(description="Name of the marketing channel (e.g., SEO, Cold Email, Meta Ads).")
    tactic: str = Field(description="Specific GTM tactic to acquire customers through this channel.")
    estimated_cost: str = Field(description="Cost rating (e.g., Free, Low, Medium, High).")
    difficulty: str = Field(description="Execution difficulty (e.g., Easy, Moderate, Hard).")

class MarketingOutputSchema(BaseModel):
    brand_positioning: str = Field(
        description="The brand narrative, tone of voice, and position relative to existing market competitors."
    )
    value_propositions: List[str] = Field(
        description="List of 3-5 high-impact value propositions solving target user pain points."
    )
    growth_channels: List[GrowthChannel] = Field(
        description="The recommended mix of organic and paid marketing channels."
    )
    gtm_milestones: List[str] = Field(
        description="Chronological GTM stages (e.g., pre-launch validation, launch campaign, scaling/referrals)."
    )
    estimated_cac_ltv_context: str = Field(
        description="Strategic targets for customer lifetime value (LTV) and maximum customer acquisition cost (CAC) boundaries."
    )

class MarketingAgent(BaseAgent):
    def __init__(self, client, model="gemini-flash-latest"):
        super().__init__(client, model)
        self.system_instruction = (
            "You are the Chief Marketing Officer (CMO) of DreamForge AI.\n"
            "Your role is to build a high-performance Go-To-Market (GTM) strategy.\n"
            "Develop distinct brand value propositions, design user acquisition channels, and map out "
            "marketing campaign timelines tailored specifically to the target market and budget context."
        )

    def formulate_gtm(self, idea, planner_instructions, competitor_insights=None, finance_insights=None):
        user_content = (
            f"Startup Idea: {idea}\n"
            f"Planner Instructions: {planner_instructions}\n"
            f"Competitors Found: {str(competitor_insights) if competitor_insights else 'None'}\n"
            f"Financial Parameters: {str(finance_insights) if finance_insights else 'None'}\n\n"
            "Generate the complete Marketing & GTM strategy blueprint matching the requested schema."
        )
        result = self.generate_structured(self.system_instruction, user_content, MarketingOutputSchema)
        return result
