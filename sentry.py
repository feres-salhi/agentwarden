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
    args = entry.get("args")
    name = str(args.get("name", "")).lower() if isinstance(args, dict) else ""
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


def ms_since(entry):
    try:
        event_time = datetime.fromisoformat(entry["time"])
        return (datetime.now(timezone.utc) - event_time).total_seconds() * 1000
    except (KeyError, TypeError, ValueError):
        return None


def handle(entry, recent_denies):
    reason = check(entry, recent_denies)
    if not reason:
        return
    killed = kill_agents()
    ms = ms_since(entry)
    shown = f"{ms:.0f} ms" if ms is not None else "unknown time"
    print(f"[SENTRY] ALERT: {reason} -> killed {len(killed)} agent(s) in {shown}")
    alert = {
        "time": datetime.now(timezone.utc).isoformat(),
        "reason": reason,
        "trigger": entry,
        "killed": len(killed),
        "ms_to_quarantine": round(ms) if ms is not None else None,
    }
    with open(ALERT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(alert) + "\n")
    recent_denies.clear()


def watch():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOG_FILE.touch(exist_ok=True)
    print("[SENTRY] on duty, watching", LOG_FILE)
    recent_denies = []
    buffer = ""
    with open(LOG_FILE, encoding="utf-8") as log:
        log.seek(0, 2)
        while True:
            chunk = log.readline()
            if not chunk:
                time.sleep(0.05)
                continue
            buffer += chunk
            if not buffer.endswith("\n"):
                continue
            line, buffer = buffer.strip(), ""
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                print("[SENTRY] WARNING: skipped an unreadable log line (still on duty)")
                continue
            if not isinstance(entry, dict):
                print("[SENTRY] WARNING: skipped a log line that is not a record (still on duty)")
                continue
            try:
                handle(entry, recent_denies)
            except Exception as error:
                print(f"[SENTRY] WARNING: error while handling a log line: {error} (still on duty)")


if __name__ == "__main__":
    watch()
