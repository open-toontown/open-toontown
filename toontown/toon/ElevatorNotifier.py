from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from direct.gui.DirectGui import *
from panda3d.core import *
from toontown.toontowngui import TTDialog

class ElevatorNotifier:
    notify = DirectNotifyGlobal.directNotify.newCategory('CatalogNotifyDialog')

    def __init__(self):
        self.frame = None
        return

    def handleButton(self):
        self.__handleButton(1)

    def createFrame(self, message, framePos = None, withStopping = True, ttDialog = False):
        if not framePos:
            framePos = (0.0, 0, 0.78)
        if not ttDialog:
            self.frame = DirectFrame(relief=None, image=DGG.getDefaultDialogGeom(), image_color=ToontownGlobals.GlobalDialogColor, image_scale=(1.0, 1.0, 0.4), text=message, text_wordwrap=16, text_scale=0.06, text_pos=(-0.0, 0.1), pos=framePos)
        else:
            self.frame = TTDialog.TTDialog(relief=None, image=DGG.getDefaultDialogGeom(), image_color=ToontownGlobals.GlobalDialogColor, image_scale=(1.0, 1.0, 0.4), text=message, text_wordwrap=16, text_scale=0.06, text_pos=(-0.0, 0.1), pos=framePos)
        buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
        self.cancelImageList = (buttons.find('**/CloseBtn_UP'), buttons.find('**/CloseBtn_DN'), buttons.find('**/CloseBtn_Rllvr'))
        self.okImageList = (buttons.find('**/ChtBx_OKBtn_UP'), buttons.find('**/ChtBx_OKBtn_DN'), buttons.find('**/ChtBx_OKBtn_Rllvr'))
        self.doneButton = DirectButton(parent=self.frame, relief=None, image=self.cancelImageList, command=self.handleButton, pos=(0, 0, -0.14))
        if not withStopping:
            self.doneButton['command'] = self.__handleButtonWithoutStopping
        self.doneButton.show()
        self.frame.show()
        return

    def cleanup(self):
        if self.frame:
            self.frame.destroy()
        self.frame = None
        self.nextButton = None
        self.doneButton = None
        self.okImageList = None
        self.cancelImageList = None
        return

    def setOkButton(self):
        self.doneButton['image'] = self.okImageList

    def setCancelButton(self):
        self.doneButton['image'] = self.cancelImageList

    def __handleButton(self, value):
        self.cleanup()
        place = base.cr.playGame.getPlace()
        if place:
            place.setState('walk')

    def showMe(self, message, pos = None, ttDialog = False):
        if self.frame == None:
            place = base.cr.playGame.getPlace()
            if place:
                self.createFrame(message, pos, True, ttDialog)
                place.setState('stopped')
        return

    def showMeWithoutStopping(self, message, pos = None, ttDialog = False):
        if self.frame == None:
            self.createFrame(message, pos, False, ttDialog)
        return

    def __handleButtonWithoutStopping(self):
        self.cleanup()

    def isNotifierOpen(self):
        if self.frame:
            return True
        else:
            return False
