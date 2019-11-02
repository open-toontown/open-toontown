from direct.distributed import DistributedObjectAI
from direct.fsm import FSM

class DistributedGolfSpotAI(DistributedObjectAI.DistributedObjectAI, FSM.FSM):

    def __init__(self, air, boss, index):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        FSM.FSM.__init__(self, 'DistributedGolfSpotAI')
        self.boss = boss
        self.index = index
        self.avId = 0
        self.allowControl = True

    def delete(self):
        DistributedObjectAI.DistributedObjectAI.delete(self)

    def getBossCogId(self):
        return self.boss.doId

    def getIndex(self):
        return self.index

    def d_setState(self, state, avId, extraInfo=0):
        self.sendUpdate('setState', [state, avId, extraInfo])

    def requestControl(self):
        if not self.allowControl:
            return
        avId = self.air.getAvatarIdFromSender()
        if avId in self.boss.involvedToons and self.avId == 0 and self.state != 'Off':
            golfSpotId = self.__getGolfSpotId(avId)
            if golfSpotId == 0:
                grantRequest = True
                if self.boss and not self.boss.isToonRoaming(avId):
                    grantRequest = False
                if grantRequest:
                    self.request('Controlled', avId)

    def requestFree(self, gotHitByBoss):
        avId = self.air.getAvatarIdFromSender()
        if avId == self.avId and self.state == 'Controlled':
            self.request('Free', gotHitByBoss)

    def forceFree(self):
        self.request('Free', 0)

    def removeToon(self, avId):
        if avId == self.avId:
            self.request('Free')

    def __getGolfSpotId(self, avId):
        if self.boss and self.boss.golfSpots != None:
            for golfSpot in self.boss.golfSpots:
                if golfSpot.avId == avId:
                    return golfSpot.doId

        return 0

    def turnOff(self):
        self.request('Off')
        self.allowControl = False

    def enterOff(self):
        self.sendUpdate('setGoingToReward', [])
        self.d_setState('O', 0)

    def exitOff(self):
        pass

    def enterControlled(self, avId):
        self.avId = avId
        self.d_setState('C', avId)

    def exitControlled(self):
        pass

    def enterFree(self, gotHitByBoss):
        self.avId = 0
        self.d_setState('F', 0, gotHitByBoss)

    def exitFree(self):
        pass
