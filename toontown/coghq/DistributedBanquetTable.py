import math
import random
from pandac.PandaModules import NodePath, Point3, VBase4, TextNode, Vec3, deg2Rad, CollisionSegment, CollisionHandlerQueue, CollisionNode, BitMask32, SmoothMover
from direct.fsm import FSM
from direct.distributed import DistributedObject
from direct.distributed.ClockDelta import globalClockDelta
from direct.directnotify import DirectNotifyGlobal
from direct.interval.IntervalGlobal import Sequence, ProjectileInterval, Parallel, LerpHprInterval, ActorInterval, Func, Wait, SoundInterval, LerpPosHprInterval, LerpScaleInterval
from direct.gui.DirectGui import DGG, DirectButton, DirectLabel, DirectWaitBar
from direct.task import Task
from toontown.suit import Suit
from toontown.suit import SuitDNA
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from toontown.coghq import BanquetTableBase
from toontown.coghq import DinerStatusIndicator
from toontown.battle import MovieUtil

class DistributedBanquetTable(DistributedObject.DistributedObject, FSM.FSM, BanquetTableBase.BanquetTableBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedBanquetTable')
    rotationsPerSeatIndex = [90,
     90,
     0,
     0,
     -90,
     -90,
     180,
     180]
    pitcherMinH = -360
    pitcherMaxH = 360
    rotateSpeed = 30
    waterPowerSpeed = base.config.GetDouble('water-power-speed', 15)
    waterPowerExponent = base.config.GetDouble('water-power-exponent', 0.75)
    useNewAnimations = True
    TugOfWarControls = False
    OnlyUpArrow = True
    if OnlyUpArrow:
        BASELINE_KEY_RATE = 3
    else:
        BASELINE_KEY_RATE = 6
    UPDATE_KEY_PRESS_RATE_TASK = 'BanquetTableUpdateKeyPressRateTask'
    YELLOW_POWER_THRESHOLD = 0.75
    RED_POWER_THRESHOLD = 0.97

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        FSM.FSM.__init__(self, 'DistributedBanquetTable')
        self.boss = None
        self.index = -1
        self.diners = {}
        self.dinerStatus = {}
        self.serviceLocs = {}
        self.chairLocators = {}
        self.sitLocators = {}
        self.activeIntervals = {}
        self.dinerStatusIndicators = {}
        self.preparedForPhaseFour = False
        self.avId = 0
        self.toon = None
        self.pitcherSmoother = SmoothMover()
        self.pitcherSmoother.setSmoothMode(SmoothMover.SMOn)
        self.smoothStarted = 0
        self.__broadcastPeriod = 0.2
        self.changeSeq = 0
        self.lastChangeSeq = 0
        self.pitcherAdviceLabel = None
        self.fireLength = 250
        self.fireTrack = None
        self.hitObject = None
        self.setupPowerBar()
        self.aimStart = None
        self.toonPitcherPosition = Point3(0, -2, 0)
        self.allowLocalRequestControl = True
        self.fadeTrack = None
        self.grabTrack = None
        self.gotHitByBoss = False
        self.keyTTL = []
        self.keyRate = 0
        self.buttons = [0, 1]
        self.lastPowerFired = 0
        self.moveSound = None
        self.releaseTrack = None
        return

    def disable(self):
        DistributedObject.DistributedObject.disable(self)
        taskMgr.remove(self.triggerName)
        taskMgr.remove(self.smoothName)
        taskMgr.remove(self.watchControlsName)
        taskMgr.remove(self.pitcherAdviceName)
        taskMgr.remove(self.posHprBroadcastName)
        taskMgr.remove(self.waterPowerTaskName)
        if self.releaseTrack:
            self.releaseTrack.finish()
            self.releaseTrack = None
        if self.fireTrack:
            self.fireTrack.finish()
            self.fireTrack = None
        self.cleanupIntervals()
        return

    def delete(self):
        DistributedObject.DistributedObject.delete(self)
        self.boss = None
        self.ignoreAll()
        for indicator in self.dinerStatusIndicators.values():
            indicator.delete()

        self.dinerStatusIndicators = {}
        for diner in self.diners.values():
            diner.delete()

        self.diners = {}
        self.powerBar.destroy()
        self.powerBar = None
        self.pitcherMoveSfx.stop()
        return

    def announceGenerate(self):
        DistributedObject.DistributedObject.announceGenerate(self)
        self.loadAssets()
        self.smoothName = self.uniqueName('pitcherSmooth')
        self.pitcherAdviceName = self.uniqueName('pitcherAdvice')
        self.posHprBroadcastName = self.uniqueName('pitcherBroadcast')
        self.waterPowerTaskName = self.uniqueName('updateWaterPower')
        self.triggerName = self.uniqueName('trigger')
        self.watchControlsName = self.uniqueName('watchControls')

    def setBossCogId(self, bossCogId):
        self.bossCogId = bossCogId
        self.boss = base.cr.doId2do[bossCogId]
        self.boss.setTable(self, self.index)

    def setIndex(self, index):
        self.index = index

    def setState(self, state, avId, extraInfo):
        self.gotHitByBoss = extraInfo
        if state == 'F':
            self.demand('Off')
        elif state == 'N':
            self.demand('On')
        elif state == 'I':
            self.demand('Inactive')
        elif state == 'R':
            self.demand('Free')
        elif state == 'C':
            self.demand('Controlled', avId)
        elif state == 'L':
            self.demand('Flat', avId)
        else:
            self.notify.error('Invalid state from AI: %s' % state)

    def setNumDiners(self, numDiners):
        self.numDiners = numDiners

    def setDinerInfo(self, hungryDurations, eatingDurations, dinerLevels):
        self.dinerInfo = {}
        for i in xrange(len(hungryDurations)):
            hungryDur = hungryDurations[i]
            eatingDur = eatingDurations[i]
            dinerLevel = dinerLevels[i]
            self.dinerInfo[i] = (hungryDur, eatingDur, dinerLevel)

    def loadAssets(self):
        self.tableGroup = loader.loadModel('phase_12/models/bossbotHQ/BanquetTableChairs')
        tableLocator = self.boss.geom.find('**/TableLocator_%d' % (self.index + 1))
        if tableLocator.isEmpty():
            self.tableGroup.reparentTo(render)
            self.tableGroup.setPos(0, 75, 0)
        else:
            self.tableGroup.reparentTo(tableLocator)
        self.tableGeom = self.tableGroup.find('**/Geometry')
        self.setupDiners()
        self.setupChairCols()
        self.squirtSfx = loader.loadSfx('phase_4/audio/sfx/AA_squirt_seltzer_miss.mp3')
        self.hitBossSfx = loader.loadSfx('phase_5/audio/sfx/SA_watercooler_spray_only.mp3')
        self.hitBossSoundInterval = SoundInterval(self.hitBossSfx, node=self.boss, volume=1.0)
        self.serveFoodSfx = loader.loadSfx('phase_4/audio/sfx/MG_sfx_travel_game_bell_for_trolley.mp3')
        self.pitcherMoveSfx = base.loadSfx('phase_4/audio/sfx/MG_cannon_adjust.mp3')

    def setupDiners(self):
        for i in xrange(self.numDiners):
            newDiner = self.createDiner(i)
            self.diners[i] = newDiner
            self.dinerStatus[i] = self.HUNGRY

    def createDiner(self, i):
        diner = Suit.Suit()
        diner.dna = SuitDNA.SuitDNA()
        level = self.dinerInfo[i][2]
        level -= 4
        diner.dna.newSuitRandom(level=level, dept='c')
        diner.setDNA(diner.dna)
        if self.useNewAnimations:
            diner.loop('sit', fromFrame=i)
        else:
            diner.pose('landing', 0)
        locator = self.tableGroup.find('**/chair_%d' % (i + 1))
        locatorScale = locator.getNetTransform().getScale()[0]
        correctHeadingNp = locator.attachNewNode('correctHeading')
        self.chairLocators[i] = correctHeadingNp
        heading = self.rotationsPerSeatIndex[i]
        correctHeadingNp.setH(heading)
        sitLocator = correctHeadingNp.attachNewNode('sitLocator')
        base.sitLocator = sitLocator
        pos = correctHeadingNp.getPos(render)
        if SuitDNA.getSuitBodyType(diner.dna.name) == 'c':
            sitLocator.setPos(0.5, 3.65, -3.75)
        else:
            sitLocator.setZ(-2.4)
            sitLocator.setY(2.5)
            sitLocator.setX(0.5)
        self.sitLocators[i] = sitLocator
        diner.setScale(1.0 / locatorScale)
        diner.reparentTo(sitLocator)
        newLoc = NodePath('serviceLoc-%d-%d' % (self.index, i))
        newLoc.reparentTo(correctHeadingNp)
        newLoc.setPos(0, 3.0, 1)
        self.serviceLocs[i] = newLoc
        base.serviceLoc = newLoc
        head = diner.find('**/joint_head')
        newIndicator = DinerStatusIndicator.DinerStatusIndicator(parent=head, pos=Point3(0, 0, 3.5), scale=5.0)
        newIndicator.wrtReparentTo(diner)
        self.dinerStatusIndicators[i] = newIndicator
        return diner

    def setupChairCols(self):
        for i in xrange(self.numDiners):
            chairCol = self.tableGroup.find('**/collision_chair_%d' % (i + 1))
            colName = 'ChairCol-%d-%d' % (self.index, i)
            chairCol.setTag('chairIndex', str(i))
            chairCol.setName(colName)
            chairCol.setCollideMask(ToontownGlobals.WallBitmask)
            self.accept('enter' + colName, self.touchedChair)

    def touchedChair(self, colEntry):
        chairIndex = int(colEntry.getIntoNodePath().getTag('chairIndex'))
        if chairIndex in self.dinerStatus:
            status = self.dinerStatus[chairIndex]
            if status in (self.HUNGRY, self.ANGRY):
                self.boss.localToonTouchedChair(self.index, chairIndex)

    def serveFood(self, food, chairIndex):
        self.removeFoodModel(chairIndex)
        serviceLoc = self.serviceLocs.get(chairIndex)
        if not food or food.isEmpty():
            foodModel = loader.loadModel('phase_12/models/bossbotHQ/canoffood')
            foodModel.setScale(ToontownGlobals.BossbotFoodModelScale)
            foodModel.reparentTo(serviceLoc)
        else:
            food.wrtReparentTo(serviceLoc)
            tray = food.find('**/tray')
            if not tray.isEmpty():
                tray.hide()
            ivalDuration = 1.5
            foodMoveIval = Parallel(SoundInterval(self.serveFoodSfx, node=food), ProjectileInterval(food, duration=ivalDuration, startPos=food.getPos(serviceLoc), endPos=serviceLoc.getPos(serviceLoc)), LerpHprInterval(food, ivalDuration, Point3(0, -360, 0)))
            intervalName = 'serveFood-%d-%d' % (self.index, chairIndex)
            foodMoveIval.start()
            self.activeIntervals[intervalName] = foodMoveIval

    def setDinerStatus(self, chairIndex, status):
        if chairIndex in self.dinerStatus:
            oldStatus = self.dinerStatus[chairIndex]
            self.dinerStatus[chairIndex] = status
            if oldStatus != status:
                if status == self.EATING:
                    self.changeDinerToEating(chairIndex)
                elif status == self.HUNGRY:
                    self.changeDinerToHungry(chairIndex)
                elif status == self.ANGRY:
                    self.changeDinerToAngry(chairIndex)
                elif status == self.DEAD:
                    self.changeDinerToDead(chairIndex)
                elif status == self.HIDDEN:
                    self.changeDinerToHidden(chairIndex)

    def removeFoodModel(self, chairIndex):
        serviceLoc = self.serviceLocs.get(chairIndex)
        if serviceLoc:
            for i in xrange(serviceLoc.getNumChildren()):
                serviceLoc.getChild(0).removeNode()

    def changeDinerToEating(self, chairIndex):
        indicator = self.dinerStatusIndicators.get(chairIndex)
        eatingDuration = self.dinerInfo[chairIndex][1]
        if indicator:
            indicator.request('Eating', eatingDuration)
        diner = self.diners[chairIndex]
        intervalName = 'eating-%d-%d' % (self.index, chairIndex)
        eatInTime = 32.0 / 24.0
        eatOutTime = 21.0 / 24.0
        eatLoopTime = 19 / 24.0
        rightHand = diner.getRightHand()
        waitTime = 5
        loopDuration = eatingDuration - eatInTime - eatOutTime - waitTime
        serviceLoc = self.serviceLocs[chairIndex]

        def foodAttach(self = self, diner = diner):
            foodModel = self.serviceLocs[chairIndex].getChild(0)
            (foodModel.reparentTo(diner.getRightHand()),)
            (foodModel.setHpr(Point3(0, -94, 0)),)
            (foodModel.setPos(Point3(-0.15, -0.7, -0.4)),)
            scaleAdj = 1
            if SuitDNA.getSuitBodyType(diner.dna.name) == 'c':
                scaleAdj = 0.6
                (foodModel.setPos(Point3(0.1, -0.25, -0.31)),)
            else:
                scaleAdj = 0.8
                (foodModel.setPos(Point3(-0.25, -0.85, -0.34)),)
            oldScale = foodModel.getScale()
            newScale = oldScale * scaleAdj
            foodModel.setScale(newScale)

        def foodDetach(self = self, diner = diner):
            foodModel = diner.getRightHand().getChild(0)
            (foodModel.reparentTo(serviceLoc),)
            (foodModel.setPosHpr(0, 0, 0, 0, 0, 0),)
            scaleAdj = 1
            if SuitDNA.getSuitBodyType(diner.dna.name) == 'c':
                scaleAdj = 0.6
            else:
                scakeAdj = 0.8
            oldScale = foodModel.getScale()
            newScale = oldScale / scaleAdj
            foodModel.setScale(newScale)

        eatIval = Sequence(ActorInterval(diner, 'sit', duration=waitTime), ActorInterval(diner, 'sit-eat-in', startFrame=0, endFrame=6), Func(foodAttach), ActorInterval(diner, 'sit-eat-in', startFrame=6, endFrame=32), ActorInterval(diner, 'sit-eat-loop', duration=loopDuration, loop=1), ActorInterval(diner, 'sit-eat-out', startFrame=0, endFrame=12), Func(foodDetach), ActorInterval(diner, 'sit-eat-out', startFrame=12, endFrame=21))
        eatIval.start()
        self.activeIntervals[intervalName] = eatIval

    def changeDinerToHungry(self, chairIndex):
        intervalName = 'eating-%d-%d' % (self.index, chairIndex)
        if intervalName in self.activeIntervals:
            self.activeIntervals[intervalName].finish()
        self.removeFoodModel(chairIndex)
        indicator = self.dinerStatusIndicators.get(chairIndex)
        if indicator:
            indicator.request('Hungry', self.dinerInfo[chairIndex][0])
        diner = self.diners[chairIndex]
        if random.choice([0, 1]):
            diner.loop('sit-hungry-left')
        else:
            diner.loop('sit-hungry-right')

    def changeDinerToAngry(self, chairIndex):
        self.removeFoodModel(chairIndex)
        indicator = self.dinerStatusIndicators.get(chairIndex)
        if indicator:
            indicator.request('Angry')
        diner = self.diners[chairIndex]
        diner.loop('sit-angry')

    def changeDinerToDead(self, chairIndex):

        def removeDeathSuit(suit, deathSuit):
            if not deathSuit.isEmpty():
                deathSuit.detachNode()
                suit.cleanupLoseActor()

        self.removeFoodModel(chairIndex)
        indicator = self.dinerStatusIndicators.get(chairIndex)
        if indicator:
            indicator.request('Dead')
        diner = self.diners[chairIndex]
        deathSuit = diner
        locator = self.tableGroup.find('**/chair_%d' % (chairIndex + 1))
        deathSuit = diner.getLoseActor()
        ival = Sequence(Func(self.notify.debug, 'before actorinterval sit-lose'), ActorInterval(diner, 'sit-lose'), Func(self.notify.debug, 'before deathSuit.setHpr'), Func(deathSuit.setHpr, diner.getHpr()), Func(self.notify.debug, 'before diner.hide'), Func(diner.hide), Func(self.notify.debug, 'before deathSuit.reparentTo'), Func(deathSuit.reparentTo, self.chairLocators[chairIndex]), Func(self.notify.debug, 'befor ActorInterval lose'), ActorInterval(deathSuit, 'lose', duration=MovieUtil.SUIT_LOSE_DURATION), Func(self.notify.debug, 'before remove deathsuit'), Func(removeDeathSuit, diner, deathSuit, name='remove-death-suit-%d-%d' % (chairIndex, self.index)), Func(self.notify.debug, 'diner.stash'), Func(diner.stash))
        spinningSound = base.loadSfx('phase_3.5/audio/sfx/Cog_Death.mp3')
        deathSound = base.loadSfx('phase_3.5/audio/sfx/ENC_cogfall_apart.mp3')
        deathSoundTrack = Sequence(Wait(0.8), SoundInterval(spinningSound, duration=1.2, startTime=1.5, volume=0.2, node=deathSuit), SoundInterval(spinningSound, duration=3.0, startTime=0.6, volume=0.8, node=deathSuit), SoundInterval(deathSound, volume=0.32, node=deathSuit))
        intervalName = 'dinerDie-%d-%d' % (self.index, chairIndex)
        deathIval = Parallel(ival, deathSoundTrack)
        deathIval.start()
        self.activeIntervals[intervalName] = deathIval

    def changeDinerToHidden(self, chairIndex):
        self.removeFoodModel(chairIndex)
        indicator = self.dinerStatusIndicators.get(chairIndex)
        if indicator:
            indicator.request('Inactive')
        diner = self.diners[chairIndex]
        diner.hide()

    def setAllDinersToSitNeutral(self):
        startFrame = 0
        for diner in self.diners.values():
            if not diner.isHidden():
                diner.loop('sit', fromFrame=startFrame)
                startFrame += 1

    def cleanupIntervals(self):
        for interval in self.activeIntervals.values():
            interval.finish()

        self.activeIntervals = {}

    def clearInterval(self, name, finish = 1):
        if self.activeIntervals.has_key(name):
            ival = self.activeIntervals[name]
            if finish:
                ival.finish()
            else:
                ival.pause()
            if self.activeIntervals.has_key(name):
                del self.activeIntervals[name]
        else:
            self.notify.debug('interval: %s already cleared' % name)

    def finishInterval(self, name):
        if self.activeIntervals.has_key(name):
            interval = self.activeIntervals[name]
            interval.finish()

    def getNotDeadInfo(self):
        notDeadList = []
        for i in xrange(self.numDiners):
            if self.dinerStatus[i] != self.DEAD:
                notDeadList.append((self.index, i, 12))

        return notDeadList

    def enterOn(self):
        pass

    def exitOn(self):
        pass

    def enterInactive(self):
        for chairIndex in xrange(self.numDiners):
            indicator = self.dinerStatusIndicators.get(chairIndex)
            if indicator:
                indicator.request('Inactive')
            self.removeFoodModel(chairIndex)

    def exitInactive(self):
        pass

    def enterFree(self):
        self.resetPowerBar()
        if self.fadeTrack:
            self.fadeTrack.finish()
            self.fadeTrack = None
        self.prepareForPhaseFour()
        if self.avId == localAvatar.doId:
            self.tableGroup.setAlphaScale(0.3)
            self.tableGroup.setTransparency(1)
            taskMgr.doMethodLater(5, self.__allowDetect, self.triggerName)
            self.fadeTrack = Sequence(Func(self.tableGroup.setTransparency, 1), self.tableGroup.colorScaleInterval(0.2, VBase4(1, 1, 1, 0.3)))
            self.fadeTrack.start()
            self.allowLocalRequestControl = False
        else:
            self.allowLocalRequestControl = True
        self.avId = 0
        return

    def exitFree(self):
        pass

    def touchedTable(self, colEntry):
        tableIndex = int(colEntry.getIntoNodePath().getTag('tableIndex'))
        if self.state == 'Free' and self.avId == 0 and self.allowLocalRequestControl:
            self.d_requestControl()

    def prepareForPhaseFour(self):
        if not self.preparedForPhaseFour:
            for i in xrange(8):
                chair = self.tableGroup.find('**/chair_%d' % (i + 1))
                if not chair.isEmpty():
                    chair.hide()
                colChairs = self.tableGroup.findAllMatches('**/ChairCol*')
                for i in xrange(colChairs.getNumPaths()):
                    col = colChairs.getPath(i)
                    col.stash()

                colChairs = self.tableGroup.findAllMatches('**/collision_chair*')
                for i in xrange(colChairs.getNumPaths()):
                    col = colChairs.getPath(i)
                    col.stash()

            tableCol = self.tableGroup.find('**/collision_table')
            colName = 'TableCol-%d' % self.index
            tableCol.setTag('tableIndex', str(self.index))
            tableCol.setName(colName)
            tableCol.setCollideMask(ToontownGlobals.WallBitmask | ToontownGlobals.BanquetTableBitmask)
            self.accept('enter' + colName, self.touchedTable)
            self.preparedForPhaseFour = True
            self.waterPitcherModel = loader.loadModel('phase_12/models/bossbotHQ/tt_m_ara_bhq_seltzerBottle')
            lampNode = self.tableGroup.find('**/lamp_med_5')
            pos = lampNode.getPos(self.tableGroup)
            lampNode.hide()
            bottleLocator = self.tableGroup.find('**/bottle_locator')
            pos = bottleLocator.getPos(self.tableGroup)
            self.waterPitcherNode = self.tableGroup.attachNewNode('pitcherNode')
            self.waterPitcherNode.setPos(pos)
            self.waterPitcherModel.reparentTo(self.waterPitcherNode)
            self.waterPitcherModel.ls()
            self.nozzle = self.waterPitcherModel.find('**/nozzle_tip')
            self.handLocator = self.waterPitcherModel.find('**/hand_locator')
            self.handPos = self.handLocator.getPos()

    def d_requestControl(self):
        self.sendUpdate('requestControl')

    def d_requestFree(self, gotHitByBoss):
        self.sendUpdate('requestFree', [gotHitByBoss])

    def enterControlled(self, avId):
        self.prepareForPhaseFour()
        self.avId = avId
        toon = base.cr.doId2do.get(avId)
        if not toon:
            return
        self.toon = toon
        self.grabTrack = self.makeToonGrabInterval(toon)
        self.notify.debug('grabTrack=%s' % self.grabTrack)
        self.pitcherCamPos = Point3(0, -50, 40)
        self.pitcherCamHpr = Point3(0, -21, 0)
        if avId == localAvatar.doId:
            self.boss.toMovieMode()
            self.__enableControlInterface()
            self.startPosHprBroadcast()
            self.grabTrack = Sequence(self.grabTrack, Func(camera.wrtReparentTo, localAvatar), LerpPosHprInterval(camera, 1, self.pitcherCamPos, self.pitcherCamHpr), Func(self.boss.toCraneMode))
            if self.TugOfWarControls:
                self.__spawnUpdateKeyPressRateTask()
            self.accept('exitCrane', self.gotBossZapped)
        else:
            self.startSmooth()
            toon.stopSmooth()
        self.grabTrack.start()

    def exitControlled(self):
        self.ignore('exitCrane')
        if self.grabTrack:
            self.grabTrack.finish()
            self.grabTrack = None
        nextState = self.getCurrentOrNextState()
        self.notify.debug('nextState=%s' % nextState)
        if nextState == 'Flat':
            place = base.cr.playGame.getPlace()
            self.notify.debug('%s' % place.fsm)
            if self.avId == localAvatar.doId:
                self.__disableControlInterface()
        else:
            if self.toon and not self.toon.isDisabled():
                self.toon.loop('neutral')
                self.toon.startSmooth()
            self.releaseTrack = self.makeToonReleaseInterval(self.toon)
            self.stopPosHprBroadcast()
            self.stopSmooth()
            if self.avId == localAvatar.doId:
                localAvatar.wrtReparentTo(render)
                self.__disableControlInterface()
                camera.reparentTo(base.localAvatar)
                camera.setPos(base.localAvatar.cameraPositions[0][0])
                camera.setHpr(0, 0, 0)
                self.goToFinalBattle()
                self.safeBossToFinalBattleMode()
            else:
                toon = base.cr.doId2do.get(self.avId)
                if toon:
                    toon.wrtReparentTo(render)
            self.releaseTrack.start()
        return

    def safeBossToFinalBattleMode(self):
        if self.boss:
            self.boss.toFinalBattleMode()

    def goToFinalBattle(self):
        if self.cr:
            place = self.cr.playGame.getPlace()
            if place and hasattr(place, 'fsm'):
                if place.fsm.getCurrentState().getName() == 'crane':
                    place.setState('finalBattle')

    def makeToonGrabInterval(self, toon):
        toon.pose('leverNeutral', 0)
        toon.update()
        rightHandPos = toon.rightHand.getPos(toon)
        self.toonPitcherPosition = Point3(self.handPos[0] - rightHandPos[0], self.handPos[1] - rightHandPos[1], 0)
        destZScale = rightHandPos[2] / self.handPos[2]
        grabIval = Sequence(Func(toon.wrtReparentTo, self.waterPitcherNode), Func(toon.loop, 'neutral'), Parallel(ActorInterval(toon, 'jump'), Sequence(Wait(0.43), Parallel(ProjectileInterval(toon, duration=0.9, startPos=toon.getPos(self.waterPitcherNode), endPos=self.toonPitcherPosition), LerpHprInterval(toon, 0.9, Point3(0, 0, 0)), LerpScaleInterval(self.waterPitcherModel, 0.9, Point3(1, 1, destZScale))))), Func(toon.setPos, self.toonPitcherPosition), Func(toon.loop, 'leverNeutral'))
        return grabIval

    def makeToonReleaseInterval(self, toon):
        temp1 = self.waterPitcherNode.attachNewNode('temp1')
        temp1.setPos(self.toonPitcherPosition)
        temp2 = self.waterPitcherNode.attachNewNode('temp2')
        temp2.setPos(0, -10, -self.waterPitcherNode.getZ())
        startPos = temp1.getPos(render)
        endPos = temp2.getPos(render)
        temp1.removeNode()
        temp2.removeNode()

        def getSlideToPos(toon = toon):
            return render.getRelativePoint(toon, Point3(0, -10, 0))

        if self.gotHitByBoss:
            self.notify.debug('creating zap interval instead')
            grabIval = Sequence(Func(toon.loop, 'neutral'), Func(toon.wrtReparentTo, render), Parallel(ActorInterval(toon, 'slip-backward'), toon.posInterval(0.5, getSlideToPos, fluid=1)))
        else:
            grabIval = Sequence(Func(toon.loop, 'neutral'), Func(toon.wrtReparentTo, render), Parallel(ActorInterval(toon, 'jump'), Sequence(Wait(0.43), ProjectileInterval(toon, duration=0.9, startPos=startPos, endPos=endPos))))
        return grabIval

    def b_clearSmoothing(self):
        self.d_clearSmoothing()
        self.clearSmoothing()

    def d_clearSmoothing(self):
        self.sendUpdate('clearSmoothing', [0])

    def clearSmoothing(self, bogus = None):
        self.pitcherSmoother.clearPositions(1)

    def doSmoothTask(self, task):
        self.pitcherSmoother.computeAndApplySmoothHpr(self.waterPitcherNode)
        return Task.cont

    def startSmooth(self):
        if not self.smoothStarted:
            taskName = self.smoothName
            taskMgr.remove(taskName)
            self.reloadPosition()
            taskMgr.add(self.doSmoothTask, taskName)
            self.smoothStarted = 1

    def stopSmooth(self):
        if self.smoothStarted:
            taskName = self.smoothName
            taskMgr.remove(taskName)
            self.forceToTruePosition()
            self.smoothStarted = 0

    def __enableControlInterface(self):
        gui = loader.loadModel('phase_3.5/models/gui/avatar_panel_gui')
        self.closeButton = DirectButton(image=(gui.find('**/CloseBtn_UP'),
         gui.find('**/CloseBtn_DN'),
         gui.find('**/CloseBtn_Rllvr'),
         gui.find('**/CloseBtn_UP')), relief=None, scale=2, text=TTLocalizer.BossbotPitcherLeave, text_scale=0.04, text_pos=(0, -0.07), text_fg=VBase4(1, 1, 1, 1), pos=(1.05, 0, -0.82), command=self.__exitPitcher)
        self.accept('escape', self.__exitPitcher)
        self.accept('control', self.__controlPressed)
        self.accept('control-up', self.__controlReleased)
        self.accept('InputState-forward', self.__upArrow)
        self.accept('InputState-reverse', self.__downArrow)
        self.accept('InputState-turnLeft', self.__leftArrow)
        self.accept('InputState-turnRight', self.__rightArrow)
        self.accept('arrow_up', self.__upArrowKeyPressed)
        self.accept('arrow_down', self.__downArrowKeyPressed)
        taskMgr.add(self.__watchControls, self.watchControlsName)
        taskMgr.doMethodLater(5, self.__displayPitcherAdvice, self.pitcherAdviceName)
        self.arrowVert = 0
        self.arrowHorz = 0
        self.powerBar.show()
        return

    def __disableControlInterface(self):
        if self.closeButton:
            self.closeButton.destroy()
            self.closeButton = None
        self.__cleanupPitcherAdvice()
        self.ignore('escape')
        self.ignore('control')
        self.ignore('control-up')
        self.ignore('InputState-forward')
        self.ignore('InputState-reverse')
        self.ignore('InputState-turnLeft')
        self.ignore('InputState-turnRight')
        self.ignore('arrow_up')
        self.ignore('arrow_down')
        self.arrowVert = 0
        self.arrowHorz = 0
        taskMgr.remove(self.watchControlsName)
        taskMgr.remove(self.waterPowerTaskName)
        self.resetPowerBar()
        self.aimStart = None
        self.powerBar.hide()
        if self.TugOfWarControls:
            self.__killUpdateKeyPressRateTask()
            self.keyTTL = []
        self.__setMoveSound(None)
        return

    def __displayPitcherAdvice(self, task):
        if self.pitcherAdviceLabel == None:
            self.pitcherAdviceLabel = DirectLabel(text=TTLocalizer.BossbotPitcherAdvice, text_fg=VBase4(1, 1, 1, 1), text_align=TextNode.ACenter, relief=None, pos=(0, 0, 0.69), scale=0.1)
        return

    def __cleanupPitcherAdvice(self):
        if self.pitcherAdviceLabel:
            self.pitcherAdviceLabel.destroy()
            self.pitcherAdviceLabel = None
        taskMgr.remove(self.pitcherAdviceName)
        return

    def showExiting(self):
        if self.closeButton:
            self.closeButton.destroy()
            self.closeButton = DirectLabel(relief=None, text=TTLocalizer.BossbotPitcherLeaving, pos=(1.05, 0, -0.88), text_pos=(0, 0), text_scale=0.06, text_fg=VBase4(1, 1, 1, 1))
        self.__cleanupPitcherAdvice()
        return

    def __exitPitcher(self):
        self.showExiting()
        self.d_requestFree(False)

    def __controlPressed(self):
        self.__cleanupPitcherAdvice()
        if self.TugOfWarControls:
            if self.power:
                self.aimStart = 1
                self.__endFireWater()
        elif self.state == 'Controlled':
            self.__beginFireWater()

    def __controlReleased(self):
        if self.TugOfWarControls:
            pass
        elif self.state == 'Controlled':
            self.__endFireWater()

    def __upArrow(self, pressed):
        self.__incrementChangeSeq()
        self.__cleanupPitcherAdvice()
        if pressed:
            self.arrowVert = 1
        elif self.arrowVert > 0:
            self.arrowVert = 0

    def __downArrow(self, pressed):
        self.__incrementChangeSeq()
        self.__cleanupPitcherAdvice()
        if pressed:
            self.arrowVert = -1
        elif self.arrowVert < 0:
            self.arrowVert = 0

    def __rightArrow(self, pressed):
        self.__incrementChangeSeq()
        self.__cleanupPitcherAdvice()
        if pressed:
            self.arrowHorz = 1
        elif self.arrowHorz > 0:
            self.arrowHorz = 0

    def __leftArrow(self, pressed):
        self.__incrementChangeSeq()
        self.__cleanupPitcherAdvice()
        if pressed:
            self.arrowHorz = -1
        elif self.arrowHorz < 0:
            self.arrowHorz = 0

    def __incrementChangeSeq(self):
        self.changeSeq = self.changeSeq + 1 & 255

    def stopPosHprBroadcast(self):
        taskName = self.posHprBroadcastName
        taskMgr.remove(taskName)

    def startPosHprBroadcast(self):
        taskName = self.posHprBroadcastName
        self.b_clearSmoothing()
        self.d_sendPitcherPos()
        taskMgr.remove(taskName)
        taskMgr.doMethodLater(self.__broadcastPeriod, self.__posHprBroadcast, taskName)

    def __posHprBroadcast(self, task):
        self.d_sendPitcherPos()
        taskName = self.posHprBroadcastName
        taskMgr.doMethodLater(self.__broadcastPeriod, self.__posHprBroadcast, taskName)
        return Task.done

    def d_sendPitcherPos(self):
        timestamp = globalClockDelta.getFrameNetworkTime()
        self.sendUpdate('setPitcherPos', [self.changeSeq, self.waterPitcherNode.getH(), timestamp])

    def setPitcherPos(self, changeSeq, h, timestamp):
        self.changeSeq = changeSeq
        if self.smoothStarted:
            now = globalClock.getFrameTime()
            local = globalClockDelta.networkToLocalTime(timestamp, now)
            self.pitcherSmoother.setH(h)
            self.pitcherSmoother.setTimestamp(local)
            self.pitcherSmoother.markPosition()
        else:
            self.waterPitcherNode.setH(h)

    def __watchControls(self, task):
        if self.arrowHorz:
            self.__movePitcher(self.arrowHorz)
        else:
            self.__setMoveSound(None)
        return Task.cont

    def __movePitcher(self, xd):
        dt = globalClock.getDt()
        h = self.waterPitcherNode.getH() - xd * self.rotateSpeed * dt
        h %= 360
        self.notify.debug('rotSpeed=%.2f curH=%.2f  xd =%.2f, dt = %.2f, h=%.2f' % (self.rotateSpeed,
         self.waterPitcherNode.getH(),
         xd,
         dt,
         h))
        limitH = h
        self.waterPitcherNode.setH(limitH)
        if xd:
            self.__setMoveSound(self.pitcherMoveSfx)

    def reloadPosition(self):
        self.pitcherSmoother.clearPositions(0)
        self.pitcherSmoother.setHpr(self.waterPitcherNode.getHpr())
        self.pitcherSmoother.setPhonyTimestamp()

    def forceToTruePosition(self):
        if self.pitcherSmoother.getLatestPosition():
            self.pitcherSmoother.applySmoothHpr(self.waterPitcherNode)
        self.pitcherSmoother.clearPositions(1)

    def getSprayTrack(self, color, origin, target, dScaleUp, dHold, dScaleDown, horizScale = 1.0, vertScale = 1.0, parent = render):
        track = Sequence()
        SPRAY_LEN = 1.5
        sprayProp = MovieUtil.globalPropPool.getProp('spray')
        sprayScale = hidden.attachNewNode('spray-parent')
        sprayRot = hidden.attachNewNode('spray-rotate')
        spray = sprayRot
        spray.setColor(color)
        if color[3] < 1.0:
            spray.setTransparency(1)

        def showSpray(sprayScale, sprayRot, sprayProp, origin, target, parent):
            if callable(origin):
                origin = origin()
            if callable(target):
                target = target()
            sprayRot.reparentTo(parent)
            sprayRot.clearMat()
            sprayScale.reparentTo(sprayRot)
            sprayScale.clearMat()
            sprayProp.reparentTo(sprayScale)
            sprayProp.clearMat()
            sprayRot.setPos(origin)
            sprayRot.lookAt(Point3(target))

        track.append(Func(showSpray, sprayScale, sprayRot, sprayProp, origin, target, parent))

        def calcTargetScale(target = target, origin = origin, horizScale = horizScale, vertScale = vertScale):
            if callable(target):
                target = target()
            if callable(origin):
                origin = origin()
            distance = Vec3(target - origin).length()
            yScale = distance / SPRAY_LEN
            targetScale = Point3(yScale * horizScale, yScale, yScale * vertScale)
            return targetScale

        track.append(LerpScaleInterval(sprayScale, dScaleUp, calcTargetScale, startScale=Point3(0.01, 0.01, 0.01)))
        track.append(Func(self.checkHitObject))
        track.append(Wait(dHold))

        def prepareToShrinkSpray(spray, sprayProp, origin, target):
            if callable(target):
                target = target()
            if callable(origin):
                origin = origin()
            sprayProp.setPos(Point3(0.0, -SPRAY_LEN, 0.0))
            spray.setPos(target)

        track.append(Func(prepareToShrinkSpray, spray, sprayProp, origin, target))
        track.append(LerpScaleInterval(sprayScale, dScaleDown, Point3(0.01, 0.01, 0.01)))

        def hideSpray(spray, sprayScale, sprayRot, sprayProp, propPool):
            sprayProp.detachNode()
            MovieUtil.removeProp(sprayProp)
            sprayRot.removeNode()
            sprayScale.removeNode()

        track.append(Func(hideSpray, spray, sprayScale, sprayRot, sprayProp, MovieUtil.globalPropPool))
        return track

    def checkHitObject(self):
        if not self.hitObject:
            return
        if self.avId != base.localAvatar.doId:
            return
        tag = self.hitObject.getNetTag('pieCode')
        pieCode = int(tag)
        if pieCode == ToontownGlobals.PieCodeBossCog:
            self.hitBossSoundInterval.start()
            self.sendUpdate('waterHitBoss', [self.index])
            if self.TugOfWarControls:
                damage = 1
                if self.lastPowerFired < self.YELLOW_POWER_THRESHOLD:
                    damage = 1
                elif self.lastPowerFired < self.RED_POWER_THRESHOLD:
                    damage = 2
                else:
                    damage = 3
                self.boss.d_hitBoss(damage)
            else:
                damage = 1
                if self.lastPowerFired < self.YELLOW_POWER_THRESHOLD:
                    damage = 1
                elif self.lastPowerFired < self.RED_POWER_THRESHOLD:
                    damage = 2
                else:
                    damage = 3
                self.boss.d_hitBoss(damage)

    def waterHitBoss(self, tableIndex):
        if self.index == tableIndex:
            self.hitBossSoundInterval.start()

    def setupPowerBar(self):
        self.powerBar = DirectWaitBar(pos=(0.0, 0, -0.94), relief=DGG.SUNKEN, frameSize=(-2.0,
         2.0,
         -0.2,
         0.2), borderWidth=(0.02, 0.02), scale=0.25, range=1, sortOrder=50, frameColor=(0.5, 0.5, 0.5, 0.5), barColor=(0.75, 0.75, 1.0, 0.8), text='', text_scale=0.26, text_fg=(1, 1, 1, 1), text_align=TextNode.ACenter, text_pos=(0, -0.05))
        self.power = 0
        self.powerBar['value'] = self.power
        self.powerBar.hide()

    def resetPowerBar(self):
        self.power = 0
        self.powerBar['value'] = self.power
        self.powerBar['text'] = ''
        self.keyTTL = []

    def __beginFireWater(self):
        if self.fireTrack and self.fireTrack.isPlaying():
            return
        if self.aimStart != None:
            return
        if not self.state == 'Controlled':
            return
        if not self.avId == localAvatar.doId:
            return
        time = globalClock.getFrameTime()
        self.aimStart = time
        messenger.send('wakeup')
        taskMgr.add(self.__updateWaterPower, self.waterPowerTaskName)
        return

    def __endFireWater(self):
        if self.aimStart == None:
            return
        if not self.state == 'Controlled':
            return
        if not self.avId == localAvatar.doId:
            return
        taskMgr.remove(self.waterPowerTaskName)
        messenger.send('wakeup')
        self.aimStart = None
        origin = self.nozzle.getPos(render)
        target = self.boss.getPos(render)
        angle = deg2Rad(self.waterPitcherNode.getH() + 90)
        x = math.cos(angle)
        y = math.sin(angle)
        fireVector = Point3(x, y, 0)
        if self.power < 0.001:
            self.power = 0.001
        self.lastPowerFired = self.power
        fireVector *= self.fireLength * self.power
        target = origin + fireVector
        segment = CollisionSegment(origin[0], origin[1], origin[2], target[0], target[1], target[2])
        fromObject = render.attachNewNode(CollisionNode('pitcherColNode'))
        fromObject.node().addSolid(segment)
        fromObject.node().setFromCollideMask(ToontownGlobals.PieBitmask | ToontownGlobals.CameraBitmask | ToontownGlobals.FloorBitmask)
        fromObject.node().setIntoCollideMask(BitMask32.allOff())
        queue = CollisionHandlerQueue()
        base.cTrav.addCollider(fromObject, queue)
        base.cTrav.traverse(render)
        queue.sortEntries()
        self.hitObject = None
        if queue.getNumEntries():
            entry = queue.getEntry(0)
            target = entry.getSurfacePoint(render)
            self.hitObject = entry.getIntoNodePath()
        base.cTrav.removeCollider(fromObject)
        fromObject.removeNode()
        self.d_firingWater(origin, target)
        self.fireWater(origin, target)
        self.resetPowerBar()
        return

    def __updateWaterPower(self, task):
        if not self.powerBar:
            print '### no power bar!!!'
            return task.done
        newPower = self.__getWaterPower(globalClock.getFrameTime())
        self.power = newPower
        self.powerBar['value'] = newPower
        if self.power < self.YELLOW_POWER_THRESHOLD:
            self.powerBar['barColor'] = VBase4(0.75, 0.75, 1.0, 0.8)
        elif self.power < self.RED_POWER_THRESHOLD:
            self.powerBar['barColor'] = VBase4(1.0, 1.0, 0.0, 0.8)
        else:
            self.powerBar['barColor'] = VBase4(1.0, 0.0, 0.0, 0.8)
        return task.cont

    def __getWaterPower(self, time):
        elapsed = max(time - self.aimStart, 0.0)
        t = elapsed / self.waterPowerSpeed
        exponent = self.waterPowerExponent
        if t > 1:
            t = t % 1
        power = 1 - math.pow(1 - t, exponent)
        if power > 1.0:
            power = 1.0
        return power

    def d_firingWater(self, origin, target):
        self.sendUpdate('firingWater', [origin[0],
         origin[1],
         origin[2],
         target[0],
         target[1],
         target[2]])

    def firingWater(self, startX, startY, startZ, endX, endY, endZ):
        origin = Point3(startX, startY, startZ)
        target = Point3(endX, endY, endZ)
        self.fireWater(origin, target)

    def fireWater(self, origin, target):
        color = VBase4(0.75, 0.75, 1, 0.8)
        dScaleUp = 0.1
        dHold = 0.3
        dScaleDown = 0.1
        horizScale = 0.1
        vertScale = 0.1
        sprayTrack = self.getSprayTrack(color, origin, target, dScaleUp, dHold, dScaleDown, horizScale, vertScale)
        duration = self.squirtSfx.length()
        if sprayTrack.getDuration() < duration:
            duration = sprayTrack.getDuration()
        soundTrack = SoundInterval(self.squirtSfx, node=self.waterPitcherModel, duration=duration)
        self.fireTrack = Parallel(sprayTrack, soundTrack)
        self.fireTrack.start()

    def getPos(self, wrt = render):
        return self.tableGroup.getPos(wrt)

    def getLocator(self):
        return self.tableGroup

    def enterFlat(self, avId):
        self.prepareForPhaseFour()
        self.resetPowerBar()
        self.notify.debug('enterFlat %d' % self.index)
        if self.avId:
            toon = base.cr.doId2do.get(self.avId)
            if toon:
                toon.wrtReparentTo(render)
                toon.setZ(0)
        self.tableGroup.setScale(1, 1, 0.01)
        if self.avId and self.avId == localAvatar.doId:
            localAvatar.b_squish(ToontownGlobals.BossCogDamageLevels[ToontownGlobals.BossCogMoveAttack])

    def exitFlat(self):
        self.tableGroup.setScale(1.0)
        if self.avId:
            toon = base.cr.doId2do.get(self.avId)
            if toon:
                if toon == localAvatar:
                    self.boss.toCraneMode()
                    toon.b_setAnimState('neutral')
                toon.setAnimState('neutral')
                toon.loop('leverNeutral')

    def __allowDetect(self, task):
        if self.fadeTrack:
            self.fadeTrack.finish()
        self.fadeTrack = Sequence(self.tableGroup.colorScaleInterval(0.2, VBase4(1, 1, 1, 1)), Func(self.tableGroup.clearColorScale), Func(self.tableGroup.clearTransparency))
        self.fadeTrack.start()
        self.allowLocalRequestControl = True

    def gotBossZapped(self):
        self.showExiting()
        self.d_requestFree(True)

    def __upArrowKeyPressed(self):
        if self.TugOfWarControls:
            self.__pressHandler(0)

    def __downArrowKeyPressed(self):
        if self.TugOfWarControls:
            self.__pressHandler(1)

    def __pressHandler(self, index):
        if index == self.buttons[0]:
            self.keyTTL.insert(0, 1.0)
            if not self.OnlyUpArrow:
                self.buttons.reverse()

    def __spawnUpdateKeyPressRateTask(self):
        taskMgr.remove(self.taskName(self.UPDATE_KEY_PRESS_RATE_TASK))
        taskMgr.doMethodLater(0.1, self.__updateKeyPressRateTask, self.taskName(self.UPDATE_KEY_PRESS_RATE_TASK))

    def __killUpdateKeyPressRateTask(self):
        taskMgr.remove(self.taskName(self.UPDATE_KEY_PRESS_RATE_TASK))

    def __updateKeyPressRateTask(self, task):
        if self.state not in 'Controlled':
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
        keyRateDiff = self.keyRate - self.BASELINE_KEY_RATE
        diffPower = keyRateDiff / 300.0
        if self.power < 1 and diffPower > 0:
            diffPower = diffPower * math.pow(1 - self.power, 1.25)
        newPower = self.power + diffPower
        if newPower > 1:
            newPower = 1
        elif newPower < 0:
            newPower = 0
        self.notify.debug('diffPower=%.2f keyRate = %d, newPower=%.2f' % (diffPower, self.keyRate, newPower))
        self.power = newPower
        self.powerBar['value'] = newPower
        if self.power < self.YELLOW_POWER_THRESHOLD:
            self.powerBar['barColor'] = VBase4(0.75, 0.75, 1.0, 0.8)
        elif self.power < self.RED_POWER_THRESHOLD:
            self.powerBar['barColor'] = VBase4(1.0, 1.0, 0.0, 0.8)
        else:
            self.powerBar['barColor'] = VBase4(1.0, 0.0, 0.0, 0.8)
        self.__spawnUpdateKeyPressRateTask()
        return Task.done

    def __setMoveSound(self, sfx):
        if sfx != self.moveSound:
            if self.moveSound:
                self.moveSound.stop()
            self.moveSound = sfx
            if self.moveSound:
                base.playSfx(self.moveSound, looping=1, volume=0.5)
