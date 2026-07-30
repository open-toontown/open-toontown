from direct.gui.DirectGui import *
from direct.fsm import FSM
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from panda3d.core import *

class GardenTutorial(DirectFrame, FSM.FSM):
    notify = DirectNotifyGlobal.directNotify.newCategory('GardenTutorial')

    def __init__(self, doneEvent = None, callback = None):
        FSM.FSM.__init__(self, 'GardenTutorial')
        self.doneEvent = doneEvent
        self.callback = callback
        self.setStateArray(['Page1',
         'Page2',
         'Page3',
         'Page4',
         'Page5'])
        DirectFrame.__init__(self, pos=(0.0, 0.0, 0.0), image_color=ToontownGlobals.GlobalDialogColor, image_scale=(1.5, 1.5, 0.9), text='', text_scale=0.06)
        self['image'] = DGG.getDefaultDialogGeom()
        self.title = DirectLabel(self, relief=None, text='', text_pos=(0.0, 0.32), text_fg=(1, 0, 0, 1), text_scale=0.13, text_font=ToontownGlobals.getSignFont())
        images = loader.loadModel('phase_5.5/models/estate/gardenTutorialPages')
        self.iPage1 = DirectFrame(self, image=images.find('**/GardenTutorialPage1'), scale=0.35, pos=(-0.51, -0.1, 0.05))
        self.iPage1.hide()
        self.iPage2 = DirectFrame(self, image=images.find('**/GardenTutorialPage2'), scale=1.25, pos=(0.43, -0.1, 0.05))
        self.iPage2.hide()
        self.iPage3 = DirectFrame(self, image=images.find('**/GardenTutorialPage3'), scale=0.5, pos=(-0.52, -0.1, 0.02))
        self.iPage3.hide()
        self.iPage4 = DirectFrame(self, image=images.find('**/GardenTutorialPage4'), scale=0.75, pos=(0, -0.1, -0.05))
        self.iPage4.hide()
        self.iPage5 = DirectFrame(self, image=images.find('**/GardenTutorialPage5'), scale=0.7, pos=(-0.51, -0.1, 0.05))
        self.iPage5.hide()
        buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
        gui = loader.loadModel('phase_3.5/models/gui/friendslist_gui')
        self.bNext = DirectButton(self, image=(gui.find('**/Horiz_Arrow_UP'),
         gui.find('**/Horiz_Arrow_DN'),
         gui.find('**/Horiz_Arrow_Rllvr'),
         gui.find('**/Horiz_Arrow_UP')), image3_color=Vec4(1, 1, 1, 0.5), relief=None, text=TTLocalizer.GardenTutorialNext, text3_fg=Vec4(0, 0, 0, 0.5), text_scale=0.05, text_pos=(0.0, -0.1), pos=(0.2, -0.3, -0.25), command=self.requestNext)
        self.bPrev = DirectButton(self, image=(gui.find('**/Horiz_Arrow_UP'),
         gui.find('**/Horiz_Arrow_DN'),
         gui.find('**/Horiz_Arrow_Rllvr'),
         gui.find('**/Horiz_Arrow_UP')), image3_color=Vec4(1, 1, 1, 0.5), image_scale=(-1.0, 1.0, 1.0), relief=None, text=TTLocalizer.GardenTutorialPrev, text3_fg=Vec4(0, 0, 0, 0.5), text_scale=0.05, text_pos=(0.0, -0.1), pos=(-0.2, -0.3, -0.25), command=self.requestPrev)
        self.bQuit = DirectButton(self, image=(buttons.find('**/ChtBx_OKBtn_UP'), buttons.find('**/ChtBx_OKBtn_DN'), buttons.find('**/ChtBx_OKBtn_Rllvr')), relief=None, text=TTLocalizer.GardenTutorialDone, text_scale=0.05, text_pos=(0.0, -0.1), pos=(0.55, -0.3, -0.25), command=self.__handleQuit)
        self.bQuit.hide()
        buttons.removeNode()
        gui.removeNode()
        self.notify.debug('garden tutorial detectedGardenPlotUse')
        base.cr.playGame.getPlace().detectedGardenPlotUse()
        curState = base.cr.playGame.getPlace().getState()
        self.notify.debug('Estate.getState() == %s' % curState)
        self.request('Page1')
        return

    def enterPage1(self, *args):
        self.title['text'] = (TTLocalizer.GardenTutorialTitle1,)
        self['text'] = TTLocalizer.GardenTutorialPage1
        self['text_pos'] = (0.15, 0.13)
        self['text_wordwrap'] = 16.5
        self.bPrev['state'] = DGG.DISABLED
        self.iPage1.show()

    def exitPage1(self, *args):
        self.bPrev['state'] = DGG.NORMAL
        self.iPage1.hide()

    def enterPage2(self, *args):
        self.title['text'] = (TTLocalizer.GardenTutorialTitle2,)
        self['text'] = TTLocalizer.GardenTutorialPage2
        self['text_pos'] = (-0.27, 0.16)
        self['text_wordwrap'] = TTLocalizer.GTenterPage2Wordwrap
        self.iPage2.show()

    def exitPage2(self, *args):
        self.iPage2.hide()

    def enterPage3(self, *args):
        self.title['text'] = (TTLocalizer.GardenTutorialTitle3,)
        self['text'] = TTLocalizer.GardenTutorialPage3
        self['text_pos'] = (0.15, 0.13)
        self['text_wordwrap'] = 16.5
        self.iPage3.show()

    def exitPage3(self, *args):
        self.iPage3.hide()

    def enterPage4(self, *args):
        self.title['text'] = (TTLocalizer.GardenTutorialTitle4,)
        self['text'] = TTLocalizer.GardenTutorialPage4
        self['text_pos'] = (0.0, 0.19)
        self['text_wordwrap'] = TTLocalizer.GTenterPage4Wordwrap
        self.iPage4.show()

    def exitPage4(self, *args):
        self.iPage4.hide()

    def enterPage5(self, *args):
        self.title['text'] = (TTLocalizer.GardenTutorialTitle5,)
        self['text'] = TTLocalizer.GardenTutorialPage5
        self['text_pos'] = (0.15, 0.13)
        self['text_wordwrap'] = 16.5
        self.bQuit.show()
        self.bNext['state'] = DGG.DISABLED
        self.iPage5.show()

    def exitPage5(self, *args):
        self.bNext['state'] = DGG.NORMAL
        self.iPage5.hide()
        self.bQuit.hide()

    def __handleQuit(self):
        self.notify.debug('garden tutorial detectedGardenPlotDone')
        base.cr.playGame.getPlace().detectedGardenPlotDone()
        if self.callback:
            self.callback()
        else:
            messenger.send(self.doneEvent)
