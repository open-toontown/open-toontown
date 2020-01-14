from direct.interval.IntervalGlobal import *
from direct.particles import ParticleEffect
from direct.particles import Particles
from direct.particles import ForceGroup
from pandac.PandaModules import *
import random
from .FireworkGlobals import *
colors = {WHITE: Vec4(1, 1, 1, 1),
 RED: Vec4(1, 0.2, 0.2, 1),
 BLUE: Vec4(0.2, 0.2, 1, 1),
 YELLOW: Vec4(1, 1, 0.2, 1),
 GREEN: Vec4(0.2, 1, 0.2, 1),
 PINK: Vec4(1, 0.5, 0.5, 1),
 PEACH: Vec4(0.9, 0.6, 0.4, 1),
 PURPLE: Vec4(1, 0.1, 1, 1),
 CYAN: Vec4(0.2, 1, 1, 1)}
textures = {SNOWFLAKE: 'phase_8/models/props/snowflake_treasure',
 MUSICNOTE: 'phase_6/models/props/music_treasure',
 FLOWER: 'phase_8/models/props/flower_treasure',
 ICECREAM: 'phase_4/models/props/icecream',
 STARFISH: 'phase_6/models/props/starfish_treasure',
 ZZZ: 'phase_8/models/props/zzz_treasure'}
fireworkId = 0

def getNextSequenceName(name):
    global fireworkId
    fireworkId += 1
    return '%s-%s' % (name, fireworkId)


def getColor(colorIndex):
    return colors.get(colorIndex)


def getTexture(textureIndex):
    return loader.loadModel(textures.get(textureIndex))


def shootFirework(style, x = 0, y = 0, z = 0, colorIndex1 = 0, colorIndex2 = 0, amp = 10):
    func = style2shootFunc.get(style)
    color1 = getColor(colorIndex1)
    if style is CIRCLESPRITE:
        color2 = getTexture(colorIndex2)
    else:
        color2 = getColor(colorIndex2)
    if func and color1 and color2:
        return func(x, y, z, color1, color2, amp)


def shootFireworkRing(x, y, z, color1, color2, amp):
    f = ParticleEffect.ParticleEffect()
    p0 = Particles.Particles('particles-1')
    p0.setFactory('PointParticleFactory')
    p0.setRenderer('SparkleParticleRenderer')
    p0.setEmitter('RingEmitter')
    p0.setPoolSize(100)
    p0.setBirthRate(0.01)
    p0.setLitterSize(100)
    p0.setLitterSpread(0)
    p0.factory.setLifespanBase(1.5)
    p0.factory.setLifespanSpread(0.5)
    p0.factory.setMassBase(1.0)
    p0.factory.setMassSpread(0.0)
    p0.factory.setTerminalVelocityBase(20.0)
    p0.factory.setTerminalVelocitySpread(2.0)
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
    f0 = ForceGroup.ForceGroup('gravity')
    force0 = LinearSourceForce(Point3(x, y, z), LinearDistanceForce.FTONEOVERR, 0.1, 1.1 * amp, 1)
    force0.setActive(1)
    f0.addForce(force0)
    force1 = LinearSinkForce(Point3(x, y, z), LinearDistanceForce.FTONEOVERR, 0.5, 2.0 * amp, 1)
    force1.setActive(1)
    f0.addForce(force1)
    f.addForceGroup(f0)
    p0.emitter.setRadius(4.0)
    f.addParticles(p0)
    f.setPos(x, y, z)
    f.setHpr(0, random.random() * 180, random.random() * 180)
    sfx = loader.loadSfx('phase_4/audio/sfx/firework_distance_03.ogg')
    t = Sequence(Func(f.start, render, render), Func(sfx.play), Wait(0.5), Func(p0.setBirthRate, 3), Wait(1.5), Func(f.cleanup), name=getNextSequenceName('shootFireworkRing'))
    t.start()


def shootFireworkRocket(x, y, z, color1, color2, amp):
    f = ParticleEffect.ParticleEffect()
    p0 = Particles.Particles('particles-1')
    p0.setFactory('PointParticleFactory')
    p0.setRenderer('SparkleParticleRenderer')
    p0.setEmitter('SphereVolumeEmitter')
    p0.setPoolSize(110)
    p0.setBirthRate(0.01)
    p0.setLitterSize(2)
    p0.setLitterSpread(0)
    p0.factory.setLifespanBase(0.4)
    p0.factory.setLifespanSpread(0.1)
    p0.factory.setMassBase(1.0)
    p0.factory.setMassSpread(0.0)
    p0.factory.setTerminalVelocityBase(400.0)
    p0.factory.setTerminalVelocitySpread(0.0)
    p0.renderer.setAlphaMode(BaseParticleRenderer.PRALPHAOUT)
    p0.renderer.setUserAlpha(1.0)
    p0.renderer.setCenterColor(color1)
    p0.renderer.setEdgeColor(color2)
    p0.renderer.setBirthRadius(0.6)
    p0.renderer.setDeathRadius(0.6)
    p0.renderer.setLifeScale(SparkleParticleRenderer.SPNOSCALE)
    p0.emitter.setEmissionType(BaseParticleEmitter.ETRADIATE)
    p0.emitter.setAmplitude(amp)
    p0.emitter.setAmplitudeSpread(0.0)
    p0.emitter.setRadius(0.3)
    f.addParticles(p0)
    gravityForceGroup = ForceGroup.ForceGroup('gravity')
    force0 = LinearVectorForce(Vec3(0.0, 0.0, -10.0), 1.0, 0)
    force0.setActive(1)
    gravityForceGroup.addForce(force0)
    f.addForceGroup(gravityForceGroup)
    f.setPos(x, y, z)
    sfxName = random.choice(('phase_4/audio/sfx/firework_whistle_01.ogg', 'phase_4/audio/sfx/firework_whistle_02.ogg'))
    sfx = loader.loadSfx(sfxName)
    t = Sequence(Func(f.start, render, render), Func(sfx.play), LerpPosInterval(f, 2.0, Vec3(x, y, z + 20 * amp), blendType='easeInOut'), Func(p0.setBirthRate, 3), Wait(0.5), Func(f.cleanup), name=getNextSequenceName('shootFirework'))
    t.start()


def shootPop(x, y, z, color1, color2, amp):
    sfxName = random.choice(('phase_4/audio/sfx/firework_distance_01.ogg', 'phase_4/audio/sfx/firework_distance_02.ogg', 'phase_4/audio/sfx/firework_distance_03.ogg'))
    sfx = loader.loadSfx(sfxName)
    t = Sequence(Func(sfx.play), Wait(3), name=getNextSequenceName('shootFireworkRocket'))
    t.start()


def shootFireworkCircle(x, y, z, color1, color2, amp):
    return shootFireworkCircleGeneric(x, y, z, color1, color2, amp, 100)


def shootFireworkCircleLarge(x, y, z, color1, color2, amp):
    return shootFireworkCircleGeneric(x, y, z, color1, color2, amp * 1.5, 200)


def shootFireworkCircleSmall(x, y, z, color1, color2, amp):
    return shootFireworkCircleGeneric(x, y, z, color1, color2, amp * 0.5, 50)


def shootFireworkCircleGeneric(x, y, z, color1, color2, amp, poolSize):
    f = ParticleEffect.ParticleEffect()
    p0 = Particles.Particles('particles-1')
    p0.setFactory('PointParticleFactory')
    p0.setRenderer('SparkleParticleRenderer')
    p0.setEmitter('SphereVolumeEmitter')
    p0.setPoolSize(poolSize)
    p0.setBirthRate(0.01)
    p0.setLitterSize(poolSize)
    p0.factory.setLifespanBase(2.0)
    p0.factory.setLifespanSpread(0.5)
    p0.factory.setTerminalVelocityBase(400.0)
    p0.factory.setTerminalVelocitySpread(40.0)
    p0.renderer.setAlphaMode(BaseParticleRenderer.PRALPHAOUT)
    p0.renderer.setUserAlpha(1.0)
    p0.renderer.setCenterColor(color1)
    p0.renderer.setEdgeColor(color1)
    p0.renderer.setBirthRadius(0.4)
    p0.renderer.setDeathRadius(0.6)
    p0.renderer.setLifeScale(SparkleParticleRenderer.SPSCALE)
    p0.emitter.setEmissionType(BaseParticleEmitter.ETRADIATE)
    p0.emitter.setAmplitudeSpread(0.1)
    p0.emitter.setAmplitude(amp)
    p0.emitter.setRadius(0.1)
    f.addParticles(p0)
    circleForceGroup = ForceGroup.ForceGroup('gravity')
    force1 = LinearSinkForce(Point3(x, y, z - 100), LinearDistanceForce.FTONEOVERRSQUARED, 2.0, 0.3 * amp * 0.1, 1)
    force1.setActive(1)
    circleForceGroup.addForce(force1)
    f.addForceGroup(circleForceGroup)
    f.setPos(x, y, z)
    sfxName = random.choice(('phase_4/audio/sfx/firework_explosion_01.ogg', 'phase_4/audio/sfx/firework_explosion_02.ogg', 'phase_4/audio/sfx/firework_explosion_03.ogg'))
    sfx = loader.loadSfx(sfxName)
    t = Sequence(Func(f.start, render, render), Func(sfx.play), Wait(0.5), Func(p0.setBirthRate, 3), Wait(0.5), Func(p0.renderer.setCenterColor, color2), Func(p0.renderer.setEdgeColor, color2), Wait(1.5), Func(f.cleanup), name=getNextSequenceName('shootFireworkCircle'))
    t.start()


def shootFireworkCircleSprite(x, y, z, color, texture, amp):
    f = ParticleEffect.ParticleEffect()
    p0 = Particles.Particles('particles-1')
    p0.setFactory('PointParticleFactory')
    p0.setRenderer('SpriteParticleRenderer')
    p0.setEmitter('SphereVolumeEmitter')
    p0.setPoolSize(100)
    p0.setBirthRate(0.01)
    p0.setLitterSize(100)
    p0.factory.setLifespanBase(2.0)
    p0.factory.setLifespanSpread(0.5)
    p0.factory.setTerminalVelocityBase(400.0)
    p0.factory.setTerminalVelocitySpread(40.0)
    p0.renderer.setAlphaMode(BaseParticleRenderer.PRALPHAUSER)
    p0.renderer.setUserAlpha(1.0)
    p0.renderer.setFromNode(texture)
    p0.renderer.setColor(color)
    p0.renderer.setXScaleFlag(1)
    p0.renderer.setYScaleFlag(1)
    p0.renderer.setInitialXScale(0.12)
    p0.renderer.setFinalXScale(0.48)
    p0.renderer.setInitialYScale(0.12)
    p0.renderer.setFinalYScale(0.48)
    p0.emitter.setEmissionType(BaseParticleEmitter.ETRADIATE)
    p0.emitter.setAmplitudeSpread(0.1)
    p0.emitter.setAmplitude(amp)
    p0.emitter.setRadius(0.1)
    f.addParticles(p0)
    circleForceGroup = ForceGroup.ForceGroup('gravity')
    force1 = LinearSinkForce(Point3(x, y, z - 100), LinearDistanceForce.FTONEOVERRSQUARED, 2.0, 0.3 * amp * 0.1, 1)
    force1.setActive(1)
    circleForceGroup.addForce(force1)
    f.addForceGroup(circleForceGroup)
    f.setPos(x, y, z)
    sfxName = random.choice(('phase_4/audio/sfx/firework_explosion_01.ogg', 'phase_4/audio/sfx/firework_explosion_02.ogg', 'phase_4/audio/sfx/firework_explosion_03.ogg'))
    sfx = loader.loadSfx(sfxName)
    t = Sequence(Func(f.start, render, render), Func(sfx.play), Wait(0.5), Func(p0.setBirthRate, 3), Wait(2.0), Func(f.cleanup), name=getNextSequenceName('shootFireworkSprite'))
    t.start()


style2shootFunc = {CIRCLE: shootFireworkCircle,
 CIRCLELARGE: shootFireworkCircleLarge,
 CIRCLESMALL: shootFireworkCircleSmall,
 CIRCLESPRITE: shootFireworkCircleSprite,
 ROCKET: shootFireworkRocket,
 RING: shootFireworkRing,
 POP: shootPop}
