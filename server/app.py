import os
from fastapi import FastAPI, HTTPException, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from .models import ResetRequest, ResetResponse, StepRequest, StepResponse, StateResponse, Observation, Reward
from .env_logic import CloudEnv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Cloud Systems Incident Responder - OpenEnv")

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for environment state (one per app instance for simplicity)
env = CloudEnv()

@app.get("/")
async def root():
    return {"status": "running", "environment": "Cloud Systems Incident Responder", "api": "OpenEnv"}

@app.post("/reset", response_model=ResetResponse)
async def reset(request: ResetRequest = Body(None)):
    # Handle missing body or missing task_id
    task_id = request.task_id if (request and request.task_id) else "task_easy_port_mismatch"
    obs, info = env.reset(task_id)
    return ResetResponse(observation=obs, info=info)

@app.post("/step", response_model=StepResponse)
async def step(request: StepRequest = Body(None)):
    # Handle missing body or missing command
    command = request.command if (request and request.command) else "ls"
    obs, reward, done, info = env.step(command)
    return StepResponse(observation=obs, reward=reward, done=done, info=info)

@app.get("/state", response_model=StateResponse)
async def state():
    return StateResponse(
        task_id=env.task_id,
        step_count=env.step_count,
        max_steps=env.max_steps,
        is_active=not env.done
    )

def start():
    import uvicorn
    # Use port 7860 for Hugging Face Spaces
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run("server.app:app", host="0.0.0.0", port=port, reload=False)

if __name__ == "__main__":
    start()
