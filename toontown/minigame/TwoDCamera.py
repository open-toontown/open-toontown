from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *
from direct.task.Task import Task
from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObject
from toontown.minigame import ToonBlitzGlobals
import math

class TwoDCamera(DistributedObject.DistributedObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('TwoDCamera')

    def __init__(self, camera):
        self.notify.debug('Constructing TwoDCamera with %s' % camera)
        self.camera = camera
        self.cameraSideView = ToonBlitzGlobals.CameraStartingPosition
        self.threeQuarterOffset = 2
        self.changeFacingInterval = None
        self.ivalControllingCamera = False
        self.accept('avatarOrientationChanged', self.setupChangeFacingInterval)
        return

    def onstage(self):
        self.camera.reparentTo(render)
        p = self.cameraSideView
        self.camera.setPosHpr(render, p[0], p[1], p[2], p[3], p[4], p[5])
        self.camera.setX(render, base.localAvatar.getX(render) + self.threeQuarterOffset)

    def destroy(self):
        self.ignore('avatarOrientationChanged')
        p = self.cameraSideView
        self.camera.setPosHpr(render, p[0], p[1], p[2], p[3], p[4], p[5])

    def update(self):
        if not self.ivalControllingCamera:
            camX = base.localAvatar.getX(render) - math.sin(base.localAvatar.getH(render) * math.pi / 180) * self.threeQuarterOffset
            self.camera.setX(render, camX)

    def clearChangeFacingInterval(self):
        if self.changeFacingInterval:
            self.changeFacingInterval.pause()
            del self.changeFacingInterval
        self.changeFacingInterval = None
        return

    def setupChangeFacingInterval(self, newHeading):
        self.clearChangeFacingInterval()
        self.newHeading = newHeading
        self.changeFacingInterval = LerpFunc(self.myLerpPos, duration=5.0)
        self.changeFacingInterval.start()

    def myLerpPos(self, t):
        self.ivalControllingCamera = True
        finalCamX = base.localAvatar.getX(render) - math.sin(self.newHeading * math.pi / 180) * self.threeQuarterOffset
        diffX = finalCamX - self.camera.getX(render)
        self.camera.setX(render, self.camera.getX(render) + diffX * t)
        if math.fabs(self.camera.getX(render) - finalCamX) < 0.01:
            self.notify.debug('giving up camera control')
            self.camera.setX(render, finalCamX)
            self.ivalControllingCamera = False
            self.clearChangeFacingInterval()
