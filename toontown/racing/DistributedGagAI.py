from direct.distributed import DistributedObjectAI
from direct.distributed.ClockDelta import *
from pandac.PandaModules import *

class DistributedGagAI(DistributedObjectAI.DistributedObjectAI):
    def __init__(self, air, ownerId, race, activateTime, x, y, z, type):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        self.activateTime=activateTime
        self.initTime=globalClockDelta.getFrameNetworkTime(16, 100)
        self.pos=(x, y, z)
        self.race=race
        self.ownerId=ownerId
        self.type = type
    def generate(self):
        DistributedObjectAI.DistributedObjectAI.generate(self)
        #This is a good time to grab the starting time


    def announceGenerate(self):
        DistributedObjectAI.DistributedObjectAI.announceGenerate(self)
        print("I'm Here!!!!")

    def delete(self):
        DistributedObjectAI.DistributedObjectAI.delete(self)

    def getRace(self):
        return self.race.doId

    def getPos(self):
        return self.pos

    def setPos(self, x, y, z):
        self.pos=(x, y, z)

    def getType(self):
        return self.type

    def setType(self, type):
        self.type = type

    def getInitTime(self):
        return self.initTime

    def getActivateTime(self):
        return self.activateTime

    def getOwnerId(self):
        return self.ownerId

    def hitSomebody(self, avId, timeStamp):
        if self.type == 0:
            taskMgr.doMethodLater(4, self.requestDelete, "deleting: "+self.uniqueName("banana"), extraArgs=[])
        elif self.type == 1:
            taskMgr.doMethodLater(4, self.requestDelete, "deleting: "+self.uniqueName("pie"), extraArgs=[])

