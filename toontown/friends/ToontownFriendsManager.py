from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectGlobal import DistributedObjectGlobal
from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator


class ToontownFriendsManager(DistributedObjectGlobal):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToontownFriendsManager')

    def sendGetFriendsListRequest(self):
        self.sendUpdate('getFriendsListRequest')

    def getFriendsListResponse(self, friendsList):
        self.cr.handleGetFriendsList(friendsList)

    def friendOnline(self, doId, commonChatFlags, whitelistChatFlags):
        self.cr.handleFriendOnline(doId, commonChatFlags, whitelistChatFlags)

    def sendGetAvatarDetailsRequest(self, avId):
        self.sendUpdate('getAvatarDetailsRequest', [avId])

    def getAvatarDetailsResponse(self, avatarDetails):
        datagram = PyDatagram(avatarDetails)
        di = PyDatagramIterator(datagram)
        self.cr.handleGetAvatarDetailsResp(di)
