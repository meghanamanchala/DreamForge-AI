import requests
from bs4 import BeautifulSoup
from tools.mcp_registry import mcp_registry
from pydantic import BaseModel, Field

class ScrapeInputs(BaseModel):
    url: str = Field(description="The exact URL of the website or competitor landing page to crawl.")

from typing import Dict

@mcp_registry.register(
    name="scrape_page_content",
    description="Fetches and parses a specific URL to clean HTML into readable text/markdown.",
    input_schema=ScrapeInputs
)
def scrape_page(url: str) -> Dict[str, str]:
    """
    Scrapes the text content of a webpage and returns the title and content.
    Returns: Dict {"title": str, "content": str, "status": str}
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return {
                "title": "",
                "content": "",
                "status": f"Failed to fetch. Status code: {response.status_code}"
            }
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "meta", "noscript", "header", "footer"]):
            script.decompose()
            
        title = soup.title.string.strip() if soup.title else ""
        
        # Get text and clean up whitespace
        text = soup.get_text(separator=' ')
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Cap length to avoid token limit issues
        max_chars = 15000
        if len(clean_text) > max_chars:
            clean_text = clean_text[:max_chars] + "\n...[Content truncated due to size limit]..."
            
        return {
            "title": title,
            "content": clean_text,
            "status": "success"
        }
    except Exception as e:
        return {
            "title": "",
            "content": "",
            "status": f"Error occurred: {str(e)}"
        }
