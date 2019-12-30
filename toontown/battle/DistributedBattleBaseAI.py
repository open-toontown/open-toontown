from otp.ai.AIBase import *
from direct.distributed.ClockDelta import *
from .BattleBase import *
from . import BattleCalculatorAI
from toontown.toonbase.ToontownBattleGlobals import *
from .SuitBattleGlobals import *
from pandac.PandaModules import *
from . import BattleExperienceAI
from direct.distributed import DistributedObjectAI
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from direct.task import Task
from direct.directnotify import DirectNotifyGlobal
from toontown.ai import DatabaseObject
from toontown.toon import DistributedToonAI
from toontown.toon import InventoryBase
from toontown.toonbase import ToontownGlobals
import random
from toontown.toon import NPCToons

class DistributedBattleBaseAI(DistributedObjectAI.DistributedObjectAI, BattleBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedBattleBaseAI')

    def __init__(self, air, zoneId, finishCallback=None, maxSuits=4, bossBattle=0, tutorialFlag=0, interactivePropTrackBonus=-1):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        self.serialNum = 0
        self.zoneId = zoneId
        self.maxSuits = maxSuits
        self.setBossBattle(bossBattle)
        self.tutorialFlag = tutorialFlag
        self.interactivePropTrackBonus = interactivePropTrackBonus
        self.finishCallback = finishCallback
        self.avatarExitEvents = []
        self.responses = {}
        self.adjustingResponses = {}
        self.joinResponses = {}
        self.adjustingSuits = []
        self.adjustingToons = []
        self.numSuitsEver = 0
        BattleBase.__init__(self)
        self.streetBattle = 1
        self.pos = Point3(0, 0, 0)
        self.initialSuitPos = Point3(0, 0, 0)
        self.toonExp = {}
        self.toonOrigQuests = {}
        self.toonItems = {}
        self.toonOrigMerits = {}
        self.toonMerits = {}
        self.toonParts = {}
        self.battleCalc = BattleCalculatorAI.BattleCalculatorAI(self, tutorialFlag)
        if self.air.suitInvasionManager.getInvading():
            mult = getInvasionMultiplier()
            self.battleCalc.setSkillCreditMultiplier(mult)
        if self.air.holidayManager.isMoreXpHolidayRunning():
            mult = getMoreXpHolidayMultiplier()
            self.battleCalc.setSkillCreditMultiplier(mult)
        self.fsm = None
        self.clearAttacks()
        self.ignoreFaceOffDone = 0
        self.needAdjust = 0
        self.movieHasBeenMade = 0
        self.movieHasPlayed = 0
        self.rewardHasPlayed = 0
        self.movieRequested = 0
        self.ignoreResponses = 0
        self.ignoreAdjustingResponses = 0
        self.taskNames = []
        self.exitedToons = []
        self.suitsKilled = []
        self.suitsKilledThisBattle = []
        self.suitsKilledPerFloor = []
        self.suitsEncountered = []
        self.newToons = []
        self.newSuits = []
        self.numNPCAttacks = 0
        self.npcAttacks = {}
        self.pets = {}
        self.fsm = ClassicFSM.ClassicFSM('DistributedBattleAI', [
         State.State('FaceOff', self.enterFaceOff, self.exitFaceOff, [
          'WaitForInput', 'Resume']),
         State.State('WaitForJoin', self.enterWaitForJoin, self.exitWaitForJoin, [
          'WaitForInput', 'Resume']),
         State.State('WaitForInput', self.enterWaitForInput, self.exitWaitForInput, [
          'MakeMovie', 'Resume']),
         State.State('MakeMovie', self.enterMakeMovie, self.exitMakeMovie, [
          'PlayMovie', 'Resume']),
         State.State('PlayMovie', self.enterPlayMovie, self.exitPlayMovie, [
          'WaitForJoin', 'Reward', 'Resume']),
         State.State('Reward', self.enterReward, self.exitReward, [
          'Resume']),
         State.State('Resume', self.enterResume, self.exitResume, []),
         State.State('Off', self.enterOff, self.exitOff, [
          'FaceOff', 'WaitForJoin'])], 'Off', 'Off')
        self.joinableFsm = ClassicFSM.ClassicFSM('Joinable', [
         State.State('Joinable', self.enterJoinable, self.exitJoinable, [
          'Unjoinable']),
         State.State('Unjoinable', self.enterUnjoinable, self.exitUnjoinable, [
          'Joinable'])], 'Unjoinable', 'Unjoinable')
        self.joinableFsm.enterInitialState()
        self.runableFsm = ClassicFSM.ClassicFSM('Runable', [
         State.State('Runable', self.enterRunable, self.exitRunable, [
          'Unrunable']),
         State.State('Unrunable', self.enterUnrunable, self.exitUnrunable, [
          'Runable'])], 'Unrunable', 'Unrunable')
        self.runableFsm.enterInitialState()
        self.adjustFsm = ClassicFSM.ClassicFSM('Adjust', [
         State.State('Adjusting', self.enterAdjusting, self.exitAdjusting, [
          'NotAdjusting', 'Adjusting']),
         State.State('NotAdjusting', self.enterNotAdjusting, self.exitNotAdjusting, [
          'Adjusting'])], 'NotAdjusting', 'NotAdjusting')
        self.adjustFsm.enterInitialState()
        self.fsm.enterInitialState()
        self.startTime = globalClock.getRealTime()
        self.adjustingTimer = Timer()
        return

    def clearAttacks(self):
        self.toonAttacks = {}
        self.suitAttacks = getDefaultSuitAttacks()

    def requestDelete(self):
        if hasattr(self, 'fsm'):
            self.fsm.request('Off')
        self.__removeTaskName(self.uniqueName('make-movie'))
        DistributedObjectAI.DistributedObjectAI.requestDelete(self)

    def delete(self):
        self.notify.debug('deleting battle')
        self.fsm.request('Off')
        self.ignoreAll()
        self.__removeAllTasks()
        del self.fsm
        del self.joinableFsm
        del self.runableFsm
        del self.adjustFsm
        self.__cleanupJoinResponses()
        self.timer.stop()
        del self.timer
        self.adjustingTimer.stop()
        del self.adjustingTimer
        self.battleCalc.cleanup()
        del self.battleCalc
        for suit in self.suits:
            del suit.battleTrap

        del self.finishCallback
        for petProxy in list(self.pets.values()):
            petProxy.requestDelete()

        DistributedObjectAI.DistributedObjectAI.delete(self)

    def pause(self):
        self.timer.stop()
        self.adjustingTimer.stop()

    def unpause(self):
        self.timer.resume()
        self.adjustingTimer.resume()

    def abortBattle(self):
        self.notify.debug('%s.abortBattle() called.' % self.doId)
        toonsCopy = self.toons[:]
        for toonId in toonsCopy:
            self.__removeToon(toonId)
            if self.fsm.getCurrentState().getName() == 'PlayMovie' or self.fsm.getCurrentState().getName() == 'MakeMovie':
                self.exitedToons.append(toonId)

        self.d_setMembers()
        self.b_setState('Resume')
        self.__removeAllTasks()
        self.timer.stop()
        self.adjustingTimer.stop()

    def findSuit(self, id):
        for s in self.suits:
            if s.doId == id:
                return s

        return None

    def __removeTaskName(self, name):
        if self.taskNames.count(name):
            self.taskNames.remove(name)
            self.notify.debug('removeTaskName() - %s' % name)
            taskMgr.remove(name)

    def __removeAllTasks(self):
        for n in self.taskNames:
            self.notify.debug('removeAllTasks() - %s' % n)
            taskMgr.remove(n)

        self.taskNames = []

    def __removeToonTasks(self, toonId):
        name = self.taskName('running-toon-%d' % toonId)
        self.__removeTaskName(name)
        name = self.taskName('to-pending-av-%d' % toonId)
        self.__removeTaskName(name)

    def getLevelDoId(self):
        return 0

    def getBattleCellId(self):
        return 0

    def getPosition(self):
        self.notify.debug('getPosition() - %s' % self.pos)
        return [
         self.pos[0], self.pos[1], self.pos[2]]

    def getInitialSuitPos(self):
        p = []
        p.append(self.initialSuitPos[0])
        p.append(self.initialSuitPos[1])
        p.append(self.initialSuitPos[2])
        return p

    def setBossBattle(self, bossBattle):
        self.bossBattle = bossBattle

    def getBossBattle(self):
        return self.bossBattle

    def b_setState(self, state):
        self.notify.debug('network:setState(%s)' % state)
        stime = globalClock.getRealTime() + SERVER_BUFFER_TIME
        self.sendUpdate('setState', [state, globalClockDelta.localToNetworkTime(stime)])
        self.setState(state)

    def setState(self, state):
        self.fsm.request(state)

    def getState(self):
        return [
         self.fsm.getCurrentState().getName(), globalClockDelta.getRealNetworkTime()]

    def d_setMembers(self):
        self.notify.debug('network:setMembers()')
        self.sendUpdate('setMembers', self.getMembers())

    def getMembers(self):
        suits = []
        for s in self.suits:
            suits.append(s.doId)

        joiningSuits = ''
        for s in self.joiningSuits:
            joiningSuits += str(suits.index(s.doId))

        pendingSuits = ''
        for s in self.pendingSuits:
            pendingSuits += str(suits.index(s.doId))

        activeSuits = ''
        for s in self.activeSuits:
            activeSuits += str(suits.index(s.doId))

        luredSuits = ''
        for s in self.luredSuits:
            luredSuits += str(suits.index(s.doId))

        suitTraps = ''
        for s in self.suits:
            if s.battleTrap == NO_TRAP:
                suitTraps += '9'
            elif s.battleTrap == BattleCalculatorAI.BattleCalculatorAI.TRAP_CONFLICT:
                suitTraps += '9'
            else:
                suitTraps += str(s.battleTrap)

        toons = []
        for t in self.toons:
            toons.append(t)

        joiningToons = ''
        for t in self.joiningToons:
            joiningToons += str(toons.index(t))

        pendingToons = ''
        for t in self.pendingToons:
            pendingToons += str(toons.index(t))

        activeToons = ''
        for t in self.activeToons:
            activeToons += str(toons.index(t))

        runningToons = ''
        for t in self.runningToons:
            runningToons += str(toons.index(t))

        self.notify.debug('getMembers() - suits: %s joiningSuits: %s pendingSuits: %s activeSuits: %s luredSuits: %s suitTraps: %s toons: %s joiningToons: %s pendingToons: %s activeToons: %s runningToons: %s' % (suits, joiningSuits, pendingSuits, activeSuits, luredSuits, suitTraps, toons, joiningToons, pendingToons, activeToons, runningToons))
        return [
         suits, joiningSuits, pendingSuits, activeSuits, luredSuits, suitTraps, toons, joiningToons, pendingToons, activeToons, runningToons, globalClockDelta.getRealNetworkTime()]

    def d_adjust(self):
        self.notify.debug('network:adjust()')
        self.sendUpdate('adjust', [globalClockDelta.getRealNetworkTime()])

    def getInteractivePropTrackBonus(self):
        return self.interactivePropTrackBonus

    def getZoneId(self):
        return self.zoneId

    def getTaskZoneId(self):
        return self.zoneId

    def d_setMovie(self):
        self.notify.debug('network:setMovie()')
        self.sendUpdate('setMovie', self.getMovie())
        self.__updateEncounteredCogs()

    def getMovie(self):
        suitIds = []
        for s in self.activeSuits:
            suitIds.append(s.doId)

        p = [self.movieHasBeenMade]
        p.append(self.activeToons)
        p.append(suitIds)
        for t in self.activeToons:
            if t in self.toonAttacks:
                ta = self.toonAttacks[t]
                index = -1
                id = ta[TOON_ID_COL]
                if id != -1:
                    index = self.activeToons.index(id)
                track = ta[TOON_TRACK_COL]
                if (track == NO_ATTACK or attackAffectsGroup(track, ta[TOON_LVL_COL])) and track != NPCSOS and track != PETSOS:
                    target = -1
                    if track == HEAL:
                        if ta[TOON_LVL_COL] == 1:
                            ta[TOON_HPBONUS_COL] = random.randint(0, 10000)
                elif track == SOS or track == NPCSOS or track == PETSOS:
                    target = ta[TOON_TGT_COL]
                elif track == HEAL:
                    if self.activeToons.count(ta[TOON_TGT_COL]) != 0:
                        target = self.activeToons.index(ta[TOON_TGT_COL])
                    else:
                        target = -1
                elif suitIds.count(ta[TOON_TGT_COL]) != 0:
                    target = suitIds.index(ta[TOON_TGT_COL])
                else:
                    target = -1
                p = p + [index,
                 track,
                 ta[TOON_LVL_COL],
                 target]
                p = p + ta[4:]
            else:
                index = self.activeToons.index(t)
                attack = getToonAttack(index)
                p = p + attack

        for i in range(4 - len(self.activeToons)):
            p = p + getToonAttack(-1)

        for sa in self.suitAttacks:
            index = -1
            id = sa[SUIT_ID_COL]
            if id != -1:
                index = suitIds.index(id)
            if sa[SUIT_ATK_COL] == -1:
                targetIndex = -1
            else:
                targetIndex = sa[SUIT_TGT_COL]
                if targetIndex == -1:
                    self.notify.debug('suit attack: %d must be group' % sa[SUIT_ATK_COL])
                else:
                    toonId = self.activeToons[targetIndex]
            p = p + [index, sa[SUIT_ATK_COL], targetIndex]
            sa[SUIT_TAUNT_COL] = 0
            if sa[SUIT_ATK_COL] != -1:
                suit = self.findSuit(id)
                sa[SUIT_TAUNT_COL] = getAttackTauntIndexFromIndex(suit, sa[SUIT_ATK_COL])
            p = p + sa[3:]

        return p

    def d_setChosenToonAttacks(self):
        self.notify.debug('network:setChosenToonAttacks()')
        self.sendUpdate('setChosenToonAttacks', self.getChosenToonAttacks())

    def getChosenToonAttacks(self):
        ids = []
        tracks = []
        levels = []
        targets = []
        for t in self.activeToons:
            if t in self.toonAttacks:
                ta = self.toonAttacks[t]
            else:
                ta = getToonAttack(t)
            ids.append(t)
            tracks.append(ta[TOON_TRACK_COL])
            levels.append(ta[TOON_LVL_COL])
            targets.append(ta[TOON_TGT_COL])

        return [ids, tracks, levels, targets]

    def d_setBattleExperience(self):
        self.notify.debug('network:setBattleExperience()')
        self.sendUpdate('setBattleExperience', self.getBattleExperience())

    def getBattleExperience(self):
        returnValue = BattleExperienceAI.getBattleExperience(4, self.activeToons, self.toonExp, self.battleCalc.toonSkillPtsGained, self.toonOrigQuests, self.toonItems, self.toonOrigMerits, self.toonMerits, self.toonParts, self.suitsKilled, self.helpfulToons)
        return returnValue

    def getToonUberStatus(self):
        fieldList = []
        uberIndex = LAST_REGULAR_GAG_LEVEL + 1
        for toon in self.activeToons:
            toonList = []
            for trackIndex in range(MAX_TRACK_INDEX):
                toonList.append(toon.inventory.numItem(track, uberIndex))

            fieldList.append(encodeUber(toonList))

        return fieldList

    def addSuit(self, suit):
        self.notify.debug('addSuit(%d)' % suit.doId)
        self.newSuits.append(suit)
        self.suits.append(suit)
        suit.battleTrap = NO_TRAP
        self.numSuitsEver += 1

    def __joinSuit(self, suit):
        self.joiningSuits.append(suit)
        toPendingTime = MAX_JOIN_T + SERVER_BUFFER_TIME
        taskName = self.taskName('to-pending-av-%d' % suit.doId)
        self.__addJoinResponse(suit.doId, taskName)
        self.taskNames.append(taskName)
        taskMgr.doMethodLater(toPendingTime, self.__serverJoinDone, taskName, extraArgs=(suit.doId, taskName))

    def __serverJoinDone(self, avId, taskName):
        self.notify.debug('join for av: %d timed out on server' % avId)
        self.__removeTaskName(taskName)
        self.__makeAvPending(avId)
        return Task.done

    def __makeAvPending(self, avId):
        self.notify.debug('__makeAvPending(%d)' % avId)
        self.__removeJoinResponse(avId)
        self.__removeTaskName(self.taskName('to-pending-av-%d' % avId))
        if self.toons.count(avId) > 0:
            self.joiningToons.remove(avId)
            self.pendingToons.append(avId)
        else:
            suit = self.findSuit(avId)
            if suit != None:
                if not suit.isEmpty():
                    if not self.joiningSuits.count(suit) == 1:
                        self.notify.warning('__makeAvPending(%d) in zone: %d' % (avId, self.zoneId))
                        self.notify.warning('toons: %s' % self.toons)
                        self.notify.warning('joining toons: %s' % self.joiningToons)
                        self.notify.warning('pending toons: %s' % self.pendingToons)
                        self.notify.warning('suits: %s' % self.suits)
                        self.notify.warning('joining suits: %s' % self.joiningSuits)
                        self.notify.warning('pending suits: %s' % self.pendingSuits)
                    self.joiningSuits.remove(suit)
                    self.pendingSuits.append(suit)
            else:
                self.notify.warning('makeAvPending() %d not in toons or suits' % avId)
                return
        self.d_setMembers()
        self.needAdjust = 1
        self.__requestAdjust()
        return

    def suitRequestJoin(self, suit):
        self.notify.debug('suitRequestJoin(%d)' % suit.getDoId())
        if self.suitCanJoin():
            self.addSuit(suit)
            self.__joinSuit(suit)
            self.d_setMembers()
            suit.prepareToJoinBattle()
            return 1
        else:
            self.notify.warning('suitRequestJoin() - not joinable - joinable state: %s max suits: %d' % (self.joinableFsm.getCurrentState().getName(), self.maxSuits))
            return 0

    def addToon(self, avId):
        print('DBB-addToon %s' % avId)
        self.notify.debug('addToon(%d)' % avId)
        toon = self.getToon(avId)
        if toon == None:
            return 0
        toon.stopToonUp()
        event = simbase.air.getAvatarExitEvent(avId)
        self.avatarExitEvents.append(event)
        self.accept(event, self.__handleUnexpectedExit, extraArgs=[avId])
        event = 'inSafezone-%s' % avId
        self.avatarExitEvents.append(event)
        self.accept(event, self.__handleSuddenExit, extraArgs=[avId, 0])
        self.newToons.append(avId)
        self.toons.append(avId)
        toon = simbase.air.doId2do.get(avId)
        if toon:
            if hasattr(self, 'doId'):
                toon.b_setBattleId(self.doId)
            else:
                toon.b_setBattleId(-1)
            messageToonAdded = 'Battle adding toon %s' % avId
            messenger.send(messageToonAdded, [avId])
        if self.fsm != None and self.fsm.getCurrentState().getName() == 'PlayMovie':
            self.responses[avId] = 1
        else:
            self.responses[avId] = 0
        self.adjustingResponses[avId] = 0
        if avId not in self.toonExp:
            p = []
            for t in Tracks:
                p.append(toon.experience.getExp(t))

            self.toonExp[avId] = p
        if avId not in self.toonOrigMerits:
            self.toonOrigMerits[avId] = toon.cogMerits[:]
        if avId not in self.toonMerits:
            self.toonMerits[avId] = [0,
             0,
             0,
             0]
        if avId not in self.toonOrigQuests:
            flattenedQuests = []
            for quest in toon.quests:
                flattenedQuests.extend(quest)

            self.toonOrigQuests[avId] = flattenedQuests
        if avId not in self.toonItems:
            self.toonItems[avId] = ([], [])
        return 1

    def __joinToon(self, avId, pos):
        self.joiningToons.append(avId)
        toPendingTime = MAX_JOIN_T + SERVER_BUFFER_TIME
        taskName = self.taskName('to-pending-av-%d' % avId)
        self.__addJoinResponse(avId, taskName, toon=1)
        taskMgr.doMethodLater(toPendingTime, self.__serverJoinDone, taskName, extraArgs=(avId, taskName))
        self.taskNames.append(taskName)

    def __updateEncounteredCogs(self):
        for toon in self.activeToons:
            if toon in self.newToons:
                for suit in self.activeSuits:
                    if hasattr(suit, 'dna'):
                        self.suitsEncountered.append({'type': suit.dna.name, 'activeToons': self.activeToons[:]})
                    else:
                        self.notify.warning('Suit has no DNA in zone %s: toons involved = %s' % (self.zoneId, self.activeToons))
                        return

                self.newToons.remove(toon)

        for suit in self.activeSuits:
            if suit in self.newSuits:
                if hasattr(suit, 'dna'):
                    self.suitsEncountered.append({'type': suit.dna.name, 'activeToons': self.activeToons[:]})
                else:
                    self.notify.warning('Suit has no DNA in zone %s: toons involved = %s' % (self.zoneId, self.activeToons))
                    return
                self.newSuits.remove(suit)

    def __makeToonRun(self, toonId, updateAttacks):
        self.activeToons.remove(toonId)
        self.toonGone = 1
        self.runningToons.append(toonId)
        taskName = self.taskName('running-toon-%d' % toonId)
        taskMgr.doMethodLater(TOON_RUN_T, self.__serverRunDone, taskName, extraArgs=(toonId, updateAttacks, taskName))
        self.taskNames.append(taskName)

    def __serverRunDone(self, toonId, updateAttacks, taskName):
        self.notify.debug('run for toon: %d timed out on server' % toonId)
        self.__removeTaskName(taskName)
        self.__removeToon(toonId)
        self.d_setMembers()
        if len(self.toons) == 0:
            self.notify.debug('last toon is gone - battle is finished')
            self.b_setState('Resume')
        else:
            if updateAttacks == 1:
                self.d_setChosenToonAttacks()
            self.needAdjust = 1
            self.__requestAdjust()
        return Task.done

    def __requestAdjust(self):
        if not self.fsm:
            return
        cstate = self.fsm.getCurrentState().getName()
        if cstate == 'WaitForInput' or cstate == 'WaitForJoin':
            if self.adjustFsm.getCurrentState().getName() == 'NotAdjusting':
                if self.needAdjust == 1:
                    self.d_adjust()
                    self.adjustingSuits = []
                    for s in self.pendingSuits:
                        self.adjustingSuits.append(s)

                    self.adjustingToons = []
                    for t in self.pendingToons:
                        self.adjustingToons.append(t)

                    self.adjustFsm.request('Adjusting')
                else:
                    self.notify.debug('requestAdjust() - dont need to')
            else:
                self.notify.debug('requestAdjust() - already adjusting')
        else:
            self.notify.debug('requestAdjust() - in state: %s' % cstate)

    def __handleUnexpectedExit(self, avId):
        disconnectCode = self.air.getAvatarDisconnectReason(avId)
        self.notify.warning('toon: %d exited unexpectedly, reason %d' % (avId, disconnectCode))
        userAborted = disconnectCode == ToontownGlobals.DisconnectCloseWindow
        self.__handleSuddenExit(avId, userAborted)

    def __handleSuddenExit(self, avId, userAborted):
        self.__removeToon(avId, userAborted=userAborted)
        if self.fsm.getCurrentState().getName() == 'PlayMovie' or self.fsm.getCurrentState().getName() == 'MakeMovie':
            self.exitedToons.append(avId)
        self.d_setMembers()
        if len(self.toons) == 0:
            self.notify.debug('last toon is gone - battle is finished')
            self.__removeAllTasks()
            self.timer.stop()
            self.adjustingTimer.stop()
            self.b_setState('Resume')
        else:
            self.needAdjust = 1
            self.__requestAdjust()

    def __removeSuit(self, suit):
        self.notify.debug('__removeSuit(%d)' % suit.doId)
        if self.suits.count(suit) != 0:
            self.suits.remove(suit)
        else:
            self.air.writeServerEvent('suspicious', self.activeToons, 'Trying to remove a suit, with suit count at zero. Probably hacker related.')
        if self.joiningSuits.count(suit) != 0:
            self.air.writeServerEvent('suspicious', self.activeToons, 'Trying to remove a suit, but joiningSuits is not zero. Probably hacker related.')
        if self.pendingSuits.count(suit) != 0:
            self.air.writeServerEvent('suspicious', self.activeToons, 'Trying to remove a suit, but pendingSuits is not zero. Probably hacker related.')
        if self.adjustingSuits.count(suit) != 0:
            self.air.writeServerEvent('suspicious', self.activeToons, 'Trying to remove a suit, but adjustingSuits is not zero. Probably hacker related.')
        if self.activeSuits.count(suit) != 0:
            self.activeSuits.remove(suit)
        else:
            self.air.writeServerEvent('suspicious', self.activeToons, 'Trying to remove a suit, but has no active suits. Probably hacker related.')
        if self.luredSuits.count(suit) == 1:
            self.luredSuits.remove(suit)
        self.suitGone = 1
        del suit.battleTrap

    def __removeToon(self, toonId, userAborted=0):
        self.notify.debug('__removeToon(%d)' % toonId)
        if self.toons.count(toonId) == 0:
            return
        self.battleCalc.toonLeftBattle(toonId)
        self.__removeToonTasks(toonId)
        self.toons.remove(toonId)
        if self.joiningToons.count(toonId) == 1:
            self.joiningToons.remove(toonId)
        if self.pendingToons.count(toonId) == 1:
            self.pendingToons.remove(toonId)
        if self.activeToons.count(toonId) == 1:
            self.notify.debug('__removeToon(%d) - suitAttacks : %s' % (toonId, self.suitAttacks))
            activeToonIdx = self.activeToons.index(toonId)
            self.notify.debug('removing activeToons[%d], updating suitAttacks SUIT_HP_COL to match' % activeToonIdx)
            for i in range(len(self.suitAttacks)):
                if activeToonIdx < len(self.suitAttacks[i][SUIT_HP_COL]):
                    del self.suitAttacks[i][SUIT_HP_COL][activeToonIdx]
                    targetIndex = self.suitAttacks[i][SUIT_TGT_COL]
                    if targetIndex == activeToonIdx:
                        self.suitAttacks[i][SUIT_TGT_COL] = -1
                    elif targetIndex > activeToonIdx:
                        self.suitAttacks[i][SUIT_TGT_COL] = targetIndex - 1
                else:
                    self.notify.warning("suitAttacks %d doesn't have an HP column for active toon index %d" % (i, activeToonIdx))

            self.activeToons.remove(toonId)
        if self.runningToons.count(toonId) == 1:
            self.runningToons.remove(toonId)
        if self.adjustingToons.count(toonId) == 1:
            self.notify.warning('removeToon() - toon: %d was adjusting!' % toonId)
            self.adjustingToons.remove(toonId)
        self.toonGone = 1
        if toonId in self.pets:
            self.pets[toonId].requestDelete()
            del self.pets[toonId]
        self.__removeResponse(toonId)
        self.__removeAdjustingResponse(toonId)
        self.__removeJoinResponses(toonId)
        event = simbase.air.getAvatarExitEvent(toonId)
        self.avatarExitEvents.remove(event)
        self.ignore(event)
        event = 'inSafezone-%s' % toonId
        self.avatarExitEvents.remove(event)
        self.ignore(event)
        toon = simbase.air.doId2do.get(toonId)
        if toon:
            toon.b_setBattleId(0)
            messageToonReleased = 'Battle releasing toon %s' % toon.doId
            messenger.send(messageToonReleased, [toon.doId])
        if not userAborted:
            toon = self.getToon(toonId)
            if toon != None:
                toon.hpOwnedByBattle = 0
                toon.d_setHp(toon.hp)
                toon.d_setInventory(toon.inventory.makeNetString())
                self.air.cogPageManager.toonEncounteredCogs(toon, self.suitsEncountered, self.getTaskZoneId())
        else:
            if len(self.suits) > 0 and not self.streetBattle:
                self.notify.info('toon %d aborted non-street battle; clearing inventory and hp.' % toonId)
                toon = DistributedToonAI.DistributedToonAI(self.air)
                toon.doId = toonId
                empty = InventoryBase.InventoryBase(toon)
                toon.b_setInventory(empty.makeNetString())
                toon.b_setHp(0)
                db = DatabaseObject.DatabaseObject(self.air, toonId)
                db.storeObject(toon, ['setInventory', 'setHp'])
                self.notify.info('killing mem leak from temporary DistributedToonAI %d' % toonId)
                toon.deleteDummy()
        return

    def getToon(self, toonId):
        if toonId in self.air.doId2do:
            return self.air.doId2do[toonId]
        else:
            self.notify.warning('getToon() - toon: %d not in repository!' % toonId)
        return None

    def toonRequestRun(self):
        toonId = self.air.getAvatarIdFromSender()
        if self.ignoreResponses == 1:
            self.notify.debug('ignoring response from toon: %d' % toonId)
            return
        self.notify.debug('toonRequestRun(%d)' % toonId)
        if not self.isRunable():
            self.notify.warning('toonRequestRun() - not runable')
            return
        updateAttacks = 0
        if self.activeToons.count(toonId) == 0:
            self.notify.warning('toon tried to run, but not found in activeToons: %d' % toonId)
            return
        for toon in self.activeToons:
            if toon in self.toonAttacks:
                ta = self.toonAttacks[toon]
                track = ta[TOON_TRACK_COL]
                level = ta[TOON_LVL_COL]
                if ta[TOON_TGT_COL] == toonId or track == HEAL and attackAffectsGroup(track, level) and len(self.activeToons) <= 2:
                    healerId = ta[TOON_ID_COL]
                    self.notify.debug('resetting toon: %ds attack' % healerId)
                    self.toonAttacks[toon] = getToonAttack(toon, track=UN_ATTACK)
                    self.responses[healerId] = 0
                    updateAttacks = 1

        self.__makeToonRun(toonId, updateAttacks)
        self.d_setMembers()
        self.needAdjust = 1
        self.__requestAdjust()

    def toonRequestJoin(self, x, y, z):
        toonId = self.air.getAvatarIdFromSender()
        self.notify.debug('toonRequestJoin(%d)' % toonId)
        self.signupToon(toonId, x, y, z)

    def toonDied(self):
        toonId = self.air.getAvatarIdFromSender()
        self.notify.debug('toonDied(%d)' % toonId)
        if toonId in self.toons:
            toon = self.getToon(toonId)
            if toon:
                toon.hp = -1
                toon.inventory.zeroInv(1)
                self.__handleSuddenExit(toonId, 0)

    def signupToon(self, toonId, x, y, z):
        if self.toons.count(toonId):
            return
        if self.toonCanJoin():
            if self.addToon(toonId):
                self.__joinToon(toonId, Point3(x, y, z))
                self.d_setMembers()
        else:
            self.notify.warning('toonRequestJoin() - not joinable')
            self.d_denyLocalToonJoin(toonId)

    def d_denyLocalToonJoin(self, toonId):
        self.notify.debug('network: denyLocalToonJoin(%d)' % toonId)
        self.sendUpdateToAvatarId(toonId, 'denyLocalToonJoin', [])

    def resetResponses(self):
        self.responses = {}
        for t in self.toons:
            self.responses[t] = 0

        self.ignoreResponses = 0

    def allToonsResponded(self):
        for t in self.toons:
            if self.responses[t] == 0:
                return 0

        self.ignoreResponses = 1
        return 1

    def __allPendingActiveToonsResponded(self):
        for t in self.pendingToons + self.activeToons:
            if self.responses[t] == 0:
                return 0

        self.ignoreResponses = 1
        return 1

    def __allActiveToonsResponded(self):
        for t in self.activeToons:
            if self.responses[t] == 0:
                return 0

        self.ignoreResponses = 1
        return 1

    def __removeResponse(self, toonId):
        del self.responses[toonId]
        if self.ignoreResponses == 0 and len(self.toons) > 0:
            currStateName = self.fsm.getCurrentState().getName()
            if currStateName == 'WaitForInput':
                if self.__allActiveToonsResponded():
                    self.notify.debug('removeResponse() - dont wait for movie')
                    self.__requestMovie()
            elif currStateName == 'PlayMovie':
                if self.__allPendingActiveToonsResponded():
                    self.notify.debug('removeResponse() - surprise movie done')
                    self.__movieDone()
            elif currStateName == 'Reward' or currStateName == 'BuildingReward':
                if self.__allActiveToonsResponded():
                    self.notify.debug('removeResponse() - surprise reward done')
                    self.handleRewardDone()

    def __resetAdjustingResponses(self):
        self.adjustingResponses = {}
        for t in self.toons:
            self.adjustingResponses[t] = 0

        self.ignoreAdjustingResponses = 0

    def __allAdjustingToonsResponded(self):
        for t in self.toons:
            if self.adjustingResponses[t] == 0:
                return 0

        self.ignoreAdjustingResponses = 1
        return 1

    def __removeAdjustingResponse(self, toonId):
        if toonId in self.adjustingResponses:
            del self.adjustingResponses[toonId]
            if self.ignoreAdjustingResponses == 0 and len(self.toons) > 0:
                if self.__allAdjustingToonsResponded():
                    self.__adjustDone()

    def __addJoinResponse(self, avId, taskName, toon=0):
        if toon == 1:
            for jr in list(self.joinResponses.values()):
                jr[avId] = 0

        self.joinResponses[avId] = {}
        for t in self.toons:
            self.joinResponses[avId][t] = 0

        self.joinResponses[avId]['taskName'] = taskName

    def __removeJoinResponses(self, avId):
        self.__removeJoinResponse(avId)
        removedOne = 0
        for j in list(self.joinResponses.values()):
            if avId in j:
                del j[avId]
                removedOne = 1

        if removedOne == 1:
            for t in self.joiningToons:
                if self.__allToonsRespondedJoin(t):
                    self.__makeAvPending(t)

    def __removeJoinResponse(self, avId):
        if avId in self.joinResponses:
            taskMgr.remove(self.joinResponses[avId]['taskName'])
            del self.joinResponses[avId]

    def __allToonsRespondedJoin(self, avId):
        jr = self.joinResponses[avId]
        for t in self.toons:
            if jr[t] == 0:
                return 0

        return 1

    def __cleanupJoinResponses(self):
        for jr in list(self.joinResponses.values()):
            taskMgr.remove(jr['taskName'])
            del jr

    def adjustDone(self):
        toonId = self.air.getAvatarIdFromSender()
        if self.ignoreAdjustingResponses == 1:
            self.notify.debug('adjustDone() - ignoring toon: %d' % toonId)
            return
        else:
            if self.adjustFsm.getCurrentState().getName() != 'Adjusting':
                self.notify.warning('adjustDone() - in state %s' % self.fsm.getCurrentState().getName())
                return
            else:
                if self.toons.count(toonId) == 0:
                    self.notify.warning('adjustDone() - toon: %d not in toon list' % toonId)
                    return
        self.adjustingResponses[toonId] += 1
        self.notify.debug('toon: %d done adjusting' % toonId)
        if self.__allAdjustingToonsResponded():
            self.__adjustDone()

    def timeout(self):
        toonId = self.air.getAvatarIdFromSender()
        if self.ignoreResponses == 1:
            self.notify.debug('timeout() - ignoring toon: %d' % toonId)
            return
        else:
            if self.fsm.getCurrentState().getName() != 'WaitForInput':
                self.notify.warning('timeout() - in state: %s' % self.fsm.getCurrentState().getName())
                return
            else:
                if self.toons.count(toonId) == 0:
                    self.notify.warning('timeout() - toon: %d not in toon list' % toonId)
                    return
        self.toonAttacks[toonId] = getToonAttack(toonId)
        self.d_setChosenToonAttacks()
        self.responses[toonId] += 1
        self.notify.debug('toon: %d timed out' % toonId)
        if self.__allActiveToonsResponded():
            self.__requestMovie(timeout=1)

    def movieDone(self):
        toonId = self.air.getAvatarIdFromSender()
        if self.ignoreResponses == 1:
            self.notify.debug('movieDone() - ignoring toon: %d' % toonId)
            return
        else:
            if self.fsm.getCurrentState().getName() != 'PlayMovie':
                self.notify.warning('movieDone() - in state %s' % self.fsm.getCurrentState().getName())
                return
            else:
                if self.toons.count(toonId) == 0:
                    self.notify.warning('movieDone() - toon: %d not in toon list' % toonId)
                    return
        self.responses[toonId] += 1
        self.notify.debug('toon: %d done with movie' % toonId)
        if self.__allPendingActiveToonsResponded():
            self.__movieDone()
        else:
            self.timer.stop()
            self.timer.startCallback(TIMEOUT_PER_USER, self.__serverMovieDone)

    def rewardDone(self):
        toonId = self.air.getAvatarIdFromSender()
        stateName = self.fsm.getCurrentState().getName()
        if self.ignoreResponses == 1:
            self.notify.debug('rewardDone() - ignoring toon: %d' % toonId)
            return
        else:
            if stateName not in ('Reward', 'BuildingReward', 'FactoryReward', 'MintReward',
                                 'StageReward', 'CountryClubReward'):
                self.notify.warning('rewardDone() - in state %s' % stateName)
                return
            else:
                if self.toons.count(toonId) == 0:
                    self.notify.warning('rewardDone() - toon: %d not in toon list' % toonId)
                    return
        self.responses[toonId] += 1
        self.notify.debug('toon: %d done with reward' % toonId)
        if self.__allActiveToonsResponded():
            self.handleRewardDone()
        else:
            self.timer.stop()
            self.timer.startCallback(TIMEOUT_PER_USER, self.serverRewardDone)

    def assignRewards(self):
        if self.rewardHasPlayed == 1:
            self.notify.debug('handleRewardDone() - reward has already played')
            return
        self.rewardHasPlayed = 1
        BattleExperienceAI.assignRewards(self.activeToons, self.battleCalc.toonSkillPtsGained, self.suitsKilled, self.getTaskZoneId(), self.helpfulToons)

    def joinDone(self, avId):
        toonId = self.air.getAvatarIdFromSender()
        if self.toons.count(toonId) == 0:
            self.notify.warning('joinDone() - toon: %d not in toon list' % toonId)
            return
        if avId not in self.joinResponses:
            self.notify.debug('joinDone() - no entry for: %d - ignoring: %d' % (avId, toonId))
            return
        jr = self.joinResponses[avId]
        if toonId in jr:
            jr[toonId] += 1
        self.notify.debug('client with localToon: %d done joining av: %d' % (toonId, avId))
        if self.__allToonsRespondedJoin(avId):
            self.__makeAvPending(avId)

    def requestAttack(self, track, level, av):
        toonId = self.air.getAvatarIdFromSender()
        if self.ignoreResponses == 1:
            self.notify.debug('requestAttack() - ignoring toon: %d' % toonId)
            return
        else:
            if self.fsm.getCurrentState().getName() != 'WaitForInput':
                self.notify.warning('requestAttack() - in state: %s' % self.fsm.getCurrentState().getName())
                return
            else:
                if self.activeToons.count(toonId) == 0:
                    self.notify.warning('requestAttack() - toon: %d not in toon list' % toonId)
                    return
        self.notify.debug('requestAttack(%d, %d, %d, %d)' % (toonId, track, level, av))
        toon = self.getToon(toonId)
        if toon == None:
            self.notify.warning('requestAttack() - no toon: %d' % toonId)
            return
        validResponse = 1
        if toon.getGameAccess() != ToontownGlobals.AccessFull:
            if track in [HEAL, TRAP, LURE, SOUND, THROW, SQUIRT, DROP] and gagIsPaidOnly(track, level):
                self.air.writeServerEvent('suspicious', toonId, 'requestAttack: non-paid player requesting attack with paid gag')
                return

        if track == SOS:
            self.notify.debug('toon: %d calls for help' % toonId)
            self.air.writeServerEvent('friendSOS', toonId, '%s' % av)
            self.toonAttacks[toonId] = getToonAttack(toonId, track=SOS, target=av)
        elif track == NPCSOS:
            self.notify.debug('toon: %d calls for help' % toonId)
            self.air.writeServerEvent('NPCSOS', toonId, '%s' % av)
            toon = self.getToon(toonId)
            if toon == None:
                return
            if av in toon.NPCFriendsDict:
                npcCollision = 0
                if av in self.npcAttacks:
                    callingToon = self.npcAttacks[av]
                    if self.activeToons.count(callingToon) == 1:
                        self.toonAttacks[toonId] = getToonAttack(toonId, track=PASS)
                        npcCollision = 1
                if npcCollision == 0:
                    self.toonAttacks[toonId] = getToonAttack(toonId, track=NPCSOS, level=5, target=av)
                    self.numNPCAttacks += 1
                    self.npcAttacks[av] = toonId
        elif track == PETSOS:
            self.notify.debug('toon: %d calls for pet: %d' % (toonId, av))
            self.air.writeServerEvent('PETSOS', toonId, '%s' % av)
            toon = self.getToon(toonId)
            if toon == None:
                return
            if not self.validate(toonId, level in toon.petTrickPhrases, 'requestAttack: invalid pet trickId: %s' % level):
                return
            self.toonAttacks[toonId] = getToonAttack(toonId, track=PETSOS, level=level, target=av)
        elif track == UN_ATTACK:
            self.notify.debug('toon: %d changed its mind' % toonId)
            self.toonAttacks[toonId] = getToonAttack(toonId, track=UN_ATTACK)
            if toonId in self.responses:
                self.responses[toonId] = 0
            validResponse = 0
        elif track == PASS:
            self.toonAttacks[toonId] = getToonAttack(toonId, track=PASS)
        elif track == FIRE:
            self.toonAttacks[toonId] = getToonAttack(toonId, track=FIRE, target=av)
        else:
            if not self.validate(toonId, track >= 0 and track <= MAX_TRACK_INDEX, 'requestAttack: invalid track %s' % track):
                return
            if not self.validate(toonId, level >= 0 and level <= MAX_LEVEL_INDEX, 'requestAttack: invalid level %s' % level):
                return
            if toon.inventory.numItem(track, level) == 0:
                self.notify.warning('requestAttack() - toon has no item track:                     %d level: %d' % (track, level))
                self.toonAttacks[toonId] = getToonAttack(toonId)
                return
            if track == HEAL:
                if self.runningToons.count(av) == 1 or attackAffectsGroup(track, level) and len(self.activeToons) < 2:
                    self.toonAttacks[toonId] = getToonAttack(toonId, track=UN_ATTACK)
                    validResponse = 0
                else:
                    self.toonAttacks[toonId] = getToonAttack(toonId, track=track, level=level, target=av)
            else:
                self.toonAttacks[toonId] = getToonAttack(toonId, track=track, level=level, target=av)
                if av == -1 and not attackAffectsGroup(track, level):
                    validResponse = 0
        self.d_setChosenToonAttacks()
        if validResponse == 1:
            self.responses[toonId] += 1
        self.notify.debug('toon: %d chose an attack' % toonId)
        if self.__allActiveToonsResponded():
            self.__requestMovie()
        return

    def requestPetProxy(self, av):
        toonId = self.air.getAvatarIdFromSender()
        if self.ignoreResponses == 1:
            self.notify.debug('requestPetProxy() - ignoring toon: %d' % toonId)
            return
        else:
            if self.fsm.getCurrentState().getName() != 'WaitForInput':
                self.notify.warning('requestPetProxy() - in state: %s' % self.fsm.getCurrentState().getName())
                return
            else:
                if self.activeToons.count(toonId) == 0:
                    self.notify.warning('requestPetProxy() - toon: %d not in toon list' % toonId)
                    return
        self.notify.debug('requestPetProxy(%s, %s)' % (toonId, av))
        toon = self.getToon(toonId)
        if toon == None:
            self.notify.warning('requestPetProxy() - no toon: %d' % toonId)
            return
        petId = toon.getPetId()
        zoneId = self.zoneId
        if petId == av:
            if toonId not in self.pets:

                def handleGetPetProxy(success, petProxy, petId=petId, zoneId=zoneId, toonId=toonId):
                    if success:
                        if petId not in simbase.air.doId2do:
                            simbase.air.requestDeleteDoId(petId)
                        else:
                            petDO = simbase.air.doId2do[petId]
                            petDO.requestDelete()
                            simbase.air.deleteDistObject(petDO)
                        petProxy.dbObject = 1
                        petProxy.generateWithRequiredAndId(petId, self.air.districtId, zoneId)
                        petProxy.broadcastDominantMood()
                        self.pets[toonId] = petProxy
                    else:
                        self.notify.warning('error generating petProxy: %s' % petId)

                self.getPetProxyObject(petId, handleGetPetProxy)
        return

    def suitCanJoin(self):
        return len(self.suits) < self.maxSuits and self.isJoinable()

    def toonCanJoin(self):
        return len(self.toons) < 4 and self.isJoinable()

    def __requestMovie(self, timeout=0):
        if self.adjustFsm.getCurrentState().getName() == 'Adjusting':
            self.notify.debug('__requestMovie() - in Adjusting')
            self.movieRequested = 1
        else:
            movieDelay = 0
            if len(self.activeToons) == 0:
                self.notify.warning('only pending toons left in battle %s, toons = %s' % (self.doId, self.toons))
            else:
                if len(self.activeSuits) == 0:
                    self.notify.warning('only pending suits left in battle %s, suits = %s' % (self.doId, self.suits))
                else:
                    if len(self.activeToons) > 1 and not timeout:
                        movieDelay = 1
            self.fsm.request('MakeMovie')
            if movieDelay:
                taskMgr.doMethodLater(0.8, self.__makeMovie, self.uniqueName('make-movie'))
                self.taskNames.append(self.uniqueName('make-movie'))
            else:
                self.__makeMovie()

    def __makeMovie(self, task=None):
        self.notify.debug('makeMovie()')
        if self._DOAI_requestedDelete:
            self.notify.warning('battle %s requested delete, then __makeMovie was called!' % self.doId)
            if hasattr(self, 'levelDoId'):
                self.notify.warning('battle %s in level %s' % (self.doId, self.levelDoId))
            return
        self.__removeTaskName(self.uniqueName('make-movie'))
        if self.movieHasBeenMade == 1:
            self.notify.debug('__makeMovie() - movie has already been made')
            return
        self.movieRequested = 0
        self.movieHasBeenMade = 1
        self.movieHasPlayed = 0
        self.rewardHasPlayed = 0
        for t in self.activeToons:
            if t not in self.toonAttacks:
                self.toonAttacks[t] = getToonAttack(t)
            attack = self.toonAttacks[t]
            if attack[TOON_TRACK_COL] == PASS or attack[TOON_TRACK_COL] == UN_ATTACK:
                self.toonAttacks[t] = getToonAttack(t)
            if self.toonAttacks[t][TOON_TRACK_COL] != NO_ATTACK:
                self.addHelpfulToon(t)

        self.battleCalc.calculateRound()
        for t in self.activeToons:
            self.sendEarnedExperience(t)
            toon = self.getToon(t)
            if toon != None:
                toon.hpOwnedByBattle = 1
                if toon.immortalMode:
                    toon.toonUp(toon.maxHp)

        self.d_setMovie()
        self.b_setState('PlayMovie')
        return Task.done

    def sendEarnedExperience(self, toonId):
        toon = self.getToon(toonId)
        if toon != None:
            expList = self.battleCalc.toonSkillPtsGained.get(toonId, None)
            if expList == None:
                toon.d_setEarnedExperience([])
            else:
                roundList = []
                for exp in expList:
                    roundList.append(int(exp + 0.5))

                toon.d_setEarnedExperience(roundList)
        return

    def enterOff(self):
        return None

    def exitOff(self):
        return None

    def enterFaceOff(self):
        return None

    def exitFaceOff(self):
        return None

    def enterWaitForJoin(self):
        self.notify.debug('enterWaitForJoin()')
        if len(self.activeSuits) > 0:
            self.b_setState('WaitForInput')
        else:
            self.notify.debug('enterWaitForJoin() - no active suits')
            self.runableFsm.request('Runable')
            self.resetResponses()
            self.__requestAdjust()
        return None

    def exitWaitForJoin(self):
        return None

    def enterWaitForInput(self):
        self.notify.debug('enterWaitForInput()')
        self.joinableFsm.request('Joinable')
        self.runableFsm.request('Runable')
        self.resetResponses()
        self.__requestAdjust()
        if not self.tutorialFlag:
            self.timer.startCallback(SERVER_INPUT_TIMEOUT, self.__serverTimedOut)
        self.npcAttacks = {}
        for toonId in self.toons:
            if bboard.get('autoRestock-%s' % toonId, False):
                toon = self.air.doId2do.get(toonId)
                if toon is not None:
                    toon.doRestock(0)

        return None

    def exitWaitForInput(self):
        self.npcAttacks = {}
        self.timer.stop()
        return None

    def __serverTimedOut(self):
        self.notify.debug('wait for input timed out on server')
        self.ignoreResponses = 1
        self.__requestMovie(timeout=1)

    def enterMakeMovie(self):
        self.notify.debug('enterMakeMovie()')
        self.runableFsm.request('Unrunable')
        self.resetResponses()
        return None

    def exitMakeMovie(self):
        return None

    def enterPlayMovie(self):
        self.notify.debug('enterPlayMovie()')
        self.joinableFsm.request('Joinable')
        self.runableFsm.request('Unrunable')
        self.resetResponses()
        movieTime = TOON_ATTACK_TIME * (len(self.activeToons) + self.numNPCAttacks) + SUIT_ATTACK_TIME * len(self.activeSuits) + SERVER_BUFFER_TIME
        self.numNPCAttacks = 0
        self.notify.debug('estimated upper bound of movie time: %f' % movieTime)
        self.timer.startCallback(movieTime, self.__serverMovieDone)

    def __serverMovieDone(self):
        self.notify.debug('movie timed out on server')
        self.ignoreResponses = 1
        self.__movieDone()

    def serverRewardDone(self):
        self.notify.debug('reward timed out on server')
        self.ignoreResponses = 1
        self.handleRewardDone()

    def handleRewardDone(self):
        self.b_setState('Resume')

    def exitPlayMovie(self):
        self.timer.stop()
        return None

    def __movieDone(self):
        self.notify.debug('__movieDone() - movie is finished')
        if self.movieHasPlayed == 1:
            self.notify.debug('__movieDone() - movie had already finished')
            return
        self.movieHasBeenMade = 0
        self.movieHasPlayed = 1
        self.ignoreResponses = 1
        needUpdate = 0
        toonHpDict = {}
        for toon in self.activeToons:
            toonHpDict[toon] = [0, 0, 0]
            actualToon = self.getToon(toon)
            self.notify.debug('BEFORE ROUND: toon: %d hp: %d' % (toon, actualToon.hp))

        deadSuits = []
        trapDict = {}
        suitsLuredOntoTraps = []
        npcTrapAttacks = []
        for activeToon in self.activeToons + self.exitedToons:
            if activeToon in self.toonAttacks:
                attack = self.toonAttacks[activeToon]
                track = attack[TOON_TRACK_COL]
                npc_level = None
                if track == NPCSOS:
                    track, npc_level, npc_hp = NPCToons.getNPCTrackLevelHp(attack[TOON_TGT_COL])
                    if track == None:
                        track = NPCSOS
                    elif track == TRAP:
                        npcTrapAttacks.append(attack)
                        toon = self.getToon(attack[TOON_ID_COL])
                        av = attack[TOON_TGT_COL]
                        if toon:
                            toon.attemptSubtractNPCFriend(av)
                        continue
                if track != NO_ATTACK:
                    toonId = attack[TOON_ID_COL]
                    level = attack[TOON_LVL_COL]
                    if npc_level != None:
                        level = npc_level
                    if attack[TOON_TRACK_COL] == NPCSOS:
                        toon = self.getToon(toonId)
                        av = attack[TOON_TGT_COL]
                        if toon:
                            toon.attemptSubtractNPCFriend(av)
                    elif track == PETSOS:
                        pass
                    elif track == FIRE:
                        pass
                    elif track != SOS:
                        toon = self.getToon(toonId)
                        if toon != None:
                            check = toon.inventory.useItem(track, level)
                            if check == -1:
                                self.air.writeServerEvent('suspicious', toonId, 'Toon generating movie for non-existant gag track %s level %s' % (track, level))
                                self.notify.warning('generating movie for non-existant gag track %s level %s! avId: %s' % (track, level, toonId))
                            if not toon.hasTrackAccess(track):
                                self.air.writeServerEvent('suspicious', toonId, 'Toon trying to throw gag on track they do not have access to (gag track %s level %s)' % (track, level))
                            toon.d_setInventory(toon.inventory.makeNetString())
                    hps = attack[TOON_HP_COL]
                    if track == SOS:
                        self.notify.debug('toon: %d called for help' % toonId)
                    elif track == NPCSOS:
                        self.notify.debug('toon: %d called for help' % toonId)
                    elif track == PETSOS:
                        self.notify.debug('toon: %d called for pet' % toonId)
                        for i in range(len(self.activeToons)):
                            toon = self.getToon(self.activeToons[i])
                            if toon != None:
                                if i < len(hps):
                                    hp = hps[i]
                                    if hp > 0:
                                        toonHpDict[toon.doId][0] += hp
                                    self.notify.debug('pet heal: toon: %d healed for hp: %d' % (toon.doId, hp))
                                else:
                                    self.notify.warning('Invalid targetIndex %s in hps %s.' % (i, hps))

                    elif track == NPC_RESTOCK_GAGS:
                        for at in self.activeToons:
                            toon = self.getToon(at)
                            if toon != None:
                                toon.inventory.NPCMaxOutInv(npc_level)
                                toon.d_setInventory(toon.inventory.makeNetString())

                    elif track == HEAL:
                        if levelAffectsGroup(HEAL, level):
                            for i in range(len(self.activeToons)):
                                at = self.activeToons[i]
                                if at != toonId or attack[TOON_TRACK_COL] == NPCSOS:
                                    toon = self.getToon(at)
                                    if toon != None:
                                        if i < len(hps):
                                            hp = hps[i]
                                        else:
                                            self.notify.warning('Invalid targetIndex %s in hps %s.' % (i, hps))
                                            hp = 0
                                        toonHpDict[toon.doId][0] += hp
                                        self.notify.debug('HEAL: toon: %d healed for hp: %d' % (toon.doId, hp))

                        else:
                            targetId = attack[TOON_TGT_COL]
                            toon = self.getToon(targetId)
                            if toon != None and targetId in self.activeToons:
                                targetIndex = self.activeToons.index(targetId)
                                if targetIndex < len(hps):
                                    hp = hps[targetIndex]
                                else:
                                    self.notify.warning('Invalid targetIndex %s in hps %s.' % (targetIndex, hps))
                                    hp = 0
                                toonHpDict[toon.doId][0] += hp
                    elif attackAffectsGroup(track, level, attack[TOON_TRACK_COL]):
                        for suit in self.activeSuits:
                            targetIndex = self.activeSuits.index(suit)
                            if targetIndex < 0 or targetIndex >= len(hps):
                                self.notify.warning('Got attack (%s, %s) on target suit %s, but hps has only %s entries: %s' % (track,
                                 level,
                                 targetIndex,
                                 len(hps),
                                 hps))
                            else:
                                hp = hps[targetIndex]
                                if hp > 0 and track == LURE:
                                    if suit.battleTrap == UBER_GAG_LEVEL_INDEX:
                                        pass
                                    suit.battleTrap = NO_TRAP
                                    needUpdate = 1
                                    if suit.doId in trapDict:
                                        del trapDict[suit.doId]
                                    if suitsLuredOntoTraps.count(suit) == 0:
                                        suitsLuredOntoTraps.append(suit)
                                if track == TRAP:
                                    targetId = suit.doId
                                    if targetId in trapDict:
                                        trapDict[targetId].append(attack)
                                    else:
                                        trapDict[targetId] = [attack]
                                    needUpdate = 1
                                died = attack[SUIT_DIED_COL] & 1 << targetIndex
                                if died != 0:
                                    if deadSuits.count(suit) == 0:
                                        deadSuits.append(suit)

                    else:
                        targetId = attack[TOON_TGT_COL]
                        target = self.findSuit(targetId)
                        if target != None:
                            targetIndex = self.activeSuits.index(target)
                            if targetIndex < 0 or targetIndex >= len(hps):
                                self.notify.warning('Got attack (%s, %s) on target suit %s, but hps has only %s entries: %s' % (track,
                                 level,
                                 targetIndex,
                                 len(hps),
                                 hps))
                            else:
                                hp = hps[targetIndex]
                                if track == TRAP:
                                    if targetId in trapDict:
                                        trapDict[targetId].append(attack)
                                    else:
                                        trapDict[targetId] = [attack]
                                if hp > 0 and track == LURE:
                                    oldBattleTrap = target.battleTrap
                                    if oldBattleTrap == UBER_GAG_LEVEL_INDEX:
                                        pass
                                    target.battleTrap = NO_TRAP
                                    needUpdate = 1
                                    if target.doId in trapDict:
                                        del trapDict[target.doId]
                                    if suitsLuredOntoTraps.count(target) == 0:
                                        suitsLuredOntoTraps.append(target)
                                    if oldBattleTrap == UBER_GAG_LEVEL_INDEX:
                                        for otherSuit in self.activeSuits:
                                            if not otherSuit == target:
                                                otherSuit.battleTrap = NO_TRAP
                                                if otherSuit.doId in trapDict:
                                                    del trapDict[otherSuit.doId]

                                died = attack[SUIT_DIED_COL] & 1 << targetIndex
                                if died != 0:
                                    if deadSuits.count(target) == 0:
                                        deadSuits.append(target)

        self.exitedToons = []
        for suitKey in list(trapDict.keys()):
            attackList = trapDict[suitKey]
            attack = attackList[0]
            target = self.findSuit(attack[TOON_TGT_COL])
            if attack[TOON_LVL_COL] == UBER_GAG_LEVEL_INDEX:
                targetId = suitKey
                target = self.findSuit(targetId)
            if len(attackList) == 1:
                if suitsLuredOntoTraps.count(target) == 0:
                    self.notify.debug('movieDone() - trap set')
                    target.battleTrap = attack[TOON_LVL_COL]
                    needUpdate = 1
                else:
                    target.battleTrap = NO_TRAP
            else:
                self.notify.debug('movieDone() - traps collided')
                if target != None:
                    target.battleTrap = NO_TRAP

        if self.battleCalc.trainTrapTriggered:
            self.notify.debug('Train trap triggered, clearing all traps')
            for otherSuit in self.activeSuits:
                self.notify.debug('suit =%d, oldBattleTrap=%d' % (otherSuit.doId, otherSuit.battleTrap))
                otherSuit.battleTrap = NO_TRAP

        currLuredSuits = self.battleCalc.getLuredSuits()
        if len(self.luredSuits) == len(currLuredSuits):
            for suit in self.luredSuits:
                if currLuredSuits.count(suit.doId) == 0:
                    needUpdate = 1
                    break

        else:
            needUpdate = 1
        self.luredSuits = []
        for i in currLuredSuits:
            suit = self.air.doId2do[i]
            self.luredSuits.append(suit)
            self.notify.debug('movieDone() - suit: %d is lured' % i)

        for attack in npcTrapAttacks:
            track, level, hp = NPCToons.getNPCTrackLevelHp(attack[TOON_TGT_COL])
            for suit in self.activeSuits:
                if self.luredSuits.count(suit) == 0 and suit.battleTrap == NO_TRAP:
                    suit.battleTrap = level

            needUpdate = 1

        for suit in deadSuits:
            self.notify.debug('removing dead suit: %d' % suit.doId)
            if suit.isDeleted():
                self.notify.debug('whoops, suit %d is deleted.' % suit.doId)
            else:
                self.notify.debug('suit had revives? %d' % suit.getMaxSkeleRevives())
                encounter = {'type': suit.dna.name,
                 'level': suit.getActualLevel(),
                 'track': suit.dna.dept,
                 'isSkelecog': suit.getSkelecog(),
                 'isForeman': suit.isForeman(),
                 'isVP': 0,
                 'isCFO': 0,
                 'isSupervisor': suit.isSupervisor(),
                 'isVirtual': suit.isVirtual(),
                 'hasRevives': suit.getMaxSkeleRevives(),
                 'activeToons': self.activeToons[:]}
                self.suitsKilled.append(encounter)
                self.suitsKilledThisBattle.append(encounter)
            self.__removeSuit(suit)
            needUpdate = 1
            suit.resume()

        lastActiveSuitDied = 0
        if len(self.activeSuits) == 0 and len(self.pendingSuits) == 0:
            lastActiveSuitDied = 1
        self.notify.debug('calculate hit points, %s' % self.suitAttacks)
        for i in range(4):
            attack = self.suitAttacks[i][SUIT_ATK_COL]
            if attack != NO_ATTACK:
                suitId = self.suitAttacks[i][SUIT_ID_COL]
                suit = self.findSuit(suitId)
                if suit == None:
                    self.notify.warning('movieDone() - suit: %d is gone!' % suitId)
                    continue
                if not (hasattr(suit, 'dna') and suit.dna):
                    toonId = self.air.getAvatarIdFromSender()
                    self.notify.warning('_movieDone avoiding crash, sender=%s but suit has no dna' % toonId)
                    self.air.writeServerEvent('suspicious', toonId, '_movieDone avoiding crash, suit has no dna')
                    continue
                adict = getSuitAttack(suit.getStyleName(), suit.getLevel(), attack)
                hps = self.suitAttacks[i][SUIT_HP_COL]
                if adict['group'] == ATK_TGT_GROUP:
                    for activeToon in self.activeToons:
                        toon = self.getToon(activeToon)
                        if toon != None:
                            targetIndex = self.activeToons.index(activeToon)
                            toonDied = self.suitAttacks[i][TOON_DIED_COL] & 1 << targetIndex
                            if targetIndex >= len(hps):
                                self.notify.warning('DAMAGE GRP: toon %s is no longer in battle!' % activeToon)
                            else:
                                hp = hps[targetIndex]
                                if hp > 0:
                                    self.notify.debug('DAMAGE GRP: toon: %d hit for dmg: %d' % (activeToon, hp))
                                    if toonDied != 0:
                                        toonHpDict[toon.doId][2] = 1
                                    toonHpDict[toon.doId][1] += hp

                elif adict['group'] == ATK_TGT_SINGLE:
                    targetIndex = self.suitAttacks[i][SUIT_TGT_COL]
                    if targetIndex >= len(self.activeToons):
                        self.notify.warning('movieDone() - toon: %d gone!' % targetIndex)
                        break
                    if targetIndex < 0:
                        self.notify.warning('movieDone() - target index is for an already gone toon!')
                        continue
                    toonId = self.activeToons[targetIndex]
                    toon = self.getToon(toonId)
                    toonDied = self.suitAttacks[i][TOON_DIED_COL] & 1 << targetIndex
                    if targetIndex >= len(hps):
                        self.notify.warning('DAMAGE SGL: toon %s is no longer in battle!' % toonId)
                    else:
                        hp = hps[targetIndex]
                        if hp > 0:
                            self.notify.debug('DAMAGE SGL: toon: %d hit for dmg: %d' % (toonId, hp))
                            if toonDied != 0:
                                toonHpDict[toon.doId][2] = 1
                            toonHpDict[toon.doId][1] += hp

        deadToons = []
        for activeToon in self.activeToons:
            hp = toonHpDict[activeToon]
            toon = self.getToon(activeToon)
            if toon != None:
                self.notify.debug('AFTER ROUND: currtoonHP: %d toonMAX: %d hheal: %d damage: %d' % (toon.hp,
                 toon.maxHp,
                 hp[0],
                 hp[1]))
                toon.hpOwnedByBattle = 0
                hpDelta = hp[0] - hp[1]
                if hpDelta >= 0:
                    toon.toonUp(hpDelta, quietly=1)
                else:
                    toon.takeDamage(-hpDelta, quietly=1)
                if toon.hp <= 0:
                    self.notify.debug('movieDone() - toon: %d was killed' % activeToon)
                    toon.inventory.zeroInv(1)
                    deadToons.append(activeToon)
                self.notify.debug('AFTER ROUND: toon: %d setHp: %d' % (toon.doId, toon.hp))

        for deadToon in deadToons:
            self.__removeToon(deadToon)
            needUpdate = 1

        self.clearAttacks()
        self.d_setMovie()
        self.d_setChosenToonAttacks()
        self.localMovieDone(needUpdate, deadToons, deadSuits, lastActiveSuitDied)
        return

    def enterResume(self):
        for suit in self.suits:
            self.notify.info('battle done, resuming suit: %d' % suit.doId)
            if suit.isDeleted():
                self.notify.info('whoops, suit %d is deleted.' % suit.doId)
            else:
                suit.resume()

        self.suits = []
        self.joiningSuits = []
        self.pendingSuits = []
        self.adjustingSuits = []
        self.activeSuits = []
        self.luredSuits = []
        for toonId in self.toons:
            toon = simbase.air.doId2do.get(toonId)
            if toon:
                toon.b_setBattleId(0)
                messageToonReleased = 'Battle releasing toon %s' % toon.doId
                messenger.send(messageToonReleased, [toon.doId])

        for exitEvent in self.avatarExitEvents:
            self.ignore(exitEvent)

        eventMsg = {}
        for encounter in self.suitsKilledThisBattle:
            cog = encounter['type']
            level = encounter['level']
            msgName = '%s%s' % (cog, level)
            if encounter['isSkelecog']:
                msgName += '+'
            if msgName in eventMsg:
                eventMsg[msgName] += 1
            else:
                eventMsg[msgName] = 1

        msgText = ''
        for msgName, count in list(eventMsg.items()):
            if msgText != '':
                msgText += ','
            msgText += '%s%s' % (count, msgName)

        self.air.writeServerEvent('battleCogsDefeated', self.doId, '%s|%s' % (msgText, self.getTaskZoneId()))

    def exitResume(self):
        pass

    def isJoinable(self):
        return self.joinableFsm.getCurrentState().getName() == 'Joinable'

    def enterJoinable(self):
        self.notify.debug('enterJoinable()')
        return None

    def exitJoinable(self):
        return None

    def enterUnjoinable(self):
        self.notify.debug('enterUnjoinable()')
        return None

    def exitUnjoinable(self):
        return None

    def isRunable(self):
        return self.runableFsm.getCurrentState().getName() == 'Runable'

    def enterRunable(self):
        self.notify.debug('enterRunable()')
        return None

    def exitRunable(self):
        return None

    def enterUnrunable(self):
        self.notify.debug('enterUnrunable()')
        return None

    def exitUnrunable(self):
        return None

    def __estimateAdjustTime(self):
        self.needAdjust = 0
        adjustTime = 0
        if len(self.pendingSuits) > 0 or self.suitGone == 1:
            self.suitGone = 0
            pos0 = self.suitPendingPoints[0][0]
            pos1 = self.suitPoints[0][0][0]
            adjustTime = self.calcSuitMoveTime(pos0, pos1)
        if len(self.pendingToons) > 0 or self.toonGone == 1:
            self.toonGone = 0
            if adjustTime == 0:
                pos0 = self.toonPendingPoints[0][0]
                pos1 = self.toonPoints[0][0][0]
                adjustTime = self.calcToonMoveTime(pos0, pos1)
        return adjustTime

    def enterAdjusting(self):
        self.notify.debug('enterAdjusting()')
        self.timer.stop()
        self.__resetAdjustingResponses()
        self.adjustingTimer.startCallback(self.__estimateAdjustTime() + SERVER_BUFFER_TIME, self.__serverAdjustingDone)
        return None

    def __serverAdjustingDone(self):
        if self.needAdjust == 1:
            self.adjustFsm.request('NotAdjusting')
            self.__requestAdjust()
        else:
            self.notify.debug('adjusting timed out on the server')
            self.ignoreAdjustingResponses = 1
            self.__adjustDone()

    def exitAdjusting(self):
        currStateName = self.fsm.getCurrentState().getName()
        if currStateName == 'WaitForInput':
            self.timer.restart()
        else:
            if currStateName == 'WaitForJoin':
                self.b_setState('WaitForInput')
        self.adjustingTimer.stop()
        return None

    def __addTrainTrapForNewSuits(self):
        hasTrainTrap = False
        trapInfo = None
        for otherSuit in self.activeSuits:
            if otherSuit.battleTrap == UBER_GAG_LEVEL_INDEX:
                hasTrainTrap = True

        if hasTrainTrap:
            for curSuit in self.activeSuits:
                if not curSuit.battleTrap == UBER_GAG_LEVEL_INDEX:
                    oldBattleTrap = curSuit.battleTrap
                    curSuit.battleTrap = UBER_GAG_LEVEL_INDEX
                    self.battleCalc.addTrainTrapForJoiningSuit(curSuit.doId)
                    self.notify.debug('setting traintrack trap for joining suit %d oldTrap=%s' % (curSuit.doId, oldBattleTrap))

        return

    def __adjustDone(self):
        for s in self.adjustingSuits:
            self.pendingSuits.remove(s)
            self.activeSuits.append(s)

        self.adjustingSuits = []
        for toon in self.adjustingToons:
            if self.pendingToons.count(toon) == 1:
                self.pendingToons.remove(toon)
            else:
                self.notify.warning('adjustDone() - toon: %d not pending!' % toon.doId)
            if self.activeToons.count(toon) == 0:
                self.activeToons.append(toon)
                self.ignoreResponses = 0
                self.sendEarnedExperience(toon)
            else:
                self.notify.warning('adjustDone() - toon: %d already active!' % toon.doId)

        self.adjustingToons = []
        self.__addTrainTrapForNewSuits()
        self.d_setMembers()
        self.adjustFsm.request('NotAdjusting')
        if self.needAdjust == 1:
            self.notify.debug('__adjustDone() - need to adjust again')
            self.__requestAdjust()

    def enterNotAdjusting(self):
        self.notify.debug('enterNotAdjusting()')
        if self.movieRequested == 1:
            if len(self.activeToons) > 0 and self.__allActiveToonsResponded():
                self.__requestMovie()
        return None

    def exitNotAdjusting(self):
        return None

    def getPetProxyObject(self, petId, callback):
        doneEvent = 'readPet-%s' % self._getNextSerialNum()
        dbo = DatabaseObject.DatabaseObject(self.air, petId, doneEvent=doneEvent)
        pet = dbo.readPetProxy()

        def handlePetProxyRead(dbo, retCode, callback=callback, pet=pet):
            success = retCode == 0
            if not success:
                self.notify.warning('pet DB read failed')
                pet = None
            callback(success, pet)
            return

        self.acceptOnce(doneEvent, handlePetProxyRead)

    def _getNextSerialNum(self):
        num = self.serialNum
        self.serialNum += 1
        return num
