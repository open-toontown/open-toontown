import math
from pandac.PandaModules import CollisionTube
from pandac.PandaModules import CollisionNode
from pandac.PandaModules import Point3
from pandac.PandaModules import VBase3
from pandac.PandaModules import RopeNode
from direct.interval.IntervalGlobal import LerpPosHprInterval
from direct.interval.IntervalGlobal import LerpPosInterval
from direct.interval.IntervalGlobal import Wait
from direct.interval.IntervalGlobal import ActorInterval
from direct.interval.MetaInterval import Sequence
from direct.interval.MetaInterval import Parallel
from direct.interval.FunctionInterval import Func
from direct.showutil.Rope import Rope
from direct.showbase.PythonUtil import fitDestAngle2Src
from direct.fsm.StatePush import StateVar, FunctionCall
from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownGlobals
from toontown.effects import Splash
from toontown.minigame.MinigamePowerMeter import MinigamePowerMeter
from toontown.minigame.ArrowKeys import ArrowKeys
from . import PartyGlobals
from . import PartyUtils
from .DistributedPartyTeamActivity import DistributedPartyTeamActivity

class DistributedPartyTugOfWarActivity(DistributedPartyTeamActivity):
    notify = directNotify.newCategory('DistributedPartyTugOfWarActivity')

    def __init__(self, cr):
        DistributedPartyTeamActivity.__init__(self, cr, PartyGlobals.ActivityIds.PartyTugOfWar, startDelay=PartyGlobals.TugOfWarStartDelay)
        self.buttons = [0, 1]
        self.arrowKeys = None
        self.keyTTL = []
        self.idealRate = 0.0
        self.keyRate = 0
        self.allOutMode = False
        self.rateMatchAward = 0.0
        self.toonIdsToStartPositions = {}
        self.toonIdsToIsPullingFlags = {}
        self.toonIdsToRightHands = {}
        self.fallenToons = []
        self.fallenPositions = []
        self.unusedFallenPositionsIndices = [0,
         1,
         2,
         3]
        self.toonIdsToAnimIntervals = {}
        self.tugRopes = []
        return

    def generate(self):
        DistributedPartyTeamActivity.generate(self)
        self._hopOffFinishedSV = StateVar(True)
        self._rewardFinishedSV = StateVar(True)
        self._isWalkStateReadyFC = FunctionCall(self._testWalkStateReady, self._hopOffFinishedSV, self._rewardFinishedSV)

    def delete(self):
        self._isWalkStateReadyFC.destroy()
        self._hopOffFinishedSV.destroy()
        self._rewardFinishedSV.destroy()
        DistributedPartyTeamActivity.delete(self)

    def handleToonJoined(self, toonId):
        DistributedPartyTeamActivity.handleToonJoined(self, toonId)
        self.toonIdsToAnimIntervals[toonId] = None
        if toonId == base.localAvatar.doId:
            base.cr.playGame.getPlace().fsm.request('activity')
            camera.wrtReparentTo(self.root)
            self.cameraMoveIval = LerpPosHprInterval(camera, 1.5, PartyGlobals.TugOfWarCameraPos, PartyGlobals.TugOfWarCameraInitialHpr, other=self.root)
            self.cameraMoveIval.start()
            self.localToonPosIndex = self.getIndex(base.localAvatar.doId, self.localToonTeam)
            self.notify.debug('posIndex: %d' % self.localToonPosIndex)
            toon = self.getAvatar(toonId)
            targetPos = self.dockPositions[self.localToonTeam][self.localToonPosIndex]
            if toon.getZ(self.root) < PartyGlobals.TugOfWarToonPositionZ:
                toon.setZ(self.root, PartyGlobals.TugOfWarToonPositionZ)
            targetH = fitDestAngle2Src(toon.getH(self.root), PartyGlobals.TugOfWarHeadings[self.localToonTeam])
            travelVector = targetPos - toon.getPos(self.root)
            duration = travelVector.length() / 5.0
            if self.toonIdsToAnimIntervals[toonId] is not None:
                self.toonIdsToAnimIntervals[toonId].finish()
            self.toonIdsToAnimIntervals[toonId] = Sequence(Func(toon.startPosHprBroadcast, 0.1), Func(toon.b_setAnimState, 'run'), LerpPosHprInterval(toon, duration, targetPos, VBase3(targetH, 0.0, 0.0), other=self.root), Func(toon.stopPosHprBroadcast), Func(toon.b_setAnimState, 'neutral'))
            self.toonIdsToAnimIntervals[toonId].start()
        return

    def handleToonExited(self, toonId):
        DistributedPartyTeamActivity.handleToonExited(self, toonId)
        if toonId == base.localAvatar.doId:
            self.cameraMoveIval.pause()
            if toonId not in self.fallenToons:
                if toonId in self.toonIdsToAnimIntervals and self.toonIdsToAnimIntervals[toonId] is not None:
                    self.toonIdsToAnimIntervals[toonId].finish()
                toon = self.getAvatar(toonId)
                targetH = fitDestAngle2Src(toon.getH(self.root), 180.0)
                targetPos = self.hopOffPositions[self.getTeam(toonId)][self.getIndex(toonId, self.getTeam(toonId))]
                hopOffAnim = Sequence(Func(toon.startPosHprBroadcast, 0.1), toon.hprInterval(0.2, VBase3(targetH, 0.0, 0.0), other=self.root), Func(toon.b_setAnimState, 'jump', 1.0), Wait(0.4), PartyUtils.arcPosInterval(0.75, toon, targetPos, 5.0, self.root), Func(toon.stopPosHprBroadcast), Func(toon.sendCurrentPosition), Func(self.hopOffFinished, toonId))
                self.toonIdsToAnimIntervals[toonId] = hopOffAnim
                self._hopOffFinishedSV.set(False)
                self.toonIdsToAnimIntervals[toonId].start()
            else:
                self._hopOffFinishedSV.set(True)
                del self.toonIdsToAnimIntervals[toonId]
        return

    def handleRewardDone(self):
        self._rewardFinishedSV.set(True)

    def _testWalkStateReady(self, hoppedOff, rewardFinished):
        if hoppedOff and rewardFinished:
            DistributedPartyTeamActivity.handleRewardDone(self)

    def hopOffFinished(self, toonId):
        if hasattr(self, 'toonIdsToAnimIntervals') and toonId in self.toonIdsToAnimIntervals:
            del self.toonIdsToAnimIntervals[toonId]
        if toonId == base.localAvatar.doId:
            if hasattr(self._hopOffFinishedSV, '_value'):
                self._hopOffFinishedSV.set(True)

    def handleToonShifted(self, toonId):
        if toonId == base.localAvatar.doId:
            self.localToonPosIndex = self.getIndex(base.localAvatar.doId, self.localToonTeam)
            if self.toonIdsToAnimIntervals[toonId] is not None:
                self.toonIdsToAnimIntervals[toonId].finish()
            toon = self.getAvatar(toonId)
            targetPos = self.dockPositions[self.localToonTeam][self.localToonPosIndex]
            self.toonIdsToAnimIntervals[toonId] = Sequence(Wait(0.6), Func(toon.startPosHprBroadcast, 0.1), Func(toon.b_setAnimState, 'run'), toon.posInterval(0.5, targetPos, other=self.root), Func(toon.stopPosHprBroadcast), Func(toon.b_setAnimState, 'neutral'))
            self.toonIdsToAnimIntervals[toonId].start()
        return

    def handleToonDisabled(self, toonId):
        if toonId in self.toonIdsToAnimIntervals:
            if self.toonIdsToAnimIntervals[toonId]:
                if self.toonIdsToAnimIntervals[toonId].isPlaying():
                    self.toonIdsToAnimIntervals[toonId].finish()
            else:
                self.notify.debug('self.toonIdsToAnimIntervals[%d] is none' % toonId)

    def setToonsPlaying(self, leftTeamToonIds, rightTeamToonIds):
        DistributedPartyTeamActivity.setToonsPlaying(self, leftTeamToonIds, rightTeamToonIds)
        self.toonIdsToRightHands.clear()
        for toonId in self.getToonIdsAsList():
            toon = self.getAvatar(toonId)
            if toon:
                self.toonIdsToRightHands[toonId] = toon.getRightHands()[0]

    def load(self):
        DistributedPartyTeamActivity.load(self)
        self.loadModels()
        self.loadGuiElements()
        self.loadSounds()
        self.loadIntervals()
        self.arrowKeys = ArrowKeys()

    def loadModels(self):
        self.playArea = loader.loadModel('phase_13/models/parties/partyTugOfWar')
        self.playArea.reparentTo(self.root)
        self.sign.reparentTo(self.playArea.find('**/TugOfWar_sign_locator'))
        self.dockPositions = [[], []]
        for i in range(4):
            self.dockPositions[0].append(Point3(-PartyGlobals.TugOfWarInitialToonPositionsXOffset - PartyGlobals.TugOfWarToonPositionXSeparation * i, 0.0, PartyGlobals.TugOfWarToonPositionZ))

        for i in range(4):
            self.dockPositions[1].append(Point3(PartyGlobals.TugOfWarInitialToonPositionsXOffset + PartyGlobals.TugOfWarToonPositionXSeparation * i, 0.0, PartyGlobals.TugOfWarToonPositionZ))

        self.hopOffPositions = [[], []]
        for i in range(1, 5):
            self.hopOffPositions[PartyGlobals.TeamActivityTeams.LeftTeam].append(self.playArea.find('**/leftTeamHopOff%d_locator' % i).getPos())
            self.hopOffPositions[PartyGlobals.TeamActivityTeams.RightTeam].append(self.playArea.find('**/rightTeamHopOff%d_locator' % i).getPos())

        for i in range(1, 5):
            pos = self.playArea.find('**/fallenToon%d_locator' % i).getPos()
            self.fallenPositions.append(pos)

        self.joinCollision = []
        self.joinCollisionNodePaths = []
        for i in range(len(PartyGlobals.TeamActivityTeams)):
            collShape = CollisionTube(PartyGlobals.TugOfWarJoinCollisionEndPoints[0], PartyGlobals.TugOfWarJoinCollisionEndPoints[1], PartyGlobals.TugOfWarJoinCollisionRadius)
            collShape.setTangible(True)
            self.joinCollision.append(CollisionNode('TugOfWarJoinCollision%d' % i))
            self.joinCollision[i].addSolid(collShape)
            tubeNp = self.playArea.attachNewNode(self.joinCollision[i])
            tubeNp.node().setCollideMask(ToontownGlobals.WallBitmask)
            self.joinCollisionNodePaths.append(tubeNp)
            self.joinCollisionNodePaths[i].setPos(PartyGlobals.TugOfWarJoinCollisionPositions[i])

        self.__enableCollisions()
        ropeModel = loader.loadModel('phase_4/models/minigames/tug_of_war_rope')
        self.ropeTexture = ropeModel.findTexture('*')
        ropeModel.removeNode()
        for i in range(PartyGlobals.TugOfWarMaximumPlayersPerTeam * 2 - 1):
            rope = Rope(self.uniqueName('TugRope%d' % i))
            if rope.showRope:
                rope.ropeNode.setRenderMode(RopeNode.RMBillboard)
                rope.ropeNode.setThickness(0.2)
                rope.setTexture(self.ropeTexture)
                rope.ropeNode.setUvMode(RopeNode.UVDistance)
                rope.ropeNode.setUvDirection(1)
                rope.setTransparency(1)
                rope.setColor(0.89, 0.89, 0.6, 1.0)
                rope.reparentTo(self.root)
                rope.stash()
            self.tugRopes.append(rope)

        self.splash = Splash.Splash(self.root)
        self.splash.setScale(2.0, 4.0, 1.0)
        pos = self.fallenPositions[0]
        self.splash.setPos(pos[0], pos[1], PartyGlobals.TugOfWarSplashZOffset)
        self.splash.hide()

    def loadGuiElements(self):
        self.powerMeter = MinigamePowerMeter(PartyGlobals.TugOfWarPowerMeterSize)
        self.powerMeter.reparentTo(aspect2d)
        self.powerMeter.setPos(0.0, 0.0, 0.6)
        self.powerMeter.hide()
        self.arrows = [None] * 2
        for x in range(len(self.arrows)):
            self.arrows[x] = loader.loadModel('phase_3/models/props/arrow')
            self.arrows[x].reparentTo(self.powerMeter)
            self.arrows[x].setScale(0.2 - 0.4 * x, 0.2, 0.2)
            self.arrows[x].setPos(0.12 - 0.24 * x, 0, -.26)

        return

    def loadSounds(self):
        self.splashSound = base.loader.loadSfx('phase_4/audio/sfx/MG_cannon_splash.ogg')
        self.whistleSound = base.loader.loadSfx('phase_4/audio/sfx/AA_sound_whistle.ogg')

    def loadIntervals(self):
        self.updateIdealRateInterval = Sequence()
        self.updateIdealRateInterval.append(Wait(PartyGlobals.TugOfWarTargetRateList[0][0]))
        for i in range(1, len(PartyGlobals.TugOfWarTargetRateList)):
            duration = PartyGlobals.TugOfWarTargetRateList[i][0]
            idealRate = PartyGlobals.TugOfWarTargetRateList[i][1]
            self.updateIdealRateInterval.append(Func(self.setIdealRate, idealRate))
            if i == len(PartyGlobals.TugOfWarTargetRateList) - 1:
                self.updateIdealRateInterval.append(Func(setattr, self, 'allOutMode', True))
            else:
                self.updateIdealRateInterval.append(Wait(duration))

        self.updateKeyPressRateInterval = Sequence(Wait(PartyGlobals.TugOfWarKeyPressUpdateRate), Func(self.updateKeyPressRate))
        self.reportToServerInterval = Sequence(Wait(PartyGlobals.TugOfWarKeyPressReportRate), Func(self.reportToServer))
        self.setupInterval = Parallel()
        self.globalSetupInterval = Sequence(Wait(PartyGlobals.TugOfWarReadyDuration + PartyGlobals.TugOfWarGoDuration), Func(self.tightenRopes))
        self.localSetupInterval = Sequence(Func(self.setStatus, TTLocalizer.PartyTugOfWarReady), Func(self.showStatus), Wait(PartyGlobals.TugOfWarReadyDuration), Func(base.playSfx, self.whistleSound), Func(self.setStatus, TTLocalizer.PartyTugOfWarGo), Wait(PartyGlobals.TugOfWarGoDuration), Func(self.enableKeys), Func(self.hideStatus), Func(self.updateIdealRateInterval.start), Func(self.updateKeyPressRateInterval.loop), Func(self.reportToServerInterval.loop))
        self.splashInterval = Sequence(Func(base.playSfx, self.splashSound), Func(self.splash.play))

    def unload(self):
        DistributedPartyTeamActivity.unload(self)
        self.arrowKeys.destroy()
        self.unloadIntervals()
        self.unloadModels()
        self.unloadGuiElements()
        self.unloadSounds()
        if hasattr(self, 'toonIds'):
            del self.toonIds
        del self.buttons
        del self.arrowKeys
        del self.keyTTL
        del self.idealRate
        del self.keyRate
        del self.allOutMode
        del self.rateMatchAward
        del self.toonIdsToStartPositions
        del self.toonIdsToIsPullingFlags
        del self.toonIdsToRightHands
        del self.fallenToons
        del self.fallenPositions
        del self.unusedFallenPositionsIndices
        self.toonIdsToAnimIntervals.clear()
        del self.toonIdsToAnimIntervals

    def unloadModels(self):
        self.playArea.removeNode()
        del self.playArea
        del self.dockPositions
        del self.hopOffPositions
        self.__disableCollisions()
        while len(self.joinCollision) > 0:
            collNode = self.joinCollision.pop()
            del collNode

        while len(self.joinCollisionNodePaths) > 0:
            collNodePath = self.joinCollisionNodePaths.pop()
            collNodePath.removeNode()
            del collNodePath

        while len(self.tugRopes) > 0:
            rope = self.tugRopes.pop()
            if rope is not None:
                rope.removeNode()
            del rope

        del self.tugRopes
        self.splash.destroy()
        del self.splash
        return

    def unloadGuiElements(self):
        for arrow in self.arrows:
            if arrow is not None:
                arrow.removeNode()
                del arrow

        del self.arrows
        if self.powerMeter is not None:
            self.powerMeter.cleanup()
            del self.powerMeter
        return

    def unloadSounds(self):
        del self.splashSound
        del self.whistleSound

    def unloadIntervals(self):
        self.updateIdealRateInterval.pause()
        del self.updateIdealRateInterval
        self.updateKeyPressRateInterval.pause()
        del self.updateKeyPressRateInterval
        self.reportToServerInterval.pause()
        del self.reportToServerInterval
        self.setupInterval.pause()
        del self.setupInterval
        self.globalSetupInterval.pause()
        del self.globalSetupInterval
        self.localSetupInterval.pause()
        del self.localSetupInterval
        self.splashInterval.pause()
        del self.splashInterval

    def __enableCollisions(self):
        for i in range(len(PartyGlobals.TeamActivityTeams)):
            self.accept('enterTugOfWarJoinCollision%d' % i, getattr(self, '_join%s' % PartyGlobals.TeamActivityTeams.getString(i)))

    def __disableCollisions(self):
        for i in range(len(PartyGlobals.TeamActivityTeams)):
            self.ignore('enterTugOfWarJoinCollision%d' % i)

    def startWaitForEnough(self):
        DistributedPartyTeamActivity.startWaitForEnough(self)
        self.__enableCollisions()

    def finishWaitForEnough(self):
        DistributedPartyTeamActivity.finishWaitForEnough(self)
        self.__disableCollisions()

    def startWaitToStart(self, waitStartTimestamp):
        DistributedPartyTeamActivity.startWaitToStart(self, waitStartTimestamp)
        self.__enableCollisions()

    def finishWaitToStart(self):
        DistributedPartyTeamActivity.finishWaitToStart(self)
        self.__disableCollisions()

    def startRules(self):
        DistributedPartyTeamActivity.startRules(self)
        self.setUpRopes()
        if self.isLocalToonPlaying:
            self.showControls()

    def finishRules(self):
        DistributedPartyTeamActivity.finishRules(self)
        if self.activityFSM.getCurrentOrNextState() == 'WaitForEnough':
            self.hideRopes()
            self.hideControls()

    def finishWaitForServer(self):
        DistributedPartyTeamActivity.finishWaitForServer(self)
        if self.activityFSM.getCurrentOrNextState() == 'WaitForEnough':
            self.hideRopes()
            self.hideControls()

    def startActive(self):
        DistributedPartyTeamActivity.startActive(self)
        self.toonIdsToStartPositions.clear()
        self.toonIdsToIsPullingFlags.clear()
        for toonId in self.getToonIdsAsList():
            self.toonIdsToIsPullingFlags[toonId] = False
            toon = self.getAvatar(toonId)
            if toon:
                self.toonIdsToStartPositions[toonId] = toon.getPos(self.root)
            else:
                self.notify.warning("couldn't find toon %d assigning 0,0,0 to startPos" % toonId)
                self.toonIdsToStartPositions[toonId] = Point3(0, 0, 0)

        self.unusedFallenPositionsIndices = [0,
         1,
         2,
         3]
        self.setupInterval = Parallel(self.globalSetupInterval)
        if self.isLocalToonPlaying:
            self.keyTTL = []
            self.idealForce = 0.0
            self.keyRate = 0
            self.rateMatchAward = 0.0
            self.allOutMode = False
            self.setIdealRate(PartyGlobals.TugOfWarTargetRateList[0][1])
            self.setupInterval.append(self.localSetupInterval)
        self.setupInterval.start()

    def finishActive(self):
        DistributedPartyTeamActivity.finishActive(self)
        self.hideControls()
        self.disableKeys()
        self.setupInterval.pause()
        self.reportToServerInterval.pause()
        self.updateKeyPressRateInterval.pause()
        self.updateIdealRateInterval.pause()
        self.hideRopes()

    def startConclusion(self, losingTeam):
        DistributedPartyTeamActivity.startConclusion(self, losingTeam)
        if self.isLocalToonPlaying:
            self._rewardFinishedSV.set(False)
            if losingTeam == PartyGlobals.TeamActivityNeitherTeam:
                self.setStatus(TTLocalizer.PartyTeamActivityGameTie)
            else:
                self.setStatus(TTLocalizer.PartyTugOfWarGameEnd)
            self.showStatus()
        if losingTeam == PartyGlobals.TeamActivityNeitherTeam:
            for toonId in self.getToonIdsAsList():
                if self.getAvatar(toonId):
                    self.getAvatar(toonId).loop('neutral')

        else:
            for toonId in self.toonIds[losingTeam]:
                if self.getAvatar(toonId):
                    self.getAvatar(toonId).loop('neutral')

            for toonId in self.toonIds[1 - losingTeam]:
                if self.getAvatar(toonId):
                    self.getAvatar(toonId).loop('victory')

        for ival in list(self.toonIdsToAnimIntervals.values()):
            if ival is not None:
                ival.finish()

        return

    def finishConclusion(self):
        DistributedPartyTeamActivity.finishConclusion(self)
        self.fallenToons = []

    def getTitle(self):
        return TTLocalizer.PartyTugOfWarTitle

    def getInstructions(self):
        return TTLocalizer.TugOfWarInstructions

    def showControls(self):
        for arrow in self.arrows:
            arrow.setColor(PartyGlobals.TugOfWarDisabledArrowColor)

        self.powerMeter.setTarget(PartyGlobals.TugOfWarTargetRateList[0][1])
        self.powerMeter.setPower(PartyGlobals.TugOfWarTargetRateList[0][1])
        self.powerMeter.setBarColor((0.0, 1.0, 0.0, 0.5))
        self.powerMeter.clearTooSlowTooFast()
        self.powerMeter.show()

    def hideControls(self):
        self.powerMeter.hide()

    def setUpRopes(self):
        self.notify.debug('setUpRopes')
        ropeIndex = 0
        leftToonId = -1
        if self.toonIds[PartyGlobals.TeamActivityTeams.LeftTeam]:
            leftToonId = self.toonIds[PartyGlobals.TeamActivityTeams.LeftTeam][0]
        rightToonId = -1
        if self.toonIds[PartyGlobals.TeamActivityTeams.RightTeam]:
            rightToonId = self.toonIds[PartyGlobals.TeamActivityTeams.RightTeam][0]
        if leftToonId in self.toonIdsToRightHands and rightToonId in self.toonIdsToRightHands:
            self.tugRopes[ropeIndex].setup(3, ((self.toonIdsToRightHands[leftToonId], (0, 0, 0)), (self.root, (0.0, 0.0, 2.5)), (self.toonIdsToRightHands[rightToonId], (0, 0, 0))), [0,
             0,
             0,
             1,
             1,
             1])
            self.tugRopes[ropeIndex].unstash()
            ropeIndex += 1
        teams = [PartyGlobals.TeamActivityTeams.LeftTeam, PartyGlobals.TeamActivityTeams.RightTeam]
        for currTeam in teams:
            numToons = len(self.toonIds[currTeam])
            if numToons > 1:
                for i in range(numToons - 1, 0, -1):
                    toon1 = self.toonIds[currTeam][i]
                    toon2 = self.toonIds[currTeam][i - 1]
                    if toon1 not in self.toonIdsToRightHands:
                        self.notify.warning('Toon in tug of war activity but not properly setup:  %s' % toon1)
                    elif toon2 not in self.toonIdsToRightHands:
                        self.notify.warning('Toon in tug of war activity but not properly setup:  %s' % toon2)
                    else:
                        self.notify.debug('Connecting rope between toon %d and toon %d of team %d.' % (i, i - 1, currTeam))
                        self.tugRopes[ropeIndex].setup(3, ((self.toonIdsToRightHands[toon1], (0, 0, 0)), (self.toonIdsToRightHands[toon1], (0, 0, 0)), (self.toonIdsToRightHands[toon2], (0, 0, 0))), [0,
                         0,
                         0,
                         1,
                         1,
                         1])
                        self.tugRopes[ropeIndex].unstash()
                        ropeIndex += 1

    def tightenRopes(self):
        self.notify.debug('tightenRopes')
        self.tugRopes[0].setup(3, ((self.toonIdsToRightHands[self.toonIds[PartyGlobals.TeamActivityTeams.LeftTeam][0]], (0, 0, 0)), (self.toonIdsToRightHands[self.toonIds[PartyGlobals.TeamActivityTeams.LeftTeam][0]], (0, 0, 0)), (self.toonIdsToRightHands[self.toonIds[PartyGlobals.TeamActivityTeams.RightTeam][0]], (0, 0, 0))), [0,
         0,
         0,
         1,
         1,
         1])

    def hideRopes(self):
        self.notify.debug('hideRopes')
        for rope in self.tugRopes:
            rope.stash()

    def handleGameTimerExpired(self):
        self.disableKeys()

    def setIdealRate(self, idealRate):
        self.notify.debug('setIdealRate( %d )' % idealRate)
        self.idealRate = idealRate
        self.idealForce = self.advantage * (4 + 0.4 * self.idealRate)

    def updateKeyPressRate(self):
        for i in range(len(self.keyTTL)):
            self.keyTTL[i] -= PartyGlobals.TugOfWarKeyPressUpdateRate

        for i in range(len(self.keyTTL)):
            if self.keyTTL[i] <= 0.0:
                a = self.keyTTL[0:i]
                del self.keyTTL
                self.keyTTL = a
                break

        self.keyRate = len(self.keyTTL)
        if self.keyRate == self.idealRate or self.keyRate == self.idealRate + 1:
            self.rateMatchAward += 0.3
        else:
            self.rateMatchAward = 0.0

    def reportToServer(self):
        self.currentForce = self.computeForce(self.keyRate)
        self.sendUpdate('reportKeyRateForce', [self.keyRate, self.currentForce])
        self.setSpeedGauge()
        self.setAnimState(base.localAvatar.doId, self.keyRate)

    def computeForce(self, keyRate):
        F = 0
        if self.allOutMode:
            F = 0.75 * keyRate
        else:
            stdDev = 0.25 * self.idealRate
            F = self.advantage * (self.rateMatchAward + 4 + 0.4 * self.idealRate) * math.pow(math.e, -math.pow(keyRate - self.idealRate, 2) / (2.0 * math.pow(stdDev, 2)))
        return F

    def setSpeedGauge(self):
        self.powerMeter.setPower(self.keyRate)
        self.powerMeter.setTarget(self.idealRate)
        if not self.allOutMode:
            self.powerMeter.updateTooSlowTooFast()
            index = float(self.currentForce) / self.idealForce
            bonus = 0.0
            if index > 1.0:
                bonus = max(1.0, index - 1.0)
                index = 1.0
            color = (0,
             0.75 * index + 0.25 * bonus,
             0.75 * (1 - index),
             0.5)
            self.powerMeter.setBarColor(color)
        else:
            self.powerMeter.setBarColor((0.0, 1.0, 0.0, 0.5))

    def updateToonKeyRate(self, toonId, keyRate):
        if toonId != base.localAvatar.doId:
            self.setAnimState(toonId, keyRate)

    def setAnimState(self, toonId, keyRate):
        if self.activityFSM.state != 'Active':
            return
        toon = self.getAvatar(toonId)
        if toonId not in self.toonIdsToIsPullingFlags:
            if self.getTeam(toonId) == None:
                self.notify.warning("setAnimState called with toonId (%d) that wasn't in self.toonIds" % toonId)
                return
            else:
                self.notify.warning('setAnimState called with toonId (%d) that was in self.toonIds but not in self.toonIdsToIsPullingFlags. Adding it.' % toonId)
                self.toonIdsToIsPullingFlags[toonId] = False
        if keyRate > 0 and not self.toonIdsToIsPullingFlags[toonId]:
            if toon:
                toon.loop('tug-o-war')
            else:
                self.notify.warning('toon %d is None, skipping toon.loop(tugowar)' % toonId)
            self.toonIdsToIsPullingFlags[toonId] = True
        if keyRate <= 0 and self.toonIdsToIsPullingFlags[toonId]:
            if toon:
                toon.pose('tug-o-war', 3)
                toon.startLookAround()
            else:
                self.notify.warning('toon %d is None, skipping toon.startLookAround' % toonId)
            self.toonIdsToIsPullingFlags[toonId] = False
        return

    def enableKeys(self):
        self.notify.debug('enableKeys')
        self.arrowKeys.setPressHandlers([lambda : self.__pressHandler(2),
         lambda : self.__pressHandler(3),
         lambda : self.__pressHandler(1),
         lambda : self.__pressHandler(0)])
        self.arrowKeys.setReleaseHandlers([lambda : self.__releaseHandler(2),
         lambda : self.__releaseHandler(3),
         lambda : self.__releaseHandler(1),
         lambda : self.__releaseHandler(0)])
        for arrow in self.arrows:
            arrow.setColor(PartyGlobals.TugOfWarEnabledArrowColor)

    def disableKeys(self):
        self.arrowKeys.setPressHandlers(self.arrowKeys.NULL_HANDLERS)
        self.arrowKeys.setReleaseHandlers(self.arrowKeys.NULL_HANDLERS)

    def __pressHandler(self, index):
        if index == self.buttons[0]:
            self.arrows[index].setColor(PartyGlobals.TugOfWarHilightedArrowColor)
            self.keyTTL.insert(0, PartyGlobals.TugOfWarKeyPressTimeToLive)
            self.buttons.reverse()

    def __releaseHandler(self, index):
        if index in self.buttons:
            self.arrows[index].setColor(PartyGlobals.TugOfWarEnabledArrowColor)

    def updateToonPositions(self, offset):
        if self.activityFSM.state != 'Active':
            return
        if self.isLocalToonPlaying:
            camera.lookAt(self.root, offset, 0.0, PartyGlobals.TugOfWarCameraLookAtHeightOffset)
        for toonId in self.getToonIdsAsList():
            if hasattr(self, 'fallenToons') and toonId not in self.fallenToons:
                toon = self.getAvatar(toonId)
                if toon is not None:
                    origPos = self.toonIdsToStartPositions[toonId]
                    curPos = toon.getPos(self.root)
                    newPos = Point3(origPos[0] + offset, curPos[1], curPos[2])
                    if self.toonIdsToAnimIntervals[toonId] != None:
                        if self.toonIdsToAnimIntervals[toonId].isPlaying():
                            self.toonIdsToAnimIntervals[toonId].finish()
                            self.checkIfFallen(toonId)
                    if toonId not in self.fallenToons:
                        self.toonIdsToAnimIntervals[toonId] = Sequence(LerpPosInterval(toon, duration=PartyGlobals.TugOfWarKeyPressReportRate, pos=newPos, other=self.root), Func(self.checkIfFallen, toonId))
                        self.toonIdsToAnimIntervals[toonId].start()

        return

    def checkIfFallen(self, toonId):
        if hasattr(self, 'fallenToons') and toonId not in self.fallenToons:
            toon = self.getAvatar(toonId)
            if toon:
                curPos = toon.getPos(self.root)
                team = self.getTeam(toonId)
                if team == PartyGlobals.TeamActivityTeams.LeftTeam and curPos[0] > -2.0 or team == PartyGlobals.TeamActivityTeams.RightTeam and curPos[0] < 2.0:
                    losingTeam = self.getTeam(toonId)
                    self.throwTeamInWater(losingTeam)
                    self.sendUpdate('reportFallIn', [losingTeam])

    def throwTeamInWater(self, losingTeam):
        self.notify.debug('throwTeamInWater( %s )' % PartyGlobals.TeamActivityTeams.getString(losingTeam))
        splashSet = False
        for toonId in self.toonIds[losingTeam]:
            self.fallenToons.append(toonId)
            toon = self.getAvatar(toonId)
            fallenPosIndex = self.toonIds[losingTeam].index(toonId)
            if fallenPosIndex < 0 or fallenPosIndex >= 4:
                fallenPosIndex = 0
            newPos = self.fallenPositions[fallenPosIndex]
            if toonId in self.toonIdsToAnimIntervals and self.toonIdsToAnimIntervals[toonId] is not None:
                if self.toonIdsToAnimIntervals[toonId].isPlaying():
                    self.toonIdsToAnimIntervals[toonId].finish()
            if toon:
                parallel = Parallel(ActorInterval(actor=toon, animName='slip-forward', duration=2.0), LerpPosInterval(toon, duration=2.0, pos=newPos, other=self.root))
            else:
                self.notify.warning('toon %d is none, skipping slip-forward' % toonId)
                parallel = Parallel()
            if not splashSet:
                splashSet = True
                parallel.append(self.splashInterval)
            if toon:
                self.toonIdsToAnimIntervals[toonId] = Sequence(parallel, Func(toon.loop, 'neutral'))
            else:
                self.notify.warning('toon %d is none, skipping toon.loop(neutral)' % toonId)
                self.toonIdsToAnimIntervals[toonId] = parallel
            self.toonIdsToAnimIntervals[toonId].start()

        return

    def setAdvantage(self, advantage):
        DistributedPartyTeamActivity.setAdvantage(self, advantage)
        if self.isLocalToonPlaying:
            self.setIdealRate(PartyGlobals.TugOfWarTargetRateList[0][1])
