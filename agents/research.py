from agents.base import BaseAgent
from pydantic import BaseModel, Field
from typing import List
from tools.search import web_search
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
            "Synthesize search results to form an accurate, data-backed assessment of the competitive landscape.\n"
            "Do not invent fake websites or fake competitors. Identify real companies operating in the domain."
        )

    def generate_search_query(self, idea, target_market, instructions):
        """Generates a specialized search query for competitors and market trends."""
        prompt = (
            f"Business Idea: {idea}\n"
            f"Target Market: {target_market}\n"
            f"Directives: {instructions}\n\n"
            "Based on the above, write a single search query that will find the top competitors, "
            "pricing details, and market trends for this startup. Return ONLY the raw search query string, nothing else."
        )
        try:
            return self.generate_text(
                system_instruction="You are a search query optimizer. Return only the raw query string.",
                user_content=prompt
            ).strip().replace('"', '')
        except Exception:
            return f"{idea} competitors {target_market}"

    def perform_research(self, idea, target_market, instructions):
        """
        Runs the full research workflow: query generation, web search, and synthesis.
        """
        # Step 1: Generate Query
        query = self.generate_search_query(idea, target_market, instructions)
        
        # Step 2: Call Tool
        search_results = web_search(query, tavily_api_key=self.tavily_api_key)
        
        # Format search results for context
        search_context_str = ""
        if search_results:
            search_context_str = "\n\nWeb Search Results:\n"
            for i, res in enumerate(search_results, 1):
                search_context_str += f"[{i}] {res['title']}\nURL: {res['url']}\nSnippet: {res['content']}\n\n"
        else:
            search_context_str = "\n\n(No external search results found. Proceeding with static industry knowledge.)\n"

        # Step 3: Synthesis Generation
        user_content = (
            f"Startup Idea: {idea}\n"
            f"Target Market: {target_market}\n"
            f"Planner Instructions: {instructions}\n"
            f"{search_context_str}\n"
            "Please compile the complete Market Research module conforming to the schema."
        )
        
        result = self.generate_structured(self.system_instruction, user_content, ResearchOutputSchema)
        return result
