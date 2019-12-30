import math
from direct.directnotify import DirectNotifyGlobal
from toontown.minigame.DropScheduler import ThreePhaseDropScheduler
from toontown.parties import PartyGlobals
from functools import reduce

class DistributedPartyCatchActivityBase:
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedPartyCatchActivityBase')
    FallRateCap_Players = 20

    def calcDifficultyConstants(self, numPlayers):
        self.FirstDropDelay = 0.0
        self.NormalDropDelay = int(1.0 / 12 * PartyGlobals.CatchActivityDuration)
        self.FasterDropDelay = int(9.0 / 12 * PartyGlobals.CatchActivityDuration)
        DistributedPartyCatchActivityBase.notify.debug('will start dropping fast after %s seconds' % self.FasterDropDelay)
        self.SlowerDropPeriodMult = 1.5
        self.FasterDropPeriodMult = 1.0 / 3
        self.ToonSpeed = 16.0

        def scaledDimensions(widthHeight, scale):
            w, h = widthHeight
            return [math.sqrt(scale * w * w), math.sqrt(scale * h * h)]

        BaseStageDimensions = [36, 36]
        self.StageAreaScale = 1.0
        self.StageLinearScale = math.sqrt(self.StageAreaScale)
        DistributedPartyCatchActivityBase.notify.debug('StageLinearScale: %s' % self.StageLinearScale)
        self.StageDimensions = scaledDimensions(BaseStageDimensions, self.StageAreaScale)
        DistributedPartyCatchActivityBase.notify.debug('StageDimensions: %s' % self.StageDimensions)
        self.StageHalfWidth = self.StageDimensions[0] / 2.0
        self.StageHalfHeight = self.StageDimensions[1] / 2.0
        self.MinOffscreenHeight = 30
        distance = math.sqrt(self.StageDimensions[0] * self.StageDimensions[0] + self.StageDimensions[1] * self.StageDimensions[1])
        distance /= self.StageLinearScale
        ToonRunDuration = distance / self.ToonSpeed
        offScreenOnScreenRatio = 1.0
        fraction = 1.0 / 3 * 0.85
        self.BaselineOnscreenDropDuration = ToonRunDuration / (fraction * (1.0 + offScreenOnScreenRatio))
        DistributedPartyCatchActivityBase.notify.debug('BaselineOnscreenDropDuration=%s' % self.BaselineOnscreenDropDuration)
        self.OffscreenTime = offScreenOnScreenRatio * self.BaselineOnscreenDropDuration
        DistributedPartyCatchActivityBase.notify.debug('OffscreenTime=%s' % self.OffscreenTime)
        self.BaselineDropDuration = self.BaselineOnscreenDropDuration + self.OffscreenTime
        self.MaxDropDuration = self.BaselineDropDuration
        self.DropPeriod = self.BaselineDropDuration / 3.0
        scaledNumPlayers = (min(numPlayers, self.FallRateCap_Players) - 1.0) * 0.85 + 1.0
        self.DropPeriod /= scaledNumPlayers
        typeProbs = {'fruit': 3,
         'anvil': 1}
        probSum = reduce(lambda x, y: x + y, list(typeProbs.values()))
        for key in list(typeProbs.keys()):
            typeProbs[key] = float(typeProbs[key]) / probSum

        scheduler = ThreePhaseDropScheduler(PartyGlobals.CatchActivityDuration, self.FirstDropDelay, self.DropPeriod, self.MaxDropDuration, self.SlowerDropPeriodMult, self.NormalDropDelay, self.FasterDropDelay, self.FasterDropPeriodMult)
        self.totalDrops = 0
        while not scheduler.doneDropping(continuous=True):
            scheduler.stepT()
            self.totalDrops += 1

        self.numFruits = int(self.totalDrops * typeProbs['fruit'])
        self.numAnvils = int(self.totalDrops - self.numFruits)
        self.generationDuration = scheduler.getDuration()
