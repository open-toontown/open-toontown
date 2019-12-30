from toontown.toonbase.ToontownGlobals import *
from . import RegenTreasurePlannerAI, DistributedDLTreasureAI

class DLTreasurePlannerAI(RegenTreasurePlannerAI.RegenTreasurePlannerAI):

    def __init__(self, zoneId):
        self.healAmount = 12
        RegenTreasurePlannerAI.RegenTreasurePlannerAI.__init__(self, zoneId, DistributedDLTreasureAI.DistributedDLTreasureAI, 'DLTreasurePlanner', 20, 2)
        return None

    def initSpawnPoints(self):
        self.spawnPoints = [(86, 69, -17.4),
         (34, -48, -16.4),
         (87, -70, -17.5),
         (-98, 99, 0.0),
         (51, 100, 0.0),
         (-45, -12, -15.0),
         (9, 8, -15.0),
         (-24, 64, -17.2),
         (-100, -99, 0.0),
         (21, -101, 0.0),
         (88, -17, -15.0),
         (32, 70, -17.4),
         (53, 35, -15.8),
         (2, -30, -15.5),
         (-40, -56, -16.8),
         (-28, 18, -15.0),
         (-34, -88, 0.0)]
        return self.spawnPoints
