from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

class Observation(BaseModel):
    filesystem: Dict[str, str] = Field(default_factory=dict, description="Simulated file contents")
    processes: List[Dict[str, Any]] = Field(default_factory=list, description="List of running services")
    logs: List[str] = Field(default_factory=list, description="Recent system logs")
    task_description: str = ""
    step_count: int = 0
    max_steps: int = 15
    last_action_result: Optional[str] = None
    last_action_error: Optional[str] = None

class StepRequest(BaseModel):
    command: Optional[str] = Field(None, description="The CLI command to execute (e.g., 'ls', 'cat', 'write', 'restart')")

class ResetRequest(BaseModel):
    task_id: Optional[str] = Field(None, description="The task identifier (easy, medium, hard)")

class ResetResponse(BaseModel):
    observation: Observation
    info: Dict[str, Any] = {}

class Reward(BaseModel):
    value: float = 0.0
    reason: str = ""

class StepResponse(BaseModel):
    observation: Observation
    reward: Reward
    done: bool
    info: Dict[str, Any] = {}

class StateResponse(BaseModel):
    task_id: str
    step_count: int
    max_steps: int
    is_active: bool
