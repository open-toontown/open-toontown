from otp.ai.AIBase import *
from direct.interval.IntervalGlobal import *
from direct.directnotify import DirectNotifyGlobal
from direct.distributed import ClockDelta
from direct.task import Task
from otp.level import DistributedEntityAI
from otp.level import BasicEntities
from direct.directnotify import DirectNotifyGlobal
from toontown.coghq import BattleBlockerAI
from toontown.coghq import LaserGameMineSweeper
from toontown.coghq import LaserGameRoll
import random

class DistributedMoverAI(DistributedEntityAI.DistributedEntityAI, NodePath, BasicEntities.NodePathAttribs):

    def __init__(self, level, entId):
        DistributedEntityAI.DistributedEntityAI.__init__(self, level, entId)
        node = hidden.attachNewNode('DistributedMoverAI')
        NodePath.__init__(self, node)
        if not hasattr(self, 'switchId'):
            self.switchId = 0
        if not hasattr(self, 'pos0Wait'):
            self.pos0Wait = 1.0
        if not hasattr(self, 'pos0Move'):
            self.pos0Move = 1.0
        if not hasattr(self, 'pos1Wait'):
            self.pos1Wait = 1.0
        if not hasattr(self, 'pos1Move'):
            self.pos1Move = 1.0
        if not hasattr(self, 'startOn'):
            self.startOn = 0
        if not hasattr(self, 'cycleType'):
            self.cycleType = 'return'
        self.moveTime = {}
        self.setTimes()
        self.oK2Play = 1

    def generate(self):
        DistributedEntityAI.DistributedEntityAI.generate(self)
        if self.switchId != 0:
            self.accept(self.getOutputEventName(self.switchId), self.reactToSwitch)
        self.timerName = 'mover %s' % self.doId
        self.setPos(self.pos)
        self.setHpr(self.hpr)
        self.setTimes()
        if self.startOn:
            self.sendMove()

    def delete(self):
        taskMgr.remove(self.timerName)
        self.ignoreAll()
        DistributedEntityAI.DistributedEntityAI.delete(self)

    def destroy(self):
        self.notify.info('destroy entity(laserField) %s' % self.entId)
        DistributedEntityAI.DistributedEntityAI.destroy(self)

    def reactToSwitch(self, on):
        if on:
            self.sendMove()

    def setPos0Move(self, time):
        self.pos0Move = time
        self.setTimes()

    def setPos1Move(self, time):
        self.pos1Move = time
        self.setTimes()

    def setPos0Wait(self, time):
        self.pos0Wait = time
        self.setTimes()

    def setPos1Wait(self, time):
        self.pos1Wait = time
        self.setTimes()

    def setTimes(self):
        self.moveTime = {}
        self.moveTime['return'] = self.pos0Move + self.pos1Wait + self.pos1Move
        self.moveTime['loop'] = self.pos0Wait + self.pos0Move + self.pos1Wait + self.pos1Move
        self.moveTime['oneWay'] = self.pos0Move
        self.moveTime['linear'] = self.pos0Move * 8

    def setCycleType(self, type):
        self.cycleType = type
        self.oK2Play = 1

    def setStartOn(self, on):
        self.startOn = on
        self.sendMove()

    def sendMove(self):
        timeStamp = ClockDelta.globalClockDelta.getRealNetworkTime()
        if self.oK2Play:
            self.sendUpdate('startMove', [timeStamp])
            taskMgr.doMethodLater(self.moveTime[self.cycleType], self.__resetTimer, self.timerName)
        self.oK2Play = 0

    def __resetTimer(self, taskMgrFooler=1):
        if not self.cycleType == 'oneWay':
            self.oK2Play = 1
            if self.cycleType in ('loop', 'linear') or self.startOn:
                self.sendMove()
        return Task.done
