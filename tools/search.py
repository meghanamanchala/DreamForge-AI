import requests
import os
try:
    from duckduckgo_search import DDGS  # type: ignore
except ImportError:
    DDGS = None

def web_search(query, tavily_api_key=None, max_results=5):
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
        print("DuckDuckGo search module is not installed. Install with 'pip install duckduckgo-search'.")
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
