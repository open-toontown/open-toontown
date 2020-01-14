from pandac.PandaModules import *
from toontown.toonbase.ToonBaseGlobal import *
from . import DistributedSZTreasure
from direct.task.Task import Task
import math
import random

class DistributedEFlyingTreasure(DistributedSZTreasure.DistributedSZTreasure):

    def __init__(self, cr):
        DistributedSZTreasure.DistributedSZTreasure.__init__(self, cr)
        self.modelPath = 'phase_5.5/models/props/popsicle_treasure'
        self.grabSoundPath = 'phase_4/audio/sfx/SZ_DD_treasure.ogg'
        self.scale = 2
        self.delT = math.pi * 2.0 * random.random()
        self.shadow = 0

    def disable(self):
        DistributedSZTreasure.DistributedSZTreasure.disable(self)
        taskMgr.remove(self.taskName('flying-treasure'))

    def generateInit(self):
        DistributedSZTreasure.DistributedSZTreasure.generateInit(self)

    def setPosition(self, x, y, z):
        DistributedSZTreasure.DistributedSZTreasure.setPosition(self, x, y, z)
        self.initPos = self.nodePath.getPos()
        self.pos = self.nodePath.getPos()

    def startAnimation(self):
        taskMgr.add(self.animateTask, self.taskName('flying-treasure'))

    def animateTask(self, task):
        pos = self.initPos
        t = 0.5 * math.pi * globalClock.getFrameTime()
        dZ = 5.0 * math.sin(t + self.delT)
        dY = 2.0 * math.cos(t + self.delT)
        self.nodePath.setPos(pos[0], pos[1], pos[2] + dZ)
        if self.pos:
            del self.pos
        self.pos = self.nodePath.getPos()
        return Task.cont
