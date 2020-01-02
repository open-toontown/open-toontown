from direct.directnotify import DirectNotifyGlobal
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from direct.showbase import PythonUtil
from direct.task import Task
from toontown.fishing.FishPhoto import DirectRegion
from toontown.racing.KartDNA import *
from toontown.racing.Kart import Kart
from toontown.racing import RaceGlobals
from toontown.shtiker.ShtikerPage import ShtikerPage
from toontown.toonbase import ToontownGlobals, TTLocalizer
from .FishPage import FishingTrophy
if (__debug__):
    import pdb
PageMode = PythonUtil.Enum('Customize, Records, Trophy')

class KartPage(ShtikerPage):
    notify = DirectNotifyGlobal.directNotify.newCategory('KartPage')

    def __init__(self):
        ShtikerPage.__init__(self)
        self.avatar = None
        self.mode = PageMode.Customize
        return

    def enter(self):
        if not hasattr(self, 'title'):
            self.load()
        self.setMode(self.mode, 1)
        ShtikerPage.enter(self)

    def exit(self):
        self.kartCustomizer.hide()
        self.racingTrophies.hide()
        self.racingRecords.hide()
        ShtikerPage.exit(self)

    def setAvatar(self, av):
        self.avatar = av

    def getAvatar(self):
        return self.avatar

    def load(self):
        ShtikerPage.load(self)
        self.kartCustomizer = KartCustomizeUI(self.avatar, self)
        self.kartCustomizer.hide()
        self.kartCustomizer.load()
        self.racingRecords = RacingRecordsUI(self.avatar, self)
        self.racingRecords.hide()
        self.racingRecords.load()
        self.racingTrophies = RacingTrophiesUI(self.avatar, self)
        self.racingTrophies.hide()
        self.racingTrophies.load()
        self.title = DirectLabel(parent=self, relief=None, text='', text_scale=0.1, pos=(0, 0, 0.65))
        normalColor = (1, 1, 1, 1)
        clickColor = (0.8, 0.8, 0, 1)
        rolloverColor = (0.15, 0.82, 1.0, 1)
        diabledColor = (1.0, 0.98, 0.15, 1)
        gui = loader.loadModel('phase_3.5/models/gui/fishingBook')
        self.customizeTab = DirectButton(parent=self, relief=None, text=TTLocalizer.KartPageCustomizeTab, text_scale=TTLocalizer.KPkartTab, text_align=TextNode.ALeft, text_pos=(-0.025, 0.0, 0.0), image=gui.find('**/tabs/polySurface1'), image_pos=(0.55, 1, -0.91), image_hpr=(0, 0, -90), image_scale=(0.033, 0.033, 0.035), image_color=normalColor, image1_color=clickColor, image2_color=rolloverColor, image3_color=diabledColor, text_fg=Vec4(0.2, 0.1, 0, 1), command=self.setMode, extraArgs=[PageMode.Customize], pos=(0.92, 0, 0.55))
        self.recordsTab = DirectButton(parent=self, relief=None, text=TTLocalizer.KartPageRecordsTab, text_scale=TTLocalizer.KPkartTab, text_align=TextNode.ALeft, image=gui.find('**/tabs/polySurface2'), image_pos=(0.12, 1, -0.91), image_hpr=(0, 0, -90), image_scale=(0.033, 0.033, 0.035), image_color=normalColor, image1_color=clickColor, image2_color=rolloverColor, image3_color=diabledColor, text_fg=Vec4(0.2, 0.1, 0, 1), command=self.setMode, extraArgs=[PageMode.Records], pos=(0.92, 0, 0.1))
        self.trophyTab = DirectButton(parent=self, relief=None, text=TTLocalizer.KartPageTrophyTab, text_scale=TTLocalizer.KPkartTab, text_pos=(0.03, 0.0, 0.0), text_align=TextNode.ALeft, image=gui.find('**/tabs/polySurface3'), image_pos=(-0.28, 1, -0.91), image_hpr=(0, 0, -90), image_scale=(0.033, 0.033, 0.035), image_color=normalColor, image1_color=clickColor, image2_color=rolloverColor, image3_color=diabledColor, text_fg=Vec4(0.2, 0.1, 0, 1), command=self.setMode, extraArgs=[PageMode.Trophy], pos=(0.92, 0, -0.3))
        self.customizeTab.setPos(-0.55, 0, 0.775)
        self.recordsTab.setPos(-0.13, 0, 0.775)
        self.trophyTab.setPos(0.28, 0, 0.775)
        gui.removeNode()
        return

    def unload(self):
        ShtikerPage.unload(self)

    def setMode(self, mode, updateAnyways = 0):
        messenger.send('wakeup')
        if not updateAnyways:
            if self.mode == mode:
                return
            else:
                self.mode = mode
        if mode == PageMode.Customize:
            self.title['text'] = TTLocalizer.KartPageTitleCustomize
            self.customizeTab['state'] = DGG.DISABLED
            self.recordsTab['state'] = DGG.NORMAL
            self.trophyTab['state'] = DGG.NORMAL
        elif mode == PageMode.Records:
            self.title['text'] = TTLocalizer.KartPageTitleRecords
            self.customizeTab['state'] = DGG.NORMAL
            self.recordsTab['state'] = DGG.DISABLED
            self.trophyTab['state'] = DGG.NORMAL
        elif mode == PageMode.Trophy:
            self.title['text'] = TTLocalizer.KartPageTitleTrophy
            self.customizeTab['state'] = DGG.NORMAL
            self.recordsTab['state'] = DGG.NORMAL
            self.trophyTab['state'] = DGG.DISABLED
        else:
            raise Exception('KartPage::setMode - Invalid Mode %s' % mode)
        self.updatePage()

    def updatePage(self):
        if self.mode == PageMode.Customize:
            self.kartCustomizer.show()
            self.racingTrophies.hide()
            self.racingRecords.hide()
        elif self.mode == PageMode.Records:
            self.kartCustomizer.hide()
            self.racingTrophies.hide()
            self.racingRecords.show()
        elif self.mode == PageMode.Trophy:
            self.kartCustomizer.hide()
            self.racingTrophies.show()
            self.racingRecords.hide()
        else:
            raise Exception('KartPage::updatePage - Invalid Mode %s' % self.mode)


class KartCustomizeUI(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('KartCustomizeUI')

    def __init__(self, avatar, parent = aspect2d):
        self.avatar = avatar
        DirectFrame.__init__(self, parent=parent, relief=None, pos=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0))
        return

    def destroy(self):
        self.itemSelector.destroy()
        self.kartViewer.destroy()
        del self.avatar
        del self.itemSelector
        del self.kartViewer
        DirectFrame.destroy(self)

    def load(self):
        uiRootNode = loader.loadModel('phase_6/models/gui/ShtikerBookUI')
        self.itemSelector = ItemSelector(self.avatar, parent=self)
        self.itemSelector.setPos(uiRootNode.find('**/uiAccessoryIcons').getPos())
        self.itemSelector.load(uiRootNode)
        self.kartViewer = KartViewer(list(self.avatar.getKartDNA()), parent=self)
        self.kartViewer.setPos(uiRootNode.find('**/uiKartView').getPos())
        self.kartViewer.load(uiRootNode, 'uiKartViewerFrame1', ['rotate_right_up',
         'rotate_right_down',
         'rotate_right_roll',
         'rotate_right_down',
         (0.275, -.08)], ['rotate_left_up',
         'rotate_left_down',
         'rotate_left_roll',
         'rotate_left_down',
         (-.27, -.08)], (0, -.08))
        self.kartViewer.uiRotateLeft.setZ(-.25)
        self.kartViewer.uiRotateRight.setZ(-.25)
        self.itemSelector.itemViewers['main'].leftArrowButton.setZ(self.kartViewer.getZ() + 0.25)
        self.itemSelector.itemViewers['main'].rightArrowButton.setZ(self.kartViewer.getZ() + 0.25)
        self.kartViewer.setBounds(-0.38, 0.38, -0.25, 0.325)
        self.kartViewer.setBgColor(1.0, 1.0, 0.8, 1.0)
        uiRootNode.removeNode()

    def getKartViewer(self):
        return self.kartViewer

    def show(self):
        self.itemSelector.itemViewers['main'].initUpdatedDNA()
        self.itemSelector.setupAccessoryIcons()
        self.itemSelector.show()
        self.kartViewer.show(list(self.avatar.getKartDNA()))
        DirectFrame.show(self)

    def hide(self):
        if hasattr(self, 'itemSelector'):
            if hasattr(self.itemSelector.itemViewers['main'], 'updatedDNA'):
                self.itemSelector.itemViewers['main'].setUpdatedDNA()
            self.itemSelector.resetAccessoryIcons()
            if hasattr(self.itemSelector.itemViewers['main'], 'confirmDlg'):
                self.itemSelector.itemViewers['main'].confirmDlg.hide()
            self.itemSelector.hide()
        if hasattr(self, 'kartViewer'):
            self.kartViewer.hide()
        DirectFrame.hide(self)


class RacingRecordsUI(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('RacingRecordsUI')

    def __init__(self, avatar, parent = aspect2d):
        self.avatar = avatar
        self.timeDisplayList = []
        self.lastTimes = []
        DirectFrame.__init__(self, parent=parent, relief=None, pos=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0))
        return

    def destroy(self):
        del self.avatar
        del self.lastTimes
        del self.timeDisplayList
        DirectFrame.destroy(self)

    def load(self):
        offset = 0
        trackNameArray = TTLocalizer.KartRace_TrackNames
        for trackId in RaceGlobals.TrackIds:
            trackName = trackNameArray[trackId]
            trackNameDisplay = DirectLabel(parent=self, relief=None, text=trackName, text_align=TextNode.ALeft, text_scale=0.075, text_fg=(0.95, 0.95, 0.0, 1.0), text_shadow=(0, 0, 0, 1), text_pos=(-0.8, 0.5 - offset), text_font=ToontownGlobals.getSignFont())
            bestTimeDisplay = DirectLabel(parent=self, relief=None, text=TTLocalizer.KartRace_Unraced, text_scale=0.06, text_fg=(0.0, 0.0, 0.0, 1.0), text_pos=(0.65, 0.5 - offset), text_font=ToontownGlobals.getToonFont())
            offset += 0.1
            self.timeDisplayList.append(bestTimeDisplay)

        return

    def show(self):
        bestTimes = self.avatar.getKartingPersonalBestAll()
        if bestTimes != self.lastTimes:
            for i in range(0, len(bestTimes)):
                time = bestTimes[i]
                if time != 0.0:
                    whole, part = divmod(time, 1)
                    min, sec = divmod(whole, 60)
                    timeText = '%02d:%02d:%02d' % (min, sec, part * 100)
                    self.timeDisplayList[i]['text'] = (timeText,)

        self.lastTimes = bestTimes
        DirectFrame.show(self)


class RacingTrophiesUI(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('RacingTrophiesUI')

    def __init__(self, avatar, parent = aspect2d):
        self.avatar = avatar
        self.trophyPanels = []
        self.trophies = None
        self.trophyTextDisplay = None
        DirectFrame.__init__(self, parent=parent, relief=None, pos=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0))
        return

    def destroy(self):
        for panel in self.trophyPanels:
            panel.destroy()

        self.ticketDisplay.destroy()
        self.trophyTextDisplay.destroy()
        del self.avatar
        del self.ticketDisplay
        del self.trophyPanels
        del self.trophies
        del self.trophyTextDisplay
        DirectFrame.destroy(self)

    def load(self):
        self.trophies = base.localAvatar.getKartingTrophies()
        xStart = -0.76
        yStart = 0.475
        xOffset = 0.17
        yOffset = 0.23
        for j in range(RaceGlobals.NumCups):
            for i in range(RaceGlobals.TrophiesPerCup):
                trophyPanel = DirectLabel(parent=self, relief=None, pos=(xStart + i * xOffset, 0.0, yStart - j * yOffset), state=DGG.NORMAL, image=DGG.getDefaultDialogGeom(), image_scale=(0.75, 1, 1), image_color=(0.8, 0.8, 0.8, 1), text=TTLocalizer.SuitPageMystery[0], text_scale=0.45, text_fg=(0, 0, 0, 1), text_pos=(0, 0, -0.25), text_font=ToontownGlobals.getInterfaceFont(), text_wordwrap=5.5)
                trophyPanel.scale = 0.2
                trophyPanel.setScale(trophyPanel.scale)
                self.trophyPanels.append(trophyPanel)

        xStart = -0.25
        yStart = -0.38
        xOffset = 0.25
        for i in range(RaceGlobals.NumCups):
            cupPanel = DirectLabel(parent=self, relief=None, pos=(xStart + i * xOffset, 0.0, yStart), state=DGG.NORMAL, image=DGG.getDefaultDialogGeom(), image_scale=(0.75, 1, 1), image_color=(0.8, 0.8, 0.8, 1), text=TTLocalizer.SuitPageMystery[0], text_scale=0.45, text_fg=(0, 0, 0, 1), text_pos=(0, 0, -0.25), text_font=ToontownGlobals.getInterfaceFont(), text_wordwrap=5.5)
            cupPanel.scale = 0.3
            cupPanel.setScale(cupPanel.scale)
            self.trophyPanels.append(cupPanel)

        self.ticketDisplay = DirectLabel(parent=self, relief=None, image=loader.loadModel('phase_6/models/karting/tickets'), image_pos=(0.2, 0, -0.635), image_scale=0.2, text=TTLocalizer.KartPageTickets + str(self.avatar.getTickets()), text_scale=0.07, text_fg=(0, 0, 0.95, 1.0), text_pos=(0, -0.65), text_font=ToontownGlobals.getSignFont())
        self.trophyTextDisplay = DirectLabel(parent=self, relief=None, text='', text_scale=0.07, text_fg=(1, 0, 0, 1), text_shadow=(0, 0, 0, 0), text_pos=(0.0, -0.175), text_font=ToontownGlobals.getInterfaceFont())
        self.updateTrophies()
        return

    def grow(self, index, pos):
        self.trophyPanels[index]['image_color'] = Vec4(1.0, 1.0, 0.8, 1.0)
        self.trophyTextDisplay['text'] = TTLocalizer.KartPageTrophyDetail % (index + 1, TTLocalizer.KartTrophyDescriptions[index])

    def shrink(self, index, pos):
        self.trophyPanels[index]['image_color'] = Vec4(1.0, 1.0, 1.0, 1.0)
        self.trophyTextDisplay['text'] = ''

    def show(self):
        self.ticketDisplay['text'] = (TTLocalizer.KartPageTickets + str(self.avatar.getTickets()),)
        if self.trophies != base.localAvatar.getKartingTrophies():
            self.trophies = base.localAvatar.getKartingTrophies()
            self.updateTrophies()
        DirectFrame.show(self)

    def updateTrophies(self):
        for t in range(len(self.trophyPanels)):
            if self.trophies[t]:
                trophyPanel = self.trophyPanels[t]
                trophyPanel['text'] = ''
                trophyModel = RacingTrophy(t)
                trophyModel.reparentTo(trophyPanel)
                trophyModel.nameLabel.hide()
                trophyModel.setPos(0, 0, -0.4)
                trophyPanel['image_color'] = Vec4(1.0, 1.0, 1.0, 1.0)
                trophyPanel.bind(DGG.ENTER, self.grow, extraArgs=[t])
                trophyPanel.bind(DGG.EXIT, self.shrink, extraArgs=[t])


class ItemSelector(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('ItemSelector')

    class ItemViewer(DirectFrame):
        notify = DirectNotifyGlobal.directNotify.newCategory('ItemViewer')

        def __init__(self, avatar, parent = aspect2d):
            self.currItem = None
            self.itemList = None
            self._parent = parent
            self.avatar = avatar
            self.currAccessoryType = None
            self.texCount = 1
            DirectFrame.__init__(self, parent=parent, relief=None, pos=(0, 0, 0), scale=(1.0, 1.0, 1.0))
            return

        def destroy(self):
            self.uiBgFrame.destroy()
            self.uiImagePlane.destroy()
            self.uiTextBox.destroy()
            self.leftArrowButton.destroy()
            self.rightArrowButton.destroy()
            del self.avatar
            del self._parent
            del self.currItem
            del self.itemList
            del self.uiBgFrame
            del self.uiImagePlane
            del self.uiTextBox
            del self.leftArrowButton
            del self.rightArrowButton
            del self.deleteButton
            DirectFrame.destroy(self)

        def setCurrentItem(self, currItem):
            self.currItem = currItem

        def getCurrentItem(self):
            return self.currItem

        def initUpdatedDNA(self):
            self.updatedDNA = list(self.avatar.getKartDNA())

        def setUpdatedDNA(self):
            currKartDNA = self.avatar.getKartDNA()
            for i in range(len(self.updatedDNA)):
                if self.updatedDNA[i] != currKartDNA[i]:
                    self.avatar.requestKartDNAFieldUpdate(i, self.updatedDNA[i])

            del self.updatedDNA

        def setItemList(self, itemList):
            self.itemList = itemList

        def load(self, uiRootNode):
            self.uiBgFrame = DirectFrame(parent=self, relief=None, geom=uiRootNode.find('**/uiAccessoryViewerFrame'), scale=1.0)
            self.uiImagePlane = DirectFrame(parent=self, relief=None, geom=uiRootNode.find('**/uiAccessoryImagePlane'), scale=0.75)
            bounds = self.uiImagePlane.getBounds()
            cm = CardMaker('uiImagePlane')
            cm.setFrame(bounds[0], bounds[1], bounds[2], bounds[3])
            self.uiImagePlane['geom'] = NodePath(cm.generate())
            self.uiImagePlane.component('geom0').setColorScale(1.0, 1.0, 0.8, 1.0)
            self.uiImagePlane.component('geom0').setTransparency(True)
            self.locator1 = self.attachNewNode('locator1')
            self.locator2 = self.attachNewNode('locator2')
            self.locator1.setPos(0, 0, 0.035)
            self.locator2.setPos(0.0, 0.0, 0.0)
            tex = loader.loadTexture('phase_6/maps/NoAccessoryIcon3.jpg', 'phase_6/maps/NoAccessoryIcon3_a.rgb')
            self.uiImagePlane.component('geom0').setTexture(tex, self.texCount)
            self.texCount += 1
            self.uiTextBox = DirectFrame(parent=self, relief=None, scale=1.0, text='', text_font=ToontownGlobals.getInterfaceFont(), text_fg=(0.5, 0, 0, 1), text_shadow=(0, 0, 0, 1), text_scale=0.0715, text_pos=(0.0, -0.23, 0.0))
            self.deleteButton = DirectButton(parent=self, relief=None, geom=(uiRootNode.find('**/uiAccessorydelete_up'),
             uiRootNode.find('**/uiAccessorydelete_down'),
             uiRootNode.find('**/uiAccessorydelete_rollover'),
             uiRootNode.find('**/uiAccessorydelete_rollover')), text=TTLocalizer.KartShtikerDelete, text_font=ToontownGlobals.getSignFont(), text_pos=(0, -0.125, 0), text_scale=TTLocalizer.KPdeleteButton, text_fg=(1, 1, 1, 1), scale=1.0, pressEffect=False, command=lambda : self.__handleItemDeleteConfirm())
            self.deleteButton.hide()
            self.leftArrowButton = DirectButton(parent=self, relief=None, geom=(uiRootNode.find('**/ArrowLeftButtonUp'),
             uiRootNode.find('**/ArrowLeftButtonDown'),
             uiRootNode.find('**/ArrowLeftButtonRollover'),
             uiRootNode.find('**/ArrowLeftButtonInactive')), scale=1.0, pressEffect=False, command=lambda : self.__handleItemChange(-1))
            self.rightArrowButton = DirectButton(parent=self, relief=None, geom=(uiRootNode.find('**/ArrowRightButtonUp'),
             uiRootNode.find('**/ArrowRightButtonDown'),
             uiRootNode.find('**/ArrowRightButtonRollover'),
             uiRootNode.find('**/ArrowRightButtonInactive')), scale=1.0, pressEffect=False, command=lambda : self.__handleItemChange(1))
            return

        def enable(self):
            self.leftArrowButton['state'] = DGG.NORMAL
            self.rightArrowButton['state'] = DGG.NORMAL

        def disable(self):
            self.leftArrowButton['state'] = DGG.DISABLED
            self.rightArrowButton['state'] = DGG.DISABLED

        def setupViewer(self, category):
            colorTypeList = [KartDNA.bodyColor, KartDNA.accColor]
            if category == InvalidEntry:
                self.__handleHideItem()
                self.__updateDeleteButton(DGG.DISABLED)
                self.disable()
            else:
                accessDict = getAccessDictByType(self.avatar.getKartAccessoriesOwned())
                self.currAccessoryType = category
                if category in colorTypeList:
                    self.itemList = list(accessDict.get(KartDNA.bodyColor, []))
                    self.itemList.append(InvalidEntry)
                elif category == KartDNA.rimsType:
                    self.itemList = list(accessDict.get(KartDNA.rimsType, []))
                    self.itemList.append(InvalidEntry)
                else:
                    self.itemList = list(accessDict.get(category, []))
                self.currItem = self.updatedDNA[category]
                if category in colorTypeList:
                    if self.currItem == InvalidEntry or self.currItem not in accessDict.get(KartDNA.bodyColor):
                        self.__updateDeleteButton(DGG.DISABLED)
                    else:
                        self.__updateDeleteButton(DGG.NORMAL, TTLocalizer.KartShtikerDelete)
                    self.__handleShowItem()
                elif category == KartDNA.rimsType:
                    if self.currItem == InvalidEntry:
                        self.__updateDeleteButton(DGG.DISABLED)
                    else:
                        self.__updateDeleteButton(DGG.NORMAL, TTLocalizer.KartShtikerDelete)
                    self.__handleShowItem()
                elif self.currItem != InvalidEntry and self.itemList != []:
                    if self.currItem in self.avatar.accessories:
                        self.__handleShowItem()
                        self.__updateDeleteButton(DGG.NORMAL, TTLocalizer.KartShtikerDelete)
                else:
                    self.__handleHideItem()
                    self.__updateDeleteButton(DGG.DISABLED)
                if len(self.itemList) == 1:
                    if self.currAccessoryType == KartDNA.rimsType:
                        self.disable()
                        self.setViewerText(TTLocalizer.KartShtikerDefault % getattr(TTLocalizer, AccessoryTypeNameDict[self.currAccessoryType]))
                    elif self.currAccessoryType in colorTypeList:
                        self.disable()
                        self.setViewerText(TTLocalizer.KartShtikerDefault % getattr(TTLocalizer, AccessoryTypeNameDict[self.currAccessoryType]))
                    else:
                        self.enable()
                elif len(self.itemList) == 0:
                    self.disable()
                    self.setViewerText(TTLocalizer.KartShtikerNo % getattr(TTLocalizer, AccessoryTypeNameDict[self.currAccessoryType]))
                else:
                    if self.currAccessoryType == KartDNA.rimsType:
                        self.setViewerText(TTLocalizer.KartShtikerDefault % getattr(TTLocalizer, AccessoryTypeNameDict[self.currAccessoryType]))
                    elif self.currAccessoryType in colorTypeList:
                        self.setViewerText(TTLocalizer.KartShtikerDefault % getattr(TTLocalizer, AccessoryTypeNameDict[self.currAccessoryType]))
                    elif self.currItem == InvalidEntry:
                        self.setViewerText(TTLocalizer.KartShtikerNo % getattr(TTLocalizer, AccessoryTypeNameDict[self.currAccessoryType]))
                    self.enable()

        def resetViewer(self):
            self.itemList = None
            self.currItem = None
            self.disable()
            return

        def __updateDeleteButton(self, state, text = TTLocalizer.KartShtikerDelete):
            self.deleteButton['state'] = state
            self.deleteButton['text'] = text
            if state == DGG.NORMAL:
                self.uiImagePlane.setPos(self.locator1.getPos())
                self.deleteButton.show()
            else:
                self.uiImagePlane.setPos(self.locator2.getPos())
                self.deleteButton.hide()

        def setViewerText(self, text):
            self.uiTextBox['text'] = text

        def __updateViewerUI(self):
            accList = [KartDNA.bodyColor, KartDNA.accColor, KartDNA.rimsType]
            if self.currItem != InvalidEntry:
                self.__handleShowItem()
                if self.currItem not in self.avatar.accessories and self.currAccessoryType in accList:
                    self.__updateDeleteButton(DGG.DISABLED)
                else:
                    self.__updateDeleteButton(DGG.NORMAL, TTLocalizer.KartShtikerDelete)
            else:
                if self.currAccessoryType in accList:
                    self.setViewerText(TTLocalizer.KartShtikerDefault % getattr(TTLocalizer, AccessoryTypeNameDict[self.currAccessoryType]))
                    self.__handleShowItem()
                else:
                    self.__handleHideItem()
                    self.setViewerText(TTLocalizer.KartShtikerNo % getattr(TTLocalizer, AccessoryTypeNameDict[self.currAccessoryType]))
                self.__updateDeleteButton(DGG.DISABLED)

        def __handleItemChange(self, direction):
            self.notify.debug('__handleItemChange: currItem %s' % self.currItem)

            def updateItem(self = self, direction = direction):
                if self.itemList.count(self.currItem) != 0:
                    index = self.itemList.index(self.currItem)
                    index += direction
                    if index < 0 or index >= len(self.itemList):
                        invalidList = [KartDNA.bodyColor, KartDNA.accColor, KartDNA.rimsType]
                        if self.currAccessoryType not in invalidList:
                            self.currItem = InvalidEntry
                        elif direction > 0:
                            self.currItem = self.itemList[0]
                        else:
                            self.currItem = self.itemList[-1]
                    else:
                        self.currItem = self.itemList[index]
                elif self.itemList == []:
                    self.currItem = InvalidEntry
                elif direction > 0:
                    self.currItem = self.itemList[0]
                else:
                    self.currItem = self.itemList[-1]

            messenger.send('wakeup')
            updateItem()
            self.__updateViewerUI()
            self.notify.debug('__handleItemChange: currItem %s' % self.currItem)
            self.updatedDNA[self.currAccessoryType] = self.currItem
            kart = self._parent._parent.getKartViewer().getKart()
            kart.updateDNAField(self.currAccessoryType, self.currItem)

        def __handleShowItem(self):
            self.uiImagePlane.component('geom0').setColorScale(1.0, 1.0, 1.0, 1.0)
            if self.currAccessoryType in [KartDNA.ebType,
             KartDNA.spType,
             KartDNA.fwwType,
             KartDNA.bwwType]:
                texNodePath = getTexCardNode(self.currItem)
                tex = loader.loadTexture('phase_6/maps/%s.jpg' % texNodePath, 'phase_6/maps/%s_a.rgb' % texNodePath)
            elif self.currAccessoryType == KartDNA.rimsType:
                if self.currItem == InvalidEntry:
                    texNodePath = getTexCardNode(getDefaultRim())
                else:
                    texNodePath = getTexCardNode(self.currItem)
                tex = loader.loadTexture('phase_6/maps/%s.jpg' % texNodePath, 'phase_6/maps/%s_a.rgb' % texNodePath)
            elif self.currAccessoryType in [KartDNA.bodyColor, KartDNA.accColor]:
                tex = loader.loadTexture('phase_6/maps/Kartmenu_paintbucket.jpg', 'phase_6/maps/Kartmenu_paintbucket_a.rgb')
                if self.currItem == InvalidEntry:
                    self.uiImagePlane.component('geom0').setColorScale(getDefaultColor())
                else:
                    self.uiImagePlane.component('geom0').setColorScale(getAccessory(self.currItem))
            elif self.currAccessoryType == KartDNA.decalType:
                kart = self._parent._parent.getKartViewer().getKart()
                kartDecal = getDecalId(kart.kartDNA[KartDNA.bodyType])
                texNodePath = getTexCardNode(self.currItem)
                tex = loader.loadTexture('phase_6/maps/%s.jpg' % texNodePath % kartDecal, 'phase_6/maps/%s_a.rgb' % texNodePath % kartDecal)
            else:
                tex = loader.loadTexture('phase_6/maps/NoAccessoryIcon3.jpg', 'phase_6/maps/NoAccessoryIcon3_a.rgb')
            colorTypeList = [KartDNA.bodyColor, KartDNA.accColor]
            if self.currItem == InvalidEntry:
                if self.currAccessoryType == KartDNA.rimsType:
                    self.setViewerText(TTLocalizer.KartShtikerDefault % getattr(TTLocalizer, AccessoryTypeNameDict[self.currAccessoryType]))
                elif self.currAccessoryType in colorTypeList:
                    self.setViewerText(TTLocalizer.KartShtikerDefault % getattr(TTLocalizer, AccessoryTypeNameDict[self.currAccessoryType]))
                elif self.currItem == InvalidEntry:
                    self.setViewerText(TTLocalizer.KartShtikerNo % getattr(TTLocalizer, AccessoryTypeNameDict[self.currAccessoryType]))
            else:
                self.setViewerText(getAccName(self.currItem) + ' ' + getattr(TTLocalizer, AccessoryTypeNameDict[self.currAccessoryType]))
            self.uiImagePlane.component('geom0').setTexture(tex, self.texCount)
            self.texCount += 1

        def __handleHideItem(self):
            self.uiImagePlane.component('geom0').setColorScale(1.0, 1.0, 1.0, 1.0)
            self.uiImagePlane.component('geom0').setTexture(loader.loadTexture('phase_6/maps/NoAccessoryIcon3.jpg', 'phase_6/maps/NoAccessoryIcon3_a.rgb'), self.texCount)
            self.texCount += 1

        def __handleItemDeleteConfirm(self):
            self.notify.debug('__handleItemDeleteConfirm:')
            if not hasattr(self, 'confirmDlg'):
                uiRootNode = loader.loadModel('phase_6/models/gui/ShtikerBookUI')
                self.confirmDlg = DirectFrame(parent=aspect2d, relief=None, geom=uiRootNode.find('**/uiAccessoryNotice'), geom_scale=1.0, text=TTLocalizer.KartPageConfirmDelete, text_scale=0.07, text_pos=(0, 0.022))
                self.confirmDlg.hide()
                self.confirmDlg.setPos(aspect2d, 0, -.195, -.195)
                self.cancelButton = DirectButton(parent=self.confirmDlg, relief=None, image=(uiRootNode.find('**/CancelButtonUp'), uiRootNode.find('**/CancelButtonDown'), uiRootNode.find('**/CancelButtonRollover')), geom=uiRootNode.find('**/CancelIcon'), scale=1.0, pressEffect=False, command=self.confirmDlg.hide)
                self.confirmButton = DirectButton(parent=self.confirmDlg, relief=None, image=(uiRootNode.find('**/CheckButtonUp'), uiRootNode.find('**/CheckButtonDown'), uiRootNode.find('**/CheckButtonRollover')), geom=uiRootNode.find('**/CheckIcon'), scale=1.0, pressEffect=False, command=self.__handleItemDelete)
            self.confirmDlg.show()
            return

        def __handleItemDelete(self):

            def handleColorDelete(self = self):
                if self.currAccessoryType == KartDNA.bodyColor:
                    if self.updatedDNA[KartDNA.accColor] == deletedItem:
                        self.avatar.requestKartDNAFieldUpdate(KartDNA.accColor, self.currItem)
                        self.updatedDNA[KartDNA.accColor] = self.currItem
                        kart = self._parent._parent.getKartViewer().getKart()
                        kart.updateDNAField(KartDNA.accColor, self.currItem)
                elif self.currAccessoryType == KartDNA.accColor:
                    if self.updatedDNA[KartDNA.bodyColor] == deletedItem:
                        self.avatar.requestKartDNAFieldUpdate(KartDNA.bodyColor, self.currItem)
                        self.updatedDNA[KartDNA.bodyColor] = self.currItem
                        kart = self._parent._parent.getKartViewer().getKart()
                        kart.updateDNAField(KartDNA.bodyColor, self.currItem)

            self.notify.debug('__handleItemDelete: Delete request on accessory %s' % self.currItem)
            self.confirmDlg.hide()
            messenger.send('wakeup')
            deletedItem = self.currItem
            self.avatar.requestRemoveOwnedAccessory(deletedItem)
            index = self.itemList.index(self.currItem)
            self.itemList.pop(index)
            self.currItem = InvalidEntry
            self.__updateViewerUI()
            self.updatedDNA[self.currAccessoryType] = self.currItem
            kart = self._parent._parent.getKartViewer().getKart()
            kart.updateDNAField(self.currAccessoryType, self.currItem)
            if self.avatar.getAccessoryByType(self.currAccessoryType) == deletedItem:
                self.avatar.requestKartDNAFieldUpdate(self.currAccessoryType, self.currItem)
            if self.currAccessoryType in [KartDNA.bodyColor, KartDNA.accColor]:
                handleColorDelete()
            if self.itemList == [] or self.itemList[0] == InvalidEntry:
                self.disable()
                self.setViewerText(TTLocalizer.KartShtikerNo % getattr(TTLocalizer, AccessoryTypeNameDict[self.currAccessoryType]))

    def __init__(self, avatar, parent = aspect2d):
        self.state = InvalidEntry
        self.avatar = avatar
        self.itemViewers = {}
        self.buttonDict = {}
        self._parent = parent
        DirectFrame.__init__(self, parent=parent, relief=None, pos=(0, 0, 0), scale=(1.0, 1.0, 1.0))
        return

    def destroy(self):
        for key in list(self.buttonDict.keys()):
            self.buttonDict[key].destroy()
            del self.buttonDict[key]

        for key in list(self.itemViewers.keys()):
            self.itemViewers[key].destroy()
            del self.itemViewers[key]

        del self.avatar
        del self.itemViewers
        del self.buttonDict
        del self.ebButton
        del self.fwwButton
        del self.bwwButton
        del self.rimButton
        del self.decalButton
        del self.paintKartButton
        del self.paintAccessoryButton
        DirectFrame.destroy(self)

    def load(self, uiRootNode):
        self.itemViewers['main'] = ItemSelector.ItemViewer(self.avatar, self)
        self.itemViewers['main'].load(uiRootNode)
        self.itemViewers['main'].setPos(self.getParent(), uiRootNode.find('**/uiAccessoryView').getPos())
        self.ebButton = DirectButton(parent=self, relief=None, geom=(uiRootNode.find('**/eBlockButton_up'),
         uiRootNode.find('**/eBlockButton_rollover'),
         uiRootNode.find('**/eBlockButton_rollover'),
         uiRootNode.find('**/eBlockButton_inactive')), scale=1.0, pressEffect=False, command=lambda : self.__changeItemCategory(KartDNA.ebType))
        self.buttonDict[KartDNA.ebType] = self.ebButton
        self.spButton = DirectButton(parent=self, relief=None, geom=(uiRootNode.find('**/spoilerButton_up'),
         uiRootNode.find('**/spoilerButton_rollover'),
         uiRootNode.find('**/spoilerButton_rollover'),
         uiRootNode.find('**/spoilerButton_inactive')), scale=1.0, pressEffect=False, command=lambda : self.__changeItemCategory(KartDNA.spType))
        self.buttonDict[KartDNA.spType] = self.spButton
        self.fwwButton = DirectButton(parent=self, relief=None, geom=(uiRootNode.find('**/frontButton_up'),
         uiRootNode.find('**/frontButton_rollover'),
         uiRootNode.find('**/frontButton_rollover'),
         uiRootNode.find('**/frontButton_inactive')), scale=1.0, pressEffect=False, command=lambda : self.__changeItemCategory(KartDNA.fwwType))
        self.buttonDict[KartDNA.fwwType] = self.fwwButton
        self.bwwButton = DirectButton(parent=self, relief=None, geom=(uiRootNode.find('**/rearButton_up'),
         uiRootNode.find('**/rearButton_rollover'),
         uiRootNode.find('**/rearButton_rollover'),
         uiRootNode.find('**/rearButton_inactive')), scale=1.0, pressEffect=False, command=lambda : self.__changeItemCategory(KartDNA.bwwType))
        self.buttonDict[KartDNA.bwwType] = self.bwwButton
        self.rimButton = DirectButton(parent=self, relief=None, geom=(uiRootNode.find('**/rimButton_up'),
         uiRootNode.find('**/rimButton_rollover'),
         uiRootNode.find('**/rimButton_rollover'),
         uiRootNode.find('**/rimButton_inactive')), scale=1.0, pressEffect=False, command=lambda : self.__changeItemCategory(KartDNA.rimsType))
        self.buttonDict[KartDNA.rimsType] = self.rimButton
        self.decalButton = DirectButton(parent=self, relief=None, geom=(uiRootNode.find('**/decalButton_up'),
         uiRootNode.find('**/decalButton_rollover'),
         uiRootNode.find('**/decalButton_rollover'),
         uiRootNode.find('**/decalButton_inactive')), scale=1.0, pressEffect=False, command=lambda : self.__changeItemCategory(KartDNA.decalType))
        self.buttonDict[KartDNA.decalType] = self.decalButton
        self.paintKartButton = DirectButton(parent=self, relief=None, geom=(uiRootNode.find('**/paintKartButton_up'),
         uiRootNode.find('**/paintKartButton_rollover'),
         uiRootNode.find('**/paintKartButton_rollover'),
         uiRootNode.find('**/paintKartButton_inactive')), scale=1.0, pressEffect=False, command=lambda : self.__changeItemCategory(KartDNA.bodyColor))
        self.buttonDict[KartDNA.bodyColor] = self.paintKartButton
        self.paintAccessoryButton = DirectButton(parent=self, relief=None, geom=(uiRootNode.find('**/paintAccessoryButton_up'),
         uiRootNode.find('**/paintAccessoryButton_rollover'),
         uiRootNode.find('**/paintAccessoryButton_rollover'),
         uiRootNode.find('**/paintAccessoryButton_inactive')), scale=1.0, pressEffect=False, command=lambda : self.__changeItemCategory(KartDNA.accColor))
        self.buttonDict[KartDNA.accColor] = self.paintAccessoryButton
        return

    def setupAccessoryIcons(self):
        accessDict = getAccessDictByType(self.avatar.getKartAccessoriesOwned())
        if accessDict == {}:
            self.itemViewers['main'].disable()
            self.itemViewers['main'].setViewerText(TTLocalizer.KartShtikerNoAccessories)
            return
        self.__changeItemCategory(self.state)

    def resetAccessoryIcons(self):
        for key in list(self.buttonDict.keys()):
            self.buttonDict[key].setProp('state', DGG.NORMAL)

        self.itemViewers['main'].show()
        self.itemViewers['main'].setViewerText('')
        self.state = InvalidEntry
        self.itemViewers['main'].resetViewer()

    def __changeItemCategory(self, buttonType):
        if buttonType == KartDNA.ebType:
            self.ebButton['state'] = DGG.DISABLED
            self.itemViewers['main'].setViewerText(TTLocalizer.KartShtikerEngineBlocks)
            self.itemViewers['main'].setupViewer(KartDNA.ebType)
        elif buttonType == KartDNA.spType:
            self.spButton['state'] = DGG.DISABLED
            self.itemViewers['main'].setViewerText(TTLocalizer.KartShtikerSpoilers)
            self.itemViewers['main'].setupViewer(KartDNA.spType)
        elif buttonType == KartDNA.fwwType:
            self.fwwButton['state'] = DGG.DISABLED
            self.itemViewers['main'].setViewerText(TTLocalizer.KartShtikerFrontWheelWells)
            self.itemViewers['main'].setupViewer(KartDNA.fwwType)
        elif buttonType == KartDNA.bwwType:
            self.bwwButton['state'] = DGG.DISABLED
            self.itemViewers['main'].setViewerText(TTLocalizer.KartShtikerBackWheelWells)
            self.itemViewers['main'].setupViewer(KartDNA.bwwType)
        elif buttonType == KartDNA.rimsType:
            self.rimButton['state'] = DGG.DISABLED
            self.itemViewers['main'].setViewerText(TTLocalizer.KartShtikerRims)
            self.itemViewers['main'].setupViewer(KartDNA.rimsType)
        elif buttonType == KartDNA.decalType:
            self.decalButton['state'] = DGG.DISABLED
            self.itemViewers['main'].setViewerText(TTLocalizer.KartShtikerDecals)
            self.itemViewers['main'].setupViewer(KartDNA.decalType)
        elif buttonType == KartDNA.bodyColor:
            self.paintKartButton['state'] = DGG.DISABLED
            self.itemViewers['main'].setViewerText(TTLocalizer.KartShtikerBodyColors)
            self.itemViewers['main'].setupViewer(KartDNA.bodyColor)
        elif buttonType == KartDNA.accColor:
            self.paintAccessoryButton['state'] = DGG.DISABLED
            self.itemViewers['main'].setViewerText(TTLocalizer.KartShtikerAccColors)
            self.itemViewers['main'].setupViewer(KartDNA.accColor)
        elif buttonType == InvalidEntry:
            self.itemViewers['main'].setViewerText(TTLocalizer.KartShtikerSelect)
            self.itemViewers['main'].setupViewer(buttonType)
        else:
            raise Exception('KartPage.py::__changeItemCategory - INVALID Category Type!')
        if self.state != buttonType and self.state != InvalidEntry:
            self.buttonDict[self.state]['state'] = DGG.NORMAL
            self.buttonDict[self.state].setColorScale(1, 1, 1, 1)
        self.state = buttonType


class KartViewer(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('KartViewer')

    def __init__(self, dna, parent):
        self.kart = None
        self.dna = dna
        self._parent = parent
        self.kartFrame = None
        self.bounds = None
        self.colors = None
        self.uiRotateRight = None
        self.uiRotateLeft = None
        self.uiRotateLabel = None
        DirectFrame.__init__(self, parent=parent, relief=None, pos=(0, 0, 0), scale=(1.0, 1.0, 1.0))
        return

    def destroy(self):
        taskMgr.remove('kartRotateTask')
        if self.kart != None:
            self.kart.delete()
            self.kart = None
        if hasattr(self, 'kartDisplayRegion'):
            self.kartDisplayRegion.unload()
        if hasattr(self, 'uiBgFrame'):
            self.uiBgFrame.destroy()
            del self.uiBgFrame
        if hasattr(self, 'uiRotateLeft') and self.uiRotateLeft:
            self.uiRotateLeft.destroy()
            del self.uiRotateLeft
        if hasattr(self, 'uiRotateRight') and self.uiRotateRight:
            self.uiRotateRight.destroy()
            del self.uiRotateRight
        if hasattr(self, 'uiRotateLabelt') and self.uiRotateLabel:
            self.uiRotateLabel.destroy()
            del self.uiRotateLabel
        if hasattr(self, 'dna'):
            del self.dna
        if hasattr(self, 'parent'):
            del self._parent
        DirectFrame.destroy(self)
        return

    def load(self, uiRootNode, bgFrame = 'uiKartViewerFrame1', rightArrow = ['rotate_right_up',
 'rotate_right_down',
 'rotate_right_roll',
 'rotate_right_down',
 (0, 0)], leftArrow = ['rotate_left_up',
 'rotate_left_down',
 'rotate_left_roll',
 'rotate_left_down',
 (0, 0)], rotatePos = (0, 0)):
        self.uiBgFrame = DirectFrame(parent=self, relief=None, geom=uiRootNode.find('**/' + bgFrame), scale=1.0)
        if leftArrow and len(leftArrow) == 5:
            self.uiRotateLeft = DirectButton(parent=self, relief=None, geom=(uiRootNode.find('**/' + leftArrow[0]),
             uiRootNode.find('**/' + leftArrow[1]),
             uiRootNode.find('**/' + leftArrow[2]),
             uiRootNode.find('**/' + leftArrow[3])), scale=1.0, text=TTLocalizer.KartView_Left, text_scale=TTLocalizer.KProtateButton, text_pos=(leftArrow[4][0], leftArrow[4][1], 0), text_fg=(1, 1, 1, 1.0), text_shadow=(0, 0, 0, 1), text_font=ToontownGlobals.getSignFont(), pressEffect=False)
            self.uiRotateLeft.bind(DGG.B1PRESS, self.__handleKartRotate, [-3])
            self.uiRotateLeft.bind(DGG.B1RELEASE, self.__endKartRotate)
        if rightArrow and len(rightArrow) == 5:
            self.uiRotateRight = DirectButton(parent=self, relief=None, geom=(uiRootNode.find('**/' + rightArrow[0]),
             uiRootNode.find('**/' + rightArrow[1]),
             uiRootNode.find('**/' + rightArrow[2]),
             uiRootNode.find('**/' + rightArrow[3])), scale=1.0, text=TTLocalizer.KartView_Right, text_scale=TTLocalizer.KProtateButton, text_pos=(rightArrow[4][0], rightArrow[4][1], 0), text_fg=(1, 1, 1, 1.0), text_shadow=(0, 0, 0, 1), text_font=ToontownGlobals.getSignFont(), pressEffect=False)
            self.uiRotateRight.bind(DGG.B1PRESS, self.__handleKartRotate, [3])
            self.uiRotateRight.bind(DGG.B1RELEASE, self.__endKartRotate)
        return

    def setBounds(self, *bounds):
        self.bounds = bounds

    def setBgColor(self, *colors):
        self.colors = colors

    def makeKartFrame(self):
        if self.kart != None:
            self.kart.delete()
            self.kart = None
        if not hasattr(self, 'kartDisplayRegion'):
            self.kartDisplayRegion = DirectRegion(parent=self)
            self.kartDisplayRegion.setBounds(*self.bounds)
            self.kartDisplayRegion.setColor(*self.colors)
        frame = self.kartDisplayRegion.load()
        if self.dna:
            self.kart = Kart()
            self.kart.setDNA(self.dna)
            self.kart.generateKart(forGui=1)
            self.kart.setDepthTest(1)
            self.kart.setDepthWrite(1)
            self.pitch = frame.attachNewNode('pitch')
            self.rotate = self.pitch.attachNewNode('rotate')
            self.scale = self.rotate.attachNewNode('scale')
            self.kart.reparentTo(self.scale)
            bMin, bMax = self.kart.getKartBounds()
            center = (bMin + bMax) / 2.0
            self.kart.setPos(-center[0], -center[1], -center[2])
            self.scale.setScale(0.5)
            self.rotate.setH(-35)
            self.pitch.setP(0)
            self.pitch.setY(getKartViewDist(self.kart.getBodyType()))
            self.kart.setScale(1, 1, 1.5)
            self.kart.setTwoSided(1)
            if self.uiRotateRight:
                self.uiRotateRight.show()
            if self.uiRotateLeft:
                self.uiRotateLeft.show()
            if self.uiRotateLabel:
                self.uiRotateLabel.show()
        else:
            if self.uiRotateRight:
                self.uiRotateRight.hide()
            if self.uiRotateLeft:
                self.uiRotateLeft.hide()
            if self.uiRotateLabel:
                self.uiRotateLabel.hide()
        return frame

    def show(self, dna = None):
        if self.kartFrame:
            if self.kart != None:
                self.kart.delete()
                self.kart = None
            if hasattr(self, 'kartDisplayRegion'):
                self.kartDisplayRegion.unload()
            self.hide()
        self.uiBgFrame.show()
        self.refresh(dna)
        self.__handleKartRotate(1)
        return

    def hide(self):
        self.uiBgFrame.hide()
        if self.kart != None:
            self.kart.delete()
            self.kart = None
        if hasattr(self, 'kartDisplayRegion'):
            self.kartDisplayRegion.unload()
        return

    def __handleKartRotate(self, direction, extraArgs = []):
        taskMgr.add(self.__rotateTask, 'kartRotateTask', extraArgs=[direction])

    def __rotateTask(self, direction):
        if hasattr(self, 'pitch'):
            self.pitch.setH(self.pitch.getH() + 0.4 * direction)
            return Task.cont
        else:
            return Task.done

    def __endKartRotate(self, extraArgs = []):
        taskMgr.remove('kartRotateTask')

    def getKart(self):
        return self.kart

    def setDNA(self, dna):
        self.dna = dna

    def refresh(self, dna = None):
        taskMgr.removeTasksMatching('kartRotateTask')
        if dna:
            self.dna = dna
        curPitch = 0
        if hasattr(self, 'pitch'):
            curPitch = self.pitch.getH()
        else:
            curPitch = 0
        if self.kart != None:
            self.kart.delete()
            self.kart = None
        del self.kartFrame
        self.kartFrame = self.makeKartFrame()
        if hasattr(self, 'pitch'):
            self.pitch.setH(curPitch)
        return


class RacingTrophy(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('RacingTrophy')

    def __init__(self, level, *args, **kwargs):
        opts = {'relief': None}
        opts.update(kwargs)
        DirectFrame.__init__(self, *args, **opts)
        self.trophy = loader.loadModel('phase_6/models/gui/racingTrophy')
        self.trophy.reparentTo(self)
        self.trophy.setPos(0, 1, 0)
        self.trophy.setScale(0.1)
        self.base = self.trophy.find('**/trophyBase')
        self.column = self.trophy.find('**/trophyColumn')
        self.top = self.trophy.find('**/trophyTop')
        self.topBase = self.trophy.find('**/trophyTopBase')
        self.statue = self.trophy.find('**/trophyStatue')
        self.base.setColorScale(1, 1, 0.8, 1)
        self.topBase.setColorScale(1, 1, 0.8, 1)
        self.greyBowl = loader.loadModel('phase_6/models/gui/racingTrophyBowl2')
        self.greyBowl.reparentTo(self)
        self.greyBowl.setPos(0, 0.5, 0)
        self.greyBowl.setScale(2.0)
        self.goldBowl = loader.loadModel('phase_6/models/gui/racingTrophyBowl')
        self.goldBowl.reparentTo(self)
        self.goldBowl.setPos(0, 0.5, 0)
        self.goldBowl.setScale(2.0)
        self.goldBowlBase = self.goldBowl.find('**/fishingTrophyBase')
        self.goldBowlBase.hide()
        self.nameLabel = DirectLabel(parent=self, relief=None, pos=(0, 0, -0.15), text='', text_scale=0.125, text_fg=Vec4(0.9, 0.9, 0.4, 1))
        self.shadow = loader.loadModel('phase_3/models/props/drop_shadow')
        self.shadow.reparentTo(self)
        self.shadow.setColor(1, 1, 1, 0.2)
        self.shadow.setPosHprScale(0, 1, 0.35, 0, 90, 0, 0.1, 0.14, 0.1)
        self.setLevel(level)
        return

    def setLevel(self, level):
        self.level = level
        if level == -1:
            self.trophy.hide()
            self.greyBowl.hide()
            self.goldBowl.hide()
            self.nameLabel.hide()
        else:
            self.nameLabel.show()
            if level < 30 and level % 10 == 9:
                self.trophy.hide()
                self.goldBowl.hide()
                self.greyBowl.show()
                self.greyBowl.setScale(8.25, 3.5, 3.5)
            elif level >= 30:
                self.trophy.hide()
                self.greyBowl.hide()
                self.goldBowl.show()
                self.goldBowlBase.hide()
            else:
                self.trophy.show()
                self.goldBowl.hide()
                self.greyBowl.hide()
            if level == 30:
                self.goldBowl.setScale(4.4, 3.1, 3.1)
            elif level == 31:
                self.goldBowl.setScale(3.6, 3.5, 3.5)
            elif level >= 32:
                self.goldBowl.setScale(5.6, 3.9, 3.9)
            if level % 10 == 9:
                pass
            elif level % 10 % 3 == 0:
                self.column.setScale(1.3229, 1.26468, 1.11878)
                self.top.setPos(0, 0, -1)
                self.__bronze()
            elif level % 10 % 3 == 1:
                self.column.setScale(1.3229, 1.26468, 1.61878)
                self.top.setPos(0, 0, -.5)
                self.__silver()
            elif level % 10 % 3 == 2:
                self.column.setScale(1.3229, 1.26468, 2.11878)
                self.top.setPos(0, 0, 0)
                self.__gold()
            if level < 10:
                self.__tealColumn()
            elif level < 20:
                self.__purpleColumn()
            elif level < 30:
                self.__blueColumn()
            else:
                self.__redColumn()

    def __bronze(self):
        self.statue.setColorScale(0.9, 0.6, 0.33, 1)

    def __silver(self):
        self.statue.setColorScale(0.9, 0.9, 1, 1)

    def __gold(self):
        self.statue.setColorScale(1, 0.95, 0.1, 1)

    def __platinum(self):
        self.statue.setColorScale(1, 0.95, 0.1, 1)

    def __tealColumn(self):
        self.column.setColorScale(0.5, 1.2, 0.85, 1)

    def __purpleColumn(self):
        self.column.setColorScale(1, 0.7, 0.95, 1)

    def __redColumn(self):
        self.column.setColorScale(1.2, 0.6, 0.6, 1)

    def __yellowColumn(self):
        self.column.setColorScale(1, 1, 0.8, 1)

    def __blueColumn(self):
        self.column.setColorScale(0.6, 0.75, 1.2, 1)

    def destroy(self):
        self.trophy.removeNode()
        self.goldBowl.removeNode()
        self.greyBowl.removeNode()
        self.shadow.removeNode()
        DirectFrame.destroy(self)
