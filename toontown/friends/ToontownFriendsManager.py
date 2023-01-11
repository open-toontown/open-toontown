from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectGlobal import DistributedObjectGlobal
from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator


class ToontownFriendsManager(DistributedObjectGlobal):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToontownFriendsManager')

    def sendGetFriendsListRequest(self):
        self.sendUpdate('getFriendsListRequest')

    def getFriendsListResponse(self, success, friendsList):
        if not success:
            self.notify.warning('An error has occurred when retrieving friends list.')
            self.cr.friendsListError = 1

        self.cr.setFriendsMap(friendsList)

    def friendOnline(self, friendId, commonChatFlags, whitelistChatFlags):
        self.cr.setFriendOnline(friendId, commonChatFlags, whitelistChatFlags)

    def friendOffline(self, friendId):
        self.cr.setFriendOffline(friendId)

    def sendGetAvatarDetailsRequest(self, avId):
        self.sendUpdate('getAvatarDetailsRequest', [avId])

    def getAvatarDetailsResponse(self, avatarDetails):
        datagram = PyDatagram(avatarDetails)
        di = PyDatagramIterator(datagram)
        self.cr.handleGetAvatarDetailsResp(di)

    def sendRemoveFriend(self, friendId):
        self.sendUpdate('removeFriend', [friendId])
