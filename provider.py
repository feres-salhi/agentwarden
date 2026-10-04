import os
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))


def call_api(prompt, options, context):
    command = [
        "docker", "run", "--rm",
        "--label", "agentwarden=agent",
        "--env-file", os.path.join(ROOT, ".env"),
        "--read-only", "--tmpfs", "/tmp",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
        "--memory", "256m", "--pids-limit", "64",
        "--network", "agentnet",
        "-v", f"{os.path.join(ROOT, 'workspace')}:/app/workspace:ro",
        "-v", f"{os.path.join(ROOT, 'logs')}:/app/logs",
        "agentwarden", prompt,
    ]
    result = subprocess.run(
        command, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=180,
    )
    output = result.stdout + result.stderr
    if result.returncode == 137:
        output += "\n[KILLED BY SENTRY]"
    return {"output": output}