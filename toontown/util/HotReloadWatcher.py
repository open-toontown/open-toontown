import importlib
import os
import sys
import time

from direct.showbase.MessengerGlobal import messenger


class HotReloadWatcher:
    def __init__(self, roots, interval=0.5):
        self.roots = [os.path.normpath(r) for r in roots]
        self.interval = float(interval)
        self._mtimes = {}
        self._nextCheck = 0.0

    def _scan(self):
        changed = []
        for root in self.roots:
            if not os.path.isdir(root):
                continue
            for dirpath, _, filenames in os.walk(root):
                for fn in filenames:
                    if not fn.endswith('.py'):
                        continue
                    path = os.path.join(dirpath, fn)
                    try:
                        mtime = os.path.getmtime(path)
                    except OSError:
                        continue
                    old = self._mtimes.get(path)
                    if old is None:
                        self._mtimes[path] = mtime
                        continue
                    if mtime != old:
                        self._mtimes[path] = mtime
                        changed.append(path)
        return changed

    def _pathToModule(self, path):
        path = os.path.normpath(path)
        for prefix in self.roots:
            prefix = os.path.normpath(prefix)
            if not path.startswith(prefix + os.sep):
                continue
            rel = path[len(prefix) + 1:]
            if rel.endswith('.py'):
                rel = rel[:-3]
            rel = rel.replace(os.sep, '.')
            if prefix.endswith('toontown'):
                return f"toontown.{rel}"
            if prefix.endswith('otp'):
                return f"otp.{rel}"
        return None

    def reloadChanged(self):
        changedPaths = self._scan()
        if not changedPaths:
            return
        modules = []
        for p in changedPaths:
            mod = self._pathToModule(p)
            if mod and mod in sys.modules:
                modules.append(mod)
        # Reload deepest modules first.
        modules = sorted(set(modules), key=lambda m: (-m.count('.'), m))
        reloaded = []
        for mod in modules:
            try:
                importlib.reload(sys.modules[mod])
                reloaded.append(mod)
            except Exception:
                # If reload fails, let caller decide next action.
                messenger.send('hot-reload-failed', [mod])
                return
        if reloaded:
            messenger.send('hot-reload-applied', [reloaded])

