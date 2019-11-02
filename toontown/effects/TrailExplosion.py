from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *
from EffectController import EffectController
from PooledEffect import PooledEffect
from toontown.effects.SparksTrailLong import SparksTrailLong
import random

class TrailExplosion(PooledEffect, EffectController):
    trailsVel = [[Vec3(150, -50, 100), Vec3(-150, -50, 100), Vec3(0, 150, 100)], [Vec3(120, 120, 100),
      Vec3(120, -120, 100),
      Vec3(-120, 120, 100),
      Vec3(-120, -120, 100)], [Vec3(0, 150, 100),
      Vec3(140, 30, 100),
      Vec3(-140, 30, 100),
      Vec3(30, -60, 100),
      Vec3(-30, -60, 100)]]

    def __init__(self):
        PooledEffect.__init__(self)
        EffectController.__init__(self)
        self.effectScale = 1.0
        self.effectColor = Vec4(1, 1, 1, 1)
        self.numTrails = 5
        self.trails = []
        self.trailEffects = []
        self.trailIval = Parallel()

    def createTrack(self):
        self.trails = []
        self.trailEffects = []
        self.trailIval = Parallel()
        vels = None
        if self.numTrails >= 3 and self.numTrails <= 5:
            vels = self.trailsVel[self.numTrails - 3]
        for i in range(self.numTrails):
            self.trails.append(self.attachNewNode('trail'))
            vel = Vec3(0, 0, 0)
            if vels:
                vel = Vec3(vels[i][0] + random.randint(-20, 20), vels[i][1] + random.randint(-20, 20), vels[i][2] + random.randint(0, 50))
            else:
                vel = Vec3(random.randint(-200, 200), random.randint(-200, 200), random.randint(80, 150))
            vel *= self.effectScale
            dur = 2.0 + random.random() / 4.0
            self.trailIval.append(ProjectileInterval(self.trails[i], startVel=vel, duration=dur, gravityMult=0.6))
            self.trailEffects.append(SparksTrailLong.getEffect())
            if self.trailEffects[i]:
                self.trailEffects[i].reparentTo(self.trails[i])
                self.trailEffects[i].setLifespan(2.0)
                self.trailEffects[i].setEffectColor(self.effectColor)
                self.trailEffects[i].setEffectScale(self.effectScale)
                self.trailIval.append(Sequence(Func(self.trailEffects[i].startLoop), Wait(dur), Func(self.trailEffects[i].stopLoop)))

        self.track = Sequence(self.trailIval, Func(self.cleanUpEffect))
        return

    def setEffectScale(self, scale):
        self.effectScale = scale

    def setEffectColor(self, color):
        self.effectColor = color

    def cleanUpEffect(self):
        for effect in self.trailEffects:
            if effect:
                effect.stopLoop()
                effect = None

        EffectController.cleanUpEffect(self)
        if self.pool and self.pool.isUsed(self):
            self.pool.checkin(self)
        return

    def destroy(self):
        EffectController.destroy(self)
        PooledEffect.destroy(self)
