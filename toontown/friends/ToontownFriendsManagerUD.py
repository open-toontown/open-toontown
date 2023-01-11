from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectGlobalUD import DistributedObjectGlobalUD
from direct.distributed.PyDatagram import *

from otp.otpbase import OTPGlobals


class FriendsOperation:

    def __init__(self, friendsManager, sender):
        self.friendsManager = friendsManager
        self.sender = sender

    def _handleDone(self):
        # TODO
        pass

    def _handleError(self, error):
        # TODO
        pass


class GetFriendsListOperation(FriendsOperation):

    def __init__(self, friendsManager, sender):
        FriendsOperation.__init__(self, friendsManager, sender)
        self.friendsList = None
        self.tempFriendsList = None
        self.onlineFriends = None
        self.currentFriendIdx = None

    def start(self):
        self.friendsList = []
        self.tempFriendsList = []
        self.onlineFriends = []
        self.currentFriendIdx = 0
        self.friendsManager.air.dbInterface.queryObject(self.friendsManager.air.dbId, self.sender,
                                                        self.__handleSenderRetrieved)

    def __handleSenderRetrieved(self, dclass, fields):
        if dclass != self.friendsManager.air.dclassesByName['DistributedToonUD']:
            self._handleError('Retrieved sender is not a DistributedToonUD!')
            return

        self.tempFriendsList = fields['setFriendsList'][0]
        if len(self.tempFriendsList) <= 0:
            self._handleDone()
            return

        self.friendsManager.air.dbInterface.queryObject(self.friendsManager.air.dbId, self.tempFriendsList[0][0],
                                                        self.__handleFriendRetrieved)

    def __handleFriendRetrieved(self, dclass, fields):
        if dclass != self.friendsManager.air.dclassesByName['DistributedToonUD']:
            self._handleError('Retrieved friend is not a DistributedToonUD!')
            return

        friendId = self.tempFriendsList[self.currentFriendIdx][0]
        self.friendsList.append([friendId, fields['setName'][0], fields['setDNAString'][0], fields['setPetId'][0]])
        if len(self.friendsList) >= len(self.tempFriendsList):
            self.__checkFriendsOnline()
            return

        self.currentFriendIdx += 1
        self.friendsManager.air.dbInterface.queryObject(self.friendsManager.air.dbId,
                                                        self.tempFriendsList[self.currentFriendIdx][0],
                                                        self.__handleFriendRetrieved)

    def __checkFriendsOnline(self):
        self.currentFriendIdx = 0
        for friendDetails in self.friendsList:
            self.friendsManager.air.getActivated(friendDetails[0], self.__gotActivatedResp)

    def __gotActivatedResp(self, avId, activated):
        self.currentFriendIdx += 1
        if activated:
            self.onlineFriends.append(avId)

        if self.currentFriendIdx >= len(self.friendsList):
            self._handleDone()

    def __sendFriendsList(self, success):
        self.friendsManager.sendUpdateToAvatarId(self.sender, 'getFriendsListResponse', [success, self.friendsList if success else []])
        for friendId in self.onlineFriends:
            self.friendsManager.sendFriendOnline(self.sender, friendId, 0, 1)

    def _handleDone(self):
        self.__sendFriendsList(True)
        FriendsOperation._handleDone(self)

    def _handleError(self, error):
        self.__sendFriendsList(False)
        FriendsOperation._handleError(self, error)


class GetAvatarDetailsOperation(FriendsOperation):

    def __init__(self, friendsManager, sender):
        FriendsOperation.__init__(self, friendsManager, sender)
        self.avId = None
        self.dclass = None
        self.fields = None

    def start(self, avId):
        self.avId = avId
        self.fields = {}
        self.friendsManager.air.dbInterface.queryObject(self.friendsManager.air.dbId, avId,
                                                        self.__handleAvatarRetrieved)

    def __handleAvatarRetrieved(self, dclass, fields):
        if dclass not in (self.friendsManager.air.dclassesByName['DistributedToonUD'],
                          self.friendsManager.air.dclassesByName['DistributedPetAI']):
            self._handleError('Retrieved avatar is not a DistributedToonUD or DistributedPetAI!')
            return

        self.dclass = dclass
        self.fields = fields
        self.fields['avId'] = self.avId
        self._handleDone()

    def __packAvatarDetails(self, dclass, fields):
        # Pack required fields.
        fieldPacker = DCPacker()
        for i in range(dclass.getNumInheritedFields()):
            field = dclass.getInheritedField(i)
            if not field.isRequired() or field.asMolecularField():
                continue

            k = field.getName()
            v = fields.get(k, None)

            fieldPacker.beginPack(field)
            if not v:
                fieldPacker.packDefaultValue()
            else:
                field.packArgs(fieldPacker, v)

            fieldPacker.endPack()

        return fieldPacker.getBytes()

    def __sendAvatarDetails(self, success):
        datagram = PyDatagram()
        datagram.addUint32(self.fields['avId'])  # avId
        datagram.addUint8(0 if success else 1)  # returnCode
        if success:
            avatarDetails = self.__packAvatarDetails(self.dclass, self.fields)
            datagram.appendData(avatarDetails)  # fields

        self.friendsManager.sendUpdateToAvatarId(self.sender, 'getAvatarDetailsResponse', [datagram.getMessage()])

    def _handleDone(self):
        self.__sendAvatarDetails(True)
        FriendsOperation._handleDone(self)

    def _handleError(self, error):
        self.__sendAvatarDetails(False)
        FriendsOperation._handleError(self, error)


class MakeFriendsOperation(FriendsOperation):

    def __init__(self, friendsManager):
        FriendsOperation.__init__(self, friendsManager, None)
        self.avatarAId = None
        self.avatarBId = None
        self.flags = None
        self.context = None
        self.resultCode = None
        self.onlineToons = None
        self.avatarAFriendsList = None
        self.avatarBFriendsList = None

    def start(self, avatarAId, avatarBId, flags, context):
        self.avatarAId = avatarAId
        self.avatarBId = avatarBId
        self.flags = flags
        self.context = context
        self.resultCode = 0
        self.onlineToons = []
        self.friendsManager.air.getActivated(self.avatarAId, self.__gotActivatedAvatarA)

    def __handleActivatedResp(self, avId, activated):
        if activated:
            self.onlineToons.append(avId)

    def __gotActivatedAvatarA(self, avId, activated):
        self.__handleActivatedResp(avId, activated)
        self.friendsManager.air.getActivated(self.avatarBId, self.__gotActivatedAvatarB)

    def __handleMakeFriends(self, dclass, fields, friendId):
        if dclass != self.friendsManager.air.dclassesByName['DistributedToonUD']:
            self._handleError('Retrieved avatar is not a DistributedToonUD!')
            return False, []

        friendsList = fields['setFriendsList'][0]
        if len(friendsList) >= OTPGlobals.MaxFriends:
            self._handleError('Avatar\'s friends list is full!')
            return False, []

        newFriend = (friendId, self.flags)
        if newFriend in friendsList:
            self._handleError('Already friends!')
            return False, []

        friendsList.append(newFriend)
        return True, friendsList

    def __handleAvatarARetrieved(self, dclass, fields):
        success, avatarAFriendsList = self.__handleMakeFriends(dclass, fields, self.avatarBId)
        if success:
            self.avatarAFriendsList = avatarAFriendsList
            self.friendsManager.air.dbInterface.queryObject(self.friendsManager.air.dbId, self.avatarBId,
                                                            self.__handleAvatarBRetrieved)

    def __gotActivatedAvatarB(self, avId, activated):
        self.__handleActivatedResp(avId, activated)
        self.friendsManager.air.dbInterface.queryObject(self.friendsManager.air.dbId, self.avatarAId,
                                                        self.__handleAvatarARetrieved)

    def __handleAvatarBRetrieved(self, dclass, fields):
        success, avatarBFriendsList = self.__handleMakeFriends(dclass, fields, self.avatarAId)
        if success:
            self.avatarBFriendsList = avatarBFriendsList
            self._handleDone()

    def __handleSetFriendsList(self, avId, friendsList):
        if avId in self.onlineToons:
            self.friendsManager.sendUpdateToAvatar(avId, 'setFriendsList', [friendsList])
        else:
            self.friendsManager.air.dbInterface.updateObject(self.friendsManager.air.dbId, avId,
                                                             self.friendsManager.air.dclassesByName[
                                                                 'DistributedToonUD'],
                                                             {'setFriendsList': [friendsList]})

    def _handleDone(self):
        self.resultCode = 1
        if self.avatarAFriendsList is not None and self.avatarBFriendsList is not None:
            self.__handleSetFriendsList(self.avatarAId, self.avatarAFriendsList)
            self.__handleSetFriendsList(self.avatarBId, self.avatarBFriendsList)

        if self.avatarAId in self.onlineToons and self.avatarBId in self.onlineToons:
            self.friendsManager.declareObject(self.avatarAId, self.avatarBId)
            self.friendsManager.declareObject(self.avatarBId, self.avatarAId)

        self.friendsManager.sendMakeFriendsResponse(self.avatarAId, self.avatarBId, self.resultCode, self.context)
        FriendsOperation._handleDone(self)

    def _handleError(self, error):
        self.resultCode = 0
        self.friendsManager.sendMakeFriendsResponse(self.avatarAId, self.avatarBId, self.resultCode, self.context)
        FriendsOperation._handleError(self, error)


class RemoveFriendOperation(FriendsOperation):

    def __init__(self, friendsManager, sender):
        FriendsOperation.__init__(self, friendsManager, sender)
        self.friendId = None
        self.onlineToons = None
        self.senderFriendsList = None
        self.friendFriendsList = None

    def start(self, friendId):
        self.friendId = friendId
        self.onlineToons = []
        self.friendsManager.air.getActivated(self.sender, self.__gotSenderActivated)

    def __handleActivatedResp(self, avId, activated):
        if activated:
            self.onlineToons.append(avId)

    def __gotSenderActivated(self, avId, activated):
        self.__handleActivatedResp(avId, activated)
        self.friendsManager.air.getActivated(self.friendId, self.__gotFriendActivated)

    def __gotFriendActivated(self, avId, activated):
        self.__handleActivatedResp(avId, activated)
        self.friendsManager.air.dbInterface.queryObject(self.friendsManager.air.dbId, self.sender,
                                                        self.__handleSenderRetrieved)

    def __handleRemoveFriend(self, dclass, fields, friendId):
        if dclass != self.friendsManager.air.dclassesByName['DistributedToonUD']:
            self._handleError('Retrieved sender is not a DistributedToonUD!')
            return False, []

        friendsList = fields['setFriendsList'][0]
        removed = False
        for index, friend in enumerate(friendsList):
            if friend[0] == friendId:
                del friendsList[index]
                removed = True
                break

        if removed:
            return True, friendsList
        else:
            self._handleError('Unable to remove friend!')
            return False, []

    def __handleSenderRetrieved(self, dclass, fields):
        success, senderFriendsList = self.__handleRemoveFriend(dclass, fields, self.friendId)
        if success:
            self.senderFriendsList = senderFriendsList
            self.friendsManager.air.dbInterface.queryObject(self.friendsManager.air.dbId, self.friendId,
                                                            self.__handleFriendRetrieved)

    def __handleFriendRetrieved(self, dclass, fields):
        success, friendFriendsList = self.__handleRemoveFriend(dclass, fields, self.sender)
        if success:
            self.friendFriendsList = friendFriendsList
            self._handleDone()

    def __handleSetFriendsList(self, avId, friendsList):
        if avId in self.onlineToons:
            self.friendsManager.sendUpdateToAvatar(avId, 'setFriendsList', [friendsList])
        else:
            self.friendsManager.air.dbInterface.updateObject(self.friendsManager.air.dbId, avId,
                                                             self.friendsManager.air.dclassesByName[
                                                                 'DistributedToonUD'],
                                                             {'setFriendsList': [friendsList]})

    def _handleDone(self):
        if self.senderFriendsList is not None and self.friendFriendsList is not None:
            self.__handleSetFriendsList(self.sender, self.senderFriendsList)
            self.__handleSetFriendsList(self.friendId, self.friendFriendsList)

        if self.sender in self.onlineToons and self.friendId in self.onlineToons:
            self.friendsManager.undeclareObject(self.sender, self.friendId)
            self.friendsManager.undeclareObject(self.friendId, self.sender)

        if self.friendId in self.onlineToons:
            self.friendsManager.sendUpdateToAvatar(self.friendId, 'friendsNotify', [self.sender, 1])

        FriendsOperation._handleDone(self)


class ComingOnlineOperation(FriendsOperation):

    def __init__(self, friendsManager):
        FriendsOperation.__init__(self, friendsManager, None)
        self.avId = None
        self.friendsList = None
        self.currentFriendIdx = None

    def start(self, avId, friendsList):
        self.avId = avId
        self.friendsList = friendsList
        self.__checkFriendsOnline()

    def __checkFriendsOnline(self):
        self.currentFriendIdx = 0
        for friendId in self.friendsList:
            self.friendsManager.air.getActivated(friendId, self.__gotFriendActivated)

    def __gotFriendActivated(self, avId, activated):
        self.currentFriendIdx += 1
        if activated:
            self.friendsManager.declareObject(avId, self.avId)
            self.friendsManager.declareObject(self.avId, avId)
            self.friendsManager.sendFriendOnline(avId, self.avId, 0, 1)

        if self.currentFriendIdx >= len(self.friendsList):
            self._handleDone()


class GoingOfflineOperation(FriendsOperation):

    def __init__(self, friendsManager):
        FriendsOperation.__init__(self, friendsManager, None)
        self.avId = None
        self.friendsList = None
        self.accId = None
        self.currentFriendIdx = None

    def start(self, avId):
        self.avId = avId
        self.friendsList = []
        self.accId = 0
        self.friendsManager.air.dbInterface.queryObject(self.friendsManager.air.dbId, self.avId, self.__handleAvatarRetrieved)

    def __handleAvatarRetrieved(self, dclass, fields):
        if dclass != self.friendsManager.air.dclassesByName['DistributedToonUD']:
            self._handleError('Retrieved avatar is not a DistributedToonUD!')
            return

        self.friendsList = fields['setFriendsList'][0]
        self.accId = fields['setDISLid'][0]
        self.__checkFriendsOnline()

    def __checkFriendsOnline(self):
        self.currentFriendIdx = 0
        for friendId, _ in self.friendsList:
            self.friendsManager.air.getActivated(friendId, self.__gotFriendActivated)

    def __gotFriendActivated(self, avId, activated):
        self.currentFriendIdx += 1
        if activated:
            self.friendsManager.undeclareObject(avId, self.avId)
            self.friendsManager.undeclareObject(self.accId, avId, isAccount=True)
            self.friendsManager.sendFriendOffline(avId, self.avId)

        if self.currentFriendIdx >= len(self.friendsList):
            self._handleDone()


class ToontownFriendsManagerUD(DistributedObjectGlobalUD):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToontownFriendsManagerUD')

    def __init__(self, air):
        DistributedObjectGlobalUD.__init__(self, air)
        self.operations = []
        self.secrets = []

    def sendMakeFriendsResponse(self, avatarAId, avatarBId, result, context):
        self.sendUpdate('makeFriendsResponse', [avatarAId, avatarBId, result, context])

    def declareObject(self, doId, objId):
        datagram = PyDatagram()
        datagram.addServerHeader(self.GetPuppetConnectionChannel(doId), self.air.ourChannel, CLIENTAGENT_DECLARE_OBJECT)
        datagram.addUint32(objId)
        datagram.addUint16(self.air.dclassesByName['DistributedToonUD'].getNumber())
        self.air.send(datagram)

    def undeclareObject(self, doId, objId, isAccount=False):
        datagram = PyDatagram()
        if isAccount:
            datagram.addServerHeader(self.GetAccountConnectionChannel(doId), self.air.ourChannel,
                                     CLIENTAGENT_UNDECLARE_OBJECT)

        else:
            datagram.addServerHeader(self.GetPuppetConnectionChannel(doId), self.air.ourChannel,
                                     CLIENTAGENT_UNDECLARE_OBJECT)
        datagram.addUint32(objId)
        self.air.send(datagram)

    def sendFriendOnline(self, avId, friendId, commonChatFlags, whitelistChatFlags):
        self.sendUpdateToAvatarId(avId, 'friendOnline', [friendId, commonChatFlags, whitelistChatFlags])

    def sendFriendOffline(self, avId, friendId):
        self.sendUpdateToAvatarId(avId, 'friendOffline', [friendId])

    def sendUpdateToAvatar(self, avId, fieldName, args=[]):
        dclass = self.air.dclassesByName['DistributedToonUD']
        if not dclass:
            return

        field = dclass.getFieldByName(fieldName)
        if not field:
            return

        datagram = field.aiFormatUpdate(avId, avId, self.air.ourChannel, args)
        self.air.send(datagram)

    def runSenderOperation(self, operationType, *args):
        sender = self.air.getAvatarIdFromSender()
        if not sender:
            return

        newOperation = operationType(self, sender)
        self.operations.append(newOperation)
        newOperation.start(*args)

    def runServerOperation(self, operationType, *args):
        newOperation = operationType(self)
        self.operations.append(newOperation)
        newOperation.start(*args)

    def getFriendsListRequest(self):
        self.runSenderOperation(GetFriendsListOperation)

    def getAvatarDetailsRequest(self, avId):
        self.runSenderOperation(GetAvatarDetailsOperation, avId)

    def makeFriends(self, avatarAId, avatarBId, flags, context):
        self.runServerOperation(MakeFriendsOperation, avatarAId, avatarBId, flags, context)

    def removeFriend(self, friendId):
        self.runSenderOperation(RemoveFriendOperation, friendId)

    def comingOnline(self, avId, friendsList):
        self.runServerOperation(ComingOnlineOperation, avId, friendsList)

    def goingOffline(self, avId):
        self.runServerOperation(GoingOfflineOperation, avId)

    def requestSecret(self, requesterId):
        print('requestSecret')
