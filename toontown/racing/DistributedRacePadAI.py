from direct.directnotify import DirectNotifyGlobal
from direct.distributed.ClockDelta import globalClockDelta
from direct.fsm.FSM import FSM

from toontown.racing import RaceGlobals
from toontown.racing.DistributedKartPadAI import DistributedKartPadAI
from toontown.racing.KartShopGlobals import KartGlobals


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
        self.avIds = []

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

    def addAvBlock(self, avId, startingBlock, paid):
        av = self.air.doId2do.get(avId)
        if not av:
            return

        if not av.hasKart():
            return KartGlobals.ERROR_CODE.eNoKart
        elif self.state == 'Off':
            return KartGlobals.ERROR_CODE.eTrackClosed
        elif self.state in ('AllAboard', 'WaitBoarding'):
            return KartGlobals.ERROR_CODE.eBoardOver
        elif startingBlock.avId != 0:
            return KartGlobals.ERROR_CODE.eOcuppied
        elif RaceGlobals.getEntryFee(self.trackInfo[0], self.trackInfo[1]) > av.getTickets():
            return KartGlobals.ERROR_CODE.eTickets

        self.avIds.append(avId)
        if not self.state == 'WaitCountdown':
            self.request('WaitCountdown')

        return KartGlobals.ERROR_CODE.success

    def removeAvBlock(self, avId, startingBlock):
        if avId == startingBlock.avId and avId in self.avIds:
            self.avIds.remove(avId)

    def kartMovieDone(self):
        if len(self.avIds) == 0 and not self.state == 'WaitEmpty':
            self.request('WaitEmpty')
        if self.state == 'WaitBoarding':
            self.considerAllAboard(0)
