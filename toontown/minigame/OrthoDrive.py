from direct.interval.IntervalGlobal import *
from direct.task.Task import Task
from otp.otpbase import OTPGlobals
from toontown.toonbase.ToonBaseGlobal import *
from . import ArrowKeys

class OrthoDrive:
    notify = DirectNotifyGlobal.directNotify.newCategory('OrthoDrive')
    TASK_NAME = 'OrthoDriveTask'
    SET_ATREST_HEADING_TASK = 'setAtRestHeadingTask'

    def __init__(self, speed, maxFrameMove = None, customCollisionCallback = None, priority = 0, setHeading = 1, upHeading = 0, instantTurn = False, wantSound = False):
        self.wantSound = wantSound
        self.speed = speed
        self.maxFrameMove = maxFrameMove
        self.customCollisionCallback = customCollisionCallback
        self.priority = priority
        self.setHeading = setHeading
        self.upHeading = upHeading
        self.arrowKeys = ArrowKeys.ArrowKeys()
        self.lt = base.localAvatar
        self.instantTurn = instantTurn

    def destroy(self):
        self.arrowKeys.destroy()
        del self.arrowKeys
        del self.customCollisionCallback

    def start(self):
        self.notify.debug('start')
        self.__placeToonHOG(self.lt.getPos())
        taskMgr.add(self.__update, OrthoDrive.TASK_NAME, priority=self.priority)
        self.lastAction = None
        return

    def __placeToonHOG(self, pos, h = None):
        if h == None:
            h = self.lt.getH()
        self.lt.setPos(pos)
        self.lt.setH(h)
        self.lastPos = pos
        self.atRestHeading = h
        self.lastXVel = 0
        self.lastYVel = 0
        return

    def stop(self):
        self.notify.debug('stop')
        self.lt.stopSound()
        taskMgr.remove(OrthoDrive.TASK_NAME)
        taskMgr.remove(OrthoDrive.SET_ATREST_HEADING_TASK)
        if hasattr(self, 'turnLocalToonIval'):
            if self.turnLocalToonIval.isPlaying():
                self.turnLocalToonIval.pause()
            del self.turnLocalToonIval
        base.localAvatar.setSpeed(0, 0)

    def __update(self, task):
        vel = Vec3(0, 0, 0)
        xVel = 0
        yVel = 0
        if self.arrowKeys.upPressed():
            yVel += 1
        if self.arrowKeys.downPressed():
            yVel -= 1
        if self.arrowKeys.leftPressed():
            xVel -= 1
        if self.arrowKeys.rightPressed():
            xVel += 1
        vel.setX(xVel)
        vel.setY(yVel)
        vel.normalize()
        vel *= self.speed
        speed = vel.length()
        action = self.lt.setSpeed(speed, 0)
        if action != self.lastAction:
            self.lastAction = action
            if self.wantSound:
                if action == OTPGlobals.WALK_INDEX or action == OTPGlobals.REVERSE_INDEX:
                    self.lt.walkSound()
                elif action == OTPGlobals.RUN_INDEX:
                    self.lt.runSound()
                else:
                    self.lt.stopSound()
        if self.setHeading:
            self.__handleHeading(xVel, yVel)
        toonPos = self.lt.getPos()
        dt = globalClock.getDt()
        posOffset = vel * dt
        posOffset += toonPos - self.lastPos
        toonPos = self.lastPos
        if self.maxFrameMove:
            posOffsetLen = posOffset.length()
            if posOffsetLen > self.maxFrameMove:
                posOffset *= self.maxFrameMove
                posOffset /= posOffsetLen
        if self.customCollisionCallback:
            toonPos = self.customCollisionCallback(toonPos, toonPos + posOffset)
        else:
            toonPos = toonPos + posOffset
        self.lt.setPos(toonPos)
        self.lastPos = toonPos
        return Task.cont

    def __handleHeading(self, xVel, yVel):
        def getHeading(xVel, yVel):
            angTab = [[None, 0, 180], [-90, -45, -135], [90, 45, 135]]
            return angTab[xVel][yVel] + self.upHeading

        def orientToon(angle, self = self):
            startAngle = self.lt.getH()
            startAngle = fitSrcAngle2Dest(startAngle, angle)
            dur = 0.1 * abs(startAngle - angle) / 90
            self.turnLocalToonIval = LerpHprInterval(self.lt, dur, Point3(angle, 0, 0), startHpr=Point3(startAngle, 0, 0), name='OrthoDriveLerpHpr')
            if self.instantTurn:
                self.turnLocalToonIval.finish()
            else:
                self.turnLocalToonIval.start()

        if xVel != self.lastXVel or yVel != self.lastYVel:
            taskMgr.remove(OrthoDrive.SET_ATREST_HEADING_TASK)
            if not (xVel or yVel):
                orientToon(self.atRestHeading)
            else:
                curHeading = getHeading(xVel, yVel)
                if ((self.lastXVel and self.lastYVel) and not (xVel and yVel)):
                    def setAtRestHeading(task, self = self, angle = curHeading):
                        self.atRestHeading = angle
                        return Task.done

                    taskMgr.doMethodLater(0.05, setAtRestHeading, OrthoDrive.SET_ATREST_HEADING_TASK)
                else:
                    self.atRestHeading = curHeading
                orientToon(curHeading)
        self.lastXVel = xVel
        self.lastYVel = yVel
