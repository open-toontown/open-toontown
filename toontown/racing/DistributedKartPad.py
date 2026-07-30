from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObject import DistributedObject
if (__debug__):
    import pdb

class DistributedKartPad(DistributedObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedKartPad')

    def __init__(self, cr):
        DistributedObject.__init__(self, cr)
        self.startingBlocks = []

    def delete(self):
        del self.startingBlocks
        DistributedObject.delete(self)

    def setArea(self, area):
        self.area = area

    def getArea(self):
        return self.area

    def addStartingBlock(self, block):
        self.startingBlocks.append(block)
        self.notify.debug('KartPad %s has added starting block %s' % (self.doId, block.doId))
