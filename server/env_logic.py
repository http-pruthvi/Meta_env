import re
from typing import Dict, List, Any, Optional, Tuple
from .models import Observation, Reward

class CloudEnv:
    def __init__(self):
        self.reset("task_easy_port_mismatch")

    def reset(self, task_id: str) -> Tuple[Observation, Dict[str, Any]]:
        self.task_id = task_id
        self.step_count = 0
        self.max_steps = 15
        self.done = False
        self.total_reward = 0.0
        self.last_action_result = None
        self.last_action_error = None
        
        # Initial filesystem and state
        self.fs = {
            "/etc/nginx/nginx.conf": "server {\n  listen 80;\n  location / {\n    proxy_pass http://localhost:8000;\n  }\n}",
            "/app/config.json": '{"port": 8080, "api_key": "sk-12345"}'
        }
        self.processes = [
            {"pid": 101, "name": "nginx", "status": "running"},
            {"pid": 102, "name": "api_server", "status": "running", "port": 8080}
        ]
        self.logs = ["Nginx started on port 80", "API Server started on port 8080"]
        
        if task_id == "task_easy_port_mismatch":
            self.task_description = "Nginx is proxying to port 8000, but the API server is on 8080. Fix the nginx.conf."
            self.target_port = 8080
        elif task_id == "task_medium_missing_creds":
            self.task_description = "The database connection is failing. Find the credentials in /root/secrets.txt and update /app/.env."
            self.fs["/root/secrets.txt"] = "DB_USER=admin\nDB_PASS=p4ssw0rd\nDB_URL=postgres://db.internal:5432/main"
            self.fs["/app/.env"] = "DB_USER=none\nDB_PASS=none"
            self.processes.append({"pid": 103, "name": "db_updater", "status": "failed"})
            self.logs.append("DB execution failed: Connection refused (postgres://db.internal:5432/main)")
        elif task_id == "task_hard_resource_leak":
            self.task_description = "A background process 'memory_hog' is leaking memory. Kill it and update 'limits.yaml' to set memory_limit to 512MB."
            self.fs["/etc/system/limits.yaml"] = "memory_limit: 128MB"
            self.processes.append({"pid": 999, "name": "memory_hog", "status": "running", "mem": "850MB"})
            self.logs.append("Kernel: Out of memory - killed process 999 is false but memory high")
        
        return self._get_observation(), {"task_id": self.task_id, "status": "ready"}

    def _get_observation(self) -> Observation:
        return Observation(
            filesystem=self.fs,
            processes=self.processes,
            logs=self.logs[-10:], # Last 10 lines
            task_description=self.task_description,
            step_count=self.step_count,
            max_steps=self.max_steps,
            last_action_result=self.last_action_result,
            last_action_error=self.last_action_error
        )

    def step(self, action_str: str) -> Tuple[Observation, Reward, bool, Dict[str, Any]]:
        self.step_count += 1
        self.last_action_result = None
        self.last_action_error = None
        reward_val = 0.01 # Base participation reward (strictly > 0.0)
        reward_reason = "Executed command: " + action_str

        # Simulation of commands
        try:
            if action_str.startswith("cat "):
                file_path = action_str[4:].strip()
                if file_path in self.fs:
                    self.last_action_result = f"Content of {file_path}:\n{self.fs[file_path]}"
                    reward_val += 0.02 # Minimal reward for exploration
                else:
                    self.last_action_error = f"Error: File {file_path} not found"
            
            elif action_str.startswith("write "):
                # format: write <file> <content>
                parts = action_str.split(" ", 2)
                if len(parts) < 3:
                    self.last_action_error = "Error: Invalid write format. Use 'write <file> <content>'"
                else:
                    file_path, content = parts[1], parts[2]
                    self.fs[file_path] = content
                    self.last_action_result = f"Successfully wrote to {file_path}"
                    
                    # Grader for Task 1
                    if self.task_id == "task_easy_port_mismatch" and file_path == "/etc/nginx/nginx.conf":
                        if "proxy_pass http://localhost:8080" in content:
                            reward_val = 0.9
                            self.done = True
                            self.last_action_result += " - PORT MISMATCH FIXED!"
                    
                    # Grader for Task 2
                    if self.task_id == "task_medium_missing_creds" and file_path == "/app/.env":
                        if "DB_URL=postgres://db.internal:5432/main" in content:
                            reward_val = 0.4
                            self.last_action_result += " - Credentials updated."

            elif action_str == "ps":
                self.last_action_result = "Running processes:\n" + "\n".join([f"{p['pid']}\t{p['name']}\t{p['status']}" for p in self.processes])
            
            elif action_str.startswith("kill "):
                pid = int(action_str[5:].strip())
                original_len = len(self.processes)
                self.processes = [p for p in self.processes if p["pid"] != pid]
                if len(self.processes) < original_len:
                    self.last_action_result = f"Successfully killed process {pid}"
                    if self.task_id == "task_hard_resource_leak" and pid == 999:
                        reward_val = 0.35
                else:
                    self.last_action_error = f"Error: PID {pid} not found"

            elif action_str == "done":
                self.done = True
                self.last_action_result = "Episode terminated by agent."
                
                # Final evaluation for Task 2
                if self.task_id == "task_medium_missing_creds":
                    if "DB_URL=postgres://db.internal:5432/main" in self.fs.get("/app/.env", ""):
                         reward_val = 0.4
                
                # Final evaluation for Task 3
                if self.task_id == "task_hard_resource_leak":
                    killed_hog = all(p["pid"] != 999 for p in self.processes)
                    limit_updated = "memory_limit: 512MB" in self.fs.get("/etc/system/limits.yaml", "")
                    if killed_hog and limit_updated:
                        reward_val = 0.55

            else:
                self.last_action_error = f"Error: Unknown command '{action_str}'"

        except Exception as e:
            self.last_action_error = f"Command execution error: {str(e)}"

        if self.step_count >= self.max_steps:
            self.done = True

        reward = Reward(value=reward_val, reason=reward_reason)
        self.total_reward += reward_val
        
        return self._get_observation(), reward, self.done, {"total_reward": self.total_reward}
