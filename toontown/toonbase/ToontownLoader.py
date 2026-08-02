from panda3d.core import *
from panda3d.toontown import *
from direct.directnotify.DirectNotifyGlobal import *
from direct.showbase import Loader
from toontown.toontowngui import ToontownLoadingScreen
from toontown.toontowngui.ZonePrefetchCatalog import zonePrefetchManager

class ToontownLoader(Loader.Loader):
    TickPeriod = 0.005

    def __init__(self, base):
        Loader.Loader.__init__(self, base)
        self.inBulkBlock = None
        self.blockName = None
        self.loadingScreen = ToontownLoadingScreen.ToontownLoadingScreen()
        self._tickCounter = 0
        self._tickSkip = 1
        self._lastTickT = 0.0
        self._loadStartT = 0.0
        return

    def destroy(self):
        if hasattr(self, 'loadingScreen') and self.loadingScreen:
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
        self._lastTickT = globalClock.getRealTime()
        self.blockName = name
        self.loadingScreen.begin(range, label, gui, tipCategory)
        try:
            if isinstance(name, int) or (isinstance(name, str) and name.isdigit()):
                zonePrefetchManager.prefetch_zone(int(name), loader=self)
        except Exception:
            pass
        return None

    def endBulkLoad(self, name):
        if not self.inBulkBlock:
            Loader.Loader.notify.warning("Tried to end a block ('%s'), but not in one" % name)
            return None
        if name != self.blockName:
            Loader.Loader.notify.warning("Tried to end a block ('%s'), other then the current one ('%s')" % (name, self.blockName))
            return None
        self.inBulkBlock = None
        expectedCount, loadedCount = self.loadingScreen.end()
        now = globalClock.getRealTime()
        Loader.Loader.notify.info("At end of block '%s', expected %s, loaded %s, duration=%s" % (self.blockName,
         expectedCount,
         loadedCount,
         now - self._loadStartT))
        return

    def abortBulkLoad(self):
        if self.inBulkBlock:
            Loader.Loader.notify.info("Aborting block ('%s')" % self.blockName)
            self.inBulkBlock = None
            self.loadingScreen.abort()
        return

    def tick(self):
        if self.inBulkBlock:
            self._tickCounter += 1
            if self._tickCounter >= self._tickSkip:
                self._tickCounter = 0
                now = globalClock.getRealTime()
                if now - self._lastTickT > self.TickPeriod:
                    self._lastTickT = now
                    self.loadingScreen.tick()
                    try:
                        base.cr.considerHeartbeat()
                    except Exception:
                        pass

    def loadModel(self, *args, **kw):
        ret = Loader.Loader.loadModel(self, *args, **kw)
        self.tick()
        if ret and hasattr(self.loadingScreen, 'on_asset_loaded'):
            path = args[0] if args else None
            self.loadingScreen.on_asset_loaded(path=path, model=ret, kind='model')
        return ret

    def loadFont(self, *args, **kw):
        ret = Loader.Loader.loadFont(self, *args, **kw)
        self.tick()
        if ret and hasattr(self.loadingScreen, 'on_asset_loaded'):
            path = args[0] if args else None
            self.loadingScreen.on_asset_loaded(path=path, kind='font')
        return ret

    def loadTexture(self, texturePath, alphaPath = None, okMissing = False):
        ret = Loader.Loader.loadTexture(self, texturePath, alphaPath, okMissing=okMissing)
        self.tick()
        if alphaPath:
            self.tick()
        if ret and hasattr(self.loadingScreen, 'on_asset_loaded'):
            self.loadingScreen.on_asset_loaded(path=texturePath, texture=ret, kind='texture')
        return ret

    def loadSfx(self, soundPath):
        ret = Loader.Loader.loadSfx(self, soundPath)
        self.tick()
        if ret and hasattr(self.loadingScreen, 'on_asset_loaded'):
            self.loadingScreen.on_asset_loaded(path=soundPath, kind='audio')
        return ret

    def loadMusic(self, soundPath):
        ret = Loader.Loader.loadMusic(self, soundPath)
        self.tick()
        if ret and hasattr(self.loadingScreen, 'on_asset_loaded'):
            self.loadingScreen.on_asset_loaded(path=soundPath, kind='audio')
        return ret

    def loadDNAFileAI(self, dnaStore, dnaFile):
        ret = loadDNAFileAI(dnaStore, dnaFile, CSDefault)
        self.tick()
        return ret

    def loadDNAFile(self, dnaStore, dnaFile):
        ret = loadDNAFile(dnaStore, dnaFile, CSDefault, 0)
        self.tick()
        return ret
