from toontown.toonbase.ToontownGlobals import *
from . import RegenTreasurePlannerAI, DistributedDDTreasureAI

class DDTreasurePlannerAI(RegenTreasurePlannerAI.RegenTreasurePlannerAI):

    def __init__(self, zoneId):
        self.healAmount = 10
        RegenTreasurePlannerAI.RegenTreasurePlannerAI.__init__(self, zoneId, DistributedDDTreasureAI.DistributedDDTreasureAI, 'DDTreasurePlanner', 20, 2)
        return None

    def initSpawnPoints(self):
        self.spawnPoints = [(52.9072, -23.4768, -12.308),
         (35.3827, -51.9196, -12.308),
         (17.4252, -57.3107, -12.308),
         (-0.716054, -68.5, -12.308),
         (-29.0169, -66.8887, -12.308),
         (-63.492, -64.2191, -12.308),
         (-72.2423, -58.3686, -12.308),
         (-97.9602, -42.8905, -12.308),
         (-102.215, -34.1519, -12.308),
         (-102.978, -4.09065, -12.308),
         (-101.305, 30.6454, -12.308),
         (-45.0621, -21.0088, -12.308),
         (-11.4043, -29.0816, -12.308),
         (2.33548, -7.71722, -12.308),
         (-8.643, 33.9891, -12.308),
         (-53.224, 18.1293, -12.308),
         (-99.7225, -8.1298, -12.308),
         (-100.457, 28.351, -12.308),
         (-76.7946, 4.21199, -12.308),
         (-64.9137, 37.5765, -12.308),
         (-17.6075, 102.135, -12.308),
         (-23.4112, 127.777, -12.308),
         (-11.3513, 128.991, -12.308),
         (-14.1068, 83.2043, -12.308),
         (53.2685, 24.3585, -12.308),
         (41.4197, 4.35384, -12.308)]
        return self.spawnPoints
