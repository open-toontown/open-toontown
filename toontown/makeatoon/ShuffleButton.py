from pandac.PandaModules import *
from direct.gui.DirectGui import *
from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownGlobals
from MakeAToonGlobals import *
from direct.directnotify import DirectNotifyGlobal
from direct.interval.IntervalGlobal import *
import random

class ShuffleButton:
    notify = DirectNotifyGlobal.directNotify.newCategory('ShuffleButton')

    def __init__(self, parent, fetchEvent):
        self.parent = parent
        self.fetchEvent = fetchEvent
        self.history = [0]
        self.historyPtr = 0
        self.maxHistory = 10
        self.load()

    def load(self):
        gui = loader.loadModel('phase_3/models/gui/tt_m_gui_mat_mainGui')
        shuffleFrame = gui.find('**/tt_t_gui_mat_shuffleFrame')
        shuffleUp = gui.find('**/tt_t_gui_mat_shuffleUp')
        shuffleDown = gui.find('**/tt_t_gui_mat_shuffleDown')
        shuffleArrowUp = gui.find('**/tt_t_gui_mat_shuffleArrowUp')
        shuffleArrowDown = gui.find('**/tt_t_gui_mat_shuffleArrowDown')
        shuffleArrowDisabled = gui.find('**/tt_t_gui_mat_shuffleArrowDisabled')
        gui.removeNode()
        del gui
        self.parentFrame = DirectFrame(parent=self.parent.parentFrame, relief=DGG.RAISED, pos=(0, 0, -1), frameColor=(1, 0, 0, 0))
        self.shuffleFrame = DirectFrame(parent=self.parentFrame, image=shuffleFrame, image_scale=halfButtonInvertScale, relief=None, frameColor=(1, 1, 1, 1))
        self.shuffleFrame.hide()
        self.shuffleBtn = DirectButton(parent=self.parentFrame, relief=None, image=(shuffleUp, shuffleDown, shuffleUp), image_scale=halfButtonInvertScale, image1_scale=(-0.63, 0.6, 0.6), image2_scale=(-0.63, 0.6, 0.6), text=(TTLocalizer.ShuffleButton,
         TTLocalizer.ShuffleButton,
         TTLocalizer.ShuffleButton,
         ''), text_font=ToontownGlobals.getInterfaceFont(), text_scale=TTLocalizer.SBshuffleBtn, text_pos=(0, -0.02), text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1), command=self.chooseRandom)
        self.incBtn = DirectButton(parent=self.parentFrame, relief=None, image=(shuffleArrowUp,
         shuffleArrowDown,
         shuffleArrowUp,
         shuffleArrowDisabled), image_scale=halfButtonInvertScale, image1_scale=halfButtonInvertHoverScale, image2_scale=halfButtonInvertHoverScale, pos=(0.202, 0, 0), command=self.__goFrontHistory)
        self.incBtn.hide()
        self.decBtn = DirectButton(parent=self.parentFrame, relief=None, image=(shuffleArrowUp,
         shuffleArrowDown,
         shuffleArrowUp,
         shuffleArrowDisabled), image_scale=halfButtonScale, image1_scale=halfButtonHoverScale, image2_scale=halfButtonHoverScale, pos=(-0.202, 0, 0), command=self.__goBackHistory)
        self.decBtn.hide()
        self.lerpDuration = 0.5
        self.showLerp = None
        self.frameShowLerp = LerpColorInterval(self.shuffleFrame, self.lerpDuration, Vec4(1, 1, 1, 1), Vec4(1, 1, 1, 0))
        self.incBtnShowLerp = LerpColorInterval(self.incBtn, self.lerpDuration, Vec4(1, 1, 1, 1), Vec4(1, 1, 1, 0))
        self.decBtnShowLerp = LerpColorInterval(self.decBtn, self.lerpDuration, Vec4(1, 1, 1, 1), Vec4(1, 1, 1, 0))
        self.__updateArrows()
        return

    def unload(self):
        if self.showLerp:
            self.showLerp.finish()
            del self.showLerp
        self.parent = None
        self.parentFrame.destroy()
        self.shuffleFrame.destroy()
        self.shuffleBtn.destroy()
        self.incBtn.destroy()
        self.decBtn.destroy()
        del self.parentFrame
        del self.shuffleFrame
        del self.shuffleBtn
        del self.incBtn
        del self.decBtn
        return

    def showButtons(self):
        self.shuffleFrame.show()
        self.shuffleBtn.show()
        self.incBtn.show()
        self.decBtn.show()

    def hideButtons(self):
        self.shuffleFrame.hide()
        self.shuffleBtn.hide()
        self.incBtn.hide()
        self.decBtn.hide()

    def setChoicePool(self, pool):
        self.pool = pool

    def chooseRandom(self):
        self.saveCurrChoice()
        self.currChoice = []
        for prop in self.pool:
            self.currChoice.append(random.choice(prop))

        self.notify.debug('current choice : %s' % self.currChoice)
        if len(self.history) == self.maxHistory:
            self.history.remove(self.history[0])
        self.history.append(0)
        self.historyPtr = len(self.history) - 1
        if len(self.history) == 2:
            self.startShowLerp()
        self.__updateArrows()
        messenger.send(self.fetchEvent)

    def getCurrChoice(self):
        return self.currChoice

    def saveCurrChoice(self):
        self.currChoice = self.parent.getCurrToonSetting()
        self.history[self.historyPtr] = self.currChoice

    def __goBackHistory(self):
        self.saveCurrChoice()
        self.historyPtr -= 1
        self.currChoice = self.history[self.historyPtr]
        self.__updateArrows()
        messenger.send(self.fetchEvent)

    def __goFrontHistory(self):
        self.saveCurrChoice()
        self.historyPtr += 1
        self.currChoice = self.history[self.historyPtr]
        self.__updateArrows()
        messenger.send(self.fetchEvent)

    def __updateArrows(self):
        if self.historyPtr == 0:
            self.decBtn['state'] = DGG.DISABLED
        else:
            self.decBtn['state'] = DGG.NORMAL
        if self.historyPtr >= len(self.history) - 1:
            self.incBtn['state'] = DGG.DISABLED
        else:
            self.incBtn['state'] = DGG.NORMAL

    def startShowLerp(self):
        self.showLerp = Sequence(Parallel(Func(self.shuffleFrame.show), Func(self.incBtn.show), Func(self.decBtn.show)), Parallel(self.frameShowLerp, self.incBtnShowLerp, self.decBtnShowLerp))
        self.showLerp.start()

    def cleanHistory(self):
        self.history = [0]
        self.historyPtr = 0
        self.shuffleFrame.hide()
        self.incBtn.hide()
        self.decBtn.hide()
