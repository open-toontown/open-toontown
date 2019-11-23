from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI

class DistributedTrophyMgrAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedTrophyMgrAI')

    def requestTrophyScore(self):
        pass

    def getLeaderInfo(self):
        return [], [], []

    def addTrophy(self, *args, **kwargs):
        pass
