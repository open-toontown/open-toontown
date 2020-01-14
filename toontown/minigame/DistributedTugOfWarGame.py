from pandac.PandaModules import *
from toontown.toonbase.ToonBaseGlobal import *
from direct.interval.IntervalGlobal import *
from .DistributedMinigame import *
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from toontown.toonbase import ToontownTimer
from toontown.toon import ToonHead
from toontown.suit import SuitDNA
from toontown.suit import Suit
from toontown.char import Char
from . import ArrowKeys
import random
from toontown.toonbase import ToontownGlobals
import string
from toontown.toonbase import TTLocalizer
from . import TugOfWarGameGlobals
from direct.showutil import Rope
from toontown.effects import Splash
from toontown.effects import Ripples
from toontown.toonbase import TTLocalizer
from . import MinigamePowerMeter
from direct.task.Task import Task

class DistributedTugOfWarGame(DistributedMinigame):
    bgm = 'phase_4/audio/bgm/MG_tug_o_war.ogg'
    toonAnimNames = ['neutral',
     'tug-o-war',
     'slip-forward',
     'slip-backward',
     'victory',
     'sad-neutral']
    suitAnimNames = ['neutral',
     'tug-o-war',
     'slip-forward',
     'slip-backward',
     'flail',
     'victory']
    UPDATE_TIMER_TASK = 'TugOfWarGameUpdateTimerTask'
    UPDATE_KEY_PRESS_RATE_TASK = 'TugOfWarGameUpdateKeyPressRateTask'
    UPDATE_ROPE_TASK = 'TugOfWarGameUpdateRopeTask'
    H_TO_L = 0
    L_TO_H = 1

    def __init__(self, cr):
        DistributedMinigame.__init__(self, cr)
        self.gameFSM = ClassicFSM.ClassicFSM('DistributedTugOfWarGame', [State.State('off', self.enterOff, self.exitOff, ['waitForGoSignal']),
         State.State('waitForGoSignal', self.enterWaitForGoSignal, self.exitWaitForGoSignal, ['tug', 'cleanup']),
         State.State('tug', self.enterTug, self.exitTug, ['gameDone', 'cleanup']),
         State.State('gameDone', self.enterGameDone, self.exitGameDone, ['cleanup']),
         State.State('cleanup', self.enterCleanup, self.exitCleanup, [])], 'off', 'cleanup')
        self.addChildGameFSM(self.gameFSM)
        self.gameType = TugOfWarGameGlobals.TOON_VS_TOON
        self.suit = None
        self.suitId = 666
        self.suitType = 'f'
        self.suitLevel = 1
        self.sides = {}
        self.avList = [[], []]
        self.buttons = [0, 1]
        self.mouseMode = 0
        self.mouseSide = 0
        self.fallenList = []
        self.handycap = 2.0
        self.advantage = 1.0
        self.tugRopes = []
        self.ropePts = []
        self.ropeTex = []
        self.rightHandDict = {}
        self.posDict = {}
        self.hprDict = {}
        self.offsetDict = {}
        self.pullingDict = {}
        self.dropShadowDict = {}
        self.arrowKeys = None
        self.keyTTL = []
        self.idealRate = 2.0
        self.idealForce = 0.0
        self.keyRate = 0
        self.allOutMode = 0
        self.rateMatchAward = 0
        self.targetRateList = [[8, 6],
         [5, 7],
         [6, 8],
         [6, 10],
         [7, 11],
         [8, 12]]
        self.nextRateIndex = 0
        self.drinkPositions = []
        for k in range(4):
            self.drinkPositions.append(VBase3(-.2 + 0.2 * k, 16 + 2 * k, 0.0))

        self.rng = RandomNumGen.RandomNumGen(1000)
        self.introTrack = None
        self.showTrack = None
        self.setupTrack = None
        self.animTracks = {}
        self.randomNumGen = None
        return

    def getTitle(self):
        return TTLocalizer.TugOfWarGameTitle

    def getInstructions(self):
        return TTLocalizer.TugOfWarInstructions

    def getMaxDuration(self):
        return TugOfWarGameGlobals.GAME_DURATION

    def load(self):
        self.notify.debug('load')
        DistributedMinigame.load(self)
        self.timer = ToontownTimer.ToontownTimer()
        self.timer.posInTopRightCorner()
        self.timer.hide()
        self.room = loader.loadModel('phase_4/models/minigames/tug_of_war_dock')
        self.room.reparentTo(hidden)
        ropeModel = loader.loadModel('phase_4/models/minigames/tug_of_war_rope')
        self.ropeTexture = ropeModel.findTexture('*')
        ropeModel.removeNode()
        self.sky = loader.loadModel('phase_3.5/models/props/TT_sky')
        self.dropShadow = loader.loadModel('phase_3/models/props/drop_shadow')
        self.correctSound = base.loader.loadSfx('phase_4/audio/sfx/MG_pos_buzzer.ogg')
        self.sndHitWater = base.loader.loadSfx('phase_4/audio/sfx/MG_cannon_splash.ogg')
        self.whistleSound = base.loader.loadSfx('phase_4/audio/sfx/AA_sound_whistle.ogg')
        self.music = base.loader.loadMusic(self.bgm)
        self.roundText = DirectLabel(text='     ', text_fg=(0, 1, 0, 1), frameColor=(1, 1, 1, 0), text_font=ToontownGlobals.getSignFont(), pos=(0.014, 0, -.84), scale=0.2)
        self.powerMeter = MinigamePowerMeter.MinigamePowerMeter(17)
        self.powerMeter.reparentTo(aspect2d)
        self.powerMeter.setPos(0, 0, 0.4)
        self.powerMeter.setPower(8)
        self.powerMeter.setTarget(8)
        self.arrows = [None] * 2
        for x in range(len(self.arrows)):
            self.arrows[x] = loader.loadModel('phase_3/models/props/arrow')
            self.arrows[x].reparentTo(self.powerMeter)
            self.arrows[x].hide()
            self.arrows[x].setScale(0.2 - 0.4 * x, 0.2, 0.2)
            self.arrows[x].setPos(0.12 - 0.24 * x, 0, -.26)
            self.disableArrow(self.arrows[x])

        self.splash = Splash.Splash(render)
        self.suitSplash = Splash.Splash(render)
        self.ripples = Ripples.Ripples(render)
        self.suitRipples = Ripples.Ripples(render)
        return

    def toggleMouseMode(self, param):
        self.mouseMode = not self.mouseMode
        if self.mouseMode:
            mpos = param.getMouse()
            if mpos[0] < 0:
                self.hilightArrow(self.arrows[1])
            else:
                self.hilightArrow(self.arrows[0])
            self.__spawnMouseSpeedTask()
        else:
            self.__releaseHandler(0)
            self.__releaseHandler(1)
            self.__killMouseSpeedTask()

    def unload(self):
        self.notify.debug('unload')
        DistributedMinigame.unload(self)
        del self.lt
        self.timer.destroy()
        del self.timer
        self.room.removeNode()
        del self.room
        self.sky.removeNode()
        del self.sky
        del self.dropShadowDict
        self.dropShadow.removeNode()
        del self.dropShadow
        del self.correctSound
        del self.sndHitWater
        del self.whistleSound
        del self.music
        self.roundText.destroy()
        del self.roundText
        if self.powerMeter:
            self.powerMeter.destroy()
            del self.powerMeter
        for x in self.arrows:
            if x:
                x.removeNode()
                del x

        del self.arrows
        self.splash.destroy()
        del self.splash
        self.suitSplash.destroy()
        del self.suitSplash
        if self.ripples != None:
            self.ripples.stop()
            self.ripples.detachNode()
            del self.ripples
        if self.suitRipples != None:
            self.suitRipples.stop()
            self.suitRipples.detachNode()
            del self.suitRipples
        for x in self.avList:
            del x

        del self.avList
        for x in self.tugRopes:
            if x != None:
                x.detachNode()
            del x

        del self.tugRopes
        for x in self.ropePts:
            if x:
                for t in x:
                    del t

                del x

        del self.ropePts
        for x in self.ropeTex:
            if x:
                for t in x:
                    t.destroy()
                    del t

                del x

        del self.ropeTex
        del self.posDict
        del self.hprDict
        self.removeChildGameFSM(self.gameFSM)
        del self.gameFSM
        if self.suit:
            self.suit.delete()
            del self.suit
        del self.sides
        del self.buttons
        del self.pullingDict
        del self.rightHandDict
        for x in self.drinkPositions:
            del x

        del self.drinkPositions
        del self.offsetDict
        del self.keyTTL
        del self.rng
        return

    def onstage(self):
        self.notify.debug('onstage')
        DistributedMinigame.onstage(self)
        self.lt = base.localAvatar
        NametagGlobals.setGlobalNametagScale(1)
        self.arrowKeys = ArrowKeys.ArrowKeys()
        self.room.reparentTo(render)
        self.room.setPosHpr(0.0, 18.39, -ToontownGlobals.FloorOffset, 0.0, 0.0, 0.0)
        self.room.setScale(0.4)
        self.sky.setZ(-5)
        self.sky.reparentTo(render)
        self.dropShadow.setColor(0, 0, 0, 0.5)
        camera.reparentTo(render)
        camera.setPosHpr(-11.4427, 9.03559, 2.80094, -49.104, -0.89, 0)
        self.dropShadow.setBin('fixed', 0, 1)
        self.splash.reparentTo(render)
        self.suitSplash.reparentTo(render)
        base.playMusic(self.music, looping=1, volume=1)
        for x in range(len(self.arrows)):
            self.arrows[x].show()

        for avId in self.avIdList:
            self.pullingDict[avId] = 0

    def offstage(self):
        self.notify.debug('offstage')
        DistributedMinigame.offstage(self)
        self.music.stop()
        if self.introTrack:
            self.introTrack.finish()
            del self.introTrack
            self.introTrack = None
        for track in list(self.animTracks.values()):
            if track:
                track.finish()
                del track
            self.animTracks = {}

        if self.showTrack:
            self.showTrack.finish()
            del self.showTrack
            self.showTrack = None
        if self.setupTrack:
            self.setupTrack.finish()
            del self.setupTrack
            self.setupTrack = None
        base.camLens.setFov(ToontownGlobals.DefaultCameraFov)
        base.camLens.setNearFar(ToontownGlobals.DefaultCameraNear, ToontownGlobals.DefaultCameraFar)
        NametagGlobals.setGlobalNametagScale(1.0)
        if self.arrowKeys:
            self.arrowKeys.setPressHandlers(self.arrowKeys.NULL_HANDLERS)
            self.arrowKeys.setReleaseHandlers(self.arrowKeys.NULL_HANDLERS)
            self.arrowKeys.destroy()
            del self.arrowKeys
            self.arrowKeys = None
        self.room.reparentTo(hidden)
        self.sky.reparentTo(hidden)
        self.splash.reparentTo(hidden)
        self.splash.stop()
        self.suitSplash.reparentTo(hidden)
        self.suitSplash.stop()
        self.ripples.reparentTo(hidden)
        self.ripples.stop()
        self.hideControls()
        self.roundText.hide()
        for avId in self.avIdList:
            av = self.getAvatar(avId)
            if av:
                av.loop('neutral')
                av.resetLOD()
                av.dropShadow.show()

        for x in self.tugRopes:
            if x != None:
                x.reparentTo(hidden)

        if self.suit:
            self.suit.reparentTo(hidden)
        for avId in self.avIdList:
            if avId in self.dropShadowDict:
                self.dropShadowDict[avId].reparentTo(hidden)

        if self.suitId in self.dropShadowDict:
            self.dropShadowDict[self.suitId].reparentTo(hidden)
        return

    def initCamera(self):
        birdseyePosHpr = [1.95461,
         18.4891,
         38.4646,
         1.18185,
         -87.5308,
         0]
        introPosHpr = [None] * 2
        introPosHpr[0] = [VBase3(-11.4427, 9.03559, 2.80094), VBase3(-49.104, -0.732374, 0)]
        introPosHpr[1] = [VBase3(16.9291, 13.9302, 2.64282), VBase3(66.9685, -6.195, 0)]
        gameCamHpr = VBase3(-1.13, 1.042, 0)
        gameCamPos = VBase3(0, 1.0838, 2.745)
        camera.reparentTo(render)
        camera.setPosHpr(introPosHpr[self.sides[self.localAvId]][0], introPosHpr[self.sides[self.localAvId]][1])
        lerpDur = 8
        self.introTrack = LerpPosHprInterval(camera, lerpDur, pos=gameCamPos, hpr=gameCamHpr, blendType='easeInOut', name=self.uniqueName('introLerpCameraPos'))
        self.introTrack.start()
        base.camLens.setFov(60 + 2 * self.numPlayers)
        base.camLens.setFar(450.0)
        return

    def sendGameType(self, index, suit):
        if not self.hasLocalToon:
            return
        self.gameType = index
        self.suitLevel = suit
        if suit == 1:
            self.suitType = 'pp'
        elif suit == 2:
            self.suitType = 'dt'
        elif suit == 3:
            self.suitType = 'gh'
        elif suit == 4:
            self.suitType = 'cr'

    def setGameReady(self):
        if not self.hasLocalToon:
            return
        self.notify.debug('setGameReady')
        if DistributedMinigame.setGameReady(self):
            return
        self.initToons()
        self.createSuits()
        self.calculatePositions()
        self.initHandycaps()
        self.initRopes()
        self.initCamera()
        self.animTracks = {}
        for avId in self.avIdList:
            self.animTracks[avId] = None

        self.animTracks[self.suitId] = None
        self.showTrack = None
        self.setupTrack = None
        self.__initGameVars()
        return

    def hideControls(self):
        for x in range(len(self.arrows)):
            self.arrows[x].hide()

        for rope in self.tugRopes:
            if rope != None:
                rope.reparentTo(hidden)

        for tex in self.ropeTex:
            if tex != None:
                for texi in tex:
                    if texi:
                        texi.reparentTo(hidden)

        if self.powerMeter != None:
            self.powerMeter.unbind(DGG.B1PRESS)
            self.powerMeter.unbind(DGG.B1RELEASE)
            self.powerMeter.hide()
        return

    def setUpRopes(self, notTaut):
        if self.numPlayers == 1:
            suitRightHand = self.suit.getRightHand()
            toonRightHand = self.rightHandDict[self.avIdList[0]]
            if notTaut:
                self.tugRopes[0].setup(3, ((toonRightHand, (0, 0, 0)), (render, (0, 18, -1)), (suitRightHand, (0, 0, 0))), [0,
                 0,
                 0,
                 1,
                 1,
                 1])
            else:
                midPt = (suitRightHand.getPos() - toonRightHand.getPos()) / 2.0
                self.tugRopes[0].setup(3, ((toonRightHand, (0, 0, 0)), (toonRightHand, (0, 0, 0)), (suitRightHand, (0, 0, 0))), [0,
                 0,
                 0,
                 1,
                 1,
                 1])
            self.tugRopes[0].reparentTo(render)
        elif self.numPlayers == 2:
            if self.gameType == TugOfWarGameGlobals.TOON_VS_COG:
                self.tugRopes[0].setup(3, ((self.rightHandDict[self.avIdList[0]], (0, 0, 0)), (self.rightHandDict[self.avIdList[0]], (0, 0, 0)), (self.rightHandDict[self.avIdList[1]], (0, 0, 0))), [0,
                 0,
                 0,
                 1,
                 1,
                 1])
                suitRightHand = self.suit.getRightHand()
                toonRightHand = self.rightHandDict[self.avIdList[1]]
                if notTaut:
                    self.tugRopes[1].setup(3, ((toonRightHand, (0, 0, 0)), (render, (0, 18, -1)), (suitRightHand, (0, 0, 0))), [0,
                     0,
                     0,
                     1,
                     1,
                     1])
                else:
                    midPt = (suitRightHand.getPos() - toonRightHand.getPos()) / 2.0
                    self.tugRopes[1].setup(3, ((toonRightHand, (0, 0, 0)), (toonRightHand, (0, 0, 0)), (suitRightHand, (0, 0, 0))), [0,
                     0,
                     0,
                     1,
                     1,
                     1])
                self.tugRopes[0].reparentTo(render)
                self.tugRopes[1].reparentTo(render)
            else:
                if notTaut:
                    self.tugRopes[0].setup(3, ((self.rightHandDict[self.avIdList[0]], (0, 0, 0)), (render, (0, 18, -1)), (self.rightHandDict[self.avIdList[1]], (0, 0, 0))), [0,
                     0,
                     0,
                     1,
                     1,
                     1])
                else:
                    self.tugRopes[0].setup(3, ((self.rightHandDict[self.avIdList[0]], (0, 0, 0)), (self.rightHandDict[self.avIdList[0]], (0, 0, 0)), (self.rightHandDict[self.avIdList[1]], (0, 0, 0))), [0,
                     0,
                     0,
                     1,
                     1,
                     1])
                self.tugRopes[0].reparentTo(render)
        elif self.numPlayers == 3:
            if self.gameType == TugOfWarGameGlobals.TOON_VS_COG:
                self.tugRopes[1].setup(3, ((self.rightHandDict[self.avIdList[1]], (0, 0, 0)), (self.rightHandDict[self.avIdList[1]], (0, 0, 0)), (self.rightHandDict[self.avIdList[2]], (0, 0, 0))), [0,
                 0,
                 0,
                 1,
                 1,
                 1])
                self.tugRopes[0].setup(3, ((self.rightHandDict[self.avIdList[0]], (0, 0, 0)), (self.rightHandDict[self.avIdList[0]], (0, 0, 0)), (self.rightHandDict[self.avIdList[1]], (0, 0, 0))), [0,
                 0,
                 0,
                 1,
                 1,
                 1])
                suitRightHand = self.suit.getRightHand()
                toonRightHand = self.rightHandDict[self.avIdList[2]]
                if notTaut:
                    self.tugRopes[2].setup(3, ((toonRightHand, (0, 0, 0)), (render, (0, 18, -1)), (suitRightHand, (0, 0, 0))), [0,
                     0,
                     0,
                     1,
                     1,
                     1])
                else:
                    midPt = (suitRightHand.getPos() - toonRightHand.getPos()) / 2.0
                    self.tugRopes[2].setup(3, ((toonRightHand, (0, 0, 0)), (toonRightHand, (0, 0, 0)), (suitRightHand, (0, 0, 0))), [0,
                     0,
                     0,
                     1,
                     1,
                     1])
                self.tugRopes[0].reparentTo(render)
                self.tugRopes[1].reparentTo(render)
                self.tugRopes[2].reparentTo(render)
            else:
                if notTaut:
                    self.tugRopes[1].setup(3, ((self.rightHandDict[self.avIdList[1]], (0, 0, 0)), (render, (0, 18, -1)), (self.rightHandDict[self.avIdList[2]], (0, 0, 0))), [0,
                     0,
                     0,
                     1,
                     1,
                     1])
                else:
                    self.tugRopes[1].setup(3, ((self.rightHandDict[self.avIdList[1]], (0, 0, 0)), (self.rightHandDict[self.avIdList[1]], (0, 0, 0)), (self.rightHandDict[self.avIdList[2]], (0, 0, 0))), [0,
                     0,
                     0,
                     1,
                     1,
                     1])
                self.tugRopes[0].setup(3, ((self.rightHandDict[self.avIdList[0]], (0, 0, 0)), (self.rightHandDict[self.avIdList[0]], (0, 0, 0)), (self.rightHandDict[self.avIdList[1]], (0, 0, 0))), [0,
                 0,
                 0,
                 1,
                 1,
                 1])
                self.tugRopes[0].reparentTo(render)
                self.tugRopes[1].reparentTo(render)
        elif self.numPlayers == 4:
            if self.gameType == TugOfWarGameGlobals.TOON_VS_COG:
                self.tugRopes[2].setup(3, ((self.rightHandDict[self.avIdList[2]], (0, 0, 0)), (self.rightHandDict[self.avIdList[2]], (0, 0, 0)), (self.rightHandDict[self.avIdList[3]], (0, 0, 0))), [0,
                 0,
                 0,
                 1,
                 1,
                 1])
                self.tugRopes[1].setup(3, ((self.rightHandDict[self.avIdList[1]], (0, 0, 0)), (self.rightHandDict[self.avIdList[1]], (0, 0, 0)), (self.rightHandDict[self.avIdList[2]], (0, 0, 0))), [0,
                 0,
                 0,
                 1,
                 1,
                 1])
                self.tugRopes[0].setup(3, ((self.rightHandDict[self.avIdList[0]], (0, 0, 0)), (self.rightHandDict[self.avIdList[0]], (0, 0, 0)), (self.rightHandDict[self.avIdList[1]], (0, 0, 0))), [0,
                 0,
                 0,
                 1,
                 1,
                 1])
                suitRightHand = self.suit.getRightHand()
                toonRightHand = self.rightHandDict[self.avIdList[3]]
                if notTaut:
                    self.tugRopes[3].setup(3, ((toonRightHand, (0, 0, 0)), (render, (0, 18, -1)), (suitRightHand, (0, 0, 0))), [0,
                     0,
                     0,
                     1,
                     1,
                     1])
                else:
                    midPt = (suitRightHand.getPos() - toonRightHand.getPos()) / 2.0
                    self.tugRopes[3].setup(3, ((toonRightHand, (0, 0, 0)), (toonRightHand, (0, 0, 0)), (suitRightHand, (0, 0, 0))), [0,
                     0,
                     0,
                     1,
                     1,
                     1])
                self.tugRopes[0].reparentTo(render)
                self.tugRopes[1].reparentTo(render)
                self.tugRopes[2].reparentTo(render)
                self.tugRopes[3].reparentTo(render)
            else:
                self.tugRopes[2].setup(3, ((self.rightHandDict[self.avIdList[2]], (0, 0, 0)), (self.rightHandDict[self.avIdList[2]], (0, 0, 0)), (self.rightHandDict[self.avIdList[3]], (0, 0, 0))), [0,
                 0,
                 0,
                 1,
                 1,
                 1])
                self.tugRopes[0].setup(3, ((self.rightHandDict[self.avIdList[0]], (0, 0, 0)), (self.rightHandDict[self.avIdList[0]], (0, 0, 0)), (self.rightHandDict[self.avIdList[1]], (0, 0, 0))), [0,
                 0,
                 0,
                 1,
                 1,
                 1])
                if notTaut:
                    self.tugRopes[1].setup(3, ((self.rightHandDict[self.avIdList[1]], (0, 0, 0)), (render, (0, 18, -1)), (self.rightHandDict[self.avIdList[2]], (0, 0, 0))), [0,
                     0,
                     0,
                     1,
                     1,
                     1])
                else:
                    self.tugRopes[1].setup(3, ((self.rightHandDict[self.avIdList[1]], (0, 0, 0)), (self.rightHandDict[self.avIdList[1]], (0, 0, 0)), (self.rightHandDict[self.avIdList[2]], (0, 0, 0))), [0,
                     0,
                     0,
                     1,
                     1,
                     1])
                self.tugRopes[0].reparentTo(render)
                self.tugRopes[1].reparentTo(render)
                self.tugRopes[2].reparentTo(render)

    def initToons(self):
        for avId in self.avIdList:
            toon = self.getAvatar(avId)
            if toon:
                toon.reparentTo(render)
                toon.useLOD(1000)
                toon.startBlink()
                toon.startLookAround()
                for anim in self.toonAnimNames:
                    toon.pose(anim, 0)

                toon.pose('tug-o-war', 3)
                self.rightHandDict[avId] = toon.getRightHands()[0]
                toon.loop('neutral')
                toon.dropShadow.hide()
                self.dropShadowDict[avId] = self.dropShadow.copyTo(hidden)
                self.dropShadowDict[avId].reparentTo(toon)
                self.dropShadowDict[avId].setScale(0.35)

    def calculatePositions(self):
        hprPositions = [VBase3(240, 0, 0), VBase3(120, 0, 0)]
        dockPositions = []
        for k in range(5):
            dockPositions.append(VBase3(-9.0 + 1.5 * k, 18, 0.1))

        for k in range(5):
            dockPositions.append(VBase3(3 + 1.5 * k, 18, 0.1))

        self.sendUpdate('sendNewAvIdList', [self.avIdList])
        if self.numPlayers == 1:
            if self.gameType == TugOfWarGameGlobals.TOON_VS_COG:
                self.posDict[self.suitId] = dockPositions[7]
                self.posDict[self.avIdList[0]] = dockPositions[2]
                self.hprDict[self.avIdList[0]] = hprPositions[0]
            else:
                self.notify.warning("can't play toon vs. toon with one player")
        elif self.numPlayers == 2:
            if self.gameType == TugOfWarGameGlobals.TOON_VS_COG:
                self.arrangeByHeight(self.avIdList, self.H_TO_L, 0, 1)
                self.posDict[self.suitId] = dockPositions[7]
                self.posDict[self.avIdList[0]] = dockPositions[1]
                self.posDict[self.avIdList[1]] = dockPositions[2]
                self.hprDict[self.avIdList[0]] = hprPositions[0]
                self.hprDict[self.avIdList[1]] = hprPositions[0]
            else:
                self.randomNumGen.shuffle(self.avIdList)
                self.posDict[self.avIdList[0]] = dockPositions[2]
                self.posDict[self.avIdList[1]] = dockPositions[7]
                self.hprDict[self.avIdList[0]] = hprPositions[0]
                self.hprDict[self.avIdList[1]] = hprPositions[1]
        elif self.numPlayers == 3:
            if self.gameType == TugOfWarGameGlobals.TOON_VS_COG:
                self.arrangeByHeight(self.avIdList, self.H_TO_L, 0, 2)
                self.posDict[self.suitId] = dockPositions[7]
                self.posDict[self.avIdList[0]] = dockPositions[0]
                self.posDict[self.avIdList[1]] = dockPositions[1]
                self.posDict[self.avIdList[2]] = dockPositions[2]
                self.hprDict[self.avIdList[0]] = hprPositions[0]
                self.hprDict[self.avIdList[1]] = hprPositions[0]
                self.hprDict[self.avIdList[2]] = hprPositions[0]
            else:
                self.randomNumGen.shuffle(self.avIdList)
                self.arrangeByHeight(self.avIdList, self.H_TO_L, 0, 1)
                self.posDict[self.avIdList[0]] = dockPositions[1]
                self.posDict[self.avIdList[1]] = dockPositions[2]
                self.posDict[self.avIdList[2]] = dockPositions[7]
                self.hprDict[self.avIdList[0]] = hprPositions[0]
                self.hprDict[self.avIdList[1]] = hprPositions[0]
                self.hprDict[self.avIdList[2]] = hprPositions[1]
        elif self.numPlayers == 4:
            if self.gameType == TugOfWarGameGlobals.TOON_VS_COG:
                self.arrangeByHeight(self.avIdList, self.H_TO_L, 0, 3)
                self.posDict[self.suitId] = dockPositions[6]
                self.posDict[self.avIdList[0]] = dockPositions[0]
                self.posDict[self.avIdList[1]] = dockPositions[1]
                self.posDict[self.avIdList[2]] = dockPositions[2]
                self.posDict[self.avIdList[3]] = dockPositions[3]
                self.hprDict[self.avIdList[0]] = hprPositions[0]
                self.hprDict[self.avIdList[1]] = hprPositions[0]
                self.hprDict[self.avIdList[2]] = hprPositions[0]
                self.hprDict[self.avIdList[3]] = hprPositions[0]
            else:
                self.randomNumGen.shuffle(self.avIdList)
                self.arrangeByHeight(self.avIdList, self.H_TO_L, 0, 1)
                self.arrangeByHeight(self.avIdList, self.L_TO_H, 2, 3)
                self.posDict[self.avIdList[0]] = dockPositions[1]
                self.posDict[self.avIdList[1]] = dockPositions[2]
                self.posDict[self.avIdList[2]] = dockPositions[7]
                self.posDict[self.avIdList[3]] = dockPositions[8]
                self.hprDict[self.avIdList[0]] = hprPositions[0]
                self.hprDict[self.avIdList[1]] = hprPositions[0]
                self.hprDict[self.avIdList[2]] = hprPositions[1]
                self.hprDict[self.avIdList[3]] = hprPositions[1]
        for x in self.avIdList:
            self.offsetDict[x] = 0
            if self.posDict[x][0] < 0:
                self.sides[x] = 0
                self.avList[0].append(x)
            else:
                self.sides[x] = 1
                self.avList[1].append(x)

        for avId in self.avIdList:
            toon = self.getAvatar(avId)
            toon.setPos(self.posDict[avId])
            toon.setHpr(self.hprDict[avId])

    def arrangeByHeight(self, avIdList, order, iStart, iFin):
        for i in range(iStart, iFin + 1):
            for j in range(i + 1, iFin + 1):
                if order == self.H_TO_L and self.rightHandDict[avIdList[i]].getZ() < self.rightHandDict[avIdList[j]].getZ() or order == self.L_TO_H and self.rightHandDict[avIdList[i]].getZ() > self.rightHandDict[avIdList[j]].getZ():
                    temp = avIdList[i]
                    avIdList[i] = avIdList[j]
                    avIdList[j] = temp

    def disableArrow(self, a):
        a.setColor(1, 0, 0, 0.3)

    def enableArrow(self, a):
        a.setColor(1, 0, 0, 1)

    def hilightArrow(self, a):
        a.setColor(1, 0.7, 0, 1)

    def unhilightArrow(self, a):
        self.enableArrow(a)

    def handleDisabledAvatar(self, avId):
        self.notify.debug('handleDisabledAvatar')
        self.notify.debug('avatar ' + str(avId) + ' disabled')
        DistributedMinigame.handleDisabledAvatar(self, avId)

    def __playing(self):
        return self.gameFSM.getCurrentState() != self.gameFSM.getFinalState()

    def setGameStart(self, timestamp):
        if not self.hasLocalToon:
            return
        self.notify.debug('setGameStart')
        if not self.__playing():
            return
        DistributedMinigame.setGameStart(self, timestamp)
        self.gameFSM.request('waitForGoSignal')

    def __initGameVars(self):
        pass

    def makeToonLookatCamera(self, toon):
        toon.headsUp(camera)

    def setText(self, t, newtext):
        t['text'] = newtext

    def setTextFG(self, t, fg):
        t['text_fg'] = fg

    def enterOff(self):
        self.notify.debug('enterOff')

    def exitOff(self):
        pass

    def enterWaitForGoSignal(self):
        self.notify.debug('enterWaitForGoSignal')
        self.powerMeter.show()
        self.sendUpdate('reportPlayerReady', [self.sides[self.localAvId]])
        self.roundText.show()
        taskMgr.doMethodLater(TugOfWarGameGlobals.WAIT_FOR_GO_TIMEOUT, self.waitForGoTimeoutTask, self.taskName('wait-for-go-timeout'))

    def exitWaitForGoSignal(self):
        taskMgr.remove(self.taskName('wait-for-go-timeout'))

    def enterTug(self):
        self.notify.debug('enterTug')
        self.__spawnUpdateIdealRateTask()
        self.__spawnUpdateTimerTask()
        self.__spawnUpdateKeyPressRateTask()
        taskMgr.doMethodLater(TugOfWarGameGlobals.TUG_TIMEOUT, self.tugTimeoutTask, self.taskName('tug-timeout'))
        if self.suit:
            self.suit.loop('tug-o-war')

    def exitTug(self):
        self.notify.debug('exitTug')
        if self.suit:
            self.suit.loop('neutral')
        self.timer.stop()
        self.timer.hide()
        taskMgr.remove(self.taskName('tug-timeout'))

    def enterGameDone(self):
        pass

    def exitGameDone(self):
        pass

    def enterCleanup(self):
        self.notify.debug('enterCleanup')
        self.__killUpdateIdealRateTask()
        self.__killUpdateTimerTask()
        self.__killUpdateKeyPressRateTask()
        self.__killUpdateRopeTask()

    def exitCleanup(self):
        pass

    def __gameTimerExpired(self):
        self.notify.debug('game timer expired')
        if self.arrowKeys:
            self.arrowKeys.setPressHandlers(self.arrowKeys.NULL_HANDLERS)
            self.arrowKeys.setReleaseHandlers(self.arrowKeys.NULL_HANDLERS)

    def __pressHandler(self, index):
        self.notify.debug('pressHandler')
        if index == self.buttons[0]:
            self.hilightArrow(self.arrows[index])
            self.keyTTL.insert(0, 1.0)
            self.buttons.reverse()

    def __releaseHandler(self, index):
        self.notify.debug('releaseHandler')
        if index in self.buttons:
            self.unhilightArrow(self.arrows[index])

    def __updateKeyPressRateTask(self, task):
        if self.gameFSM.getCurrentState().getName() != 'tug':
            return Task.done
        for i in range(len(self.keyTTL)):
            self.keyTTL[i] -= 0.1

        for i in range(len(self.keyTTL)):
            if self.keyTTL[i] <= 0:
                a = self.keyTTL[0:i]
                del self.keyTTL
                self.keyTTL = a
                break

        self.keyRate = len(self.keyTTL)
        if self.keyRate == self.idealRate or self.keyRate == self.idealRate + 1:
            self.rateMatchAward += 0.3
        else:
            self.rateMatchAward = 0
        self.__spawnUpdateKeyPressRateTask()
        return Task.done

    def __updateTimerTask(self, task):
        if self.gameFSM.getCurrentState().getName() != 'tug':
            return Task.done
        self.currentForce = self.computeForce(self.keyRate)
        self.sendUpdate('reportCurrentKeyRate', [self.keyRate, self.currentForce])
        self.setSpeedGauge()
        self.setAnimState(self.localAvId, self.keyRate)
        self.__spawnUpdateTimerTask()
        return Task.done

    def __spawnUpdateTimerTask(self):
        taskMgr.remove(self.taskName(self.UPDATE_TIMER_TASK))
        taskMgr.doMethodLater(TugOfWarGameGlobals.SEND_UPDATE, self.__updateTimerTask, self.taskName(self.UPDATE_TIMER_TASK))

    def __killUpdateTimerTask(self):
        taskMgr.remove(self.taskName(self.UPDATE_TIMER_TASK))

    def __spawnUpdateKeyPressRateTask(self):
        taskMgr.remove(self.taskName(self.UPDATE_KEY_PRESS_RATE_TASK))
        taskMgr.doMethodLater(0.1, self.__updateKeyPressRateTask, self.taskName(self.UPDATE_KEY_PRESS_RATE_TASK))

    def __killUpdateKeyPressRateTask(self):
        taskMgr.remove(self.taskName(self.UPDATE_KEY_PRESS_RATE_TASK))

    def __spawnUpdateIdealRateTask(self):
        self.idealRate = self.targetRateList[self.nextRateIndex][1]
        self.idealForce = self.advantage * (4 + 0.4 * self.idealRate)
        taskMgr.doMethodLater(self.targetRateList[self.nextRateIndex][0], self.__updateIdealRateTask, self.taskName('targetRateTimer'))

    def __updateIdealRateTask(self, task):
        self.nextRateIndex = self.nextRateIndex + 1
        if self.nextRateIndex < len(self.targetRateList):
            if self.nextRateIndex == len(self.targetRateList) - 1:
                self.allOutMode = 1
            self.idealRate = self.targetRateList[self.nextRateIndex][1]
            self.idealForce = self.advantage * (4 + 0.4 * self.idealRate)
            taskMgr.doMethodLater(self.targetRateList[self.nextRateIndex][0], self.__updateIdealRateTask, self.taskName('targetRateTimer'))
        return Task.done

    def __killUpdateIdealRateTask(self):
        taskMgr.remove(self.taskName('targetRateTimer'))

    def sendGoSignal(self, index):
        if not self.hasLocalToon:
            return
        self.notify.debug('sendGoSignal')
        self.buttons = index
        self.setupTrack = None
        self.showTrack = None

        def startTimer(self = self):
            self.currentStartTime = int(globalClock.getFrameTime() * 1000)
            time = 10
            self.timer.show()
            self.timer.setTime(TugOfWarGameGlobals.GAME_DURATION)
            self.timer.countdown(TugOfWarGameGlobals.GAME_DURATION, self.__gameTimerExpired)

        def enableKeys(self = self):

            def keyPress(self, index):
                self.__pressHandler(index)

            def keyRelease(self, index):
                self.__releaseHandler(index)

            self.arrowKeys.setPressHandlers([lambda self = self, keyPress = keyPress: keyPress(self, 2),
             lambda self = self, keyPress = keyPress: keyPress(self, 3),
             lambda self = self, keyPress = keyPress: keyPress(self, 1),
             lambda self = self, keyPress = keyPress: keyPress(self, 0)])
            self.arrowKeys.setReleaseHandlers([lambda self = self, keyRelease = keyRelease: keyRelease(self, 2),
             lambda self = self, keyRelease = keyRelease: keyRelease(self, 3),
             lambda self = self, keyRelease = keyRelease: keyRelease(self, 1),
             lambda self = self, keyRelease = keyRelease: keyRelease(self, 0)])
            for x in index:
                self.enableArrow(self.arrows[x])

        if self.introTrack != None:
            self.introTrack.finish()
            self.introTrack = None
        self.setupTrack = Sequence(Func(self.setText, self.roundText, TTLocalizer.TugOfWarGameReady), Wait(1.5), Func(base.playSfx, self.whistleSound), Func(self.setText, self.roundText, TTLocalizer.TugOfWarGameGo), Func(self.roundText.setScale, 0.3), Wait(1.5), Func(startTimer), Func(enableKeys), Func(self.gameFSM.request, 'tug'), Func(self.setText, self.roundText, ' '), Func(self.roundText.setScale, 0.2))
        self.setupTrack.start()
        return

    def sendStopSignal(self, winners, losers, tieers):
        if not self.hasLocalToon:
            return
        self.notify.debug('sendStopSignal')
        self.gameFSM.request('gameDone')
        self.hideControls()
        reactSeq = Sequence()
        exitSeq = Sequence()
        suitSlipTime = 0
        if self.gameFSM.getCurrentState().getName() == 'cleanup' or not self.randomNumGen:
            return
        if self.suit:
            if self.suitId in winners:
                newPos = VBase3(2.65, 18, 0.1)
                randInt = self.randomNumGen.randrange(0, 10)
                oopsTrack = Wait(0)
                if randInt < 3:
                    suitSlipTime = 2.2
                    waterPos = VBase3(0, 16, -5)
                    newPos -= VBase3(0.4, 0, 0)
                    self.suitSplash.stop()
                    self.suitSplash.setPos(waterPos[0], waterPos[1], -1.8)
                    self.suitSplash.setScale(3.5, 3.5, 1)
                    self.suitRipples.setPos(waterPos[0], waterPos[1], -1.7)
                    self.suitRipples.setScale(1, 1, 1)
                    startHpr = self.suit.getHpr()
                    destHpr = startHpr + VBase3(0, 0, -30)
                    oopsTrack = Sequence(Parallel(Func(self.suit.play, 'flail', None, 26, 38), LerpHprInterval(self.suit, 0.5, destHpr, startHpr=startHpr)), Parallel(Func(self.suit.play, 'slip-forward'), LerpPosInterval(self.suit, duration=1, pos=waterPos), Sequence(Wait(0.55), Func(base.playSfx, self.sndHitWater), Func(self.suitSplash.play), Func(self.ripples.play))))
                    reactSeq.append(Sequence(Func(self.suit.loop, 'victory'), Wait(2.6), LerpPosInterval(self.suit, duration=2, pos=newPos), oopsTrack, Func(self.suit.loop, 'neutral')))
        for avId in self.avIdList:
            toon = self.getAvatar(avId)
            toon.loop('neutral')
            if avId in winners:
                reactSeq.append(Func(toon.loop, 'victory'))
            elif avId in losers:
                reactSeq.append(Func(toon.loop, 'neutral'))
            else:
                reactSeq.append(Func(toon.loop, 'neutral'))

        if self.localAvId in winners:
            exitSeq.append(Func(self.setText, self.roundText, TTLocalizer.TugOfWarGameEnd))
            exitSeq.append(Wait(5.0))
        elif self.localAvId in losers:
            exitSeq.append(Func(self.setText, self.roundText, TTLocalizer.TugOfWarGameEnd))
            exitSeq.append(Wait(4.8 + suitSlipTime))
        else:
            exitSeq.append(Func(self.setText, self.roundText, TTLocalizer.TugOfWarGameTie))
            exitSeq.append(Wait(2.5))
        exitSeq.append(Func(self.gameOver))
        self.showTrack = Parallel(reactSeq, exitSeq)
        for x in list(self.animTracks.values()):
            if x != None:
                x.finish()

        self.showTrack.start()
        if self.arrowKeys:
            self.arrowKeys.setPressHandlers(self.arrowKeys.NULL_HANDLERS)
            self.arrowKeys.setReleaseHandlers(self.arrowKeys.NULL_HANDLERS)
        return

    def remoteKeyRateUpdate(self, avId, keyRate):
        if not self.hasLocalToon:
            return
        if avId != self.localAvId:
            self.setAnimState(avId, keyRate)

    def sendSuitPosition(self, suitOffset):
        if not self.hasLocalToon:
            return
        if self.gameFSM.getCurrentState().getName() != 'tug':
            return
        self.suitOffset = suitOffset
        self.moveSuits()

    def sendCurrentPosition(self, avIdList, offsetList):
        if not self.hasLocalToon:
            return
        if self.gameFSM.getCurrentState().getName() != 'tug':
            return
        for i in range(len(avIdList)):
            self.offsetDict[avIdList[i]] = offsetList[i]

        self.moveToons()
        self.setUpRopes(0)

    def createSuits(self):
        if self.gameType == TugOfWarGameGlobals.TOON_VS_COG:
            self.suit = Suit.Suit()
            self.origSuitPosHpr = [VBase3(6.0, 18, 0.1), VBase3(120, 0, 0)]
            self.suitOffset = 0
            d = SuitDNA.SuitDNA()
            d.newSuit(self.suitType)
            self.suit.setDNA(d)
            self.suit.reparentTo(render)
            self.suit.setPos(self.origSuitPosHpr[0])
            self.suit.setHpr(self.origSuitPosHpr[1])
            for anim in self.suitAnimNames:
                self.suit.pose(anim, 0)

            self.suit.pose('tug-o-war', 0)
            self.dropShadowDict[self.suitId] = self.dropShadow.copyTo(hidden)
            self.dropShadowDict[self.suitId].reparentTo(self.suit)
            self.dropShadowDict[self.suitId].setScale(0.45)

    def initHandycaps(self):
        if self.numPlayers == 3 and self.gameType == TugOfWarGameGlobals.TOON_VS_TOON:
            if len(self.avList[0]) == 1:
                toon = self.getAvatar(self.avList[0][0])
                if self.avList[0][0] == self.localAvId:
                    self.advantage = 2.0
                toon.applyCheesyEffect(ToontownGlobals.CEBigHead)
            elif len(self.avList[1]) == 1:
                toon = self.getAvatar(self.avList[1][0])
                if self.avList[1][0] == self.localAvId:
                    self.advantage = 2.0
                toon.applyCheesyEffect(ToontownGlobals.CEBigHead)

    def setSpeedGauge(self):
        self.powerMeter.setPower(self.keyRate)
        self.powerMeter.setTarget(self.idealRate)
        if not self.allOutMode:
            self.powerMeter.updateTooSlowTooFast()
        if not self.allOutMode:
            index = float(self.currentForce) / self.idealForce
            bonus = 0.0
            if index > 1:
                bonus = max(1, index - 1)
                index = 1
            color = (0,
             0.75 * index + 0.25 * bonus,
             0.75 * (1 - index),
             0.5)
            self.powerMeter.setBarColor(color)
        else:
            self.powerMeter.setBarColor((0, 1, 0, 0.5))

    def setAnimState(self, avId, keyRate):
        if self.gameFSM.getCurrentState().getName() != 'tug':
            return
        toon = self.getAvatar(avId)
        if keyRate > 0 and self.pullingDict[avId] == 0:
            toon.loop('tug-o-war')
            self.pullingDict[avId] = 1
        if keyRate <= 0 and self.pullingDict[avId] == 1:
            toon.pose('tug-o-war', 3)
            toon.startLookAround()
            self.pullingDict[avId] = 0

    def moveSuits(self):
        if self.gameType != TugOfWarGameGlobals.TOON_VS_COG:
            return
        origPos = self.origSuitPosHpr[0]
        curPos = self.suit.getPos()
        newPos = VBase3(origPos[0] + self.suitOffset, curPos[1], curPos[2])
        if self.animTracks[self.suitId] != None:
            if self.animTracks[self.suitId].isPlaying():
                self.animTracks[self.suitId].finish()
                self.checkIfFallen()
        if self.suitId not in self.fallenList:
            self.animTracks[self.suitId] = Sequence(LerpPosInterval(self.suit, duration=TugOfWarGameGlobals.SEND_UPDATE, pos=newPos), Func(self.checkIfFallen))
            self.animTracks[self.suitId].start()
        return

    def moveToons(self):
        for avId in self.avIdList:
            if avId not in self.fallenList:
                toon = self.getAvatar(avId)
                if toon:
                    origPos = self.posDict[avId]
                    curPos = toon.getPos()
                    newPos = VBase3(origPos[0] + self.offsetDict[avId] / self.handycap, curPos[1], curPos[2])
                    if self.animTracks[avId] != None:
                        if self.animTracks[avId].isPlaying():
                            self.animTracks[avId].finish()
                            self.checkIfFallen(avId)
                    if avId not in self.fallenList:
                        self.animTracks[avId] = Sequence(LerpPosInterval(toon, duration=TugOfWarGameGlobals.SEND_UPDATE, pos=newPos), Func(self.checkIfFallen, avId))
                        self.animTracks[avId].start()

        return

    def checkIfFallen(self, avId = None):
        if avId == None:
            if self.suitId not in self.fallenList:
                curPos = self.suit.getPos()
                if curPos[0] < 0 and curPos[0] > -2 or curPos[0] > 0 and curPos[0] < 2:
                    self.hideControls()
                    self.throwInWater()
                    losingSide = 1
                    self.sendUpdate('reportEndOfContest', [losingSide])
        elif avId not in self.fallenList:
            toon = self.getAvatar(avId)
            if toon:
                curPos = toon.getPos()
                if curPos[0] < 0 and curPos[0] > -2 or curPos[0] > 0 and curPos[0] < 2:
                    self.hideControls()
                    losingSide = self.sides[avId]
                    for avId in self.avIdList:
                        if self.sides[avId] == losingSide:
                            self.throwInWater(avId)

                    self.sendUpdate('reportEndOfContest', [losingSide])
        return

    def throwInWater(self, avId = None):
        if avId == None:
            self.fallenList.append(self.suitId)
            waterPos = self.drinkPositions.pop()
            newPos = VBase3(waterPos[0], waterPos[1], waterPos[2] - self.suit.getHeight() / 1.5)
            self.suit.loop('neutral')
            self.dropShadowDict[self.suitId].reparentTo(hidden)
            loser = self.suit
            animId = self.suitId
        else:
            self.fallenList.append(avId)
            toon = self.getAvatar(avId)
            waterPos = self.drinkPositions.pop()
            newPos = VBase3(waterPos[0], waterPos[1], waterPos[2] - toon.getHeight())
            toon.loop('neutral')
            self.dropShadowDict[avId].reparentTo(hidden)
            loser = toon
            animId = avId
        if self.animTracks[animId] != None:
            if self.animTracks[animId].isPlaying():
                self.animTracks[animId].finish()
        self.splash.setPos(newPos[0], newPos[1], -1.8)
        self.splash.setScale(2.5, 2.5, 1)
        self.ripples.setPos(newPos[0], newPos[1], -1.7)
        self.ripples.setScale(1, 1, 1)
        self.animTracks[animId] = Sequence(Parallel(ActorInterval(actor=loser, animName='slip-forward', duration=2.0), LerpPosInterval(loser, duration=2.0, pos=newPos), Sequence(Wait(1.0), Parallel(Func(base.playSfx, self.sndHitWater), Func(self.splash.play), Func(self.ripples.play)))), Func(loser.loop, 'neutral'))
        self.animTracks[animId].start()
        return

    def computeForce(self, keyRate):
        F = 0
        if self.allOutMode == 1:
            F = 0.75 * keyRate
        else:
            stdDev = 0.25 * self.idealRate
            F = self.advantage * (self.rateMatchAward + 4 + 0.4 * self.idealRate) * math.pow(math.e, -math.pow(keyRate - self.idealRate, 2) / (2.0 * math.pow(stdDev, 2)))
        return F

    def initRopes(self):
        if self.gameType == TugOfWarGameGlobals.TOON_VS_COG:
            numRopes = self.numPlayers
        else:
            numRopes = self.numPlayers - 1
        for x in range(0, numRopes):
            rope = Rope.Rope(self.uniqueName('TugRope' + str(x)))
            if rope.showRope:
                rope.ropeNode.setRenderMode(RopeNode.RMBillboard)
                rope.ropeNode.setThickness(0.2)
                rope.setTexture(self.ropeTexture)
                rope.ropeNode.setUvMode(RopeNode.UVDistance)
                rope.ropeNode.setUvDirection(1)
                rope.setTransparency(1)
                rope.setColor(0.89, 0.89, 0.6, 1)
            self.tugRopes.append(rope)

        self.setUpRopes(1)

    def __spawnUpdateRopeTask(self):
        taskMgr.remove(self.taskName(self.UPDATE_ROPE_TASK))
        taskMgr.add(self.__updateRopeTask, self.taskName(self.UPDATE_ROPE_TASK))

    def __updateRopeTask(self, task):
        if self.tugRopes != None:
            for i in range(len(self.tugRopes)):
                if self.tugRopes[i] != None:
                    self.ropePts[i] = self.tugRopes[i].getPoints(len(self.ropeTex[i]))
                    for j in range(len(self.ropePts[i])):
                        self.ropeTex[i][j].setPos(self.ropePts[i][j])

        return Task.cont

    def __killUpdateRopeTask(self):
        taskMgr.remove(self.taskName(self.UPDATE_ROPE_TASK))

    def tugTimeoutTask(self, task):
        self.gameOver()
        return Task.done

    def waitForGoTimeoutTask(self, task):
        self.gameOver()
        return Task.done

    def __spawnMouseSpeedTask(self):
        taskMgr.remove(self.taskName('mouseSpeed'))
        taskMgr.add(self.__mouseSpeedTask, self.taskName('mouseSpeed'))

    def __killMouseSpeedTask(self):
        taskMgr.remove(self.taskName('mouseSpeed'))

    def __mouseSpeedTask(self, task):
        dx = 0.1
        if self.mouseMode:
            mx = base.mouseWatcherNode.getMouseX()
            my = base.mouseWatcherNode.getMouseY()
            if self.mouseSide == 0:
                if mx > dx:
                    self.mouseSide = 1
                    self.__releaseHandler(1)
                    self.__pressHandler(0)
                elif mx > -dx:
                    self.__releaseHandler(1)
            elif self.mouseSide == 1:
                if mx < -dx:
                    self.mouseSide = 0
                    self.__releaseHandler(0)
                    self.__pressHandler(1)
                elif mx < dx:
                    self.__releaseHandler(0)
        return Task.cont
