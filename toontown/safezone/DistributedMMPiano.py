from pandac.PandaModules import *
from direct.task.Task import Task
from direct.distributed.ClockDelta import *
from direct.interval.IntervalGlobal import *
from direct.distributed import DistributedObject
from pandac.PandaModules import NodePath
from toontown.toonbase import ToontownGlobals
ChangeDirectionDebounce = 1.0
ChangeDirectionTime = 1.0

class DistributedMMPiano(DistributedObject.DistributedObject):

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        self.spinStartTime = 0.0
        self.rpm = 0.0
        self.degreesPerSecond = self.rpm / 60.0 * 360.0
        self.offset = 0.0
        self.oldOffset = 0.0
        self.lerpStart = 0.0
        self.lerpFinish = 1.0
        self.speedUpSound = None
        self.changeDirectionSound = None
        self.lastChangeDirection = 0.0
        return

    def generate(self):
        self.piano = base.cr.playGame.hood.loader.piano
        base.cr.parentMgr.registerParent(ToontownGlobals.SPMinniesPiano, self.piano)
        self.accept('enterlarge_round_keyboard_collisions', self.__handleOnFloor)
        self.accept('exitlarge_round_keyboard_collisions', self.__handleOffFloor)
        self.accept('entero7', self.__handleChangeDirectionButton)
        self.speedUpSound = base.loadSfx('phase_6/audio/sfx/SZ_MM_gliss.mp3')
        self.changeDirectionSound = base.loadSfx('phase_6/audio/sfx/SZ_MM_cymbal.mp3')
        self.__setupSpin()
        DistributedObject.DistributedObject.generate(self)

    def __setupSpin(self):
        taskMgr.add(self.__updateSpin, self.taskName('pianoSpinTask'))

    def __stopSpin(self):
        taskMgr.remove(self.taskName('pianoSpinTask'))

    def __updateSpin(self, task):
        now = globalClock.getFrameTime()
        if now > self.lerpFinish:
            offset = self.offset
        elif now > self.lerpStart:
            t = (now - self.lerpStart) / (self.lerpFinish - self.lerpStart)
            offset = self.oldOffset + t * (self.offset - self.oldOffset)
        else:
            offset = self.oldOffset
        heading = self.degreesPerSecond * (now - self.spinStartTime) + offset
        self.piano.setHprScale(heading % 360.0, 0.0, 0.0, 1.0, 1.0, 1.0)
        return Task.cont

    def disable(self):
        del self.piano
        base.cr.parentMgr.unregisterParent(ToontownGlobals.SPMinniesPiano)
        self.ignore('enterlarge_round_keyboard_collisions')
        self.ignore('exitlarge_round_keyboard_collisions')
        self.ignore('entero7')
        self.ignore('entericon_center_collisions')
        self.speedUpSound = None
        self.changeDirectionSound = None
        self.__stopSpin()
        DistributedObject.DistributedObject.disable(self)
        return

    def setSpeed(self, rpm, offset, timestamp):
        timestamp = globalClockDelta.networkToLocalTime(timestamp)
        degreesPerSecond = rpm / 60.0 * 360.0
        now = globalClock.getFrameTime()
        oldHeading = self.degreesPerSecond * (now - self.spinStartTime) + self.offset
        oldHeading = oldHeading % 360.0
        oldOffset = oldHeading - degreesPerSecond * (now - timestamp)
        self.rpm = rpm
        self.degreesPerSecond = degreesPerSecond
        self.offset = offset
        self.spinStartTime = timestamp
        while oldOffset - offset < -180.0:
            oldOffset += 360.0

        while oldOffset - offset > 180.0:
            oldOffset -= 360.0

        self.oldOffset = oldOffset
        self.lerpStart = now
        self.lerpFinish = timestamp + ChangeDirectionTime

    def playSpeedUp(self, avId):
        if avId != base.localAvatar.doId:
            base.playSfx(self.speedUpSound)

    def playChangeDirection(self, avId):
        if avId != base.localAvatar.doId:
            base.playSfx(self.changeDirectionSound)

    def __handleOnFloor(self, collEntry):
        self.cr.playGame.getPlace().activityFsm.request('OnPiano')
        self.sendUpdate('requestSpeedUp', [])
        base.playSfx(self.speedUpSound)

    def __handleOffFloor(self, collEntry):
        self.cr.playGame.getPlace().activityFsm.request('off')

    def __handleSpeedUpButton(self, collEntry):
        self.sendUpdate('requestSpeedUp', [])
        base.playSfx(self.speedUpSound)

    def __handleChangeDirectionButton(self, collEntry):
        now = globalClock.getFrameTime()
        if now - self.lastChangeDirection < ChangeDirectionDebounce:
            return
        self.lastChangeDirection = now
        self.sendUpdate('requestChangeDirection', [])
        base.playSfx(self.changeDirectionSound)
