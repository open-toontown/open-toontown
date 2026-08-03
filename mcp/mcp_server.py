"""
TTBTN (Toontown) MCP Server.

Lets an AI assistant (Claude Code, Cursor, etc.) communicate with and test the
Toontown game whenever something is implemented:

  * Start/stop the local server stack (Astron + UberDOG + AI).
  * Launch the game client with auto-login + auto "pick a player", talk to the
    in-game MCP bridge (chat / magic words / teleport / state / screenshots).
  * Tail logs and scan crash logs for tracebacks.
  * Run a full smoke test that boots everything, picks a toon, and reports
    whether the game crashed.

Run (stdio transport, what MCP clients expect):
    mcp/.venv/Scripts/python mcp/mcp_server.py

See mcp/README.md for registration in Claude Code / Cursor / Claude Desktop.
"""

import json
import os
import sys
import time
from datetime import datetime

# Make sibling modules importable regardless of how we are launched.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP

import game_runner as gr

mcp = FastMCP('ttbtn-game')

# Shared runtime state (tools run in the same process).
_servers = gr.ServerManager()
_client = gr.ClientLauncher()
_runtime_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'runtime')


# --------------------------------------------------------------------------- #
# Info / status
# --------------------------------------------------------------------------- #

@mcp.tool()
def get_project_info() -> dict:
    """Return basic info about the Toontown project: root path, bundled Python,
    Astron binary, and git branch."""
    import subprocess as _sp
    branch = ''
    try:
        r = _sp.run(['git', '-C', gr.PROJECT_ROOT, 'rev-parse', '--abbrev-ref', 'HEAD'],
                    capture_output=True, text=True, timeout=5)
        branch = r.stdout.strip()
    except Exception:
        pass
    return {
        'projectRoot': gr.PROJECT_ROOT,
        'bundledPython': gr.ppython_path(),
        'astrond': gr.find_astrond(),
        'gitBranch': branch,
        'logsDir': gr.log_dir(),
        'mcpBridgePort': _client.bridge_port,
    }


@mcp.tool()
def game_status() -> dict:
    """Report whether the local servers and the game client are running, whether
    the in-game MCP bridge is reachable, and which log files are newest."""
    return {
        'serversUp': _servers.are_up(),
        'messageDirector': gr.is_port_open(gr.MD_HOST, gr.MD_PORT),
        'clientAgent': gr.is_port_open(gr.MD_HOST, gr.CA_PORT),
        'clientRunning': _client.is_running(),
        'clientExitCode': _client.exit_code(),
        'bridgeReachable': _client.bridge_available(timeout_s=1.0) if _client.is_running() else False,
        'latestLogs': [os.path.basename(p) for p in gr.latest_log_paths(5)],
    }


# --------------------------------------------------------------------------- #
# Servers
# --------------------------------------------------------------------------- #

@mcp.tool()
def start_servers(timeout_s: int = 60, force_python: bool = False) -> dict:
    """Start the local server stack (Astron MessageDirector, UberDOG, AI) if it
    is not already up. Waits for ports 7199/7198. Set force_python=True to
    always (re)spawn UberDOG/AI, avoiding stale client-agent listeners."""
    return _servers.start(timeout_s=timeout_s, force_python=force_python)


@mcp.tool()
def stop_servers() -> dict:
    """Stop any local server processes this MCP server started."""
    return _servers.stop()


# --------------------------------------------------------------------------- #
# Client
# --------------------------------------------------------------------------- #

def _write_smoke_prc(avatar_choice: int, login_token: str, window_title: str,
                     extra: dict | None = None) -> str:
    os.makedirs(_runtime_dir, exist_ok=True)
    path = os.path.join(_runtime_dir, 'smoke_%s.prc' % datetime.now().strftime('%H%M%S'))
    lines = [
        'win-size 960 540',
        'fullscreen 0',
        'window-title %s' % window_title,
        'want-mcp-bridge 1',
        'mcp-bridge-port %d' % _client.bridge_port,
        'mcp-bridge-token %s' % _client.bridge_token,
        'auto-avatar-choice %d' % avatar_choice,
        'toontown-auto-login %s' % login_token,
        'toontown-auto-password %s' % login_token,
        'auto-start-local-servers 0',
        'audio-music-active 0',
        'audio-sfx-active 0',
        'want-modern-outdoor-lighting 0',
        'want-procedural-sky 0',
        'want-loading-asset-preview 0',
        'want-async-zone-prefetch 0',
        'interpolate-frames 0',
    ]
    for k, v in (extra or {}).items():
        lines.append('%s %s' % (k, v))
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    return path


@mcp.tool()
def start_game(avatar_choice: int = 0, login_token: str = 'dev',
               window_title: str = 'TTBTN MCP', wait_for_bridge_s: int = 120) -> dict:
    """Launch the game client. It auto-logs in as `login_token` and auto-picks
    the avatar at `avatar_choice` (0-based slot). Optionally waits until the
    in-game MCP bridge answers ping."""
    prc = _write_smoke_prc(avatar_choice, login_token, window_title)
    result = _client.launch(extra_prc=prc, login_token=login_token, avatar_choice=avatar_choice,
                            window_title=window_title)
    if not result.get('launched'):
        return result
    deadline = time.time() + wait_for_bridge_s
    while time.time() < deadline and _client.is_running():
        if _client.bridge_available(timeout_s=1.5):
            result['bridgeReachable'] = True
            result['pid'] = result.get('pid')
            return result
        time.sleep(2)
    result['bridgeReachable'] = False
    result['note'] = 'bridge not reachable within %ss (still booting?)' % wait_for_bridge_s
    return result


@mcp.tool()
def stop_game() -> dict:
    """Ask the game client to quit cleanly (via the bridge), killing the process
    if it does not exit in time."""
    return _client.stop()


@mcp.tool()
def avatar_state() -> dict:
    """Query the running client for the local avatar's state (name, zone, laff,
    money, connection). Returns an error if the client/bridge is unavailable."""
    st = _client.poll_state()
    if st is None:
        return {'error': 'client or bridge not reachable'}
    return st


@mcp.tool()
def send_command(cmd: str, args: dict | None = None) -> dict:
    """Send a command to the in-game MCP bridge. Supported commands:
      - chat:      {"text": "~maxLaff"}           send chat / magic word
      - teleport:  {"zoneId": 22000}              zone-teleport the avatar
      - exec:      {"code": "localAvatar.getZoneId()"}  run a Python expression
      - screenshot: {"name": "shot1"}             save a PNG under logs/mcp/
      - state:     {}                              avatar/game state
      - quit:      {"code": 0}                    exit the game client
    """
    return _client.bridge_request(cmd, args or {})


# --------------------------------------------------------------------------- #
# Logs
# --------------------------------------------------------------------------- #

@mcp.tool()
def latest_logs(n: int = 40, grep: str = '', since_hours: float = 24) -> dict:
    """Tail the newest client/server log files. `grep` filters matching lines."""
    paths = gr.latest_log_paths(5)
    if not paths:
        return {'logs': [], 'note': 'no logs found in %s' % gr.log_dir()}
    out = []
    for p in paths[:3]:
        body = gr.tail_lines(p, n_lines=n)
        if grep:
            body = '\n'.join([ln for ln in body.splitlines() if grep.lower() in ln.lower()])
            if not body.strip():
                continue
        out.append({'file': os.path.basename(p), 'body': body[-4000:]})
    return {'logs': out}


@mcp.tool()
def scan_crash_logs(max_results: int = 25, since_hours: float = 24) -> dict:
    """Scan recent logs for crash tracebacks (NameError, AssertionError,
    AttributeError, import failures, 'panda error code to 12', etc.). Each match
    includes the traceback frames with file/line so the cause is easy to find."""
    crashes = gr.scan_crash_logs(max_results=max_results, since_hours=since_hours)
    return {'crashes': crashes, 'count': len(crashes)}


# --------------------------------------------------------------------------- #
# Smoke test
# --------------------------------------------------------------------------- #

@mcp.tool()
def run_smoke_test(timeout_s: int = 240, avatar_choice: int = 0,
                   login_token: str = 'dev', stop_client: bool = True,
                   stop_servers: bool = False, attempts: int = 2) -> dict:
    """Full regression flow: ensure local servers are up, launch the client with
    auto-login + auto pick-a-player, poll until the avatar is in the world or a
    crash/traceback appears, then stop the client. Returns a PASS/FAIL report
    with crash details and a log tail. If the first attempt stalls (local
    server-stack race), it restarts the stack and retries. Use this after
    implementing game code."""
    report = {
        'test': 'smoke: boot -> login -> pick player -> in world',
        'startedAt': datetime.now().strftime('%H:%M:%S'),
        'passed': False,
        'attempts': max(1, int(attempts)),
    }

    for attempt in range(1, report['attempts'] + 1):
        report['attempt'] = attempt
        report['servers'] = _servers.start(force_python=True)
        if not report['servers'].get('mdUp') or not report['servers'].get('caUp'):
            report['note'] = 'server stack failed to come up'
            report['crashes'] = gr.scan_crash_logs(since_hours=2)[:5]
            break

        prc = _write_smoke_prc(avatar_choice, login_token, 'TTBTN MCP Smoke Test')
        launch = _client.launch(extra_prc=prc, login_token=login_token, avatar_choice=avatar_choice,
                                window_title='TTBTN MCP Smoke Test')
        report['clientPid'] = launch.get('pid')
        report['clientStdoutLog'] = launch.get('stdoutLog')
        report['prcFile'] = prc

        deadline = time.time() + timeout_s
        last_state = None
        crashes = []
        while time.time() < deadline:
            code = _client.exit_code()
            if code is not None:
                report['clientExited'] = code
                report['note'] = 'client exited early (code %s)' % code
                crashes = gr.scan_crash_logs(since_hours=2)
                report['crashes'] = crashes[:6]
                break
            st = _client.poll_state()
            if st:
                last_state = st
                av = st.get('avatar') or {}
                if av.get('name') and st.get('connected'):
                    report['passed'] = True
                    report['pickedAvatar'] = av
                    report['place'] = st.get('place')
                    report['note'] = 'avatar picked and connected; no crash'
                    break
            crashes = gr.scan_crash_logs(since_hours=2)
            if crashes:
                report['note'] = 'crash traceback detected in logs'
                report['crashes'] = crashes[:6]
                break
            time.sleep(3)
        else:
            report['note'] = 'timed out after %ss without reaching in-world state' % timeout_s
            report['crashes'] = gr.scan_crash_logs(since_hours=2)[:6]

        report['state'] = last_state
        if report.get('passed'):
            break
        if attempt < report['attempts']:
            # Stack race (e.g. astron interest timeout): tear down and retry.
            try:
                _client.stop()
            except Exception:
                pass
            try:
                _servers.restart(timeout_s=90)
            except Exception:
                pass
            report['state'] = None

    if stop_client:
        report['stoppedClient'] = _client.stop()
    if stop_servers:
        report['stoppedServers'] = _servers.stop()
    newest = gr.latest_log_paths(1)
    report['logTail'] = gr.tail_lines(newest[0], 30) if newest else ''
    stdout_log = report.get('clientStdoutLog')
    if stdout_log and os.path.isfile(stdout_log):
        report['clientStdoutTail'] = gr.tail_lines(stdout_log, 25)
    report['finishedAt'] = datetime.now().strftime('%H:%M:%S')
    return report


def main():
    mcp.run()


if __name__ == '__main__':
    main()
