import math
import random
import time
from pandac.PandaModules import TextNode, BitMask32, Point3, Vec3, Vec4, deg2Rad, Mat3, NodePath, VBase4, OdeTriMeshData, OdeTriMeshGeom, OdeRayGeom, CollisionTraverser, CollisionSegment, CollisionNode, CollisionHandlerQueue
from direct.distributed import DistributedObject
from direct.directnotify import DirectNotifyGlobal
from otp.otpbase import OTPGlobals
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownTimer
from direct.gui.DirectGui import DirectWaitBar, DGG, DirectLabel
from direct.task import Task
from direct.fsm.FSM import FSM
from toontown.minigame import ArrowKeys
from direct.showbase import PythonUtil
from toontown.golf import BuildGeometry
from toontown.golf import DistributedPhysicsWorld
from toontown.golf import GolfGlobals
from direct.interval.IntervalGlobal import Sequence, Parallel, LerpScaleInterval, LerpFunctionInterval, Func, Wait, SoundInterval, ParallelEndTogether, LerpPosInterval, ActorInterval, LerpPosHprInterval, LerpColorScaleInterval, WaitInterval
from direct.actor import Actor
from toontown.golf import GolfHoleBase
from toontown.distributed import DelayDelete

class DistributedGolfHole(DistributedPhysicsWorld.DistributedPhysicsWorld, FSM, GolfHoleBase.GolfHoleBase):
    defaultTransitions = {'Off': ['Cleanup', 'ChooseTee', 'WatchTee'],
     'ChooseTee': ['Aim', 'Cleanup'],
     'WatchTee': ['WatchAim',
                  'Cleanup',
                  'WatchTee',
                  'ChooseTee',
                  'Aim'],
     'Wait': ['Aim',
              'WatchAim',
              'Playback',
              'Cleanup',
              'ChooseTee',
              'WatchTee'],
     'Aim': ['Shoot',
             'Playback',
             'Cleanup',
             'Aim',
             'WatchAim'],
     'WatchAim': ['WatchAim',
                  'WatchShoot',
                  'Playback',
                  'Cleanup',
                  'Aim',
                  'ChooseTee',
                  'WatchTee'],
     'Playback': ['Wait',
                  'Aim',
                  'WatchAim',
                  'Cleanup',
                  'ChooseTee',
                  'WatchTee'],
     'Cleanup': ['Off']}
    id = 0
    notify = directNotify.newCategory('DistributedGolfHole')
    unlimitedAimTime = base.config.GetBool('unlimited-aim-time', 0)
    unlimitedTeeTime = base.config.GetBool('unlimited-tee-time', 0)
    golfPowerSpeed = base.config.GetDouble('golf-power-speed', 3)
    golfPowerExponent = base.config.GetDouble('golf-power-exponent', 0.75)
    DefaultCamP = -16
    MaxCamP = -90

    def __init__(self, cr):
        self.notify.debug('Hole Init')
        DistributedPhysicsWorld.DistributedPhysicsWorld.__init__(self, base.cr)
        GolfHoleBase.GolfHoleBase.__init__(self, 1)
        FSM.__init__(self, 'Golf_%s_FSM' % self.id)
        self.currentGolfer = 0
        self.ballDict = {}
        self.ballShadowDict = {}
        self.holeNodes = []
        self.golfCourse = None
        self.golfCourseRequest = None
        self.holePositions = []
        self.timer = None
        self.teeTimer = None
        self.aimStart = None
        self.titleLabel = None
        self.teeInstructions = None
        self.aimInstructions = None
        self.powerReminder = None
        self.lastTimeHeadingSent = 0
        self.lastTempHeadingSent = 0
        self.holdCycleTime = 0.0
        self.inPlayBack = 0
        self.swingInterval = None
        self.sfxInterval = None
        self.isLookingAtPutt = False
        self.clubs = {}
        self.camInterval = None
        self.flyOverInterval = None
        self.needToDoFlyOver = True
        self.translucentLastFrame = []
        self.translucentCurFrame = []
        self.localMissedSwings = 0
        self.localToonHitControl = False
        self.warningInterval = None
        self.playBackDelayDelete = None
        self.aimMomentum = 0.0
        self.lastBumpSfxPos = Point3(0, 0, 0)
        self.__textGen = TextNode('golfHoleText')
        self.__textGen.setFont(ToontownGlobals.getSignFont())
        self.__textGen.setAlign(TextNode.ACenter)
        if TTLocalizer.getLanguage() in ['castillian',
         'japanese',
         'german',
         'portuguese',
         'french']:
            self.__textGen.setGlyphScale(0.7)
        self.avIdList = []
        self.enterAimStart = 0
        return

    def generate(self):
        self.notify.debug('Hole Generate')
        DistributedPhysicsWorld.DistributedPhysicsWorld.generate(self)
        self.golfPowerTaskName = self.uniqueName('updateGolfPower')

    def announceGenerate(self):
        DistributedPhysicsWorld.DistributedPhysicsWorld.announceGenerate(self)
        self.setup()
        self.sendReady()
        self.request('Off')
        index = 1
        for avId in self.avIdList:
            self.createBall(avId, index)
            self.createClub(avId)
            index += 1

        if self.avIdList:
            avId = self.avIdList[0]
            self.currentGolfer = avId
        self.currentGolferActive = False

    def delete(self):
        self.removePlayBackDelayDelete()
        self.request('Cleanup')
        taskMgr.remove(self.golfPowerTaskName)
        DistributedPhysicsWorld.DistributedPhysicsWorld.delete(self)
        GolfHoleBase.GolfHoleBase.delete(self)
        if hasattr(self, 'perfectIval'):
            self.perfectIval.pause()
            del self.perfectIval
        self.golfCourse = None
        if self.teeInstructions:
            self.teeInstructions.destroy()
            self.teeInstructions = None
        if self.aimInstructions:
            self.aimInstructions.destory()
            self.aimInstructions = None
        if self.powerReminder:
            self.powerReminder.destroy()
            self.powerReminder = None
        if self.swingInterval:
            self.swingInterval.pause()
            self.swingInterval = None
        if self.sfxInterval:
            self.sfxInterval.pause()
            self.sfxInterval = None
        if self.camInterval:
            self.camInterval.pause()
            self.camInterval = None
        for club in self.clubs:
            self.clubs[club].removeNode()

        del self.clubs
        if hasattr(self, 'scoreBoard'):
            if hasattr(self.scoreBoard, 'maximizeB'):
                if self.scoreBoard.maximizeB:
                    self.scoreBoard.maximizeB.hide()
        if not self.titleLabel == None:
            self.titleLabel.destroy()
            self.notify.debug('Deleted title label')
        self.notify.debug('Delete function')
        if self.flyOverInterval:
            self.flyOverInterval.pause()
        self.flyOverInterval = None
        for key in self.ballShadowDict:
            self.ballShadowDict[key].removeNode()

        self.dropShadowModel.removeNode()
        return

    def sendReady(self):
        self.sendUpdate('setAvatarReadyHole', [])

    def createClub(self, avId):
        club = NodePath('club-%s' % avId)
        clubModel = loader.loadModel('phase_6/models/golf/putter')
        clubModel.reparentTo(club)
        clubModel.setR(clubModel, 45)
        self.clubs[avId] = club

    def attachClub(self, avId, pointToBall = False):
        club = self.clubs[avId]
        if club:
            av = base.cr.doId2do.get(avId)
            if av:
                av.useLOD(1000)
                lHand = av.getLeftHands()[0]
                club.setPos(0, 0, 0)
                club.reparentTo(lHand)
                netScale = club.getNetTransform().getScale()[1]
                counterActToonScale = lHand.find('**/counteractToonScale')
                if counterActToonScale.isEmpty():
                    counterActToonScale = lHand.attachNewNode('counteractToonScale')
                    counterActToonScale.setScale(1 / netScale)
                    self.notify.debug('creating counterActToonScale for %s' % av.getName())
                club.reparentTo(counterActToonScale)
                club.setX(-0.25 * netScale)
                if pointToBall:
                    club.lookAt(self.clubLookatSpot)

    def createToonRay(self):
        self.toonRay = OdeRayGeom(self.space, 10.0)
        self.toonRay.setCollideBits(BitMask32(16777215))
        self.toonRay.setCategoryBits(BitMask32(0))
        self.toonRay.setRotation(Mat3(1, 0, 0, 0, -1, 0, 0, 0, -1))
        self.space.setCollideId(self.toonRay, GolfGlobals.TOON_RAY_COLLIDE_ID)
        self.rayList.append(self.toonRay)

    def createSkyRay(self):
        self.skyRay = OdeRayGeom(self.space, 100.0)
        self.skyRay.setCollideBits(BitMask32(240))
        self.skyRay.setCategoryBits(BitMask32(0))
        self.skyRay.setRotation(Mat3(1, 0, 0, 0, -1, 0, 0, 0, -1))
        self.space.setCollideId(self.skyRay, 78)
        self.rayList.append(self.skyRay)

    def createCameraRay(self):
        self.cameraRay = OdeRayGeom(self.space, 30.0)
        self.cameraRay.setCollideBits(BitMask32(8388608))
        self.cameraRay.setCategoryBits(BitMask32(0))
        self.space.setCollideId(self.cameraRay, GolfGlobals.CAMERA_RAY_COLLIDE_ID)
        self.cameraRayNodePath = self.terrainModel.attachNewNode('cameraRayNodePath')
        self.rayList.append(self.cameraRay)

    def loadLevel(self):
        GolfHoleBase.GolfHoleBase.loadLevel(self)
        self.teeNodePath = self.terrainModel.find('**/tee0')
        if self.teeNodePath.isEmpty():
            teePos = Vec3(0, 0, 10)
        else:
            teePos = self.teeNodePath.getPos()
            teePos.setZ(teePos.getZ() + GolfGlobals.GOLF_BALL_RADIUS)
            self.notify.debug('teeNodePath heading = %s' % self.teeNodePath.getH())
        self.teePositions = [teePos]
        teeIndex = 1
        teeNode = self.terrainModel.find('**/tee%d' % teeIndex)
        while not teeNode.isEmpty():
            teePos = teeNode.getPos()
            teePos.setZ(teePos.getZ() + GolfGlobals.GOLF_BALL_RADIUS)
            self.teePositions.append(teePos)
            self.notify.debug('teeNodeP heading = %s' % teeNode.getH())
            teeIndex += 1
            teeNode = self.terrainModel.find('**/tee%d' % teeIndex)

        self.holeBottomNodePath = self.terrainModel.find('**/holebottom0')
        if self.holeBottomNodePath.isEmpty():
            self.holeBottomPos = Vec3(*self.holeInfo['holePos'][0])
        else:
            self.holeBottomPos = self.holeBottomNodePath.getPos()
        self.holePositions.append(self.holeBottomPos)
        minHard = Point3(0, 0, 0)
        maxHard = Point3(0, 0, 0)
        self.hardSurfaceNodePath.calcTightBounds(minHard, maxHard)
        centerX = (minHard[0] + maxHard[0]) / 2.0
        centerY = (minHard[1] + maxHard[1]) / 2.0
        heightX = (centerX - minHard[0]) / math.tan(deg2Rad(23))
        heightY = (centerY - minHard[1]) / math.tan(deg2Rad(18))
        height = max(heightX, heightY)
        self.camTopViewPos = Point3(centerX, centerY, height)
        self.camTopViewHpr = Point3(0, -90, 0)
        self.createRays()
        self.createToonRay()
        self.createCameraRay()

    def createLocatorDict(self):
        self.locDict = {}
        locatorNum = 1
        curNodePath = self.hardSurfaceNodePath.find('**/locator%d' % locatorNum)
        while not curNodePath.isEmpty():
            self.locDict[locatorNum] = curNodePath
            locatorNum += 1
            curNodePath = self.hardSurfaceNodePath.find('**/locator%d' % locatorNum)

    def loadBlockers(self):
        loadAll = base.config.GetBool('golf-all-blockers', 0)
        self.createLocatorDict()
        self.blockerNums = self.holeInfo['blockers']
        for locatorNum in self.locDict:
            if locatorNum in self.blockerNums or loadAll:
                locator = self.locDict[locatorNum]
                locatorParent = locator.getParent()
                locator.getChildren().wrtReparentTo(locatorParent)
            else:
                self.locDict[locatorNum].removeNode()

        self.hardSurfaceNodePath.flattenStrong()

    def loadSounds(self):
        self.hitBallSfx = loader.loadSfx('phase_6/audio/sfx/Golf_Hit_Ball.mp3')
        self.holeInOneSfx = loader.loadSfx('phase_6/audio/sfx/Golf_Hole_In_One.mp3')
        self.holeInTwoPlusSfx = loader.loadSfx('phase_4/audio/sfx/MG_sfx_vine_game_fall.mp3')
        self.ballGoesInStartSfx = loader.loadSfx('phase_6/audio/sfx/Golf_Ball_Goes_In_Start.wav')
        self.ballGoesInLoopSfx = loader.loadSfx('phase_6/audio/sfx/Golf_Ball_Goes_In_Loop.wav')
        self.ballGoesToRestSfx = loader.loadSfx('phase_6/audio/sfx/Golf_Ball_Rest_In_Cup.mp3')
        self.kickedOutSfx = loader.loadSfx('phase_6/audio/sfx/Golf_Sad_Noise_Kicked_Off_Hole.mp3')
        self.crowdBuildupSfx = []
        self.crowdApplauseSfx = []
        self.crowdMissSfx = []
        for i in xrange(4):
            self.crowdBuildupSfx.append(loader.loadSfx('phase_6/audio/sfx/Golf_Crowd_Buildup.mp3'))
            self.crowdApplauseSfx.append(loader.loadSfx('phase_6/audio/sfx/Golf_Crowd_Applause.mp3'))
            self.crowdMissSfx.append(loader.loadSfx('phase_6/audio/sfx/Golf_Crowd_Miss.mp3'))

        self.bumpHardSfx = loader.loadSfx('phase_6/audio/sfx/Golf_Hit_Barrier_3.mp3')
        self.bumpMoverSfx = loader.loadSfx('phase_4/audio/sfx/Golf_Hit_Barrier_2.mp3')
        self.bumpWindmillSfx = loader.loadSfx('phase_4/audio/sfx/Golf_Hit_Barrier_1.mp3')

    def setup(self):
        self.notify.debug('setup golf hole')
        self.loadLevel()
        self.loadSounds()
        self.camMove = 0
        self.arrowKeys = ArrowKeys.ArrowKeys()
        self.arrowKeys.setPressHandlers([None,
         None,
         self.__leftArrowPressed,
         self.__rightArrowPressed,
         self.__beginTossGolf])
        self.arrowKeys.setReleaseHandlers([None,
         None,
         None,
         None,
         self.__endTossGolf])
        self.targets = render.attachNewNode('targetGameTargets')
        self.ballFollow = render.attachNewNode('nodeAtBall')
        self.startingTeeHeading = self.teeNodePath.getH()
        self.ballFollow.setH(self.startingTeeHeading)
        self.ballFollowToonSpot = self.ballFollow.attachNewNode('toonAimSpot')
        self.ballFollowToonSpot.setX(-2.0)
        self.ballFollowToonSpot.setY(0)
        self.ballFollowToonSpot.setH(-90)
        self.clubLookatSpot = self.ballFollow.attachNewNode('clubLookat')
        self.clubLookatSpot.setY(-(GolfGlobals.GOLF_BALL_RADIUS + 0.1))
        camera.reparentTo(self.ballFollow)
        self.camPosBallFollow = Point3(0.0, -23.0, 12.0)
        self.camHprBallFollow = Point3(0, -16.0, 0)
        camera.setPos(self.camPosBallFollow)
        camera.setHpr(self.camHprBallFollow)
        if self.holeBottomNodePath.isEmpty():
            holePositions = self.holePositions
            for index in xrange(len(holePositions)):
                holePos = holePositions[index]
                targetNodePathGeom, t1, t2 = BuildGeometry.addCircleGeom(self.targets, 16, 1)
                targetNodePathGeom.setPos(holePos)
                targetNodePathGeom.setBin('ground', 0)
                targetNodePathGeom.setDepthWrite(False)
                targetNodePathGeom.setDepthTest(False)
                targetNodePathGeom.setTransparency(TransparencyAttrib.MAlpha)
                targetNodePathGeom.setColorScale(0.0, 0.0, 0.0, 1.0)
                self.holeNodes.append(targetNodePathGeom)
                holeSphere = CollisionSphere(0, 0, 0, 1)
                holeSphere.setTangible(1)
                holeCNode = CollisionNode('Hole')
                holeCNode.addSolid(holeSphere)
                holeC = targetNodePathGeom.attachNewNode(holeCNode)
                holeC.show()

            holeC.setCollideMask(ToontownGlobals.PieBitmask)
        toon = base.localAvatar
        toon.setPos(0.0, 0.0, -100.0)
        toon.b_setAnimState('neutral', 1.0)
        self.pollingCtrl = 0
        self.timeLastCtrl = 0.0
        self.powerBar = DirectWaitBar(guiId='launch power bar', pos=(0.0, 0, -0.65), relief=DGG.SUNKEN, frameSize=(-2.0,
         2.0,
         -0.2,
         0.2), borderWidth=(0.02, 0.02), scale=0.25, range=100, sortOrder=50, frameColor=(0.5, 0.5, 0.5, 0.5), barColor=(1.0, 0.0, 0.0, 1.0), text='', text_scale=0.26, text_fg=(1, 1, 1, 1), text_align=TextNode.ACenter, text_pos=(0, -0.05))
        self.power = 0
        self.powerBar['value'] = self.power
        self.powerBar.hide()
        self.accept('tab', self.tabKeyPressed)
        self.putAwayAllToons()
        base.transitions.irisOut(t=0)
        self.dropShadowModel = loader.loadModel('phase_3/models/props/drop_shadow')
        self.dropShadowModel.setColor(0, 0, 0, 0.5)
        self.dropShadowModel.flattenMedium()
        self.dropShadowModel.hide()
        return

    def switchToAnimState(self, animStateName, forced = False):
        curAnimState = base.localAvatar.animFSM.getCurrentState()
        curAnimStateName = ''
        if curAnimState:
            curAnimStateName = curAnimState.getName()
        if curAnimStateName != animStateName or forced:
            base.localAvatar.b_setAnimState(animStateName)

    def __aimTask(self, task):
        self.attachClub(self.currentGolfer, True)
        x = -math.sin(self.ballFollow.getH() * 0.0174532925)
        y = math.cos(self.ballFollow.getH() * 0.0174532925)
        dt = globalClock.getDt()
        b = self.curGolfBall()
        forceMove = 500
        forceMoveDt = forceMove * dt
        posUpdate = False
        momentumChange = dt * 60.0
        if (self.arrowKeys.upPressed() or self.arrowKeys.downPressed()) and not self.golfCourse.canDrive(self.currentGolfer):
            posUpdate = True
            self.aimMomentum = 0.0
            self.ballFollow.headsUp(self.holeBottomNodePath)
        elif self.arrowKeys.rightPressed() and not self.arrowKeys.leftPressed():
            self.aimMomentum -= momentumChange
            if self.aimMomentum > 0:
                self.aimMomentum = 0.0
            elif self.aimMomentum < -30.0:
                self.aimMomentum = -30.0
            posUpdate = True
            self.switchToAnimState('GolfRotateLeft')
            self.scoreBoard.hide()
        elif self.arrowKeys.leftPressed() and not self.arrowKeys.rightPressed():
            self.aimMomentum += momentumChange
            if self.aimMomentum < 0.0:
                self.aimMomentum = 0.0
            elif self.aimMomentum > 30.0:
                self.aimMomentum = 30.0
            posUpdate = True
            self.switchToAnimState('GolfRotateRight')
            self.scoreBoard.hide()
        else:
            self.aimMomentum = 0.0
            self.switchToAnimState('GolfPuttLoop')
        self.ballFollow.setH(self.ballFollow.getH() + self.aimMomentum * dt)
        if self.arrowKeys.upPressed() and self.golfCourse.canDrive(self.currentGolfer):
            b.enable()
            b.addForce(Vec3(x * forceMoveDt, y * forceMoveDt, 0))
        if self.arrowKeys.downPressed() and self.golfCourse.canDrive(self.currentGolfer):
            b.enable()
            b.addForce(Vec3(-x * forceMoveDt, -y * forceMoveDt, 0))
        if self.arrowKeys.leftPressed() and self.arrowKeys.rightPressed() and self.golfCourse.canDrive(self.currentGolfer):
            b.enable()
            b.addForce(Vec3(0, 0, 3000 * dt))
        if posUpdate:
            if globalClock.getFrameTime() - self.lastTimeHeadingSent > 0.2:
                self.sendUpdate('setTempAimHeading', [localAvatar.doId, self.ballFollow.getH()])
                self.lastTimeHeadingSent = globalClock.getFrameTime()
                self.lastTempHeadingSent = self.ballFollow.getH()
        elif self.lastTempHeadingSent != self.ballFollow.getH():
            self.sendUpdate('setTempAimHeading', [localAvatar.doId, self.ballFollow.getH()])
            self.lastTimeHeadingSent = globalClock.getFrameTime()
            self.lastTempHeadingSent = self.ballFollow.getH()
        self.setCamera2Ball()
        self.fixCurrentGolferFeet()
        self.adjustClub()
        self.orientCameraRay()
        return task.cont

    def fixCurrentGolferFeet(self):
        golfer = base.cr.doId2do.get(self.currentGolfer)
        if not golfer:
            return
        golferPos = golfer.getPos(render)
        newPos = Vec3(golferPos[0], golferPos[1], golferPos[2] + 5)
        self.toonRay.setPosition(newPos)

    def adjustClub(self):
        club = self.clubs[self.currentGolfer]
        if club:
            distance = club.getDistance(self.clubLookatSpot)
            scaleFactor = distance / 2.058
            club.setScale(1, scaleFactor, 1)

    def resetPowerBar(self):
        self.power = 0
        self.powerBar['value'] = self.power
        self.powerBar['text'] = ''

    def sendSwingInfo(self):
        kickHimOut = self.updateWarning()
        if kickHimOut:
            return
        curAimTime = globalClock.getRealTime() - self.enterAimStart
        if curAimTime < 0:
            curAimTime = 0
        if curAimTime > GolfGlobals.AIM_DURATION:
            curAimTime = GolfGlobals.AIM_DURATION
        self.notify.debug('curAimTime = %f' % curAimTime)
        x = -math.sin(self.ballFollow.getH() * 0.0174532925)
        y = math.cos(self.ballFollow.getH() * 0.0174532925)
        b = self.curGolfBall()
        if hasattr(base, 'golfPower') and base.golfPower != None:
            self.power = float(base.golfPower)
        if not self.swingInfoSent:
            self.sendUpdate('postSwingState', [self.getCycleTime(),
             self.power,
             b.getPosition()[0],
             b.getPosition()[1],
             b.getPosition()[2],
             x,
             y,
             curAimTime,
             self.getCommonObjectData()])
        self.swingInfoSent = True
        if self.power < 15 and self.golfCourse.scores[localAvatar.doId][self.golfCourse.curHoleIndex] == 0:
            self.powerReminder = DirectLabel(text=TTLocalizer.GolfPowerReminder, text_shadow=(0, 0, 0, 1), text_fg=VBase4(1, 1, 0.0, 1), text_align=TextNode.ACenter, relief=None, pos=(0, 0, 0.8), scale=0.12)
        return

    def updateWarning(self):
        retval = False
        if not self.localToonHitControl:
            self.localMissedSwings += 1
        else:
            self.localMissedSwings = 0
        if self.localMissedSwings == GolfGlobals.KICKOUT_SWINGS - 1:
            self.warningLabel = DirectLabel(parent=aspect2d, relief=None, pos=(0, 0, 0), text_align=TextNode.ACenter, text=TTLocalizer.GolfWarningMustSwing, text_scale=0.12, text_font=ToontownGlobals.getSignFont(), text_fg=(1, 0.1, 0.1, 1), text_wordwrap=20)
            self.warningInterval = Sequence(LerpColorScaleInterval(self.warningLabel, 10, Vec4(1, 1, 1, 0), startColorScale=Vec4(1, 1, 1, 1), blendType='easeIn'), Func(self.warningLabel.destroy))
            self.warningInterval.start()
        elif self.localMissedSwings >= GolfGlobals.KICKOUT_SWINGS:
            self.golfCourse.handleFallingAsleepGolf(None)
            retval = True
        return retval

    def assignRecordSwing(self, avId, cycleTime, power, x, y, z, dirX, dirY, commonObjectData):
        ball = self.ballDict[avId]['golfBall']
        holdBallPos = ball.getPosition()
        self.useCommonObjectData(commonObjectData)
        self.trackRecordBodyFlight(ball, cycleTime, power, Vec3(x, y, z), dirX, dirY)
        ball.setPosition(holdBallPos)
        self.sendUpdate('ballMovie2AI', [cycleTime,
         avId,
         self.recording,
         self.aVRecording,
         self.ballInHoleFrame,
         self.ballTouchedHoleFrame,
         self.ballFirstTouchedHoleFrame,
         commonObjectData])
        self.ballMovie2Client(cycleTime, avId, self.recording, self.aVRecording, self.ballInHoleFrame, self.ballTouchedHoleFrame, self.ballFirstTouchedHoleFrame, commonObjectData)

    def __watchAimTask(self, task):
        self.setCamera2Ball()
        self.attachClub(self.currentGolfer, True)
        self.adjustClub()
        self.fixCurrentGolferFeet()
        self.orientCameraRay()
        return task.cont

    def __watchTeeTask(self, task):
        self.setCamera2Ball()
        return task.cont

    def curGolfBall(self):
        return self.ballDict[self.currentGolfer]['golfBall']

    def curGolfBallGeom(self):
        return self.ballDict[self.currentGolfer]['golfBallGeom']

    def curBallShadow(self):
        return self.ballShadowDict[self.currentGolfer]

    def cleanupGeom(self):
        self.targets.remove()
        self.terrainModel.remove()
        self.powerBar.destroy()

    def cleanupPowerBar(self):
        self.powerBar.hide()

    def cleanupPhysics(self):
        pass

    def curBall(self):
        return self.ballDict[self.currentGolfer]['ball']

    def curBallANP(self):
        return self.ballDict[self.currentGolfer]['ballActorNodePath']

    def curBallActor(self):
        return self.ballDict[self.currentGolfer]['ballActor']

    def enterAim(self):
        self.notify.debug('Aim')
        self.notify.debug('currentGolfer = %s' % self.currentGolfer)
        self.switchToAnimState('GolfPuttLoop', forced=True)
        self.swingInfoSent = False
        self.lastState = self.state
        self.aimMomentum = 0.0
        self.enterAimStart = globalClock.getRealTime()
        taskMgr.add(self.__aimTask, 'Aim Task')
        self.showOnlyCurGolfer()
        strokes = self.golfCourse.getStrokesForCurHole(self.currentGolfer)
        self.camPivot = self.ballFollow.attachNewNode('golf-camPivot')
        self.targetCamPivot = self.ballFollow.attachNewNode('golf-targetCamPivot')
        self.targetCamPivot.setP(self.DefaultCamP)
        self.curCamPivot = self.ballFollow.attachNewNode('golf-curCamPivot')
        self.curCamPivot.setP(self.DefaultCamP)
        self.ccTrav = CollisionTraverser('golf.ccTrav')
        self.ccLine = CollisionSegment(0.0, 0.0, 0.0, 1.0, 0.0, 0.0)
        self.ccLineNode = CollisionNode('golf.ccLineNode')
        self.ccLineNode.addSolid(self.ccLine)
        self.ccLineNodePath = self.camPivot.attachNewNode(self.ccLineNode)
        self.ccLineBitMask = BitMask32(1048576)
        self.ccLineNode.setFromCollideMask(self.ccLineBitMask)
        self.ccLineNode.setIntoCollideMask(BitMask32.allOff())
        self.camCollisionQueue = CollisionHandlerQueue()
        self.ccTrav.addCollider(self.ccLineNodePath, self.camCollisionQueue)
        if strokes:
            self.ballFollow.headsUp(self.holeBottomNodePath)
        self.camPivot.setP(self.DefaultCamP)
        self._golfBarrierCollection = self.terrainModel.findAllMatches('**/collision?')
        self._camAdjust = ScratchPad()
        self._camAdjust.iters = 0
        self._camAdjust.lower = self.DefaultCamP
        self._camAdjust.upper = self.MaxCamP
        base.camera.setPos(self.camPosBallFollow)
        base.camera.setHpr(self.camHprBallFollow)
        self.camPivot.setP(self.DefaultCamP)
        base.camera.wrtReparentTo(self.camPivot)
        A = Point3(0, 0, 0)
        B = base.camera.getPos()
        AtoB = B - A
        AtoBnorm = Point3(AtoB)
        AtoBnorm.normalize()
        A += AtoBnorm * 0.4
        self.ccLine.setPointA(A)
        self.ccLine.setPointB(B)
        self.camPivot.setP(self.DefaultCamP)
        self._camAdjust.task = taskMgr.add(self._adjustCamera, 'adjustCamera')
        self.resetPowerBar()
        self.powerBar.show()
        self.aimDuration = GolfGlobals.AIM_DURATION
        if not self.unlimitedAimTime:
            self.timer = ToontownTimer.ToontownTimer()
            self.timer.posInTopRightCorner()
            self.timer.setTime(self.aimDuration)
            self.timer.countdown(self.aimDuration, self.timerExpired)
        self.aimInstructions = DirectLabel(text=TTLocalizer.GolfAimInstructions, text_shadow=(0, 0, 0, 1), text_fg=VBase4(1, 1, 1, 1), text_align=TextNode.ACenter, relief=None, pos=(0, 0, -0.8), scale=TTLocalizer.DGHaimInstructions)
        self.skyContact = 1
        self.localToonHitControl = False
        self._adjustCamera()
        return

    def exitAim(self):
        localAvatar.wrtReparentTo(render)
        taskMgr.remove(self._camAdjust.task)
        taskMgr.remove('Aim Task')
        taskMgr.remove(self.golfPowerTaskName)
        if self.timer:
            self.timer.stop()
            self.timer.destroy()
            self.timer = None
        self.powerBar.hide()
        self.ccLineNodePath.detachNode()
        self.targetCamPivot.detachNode()
        self.curCamPivot.detachNode()
        self.camPivot.detachNode()
        if self.aimInstructions:
            self.aimInstructions.destroy()
            self.aimInstructions = None
        return

    def timerExpired(self):
        taskMgr.remove(self.golfPowerTaskName)
        self.aimStart = None
        self.sendSwingInfo()
        self.resetPowerBar()
        return

    def _adjustCamera(self, task=None, first=True):
        if task is None and first:
            while 1:
                self._adjustCamera(first=False)
                if self._camAdjust.iters == 0:
                    return Task.cont

        MaxIters = 5
        finalP = self._camAdjust.lower

        localAvatar.stash()
        for barrier in self._golfBarrierCollection:
            barrier.stash()

        self.ccTrav.traverse(render)

        for barrier in self._golfBarrierCollection:
            barrier.unstash()
        localAvatar.unstash()

        midP = (self._camAdjust.lower + self._camAdjust.upper)/2
        if self.camCollisionQueue.getNumEntries() > 0:
            self.camCollisionQueue.sortEntries()
            entry = self.camCollisionQueue.getEntry(0)
            sPoint = entry.getSurfacePoint(self.camPivot)
            self._camAdjust.lower = self.camPivot.getP()
            finalP = midP
            self.camPivot.setP(finalP)
        else:
            self._camAdjust.upper = self.camPivot.getP()
            finalP = self._camAdjust.upper
            self.camPivot.setP(midP)
            if abs(self._camAdjust.lower - self._camAdjust.upper) < 1.0:
                self._camAdjust.iters = MaxIters

        self._camAdjust.iters += 1
        if self._camAdjust.iters >= MaxIters:
            self.targetCamPivot.setP(self._camAdjust.upper)
            if task is None:
                self.curCamPivot.setP(finalP)
            self._camAdjust.iters = 0
            self._camAdjust.lower = self.DefaultCamP
            self._camAdjust.upper = self.MaxCamP
            self.camPivot.setP(self.DefaultCamP)

        if task is not None:
            self.curCamPivot.setP(self.curCamPivot,
                self.targetCamPivot.getP(self.curCamPivot)*min(1.0, 1.0*globalClock.getDt()))

        curP = self.curCamPivot.getP()
        self.curCamPivot.setP(self.DefaultCamP)
        base.camera.reparentTo(self.ballFollow)
        base.camera.setPos(self.camPosBallFollow)
        base.camera.setHpr(self.camHprBallFollow)
        base.camera.wrtReparentTo(self.curCamPivot)
        self.curCamPivot.setP(curP)
        base.camera.wrtReparentTo(self.ballFollow)

        return Task.cont

    def enterChooseTee(self):
        self.notify.debug('ChooseTee')
        self.curGolfBallGeom().show()
        self.curBallShadow().show()
        self.lastState = self.state
        taskMgr.add(self.__chooseTeeTask, 'ChooseTee Task')
        self.ballFollow.setH(self.startingTeeHeading)
        self.localAvatarChosenTee = False
        self.localTempTee = 0
        if len(self.teePositions) > 1:
            self.localTempTee = 1
        self.chooseTeeDuration = GolfGlobals.TEE_DURATION
        if not self.unlimitedTeeTime:
            self.teeTimer = ToontownTimer.ToontownTimer()
            self.teeTimer.posInTopRightCorner()
            self.teeTimer.setTime(self.chooseTeeDuration)
            self.teeTimer.countdown(self.chooseTeeDuration, self.teeTimerExpired)
        self.teeInstructions = DirectLabel(text=TTLocalizer.GolfChooseTeeInstructions, text_fg=VBase4(1, 1, 1, 1), text_align=TextNode.ACenter, text_shadow=(0, 0, 0, 1), relief=None, pos=(0, 0, -0.75), scale=TTLocalizer.DGHteeInstructions)
        self.powerBar.hide()
        return

    def exitChooseTee(self):
        localAvatar.wrtReparentTo(render)
        if hasattr(self, 'teeInstructions') and self.teeInstructions:
            self.teeInstructions.destroy()
        self.teeInstructions = None
        taskMgr.remove('ChooseTee Task')
        taskMgr.remove(self.golfPowerTaskName)
        if self.teeTimer:
            self.teeTimer.stop()
            self.teeTimer.destroy()
            self.teeTimer = None
        self.powerBar.show()
        return

    def sendTeeInfo(self):
        self.sendUpdate('setAvatarTee', [self.localTempTee])
        self.localAvatarChosenTee = True

    def __chooseTeeTask(self, task):
        if self.localAvatarChosenTee:
            return task.done
        if self.arrowKeys.jumpPressed():
            if self.flyOverInterval and self.flyOverInterval.isPlaying():
                pass
            else:
                self.sendTeeInfo()
        return task.cont

    def changeTee(self, newTee):
        ball = self.curGolfBall()
        ball.setPosition(self.teePositions[newTee])
        self.setCamera2Ball()
        self.fixCurrentGolferFeet()
        self.adjustClub()

    def changeLocalTee(self, newTee):
        self.changeTee(newTee)
        self.sendUpdate('setAvatarTempTee', [localAvatar.doId, newTee])
        self.fixCurrentGolferFeet()
        self.adjustClub()

    def __leftArrowPressed(self):
        if self.state != 'ChooseTee':
            return
        self.localTempTee -= 1
        if self.localTempTee < 0:
            self.localTempTee = len(self.teePositions) - 1
        self.changeLocalTee(self.localTempTee)

    def __rightArrowPressed(self):
        if self.state != 'ChooseTee':
            return
        self.localTempTee += 1
        self.localTempTee %= len(self.teePositions)
        self.changeLocalTee(self.localTempTee)

    def teeTimerExpired(self):
        self.sendTeeInfo()

    def enterWatchAim(self):
        self.notify.debug('Watch Aim')
        self.notify.debugStateCall(self)
        self.notify.debug('currentGolfer = %s' % self.currentGolfer)
        strokes = self.golfCourse.getStrokesForCurHole(self.currentGolfer)
        if strokes:
            self.ballFollow.lookAt(self.holeBottomNodePath)
            self.ballFollow.setP(0)
        self.showOnlyCurGolfer()
        taskMgr.add(self.__watchAimTask, 'Watch Aim Task')

    def exitWatchAim(self):
        self.notify.debugStateCall(self)
        av = base.cr.doId2do.get(self.currentGolfer)
        if av:
            heading = av.getH(render)
            toonPos = av.getPos(render)
            av.reparentTo(render)
            av.setH(heading)
            av.setPos(toonPos)
            self.notify.debug('av %s now at position %s' % (av.getName(), av.getPos()))
        else:
            self.notify.debug('could not get avId %d' % self.currentGolfer)
        taskMgr.remove('Watch Aim Task')

    def enterWatchTee(self):
        self.notify.debug('Watch Tee')
        self.notify.debugStateCall(self)
        self.curGolfBallGeom().show()
        self.ballFollow.setH(self.startingTeeHeading)
        self.ballShadowDict[self.currentGolfer].show()

    def exitWatchTee(self):
        self.notify.debugStateCall(self)
        av = base.cr.doId2do.get(self.currentGolfer)
        taskMgr.remove('Watch Tee Task')

    def enterWait(self):
        self.notify.debug('Wait')
        self.notify.debugStateCall(self)

    def exitWait(self):
        self.notify.debugStateCall(self)

    def removePlayBackDelayDelete(self):
        if self.playBackDelayDelete:
            self.playBackDelayDelete.destroy()
            self.playBackDelayDelete = None
        return

    def enterPlayback(self):

        def shiftClubToRightHand():
            club = self.clubs[self.currentGolfer]
            av = base.cr.doId2do.get(self.currentGolfer)
            if av and club:
                club.wrtReparentTo(av.getRightHands()[0])

        av = base.cr.doId2do.get(self.currentGolfer)
        if not av:
            return
        else:
            self.removePlayBackDelayDelete()
            self.playBackDelayDelete = DelayDelete.DelayDelete(av, 'GolfHole.enterPlayback')
        self.accept('clientCleanup', self._handleClientCleanup)
        self.inPlayBack = 1
        self.setLookingAtPutt(False)
        self.swingInterval = Sequence(ActorInterval(av, 'swing-putt', startFrame=0, endFrame=GolfGlobals.BALL_CONTACT_FRAME), Func(self.startBallPlayback), ActorInterval(av, 'swing-putt', startFrame=GolfGlobals.BALL_CONTACT_FRAME, endFrame=23), Func(shiftClubToRightHand), Func(self.setLookingAtPutt, True), Func(self.removePlayBackDelayDelete))
        adjustedBallTouchedHoleTime = self.ballTouchedHoleTime + GolfGlobals.BALL_CONTACT_TIME
        adjustedBallFirstTouchedHoleTime = self.ballFirstTouchedHoleTime + GolfGlobals.BALL_CONTACT_TIME
        adjustedBallDropTime = self.ballDropTime + GolfGlobals.BALL_CONTACT_TIME
        adjustedPlaybackEndTime = self.playbackMovieDuration + GolfGlobals.BALL_CONTACT_TIME
        self.notify.debug('adjustedTimes ballTouched=%.2f ballFirstTouched=%.2f ballDrop=%.2f playbaybackEnd=%.2f' % (adjustedBallTouchedHoleTime,
         adjustedBallFirstTouchedHoleTime,
         adjustedBallDropTime,
         adjustedPlaybackEndTime))
        if self.ballWillGoInHole:
            curDuration = self.swingInterval.getDuration()
            lookPuttInterval = ActorInterval(av, 'look-putt')
            if curDuration < adjustedBallDropTime:
                self.swingInterval.append(lookPuttInterval)
            curDuration = self.swingInterval.getDuration()
            diffTime = adjustedBallDropTime - curDuration
            if diffTime > 0:
                self.swingInterval.append(ActorInterval(av, 'lookloop-putt', endTime=diffTime))
            self.swingInterval.append(ActorInterval(av, 'good-putt', endTime=self.playbackMovieDuration, loop=1))
        elif self.ballTouchedHoleTime:
            self.notify.debug('doing self.ballTouchedHoleTime')
            curDuration = self.swingInterval.getDuration()
            lookPuttInterval = ActorInterval(av, 'look-putt')
            if curDuration < adjustedBallTouchedHoleTime:
                self.swingInterval.append(lookPuttInterval)
            curDuration = self.swingInterval.getDuration()
            diffTime = adjustedBallTouchedHoleTime - curDuration
            if diffTime > 0:
                self.swingInterval.append(ActorInterval(av, 'lookloop-putt', endTime=diffTime))
            self.swingInterval.append(ActorInterval(av, 'bad-putt', endFrame=32))
            self.swingInterval.append(ActorInterval(av, 'badloop-putt', endTime=self.playbackMovieDuration, loop=1))
        else:
            self.swingInterval.append(ActorInterval(av, 'look-putt'))
            self.swingInterval.append(ActorInterval(av, 'lookloop-putt', endTime=self.playbackMovieDuration, loop=1))
        sfxInterval = Parallel()
        ballHitInterval = Sequence(Wait(GolfGlobals.BALL_CONTACT_TIME), SoundInterval(self.hitBallSfx))
        sfxInterval.append(ballHitInterval)
        if self.ballWillGoInHole:
            ballRattle = Sequence()
            timeToPlayBallRest = adjustedPlaybackEndTime - self.ballGoesToRestSfx.length()
            if adjustedBallFirstTouchedHoleTime < timeToPlayBallRest:
                diffTime = timeToPlayBallRest - adjustedBallFirstTouchedHoleTime
                if self.ballGoesInStartSfx.length() < diffTime:
                    ballRattle.append(Wait(adjustedBallFirstTouchedHoleTime))
                    ballRattle.append(SoundInterval(self.ballGoesInStartSfx))
                    timeToPlayLoop = adjustedBallFirstTouchedHoleTime + self.ballGoesInStartSfx.length()
                    loopTime = timeToPlayBallRest - timeToPlayLoop
                    if self.ballGoesInLoopSfx.length() == 0.0:
                        numLoops = 0
                    else:
                        numLoops = int(loopTime / self.ballGoesInLoopSfx.length())
                    self.notify.debug('numLoops=%d loopTime=%f' % (numLoops, loopTime))
                    if loopTime > 0:
                        ballRattle.append(SoundInterval(self.ballGoesInLoopSfx, loop=1, duration=loopTime, seamlessLoop=True))
                    ballRattle.append(SoundInterval(self.ballGoesToRestSfx))
                    self.notify.debug('playing full rattling')
                else:
                    self.notify.debug('playing abbreviated rattling')
                    timeToPlayBallGoesIn = adjustedBallFirstTouchedHoleTime
                    ballRattle.append(Wait(timeToPlayBallGoesIn))
                    startTime = self.ballGoesInStartSfx.length() - diffTime
                    self.notify.debug('adjustedBallDropTime=%s diffTime=%s starTime=%s' % (adjustedBallDropTime, diffTime, startTime))
                    ballRattle.append(SoundInterval(self.ballGoesInStartSfx, startTime=startTime))
                    ballRattle.append(SoundInterval(self.ballGoesToRestSfx))
            else:
                self.notify.debug('playing abbreviated ball goes to rest')
                ballRattle.append(Wait(adjustedBallFirstTouchedHoleTime))
                diffTime = adjustedPlaybackEndTime - adjustedBallFirstTouchedHoleTime
                startTime = self.ballGoesToRestSfx.length() - diffTime
                self.notify.debug('adjustedBallDropTime=%s diffTime=%s starTime=%s' % (adjustedBallDropTime, diffTime, startTime))
                ballRattle.append(SoundInterval(self.ballGoesToRestSfx, startTime=startTime))
            sfxInterval.append(ballRattle)
        crowdBuildupSfx = self.crowdBuildupSfx[self.avIdList.index(self.currentGolfer)]
        crowdApplauseSfx = self.crowdApplauseSfx[self.avIdList.index(self.currentGolfer)]
        crowdMissSfx = self.crowdMissSfx[self.avIdList.index(self.currentGolfer)]
        if self.ballWillGoInHole:
            crowdIval = Sequence()
            buildupLength = crowdBuildupSfx.length()
            self.notify.debug('buildupLength=%s' % buildupLength)
            diffTime = adjustedBallFirstTouchedHoleTime - buildupLength
            if diffTime > 0:
                crowdIval.append(Wait(diffTime))
                crowdIval.append(SoundInterval(crowdBuildupSfx))
                crowdIval.append(SoundInterval(crowdApplauseSfx))
            else:
                startTime = buildupLength - adjustedBallFirstTouchedHoleTime
                self.notify.debug('playing abbreviated crowd build and applause diffTime=%s startTime=%s' % (diffTime, startTime))
                crowdIval.append(SoundInterval(crowdBuildupSfx, startTime=startTime))
                crowdIval.append(SoundInterval(crowdApplauseSfx))
            sfxInterval.append(crowdIval)
        elif self.ballFirstTouchedHoleTime:
            crowdIval = Sequence()
            buildupLength = crowdBuildupSfx.length()
            self.notify.debug('touched but not going in buildupLength=%s' % buildupLength)
            diffTime = adjustedBallFirstTouchedHoleTime - buildupLength
            if diffTime > 0:
                self.notify.debug('waiting %.2f to play crowd buildup' % diffTime)
                crowdIval.append(Wait(diffTime))
                crowdIval.append(SoundInterval(crowdBuildupSfx))
                crowdIval.append(SoundInterval(crowdMissSfx))
            else:
                startTime = buildupLength - adjustedBallFirstTouchedHoleTime
                self.notify.debug('playing abbreviated crowd build and miss diffTime=%s startTime=%s' % (diffTime, startTime))
                crowdIval.append(SoundInterval(crowdBuildupSfx, startTime=startTime))
                crowdIval.append(SoundInterval(crowdMissSfx))
            sfxInterval.append(crowdIval)
        if self.sfxInterval:
            sfxInterval.finish()
        self.sfxInterval = sfxInterval
        self.sfxInterval.start()
        self.swingInterval.start()

    def exitPlayback(self):
        self.notify.debug('Exiting Playback')
        if self.swingInterval:
            self.swingInterval.pause()
        av = base.cr.doId2do.get(self.currentGolfer)
        if av:
            if self.ballWillGoInHole:
                av.loop('good-putt', restart=0)
            elif self.ballTouchedHoleTime:
                pass
            else:
                av.loop('neutral')
        self.setLookingAtPutt(False)
        if av == base.localAvatar:
            if self.ballWillGoInHole:
                av.b_setAnimState('GolfGoodPutt')
            elif self.ballTouchedHoleTime:
                av.b_setAnimState('GolfBadPutt')
            else:
                av.b_setAnimState('neutral')
        taskMgr.remove('playback task')
        self.curGolfBall().disable()
        self.readyCurrentGolfer(None)
        self.inPlayBack = 0
        if self.powerReminder:
            self.powerReminder.destroy()
            self.powerReminder = None
        return

    def setLookingAtPutt(self, newVal):
        self.isLookingAtPutt = newVal

    def getLookingAtPutt(self):
        return self.isLookingAtPutt

    def startBallPlayback(self):
        self.playbackFrameNum = 0
        self.sourceFrame = self.recording[0]
        self.destFrameNum = 1
        self.destFrame = self.recording[self.destFrameNum]
        self.aVSourceFrame = self.aVRecording[0]
        self.aVDestFrameNum = 1
        self.aVDestFrame = self.aVRecording[self.aVDestFrameNum]
        self.inPlayBack = 2

    def isCurBallInHole(self):
        retval = False
        ball = self.curGolfBall()
        ballPos = ball.getPosition()
        for holePos in self.holePositions:
            displacement = ballPos - holePos
            length = displacement.length()
            self.notify.debug('hole %s length=%s' % (holePos, length))
            if length <= GolfGlobals.DistanceToBeInHole:
                retval = True
                break

        return retval

    def handleBallGoingInHole(self):
        par = GolfGlobals.HoleInfo[self.holeId]['par']
        unlimitedSwing = False
        av = base.cr.doId2do.get(self.currentGolfer)
        if av:
            unlimitedSwing = av.getUnlimitedSwing()
        if not unlimitedSwing:
            self.curGolfBall().setPosition(0, 0, -100)
            self.ballShadowDict[self.currentGolfer].setPos(0, 0, -100)
            self.ballShadowDict[self.currentGolfer].hide()
        strokes = 3
        if self.golfCourse:
            strokes = self.golfCourse.getStrokesForCurHole(self.currentGolfer)
        else:
            self.notify.warning('self.golfCourse is None')
        diff = strokes - par
        if diff > 0:
            textStr = '+' + str(diff)
        else:
            textStr = diff
        if strokes == 1:
            textStr = TTLocalizer.GolfHoleInOne
        elif diff in TTLocalizer.GolfShotDesc:
            if self.ballWillGoInHole:
                textStr = TTLocalizer.GolfShotDesc[diff]
        perfectTextSubnode = hidden.attachNewNode(self.__genText(textStr))
        perfectText = hidden.attachNewNode('perfectText')
        perfectTextSubnode.reparentTo(perfectText)
        frame = self.__textGen.getCardActual()
        offsetY = -abs(frame[2] + frame[3]) / 2.0 - 1.35
        perfectTextSubnode.setPos(0, 0, offsetY)
        perfectText.setColor(1, 0.1, 0.1, 1)

        def fadeFunc(t, text = perfectText):
            text.setColorScale(1, 1, 1, t)

        def destroyText(text = perfectText):
            text.removeNode()

        animTrack = Sequence()
        av = base.cr.doId2do.get(self.currentGolfer)
        animTrack.append(Func(self.golfCourse.updateScoreBoard))
        textTrack = Sequence(Func(perfectText.reparentTo, aspect2d), Parallel(LerpScaleInterval(perfectText, duration=0.5, scale=0.3, startScale=0.0), LerpFunctionInterval(fadeFunc, fromData=0.0, toData=1.0, duration=0.5)), Wait(2.0), Parallel(LerpScaleInterval(perfectText, duration=0.5, scale=1.0), LerpFunctionInterval(fadeFunc, fromData=1.0, toData=0.0, duration=0.5, blendType='easeIn')), Func(destroyText), WaitInterval(0.5), Func(self.sendUpdate, 'turnDone', []))
        soundTrack = Sequence()
        if strokes == 1:
            soundTrack.append(SoundInterval(self.holeInOneSfx))
        elif self.hasCurGolferReachedMaxSwing and not self.ballWillGoInHole:
            soundTrack.append(SoundInterval(self.kickedOutSfx))
        self.perfectIval = Parallel(textTrack, soundTrack, animTrack)
        self.perfectIval.start()

    def __playbackTask(self, task):
        return self.playBackFrame(task)

    def toonRayCollisionCallback(self, x, y, z):
        if self.state not in ('Aim', 'WatchAim', 'ChooseTee', 'WatchTee'):
            return
        tempPath = render.attachNewNode('temp')
        tempPath.setPos(x, y, z)
        relPos = tempPath.getPos(self.ballFollowToonSpot)
        av = base.cr.doId2do.get(self.currentGolfer)
        if av:
            zToUse = relPos[2]
            if zToUse < 0 - GolfGlobals.GOLF_BALL_RADIUS:
                zToUse = 0 - GolfGlobals.GOLF_BALL_RADIUS
            av.setPos(0, 0, zToUse)
        tempPath.removeNode()

    def preStep(self):
        if self.currentGolferActive:
            GolfHoleBase.GolfHoleBase.preStep(self)

    def postStep(self):
        if self.currentGolferActive:
            GolfHoleBase.GolfHoleBase.postStep(self)
            DistributedPhysicsWorld.DistributedPhysicsWorld.postStep(self)
            if self.inPlayBack == 2:
                self.playBackFrame()
                self.makeCurGolferLookAtBall()
            elif self.state == 'Playback' and self.inPlayBack == 0:
                self.request('Wait')
            self.updateTranslucentObjects()

    def updateTranslucentObjects(self):
        for translucentNodePathLastFrame in self.translucentLastFrame:
            if translucentNodePathLastFrame not in self.translucentCurFrame:
                translucentNodePathLastFrame.setColorScale(1, 1, 1, 1)

        for transNpCurFrame in self.translucentCurFrame:
            if transNpCurFrame not in self.translucentLastFrame:
                self.notify.debug('making translucent %s' % transNpCurFrame)
                transNpCurFrame.setColorScale(1, 1, 1, 0.25)
                transNpCurFrame.setTransparency(1)

    def makeCurGolferLookAtBall(self):
        if self.getLookingAtPutt():
            av = base.cr.doId2do.get(self.currentGolfer)
            if av:
                ballPos = self.curGolfBall().getPosition()
                av.headsUp(ballPos[0], ballPos[1], ballPos[2])
                av.setH(av.getH() - 90)

    def playBackFrame(self):
        doPrint = 0
        doAVPrint = 0
        lastFrame = self.recording[len(self.recording) - 1][0]
        if self.playbackFrameNum >= self.destFrame[0]:
            self.sourceFrame = self.destFrame
            self.destFrameNum += 1
            doPrint = 1
            if self.destFrameNum < len(self.recording):
                self.destFrame = self.recording[self.destFrameNum]
            else:
                self.notify.debug('recording length %s' % len(self.recording))
                if self.isCurBallInHole() or self.hasCurGolferReachedMaxSwing():
                    self.handleBallGoingInHole()
                    self.request('Wait')
                else:
                    self.golfCourse.updateScoreBoard()
                    self.request('Wait')
                    self.sendUpdate('turnDone', [])
                return
        self.projLength = self.destFrame[0] - self.sourceFrame[0]
        self.projPen = self.destFrame[0] - self.playbackFrameNum
        propSource = float(self.projPen) / float(self.projLength)
        propDest = 1.0 - propSource
        projX = self.sourceFrame[1] * propSource + self.destFrame[1] * propDest
        projY = self.sourceFrame[2] * propSource + self.destFrame[2] * propDest
        projZ = self.sourceFrame[3] * propSource + self.destFrame[3] * propDest
        newPos = Vec3(projX, projY, projZ)
        ball = self.curGolfBall()
        ball.setPosition(newPos)
        if self.playbackFrameNum >= self.aVDestFrame[0]:
            self.aVSourceFrame = self.aVDestFrame
            self.aVDestFrameNum += 1
            doAVPrint = 1
            if self.aVDestFrameNum < len(self.aVRecording):
                self.aVDestFrame = self.aVRecording[self.aVDestFrameNum]
                newAV = Vec3(self.aVSourceFrame[1], self.aVSourceFrame[2], self.aVSourceFrame[3])
        self.projLength = self.aVDestFrame[0] - self.aVSourceFrame[0]
        self.projPen = self.aVDestFrame[0] - self.playbackFrameNum
        propSource = float(self.projPen) / float(self.projLength)
        propDest = 1.0 - propSource
        projX = self.aVSourceFrame[1] * propSource + self.aVDestFrame[1] * propDest
        projY = self.aVSourceFrame[2] * propSource + self.aVDestFrame[2] * propDest
        projZ = self.aVSourceFrame[3] * propSource + self.aVDestFrame[3] * propDest
        newAV = Vec3(projX, projY, projZ)
        ball = self.curGolfBall()
        ball.setAngularVel(newAV)
        if self.playbackFrameNum < lastFrame - 1:
            ball.enable()
        else:
            ball.disable()
        self.setCamera2Ball()
        self.placeBodies()
        if doAVPrint:
            pass
        if doPrint:
            self.notify.debug('. %s %s %s %s %s' % (self.playbackFrameNum,
             self.sourceFrame[0],
             self.destFrame[0],
             self.destFrameNum,
             newPos))
        self.playbackFrameNum += 1

    def enterCleanup(self):
        taskMgr.remove('update task')
        if hasattr(self, 'arrowKeys'):
            self.arrowKeys.destroy()
        self.arrowKeys = None
        self.ignoreAll()
        if self.swingInterval:
            self.swingInterval.pause()
            self.swingInterval = None
        if self.sfxInterval:
            self.sfxInterval.pause()
            self.sfxInterval = None
        self.cleanupGeom()
        return

    def exitCleanup(self):
        pass

    def setCamera2Ball(self):
        b = self.curGolfBall()
        ballPos = Point3(b.getPosition()[0], b.getPosition()[1], b.getPosition()[2])
        self.ballFollow.setPos(ballPos)

    def hitBall(self, ball, power, x, y):
        self.performSwing(self, ball, power, x, y)

    def ballMovie2Client(self, cycleTime, avId, movie, spinMovie, ballInFrame, ballTouchedHoleFrame, ballFirstTouchedHoleFrame, commonObjectData):
        self.notify.debug('received Movie, number of frames %s %s ballInFrame=%d ballTouchedHoleFrame=%d ballFirstTouchedHoleFrame=%d' % (len(movie),
         len(spinMovie),
         ballInFrame,
         ballTouchedHoleFrame,
         ballFirstTouchedHoleFrame))
        if self.state == 'Playback':
            self.notify.debug('SMASHED PLAYBACK')
            return
        self.ballShadowDict[avId].show()
        self.holdCycleTime = cycleTime
        self.holdCommonObjectData = commonObjectData
        self.useCommonObjectData(self.holdCommonObjectData)
        self.recording = movie
        self.aVRecording = spinMovie
        endingBallPos = Vec3(movie[-1][1], movie[-1][2], movie[-1][3])
        endingFrame = movie[-1][0]
        self.playbackMovieDuration = endingFrame * self.DTAStep
        self.notify.debug('playback movie duration=%s' % self.playbackMovieDuration)
        displacement = self.holePositions[0] - endingBallPos
        self.ballWillGoInHole = False
        if displacement.length() <= GolfGlobals.DistanceToBeInHole:
            self.ballWillGoInHole = True
        self.notify.debug('endingBallPos=%s, distanceToHole=%s, ballWillGoInHole=%s' % (endingBallPos, displacement.length(), self.ballWillGoInHole))
        self.ballDropTime = ballInFrame * self.DTAStep
        self.ballTouchedHoleTime = ballTouchedHoleFrame * self.DTAStep
        self.ballFirstTouchedHoleTime = ballFirstTouchedHoleFrame * self.DTAStep
        if self.state == 'WatchTee':
            self.request('WatchAim')
        self.request('Playback')

    def golfersTurn(self, avId):
        self.readyCurrentGolfer(avId)
        if avId == localAvatar.doId:
            self.setCamera2Ball()
            self.request('Aim')
        else:
            self.setCamera2Ball()
            self.request('WatchAim')

    def readyCurrentGolfer(self, avId):
        for index in self.ballDict:
            self.ballDict[index]['golfBallOdeGeom'].setCollideBits(BitMask32(0))
            self.ballDict[index]['golfBallOdeGeom'].setCategoryBits(BitMask32(0))
            self.ballDict[index]['golfBall'].disable()

        if avId:
            self.currentGolfer = avId
            self.currentGolferActive = True
            if avId in self.ballDict:
                self.ballDict[avId]['golfBallOdeGeom'].setCollideBits(BitMask32(16777215))
                self.ballDict[avId]['golfBallOdeGeom'].setCategoryBits(BitMask32(4278190080L))
        else:
            self.currentGolferActive = False

    def setGolferIds(self, avIds):
        self.avIdList = avIds
        self.numPlayers = len(self.avIdList)
        self.teeChosen = {}
        for avId in self.avIdList:
            self.teeChosen[avId] = -1

    def setHoleId(self, holeId):
        self.holeId = holeId
        self.holeInfo = GolfGlobals.HoleInfo[holeId]

    def createBall(self, avId, index = None):
        golfBallGeom, golfBall, odeGeom = self.createSphere(self.world, self.space, GolfGlobals.GOLF_BALL_DENSITY, GolfGlobals.GOLF_BALL_RADIUS, index)
        startPos = self.teePositions[0]
        if len(self.teePositions) > 1:
            startPos = self.teePositions[1]
        golfBall.setPosition(startPos)
        golfBallGeom.hide()
        if self.notify.getDebug():
            self.notify.debug('golf ball body id')
            golfBall.write()
            self.notify.debug(' -')
        golfBallGeom.setName('golfBallGeom%s' % avId)
        self.ballDict[avId] = {'golfBall': golfBall,
         'golfBallGeom': golfBallGeom,
         'golfBallOdeGeom': odeGeom}
        golfBall.disable()
        shadow = self.dropShadowModel.copyTo(render)
        shadow.setBin('shadow', 100)
        shadow.setScale(0.09)
        shadow.setDepthWrite(False)
        shadow.setDepthTest(True)
        self.ballShadowDict[avId] = shadow
        shadow.hide()

    def setGolfCourseDoId(self, golfCourseDoId):
        self.golfCourseDoId = golfCourseDoId
        self.golfCourse = base.cr.doId2do.get(self.golfCourseDoId)
        if not self.golfCourse:
            self.cr.relatedObjectMgr.abortRequest(self.golfCourseRequest)
            self.golfCourseRequest = self.cr.relatedObjectMgr.requestObjects([self.golfCourseDoId], eachCallback=self.__gotGolfCourse)
        else:
            self.scoreBoard = self.golfCourse.scoreBoard
            self.scoreBoard.hide()

    def __gotGolfCourse(self, golfCourse):
        self.golfCourseRequest = None
        self.golfCourse = golfCourse
        return

    def __genText(self, text):
        self.__textGen.setText(text)
        return self.__textGen.generate()

    def sendBox(self, pos0, pos1, pos2, quat0, quat1, quat2, quat3, anV0, anV1, anV2, lnV0, lnV1, lnV2):
        self.swingBox.setPosition(pos0, pos1, pos2)
        self.swingBox.setQuaternion(Quat(quat0, quat1, quat2, quat3))
        self.swingBox.setAngularVel(anV0, anV1, anV2)
        self.swingBox.setLinearVel(lnV0, lnV1, lnV2)

    def hasCurGolferReachedMaxSwing(self):
        strokes = self.golfCourse.getStrokesForCurHole(self.currentGolfer)
        maxSwing = self.holeInfo['maxSwing']
        retval = strokes >= maxSwing
        if retval:
            pass
        return retval

    def __getGolfPower(self, time):
        elapsed = max(time - self.aimStart, 0.0)
        t = elapsed / self.golfPowerSpeed
        t = math.pow(t, self.golfPowerExponent)
        power = int(t * 100) % 200
        if power > 100:
            power = 200 - power
        return power

    def __beginTossGolf(self):
        if self.aimStart != None:
            return
        if not self.state == 'Aim':
            return
        if self.swingInfoSent:
            return
        self.localToonHitControl = True
        time = globalClock.getFrameTime()
        self.aimStart = time
        messenger.send('wakeup')
        self.scoreBoard.hide()
        taskMgr.add(self.__updateGolfPower, self.golfPowerTaskName)
        return

    def __endTossGolf(self):
        if self.aimStart == None:
            return
        if not self.state == 'Aim':
            return
        messenger.send('wakeup')
        taskMgr.remove(self.golfPowerTaskName)
        self.aimStart = None
        self.sendSwingInfo()
        self.resetPowerBar()
        return

    def __updateGolfPower(self, task):
        if not self.powerBar:
            print '### no power bar!!!'
            return Task.done
        newPower = self.__getGolfPower(globalClock.getFrameTime())
        self.power = newPower
        self.powerBar['value'] = newPower
        self.powerBar['text'] = TTLocalizer.GolfPowerBarText % {'power': newPower}
        return Task.cont

    def golferChooseTee(self, avId):
        self.readyCurrentGolfer(avId)
        self.putAwayAllToons()
        if self.needToDoFlyOver and self.doFlyOverMovie(avId):
            pass
        else:
            if avId == localAvatar.doId:
                self.setCamera2Ball()
                if not self.state == 'ChooseTee':
                    self.request('ChooseTee')
            else:
                self.setCamera2Ball()
                self.request('WatchTee')
            self.takeOutToon(self.currentGolfer)

    def setAvatarTempTee(self, avId, tempTee):
        if self.state != 'WatchTee':
            return
        if avId != self.currentGolfer:
            self.notify.warning('setAvatarTempTee avId=%s not equal to self.currentGolfer=%s' % (avId, self.currentGolfer))
            return
        self.changeTee(tempTee)

    def setAvatarFinalTee(self, avId, finalTee):
        if avId != self.currentGolfer:
            self.notify.warning('setAvatarTempTee avId=%s not equal to self.currentGolfer=%s' % (avId, self.currentGolfer))
            return
        self.changeTee(finalTee)

    def setTempAimHeading(self, avId, heading):
        if avId != self.currentGolfer:
            self.notify.warning('setAvatarTempTee avId=%s not equal to self.currentGolfer=%s' % (avId, self.currentGolfer))
            return
        if self.state != 'WatchAim':
            return
        if avId != localAvatar.doId:
            self.ballFollow.setH(heading)

    def stickToonToBall(self, avId):
        av = base.cr.doId2do.get(avId)
        if av:
            av.reparentTo(self.ballFollowToonSpot)
            av.setPos(0, 0, 0)
            av.setH(0)

    def putAwayToon(self, avId):
        av = base.cr.doId2do.get(avId)
        if av:
            av.reparentTo(render)
            av.setPos(0, 0, -1000)
            av.setH(0)

    def putAwayAllToons(self):
        for avId in self.avIdList:
            self.putAwayToon(avId)

    def takeOutToon(self, avId):
        self.stickToonToBall(avId)
        self.fixCurrentGolferFeet()
        self.attachClub(avId)

    def showOnlyCurGolfer(self):
        self.notify.debug('curGolfer = %s' % self.currentGolfer)
        self.stickToonToBall(self.currentGolfer)
        self.fixCurrentGolferFeet()
        self.attachClub(self.currentGolfer)
        for avId in self.avIdList:
            if avId != self.currentGolfer:
                self.putAwayToon(avId)

    def tabKeyPressed(self):
        doInterval = True
        self.notify.debug('tab key pressed')
        if not hasattr(self, 'ballFollow'):
            return
        if self.flyOverInterval and self.flyOverInterval.isPlaying():
            return
        if self.camInterval and self.camInterval.isPlaying():
            self.camInterval.pause()
        if base.camera.getParent() == self.ballFollow:
            if doInterval:
                curHpr = camera.getHpr(render)
                angle = PythonUtil.closestDestAngle2(curHpr[0], 0)
                self.camInterval = Sequence(Func(base.camera.wrtReparentTo, render), LerpPosHprInterval(base.camera, 2, self.camTopViewPos, self.camTopViewHpr))
                self.camInterval.start()
            else:
                base.camera.reparentTo(render)
                base.camera.setPos(self.camTopViewPos)
                base.camera.setHpr(self.camTopViewHpr)
        elif doInterval:
            curHpr = camera.getHpr(self.ballFollow)
            angle = PythonUtil.closestDestAngle2(curHpr[0], 0)
            self.camInterval = Sequence(Func(base.camera.wrtReparentTo, self.ballFollow), LerpPosHprInterval(base.camera, 2, self.camPosBallFollow, self.camHprBallFollow))
            self.camInterval.start()
        else:
            base.camera.reparentTo(self.ballFollow)
            base.camera.setPos(self.camPosBallFollow)
            base.camera.setHpr(self.camHprBallFollow)

    def doFlyOverMovie(self, avId):
        title = GolfGlobals.getCourseName(self.golfCourse.courseId) + ' :\n ' + GolfGlobals.getHoleName(self.holeId) + '\n' + TTLocalizer.GolfPar + ' : ' + '%s' % self.holeInfo['par']
        self.titleLabel = DirectLabel(parent=aspect2d, relief=None, pos=(0, 0, 0.8), text_align=TextNode.ACenter, text=title, text_scale=0.12, text_font=ToontownGlobals.getSignFont(), text_fg=(1, 0.8, 0.4, 1))
        self.titleLabel.setBin('opaque', 19)
        self.titleLabel.hide()
        self.needToDoFlyOver = False
        bamFile = self.holeInfo['terrainModel']
        fileName = bamFile.split('/')[-1]
        dotIndex = fileName.find('.')
        baseName = fileName[0:dotIndex]
        camModelName = baseName + '_cammodel.bam'
        cameraName = baseName + '_camera.bam'
        path = bamFile[0:bamFile.find(fileName)]
        camModelFullPath = path + camModelName
        cameraAnimFullPath = path + cameraName
        try:
            self.flyOverActor = Actor.Actor(camModelFullPath, {'camera': cameraAnimFullPath})
        except StandardError:
            self.notify.debug("Couldn't find flyover %s" % camModelFullPath)
            return False

        base.transitions.noIris()
        self.flyOverActor.reparentTo(render)
        self.flyOverActor.setBlend(frameBlend=True)
        flyOverJoint = self.flyOverActor.find('**/camera1')
        children = flyOverJoint.getChildren()
        numChild = children.getNumPaths()
        for i in xrange(numChild):
            childNodePath = children.getPath(i)
            childNodePath.removeNode()

        self.flyOverJoint = flyOverJoint
        self.flyOverInterval = Sequence(Func(base.camera.reparentTo, flyOverJoint), Func(base.camera.clearTransform), Func(self.titleLabel.show), ActorInterval(self.flyOverActor, 'camera'), Func(base.camera.reparentTo, self.ballFollow), Func(base.camera.setPos, self.camPosBallFollow), Func(base.camera.setHpr, self.camHprBallFollow))
        if avId == localAvatar.doId:
            self.flyOverInterval.append(Func(self.setCamera2Ball))
            self.flyOverInterval.append(Func(self.safeRequestToState, 'ChooseTee'))
        else:
            self.flyOverInterval.append(Func(self.setCamera2Ball))
            self.flyOverInterval.append(Func(self.safeRequestToState, 'WatchTee'))
        self.flyOverInterval.append(Func(self.titleLabel.hide))
        self.flyOverInterval.append(Func(self.takeOutToon, avId))
        self.flyOverInterval.start()
        return True

    def avExited(self, avId):
        if self.state == 'Playback' and self.currentGolfer == avId:
            pass
        else:
            self.ballDict[avId]['golfBallGeom'].hide()

    def orientCameraRay(self):
        pos = base.camera.getPos(self.terrainModel)
        self.cameraRayNodePath.setPos(pos)
        self.cameraRayNodePath.lookAt(self.ballFollow)
        renderPos = self.cameraRayNodePath.getPos(render)
        if renderPos != pos:
            self.notify.debug('orientCamerRay this should not happen')
        ballPos = self.ballFollow.getPos(self.terrainModel)
        dirCam = Vec3(ballPos - pos)
        dirCam.normalize()
        self.cameraRay.set(pos, dirCam)

    def performSwing(self, ball, power, dirX, dirY):
        startTime = globalClock.getRealTime()
        avId = base.localAvatar.doId
        position = ball.getPosition()
        x = position[0]
        y = position[1]
        z = position[2]
        if avId not in self.golfCourse.drivingToons:
            x = position[0]
            y = position[1]
            z = position[2]
        self.swingTime = cycleTime
        lift = 0
        ball = self.ball
        forceMove = 2500
        if power > 50:
            lift = 0
        ball.enable()
        ball.setPosition(x, y, z)
        ball.setLinearVel(0.0, 0.0, 0.0)
        ball.setAngularVel(0.0, 0.0, 0.0)
        ball.addForce(Vec3(dirX * forceMove * power / 100.0, dirY * forceMove * power / 100.0, lift))
        self.initRecord()
        safety = 0
        self.llv = None
        self.record(ball)
        while ball.isEnabled() and len(self.recording) < 2000:
            self.preStep()
            self.simulate()
            self.postStep()
            self.record(ball)
            safety += 1

        self.record(ball)
        midTime = globalClock.getRealTime()
        self.processRecording()
        self.processAVRecording()
        self.notify.debug('Recording End time %s cycle %s len %s avLen %s' % (self.timingSimTime,
         self.getSimCycleTime(),
         len(self.recording),
         len(self.aVRecording)))
        self.request('WaitPlayback')
        length = len(self.recording) - 1
        x = self.recording[length][1]
        y = self.recording[length][2]
        z = self.recording[length][3]
        self.ballPos[avId] = Vec3(x, y, z)
        endTime = globalClock.getRealTime()
        diffTime = endTime - startTime
        fpsTime = self.frame / diffTime
        self.notify.debug('Time Start %s Mid %s End %s Diff %s Fps %s frames %s' % (startTime,
         midTime,
         endTime,
         diffTime,
         fpsTime,
         self.frame))
        self.ballMovie2Client(cycleTime, avId, self.recording, self.aVRecording, self.ballInHoleFrame, self.ballTouchedHoleFrame, self.ballFirstTouchedHoleFrame)
        return

    def handleBallHitNonGrass(self, c0, c1):
        if not self.inPlayBack:
            return
        golfBallPos = self.curGolfBall().getPosition()
        if self.lastBumpSfxPos == golfBallPos:
            return
        if GolfGlobals.HARD_COLLIDE_ID in [c0, c1]:
            if not self.bumpHardSfx.status() == self.bumpHardSfx.PLAYING:
                distance = (golfBallPos - self.lastBumpSfxPos).length()
                if distance > 2.0:
                    base.playSfx(self.bumpHardSfx)
                    self.lastBumpSfxPos = golfBallPos
        elif GolfGlobals.MOVER_COLLIDE_ID in [c0, c1]:
            if not self.bumpMoverSfx.status() == self.bumpMoverSfx.PLAYING:
                base.playSfx(self.bumpMoverSfx)
                self.lastBumpSfxPos = golfBallPos
        elif GolfGlobals.WINDMILL_BASE_COLLIDE_ID in [c0, c1]:
            if not self.bumpWindmillSfx.status() == self.bumpWindmillSfx.PLAYING:
                base.playSfx(self.bumpWindmillSfx)
                self.lastBumpSfxPos = golfBallPos

    def safeRequestToState(self, newState):
        doingRequest = False
        if self.state in self.defaultTransitions:
            if newState in self.defaultTransitions[self.state]:
                self.request(newState)
                doingRequest = True
        if not doingRequest:
            self.notify.warning('ignoring transition from %s to %s' % (self.state, newState))

    def doMagicWordHeading(self, heading):
        if self.state == 'Aim':
            self.aimMomentum = 0.0
            self.ballFollow.setH(float(heading))

    def _handleClientCleanup(self):
        self.removePlayBackDelayDelete()
        self.ignore('clientCleanup')
