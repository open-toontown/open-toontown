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

class DistributedSecurityCameraAI(DistributedEntityAI.DistributedEntityAI, NodePath, BasicEntities.NodePathAttribs):

    def __init__(self, level, entId):
        DistributedEntityAI.DistributedEntityAI.__init__(self, level, entId)
        node = hidden.attachNewNode('DistributedSecurityCameraAI')
        NodePath.__init__(self, node)
        if not hasattr(self, 'switchId'):
            self.switchId = 0
        if not hasattr(self, 'damPow'):
            self.damPow = 1
        self.enabled = 1
        self.detectName = None
        return

    def generate(self):
        DistributedEntityAI.DistributedEntityAI.generate(self)
        if self.switchId != 0:
            self.accept(self.getOutputEventName(self.switchId), self.reactToSwitch)
        self.detectName = 'laserField %s' % self.doId
        taskMgr.doMethodLater(3.0, self.__detect, self.detectName)
        self.setPos(self.pos)
        self.setHpr(self.hpr)

    def delete(self):
        if self.detectName:
            taskMgr.remove(self.detectName)
        self.ignoreAll()
        DistributedEntityAI.DistributedEntityAI.delete(self)

    def destroy(self):
        self.notify.info('destroy entity(laserField) %s' % self.entId)
        DistributedEntityAI.DistributedEntityAI.destroy(self)

    def __detect(self, task):
        isThereAnyToons = False
        if hasattr(self, 'level'):
            toonInRange = 0
            for avId in self.level.presentAvIds:
                if avId in self.air.doId2do:
                    av = self.air.doId2do[avId]
                    isThereAnyToons = True
                    distance = self.getDistance(av)

            if isThereAnyToons:
                randTime = float(random.randint(1, 6)) * 0.5
                taskMgr.doMethodLater(randTime, self.__detect, self.detectName)
                randTarget = random.randint(0, 100)
                self.sendUpdate('setTarget', [randTarget])
        return Task.done

    def hit(self, hitX, hitY):
        if self.enabled:
            self.game.hit(hitX, hitY)

    def reactToSwitch(self, on):
        if on:
            self.trapDisable()
            self.game.win()

    def trapFire(self):
        avId = self.air.getAvatarIdFromSender()
        toon = self.air.doId2do[avId]
        if toon:
            toon.takeDamage(self.damPow)

    def trapDisable(self):
        self.enabled = 0
