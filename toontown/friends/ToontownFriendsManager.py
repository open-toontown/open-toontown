from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectGlobal import DistributedObjectGlobal


class ToontownFriendsManager(DistributedObjectGlobal):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToontownFriendsManager')

    def sendGetFriendsListRequest(self):
        self.sendUpdate('getFriendsListRequest')
