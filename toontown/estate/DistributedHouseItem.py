from direct.distributed import DistributedObject
from direct.distributed.ClockDelta import *
from direct.interval.IntervalGlobal import *

from toontown.toonbase import ToontownGlobals, TTLocalizer
from toontown.toonbase.ToontownGlobals import *


class DistributedHouseItem(DistributedObject.DistributedObject):
    notify = directNotify.newCategory('DistributedHouseItem')

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)

    def generate(self):
        DistributedObject.DistributedObject.generate(self)

    def announceGenerate(self):
        DistributedObject.DistributedObject.announceGenerate(self)
        self.load()

    def load(self):
        pass

    def disable(self):
        DistributedObject.DistributedObject.disable(self)

    def delete(self):
        DistributedObject.DistributedObject.delete(self)
