from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *
from .StomperGlobals import *
from direct.distributed import ClockDelta
from direct.showbase.PythonUtil import lerp
import math
from otp.level import DistributedEntity
from direct.directnotify import DirectNotifyGlobal
from pandac.PandaModules import NodePath
from otp.level import BasicEntities
from direct.task import Task
from toontown.toonbase import ToontownGlobals
from toontown.coghq import BattleBlocker
import random
from math import *

class DistributedMover(BasicEntities.DistributedNodePathEntity):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedMover')
    laserFieldModels = ['phase_9/models/cogHQ/square_stomper']

    def __init__(self, cr):
        BasicEntities.DistributedNodePathEntity.__init__(self, cr)
        self.attachedEnt = None
        self.oldParent = None
        self.entity2Move = None
        self.moveTarget = None
        self.pos0Wait = 1.0
        self.pos0Move = 1.0
        self.pos1Wait = 1.0
        self.pos1Move = 1.0
        self.moverIval = None
        return

    def generateInit(self):
        self.notify.debug('generateInit')
        BasicEntities.DistributedNodePathEntity.generateInit(self)

    def generate(self):
        self.notify.debug('generate')
        BasicEntities.DistributedNodePathEntity.generate(self)

    def announceGenerate(self):
        self.notify.debug('announceGenerate')
        BasicEntities.DistributedNodePathEntity.announceGenerate(self)
        self.loadModel()

    def disable(self):
        self.notify.debug('disable')
        self.ignoreAll()
        taskMgr.remove(self.taskName)
        BasicEntities.DistributedNodePathEntity.disable(self)

    def delete(self):
        self.notify.debug('delete')
        if self.moverIval:
            self.moverIval.finish()
        self.unloadModel()
        if self.taskName:
            taskMgr.remove(self.taskName)
        BasicEntities.DistributedNodePathEntity.delete(self)

    def loadModel(self):
        self.moverNode = self.attachNewNode('mover')
        self.rotateNode = self.attachNewNode('rotate')
        self.model = None
        if self.entity2Move:
            self.setEntity2Move(self.entity2Move)
        self.taskName = 'moverUpdate %s' % self.doId
        return

    def unloadModel(self):
        if self.model:
            self.model.removeNode()
            del self.model
            self.model = None
        return

    def setEntity2Move(self, entId):
        self.entity2Move = entId
        if entId:
            ent = self.level.getEntity(entId)
            if self.attachedEnt and not self.attachedEnt.isEmpty():
                self.attachedEnt.reparentTo(self.oldParent)
            self.oldParent = ent.getParent()
            ent.reparentTo(self.moverNode)
            self.attachedEnt = ent

    def startMove(self, timeStamp):
        currentTime = ClockDelta.globalClockDelta.getRealNetworkTime()
        timeDiff = (currentTime - timeStamp) / 1000.0
        target = self.level.getEntity(self.moveTarget)
        if not target:
            return
        okay2Play = 1
        if self.moverIval:
            self.moverIval.finish()
            if self.moverIval.isPlaying():
                okay2Play = 0
        if okay2Play and self.moveTarget:
            childList = self.getChildren()
            for child in childList:
                if child != self.moverNode:
                    child.reparentTo(self.moverNode)

            timeLag = 0.0
            timeJump = self.pos0Move - timeDiff
            if timeJump < 0 or self.cycleType in 'linear':
                timeJump = self.pos0Move
                timeLag = timeDiff
            myBlend = 'easeInOut'
            if self.cycleType in 'linear':
                myBlend = 'noBlend'
            self.moverIval = Sequence()
            firstIVal = LerpPosHprInterval(self.moverNode, timeJump, Vec3(target.getPos(self)[0], target.getPos(self)[1], target.getPos(self)[2]), Vec3(target.getHpr(self)[0], target.getHpr(self)[1], target.getHpr(self)[2]), blendType=myBlend, fluid=1)
            self.moverIval.append(firstIVal)
            if self.cycleType in 'linear':
                for linearCycle in range(10):
                    self.moverIval.append(firstIVal)

            if self.cycleType != 'oneWay':
                self.moverIval.append(Wait(self.pos1Wait))
                self.moverIval.append(LerpPosHprInterval(self.moverNode, self.pos1Move, Vec3(0, 0, 0), Vec3(0, 0, 0), blendType=myBlend, fluid=1))
            if self.cycleType == 'loop':
                self.moverIval.append(Wait(self.pos0Wait))
            self.moverIval.start()
            self.moverIval.setT(timeLag)
