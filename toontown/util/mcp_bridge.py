##################################################
# MCP Test Bridge (opt-in)
##################################################
# A small localhost TCP/JSON command server that runs inside the game client so
# an external MCP server (AI assistant) can drive and inspect a running game.
#
# OFF BY DEFAULT. Enable with PRC overrides (usually injected by the MCP server
# through a generated .prc file, see mcp/README.md):
#
#     want-mcp-bridge 1
#     mcp-bridge-port 29100
#     mcp-bridge-token dev
#
# Security: binds to 127.0.0.1 only and requires the token on every request.
# Commands that touch Panda state are dispatched onto the main thread via the
# task manager (never run from the listener thread).
#
# Wire format: one JSON object per line, both directions.
#   request:  {"token": "...", "cmd": "state", "args": {...}}
#   response: {"ok": true, "data": {...}} | {"ok": false, "error": "..."}
##################################################

import json
import os
import socket
import threading
from collections import deque

from panda3d.core import ConfigVariableString, Filename
from direct.task.TaskManagerGlobal import taskMgr
from direct.showbase.MessengerGlobal import messenger


class MCPBridge:
    """Localhost JSON command bridge for the Toontown game client."""

    def __init__(self):
        self.host = '127.0.0.1'
        self.port = int(ConfigVariableString('mcp-bridge-port', '29100').value)
        self.token = ConfigVariableString('mcp-bridge-token', '').value
        if not self.token:
            self.token = os.environ.get('TTBTN_MCP_TOKEN', '')
        # Fail closed: never expose a tokenless listener on localhost.
        if not self.token:
            print('MCPBridge: refusing to start - set mcp-bridge-token (or TTBTN_MCP_TOKEN)')
            self._listener = None
            return
        self._queue = deque()
        self._lock = threading.Lock()
        self._stop = threading.Event()

        self._listener = threading.Thread(target=self._listen, name='mcp-bridge-listener', daemon=True)
        self._listener.start()
        try:
            taskMgr.add(self._drainTask, 'mcpBridge-drain')
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    # Socket plumbing
    # ------------------------------------------------------------------ #
    def _listen(self):
        try:
            srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind((self.host, self.port))
            srv.listen(4)
            srv.settimeout(0.5)
        except OSError as e:
            print('MCPBridge: failed to bind %s:%s: %s' % (self.host, self.port, e))
            return
        while not self._stop.is_set():
            try:
                conn, _ = srv.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            try:
                self._handle_conn(conn)
            except Exception:
                try:
                    conn.close()
                except Exception:
                    pass
        try:
            srv.close()
        except Exception:
            pass

    def _handle_conn(self, conn):
        conn.settimeout(5.0)
        try:
            raw = conn.makefile('r', encoding='utf-8', errors='replace').readline()
        except Exception:
            raw = None
        if not raw:
            try:
                conn.close()
            except Exception:
                pass
            return
        try:
            req = json.loads(raw)
        except (ValueError, TypeError):
            self._respond(conn, {'ok': False, 'error': 'invalid json'})
            return
        if req.get('token') != self.token:
            self._respond(conn, {'ok': False, 'error': 'bad token'})
            return
        cmd = str(req.get('cmd', ''))
        args = req.get('args') or {}
        # Fast, no-Panda commands can be answered from the listener thread.
        if cmd == 'ping':
            self._respond(conn, {'ok': True, 'data': {'pong': True}})
            return
        if cmd == 'bridge_info':
            self._respond(conn, {
                'ok': True,
                'data': {'host': self.host, 'port': self.port, 'token_required': bool(self.token)},
            })
            return
        # Everything else runs on the main thread via the drain task.
        with self._lock:
            self._queue.append((conn, cmd, args))

    @staticmethod
    def _respond(conn, payload):
        try:
            # Commands run on the main thread and may take longer than the
            # accept-timeout; never let a stale timeout kill the response write.
            conn.settimeout(None)
            conn.sendall((json.dumps(payload) + '\n').encode('utf-8'))
            conn.close()
        except Exception:
            try:
                conn.close()
            except Exception:
                pass

    # ------------------------------------------------------------------ #
    # Main-thread dispatch
    # ------------------------------------------------------------------ #
    def _drainTask(self, task):
        while True:
            with self._lock:
                if not self._queue:
                    break
                conn, cmd, args = self._queue.popleft()
            try:
                data = self._dispatch(cmd, args)
                self._respond(conn, {'ok': True, 'data': data})
            except Exception as e:
                self._respond(conn, {'ok': False, 'error': '%s: %s' % (type(e).__name__, e)})
        return task.cont

    def _dispatch(self, cmd, args):
        if cmd == 'state':
            return self._cmd_state()
        if cmd == 'chat':
            return self._cmd_chat(args)
        if cmd == 'teleport':
            return self._cmd_teleport(args)
        if cmd == 'exec':
            return self._cmd_exec(args)
        if cmd == 'screenshot':
            return self._cmd_screenshot(args)
        if cmd == 'quit':
            self._cmd_quit(args)
            return {'quitting': True}
        raise ValueError('unknown command: %s' % cmd)

    # ------------------------------------------------------------------ #
    # Commands
    # ------------------------------------------------------------------ #
    def _cmd_state(self):
        base = self._base()
        cr = getattr(base, 'cr', None)
        la = getattr(base, 'localAvatar', None)
        state = {
            'windowOpen': bool(getattr(base, 'win', None)),
            'connected': bool(cr and cr.isConnected()),
            'magicWordManager': bool(cr and getattr(cr, 'magicWordManager', None)),
            'wantMagicWords': bool(cr and getattr(cr, 'wantMagicWords', False)),
        }
        if la is not None:
            try:
                state['avatar'] = {
                    'name': la.getName(),
                    'doId': la.getDoId(),
                    'zoneId': la.getZoneId(),
                    'hp': la.getHp(),
                    'maxHp': la.getMaxHp(),
                    'money': la.getMoney(),
                    'accessLevel': la.getAccessLevel() if hasattr(la, 'getAccessLevel') else None,
                }
            except Exception as e:
                state['avatarError'] = str(e)
        if cr is not None and getattr(cr, 'playGame', None):
            try:
                state['place'] = cr.playGame.getPlace().fsm.getCurrentState().getName()
            except Exception:
                state['place'] = None
        return state

    def _cmd_chat(self, args):
        base = self._base()
        text = str(args.get('text', ''))
        ta = getattr(base, 'talkAssistant', None)
        if ta is None:
            raise RuntimeError('talkAssistant not initialized yet')
        ta.sendOpenTalk(text)
        return {'sent': text}

    def _cmd_teleport(self, args):
        base = self._base()
        cr = getattr(base, 'cr', None)
        zoneId = int(args.get('zoneId', 0))
        if zoneId <= 0:
            raise ValueError('zoneId must be > 0')
        # Direct zone request, mirroring the server-side teleportResponse().
        place = cr.playGame.getPlace()
        from toontown.hood import ZoneUtil
        place.fsm.forceTransition('teleportOut', [{
            'loader': ZoneUtil.getBranchLoaderName(zoneId),
            'where': ZoneUtil.getToonWhereName(zoneId),
            'how': 'teleportIn',
            'hoodId': ZoneUtil.getHoodId(zoneId),
            'zoneId': zoneId,
            'shardId': None,
            'avId': -1,
        }])
        return {'via': 'place', 'zoneId': zoneId}

    def _cmd_exec(self, args):
        base = self._base()
        code = str(args.get('code', ''))
        ns = {
            'base': base,
            'cr': getattr(base, 'cr', None),
            'localAvatar': getattr(base, 'localAvatar', None),
            'taskMgr': taskMgr,
            'messenger': messenger,
            'loader': getattr(base, 'loader', None),
            'render': getattr(base, 'render', None),
            'camera': getattr(base, 'camera', None),
            'hidden': getattr(base, 'hidden', None),
        }
        try:
            result = eval(code, {'__builtins__': {}}, ns)  # noqa: S307
            return {'result': str(result)}
        except SyntaxError:
            exec(compile(code, '<mcp-exec>', 'exec'), {'__builtins__': {}}, ns)  # noqa: S102
            return {'result': 'exec ok'}
        except Exception as e:
            return {'error': '%s: %s' % (type(e).__name__, e)}

    def _cmd_screenshot(self, args):
        base = self._base()
        win = getattr(base, 'win', None)
        if win is None:
            raise RuntimeError('no window')
        name = str(args.get('name') or 'mcp_shot')
        out_dir = ConfigVariableString('mcp-bridge-screenshot-dir', 'logs/mcp').value
        try:
            os.makedirs(out_dir, exist_ok=True)
        except Exception:
            pass
        path = os.path.join(out_dir, name + '.png')
        if not win.saveScreenshot(Filename.fromOsSpecific(path)):
            raise RuntimeError('screenshot failed')
        return {'path': os.path.abspath(path)}

    def _cmd_quit(self, args):
        base = self._base()
        code = int(args.get('code', 0))
        try:
            launcher.setPandaErrorCode(code)
        except Exception:
            pass
        exitFunc = getattr(base, 'exitFunc', None) or getattr(base, 'userExit', None)
        if callable(exitFunc):
            try:
                exitFunc()
                return
            except Exception:
                pass
        import sys
        sys.exit(code)

    def _base(self):
        import builtins
        b = getattr(builtins, 'base', None)
        if b is None:
            from direct.showbase import ShowBaseGlobal
            b = getattr(ShowBaseGlobal, 'base', None)
        if b is None:
            raise RuntimeError('game base not available yet')
        return b
