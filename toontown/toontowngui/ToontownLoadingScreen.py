from direct.gui.DirectGui import *
from panda3d.core import *
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
import random

class ToontownLoadingScreen:

    def __init__(self):
        self.__expectedCount = 0
        self.__count = 0
        self.__updateSkip = 5
        self.__updateCounter = 0
        # Background art was authored for 4:3; we widen it for 16:9+ without
        # stretching text/UI by keeping UI elements parented to aspect2d.
        self.background = loader.loadModel('phase_3/models/gui/progress-background')
        self.banner = loader.loadModel('phase_3/models/gui/toon_council').find('**/scroll')
        self.banner.setScale(0.4, 0.4, 0.4)
        self.tip = DirectLabel(guiId='ToontownLoadingScreenTip', parent=self.banner, relief=None, text='', text_scale=TTLocalizer.TLStip, textMayChange=1, pos=(-1.2, 0.0, 0.1), text_fg=(0.4, 0.3, 0.2, 1), text_wordwrap=13, text_align=TextNode.ALeft)
        self.title = DirectLabel(guiId='ToontownLoadingScreenTitle', parent=hidden, relief=None, pos=(-1.06, 0, -0.77), text='', textMayChange=1, text_scale=0.08, text_fg=(0, 0, 0.5, 1), text_align=TextNode.ALeft)
        self.waitBar = DirectWaitBar(guiId='ToontownLoadingScreenWaitBar', parent=hidden, frameSize=(-1.06,
         1.06,
         -0.03,
         0.03), pos=(0, 0, -0.85), text='')
        return

    def __getBackgroundXScale(self):
        # aspect2d is a fixed-height space; its width expands with aspect ratio.
        # The original art is laid out for 4:3 (1.333...).
        try:
            currentAspect = float(base.camLens.getAspectRatio())
        except Exception:
            currentAspect = 4.0 / 3.0
        return max(1.0, currentAspect / (4.0 / 3.0))

    def __applyWidescreenLayout(self):
        # Keep a consistent margin from the left/right edges regardless of aspect.
        leftMargin = 0.273333  # (-1.06) - (-4/3)
        rightMargin = 0.273333 # (4/3) - (1.06)
        xLeft = base.a2dLeft + leftMargin
        xRight = base.a2dRight - rightMargin

        self.title.setPos(xLeft, 0, -0.77)
        self.waitBar['frameSize'] = (xLeft, xRight, -0.03, 0.03)
        self.waitBar.setPos(0, 0, -0.85)

    def destroy(self):
        self.tip.destroy()
        self.title.destroy()
        self.waitBar.destroy()
        self.banner.removeNode()
        self.background.removeNode()

    def getTip(self, tipCategory):
        return TTLocalizer.TipTitle + '\n' + random.choice(TTLocalizer.TipDict.get(tipCategory))

    def begin(self, range, label, gui, tipCategory, minimal=False):
        self.waitBar['range'] = range
        self.title['text'] = label
        self.tip['text'] = self.getTip(tipCategory)
        self.__count = 0
        self.__expectedCount = range
        if minimal:
            self.waitBar.reparentTo(hidden)
            self.title.reparentTo(hidden)
            self.banner.reparentTo(hidden)
            self.background.reparentTo(hidden)
        else:
            self.waitBar.reparentTo(aspect2dp, DGG.NO_FADE_SORT_INDEX)
            self.title.reparentTo(aspect2dp, DGG.NO_FADE_SORT_INDEX)
            self.banner.reparentTo(aspect2dp, DGG.NO_FADE_SORT_INDEX)

            if gui:
                self.background.reparentTo(aspect2dp, DGG.NO_FADE_SORT_INDEX)
                self.background.setScale(self.__getBackgroundXScale(), 1.0, 1.0)
            else:
                self.background.reparentTo(hidden)
                self.banner.reparentTo(hidden)

            self.__applyWidescreenLayout()
        self.waitBar.update(self.__count)

    def get_progress_fraction(self):
        if self.__expectedCount <= 0:
            return 1.0
        return max(0.0, min(1.0, float(self.__count) / float(self.__expectedCount)))

    def end(self):
        self.waitBar.finish()
        self.waitBar.reparentTo(hidden)
        self.title.reparentTo(hidden)
        self.banner.reparentTo(hidden)
        self.background.reparentTo(hidden)
        return (self.__expectedCount, self.__count)

    def abort(self):
        self.banner.reparentTo(hidden)
        self.background.reparentTo(hidden)

    def tick(self):
        self.__count = self.__count + 1
        self.__updateCounter += 1
        if self.__updateCounter >= self.__updateSkip:
            self.__updateCounter = 0
            self.waitBar.update(self.__count)
