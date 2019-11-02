from direct.distributed.ClockDelta import globalClockDelta
from toontown.toonbase import TTLocalizer
from toontown.parties import PartyGlobals
from toontown.parties.DistributedPartyActivity import DistributedPartyActivity
from toontown.parties.activityFSMs import TeamActivityFSM
from toontown.parties.TeamActivityGui import TeamActivityGui

class DistributedPartyTeamActivity(DistributedPartyActivity):
    notify = directNotify.newCategory('DistributedPartyTeamActivity')

    def __init__(self, cr, activityId, startDelay = PartyGlobals.TeamActivityStartDelay, balanceTeams = False):
        DistributedPartyActivity.__init__(self, cr, activityId, PartyGlobals.ActivityTypes.GuestInitiated, wantRewardGui=True)
        self.notify.debug('__init__')
        self.toonIds = ([], [])
        self.isLocalToonPlaying = False
        self.localToonTeam = None
        self.advantage = 1.0
        self.waitToStartTimestamp = None
        self._maxPlayersPerTeam = 0
        self._minPlayersPerTeam = 0
        self._duration = 0
        self._startDelay = base.config.GetFloat('party-team-activity-start-delay', startDelay)
        self._willBalanceTeams = balanceTeams
        self._currentStatus = ''
        return

    def load(self):
        DistributedPartyActivity.load(self)
        self.teamActivityGui = TeamActivityGui(self)
        self.activityFSM = TeamActivityFSM(self)

    def unload(self):
        DistributedPartyActivity.unload(self)
        del self.activityFSM
        self.teamActivityGui.unload()
        del self.teamActivityGui
        if hasattr(self, 'toonIds'):
            del self.toonIds
        del self.isLocalToonPlaying
        del self.localToonTeam
        del self.advantage
        del self.waitToStartTimestamp

    def handleToonShifted(self, toonId):
        self.notify.error('handleToonShifted( toonId=%d ) must be overriden by child class.' % toonId)

    def handleToonSwitchedTeams(self, toonId):
        if toonId == base.localAvatar.doId and self._canSwitchTeams:
            if self.isState('WaitForEnough') or self.isState('WaitToStart'):
                self.teamActivityGui.enableExitButton()
                self.teamActivityGui.enableSwitchButton()

    def handleToonDisabled(self, toonId):
        self.notify.error('handleToonDisabled( toonId=%d ) must be overriden by child class.' % toonId)

    def setPlayersPerTeam(self, min, max):
        self._minPlayersPerTeam = min
        self._maxPlayersPerTeam = max

    def setDuration(self, duration):
        self._duration = duration

    def setCanSwitchTeams(self, canSwitchTeams):
        self._canSwitchTeams = canSwitchTeams

    def d_toonJoinRequest(self, team):
        if self.isLocalToonInActivity():
            return
        if self.activityFSM.state in ['WaitForEnough', 'WaitToStart'] and self._localToonRequestStatus is None:
            base.cr.playGame.getPlace().fsm.request('activity')
            self.localToonJoining()
            self.sendUpdate('toonJoinRequest', [team])
        return

    def d_toonExitRequest(self):
        toonId = base.localAvatar.doId
        team = self.getTeam(toonId)
        if team is not None:
            if self._localToonRequestStatus is None:
                self.localToonExiting()
                self.sendUpdate('toonExitRequest', [team])
        else:
            self.notify.warning('Not sending exitRequest as localToon has no team.')
        return

    def joinRequestDenied(self, reason):
        DistributedPartyActivity.joinRequestDenied(self, reason)
        self.notify.debug('joinRequestDenied')
        if reason == PartyGlobals.DenialReasons.Full:
            self.showMessage(TTLocalizer.PartyTeamActivityTeamFull)
        elif reason == PartyGlobals.DenialReasons.Default:
            self.showMessage(TTLocalizer.PartyTeamActivityJoinDenied % self.getTitle())

    def exitRequestDenied(self, reason):
        DistributedPartyActivity.exitRequestDenied(self, reason)
        if reason == PartyGlobals.DenialReasons.Default:
            self.showMessage(TTLocalizer.PartyTeamActivityExitDenied % self.getTitle())
        if self.isLocalToonPlaying and (self.isState('WaitToStart') or self.isState('WaitForEnough')):
            self.teamActivityGui.enableExitButton()
            if self._canSwitchTeams:
                self.teamActivityGui.enableSwitchButton()

    def d_toonSwitchTeamRequest(self):
        if not self._canSwitchTeams:
            return
        self.sendUpdate('toonSwitchTeamRequest')

    def switchTeamRequestDenied(self, reason):
        self.notify.debug('switchTeamRequestDenied')
        if reason == PartyGlobals.DenialReasons.Full:
            self.showMessage(TTLocalizer.PartyTeamActivityTeamFull, endState='activity')
        elif reason == PartyGlobals.DenialReasons.Default:
            self.showMessage(TTLocalizer.PartyTeamActivitySwitchDenied, endState='activity')
        if self.isLocalToonPlaying and (self.isState('WaitToStart') or self.isState('WaitForEnough')) and self._canSwitchTeams:
            self.teamActivityGui.enableSwitchButton()

    def setToonsPlaying(self, leftTeamToonIds, rightTeamToonIds):
        newToonIds = [leftTeamToonIds, rightTeamToonIds]
        exitedToons, joinedToons, shifters, switchers = self.getToonsPlayingChanges(self.toonIds, newToonIds)
        if base.localAvatar.doId in exitedToons:
            self.localToonExiting()
        self._processExitedToons(exitedToons)
        self.setToonIds([leftTeamToonIds, rightTeamToonIds])
        self._processJoinedToons(joinedToons)
        for toonId in shifters:
            self.handleToonShifted(toonId)

        if self._canSwitchTeams:
            for toonId in switchers:
                self.handleToonSwitchedTeams(toonId)

        if self.isState('WaitForEnough'):
            self._updateWaitForEnoughStatus()

    def _updateWaitForEnoughStatus(self):
        amount = self.getNumToonsNeededToStart()
        if self._willBalanceTeams:
            text = TTLocalizer.PartyTeamActivityForMoreWithBalance
        else:
            text = TTLocalizer.PartyTeamActivityForMore
        if amount > 1:
            plural = TTLocalizer.PartyTeamActivityForMorePlural
        else:
            plural = ''
        self.setStatus(text % (amount, plural))

    def setState(self, newState, timestamp, data):
        DistributedPartyActivity.setState(self, newState, timestamp)
        if newState == 'WaitToStart':
            self.activityFSM.request(newState, timestamp)
        elif newState == 'Conclusion':
            self.activityFSM.request(newState, data)
        else:
            self.activityFSM.request(newState)

    def d_toonReady(self):
        self.sendUpdate('toonReady')

    def setAdvantage(self, advantage):
        self.advantage = advantage

    def handleToonJoined(self, toonId):
        if toonId == base.localAvatar.doId:
            self.isLocalToonPlaying = True
            self.localToonTeam = self.getTeam(base.localAvatar.doId)
            self.teamActivityGui.load()
            self.teamActivityGui.enableExitButton()
            if self._canSwitchTeams:
                self.teamActivityGui.enableSwitchButton()
            if self.activityFSM.state == 'WaitToStart':
                self.showWaitToStartCountdown()
            else:
                self.showStatus()

    def handleToonExited(self, toonId):
        if toonId == base.localAvatar.doId:
            self.hideStatus()
            self.teamActivityGui.disableExitButton()
            if self._canSwitchTeams:
                self.teamActivityGui.disableSwitchButton()
            if self.activityFSM.state == 'WaitToStart':
                self.hideWaitToStartCountdown()
            self.teamActivityGui.unload()
            self.isLocalToonPlaying = False
            self.localToonTeam = None
        return

    def handleRulesDone(self):
        self.notify.debug('handleRulesDone')
        self.d_toonReady()
        self.activityFSM.request('WaitForServer')

    def handleGameTimerExpired(self):
        pass

    def getToonsPlayingChanges(self, oldToonIds, newToonIds):
        oldLeftTeam = oldToonIds[0]
        oldRightTeam = oldToonIds[1]
        newLeftTeam = newToonIds[0]
        newRightTeam = newToonIds[1]
        oldToons = set(oldLeftTeam + oldRightTeam)
        newToons = set(newLeftTeam + newRightTeam)
        exitedToons = oldToons.difference(newToons)
        joinedToons = newToons.difference(oldToons)
        shifters = []
        if self._canSwitchTeams:
            switchers = list(set(oldLeftTeam) & set(newRightTeam)) + list(set(oldRightTeam) & set(newLeftTeam))
        else:
            switchers = []
        for i in range(len(PartyGlobals.TeamActivityTeams)):
            persistentToons = set(oldToonIds[i]) & set(newToonIds[i])
            for toonId in persistentToons:
                if oldToonIds[i].index(toonId) != newToonIds[i].index(toonId):
                    shifters.append(toonId)

        return (list(exitedToons),
         list(joinedToons),
         shifters,
         switchers)

    def getMaxPlayersPerTeam(self):
        return self._maxPlayersPerTeam

    def getMinPlayersPerTeam(self):
        return self._minPlayersPerTeam

    def getNumToonsNeededToStart(self):
        if self._willBalanceTeams:
            return abs(self._minPlayersPerTeam * 2 - self.getNumToonsPlaying())
        else:
            return self._minPlayersPerTeam

    def getToonIdsAsList(self):
        return self.toonIds[0] + self.toonIds[1]

    def getNumToonsPlaying(self):
        return len(self.toonIds[0]) + len(self.toonIds[1])

    def getNumToonsInTeam(self, team):
        return len(self.toonIds[team])

    def getTeam(self, toonId):
        for i in range(len(PartyGlobals.TeamActivityTeams)):
            if self.toonIds[i].count(toonId) > 0:
                return i
        else:
            return None

        return None

    def getIndex(self, toonId, team):
        if self.toonIds[team].count(toonId) > 0:
            return self.toonIds[team].index(toonId)
        else:
            return None
        return None

    def _joinLeftTeam(self, collEntry):
        if self.isLocalToonInActivity():
            return
        self.d_toonJoinRequest(PartyGlobals.TeamActivityTeams.LeftTeam)

    def _joinRightTeam(self, collEntry):
        if self.isLocalToonInActivity():
            return
        self.d_toonJoinRequest(PartyGlobals.TeamActivityTeams.RightTeam)

    def showWaitToStartCountdown(self):
        if self.waitToStartTimestamp is None:
            self.notify.warning('showWaitToStartCountdown was called when self.waitToStartTimestamp was None')
            return
        self.teamActivityGui.showWaitToStartCountdown(self._startDelay, self.waitToStartTimestamp, almostDoneCallback=self._onCountdownAlmostDone)
        self.showStatus()
        self.teamActivityGui.enableExitButton()
        return

    def _onCountdownAlmostDone(self):
        if self._canSwitchTeams:
            self.teamActivityGui.disableSwitchButton()

    def hideWaitToStartCountdown(self):
        self.teamActivityGui.hideWaitToStartCountdown()
        self.teamActivityGui.disableExitButton()
        self.hideStatus()

    def setStatus(self, text):
        self._currentStatus = text
        if self.isLocalToonPlaying:
            self.showStatus()

    def showStatus(self):
        if self.teamActivityGui is not None:
            self.teamActivityGui.showStatus(self._currentStatus)
        return

    def hideStatus(self):
        if self.teamActivityGui is not None:
            self.teamActivityGui.hideStatus()
        return

    def toonsCanSwitchTeams(self):
        return self._canSwitchTeams

    def isState(self, state):
        return hasattr(self, 'activityFSM') and self.activityFSM.getCurrentOrNextState() == state

    def startWaitForEnough(self):
        self.notify.debug('startWaitForEnough')
        self.advantage = 1.0
        self._updateWaitForEnoughStatus()
        if self.isLocalToonPlaying:
            self.teamActivityGui.enableExitButton()
            if self._canSwitchTeams:
                self.teamActivityGui.enableSwitchButton()

    def finishWaitForEnough(self):
        self.notify.debug('finishWaitForEnough')

    def startWaitToStart(self, waitStartTimestamp):
        self.notify.debug('startWaitToStart')
        self.waitToStartTimestamp = globalClockDelta.networkToLocalTime(waitStartTimestamp)
        self._updateWaitForEnoughStatus()
        self.setStatus(TTLocalizer.PartyTeamActivityWaitingToStart)
        if self.isLocalToonPlaying:
            self.showWaitToStartCountdown()

    def finishWaitToStart(self):
        self.notify.debug('finishWaitToStart')
        if self.isLocalToonPlaying:
            self.hideWaitToStartCountdown()
            if self._canSwitchTeams:
                self.teamActivityGui.disableSwitchButton()
        self.waitToStartTimestamp = None
        return

    def startRules(self):
        self.notify.debug('startRules')
        if self.isLocalToonPlaying:
            DistributedPartyActivity.startRules(self)

    def finishRules(self):
        self.notify.debug('finishRules')
        if self.isLocalToonPlaying:
            DistributedPartyActivity.finishRules(self)
        if self.activityFSM.getCurrentOrNextState() == 'WaitForEnough':
            DistributedPartyActivity.finishRules(self)

    def startWaitForServer(self):
        self.notify.debug('startWaitForServer')
        self.setStatus(TTLocalizer.PartyTeamActivityWaitingForOtherPlayers)

    def finishWaitForServer(self):
        self.notify.debug('finishWaitForServer')
        if self.isLocalToonPlaying:
            self.hideStatus()

    def startActive(self):
        self.notify.debug('startActive')
        if self.isLocalToonPlaying:
            self.hideStatus()
            self.teamActivityGui.showTimer(self._duration)

    def finishActive(self):
        self.notify.debug('finishActive')
        if self.isLocalToonPlaying:
            self.teamActivityGui.hideTimer()
            self.hideStatus()

    def startConclusion(self, data):
        self.notify.debug('startConclusion')
        self.setStatus('')
        if self.isLocalToonPlaying:
            self.localToonExiting()

    def finishConclusion(self):
        self.notify.debug('finishConclusion')
        if self.isLocalToonPlaying:
            self.hideStatus()
