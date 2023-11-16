from direct.directnotify import DirectNotifyGlobal
from direct.distributed import ClockDelta
from direct.interval.IntervalGlobal import *
from direct.task import Task

from otp.ai.AIBase import *
from otp.level import BasicEntities, DistributedEntityAI


class DistributedElevatorMarkerAI(DistributedEntityAI.DistributedEntityAI, NodePath, BasicEntities.NodePathAttribs):

    def __init__(self, level, entId):
        DistributedEntityAI.DistributedEntityAI.__init__(self, level, entId)
        node = hidden.attachNewNode('DistributedElevatorMarkerAI')
        NodePath.__init__(self, node)

    def generate(self):
        DistributedEntityAI.DistributedEntityAI.generate(self)
        self.setPos(self.pos)
        self.setHpr(self.hpr)

    def delete(self):
        self.ignoreAll()
        DistributedEntityAI.DistributedEntityAI.delete(self)

    def destroy(self):
        self.notify.info('destroy entity(elevatorMaker) %s' % self.entId)
        DistributedEntityAI.DistributedEntityAI.destroy(self)
