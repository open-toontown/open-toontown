from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectGlobalUD import DistributedObjectGlobalUD


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


class FriendsListOperation(FriendsOperation):

    def start(self):
        self.friendsManager.air.dbInterface.queryObject(self.friendsManager.air.dbId, self.sender,
                                                        self.__handleSenderRetrieved)

    def __handleSenderRetrieved(self, dclass, fields):
        if dclass != self.friendsManager.air.dclassesByName['DistributedToonUD']:
            self._handleError('Retrieved sender is not a DistributedToonUD!')
            return

        self.tempFriendsList = fields['setFriendsList'][0]
        if len(self.tempFriendsList) <= 0:
            self.__sendFriendsList([])
            self._handleDone()
            return

        self.currentFriendIdx = 0
        self.friendsList = []
        self.friendsManager.air.dbInterface.queryObject(self.friendsManager.air.dbId, self.tempFriendsList[0][0],
                                                        self.__handleFriendRetrieved)

    def __handleFriendRetrieved(self, dclass, fields):
        if dclass != self.friendsManager.air.dclassesByName['DistributedToonUD']:
            self._handleError('Retrieved friend is not a DistributedToonUD!')
            return

        friendId = self.tempFriendsList[self.currentFriendIdx][0]
        self.friendsList.append([friendId, fields['setName'][0], fields['setDNAString'][0], fields['setPetId'][0]])
        if len(self.friendsList) >= len(self.tempFriendsList):
            self.__sendFriendsList(self.friendsList)
            self._handleDone()
            return

        self.currentFriendIdx += 1
        self.friendsManager.air.dbInterface.queryObject(self.friendsManager.air.dbId,
                                                        self.tempFriendsList[self.currentFriendIdx][0],
                                                        self.__handleFriendRetrieved)

    def __sendFriendsList(self, friendsList):
        self.friendsManager.notify.info('TODO: __sendFriendsList')


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
        self.runOperation(FriendsListOperation)
