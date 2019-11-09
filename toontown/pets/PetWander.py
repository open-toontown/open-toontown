from pandac.PandaModules import *
from libtoontown import *
from direct.showbase.PythonUtil import reduceAngle, randFloat, normalDistrib
from direct.showbase import DirectObject
from toontown.pets import PetChase
from toontown.pets import PetConstants

class PetWander(CPetChase, DirectObject.DirectObject):

    def __init__(self, minDist = 5.0, moveAngle = 20.0):
        self.movingTarget = hidden.attachNewNode('petWanderTarget')
        CPetChase.__init__(self, self.movingTarget, minDist, moveAngle)
        self.targetMoveCountdown = 0
        self.collEvent = None
        self.gotCollision = False
        return

    def isCpp(self):
        return 0

    def __ignoreCollisions(self):
        if self.collEvent is not None:
            self.ignore(self.collEvent)
            self.collEvent = None
        return

    def _setMover(self, mover):
        CPetChase.setMover(self, mover)
        self.mover = mover
        self.__ignoreCollisions()
        self.collEvent = mover.getCollisionEventName()
        self.accept(self.collEvent, self._handleCollision)

    def _clearMover(self, mover):
        CPetChase.clearMover(self, mover)
        self.__ignoreCollisions()

    def _handleCollision(self, collEntry):
        self.gotCollision = True
        self.movingTarget.setPos(self.getNodePath().getPos())
        self.targetMoveCountdown *= 0.5

    def destroy(self):
        self.__ignoreCollisions()
        self.movingTarget.removeNode()
        del self.movingTarget

    def _process(self, dt):
        self.targetMoveCountdown -= dt
        if self.targetMoveCountdown <= 0.0:
            distance = normalDistrib(3.0, 30.0)
            heading = normalDistrib(-(90 + 45), 90 + 45)
            if self.gotCollision:
                self.gotCollision = False
                heading = heading + 180
            target = self.getTarget()
            target.setPos(self.getNodePath().getPos())
            target.setH(target, heading)
            target.setY(target, distance)
            duration = distance / self.mover.getFwdSpeed()
            self.targetMoveCountdown = duration * randFloat(1.2, 3.0)
        CPetChase.process(self, dt)
