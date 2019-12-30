from toontown.toonbase.ToonBaseGlobal import *
from otp.otpbase import OTPGlobals
from direct.interval.IntervalGlobal import *
from . import ArrowKeys
from direct.task.Task import Task

class TwoDDrive:
    notify = DirectNotifyGlobal.directNotify.newCategory('TwoDDrive')
    TASK_NAME = 'TwoDDriveTask'
    SET_ATREST_HEADING_TASK = 'setAtRestHeadingTask'

    def __init__(self, game, speed, maxFrameMove = None, customCollisionCallback = None, priority = 0, setHeading = 1, upHeading = 0):
        self.game = game
        self.speed = speed
        self.maxFrameMove = maxFrameMove
        self.customCollisionCallback = customCollisionCallback
        self.priority = priority
        self.setHeading = setHeading
        self.upHeading = upHeading
        self.arrowKeys = ArrowKeys.ArrowKeys()
        self.wasUpReleased = True
        self.lt = base.localAvatar
        base.localAvatar.useTwoDControls()
        base.localAvatar.controlManager.currentControls.avatarControlJumpForce = 30.0
        self.ONE_JUMP_PER_UP_PRESSED = True
        self.lastAction = None
        self.isMovingX = False
        return

    def destroy(self):
        self.game = None
        base.localAvatar.controlManager.currentControls.avatarControlJumpForce = 24.0
        base.localAvatar.useWalkControls()
        self.arrowKeys.destroy()
        del self.arrowKeys
        del self.customCollisionCallback
        self.lastAction = None
        return

    def start(self):
        self.notify.debug('start')
        self.__placeToonHOG(self.lt.getPos())
        base.localAvatar.enableAvatarControls()
        taskMgr.remove(TwoDDrive.TASK_NAME)
        taskMgr.add(self.__update, TwoDDrive.TASK_NAME, priority=self.priority)

    def __placeToonHOG(self, pos, h = None):
        if h == None:
            h = self.lt.getH()
        self.lt.setPos(pos)
        self.lt.setH(h)
        self.lastPos = pos
        self.atRestHeading = h
        self.oldAtRestHeading = h
        self.lastXVel = 0
        self.lastYVel = 0
        return

    def stop(self):
        self.notify.debug('stop')
        base.localAvatar.disableAvatarControls()
        taskMgr.remove(TwoDDrive.TASK_NAME)
        taskMgr.remove(TwoDDrive.SET_ATREST_HEADING_TASK)
        if hasattr(self, 'turnLocalToonIval'):
            if self.turnLocalToonIval.isPlaying():
                self.turnLocalToonIval.pause()
            del self.turnLocalToonIval
        base.localAvatar.setSpeed(0, 0)
        base.localAvatar.stopSound()

    def __update(self, task):
        vel = Vec3(0, 0, 0)
        xVel = 0
        yVel = 0
        if self.ONE_JUMP_PER_UP_PRESSED:
            if not self.arrowKeys.upPressed():
                self.wasUpReleased = True
            elif self.arrowKeys.upPressed() and self.wasUpReleased:
                self.wasUpReleased = False
                if not self.game.isHeadInFloor:
                    if localAvatar.controlManager.currentControls == localAvatar.controlManager.get('twoD'):
                        base.localAvatar.controlManager.currentControls.jumpPressed()
        elif self.arrowKeys.upPressed():
            if not self.game.isHeadInFloor:
                if localAvatar.controlManager.currentControls == localAvatar.controlManager.get('twoD'):
                    base.localAvatar.controlManager.currentControls.jumpPressed()
        if self.arrowKeys.leftPressed():
            xVel -= 1
        if self.arrowKeys.rightPressed():
            xVel += 1
        vel.setX(xVel)
        vel.setY(yVel)
        vel.normalize()
        vel *= self.speed
        if abs(xVel) > 0:
            if not self.isMovingX:
                self.isMovingX = True
                messenger.send('avatarMovingX')
        elif self.isMovingX:
            self.isMovingX = False
            messenger.send('avatarStoppedX')
        speed = vel.length()
        action = self.lt.setSpeed(speed, 0)
        if action != self.lastAction:
            self.lastAction = action
            if action == OTPGlobals.RUN_INDEX:
                base.localAvatar.runSound()
            else:
                base.localAvatar.stopSound()
        if self.setHeading:
            self.__handleHeading(xVel, yVel)
        toonPos = self.lt.getPos()
        dt = globalClock.getDt()
        posOffset = vel * dt
        if self.customCollisionCallback:
            toonPos = self.customCollisionCallback(toonPos, toonPos + posOffset)
        else:
            toonPos += posOffset
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
            self.turnLocalToonIval = LerpHprInterval(self.lt, dur, Point3(angle, 0, 0), startHpr=Point3(startAngle, 0, 0), name='TwoDDriveLerpHpr')
            self.turnLocalToonIval.start()
            if self.atRestHeading != self.oldAtRestHeading:
                self.oldAtRestHeading = self.atRestHeading
                messenger.send('avatarOrientationChanged', [self.atRestHeading])

        if xVel != self.lastXVel or yVel != self.lastYVel:
            taskMgr.remove(TwoDDrive.SET_ATREST_HEADING_TASK)
            if not (xVel or yVel):
                orientToon(self.atRestHeading)
            else:
                curHeading = getHeading(xVel, yVel)
                if ((self.lastXVel and self.lastYVel) and not (xVel and yVel)):
                    def setAtRestHeading(task, self = self, angle = curHeading):
                        self.atRestHeading = angle
                        return Task.done

                    taskMgr.doMethodLater(0.05, setAtRestHeading, TwoDDrive.SET_ATREST_HEADING_TASK)
                else:
                    self.atRestHeading = curHeading
                orientToon(curHeading)
        self.lastXVel = xVel
        self.lastYVel = yVel
