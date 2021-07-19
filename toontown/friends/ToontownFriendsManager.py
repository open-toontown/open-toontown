from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectGlobal import DistributedObjectGlobal
from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator


class ToontownFriendsManager(DistributedObjectGlobal):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToontownFriendsManager')

    def sendGetFriendsListRequest(self):
        self.sendUpdate('getFriendsListRequest')

    def getFriendsListResponse(self, friendsList):
        datagram = PyDatagram(friendsList)
        di = PyDatagramIterator(datagram)
        self.cr.handleGetFriendsList(di)

    def friendOnline(self, friend):
        datagram = PyDatagram(friend)
        di = PyDatagramIterator(datagram)
        self.cr.handleFriendOnline(di)

    def sendGetAvatarDetailsRequest(self, avId):
        self.sendUpdate('getAvatarDetailsRequest', [avId])

    def getAvatarDetailsResponse(self, avatarDetails):
        datagram = PyDatagram(avatarDetails)
        di = PyDatagramIterator(datagram)
        self.cr.handleGetAvatarDetailsResp(di)
