from direct.gui.DirectGui import *
from panda3d.core import *
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
import random
from toontown.toontowngui import ModernLoadingScreen

class ToontownLoadingScreen:

    def __init__(self):
        self.__expectedCount = 0
        self.__count = 0
        self.__updateSkip = 1
        self.__updateCounter = 0
        self.modern = None
        if ConfigVariableBool('want-modern-launcher-ui', True).value:
            try:
                if hasattr(base, 'modernLoading') and base.modernLoading:
                    self.modern = base.modernLoading
                else:
                    self.modern = ModernLoadingScreen.ModernLoadingScreen()
                    base.modernLoading = self.modern
            except Exception:
                self.modern = None
        self.gui = loader.loadModel('phase_3/models/gui/progress-background')
        self.banner = loader.loadModel('phase_3/models/gui/toon_council').find('**/scroll')
        self.banner.reparentTo(self.gui)
        self.banner.setScale(0.4, 0.4, 0.4)
        # Widescreen support: stretch the 4:3 background to cover widescreen
        # displays, then counter-scale the child elements so they keep their
        # original proportions (no black bars, no distorted text).
        self.wideScale = 1.0
        try:
            self.wideScale = float(base.getWidescreenGUIXScale())
        except Exception:
            self.wideScale = 1.0
        if self.wideScale != 1.0:
            self.gui.setScale(self.wideScale, 1, 1)
            self.banner.setScale(0.4 / self.wideScale, 0.4, 0.4)
        self.tip = DirectLabel(guiId='ToontownLoadingScreenTip', parent=self.banner, relief=None, text='', text_scale=TTLocalizer.TLStip, textMayChange=1, pos=(-1.2, 0.0, 0.1), text_fg=(0.4, 0.3, 0.2, 1), text_wordwrap=13, text_align=TextNode.ALeft)
        self.title = DirectLabel(guiId='ToontownLoadingScreenTitle', parent=self.gui, relief=None, pos=(-1.06, 0, -0.77), text='', textMayChange=1, text_scale=0.08, text_fg=(0, 0, 0.5, 1), text_align=TextNode.ALeft)
        self.waitBar = DirectWaitBar(guiId='ToontownLoadingScreenWaitBar', parent=self.gui, frameSize=(-1.06,
         1.06,
         -0.03,
         0.03), pos=(0, 0, -0.85), text='')
        return

    def destroy(self):
        import builtins
        b = getattr(builtins, 'base', None)
        if self.modern and self.modern is not getattr(b, 'modernLoading', None):
            try:
                self.modern.destroy()
            except Exception:
                pass
        self.modern = None
        self.tip.destroy()
        self.title.destroy()
        self.waitBar.destroy()
        self.banner.removeNode()
        self.gui.removeNode()

    def getTip(self, tipCategory):
        tips = TTLocalizer.TipDict.get(tipCategory)
        if tips:
            return TTLocalizer.TipTitle + '\n' + random.choice(tips)
        return TTLocalizer.TipTitle

    def begin(self, range, label, gui, tipCategory):
        self.__count = 0
        self.__expectedCount = max(1, range)
        tip_text = self.getTip(tipCategory)
        if self.modern and self.modern.enabled():
            self.modern.enter_bulk_load('bulk', label, self.__expectedCount)
            self.modern.set_status(label)
            self.modern.set_detail(tip_text)
            self.modern.set_progress(0.0)
            self.gui.reparentTo(hidden)
            self.waitBar.reparentTo(hidden)
            self.title.reparentTo(hidden)
            return
        self.waitBar['range'] = range
        self.title['text'] = label
        self.tip['text'] = tip_text
        if gui:
            self.waitBar.reparentTo(self.gui)
            self.title.reparentTo(self.gui)
            if self.wideScale != 1.0:
                # Counter-scale so the bar/title keep 4:3 proportions on widescreen
                self.waitBar.setScale(1.0 / self.wideScale, 1, 1)
                self.title.setScale(1.0 / self.wideScale, 1, 1)
            self.gui.reparentTo(aspect2dp, DGG.NO_FADE_SORT_INDEX)
        else:
            self.waitBar.reparentTo(aspect2dp, DGG.NO_FADE_SORT_INDEX)
            self.title.reparentTo(aspect2dp, DGG.NO_FADE_SORT_INDEX)
            self.gui.reparentTo(hidden)
        self.waitBar.update(self.__count)

    def end(self):
        if self.modern and self.modern.enabled():
            self.modern.set_progress(100.0)
            self.modern.leave_bulk_load()
            return (self.__expectedCount, self.__count)
        self.waitBar.finish()
        self.waitBar.reparentTo(self.gui)
        self.title.reparentTo(self.gui)
        if self.wideScale != 1.0:
            # Restore normal scale now that the screen is hidden
            self.waitBar.setScale(1, 1, 1)
            self.title.setScale(1, 1, 1)
        self.gui.reparentTo(hidden)
        return (self.__expectedCount, self.__count)

    def abort(self):
        if self.modern and self.modern.enabled():
            self.modern.leave_bulk_load()
            return
        self.gui.reparentTo(hidden)

    def tick(self):
        self.__count += 1
        if self.modern and self.modern.enabled():
            pct = (float(self.__count) / float(self.__expectedCount)) * 100.0
            self.modern.set_progress(pct)
            return
        self.__updateCounter += 1
        if self.__updateCounter >= self.__updateSkip:
            self.__updateCounter = 0
            self.waitBar.update(self.__count)

    def on_asset_loaded(self, path=None, model=None, texture=None, kind='model'):
        if self.modern and self.modern.enabled():
            try:
                self.modern.on_asset_loaded(path=path, model=model, texture=texture, kind=kind)
            except Exception:
                pass
