from agents.base import BaseAgent
from pydantic import BaseModel, Field
from typing import List

class EvaluationScorecard(BaseModel):
    passed: bool = Field(
        description="True if the drafts are consistent, coherent, and realistic. False if rework is required."
    )
    completeness_score: float = Field(
        description="Rating from 0.0 to 10.0 checking if all necessary modules are structured and detailed."
    )
    feasibility_score: float = Field(
        description="Rating from 0.0 to 10.0 evaluating if the growth parameters and costs are realistic."
    )
    alignment_score: float = Field(
        description="Rating from 0.0 to 10.0 checking if the financial operational budgets and GTM channel spend align."
    )
    feedback_comments: List[str] = Field(
        description="Structured checklist of findings and concerns identified."
    )
    rework_needed: bool = Field(
        description="True if an agent must make edits before final approval; False otherwise."
    )
    target_agent: str = Field(
        description="The agent that must perform the rework: 'Research Agent', 'Finance Agent', 'Marketing Agent', or 'None'."
    )

class ReviewerAgent(BaseAgent):
    def __init__(self, client, model="gemini-flash-latest"):
        super().__init__(client, model)
        self.system_instruction = (
            "You are the Lead Evaluation Agent and Investment Auditor at DreamForge AI.\n"
            "Your role is to act as an LLM-as-a-Judge and critique the generated plans.\n"
            "Evaluate the drafts based on: completeness, feasibility, and cross-agent alignment.\n"
            "Double check if numbers or customer segments conflict between Finance, Research, and GTM plans.\n"
            "If any critical flaw is found (or if average score < 8.0), set passed = false, rework_needed = true, "
            "specify the target_agent, and list clear critiques in feedback_comments.\n"
            "If all systems are aligned, set passed = true, rework_needed = false, target_agent = 'None'."
        )

    def audit_drafts(self, idea, planner_data, research_data, finance_data, marketing_data):
        user_content = (
            f"Startup Idea: {idea}\n\n"
            f"Planner Summary: {planner_data}\n\n"
            f"Research Draft: {research_data}\n\n"
            f"Finance Draft: {finance_data}\n\n"
            f"Marketing Draft: {marketing_data}\n\n"
            "Audit these drafts to generate a multi-dimensional evaluation scorecard conforming to the schema."
        )
        result = self.generate_structured(self.system_instruction, user_content, EvaluationScorecard)
        return result
