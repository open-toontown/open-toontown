from direct.distributed import DistributedObject
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals
from pandac.PandaModules import *
from direct.distributed.ClockDelta import *
import time

class DistributedTimer(DistributedObject.DistributedObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedTimer')

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)

    def generate(self):
        DistributedObject.DistributedObject.generate(self)
        base.cr.DTimer = self

    def delete(self):
        DistributedObject.DistributedObject.delete(self)
        base.cr.DTimer = None
        return

    def setStartTime(self, time):
        self.startTime = time
        print('TIMER startTime %s' % time)

    def getStartTime(self):
        return self.startTime

    def getTime(self):
        elapsedTime = globalClockDelta.localElapsedTime(self.startTime, bits=32)
        return elapsedTime
