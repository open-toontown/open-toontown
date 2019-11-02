from toontown.toonbase.ToonBaseGlobal import *
from direct.interval.IntervalGlobal import *
from direct.distributed.ClockDelta import *
from direct.showbase import Audio3DManager
from toontown.toonbase import ToontownGlobals
import cPickle
from DistributedToonInterior import DistributedToonInterior
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM, State
from direct.distributed import DistributedObject
from direct.fsm import State
from direct.actor import Actor
import random
import time
import ToonInteriorColors
from toontown.hood import ZoneUtil
from toontown.toon import ToonDNA
from toontown.toon import ToonHead

class DistributedToonHallInterior(DistributedToonInterior):

    def __init__(self, cr):
        DistributedToonInterior.__init__(self, cr)
        self.sillyFSM = ClassicFSM.ClassicFSM('SillyOMeter', [State.State('Setup', self.enterSetup, self.exitSetup, ['Phase0',
          'Phase1',
          'Phase2',
          'Phase3',
          'Phase4',
          'Phase5',
          'Phase6',
          'Phase7',
          'Phase8',
          'Phase9',
          'Phase10',
          'Phase11',
          'Phase12',
          'Phase13',
          'Phase14',
          'Phase15',
          'Flat',
          'Off']),
         State.State('Phase0', self.enterPhase0, self.exitPhase0, ['Phase1', 'Flat', 'Off']),
         State.State('Phase1', self.enterPhase1, self.exitPhase1, ['Phase2', 'Flat', 'Off']),
         State.State('Phase2', self.enterPhase2, self.exitPhase2, ['Phase3', 'Flat', 'Off']),
         State.State('Phase3', self.enterPhase3, self.exitPhase3, ['Phase4', 'Flat', 'Off']),
         State.State('Phase4', self.enterPhase4, self.exitPhase4, ['Phase5', 'Flat', 'Off']),
         State.State('Phase5', self.enterPhase5, self.exitPhase5, ['Phase6', 'Flat', 'Off']),
         State.State('Phase6', self.enterPhase6, self.exitPhase6, ['Phase7', 'Flat', 'Off']),
         State.State('Phase7', self.enterPhase7, self.exitPhase7, ['Phase8', 'Flat', 'Off']),
         State.State('Phase8', self.enterPhase8, self.exitPhase8, ['Phase9', 'Flat', 'Off']),
         State.State('Phase9', self.enterPhase9, self.exitPhase9, ['Phase10', 'Flat', 'Off']),
         State.State('Phase10', self.enterPhase10, self.exitPhase10, ['Phase11', 'Flat', 'Off']),
         State.State('Phase11', self.enterPhase11, self.exitPhase11, ['Phase12', 'Flat', 'Off']),
         State.State('Phase12', self.enterPhase12, self.exitPhase12, ['Phase13', 'Flat', 'Off']),
         State.State('Phase13', self.enterPhase13, self.exitPhase13, ['Phase14', 'Flat', 'Off']),
         State.State('Phase14', self.enterPhase14, self.exitPhase14, ['Phase15', 'Flat', 'Off']),
         State.State('Phase15', self.enterPhase15, self.exitPhase15, ['Flat', 'Off']),
         State.State('Flat', self.enterFlat, self.exitFlat, ['Off', 'Phase0']),
         State.State('Off', self.enterOff, self.exitOff, [])], 'Setup', 'Off')

    def setup(self):
        self.dnaStore = base.cr.playGame.dnaStore
        self.randomGenerator = random.Random()
        self.randomGenerator.seed(self.zoneId)
        interior = self.randomDNAItem('TI_hall', self.dnaStore.findNode)
        self.interior = interior.copyTo(render)
        hoodId = ZoneUtil.getCanonicalHoodId(self.zoneId)
        self.colors = ToonInteriorColors.colors[hoodId]
        self.replaceRandomInModel(self.interior)
        doorModelName = 'door_double_round_ul'
        if doorModelName[-1:] == 'r':
            doorModelName = doorModelName[:-1] + 'l'
        else:
            doorModelName = doorModelName[:-1] + 'r'
        door = self.dnaStore.findNode(doorModelName)
        door_origin = render.find('**/door_origin;+s')
        doorNP = door.copyTo(door_origin)
        door_origin.setScale(0.8, 0.8, 0.8)
        door_origin.setPos(door_origin, 0, -0.025, 0)
        color = self.randomGenerator.choice(self.colors['TI_door'])
        DNADoor.setupDoor(doorNP, self.interior, door_origin, self.dnaStore, str(self.block), color)
        doorFrame = doorNP.find('door_*_flat')
        doorFrame.wrtReparentTo(self.interior)
        doorFrame.setColor(color)
        del self.colors
        del self.dnaStore
        del self.randomGenerator
        self.interior.flattenMedium()
        self.sillyFSM.enterInitialState()

    def sillyMeterIsRunning(self, isRunning):
        if isRunning:
            self.sillyFSM.request('Phase0')
        else:
            self.sillyFSM.request('Flat')

    def selectPhase(self, newPhase):
        try:
            gotoPhase = 'Phase' + str(newPhase)
            if self.sillyFSM.hasStateNamed(gotoPhase) and not self.sillyFSM.getCurrentState() == self.sillyFSM.getStateNamed(gotoPhase):
                self.sillyFSM.request(gotoPhase)
        except:
            self.notify.warning('Illegal phase transition requested %s' % newPhase)

    def startIfNeeded(self):
        try:
            self.curPhase = self.getPhaseToRun()
            if self.curPhase >= 0:
                self.sillyFSM.request('Phase' + str(self.curPhase))
            else:
                self.sillyFSM.request('Flat')
        except:
            pass

    def getPhaseToRun(self):
        result = -1
        enoughInfoToRun = False
        if base.cr.newsManager.isHolidayRunning(ToontownGlobals.SILLYMETER_HOLIDAY) or base.cr.newsManager.isHolidayRunning(ToontownGlobals.SILLYMETER_EXT_HOLIDAY):
            if hasattr(base.cr, 'SillyMeterMgr') and not base.cr.SillyMeterMgr.isDisabled():
                enoughInfoToRun = True
            elif hasattr(base.cr, 'SillyMeterMgr'):
                self.notify.debug('isDisabled = %s' % base.cr.SillyMeterMgr.isDisabled())
            else:
                self.notify.debug('base.cr does not have SillyMeterMgr')
        else:
            self.notify.debug('holiday is not running')
        self.notify.debug('enoughInfoToRun = %s' % enoughInfoToRun)
        if enoughInfoToRun and base.cr.SillyMeterMgr.getIsRunning():
            result = base.cr.SillyMeterMgr.getCurPhase()
        return result

    def calculatePhaseDuration(self):
        result = -1
        valid = False
        if base.cr.newsManager.isHolidayRunning(ToontownGlobals.SILLYMETER_HOLIDAY) or base.cr.newsManager.isHolidayRunning(ToontownGlobals.SILLYMETER_EXT_HOLIDAY):
            if hasattr(base.cr, 'SillyMeterMgr') and not base.cr.SillyMeterMgr.isDisabled():
                valid = True
            elif hasattr(base.cr, 'SillyMeterMgr'):
                self.notify.debug('isDisabled = %s' % base.cr.SillyMeterMgr.isDisabled())
            else:
                self.notify.debug('base.cr does not have SillyMeterMgr')
        else:
            self.notify.debug('holiday is not running')
        self.notify.debug('valid = %s' % valid)
        if valid and base.cr.SillyMeterMgr.getIsRunning():
            result = base.cr.SillyMeterMgr.getCurPhaseDuration()
        return result

    def calculateFrameOffset(self, phaseDuration, numFrames):
        result = -1
        valid = False
        if base.cr.newsManager.isHolidayRunning(ToontownGlobals.SILLYMETER_HOLIDAY) or base.cr.newsManager.isHolidayRunning(ToontownGlobals.SILLYMETER_EXT_HOLIDAY):
            if hasattr(base.cr, 'SillyMeterMgr') and not base.cr.SillyMeterMgr.isDisabled():
                valid = True
            elif hasattr(base.cr, 'SillyMeterMgr'):
                self.notify.debug('isDisabled = %s' % base.cr.SillyMeterMgr.isDisabled())
            else:
                self.notify.debug('base.cr does not have SillyMeterMgr')
        else:
            self.notify.debug('holiday is not running')
        self.notify.debug('valid = %s' % valid)
        if valid and base.cr.SillyMeterMgr.getIsRunning():
            startTime = time.mktime(base.cr.SillyMeterMgr.getCurPhaseStartDate().timetuple())
            serverTime = time.mktime(base.cr.toontownTimeManager.getCurServerDateTime().timetuple())
            offset = (serverTime - startTime) / phaseDuration
            if offset < 0:
                result = -1
            else:
                result = offset * numFrames
        return result

    def calculateFrameRange(self, frameNo):
        pass

    def enterSetup(self):
        ropes = loader.loadModel('phase_4/models/modules/tt_m_ara_int_ropes')
        ropes.reparentTo(self.interior)
        self.sillyMeter = Actor.Actor('phase_4/models/props/tt_a_ara_ttc_sillyMeter_default', {'arrowTube': 'phase_4/models/props/tt_a_ara_ttc_sillyMeter_arrowFluid',
         'phaseOne': 'phase_4/models/props/tt_a_ara_ttc_sillyMeter_phaseOne',
         'phaseTwo': 'phase_4/models/props/tt_a_ara_ttc_sillyMeter_phaseTwo',
         'phaseThree': 'phase_4/models/props/tt_a_ara_ttc_sillyMeter_phaseThree',
         'phaseFour': 'phase_4/models/props/tt_a_ara_ttc_sillyMeter_phaseFour',
         'phaseFourToFive': 'phase_4/models/props/tt_a_ara_ttc_sillyMeter_phaseFourToFive',
         'phaseFive': 'phase_4/models/props/tt_a_ara_ttc_sillyMeter_phaseFive'})
        self.sillyMeter.reparentTo(self.interior)
        self.flatSillyMeter = loader.loadModel('phase_3.5/models/modules/tt_m_ara_int_sillyMeterFlat')
        self.flatSillyMeter.reparentTo(self.interior)
        self.flatSillyMeter.hide()
        self.flatDuck = loader.loadModel('phase_3.5/models/modules/tt_m_ara_int_scientistDuckFlat')
        loc1 = self.interior.find('**/npc_origin_1')
        if loc1:
            self.flatDuck.reparentTo(loc1)
        self.flatDuck.hide()
        self.flatMonkey = loader.loadModel('phase_3.5/models/modules/tt_m_ara_int_scientistMonkeyFlat')
        loc1 = self.interior.find('**/npc_origin_2')
        if loc1:
            self.flatMonkey.reparentTo(loc1)
        self.flatMonkey.hide()
        self.flatHorse = loader.loadModel('phase_3.5/models/modules/tt_m_ara_int_scientistHorseFlat')
        loc1 = self.interior.find('**/npc_origin_3')
        if loc1:
            self.flatHorse.reparentTo(loc1)
        self.flatHorse.hide()
        self.smPhase1 = self.sillyMeter.find('**/stage1')
        self.smPhase2 = self.sillyMeter.find('**/stage2')
        self.smPhase3 = self.sillyMeter.find('**/stage3')
        self.smPhase4 = self.sillyMeter.find('**/stage4')
        self.smPhase2.hide()
        self.smPhase3.hide()
        self.smPhase4.hide()
        thermometerLocator = self.sillyMeter.findAllMatches('**/uvj_progressBar')[1]
        thermometerMesh = self.sillyMeter.find('**/tube')
        thermometerMesh.setTexProjector(thermometerMesh.findTextureStage('default'), thermometerLocator, self.sillyMeter)
        self.sillyMeter.flattenMedium()
        self.sillyMeter.makeSubpart('arrow', ['uvj_progressBar*', 'def_springA'])
        self.sillyMeter.makeSubpart('meter', ['def_pivot'], ['uvj_progressBar*', 'def_springA'])
        self.audio3d = Audio3DManager.Audio3DManager(base.sfxManagerList[0], camera)
        self.phase1Sfx = self.audio3d.loadSfx('phase_4/audio/sfx/tt_s_prp_sillyMeterPhaseOne.mp3')
        self.phase1Sfx.setLoop(True)
        self.phase2Sfx = self.audio3d.loadSfx('phase_4/audio/sfx/tt_s_prp_sillyMeterPhaseTwo.mp3')
        self.phase2Sfx.setLoop(True)
        self.phase3Sfx = self.audio3d.loadSfx('phase_4/audio/sfx/tt_s_prp_sillyMeterPhaseThree.mp3')
        self.phase3Sfx.setLoop(True)
        self.phase4Sfx = self.audio3d.loadSfx('phase_4/audio/sfx/tt_s_prp_sillyMeterPhaseFour.mp3')
        self.phase4Sfx.setLoop(True)
        self.phase4To5Sfx = self.audio3d.loadSfx('phase_4/audio/sfx/tt_s_prp_sillyMeterPhaseFourToFive.mp3')
        self.phase4To5Sfx.setLoop(False)
        self.phase5Sfx = self.audio3d.loadSfx('phase_4/audio/sfx/tt_s_prp_sillyMeterPhaseFive.mp3')
        self.phase5Sfx.setLoop(True)
        self.arrowSfx = self.audio3d.loadSfx('phase_4/audio/sfx/tt_s_prp_sillyMeterArrow.mp3')
        self.arrowSfx.setLoop(False)
        self.audio3d.setDropOffFactor(0.1)
        self.accept('SillyMeterPhase', self.selectPhase)
        self.accept('SillyMeterIsRunning', self.sillyMeterIsRunning)
        self.startIfNeeded()

    def exitSetup(self):
        self.ignore('SillyMeterPhase')

    def enterPhase0(self):
        phaseDuration = self.calculatePhaseDuration()
        if phaseDuration < 0:
            phaseDuration = 604800
        self.animSeq = Parallel(ActorInterval(self.sillyMeter, 'arrowTube', partName='arrow', duration=phaseDuration, constrainedLoop=1, startFrame=1, endFrame=30), Sequence(Func(self.phase1Sfx.play), Func(self.audio3d.attachSoundToObject, self.phase1Sfx, self.sillyMeter)))
        self.animSeq.start()
        self.sillyMeter.loop('phaseOne', partName='meter')
        self.accept('SillyMeterPhase', self.selectPhase)

    def exitPhase0(self):
        self.animSeq.finish()
        del self.animSeq
        self.audio3d.detachSound(self.phase1Sfx)
        self.phase1Sfx.stop()
        self.sillyMeter.stop()
        self.ignore('SillyMeterPhase')

    def enterPhase1(self):
        phaseDuration = self.calculatePhaseDuration()
        if phaseDuration < 0:
            phaseDuration = 604800
        self.audio3d.attachSoundToObject(self.phase1Sfx, self.sillyMeter)
        self.animSeq = Sequence(Sequence(ActorInterval(self.sillyMeter, 'arrowTube', partName='arrow', constrainedLoop=0, startFrame=31, endFrame=42), Func(self.arrowSfx.play)), Parallel(ActorInterval(self.sillyMeter, 'arrowTube', partName='arrow', duration=phaseDuration, constrainedLoop=1, startFrame=42, endFrame=71), Sequence(Func(self.phase1Sfx.play), Func(self.audio3d.attachSoundToObject, self.phase1Sfx, self.sillyMeter))))
        self.animSeq.start()
        self.sillyMeter.loop('phaseOne', partName='meter')
        self.accept('SillyMeterPhase', self.selectPhase)

    def exitPhase1(self):
        self.audio3d.detachSound(self.phase1Sfx)
        self.phase1Sfx.stop()
        self.animSeq.finish()
        del self.animSeq
        self.sillyMeter.stop()
        self.ignore('SillyMeterPhase')

    def enterPhase2(self):
        phaseDuration = self.calculatePhaseDuration()
        if phaseDuration < 0:
            phaseDuration = 604800
        self.animSeq = Parallel(ActorInterval(self.sillyMeter, 'arrowTube', partName='arrow', duration=phaseDuration, constrainedLoop=1, startFrame=42, endFrame=71), Sequence(Func(self.phase1Sfx.play), Func(self.audio3d.attachSoundToObject, self.phase1Sfx, self.sillyMeter)))
        self.animSeq.start()
        self.smPhase2.show()
        self.sillyMeter.loop('phaseOne', partName='meter')
        self.accept('SillyMeterPhase', self.selectPhase)

    def exitPhase2(self):
        self.animSeq.finish()
        del self.animSeq
        self.smPhase2.hide()
        self.audio3d.detachSound(self.phase1Sfx)
        self.phase1Sfx.stop()
        self.sillyMeter.stop()
        self.ignore('SillyMeterPhase')

    def enterPhase3(self):
        phaseDuration = self.calculatePhaseDuration()
        if phaseDuration < 0:
            phaseDuration = 604800
        self.animSeq = Sequence(Sequence(ActorInterval(self.sillyMeter, 'arrowTube', partName='arrow', constrainedLoop=0, startFrame=72, endFrame=83), Func(self.arrowSfx.play)), Parallel(ActorInterval(self.sillyMeter, 'arrowTube', partName='arrow', duration=phaseDuration, constrainedLoop=1, startFrame=83, endFrame=112), Sequence(Func(self.phase1Sfx.play), Func(self.audio3d.attachSoundToObject, self.phase1Sfx, self.sillyMeter))))
        self.animSeq.start()
        self.smPhase2.show()
        self.sillyMeter.loop('phaseOne', partName='meter')
        self.accept('SillyMeterPhase', self.selectPhase)

    def exitPhase3(self):
        self.animSeq.finish()
        del self.animSeq
        self.smPhase2.hide()
        self.audio3d.detachSound(self.phase1Sfx)
        self.phase1Sfx.stop()
        self.sillyMeter.stop()
        self.ignore('SillyMeterPhase')

    def enterPhase4(self):
        phaseDuration = self.calculatePhaseDuration()
        if phaseDuration < 0:
            phaseDuration = 604800
        self.animSeq = Sequence(Sequence(ActorInterval(self.sillyMeter, 'arrowTube', partName='arrow', constrainedLoop=0, startFrame=113, endFrame=124), Func(self.arrowSfx.play)), Parallel(ActorInterval(self.sillyMeter, 'arrowTube', partName='arrow', duration=phaseDuration, constrainedLoop=1, startFrame=124, endFrame=153), Sequence(Func(self.phase1Sfx.play), Func(self.audio3d.attachSoundToObject, self.phase1Sfx, self.sillyMeter))))
        self.animSeq.start()
        self.smPhase2.show()
        self.sillyMeter.loop('phaseOne', partName='meter')
        self.accept('SillyMeterPhase', self.selectPhase)

    def exitPhase4(self):
        self.animSeq.finish()
        del self.animSeq
        self.smPhase2.hide()
        self.audio3d.detachSound(self.phase1Sfx)
        self.phase1Sfx.stop()
        self.sillyMeter.stop()
        self.ignore('SillyMeterPhase')

    def enterPhase5(self):
        phaseDuration = self.calculatePhaseDuration()
        if phaseDuration < 0:
            phaseDuration = 604800
        self.animSeq = Sequence(Sequence(ActorInterval(self.sillyMeter, 'arrowTube', partName='arrow', constrainedLoop=0, startFrame=154, endFrame=165), Func(self.arrowSfx.play)), Parallel(ActorInterval(self.sillyMeter, 'arrowTube', partName='arrow', duration=phaseDuration, constrainedLoop=1, startFrame=165, endFrame=194), Sequence(Func(self.phase2Sfx.play), Func(self.audio3d.attachSoundToObject, self.phase2Sfx, self.sillyMeter))))
        self.animSeq.start()
        self.smPhase2.show()
        self.sillyMeter.loop('phaseTwo', partName='meter')
        self.accept('SillyMeterPhase', self.selectPhase)

    def exitPhase5(self):
        self.animSeq.finish()
        del self.animSeq
        self.smPhase2.hide()
        self.audio3d.detachSound(self.phase2Sfx)
        self.phase2Sfx.stop()
        self.sillyMeter.stop()
        self.ignore('SillyMeterPhase')

    def enterPhase6(self):
        phaseDuration = self.calculatePhaseDuration()
        if phaseDuration < 0:
            phaseDuration = 604800
        self.animSeq = Sequence(Sequence(ActorInterval(self.sillyMeter, 'arrowTube', partName='arrow', constrainedLoop=0, startFrame=195, endFrame=206), Func(self.arrowSfx.play)), Parallel(ActorInterval(self.sillyMeter, 'arrowTube', partName='arrow', duration=phaseDuration, constrainedLoop=1, startFrame=206, endFrame=235), Sequence(Func(self.phase2Sfx.play), Func(self.audio3d.attachSoundToObject, self.phase2Sfx, self.sillyMeter))))
        self.animSeq.start()
        self.smPhase2.show()
        self.sillyMeter.loop('phaseTwo', partName='meter')
        self.accept('SillyMeterPhase', self.selectPhase)

    def exitPhase6(self):
        self.animSeq.finish()
        del self.animSeq
        self.smPhase2.hide()
        self.audio3d.detachSound(self.phase2Sfx)
        self.phase2Sfx.stop()
        self.sillyMeter.stop()
        self.ignore('SillyMeterPhase')

    def enterPhase7(self):
        phaseDuration = self.calculatePhaseDuration()
        if phaseDuration < 0:
            phaseDuration = 604800
        self.animSeq = Sequence(Sequence(ActorInterval(self.sillyMeter, 'arrowTube', partName='arrow', constrainedLoop=0, startFrame=236, endFrame=247), Func(self.arrowSfx.play)), Parallel(ActorInterval(self.sillyMeter, 'arrowTube', partName='arrow', duration=phaseDuration, constrainedLoop=1, startFrame=247, endFrame=276), Sequence(Func(self.phase3Sfx.play), Func(self.audio3d.attachSoundToObject, self.phase3Sfx, self.sillyMeter))))
        self.animSeq.start()
        self.smPhase2.show()
        self.smPhase3.show()
        self.sillyMeter.loop('phaseThree', partName='meter')
        self.accept('SillyMeterPhase', self.selectPhase)

    def exitPhase7(self):
        self.animSeq.finish()
        del self.animSeq
        self.smPhase2.hide()
        self.smPhase3.hide()
        self.audio3d.detachSound(self.phase3Sfx)
        self.phase3Sfx.stop()
        self.sillyMeter.stop()
        self.ignore('SillyMeterPhase')

    def enterPhase8(self):
        phaseDuration = self.calculatePhaseDuration()
        if phaseDuration < 0:
            phaseDuration = 604800
        self.animSeq = Sequence(Sequence(ActorInterval(self.sillyMeter, 'arrowTube', partName='arrow', constrainedLoop=0, startFrame=277, endFrame=288), Func(self.arrowSfx.play)), Parallel(ActorInterval(self.sillyMeter, 'arrowTube', partName='arrow', duration=phaseDuration, constrainedLoop=1, startFrame=288, endFrame=317), Sequence(Func(self.phase3Sfx.play), Func(self.audio3d.attachSoundToObject, self.phase3Sfx, self.sillyMeter))))
        self.animSeq.start()
        self.smPhase2.show()
        self.smPhase3.show()
        self.sillyMeter.loop('phaseThree', partName='meter')
        self.accept('SillyMeterPhase', self.selectPhase)

    def exitPhase8(self):
        self.animSeq.finish()
        del self.animSeq
        self.smPhase2.hide()
        self.smPhase3.hide()
        self.audio3d.detachSound(self.phase3Sfx)
        self.phase3Sfx.stop()
        self.sillyMeter.stop()
        self.ignore('SillyMeterPhase')

    def enterPhase9(self):
        phaseDuration = self.calculatePhaseDuration()
        if phaseDuration < 0:
            phaseDuration = 604800
        self.animSeq = Sequence(Sequence(ActorInterval(self.sillyMeter, 'arrowTube', partName='arrow', constrainedLoop=0, startFrame=318, endFrame=329), Func(self.arrowSfx.play)), Parallel(ActorInterval(self.sillyMeter, 'arrowTube', partName='arrow', duration=phaseDuration, constrainedLoop=1, startFrame=329, endFrame=358), Sequence(Func(self.phase3Sfx.play), Func(self.audio3d.attachSoundToObject, self.phase3Sfx, self.sillyMeter))))
        self.animSeq.start()
        self.smPhase2.show()
        self.smPhase3.show()
        self.sillyMeter.loop('phaseThree', partName='meter')
        self.accept('SillyMeterPhase', self.selectPhase)

    def exitPhase9(self):
        self.animSeq.finish()
        del self.animSeq
        self.smPhase2.hide()
        self.smPhase3.hide()
        self.audio3d.detachSound(self.phase3Sfx)
        self.phase3Sfx.stop()
        self.sillyMeter.stop()
        self.ignore('SillyMeterPhase')

    def enterPhase10(self):
        phaseDuration = self.calculatePhaseDuration()
        if phaseDuration < 0:
            phaseDuration = 604800
        self.animSeq = Sequence(Sequence(ActorInterval(self.sillyMeter, 'arrowTube', partName='arrow', constrainedLoop=0, startFrame=359, endFrame=370), Func(self.arrowSfx.play)), Parallel(ActorInterval(self.sillyMeter, 'arrowTube', partName='arrow', duration=phaseDuration, constrainedLoop=1, startFrame=370, endFrame=399), Sequence(Func(self.phase4Sfx.play), Func(self.audio3d.attachSoundToObject, self.phase4Sfx, self.sillyMeter))))
        self.animSeq.start()
        self.smPhase2.show()
        self.smPhase3.show()
        self.smPhase4.show()
        self.sillyMeter.loop('phaseFour', partName='meter')
        self.accept('SillyMeterPhase', self.selectPhase)

    def exitPhase10(self):
        self.animSeq.finish()
        del self.animSeq
        self.smPhase2.hide()
        self.smPhase3.hide()
        self.smPhase4.hide()
        self.audio3d.detachSound(self.phase4Sfx)
        self.phase4Sfx.stop()
        self.sillyMeter.stop()
        self.ignore('SillyMeterPhase')

    def enterPhase11(self):
        phaseDuration = self.calculatePhaseDuration()
        if phaseDuration < 0:
            phaseDuration = 604800
        self.animSeq = Sequence(Sequence(ActorInterval(self.sillyMeter, 'arrowTube', partName='arrow', constrainedLoop=0, startFrame=400, endFrame=411), Func(self.arrowSfx.play)), Parallel(ActorInterval(self.sillyMeter, 'arrowTube', partName='arrow', duration=phaseDuration, constrainedLoop=1, startFrame=411, endFrame=440), Sequence(Func(self.phase4Sfx.play), Func(self.audio3d.attachSoundToObject, self.phase4Sfx, self.sillyMeter))))
        self.animSeq.start()
        self.smPhase2.show()
        self.smPhase3.show()
        self.smPhase4.show()
        self.sillyMeter.loop('phaseFour', partName='meter')
        self.accept('SillyMeterPhase', self.selectPhase)

    def exitPhase11(self):
        self.animSeq.finish()
        del self.animSeq
        self.smPhase2.hide()
        self.smPhase3.hide()
        self.smPhase4.hide()
        self.audio3d.detachSound(self.phase4Sfx)
        self.phase4Sfx.stop()
        self.sillyMeter.stop()
        self.ignore('SillyMeterPhase')

    def enterPhase12(self):
        phaseDuration = self.calculatePhaseDuration()
        if phaseDuration < 0:
            phaseDuration = 604800
        elif phaseDuration > 2000000:
            phaseDuration = 2000000
        self.animSeq = Sequence(Sequence(ActorInterval(self.sillyMeter, 'arrowTube', partName='arrow', constrainedLoop=0, startFrame=441, endFrame=452), Func(self.arrowSfx.play)), Parallel(ActorInterval(self.sillyMeter, 'arrowTube', partName='arrow', duration=phaseDuration, constrainedLoop=1, startFrame=452, endFrame=481), Sequence(Func(self.phase4Sfx.play), Func(self.audio3d.attachSoundToObject, self.phase4Sfx, self.sillyMeter))))
        self.animSeq.start()
        self.smPhase2.show()
        self.smPhase3.show()
        self.smPhase4.show()
        self.sillyMeter.loop('phaseFour', partName='meter')
        self.accept('SillyMeterPhase', self.selectPhase)

    def exitPhase12(self):
        self.animSeq.finish()
        del self.animSeq
        self.smPhase2.hide()
        self.smPhase3.hide()
        self.smPhase4.hide()
        self.audio3d.detachSound(self.phase4Sfx)
        self.phase4Sfx.stop()
        self.sillyMeter.stop()
        self.ignore('SillyMeterPhase')

    def enterPhase13(self):
        phaseDuration = self.calculatePhaseDuration()
        if phaseDuration < 0:
            phaseDuration = 604800
        self.animSeq = Sequence(Parallel(Func(self.phase4To5Sfx.play), ActorInterval(self.sillyMeter, 'phaseFourToFive', constrainedLoop=0, startFrame=1, endFrame=120)), Parallel(ActorInterval(self.sillyMeter, 'phaseFive', duration=phaseDuration, constrainedLoop=1, startFrame=1, endFrame=48), Sequence(Func(self.phase5Sfx.play), Func(self.audio3d.attachSoundToObject, self.phase5Sfx, self.sillyMeter))))
        self.animSeq.start()
        self.smPhase2.show()
        self.smPhase3.show()
        self.smPhase4.show()
        self.accept('SillyMeterPhase', self.selectPhase)

    def exitPhase13(self):
        self.animSeq.finish()
        del self.animSeq
        self.smPhase2.hide()
        self.smPhase3.hide()
        self.smPhase4.hide()
        self.audio3d.detachSound(self.phase5Sfx)
        self.phase5Sfx.stop()
        self.sillyMeter.stop()
        self.ignore('SillyMeterPhase')

    def enterPhase14(self):
        phaseDuration = self.calculatePhaseDuration()
        if phaseDuration < 0:
            phaseDuration = 604800
        self.animSeq = Parallel(ActorInterval(self.sillyMeter, 'phaseFive', duration=phaseDuration, constrainedLoop=1, startFrame=1, endFrame=48), Sequence(Func(self.phase5Sfx.play), Func(self.audio3d.attachSoundToObject, self.phase5Sfx, self.sillyMeter)))
        self.animSeq.start()
        self.smPhase2.show()
        self.smPhase3.show()
        self.smPhase4.show()
        self.accept('SillyMeterPhase', self.selectPhase)

    def exitPhase14(self):
        self.animSeq.finish()
        del self.animSeq
        self.smPhase2.hide()
        self.smPhase3.hide()
        self.smPhase4.hide()
        self.audio3d.detachSound(self.phase5Sfx)
        self.phase5Sfx.stop()
        self.sillyMeter.stop()
        self.ignore('SillyMeterPhase')

    def enterPhase15(self):
        phaseDuration = self.calculatePhaseDuration()
        if phaseDuration < 0:
            phaseDuration = 604800
        self.animSeq = Parallel(ActorInterval(self.sillyMeter, 'phaseFive', duration=phaseDuration, constrainedLoop=1, startFrame=1, endFrame=48), Sequence(Func(self.phase5Sfx.play), Func(self.audio3d.attachSoundToObject, self.phase5Sfx, self.sillyMeter)))
        self.animSeq.start()
        self.smPhase2.show()
        self.smPhase3.show()
        self.smPhase4.show()
        self.accept('SillyMeterPhase', self.selectPhase)

    def exitPhase15(self):
        self.animSeq.finish()
        del self.animSeq
        self.smPhase2.hide()
        self.smPhase3.hide()
        self.smPhase4.hide()
        self.audio3d.detachSound(self.phase5Sfx)
        self.phase5Sfx.stop()
        self.sillyMeter.stop()
        self.ignore('SillyMeterPhase')

    def enterFlat(self):
        self.sillyMeter.hide()
        self.flatSillyMeter.show()
        self.flatDuck.show()
        self.flatMonkey.show()
        self.flatHorse.show()

    def exitFlat(self):
        self.sillyMeter.show()
        self.flatSillyMeter.hide()
        self.flatDuck.hide()
        self.flatMonkey.hide()
        self.flatHorse.hide()

    def enterOff(self):
        if hasattr(self, 'animSeq') and self.animSeq:
            self.animSeq.finish()
        self.ignore('SillyMeterPhase')
        if hasattr(self, 'sillyMeter'):
            del self.sillyMeter
        if hasattr(self, 'smPhase1'):
            del self.smPhase1
        if hasattr(self, 'smPhase2'):
            del self.smPhase2
        if hasattr(self, 'smPhase3'):
            del self.smPhase3
        if hasattr(self, 'smPhase4'):
            del self.smPhase4
        self.cleanUpSounds()

    def exitOff(self):
        pass

    def enterToon(self):
        self.toonhallView = (Point3(0, -5, 3),
         Point3(0, 12.0, 7.0),
         Point3(0.0, 10.0, 5.0),
         Point3(0.0, 10.0, 5.0),
         1)
        self.setupCollisions(2.5)
        self.firstEnter = 1
        self.accept('CamChangeColl' + '-into', self.handleCloseToWall)

    def exitToon(self):
        pass

    def handleCloseToWall(self, collEntry):
        if self.firstEnter == 0:
            return
        interiorRopes = self.interior.find('**/*interior_ropes')
        if interiorRopes == collEntry.getIntoNodePath().getParent():
            return
        self.restoreCam()
        self.accept('CamChangeColl' + '-exit', self.handleAwayFromWall)

    def handleAwayFromWall(self, collEntry):
        if self.firstEnter == 1:
            self.cleanUpCollisions()
            self.setupCollisions(0.75)
            self.oldView = base.localAvatar.cameraIndex
            base.localAvatar.addCameraPosition(self.toonhallView)
            self.firstEnter = 0
            self.setUpToonHallCam()
            return
        flippy = self.interior.find('**/*Flippy*/*NPCToon*')
        if flippy == collEntry.getIntoNodePath():
            self.setUpToonHallCam()

    def setupCollisions(self, radius):
        r = base.localAvatar.getClampedAvatarHeight() * radius
        cs = CollisionSphere(0, 0, 0, r)
        cn = CollisionNode('CamChangeColl')
        cn.addSolid(cs)
        cn.setFromCollideMask(ToontownGlobals.WallBitmask)
        cn.setIntoCollideMask(BitMask32.allOff())
        self.camChangeNP = base.localAvatar.getPart('torso', '1000').attachNewNode(cn)
        self.cHandlerEvent = CollisionHandlerEvent()
        self.cHandlerEvent.addInPattern('%fn-into')
        self.cHandlerEvent.addOutPattern('%fn-exit')
        base.cTrav.addCollider(self.camChangeNP, self.cHandlerEvent)

    def cleanUpCollisions(self):
        base.cTrav.removeCollider(self.camChangeNP)
        self.camChangeNP.detachNode()
        if hasattr(self, 'camChangeNP'):
            del self.camChangeNP
        if hasattr(self, 'cHandlerEvent'):
            del self.cHandlerEvent

    def cleanUpSounds(self):

        def __cleanUpSound__(soundFile):
            if soundFile.status() == soundFile.PLAYING:
                soundFile.setLoop(False)
                soundFile.stop()

        if hasattr(self, 'audio3d'):
            self.audio3d.disable()
            del self.audio3d
        if hasattr(self, 'phase1Sfx'):
            __cleanUpSound__(self.phase1Sfx)
            del self.phase1Sfx
        if hasattr(self, 'phase2Sfx'):
            __cleanUpSound__(self.phase2Sfx)
            del self.phase2Sfx
        if hasattr(self, 'phase3Sfx'):
            __cleanUpSound__(self.phase3Sfx)
            del self.phase3Sfx
        if hasattr(self, 'phase4Sfx'):
            __cleanUpSound__(self.phase4Sfx)
            del self.phase4Sfx
        if hasattr(self, 'phase4To5Sfx'):
            __cleanUpSound__(self.phase4To5Sfx)
            del self.phase4To5Sfx
        if hasattr(self, 'phase5Sfx'):
            __cleanUpSound__(self.phase5Sfx)
            del self.phase5Sfx
        if hasattr(self, 'arrowSfx'):
            __cleanUpSound__(self.arrowSfx)
            del self.arrowSfx

    def setUpToonHallCam(self):
        base.localAvatar.setCameraFov(75)
        base.localAvatar.setCameraSettings(self.toonhallView)

    def restoreCam(self):
        base.localAvatar.setCameraFov(ToontownGlobals.DefaultCameraFov)
        if hasattr(self, 'oldView'):
            base.localAvatar.setCameraPositionByIndex(self.oldView)

    def disable(self):
        self.setUpToonHallCam()
        base.localAvatar.removeCameraPosition()
        base.localAvatar.resetCameraPosition()
        self.restoreCam()
        self.ignoreAll()
        self.cleanUpCollisions()
        if hasattr(self, 'sillyFSM'):
            self.sillyFSM.requestFinalState()
            del self.sillyFSM
        DistributedToonInterior.disable(self)

    def delete(self):
        DistributedToonInterior.delete(self)
