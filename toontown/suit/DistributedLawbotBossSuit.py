from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from direct.directnotify import DirectNotifyGlobal
from . import DistributedSuitBase
from toontown.toonbase import ToontownGlobals
from toontown.battle import MovieUtil

class DistributedLawbotBossSuit(DistributedSuitBase.DistributedSuitBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedLawbotBossSuit')
    timeToShow = 1.0
    timeToRelease = 3.15
    throwPaperEndTime = 4.33

    def __init__(self, cr):
        self.flyingEvidenceTrack = None
        try:
            self.DistributedSuit_initialized
        except:
            self.DistributedSuit_initialized = 1
            DistributedSuitBase.DistributedSuitBase.__init__(self, cr)
            self.activeIntervals = {}
            self.boss = None
            self.fsm = ClassicFSM.ClassicFSM('DistributedLawbotBossSuit', [
                State.State('Off',
                            self.enterOff,
                            self.exitOff, [
                                'Walk',
                                'Battle',
                                'neutral']),
                State.State('Walk',
                            self.enterWalk,
                            self.exitWalk, [
                                'WaitForBattle',
                                'Battle']),
                State.State('Battle',
                            self.enterBattle,
                            self.exitBattle, []),
                State.State('neutral',
                            self.enterNeutral,
                            self.exitNeutral, [
                                'PreThrowProsecute',
                                'PreThrowAttack',
                                'Stunned']),
                State.State('PreThrowProsecute',
                            self.enterPreThrowProsecute,
                            self.exitPreThrowProsecute,
                            ['PostThrowProsecute',
                             'neutral',
                             'Stunned']),
                State.State('PostThrowProsecute',
                            self.enterPostThrowProsecute,
                            self.exitPostThrowProsecute, [
                                'neutral',
                                'Stunned']),
                State.State('PreThrowAttack',
                            self.enterPreThrowAttack,
                            self.exitPreThrowAttack, [
                                'PostThrowAttack',
                                'neutral',
                                'Stunned']),
                State.State('PostThrowAttack',
                            self.enterPostThrowAttack,
                            self.exitPostThrowAttack, [
                                'neutral',
                                'Stunned']),
                State.State('Stunned',
                            self.enterStunned,
                            self.exitStunned, [
                                'neutral']),
                State.State('WaitForBattle',
                            self.enterWaitForBattle,
                            self.exitWaitForBattle, [
                                'Battle'])],
                'Off', 'Off')
            self.fsm.enterInitialState()

        return

    def generate(self):
        self.notify.debug('DLBS.generate:')
        DistributedSuitBase.DistributedSuitBase.generate(self)

    def announceGenerate(self):
        DistributedSuitBase.DistributedSuitBase.announceGenerate(self)
        self.notify.debug('DLBS.announceGenerate')
        colNode = self.find('**/distAvatarCollNode*')
        colNode.setTag('pieCode', str(ToontownGlobals.PieCodeLawyer))
        self.attackEvidenceA = self.getEvidence(True)
        self.attackEvidenceB = self.getEvidence(True)
        self.attackEvidence = self.attackEvidenceA
        self.prosecuteEvidence = self.getEvidence(False)
        self.hideName()
        self.setPickable(False)

    def disable(self):
        self.notify.debug('DistributedSuit %d: disabling' % self.getDoId())
        self.setState('Off')
        DistributedSuitBase.DistributedSuitBase.disable(self)
        self.cleanupIntervals()
        self.boss = None
        return

    def delete(self):
        try:
            self.DistributedSuit_deleted
        except:
            self.DistributedSuit_deleted = 1
            self.notify.debug('DistributedSuit %d: deleting' % self.getDoId())
            del self.fsm
            DistributedSuitBase.DistributedSuitBase.delete(self)

    def d_requestBattle(self, pos, hpr):
        self.cr.playGame.getPlace().setState('WaitForBattle')
        self.sendUpdate('requestBattle', [pos[0],
         pos[1],
         pos[2],
         hpr[0],
         hpr[1],
         hpr[2]])
        return None

    def __handleToonCollision(self, collEntry):
        toonId = base.localAvatar.getDoId()
        self.notify.debug('Distributed suit: requesting a Battle with ' + 'toon: %d' % toonId)
        self.d_requestBattle(self.getPos(), self.getHpr())
        self.setState('WaitForBattle')
        return None

    def enterWalk(self):
        self.notify.debug('enterWalk')
        self.enableBattleDetect('walk', self.__handleToonCollision)
        self.loop('walk', 0)
        pathPoints = [Vec3(50, 15, 0),
         Vec3(50, 25, 0),
         Vec3(20, 25, 0),
         Vec3(20, 15, 0),
         Vec3(50, 15, 0)]
        self.tutWalkTrack = self.makePathTrack(self, pathPoints, 4.5, 'tutFlunkyWalk')
        self.tutWalkTrack.loop()

    def exitWalk(self):
        self.notify.debug('exitWalk')
        self.disableBattleDetect()
        self.tutWalkTrack.pause()
        self.tutWalkTrack = None
        return

    def enterNeutral(self):
        self.notify.debug('enterNeutral')
        self.notify.debug('DistributedLawbotBossSuit: Neutral')
        self.loop('neutral', 0)

    def exitNeutral(self):
        self.notify.debug('exitNeutral')

    def doAttack(self, x1, y1, z1, x2, y2, z2):
        self.notify.debug('x1=%.2f y1=%.2f z2=%.2f x2=%.2f y2=%.2f z2=%.2f' % (x1,
         y1,
         z1,
         x2,
         y2,
         z2))
        self.curTargetPt = Point3(x2, y2, z2)
        self.fsm.request('PreThrowAttack')
        return
        attackEvidence = self.getEvidence(True)
        nodePath = render
        node = nodePath.attachNewNode('attackEvidence-%s' % self.doId)
        node.setPos(x1, y1, z1)
        duration = 3.0
        throwName = self.uniqueName('lawyerAttack')
        throwingSeq = self.makeAttackThrowingTrack(attackEvidence, duration, Point3(x2, y2, z2))
        fullSequence = Sequence(throwingSeq, name=throwName)
        self.activeIntervals[throwName] = fullSequence
        fullSequence.start()

    def doProsecute(self):
        self.notify.debug('doProsecute')
        bounds = self.boss.prosecutionColNodePath.getBounds()
        panCenter = bounds.getCenter()
        localPos = panCenter
        prosecutionPanPos = render.getRelativePoint(self.boss.prosecutionColNodePath, localPos)
        self.curTargetPt = prosecutionPanPos
        self.fsm.request('PreThrowProsecute')
        return
        attackEvidence = self.getEvidence(False)
        nodePath = render
        node = nodePath.attachNewNode('prosecuteEvidence-%s' % self.doId)
        node.setPos(self.getPos())
        duration = ToontownGlobals.LawbotBossLawyerToPanTime
        throwName = self.uniqueName('lawyerProsecute')
        throwingSeq = self.makeProsecuteThrowingTrack(attackEvidence, duration, prosecutionPanPos)
        fullSequence = Sequence(throwingSeq, Func(self.boss.flashGreen), Func(self.clearInterval, throwName), name=throwName)
        self.activeIntervals[throwName] = fullSequence
        fullSequence.start()

    def makeDummySequence(self):
        retval = Sequence(Wait(10))
        return retval

    def makeProsecuteThrowingTrack(self, evidence, inFlightDuration, hitPos):
        suitTrack = Sequence()
        suitTrack.append(ActorInterval(self, 'throw-paper'))
        throwPaperDuration = suitTrack.getDuration()
        inFlight = Parallel(evidence.posInterval(inFlightDuration, hitPos, fluid=1))
        origHpr = self.getHpr()
        self.headsUp(hitPos)
        newHpr = self.getHpr()
        self.setHpr(origHpr)
        rotateTrack = Sequence(self.hprInterval(self.timeToShow, newHpr, fluid=1))
        propTrack = Sequence(Func(evidence.hide), Func(evidence.setPos, 0, 0.5, -0.3), Func(evidence.reparentTo, self.getRightHand()), Wait(self.timeToShow), Func(evidence.show), Wait(self.timeToRelease - self.timeToShow), Func(evidence.wrtReparentTo, render), Func(self.makeDummySequence), inFlight, Func(evidence.detachNode))
        throwingTrack = Parallel(suitTrack, propTrack, rotateTrack)
        return throwingTrack

    def makeAttackThrowingTrack(self, evidence, inFlightDuration, hitPos):
        suitTrack = Sequence()
        suitTrack.append(ActorInterval(self, 'throw-paper'))
        throwPaperDuration = suitTrack.getDuration()
        origHpr = self.getHpr()
        self.headsUp(hitPos)
        newHpr = self.getHpr()
        self.setHpr(origHpr)
        rotateTrack = Sequence(self.hprInterval(self.timeToShow, newHpr, fluid=1))
        propTrack = Sequence(Func(evidence.hide), Func(evidence.setPos, 0, 0.5, -0.3), Func(evidence.reparentTo, self.getRightHand()), Wait(self.timeToShow), Func(evidence.show), Wait(self.timeToRelease - self.timeToShow), Func(evidence.wrtReparentTo, render), Func(evidence.setZ, 1.3), evidence.posInterval(inFlightDuration, hitPos, fluid=1), Func(evidence.detachNode))
        throwingTrack = Parallel(suitTrack, propTrack, rotateTrack)
        return throwingTrack

    def makePreThrowAttackTrack(self, evidence, inFlightDuration, hitPos):
        suitTrack = Sequence()
        suitTrack.append(ActorInterval(self, 'throw-paper', endTime=self.timeToRelease))
        throwPaperDuration = suitTrack.getDuration()
        origHpr = self.getHpr()
        self.headsUp(hitPos)
        newHpr = self.getHpr()
        self.setHpr(origHpr)
        rotateTrack = Sequence(self.hprInterval(self.timeToShow, newHpr, fluid=1))
        propTrack = Sequence(Func(evidence.hide), Func(evidence.setPos, 0, 0.5, -0.3), Func(evidence.setScale, 1), Func(evidence.setHpr, 0, 0, 0), Func(evidence.reparentTo, self.getRightHand()), Wait(self.timeToShow), Func(evidence.show), Wait(self.timeToRelease - self.timeToShow))
        throwingTrack = Parallel(suitTrack, propTrack, rotateTrack)
        return throwingTrack

    def makePostThrowAttackTrack(self, evidence, inFlightDuration, hitPos):
        suitTrack = Sequence()
        suitTrack.append(ActorInterval(self, 'throw-paper', startTime=self.timeToRelease))
        propTrack = Sequence(Func(evidence.wrtReparentTo, render), Func(evidence.setScale, 1), Func(evidence.show), Func(evidence.setZ, 1.3), evidence.posInterval(inFlightDuration, hitPos, fluid=1), Func(evidence.hide))
        return (suitTrack, propTrack)

    def makePreThrowProsecuteTrack(self, evidence, inFlightDuration, hitPos):
        return self.makePreThrowAttackTrack(evidence, inFlightDuration, hitPos)

    def makePostThrowProsecuteTrack(self, evidence, inFlightDuration, hitPos):
        suitTrack = Sequence()
        suitTrack.append(ActorInterval(self, 'throw-paper', startTime=self.timeToRelease))
        propTrack = Sequence(Func(evidence.wrtReparentTo, render), Func(evidence.setScale, 1), Func(evidence.show), evidence.posInterval(inFlightDuration, hitPos, fluid=1), Func(evidence.hide))
        return (suitTrack, propTrack)

    def getEvidence(self, usedForAttack = False):
        model = loader.loadModel('phase_5/models/props/lawbook')
        if usedForAttack:
            bounds = model.getBounds()
            center = bounds.getCenter()
            radius = bounds.getRadius()
            sphere = CollisionSphere(center.getX(), center.getY(), center.getZ(), radius)
            colNode = CollisionNode('BossZap')
            colNode.setTag('attackCode', str(ToontownGlobals.BossCogLawyerAttack))
            colNode.addSolid(sphere)
            model.attachNewNode(colNode)
            model.setTransparency(1)
            model.setAlphaScale(0.5)
        return model

    def cleanupIntervals(self):
        for interval in list(self.activeIntervals.values()):
            interval.finish()

        self.activeIntervals = {}

    def clearInterval(self, name, finish = 1):
        if name in self.activeIntervals:
            ival = self.activeIntervals[name]
            if finish:
                ival.finish()
            else:
                ival.pause()
            if name in self.activeIntervals:
                del self.activeIntervals[name]
        else:
            self.notify.debug('interval: %s already cleared' % name)

    def setBossCogId(self, bossCogId):
        self.bossCogId = bossCogId
        self.boss = base.cr.doId2do[bossCogId]

    def doStun(self):
        self.notify.debug('doStun')
        self.fsm.request('Stunned')

    def enterPreThrowProsecute(self):
        duration = ToontownGlobals.LawbotBossLawyerToPanTime
        throwName = self.uniqueName('preThrowProsecute')
        preThrowTrack = self.makePreThrowProsecuteTrack(self.prosecuteEvidence, duration, self.curTargetPt)
        fullSequence = Sequence(preThrowTrack, Func(self.requestStateIfNotInFlux, 'PostThrowProsecute'), name=throwName)
        self.activeIntervals[throwName] = fullSequence
        fullSequence.start()

    def exitPreThrowProsecute(self):
        throwName = self.uniqueName('preThrowProsecute')
        if throwName in self.activeIntervals:
            self.activeIntervals[throwName].pause()
            del self.activeIntervals[throwName]

    def enterPostThrowProsecute(self):
        duration = ToontownGlobals.LawbotBossLawyerToPanTime
        throwName = self.uniqueName('postThrowProsecute')
        postThrowTrack, self.flyingEvidenceTrack = self.makePostThrowProsecuteTrack(self.prosecuteEvidence, duration, self.curTargetPt)
        fullSequence = Sequence(postThrowTrack, Func(self.requestStateIfNotInFlux, 'neutral'), name=throwName)
        self.activeIntervals[throwName] = fullSequence
        fullSequence.start()
        flyName = self.uniqueName('flyingEvidence')
        self.activeIntervals[flyName] = self.flyingEvidenceTrack
        self.flyingEvidenceTrack.append(Func(self.finishedWithFlying, 'prosecute'))
        self.flyingEvidenceTrack.start()

    def exitPostThrowProsecute(self):
        throwName = self.uniqueName('postThrowProsecute')
        if throwName in self.activeIntervals:
            self.activeIntervals[throwName].finish()
            del self.activeIntervals[throwName]

    def requestStateIfNotInFlux(self, state):
        if not self.fsm._ClassicFSM__internalStateInFlux:
            self.fsm.request(state)

    def enterPreThrowAttack(self):
        if self.attackEvidence == self.attackEvidenceA:
            self.attackEvidence = self.attackEvidenceB
        else:
            self.attackEvidence = self.attackEvidenceA
        duration = 3.0
        throwName = self.uniqueName('preThrowAttack')
        preThrowTrack = self.makePreThrowAttackTrack(self.attackEvidence, duration, self.curTargetPt)
        fullSequence = Sequence(preThrowTrack, Func(self.requestStateIfNotInFlux, 'PostThrowAttack'), name=throwName)
        self.activeIntervals[throwName] = fullSequence
        fullSequence.start()

    def exitPreThrowAttack(self):
        throwName = self.uniqueName('preThrowAttack')
        if throwName in self.activeIntervals:
            self.activeIntervals[throwName].pause()
            del self.activeIntervals[throwName]

    def enterPostThrowAttack(self):
        duration = 3.0
        throwName = self.uniqueName('postThrowAttack')
        postThrowTrack, self.flyingEvidenceTrack = self.makePostThrowAttackTrack(self.attackEvidence, duration, self.curTargetPt)
        fullSequence = Sequence(postThrowTrack, Func(self.requestStateIfNotInFlux, 'neutral'), name=throwName)
        self.notify.debug('duration of postThrowAttack = %f' % fullSequence.getDuration())
        self.activeIntervals[throwName] = fullSequence
        fullSequence.start()
        flyName = self.uniqueName('flyingEvidence')
        self.activeIntervals[flyName] = self.flyingEvidenceTrack
        self.flyingEvidenceTrack.append(Func(self.finishedWithFlying, 'attack'))
        self.flyingEvidenceTrack.start()

    def finishedWithFlying(self, str):
        self.notify.debug('finished flyingEvidenceTrack %s' % str)

    def exitPostThrowAttack(self):
        throwName = self.uniqueName('postThrowAttack')
        if throwName in self.activeIntervals:
            self.activeIntervals[throwName].finish()
            del self.activeIntervals[throwName]

    def enterStunned(self):
        stunSequence = MovieUtil.createSuitStunInterval(self, 0, ToontownGlobals.LawbotBossLawyerStunTime)
        seqName = stunSequence.getName()
        stunSequence.append(Func(self.fsm.request, 'neutral'))
        self.activeIntervals[seqName] = stunSequence
        stunSequence.start()

    def exitStunned(self):
        self.prosecuteEvidence.hide()
        self.attackEvidence.hide()
