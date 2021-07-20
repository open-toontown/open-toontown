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
        datagram = PyDatagram()
        datagram.addUint8(0 if success else 1)  # error
        if success:
            count = len(self.friendsList)
            datagram.addUint16(count)  # count
            for i in range(count):
                datagram.addUint32(self.friendsList[i][0])  # doId
                datagram.addString(self.friendsList[i][1])  # name
                datagram.addBlob(self.friendsList[i][2])  # dnaString
                datagram.addUint32(self.friendsList[i][3])  # petId

        self.friendsManager.sendUpdateToAvatarId(self.sender, 'getFriendsListResponse', [datagram.getMessage()])
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
        self.friendsManager.air.dbInterface.queryObject(self.friendsManager.air.dbId, self.avatarAId,
                                                        self.__handleAvatarARetrieved)

    def __handleMakeFriends(self, dclass, fields, avId, friendId):
        if dclass != self.friendsManager.air.dclassesByName['DistributedToonUD']:
            self._handleError('Retrieved avatar is not a DistributedToonUD!')
            return

        friendsList = fields['setFriendsList'][0]
        if len(friendsList) >= OTPGlobals.MaxFriends:
            self._handleError('Avatar\'s friends list is full!')
            return

        newFriend = (friendId, self.flags)
        if newFriend in friendsList:
            self._handleError('Already friends!')
            return

        friendsList.append(newFriend)
        self.friendsManager.air.dbInterface.updateObject(self.friendsManager.air.dbId, avId,
                                                         self.friendsManager.air.dclassesByName['DistributedToonUD'],
                                                         {'setFriendsList': [friendsList]})
        if avId in self.onlineToons:
            self.friendsManager.sendUpdateToAvatar(avId, 'setFriendsList', [friendsList])
            if friendId in self.onlineToons:
                self.friendsManager.sendFriendOnline(avId, friendId, 0, 1)

    def __handleAvatarARetrieved(self, dclass, fields):
        self.__handleMakeFriends(dclass, fields, self.avatarAId, self.avatarBId)
        self.friendsManager.air.getActivated(self.avatarBId, self.__gotActivatedAvatarB)

    def __gotActivatedAvatarB(self, avId, activated):
        self.__handleActivatedResp(avId, activated)
        self.friendsManager.air.dbInterface.queryObject(self.friendsManager.air.dbId, self.avatarBId,
                                                        self.__handleAvatarBRetrieved)

    def __handleAvatarBRetrieved(self, dclass, fields):
        self.__handleMakeFriends(dclass, fields, self.avatarBId, self.avatarAId)
        self._handleDone()

    def _handleDone(self):
        self.resultCode = 1
        FriendsOperation._handleDone(self)

    def _handleError(self, error):
        self.resultCode = 0
        FriendsOperation._handleError(self, error)


class ToontownFriendsManagerUD(DistributedObjectGlobalUD):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToontownFriendsManagerUD')

    def __init__(self, air):
        DistributedObjectGlobalUD.__init__(self, air)
        self.operations = []

    def sendFriendOnline(self, avId, friendId, commonChatFlags, whitelistChatFlags):
        datagram = PyDatagram()
        datagram.addUint32(friendId)  # doId
        datagram.addUint8(commonChatFlags)  # commonChatFlags
        datagram.addUint8(whitelistChatFlags)  # whitelistChatFlags
        self.sendUpdateToAvatarId(avId, 'friendOnline', [datagram.getMessage()])

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
