from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectGlobal import DistributedObjectGlobal


class ToontownFriendsManager(DistributedObjectGlobal):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToontownFriendsManager')

    def sendGetFriendsListRequest(self):
        self.sendUpdate('getFriendsListRequest')

    def getFriendsListResponse(self, friendsList):
        self.cr.handleGetFriendsList(friendsList)

    def friendOnline(self, doId, commonChatFlags, whitelistChatFlags):
        self.cr.handleFriendOnline(doId, commonChatFlags, whitelistChatFlags)
