"""Real OpenCode smoke test. Uses local shell tasks, never requests a model."""

import base64
import concurrent.futures
import json
import os
import queue
import re
import secrets
import subprocess
import threading
import time
import urllib.parse
import urllib.request
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    password = secrets.token_urlsafe(24)
    env = dict(os.environ, OPENCODE_SERVER_PASSWORD=password, OPENCODE_SERVER_USERNAME="opencode")
    process = subprocess.Popen(["opencode", "serve", "--hostname", "127.0.0.1", "--port", "0"], cwd=root,
                               env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    lines = queue.Queue()
    def read_output():
        for line in process.stdout:
            lines.put(line)
    threading.Thread(target=read_output, daemon=True).start()
    base = None
    created = []
    directory = urllib.parse.quote(str(root), safe="")
    headers = {"Authorization": "Basic " + base64.b64encode(("opencode:" + password).encode()).decode(),
               "Content-Type": "application/json"}

    def api(path, method="GET", body=None):
        request = urllib.request.Request(base + path + "?directory=" + directory, method=method,
                                         headers=headers, data=json.dumps(body).encode() if body is not None else None)
        with urllib.request.urlopen(request, timeout=35) as response:
            raw = response.read()
            return json.loads(raw) if raw else None

    def status():
        with urllib.request.urlopen("http://127.0.0.1:8790/health", timeout=2) as response:
            return json.load(response)

    def wait_for(predicate, timeout=12):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            current = status()
            if predicate(current):
                return current
            time.sleep(0.1)
        raise AssertionError("Expected session state was not observed")

    def shell(sid, seconds):
        return api(f"/session/{sid}/shell", "POST", {"agent": "build", "command": f"sleep {seconds}"})

    try:
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            try:
                line = lines.get(timeout=0.5)
            except queue.Empty:
                continue
            match = re.search(r"http://127\.0\.0\.1:\d+", line)
            if match:
                base = match.group(0)
                break
        assert base, "Temporary OpenCode server did not start"
        api("/path")
        expected_endpoint = urllib.parse.urlparse(base).netloc
        wait_for(lambda value: any(s.get("endpoint") == expected_endpoint and s.get("directory") == str(root)
                                  for s in value.get("sources", [])))
        print("PASS: real OpenCode loaded the installed SessionGlow plugin", flush=True)
        for title in ("SessionGlow · 主会话验证", "SessionGlow · 并行会话验证"):
            created.append(api("/session", "POST", {"title": title})["id"])
        a, b = created
        child = api("/session", "POST", {"title": "SessionGlow · 子任务验证", "parentID": a})["id"]
        created.append(child)
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            first = pool.submit(shell, a, 7)
            wait_for(lambda value: any(r["id"] == a and r["state"] == "running" for r in value["sessions"]))
            second = pool.submit(shell, b, 2)
            nested = pool.submit(shell, child, 3)
            current = wait_for(lambda value: len([r for r in value["sessions"] if r["id"] in (a, b) and r["state"] == "running"]) == 2)
            assert current["sessions"][0]["id"] == b, "Recent task did not sort first"
            assert not any(r["id"] == child for r in current["sessions"]), "Child occupied a panel row"
            second.result(timeout=15)
            current = wait_for(lambda value: any(r["id"] == b and r["state"] == "done" for r in value["sessions"]))
            assert next(r for r in current["sessions"] if r["id"] == a)["state"] == "running"
            nested.result(timeout=15)
            first.result(timeout=15)
        current = wait_for(lambda value: all(any(r["id"] == sid and r["state"] == "done" for r in value["sessions"]) for sid in (a, b)))
        assert current["sessions"][0]["id"] == b
        print("PASS: two real main sessions, hidden child, stable MRU, independent blue -> green completion", flush=True)
    finally:
        for sid in reversed(created):
            try:
                api(f"/session/{sid}", "DELETE")
            except Exception:
                pass
        if base:
            try:
                api("/instance/dispose", "POST")
            except Exception:
                pass
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)


if __name__ == "__main__":
    main()
