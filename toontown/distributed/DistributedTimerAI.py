from direct.distributed import DistributedObjectAI
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals
from panda3d.core import *
from direct.distributed.ClockDelta import *
import time

class DistributedTimerAI(DistributedObjectAI.DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedTimerAI')

    def __init__(self, air):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        self.setStartTime(globalClockDelta.getRealNetworkTime(bits=32))

    def generate(self):
        DistributedObjectAI.DistributedObjectAI.generate(self)

    def setStartTime(self, time):
        self.startTime = time

    def getStartTime(self):
        return self.startTime
