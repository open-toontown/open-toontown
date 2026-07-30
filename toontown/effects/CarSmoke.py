from panda3d.core import *
from direct.particles import ParticleEffect
from direct.directnotify import DirectNotifyGlobal
from direct.showbase import AppRunnerGlobal
import os

class CarSmoke(NodePath):

    def __init__(self, parent):
        NodePath.__init__(self)
        notify = DirectNotifyGlobal.directNotify.newCategory('CarSmokeParticles')
        self.effectNode = parent.attachNewNode('carSmoke')
        self.effectNode.setBin('fixed', 1)
        self.effectNode.setDepthWrite(0)
        self.effect = ParticleEffect.ParticleEffect()
        particleSearchPath = DSearchPath()
        if AppRunnerGlobal.appRunner:
            particleSearchPath.appendDirectory(Filename.expandFrom('$TT_3_5_ROOT/phase_3.5/etc'))
        else:
            basePath = os.path.expandvars('$TOONTOWN') or './toontown'
            particleSearchPath.appendDirectory(Filename.fromOsSpecific(basePath + '/src/effects'))
            particleSearchPath.appendDirectory(Filename('phase_3.5/etc'))
            particleSearchPath.appendDirectory(Filename('phase_4/etc'))
            particleSearchPath.appendDirectory(Filename('phase_5/etc'))
            particleSearchPath.appendDirectory(Filename('phase_6/etc'))
            particleSearchPath.appendDirectory(Filename('phase_7/etc'))
            particleSearchPath.appendDirectory(Filename('phase_8/etc'))
            particleSearchPath.appendDirectory(Filename('phase_9/etc'))
            particleSearchPath.appendDirectory(Filename('.'))
        pfile = Filename('smokeTest4.ptf')
        found = vfs.resolveFilename(pfile, particleSearchPath)
        if not found:
            notify.warning('loadParticleFile() - no path: %s' % pfile)
            return
        notify.debug('Loading particle file: %s' % pfile)
        self.effect.loadConfig(pfile)
        ren = self.effect.getParticlesNamed('particles-1').getRenderer()
        ren.setTextureFromNode('phase_4/models/props/tt_m_efx_ext_smoke', '**/*')

    def start(self):
        self.effect.start(parent=self.effectNode)

    def stop(self):
        try:
            self.effect.disable()
        except AttributeError:
            pass

    def destroy(self):
        self.stop()
        self.effect.cleanup()
        self.effectNode.removeNode()
        del self.effect
        del self.effectNode
