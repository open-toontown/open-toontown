from panda3d.core import *
from direct.distributed.ClockDelta import globalClockDelta
from direct.distributed.DistributedObject import DistributedObject
from direct.interval import IntervalGlobal as IG
from toontown.cogdominium import CogdoCraneGameConsts as GameConsts
from toontown.suit.Suit import Suit

class DistCogdoCraneCog(Suit, DistributedObject):

    def __init__(self, cr):
        DistributedObject.__init__(self, cr)
        Suit.__init__(self)
        self._moveIval = None
        return

    def setGameId(self, gameId):
        self._gameId = gameId

    def getGame(self):
        return self.cr.doId2do.get(self._gameId)

    def setSpawnInfo(self, entranceId, timestamp):
        self._startMoveIval(entranceId, globalClockDelta.networkToLocalTime(timestamp))

    def _startMoveIval(self, entranceId, startT):
        self._stopMoveIval()
        unitVecs = (Vec3(1, 0, 0),
         Vec3(0, 1, 0),
         Vec3(-1, 0, 0),
         Vec3(0, -1, 0))
        machineDistance = 4
        entranceDistance = 60
        startPos = unitVecs[entranceId] * entranceDistance
        endPos = unitVecs[entranceId] * machineDistance
        walkDur = (endPos - startPos).length() / GameConsts.CogSettings.CogWalkSpeed.get()
        sceneRoot = self.getGame().getSceneRoot()
        moveIval = IG.Sequence(IG.Func(self.reparentTo, sceneRoot), IG.Func(self.setPos, startPos), IG.Func(self.lookAt, sceneRoot), IG.Func(self.loop, 'walk'), IG.LerpPosInterval(self, walkDur, endPos, startPos=startPos))
        interactIval = IG.Sequence(IG.Func(self.loop, 'neutral'), IG.Wait(GameConsts.CogSettings.CogMachineInteractDuration.get()))
        flyIval = IG.Sequence(IG.Func(self.pose, 'landing', 0), IG.LerpPosInterval(self, GameConsts.CogSettings.CogFlyAwayDuration.get(), self._getFlyAwayDest, blendType='easeIn'))
        self._moveIval = IG.Sequence(moveIval, interactIval, flyIval)
        self._moveIval.start(globalClock.getFrameTime() - startT)

    def _getFlyAwayDest(self):
        return self.getPos() + Vec3(0, 0, GameConsts.CogSettings.CogFlyAwayHeight.get())

    def _stopMoveIval(self):
        if self._moveIval:
            self._moveIval.finish()
            self._moveIval = None
        return

    def disable(self):
        self._stopMoveIval()
        DistributedObject.disable(self)

    def delete(self):
        Suit.delete(self)
        DistributedObject.delete(self)

    def setDNAString(self, dnaString):
        Suit.setDNAString(self, dnaString)
