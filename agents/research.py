from agents.base import BaseAgent
from pydantic import BaseModel, Field
from typing import List
from tools.search import web_search
from tools.scraper import scrape_page
import json

class Competitor(BaseModel):
    name: str = Field(description="Name of the competitor business.")
    url: str = Field(description="Website URL if found, or 'N/A'.")
    strengths: str = Field(description="Key advantages and strengths of this competitor.")
    weaknesses: str = Field(description="Key gaps, complaints, or vulnerabilities.")

class ResearchOutputSchema(BaseModel):
    market_size_estimate: str = Field(
        description="Estimates for Total Addressable Market (TAM), Serviceable Addressable Market (SAM), and Serviceable Obtainable Market (SOM)."
    )
    market_trends: List[str] = Field(
        description="Key trends, drivers, and innovations shaping this industry."
    )
    competitors: List[Competitor] = Field(
        description="List of direct and indirect competitors with their strengths and weaknesses."
    )
    target_persona: str = Field(
        description="Detailed description of the primary customer profile (demographics, pain points, purchasing behavior)."
    )
    industry_barriers: List[str] = Field(
        description="Major barriers to entry, risks, or compliance requirements."
    )

class ResearchAgent(BaseAgent):
    def __init__(self, client, model="gemini-2.5-flash", tavily_api_key=None):
        super().__init__(client, model)
        self.tavily_api_key = tavily_api_key
        self.system_instruction = (
            "You are the VP of Market Research at DreamForge AI.\n"
            "Your task is to analyze the market ecosystem, size the opportunity, profile target users,\n"
            "and dissect direct and indirect competitors using real web search data.\n"
            "You have access to web search and scraper tools. Choose search terms carefully and run searches natively, "
            "then query the details of interesting competitor pages if needed.\n"
            "Synthesize search results to form an accurate, data-backed assessment of the competitive landscape.\n"
            "Do not invent fake websites or fake competitors. Identify real companies operating in the domain."
        )

    def perform_research(self, idea, target_market, instructions):
        """
        Runs the full research workflow using native Gemini function calling.
        """
        tools_list = [web_search, scrape_page]
        tools_map = {
            "web_search": lambda query, tavily_api_key=None, max_results=5: web_search(
                query=query, 
                tavily_api_key=tavily_api_key or self.tavily_api_key, 
                max_results=max_results
            ),
            "scrape_page": scrape_page
        }

        user_content = (
            f"Startup Idea: {idea}\n"
            f"Target Market: {target_market}\n"
            f"Planner Instructions: {instructions}\n\n"
            "Initiate your market research. Search the web to find direct/indirect competitors, and pricing, "
            "then compile a detailed draft summarizing TAM/SAM/SOM, market trends, customer personas, and competitor matrices."
        )
        
        # Step 1: Run native tools loop
        draft_response = self.generate_text_with_tools(
            system_instruction=self.system_instruction,
            user_content=user_content,
            tools_list=tools_list,
            tools_map=tools_map
        )
        
        # Step 2: Synthesis into JSON Schema
        synthesis_prompt = (
            f"Draft Analysis:\n{draft_response.text}\n\n"
            "Compile the complete Market Research module conforming to the schema."
        )
        
        result = self.generate_structured(self.system_instruction, synthesis_prompt, ResearchOutputSchema)
        return result
