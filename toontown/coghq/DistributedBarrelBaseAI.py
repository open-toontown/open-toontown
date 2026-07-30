from direct.directnotify import DirectNotifyGlobal
from otp.level import DistributedEntityAI
from direct.task import Task
from toontown.coghq import BarrelBase

class DistributedBarrelBaseAI(DistributedEntityAI.DistributedEntityAI, BarrelBase.BarrelBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedBarrelBaseAI')

    def __init__(self, level, entId):
        self.rewardPerGrabMax = 0
        DistributedEntityAI.DistributedEntityAI.__init__(self, level, entId)
        self.usedAvIds = []

    def delete(self):
        taskMgr.remove(self.taskName('resetGags'))
        del self.usedAvIds
        del self.pos
        DistributedEntityAI.DistributedEntityAI.delete(self)

    def requestGrab(self):
        avId = self.air.getAvatarIdFromSender()
        self.notify.debug('requestGrab %s' % avId)
        if avId not in self.usedAvIds:
            self.usedAvIds.append(avId)
            self.d_setGrab(avId)
        else:
            self.sendUpdate('setReject')

    def d_setGrab(self, avId):
        self.sendUpdate('setGrab', [avId])
