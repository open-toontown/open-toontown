from direct.distributed import DistributedNodeAI
from direct.fsm import ClassicFSM
from direct.fsm import State
from direct.task import Task
from . import FishingTargetGlobals
import random
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals
import math
from direct.distributed.ClockDelta import *

class DistributedFishingTargetAI(DistributedNodeAI.DistributedNodeAI):

    notify = DirectNotifyGlobal.directNotify.newCategory("DistributedFishingTargetAI")

    def __init__(self, air, pond, hunger):
        DistributedNodeAI.DistributedNodeAI.__init__(self, air)
        self.notify.debug("init")
        self.pond = pond
        self.area = self.pond.getArea()
        self.hunger = hunger
        # For now we are always moving
        self.stateIndex = FishingTargetGlobals.MOVING
        self.centerPoint = FishingTargetGlobals.getTargetCenter(self.area)
        self.maxRadius = FishingTargetGlobals.getTargetRadius(self.area)
        self.currentAngle = 0.0
        self.currentRadius = 0.0
        self.time = 0.0

    def generate(self):
        DistributedNodeAI.DistributedNodeAI.generate(self)
        self.moveToNextPos()

    def delete(self):
        taskMgr.remove(self.taskName('moveFishingTarget'))
        del self.pond
        DistributedNodeAI.DistributedNodeAI.delete(self)

    def getPondDoId(self):
        return self.pond.getDoId()

    def getHunger(self):
        return self.hunger

    def isHungry(self):
        # See if we are hungry at this instant
        return (random.random() <= self.hunger)

    def getCurrentPos(self):
        x = (self.currentRadius * math.cos(self.currentAngle)) + self.centerPoint[0]
        y = (self.currentRadius * math.sin(self.currentAngle)) + self.centerPoint[1]
        z = self.centerPoint[2]
        return (x, y, z)

    def getState(self):
        return [self.stateIndex, self.currentAngle, self.currentRadius, 
                self.time, globalClockDelta.getRealNetworkTime()]

    def d_setState(self, stateIndex, angle, radius, time):
        self.sendUpdate('setState', [stateIndex, angle, radius, time,
                                     globalClockDelta.getRealNetworkTime()])
        
    def moveToNextPos(self, task=None):
        # Send out our current position before moving
        self.d_setPos(*self.getCurrentPos())
        # Now grab a new angle and radius (polar coords)
        self.currentAngle = random.random() * 360.0
        self.currentRadius = random.random() * self.maxRadius
        # Pick a travel duration
        self.time = 6.0 + (6.0 * random.random())
        self.d_setState(self.stateIndex, self.currentAngle, self.currentRadius, self.time)
        waitTime = 1.0 + random.random() * 4.0
        taskMgr.doMethodLater(self.time + waitTime,
                              self.moveToNextPos,
                              self.taskName('moveFishingTarget'))
