from direct.directnotify import DirectNotifyGlobal
from . import ShtikerPage
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from toontown.toonbase import TTLocalizer
from toontown.estate import FlowerBrowser
from toontown.estate import GardenGlobals
from toontown.estate import FlowerPicker
from toontown.estate import SpecialsPhoto
from toontown.toontowngui import TTDialog
GardenPage_Basket = 0
GardenPage_Collection = 1
GardenPage_Trophy = 2
GardenPage_Specials = 3
TROPHIES_PER_ROW = 5

class GardenPage(ShtikerPage.ShtikerPage):
    notify = DirectNotifyGlobal.directNotify.newCategory('GardenPage')

    def __init__(self):
        self.notify.debug('__init__')
        ShtikerPage.ShtikerPage.__init__(self)
        self.mode = GardenPage_Basket
        self.accept('use-special-response', self.useSpecialDone)
        self.resultDialog = None
        return

    def enter(self):
        self.notify.debug('enter')
        if not hasattr(self, 'title'):
            self.load()
        self.setMode(self.mode, 1)
        self.accept(localAvatar.uniqueName('flowerBasketChange'), self.updatePage)
        ShtikerPage.ShtikerPage.enter(self)

    def exit(self):
        self.notify.debug('exit')
        if hasattr(self, 'picker'):
            self.picker.hide()
        if hasattr(self, 'browser'):
            self.browser.hide()
        if hasattr(self, 'specialsFrame'):
            self.specialsFrame.hide()
        if hasattr(self, 'specialsPhoto'):
            self.specialsPhoto.hide()
        if hasattr(self, 'useSpecialButton'):
            self.hide()
        self.cleanupResultDialog()
        ShtikerPage.ShtikerPage.exit(self)

    def load(self):
        self.notify.debug('load')
        ShtikerPage.ShtikerPage.load(self)
        gui = loader.loadModel('phase_3.5/models/gui/fishingBook')
        trophyCase = gui.find('**/trophyCase1')
        trophyCase.find('glass1').reparentTo(trophyCase, -1)
        trophyCase.find('shelf').reparentTo(trophyCase, -1)
        self.trophyCase = trophyCase
        self.title = DirectLabel(parent=self, relief=None, text='', text_scale=0.1, pos=(0, 0, 0.65))
        normalColor = (1, 1, 1, 1)
        clickColor = (0.8, 0.8, 0, 1)
        rolloverColor = (0.15, 0.82, 1.0, 1)
        diabledColor = (1.0, 0.98, 0.15, 1)
        self.basketTab = DirectButton(parent=self, relief=None, text=TTLocalizer.GardenPageBasketTab, text_scale=TTLocalizer.GPbasketTab, text_align=TextNode.ALeft, image=gui.find('**/tabs/polySurface1'), image_pos=(0.55, 1, -0.91), image_hpr=(0, 0, -90), image_scale=(0.033, 0.033, 0.035), image_color=normalColor, image1_color=clickColor, image2_color=rolloverColor, image3_color=diabledColor, text_fg=Vec4(0.2, 0.1, 0, 1), command=self.setMode, extraArgs=[GardenPage_Basket], pos=(0.92, 0, 0.55))
        self.collectionTab = DirectButton(parent=self, relief=None, text=TTLocalizer.GardenPageCollectionTab, text_scale=TTLocalizer.GPcollectionTab, text_align=TextNode.ALeft, image=gui.find('**/tabs/polySurface2'), image_pos=(0.12, 1, -0.91), image_hpr=(0, 0, -90), image_scale=(0.033, 0.033, 0.035), image_color=normalColor, image1_color=clickColor, image2_color=rolloverColor, image3_color=diabledColor, text_fg=Vec4(0.2, 0.1, 0, 1), command=self.setMode, extraArgs=[GardenPage_Collection], pos=(0.92, 0, 0.1))
        self.trophyTab = DirectButton(parent=self, relief=None, text=TTLocalizer.GardenPageTrophyTab, text_scale=TTLocalizer.GPtrophyTab, text_align=TextNode.ALeft, image=gui.find('**/tabs/polySurface3'), image_pos=(-0.28, 1, -0.91), image_hpr=(0, 0, -90), image_scale=(0.033, 0.033, 0.035), image_color=normalColor, image1_color=clickColor, image2_color=rolloverColor, image3_color=diabledColor, text_fg=Vec4(0.2, 0.1, 0, 1), command=self.setMode, extraArgs=[GardenPage_Trophy], pos=(0.92, 0, -0.3))
        self.specialsTab = DirectButton(parent=self, relief=None, text=TTLocalizer.GardenPageSpecialsTab, text_scale=TTLocalizer.GPspecialsTab, text_align=TextNode.ALeft, image=gui.find('**/tabs/polySurface3'), image_pos=(-0.28, 1, -0.91), image_hpr=(0, 0, -90), image_scale=(0.033, 0.033, 0.035), image_color=normalColor, image1_color=clickColor, image2_color=rolloverColor, image3_color=diabledColor, text_fg=Vec4(0.2, 0.1, 0, 1), command=self.setMode, extraArgs=[GardenPage_Specials], pos=(0.92, 0, -0.3))
        self.basketTab.setPos(-0.75, 0, 0.775)
        self.collectionTab.setPos(-0.33, 0, 0.775)
        self.trophyTab.setPos(0.09, 0, 0.775)
        self.specialsTab.setPos(0.51, 0, 0.775)
        gui = loader.loadModel('phase_3.5/models/gui/friendslist_gui')
        self.gardenSpecialsList = DirectScrolledList(parent=self, relief=None, incButton_image=(gui.find('**/FndsLst_ScrollUp'),
         gui.find('**/FndsLst_ScrollDN'),
         gui.find('**/FndsLst_ScrollUp_Rllvr'),
         gui.find('**/FndsLst_ScrollUp')), incButton_relief=None, incButton_pos=(0.0, 0.0, -1.1), incButton_image1_color=Vec4(1.0, 0.9, 0.4, 1.0), incButton_image3_color=Vec4(1.0, 1.0, 0.6, 0.5), incButton_scale=(1.0, 1.0, -1.0), decButton_image=(gui.find('**/FndsLst_ScrollUp'),
         gui.find('**/FndsLst_ScrollDN'),
         gui.find('**/FndsLst_ScrollUp_Rllvr'),
         gui.find('**/FndsLst_ScrollUp')), decButton_relief=None, decButton_pos=(0.0, 0.0, 0.117), decButton_image1_color=Vec4(1.0, 1.0, 0.6, 1.0), decButton_image3_color=Vec4(1.0, 1.0, 0.6, 0.6), itemFrame_pos=(-0.2, 0.0, 0.05), itemFrame_relief=None, numItemsVisible=18, items=[], pos=(-0.6, 0, 0.45))
        self.gardenSpecialsList.hide()
        self.specialsFrame = DirectFrame(parent=self, relief=None, pos=(0.45, 0.0, 0.25), text='', text_wordwrap=14.4, text_pos=(0, -0.46), text_scale=0.06)
        self.specialsInfo = DirectLabel(parent=self.specialsFrame, relief=None, pos=(0.0, 0.0, -0.0), text=' ', text_wordwrap=12.4, text_pos=(0, -0.46), text_scale=0.06)
        self.specialsPhoto = SpecialsPhoto.SpecialsPhoto(-1, parent=self.specialsFrame)
        self.specialsPhoto.setBackBounds(-0.3, 0.3, -0.235, 0.25)
        self.specialsPhoto.setBackColor(1.0, 1.0, 0.74901, 1.0)
        buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
        okImageList = (buttons.find('**/ChtBx_OKBtn_UP'), buttons.find('**/ChtBx_OKBtn_DN'), buttons.find('**/ChtBx_OKBtn_Rllvr'))
        self.useSpecialButton = DirectButton(parent=self, relief=None, image=okImageList, pos=(0.45, 0, -0.5), text=TTLocalizer.UseSpecial, text_scale=0.06, text_pos=(0, -0.1), command=self.__useSpecial)
        buttons.removeNode()
        return

    def setMode(self, mode, updateAnyways = 0):
        messenger.send('wakeup')
        if not updateAnyways:
            if self.mode == mode:
                return
            else:
                self.mode = mode
        self.gardenSpecialsList.hide()
        self.specialsPhoto.hide()
        self.specialsFrame.hide()
        self.useSpecialButton.hide()
        if mode == GardenPage_Basket:
            self.title['text'] = TTLocalizer.GardenPageTitleBasket
            if not hasattr(self, 'picker'):
                self.createFlowerPicker()
            self.picker.show()
            if hasattr(self, 'browser'):
                self.browser.hide()
            if hasattr(self, 'trophyFrame'):
                self.trophyFrame.hide()
            self.basketTab['state'] = DGG.DISABLED
            self.collectionTab['state'] = DGG.NORMAL
            self.trophyTab['state'] = DGG.NORMAL
            self.specialsTab['state'] = DGG.NORMAL
        elif mode == GardenPage_Collection:
            self.title['text'] = TTLocalizer.GardenPageTitleCollection
            if hasattr(self, 'picker'):
                self.picker.hide()
            if not hasattr(self, 'browser'):
                self.createAlbumBrowser()
            self.browser.show()
            if hasattr(self, 'trophyFrame'):
                self.trophyFrame.hide()
            self.basketTab['state'] = DGG.NORMAL
            self.collectionTab['state'] = DGG.DISABLED
            self.trophyTab['state'] = DGG.NORMAL
            self.specialsTab['state'] = DGG.NORMAL
        elif mode == GardenPage_Trophy:
            self.title['text'] = TTLocalizer.GardenPageTitleTrophy
            if hasattr(self, 'picker'):
                self.picker.hide()
            if hasattr(self, 'browser'):
                self.browser.hide()
            if not hasattr(self, 'trophyFrame'):
                self.createGardenTrophyFrame()
            self.trophyFrame.show()
            self.basketTab['state'] = DGG.NORMAL
            self.collectionTab['state'] = DGG.NORMAL
            self.trophyTab['state'] = DGG.DISABLED
            self.specialsTab['state'] = DGG.NORMAL
        elif mode == GardenPage_Specials:
            self.title['text'] = TTLocalizer.GardenPageTitleSpecials
            if hasattr(self, 'picker'):
                self.picker.hide()
            if hasattr(self, 'browser'):
                self.browser.hide()
            if hasattr(self, 'trophyFrame'):
                self.trophyFrame.hide()
            self.basketTab['state'] = DGG.NORMAL
            self.collectionTab['state'] = DGG.NORMAL
            self.trophyTab['state'] = DGG.NORMAL
            self.specialsTab['state'] = DGG.DISABLED
            self.gardenSpecialsList.show()
            specialsList = localAvatar.getGardenSpecials()
            self.specialsPhoto.show()
            self.specialsFrame.show()
            self.createGardenSpecialsList()
        self.updatePage()

    def createGardenSpecialsList(self):
        self.clearGS()
        self.specialsInfo['text'] = ''
        self.useSpecialButton.hide()
        self.specialsPhoto.hide()
        self.specialsPhoto.update(-1)
        self.specialsPhoto.show()
        specialsList = localAvatar.getGardenSpecials()
        firstEntry = None
        if len(specialsList) == 0:
            self.gardenSpecialsList['incButton_image1_color'] = Vec4(1.0, 0.9, 0.4, 0.0)
            self.gardenSpecialsList['incButton_image3_color'] = Vec4(1.0, 0.9, 0.4, 0.0)
            self.gardenSpecialsList['decButton_image1_color'] = Vec4(1.0, 0.9, 0.4, 0.0)
            self.gardenSpecialsList['decButton_image3_color'] = Vec4(1.0, 0.9, 0.4, 0.0)
        else:
            self.gardenSpecialsList['incButton_image1_color'] = Vec4(1.0, 0.9, 0.4, 1.0)
            self.gardenSpecialsList['incButton_image3_color'] = Vec4(1.0, 0.9, 0.4, 1.0)
            self.gardenSpecialsList['decButton_image1_color'] = Vec4(1.0, 0.9, 0.4, 1.0)
            self.gardenSpecialsList['decButton_image3_color'] = Vec4(1.0, 0.9, 0.4, 1.0)
            for entry in specialsList:
                if not firstEntry:
                    firstEntry = entry
                someItem = DirectScrolledListItem(parent=self.gardenSpecialsList, text='%s x %s' % (GardenGlobals.Specials[entry[0]]['photoName'], entry[1]), text_align=TextNode.ALeft, text_fg=(0.0, 0.0, 0.0, 1), text_bg=(1.0, 1.0, 1, 0), text_scale=0.06, relief=None, command=self.showSpecialsPanel, extraArgs=[entry])
                self.gardenSpecialsList.addItem(someItem)
                self.specialsPhoto.show()

            if firstEntry:
                self.showSpecialsPanel(firstEntry)
        return

    def showSpecialsPanel(self, entry):
        type = entry[0]
        number = entry[1]
        self.specialsPhoto.hide()
        self.specialsPhoto.update(type)
        self.specialsPhoto.show()
        self.specialsInfo['text'] = GardenGlobals.Specials[entry[0]]['description']
        self.selectedSpecial = type
        specialInfo = GardenGlobals.Specials[entry[0]]
        if 'useFromShtiker' in specialInfo and specialInfo['useFromShtiker']:
            self.useSpecialButton.show()
        else:
            self.useSpecialButton.hide()

    def __useSpecial(self):
        self.useSpecialButton['state'] = DGG.DISABLED
        localAvatar.sendUpdate('reqUseSpecial', [self.selectedSpecial])

    def clearGS(self):
        while len(self.gardenSpecialsList['items']) > 0:
            for item in self.gardenSpecialsList['items']:
                self.gardenSpecialsList.removeItem(item, 1)
                if hasattr(item, 'destroy'):
                    item.destroy()
                if hasattr(item, 'delete'):
                    item.delete()
                del item

    def createAlbumBrowser(self):
        if not hasattr(self, 'browser'):
            self.browser = FlowerBrowser.FlowerBrowser(self)
            self.browser.setScale(1.1)
            self.collectedTotal = DirectLabel(parent=self.browser, relief=None, text='', text_scale=0.06, pos=(0, 0, -0.61))
        return

    def createGardenTrophyFrame(self):
        if not hasattr(self, 'trophyFrame'):
            self.trophyFrame = DirectFrame(parent=self, relief=None, image=self.trophyCase, image_pos=(0, 1, 0), image_scale=0.034)
            self.trophyFrame.hide()
            self.trophies = []
            hOffset = -0.5
            vOffset = 0.4
            for level, trophyDesc in list(GardenGlobals.TrophyDict.items()):
                trophy = GardenTrophy(-1)
                trophy.nameLabel['text'] = trophyDesc[0]
                trophy.reparentTo(self.trophyFrame)
                trophy.setScale(0.36)
                if level % TROPHIES_PER_ROW == 0:
                    hOffset = -0.5
                    vOffset -= 0.4
                trophy.setPos(hOffset, 0, vOffset)
                hOffset += 0.25
                self.trophies.append(trophy)

        return

    def createFlowerPicker(self):
        if not hasattr(self, 'picker'):
            self.picker = FlowerPicker.FlowerPicker(self)
            self.picker.setPos(-0.555, 0, 0.1)
            self.picker.setScale(0.95)
            self.FUDGE_FACTOR = 0.01
            self.barLength = 1.1
            self.shovelBar = DirectWaitBar(parent=self.picker, pos=(0.95, 0, -0.55), relief=DGG.SUNKEN, frameSize=(-0.65,
             1.05,
             -0.1,
             0.1), borderWidth=(0.025, 0.025), scale=0.45, frameColor=(0.8, 0.8, 0.7, 1), barColor=(0.6, 0.4, 0.2, 1), range=self.barLength + self.FUDGE_FACTOR, value=self.barLength * 0.5 + self.FUDGE_FACTOR, text=' ' + TTLocalizer.Laff, text_scale=0.11, text_fg=(0.05, 0.14, 0.2, 1), text_align=TextNode.ALeft, text_pos=(-0.57, -0.035))
            self.wateringCanBar = DirectWaitBar(parent=self.picker, pos=(0.95, 0, -0.75), relief=DGG.SUNKEN, frameSize=(-0.65,
             1.05,
             -0.1,
             0.1), borderWidth=(0.025, 0.025), scale=0.45, frameColor=(0.8, 0.8, 0.7, 1), barColor=(0.4, 0.6, 1.0, 1), range=self.barLength + self.FUDGE_FACTOR, value=self.barLength * 0.5 + self.FUDGE_FACTOR, text=' ' + TTLocalizer.Laff, text_scale=0.11, text_fg=(0.05, 0.14, 0.2, 1), text_align=TextNode.ALeft, text_pos=(-0.57, -0.035))

    def unload(self):
        print('gardenPage Unloading')
        if hasattr(self, 'specialsPhoto'):
            del self.specialsPhoto
        if hasattr(self, 'trophies'):
            del self.trophies
        if hasattr(self, 'trophyCase'):
            del self.trophyCase
        if hasattr(self, 'useSpecialButton'):
            self.useSpecialButton.destroy()
            del self.useSpecialButton
        self.cleanupResultDialog()
        self.gardenSpecialsList.destroy()
        self.basketTab.destroy()
        self.collectionTab.destroy()
        self.trophyTab.destroy()
        self.specialsTab.destroy()
        ShtikerPage.ShtikerPage.unload(self)

    def updatePage(self):
        if hasattr(self, 'collectedTotal'):
            self.collectedTotal['text'] = TTLocalizer.GardenPageCollectedTotal % (len(base.localAvatar.flowerCollection), GardenGlobals.getNumberOfFlowerVarieties())
        if hasattr(self, 'shovelBar'):
            shovel = base.localAvatar.shovel
            shovelName = TTLocalizer.ShovelNameDict[shovel]
            curShovelSkill = base.localAvatar.shovelSkill
            maxShovelSkill = GardenGlobals.ShovelAttributes[shovel]['skillPts']
            if shovel == GardenGlobals.MAX_SHOVELS - 1:
                maxShovelSkill -= 1
            wateringCan = base.localAvatar.wateringCan
            wateringCanName = TTLocalizer.WateringCanNameDict[wateringCan]
            curWateringCanSkill = base.localAvatar.wateringCanSkill
            maxWateringCanSkill = GardenGlobals.WateringCanAttributes[wateringCan]['skillPts']
            if wateringCan == GardenGlobals.MAX_WATERING_CANS - 1:
                maxWateringCanSkill -= 1
            textToUse = TTLocalizer.GardenPageShovelInfo % (shovelName, curShovelSkill, maxShovelSkill)
            self.shovelBar['text'] = textToUse
            self.shovelBar['value'] = float(curShovelSkill) / float(maxShovelSkill) * self.barLength + self.FUDGE_FACTOR
            textToUse = TTLocalizer.GardenPageWateringCanInfo % (wateringCanName, curWateringCanSkill, maxWateringCanSkill)
            self.wateringCanBar['text'] = textToUse
            self.wateringCanBar['value'] = float(curWateringCanSkill) / float(maxWateringCanSkill) * self.barLength + self.FUDGE_FACTOR
        else:
            print('no shovel bar')
        if self.mode == GardenPage_Collection:
            if hasattr(self, 'browser'):
                self.browser.update()
        elif self.mode == GardenPage_Basket:
            if hasattr(self, 'picker'):
                newBasketFlower = base.localAvatar.flowerBasket.getFlower()
                self.picker.update(newBasketFlower)
        elif self.mode == GardenPage_Trophy:
            if hasattr(self, 'trophies'):
                for trophy in self.trophies:
                    trophy.setLevel(-1)

                for trophyId in base.localAvatar.getGardenTrophies():
                    self.trophies[trophyId].setLevel(trophyId)

        elif self.mode == GardenPage_Specials:
            self.createGardenSpecialsList()
            if not base.cr.playGame.getPlace().getState() == 'stickerBook':
                self.specialsPhoto.hide()

    def destroy(self):
        self.notify.debug('destroy')
        self.useSpecialButton.destroy()
        if hasattr(self, 'gardenSpecialsList'):
            self.clearGS()
            self.gardenSpecialsList.destroy()
        self.ignoreAll()
        self.cleanupResultDialog()
        DirectFrame.destroy(self)

    def useSpecialDone(self, response):
        stringToShow = ''
        if response == 'success':
            stringToShow = TTLocalizer.UseSpecialSuccess
        elif response == 'badlocation':
            stringToShow = TTLocalizer.UseSpecialBadLocation
        else:
            stringToShow = 'Unknown response %s' % response
        self.resultDialog = TTDialog.TTDialog(parent=aspect2dp, style=TTDialog.Acknowledge, text=stringToShow, command=self.cleanupResultDialog)

    def cleanupResultDialog(self, value = None):
        if self.resultDialog:
            self.resultDialog.destroy()
            self.resultDialog = None
            self.useSpecialButton['state'] = DGG.NORMAL
        return


class GardenTrophy(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('GardenTrophy')

    def __init__(self, level):
        DirectFrame.__init__(self, relief=None)
        self.initialiseoptions(GardenTrophy)
        self.trophy = loader.loadModel('phase_3.5/models/gui/fishingTrophy')
        self.trophy.reparentTo(self)
        self.trophy.setPos(0, 1, 0)
        self.trophy.setScale(0.1)
        self.base = self.trophy.find('**/trophyBase')
        self.column = self.trophy.find('**/trophyColumn')
        self.top = self.trophy.find('**/trophyTop')
        self.topBase = self.trophy.find('**/trophyTopBase')
        self.statue = self.trophy.find('**/trophyStatue')
        self.base.setColorScale(1, 1, 0.8, 1)
        self.bowl = loader.loadModel('phase_3.5/models/gui/fishingTrophyBowl')
        self.bowl.reparentTo(self)
        self.bowl.setPos(0, 1, 0)
        self.bowl.setScale(2.0)
        self.bowlTop = self.bowl.find('**/fishingTrophyGreyBowl')
        self.bowlBase = self.bowl.find('**/fishingTrophyBase')
        self.bowlBase.setScale(1.25, 1, 1)
        self.bowlBase.setColorScale(1, 1, 0.8, 1)
        self.nameLabel = DirectLabel(parent=self, relief=None, pos=(0, 0, -0.15), text='Trophy Text', text_scale=0.125, text_fg=Vec4(0.9, 0.9, 0.4, 1))
        self.shadow = loader.loadModel('phase_3/models/props/drop_shadow')
        self.shadow.reparentTo(self)
        self.shadow.setColor(1, 1, 1, 0.2)
        self.shadow.setPosHprScale(0, 1, 0.35, 0, 90, 0, 0.1, 0.14, 0.1)
        self.setLevel(level)
        return

    def setLevel(self, level):
        self.level = level
        order = ('C', 'D', 'B', 'A')
        scales = (0.25, 0.25, 0.22, 0.25)
        metalTrophy = ('wheelbarrel', 'shovels', 'flower', 'watering_can')
        if self.level >= 0 and self.level < len(order):
            modelStr = 'phase_5.5/models/estate/trophy'
            modelStr += order[level]
            self.gardenTrophy = loader.loadModel(modelStr)
            self.gardenTrophy.setScale(scales[level])
            self.gardenTrophy.reparentTo(self)
            self.metalTrophy = self.gardenTrophy.find('**/%s' % metalTrophy[level])
        if level == -1:
            self.trophy.hide()
            self.bowl.hide()
            self.nameLabel.hide()
        elif level == 0:
            self.trophy.show()
            self.trophy.hide()
            self.bowl.hide()
            self.nameLabel.show()
            self.column.setScale(1.3229, 1.26468, 1.11878)
            self.top.setPos(0, 0, -1)
            self.__bronze()
        elif level == 1:
            self.trophy.show()
            self.trophy.hide()
            self.bowl.hide()
            self.nameLabel.show()
            self.column.setScale(1.3229, 1.26468, 1.61878)
            self.top.setPos(0, 0, -0.5)
            self.__bronze()
        elif level == 2:
            self.trophy.show()
            self.trophy.hide()
            self.bowl.hide()
            self.nameLabel.show()
            self.column.setScale(1.3229, 1.26468, 2.11878)
            self.top.setPos(0, 0, 0)
            self.__silver()
        elif level == 3:
            self.trophy.show()
            self.trophy.hide()
            self.bowl.hide()
            self.nameLabel.show()
            self.column.setScale(1.3229, 1.26468, 2.61878)
            self.top.setPos(0, 0, 0.5)
            self.__silver()
        elif level == 4:
            self.trophy.show()
            self.bowl.hide()
            self.nameLabel.show()
            self.column.setScale(1.3229, 1.26468, 3.11878)
            self.top.setPos(0, 0, 1)
            self.__gold()
        elif level == 5:
            self.trophy.hide()
            self.bowl.show()
            self.bowlTop.setScale(1.75)
            self.nameLabel.show()
            self.__bronze()
        elif level == 6:
            self.trophy.hide()
            self.bowl.show()
            self.bowlTop.setScale(2.0)
            self.nameLabel.show()
            self.__silver()
        elif level >= 7:
            self.trophy.hide()
            self.bowl.show()
            self.bowlTop.setScale(2.25)
            self.nameLabel.show()
            self.__gold()

    def __bronze(self):
        self.top.setColorScale(0.9, 0.6, 0.33, 1)
        self.bowlTop.setColorScale(0.9, 0.6, 0.33, 1)
        self.metalTrophy.setColorScale(0.9, 0.6, 0.33, 1)

    def __silver(self):
        self.top.setColorScale(0.9, 0.9, 1, 1)
        self.bowlTop.setColorScale(0.9, 0.9, 1, 1)
        self.metalTrophy.setColorScale(0.9, 0.9, 1, 1)

    def __gold(self):
        self.top.setColorScale(1, 0.95, 0.1, 1)
        self.bowlTop.setColorScale(1, 0.95, 0.1, 1)
        self.metalTrophy.setColorScale(1, 0.95, 0.1, 1)

    def destroy(self):
        self.trophy.removeNode()
        self.bowl.removeNode()
        self.shadow.removeNode()
        if hasattr(self, 'gardenTrophy'):
            self.gardenTrophy.removeNode()
        DirectFrame.destroy(self)
