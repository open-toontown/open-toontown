import math
from pandac.PandaModules import NodePath, Point3
from . import PartyGlobals
inverse_e = 1.0 / math.e

def getCogDistanceUnitsFromCenter(distance):
    return int(round(distance * (PartyGlobals.CogActivityArenaLength / 2.0)))


class CameraManager:
    nextID = 0

    def __init__(self, cameraNP):
        self.cameraNP = cameraNP
        self.id = CameraManager.nextID
        CameraManager.nextID += 1
        self.otherNP = render
        self.lookAtNP = NodePath('CameraManager%d.lookAtNP' % self.id)
        self.lookAtEnabled = False
        self.targetPos = Point3(0.0, 0.0, 0.0)
        self.targetLookAtPos = Point3(0.0, 1.0, 0.0)
        self.enabled = False
        self.rate = 10.0

    def destroy(self):
        if self.enabled:
            self.setEnabled(False)
        self.lookAtNP.removeNode()
        del self.lookAtNP
        del self.targetPos
        del self.targetLookAtPos
        del self.otherNP

    def setEnabled(self, enabled):
        if enabled != self.enabled:
            if enabled:
                taskMgr.add(self.updateTask, 'CameraManager%d.update' % self.id)
            else:
                taskMgr.remove('CameraManager%d.update' % self.id)
            self.enabled = enabled

    def setTargetPos(self, p):
        self.targetPos = p

    def setPos(self, p):
        self.targetPos = p
        self.cameraNP.setPos(self.otherNP, p)

    def setTargetLookAtPos(self, p):
        self.lookAtEnabled = True
        self.targetLookAtPos = p

    def setLookAtPos(self, p):
        self.lookAtEnabled = True
        self.targetLookAtPos = p
        self.lookAtNP.setPos(p)

    def setHpr(self, hpr):
        self.lookAtEnabled = False
        self.cameraNP.setHpr(self.otherNP, hpr)

    def updateTask(self, task):
        newCameraPos = self.rateInterpolate(self.cameraNP.getPos(self.otherNP), self.targetPos)
        self.cameraNP.setPos(self.otherNP, newCameraPos)
        if self.lookAtEnabled:
            newLookAtPos = self.rateInterpolate(self.lookAtNP.getPos(self.otherNP), self.targetLookAtPos)
            self.lookAtNP.setPos(self.otherNP, newLookAtPos)
            self.cameraNP.lookAt(self.lookAtNP)
        return task.cont

    def rateInterpolate(self, currentPos, targetPos):
        dt = globalClock.getDt()
        vec = currentPos - targetPos
        return targetPos + vec * inverse_e ** (dt * self.rate)


class StrafingControl:

    def __init__(self, player):
        self.player = player
        self.defaultOffset = Point3(1.0, -7.5, self.player.toon.getHeight() + 1.0)

    def destroy(self):
        self.player = None
        del self.player
        self.defaultOffset = None
        del self.defaultOffset
        return

    def update(self):
        self.player.tempNP.setPos(self.player.locator, self.player.toon.getPos() + self.defaultOffset)
        self.player.cameraManager.setTargetPos(self.player.tempNP.getPos(render))
        self.player.tempNP.setPos(self.player.locator, self.player.toon.getPos() + self.defaultOffset + Point3(0, 20, 0))
        self.player.cameraManager.setTargetLookAtPos(self.player.tempNP.getPos(render))
        if not self.player._aimMode and self.player.input.throwPiePressed:
            self.toggleAim()
        if self.player._aimMode and not self.player.input.throwPiePressed and (self.player.input.upPressed or self.player.input.downPressed or self.player.input.leftPressed or self.player.input.rightPressed):
            self.toggleAim()
        if not self.player._aimMode:
            if not (self.player.input.upPressed or self.player.input.downPressed or self.player.input.leftPressed or self.player.input.rightPressed):
                self.player.faceForward()
            return
        if self.player.input.throwPiePressed:
            self.player.gui.updatePiePowerMeter(self.player.getPieThrowingPower(globalClock.getFrameTime()))

    def toggleAim(self):
        self.player._aimMode = not self.player._aimMode
        if not self.player._aimMode:
            self.player.orthoWalking = True
            self.player.orthoWalk.start()
            self.player._rotation = 0.0
            self.player._prevRotation = 0.0
            self.player.gui.hidePiePowerMeter()
            self.player.toon.setH(0.0)
        else:
            self.player.orthoWalk.stop()
            self.player.orthoWalking = False
            self.player.toon.setH(0.0)
            self.player.gui.showPiePowerMeter()

    def enable(self):
        self.player._aimMode = False
        camera.wrtReparentTo(self.player.locator)
        self.player.cameraManager.setEnabled(True)
        activityView = self.player.activity.view
        pos = activityView.teamCamPosLocators[self.player.team].getPos(render)
        aim = activityView.teamCamAimLocators[self.player.team].getPos(render)
        self.player.cameraManager.setPos(pos)
        self.player.cameraManager.setLookAtPos(aim)
        self.player.tempNP.reparentTo(self.player.locator)
        self.player.tempNP.setPos(self.player.locator, self.player.toon.getPos() + self.defaultOffset)
        self.player.cameraManager.setTargetPos(self.player.tempNP.getPos(render))
