import math
from direct.showbase.PythonUtil import bound, lerp
from direct.task.Task import Task
from direct.interval.MetaInterval import Sequence, Parallel
from direct.interval.FunctionInterval import Func, Wait
from direct.interval.SoundInterval import SoundInterval
from direct.interval.LerpInterval import LerpScaleInterval, LerpFunc
from direct.directnotify import DirectNotifyGlobal
from pandac.PandaModules import NodePath, Point3, VBase3
from toontown.minigame.OrthoDrive import OrthoDrive
from toontown.minigame.OrthoWalk import OrthoWalk
from toontown.battle.BattleProps import globalPropPool
from toontown.battle.BattleSounds import globalBattleSoundCache
import PartyGlobals
from PartyCogActivityInput import PartyCogActivityInput
from PartyCogActivityGui import PartyCogActivityGui
from PartyCogUtils import CameraManager
from PartyCogUtils import StrafingControl
UPDATE_TASK_NAME = 'PartyCogActivityLocalPlayer_UpdateTask'
THROW_PIE_LIMIT_TIME = 0.2

class PartyCogActivityPlayer:
    toon = None
    position = None
    team = None
    score = 0
    enabled = False
    notify = DirectNotifyGlobal.directNotify.newCategory('PartyCogActivityPlayer')

    def __init__(self, activity, toon, position, team):
        self.activity = activity
        self.position = position
        self.toon = toon
        self.team = team
        self.netTimeSentToStartByHit = 0
        self.kaboomTrack = None
        self.locator = None
        self.teamSpot = self.activity.getIndex(self.toon.doId, self.team)
        splatName = 'splat-creampie'
        self.splat = globalPropPool.getProp(splatName)
        self.splat.setBillboardPointEye()
        self.splatType = globalPropPool.getPropType(splatName)
        self.pieHitSound = globalBattleSoundCache.getSound('AA_wholepie_only.mp3')
        return

    def destroy(self):
        self.cleanUpIvals()
        self.toon = None
        self.locator = None
        self.position = None
        self.pieHitSound = None
        self.splat = None
        return

    def cleanUpIvals(self):
        if self.kaboomTrack is not None and self.kaboomTrack.isPlaying():
            self.kaboomTrack.finish()
        self.kaboomTrack = None
        return

    def faceForward(self):
        self.toon.setH(0)

    def setToonStartPosition(self, position):
        self.position = position

    def updateToonPosition(self):
        self.toon.setPos(self.activity.root, self.position)
        self.toon.setH(self.locator, 0.0)

    def setTeam(self, team):
        self.team = team
        self.locator = self.activity.view.teamLocators[self.team]
        self.teamSpot = self.activity.getIndex(self.toon.doId, self.team)

    def entersActivity(self):
        self.locator = self.activity.view.teamLocators[self.team]

    def exitsActivity(self):
        offset = 0
        if self.teamSpot:
            offset = 4.0 * self.teamSpot
        self.toon.wrtReparentTo(render)
        self.toon.setPos(self.locator, offset, -35.0, 0.0)
        self.toon.setH(self.activity.root, 0.0)
        self.locator = None
        return

    def enable(self):
        if self.enabled:
            return
        self.toon.wrtReparentTo(self.locator)
        self.enabled = True

    def disable(self):
        if not self.enabled:
            return
        self.toon.wrtReparentTo(render)
        self.enabled = False
        self.cleanUpIvals()

    def hitBody(self):
        points = PartyGlobals.CogActivityHitPoints
        self.score += points
        return points

    def hitHead(self):
        points = PartyGlobals.CogActivityHitPointsForHead
        self.score += points
        return points

    def resetScore(self):
        self.score = 0

    def respondToPieHit(self, timestamp, pos):
        if self.netTimeSentToStartByHit < timestamp:
            self.__showSplat(pos)
            if self.netTimeSentToStartByHit < timestamp:
                self.netTimeSentToStartByHit = timestamp
        else:
            self.activity.notify.debug('PartyCogPlayer respondToPieHit self.netTimeSentToStartByHit = %s' % self.netTimeSentToStartByHit)

    def __showSplat(self, position):
        if self.kaboomTrack is not None and self.kaboomTrack.isPlaying():
            self.kaboomTrack.finish()
        if not self.pieHitSound:
            self.notify.warning('Trying to play hit sound on destroyed player')
            return
        splatName = 'splat-creampie'
        self.splat = globalPropPool.getProp(splatName)
        self.splat.setBillboardPointEye()
        self.splat.reparentTo(render)
        self.splat.setPos(self.toon, position)
        self.splat.setY(self.toon, bound(self.splat.getY(), self.toon.getHeight() / 2.0, position.getY()))
        self.splat.setAlphaScale(1.0)
        targetscale = 0.75

        def setSplatAlpha(amount):
            self.splat.setAlphaScale(amount)

        self.kaboomTrack = Parallel(SoundInterval(self.pieHitSound, node=self.toon, volume=1.0, cutOff=PartyGlobals.PARTY_COG_CUTOFF), Sequence(Func(self.splat.showThrough), Parallel(Sequence(LerpScaleInterval(self.splat, duration=0.175, scale=targetscale, startScale=Point3(0.1, 0.1, 0.1), blendType='easeOut'), Wait(0.175)), Sequence(Wait(0.1), LerpFunc(setSplatAlpha, duration=1.0, fromData=1.0, toData=0.0, blendType='easeOut'))), Func(self.splat.cleanup), Func(self.splat.removeNode)))
        self.kaboomTrack.start()
        return


class PartyCogActivityLocalPlayer(PartyCogActivityPlayer):

    def __init__(self, activity, position, team, exitActivityCallback = None):
        PartyCogActivityPlayer.__init__(self, activity, base.localAvatar, position, team)
        self.input = PartyCogActivityInput(exitActivityCallback)
        self.gui = PartyCogActivityGui()
        self.throwPiePrevTime = 0
        self.lastMoved = 0
        if base.localAvatar:
            self.prevPos = base.localAvatar.getPos()
        self.cameraManager = None
        self.control = None
        self.consecutiveShortThrows = 0
        return

    def destroy(self):
        if self.enabled:
            self.disable()
        if self.cameraManager is not None:
            self.cameraManager.setEnabled(False)
            self.cameraManager.destroy()
        del self.cameraManager
        del self.gui
        del self.input
        if self.control is not None:
            self.control.destroy()
        del self.control
        PartyCogActivityPlayer.destroy(self)
        return

    def _initOrthoWalk(self):
        orthoDrive = OrthoDrive(9.778, customCollisionCallback=self.activity.view.checkOrthoDriveCollision)
        self.orthoWalk = OrthoWalk(orthoDrive, broadcast=True)

    def _destroyOrthoWalk(self):
        self.orthoWalk.stop()
        self.orthoWalk.destroy()
        del self.orthoWalk

    def getPieThrowingPower(self, time):
        elapsed = max(time - self.input.throwPiePressedStartTime, 0.0)
        w = 1.0 / PartyGlobals.CogActivityPowerMeterTime * 2.0 * math.pi
        power = int(round(-math.cos(w * elapsed) * 50.0 + 50.0))
        return power

    def isShortThrow(self, time):
        elapsed = max(time - self.input.throwPiePressedStartTime, 0.0)
        return elapsed <= PartyGlobals.CogActivityShortThrowTime

    def checkForThrowSpam(self, time):
        if self.isShortThrow(time):
            self.consecutiveShortThrows += 1
        else:
            self.consecutiveShortThrows = 0
        return self.consecutiveShortThrows >= PartyGlobals.CogActivityShortThrowSpam

    def _startUpdateTask(self):
        task = Task(self._updateTask)
        task.lastPositionBroadcastTime = 0.0
        self.throwPiePrevTime = 0
        taskMgr.add(task, UPDATE_TASK_NAME)

    def _stopUpdateTask(self):
        taskMgr.remove(UPDATE_TASK_NAME)

    def _updateTask(self, task):
        self._update()
        if base.localAvatar.getPos() != self.prevPos:
            self.prevPos = base.localAvatar.getPos()
            self.lastMoved = self.activity.getCurrentActivityTime()
        if max(self.activity.getCurrentActivityTime() - self.lastMoved, 0) > PartyGlobals.ToonMoveIdleThreshold:
            self.gui.showMoveControls()
        if max(self.activity.getCurrentActivityTime() - self.throwPiePrevTime, 0) > PartyGlobals.ToonAttackIdleThreshold:
            self.gui.showAttackControls()
        if self.input.throwPieWasReleased:
            if self.checkForThrowSpam(globalClock.getFrameTime()):
                self.gui.showSpamWarning()
            self.input.throwPieWasReleased = False
            self.throwPie(self.getPieThrowingPower(globalClock.getFrameTime()))
        return Task.cont

    def throwPie(self, piePower):
        if not self.activity.isState('Active'):
            return
        if self.activity.getCurrentActivityTime() - self.throwPiePrevTime > THROW_PIE_LIMIT_TIME:
            self.throwPiePrevTime = self.activity.getCurrentActivityTime()
            self.activity.b_pieThrow(self.toon, piePower)

    def _update(self):
        self.control.update()

    def getLookat(self, whosLooking, refNode = None):
        if refNode is None:
            refNode = render
        dist = 5.0
        oldParent = self.tempNP.getParent()
        self.tempNP.reparentTo(whosLooking)
        self.tempNP.setPos(0.0, dist, 0.0)
        pos = self.tempNP.getPos(refNode)
        self.tempNP.reparentTo(oldParent)
        return pos

    def entersActivity(self):
        base.cr.playGame.getPlace().setState('activity')
        PartyCogActivityPlayer.entersActivity(self)
        self.gui.disableToontownHUD()
        self.cameraManager = CameraManager(camera)
        self.tempNP = NodePath('temp')
        self.lookAtMyTeam()
        self.control = StrafingControl(self)

    def exitsActivity(self):
        PartyCogActivityPlayer.exitsActivity(self)
        self.gui.enableToontownHUD()
        self.cameraManager.setEnabled(False)
        self.tempNP.removeNode()
        self.tempNP = None
        if not aspect2d.find('**/JellybeanRewardGui*'):
            base.cr.playGame.getPlace().setState('walk')
        else:
            self.toon.startPosHprBroadcast()
        return

    def getRunToStartPositionIval(self):
        targetH = self.locator.getH()
        travelVec = self.position - self.toon.getPos(self.activity.root)
        duration = travelVec.length() / 9.778
        startH = 0.0
        if travelVec.getY() < 0.0:
            startH = 180.0
        return Sequence(Func(self.toon.startPosHprBroadcast, 0.1), Func(self.toon.b_setAnimState, 'run'), Parallel(self.toon.hprInterval(0.5, VBase3(startH, 0.0, 0.0), other=self.activity.root), self.toon.posInterval(duration, self.position, other=self.activity.root)), Func(self.toon.b_setAnimState, 'neutral'), self.toon.hprInterval(0.25, VBase3(targetH, 0.0, 0.0), other=self.activity.root), Func(self.toon.stopPosHprBroadcast))

    def enable(self):
        if self.enabled:
            return
        PartyCogActivityPlayer.enable(self)
        self.toon.b_setAnimState('Happy')
        self._initOrthoWalk()
        self.orthoWalk.start()
        self.orthoWalking = True
        self.input.enable()
        self.gui.disableToontownHUD()
        self.gui.load()
        self.gui.setScore(0)
        self.gui.showScore()
        self.gui.setTeam(self.team)
        self.gui.startTrackingCogs(self.activity.view.cogManager.cogs)
        self.control.enable()
        self._startUpdateTask()

    def disable(self):
        if not self.enabled:
            return
        self._stopUpdateTask()
        self.toon.b_setAnimState('neutral')
        PartyCogActivityPlayer.disable(self)
        self.orthoWalking = False
        self.orthoWalk.stop()
        self._destroyOrthoWalk()
        self.input.disable()
        self._aimMode = False
        self.cameraManager.setEnabled(False)
        self.gui.hide()
        self.gui.stopTrackingCogs()
        self.gui.unload()

    def updateScore(self):
        self.gui.setScore(self.score)

    def b_updateToonPosition(self):
        self.updateToonPosition()
        self.d_updateToonPosition()

    def d_updateToonPosition(self):
        self.toon.d_setPos(self.toon.getX(), self.toon.getY(), self.toon.getZ())
        self.toon.d_setH(self.toon.getH())

    def lookAtArena(self):
        self.cameraManager.setEnabled(True)
        self.cameraManager.setTargetPos(self.activity.view.arena.find('**/conclusionCamPos_locator').getPos(render))
        self.cameraManager.setTargetLookAtPos(self.activity.view.arena.find('**/conclusionCamAim_locator').getPos(render))

    def lookAtMyTeam(self):
        activityView = self.activity.view
        arena = activityView.arena
        pos = activityView.teamCamPosLocators[self.team].getPos()
        aim = activityView.teamCamAimLocators[self.team].getPos()
        camera.wrtReparentTo(arena)
        self.cameraManager.setPos(camera.getPos(render))
        self.tempNP.reparentTo(arena)
        self.tempNP.setPos(arena, pos)
        self.cameraManager.setTargetPos(self.tempNP.getPos(render))
        self.cameraManager.setLookAtPos(self.getLookat(camera))
        self.tempNP.reparentTo(arena)
        self.tempNP.setPos(arena, aim)
        self.cameraManager.setTargetLookAtPos(self.tempNP.getPos(render))
        self.cameraManager.setEnabled(True)
        camera.setP(0.0)
        camera.setR(0.0)
