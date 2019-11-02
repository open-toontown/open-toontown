from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *
from toontown.toonbase.ToontownGlobals import *
from direct.directnotify import DirectNotifyGlobal
import DistributedBarrelBase

class DistributedBeanBarrel(DistributedBarrelBase.DistributedBarrelBase):

    def __init__(self, cr):
        DistributedBarrelBase.DistributedBarrelBase.__init__(self, cr)
        self.numGags = 0
        self.gagScale = 3.0

    def disable(self):
        DistributedBarrelBase.DistributedBarrelBase.disable(self)
        self.ignoreAll()

    def delete(self):
        self.gagModel.removeNode()
        del self.gagModel
        DistributedBarrelBase.DistributedBarrelBase.delete(self)

    def applyLabel(self):
        purchaseModels = loader.loadModel('phase_4/models/gui/purchase_gui')
        self.gagModel = purchaseModels.find('**/Jar')
        self.gagModel.reparentTo(self.gagNode)
        self.gagModel.setScale(self.gagScale)
        self.gagModel.setPos(0, -0.1, 0)
        purchaseModels.removeNode()

    def setGrab(self, avId):
        DistributedBarrelBase.DistributedBarrelBase.setGrab(self, avId)
