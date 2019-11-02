from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *
from direct.distributed.ClockDelta import *
from direct.directnotify import DirectNotifyGlobal
from otp.avatar import DistributedAvatar
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import ToontownBattleGlobals
from toontown.battle import BattleExperience
from toontown.battle import BattleBase
import BossCog
import SuitDNA
from toontown.coghq import CogDisguiseGlobals
from direct.showbase import Transitions
from toontown.hood import ZoneUtil
from toontown.building import ElevatorUtils
from toontown.building import ElevatorConstants
from toontown.distributed import DelayDelete
from toontown.effects import DustCloud
from toontown.toonbase import TTLocalizer
from toontown.friends import FriendsListManager
from direct.controls.ControlManager import CollisionHandlerRayStart
from direct.showbase import PythonUtil
import random

class DistributedBossCog(DistributedAvatar.DistributedAvatar, BossCog.BossCog):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedBossCog')
    allowClickedNameTag = True

    def __init__(self, cr):
        DistributedAvatar.DistributedAvatar.__init__(self, cr)
        BossCog.BossCog.__init__(self)
        self.gotAllToons = 0
        self.toonsA = []
        self.toonsB = []
        self.involvedToons = []
        self.toonRequest = None
        self.battleNumber = 0
        self.battleAId = None
        self.battleBId = None
        self.battleA = None
        self.battleB = None
        self.battleRequest = None
        self.arenaSide = 0
        self.toonSphere = None
        self.localToonIsSafe = 0
        self.__toonsStuckToFloor = []
        self.cqueue = None
        self.rays = None
        self.ray1 = None
        self.ray2 = None
        self.ray3 = None
        self.e1 = None
        self.e2 = None
        self.e3 = None
        self.battleANode = self.attachNewNode('battleA')
        self.battleBNode = self.attachNewNode('battleB')
        self.battleANode.setPosHpr(*ToontownGlobals.BossCogBattleAPosHpr)
        self.battleBNode.setPosHpr(*ToontownGlobals.BossCogBattleBPosHpr)
        self.activeIntervals = {}
        self.flashInterval = None
        self.elevatorType = ElevatorConstants.ELEVATOR_VP
        return

    def announceGenerate(self):
        DistributedAvatar.DistributedAvatar.announceGenerate(self)
        self.prevCogSuitLevel = localAvatar.getCogLevels()[CogDisguiseGlobals.dept2deptIndex(self.style.dept)]
        nearBubble = CollisionSphere(0, 0, 0, 50)
        nearBubble.setTangible(0)
        nearBubbleNode = CollisionNode('NearBoss')
        nearBubbleNode.setCollideMask(ToontownGlobals.WallBitmask)
        nearBubbleNode.addSolid(nearBubble)
        self.attachNewNode(nearBubbleNode)
        self.accept('enterNearBoss', self.avatarNearEnter)
        self.accept('exitNearBoss', self.avatarNearExit)
        self.collNode.removeSolid(0)
        tube1 = CollisionTube(6.5, -7.5, 2, 6.5, 7.5, 2, 2.5)
        tube2 = CollisionTube(-6.5, -7.5, 2, -6.5, 7.5, 2, 2.5)
        roof = CollisionPolygon(Point3(-4.4, 7.1, 5.5), Point3(-4.4, -7.1, 5.5), Point3(4.4, -7.1, 5.5), Point3(4.4, 7.1, 5.5))
        side1 = CollisionPolygon(Point3(-4.4, -7.1, 5.5), Point3(-4.4, 7.1, 5.5), Point3(-4.4, 7.1, 0), Point3(-4.4, -7.1, 0))
        side2 = CollisionPolygon(Point3(4.4, 7.1, 5.5), Point3(4.4, -7.1, 5.5), Point3(4.4, -7.1, 0), Point3(4.4, 7.1, 0))
        front1 = CollisionPolygon(Point3(4.4, -7.1, 5.5), Point3(-4.4, -7.1, 5.5), Point3(-4.4, -7.1, 5.2), Point3(4.4, -7.1, 5.2))
        back1 = CollisionPolygon(Point3(-4.4, 7.1, 5.5), Point3(4.4, 7.1, 5.5), Point3(4.4, 7.1, 5.2), Point3(-4.4, 7.1, 5.2))
        self.collNode.addSolid(tube1)
        self.collNode.addSolid(tube2)
        self.collNode.addSolid(roof)
        self.collNode.addSolid(side1)
        self.collNode.addSolid(side2)
        self.collNode.addSolid(front1)
        self.collNode.addSolid(back1)
        self.collNodePath.reparentTo(self.axle)
        self.collNode.setCollideMask(ToontownGlobals.PieBitmask | ToontownGlobals.WallBitmask | ToontownGlobals.CameraBitmask)
        self.collNode.setName('BossZap')
        self.setTag('attackCode', str(ToontownGlobals.BossCogElectricFence))
        self.accept('enterBossZap', self.__touchedBoss)
        bubbleL = CollisionSphere(10, -5, 0, 10)
        bubbleL.setTangible(0)
        bubbleLNode = CollisionNode('BossZap')
        bubbleLNode.setCollideMask(ToontownGlobals.WallBitmask)
        bubbleLNode.addSolid(bubbleL)
        self.bubbleL = self.axle.attachNewNode(bubbleLNode)
        self.bubbleL.setTag('attackCode', str(ToontownGlobals.BossCogSwatLeft))
        self.bubbleL.stash()
        bubbleR = CollisionSphere(-10, -5, 0, 10)
        bubbleR.setTangible(0)
        bubbleRNode = CollisionNode('BossZap')
        bubbleRNode.setCollideMask(ToontownGlobals.WallBitmask)
        bubbleRNode.addSolid(bubbleR)
        self.bubbleR = self.axle.attachNewNode(bubbleRNode)
        self.bubbleR.setTag('attackCode', str(ToontownGlobals.BossCogSwatRight))
        self.bubbleR.stash()
        bubbleF = CollisionSphere(0, -25, 0, 12)
        bubbleF.setTangible(0)
        bubbleFNode = CollisionNode('BossZap')
        bubbleFNode.setCollideMask(ToontownGlobals.WallBitmask)
        bubbleFNode.addSolid(bubbleF)
        self.bubbleF = self.rotateNode.attachNewNode(bubbleFNode)
        self.bubbleF.setTag('attackCode', str(ToontownGlobals.BossCogFrontAttack))
        self.bubbleF.stash()

    def disable(self):
        DistributedAvatar.DistributedAvatar.disable(self)
        self.battleAId = None
        self.battleBId = None
        self.battleA = None
        self.battleB = None
        self.cr.relatedObjectMgr.abortRequest(self.toonRequest)
        self.toonRequest = None
        self.cr.relatedObjectMgr.abortRequest(self.battleRequest)
        self.battleRequest = None
        self.stopAnimate()
        self.cleanupIntervals()
        self.cleanupFlash()
        self.disableLocalToonSimpleCollisions()
        self.ignoreAll()
        return

    def delete(self):
        try:
            self.DistributedBossCog_deleted
        except:
            self.DistributedBossCog_deleted = 1
            self.ignoreAll()
            DistributedAvatar.DistributedAvatar.delete(self)
            BossCog.BossCog.delete(self)

    def setDNAString(self, dnaString):
        BossCog.BossCog.setDNAString(self, dnaString)

    def getDNAString(self):
        return self.dna.makeNetString()

    def setDNA(self, dna):
        BossCog.BossCog.setDNA(self, dna)

    def setToonIds(self, involvedToons, toonsA, toonsB):
        self.involvedToons = involvedToons
        self.toonsA = toonsA
        self.toonsB = toonsB
        self.cr.relatedObjectMgr.abortRequest(self.toonRequest)
        self.gotAllToons = 0
        self.toonRequest = self.cr.relatedObjectMgr.requestObjects(self.involvedToons, allCallback=self.__gotAllToons, eachCallback=self.gotToon)

    def getDialogueArray(self, *args):
        return BossCog.BossCog.getDialogueArray(self, *args)

    def storeInterval(self, interval, name):
        if name in self.activeIntervals:
            ival = self.activeIntervals[name]
            if hasattr(ival, 'delayDelete') or hasattr(ival, 'delayDeletes'):
                self.clearInterval(name, finish=1)
        self.activeIntervals[name] = interval

    def cleanupIntervals(self):
        for interval in self.activeIntervals.values():
            interval.finish()
            DelayDelete.cleanupDelayDeletes(interval)

        self.activeIntervals = {}

    def clearInterval(self, name, finish = 1):
        if self.activeIntervals.has_key(name):
            ival = self.activeIntervals[name]
            if finish:
                ival.finish()
            else:
                ival.pause()
            if self.activeIntervals.has_key(name):
                DelayDelete.cleanupDelayDeletes(ival)
                del self.activeIntervals[name]
        else:
            self.notify.debug('interval: %s already cleared' % name)

    def finishInterval(self, name):
        if self.activeIntervals.has_key(name):
            interval = self.activeIntervals[name]
            interval.finish()

    def d_avatarEnter(self):
        self.sendUpdate('avatarEnter', [])

    def d_avatarExit(self):
        self.sendUpdate('avatarExit', [])

    def avatarNearEnter(self, entry):
        self.sendUpdate('avatarNearEnter', [])

    def avatarNearExit(self, entry):
        self.sendUpdate('avatarNearExit', [])

    def hasLocalToon(self):
        doId = localAvatar.doId
        return doId in self.toonsA or doId in self.toonsB

    def setBattleExperience(self, id0, origExp0, earnedExp0, origQuests0, items0, missedItems0, origMerits0, merits0, parts0, id1, origExp1, earnedExp1, origQuests1, items1, missedItems1, origMerits1, merits1, parts1, id2, origExp2, earnedExp2, origQuests2, items2, missedItems2, origMerits2, merits2, parts2, id3, origExp3, earnedExp3, origQuests3, items3, missedItems3, origMerits3, merits3, parts3, id4, origExp4, earnedExp4, origQuests4, items4, missedItems4, origMerits4, merits4, parts4, id5, origExp5, earnedExp5, origQuests5, items5, missedItems5, origMerits5, merits5, parts5, id6, origExp6, earnedExp6, origQuests6, items6, missedItems6, origMerits6, merits6, parts6, id7, origExp7, earnedExp7, origQuests7, items7, missedItems7, origMerits7, merits7, parts7, deathList, uberList, helpfulToons):
        self.deathList = deathList
        self.uberList = uberList
        self.helpfulToons = helpfulToons
        entries = ((id0,
          origExp0,
          earnedExp0,
          origQuests0,
          items0,
          missedItems0,
          origMerits0,
          merits0,
          parts0),
         (id1,
          origExp1,
          earnedExp1,
          origQuests1,
          items1,
          missedItems1,
          origMerits1,
          merits1,
          parts1),
         (id2,
          origExp2,
          earnedExp2,
          origQuests2,
          items2,
          missedItems2,
          origMerits2,
          merits2,
          parts2),
         (id3,
          origExp3,
          earnedExp3,
          origQuests3,
          items3,
          missedItems3,
          origMerits3,
          merits3,
          parts3),
         (id4,
          origExp4,
          earnedExp4,
          origQuests4,
          items4,
          missedItems4,
          origMerits4,
          merits4,
          parts4),
         (id5,
          origExp5,
          earnedExp5,
          origQuests5,
          items5,
          missedItems5,
          origMerits5,
          merits5,
          parts5),
         (id6,
          origExp6,
          earnedExp6,
          origQuests6,
          items6,
          missedItems6,
          origMerits6,
          merits6,
          parts6),
         (id7,
          origExp7,
          earnedExp7,
          origQuests7,
          items7,
          missedItems7,
          origMerits7,
          merits7,
          parts7))
        self.toonRewardDicts = BattleExperience.genRewardDicts(entries)
        self.toonRewardIds = [id0,
         id1,
         id2,
         id3,
         id4,
         id5,
         id6,
         id7]

    def setArenaSide(self, arenaSide):
        self.arenaSide = arenaSide

    def setState(self, state):
        self.request(state)

    def gotToon(self, toon):
        stateName = self.state

    def __gotAllToons(self, toons):
        self.gotAllToons = 1
        messenger.send('gotAllToons')

    def setBattleIds(self, battleNumber, battleAId, battleBId):
        self.battleNumber = battleNumber
        self.battleAId = battleAId
        self.battleBId = battleBId
        self.cr.relatedObjectMgr.abortRequest(self.battleRequest)
        self.battleRequest = self.cr.relatedObjectMgr.requestObjects([self.battleAId, self.battleBId], allCallback=self.__gotBattles)

    def __gotBattles(self, battles):
        self.battleRequest = None
        if self.battleA and self.battleA != battles[0]:
            self.battleA.cleanupBattle()
        if self.battleB and self.battleB != battles[1]:
            self.battleB.cleanupBattle()
        self.battleA = battles[0]
        self.battleB = battles[1]
        return

    def cleanupBattles(self):
        if self.battleA:
            self.battleA.cleanupBattle()
        if self.battleB:
            self.battleB.cleanupBattle()

    def makeEndOfBattleMovie(self, hasLocalToon):
        return Sequence()

    def controlToons(self):
        for toonId in self.involvedToons:
            toon = self.cr.doId2do.get(toonId)
            if toon:
                toon.stopLookAround()
                toon.stopSmooth()

        if self.hasLocalToon():
            self.toMovieMode()

    def enableLocalToonSimpleCollisions(self):
        if not self.toonSphere:
            sphere = CollisionSphere(0, 0, 1, 1)
            sphere.setRespectEffectiveNormal(0)
            sphereNode = CollisionNode('SimpleCollisions')
            sphereNode.setFromCollideMask(ToontownGlobals.WallBitmask | ToontownGlobals.FloorBitmask)
            sphereNode.setIntoCollideMask(BitMask32.allOff())
            sphereNode.addSolid(sphere)
            self.toonSphere = NodePath(sphereNode)
            self.toonSphereHandler = CollisionHandlerPusher()
            self.toonSphereHandler.addCollider(self.toonSphere, localAvatar)
        self.toonSphere.reparentTo(localAvatar)
        base.cTrav.addCollider(self.toonSphere, self.toonSphereHandler)

    def disableLocalToonSimpleCollisions(self):
        if self.toonSphere:
            base.cTrav.removeCollider(self.toonSphere)
            self.toonSphere.detachNode()

    def toOuchMode(self):
        if self.cr:
            place = self.cr.playGame.getPlace()
            if place and hasattr(place, 'fsm'):
                place.setState('ouch')

    def toCraneMode(self):
        if self.cr:
            place = self.cr.playGame.getPlace()
            if place and hasattr(place, 'fsm'):
                place.setState('crane')

    def toMovieMode(self):
        if self.cr:
            place = self.cr.playGame.getPlace()
            if place and hasattr(place, 'fsm'):
                place.setState('movie')

    def toWalkMode(self):
        if self.cr:
            place = self.cr.playGame.getPlace()
            if place and hasattr(place, 'fsm'):
                place.setState('walk')

    def toFinalBattleMode(self):
        if self.cr:
            place = self.cr.playGame.getPlace()
            if place and hasattr(place, 'fsm'):
                place.setState('finalBattle')

    def releaseToons(self, finalBattle = 0):
        for toonId in self.involvedToons:
            toon = self.cr.doId2do.get(toonId)
            if toon:
                if self.battleA and toon in self.battleA.toons:
                    pass
                elif self.battleB and toon in self.battleB.toons:
                    pass
                else:
                    toon.startLookAround()
                    toon.startSmooth()
                    toon.wrtReparentTo(render)
                    if toon == localAvatar:
                        if finalBattle:
                            self.toFinalBattleMode()
                        else:
                            self.toWalkMode()

    def stickToonsToFloor(self):
        self.unstickToons()
        rayNode = CollisionNode('stickToonsToFloor')
        rayNode.addSolid(CollisionRay(0.0, 0.0, CollisionHandlerRayStart, 0.0, 0.0, -1.0))
        rayNode.setFromCollideMask(ToontownGlobals.FloorBitmask)
        rayNode.setIntoCollideMask(BitMask32.allOff())
        ray = NodePath(rayNode)
        lifter = CollisionHandlerFloor()
        lifter.setOffset(ToontownGlobals.FloorOffset)
        lifter.setReach(10.0)
        for toonId in self.involvedToons:
            toon = base.cr.doId2do.get(toonId)
            if toon:
                toonRay = ray.instanceTo(toon)
                lifter.addCollider(toonRay, toon)
                base.cTrav.addCollider(toonRay, lifter)
                self.__toonsStuckToFloor.append(toonRay)

    def unstickToons(self):
        for toonRay in self.__toonsStuckToFloor:
            base.cTrav.removeCollider(toonRay)
            toonRay.removeNode()

        self.__toonsStuckToFloor = []

    def stickBossToFloor(self):
        self.unstickBoss()
        self.ray1 = CollisionRay(0.0, 10.0, 20.0, 0.0, 0.0, -1.0)
        self.ray2 = CollisionRay(0.0, 0.0, 20.0, 0.0, 0.0, -1.0)
        self.ray3 = CollisionRay(0.0, -10.0, 20.0, 0.0, 0.0, -1.0)
        rayNode = CollisionNode('stickBossToFloor')
        rayNode.addSolid(self.ray1)
        rayNode.addSolid(self.ray2)
        rayNode.addSolid(self.ray3)
        rayNode.setFromCollideMask(ToontownGlobals.FloorBitmask)
        rayNode.setIntoCollideMask(BitMask32.allOff())
        self.rays = self.attachNewNode(rayNode)
        self.cqueue = CollisionHandlerQueue()
        base.cTrav.addCollider(self.rays, self.cqueue)

    def rollBoss(self, t, fromPos, deltaPos):
        self.setPos(fromPos + deltaPos * t)
        if not self.cqueue:
            return
        self.cqueue.sortEntries()
        numEntries = self.cqueue.getNumEntries()
        if numEntries != 0:
            for i in range(self.cqueue.getNumEntries() - 1, -1, -1):
                entry = self.cqueue.getEntry(i)
                solid = entry.getFrom()
                if solid == self.ray1:
                    self.e1 = entry
                elif solid == self.ray2:
                    self.e2 = entry
                elif solid == self.ray3:
                    self.e3 = entry
                else:
                    self.notify.warning('Unexpected ray in __liftBoss')
                    return

            self.cqueue.clearEntries()
        if not (self.e1 and self.e2 and self.e3):
            self.notify.debug('Some points missed in __liftBoss')
            return
        p1 = self.e1.getSurfacePoint(self)
        p2 = self.e2.getSurfacePoint(self)
        p3 = self.e3.getSurfacePoint(self)
        p2a = (p1 + p3) / 2
        if p2a[2] > p2[2]:
            center = p2a
        else:
            center = p2
        self.setZ(self, center[2])
        if p1[2] > p2[2] + 0.01 or p3[2] > p2[2] + 0.01:
            mat = Mat4(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            if abs(p3[2] - center[2]) < abs(p1[2] - center[2]):
                lookAt(mat, Vec3(p1 - center), CSDefault)
            else:
                lookAt(mat, Vec3(center - p3), CSDefault)
            self.rotateNode.setMat(mat)
        else:
            self.rotateNode.clearTransform()

    def unstickBoss(self):
        if self.rays:
            base.cTrav.removeCollider(self.rays)
            self.rays.removeNode()
        self.rays = None
        self.ray1 = None
        self.ray2 = None
        self.ray3 = None
        self.e1 = None
        self.e2 = None
        self.e3 = None
        self.rotateNode.clearTransform()
        self.cqueue = None
        return

    def rollBossToPoint(self, fromPos, fromHpr, toPos, toHpr, reverse):
        vector = Vec3(toPos - fromPos)
        distance = vector.length()
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
        turnTime = abs(toHpr[0] - fromHpr[0]) / ToontownGlobals.BossCogTurnSpeed
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
        track = Sequence(Func(self.setPos, fromPos), Func(self.headsUp, toPos), Parallel(self.hprInterval(turnTime, toHpr, fromHpr), self.rollLeftTreads(turnTime, leftRate), self.rollRightTreads(turnTime, -leftRate)), Parallel(LerpFunctionInterval(self.rollBoss, duration=rollTime, extraArgs=[fromPos, deltaPos]), self.rollLeftTreads(rollTime, rollTreadRate), self.rollRightTreads(rollTime, rollTreadRate)))
        return (track, toHpr)

    def setupElevator(self, elevatorModel):
        self.elevatorModel = elevatorModel
        self.leftDoor = self.elevatorModel.find('**/left-door')
        if self.leftDoor.isEmpty():
            self.leftDoor = self.elevatorModel.find('**/left_door')
        self.rightDoor = self.elevatorModel.find('**/right-door')
        if self.rightDoor.isEmpty():
            self.rightDoor = self.elevatorModel.find('**/right_door')
        self.openSfx = base.loadSfx('phase_9/audio/sfx/CHQ_FACT_door_open_sliding.mp3')
        self.finalOpenSfx = base.loadSfx('phase_9/audio/sfx/CHQ_FACT_door_open_final.mp3')
        self.closeSfx = base.loadSfx('phase_9/audio/sfx/CHQ_FACT_door_open_sliding.mp3')
        self.finalCloseSfx = base.loadSfx('phase_9/audio/sfx/CHQ_FACT_door_open_final.mp3')
        self.openDoors = ElevatorUtils.getOpenInterval(self, self.leftDoor, self.rightDoor, self.openSfx, self.finalOpenSfx, self.elevatorType)
        self.closeDoors = ElevatorUtils.getCloseInterval(self, self.leftDoor, self.rightDoor, self.closeSfx, self.finalCloseSfx, self.elevatorType)
        self.closeDoors.start()
        self.closeDoors.finish()

    def putToonInCogSuit(self, toon):
        if not toon.isDisguised:
            deptIndex = SuitDNA.suitDepts.index(self.style.dept)
            toon.setCogIndex(deptIndex)
        toon.getGeomNode().hide()

    def placeToonInElevator(self, toon):
        self.putToonInCogSuit(toon)
        toonIndex = self.involvedToons.index(toon.doId)
        toon.reparentTo(self.elevatorModel)
        toon.setPos(*ElevatorConstants.BigElevatorPoints[toonIndex])
        toon.setHpr(180, 0, 0)
        toon.suit.loop('neutral')

    def toonNormalEyes(self, toons, bArrayOfObjs = False):
        if bArrayOfObjs:
            toonObjs = toons
        else:
            toonObjs = []
            for toonId in toons:
                toon = base.cr.doId2do.get(toonId)
                if toon:
                    toonObjs.append(toon)

        seq = Sequence()
        for toon in toonObjs:
            seq.append(Func(toon.normalEyes))
            seq.append(Func(toon.blinkEyes))

        return seq

    def toonDied(self, avId):
        if avId == localAvatar.doId:
            self.localToonDied()

    def localToonToSafeZone(self):
        target_sz = ZoneUtil.getSafeZoneId(localAvatar.defaultZone)
        place = self.cr.playGame.getPlace()
        place.fsm.request('teleportOut', [{'loader': ZoneUtil.getLoaderName(target_sz),
          'where': ZoneUtil.getWhereName(target_sz, 1),
          'how': 'teleportIn',
          'hoodId': target_sz,
          'zoneId': target_sz,
          'shardId': None,
          'avId': -1,
          'battle': 1}])
        return

    def localToonDied(self):
        target_sz = ZoneUtil.getSafeZoneId(localAvatar.defaultZone)
        place = self.cr.playGame.getPlace()
        place.fsm.request('died', [{'loader': ZoneUtil.getLoaderName(target_sz),
          'where': ZoneUtil.getWhereName(target_sz, 1),
          'how': 'teleportIn',
          'hoodId': target_sz,
          'zoneId': target_sz,
          'shardId': None,
          'avId': -1,
          'battle': 1}])
        return

    def toonsToBattlePosition(self, toonIds, battleNode):
        points = BattleBase.BattleBase.toonPoints[len(toonIds) - 1]
        self.notify.debug('toonsToBattlePosition: points = %s' % points[0][0])
        for i in range(len(toonIds)):
            toon = base.cr.doId2do.get(toonIds[i])
            if toon:
                toon.reparentTo(render)
                pos, h = points[i]
                self.notify.debug('toonsToBattlePosition: battleNode=%s %.2f %.2f %.2f %.2f %.2f %.2f' % (battleNode,
                 pos[0],
                 pos[1],
                 pos[2],
                 h,
                 0,
                 0))
                self.notify.debug('old toon pos %s' % toon.getPos())
                self.notify.debug('pos=%.2f %.2f %.2f h=%.2f' % (pos[0],
                 pos[1],
                 pos[2],
                 h))
                self.notify.debug('battleNode.pos = %s' % battleNode.getPos())
                self.notify.debug('battleNode.hpr = %s' % battleNode.getHpr())
                toon.setPosHpr(battleNode, pos[0], pos[1], pos[2], h, 0, 0)
                self.notify.debug('new toon pos %s ' % toon.getPos())

    def __touchedBoss(self, entry):
        self.notify.debug('%s' % entry)
        self.notify.debug('fromPos = %s' % entry.getFromNodePath().getPos(render))
        self.notify.debug('intoPos = %s' % entry.getIntoNodePath().getPos(render))
        attackCodeStr = entry.getIntoNodePath().getNetTag('attackCode')
        if attackCodeStr == '':
            self.notify.warning('Node %s has no attackCode tag.' % repr(entry.getIntoNodePath()))
            return
        attackCode = int(attackCodeStr)
        if attackCode == ToontownGlobals.BossCogLawyerAttack and self.dna.dept != 'l':
            self.notify.warning('got lawyer attack but not in CJ boss battle')
            return
        self.zapLocalToon(attackCode)

    def zapLocalToon(self, attackCode, origin = None):
        if self.localToonIsSafe or localAvatar.ghostMode or localAvatar.isStunned:
            return
        messenger.send('interrupt-pie')
        place = self.cr.playGame.getPlace()
        currentState = None
        if place:
            currentState = place.fsm.getCurrentState().getName()
        if currentState != 'walk' and currentState != 'finalBattle' and currentState != 'crane':
            return
        toon = localAvatar
        fling = 1
        shake = 0
        if attackCode == ToontownGlobals.BossCogAreaAttack:
            fling = 0
            shake = 1
        if fling:
            if origin == None:
                origin = self
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
         hpr[0] % 360.0,
         hpr[1],
         hpr[2],
         bp2d[0],
         bp2d[1],
         attackCode,
         timestamp])
        self.doZapToon(toon, fling=fling, shake=shake)
        return

    def showZapToon(self, toonId, x, y, z, h, p, r, attackCode, timestamp):
        if toonId == localAvatar.doId:
            return
        ts = globalClockDelta.localElapsedTime(timestamp)
        pos = Point3(x, y, z)
        hpr = VBase3(h, p, r)
        fling = 1
        toon = self.cr.doId2do.get(toonId)
        if toon:
            if attackCode == ToontownGlobals.BossCogAreaAttack:
                pos = None
                hpr = None
                fling = 0
            else:
                ts -= toon.smoother.getDelay()
            self.doZapToon(toon, pos=pos, hpr=hpr, ts=ts, fling=fling)
        return

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
            toonTrack += [ActorInterval(toon, 'slip-backward'), toon.posInterval(0.5, getSlideToPos, fluid=1)]
        else:
            toonTrack += [ActorInterval(toon, 'slip-forward')]
        zapTrack.append(toonTrack)
        if toon == localAvatar:
            zapTrack.append(Func(self.disableLocalToonSimpleCollisions))
            currentState = self.state
            if currentState == 'BattleThree':
                zapTrack.append(Func(self.toFinalBattleMode))
            elif hasattr(self, 'chairs'):
                zapTrack.append(Func(self.toFinalBattleMode))
            else:
                zapTrack.append(Func(self.toWalkMode))
        else:
            zapTrack.append(Func(toon.startSmooth))
        if ts > 0:
            startTime = ts
        else:
            zapTrack = Sequence(Wait(-ts), zapTrack)
            startTime = 0
        zapTrack.append(Func(self.clearInterval, zapName))
        zapTrack.delayDelete = DelayDelete.DelayDelete(toon, 'BossCog.doZapToon')
        zapTrack.start(startTime)
        self.storeInterval(zapTrack, zapName)
        return

    def setAttackCode(self, attackCode, avId = 0):
        self.attackCode = attackCode
        self.attackAvId = avId
        if attackCode == ToontownGlobals.BossCogDizzy:
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
        elif attackCode == ToontownGlobals.BossCogDirectedAttack or attackCode == ToontownGlobals.BossCogSlowDirectedAttack:
            self.setDizzy(0)
            self.doDirectedAttack(avId, attackCode)
        elif attackCode == ToontownGlobals.BossCogNoAttack:
            self.setDizzy(0)
            self.doAnimate(None, raised=1)
        return

    def cleanupAttacks(self):
        pass

    def cleanupFlash(self):
        if self.flashInterval:
            self.flashInterval.finish()
            self.flashInterval = None
        return

    def flashRed(self):
        self.cleanupFlash()
        self.setColorScale(1, 1, 1, 1)
        i = Sequence(self.colorScaleInterval(0.1, colorScale=VBase4(1, 0, 0, 1)), self.colorScaleInterval(0.3, colorScale=VBase4(1, 1, 1, 1)))
        self.flashInterval = i
        i.start()

    def flashGreen(self):
        self.cleanupFlash()
        if not self.isEmpty():
            self.setColorScale(1, 1, 1, 1)
            i = Sequence(self.colorScaleInterval(0.1, colorScale=VBase4(0, 1, 0, 1)), self.colorScaleInterval(0.3, colorScale=VBase4(1, 1, 1, 1)))
            self.flashInterval = i
            i.start()

    def getGearFrisbee(self):
        return loader.loadModel('phase_9/models/char/gearProp')

    def backupToonsToBattlePosition(self, toonIds, battleNode):
        self.notify.debug('backupToonsToBattlePosition:')
        ival = Parallel()
        points = BattleBase.BattleBase.toonPoints[len(toonIds) - 1]
        for i in range(len(toonIds)):
            toon = base.cr.doId2do.get(toonIds[i])
            if toon:
                pos, h = points[i]
                pos = render.getRelativePoint(battleNode, pos)
                ival.append(Sequence(Func(toon.setPlayRate, -0.8, 'walk'), Func(toon.loop, 'walk'), toon.posInterval(3, pos), Func(toon.setPlayRate, 1, 'walk'), Func(toon.loop, 'neutral')))

        return ival

    def loseCogSuits(self, toons, battleNode, camLoc, arrayOfObjs = False):
        seq = Sequence()
        if not toons:
            return seq
        self.notify.debug('battleNode=%s camLoc=%s' % (battleNode, camLoc))
        seq.append(Func(camera.setPosHpr, battleNode, *camLoc))
        suitsOff = Parallel()
        if arrayOfObjs:
            toonArray = toons
        else:
            toonArray = []
            for toonId in toons:
                toon = base.cr.doId2do.get(toonId)
                if toon:
                    toonArray.append(toon)

        for toon in toonArray:
            dustCloud = DustCloud.DustCloud()
            dustCloud.setPos(0, 2, 3)
            dustCloud.setScale(0.5)
            dustCloud.setDepthWrite(0)
            dustCloud.setBin('fixed', 0)
            dustCloud.createTrack()
            suitsOff.append(Sequence(Func(dustCloud.reparentTo, toon), Parallel(dustCloud.track, Sequence(Wait(0.3), Func(toon.takeOffSuit), Func(toon.sadEyes), Func(toon.blinkEyes), Func(toon.play, 'slip-backward'), Wait(0.7))), Func(dustCloud.detachNode), Func(dustCloud.destroy)))

        seq.append(suitsOff)
        return seq

    def doDirectedAttack(self, avId, attackCode):
        toon = base.cr.doId2do.get(avId)
        if toon:
            gearRoot = self.rotateNode.attachNewNode('gearRoot')
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
                node = gearRoot.attachNewNode(str(i))
                node.hide()
                node.setPos(0, 5.85, 4.0)
                gear = gearModel.instanceTo(node)
                x = random.uniform(-5, 5)
                z = random.uniform(-3, 3)
                h = random.uniform(-720, 720)
                gearTrack.append(Sequence(Wait(i * 0.15), Func(node.show), Parallel(node.posInterval(1, Point3(x, 50, z), fluid=1), node.hprInterval(1, VBase3(h, 0, 0), fluid=1)), Func(node.detachNode)))

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
            seq = Sequence(ParallelEndTogether(self.pelvis.hprInterval(1, VBase3(toToonH, 0, 0)), neutral1Anim), extraAnim, Parallel(Sequence(Wait(0.19), gearTrack, Func(gearRoot.detachNode), self.pelvis.hprInterval(0.2, VBase3(0, 0, 0))), Sequence(throwAnim, neutral2Anim)))
            self.doAnimate(seq, now=1, raised=1)

    def announceAreaAttack(self):
        if not getattr(localAvatar.controlManager.currentControls, 'isAirborne', 0):
            self.zapLocalToon(ToontownGlobals.BossCogAreaAttack)

    def loadEnvironment(self):
        self.elevatorMusic = base.loadMusic('phase_7/audio/bgm/tt_elevator.mid')
        self.stingMusic = base.loadMusic('phase_7/audio/bgm/encntr_suit_winning_indoor.mid')
        self.battleOneMusic = base.loadMusic('phase_3.5/audio/bgm/encntr_general_bg.mid')
        self.battleThreeMusic = base.loadMusic('phase_7/audio/bgm/encntr_suit_winning_indoor.mid')
        self.epilogueMusic = base.loadMusic('phase_9/audio/bgm/encntr_hall_of_fame.mid')

    def unloadEnvironment(self):
        pass

    def enterOff(self):
        self.cleanupIntervals()
        self.hide()
        self.clearChat()
        self.toWalkMode()

    def exitOff(self):
        self.show()

    def enterWaitForToons(self):
        self.cleanupIntervals()
        self.hide()
        if self.gotAllToons:
            self.__doneWaitForToons()
        else:
            self.accept('gotAllToons', self.__doneWaitForToons)
        self.transitions = Transitions.Transitions(loader)
        self.transitions.IrisModelName = 'phase_3/models/misc/iris'
        self.transitions.FadeModelName = 'phase_3/models/misc/fade'
        self.transitions.fadeScreen(alpha=1)
        NametagGlobals.setMasterArrowsOn(0)

    def __doneWaitForToons(self):
        self.doneBarrier('WaitForToons')

    def exitWaitForToons(self):
        self.show()
        self.transitions.noFade()
        del self.transitions
        NametagGlobals.setMasterArrowsOn(1)

    def enterElevator(self):
        for toonId in self.involvedToons:
            toon = self.cr.doId2do.get(toonId)
            if toon:
                toon.stopLookAround()
                toon.stopSmooth()
                self.placeToonInElevator(toon)

        self.toMovieMode()
        camera.reparentTo(self.elevatorModel)
        camera.setPosHpr(0, 30, 8, 180, 0, 0)
        base.playMusic(self.elevatorMusic, looping=1, volume=1.0)
        ival = Sequence(ElevatorUtils.getRideElevatorInterval(self.elevatorType), ElevatorUtils.getRideElevatorInterval(self.elevatorType), self.openDoors, Func(camera.wrtReparentTo, render), Func(self.__doneElevator))
        intervalName = 'ElevatorMovie'
        ival.start()
        self.storeInterval(ival, intervalName)

    def __doneElevator(self):
        self.doneBarrier('Elevator')

    def exitElevator(self):
        intervalName = 'ElevatorMovie'
        self.clearInterval(intervalName)
        self.elevatorMusic.stop()
        ElevatorUtils.closeDoors(self.leftDoor, self.rightDoor, self.elevatorType)

    def enterIntroduction(self):
        self.controlToons()
        ElevatorUtils.openDoors(self.leftDoor, self.rightDoor, self.elevatorType)
        NametagGlobals.setMasterArrowsOn(0)
        intervalName = 'IntroductionMovie'
        delayDeletes = []
        seq = Sequence(self.makeIntroductionMovie(delayDeletes), Func(self.__beginBattleOne), name=intervalName)
        seq.delayDeletes = delayDeletes
        seq.start()
        self.storeInterval(seq, intervalName)

    def __beginBattleOne(self):
        intervalName = 'IntroductionMovie'
        self.clearInterval(intervalName)
        self.doneBarrier('Introduction')

    def exitIntroduction(self):
        self.notify.debug('DistributedBossCog.exitIntroduction:')
        intervalName = 'IntroductionMovie'
        self.clearInterval(intervalName)
        self.unstickToons()
        self.releaseToons()
        NametagGlobals.setMasterArrowsOn(1)
        ElevatorUtils.closeDoors(self.leftDoor, self.rightDoor, self.elevatorType)

    def enterBattleOne(self):
        self.cleanupIntervals()
        mult = ToontownBattleGlobals.getBossBattleCreditMultiplier(1)
        localAvatar.inventory.setBattleCreditMultiplier(mult)
        self.toonsToBattlePosition(self.toonsA, self.battleANode)
        self.toonsToBattlePosition(self.toonsB, self.battleBNode)
        self.releaseToons()
        base.playMusic(self.battleOneMusic, looping=1, volume=0.9)

    def exitBattleOne(self):
        self.cleanupBattles()
        self.battleOneMusic.stop()
        localAvatar.inventory.setBattleCreditMultiplier(1)

    def enterBattleThree(self):
        self.cleanupIntervals()
        self.releaseToons(finalBattle=1)
        self.accept('clickedNametag', self.__clickedNameTag)
        self.accept('friendAvatar', self.__handleFriendAvatar)
        self.accept('avatarDetails', self.__handleAvatarDetails)
        NametagGlobals.setMasterArrowsOn(0)
        NametagGlobals.setMasterNametagsActive(1)

    def exitBattleThree(self):
        self.ignore('clickedNameTag')
        self.ignore('friendAvatar')
        self.ignore('avatarDetails')
        self.cleanupIntervals()

    def __clickedNameTag(self, avatar):
        self.notify.debug('__clickedNameTag')
        if not (self.state == 'BattleThree' or self.state == 'BattleFour'):
            return
        if not self.allowClickedNameTag:
            return
        if self.cr:
            place = self.cr.playGame.getPlace()
            if place and hasattr(place, 'fsm'):
                FriendsListManager.FriendsListManager._FriendsListManager__handleClickedNametag(place, avatar)

    def __handleFriendAvatar(self, avId, avName, avDisableName):
        self.notify.debug('__handleFriendAvatar')
        if not (self.state == 'BattleThree' or self.state == 'BattleFour'):
            return
        if not self.allowClickedNameTag:
            return
        if self.cr:
            place = self.cr.playGame.getPlace()
            if place and hasattr(place, 'fsm'):
                FriendsListManager.FriendsListManager._FriendsListManager__handleFriendAvatar(place, avId, avName, avDisableName)

    def __handleAvatarDetails(self, avId, avName, playerId = None):
        self.notify.debug('__handleAvatarDetails')
        if not (self.state == 'BattleThree' or self.state == 'BattleFour'):
            return
        if not self.allowClickedNameTag:
            return
        if self.cr:
            place = self.cr.playGame.getPlace()
            if place and hasattr(place, 'fsm'):
                FriendsListManager.FriendsListManager._FriendsListManager__handleAvatarDetails(place, avId, avName, playerId)

    def enterBattleFour(self):
        self.cleanupIntervals()
        self.releaseToons(finalBattle=1)
        self.accept('clickedNametag', self.__clickedNameTag)
        self.accept('friendAvatar', self.__handleFriendAvatar)
        self.accept('avatarDetails', self.__handleAvatarDetails)
        NametagGlobals.setMasterArrowsOn(0)
        NametagGlobals.setMasterNametagsActive(1)

    def exitBattleFour(self):
        self.ignore('clickedNameTag')
        self.ignore('friendAvatar')
        self.ignore('avatarDetails')
        self.cleanupIntervals()

    def enterFrolic(self):
        self.cleanupIntervals()
        self.clearChat()
        self.reparentTo(render)
        self.stopAnimate()
        self.pose('Ff_neutral', 0)
        self.releaseToons()

    def exitFrolic(self):
        pass

    def setToonsToNeutral(self, toonIds):
        for i in range(len(toonIds)):
            toon = base.cr.doId2do.get(toonIds[i])
            if toon:
                if toon.isDisguised:
                    toon.suit.loop('neutral')
                toon.loop('neutral')

    def wearCogSuits(self, toons, battleNode, camLoc, arrayOfObjs = False, waiter = False):
        seq = Sequence()
        if not toons:
            return seq
        self.notify.debug('battleNode=%s camLoc=%s' % (battleNode, camLoc))
        if camLoc:
            seq.append(Func(camera.setPosHpr, battleNode, *camLoc))
        suitsOff = Parallel()
        if arrayOfObjs:
            toonArray = toons
        else:
            toonArray = []
            for toonId in toons:
                toon = base.cr.doId2do.get(toonId)
                if toon:
                    toonArray.append(toon)

        for toon in toonArray:
            dustCloud = DustCloud.DustCloud()
            dustCloud.setPos(0, 2, 3)
            dustCloud.setScale(0.5)
            dustCloud.setDepthWrite(0)
            dustCloud.setBin('fixed', 0)
            dustCloud.createTrack()
            makeWaiter = Sequence()
            if waiter:
                makeWaiter = Func(toon.makeWaiter)
            suitsOff.append(Sequence(Func(dustCloud.reparentTo, toon), Parallel(dustCloud.track, Sequence(Wait(0.3), Func(self.putToonInCogSuit, toon), makeWaiter, Wait(0.7))), Func(dustCloud.detachNode)))

        seq.append(suitsOff)
        return seq
