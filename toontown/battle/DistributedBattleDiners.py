import random
from pandac.PandaModules import VBase3, Point3
from direct.interval.IntervalGlobal import Sequence, Wait, Func, Parallel, Track, LerpPosInterval, ProjectileInterval, SoundInterval, ActorInterval
from direct.directnotify import DirectNotifyGlobal
from toontown.battle import DistributedBattleFinal
from toontown.suit import SuitTimings
from toontown.toonbase import ToontownGlobals
from toontown.battle import BattleProps

class DistributedBattleDiners(DistributedBattleFinal.DistributedBattleFinal):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedBattleDiners')

    def __init__(self, cr):
        DistributedBattleFinal.DistributedBattleFinal.__init__(self, cr)
        self.initialReservesJoiningDone = False
        base.dbw = self

    def announceGenerate(self):
        DistributedBattleFinal.DistributedBattleFinal.announceGenerate(self)
        self.moveSuitsToInitialPos()

    def showSuitsJoining(self, suits, ts, name, callback):
        if len(suits) == 0 and not self.initialReservesJoiningDone:
            self.initialReservesJoiningDone = True
            self.doInitialSuitsJoining(ts, name, callback)
            return
        self.showSuitsFalling(suits, ts, name, callback)

    def doInitialSuitsJoining(self, ts, name, callback):
        done = Func(callback)
        if self.hasLocalToon():
            camera.reparentTo(self)
            if random.choice([0, 1]):
                camera.setPosHpr(20, -4, 7, 60, 0, 0)
            else:
                camera.setPosHpr(-20, -4, 7, -60, 0, 0)
        track = Sequence(Wait(0.5), done, name=name)
        track.start(ts)
        self.storeInterval(track, name)

    def moveSuitsToInitialPos(self):
        battlePts = self.suitPoints[len(self.suitPendingPoints) - 1]
        for i in xrange(len(self.suits)):
            suit = self.suits[i]
            suit.reparentTo(self)
            destPos, destHpr = self.getActorPosHpr(suit, self.suits)
            suit.setPos(destPos)
            suit.setHpr(destHpr)

    def showSuitsFalling(self, suits, ts, name, callback):
        if self.bossCog == None:
            return
        suitTrack = Parallel()
        delay = 0
        for suit in suits:
            suit.setState('Battle')
            if suit.dna.dept == 'l':
                suit.reparentTo(self.bossCog)
                suit.setPos(0, 0, 0)
            if suit in self.joiningSuits:
                i = len(self.pendingSuits) + self.joiningSuits.index(suit)
                destPos, h = self.suitPendingPoints[i]
                destHpr = VBase3(h, 0, 0)
            else:
                destPos, destHpr = self.getActorPosHpr(suit, self.suits)
            startPos = destPos + Point3(0, 0, SuitTimings.fromSky * ToontownGlobals.SuitWalkSpeed)
            self.notify.debug('startPos for %s = %s' % (suit, startPos))
            suit.reparentTo(self)
            suit.setPos(startPos)
            suit.headsUp(self)
            moveIval = Sequence()
            chairInfo = self.bossCog.claimOneChair()
            if chairInfo:
                moveIval = self.createDinerMoveIval(suit, destPos, chairInfo)
            suitTrack.append(Track((delay, Sequence(moveIval, Func(suit.loop, 'neutral')))))
            delay += 1

        if self.hasLocalToon():
            camera.reparentTo(self)
            self.notify.debug('self.battleSide =%s' % self.battleSide)
            camHeading = -20
            camX = -4
            if self.battleSide == 0:
                camHeading = 20
                camX = 4
            camera.setPosHpr(camX, -15, 7, camHeading, 0, 0)
        done = Func(callback)
        track = Sequence(suitTrack, done, name=name)
        track.start(ts)
        self.storeInterval(track, name)
        return

    def createDinerMoveIval(self, suit, destPos, chairInfo):
        dur = suit.getDuration('landing')
        fr = suit.getFrameRate('landing')
        landingDur = dur
        totalDur = 7.3
        animTimeInAir = totalDur - dur
        flyingDur = animTimeInAir
        impactLength = dur - animTimeInAir
        tableIndex = chairInfo[0]
        chairIndex = chairInfo[1]
        table = self.bossCog.tables[tableIndex]
        chairLocator = table.chairLocators[chairIndex]
        chairPos = chairLocator.getPos(self)
        chairHpr = chairLocator.getHpr(self)
        suit.setPos(chairPos)
        table.setDinerStatus(chairIndex, table.HIDDEN)
        suit.setHpr(chairHpr)
        wayPoint = (chairPos + destPos) / 2.0
        wayPoint.setZ(wayPoint.getZ() + 20)
        moveIval = Sequence(Func(suit.headsUp, self), Func(suit.pose, 'landing', 0), ProjectileInterval(suit, duration=flyingDur, startPos=chairPos, endPos=destPos, gravityMult=0.25), ActorInterval(suit, 'landing'))
        if suit.prop == None:
            suit.prop = BattleProps.globalPropPool.getProp('propeller')
        propDur = suit.prop.getDuration('propeller')
        lastSpinFrame = 8
        fr = suit.prop.getFrameRate('propeller')
        spinTime = lastSpinFrame / fr
        openTime = (lastSpinFrame + 1) / fr
        suit.attachPropeller()
        propTrack = Parallel(SoundInterval(suit.propInSound, duration=flyingDur, node=suit), Sequence(ActorInterval(suit.prop, 'propeller', constrainedLoop=1, duration=flyingDur + 1, startTime=0.0, endTime=spinTime), ActorInterval(suit.prop, 'propeller', duration=landingDur, startTime=openTime), Func(suit.detachPropeller)))
        result = Parallel(moveIval, propTrack)
        return result
