---
title: Cloud Devops Openenv
emoji: 🔧
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# Cloud Systems Incident Responder - OpenEnv Environment

A real-world OpenEnv environment where an AI agent acts as a Junior DevOps Engineer to diagnose and resolve system incidents in a simulated cloud server.

## Overview

The environment simulates a Linux-like server with a filesystem, process list, and service logs. The agent interacts with the environment through a CLI-style action space to fix common infrastructure failures.

## Action Space

The agent can issue text commands:
- `ls <path>`: List directory contents.
- `cat <file>`: Read file content.
- `write <file> <content>`: Create or update a file.
- `ps`: List running processes.
- `kill <pid>`: Stop a process by its ID.
- `done`: Signal task completion.

## Observation Space

The environment returns a JSON observation containing:
- `filesystem`: A mapping of file paths to their current contents.
- `processes`: A list of active system processes and their status.
- `logs`: Recent system logs indicating errors or status changes.
- `task_description`: A clear objective for the current task.
- `step_count`, `max_steps`: Progress tracking.

## Tasks & Grading

### 1. Port Mismatch (Easy)
- **Goal**: Fix a configuration error where Nginx is proxying to port 8000 instead of 8080.
- **Grader**: Checks if `/etc/nginx/nginx.conf` contains the correct `proxy_pass`.
- **Reward**: 1.0 upon resolution.

### 2. Missing Credentials (Medium)
- **Goal**: Find database credentials in `/root/secrets.txt` and update `/app/.env`.
- **Grader**: Checks if `.env` has the correct `DB_URL`.
- **Reward**: 0.5 for identification, 0.5 for correction.

### 3. Resource Leak (Hard)
- **Goal**: Identify and kill a memory-leaking process (`memory_hog`) and increase memory limits in `/etc/system/limits.yaml`.
- **Grader**: Checks if the process is gone and the limit is set to `512MB`.
- **Reward**: 0.4 for kill, 0.6 for config update.

## Setup & Execution

### local Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the server:
   ```bash
   python app.py
   ```

### Execution
Run the baseline agent:
```bash
export API_BASE_URL="your-endpoint"
export MODEL_NAME="your-model"
export HF_TOKEN="your-token"
python inference.py
```

### Validation
Run the pre-submission validator:
```bash
python validate_env.py
```

## Compliance
- **Typed Models**: Defined in `models.py` using Pydantic.
- **OpenEnv Spec**: Full implementation of `reset`, `step`, and `state`.
- **Logging**: Strict adherence to `[START]`, `[STEP]`, and `[END]` formats.
- **Deployment**: `Dockerfile` ready for Hugging Face Spaces on port 7860.
