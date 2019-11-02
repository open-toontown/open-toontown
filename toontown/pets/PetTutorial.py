from direct.gui.DirectGui import *
from pandac.PandaModules import *
from direct.fsm import FSM
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer

class PetTutorial(DirectFrame, FSM.FSM):
    notify = DirectNotifyGlobal.directNotify.newCategory('PetTutorial')

    def __init__(self, doneEvent):
        FSM.FSM.__init__(self, 'PetTutorial')
        self.doneEvent = doneEvent
        self.setStateArray(['Page1', 'Page2', 'Page3'])
        DirectFrame.__init__(self, pos=(0.0, 0.0, 0.0), image_color=ToontownGlobals.GlobalDialogColor, image_scale=(1.5, 1.5, 0.9), text='', text_scale=0.06)
        self['image'] = DGG.getDefaultDialogGeom()
        self.title = DirectLabel(self, relief=None, text='', text_pos=(0.0, 0.32), text_fg=(1, 0, 0, 1), text_scale=TTLocalizer.PTtitle, text_font=ToontownGlobals.getSignFont())
        images = loader.loadModel('phase_5.5/models/gui/PetTutorial')
        self.iPage1 = DirectFrame(self, image=images.find('**/PetTutorialPanel'), scale=0.75, pos=(-0.55, -0.1, 0))
        self.iPage1.hide()
        self.iPage2 = DirectFrame(self, image=images.find('**/PetTutorialSpeedChat'), scale=0.75, pos=(0.43, -0.1, 0.05))
        self.iPage2.hide()
        self.iPage3 = DirectFrame(self, image=images.find('**/PetTutorialCattlelog'), scale=0.75, pos=(-0.55, -0.1, 0))
        self.iPage3.hide()
        buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
        gui = loader.loadModel('phase_3.5/models/gui/friendslist_gui')
        self.bNext = DirectButton(self, image=(gui.find('**/Horiz_Arrow_UP'),
         gui.find('**/Horiz_Arrow_DN'),
         gui.find('**/Horiz_Arrow_Rllvr'),
         gui.find('**/Horiz_Arrow_UP')), image3_color=Vec4(1, 1, 1, 0.5), relief=None, text=TTLocalizer.PetTutorialNext, text3_fg=Vec4(0, 0, 0, 0.5), text_scale=0.05, text_pos=(0.0, -0.1), pos=(0.2, -0.3, -0.25), command=self.requestNext)
        self.bPrev = DirectButton(self, image=(gui.find('**/Horiz_Arrow_UP'),
         gui.find('**/Horiz_Arrow_DN'),
         gui.find('**/Horiz_Arrow_Rllvr'),
         gui.find('**/Horiz_Arrow_UP')), image3_color=Vec4(1, 1, 1, 0.5), image_scale=(-1.0, 1.0, 1.0), relief=None, text=TTLocalizer.PetTutorialPrev, text3_fg=Vec4(0, 0, 0, 0.5), text_scale=0.05, text_pos=(0.0, -0.1), pos=(-0.2, -0.3, -0.25), command=self.requestPrev)
        self.bQuit = DirectButton(self, image=(buttons.find('**/ChtBx_OKBtn_UP'), buttons.find('**/ChtBx_OKBtn_DN'), buttons.find('**/ChtBx_OKBtn_Rllvr')), relief=None, text=TTLocalizer.PetTutorialDone, text_scale=0.05, text_pos=(0.0, -0.1), pos=(0.55, -0.3, -0.25), command=self.__handleQuit)
        self.bQuit.hide()
        buttons.removeNode()
        gui.removeNode()
        self.request('Page1')
        return

    def enterPage1(self, *args):
        self.title['text'] = (TTLocalizer.PetTutorialTitle1,)
        self['text'] = TTLocalizer.PetTutorialPage1
        self['text_pos'] = TTLocalizer.PTenterPage1Pos
        self['text_wordwrap'] = 16.5
        self.bPrev['state'] = DGG.DISABLED
        self.iPage1.show()

    def exitPage1(self, *args):
        self.bPrev['state'] = DGG.NORMAL
        self.iPage1.hide()

    def enterPage2(self, *args):
        self.title['text'] = (TTLocalizer.PetTutorialTitle2,)
        self['text'] = TTLocalizer.PetTutorialPage2
        self['text_pos'] = TTLocalizer.PTenterPage2Pos
        self['text_wordwrap'] = 13.5
        self.iPage2.show()

    def exitPage2(self, *args):
        self.iPage2.hide()

    def enterPage3(self, *args):
        self.title['text'] = (TTLocalizer.PetTutorialTitle3,)
        self['text'] = TTLocalizer.PetTutorialPage3
        self['text_pos'] = TTLocalizer.PTenterPage3Pos
        self['text_wordwrap'] = 16.5
        self.bQuit.show()
        self.bNext['state'] = DGG.DISABLED
        self.iPage3.show()

    def exitPage3(self, *args):
        self.bNext['state'] = DGG.NORMAL
        self.iPage3.hide()
        self.bQuit.hide()

    def __handleQuit(self):
        base.localAvatar.b_setPetTutorialDone(True)
        messenger.send(self.doneEvent)
