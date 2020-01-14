from pandac.PandaModules import Point3, ForceNode, LinearVectorForce, CollisionHandlerEvent, CollisionNode, CollisionSphere, Camera, PerspectiveLens, Vec4, Point2, ActorNode, Vec3, BitMask32
from direct.interval.IntervalGlobal import Sequence, Parallel, Func, Wait, LerpPosInterval, ActorInterval, LerpScaleInterval, ProjectileInterval, SoundInterval
from direct.directnotify import DirectNotifyGlobal
from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectGui import DGG
from toontown.toonbase import ToontownGlobals
from direct.task.Task import Task
from direct.fsm import ClassicFSM, State
from toontown.toonbase import TTLocalizer
from toontown.minigame.DistributedMinigame import DistributedMinigame
from toontown.minigame import SwingVine
from toontown.minigame import ArrowKeys
from toontown.minigame import VineGameGlobals
from toontown.minigame import VineTreasure
from toontown.minigame import MinigameAvatarScorePanel
from toontown.toonbase import ToontownTimer
from toontown.minigame import VineHeadFrame
from toontown.minigame import VineBat

class DistributedVineGame(DistributedMinigame):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedVineGame')
    UpdateLocalToonTask = 'VineGameUpdateLocalToonTask'
    LocalPhysicsRadius = 1.5
    Gravity = 32
    ToonVerticalRate = 0.25
    FallingNot = 0
    FallingNormal = 1
    FallingSpider = 2
    FallingBat = 3
    JumpingFrame = 128
    ToonMaxRightFrame = 35

    def __init__(self, cr):
        DistributedMinigame.__init__(self, cr)
        self.JumpSpeed = 64
        self.TwoVineView = True
        self.ArrowToChangeFacing = True
        self.gameFSM = ClassicFSM.ClassicFSM('DistributedVineGame', [State.State('off', self.enterOff, self.exitOff, ['play']),
         State.State('play', self.enterPlay, self.exitPlay, ['cleanup', 'showScores', 'waitShowScores']),
         State.State('waitShowScores', self.enterWaitShowScores, self.exitWaitShowScores, ['cleanup', 'showScores']),
         State.State('showScores', self.enterShowScores, self.exitShowScores, ['cleanup']),
         State.State('cleanup', self.enterCleanup, self.exitCleanup, [])], 'off', 'cleanup')
        self.addChildGameFSM(self.gameFSM)
        self.cameraTopView = (17.6, 6.18756, 43.9956, 0, -89, 0)
        self.cameraThreeQuarterView = (0, -63.2, 16.3, 0, 0, 0)
        self.cameraSidePos = Point3(0, -63.2, 16.3)
        self.cameraTwoVineSidePos = Point3(0, -53, 17.3)
        self.cameraTwoVineAdj = 5
        self.cameraSideView = (-15, -53, 17.3, 0, 0, 0)
        self.localPhysicsNP = None
        self.vines = []
        self.physicsHandler = None
        self.lastJumpVine = -1
        self.lastJumpPos = None
        self.lastJumpT = 0
        self.lastJumpFacingRight = True
        self.lastJumpTime = 0
        self.toonInfo = {}
        self.otherToonPhysics = {}
        self.headFrames = {}
        self.changeFacingInterval = None
        self.attachingToVineCamIval = None
        self.localToonJumpAnimIval = None
        self.endingTracks = {}
        self.endingTrackTaskNames = []
        self.sendNewVineTUpdateAsap = False
        self.lastNewVineTUpdate = 0
        self.defaultMaxX = (VineGameGlobals.NumVines + 1) * VineGameGlobals.VineXIncrement
        return

    def getClimbDir(self, avId):
        retval = 0
        if avId in self.toonInfo:
            retval = self.toonInfo[avId][5]
        return retval

    def moveCameraToSide(self):
        camera.reparentTo(render)
        p = self.cameraSideView
        camera.setPosHpr(p[0], p[1], p[2], p[3], p[4], p[5])

    def getTitle(self):
        return TTLocalizer.VineGameTitle

    def getInstructions(self):
        return TTLocalizer.VineGameInstructions

    def getMaxDuration(self):
        return 0

    def defineConstants(self):
        self.ShowToonSpheres = 0

    def load(self):
        self.notify.debug('load')
        DistributedMinigame.load(self)
        self.defineConstants()
        self.music = base.loader.loadMusic('phase_4/audio/bgm/MG_Vine.ogg')
        self.gameAssets = loader.loadModel('phase_4/models/minigames/vine_game')
        self.gameBoard = self.gameAssets.find('**/background')
        self.gameBoard.reparentTo(render)
        self.gameBoard.show()
        self.gameBoard.setPosHpr(0, 0, 0, 0, 0, 0)
        self.gameBoard.setTransparency(1)
        self.gameBoard.setColorScale(1, 1, 1, 0.5)
        self.gameBoard.setScale(1.0)
        self.gameBoard.hide(VineGameGlobals.RadarCameraBitmask)
        self.treasureModel = self.gameAssets.find('**/bananas')
        self.setupVineCourse()
        self.grabSound = base.loader.loadSfx('phase_4/audio/sfx/MG_sfx_vine_game_bananas.ogg')
        self.jumpSound = base.loader.loadSfx('phase_4/audio/sfx/MG_sfx_vine_game_jump.ogg')
        self.catchSound = base.loader.loadSfx('phase_4/audio/sfx/MG_sfx_vine_game_catch.ogg')
        self.spiderHitSound = base.loader.loadSfx('phase_4/audio/sfx/MG_sfx_vine_game_spider_hit.ogg')
        self.batHitVineSound = base.loader.loadSfx('phase_4/audio/sfx/MG_sfx_vine_game_bat_hit.ogg')
        self.batHitMidairSound = base.loader.loadSfx('phase_4/audio/sfx/MG_sfx_vine_game_bat_hit_midair.ogg')
        self.winSound = base.loader.loadSfx('phase_4/audio/sfx/MG_sfx_vine_game_finish.ogg')
        self.fallSound = base.loader.loadSfx('phase_4/audio/sfx/MG_sfx_vine_game_fall.ogg')
        self.loadBats()
        self.createBatIvals()
        bothPlatform = loader.loadModel('phase_4/models/minigames/vine_game_shelf')
        self.startPlatform = bothPlatform.find('**/start1')
        self.startPlatform.setPos(-16, 0, 15)
        self.startPlatform.reparentTo(render)
        self.startPlatform.setScale(1.0, 1.0, 0.75)
        self.endPlatform = bothPlatform.find('**/end1')
        endPos = self.vines[VineGameGlobals.NumVines - 1].getPos()
        self.endPlatform.setPos(endPos[0] + 20, 0, 15)
        self.endPlatform.reparentTo(render)
        self.endPlatform.setScale(1.0, 1.0, 0.75)

    def unload(self):
        self.notify.debug('unload')
        DistributedMinigame.unload(self)
        self.removeChildGameFSM(self.gameFSM)
        del self.gameFSM
        del self.music
        self.gameAssets.removeNode()
        self.gameBoard.removeNode()
        del self.gameBoard
        self.treasureModel.removeNode()
        del self.treasureModel
        for vine in self.vines:
            vine.unload()
            del vine

        self.vines = []
        self.destroyBatIvals()
        for bat in self.bats:
            bat.destroy()
            del bat

        self.bats = []
        del self.grabSound
        del self.jumpSound
        del self.catchSound
        del self.spiderHitSound
        del self.batHitVineSound
        del self.batHitMidairSound
        del self.winSound
        del self.fallSound
        if self.localToonJumpAnimIval:
            self.localToonJumpAnimIval.finish()
            del self.localToonJumpAnimIval
        self.startPlatform.removeNode()
        self.endPlatform.removeNode()

    def onstage(self):
        self.notify.debug('onstage')
        DistributedMinigame.onstage(self)
        for avId in self.avIdList:
            self.updateToonInfo(avId, vineIndex=0, vineT=VineGameGlobals.VineStartingT, posX=0, posZ=0, facingRight=0, climbDir=0, fallingInfo=self.FallingNot)

        self.scorePanels = []
        self.gameBoard.reparentTo(render)
        self.moveCameraToSide()
        self.arrowKeys = ArrowKeys.ArrowKeys()
        handlers = [self.upArrowKeyHandler,
         self.downArrowKeyHandler,
         self.leftArrowKeyHandler,
         self.rightArrowKeyHandler,
         None]
        self.arrowKeys.setPressHandlers(handlers)
        self.numTreasures = len(self.vines) - 1
        self.treasures = []
        for i in range(self.numTreasures):
            height = self.randomNumGen.randrange(10, 25)
            xPos = self.randomNumGen.randrange(12, 18)
            pos = Point3(self.vines[i].getX() + 15, 0, height)
            self.treasures.append(VineTreasure.VineTreasure(self.treasureModel, pos, i, self.doId))

        gravityFN = ForceNode('world-forces')
        gravityFNP = render.attachNewNode(gravityFN)
        gravityForce = LinearVectorForce(0, 0, -self.Gravity)
        gravityFN.addForce(gravityForce)
        base.physicsMgr.addLinearForce(gravityForce)
        self.gravityForce = gravityForce
        self.gravityForceFNP = gravityFNP
        lt = base.localAvatar
        radius = 0.7
        handler = CollisionHandlerEvent()
        handler.setInPattern('ltCatch-%fn')
        self.bodyColEventNames = []
        self.ltLegsCollNode = CollisionNode('catchLegsCollNode')
        self.bodyColEventNames.append('ltCatch-%s' % 'catchLegsCollNode')
        self.ltLegsCollNode.setCollideMask(VineGameGlobals.SpiderBitmask)
        self.ltTorsoCollNode = CollisionNode('catchTorsoCollNode')
        self.bodyColEventNames.append('ltCatch-%s' % 'catchTorsoCollNode')
        self.ltTorsoCollNode.setCollideMask(VineGameGlobals.SpiderBitmask)
        self.ltHeadCollNode = CollisionNode('catchHeadCollNode')
        self.bodyColEventNames.append('ltCatch-%s' % 'catchHeadCollNode')
        self.ltHeadCollNode.setCollideMask(VineGameGlobals.SpiderBitmask)
        self.ltLHandCollNode = CollisionNode('catchLHandCollNode')
        self.bodyColEventNames.append('ltCatch-%s' % 'catchLHandCollNode')
        self.ltLHandCollNode.setCollideMask(VineGameGlobals.SpiderBitmask)
        self.ltRHandCollNode = CollisionNode('catchRHandCollNode')
        self.bodyColEventNames.append('ltCatch-%s' % 'catchRHandCollNode')
        self.ltRHandCollNode.setCollideMask(VineGameGlobals.SpiderBitmask)
        legsCollNodepath = lt.attachNewNode(self.ltLegsCollNode)
        legsCollNodepath.hide()
        head = base.localAvatar.getHeadParts().getPath(2)
        headCollNodepath = head.attachNewNode(self.ltHeadCollNode)
        headCollNodepath.hide()
        torso = base.localAvatar.getTorsoParts().getPath(2)
        torsoCollNodepath = torso.attachNewNode(self.ltTorsoCollNode)
        torsoCollNodepath.hide()
        self.torso = torsoCollNodepath
        lHand = base.localAvatar.getLeftHands()[0]
        lHandCollNodepath = lHand.attachNewNode(self.ltLHandCollNode)
        lHandCollNodepath.hide()
        rHand = base.localAvatar.getRightHands()[0]
        rHandCollNodepath = rHand.attachNewNode(self.ltRHandCollNode)
        rHandCollNodepath.hide()
        lt.cTrav.addCollider(legsCollNodepath, handler)
        lt.cTrav.addCollider(headCollNodepath, handler)
        lt.cTrav.addCollider(lHandCollNodepath, handler)
        lt.cTrav.addCollider(rHandCollNodepath, handler)
        lt.cTrav.addCollider(torsoCollNodepath, handler)
        if self.ShowToonSpheres:
            legsCollNodepath.show()
            headCollNodepath.show()
            lHandCollNodepath.show()
            rHandCollNodepath.show()
            torsoCollNodepath.show()
        self.ltLegsCollNode.addSolid(CollisionSphere(0, 0, radius, radius))
        self.ltHeadCollNode.addSolid(CollisionSphere(0, 0, 0, radius))
        self.ltLHandCollNode.addSolid(CollisionSphere(0, 0, 0, 2 * radius / 3.0))
        self.ltRHandCollNode.addSolid(CollisionSphere(0, 0, 0, 2 * radius / 3.0))
        self.ltTorsoCollNode.addSolid(CollisionSphere(0, 0, radius, radius * 2))
        self.toonCollNodes = [legsCollNodepath,
         headCollNodepath,
         lHandCollNodepath,
         rHandCollNodepath,
         torsoCollNodepath]
        for eventName in self.bodyColEventNames:
            self.accept(eventName, self.toonHitSomething)

        self.introTrack = self.getIntroTrack()
        self.introTrack.start()
        return

    def offstage(self):
        self.notify.debug('offstage')
        for panel in self.scorePanels:
            panel.cleanup()

        del self.scorePanels
        self.gameBoard.hide()
        DistributedMinigame.offstage(self)
        self.arrowKeys.destroy()
        del self.arrowKeys
        for avId in self.avIdList:
            av = self.getAvatar(avId)
            if av:
                av.dropShadow.show()
                av.resetLOD()

        for treasure in self.treasures:
            treasure.destroy()

        del self.treasures
        base.physicsMgr.removeLinearForce(self.gravityForce)
        self.gravityForceFNP.removeNode()
        for collNode in self.toonCollNodes:
            while collNode.node().getNumSolids():
                collNode.node().removeSolid(0)

            base.localAvatar.cTrav.removeCollider(collNode)

        del self.toonCollNodes
        for eventName in self.bodyColEventNames:
            self.ignore(eventName)

        self.ignoreAll()
        if self.introTrack.isPlaying():
            self.introTrack.finish()
        del self.introTrack
        for vine in self.vines:
            vine.stopSwing()
            vine.hide()

        self.startPlatform.hide()
        self.endPlatform.hide()

    def handleDisabledAvatar(self, avId):
        self.notify.debug('handleDisabledAvatar')
        self.notify.debug('avatar ' + str(avId) + ' disabled')
        DistributedMinigame.handleDisabledAvatar(self, avId)

    def updateToonInfo(self, avId, vineIndex = None, vineT = None, posX = None, posZ = None, facingRight = None, climbDir = None, velX = None, velZ = None, fallingInfo = None):
        newVineIndex = vineIndex
        newVineT = vineT
        newPosX = posX
        newPosZ = posZ
        newFacingRight = facingRight
        newClimbDir = climbDir
        newVelX = velX
        newVelZ = velZ
        newFallingInfo = fallingInfo
        oldInfo = None
        if avId in self.toonInfo:
            oldInfo = self.toonInfo[avId]
            if vineIndex == None:
                newVineIndex = oldInfo[0]
            if vineT == None:
                newVineT = oldInfo[1]
            if posX == None:
                newPosX = oldInfo[2]
            if posZ == None:
                newPosZ = oldInfo[3]
            if facingRight == None:
                newFacingRight = oldInfo[4]
            if climbDir == None:
                newClimbDir = oldInfo[5]
            if velX == None:
                newVelX = oldInfo[6]
            if velZ == None:
                newVelZ = oldInfo[7]
            if fallingInfo == None:
                newFallingInfo = oldInfo[8]
        if newVineIndex < -1 or newVineIndex >= len(self.vines):
            self.notify.warning('invalid vineIndex for %d, forcing 0' % avId)
            newVineIndex = 0
        if newVineT < 0 or newVineT > 1:
            self.notify.warning('invalid vineT for %d, setting to 0' % avId)
        if not (newFacingRight == 0 or newFacingRight == 1):
            self.notify.warning('invalid facingRight for %d, forcing to 1' % avId)
            newFacingRight = 1
        if newPosX < -1000 or newPosX > 2000:
            self.notify.warning('invalid posX for %d, forcing to 0' % avId)
            newPosX = 0
        if newPosZ < -100 or newPosZ > 1000:
            self.notify.warning('invalid posZ for %d, forcing to 0' % avId)
            newPosZ = 0
        if newVelX is not None and (newVelX < -1000 or newVelX > 1000):
            self.notify.warning('invalid velX %s for %d, forcing to 0' % (newVelX, avId))
            newVelX = 0
        if newVelZ is not None and (newVelZ < -1000 or newVelZ > 1000):
            self.notify.warning('invalid velZ %s for %d, forcing to 0' % (newVelZ, avId))
            newVelZ = 0
        if newFallingInfo < self.FallingNot or newFallingInfo > self.FallingBat:
            self.notify.warning('invalid fallingInfo for %d, forcing to 0' % avId)
            newFallingInfo = 0
        newInfo = [newVineIndex,
            newVineT,
            newPosX,
            newPosZ,
            newFacingRight,
            newClimbDir,
            newVelX,
            newVelZ,
            newFallingInfo]
        self.toonInfo[avId] = newInfo
        if oldInfo:
            self.applyToonInfoChange(avId, newInfo, oldInfo)
        self.sanityCheck()
        return

    def applyToonInfoChange(self, avId, newInfo, oldInfo):
        if not self.isInPlayState():
            return
        oldVine = oldInfo[0]
        newVine = newInfo[0]
        if not oldVine == newVine:
            self.notify.debug('we have a vine change')
            if oldVine == -1:
                self.notify.debug(' we were jumping and now attaching to a new vine')
                newVineT = newInfo[1]
                newFacingRight = newInfo[4]
                self.vines[newVine].attachToon(avId, newVineT, newFacingRight)
                if newVine == VineGameGlobals.NumVines - 1:
                    self.doEndingTrackTask(avId)
            elif newVine == -1:
                self.notify.debug('we were attached to a vine and we are now jumping')
                curInfo = self.vines[oldVine].getAttachedToonInfo(avId)
                self.vines[oldVine].detachToon(avId)
                if not avId == self.localAvId:
                    posX = newInfo[2]
                    posZ = newInfo[3]
                    velX = newInfo[6]
                    velZ = newInfo[7]
                    self.makeOtherToonJump(avId, posX, posZ, velX, velZ)
            else:
                self.notify.warning('should not happen directly going from one vine to another')
                self.vines[oldVine].detachToon(avId)
                newVineT = newInfo[1]
                newFacingRight = newInfo[4]
                self.vines[newVine].attachToon(avId, newVineT, newFacingRight)
        elif newVine == oldVine and newInfo[4] != oldInfo[4]:
            self.notify.debug('# still on the same vine, but we changed facing')
            self.vines[newVine].changeAttachedToonFacing(avId, newInfo[4])
        elif newVine >= 0:
            self.vines[newVine].changeAttachedToonT(avId, newInfo[1])
        else:
            self.notify.debug('we are still falling')
            if oldInfo[8] != newInfo[8]:
                if not avId == self.localAvId:
                    posX = newInfo[2]
                    posZ = newInfo[3]
                    velX = newInfo[6]
                    velZ = newInfo[7]
                    self.makeOtherToonFallFromMidair(avId, posX, posZ, velX, velZ)

    def sanityCheck(self):
        if not self.isInPlayState():
            return
        for avId in list(self.toonInfo.keys()):
            myVineIndex = self.toonInfo[avId][0]
            foundVines = []
            foundVineIndex = -1
            for curVine in range(len(self.vines)):
                curInfo = self.vines[curVine].getAttachedToonInfo(avId)
                if curInfo:
                    foundVines.append(curVine)
                    foundVineIndex = curVine

            if len(foundVines) > 1:
                self.notify.warning('toon %d is attached to vines %s' % (avId, foundVines))
            if not foundVineIndex == myVineIndex and not myVineIndex == VineGameGlobals.NumVines - 1:
                self.notify.warning('avId=%d foundVineIndex=%d != myVineIndex=%d' % (avId, foundVineIndex, myVineIndex))

    def getVineAndVineInfo(self, avId):
        retVine = -1
        retInfo = None
        for curVine in range(len(self.vines)):
            curInfo = self.vines[curVine].getAttachedToonInfo(avId)
            if curInfo:
                retVine = curVine
                retInfo = curInfo
                break

        if self.toonInfo[avId][0] != retVine:
            self.notify.warning("getVineAndVineInfo don't agree, toonInfo[%d]=%s, retVine=%d" % (avId, self.toonInfo[avId][0], retVine))
        return (retVine, curInfo)

    def setGameReady(self):
        if not self.hasLocalToon:
            return
        self.notify.debug('setGameReady')
        if DistributedMinigame.setGameReady(self):
            return
        self.toonOffsets = {}
        self.toonOffsetsFalling = {}
        for index in range(self.numPlayers):
            avId = self.avIdList[index]
            toon = self.getAvatar(avId)
            if toon:
                toon.reparentTo(render)
                toon.setPos(0, 0, 0)
                toon.setHpr(0, 0, 0)
                self.toonOffsets[avId] = self.calcToonOffset(toon)
                toon.dropShadow.hide()
                newHeadFrame = VineHeadFrame.VineHeadFrame(toon)
                newHeadFrame.hide()
                self.headFrames[avId] = newHeadFrame
                toon.useLOD(1000)
                toon.setX(-100)

    def calcToonOffset(self, toon):
        offset = Point3(0, 0, 0)
        toon.pose('swing', 74)
        leftHand = toon.find('**/leftHand')
        if not leftHand.isEmpty():
            offset = leftHand.getPos(toon)
        return offset

    def setGameStart(self, timestamp):
        if not self.hasLocalToon:
            return
        self.notify.debug('setGameStart')
        DistributedMinigame.setGameStart(self, timestamp)
        if self.introTrack.isPlaying():
            self.introTrack.finish()
        self.gameFSM.request('play')

    def enterOff(self):
        self.notify.debug('enterOff')

    def exitOff(self):
        pass

    def enterPlay(self):
        self.notify.debug('enterPlay')
        if base.localAvatar.laffMeter:
            base.localAvatar.laffMeter.stop()
        self.createRadar()
        self.scores = [0] * self.numPlayers
        spacing = 0.4
        for i in range(self.numPlayers):
            avId = self.avIdList[i]
            avName = self.getAvatarName(avId)
            scorePanel = MinigameAvatarScorePanel.MinigameAvatarScorePanel(avId, avName)
            scorePanel.setScale(0.9)
            scorePanel.setPos(0.75 - spacing * (self.numPlayers - 1 - i), 0.0, 0.85)
            scorePanel.makeTransparent(0.75)
            self.scorePanels.append(scorePanel)

        for vine in self.vines:
            vine.show()
            vine.startSwing()

        self.startBatIvals()
        for avId in self.avIdList:
            toon = self.getAvatar(avId)
            if toon:
                if avId == self.localAvId:
                    self.attachLocalToonToVine(0, VineGameGlobals.VineStartingT)
                else:
                    self.vines[0].attachToon(avId, VineGameGlobals.VineStartingT, self.lastJumpFacingRight)

        self.timer = ToontownTimer.ToontownTimer()
        self.timer.posInTopRightCorner()
        self.timer.setTime(VineGameGlobals.GameDuration)
        self.timer.countdown(VineGameGlobals.GameDuration, self.timerExpired)
        base.playMusic(self.music, looping=1, volume=0.9)
        self.__spawnUpdateLocalToonTask()

    def exitPlay(self):
        self.notify.debug('exitPlay')
        if base.localAvatar.laffMeter:
            base.localAvatar.laffMeter.start()
        self.timer.stop()
        self.timer.destroy()
        del self.timer
        self.clearLocalPhysics()
        for ival in self.batIvals:
            ival.finish()
            del ival

        self.batIvals = []
        self.music.stop()

    def enterWaitShowScores(self):
        self.notify.debug('enterWaitShowScores')

    def exitWaitShowScores(self):
        self.notify.debug('exitWaitShowScores')

    def enterShowScores(self):
        self.notify.debug('enterShowScores')
        lerpTrack = Parallel()
        lerpDur = 0.5
        tY = 0.6
        bY = -.05
        lX = -.5
        cX = 0
        rX = 0.5
        scorePanelLocs = (((cX, bY),),
         ((lX, bY), (rX, bY)),
         ((cX, tY), (lX, bY), (rX, bY)),
         ((lX, tY),
          (rX, tY),
          (lX, bY),
          (rX, bY)))
        scorePanelLocs = scorePanelLocs[self.numPlayers - 1]
        for i in range(self.numPlayers):
            panel = self.scorePanels[i]
            pos = scorePanelLocs[i]
            lerpTrack.append(Parallel(LerpPosInterval(panel, lerpDur, Point3(pos[0], 0, pos[1]), blendType='easeInOut'), LerpScaleInterval(panel, lerpDur, Vec3(panel.getScale()) * 2.0, blendType='easeInOut')))

        self.showScoreTrack = Parallel(lerpTrack, Sequence(Wait(VineGameGlobals.ShowScoresDuration), Func(self.gameOver)))
        self.showScoreTrack.start()

    def exitShowScores(self):
        self.showScoreTrack.pause()
        del self.showScoreTrack

    def enterCleanup(self):
        self.notify.debug('enterCleanup')
        self.destroyRadar()
        self.__killUpdateLocalToonTask()
        self.cleanupEndingTracks()
        for avId in self.headFrames:
            self.headFrames[avId].destroy()

    def exitCleanup(self):
        pass

    def __spawnUpdateLocalToonTask(self):
        taskMgr.remove(self.UpdateLocalToonTask)
        taskMgr.add(self.__updateLocalToonTask, self.UpdateLocalToonTask)

    def __killUpdateLocalToonTask(self):
        taskMgr.remove(self.UpdateLocalToonTask)

    def clearLocalPhysics(self):
        if self.localPhysicsNP:
            an = self.localPhysicsNP.node()
            base.physicsMgr.removePhysicalNode(an)
            self.localPhysicsNP.removeNode()
            del self.localPhysicsNP
            self.localPhysicsNP = None
        if hasattr(self, 'treasureCollNodePath') and self.treasureCollNodePath:
            self.treasureCollNodePath.removeNode()
        return

    def handleLocalToonFellDown(self):
        self.notify.debug('attaching toon back to vine since he fell')
        self.fallSound.play()
        vineToAttach = self.lastJumpVine
        if self.toonInfo[self.localAvId][8] == self.FallingSpider:
            if self.vines[vineToAttach].hasSpider:
                vineToAttach -= 1
        if vineToAttach < 0:
            vineToAttach = 0
        self.attachLocalToonToVine(vineToAttach, VineGameGlobals.VineFellDownT)

    def makeCameraFollowJumpingToon(self):
        camera.setHpr(0, 0, 0)
        if self.TwoVineView:
            camera.setPos(self.cameraTwoVineSidePos)
            maxVine = self.lastJumpVine + 1
            if maxVine >= len(self.vines):
                maxVine = len(self.vines) - 1
            maxX = self.defaultMaxX
            if self.vines:
                maxX = self.vines[maxVine].getX()
            minVine = self.lastJumpVine - 1
            if minVine < 0:
                minVine = 0
            minX = 0
            if self.vines:
                minX = self.vines[minVine].getX()
            camera.setX(base.localAvatar.getX(render))
            if camera.getX() > maxX:
                camera.setX(maxX)
            if camera.getX() < minX:
                camera.setX(minX)
        else:
            camera.setPos(self.cameraSidePos)
            maxVine = self.lastJumpVine + 1
            if maxVine >= len(self.vines):
                maxVine = len(self.vines) - 1
            maxX = self.vines[maxVine].getX()
            minVine = self.lastJumpVine - 1
            if minVine < 0:
                minVine = 0
            minX = self.vines[minVine].getX()
            camera.setX(base.localAvatar.getX(render))
            if camera.getX() > maxX:
                camera.setX(maxX)
            if camera.getX() < minX:
                camera.setX(minX)

    def __updateOtherToonsClimbing(self):
        for avId in list(self.toonInfo.keys()):
            if avId == self.localAvId:
                continue
            toonInfo = self.toonInfo[avId]
            vineIndex = toonInfo[0]
            if vineIndex == -1:
                continue
            climbDir = toonInfo[5]
            if climbDir == None or climbDir == 0:
                continue
            curT = toonInfo[1]
            dt = globalClock.getDt()
            diffT = 0
            baseVerticalRate = self.ToonVerticalRate
            if climbDir == -1:
                diffT -= baseVerticalRate * dt
            if climbDir == 1:
                diffT += baseVerticalRate * dt
            newT = curT + diffT
            if newT > 1:
                newT = 1
            if newT < 0:
                newT = 0
            if not newT == curT:
                toonInfo[1] = newT
                self.vines[vineIndex].changeAttachedToonT(avId, newT)

        return

    def __updateLocalToonTask(self, task):
        dt = globalClock.getDt()
        self.updateRadar()
        self.__updateOtherToonsClimbing()
        for bat in self.bats:
            bat.checkScreech()

        if self.localPhysicsNP:
            pos = self.localPhysicsNP.getPos(render)
            if pos[2] < 0:
                self.handleLocalToonFellDown()
        avId = self.localAvId
        curInfo = None
        for vineIndex in range(len(self.vines)):
            curInfo = self.vines[vineIndex].getAttachedToonInfo(avId)
            if curInfo:
                break

        if not curInfo:
            if avId not in self.endingTracks:
                self.makeCameraFollowJumpingToon()
                if self.localPhysicsNP:
                    pos = self.localPhysicsNP.getPos(render)
        else:
            curT = curInfo[0]
            diffT = 0
            baseVerticalRate = self.ToonVerticalRate
            onEndVine = vineIndex == len(self.vines) - 1
            if self.arrowKeys.upPressed() and not onEndVine and self.isInPlayState():
                diffT -= baseVerticalRate * dt
            if self.arrowKeys.downPressed() and not onEndVine and self.isInPlayState():
                diffT += baseVerticalRate * dt
            newT = curT + diffT
            if newT > 1:
                newT = 1
            if newT < 0:
                newT = 0
            oldClimbDir = self.getClimbDir(avId)
            climbDir = 0
            if diffT < 0:
                climbDir = -1
            elif diffT > 0:
                climbDir = 1
            if not newT == curT:
                self.vines[vineIndex].changeAttachedToonT(avId, newT)
            if newT != curT or self.getClimbDir(avId) and not curT == 1.0 or oldClimbDir != climbDir:
                if oldClimbDir != climbDir:
                    self.sendNewVineTUpdateAsap = True
                self.b_setNewVineT(avId, newT, climbDir)
        return task.cont

    def setupCollisions(self, anp):
        fromObject = anp.attachNewNode(CollisionNode('colNode'))
        fromObject.node().addSolid(CollisionSphere(0, 0, 0, self.LocalPhysicsRadius))
        fromCollideMask = ToontownGlobals.PieBitmask
        self.notify.debug('fromCollideMask = %s' % fromCollideMask)
        fromObject.node().setFromCollideMask(fromCollideMask)
        self.handler = CollisionHandlerEvent()
        self.handler.addInPattern('%fn-into')
        base.cTrav.setRespectPrevTransform(True)
        base.cTrav.addCollider(fromObject, self.handler)
        eventName = '%s-into' % fromObject.getName()
        self.accept(eventName, self.swingVineEnter)
        height = base.localAvatar.getHeight()
        self.treasureSphereName = 'treasureCollider'
        center = Point3(0, 0, 0)
        radius = VineTreasure.VineTreasure.RADIUS
        self.treasureCollSphere = CollisionSphere(center[0], center[1], center[2], radius)
        self.treasureCollSphere.setTangible(0)
        self.treasureCollNode = CollisionNode(self.treasureSphereName)
        self.treasureCollNode.setFromCollideMask(ToontownGlobals.WallBitmask)
        self.treasureCollNode.addSolid(self.treasureCollSphere)
        self.treasureCollNodePath = self.torso.attachNewNode(self.treasureCollNode)
        self.treasureHandler = CollisionHandlerEvent()
        self.treasureHandler.addInPattern('%fn-intoTreasure')
        base.cTrav.addCollider(self.treasureCollNodePath, self.treasureHandler)
        eventName = '%s-intoTreasure' % self.treasureCollNodePath.getName()
        self.notify.debug('eventName = %s' % eventName)
        self.accept(eventName, self.treasureEnter)

    def getFocusCameraPos(self, vineIndex, facingRight):
        retPos = Point3(0, 0, 0)
        if self.TwoVineView:
            pos = self.vines[vineIndex].getPos()
            retPos = Point3(self.cameraTwoVineSidePos)
            if vineIndex == 0:
                nextVinePos = self.vines[vineIndex + 1].getPos()
                newX = (pos.getX() + nextVinePos.getX()) / 2.0
                newX -= self.cameraTwoVineAdj
                retPos.setX(newX)
            elif vineIndex == VineGameGlobals.NumVines - 1:
                nextVinePos = self.vines[vineIndex].getPos()
                nextVinePos.setX(nextVinePos.getX() + VineGameGlobals.VineXIncrement)
                newX = (pos.getX() + nextVinePos.getX()) / 2.0
                newX += self.cameraTwoVineAdj
                retPos.setX(newX)
            else:
                otherVineIndex = vineIndex - 1
                if self.lastJumpFacingRight:
                    otherVineIndex = vineIndex + 1
                nextVinePos = self.vines[otherVineIndex].getPos()
                newX = (pos.getX() + nextVinePos.getX()) / 2.0
                if self.lastJumpFacingRight:
                    newX -= self.cameraTwoVineAdj
                else:
                    newX += self.cameraTwoVineAdj
                retPos.setX(newX)
        else:
            pos = self.vines[vineIndex].getPos()
            retPos.setX(pos.getX())
        self.notify.debug('getFocusCameraPos returning %s' % retPos)
        return retPos

    def focusCameraOnVine(self, vineIndex):
        camera.setHpr(0, 0, 0)
        newCameraPos = self.getFocusCameraPos(vineIndex, self.lastJumpFacingRight)
        camera.setPos(newCameraPos)

    def attachLocalToonToVine(self, vineIndex, vineT, focusCameraImmediately = True, playSfx = False):
        self.notify.debug('focusCameraImmediately = %s' % focusCameraImmediately)
        if playSfx:
            self.catchSound.play()
        self.clearLocalPhysics()
        vine = self.vines[vineIndex]
        self.lastJumpVine = -1
        self.lastJumpPos = None
        self.lastJumpT = 0
        if focusCameraImmediately:
            self.focusCameraOnVine(vineIndex)
        self.b_setNewVine(self.localAvId, vineIndex, vineT, self.lastJumpFacingRight)
        return

    def setupJumpingTransitionIval(self, vineIndex):
        self.doingJumpTransition = False
        self.localToonJumpAnimIval = self.createJumpingTransitionIval(vineIndex)
        if self.localToonJumpAnimIval:
            self.doingJumpTransition = True

    def createJumpingTransitionIval(self, vineIndex):
        retval = None
        curInfo = self.vines[vineIndex].getAttachedToonInfo(base.localAvatar.doId)
        if curInfo:
            swingSeq = curInfo[6]
            if swingSeq:
                curFrame = -1
                for i in range(len(swingSeq)):
                    self.notify.debug('testing actor interval i=%d' % i)
                    actorIval = swingSeq[i]
                    if not actorIval.isStopped():
                        testFrame = actorIval.getCurrentFrame()
                        self.notify.debug('actor ival is not stopped, testFrame=%f' % testFrame)
                        if testFrame:
                            curFrame = testFrame
                            break

                if curFrame > -1:
                    duration = 0.25
                    if curFrame > self.ToonMaxRightFrame:
                        desiredFps = abs(self.JumpingFrame - curFrame) / duration
                        playRate = desiredFps / 24.0
                        retval = ActorInterval(base.localAvatar, 'swing', startFrame=curFrame, endFrame=self.JumpingFrame, playRate=playRate)
                    else:
                        numFrames = curFrame + 1
                        numFrames += SwingVine.SwingVine.MaxNumberOfFramesInSwingAnim - self.JumpingFrame + 1
                        desiredFps = numFrames / duration
                        playRate = desiredFps / 24.0
                        toonJump1 = ActorInterval(base.localAvatar, 'swing', startFrame=curFrame, endFrame=0, playRate=playRate)
                        toonJump2 = ActorInterval(base.localAvatar, 'swing', startFrame=SwingVine.SwingVine.MaxNumberOfFramesInSwingAnim - 1, endFrame=self.JumpingFrame, playRate=playRate)
                        retval = Sequence(toonJump1, toonJump2)
        return retval

    def detachLocalToonFromVine(self, vineIndex, facingRight):
        vine = self.vines[vineIndex]
        self.lastJumpVine = vineIndex
        self.lastJumpTime = self.getCurrentGameTime()
        self.curFrame = base.localAvatar.getCurrentFrame()
        curInfo = vine.getAttachedToonInfo(base.localAvatar.doId)
        if curInfo:
            self.lastJumpPos = curInfo[1]
            self.lastJumpT = curInfo[0]
        else:
            self.lastJumpPos = None
            self.lastJumpT = 0
            self.notify.warning('vine %d failed get tooninfo %d' % (vineIndex, base.localAvatar.doId))
        self.setupJumpingTransitionIval(vineIndex)
        self.vines[vineIndex].detachToon(base.localAvatar.doId)
        return

    def treasureEnter(self, entry):
        self.notify.debug('---- treasure Enter ---- ')
        self.notify.debug('%s' % entry)
        name = entry.getIntoNodePath().getName()
        parts = name.split('-')
        if len(parts) < 3:
            self.notify.debug('collided with %s, but returning' % name)
            return
        if not int(parts[1]) == self.doId:
            self.notify.debug("collided with %s, but doId doesn't match" % name)
            return
        treasureNum = int(parts[2])
        self.__treasureGrabbed(treasureNum)

    def swingVineEnter(self, entry):
        self.notify.debug('%s' % entry)
        self.notify.debug('---- swingVine Enter ---- ')
        name = entry.getIntoNodePath().getName()
        parts = name.split('-')
        if len(parts) < 3:
            self.notify.debug('collided with %s, but returning' % name)
            return
        vineIndex = int(parts[1])
        if vineIndex < 0 or vineIndex >= len(self.vines):
            self.notify.warning('invalid vine index %d' % vineIndex)
            return
        if vineIndex == self.lastJumpVine:
            if self.lastJumpPos:
                diff = self.lastJumpPos - entry.getSurfacePoint(render)
                if diff.length() < self.LocalPhysicsRadius:
                    return
            if self.getCurrentGameTime() - self.lastJumpTime < VineGameGlobals.JumpTimeBuffer:
                return
        fallingInfo = self.toonInfo[self.localAvId][8]
        if fallingInfo == self.FallingSpider or fallingInfo == self.FallingBat:
            return
        if abs(self.lastJumpVine - vineIndex) > 1:
            return
        vine = self.vines[vineIndex]
        vineT = vine.calcTFromTubeHit(entry)
        self.attachLocalToonToVine(vineIndex, vineT, False, playSfx=True)
        self.setupAttachingToVineCamIval(vineIndex, self.lastJumpFacingRight)

    def makeOtherToonJump(self, avId, posX, posZ, velX, velZ):
        if avId not in self.otherToonPhysics:
            an = ActorNode('other-physics%s' % avId)
            anp = render.attachNewNode(an)
            base.physicsMgr.attachPhysicalNode(an)
            self.otherToonPhysics[avId] = (an, anp)
        an, anp = self.otherToonPhysics[avId]
        anp.setPos(posX, 0, posZ)
        av = base.cr.doId2do.get(avId)
        if av:
            av.reparentTo(anp)
            av.setPos(-self.toonOffsets[self.localAvId])
            av.pose('swing', self.JumpingFrame)
            self.notify.debug('pose set to swing jumping frame.')
        if velX >= 0:
            anp.setH(-90)
        else:
            anp.setH(90)
        physObject = an.getPhysicsObject()
        physObject.setVelocity(velX, 0, velZ)

    def makeOtherToonFallFromMidair(self, avId, posX, posZ, velX, velZ):
        if avId not in self.otherToonPhysics:
            an = ActorNode('other-physics%s' % avId)
            anp = render.attachNewNode(an)
            base.physicsMgr.attachPhysicalNode(an)
            self.otherToonPhysics[avId] = (an, anp)
        an, anp = self.otherToonPhysics[avId]
        anp.setPos(posX, 0, posZ)
        av = base.cr.doId2do.get(avId)
        if av:
            av.reparentTo(anp)
            av.setPos(-self.toonOffsets[self.localAvId])
        if velX >= 0:
            anp.setH(-90)
        else:
            anp.setH(90)
        physObject = an.getPhysicsObject()
        physObject.setVelocity(velX, 0, velZ)

    def makeLocalToonJump(self, vineIndex, t, pos, normal):
        self.jumpSound.play()
        self.clearChangeFacingInterval()
        self.clearAttachingToVineCamIval()
        an = ActorNode('av-physics')
        anp = render.attachNewNode(an)
        anp.setPos(pos)
        base.localAvatar.reparentTo(anp)
        base.localAvatar.setPos(-self.toonOffsets[self.localAvId])
        if normal.getX() >= 0:
            self.lastJumpFacingRight = True
            anp.setH(-90)
        else:
            anp.setH(90)
            self.lastJumpFacingRight = False
        base.physicsMgr.attachPhysicalNode(an)
        physObject = an.getPhysicsObject()
        velocity = normal * self.JumpSpeed
        velocity *= t
        self.notify.debug('jumping from vine with velocity of %s' % velocity)
        physObject.setVelocity(velocity)
        self.localPhysicsNP = anp
        self.setupCollisions(anp)
        if self.doingJumpTransition:
            self.localToonJumpAnimIval.start()
        else:
            base.localAvatar.pose('swing', self.JumpingFrame)
        self.b_setJumpingFromVine(self.localAvId, vineIndex, self.lastJumpFacingRight, pos[0], pos[2], velocity[0], velocity[2])

    def makeLocalToonFallFromVine(self, fallingInfo):
        self.clearAttachingToVineCamIval()
        self.clearChangeFacingInterval()
        vineIndex, vineInfo = self.getVineAndVineInfo(self.localAvId)
        if vineIndex == -1:
            self.notify.warning('we are not attached to a vine')
            return
        pos = vineInfo[1]
        self.detachLocalToonFromVine(vineIndex, self.lastJumpFacingRight)
        self.clearChangeFacingInterval()
        an = ActorNode('av-physics')
        anp = render.attachNewNode(an)
        anp.setPos(vineInfo[1])
        base.localAvatar.reparentTo(anp)
        base.localAvatar.setPos(-self.toonOffsets[self.localAvId])
        if self.lastJumpFacingRight:
            anp.setH(-90)
        else:
            anp.setH(90)
        base.physicsMgr.attachPhysicalNode(an)
        physObject = an.getPhysicsObject()
        velocity = Vec3(0, 0, -0.1)
        physObject.setVelocity(velocity)
        self.localPhysicsNP = anp
        self.b_setFallingFromVine(self.localAvId, vineIndex, self.lastJumpFacingRight, pos[0], pos[2], velocity[0], velocity[2], fallingInfo)

    def makeLocalToonFallFromMidair(self, fallingInfo):
        vineIndex, vineInfo = self.getVineAndVineInfo(self.localAvId)
        if not vineIndex == -1:
            self.notify.warning(' makeLocalToonFallFromMidair we are still attached to a vine')
            return
        if not self.localPhysicsNP:
            self.notify.warning('self.localPhysicsNP is invalid')
            return
        pos = self.localPhysicsNP.getPos()
        an = self.localPhysicsNP.node()
        physObject = an.getPhysicsObject()
        velocity = Vec3(0, 0, -0.1)
        physObject.setVelocity(velocity)
        self.b_setFallingFromMidair(self.localAvId, self.lastJumpFacingRight, pos[0], pos[2], velocity[0], velocity[2], fallingInfo)

    def changeLocalToonFacing(self, vineIndex, swingVineInfo, newFacingRight):
        self.lastJumpFacingRight = newFacingRight
        self.attachLocalToonToVine(vineIndex, swingVineInfo[0], focusCameraImmediately=False)
        self.setupChangeFacingInterval(vineIndex, newFacingRight)

    def upArrowKeyHandler(self):
        self.sendNewVineTUpdateAsap = True

    def downArrowKeyHandler(self):
        self.sendNewVineTUpdateAsap = True

    def rightArrowKeyHandler(self):
        curInfo = None
        for vineIndex in range(len(self.vines)):
            curInfo = self.vines[vineIndex].getAttachedToonInfo(base.localAvatar.doId)
            if curInfo:
                break

        if not curInfo:
            return
        if vineIndex == len(self.vines) - 1:
            return
        if not self.isInPlayState():
            return
        doJump = True
        if self.ArrowToChangeFacing:
            if not self.lastJumpFacingRight:
                doJump = False
                self.changeLocalToonFacing(vineIndex, curInfo, True)
        if doJump:
            self.detachLocalToonFromVine(vineIndex, 1)
            normal = curInfo[2]
            self.makeLocalToonJump(vineIndex, curInfo[0], curInfo[1], normal)
        return

    def leftArrowKeyHandler(self):
        curInfo = None
        for vineIndex in range(len(self.vines)):
            curInfo = self.vines[vineIndex].getAttachedToonInfo(base.localAvatar.doId)
            if curInfo:
                break

        curInfo = self.vines[vineIndex].getAttachedToonInfo(base.localAvatar.doId)
        if not curInfo:
            return
        if vineIndex == 0:
            return
        if vineIndex == len(self.vines) - 1:
            return
        if not self.isInPlayState():
            return
        doJump = True
        if self.ArrowToChangeFacing:
            if self.lastJumpFacingRight:
                doJump = False
                self.changeLocalToonFacing(vineIndex, curInfo, False)
        if doJump:
            self.detachLocalToonFromVine(vineIndex, 0)
            normal = curInfo[2]
            normal *= -1
            self.makeLocalToonJump(vineIndex, curInfo[0], curInfo[1], normal)
        return

    def b_setNewVine(self, avId, vineIndex, vineT, facingRight):
        self.setNewVine(avId, vineIndex, vineT, facingRight)
        self.d_setNewVine(avId, vineIndex, vineT, facingRight)

    def d_setNewVine(self, avId, vineIndex, vineT, facingRight):
        self.notify.debug('setNewVine avId=%d vineIndex=%s' % (avId, vineIndex))
        self.sendUpdate('setNewVine', [avId,
         vineIndex,
         vineT,
         facingRight])

    def setNewVine(self, avId, vineIndex, vineT, facingRight):
        self.updateToonInfo(avId, vineIndex=vineIndex, vineT=vineT, facingRight=facingRight, climbDir=0, fallingInfo=self.FallingNot)

    def b_setNewVineT(self, avId, vineT, climbDir):
        self.setNewVineT(avId, vineT, climbDir)
        self.d_setNewVineT(avId, vineT, climbDir)

    def d_setNewVineT(self, avId, vineT, climbDir):
        sendIt = False
        curTime = self.getCurrentGameTime()
        if self.sendNewVineTUpdateAsap:
            sendIt = True
        elif curTime - self.lastNewVineTUpdate > 0.2:
            sendIt = True
        if sendIt:
            self.sendUpdate('setNewVineT', [avId, vineT, climbDir])
            self.sendNewVineTUpdateAsap = False
            self.lastNewVineTUpdate = self.getCurrentGameTime()

    def setNewVineT(self, avId, vineT, climbDir):
        self.updateToonInfo(avId, vineT=vineT, climbDir=climbDir)

    def b_setJumpingFromVine(self, avId, vineIndex, facingRight, posX, posZ, velX, velZ):
        self.setJumpingFromVine(avId, vineIndex, facingRight, posX, posZ, velX, velZ)
        self.d_setJumpingFromVine(avId, vineIndex, facingRight, posX, posZ, velX, velZ)

    def d_setJumpingFromVine(self, avId, vineIndex, facingRight, posX, posZ, velX, velZ):
        self.sendUpdate('setJumpingFromVine', [avId,
         vineIndex,
         facingRight,
         posX,
         posZ,
         velX,
         velZ])

    def setJumpingFromVine(self, avId, vineIndex, facingRight, posX, posZ, velX, velZ):
        self.updateToonInfo(avId, vineIndex=-1, facingRight=facingRight, posX=posX, posZ=posZ, velX=velX, velZ=velZ)

    def b_setFallingFromVine(self, avId, vineIndex, facingRight, posX, posZ, velX, velZ, fallingInfo):
        self.setFallingFromVine(avId, vineIndex, facingRight, posX, posZ, velX, velZ, fallingInfo)
        self.d_setFallingFromVine(avId, vineIndex, facingRight, posX, posZ, velX, velZ, fallingInfo)

    def d_setFallingFromVine(self, avId, vineIndex, facingRight, posX, posZ, velX, velZ, fallingInfo):
        self.sendUpdate('setFallingFromVine', [avId,
         vineIndex,
         facingRight,
         posX,
         posZ,
         velX,
         velZ,
         fallingInfo])

    def setFallingFromVine(self, avId, vineIndex, facingRight, posX, posZ, velX, velZ, fallingInfo):
        self.updateToonInfo(avId, vineIndex=-1, facingRight=facingRight, posX=posX, posZ=posZ, velX=velX, velZ=velZ, fallingInfo=fallingInfo)

    def b_setFallingFromMidair(self, avId, facingRight, posX, posZ, velX, velZ, fallingInfo):
        self.setFallingFromMidair(avId, facingRight, posX, posZ, velX, velZ, fallingInfo)
        self.d_setFallingFromMidair(avId, facingRight, posX, posZ, velX, velZ, fallingInfo)

    def d_setFallingFromMidair(self, avId, facingRight, posX, posZ, velX, velZ, fallingInfo):
        self.sendUpdate('setFallingFromMidair', [avId,
         facingRight,
         posX,
         posZ,
         velX,
         velZ,
         fallingInfo])

    def setFallingFromMidair(self, avId, facingRight, posX, posZ, velX, velZ, fallingInfo):
        self.updateToonInfo(avId=avId, facingRight=facingRight, posX=posX, posZ=posZ, velX=velX, velZ=velZ, fallingInfo=fallingInfo)

    def d_setFallingPos(self, avId, posX, posZ):
        self.sendUpdate('setFallingPos', [avId, posX, posZ])

    def setFallingPos(self, avId, posX, posZ):
        self.updateToonInfo(avId, posX=posX, posZ=posZ)

    def __treasureGrabbed(self, treasureNum):
        self.treasures[treasureNum].showGrab()
        self.grabSound.play()
        self.sendUpdate('claimTreasure', [treasureNum])

    def setTreasureGrabbed(self, avId, treasureNum):
        if not self.hasLocalToon:
            return
        self.notify.debug('treasure %s grabbed by %s' % (treasureNum, avId))
        if avId != self.localAvId:
            self.treasures[treasureNum].showGrab()
        i = self.avIdList.index(avId)
        self.scores[i] += 1
        self.scorePanels[i].setScore(self.scores[i])

    def setScore(self, avId, score):
        if not self.hasLocalToon:
            return
        i = self.avIdList.index(avId)
        if hasattr(self, 'scorePanels'):
            self.scores[i] += score
            self.scorePanels[i].setScore(score)

    def timerExpired(self):
        self.notify.debug('game timer expired')
        if not VineGameGlobals.EndlessGame:
            if hasattr(self, 'gameFSM'):
                self.gameFSM.request('showScores')

    def allAtEndVine(self):
        if not self.hasLocalToon:
            return
        self.notify.debug('all at end vine')
        if not VineGameGlobals.EndlessGame:
            self.gameFSM.request('showScores')

    def clearChangeFacingInterval(self):
        if self.changeFacingInterval:
            self.changeFacingInterval.pause()
            del self.changeFacingInterval
        self.changeFacingInterval = None
        return

    def setupChangeFacingInterval(self, vineIndex, newFacingRight):
        self.clearChangeFacingInterval()
        self.changeFacingInterval = Sequence()
        if not (vineIndex == 0 or vineIndex == VineGameGlobals.NumVines - 1):
            destPos = self.getFocusCameraPos(vineIndex, newFacingRight)
            self.changeFacingInterval.append(LerpPosInterval(base.camera, 0.5, destPos))
            self.changeFacingInterval.append(Func(self.clearChangeFacingInterval))
        self.changeFacingInterval.start()

    def clearAttachingToVineCamIval(self):
        if self.attachingToVineCamIval:
            self.attachingToVineCamIval.pause()
            del self.attachingToVineCamIval
        self.attachingToVineCamIval = None
        return

    def setupAttachingToVineCamIval(self, vineIndex, facingRight):
        self.clearAttachingToVineCamIval()
        self.attachingToVineCamIval = Sequence()
        destPos = self.getFocusCameraPos(vineIndex, facingRight)
        self.attachingToVineCamIval.append(LerpPosInterval(base.camera, 0.5, destPos))
        self.attachingToVineCamIval.append(Func(self.clearAttachingToVineCamIval))
        self.attachingToVineCamIval.start()

    def createRadar(self):
        self.cCamera = render.attachNewNode('cCamera')
        self.cCamNode = Camera('cCam')
        self.cCamNode.setCameraMask(VineGameGlobals.RadarCameraBitmask)
        self.cLens = PerspectiveLens()
        xFov = 40
        yFov = 2.5
        self.cLens.setFov(xFov, yFov)
        self.cLens.setNear(0.1)
        self.cLens.setFar(1300.0)
        self.cCamNode.setLens(self.cLens)
        self.cCamNode.setScene(render)
        self.cCam = self.cCamera.attachNewNode(self.cCamNode)
        self.cCam.setPos(300, -850, 16.3)
        endY = yFov / xFov
        self.endZRadar = 0.09375
        self.cDr = base.win.makeDisplayRegion(0, 1, 0, self.endZRadar)
        self.cDr.setSort(1)
        self.cDr.setClearDepthActive(1)
        self.cDr.setClearColorActive(1)
        self.cDr.setClearColor(Vec4(0.85, 0.95, 0.95, 1))
        self.cDr.setCamera(self.cCam)
        self.radarSeparator = DirectFrame(relief=None, image=DGG.getDefaultDialogGeom(), image_color=(0.2, 0.0, 0.8, 1), image_scale=(2.65, 1.0, 0.01), pos=(0, 0, -0.8125))
        self.oldBaseCameraMask = base.camNode.getCameraMask()
        base.camNode.setCameraMask(BitMask32.bit(0))
        return

    def destroyRadar(self):
        base.win.removeDisplayRegion(self.cDr)
        self.cCamera.removeNode()
        del self.cCamera
        del self.cCamNode
        del self.cLens
        del self.cCam
        del self.cDr
        self.radarSeparator.destroy()
        del self.radarSeparator
        base.camNode.setCameraMask(self.oldBaseCameraMask)

    def updateRadar(self):
        for avId in self.headFrames:
            av = base.cr.doId2do.get(avId)
            headFrameShown = False
            if av:
                avPos = av.getPos(render)
                newPoint = self.mapRadarToAspect2d(render, avPos)
                if newPoint:
                    headFrameShown = True
                    self.headFrames[avId].setPos(newPoint[0], newPoint[1], newPoint[2])
            if headFrameShown:
                self.headFrames[avId].show()
            else:
                self.headFrames[avId].hide()

    def mapRadarToAspect2d(self, node, point):
        if point[0] > 26:
            pass
        p3 = self.cCam.getRelativePoint(node, point)
        p2 = Point2()
        if not self.cLens.project(p3, p2):
            return None
        r2d = Point3(p2[0], 0, p2[1])
        a2d = aspect2d.getRelativePoint(render2d, r2d)
        zAspect2DRadar = self.endZRadar * 2.0 - 1
        oldZ = a2d.getZ()
        newZ = (oldZ + 1) / 2.0 * (zAspect2DRadar + 1)
        newZ -= 1
        a2d.setZ(newZ)
        return a2d

    def localToonHitSpider(self, colEntry):
        self.notify.debug('toonHitSpider')
        if self.toonInfo[self.localAvId][0] == -1:
            fallingInfo = self.toonInfo[self.localAvId][8]
            if not (fallingInfo == self.FallingBat or fallingInfo == self.FallingSpider):
                self.spiderHitSound.play()
                self.makeLocalToonFallFromMidair(self.FallingSpider)
        else:
            self.spiderHitSound.play()
            self.makeLocalToonFallFromVine(self.FallingSpider)

    def localToonHitBat(self, colEntry):
        self.notify.debug('toonHitBat')
        if self.toonInfo[self.localAvId][0] == VineGameGlobals.NumVines - 1:
            return
        if self.toonInfo[self.localAvId][0] == -1:
            self.batHitMidairSound.play()
            fallingInfo = self.toonInfo[self.localAvId][8]
            if not (fallingInfo == self.FallingBat or fallingInfo == self.FallingSpider):
                self.makeLocalToonFallFromMidair(self.FallingBat)
        else:
            self.batHitVineSound.play()
            self.makeLocalToonFallFromVine(self.FallingBat)

    def toonHitSomething(self, colEntry):
        if not self.isInPlayState():
            return
        intoName = colEntry.getIntoNodePath().getName()
        if 'spider' in intoName:
            self.localToonHitSpider(colEntry)
        elif 'bat' in intoName:
            self.localToonHitBat(colEntry)

    def setVineSections(self, vineSections):
        self.vineSections = vineSections

    def setupVineCourse(self):
        vineIndex = 0
        for section in self.vineSections:
            for vineInfo in VineGameGlobals.CourseSections[section]:
                length, baseAngle, vinePeriod, spiderPeriod = vineInfo
                posX = vineIndex * VineGameGlobals.VineXIncrement
                newVine = SwingVine.SwingVine(vineIndex, posX, 0, VineGameGlobals.VineHeight, length=length, baseAngle=baseAngle, period=vinePeriod, spiderPeriod=spiderPeriod)
                self.vines.append(newVine)
                vineIndex += 1

    def loadBats(self):
        self.bats = []
        szId = self.getSafezoneId()
        self.batInfo = VineGameGlobals.BatInfo[szId]
        batIndex = 0
        for batTuple in self.batInfo:
            newBat = VineBat.VineBat(batIndex, self.batInfo[batIndex][0])
            xPos = VineGameGlobals.VineXIncrement * VineGameGlobals.NumVines + 100
            newBat.setX(xPos)
            self.bats.append(newBat)
            batIndex += 1

    def createBatIvals(self):
        self.batIvals = []
        for batIndex in range(len(self.bats)):
            newBatIval = self.createBatIval(batIndex)
            self.batIvals.append(newBatIval)

    def startBatIvals(self):
        for batIval in self.batIvals:
            batIval.start()

    def destroyBatIvals(self):
        for batIval in self.batIvals:
            batIval.finish()

        self.batIvals = []

    def createBatIval(self, batIndex):
        timeToTraverseField = self.batInfo[batIndex][0]
        initialDelay = self.batInfo[batIndex][1]
        startMultiplier = 1
        if len(self.batInfo[batIndex]) >= 3:
            startMultiplier = 0.25
        batIval = Sequence()
        batIval.append(Wait(initialDelay))
        batIval.append(Func(self.bats[batIndex].startFlying))
        startX = VineGameGlobals.VineXIncrement * VineGameGlobals.NumVines
        endX = -VineGameGlobals.VineXIncrement
        firstInterval = True
        while batIval.getDuration() < VineGameGlobals.GameDuration:
            batHeight = self.randomNumGen.randrange(VineGameGlobals.BatMinHeight, VineGameGlobals.BatMaxHeight)
            batIval.append(Func(self.bats[batIndex].startLap))
            if firstInterval:
                newIval = LerpPosInterval(self.bats[batIndex], duration=timeToTraverseField * startMultiplier, pos=Point3(endX, 0, batHeight), startPos=Point3(startX * startMultiplier, 0, batHeight))
            else:
                newIval = LerpPosInterval(self.bats[batIndex], duration=timeToTraverseField, pos=Point3(endX, 0, batHeight), startPos=Point3(startX, 0, batHeight))
            batIval.append(newIval)
            firstInterval = False

        batIval.append(Func(self.bats[batIndex].stopFlying))
        return batIval

    def isInPlayState(self):
        if not self.gameFSM.getCurrentState():
            return False
        if not self.gameFSM.getCurrentState().getName() == 'play':
            return False
        return True

    def getIntroTrack(self):
        retval = Sequence()
        toonTakeoffs = Parallel()
        didCameraMove = False
        for index in range(len(self.avIdList)):
            avId = self.avIdList[index]
            if avId != self.localAvId:
                continue
            oneSeq = Sequence()
            oneSeqAndHowl = Parallel()
            av = base.cr.doId2do.get(avId)
            if av:
                toonOffset = self.calcToonOffset(av)
                platformPos = self.startPlatform.getPos()
                endPos = self.vines[0].getPos()
                endPos.setZ(endPos.getZ() - toonOffset.getZ() - VineGameGlobals.VineStartingT * self.vines[0].cableLength)
                xPos = platformPos[0] - 0.5
                takeOffPos = Point3(xPos, platformPos[1], platformPos[2])
                leftPos = Point3(xPos - 27, platformPos[1], platformPos[2])
                self.notify.debug('leftPos = %s platformPos=%s' % (leftPos, platformPos))
                startRunningPos = Point3(takeOffPos)
                startRunningPos.setX(startRunningPos.getX() - 7)
                oneSeq.append(Func(av.dropShadow.show))
                oneSeq.append(Func(av.setH, -90))
                oneSeq.append(Func(av.setPos, takeOffPos[0], takeOffPos[1], takeOffPos[2]))
                exclamationSfx = av.getDialogueSfx('exclamation', 0)
                oneSeq.append(Parallel(ActorInterval(av, 'confused', duration=3)))
                questionSfx = av.getDialogueSfx('question', 0)
                oneSeq.append(Parallel(ActorInterval(av, 'think', duration=3.0), SoundInterval(questionSfx, duration=3)))
                oneSeq.append(Func(av.setH, 90))
                oneSeq.append(Func(av.setPlayRate, 1, 'walk'))
                oneSeq.append(Func(av.loop, 'walk'))
                oneSeq.append(Parallel(LerpPosInterval(av, pos=leftPos, duration=5.25), SoundInterval(av.soundWalk, loop=1, duration=5.25)))
                oneSeq.append(Func(av.setH, -90))
                oneSeq.append(Func(av.loop, 'run'))
                oneSeq.append(Parallel(LerpPosInterval(av, pos=takeOffPos, duration=2.5), SoundInterval(av.soundRun, loop=1, duration=2.5)))
                oneSeq.append(Func(av.dropShadow.hide))
                howlTime = oneSeq.getDuration()
                oneSeq.append(Parallel(LerpPosInterval(av, pos=endPos, duration=0.5), Func(av.pose, 'swing', self.JumpingFrame)))
                attachingToVineSeq = Sequence(ActorInterval(av, 'swing', startFrame=self.JumpingFrame, endFrame=143, playRate=2.0), ActorInterval(av, 'swing', startFrame=0, endFrame=86, playRate=2.0))
                attachingToVine = Parallel(attachingToVineSeq, SoundInterval(self.catchSound))
                if didCameraMove:
                    oneSeq.append(attachingToVine)
                else:
                    attachAndMoveCam = Parallel(attachingToVine, LerpPosInterval(base.camera, pos=self.getFocusCameraPos(0, True), duration=2))
                    oneSeq.append(attachAndMoveCam)
                oneSeq.append(Func(av.setPos, 0, 0, 0))
                oneSeq.append(Func(av.setH, 0))
                oneSeq.append(Func(self.vines[0].attachToon, avId, VineGameGlobals.VineStartingT, self.lastJumpFacingRight, setupAnim=False))
                oneSeq.append(Func(self.vines[0].updateAttachedToons))
                howlSfx = av.getDialogueSfx('special', 0)
                howlSeq = Sequence(Wait(howlTime), SoundInterval(howlSfx))
                exclamationSeq = Sequence(Wait(0.5), SoundInterval(exclamationSfx))
                oneSeqAndHowl = Parallel(oneSeq, howlSeq, exclamationSeq)
            toonTakeoffs.append(oneSeqAndHowl)

        retval.append(toonTakeoffs)
        return retval

    def doEndingTrackTask(self, avId):
        taskName = 'VineGameEnding-%s' % avId
        if avId not in self.endingTracks:
            taskMgr.doMethodLater(0.5, self.setupEndingTrack, taskName, extraArgs=(avId,))
            self.endingTrackTaskNames.append(taskName)

    def debugCameraPos(self):
        self.notify.debug('cameraPos = %s' % base.camera.getPos())

    def setupEndingTrack(self, avId):
        if avId in self.endingTracks:
            self.notify.warning('setupEndingTrack duplicate call avId=%d' % avId)
            return
        if len(self.vines) == 0:
            return
        endVine = VineGameGlobals.NumVines - 1
        platformPos = self.endPlatform.getPos()
        avIndex = self.avIdList.index(avId)
        landingPos = Point3(platformPos)
        landingPos.setX(landingPos.getX() + avIndex * 2)
        endingTrack = Sequence()
        av = base.cr.doId2do.get(avId)
        avPos = av.getPos(render)
        cameraPos = base.camera.getPos()
        self.notify.debug('avPos=%s cameraPos=%s' % (avPos, base.camera.getPos()))
        if av:
            midX = landingPos[0]
            midZ = platformPos[2] + 6
            jumpingTransition = self.createJumpingTransitionIval(endVine)
            endingTrack.append(Func(self.vines[endVine].detachToon, avId))
            endingTrack.append(Func(av.wrtReparentTo, render))
            endingTrack.append(Func(self.debugCameraPos))
            endingTrack.append(Func(av.loop, 'jump-idle'))
            landingIval = Parallel(ProjectileInterval(av, startPos=av.getPos(render), endZ=landingPos[2], wayPoint=Point3(midX, 0, midZ), timeToWayPoint=1))
            endingTrack.append(landingIval)
            endingTrack.append(Func(av.dropShadow.show))
            endingTrack.append(Func(av.play, 'jump-land'))
            endingTrack.append(Func(self.winSound.play))
            endingTrack.append(Func(av.loop, 'victory'))
        self.endingTracks[avId] = endingTrack
        endingTrack.start()
        return Task.done

    def cleanupEndingTracks(self):
        for taskName in self.endingTrackTaskNames:
            taskMgr.remove(taskName)

        for endingTrack in list(self.endingTracks.values()):
            endingTrack.finish
            del endingTrack

        self.endingTracks = {}
