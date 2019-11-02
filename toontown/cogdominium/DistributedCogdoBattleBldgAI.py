from direct.directnotify import DirectNotifyGlobal
from toontown.battle import DistributedBattleBldgAI

class DistributedCogdoBattleBldgAI(DistributedBattleBldgAI.DistributedBattleBldgAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedCogdoBattleBldgAI')

    def __init__(self, air, zoneId, roundCallback = None, finishCallback = None, maxSuits = 4, bossBattle = 0):
        DistributedBattleBldgAI.DistributedBattleBldgAI.__init__(self, air, zoneId, roundCallback, finishCallback, maxSuits, bossBattle)
