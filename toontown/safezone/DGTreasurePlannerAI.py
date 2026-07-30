from toontown.toonbase.ToontownGlobals import *
from . import RegenTreasurePlannerAI, DistributedDGTreasureAI

class DGTreasurePlannerAI(RegenTreasurePlannerAI.RegenTreasurePlannerAI):

    def __init__(self, zoneId):
        self.healAmount = 10
        RegenTreasurePlannerAI.RegenTreasurePlannerAI.__init__(self, zoneId, DistributedDGTreasureAI.DistributedDGTreasureAI, 'DGTreasurePlanner', 15, 2)
        return None

    def initSpawnPoints(self):
        self.spawnPoints = [(-49, 156, 0.0),
         (-59, 50, 0.0),
         (19, 16, 0.0),
         (76, 38, 1.1),
         (102, 121, 0.0),
         (69, 123, 0.0),
         (49, 105, 0.0),
         (24, 156, 0.0),
         (-27, 127, 0.0),
         (-56, 105, 0.0),
         (-40, 113, 0.0),
         (25, 114, 0.0),
         (-6, 84, 0.0),
         (19, 96, 0.0),
         (0, 114, 0.0),
         (-78, 157, 10.0),
         (-33.4, 218.2, 10.0),
         (57, 205, 10.0),
         (32, 77, 0.0),
         (-102, 101, 0.0)]
        return self.spawnPoints
