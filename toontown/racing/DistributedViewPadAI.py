from direct.directnotify import DirectNotifyGlobal
from direct.distributed.ClockDelta import globalClockDelta

from toontown.racing.DistributedKartPadAI import DistributedKartPadAI


class DistributedViewPadAI(DistributedKartPadAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedViewPadAI')

    def __init__(self, air):
        DistributedKartPadAI.__init__(self, air)
        self.lastEntered = 0

    def announceGenerate(self):
        DistributedKartPadAI.announceGenerate(self)
        self.lastEntered = globalClockDelta.getRealNetworkTime()

    def getLastEntered(self):
        return self.lastEntered
