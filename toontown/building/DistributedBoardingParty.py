from pandac.PandaModules import *
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownGlobals
from direct.distributed import DistributedObject
from toontown.toon import GroupInvitee
from toontown.toon import GroupPanel
from toontown.toon import BoardingGroupInviterPanels
from toontown.building import BoardingPartyBase
from direct.gui.DirectGui import *
from toontown.toontowngui import TTDialog
from toontown.hood import ZoneUtil
from toontown.toontowngui import TeaserPanel
from direct.interval.IntervalGlobal import *
import BoardingGroupShow

class DistributedBoardingParty(DistributedObject.DistributedObject, BoardingPartyBase.BoardingPartyBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedBoardingParty')
    InvitationFailedTimeout = 60.0

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        BoardingPartyBase.BoardingPartyBase.__init__(self)
        self.groupInviteePanel = None
        self.groupPanel = None
        self.inviterPanels = BoardingGroupInviterPanels.BoardingGroupInviterPanels()
        self.lastInvitationFailedMessage = {}
        self.goToPreShowTrack = None
        self.goToShowTrack = None
        return

    def generate(self):
        self.load()
        DistributedObject.DistributedObject.generate(self)
        localAvatar.boardingParty = self

    def announceGenerate(self):
        canonicalZoneId = ZoneUtil.getCanonicalZoneId(self.zoneId)
        self.notify.debug('canonicalZoneId = %s' % canonicalZoneId)
        localAvatar.chatMgr.chatInputSpeedChat.addBoardingGroupMenu(canonicalZoneId)
        if base.config.GetBool('want-singing', 0):
            localAvatar.chatMgr.chatInputSpeedChat.addSingingGroupMenu()

    def delete(self):
        DistributedObject.DistributedObject.delete(self)

    def disable(self):
        self.finishGoToPreShowTrack()
        self.finishGoToShowTrack()
        self.forceCleanupInviteePanel()
        self.forceCleanupInviterPanels()
        self.inviterPanels = None
        if self.groupPanel:
            self.groupPanel.cleanup()
        self.groupPanel = None
        DistributedObject.DistributedObject.disable(self)
        BoardingPartyBase.BoardingPartyBase.cleanup(self)
        localAvatar.boardingParty = None
        localAvatar.chatMgr.chatInputSpeedChat.removeBoardingGroupMenu()
        self.lastInvitationFailedMessage = {}
        return

    def getElevatorIdList(self):
        return self.elevatorIdList

    def setElevatorIdList(self, elevatorIdList):
        self.notify.debug('setElevatorIdList')
        self.elevatorIdList = elevatorIdList

    def load(self):
        pass

    def postGroupInfo(self, leaderId, memberList, inviteeList, kickedList):
        self.notify.debug('postgroupInfo')
        isMyGroup = 0
        removedMemberIdList = []
        if self.groupListDict.has_key(leaderId):
            oldGroupEntry = self.groupListDict[leaderId]
        else:
            oldGroupEntry = [[], [], []]
        oldMemberList = oldGroupEntry[0]
        newGroupEntry = [memberList, inviteeList, kickedList]
        self.groupListDict[leaderId] = newGroupEntry
        if not len(oldMemberList) == len(memberList):
            for oldMember in oldMemberList:
                if oldMember not in memberList:
                    if oldMember in self.avIdDict:
                        if self.avIdDict[oldMember] == leaderId:
                            self.avIdDict.pop(oldMember)
                            removedMemberIdList.append(oldMember)

        self.avIdDict[leaderId] = leaderId
        if leaderId == localAvatar.doId:
            isMyGroup = 1
        for memberId in memberList:
            self.avIdDict[memberId] = leaderId
            if memberId == localAvatar.doId:
                isMyGroup = 1

        if newGroupEntry[0] == [0] or not newGroupEntry[0]:
            dgroup = self.groupListDict.pop(leaderId)
            for memberId in dgroup[0]:
                if self.avIdDict.has_key(memberId):
                    self.avIdDict.pop(memberId)

        if isMyGroup:
            self.notify.debug('new info posted on my group')
            if not self.groupPanel:
                self.groupPanel = GroupPanel.GroupPanel(self)
            messenger.send('updateGroupStatus')
            for removedMemberId in removedMemberIdList:
                removedMember = base.cr.doId2do.get(removedMemberId)
                if not removedMember:
                    removedMember = base.cr.identifyFriend(removedMemberId)
                if removedMember:
                    removedMemberName = removedMember.name
                    messageText = TTLocalizer.BoardingMessageLeftGroup % removedMemberName
                    localAvatar.setSystemMessage(0, messageText, WhisperPopup.WTToontownBoardingGroup)

        elif localAvatar.doId in oldMemberList and localAvatar.doId not in memberList:
            messenger.send('updateGroupStatus')
            if self.groupPanel:
                self.groupPanel.cleanup()
            self.groupPanel = None
        else:
            self.notify.debug('new info posted on some other group')
        return

    def postInvite(self, leaderId, inviterId):
        self.notify.debug('post Invite')
        if not base.cr.avatarFriendsManager.checkIgnored(inviterId):
            inviter = base.cr.doId2do.get(inviterId)
            if inviter:
                if self.inviterPanels.isInvitingPanelUp() or self.inviterPanels.isInvitationRejectedPanelUp():
                    self.inviterPanels.forceCleanup()
                self.groupInviteePanel = GroupInvitee.GroupInvitee()
                self.groupInviteePanel.make(self, inviter, leaderId)
                if base.config.GetBool('reject-boarding-group-invites', 0):
                    self.groupInviteePanel.forceCleanup()
                    self.groupInviteePanel = None
        return

    def postKick(self, leaderId):
        self.notify.debug('%s was kicked out of the Boarding Group by %s' % (localAvatar.doId, leaderId))
        localAvatar.setSystemMessage(0, TTLocalizer.BoardingMessageKickedOut, WhisperPopup.WTToontownBoardingGroup)

    def postSizeReject(self, leaderId, inviterId, inviteeId):
        self.notify.debug('%s was not invited because the group is full' % inviteeId)

    def postKickReject(self, leaderId, inviterId, inviteeId):
        self.notify.debug('%s was not invited because %s has kicked them from the group' % (inviteeId, leaderId))

    def postInviteDelcined(self, inviteeId):
        self.notify.debug("%s delinced %s's Boarding Group invitation." % (inviteeId, localAvatar.doId))
        invitee = base.cr.doId2do.get(inviteeId)
        if invitee:
            self.inviterPanels.createInvitationRejectedPanel(self, inviteeId)

    def postInviteAccepted(self, inviteeId):
        self.notify.debug("%s accepted %s's Boarding Group invitation." % (inviteeId, localAvatar.doId))
        if self.inviterPanels.isInvitingPanelIdCorrect(inviteeId):
            self.inviterPanels.destroyInvitingPanel()

    def postInviteCanceled(self):
        self.notify.debug('The invitation to the Boarding Group was cancelled')
        if self.isInviteePanelUp():
            self.groupInviteePanel.cleanup()
            self.groupInviteePanel = None
        return

    def postInviteNotQualify(self, avId, reason, elevatorId):
        messenger.send('updateGroupStatus')
        rejectText = ''
        minLaff = TTLocalizer.BoardingMore
        if elevatorId:
            elevator = base.cr.doId2do.get(elevatorId)
            if elevator:
                minLaff = elevator.minLaff
        if avId == localAvatar.doId:
            if reason == BoardingPartyBase.BOARDCODE_MINLAFF:
                rejectText = TTLocalizer.BoardingInviteMinLaffInviter % minLaff
            if reason == BoardingPartyBase.BOARDCODE_PROMOTION:
                rejectText = TTLocalizer.BoardingInvitePromotionInviter
        else:
            avatar = base.cr.doId2do.get(avId)
            if avatar:
                avatarNameText = avatar.name
            else:
                avatarNameText = ''
            if reason == BoardingPartyBase.BOARDCODE_MINLAFF:
                rejectText = TTLocalizer.BoardingInviteMinLaffInvitee % (avatarNameText, minLaff)
            if reason == BoardingPartyBase.BOARDCODE_PROMOTION:
                rejectText = TTLocalizer.BoardingInvitePromotionInvitee % avatarNameText
            if reason == BoardingPartyBase.BOARDCODE_BATTLE:
                rejectText = TTLocalizer.TeleportPanelNotAvailable % avatarNameText
            if reason == BoardingPartyBase.BOARDCODE_NOT_PAID:
                rejectText = TTLocalizer.BoardingInviteNotPaidInvitee % avatarNameText
            if reason == BoardingPartyBase.BOARDCODE_DIFF_GROUP:
                rejectText = TTLocalizer.BoardingInviteeInDiffGroup % avatarNameText
            if reason == BoardingPartyBase.BOARDCODE_PENDING_INVITE:
                rejectText = TTLocalizer.BoardingInviteePendingIvite % avatarNameText
            if reason == BoardingPartyBase.BOARDCODE_IN_ELEVATOR:
                rejectText = TTLocalizer.BoardingInviteeInElevator % avatarNameText
        if self.inviterPanels.isInvitingPanelIdCorrect(avId) or avId == localAvatar.doId:
            self.inviterPanels.destroyInvitingPanel()
        self.showMe(rejectText)

    def postAlreadyInGroup(self):
        self.showMe(TTLocalizer.BoardingAlreadyInGroup)

    def postGroupAlreadyFull(self):
        self.showMe(TTLocalizer.BoardingGroupAlreadyFull)

    def postSomethingMissing(self):
        self.showMe(TTLocalizer.BoardcodeMissing)

    def postRejectBoard(self, elevatorId, reason, avatarsFailingRequirements, avatarsInBattle):
        self.showRejectMessage(elevatorId, reason, avatarsFailingRequirements, avatarsInBattle)
        self.enableGoButton()

    def postRejectGoto(self, elevatorId, reason, avatarsFailingRequirements, avatarsInBattle):
        self.showRejectMessage(elevatorId, reason, avatarsFailingRequirements, avatarsInBattle)

    def postMessageInvited(self, inviteeId, inviterId):
        inviterName = ''
        inviteeName = ''
        inviter = base.cr.doId2do.get(inviterId)
        if inviter:
            inviterName = inviter.name
        invitee = base.cr.doId2do.get(inviteeId)
        if invitee:
            inviteeName = invitee.name
        messageText = TTLocalizer.BoardingMessageInvited % (inviterName, inviteeName)
        localAvatar.setSystemMessage(0, messageText, WhisperPopup.WTToontownBoardingGroup)

    def postMessageInvitationFailed(self, inviterId):
        inviterName = ''
        inviter = base.cr.doId2do.get(inviterId)
        if inviter:
            inviterName = inviter.name
        if self.invitationFailedMessageOk(inviterId):
            messageText = TTLocalizer.BoardingMessageInvitationFailed % inviterName
            localAvatar.setSystemMessage(0, messageText, WhisperPopup.WTToontownBoardingGroup)

    def postMessageAcceptanceFailed(self, inviteeId, reason):
        inviteeName = ''
        messageText = ''
        invitee = base.cr.doId2do.get(inviteeId)
        if invitee:
            inviteeName = invitee.name
        if reason == BoardingPartyBase.INVITE_ACCEPT_FAIL_GROUP_FULL:
            messageText = TTLocalizer.BoardingMessageGroupFull % inviteeName
        localAvatar.setSystemMessage(0, messageText, WhisperPopup.WTToontownBoardingGroup)
        if self.inviterPanels.isInvitingPanelIdCorrect(inviteeId):
            self.inviterPanels.destroyInvitingPanel()

    def invitationFailedMessageOk(self, inviterId):
        now = globalClock.getFrameTime()
        lastTime = self.lastInvitationFailedMessage.get(inviterId, None)
        if lastTime:
            elapsedTime = now - lastTime
            if elapsedTime < self.InvitationFailedTimeout:
                return False
        self.lastInvitationFailedMessage[inviterId] = now
        return True

    def showRejectMessage(self, elevatorId, reason, avatarsFailingRequirements, avatarsInBattle):
        leaderId = localAvatar.doId
        rejectText = ''

        def getAvatarText(avIdList):
            avatarText = ''
            nameList = []
            for avId in avIdList:
                avatar = base.cr.doId2do.get(avId)
                if avatar:
                    nameList.append(avatar.name)

            if len(nameList) > 0:
                lastName = nameList.pop()
                avatarText = lastName
                if len(nameList) > 0:
                    secondLastName = nameList.pop()
                    for name in nameList:
                        avatarText = name + ', '

                    avatarText += secondLastName + ' ' + TTLocalizer.And + ' ' + lastName
            return avatarText

        if reason == BoardingPartyBase.BOARDCODE_MINLAFF:
            self.notify.debug("%s 's group cannot board because it does not have enough laff points." % leaderId)
            elevator = base.cr.doId2do.get(elevatorId)
            if elevator:
                minLaffPoints = elevator.minLaff
            else:
                minLaffPoints = TTLocalizer.BoardingMore
            if leaderId in avatarsFailingRequirements:
                rejectText = TTLocalizer.BoardcodeMinLaffLeader % minLaffPoints
            else:
                avatarNameText = getAvatarText(avatarsFailingRequirements)
                if len(avatarsFailingRequirements) == 1:
                    rejectText = TTLocalizer.BoardcodeMinLaffNonLeaderSingular % (avatarNameText, minLaffPoints)
                else:
                    rejectText = TTLocalizer.BoardcodeMinLaffNonLeaderPlural % (avatarNameText, minLaffPoints)
        elif reason == BoardingPartyBase.BOARDCODE_PROMOTION:
            self.notify.debug("%s 's group cannot board because it does not have enough promotion merits." % leaderId)
            if leaderId in avatarsFailingRequirements:
                rejectText = TTLocalizer.BoardcodePromotionLeader
            else:
                avatarNameText = getAvatarText(avatarsFailingRequirements)
                if len(avatarsFailingRequirements) == 1:
                    rejectText = TTLocalizer.BoardcodePromotionNonLeaderSingular % avatarNameText
                else:
                    rejectText = TTLocalizer.BoardcodePromotionNonLeaderPlural % avatarNameText
        elif reason == BoardingPartyBase.BOARDCODE_BATTLE:
            self.notify.debug("%s 's group cannot board because it is in a battle" % leaderId)
            if leaderId in avatarsInBattle:
                rejectText = TTLocalizer.BoardcodeBattleLeader
            else:
                avatarNameText = getAvatarText(avatarsInBattle)
                if len(avatarsInBattle) == 1:
                    rejectText = TTLocalizer.BoardcodeBattleNonLeaderSingular % avatarNameText
                else:
                    rejectText = TTLocalizer.BoardcodeBattleNonLeaderPlural % avatarNameText
        elif reason == BoardingPartyBase.BOARDCODE_SPACE:
            self.notify.debug("%s 's group cannot board there was not enough room" % leaderId)
            rejectText = TTLocalizer.BoardcodeSpace
        elif reason == BoardingPartyBase.BOARDCODE_MISSING:
            self.notify.debug("%s 's group cannot board because something was missing" % leaderId)
            rejectText = TTLocalizer.BoardcodeMissing
        base.localAvatar.elevatorNotifier.showMe(rejectText)

    def postGroupDissolve(self, quitterId, leaderId, memberList, kick):
        self.notify.debug('%s group has dissolved' % leaderId)
        isMyGroup = 0
        if localAvatar.doId == quitterId or localAvatar.doId == leaderId:
            isMyGroup = 1
        if self.groupListDict.has_key(leaderId):
            if leaderId == localAvatar.doId:
                isMyGroup = 1
                if self.avIdDict.has_key(leaderId):
                    self.avIdDict.pop(leaderId)
            dgroup = self.groupListDict.pop(leaderId)
            for memberId in memberList:
                if memberId == localAvatar.doId:
                    isMyGroup = 1
                if self.avIdDict.has_key(memberId):
                    self.avIdDict.pop(memberId)

        if isMyGroup:
            self.notify.debug('new info posted on my group')
            messenger.send('updateGroupStatus')
            groupFormed = False
            if self.groupPanel:
                groupFormed = True
                self.groupPanel.cleanup()
            self.groupPanel = None
            if groupFormed:
                if leaderId == quitterId:
                    if not localAvatar.doId == leaderId:
                        localAvatar.setSystemMessage(0, TTLocalizer.BoardingMessageGroupDissolved, WhisperPopup.WTToontownBoardingGroup)
                elif not kick:
                    if not localAvatar.doId == quitterId:
                        quitter = base.cr.doId2do.get(quitterId)
                        if quitter:
                            quitterName = quitter.name
                            messageText = TTLocalizer.BoardingMessageLeftGroup % quitterName
                            localAvatar.setSystemMessage(0, messageText, WhisperPopup.WTToontownBoardingGroup)
                        else:
                            messageText = TTLocalizer.BoardingMessageGroupDisbandedGeneric
                            localAvatar.setSystemMessage(0, messageText, WhisperPopup.WTToontownBoardingGroup)
        return

    def requestInvite(self, inviteeId):
        self.notify.debug('requestInvite %s' % inviteeId)
        elevator = base.cr.doId2do.get(self.getElevatorIdList()[0])
        if elevator:
            if elevator.allowedToEnter(self.zoneId):
                if inviteeId in self.getGroupKickList(localAvatar.doId):
                    if not self.isGroupLeader(localAvatar.doId):
                        avatar = base.cr.doId2do.get(inviteeId)
                        if avatar:
                            avatarNameText = avatar.name
                        else:
                            avatarNameText = ''
                        rejectText = TTLocalizer.BoardingInviteeInKickOutList % avatarNameText
                        self.showMe(rejectText)
                        return
                if self.inviterPanels.isInvitingPanelUp():
                    self.showMe(TTLocalizer.BoardingPendingInvite, pos=(0, 0, 0))
                elif len(self.getGroupMemberList(localAvatar.doId)) >= self.maxSize:
                    self.showMe(TTLocalizer.BoardingInviteGroupFull)
                else:
                    invitee = base.cr.doId2do.get(inviteeId)
                    if invitee:
                        self.inviterPanels.createInvitingPanel(self, inviteeId)
                        self.sendUpdate('requestInvite', [inviteeId])
            else:
                place = base.cr.playGame.getPlace()
                if place:
                    place.fsm.request('stopped')
                self.teaserDialog = TeaserPanel.TeaserPanel(pageName='cogHQ', doneFunc=self.handleOkTeaser)

    def handleOkTeaser(self):
        self.teaserDialog.destroy()
        del self.teaserDialog
        place = base.cr.playGame.getPlace()
        if place:
            place.fsm.request('walk')

    def requestCancelInvite(self, inviteeId):
        self.sendUpdate('requestCancelInvite', [inviteeId])

    def requestAcceptInvite(self, leaderId, inviterId):
        self.notify.debug('requestAcceptInvite %s %s' % (leaderId, inviterId))
        self.sendUpdate('requestAcceptInvite', [leaderId, inviterId])

    def requestRejectInvite(self, leaderId, inviterId):
        self.sendUpdate('requestRejectInvite', [leaderId, inviterId])

    def requestKick(self, kickId):
        self.sendUpdate('requestKick', [kickId])

    def requestLeave(self):
        if self.goToShowTrack and self.goToShowTrack.isPlaying():
            return
        place = base.cr.playGame.getPlace()
        if place:
            if not place.getState() == 'elevator':
                if self.avIdDict.has_key(localAvatar.doId):
                    leaderId = self.avIdDict[localAvatar.doId]
                    self.sendUpdate('requestLeave', [leaderId])

    def handleEnterElevator(self, elevator):
        if self.getGroupLeader(localAvatar.doId) == localAvatar.doId:
            if base.localAvatar.hp > 0:
                self.cr.playGame.getPlace().detectedElevatorCollision(elevator)
                self.sendUpdate('requestBoard', [elevator.doId])
                elevatorId = elevator.doId
                if elevatorId in self.elevatorIdList:
                    offset = self.elevatorIdList.index(elevatorId)
                    if self.groupPanel:
                        self.groupPanel.scrollToDestination(offset)
                    self.informDestChange(offset)
                self.disableGoButton()

    def informDestChange(self, offset):
        self.sendUpdate('informDestinationInfo', [offset])

    def postDestinationInfo(self, offset):
        if self.groupPanel:
            self.groupPanel.changeDestination(offset)

    def enableGoButton(self):
        if self.groupPanel:
            self.groupPanel.enableGoButton()
            self.groupPanel.enableDestinationScrolledList()

    def disableGoButton(self):
        if self.groupPanel:
            self.groupPanel.disableGoButton()
            self.groupPanel.disableDestinationScrolledList()

    def isInviteePanelUp(self):
        if self.groupInviteePanel:
            if not self.groupInviteePanel.isEmpty():
                return True
            self.groupInviteePanel = None
        return False

    def requestGoToFirstTime(self, elevatorId):
        self.waitingForFirstResponse = True
        self.firstRequestAccepted = False
        self.sendUpdate('requestGoToFirstTime', [elevatorId])
        self.startGoToPreShow(elevatorId)

    def acceptGoToFirstTime(self, elevatorId):
        self.waitingForFirstResponse = False
        self.firstRequestAccepted = True

    def requestGoToSecondTime(self, elevatorId):
        if not self.waitingForFirstResponse:
            if self.firstRequestAccepted:
                self.firstRequestAccepted = False
                self.disableGoButton()
                self.sendUpdate('requestGoToSecondTime', [elevatorId])
        else:
            self.postRejectGoto(elevatorId, BoardingPartyBase.BOARDCODE_MISSING, [], [])
            self.cancelGoToElvatorDest()

    def acceptGoToSecondTime(self, elevatorId):
        self.startGoToShow(elevatorId)

    def rejectGoToRequest(self, elevatorId, reason, avatarsFailingRequirements, avatarsInBattle):
        self.firstRequestAccepted = False
        self.waitingForFirstResponse = False
        self.cancelGoToElvatorDest()
        self.postRejectGoto(elevatorId, reason, avatarsFailingRequirements, avatarsInBattle)

    def startGoToPreShow(self, elevatorId):
        self.notify.debug('Starting Go Pre Show.')
        place = base.cr.playGame.getPlace()
        if place:
            place.setState('stopped')
        goButtonPreShow = BoardingGroupShow.BoardingGroupShow(localAvatar)
        goButtonPreShowTrack = goButtonPreShow.getGoButtonPreShow()
        if self.groupPanel:
            self.groupPanel.changeGoToCancel()
            self.groupPanel.disableQuitButton()
            self.groupPanel.disableDestinationScrolledList()
        self.finishGoToPreShowTrack()
        self.goToPreShowTrack = Sequence()
        self.goToPreShowTrack.append(goButtonPreShowTrack)
        self.goToPreShowTrack.append(Func(self.requestGoToSecondTime, elevatorId))
        self.goToPreShowTrack.start()

    def finishGoToPreShowTrack(self):
        if self.goToPreShowTrack:
            self.goToPreShowTrack.finish()
            self.goToPreShowTrack = None
        return

    def startGoToShow(self, elevatorId):
        self.notify.debug('Starting Go Show.')
        localAvatar.boardingParty.forceCleanupInviterPanels()
        elevatorName = self.__getDestName(elevatorId)
        if self.groupPanel:
            self.groupPanel.disableQuitButton()
        goButtonShow = BoardingGroupShow.BoardingGroupShow(localAvatar)
        place = base.cr.playGame.getPlace()
        if place:
            place.setState('stopped')
        self.goToShowTrack = goButtonShow.getGoButtonShow(elevatorName)
        self.goToShowTrack.start()

    def finishGoToShowTrack(self):
        if self.goToShowTrack:
            self.goToShowTrack.finish()
            self.goToShowTrack = None
        return

    def cancelGoToElvatorDest(self):
        self.notify.debug('%s cancelled the GoTo Button.' % localAvatar.doId)
        self.firstRequestAccepted = False
        self.waitingForFirstResponse = False
        self.finishGoToPreShowTrack()
        place = base.cr.playGame.getPlace()
        if place:
            place.setState('walk')
        if self.groupPanel:
            self.groupPanel.changeCancelToGo()
            self.groupPanel.enableGoButton()
            self.groupPanel.enableQuitButton()
            self.groupPanel.enableDestinationScrolledList()

    def __getDestName(self, elevatorId):
        elevator = base.cr.doId2do.get(elevatorId)
        destName = ''
        if elevator:
            destName = elevator.getDestName()
        return destName

    def showMe(self, message, pos = None):
        base.localAvatar.elevatorNotifier.showMeWithoutStopping(message, pos)

    def forceCleanupInviteePanel(self):
        if self.isInviteePanelUp():
            self.groupInviteePanel.forceCleanup()
            self.groupInviteePanel = None
        return

    def forceCleanupInviterPanels(self):
        if self.inviterPanels:
            self.inviterPanels.forceCleanup()
