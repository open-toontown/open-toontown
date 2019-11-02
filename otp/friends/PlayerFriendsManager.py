from direct.distributed.DistributedObjectGlobal import DistributedObjectGlobal
from direct.directnotify.DirectNotifyGlobal import directNotify
from otp.otpbase import OTPGlobals
from otp.avatar.Avatar import teleportNotify
from otp.friends import FriendResponseCodes

class PlayerFriendsManager(DistributedObjectGlobal):
    notify = directNotify.newCategory('PlayerFriendsManager')

    def __init__(self, cr):
        DistributedObjectGlobal.__init__(self, cr)
        self.playerFriendsList = set()
        self.playerId2Info = {}
        self.playerAvId2avInfo = {}
        self.accept('gotExtraFriendHandles', self.__handleFriendHandles)

    def delete(self):
        self.ignoreAll()

    def sendRequestInvite(self, playerId):
        print 'PFM sendRequestInvite id:%s' % playerId
        self.sendUpdate('requestInvite', [0, playerId, True])

    def sendRequestDecline(self, playerId):
        self.sendUpdate('requestDecline', [0, playerId])

    def sendRequestRemove(self, playerId):
        self.sendUpdate('requestRemove', [0, playerId])

    def sendRequestUnlimitedSecret(self):
        self.sendUpdate('requestUnlimitedSecret', [0])

    def sendRequestLimitedSecret(self, username, password):
        self.sendUpdate('requestLimitedSecret', [0, username, password])

    def sendRequestUseUnlimitedSecret(self, secret):
        pass

    def sendRequestUseLimitedSecret(self, secret, username, password):
        pass

    def sendSCWhisper(self, recipientId, msgId):
        self.sendUpdate('whisperSCTo', [0, recipientId, msgId])

    def sendSCCustomWhisper(self, recipientId, msgId):
        self.sendUpdate('whisperSCCustomTo', [0, recipientId, msgId])

    def sendSCEmoteWhisper(self, recipientId, msgId):
        self.sendUpdate('whisperSCEmoteTo', [0, recipientId, msgId])

    def setTalkAccount(self, toAc, fromAc, fromName, message, mods, flags):
        localAvatar.displayTalkAccount(fromAc, fromName, message, mods)
        toName = None
        friendInfo = self.getFriendInfo(toAc)
        if friendInfo:
            toName = friendInfo.playerName
        elif toAc == localAvatar.DISLid:
            toName = localAvatar.getName()
        base.talkAssistant.receiveAccountTalk(None, None, fromAc, fromName, toAc, toName, message)
        return

    def invitationFrom(self, playerId, avatarName):
        messenger.send(OTPGlobals.PlayerFriendInvitationEvent, [playerId, avatarName])

    def retractInvite(self, playerId):
        messenger.send(OTPGlobals.PlayerFriendRetractInviteEvent, [playerId])

    def rejectInvite(self, playerId, reason):
        messenger.send(OTPGlobals.PlayerFriendRejectInviteEvent, [playerId, reason])

    def rejectRemove(self, playerId, reason):
        messenger.send(OTPGlobals.PlayerFriendRejectRemoveEvent, [playerId, reason])

    def secretResponse(self, secret):
        print 'secretResponse %s' % secret
        messenger.send(OTPGlobals.PlayerFriendNewSecretEvent, [secret])

    def rejectSecret(self, reason):
        print 'rejectSecret %s' % reason
        messenger.send(OTPGlobals.PlayerFriendRejectNewSecretEvent, [reason])

    def rejectUseSecret(self, reason):
        print 'rejectUseSecret %s' % reason
        messenger.send(OTPGlobals.PlayerFriendRejectUseSecretEvent, [reason])

    def invitationResponse(self, playerId, respCode, context):
        if respCode == FriendResponseCodes.INVITATION_RESP_DECLINE:
            messenger.send(OTPGlobals.PlayerFriendRejectInviteEvent, [playerId, respCode])
        elif respCode == FriendResponseCodes.INVITATION_RESP_NEW_FRIENDS:
            pass

    def updatePlayerFriend(self, id, info, isNewFriend):
        self.notify.warning('updatePlayerFriend: %s, %s, %s' % (id, info, isNewFriend))
        info.calcUnderstandableYesNo()
        if info.playerName[0:5] == 'Guest':
            info.playerName = 'Guest ' + info.playerName[5:]
        if id not in self.playerFriendsList:
            self.playerFriendsList.add(id)
            self.playerId2Info[id] = info
            messenger.send(OTPGlobals.PlayerFriendAddEvent, [id, info, isNewFriend])
        elif self.playerId2Info.has_key(id):
            if not self.playerId2Info[id].onlineYesNo and info.onlineYesNo:
                self.playerId2Info[id] = info
                messenger.send('playerOnline', [id])
                base.talkAssistant.receiveFriendAccountUpdate(id, info.playerName, info.onlineYesNo)
            elif self.playerId2Info[id].onlineYesNo and not info.onlineYesNo:
                self.playerId2Info[id] = info
                messenger.send('playerOffline', [id])
                base.talkAssistant.receiveFriendAccountUpdate(id, info.playerName, info.onlineYesNo)
        if not self.askAvatarKnownHere(info.avatarId):
            self.requestAvatarInfo(info.avatarId)
        self.playerId2Info[id] = info
        av = base.cr.doId2do.get(info.avatarId, None)
        if av is not None:
            av.considerUnderstandable()
        messenger.send(OTPGlobals.PlayerFriendUpdateEvent, [id, info])
        return

    def removePlayerFriend(self, id):
        if id not in self.playerFriendsList:
            return
        self.playerFriendsList.remove(id)
        info = self.playerId2Info.pop(id, None)
        if info is not None:
            av = base.cr.doId2do.get(info.avatarId, None)
            if av is not None:
                av.considerUnderstandable()
        messenger.send(OTPGlobals.PlayerFriendRemoveEvent, [id])
        return

    def whisperSCFrom(self, playerId, msg):
        base.talkAssistant.receivePlayerWhisperSpeedChat(msg, playerId)

    def isFriend(self, pId):
        return self.isPlayerFriend(pId)

    def isPlayerFriend(self, pId):
        if not pId:
            return 0
        return pId in self.playerFriendsList

    def isAvatarOwnerPlayerFriend(self, avId):
        pId = self.findPlayerIdFromAvId(avId)
        if pId and self.isPlayerFriend(pId):
            return True
        else:
            return False

    def getFriendInfo(self, pId):
        return self.playerId2Info.get(pId)

    def findPlayerIdFromAvId(self, avId):
        for playerId in self.playerId2Info:
            if self.playerId2Info[playerId].avatarId == avId:
                if self.playerId2Info[playerId].onlineYesNo:
                    return playerId

        return None

    def findAvIdFromPlayerId(self, pId):
        pInfo = self.playerId2Info.get(pId)
        if pInfo:
            return pInfo.avatarId
        else:
            return None
        return None

    def findPlayerInfoFromAvId(self, avId):
        playerId = self.findPlayerIdFromAvId(avId)
        if playerId:
            return self.getFriendInfo(playerId)
        else:
            return None
        return None

    def askAvatarOnline(self, avId):
        returnValue = 0
        if self.cr.doId2do.has_key(avId):
            returnValue = 1
        if self.playerAvId2avInfo.has_key(avId):
            playerId = self.findPlayerIdFromAvId(avId)
            if self.playerId2Info.has_key(playerId):
                playerInfo = self.playerId2Info[playerId]
                if playerInfo.onlineYesNo:
                    returnValue = 1
        return returnValue

    def countTrueFriends(self):
        count = 0
        for id in self.playerId2Info:
            if self.playerId2Info[id].openChatFriendshipYesNo:
                count += 1

        return count

    def askTransientFriend(self, avId):
        if self.playerAvId2avInfo.has_key(avId) and not base.cr.isAvatarFriend(avId):
            return 1
        else:
            return 0

    def askAvatarKnown(self, avId):
        if self.askAvatarKnownElseWhere(avId) or self.askAvatarKnownHere(avId):
            return 1
        else:
            return 0

    def askAvatarKnownElseWhere(self, avId):
        if hasattr(base, 'cr'):
            if base.cr.askAvatarKnown(avId):
                return 1
        return 0

    def askAvatarKnownHere(self, avId):
        if self.playerAvId2avInfo.has_key(avId):
            return 1
        else:
            return 0

    def requestAvatarInfo(self, avId):
        if hasattr(base, 'cr'):
            base.cr.queueRequestAvatarInfo(avId)

    def __handleFriendHandles(self, handleList):
        for handle in handleList:
            self.playerAvId2avInfo[handle.getDoId()] = handle

        messenger.send('friendsListChanged')

    def getAvHandleFromId(self, avId):
        if self.playerAvId2avInfo.has_key(avId):
            return self.playerAvId2avInfo[avId]
        else:
            return None
        return None

    def identifyFriend(self, avId):
        handle = None
        teleportNotify.debug('identifyFriend(%s)' % avId)
        handle = base.cr.identifyFriend(avId)
        if not handle:
            teleportNotify.debug('getAvHandleFromId(%s)' % avId)
            handle = self.getAvHandleFromId(avId)
        return handle

    def getAllOnlinePlayerAvatars(self):
        returnList = []
        for avatarId in self.playerAvId2avInfo:
            playerId = self.findPlayerIdFromAvId(avatarId)
            if playerId:
                if self.playerId2Info[playerId].onlineYesNo:
                    returnList.append(avatarId)

        return returnList

    def identifyAvatar(self, doId):
        if base.cr.doId2do.has_key(doId):
            return base.cr.doId2do[doId]
        else:
            return self.identifyFriend(doId)

    def friendsListFull(self):
        return len(self.playerFriendsList) >= OTPGlobals.MaxPlayerFriends
