import math
from pandac.PandaModules import *
from direct.distributed.ClockDelta import *
from direct.interval.IntervalGlobal import *
from otp.otpbase.PythonUtil import quantizeVec
from direct.task.Task import Task
from toontown.toontowngui import TTDialog
from toontown.toonbase.ToonBaseGlobal import *
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from toontown.effects import Splash, DustCloud, Wake
from toontown.minigame import Trajectory
from toontown.minigame import CannonGameGlobals
from toontown.parties import PartyGlobals
from toontown.parties.PartyGlobals import ActivityIds
from toontown.parties.PartyGlobals import ActivityTypes
from toontown.parties.PartyGlobals import FireworksStartedEvent
from toontown.parties.PartyGlobals import FireworksFinishedEvent
from toontown.parties.PartyGlobals import PartyCannonCollisions
from toontown.parties.DistributedPartyActivity import DistributedPartyActivity
from toontown.parties.CannonGui import CannonGui
from toontown.parties.PartyUtils import toRadians, toDegrees
CANNON_ROTATION_VEL = 15.0
CANNON_ANGLE_VEL = 15.0
GROUND_PLANE_MIN = -15
SHADOW_Z_OFFSET = 0.5
INITIAL_VELOCITY = 90.0
WHISTLE_SPEED = INITIAL_VELOCITY * 0.35

class DistributedPartyCannonActivity(DistributedPartyActivity):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedPartyCannonActivity')
    HIT_GROUND = 0
    HIT_TOWER = 1
    HIT_WATER = 2
    REACTIVATE_CLOUD_TASK = 'PartyActivity_ReactivateLastCloud'
    RULES_DONE_EVENT = 'DistributedPartyCannonActivity_RULES_DONE_EVENT'
    LOCAL_TOON_LANDED_EVENT = 'DistributedPartyCannonActivity_LOCAL_TOON_LANDED_EVENT'
    NetDivisor = 100
    TimeFactor = 0.75
    BroadcastPeriod = 0.2

    def __init__(self, cr):
        DistributedPartyActivity.__init__(self, cr, ActivityIds.PartyCannon, ActivityTypes.Continuous, wantRewardGui=True)
        self.gui = None
        self.firingCannon = None
        self.shadowNode = None
        self.partyDoId = None
        self.splash = None
        self.dustCloud = None
        self.lastWakeTime = 0
        self.localFlyingDropShadow = None
        self.localFlyingToon = None
        self.localFlyingToonId = 0
        self._lastBroadcastTime = -self.BroadcastPeriod
        self._dirtyNewVel = None
        self.hitBumper = 0
        self.hitCloud = 0
        self.lastPos = Vec3(0, 0, 0)
        self.lastVel = Vec3(0, 0, 0)
        self.vel = Vec3(0, 0, 0)
        self.landingPos = Vec3(0, 0, 0)
        self.t = 0
        self.lastT = 0
        self.deltaT = 0
        self._lastCloudHit = None
        self.cameraPos = Vec3(0, -15.0, -25.0)
        self.cameraSpeed = 5.0
        self.camNode = None
        self.flyingToonOffsetRotation = 0
        self.flyingToonOffsetAngle = 0
        self.flyingToonOffsetX = 0
        self.flyingToonOffsetY = 0
        self.flyingToonCloudsHit = 0
        self.initialFlyVel = 0
        self._localPlayedBefore = False
        self.hitTrack = None
        self.cTrav = None
        self.flyColNode = None
        self.flyColNodePath = None
        self._flyingCollisionTaskName = None
        return

    def generateInit(self):
        DistributedPartyActivity.generateInit(self)
        self.taskNameFireCannon = self.taskName('fireCannon')
        self.taskNameShoot = self.taskName('shootTask')
        self.taskNameFly = self.taskName('flyTask')
        self.gui = CannonGui()

    def load(self):
        self.notify.debug('load')
        DistributedPartyActivity.load(self)
        base.cr.playGame.hood.loader.loadClouds()
        base.cr.playGame.hood.loader.setCloudSwitch(1)
        self.shadow = loader.loadModel('phase_3/models/props/drop_shadow')
        self.shadowNode = hidden.attachNewNode('dropShadow')
        self.shadow.copyTo(self.shadowNode)
        self.shadowNode.setColor(0, 0, 0, 0.5)
        self.shadowNode.setBin('fixed', 0, 1)
        self.splash = Splash.Splash(render)
        self.dustCloud = DustCloud.DustCloud(render)
        self.dustCloud.setBillboardPointEye()
        self.sndHitGround = base.loader.loadSfx('phase_4/audio/sfx/MG_cannon_hit_dirt.ogg')
        self.sndHitWater = base.loader.loadSfx('phase_4/audio/sfx/MG_cannon_splash.ogg')
        self.sndHitHouse = base.loader.loadSfx('phase_5/audio/sfx/AA_drop_sandbag.ogg')
        self.sndBounce1 = base.loader.loadSfx('phase_13/audio/sfx/bounce1.ogg')
        self.sndBounce2 = base.loader.loadSfx('phase_13/audio/sfx/bounce2.ogg')
        self.sndBounce3 = base.loader.loadSfx('phase_13/audio/sfx/bounce3.ogg')
        self.onstage()
        self.sign.reparentTo(hidden)
        self.sign.setPos(-6.0, 10.0, 0.0)
        self.accept(FireworksStartedEvent, self.__handleFireworksStarted)
        self.accept(FireworksFinishedEvent, self.__handleFireworksFinished)

    def generate(self):
        DistributedPartyActivity.generate(self)
        self._doneCannons = False
        self._avId2trajectoryInfo = {}
        self._remoteToonFlyTaskName = 'remoteToonFlyTask-%s' % self.doId
        taskMgr.add(self._remoteToonFlyTask, self._remoteToonFlyTaskName, priority=45)
        self.d_cloudsColorRequest()

    def unload(self):
        self.notify.debug('unload')
        DistributedPartyActivity.unload(self)
        if self.shadowNode is not None:
            self.shadowNode.removeNode()
            del self.shadowNode
        if self.splash is not None:
            self.splash.destroy()
            del self.splash
        if self.dustCloud is not None:
            self.dustCloud.destroy()
            del self.dustCloud
        del self.sndHitHouse
        del self.sndHitGround
        del self.sndHitWater
        del self.sndBounce1
        del self.sndBounce2
        del self.sndBounce3
        if self.localFlyingToon:
            self.__resetToon(self.localFlyingToon)
            self.localFlyingToon.loop('neutral')
            self.localFlyingToon.setPlayRate(1.0, 'run')
            self.localFlyingToon = None
        self.ignoreAll()
        return

    def onstage(self):
        self.notify.debug('onstage')
        self.splash.reparentTo(render)
        self.dustCloud.reparentTo(render)

    def offstage(self):
        self.notify.debug('offstage')
        if self.splash is not None:
            self.splash.reparentTo(hidden)
            self.splash.stop()
        if self.dustCloud is not None:
            self.dustCloud.reparentTo(hidden)
            self.dustCloud.stop()
        return

    def disable(self):
        taskMgr.remove(self._remoteToonFlyTaskName)
        if self._flyingCollisionTaskName:
            taskMgr.remove(self._flyingCollisionTaskName)
        taskMgr.remove(self.taskNameFireCannon)
        taskMgr.remove(self.taskNameShoot)
        taskMgr.remove(self.taskNameFly)
        taskMgr.remove(DistributedPartyCannonActivity.REACTIVATE_CLOUD_TASK)
        self.ignoreAll()
        if self.localFlyingToonId:
            self.__stopCollisionHandler(self.localFlyingToon)
            self.__stopLocalFlyTask(self.localFlyingToonId)
            self.setMovie(PartyGlobals.CANNON_MOVIE_CLEAR, self.localFlyingToonId)
        if self.hitTrack is not None:
            self.hitTrack.finish()
            del self.hitTrack
            self.hitTrack = None
        DistributedPartyActivity.disable(self)
        return

    def delete(self):
        self.offstage()
        DistributedPartyActivity.delete(self)

    def setMovie(self, mode, toonId):
        self.notify.debug('%s setMovie(%s, %s)' % (self.doId, toonId, mode))
        if toonId != base.localAvatar.doId:
            return
        if mode == PartyGlobals.CANNON_MOVIE_CLEAR:
            self.landToon(toonId)
        elif mode == PartyGlobals.CANNON_MOVIE_LANDED:
            self.landToon(toonId)
        elif mode == PartyGlobals.CANNON_MOVIE_FORCE_EXIT:
            self.landToon(toonId)

    def __handleAvatarGone(self):
        self.setMovie(PartyGlobals.CANNON_MOVIE_CLEAR, 0)

    def handleToonDisabled(self, toonId):
        self.notify.warning('handleToonDisabled no implementation yet')

    def handleToonJoined(self, toonId):
        self.notify.warning('handleToonJoined no implementation yet')

    def isLocalToon(self, av):
        return base.localAvatar == av

    def isLocalToonId(self, toonId):
        return base.localAvatar.doId == toonId

    def getTitle(self):
        return TTLocalizer.PartyCannonActivityTitle

    def getInstructions(self):
        return TTLocalizer.PartyCannonActivityInstructions

    def hasPlayedBefore(self):
        return self._localPlayedBefore

    def displayRules(self):
        self.startRules()

    def handleRulesDone(self):
        self.finishRules()
        self._localPlayedBefore = True
        messenger.send(DistributedPartyCannonActivity.RULES_DONE_EVENT)

    def setCannonWillFire(self, cannonId, zRot, angle):
        self.notify.debug('setCannonWillFire: %d %d %d' % (cannonId, zRot, angle))
        cannon = base.cr.doId2do.get(cannonId)
        if cannon is None:
            self.notify.warning("Cannon has not been created, but we got this message. Don't show firing.")
            return
        if not cannon.getToonInside():
            self.notify.warning("setCannonWillFire, but no toon insde. Don't show firing")
            return
        if self.isLocalToon(cannon.getToonInside()):
            self.localFlyingToon = base.localAvatar
            self.localFlyingToonId = base.localAvatar.doId
            self.localFiringCannon = cannon
            self.flyingToonCloudsHit = 0
        cannon.updateModel(zRot, angle)
        toonId = cannon.getToonInside().doId
        task = Task(self.__fireCannonTask)
        task.toonId = toonId
        task.cannon = cannon
        taskMgr.add(task, self.taskNameFireCannon)
        self.toonIds.append(toonId)
        return

    def __fireCannonTask(self, task):
        launchTime = 0.0
        toonId = task.toonId
        cannon = task.cannon
        toon = cannon.getToonInside()
        self.notify.debug(str(self.doId) + ' FIRING CANNON FOR TOON ' + str(toonId))
        if not cannon.isToonInside():
            return Task.done
        if self.isLocalToonId(toonId):
            self.inWater = 0
            startPos, startHpr, startVel, trajectory = self.__calcFlightResults(cannon, toonId, launchTime)

            self.notify.debug('start position: ' + str(startPos))
            self.notify.debug('start velocity: ' + str(startVel))
            self.notify.debug('time of launch: ' + str(launchTime))
        cannon.removeToonReadyToFire()
        shootTask = Task(self.__shootTask, self.taskNameShoot)
        shootTask.info = {'toonId': toonId,
         'cannon': cannon}
        if self.isLocalToonId(toonId):
            self.flyingToonOffsetRotation = 0
            self.flyingToonOffsetAngle = 0
            self.flyingToonOffsetX = 0
            self.flyingToonOffsetY = 0
            self.hitCloud = 0
            self.initialFlyVel = INITIAL_VELOCITY
            self.camNode = NodePath(self.uniqueName('flyingCamera'))
            self.camNode.setScale(0.5)
            self.camNode.setPos(self.localFlyingToon.getPos())
            self.camNode.setHpr(self.localFlyingToon.getHpr())
            self.camNode.reparentTo(render)
            self.lastStartVel = startVel
            place = base.cr.playGame.getPlace()
            place.fsm.request('activity')
            toon.dropShadow.hide()
            self.localFlyingDropShadow = self.shadowNode.copyTo(hidden)
            vel = startVel
            toon.lookAt(toon.getPos() + Vec3(vel[0], vel[1], vel[2]))
            toon.setP(localAvatar, -90)
            hpr = toon.getHpr()
            toon.d_setPosHpr(startPos[0], startPos[1], startPos[2], hpr[0], hpr[1], hpr[2])
            self.localFlyingToon.wrtReparentTo(render)
            info = {}
            info['toonId'] = toonId
            info['trajectory'] = trajectory
            info['launchTime'] = launchTime
            info['toon'] = self.localFlyingToon
            info['hRot'] = cannon.getRotation()
            camera.wrtReparentTo(self.localFlyingToon)
            flyTask = Task(self.__localFlyTask, self.taskNameFly)
            flyTask.info = info
            seqTask = Task.sequence(shootTask, flyTask)
            self.__startCollisionHandler()
            self.notify.debug('Disable standard local toon controls.')
            base.localAvatar.disableAvatarControls()
            frameTime = globalClock.getFrameTime()
            netLaunchTime = globalClockDelta.localToNetworkTime(launchTime + frameTime, bits=31)
            self.sendUpdate('setToonTrajectoryAi', [netLaunchTime,
             startPos[0],
             startPos[1],
             startPos[2],
             startHpr[0],
             startHpr[1],
             startHpr[2],
             startVel[0],
             startVel[1],
             startVel[2]])
        else:
            seqTask = shootTask
        taskMgr.add(seqTask, self.taskName('flyingToon') + '-' + str(toonId))
        toon.startSmooth()
        return Task.done

    def setToonTrajectory(self, avId, launchTime, x, y, z, h, p, r, vx, vy, vz):
        if avId == localAvatar.doId:
            return
        startPos = Vec3(x, y, z)
        startHpr = Vec3(h, p, r)
        startVel = Vec3(vx, vy, vz)
        startT = globalClockDelta.networkToLocalTime(launchTime, bits=31) + 0.2
        trajectory = Trajectory.Trajectory(0.0, startPos, startVel)
        self._avId2trajectoryInfo[avId] = ScratchPad(startPos=startPos, startHpr=startHpr, startVel=startVel, startT=startT, trajectory=trajectory)

    def _remoteToonFlyTask(self, task = None):
        ids2del = []
        frameTime = globalClock.getFrameTime()
        for avId, trajInfo in self._avId2trajectoryInfo.items():
            trajectory = trajInfo.trajectory
            startTime = trajInfo.startT
            groundTime = trajectory.calcTimeOfImpactOnPlane(0.0) / self.TimeFactor + startTime
            now = frameTime
            if now < startTime:
                now = startTime
            if now > groundTime:
                now = groundTime
            t = max(0.0, now - startTime)
            t *= self.TimeFactor
            toon = self.cr.getDo(avId)
            if toon is None:
                ids2del.append(avId)
            else:
                toon.setFluidPos(trajectory.getPos(t))
                vel = trajectory.getVel(t)
                toon.lookAt(toon.getPos() + Vec3(vel[0], vel[1], vel[2]))
                toon.setP(toon, -90)

        for avId in ids2del:
            del self._avId2trajectoryInfo[avId]

        return Task.cont

    def __calcFlightResults(self, cannon, toonId, launchTime):
        startPos = cannon.getToonFirePos()
        startHpr = cannon.getToonFireHpr()
        startVel = cannon.getToonFireVel()
        quantizeVec(startPos, self.NetDivisor)
        quantizeVec(startHpr, self.NetDivisor)
        quantizeVec(startVel, self.NetDivisor)
        trajectory = Trajectory.Trajectory(launchTime, startPos, startVel)
        self.trajectory = trajectory
        return startPos, startHpr, startVel, trajectory

    def __shootTask(self, task):
        task.info['cannon'].fire()
        toonId = task.info['toonId']
        toon = base.cr.doId2do.get(toonId)
        if toon:
            toon.loop('swim')
        else:
            self.notify.debug('__shootTask avoided a crash, toon %d not found' % toonId)
        if self.isLocalToonId(task.info['toonId']):
            self.localFlyingDropShadow.reparentTo(render)
            self.gui.enableAimKeys()
        return Task.done

    def d_setLanded(self, toonId):
        printStack()
        self.notify.debug('d_setLanded %s' % toonId)
        if self.isLocalToonId(toonId):
            if self.cr:
                self.sendUpdate('setLanded', [toonId])
            else:
                self.notify.debug('we avoided crash 2')

    def setLanded(self, toonId):
        if toonId in self._avId2trajectoryInfo:
            del self._avId2trajectoryInfo[toonId]

    def landToon(self, toonId):
        self.notify.debug('%s landToon' % self.doId)
        toon = base.cr.doId2do.get(toonId)
        if toon is not None:
            toon.resetLOD()
            if toon == base.localAvatar:
                self.__stopCollisionHandler(base.localAvatar)
            toon.wrtReparentTo(render)
            self.__setToonUpright(toon)
            toon.setPlayRate(1.0, 'run')
            toon.startSmooth()
            toon.setScale(1.0)
            self.ignore(toon.uniqueName('disable'))
            self.__cleanupFlyingToonData(toon)
            toon.dropShadow.show()
        place = base.cr.playGame.getPlace()
        if place is not None:
            if not hasattr(place, 'fsm'):
                return
        if toon is not None and toon == base.localAvatar:
            self.__localDisplayLandedResults()
        return

    def __localDisplayLandedResults(self):
        if self.flyingToonCloudsHit > 0:
            self._doneCannons = True
        else:
            self.__localToonDoneLanding()

    def handleRewardDone(self):
        DistributedPartyActivity.handleRewardDone(self)
        if self._doneCannons:
            self.__localToonDoneLanding()

    def __localToonDoneLanding(self):
        base.cr.playGame.getPlace().fsm.request('walk')
        self.notify.debug('__localToonDoneLanding')
        base.localAvatar.collisionsOn()
        base.localAvatar.startPosHprBroadcast()
        base.localAvatar.enableAvatarControls()
        messenger.send(DistributedPartyCannonActivity.LOCAL_TOON_LANDED_EVENT)

    def __setToonUpright(self, toon, pos = None):
        if toon:
            if self.inWater:
                toon.setP(0)
                toon.setR(0)
                return
            if not pos:
                pos = toon.getPos(render)
            toon.setPos(render, pos)
            toon.loop('neutral')
            if self.localFiringCannon and hasattr(self.localFiringCannon, 'cannonNode'):
                if self.localFiringCannon.cannonNode:
                    toon.lookAt(self.localFiringCannon.cannonNode)
                else:
                    self.notify.debug('we avoided crash 1.')
            toon.setP(0)
            toon.setR(0)
            toon.setScale(1, 1, 1)

    def __resetToonToCannon(self, avatar):
        self.notify.debug('__resetToonToCannon')
        if not avatar and self.localFlyingToonId:
            avatar = base.cr.doId2do.get(self.localFlyingToonId, None)
        if avatar:
            self.__resetToon(avatar)
        return

    def __resetToon(self, avatar, pos = None):
        self.notify.debug('__resetToon')
        if avatar:
            self.__stopCollisionHandler(avatar)
            self.__setToonUpright(avatar, pos)
            if self.isLocalToonId(avatar.doId):
                self.notify.debug('toon setting position to %s' % pos)
                if pos:
                    base.localAvatar.setPos(pos)
                camera.reparentTo(avatar)
            self.d_setLanded(avatar.doId)

    def __updateFlightVelocity(self, trajectory):
        hpr = LRotationf(self.flyingToonOffsetRotation, 0, 0)
        newVel = hpr.xform(self.lastStartVel)
        hpr = LRotationf(0, self.flyingToonOffsetAngle, 0)
        zVel = hpr.xform(self.lastStartVel).getZ()
        if zVel < newVel.getZ():
            newVel.setZ(zVel)
        trajectory.setStartVel(newVel)
        now = globalClock.getFrameTime()
        if now - self._lastBroadcastTime >= self.BroadcastPeriod:
            self._dirtyNewVel = newVel
        if self._dirtyNewVel:
            self.sendUpdate('updateToonTrajectoryStartVelAi', [self._dirtyNewVel[0], self._dirtyNewVel[1], self._dirtyNewVel[2]])
            self._lastBroadcastTime = now
            self._dirtyNewVel = None
        return

    def updateToonTrajectoryStartVel(self, avId, vx, vy, vz):
        if avId == localAvatar.doId:
            return
        if avId in self._avId2trajectoryInfo:
            self._avId2trajectoryInfo[avId].trajectory.setStartVel(Vec3(vx, vy, vz))

    def __isFlightKeyPressed(self):
        return self.gui.leftPressed or self.gui.rightPressed or self.gui.upPressed or self.gui.downPressed

    def __moveFlyingToon(self, toon):
        toonP = toon.getP(render)
        isToonFlyingHorizontal = toonP > -150 and toonP < -30
        OFFSET = 0.25
        rotVel = 0
        if self.gui.leftPressed:
            if isToonFlyingHorizontal:
                rotVel += CANNON_ROTATION_VEL
            else:
                self.flyingToonOffsetX -= OFFSET
        if self.gui.rightPressed:
            if isToonFlyingHorizontal:
                rotVel -= CANNON_ROTATION_VEL
            else:
                self.flyingToonOffsetX += OFFSET
        self.flyingToonOffsetRotation += rotVel * globalClock.getDt()
        angVel = 0
        if self.gui.upPressed:
            if not isToonFlyingHorizontal:
                self.flyingToonOffsetY -= OFFSET
        if self.gui.downPressed:
            if isToonFlyingHorizontal:
                angVel += CANNON_ANGLE_VEL
            else:
                self.flyingToonOffsetY += OFFSET
        self.flyingToonOffsetAngle += angVel * globalClock.getDt()

    def __stopLocalFlyTask(self, toonId):
        taskMgr.remove(self.taskName('flyingToon') + '-' + str(toonId))
        self.gui.disableAimKeys()

    def __localFlyTask(self, task):
        toon = task.info['toon']
        if toon.isEmpty():
            self.__resetToonToCannon(self.localFlyingToon)
            return Task.done
        curTime = task.time + task.info['launchTime']
        t = curTime
        t *= self.TimeFactor
        self.lastT = self.t
        self.t = t
        deltaT = self.t - self.lastT
        self.deltaT = deltaT
        if self.hitBumper:
            pos = self.lastPos + self.lastVel * deltaT
            vel = self.lastVel
            self.lastVel += Vec3(0, 0, -32.0) * deltaT
            self.lastPos = pos
            toon.setFluidPos(pos)
            lastR = toon.getR()
            toon.setR(lastR - deltaT * self.angularVel * 2.0)
            cameraView = 0
        else:
            if not self.hitCloud and self.__isFlightKeyPressed():
                self.__moveFlyingToon(toon)
                self.__updateFlightVelocity(task.info['trajectory'])
            if self.hitCloud == 1:
                vel = task.info['trajectory'].getVel(t)
                startPos = toon.getPos(render)
                task.info['trajectory'].setStartTime(t)
                task.info['trajectory'].setStartPos(startPos)
                task.info['trajectory'].setStartVel(self.lastVel)
                toon.lookAt(toon.getPos() + vel)
                toon.setH(-toon.getH())
                now = globalClock.getFrameTime()
                netLaunchTime = globalClockDelta.localToNetworkTime(now, bits=31)
                hpr = toon.getHpr()
                self.sendUpdate('setToonTrajectoryAi', [netLaunchTime,
                 startPos[0],
                 startPos[1],
                 startPos[2],
                 hpr[0],
                 hpr[1],
                 hpr[2],
                 self.lastVel[0],
                 self.lastVel[1],
                 self.lastVel[2]])
                self._lastBroadcastTime = now
                self._dirtyNewVel = None
                self.flyingToonOffsetRotation = 0
                self.flyingToonOffsetAngle = 0
                self.flyingToonOffsetX = 0
                self.flyingToonOffsetY = 0
                self.hitCloud = 2
            pos = task.info['trajectory'].getPos(t)
            toon.setFluidPos(pos)
            toon.setFluidPos(toon, self.flyingToonOffsetX, self.flyingToonOffsetY, 0)
            vel = task.info['trajectory'].getVel(t)
            toon.lookAt(toon.getPos() + Vec3(vel[0], vel[1], vel[2]))
            toon.setP(toon.getP() - 90)
            cameraView = 2
            if self.hitCloud == 2:
                self.lastStartVel = vel
                self.hitCloud = 0
        shadowPos = toon.getPos()
        shadowPos.setZ(SHADOW_Z_OFFSET)
        self.localFlyingDropShadow.setPos(shadowPos)
        if pos.getZ() < -20 or pos.getZ() > 1000:
            self.notify.debug('stopping fly task toon.getZ()=%.2f' % pos.getZ())
            self.__resetToonToCannon(self.localFlyingToon)
            return Task.done
        self.__setFlyingCameraView(task.info['toon'], cameraView, deltaT)
        return Task.cont

    def __setFlyingCameraView(self, toon, view, deltaT):
        if toon != base.localAvatar:
            return
        lookAt = toon.getPos(render)
        hpr = toon.getHpr(render)
        if view == 0:
            camera.wrtReparentTo(render)
            camera.lookAt(lookAt)
        elif view == 1:
            camera.reparentTo(render)
            camera.setPos(render, 100, 100, 35.25)
            camera.lookAt(render, lookAt)
        elif view == 2:
            if camera.getParent() != self.camNode:
                camera.wrtReparentTo(self.camNode)
                camera.setPos(self.cameraPos)
                camera.lookAt(toon)
            self.camNode.setPos(toon.getPos(render))
            camHpr = self.camNode.getHpr(toon)
            vec = -Point3(0, 0, 0) - camHpr
            relativeSpeed = math.pow(vec.length() / 60.0, 2) + 0.1
            newHpr = camHpr + vec * deltaT * self.cameraSpeed * relativeSpeed
            self.camNode.setHpr(toon, newHpr)
            camera.lookAt(self.camNode)
            camera.setR(render, 0)

    def __cleanupFlyingToonData(self, toon):
        self.notify.debug('__cleanupFlyingToonData')
        if toon:
            toon.dropShadow.show()
            self.toonIds.remove(toon.doId)
            if self.isLocalToon(toon):
                if self.localFlyingDropShadow != None:
                    self.localFlyingDropShadow.removeNode()
                    self.localFlyingDropShadow = None
                self.hitBumper = 0
                self.angularVel = 0
                self.vel = Vec3(0, 0, 0)
                self.lastVel = Vec3(0, 0, 0)
                self.lastPos = Vec3(0, 0, 0)
                self.landingPos = Vec3(0, 0, 0)
                self.t = 0
                self.lastT = 0
                self.deltaT = 0
                self.lastWakeTime = 0
                self.localFlyingToon = None
                self.localFlyingToonId = 0
                self.localFiringCannon = None
                if hasattr(self, 'camNode') and self.camNode:
                    self.camNode.removeNode()
                    self.camNode = None
        return

    def __startCollisionHandler(self):
        self.flyColSphere = CollisionSphere(0, 0, self.localFlyingToon.getHeight() / 2.0, 1.0)
        self.flyColNode = CollisionNode(self.uniqueName('flySphere'))
        self.flyColNode.setCollideMask(ToontownGlobals.WallBitmask | ToontownGlobals.FloorBitmask)
        self.flyColNode.addSolid(self.flyColSphere)
        self.flyColNodePath = self.localFlyingToon.attachNewNode(self.flyColNode)
        self.flyColNodePath.setColor(1, 0, 0, 1)
        self._activeCollisions = set()
        self.handler = CollisionHandlerQueue()
        self._flyingCollisionTaskName = 'checkFlyingToonCollision-%s' % self.doId
        taskMgr.add(self._checkFlyingToonCollision, self._flyingCollisionTaskName)
        base.cTrav.addCollider(self.flyColNodePath, self.handler)

    def __stopCollisionHandler(self, avatar):
        self.notify.debug('%s __stopCollisionHandler' % self.doId)
        if self._flyingCollisionTaskName:
            taskMgr.remove(self._flyingCollisionTaskName)
            self._flyingCollisionTaskName = None
            self._activeCollisions = set()
        if avatar:
            avatar.loop('neutral')
            if self.flyColNode:
                self.flyColNode = None
            self.flyColSphere = None
            if self.flyColNodePath:
                base.cTrav.removeCollider(self.flyColNodePath)
                self.flyColNodePath.removeNode()
                self.flyColNodePath = None
            self.handler = None
        return

    def _checkFlyingToonCollision(self, task = None):
        curCollisions = set()
        if self.handler.getNumEntries():
            self.handler.sortEntries()
            i = self.handler.getNumEntries()
            activeEntry = None
            while i > 0:
                entry = self.handler.getEntry(i - 1)
                k = (str(entry.getFromNodePath()), str(entry.getIntoNodePath()))
                curCollisions.add(k)
                if activeEntry is None and k not in self._activeCollisions:
                    activeEntry = entry
                    self._activeCollisions.add(k)
                i -= 1

            if activeEntry is not None:
                self.__handleFlyingToonCollision(activeEntry)
            if self.handler:
                self.handler.clearEntries()
        for k in list(self._activeCollisions):
            if k not in curCollisions:
                self._activeCollisions.remove(k)

        return Task.cont

    def __handleFlyingToonCollision(self, collisionEntry):
        self.notify.debug('%s __handleToonCollision' % self.doId)
        if self.localFlyingToon == None or self.flyColNode == None:
            return
        hitNode = collisionEntry.getIntoNode().getName()
        self.notify.debug('hitNode = %s' % hitNode)
        self.notify.debug('hitNodePath.getParent = %s' % collisionEntry.getIntoNodePath().getParent())
        self.vel = self.trajectory.getVel(self.t)
        vel = self.trajectory.getVel(self.t)
        vel.normalize()
        if self.hitBumper:
            vel = self.lastVel * 1
            vel.normalize()
        self.notify.debug('normalized vel=%s' % vel)
        solid = collisionEntry.getInto()
        intoNormal = collisionEntry.getSurfaceNormal(collisionEntry.getIntoNodePath())
        self.notify.debug('old intoNormal = %s' % intoNormal)
        intoNormal = collisionEntry.getSurfaceNormal(render)
        self.notify.debug('new intoNormal = %s' % intoNormal)
        hitPylonAboveWater = False
        hitPylonBelowWater = False
        hitNormal = intoNormal
        if hitNode.find('cSphere') == 0 or hitNode.find('treasureSphere') == 0 or hitNode.find('prop') == 0 or hitNode.find('distAvatarCollNode') == 0 or hitNode.find('CannonSphere') == 0 or hitNode.find('plotSphere') == 0 or hitNode.find('flySphere') == 0 or hitNode.find('FishingSpotSphere') == 0 or hitNode.find('TrampolineTrigger') == 0 or hitNode == 'gagtree_collision' or hitNode == 'sign_collision' or hitNode == 'FlowerSellBox' or hitPylonBelowWater:
            self.notify.debug('--------------hit and ignoring %s' % hitNode)
            return
        if vel.dot(hitNormal) > 0 and not hitNode == 'collision_roof' and not hitNode == 'collision_fence':
            self.notify.debug('--------------hit and ignoring backfacing %s, dot=%s' % (hitNode, vel.dot(hitNormal)))
            return
        intoNode = collisionEntry.getIntoNodePath()
        bumperNodes = ['sky_collision'] + PartyCannonCollisions['bounce'] + PartyCannonCollisions['fence']
        cloudBumpers = PartyCannonCollisions['clouds']
        bumperNodes += cloudBumpers
        if hitNode in bumperNodes or hitNode.find('cogPie') == 0 or PartyCannonCollisions['trampoline_bounce'] in hitNode:
            if hitNode == 'sky_collision' or hitNode in PartyCannonCollisions['fence'] or hitNode.find('cogPie') == 0:
                self.__hitFence(self.localFlyingToon, collisionEntry)
            elif PartyCannonCollisions['trampoline_bounce'] in hitNode or hitNode in PartyCannonCollisions['bounce']:
                if hitNode == 'wall_collision':
                    hitSound = self.sndBounce2
                else:
                    hitSound = self.sndBounce3
                self.hitCloud = 1
                self.__hitBumper(self.localFlyingToon, collisionEntry, hitSound, kr=0.09, angVel=5)
                self.hitBumper = 0
            elif hitNode in cloudBumpers:
                self.__hitCloudPlatform(self.localFlyingToon, collisionEntry)
            elif hitNode == 'statuaryCol':
                self.__hitStatuary(self.localFlyingToon, collisionEntry)
            else:
                self.notify.debug('*************** hit something else ************')
            return
        else:
            self.__stopCollisionHandler(self.localFlyingToon)
            self.__stopLocalFlyTask(self.localFlyingToonId)
            self.notify.debug('stopping flying since we hit %s' % hitNode)
        if self.isLocalToonId(self.localFlyingToon.doId):
            camera.wrtReparentTo(render)
        if self.localFlyingDropShadow:
            self.localFlyingDropShadow.reparentTo(hidden)
        pos = collisionEntry.getSurfacePoint(render)
        hpr = self.localFlyingToon.getHpr()
        hitPos = collisionEntry.getSurfacePoint(render)
        pos = hitPos
        self.landingPos = pos
        self.notify.debug('hitNode, Normal = %s,%s' % (hitNode, intoNormal))
        track = Sequence()
        track.append(Func(self.localFlyingToon.wrtReparentTo, render))
        if self.isLocalToonId(self.localFlyingToon.doId):
            track.append(Func(self.localFlyingToon.collisionsOff))
        if hitNode in PartyCannonCollisions['ground']:
            track.append(Func(self.__hitGround, self.localFlyingToon, pos))
            track.append(Wait(1.0))
            track.append(Func(self.__setToonUpright, self.localFlyingToon, self.landingPos))
        elif hitNode in PartyCannonCollisions['fence']:
            track.append(Func(self.__hitFence, self.localFlyingToon, collisionEntry))
        elif hitNode == 'collision3':
            track.append(Func(self.__hitWater, self.localFlyingToon, pos, collisionEntry))
            track.append(Wait(2.0))
            track.append(Func(self.__setToonUpright, self.localFlyingToon, self.landingPos))
        elif hitNode.find('cloudSphere') == 0:
            track.append(Func(self.__hitCloudPlatform, self.localFlyingToon, collisionEntry))
        else:
            self.notify.warning('************* unhandled hitNode=%s parent =%s' % (hitNode, collisionEntry.getIntoNodePath().getParent()))
        track.append(Func(self.d_setLanded, self.localFlyingToonId))
        if self.isLocalToonId(self.localFlyingToonId):
            track.append(Func(self.localFlyingToon.collisionsOn))
        if self.hitTrack:
            self.hitTrack.finish()
        self.hitTrack = track
        self.hitTrack.start()
        return

    def __hitBumper(self, avatar, collisionEntry, sound, kr = 0.6, angVel = 1):
        self.hitBumper = 1
        base.playSfx(sound)
        hitP = avatar.getPos(render)
        self.lastPos = hitP
        normal = collisionEntry.getSurfaceNormal(render)
        self.notify.debug('normal = %s' % normal)
        vel = self.vel * 1
        speed = vel.length()
        vel.normalize()
        self.notify.debug('old vel = %s' % vel)
        if self.hitCloud:
            centerVec = Vec3(-avatar.getPos(self.getParentNodePath()))
            centerVec.setZ(0)
            d = centerVec.length() / 15.0
            centerVec.setZ(abs(centerVec.length() * math.sin(70.0)))
            centerVec.normalize()
            newVel = centerVec * d + normal * 0.2
            newVel = newVel * (kr * speed)
            self.initialFlyVel = kr * speed
        else:
            newVel = (normal * 2.0 + vel) * (kr * speed)
        self.lastVel = newVel
        self.notify.debug('new vel = %s' % newVel)
        self.angularVel = angVel * 360
        if self.hitCloud:
            return
        t = Sequence(Func(avatar.pose, 'lose', 110))
        t.start()

    def __hitGround(self, avatar, pos, extraArgs = []):
        self.notify.debug('__hitGround')
        hitP = avatar.getPos(render)
        self.notify.debug('hitGround pos = %s, hitP = %s' % (pos, hitP))
        self.notify.debug('avatar hpr = %s' % avatar.getHpr())
        avatar.setPos(pos[0], pos[1], pos[2] + avatar.getHeight() / 3.0)
        avatar.setHpr(avatar.getH(), -135, 0)
        self.notify.debug('parent = %s' % avatar.getParent())
        self.notify.debug('pos = %s, hpr = %s' % (avatar.getPos(render), avatar.getHpr(render)))
        self.__playDustCloud(avatar, pos)
        base.playSfx(self.sndHitGround)
        avatar.setPlayRate(2.0, 'run')
        avatar.loop('run')

    def __playDustCloud(self, toon, pos):
        self.dustCloud.setPos(render, pos[0], pos[1], pos[2] + toon.getHeight() / 3.0)
        self.dustCloud.setScale(0.35)
        self.dustCloud.play()

    def __hitFence(self, avatar, collisionEntry, extraArgs = []):
        self.notify.debug('__hitFence')
        self.__hitBumper(avatar, collisionEntry, self.sndHitHouse, kr=0.2, angVel=3)

    def __hitWater(self, avatar, pos, collisionEntry, extraArgs = []):
        hitP = avatar.getPos(render)
        if hitP[2] > ToontownGlobals.EstateWakeWaterHeight:
            self.notify.debug('we hit the ground before we hit water')
            self.__hitGround(avatar, pos, extraArgs)
            return
        self.notify.debug('hit water')
        hitP = avatar.getPos(render)
        avatar.loop('neutral')
        self.splash.setPos(hitP)
        self.splash.setZ(ToontownGlobals.EstateWakeWaterHeight)
        self.splash.setScale(2)
        self.splash.play()
        base.playSfx(self.sndHitWater)
        place = base.cr.playGame.getPlace()

    def __hitStatuary(self, avatar, collisionEntry, extraArgs = []):
        self.__hitBumper(avatar, collisionEntry, self.sndHitHouse, kr=0.4, angVel=5)

    def d_cloudsColorRequest(self):
        self.notify.debug('cloudsColorRequest')
        self.sendUpdate('cloudsColorRequest')

    def cloudsColorResponse(self, cloudColorList):
        self.notify.debug('cloudsColorResponse: %s' % cloudColorList)
        for cloudColor in cloudColorList:
            self.setCloudHit(*cloudColor)

    def d_requestCloudHit(self, cloudNumber, color):
        self.sendUpdate('requestCloudHit', [cloudNumber,
         color.getX(),
         color.getY(),
         color.getZ()])

    def setCloudHit(self, cloudNumber, r, g, b):
        cloud = render.find('**/cloud-%d' % cloudNumber)
        if not cloud.isEmpty():
            cloud.setColor(r, g, b, 1.0)
        else:
            self.notify.debug('Could not find cloud-%d' % cloudNumber)

    def __hitCloudPlatform(self, avatar, collisionEntry, extraArgs = []):
        if not self.hitBumper and not self.hitCloud:
            self.hitCloud = 1
            self.__hitBumper(avatar, collisionEntry, self.sndBounce1, kr=0.35, angVel=5)
            self.hitBumper = 0
            if self._lastCloudHit is None:
                cloud = collisionEntry.getIntoNodePath().getParent()
                self._lastCloudHit = cloud
                cloud.setColor(base.localAvatar.style.getHeadColor())
                cloudNumber = int(cloud.getNetTag('number'))
                self.d_requestCloudHit(cloudNumber, base.localAvatar.style.getHeadColor())
                self.__playDustCloud(avatar, collisionEntry.getSurfacePoint(render))
                self.flyingToonCloudsHit += 1
                taskMgr.doMethodLater(0.25, self.__reactivateLastCloudHit, DistributedPartyCannonActivity.REACTIVATE_CLOUD_TASK)
        return

    def __reactivateLastCloudHit(self, task):
        self._lastCloudHit = None
        return Task.done

    def __handleFireworksStarted(self):
        self.notify.debug('__handleFireworksStarted')
        base.cr.playGame.hood.loader.fadeClouds()

    def __handleFireworksFinished(self):
        self.notify.debug('__handleFireworksFinished')
        if self.__checkHoodValidity():
            base.cr.playGame.hood.loader.fadeClouds()
        else:
            self.notify.debug('Toon has left the party')

    def __checkHoodValidity(self):
        if hasattr(base.cr.playGame, 'hood') and base.cr.playGame.hood and hasattr(base.cr.playGame.hood, 'loader') and base.cr.playGame.hood.loader and hasattr(base.cr.playGame.hood.loader, 'geom') and base.cr.playGame.hood.loader.geom:
            return True
        else:
            return False

    def handleToonExited(self, toonId):
        self.notify.debug('DistributedPartyCannonActivity handleToonExited( toonId=%s ) ' % toonId)
        if toonId in self.cr.doId2do:
            self.notify.warning('handleToonExited is not defined')
