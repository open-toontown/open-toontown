from direct.directnotify import DirectNotifyGlobal

from toontown.toonbase.ToontownGlobals import *

from . import BasicEntities


class EntrancePoint(BasicEntities.NodePathEntity):

    def __init__(self, level, entId):
        BasicEntities.NodePathEntity.__init__(self, level, entId)
        self.rotator = self.attachNewNode('rotator')
        self.placer = self.rotator.attachNewNode('placer')
        self.initEntrancePoint()

    def destroy(self):
        self.destroyEntrancePoint()
        self.placer.removeNode()
        self.rotator.removeNode()
        del self.placer
        del self.rotator
        BasicEntities.NodePathEntity.destroy(self)

    def placeToon(self, toon, toonIndex, numToons):
        self.placer.setY(-self.radius)
        self.rotator.setH(-self.theta * (numToons - 1) * 0.5 + toonIndex * self.theta)
        toon.setPosHpr(self.placer, 0, 0, 0, 0, 0, 0)

    def initEntrancePoint(self):
        if self.entranceId >= 0:
            self.level.entranceId2entity[self.entranceId] = self

    def destroyEntrancePoint(self):
        if self.entranceId >= 0:
            if self.entranceId in self.level.entranceId2entity:
                del self.level.entranceId2entity[self.entranceId]

    if __dev__:

        def attribChanged(self, *args):
            BasicEntities.NodePathEntity.attribChanged(self, *args)
            self.destroyEntrancePoint()
            self.initEntrancePoint()
