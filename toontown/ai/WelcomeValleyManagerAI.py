from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI

from toontown.hood import ZoneUtil
from toontown.hood.GSHoodDataAI import GSHoodDataAI
from toontown.hood.TTHoodDataAI import TTHoodDataAI
from toontown.toonbase import ToontownGlobals


class WelcomeValleyManagerAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('WelcomeValleyManagerAI')

    def requestZoneIdMessage(self, zoneId, context):
        avId = self.air.getAvatarIdFromSender()
        if zoneId == 0:
            zoneId = ToontownGlobals.WelcomeValleyBegin

        self.toonSetZone(avId, zoneId)
        self.sendUpdateToAvatarId(avId, 'requestZoneIdResponse', [zoneId, context])

    def toonSetZone(self, doId, zoneId):
        event = self.staticGetLogicalZoneChangeEvent(doId)
        inWelcomeValley = self.isAccepting(event)
        if not ZoneUtil.isDynamicZone(zoneId):
            if ZoneUtil.isWelcomeValley(zoneId) and not inWelcomeValley:
                self.air.districtStats.b_setNewAvatarCount(self.air.districtStats.getNewAvatarCount() + 1)
                self.accept(event, lambda newZoneId, _: self.toonSetZone(doId, newZoneId))
                self.accept(self.air.getAvatarExitEvent(doId), self.toonSetZone,
                            extraArgs=[doId, ToontownGlobals.ToontownCentral])
            elif (not ZoneUtil.isWelcomeValley(zoneId)) and inWelcomeValley:
                self.air.districtStats.b_setNewAvatarCount(self.air.districtStats.getNewAvatarCount() - 1)
                self.ignore(event)
                self.ignore(self.air.getAvatarExitEvent(doId))

    def createWelcomeValleyZones(self):
        self.notify.info('Creating Welcome Valley zones...')

        # Toontown Central
        self.air.generateHood(TTHoodDataAI, 22000)

        # Goofy Speedway
        self.air.generateHood(GSHoodDataAI, 23000)
