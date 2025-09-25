from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import threading
import time
import sqlite3
from typing import Optional
from src.agent import InstagramAppointmentSetter
import os

app = FastAPI(title="Instagram DM Agent MVP", description="API for controlling the Instagram DM appointment setter agent")

# Add CORS middleware to allow frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for agent control
agent_instance: Optional[InstagramAppointmentSetter] = None
agent_thread: Optional[threading.Thread] = None
agent_running = False

class AgentConfig(BaseModel):
    username: str
    password: str
    target_account: str
    api_key: str
    verification_code: Optional[str] = None

def get_db_path(username: str) -> str:
    """Generate a unique database path for each Instagram account"""
    # Clean username to create a valid filename
    clean_username = username.replace('@', '').replace('.', '_').replace('-', '_')
    return f"leads_{clean_username}.db"

def run_agent_background(config: AgentConfig):
    """Function to run the agent in background thread"""
    global agent_instance, agent_running

    try:
        # Generate unique database path for this account
        db_path = get_db_path(config.username)

        # Create agent instance with custom database
        agent_instance = InstagramAppointmentSetter(
            username=config.username,
            password=config.password,
            verification_code=config.verification_code,
            api_key=config.api_key,
            db_path=db_path
        )

        # Login
        agent_instance.login()

        # Run the agent loop
        agent_running = True
        agent_instance.run(target_account=config.target_account)

    except Exception as e:
        print(f"Agent error: {e}")
        agent_running = False

@app.post("/api/start-agent")
async def start_agent(config: AgentConfig, background_tasks: BackgroundTasks):
    """Start the Instagram DM agent"""
    global agent_thread, agent_running

    if agent_running:
        raise HTTPException(status_code=400, detail="Agent is already running")

    # Start agent in background
    background_tasks.add_task(run_agent_background, config)

    return {"message": "Agent started successfully", "status": "running"}

@app.post("/api/stop-agent")
async def stop_agent():
    """Stop the Instagram DM agent"""
    global agent_instance, agent_running

    if not agent_running:
        raise HTTPException(status_code=400, detail="Agent is not running")

    # Note: In a real implementation, you'd need a proper way to stop the agent
    # For now, we'll just set the flag
    agent_running = False

    return {"message": "Agent stop signal sent", "status": "stopping"}

@app.get("/api/status")
async def get_agent_status():
    """Get the current status of the agent"""
    global agent_running

    return {
        "running": agent_running,
        "status": "running" if agent_running else "stopped"
    }

@app.get("/api/kpis/{username}")
async def get_kpis(username: str):
    """Get Key Performance Indicators from the database for a specific account"""
    try:
        # Get the database path for this username
        db_path = get_db_path(username)

        # Check if database exists
        if not os.path.exists(db_path):
            return {
                "total_messages_sent": 0,
                "total_replies": 0,
                "total_qualified": 0,
                "response_rate": 0.0,
                "qualification_rate": 0.0,
                "message": "No data available for this account yet"
            }

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get total messages sent today
        cursor.execute("SELECT COUNT(*) FROM leads WHERE DATE(last_contacted_at) = DATE('now', 'localtime')")
        total_messages_sent = cursor.fetchone()[0]

        # Get total replies received
        cursor.execute("SELECT COUNT(*) FROM leads WHERE status = 'replied'")
        total_replies = cursor.fetchone()[0]

        # Get total qualified leads (leads that received a response from the AI)
        cursor.execute("SELECT COUNT(*) FROM leads WHERE status = 'replied'")
        total_qualified = cursor.fetchone()[0]

        # Calculate response rate
        response_rate = (total_replies / total_messages_sent * 100) if total_messages_sent > 0 else 0

        # Calculate qualification rate
        qualification_rate = (total_qualified / total_replies * 100) if total_replies > 0 else 0

        conn.close()

        return {
            "total_messages_sent": total_messages_sent,
            "total_replies": total_replies,
            "total_qualified": total_qualified,
            "response_rate": round(response_rate, 2),
            "qualification_rate": round(qualification_rate, 2)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching KPIs: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main HTML interface"""
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Error: index.html not found</h1>", status_code=404)

@app.get("/script.js", response_class=FileResponse)
async def get_script():
    """Serve the JavaScript file"""
    return FileResponse("script.js", media_type="application/javascript")

@app.get("/api")
async def api_root():
    """API root endpoint"""
    return {"message": "Instagram DM Agent MVP API", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
