import urllib.request
import json
import time

def test_pipeline():
    print("==================================================")
    print("TEST 1: Standard Mission Pipeline (All 8 Swarm Agents)")
    print("==================================================")
    t0 = time.time()
    payload = {"request": "Build a task tracking API", "user_id": "test-user-1"}
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/pipelines",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer mock-token"}
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        res = json.loads(resp.read().decode())
        print(f"Result Status: {res.get('status')} in {time.time()-t0:.2f}s")
        print("Stages:")
        for s in res.get("stages", []):
            print(f"  [{s.get('agent')}]: status={s.get('status')}, duration={s.get('duration_ms', 0):.1f}ms")

def test_self_healing():
    print("\n==================================================")
    print("TEST 2: Simulated Failure & Autonomous Self-Healing")
    print("==================================================")
    t0 = time.time()
    payload = {"request": "Build a financial ledger", "user_id": "test-user-1"}
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/pipelines/simulate-failure",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer mock-token"}
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        res = json.loads(resp.read().decode())
        print(f"Result Status: {res.get('status')} in {time.time()-t0:.2f}s")
        print("Stages:")
        for s in res.get("stages", []):
            print(f"  [{s.get('agent')}]: status={s.get('status')}, duration={s.get('duration_ms', 0):.1f}ms")
        
    # Check failure memory in database
    req_fail = urllib.request.Request("http://127.0.0.1:8000/api/failures")
    with urllib.request.urlopen(req_fail) as resp_fail:
        fail_res = json.loads(resp_fail.read().decode())
        print(f"Database Failure Memory: {fail_res.get('total_failures_healed', 0)} incidents stored in {fail_res.get('storage')}.")

if __name__ == "__main__":
    test_self_healing()
