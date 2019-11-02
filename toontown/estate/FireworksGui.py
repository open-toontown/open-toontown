from direct.gui.DirectGui import *
from pandac.PandaModules import *
from direct.gui.DirectScrolledList import *
from toontown.toonbase import ToontownGlobals
import FireworkItemPanel
from direct.directnotify import DirectNotifyGlobal
from toontown.effects import FireworkGlobals
from toontown.effects import Fireworks
NUM_ITEMS_SHOWN = 4

class FireworksGui(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('FireworksGui')

    def __init__(self, doneEvent, shootEvent):
        DirectFrame.__init__(self, relief=None, geom=DGG.getDefaultDialogGeom(), geom_color=(0, 0.5, 1, 1), geom_scale=(0.43, 1, 1.4), pos=(1.1, 0, 0))
        self.initialiseoptions(FireworksGui)
        self.doneEvent = doneEvent
        self.shootEvent = shootEvent
        self.itemList = []
        self.type = None
        self.load()
        return

    def load(self):
        itemTypes = [0,
         1,
         2,
         3,
         4,
         5]
        itemStrings = []
        for i in itemTypes:
            itemStrings.append(FireworkGlobals.Names[i])

        gui = loader.loadModel('phase_3.5/models/gui/friendslist_gui')
        self.panelPicker = DirectScrolledList(parent=self, items=itemStrings, command=self.scrollItem, itemMakeFunction=FireworkItemPanel.FireworkItemPanel, itemMakeExtraArgs=[self, itemTypes, self.shootEvent], numItemsVisible=NUM_ITEMS_SHOWN, incButton_image=(gui.find('**/FndsLst_ScrollUp'),
         gui.find('**/FndsLst_ScrollDN'),
         gui.find('**/FndsLst_ScrollUp_Rllvr'),
         gui.find('**/FndsLst_ScrollUp')), incButton_relief=None, incButton_scale=(0.5, 1, -1), incButton_pos=(0, 0, -1.08), incButton_image3_color=Vec4(1, 1, 1, 0.3), decButton_image=(gui.find('**/FndsLst_ScrollUp'),
         gui.find('**/FndsLst_ScrollDN'),
         gui.find('**/FndsLst_ScrollUp_Rllvr'),
         gui.find('**/FndsLst_ScrollUp')), decButton_relief=None, decButton_scale=(0.5, 1, 1), decButton_pos=(0, 0, 0.2), decButton_image3_color=Vec4(1, 1, 1, 0.3))
        self.panelPicker.setPos(-.06, 0, 0.42)
        buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
        cancelImageList = (buttons.find('**/CloseBtn_UP'), buttons.find('**/CloseBtn_DN'), buttons.find('**/CloseBtn_Rllvr'))
        self.cancelButton = DirectButton(parent=self, relief=None, image=cancelImageList, pos=(0.15, 0, -0.62), text_scale=0.06, text_pos=(0, -0.1), command=self.__cancel)
        buttons.removeNode()
        self.hilightColor = VBase4(1, 1, 1, 1)
        self.bgColor = VBase4(0.8, 0.8, 0.8, 1)
        self.colorButtons = []
        for i in Fireworks.colors.keys():
            color = Fireworks.colors[i]
            height = 0.07
            paddedHeight = 0.1
            buttonBg = DirectFrame(self, geom=DGG.getDefaultDialogGeom(), geom_scale=paddedHeight, geom_color=self.bgColor, pos=(0.15, 0, 0.5 - (paddedHeight + 0.025) * i), relief=None)
            self.initialiseoptions(buttonBg)
            button = DirectButton(buttonBg, image=(DGG.getDefaultDialogGeom(), DGG.getDefaultDialogGeom(), DGG.getDefaultDialogGeom()), relief=None, command=self.__handleColor, extraArgs=[i])
            button.setScale(height)
            button.setColor(color)
            self.colorButtons.append([button, buttonBg])

        self.__initColor(0)
        return

    def unload(self):
        del self.parent
        del self.itemList
        del self.panelPicker

    def update(self):
        pass

    def __cancel(self):
        messenger.send(self.doneEvent)

    def __initColor(self, index):
        self.colorButtons[index][1]['geom_color'] = self.hilightColor
        self.colorButtons[index][1].setScale(1.2)
        self.curColor = index
        self.fadeColor = 0

    def __handleColor(self, index):
        color = Fireworks.colors[index]
        for i in range(len(self.colorButtons)):
            self.colorButtons[i][1]['geom_color'] = self.bgColor
            self.colorButtons[i][1].setScale(1)

        self.colorButtons[index][1].setScale(1.2)
        if index == self.curColor:
            self.fadeColor = (self.fadeColor + 1) % len(Fireworks.colors)
        else:
            self.fadeColor = 0
        self.colorButtons[index][1]['geom_color'] = Fireworks.colors[self.fadeColor]
        self.curColor = index

    def scrollItem(self):
        pass

    def getCurColor(self):
        return (self.curColor, self.fadeColor)
