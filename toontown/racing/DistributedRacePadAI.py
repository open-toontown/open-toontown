from direct.directnotify import DirectNotifyGlobal
from direct.distributed.ClockDelta import globalClockDelta

from toontown.racing.DistributedKartPadAI import DistributedKartPadAI


class DistributedRacePadAI(DistributedKartPadAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedRacePadAI')

    def __init__(self, air):
        DistributedKartPadAI.__init__(self, air)
        self.state = 'Off'
        self.trackInfo = [0, 0]

    def setState(self, state):
        self.state = state

    def d_setState(self, state):
        self.sendUpdate('setState', [state, globalClockDelta.getRealNetworkTime()])

    def b_setState(self, state):
        self.setState(state)
        self.d_setState(state)

    def getState(self):
        return self.state, globalClockDelta.getRealNetworkTime()

    def getTrackInfo(self):
        return self.trackInfo

    def request(self, state):
        self.b_setState(state)
