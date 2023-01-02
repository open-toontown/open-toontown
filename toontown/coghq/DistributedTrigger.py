from panda3d.core import *
from panda3d.core import *
from direct.interval.IntervalGlobal import *
from direct.distributed.ClockDelta import *
from . import MovingPlatform
from toontown.toonbase import ToontownGlobals
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM
from . import DistributedSwitch
from toontown.toonbase import TTLocalizer

class DistributedTrigger(DistributedSwitch.DistributedSwitch):

    def setupSwitch(self):
        radius = 1.0
        cSphere = CollisionSphere(0.0, 0.0, 0.0, radius)
        cSphere.setTangible(0)
        cSphereNode = CollisionNode(self.getName())
        cSphereNode.addSolid(cSphere)
        self.cSphereNodePath = self.attachNewNode(cSphereNode)
        cSphereNode.setCollideMask(ToontownGlobals.WallBitmask)
        self.flattenMedium()

    def delete(self):
        self.cSphereNodePath.removeNode()
        del self.cSphereNodePath
        DistributedSwitch.DistributedSwitch.delete(self)

    def enterTrigger(self, args = None):
        DistributedSwitch.DistributedSwitch.enterTrigger(self, args)
        self.setIsOn(1)

    def exitTrigger(self, args = None):
        DistributedSwitch.DistributedSwitch.exitTrigger(self, args)
        self.setIsOn(0)

    def getName(self):
        if self.triggerName != '':
            return self.triggerName
        else:
            return DistributedSwitch.DistributedSwitch.getName(self)
