import math

from panda3d.core import *
from panda3d.core import NodePath

from direct.directnotify import DirectNotifyGlobal
from direct.distributed import ClockDelta
from direct.interval.IntervalGlobal import *
from direct.showbase.PythonUtil import lerp
from direct.task import Task

from otp.level import BasicEntities, DistributedEntity

from toontown.toonbase import ToontownGlobals

from .StomperGlobals import *


class DistributedElevatorMarker(BasicEntities.DistributedNodePathEntity):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedElevatorMarker')
    elevatorMarkerModels = ['phase_9/models/cogHQ/square_stomper']

    def __init__(self, cr):
        BasicEntities.DistributedNodePathEntity.__init__(self, cr)

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
        DistributedEntity.DistributedEntity.disable(self)

    def delete(self):
        self.notify.debug('delete')
        self.unloadModel()
        BasicEntities.DistributedNodePathEntity.delete(self)

    def loadModel(self):
        self.rotateNode = self.attachNewNode('rotate')
        self.model = None
        if __dev__:
            self.model = loader.loadModel(self.elevatorMarkerModels[self.modelPath])
            self.model.reparentTo(self.rotateNode)
        return

    def unloadModel(self):
        if self.model:
            self.model.removeNode()
            del self.model
            self.model = None
        return
