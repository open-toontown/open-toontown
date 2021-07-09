from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectGlobalAI import DistributedObjectGlobalAI


class FriendManagerAI(DistributedObjectGlobalAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('FriendManagerAI')

    def friendQuery(self, inviteeId):
        self.notify.info('Hello world: %s' % inviteeId)
