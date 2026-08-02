from direct.gui.DirectGui import *
from panda3d.core import *

from toontown.shtiker import ShtikerPage
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from toontown.quest import AutoerManager


class AutoerPage(ShtikerPage.ShtikerPage):

    def __init__(self):
        ShtikerPage.ShtikerPage.__init__(self)
        return

    def load(self):
        ShtikerPage.ShtikerPage.load(self)
        self.title = DirectLabel(
            parent=self,
            relief=None,
            text=TTLocalizer.AutoerPageTitle,
            text_scale=0.12,
            pos=(0, 0, 0.62),
        )
        helpText = TTLocalizer.AutoerPageHelp
        self.helpLabel = DirectLabel(
            parent=self,
            relief=None,
            text=helpText,
            text_scale=0.045,
            text_align=TextNode.ACenter,
            text_wordwrap=28,
            pos=(0, 0, 0.38),
        )
        self.statusLabel = DirectLabel(
            parent=self,
            relief=None,
            text=TTLocalizer.AutoerPageStatusIdle,
            text_scale=0.045,
            text_align=TextNode.ACenter,
            pos=(0, 0, 0.06),
            textMayChange=1,
        )
        # frameSize in aspect2d units: keep width ~1.0–1.2 (same ballpark as InventoryPage restock, etc.)
        btnFrame = (-1.05, 1.05, -0.1, 0.1)
        btnTextScale = 0.042
        self.loadBtn = DirectButton(
            parent=self,
            relief=DGG.RAISED,
            text=TTLocalizer.AutoerPageLoad,
            text_scale=btnTextScale,
            frameSize=btnFrame,
            borderWidth=(0.01, 0.01),
            pos=(0, 0, -0.14),
            command=self.__loadBundle,
        )
        self.startBtn = DirectButton(
            parent=self,
            relief=DGG.RAISED,
            text=TTLocalizer.AutoerPageStartTasks,
            text_scale=btnTextScale,
            frameSize=btnFrame,
            borderWidth=(0.01, 0.01),
            pos=(0, 0, -0.3),
            command=self.__startTasks,
        )
        self.stopBtn = DirectButton(
            parent=self,
            relief=DGG.RAISED,
            text=TTLocalizer.AutoerPageStopAll,
            text_scale=btnTextScale,
            frameSize=btnFrame,
            borderWidth=(0.01, 0.01),
            pos=(0, 0, -0.46),
            command=self.__stopAll,
            text_fg=(0.9, 0.2, 0.2, 1),
        )
        return

    def unload(self):
        del self.title
        del self.helpLabel
        del self.statusLabel
        self.loadBtn.destroy()
        del self.loadBtn
        self.startBtn.destroy()
        del self.startBtn
        self.stopBtn.destroy()
        del self.stopBtn
        ShtikerPage.ShtikerPage.unload(self)

    def __refreshStatus(self):
        if AutoerManager.isBundleLoaded():
            self.statusLabel['text'] = TTLocalizer.AutoerPageStatusLoaded
        else:
            self.statusLabel['text'] = TTLocalizer.AutoerPageStatusIdle

    def __loadBundle(self):
        messenger.send('wakeup')
        if AutoerManager.loadAutoerBundle():
            self.__refreshStatus()
            try:
                base.localAvatar.setSystemMessage(0, TTLocalizer.AutoerPageMsgLoaded)
            except Exception:
                pass
        else:
            try:
                base.localAvatar.setSystemMessage(0, TTLocalizer.AutoerPageMsgLoadFail)
            except Exception:
                pass

    def __startTasks(self):
        messenger.send('wakeup')
        if AutoerManager.startTaskAutomation():
            self.__refreshStatus()
            try:
                base.localAvatar.setSystemMessage(0, TTLocalizer.AutoerPageMsgStarted)
            except Exception:
                pass

    def __stopAll(self):
        messenger.send('wakeup')
        AutoerManager.stopAllAutoers()
        self.__refreshStatus()

    def enter(self):
        ShtikerPage.ShtikerPage.enter(self)
        self.__refreshStatus()

    def exit(self):
        ShtikerPage.ShtikerPage.exit(self)
