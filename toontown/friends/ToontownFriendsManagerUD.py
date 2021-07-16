from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectGlobalUD import DistributedObjectGlobalUD


class ToontownFriendsManagerUD(DistributedObjectGlobalUD):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToontownFriendsManagerUD')

    def getFriendsListRequest(self):
        self.notify.info('getFriendsListRequest TODO')
