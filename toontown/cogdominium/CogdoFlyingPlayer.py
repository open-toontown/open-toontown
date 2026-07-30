from panda3d.core import DepthOffsetAttrib, NodePath, Vec3, Vec4, TextNode
from direct.directnotify import DirectNotifyGlobal
from direct.fsm.FSM import FSM
from direct.interval.FunctionInterval import Wait
from direct.interval.IntervalGlobal import Func, LerpHprInterval, LerpScaleInterval, LerpFunctionInterval
from direct.interval.MetaInterval import Sequence, Parallel
from direct.distributed.ClockDelta import globalClockDelta
from toontown.toonbase import ToontownGlobals
from toontown.effects import DustCloud
from . import CogdoFlyingGameGlobals as Globals
from . import CogdoUtil
from .CogdoFlyingObjects import CogdoFlyingGatherable
from .CogdoFlyingUtil import swapAvatarShadowPlacer

class CogdoFlyingPlayer(FSM):
    notify = DirectNotifyGlobal.directNotify.newCategory('CogdoFlyingPlayer')

    def __init__(self, toon):
        FSM.__init__(self, 'CogdoFlyingPlayer')
        self.toon = toon
        self.toon.reparentTo(render)
        self.legalEaglesTargeting = []
        self.activeBuffs = []
        self.initModels()
        self.initIntervals()
        self.netTimeSentToStartDeath = 0
        self.backpackState = -1
        self.lastBackpackState = -1
        self.lastPropellerSpinRate = Globals.Gameplay.NormalPropSpeed
        self.propellerSpinRate = Globals.Gameplay.NormalPropSpeed
        self.setFuelState(Globals.Gameplay.FuelStates.FuelNoPropeller)
        self.setOldFuelState(self.fuelState)
        CogdoFlyingPlayer.setBlades(self, Globals.Gameplay.FuelStates.FuelNoPropeller)
        self.setBackpackState(Globals.Gameplay.BackpackStates.Normal)

    def initModels(self):
        self.createPropeller()
        self.createRedTapeRing()

    def createPropeller(self):
        self.propellerSmoke = DustCloud.DustCloud(self.toon, wantSound=False)
        self.propellerSmoke.setBillboardPointEye()
        self.propellerSmoke.setBin('fixed', 5002)
        self.backpack = CogdoUtil.loadFlyingModel('propellerPack')
        self.backpack.setScale(1.3)
        self.backpack.setHpr(180.0, 0.0, 0.0)
        self.backpackInstances = []
        self.backpackTextureCard = CogdoUtil.loadFlyingModel('propellerPack_card')
        parts = self.toon.getTorsoParts()
        for part in parts:
            backpackInstance = part.attachNewNode('backpackInstance')
            animal = self.toon.style.getAnimal()
            bodyScale = ToontownGlobals.toonBodyScales[animal]
            backpackHeight = ToontownGlobals.torsoHeightDict[self.toon.style.torso] * bodyScale - 0.5
            backpackInstance.setPos(0.0, -0.325, backpackHeight)
            self.backpackInstances.append(backpackInstance)
            self.backpack.instanceTo(backpackInstance)

        self.propInstances = []
        self.propeller = CogdoUtil.loadFlyingModel('toonPropeller')
        for part in self.backpackInstances:
            propInstance = part.attachNewNode('propInstance')
            propInstance.setPos(0.0, -0.275, 0.0)
            propInstance.setHpr(0.0, 20.0, 0.0)
            propInstance.setScale(1.0, 1.0, 1.25)
            self.propInstances.append(propInstance)
            self.propeller.instanceTo(propInstance)

        self.blades = []
        self.activeBlades = []
        index = 1
        blade = self.propeller.find('**/propeller%d' % index)
        while not blade.isEmpty():
            self.blades.append(blade)
            index += 1
            blade = self.propeller.find('**/propeller%d' % index)

        for blade in self.blades:
            self.activeBlades.append(blade)

    def createRedTapeRing(self):
        self.redTapeRing = CogdoUtil.loadFlyingModel('redTapeRing')
        self.redTapeRing.setTwoSided(True)
        self.redTapeRing.reparentTo(self.toon)
        self.redTapeRing.hide()
        self.redTapeRing.setScale(1.25)
        self.redTapeRing.setZ(self.toon.getHeight() / 2.0)

    def initIntervals(self):
        self.baseSpinDuration = 1.0
        self.propellerSpinLerp = LerpFunctionInterval(self.propeller.setH, fromData=0.0, toData=360.0, duration=self.baseSpinDuration, name='%s.propellerSpinLerp-%s' % (self.__class__.__name__, self.toon.doId))
        singleBlinkTime = Globals.Gameplay.TargetedWarningSingleBlinkTime
        blinkTime = Globals.Gameplay.TargetedWarningBlinkTime
        self.blinkLoop = Sequence(Wait(singleBlinkTime / 2.0), Func(self.setBackpackTexture, Globals.Gameplay.BackpackStates.Attacked), Wait(singleBlinkTime / 2.0), Func(self.setBackpackTexture, Globals.Gameplay.BackpackStates.Targeted), name='%s.blinkLoop-%s' % (self.__class__.__name__, self.toon.doId))
        self.blinkWarningSeq = Sequence(Func(self.blinkLoop.loop), Wait(blinkTime), Func(self.blinkLoop.clearToInitial), name='%s.blinkWarningSeq-%s' % (self.__class__.__name__, self.toon.doId))
        dur = Globals.Gameplay.BackpackRefuelDuration
        self.refuelSeq = Sequence(Func(self.setPropellerSpinRate, Globals.Gameplay.RefuelPropSpeed), Wait(dur), Func(self.returnBackpackToLastStateFunc), name='%s.refuelSeq-%s' % (self.__class__.__name__, self.toon.doId))
        scale = self.redTapeRing.getScale()
        pulseTime = 1.0
        self.pulseBubbleSeq = Parallel(Sequence(LerpFunctionInterval(self.redTapeRing.setScale, fromData=scale, toData=scale * 1.1, duration=pulseTime / 2.0, blendType='easeInOut'), LerpFunctionInterval(self.redTapeRing.setScale, fromData=scale * 1.1, toData=scale, duration=pulseTime / 2.0, blendType='easeInOut')), LerpHprInterval(self.redTapeRing, pulseTime, Vec3(360, 0, 0), startHpr=Vec3(0, 0, 0)), name='%s.pulseBubbleSeq-%s' % (self.__class__.__name__, self.toon.doId))
        bouncePercent = 1.2
        scaleTime = 0.5
        scaleBounceTime = 0.25
        self.popUpBubbleLerp = LerpScaleInterval(self.redTapeRing, scaleTime, scale * bouncePercent, startScale=0.0, blendType='easeInOut')
        self.popUpBubbleSeq = Sequence(Func(self.updateLerpStartScale, self.popUpBubbleLerp, self.redTapeRing), Func(self.redTapeRing.show), self.popUpBubbleLerp, LerpScaleInterval(self.redTapeRing, scaleBounceTime, scale, startScale=scale * bouncePercent, blendType='easeInOut'), Func(self.pulseBubbleSeq.loop), name='%s.popUpBubbleSeq-%s' % (self.__class__.__name__, self.toon.doId))
        self.removeBubbleLerp = LerpScaleInterval(self.redTapeRing, scaleBounceTime, scale * bouncePercent, startScale=scale, blendType='easeInOut')
        self.removeBubbleSeq = Sequence(Func(self.pulseBubbleSeq.clearToInitial), Func(self.updateLerpStartScale, self.removeBubbleLerp, self.redTapeRing), self.removeBubbleLerp, LerpScaleInterval(self.redTapeRing, scaleTime, 0.0, startScale=scale * bouncePercent, blendType='easeInOut'), Func(self.redTapeRing.hide), name='%s.removeBubbleSeq-%s' % (self.__class__.__name__, self.toon.doId))
        self.redTapeRing.setScale(0.0)
        self.deathInterval = Sequence(Parallel(LerpHprInterval(self.toon, 1.0, Vec3(720, 0, 0)), LerpFunctionInterval(self.toon.setScale, fromData=1.0, toData=0.1, duration=1.0)), Func(self.toon.stash), name='%s.deathInterval-%s' % (self.__class__.__name__, self.toon.doId))
        self.spawnInterval = Sequence(Func(self.toon.stash), Func(self.resetToon), Wait(1.0), Func(self.toon.setAnimState, 'TeleportIn'), Func(self.toon.unstash), name='%s.spawnInterval-%s' % (self.__class__.__name__, self.toon.doId))
        singleBlinkTime = Globals.Gameplay.InvulSingleBlinkTime
        blinkTime = Globals.Gameplay.InvulBlinkTime
        invulBuffTime = Globals.Gameplay.InvulBuffTime
        self.blinkBubbleLoop = Sequence(LerpFunctionInterval(self.redTapeRing.setAlphaScale, fromData=1.0, toData=0.0, duration=singleBlinkTime / 2.0, blendType='easeInOut'), LerpFunctionInterval(self.redTapeRing.setAlphaScale, fromData=0.0, toData=1.0, duration=singleBlinkTime / 2.0, blendType='easeInOut'), name='%s.blinkBubbleLoop-%s' % (self.__class__.__name__, self.toon.doId))
        self.blinkBubbleSeq = Sequence(Wait(invulBuffTime - blinkTime), Func(self.blinkBubbleLoop.loop), Wait(blinkTime), Func(self.blinkBubbleLoop.finish), name='%s.blinkBubbleSeq-%s' % (self.__class__.__name__, self.toon.doId))

    def returnBackpackToLastStateFunc(self):
        if self.backpackState == Globals.Gameplay.BackpackStates.Refuel:
            self.returnBackpackToLastState()

    def setPropellerSpinRateFunc(self):
        if self.propellerSpinRate == Globals.Gameplay.RefuelPropSpeed:
            self.setPropellerSpinRate(self.lastPropellerSpinRate)

    def returnBackpackToLastState(self):
        self.setBackpackState(self.lastBackpackState)

    def setBackpackState(self, state):
        if state == self.backpackState:
            return
        self.lastBackpackState = self.backpackState
        self.backpackState = state
        self.blinkWarningSeq.clearToInitial()
        self.refuelSeq.clearToInitial()
        self.blinkLoop.clearToInitial()
        if self.lastBackpackState == Globals.Gameplay.BackpackStates.Refuel:
            self.setPropellerSpinRateFunc()
        if state in Globals.Gameplay.BackpackStates:
            if state == Globals.Gameplay.BackpackStates.Normal:
                pass
            elif state == Globals.Gameplay.BackpackStates.Targeted:
                pass
            elif state == Globals.Gameplay.BackpackStates.Refuel:
                self.refuelSeq.start()
            elif state == Globals.Gameplay.BackpackStates.Attacked:
                self.blinkWarningSeq.start()
            self.setBackpackTexture(state)

    def setBackpackTexture(self, state):
        texName = Globals.Gameplay.BackpackState2TextureName[state]
        tex = self.backpackTextureCard.findTexture(texName)
        self.backpack.setTexture(tex, 1)

    def updateLerpStartScale(self, lerp, nodepath):
        lerp.setStartScale(nodepath.getScale())

    def handleEnterGatherable(self, gatherable, elapsedTime):
        if gatherable.type == Globals.Level.GatherableTypes.InvulPowerup:
            self.blinkBubbleSeq.clearToInitial()
            self.blinkBubbleSeq.start(elapsedTime)
            self.removeBubbleSeq.clearToInitial()
            self.popUpBubbleSeq.start()
            if gatherable.type not in self.activeBuffs:
                self.activeBuffs.append(gatherable.type)
        elif gatherable.type == Globals.Level.GatherableTypes.Propeller:
            self.setBackpackState(Globals.Gameplay.BackpackStates.Refuel)

    def handleDebuffPowerup(self, pickupType, elapsedTime):
        if pickupType == Globals.Level.GatherableTypes.InvulPowerup:
            self.blinkBubbleSeq.finish()
            self.popUpBubbleSeq.clearToInitial()
            self.removeBubbleSeq.start()
            if pickupType in self.activeBuffs:
                self.activeBuffs.remove(pickupType)

    def isBuffActive(self, pickupType):
        if pickupType in self.activeBuffs:
            return True
        return False

    def isInvulnerable(self):
        if Globals.Level.GatherableTypes.InvulPowerup in self.activeBuffs:
            return True
        return False

    def setFuelState(self, fuelState):
        self.fuelState = fuelState

    def setOldFuelState(self, fuelState):
        self.oldFuelState = fuelState

    def hasFuelStateChanged(self):
        if self.fuelState != self.oldFuelState:
            return True
        else:
            return False

    def updatePropellerSmoke(self):
        if not self.hasFuelStateChanged():
            return
        if self.fuelState in [Globals.Gameplay.FuelStates.FuelNoPropeller, Globals.Gameplay.FuelStates.FuelNormal]:
            self.propellerSmoke.stop()
        elif self.fuelState in [Globals.Gameplay.FuelStates.FuelVeryLow, Globals.Gameplay.FuelStates.FuelEmpty]:
            self.propellerSmoke.stop()
            self.propellerSmoke.setScale(0.25)
            self.propellerSmoke.setZ(self.toon.getHeight() + 2.5)
            self.propellerSmoke.loop(rate=48)
        elif self.fuelState in [Globals.Gameplay.FuelStates.FuelLow]:
            self.propellerSmoke.stop()
            self.propellerSmoke.setScale(0.0825)
            self.propellerSmoke.setZ(self.toon.getHeight() + 2.0)
            self.propellerSmoke.loop(rate=24)

    def resetBlades(self):
        self.setBlades(len(self.blades))

    def setAsLegalEagleTarget(self, legalEagle):
        if legalEagle not in self.legalEaglesTargeting:
            self.legalEaglesTargeting.append(legalEagle)

    def removeAsLegalEagleTarget(self, legalEagle):
        if legalEagle in self.legalEaglesTargeting:
            self.legalEaglesTargeting.remove(legalEagle)

    def isLegalEagleTarget(self):
        if len(self.legalEaglesTargeting) > 0:
            return True
        else:
            return False

    def setBlades(self, fuelState):
        if fuelState not in Globals.Gameplay.FuelStates:
            return
        numBlades = fuelState - 1
        if len(self.activeBlades) != numBlades:
            for i in range(len(self.activeBlades)):
                blade = self.activeBlades.pop()
                blade.stash()

            if numBlades > len(self.blades):
                numBlades = len(self.blades)
            if numBlades > 0:
                for i in range(numBlades):
                    blade = self.blades[i]
                    self.activeBlades.append(blade)
                    blade.unstash()

            if fuelState == Globals.Gameplay.FuelStates.FuelNoPropeller:
                for prop in self.propInstances:
                    prop.hide()

            else:
                for prop in self.propInstances:
                    prop.show()

            self.setFuelState(fuelState)
            self.updatePropellerSmoke()
            self.setOldFuelState(self.fuelState)

    def bladeLost(self):
        if len(self.activeBlades) > 0:
            blade = self.activeBlades.pop()
            blade.stash()
            self.setFuelState(len(self.activeBlades) + 1)
            self.updatePropellerSmoke()
            self.setOldFuelState(self.fuelState)

    def setPropellerSpinRate(self, newRate):
        self.lastPropellerSpinRate = self.propellerSpinRate
        self.propellerSpinRate = newRate
        self.notify.debug('(%s) New propeller speed:%s, old propeller speed:%s' % (self.toon.doId, self.propellerSpinRate, self.lastPropellerSpinRate))
        self.propellerSpinLerp.setPlayRate(newRate)

    def died(self, elapsedTime):
        self.deathInterval.start(elapsedTime)
        self.propellerSmoke.stop()

    def spawn(self, elapsedTime):
        self.spawnInterval.start(elapsedTime)

    def resetToon(self):
        self.toon.setScale(1.0)

    def enable(self):
        self.toon.setAnimState('Happy', 1.0)
        self.toon.setForceJumpIdle(True)
        self.toon.setSpeed(0, 0)
        self.setPropellerSpinRate(Globals.Gameplay.NormalPropSpeed)
        self.propellerSpinLerp.loop()

    def disable(self):
        pass

    def unload(self):
        self.ignoreAll()
        if self.toon:
            self.toon.showName()
        self.backpackTextureCard.removeNode()
        del self.backpackTextureCard
        self.refuelSeq.clearToInitial()
        del self.refuelSeq
        self.pulseBubbleSeq.clearToInitial()
        del self.pulseBubbleSeq
        self.blinkBubbleLoop.clearToInitial()
        del self.blinkBubbleLoop
        self.blinkBubbleSeq.clearToInitial()
        del self.blinkBubbleSeq
        self.popUpBubbleLerp.clearToInitial()
        del self.popUpBubbleLerp
        self.popUpBubbleSeq.clearToInitial()
        del self.popUpBubbleSeq
        self.removeBubbleLerp.clearToInitial()
        del self.removeBubbleLerp
        self.removeBubbleSeq.clearToInitial()
        del self.removeBubbleSeq
        self.propellerSmoke.destroy()
        del self.propellerSmoke
        self.blinkWarningSeq.clearToInitial()
        del self.blinkWarningSeq
        self.blinkLoop.clearToInitial()
        del self.blinkLoop
        self.redTapeRing.removeNode()
        del self.redTapeRing
        self.propellerSpinLerp.clearToInitial()
        del self.propellerSpinLerp
        for prop in self.propInstances:
            prop.removeNode()

        del self.propInstances[:]
        self.propeller.removeNode()
        del self.propeller
        for backpack in self.backpackInstances:
            backpack.removeNode()

        del self.backpackInstances[:]
        self.backpack.removeNode()
        del self.backpack
        del self.activeBuffs[:]
        del self.legalEaglesTargeting[:]
        del self.toon
        self.toon = None
        if self.deathInterval:
            self.deathInterval.clearToInitial()
            self.deathInterval = None
        if self.spawnInterval:
            self.spawnInterval.clearToInitial()
            self.spawnInterval = None
        return

    def start(self):
        swapAvatarShadowPlacer(self.toon, self.toon.uniqueName('toonShadowPlacer'))
        self.toon.startSmooth()

    def exit(self):
        self.toon.setForceJumpIdle(False)
        self.propellerSmoke.reparentTo(hidden)
        self.propellerSmoke.stop()
        if self.toon:
            CogdoFlyingPlayer.resetToon(self)
            self.toon.setActiveShadow(0)
            self.toon.deleteDropShadow()
            self.toon.initializeDropShadow()
            self.toon.setActiveShadow(1)
        else:
            self.notify.warning("There's no toon in offstage, this is bad!")
