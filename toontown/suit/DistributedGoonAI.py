from otp.ai.AIBaseGlobal import *
from .GoonGlobals import *
from direct.directnotify import DirectNotifyGlobal
from toontown.battle import SuitBattleGlobals
from toontown.coghq import DistributedCrushableEntityAI
from . import GoonPathData
from direct.distributed import ClockDelta
import random
from direct.task import Task

class DistributedGoonAI(DistributedCrushableEntityAI.DistributedCrushableEntityAI):
    UPDATE_TIMESTAMP_INTERVAL = 180.0
    STUN_TIME = 4
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedGoonAI')

    def __init__(self, level, entId):
        self.hFov = 70
        self.attackRadius = 15
        self.strength = 15
        self.velocity = 4
        self.scale = 1.0
        DistributedCrushableEntityAI.DistributedCrushableEntityAI.__init__(self, level, entId)
        self.curInd = 0
        self.dir = GOON_FORWARD
        self.parameterized = 0
        self.width = 1
        self.crushed = 0
        self.pathStartTime = None
        self.walkTrackTime = 0.0
        self.totalPathTime = 1.0
        return

    def delete(self):
        taskMgr.remove(self.taskName('sync'))
        taskMgr.remove(self.taskName('resumeWalk'))
        taskMgr.remove(self.taskName('recovery'))
        taskMgr.remove(self.taskName('deleteGoon'))
        taskMgr.remove(self.taskName('GoonBombCheck'))
        DistributedCrushableEntityAI.DistributedCrushableEntityAI.delete(self)

    def generate(self):
        self.notify.debug('generate')
        DistributedCrushableEntityAI.DistributedCrushableEntityAI.generate(self)
        if self.level:
            self.level.setEntityCreateCallback(self.parentEntId, self.startGoon)

    def startGoon(self):
        ts = 100 * random.random()
        self.sendMovie(GOON_MOVIE_WALK, pauseTime=ts)

    def requestBattle(self, pauseTime):
        avId = self.air.getAvatarIdFromSender()
        self.notify.debug('requestBattle, avId = %s' % avId)
        self.sendMovie(GOON_MOVIE_BATTLE, avId, pauseTime)
        taskMgr.remove(self.taskName('resumeWalk'))
        taskMgr.doMethodLater(5, self.sendMovie, self.taskName('resumeWalk'), extraArgs=(GOON_MOVIE_WALK, avId, pauseTime))

    def requestStunned(self, pauseTime):
        avId = self.air.getAvatarIdFromSender()
        self.notify.debug('requestStunned(%s)' % avId)
        if self.level:
            if not hasattr(self.level, 'goonStunRequests'):
                self.level.goonStunRequests = {}
            if taskMgr.hasTaskNamed(self.taskName('GoonBombCheck')):
                if avId in self.level.goonStunRequests:
                    self.level.goonStunRequests[avId] = self.level.goonStunRequests[avId] + 1
                else:
                    self.level.goonStunRequests[avId] = 1
            else:
                self.level.goonStunRequests[avId] = 1
                taskMgr.doMethodLater(0.1, self.accumulateGoonMessages, self.taskName('GoonBombCheck'))
        self.sendMovie(GOON_MOVIE_STUNNED, avId, pauseTime)
        taskMgr.remove(self.taskName('recovery'))
        taskMgr.doMethodLater(self.STUN_TIME, self.sendMovie, self.taskName('recovery'), extraArgs=(GOON_MOVIE_RECOVERY, avId, pauseTime))

    def accumulateGoonMessages(self, task):
        if not hasattr(self.level, 'goonStunRequests'):
            return
        for toonId in self.level.goonStunRequests:
            if self.level.goonStunRequests[toonId] > 2:
                self.air.writeServerEvent('suspicious', toonId, 'Stunned multiple goons very close together. Possible multihack.')

        self.level.goonStunRequests.clear()
        del self.level.goonStunRequests

    def requestResync(self, task=None):
        self.notify.debug('resyncGoon')
        self.sendMovie(GOON_MOVIE_SYNC)
        self.updateGrid()

    def sendMovie(self, type, avId=0, pauseTime=0):
        if type == GOON_MOVIE_WALK:
            self.pathStartTime = globalClock.getFrameTime()
            if self.parameterized:
                self.walkTrackTime = pauseTime % self.totalPathTime
            else:
                self.walkTrackTime = pauseTime
            self.notify.debug('GOON_MOVIE_WALK doId = %s, pathStartTime = %s, walkTrackTime = %s' % (self.doId, self.pathStartTime, self.walkTrackTime))
        if type == GOON_MOVIE_WALK or type == GOON_MOVIE_SYNC:
            curT = globalClock.getFrameTime()
            elapsedT = curT - self.pathStartTime
            pathT = self.walkTrackTime + elapsedT
            if self.parameterized:
                pathT = pathT % self.totalPathTime
            self.sendUpdate('setMovie', [type, avId, pathT, ClockDelta.globalClockDelta.localToNetworkTime(curT)])
            taskMgr.remove(self.taskName('sync'))
            taskMgr.doMethodLater(self.UPDATE_TIMESTAMP_INTERVAL, self.requestResync, self.taskName('sync'), extraArgs=None)
        else:
            self.sendUpdate('setMovie', [type, avId, pauseTime, ClockDelta.globalClockDelta.getFrameNetworkTime()])
        return

    def updateGrid(self):
        if not self.parameterized:
            return
        if self.grid and hasattr(self, 'entId'):
            self.grid.removeObject(self.entId)
            if not self.crushed:
                curT = globalClock.getFrameTime()
                if self.pathStartTime:
                    elapsedT = curT - self.pathStartTime
                else:
                    elapsedT = 0
                pathT = (self.walkTrackTime + elapsedT) % self.totalPathTime
                pt = self.getPathPoint(pathT)
                if not self.grid.addObjectByPos(self.entId, pt):
                    self.notify.warning("updateGrid: couldn't put goon in grid")

    def doCrush(self, crusherId, axis):
        self.notify.debug('doCrush %s' % self.doId)
        DistributedCrushableEntityAI.DistributedCrushableEntityAI.doCrush(self, crusherId, axis)
        self.crushed = 1
        self.grid.removeObject(self.entId)
        taskMgr.doMethodLater(5.0, self.doDelete, self.taskName('deleteGoon'))

    def doDelete(self, task):
        self.requestDelete()
        return Task.done

    def setParameterize(self, x, y, z, pathIndex):
        if not hasattr(self, 'level') or not self.level:
            return
        pathId = GoonPathData.taskZoneId2pathId[self.level.getTaskZoneId()]
        pathData = GoonPathData.Paths[pathId]
        self.pathOrigin = Vec3(x, y, z)
        if pathIndex > len(pathData):
            self.notify.warning('Invalid path index given, using 0')
            pathIndex = 0
        pathPts = pathData[pathIndex] + [pathData[pathIndex][0]]
        invVel = 1.0 / self.velocity
        t = 0
        self.tSeg = [t]
        self.pathSeg = []
        for i in range(len(pathPts) - 1):
            ptA = pathPts[i]
            ptB = pathPts[i + 1]
            t += T_TURN
            self.tSeg.append(t)
            self.pathSeg.append([Vec3(0, 0, 0), 0, ptA])
            seg = Vec3(ptB - ptA)
            segLength = seg.length()
            t += invVel * segLength
            self.tSeg.append(t)
            self.pathSeg.append([seg, segLength, ptA])

        self.totalPathTime = t
        self.pathPts = pathPts
        self.parameterized = 1

    def getPathPoint(self, t):
        for i in range(len(self.tSeg) - 1):
            if t >= self.tSeg[i] and t < self.tSeg[i + 1]:
                tSeg = t - self.tSeg[i]
                t = tSeg / (self.tSeg[i + 1] - self.tSeg[i])
                seg = self.pathSeg[i][0]
                ptA = self.pathSeg[i][2]
                pt = ptA + seg * t
                return self.pathOrigin + pt

        self.notify.warning("Couldn't find valid path point")
        return Vec3(0, 0, 0)

    def b_setVelocity(self, velocity):
        self.setVelocity(velocity)
        self.d_setVelocity(velocity)

    def setVelocity(self, velocity):
        self.velocity = velocity

    def d_setVelocity(self, velocity):
        self.sendUpdate('setVelocity', [velocity])

    def getVelocity(self):
        return self.velocity

    def b_setHFov(self, hFov):
        self.setHFov(hFov)
        self.d_setHFov(hFov)

    def setHFov(self, hFov):
        self.hFov = hFov

    def d_setHFov(self, hFov):
        self.sendUpdate('setHFov', [hFov])

    def getHFov(self):
        return self.hFov

    def b_setAttackRadius(self, attackRadius):
        self.setAttackRadius(attackRadius)
        self.d_setAttackRadius(attackRadius)

    def setAttackRadius(self, attackRadius):
        self.attackRadius = attackRadius

    def d_setAttackRadius(self, attackRadius):
        self.sendUpdate('setAttackRadius', [attackRadius])

    def getAttackRadius(self):
        return self.attackRadius

    def b_setStrength(self, strength):
        self.setStrength(strength)
        self.d_setStrength(strength)

    def setStrength(self, strength):
        self.strength = strength

    def d_setStrength(self, strength):
        self.sendUpdate('setStrength', [strength])

    def getStrength(self):
        return self.strength

    def b_setGoonScale(self, scale):
        self.setGoonScale(scale)
        self.d_setGoonScale(scale)

    def setGoonScale(self, scale):
        self.scale = scale

    def d_setGoonScale(self, scale):
        self.sendUpdate('setGoonScale', [scale])

    def getGoonScale(self):
        return self.scale

    def b_setupGoon(self, velocity, hFov, attackRadius, strength, scale):
        self.setupGoon(velocity, hFov, attackRadius, strength, scale)
        self.d_setupGoon(velocity, hFov, attackRadius, strength, scale)

    def setupGoon(self, velocity, hFov, attackRadius, strength, scale):
        self.setVelocity(velocity)
        self.setHFov(hFov)
        self.setAttackRadius(attackRadius)
        self.setStrength(strength)
        self.setGoonScale(scale)

    def d_setupGoon(self, velocity, hFov, attackRadius, strength, scale):
        self.sendUpdate('setupGoon', [velocity, hFov, attackRadius, strength, scale])
