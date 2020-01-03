from direct.directnotify import DirectNotifyGlobal
from direct.distributed.ClockDelta import globalClockDelta
from direct.fsm.FSM import FSM

from toontown.racing import RaceGlobals
from toontown.racing.DistributedKartPadAI import DistributedKartPadAI
from toontown.racing.KartShopGlobals import KartGlobals
from toontown.racing.RaceManagerAI import CircuitRaceHolidayMgr


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

    def delete(self):
        taskMgr.remove(self.uniqueName('changeTrack'))
        taskMgr.remove(self.uniqueName('countdownTask'))
        taskMgr.remove(self.uniqueName('enterRaceTask'))
        DistributedKartPadAI.delete(self)

    def request(self, state):
        FSM.request(self, state)
        self.b_setState(state)

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
        self.trackInfo = trackInfo

    def d_setTrackInfo(self, trackInfo):
        self.sendUpdate('setTrackInfo', [trackInfo])

    def b_setTrackInfo(self, trackInfo):
        self.setTrackInfo(trackInfo)
        self.d_setTrackInfo(trackInfo)

    def getTrackInfo(self):
        return self.trackInfo

    def enterWaitEmpty(self):
        taskMgr.doMethodLater(RaceGlobals.TrackSignDuration, self.changeTrack, self.uniqueName('changeTrack'))

    def exitWaitEmpty(self):
        taskMgr.remove(self.uniqueName('changeTrack'))

    def enterWaitCountdown(self):
        taskMgr.doMethodLater(KartGlobals.COUNTDOWN_TIME, self.considerAllAboard, self.uniqueName('countdownTask'))

    def exitWaitCountdown(self):
        taskMgr.remove(self.uniqueName('countdownTask'))

    def enterAllAboard(self):
        taskMgr.doMethodLater(KartGlobals.ENTER_RACE_TIME, self.enterRace, self.uniqueName('enterRaceTask'))

    def exitAllAboard(self):
        self.avIds = []
        taskMgr.remove(self.uniqueName('enterRaceTask'))

    def changeTrack(self, task):
        trackInfo = RaceGlobals.getNextRaceInfo(self.trackInfo[0], self.genre, self.index)
        trackId, raceType = trackInfo[0], trackInfo[1]
        if raceType == RaceGlobals.ToonBattle and bboard.get(CircuitRaceHolidayMgr.PostName):
            raceType = RaceGlobals.Circuit

        self.b_setTrackInfo([trackId, raceType])
        self.laps = trackInfo[2]
        return task.again

    def considerAllAboard(self, task=None):
        for startingBlock in self.startingBlocks:
            if startingBlock.currentMovie:
                if not self.state == 'WaitBoarding':
                    self.request('WaitBoarding')
                return

        if self.trackInfo[1] in (RaceGlobals.ToonBattle, RaceGlobals.Circuit) and len(self.avIds) < 2:
            for startingBlock in self.startingBlocks:
                if startingBlock.avId != 0:
                    startingBlock.normalExit()

            self.request('WaitEmpty')
            return

        self.request('AllAboard')
        if task:
            return task.done

    def enterRace(self, task):
        trackId, raceType = self.trackInfo
        circuitLoop = []
        if raceType == RaceGlobals.Circuit:
            circuitLoop = RaceGlobals.getCircuitLoop(trackId)

        raceZone = self.air.raceMgr.createRace(trackId, raceType, self.laps, self.avIds, circuitLoop=circuitLoop[1:], circuitPoints={}, circuitTimes={})
        for startingBlock in self.startingBlocks:
            self.sendUpdateToAvatarId(startingBlock.avId, 'setRaceZone', [raceZone])
            startingBlock.raceExit()

        return task.done

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
            self.considerAllAboard()
