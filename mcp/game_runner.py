"""
Game process management + log analysis for the TTBTN MCP server.

This module is deliberately pure-Python (stdlib only) so it can be imported by
both the MCP server and standalone test scripts. It knows how to:

  * Start/stop the local Astron + UberDOG + AI server stack.
  * Launch the game client with a generated PRC override (auto-login,
    auto-avatar-choice, MCP bridge) and a LOGIN_TOKEN.
  * Talk to the in-game MCP bridge (localhost JSON socket).
  * Tail the newest client/server logs and scan them for crash tracebacks.
"""

import json
import os
import re
import socket
import subprocess
import sys
import threading
import time
from datetime import datetime

# --------------------------------------------------------------------------- #
# Paths / environment
# --------------------------------------------------------------------------- #

ROOT = os.path.dirname(os.path.abspath(__file__))  # .../ttbtn/mcp
PROJECT_ROOT = os.path.dirname(ROOT)
RUNTIME_DIR = os.path.join(ROOT, 'runtime')
RUNTIME_LOGS = os.path.join(RUNTIME_DIR, 'logs')

MD_HOST = '127.0.0.1'
MD_PORT = 7199
CA_PORT = 7198
EVENTLOGGER_IP = '127.0.0.1:7197'
STATESERVER = '4002'

DEFAULT_BRIDGE_PORT = 29100
DEFAULT_BRIDGE_TOKEN = 'dev'

CRASH_PATTERNS = [
    r'Traceback \(most recent call last\):',
    r'\b(AssertionError|NameError|AttributeError|ImportError|KeyError|TypeError|'
    r'ValueError|RuntimeError|IndexError|ZeroDivisionError|OSError|EOFError|'
    r'OverflowError|MemoryError)\b',
    r'Exception (occurred|in|exit)|panda error code to 12|Client exception:',
]


def ppython_path():
    try:
        with open(os.path.join(PROJECT_ROOT, 'PPYTHON_PATH'), 'r', encoding='utf-8') as f:
            p = f.read().strip()
        if p and not os.path.isabs(p):
            p = os.path.join(PROJECT_ROOT, p)
        p = os.path.normpath(p)
        if os.path.isfile(p):
            return p
    except Exception:
        pass
    return sys.executable


def find_astrond():
    candidates = [
        os.path.join(PROJECT_ROOT, 'astron', 'win32', 'astrond.exe'),
        os.path.join(PROJECT_ROOT, 'astron', 'astrond.exe'),
        os.path.join(PROJECT_ROOT, 'astron', 'bin', 'astrond.exe'),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


def is_port_open(host, port, timeout_s=0.4):
    try:
        with socket.create_connection((host, port), timeout=timeout_s):
            return True
    except OSError:
        return False


def _now_str():
    return datetime.now().strftime('%H:%M:%S')


# --------------------------------------------------------------------------- #
# Server manager
# --------------------------------------------------------------------------- #

class ServerManager:
    """Starts / stops the local Astron + UberDOG + AI stack."""

    def __init__(self):
        self._procs = []

    def _spawn(self, args, cwd, tag):
        flags = 0
        if os.name == 'nt':
            flags = subprocess.CREATE_NO_WINDOW
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'
        env.pop('PYTHONPATH', None)
        env.pop('TTBTN_EXTRA_PRC', None)
        # Log to a file instead of a pipe so the child never blocks on a full
        # stdout pipe and survives if this process exits.
        os.makedirs(RUNTIME_LOGS, exist_ok=True)
        out_path = os.path.join(RUNTIME_LOGS, '%s_%s.log' % (tag, datetime.now().strftime('%H%M%S')))
        out = open(out_path, 'w', encoding='utf-8', errors='replace')
        proc = subprocess.Popen(
            list(args),
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=out,
            stderr=subprocess.STDOUT,
            env=env,
            creationflags=flags,
        )
        self._procs.append(proc)
        self._out_paths = getattr(self, '_out_paths', [])
        self._out_paths.append(out_path)
        self._out_files = getattr(self, '_out_files', [])
        self._out_files.append(out)
        return proc

    def are_up(self):
        return is_port_open(MD_HOST, MD_PORT) and is_port_open(MD_HOST, CA_PORT)

    def start(self, timeout_s=60, force_python=False):
        """Ensure MD + client agent are reachable; spawn stack if needed.

        With force_python=True, UberDOG/AI are (re)spawned when the MD was not
        already up, so a stale client-agent listener left over from a previous
        crashed session cannot cause a login hang. If a complete working stack
        is already up (e.g. the user's own), it is left alone.
        """
        md_up = is_port_open(MD_HOST, MD_PORT, timeout_s=0.3)
        ca_up = is_port_open(MD_HOST, CA_PORT, timeout_s=0.3)
        if md_up and ca_up and not force_python:
            return {'started': False, 'note': 'servers already up'}

        astrond = find_astrond()
        if not astrond:
            return {'started': False, 'error': 'astrond.exe not found under astron/'}
        pp = ppython_path()

        started = []
        started_md = False
        if not md_up:
            self._spawn([astrond, '--loglevel', 'info', '../config/astrond.yml'],
                        cwd=os.path.join(PROJECT_ROOT, 'astron', 'win32'), tag='astron')
            started.append('astron')
            started_md = True
            deadline = time.time() + timeout_s
            while time.time() < deadline and not is_port_open(MD_HOST, MD_PORT):
                time.sleep(0.3)
            if not is_port_open(MD_HOST, MD_PORT):
                return {'started': True, 'error': 'Astron MessageDirector never opened'}

        # Spawn UD/AI when the client agent is missing, or (force_python) when
        # the MessageDirector was down - in that case a stale CA listener cannot
        # be trusted. Never duplicate against a healthy external stack.
        if not is_port_open(MD_HOST, CA_PORT, timeout_s=0.3) or (force_python and started_md):
            self._spawn([
                pp, '-u', '-m', 'toontown.uberdog.UDStart',
                '--base-channel', '1000000', '--max-channels', '999999',
                '--stateserver', STATESERVER,
                '--messagedirector-ip', '%s:%s' % (MD_HOST, MD_PORT),
                '--eventlogger-ip', EVENTLOGGER_IP,
            ], cwd=PROJECT_ROOT, tag='uberdog')
            self._spawn([
                pp, '-u', '-m', 'toontown.ai.AIStart',
                '--base-channel', '401000000', '--max-channels', '999999',
                '--stateserver', STATESERVER,
                '--messagedirector-ip', '%s:%s' % (MD_HOST, MD_PORT),
                '--eventlogger-ip', EVENTLOGGER_IP,
                '--district-name', 'Toon Valley',
            ], cwd=PROJECT_ROOT, tag='ai')
            started += ['uberdog', 'ai']
            deadline = time.time() + timeout_s
            while time.time() < deadline and not is_port_open(MD_HOST, CA_PORT):
                time.sleep(0.3)

        # Freshly-booted UberDOG/AI need to finish loading the YAML DB and
        # registering before a client can log in. Instead of a fixed sleep, wait
        # for their own 'ready' markers in the runtime logs (deterministic).
        if 'uberdog' in started or 'ai' in started:
            self._wait_ready_markers(timeout_s=timeout_s)

        return {'started': bool(started), 'components': started,
                'mdUp': is_port_open(MD_HOST, MD_PORT),
                'caUp': is_port_open(MD_HOST, CA_PORT)}

    def _wait_ready_markers(self, timeout_s=60):
        """Wait until UberDOG and AI announce readiness in their runtime logs."""
        markers = [('uberdog', 'UberDOG server is ready.'),
                   ('ai', 'ToontownAIRepository: Done.')]
        log_paths = getattr(self, '_out_paths', [])
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            found = {}
            for tag, marker in markers:
                for p in reversed(log_paths):
                    base = os.path.basename(p)
                    if not base.startswith(tag + '_'):
                        continue
                    try:
                        with open(p, 'r', encoding='utf-8', errors='replace') as f:
                            content = f.read()
                    except Exception:
                        content = ''
                    if marker in content:
                        found[tag] = True
                        break
            if len(found) == len(markers):
                return
            time.sleep(0.5)

    def stop(self):
        killed = []
        for proc in reversed(list(self._procs)):
            try:
                if proc.poll() is None:
                    proc.terminate()
                    killed.append(proc.pid)
            except Exception:
                pass
        time.sleep(0.8)
        for proc in list(self._procs):
            try:
                if proc.poll() is None:
                    proc.kill()
            except Exception:
                pass
        self._procs = []
        # Close the stdout log file handles we own.
        for f in list(getattr(self, '_out_files', [])):
            try:
                f.close()
            except Exception:
                pass
        self._out_files = []
        return {'terminated': killed, 'logPaths': getattr(self, '_out_paths', [])}

    def restart(self, timeout_s=90):
        """Stop whatever we spawned and start a fresh stack."""
        self.stop()
        time.sleep(1.0)
        return self.start(timeout_s=timeout_s, force_python=True)


# --------------------------------------------------------------------------- #
# Client launcher
# --------------------------------------------------------------------------- #

class ClientLauncher:
    """Launches / stops the game client process."""

    def __init__(self, bridge_port=DEFAULT_BRIDGE_PORT, bridge_token=DEFAULT_BRIDGE_TOKEN):
        self.bridge_port = bridge_port
        self.bridge_token = bridge_token
        self.proc = None
        self._lock = threading.Lock()

    def is_running(self):
        with self._lock:
            return self.proc is not None and self.proc.poll() is None

    def launch(self, extra_prc=None, login_token='dev', avatar_choice=0, window_title='TTBTN MCP'):
        """Launch the client. `extra_prc` is a path to a generated PRC file.

        The client's stdout/stderr go to a file (never a pipe) so the game can
        never block on a full pipe buffer, and so logs survive process exits.
        """
        if self.is_running():
            return {'launched': False, 'error': 'client already running'}
        pp = ppython_path()
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'
        env['LOGIN_TOKEN'] = login_token
        env.pop('PYTHONPATH', None)
        if extra_prc:
            env['TTBTN_EXTRA_PRC'] = os.path.abspath(extra_prc)
        flags = 0
        if os.name == 'nt':
            flags = subprocess.CREATE_NO_WINDOW
        os.makedirs(RUNTIME_LOGS, exist_ok=True)
        self._stdout_path = os.path.join(RUNTIME_LOGS, 'client_%s.log' % datetime.now().strftime('%H%M%S'))
        out = open(self._stdout_path, 'w', encoding='utf-8', errors='replace')
        proc = subprocess.Popen(
            [pp, '-u', '-m', 'toontown.launcher.QuickStartLauncher'],
            cwd=PROJECT_ROOT,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=out,
            stderr=subprocess.STDOUT,
            creationflags=flags,
        )
        with self._lock:
            self.proc = proc
        return {'launched': True, 'pid': proc.pid, 'stdoutLog': self._stdout_path}

    def exit_code(self):
        with self._lock:
            if self.proc is None:
                return None
            return self.proc.poll()

    def stop(self):
        """Ask the bridge to quit cleanly; kill the process if that fails."""
        try:
            self.bridge_request('quit', {'code': 0})
        except Exception:
            pass
        with self._lock:
            proc = self.proc
        if proc is None:
            return {'stopped': False, 'note': 'no client process'}
        deadline = time.time() + 8
        while time.time() < deadline and proc.poll() is None:
            time.sleep(0.2)
        if proc.poll() is None:
            try:
                proc.terminate()
            except Exception:
                pass
            try:
                proc.kill()
            except Exception:
                pass
        code = proc.poll()
        self.proc = None
        return {'stopped': True, 'exitCode': code}

    # Bridge ---------------------------------------------------------------- #
    def bridge_available(self, timeout_s=2.0):
        try:
            self.bridge_request('ping', {}, timeout_s=timeout_s)
            return True
        except Exception:
            return False

    def bridge_request(self, cmd, args=None, timeout_s=5.0):
        payload = json.dumps({'token': self.bridge_token, 'cmd': cmd, 'args': args or {}})
        with socket.create_connection(('127.0.0.1', self.bridge_port), timeout=timeout_s) as s:
            s.settimeout(timeout_s)
            s.sendall((payload + '\n').encode('utf-8'))
            raw = s.makefile('r', encoding='utf-8', errors='replace').readline()
        resp = json.loads(raw)
        if not resp.get('ok'):
            raise RuntimeError(resp.get('error', 'bridge error'))
        return resp.get('data')

    def poll_state(self):
        try:
            return self.bridge_request('state', {}, timeout_s=3.0)
        except Exception:
            return None


# --------------------------------------------------------------------------- #
# Logs & crash scanning
# --------------------------------------------------------------------------- #

def log_dir():
    return os.path.join(PROJECT_ROOT, 'logs')


def latest_log_paths(n=5, prefix='toontown'):
    d = log_dir()
    if not os.path.isdir(d):
        return []
    files = [os.path.join(d, f) for f in os.listdir(d) if f.startswith(prefix) and f.endswith('.log')]
    files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return files[:n]


def tail_lines(path, n_lines=40):
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        return ''.join(lines[-n_lines:])
    except Exception as e:
        return '<!-- could not read %s: %s -->' % (path, e)


def scan_crash_logs(max_results=25, since_hours=None, prefix='toontown'):
    """Find crash tracebacks in the newest log files.

    Returns a list of dicts: {path, at, error, trace: [{file, line, func}]}.
    """
    d = log_dir()
    if not os.path.isdir(d):
        return []
    files = [os.path.join(d, f) for f in os.listdir(d)
             if f.startswith(prefix) and f.endswith('.log')]
    files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    if since_hours is not None:
        cutoff = time.time() - since_hours * 3600
        files = [p for p in files if os.path.getmtime(p) >= cutoff]

    results = []
    file_re = re.compile(r'File "(.+)", line (\d+), in (.+)')
    for path in files:
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
        except Exception:
            continue
        i = 0
        while i < len(lines) and len(results) < max_results:
            line = lines[i].strip()
            if 'Traceback (most recent call last):' in line:
                trace = []
                j = i + 1
                error = None
                while j < len(lines):
                    raw = lines[j].rstrip('\r\n')
                    stripped = raw.strip()
                    if not stripped:
                        j += 1
                        continue
                    m = file_re.match(stripped)
                    if m:
                        trace.append({'file': m.group(1), 'line': int(m.group(2)), 'func': m.group(3)})
                    elif raw[:1].isspace():
                        # Indented line = source line echoed in the traceback; skip.
                        pass
                    else:
                        # Unindented line right after the frames is the exception.
                        error = stripped[:400]
                        break
                    j += 1
                results.append({
                    'path': os.path.basename(path),
                    'at': datetime.fromtimestamp(os.path.getmtime(path)).strftime('%m-%d %H:%M:%S'),
                    'error': error or 'traceback',
                    'trace': trace[-8:],
                })
                i = j
            else:
                i += 1
    # Dedupe the (path, error) pairs (the same crash is often logged twice:
    # once by the task manager and once by the launcher main loop).
    seen = set()
    unique = []
    for r in results:
        key = (r['path'], r['error'])
        if key in seen:
            continue
        seen.add(key)
        unique.append(r)
    return unique[:max_results]


def grep_logs(pattern, max_results=30, since_hours=None, prefix='toontown'):
    import fnmatch as _fn
    d = log_dir()
    if not os.path.isdir(d):
        return []
    files = [os.path.join(d, f) for f in os.listdir(d)
             if f.startswith(prefix) and f.endswith('.log')]
    files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    if since_hours is not None:
        cutoff = time.time() - since_hours * 3600
        files = [p for p in files if os.path.getmtime(p) >= cutoff]
    out = []
    try:
        rx = re.compile(pattern, re.IGNORECASE)
    except re.error:
        return [{'error': 'invalid regex'}]
    for path in files[:6]:
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                for ln in f:
                    if rx.search(ln):
                        out.append({'file': os.path.basename(path), 'line': ln.rstrip()[:500]})
                        if len(out) >= max_results:
                            return out
        except Exception:
            continue
    return out
