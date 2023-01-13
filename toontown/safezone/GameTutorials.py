from direct.gui.DirectGui import *
from direct.fsm import FSM
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from panda3d.core import *
from direct.interval.IntervalGlobal import *

class ChineseTutorial(DirectFrame, FSM.FSM):

    def __init__(self, doneFunction, doneEvent = None, callback = None):
        FSM.FSM.__init__(self, 'ChineseTutorial')
        self.doneFunction = doneFunction
        base.localAvatar.startSleepWatch(self.handleQuit)
        self.doneEvent = doneEvent
        self.callback = callback
        self.setStateArray(['Page1', 'Page2', 'Quit'])
        base.localAvatar.startSleepWatch(self.handleQuit)
        DirectFrame.__init__(self, pos=(-0.7, 0.0, 0.0), image_color=ToontownGlobals.GlobalDialogColor, image_scale=(1.0, 1.5, 1.0), text='', text_scale=0.06)
        self.accept('stoppedAsleep', self.handleQuit)
        self['image'] = DGG.getDefaultDialogGeom()
        self.title = DirectLabel(self, relief=None, text='', text_pos=(0.0, 0.4), text_fg=(1, 0, 0, 1), text_scale=0.13, text_font=ToontownGlobals.getSignFont())
        images = loader.loadModel('phase_6/models/golf/checker_tutorial.bam')
        images.setTransparency(1)
        self.iPage1 = images.find('**/tutorialPage1*')
        self.iPage1.reparentTo(aspect2d)
        self.iPage1.setPos(0.43, -0.1, 0.0)
        self.iPage1.setScale(13.95)
        self.iPage1.setTransparency(1)
        self.iPage1.hide()
        self.iPage1.getChildren()[1].hide()
        self.iPage2 = images.find('**/tutorialPage3*')
        self.iPage2.reparentTo(aspect2d)
        self.iPage2.setPos(0.43, -0.1, 0.5)
        self.iPage2.setScale(13.95)
        self.iPage2.setTransparency(1)
        self.iPage2.hide()
        self.iPage3 = images.find('**/tutorialPage2*')
        self.iPage3.reparentTo(aspect2d)
        self.iPage3.setPos(0.43, -0.1, -0.5)
        self.iPage3.setScale(13.95)
        self.iPage3.setTransparency(1)
        self.iPage3.hide()
        buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
        gui = loader.loadModel('phase_3.5/models/gui/friendslist_gui')
        self.bNext = DirectButton(self, image=(gui.find('**/Horiz_Arrow_UP'),
         gui.find('**/Horiz_Arrow_DN'),
         gui.find('**/Horiz_Arrow_Rllvr'),
         gui.find('**/Horiz_Arrow_UP')), image3_color=Vec4(1, 1, 1, 0.5), relief=None, text=TTLocalizer.ChineseTutorialNext, text3_fg=Vec4(0, 0, 0, 0.5), text_scale=0.05, text_pos=(0.0, -0.1), pos=(0.35, -0.3, -0.33), command=self.requestNext)
        self.bPrev = DirectButton(self, image=(gui.find('**/Horiz_Arrow_UP'),
         gui.find('**/Horiz_Arrow_DN'),
         gui.find('**/Horiz_Arrow_Rllvr'),
         gui.find('**/Horiz_Arrow_UP')), image3_color=Vec4(1, 1, 1, 0.5), image_scale=(-1.0, 1.0, 1.0), relief=None, text=TTLocalizer.ChineseTutorialPrev, text3_fg=Vec4(0, 0, 0, 0.5), text_scale=0.05, text_pos=(0.0, -0.1), pos=(-0.35, -0.3, -0.33), command=self.requestPrev)
        self.bQuit = DirectButton(self, image=(buttons.find('**/ChtBx_OKBtn_UP'), buttons.find('**/ChtBx_OKBtn_DN'), buttons.find('**/ChtBx_OKBtn_Rllvr')), relief=None, text=TTLocalizer.ChineseTutorialDone, text_scale=0.05, text_pos=(0.0, -0.1), pos=(0.0, -0.3, -0.33), command=self.handleQuit)
        self.bQuit.hide()
        buttons.removeNode()
        gui.removeNode()
        self.request('Page1')
        return

    def __del__(self):
        self.cleanup()

    def enterPage1(self, *args):
        self.bNext.show()
        self.title['text'] = (TTLocalizer.ChineseTutorialTitle1,)
        self['text'] = TTLocalizer.ChinesePage1
        self['text_pos'] = (0.0, 0.23)
        self['text_wordwrap'] = 13.5
        self.bPrev['state'] = DGG.DISABLED
        self.bPrev.hide()
        self.bNext['state'] = DGG.NORMAL
        self.iPage1.show()
        self.blinker = Sequence()
        obj = self.iPage1.getChildren()[1]
        self.iPage1.getChildren()[1].show()
        self.blinker.append(LerpColorInterval(obj, 0.5, Vec4(0.5, 0.5, 0, 0.0), Vec4(0.2, 0.2, 0.2, 1)))
        self.blinker.append(LerpColorInterval(obj, 0.5, Vec4(0.2, 0.2, 0.2, 1), Vec4(0.5, 0.5, 0, 0.0)))
        self.blinker.loop()

    def exitPage1(self, *args):
        self.bPrev['state'] = DGG.NORMAL
        self.iPage1.hide()
        self.iPage1.getChildren()[1].hide()
        self.blinker.finish()

    def enterPage2(self, *args):
        self.bPrev.show()
        self.title['text'] = (TTLocalizer.ChineseTutorialTitle2,)
        self['text'] = TTLocalizer.ChinesePage2
        self['text_pos'] = (0.0, 0.28)
        self['text_wordwrap'] = 12.5
        self.bNext['state'] = DGG.DISABLED
        self.bNext.hide()
        self.iPage2.show()
        self.iPage3.show()
        self.bQuit.show()

    def exitPage2(self, *args):
        self.iPage2.hide()
        self.bQuit.hide()
        self.iPage3.hide()

    def enterQuit(self, *args):
        self.iPage1.removeNode()
        self.iPage2.removeNode()
        self.iPage3.removeNode()
        self.bNext.destroy()
        self.bPrev.destroy()
        self.bQuit.destroy()
        DirectFrame.destroy(self)

    def exitQuit(self, *args):
        pass

    def handleQuit(self, task = None):
        base.cr.playGame.getPlace().setState('walk')
        self.forceTransition('Quit')
        self.doneFunction()
        if task != None:
            task.done
        return


class CheckersTutorial(DirectFrame, FSM.FSM):

    def __init__(self, doneFunction, doneEvent = None, callback = None):
        FSM.FSM.__init__(self, 'CheckersTutorial')
        self.doneFunction = doneFunction
        base.localAvatar.startSleepWatch(self.handleQuit)
        self.doneEvent = doneEvent
        self.callback = callback
        self.setStateArray(['Page1',
         'Page2',
         'Page3',
         'Quit'])
        DirectFrame.__init__(self, pos=(-0.7, 0.0, 0.0), image_color=ToontownGlobals.GlobalDialogColor, image_scale=(1.0, 1.5, 1.0), text='', text_scale=0.06)
        self.accept('stoppedAsleep', self.handleQuit)
        self['image'] = DGG.getDefaultDialogGeom()
        self.title = DirectLabel(self, relief=None, text='', text_pos=(0.0, 0.4), text_fg=(1, 0, 0, 1), text_scale=0.13, text_font=ToontownGlobals.getSignFont())
        images = loader.loadModel('phase_6/models/golf/regularchecker_tutorial.bam')
        images.setTransparency(1)
        self.iPage1 = images.find('**/tutorialPage1*')
        self.iPage1.reparentTo(aspect2d)
        self.iPage1.setPos(0.43, -0.1, 0.0)
        self.iPage1.setScale(0.4)
        self.iPage1.setTransparency(1)
        self.iPage1.hide()
        self.iPage2 = images.find('**/tutorialPage2*')
        self.iPage2.reparentTo(aspect2d)
        self.iPage2.setPos(0.43, -0.1, 0.0)
        self.iPage2.setScale(0.4)
        self.iPage2.setTransparency(1)
        self.iPage2.hide()
        self.iPage3 = images.find('**/tutorialPage3*')
        self.iPage3.reparentTo(aspect2d)
        self.iPage3.setPos(0.6, -0.1, 0.5)
        self.iPage3.setScale(0.4)
        self.iPage3.setTransparency(1)
        self.obj = self.iPage3.find('**/king*')
        self.iPage3.hide()
        self.iPage4 = images.find('**/tutorialPage4*')
        self.iPage4.reparentTo(aspect2d)
        self.iPage4.setPos(0.6, -0.1, -0.5)
        self.iPage4.setScale(0.4)
        self.iPage4.setTransparency(1)
        self.iPage4.hide()
        buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
        gui = loader.loadModel('phase_3.5/models/gui/friendslist_gui')
        self.bNext = DirectButton(self, image=(gui.find('**/Horiz_Arrow_UP'),
         gui.find('**/Horiz_Arrow_DN'),
         gui.find('**/Horiz_Arrow_Rllvr'),
         gui.find('**/Horiz_Arrow_UP')), image3_color=Vec4(1, 1, 1, 0.5), relief=None, text=TTLocalizer.ChineseTutorialNext, text3_fg=Vec4(0, 0, 0, 0.5), text_scale=0.05, text_pos=(0.0, -0.1), pos=(0.35, -0.3, -0.33), command=self.requestNext)
        self.bPrev = DirectButton(self, image=(gui.find('**/Horiz_Arrow_UP'),
         gui.find('**/Horiz_Arrow_DN'),
         gui.find('**/Horiz_Arrow_Rllvr'),
         gui.find('**/Horiz_Arrow_UP')), image3_color=Vec4(1, 1, 1, 0.5), image_scale=(-1.0, 1.0, 1.0), relief=None, text=TTLocalizer.ChineseTutorialPrev, text3_fg=Vec4(0, 0, 0, 0.5), text_scale=0.05, text_pos=(0.0, -0.1), pos=(-0.35, -0.3, -0.33), command=self.requestPrev)
        self.bQuit = DirectButton(self, image=(buttons.find('**/ChtBx_OKBtn_UP'), buttons.find('**/ChtBx_OKBtn_DN'), buttons.find('**/ChtBx_OKBtn_Rllvr')), relief=None, text=TTLocalizer.ChineseTutorialDone, text_scale=0.05, text_pos=(0.0, -0.1), pos=(0.0, -0.3, -0.33), command=self.handleQuit)
        self.bQuit.hide()
        buttons.removeNode()
        gui.removeNode()
        self.request('Page1')
        return

    def __del__(self):
        self.cleanup()

    def enterPage1(self, *args):
        self.bNext.show()
        self.title['text'] = (TTLocalizer.ChineseTutorialTitle1,)
        self['text'] = TTLocalizer.CheckersPage1
        self['text_pos'] = (0.0, 0.23)
        self['text_wordwrap'] = 13.5
        self['text_scale'] = 0.06
        self.bPrev['state'] = DGG.DISABLED
        self.bPrev.hide()
        self.bNext['state'] = DGG.NORMAL
        self.iPage1.show()

    def exitPage1(self, *args):
        self.bPrev['state'] = DGG.NORMAL
        self.iPage1.hide()

    def enterPage2(self, *args):
        self.bPrev.show()
        self.bNext.show()
        self.title['text'] = (TTLocalizer.ChineseTutorialTitle2,)
        self['text'] = TTLocalizer.CheckersPage2
        self['text_pos'] = (0.0, 0.28)
        self['text_wordwrap'] = 12.5
        self['text_scale'] = 0.06
        self.bNext['state'] = DGG.NORMAL
        self.iPage2.show()

    def exitPage2(self, *args):
        self.iPage2.hide()

    def enterPage3(self, *args):
        self.bPrev.show()
        self.title['text'] = (TTLocalizer.ChineseTutorialTitle2,)
        self['text'] = TTLocalizer.CheckersPage3 + '\n\n' + TTLocalizer.CheckersPage4
        self['text_pos'] = (0.0, 0.32)
        self['text_wordwrap'] = 19
        self['text_scale'] = 0.05
        self.bNext['state'] = DGG.DISABLED
        self.blinker = Sequence()
        self.blinker.append(LerpColorInterval(self.obj, 0.5, Vec4(0.5, 0.5, 0, 0.0), Vec4(0.9, 0.9, 0, 1)))
        self.blinker.append(LerpColorInterval(self.obj, 0.5, Vec4(0.9, 0.9, 0, 1), Vec4(0.5, 0.5, 0, 0.0)))
        self.blinker.loop()
        self.bNext.hide()
        self.iPage3.show()
        self.iPage4.show()
        self.bQuit.show()

    def exitPage3(self, *args):
        self.blinker.finish()
        self.iPage3.hide()
        self.bQuit.hide()
        self.iPage4.hide()

    def enterQuit(self, *args):
        self.iPage1.removeNode()
        self.iPage2.removeNode()
        self.iPage3.removeNode()
        self.bNext.destroy()
        self.bPrev.destroy()
        self.bQuit.destroy()
        DirectFrame.destroy(self)

    def exitQuit(self, *args):
        pass

    def handleQuit(self, task = None):
        self.forceTransition('Quit')
        base.cr.playGame.getPlace().setState('walk')
        self.doneFunction()
        if task != None:
            task.done
        return
