from direct.distributed.ClockDelta import globalClockDelta
from direct.distributed.DistributedObjectAI import DistributedObjectAI

class DistCogdoCraneCogAI(DistributedObjectAI):

    def __init__(self, air, game, dna, entranceId, spawnTime):
        DistributedObjectAI.__init__(self, air)
        self._gameId = game.doId
        self._dna = dna
        self._entranceId = entranceId
        self._spawnTime = spawnTime

    def getGameId(self):
        return self._gameId

    def getDNAString(self):
        return self._dna.makeNetString()

    def getSpawnInfo(self):
        return (self._entranceId, globalClockDelta.localToNetworkTime(self._spawnTime))
