from toontown.toonbase.ToontownGlobals import *
from . import RegenTreasurePlannerAI, DistributedBRTreasureAI

class BRTreasurePlannerAI(RegenTreasurePlannerAI.RegenTreasurePlannerAI):

    def __init__(self, zoneId):
        self.healAmount = 12
        RegenTreasurePlannerAI.RegenTreasurePlannerAI.__init__(self, zoneId, DistributedBRTreasureAI.DistributedBRTreasureAI, 'BRTreasurePlanner', 20, 2)
        return None

    def initSpawnPoints(self):
        self.spawnPoints = [(-108, 46, 6.2),
         (-111, 74, 6.2),
         (-126, 81, 6.2),
         (-74, -75, 3.0),
         (-136, -51, 3.0),
         (-20, 35, 6.2),
         (-55, 109, 6.2),
         (58, -57, 6.2),
         (-42, -134, 6.2),
         (-68, -148, 6.2),
         (-1, -62, 6.2),
         (25, 2, 6.2),
         (-133, 53, 6.2),
         (-99, 86, 6.2),
         (30, 63, 6.2),
         (-147, 3, 6.2),
         (-135, -102, 6.2),
         (35, -98, 6.2)]
        return self.spawnPoints
