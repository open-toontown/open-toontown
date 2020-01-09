from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *
from toontown.toonbase.ToontownGlobals import *
from .CrateGlobals import *
from otp.level import BasicEntities
from direct.directnotify import DirectNotifyGlobal

class DistributedGrid(BasicEntities.DistributedNodePathEntity):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedGrid')

    def __init__(self, cr):
        BasicEntities.DistributedNodePathEntity.__init__(self, cr)
        self.model = None
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
        BasicEntities.DistributedNodePathEntity.disable(self)
        self.unloadModel()
        self.ignoreAll()

    def delete(self):
        BasicEntities.DistributedNodePathEntity.delete(self)

    def loadModel(self):
        self.notify.debug('loadModel')
        texSize = 6.0
        scale = self.cellSize / texSize
        self.model = loader.loadModel('phase_9/models/cogHQ/FloorWear.bam')
        self.model.reparentTo(self)
        long = self.numCol
        short = self.numRow
        h = 0
        if self.numCol < self.numRow:
            long = self.numRow
            short = self.numCol
            h = 90
        self.model.setScale(scale * long, scale * short, 1)
        self.model.setHpr(h, 180, 0)
        self.model.setPos(self.cellSize * self.numCol / 2.0, self.cellSize * self.numRow / 2.0, 0.025)
        self.model.setColor(0.588, 0.588, 0.459, 0.4)

    def unloadModel(self):
        if self.model:
            self.model.removeNode()
            del self.model

    def setNumRow(self, rows):
        self.numRow = rows
        self.unloadModel()
        self.loadModel()

    def setNumCol(self, cols):
        self.numCol = cols
        self.unloadModel()
        self.loadModel()
