from panda3d.core import *
from panda3d.toontown import *
from direct.directnotify.DirectNotifyGlobal import *
from direct.showbase import Loader
from toontown.toontowngui import ToontownLoadingScreen
import time

class ToontownLoader(Loader.Loader):
    TickPeriod = 0.01

    def __init__(self, base):
        Loader.Loader.__init__(self, base)
        self.inBulkBlock = None
        self.blockName = None
        self.loadingScreen = ToontownLoadingScreen.ToontownLoadingScreen()
        self._tickCounter = 0
        self._tickSkip = 10
        self._prefetch_handles = []
        return

    def cancelPrefetchRequests(self):
        for h in list(self._prefetch_handles):
            try:
                if hasattr(h, 'cancel') and not h.cancelled() and not h.done():
                    h.cancel()
            except Exception:
                pass
        self._prefetch_handles = []

    def schedulePrefetchForQuietZone(self, request_status):
        if not ConfigVariableBool('want-async-zone-prefetch', True).value:
            return
        self.cancelPrefetchRequests()
        try:
            from toontown.toonbase import ZonePrefetchCatalog

            paths = ZonePrefetchCatalog.paths_for_quiet_zone(request_status)
        except Exception:
            paths = []
        for i, path in enumerate(paths):
            self._startPrefetchModel(path, priority=max(1, 80 - i))

    def _startPrefetchModel(self, path, priority=10):
        holder = {'cb': None}

        def _done(model):
            cb = holder['cb']
            try:
                if cb is not None and cb in self._prefetch_handles:
                    self._prefetch_handles.remove(cb)
            except Exception:
                pass
            try:
                if model is not None and not model.isEmpty():
                    ModelPool.addModel(path, model.node())
            except Exception:
                pass

        try:
            cb = Loader.Loader.loadModel(
                self,
                path,
                callback=_done,
                blocking=False,
                okMissing=True,
                priority=priority,
            )
            holder['cb'] = cb
            if cb is not None and hasattr(cb, 'requests'):
                self._prefetch_handles.append(cb)
        except Exception:
            pass


    def _notifyModernAsset(self, path, node=None, texture=None, kind='model'):
        try:
            ml = getattr(self.base, 'modernLoading', None)
            if ml is None or not ml.enabled():
                return
            ml.on_asset_loaded(path=path, model=node, texture=texture, kind=kind)
        except Exception:
            pass

    def destroy(self):
        self.cancelPrefetchRequests()
        self.loadingScreen.destroy()
        del self.loadingScreen
        Loader.Loader.destroy(self)

    def beginBulkLoad(self, name, label, range, gui, tipCategory):
        self._loadStartT = globalClock.getRealTime()
        Loader.Loader.notify.info("starting bulk load of block '%s'" % name)
        if self.inBulkBlock:
            Loader.Loader.notify.warning("Tried to start a block ('%s'), but am already in a block ('%s')" % (name, self.blockName))
            return None
        self.inBulkBlock = 1
        self._bulkPrevTickSkip = self._tickSkip
        self._tickSkip = 1
        self._lastTickT = globalClock.getRealTime()
        self.blockName = name
        try:
            ml = getattr(self.base, 'modernLoading', None)
            if ml and ml.enabled():
                ml.enter_bulk_load(name, label, range)
                if ConfigVariableBool('minimal-legacy-loading-with-modern', True).value:
                    gui = 0
        except Exception:
            pass
        minimal = False
        try:
            ml = getattr(self.base, 'modernLoading', None)
            if ml and ml.enabled() and ConfigVariableBool('minimal-legacy-loading-with-modern', True).value:
                minimal = True
        except Exception:
            pass
        self.loadingScreen.begin(range, label, gui, tipCategory, minimal=minimal)
        return None

    def endBulkLoad(self, name):
        if not self.inBulkBlock:
            Loader.Loader.notify.warning("Tried to end a block ('%s'), but not in one" % name)
            return None
        if name != self.blockName:
            Loader.Loader.notify.warning("Tried to end a block ('%s'), other then the current one ('%s')" % (name, self.blockName))
            return None
        self.inBulkBlock = None
        self._tickSkip = self._bulkPrevTickSkip
        expectedCount, loadedCount = self.loadingScreen.end()
        now = globalClock.getRealTime()
        Loader.Loader.notify.info("At end of block '%s', expected %s, loaded %s, duration=%s" % (self.blockName,
         expectedCount,
         loadedCount,
         now - self._loadStartT))
        try:
            ml = getattr(self.base, 'modernLoading', None)
            if ml and ml.enabled():
                ml.leave_bulk_load()
        except Exception:
            pass
        return

    def abortBulkLoad(self):
        if self.inBulkBlock:
            Loader.Loader.notify.info("Aborting block ('%s')" % self.blockName)
            self.inBulkBlock = None
            self._tickSkip = self._bulkPrevTickSkip
            self.loadingScreen.abort()
            try:
                ml = getattr(self.base, 'modernLoading', None)
                if ml and ml.enabled():
                    ml.leave_bulk_load()
            except Exception:
                pass
        return

    def tick(self):
        if self.inBulkBlock:
            self._tickCounter += 1
            if self._tickCounter >= self._tickSkip:
                self._tickCounter = 0
                now = globalClock.getRealTime()
                if now - self._lastTickT > self.TickPeriod:
                    self._lastTickT += self.TickPeriod
                    self.loadingScreen.tick()
                    try:
                        ml = getattr(self.base, 'modernLoading', None)
                        if ml and ml.enabled():
                            if not ConfigVariableBool('want-zero-load-ui', False).value:
                                ml.set_progress(self.loadingScreen.get_progress_fraction() * 100.0)
                    except Exception:
                        pass
                    try:
                        if getattr(self.base, 'cr', None):
                            self.base.cr.considerHeartbeat()
                    except:
                        pass
                    # Critical: bulk loads can otherwise run as one giant "frame"
                    # (unplayable hitch). Yield so the OS and render thread can
                    # breathe, spreading the work across multiple frames.
                    try:
                        time.sleep(0)
                    except Exception:
                        pass

    def loadModel(self, *args, **kw):
        ret = Loader.Loader.loadModel(self, *args, **kw)
        if kw.get('callback') is not None:
            return ret
        self.tick()
        path = str(args[0]) if args else None
        if ret is not None and not ret.isEmpty():
            self._notifyModernAsset(path, node=ret)
        else:
            self._notifyModernAsset(path, node=None)
        return ret

    def loadFont(self, *args, **kw):
        ret = Loader.Loader.loadFont(self, *args, **kw)
        self.tick()
        path = str(args[0]) if args else None
        self._notifyModernAsset(path, node=None, kind='font')
        return ret

    def loadTexture(self, texturePath, alphaPath = None, okMissing = False):
        ret = Loader.Loader.loadTexture(self, texturePath, alphaPath, okMissing=okMissing)
        self.tick()
        if alphaPath:
            self.tick()
        self._notifyModernAsset(str(texturePath), texture=ret)
        return ret

    def loadSfx(self, soundPath):
        ret = Loader.Loader.loadSfx(self, soundPath)
        self.tick()
        self._notifyModernAsset(str(soundPath), kind='audio')
        return ret

    def loadMusic(self, soundPath):
        ret = Loader.Loader.loadMusic(self, soundPath)
        self.tick()
        self._notifyModernAsset(str(soundPath), kind='audio')
        return ret

    def loadDNAFileAI(self, dnaStore, dnaFile):
        ret = loadDNAFileAI(dnaStore, dnaFile, CSDefault)
        self.tick()
        return ret

    def loadDNAFile(self, dnaStore, dnaFile):
        ret = loadDNAFile(dnaStore, dnaFile, CSDefault, 0)
        self.tick()
        return ret
