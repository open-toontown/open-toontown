import math
from direct.showbase.DirectObject import DirectObject
from direct.directnotify import DirectNotifyGlobal
from direct.fsm.FSM import FSM
from direct.task.Task import Task
from direct.interval.IntervalGlobal import Sequence, Parallel, LerpScaleInterval, LerpFunctionInterval, Func, Wait, LerpFunc, SoundInterval, ParallelEndTogether, LerpPosInterval, ActorInterval, LerpPosHprInterval, LerpHprInterval
from direct.directutil import Mopath
from direct.showbase.PythonUtil import bound as clamp
from pandac.PandaModules import CollisionSphere, CollisionNode, CollisionTube, CollisionPolygon, Vec3, Point3
from toontown.suit import Suit
from toontown.suit import SuitDNA
from toontown.toonbase import ToontownGlobals
from toontown.battle import BattleProps
from .CogdoFlyingUtil import swapAvatarShadowPlacer
from . import CogdoUtil
from . import CogdoFlyingGameGlobals as Globals

class CogdoFlyingLegalEagle(FSM, DirectObject):
    CollSphereName = 'CogdoFlyingLegalEagleSphere'
    CollisionEventName = 'CogdoFlyingLegalEagleCollision'
    InterestCollName = 'CogdoFlyingLegalEagleInterestCollision'
    RequestAddTargetEventName = 'CogdoFlyingLegalEagleRequestTargetEvent'
    RequestAddTargetAgainEventName = 'CogdoFlyingLegalEagleRequestTargetAgainEvent'
    RequestRemoveTargetEventName = 'CogdoFlyingLegalEagleRemoveTargetEvent'
    ForceRemoveTargetEventName = 'CogdoFlyingLegalEagleForceRemoveTargetEvent'
    EnterLegalEagle = 'CogdoFlyingLegalEagleDamageToon'
    ChargingToAttackEventName = 'LegalEagleChargingToAttack'
    LockOnToonEventName = 'LegalEagleLockOnToon'
    CooldownEventName = 'LegalEagleCooldown'
    notify = DirectNotifyGlobal.directNotify.newCategory('CogdoFlyingLegalEagle')

    def __init__(self, nest, index, suitDnaName = 'le'):
        FSM.__init__(self, 'CogdoFlyingLegalEagle')
        self.defaultTransitions = {'Off': ['Roost'],
         'Roost': ['TakeOff', 'Off'],
         'TakeOff': ['LockOnToon', 'LandOnNest', 'Off'],
         'LockOnToon': ['RetreatToNest', 'ChargeUpAttack', 'Off'],
         'ChargeUpAttack': ['RetreatToNest', 'Attack', 'Off'],
         'Attack': ['RetreatToSky', 'Off'],
         'RetreatToSky': ['Cooldown', 'Off'],
         'Cooldown': ['LockOnToon', 'LandOnNest', 'Off'],
         'RetreatToNest': ['LandOnNest', 'Off'],
         'LandOnNest': ['Roost', 'Off']}
        self.index = index
        self.nest = nest
        self.target = None
        self.isEagleInterested = False
        self.collSphere = None
        self.suit = Suit.Suit()
        d = SuitDNA.SuitDNA()
        d.newSuit(suitDnaName)
        self.suit.setDNA(d)
        self.suit.reparentTo(render)
        swapAvatarShadowPlacer(self.suit, 'legalEagle-%sShadowPlacer' % index)
        self.suit.setPos(self.nest.getPos(render))
        self.suit.setHpr(-180, 0, 0)
        self.suit.stash()
        self.prop = None
        self.attachPropeller()
        head = self.suit.find('**/joint_head')
        self.interestConeOrigin = self.nest.attachNewNode('fakeHeadNodePath')
        self.interestConeOrigin.setPos(render, head.getPos(render) + Vec3(0, Globals.LegalEagle.InterestConeOffset, 0))
        self.attackTargetPos = None
        self.startOfRetreatToSkyPos = None
        pathModel = CogdoUtil.loadFlyingModel('legalEaglePaths')
        self.chargeUpMotionPath = Mopath.Mopath(name='chargeUpMotionPath-%i' % self.index)
        self.chargeUpMotionPath.loadNodePath(pathModel.find('**/charge_path'))
        self.retreatToSkyMotionPath = Mopath.Mopath(name='retreatToSkyMotionPath-%i' % self.index)
        self.retreatToSkyMotionPath.loadNodePath(pathModel.find('**/retreat_path'))
        audioMgr = base.cogdoGameAudioMgr
        self._screamSfx = audioMgr.createSfx('legalEagleScream', self.suit)
        self.initIntervals()
        return

    def attachPropeller(self):
        if self.prop == None:
            self.prop = BattleProps.globalPropPool.getProp('propeller')
            head = self.suit.find('**/joint_head')
            self.prop.reparentTo(head)
        return

    def detachPropeller(self):
        if self.prop:
            self.prop.cleanup()
            self.prop.removeNode()
            self.prop = None
        return

    def _getAnimationIval(self, animName, startFrame = 0, endFrame = None, duration = 1):
        if endFrame == None:
            self.suit.getNumFrames(animName) - 1
        frames = endFrame - startFrame
        frameRate = self.suit.getFrameRate(animName)
        newRate = frames / duration
        playRate = newRate / frameRate
        ival = Sequence(ActorInterval(self.suit, animName, playRate=playRate))
        return ival

    def initIntervals(self):
        dur = Globals.LegalEagle.LiftOffTime
        nestPos = self.nest.getPos(render)
        airPos = nestPos + Vec3(0.0, 0.0, Globals.LegalEagle.LiftOffHeight)
        self.takeOffSeq = Sequence(Parallel(Sequence(Wait(dur * 0.6), LerpPosInterval(self.suit, dur * 0.4, startPos=nestPos, pos=airPos, blendType='easeInOut'))), Wait(1.5), Func(self.request, 'next'), name='%s.takeOffSeq-%i' % (self.__class__.__name__, self.index))
        self.landOnNestPosLerp = LerpPosInterval(self.suit, 1.0, startPos=airPos, pos=nestPos, blendType='easeInOut')
        self.landingSeq = Sequence(Func(self.updateLandOnNestPosLerp), Parallel(self.landOnNestPosLerp), Func(self.request, 'next'), name='%s.landingSeq-%i' % (self.__class__.__name__, self.index))
        dur = Globals.LegalEagle.ChargeUpTime
        self.chargeUpPosLerp = LerpFunc(self.moveAlongChargeUpMopathFunc, fromData=0.0, toData=self.chargeUpMotionPath.getMaxT(), duration=dur, blendType='easeInOut')
        self.chargeUpAttackSeq = Sequence(Func(self.updateChargeUpPosLerp), self.chargeUpPosLerp, Func(self.request, 'next'), name='%s.chargeUpAttackSeq-%i' % (self.__class__.__name__, self.index))
        dur = Globals.LegalEagle.RetreatToNestTime
        self.retreatToNestPosLerp = LerpPosInterval(self.suit, dur, startPos=Vec3(0, 0, 0), pos=airPos, blendType='easeInOut')
        self.retreatToNestSeq = Sequence(Func(self.updateRetreatToNestPosLerp), self.retreatToNestPosLerp, Func(self.request, 'next'), name='%s.retreatToNestSeq-%i' % (self.__class__.__name__, self.index))
        dur = Globals.LegalEagle.RetreatToSkyTime
        self.retreatToSkyPosLerp = LerpFunc(self.moveAlongRetreatMopathFunc, fromData=0.0, toData=self.retreatToSkyMotionPath.getMaxT(), duration=dur, blendType='easeOut')
        self.retreatToSkySeq = Sequence(Func(self.updateRetreatToSkyPosLerp), self.retreatToSkyPosLerp, Func(self.request, 'next'), name='%s.retreatToSkySeq-%i' % (self.__class__.__name__, self.index))
        dur = Globals.LegalEagle.PreAttackTime
        self.preAttackLerpXY = LerpFunc(self.updateAttackXY, fromData=0.0, toData=1.0, duration=dur)
        self.preAttackLerpZ = LerpFunc(self.updateAttackZ, fromData=0.0, toData=1.0, duration=dur, blendType='easeOut')
        dur = Globals.LegalEagle.PostAttackTime
        self.postAttackPosLerp = LerpPosInterval(self.suit, dur, startPos=Vec3(0, 0, 0), pos=Vec3(0, 0, 0))
        self.attackSeq = Sequence(Parallel(self.preAttackLerpXY, self.preAttackLerpZ), Func(self.updatePostAttackPosLerp), self.postAttackPosLerp, Func(self.request, 'next'), name='%s.attackSeq-%i' % (self.__class__.__name__, self.index))
        dur = Globals.LegalEagle.CooldownTime
        self.cooldownSeq = Sequence(Wait(dur), Func(self.request, 'next'), name='%s.cooldownSeq-%i' % (self.__class__.__name__, self.index))
        self.propTrack = Sequence(ActorInterval(self.prop, 'propeller', startFrame=0, endFrame=14))
        self.hoverOverNestSeq = Sequence(ActorInterval(self.suit, 'landing', startFrame=10, endFrame=20, playRate=0.5), ActorInterval(self.suit, 'landing', startFrame=20, endFrame=10, playRate=0.5))

    def initCollision(self):
        self.collSphere = CollisionSphere(0, 0, 0, 0)
        self.collSphere.setTangible(0)
        self.collNode = CollisionNode('%s-%s' % (self.CollSphereName, self.index))
        self.collNode.setIntoCollideMask(ToontownGlobals.WallBitmask)
        self.collNode.addSolid(self.collSphere)
        self.collNodePath = self.suit.attachNewNode(self.collNode)
        self.collNodePath.hide()
        self.accept('enter%s-%s' % (self.CollSphereName, self.index), self.handleEnterSphere)
        self.setCollSphereToNest()

    def getInterestConeLength(self):
        return Globals.LegalEagle.InterestConeLength + Globals.LegalEagle.InterestConeOffset

    def isToonInView(self, toon):
        distanceThreshold = self.getInterestConeLength()
        angleThreshold = Globals.LegalEagle.InterestConeAngle
        toonPos = toon.getPos(render)
        nestPos = self.nest.getPos(render)
        distance = toon.getDistance(self.interestConeOrigin)
        if distance > distanceThreshold:
            return False
        if toonPos[1] > nestPos[1]:
            return False
        a = toon.getPos(render) - self.interestConeOrigin.getPos(render)
        a.normalize()
        b = Vec3(0, -1, 0)
        dotProduct = a.dot(b)
        angle = math.degrees(math.acos(dotProduct))
        if angle <= angleThreshold / 2.0:
            return True
        else:
            return False

    def update(self, dt, localPlayer):
        if Globals.Dev.NoLegalEagleAttacks:
            return
        inView = self.isToonInView(localPlayer.toon)
        if inView and not self.isEagleInterested:
            self.handleEnterInterest()
        elif inView and self.isEagleInterested:
            self.handleAgainInterest()
        elif not inView and self.isEagleInterested:
            self.handleExitInterest()

    def updateLockOnTask(self):
        dt = globalClock.getDt()
        targetPos = self.target.getPos(render)
        suitPos = self.suit.getPos(render)
        nestPos = self.nest.getPos(render)
        attackPos = Vec3(targetPos)
        attackPos[1] = nestPos[1] + Globals.LegalEagle.LockOnDistanceFromNest
        attackPos[2] += Globals.LegalEagle.VerticalOffset
        if attackPos[2] < nestPos[2]:
            attackPos[2] = nestPos[2]
        attackChangeVec = (attackPos - suitPos) * Globals.LegalEagle.LockOnSpeed
        self.suit.setPos(suitPos + attackChangeVec * dt)
        return Task.cont

    def updateAttackXY(self, value):
        if Globals.LegalEagle.EagleAttackShouldXCorrect:
            x = self.readyToAttackPos.getX() + (self.attackTargetPos.getX() - self.readyToAttackPos.getX()) * value
            self.suit.setX(x)
        y = self.readyToAttackPos.getY() + (self.attackTargetPos.getY() - self.readyToAttackPos.getY()) * value
        self.suit.setY(y)

    def updateAttackZ(self, value):
        z = self.readyToAttackPos.getZ() + (self.attackTargetPos.getZ() - self.readyToAttackPos.getZ()) * value
        self.suit.setZ(z)

    def moveAlongChargeUpMopathFunc(self, value):
        self.chargeUpMotionPath.goTo(self.suit, value)
        self.suit.setPos(self.suit.getPos() + self.startOfChargeUpPos)

    def moveAlongRetreatMopathFunc(self, value):
        self.retreatToSkyMotionPath.goTo(self.suit, value)
        self.suit.setPos(self.suit.getPos() + self.startOfRetreatToSkyPos)

    def updateChargeUpPosLerp(self):
        self.startOfChargeUpPos = self.suit.getPos(render)

    def updateLandOnNestPosLerp(self):
        self.landOnNestPosLerp.setStartPos(self.suit.getPos())

    def updateRetreatToNestPosLerp(self):
        self.retreatToNestPosLerp.setStartPos(self.suit.getPos())

    def updateRetreatToSkyPosLerp(self):
        self.startOfRetreatToSkyPos = self.suit.getPos(render)

    def updatePostAttackPosLerp(self):
        suitPos = self.suit.getPos(render)
        finalPos = suitPos + Vec3(0, -Globals.LegalEagle.PostAttackLength, 0)
        self.postAttackPosLerp.setStartPos(suitPos)
        self.postAttackPosLerp.setEndPos(finalPos)

    def handleEnterSphere(self, collEntry):
        self.notify.debug('handleEnterSphere:%i' % self.index)
        messenger.send(CogdoFlyingLegalEagle.EnterLegalEagle, [self, collEntry])

    def handleEnterInterest(self):
        self.notify.debug('handleEnterInterestColl:%i' % self.index)
        self.isEagleInterested = True
        messenger.send(CogdoFlyingLegalEagle.RequestAddTargetEventName, [self.index])

    def handleAgainInterest(self):
        self.isEagleInterested = True
        messenger.send(CogdoFlyingLegalEagle.RequestAddTargetAgainEventName, [self.index])

    def handleExitInterest(self):
        self.notify.debug('handleExitInterestSphere:%i' % self.index)
        self.isEagleInterested = False
        messenger.send(CogdoFlyingLegalEagle.RequestRemoveTargetEventName, [self.index])

    def hasTarget(self):
        if self.target != None:
            return True
        else:
            return False
        return

    def setTarget(self, toon, elapsedTime = 0.0):
        self.notify.debug('Setting eagle %i to target: %s, elapsed time: %s' % (self.index, toon.getName(), elapsedTime))
        self.target = toon
        if self.state == 'Roost':
            self.request('next', elapsedTime)
        if self.state == 'ChargeUpAttack':
            messenger.send(CogdoFlyingLegalEagle.ChargingToAttackEventName, [self.target.doId])

    def clearTarget(self, elapsedTime = 0.0):
        self.notify.debug('Clearing target from eagle %i, elapsed time: %s' % (self.index, elapsedTime))
        messenger.send(CogdoFlyingLegalEagle.CooldownEventName, [self.target.doId])
        self.target = None
        if self.state in ['LockOnToon']:
            self.request('next', elapsedTime)
        return

    def leaveCooldown(self, elapsedTime = 0.0):
        if self.state in ['Cooldown']:
            self.request('next', elapsedTime)

    def shouldBeInFrame(self):
        if self.state in ['TakeOff', 'LockOnToon', 'ChargeUpAttack']:
            return True
        elif self.state == 'Attack':
            distance = self.suit.getDistance(self.target)
            threshold = Globals.LegalEagle.EagleAndTargetDistCameraTrackThreshold
            suitPos = self.suit.getPos(render)
            targetPos = self.target.getPos(render)
            if distance > threshold and suitPos[1] > targetPos[1]:
                return True
        return False

    def getTarget(self):
        return self.target

    def onstage(self):
        self.suit.unstash()
        self.request('Roost')

    def offstage(self):
        self.suit.stash()
        self.request('Off')

    def gameStart(self, gameStartTime):
        self.gameStartTime = gameStartTime
        self.initCollision()

    def gameEnd(self):
        self.shutdownCollisions()

    def shutdownCollisions(self):
        self.ignoreAll()
        if self.collSphere != None:
            del self.collSphere
            self.collSphere = None
        if self.collNodePath != None:
            self.collNodePath.removeNode()
            del self.collNodePath
            self.collNodePath = None
        if self.collNode != None:
            del self.collNode
            self.collNode = None
        return

    def destroy(self):
        self.request('Off')
        self.detachPropeller()
        del self._screamSfx
        self.suit.cleanup()
        self.suit.removeNode()
        self.suit.delete()
        self.interestConeOrigin.removeNode()
        del self.interestConeOrigin
        self.nest = None
        self.target = None
        taskMgr.remove('updateLockOnTask-%i' % self.index)
        taskMgr.remove('exitLockOnToon-%i' % self.index)
        self.propTrack.clearToInitial()
        del self.propTrack
        del self.chargeUpMotionPath
        del self.retreatToSkyMotionPath
        self.takeOffSeq.clearToInitial()
        del self.takeOffSeq
        del self.landOnNestPosLerp
        self.landingSeq.clearToInitial()
        del self.landingSeq
        del self.chargeUpPosLerp
        self.chargeUpAttackSeq.clearToInitial()
        del self.chargeUpAttackSeq
        del self.retreatToNestPosLerp
        self.retreatToNestSeq.clearToInitial()
        del self.retreatToNestSeq
        del self.retreatToSkyPosLerp
        self.retreatToSkySeq.clearToInitial()
        del self.retreatToSkySeq
        del self.postAttackPosLerp
        self.attackSeq.clearToInitial()
        del self.attackSeq
        self.cooldownSeq.clearToInitial()
        del self.cooldownSeq
        self.hoverOverNestSeq.clearToInitial()
        del self.hoverOverNestSeq
        del self.preAttackLerpXY
        del self.preAttackLerpZ
        return

    def requestNext(self):
        self.request('next')

    def setCollSphereToNest(self):
        if hasattr(self, 'collSphere') and self.collSphere is not None:
            radius = Globals.LegalEagle.OnNestDamageSphereRadius
            self.collSphere.setCenter(Point3(0.0, -Globals.Level.LaffPowerupNestOffset[1], self.suit.getHeight() / 2.0))
            self.collSphere.setRadius(radius)
        return

    def setCollSphereToTargeting(self):
        if hasattr(self, 'collSphere') and self.collSphere is not None:
            radius = Globals.LegalEagle.DamageSphereRadius
            self.collSphere.setCenter(Point3(0, 0, radius * 2))
            self.collSphere.setRadius(radius)
        return

    def enterRoost(self):
        self.notify.info("enter%s: '%s' -> '%s'" % (self.newState, self.oldState, self.newState))
        self.hoverOverNestSeq.loop()
        self.propTrack.loop()
        self.setCollSphereToNest()

    def filterRoost(self, request, args):
        self.notify.debug("filter%s( '%s', '%s' )" % (self.state, request, args))
        if request == self.state:
            return None
        elif request == 'next':
            return 'TakeOff'
        else:
            return self.defaultFilter(request, args)
        return None

    def exitRoost(self):
        self.notify.debug("exit%s: '%s' -> '%s'" % (self.oldState, self.oldState, self.newState))
        self.hoverOverNestSeq.pause()
        self.setCollSphereToTargeting()

    def enterTakeOff(self, elapsedTime = 0.0):
        self.notify.info("enter%s: '%s' -> '%s', elapsedTime:%s" % (self.newState,
         self.oldState,
         self.newState,
         elapsedTime))
        self.takeOffSeq.start(elapsedTime)
        self.hoverOverNestSeq.loop()

    def filterTakeOff(self, request, args):
        self.notify.debug("filter%s( '%s', '%s' )" % (self.state, request, args))
        if request == self.state:
            return None
        elif request == 'next':
            if self.hasTarget():
                return 'LockOnToon'
            else:
                return 'LandOnNest'
        else:
            return self.defaultFilter(request, args)
        return None

    def exitTakeOff(self):
        self.notify.debug("exit%s: '%s' -> '%s'" % (self.oldState, self.oldState, self.newState))
        self.takeOffSeq.clearToInitial()
        self.hoverOverNestSeq.pause()

    def enterLockOnToon(self, elapsedTime = 0.0):
        self.notify.info("enter%s: '%s' -> '%s', elapsedTime:%s" % (self.newState,
         self.oldState,
         self.newState,
         elapsedTime))
        taskName = 'updateLockOnTask-%i' % self.index
        taskMgr.add(self.updateLockOnTask, taskName, 45, extraArgs=[])
        messenger.send(CogdoFlyingLegalEagle.LockOnToonEventName, [self.target.doId])
        range = self.target.getDistance(self.interestConeOrigin) / self.getInterestConeLength()
        range = clamp(range, 0.0, 1.0)
        dur = Globals.LegalEagle.LockOnTime
        if self.oldState == 'TakeOff':
            dur *= range
        else:
            dur += Globals.LegalEagle.ExtraPostCooldownTime
        taskName = 'exitLockOnToon-%i' % self.index
        taskMgr.doMethodLater(dur, self.requestNext, taskName, extraArgs=[])

    def filterLockOnToon(self, request, args):
        self.notify.debug("filter%s( '%s', '%s' )" % (self.state, request, args))
        if request == self.state:
            return None
        elif request == 'next':
            if self.hasTarget():
                return 'ChargeUpAttack'
            else:
                return 'RetreatToNest'
        else:
            return self.defaultFilter(request, args)
        return None

    def exitLockOnToon(self):
        self.notify.debug("exit%s: '%s' -> '%s'" % (self.oldState, self.oldState, self.newState))
        taskMgr.remove('updateLockOnTask-%i' % self.index)
        taskMgr.remove('exitLockOnToon-%i' % self.index)

    def enterChargeUpAttack(self, elapsedTime = 0.0):
        self.notify.info("enter%s: '%s' -> '%s', elapsedTime:%s" % (self.newState,
         self.oldState,
         self.newState,
         elapsedTime))
        self.chargeUpAttackSeq.start(elapsedTime)
        messenger.send(CogdoFlyingLegalEagle.ChargingToAttackEventName, [self.target.doId])

    def filterChargeUpAttack(self, request, args):
        self.notify.debug("filter%s( '%s', '%s' )" % (self.state, request, args))
        if request == self.state:
            return None
        elif request == 'next':
            if self.hasTarget():
                return 'Attack'
            else:
                return 'RetreatToNest'
        else:
            return self.defaultFilter(request, args)
        return None

    def exitChargeUpAttack(self):
        self.notify.debug("exit%s: '%s' -> '%s'" % (self.oldState, self.oldState, self.newState))
        self.chargeUpAttackSeq.clearToInitial()

    def enterAttack(self, elapsedTime = 0.0):
        self.notify.info("enter%s: '%s' -> '%s', elapsedTime:%s" % (self.newState,
         self.oldState,
         self.newState,
         elapsedTime))
        self.attackTargetPos = self.target.getPos(render)
        targetState = self.target.animFSM.getCurrentState().getName()
        self._screamSfx.play()
        if targetState == 'jumpAirborne':
            self.attackTargetPos[2] += Globals.LegalEagle.VerticalOffset
        else:
            self.attackTargetPos[2] += Globals.LegalEagle.PlatformVerticalOffset
        self.readyToAttackPos = self.suit.getPos(render)
        self.attackSeq.start(elapsedTime)

    def filterAttack(self, request, args):
        self.notify.debug("filter%s( '%s', '%s' )" % (self.state, request, args))
        if request == self.state:
            return None
        elif request == 'next':
            return 'RetreatToSky'
        else:
            return self.defaultFilter(request, args)
        return None

    def exitAttack(self):
        self.notify.debug("exit%s: '%s' -> '%s'" % (self.oldState, self.oldState, self.newState))
        self.attackSeq.clearToInitial()
        taskMgr.remove('updateAttackPosTask-%i' % self.index)

    def enterRetreatToSky(self, elapsedTime = 0.0):
        self.notify.info("enter%s: '%s' -> '%s', elapsedTime:%s" % (self.newState,
         self.oldState,
         self.newState,
         elapsedTime))
        self.retreatToSkySeq.start(elapsedTime)

    def filterRetreatToSky(self, request, args):
        self.notify.debug("filter%s( '%s', '%s' )" % (self.state, request, args))
        if request == self.state:
            return None
        elif request == 'next':
            return 'Cooldown'
        else:
            return self.defaultFilter(request, args)
        return None

    def exitRetreatToSky(self):
        self.notify.debug("exit%s: '%s' -> '%s'" % (self.oldState, self.oldState, self.newState))
        self.retreatToSkySeq.clearToInitial()

    def enterCooldown(self):
        if self.target != None:
            messenger.send(CogdoFlyingLegalEagle.CooldownEventName, [self.target.doId])
        self.suit.stash()
        self.notify.info("enter%s: '%s' -> '%s'" % (self.newState, self.oldState, self.newState))
        return

    def filterCooldown(self, request, args):
        self.notify.debug("filter%s( '%s', '%s' )" % (self.state, request, args))
        if request == self.state:
            return None
        elif request == 'next':
            if self.hasTarget():
                return 'LockOnToon'
            else:
                return 'LandOnNest'
        else:
            return self.defaultFilter(request, args)
        return None

    def exitCooldown(self):
        self.notify.debug("exit%s: '%s' -> '%s'" % (self.oldState, self.oldState, self.newState))
        self.suit.unstash()
        self.cooldownSeq.clearToInitial()
        if self.newState != 'Off':
            heightOffNest = Globals.LegalEagle.PostCooldownHeightOffNest
            nestPos = self.nest.getPos(render)
            if self.newState in ['LandOnNest']:
                self.suit.setPos(nestPos + Vec3(0, 0, heightOffNest))
            else:
                targetPos = self.target.getPos(render)
                attackPos = Vec3(targetPos)
                attackPos[1] = nestPos[1]
                attackPos[2] = nestPos[2] + heightOffNest
                self.suit.setPos(attackPos)

    def enterRetreatToNest(self, elapsedTime = 0.0):
        self.notify.info("enter%s: '%s' -> '%s', elapsedTime:%s" % (self.newState,
         self.oldState,
         self.newState,
         elapsedTime))
        self.retreatToNestSeq.start(elapsedTime)

    def filterRetreatToNest(self, request, args):
        self.notify.debug("filter%s( '%s', '%s' )" % (self.state, request, args))
        if request == self.state:
            return None
        elif request == 'next':
            return 'LandOnNest'
        else:
            return self.defaultFilter(request, args)
        return None

    def exitRetreatToNest(self):
        self.retreatToNestSeq.clearToInitial()

    def enterLandOnNest(self, elapsedTime = 0.0):
        self.notify.info("enter%s: '%s' -> '%s', elapsedTime:%s" % (self.newState,
         self.oldState,
         self.newState,
         elapsedTime))
        self.landingSeq.start(elapsedTime)

    def filterLandOnNest(self, request, args):
        self.notify.debug("filter%s( '%s', '%s' )" % (self.state, request, args))
        if request == self.state:
            return None
        elif request == 'next':
            if self.hasTarget():
                return 'TakeOff'
            else:
                return 'Roost'
        else:
            return self.defaultFilter(request, args)
        return None

    def exitLandOnNest(self):
        self.landingSeq.clearToInitial()
