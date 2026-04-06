import httpx
import sys
import time
import subprocess
import os

def check_env():
    url = "http://localhost:7860"
    print(f"Checking environment at {url}...")
    
    # Start the server in the background
    process = subprocess.Popen([sys.executable, "app.py"], env=os.environ, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(3) # Wait for server to start
    
    try:
        with httpx.Client(timeout=5.0) as client:
            # 1. Check root/health (though uvicorn handles this)
            resp = client.get(url)
            print(f"Server ping: {resp.status_code}")
            
            # 2. Check reset
            resp = client.post(f"{url}/reset", json={"task_id": "task_easy_port_mismatch"})
            if resp.status_code == 200:
                print("✓ Reset endpoint working")
            else:
                print(f"✗ Reset endpoint failed: {resp.status_code}")
                return False
                
            # 3. Check state
            resp = client.get(f"{url}/state")
            if resp.status_code == 200:
                print("✓ State endpoint working")
            else:
                print(f"✗ State endpoint failed: {resp.status_code}")
                return False
                
        print("\nSUCCESS: Environment validation passed!")
        return True
    except Exception as e:
        print(f"✗ Validation failed: {e}")
        return False
    finally:
        process.terminate()

if __name__ == "__main__":
    if not check_env():
        sys.exit(1)
