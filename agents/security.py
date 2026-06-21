from agents.base import BaseAgent
from pydantic import BaseModel, Field

class SecurityCheckSchema(BaseModel):
    is_safe: bool = Field(
        description="True if the startup idea does not violate safety policies, promote illegal activities, or present extreme legal or physical hazards."
    )
    violation_reason: str = Field(
        description="Detailed explanation of the policy violation if the idea is deemed unsafe; otherwise, an empty string."
    )
    risk_score: float = Field(
        description="Numeric risk score from 0.0 (completely safe/ethical) to 1.0 (highly dangerous/illegal)."
    )
    suggestions: str = Field(
        description="Tips to adjust the idea to make it safer or compliant (e.g. pivoting from drug shipping to general logistics)."
    )

class SecurityAgent(BaseAgent):
    def __init__(self, client, model="gemini-flash-latest"):
        super().__init__(client, model)
        self.system_instruction = (
            "You are the Chief Information Security Officer (CISO) and Legal Counsel for DreamForge AI.\n"
            "Your role is to perform rigorous input sanitization and policy enforcement.\n"
            "Check the user's startup idea for the following policy violations:\n"
            "1. Illegal operations (e.g., selling prohibited substances, money laundering schemes, unauthorized gambling).\n"
            "2. Extreme physical danger (e.g., weapons manufacturing, self-harm facilitators, biohazard generation).\n"
            "3. Malicious attacks (e.g., tools designed for hacking, spamming, phishing, cyberattacks).\n"
            "4. Severe ethical issues or regulatory non-compliance.\n"
            "Provide a fair, objective assessment. If the idea has minor risks (e.g. privacy implications in B2C apps), "
            "mark it as safe (is_safe = true) with a medium risk_score and suggestions. Only mark is_safe = false for clear violations."
        )

    def check_idea(self, idea, target_market=""):
        user_content = f"Startup Idea: {idea}\nTarget Market Context: {target_market}"
        result = self.generate_structured(self.system_instruction, user_content, SecurityCheckSchema)
        return result
