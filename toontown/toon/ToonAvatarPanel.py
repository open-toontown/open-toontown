from pandac.PandaModules import *
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from direct.showbase import DirectObject
from . import ToonHead
from toontown.friends import FriendHandle
from . import LaffMeter
from otp.avatar import Avatar
from direct.distributed import DistributedObject
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from toontown.friends import ToontownFriendSecret
from . import ToonAvatarDetailPanel
from . import AvatarPanelBase
from toontown.toontowngui import TTDialog
from otp.otpbase import OTPGlobals

class ToonAvatarPanel(AvatarPanelBase.AvatarPanelBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToonAvatarPanel')

    def __init__(self, avatar, playerId = None):
        from toontown.friends import FriendsListPanel

        if base.cr.doId2do.get(avatar.getDoId()):
            avatar = base.cr.doId2do.get(avatar.getDoId())
        AvatarPanelBase.AvatarPanelBase.__init__(self, avatar, FriendsListPanel=FriendsListPanel)

        self.notify.debug('Opening toon panel, avId=%d' % self.avId)
        self.playerId = playerId

        if not self.playerId:
            av = base.cr.doId2do.get(self.avId)
            if av:
                self.playerId = avatar.DISLid
            else:
                self.playerId = 0

        self.playerInfo = None
        if self.playerId:
            self.playerInfo = base.cr.playerFriendsManager.playerId2Info.get(playerId)

        self.laffMeter = None
        wantsLaffMeter = hasattr(avatar, 'hp')

        if not hasattr(avatar, 'style'):
            self.notify.warning("Avatar has no 'style'. Abort initialization.")
            AvatarPanelBase.AvatarPanelBase.cleanup(self)
            return

        base.localAvatar.obscureFriendsListButton(1)

        gui = loader.loadModel('phase_3.5/models/gui/avatar_panel_gui')
        self.frame = DirectFrame(
                                 image=gui.find('**/avatar_panel'),
                                 relief=None,
                                 pos=(1.1, 100, 0.525))

        self.disabledImageColor = Vec4(1, 1, 1, 0.4)
        self.text0Color = Vec4(1, 1, 1, 1)
        self.text1Color = Vec4(0.5, 1, 0.5, 1)
        self.text2Color = Vec4(1, 1, 0.5, 1)
        self.text3Color = Vec4(0.6, 0.6, 0.6, 1)

        self.head = self.frame.attachNewNode('head')
        self.head.setPos(0.02, 0, 0.31)
        self.headModel = ToonHead.ToonHead()
        self.headModel.setupHead(avatar.style, forGui=1)
        self.headModel.fitAndCenterHead(0.175, forGui=1)
        self.headModel.reparentTo(self.head)

        self.headModel.startBlink()
        self.headModel.startLookAround()

        self.healthText = DirectLabel(
            parent=self.frame,
            text='',
            pos=(0.06, 0, 0.2),
            text_pos=(0, 0),
            text_scale=0.05)

        self.healthText.hide()


        self.nameLabel = DirectLabel(
            parent=self.frame,
            pos=(0.0125, 0, 0.4),
            relief=None,
            text=self.avName,
            text_font=avatar.getFont(),
            text_fg=Vec4(0, 0, 0, 1),
            text_pos=(0, 0),
            text_scale=0.042,
            text_wordwrap=7.5,
            text_shadow=(1, 1, 1, 1))


        self.closeButton = DirectButton(
            parent=self.frame,
            image=(
                gui.find('**/CloseBtn_UP'),
                gui.find('**/CloseBtn_DN'),
                gui.find('**/CloseBtn_Rllvr'),
                gui.find('**/CloseBtn_UP')),
            relief=None,
            pos=(0.157644, 0, -0.379167),
            command=self.__handleClose)


        self.friendButton = DirectButton(
            parent=self.frame,
            image=(
                gui.find('**/Frnds_Btn_UP'),
                gui.find('**/Frnds_Btn_DN'),
                gui.find('**/Frnds_Btn_RLVR'),
                gui.find('**/Frnds_Btn_UP')),
            image3_color=self.disabledImageColor,
            image_scale=0.9,
            relief=None,
            text=TTLocalizer.AvatarPanelFriends,
            text_scale=0.06,
            pos=(-0.103, 0, 0.133),
            text0_fg=self.text0Color,
            text1_fg=self.text1Color,
            text2_fg=self.text2Color,
            text3_fg=self.text3Color,
            text_pos=(0.06, -0.02),
            text_align=TextNode.ALeft,
            command=self.__handleFriend)



        if base.cr.playerFriendsManager.askTransientFriend(self.avId) and self.avId not in base.cr.doId2do:
            self.friendButton['state'] = DGG.DISABLED


        if base.cr.avatarFriendsManager.checkIgnored(self.avId):
            self.friendButton['state'] = DGG.DISABLED

        self.goToButton = DirectButton(
            parent=self.frame,
            image=(
                gui.find('**/Go2_Btn_UP'),
                gui.find('**/Go2_Btn_DN'),
                gui.find('**/Go2_Btn_RLVR'),
                gui.find('**/Go2_Btn_UP')),
            image3_color=self.disabledImageColor,
            image_scale=0.9,
            relief=None,
            pos=(-0.103, 0, 0.045),
            text=TTLocalizer.AvatarPanelGoTo,
            text0_fg=self.text0Color,
            text1_fg=self.text1Color,
            text2_fg=self.text2Color,
            text3_fg=self.text3Color,
            text_scale=0.06,
            text_pos=(0.06, -0.015),
            text_align=TextNode.ALeft,
            command=self.__handleGoto)



        if base.cr.avatarFriendsManager.checkIgnored(self.avId):
            self.goToButton['state'] = DGG.DISABLED

        self.whisperButton = DirectButton(
            parent=self.frame,
            image=(
                gui.find('**/ChtBx_ChtBtn_UP'),
                gui.find('**/ChtBx_ChtBtn_DN'),
                gui.find('**/ChtBx_ChtBtn_RLVR'),
                gui.find('**/ChtBx_ChtBtn_UP')),
            image3_color=self.disabledImageColor,
            image_scale=0.9,
            relief=None,
            pos=(-0.103, 0, -0.0375),
            text=TTLocalizer.AvatarPanelWhisper,
            text0_fg=self.text0Color,
            text1_fg=self.text1Color,
            text2_fg=self.text2Color,
            text3_fg=self.text3Color,
            text_scale=TTLocalizer.TAPwhisperButton,
            text_pos=(0.06, -0.0125),
            text_align=TextNode.ALeft,
            command=self.__handleWhisper)



        if base.cr.avatarFriendsManager.checkIgnored(self.avId):
            self.whisperButton['state'] = DGG.DISABLED

        self.secretsButton = DirectButton(
            parent=self.frame,
            image=(
                gui.find('**/Amuse_Btn_UP'),
                gui.find('**/Amuse_Btn_DN'),
                gui.find('**/Amuse_Btn_RLVR'),
                gui.find('**/Amuse_Btn_UP')),
            image3_color=self.disabledImageColor,
            image_scale=0.9,
            relief=None,
            pos=(-0.103, 0, -0.13),
            text=TTLocalizer.AvatarPanelSecrets,
            text0_fg=self.text0Color,
            text1_fg=self.text1Color,
            text2_fg=self.text2Color,
            text3_fg=self.text3Color,
            text_scale=TTLocalizer.TAPsecretsButton,
            text_pos=(0.055, -0.01),
            text_align=TextNode.ALeft,
            command=self.__handleSecrets)



        if base.cr.avatarFriendsManager.checkIgnored(self.avId):
            self.secretsButton['state'] = DGG.DISABLED


        from toontown.coghq import CogHQBossBattle
        if isinstance(base.cr.playGame.getPlace(), CogHQBossBattle.CogHQBossBattle) and \
                base.localAvatar.getGameAccess() != OTPGlobals.AccessFull:
            self.secretsButton['state'] = DGG.DISABLED

        ignoreStr, ignoreCmd, ignoreScale = self.getIgnoreButtonInfo()

        self.ignoreButton = DirectButton(
            parent=self.frame,
            image=(
                gui.find('**/Ignore_Btn_UP'),
                gui.find('**/Ignore_Btn_DN'),
                gui.find('**/Ignore_Btn_RLVR'),
                gui.find('**/Ignore_Btn_UP')),
            image3_color=self.disabledImageColor,
            image_scale=0.9,
            relief=None,
            pos=(-0.103697, 0, -0.21),
            text=ignoreStr,
            text0_fg=self.text0Color,
            text1_fg=self.text1Color,
            text2_fg=self.text2Color,
            text3_fg=self.text3Color,
            text_scale=ignoreScale,
            text_pos=(0.06, -0.015),
            text_align=TextNode.ALeft,
            command=ignoreCmd)


        if base.cr.productName not in ['JP', 'DE', 'BR', 'FR']:
            self.reportButton = DirectButton(
                parent=self.frame,
                image=(
                    gui.find('**/report_BtnUP'),
                    gui.find('**/report_BtnDN'),
                    gui.find('**/report_BtnRLVR'),
                    gui.find('**/report_BtnUP')),
                image3_color=self.disabledImageColor,
                image_scale=0.65,
                relief=None,
                pos=(-0.103, 0, -0.29738),
                text=TTLocalizer.AvatarPanelReport,
                text0_fg=self.text0Color,
                text1_fg=self.text1Color,
                text2_fg=self.text2Color,
                text3_fg=self.text3Color,
                text_scale=0.06,
                text_pos=(0.06, -0.015),
                text_align=TextNode.ALeft,
                command=self.handleReport)


        if not base.localAvatar.isTeleportAllowed():
            self.goToButton['state'] = DGG.DISABLED

        self.detailButton = DirectButton(
            parent=self.frame,
            image=(
                gui.find('**/ChtBx_BackBtn_UP'),
                gui.find('**/ChtBx_BackBtn_DN'),
                gui.find('**/ChtBx_BackBtn_Rllvr'),
                gui.find('**/ChtBx_BackBtn_UP')),
            relief=None,
            text=('', TTLocalizer.AvatarPanelDetail,
                  TTLocalizer.AvatarPanelDetail, ''),
            text_fg=self.text2Color,
            text_shadow=(0, 0, 0, 1),
            text_scale=0.055,
            text_pos=(-0.075, -0.01),
            text_align=TextNode.ARight,
            pos=(-0.133773, 0, -0.395),
            command=self.__handleDetails)


        self.__makeBoardingGui()
        self.__makePetGui(avatar)

        self.__checkGroupStatus()

        gui.removeNode()


        if wantsLaffMeter:
            self.__makeLaffMeter(avatar)
            self.__updateHp(avatar.hp, avatar.maxHp)
            self.healthText.show()
            self.laffMeter.show()

        menuX = -0.05
        menuScale = 0.064

        if self.avGenerateName:
            self.accept(self.avGenerateName, self.__handleGenerateAvatar)
        if self.avHpChangeName:
            self.accept(self.avHpChangeName, self.__updateHp)
        self.accept('updateLaffMeter', self.__updateLaffMeter)

        self.accept('updateGroupStatus', self.__checkGroupStatus)

        self.frame.show()
        messenger.send('avPanelDone')

    def disableAll(self):
        self.detailButton['state'] = DGG.DISABLED
        if base.cr.productName not in ['ES',
         'JP',
         'DE',
         'BR',
         'FR']:
            self.reportButton['state'] = DGG.DISABLED
        self.ignoreButton['state'] = DGG.DISABLED
        self.goToButton['state'] = DGG.DISABLED
        self.secretsButton['state'] = DGG.DISABLED
        self.whisperButton['state'] = DGG.DISABLED
        self.petButton['state'] = DGG.DISABLED
        self.friendButton['state'] = DGG.DISABLED
        self.closeButton['state'] = DGG.DISABLED
        self.groupButton['state'] = DGG.DISABLED
        self.boardingInfoButton['state'] = DGG.DISABLED

    def cleanup(self):
        if not hasattr(self, 'frame') or self.frame == None:
            return
        self.notify.debug('Clean up toon panel, avId=%d' % self.avId)
        if self.frame:
            self.frame.destroy()
            del self.frame
        self.frame = None
        ToonAvatarDetailPanel.unloadAvatarDetail()
        if self.groupButton:
            self.groupButton.destroy()
            del self.groupButton
        self.groupButton = None
        if self.boardingInfoButton:
            self.boardingInfoButton.destroy()
            del self.boardingInfoButton
        self.boardingInfoButton = None
        if self.boardingInfoText:
            self.boardingInfoText.destroy()
            del self.boardingInfoText
        self.boardingInfoText = None
        if self.groupFrame:
            self.groupFrame.destroy()
            del self.groupFrame
        self.groupFrame = None
        self.head.removeNode()
        del self.head
        self.headModel.stopBlink()
        self.headModel.stopLookAroundNow()
        self.headModel.delete()
        del self.headModel
        base.localAvatar.obscureFriendsListButton(-1)
        self.laffMeter = None
        self.ignore('updateLaffMeter')
        self.ignoreAll()
        if hasattr(self.avatar, 'bFake') and self.avatar.bFake:
            self.avatar.delete()
        base.setCellsAvailable([base.rightCells[0]], 1)
        AvatarPanelBase.AvatarPanelBase.cleanup(self)
        return

    def __handleGoto(self):
        if base.localAvatar.isTeleportAllowed():
            base.localAvatar.chatMgr.noWhisper()
            messenger.send('gotoAvatar', [self.avId, self.avName, self.avDisableName])

    def __handleToPet(self):
        toonAvatar = self.avatar
        if base.cr.doId2do.get(toonAvatar.getDoId()):
            toonAvatar = base.cr.doId2do.get(toonAvatar.getDoId())
        petAvatar = base.cr.doId2do.get(toonAvatar.getPetId())
        self.disableAll()
        from toontown.pets import PetDetail
        PetDetail.PetDetail(toonAvatar.getPetId(), self.__petDetailsLoaded)

    def __petDetailsLoaded(self, avatar):
        self.cleanup()
        if avatar:
            self.notify.debug("Looking at someone's pet. pet doId = %s" % avatar.doId)
            messenger.send('clickedNametag', [avatar])

    def __handleWhisper(self):
        base.localAvatar.chatMgr.whisperTo(self.avName, self.avId, None)
        return

    def __handleSecrets(self):
        base.localAvatar.chatMgr.noWhisper()
        ToontownFriendSecret.showFriendSecret(ToontownFriendSecret.AvatarSecret)

    def __handleFriend(self):
        base.localAvatar.chatMgr.noWhisper()
        messenger.send('friendAvatar', [self.avId, self.avName, self.avDisableName])

    def __handleDetails(self):
        base.localAvatar.chatMgr.noWhisper()
        messenger.send('avatarDetails', [self.avId, self.avName, self.playerId])

    def __handleDisableAvatar(self):
        if not base.cr.isFriend(self.avId):
            self.cleanup()
            AvatarPanelBase.currentAvatarPanel = None
        else:
            self.healthText.hide()
            if self.laffMeter != None:
                self.laffMeter.stop()
                self.laffMeter.destroy()
                self.laffMeter = None
        return

    def __handleGenerateAvatar(self, avatar):
        newAvatar = base.cr.doId2do.get(self.avatar.doId)
        if newAvatar:
            self.avatar = newAvatar
        self.__updateLaffMeter(avatar, avatar.hp, avatar.maxHp)
        self.__checkGroupStatus()

    def __updateLaffMeter(self, avatar, hp, maxHp):
        if self.laffMeter == None:
            self.__makeLaffMeter(avatar)
        self.__updateHp(avatar.hp, avatar.maxHp)
        self.laffMeter.show()
        self.healthText.show()
        return

    def __makeLaffMeter(self, avatar):
        self.laffMeter = LaffMeter.LaffMeter(avatar.style, avatar.hp, avatar.maxHp)
        self.laffMeter.reparentTo(self.frame)
        self.laffMeter.setPos(-0.1, 0, 0.24)
        self.laffMeter.setScale(0.03)

    def __updateHp(self, hp, maxHp, quietly = 0):
        if self.laffMeter != None and hp != None and maxHp != None:
            self.laffMeter.adjustFace(hp, maxHp)
            self.healthText['text'] = '%d / %d' % (hp, maxHp)
        return

    def __handleClose(self):
        self.cleanup()
        AvatarPanelBase.currentAvatarPanel = None
        if self.friendsListShown:
            self.FriendsListPanel.showFriendsList()
        return

    def getAvId(self):
        if hasattr(self, 'avatar'):
            if self.avatar:
                return self.avatar.doId
        return None

    def getPlayerId(self):
        if hasattr(self, 'playerId'):
            return self.playerId
        return None

    def isHidden(self):
        if not hasattr(self, 'frame') or not self.frame:
            return 1
        return self.frame.isHidden()

    def getType(self):
        return 'toon'

    def handleInvite(self):
        if localAvatar.boardingParty.isInviteePanelUp():
            localAvatar.boardingParty.showMe(TTLocalizer.BoardingPendingInvite, pos=(0, 0, 0))
        else:
            self.groupButton['state'] = DGG.DISABLED
            localAvatar.boardingParty.requestInvite(self.avId)

    def handleKick(self):
        if not base.cr.playGame.getPlace().getState() == 'elevator':
            self.confirmKickOutDialog = TTDialog.TTDialog(style=TTDialog.YesNo, text=TTLocalizer.BoardingKickOutConfirm % self.avName, command=self.__confirmKickOutCallback)
            self.confirmKickOutDialog.show()

    def __confirmKickOutCallback(self, value):
        if self.confirmKickOutDialog:
            self.confirmKickOutDialog.destroy()
        self.confirmKickOutDialog = None
        if value > 0:
            if self.groupButton:
                self.groupButton['state'] = DGG.DISABLED
            localAvatar.boardingParty.requestKick(self.avId)
        return

    def __checkGroupStatus(self):
        self.groupFrame.hide()
        if hasattr(self, 'avatar'):
            if self.avatar and hasattr(self.avatar, 'getZoneId') and localAvatar.getZoneId() == self.avatar.getZoneId():
                if localAvatar.boardingParty:
                    if self.avId in localAvatar.boardingParty.getGroupMemberList(localAvatar.doId):
                        if localAvatar.boardingParty.getGroupLeader(localAvatar.doId) == localAvatar.doId:
                            self.groupButton['text'] = ('', TTLocalizer.AvatarPanelGroupMemberKick, TTLocalizer.AvatarPanelGroupMemberKick)
                            self.groupButton['image'] = self.kickOutImageList
                            self.groupButton['command'] = self.handleKick
                            self.groupButton['state'] = DGG.NORMAL
                        else:
                            self.groupButton['text'] = ('', TTLocalizer.AvatarPanelGroupMember, TTLocalizer.AvatarPanelGroupMember)
                            self.groupButton['command'] = None
                            self.groupButton['image'] = self.inviteImageDisabled
                            self.groupButton['image_color'] = Vec4(1, 1, 1, 0.4)
                            self.groupButton['state'] = DGG.NORMAL
                    else:
                        self.groupButton['text'] = ('', TTLocalizer.AvatarPanelGroupInvite, TTLocalizer.AvatarPanelGroupInvite)
                        self.groupButton['command'] = self.handleInvite
                        self.groupButton['image'] = self.inviteImageList
                        self.groupButton['state'] = DGG.NORMAL
                    if base.config.GetBool('want-boarding-groups', 1):
                        base.setCellsAvailable([base.rightCells[0]], 0)
                        self.groupFrame.show()
        return

    def handleReadInfo(self, task = None):
        self.boardingInfoButton['state'] = DGG.DISABLED
        if self.boardingInfoText:
            self.boardingInfoText.destroy()
        self.boardingInfoText = TTDialog.TTDialog(style=TTDialog.Acknowledge, text=TTLocalizer.BoardingPartyInform % localAvatar.boardingParty.maxSize, command=self.handleCloseInfo)

    def handleCloseInfo(self, *extraArgs):
        self.boardingInfoButton['state'] = DGG.NORMAL
        if self.boardingInfoText:
            self.boardingInfoText.destroy()
            del self.boardingInfoText
        self.boardingInfoText = None
        return

    def __makePetGui(self, avatar):
        petGui = loader.loadModel('phase_3.5/models/gui/PetControlPannel')
        self.petButton = DirectButton(parent=self.frame, image=(petGui.find('**/PetControlToonButtonUp1'), petGui.find('**/PetControlToonButtonDown1'), petGui.find('**/PetControlToonButtonRollover1')), geom=petGui.find('**/PetBattleIcon'), geom3_color=self.disabledImageColor, relief=None, pos=(0.22, -0.2, -0.475), text=('',
         TTLocalizer.AvatarPanelPet,
         TTLocalizer.AvatarPanelPet,
         ''), text_fg=self.text2Color, text_shadow=(0, 0, 0, 1), text_scale=0.325, text_pos=(-1.3, 0.05), text_align=TextNode.ACenter, command=self.__handleToPet)
        self.petButton.setScale(0.15)
        if not (base.wantPets and avatar.hasPet()):
            self.petButton['state'] = DGG.DISABLED
            self.petButton.hide()
        petGui.removeNode()
        return

    def __makeBoardingGui(self):
        self.confirmKickOutDialog = None
        groupAvatarBgGui = loader.loadModel('phase_3.5/models/gui/tt_m_gui_brd_avatarPanelBg')
        boardingGroupBGImage = groupAvatarBgGui.find('**/tt_t_gui_brd_avatar_panel_party')
        self.groupFrame = DirectFrame(parent=self.frame, relief=None, image=boardingGroupBGImage, image_scale=(0.5, 1, 0.5), textMayChange=1, text=TTLocalizer.BoardingPartyTitle, text_wordwrap=16, text_scale=TTLocalizer.TAPgroupFrame, text_pos=(0.01, 0.08), pos=(0, 0, -0.61))
        groupInviteGui = loader.loadModel('phase_3.5/models/gui/tt_m_gui_brd_inviteButton')
        self.inviteImageList = (groupInviteGui.find('**/tt_t_gui_brd_inviteUp'),
         groupInviteGui.find('**/tt_t_gui_brd_inviteDown'),
         groupInviteGui.find('**/tt_t_gui_brd_inviteHover'),
         groupInviteGui.find('**/tt_t_gui_brd_inviteUp'))
        self.kickOutImageList = (groupInviteGui.find('**/tt_t_gui_brd_kickoutUp'),
         groupInviteGui.find('**/tt_t_gui_brd_kickoutDown'),
         groupInviteGui.find('**/tt_t_gui_brd_kickoutHover'),
         groupInviteGui.find('**/tt_t_gui_brd_kickoutUp'))
        self.inviteImageDisabled = groupInviteGui.find('**/tt_t_gui_brd_inviteDisabled')
        self.groupButton = DirectButton(parent=self.groupFrame, image=self.inviteImageList, image3_color=self.disabledImageColor, image_scale=0.85, relief=None, text=('', TTLocalizer.AvatarPanelGroupInvite, TTLocalizer.AvatarPanelGroupInvite), text0_fg=self.text0Color, text1_fg=self.text1Color, text2_fg=self.text2Color, text3_fg=self.text3Color, text_scale=TTLocalizer.TAPgroupButton, text_pos=(-0.0, -0.1), text_align=TextNode.ACenter, command=self.handleInvite, pos=(0.01013, 0, -0.05464))
        helpGui = loader.loadModel('phase_3.5/models/gui/tt_m_gui_brd_help')
        helpImageList = (helpGui.find('**/tt_t_gui_brd_helpUp'),
         helpGui.find('**/tt_t_gui_brd_helpDown'),
         helpGui.find('**/tt_t_gui_brd_helpHover'),
         helpGui.find('**/tt_t_gui_brd_helpDown'))
        self.boardingInfoButton = DirectButton(parent=self.groupFrame, relief=None, text_pos=(-0.05, 0.05), text_scale=0.06, text_align=TextNode.ALeft, text_fg=Vec4(1, 1, 1, 1), text_shadow=Vec4(0, 0, 0, 1), image=helpImageList, image_scale=(0.5, 1, 0.5), image3_color=self.disabledImageColor, scale=1.05, command=self.handleReadInfo, pos=(0.1829, 0, 0.02405))
        self.boardingInfoText = None
        groupInviteGui.removeNode()
        groupAvatarBgGui.removeNode()
        helpGui.removeNode()
        return
