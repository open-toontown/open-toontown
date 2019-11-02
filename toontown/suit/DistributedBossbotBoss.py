import math
import random
from pandac.PandaModules import NametagGroup, CFSpeech, VBase3, CollisionPlane, CollisionNode, CollisionSphere, CollisionTube, NodePath, Plane, Vec3, Vec2, Point3, BitMask32, CollisionHandlerEvent, TextureStage, VBase4, BoundingSphere
from direct.interval.IntervalGlobal import Sequence, Wait, Func, LerpHprInterval, Parallel, LerpPosInterval, Track, ActorInterval, ParallelEndTogether, LerpFunctionInterval, LerpScaleInterval, LerpPosHprInterval, SoundInterval
from direct.task import Task
from direct.fsm import FSM
from direct.directnotify import DirectNotifyGlobal
from direct.distributed.ClockDelta import globalClockDelta
from direct.showbase import PythonUtil
from direct.task import Task
from toontown.distributed import DelayDelete
from toontown.toonbase import ToontownGlobals
from toontown.suit import DistributedBossCog
from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownGlobals
from toontown.suit import SuitDNA
from toontown.toon import Toon
from toontown.toon import ToonDNA
from toontown.building import ElevatorConstants
from toontown.toonbase import ToontownTimer
from toontown.toonbase import ToontownBattleGlobals
from toontown.battle import RewardPanel
from toontown.battle import MovieToonVictory
from toontown.coghq import CogDisguiseGlobals
from toontown.suit import Suit
from toontown.suit import SuitDNA
from toontown.effects import DustCloud
OneBossCog = None
TTL = TTLocalizer

class DistributedBossbotBoss(DistributedBossCog.DistributedBossCog, FSM.FSM):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedBossbotBoss')
    BallLaunchOffset = Point3(10.5, 8.5, -5)

    def __init__(self, cr):
        self.notify.debug('----- __init___')
        DistributedBossCog.DistributedBossCog.__init__(self, cr)
        FSM.FSM.__init__(self, 'DistributedBossbotBoss')
        self.bossDamage = 0
        self.bossMaxDamage = ToontownGlobals.BossbotBossMaxDamage
        self.elevatorType = ElevatorConstants.ELEVATOR_BB
        self.resistanceToon = None
        self.resistanceToonOnstage = 0
        self.battleANode.setPosHpr(*ToontownGlobals.WaiterBattleAPosHpr)
        self.battleBNode.setPosHpr(*ToontownGlobals.WaiterBattleBPosHpr)
        self.toonFoodStatus = {}
        self.belts = [None, None]
        self.tables = {}
        self.golfSpots = {}
        self.servingTimer = None
        self.notDeadList = None
        self.moveTrack = None
        self.speedDamage = 0
        self.maxSpeedDamage = ToontownGlobals.BossbotMaxSpeedDamage
        self.speedRecoverRate = 0
        self.speedRecoverStartTime = 0
        self.ballLaunch = None
        self.moveTrack = None
        self.lastZapLocalTime = 0
        self.numAttacks = 0
        return

    def announceGenerate(self):
        global OneBossCog
        DistributedBossCog.DistributedBossCog.announceGenerate(self)
        self.loadEnvironment()
        self.__makeResistanceToon()
        localAvatar.chatMgr.chatInputSpeedChat.addCEOMenu()
        if OneBossCog != None:
            self.notify.warning('Multiple BossCogs visible.')
        OneBossCog = self
        render.setTag('pieCode', str(ToontownGlobals.PieCodeNotBossCog))
        self.setTag('attackCode', str(ToontownGlobals.BossCogGolfAttack))
        target = CollisionTube(0, -2, -2, 0, -1, 9, 4.0)
        targetNode = CollisionNode('BossZap')
        targetNode.addSolid(target)
        targetNode.setCollideMask(ToontownGlobals.PieBitmask)
        self.targetNodePath = self.pelvis.attachNewNode(targetNode)
        self.targetNodePath.setTag('pieCode', str(ToontownGlobals.PieCodeBossCog))
        self.axle.getParent().setTag('pieCode', str(ToontownGlobals.PieCodeBossCog))
        disk = loader.loadModel('phase_9/models/char/bossCog-gearCollide')
        disk.find('**/+CollisionNode').setName('BossZap')
        disk.reparentTo(self.pelvis)
        disk.setZ(0.8)
        closeBubble = CollisionSphere(0, 0, 0, 10)
        closeBubble.setTangible(0)
        closeBubbleNode = CollisionNode('CloseBoss')
        closeBubbleNode.setIntoCollideMask(BitMask32(0))
        closeBubbleNode.setFromCollideMask(ToontownGlobals.BanquetTableBitmask)
        closeBubbleNode.addSolid(closeBubble)
        self.closeBubbleNode = closeBubbleNode
        self.closeHandler = CollisionHandlerEvent()
        self.closeHandler.addInPattern('closeEnter')
        self.closeHandler.addOutPattern('closeExit')
        self.closeBubbleNodePath = self.attachNewNode(closeBubbleNode)
        (base.cTrav.addCollider(self.closeBubbleNodePath, self.closeHandler),)
        self.accept('closeEnter', self.closeEnter)
        self.accept('closeExit', self.closeExit)
        self.treads = self.find('**/treads')
        demotedCeo = Suit.Suit()
        demotedCeo.dna = SuitDNA.SuitDNA()
        demotedCeo.dna.newSuit('f')
        demotedCeo.setDNA(demotedCeo.dna)
        demotedCeo.reparentTo(self.geom)
        demotedCeo.loop('neutral')
        demotedCeo.stash()
        self.demotedCeo = demotedCeo
        self.bossClub = loader.loadModel('phase_12/models/char/bossbotBoss-golfclub')
        overtimeOneClubSequence = Sequence(self.bossClub.colorScaleInterval(0.1, colorScale=VBase4(0, 1, 0, 1)), self.bossClub.colorScaleInterval(0.3, colorScale=VBase4(1, 1, 1, 1)))
        overtimeTwoClubSequence = Sequence(self.bossClub.colorScaleInterval(0.1, colorScale=VBase4(1, 0, 0, 1)), self.bossClub.colorScaleInterval(0.3, colorScale=VBase4(1, 1, 1, 1)))
        self.bossClubIntervals = [overtimeOneClubSequence, overtimeTwoClubSequence]
        self.rightHandJoint = self.find('**/joint17')
        self.setPosHpr(*ToontownGlobals.BossbotBossBattleOnePosHpr)
        self.reparentTo(render)
        self.toonUpSfx = loader.loadSfx('phase_11/audio/sfx/LB_toonup.mp3')
        self.warningSfx = loader.loadSfx('phase_5/audio/sfx/Skel_COG_VO_grunt.mp3')
        self.swingClubSfx = loader.loadSfx('phase_5/audio/sfx/SA_hardball.mp3')
        self.moveBossTaskName = 'CEOMoveTask'
        return

    def disable(self):
        global OneBossCog
        self.notify.debug('----- disable')
        DistributedBossCog.DistributedBossCog.disable(self)
        self.demotedCeo.delete()
        base.cTrav.removeCollider(self.closeBubbleNodePath)
        taskMgr.remove('RecoverSpeedDamage')
        self.request('Off')
        self.unloadEnvironment()
        self.__cleanupResistanceToon()
        if self.servingTimer:
            self.servingTimer.destroy()
            del self.servingTimer
        localAvatar.chatMgr.chatInputSpeedChat.removeCEOMenu()
        if OneBossCog == self:
            OneBossCog = None
        self.promotionMusic.stop()
        self.betweenPhaseMusic.stop()
        self.phaseTwoMusic.stop()
        self.phaseFourMusic.stop()
        self.interruptMove()
        for ival in self.bossClubIntervals:
            ival.finish()

        self.belts = []
        self.tables = {}
        self.removeAllTasks()
        return

    def loadEnvironment(self):
        self.notify.debug('----- loadEnvironment')
        DistributedBossCog.DistributedBossCog.loadEnvironment(self)
        self.geom = loader.loadModel('phase_12/models/bossbotHQ/BanquetInterior_1')
        self.elevatorEntrance = self.geom.find('**/elevator_origin')
        elevatorModel = loader.loadModel('phase_12/models/bossbotHQ/BB_Inside_Elevator')
        if not elevatorModel:
            elevatorModel = loader.loadModel('phase_12/models/bossbotHQ/BB_Elevator')
        elevatorModel.reparentTo(self.elevatorEntrance)
        self.setupElevator(elevatorModel)
        self.banquetDoor = self.geom.find('**/door3')
        plane = CollisionPlane(Plane(Vec3(0, 0, 1), Point3(0, 0, -50)))
        planeNode = CollisionNode('dropPlane')
        planeNode.addSolid(plane)
        planeNode.setCollideMask(ToontownGlobals.PieBitmask)
        self.geom.attachNewNode(planeNode)
        self.geom.reparentTo(render)
        self.promotionMusic = base.loadMusic('phase_7/audio/bgm/encntr_suit_winning_indoor.mid')
        self.betweenPhaseMusic = base.loadMusic('phase_9/audio/bgm/encntr_toon_winning.mid')
        self.phaseTwoMusic = base.loadMusic('phase_12/audio/bgm/BossBot_CEO_v1.mid')
        self.phaseFourMusic = base.loadMusic('phase_12/audio/bgm/BossBot_CEO_v2.mid')
        self.pickupFoodSfx = loader.loadSfx('phase_6/audio/sfx/SZ_MM_gliss.mp3')
        self.explodeSfx = loader.loadSfx('phase_4/audio/sfx/firework_distance_02.mp3')

    def unloadEnvironment(self):
        self.notify.debug('----- unloadEnvironment')
        for belt in self.belts:
            if belt:
                belt.cleanup()

        for spot in self.golfSpots.values():
            if spot:
                spot.cleanup()

        self.golfSpots = {}
        self.geom.removeNode()
        del self.geom
        DistributedBossCog.DistributedBossCog.unloadEnvironment(self)

    def __makeResistanceToon(self):
        if self.resistanceToon:
            return
        npc = Toon.Toon()
        npc.setName(TTLocalizer.BossbotResistanceToonName)
        npc.setPickable(0)
        npc.setPlayerType(NametagGroup.CCNonPlayer)
        dna = ToonDNA.ToonDNA()
        dna.newToonRandom(11237, 'm', 1)
        dna.head = 'sls'
        npc.setDNAString(dna.makeNetString())
        npc.animFSM.request('neutral')
        npc.loop('neutral')
        self.resistanceToon = npc
        self.resistanceToon.setPosHpr(*ToontownGlobals.BossbotRTIntroStartPosHpr)
        state = random.getstate()
        random.seed(self.doId)
        self.resistanceToon.suitType = SuitDNA.getRandomSuitByDept('c')
        random.setstate(state)

    def __cleanupResistanceToon(self):
        self.__hideResistanceToon()
        if self.resistanceToon:
            self.resistanceToon.takeOffSuit()
            self.resistanceToon.removeActive()
            self.resistanceToon.delete()
            self.resistanceToon = None
        return

    def __showResistanceToon(self, withSuit):
        if not self.resistanceToonOnstage:
            self.resistanceToon.addActive()
            self.resistanceToon.reparentTo(self.geom)
            self.resistanceToonOnstage = 1
        if withSuit:
            suit = self.resistanceToon.suitType
            self.resistanceToon.putOnSuit(suit, False)
        else:
            self.resistanceToon.takeOffSuit()

    def __hideResistanceToon(self):
        if self.resistanceToonOnstage:
            self.resistanceToon.removeActive()
            self.resistanceToon.detachNode()
            self.resistanceToonOnstage = 0

    def enterElevator(self):
        DistributedBossCog.DistributedBossCog.enterElevator(self)
        self.resistanceToon.removeActive()
        self.__showResistanceToon(True)
        self.resistanceToon.suit.loop('neutral')
        base.camera.setPos(0, 21, 7)
        self.reparentTo(render)
        self.setPosHpr(*ToontownGlobals.BossbotBossBattleOnePosHpr)
        self.loop('Ff_neutral')
        self.show()

    def enterIntroduction(self):
        if not self.resistanceToonOnstage:
            self.__showResistanceToon(True)
        DistributedBossCog.DistributedBossCog.enterIntroduction(self)
        base.playMusic(self.promotionMusic, looping=1, volume=0.9)

    def exitIntroduction(self):
        DistributedBossCog.DistributedBossCog.exitIntroduction(self)
        self.promotionMusic.stop()

    def makeIntroductionMovie(self, delayDeletes):
        rToon = self.resistanceToon
        rToonStartPos = Point3(ToontownGlobals.BossbotRTIntroStartPosHpr[0], ToontownGlobals.BossbotRTIntroStartPosHpr[1], ToontownGlobals.BossbotRTIntroStartPosHpr[2])
        rToonEndPos = rToonStartPos + Point3(40, 0, 0)
        elevCamPosHpr = ToontownGlobals.BossbotElevCamPosHpr
        closeUpRTCamPos = Point3(elevCamPosHpr[0], elevCamPosHpr[1], elevCamPosHpr[2])
        closeUpRTCamHpr = Point3(elevCamPosHpr[3], elevCamPosHpr[4], elevCamPosHpr[5])
        closeUpRTCamPos.setY(closeUpRTCamPos.getY() + 20)
        closeUpRTCamPos.setZ(closeUpRTCamPos.getZ() + -2)
        closeUpRTCamHpr = Point3(0, 5, 0)
        loseSuitCamPos = Point3(rToonStartPos)
        loseSuitCamPos += Point3(0, -5, 4)
        loseSuitCamHpr = Point3(180, 0, 0)
        waiterCamPos = Point3(rToonStartPos)
        waiterCamPos += Point3(-5, -10, 5)
        waiterCamHpr = Point3(-30, 0, 0)
        track = Sequence(Func(camera.reparentTo, render), Func(camera.setPosHpr, *elevCamPosHpr), Func(rToon.setChatAbsolute, TTL.BossbotRTWelcome, CFSpeech), LerpPosHprInterval(camera, 3, closeUpRTCamPos, closeUpRTCamHpr), Func(rToon.setChatAbsolute, TTL.BossbotRTRemoveSuit, CFSpeech), Wait(3), Func(self.clearChat), self.loseCogSuits(self.toonsA + self.toonsB, render, (loseSuitCamPos[0],
         loseSuitCamPos[1],
         loseSuitCamPos[2],
         loseSuitCamHpr[0],
         loseSuitCamHpr[1],
         loseSuitCamHpr[2])), self.toonNormalEyes(self.involvedToons), Wait(2), Func(camera.setPosHpr, closeUpRTCamPos, closeUpRTCamHpr), Func(rToon.setChatAbsolute, TTL.BossbotRTFightWaiter, CFSpeech), Wait(1), LerpHprInterval(camera, 2, Point3(-15, 5, 0)), Sequence(Func(rToon.suit.loop, 'walk'), rToon.hprInterval(1, VBase3(270, 0, 0)), rToon.posInterval(2.5, rToonEndPos), Func(rToon.suit.loop, 'neutral')), Wait(3), Func(rToon.clearChat), Func(self.__hideResistanceToon))
        return track

    def enterFrolic(self):
        self.notify.debug('----- enterFrolic')
        self.setPosHpr(*ToontownGlobals.BossbotBossBattleOnePosHpr)
        DistributedBossCog.DistributedBossCog.enterFrolic(self)
        self.show()

    def enterPrepareBattleTwo(self):
        self.controlToons()
        self.setToonsToNeutral(self.involvedToons)
        for toonId in self.involvedToons:
            toon = self.cr.doId2do.get(toonId)
            if toon:
                toon.takeOffSuit()

        self.__showResistanceToon(True)
        self.resistanceToon.setPosHpr(*ToontownGlobals.BossbotRTPreTwoPosHpr)
        self.__arrangeToonsAroundResistanceToon()
        intervalName = 'PrepareBattleTwoMovie'
        delayDeletes = []
        seq = Sequence(self.makePrepareBattleTwoMovie(delayDeletes), Func(self.__onToBattleTwo), name=intervalName)
        seq.delayDeletes = delayDeletes
        seq.start()
        self.storeInterval(seq, intervalName)
        base.playMusic(self.betweenPhaseMusic, looping=1, volume=0.9)

    def makePrepareBattleTwoMovie(self, delayDeletes):
        for toonId in self.involvedToons:
            toon = self.cr.doId2do.get(toonId)
            if toon:
                delayDeletes.append(DelayDelete.DelayDelete(toon, 'BossbotBoss.makePrepareBattleTwoMovie'))

        rToon = self.resistanceToon
        rToonStartPos = Point3(ToontownGlobals.BossbotRTPreTwoPosHpr[0], ToontownGlobals.BossbotRTPreTwoPosHpr[1], ToontownGlobals.BossbotRTPreTwoPosHpr[2])
        rToonEndPos = rToonStartPos + Point3(-40, 0, 0)
        bossPos = Point3(ToontownGlobals.BossbotBossPreTwoPosHpr[0], ToontownGlobals.BossbotBossPreTwoPosHpr[1], ToontownGlobals.BossbotBossPreTwoPosHpr[2])
        bossEndPos = Point3(ToontownGlobals.BossbotBossBattleOnePosHpr[0], ToontownGlobals.BossbotBossBattleOnePosHpr[1], ToontownGlobals.BossbotBossBattleOnePosHpr[2])
        tempNode = self.attachNewNode('temp')
        tempNode.setPos(0, -40, 18)

        def getCamBossPos(tempNode = tempNode):
            return tempNode.getPos(render)

        rNode = rToon.attachNewNode('temp2')
        rNode.setPos(-5, 25, 12)

        def getCamRTPos(rNode = rNode):
            return rNode.getPos(render)

        track = Sequence(
            Func(camera.reparentTo, render),
            Func(camera.setPos, rToon, 0, 22, 6),
            Func(camera.setHpr, 0, 0, 0),
            Func(rToon.setChatAbsolute, TTL.BossbotRTWearWaiter, CFSpeech),
            Wait(3.0),
            self.wearCogSuits(self.toonsA + self.toonsB, render, None, waiter=True),
            Func(rToon.clearChat),
            Func(self.setPosHpr, bossPos, Point3(0, 0, 0)),
            Parallel(LerpHprInterval(self.banquetDoor, 2, Point3(90, 0, 0)),
                     LerpPosInterval(camera, 2, getCamBossPos)),
            Func(self.setChatAbsolute, TTL.BossbotBossPreTwo1, CFSpeech),
            Wait(3.0),
            Func(self.setChatAbsolute, TTL.BossbotBossPreTwo2, CFSpeech),
            Wait(3.0),
            Parallel(
                LerpHprInterval(self.banquetDoor, 2, Point3(0, 0, 0)),
                LerpPosHprInterval(camera, 2, getCamRTPos, Point3(10, -8, 0))),
            Func(self.setPos, bossEndPos),
            Func(self.clearChat),
            Func(rToon.setChatAbsolute, TTL.BossbotRTServeFood1, CFSpeech),
            Wait(3.0),
            Func(rToon.setChatAbsolute, TTL.BossbotRTServeFood2, CFSpeech),
            Wait(1.0),
            LerpHprInterval(self.banquetDoor, 2, Point3(120, 0, 0)),
            Sequence(
                Func(rToon.suit.loop, 'walk'),
                rToon.hprInterval(1, VBase3(90, 0, 0)),
                rToon.posInterval(2.5, rToonEndPos),
                Func(rToon.suit.loop, 'neutral')),
            self.createWalkInInterval(),
            Func(self.banquetDoor.setH, 0),
            Func(rToon.clearChat),
            Func(self.__hideResistanceToon))
        return track

    def createWalkInInterval(self):
        retval = Parallel()
        delay = 0
        index = 0
        for toonId in self.involvedToons:
            toon = base.cr.doId2do.get(toonId)
            if not toon:
                continue
            destPos = Point3(-14 + index * 4, 25, 0)

            def toWalk(toon):
                if hasattr(toon, 'suit') and toon.suit:
                    toon.suit.loop('walk')

            def toNeutral(toon):
                if hasattr(toon, 'suit') and toon.suit:
                    toon.suit.loop('neutral')

            retval.append(Sequence(Wait(delay), Func(toon.wrtReparentTo, render), Func(toWalk, toon), Func(toon.headsUp, 0, 0, 0), LerpPosInterval(toon, 3, Point3(0, 0, 0)), Func(toon.headsUp, destPos), LerpPosInterval(toon, 3, destPos), LerpHprInterval(toon, 1, Point3(0, 0, 0)), Func(toNeutral, toon)))
            if toon == base.localAvatar:
                retval.append(Sequence(Wait(delay), Func(camera.reparentTo, toon), Func(camera.setPos, toon.cameraPositions[0][0]), Func(camera.setHpr, 0, 0, 0)))
            delay += 1.0
            index += 1

        return retval

    def __onToBattleTwo(self, elapsedTime = 0):
        self.doneBarrier('PrepareBattleTwo')

    def exitPrepareBattleTwo(self):
        self.clearInterval('PrepareBattleTwoMovie')
        self.betweenPhaseMusic.stop()

    def __arrangeToonsAroundResistanceToon(self):
        radius = 9
        numToons = len(self.involvedToons)
        center = (numToons - 1) / 2.0
        for i in range(numToons):
            toon = self.cr.doId2do.get(self.involvedToons[i])
            if toon:
                angle = 90 - 25 * (i - center)
                radians = angle * math.pi / 180.0
                x = math.cos(radians) * radius
                y = math.sin(radians) * radius
                toon.reparentTo(render)
                toon.setPos(self.resistanceToon, x, y, 0)
                toon.headsUp(self.resistanceToon)
                toon.loop('neutral')
                toon.show()

    def enterBattleTwo(self):
        self.releaseToons(finalBattle=1)
        for toonId in self.involvedToons:
            toon = self.cr.doId2do.get(toonId)
            if toon:
                self.putToonInCogSuit(toon)

        self.servingTimer = ToontownTimer.ToontownTimer()
        self.servingTimer.posInTopRightCorner()
        self.servingTimer.countdown(ToontownGlobals.BossbotBossServingDuration)
        base.playMusic(self.phaseTwoMusic, looping=1, volume=0.9)

    def exitBattleTwo(self):
        if self.servingTimer:
            self.servingTimer.destroy()
            del self.servingTimer
            self.servingTimer = None
        for toonId in self.involvedToons:
            self.removeFoodFromToon(toonId)

        self.phaseTwoMusic.stop()
        return

    def setBelt(self, belt, beltIndex):
        if beltIndex < len(self.belts):
            self.belts[beltIndex] = belt

    def localToonTouchedBeltFood(self, beltIndex, foodIndex, foodNum):
        avId = base.localAvatar.doId
        doRequest = False
        if avId not in self.toonFoodStatus:
            doRequest = True
        elif not self.toonFoodStatus[avId]:
            doRequest = True
        if doRequest:
            self.sendUpdate('requestGetFood', [beltIndex, foodIndex, foodNum])

    def toonGotFood(self, avId, beltIndex, foodIndex, foodNum):
        if self.belts[beltIndex]:
            self.belts[beltIndex].removeFood(foodIndex)
            self.putFoodOnToon(avId, beltIndex, foodNum)

    def putFoodOnToon(self, avId, beltIndex, foodNum):
        self.toonFoodStatus[avId] = (beltIndex, foodNum)
        av = base.cr.doId2do.get(avId)
        if av:
            intervalName = self.uniqueName('loadFoodSoundIval-%d' % avId)
            seq = SoundInterval(self.pickupFoodSfx, node=av, name=intervalName)
            oldSeq = self.activeIntervals.get(intervalName)
            if oldSeq:
                oldSeq.finish()
            seq.start()
            self.activeIntervals[intervalName] = seq
            foodModel = loader.loadModel('phase_12/models/bossbotHQ/canoffood')
            foodModel.setName('cogFood')
            foodModel.setScale(ToontownGlobals.BossbotFoodModelScale)
            foodModel.reparentTo(av.suit.getRightHand())
            foodModel.setHpr(52.1961, 180.4983, -4.2882)
            curAnim = av.suit.getCurrentAnim()
            self.notify.debug('curAnim=%s' % curAnim)
            if curAnim in ('walk', 'run'):
                av.suit.loop('tray-walk')
            elif curAnim == 'neutral':
                self.notify.debug('looping tray-netural')
                av.suit.loop('tray-neutral')
            else:
                self.notify.warning("don't know what to do with anim=%s" % curAnim)

    def removeFoodFromToon(self, avId):
        self.toonFoodStatus[avId] = None
        av = base.cr.doId2do.get(avId)
        if av:
            cogFood = av.find('**/cogFood')
            if not cogFood.isEmpty():
                cogFood.removeNode()
        return

    def detachFoodFromToon(self, avId):
        cogFood = None
        self.toonFoodStatus[avId] = None
        av = base.cr.doId2do.get(avId)
        if av:
            cogFood = av.find('**/cogFood')
            if not cogFood.isEmpty():
                retval = cogFood
                cogFood.wrtReparentTo(render)
            curAnim = av.suit.getCurrentAnim()
            self.notify.debug('curAnim=%s' % curAnim)
            if curAnim == 'tray-walk':
                av.suit.loop('run')
            elif curAnim == 'tray-neutral':
                av.suit.loop('neutral')
            else:
                self.notify.warning("don't know what to do with anim=%s" % curAnim)
        return cogFood

    def setTable(self, table, tableIndex):
        self.tables[tableIndex] = table

    def localToonTouchedChair(self, tableIndex, chairIndex):
        avId = base.localAvatar.doId
        if avId in self.toonFoodStatus and self.toonFoodStatus[avId] != None:
            self.sendUpdate('requestServeFood', [tableIndex, chairIndex])
        return

    def toonServeFood(self, avId, tableIndex, chairIndex):
        food = self.detachFoodFromToon(avId)
        table = self.tables[tableIndex]
        table.serveFood(food, chairIndex)

    def enterPrepareBattleThree(self):
        self.calcNotDeadList()
        self.battleANode.setPosHpr(*ToontownGlobals.DinerBattleAPosHpr)
        self.battleBNode.setPosHpr(*ToontownGlobals.DinerBattleBPosHpr)
        self.cleanupIntervals()
        self.controlToons()
        self.setToonsToNeutral(self.involvedToons)
        for toonId in self.involvedToons:
            toon = self.cr.doId2do.get(toonId)
            if toon:
                self.putToonInCogSuit(toon)

        intervalName = 'PrepareBattleThreeMovie'
        seq = Sequence(self.makePrepareBattleThreeMovie(), Func(self.__onToBattleThree), name=intervalName)
        seq.start()
        self.storeInterval(seq, intervalName)
        base.playMusic(self.betweenPhaseMusic, looping=1, volume=0.9)

    def calcNotDeadList(self):
        if not self.notDeadList:
            self.notDeadList = []
            for tableIndex in xrange(len(self.tables)):
                table = self.tables[tableIndex]
                tableInfo = table.getNotDeadInfo()
                self.notDeadList += tableInfo

    def exitPrepareBattleThree(self):
        self.clearInterval('PrepareBattleThreeMovie')
        self.betweenPhaseMusic.stop()

    def __onToBattleThree(self, elapsedTime = 0):
        self.doneBarrier('PrepareBattleThree')

    def makePrepareBattleThreeMovie(self):
        loseSuitCamAngle = (0, 19, 6, -180, -5, 0)
        track = Sequence(
            Func(camera.reparentTo, self),
            Func(camera.setPos, Point3(0, -45, 5)),
            Func(camera.setHpr, Point3(0, 14, 0)),
            Func(self.setChatAbsolute, TTL.BossbotPhase3Speech1, CFSpeech),
            Wait(3.0),
            Func(self.setChatAbsolute, TTL.BossbotPhase3Speech2, CFSpeech),
            Wait(3.0),
            Func(camera.setPosHpr, base.localAvatar, *loseSuitCamAngle),
            Wait(1.0),
            self.loseCogSuits(self.toonsA + self.toonsB, base.localAvatar, loseSuitCamAngle),
            self.toonNormalEyes(self.involvedToons),
            Wait(2),
            Func(camera.reparentTo, self),
            Func(camera.setPos, Point3(0, -45, 5)),
            Func(camera.setHpr, Point3(0, 14, 0)),
            Func(self.setChatAbsolute, TTL.BossbotPhase3Speech3, CFSpeech),
            Wait(3.0),
            Func(self.clearChat))
        return track

    def enterBattleThree(self):
        self.cleanupIntervals()
        self.calcNotDeadList()
        for table in self.tables.values():
            table.setAllDinersToSitNeutral()

        self.battleANode.setPosHpr(*ToontownGlobals.DinerBattleAPosHpr)
        self.battleBNode.setPosHpr(*ToontownGlobals.DinerBattleBPosHpr)
        self.setToonsToNeutral(self.involvedToons)
        for toonId in self.involvedToons:
            toon = self.cr.doId2do.get(toonId)
            if toon:
                toon.takeOffSuit()

        mult = 1
        localAvatar.inventory.setBattleCreditMultiplier(mult)
        self.toonsToBattlePosition(self.toonsA, self.battleANode)
        self.toonsToBattlePosition(self.toonsB, self.battleBNode)
        self.releaseToons()
        base.playMusic(self.battleOneMusic, looping=1, volume=0.9)

    def exitBattleThree(self):
        self.cleanupBattles()
        self.battleOneMusic.stop()
        localAvatar.inventory.setBattleCreditMultiplier(1)

    def claimOneChair(self):
        chairInfo = None
        if self.notDeadList:
            chairInfo = self.notDeadList.pop()
        return chairInfo

    def enterPrepareBattleFour(self):
        self.controlToons()
        intervalName = 'PrepareBattleFourMovie'
        seq = Sequence(self.makePrepareBattleFourMovie(), Func(self.__onToBattleFour), name=intervalName)
        seq.start()
        self.storeInterval(seq, intervalName)
        base.playMusic(self.phaseFourMusic, looping=1, volume=0.9)

    def exitPrepareBattleFour(self):
        self.clearInterval('PrepareBattleFourMovie')
        self.phaseFourMusic.stop()

    def makePrepareBattleFourMovie(self):
        rToon = self.resistanceToon
        offsetZ = rToon.suit.getHeight() / 2.0
        track = Sequence(
            Func(self.__showResistanceToon, True),
            Func(rToon.setPos, Point3(0, -5, 0)),
            Func(rToon.setHpr, Point3(0, 0, 0)),
            Func(camera.reparentTo, rToon),
            Func(camera.setPos, Point3(0, 13, 3 + offsetZ)),
            Func(camera.setHpr, Point3(-180, 0, 0)),
            Func(self.banquetDoor.setH, 90),
            Func(rToon.setChatAbsolute, TTL.BossbotRTPhase4Speech1, CFSpeech),
            Wait(4.0),
            Func(rToon.setChatAbsolute, TTL.BossbotRTPhase4Speech2, CFSpeech),
            Wait(4.0),
            Func(self.__hideResistanceToon),
            Func(camera.reparentTo, self),
            Func(camera.setPos, Point3(0, -45, 5)),
            Func(camera.setHpr, Point3(0, 14, 0)),
            Func(self.setChatAbsolute, TTL.BossbotPhase4Speech1, CFSpeech),
            Func(self.banquetDoor.setH, 0),
            Wait(3.0),
            Func(self.setChatAbsolute, TTL.BossbotPhase4Speech2, CFSpeech),
            Func(self.bossClub.setScale, 0.01),
            Func(self.bossClub.reparentTo, self.rightHandJoint),
            LerpScaleInterval(self.bossClub, 3, Point3(1, 1, 1)),
            Func(self.clearChat))
        return track

    def __onToBattleFour(self, elapsedTime = 0):
        self.doneBarrier('PrepareBattleFour')

    def enterBattleFour(self):
        DistributedBossCog.DistributedBossCog.enterBattleFour(self)
        self.releaseToons(finalBattle=1)
        self.setToonsToNeutral(self.involvedToons)
        for toonId in self.involvedToons:
            toon = self.cr.doId2do.get(toonId)
            if toon:
                toon.takeOffSuit()

        self.bossClub.reparentTo(self.rightHandJoint)
        self.generateHealthBar()
        self.updateHealthBar()
        base.playMusic(self.phaseFourMusic, looping=1, volume=0.9)

    def exitBattleFour(self):
        DistributedBossCog.DistributedBossCog.exitBattleFour(self)
        self.phaseFourMusic.stop()

    def d_hitBoss(self, bossDamage):
        self.sendUpdate('hitBoss', [bossDamage])

    def d_ballHitBoss(self, bossDamage):
        self.sendUpdate('ballHitBoss', [bossDamage])

    def setBossDamage(self, bossDamage, recoverRate, recoverStartTime):
        if bossDamage > self.bossDamage:
            delta = bossDamage - self.bossDamage
            self.flashRed()
            self.showHpText(-delta, scale=5)
        self.bossDamage = bossDamage
        self.updateHealthBar()

    def setGolfSpot(self, golfSpot, golfSpotIndex):
        self.golfSpots[golfSpotIndex] = golfSpot

    def enterVictory(self):
        self.notify.debug('----- enterVictory')
        self.cleanupIntervals()
        self.cleanupAttacks()
        self.doAnimate('Ff_neutral', now=1)
        self.stopMoveTask()
        if hasattr(self, 'tableIndex'):
            table = self.tables[self.tableIndex]
            table.tableGroup.hide()
        self.loop('neutral')
        localAvatar.setCameraFov(ToontownGlobals.BossBattleCameraFov)
        self.clearChat()
        self.controlToons()
        self.setToonsToNeutral(self.involvedToons)
        self.happy = 1
        self.raised = 1
        self.forward = 1
        intervalName = 'VictoryMovie'
        seq = Sequence(self.makeVictoryMovie(), Func(self.__continueVictory), name=intervalName)
        seq.start()
        self.storeInterval(seq, intervalName)
        base.playMusic(self.phaseFourMusic, looping=1, volume=0.9)

    def __continueVictory(self):
        self.notify.debug('----- __continueVictory')
        self.stopAnimate()
        self.doneBarrier('Victory')

    def exitVictory(self):
        self.notify.debug('----- exitVictory')
        self.stopAnimate()
        self.unstash()
        localAvatar.setCameraFov(ToontownGlobals.CogHQCameraFov)
        self.phaseFourMusic.stop()

    def makeVictoryMovie(self):
        self.show()
        dustCloud = DustCloud.DustCloud(fBillboard=0, wantSound=1)
        dustCloud.reparentTo(self)
        dustCloud.setPos(0, -10, 3)
        dustCloud.setScale(4)
        dustCloud.wrtReparentTo(self.geom)
        dustCloud.createTrack(12)
        newHpr = self.getHpr()
        newHpr.setX(newHpr.getX() + 180)
        bossTrack = Sequence(
            Func(self.show),
            Func(camera.reparentTo, self),
            Func(camera.setPos, Point3(0, -35, 25)),
            Func(camera.setHpr, Point3(0, -20, 0)),
            Func(self.setChatAbsolute, TTL.BossbotRewardSpeech1, CFSpeech),
            Wait(3.0),
            Func(self.setChatAbsolute, TTL.BossbotRewardSpeech2, CFSpeech),
            Wait(2.0),
            Func(self.clearChat),
            Parallel(
                Sequence(
                    Wait(0.5),
                    Func(self.demotedCeo.setPos, self.getPos()),
                    Func(self.demotedCeo.setHpr, newHpr),
                    Func(self.hide),
                    Wait(0.5),
                    Func(self.demotedCeo.reparentTo, self.geom),
                    Func(self.demotedCeo.unstash)),
                Sequence(dustCloud.track)),
            Wait(2.0),
            Func(dustCloud.destroy))
        return bossTrack

    def enterReward(self):
        self.cleanupIntervals()
        self.clearChat()
        self.resistanceToon.clearChat()
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
                delayDeletes.append(DelayDelete.DelayDelete(toon, 'BossbotBoss.enterReward'))

        ival.delayDeletes = delayDeletes
        ival.start()
        self.storeInterval(ival, intervalName)
        base.playMusic(self.betweenPhaseMusic, looping=1, volume=0.9)

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
        self.betweenPhaseMusic.stop()

    def enterEpilogue(self):
        self.cleanupIntervals()
        self.clearChat()
        self.resistanceToon.clearChat()
        self.stash()
        self.stopAnimate()
        self.controlToons()
        self.__showResistanceToon(False)
        self.resistanceToon.reparentTo(render)
        self.resistanceToon.setPosHpr(*ToontownGlobals.BossbotRTEpiloguePosHpr)
        self.resistanceToon.loop('Sit')
        self.__arrangeToonsAroundResistanceToonForReward()
        camera.reparentTo(render)
        camera.setPos(self.resistanceToon, -9, 12, 6)
        camera.lookAt(self.resistanceToon, 0, 0, 3)
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

    def makeEpilogueMovie(self):
        epSpeech = TTLocalizer.BossbotRTCongratulations
        epSpeech = self.__talkAboutPromotion(epSpeech)
        bossTrack = Sequence(Func(self.resistanceToon.animFSM.request, 'neutral'), Func(self.resistanceToon.setLocalPageChat, epSpeech, 0))
        return bossTrack

    def __talkAboutPromotion(self, speech):
        if self.prevCogSuitLevel < ToontownGlobals.MaxCogSuitLevel:
            newCogSuitLevel = localAvatar.getCogLevels()[CogDisguiseGlobals.dept2deptIndex(self.style.dept)]
            if newCogSuitLevel == ToontownGlobals.MaxCogSuitLevel:
                speech += TTLocalizer.BossbotRTLastPromotion % (ToontownGlobals.MaxCogSuitLevel + 1)
            if newCogSuitLevel in ToontownGlobals.CogSuitHPLevels:
                speech += TTLocalizer.BossbotRTHPBoost
        else:
            speech += TTLocalizer.BossbotRTMaxed % (ToontownGlobals.MaxCogSuitLevel + 1)
        return speech

    def __arrangeToonsAroundResistanceToonForReward(self):
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
                toon.setPos(self.resistanceToon, x, y, 0)
                toon.headsUp(self.resistanceToon)
                toon.loop('neutral')
                toon.show()

    def doDirectedAttack(self, avId, attackCode):
        toon = base.cr.doId2do.get(avId)
        if toon:
            distance = toon.getDistance(self)
            gearRoot = self.rotateNode.attachNewNode('gearRoot-atk%d' % self.numAttacks)
            gearRoot.setZ(10)
            gearRoot.setTag('attackCode', str(attackCode))
            gearModel = self.getGearFrisbee()
            gearModel.setScale(0.2)
            gearRoot.headsUp(toon)
            toToonH = PythonUtil.fitDestAngle2Src(0, gearRoot.getH() + 180)
            gearRoot.lookAt(toon)
            neutral = 'Fb_neutral'
            if not self.twoFaced:
                neutral = 'Ff_neutral'
            gearTrack = Parallel()
            for i in range(4):
                nodeName = '%s-%s' % (str(i), globalClock.getFrameTime())
                node = gearRoot.attachNewNode(nodeName)
                node.hide()
                node.setPos(0, 5.85, 4.0)
                gear = gearModel.instanceTo(node)
                x = random.uniform(-5, 5)
                z = random.uniform(-3, 3)
                h = random.uniform(-720, 720)
                if i == 2:
                    x = 0
                    z = 0

                def detachNode(node):
                    if not node.isEmpty():
                        node.detachNode()
                    return Task.done

                def detachNodeLater(node = node):
                    if node.isEmpty():
                        return
                    center = node.node().getBounds().getCenter()
                    node.node().setBounds(BoundingSphere(center, distance * 1.5))
                    node.node().setFinal(1)
                    self.doMethodLater(0.005, detachNode, 'detach-%s-%s' % (gearRoot.getName(), node.getName()), extraArgs=[node])

                gearTrack.append(Sequence(Wait(i * 0.15), Func(node.show), Parallel(node.posInterval(1, Point3(x, distance, z), fluid=1), node.hprInterval(1, VBase3(h, 0, 0), fluid=1)), Func(detachNodeLater)))

            if not self.raised:
                neutral1Anim = self.getAnim('down2Up')
                self.raised = 1
            else:
                neutral1Anim = ActorInterval(self, neutral, startFrame=48)
            throwAnim = self.getAnim('throw')
            neutral2Anim = ActorInterval(self, neutral)
            extraAnim = Sequence()
            if attackCode == ToontownGlobals.BossCogSlowDirectedAttack:
                extraAnim = ActorInterval(self, neutral)

            def detachGearRoot(task, gearRoot = gearRoot):
                if not gearRoot.isEmpty():
                    gearRoot.detachNode()
                return task.done

            def detachGearRootLater(gearRoot = gearRoot):
                if gearRoot.isEmpty():
                    return
                self.doMethodLater(0.01, detachGearRoot, 'detach-%s' % gearRoot.getName())

            seq = Sequence(ParallelEndTogether(self.pelvis.hprInterval(1, VBase3(toToonH, 0, 0)), neutral1Anim), extraAnim, Parallel(Sequence(Wait(0.19), gearTrack, Func(detachGearRootLater), self.pelvis.hprInterval(0.2, VBase3(0, 0, 0))), Sequence(throwAnim, neutral2Anim)))
            self.doAnimate(seq, now=1, raised=1)

    def setBattleDifficulty(self, diff):
        self.notify.debug('battleDifficulty = %d' % diff)
        self.battleDifficulty = diff

    def doMoveAttack(self, tableIndex):
        self.tableIndex = tableIndex
        table = self.tables[tableIndex]
        fromPos = self.getPos()
        fromHpr = self.getHpr()
        toPos = table.getPos()
        foo = render.attachNewNode('foo')
        foo.setPos(self.getPos())
        foo.setHpr(self.getHpr())
        foo.lookAt(table.getLocator())
        toHpr = foo.getHpr()
        toHpr.setX(toHpr.getX() - 180)
        foo.removeNode()
        reverse = False
        moveTrack, hpr = self.moveBossToPoint(fromPos, fromHpr, toPos, toHpr, reverse)
        self.moveTrack = moveTrack
        self.moveTrack.start()
        self.storeInterval(self.moveTrack, 'moveTrack')

    def interruptMove(self):
        if self.moveTrack and self.moveTrack.isPlaying():
            self.moveTrack.pause()
        self.stopMoveTask()

    def setAttackCode(self, attackCode, avId = 0):
        if self.state != 'BattleFour':
            return
        self.numAttacks += 1
        self.notify.debug('numAttacks=%d' % self.numAttacks)
        self.attackCode = attackCode
        self.attackAvId = avId
        if attackCode == ToontownGlobals.BossCogMoveAttack:
            self.interruptMove()
            self.doMoveAttack(avId)
        elif attackCode == ToontownGlobals.BossCogGolfAttack:
            self.interruptMove()
            self.cleanupAttacks()
            self.doGolfAttack(avId, attackCode)
        elif attackCode == ToontownGlobals.BossCogDizzy:
            self.setDizzy(1)
            self.cleanupAttacks()
            self.doAnimate(None, raised=0, happy=1)
        elif attackCode == ToontownGlobals.BossCogDizzyNow:
            self.setDizzy(1)
            self.cleanupAttacks()
            self.doAnimate('hit', happy=1, now=1)
        elif attackCode == ToontownGlobals.BossCogSwatLeft:
            self.setDizzy(0)
            self.doAnimate('ltSwing', now=1)
        elif attackCode == ToontownGlobals.BossCogSwatRight:
            self.setDizzy(0)
            self.doAnimate('rtSwing', now=1)
        elif attackCode == ToontownGlobals.BossCogAreaAttack:
            self.setDizzy(0)
            self.doAnimate('areaAttack', now=1)
        elif attackCode == ToontownGlobals.BossCogFrontAttack:
            self.setDizzy(0)
            self.doAnimate('frontAttack', now=1)
        elif attackCode == ToontownGlobals.BossCogRecoverDizzyAttack:
            self.setDizzy(0)
            self.doAnimate('frontAttack', now=1)
        elif attackCode == ToontownGlobals.BossCogDirectedAttack or attackCode == ToontownGlobals.BossCogSlowDirectedAttack or attackCode == ToontownGlobals.BossCogGearDirectedAttack:
            self.interruptMove()
            self.setDizzy(0)
            self.doDirectedAttack(avId, attackCode)
        elif attackCode == ToontownGlobals.BossCogGolfAreaAttack:
            self.interruptMove()
            self.setDizzy(0)
            self.doGolfAreaAttack()
        elif attackCode == ToontownGlobals.BossCogNoAttack:
            self.setDizzy(0)
            self.doAnimate(None, raised=1)
        elif attackCode == ToontownGlobals.BossCogOvertimeAttack:
            self.interruptMove()
            self.setDizzy(0)
            self.cleanupAttacks()
            self.doOvertimeAttack(avId)
        return

    def signalAtTable(self):
        self.sendUpdate('reachedTable', [self.tableIndex])

    def closeEnter(self, colEntry):
        tableStr = colEntry.getIntoNodePath().getNetTag('tableIndex')
        if tableStr:
            tableIndex = int(tableStr)
            self.sendUpdate('hitTable', [tableIndex])

    def closeExit(self, colEntry):
        tableStr = colEntry.getIntoNodePath().getNetTag('tableIndex')
        if tableStr:
            tableIndex = int(tableStr)
            if self.tableIndex != tableIndex:
                self.sendUpdate('awayFromTable', [tableIndex])

    def setSpeedDamage(self, speedDamage, recoverRate, timestamp):
        recoverStartTime = globalClockDelta.networkToLocalTime(timestamp)
        self.speedDamage = speedDamage
        self.speedRecoverRate = recoverRate
        self.speedRecoverStartTime = recoverStartTime
        speedFraction = max(1 - speedDamage / self.maxSpeedDamage, 0)
        self.treads.setColorScale(1, speedFraction, speedFraction, 1)
        taskName = 'RecoverSpeedDamage'
        taskMgr.remove(taskName)
        if self.speedRecoverRate:
            taskMgr.add(self.__recoverSpeedDamage, taskName)

    def getSpeedDamage(self):
        now = globalClock.getFrameTime()
        elapsed = now - self.speedRecoverStartTime
        return max(self.speedDamage - self.speedRecoverRate * elapsed / 60.0, 0)

    def getFractionalSpeedDamage(self):
        result = self.getSpeedDamage() / self.maxSpeedDamage
        return result

    def __recoverSpeedDamage(self, task):
        speedDamage = self.getSpeedDamage()
        speedFraction = max(1 - speedDamage / self.maxSpeedDamage, 0)
        self.treads.setColorScale(1, speedFraction, speedFraction, 1)
        return task.cont

    def moveBossToPoint(self, fromPos, fromHpr, toPos, toHpr, reverse):
        vector = Vec3(toPos - fromPos)
        distance = vector.length()
        self.distanceToTravel = distance
        self.notify.debug('self.distanceToTravel = %s' % self.distanceToTravel)
        if toHpr == None:
            mat = Mat3(0, 0, 0, 0, 0, 0, 0, 0, 0)
            headsUp(mat, vector, CSDefault)
            scale = VBase3(0, 0, 0)
            shear = VBase3(0, 0, 0)
            toHpr = VBase3(0, 0, 0)
            decomposeMatrix(mat, scale, shear, toHpr, CSDefault)
        if fromHpr:
            newH = PythonUtil.fitDestAngle2Src(fromHpr[0], toHpr[0])
            toHpr = VBase3(newH, 0, 0)
        else:
            fromHpr = toHpr
        turnTime = abs(toHpr[0] - fromHpr[0]) / self.getCurTurnSpeed()
        if toHpr[0] < fromHpr[0]:
            leftRate = ToontownGlobals.BossCogTreadSpeed
        else:
            leftRate = -ToontownGlobals.BossCogTreadSpeed
        if reverse:
            rollTreadRate = -ToontownGlobals.BossCogTreadSpeed
        else:
            rollTreadRate = ToontownGlobals.BossCogTreadSpeed
        rollTime = distance / ToontownGlobals.BossCogRollSpeed
        deltaPos = toPos - fromPos
        self.toPos = toPos
        self.fromPos = fromPos
        self.dirVector = self.toPos - self.fromPos
        self.dirVector.normalize()
        track = Sequence(Func(self.setPos, fromPos), Func(self.headsUp, toPos), Parallel(self.hprInterval(turnTime, toHpr, fromHpr), self.rollLeftTreads(turnTime, leftRate), self.rollRightTreads(turnTime, -leftRate)), Func(self.startMoveTask))
        return (track, toHpr)

    def getCurTurnSpeed(self):
        result = ToontownGlobals.BossbotTurnSpeedMax - (ToontownGlobals.BossbotTurnSpeedMax - ToontownGlobals.BossbotTurnSpeedMin) * self.getFractionalSpeedDamage()
        return result

    def getCurRollSpeed(self):
        result = ToontownGlobals.BossbotRollSpeedMax - (ToontownGlobals.BossbotRollSpeedMax - ToontownGlobals.BossbotRollSpeedMin) * self.getFractionalSpeedDamage()
        return result

    def getCurTreadSpeed(self):
        result = ToontownGlobals.BossbotTreadSpeedMax - (ToontownGlobals.BossbotTreadSpeedMax - ToontownGlobals.BossbotTreadSpeedMin) * self.getFractionalSpeedDamage()
        return result

    def startMoveTask(self):
        taskMgr.add(self.moveBossTask, self.moveBossTaskName)

    def stopMoveTask(self):
        taskMgr.remove(self.moveBossTaskName)

    def moveBossTask(self, task):
        dt = globalClock.getDt()
        distanceTravelledThisFrame = dt * self.getCurRollSpeed()
        diff = self.toPos - self.getPos()
        distanceLeft = diff.length()

        def rollTexMatrix(t, object = object):
            object.setTexOffset(TextureStage.getDefault(), t, 0)

        self.treadsLeftPos += dt * self.getCurTreadSpeed()
        self.treadsRightPos += dt * self.getCurTreadSpeed()
        rollTexMatrix(self.treadsLeftPos, self.treadsLeft)
        rollTexMatrix(self.treadsRightPos, self.treadsRight)
        if distanceTravelledThisFrame >= distanceLeft:
            self.setPos(self.toPos)
            self.signalAtTable()
            return Task.done
        else:
            newPos = self.getPos() + self.dirVector * dt * self.getCurRollSpeed()
            self.setPos(newPos)
            return Task.cont

    def doZapToon(self, toon, pos = None, hpr = None, ts = 0, fling = 1, shake = 1):
        zapName = toon.uniqueName('zap')
        self.clearInterval(zapName)
        zapTrack = Sequence(name=zapName)
        if toon == localAvatar:
            self.toOuchMode()
            messenger.send('interrupt-pie')
            self.enableLocalToonSimpleCollisions()
        else:
            zapTrack.append(Func(toon.stopSmooth))

        def getSlideToPos(toon = toon):
            return render.getRelativePoint(toon, Point3(0, -5, 0))

        if pos != None and hpr != None:
            (zapTrack.append(Func(toon.setPosHpr, pos, hpr)),)
        toonTrack = Parallel()
        if shake and toon == localAvatar:
            toonTrack.append(Sequence(Func(camera.setZ, camera, 1), Wait(0.15), Func(camera.setZ, camera, -2), Wait(0.15), Func(camera.setZ, camera, 1)))
        if fling:
            if self.isToonRoaming(toon.doId):
                toonTrack += [ActorInterval(toon, 'slip-backward')]
                toonTrack += [toon.posInterval(0.5, getSlideToPos, fluid=1)]
        else:
            toonTrack += [ActorInterval(toon, 'slip-forward')]
        zapTrack.append(toonTrack)
        if toon == localAvatar:
            zapTrack.append(Func(self.disableLocalToonSimpleCollisions))
            currentState = self.state
            if currentState in ('BattleFour', 'BattleTwo'):
                zapTrack.append(Func(self.toFinalBattleMode))
            else:
                self.notify.warning('doZapToon going to walkMode, how did this happen?')
                zapTrack.append(Func(self.toWalkMode))
        else:
            zapTrack.append(Func(toon.startSmooth))
        if ts > 0:
            startTime = ts
        else:
            zapTrack = Sequence(Wait(-ts), zapTrack)
            startTime = 0
        zapTrack.append(Func(self.clearInterval, zapName))
        zapTrack.delayDelete = DelayDelete.DelayDelete(toon, 'BossbotBoss.doZapToon')
        zapTrack.start(startTime)
        self.storeInterval(zapTrack, zapName)
        return

    def zapLocalToon(self, attackCode, origin = None):
        if self.localToonIsSafe or localAvatar.ghostMode or localAvatar.isStunned:
            return
        if globalClock.getFrameTime() < self.lastZapLocalTime + 1.0:
            return
        else:
            self.lastZapLocalTime = globalClock.getFrameTime()
        self.notify.debug('zapLocalToon frameTime=%s' % globalClock.getFrameTime())
        messenger.send('interrupt-pie')
        place = self.cr.playGame.getPlace()
        currentState = None
        if place:
            currentState = place.fsm.getCurrentState().getName()
        if currentState != 'walk' and currentState != 'finalBattle' and currentState != 'crane':
            return
        self.notify.debug('continuing zap')
        toon = localAvatar
        fling = 1
        shake = 0
        if attackCode == ToontownGlobals.BossCogAreaAttack:
            fling = 0
            shake = 1
        if fling:
            if origin == None:
                origin = self
            if self.isToonRoaming(toon.doId):
                camera.wrtReparentTo(render)
                toon.headsUp(origin)
                camera.wrtReparentTo(toon)
        bossRelativePos = toon.getPos(self.getGeomNode())
        bp2d = Vec2(bossRelativePos[0], bossRelativePos[1])
        bp2d.normalize()
        pos = toon.getPos()
        hpr = toon.getHpr()
        timestamp = globalClockDelta.getFrameNetworkTime()
        self.sendUpdate('zapToon', [pos[0],
         pos[1],
         pos[2],
         hpr[0],
         hpr[1],
         hpr[2],
         bp2d[0],
         bp2d[1],
         attackCode,
         timestamp])
        self.doZapToon(toon, fling=fling, shake=shake)
        return

    def getToonTableIndex(self, toonId):
        tableIndex = -1
        for table in self.tables.values():
            if table.avId == toonId:
                tableIndex = table.index
                break

        return tableIndex

    def getToonGolfSpotIndex(self, toonId):
        golfSpotIndex = -1
        for golfSpot in self.golfSpots.values():
            if golfSpot.avId == toonId:
                golfSpotIndex = golfSpot.index
                break

        return golfSpotIndex

    def isToonOnTable(self, toonId):
        result = self.getToonTableIndex(toonId) != -1
        return result

    def isToonOnGolfSpot(self, toonId):
        result = self.getToonGolfSpotIndex(toonId) != -1
        return result

    def isToonRoaming(self, toonId):
        result = not self.isToonOnTable(toonId) and not self.isToonOnGolfSpot(toonId)
        return result

    def getGolfBall(self):
        golfRoot = NodePath('golfRoot')
        golfBall = loader.loadModel('phase_6/models/golf/golf_ball')
        golfBall.setColorScale(0.75, 0.75, 0.75, 0.5)
        golfBall.setTransparency(1)
        ballScale = 5
        golfBall.setScale(ballScale)
        golfBall.reparentTo(golfRoot)
        cs = CollisionSphere(0, 0, 0, ballScale * 0.25)
        cs.setTangible(0)
        cn = CollisionNode('BossZap')
        cn.addSolid(cs)
        cn.setIntoCollideMask(ToontownGlobals.WallBitmask)
        cnp = golfRoot.attachNewNode(cn)
        return golfRoot

    def doGolfAttack(self, avId, attackCode):
        toon = base.cr.doId2do.get(avId)
        if toon:
            distance = toon.getDistance(self)
            self.notify.debug('distance = %s' % distance)
            gearRoot = self.rotateNode.attachNewNode('gearRoot-atk%d' % self.numAttacks)
            gearRoot.setZ(10)
            gearRoot.setTag('attackCode', str(attackCode))
            gearModel = self.getGolfBall()
            self.ballLaunch = NodePath('')
            self.ballLaunch.reparentTo(gearRoot)
            self.ballLaunch.setPos(self.BallLaunchOffset)
            gearRoot.headsUp(toon)
            toToonH = PythonUtil.fitDestAngle2Src(0, gearRoot.getH() + 180)
            gearRoot.lookAt(toon)
            neutral = 'Fb_neutral'
            if not self.twoFaced:
                neutral = 'Ff_neutral'
            gearTrack = Parallel()
            for i in range(5):
                nodeName = '%s-%s' % (str(i), globalClock.getFrameTime())
                node = gearRoot.attachNewNode(nodeName)
                node.hide()
                node.reparentTo(self.ballLaunch)
                node.wrtReparentTo(gearRoot)
                distance = toon.getDistance(node)
                gear = gearModel.instanceTo(node)
                x = random.uniform(-5, 5)
                z = random.uniform(-3, 3)
                p = random.uniform(-720, -90)
                y = distance + random.uniform(5, 15)
                if i == 2:
                    x = 0
                    z = 0
                    y = distance + 10

                def detachNode(node):
                    if not node.isEmpty():
                        node.detachNode()
                    return Task.done

                def detachNodeLater(node = node):
                    if node.isEmpty():
                        return
                    node.node().setBounds(BoundingSphere(Point3(0, 0, 0), distance * 1.5))
                    node.node().setFinal(1)
                    self.doMethodLater(0.005, detachNode, 'detach-%s-%s' % (gearRoot.getName(), node.getName()), extraArgs=[node])

                gearTrack.append(Sequence(Wait(26.0 / 24.0), Wait(i * 0.15), Func(node.show), Parallel(node.posInterval(1, Point3(x, y, z), fluid=1), node.hprInterval(1, VBase3(0, p, 0), fluid=1)), Func(detachNodeLater)))

            if not self.raised:
                neutral1Anim = self.getAnim('down2Up')
                self.raised = 1
            else:
                neutral1Anim = ActorInterval(self, neutral, startFrame=48)
            throwAnim = self.getAnim('golf_swing')
            neutral2Anim = ActorInterval(self, neutral)
            extraAnim = Sequence()
            if attackCode == ToontownGlobals.BossCogSlowDirectedAttack:
                extraAnim = ActorInterval(self, neutral)

            def detachGearRoot(task, gearRoot = gearRoot):
                if not gearRoot.isEmpty():
                    gearRoot.detachNode()
                return task.done

            def detachGearRootLater(gearRoot = gearRoot):
                self.doMethodLater(0.01, detachGearRoot, 'detach-%s' % gearRoot.getName())

            seq = Sequence(ParallelEndTogether(self.pelvis.hprInterval(1, VBase3(toToonH, 0, 0)), neutral1Anim), extraAnim, Parallel(Sequence(Wait(0.19), gearTrack, Func(detachGearRootLater), self.pelvis.hprInterval(0.2, VBase3(0, 0, 0))), Sequence(throwAnim, neutral2Anim), Sequence(Wait(0.85), SoundInterval(self.swingClubSfx, node=self, duration=0.45, cutOff=300, listenerNode=base.localAvatar))))
            self.doAnimate(seq, now=1, raised=1)

    def doGolfAreaAttack(self):
        toons = []
        for toonId in self.involvedToons:
            toon = base.cr.doId2do.get(toonId)
            if toon:
                toons.append(toon)

        if not toons:
            return
        neutral = 'Fb_neutral'
        if not self.twoFaced:
            neutral = 'Ff_neutral'
        if not self.raised:
            neutral1Anim = self.getAnim('down2Up')
            self.raised = 1
        else:
            neutral1Anim = ActorInterval(self, neutral, startFrame=48)
        throwAnim = self.getAnim('golf_swing')
        neutral2Anim = ActorInterval(self, neutral)
        extraAnim = Sequence()
        if False:
            extraAnim = ActorInterval(self, neutral)
        gearModel = self.getGolfBall()
        toToonH = self.rotateNode.getH() + 360
        self.notify.debug('toToonH = %s' % toToonH)
        gearRoots = []
        allGearTracks = Parallel()
        for toon in toons:
            gearRoot = self.rotateNode.attachNewNode('gearRoot-atk%d-%d' % (self.numAttacks, toons.index(toon)))
            gearRoot.setZ(10)
            gearRoot.setTag('attackCode', str(ToontownGlobals.BossCogGolfAreaAttack))
            gearRoot.lookAt(toon)
            ballLaunch = NodePath('')
            ballLaunch.reparentTo(gearRoot)
            ballLaunch.setPos(self.BallLaunchOffset)
            gearTrack = Parallel()
            for i in range(5):
                nodeName = '%s-%s' % (str(i), globalClock.getFrameTime())
                node = gearRoot.attachNewNode(nodeName)
                node.hide()
                node.reparentTo(ballLaunch)
                node.wrtReparentTo(gearRoot)
                distance = toon.getDistance(node)
                toonPos = toon.getPos(render)
                nodePos = node.getPos(render)
                vector = toonPos - nodePos
                gear = gearModel.instanceTo(node)
                x = random.uniform(-5, 5)
                z = random.uniform(-3, 3)
                p = random.uniform(-720, -90)
                y = distance + random.uniform(5, 15)
                if i == 2:
                    x = 0
                    z = 0
                    y = distance + 10

                def detachNode(node):
                    if not node.isEmpty():
                        node.detachNode()
                    return Task.done

                def detachNodeLater(node = node):
                    if node.isEmpty():
                        return
                    node.node().setBounds(BoundingSphere(Point3(0, 0, 0), distance * 1.5))
                    node.node().setFinal(1)
                    self.doMethodLater(0.005, detachNode, 'detach-%s-%s' % (gearRoot.getName(), node.getName()), extraArgs=[node])

                gearTrack.append(Sequence(Wait(26.0 / 24.0), Wait(i * 0.15), Func(node.show), Parallel(node.posInterval(1, Point3(x, y, z), fluid=1), node.hprInterval(1, VBase3(0, p, 0), fluid=1)), Func(detachNodeLater)))

            allGearTracks.append(gearTrack)

        def detachGearRoots(gearRoots = gearRoots):
            for gearRoot in gearRoots:

                def detachGearRoot(task, gearRoot = gearRoot):
                    if not gearRoot.isEmpty():
                        gearRoot.detachNode()
                    return task.done

                if gearRoot.isEmpty():
                    continue
                self.doMethodLater(0.01, detachGearRoot, 'detach-%s' % gearRoot.getName())

            gearRoots = []

        rotateFire = Parallel(self.pelvis.hprInterval(2, VBase3(toToonH + 1440, 0, 0)), allGearTracks)
        seq = Sequence(Func(base.playSfx, self.warningSfx), Func(self.saySomething, TTLocalizer.GolfAreaAttackTaunt), ParallelEndTogether(self.pelvis.hprInterval(2, VBase3(toToonH, 0, 0)), neutral1Anim), extraAnim, Parallel(Sequence(rotateFire, Func(detachGearRoots), Func(self.pelvis.setHpr, VBase3(0, 0, 0))), Sequence(throwAnim, neutral2Anim), Sequence(Wait(0.85), SoundInterval(self.swingClubSfx, node=self, duration=0.45, cutOff=300, listenerNode=base.localAvatar))))
        self.doAnimate(seq, now=1, raised=1)

    def saySomething(self, chatString):
        intervalName = 'CEOTaunt'
        seq = Sequence(name=intervalName)
        seq.append(Func(self.setChatAbsolute, chatString, CFSpeech))
        seq.append(Wait(4.0))
        seq.append(Func(self.clearChat))
        oldSeq = self.activeIntervals.get(intervalName)
        if oldSeq:
            oldSeq.finish()
        seq.start()
        self.activeIntervals[intervalName] = seq

    def d_hitToon(self, toonId):
        self.notify.debug('----- d_hitToon')
        self.sendUpdate('hitToon', [toonId])

    def toonGotHealed(self, toonId):
        toon = base.cr.doId2do.get(toonId)
        if toon:
            base.playSfx(self.toonUpSfx, node=toon)

    def localToonTouchedBeltToonup(self, beltIndex, toonupIndex, toonupNum):
        avId = base.localAvatar.doId
        doRequest = True
        if doRequest:
            self.sendUpdate('requestGetToonup', [beltIndex, toonupIndex, toonupNum])

    def toonGotToonup(self, avId, beltIndex, toonupIndex, toonupNum):
        if self.belts[beltIndex]:
            self.belts[beltIndex].removeToonup(toonupIndex)
        toon = base.cr.doId2do.get(avId)
        if toon:
            base.playSfx(self.toonUpSfx, node=toon)

    def doOvertimeAttack(self, index):
        attackCode = ToontownGlobals.BossCogOvertimeAttack
        attackBelts = Sequence()
        if index < len(self.belts):
            belt = self.belts[index]
            self.saySomething(TTLocalizer.OvertimeAttackTaunts[index])
            if index:
                self.bossClubIntervals[0].finish()
                self.bossClubIntervals[1].loop()
            else:
                self.bossClubIntervals[1].finish()
                self.bossClubIntervals[0].loop()
            distance = belt.beltModel.getDistance(self)
            gearRoot = self.rotateNode.attachNewNode('gearRoot')
            gearRoot.setZ(10)
            gearRoot.setTag('attackCode', str(attackCode))
            gearModel = self.getGearFrisbee()
            gearModel.setScale(0.2)
            gearRoot.headsUp(belt.beltModel)
            toToonH = PythonUtil.fitDestAngle2Src(0, gearRoot.getH() + 180)
            gearRoot.lookAt(belt.beltModel)
            neutral = 'Fb_neutral'
            if not self.twoFaced:
                neutral = 'Ff_neutral'
            gearTrack = Parallel()
            for i in range(4):
                node = gearRoot.attachNewNode(str(i))
                node.hide()
                node.setPos(0, 5.85, 4.0)
                gear = gearModel.instanceTo(node)
                x = random.uniform(-5, 5)
                z = random.uniform(-3, 3)
                h = random.uniform(-720, 720)
                gearTrack.append(Sequence(Wait(i * 0.15), Func(node.show), Parallel(node.posInterval(1, Point3(x, distance, z), fluid=1), node.hprInterval(1, VBase3(h, 0, 0), fluid=1)), Func(node.detachNode)))

            if not self.raised:
                neutral1Anim = self.getAnim('down2Up')
                self.raised = 1
            else:
                neutral1Anim = ActorInterval(self, neutral, startFrame=48)
            throwAnim = self.getAnim('throw')
            neutral2Anim = ActorInterval(self, neutral)
            extraAnim = Sequence()
            if attackCode == ToontownGlobals.BossCogSlowDirectedAttack:
                extraAnim = ActorInterval(self, neutral)
            seq = Sequence(ParallelEndTogether(self.pelvis.hprInterval(1, VBase3(toToonH, 0, 0)), neutral1Anim), extraAnim, Parallel(Sequence(Wait(0.19), gearTrack, Func(gearRoot.detachNode), Func(self.explodeSfx.play), self.pelvis.hprInterval(0.2, VBase3(0, 0, 0))), Sequence(throwAnim, neutral2Anim)), Func(belt.request, 'Inactive'))
            attackBelts.append(seq)
        self.notify.debug('attackBelts duration= %.2f' % attackBelts.getDuration())
        self.doAnimate(attackBelts, now=1, raised=1)
