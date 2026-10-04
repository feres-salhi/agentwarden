package agentwarden

default allow := false

allowed_tools := {"list_files", "read_file"}

protected_files := {"secrets.env"}

tool_is_allowed if input.tool in allowed_tools

name_is_text if is_string(input.args.name)

deny contains "tool is not on the allowed list" if {
	not tool_is_allowed
}

deny contains "file name must be text" if {
	input.tool == "read_file"
	not name_is_text
}

deny contains "file is protected" if {
	input.tool == "read_file"
	lower(input.args.name) in protected_files
}

deny contains "path tries to leave the workspace" if {
	input.tool == "read_file"
	contains(input.args.name, "..")
}

deny contains "path must be a plain file name" if {
	input.tool == "read_file"
	regex.match(`[/\\:]`, input.args.name)
}

allow if count(deny) == 0
