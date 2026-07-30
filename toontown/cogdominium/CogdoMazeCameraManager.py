from direct.showbase.PythonUtil import bound as clamp
from . import CogdoMazeGameGlobals as Globals
import math
import random

class CogdoMazeCameraManager:
    toonJumpSpeed = 30.0
    toonJumpDir = 1.0
    toonMaxHeight = 1.8
    maxHeightOffset = 1.5
    savedShakeStrength = 0.0
    toonIsShaking = False
    rumbleOffDuration = 2.0
    rumbleOnDuration = 1.5
    rumbleOffTimer = 0.0
    rumbleOnTimer = -1
    savedCamZ = 0.0
    savedCamX = 0.0
    shakeStrengthThreshold = 2.8
    savedRumbleTimer = 0.0
    rumbleFreq = 0.1
    rumbleSmall = 0.05
    rumbleBig = 0.16
    rumbleMagnitude = rumbleSmall

    def __init__(self, toon, maze, cam, root):
        self.toon = toon
        self.maze = maze
        self.camera = cam
        self.root = root
        self.shakeStrength = 0.0
        self.shakeOffset = 0.0
        self.shakeTime = 0.0
        self.defaultHeight = 0.0
        self.minPos = self.maze.tile2world(3, 5)
        self.maxPos = self.maze.tile2world(self.maze.width - 3, self.maze.height - 3)
        self._camAngle = Globals.CameraAngle
        self._camDistance = Globals.CameraMinDistance
        self._camTargetDistance = self._camDistance

    def enable(self):
        self.parent = self.root.attachNewNode('GameCamParent')
        self.parent.setPos(self.toon, 0, 0, 0)
        self.parent.setHpr(self.root, 180, self._camAngle, 0)
        self.camera.reparentTo(self.parent)
        self.camera.setPos(0, self._camDistance, 0)
        self.camera.lookAt(self.toon)
        self.defaultHeight = self.parent.getZ()
        self.update(0)

    def setCameraTargetDistance(self, distance):
        self._camTargetDistance = distance

    def disable(self):
        self.camera.wrtReparentTo(render)
        self.parent.removeNode()
        del self.parent

    def update(self, dt):
        toonPos = self.toon.getPos()
        self.parent.setPos(self.toon.getParent(), clamp(toonPos.getX(), self.minPos[0], self.maxPos[0]), clamp(toonPos.getY(), self.minPos[1], self.maxPos[1]), 0)
        if self._camDistance != self._camTargetDistance:
            self._updateCameraDistance()
        if self.shakeOffset > 0 or self.shakeStrength > 0:
            self.updateShake(dt)
        self.updateRumble(dt)

    def _updateCameraDistance(self):
        if self._camDistance < self._camTargetDistance:
            self._camDistance += min(0.4 * (self._camDistance / self._camTargetDistance), self._camTargetDistance - self._camDistance)
        elif self._camDistance > self._camTargetDistance:
            self._camDistance += max(-0.4 * (self._camDistance / self._camTargetDistance), self._camTargetDistance - self._camDistance)
        self.camera.setY(self._camDistance)

    def updateShake(self, dt):
        if self.shakeStrength > 0:
            if self.shakeStrength > Globals.CameraShakeMax:
                self.shakeStrength = Globals.CameraShakeMax
            height = self.defaultHeight + self.shakeStrength
            self.shakeStrength = self.shakeStrength - Globals.CameraShakeFalloff * dt
            if self.shakeStrength < 0.0:
                self.shakeStrength = 0.0
        else:
            height = self.shakeStrength

    def shake(self, strength):
        self.shakeStrength += strength * 1.5
        self.toonIsShaking = True

    def updateToonShake(self, dt):
        if self.toonIsShaking:
            newHeight = self.toon.getZ() + self.toonJumpDir * dt * self.savedShakeStrength * self.toonJumpSpeed
            maxHeight = self.savedShakeStrength * self.maxHeightOffset
            if maxHeight > self.toonMaxHeight:
                maxHeight = self.toonMaxHeight
            if newHeight >= maxHeight:
                newHeight = maxHeight
                self.toonJumpDir = -1.0
            elif newHeight <= 0.0:
                newHeight = 0.0
                self.toonJumpDir = 1.0
                self.toonIsShaking = False
            self.toon.setZ(newHeight)

    def updateRumble(self, dt):
        if self.rumbleOnTimer == -1:
            self.rumbleOffTimer += dt
            if self.rumbleOffTimer > self.rumbleOffDuration:
                self.rumbleOnTimer = 0.0
                self.savedRumbleTimer = 0.0
                self.rumbleOffTimer = -1
                self.rumbleOnDuration = 1.5
                self.savedCamZ = self.camera.getZ()
                self.savedCamX = self.camera.getX()
        else:
            if self.rumbleOnTimer > self.savedRumbleTimer + self.rumbleFreq:
                self.savedRumbleTimer += self.rumbleFreq
                self.rumble(self.rumbleMagnitude)
            self.rumbleOnTimer += dt
            if self.rumbleOnTimer > self.rumbleOnDuration:
                self.rumbleOffTimer = 0.0
                self.rumbleOnTimer = -1
                if self.shakeStrength > self.shakeStrengthThreshold:
                    self.rumbleOffDuration = 0.5
                    self.rumbleMagnitude = self.rumbleBig
                else:
                    self.rumbleOffDuration = random.uniform(1.0, 3.0)
                    self.rumbleMagnitude = self.rumbleSmall

    def rumble(self, magnitude):
        self.rumbleMagnitude *= -1.0
        dz = self.rumbleMagnitude
        self.camera.setZ(self.savedCamZ + dz)
        dx = dz
        self.camera.setZ(self.savedCamX + dx)
