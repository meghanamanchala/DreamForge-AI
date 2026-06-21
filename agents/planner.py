from agents.base import BaseAgent
from pydantic import BaseModel, Field
from typing import List

class PlannerTask(BaseModel):
    agent_name: str = Field(
        description="Name of the target agent (Research Agent, Finance Agent, or Marketing Agent)."
    )
    instructions: str = Field(
        description="Specific instructions for this agent, highlighting custom requirements or priorities based on this business idea."
    )

class PlannerOutputSchema(BaseModel):
    startup_name: str = Field(
        description="A proposed, creative name for the startup."
    )
    one_liner: str = Field(
        description="A clear, punchy one-liner summarizing the startup's core value proposition."
    )
    executive_summary: str = Field(
        description="A comprehensive 2-3 paragraph executive summary of the business vision, the problem it solves, and the innovation."
    )
    tasks: List[PlannerTask] = Field(
        description="Custom-tailored task briefs assigned to the Research Agent, Finance Agent, and Marketing Agent."
    )

class PlannerAgent(BaseAgent):
    def __init__(self, client, model="gemini-flash-latest"):
        super().__init__(client, model)
        self.system_instruction = (
            "You are the Chief Executive Officer (CEO) and Lead Planner of DreamForge AI.\n"
            "Your job is to deconstruct a startup idea and build its initial skeleton.\n"
            "Generate a creative company name, a high-converting one-liner, a professional executive summary,\n"
            "and create customized task lists for the other three functional executives:\n"
            "1. Research Agent: Needs directives on which markets, segments, and competitor groups to study.\n"
            "2. Finance Agent: Needs directives on what pricing structures (e.g. freemium SaaS vs. transactional cut), variable costs, and capex items to forecast.\n"
            "3. Marketing Agent: Needs directives on positioning, target personas, and GTM growth channels.\n"
            "Make sure your instructions are highly tailored. If it is an agricultural tech app, don't give general software marketing instructions."
        )

    def plan_blueprint(self, idea, target_market=""):
        user_content = f"Startup Idea: {idea}\nTarget Market Context: {target_market}"
        result = self.generate_structured(self.system_instruction, user_content, PlannerOutputSchema)
        return result
