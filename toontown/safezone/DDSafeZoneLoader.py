from pandac.PandaModules import *
import SafeZoneLoader
import DDPlayground
from direct.fsm import State
from toontown.char import CharDNA
from toontown.char import Char
from toontown.toonbase import ToontownGlobals

class DDSafeZoneLoader(SafeZoneLoader.SafeZoneLoader):

    def __init__(self, hood, parentFSM, doneEvent):
        SafeZoneLoader.SafeZoneLoader.__init__(self, hood, parentFSM, doneEvent)
        self.playgroundClass = DDPlayground.DDPlayground
        self.musicFile = 'phase_6/audio/bgm/DD_nbrhood.mid'
        self.activityMusicFile = 'phase_6/audio/bgm/DD_SZ_activity.mid'
        self.dnaFile = 'phase_6/dna/donalds_dock_sz.dna'
        self.safeZoneStorageDNAFile = 'phase_6/dna/storage_DD_sz.dna'

    def load(self):
        SafeZoneLoader.SafeZoneLoader.load(self)
        self.seagullSound = base.loadSfx('phase_6/audio/sfx/SZ_DD_Seagull.mp3')
        self.underwaterSound = base.loadSfx('phase_4/audio/sfx/AV_ambient_water.mp3')
        self.swimSound = base.loadSfx('phase_4/audio/sfx/AV_swim_single_stroke.mp3')
        self.submergeSound = base.loadSfx('phase_5.5/audio/sfx/AV_jump_in_water.mp3')
        water = self.geom.find('**/water')
        water.setTransparency(1)
        water.setColor(1, 1, 1, 0.8)
        self.boat = self.geom.find('**/donalds_boat')
        if self.boat.isEmpty():
            self.notify.error('Boat not found')
        else:
            wheel = self.boat.find('**/wheel')
            if wheel.isEmpty():
                self.notify.warning('Wheel not found')
            else:
                wheel.hide()
            self.boat.stash()
        self.dockSound = base.loadSfx('phase_6/audio/sfx/SZ_DD_dockcreak.mp3')
        self.foghornSound = base.loadSfx('phase_5/audio/sfx/SZ_DD_foghorn.mp3')
        self.bellSound = base.loadSfx('phase_6/audio/sfx/SZ_DD_shipbell.mp3')
        self.waterSound = base.loadSfx('phase_6/audio/sfx/SZ_DD_waterlap.mp3')

    def unload(self):
        SafeZoneLoader.SafeZoneLoader.unload(self)
        del self.seagullSound
        del self.underwaterSound
        del self.swimSound
        del self.dockSound
        del self.foghornSound
        del self.bellSound
        del self.waterSound
        del self.submergeSound
        del self.boat

    def enter(self, requestStatus):
        SafeZoneLoader.SafeZoneLoader.enter(self, requestStatus)

    def exit(self):
        SafeZoneLoader.SafeZoneLoader.exit(self)
