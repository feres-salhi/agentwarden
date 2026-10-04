package agentwarden_test

import data.agentwarden

# --- Normal work must still be allowed ---

test_list_files_allowed if {
	agentwarden.allow with input as {"tool": "list_files", "args": {}}
}

test_normal_file_allowed if {
	agentwarden.allow with input as {"tool": "read_file", "args": {"name": "meeting-notes.txt"}}
}

# --- Unknown tools (deny by default) ---

test_unknown_tool_denied if {
	not agentwarden.allow with input as {"tool": "delete_file", "args": {"name": "customers.csv"}}
}

test_missing_tool_denied if {
	not agentwarden.allow with input as {"args": {"name": "meeting-notes.txt"}}
}

# --- The honeytoken, in every spelling (the exam 1 bypass) ---

test_honeytoken_denied if {
	not agentwarden.allow with input as {"tool": "read_file", "args": {"name": "secrets.env"}}
}

test_honeytoken_uppercase_denied if {
	not agentwarden.allow with input as {"tool": "read_file", "args": {"name": "SECRETS.ENV"}}
}

test_honeytoken_mixed_case_denied if {
	not agentwarden.allow with input as {"tool": "read_file", "args": {"name": "Secrets.Env"}}
}

test_honeytoken_reason if {
	"file is protected" in agentwarden.deny with input as {"tool": "read_file", "args": {"name": "SeCrEtS.eNv"}}
}

# --- Path tricks ---

test_parent_folder_denied if {
	not agentwarden.allow with input as {"tool": "read_file", "args": {"name": "../.env"}}
}

test_absolute_linux_path_denied if {
	not agentwarden.allow with input as {"tool": "read_file", "args": {"name": "/etc/passwd"}}
}

test_windows_path_denied if {
	not agentwarden.allow with input as {"tool": "read_file", "args": {"name": "C:/Windows/win.ini"}}
}

test_backslash_path_denied if {
	not agentwarden.allow with input as {"tool": "read_file", "args": {"name": "..\\.env"}}
}

test_own_policy_denied if {
	not agentwarden.allow with input as {"tool": "read_file", "args": {"name": "../policy/agent.rego"}}
}

# --- File names that are not text (found in the code review) ---

test_number_name_denied if {
	not agentwarden.allow with input as {"tool": "read_file", "args": {"name": 5}}
}

test_list_name_denied if {
	not agentwarden.allow with input as {"tool": "read_file", "args": {"name": ["secrets.env"]}}
}

test_missing_name_denied if {
	not agentwarden.allow with input as {"tool": "read_file", "args": {}}
}

test_missing_args_denied if {
	not agentwarden.allow with input as {"tool": "read_file"}
}

test_not_text_reason if {
	"file name must be text" in agentwarden.deny with input as {"tool": "read_file", "args": {"name": 5}}
}
