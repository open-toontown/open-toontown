from pandac.PandaModules import *
from toontown.toonbase.ToonBaseGlobal import *
from direct.interval.IntervalGlobal import *
from .BattleBase import *
from direct.distributed.ClockDelta import *
from toontown.toonbase import ToontownBattleGlobals
from direct.distributed import DistributedNode
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from direct.task.Task import Task
from direct.directnotify import DirectNotifyGlobal
from . import Movie
from . import MovieUtil
from toontown.suit import Suit
from direct.actor import Actor
from . import BattleProps
from direct.particles import ParticleEffect
from . import BattleParticles
from toontown.hood import ZoneUtil
from toontown.distributed import DelayDelete
from toontown.toon import TTEmote
from otp.avatar import Emote

class DistributedBattleBase(DistributedNode.DistributedNode, BattleBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedBattleBase')
    id = 0
    camPos = ToontownBattleGlobals.BattleCamDefaultPos
    camHpr = ToontownBattleGlobals.BattleCamDefaultHpr
    camFov = ToontownBattleGlobals.BattleCamDefaultFov
    camMenuFov = ToontownBattleGlobals.BattleCamMenuFov
    camJoinPos = ToontownBattleGlobals.BattleCamJoinPos
    camJoinHpr = ToontownBattleGlobals.BattleCamJoinHpr

    def __init__(self, cr, townBattle):
        DistributedNode.DistributedNode.__init__(self, cr)
        NodePath.__init__(self)
        self.assign(render.attachNewNode(self.uniqueBattleName('distributed-battle')))
        BattleBase.__init__(self)
        self.bossBattle = 0
        self.townBattle = townBattle
        self.__battleCleanedUp = 0
        self.activeIntervals = {}
        self.localToonJustJoined = 0
        self.choseAttackAlready = 0
        self.toons = []
        self.exitedToons = []
        self.suitTraps = ''
        self.membersKeep = None
        self.faceOffName = self.uniqueBattleName('faceoff')
        self.localToonBattleEvent = self.uniqueBattleName('localtoon-battle-event')
        self.adjustName = self.uniqueBattleName('adjust')
        self.timerCountdownTaskName = self.uniqueBattleName('timer-countdown')
        self.movie = Movie.Movie(self)
        self.timer = Timer()
        self.needAdjustTownBattle = 0
        self.streetBattle = 1
        self.levelBattle = 0
        self.localToonFsm = ClassicFSM.ClassicFSM('LocalToon', [State.State('HasLocalToon', self.enterHasLocalToon, self.exitHasLocalToon, ['NoLocalToon', 'WaitForServer']), State.State('NoLocalToon', self.enterNoLocalToon, self.exitNoLocalToon, ['HasLocalToon', 'WaitForServer']), State.State('WaitForServer', self.enterWaitForServer, self.exitWaitForServer, ['HasLocalToon', 'NoLocalToon'])], 'WaitForServer', 'WaitForServer')
        self.localToonFsm.enterInitialState()
        self.fsm = ClassicFSM.ClassicFSM('DistributedBattle', [State.State('Off', self.enterOff, self.exitOff, ['FaceOff',
          'WaitForInput',
          'WaitForJoin',
          'MakeMovie',
          'PlayMovie',
          'Reward',
          'Resume']),
         State.State('FaceOff', self.enterFaceOff, self.exitFaceOff, ['WaitForInput']),
         State.State('WaitForJoin', self.enterWaitForJoin, self.exitWaitForJoin, ['WaitForInput', 'Resume']),
         State.State('WaitForInput', self.enterWaitForInput, self.exitWaitForInput, ['WaitForInput', 'PlayMovie', 'Resume']),
         State.State('MakeMovie', self.enterMakeMovie, self.exitMakeMovie, ['PlayMovie', 'Resume']),
         State.State('PlayMovie', self.enterPlayMovie, self.exitPlayMovie, ['WaitForInput',
          'WaitForJoin',
          'Reward',
          'Resume']),
         State.State('Reward', self.enterReward, self.exitReward, ['Resume']),
         State.State('Resume', self.enterResume, self.exitResume, [])], 'Off', 'Off')
        self.fsm.enterInitialState()
        self.adjustFsm = ClassicFSM.ClassicFSM('Adjust', [State.State('Adjusting', self.enterAdjusting, self.exitAdjusting, ['NotAdjusting']), State.State('NotAdjusting', self.enterNotAdjusting, self.exitNotAdjusting, ['Adjusting'])], 'NotAdjusting', 'NotAdjusting')
        self.adjustFsm.enterInitialState()
        self.interactiveProp = None
        return

    def uniqueBattleName(self, name):
        DistributedBattleBase.id += 1
        return name + '-%d' % DistributedBattleBase.id

    def generate(self):
        self.notify.debug('generate(%s)' % self.doId)
        DistributedNode.DistributedNode.generate(self)
        self.__battleCleanedUp = 0
        self.reparentTo(render)
        self._skippingRewardMovie = False

    def storeInterval(self, interval, name):
        if name in self.activeIntervals:
            ival = self.activeIntervals[name]
            if hasattr(ival, 'delayDelete') or hasattr(ival, 'delayDeletes'):
                self.clearInterval(name, finish=1)
        self.activeIntervals[name] = interval

    def __cleanupIntervals(self):
        for interval in list(self.activeIntervals.values()):
            interval.finish()
            DelayDelete.cleanupDelayDeletes(interval)

        self.activeIntervals = {}

    def clearInterval(self, name, finish = 0):
        if name in self.activeIntervals:
            ival = self.activeIntervals[name]
            if finish:
                ival.finish()
            else:
                ival.pause()
            if name in self.activeIntervals:
                DelayDelete.cleanupDelayDeletes(ival)
                if name in self.activeIntervals:
                    del self.activeIntervals[name]
        else:
            self.notify.debug('interval: %s already cleared' % name)

    def finishInterval(self, name):
        if name in self.activeIntervals:
            interval = self.activeIntervals[name]
            interval.finish()

    def disable(self):
        self.notify.debug('disable(%s)' % self.doId)
        self.cleanupBattle()
        DistributedNode.DistributedNode.disable(self)

    def battleCleanedUp(self):
        return self.__battleCleanedUp

    def cleanupBattle(self):
        if self.__battleCleanedUp:
            return
        self.notify.debug('cleanupBattle(%s)' % self.doId)
        self.__battleCleanedUp = 1
        self.__cleanupIntervals()
        self.fsm.requestFinalState()
        if self.hasLocalToon():
            self.removeLocalToon()
            base.camLens.setFov(ToontownGlobals.DefaultCameraFov)
        self.localToonFsm.request('WaitForServer')
        self.ignoreAll()
        for suit in self.suits:
            if suit.battleTrap != NO_TRAP:
                self.notify.debug('250 calling self.removeTrap, suit=%d' % suit.doId)
                self.removeTrap(suit)
            suit.battleTrap = NO_TRAP
            suit.battleTrapProp = None
            self.notify.debug('253 suit.battleTrapProp = None')
            suit.battleTrapIsFresh = 0

        self.suits = []
        self.pendingSuits = []
        self.joiningSuits = []
        self.activeSuits = []
        self.suitTraps = ''
        self.toons = []
        self.joiningToons = []
        self.pendingToons = []
        self.activeToons = []
        self.runningToons = []
        self.__stopTimer()
        self.__cleanupIntervals()
        self._removeMembersKeep()
        return

    def delete(self):
        self.notify.debug('delete(%s)' % self.doId)
        self.__cleanupIntervals()
        self._removeMembersKeep()
        self.movie.cleanup()
        del self.townBattle
        self.removeNode()
        self.fsm = None
        self.localToonFsm = None
        self.adjustFsm = None
        self.__stopTimer()
        self.timer = None
        DistributedNode.DistributedNode.delete(self)
        return

    def loadTrap(self, suit, trapid):
        self.notify.debug('loadTrap() trap: %d suit: %d' % (trapid, suit.doId))
        trapName = AvProps[TRAP][trapid]
        trap = BattleProps.globalPropPool.getProp(trapName)
        suit.battleTrap = trapid
        suit.battleTrapIsFresh = 0
        suit.battleTrapProp = trap
        self.notify.debug('suit.battleTrapProp = trap %s' % trap)
        if trap.getName() == 'traintrack':
            pass
        else:
            trap.wrtReparentTo(suit)
        distance = MovieUtil.SUIT_TRAP_DISTANCE
        if trapName == 'rake':
            distance = MovieUtil.SUIT_TRAP_RAKE_DISTANCE
            distance += MovieUtil.getSuitRakeOffset(suit)
            trap.setH(180)
            trap.setScale(0.7)
        elif trapName == 'trapdoor' or trapName == 'quicksand':
            trap.setScale(1.7)
        elif trapName == 'marbles':
            distance = MovieUtil.SUIT_TRAP_MARBLES_DISTANCE
            trap.setH(94)
        elif trapName == 'tnt':
            trap.setP(90)
            tip = trap.find('**/joint_attachEmitter')
            sparks = BattleParticles.createParticleEffect(file='tnt')
            trap.sparksEffect = sparks
            sparks.start(tip)
        trap.setPos(0, distance, 0)
        if isinstance(trap, Actor.Actor):
            frame = trap.getNumFrames(trapName) - 1
            trap.pose(trapName, frame)

    def removeTrap(self, suit, removeTrainTrack = False):
        self.notify.debug('removeTrap() from suit: %d, removeTrainTrack=%s' % (suit.doId, removeTrainTrack))
        if suit.battleTrapProp == None:
            self.notify.debug('suit.battleTrapProp == None, suit.battleTrap=%s setting to NO_TRAP, returning' % suit.battleTrap)
            suit.battleTrap = NO_TRAP
            return
        if suit.battleTrap == UBER_GAG_LEVEL_INDEX:
            if removeTrainTrack:
                self.notify.debug('doing removeProp on traintrack')
                MovieUtil.removeProp(suit.battleTrapProp)
                for otherSuit in self.suits:
                    if not otherSuit == suit:
                        otherSuit.battleTrapProp = None
                        self.notify.debug('351 otherSuit=%d otherSuit.battleTrapProp = None' % otherSuit.doId)
                        otherSuit.battleTrap = NO_TRAP
                        otherSuit.battleTrapIsFresh = 0

            else:
                self.notify.debug('deliberately not doing removeProp on traintrack')
        else:
            self.notify.debug('suit.battleTrap != UBER_GAG_LEVEL_INDEX')
            MovieUtil.removeProp(suit.battleTrapProp)
        suit.battleTrapProp = None
        self.notify.debug('360 suit.battleTrapProp = None')
        suit.battleTrap = NO_TRAP
        suit.battleTrapIsFresh = 0
        return

    def pause(self):
        self.timer.stop()

    def unpause(self):
        self.timer.resume()

    def findSuit(self, id):
        for s in self.suits:
            if s.doId == id:
                return s

        return None

    def findToon(self, id):
        toon = self.getToon(id)
        if toon == None:
            return
        for t in self.toons:
            if t == toon:
                return t

        return

    def isSuitLured(self, suit):
        if self.luredSuits.count(suit) != 0:
            return 1
        return 0

    def unlureSuit(self, suit):
        self.notify.debug('movie unluring suit %s' % suit.doId)
        if self.luredSuits.count(suit) != 0:
            self.luredSuits.remove(suit)
            self.needAdjustTownBattle = 1
        return None

    def lureSuit(self, suit):
        self.notify.debug('movie luring suit %s' % suit.doId)
        if self.luredSuits.count(suit) == 0:
            self.luredSuits.append(suit)
            self.needAdjustTownBattle = 1
        return None

    def getActorPosHpr(self, actor, actorList = []):
        if isinstance(actor, Suit.Suit):
            if actorList == []:
                actorList = self.activeSuits
            if actorList.count(actor) != 0:
                numSuits = len(actorList) - 1
                index = actorList.index(actor)
                point = self.suitPoints[numSuits][index]
                return (Point3(point[0]), VBase3(point[1], 0.0, 0.0))
            else:
                self.notify.warning('getActorPosHpr() - suit not active')
        else:
            if actorList == []:
                actorList = self.activeToons
            if actorList.count(actor) != 0:
                numToons = len(actorList) - 1
                index = actorList.index(actor)
                point = self.toonPoints[numToons][index]
                return (Point3(point[0]), VBase3(point[1], 0.0, 0.0))
            else:
                self.notify.warning('getActorPosHpr() - toon not active')

    def setLevelDoId(self, levelDoId):
        pass

    def setBattleCellId(self, battleCellId):
        pass

    def setInteractivePropTrackBonus(self, trackBonus):
        self.interactivePropTrackBonus = trackBonus

    def getInteractivePropTrackBonus(self):
        return self.interactivePropTrackBonus

    def setPosition(self, x, y, z):
        self.notify.debug('setPosition() - %d %d %d' % (x, y, z))
        pos = Point3(x, y, z)
        self.setPos(pos)

    def setInitialSuitPos(self, x, y, z):
        self.initialSuitPos = Point3(x, y, z)
        self.headsUp(self.initialSuitPos)

    def setZoneId(self, zoneId):
        self.zoneId = zoneId

    def setBossBattle(self, value):
        self.bossBattle = value

    def setState(self, state, timestamp):
        if self.__battleCleanedUp:
            return
        self.notify.debug('setState(%s)' % state)
        self.fsm.request(state, [globalClockDelta.localElapsedTime(timestamp)])

    def setMembers(self, suits, suitsJoining, suitsPending, suitsActive, suitsLured, suitTraps, toons, toonsJoining, toonsPending, toonsActive, toonsRunning, timestamp):
        if self.__battleCleanedUp:
            return
        self.notify.debug('setMembers() - suits: %s suitsJoining: %s suitsPending: %s suitsActive: %s suitsLured: %s suitTraps: %s toons: %s toonsJoining: %s toonsPending: %s toonsActive: %s toonsRunning: %s' % (suits,
         suitsJoining,
         suitsPending,
         suitsActive,
         suitsLured,
         suitTraps,
         toons,
         toonsJoining,
         toonsPending,
         toonsActive,
         toonsRunning))
        ts = globalClockDelta.localElapsedTime(timestamp)
        oldsuits = self.suits
        self.suits = []
        suitGone = 0
        for s in suits:
            if s in self.cr.doId2do:
                suit = self.cr.doId2do[s]
                suit.setState('Battle')
                self.suits.append(suit)
                suit.interactivePropTrackBonus = self.interactivePropTrackBonus
                try:
                    suit.battleTrap
                except:
                    suit.battleTrap = NO_TRAP
                    suit.battleTrapProp = None
                    self.notify.debug('496 suit.battleTrapProp = None')
                    suit.battleTrapIsFresh = 0

            else:
                self.notify.warning('setMembers() - no suit in repository: %d' % s)
                self.suits.append(None)
                suitGone = 1

        numSuitsThatDied = 0
        for s in oldsuits:
            if self.suits.count(s) == 0:
                self.__removeSuit(s)
                numSuitsThatDied += 1
                self.notify.debug('suit %d dies, numSuitsThatDied=%d' % (s.doId, numSuitsThatDied))

        if numSuitsThatDied == 4:
            trainTrap = self.find('**/traintrack')
            if not trainTrap.isEmpty():
                self.notify.debug('removing old train trap when 4 suits died')
                trainTrap.removeNode()
        for s in suitsJoining:
            suit = self.suits[int(s)]
            if suit != None and self.joiningSuits.count(suit) == 0:
                self.makeSuitJoin(suit, ts)

        for s in suitsPending:
            suit = self.suits[int(s)]
            if suit != None and self.pendingSuits.count(suit) == 0:
                self.__makeSuitPending(suit)

        activeSuits = []
        for s in suitsActive:
            suit = self.suits[int(s)]
            if suit != None and self.activeSuits.count(suit) == 0:
                activeSuits.append(suit)

        oldLuredSuits = self.luredSuits
        self.luredSuits = []
        for s in suitsLured:
            suit = self.suits[int(s)]
            if suit != None:
                self.luredSuits.append(suit)
                if oldLuredSuits.count(suit) == 0:
                    self.needAdjustTownBattle = 1

        if self.needAdjustTownBattle == 0:
            for s in oldLuredSuits:
                if self.luredSuits.count(s) == 0:
                    self.needAdjustTownBattle = 1

        index = 0
        oldSuitTraps = self.suitTraps
        self.suitTraps = suitTraps
        for s in suitTraps:
            trapid = int(s)
            if trapid == 9:
                trapid = -1
            suit = self.suits[index]
            index += 1
            if suit != None:
                if (trapid == NO_TRAP or trapid != suit.battleTrap) and suit.battleTrapProp != None:
                    self.notify.debug('569 calling self.removeTrap, suit=%d' % suit.doId)
                    self.removeTrap(suit)
                if trapid != NO_TRAP and suit.battleTrapProp == None:
                    if self.fsm.getCurrentState().getName() != 'PlayMovie':
                        self.loadTrap(suit, trapid)

        if len(oldSuitTraps) != len(self.suitTraps):
            self.needAdjustTownBattle = 1
        else:
            for i in range(len(oldSuitTraps)):
                if oldSuitTraps[i] == '9' and self.suitTraps[i] != '9' or oldSuitTraps[i] != '9' and self.suitTraps[i] == '9':
                    self.needAdjustTownBattle = 1
                    break

        if suitGone:
            validSuits = []
            for s in self.suits:
                if s != None:
                    validSuits.append(s)

            self.suits = validSuits
            self.needAdjustTownBattle = 1
        oldtoons = self.toons
        self.toons = []
        toonGone = 0
        for t in toons:
            toon = self.getToon(t)
            if toon == None:
                self.notify.warning('setMembers() - toon not in cr!')
                self.toons.append(None)
                toonGone = 1
                continue
            self.toons.append(toon)
            if oldtoons.count(toon) == 0:
                self.notify.debug('setMembers() - add toon: %d' % toon.doId)
                self.__listenForUnexpectedExit(toon)
                toon.stopLookAround()
                toon.stopSmooth()

        for t in oldtoons:
            if self.toons.count(t) == 0:
                if self.__removeToon(t) == 1:
                    self.notify.debug('setMembers() - local toon left battle')
                    return []

        for t in toonsJoining:
            if int(t) < len(self.toons):
                toon = self.toons[int(t)]
                if toon != None and self.joiningToons.count(toon) == 0:
                    self.__makeToonJoin(toon, toonsPending, ts)
            else:
                self.notify.warning('setMembers toonsJoining t=%s not in self.toons %s' % (t, self.toons))

        for t in toonsPending:
            if int(t) < len(self.toons):
                toon = self.toons[int(t)]
                if toon != None and self.pendingToons.count(toon) == 0:
                    self.__makeToonPending(toon, ts)
            else:
                self.notify.warning('setMembers toonsPending t=%s not in self.toons %s' % (t, self.toons))

        for t in toonsRunning:
            toon = self.toons[int(t)]
            if toon != None and self.runningToons.count(toon) == 0:
                self.__makeToonRun(toon, ts)

        activeToons = []
        for t in toonsActive:
            toon = self.toons[int(t)]
            if toon != None and self.activeToons.count(toon) == 0:
                activeToons.append(toon)

        if len(activeSuits) > 0 or len(activeToons) > 0:
            self.__makeAvsActive(activeSuits, activeToons)
        if toonGone == 1:
            validToons = []
            for toon in self.toons:
                if toon != None:
                    validToons.append(toon)

            self.toons = validToons
        if len(self.activeToons) > 0:
            self.__requestAdjustTownBattle()
        currStateName = self.localToonFsm.getCurrentState().getName()
        if self.toons.count(base.localAvatar):
            if oldtoons.count(base.localAvatar) == 0:
                self.notify.debug('setMembers() - local toon just joined')
                if self.streetBattle == 1:
                    base.cr.playGame.getPlace().enterZone(self.zoneId)
                self.localToonJustJoined = 1
            if currStateName != 'HasLocalToon':
                self.localToonFsm.request('HasLocalToon')
        else:
            if oldtoons.count(base.localAvatar):
                self.notify.debug('setMembers() - local toon just ran')
                if self.levelBattle:
                    self.unlockLevelViz()
            if currStateName != 'NoLocalToon':
                self.localToonFsm.request('NoLocalToon')
        return oldtoons

    def adjust(self, timestamp):
        if self.__battleCleanedUp:
            return
        self.notify.debug('adjust(%f) from server' % globalClockDelta.localElapsedTime(timestamp))
        self.adjustFsm.request('Adjusting', [globalClockDelta.localElapsedTime(timestamp)])

    def setMovie(self, active, toons, suits, id0, tr0, le0, tg0, hp0, ac0, hpb0, kbb0, died0, revive0, id1, tr1, le1, tg1, hp1, ac1, hpb1, kbb1, died1, revive1, id2, tr2, le2, tg2, hp2, ac2, hpb2, kbb2, died2, revive2, id3, tr3, le3, tg3, hp3, ac3, hpb3, kbb3, died3, revive3, sid0, at0, stg0, dm0, sd0, sb0, st0, sid1, at1, stg1, dm1, sd1, sb1, st1, sid2, at2, stg2, dm2, sd2, sb2, st2, sid3, at3, stg3, dm3, sd3, sb3, st3):
        if self.__battleCleanedUp:
            return
        self.notify.debug('setMovie()')
        if int(active) == 1:
            self.notify.debug('setMovie() - movie is active')
            self.movie.genAttackDicts(toons, suits, id0, tr0, le0, tg0, hp0, ac0, hpb0, kbb0, died0, revive0, id1, tr1, le1, tg1, hp1, ac1, hpb1, kbb1, died1, revive1, id2, tr2, le2, tg2, hp2, ac2, hpb2, kbb2, died2, revive2, id3, tr3, le3, tg3, hp3, ac3, hpb3, kbb3, died3, revive3, sid0, at0, stg0, dm0, sd0, sb0, st0, sid1, at1, stg1, dm1, sd1, sb1, st1, sid2, at2, stg2, dm2, sd2, sb2, st2, sid3, at3, stg3, dm3, sd3, sb3, st3)

    def setChosenToonAttacks(self, ids, tracks, levels, targets):
        if self.__battleCleanedUp:
            return
        self.notify.debug('setChosenToonAttacks() - (%s), (%s), (%s), (%s)' % (ids,
         tracks,
         levels,
         targets))
        toonIndices = []
        targetIndices = []
        unAttack = 0
        localToonInList = 0
        for i in range(len(ids)):
            track = tracks[i]
            level = levels[i]
            toon = self.findToon(ids[i])
            if toon == None or self.activeToons.count(toon) == 0:
                self.notify.warning('setChosenToonAttacks() - toon gone or not in battle: %d!' % ids[i])
                toonIndices.append(-1)
                tracks.append(-1)
                levels.append(-1)
                targetIndices.append(-1)
                continue
            if toon == base.localAvatar:
                localToonInList = 1
            toonIndices.append(self.activeToons.index(toon))
            if track == SOS:
                targetIndex = -1
            elif track == NPCSOS:
                targetIndex = -1
            elif track == PETSOS:
                targetIndex = -1
            elif track == PASS:
                targetIndex = -1
                tracks[i] = PASS_ATTACK
            elif attackAffectsGroup(track, level):
                targetIndex = -1
            elif track == HEAL:
                target = self.findToon(targets[i])
                if target != None and self.activeToons.count(target) != 0:
                    targetIndex = self.activeToons.index(target)
                else:
                    targetIndex = -1
            elif track == UN_ATTACK:
                targetIndex = -1
                tracks[i] = NO_ATTACK
                if toon == base.localAvatar:
                    unAttack = 1
                    self.choseAttackAlready = 0
            elif track == NO_ATTACK:
                targetIndex = -1
            else:
                target = self.findSuit(targets[i])
                if target != None and self.activeSuits.count(target) != 0:
                    targetIndex = self.activeSuits.index(target)
                else:
                    targetIndex = -1
            targetIndices.append(targetIndex)

        for i in range(4 - len(ids)):
            toonIndices.append(-1)
            tracks.append(-1)
            levels.append(-1)
            targetIndices.append(-1)

        self.townBattleAttacks = (toonIndices,
         tracks,
         levels,
         targetIndices)
        if self.localToonActive() and localToonInList == 1:
            if unAttack == 1 and self.fsm.getCurrentState().getName() == 'WaitForInput':
                if self.townBattle.fsm.getCurrentState().getName() != 'Attack':
                    self.townBattle.setState('Attack')
            self.townBattle.updateChosenAttacks(self.townBattleAttacks[0], self.townBattleAttacks[1], self.townBattleAttacks[2], self.townBattleAttacks[3])
        return

    def setBattleExperience(self, id0, origExp0, earnedExp0, origQuests0, items0, missedItems0, origMerits0, merits0, parts0, id1, origExp1, earnedExp1, origQuests1, items1, missedItems1, origMerits1, merits1, parts1, id2, origExp2, earnedExp2, origQuests2, items2, missedItems2, origMerits2, merits2, parts2, id3, origExp3, earnedExp3, origQuests3, items3, missedItems3, origMerits3, merits3, parts3, deathList, uberList, helpfulToonsList):
        if self.__battleCleanedUp:
            return
        self.movie.genRewardDicts(id0, origExp0, earnedExp0, origQuests0, items0, missedItems0, origMerits0, merits0, parts0, id1, origExp1, earnedExp1, origQuests1, items1, missedItems1, origMerits1, merits1, parts1, id2, origExp2, earnedExp2, origQuests2, items2, missedItems2, origMerits2, merits2, parts2, id3, origExp3, earnedExp3, origQuests3, items3, missedItems3, origMerits3, merits3, parts3, deathList, uberList, helpfulToonsList)

    def __listenForUnexpectedExit(self, toon):
        self.accept(toon.uniqueName('disable'), self.__handleUnexpectedExit, extraArgs=[toon])
        self.accept(toon.uniqueName('died'), self.__handleDied, extraArgs=[toon])

    def __handleUnexpectedExit(self, toon):
        self.notify.warning('handleUnexpectedExit() - toon: %d' % toon.doId)
        self.__removeToon(toon, unexpected=1)

    def __handleDied(self, toon):
        self.notify.warning('handleDied() - toon: %d' % toon.doId)
        if toon == base.localAvatar:
            self.d_toonDied(toon.doId)
            self.cleanupBattle()

    def delayDeleteMembers(self):
        membersKeep = []
        for t in self.toons:
            membersKeep.append(DelayDelete.DelayDelete(t, 'delayDeleteMembers'))

        for s in self.suits:
            membersKeep.append(DelayDelete.DelayDelete(s, 'delayDeleteMembers'))

        self._removeMembersKeep()
        self.membersKeep = membersKeep

    def _removeMembersKeep(self):
        if self.membersKeep:
            for delayDelete in self.membersKeep:
                delayDelete.destroy()

        self.membersKeep = None
        return

    def __removeSuit(self, suit):
        self.notify.debug('__removeSuit(%d)' % suit.doId)
        if self.suits.count(suit) != 0:
            self.suits.remove(suit)
        if self.joiningSuits.count(suit) != 0:
            self.joiningSuits.remove(suit)
        if self.pendingSuits.count(suit) != 0:
            self.pendingSuits.remove(suit)
        if self.activeSuits.count(suit) != 0:
            self.activeSuits.remove(suit)
        self.suitGone = 1
        if suit.battleTrap != NO_TRAP:
            self.notify.debug('882 calling self.removeTrap, suit=%d' % suit.doId)
            self.removeTrap(suit)
        suit.battleTrap = NO_TRAP
        suit.battleTrapProp = None
        self.notify.debug('883 suit.battleTrapProp = None')
        suit.battleTrapIsFresh = 0
        return

    def __removeToon(self, toon, unexpected = 0):
        self.notify.debug('__removeToon(%d)' % toon.doId)
        self.exitedToons.append(toon)
        if self.toons.count(toon) != 0:
            self.toons.remove(toon)
        if self.joiningToons.count(toon) != 0:
            self.clearInterval(self.taskName('to-pending-toon-%d' % toon.doId))
            if toon in self.joiningToons:
                self.joiningToons.remove(toon)
        if self.pendingToons.count(toon) != 0:
            self.pendingToons.remove(toon)
        if self.activeToons.count(toon) != 0:
            self.activeToons.remove(toon)
        if self.runningToons.count(toon) != 0:
            self.clearInterval(self.taskName('running-%d' % toon.doId), finish=1)
            if toon in self.runningToons:
                self.runningToons.remove(toon)
        self.ignore(toon.uniqueName('disable'))
        self.ignore(toon.uniqueName('died'))
        self.toonGone = 1
        if toon == base.localAvatar:
            self.removeLocalToon()
            self.__teleportToSafeZone(toon)
            return 1
        return 0

    def removeLocalToon(self):
        if self._skippingRewardMovie:
            return
        if base.cr.playGame.getPlace() != None:
            base.cr.playGame.getPlace().setState('walk')
        base.localAvatar.earnedExperience = None
        self.localToonFsm.request('NoLocalToon')
        return

    def removeInactiveLocalToon(self, toon):
        self.notify.debug('removeInactiveLocalToon(%d)' % toon.doId)
        self.exitedToons.append(toon)
        if self.toons.count(toon) != 0:
            self.toons.remove(toon)
        if self.joiningToons.count(toon) != 0:
            self.clearInterval(self.taskName('to-pending-toon-%d' % toon.doId), finish=1)
            if toon in self.joiningToons:
                self.joiningToons.remove(toon)
        if self.pendingToons.count(toon) != 0:
            self.pendingToons.remove(toon)
        self.ignore(toon.uniqueName('disable'))
        self.ignore(toon.uniqueName('died'))
        base.cr.playGame.getPlace().setState('walk')
        self.localToonFsm.request('WaitForServer')

    def __createJoinInterval(self, av, destPos, destHpr, name, ts, callback, toon = 0):
        joinTrack = Sequence()
        joinTrack.append(Func(Emote.globalEmote.disableAll, av, 'dbattlebase, createJoinInterval'))
        avPos = av.getPos(self)
        avPos = Point3(avPos[0], avPos[1], 0.0)
        av.setShadowHeight(0)
        plist = self.buildJoinPointList(avPos, destPos, toon)
        if len(plist) == 0:
            joinTrack.append(Func(av.headsUp, self, destPos))
            if toon == 0:
                timeToDest = self.calcSuitMoveTime(avPos, destPos)
                joinTrack.append(Func(av.loop, 'walk'))
            else:
                timeToDest = self.calcToonMoveTime(avPos, destPos)
                joinTrack.append(Func(av.loop, 'run'))
            if timeToDest > BATTLE_SMALL_VALUE:
                joinTrack.append(LerpPosInterval(av, timeToDest, destPos, other=self))
                totalTime = timeToDest
            else:
                totalTime = 0
        else:
            timeToPerimeter = 0
            if toon == 0:
                timeToPerimeter = self.calcSuitMoveTime(plist[0], avPos)
                timePerSegment = 10.0 / BattleBase.suitSpeed
                timeToDest = self.calcSuitMoveTime(BattleBase.posA, destPos)
            else:
                timeToPerimeter = self.calcToonMoveTime(plist[0], avPos)
                timePerSegment = 10.0 / BattleBase.toonSpeed
                timeToDest = self.calcToonMoveTime(BattleBase.posE, destPos)
            totalTime = timeToPerimeter + (len(plist) - 1) * timePerSegment + timeToDest
            if totalTime > MAX_JOIN_T:
                self.notify.warning('__createJoinInterval() - time: %f' % totalTime)
            joinTrack.append(Func(av.headsUp, self, plist[0]))
            if toon == 0:
                joinTrack.append(Func(av.loop, 'walk'))
            else:
                joinTrack.append(Func(av.loop, 'run'))
            joinTrack.append(LerpPosInterval(av, timeToPerimeter, plist[0], other=self))
            for p in plist[1:]:
                joinTrack.append(Func(av.headsUp, self, p))
                joinTrack.append(LerpPosInterval(av, timePerSegment, p, other=self))

            joinTrack.append(Func(av.headsUp, self, destPos))
            joinTrack.append(LerpPosInterval(av, timeToDest, destPos, other=self))
        joinTrack.append(Func(av.loop, 'neutral'))
        joinTrack.append(Func(av.headsUp, self, Point3(0, 0, 0)))
        tval = totalTime - ts
        if tval < 0:
            tval = totalTime
        joinTrack.append(Func(Emote.globalEmote.releaseAll, av, 'dbattlebase, createJoinInterval'))
        joinTrack.append(Func(callback, av, tval))
        if av == base.localAvatar:
            camTrack = Sequence()

            def setCamFov(fov):
                base.camLens.setFov(fov)

            camTrack.append(Func(setCamFov, self.camFov))
            camTrack.append(Func(camera.wrtReparentTo, self))
            camTrack.append(Func(camera.setPos, self.camJoinPos))
            camTrack.append(Func(camera.setHpr, self.camJoinHpr))
            return Parallel(joinTrack, camTrack, name=name)
        else:
            return Sequence(joinTrack, name=name)

    def makeSuitJoin(self, suit, ts):
        self.notify.debug('makeSuitJoin(%d)' % suit.doId)
        spotIndex = len(self.pendingSuits) + len(self.joiningSuits)
        self.joiningSuits.append(suit)
        suit.setState('Battle')
        openSpot = self.suitPendingPoints[spotIndex]
        pos = openSpot[0]
        hpr = VBase3(openSpot[1], 0.0, 0.0)
        trackName = self.taskName('to-pending-suit-%d' % suit.doId)
        track = self.__createJoinInterval(suit, pos, hpr, trackName, ts, self.__handleSuitJoinDone)
        track.start(ts)
        track.delayDelete = DelayDelete.DelayDelete(suit, 'makeSuitJoin')
        self.storeInterval(track, trackName)
        if ToontownBattleGlobals.SkipMovie:
            track.finish()

    def __handleSuitJoinDone(self, suit, ts):
        self.notify.debug('suit: %d is now pending' % suit.doId)
        if self.hasLocalToon():
            self.d_joinDone(base.localAvatar.doId, suit.doId)

    def __makeSuitPending(self, suit):
        self.notify.debug('__makeSuitPending(%d)' % suit.doId)
        self.clearInterval(self.taskName('to-pending-suit-%d' % suit.doId), finish=1)
        if self.joiningSuits.count(suit):
            self.joiningSuits.remove(suit)
        self.pendingSuits.append(suit)

    def __teleportToSafeZone(self, toon):
        self.notify.debug('teleportToSafeZone(%d)' % toon.doId)
        hoodId = ZoneUtil.getCanonicalHoodId(self.zoneId)
        if hoodId in base.localAvatar.hoodsVisited:
            target_sz = ZoneUtil.getSafeZoneId(self.zoneId)
        else:
            target_sz = ZoneUtil.getSafeZoneId(base.localAvatar.defaultZone)
        base.cr.playGame.getPlace().fsm.request('teleportOut', [{'loader': ZoneUtil.getLoaderName(target_sz),
          'where': ZoneUtil.getWhereName(target_sz, 1),
          'how': 'teleportIn',
          'hoodId': target_sz,
          'zoneId': target_sz,
          'shardId': None,
          'avId': -1,
          'battle': 1}])
        return

    def __makeToonJoin(self, toon, pendingToons, ts):
        self.notify.debug('__makeToonJoin(%d)' % toon.doId)
        spotIndex = len(pendingToons) + len(self.joiningToons)
        self.joiningToons.append(toon)
        openSpot = self.toonPendingPoints[spotIndex]
        pos = openSpot[0]
        hpr = VBase3(openSpot[1], 0.0, 0.0)
        trackName = self.taskName('to-pending-toon-%d' % toon.doId)
        track = self.__createJoinInterval(toon, pos, hpr, trackName, ts, self.__handleToonJoinDone, toon=1)
        if toon != base.localAvatar:
            toon.animFSM.request('off')
        track.start(ts)
        track.delayDelete = DelayDelete.DelayDelete(toon, '__makeToonJoin')
        self.storeInterval(track, trackName)

    def __handleToonJoinDone(self, toon, ts):
        self.notify.debug('__handleToonJoinDone() - pending: %d' % toon.doId)
        if self.hasLocalToon():
            self.d_joinDone(base.localAvatar.doId, toon.doId)

    def __makeToonPending(self, toon, ts):
        self.notify.debug('__makeToonPending(%d)' % toon.doId)
        self.clearInterval(self.taskName('to-pending-toon-%d' % toon.doId), finish=1)
        if self.joiningToons.count(toon):
            self.joiningToons.remove(toon)
        spotIndex = len(self.pendingToons)
        self.pendingToons.append(toon)
        openSpot = self.toonPendingPoints[spotIndex]
        pos = openSpot[0]
        hpr = VBase3(openSpot[1], 0.0, 0.0)
        toon.loop('neutral')
        toon.setPosHpr(self, pos, hpr)
        if base.localAvatar == toon:
            currStateName = self.fsm.getCurrentState().getName()

    def __makeAvsActive(self, suits, toons):
        self.notify.debug('__makeAvsActive()')
        self.__stopAdjusting()
        for s in suits:
            if self.joiningSuits.count(s):
                self.notify.warning('suit: %d was in joining list!' % s.doId)
                self.joiningSuits.remove(s)
            if self.pendingSuits.count(s):
                self.pendingSuits.remove(s)
            self.notify.debug('__makeAvsActive() - suit: %d' % s.doId)
            self.activeSuits.append(s)

        if len(self.activeSuits) >= 1:
            for suit in self.activeSuits:
                suitPos, suitHpr = self.getActorPosHpr(suit)
                if self.isSuitLured(suit) == 0:
                    suit.setPosHpr(self, suitPos, suitHpr)
                else:
                    spos = Point3(suitPos[0], suitPos[1] - MovieUtil.SUIT_LURE_DISTANCE, suitPos[2])
                    suit.setPosHpr(self, spos, suitHpr)
                suit.loop('neutral')

        for toon in toons:
            if self.joiningToons.count(toon):
                self.notify.warning('toon: %d was in joining list!' % toon.doId)
                self.joiningToons.remove(toon)
            if self.pendingToons.count(toon):
                self.pendingToons.remove(toon)
            self.notify.debug('__makeAvsActive() - toon: %d' % toon.doId)
            if self.activeToons.count(toon) == 0:
                self.activeToons.append(toon)
            else:
                self.notify.warning('makeAvsActive() - toon: %d is active!' % toon.doId)

        if len(self.activeToons) >= 1:
            for toon in self.activeToons:
                toonPos, toonHpr = self.getActorPosHpr(toon)
                toon.setPosHpr(self, toonPos, toonHpr)
                toon.loop('neutral')

        if self.fsm.getCurrentState().getName() == 'WaitForInput' and self.localToonActive() and self.localToonJustJoined == 1:
            self.notify.debug('makeAvsActive() - local toon just joined')
            self.__enterLocalToonWaitForInput()
            self.localToonJustJoined = 0
            self.startTimer()

    def __makeToonRun(self, toon, ts):
        self.notify.debug('__makeToonRun(%d)' % toon.doId)
        if self.activeToons.count(toon):
            self.activeToons.remove(toon)
        self.runningToons.append(toon)
        self.toonGone = 1
        self.__stopTimer()
        if self.localToonRunning():
            self.townBattle.setState('Off')
        runMTrack = MovieUtil.getToonTeleportOutInterval(toon)
        runName = self.taskName('running-%d' % toon.doId)
        self.notify.debug('duration: %f' % runMTrack.getDuration())
        runMTrack.start(ts)
        runMTrack.delayDelete = DelayDelete.DelayDelete(toon, '__makeToonRun')
        self.storeInterval(runMTrack, runName)

    def getToon(self, toonId):
        if toonId in self.cr.doId2do:
            return self.cr.doId2do[toonId]
        else:
            self.notify.warning('getToon() - toon: %d not in repository!' % toonId)
            return None
        return None

    def d_toonRequestJoin(self, toonId, pos):
        self.notify.debug('network:toonRequestJoin()')
        self.sendUpdate('toonRequestJoin', [pos[0], pos[1], pos[2]])

    def d_toonRequestRun(self, toonId):
        self.notify.debug('network:toonRequestRun()')
        self.sendUpdate('toonRequestRun', [])

    def d_toonDied(self, toonId):
        self.notify.debug('network:toonDied()')
        self.sendUpdate('toonDied', [])

    def d_faceOffDone(self, toonId):
        self.notify.debug('network:faceOffDone()')
        self.sendUpdate('faceOffDone', [])

    def d_adjustDone(self, toonId):
        self.notify.debug('network:adjustDone()')
        self.sendUpdate('adjustDone', [])

    def d_timeout(self, toonId):
        self.notify.debug('network:timeout()')
        self.sendUpdate('timeout', [])

    def d_movieDone(self, toonId):
        self.notify.debug('network:movieDone()')
        self.sendUpdate('movieDone', [])

    def d_rewardDone(self, toonId):
        self.notify.debug('network:rewardDone()')
        self.sendUpdate('rewardDone', [])

    def d_joinDone(self, toonId, avId):
        self.notify.debug('network:joinDone(%d)' % avId)
        self.sendUpdate('joinDone', [avId])

    def d_requestAttack(self, toonId, track, level, av):
        self.notify.debug('network:requestAttack(%d, %d, %d)' % (track, level, av))
        self.sendUpdate('requestAttack', [track, level, av])

    def d_requestPetProxy(self, toonId, av):
        self.notify.debug('network:requestPetProxy(%s)' % av)
        self.sendUpdate('requestPetProxy', [av])

    def enterOff(self, ts = 0):
        self.localToonFsm.requestFinalState()
        return None

    def exitOff(self):
        return None

    def enterFaceOff(self, ts = 0):
        return None

    def exitFaceOff(self):
        return None

    def enterWaitForJoin(self, ts = 0):
        self.notify.debug('enterWaitForJoin()')
        return None

    def exitWaitForJoin(self):
        return None

    def __enterLocalToonWaitForInput(self):
        self.notify.debug('enterLocalToonWaitForInput()')
        camera.setPosHpr(self.camPos, self.camHpr)
        base.camLens.setFov(self.camMenuFov)
        NametagGlobals.setMasterArrowsOn(0)
        self.townBattle.setState('Attack')
        self.accept(self.localToonBattleEvent, self.__handleLocalToonBattleEvent)

    def startTimer(self, ts = 0):
        self.notify.debug('startTimer()')
        if ts >= CLIENT_INPUT_TIMEOUT:
            self.notify.warning('startTimer() - ts: %f timeout: %f' % (ts, CLIENT_INPUT_TIMEOUT))
            self.__timedOut()
            return
        self.timer.startCallback(CLIENT_INPUT_TIMEOUT - ts, self.__timedOut)
        timeTask = Task.loop(Task(self.__countdown), Task.pause(0.2))
        taskMgr.add(timeTask, self.timerCountdownTaskName)

    def __stopTimer(self):
        self.notify.debug('__stopTimer()')
        self.timer.stop()
        taskMgr.remove(self.timerCountdownTaskName)

    def __countdown(self, task):
        if hasattr(self.townBattle, 'timer'):
            self.townBattle.updateTimer(int(self.timer.getT()))
        else:
            self.notify.warning('__countdown has tried to update a timer that has been deleted. Stopping timer')
            self.__stopTimer()
        return Task.done

    def enterWaitForInput(self, ts = 0):
        self.notify.debug('enterWaitForInput()')
        if self.interactiveProp:
            self.interactiveProp.gotoBattleCheer()
        self.choseAttackAlready = 0
        if self.localToonActive():
            self.__enterLocalToonWaitForInput()
            self.startTimer(ts)
        if self.needAdjustTownBattle == 1:
            self.__adjustTownBattle()
        return None

    def exitWaitForInput(self):
        self.notify.debug('exitWaitForInput()')
        if self.localToonActive():
            self.townBattle.setState('Off')
            base.camLens.setFov(self.camFov)
            self.ignore(self.localToonBattleEvent)
            self.__stopTimer()
        return None

    def __handleLocalToonBattleEvent(self, response):
        mode = response['mode']
        noAttack = 0
        if mode == 'Attack':
            self.notify.debug('got an attack')
            track = response['track']
            level = response['level']
            target = response['target']
            targetId = target
            if track == HEAL and not levelAffectsGroup(HEAL, level):
                if target >= 0 and target < len(self.activeToons):
                    targetId = self.activeToons[target].doId
                else:
                    self.notify.warning('invalid toon target: %d' % target)
                    track = -1
                    level = -1
                    targetId = -1
            elif track == HEAL and len(self.activeToons) == 1:
                self.notify.warning('invalid group target for heal')
                track = -1
                level = -1
            elif not attackAffectsGroup(track, level):
                if target >= 0 and target < len(self.activeSuits):
                    targetId = self.activeSuits[target].doId
                else:
                    target = -1
            if len(self.luredSuits) > 0:
                if track == TRAP or track == LURE and not levelAffectsGroup(LURE, level):
                    if target != -1:
                        suit = self.findSuit(targetId)
                        if self.luredSuits.count(suit) != 0:
                            self.notify.warning('Suit: %d was lured!' % targetId)
                            track = -1
                            level = -1
                            targetId = -1
                elif track == LURE:
                    if levelAffectsGroup(LURE, level) and len(self.activeSuits) == len(self.luredSuits):
                        self.notify.warning('All suits are lured!')
                        track = -1
                        level = -1
                        targetId = -1
            if track == TRAP:
                if target != -1:
                    if attackAffectsGroup(track, level):
                        pass
                    else:
                        suit = self.findSuit(targetId)
                        if suit.battleTrap != NO_TRAP:
                            self.notify.warning('Suit: %d was already trapped!' % targetId)
                            track = -1
                            level = -1
                            targetId = -1
            self.d_requestAttack(base.localAvatar.doId, track, level, targetId)
        elif mode == 'Run':
            self.notify.debug('got a run')
            self.d_toonRequestRun(base.localAvatar.doId)
        elif mode == 'SOS':
            targetId = response['id']
            self.notify.debug('got an SOS for friend: %d' % targetId)
            self.d_requestAttack(base.localAvatar.doId, SOS, -1, targetId)
        elif mode == 'NPCSOS':
            targetId = response['id']
            self.notify.debug('got an NPCSOS for friend: %d' % targetId)
            self.d_requestAttack(base.localAvatar.doId, NPCSOS, -1, targetId)
        elif mode == 'PETSOS':
            targetId = response['id']
            trickId = response['trickId']
            self.notify.debug('got an PETSOS for pet: %d' % targetId)
            self.d_requestAttack(base.localAvatar.doId, PETSOS, trickId, targetId)
        elif mode == 'PETSOSINFO':
            petProxyId = response['id']
            self.notify.debug('got a PETSOSINFO for pet: %d' % petProxyId)
            if petProxyId in base.cr.doId2do:
                self.notify.debug('pet: %d was already in the repository' % petProxyId)
                proxyGenerateMessage = 'petProxy-%d-generated' % petProxyId
                messenger.send(proxyGenerateMessage)
            else:
                self.d_requestPetProxy(base.localAvatar.doId, petProxyId)
            noAttack = 1
        elif mode == 'Pass':
            targetId = response['id']
            self.notify.debug('got a Pass')
            self.d_requestAttack(base.localAvatar.doId, PASS, -1, -1)
        elif mode == 'UnAttack':
            self.d_requestAttack(base.localAvatar.doId, UN_ATTACK, -1, -1)
            noAttack = 1
        elif mode == 'Fire':
            target = response['target']
            targetId = self.activeSuits[target].doId
            self.d_requestAttack(base.localAvatar.doId, FIRE, -1, targetId)
        else:
            self.notify.warning('unknown battle response')
            return
        if noAttack == 1:
            self.choseAttackAlready = 0
        else:
            self.choseAttackAlready = 1

    def __timedOut(self):
        if self.choseAttackAlready == 1:
            return
        self.notify.debug('WaitForInput timed out')
        if self.localToonActive():
            self.notify.debug('battle timed out')
            self.d_timeout(base.localAvatar.doId)

    def enterMakeMovie(self, ts = 0):
        self.notify.debug('enterMakeMovie()')
        return None

    def exitMakeMovie(self):
        return None

    def enterPlayMovie(self, ts):
        self.notify.debug('enterPlayMovie()')
        self.delayDeleteMembers()
        if self.hasLocalToon():
            NametagGlobals.setMasterArrowsOn(0)
        if ToontownBattleGlobals.SkipMovie:
            self.movie.play(ts, self.__handleMovieDone)
            self.movie.finish()
        else:
            self.movie.play(ts, self.__handleMovieDone)
        return None

    def __handleMovieDone(self):
        self.notify.debug('__handleMovieDone()')
        if self.hasLocalToon():
            self.d_movieDone(base.localAvatar.doId)
        self.movie.reset()

    def exitPlayMovie(self):
        self.notify.debug('exitPlayMovie()')
        self.movie.reset(finish=1)
        self._removeMembersKeep()
        self.townBattleAttacks = ([-1,
          -1,
          -1,
          -1],
         [-1,
          -1,
          -1,
          -1],
         [-1,
          -1,
          -1,
          -1],
         [0,
          0,
          0,
          0])
        return None

    def hasLocalToon(self):
        return self.toons.count(base.localAvatar) > 0

    def localToonPendingOrActive(self):
        return self.pendingToons.count(base.localAvatar) > 0 or self.activeToons.count(base.localAvatar) > 0

    def localToonActive(self):
        return self.activeToons.count(base.localAvatar) > 0

    def localToonActiveOrRunning(self):
        return self.activeToons.count(base.localAvatar) > 0 or self.runningToons.count(base.localAvatar) > 0

    def localToonRunning(self):
        return self.runningToons.count(base.localAvatar) > 0

    def enterHasLocalToon(self):
        self.notify.debug('enterHasLocalToon()')
        if base.cr.playGame.getPlace() != None:
            base.cr.playGame.getPlace().setState('battle', self.localToonBattleEvent)
            if localAvatar and hasattr(localAvatar, 'inventory') and localAvatar.inventory:
                localAvatar.inventory.setInteractivePropTrackBonus(self.interactivePropTrackBonus)
        camera.wrtReparentTo(self)
        base.camLens.setFov(self.camFov)
        return

    def exitHasLocalToon(self):
        self.ignore(self.localToonBattleEvent)
        self.__stopTimer()
        if localAvatar and hasattr(localAvatar, 'inventory') and localAvatar.inventory:
            localAvatar.inventory.setInteractivePropTrackBonus(-1)
        stateName = None
        place = base.cr.playGame.getPlace()
        if place:
            stateName = place.fsm.getCurrentState().getName()
        if stateName == 'died':
            self.movie.reset()
            camera.reparentTo(render)
            camera.setPosHpr(localAvatar, 5.2, 5.45, localAvatar.getHeight() * 0.66, 131.5, 3.6, 0)
        else:
            camera.wrtReparentTo(base.localAvatar)
            messenger.send('localToonLeftBattle')
        base.camLens.setFov(ToontownGlobals.DefaultCameraFov)
        return

    def enterNoLocalToon(self):
        self.notify.debug('enterNoLocalToon()')
        return None

    def exitNoLocalToon(self):
        return None

    def setSkippingRewardMovie(self):
        self._skippingRewardMovie = True

    def enterWaitForServer(self):
        self.notify.debug('enterWaitForServer()')
        return None

    def exitWaitForServer(self):
        return None

    def createAdjustInterval(self, av, destPos, destHpr, toon = 0, run = 0):
        if run == 1:
            adjustTime = self.calcToonMoveTime(destPos, av.getPos(self))
        else:
            adjustTime = self.calcSuitMoveTime(destPos, av.getPos(self))
        self.notify.debug('creating adjust interval for: %d' % av.doId)
        adjustTrack = Sequence()
        if run == 1:
            adjustTrack.append(Func(av.loop, 'run'))
        else:
            adjustTrack.append(Func(av.loop, 'walk'))
        adjustTrack.append(Func(av.headsUp, self, destPos))
        adjustTrack.append(LerpPosInterval(av, adjustTime, destPos, other=self))
        adjustTrack.append(Func(av.setHpr, self, destHpr))
        adjustTrack.append(Func(av.loop, 'neutral'))
        return adjustTrack

    def __adjust(self, ts, callback):
        self.notify.debug('__adjust(%f)' % ts)
        adjustTrack = Parallel()
        if len(self.pendingSuits) > 0 or self.suitGone == 1:
            self.suitGone = 0
            numSuits = len(self.pendingSuits) + len(self.activeSuits) - 1
            index = 0
            for suit in self.activeSuits:
                point = self.suitPoints[numSuits][index]
                pos = suit.getPos(self)
                destPos = point[0]
                if self.isSuitLured(suit) == 1:
                    destPos = Point3(destPos[0], destPos[1] - MovieUtil.SUIT_LURE_DISTANCE, destPos[2])
                if pos != destPos:
                    destHpr = VBase3(point[1], 0.0, 0.0)
                    adjustTrack.append(self.createAdjustInterval(suit, destPos, destHpr))
                index += 1

            for suit in self.pendingSuits:
                point = self.suitPoints[numSuits][index]
                destPos = point[0]
                destHpr = VBase3(point[1], 0.0, 0.0)
                adjustTrack.append(self.createAdjustInterval(suit, destPos, destHpr))
                index += 1

        if len(self.pendingToons) > 0 or self.toonGone == 1:
            self.toonGone = 0
            numToons = len(self.pendingToons) + len(self.activeToons) - 1
            index = 0
            for toon in self.activeToons:
                point = self.toonPoints[numToons][index]
                pos = toon.getPos(self)
                destPos = point[0]
                if pos != destPos:
                    destHpr = VBase3(point[1], 0.0, 0.0)
                    adjustTrack.append(self.createAdjustInterval(toon, destPos, destHpr))
                index += 1

            for toon in self.pendingToons:
                point = self.toonPoints[numToons][index]
                destPos = point[0]
                destHpr = VBase3(point[1], 0.0, 0.0)
                adjustTrack.append(self.createAdjustInterval(toon, destPos, destHpr))
                index += 1

        if len(adjustTrack) > 0:
            self.notify.debug('creating adjust multitrack')
            e = Func(self.__handleAdjustDone)
            track = Sequence(adjustTrack, e, name=self.adjustName)
            self.storeInterval(track, self.adjustName)
            track.start(ts)
            if ToontownBattleGlobals.SkipMovie:
                track.finish()
        else:
            self.notify.warning('adjust() - nobody needed adjusting')
            self.__adjustDone()

    def __handleAdjustDone(self):
        self.notify.debug('__handleAdjustDone() - client adjust finished')
        self.clearInterval(self.adjustName)
        self.__adjustDone()

    def __stopAdjusting(self):
        self.notify.debug('__stopAdjusting()')
        self.clearInterval(self.adjustName)
        if self.adjustFsm.getCurrentState().getName() == 'Adjusting':
            self.adjustFsm.request('NotAdjusting')

    def __requestAdjustTownBattle(self):
        self.notify.debug('__requestAdjustTownBattle() curstate = %s' % self.fsm.getCurrentState().getName())
        if self.fsm.getCurrentState().getName() == 'WaitForInput':
            self.__adjustTownBattle()
        else:
            self.needAdjustTownBattle = 1

    def __adjustTownBattle(self):
        self.notify.debug('__adjustTownBattle()')
        if self.localToonActive() and len(self.activeSuits) > 0:
            self.notify.debug('__adjustTownBattle() - adjusting town battle')
            luredSuits = []
            for suit in self.luredSuits:
                if suit not in self.activeSuits:
                    self.notify.error('lured suit not in self.activeSuits')
                luredSuits.append(self.activeSuits.index(suit))

            trappedSuits = []
            for suit in self.activeSuits:
                if suit.battleTrap != NO_TRAP:
                    trappedSuits.append(self.activeSuits.index(suit))

            self.townBattle.adjustCogsAndToons(self.activeSuits, luredSuits, trappedSuits, self.activeToons)
            if hasattr(self, 'townBattleAttacks'):
                self.townBattle.updateChosenAttacks(self.townBattleAttacks[0], self.townBattleAttacks[1], self.townBattleAttacks[2], self.townBattleAttacks[3])
        self.needAdjustTownBattle = 0

    def __adjustDone(self):
        self.notify.debug('__adjustDone()')
        if self.hasLocalToon():
            self.d_adjustDone(base.localAvatar.doId)
        self.adjustFsm.request('NotAdjusting')

    def enterAdjusting(self, ts):
        self.notify.debug('enterAdjusting()')
        if self.localToonActive():
            self.__stopTimer()
        self.delayDeleteMembers()
        self.__adjust(ts, self.__handleAdjustDone)
        return None

    def exitAdjusting(self):
        self.notify.debug('exitAdjusting()')
        self.finishInterval(self.adjustName)
        self._removeMembersKeep()
        currStateName = self.fsm.getCurrentState().getName()
        if currStateName == 'WaitForInput' and self.localToonActive():
            self.startTimer()
        return None

    def enterNotAdjusting(self):
        self.notify.debug('enterNotAdjusting()')
        return None

    def exitNotAdjusting(self):
        return None

    def visualize(self):
        try:
            self.isVisualized
        except:
            self.isVisualized = 0

        if self.isVisualized:
            self.vis.removeNode()
            del self.vis
            self.detachNode()
            self.isVisualized = 0
        else:
            lsegs = LineSegs()
            lsegs.setColor(0.5, 0.5, 1, 1)
            lsegs.moveTo(0, 0, 0)
            for p in BattleBase.allPoints:
                lsegs.drawTo(p[0], p[1], p[2])

            p = BattleBase.allPoints[0]
            lsegs.drawTo(p[0], p[1], p[2])
            self.vis = self.attachNewNode(lsegs.create())
            self.reparentTo(render)
            self.isVisualized = 1

    def setupCollisions(self, name):
        self.lockout = CollisionTube(0, 0, 0, 0, 0, 9, 9)
        lockoutNode = CollisionNode(name)
        lockoutNode.addSolid(self.lockout)
        lockoutNode.setCollideMask(ToontownGlobals.WallBitmask)
        self.lockoutNodePath = self.attachNewNode(lockoutNode)
        self.lockoutNodePath.detachNode()

    def removeCollisionData(self):
        del self.lockout
        self.lockoutNodePath.removeNode()
        del self.lockoutNodePath

    def enableCollision(self):
        self.lockoutNodePath.reparentTo(self)
        if len(self.toons) < 4:
            self.accept(self.getCollisionName(), self.__handleLocalToonCollision)

    def __handleLocalToonCollision(self, collEntry):
        self.notify.debug('localToonCollision')
        if self.fsm.getCurrentState().getName() == 'Off':
            self.notify.debug('ignoring collision in Off state')
            return
        if not base.localAvatar.wantBattles:
            return
        if self._skippingRewardMovie:
            return
        base.cr.playGame.getPlace().setState('WaitForBattle')
        toon = base.localAvatar
        self.d_toonRequestJoin(toon.doId, toon.getPos(self))
        base.localAvatar.preBattleHpr = base.localAvatar.getHpr(render)
        self.localToonFsm.request('WaitForServer')
        self.onWaitingForJoin()

    def onWaitingForJoin(self):
        pass

    def denyLocalToonJoin(self):
        self.notify.debug('denyLocalToonJoin()')
        place = self.cr.playGame.getPlace()
        if place.fsm.getCurrentState().getName() == 'WaitForBattle':
            place.setState('walk')
        self.localToonFsm.request('NoLocalToon')

    def disableCollision(self):
        self.ignore(self.getCollisionName())
        self.lockoutNodePath.detachNode()

    def openBattleCollision(self):
        if not self.hasLocalToon():
            self.enableCollision()

    def closeBattleCollision(self):
        self.ignore(self.getCollisionName())

    def getCollisionName(self):
        return 'enter' + self.lockoutNodePath.getName()
