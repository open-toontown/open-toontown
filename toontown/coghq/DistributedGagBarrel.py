from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *
from toontown.toonbase.ToontownGlobals import *
from direct.directnotify import DirectNotifyGlobal
from . import DistributedBarrelBase

class DistributedGagBarrel(DistributedBarrelBase.DistributedBarrelBase):

    def __init__(self, cr):
        self.gagLevelMax = 0
        DistributedBarrelBase.DistributedBarrelBase.__init__(self, cr)
        self.numGags = 0
        self.gagScale = 13.0

    def disable(self):
        DistributedBarrelBase.DistributedBarrelBase.disable(self)
        self.ignoreAll()

    def delete(self):
        if hasattr(self, 'gagModel') and self.gagModel:
            self.gagModel.removeNode()
            del self.gagModel
        DistributedBarrelBase.DistributedBarrelBase.delete(self)

    def applyLabel(self):
        invModel = loader.loadModel('phase_3.5/models/gui/inventory_icons')
        self.invModels = []
        from toontown.toonbase import ToontownBattleGlobals
        for gagTrack in range(len(ToontownBattleGlobals.AvPropsNew)):
            itemList = []
            for item in range(len(ToontownBattleGlobals.AvPropsNew[gagTrack])):
                itemList.append(invModel.find('**/' + ToontownBattleGlobals.AvPropsNew[gagTrack][item]))

            self.invModels.append(itemList)

        invModel.removeNode()
        del invModel
        try:
            gagTrack = self.getGagTrack()
            gagLevel = self.getGagLevel()
            self.notify.debug('gagTrack = %s, gagLevel = %s' % (gagTrack, gagLevel))
            self.gagModel = self.invModels[gagTrack][gagLevel]
            self.gagModel.reparentTo(self.gagNode)
            self.gagModel.setScale(self.gagScale)
            self.gagModel.setPos(0, -0.1, 0)
        except AttributeError:
            self.notify.warning("Gag barrel is missing an attribute, can't apply label.")

    def setNumGags(self, num):
        self.numGags = num
        if hasattr(self, 'gagModel') and self.gagModel:
            if self.numGags == 0:
                self.gagModel.setColorScale(0.5, 0.5, 0.5, 1)
            else:
                self.gagModel.clearColorScale()

    def setGrab(self, avId):
        DistributedBarrelBase.DistributedBarrelBase.setGrab(self, avId)

    def resetBarrel(self):
        DistributedBarrelBase.DistributedBarrelBase.resetBarrel(self)
        if hasattr(self, 'gagModel') and self.gagModel:
            self.gagModel.setScale(self.gagScale)
