from direct.directnotify import DirectNotifyGlobal
from pandac.PandaModules import *
from toontown.toonbase.ToonBaseGlobal import *
from DistributedMinigame import *
from direct.distributed.ClockDelta import *
from direct.interval.IntervalGlobal import *
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import ToontownTimer
from direct.task.Task import Task
import Trajectory
import math
from toontown.toon import ToonHead
from toontown.effects import Splash
from toontown.effects import DustCloud
import CannonGameGlobals
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from toontown.toonbase import TTLocalizer
LAND_TIME = 2
WORLD_SCALE = 2.0
GROUND_SCALE = 1.4 * WORLD_SCALE
CANNON_SCALE = 1.0
FAR_PLANE_DIST = 600 * WORLD_SCALE
CANNON_Y = -int(CannonGameGlobals.TowerYRange / 2 * 1.3)
CANNON_X_SPACING = 12
CANNON_Z = 20
CANNON_MOVE_UPDATE_FREQ = 0.5
CAMERA_PULLBACK_MIN = 20
CAMERA_PULLBACK_MAX = 40
MAX_LOOKAT_OFFSET = 80
TOON_TOWER_THRESHOLD = 150
SHADOW_Z_OFFSET = 0.5
TOWER_HEIGHT = 43.85
TOWER_RADIUS = 10.5
BUCKET_HEIGHT = 36
TOWER_Y_RANGE = CannonGameGlobals.TowerYRange
TOWER_X_RANGE = int(TOWER_Y_RANGE / 2.0)
INITIAL_VELOCITY = 94.0
WHISTLE_SPEED = INITIAL_VELOCITY * 0.55

class DistributedCannonGame(DistributedMinigame):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedMinigame')
    font = ToontownGlobals.getToonFont()
    LOCAL_CANNON_MOVE_TASK = 'localCannonMoveTask'
    REWARD_COUNTDOWN_TASK = 'cannonGameRewardCountdown'
    HIT_GROUND = 0
    HIT_TOWER = 1
    HIT_WATER = 2
    FIRE_KEY = 'control'
    UP_KEY = 'arrow_up'
    DOWN_KEY = 'arrow_down'
    LEFT_KEY = 'arrow_left'
    RIGHT_KEY = 'arrow_right'
    INTRO_TASK_NAME = 'CannonGameIntro'
    INTRO_TASK_NAME_CAMERA_LERP = 'CannonGameIntroCamera'

    def __init__(self, cr):
        DistributedMinigame.__init__(self, cr)
        self.gameFSM = ClassicFSM.ClassicFSM('DistributedCannonGame', [State.State('off', self.enterOff, self.exitOff, ['aim']),
         State.State('aim', self.enterAim, self.exitAim, ['shoot', 'waitForToonsToLand', 'cleanup']),
         State.State('shoot', self.enterShoot, self.exitShoot, ['aim', 'waitForToonsToLand', 'cleanup']),
         State.State('waitForToonsToLand', self.enterWaitForToonsToLand, self.exitWaitForToonsToLand, ['cleanup']),
         State.State('cleanup', self.enterCleanup, self.exitCleanup, [])], 'off', 'cleanup')
        self.addChildGameFSM(self.gameFSM)
        self.cannonLocationDict = {}
        self.cannonPositionDict = {}
        self.cannonDict = {}
        self.toonModelDict = {}
        self.dropShadowDict = {}
        self.toonHeadDict = {}
        self.toonScaleDict = {}
        self.toonIntervalDict = {}
        self.leftPressed = 0
        self.rightPressed = 0
        self.upPressed = 0
        self.downPressed = 0
        self.cannonMoving = 0
        self.modelCount = 14

    def getTitle(self):
        return TTLocalizer.CannonGameTitle

    def getInstructions(self):
        return TTLocalizer.CannonGameInstructions

    def getMaxDuration(self):
        return CannonGameGlobals.GameTime

    def load(self):
        self.notify.debug('load')
        DistributedMinigame.load(self)
        self.sky = loader.loadModel('phase_3.5/models/props/TT_sky')
        self.ground = loader.loadModel('phase_4/models/minigames/toon_cannon_gameground')
        self.tower = loader.loadModel('phase_4/models/minigames/toon_cannon_water_tower')
        self.cannon = loader.loadModel('phase_4/models/minigames/toon_cannon')
        self.dropShadow = loader.loadModel('phase_3/models/props/drop_shadow')
        self.hill = loader.loadModel('phase_4/models/minigames/cannon_hill')
        self.sky.setScale(WORLD_SCALE)
        self.ground.setScale(GROUND_SCALE)
        self.cannon.setScale(CANNON_SCALE)
        self.dropShadow.setColor(0, 0, 0, 0.5)
        self.ground.setColor(0.85, 0.85, 0.85, 1.0)
        self.hill.setScale(1, 1, CANNON_Z / 20.0)
        self.dropShadow.setBin('fixed', 0, 1)
        self.splash = Splash.Splash(render)
        self.dustCloud = DustCloud.DustCloud(render)
        purchaseModels = loader.loadModel('phase_4/models/gui/purchase_gui')
        self.jarImage = purchaseModels.find('**/Jar')
        self.jarImage.reparentTo(hidden)
        self.rewardPanel = DirectLabel(parent=hidden, relief=None, pos=(1.16, 0.0, 0.45), scale=0.65, text='', text_scale=0.2, text_fg=(0.95, 0.95, 0, 1), text_pos=(0, -.13), text_font=ToontownGlobals.getSignFont(), image=self.jarImage)
        self.rewardPanelTitle = DirectLabel(parent=self.rewardPanel, relief=None, pos=(0, 0, 0.06), scale=0.08, text=TTLocalizer.CannonGameReward, text_fg=(0.95, 0.95, 0, 1), text_shadow=(0, 0, 0, 1))
        self.music = base.loadMusic('phase_4/audio/bgm/MG_cannon_game.mid')
        self.sndCannonMove = base.loadSfx('phase_4/audio/sfx/MG_cannon_adjust.mp3')
        self.sndCannonFire = base.loadSfx('phase_4/audio/sfx/MG_cannon_fire_alt.mp3')
        self.sndHitGround = base.loadSfx('phase_4/audio/sfx/MG_cannon_hit_dirt.mp3')
        self.sndHitTower = base.loadSfx('phase_4/audio/sfx/MG_cannon_hit_tower.mp3')
        self.sndHitWater = base.loadSfx('phase_4/audio/sfx/MG_cannon_splash.mp3')
        self.sndWhizz = base.loadSfx('phase_4/audio/sfx/MG_cannon_whizz.mp3')
        self.sndWin = base.loadSfx('phase_4/audio/sfx/MG_win.mp3')
        self.sndRewardTick = base.loadSfx('phase_3.5/audio/sfx/tick_counter.mp3')
        guiModel = 'phase_4/models/gui/cannon_game_gui'
        cannonGui = loader.loadModel(guiModel)
        self.aimPad = DirectFrame(image=cannonGui.find('**/CannonFire_PAD'), relief=None, pos=(0.7, 0, -0.553333), scale=0.8)
        cannonGui.removeNode()
        self.aimPad.hide()
        self.fireButton = DirectButton(parent=self.aimPad, image=((guiModel, '**/Fire_Btn_UP'), (guiModel, '**/Fire_Btn_DN'), (guiModel, '**/Fire_Btn_RLVR')), relief=None, pos=(0.0115741, 0, 0.00505051), scale=1.0, command=self.__firePressed)
        self.upButton = DirectButton(parent=self.aimPad, image=((guiModel, '**/Cannon_Arrow_UP'), (guiModel, '**/Cannon_Arrow_DN'), (guiModel, '**/Cannon_Arrow_RLVR')), relief=None, pos=(0.0115741, 0, 0.221717))
        self.downButton = DirectButton(parent=self.aimPad, image=((guiModel, '**/Cannon_Arrow_UP'), (guiModel, '**/Cannon_Arrow_DN'), (guiModel, '**/Cannon_Arrow_RLVR')), relief=None, pos=(0.0136112, 0, -0.210101), image_hpr=(0, 0, 180))
        self.leftButton = DirectButton(parent=self.aimPad, image=((guiModel, '**/Cannon_Arrow_UP'), (guiModel, '**/Cannon_Arrow_DN'), (guiModel, '**/Cannon_Arrow_RLVR')), relief=None, pos=(-0.199352, 0, -0.000505269), image_hpr=(0, 0, -90))
        self.rightButton = DirectButton(parent=self.aimPad, image=((guiModel, '**/Cannon_Arrow_UP'), (guiModel, '**/Cannon_Arrow_DN'), (guiModel, '**/Cannon_Arrow_RLVR')), relief=None, pos=(0.219167, 0, -0.00101024), image_hpr=(0, 0, 90))
        self.aimPad.setColor(1, 1, 1, 0.9)

        def bindButton(button, upHandler, downHandler):
            button.bind(DGG.B1PRESS, lambda x, handler = upHandler: handler())
            button.bind(DGG.B1RELEASE, lambda x, handler = downHandler: handler())

        bindButton(self.upButton, self.__upPressed, self.__upReleased)
        bindButton(self.downButton, self.__downPressed, self.__downReleased)
        bindButton(self.leftButton, self.__leftPressed, self.__leftReleased)
        bindButton(self.rightButton, self.__rightPressed, self.__rightReleased)
        self.timer = ToontownTimer.ToontownTimer()
        self.timer.posInTopRightCorner()
        self.timer.hide()
        self.DEBUG_TOWER_RANGE = 0
        self.DEBUG_CANNON_FAR_LEFT = 0
        self.DEBUG_TOWER_NEAR = 1
        self.DEBUG_TOWER_FAR_LEFT = 1
        return

    def unload(self):
        self.notify.debug('unload')
        DistributedMinigame.unload(self)
        self.sky.removeNode()
        del self.sky
        self.ground.removeNode()
        del self.ground
        self.tower.removeNode()
        del self.tower
        self.cannon.removeNode()
        del self.cannon
        del self.dropShadowDict
        self.dropShadow.removeNode()
        del self.dropShadow
        self.splash.destroy()
        del self.splash
        self.dustCloud.destroy()
        del self.dustCloud
        self.hill.removeNode()
        del self.hill
        self.rewardPanel.destroy()
        del self.rewardPanel
        self.jarImage.removeNode()
        del self.jarImage
        del self.music
        del self.sndCannonMove
        del self.sndCannonFire
        del self.sndHitGround
        del self.sndHitTower
        del self.sndHitWater
        del self.sndWhizz
        del self.sndWin
        del self.sndRewardTick
        self.aimPad.destroy()
        del self.aimPad
        del self.fireButton
        del self.upButton
        del self.downButton
        del self.leftButton
        del self.rightButton
        for avId in self.toonHeadDict.keys():
            head = self.toonHeadDict[avId]
            head.stopBlink()
            head.stopLookAroundNow()
            av = self.getAvatar(avId)
            if av:
                av.loop('neutral')
                av.setPlayRate(1.0, 'run')
                av.nametag.removeNametag(head.tag)
            head.delete()

        del self.toonHeadDict
        for model in self.toonModelDict.values():
            model.removeNode()

        del self.toonModelDict
        del self.toonScaleDict
        for interval in self.toonIntervalDict.values():
            interval.finish()

        del self.toonIntervalDict
        for avId in self.avIdList:
            self.cannonDict[avId][0].removeNode()
            del self.cannonDict[avId][0]

        del self.cannonDict
        self.timer.destroy()
        del self.timer
        del self.cannonLocationDict
        self.removeChildGameFSM(self.gameFSM)
        del self.gameFSM

    def onstage(self):
        self.notify.debug('onstage')
        DistributedMinigame.onstage(self)
        self.__createCannons()
        for avId in self.avIdList:
            self.cannonDict[avId][0].reparentTo(render)

        self.towerPos = self.getTowerPosition()
        self.tower.setPos(self.towerPos)
        self.tower.reparentTo(render)
        self.sky.reparentTo(render)
        self.ground.reparentTo(render)
        self.hill.setPosHpr(0, CANNON_Y + 2.33, 0, 0, 0, 0)
        self.hill.reparentTo(render)
        self.splash.reparentTo(render)
        self.dustCloud.reparentTo(render)
        self.__createToonModels(self.localAvId)
        camera.reparentTo(render)
        self.__oldCamFar = base.camLens.getFar()
        base.camLens.setFar(FAR_PLANE_DIST)
        self.__startIntro()
        base.transitions.irisIn(0.4)
        base.playMusic(self.music, looping=1, volume=0.8)

    def offstage(self):
        self.notify.debug('offstage')
        self.sky.reparentTo(hidden)
        self.ground.reparentTo(hidden)
        self.hill.reparentTo(hidden)
        self.tower.reparentTo(hidden)
        for avId in self.avIdList:
            self.cannonDict[avId][0].reparentTo(hidden)
            if self.dropShadowDict.has_key(avId):
                self.dropShadowDict[avId].reparentTo(hidden)
            av = self.getAvatar(avId)
            if av:
                av.dropShadow.show()
                av.resetLOD()

        self.splash.reparentTo(hidden)
        self.splash.stop()
        self.dustCloud.reparentTo(hidden)
        self.dustCloud.stop()
        self.__stopIntro()
        base.camLens.setFar(self.__oldCamFar)
        self.timer.reparentTo(hidden)
        self.rewardPanel.reparentTo(hidden)
        DistributedMinigame.offstage(self)

    def getTowerPosition(self):
        yRange = TOWER_Y_RANGE
        yMin = yRange * 0.3
        yMax = yRange
        if self.DEBUG_TOWER_RANGE:
            if self.DEBUG_TOWER_NEAR:
                y = yMin
            else:
                y = yMax
        else:
            y = self.randomNumGen.randint(yMin, yMax)
        xRange = TOWER_X_RANGE
        if self.DEBUG_TOWER_RANGE:
            if self.DEBUG_TOWER_FAR_LEFT:
                x = 0
            else:
                x = xRange
        else:
            x = self.randomNumGen.randint(0, xRange)
        x = x - int(xRange / 2.0)
        if base.wantMinigameDifficulty:
            diff = self.getDifficulty()
            scale = 0.5 + 0.5 * diff
            x *= scale
            yCenter = (yMin + yMax) / 2.0
            y = (y - yCenter) * scale + yCenter
        x = float(x) * (float(y) / float(yRange))
        y = y - int(yRange / 2.0)
        self.notify.debug('getTowerPosition: ' + str(x) + ', ' + str(y))
        return Point3(x, y, 0.0)

    def __createCannons(self):
        for avId in self.avIdList:
            cannon = self.cannon.copyTo(hidden)
            barrel = cannon.find('**/cannon')
            self.cannonDict[avId] = [cannon, barrel]

        numAvs = self.numPlayers
        for i in range(numAvs):
            avId = self.avIdList[i]
            self.cannonLocationDict[avId] = Point3(i * CANNON_X_SPACING - (numAvs - 1) * CANNON_X_SPACING / 2, CANNON_Y, CANNON_Z)
            if self.DEBUG_TOWER_RANGE:
                if self.DEBUG_CANNON_FAR_LEFT:
                    self.cannonLocationDict[avId] = Point3(0 * CANNON_X_SPACING - (4 - 1) * CANNON_X_SPACING / 2, CANNON_Y, CANNON_Z)
                else:
                    self.cannonLocationDict[avId] = Point3(3 * CANNON_X_SPACING - (4 - 1) * CANNON_X_SPACING / 2, CANNON_Y, CANNON_Z)
            self.cannonPositionDict[avId] = [0, CannonGameGlobals.CANNON_ANGLE_MIN]
            self.cannonDict[avId][0].setPos(self.cannonLocationDict[avId])
            self.__updateCannonPosition(avId)

    def setGameReady(self):
        if not self.hasLocalToon:
            return
        self.notify.debug('setGameReady')
        if DistributedMinigame.setGameReady(self):
            return
        for avId in self.avIdList:
            if avId != self.localAvId:
                self.__createToonModels(avId)

    def __createToonModels(self, avId):
        toon = self.getAvatar(avId)
        self.toonScaleDict[avId] = toon.getScale()
        toon.useLOD(1000)
        toonParent = render.attachNewNode('toonOriginChange')
        toon.reparentTo(toonParent)
        toon.setPosHpr(0, 0, -(toon.getHeight() / 2.0), 0, 0, 0)
        self.toonModelDict[avId] = toonParent
        head = ToonHead.ToonHead()
        head.setupHead(self.getAvatar(avId).style)
        head.reparentTo(hidden)
        self.toonHeadDict[avId] = head
        toon = self.getAvatar(avId)
        tag = NametagFloat3d()
        tag.setContents(Nametag.CSpeech | Nametag.CThought)
        tag.setBillboardOffset(0)
        tag.setAvatar(head)
        toon.nametag.addNametag(tag)
        tagPath = head.attachNewNode(tag.upcastToPandaNode())
        tagPath.setPos(0, 0, 1)
        head.tag = tag
        self.__loadToonInCannon(avId)
        self.getAvatar(avId).dropShadow.hide()
        self.dropShadowDict[avId] = self.dropShadow.copyTo(hidden)

    def setGameStart(self, timestamp):
        if not self.hasLocalToon:
            return
        self.notify.debug('setGameStart')
        DistributedMinigame.setGameStart(self, timestamp)
        self.__stopIntro()
        self.__putCameraBehindCannon()
        if not base.config.GetBool('endless-cannon-game', 0):
            self.timer.show()
            self.timer.countdown(CannonGameGlobals.GameTime, self.__gameTimerExpired)
        self.rewardPanel.reparentTo(aspect2d)
        self.scoreMult = MinigameGlobals.getScoreMult(self.cr.playGame.hood.id)
        self.__startRewardCountdown()
        self.airborneToons = 0
        self.clockStopTime = None
        self.gameFSM.request('aim')
        return

    def __gameTimerExpired(self):
        self.notify.debug('game timer expired')
        self.gameOver()

    def __playing(self):
        return self.gameFSM.getCurrentState() != self.gameFSM.getFinalState()

    def updateCannonPosition(self, avId, zRot, angle):
        if not self.hasLocalToon:
            return
        if not self.__playing():
            return
        if avId != self.localAvId:
            self.cannonPositionDict[avId] = [zRot, angle]
            self.__updateCannonPosition(avId)

    def setCannonWillFire(self, avId, fireTime, zRot, angle):
        if not self.hasLocalToon:
            return
        if not self.__playing():
            return
        self.notify.debug('setCannonWillFire: ' + str(avId) + ': zRot=' + str(zRot) + ', angle=' + str(angle) + ', time=' + str(fireTime))
        self.cannonPositionDict[avId][0] = zRot
        self.cannonPositionDict[avId][1] = angle
        self.__updateCannonPosition(avId)
        task = Task(self.__fireCannonTask)
        task.avId = avId
        task.fireTime = fireTime
        timeToWait = task.fireTime - self.getCurrentGameTime()
        if timeToWait > 0.0:
            fireTask = Task.sequence(Task.pause(timeToWait), task)
        else:
            fireTask = task
        fireTask = task
        taskMgr.add(fireTask, 'fireCannon' + str(avId))
        self.airborneToons += 1

    def announceToonWillLandInWater(self, avId, landTime):
        if not self.hasLocalToon:
            return
        self.notify.debug('announceToonWillLandInWater: ' + str(avId) + ': time=' + str(landTime))
        if self.clockStopTime == None:
            self.clockStopTime = landTime
        return

    def enterOff(self):
        self.notify.debug('enterOff')

    def exitOff(self):
        pass

    def enterAim(self):
        self.notify.debug('enterAim')
        self.__enableAimInterface()
        self.__putCameraBehindCannon()

    def exitAim(self):
        self.__disableAimInterface()

    def enterShoot(self):
        self.notify.debug('enterShoot')
        self.__broadcastLocalCannonPosition()
        self.sendUpdate('setCannonLit', [self.cannonPositionDict[self.localAvId][0], self.cannonPositionDict[self.localAvId][1]])

    def exitShoot(self):
        pass

    def __somebodyWon(self, avId):
        if avId == self.localAvId:
            base.playSfx(self.sndWin)
        self.__killRewardCountdown()
        self.timer.stop()
        self.gameFSM.request('waitForToonsToLand')

    def enterWaitForToonsToLand(self):
        self.notify.debug('enterWaitForToonsToLand')
        if not self.airborneToons:
            self.gameOver()

    def exitWaitForToonsToLand(self):
        pass

    def enterCleanup(self):
        self.notify.debug('enterCleanup')
        self.music.stop()
        self.__killRewardCountdown()
        if hasattr(self, 'jarIval'):
            self.jarIval.finish()
            del self.jarIval
        for avId in self.avIdList:
            taskMgr.remove('fireCannon' + str(avId))
            taskMgr.remove('flyingToon' + str(avId))

    def exitCleanup(self):
        pass

    def __enableAimInterface(self):
        self.aimPad.show()
        self.accept(self.FIRE_KEY, self.__fireKeyPressed)
        self.accept(self.UP_KEY, self.__upKeyPressed)
        self.accept(self.DOWN_KEY, self.__downKeyPressed)
        self.accept(self.LEFT_KEY, self.__leftKeyPressed)
        self.accept(self.RIGHT_KEY, self.__rightKeyPressed)
        self.__spawnLocalCannonMoveTask()

    def __disableAimInterface(self):
        self.aimPad.hide()
        self.ignore(self.FIRE_KEY)
        self.ignore(self.UP_KEY)
        self.ignore(self.DOWN_KEY)
        self.ignore(self.LEFT_KEY)
        self.ignore(self.RIGHT_KEY)
        self.ignore(self.FIRE_KEY + '-up')
        self.ignore(self.UP_KEY + '-up')
        self.ignore(self.DOWN_KEY + '-up')
        self.ignore(self.LEFT_KEY + '-up')
        self.ignore(self.RIGHT_KEY + '-up')
        self.__killLocalCannonMoveTask()

    def __fireKeyPressed(self):
        self.ignore(self.FIRE_KEY)
        self.accept(self.FIRE_KEY + '-up', self.__fireKeyReleased)
        self.__firePressed()

    def __upKeyPressed(self):
        self.ignore(self.UP_KEY)
        self.accept(self.UP_KEY + '-up', self.__upKeyReleased)
        self.__upPressed()

    def __downKeyPressed(self):
        self.ignore(self.DOWN_KEY)
        self.accept(self.DOWN_KEY + '-up', self.__downKeyReleased)
        self.__downPressed()

    def __leftKeyPressed(self):
        self.ignore(self.LEFT_KEY)
        self.accept(self.LEFT_KEY + '-up', self.__leftKeyReleased)
        self.__leftPressed()

    def __rightKeyPressed(self):
        self.ignore(self.RIGHT_KEY)
        self.accept(self.RIGHT_KEY + '-up', self.__rightKeyReleased)
        self.__rightPressed()

    def __fireKeyReleased(self):
        self.ignore(self.FIRE_KEY + '-up')
        self.accept(self.FIRE_KEY, self.__fireKeyPressed)
        self.__fireReleased()

    def __leftKeyReleased(self):
        self.ignore(self.LEFT_KEY + '-up')
        self.accept(self.LEFT_KEY, self.__leftKeyPressed)
        self.__leftReleased()

    def __rightKeyReleased(self):
        self.ignore(self.RIGHT_KEY + '-up')
        self.accept(self.RIGHT_KEY, self.__rightKeyPressed)
        self.__rightReleased()

    def __upKeyReleased(self):
        self.ignore(self.UP_KEY + '-up')
        self.accept(self.UP_KEY, self.__upKeyPressed)
        self.__upReleased()

    def __downKeyReleased(self):
        self.ignore(self.DOWN_KEY + '-up')
        self.accept(self.DOWN_KEY, self.__downKeyPressed)
        self.__downReleased()

    def __firePressed(self):
        self.notify.debug('fire pressed')
        self.gameFSM.request('shoot')

    def __upPressed(self):
        self.notify.debug('up pressed')
        self.upPressed = self.__enterControlActive(self.upPressed)

    def __downPressed(self):
        self.notify.debug('down pressed')
        self.downPressed = self.__enterControlActive(self.downPressed)

    def __leftPressed(self):
        self.notify.debug('left pressed')
        self.leftPressed = self.__enterControlActive(self.leftPressed)

    def __rightPressed(self):
        self.notify.debug('right pressed')
        self.rightPressed = self.__enterControlActive(self.rightPressed)

    def __upReleased(self):
        self.notify.debug('up released')
        self.upPressed = self.__exitControlActive(self.upPressed)

    def __downReleased(self):
        self.notify.debug('down released')
        self.downPressed = self.__exitControlActive(self.downPressed)

    def __leftReleased(self):
        self.notify.debug('left released')
        self.leftPressed = self.__exitControlActive(self.leftPressed)

    def __rightReleased(self):
        self.notify.debug('right released')
        self.rightPressed = self.__exitControlActive(self.rightPressed)

    def __enterControlActive(self, control):
        return control + 1

    def __exitControlActive(self, control):
        return max(0, control - 1)

    def __spawnLocalCannonMoveTask(self):
        self.leftPressed = 0
        self.rightPressed = 0
        self.upPressed = 0
        self.downPressed = 0
        self.cannonMoving = 0
        task = Task(self.__localCannonMoveTask)
        task.lastPositionBroadcastTime = 0.0
        taskMgr.add(task, self.LOCAL_CANNON_MOVE_TASK)

    def __killLocalCannonMoveTask(self):
        taskMgr.remove(self.LOCAL_CANNON_MOVE_TASK)
        if self.cannonMoving:
            self.sndCannonMove.stop()

    def __localCannonMoveTask(self, task):
        pos = self.cannonPositionDict[self.localAvId]
        oldRot = pos[0]
        oldAng = pos[1]
        rotVel = 0
        if self.leftPressed:
            rotVel += CannonGameGlobals.CANNON_ROTATION_VEL
        if self.rightPressed:
            rotVel -= CannonGameGlobals.CANNON_ROTATION_VEL
        pos[0] += rotVel * globalClock.getDt()
        if pos[0] < CannonGameGlobals.CANNON_ROTATION_MIN:
            pos[0] = CannonGameGlobals.CANNON_ROTATION_MIN
        elif pos[0] > CannonGameGlobals.CANNON_ROTATION_MAX:
            pos[0] = CannonGameGlobals.CANNON_ROTATION_MAX
        angVel = 0
        if self.upPressed:
            angVel += CannonGameGlobals.CANNON_ANGLE_VEL
        if self.downPressed:
            angVel -= CannonGameGlobals.CANNON_ANGLE_VEL
        pos[1] += angVel * globalClock.getDt()
        if pos[1] < CannonGameGlobals.CANNON_ANGLE_MIN:
            pos[1] = CannonGameGlobals.CANNON_ANGLE_MIN
        elif pos[1] > CannonGameGlobals.CANNON_ANGLE_MAX:
            pos[1] = CannonGameGlobals.CANNON_ANGLE_MAX
        if oldRot != pos[0] or oldAng != pos[1]:
            if self.cannonMoving == 0:
                self.cannonMoving = 1
                base.playSfx(self.sndCannonMove, looping=1)
            self.__updateCannonPosition(self.localAvId)
            if task.time - task.lastPositionBroadcastTime > CANNON_MOVE_UPDATE_FREQ:
                task.lastPositionBroadcastTime = task.time
                self.__broadcastLocalCannonPosition()
        elif self.cannonMoving:
            self.cannonMoving = 0
            self.sndCannonMove.stop()
            self.__broadcastLocalCannonPosition()
        return Task.cont

    def __broadcastLocalCannonPosition(self):
        self.sendUpdate('setCannonPosition', [self.cannonPositionDict[self.localAvId][0], self.cannonPositionDict[self.localAvId][1]])

    def __updateCannonPosition(self, avId):
        self.cannonDict[avId][0].setHpr(self.cannonPositionDict[avId][0], 0.0, 0.0)
        self.cannonDict[avId][1].setHpr(0.0, self.cannonPositionDict[avId][1], 0.0)

    def __getCameraPositionBehindCannon(self):
        return Point3(self.cannonLocationDict[self.localAvId][0], CANNON_Y - 25.0, CANNON_Z + 7)

    def __putCameraBehindCannon(self):
        camera.setPos(self.__getCameraPositionBehindCannon())
        camera.setHpr(0, 0, 0)

    def __loadToonInCannon(self, avId):
        self.toonModelDict[avId].detachNode()
        head = self.toonHeadDict[avId]
        head.startBlink()
        head.startLookAround()
        head.reparentTo(self.cannonDict[avId][1])
        head.setPosHpr(0, 6, 0, 0, -45, 0)
        sc = self.toonScaleDict[avId]
        head.setScale(render, sc[0], sc[1], sc[2])

    def __toRadians(self, angle):
        return angle * 2.0 * math.pi / 360.0

    def __toDegrees(self, angle):
        return angle * 360.0 / (2.0 * math.pi)

    def __calcFlightResults(self, avId, launchTime):
        head = self.toonHeadDict[avId]
        startPos = head.getPos(render)
        startHpr = head.getHpr(render)
        hpr = self.cannonDict[avId][1].getHpr(render)
        towerPos = self.tower.getPos(render)
        rotation = self.__toRadians(hpr[0])
        angle = self.__toRadians(hpr[1])
        horizVel = INITIAL_VELOCITY * math.cos(angle)
        xVel = horizVel * -math.sin(rotation)
        yVel = horizVel * math.cos(rotation)
        zVel = INITIAL_VELOCITY * math.sin(angle)
        startVel = Vec3(xVel, yVel, zVel)
        trajectory = Trajectory.Trajectory(launchTime, startPos, startVel)
        towerList = [towerPos + Point3(0, 0, BUCKET_HEIGHT), TOWER_RADIUS, TOWER_HEIGHT - BUCKET_HEIGHT]
        self.notify.debug('calcFlightResults(%s): rotation(%s), angle(%s), horizVel(%s), xVel(%s), yVel(%s), zVel(%s), startVel(%s), trajectory(%s), towerList(%s)' % (avId,
         rotation,
         angle,
         horizVel,
         xVel,
         yVel,
         zVel,
         startVel,
         trajectory,
         towerList))
        timeOfImpact, hitWhat = self.__calcToonImpact(trajectory, towerList)
        return {'startPos': startPos,
         'startHpr': startHpr,
         'startVel': startVel,
         'trajectory': trajectory,
         'timeOfImpact': timeOfImpact,
         'hitWhat': hitWhat}

    def __fireCannonTask(self, task):
        launchTime = task.fireTime
        avId = task.avId
        self.notify.debug('FIRING CANNON FOR AVATAR ' + str(avId))
        flightResults = self.__calcFlightResults(avId, launchTime)
        if not isClient():
            print 'EXECWARNING DistributedCannonGame: %s' % flightResults
            printStack()
        for key in flightResults:
            exec "%s = flightResults['%s']" % (key, key)

        self.notify.debug('start position: ' + str(startPos))
        self.notify.debug('start velocity: ' + str(startVel))
        self.notify.debug('time of launch: ' + str(launchTime))
        self.notify.debug('time of impact: ' + str(timeOfImpact))
        self.notify.debug('location of impact: ' + str(trajectory.getPos(timeOfImpact)))
        if hitWhat == self.HIT_WATER:
            self.notify.debug('toon will land in the water')
        elif hitWhat == self.HIT_TOWER:
            self.notify.debug('toon will hit the tower')
        else:
            self.notify.debug('toon will hit the ground')
        head = self.toonHeadDict[avId]
        head.stopBlink()
        head.stopLookAroundNow()
        head.reparentTo(hidden)
        av = self.toonModelDict[avId]
        av.reparentTo(render)
        av.setPos(startPos)
        av.setHpr(startHpr)
        avatar = self.getAvatar(avId)
        avatar.loop('swim')
        avatar.setPosHpr(0, 0, -(avatar.getHeight() / 2.0), 0, 0, 0)
        shootTask = Task(self.__shootTask)
        flyTask = Task(self.__flyTask)
        seqDoneTask = Task(self.__flySequenceDoneTask)
        info = {}
        info['avId'] = avId
        info['trajectory'] = trajectory
        info['launchTime'] = launchTime
        info['timeOfImpact'] = timeOfImpact
        info['hitWhat'] = hitWhat
        info['toon'] = self.toonModelDict[avId]
        info['hRot'] = self.cannonPositionDict[avId][0]
        info['haveWhistled'] = 0
        info['maxCamPullback'] = CAMERA_PULLBACK_MIN
        info['timeEnterTowerXY'], info['timeExitTowerXY'] = trajectory.calcEnterAndLeaveCylinderXY(self.tower.getPos(render), TOWER_RADIUS)
        shootTask.info = info
        flyTask.info = info
        seqDoneTask.info = info
        seqTask = Task.sequence(shootTask, flyTask, Task.pause(LAND_TIME), seqDoneTask)
        taskMgr.add(seqTask, 'flyingToon' + str(avId))
        if avId == self.localAvId:
            if info['hitWhat'] == self.HIT_WATER:
                self.sendUpdate('setToonWillLandInWater', [info['timeOfImpact']])
        return Task.done

    def __calcToonImpact(self, trajectory, waterTower):
        self.notify.debug('trajectory: %s' % trajectory)
        self.notify.debug('waterTower: %s' % waterTower)
        waterDiscCenter = Point3(waterTower[0])
        waterDiscCenter.setZ(waterDiscCenter[2] + waterTower[2])
        t_waterImpact = trajectory.checkCollisionWithDisc(waterDiscCenter, waterTower[1])
        self.notify.debug('t_waterImpact: %s' % t_waterImpact)
        if t_waterImpact > 0:
            return (t_waterImpact, self.HIT_WATER)
        t_towerImpact = trajectory.checkCollisionWithCylinderSides(waterTower[0], waterTower[1], waterTower[2])
        self.notify.debug('t_towerImpact: %s' % t_towerImpact)
        if t_towerImpact > 0:
            return (t_towerImpact, self.HIT_TOWER)
        t_groundImpact = trajectory.checkCollisionWithGround()
        self.notify.debug('t_groundImpact: %s' % t_groundImpact)
        if t_groundImpact >= trajectory.getStartTime():
            return (t_groundImpact, self.HIT_GROUND)
        else:
            self.notify.error('__calcToonImpact: toon never impacts ground?')
            return (self.startTime, self.HIT_GROUND)

    def __shootTask(self, task):
        base.playSfx(self.sndCannonFire)
        self.dropShadowDict[task.info['avId']].reparentTo(render)
        return Task.done

    def __flyTask(self, task):
        curTime = task.time + task.info['launchTime']
        t = min(curTime, task.info['timeOfImpact'])
        pos = task.info['trajectory'].getPos(t)
        task.info['toon'].setPos(pos)
        shadowPos = Point3(pos)
        if t >= task.info['timeEnterTowerXY'] and t <= task.info['timeExitTowerXY'] and pos[2] >= self.tower.getPos(render)[2] + TOWER_HEIGHT:
            shadowPos.setZ(self.tower.getPos(render)[2] + TOWER_HEIGHT + SHADOW_Z_OFFSET)
        else:
            shadowPos.setZ(SHADOW_Z_OFFSET)
        self.dropShadowDict[task.info['avId']].setPos(shadowPos)
        vel = task.info['trajectory'].getVel(t)
        run = math.sqrt(vel[0] * vel[0] + vel[1] * vel[1])
        rise = vel[2]
        theta = self.__toDegrees(math.atan(rise / run))
        task.info['toon'].setHpr(task.info['hRot'], -90 + theta, 0)
        if task.info['avId'] == self.localAvId:
            lookAt = self.tower.getPos(render)
            lookAt.setZ(lookAt.getZ() - TOWER_HEIGHT / 2.0)
            towerPos = Point3(self.towerPos)
            towerPos.setZ(TOWER_HEIGHT)
            ttVec = Vec3(pos - towerPos)
            toonTowerDist = ttVec.length()
            multiplier = 0.0
            if toonTowerDist < TOON_TOWER_THRESHOLD:
                up = Vec3(0.0, 0.0, 1.0)
                perp = up.cross(vel)
                perp.normalize()
                if ttVec.dot(perp) > 0.0:
                    perp = Vec3(-perp[0], -perp[1], -perp[2])
                a = 1.0 - toonTowerDist / TOON_TOWER_THRESHOLD
                a_2 = a * a
                multiplier = -2.0 * a_2 * a + 3 * a_2
                lookAt = lookAt + perp * (multiplier * MAX_LOOKAT_OFFSET)
            foo = Vec3(pos - lookAt)
            foo.normalize()
            task.info['maxCamPullback'] = max(task.info['maxCamPullback'], CAMERA_PULLBACK_MIN + multiplier * (CAMERA_PULLBACK_MAX - CAMERA_PULLBACK_MIN))
            foo = foo * task.info['maxCamPullback']
            camPos = pos + Point3(foo)
            camera.setPos(camPos)
            camera.lookAt(pos)
        if task.info['haveWhistled'] == 0:
            if -vel[2] > WHISTLE_SPEED:
                if t < task.info['timeOfImpact'] - 0.5:
                    task.info['haveWhistled'] = 1
                    base.playSfx(self.sndWhizz)
        if t == task.info['timeOfImpact']:
            if task.info['haveWhistled']:
                self.sndWhizz.stop()
            self.dropShadowDict[task.info['avId']].reparentTo(hidden)
            avatar = self.getAvatar(task.info['avId'])
            if task.info['hitWhat'] == self.HIT_WATER:
                avatar.loop('neutral')
                self.splash.setPos(task.info['toon'].getPos())
                self.splash.setScale(2)
                self.splash.play()
                base.playSfx(self.sndHitWater)
                task.info['toon'].setHpr(task.info['hRot'], 0, 0)
                self.__somebodyWon(task.info['avId'])
            elif task.info['hitWhat'] == self.HIT_TOWER:
                toon = task.info['toon']
                pos = toon.getPos()
                ttVec = Vec3(pos - self.towerPos)
                ttVec.setZ(0)
                ttVec.normalize()
                h = rad2Deg(math.asin(ttVec[0]))
                toon.setHpr(h, 94, 0)
                deltaZ = TOWER_HEIGHT - BUCKET_HEIGHT
                sf = min(max(pos[2] - BUCKET_HEIGHT, 0), deltaZ) / deltaZ
                hitPos = pos + Point3(ttVec * (0.75 * sf))
                toon.setPos(hitPos)
                hitPos.setZ(hitPos[2] - 1.0)
                s = Sequence(Wait(0.5), toon.posInterval(duration=LAND_TIME - 0.5, pos=hitPos, blendType='easeIn'))
                self.toonIntervalDict[task.info['avId']] = s
                s.start()
                avatar.iPos()
                avatar.pose('slip-forward', 25)
                base.playSfx(self.sndHitTower)
            elif task.info['hitWhat'] == self.HIT_GROUND:
                task.info['toon'].setP(render, -150.0)
                self.dustCloud.setPos(task.info['toon'], 0, 0, -2.5)
                self.dustCloud.setScale(0.35)
                self.dustCloud.play()
                base.playSfx(self.sndHitGround)
                avatar.setPlayRate(2.0, 'run')
                avatar.loop('run')
            return Task.done
        return Task.cont

    def __flySequenceDoneTask(self, task):
        self.airborneToons -= 1
        if self.gameFSM.getCurrentState().getName() == 'waitForToonsToLand':
            if 0 == self.airborneToons:
                self.gameOver()
        else:
            self.__loadToonInCannon(task.info['avId'])
            if task.info['avId'] == self.localAvId:
                self.gameFSM.request('aim')
        return Task.done

    def __startRewardCountdown(self):
        taskMgr.remove(self.REWARD_COUNTDOWN_TASK)
        taskMgr.add(self.__updateRewardCountdown, self.REWARD_COUNTDOWN_TASK)

    def __killRewardCountdown(self):
        taskMgr.remove(self.REWARD_COUNTDOWN_TASK)

    def __updateRewardCountdown(self, task):
        if not hasattr(self, 'rewardPanel'):
            return Task.cont
        curTime = self.getCurrentGameTime()
        if self.clockStopTime is not None:
            if self.clockStopTime < curTime:
                self.__killRewardCountdown()
                curTime = self.clockStopTime
        score = int(self.scoreMult * CannonGameGlobals.calcScore(curTime) + 0.5)
        if not hasattr(task, 'curScore'):
            task.curScore = score
        self.rewardPanel['text'] = str(score)
        if task.curScore != score:
            if hasattr(self, 'jarIval'):
                self.jarIval.finish()
            s = self.rewardPanel.getScale()
            self.jarIval = Parallel(Sequence(self.rewardPanel.scaleInterval(0.15, s * 3.0 / 4.0, blendType='easeOut'), self.rewardPanel.scaleInterval(0.15, s, blendType='easeIn')), SoundInterval(self.sndRewardTick), name='cannonGameRewardJarThrob')
            self.jarIval.start()
        task.curScore = score
        return Task.cont

    def __startIntro(self):
        self.T_WATER = 1
        self.T_WATER2LONGVIEW = 1
        self.T_LONGVIEW = 1
        self.T_LONGVIEW2TOONHEAD = 2
        self.T_TOONHEAD = 2
        self.T_TOONHEAD2CANNONBACK = 2
        taskLookInWater = Task(self.__taskLookInWater)
        taskPullBackFromWater = Task(self.__taskPullBackFromWater)
        taskFlyUpToToon = Task(self.__flyUpToToon)
        taskFlyToBackOfCannon = Task(self.__flyToBackOfCannon)
        commonData = {}
        taskLookInWater.data = commonData
        taskPullBackFromWater.data = commonData
        taskFlyUpToToon.data = commonData
        taskFlyToBackOfCannon.data = commonData
        introTask = Task.sequence(taskLookInWater, Task.pause(self.T_WATER), taskPullBackFromWater, Task.pause(self.T_WATER2LONGVIEW + self.T_LONGVIEW), taskFlyUpToToon, Task.pause(self.T_LONGVIEW2TOONHEAD + self.T_TOONHEAD), taskFlyToBackOfCannon)
        taskMgr.add(introTask, self.INTRO_TASK_NAME)

    def __stopIntro(self):
        taskMgr.remove(self.INTRO_TASK_NAME)
        taskMgr.remove(self.INTRO_TASK_NAME_CAMERA_LERP)
        camera.wrtReparentTo(render)

    def __spawnCameraLookAtLerp(self, targetPos, targetLookAt, duration):
        oldPos = camera.getPos()
        oldHpr = camera.getHpr()
        camera.setPos(targetPos)
        camera.lookAt(targetLookAt)
        targetHpr = camera.getHpr()
        camera.setPos(oldPos)
        camera.setHpr(oldHpr)
        camera.lerpPosHpr(Point3(targetPos), targetHpr, duration, blendType='easeInOut', task=self.INTRO_TASK_NAME_CAMERA_LERP)

    def __taskLookInWater(self, task):
        task.data['cannonCenter'] = Point3(0, CANNON_Y, CANNON_Z)
        task.data['towerWaterCenter'] = Point3(self.towerPos + Point3(0, 0, TOWER_HEIGHT))
        task.data['vecTowerToCannon'] = Point3(task.data['cannonCenter'] - task.data['towerWaterCenter'])
        vecAwayFromCannons = Vec3(Point3(0, 0, 0) - task.data['vecTowerToCannon'])
        vecAwayFromCannons.setZ(0.0)
        vecAwayFromCannons.normalize()
        camLoc = Point3(vecAwayFromCannons * 20) + Point3(0, 0, 20)
        camLoc = camLoc + task.data['towerWaterCenter']
        camera.setPos(camLoc)
        camera.lookAt(task.data['towerWaterCenter'])
        task.data['vecAwayFromCannons'] = vecAwayFromCannons
        return Task.done

    def __taskPullBackFromWater(self, task):
        camLoc = Point3(task.data['vecAwayFromCannons'] * 40) + Point3(0, 0, 20)
        camLoc = camLoc + task.data['towerWaterCenter']
        lookAt = task.data['cannonCenter']
        self.__spawnCameraLookAtLerp(camLoc, lookAt, self.T_WATER2LONGVIEW)
        return Task.done

    def __flyUpToToon(self, task):
        headPos = self.toonHeadDict[self.localAvId].getPos(render)
        camLoc = headPos + Point3(0, 5, 0)
        lookAt = Point3(headPos)
        self.__spawnCameraLookAtLerp(camLoc, lookAt, self.T_LONGVIEW2TOONHEAD)
        return Task.done

    def __flyToBackOfCannon(self, task):
        lerpNode = hidden.attachNewNode('CannonGameCameraLerpNode')
        lerpNode.reparentTo(render)
        lerpNode.setPos(self.cannonLocationDict[self.localAvId] + Point3(0, 1, 0))
        relCamPos = camera.getPos(lerpNode)
        relCamHpr = camera.getHpr(lerpNode)
        startRotation = lerpNode.getHpr()
        endRotation = Point3(-180, 0, 0)
        lerpNode.setHpr(endRotation)
        camera.setPos(self.__getCameraPositionBehindCannon())
        endPos = camera.getPos(lerpNode)
        lerpNode.setHpr(startRotation)
        camera.reparentTo(lerpNode)
        camera.setPos(relCamPos)
        camera.setHpr(relCamHpr)
        lerpNode.lerpHpr(endRotation, self.T_TOONHEAD2CANNONBACK, blendType='easeInOut', task=self.INTRO_TASK_NAME_CAMERA_LERP)
        camera.lerpPos(endPos, self.T_TOONHEAD2CANNONBACK, blendType='easeInOut', task=self.INTRO_TASK_NAME_CAMERA_LERP)
        return Task.done
