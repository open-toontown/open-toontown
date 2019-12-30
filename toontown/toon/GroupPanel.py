from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from direct.showbase import DirectObject
from toontown.toon import ToonAvatarPanel
from toontown.toontowngui import TTDialog

class GroupPanel(DirectObject.DirectObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('GroupPanel')

    def __init__(self, boardingParty):
        self.boardingParty = boardingParty
        self.leaderId = self.boardingParty.getGroupLeader(localAvatar.doId)
        self.elevatorIdList = self.boardingParty.getElevatorIdList()
        self.frame = None
        self.confirmQuitDialog = None
        self.goButton = None
        self.destScrollList = None
        self.destFrame = None
        self.goingToLabel = None
        self.destIndexSelected = 0
        self.__load()
        self.ignore('stickerBookEntered')
        self.accept('stickerBookEntered', self.__forceHide)
        self.ignore('stickerBookExited')
        self.accept('stickerBookExited', self.__forceShow)
        return

    def cleanup(self):
        base.setCellsAvailable(base.leftCells, 1)
        self.quitButton.destroy()
        self.hideButton.destroy()
        self.showButton.destroy()
        self.scrollList.destroy()
        if self.goButton:
            self.goButton.destroy()
            self.goButton = None
        if self.destScrollList:
            self.destScrollList.destroy()
            self.destScrollList = None
        if self.destFrame:
            self.destFrame.destroy()
            self.destFrame = None
        if self.goingToLabel:
            self.goingToLabel.destroy()
            self.goingToLabel = None
        if self.frame:
            self.frame.destroy()
            self.frame = None
        self.leaveButton = None
        self.boardingParty = None
        self.ignoreAll()
        return

    def __load(self):
        self.guiBg = loader.loadModel('phase_9/models/gui/tt_m_gui_brd_groupListBg')
        self.__defineConstants()
        if self.boardingParty.maxSize == 4:
            bgImage = self.guiBg.find('**/tt_t_gui_brd_memberListTop_half')
            bgImageZPos = 0.14
            frameZPos = -0.121442
            quitButtonZPos = -0.019958
        else:
            bgImage = self.guiBg.find('**/tt_t_gui_brd_memberListTop')
            bgImageZPos = 0
            frameZPos = 0.0278943
            quitButtonZPos = -0.30366
        guiButtons = loader.loadModel('phase_9/models/gui/tt_m_gui_brd_status')
        self.frame = DirectFrame(relief=None, image=bgImage, image_scale=(0.5, 1, 0.5), image_pos=(0, 0, bgImageZPos), textMayChange=1, pos=(-1.044, 0, frameZPos))
        self.frameBounds = self.frame.getBounds()
        leaveButtonGui = loader.loadModel('phase_3.5/models/gui/tt_m_gui_brd_leaveBtn')
        leaveImageList = (leaveButtonGui.find('**/tt_t_gui_brd_leaveUp'),
         leaveButtonGui.find('**/tt_t_gui_brd_leaveDown'),
         leaveButtonGui.find('**/tt_t_gui_brd_leaveHover'),
         leaveButtonGui.find('**/tt_t_gui_brd_leaveUp'))
        self.leaderButtonImage = guiButtons.find('**/tt_t_gui_brd_statusLeader')
        self.availableButtonImage = guiButtons.find('**/tt_t_gui_brd_statusOn')
        self.battleButtonImage = guiButtons.find('**/tt_t_gui_brd_statusBattle')
        if localAvatar.doId == self.leaderId:
            quitText = TTLocalizer.QuitBoardingPartyLeader
        else:
            quitText = TTLocalizer.QuitBoardingPartyNonLeader
        self.disabledOrangeColor = Vec4(1, 0.5, 0.25, 0.9)
        self.quitButton = DirectButton(parent=self.frame, relief=None, image=leaveImageList, image_scale=0.065, command=self.__handleLeaveButton, text=('',
         quitText,
         quitText,
         ''), text_scale=0.06, text_fg=Vec4(1, 1, 1, 1), text_shadow=Vec4(0, 0, 0, 1), text_pos=(0.045, 0.0), text_align=TextNode.ALeft, pos=(0.223, 0, quitButtonZPos), image3_color=self.disabledOrangeColor)
        arrowGui = loader.loadModel('phase_9/models/gui/tt_m_gui_brd_arrow')
        hideImageList = (arrowGui.find('**/tt_t_gui_brd_arrow_up'), arrowGui.find('**/tt_t_gui_brd_arrow_down'), arrowGui.find('**/tt_t_gui_brd_arrow_hover'))
        showImageList = (arrowGui.find('**/tt_t_gui_brd_arrow_up'), arrowGui.find('**/tt_t_gui_brd_arrow_down'), arrowGui.find('**/tt_t_gui_brd_arrow_hover'))
        self.hideButton = DirectButton(relief=None, text_pos=(0, 0.15), text_scale=0.06, text_align=TextNode.ALeft, text_fg=Vec4(0, 0, 0, 1), text_shadow=Vec4(1, 1, 1, 1), image=hideImageList, image_scale=(-0.35, 1, 0.5), pos=(-1.3081, 0, 0.03), scale=1.05, command=self.hide)
        self.showButton = DirectButton(relief=None, text=('', TTLocalizer.BoardingGroupShow, TTLocalizer.BoardingGroupShow), text_pos=(0.03, 0), text_scale=0.06, text_align=TextNode.ALeft, text_fg=Vec4(1, 1, 1, 1), text_shadow=Vec4(0, 0, 0, 1), image=showImageList, image_scale=(0.35, 1, 0.5), pos=(-1.3081, 0, 0.03), scale=1.05, command=self.show)
        self.showButton.hide()
        self.frame.show()
        self.__makeAvatarNameScrolledList()
        if localAvatar.doId == self.leaderId:
            self.__makeDestinationScrolledList()
        else:
            self.__makeDestinationFrame()
        self.__makeGoingToLabel()
        self.accept('updateGroupStatus', self.__checkGroupStatus)
        self.accept('ToonBattleIdUpdate', self.__possibleGroupUpdate)
        base.setCellsAvailable([base.leftCells[1], base.leftCells[2]], 0)
        if self.boardingParty.isGroupLeader(localAvatar.doId):
            base.setCellsAvailable([base.leftCells[0]], 0)
        self.__addTestNames(self.boardingParty.maxSize)
        self.guiBg.removeNode()
        guiButtons.removeNode()
        leaveButtonGui.removeNode()
        arrowGui.removeNode()
        return

    def __defineConstants(self):
        self.forcedHidden = False
        self.textFgcolor = NametagGlobals.getNameFg(NametagGroup.CCSpeedChat, PGButton.SInactive)
        self.textBgRolloverColor = Vec4(1, 1, 0, 1)
        self.textBgDownColor = Vec4(0.5, 0.9, 1, 1)
        self.textBgDisabledColor = Vec4(0.4, 0.8, 0.4, 1)

    def __handleLeaveButton(self):
        messenger.send('wakeup')
        if not base.cr.playGame.getPlace().getState() == 'elevator':
            self.confirmQuitDialog = TTDialog.TTDialog(style=TTDialog.YesNo, text=TTLocalizer.QuitBoardingPartyConfirm, command=self.__confirmQuitCallback)
            self.confirmQuitDialog.show()

    def __confirmQuitCallback(self, value):
        if self.confirmQuitDialog:
            self.confirmQuitDialog.destroy()
        self.confirmQuitDialog = None
        if value > 0:
            if self.boardingParty:
                self.boardingParty.requestLeave()
        return

    def __handleGoButton(self):
        offset = self.destScrollList.getSelectedIndex()
        elevatorId = self.elevatorIdList[offset]
        self.boardingParty.requestGoToFirstTime(elevatorId)

    def __handleCancelGoButton(self):
        self.boardingParty.cancelGoToElvatorDest()

    def __checkGroupStatus(self):
        if not self.boardingParty:
            return
        self.notify.debug('__checkGroupStatus %s' % self.boardingParty.getGroupMemberList(localAvatar.doId))
        myMemberList = self.boardingParty.getGroupMemberList(localAvatar.doId)
        self.scrollList.removeAndDestroyAllItems(refresh=0)
        if myMemberList:
            for avId in myMemberList:
                avatarButton = self.__getAvatarButton(avId)
                if avatarButton:
                    self.scrollList.addItem(avatarButton, refresh=0)

            self.scrollList.refresh()

    def __possibleGroupUpdate(self, avId):
        self.notify.debug('GroupPanel __possibleGroupUpdate')
        if not self.boardingParty:
            return
        myMemberList = self.boardingParty.getGroupMemberList(localAvatar.doId)
        if avId in myMemberList:
            self.__checkGroupStatus()

    def __makeAvatarNameScrolledList(self):
        friendsListGui = loader.loadModel('phase_3.5/models/gui/friendslist_gui')
        self.scrollList = DirectScrolledList(parent=self.frame, relief=None, incButton_image=(friendsListGui.find('**/FndsLst_ScrollUp'),
         friendsListGui.find('**/FndsLst_ScrollDN'),
         friendsListGui.find('**/FndsLst_ScrollUp_Rllvr'),
         friendsListGui.find('**/FndsLst_ScrollUp')), incButton_pos=(0.0, 0.0, -0.35), incButton_image1_color=Vec4(1.0, 0.9, 0.4, 0), incButton_image3_color=Vec4(1.0, 1.0, 0.6, 0), incButton_scale=(1.0, 1.0, -1.0), incButton_relief=None, decButton_image=(friendsListGui.find('**/FndsLst_ScrollUp'),
         friendsListGui.find('**/FndsLst_ScrollDN'),
         friendsListGui.find('**/FndsLst_ScrollUp_Rllvr'),
         friendsListGui.find('**/FndsLst_ScrollUp')), decButton_pos=(0.0, 0.0, 0.1), decButton_image1_color=Vec4(1.0, 1.0, 0.6, 0), decButton_image3_color=Vec4(1.0, 1.0, 0.6, 0), decButton_relief=None, itemFrame_pos=(-0.195, 0.0, 0.185), itemFrame_borderWidth=(0.1, 0.1), numItemsVisible=8, itemFrame_scale=1.0, forceHeight=0.07, items=[], pos=(0, 0, 0.075))
        clipper = PlaneNode('clipper')
        clipper.setPlane(Plane(Vec3(-1, 0, 0), Point3(0.235, 0, 0)))
        clipNP = self.scrollList.attachNewNode(clipper)
        self.scrollList.setClipPlane(clipNP)
        friendsListGui.removeNode()
        return

    def __makeDestinationScrolledList(self):
        arrowGui = loader.loadModel('phase_9/models/gui/tt_m_gui_brd_gotoArrow')
        incrementImageList = (arrowGui.find('**/tt_t_gui_brd_arrowL_gotoUp'),
         arrowGui.find('**/tt_t_gui_brd_arrowL_gotoDown'),
         arrowGui.find('**/tt_t_gui_brd_arrowL_gotoHover'),
         arrowGui.find('**/tt_t_gui_brd_arrowL_gotoUp'))
        if self.boardingParty.maxSize == 4:
            zPos = -0.177083
        else:
            zPos = -0.463843
        bottomImage = self.guiBg.find('**/tt_t_gui_brd_memberListBtm_leader')
        self.destScrollList = DirectScrolledList(
            parent=self.frame,
            relief=None,
            image=bottomImage,
            image_scale=(0.5, 1, 0.5),
            incButton_image=incrementImageList,
            incButton_pos=(0.217302, 0, 0.07),
            incButton_image3_color=Vec4(1.0, 1.0, 0.6, 0.5),
            incButton_scale=(-0.5, 1, 0.5),
            incButton_relief=None,
            incButtonCallback=self.__informDestChange,
            decButton_image=incrementImageList,
            decButton_pos=(-0.217302, 0, 0.07),
            decButton_scale=(0.5, 1, 0.5),
            decButton_image3_color=Vec4(1.0, 1.0, 0.6, 0.5),
            decButton_relief=None,
            decButtonCallback=self.__informDestChange,
            itemFrame_pos=(0, 0, 0.06),
            itemFrame_borderWidth=(0.1, 0.1),
            numItemsVisible=1,
            itemFrame_scale=TTLocalizer.GPdestScrollList,
            forceHeight=0.07,
            items=[],
            pos=(0, 0, zPos),
            scrollSpeed=0.1)
        arrowGui.removeNode()
        self.__addDestNames()
        self.__makeGoButton()
        return

    def __addDestNames(self):
        for i in range(len(self.elevatorIdList)):
            destName = self.__getDestName(i)
            self.destScrollList.addItem(destName, refresh=0)

        self.destScrollList.refresh()

    def __getDestName(self, offset):
        elevatorId = self.elevatorIdList[offset]
        elevator = base.cr.doId2do.get(elevatorId)
        if elevator:
            destName = elevator.getDestName()
        return destName

    def __makeDestinationFrame(self):
        destName = self.__getDestName(self.destIndexSelected)
        if self.boardingParty.maxSize == 4:
            zPos = -0.12
        else:
            zPos = -0.404267
        bottomImage = self.guiBg.find('**/tt_t_gui_brd_memberListBtm_nonLeader')
        self.destFrame = DirectFrame(parent=self.frame, relief=None, image=bottomImage, image_scale=(0.5, 1, 0.5), text=destName, text_align=TextNode.ACenter, text_scale=TTLocalizer.GPdestFrame, pos=(0, 0, zPos))
        return

    def __makeGoButton(self):
        goGui = loader.loadModel('phase_9/models/gui/tt_m_gui_brd_gotoBtn')
        self.goImageList = (goGui.find('**/tt_t_gui_brd_gotoUp'),
         goGui.find('**/tt_t_gui_brd_gotoDown'),
         goGui.find('**/tt_t_gui_brd_gotoHover'),
         goGui.find('**/tt_t_gui_brd_gotoUp'))
        self.cancelGoImageList = (goGui.find('**/tt_t_gui_brd_cancelGotoUp'),
         goGui.find('**/tt_t_gui_brd_cancelGotoDown'),
         goGui.find('**/tt_t_gui_brd_cancelGotoHover'),
         goGui.find('**/tt_t_gui_brd_cancelGotoUp'))
        if self.boardingParty.maxSize == 4:
            zPos = -0.028
            zPos = -0.0360483
        else:
            zPos = -0.0353787
        self.goButton = DirectButton(parent=self.destScrollList, relief=None, image=self.goImageList, image_scale=(0.48, 1, 0.48), command=self.__handleGoButton, text=('',
         TTLocalizer.BoardingGo,
         TTLocalizer.BoardingGo,
         ''), text_scale=TTLocalizer.GPgoButton, text_fg=Vec4(1, 1, 1, 1), text_shadow=Vec4(0, 0, 0, 1), text_pos=(0, -0.12), pos=(-0.003, 0, zPos))
        goGui.removeNode()
        return

    def __getAvatarButton(self, avId):
        toon = base.cr.doId2do.get(avId)
        if not toon:
            return None
        toonName = toon.getName()
        inBattle = 0
        buttonImage = self.availableButtonImage
        if toon.battleId:
            inBattle = 1
            buttonImage = self.battleButtonImage
            if avId == localAvatar.doId:
                self.__forceHide()
        else:
            if avId == self.leaderId:
                buttonImage = self.leaderButtonImage
            if avId == localAvatar.doId:
                self.__forceShow()
        return DirectButton(parent=self.frame, relief=None, image=buttonImage, image_scale=(0.06, 1.0, 0.06), text=toonName, text_align=TextNode.ALeft, text_wordwrap=16, text_scale=0.04, text_pos=(0.05, -0.015), text_fg=self.textFgcolor, text1_bg=self.textBgDownColor, text2_bg=self.textBgRolloverColor, text3_fg=self.textBgDisabledColor, pos=(0, 0, 0.2), command=self.__openToonAvatarPanel, extraArgs=[toon, avId])

    def __openToonAvatarPanel(self, avatar, avId):
        if avId != localAvatar.doId and avatar:
            messenger.send('clickedNametag', [avatar])

    def __addTestNames(self, num):
        for i in range(num):
            avatarButton = self.__getAvatarButton(localAvatar.doId)
            self.scrollList.addItem(avatarButton, refresh=0)

        self.scrollList.refresh()

    def __isForcedHidden(self):
        if self.forcedHidden and self.frame.isHidden():
            return True
        else:
            return False

    def hide(self):
        self.frame.hide()
        self.hideButton.hide()
        self.showButton.show()

    def show(self):
        self.frame.show()
        self.forcedHidden = False
        self.showButton.hide()
        self.hideButton.show()

    def __forceHide(self):
        if not self.frame.isHidden():
            self.forcedHidden = True
            self.hide()

    def __forceShow(self):
        if self.__isForcedHidden():
            self.show()

    def __informDestChange(self):
        self.boardingParty.informDestChange(self.destScrollList.getSelectedIndex())

    def changeDestination(self, offset):
        if localAvatar.doId != self.leaderId:
            self.destIndexSelected = offset
            if self.destFrame:
                self.destFrame['text'] = self.__getDestName(self.destIndexSelected)

    def scrollToDestination(self, offset):
        if localAvatar.doId == self.leaderId:
            if self.destScrollList:
                self.destIndexSelected = offset
                self.destScrollList.scrollTo(offset)

    def __makeGoingToLabel(self):
        if self.boardingParty.maxSize == 4:
            zPos = -0.0466546
        else:
            zPos = -0.331731
        self.goingToLabel = DirectLabel(parent=self.frame, relief=None, text=TTLocalizer.BoardingGoingTo, text_scale=0.045, text_align=TextNode.ALeft, text_fg=Vec4(0, 0, 0, 1), pos=(-0.1966, 0, zPos))
        return

    def disableQuitButton(self):
        if self.quitButton and not self.quitButton.isEmpty():
            self.quitButton['state'] = DGG.DISABLED

    def enableQuitButton(self):
        if self.quitButton and not self.quitButton.isEmpty():
            self.quitButton['state'] = DGG.NORMAL

    def disableGoButton(self):
        if self.goButton and not self.goButton.isEmpty():
            self.goButton['state'] = DGG.DISABLED
            self.goButton['image_color'] = Vec4(1, 1, 1, 0.4)

    def enableGoButton(self):
        if self.goButton and not self.goButton.isEmpty():
            self.goButton['state'] = DGG.NORMAL
            self.goButton['image_color'] = Vec4(1, 1, 1, 1)

    def disableDestinationScrolledList(self):
        if self.destScrollList and not self.destScrollList.isEmpty():
            self.destScrollList.incButton['state'] = DGG.DISABLED
            self.destScrollList.decButton['state'] = DGG.DISABLED

    def enableDestinationScrolledList(self):
        if self.destScrollList and not self.destScrollList.isEmpty():
            self.destScrollList.incButton['state'] = DGG.NORMAL
            self.destScrollList.decButton['state'] = DGG.NORMAL

    def changeGoToCancel(self):
        if self.goButton and not self.goButton.isEmpty():
            self.goButton['image'] = self.cancelGoImageList
            self.goButton['text'] = (TTLocalizer.BoardingCancelGo,
             TTLocalizer.BoardingCancelGo,
             TTLocalizer.BoardingCancelGo,
             '')
            self.goButton['command'] = self.__handleCancelGoButton

    def changeCancelToGo(self):
        if self.goButton and not self.goButton.isEmpty():
            self.goButton['image'] = self.goImageList
            self.goButton['text'] = ('',
             TTLocalizer.BoardingGo,
             TTLocalizer.BoardingGo,
             '')
            self.goButton['command'] = self.__handleGoButton
