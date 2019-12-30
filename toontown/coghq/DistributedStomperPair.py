from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *
import math
from . import StomperGlobals
from direct.directnotify import DirectNotifyGlobal
from otp.level import BasicEntities

class DistributedStomperPair(BasicEntities.DistributedNodePathEntity):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedStomperPair')

    def __init__(self, cr):
        BasicEntities.DistributedNodePathEntity.__init__(self, cr)
        self.children = None
        return

    def delete(self):
        BasicEntities.DistributedNodePathEntity.delete(self)
        self.ignoreAll()

    def generateInit(self):
        self.notify.debug('generateInit')
        BasicEntities.DistributedNodePathEntity.generateInit(self)

    def generate(self):
        self.notify.debug('generate')
        BasicEntities.DistributedNodePathEntity.generate(self)

    def announceGenerate(self):
        self.notify.debug('announceGenerate')
        BasicEntities.DistributedNodePathEntity.announceGenerate(self)
        self.listenForChildren()

    def listenForChildren(self):
        if self.stomperIds:
            for entId in self.stomperIds:
                self.accept(self.getUniqueName('crushMsg', entId), self.checkSquashedToon)

    def checkSquashedToon(self):
        tPos = base.localAvatar.getPos(self)
        print('tpos = %s' % tPos)
        yRange = 3.0
        xRange = 3.0
        if tPos[1] < yRange and tPos[1] > -yRange and tPos[0] < xRange and tPos[0] > -xRange:
            self.level.b_setOuch(3)
