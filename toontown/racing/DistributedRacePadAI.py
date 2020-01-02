from direct.directnotify import DirectNotifyGlobal
from direct.distributed.ClockDelta import globalClockDelta
from direct.fsm.FSM import FSM

from toontown.racing.DistributedKartPadAI import DistributedKartPadAI


class DistributedRacePadAI(DistributedKartPadAI, FSM):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedRacePadAI')
    defaultTransitions = {'Off': ['WaitEmpty'],
                          'WaitEmpty': ['WaitCountdown', 'Off'],
                          'WaitCountdown': ['WaitEmpty',
                                            'WaitBoarding',
                                            'Off',
                                            'AllAboard'],
                          'WaitBoarding': ['AllAboard', 'WaitEmpty', 'Off'],
                          'AllAboard': ['Off', 'WaitEmpty', 'WaitCountdown']}

    def __init__(self, air):
        DistributedKartPadAI.__init__(self, air)
        FSM.__init__(self, 'DistributedRacePadAI')
        self.genre = 'urban'
        self.state = 'Off'
        self.trackInfo = [0, 0]
        self.laps = 3

    def setState(self, state):
        self.state = state

    def d_setState(self, state):
        self.sendUpdate('setState', [state, globalClockDelta.getRealNetworkTime()])

    def b_setState(self, state):
        self.setState(state)
        self.d_setState(state)

    def getState(self):
        return self.state, globalClockDelta.getRealNetworkTime()

    def setTrackInfo(self, trackInfo):
        self.trackInfo = [trackInfo[0], trackInfo[1]]

    def getTrackInfo(self):
        return self.trackInfo

    def request(self, state):
        FSM.request(self, state)
        self.b_setState(state)
