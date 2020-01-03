from pandac.PandaModules import *
from direct.particles import ParticleEffect
from direct.directnotify import DirectNotifyGlobal
import os

class Drift(NodePath):

    def __init__(self, parent, renderParent):
        NodePath.__init__(self)
        notify = DirectNotifyGlobal.directNotify.newCategory('DriftParticles')
        self.renderParent = renderParent.attachNewNode('driftRenderParent')
        self.renderParent.setBin('fixed', 0)
        self.renderParent.setDepthWrite(0)
        self.assign(parent.attachNewNode('drift'))
        self.effect = ParticleEffect.ParticleEffect()
        particleSearchPath = DSearchPath()
        if __debug__:
            particleSearchPath.appendDirectory(Filename('resources/phase_3.5/etc'))
            particleSearchPath.appendDirectory(Filename('resources/phase_4/etc'))
            particleSearchPath.appendDirectory(Filename('resources/phase_5/etc'))
            particleSearchPath.appendDirectory(Filename('resources/phase_6/etc'))
            particleSearchPath.appendDirectory(Filename('resources/phase_7/etc'))
            particleSearchPath.appendDirectory(Filename('resources/phase_8/etc'))
            particleSearchPath.appendDirectory(Filename('resources/phase_9/etc'))
        pfile = Filename('drift.ptf')
        found = vfs.resolveFilename(pfile, particleSearchPath)
        if not found:
            notify.warning('loadParticleFile() - no path: %s' % pfile)
            return
        notify.debug('Loading particle file: %s' % pfile)
        self.effect.loadConfig(pfile)
        ren = self.effect.getParticlesNamed('particles-1').getRenderer()
        ren.setTextureFromNode('phase_6/models/karting/driftSmoke', '**/*')

    def start(self):
        self.effect.start(self, self.renderParent)

    def stop(self):
        self.effect.disable()

    def destroy(self):
        self.stop()
        self.effect.cleanup()
        self.renderParent.removeNode()
        del self.effect
        del self.renderParent
