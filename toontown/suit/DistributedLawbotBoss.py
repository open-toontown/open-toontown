from direct.showbase.ShowBase import *
from direct.interval.IntervalGlobal import *
from toontown.battle.BattleProps import *
from direct.distributed.ClockDelta import *
from direct.showbase.PythonUtil import Functor
from direct.showbase.PythonUtil import StackTrace
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from panda3d.otp import *
from direct.fsm import FSM
from direct.fsm import ClassicFSM
from direct.fsm import State
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import ToontownBattleGlobals
from . import DistributedBossCog
from toontown.toonbase import TTLocalizer
from . import SuitDNA
from toontown.toon import Toon
from toontown.battle import BattleBase
from direct.directutil import Mopath
from direct.showutil import Rope
from toontown.distributed import DelayDelete
from toontown.battle import MovieToonVictory
from toontown.building import ElevatorUtils
from toontown.battle import RewardPanel
from toontown.toon import NPCToons
from direct.task import Task
import random
import math
import functools
from toontown.coghq import CogDisguiseGlobals
from toontown.building import ElevatorConstants
from toontown.toonbase import ToontownTimer
OneBossCog = None

class DistributedLawbotBoss(DistributedBossCog.DistributedBossCog, FSM.FSM):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedLawbotBoss')
    debugPositions = False

    def __init__(self, cr):
        self.notify.debug('----- __init___')
        DistributedBossCog.DistributedBossCog.__init__(self, cr)
        FSM.FSM.__init__(self, 'DistributedLawbotBoss')
        self.lawyers = []
        self.lawyerRequest = None
        self.bossDamage = 0
        self.attackCode = None
        self.attackAvId = 0
        self.recoverRate = 0
        self.recoverStartTime = 0
        self.bossDamageMovie = None
        self.everThrownPie = 0
        self.battleThreeMusicTime = 0
        self.insidesANodePath = None
        self.insidesBNodePath = None
        self.strafeInterval = None
        self.onscreenMessage = None
        self.bossMaxDamage = ToontownGlobals.LawbotBossMaxDamage
        self.elevatorType = ElevatorConstants.ELEVATOR_CJ
        self.gavels = {}
        self.chairs = {}
        self.cannons = {}
        self.useCannons = 1
        self.juryBoxIval = None
        self.juryTimer = None
        self.witnessToon = None
        self.witnessToonOnstage = False
        self.numToonJurorsSeated = 0
        self.mainDoor = None
        self.reflectedMainDoor = None
        self.panFlashInterval = None
        self.panDamage = ToontownGlobals.LawbotBossDefensePanDamage
        if base.config.GetBool('lawbot-boss-cheat', 0):
            self.panDamage = 25
        self.evidenceHitSfx = None
        self.toonUpSfx = None
        self.bonusTimer = None
        self.warningSfx = None
        self.juryMovesSfx = None
        self.baseColStashed = False
        self.battleDifficulty = 0
        self.bonusWeight = 0
        self.numJurorsLocalToonSeated = 0
        self.cannonIndex = -1
        return

    def announceGenerate(self):
        global OneBossCog
        self.notify.debug('----- announceGenerate')
        DistributedBossCog.DistributedBossCog.announceGenerate(self)
        self.setName(TTLocalizer.LawbotBossName)
        nameInfo = TTLocalizer.BossCogNameWithDept % {'name': self._name,
         'dept': SuitDNA.getDeptFullname(self.style.dept)}
        self.setDisplayName(nameInfo)
        self.piesRestockSfx = loader.loadSfx('phase_5/audio/sfx/LB_receive_evidence.ogg')
        self.rampSlideSfx = loader.loadSfx('phase_9/audio/sfx/CHQ_VP_ramp_slide.ogg')
        self.evidenceHitSfx = loader.loadSfx('phase_11/audio/sfx/LB_evidence_hit.ogg')
        self.warningSfx = loader.loadSfx('phase_9/audio/sfx/CHQ_GOON_tractor_beam_alarmed.ogg')
        self.juryMovesSfx = loader.loadSfx('phase_11/audio/sfx/LB_jury_moves.ogg')
        self.toonUpSfx = loader.loadSfx('phase_11/audio/sfx/LB_toonup.ogg')
        self.strafeSfx = []
        for i in range(10):
            self.strafeSfx.append(loader.loadSfx('phase_3.5/audio/sfx/SA_shred.ogg'))

        render.setTag('pieCode', str(ToontownGlobals.PieCodeNotBossCog))
        insidesA = CollisionPolygon(Point3(4.0, -2.0, 5.0), Point3(-4.0, -2.0, 5.0), Point3(-4.0, -2.0, 0.5), Point3(4.0, -2.0, 0.5))
        insidesANode = CollisionNode('BossZap')
        insidesANode.addSolid(insidesA)
        insidesANode.setCollideMask(ToontownGlobals.PieBitmask | ToontownGlobals.WallBitmask)
        self.insidesANodePath = self.axle.attachNewNode(insidesANode)
        self.insidesANodePath.setTag('pieCode', str(ToontownGlobals.PieCodeBossInsides))
        self.insidesANodePath.stash()
        insidesB = CollisionPolygon(Point3(-4.0, 2.0, 5.0), Point3(4.0, 2.0, 5.0), Point3(4.0, 2.0, 0.5), Point3(-4.0, 2.0, 0.5))
        insidesBNode = CollisionNode('BossZap')
        insidesBNode.addSolid(insidesB)
        insidesBNode.setCollideMask(ToontownGlobals.PieBitmask | ToontownGlobals.WallBitmask)
        self.insidesBNodePath = self.axle.attachNewNode(insidesBNode)
        self.insidesBNodePath.setTag('pieCode', str(ToontownGlobals.PieCodeBossInsides))
        self.insidesBNodePath.stash()
        target = CollisionTube(0, -1, 4, 0, -1, 9, 3.5)
        targetNode = CollisionNode('BossZap')
        targetNode.addSolid(target)
        targetNode.setCollideMask(ToontownGlobals.PieBitmask)
        self.targetNodePath = self.pelvis.attachNewNode(targetNode)
        self.targetNodePath.setTag('pieCode', str(ToontownGlobals.PieCodeBossCog))
        shield = CollisionTube(0, 1, 4, 0, 1, 7, 3.5)
        shieldNode = CollisionNode('BossZap')
        shieldNode.addSolid(shield)
        shieldNode.setCollideMask(ToontownGlobals.PieBitmask | ToontownGlobals.CameraBitmask)
        shieldNodePath = self.pelvis.attachNewNode(shieldNode)
        disk = loader.loadModel('phase_9/models/char/bossCog-gearCollide')
        disk.find('**/+CollisionNode').setName('BossZap')
        disk.reparentTo(self.pelvis)
        disk.setZ(0.8)
        self.loadEnvironment()
        self.__makeWitnessToon()
        self.__loadMopaths()
        localAvatar.chatMgr.chatInputSpeedChat.addCJMenu()
        if OneBossCog != None:
            self.notify.warning('Multiple BossCogs visible.')
        OneBossCog = self
        return

    def disable(self):
        global OneBossCog
        self.notify.debug('----- disable')
        DistributedBossCog.DistributedBossCog.disable(self)
        self.request('Off')
        self.unloadEnvironment()
        self.__cleanupWitnessToon()
        self.__unloadMopaths()
        self.__clearOnscreenMessage()
        taskMgr.remove(self.uniqueName('PieAdvice'))
        self.__cleanupStrafe()
        self.__cleanupJuryBox()
        render.clearTag('pieCode')
        self.targetNodePath.detachNode()
        self.cr.relatedObjectMgr.abortRequest(self.lawyerRequest)
        self.lawyerRequest = None
        self.betweenBattleMusic.stop()
        self.promotionMusic.stop()
        self.stingMusic.stop()
        self.battleTwoMusic.stop()
        self.battleThreeMusic.stop()
        self.epilogueMusic.stop()
        if self.juryTimer:
            self.juryTimer.destroy()
            del self.juryTimer
        if self.bonusTimer:
            self.bonusTimer.destroy()
            del self.bonusTimer
        localAvatar.chatMgr.chatInputSpeedChat.removeCJMenu()
        if OneBossCog == self:
            OneBossCog = None
        return

    def delete(self):
        self.notify.debug('----- delete')
        DistributedBossCog.DistributedBossCog.delete(self)

    def d_hitBoss(self, bossDamage):
        self.notify.debug('----- d_hitBoss')
        self.sendUpdate('hitBoss', [bossDamage])

    def d_healBoss(self, bossHeal):
        self.notify.debug('----- d_bossHeal')
        self.sendUpdate('healBoss', [bossHeal])

    def d_hitBossInsides(self):
        self.notify.debug('----- d_hitBossInsides')
        self.sendUpdate('hitBossInsides', [])

    def d_hitDefensePan(self):
        self.notify.debug('----- d_hitDefensePan')
        self.sendUpdate('hitDefensePan', [])

    def d_hitProsecutionPan(self):
        self.notify.debug('----- d_hitProsecutionPan')
        self.sendUpdate('hitProsecutionPan', [])

    def d_hitToon(self, toonId):
        self.notify.debug('----- d_hitToon')
        self.sendUpdate('hitToon', [toonId])

    def gotToon(self, toon):
        stateName = self.state
        if stateName == 'Elevator':
            self.placeToonInElevator(toon)

    def setLawyerIds(self, lawyerIds):
        self.lawyers = []
        self.cr.relatedObjectMgr.abortRequest(self.lawyerRequest)
        self.lawyerRequest = self.cr.relatedObjectMgr.requestObjects(lawyerIds, allCallback=self.__gotLawyers)

    def __gotLawyers(self, lawyers):
        self.lawyerRequest = None
        self.lawyers = lawyers
        for i in range(len(self.lawyers)):
            suit = self.lawyers[i]
            suit.fsm.request('neutral')
            suit.loop('neutral')
            suit.setBossCogId(self.doId)

        return

    def setBossDamage(self, bossDamage, recoverRate, timestamp):
        recoverStartTime = globalClockDelta.networkToLocalTime(timestamp)
        self.bossDamage = bossDamage
        self.recoverRate = recoverRate
        self.recoverStartTime = recoverStartTime
        taskName = 'RecoverBossDamage'
        taskMgr.remove(taskName)
        if self.bossDamageMovie:
            if self.bossDamage >= self.bossMaxDamage:
                self.notify.debug('finish the movie then transition to NearVictory')
                self.bossDamageMovie.resumeUntil(self.bossDamageMovie.getDuration())
            else:
                self.bossDamageMovie.resumeUntil(self.bossDamage * self.bossDamageToMovie)
                if self.recoverRate:
                    taskMgr.add(self.__recoverBossDamage, taskName)
        self.makeScaleReflectDamage()

    def getBossDamage(self):
        self.notify.debug('----- getBossDamage')
        now = globalClock.getFrameTime()
        elapsed = now - self.recoverStartTime
        return max(self.bossDamage - self.recoverRate * elapsed / 60.0, 0)

    def __recoverBossDamage(self, task):
        self.notify.debug('----- __recoverBossDamage')
        if self.bossDamageMovie:
            self.bossDamageMovie.setT(self.getBossDamage() * self.bossDamageToMovie)
        return Task.cont

    def __walkToonToPromotion(self, toonId, delay, mopath, track, delayDeletes):
        self.notify.debug('----- __walkToonToPromotion')
        toon = base.cr.doId2do.get(toonId)
        if toon:
            destPos = toon.getPos()
            self.placeToonInElevator(toon)
            toon.wrtReparentTo(render)
            ival = Sequence(Wait(delay), Func(toon.suit.setPlayRate, 1, 'walk'), Func(toon.suit.loop, 'walk'), toon.posInterval(1, Point3(0, 90, 20)), ParallelEndTogether(MopathInterval(mopath, toon), toon.posInterval(2, destPos, blendType='noBlend')), Func(toon.suit.loop, 'neutral'))
            track.append(ival)
            delayDeletes.append(DelayDelete.DelayDelete(toon, 'LawbotBoss.__walkToonToPromotion'))

    def __walkSuitToPoint(self, node, fromPos, toPos):
        self.notify.debug('----- __walkSuitToPoint')
        vector = Vec3(toPos - fromPos)
        distance = vector.length()
        time = distance / (ToontownGlobals.SuitWalkSpeed * 1.8)
        return Sequence(Func(node.setPos, fromPos), Func(node.headsUp, toPos), node.posInterval(time, toPos))

    def __makeRollToBattleTwoMovie(self):
        startPos = Point3(ToontownGlobals.LawbotBossBattleOnePosHpr[0], ToontownGlobals.LawbotBossBattleOnePosHpr[1], ToontownGlobals.LawbotBossBattleOnePosHpr[2])
        if self.arenaSide:
            topRampPos = Point3(*ToontownGlobals.LawbotBossTopRampPosB)
            topRampTurnPos = Point3(*ToontownGlobals.LawbotBossTopRampTurnPosB)
            p3Pos = Point3(*ToontownGlobals.LawbotBossP3PosB)
        else:
            topRampPos = Point3(*ToontownGlobals.LawbotBossTopRampPosA)
            topRampTurnPos = Point3(*ToontownGlobals.LawbotBossTopRampTurnPosA)
            p3Pos = Point3(*ToontownGlobals.LawbotBossP3PosA)
        battlePos = Point3(ToontownGlobals.LawbotBossBattleTwoPosHpr[0], ToontownGlobals.LawbotBossBattleTwoPosHpr[1], ToontownGlobals.LawbotBossBattleTwoPosHpr[2])
        battleHpr = VBase3(ToontownGlobals.LawbotBossBattleTwoPosHpr[3], ToontownGlobals.LawbotBossBattleTwoPosHpr[4], ToontownGlobals.LawbotBossBattleTwoPosHpr[5])
        bossTrack = Sequence()
        self.notify.debug('calling setPosHpr')
        myInterval = camera.posHprInterval(8, Point3(-22, -100, 35), Point3(-10, -13, 0), startPos=Point3(-22, -90, 35), startHpr=Point3(-10, -13, 0), blendType='easeInOut')
        chatTrack = Sequence(Func(self.setChatAbsolute, TTLocalizer.LawbotBossTempJury1, CFSpeech), Func(camera.reparentTo, localAvatar), Func(camera.setPos, localAvatar.cameraPositions[0][0]), Func(camera.setHpr, 0, 0, 0), Func(self.releaseToons, 1))
        bossTrack.append(Func(self.getGeomNode().setH, 180))
        track, hpr = self.rollBossToPoint(startPos, None, battlePos, None, 0)
        bossTrack.append(track)
        track, hpr = self.rollBossToPoint(battlePos, hpr, battlePos, battleHpr, 0)
        self.makeToonsWait()
        finalPodiumPos = Point3(self.podium.getX(), self.podium.getY(), self.podium.getZ() + ToontownGlobals.LawbotBossBattleTwoPosHpr[2])
        finalReflectedPodiumPos = Point3(self.reflectedPodium.getX(), self.reflectedPodium.getY(), self.reflectedPodium.getZ() + ToontownGlobals.LawbotBossBattleTwoPosHpr[2])
        return Sequence(chatTrack, bossTrack, Func(self.getGeomNode().setH, 0), Parallel(self.podium.posInterval(5.0, finalPodiumPos), self.reflectedPodium.posInterval(5.0, finalReflectedPodiumPos), Func(self.stashBoss), self.posInterval(5.0, battlePos), Func(taskMgr.doMethodLater, 0.01, self.unstashBoss, 'unstashBoss')), name=self.uniqueName('BattleTwoMovie'))

    def __makeRollToBattleThreeMovie(self):
        startPos = Point3(ToontownGlobals.LawbotBossBattleTwoPosHpr[0], ToontownGlobals.LawbotBossBattleTwoPosHpr[1], ToontownGlobals.LawbotBossBattleTwoPosHpr[2])
        battlePos = Point3(ToontownGlobals.LawbotBossBattleThreePosHpr[0], ToontownGlobals.LawbotBossBattleThreePosHpr[1], ToontownGlobals.LawbotBossBattleThreePosHpr[2])
        battleHpr = VBase3(ToontownGlobals.LawbotBossBattleThreePosHpr[3], ToontownGlobals.LawbotBossBattleThreePosHpr[4], ToontownGlobals.LawbotBossBattleThreePosHpr[5])
        bossTrack = Sequence()
        myInterval = camera.posHprInterval(8, Point3(-22, -100, 35), Point3(-10, -13, 0), startPos=Point3(-22, -90, 35), startHpr=Point3(-10, -13, 0), blendType='easeInOut')
        chatTrack = Sequence(Func(self.setChatAbsolute, TTLocalizer.LawbotBossTrialChat1, CFSpeech), Func(camera.reparentTo, localAvatar), Func(camera.setPos, localAvatar.cameraPositions[0][0]), Func(camera.setHpr, 0, 0, 0), Func(self.releaseToons, 1))
        bossTrack.append(Func(self.getGeomNode().setH, 180))
        bossTrack.append(Func(self.loop, 'Ff_neutral'))
        track, hpr = self.rollBossToPoint(startPos, None, battlePos, None, 0)
        bossTrack.append(track)
        track, hpr = self.rollBossToPoint(battlePos, hpr, battlePos, battleHpr, 0)
        self.makeToonsWait()
        return Sequence(chatTrack, bossTrack, Func(self.getGeomNode().setH, 0), name=self.uniqueName('BattleTwoMovie'))

    def toNeutralMode(self):
        if self.cr:
            place = self.cr.playGame.getPlace()
            if place and hasattr(place, 'fsm'):
                place.setState('waitForBattle')

    def makeToonsWait(self):
        self.notify.debug('makeToonsWait')
        for toonId in self.involvedToons:
            toon = self.cr.doId2do.get(toonId)
            if toon:
                toon.stopLookAround()
                toon.stopSmooth()

        if self.hasLocalToon():
            self.toMovieMode()
        for toonId in self.involvedToons:
            toon = self.cr.doId2do.get(toonId)
            if toon:
                toon.loop('neutral')

    def makeEndOfBattleMovie(self, hasLocalToon):
        name = self.uniqueName('Drop')
        seq = Sequence(name=name)
        seq += [Wait(0.0)]
        if hasLocalToon:
            seq += [Func(self.show),
             Func(camera.reparentTo, localAvatar),
             Func(camera.setPos, localAvatar.cameraPositions[0][0]),
             Func(camera.setHpr, 0, 0, 0)]
        seq.append(Func(self.setChatAbsolute, TTLocalizer.LawbotBossPassExam, CFSpeech))
        seq.append(Wait(5.0))
        seq.append(Func(self.clearChat))
        return seq

    def __makeBossDamageMovie(self):
        self.notify.debug('---- __makeBossDamageMovie')
        startPos = Point3(ToontownGlobals.LawbotBossBattleThreePosHpr[0], ToontownGlobals.LawbotBossBattleThreePosHpr[1], ToontownGlobals.LawbotBossBattleThreePosHpr[2])
        startHpr = Point3(*ToontownGlobals.LawbotBossBattleThreeHpr)
        bottomPos = Point3(*ToontownGlobals.LawbotBossBottomPos)
        deathPos = Point3(*ToontownGlobals.LawbotBossDeathPos)
        self.setPosHpr(startPos, startHpr)
        bossTrack = Sequence()
        bossTrack.append(Func(self.loop, 'Ff_neutral'))
        track, hpr = self.rollBossToPoint(startPos, startHpr, bottomPos, None, 1)
        bossTrack.append(track)
        track, hpr = self.rollBossToPoint(bottomPos, startHpr, deathPos, None, 1)
        bossTrack.append(track)
        duration = bossTrack.getDuration()
        return bossTrack

    def __showOnscreenMessage(self, text):
        self.notify.debug('----- __showOnscreenmessage')
        if self.onscreenMessage:
            self.onscreenMessage.destroy()
            self.onscreenMessage = None
        self.onscreenMessage = DirectLabel(text=text, text_fg=VBase4(1, 1, 1, 1), text_align=TextNode.ACenter, relief=None, pos=(0, 0, 0.35), scale=0.1)
        return

    def __clearOnscreenMessage(self):
        if self.onscreenMessage:
            self.onscreenMessage.destroy()
            self.onscreenMessage = None
        return

    def __showWaitingMessage(self, task):
        self.notify.debug('----- __showWaitingMessage')
        self.__showOnscreenMessage(TTLocalizer.BuildingWaitingForVictors)

    def loadEnvironment(self):
        self.notify.debug('----- loadEnvironment')
        DistributedBossCog.DistributedBossCog.loadEnvironment(self)
        self.geom = loader.loadModel('phase_11/models/lawbotHQ/LawbotCourtroom3')
        self.geom.setPos(0, 0, -71.601)
        self.geom.setScale(1)
        self.elevatorEntrance = self.geom.find('**/elevator_origin')
        self.elevatorEntrance.getChildren().detach()
        self.elevatorEntrance.setScale(1)
        elevatorModel = loader.loadModel('phase_11/models/lawbotHQ/LB_Elevator')
        elevatorModel.reparentTo(self.elevatorEntrance)
        self.setupElevator(elevatorModel)
        self.promotionMusic = base.loader.loadMusic('phase_7/audio/bgm/encntr_suit_winning_indoor.ogg')
        self.betweenBattleMusic = base.loader.loadMusic('phase_9/audio/bgm/encntr_toon_winning.ogg')
        self.battleTwoMusic = base.loader.loadMusic('phase_11/audio/bgm/LB_juryBG.ogg')
        floor = self.geom.find('**/MidVaultFloor1')
        if floor.isEmpty():
            floor = self.geom.find('**/CR3_Floor')
        self.evFloor = self.replaceCollisionPolysWithPlanes(floor)
        self.evFloor.reparentTo(self.geom)
        self.evFloor.setName('floor')
        plane = CollisionPlane(Plane(Vec3(0, 0, 1), Point3(0, 0, -50)))
        planeNode = CollisionNode('dropPlane')
        planeNode.addSolid(plane)
        planeNode.setCollideMask(ToontownGlobals.PieBitmask)
        self.geom.attachNewNode(planeNode)
        self.door3 = self.geom.find('**/SlidingDoor1/')
        if self.door3.isEmpty():
            self.door3 = self.geom.find('**/interior/CR3_Door')
        self.mainDoor = self.geom.find('**/Door_1')
        if not self.mainDoor.isEmpty():
            itemsToHide = ['interior/Door_1']
            for str in itemsToHide:
                stuffToHide = self.geom.find('**/%s' % str)
                if not stuffToHide.isEmpty():
                    self.notify.debug('found %s' % stuffToHide)
                    stuffToHide.wrtReparentTo(self.mainDoor)
                else:
                    self.notify.debug('not found %s' % stuffToHide)

        self.reflectedMainDoor = self.geom.find('**/interiorrefl/CR3_Door')
        if not self.reflectedMainDoor.isEmpty():
            itemsToHide = ['Reflections/Door_1']
            for str in itemsToHide:
                stuffToHide = self.geom.find('**/%s' % str)
                if not stuffToHide.isEmpty():
                    self.notify.debug('found %s' % stuffToHide)
                    stuffToHide.wrtReparentTo(self.reflectedMainDoor)
                else:
                    self.notify.debug('not found %s' % stuffToHide)

        self.geom.reparentTo(render)
        self.loadWitnessStand()
        self.loadScale()
        self.scaleNodePath.stash()
        self.loadJuryBox()
        self.loadPodium()
        ug = self.geom.find('**/Reflections')
        ug.setBin('ground', -10)

    def loadJuryBox(self):
        self.juryBox = self.geom.find('**/JuryBox')
        juryBoxPos = self.juryBox.getPos()
        newPos = juryBoxPos - Point3(*ToontownGlobals.LawbotBossJuryBoxRelativeEndPos)
        if not self.debugPositions:
            self.juryBox.setPos(newPos)
        self.reflectedJuryBox = self.geom.find('**/JuryBox_Geo_Reflect')
        reflectedJuryBoxPos = self.reflectedJuryBox.getPos()
        newReflectedPos = reflectedJuryBoxPos - Point3(*ToontownGlobals.LawbotBossJuryBoxRelativeEndPos)
        if not self.debugPositions:
            self.reflectedJuryBox.setPos(newReflectedPos)
        if not self.reflectedJuryBox.isEmpty():
            if self.debugPositions:
                self.reflectedJuryBox.show()
        self.reflectedJuryBox.setZ(self.reflectedJuryBox.getZ() + ToontownGlobals.LawbotBossJuryBoxRelativeEndPos[2])

    def loadPodium(self):
        self.podium = self.geom.find('**/Podium')
        newZ = self.podium.getZ() - ToontownGlobals.LawbotBossBattleTwoPosHpr[2]
        if not self.debugPositions:
            self.podium.setZ(newZ)
        self.reflectedPodium = self.geom.find('**/Podium_Geo1_Refl')
        reflectedZ = self.reflectedPodium.getZ()
        if not self.debugPositions:
            self.reflectedPodium.setZ(reflectedZ)
        if not self.reflectedPodium.isEmpty():
            if self.debugPositions:
                self.reflectedPodium.show()

    def loadCannons(self):
        pass

    def loadWitnessStand(self):
        self.realWitnessStand = self.geom.find('**/WitnessStand')
        if not self.realWitnessStand.isEmpty():
            pass
        self.reflectedWitnessStand = self.geom.find('**/Witnessstand_Geo_Reflect')
        if not self.reflectedWitnessStand.isEmpty():
            pass
        colNode = self.realWitnessStand.find('**/witnessStandCollisions/Witnessstand_Collision')
        colNode.setName('WitnessStand')

    def loadScale(self):
        self.useProgrammerScale = base.config.GetBool('want-injustice-scale-debug', 0)
        if self.useProgrammerScale:
            self.loadScaleOld()
        else:
            self.loadScaleNew()

    def __debugScale(self):
        prosecutionPanPos = self.prosecutionPanNodePath.getPos()
        origin = Point3(0, 0, 0)
        prosecutionPanRelPos = self.scaleNodePath.getRelativePoint(self.prosecutionPanNodePath, origin)
        panRenderPos = render.getRelativePoint(self.prosecutionPanNodePath, origin)
        self.notify.debug('prosecutionPanPos = %s' % prosecutionPanPos)
        self.notify.debug('prosecutionPanRelPos = %s' % prosecutionPanRelPos)
        self.notify.debug('panRenderPos = %s' % panRenderPos)
        prosecutionLocatorPos = self.prosecutionLocator.getPos()
        prosecutionLocatorRelPos = self.scaleNodePath.getRelativePoint(self.prosecutionLocator, origin)
        locatorRenderPos = render.getRelativePoint(self.prosecutionLocator, origin)
        self.notify.debug('prosecutionLocatorPos = %s ' % prosecutionLocatorPos)
        self.notify.debug('prosecutionLocatorRelPos = %s ' % prosecutionLocatorRelPos)
        self.notify.debug('locatorRenderPos = %s' % locatorRenderPos)
        beamPos = self.beamNodePath.getPos()
        beamRelPos = self.scaleNodePath.getRelativePoint(self.beamNodePath, origin)
        beamRenderPos = render.getRelativePoint(self.beamNodePath, origin)
        self.notify.debug('beamPos = %s' % beamPos)
        self.notify.debug('beamRelPos = %s' % beamRelPos)
        self.notify.debug('beamRenderPos = %s' % beamRenderPos)
        beamBoundsCenter = self.beamNodePath.getBounds().getCenter()
        self.notify.debug('beamBoundsCenter = %s' % beamBoundsCenter)
        beamLocatorBounds = self.beamLocator.getBounds()
        beamLocatorPos = beamLocatorBounds.getCenter()
        self.notify.debug('beamLocatorPos = %s' % beamLocatorPos)

    def loadScaleNew(self):
        self.scaleNodePath = loader.loadModel('phase_11/models/lawbotHQ/scale')
        self.beamNodePath = self.scaleNodePath.find('**/scaleBeam')
        self.defensePanNodePath = self.scaleNodePath.find('**/defensePan')
        self.prosecutionPanNodePath = self.scaleNodePath.find('**/prosecutionPan')
        self.defenseColNodePath = self.scaleNodePath.find('**/DefenseCol')
        self.defenseColNodePath.setTag('pieCode', str(ToontownGlobals.PieCodeDefensePan))
        self.prosecutionColNodePath = self.scaleNodePath.find('**/ProsecutionCol')
        self.prosecutionColNodePath.setTag('pieCode', str(ToontownGlobals.PieCodeProsecutionPan))
        self.standNodePath = self.scaleNodePath.find('**/scaleStand')
        self.scaleNodePath.setPosHpr(*ToontownGlobals.LawbotBossInjusticePosHpr)
        self.defenseLocator = self.scaleNodePath.find('**/DefenseLocator')
        defenseLocBounds = self.defenseLocator.getBounds()
        defenseLocPos = defenseLocBounds.getCenter()
        self.notify.debug('defenseLocatorPos = %s' % defenseLocPos)
        self.defensePanNodePath.setPos(defenseLocPos)
        self.defensePanNodePath.reparentTo(self.beamNodePath)
        self.notify.debug('defensePanNodePath.getPos()=%s' % self.defensePanNodePath.getPos())
        self.prosecutionLocator = self.scaleNodePath.find('**/ProsecutionLocator')
        prosecutionLocBounds = self.prosecutionLocator.getBounds()
        prosecutionLocPos = prosecutionLocBounds.getCenter()
        self.notify.debug('prosecutionLocatorPos = %s' % prosecutionLocPos)
        self.prosecutionPanNodePath.setPos(prosecutionLocPos)
        self.prosecutionPanNodePath.reparentTo(self.beamNodePath)
        self.beamLocator = self.scaleNodePath.find('**/StandLocator1')
        beamLocatorBounds = self.beamLocator.getBounds()
        beamLocatorPos = beamLocatorBounds.getCenter()
        negBeamLocatorPos = -beamLocatorPos
        self.notify.debug('beamLocatorPos = %s' % beamLocatorPos)
        self.notify.debug('negBeamLocatorPos = %s' % negBeamLocatorPos)
        self.beamNodePath.setPos(beamLocatorPos)
        self.scaleNodePath.setScale(*ToontownGlobals.LawbotBossInjusticeScale)
        self.scaleNodePath.wrtReparentTo(self.geom)
        self.baseHighCol = self.scaleNodePath.find('**/BaseHighCol')
        oldBitMask = self.baseHighCol.getCollideMask()
        newBitMask = oldBitMask & ~ToontownGlobals.PieBitmask
        newBitMask = newBitMask & ~ToontownGlobals.CameraBitmask
        self.baseHighCol.setCollideMask(newBitMask)
        self.defenseHighCol = self.scaleNodePath.find('**/DefenseHighCol')
        self.defenseHighCol.stash()
        self.defenseHighCol.setCollideMask(newBitMask)
        self.baseTopCol = self.scaleNodePath.find('**/Scale_base_top_collision')
        self.baseSideCol = self.scaleNodePath.find('**/Scale_base_side_col')
        self.defenseLocator.hide()
        self.prosecutionLocator.hide()
        self.beamLocator.hide()

    def loadScaleOld(self):
        startingTilt = 0
        self.scaleNodePath = NodePath('injusticeScale')
        beamGeom = self.createBlock(0.25, 2, 0.125, -0.25, -2, -0.125, 0, 1.0, 0, 1.0)
        self.beamNodePath = NodePath('scaleBeam')
        self.beamNodePath.attachNewNode(beamGeom)
        self.beamNodePath.setPos(0, 0, 3)
        self.beamNodePath.reparentTo(self.scaleNodePath)
        defensePanGeom = self.createBlock(0.5, 0.5, 0, -0.5, -0.5, -2, 0, 0, 1.0, 0.25)
        self.defensePanNodePath = NodePath('defensePan')
        self.defensePanNodePath.attachNewNode(defensePanGeom)
        self.defensePanNodePath.setPos(0, -2, 0)
        self.defensePanNodePath.reparentTo(self.beamNodePath)
        defenseTube = CollisionTube(0, 0, -0.5, 0, 0, -1.5, 0.6)
        defenseTube.setTangible(1)
        defenseCollNode = CollisionNode('DefenseCol')
        defenseCollNode.addSolid(defenseTube)
        self.defenseColNodePath = self.defensePanNodePath.attachNewNode(defenseCollNode)
        self.defenseColNodePath.setTag('pieCode', str(ToontownGlobals.PieCodeDefensePan))
        prosecutionPanGeom = self.createBlock(0.5, 0.5, 0, -0.5, -0.5, -2, 1.0, 0, 0, 1.0)
        self.prosecutionPanNodePath = NodePath('prosecutionPan')
        self.prosecutionPanNodePath.attachNewNode(prosecutionPanGeom)
        self.prosecutionPanNodePath.setPos(0, 2, 0)
        self.prosecutionPanNodePath.reparentTo(self.beamNodePath)
        prosecutionTube = CollisionTube(0, 0, -0.5, 0, 0, -1.5, 0.6)
        prosecutionTube.setTangible(1)
        prosecutionCollNode = CollisionNode(self.uniqueName('ProsecutionCol'))
        prosecutionCollNode.addSolid(prosecutionTube)
        self.prosecutionColNodePath = self.prosecutionPanNodePath.attachNewNode(prosecutionCollNode)
        self.prosecutionColNodePath.setTag('pieCode', str(ToontownGlobals.PieCodeProsecutionPan))
        standGeom = self.createBlock(0.25, 0.25, 0, -0.25, -0.25, 3)
        self.standNodePath = NodePath('scaleStand')
        self.standNodePath.attachNewNode(standGeom)
        self.standNodePath.reparentTo(self.scaleNodePath)
        self.scaleNodePath.setPosHpr(*ToontownGlobals.LawbotBossInjusticePosHpr)
        self.scaleNodePath.setScale(5.0)
        self.scaleNodePath.wrtReparentTo(self.geom)
        self.setScaleTilt(startingTilt)

    def setScaleTilt(self, tilt):
        self.beamNodePath.setP(tilt)
        if self.useProgrammerScale:
            self.defensePanNodePath.setP(-tilt)
            self.prosecutionPanNodePath.setP(-tilt)
        else:
            self.defensePanNodePath.setP(-tilt)
            self.prosecutionPanNodePath.setP(-tilt)

    def stashBaseCol(self):
        if not self.baseColStashed:
            self.notify.debug('stashBaseCol')
            self.baseTopCol.stash()
            self.baseSideCol.stash()
            self.baseColStashed = True

    def unstashBaseCol(self):
        if self.baseColStashed:
            self.notify.debug('unstashBaseCol')
            self.baseTopCol.unstash()
            self.baseSideCol.unstash()
            self.baseColStashed = False

    def makeScaleReflectDamage(self):
        diffDamage = self.bossDamage - ToontownGlobals.LawbotBossInitialDamage
        diffDamage *= 1.0
        if diffDamage >= 0:
            percentDamaged = diffDamage / (ToontownGlobals.LawbotBossMaxDamage - ToontownGlobals.LawbotBossInitialDamage)
            tilt = percentDamaged * ToontownGlobals.LawbotBossWinningTilt
        else:
            percentDamaged = diffDamage / (ToontownGlobals.LawbotBossInitialDamage - 0)
            tilt = percentDamaged * ToontownGlobals.LawbotBossWinningTilt
        self.setScaleTilt(tilt)
        if self.bossDamage < ToontownGlobals.LawbotBossMaxDamage * 0.85:
            self.unstashBaseCol()
        else:
            self.stashBaseCol()

    def unloadEnvironment(self):
        self.notify.debug('----- unloadEnvironment')
        DistributedBossCog.DistributedBossCog.unloadEnvironment(self)
        self.geom.removeNode()
        del self.geom

    def __loadMopaths(self):
        self.notify.debug('----- __loadMopaths')
        self.toonsEnterA = Mopath.Mopath()
        self.toonsEnterA.loadFile('phase_9/paths/bossBattle-toonsEnterA')
        self.toonsEnterA.fFaceForward = 1
        self.toonsEnterA.timeScale = 35
        self.toonsEnterB = Mopath.Mopath()
        self.toonsEnterB.loadFile('phase_9/paths/bossBattle-toonsEnterB')
        self.toonsEnterB.fFaceForward = 1
        self.toonsEnterB.timeScale = 35

    def __unloadMopaths(self):
        self.notify.debug('----- __unloadMopaths')
        self.toonsEnterA.reset()
        self.toonsEnterB.reset()

    def enterOff(self):
        self.notify.debug('----- enterOff')
        DistributedBossCog.DistributedBossCog.enterOff(self)
        if self.witnessToon:
            self.witnessToon.clearChat()

    def enterWaitForToons(self):
        self.notify.debug('----- enterWaitForToons')
        DistributedBossCog.DistributedBossCog.enterWaitForToons(self)
        self.geom.hide()
        self.witnessToon.removeActive()

    def exitWaitForToons(self):
        self.notify.debug('----- exitWaitForToons')
        DistributedBossCog.DistributedBossCog.exitWaitForToons(self)
        self.geom.show()
        self.witnessToon.addActive()

    def enterElevator(self):
        self.notify.debug('----- enterElevator')
        DistributedBossCog.DistributedBossCog.enterElevator(self)
        self.witnessToon.removeActive()
        self.reparentTo(render)
        self.setPosHpr(*ToontownGlobals.LawbotBossBattleOnePosHpr)
        self.happy = 1
        self.raised = 1
        self.forward = 1
        self.doAnimate()
        self.__hideWitnessToon()
        if not self.mainDoor.isEmpty():
            self.mainDoor.stash()
        if not self.reflectedMainDoor.isEmpty():
            self.reflectedMainDoor.stash()
        camera.reparentTo(self.elevatorModel)
        camera.setPosHpr(0, 30, 8, 180, 0, 0)

    def exitElevator(self):
        self.notify.debug('----- exitElevator')
        DistributedBossCog.DistributedBossCog.exitElevator(self)
        self.witnessToon.removeActive()

    def enterIntroduction(self):
        self.notify.debug('----- enterIntroduction')
        self.reparentTo(render)
        self.setPosHpr(*ToontownGlobals.LawbotBossBattleOnePosHpr)
        self.stopAnimate()
        self.__hideWitnessToon()
        DistributedBossCog.DistributedBossCog.enterIntroduction(self)
        base.playMusic(self.promotionMusic, looping=1, volume=0.9)
        if not self.mainDoor.isEmpty():
            self.mainDoor.stash()
        if not self.reflectedMainDoor.isEmpty():
            self.reflectedMainDoor.stash()

    def exitIntroduction(self):
        self.notify.debug('----- exitIntroduction')
        DistributedBossCog.DistributedBossCog.exitIntroduction(self)
        self.promotionMusic.stop()
        if not self.mainDoor.isEmpty():
            pass
        if not self.reflectedMainDoor.isEmpty():
            self.reflectedMainDoor.unstash()
        if not self.elevatorEntrance.isEmpty():
            pass

    def enterBattleOne(self):
        self.notify.debug('----- LawbotBoss.enterBattleOne ')
        DistributedBossCog.DistributedBossCog.enterBattleOne(self)
        self.reparentTo(render)
        self.setPosHpr(*ToontownGlobals.LawbotBossBattleOnePosHpr)
        self.clearChat()
        self.loop('Ff_neutral')
        self.notify.debug('self.battleANode = %s' % self.battleANode)
        self.__hideWitnessToon()
        if self.battleA == None or self.battleB == None:
            pass
        return

    def exitBattleOne(self):
        self.notify.debug('----- exitBattleOne')
        DistributedBossCog.DistributedBossCog.exitBattleOne(self)

    def stashBoss(self):
        self.stash()

    def unstashBoss(self, task):
        self.unstash()
        self.reparentTo(render)

    def enterRollToBattleTwo(self):
        self.notify.debug('----- enterRollToBattleTwo')
        self.releaseToons(finalBattle=1)
        self.stashBoss()
        self.toonsToBattlePosition(self.involvedToons, self.battleANode)
        self.stickBossToFloor()
        intervalName = 'RollToBattleTwo'
        seq = Sequence(self.__makeRollToBattleTwoMovie(), Func(self.__onToPrepareBattleTwo), name=intervalName)
        seq.start()
        self.storeInterval(seq, intervalName)
        base.playMusic(self.betweenBattleMusic, looping=1, volume=0.9)
        taskMgr.doMethodLater(0.01, self.unstashBoss, 'unstashBoss')

    def __onToPrepareBattleTwo(self):
        self.notify.debug('----- __onToPrepareBattleTwo')
        self.unstickBoss()
        self.setPosHpr(*ToontownGlobals.LawbotBossBattleTwoPosHpr)
        self.doneBarrier('RollToBattleTwo')

    def exitRollToBattleTwo(self):
        self.notify.debug('----- exitRollToBattleTwo')
        self.unstickBoss()
        intervalName = 'RollToBattleTwo'
        self.clearInterval(intervalName)
        self.betweenBattleMusic.stop()

    def enterPrepareBattleTwo(self):
        self.notify.debug('----- enterPrepareBattleTwo')
        self.cleanupIntervals()
        self.controlToons()
        self.setToonsToNeutral(self.involvedToons)
        self.clearChat()
        self.reparentTo(render)
        self.__showWitnessToon()
        prepareBattleTwoMovie = self.__makePrepareBattleTwoMovie()
        intervalName = 'prepareBattleTwo'
        seq = Sequence(prepareBattleTwoMovie, name=intervalName)
        seq.start()
        self.storeInterval(seq, intervalName)
        self.acceptOnce('doneChatPage', self.__showCannonsAppearing)
        base.playMusic(self.stingMusic, looping=0, volume=1.0)

    def __showCannonsAppearing(self, elapsedTime = 0):
        allCannonsAppear = Sequence(Func(self.__positionToonsInFrontOfCannons), Func(camera.reparentTo, localAvatar), Func(camera.setPos, localAvatar.cameraPositions[2][0]), Func(camera.lookAt, localAvatar))
        multiCannons = Parallel()
        index = 0
        self.involvedToons.sort()
        for toonId in self.involvedToons:
            toon = self.cr.doId2do.get(toonId)
            if toon:
                if index in self.cannons:
                    cannon = self.cannons[index]
                    cannonSeq = cannon.generateCannonAppearTrack(toon)
                    multiCannons.append(cannonSeq)
                    index += 1
                else:
                    self.notify.warning('No cannon %d but we have a toon =%d' % (index, toonId))

        allCannonsAppear.append(multiCannons)
        intervalName = 'prepareBattleTwoCannonsAppear'
        seq = Sequence(allCannonsAppear, Func(self.__onToBattleTwo), name=intervalName)
        seq.start()
        self.storeInterval(seq, intervalName)

    def __onToBattleTwo(self, elapsedTime = 0):
        self.notify.debug('----- __onToBattleTwo')
        self.doneBarrier('PrepareBattleTwo')
        taskMgr.doMethodLater(1, self.__showWaitingMessage, self.uniqueName('WaitingMessage'))

    def exitPrepareBattleTwo(self):
        self.notify.debug('----- exitPrepareBattleTwo')
        self.show()
        taskMgr.remove(self.uniqueName('WaitingMessage'))
        self.ignore('doneChatPage')
        self.__clearOnscreenMessage()
        self.stingMusic.stop()

    def enterBattleTwo(self):
        self.notify.debug('----- enterBattleTwo')
        self.cleanupIntervals()
        mult = ToontownBattleGlobals.getBossBattleCreditMultiplier(2)
        localAvatar.inventory.setBattleCreditMultiplier(mult)
        self.reparentTo(render)
        self.setPosHpr(*ToontownGlobals.LawbotBossBattleTwoPosHpr)
        self.clearChat()
        self.witnessToon.clearChat()
        self.releaseToons(finalBattle=1)
        self.__showWitnessToon()
        if not self.useCannons:
            self.toonsToBattlePosition(self.toonsA, self.battleANode)
            self.toonsToBattlePosition(self.toonsB, self.battleBNode)
        base.playMusic(self.battleTwoMusic, looping=1, volume=0.9)
        self.startJuryBoxMoving()
        for index in range(len(self.cannons)):
            cannon = self.cannons[index]
            cannon.cannon.show()

    def getChairParent(self):
        return self.juryBox

    def startJuryBoxMoving(self):
        curPos = self.juryBox.getPos()
        endingAbsPos = Point3(curPos[0] + ToontownGlobals.LawbotBossJuryBoxRelativeEndPos[0], curPos[1] + ToontownGlobals.LawbotBossJuryBoxRelativeEndPos[1], curPos[2] + ToontownGlobals.LawbotBossJuryBoxRelativeEndPos[2])
        curReflectedPos = self.reflectedJuryBox.getPos()
        reflectedEndingAbsPos = Point3(curReflectedPos[0] + ToontownGlobals.LawbotBossJuryBoxRelativeEndPos[0], curReflectedPos[1] + ToontownGlobals.LawbotBossJuryBoxRelativeEndPos[1], curReflectedPos[2] + ToontownGlobals.LawbotBossJuryBoxRelativeEndPos[2])
        self.juryBoxIval = Parallel(self.juryBox.posInterval(ToontownGlobals.LawbotBossJuryBoxMoveTime, endingAbsPos), self.reflectedJuryBox.posInterval(ToontownGlobals.LawbotBossJuryBoxMoveTime, reflectedEndingAbsPos), SoundInterval(self.juryMovesSfx, node=self.chairs[2].nodePath, duration=ToontownGlobals.LawbotBossJuryBoxMoveTime, loop=1, volume=1.0))
        self.juryBoxIval.start()
        self.juryTimer = ToontownTimer.ToontownTimer()
        self.juryTimer.posInTopRightCorner()
        self.juryTimer.countdown(ToontownGlobals.LawbotBossJuryBoxMoveTime)

    def exitBattleTwo(self):
        self.notify.debug('----- exitBattleTwo')
        intervalName = self.uniqueName('Drop')
        self.clearInterval(intervalName)
        self.cleanupBattles()
        self.battleTwoMusic.stop()
        localAvatar.inventory.setBattleCreditMultiplier(1)
        if self.juryTimer:
            self.juryTimer.destroy()
            del self.juryTimer
            self.juryTimer = None
        for chair in list(self.chairs.values()):
            chair.stopCogsFlying()

        return

    def enterRollToBattleThree(self):
        self.notify.debug('----- enterRollToBattleThree')
        self.reparentTo(render)
        self.stickBossToFloor()
        intervalName = 'RollToBattleThree'
        seq = Sequence(self.__makeRollToBattleThreeMovie(), Func(self.__onToPrepareBattleThree), name=intervalName)
        seq.start()
        self.storeInterval(seq, intervalName)
        base.playMusic(self.betweenBattleMusic, looping=1, volume=0.9)

    def __onToPrepareBattleThree(self):
        self.notify.debug('----- __onToPrepareBattleThree')
        self.unstickBoss()
        self.setPosHpr(*ToontownGlobals.LawbotBossBattleThreePosHpr)
        self.doneBarrier('RollToBattleThree')

    def exitRollToBattleThree(self):
        self.notify.debug('----- exitRollToBattleThree')
        self.unstickBoss()
        intervalName = 'RollToBattleThree'
        self.clearInterval(intervalName)
        self.betweenBattleMusic.stop()

    def enterPrepareBattleThree(self):
        self.notify.debug('----- enterPrepareBattleThree')
        self.cleanupIntervals()
        self.controlToons()
        self.setToonsToNeutral(self.involvedToons)
        self.clearChat()
        self.reparentTo(render)
        base.playMusic(self.betweenBattleMusic, looping=1, volume=0.9)
        self.__showWitnessToon()
        prepareBattleThreeMovie = self.__makePrepareBattleThreeMovie()
        self.acceptOnce('doneChatPage', self.__onToBattleThree)
        intervalName = 'prepareBattleThree'
        seq = Sequence(prepareBattleThreeMovie, name=intervalName)
        seq.start()
        self.storeInterval(seq, intervalName)

    def __onToBattleThree(self, elapsed):
        self.notify.debug('----- __onToBattleThree')
        self.doneBarrier('PrepareBattleThree')
        taskMgr.doMethodLater(1, self.__showWaitingMessage, self.uniqueName('WaitingMessage'))

    def exitPrepareBattleThree(self):
        self.notify.debug('----- exitPrepareBattleThree')
        self.show()
        taskMgr.remove(self.uniqueName('WaitingMessage'))
        self.ignore('doneChatPage')
        intervalName = 'PrepareBattleThree'
        self.clearInterval(intervalName)
        self.__clearOnscreenMessage()
        self.betweenBattleMusic.stop()

    def enterBattleThree(self):
        DistributedBossCog.DistributedBossCog.enterBattleThree(self)
        self.scaleNodePath.unstash()
        localAvatar.setPos(-3, 0, 0)
        camera.reparentTo(localAvatar)
        camera.setPos(localAvatar.cameraPositions[0][0])
        camera.setHpr(0, 0, 0)
        self.clearChat()
        self.witnessToon.clearChat()
        self.reparentTo(render)
        self.happy = 1
        self.raised = 1
        self.forward = 1
        self.doAnimate()
        self.accept('enterWitnessStand', self.__touchedWitnessStand)
        self.accept('pieSplat', self.__pieSplat)
        self.accept('localPieSplat', self.__localPieSplat)
        self.accept('outOfPies', self.__outOfPies)
        self.accept('begin-pie', self.__foundPieButton)
        self.accept('enterDefenseCol', self.__enterDefenseCol)
        self.accept('enterProsecutionCol', self.__enterProsecutionCol)
        localAvatar.setCameraFov(ToontownGlobals.BossBattleCameraFov)
        taskMgr.doMethodLater(30, self.__howToGetPies, self.uniqueName('PieAdvice'))
        self.stickBossToFloor()
        self.setPosHpr(*ToontownGlobals.LawbotBossBattleThreePosHpr)
        self.bossMaxDamage = ToontownGlobals.LawbotBossMaxDamage
        base.playMusic(self.battleThreeMusic, looping=1, volume=0.9)
        self.__showWitnessToon()
        diffSettings = ToontownGlobals.LawbotBossDifficultySettings[self.battleDifficulty]
        if diffSettings[4]:
            localAvatar.chatMgr.chatInputSpeedChat.removeCJMenu()
            localAvatar.chatMgr.chatInputSpeedChat.addCJMenu(self.bonusWeight)

    def __doneBattleThree(self):
        self.notify.debug('----- __doneBattleThree')
        self.setState('NearVictory')
        self.unstickBoss()

    def exitBattleThree(self):
        self.notify.debug('----- exitBattleThree')
        DistributedBossCog.DistributedBossCog.exitBattleThree(self)
        NametagGlobals.setMasterArrowsOn(1)
        bossDoneEventName = self.uniqueName('DestroyedBoss')
        self.ignore(bossDoneEventName)
        taskMgr.remove(self.uniqueName('StandUp'))
        self.ignore('enterWitnessStand')
        self.ignore('pieSplat')
        self.ignore('localPieSplat')
        self.ignore('outOfPies')
        self.ignore('begin-pie')
        self.ignore('enterDefenseCol')
        self.ignore('enterProsecutionCol')
        self.__clearOnscreenMessage()
        taskMgr.remove(self.uniqueName('PieAdvice'))
        localAvatar.setCameraFov(ToontownGlobals.CogHQCameraFov)
        if self.bossDamageMovie:
            self.bossDamageMovie.finish()
        self.bossDamageMovie = None
        self.unstickBoss()
        taskName = 'RecoverBossDamage'
        taskMgr.remove(taskName)
        self.battleThreeMusicTime = self.battleThreeMusic.getTime()
        self.battleThreeMusic.stop()
        return

    def enterNearVictory(self):
        self.cleanupIntervals()
        self.reparentTo(render)
        self.setPos(*ToontownGlobals.LawbotBossDeathPos)
        self.setHpr(*ToontownGlobals.LawbotBossBattleThreeHpr)
        self.clearChat()
        self.releaseToons(finalBattle=1)
        self.accept('pieSplat', self.__finalPieSplat)
        self.accept('localPieSplat', self.__localPieSplat)
        self.accept('outOfPies', self.__outOfPies)
        localAvatar.setCameraFov(ToontownGlobals.BossBattleCameraFov)
        self.happy = 0
        self.raised = 0
        self.forward = 1
        self.doAnimate()
        self.setDizzy(1)
        base.playMusic(self.battleThreeMusic, looping=1, volume=0.9, time=self.battleThreeMusicTime)

    def exitNearVictory(self):
        self.notify.debug('----- exitNearVictory')
        self.ignore('pieSplat')
        self.ignore('localPieSplat')
        self.ignore('outOfPies')
        self.__clearOnscreenMessage()
        taskMgr.remove(self.uniqueName('PieAdvice'))
        localAvatar.setCameraFov(ToontownGlobals.CogHQCameraFov)
        self.setDizzy(0)
        self.battleThreeMusicTime = self.battleThreeMusic.getTime()
        self.battleThreeMusic.stop()

    def enterVictory(self):
        self.notify.debug('----- enterVictory')
        self.cleanupIntervals()
        self.reparentTo(render)
        self.setPosHpr(*ToontownGlobals.LawbotBossBattleThreePosHpr)
        self.loop('neutral')
        localAvatar.setCameraFov(ToontownGlobals.BossBattleCameraFov)
        self.clearChat()
        self.witnessToon.clearChat()
        self.controlToons()
        self.setToonsToNeutral(self.involvedToons)
        self.happy = 1
        self.raised = 1
        self.forward = 1
        intervalName = 'VictoryMovie'
        seq = Sequence(self.makeVictoryMovie(), Func(self.__continueVictory), name=intervalName)
        seq.start()
        self.storeInterval(seq, intervalName)
        base.playMusic(self.battleThreeMusic, looping=1, volume=0.9, time=self.battleThreeMusicTime)

    def __continueVictory(self):
        self.notify.debug('----- __continueVictory')
        self.stopAnimate()
        self.doneBarrier('Victory')

    def exitVictory(self):
        self.notify.debug('----- exitVictory')
        self.stopAnimate()
        self.unstash()
        localAvatar.setCameraFov(ToontownGlobals.CogHQCameraFov)
        self.battleThreeMusicTime = self.battleThreeMusic.getTime()
        self.battleThreeMusic.stop()

    def enterDefeat(self):
        self.notify.debug('----- enterDefeat')
        self.cleanupIntervals()
        localAvatar.setCameraFov(ToontownGlobals.BossBattleCameraFov)
        self.reparentTo(render)
        self.clearChat()
        self.releaseToons(finalBattle=1)
        self.happy = 0
        self.raised = 0
        self.forward = 1
        intervalName = 'DefeatMovie'
        seq = Sequence(self.makeDefeatMovie(), Func(self.__continueDefeat), name=intervalName)
        seq.start()
        self.storeInterval(seq, intervalName)
        base.playMusic(self.battleThreeMusic, looping=1, volume=0.9, time=self.battleThreeMusicTime)

    def __continueDefeat(self):
        self.notify.debug('----- __continueDefeat')
        self.stopAnimate()
        self.doneBarrier('Defeat')

    def exitDefeat(self):
        self.notify.debug('----- exitDefeat')
        self.stopAnimate()
        self.unstash()
        localAvatar.setCameraFov(ToontownGlobals.CogHQCameraFov)
        self.battleThreeMusicTime = self.battleThreeMusic.getTime()
        self.battleThreeMusic.stop()

    def enterReward(self):
        self.cleanupIntervals()
        self.clearChat()
        self.witnessToon.clearChat()
        self.stash()
        self.stopAnimate()
        self.controlToons()
        panelName = self.uniqueName('reward')
        self.rewardPanel = RewardPanel.RewardPanel(panelName)
        victory, camVictory, skipper = MovieToonVictory.doToonVictory(1, self.involvedToons, self.toonRewardIds, self.toonRewardDicts, self.deathList, self.rewardPanel, allowGroupShot=0, uberList=self.uberList, noSkip=True)
        ival = Sequence(Parallel(victory, camVictory), Func(self.__doneReward))
        intervalName = 'RewardMovie'
        delayDeletes = []
        for toonId in self.involvedToons:
            toon = self.cr.doId2do.get(toonId)
            if toon:
                delayDeletes.append(DelayDelete.DelayDelete(toon, 'LawbotBoss.enterReward'))

        ival.delayDeletes = delayDeletes
        ival.start()
        self.storeInterval(ival, intervalName)
        base.playMusic(self.battleThreeMusic, looping=1, volume=0.9, time=self.battleThreeMusicTime)

    def __doneReward(self):
        self.notify.debug('----- __doneReward')
        self.doneBarrier('Reward')
        self.toWalkMode()

    def exitReward(self):
        self.notify.debug('----- exitReward')
        intervalName = 'RewardMovie'
        self.clearInterval(intervalName)
        self.unstash()
        self.rewardPanel.destroy()
        del self.rewardPanel
        self.battleThreeMusicTime = 0
        self.battleThreeMusic.stop()

    def enterEpilogue(self):
        self.cleanupIntervals()
        self.clearChat()
        self.witnessToon.clearChat()
        self.stash()
        self.stopAnimate()
        self.controlToons()
        self.__showWitnessToon()
        self.witnessToon.reparentTo(render)
        self.witnessToon.setPosHpr(*ToontownGlobals.LawbotBossWitnessEpiloguePosHpr)
        self.witnessToon.loop('Sit')
        self.__arrangeToonsAroundWitnessToon()
        camera.reparentTo(render)
        camera.setPos(self.witnessToon, -9, 12, 6)
        camera.lookAt(self.witnessToon, 0, 0, 3)
        intervalName = 'EpilogueMovie'
        seq = Sequence(self.makeEpilogueMovie(), name=intervalName)
        seq.start()
        self.storeInterval(seq, intervalName)
        self.accept('doneChatPage', self.__doneEpilogue)
        base.playMusic(self.epilogueMusic, looping=1, volume=0.9)

    def __doneEpilogue(self, elapsedTime = 0):
        self.notify.debug('----- __doneEpilogue')
        intervalName = 'EpilogueMovieToonAnim'
        self.clearInterval(intervalName)
        track = Parallel(Sequence(Wait(0.5), Func(self.localToonToSafeZone)))
        self.storeInterval(track, intervalName)
        track.start()

    def exitEpilogue(self):
        self.notify.debug('----- exitEpilogue')
        self.clearInterval('EpilogueMovieToonAnim')
        self.unstash()
        self.epilogueMusic.stop()

    def enterFrolic(self):
        self.notify.debug('----- enterFrolic')
        self.setPosHpr(*ToontownGlobals.LawbotBossBattleOnePosHpr)
        DistributedBossCog.DistributedBossCog.enterFrolic(self)
        self.show()

    def doorACallback(self, isOpen):
        if self.insidesANodePath:
            if isOpen:
                self.insidesANodePath.unstash()
            else:
                self.insidesANodePath.stash()

    def doorBCallback(self, isOpen):
        if self.insidesBNodePath:
            if isOpen:
                self.insidesBNodePath.unstash()
            else:
                self.insidesBNodePath.stash()

    def __toonsToPromotionPosition(self, toonIds, battleNode):
        self.notify.debug('----- __toonsToPromotionPosition')
        points = BattleBase.BattleBase.toonPoints[len(toonIds) - 1]
        for i in range(len(toonIds)):
            toon = base.cr.doId2do.get(toonIds[i])
            if toon:
                toon.reparentTo(render)
                pos, h = points[i]
                toon.setPosHpr(battleNode, pos[0], pos[1] + 10, pos[2], h, 0, 0)

    def __outOfPies(self):
        self.notify.debug('----- outOfPies')
        self.__showOnscreenMessage(TTLocalizer.LawbotBossNeedMoreEvidence)
        taskMgr.doMethodLater(20, self.__howToGetPies, self.uniqueName('PieAdvice'))

    def __howToGetPies(self, task):
        self.notify.debug('----- __howToGetPies')
        self.__showOnscreenMessage(TTLocalizer.LawbotBossHowToGetEvidence)

    def __howToThrowPies(self, task):
        self.notify.debug('----- __howToThrowPies')
        self.__showOnscreenMessage(TTLocalizer.LawbotBossHowToThrowPies)

    def __foundPieButton(self):
        self.everThrownPie = 1
        self.__clearOnscreenMessage()
        taskMgr.remove(self.uniqueName('PieAdvice'))

    def __touchedWitnessStand(self, entry):
        self.sendUpdate('touchWitnessStand', [])
        self.__clearOnscreenMessage()
        taskMgr.remove(self.uniqueName('PieAdvice'))
        base.playSfx(self.piesRestockSfx)
        if not self.everThrownPie:
            taskMgr.doMethodLater(30, self.__howToThrowPies, self.uniqueName('PieAdvice'))

    def __pieSplat(self, toon, pieCode):
        if pieCode == ToontownGlobals.PieCodeBossInsides:
            if toon == localAvatar:
                self.d_hitBossInsides()
            self.flashRed()
        elif pieCode == ToontownGlobals.PieCodeBossCog:
            if toon == localAvatar:
                self.d_hitBoss(1)
            if self.dizzy:
                self.flashRed()
                self.doAnimate('hit', now=1)
        elif pieCode == ToontownGlobals.PieCodeDefensePan:
            self.flashRed()
            self.flashPanBlue()
            base.playSfx(self.evidenceHitSfx, node=self.defensePanNodePath, volume=0.25)
            if toon == localAvatar:
                self.d_hitBoss(self.panDamage)
        elif pieCode == ToontownGlobals.PieCodeProsecutionPan:
            self.flashGreen()
            if toon == localAvatar:
                pass
        elif pieCode == ToontownGlobals.PieCodeLawyer:
            pass

    def __localPieSplat(self, pieCode, entry):
        if pieCode == ToontownGlobals.PieCodeLawyer:
            self.__lawyerGotHit(entry)
        if pieCode != ToontownGlobals.PieCodeToon:
            return
        avatarDoId = entry.getIntoNodePath().getNetTag('avatarDoId')
        if avatarDoId == '':
            self.notify.warning('Toon %s has no avatarDoId tag.' % repr(entry.getIntoNodePath()))
            return
        doId = int(avatarDoId)
        if doId != localAvatar.doId:
            self.d_hitToon(doId)

    def __lawyerGotHit(self, entry):
        lawyerCol = entry.getIntoNodePath()
        names = lawyerCol.getName().split('-')
        lawyerDoId = int(names[1])
        for lawyer in self.lawyers:
            if lawyerDoId == lawyer.doId:
                lawyer.sendUpdate('hitByToon', [])

    def __finalPieSplat(self, toon, pieCode):
        if pieCode != ToontownGlobals.PieCodeDefensePan:
            return
        self.sendUpdate('finalPieSplat', [])
        self.ignore('pieSplat')

    def cleanupAttacks(self):
        self.notify.debug('----- cleanupAttacks')
        self.__cleanupStrafe()

    def __cleanupStrafe(self):
        self.notify.debug('----- __cleanupStrage')
        if self.strafeInterval:
            self.strafeInterval.finish()
            self.strafeInterval = None
        return

    def __cleanupJuryBox(self):
        self.notify.debug('----- __cleanupJuryBox')
        if self.juryBoxIval:
            self.juryBoxIval.finish()
            self.juryBoxIval = None
        if self.juryBox:
            self.juryBox.removeNode()
        return

    def doStrafe(self, side, direction):
        gearRoot = self.rotateNode.attachNewNode('gearRoot')
        if side == 0:
            gearRoot.setPos(0, -7, 3)
            gearRoot.setHpr(180, 0, 0)
            door = self.doorA
        else:
            gearRoot.setPos(0, 7, 3)
            door = self.doorB
        gearRoot.setTag('attackCode', str(ToontownGlobals.BossCogStrafeAttack))
        gearModel = self.getGearFrisbee()
        gearModel.setScale(0.1)
        t = self.getBossDamage() / 100.0
        gearTrack = Parallel()
        numGears = int(4 + 6 * t + 0.5)
        time = 5.0 - 4.0 * t
        spread = 60 * math.pi / 180.0
        if direction == 1:
            spread = -spread
        dist = 50
        rate = time / numGears
        for i in range(numGears):
            node = gearRoot.attachNewNode(str(i))
            node.hide()
            node.setPos(0, 0, 0)
            gear = gearModel.instanceTo(node)
            angle = (float(i) / (numGears - 1) - 0.5) * spread
            x = dist * math.sin(angle)
            y = dist * math.cos(angle)
            h = random.uniform(-720, 720)
            gearTrack.append(Sequence(Wait(i * rate), Func(node.show), Parallel(node.posInterval(1, Point3(x, y, 0), fluid=1), node.hprInterval(1, VBase3(h, 0, 0), fluid=1), Sequence(SoundInterval(self.strafeSfx[i], volume=0.2, node=self), duration=0)), Func(node.detachNode)))

        seq = Sequence(Func(door.request, 'open'), Wait(0.7), gearTrack, Func(door.request, 'close'))
        self.__cleanupStrafe()
        self.strafeInterval = seq
        seq.start()

    def replaceCollisionPolysWithPlanes(self, model):
        newCollisionNode = CollisionNode('collisions')
        newCollideMask = BitMask32(0)
        planes = []
        collList = model.findAllMatches('**/+CollisionNode')
        if not collList:
            collList = [model]
        for cnp in collList:
            cn = cnp.node()
            if not isinstance(cn, CollisionNode):
                self.notify.warning('Not a collision node: %s' % repr(cnp))
                break
            newCollideMask = newCollideMask | cn.getIntoCollideMask()
            for i in range(cn.getNumSolids()):
                solid = cn.getSolid(i)
                if isinstance(solid, CollisionPolygon):
                    plane = Plane(solid.getPlane())
                    planes.append(plane)
                else:
                    self.notify.warning('Unexpected collision solid: %s' % repr(solid))
                    newCollisionNode.addSolid(plane)

        newCollisionNode.setIntoCollideMask(newCollideMask)
        threshold = 0.1
        planes.sort(key=functools.cmp_to_key(lambda p1, p2: p1.compareTo(p2, threshold)))
        lastPlane = None
        for plane in planes:
            if lastPlane == None or plane.compareTo(lastPlane, threshold) != 0:
                cp = CollisionPlane(plane)
                newCollisionNode.addSolid(cp)
                lastPlane = plane

        return NodePath(newCollisionNode)

    def makeIntroductionMovie(self, delayDeletes):
        self.notify.debug('----- makeIntroductionMovie')
        for toonId in self.involvedToons:
            toon = self.cr.doId2do.get(toonId)
            if toon:
                delayDeletes.append(DelayDelete.DelayDelete(toon, 'LawbotBoss.makeIntroductionMovie'))

        track = Parallel()
        bossAnimTrack = Sequence(
            ActorInterval(self, 'Ff_speech', startTime=2, duration=10, loop=1),
            ActorInterval(self, 'Ff_lookRt', duration=3),
            ActorInterval(self, 'Ff_lookRt', duration=3, startTime=3, endTime=0),
            ActorInterval(self, 'Ff_neutral', duration=2),
            ActorInterval(self, 'Ff_speech', duration=7, loop=1))
        track.append(bossAnimTrack)
        attackToons = TTLocalizer.BossCogAttackToons
        dialogTrack = Track(
            (0, Func(self.setChatAbsolute, TTLocalizer.LawbotBossTempIntro0, CFSpeech)),
            (5.6, Func(self.setChatAbsolute, TTLocalizer.LawbotBossTempIntro1, CFSpeech)),
            (12, Func(self.setChatAbsolute, TTLocalizer.LawbotBossTempIntro2, CFSpeech)),
            (18, Func(self.setChatAbsolute, TTLocalizer.LawbotBossTempIntro3, CFSpeech)),
            (22, Func(self.setChatAbsolute, TTLocalizer.LawbotBossTempIntro4, CFSpeech)),
            (24, Sequence(
                Func(self.clearChat),
                self.loseCogSuits(self.toonsA + self.toonsB, render, (-2.798, -70, 10, 180, 0, 0)))),
            (27, Sequence(
                self.toonNormalEyes(self.involvedToons),
                Func(self.loop, 'Ff_neutral'),
                Func(self.setChatAbsolute, attackToons, CFSpeech))))
        track.append(dialogTrack)
        return Sequence(
            Func(self.stickToonsToFloor),
            track,
            Func(self.unstickToons), name=self.uniqueName('Introduction'))

    def walkToonsToBattlePosition(self, toonIds, battleNode):
        self.notify.debug('walkToonsToBattlePosition-----------------------------------------------')
        self.notify.debug('toonIds=%s  battleNode=%s' % (toonIds, battleNode))
        ival = Parallel()
        points = BattleBase.BattleBase.toonPoints[len(toonIds) - 1]
        self.notify.debug('walkToonsToBattlePosition: points = %s' % points[0][0])
        for i in range(len(toonIds)):
            toon = base.cr.doId2do.get(toonIds[i])
            if toon:
                pos, h = points[i]
                origPos = pos
                self.notify.debug('origPos = %s' % origPos)
                self.notify.debug('batlleNode.getTransform = %s  render.getTransform=%s' % (battleNode.getTransform(), render.getTransform()))
                self.notify.debug('render.getScale()=%s  battleNode.getScale()=%s' % (render.getScale(), battleNode.getScale()))
                myCurPos = self.getPos()
                self.notify.debug('myCurPos = %s' % self.getPos())
                self.notify.debug('battleNode.parent() = %s' % battleNode.getParent())
                self.notify.debug('battleNode.parent().getPos() = %s' % battleNode.getParent().getPos())
                bnParent = battleNode.getParent()
                battleNode.wrtReparentTo(render)
                bnWorldPos = battleNode.getPos()
                battleNode.wrtReparentTo(bnParent)
                self.notify.debug('battle node world pos = %s' % bnWorldPos)
                pos = render.getRelativePoint(battleNode, pos)
                self.notify.debug('walktToonsToBattlePosition: render.getRelativePoint result = %s' % pos)
                self.notify.debug('walkToonsToBattlePosition: final pos = %s' % pos)
                ival.append(Sequence(Func(toon.setPlayRate, 0.8, 'walk'), Func(toon.loop, 'walk'), toon.posInterval(3, pos), Func(toon.setPlayRate, 1, 'walk'), Func(toon.loop, 'neutral')))

        return ival

    def toonsToBattlePosition(self, toonIds, battleNode):
        self.notify.debug('DistrutedLawbotBoss.toonsToBattlePosition----------------------------------------')
        self.notify.debug('toonIds=%s battleNode=%s' % (toonIds, battleNode))
        if len(toonIds) < 5:
            points = BattleBase.BattleBase.toonPoints[len(toonIds) - 1]
        else:
            points = list(BattleBase.BattleBase.toonPoints[3])
            points.extend(BattleBase.BattleBase.toonPoints[len(toonIds) - 5])
        self.notify.debug('toonsToBattlePosition: points = %s' % points[0][0])
        for i in range(len(toonIds)):
            toon = base.cr.doId2do.get(toonIds[i])
            if toon:
                toon.wrtReparentTo(render)
                pos, h = points[i]
                if i > 3:
                    pos.setY(pos.getY() + 2.0)
                bnParent = battleNode.getParent()
                battleNode.wrtReparentTo(render)
                bnWorldPos = battleNode.getPos()
                battleNode.wrtReparentTo(bnParent)
                toon.setPosHpr(battleNode, pos[0], pos[1], pos[2], h, 0, 0)
                self.notify.debug('new toon pos %s ' % toon.getPos())

    def touchedGavel(self, gavel, entry):
        self.notify.debug('touchedGavel')
        attackCodeStr = entry.getIntoNodePath().getNetTag('attackCode')
        if attackCodeStr == '':
            self.notify.warning('Node %s has no attackCode tag.' % repr(entry.getIntoNodePath()))
            return
        attackCode = int(attackCodeStr)
        into = entry.getIntoNodePath()
        self.zapLocalToon(attackCode, into)

    def touchedGavelHandle(self, gavel, entry):
        attackCodeStr = entry.getIntoNodePath().getNetTag('attackCode')
        if attackCodeStr == '':
            self.notify.warning('Node %s has no attackCode tag.' % repr(entry.getIntoNodePath()))
            return
        attackCode = int(attackCodeStr)
        into = entry.getIntoNodePath()
        self.zapLocalToon(attackCode, into)

    def createBlock(self, x1, y1, z1, x2, y2, z2, r = 1.0, g = 1.0, b = 1.0, a = 1.0):
        gFormat = GeomVertexFormat.getV3n3cpt2()
        myVertexData = GeomVertexData('holds my vertices', gFormat, Geom.UHDynamic)
        vertexWriter = GeomVertexWriter(myVertexData, 'vertex')
        normalWriter = GeomVertexWriter(myVertexData, 'normal')
        colorWriter = GeomVertexWriter(myVertexData, 'color')
        texWriter = GeomVertexWriter(myVertexData, 'texcoord')
        vertexWriter.addData3f(x1, y1, z1)
        vertexWriter.addData3f(x2, y1, z1)
        vertexWriter.addData3f(x1, y2, z1)
        vertexWriter.addData3f(x2, y2, z1)
        vertexWriter.addData3f(x1, y1, z2)
        vertexWriter.addData3f(x2, y1, z2)
        vertexWriter.addData3f(x1, y2, z2)
        vertexWriter.addData3f(x2, y2, z2)
        for index in range(8):
            normalWriter.addData3f(1.0, 1.0, 1.0)
            colorWriter.addData4f(r, g, b, a)
            texWriter.addData2f(1.0, 1.0)

        tris = GeomTriangles(Geom.UHDynamic)
        tris.addVertex(0)
        tris.addVertex(1)
        tris.addVertex(2)
        tris.closePrimitive()
        tris.addVertex(1)
        tris.addVertex(3)
        tris.addVertex(2)
        tris.closePrimitive()
        tris.addVertex(2)
        tris.addVertex(3)
        tris.addVertex(6)
        tris.closePrimitive()
        tris.addVertex(3)
        tris.addVertex(7)
        tris.addVertex(6)
        tris.closePrimitive()
        tris.addVertex(0)
        tris.addVertex(2)
        tris.addVertex(4)
        tris.closePrimitive()
        tris.addVertex(2)
        tris.addVertex(6)
        tris.addVertex(4)
        tris.closePrimitive()
        tris.addVertex(1)
        tris.addVertex(5)
        tris.addVertex(3)
        tris.closePrimitive()
        tris.addVertex(3)
        tris.addVertex(5)
        tris.addVertex(7)
        tris.closePrimitive()
        tris.addVertex(0)
        tris.addVertex(4)
        tris.addVertex(5)
        tris.closePrimitive()
        tris.addVertex(1)
        tris.addVertex(0)
        tris.addVertex(5)
        tris.closePrimitive()
        tris.addVertex(4)
        tris.addVertex(6)
        tris.addVertex(7)
        tris.closePrimitive()
        tris.addVertex(7)
        tris.addVertex(5)
        tris.addVertex(4)
        tris.closePrimitive()
        cubeGeom = Geom(myVertexData)
        cubeGeom.addPrimitive(tris)
        cubeGN = GeomNode('cube')
        cubeGN.addGeom(cubeGeom)
        return cubeGN

    def __enterDefenseCol(self, entry):
        self.notify.debug('__enterDefenseCol')

    def __enterProsecutionCol(self, entry):
        self.notify.debug('__enterProsecutionCol')

    def makeVictoryMovie(self):
        myFromPos = Point3(ToontownGlobals.LawbotBossBattleThreePosHpr[0], ToontownGlobals.LawbotBossBattleThreePosHpr[1], ToontownGlobals.LawbotBossBattleThreePosHpr[2])
        myToPos = Point3(myFromPos[0], myFromPos[1] + 30, myFromPos[2])
        rollThroughDoor = self.rollBossToPoint(fromPos=myFromPos, fromHpr=None, toPos=myToPos, toHpr=None, reverse=0)
        rollTrack = Sequence(
            Func(self.getGeomNode().setH, 180),
            rollThroughDoor[0],
            Func(self.getGeomNode().setH, 0))
        rollTrackDuration = rollTrack.getDuration()
        self.notify.debug('rollTrackDuration = %f' % rollTrackDuration)
        doorStartPos = self.door3.getPos()
        doorEndPos = Point3(doorStartPos[0], doorStartPos[1], doorStartPos[2] + 25)
        bossTrack = Track(
            (0.5, Sequence(
                Func(self.clearChat),
                Func(camera.reparentTo, render),
                Func(camera.setPos, -3, 45, 25),
                Func(camera.setHpr, 0, 10, 0))),
            (1.0, Func(self.setChatAbsolute, TTLocalizer.LawbotBossDefenseWins1, CFSpeech)),
            (5.5, Func(self.setChatAbsolute, TTLocalizer.LawbotBossDefenseWins2, CFSpeech)),
            (9.5, Sequence(Func(camera.wrtReparentTo, render))),
            (9.6, Parallel(
                rollTrack,
                Func(self.setChatAbsolute, TTLocalizer.LawbotBossDefenseWins3, CFSpeech),
                self.door3.posInterval(2, doorEndPos, startPos=doorStartPos))),
            (13.1, Sequence(self.door3.posInterval(1, doorStartPos))))
        retTrack = Parallel(bossTrack, ActorInterval(self, 'Ff_speech', loop=1))
        return bossTrack

    def makeEpilogueMovie(self):
        epSpeech = TTLocalizer.WitnessToonCongratulations
        epSpeech = self.__talkAboutPromotion(epSpeech)
        bossTrack = Sequence(Func(self.witnessToon.animFSM.request, 'neutral'), Func(self.witnessToon.setLocalPageChat, epSpeech, 0))
        return bossTrack

    def makeDefeatMovie(self):
        bossTrack = Track((0.0, Sequence(Func(self.clearChat), Func(self.reverseHead), ActorInterval(self, 'Ff_speech'))), (1.0, Func(self.setChatAbsolute, TTLocalizer.LawbotBossProsecutionWins, CFSpeech)))
        return bossTrack

    def __makeWitnessToon(self):
        dnaNetString = b't\x1b\x00\x01\x01\x00\x03\x00\x03\x01\x10\x13\x00\x13\x13'
        npc = Toon.Toon()
        npc.setDNAString(dnaNetString)
        npc.setName(TTLocalizer.WitnessToonName)
        npc.setPickable(0)
        npc.setPlayerType(NametagGroup.CCNonPlayer)
        npc.animFSM.request('Sit')
        self.witnessToon = npc
        self.witnessToon.setPosHpr(*ToontownGlobals.LawbotBossWitnessStandPosHpr)

    def __cleanupWitnessToon(self):
        self.__hideWitnessToon()
        if self.witnessToon:
            self.witnessToon.removeActive()
            self.witnessToon.delete()
            self.witnessToon = None
        return

    def __showWitnessToon(self):
        if not self.witnessToonOnstage:
            self.witnessToon.addActive()
            self.witnessToon.reparentTo(self.geom)
            seatCenter = self.realWitnessStand.find('**/witnessStandSeatEdge')
            center = seatCenter.getPos()
            self.notify.debug('center = %s' % center)
            self.witnessToon.setPos(center)
            self.witnessToon.setH(180)
            self.witnessToon.setZ(self.witnessToon.getZ() - 1.5)
            self.witnessToon.setY(self.witnessToon.getY() - 1.15)
            self.witnessToonOnstage = 1

    def __hideWitnessToon(self):
        if self.witnessToonOnstage:
            self.witnessToon.removeActive()
            self.witnessToon.detachNode()
            self.witnessToonOnstage = 0

    def __hideToons(self):
        for toonId in self.involvedToons:
            toon = self.cr.doId2do.get(toonId)
            if toon:
                toon.hide()

    def __showToons(self):
        for toonId in self.involvedToons:
            toon = self.cr.doId2do.get(toonId)
            if toon:
                toon.show()

    def __arrangeToonsAroundWitnessToon(self):
        radius = 7
        numToons = len(self.involvedToons)
        center = (numToons - 1) / 2.0
        for i in range(numToons):
            toon = self.cr.doId2do.get(self.involvedToons[i])
            if toon:
                angle = 90 - 15 * (i - center)
                radians = angle * math.pi / 180.0
                x = math.cos(radians) * radius
                y = math.sin(radians) * radius
                toon.setPos(self.witnessToon, x, y, 0)
                toon.headsUp(self.witnessToon)
                toon.loop('neutral')
                toon.show()

    def __talkAboutPromotion(self, speech):
        if self.prevCogSuitLevel < ToontownGlobals.MaxCogSuitLevel:
            newCogSuitLevel = localAvatar.getCogLevels()[CogDisguiseGlobals.dept2deptIndex(self.style.dept)]
            if newCogSuitLevel == ToontownGlobals.MaxCogSuitLevel:
                speech += TTLocalizer.WitnessToonLastPromotion % (ToontownGlobals.MaxCogSuitLevel + 1)
            if newCogSuitLevel in ToontownGlobals.CogSuitHPLevels:
                speech += TTLocalizer.WitnessToonHPBoost
        else:
            speech += TTLocalizer.WitnessToonMaxed % (ToontownGlobals.MaxCogSuitLevel + 1)
        return speech

    def __positionToonsInFrontOfCannons(self):
        self.notify.debug('__positionToonsInFrontOfCannons')
        index = 0
        self.involvedToons.sort()
        for toonId in self.involvedToons:
            if index in self.cannons:
                cannon = self.cannons[index]
                toon = self.cr.doId2do.get(toonId)
                self.notify.debug('cannonId = %d' % cannon.doId)
                cannonPos = cannon.nodePath.getPos(render)
                self.notify.debug('cannonPos = %s' % cannonPos)
                if toon:
                    self.notify.debug('toon = %s' % toon.getName())
                    toon.reparentTo(cannon.nodePath)
                    toon.setPos(0, 8, 0)
                    toon.setH(180)
                    renderPos = toon.getPos(render)
                    self.notify.debug('renderPos =%s' % renderPos)
                    index += 1

        self.notify.debug('done with positionToons')

    def __makePrepareBattleTwoMovie(self):
        chatString = TTLocalizer.WitnessToonPrepareBattleTwo % ToontownGlobals.LawbotBossJurorsForBalancedScale
        movie = Sequence(Func(camera.reparentTo, self.witnessToon), Func(camera.setPos, 0, 8, 2), Func(camera.setHpr, 180, 10, 0), Func(self.witnessToon.setLocalPageChat, chatString, 0))
        return movie

    def __doWitnessPrepareBattleThreeChat(self):
        self.notify.debug('__doWitnessPrepareBattleThreeChat: original self.numToonJurorsSeated = %d' % self.numToonJurorsSeated)
        self.countToonJurors()
        self.notify.debug('after calling self.countToonJurors, numToonJurorsSeated=%d' % self.numToonJurorsSeated)
        if self.numToonJurorsSeated == 0:
            juryResult = TTLocalizer.WitnessToonNoJuror
        elif self.numToonJurorsSeated == 1:
            juryResult = TTLocalizer.WitnessToonOneJuror
        elif self.numToonJurorsSeated == 12:
            juryResult = TTLocalizer.WitnessToonAllJurors
        else:
            juryResult = TTLocalizer.WitnessToonSomeJurors % self.numToonJurorsSeated
        juryResult += '\x07'
        trialSpeech = juryResult
        trialSpeech += TTLocalizer.WitnessToonPrepareBattleThree
        diffSettings = ToontownGlobals.LawbotBossDifficultySettings[self.battleDifficulty]
        if diffSettings[4]:
            newWeight, self.bonusWeight, self.numJurorsLocalToonSeated = self.calculateWeightOfToon(base.localAvatar.doId)
            if self.bonusWeight > 0:
                if self.bonusWeight == 1:
                    juryWeightBonus = TTLocalizer.WitnessToonJuryWeightBonusSingular.get(self.battleDifficulty)
                else:
                    juryWeightBonus = TTLocalizer.WitnessToonJuryWeightBonusPlural.get(self.battleDifficulty)
                if juryWeightBonus:
                    weightBonusText = juryWeightBonus % (self.numJurorsLocalToonSeated, self.bonusWeight)
                    trialSpeech += '\x07'
                    trialSpeech += weightBonusText
        self.witnessToon.setLocalPageChat(trialSpeech, 0)

    def __makePrepareBattleThreeMovie(self):
        movie = Sequence(Func(camera.reparentTo, render), Func(camera.setPos, -15, 15, 20), Func(camera.setHpr, -90, 0, 0), Wait(3), Func(camera.reparentTo, self.witnessToon), Func(camera.setPos, 0, 8, 2), Func(camera.setHpr, 180, 10, 0), Func(self.__doWitnessPrepareBattleThreeChat))
        return movie

    def countToonJurors(self):
        self.numToonJurorsSeated = 0
        for key in list(self.chairs.keys()):
            chair = self.chairs[key]
            if chair.state == 'ToonJuror' or chair.state == None and chair.newState == 'ToonJuror':
                self.numToonJurorsSeated += 1

        self.notify.debug('self.numToonJurorsSeated = %d' % self.numToonJurorsSeated)
        return

    def cleanupPanFlash(self):
        if self.panFlashInterval:
            self.panFlashInterval.finish()
            self.panFlashInterval = None
        return

    def flashPanBlue(self):
        self.cleanupPanFlash()
        intervalName = 'FlashPanBlue'
        self.defensePanNodePath.setColorScale(1, 1, 1, 1)
        seq = Sequence(self.defensePanNodePath.colorScaleInterval(0.1, colorScale=VBase4(0, 0, 1, 1)), self.defensePanNodePath.colorScaleInterval(0.3, colorScale=VBase4(1, 1, 1, 1)), name=intervalName)
        self.panFlashInterval = seq
        seq.start()
        self.storeInterval(seq, intervalName)

    def saySomething(self, chatString):
        intervalName = 'ChiefJusticeTaunt'
        seq = Sequence(name=intervalName)
        seq.append(Func(self.setChatAbsolute, chatString, CFSpeech))
        seq.append(Wait(4.0))
        seq.append(Func(self.clearChat))
        oldSeq = self.activeIntervals.get(intervalName)
        if oldSeq:
            oldSeq.finish()
        seq.start()
        self.storeInterval(seq, intervalName)

    def setTaunt(self, tauntIndex, extraInfo):
        gotError = False
        if not hasattr(self, 'state'):
            self.notify.warning('returning from setTaunt, no attr state')
            gotError = True
        elif not self.state == 'BattleThree':
            self.notify.warning('returning from setTaunt, not in battle three state, state=%s', self.state)
            gotError = True
        if not hasattr(self, 'nametag'):
            self.notify.warning('returning from setTaunt, no attr nametag')
            gotError = True
        if gotError:
            st = StackTrace()
            print(st)
            return
        chatString = TTLocalizer.LawbotBossTaunts[1]
        if tauntIndex == 0:
            if extraInfo < len(self.involvedToons):
                toonId = self.involvedToons[extraInfo]
                toon = base.cr.doId2do.get(toonId)
                if toon:
                    chatString = TTLocalizer.LawbotBossTaunts[tauntIndex] % toon.getName()
        else:
            chatString = TTLocalizer.LawbotBossTaunts[tauntIndex]
        self.saySomething(chatString)

    def toonGotHealed(self, toonId):
        toon = base.cr.doId2do.get(toonId)
        if toon:
            base.playSfx(self.toonUpSfx, node=toon)

    def hideBonusTimer(self):
        if self.bonusTimer:
            self.bonusTimer.hide()

    def enteredBonusState(self):
        self.witnessToon.clearChat()
        text = TTLocalizer.WitnessToonBonus % (ToontownGlobals.LawbotBossBonusWeightMultiplier, ToontownGlobals.LawbotBossBonusDuration)
        self.witnessToon.setChatAbsolute(text, CFSpeech | CFTimeout)
        base.playSfx(self.toonUpSfx)
        if not self.bonusTimer:
            self.bonusTimer = ToontownTimer.ToontownTimer()
            self.bonusTimer.posInTopRightCorner()
        self.bonusTimer.show()
        self.bonusTimer.countdown(ToontownGlobals.LawbotBossBonusDuration, self.hideBonusTimer)

    def setAttackCode(self, attackCode, avId = 0):
        DistributedBossCog.DistributedBossCog.setAttackCode(self, attackCode, avId)
        if attackCode == ToontownGlobals.BossCogAreaAttack:
            self.saySomething(TTLocalizer.LawbotBossAreaAttackTaunt)
            base.playSfx(self.warningSfx)

    def setBattleDifficulty(self, diff):
        self.notify.debug('battleDifficulty = %d' % diff)
        self.battleDifficulty = diff

    def toonEnteredCannon(self, toonId, cannonIndex):
        if base.localAvatar.doId == toonId:
            self.cannonIndex = cannonIndex

    def numJurorsSeatedByCannon(self, cannonIndex):
        retVal = 0
        for chair in list(self.chairs.values()):
            if chair.state == 'ToonJuror':
                if chair.toonJurorIndex == cannonIndex:
                    retVal += 1

        return retVal

    def calculateWeightOfToon(self, toonId):
        defaultWeight = 1
        bonusWeight = 0
        newWeight = 1
        cannonIndex = self.cannonIndex
        numJurors = 0
        if not cannonIndex == None and cannonIndex >= 0:
            diffSettings = ToontownGlobals.LawbotBossDifficultySettings[self.battleDifficulty]
            if diffSettings[4]:
                numJurors = self.numJurorsSeatedByCannon(cannonIndex)
                bonusWeight = numJurors - diffSettings[5]
                if bonusWeight < 0:
                    bonusWeight = 0
            newWeight = defaultWeight + bonusWeight
            self.notify.debug('toon %d has weight of %d' % (toonId, newWeight))
        return (newWeight, bonusWeight, numJurors)
