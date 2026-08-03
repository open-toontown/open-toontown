# TTBTN Game MCP Server

A [Model Context Protocol](https://modelcontextprotocol.io) server that lets an AI
assistant (Claude Code, Cursor, Claude Desktop, …) **communicate with and test the
Toontown game** whenever something is implemented.

It does three things:

1. **Controls the process stack** — starts/stops Astron + UberDOG + AI and the game
   client, exactly like `win32/startall.bat`, but programmatically.
2. **Drives a live game** — the client runs an *opt-in* localhost bridge
   (`toontown/util/mcp_bridge.py`, enabled via PRC, off by default) that the server
   uses to send chat / magic words, teleport, read avatar state, take screenshots,
   and even `exec` expressions inside the game process.
3. **Reports test results** — tails logs and scans them for crash tracebacks
   (`NameError`, `AssertionError`, `panda error code to 12`, …), plus a one-shot
   `run_smoke_test` that boots everything, auto-logs in, auto-picks a player and
   reports PASS/FAIL with the crash details.

## Requirements

- Windows (the bundled Panda3D Python is at `Panda3D/python/python.exe`)
- A system Python 3.10+ for the MCP server's own venv (the server itself does not
  need Panda3D — it only spawns processes and talks JSON)
- The game's local server stack must be runnable (Astron `astron/win32/astrond.exe`)

## Setup

```bat
:: create the venv with a system Python 3.10+ and install the MCP SDK
python -m venv mcp\.venv
mcp\.venv\Scripts\python -m pip install -r mcp\requirements.txt
```

The game is spawned with the bundled Python from `PPYTHON_PATH` — nothing is
installed into the game's Python.

## Running / testing the server

```bat
mcp\.venv\Scripts\python mcp\test_client.py
```

This connects over stdio like a real client and calls the read-only tools
(project info, status, crash scan, log tail). For the live game tools, start the
servers and the client first (see below) or call `run_smoke_test`:

```bat
mcp\.venv\Scripts\python mcp\test_client.py run_smoke_test
```

## Registering with an AI assistant

**Claude Code** (`.mcp.json` in the project root):

```json
{
  "mcpServers": {
    "ttbtn-game": {
      "command": "C:\\Users\\Shadow\\Desktop\\ttbtn\\mcp\\.venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\Shadow\\Desktop\\ttbtn\\mcp\\mcp_server.py"],
      "cwd": "C:\\Users\\Shadow\\Desktop\\ttbtn\\mcp"
    }
  }
}
```

**Cursor** — add the same entry under `Settings → MCP` (or `.cursor/mcp.json`).
**Claude Desktop** — `claude_desktop_config.json` → `mcpServers`.

## Tools

| Tool | Purpose |
| ---- | ------- |
| `get_project_info` | repo root, bundled Python, git branch |
| `game_status` | servers/client/bridge up? newest logs |
| `start_servers` / `stop_servers` | manage the local Astron+UD+AI stack |
| `start_game` | launch client: auto-login + auto pick-a-player |
| `stop_game` | cleanly quit the client (bridge → kill fallback) |
| `avatar_state` | local avatar name / zone / laff / money / place |
| `send_command` | `chat`, `teleport`, `exec`, `screenshot`, `quit` to the bridge |
| `latest_logs` | tail logs, optional grep filter |
| `scan_crash_logs` | tracebacks with file/line frames from recent logs |
| `run_smoke_test` | full boot → login → pick player → in-world, PASS/FAIL report |

### Example: test after a code change

1. `run_smoke_test` — if it fails, `scan_crash_logs` tells you the file/line.
2. For live exploration: `start_game` → `avatar_state` → `send_command chat ~maxLaff`
   → `send_command screenshot` → `stop_game`.

## How the game bridge is enabled

The server writes a generated PRC file (`mcp/runtime/smoke_*.prc`) containing:

```
want-mcp-bridge 1
mcp-bridge-port 29100
mcp-bridge-token dev
auto-avatar-choice 0
toontown-auto-login dev
```

`QuickStartLauncher` loads it via the `TTBTN_EXTRA_PRC` environment variable
(added in `toontown/launcher/QuickStartLauncher.py`). The bridge itself binds to
`127.0.0.1` only and requires the token on every request — never enable it on a
public server.

## Security notes

- The bridge is **off by default**; it only starts with `want-mcp-bridge 1`.
- It binds to `127.0.0.1` and requires a token (PRC `mcp-bridge-token` or env
  `TTBTN_MCP_TOKEN`).
- `exec` runs Python inside the game process — treat it like a debugger.
