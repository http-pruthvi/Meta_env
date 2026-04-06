import os
import json
import time
import httpx
from openai import OpenAI
from typing import List, Dict, Any, Optional

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "openai/gpt-4o")
HF_TOKEN = os.getenv("HF_TOKEN", "")
ENV_URL = os.getenv("ENV_URL", "http://localhost:7860")

# Task Definitions
TASKS = ["task_easy_port_mismatch", "task_medium_missing_creds", "task_hard_resource_leak"]

def run_task(client: OpenAI, task_id: str):
    # Setup for [START]
    env_name = "cloud-incident-responder"
    print(f"[START] task={task_id} env={env_name} model={MODEL_NAME}")
    
    # Reset Environment
    with httpx.Client(timeout=30.0) as http_client:
        try:
            resp = http_client.post(f"{ENV_URL}/reset", json={"task_id": task_id})
            resp.raise_for_status()
            data = resp.json()
            observation = data["observation"]
        except Exception as e:
            print(f"[END] success=false steps=0 score=0.00 rewards= error=Reset failed: {str(e)}")
            return

        done = False
        step_n = 0
        rewards = []
        last_error = "null"

        while not done and step_n < 15:
            step_n += 1
            
            # Prepare prompt for LLM
            prompt = f"""Task: {observation['task_description']}
Current State:
Files: {observation['filesystem']}
Processes: {observation['processes']}
Recent Logs: {observation['logs']}
Last Result: {observation['last_action_result']}
Last Error: {observation['last_action_error']}

Instructions: You are a DevOps engineer. Issue a single CLI command to resolve the incident.
Valid commands: ls <path>, cat <file>, write <file> <content>, ps, kill <pid>, done.
Respond with ONLY the command string.
"""
            
            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=50,
                    temperature=0.0
                )
                action_str = response.choices[0].message.content.strip()
            except Exception as e:
                action_str = "done"
                last_error = str(e)

            # Step Environment
            try:
                step_resp = http_client.post(f"{ENV_URL}/step", json={"command": action_str})
                step_resp.raise_for_status()
                step_data = step_resp.json()
                
                observation = step_data["observation"]
                reward = step_data["reward"]["value"]
                done = step_data["done"]
                last_error = observation["last_action_error"] or "null"
                
                rewards.append(reward)
                
                # [STEP] output
                done_str = "true" if done else "false"
                print(f"[STEP] step={step_n} action={action_str} reward={reward:.2f} done={done_str} error={last_error}")
                
            except Exception as e:
                print(f"[STEP] step={step_n} action={action_str} reward=0.00 done=true error={str(e)}")
                done = True
                rewards.append(0.0)

        # [END] output
        success = "true" if any(r > 0.5 for r in rewards) else "false"
        score = sum(rewards) / len(TASKS) # Simplified score mapping
        # Wait, the requirement says score in [0, 1] per task. So score = sum(rewards) clamped to 1.0
        task_score = min(sum(rewards), 1.0)
        rewards_str = ",".join([f"{r:.2f}" for r in rewards])
        print(f"[END] success={success} steps={step_n} score={task_score:.2f} rewards={rewards_str}")

def main():
    if not HF_TOKEN and "localhost" not in ENV_URL:
        # Fallback if running locally without token
        pass

    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN or "dummy")
    
    for task in TASKS:
        run_task(client, task)

if __name__ == "__main__":
    main()
