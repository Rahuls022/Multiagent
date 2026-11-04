import urllib.request
import json
import time

t0 = time.time()
print("Submitting mission: 'Build a student management portal'...")
payload = {"request": "Build a student management portal", "user_id": "demo-lead-1"}
data = json.dumps(payload).encode("utf-8")
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer mock-demo-jwt-swarm-token",
}
req = urllib.request.Request("http://127.0.0.1:8000/api/pipelines", data=data, headers=headers)

try:
    resp = urllib.request.urlopen(req, timeout=300)
    res = json.loads(resp.read().decode())
    duration = time.time() - t0
    print(f"Response received in {duration:.2f}s! Status: {res.get('status')}")
    print("Workflow state:", res.get("workflow_state"))
    print("Stages:")
    for s in res.get("stages", []):
        print(f"  - {s.get('agent')}: {s.get('status')} ({s.get('duration_ms', 0)}ms)")
    if res.get("status") == "failed":
        print("Final result / Failure:", res.get("final_result"))
except urllib.error.HTTPError as e:
    print("HTTP ERROR:", e.code, e.read().decode())
except Exception as e:
    print("EXCEPTION:", type(e), e)
