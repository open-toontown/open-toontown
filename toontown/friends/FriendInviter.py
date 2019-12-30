from pandac.PandaModules import *
from direct.task.Task import Task
from toontown.toonbase.ToontownGlobals import *
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from direct.showbase import DirectObject
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import TTLocalizer
from toontown.toon import ToonTeleportPanel
from toontown.suit import Suit
from toontown.pets import Pet
from otp.otpbase import OTPLocalizer
from otp.otpbase import OTPGlobals
from otp.uberdog import RejectCode
globalFriendInviter = None

def showFriendInviter(avId, avName, avDisableName):
    global globalFriendInviter
    if globalFriendInviter != None:
        globalFriendInviter.cleanup()
        globalFriendInviter = None
    globalFriendInviter = FriendInviter(avId, avName, avDisableName)
    return


def hideFriendInviter():
    global globalFriendInviter
    if globalFriendInviter != None:
        globalFriendInviter.cleanup()
        globalFriendInviter = None
    return


def unloadFriendInviter():
    global globalFriendInviter
    if globalFriendInviter != None:
        globalFriendInviter.cleanup()
        globalFriendInviter = None
    return


class FriendInviter(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('FriendInviter')

    def __init__(self, avId, avName, avDisableName):
        self.wantPlayerFriends = base.config.GetBool('want-player-friends', 0)
        DirectFrame.__init__(self, pos=(0.3, 0.1, 0.65), image_color=GlobalDialogColor, image_scale=(1.0, 1.0, 0.6), text='', text_wordwrap=TTLocalizer.FIdirectFrameWordwrap, text_scale=TTLocalizer.FIdirectFrame, text_pos=TTLocalizer.FIdirectFramePos)
        self['image'] = DGG.getDefaultDialogGeom()
        self.avId = avId
        self.toonName = avName
        avatar = base.cr.doId2do.get(self.avId)
        self.playerId = None
        self.playerName = None
        if avatar:
            self.playerId = avatar.DISLid
            self.playerName = avatar.DISLname + ' ' + str(avatar.DISLid)
        self.avDisableName = avDisableName
        self.playerFriend = 0
        self.fsm = ClassicFSM.ClassicFSM('FriendInviter', [State.State('off', self.enterOff, self.exitOff),
         State.State('getNewFriend', self.enterGetNewFriend, self.exitGetNewFriend),
         State.State('begin', self.enterBegin, self.exitBegin),
         State.State('check', self.enterCheck, self.exitCheck),
         State.State('tooMany', self.enterTooMany, self.exitTooMany),
         State.State('checkAvailability', self.enterCheckAvailability, self.exitCheckAvailability),
         State.State('notAvailable', self.enterNotAvailable, self.exitNotAvailable),
         State.State('notAcceptingFriends', self.enterNotAcceptingFriends, self.exitNotAcceptingFriends),
         State.State('wentAway', self.enterWentAway, self.exitWentAway),
         State.State('already', self.enterAlready, self.exitAlready),
         State.State('askingCog', self.enterAskingCog, self.exitAskingCog),
         State.State('askingPet', self.enterAskingPet, self.exitAskingPet),
         State.State('endFriendship', self.enterEndFriendship, self.exitEndFriendship),
         State.State('friendsNoMore', self.enterFriendsNoMore, self.exitFriendsNoMore),
         State.State('self', self.enterSelf, self.exitSelf),
         State.State('ignored', self.enterIgnored, self.exitIgnored),
         State.State('asking', self.enterAsking, self.exitAsking),
         State.State('yes', self.enterYes, self.exitYes),
         State.State('no', self.enterNo, self.exitNo),
         State.State('otherTooMany', self.enterOtherTooMany, self.exitOtherTooMany),
         State.State('maybe', self.enterMaybe, self.exitMaybe),
         State.State('down', self.enterDown, self.exitDown),
         State.State('cancel', self.enterCancel, self.exitCancel)], 'off', 'off')
        self.context = None
        from toontown.toon import ToonAvatarDetailPanel
        ToonTeleportPanel.hideTeleportPanel()
        ToonAvatarDetailPanel.hideAvatarDetail()
        buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
        gui = loader.loadModel('phase_3.5/models/gui/avatar_panel_gui')
        self.bOk = DirectButton(self, image=(buttons.find('**/ChtBx_OKBtn_UP'), buttons.find('**/ChtBx_OKBtn_DN'), buttons.find('**/ChtBx_OKBtn_Rllvr')), relief=None, text=OTPLocalizer.FriendInviterOK, text_scale=0.05, text_pos=(0.0, -0.1), pos=(0.0, 0.0, -0.1), command=self.__handleOk)
        self.bOk.hide()
        self.bCancel = DirectButton(self, image=(buttons.find('**/CloseBtn_UP'), buttons.find('**/CloseBtn_DN'), buttons.find('**/CloseBtn_Rllvr')), relief=None, text=OTPLocalizer.FriendInviterCancel, text_scale=0.05, text_pos=(0.0, -0.1), pos=TTLocalizer.FIbCancelPos, command=self.__handleCancel)
        self.bCancel.hide()
        self.bStop = DirectButton(self, image=(gui.find('**/Ignore_Btn_UP'), gui.find('**/Ignore_Btn_DN'), gui.find('**/Ignore_Btn_RLVR')), relief=None, text=OTPLocalizer.FriendInviterStopBeingFriends, text_align=TextNode.ALeft, text_scale=TTLocalizer.FIbStop, text_pos=TTLocalizer.FIbStopTextPos, pos=TTLocalizer.FIbStopPos, command=self.__handleStop)
        self.bStop.hide()
        self.bYes = DirectButton(self, image=(buttons.find('**/ChtBx_OKBtn_UP'), buttons.find('**/ChtBx_OKBtn_DN'), buttons.find('**/ChtBx_OKBtn_Rllvr')), relief=None, text=OTPLocalizer.FriendInviterYes, text_scale=0.05, text_pos=(0.0, -0.1), pos=TTLocalizer.FIbYesPos, command=self.__handleYes)
        self.bYes.hide()
        self.bNo = DirectButton(self, image=(buttons.find('**/CloseBtn_UP'), buttons.find('**/CloseBtn_DN'), buttons.find('**/CloseBtn_Rllvr')), relief=None, text=OTPLocalizer.FriendInviterNo, text_scale=0.05, text_pos=(0.0, -0.1), pos=(0.15, 0.0, -0.1), command=self.__handleNo)
        self.bNo.hide()
        self.bToon = DirectButton(self, image=(buttons.find('**/ChtBx_OKBtn_UP'), buttons.find('**/ChtBx_OKBtn_DN'), buttons.find('**/ChtBx_OKBtn_Rllvr')), relief=None, text=TTLocalizer.FriendInviterToon, text_scale=0.05, text_pos=(0.0, -0.1), pos=(-0.35, 0.0, -0.05), command=self.__handleToon)
        toonText = DirectLabel(parent=self, relief=None, pos=Vec3(0.35, 0, -0.2), text=TTLocalizer.FriendInviterToonFriendInfo, text_fg=(0, 0, 0, 1), text_pos=(0, 0), text_scale=0.045, text_align=TextNode.ACenter)
        toonText.reparentTo(self.bToon.stateNodePath[2])
        self.bToon.hide()
        self.bPlayer = DirectButton(self, image=(buttons.find('**/ChtBx_OKBtn_UP'), buttons.find('**/ChtBx_OKBtn_DN'), buttons.find('**/ChtBx_OKBtn_Rllvr')), relief=None, text=TTLocalizer.FriendInviterPlayer, text_scale=0.05, text_pos=(0.0, -0.1), pos=(0.0, 0.0, -0.05), command=self.__handlePlayer)
        playerText = DirectLabel(parent=self, relief=None, pos=Vec3(0, 0, -0.2), text=TTLocalizer.FriendInviterPlayerFriendInfo, text_fg=(0, 0, 0, 1), text_pos=(0, 0), text_scale=0.045, text_align=TextNode.ACenter)
        playerText.reparentTo(self.bPlayer.stateNodePath[2])
        self.bPlayer.hide()
        buttons.removeNode()
        gui.removeNode()
        self.fsm.enterInitialState()
        if self.avId == None:
            self.fsm.request('getNewFriend')
        else:
            self.fsm.request('begin')
        return

    def cleanup(self):
        self.fsm.request('cancel')
        del self.fsm
        self.destroy()

    def getName(self):
        if self.playerFriend:
            name = self.playerName
            if name == None:
                name = TTLocalizer.FriendInviterThatPlayer
        else:
            name = self.toonName
            if name == None:
                name = TTLocalizer.FriendInviterThatToon
        return name

    def enterOff(self):
        pass

    def exitOff(self):
        pass

    def enterGetNewFriend(self):
        self['text'] = TTLocalizer.FriendInviterClickToon % len(base.localAvatar.friendsList)
        if base.cr.productName in ['JP',
         'DE',
         'BR',
         'FR']:
            self.bOk.show()
        else:
            self.bCancel.show()
        self.accept('clickedNametag', self.__handleClickedNametag)

    def exitGetNewFriend(self):
        self.bCancel.hide()
        self.ignore('clickedNametag')

    def __handleClickedNametag(self, avatar):
        self.avId = avatar.doId
        self.toonName = avatar.getName()
        if hasattr(avatar, 'DISLid'):
            self.playerId = avatar.DISLid
            self.playerName = avatar.DISLname
        self.avDisableName = avatar.uniqueName('disable')
        self.fsm.request('begin')

    def enterBegin(self):
        myId = base.localAvatar.doId
        self['text'] = TTLocalizer.FriendInviterBegin
        self.bCancel.setPos(0.35, 0.0, -0.05)
        self.bCancel.show()
        self.bToon.show()
        if self.wantPlayerFriends and base.cr.productName != 'DisneyOnline-UK' and base.cr.productName != 'DisneyOnline-AP':
            self.bPlayer.show()
        else:
            self.__handleToon()
        self.accept(self.avDisableName, self.__handleDisableAvatar)

    def exitBegin(self):
        self.ignore(self.avDisableName)
        self.bToon.hide()
        if self.wantPlayerFriends and base.cr.productName != 'DisneyOnline-UK' and base.cr.productName != 'DisneyOnline-AP':
            self.bPlayer.hide()
        self.bCancel.setPos(0.0, 0.0, -0.1)
        self.bCancel.hide()

    def enterCheck(self):
        myId = base.localAvatar.doId
        self.accept(self.avDisableName, self.__handleDisableAvatar)
        if self.avId == myId:
            self.fsm.request('self')
        elif not self.playerFriend and base.cr.isFriend(self.avId):
            self.fsm.request('already')
        elif self.playerFriend and base.cr.playerFriendsManager.isPlayerFriend(self.avId):
            self.fsm.request('already')
        else:
            if not self.playerFriend:
                tooMany = len(base.localAvatar.friendsList) >= MaxFriends
            elif self.playerFriend:
                tooMany = base.cr.playerFriendsManager.friendsListFull()
            if tooMany:
                self.fsm.request('tooMany')
            else:
                self.fsm.request('checkAvailability')

    def exitCheck(self):
        self.ignore(self.avDisableName)

    def enterTooMany(self):
        if self.playerFriend:
            text = OTPLocalizer.FriendInviterPlayerTooMany
            name = self.playerName
        else:
            text = OTPLocalizer.FriendInviterToonTooMany
            name = self.toonName
        self['text'] = text % name
        self.bCancel.show()
        self.bCancel.setPos(0.0, 0.0, -0.16)

    def exitTooMany(self):
        self.bCancel.hide()

    def enterCheckAvailability(self):
        self.accept(self.avDisableName, self.__handleDisableAvatar)
        if not self.playerFriend:
            if self.avId not in base.cr.doId2do:
                self.fsm.request('wentAway')
                return
        if self.avId not in base.cr.doId2do:
            self.fsm.request('wentAway')
            return
        else:
            avatar = base.cr.doId2do.get(self.avId)
        if isinstance(avatar, Suit.Suit):
            self.fsm.request('askingCog')
            return
        if isinstance(avatar, Pet.Pet):
            self.fsm.request('askingPet')
            return
        if not self.playerFriend:
            if not base.cr.friendManager:
                self.notify.warning('No FriendManager available.')
                self.fsm.request('down')
                return
        if self.playerFriend:
            self.notify.info('Inviter requesting player friend')
            self['text'] = OTPLocalizer.FriendInviterAsking % self.playerName
            base.cr.playerFriendsManager.sendRequestInvite(self.playerId)
            self.accept(OTPGlobals.PlayerFriendRejectInviteEvent, self.__playerFriendRejectResponse)
            self.accept(OTPGlobals.PlayerFriendAddEvent, self.__playerFriendAcceptResponse)
            self.bOk.show()
        else:
            base.cr.friendManager.up_friendQuery(self.avId)
            self['text'] = OTPLocalizer.FriendInviterCheckAvailability % self.toonName
            self.accept('friendResponse', self.__friendResponse)
            self.bCancel.show()
        self.accept('friendConsidering', self.__friendConsidering)

    def exitCheckAvailability(self):
        self.ignore(self.avDisableName)
        self.ignore('friendConsidering')
        self.ignore('friendResponse')
        self.bCancel.hide()

    def enterNotAvailable(self):
        self['text'] = OTPLocalizer.FriendInviterNotAvailable % self.getName()
        self.context = None
        self.bOk.show()
        return

    def exitNotAvailable(self):
        self.bOk.hide()

    def enterNotAcceptingFriends(self):
        self['text'] = OTPLocalizer.FriendInviterFriendSaidNoNewFriends % self.getName()
        self.context = None
        self.bOk.show()
        return

    def exitNotAcceptingFriends(self):
        self.bOk.hide()

    def enterWentAway(self):
        self['text'] = OTPLocalizer.FriendInviterWentAway % self.getName()
        if not self.playerFriend:
            if self.context != None:
                base.cr.friendManager.up_cancelFriendQuery(self.context)
                self.context = None
        self.bOk.show()
        return

    def exitWentAway(self):
        self.bOk.hide()

    def enterAlready(self):
        if self.playerFriend:
            self['text'] = TTLocalizer.FriendInviterPlayerAlready % self.getName()
            self.bStop['text'] = TTLocalizer.FriendInviterStopBeingPlayerFriends
        else:
            self['text'] = TTLocalizer.FriendInviterToonAlready % self.getName()
            self.bStop['text'] = TTLocalizer.FriendInviterStopBeingToonFriends
        self.context = None
        if base.cr.productName in ['JP',
         'DE',
         'BR',
         'FR']:
            self.bStop.setPos(-0.2, 0.0, -0.1)
            self.bCancel.setPos(0.2, 0.0, -0.1)
        self.bStop.show()
        self.bCancel.show()
        return

    def exitAlready(self):
        self['text'] = ''
        self.bStop.hide()
        self.bCancel.hide()

    def enterAskingCog(self):
        self['text'] = OTPLocalizer.FriendInviterAskingCog % self.getName()
        taskMgr.doMethodLater(2.0, self.cogReplies, 'cogFriendship')
        self.bCancel.show()

    def exitAskingCog(self):
        taskMgr.remove('cogFriendship')
        self.bCancel.hide()

    def cogReplies(self, task):
        self.fsm.request('no')
        return Task.done

    def enterAskingPet(self):
        self['text'] = OTPLocalizer.FriendInviterAskingPet % self.getName()
        if base.localAvatar.hasPet():
            if base.localAvatar.getPetId() == self.avId:
                self['text'] = OTPLocalizer.FriendInviterAskingMyPet % self.getName()
        self.context = None
        self.bOk.show()
        return

    def exitAskingPet(self):
        self.bOk.hide()

    def enterEndFriendship(self):
        if self.playerFriend:
            self['text'] = TTLocalizer.FriendInviterEndFriendshipPlayer % self.getName()
            if base.cr.isFriend(self.avId):
                self['text'] = self['text'] + TTLocalizer.FriendInviterRemainToon % self.toonName
        else:
            self['text'] = TTLocalizer.FriendInviterEndFriendshipToon % self.getName()
            if base.cr.playerFriendsManager.isPlayerFriend(self.playerId):
                self['text'] = self['text'] + TTLocalizer.FriendInviterRemainPlayer % self.playerName
        self.context = None
        self.bYes.show()
        self.bNo.show()
        return

    def exitEndFriendship(self):
        self.bYes.hide()
        self.bNo.hide()

    def enterFriendsNoMore(self):
        if self.playerFriend:
            self.notify.info('### send player remove')
            base.cr.playerFriendsManager.sendRequestRemove(self.playerId)
        else:
            self.notify.info('### send avatar remove')
            base.cr.removeFriend(self.avId)
        self['text'] = OTPLocalizer.FriendInviterFriendsNoMore % self.getName()
        self.bOk.show()
        if self.avId not in base.cr.doId2do:
            messenger.send(self.avDisableName)

    def exitFriendsNoMore(self):
        self.bOk.hide()

    def enterSelf(self):
        self['text'] = OTPLocalizer.FriendInviterSelf
        self.context = None
        self.bOk.show()
        return

    def exitSelf(self):
        self.bOk.hide()

    def enterIgnored(self):
        self['text'] = OTPLocalizer.FriendInviterIgnored % self.toonName
        self.context = None
        self.bOk.show()
        return

    def exitIgnored(self):
        self.bOk.hide()

    def enterAsking(self):
        self.accept(self.avDisableName, self.__handleDisableAvatar)
        self['text'] = OTPLocalizer.FriendInviterAsking % self.toonName
        self.accept('friendResponse', self.__friendResponse)
        self.bCancel.show()

    def exitAsking(self):
        self.ignore(self.avDisableName)
        self.ignore('friendResponse')
        self.bCancel.hide()

    def enterYes(self):
        self['text'] = OTPLocalizer.FriendInviterFriendSaidYes % self.toonName
        self.context = None
        self.bOk.show()
        return

    def exitYes(self):
        self.bOk.hide()

    def enterNo(self):
        self['text'] = OTPLocalizer.FriendInviterFriendSaidNo % self.toonName
        self.context = None
        self.bOk.show()
        return

    def exitNo(self):
        self.bOk.hide()

    def enterOtherTooMany(self):
        self['text'] = OTPLocalizer.FriendInviterOtherTooMany % self.toonName
        self.context = None
        self.bOk.show()
        return

    def exitOtherTooMany(self):
        self.bOk.hide()

    def enterMaybe(self):
        self['text'] = OTPLocalizer.FriendInviterMaybe % self.toonName
        self.context = None
        self.bOk.show()
        return

    def exitMaybe(self):
        self.bOk.hide()

    def enterDown(self):
        self['text'] = OTPLocalizer.FriendInviterDown
        self.context = None
        self.bOk.show()
        return

    def exitDown(self):
        self.bOk.hide()

    def enterCancel(self):
        if not self.playerFriend:
            if self.context != None:
                base.cr.friendManager.up_cancelFriendQuery(self.context)
                self.context = None
        self.fsm.request('off')
        return

    def exitCancel(self):
        pass

    def __handleOk(self):
        if base.config.GetBool('want-qa-regression', 0):
            self.notify.info('QA-REGRESSION: MAKEAFRIENDSHIP: Make a friendship')
        unloadFriendInviter()

    def __handleCancel(self):
        if base.friendMode == 1:
            if self.avId:
                base.cr.avatarFriendsManager.sendRequestRemove(self.avId)
        unloadFriendInviter()

    def __handleStop(self):
        if base.config.GetBool('want-qa-regression', 0):
            self.notify.info('QA-REGRESSION: BREAKAFRIENDSHIP: Break a friendship')
        self.fsm.request('endFriendship')

    def __handleYes(self):
        if self.fsm.getCurrentState().getName() == 'endFriendship':
            self.fsm.request('friendsNoMore')
        else:
            unloadFriendInviter()

    def __handleToon(self):
        if self.fsm.getCurrentState().getName() == 'begin':
            self.fsm.request('check')
        else:
            unloadFriendInviter()

    def __handlePlayer(self):
        if self.fsm.getCurrentState().getName() == 'begin':
            self.playerFriend = 1
            self.fsm.request('check')
        else:
            unloadFriendInviter()

    def __handleNo(self):
        unloadFriendInviter()

    def __handleList(self):
        messenger.send('openFriendsList')

    def __friendConsidering(self, yesNoAlready, context):
        if yesNoAlready == 1:
            self.context = context
            self.fsm.request('asking')
        elif yesNoAlready == 0:
            self.fsm.request('notAvailable')
        elif yesNoAlready == 2:
            self.fsm.request('already')
        elif yesNoAlready == 3:
            self.fsm.request('self')
        elif yesNoAlready == 4:
            self.fsm.request('ignored')
        elif yesNoAlready == 6:
            self.fsm.request('notAcceptingFriends')
        elif yesNoAlready == 10:
            self.fsm.request('no')
        elif yesNoAlready == 13:
            self.fsm.request('otherTooMany')
        else:
            self.notify.warning('Got unexpected response to friendConsidering: %s' % yesNoAlready)
            self.fsm.request('maybe')

    def __friendResponse(self, yesNoMaybe, context):
        if self.context != context:
            self.notify.warning('Unexpected change of context from %s to %s.' % (self.context, context))
            self.context = context
        if yesNoMaybe == 1:
            self.fsm.request('yes')
        elif yesNoMaybe == 0:
            self.fsm.request('no')
        elif yesNoMaybe == 3:
            self.fsm.request('otherTooMany')
        else:
            self.notify.warning('Got unexpected response to friendResponse: %s' % yesNoMaybe)
            self.fsm.request('maybe')

    def __playerFriendRejectResponse(self, avId, reason):
        self.notify.debug('Got reject response to friendResponse: %s' % reason)
        if reason == RejectCode.RejectCode.INVITATION_DECLINED:
            self.fsm.request('no')
        elif reason == RejectCode.RejectCode.FRIENDS_LIST_FULL:
            self.fsm.request('otherTooMany')
        else:
            self.notify.warning('Got unexpected response to friendResponse: %s' % reason)
            self.fsm.request('maybe')

    def __playerFriendAcceptResponse(self):
        self.fsm.request('yes')

    def __handleDisableAvatar(self):
        self.fsm.request('wentAway')
