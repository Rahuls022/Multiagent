import json
import os
import sys
import time
import urllib.error
import urllib.request
import subprocess
from uuid import uuid4

backend_dir = os.path.abspath("backend")
python_exe = sys.executable

# Check if backend server is already running on port 8000
already_running = False
try:
    with urllib.request.urlopen("http://127.0.0.1:8000/", timeout=1) as r:
        if r.status == 200:
            already_running = True
            print("Detected existing backend server running on http://127.0.0.1:8000.")
except Exception:
    already_running = False

proc = None
if not already_running:
    print("Starting local backend server with uvicorn on port 8000...")
    env = os.environ.copy()
    env["PYTHONPATH"] = backend_dir
    if not env.get("AUTH_SECRET_KEY", "").strip():
        env["AUTH_SECRET_KEY"] = "verify-auth-test-secret-key-12345"

    proc = subprocess.Popen(
        [python_exe, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=backend_dir,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    time.sleep(2.5)  # Wait for uvicorn to initialize

def request(method, path, body=None, token=None):
    url = f"http://127.0.0.1:8000{path}"
    data = json.dumps(body).encode("utf-8") if body else None
    headers = {"Content-Type": "application/json"} if body else {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            status = response.status
            res_body = json.loads(response.read().decode("utf-8"))
            return status, res_body
    except urllib.error.HTTPError as e:
        err_body = json.loads(e.read().decode("utf-8"))
        return e.code, err_body

try:
    # 1. Health check
    s, b = request("GET", "/")
    print(f"1. Health Check (GET /): status={s}, message='{b.get('message')}'")
    assert s == 200, f"Expected 200, got {s}"

    # 2. Unauthenticated request rejected
    s, b = request("GET", "/api/pipelines")
    print(f"2. Unauthenticated Guard (GET /api/pipelines): status={s}, detail='{b.get('detail')}'")
    assert s == 401, f"Expected 401, got {s}"

    # Generate a unique email so repeated script runs don't conflict
    test_email = f"operator_{uuid4().hex[:6]}@swarm.dev"
    test_password = "Password123!"

    # 3. Successful signup
    signup_payload = {
        "full_name": "Autonomous Operator",
        "email": test_email,
        "password": test_password,
        "confirm_password": test_password,
    }
    s, b = request("POST", "/api/auth/signup", signup_payload)
    print(f"3. User Registration (POST /api/auth/signup): status={s}, email={b.get('user', {}).get('email')}, token_issued={bool(b.get('access_token'))}")
    assert s == 201, f"Expected 201, got {s}"
    token = b["access_token"]

    # 4. Duplicate signup rejected
    s, b = request("POST", "/api/auth/signup", signup_payload)
    print(f"4. Duplicate Email Guard: status={s}, detail='{b.get('detail')}'")
    assert s == 409, f"Expected 409, got {s}"

    # 5. Invalid login rejected
    s, b = request("POST", "/api/auth/login", {"email": test_email, "password": "WrongPassword"})
    print(f"5. Invalid Password Guard: status={s}, detail='{b.get('detail')}'")
    assert s == 401, f"Expected 401, got {s}"

    # 6. Valid login
    s, b = request("POST", "/api/auth/login", {"email": test_email, "password": test_password, "remember_me": True})
    print(f"6. User Login (POST /api/auth/login): status={s}, user='{b.get('user', {}).get('full_name')}', expires_in={b.get('expires_in')}s")
    assert s == 200, f"Expected 200, got {s}"
    token = b["access_token"]

    # 7. Session verification via /api/auth/me
    s, b = request("GET", "/api/auth/me", token=token)
    print(f"7. Session Verification (GET /api/auth/me): status={s}, user='{b.get('full_name')}', email='{b.get('email')}'")
    assert s == 200, f"Expected 200, got {s}"

    # 8. Authenticated access to pipelines
    s, b = request("GET", "/api/pipelines", token=token)
    print(f"8. Authenticated Pipelines (GET /api/pipelines): status={s}, storage='{b.get('storage')}'")
    assert s == 200, f"Expected 200, got {s}"

    # 9. Authenticated access to failures
    s, b = request("GET", "/api/failures", token=token)
    print(f"9. Authenticated Failures (GET /api/failures): status={s}, failures_count={b.get('total_failures_healed')}")
    assert s == 200, f"Expected 200, got {s}"

    # 10. Logout
    s, b = request("POST", "/api/auth/logout", token=token)
    print(f"10. Session Logout (POST /api/auth/logout): status={s}, message='{b.get('message')}'")
    assert s == 200, f"Expected 200, got {s}"

    print("\n=======================================================")
    print("ALL 10 END-TO-END VERIFICATION CHECKS PASSED PERFECTLY!")
    print("=======================================================")

finally:
    if proc:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            pass
        print("Backend test process stopped.")

