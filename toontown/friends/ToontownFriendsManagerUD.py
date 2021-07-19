from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectGlobalUD import DistributedObjectGlobalUD
from direct.distributed.PyDatagram import *


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
            datagram = PyDatagram()
            datagram.addUint32(friendId)  # doId
            datagram.addUint8(0)  # commonChatFlags
            datagram.addUint8(1)  # whitelistChatFlags
            self.friendsManager.sendUpdateToAvatarId(self.sender, 'friendOnline', [datagram.getMessage()])

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
        datagram.addUint32(self.fields['avId'])
        datagram.addUint8(0 if success else 1)
        if success:
            avatarDetails = self.__packAvatarDetails(self.dclass, self.fields)
            datagram.appendData(avatarDetails)

        self.friendsManager.sendUpdateToAvatarId(self.sender, 'getAvatarDetailsResponse', [datagram.getMessage()])

    def _handleDone(self):
        self.__sendAvatarDetails(True)
        FriendsOperation._handleDone(self)

    def _handleError(self, error):
        self.__sendAvatarDetails(False)
        FriendsOperation._handleError(self, error)


class ToontownFriendsManagerUD(DistributedObjectGlobalUD):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToontownFriendsManagerUD')

    def __init__(self, air):
        DistributedObjectGlobalUD.__init__(self, air)
        self.operations = []

    def runOperation(self, operationType, *args):
        sender = self.air.getAvatarIdFromSender()
        if not sender:
            return

        newOperation = operationType(self, sender)
        self.operations.append(newOperation)
        newOperation.start(*args)

    def getFriendsListRequest(self):
        self.runOperation(GetFriendsListOperation)

    def getAvatarDetailsRequest(self, avId):
        self.runOperation(GetAvatarDetailsOperation, avId)
