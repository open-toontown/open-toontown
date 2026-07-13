import os
import socket
import subprocess
import sys
import threading
import time

from panda3d.core import ConfigVariableBool, ConfigVariableDouble, ConfigVariableString


def _is_tcp_open(host: str, port: int, timeout_s: float) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout_s):
            return True
    except OSError:
        return False


class LocalServerManager:
    """
    Best-effort helper for local development:
    - Starts Astron (astrond), UberDOG, and AI using the existing win32 batch scripts.
    - Waits for the MessageDirector port to accept connections before returning.

    This is intentionally conservative: if ports are already open, it does nothing.
    """

    def __init__(self):
        self._procs = []
        self._streams = []

        self._enabled = ConfigVariableBool('auto-start-local-servers', False).value
        self._show_consoles = ConfigVariableBool('local-servers-show-consoles', False).value
        self._forward_logs = ConfigVariableBool('local-servers-forward-logs', True).value
        # If True, always spawn UberDOG/AI even when MD is already up.
        # This helps ensure logs can be forwarded (only possible for processes we spawn).
        self._always_spawn_python = ConfigVariableBool('local-servers-always-spawn-python', True).value
        self._host = ConfigVariableString('local-servers-host', '127.0.0.1').value
        self._md_port = int(ConfigVariableString('local-servers-md-port', '7199').value)
        # Client agent / gameserver port (HTTP interface). If open with MD, stack is already serving.
        self._ca_port = int(ConfigVariableString('local-servers-ca-port', '7198').value)
        # When MD is up and CA port is open, skip spawning UberDOG/AI unless force flag is set (avoids duplicate sessions).
        self._skip_python_if_ca_open = ConfigVariableBool('local-servers-skip-python-if-ca-open', True).value
        # After killing orphaned UD/AI, set this #t so the launcher spawns fresh Python servers even if CA still listens.
        self._force_python_spawn = ConfigVariableBool('local-servers-force-python-spawn', False).value
        self._poll_timeout_s = float(ConfigVariableDouble('local-servers-start-timeout', 25.0).value)
        self._poll_interval_s = float(ConfigVariableDouble('local-servers-poll-interval', 0.15).value)

    def enabled(self) -> bool:
        return bool(self._enabled)

    def _workspace_root(self) -> str:
        # Current working directory is typically the repo root already,
        # but be robust when launched from deeper paths.
        cwd = os.getcwd()
        # Heuristic: project has these top-level directories in this repo.
        for _ in range(6):
            if os.path.isdir(os.path.join(cwd, 'toontown')) and os.path.isdir(os.path.join(cwd, 'win32')):
                return cwd
            parent = os.path.dirname(cwd)
            if parent == cwd:
                break
            cwd = parent
        return os.getcwd()

    def _bat(self, rel_path: str) -> str:
        root = self._workspace_root()
        return os.path.join(root, rel_path)

    def _creationflags(self) -> int:
        if os.name != 'nt':
            return 0
        if self._show_consoles:
            return subprocess.CREATE_NEW_CONSOLE
        return subprocess.CREATE_NO_WINDOW

    def _spawn(self, args, cwd=None) -> None:
        stdout = subprocess.DEVNULL
        stderr = subprocess.DEVNULL
        if self._forward_logs:
            stdout = subprocess.PIPE
            stderr = subprocess.PIPE

        env = None
        if self._forward_logs:
            # Ensure Python children flush immediately when piped.
            try:
                env = os.environ.copy()
                env['PYTHONUNBUFFERED'] = '1'
            except Exception:
                env = None

        proc = subprocess.Popen(
            list(args),
            cwd=cwd or self._workspace_root(),
            stdin=subprocess.DEVNULL,
            stdout=stdout,
            stderr=stderr,
            bufsize=1,
            text=True,
            encoding='utf-8',
            errors='replace',
            env=env,
            creationflags=self._creationflags(),
        )
        self._procs.append(proc)
        try:
            sys.stdout.write('[LocalServers] spawned: %s\n' % (' '.join(map(str, args)),))
            sys.stdout.flush()
        except Exception:
            pass

    def _start_log_forwarding(self, proc, tag: str):
        if not self._forward_logs:
            return
        if not proc:
            return

        def pump(stream, is_err: bool):
            if not stream:
                return
            try:
                for line in iter(stream.readline, ''):
                    if not line:
                        break
                    try:
                        prefix = f'[{tag}] '
                        out = sys.stderr if is_err else sys.stdout
                        out.write(prefix + line)
                        out.flush()
                    except Exception:
                        pass
            except Exception:
                pass
            finally:
                try:
                    stream.close()
                except Exception:
                    pass

        try:
            if proc.stdout:
                t = threading.Thread(target=pump, args=(proc.stdout, False), daemon=True)
                t.start()
                self._streams.append(t)
        except Exception:
            pass
        try:
            if proc.stderr:
                t = threading.Thread(target=pump, args=(proc.stderr, True), daemon=True)
                t.start()
                self._streams.append(t)
        except Exception:
            pass
        try:
            sys.stdout.write('[LocalServers] forwarding enabled for %s\n' % tag)
            sys.stdout.flush()
        except Exception:
            pass

        # Also report if the process exits early (helps diagnose "no logs").
        def watch_exit():
            try:
                code = proc.wait()
                try:
                    sys.stdout.write(f'[{tag}] <process exited code={code}>\n')
                    sys.stdout.flush()
                except Exception:
                    pass
            except Exception:
                pass

        try:
            t = threading.Thread(target=watch_exit, daemon=True)
            t.start()
            self._streams.append(t)
        except Exception:
            pass

    def _read_ppython_path(self):
        try:
            path = os.path.join(self._workspace_root(), 'PPYTHON_PATH')
            with open(path, 'r', encoding='utf-8') as f:
                pp = f.read().strip()
            return pp or None
        except Exception:
            return None

    def _find_astrond(self):
        root = self._workspace_root()
        candidates = [
            os.path.join(root, 'astron', 'win32', 'astrond.exe'),
            os.path.join(root, 'astron', 'bin', 'astrond.exe'),
            os.path.join(root, 'bin', 'astrond.exe'),
        ]
        for c in candidates:
            if os.path.isfile(c):
                return c
        return 'astrond'

    def _start_astron(self) -> None:
        astrond = self._find_astrond()
        cfg = os.path.join(self._workspace_root(), 'astron', 'config', 'astrond.yml')
        self._spawn([astrond, '--loglevel', 'info', cfg], cwd=self._workspace_root())
        try:
            self._start_log_forwarding(self._procs[-1], 'Astron')
        except Exception:
            pass

    def _start_uberdog(self) -> None:
        pp = self._read_ppython_path()
        if not pp:
            try:
                sys.stdout.write('[LocalServers] UberDOG not started: PPYTHON_PATH missing\n')
                sys.stdout.flush()
            except Exception:
                pass
            return
        self._spawn(
            [
                pp,
                '-u',
                '-m',
                'toontown.uberdog.UDStart',
                '--base-channel',
                '1000000',
                '--max-channels',
                '999999',
                '--stateserver',
                '4002',
                '--messagedirector-ip',
                '127.0.0.1:7199',
                '--eventlogger-ip',
                '127.0.0.1:7197',
            ],
            cwd=self._workspace_root(),
        )
        try:
            self._start_log_forwarding(self._procs[-1], 'UberDOG')
        except Exception:
            pass

    def _start_ai(self) -> None:
        pp = self._read_ppython_path()
        if not pp:
            try:
                sys.stdout.write('[LocalServers] AI not started: PPYTHON_PATH missing\n')
                sys.stdout.flush()
            except Exception:
                pass
            return
        self._spawn(
            [
                pp,
                '-u',
                '-m',
                'toontown.ai.AIStart',
                '--base-channel',
                '401000000',
                '--max-channels',
                '999999',
                '--stateserver',
                '4002',
                '--messagedirector-ip',
                '127.0.0.1:7199',
                '--eventlogger-ip',
                '127.0.0.1:7197',
                '--district-name',
                'Toon Valley',
            ],
            cwd=self._workspace_root(),
        )
        try:
            self._start_log_forwarding(self._procs[-1], 'AI')
        except Exception:
            pass

    def is_message_director_up(self) -> bool:
        return _is_tcp_open(self._host, self._md_port, timeout_s=0.2)

    def start_if_needed(self, status_cb=None) -> bool:
        """
        Returns True if the MessageDirector is reachable by the end, else False.
        """
        if not self.enabled():
            return self.is_message_director_up()

        def status(msg: str):
            if callable(status_cb):
                try:
                    status_cb(msg)
                except Exception:
                    pass

        try:
            sys.stdout.write('[LocalServers] root=%s\n' % self._workspace_root())
            sys.stdout.write('[LocalServers] md=%s:%s\n' % (self._host, self._md_port))
            sys.stdout.flush()
        except Exception:
            pass

        md_up_initially = self.is_message_director_up()
        if md_up_initially:
            ca_up = _is_tcp_open(self._host, self._ca_port, timeout_s=0.25)
            skip_python = (
                ca_up
                and self._skip_python_if_ca_open
                and not self._force_python_spawn
            )
            if skip_python:
                try:
                    sys.stdout.write(
                        '[LocalServers] MD and client agent (%s:%s) already up; skipping UberDOG/AI spawn '
                        '(local-servers-skip-python-if-ca-open). If login drops with 10053 or error 100, '
                        'stop orphaned UberDOG/AI (or restart Astron), or set local-servers-force-python-spawn #t '
                        'after closing duplicate clients.\n'
                        % (self._host, self._ca_port)
                    )
                    sys.stdout.flush()
                except Exception:
                    pass
                return True
            if self._always_spawn_python:
                if ca_up and self._force_python_spawn:
                    status('MessageDirector up: forcing UberDOG/AI spawn (local-servers-force-python-spawn)…')
                else:
                    status('MessageDirector already running; starting UberDOG/AI…')
                try:
                    pp = self._read_ppython_path()
                    sys.stdout.write('[LocalServers] PPYTHON_PATH=%s\n' % (pp or '<missing>',))
                    sys.stdout.flush()
                except Exception:
                    pass
                self._start_uberdog()
                time.sleep(0.15)
                self._start_ai()
                time.sleep(0.15)
            return True

        status('Starting local Astron cluster…')
        self._start_astron()

        status('Waiting for MessageDirector…')
        deadline = time.time() + self._poll_timeout_s
        while time.time() < deadline:
            if self.is_message_director_up():
                break
            time.sleep(self._poll_interval_s)

        if not self.is_message_director_up():
            status('Local server startup timed out (will still try to connect).')
            return False

        status('Starting UberDOG…')
        try:
            pp = self._read_ppython_path()
            sys.stdout.write('[LocalServers] PPYTHON_PATH=%s\n' % (pp or '<missing>',))
            sys.stdout.flush()
        except Exception:
            pass
        self._start_uberdog()
        time.sleep(0.15)

        status('Starting AI (district)…')
        self._start_ai()
        time.sleep(0.15)

        status('Local servers are up.')
        return True

    def shutdown(self, status_cb=None):
        """
        Stop any server processes we started.
        This intentionally only kills processes spawned by this manager.
        """
        def status(msg: str):
            if callable(status_cb):
                try:
                    status_cb(msg)
                except Exception:
                    pass

        if not self._procs:
            return

        status('Stopping local servers…')

        # Terminate in reverse startup order (AI, UberDOG, Astron).
        for proc in reversed(list(self._procs)):
            try:
                if proc.poll() is None:
                    proc.terminate()
            except Exception:
                pass

        # Give them a moment to exit cleanly.
        deadline = time.time() + 2.0
        while time.time() < deadline:
            alive = False
            for proc in self._procs:
                try:
                    if proc.poll() is None:
                        alive = True
                        break
                except Exception:
                    pass
            if not alive:
                break
            time.sleep(0.05)

        # Force kill any stragglers.
        for proc in self._procs:
            try:
                if proc.poll() is None:
                    proc.kill()
            except Exception:
                pass

        self._procs = []
        self._streams = []
        status('Local servers stopped.')

