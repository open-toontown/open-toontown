from toontown.toonbase.ToontownGlobals import *
from . import RegenTreasurePlannerAI
from . import DistributedEFlyingTreasureAI

class EFlyingTreasurePlannerAI(RegenTreasurePlannerAI.RegenTreasurePlannerAI):
    def __init__(self, estateAI, zoneId):
        self.healAmount = 3
        RegenTreasurePlannerAI.RegenTreasurePlannerAI.__init__(
            self,
            zoneId,
            DistributedEFlyingTreasureAI.DistributedEFlyingTreasureAI, # Constructor
            "EFlyingTreasurePlanner",
            20, # Frequency of spawn
            7   # Max number of treasures
            )
        # keep reference to estateAI, so we can tell the estate
        # when the treasures are updated (needed for cannon fire intersection calc)
        self.estateAI = estateAI
        
    def initSpawnPoints(self):
        self.spawnPoints = [
            (-14, -47.06, 25.177),
            (-24, -43.17, 30.755),
            (121, 9.9, 24.025),
            (2.644, 64.941, 29.672),
            (-0.3, -22.5, 32.025),
            (47.34, 9.3, 35.025),
            (26.6, -2.49, 27.485),
            (55.9, -13.1, 33.156),
            (-57.9, 13.38, 28.386),
            (-85.1, 48.9, 30.025),
            (-2.702, -96.892, 28.765),
            (65, 2.7, 30.025),
            (-4.4, 42.945, 29.284),
            (-8.495, -62.438, 31.88),
            (-74.27, -83.832, 28.05),
            (-80.99, 5.753, 28.05),
            (80.906, 53.857, 28.05),
            (97.955, 0.618, 29.05),
            (47.26, -62.193, 30.05),
            (-63.865, 24.788, 30.025),
            (-28.826, 25.024, 28.559),
            ]
        return self.spawnPoints
            
    def placeRandomTreasure(self):
        RegenTreasurePlannerAI.RegenTreasurePlannerAI.placeRandomTreasure(self)

        # Update the estate's list of treasures
        self.estateAI.updateFlyingTreasureList()
                                                     
                       
