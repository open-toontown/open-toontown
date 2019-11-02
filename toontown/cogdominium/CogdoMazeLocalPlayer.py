from pandac.PandaModules import Point3, CollisionNode, CollisionSphere, CollisionHandlerEvent
from direct.interval.IntervalGlobal import Func, Sequence, Wait
from direct.showbase.PythonUtil import bound as clamp
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import TTLocalizer
from toontown.minigame.OrthoDrive import OrthoDrive
from toontown.minigame.OrthoWalk import OrthoWalk
from toontown.toonbase import ToontownGlobals
import CogdoGameConsts
import CogdoMazeGameGlobals as Globals
from CogdoMazePlayer import CogdoMazePlayer
from CogdoMazeCameraManager import CogdoMazeCameraManager

class CogdoMazeLocalPlayer(CogdoMazePlayer):
    notify = directNotify.newCategory('CogdoMazeLocalPlayer')

    def __init__(self, id, toon, game, guiMgr):
        CogdoMazePlayer.__init__(self, id, toon)
        self.disableGagCollision()
        self.game = game
        self.maze = self.game.maze
        self._guiMgr = guiMgr
        self.cameraMgr = CogdoMazeCameraManager(self.toon, self.maze, camera, render)
        self._proximityRadius = self.maze.cellWidth * Globals.CameraRemoteToonRadius
        orthoDrive = OrthoDrive(Globals.ToonRunSpeed, maxFrameMove=self.maze.cellWidth / 2, customCollisionCallback=self.maze.doOrthoCollisions, wantSound=True)
        self.orthoWalk = OrthoWalk(orthoDrive)
        self._audioMgr = base.cogdoGameAudioMgr
        self._getMemoSfx = self._audioMgr.createSfx('getMemo', source=self.toon)
        self._waterCoolerFillSfx = self._audioMgr.createSfx('waterCoolerFill', source=self.toon)
        self._hitByDropSfx = self._audioMgr.createSfx('toonHitByDrop', source=self.toon)
        self._winSfx = self._audioMgr.createSfx('win')
        self._loseSfx = self._audioMgr.createSfx('lose')
        self.enabled = False
        self.pickupCount = 0
        self.numEntered = 0
        self.throwPending = False
        self.coolDownAfterHitInterval = Sequence(Wait(Globals.HitCooldownTime), Func(self.setInvulnerable, False), name='coolDownAfterHitInterval-%i' % self.toon.doId)
        self.invulnerable = False
        self.gagHandler = CollisionHandlerEvent()
        self.gagHandler.addInPattern('%fn-into-%in')
        self.exited = False
        self.hints = {'find': False,
         'throw': False,
         'squashed': False,
         'boss': False,
         'minion': False}
        self.accept('control', self.controlKeyPressed)

    def destroy(self):
        self.toon.showName()
        self.ignoreAll()
        self.coolDownAfterHitInterval.clearToInitial()
        del self.coolDownAfterHitInterval
        del self._getMemoSfx
        del self._waterCoolerFillSfx
        del self._hitByDropSfx
        del self._winSfx
        self.orthoWalk.stop()
        self.orthoWalk.destroy()
        del self.orthoWalk
        CogdoMazePlayer.destroy(self)

    def __initCollisions(self):
        collSphere = CollisionSphere(0, 0, 0, Globals.PlayerCollisionRadius)
        collSphere.setTangible(0)
        self.mazeCollisionName = Globals.LocalPlayerCollisionName
        collNode = CollisionNode(self.mazeCollisionName)
        collNode.addSolid(collSphere)
        collNodePath = self.toon.attachNewNode(collNode)
        collNodePath.hide()
        handler = CollisionHandlerEvent()
        handler.addInPattern('%fn-into-%in')
        base.cTrav.addCollider(collNodePath, handler)
        self.handler = handler
        self._collNodePath = collNodePath

    def clearCollisions(self):
        self.handler.clear()

    def __disableCollisions(self):
        self._collNodePath.removeNode()
        del self._collNodePath

    def _isNearPlayer(self, player):
        return self.toon.getDistance(player.toon) <= self._proximityRadius

    def update(self, dt):
        if self.getCurrentOrNextState() != 'Off':
            self._updateCamera(dt)

    def _updateCamera(self, dt):
        numPlayers = 0.0
        for player in self.game.players:
            if player != self and player.toon and self._isNearPlayer(player):
                numPlayers += 1

        d = clamp(Globals.CameraMinDistance + numPlayers / (CogdoGameConsts.MaxPlayers - 1) * (Globals.CameraMaxDistance - Globals.CameraMinDistance), Globals.CameraMinDistance, Globals.CameraMaxDistance)
        self.cameraMgr.setCameraTargetDistance(d)
        self.cameraMgr.update(dt)

    def enterOff(self):
        CogdoMazePlayer.enterOff(self)

    def exitOff(self):
        CogdoMazePlayer.exitOff(self)
        self.toon.hideName()

    def enterReady(self):
        CogdoMazePlayer.enterReady(self)
        self.cameraMgr.enable()

    def exitReady(self):
        CogdoMazePlayer.enterReady(self)

    def enterNormal(self):
        CogdoMazePlayer.enterNormal(self)
        self.orthoWalk.start()

    def exitNormal(self):
        CogdoMazePlayer.exitNormal(self)
        self.orthoWalk.stop()

    def enterHit(self, elapsedTime = 0.0):
        CogdoMazePlayer.enterHit(self, elapsedTime)
        self.setInvulnerable(True)

    def exitHit(self):
        CogdoMazePlayer.exitHit(self)
        self.coolDownAfterHitInterval.clearToInitial()
        self.coolDownAfterHitInterval.start()

    def enterDone(self):
        CogdoMazePlayer.enterDone(self)
        self._guiMgr.hideQuestArrow()
        self.ignore('control')
        self._guiMgr.setMessage('')
        if self.exited == False:
            self.lostMemos()

    def exitDone(self):
        CogdoMazePlayer.exitDone(self)

    def hitByDrop(self):
        if self.equippedGag is not None and not self.hints['squashed']:
            self._guiMgr.setMessageTemporary(TTLocalizer.CogdoMazeSquashHint, Globals.HintTimeout)
            self.hints['squashed'] = True
        self._hitByDropSfx.play()
        CogdoMazePlayer.hitByDrop(self)
        return

    def equipGag(self):
        CogdoMazePlayer.equipGag(self)
        self._waterCoolerFillSfx.play()
        messenger.send(Globals.WaterCoolerHideEventName, [])
        if not self.hints['throw']:
            self._guiMgr.setMessage(TTLocalizer.CogdoMazeThrowHint)
            self.hints['throw'] = True

    def hitSuit(self, suitType):
        if suitType == Globals.SuitTypes.Boss and not self.hints['boss']:
            self._guiMgr.setMessageTemporary(TTLocalizer.CogdoMazeBossHint, Globals.HintTimeout)
            self.hints['boss'] = True
        if suitType != Globals.SuitTypes.Boss and not self.hints['minion']:
            self._guiMgr.setMessageTemporary(TTLocalizer.CogdoMazeMinionHint, Globals.HintTimeout)
            self.hints['minion'] = True

    def createThrowGag(self, gag):
        throwGag = CogdoMazePlayer.createThrowGag(self, gag)
        collSphere = CollisionSphere(0, 0, 0, 0.5)
        collSphere.setTangible(0)
        name = Globals.GagCollisionName
        collNode = CollisionNode(name)
        collNode.setFromCollideMask(ToontownGlobals.PieBitmask)
        collNode.addSolid(collSphere)
        colNp = throwGag.attachNewNode(collNode)
        base.cTrav.addCollider(colNp, self.gagHandler)
        return throwGag

    def showToonThrowingGag(self, heading, pos):
        self._guiMgr.clearMessage()
        return CogdoMazePlayer.showToonThrowingGag(self, heading, pos)

    def removeGag(self):
        if self.equippedGag is None:
            return
        CogdoMazePlayer.removeGag(self)
        self.throwPending = False
        messenger.send(Globals.WaterCoolerShowEventName, [])
        return

    def controlKeyPressed(self):
        if self.game.finished or self.throwPending or self.getCurrentOrNextState() == 'Hit' or self.equippedGag == None:
            return
        self.throwPending = True
        heading = self.toon.getH()
        pos = self.toon.getPos()
        self.game.requestUseGag(pos.getX(), pos.getY(), heading)
        return

    def completeThrow(self):
        self.clearCollisions()
        CogdoMazePlayer.completeThrow(self)

    def shakeCamera(self, strength):
        self.cameraMgr.shake(strength)

    def getCameraShake(self):
        return self.cameraMgr.shakeStrength

    def setInvulnerable(self, bool):
        self.invulnerable = bool

    def handleGameStart(self):
        self.numEntered = len(self.game.players)
        self.__initCollisions()
        self._guiMgr.startGame(TTLocalizer.CogdoMazeFindHint)
        self.hints['find'] = True
        self.notify.info('toonId:%d laff:%d/%d  %d player(s) started maze game' % (self.toon.doId,
         self.toon.hp,
         self.toon.maxHp,
         len(self.game.players)))

    def handleGameExit(self):
        self.cameraMgr.disable()
        self.__disableCollisions()

    def handlePickUp(self, toonId):
        if toonId == self.toon.doId:
            self.pickupCount += 1
            self._guiMgr.setPickupCount(self.pickupCount)
            if self.pickupCount == 1:
                self._guiMgr.showPickupCounter()
            self._getMemoSfx.play()

    def handleOpenDoor(self, door):
        self._guiMgr.setMessage(TTLocalizer.CogdoMazeGameDoorOpens)
        self._guiMgr.showQuestArrow(self.toon, door, Point3(0, 0, self.toon.getHeight() + 2))

    def handleTimeAlert(self):
        self._guiMgr.setMessageTemporary(TTLocalizer.CogdoMazeGameTimeAlert)

    def handleToonRevealsDoor(self, toonId, door):
        if toonId == self.toon.doId:
            self._guiMgr.setMessageTemporary(TTLocalizer.CogdoMazeGameLocalToonFoundExit)

    def handleToonEntersDoor(self, toonId, door):
        self.exited = True
        message = ''
        if door.getPlayerCount() < len(self.game.players):
            message = TTLocalizer.CogdoMazeGameWaitingForToons
        if toonId == self.toon.doId:
            self._guiMgr.setMessage(message)
            self._winSfx.play()
            self._audioMgr.stopMusic()
        self.notify.info('toonId:%d laff:%d/%d  %d player(s) succeeded in maze game. Going to the executive suit building.' % (toonId,
         self.toon.hp,
         self.toon.maxHp,
         len(self.game.players)))
        if self.numEntered > len(self.game.players):
            self.notify.info('%d player(s) failed in maze game' % (self.numEntered - len(self.game.players)))

    def lostMemos(self):
        self.pickupCount = 0
        self._guiMgr.setMessageTemporary(TTLocalizer.CogdoMazeGameTimeOut)
        self._guiMgr.setPickupCount(self.pickupCount)
        self.notify.info('toonId:%d laff:%d/%d  %d player(s) failed in maze game' % (self.toon.doId,
         self.toon.hp,
         self.toon.maxHp,
         len(self.game.players)))
