from toontown.toonbase.ToontownGlobals import *
from . import RegenTreasurePlannerAI
from . import DistributedETreasureAI

class ETreasurePlannerAI(RegenTreasurePlannerAI.RegenTreasurePlannerAI):
    def __init__(self, zoneId):
        self.healAmount = 2
        RegenTreasurePlannerAI.RegenTreasurePlannerAI.__init__(
            self,
            zoneId,
            DistributedETreasureAI.DistributedETreasureAI, # Constructor
            "ETreasurePlanner",
            50, # Frequency of spawn
            3   # Max number of treasures
            )

    def initSpawnPoints(self):
        self.spawnPoints = [
            (-125, -20.06, 1.177),
            (-24, -43.17, 5.755),
            (121, 9.9, 0.025),
            (2.644, 64.941, 4.672),
            (-0.3, -22.5, 7.025),
            (47.34, 9.3, 8.025),
            (26.6, -2.49, 11.485),
            (55.9, -13.1, 8.156),
            (-57.9, 13.38, 2.386),
            (-85.1, 48.9, 0.025),
            (-2.702, -96.892, 3.765),
            # (53, -133.7, 0.025), # Too close to fishing dock
            (0.409, -102.945, -1.284),
            (-8.495, -62.438, 1.88),
            (-74.27, -83.832, 0.05),
            (-80.99, 5.753, 0.05),
            (80.906, 53.857, 0.05),
            (97.955, 0.618, 0.05),
            (47.26, -62.193, 0.05),
            (-71.865, -132.788, 0.025),
            (-28.826, 25.024, 2.559),
            ]
        return self.spawnPoints
            
            
                                                     
