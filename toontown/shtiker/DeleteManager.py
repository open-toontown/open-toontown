from panda3d.core import *
from direct.distributed import DistributedObject
from direct.directnotify import DirectNotifyGlobal

class DeleteManager(DistributedObject.DistributedObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('DeleteManager')
    neverDisable = 1

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)

    def generate(self):
        DistributedObject.DistributedObject.generate(self)
        self.accept('deleteItems', self.d_setInventory)

    def disable(self):
        self.ignore('deleteItems')
        DistributedObject.DistributedObject.disable(self)

    def d_setInventory(self, newInventoryString):
        self.sendUpdate('setInventory', [newInventoryString])
