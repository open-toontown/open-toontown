from toontown.toonbase import ToontownGlobals
from direct.directnotify import DirectNotifyGlobal
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from toontown.toonbase import TTLocalizer
import FishPanel

class FishPicker(DirectScrolledList):
    notify = DirectNotifyGlobal.directNotify.newCategory('FishPicker')

    def __init__(self, parent = aspect2d, **kw):
        self.fishList = []
        self.parent = parent
        self.shown = 0
        gui = loader.loadModel('phase_3.5/models/gui/friendslist_gui')
        optiondefs = (('parent', self.parent, None),
         ('relief', None, None),
         ('incButton_image', (gui.find('**/FndsLst_ScrollUp'),
           gui.find('**/FndsLst_ScrollDN'),
           gui.find('**/FndsLst_ScrollUp_Rllvr'),
           gui.find('**/FndsLst_ScrollUp')), None),
         ('incButton_relief', None, None),
         ('incButton_scale', (1.6, 1.6, -1.6), None),
         ('incButton_pos', (0.16, 0, -0.47), None),
         ('incButton_image3_color', Vec4(0.7, 0.7, 0.7, 0.75), None),
         ('decButton_image', (gui.find('**/FndsLst_ScrollUp'),
           gui.find('**/FndsLst_ScrollDN'),
           gui.find('**/FndsLst_ScrollUp_Rllvr'),
           gui.find('**/FndsLst_ScrollUp')), None),
         ('decButton_relief', None, None),
         ('decButton_scale', (1.6, 1.6, 1.6), None),
         ('decButton_pos', (0.16, 0, 0.09), None),
         ('decButton_image3_color', Vec4(0.7, 0.7, 0.7, 0.75), None),
         ('itemFrame_pos', (-0.025, 0, 0), None),
         ('itemFrame_scale', 0.54, None),
         ('itemFrame_relief', None, None),
         ('itemFrame_frameSize', (-0.05,
           0.75,
           -0.75,
           0.05), None),
         ('numItemsVisible', 10, None),
         ('items', [], None))
        self.defineoptions(kw, optiondefs)
        DirectScrolledList.__init__(self, parent)
        self.initialiseoptions(FishPicker)
        self.fishGui = loader.loadModel('phase_3.5/models/gui/fishingBook').find('**/bucket')
        self.fishGui.find('**/fram1').removeNode()
        self.fishGui.find('**/bubble').removeNode()
        self.fishGui.reparentTo(self, -1)
        self.fishGui.setPos(0.63, 0.1, -0.1)
        self.fishGui.setScale(0.035)
        self.info = DirectLabel(parent=self, relief=None, text='', text_scale=0.055, pos=(0.18, 0, -0.67))
        self.fishPanel = FishPanel.FishPanel(parent=self)
        self.fishPanel.setSwimBounds(-0.3, 0.3, -0.235, 0.25)
        self.fishPanel.setSwimColor(1.0, 1.0, 0.74901, 1.0)
        gui.removeNode()
        return None

    def destroy(self):
        DirectScrolledList.destroy(self)
        self.parent = None
        self.fishList = []
        self.fishPanel = None
        return

    def hideFishPanel(self):
        self.fishPanel.hide()

    def hide(self):
        if not hasattr(self, 'loaded'):
            return
        self.hideFishPanel()
        DirectScrolledList.hide(self)
        self.shown = 0

    def show(self):
        if not hasattr(self, 'loaded'):
            self.load()
        self.updatePanel()
        DirectScrolledList.show(self)
        self.shown = 1

    def load(self):
        self.loaded = 1
        self.fishPanel.load()
        self.fishPanel.setPos(1.05, 0, 0.1)
        self.fishPanel.setScale(0.9)

    def update(self, newFishes):
        for fish, fishButton in self.fishList[:]:
            self.removeItem(fishButton)
            fishButton.destroy()
            self.fishList.remove([fish, fishButton])

        for fish in newFishes:
            fishButton = self.makeFishButton(fish)
            self.addItem(fishButton)
            self.fishList.append([fish, fishButton])

        value = 0
        for fish in newFishes:
            value += fish.getValue()

        maxFish = base.localAvatar.getMaxFishTank()
        self.info['text'] = TTLocalizer.FishPickerTotalValue % (len(newFishes), maxFish, value)
        if self.shown:
            self.updatePanel()

    def updatePanel(self):
        if len(self.fishList) >= 1:
            self.showFishPanel(self.fishList[0][0])
        else:
            self.hideFishPanel()

    def makeFishButton(self, fish):
        return DirectScrolledListItem(parent=self, relief=None, text=fish.getSpeciesName(), text_scale=0.07, text_align=TextNode.ALeft, text1_fg=Vec4(1, 1, 0, 1), text2_fg=Vec4(0.5, 0.9, 1, 1), text3_fg=Vec4(0.4, 0.8, 0.4, 1), command=self.showFishPanel, extraArgs=[fish])

    def showFishPanel(self, fish):
        self.fishPanel.update(fish)
        self.fishPanel.show()
