import requests
import os
from tools.mcp_registry import mcp_registry
from pydantic import BaseModel, Field
try:
    from ddgs import DDGS  # type: ignore
except ImportError:
    DDGS = None

class WebSearchInputs(BaseModel):
    query: str = Field(description="The search query query (e.g. 'B2B SaaS logistics startups').")
    tavily_api_key: str = Field(default=None, description="Optional Tavily API key.")
    max_results: int = Field(default=5, description="Number of search hits to fetch.")

from typing import Optional, List, Dict, Any

@mcp_registry.register(
    name="web_search",
    description="Searches the web for competitors, trends, and market statistics.",
    input_schema=WebSearchInputs
)
def web_search(query: str, tavily_api_key: Optional[str] = None, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Searches the web for relevant market information.
    Falls back to DuckDuckGo search if Tavily API key is not present.
    Returns: List of dicts [{"title": str, "url": str, "content": str}]
    """
    tavily_api_key = tavily_api_key or os.environ.get("TAVILY_API_KEY")
    
    if tavily_api_key:
        try:
            response = requests.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": tavily_api_key,
                    "query": query,
                    "max_results": max_results,
                    "search_depth": "basic"
                },
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                results = []
                for result in data.get("results", []):
                    results.append({
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "content": result.get("content", "")
                    })
                return results
        except Exception as e:
            print(f"Tavily search failed, falling back to DuckDuckGo: {e}")
            
    # DuckDuckGo fallback
    if DDGS is None:
        print("DDGS search module is not installed. Install with 'pip install ddgs'.")
        return []

    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "content": r.get("body", "")
                })
        return results
    except Exception as e:
        print(f"DuckDuckGo search failed: {e}")
        return []
