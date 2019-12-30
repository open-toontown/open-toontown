from pandac.PandaModules import *
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from direct.gui.DirectScrolledList import *
from toontown.toonbase import ToontownGlobals
from toontown.toontowngui import TTDialog
from . import CatalogItem
from . import CatalogInvalidItem
from . import CatalogFurnitureItem
from toontown.toonbase import TTLocalizer
from . import CatalogItemPanel
from . import CatalogItemTypes
from direct.actor import Actor
import random
from toontown.toon import DistributedToon
from direct.directnotify import DirectNotifyGlobal
NUM_CATALOG_ROWS = 3
NUM_CATALOG_COLS = 2
CatalogPanelCenters = [[Point3(-0.95, 0, 0.91), Point3(-0.275, 0, 0.91)], [Point3(-0.95, 0, 0.275), Point3(-0.275, 0, 0.275)], [Point3(-0.95, 0, -0.4), Point3(-0.275, 0, -0.4)]]
CatalogPanelColors = {CatalogItemTypes.FURNITURE_ITEM: Vec4(0.733, 0.78, 0.933, 1.0),
 CatalogItemTypes.CHAT_ITEM: Vec4(0.922, 0.922, 0.753, 1.0),
 CatalogItemTypes.CLOTHING_ITEM: Vec4(0.918, 0.69, 0.69, 1.0),
 CatalogItemTypes.EMOTE_ITEM: Vec4(0.922, 0.922, 0.753, 1.0),
 CatalogItemTypes.WALLPAPER_ITEM: Vec4(0.749, 0.984, 0.608, 1.0),
 CatalogItemTypes.WINDOW_ITEM: Vec4(0.827, 0.91, 0.659, 1.0)}

class CatalogScreen(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('CatalogScreen')

    def __init__(self, parent = aspect2d, **kw):
        guiItems = loader.loadModel('phase_5.5/models/gui/catalog_gui')
        background = guiItems.find('**/catalog_background')
        guiButton = loader.loadModel('phase_3/models/gui/quit_button')
        guiBack = loader.loadModel('phase_5.5/models/gui/package_delivery_panel')
        optiondefs = (('scale', 0.667, None),
         ('pos', (0, 1, 0.025), None),
         ('phone', None, None),
         ('doneEvent', None, None),
         ('image', background, None),
         ('relief', None, None))
        self.defineoptions(kw, optiondefs)
        DirectFrame.__init__(self, parent)
        self.friendGiftIndex = 0
        self.friendGiftHandle = None
        self.frienddoId = None
        self.receiverName = 'Error Nameless Toon'
        self.friends = {}
        self.family = {}
        self.ffList = []
        self.textRolloverColor = Vec4(1, 1, 0, 1)
        self.textDownColor = Vec4(0.5, 0.9, 1, 1)
        self.textDisabledColor = Vec4(0.4, 0.8, 0.4, 1)
        self.giftAvatar = None
        self.gotAvatar = 0
        self.allowGetDetails = 1
        self.load(guiItems, guiButton, guiBack)
        self.initialiseoptions(CatalogScreen)
        self.enableBackorderCatalogButton()
        self.setMaxPageIndex(self.numNewPages)
        self.setPageIndex(-1)
        self.showPageItems()
        self.hide()
        self.clarabelleChatNP = None
        self.clarabelleChatBalloon = None
        self.gifting = -1
        self.createdGiftGui = None
        self.viewing = None
        return

    def show(self):
        self.accept('CatalogItemPurchaseRequest', self.__handlePurchaseRequest)
        self.accept('CatalogItemGiftPurchaseRequest', self.__handleGiftPurchaseRequest)
        self.accept(localAvatar.uniqueName('moneyChange'), self.__moneyChange)
        self.accept(localAvatar.uniqueName('bankMoneyChange'), self.__bankMoneyChange)
        self.accept(localAvatar.uniqueName('emblemsChange'), self.__emblemChange)
        deliveryText = 'setDeliverySchedule-%s' % base.localAvatar.doId
        self.accept(deliveryText, self.remoteUpdate)
        render.hide()
        DirectFrame.show(self)

        def clarabelleGreeting(task):
            self.setClarabelleChat(TTLocalizer.CatalogGreeting)

        def clarabelleHelpText1(task):
            self.setClarabelleChat(TTLocalizer.CatalogHelpText1)

        taskMgr.doMethodLater(1.0, clarabelleGreeting, 'clarabelleGreeting')
        taskMgr.doMethodLater(12.0, clarabelleHelpText1, 'clarabelleHelpText1')
        if hasattr(self, 'giftToggle'):
            self.giftToggle['state'] = DGG.DISABLED
            self.giftToggle['text'] = TTLocalizer.CatalogGiftToggleWait
        base.cr.deliveryManager.sendAck()
        self.accept('DeliveryManagerAck', self.__handleUDack)
        taskMgr.doMethodLater(10.0, self.__handleNoAck, 'ackTimeOut')

    def hide(self):
        self.ignore('CatalogItemPurchaseRequest')
        self.ignore('CatalogItemGiftPurchaseRequest')
        self.ignore('DeliveryManagerAck')
        taskMgr.remove('ackTimeOut')
        self.ignore(localAvatar.uniqueName('moneyChange'))
        self.ignore(localAvatar.uniqueName('bankMoneyChange'))
        self.ignore(localAvatar.uniqueName('emblemsChange'))
        deliveryText = 'setDeliverySchedule-%s' % base.localAvatar.doId
        self.ignore(deliveryText)
        render.show()
        DirectFrame.hide(self)

    def setNumNewPages(self, numNewPages):
        self.numNewPages = numNewPages

    def setNumBackPages(self, numBackPages):
        self.numBackPages = numBackPages

    def setNumLoyaltyPages(self, numLoyaltyPages):
        self.numLoyaltyPages = numLoyaltyPages

    def setNumEmblemPages(self, numEmblemPages):
        self.numEmblemPages = numEmblemPages

    def setPageIndex(self, index):
        self.pageIndex = index

    def setMaxPageIndex(self, numPages):
        self.maxPageIndex = max(numPages - 1, -1)

    def enableBackorderCatalogButton(self):
        self.backCatalogButton['state'] = DGG.NORMAL
        self.newCatalogButton['state'] = DGG.DISABLED
        self.loyaltyCatalogButton['state'] = DGG.DISABLED
        self.emblemCatalogButton['state'] = DGG.DISABLED

    def enableNewCatalogButton(self):
        self.backCatalogButton['state'] = DGG.DISABLED
        self.newCatalogButton['state'] = DGG.NORMAL
        self.loyaltyCatalogButton['state'] = DGG.DISABLED
        self.emblemCatalogButton['state'] = DGG.DISABLED

    def enableLoyaltyCatalogButton(self):
        self.backCatalogButton['state'] = DGG.DISABLED
        self.newCatalogButton['state'] = DGG.DISABLED
        self.loyaltyCatalogButton['state'] = DGG.NORMAL
        self.emblemCatalogButton['state'] = DGG.DISABLED

    def enableEmblemCatalogButton(self):
        self.backCatalogButton['state'] = DGG.DISABLED
        self.newCatalogButton['state'] = DGG.DISABLED
        self.loyaltyCatalogButton['state'] = DGG.DISABLED
        self.emblemCatalogButton['state'] = DGG.NORMAL

    def modeBackorderCatalog(self):
        self.backCatalogButton['state'] = DGG.DISABLED
        self.newCatalogButton['state'] = DGG.NORMAL
        self.loyaltyCatalogButton['state'] = DGG.NORMAL
        self.emblemCatalogButton['state'] = DGG.NORMAL

    def modeNewCatalog(self):
        self.backCatalogButton['state'] = DGG.NORMAL
        self.newCatalogButton['state'] = DGG.DISABLED
        self.loyaltyCatalogButton['state'] = DGG.NORMAL
        self.emblemCatalogButton['state'] = DGG.NORMAL

    def modeLoyaltyCatalog(self):
        self.backCatalogButton['state'] = DGG.NORMAL
        self.newCatalogButton['state'] = DGG.NORMAL
        self.loyaltyCatalogButton['state'] = DGG.DISABLED
        self.emblemCatalogButton['state'] = DGG.NORMAL

    def modeEmblemCatalog(self):
        self.backCatalogButton['state'] = DGG.NORMAL
        self.newCatalogButton['state'] = DGG.NORMAL
        self.loyaltyCatalogButton['state'] = DGG.NORMAL
        self.emblemCatalogButton['state'] = DGG.DISABLED

    def showNewItems(self, index = None):
        if base.config.GetBool('want-qa-regression', 0):
            self.notify.info('QA-REGRESSION: CATALOG: New item')
        taskMgr.remove('clarabelleHelpText1')
        messenger.send('wakeup')
        self.viewing = 'New'
        self.modeNewCatalog()
        self.setMaxPageIndex(self.numNewPages)
        if self.numNewPages == 0:
            self.setPageIndex(-1)
        elif index is not None:
            self.setPageIndex(index)
        else:
            self.setPageIndex(0)
        self.showPageItems()
        return

    def showBackorderItems(self, index = None):
        if base.config.GetBool('want-qa-regression', 0):
            self.notify.info('QA-REGRESSION: CATALOG: Backorder item')
        taskMgr.remove('clarabelleHelpText1')
        messenger.send('wakeup')
        self.viewing = 'Backorder'
        self.modeBackorderCatalog()
        self.setMaxPageIndex(self.numBackPages)
        if self.numBackPages == 0:
            self.setPageIndex(-1)
        elif index is not None:
            self.setPageIndex(index)
        else:
            self.setPageIndex(0)
        self.showPageItems()
        return

    def showLoyaltyItems(self, index = None):
        if base.config.GetBool('want-qa-regression', 0):
            self.notify.info('QA-REGRESSION: CATALOG: Special item')
        taskMgr.remove('clarabelleHelpText1')
        messenger.send('wakeup')
        self.viewing = 'Loyalty'
        self.modeLoyaltyCatalog()
        self.setMaxPageIndex(self.numLoyaltyPages)
        if self.numLoyaltyPages == 0:
            self.setPageIndex(-1)
        elif index is not None:
            self.setPageIndex(index)
        else:
            self.setPageIndex(0)
        self.showPageItems()
        return

    def showEmblemItems(self, index = None):
        if base.config.GetBool('want-qa-regression', 0):
            self.notify.info('QA-REGRESSION: CATALOG: Emblem item')
        taskMgr.remove('clarabelleHelpText1')
        messenger.send('wakeup')
        self.viewing = 'Emblem'
        self.modeEmblemCatalog()
        self.setMaxPageIndex(self.numEmblemPages)
        if self.numEmblemPages == 0:
            self.setPageIndex(-1)
        elif index is not None:
            self.setPageIndex(index)
        else:
            self.setPageIndex(0)
        self.showPageItems()
        return

    def showNextPage(self):
        taskMgr.remove('clarabelleHelpText1')
        messenger.send('wakeup')
        self.pageIndex = self.pageIndex + 1
        if self.viewing == None:
            self.modeNewCatalog()
            self.viewing == 'New'
        if self.viewing == 'New' and self.pageIndex > self.maxPageIndex and self.numBackPages > 0:
            self.showBackorderItems()
        if self.viewing == 'New' and self.pageIndex > self.maxPageIndex and self.numLoyaltyPages > 0:
            self.showLoyaltyItems()
        elif self.viewing == 'Backorder' and self.pageIndex > self.maxPageIndex and self.numLoyaltyPages > 0:
            self.showLoyaltyItems()
        elif self.viewing == 'Loyalty' and self.pageIndex > self.maxPageIndex and self.numEmblemPages > 0:
            self.showEmblemItems()
        else:
            self.pageIndex = min(self.pageIndex, self.maxPageIndex)
            self.showPageItems()
        return

    def showBackPage(self):
        taskMgr.remove('clarabelleHelpText1')
        messenger.send('wakeup')
        self.pageIndex = self.pageIndex - 1
        if self.viewing == 'Backorder' and self.pageIndex < 0 and self.numNewPages > 0:
            self.showNewItems(self.numNewPages - 1)
        elif self.viewing == 'Loyalty' and self.pageIndex < 0 and self.numBackPages > 0:
            self.showBackorderItems(self.numBackPages - 1)
        elif self.viewing == 'Emblem' and self.pageIndex < 0 and self.numLoyaltyPages > 0:
            self.showLoyaltyItems(self.numLoyaltyPages - 1)
        else:
            self.pageIndex = max(self.pageIndex, -1)
            self.showPageItems()

    def showPageItems(self):
        self.hidePages()
        if self.viewing == None:
            self.viewing = 'New'
        if self.pageIndex < 0:
            self.closeCover()
        else:
            if self.pageIndex == 0:
                self.openCover()
            if self.viewing == 'New':
                page = self.pageList[self.pageIndex]
                newOrBackOrLoyalty = 0
            elif self.viewing == 'Backorder':
                page = self.backPageList[self.pageIndex]
                newOrBackOrLoyalty = 1
            elif self.viewing == 'Loyalty':
                page = self.loyaltyPageList[self.pageIndex]
                newOrBackOrLoyalty = 2
            elif self.viewing == 'Emblem':
                page = self.emblemPageList[self.pageIndex]
                newOrBackOrLoyalty = 3
            page.show()
            for panel in self.panelDict[page.id()]:
                panel.load()
                if panel.ival:
                    panel.ival.loop()
                self.visiblePanels.append(panel)

            pIndex = 0
            randGen = random.Random()
            randGen.seed(base.localAvatar.catalogScheduleCurrentWeek + (self.pageIndex << 8) + (newOrBackOrLoyalty << 16))
            for i in range(NUM_CATALOG_ROWS):
                for j in range(NUM_CATALOG_COLS):
                    if pIndex < len(self.visiblePanels):
                        type = self.visiblePanels[pIndex]['item'].getTypeCode()
                        self.squares[i][j].setColor(list(CatalogPanelColors.values())[randGen.randint(0, len(CatalogPanelColors) - 1)])
                        cs = 0.7 + 0.3 * randGen.random()
                        self.squares[i][j].setColorScale(0.7 + 0.3 * randGen.random(), 0.7 + 0.3 * randGen.random(), 0.7 + 0.3 * randGen.random(), 1)
                    else:
                        self.squares[i][j].setColor(CatalogPanelColors[CatalogItemTypes.CHAT_ITEM])
                        self.squares[i][j].clearColorScale()
                    pIndex += 1

            if self.viewing == 'New':
                text = TTLocalizer.CatalogNew
            elif self.viewing == 'Loyalty':
                text = TTLocalizer.CatalogLoyalty
            elif self.viewing == 'Backorder':
                text = TTLocalizer.CatalogBackorder
            elif self.viewing == 'Emblem':
                text = TTLocalizer.CatalogEmblem
            self.pageLabel['text'] = text + ' - %d' % (self.pageIndex + 1)
            if self.pageIndex < self.maxPageIndex:
                self.nextPageButton.show()
            elif self.viewing == 'New' and self.numBackPages == 0 and self.numLoyaltyPages == 0:
                self.nextPageButton.hide()
            elif self.viewing == 'Backorder' and self.numLoyaltyPages == 0:
                self.nextPageButton.hide()
            elif self.viewing == 'Loyalty' and self.numEmblemPages == 0:
                self.nextPageButton.hide()
            elif self.viewing == 'Loyalty' and self.numEmblemPages > 0:
                self.nextPageButton.show()
            elif self.viewing == 'Emblem':
                self.nextPageButton.hide()
            self.adjustForSound()
            self.update()
        return

    def adjustForSound(self):
        numEmoteItems = 0
        emotePanels = []
        for visIndex in range(len(self.visiblePanels)):
            panel = self.visiblePanels[visIndex]
            item = panel['item']
            catalogType = item.getTypeCode()
            if catalogType == CatalogItemTypes.EMOTE_ITEM:
                numEmoteItems += 1
                emotePanels.append(panel)
            else:
                panel.soundOnButton.hide()
                panel.soundOffButton.hide()

        if numEmoteItems == 1:
            emotePanels[0].handleSoundOnButton()
        elif numEmoteItems > 1:
            for panel in emotePanels:
                panel.handleSoundOffButton()

    def hidePages(self):
        for page in self.pageList:
            page.hide()

        for page in self.backPageList:
            page.hide()

        for page in self.loyaltyPageList:
            page.hide()

        for page in self.emblemPageList:
            page.hide()

        for panel in self.visiblePanels:
            if panel.ival:
                panel.ival.finish()

        self.visiblePanels = []

    def openCover(self):
        self.cover.hide()
        self.hideDummyTabs()
        self.backPageButton.show()
        self.pageLabel.show()

    def closeCover(self):
        self.cover.show()
        self.showDummyTabs()
        self.nextPageButton.show()
        self.backPageButton.hide()
        self.pageLabel.hide()
        self.hidePages()

    def showDummyTabs(self):
        if self.numNewPages > 0:
            self.newCatalogButton2.show()
        if self.numBackPages > 0:
            self.backCatalogButton2.show()
        if self.numLoyaltyPages > 0:
            self.loyaltyCatalogButton2.show()
        if self.numEmblemPages > 0:
            self.emblemCatalogButton2.show()
        self.newCatalogButton.hide()
        self.backCatalogButton.hide()
        self.loyaltyCatalogButton.hide()
        self.emblemCatalogButton.hide()

    def hideDummyTabs(self):
        self.newCatalogButton2.hide()
        self.backCatalogButton2.hide()
        self.loyaltyCatalogButton2.hide()
        self.emblemCatalogButton2.hide()
        if self.numNewPages > 0:
            self.newCatalogButton.show()
        if self.numBackPages > 0:
            self.backCatalogButton.show()
        if self.numLoyaltyPages > 0:
            self.loyaltyCatalogButton.show()
        if self.numEmblemPages > 0:
            self.emblemCatalogButton.show()

    def packPages(self, panelList, pageList, prefix):
        i = 0
        j = 0
        numPages = 0
        pageName = prefix + '_page%d' % numPages
        for item in panelList:
            if i == 0 and j == 0:
                numPages += 1
                pageName = prefix + '_page%d' % numPages
                page = self.base.attachNewNode(pageName)
                pageList.append(page)
            item.reparentTo(page)
            item.setPos(CatalogPanelCenters[i][j])
            itemList = self.panelDict.get(page.id(), [])
            itemList.append(item)
            self.panelDict[page.id()] = itemList
            j += 1
            if j == NUM_CATALOG_COLS:
                j = 0
                i += 1
            if i == NUM_CATALOG_ROWS:
                i = 0

        return numPages

    def load(self, guiItems, guiButton, guiBack):
        self.pageIndex = -1
        self.maxPageIndex = 0
        self.numNewPages = 0
        self.numBackPages = 5
        self.numLoyaltyPages = 0
        self.viewing = 'New'
        self.panelList = []
        self.backPanelList = []
        self.pageList = []
        self.backPageList = []
        self.loyaltyPanelList = []
        self.loyaltyPageList = []
        self.emblemPanelList = []
        self.emblemPageList = []
        self.panelDict = {}
        self.visiblePanels = []
        self.responseDialog = None
        catalogBase = guiItems.find('**/catalog_base')
        self.base = DirectLabel(self, relief=None, image=catalogBase)
        newDown = guiItems.find('**/new1')
        newUp = guiItems.find('**/new2')
        backDown = guiItems.find('**/previous2')
        backUp = guiItems.find('**/previous1')
        giftToggleUp = guiItems.find('**/giftButtonUp')
        giftToggleDown = guiItems.find('**/giftButtonDown')
        giftFriends = guiItems.find('**/gift_names')
        oldLift = 0.4
        lift = 0.4
        liftDiff = lift - oldLift
        lift2 = 0.05
        smash = 0.75
        priceScale = 0.15
        emblemIcon = loader.loadModel('phase_3.5/models/gui/tt_m_gui_gen_emblemIcons')
        silverModel = emblemIcon.find('**/tt_t_gui_gen_emblemSilver')
        goldModel = emblemIcon.find('**/tt_t_gui_gen_emblemGold')
        self.silverLabel = DirectLabel(parent=self, relief=None, pos=(1.05, 0, -0.6), scale=priceScale, image=silverModel, image_pos=(-0.4, 0, 0.4), text=str(localAvatar.emblems[ToontownGlobals.EmblemTypes.Silver]), text_fg=(0.95, 0.95, 0, 1), text_shadow=(0, 0, 0, 1), text_font=ToontownGlobals.getSignFont(), text_align=TextNode.ALeft)
        base.silverLabel = self.silverLabel
        self.goldLabel = DirectLabel(parent=self, relief=None, pos=(1.05, 0, -0.8), scale=priceScale, image=goldModel, image_pos=(-0.4, 0, 0.4), text=str(localAvatar.emblems[ToontownGlobals.EmblemTypes.Gold]), text_fg=(0.95, 0.95, 0, 1), text_shadow=(0, 0, 0, 1), text_font=ToontownGlobals.getSignFont(), text_align=TextNode.ALeft)
        base.goldLabel = self.goldLabel
        if not base.cr.wantEmblems:
            self.hideEmblems()
        self.newCatalogButton = DirectButton(self.base, relief=None, pos=(0, 0, 0.17), frameSize=(-0.2,
         0.25,
         0.45,
         1.2), image=[newDown,
         newDown,
         newDown,
         newUp], image_scale=(1.0, 1.0, smash), image_pos=(0.0, 0.0, lift), pressEffect=0, command=self.showNewItems, text=TTLocalizer.CatalogNew, text_font=ToontownGlobals.getSignFont(), text_pos=(-0.4 - lift, 0.13), text3_pos=(-0.4 - lift, 0.1), text_scale=0.08, text_fg=(0.353, 0.627, 0.627, 1.0), text2_fg=(0.353, 0.427, 0.427, 1.0))
        self.newCatalogButton.hide()
        self.newCatalogButton2 = DirectButton(self.base, relief=None, pos=(0, 0, 0.17), frameSize=(-0.2,
         0.25,
         0.45,
         1.2), image=newDown, image_scale=(1.0, 1.0, smash), image_pos=(0.0, 0.0, lift), pressEffect=0, command=self.showNewItems, text=TTLocalizer.CatalogNew, text_font=ToontownGlobals.getSignFont(), text_pos=(-0.4 - lift, 0.13), text_scale=0.08, text_fg=(0.353, 0.627, 0.627, 1.0), text2_fg=(0.353, 0.427, 0.427, 1.0))
        self.newCatalogButton2.hide()
        self.backCatalogButton = DirectButton(self.base, relief=None, pos=(0, 0, 0.269), frameSize=(-0.2,
         0.25,
         -0.2,
         0.4), image=[backDown,
         backDown,
         backDown,
         backUp], image_scale=(1.0, 1.0, smash), image_pos=(0.0, 0.0, lift), pressEffect=0, command=self.showBackorderItems, text=TTLocalizer.CatalogBackorder, text_font=ToontownGlobals.getSignFont(), text_pos=(0.25 - lift, 0.132), text3_pos=(0.25 - lift, 0.112), text_scale=TTLocalizer.CSbackCatalogButton, text_fg=(0.392, 0.549, 0.627, 1.0), text2_fg=(0.392, 0.349, 0.427, 1.0))
        self.backCatalogButton.hide()
        self.backCatalogButton2 = DirectButton(self.base, relief=None, pos=(0, 0, 0.269), frameSize=(-0.2,
         0.25,
         -0.2,
         0.4), image_scale=(1.0, 1.0, smash), image_pos=(0.0, 0.0, lift), image=backDown, pressEffect=0, command=self.showBackorderItems, text=TTLocalizer.CatalogBackorder, text_font=ToontownGlobals.getSignFont(), text_pos=(0.25 - lift, 0.132), text_scale=TTLocalizer.CSbackCatalogButton, text_fg=(0.392, 0.549, 0.627, 1.0), text2_fg=(0.392, 0.349, 0.427, 1.0))
        self.backCatalogButton2.hide()
        self.loyaltyCatalogButton = DirectButton(self.base, relief=None, pos=(0, 0, 0.469), frameSize=(-0.2,
         0.25,
         -0.85,
         -0.3), image=[newDown,
         newDown,
         newDown,
         newUp], image_scale=(1.0, 1.0, smash), image_pos=(0.0, 0.0, -1.4 + lift), pressEffect=0, command=self.showLoyaltyItems, text=TTLocalizer.CatalogLoyalty, text_font=ToontownGlobals.getSignFont(), text_pos=(1.0 - lift, 0.132), text3_pos=(1.0 - lift, 0.112), text_scale=0.065, text_fg=(0.353, 0.627, 0.627, 1.0), text2_fg=(0.353, 0.427, 0.427, 1.0))
        self.loyaltyCatalogButton.hide()
        self.loyaltyCatalogButton2 = DirectButton(self.base, relief=None, pos=(0, 0, 0.469), frameSize=(-0.2,
         0.25,
         -0.85,
         -0.3), image_scale=(1.0, 1.0, smash), image_pos=(0.0, 0.0, -1.4 + lift), image=newDown, pressEffect=0, command=self.showLoyaltyItems, text=TTLocalizer.CatalogLoyalty, text_font=ToontownGlobals.getSignFont(), text_pos=(1.0 - lift, 0.132), text_scale=0.065, text_fg=(0.353, 0.627, 0.627, 1.0), text2_fg=(0.353, 0.427, 0.427, 1.0))
        self.loyaltyCatalogButton2.hide()
        self.emblemCatalogButton = DirectButton(self.base, relief=None, pos=(0, 0, 1.05), frameSize=(-0.2,
         0.25,
         -2.0,
         -1.45), image=[backDown,
         backDown,
         backDown,
         backUp], image_scale=(1.0, 1.0, smash), image_pos=(0.0, 0.0, -1.9 + lift), pressEffect=0, command=self.showEmblemItems, text=TTLocalizer.CatalogEmblem, text_font=ToontownGlobals.getSignFont(), text_pos=(1.75, 0.132), text3_pos=(1.75, 0.112), text_scale=0.065, text_fg=(0.353, 0.627, 0.627, 1.0), text2_fg=(0.353, 0.427, 0.427, 1.0))
        self.emblemCatalogButton.hide()
        self.emblemCatalogButton2 = DirectButton(self.base, relief=None, pos=(0, 0, 1.05), frameSize=(-0.2,
         0.25,
         -2.0,
         -1.45), image_scale=(1.0, 1.0, smash), image_pos=(0.0, 0.0, -1.9 + lift), image=backDown, pressEffect=0, command=self.showEmblemItems, text=TTLocalizer.CatalogEmblem, text_font=ToontownGlobals.getSignFont(), text_pos=(1.75, 0.132), text_scale=0.065, text_fg=(0.353, 0.627, 0.627, 1.0), text2_fg=(0.353, 0.427, 0.427, 1.0))
        self.emblemCatalogButton2.hide()
        self.__makeFFlist()
        if len(self.ffList) > 0:
            self.giftToggle = DirectButton(self.base, relief=None, pressEffect=0, image=(giftToggleUp, giftToggleDown, giftToggleUp), image_scale=(1.0, 1, 0.7), command=self.__giftToggle, text=TTLocalizer.CatalogGiftToggleOff, text_font=ToontownGlobals.getSignFont(), text_pos=TTLocalizer.CSgiftTogglePos, text_scale=TTLocalizer.CSgiftToggle, text_fg=(0.353, 0.627, 0.627, 1.0), text3_fg=(0.15, 0.3, 0.3, 1.0), text2_fg=(0.353, 0.427, 0.427, 1.0), image_color=Vec4(1.0, 1.0, 0.2, 1.0), image1_color=Vec4(0.9, 0.85, 0.2, 1.0), image2_color=Vec4(0.9, 0.85, 0.2, 1.0), image3_color=Vec4(0.5, 0.45, 0.2, 1.0))
            self.giftToggle.setPos(0.0, 0, -0.035)
            self.giftLabel = DirectLabel(self.base, relief=None, image=giftFriends, image_scale=(1.15, 1, 1.14), text=' ', text_font=ToontownGlobals.getSignFont(), text_pos=(1.2, -0.97), text_scale=0.07, text_fg=(0.392, 0.549, 0.627, 1.0), sortOrder=100, textMayChange=1)
            self.giftLabel.setPos(-0.15, 0, 0.08)
            self.giftLabel.hide()
            self.friendLabel = DirectLabel(self.base, relief=None, text='Friend Name', text_font=ToontownGlobals.getSignFont(), text_pos=(-0.25, 0.132), text_scale=0.068, text_align=TextNode.ALeft, text_fg=(0.992, 0.949, 0.327, 1.0), sortOrder=100, textMayChange=1)
            self.friendLabel.setPos(0.5, 0, -0.42)
            self.friendLabel.hide()
            gui = loader.loadModel('phase_3.5/models/gui/friendslist_gui')
            self.scrollList = DirectScrolledList(parent=self, relief=None, incButton_image=(gui.find('**/FndsLst_ScrollUp'),
             gui.find('**/FndsLst_ScrollDN'),
             gui.find('**/FndsLst_ScrollUp_Rllvr'),
             gui.find('**/FndsLst_ScrollUp')), incButton_relief=None, incButton_pos=(0.0, 0.0, -0.316), incButton_image1_color=Vec4(1.0, 0.9, 0.4, 1.0), incButton_image3_color=Vec4(1.0, 1.0, 0.6, 0.5), incButton_scale=(1.0, 1.0, -1.0), decButton_image=(gui.find('**/FndsLst_ScrollUp'),
             gui.find('**/FndsLst_ScrollDN'),
             gui.find('**/FndsLst_ScrollUp_Rllvr'),
             gui.find('**/FndsLst_ScrollUp')), decButton_relief=None, decButton_pos=(0.0, 0.0, 0.117), decButton_image1_color=Vec4(1.0, 1.0, 0.6, 1.0), decButton_image3_color=Vec4(1.0, 1.0, 0.6, 0.6), itemFrame_pos=(-0.17, 0.0, 0.06), itemFrame_relief=None, numItemsVisible=8, items=[])
            self.scrollList.setPos(1.2, 0, -0.58)
            self.scrollList.setScale(1.5)
            self.scrollList.hide()
            clipper = PlaneNode('clipper')
            clipper.setPlane(Plane(Vec3(-1, 0, 0), Point3(0.17, 0, 0)))
            clipNP = self.scrollList.attachNewNode(clipper)
            self.scrollList.setClipPlane(clipNP)
            self.__makeScrollList()
            friendId = self.ffList[0]
            self.__chooseFriend(self.ffList[0][0], self.ffList[0][1])
            self.update()
            self.createdGiftGui = 1
        for i in range(4):
            self.newCatalogButton.component('text%d' % i).setR(90)
            self.newCatalogButton2.component('text%d' % i).setR(90)
            self.backCatalogButton.component('text%d' % i).setR(90)
            self.backCatalogButton2.component('text%d' % i).setR(90)
            self.loyaltyCatalogButton.component('text%d' % i).setR(90)
            self.loyaltyCatalogButton2.component('text%d' % i).setR(90)
            self.emblemCatalogButton.component('text%d' % i).setR(90)
            self.emblemCatalogButton2.component('text%d' % i).setR(90)

        self.squares = [[],
         [],
         [],
         []]
        for i in range(NUM_CATALOG_ROWS):
            for j in range(NUM_CATALOG_COLS):
                square = guiItems.find('**/square%d%db' % (i + 1, j + 1))
                label = DirectLabel(self.base, image=square, relief=None, state='normal')
                self.squares[i].append(label)

        def priceSort(a, b, type):
            priceA = a.getPrice(type)
            priceB = b.getPrice(type)
            return priceB - priceA

        itemList = base.localAvatar.monthlyCatalog + base.localAvatar.weeklyCatalog
        itemList.sort(lambda a, b: priceSort(a, b, CatalogItem.CatalogTypeWeekly))
        itemList.reverse()
        allClosetItems = CatalogFurnitureItem.getAllClosets()
        isMaxClosetOfferred = False
        for item in itemList:
            if item in allClosetItems and item.furnitureType in CatalogFurnitureItem.MaxClosetIds:
                isMaxClosetOfferred = True
                break

        for item in itemList:
            if isinstance(item, CatalogInvalidItem.CatalogInvalidItem):
                self.notify.warning('skipping catalog invalid item %s' % item)
                continue
            if isMaxClosetOfferred and item in allClosetItems and item.furnitureType not in CatalogFurnitureItem.MaxClosetIds:
                continue
            if item.loyaltyRequirement() != 0:
                self.loyaltyPanelList.append(CatalogItemPanel.CatalogItemPanel(parent=hidden, item=item, type=CatalogItem.CatalogTypeLoyalty, parentCatalogScreen=self))
            elif item.getEmblemPrices():
                self.emblemPanelList.append(CatalogItemPanel.CatalogItemPanel(parent=hidden, item=item, type=CatalogItem.CatalogTypeWeekly, parentCatalogScreen=self))
            else:
                self.panelList.append(CatalogItemPanel.CatalogItemPanel(parent=hidden, item=item, type=CatalogItem.CatalogTypeWeekly, parentCatalogScreen=self))

        itemList = base.localAvatar.backCatalog
        itemList.sort(lambda a, b: priceSort(a, b, CatalogItem.CatalogTypeBackorder))
        itemList.reverse()
        for item in itemList:
            if isinstance(item, CatalogInvalidItem.CatalogInvalidItem):
                self.notify.warning('skipping catalog invalid item %s' % item)
                continue
            if isMaxClosetOfferred and item in allClosetItems and item.furnitureType not in CatalogFurnitureItem.MaxClosetIds:
                continue
            if item.loyaltyRequirement() != 0:
                self.loyaltyPanelList.append(CatalogItemPanel.CatalogItemPanel(parent=hidden, item=item, type=CatalogItem.CatalogTypeLoyalty, parentCatalogScreen=self))
            elif item.getEmblemPrices():
                self.emblemPanelList.append(CatalogItemPanel.CatalogItemPanel(parent=hidden, item=item, type=CatalogItem.CatalogTypeBackOrder, parentCatalogScreen=self))
            else:
                self.backPanelList.append(CatalogItemPanel.CatalogItemPanel(parent=hidden, item=item, type=CatalogItem.CatalogTypeBackorder, parentCatalogScreen=self))

        numPages = self.packPages(self.panelList, self.pageList, 'new')
        self.setNumNewPages(numPages)
        numPages = self.packPages(self.backPanelList, self.backPageList, 'back')
        self.setNumBackPages(numPages)
        numPages = self.packPages(self.loyaltyPanelList, self.loyaltyPageList, 'loyalty')
        self.setNumLoyaltyPages(numPages)
        numPages = self.packPages(self.emblemPanelList, self.emblemPageList, 'emblem')
        self.setNumEmblemPages(numPages)
        currentWeek = base.localAvatar.catalogScheduleCurrentWeek - 1
        if currentWeek < 57:
            seriesNumber = currentWeek / ToontownGlobals.CatalogNumWeeksPerSeries + 1
            weekNumber = currentWeek % ToontownGlobals.CatalogNumWeeksPerSeries + 1
        elif currentWeek < 65:
            seriesNumber = 6
            weekNumber = currentWeek - 56
        else:
            seriesNumber = currentWeek / ToontownGlobals.CatalogNumWeeksPerSeries + 2
            weekNumber = currentWeek % ToontownGlobals.CatalogNumWeeksPerSeries + 1
        geom = NodePath('cover')
        cover = guiItems.find('**/cover')
        maxSeries = ToontownGlobals.CatalogNumWeeks / ToontownGlobals.CatalogNumWeeksPerSeries + 1
        coverSeries = (seriesNumber - 1) % maxSeries + 1
        coverPicture = cover.find('**/cover_picture%s' % coverSeries)
        if not coverPicture.isEmpty():
            coverPicture.reparentTo(geom)
        bottomSquare = cover.find('**/cover_bottom')
        topSquare = guiItems.find('**/square12b2')
        if seriesNumber == 1:
            topSquare.setColor(0.651, 0.404, 0.322, 1.0)
            bottomSquare.setColor(0.655, 0.522, 0.263, 1.0)
        else:
            topSquare.setColor(0.651, 0.404, 0.322, 1.0)
            bottomSquare.setColor(0.655, 0.522, 0.263, 1.0)
        bottomSquare.reparentTo(geom)
        topSquare.reparentTo(geom)
        cover.find('**/clarabelle_text').reparentTo(geom)
        cover.find('**/blue_circle').reparentTo(geom)
        cover.find('**/clarabelle').reparentTo(geom)
        cover.find('**/circle_green').reparentTo(geom)
        self.cover = DirectLabel(self.base, relief=None, geom=geom)
        self.catalogNumber = DirectLabel(self.cover, relief=None, scale=0.2, pos=(-0.22, 0, -0.33), text='#%d' % weekNumber, text_fg=(0.95, 0.95, 0, 1), text_shadow=(0, 0, 0, 1), text_font=ToontownGlobals.getInterfaceFont())
        self.catalogSeries = DirectLabel(self.cover, relief=None, scale=(0.22, 1, 0.18), pos=(-0.76, 0, -0.9), text=TTLocalizer.CatalogSeriesLabel % seriesNumber, text_fg=(0.9, 0.9, 0.4, 1), text_shadow=(0, 0, 0, 1), text_font=ToontownGlobals.getInterfaceFont())
        self.catalogSeries.setShxz(0.4)
        self.rings = DirectLabel(self.base, relief=None, geom=guiItems.find('**/rings'))
        self.clarabelleFrame = DirectLabel(self, relief=None, image=guiItems.find('**/clarabelle_frame'))
        hangupGui = guiItems.find('**/hangup')
        hangupRolloverGui = guiItems.find('**/hangup_rollover')
        self.hangup = DirectButton(self, relief=None, pos=(1.78, 0, -1.3), image=[hangupGui,
         hangupRolloverGui,
         hangupRolloverGui,
         hangupGui], text=['', TTLocalizer.CatalogHangUp, TTLocalizer.CatalogHangUp], text_fg=Vec4(1), text_scale=0.07, text_pos=(0.0, 0.14), command=self.hangUp)
        self.beanBank = DirectLabel(self, relief=None, image=guiItems.find('**/bean_bank'), text=str(base.localAvatar.getMoney() + base.localAvatar.getBankMoney()), text_align=TextNode.ARight, text_scale=0.11, text_fg=(0.95, 0.95, 0, 1), text_shadow=(0, 0, 0, 1), text_pos=(0.75, -0.81), text_font=ToontownGlobals.getSignFont())
        nextUp = guiItems.find('**/arrow_up')
        nextRollover = guiItems.find('**/arrow_Rollover')
        nextDown = guiItems.find('**/arrow_Down')
        prevUp = guiItems.find('**/arrowUp')
        prevDown = guiItems.find('**/arrowDown1')
        prevRollover = guiItems.find('**/arrowRollover')
        self.nextPageButton = DirectButton(self, relief=None, pos=(-0.1, 0, -0.9), image=[nextUp,
         nextDown,
         nextRollover,
         nextUp], image_color=(0.9, 0.9, 0.9, 1), image2_color=(1, 1, 1, 1), command=self.showNextPage)
        self.backPageButton = DirectButton(self, relief=None, pos=(-0.1, 0, -0.9), image=[prevUp,
         prevDown,
         prevRollover,
         prevUp], image_color=(0.9, 0.9, 0.9, 1), image2_color=(1, 1, 1, 1), command=self.showBackPage)
        self.backPageButton.hide()
        self.pageLabel = DirectLabel(self.base, relief=None, pos=(-1.33, 0, -0.9), scale=0.06, text=TTLocalizer.CatalogPagePrefix, text_fg=(0.95, 0.95, 0, 1), text_shadow=(0, 0, 0, 1), text_font=ToontownGlobals.getSignFont(), text_align=TextNode.ALeft)
        self.loadClarabelle()
        return

    def loadClarabelle(self):
        self.cRender = NodePath('cRender')
        self.cCamera = self.cRender.attachNewNode('cCamera')
        self.cCamNode = Camera('cCam')
        self.cLens = PerspectiveLens()
        self.cLens.setFov(40, 40)
        self.cLens.setNear(0.1)
        self.cLens.setFar(100.0)
        self.cCamNode.setLens(self.cLens)
        self.cCamNode.setScene(self.cRender)
        self.cCam = self.cCamera.attachNewNode(self.cCamNode)
        self.cDr = base.win.makeDisplayRegion(0.58, 0.82, 0.53, 0.85)
        self.cDr.setSort(1)
        self.cDr.setClearDepthActive(1)
        self.cDr.setClearColorActive(1)
        self.cDr.setClearColor(Vec4(0.3, 0.3, 0.3, 1))
        self.cDr.setCamera(self.cCam)
        self.clarabelle = Actor.Actor('phase_5.5/models/char/Clarabelle-zero', {'listen': 'phase_5.5/models/char/Clarabelle-listens'})
        self.clarabelle.loop('listen')
        self.clarabelle.find('**/eyes').setBin('fixed', 0)
        self.clarabelle.find('**/pupilL').setBin('fixed', 1)
        self.clarabelle.find('**/pupilR').setBin('fixed', 1)
        self.clarabelle.find('**/glassL').setBin('fixed', 2)
        self.clarabelle.find('**/glassR').setBin('fixed', 2)
        switchboard = loader.loadModel('phase_5.5/models/estate/switchboard')
        switchboard.reparentTo(self.clarabelle)
        switchboard.setPos(0, -2, 0)
        self.clarabelle.reparentTo(self.cRender)
        self.clarabelle.setPosHprScale(-0.56, 6.43, -3.81, 121.61, 0.0, 0.0, 1.0, 1.0, 1.0)
        self.clarabelleFrame.setPosHprScale(-0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0)

    def reload(self):
        for panel in self.panelList + self.backPanelList + self.loyaltyPanelList + self.emblemPanelList:
            panel.destroy()

        def priceSort(a, b, type):
            priceA = a.getPrice(type)
            priceB = b.getPrice(type)
            return priceB - priceA

        self.pageIndex = -1
        self.maxPageIndex = 0
        self.numNewPages = 0
        self.numBackPages = 5
        self.numLoyaltyPages = 0
        self.viewing = 'New'
        self.panelList = []
        self.backPanelList = []
        self.loyaltyList = []
        self.pageList = []
        self.backPageList = []
        self.loyaltyPanelList = []
        self.loyaltyPageList = []
        self.panelDict = {}
        self.visiblePanels = []
        itemList = base.localAvatar.monthlyCatalog + base.localAvatar.weeklyCatalog
        itemList.sort(lambda a, b: priceSort(a, b, CatalogItem.CatalogTypeWeekly))
        itemList.reverse()
        for item in itemList:
            if item.loyaltyRequirement() != 0:
                self.loyaltyPanelList.append(CatalogItemPanel.CatalogItemPanel(parent=hidden, item=item, type=CatalogItem.CatalogTypeLoyalty, parentCatalogScreen=self))
            else:
                self.panelList.append(CatalogItemPanel.CatalogItemPanel(parent=hidden, item=item, type=CatalogItem.CatalogTypeWeekly))

        itemList = base.localAvatar.backCatalog
        itemList.sort(lambda a, b: priceSort(a, b, CatalogItem.CatalogTypeBackorder))
        itemList.reverse()
        for item in itemList:
            if item.loyaltyRequirement() != 0:
                self.loyaltyPanelList.append(CatalogItemPanel.CatalogItemPanel(parent=hidden, item=item, type=CatalogItem.CatalogTypeLoyalty, parentCatalogScreen=self))
            else:
                self.backPanelList.append(CatalogItemPanel.CatalogItemPanel(parent=hidden, item=item, type=CatalogItem.CatalogTypeBackorder))

        numPages = self.packPages(self.panelList, self.pageList, 'new')
        self.setNumNewPages(numPages)
        numPages = self.packPages(self.backPanelList, self.backPageList, 'back')
        self.setNumBackPages(numPages)
        numPages = self.packPages(self.loyaltyPanelList, self.loyaltyPageList, 'loyalty')
        self.setNumLoyaltyPages(numPages)
        seriesNumber = (base.localAvatar.catalogScheduleCurrentWeek - 1) / ToontownGlobals.CatalogNumWeeksPerSeries + 1
        self.catalogSeries['text'] = Localizer.CatalogSeriesLabel % seriesNumber
        weekNumber = (base.localAvatar.catalogScheduleCurrentWeek - 1) % ToontownGlobals.CatalogNumWeeksPerSeries + 1
        self.catalogNumber['text'] = '#%d' % weekNumber
        self.enableBackorderCatalogButton()
        self.setMaxPageIndex(self.numNewPages)
        self.setPageIndex(-1)
        self.showPageItems()

    def unload(self):
        taskMgr.remove('clearClarabelleChat')
        taskMgr.remove('postGoodbyeHangUp')
        taskMgr.remove('clarabelleGreeting')
        taskMgr.remove('clarabelleHelpText1')
        taskMgr.remove('clarabelleAskAnythingElse')
        if self.giftAvatar:
            base.cr.cancelAvatarDetailsRequest(self.giftAvatar)
        self.hide()
        self.destroy()
        del self.base
        del self.squares
        for panel in self.panelList + self.backPanelList + self.loyaltyPanelList + self.emblemPanelList:
            panel.destroy()

        del self.panelList
        del self.backPanelList
        del self.cover
        del self.rings
        del self.clarabelleFrame
        del self.hangup
        del self.beanBank
        del self.silverLabel
        del self.goldLabel
        del self.nextPageButton
        del self.backPageButton
        del self.newCatalogButton
        del self.newCatalogButton2
        del self.backCatalogButton
        del self.backCatalogButton2
        del self.loyaltyCatalogButton
        del self.loyaltyCatalogButton2
        del self.pageLabel
        if self.createdGiftGui:
            del self.giftToggle
            del self.giftLabel
            del self.friendLabel
            del self.scrollList
        self.unloadClarabelle()
        if self.responseDialog:
            self.responseDialog.cleanup()
            self.responseDialog = None
        if self.giftAvatar:
            if hasattr(self.giftAvatar, 'doId'):
                self.giftAvatar.delete()
            else:
                self.giftAvatar = None
        return

    def unloadClarabelle(self):
        base.win.removeDisplayRegion(self.cDr)
        del self.cRender
        del self.cCamera
        del self.cCamNode
        del self.cLens
        del self.cCam
        del self.cDr
        self.clarabelle.cleanup()
        del self.clarabelle

    def hangUp(self):
        if hasattr(self, 'giftAvatar') and self.giftAvatar:
            self.giftAvatar.disable()
        self.setClarabelleChat(random.choice(TTLocalizer.CatalogGoodbyeList))
        self.setPageIndex(-1)
        self.showPageItems()
        self.nextPageButton.hide()
        self.backPageButton.hide()
        self.newCatalogButton.hide()
        self.newCatalogButton2.hide()
        self.backCatalogButton.hide()
        self.backCatalogButton2.hide()
        self.loyaltyCatalogButton.hide()
        self.loyaltyCatalogButton2.hide()
        self.emblemCatalogButton.hide()
        self.emblemCatalogButton2.hide()
        self.hangup.hide()
        taskMgr.remove('clarabelleGreeting')
        taskMgr.remove('clarabelleHelpText1')
        taskMgr.remove('clarabelleAskAnythingElse')

        def postGoodbyeHangUp(task):
            messenger.send(self['doneEvent'])
            self.unload()

        taskMgr.doMethodLater(1.5, postGoodbyeHangUp, 'postGoodbyeHangUp')

    def remoteUpdate(self):
        self.update()

    def update(self, lock = 0):
        if not hasattr(self.giftAvatar, 'doId'):
            if self.gifting == 1:
                self.__giftToggle()
        if hasattr(self, 'beanBank'):
            self.beanBank['text'] = str(base.localAvatar.getTotalMoney())
            if lock == 0:
                for item in self.panelList + self.backPanelList + self.loyaltyPanelList + self.emblemPanelList:
                    if type(item) != type(''):
                        item.updateButtons(self.gifting)

    def __handlePurchaseRequest(self, item):
        item.requestPurchase(self['phone'], self.__handlePurchaseResponse)
        taskMgr.remove('clarabelleAskAnythingElse')

    def __handleGiftPurchaseRequest(self, item):
        item.requestGiftPurchase(self['phone'], self.frienddoId, self.__handleGiftPurchaseResponse)
        taskMgr.remove('clarabelleAskAnythingElse')

    def __handlePurchaseResponse(self, retCode, item):
        if retCode == ToontownGlobals.P_UserCancelled:
            self.update()
            return
        self.setClarabelleChat(item.getRequestPurchaseErrorText(retCode), item.getRequestPurchaseErrorTextTimeout())

    def __handleGiftPurchaseResponse(self, retCode, item):
        if retCode == ToontownGlobals.P_UserCancelled:
            return
        if self.isEmpty() or self.isHidden():
            return
        self.setClarabelleChat(item.getRequestGiftPurchaseErrorText(retCode) % self.receiverName)
        self.__loadFriend()

        def askAnythingElse(task):
            self.setClarabelleChat(TTLocalizer.CatalogAnythingElse)

        if retCode >= 0:
            taskMgr.doMethodLater(8, askAnythingElse, 'clarabelleAskAnythingElse')

    def __clearDialog(self, event):
        self.responseDialog.cleanup()
        self.responseDialog = None
        return

    def setClarabelleChat(self, str, timeout = 6):
        self.clearClarabelleChat()
        if not self.clarabelleChatBalloon:
            self.clarabelleChatBalloon = loader.loadModel('phase_3/models/props/chatbox.bam')
        self.clarabelleChat = ChatBalloon(self.clarabelleChatBalloon.node())
        chatNode = self.clarabelleChat.generate(str, ToontownGlobals.getInterfaceFont(), 10, Vec4(0, 0, 0, 1), Vec4(1, 1, 1, 1), 0, 0, 0, NodePath(), 0, 0, NodePath())
        self.clarabelleChatNP = self.attachNewNode(chatNode, 1000)
        self.clarabelleChatNP.setScale(0.08)
        self.clarabelleChatNP.setPos(0.7, 0, 0.6)
        if timeout:
            taskMgr.doMethodLater(timeout, self.clearClarabelleChat, 'clearClarabelleChat')

    def clearClarabelleChat(self, task = None):
        taskMgr.remove('clearClarabelleChat')
        if self.clarabelleChatNP:
            self.clarabelleChatNP.removeNode()
            self.clarabelleChatNP = None
            del self.clarabelleChat
        return

    def __moneyChange(self, money):
        if self.gifting > 0:
            self.update(1)
        else:
            self.update(0)

    def __bankMoneyChange(self, bankMoney):
        if self.gifting > 0:
            self.update(1)
        else:
            self.update(0)

    def __emblemChange(self, newEmblems):
        self.silverLabel['text'] = str(newEmblems[0])
        self.goldLabel['text'] = str(newEmblems[1])

    def showEmblems(self):
        if base.cr.wantEmblems:
            self.silverLabel.show()
            self.goldLabel.show()

    def hideEmblems(self):
        self.silverLabel.hide()
        self.goldLabel.hide()

    def checkFamily(self, doId):
        test = 0
        for familyMember in base.cr.avList:
            if familyMember.id == doId:
                test = 1

        return test

    def __makeFFlist(self):
        for familyMember in base.cr.avList:
            if familyMember.id != base.localAvatar.doId:
                newFF = (familyMember.id, familyMember.name, NametagGroup.CCNonPlayer)
                self.ffList.append(newFF)

        for friendPair in base.localAvatar.friendsList:
            friendId, flags = friendPair
            handle = base.cr.identifyFriend(friendId)
            if handle and not self.checkFamily(friendId):
                if hasattr(handle, 'getName'):
                    colorCode = NametagGroup.CCSpeedChat
                    if flags & ToontownGlobals.FriendChat:
                        colorCode = NametagGroup.CCFreeChat
                    newFF = (friendPair[0], handle.getName(), colorCode)
                    self.ffList.append(newFF)
                else:
                    self.notify.warning('Bad Handle for getName in makeFFlist')

        hasManager = hasattr(base.cr, 'playerFriendsManager')
        if hasManager:
            for avatarId in base.cr.playerFriendsManager.getAllOnlinePlayerAvatars():
                handle = base.cr.playerFriendsManager.getAvHandleFromId(avatarId)
                playerId = base.cr.playerFriendsManager.findPlayerIdFromAvId(avatarId)
                playerInfo = base.cr.playerFriendsManager.getFriendInfo(playerId)
                freeChat = playerInfo.understandableYesNo
                if handle and not self.checkFamily(avatarId):
                    if hasattr(handle, 'getName'):
                        colorCode = NametagGroup.CCSpeedChat
                        if freeChat:
                            colorCode = NametagGroup.CCFreeChat
                        newFF = (avatarId, handle.getName(), colorCode)
                        self.ffList.append(newFF)
                    else:
                        self.notify.warning('Bad Handle for getName in makeFFlist')

    def __makeScrollList(self):
        for ff in self.ffList:
            ffbutton = self.makeFamilyButton(ff[0], ff[1], ff[2])
            if ffbutton:
                self.scrollList.addItem(ffbutton, refresh=0)
                self.friends[ff] = ffbutton

        self.scrollList.refresh()

    def makeFamilyButton(self, familyId, familyName, colorCode):
        fg = NametagGlobals.getNameFg(colorCode, PGButton.SInactive)
        return DirectButton(relief=None, text=familyName, text_scale=0.04, text_align=TextNode.ALeft, text_fg=fg, text1_bg=self.textDownColor, text2_bg=self.textRolloverColor, text3_fg=self.textDisabledColor, textMayChange=0, command=self.__chooseFriend, extraArgs=[familyId, familyName])

    def __chooseFriend(self, friendId, friendName):
        messenger.send('wakeup')
        self.frienddoId = friendId
        self.receiverName = friendName
        self.friendLabel['text'] = TTLocalizer.CatalogGiftTo % self.receiverName
        self.__loadFriend()

    def __loadFriend(self):
        if self.allowGetDetails == 0:
            CatalogScreen.notify.warning('smashing requests')
        if self.frienddoId and self.allowGetDetails:
            if self.giftAvatar:
                if hasattr(self.giftAvatar, 'doId'):
                    self.giftAvatar.disable()
                    self.giftAvatar.delete()
                self.giftAvatar = None
            self.giftAvatar = DistributedToon.DistributedToon(base.cr)
            self.giftAvatar.doId = self.frienddoId
            self.giftAvatar.forceAllowDelayDelete()
            self.giftAvatar.generate()
            base.cr.getAvatarDetails(self.giftAvatar, self.__handleAvatarDetails, 'DistributedToon')
            self.gotAvatar = 0
            self.allowGetDetails = 0
            self.scrollList['state'] = DGG.DISABLED
        return

    def __handleAvatarDetails(self, gotData, avatar, dclass):
        if self.giftAvatar.doId != avatar.doId or gotData == 0:
            CatalogScreen.notify.error('Get Gift Avatar Failed')
            self.gotAvatar = 0
            return
        else:
            self.gotAvatar = 1
            self.giftAvatar = avatar
            self.scrollList['state'] = DGG.NORMAL
        self.allowGetDetails = 1
        self.update()

    def __giftToggle(self):
        messenger.send('wakeup')
        if self.gifting == -1:
            self.gifting = 1
            self.giftLabel.show()
            self.friendLabel.show()
            self.scrollList.show()
            self.hideEmblems()
            self.giftToggle['text'] = TTLocalizer.CatalogGiftToggleOn
            self.__loadFriend()
        else:
            self.gifting = -1
            self.giftLabel.hide()
            self.friendLabel.hide()
            self.scrollList.hide()
            self.showEmblems()
            self.giftToggle['text'] = TTLocalizer.CatalogGiftToggleOff
            self.update()

    def __handleUDack(self, caller = None):
        taskMgr.remove('ackTimeOut')
        if hasattr(self, 'giftToggle') and self.giftToggle:
            self.giftToggle['state'] = DGG.NORMAL
            self.giftToggle['text'] = TTLocalizer.CatalogGiftToggleOff

    def __handleNoAck(self, caller = None):
        if hasattr(self, 'giftToggle') and self.giftToggle:
            self.giftToggle['text'] = TTLocalizer.CatalogGiftToggleNoAck
