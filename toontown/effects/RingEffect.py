from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *
from direct.particles import ParticleEffect, Particles, ForceGroup
from .EffectController import EffectController
from .PooledEffect import PooledEffect
import random

class RingEffect(PooledEffect, EffectController):

    def __init__(self):
        PooledEffect.__init__(self)
        EffectController.__init__(self)
        model = loader.loadModel('phase_4/models/props/tt_m_efx_ext_fireworkCards')
        self.card = model.find('**/tt_t_efx_ext_particleSpark_soft')
        self.cardScale = 16.0
        self.effectModel = model.find('**/tt_t_efx_ext_particleStars')
        self.effectModel.reparentTo(self)
        self.effectModel.setColorScale(0, 0, 0, 0)
        self.setAttrib(ColorBlendAttrib.make(ColorBlendAttrib.MAdd, ColorBlendAttrib.OIncomingAlpha, ColorBlendAttrib.OOne))
        self.setBillboardPointWorld()
        self.setDepthWrite(0)
        self.setLightOff()
        self.setFogOff()
        self.effectScale = 1.0
        self.effectColor = Vec4(1, 1, 1, 1)
        self.f = ParticleEffect.ParticleEffect('RingEffect')
        self.f.reparentTo(self)
        self.p0 = Particles.Particles('particles-2')
        self.p0.setFactory('PointParticleFactory')
        self.p0.setRenderer('SpriteParticleRenderer')
        self.p0.setEmitter('RingEmitter')
        self.f.addParticles(self.p0)
        f0 = ForceGroup.ForceGroup('Gravity')
        force0 = LinearVectorForce(Vec3(0.0, 0.0, -15.0), 1.0, 0)
        force0.setVectorMasks(1, 1, 1)
        force0.setActive(1)
        f0.addForce(force0)
        self.f.addForceGroup(f0)
        f1 = ForceGroup.ForceGroup('Noise')
        force1 = LinearNoiseForce(2.5, 0.0)
        force1.setVectorMasks(1, 1, 1)
        force1.setActive(1)
        f1.addForce(force1)
        self.f.addForceGroup(f1)
        self.p0.setPoolSize(16)
        self.p0.setBirthRate(0.1)
        self.p0.setLitterSize(16)
        self.p0.setLitterSpread(0)
        self.p0.setSystemLifespan(0.0)
        self.p0.setLocalVelocityFlag(1)
        self.p0.setSystemGrowsOlderFlag(0)
        self.p0.factory.setLifespanBase(1.0)
        self.p0.factory.setLifespanSpread(0.2)
        self.p0.factory.setMassBase(1.0)
        self.p0.factory.setMassSpread(0.0)
        self.p0.factory.setTerminalVelocityBase(400.0)
        self.p0.factory.setTerminalVelocitySpread(0.0)
        self.p0.renderer.setAlphaMode(BaseParticleRenderer.PRALPHAINOUT)
        self.p0.renderer.setUserAlpha(1.0)
        self.p0.renderer.setColorBlendMode(ColorBlendAttrib.MAdd, ColorBlendAttrib.OIncomingAlpha, ColorBlendAttrib.OOne)
        self.p0.renderer.setFromNode(self.card)
        self.p0.renderer.setColor(Vec4(1.0, 1.0, 1.0, 1.0))
        self.p0.renderer.setXScaleFlag(1)
        self.p0.renderer.setYScaleFlag(1)
        self.p0.renderer.setAnimAngleFlag(0)
        self.p0.renderer.setNonanimatedTheta(0.0)
        self.p0.renderer.setAlphaBlendMethod(BaseParticleRenderer.PPBLENDLINEAR)
        self.p0.renderer.setAlphaDisable(0)
        self.p0.emitter.setEmissionType(BaseParticleEmitter.ETRADIATE)
        self.p0.emitter.setAmplitudeSpread(0.0)
        self.p0.emitter.setOffsetForce(Vec3(0.0, 0.0, 0.0))
        self.p0.emitter.setExplicitLaunchVector(Vec3(1.0, 0.0, 0.0))
        self.p0.emitter.setRadiateOrigin(Point3(0.0, 0.0, 0.0))
        self.p0.emitter.setUniformEmission(16)
        self.setEffectScale(self.effectScale)
        self.setEffectColor(self.effectColor)

    def createTrack(self):
        self.f.setP(random.randint(50, 100))
        self.effectModel.setR(random.randint(0, 90))
        self.effectModel.setPos(random.randint(-20, 20), random.randint(-20, 20), random.randint(-20, 20))
        fadeBlast = self.effectModel.colorScaleInterval(1.0, Vec4(0, 0, 0, 0), startColorScale=Vec4(self.effectColor), blendType='easeIn')
        scaleBlast = self.effectModel.scaleInterval(1.0, 75 * self.effectScale, startScale=50 * self.effectScale, blendType='easeOut')
        self.track = Sequence(Func(self.p0.setBirthRate, 0.15), Func(self.p0.clearToInitial), Func(self.f.start, self, self), Parallel(fadeBlast, scaleBlast), Func(self.p0.setBirthRate, 100.0), Wait(3.0), Func(self.cleanUpEffect))

    def setEffectScale(self, scale):
        self.effectScale = scale
        self.p0.renderer.setInitialXScale(1.4 * self.cardScale * scale)
        self.p0.renderer.setFinalXScale(1.2 * self.cardScale * scale)
        self.p0.renderer.setInitialYScale(1.4 * self.cardScale * scale)
        self.p0.renderer.setFinalYScale(1.2 * self.cardScale * scale)
        self.p0.emitter.setAmplitude(75.0 * scale)
        self.p0.emitter.setRadius(200.0 * scale)

    def setRadius(self, radius):
        self.p0.emitter.setRadius(radius)

    def setEffectColor(self, color):
        self.effectColor = color
        self.p0.renderer.setColor(self.effectColor)

    def cleanUpEffect(self):
        EffectController.cleanUpEffect(self)
        if self.pool and self.pool.isUsed(self):
            self.pool.checkin(self)

    def destroy(self):
        EffectController.destroy(self)
        PooledEffect.destroy(self)
