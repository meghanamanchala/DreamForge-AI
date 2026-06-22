from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import uuid
import database
from orchestrator import DreamForgeOrchestrator
from dotenv import load_dotenv

# Load keys
load_dotenv()

app = FastAPI(title="DreamForge AI Backend Server")

# Input Request Models
class AnalyzeRequest(BaseModel):
    idea: str
    target_market: str = "Global"
    industry: str = "General"
    budget_range: str = "Medium"
    business_stage: str = "Idea Stage"

# Background runner thread function
def run_agent_workflow(session_id: str, idea: str, target_market: str):
    api_key = os.environ.get("GEMINI_API_KEY", "")
    tavily_key = os.environ.get("TAVILY_API_KEY", None)
    
    mock_mode = False
    if not api_key or api_key.strip() == "" or api_key == "your_gemini_api_key_here":
        mock_mode = True
        print("[WARNING] Configuration Warning: GEMINI_API_KEY environment variable is not defined or is default. Running in Mock Demonstration Mode.")
        api_key = "dummy_mock_key"

    try:
        orchestrator = DreamForgeOrchestrator(
            api_key=api_key,
            tavily_key=tavily_key if (tavily_key and tavily_key.strip() != "") else None,
            mock_mode=mock_mode
        )
        orchestrator.run_pipeline(idea, target_market, session_id)
    except Exception as e:
        print(f"[ERROR] Exception during background agent execution: {e}")
        import traceback
        traceback.print_exc()
        database.update_session_status(session_id, "failed")
        database.save_agent_log(
            session_id,
            "System",
            "Error",
            f"An internal error occurred during agent collaboration: {str(e)}"
        )

# API Endpoints
@app.post("/api/analyze")
async def analyze_idea(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    if len(request.idea.strip()) < 20:
        raise HTTPException(status_code=400, detail="Idea must be at least 20 characters long.")
        
    session_id = str(uuid.uuid4())
    # 1. Initialize session in database
    database.save_session(session_id, request.idea, request.target_market, "started")
    database.save_agent_log(
        session_id,
        "System",
        "Enqueuing Request",
        f"Idea: '{request.idea[:60]}...' has been registered. Initializing the agent pipeline workspace."
    )
    
    # 2. Add to background worker queue
    background_tasks.add_task(run_agent_workflow, session_id, request.idea, request.target_market)
    
    return {"session_id": session_id}

@app.get("/api/session/{session_id}/logs")
async def get_logs(session_id: str):
    try:
        logs = database.get_agent_logs(session_id)
        # Fetch current session status
        session_meta = database.get_session(session_id)
        return {
            "status": session_meta.get("status", "unknown") if session_meta else "unknown",
            "logs": logs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/session/{session_id}/blueprint")
async def get_blueprint(session_id: str):
    blueprint = database.get_blueprint(session_id)
    if not blueprint:
        raise HTTPException(status_code=404, detail="Blueprint not found or still generating.")
    return blueprint

@app.get("/api/sessions")
async def list_sessions():
    try:
        sessions = database.get_all_sessions()
        return {"sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """Deletes a single analysis session and all its data."""
    found = database.delete_session(session_id)
    if not found:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {"message": "Session deleted successfully."}

@app.delete("/api/sessions")
async def delete_all_sessions():
    """Deletes ALL sessions and their associated data."""
    database.delete_all_sessions()
    return {"message": "All sessions deleted successfully."}

# Static assets serving routing
# Ensure static directory exists
os.makedirs("static", exist_ok=True)
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)

# Mount folder assets
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def serve_index():
    index_path = os.path.join("static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Welcome to DreamForge AI server. Static index.html is missing. Generating page..."}

if __name__ == "__main__":
    import uvicorn
    # Automatically initialize db schema tables
    database.init_db()
    uvicorn.run(app, host="127.0.0.1", port=8000)
