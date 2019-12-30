from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase.ToontownGlobals import *
from toontown.safezone import RegenTreasurePlannerAI
from . import DistributedTagTreasureAI

class TagTreasurePlannerAI(RegenTreasurePlannerAI.RegenTreasurePlannerAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('TagTreasurePlannerAI')

    def __init__(self, zoneId, callback):
        self.numPlayers = 0
        RegenTreasurePlannerAI.RegenTreasurePlannerAI.__init__(self, zoneId, DistributedTagTreasureAI.DistributedTagTreasureAI, 'TagTreasurePlanner-' + str(zoneId), 3, 4, callback)
        return None

    def initSpawnPoints(self):
        self.spawnPoints = [(0, 0, 0.1),
         (5, 20, 0.1),
         (0, 40, 0.1),
         (-5, -20, 0.1),
         (0, -40, 0.1),
         (20, 0, 0.1),
         (40, 5, 0.1),
         (-20, -5, 0.1),
         (-40, 0, 0.1),
         (22, 20, 0.1),
         (-20, 22, 0.1),
         (20, -20, 0.1),
         (-25, -20, 0.1),
         (20, 40, 0.1),
         (20, -44, 0.1),
         (-24, 40, 0.1),
         (-20, -40, 0.1)]
        return self.spawnPoints
