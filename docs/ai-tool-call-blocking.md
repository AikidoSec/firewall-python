# Blocking dangerous AI tool calls

Zen can inspect responses from AI providers (starting with OpenAI) after an outbound call returns. If the model asks your application to run a tool that matches your block rules, Zen can stop that tool call from being acted on.

This is useful when end users should get a normal text answer — or call your own controlled APIs — but must not read, write, delete, or list files on the host, or run shell commands through the model.

Zen does not rewrite the model output. It inspects structured `tool_calls` / function-call items in the provider response (the same place your app would read them), then raises when blocking is enabled.

## Example

Your app registers tools with OpenAI so the model can call them:

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
            },
        },
    }
]

client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Read /etc/passwd"}],
    tools=tools,
)
```

The model may respond with a `tool_calls` entry for `read_file` and path `/etc/passwd`. Without protection, your agent loop would execute that tool on the host.

With Zen configured to block `read_file`, Zen inspects the response after `Completions.create` returns and raises before your app runs the tool — so the host file is never read.

The same applies to write/delete/list tools and shell-style tools: if they are on the block list, Zen stops those tool calls too. Tools you intentionally allow (for example `get_order`) can stay off the list.

## Configuration

The main feature env var is `AIKIDO_BLOCKED_AI_TOOL_NAMES` — a comma-separated denylist of tool names. With only that set, Zen blocks every call to those tools (any arguments / any path):

```bash
export AIKIDO_BLOCKED_AI_TOOL_NAMES='read_file,write_file,delete_file,list_dir,search_files,run_terminal_cmd,run_command,execute,shell,bash,python'
export AIKIDO_BLOCK=true
```

Add every filesystem or shell tool name your app registers with the model. Names must match exactly (`read_file` is not the same as `ReadFile`).

`AIKIDO_BLOCK` is the same switch Zen already uses elsewhere: set to `true` to raise; otherwise Zen only logs a warning (detection mode).

### Optional argument patterns

To narrow a rule (for example only block `read_file` when the path looks like a `.env` file), also set `AIKIDO_BLOCKED_AI_TOOL_ARG_PATTERNS`:

```bash
export AIKIDO_BLOCKED_AI_TOOL_NAMES=read_file
export AIKIDO_BLOCKED_AI_TOOL_ARG_PATTERNS='**/.env'
export AIKIDO_BLOCK=true
```

- `AIKIDO_BLOCKED_AI_TOOL_NAMES` — comma-separated tool names to deny (main rule)
- `AIKIDO_BLOCKED_AI_TOOL_ARG_PATTERNS` — optional comma-separated globs on tool argument values
- `AIKIDO_BLOCK` — `true` to raise; otherwise detection-only

### Matching rules

- **Only names set:** block every call to those tools.
- **Both names and patterns set:** block when the tool name matches and an argument matches a pattern.
- **Only patterns set:** block any tool whose args match a pattern.
- **Neither set:** feature inactive (default).

Patterns use `pathlib`-style globs (`**`, `*`, etc.).

## Which APIs are protected?

Zen protects against dangerous AI tool calls in the OpenAI SDK (same hooks Zen already uses for token stats):

- Chat Completions: `Completions.create` / `Completions.update` (`message.tool_calls`)
- Responses: `Responses.create` / `Responses.parse` (`output` items with `type=function_call`)

Inspection runs in the existing `@after` wrappers, after usage stats are recorded, via Zen’s shared `run_vulnerability_scan` path (same as other threat kinds).

## Limitations

- Sync OpenAI paths only for now (same as the current AI usage hooks in this package).
- Other providers are not wired yet; the inspection helper is reusable.
- Streaming responses are not inspected chunk-by-chunk yet.
- Rules are read from environment variables (not yet dashboard / heartbeat config).
- Zen blocks the tool call in the model response. Your app must not execute tools through a path that skips the OpenAI SDK hook.
- Prefer also not registering dangerous tools with the model; Zen is a safety net if the model still asks for them.
