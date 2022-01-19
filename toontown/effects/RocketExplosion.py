from panda3d.core import *
from direct.particles import ParticleEffect
from direct.directnotify import DirectNotifyGlobal
from direct.interval.IntervalGlobal import *

class RocketExplosion(NodePath):

    def __init__(self, parent, smokeParent):
        NodePath.__init__(self)
        notify = DirectNotifyGlobal.directNotify.newCategory('RocketExplosionParticles')
        self.effectNode = parent.attachNewNode('RocketExplosion')
        self.effectNode.setBin('fixed', 1)
        self.effectNode.setDepthWrite(1)
        self.smokeEffectNode = smokeParent.attachNewNode('RocketSmoke')
        self.smokeEffectNode.setBin('fixed', 1)
        self.smokeEffectNode.setDepthWrite(0)
        self.effect = ParticleEffect.ParticleEffect('RocketFire')
        self.smokeEffect = ParticleEffect.ParticleEffect('RocketSmoke')
        particleSearchPath = DSearchPath()
        if __debug__:
            particleSearchPath.appendDirectory(Filename('resources/phase_3.5/etc'))
            particleSearchPath.appendDirectory(Filename('resources/phase_4/etc'))
            particleSearchPath.appendDirectory(Filename('resources/phase_5/etc'))
            particleSearchPath.appendDirectory(Filename('resources/phase_6/etc'))
            particleSearchPath.appendDirectory(Filename('resources/phase_7/etc'))
            particleSearchPath.appendDirectory(Filename('resources/phase_8/etc'))
            particleSearchPath.appendDirectory(Filename('resources/phase_9/etc'))
        pfile = Filename('tt_p_efx_rocketLaunchFire.ptf')
        found = vfs.resolveFilename(pfile, particleSearchPath)
        if not found:
            notify.warning('loadParticleFile() - no path: %s' % pfile)
            return
        notify.debug('Loading particle file: %s' % pfile)
        self.effect.loadConfig(pfile)
        ren = self.effect.getParticlesNamed('particles-1').getRenderer()
        ren.setTextureFromNode('phase_4/models/props/tt_m_efx_fireball', '**/*')
        pfile = Filename('tt_p_efx_rocketLaunchSmoke.ptf')
        found = vfs.resolveFilename(pfile, particleSearchPath)
        if not found:
            notify.warning('loadParticleFile() - no path: %s' % pfile)
            return
        notify.debug('Loading particle file: %s' % pfile)
        self.smokeEffect.loadConfig(pfile)
        ren = self.smokeEffect.getParticlesNamed('particles-1').getRenderer()
        ren.setTextureFromNode('phase_4/models/props/tt_m_efx_smoke', '**/*')
        self.endSeq = None
        self.cleanupCompleted = 0
        return

    def start(self):
        self.effect.start(parent=self.effectNode)
        self.smokeEffect.start(parent=self.smokeEffectNode)

    def stop(self):
        try:
            self.effect.disable()
            self.smokeEffect.disable()
        except AttributeError:
            pass

    def end(self):
        self.endSeq = Sequence(LerpColorScaleInterval(self.smokeEffectNode, 2.0, Vec4(1, 1, 1, 0)), Func(self.destroy))
        self.endSeq.start()

    def destroy(self):
        if self.endSeq:
            self.endSeq.pause()
            self.endSeq = None
        self.stop()
        if not self.cleanupCompleted:
            self.effect.cleanup()
            self.smokeEffect.cleanup()
            self.effectNode.removeNode()
            self.smokeEffectNode.removeNode()
            del self.effect
            del self.smokeEffect
            del self.effectNode
            del self.smokeEffectNode
            self.cleanupCompleted = 1
        return
