from pandac.PandaModules import *
from direct.gui.DirectGui import *
from direct.gui import DirectGuiGlobals
from pandac.PandaModules import *
from direct.directnotify import DirectNotifyGlobal
from . import TTDialog
from toontown.toonbase import TTLocalizer
from direct.showbase import PythonUtil
from direct.showbase.DirectObject import DirectObject
from otp.login import LeaveToPayDialog
Pages = {'otherHoods': (TTLocalizer.TeaserOtherHoods,),
 'typeAName': (TTLocalizer.TeaserTypeAName,),
 'sixToons': (TTLocalizer.TeaserSixToons,),
 'otherGags': (TTLocalizer.TeaserOtherGags,),
 'clothing': (TTLocalizer.TeaserClothing,),
 'cogHQ': (TTLocalizer.TeaserCogHQ,),
 'secretChat': (TTLocalizer.TeaserSecretChat,),
 'quests': (TTLocalizer.TeaserQuests,),
 'emotions': (TTLocalizer.TeaserEmotions,),
 'minigames': (TTLocalizer.TeaserMinigames,),
 'karting': (TTLocalizer.TeaserKarting,),
 'kartingAccessories': (TTLocalizer.TeaserKartingAccessories,),
 'gardening': (TTLocalizer.TeaserGardening,),
 'tricks': (TTLocalizer.TeaserTricks,),
 'species': (TTLocalizer.TeaserSpecies,),
 'golf': (TTLocalizer.TeaserGolf,),
 'fishing': (TTLocalizer.TeaserFishing,),
 'parties': (TTLocalizer.TeaserParties,),
 'plantGags': (TTLocalizer.TeaserPlantGags,),
 'pickGags': (TTLocalizer.TeaserPickGags,),
 'restockGags': (TTLocalizer.TeaserRestockGags,),
 'getGags': (TTLocalizer.TeaserGetGags,),
 'useGags': (TTLocalizer.TeaserUseGags,)}
PageOrder = ['sixToons',
 'typeAName',
 'species',
 'otherHoods',
 'otherGags',
 'clothing',
 'parties',
 'tricks',
 'cogHQ',
 'secretChat',
 'quests',
 'emotions',
 'minigames',
 'karting',
 'kartingAccessories',
 'gardening',
 'golf',
 'fishing',
 'plantGags',
 'pickGags',
 'restockGags',
 'getGags',
 'useGags']

class TeaserPanel(DirectObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('TeaserPanel')

    def __init__(self, pageName, doneFunc = None):
        self.doneFunc = doneFunc
        if not hasattr(self, 'browser'):
            self.browser = FeatureBrowser()
            self.browser.load()
            self.browser.setPos(0, 0, TTLocalizer.TPbrowserPosZ)
            self.browser.setScale(0.75)
            self.browser.reparentTo(hidden)
        self.upsellBackground = loader.loadModel('phase_3/models/gui/tt_m_gui_ups_panelBg')
        self.leaveDialog = None
        self.showPage(pageName)
        self.ignore('exitingStoppedState')
        self.accept('exitingStoppedState', self.cleanup)
        return

    def __handleDone(self, choice = 0):
        self.cleanup()
        self.unload()
        if choice == 1:
            self.__handlePay()
        else:
            self.__handleContinue()

    def __handleContinue(self):
        if self.doneFunc:
            self.notify.debug('calling doneFunc')
            self.doneFunc()

    def __handlePay(self):
        if base.cr.isWebPlayToken() or __dev__:
            if self.leaveDialog == None:
                self.notify.debug('making LTP')
                self.leaveDialog = LeaveToPayDialog.LeaveToPayDialog(0, doneFunc=self.doneFunc)
            self.notify.debug('showing LTP')
            self.leaveDialog.show()
        else:
            self.notify.error('You should not have a TeaserPanel without a PlayToken')
        return

    def destroy(self):
        self.cleanup()

    def cleanup(self):
        if hasattr(self, 'browser'):
            self.browser.reparentTo(hidden)
            self.browser.ignoreAll()
        if hasattr(self, 'dialog'):
            base.transitions.noTransitions()
            self.dialog.cleanup()
            del self.dialog
        if self.leaveDialog:
            self.leaveDialog.destroy()
            self.leaveDialog = None
        self.ignoreAll()
        return

    def unload(self):
        if hasattr(self, 'browser'):
            self.browser.destroy()
            del self.browser

    def showPage(self, pageName):
        if pageName not in PageOrder:
            self.notify.error("unknown page '%s'" % pageName)
        base.cr.centralLogger.writeClientEvent('velvetRope: %s' % pageName)
        self.browser.scrollTo(PageOrder.index(pageName))
        self.cleanup()
        self.dialog = TTDialog.TTDialog(parent=aspect2dp, text=TTLocalizer.TeaserTop, text_scale=TTLocalizer.TPdialog, text_align=TextNode.ACenter, text_wordwrap=TTLocalizer.TPdialogWordwrap, topPad=-0.15, midPad=1.25, sidePad=0.25, pad=(0.25, 0.25), command=self.__handleDone, fadeScreen=0.5, style=TTDialog.TwoChoice, buttonTextList=[TTLocalizer.TeaserSubscribe, TTLocalizer.TeaserContinue], button_text_scale=TTLocalizer.TPbuttonTextList, buttonPadSF=5.5, sortOrder=DGG.NO_FADE_SORT_INDEX, image=self.upsellBackground)
        self.dialog.setPos(0, 0, 0.75)
        self.browser.reparentTo(self.dialog)
        base.transitions.fadeScreen(0.5)
        if base.config.GetBool('want-teaser-scroll-keys', 0):
            self.accept('arrow_right', self.showNextPage)
            self.accept('arrow_left', self.showPrevPage)
        self.accept('stoppedAsleep', self.__handleDone)

    def showNextPage(self):
        self.notify.debug('show next')
        self.browser.scrollBy(1)

    def showPrevPage(self):
        self.notify.debug('show prev')
        self.browser.scrollBy(-1)

    def showPay(self):
        self.dialog.buttonList[0].show()

    def hidePay(self):
        self.dialog.buttonList[0].hide()

    def removed(self):
        if hasattr(self, 'dialog') and self.dialog:
            return self.dialog.removed()
        elif hasattr(self, 'leaveDialog') and self.leaveDialog:
            return self.leaveDialog.removed()
        else:
            return 1


class FeatureBrowser(DirectScrolledList):

    def __init__(self, parent = aspect2dp, **kw):
        self._parent = parent
        optiondefs = (('parent', self._parent, None),
         ('relief', None, None),
         ('numItemsVisible', 1, None),
         ('items', [], None))
        self.defineoptions(kw, optiondefs)
        DirectScrolledList.__init__(self, parent)
        self.incButton.hide()
        self.decButton.hide()
        self.initialiseoptions(FeatureBrowser)
        return

    def destroy(self):
        DirectScrolledList.destroy(self)

    def load(self):
        guiModel = loader.loadModel('phase_3/models/gui/tt_m_gui_ups_logo_noText')
        leftLocator = guiModel.find('**/bubbleLeft_locator')
        rightLocator = guiModel.find('**/bubbleRight_locator')
        haveFunNode = TextNode('Have Fun')
        haveFunNode.setText(TTLocalizer.TeaserHaveFun)
        haveFunNode.setTextColor(0, 0, 0, 1)
        haveFunNode.setWordwrap(6)
        haveFunNode.setAlign(TextNode.ACenter)
        haveFunNode.setFont(DirectGuiGlobals.getDefaultFont())
        haveFun = NodePath(haveFunNode)
        haveFun.reparentTo(rightLocator)
        haveFun.setScale(TTLocalizer.TPhaveFun)
        JoinUsNode = TextNode('Join Us')
        JoinUsNode.setText(TTLocalizer.TeaserJoinUs)
        JoinUsNode.setTextColor(0, 0, 0, 1)
        JoinUsNode.setWordwrap(6)
        JoinUsNode.setAlign(TextNode.ACenter)
        JoinUsNode.setFont(DirectGuiGlobals.getDefaultFont())
        JoinUs = NodePath(JoinUsNode)
        JoinUs.reparentTo(leftLocator)
        JoinUs.setPos(0, 0, -0.025)
        JoinUs.setScale(TTLocalizer.TPjoinUs)
        for page in PageOrder:
            textInfo = Pages.get(page)
            textInfo = textInfo[0] + TTLocalizer.TeaserDefault
            panel = DirectFrame(parent=self, relief=None, image=guiModel, image_scale=(0.65, 0.65, 0.65), image_pos=(0, 0, 0.0), text_align=TextNode.ACenter, text=textInfo, text_scale=TTLocalizer.TPpanel, text_pos=TTLocalizer.TPpanelPos)
            self.addItem(panel)

        guiModel.removeNode()
        return
