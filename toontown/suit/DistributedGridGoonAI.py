from otp.ai.AIBaseGlobal import *
from direct.directnotify import DirectNotifyGlobal
from toontown.battle import SuitBattleGlobals
from . import DistributedGoonAI
from direct.task.Task import Task
from toontown.coghq import DistributedCrushableEntityAI
import random

class DistributedGridGoonAI(DistributedGoonAI.DistributedGoonAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedGridGoonAI')

    def __init__(self, level, entId):
        self.grid = None
        self.h = 0
        DistributedGoonAI.DistributedGoonAI.__init__(self, level, entId)
        return

    def generate(self):
        self.notify.debug('generate')
        DistributedCrushableEntityAI.DistributedCrushableEntityAI.generate(self)

    def initGridDependents(self):
        taskMgr.doMethodLater(2, self.goToNextPoint, self.taskName('walkTask'))

    def getPosition(self):
        if self.grid:
            return self.grid.getObjPos(self.entId)

    def getH(self):
        return self.h

    def goToNextPoint(self, task):
        if not self.grid:
            self.notify.warning("couldn't find grid, not starting")
            return
        if self.grid.checkMoveDir(self.entId, self.h):
            ptA = Point3(*self.getPosition())
            self.grid.doMoveDir(self.entId, self.h)
            ptB = Point3(*self.getPosition())
            self.sendUpdate('setPathPts', [ptA[0], ptA[1], ptA[2], ptB[0], ptB[1], ptB[2]])
            tPathSegment = Vec3(ptA - ptB).length() / self.velocity
        else:
            turn = int(random.randrange(1, 4) * 90)
            self.h = (self.h + turn) % 360
            tPathSegment = 0.1
        taskMgr.doMethodLater(tPathSegment, self.goToNextPoint, self.taskName('walkTask'))
        return Task.done
