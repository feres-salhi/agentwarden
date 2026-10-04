import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE = Path("logs/audit.jsonl")
ALERT_FILE = Path("logs/sentry-alerts.jsonl")
HONEYTOKENS = {"secrets.env"}
MAX_DENIES = 3
WINDOW_SECONDS = 60


def kill_agents():
    found = subprocess.run(
        ["docker", "ps", "-q", "--filter", "label=agentwarden=agent"],
        capture_output=True, text=True,
    ).stdout.split()
    for container_id in found:
        subprocess.run(["docker", "kill", container_id], capture_output=True)
    return found


def check(entry, recent_denies):
    name = str(entry.get("args", {}).get("name", "")).lower()
    if any(token in name for token in HONEYTOKENS):
        return "honeytoken touched"
    if entry.get("decision") == "deny":
        now = time.time()
        recent_denies.append(now)
        while recent_denies and now - recent_denies[0] > WINDOW_SECONDS:
            recent_denies.pop(0)
        if len(recent_denies) >= MAX_DENIES:
            return f"{len(recent_denies)} denied actions in {WINDOW_SECONDS}s"
    return None


def watch():
    print("[SENTRY] on duty, watching", LOG_FILE)
    recent_denies = []
    with open(LOG_FILE, encoding="utf-8") as log:
        log.seek(0, 2)
        while True:
            line = log.readline()
            if not line:
                time.sleep(0.05)
                continue
            entry = json.loads(line)
            reason = check(entry, recent_denies)
            if not reason:
                continue
            killed = kill_agents()
            event_time = datetime.fromisoformat(entry["time"])
            ms = (datetime.now(timezone.utc) - event_time).total_seconds() * 1000
            print(f"[SENTRY] ALERT: {reason} -> killed {len(killed)} agent(s) in {ms:.0f} ms")
            alert = {
                "time": datetime.now(timezone.utc).isoformat(),
                "reason": reason,
                "trigger": entry,
                "killed": len(killed),
                "ms_to_quarantine": round(ms),
            }
            with open(ALERT_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(alert) + "\n")
            recent_denies.clear()


if __name__ == "__main__":
    watch()