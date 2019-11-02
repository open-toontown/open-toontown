import math
import random
from pandac.PandaModules import Vec3
from direct.showbase import PythonUtil
from direct.directnotify import DirectNotifyGlobal
from direct.task.Task import Task
from direct.interval.FunctionInterval import Wait
from direct.interval.IntervalGlobal import Func, LerpFunc, LerpPosInterval, LerpHprInterval, LerpFunctionInterval
from direct.interval.MetaInterval import Sequence, Parallel
from direct.showbase.PythonUtil import bound as clamp
from direct.distributed.ClockDelta import globalClockDelta
from otp.otpbase import OTPGlobals
from toontown.minigame.OrthoDrive import OrthoDrive
from toontown.minigame.OrthoWalk import OrthoWalk
from toontown.toonbase import TTLocalizer
from CogdoFlyingCollisions import CogdoFlyingCollisions
from CogdoFlyingPlayer import CogdoFlyingPlayer
from CogdoFlyingGuiManager import CogdoFlyingGuiManager
from CogdoFlyingInputManager import CogdoFlyingInputManager
from CogdoFlyingCameraManager import CogdoFlyingCameraManager
from CogdoFlyingObjects import CogdoFlyingPlatform, CogdoFlyingGatherable
from CogdoFlyingLegalEagle import CogdoFlyingLegalEagle
import CogdoFlyingGameGlobals as Globals

class CogdoFlyingLocalPlayer(CogdoFlyingPlayer):
    notify = DirectNotifyGlobal.directNotify.newCategory('CogdoFlyingLocalPlayer')
    BroadcastPosTask = 'CogdoFlyingLocalPlayerBroadcastPos'
    PlayWaitingMusicEventName = 'PlayWaitingMusicEvent'
    RanOutOfTimeEventName = 'RanOutOfTimeEvent'
    PropStates = PythonUtil.Enum(('Normal', 'Overdrive', 'Off'))

    def __init__(self, toon, game, level, guiMgr):
        CogdoFlyingPlayer.__init__(self, toon)
        self.defaultTransitions = {'Inactive': ['FreeFly', 'Running'],
         'FreeFly': ['Inactive',
                     'OutOfTime',
                     'Death',
                     'FlyingUp',
                     'Running',
                     'HitWhileFlying',
                     'InWhirlwind'],
         'FlyingUp': ['Inactive',
                      'OutOfTime',
                      'Death',
                      'FreeFly',
                      'Running',
                      'HitWhileFlying',
                      'InWhirlwind'],
         'InWhirlwind': ['Inactive',
                         'OutOfTime',
                         'Death',
                         'FreeFly',
                         'HitWhileFlying'],
         'HitWhileFlying': ['Inactive',
                            'OutOfTime',
                            'Death',
                            'FreeFly',
                            'InWhirlwind'],
         'Death': ['Inactive', 'OutOfTime', 'Spawn'],
         'Running': ['Inactive',
                     'OutOfTime',
                     'FreeFly',
                     'FlyingUp',
                     'Refuel',
                     'WaitingForWin',
                     'HitWhileRunning'],
         'HitWhileRunning': ['Inactive',
                             'OutOfTime',
                             'Death',
                             'Running',
                             'FreeFly'],
         'Spawn': ['Inactive',
                   'OutOfTime',
                   'Running',
                   'WaitingForWin'],
         'OutOfTime': ['Inactive', 'Spawn'],
         'WaitingForWin': ['Inactive', 'Win'],
         'Win': ['Inactive']}
        self.game = game
        self._level = level
        self._guiMgr = guiMgr
        self._inputMgr = CogdoFlyingInputManager()
        self._cameraMgr = CogdoFlyingCameraManager(camera, render, self, self._level)
        self.velocity = Vec3(0.0, 0.0, 0.0)
        self.instantaneousVelocity = Vec3(0.0, 0.0, 0.0)
        self.controlVelocity = Vec3(0.0, 0.0, 0.0)
        self.fanVelocity = Vec3(0.0, 0.0, 0.0)
        self.activeFans = []
        self.fansStillHavingEffect = []
        self.fanIndex2ToonVelocity = {}
        self.legalEagleInterestRequest = {}
        self.activeWhirlwind = None
        self.oldPos = Vec3(0.0, 0.0, 0.0)
        self.checkpointPlatform = None
        self.isHeadInCeiling = False
        self.isToonOnFloor = False
        self.fuel = 0.0
        self.score = 0
        self.postSpawnState = 'Running'
        self.didTimeRunOut = False
        self.hasPressedCtrlYet = False
        self.hasPickedUpFirstPropeller = False
        self.surfacePoint = None
        self.legalEagleHitting = False
        self.propState = None
        self.broadcastPeriod = Globals.AI.BroadcastPeriod
        self.initSfx()
        self.initLocalPlayerIntervals()
        self.initCollisions()
        self.initOrthoWalker()
        self.playerNumber = -1
        self.fuel = 0.0
        self._guiMgr.setFuel(self.fuel)
        self.setCheckpointPlatform(self._level.startPlatform)
        return None

    def initSfx(self):
        audioMgr = base.cogdoGameAudioMgr
        self._deathSfx = audioMgr.createSfx('death')
        self._hitByWhirlwindSfx = audioMgr.createSfx('toonInWhirlwind')
        self._bladeBreakSfx = audioMgr.createSfx('bladeBreak')
        self._collideSfx = audioMgr.createSfx('collide')
        self._toonHitSfx = audioMgr.createSfx('toonHit')
        self._getMemoSfx = audioMgr.createSfx('getMemo')
        self._getLaffSfx = audioMgr.createSfx('getLaff')
        self._getRedTapeSfx = audioMgr.createSfx('getRedTape')
        self._refuelSfx = audioMgr.createSfx('refuel')
        self._fanSfx = audioMgr.createSfx('fan')
        self._invulDebuffSfx = audioMgr.createSfx('invulDebuff')
        self._invulBuffSfx = audioMgr.createSfx('invulBuff')
        self._winSfx = audioMgr.createSfx('win')
        self._loseSfx = audioMgr.createSfx('lose')
        self._refuelSpinSfx = audioMgr.createSfx('refuelSpin')
        self._propellerSfx = audioMgr.createSfx('propeller', self.toon)

    def destroySfx(self):
        del self._deathSfx
        del self._hitByWhirlwindSfx
        del self._bladeBreakSfx
        del self._collideSfx
        del self._toonHitSfx
        del self._propellerSfx
        del self._getMemoSfx
        del self._getLaffSfx
        del self._refuelSfx
        del self._fanSfx
        del self._invulBuffSfx
        del self._invulDebuffSfx
        del self._getRedTapeSfx
        del self._refuelSpinSfx

    def setPlayerNumber(self, num):
        self.playerNumber = num

    def getPlayerNumber(self):
        return self.playerNumber

    def initOrthoWalker(self):
        orthoDrive = OrthoDrive(9.778, maxFrameMove=0.5, wantSound=True)
        self.orthoWalk = OrthoWalk(orthoDrive, broadcast=False, collisions=False, broadcastPeriod=Globals.AI.BroadcastPeriod)

    def initLocalPlayerIntervals(self):
        self.coolDownAfterHitInterval = Sequence(Wait(Globals.Gameplay.HitCooldownTime), Func(self.setEnemyHitting, False), name='coolDownAfterHitInterval-%i' % self.toon.doId)
        self.deathInterval = Sequence(Func(self.resetVelocities), Parallel(Parallel(Func(self._deathSfx.play), LerpHprInterval(self.toon, 1.0, Vec3(720, 0, 0)), LerpFunctionInterval(self.toon.setScale, fromData=1.0, toData=0.1, duration=1.0), self.toon.posInterval(0.5, Vec3(0, 0, -25), other=self.toon)), Sequence(Wait(0.5), Func(base.transitions.irisOut))), Func(self.toon.stash), Wait(1.0), Func(self.toonSpawnFunc), name='%s.deathInterval' % self.__class__.__name__)
        self.outOfTimeInterval = Sequence(Func(messenger.send, CogdoFlyingLocalPlayer.PlayWaitingMusicEventName), Func(self._loseSfx.play), Func(base.transitions.irisOut), Wait(1.0), Func(self.resetVelocities), Func(self._guiMgr.setMessage, '', transition=None), Func(self.toon.stash), Func(self.toonSpawnFunc), name='%s.outOfTimeInterval' % self.__class__.__name__)
        self.spawnInterval = Sequence(Func(self.resetToonFunc), Func(self._cameraMgr.update, 0.0), Func(self._level.update), Func(self.toon.cnode.broadcastPosHprFull), Func(base.transitions.irisIn), Wait(0.5), Func(self.toon.setAnimState, 'TeleportIn'), Func(self.toon.unstash), Wait(1.5), Func(self.requestPostSpawnState), name='%s.spawnInterval' % self.__class__.__name__)
        self.waitingForWinInterval = Sequence(Func(self._guiMgr.setMessage, TTLocalizer.CogdoFlyingGameWaiting % '.'), Wait(1.5), Func(self._guiMgr.setMessage, TTLocalizer.CogdoFlyingGameWaiting % '..'), Wait(1.5), Func(self._guiMgr.setMessage, TTLocalizer.CogdoFlyingGameWaiting % '...'), Wait(1.5), name='%s.waitingForWinInterval' % self.__class__.__name__)
        self.waitingForWinSeq = Sequence(Func(self.setWaitingForWinState), Wait(4.0), Func(self.removeAllMemos), Wait(2.0), Func(self.game.distGame.d_sendRequestAction, Globals.AI.GameActions.LandOnWinPlatform, 0), Func(self.playWaitingForWinInterval), name='%s.waitingForWinSeq' % self.__class__.__name__)
        self.winInterval = Sequence(Func(self._guiMgr.setMessage, ''), Wait(4.0), Func(self.game.distGame.d_sendRequestAction, Globals.AI.GameActions.WinStateFinished, 0), name='%s.winInterval' % self.__class__.__name__)
        self.goSadSequence = Sequence(Wait(2.5), Func(base.transitions.irisOut, 1.5), name='%s.goSadSequence' % self.__class__.__name__)
        self.introGuiSeq = Sequence(Wait(0.5), Parallel(Func(self._guiMgr.setTemporaryMessage, TTLocalizer.CogdoFlyingGameMinimapIntro, duration=5.0), Sequence(Wait(1.0), Func(self._guiMgr.presentProgressGui))), Wait(5.0), Func(self._guiMgr.setMessage, TTLocalizer.CogdoFlyingGamePickUpAPropeller), name='%s.introGuiSeq' % self.__class__.__name__)
        return

    def goSad(self):
        self.goSadSequence.start()

    def setWaitingForWinState(self):
        if self.didTimeRunOut:
            self.toon.b_setAnimState('Sad')
            self._guiMgr.setMessage(TTLocalizer.CogdoFlyingGameOutOfTime, transition='blink')
        else:
            self._winSfx.play()
            messenger.send(CogdoFlyingLocalPlayer.PlayWaitingMusicEventName)
            self.toon.b_setAnimState('victory')
            self._guiMgr.setMessage(TTLocalizer.CogdoFlyingGameYouMadeIt)

    def removeAllMemos(self):
        if self.didTimeRunOut:
            messenger.send(CogdoFlyingLocalPlayer.RanOutOfTimeEventName)

    def playWaitingForWinInterval(self):
        if not self.game.distGame.isSinglePlayer():
            self.waitingForWinInterval.loop()

    def resetToonFunc(self):
        self.resetToon(resetFuel=self.hasPickedUpFirstPropeller)

    def _loopPropellerSfx(self, playRate = 1.0, volume = 1.0):
        self._propellerSfx.loop(playRate=playRate, volume=1.0)

    def initCollisions(self):
        avatarRadius = 2.0
        reach = 4.0
        self.flyerCollisions = CogdoFlyingCollisions()
        self.flyerCollisions.setWallBitMask(OTPGlobals.WallBitmask)
        self.flyerCollisions.setFloorBitMask(OTPGlobals.FloorBitmask)
        self.flyerCollisions.initializeCollisions(base.cTrav, self.toon, avatarRadius, OTPGlobals.FloorOffset, reach)
        self.flyerCollisions.setCollisionsActive(0)
        floorColl = CogdoFlyingPlatform.FloorCollName
        ceilingColl = CogdoFlyingPlatform.CeilingCollName
        self.accept('Flyer.cHeadCollSphere-enter-%s' % ceilingColl, self.__handleHeadCollisionIntoCeiling)
        self.accept('Flyer.cHeadCollSphere-exit-%s' % ceilingColl, self.__handleHeadCollisionExitCeiling)
        self.accept('Flyer.cFloorEventSphere-exit-%s' % floorColl, self.__handleEventCollisionExitFloor)
        self.accept('Flyer.cRayNode-enter-%s' % floorColl, self.__handleRayCollisionEnterFloor)
        self.accept('Flyer.cRayNode-again-%s' % floorColl, self.__handleRayCollisionAgainFloor)

    def enable(self):
        CogdoFlyingPlayer.enable(self)
        self.toon.hideName()

    def disable(self):
        CogdoFlyingPlayer.disable(self)

    def isLegalEagleInterestRequestSent(self, index):
        if index in self.legalEagleInterestRequest:
            return True
        else:
            return False

    def setLegalEagleInterestRequest(self, index):
        if index not in self.legalEagleInterestRequest:
            self.legalEagleInterestRequest[index] = True
        else:
            CogdoFlyingLocalPlayer.notify.warning('Attempting to set an legal eagle interest request when one already exists:%s' % index)

    def clearLegalEagleInterestRequest(self, index):
        if index in self.legalEagleInterestRequest:
            del self.legalEagleInterestRequest[index]

    def setBackpackState(self, state):
        if state == self.backpackState:
            return
        CogdoFlyingPlayer.setBackpackState(self, state)
        if state in Globals.Gameplay.BackpackStates:
            if state == Globals.Gameplay.BackpackStates.Normal:
                messenger.send(CogdoFlyingGuiManager.ClearMessageDisplayEventName)
            elif state == Globals.Gameplay.BackpackStates.Targeted:
                messenger.send(CogdoFlyingGuiManager.EagleTargetingLocalPlayerEventName)
            elif state == Globals.Gameplay.BackpackStates.Attacked:
                messenger.send(CogdoFlyingGuiManager.EagleAttackingLocalPlayerEventName)

    def requestPostSpawnState(self):
        self.request(self.postSpawnState)

    def toonSpawnFunc(self):
        self.game.distGame.b_toonSpawn(self.toon.doId)

    def __handleHeadCollisionIntoCeiling(self, collEntry):
        self.isHeadInCeiling = True
        self.surfacePoint = self.toon.getPos()
        self._collideSfx.play()
        if self.controlVelocity[2] > 0.0:
            self.controlVelocity[2] = -self.controlVelocity[2] / 2.0

    def __handleHeadCollisionExitCeiling(self, collEntry):
        self.isHeadInCeiling = False
        self.surfacePoint = None
        return

    def landOnPlatform(self, collEntry):
        surfacePoint = collEntry.getSurfacePoint(render)
        intoNodePath = collEntry.getIntoNodePath()
        platform = CogdoFlyingPlatform.getFromNode(intoNodePath)
        if platform is not None:
            if not platform.isStartOrEndPlatform():
                taskMgr.doMethodLater(0.5, self.delayedLandOnPlatform, 'delayedLandOnPlatform', extraArgs=[platform])
            elif platform.isEndPlatform():
                taskMgr.doMethodLater(1.0, self.delayedLandOnWinPlatform, 'delayedLandOnWinPlatform', extraArgs=[platform])
        self.isToonOnFloor = True
        self.controlVelocity = Vec3(0.0, 0.0, 0.0)
        self.toon.setPos(render, surfacePoint)
        self.toon.setHpr(0, 0, 0)
        self.request('Running')
        return

    def __handleRayCollisionEnterFloor(self, collEntry):
        fromNodePath = collEntry.getFromNodePath()
        intoNodePath = collEntry.getIntoNodePath()
        intoName = intoNodePath.getName()
        fromName = fromNodePath.getName()
        toonPos = self.toon.getPos(render)
        collPos = collEntry.getSurfacePoint(render)
        if toonPos.getZ() < collPos.getZ() + Globals.Gameplay.RayPlatformCollisionThreshold:
            if not self.isToonOnFloor and self.state in ['FreeFly', 'FlyingUp']:
                self.landOnPlatform(collEntry)

    def __handleRayCollisionAgainFloor(self, collEntry):
        fromNodePath = collEntry.getFromNodePath()
        intoNodePath = collEntry.getIntoNodePath()
        intoName = intoNodePath.getName()
        fromName = fromNodePath.getName()
        toonPos = self.toon.getPos(render)
        collPos = collEntry.getSurfacePoint(render)
        if toonPos.getZ() < collPos.getZ() + Globals.Gameplay.RayPlatformCollisionThreshold:
            if not self.isToonOnFloor and self.state in ['FreeFly', 'FlyingUp']:
                self.landOnPlatform(collEntry)

    def __handleEventCollisionExitFloor(self, collEntry):
        fromNodePath = collEntry.getFromNodePath()
        intoNodePath = collEntry.getIntoNodePath()
        intoName = intoNodePath.getName()
        fromName = fromNodePath.getName()
        if self.isToonOnFloor:
            self.notify.debug('~~~Exit Floor:%s -> %s' % (intoName, fromName))
            self.isToonOnFloor = False
            taskMgr.remove('delayedLandOnPlatform')
            taskMgr.remove('delayedLandOnWinPlatform')
            if self.state not in ['FlyingUp', 'Spawn']:
                self.notify.debug('Exited floor')
                self.request('FreeFly')

    def delayedLandOnPlatform(self, platform):
        self.setCheckpointPlatform(platform)
        return Task.done

    def delayedLandOnWinPlatform(self, platform):
        self.setCheckpointPlatform(self._level.endPlatform)
        self.request('WaitingForWin')
        return Task.done

    def handleTimerExpired(self):
        if self.state not in ['WaitingForWin', 'Win']:
            self.setCheckpointPlatform(self._level.endPlatform)
            self.postSpawnState = 'WaitingForWin'
            self.didTimeRunOut = True
            if self.state not in ['Death']:
                self.request('OutOfTime')

    def ready(self):
        self.resetToon(resetFuel=False)
        self._cameraMgr.enable()
        self._cameraMgr.update()

    def start(self):
        CogdoFlyingPlayer.start(self)
        self.toon.collisionsOff()
        self.flyerCollisions.setAvatar(self.toon)
        self.flyerCollisions.setCollisionsActive(1)
        self._levelBounds = self._level.getBounds()
        self.introGuiSeq.start()
        self.request('Running')

    def exit(self):
        self.request('Inactive')
        CogdoFlyingPlayer.exit(self)
        self._cameraMgr.disable()
        self.flyerCollisions.setCollisionsActive(0)
        self.flyerCollisions.setAvatar(None)
        taskMgr.remove('delayedLandOnFuelPlatform')
        taskMgr.remove('delayedLandOnWinPlatform')
        self.ignoreAll()
        return

    def unload(self):
        self.toon.showName()
        self.toon.collisionsOn()
        self._destroyEventIval()
        self._destroyEnemyHitIval()
        CogdoFlyingPlayer.unload(self)
        self._fanSfx.stop()
        self.flyerCollisions.deleteCollisions()
        del self.flyerCollisions
        self.ignoreAll()
        taskMgr.remove('delayedLandOnPlatform')
        taskMgr.remove('delayedLandOnWinPlatform')
        self.checkpointPlatform = None
        self._cameraMgr.disable()
        del self._cameraMgr
        del self.game
        self._inputMgr.destroy()
        del self._inputMgr
        self.introGuiSeq.clearToInitial()
        del self.introGuiSeq
        if self.goSadSequence:
            self.goSadSequence.clearToInitial()
            del self.goSadSequence
        if self.coolDownAfterHitInterval:
            self.coolDownAfterHitInterval.clearToInitial()
            del self.coolDownAfterHitInterval
        if self.deathInterval:
            self.deathInterval.clearToInitial()
            del self.deathInterval
        if self.spawnInterval:
            self.spawnInterval.clearToInitial()
            del self.spawnInterval
        if self.outOfTimeInterval:
            self.outOfTimeInterval.clearToInitial()
            del self.outOfTimeInterval
        if self.winInterval:
            self.winInterval.clearToInitial()
            del self.winInterval
        if self.waitingForWinInterval:
            self.waitingForWinInterval.clearToInitial()
            del self.waitingForWinInterval
        if self.waitingForWinSeq:
            self.waitingForWinSeq.clearToInitial()
            del self.waitingForWinSeq
        del self.activeFans[:]
        del self.fansStillHavingEffect[:]
        self.fanIndex2ToonVelocity.clear()
        self.orthoWalk.stop()
        self.orthoWalk.destroy()
        del self.orthoWalk
        self.destroySfx()
        return

    def setCheckpointPlatform(self, platform):
        self.checkpointPlatform = platform

    def resetVelocities(self):
        self.fanVelocity = Vec3(0.0, 0.0, 0.0)
        self.controlVelocity = Vec3(0.0, 0.0, 0.0)
        self.velocity = Vec3(0.0, 0.0, 0.0)

    def resetToon(self, resetFuel = True):
        CogdoFlyingPlayer.resetToon(self)
        self.resetVelocities()
        del self.activeFans[:]
        del self.fansStillHavingEffect[:]
        self.fanIndex2ToonVelocity.clear()
        self._fanSfx.stop()
        spawnPos = self.checkpointPlatform.getSpawnPosForPlayer(self.getPlayerNumber(), render)
        self.activeWhirlwind = None
        self.toon.setPos(render, spawnPos)
        self.toon.setHpr(render, 0, 0, 0)
        if resetFuel:
            self.resetFuel()
        self.isHeadInCeiling = False
        self.isToonOnFloor = True
        return

    def activateFlyingBroadcast(self):
        self.timeSinceLastPosBroadcast = 0.0
        self.lastPosBroadcast = self.toon.getPos()
        self.lastHprBroadcast = self.toon.getHpr()
        toon = self.toon
        toon.d_clearSmoothing()
        toon.sendCurrentPosition()
        taskMgr.remove(self.BroadcastPosTask)
        taskMgr.add(self.doBroadcast, self.BroadcastPosTask)

    def shutdownFlyingBroadcast(self):
        taskMgr.remove(self.BroadcastPosTask)

    def doBroadcast(self, task):
        dt = globalClock.getDt()
        self.timeSinceLastPosBroadcast += dt
        if self.timeSinceLastPosBroadcast >= self.broadcastPeriod:
            self.timeSinceLastPosBroadcast = 0.0
            self.toon.cnode.broadcastPosHprFull()
        return Task.cont

    def died(self, timestamp):
        self.request('Death')

    def spawn(self, timestamp):
        self.request('Spawn')

    def updateToonFlyingState(self, dt):
        leftPressed = self._inputMgr.arrowKeys.leftPressed()
        rightPressed = self._inputMgr.arrowKeys.rightPressed()
        upPressed = self._inputMgr.arrowKeys.upPressed()
        downPressed = self._inputMgr.arrowKeys.downPressed()
        jumpPressed = self._inputMgr.arrowKeys.jumpPressed()
        if not self.hasPressedCtrlYet and jumpPressed and self.isFuelLeft():
            self.hasPressedCtrlYet = True
            messenger.send(CogdoFlyingGuiManager.FirstPressOfCtrlEventName)
        if jumpPressed and self.isFuelLeft():
            if self.state == 'FreeFly' and self.isInTransition() == False:
                self.notify.debug('FreeFly -> FlyingUp')
                self.request('FlyingUp')
        elif self.state == 'FlyingUp' and self.isInTransition() == False:
            self.notify.debug('FlyingUp -> FreeFly')
            self.request('FreeFly')
        if leftPressed and not rightPressed:
            self.toon.setH(self.toon, Globals.Gameplay.ToonTurning['turningSpeed'] * dt)
            max = Globals.Gameplay.ToonTurning['maxTurningAngle']
            if self.toon.getH() > max:
                self.toon.setH(max)
        elif rightPressed and not leftPressed:
            self.toon.setH(self.toon, -1.0 * Globals.Gameplay.ToonTurning['turningSpeed'] * dt)
            min = -1.0 * Globals.Gameplay.ToonTurning['maxTurningAngle']
            if self.toon.getH() < min:
                self.toon.setH(min)

    def updateControlVelocity(self, dt):
        leftPressed = self._inputMgr.arrowKeys.leftPressed()
        rightPressed = self._inputMgr.arrowKeys.rightPressed()
        upPressed = self._inputMgr.arrowKeys.upPressed()
        downPressed = self._inputMgr.arrowKeys.downPressed()
        jumpPressed = self._inputMgr.arrowKeys.jumpPressed()
        if leftPressed:
            self.controlVelocity[0] -= Globals.Gameplay.ToonAcceleration['turning'] * dt
        if rightPressed:
            self.controlVelocity[0] += Globals.Gameplay.ToonAcceleration['turning'] * dt
        if upPressed:
            self.controlVelocity[1] += Globals.Gameplay.ToonAcceleration['forward'] * dt
        if downPressed:
            self.controlVelocity[2] -= Globals.Gameplay.ToonAcceleration['activeDropDown'] * dt
            self.controlVelocity[1] -= Globals.Gameplay.ToonAcceleration['activeDropBack'] * dt
        if jumpPressed and self.isFuelLeft():
            self.controlVelocity[2] += Globals.Gameplay.ToonAcceleration['boostUp'] * dt
        minVal = -Globals.Gameplay.ToonVelMax['turning']
        maxVal = Globals.Gameplay.ToonVelMax['turning']
        if not leftPressed and not rightPressed or self.controlVelocity[0] > maxVal or self.controlVelocity[0] < minVal:
            x = self.dampenVelocityVal(self.controlVelocity[0], 'turning', 'turning', minVal, maxVal, dt)
            self.controlVelocity[0] = x
        minVal = -Globals.Gameplay.ToonVelMax['backward']
        maxVal = Globals.Gameplay.ToonVelMax['forward']
        if not upPressed and not downPressed or self.controlVelocity[1] > maxVal or self.controlVelocity[1] < minVal:
            y = self.dampenVelocityVal(self.controlVelocity[1], 'backward', 'forward', minVal, maxVal, dt)
            self.controlVelocity[1] = y
        if self.isFuelLeft():
            minVal = -Globals.Gameplay.ToonVelMax['fall']
        else:
            minVal = -Globals.Gameplay.ToonVelMax['fallNoFuel']
        maxVal = Globals.Gameplay.ToonVelMax['boost']
        if self.controlVelocity[2] > minVal:
            if (not self._inputMgr.arrowKeys.jumpPressed() or not self.isFuelLeft()) and not self.isToonOnFloor:
                self.controlVelocity[2] -= Globals.Gameplay.ToonAcceleration['fall'] * dt
        if self.controlVelocity[2] < 0.0 and self.isToonOnFloor:
            self.controlVelocity[2] = 0.0
        minVal = -Globals.Gameplay.ToonVelMax['turning']
        maxVal = Globals.Gameplay.ToonVelMax['turning']
        self.controlVelocity[0] = clamp(self.controlVelocity[0], minVal, maxVal)
        minVal = -Globals.Gameplay.ToonVelMax['backward']
        maxVal = Globals.Gameplay.ToonVelMax['forward']
        self.controlVelocity[1] = clamp(self.controlVelocity[1], minVal, maxVal)
        if self.isFuelLeft():
            minVal = -Globals.Gameplay.ToonVelMax['fall']
        else:
            minVal = -Globals.Gameplay.ToonVelMax['fallNoFuel']
        maxVal = Globals.Gameplay.ToonVelMax['boost']
        self.controlVelocity[2] = clamp(self.controlVelocity[2], minVal, maxVal)

    def updateFanVelocity(self, dt):
        fanHeight = Globals.Gameplay.FanCollisionTubeHeight
        min = Globals.Gameplay.FanMinPower
        max = Globals.Gameplay.FanMaxPower
        powerRange = max - min
        for fan in self.activeFans:
            blowVec = fan.getBlowDirection()
            blowVec *= Globals.Gameplay.ToonAcceleration['fan'] * dt
            if Globals.Gameplay.UseVariableFanPower:
                distance = fan.model.getDistance(self.toon)
                power = math.fabs(distance / fanHeight - 1.0) * powerRange + min
                power = clamp(power, min, max)
                blowVec *= power
            fanVelocity = self.fanIndex2ToonVelocity[fan.index]
            fanVelocity += blowVec

        removeList = []
        for fan in self.fansStillHavingEffect:
            if fan not in self.activeFans:
                blowVec = fan.getBlowDirection()
                blowVec *= Globals.Gameplay.ToonDeceleration['fan'] * dt
                fanVelocity = Vec3(self.fanIndex2ToonVelocity[fan.index])
                lastLen = fanVelocity.length()
                fanVelocity -= blowVec
                if fanVelocity.length() > lastLen:
                    removeList.append(fan)
                else:
                    self.fanIndex2ToonVelocity[fan.index] = fanVelocity

        for fan in removeList:
            self.fansStillHavingEffect.remove(fan)
            del self.fanIndex2ToonVelocity[fan.index]

        self.fanVelocity = Vec3(0.0, 0.0, 0.0)
        for fan in self.fansStillHavingEffect:
            self.fanVelocity += self.fanIndex2ToonVelocity[fan.index]

        minVal = -Globals.Gameplay.ToonVelMax['fan']
        maxVal = Globals.Gameplay.ToonVelMax['fan']
        self.fanVelocity[0] = clamp(self.fanVelocity[0], minVal, maxVal)
        self.fanVelocity[1] = clamp(self.fanVelocity[1], minVal, maxVal)
        self.fanVelocity[2] = clamp(self.fanVelocity[2], minVal, maxVal)

    def dampenVelocityVal(self, velocityVal, typeNeg, typePos, minVal, maxVal, dt):
        if velocityVal > 0.0:
            velocityVal -= Globals.Gameplay.ToonDeceleration[typePos] * dt
            velocityVal = clamp(velocityVal, 0.0, maxVal)
        elif velocityVal < 0.0:
            velocityVal += Globals.Gameplay.ToonDeceleration[typeNeg] * dt
            velocityVal = clamp(velocityVal, minVal, 0.0)
        return velocityVal

    def allowFuelDeath(self):
        if Globals.Gameplay.DoesToonDieWithFuel:
            return True
        else:
            return not self.isFuelLeft()

    def updateToonPos(self, dt):
        toonWorldY = self.toon.getY(render)
        if self.hasPickedUpFirstPropeller == False:
            if toonWorldY > -7.6:
                self.toon.setY(-7.6)
            elif toonWorldY < -35.0:
                self.toon.setY(-35.0)
            return
        self.velocity = self.controlVelocity + self.fanVelocity
        vel = self.velocity * dt
        self.toon.setPos(self.toon, vel[0], vel[1], vel[2])
        toonPos = self.toon.getPos()
        if Globals.Dev.DisableDeath:
            pass
        elif toonPos[2] < 0.0 and self.state in ['FreeFly', 'FlyingUp'] and self.allowFuelDeath():
            self.postSpawnState = 'Running'
            self.game.distGame.b_toonDied(self.toon.doId)
        if toonPos[2] > self._levelBounds[2][1]:
            self.controlVelocity[2] = 0.0
            self.fanVelocity[2] = 0.0
        toonPos = Vec3(clamp(toonPos[0], self._levelBounds[0][0], self._levelBounds[0][1]), clamp(toonPos[1], self._levelBounds[1][0], self._levelBounds[1][1]), clamp(toonPos[2], self._levelBounds[2][0], self._levelBounds[2][1]))
        if self.isHeadInCeiling and toonPos[2] > self.surfacePoint[2]:
            toonPos[2] = self.surfacePoint[2]
        self.toon.setPos(toonPos)
        if self.toon.getY(render) < -10:
            self.toon.setY(-10.0)

    def printFanInfo(self, string):
        if len(self.fanIndex2ToonVelocity) > 0:
            self.notify.info('==AFTER %s==' % string)
            self.notify.info('Fan velocity:%s' % self.fanVelocity)
        if len(self.activeFans) > 0:
            self.notify.info('%s' % self.activeFans)
        if len(self.fanIndex2ToonVelocity) > 0:
            self.notify.info('%s' % self.fanIndex2ToonVelocity)
        if len(self.fansStillHavingEffect) > 0:
            self.notify.info('%s' % self.fansStillHavingEffect)

    def resetFuel(self):
        self.setFuel(Globals.Gameplay.FuelNormalAmt)

    def isFuelLeft(self):
        return self.fuel > 0.0

    def setFuel(self, fuel):
        self.fuel = fuel
        self._guiMgr.setFuel(fuel)
        if self.fuel <= 0.0:
            fuelState = Globals.Gameplay.FuelStates.FuelEmpty
        elif self.fuel < Globals.Gameplay.FuelVeryLowAmt:
            fuelState = Globals.Gameplay.FuelStates.FuelVeryLow
        elif self.fuel < Globals.Gameplay.FuelLowAmt:
            fuelState = Globals.Gameplay.FuelStates.FuelLow
        else:
            fuelState = Globals.Gameplay.FuelStates.FuelNormal
        if fuelState > self.fuelState:
            self.game.distGame.b_toonSetBlades(self.toon.doId, fuelState)
        if fuelState < self.fuelState:
            if self.state in ['FlyingUp', 'FreeFly', 'Running']:
                self.game.distGame.b_toonBladeLost(self.toon.doId)

    def resetBlades(self):
        CogdoFlyingPlayer.resetBlades(self)
        self._guiMgr.resetBlades()

    def setBlades(self, fuelState):
        CogdoFlyingPlayer.setBlades(self, fuelState)
        self._guiMgr.setBlades(fuelState)

    def bladeLost(self):
        CogdoFlyingPlayer.bladeLost(self)
        self._bladeBreakSfx.play(volume=0.35)
        self._guiMgr.bladeLost()

    def updateFuel(self, dt):
        if Globals.Dev.InfiniteFuel:
            self.setFuel(Globals.Gameplay.FuelNormalAmt)
        elif self.state in Globals.Gameplay.DepleteFuelStates and self.fuel > 0.0:
            self.setFuel(self.fuel - Globals.Gameplay.FuelBurnRate * dt)
        elif self.fuel < 0.0:
            self.setFuel(0.0)

    def update(self, dt = 0.0):
        self.instantaneousVelocity = (self.toon.getPos() - self.oldPos) / dt
        self.oldPos = self.toon.getPos()
        self.updateFuel(dt)
        if self.isFlying():
            self.updateToonFlyingState(dt)
        if self.state in ['FreeFly', 'FlyingUp', 'Death']:
            self.updateControlVelocity(dt)
        self.updateFanVelocity(dt)
        self.updateToonPos(dt)
        self._cameraMgr.update(dt)

    def isFlying(self):
        if self.state in ['FreeFly', 'FlyingUp']:
            return True
        else:
            return False

    def pressedControlWhileRunning(self):
        if self.isFuelLeft() and self.state == 'Running':
            self.notify.debug('Pressed Control and have fuel')
            self.request('FlyingUp')
        else:
            self.ignore('control')
            self.ignore('lcontrol')
            self.acceptOnce('control', self.pressedControlWhileRunning)
            self.acceptOnce('lcontrol', self.pressedControlWhileRunning)

    def setPropellerState(self, propState):
        if not self.hasPickedUpFirstPropeller:
            propState = CogdoFlyingLocalPlayer.PropStates.Off
        if self.propState != propState:
            oldState = self.propState
            self.propState = propState
            if self.propState == CogdoFlyingLocalPlayer.PropStates.Normal:
                if not self.propellerSpinLerp.isPlaying():
                    self.propellerSpinLerp.loop()
                self.setPropellerSpinRate(Globals.Gameplay.NormalPropSpeed)
                self._guiMgr.setPropellerSpinRate(Globals.Gameplay.NormalPropSpeed)
                self._loopPropellerSfx(playRate=0.7, volume=0.8)
            elif self.propState == CogdoFlyingLocalPlayer.PropStates.Overdrive:
                if not self.propellerSpinLerp.isPlaying():
                    self.propellerSpinLerp.loop()
                self.setPropellerSpinRate(Globals.Gameplay.OverdrivePropSpeed)
                self._guiMgr.setPropellerSpinRate(Globals.Gameplay.OverdrivePropSpeed)
                self._loopPropellerSfx(playRate=1.1)
            elif self.propState == CogdoFlyingLocalPlayer.PropStates.Off:
                self.propellerSpinLerp.pause()
                self._propellerSfx.stop()

    def enterInactive(self):
        CogdoFlyingLocalPlayer.notify.info("enter%s: '%s' -> '%s'" % (self.newState, self.oldState, self.newState))
        self._inputMgr.disable()
        self.setPropellerState(CogdoFlyingLocalPlayer.PropStates.Off)
        self.shutdownFlyingBroadcast()

    def filterInactive(self, request, args):
        if request == self.state:
            return None
        else:
            return self.defaultFilter(request, args)
        return None

    def exitInactive(self):
        CogdoFlyingLocalPlayer.notify.debug("exit%s: '%s' -> '%s'" % (self.oldState, self.oldState, self.newState))
        self._inputMgr.enable()
        self.activateFlyingBroadcast()

    def enterSpawn(self):
        CogdoFlyingLocalPlayer.notify.info("enter%s: '%s' -> '%s'" % (self.newState, self.oldState, self.newState))
        self.toon.b_setAnimState('Happy', 1.0)
        self.setPropellerState(CogdoFlyingLocalPlayer.PropStates.Normal)
        self.spawnInterval.start()

    def filterSpawn(self, request, args):
        if request == self.state:
            return None
        else:
            return self.defaultFilter(request, args)
        return None

    def exitSpawn(self):
        CogdoFlyingLocalPlayer.notify.debug("exit%s: '%s' -> '%s'" % (self.oldState, self.oldState, self.newState))

    def enterFreeFly(self):
        CogdoFlyingLocalPlayer.notify.info("enter%s: '%s' -> '%s'" % (self.newState, self.oldState, self.newState))
        self.setPropellerState(CogdoFlyingLocalPlayer.PropStates.Normal)
        if self.oldState in ['Running', 'HitWhileRunning']:
            self.toon.jumpStart()
            self.toon.setHpr(render, 0, 0, 0)

    def filterFreeFly(self, request, args):
        if request == self.state:
            return None
        else:
            return self.defaultFilter(request, args)
        return None

    def exitFreeFly(self):
        CogdoFlyingLocalPlayer.notify.debug("exit%s: '%s' -> '%s'" % (self.oldState, self.oldState, self.newState))

    def enterFlyingUp(self):
        CogdoFlyingLocalPlayer.notify.info("enter%s: '%s' -> '%s'" % (self.newState, self.oldState, self.newState))
        self.setPropellerState(CogdoFlyingLocalPlayer.PropStates.Overdrive)
        if self.oldState in ['Running']:
            self.toon.jumpStart()
            self.toon.setHpr(render, 0, 0, 0)

    def filterFlyingUp(self, request, args):
        if request == self.state:
            return None
        else:
            return self.defaultFilter(request, args)
        return None

    def exitFlyingUp(self):
        CogdoFlyingLocalPlayer.notify.debug("exit%s: '%s' -> '%s'" % (self.oldState, self.oldState, self.newState))

    def enterHitWhileFlying(self, elapsedTime = 0.0):
        CogdoFlyingLocalPlayer.notify.info("enter%s: '%s' -> '%s'" % (self.newState, self.oldState, self.newState))
        self.setEnemyHitting(True)
        self._toonHitSfx.play()
        self.startHitFlyingToonInterval()
        self.setPropellerState(CogdoFlyingLocalPlayer.PropStates.Normal)

    def filterHitWhileFlying(self, request, args):
        if request == self.state:
            return None
        else:
            return self.defaultFilter(request, args)
        return None

    def exitHitWhileFlying(self):
        CogdoFlyingLocalPlayer.notify.debug("exit%s: '%s' -> '%s'" % (self.oldState, self.oldState, self.newState))
        self.enemyHitIval.clearToInitial()
        self.coolDownAfterHitInterval.clearToInitial()
        self.coolDownAfterHitInterval.start()

    def enterInWhirlwind(self, elapsedTime = 0.0):
        CogdoFlyingLocalPlayer.notify.info("enter%s: '%s' -> '%s'" % (self.newState, self.oldState, self.newState))
        self._hitByWhirlwindSfx.play()
        self.startHitByWhirlwindInterval()
        self.setPropellerState(CogdoFlyingLocalPlayer.PropStates.Normal)

    def filterInWhirlwind(self, request, args):
        if request == self.state:
            return None
        else:
            return self.defaultFilter(request, args)
        return None

    def exitInWhirlwind(self):
        CogdoFlyingLocalPlayer.notify.debug("exit%s: '%s' -> '%s'" % (self.oldState, self.oldState, self.newState))
        self.eventIval.clearToInitial()

    def enterHitWhileRunning(self, elapsedTime = 0.0):
        CogdoFlyingLocalPlayer.notify.info("enter%s: '%s' -> '%s'" % (self.newState, self.oldState, self.newState))
        self.setEnemyHitting(True)
        self._toonHitSfx.play()
        self.toon.b_setAnimState('FallDown')
        self.startHitRunningToonInterval()
        self.setPropellerState(CogdoFlyingLocalPlayer.PropStates.Normal)

    def filterHitWhileRunning(self, request, args):
        if request == self.state:
            return None
        else:
            return self.defaultFilter(request, args)
        return None

    def exitHitWhileRunning(self):
        CogdoFlyingLocalPlayer.notify.debug("exit%s: '%s' -> '%s'" % (self.oldState, self.oldState, self.newState))
        self.enemyHitIval.clearToInitial()
        self.coolDownAfterHitInterval.clearToInitial()
        self.coolDownAfterHitInterval.start()

    def enterRunning(self):
        CogdoFlyingLocalPlayer.notify.info("enter%s: '%s' -> '%s'" % (self.newState, self.oldState, self.newState))
        self.toon.b_setAnimState('Happy', 1.0)
        if self.oldState not in ['Spawn', 'HitWhileRunning', 'Inactive']:
            self.toon.jumpHardLand()
            self._collideSfx.play()
        self.orthoWalk.start()
        self.setPropellerState(CogdoFlyingLocalPlayer.PropStates.Normal)
        self.ignore('control')
        self.ignore('lcontrol')
        self.acceptOnce('control', self.pressedControlWhileRunning)
        self.acceptOnce('lcontrol', self.pressedControlWhileRunning)

    def filterRunning(self, request, args):
        if request == self.state:
            return None
        else:
            return self.defaultFilter(request, args)
        return None

    def exitRunning(self):
        CogdoFlyingLocalPlayer.notify.debug("exit%s: '%s' -> '%s'" % (self.oldState, self.oldState, self.newState))
        self.orthoWalk.stop()
        self.ignore('control')
        self.ignore('lcontrol')

    def enterOutOfTime(self):
        CogdoFlyingLocalPlayer.notify.info("enter%s: '%s' -> '%s'" % (self.newState, self.oldState, self.newState))
        if self.spawnInterval.isPlaying():
            self.spawnInterval.clearToInitial()
        self.ignoreAll()
        self.introGuiSeq.clearToInitial()
        self.setPropellerState(CogdoFlyingLocalPlayer.PropStates.Off)
        if not Globals.Dev.NoLegalEagleAttacks:
            for eagle in self.legalEaglesTargeting:
                messenger.send(CogdoFlyingLegalEagle.RequestRemoveTargetEventName, [eagle.index])

        taskMgr.remove('delayedLandOnPlatform')
        taskMgr.remove('delayedLandOnWinPlatform')
        self.outOfTimeInterval.start()

    def filterOutOfTime(self, request, args):
        if request == self.state:
            return None
        else:
            return self.defaultFilter(request, args)
        return None

    def exitOutOfTime(self):
        CogdoFlyingLocalPlayer.notify.debug("exit%s: '%s' -> '%s'" % (self.oldState, self.oldState, self.newState))

    def enterDeath(self):
        CogdoFlyingLocalPlayer.notify.info("enter%s: '%s' -> '%s'" % (self.newState, self.oldState, self.newState))
        self.propellerSmoke.stop()
        self.deathInterval.start()
        self.toon.b_setAnimState('jumpAirborne', 1.0)
        self.setPropellerState(CogdoFlyingLocalPlayer.PropStates.Off)
        if not Globals.Dev.NoLegalEagleAttacks:
            for eagle in self.legalEaglesTargeting:
                messenger.send(CogdoFlyingLegalEagle.RequestRemoveTargetEventName, [eagle.index])

    def filterDeath(self, request, args):
        if request == self.state:
            return None
        else:
            return self.defaultFilter(request, args)
        return None

    def exitDeath(self):
        CogdoFlyingLocalPlayer.notify.debug("exit%s: '%s' -> '%s'" % (self.oldState, self.oldState, self.newState))
        self.deathInterval.clearToInitial()

    def enterWaitingForWin(self):
        CogdoFlyingLocalPlayer.notify.info("enter%s: '%s' -> '%s'" % (self.newState, self.oldState, self.newState))
        self.resetFuel()
        self._guiMgr.hideRefuelGui()
        self.waitingForWinSeq.start()
        self.setPropellerState(CogdoFlyingLocalPlayer.PropStates.Normal)
        if not Globals.Dev.NoLegalEagleAttacks:
            self.game.forceClearLegalEagleInterestInToon(self.toon.doId)

    def filterWaitingForWin(self, request, args):
        if request == self.state:
            return None
        else:
            return self.defaultFilter(request, args)
        return None

    def exitWaitingForWin(self):
        CogdoFlyingLocalPlayer.notify.debug("exit%s: '%s' -> '%s'" % (self.oldState, self.oldState, self.newState))
        self.waitingForWinSeq.finish()
        self.waitingForWinInterval.clearToInitial()

    def enterWin(self):
        CogdoFlyingLocalPlayer.notify.info("enter%s: '%s' -> '%s'" % (self.newState, self.oldState, self.newState))
        self._guiMgr.stopTimer()
        self.winInterval.start()
        self.setPropellerState(CogdoFlyingLocalPlayer.PropStates.Normal)

    def filterWin(self, request, args):
        if request == self.state:
            return None
        else:
            return self.defaultFilter(request, args)
        return None

    def exitWin(self):
        CogdoFlyingLocalPlayer.notify.debug("exit%s: '%s' -> '%s'" % (self.oldState, self.oldState, self.newState))

    def _destroyEventIval(self):
        if hasattr(self, 'eventIval'):
            self.eventIval.clearToInitial()
            del self.eventIval

    def startEventIval(self, ival):
        self._destroyEventIval()
        self.eventIval = ival
        self.eventIval.start()

    def _destroyEnemyHitIval(self):
        if hasattr(self, 'enemyHitIval'):
            self.enemyHitIval.clearToInitial()
            del self.enemyHitIval

    def startEnemyHitIval(self, ival):
        self._destroyEnemyHitIval()
        self.enemyHitIval = ival
        self.enemyHitIval.start()

    def isEnemyHitting(self):
        return self.legalEagleHitting

    def setEnemyHitting(self, value):
        self.legalEagleHitting = value

    def shouldLegalEagleBeInFrame(self):
        if not self.isLegalEagleTarget():
            return False
        else:
            index = len(self.legalEaglesTargeting) - 1
            eagle = self.legalEaglesTargeting[index]
            return eagle.shouldBeInFrame()

    def startHitRunningToonInterval(self):
        dur = self.toon.getDuration('slip-backward')
        self.startEnemyHitIval(Sequence(Wait(dur), Func(self.request, 'Running'), name='hitByLegalEagleIval-%i' % self.toon.doId))

    def startHitFlyingToonInterval(self):
        hitByEnemyPos = self.toon.getPos(render)
        collVec = hitByEnemyPos - self.collPos
        collVec[2] = 0.0
        collVec.normalize()
        collVec *= Globals.Gameplay.HitKnockbackDist

        def spinPlayer(t, rand):
            if rand == 0:
                self.toon.setH(-(t * 720.0))
            else:
                self.toon.setH(t * 720.0)

        direction = random.randint(0, 1)
        self.startEnemyHitIval(Sequence(Parallel(LerpFunc(spinPlayer, fromData=0.0, toData=1.0, duration=Globals.Gameplay.HitKnockbackTime, blendType='easeInOut', extraArgs=[direction]), LerpPosInterval(self.toon, duration=Globals.Gameplay.HitKnockbackTime, pos=hitByEnemyPos + collVec, blendType='easeOut')), Func(self.request, 'FreeFly'), name='hitByLegalEagleIval-%i' % self.toon.doId))

    def startHitByWhirlwindInterval(self):

        def spinPlayer(t):
            self.controlVelocity[2] = 1.0
            angle = math.radians(t * (720.0 * 2 - 180))
            self.toon.setPos(self.activeWhirlwind.model.getX(self.game.level.root) + math.cos(angle) * 2, self.activeWhirlwind.model.getY(self.game.level.root) + math.sin(angle) * 2, self.toon.getZ())

        def movePlayerBack(t):
            self.toon.setY(self.activeWhirlwind.model.getY(self.game.level.root) - t * Globals.Gameplay.WhirlwindMoveBackDist)

        self.startEventIval(Sequence(Func(self._cameraMgr.freeze), Func(self.activeWhirlwind.disable), LerpFunc(spinPlayer, fromData=0.0, toData=1.0, duration=Globals.Gameplay.WhirlwindSpinTime), LerpFunc(movePlayerBack, fromData=0.0, toData=1.0, duration=Globals.Gameplay.WhirlwindMoveBackTime, blendType='easeOut'), Func(self.activeWhirlwind.enable), Func(self._cameraMgr.unfreeze), Func(self.request, 'FreeFly'), name='spinPlayerIval-%i' % self.toon.doId))

    def handleEnterWhirlwind(self, whirlwind):
        self.activeWhirlwind = whirlwind
        self.request('InWhirlwind')

    def handleEnterEnemyHit(self, enemy, collPos):
        self.collPos = collPos
        if self.state in ['FlyingUp', 'FreeFly']:
            self.request('HitWhileFlying')
        elif self.state in ['Running']:
            self.request('HitWhileRunning')

    def handleEnterFan(self, fan):
        if fan in self.activeFans:
            return
        if len(self.activeFans) == 0:
            self._fanSfx.loop()
        self.activeFans.append(fan)
        if fan.index not in self.fanIndex2ToonVelocity:
            self.fanIndex2ToonVelocity[fan.index] = Vec3(0.0, 0.0, 0.0)
        if fan not in self.fansStillHavingEffect:
            self.fansStillHavingEffect.append(fan)

    def handleExitFan(self, fan):
        if fan in self.activeFans:
            self.activeFans.remove(fan)
        if len(self.activeFans) == 0:
            self._fanSfx.stop()

    def handleDebuffPowerup(self, pickupType, elapsedTime):
        self._invulDebuffSfx.play()
        CogdoFlyingPlayer.handleDebuffPowerup(self, pickupType, elapsedTime)
        messenger.send(CogdoFlyingGuiManager.ClearMessageDisplayEventName)

    def handleEnterGatherable(self, gatherable, elapsedTime):
        CogdoFlyingPlayer.handleEnterGatherable(self, gatherable, elapsedTime)
        if gatherable.type == Globals.Level.GatherableTypes.Memo:
            self.handleEnterMemo(gatherable)
        elif gatherable.type == Globals.Level.GatherableTypes.Propeller:
            self.handleEnterPropeller(gatherable)
        elif gatherable.type == Globals.Level.GatherableTypes.LaffPowerup:
            self._getLaffSfx.play()
        elif gatherable.type == Globals.Level.GatherableTypes.InvulPowerup:
            self._getRedTapeSfx.play()
            messenger.send(CogdoFlyingGuiManager.InvulnerableEventName)

    def handleEnterMemo(self, gatherable):
        self.score += 1
        if self.score == 1:
            self._guiMgr.presentMemoGui()
            self._guiMgr.setTemporaryMessage(TTLocalizer.CogdoFlyingGameMemoIntro, 4.0)
        self._guiMgr.setMemoCount(self.score)
        self._getMemoSfx.play()

    def handleEnterPropeller(self, gatherable):
        if self.fuel < 1.0:
            if not self.hasPickedUpFirstPropeller:
                messenger.send(CogdoFlyingGuiManager.PickedUpFirstPropellerEventName)
                self.introGuiSeq.clearToInitial()
                self.hasPickedUpFirstPropeller = True
                self.setPropellerState(CogdoFlyingLocalPlayer.PropStates.Normal)
            self.setFuel(1.0)
            self._guiMgr.update()
            self._refuelSfx.play()
            self._refuelSpinSfx.play(volume=0.15)
