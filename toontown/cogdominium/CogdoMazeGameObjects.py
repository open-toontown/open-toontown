from pandac.PandaModules import CollisionSphere, CollisionTube, CollisionNode
from pandac.PandaModules import NodePath, BitMask32
from pandac.PandaModules import Point3, Point4, WaitInterval, Vec3, Vec4
from direct.interval.IntervalGlobal import LerpScaleInterval, LerpColorScaleInterval, LerpPosInterval, LerpFunc
from direct.interval.IntervalGlobal import Func, Sequence, Parallel
from direct.showbase.DirectObject import DirectObject
from direct.task.Task import Task
from toontown.toonbase import ToontownGlobals
import CogdoMazeGameGlobals as Globals
from CogdoGameExit import CogdoGameExit
import CogdoUtil
import math
import random

class CogdoMazeSplattable:

    def __init__(self, object, name, collisionRadius):
        self.object = object
        self.splat = CogdoUtil.loadMazeModel('splash')
        self.splat.setBillboardPointEye()
        self.splat.setBin('fixed', 40)
        self.splat.setDepthTest(False)
        self.splat.setDepthWrite(False)
        self.splatTrack = None
        self._splatSfxIval = base.cogdoGameAudioMgr.createSfxIval('splat')
        self.initGagCollision(name, collisionRadius)
        return

    def destroy(self):
        self.disableGagCollision()
        if self._splatSfxIval.isPlaying():
            self._splatSfxIval.finish()
        del self._splatSfxIval

    def initGagCollision(self, name, radius):
        self.gagCollisionName = name
        collision = CollisionTube(0, 0, 0, 0, 0, 4, radius)
        collision.setTangible(1)
        self.gagCollNode = CollisionNode(self.gagCollisionName)
        self.gagCollNode.setIntoCollideMask(ToontownGlobals.PieBitmask)
        self.gagCollNode.addSolid(collision)
        self.gagCollNodePath = self.object.attachNewNode(self.gagCollNode)

    def disableGagCollision(self):
        self.gagCollNodePath.removeNode()

    def doSplat(self):
        if self.splatTrack and self.splatTrack.isPlaying():
            self.splatTrack.finish()
        self.splat.reparentTo(render)
        self.splat.setPos(self.object, 0, 0, 3.0)
        self.splat.setY(self.splat.getY() - 1.0)
        self._splatSfxIval.node = self.splat
        self.splatTrack = Parallel(self._splatSfxIval, Sequence(Func(self.splat.showThrough), LerpScaleInterval(self.splat, duration=0.5, scale=6, startScale=1, blendType='easeOut'), Func(self.splat.hide)))
        self.splatTrack.start()


class CogdoMazeDrop(NodePath, DirectObject):

    def __init__(self, game, id, x, y):
        NodePath.__init__(self, 'dropNode%s' % id)
        self.game = game
        self.id = id
        self.reparentTo(hidden)
        self.setPos(x, y, 0)
        shadow = loader.loadModel('phase_3/models/props/square_drop_shadow')
        shadow.setZ(0.2)
        shadow.setBin('ground', 10)
        shadow.setColor(1, 1, 1, 1)
        shadow.reparentTo(self)
        self.shadow = shadow
        drop = CogdoUtil.loadMazeModel('cabinetSmFalling')
        roll = random.randint(-15, 15)
        drop.setHpr(0, 0, roll)
        drop.setZ(Globals.DropHeight)
        self.collTube = CollisionTube(0, 0, 0, 0, 0, 4, Globals.DropCollisionRadius)
        self.collTube.setTangible(0)
        name = Globals.DropCollisionName
        self.collNode = CollisionNode(name)
        self.collNode.addSolid(self.collTube)
        self.collNodePath = drop.attachNewNode(self.collNode)
        self.collNodePath.hide()
        self.collNodePath.setTag('isFalling', str('True'))
        drop.reparentTo(self)
        self.drop = drop
        self._dropSfx = base.cogdoGameAudioMgr.createSfxIval('drop', volume=0.6)

    def disableCollisionDamage(self):
        self.collTube.setTangible(1)
        self.collTube.setRadius(Globals.DroppedCollisionRadius)
        self.collNode.setIntoCollideMask(ToontownGlobals.WallBitmask)
        self.collNodePath.setTag('isFalling', str('False'))

    def getDropIval(self):
        shadow = self.shadow
        drop = self.drop
        id = self.id
        hangTime = Globals.ShadowTime
        dropTime = Globals.DropTime
        dropHeight = Globals.DropHeight
        targetShadowScale = 0.5
        targetShadowAlpha = 0.4
        shadowScaleIval = LerpScaleInterval(shadow, dropTime, targetShadowScale, startScale=0)
        shadowAlphaIval = LerpColorScaleInterval(shadow, hangTime, Point4(1, 1, 1, targetShadowAlpha), startColorScale=Point4(1, 1, 1, 0))
        shadowIval = Parallel(shadowScaleIval, shadowAlphaIval)
        startPos = Point3(0, 0, dropHeight)
        drop.setPos(startPos)
        dropIval = LerpPosInterval(drop, dropTime, Point3(0, 0, 0), startPos=startPos, blendType='easeIn')
        dropSoundIval = self._dropSfx
        dropSoundIval.node = self
        self.drop.setTransparency(1)

        def _setRandScale(t):
            self.drop.setScale(self, 1 - random.random() / 16, 1 - random.random() / 16, 1 - random.random() / 4)

        scaleChange = 0.4 + random.random() / 4
        dropShakeSeq = Sequence(LerpScaleInterval(self.drop, 0.25, Vec3(1.0 + scaleChange, 1.0 + scaleChange / 2, 1.0 - scaleChange), blendType='easeInOut'), LerpScaleInterval(self.drop, 0.25, Vec3(1.0, 1.0, 1.0), blendType='easeInOut'), Func(self.disableCollisionDamage), LerpScaleInterval(self.drop, 0.2, Vec3(1.0 + scaleChange / 8, 1.0 + scaleChange / 8, 1.0 - scaleChange / 8), blendType='easeInOut'), LerpScaleInterval(self.drop, 0.2, Vec3(1.0, 1.0, 1.0), blendType='easeInOut'), LerpScaleInterval(self.drop, 0.15, Vec3(1.0 + scaleChange / 16, 1.0 + scaleChange / 16, 1.0 - scaleChange / 16), blendType='easeInOut'), LerpScaleInterval(self.drop, 0.15, Vec3(1.0, 1.0, 1.0), blendType='easeInOut'), LerpScaleInterval(self.drop, 0.1, Vec3(1.0 + scaleChange / 16, 1.0 + scaleChange / 8, 1.0 - scaleChange / 16), blendType='easeInOut'), LerpColorScaleInterval(self.drop, Globals.DropFadeTime, Vec4(1.0, 1.0, 1.0, 0.0)))
        ival = Sequence(Func(self.reparentTo, render), Parallel(Sequence(WaitInterval(hangTime), dropIval), shadowIval), Parallel(Func(self.game.dropHit, self, id), dropSoundIval, dropShakeSeq), Func(self.game.cleanupDrop, id), name='drop%s' % id)
        self.ival = ival
        return ival

    def destroy(self):
        self.ival.pause()
        self.ival = None
        self._dropSfx.pause()
        self._dropSfx = None
        self.collTube = None
        self.collNode = None
        self.collNodePath.removeNode()
        self.collNodePath = None
        self.removeNode()
        return


class CogdoMazeExit(CogdoGameExit, DirectObject):
    EnterEventName = 'CogdoMazeDoor_Enter'

    def __init__(self):
        CogdoGameExit.__init__(self)
        self.revealed = False
        self._players = []
        self._initCollisions()

    def _initCollisions(self):
        collSphere = CollisionSphere(0, 0, 0, 3.0)
        collSphere.setTangible(0)
        self.collNode = CollisionNode(self.getName())
        self.collNode.addSolid(collSphere)
        self.collNP = self.attachNewNode(self.collNode)

    def destroy(self):
        self.ignoreAll()
        CogdoGameExit.destroy(self)

    def enable(self):
        self.collNode.setFromCollideMask(ToontownGlobals.WallBitmask)
        self.accept('enter' + self.getName(), self._handleEnterCollision)

    def disable(self):
        self.ignore('enter' + self.getName())
        self.collNode.setFromCollideMask(BitMask32(0))

    def _handleEnterCollision(self, collEntry):
        messenger.send(CogdoMazeExit.EnterEventName, [self])

    def onstage(self):
        self.unstash()
        self.enable()

    def offstage(self):
        self.stash()
        self.disable()

    def playerEntersDoor(self, player):
        if player not in self._players:
            self._players.append(player)
            self.toonEnters(player.toon)

    def getPlayerCount(self):
        return len(self._players)

    def hasPlayer(self, player):
        return player in self._players


class CogdoMazeWaterCooler(NodePath, DirectObject):
    UpdateTaskName = 'CogdoMazeWaterCooler_Update'

    def __init__(self, serialNum, model):
        NodePath.__init__(self, 'CogdoMazeWaterCooler-%i' % serialNum)
        self.serialNum = serialNum
        self._model = model
        self._model.reparentTo(self)
        self._model.setPosHpr(0, 0, 0, 0, 0, 0)
        self._initCollisions()
        self._initArrow()
        self._update = None
        self.__startUpdateTask()
        return

    def destroy(self):
        self.ignoreAll()
        self.__stopUpdateTask()
        self.collNodePath.removeNode()
        self.removeNode()

    def _initCollisions(self):
        offset = Globals.WaterCoolerTriggerOffset
        self.collSphere = CollisionSphere(offset[0], offset[1], offset[2], Globals.WaterCoolerTriggerRadius)
        self.collSphere.setTangible(0)
        name = Globals.WaterCoolerCollisionName
        self.collNode = CollisionNode(name)
        self.collNode.addSolid(self.collSphere)
        self.collNodePath = self.attachNewNode(self.collNode)

    def _initArrow(self):
        matchingGameGui = loader.loadModel('phase_3.5/models/gui/matching_game_gui')
        arrow = matchingGameGui.find('**/minnieArrow')
        arrow.setScale(Globals.CoolerArrowScale)
        arrow.setColor(*Globals.CoolerArrowColor)
        arrow.setPos(0, 0, Globals.CoolerArrowZ)
        arrow.setHpr(0, 0, 90)
        arrow.setBillboardAxis()
        self._arrow = NodePath('Arrow')
        arrow.reparentTo(self._arrow)
        self._arrow.reparentTo(self)
        self._arrowTime = 0
        self.accept(Globals.WaterCoolerShowEventName, self.showArrow)
        self.accept(Globals.WaterCoolerHideEventName, self.hideArrow)
        matchingGameGui.removeNode()

    def showArrow(self):
        self._arrow.unstash()

    def hideArrow(self):
        self._arrow.stash()

    def update(self, dt):
        newZ = math.sin(globalClock.getFrameTime() * Globals.CoolerArrowSpeed) * Globals.CoolerArrowBounce
        self._arrow.setZ(newZ)

    def __startUpdateTask(self):
        self.__stopUpdateTask()
        self._update = taskMgr.add(self._updateTask, self.UpdateTaskName, 45)

    def __stopUpdateTask(self):
        if self._update is not None:
            taskMgr.remove(self._update)
        return

    def _updateTask(self, task):
        dt = globalClock.getDt()
        self.update(dt)
        return Task.cont
