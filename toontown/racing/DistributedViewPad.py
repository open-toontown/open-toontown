from direct.directnotify import DirectNotifyGlobal
from direct.distributed.ClockDelta import *
from direct.task import Task
from pandac.PandaModules import *
from toontown.racing.DistributedKartPad import DistributedKartPad
from toontown.racing.KartShopGlobals import KartGlobals
if (__debug__):
    import pdb

class DistributedViewPad(DistributedKartPad):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedViewPad')
    id = 0

    def __init__(self, cr):
        DistributedKartPad.__init__(self, cr)
        self.id = DistributedViewPad.id
        DistributedViewPad.id += 1

    def setLastEntered(self, timeStamp):
        self.timeStamp = timeStamp

    def getTimestamp(self, avId):
        return self.timeStamp

    def addStartingBlock(self, block):
        block.cameraPos = Point3(0, 23, 7)
        block.cameraHpr = Point3(180, -10, 0)
        DistributedKartPad.addStartingBlock(self, block)
