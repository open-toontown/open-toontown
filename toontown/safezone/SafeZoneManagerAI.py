from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI

HealFrequency = 30.0


class SafeZoneManagerAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('SafeZoneManagerAI')

    def enterSafeZone(self):
        avId = self.air.getAvatarIdFromSender()
        if not avId:
            return

        av = self.air.doId2do.get(avId)
        if not av:
            return

        if not av.isToonedUp():
            av.startToonUp(HealFrequency)

    def exitSafeZone(self):
        avId = self.air.getAvatarIdFromSender()
        if not avId:
            return

        av = self.air.doId2do.get(avId)
        if not av:
            return

        av.stopToonUp()
