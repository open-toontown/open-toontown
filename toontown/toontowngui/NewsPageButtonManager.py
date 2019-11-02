from pandac.PandaModules import VBase4, VBase3
from direct.fsm import FSM
from direct.directnotify import DirectNotifyGlobal
from direct.gui.DirectButton import DirectButton
from toontown.toonbase import ToontownGlobals
from direct.gui.DirectGui import *
from direct.interval.IntervalGlobal import *
from toontown.toonbase import TTLocalizer
from toontown.coghq import CogHQBossBattle

class NewsPageButtonManager(FSM.FSM):
    notify = DirectNotifyGlobal.directNotify.newCategory('NewsPageButtonManager')

    def __init__(self):
        FSM.FSM.__init__(self, 'NewsPageButtonManager')
        self.buttonsLoaded = False
        self.clearGoingToNewsInfo()
        self.__blinkIval = None
        self.load()
        return

    def load(self):
        btnGui = loader.loadModel('phase_3.5/models/gui/tt_m_gui_ign_newsBtnGui')
        bookModel = loader.loadModel('phase_3.5/models/gui/tt_m_gui_ign_shtickerBook')
        self.openNewNewsUp = btnGui.find('**/tt_t_gui_ign_new')
        self.openNewNewsUpBlink = btnGui.find('**/tt_t_gui_ign_newBlink')
        self.openNewNewsHover = btnGui.find('**/tt_t_gui_ign_newHover')
        self.openOldNewsUp = btnGui.find('**/tt_t_gui_ign_oldNews')
        self.openOldNewsHover = btnGui.find('**/tt_t_gui_ign_oldHover')
        self.closeNewsUp = bookModel.find('**/tt_t_gui_sbk_newsPage1')
        self.closeNewsHover = bookModel.find('**/tt_t_gui_sbk_newsPage2')
        btnGui.removeNode()
        bookModel.removeNode()
        oldScale = 0.5
        newScale = 0.9
        shtickerBookScale = 0.305
        newPos = VBase3(0.914, 0, 0.862)
        shtickerBookPos = VBase3(1.175, 0, -0.83)
        textScale = 0.06
        self.newIssueButton = DirectButton(relief=None, sortOrder=DGG.BACKGROUND_SORT_INDEX - 1, image=(self.openNewNewsUp, self.openNewNewsHover, self.openNewNewsHover), text=('', TTLocalizer.EventsPageNewsTabName, TTLocalizer.EventsPageNewsTabName), text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1), text_scale=textScale, text_font=ToontownGlobals.getInterfaceFont(), pos=newPos, scale=newScale, command=self.__handleGotoNewsButton)
        self.gotoPrevPageButton = DirectButton(relief=None, image=(self.closeNewsUp, self.closeNewsHover, self.closeNewsHover), text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1), text_scale=textScale, text_font=ToontownGlobals.getInterfaceFont(), pos=shtickerBookPos, scale=shtickerBookScale, command=self.__handleGotoPrevPageButton)
        self.goto3dWorldButton = DirectButton(relief=None, image=(self.closeNewsUp, self.closeNewsHover, self.closeNewsHover), text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1), text_scale=textScale, text_font=ToontownGlobals.getInterfaceFont(), pos=shtickerBookPos, scale=shtickerBookScale, command=self.__handleGoto3dWorldButton)
        self.hideNewIssueButton()
        self.gotoPrevPageButton.hide()
        self.goto3dWorldButton.hide()
        self.accept('newIssueOut', self.handleNewIssueOut)
        bounce1Pos = VBase3(newPos.getX(), newPos.getY(), newPos.getZ() + 0.022)
        bounce2Pos = VBase3(newPos.getX(), newPos.getY(), newPos.getZ() + 0.015)
        bounceIval = Sequence(LerpPosInterval(self.newIssueButton, 0.1, bounce1Pos, blendType='easeOut'), LerpPosInterval(self.newIssueButton, 0.1, newPos, blendType='easeIn'), LerpPosInterval(self.newIssueButton, 0.07, bounce2Pos, blendType='easeOut'), LerpPosInterval(self.newIssueButton, 0.07, newPos, blendType='easeIn'))
        self.__blinkIval = Sequence(Func(self.__showOpenEyes), Wait(2), bounceIval, Wait(0.5), Func(self.__showClosedEyes), Wait(0.1), Func(self.__showOpenEyes), Wait(0.1), Func(self.__showClosedEyes), Wait(0.1))
        self.__blinkIval.loop()
        self.__blinkIval.pause()
        self.buttonsLoaded = True
        return

    def __showOpenEyes(self):
        self.newIssueButton['image'] = (self.openNewNewsUp, self.openNewNewsHover, self.openNewNewsHover)

    def __showClosedEyes(self):
        self.newIssueButton['image'] = (self.openNewNewsUpBlink, self.openNewNewsHover, self.openNewNewsHover)

    def clearGoingToNewsInfo(self):
        self.goingToNewsPageFrom3dWorld = False
        self.setGoingToNewsPageFromStickerBook(False)

    def __handleGotoNewsButton(self):
        currentState = base.localAvatar.animFSM.getCurrentState().getName()
        if currentState == 'jumpAirborne':
            return
        from toontown.toon import LocalToon
        if not LocalToon.WantNewsPage:
            return
        if base.cr and base.cr.playGame and base.cr.playGame.getPlace() and base.cr.playGame.getPlace().fsm:
            fsm = base.cr.playGame.getPlace().fsm
            curState = fsm.getCurrentState().getName()
            if curState == 'walk':
                if hasattr(localAvatar, 'newsPage'):
                    base.cr.centralLogger.writeClientEvent('news gotoNewsButton clicked')
                    localAvatar.book.setPage(localAvatar.newsPage)
                    fsm.request('stickerBook')
                    self.goingToNewsPageFrom3dWorld = True
            elif curState == 'stickerBook':
                if hasattr(localAvatar, 'newsPage'):
                    base.cr.centralLogger.writeClientEvent('news gotoNewsButton clicked')
                    fsm.request('stickerBook')
                    if hasattr(localAvatar, 'newsPage') and localAvatar.newsPage:
                        localAvatar.book.goToNewsPage(localAvatar.newsPage)

    def __handleGotoPrevPageButton(self):
        self.clearGoingToNewsInfo()
        localAvatar.book.setPageBeforeNews()
        self.showAppropriateButton()
        self.ignoreEscapeKeyPress()

    def __handleGoto3dWorldButton(self):
        localAvatar.book.closeBook()

    def hideNewIssueButton(self):
        if hasattr(self, 'newIssueButton') and self.newIssueButton:
            self.newIssueButton.hide()
            localAvatar.clarabelleNewsPageCollision(False)

    def __showNewIssueButton(self):
        self.newIssueButton.show()
        localAvatar.clarabelleNewsPageCollision(True)

    def hideAllButtons(self):
        if not self.buttonsLoaded:
            return
        self.gotoPrevPageButton.hide()
        self.goto3dWorldButton.hide()
        self.hideNewIssueButton()
        self.__blinkIval.pause()

    def isNewIssueButtonShown(self):
        if localAvatar.getLastTimeReadNews() < base.cr.inGameNewsMgr.getLatestIssue():
            return True
        return False

    def enterHidden(self):
        self.hideAllButtons()

    def exitHidden(self):
        pass

    def enterNormalWalk(self):
        if not self.buttonsLoaded:
            return
        if localAvatar.getLastTimeReadNews() < base.cr.inGameNewsMgr.getLatestIssue():
            self.__showNewIssueButton()
            self.__blinkIval.resume()
        else:
            self.hideNewIssueButton()
        self.gotoPrevPageButton.hide()
        self.goto3dWorldButton.hide()

    def exitNormalWalk(self):
        if not self.buttonsLoaded:
            return
        self.hideAllButtons()

    def enterGotoWorld(self):
        if not self.buttonsLoaded:
            return
        self.hideAllButtons()
        self.goto3dWorldButton.show()

    def exitGotoWorld(self):
        if not self.buttonsLoaded:
            return
        self.hideAllButtons()
        localAvatar.book.setPageBeforeNews(enterPage=False)
        self.clearGoingToNewsInfo()

    def enterPrevPage(self):
        if not self.buttonsLoaded:
            return
        self.hideAllButtons()
        self.gotoPrevPageButton.show()

    def exitPrevPage(self):
        if not self.buttonsLoaded:
            return
        self.hideAllButtons()

    def showAppropriateButton(self):
        self.notify.debugStateCall(self)
        from toontown.toon import LocalToon
        if not LocalToon.WantNewsPage:
            return
        if not self.buttonsLoaded:
            return
        if base.cr and base.cr.playGame and base.cr.playGame.getPlace() and hasattr(base.cr.playGame.getPlace(), 'fsm') and base.cr.playGame.getPlace().fsm:
            fsm = base.cr.playGame.getPlace().fsm
            curState = fsm.getCurrentState().getName()
            book = localAvatar.book
            if curState == 'walk':
                if localAvatar.tutorialAck and not localAvatar.isDisguised and not isinstance(base.cr.playGame.getPlace(), CogHQBossBattle.CogHQBossBattle):
                    self.request('NormalWalk')
                else:
                    self.request('Hidden')
            elif curState == 'stickerBook':
                if self.goingToNewsPageFrom3dWorld:
                    if localAvatar.tutorialAck:
                        self.request('GotoWorld')
                    else:
                        self.request('Hidden')
                elif self.goingToNewsPageFromStickerBook or hasattr(localAvatar, 'newsPage') and localAvatar.book.isOnPage(localAvatar.newsPage):
                    if localAvatar.tutorialAck:
                        self.request('PrevPage')
                    else:
                        self.request('Hidden')
                elif localAvatar.tutorialAck:
                    self.request('NormalWalk')
                else:
                    self.request('Hidden')

    def setGoingToNewsPageFromStickerBook(self, newVal):
        self.goingToNewsPageFromStickerBook = newVal

    def enterOff(self):
        self.ignoreAll()
        if not self.buttonsLoaded:
            return
        if self.__blinkIval:
            self.__blinkIval.finish()
            self.__blinkIval = None
        self.newIssueButton.destroy()
        self.gotoPrevPageButton.destroy()
        self.goto3dWorldButton.destroy()
        del self.openNewNewsUp
        del self.openNewNewsUpBlink
        del self.openNewNewsHover
        del self.openOldNewsUp
        del self.openOldNewsHover
        del self.closeNewsUp
        del self.closeNewsHover
        return

    def exitOff(self):
        self.notify.warning('Should not get here. NewsPageButtonManager.exitOff')

    def simulateEscapeKeyPress(self):
        if self.goingToNewsPageFrom3dWorld:
            self.__handleGoto3dWorldButton()
        if self.goingToNewsPageFromStickerBook:
            self.__handleGotoPrevPageButton()

    def handleNewIssueOut(self):
        if localAvatar.isReadingNews():
            pass
        else:
            self.showAppropriateButton()

    def acceptEscapeKeyPress(self):
        self.accept(ToontownGlobals.StickerBookHotkey, self.simulateEscapeKeyPress)
        self.accept(ToontownGlobals.OptionsPageHotkey, self.simulateEscapeKeyPress)

    def ignoreEscapeKeyPress(self):
        self.ignore(ToontownGlobals.StickerBookHotkey)
        self.ignore(ToontownGlobals.OptionsPageHotkey)
