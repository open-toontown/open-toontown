import math
from pandac.PandaModules import *
from direct.interval.MetaInterval import Sequence, Parallel
from direct.interval.FunctionInterval import Func
from direct.interval.LerpInterval import LerpScaleInterval, LerpColorScaleInterval
from direct.showbase.PythonUtil import bound
from toontown.toon import ToonHead
from toontown.minigame.CannonGameGlobals import *
from toontown.toonbase import ToontownGlobals
from toontown.parties.PartyUtils import toRadians, calcVelocity
from direct.showbase.PythonUtil import StackTrace
CANNON_ROTATION_MIN = -70
CANNON_ROTATION_MAX = 70
INITIAL_VELOCITY = 80.0
CANNON_BARREL_TOONHEAD_Y = 6.0

class Cannon:
    notify = directNotify.newCategory('DistributedPartyCannon')

    def __init__(self, parent, pos = Point3(0, 0, 0)):
        self.__previousRotation = 0.0
        self.__previousAngle = 0.0
        self._rotation = 0.0
        self._angle = 0.0
        self._position = pos
        self._parent = parent
        self.parentNode = None
        self.cannonNode = None
        self.barrelNode = None
        self.sndCannonMove = None
        self.sndCannonFire = None
        self.collSphere = None
        self.collNode = None
        self.collNodePath = None
        self.toonInside = None
        self.toonHead = None
        self.toonOriginalScale = 0.0
        self.toonParentNode = None
        return

    def reset(self):
        self.setRotation(0)
        self.setAngle((CANNON_ANGLE_MIN + CANNON_ANGLE_MAX * 0.5) * 0.5)
        self.parentNode.setPos(self._position)
        self.updateModel()

    def load(self, nodeName):
        self.parentNode = NodePath(nodeName)
        self.cannonNode = loader.loadModel('phase_4/models/minigames/toon_cannon')
        self.cannonNode.reparentTo(self.parentNode)
        self.barrelNode = self.cannonNode.find('**/cannon')
        self.shadowNode = self.cannonNode.find('**/square_drop_shadow')
        self.smokeNode = loader.loadModel('phase_4/models/props/test_clouds')
        self.smokeNode.setBillboardPointEye()
        self.sndCannonMove = base.loadSfx('phase_4/audio/sfx/MG_cannon_adjust.mp3')
        self.sndCannonFire = base.loadSfx('phase_4/audio/sfx/MG_cannon_fire_alt.mp3')
        self.collSphere = CollisionSphere(0, 0, 0, self.getSphereRadius())
        self.collSphere.setTangible(1)
        self.collNode = CollisionNode(self.getCollisionName())
        self.collNode.setCollideMask(ToontownGlobals.WallBitmask)
        self.collNode.addSolid(self.collSphere)
        self.collNodePath = self.parentNode.attachNewNode(self.collNode)

    def unload(self):
        self.__cleanupToonInside()
        if self.cannonNode:
            self.cannonNode.removeNode()
            self.cannonNode = None
        if self.smokeNode:
            self.smokeNode.removeNode()
            self.smokeNode = None
        del self.sndCannonMove
        del self.sndCannonFire
        del self._position
        self.ignoreAll()
        return

    def updateModel(self, rotation = None, angle = None):
        if rotation:
            self.rotation = rotation
        if angle:
            self.angle = angle
        self.cannonNode.setHpr(self._rotation, 0, 0)
        self.barrelNode.setHpr(0, self._angle, 0)
        maxP = 90
        newP = self.barrelNode.getP()
        yScale = 1 - 0.5 * float(newP) / maxP
        self.shadowNode.setScale(1, yScale, 1)

    def playFireSequence(self):
        self.smokeNode.reparentTo(self.barrelNode)
        self.smokeNode.setPos(0, 6, -3)
        self.smokeNode.setScale(0.5)
        self.smokeNode.wrtReparentTo(render)
        track = Sequence(Parallel(LerpScaleInterval(self.smokeNode, 0.5, 3), LerpColorScaleInterval(self.smokeNode, 0.5, Vec4(2, 2, 2, 0))), Func(self.smokeNode.reparentTo, hidden), Func(self.smokeNode.clearColorScale))
        base.playSfx(self.sndCannonFire)
        track.start()

    def loopMovingSound(self):
        base.playSfx(self.sndCannonMove, looping=1)

    def stopMovingSound(self):
        self.sndCannonMove.stop()

    def show(self):
        self.reset()
        self.parentNode.reparentTo(self._parent)

    def hide(self):
        self.parentNode.reparentTo(hidden)

    def placeToonInside(self, toon):
        self.__setToonInside(toon)
        self.__createToonHead(toon)
        self.__placeToon()

    def __setToonInside(self, toon):
        self.toonInside = toon
        toonName = 'None'
        if toon:
            toonName = toon.getName()
        self.notify.debug('__setToonInside self.toonInside=%s\nstack=%s' % (toonName, StackTrace().compact()))
        self.toonInside.stopSmooth()
        self.toonOriginalScale = toon.getScale()
        toon.useLOD(1000)
        self.toonParentNode = render.attachNewNode('toonOriginChange')
        self.toonInside.wrtReparentTo(self.toonParentNode)
        self.toonInside.setPosHpr(0, 0, -(self.toonInside.getHeight() / 2.0), 0, -90, 0)

    def __createToonHead(self, toon):
        self.toonHead = ToonHead.ToonHead()
        self.toonHead.setupHead(toon.style)
        self.toonHead.reparentTo(hidden)
        tag = NametagFloat3d()
        tag.setContents(Nametag.CSpeech | Nametag.CThought)
        tag.setBillboardOffset(0)
        tag.setAvatar(self.toonHead)
        toon.nametag.addNametag(tag)
        tagPath = self.toonHead.attachNewNode(tag.upcastToPandaNode())
        tagPath.setPos(0, 0, 1)
        self.toonHead.tag = tag

    def __placeToon(self):
        self.showToonHead()
        self.toonHead.setPosHpr(0, CANNON_BARREL_TOONHEAD_Y, 0, 0, -45, 0)
        scale = self.toonOriginalScale
        self.toonHead.setScale(render, scale[0], scale[1], scale[2])
        self.toonParentNode.reparentTo(hidden)
        self.toonParentNode.setPos(self.getToonFirePos())

    def showToonHead(self):
        if self.toonHead:
            self.toonHead.startBlink()
            self.toonHead.startLookAround()
            self.toonHead.reparentTo(self.barrelNode)

    def hideToonHead(self):
        if self.toonHead:
            self.toonHead.stopBlink()
            self.toonHead.stopLookAroundNow()
            self.toonHead.reparentTo(hidden)

    def removeToonReadyToFire(self):
        toon = self.toonInside
        self.toonInside.wrtReparentTo(render)
        y = self.toonHead.getY(self.barrelNode) - (self.toonInside.getHeight() - self.toonHead.getHeight())
        self.toonInside.setPosHpr(self.barrelNode, 0, y, 0, 0, -90, 0)
        return self.__removeToon()

    def removeToonDidNotFire(self):
        self.toonInside.reparentTo(self.cannonNode)
        self.toonInside.setPos(2, -4, 0)
        self.toonInside.wrtReparentTo(render)
        return self.__removeToon()

    def __removeToon(self):
        self.stopMovingSound()
        toonNode = self.toonParentNode
        self.toonInside.resetLOD()
        self.hideToonHead()
        self.__cleanupToonInside()
        return toonNode

    def __cleanupToonInside(self):
        toonName = 'None'
        if self.toonInside:
            toonName = self.toonInside.getName()
        self.notify.debug('__cleanupToonInside self.toonInside=%s\nstack=%s' % (toonName, StackTrace().compact()))
        if self.toonHead != None:
            self.hideToonHead()
            if hasattr(self.toonInside, 'nametag'):
                self.toonInside.nametag.removeNametag(self.toonHead.tag)
            self.toonHead.delete()
            self.toonHead = None
        self.toonInside = None
        self.toonParentNode = None
        return

    def getSphereRadius(self):
        return 1.5

    def getCollisionName(self):
        return self.parentNode.getName() + 'Collision'

    def getEnterCollisionName(self):
        return 'enter' + self.getCollisionName()

    def isToonInside(self):
        return self.toonHead != None

    def getToonInside(self):
        return self.toonInside

    def setRotation(self, rotation):
        self.__previousRotation = self._rotation
        self._rotation = bound(rotation, CANNON_ROTATION_MIN, CANNON_ROTATION_MAX)

    def getRotation(self):
        return self._rotation

    def setAngle(self, angle):
        self.__previousAngle = self._angle
        self._angle = bound(angle, CANNON_ANGLE_MIN, CANNON_ANGLE_MAX)

    def getAngle(self):
        return self._angle

    def hasMoved(self):
        return self.__previousRotation != self._rotation or self.__previousAngle != self._angle

    def getBarrelHpr(self, node):
        return self.barrelNode.getHpr(node)

    def getToonFirePos(self):
        if self.toonHead:
            return self.toonHead.getPos(render)
        return Point3.zero()

    def getToonFireHpr(self):
        if self.toonHead:
            return self.toonHead.getHpr(render)
        return Point3.zero()

    def getToonFireVel(self):
        hpr = self.barrelNode.getHpr(render)
        rotation = toRadians(hpr[0])
        angle = toRadians(hpr[1])
        return calcVelocity(rotation, angle, initialVelocity=INITIAL_VELOCITY)
