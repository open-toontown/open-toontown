from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *
from direct.task.TaskManagerGlobal import *
from direct.distributed.ClockDelta import *
from direct.directnotify import DirectNotifyGlobal
from . import GoonGlobals
from direct.task.Task import Task
from toontown.toonbase import ToontownGlobals
from otp.otpbase import OTPGlobals
from toontown.coghq import DistributedCashbotBossObject
from direct.showbase import PythonUtil
from . import DistributedGoon

class DistributedCashbotBossGoon(DistributedGoon.DistributedGoon, DistributedCashbotBossObject.DistributedCashbotBossObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedCashbotBossGoon')
    walkGrabZ = -3.6
    stunGrabZ = -2.2
    wiggleFreeTime = 2
    craneFrictionCoef = 0.15
    craneSlideSpeed = 10
    craneRotateSpeed = 20

    def __init__(self, cr):
        DistributedCashbotBossObject.DistributedCashbotBossObject.__init__(self, cr)
        DistributedGoon.DistributedGoon.__init__(self, cr)
        self.target = None
        self.arrivalTime = None
        self.flyToMagnetSfx = loader.loadSfx('phase_5/audio/sfx/TL_rake_throw_only.ogg')
        self.hitMagnetSfx = loader.loadSfx('phase_4/audio/sfx/AA_drop_anvil_miss.ogg')
        self.toMagnetSoundInterval = Sequence(SoundInterval(self.flyToMagnetSfx, duration=ToontownGlobals.CashbotBossToMagnetTime, node=self), SoundInterval(self.hitMagnetSfx, node=self))
        self.hitFloorSfx = loader.loadSfx('phase_5/audio/sfx/AA_drop_flowerpot.ogg')
        self.hitFloorSoundInterval = SoundInterval(self.hitFloorSfx, duration=1.0, node=self)
        self.wiggleSfx = loader.loadSfx('phase_5/audio/sfx/SA_finger_wag.ogg')
        return

    def generate(self):
        DistributedCashbotBossObject.DistributedCashbotBossObject.generate(self)
        DistributedGoon.DistributedGoon.generate(self)

    def announceGenerate(self):
        DistributedCashbotBossObject.DistributedCashbotBossObject.announceGenerate(self)
        self.setupPhysics('goon')
        DistributedGoon.DistributedGoon.announceGenerate(self)
        self.name = 'goon-%s' % self.doId
        self.setName(self.name)
        self.setTag('doId', str(self.doId))
        self.collisionNode.setName('goon')
        cs = CollisionSphere(0, 0, 4, 4)
        self.collisionNode.addSolid(cs)
        self.collisionNode.setIntoCollideMask(ToontownGlobals.PieBitmask | ToontownGlobals.CashbotBossObjectBitmask)
        self.wiggleTaskName = self.uniqueName('wiggleTask')
        self.wiggleFreeName = self.uniqueName('wiggleFree')
        self.boss.goons.append(self)
        self.reparentTo(render)

    def disable(self):
        i = self.boss.goons.index(self)
        del self.boss.goons[i]
        DistributedGoon.DistributedGoon.disable(self)
        DistributedCashbotBossObject.DistributedCashbotBossObject.disable(self)

    def delete(self):
        DistributedGoon.DistributedGoon.delete(self)
        DistributedCashbotBossObject.DistributedCashbotBossObject.delete(self)

    def hideShadows(self):
        self.dropShadow.hide()

    def showShadows(self):
        self.dropShadow.show()

    def getMinImpact(self):
        return ToontownGlobals.CashbotBossGoonImpact

    def doHitBoss(self, impact):
        self.d_hitBoss(impact)
        self.b_destroyGoon()

    def __startWalk(self):
        self.__stopWalk()
        if self.target:
            now = globalClock.getFrameTime()
            availableTime = self.arrivalTime - now
            if availableTime > 0:
                origH = self.getH()
                h = PythonUtil.fitDestAngle2Src(origH, self.targetH)
                delta = abs(h - origH)
                turnTime = delta / (self.velocity * 5)
                dist = Vec3(self.target - self.getPos()).length()
                walkTime = dist / self.velocity
                denom = turnTime + walkTime
                if denom != 0:
                    timeCompress = availableTime / denom
                    self.walkTrack = Sequence(self.hprInterval(turnTime * timeCompress, VBase3(h, 0, 0)), self.posInterval(walkTime * timeCompress, self.target))
                    self.walkTrack.start()
            else:
                self.setPos(self.target)
                self.setH(self.targetH)

    def __stopWalk(self):
        if self.walkTrack:
            self.walkTrack.pause()
            self.walkTrack = None
        return

    def __wiggleTask(self, task):
        elapsed = globalClock.getFrameTime() - self.wiggleStart
        h = math.sin(elapsed * 17) * 5
        p = math.sin(elapsed * 29) * 10
        self.crane.wiggleMagnet.setHpr(h, p, 0)
        return Task.cont

    def __wiggleFree(self, task):
        self.crane.releaseObject()
        self.stashCollisions()
        return Task.done

    def fellOut(self):
        self.b_destroyGoon()

    def handleToonDetect(self, collEntry = None):
        if self.boss.localToonIsSafe:
            return
        DistributedGoon.DistributedGoon.handleToonDetect(self, collEntry)

    def prepareGrab(self):
        DistributedCashbotBossObject.DistributedCashbotBossObject.prepareGrab(self)
        if self.isStunned or self.boss.localToonIsSafe:
            self.pose('collapse', 48)
            self.grabPos = (0, 0, self.stunGrabZ * self.scale)
        else:
            self.setPlayRate(4, 'walk')
            self.loop('walk')
            self.grabPos = (0, 0, self.walkGrabZ * self.scale)
            self.wiggleStart = globalClock.getFrameTime()
            taskMgr.add(self.__wiggleTask, self.wiggleTaskName)
            base.sfxPlayer.playSfx(self.wiggleSfx, node=self)
            if self.avId == localAvatar.doId:
                taskMgr.doMethodLater(self.wiggleFreeTime, self.__wiggleFree, self.wiggleFreeName)
        self.radar.hide()

    def prepareRelease(self):
        DistributedCashbotBossObject.DistributedCashbotBossObject.prepareRelease(self)
        self.crane.wiggleMagnet.setHpr(0, 0, 0)
        taskMgr.remove(self.wiggleTaskName)
        taskMgr.remove(self.wiggleFreeName)
        self.setPlayRate(self.animMultiplier, 'walk')

    def setObjectState(self, state, avId, craneId):
        if state == 'W':
            self.demand('Walk')
        elif state == 'B':
            if self.state != 'Battle':
                self.demand('Battle')
        elif state == 'S':
            if self.state != 'Stunned':
                self.demand('Stunned')
        elif state == 'R':
            if self.state != 'Recovery':
                self.demand('Recovery')
        elif state == 'a':
            self.demand('EmergeA')
        elif state == 'b':
            self.demand('EmergeB')
        else:
            DistributedCashbotBossObject.DistributedCashbotBossObject.setObjectState(self, state, avId, craneId)

    def setTarget(self, x, y, h, arrivalTime):
        self.target = Point3(x, y, 0)
        self.targetH = h
        now = globalClock.getFrameTime()
        self.arrivalTime = globalClockDelta.networkToLocalTime(arrivalTime, now)
        if self.state == 'Walk':
            self.__startWalk()

    def d_destroyGoon(self):
        self.sendUpdate('destroyGoon')

    def b_destroyGoon(self):
        if not self.isDead:
            self.d_destroyGoon()
            self.destroyGoon()

    def destroyGoon(self):
        if not self.isDead:
            self.playCrushMovie(None, None)
        self.demand('Off')
        return

    def enterOff(self):
        DistributedGoon.DistributedGoon.enterOff(self)
        DistributedCashbotBossObject.DistributedCashbotBossObject.enterOff(self)

    def exitOff(self):
        DistributedCashbotBossObject.DistributedCashbotBossObject.exitOff(self)
        DistributedGoon.DistributedGoon.exitOff(self)

    def enterWalk(self, avId = None, ts = 0):
        self.startToonDetect()
        self.isStunned = 0
        self.__startWalk()
        self.loop('walk', 0)
        self.unstashCollisions()

    def exitWalk(self):
        self.__stopWalk()
        self.stopToonDetect()
        self.stop()

    def enterEmergeA(self):
        self.undead()
        self.reparentTo(render)
        self.stopToonDetect()
        self.boss.doorA.request('open')
        self.radar.hide()
        self.__startWalk()
        self.loop('walk', 0)

    def exitEmergeA(self):
        if self.boss.doorA:
            self.boss.doorA.request('close')
        self.radar.show()
        self.__stopWalk()

    def enterEmergeB(self):
        self.undead()
        self.reparentTo(render)
        self.stopToonDetect()
        self.boss.doorB.request('open')
        self.radar.hide()
        self.__startWalk()
        self.loop('walk', 0)

    def exitEmergeB(self):
        if self.boss.doorB:
            self.boss.doorB.request('close')
        self.radar.show()
        self.__stopWalk()

    def enterBattle(self, avId = None, ts = 0):
        DistributedGoon.DistributedGoon.enterBattle(self, avId, ts)
        avatar = base.cr.doId2do.get(avId)
        if avatar:
            messenger.send('exitCrane')
            avatar.stunToon()
        self.unstashCollisions()

    def enterStunned(self, ts = 0):
        DistributedGoon.DistributedGoon.enterStunned(self, ts)
        self.unstashCollisions()

    def enterRecovery(self, ts = 0, pauseTime = 0):
        DistributedGoon.DistributedGoon.enterRecovery(self, ts, pauseTime)
        self.unstashCollisions()
