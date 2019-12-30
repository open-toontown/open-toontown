import random
from pandac.PandaModules import *
from direct.interval.IntervalGlobal import Sequence, Func, Parallel, Wait, LerpHprInterval, LerpScaleInterval, LerpFunctionInterval
from otp.otpbase import OTPGlobals
from toontown.toonbase import ToontownGlobals
from .CogdoGameGatherable import CogdoGameGatherable, CogdoMemo
from . import CogdoFlyingGameGlobals as Globals
from . import CogdoUtil
from direct.particles import ParticleEffect
from direct.particles import Particles
from direct.particles import ForceGroup

class CogdoFlyingGatherableFactory:

    def __init__(self):
        self._serialNum = -1
        self._memoModel = CogdoUtil.loadModel('memo', 'shared').find('**/memo')
        self._propellerModel = CogdoUtil.loadFlyingModel('propellers').find('**/mesh')
        self._powerUpModels = {}
        for type, modelName in list(Globals.Level.PowerupType2Model.items()):
            model = CogdoUtil.loadFlyingModel(modelName).find('**/' + Globals.Level.PowerupType2Node[type])
            self._powerUpModels[type] = model
            model.setTransparency(True)
            model.setScale(0.5)

    def createMemo(self):
        self._serialNum += 1
        return CogdoFlyingMemo(self._serialNum, self._memoModel)

    def createPropeller(self):
        self._serialNum += 1
        return CogdoFlyingPropeller(self._serialNum, self._propellerModel)

    def createPowerup(self, type):
        self._serialNum += 1
        return CogdoFlyingPowerup(self._serialNum, type, self._powerUpModels[type])

    def createSparkles(self, color1, color2, amp):
        self.f = ParticleEffect.ParticleEffect('particleEffect_sparkles')
        p0 = Particles.Particles('particles-1')
        p0.setFactory('PointParticleFactory')
        p0.setRenderer('SparkleParticleRenderer')
        p0.setEmitter('RingEmitter')
        p0.setPoolSize(15)
        p0.setBirthRate(0.1)
        p0.setLitterSize(100)
        p0.setLitterSpread(0)
        p0.factory.setLifespanBase(0.6)
        p0.factory.setLifespanSpread(0.1)
        p0.factory.setMassBase(1.0)
        p0.factory.setMassSpread(0.0)
        p0.factory.setTerminalVelocityBase(3.0)
        p0.factory.setTerminalVelocitySpread(1.0)
        p0.renderer.setAlphaMode(BaseParticleRenderer.PRALPHAOUT)
        p0.renderer.setUserAlpha(1.0)
        p0.renderer.setCenterColor(color1)
        p0.renderer.setEdgeColor(color2)
        p0.renderer.setBirthRadius(0.3)
        p0.renderer.setDeathRadius(0.3)
        p0.renderer.setLifeScale(SparkleParticleRenderer.SPNOSCALE)
        p0.emitter.setEmissionType(BaseParticleEmitter.ETRADIATE)
        p0.emitter.setAmplitude(0)
        p0.emitter.setAmplitudeSpread(0)
        f0 = ForceGroup.ForceGroup('Gravity')
        force0 = LinearVectorForce(Vec3(0.0, 0.0, -10.0), 1.0, 0)
        force0.setVectorMasks(1, 1, 1)
        force0.setActive(1)
        f0.addForce(force0)
        self.f.addForceGroup(f0)
        p0.emitter.setRadius(2.0)
        self.f.addParticles(p0)
        self.f.setPos(0, 0, 0)
        self.f.setHpr(0, random.random() * 180, random.random() * 180)
        return self.f

    def destroy(self):
        self._memoModel.removeNode()
        del self._memoModel
        self._propellerModel.removeNode()
        del self._propellerModel
        for model in list(self._powerUpModels.values()):
            model.removeNode()

        del self._powerUpModels
        if Globals.Level.AddSparkleToPowerups:
            self.f.cleanup()
            del self.f


class CogdoFlyingGatherableBase:

    def __init__(self, type):
        self.type = type
        self.initFlash()

    def initFlash(self):
        model = CogdoUtil.loadFlyingModel('gatherableFlash_card')
        texName = Globals.Level.GatherableType2TextureName[self.type]
        tex = model.findTexture(texName)
        tex.setWrapU(Texture.WMRepeat)
        tex.setWrapV(Texture.WMRepeat)
        del model
        self.ts = TextureStage('ts')
        self.ts.setMode(TextureStage.MCombine)
        self.ts.setSort(1)
        self.ts.setCombineRgb(TextureStage.CMInterpolate, TextureStage.CSPrevious, TextureStage.COSrcColor, TextureStage.CSTexture, TextureStage.COSrcColor, TextureStage.CSConstant, TextureStage.COSrcColor)
        self.ts.setCombineAlpha(TextureStage.CMInterpolate, TextureStage.CSPrevious, TextureStage.COSrcAlpha, TextureStage.CSTexture, TextureStage.COSrcAlpha, TextureStage.CSConstant, TextureStage.COSrcAlpha)
        self._model.setTexture(self.ts, tex)
        dur = Globals.Gameplay.GatherableFlashTime
        self.flashLoop = Sequence(LerpFunctionInterval(self.setTextureAlphaFunc, fromData=1.0, toData=0.25, duration=dur / 2.0, blendType='easeInOut'), LerpFunctionInterval(self.setTextureAlphaFunc, fromData=0.25, toData=1.0, duration=dur / 2.0, blendType='easeInOut'), Wait(1.0), name='%s.flashLoop-%s' % (self.__class__.__name__, self.serialNum))

    def show(self):
        self.enableFlash()

    def hide(self):
        self.disableFlash()

    def enable(self):
        pass

    def disable(self):
        pass

    def enableFlash(self):
        self.flashLoop.loop()

    def disableFlash(self):
        self.flashLoop.clearToInitial()

    def destroy(self):
        self.disableFlash()
        del self.flashLoop
        del self.ts

    def setTextureAlphaFunc(self, value):
        self.ts.setColor(Vec4(value, value, value, value))

    def isPowerUp(self):
        return False


class CogdoFlyingGatherable(CogdoGameGatherable, CogdoFlyingGatherableBase):

    def __init__(self, type, serialNum, modelToInstance, triggerRadius, animate = True):
        CogdoGameGatherable.__init__(self, serialNum, modelToInstance, triggerRadius, animate=animate)
        CogdoFlyingGatherableBase.__init__(self, type)

    def enable(self):
        CogdoGameGatherable.enable(self)
        CogdoFlyingGatherableBase.enable(self)

    def disable(self):
        CogdoGameGatherable.disable(self)
        CogdoFlyingGatherableBase.disable(self)

    def show(self):
        CogdoGameGatherable.show(self)
        CogdoFlyingGatherableBase.show(self)

    def hide(self):
        CogdoGameGatherable.hide(self)
        CogdoFlyingGatherableBase.hide(self)

    def destroy(self):
        CogdoGameGatherable.destroy(self)
        CogdoFlyingGatherableBase.destroy(self)


class CogdoFlyingMemo(CogdoFlyingGatherableBase, CogdoMemo):

    def __init__(self, serialNum, model):
        CogdoMemo.__init__(self, serialNum, triggerRadius=Globals.Gameplay.MemoCollisionRadius, spinRate=Globals.Gameplay.MemoSpinRate, model=model)
        CogdoFlyingGatherableBase.__init__(self, Globals.Level.GatherableTypes.Memo)
        self.floatTimer = 0.0
        self.floatSpeed = 1.0
        self.floatDuration = 2.0

    def _handleEnterCollision(self, collEntry):
        CogdoGameGatherable._handleEnterCollision(self, collEntry)

    def enable(self):
        CogdoFlyingGatherableBase.enable(self)
        CogdoMemo.enable(self)

    def disable(self):
        CogdoFlyingGatherableBase.disable(self)
        CogdoMemo.disable(self)

    def show(self):
        CogdoFlyingGatherableBase.show(self)
        CogdoMemo.show(self)

    def hide(self):
        CogdoFlyingGatherableBase.hide(self)
        CogdoMemo.hide(self)

    def destroy(self):
        CogdoFlyingGatherableBase.destroy(self)
        CogdoMemo.destroy(self)

    def update(self, dt):
        self.floatTimer += dt
        if self.floatTimer < self.floatDuration:
            self.setPos(self.getPos() + Vec3(0, 0, dt * self.floatSpeed))
        elif self.floatTimer < self.floatDuration * 2.0:
            self.setPos(self.getPos() - Vec3(0, 0, dt * self.floatSpeed))
        else:
            self.floatTimer = 0.0
            self.floatSpeed = random.uniform(0.5, 1.0)
            self.floatDuration = random.uniform(1.9, 2.1)


class CogdoFlyingPowerup(CogdoFlyingGatherable):

    def __init__(self, serialNum, powerupType, model):
        self._pickedUpList = []
        self._isToonLocal = False
        CogdoFlyingGatherable.__init__(self, powerupType, serialNum, model, Globals.Gameplay.MemoCollisionRadius)
        self.initInterval()

    def initInterval(self):
        bouncePercent = 1.2
        scale = self._model.getScale()
        shrinkPowerupLerp = LerpScaleInterval(self._model, 0.5, 0.0, startScale=0.0, blendType='easeInOut')
        growPowerupLerp = LerpScaleInterval(self._model, 0.5, scale * bouncePercent, startScale=0.0, blendType='easeInOut')
        bouncePowerupLerp = LerpScaleInterval(self._model, 0.25, scale, startScale=scale * bouncePercent, blendType='easeInOut')
        self.pickUpSeq = Sequence(Func(self.updateLerpStartScale, shrinkPowerupLerp, self._model), shrinkPowerupLerp, Func(self.ghostPowerup), growPowerupLerp, bouncePowerupLerp, name='%s.pickUpSeq-%s' % (self.__class__.__name__, self.serialNum))

    def isPowerUp(self):
        return True

    def updateLerpStartScale(self, lerp, nodepath):
        lerp.setStartScale(nodepath.getScale())

    def wasPickedUpByToon(self, toon):
        if toon.doId in self._pickedUpList:
            return True
        return False

    def ghostPowerup(self):
        if self._isToonLocal:
            self._model.setAlphaScale(0.5)
            if Globals.Level.AddSparkleToPowerups:
                self.f = self.find('**/particleEffect_sparkles')
                self.f.hide()

    def pickUp(self, toon, elapsedSeconds = 0.0):
        if self.wasPickedUpByToon(toon) == True:
            return
        self._pickedUpList.append(toon.doId)
        self._isToonLocal = toon.isLocal()
        if self._animate:
            self.pickUpSeq.clearToInitial()
            self.pickUpSeq.start()
        else:
            self.ghostPowerup()

    def destroy(self):
        del self._pickedUpList[:]
        self.pickUpSeq.clearToInitial()
        del self.pickUpSeq
        CogdoFlyingGatherable.destroy(self)

    def update(self, dt):
        self._model.setH(self._model.getH() + Globals.Gameplay.MemoSpinRate * dt)


class CogdoFlyingPropeller(CogdoFlyingGatherable):

    def __init__(self, serialNum, model):
        CogdoFlyingGatherable.__init__(self, Globals.Level.GatherableTypes.Propeller, serialNum, model, Globals.Gameplay.PropellerCollisionRadius, animate=False)
        self.activePropellers = []
        self.usedPropellers = []
        propellers = self._model.findAllMatches('**/propeller*')
        for prop in propellers:
            self.activePropellers.append(prop)

        self.initIntervals()

    def initIntervals(self):
        self.animatedPropellerIval = Parallel(name='%s.object-%i-animatePropellerIval' % (self.__class__.__name__, self.serialNum))
        for propeller in self.activePropellers:
            self.animatedPropellerIval.append(LerpHprInterval(propeller, duration=Globals.Level.PropellerSpinDuration, startHpr=Vec3(0.0, 0.0, 0.0), hpr=Vec3(360.0, 0.0, 0.0)))

    def show(self):
        self.animatedPropellerIval.loop()
        CogdoFlyingGatherable.show(self)

    def hide(self):
        self.animatedPropellerIval.clearToInitial()
        CogdoFlyingGatherable.hide(self)

    def destroy(self):
        taskMgr.removeTasksMatching('propeller-respawn-*')
        self.animatedPropellerIval.clearToInitial()
        del self.animatedPropellerIval
        CogdoFlyingGatherable.destroy(self)

    def pickUp(self, toon, elapsedSeconds = 0.0):
        prop = self.removePropeller()
        if prop != None:
            respawnTime = Globals.Gameplay.PropellerRespawnTime
            if elapsedSeconds < respawnTime:
                taskMgr.doMethodLater(respawnTime - elapsedSeconds, self.addPropeller, 'propeller-respawn-%i' % self.serialNum, extraArgs=[prop])
            else:
                self.addPropeller(prop)
        else:
            self.disable()
        return

    def addPropeller(self, prop):
        if len(self.usedPropellers) > 0:
            if len(self.activePropellers) == 0:
                self.enable()
            self.usedPropellers.remove(prop)
            prop.show()
            self.activePropellers.append(prop)
            self._wasPickedUp = False

    def removePropeller(self):
        if len(self.activePropellers) > 0:
            prop = self.activePropellers.pop()
            prop.hide()
            self.usedPropellers.append(prop)
            if len(self.activePropellers) == 0:
                self._wasPickedUp = True
            return prop
        return None

    def isPropeller(self):
        if len(self.activePropellers) > 0:
            return True
        else:
            return False


class CogdoFlyingLevelFog:

    def __init__(self, level, color = Globals.Level.FogColor):
        self._level = level
        self.color = color
        fogDistance = self._level.quadLengthUnits * max(1, self._level.quadVisibiltyAhead * 0.2)
        self.fog = Fog('RenderFog')
        self.fog.setColor(self.color)
        self.fog.setLinearRange(fogDistance * Globals.Level.RenderFogStartFactor, fogDistance)
        self._visible = False
        self._clearColor = Vec4(base.win.getClearColor())
        self._clearColor.setW(1.0)

    def destroy(self):
        self.setVisible(False)
        if hasattr(self, 'fog'):
            del self.fog

    def isVisible(self):
        return self._visible

    def setVisible(self, visible):
        self._visible = visible
        if self._visible:
            base.win.setClearColor(self.color)
            render.setFog(self.fog)
        else:
            base.win.setClearColor(self._clearColor)
            render.clearFog()


class CogdoFlyingPlatform:
    CeilingCollName = 'col_ceiling'
    FloorCollName = 'col_floor'

    def __init__(self, model, type = Globals.Level.PlatformTypes.Platform, parent = None):
        self._model = model
        self._type = type
        if parent is not None:
            self._model.reparentTo(parent)
        self._initCollisions()
        return

    def __str__(self):
        return '<%s model=%s, type=%s>' % (self.__class__.__name__, self._model, self._type)

    def destroy(self):
        self._floorColl.clearPythonTag('platform')
        self._model.removeNode()
        del self._model
        del self._type
        del self._floorColl
        del self._ceilingColl

    def onstage(self):
        self._model.unstash()

    def offstage(self):
        self._model.stash()

    def _initCollisions(self):
        self._floorColl = self._model.find('**/*%s' % CogdoFlyingPlatform.FloorCollName)
        self._floorColl.setName(CogdoFlyingPlatform.FloorCollName)
        self._floorColl.node().setIntoCollideMask(ToontownGlobals.FloorEventBitmask | OTPGlobals.FloorBitmask)
        self._floorColl.setPythonTag('platform', self)
        self._ceilingColl = self._model.find('**/*%s' % CogdoFlyingPlatform.CeilingCollName)
        self._ceilingColl.setName(CogdoFlyingPlatform.CeilingCollName)
        self._ceilingColl.node().setIntoCollideMask(ToontownGlobals.CeilingBitmask)

    def getType(self):
        return self._type

    def getName(self):
        return self._model.getName()

    def getModel(self):
        return self._model

    def isStartPlatform(self):
        return self._type == Globals.Level.PlatformTypes.StartPlatform

    def isEndPlatform(self):
        return self._type == Globals.Level.PlatformTypes.EndPlatform

    def isStartOrEndPlatform(self):
        return self.isStartPlatform() or self.isEndPlatform()

    def getSpawnPosForPlayer(self, playerNum, parent):
        offset = Globals.Level.PlatformType2SpawnOffset[self._type]
        spawnLoc = self._model.find('**/spawn_loc')
        x = (playerNum - 2.0) % 2 * offset
        y = (playerNum - 1.0) % 2 * offset
        if not spawnLoc.isEmpty():
            spawnPos = spawnLoc.getPos(parent) + Vec3(x, y, 0.0)
        else:
            spawnPos = self._floorColl.getPos(parent) + Vec3(x, y, 0.0)
        return spawnPos

    @staticmethod
    def getFromNode(node):
        return node.getPythonTag('platform')
