from direct.gui.DirectGui import *
from pandac.PandaModules import *
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from direct.task import Task
from . import FishBase
from . import FishPicker

class FishSellGUI(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('FishGui')

    def __init__(self, doneEvent):
        DirectFrame.__init__(self, relief=None, state='normal', geom=DGG.getDefaultDialogGeom(), geom_color=ToontownGlobals.GlobalDialogColor, geom_scale=(2.0, 1, 1.5), frameSize=(-1, 1, -1, 1), pos=(0, 0, 0), text='', text_wordwrap=26, text_scale=0.06, text_pos=(0, 0.65))
        self.initialiseoptions(FishSellGUI)
        self.doneEvent = doneEvent
        self.picker = FishPicker.FishPicker(self)
        self.picker.load()
        self.picker.setPos(-0.59, 0, 0.03)
        self.picker.setScale(0.93)
        newTankFish = base.localAvatar.fishTank.getFish()
        self.picker.update(newTankFish)
        self.picker.show()
        buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
        okImageList = (buttons.find('**/ChtBx_OKBtn_UP'), buttons.find('**/ChtBx_OKBtn_DN'), buttons.find('**/ChtBx_OKBtn_Rllvr'))
        cancelImageList = (buttons.find('**/CloseBtn_UP'), buttons.find('**/CloseBtn_DN'), buttons.find('**/CloseBtn_Rllvr'))
        self.cancelButton = DirectButton(parent=self, relief=None, image=cancelImageList, pos=(0.3, 0, -0.58), text=TTLocalizer.FishGuiCancel, text_scale=TTLocalizer.FSGUIcancelButton, text_pos=(0, -0.1), command=self.__cancel)
        self.okButton = DirectButton(parent=self, relief=None, image=okImageList, pos=(0.6, 0, -0.58), text=TTLocalizer.FishGuiOk, text_scale=TTLocalizer.FSGUIokButton, text_pos=(0, -0.1), command=self.__sellFish)
        self.rewardDoubledJellybeanLabel = DirectLabel(text='', text_fg=(1.0, 0.125, 0.125, 1.0), relief=None, pos=(0.45, 0, -0.48), scale=0.07)
        buttons.removeNode()
        self.__updateFishValue()
        return

    def destroy(self):
        DirectFrame.destroy(self)
        self.rewardDoubledJellybeanLabel.removeNode()
        del self.rewardDoubledJellybeanLabel

    def __cancel(self):
        messenger.send(self.doneEvent, [0])

    def __sellFish(self):
        messenger.send(self.doneEvent, [1])

    def __updateFishValue(self):
        doubledJellybean = ''
        if base.cr.newsManager.isHolidayRunning(ToontownGlobals.JELLYBEAN_FISHING_HOLIDAY) or base.cr.newsManager.isHolidayRunning(ToontownGlobals.JELLYBEAN_FISHING_HOLIDAY_MONTH):
            doubledJellybean = TTLocalizer.PartyRewardDoubledJellybean
            self.rewardDoubledJellybeanLabel['text'] = doubledJellybean
            self.rewardDoubledJellybeanLabel.setText()
        fishTank = base.localAvatar.getFishTank()
        num = len(fishTank)
        value = fishTank.getTotalValue()
        self['text'] = TTLocalizer.FishTankValue % {'name': base.localAvatar.getName(),
         'num': num,
         'value': value}
        self.setText()
