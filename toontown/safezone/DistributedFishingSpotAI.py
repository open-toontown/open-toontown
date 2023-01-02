from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI
from toontown.fishing import FishGlobals

class DistributedFishingSpotAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedFishingSpotAI')

    def __init__(self, air, pond, x, y, z, h, p, r):
        DistributedObjectAI.__init__(self, air)
        self.avId = 0
        self.pondId = pond.doId
        self.posHpr = (x, y, z, h, p, r)
    
    def getPondDoId(self):
        return self.pondId

    def getPosHpr(self):
        return self.posHpr

    def d_setOccupied(self, avId):
        self.avId = avId
        self.sendUpdate('setOccupied', [avId])
    
    def d_setMovie(self, mode, code, itemDesc1, itemDesc2, itemDesc3, power, h):
        self.sendUpdate('setMovie', [mode, code, itemDesc1, itemDesc2, itemDesc3, power, h])

    def requestEnter(self):
        avId = self.air.getAvatarIdFromSender()
        self.d_setOccupied(avId)
        self.d_setMovie(FishGlobals.EnterMovie, 0, 0, 0, 0, 0, 0)
    
    def requestExit(self):
        if self.avId == self.air.getAvatarIdFromSender():
            taskMgr.doMethodLater(1.0, self.completeExit, 'completeExit')
    
    def completeExit(self, task):
        self.d_setOccupied(0)
        self.d_setMovie(FishGlobals.ExitMovie, 0, 0, 0, 0, 0, 0,)
