from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *
import SafeZoneLoader
import BRPlayground
from toontown.battle import BattleParticles

class BRSafeZoneLoader(SafeZoneLoader.SafeZoneLoader):
    SnowFadeLerpTime = 2.0

    def __init__(self, hood, parentFSM, doneEvent):
        SafeZoneLoader.SafeZoneLoader.__init__(self, hood, parentFSM, doneEvent)
        self.playgroundClass = BRPlayground.BRPlayground
        self.musicFile = 'phase_8/audio/bgm/TB_nbrhood.mid'
        self.activityMusicFile = 'phase_8/audio/bgm/TB_SZ_activity.mid'
        self.dnaFile = 'phase_8/dna/the_burrrgh_sz.dna'
        self.safeZoneStorageDNAFile = 'phase_8/dna/storage_BR_sz.dna'

    def load(self):
        SafeZoneLoader.SafeZoneLoader.load(self)
        self.wind1Sound = base.loadSfx('phase_8/audio/sfx/SZ_TB_wind_1.mp3')
        self.wind2Sound = base.loadSfx('phase_8/audio/sfx/SZ_TB_wind_2.mp3')
        self.wind3Sound = base.loadSfx('phase_8/audio/sfx/SZ_TB_wind_3.mp3')
        self.snow = BattleParticles.loadParticleFile('snowdisk.ptf')
        self.snow.setPos(0, 0, 5)
        self.snowRender = self.geom.attachNewNode('snowRender')
        self.snowRender.setDepthWrite(0)
        self.snowRender.setBin('fixed', 1)
        self.snowFade = None
        return

    def unload(self):
        del self.wind1Sound
        del self.wind2Sound
        del self.wind3Sound
        del self.snow
        del self.snowRender
        SafeZoneLoader.SafeZoneLoader.unload(self)

    def enter(self, requestStatus):
        SafeZoneLoader.SafeZoneLoader.enter(self, requestStatus)
        self.snow.start(camera, self.snowRender)
        self.accept('enterigloo-interior', self.enterIgloo)
        self.accept('exitigloo-interior', self.exitIgloo)

    def exit(self):
        self.ignore('enterigloo-interior')
        self.ignore('exitigloo-interior')
        self.resetSnowLerp()
        self.snow.cleanup()
        SafeZoneLoader.SafeZoneLoader.exit(self)

    def enterIgloo(self, entry):
        self.fadeOutSnow()

    def exitIgloo(self, entry):
        self.fadeInSnow()

    def resetSnowLerp(self):
        if self.snowFade != None:
            self.snowFade.stop()
            self.snowFade = None
        return

    def fadeInSnow(self):
        self.resetSnowLerp()
        currentScale = self.snowRender.getColorScale()[3]
        ivals = [LerpFunctionInterval(self.snowRender.setAlphaScale, fromData=currentScale, toData=1.0, duration=self.SnowFadeLerpTime), FunctionInterval(self.snowRender.clearColorScale)]
        self.snowFade = Track(ivals, 'snow-fade')
        self.snowFade.play()

    def fadeOutSnow(self):
        self.resetSnowLerp()
        currentScale = self.snowRender.getColorScale()[3]
        ivals = [LerpFunctionInterval(self.snowRender.setAlphaScale, fromData=currentScale, toData=0.0, duration=self.SnowFadeLerpTime)]
        self.snowFade = Track(ivals, 'snow-fade')
        self.snowFade.play()
