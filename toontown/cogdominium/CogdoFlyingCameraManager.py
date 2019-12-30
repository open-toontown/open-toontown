import math
from pandac.PandaModules import NodePath, Vec3
from pandac.PandaModules import CollisionTraverser, CollisionHandlerQueue
from pandac.PandaModules import CollisionRay, CollisionNode
from math import pi, sin, cos
from direct.showbase.PythonUtil import bound as clamp
from otp.otpbase import OTPGlobals
from toontown.toonbase import ToontownGlobals
from . import CogdoFlyingGameGlobals as Globals
INVERSE_E = 1.0 / math.e

def smooth(old, new):
    return old * 0.7 + new * 0.3


class CogdoFlyingCameraManager:

    def __init__(self, cam, parent, player, level):
        self._toon = player.toon
        self._camera = cam
        self._parent = parent
        self._player = player
        self._level = level
        self._enabled = False

    def enable(self):
        if self._enabled:
            return
        self._toon.detachCamera()
        self._prevToonY = 0.0
        levelBounds = self._level.getBounds()
        l = Globals.Camera.LevelBoundsFactor
        self._bounds = ((levelBounds[0][0] * l[0], levelBounds[0][1] * l[0]), (levelBounds[1][0] * l[1], levelBounds[1][1] * l[1]), (levelBounds[2][0] * l[2], levelBounds[2][1] * l[2]))
        self._lookAtZ = self._toon.getHeight() + Globals.Camera.LookAtToonHeightOffset
        self._camParent = NodePath('CamParent')
        self._camParent.reparentTo(self._parent)
        self._camParent.setPos(self._toon, 0, 0, 0)
        self._camParent.setHpr(180, Globals.Camera.Angle, 0)
        self._camera.reparentTo(self._camParent)
        self._camera.setPos(0, Globals.Camera.Distance, 0)
        self._camera.lookAt(self._toon, 0, 0, self._lookAtZ)
        self._cameraLookAtNP = NodePath('CameraLookAt')
        self._cameraLookAtNP.reparentTo(self._camera.getParent())
        self._cameraLookAtNP.setPosHpr(self._camera.getPos(), self._camera.getHpr())
        self._levelBounds = self._level.getBounds()
        self._enabled = True
        self._frozen = False
        self._initCollisions()

    def _initCollisions(self):
        self._camCollRay = CollisionRay()
        camCollNode = CollisionNode('CameraToonRay')
        camCollNode.addSolid(self._camCollRay)
        camCollNode.setFromCollideMask(OTPGlobals.WallBitmask | OTPGlobals.CameraBitmask | ToontownGlobals.FloorEventBitmask | ToontownGlobals.CeilingBitmask)
        camCollNode.setIntoCollideMask(0)
        self._camCollNP = self._camera.attachNewNode(camCollNode)
        self._camCollNP.show()
        self._collOffset = Vec3(0, 0, 0.5)
        self._collHandler = CollisionHandlerQueue()
        self._collTrav = CollisionTraverser()
        self._collTrav.addCollider(self._camCollNP, self._collHandler)
        self._betweenCamAndToon = {}
        self._transNP = NodePath('trans')
        self._transNP.reparentTo(render)
        self._transNP.setTransparency(True)
        self._transNP.setAlphaScale(Globals.Camera.AlphaBetweenToon)
        self._transNP.setBin('fixed', 10000)

    def _destroyCollisions(self):
        self._collTrav.removeCollider(self._camCollNP)
        self._camCollNP.removeNode()
        del self._camCollNP
        del self._camCollRay
        del self._collHandler
        del self._collOffset
        del self._betweenCamAndToon
        self._transNP.removeNode()
        del self._transNP

    def freeze(self):
        self._frozen = True

    def unfreeze(self):
        self._frozen = False

    def disable(self):
        if not self._enabled:
            return
        self._destroyCollisions()
        self._camera.wrtReparentTo(render)
        self._cameraLookAtNP.removeNode()
        del self._cameraLookAtNP
        self._camParent.removeNode()
        del self._camParent
        del self._prevToonY
        del self._lookAtZ
        del self._bounds
        del self._frozen
        self._enabled = False

    def update(self, dt = 0.0):
        self._updateCam(dt)
        self._updateCollisions()

    def _updateCam(self, dt):
        toonPos = self._toon.getPos()
        camPos = self._camParent.getPos()
        x = camPos[0]
        z = camPos[2]
        toonWorldX = self._toon.getX(render)
        maxX = Globals.Camera.MaxSpinX
        toonWorldX = clamp(toonWorldX, -1.0 * maxX, maxX)
        spinAngle = Globals.Camera.MaxSpinAngle * toonWorldX * toonWorldX / (maxX * maxX)
        newH = 180.0 + spinAngle
        self._camParent.setH(newH)
        spinAngle = spinAngle * (pi / 180.0)
        distBehindToon = Globals.Camera.SpinRadius * cos(spinAngle)
        distToRightOfToon = Globals.Camera.SpinRadius * sin(spinAngle)
        d = self._camParent.getX() - clamp(toonPos[0], *self._bounds[0])
        if abs(d) > Globals.Camera.LeewayX:
            if d > Globals.Camera.LeewayX:
                x = toonPos[0] + Globals.Camera.LeewayX
            else:
                x = toonPos[0] - Globals.Camera.LeewayX
        x = self._toon.getX(render) + distToRightOfToon
        boundToonZ = min(toonPos[2], self._bounds[2][1])
        d = z - boundToonZ
        if d > Globals.Camera.MinLeewayZ:
            if self._player.velocity[2] >= 0 and toonPos[1] != self._prevToonY or self._player.velocity[2] > 0:
                z = boundToonZ + d * INVERSE_E ** (dt * Globals.Camera.CatchUpRateZ)
            elif d > Globals.Camera.MaxLeewayZ:
                z = boundToonZ + Globals.Camera.MaxLeewayZ
        elif d < -Globals.Camera.MinLeewayZ:
            z = boundToonZ - Globals.Camera.MinLeewayZ
        if self._frozen:
            y = camPos[1]
        else:
            y = self._toon.getY(render) - distBehindToon
        self._camParent.setPos(x, smooth(camPos[1], y), smooth(camPos[2], z))
        if toonPos[2] < self._bounds[2][1]:
            h = self._cameraLookAtNP.getH()
            if d >= Globals.Camera.MinLeewayZ:
                self._cameraLookAtNP.lookAt(self._toon, 0, 0, self._lookAtZ)
            elif d <= -Globals.Camera.MinLeewayZ:
                self._cameraLookAtNP.lookAt(self._camParent, 0, 0, self._lookAtZ)
            self._cameraLookAtNP.setHpr(h, self._cameraLookAtNP.getP(), 0)
            self._camera.setHpr(smooth(self._camera.getHpr(), self._cameraLookAtNP.getHpr()))
        self._prevToonY = toonPos[1]

    def _updateCollisions(self):
        pos = self._toon.getPos(self._camera) + self._collOffset
        self._camCollRay.setOrigin(pos)
        direction = -Vec3(pos)
        direction.normalize()
        self._camCollRay.setDirection(direction)
        self._collTrav.traverse(render)
        nodesInBetween = {}
        if self._collHandler.getNumEntries() > 0:
            self._collHandler.sortEntries()
            for entry in self._collHandler.getEntries():
                name = entry.getIntoNode().getName()
                if name.find('col_') >= 0:
                    np = entry.getIntoNodePath().getParent()
                    if np not in nodesInBetween:
                        nodesInBetween[np] = np.getParent()

        for np in list(nodesInBetween.keys()):
            if np in self._betweenCamAndToon:
                del self._betweenCamAndToon[np]
            else:
                np.setTransparency(True)
                np.wrtReparentTo(self._transNP)
                if np.getName().find('lightFixture') >= 0:
                    np.find('**/*floor_mesh').hide()
                elif np.getName().find('platform') >= 0:
                    np.find('**/*Floor').hide()

        for np, parent in list(self._betweenCamAndToon.items()):
            np.wrtReparentTo(parent)
            np.setTransparency(False)
            if np.getName().find('lightFixture') >= 0:
                np.find('**/*floor_mesh').show()
            elif np.getName().find('platform') >= 0:
                np.find('**/*Floor').show()

        self._betweenCamAndToon = nodesInBetween
