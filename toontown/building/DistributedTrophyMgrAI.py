from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI


class DistributedTrophyMgrAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedTrophyMgrAI')

    def __init__(self, air):
        DistributedObjectAI.__init__(self, air)
        self.leaderInfo = ([], [], [])

    def requestTrophyScore(self):
        pass

    def getLeaderInfo(self):
        return self.leaderInfo

    def addTrophy(self, avId, name, numFloors):
        pass

    def removeTrophy(self, avId, numFloors):
        pass  # TODO
