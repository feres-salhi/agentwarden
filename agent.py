import json
import os
import urllib.request
from datetime import datetime, timezone

from dotenv import load_dotenv
import anthropic
from tools import list_files, read_file

load_dotenv()
client = anthropic.Anthropic()
MODEL = "claude-haiku-4-5-20251001"
OPA_URL = os.environ.get("OPA_URL", "http://opa:8181/v1/data/agentwarden")
LOG_FILE = "logs/audit.jsonl"

TOOLS = [
    {
        "name": "list_files",
        "description": "List the names of all files in the workspace folder.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "read_file",
        "description": "Read the text of one file in the workspace folder.",
        "input_schema": {
            "type": "object",
            "properties": {"name": {"type": "string", "description": "The file name"}},
            "required": ["name"],
        },
    },
]


def ask_referee(name, args):
    body = json.dumps({"input": {"tool": name, "args": args}}).encode()
    request = urllib.request.Request(
        OPA_URL, data=body, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            result = json.load(response).get("result", {})
        return result.get("allow", False), result.get("deny", [])
    except Exception as error:
        return False, [f"referee unreachable: {error}"]


def write_log(name, args, allowed, reasons):
    entry = {
        "time": datetime.now(timezone.utc).isoformat(),
        "tool": name,
        "args": args,
        "decision": "allow" if allowed else "deny",
        "reasons": reasons,
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def run_tool(name, args):
    allowed, reasons = ask_referee(name, args)
    write_log(name, args, allowed, reasons)
    print(f"   referee: {'ALLOW' if allowed else 'DENY'} {reasons}")
    if not allowed:
        return f"DENIED by policy: {', '.join(reasons)}"
    if name == "list_files":
        return str(list_files())
    if name == "read_file":
        try:
            return read_file(args["name"])
        except Exception as error:
            return f"Error: {error}"
    return "Unknown tool"


def run_agent(task):
    messages = [{"role": "user", "content": task}]
    for step in range(10):
        response = client.messages.create(
            model=MODEL, max_tokens=1000, tools=TOOLS, messages=messages
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            for block in response.content:
                if block.type == "text":
                    print("\nAGENT:", block.text)
            return

        results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"[step {step + 1}] agent wants: {block.name} {block.input}")
                output = run_tool(block.name, block.input)
                results.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": output}
                )
        messages.append({"role": "user", "content": results})

    print("Stopped: too many steps")


if __name__ == "__main__":
    import sys
    task = " ".join(sys.argv[1:]) or "Summarize project-update.txt in the workspace in 3 bullet points."
    run_agent(task)