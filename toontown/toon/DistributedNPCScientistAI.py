import DistributedNPCToonBaseAI
from toontown.toonbase import TTLocalizer, ToontownGlobals
from direct.fsm import ClassicFSM, State
from direct.task.Task import Task

class DistributedNPCScientistAI(DistributedNPCToonBaseAI.DistributedNPCToonBaseAI):

    def __init__(self, air, npcId, questCallback = None, hq = 0):
        DistributedNPCToonBaseAI.DistributedNPCToonBaseAI.__init__(self, air, npcId, questCallback)
        self.scientistFSM = ClassicFSM.ClassicFSM('Scientist', [
            State.State('Neutral',
                        self.enterNeutral,
                        self.exitNeutral, [
                            'Phase0',
                            'Phase1',
                            'Phase2',
                            'Phase2_5',
                            'Phase3',
                            'Phase4',
                            'Phase5',
                            'Off']),
            State.State('Phase0',
                        self.enterPhase0,
                        self.exitPhase0, [
                            'Phase1',
                            'Neutral']),
         State.State('Phase1',
                     self.enterPhase1,
                     self.exitPhase1, [
                         'Phase2',
                         'Neutral']),
         State.State('Phase2',
                     self.enterPhase2,
                     self.exitPhase2, [
                         'Phase2_5',
                         'Neutral']),
         State.State('Phase2_5',
                     self.enterPhase2_5,
                     self.exitPhase2_5, [
                         'Phase3',
                         'Neutral']),
         State.State('Phase3',
                     self.enterPhase3,
                     self.exitPhase3, [
                         'Phase4',
                         'Neutral']),
         State.State('Phase4',
                     self.enterPhase4,
                     self.exitPhase4, [
                         'Phase5',
                         'Neutral']),
         State.State('Phase5',
                     self.enterPhase5,
                     self.exitPhase5, [
                         'Neutral']),
         State.State('Off',
                     self.enterOff,
                     self.exitOff, [])],
         'Neutral', 'Off')
         
        if self.npcId == 2018 or self.npcId == 2019:
            self.startAnimState = 'ScientistJealous'
        elif self.npcId == 2020:
            self.startAnimState = 'ScientistEmcee'
        self.scientistFSM.enterInitialState()

    def selectPhase(self, newPhase):
        try:
            if newPhase <= 4:
                gotoPhase = '0'
            elif newPhase <= 6:
                gotoPhase = '1'
            elif newPhase <= 11:
                gotoPhase = '2'
            elif newPhase <= 12:
                gotoPhase = '2_5'
            elif newPhase <= 13:
                gotoPhase = '3'
            elif newPhase <= 14:
                gotoPhase = '4'
            elif newPhase <= 15:
                gotoPhase = '5'
            else:
                if not self.scientistFSM.getCurrentState() == self.scientistFSM.getStateNamed('Neutral'):
                    self.scientistFSM.request('Neutral')
                return
            gotoPhase = 'Phase' + gotoPhase
            if not self.scientistFSM.getCurrentState() == self.scientistFSM.getStateNamed(gotoPhase):
                self.scientistFSM.request(gotoPhase)
        except:
            self.notify.warning('Illegal phase transition requested')

    def startIfNeeded(self):
        if hasattr(simbase.air, 'holidayManager') and simbase.air.holidayManager:
            self.curPhase = self.getPhaseToRun()
            if self.curPhase != -1:
                self.selectPhase(self.curPhase)

    def getPhaseToRun(self):
        result = -1
        enoughInfoToRun = False
        if simbase.air.holidayManager.isHolidayRunning(ToontownGlobals.SILLYMETER_HOLIDAY) or simbase.air.holidayManager.isHolidayRunning(ToontownGlobals.SILLYMETER_EXT_HOLIDAY):
            if hasattr(simbase.air, 'SillyMeterMgr'):
                enoughInfoToRun = True
            else:
                self.notify.debug('simbase.air does not have SillyMeterMgr')
        else:
            self.notify.debug('holiday is not running')
        self.notify.debug('enoughInfoToRun = %s' % enoughInfoToRun)
        if enoughInfoToRun and simbase.air.SillyMeterMgr.getIsRunning():
            result = simbase.air.SillyMeterMgr.getCurPhase()
        return result

    def enterNeutral(self):
        self.accept('SillyMeterPhase', self.selectPhase)
        self.startIfNeeded()

    def exitNeutral(self):
        self.ignore('SillyMeterPhase')

    def enterPhase0(self):
        if self.npcId == 2020:
            self.air.dialogueManager.requestDialogue(self, TTLocalizer.AprilToonsPhasePreTopTopic, endPause=30)
        elif self.npcId == 2018 or self.npcId == 2019:
            self.d_setAnimState('ScientistJealous', 1.0)
        self.accept('SillyMeterPhase', self.selectPhase)

    def exitPhase0(self):
        if self.npcId == 2020:
            self.air.dialogueManager.leaveDialogue(self, TTLocalizer.AprilToonsPhasePreTopTopic)
        self.ignore('SillyMeterPhase')

    def enterPhase1(self):
        if self.npcId == 2020:
            self.air.dialogueManager.requestDialogue(self, TTLocalizer.AprilToonsPhasePreTopTopic, endPause=30)
        elif self.npcId == 2018 or self.npcId == 2019:
            self.d_setAnimState('ScientistJealous', 1.0)
        self.accept('SillyMeterPhase', self.selectPhase)

    def exitPhase1(self):
        if self.npcId == 2020:
            self.air.dialogueManager.leaveDialogue(self, TTLocalizer.AprilToonsPhasePreTopTopic)
        self.ignore('SillyMeterPhase')

    def enterPhase2(self):
        if self.npcId == 2020:
            self.air.dialogueManager.requestDialogue(self, TTLocalizer.AprilToonsPhasePreTopTopic, endPause=30)
        elif self.npcId == 2018 or self.npcId == 2019:
            self.d_setAnimState('ScientistWork', 1.0)
        self.accept('SillyMeterPhase', self.selectPhase)

    def exitPhase2(self):
        if self.npcId == 2020:
            self.air.dialogueManager.leaveDialogue(self, TTLocalizer.AprilToonsPhasePreTopTopic)
        self.ignore('SillyMeterPhase')

    def enterPhase2_5(self):
        if self.npcId == 2020:
            if simbase.air.holidayManager.isHolidayRunning(ToontownGlobals.SILLYMETER_EXT_HOLIDAY):
                self.air.dialogueManager.requestDialogue(self, TTLocalizer.AprilToonsExtPhaseTopTopic, endPause=30)
            else:
                self.air.dialogueManager.requestDialogue(self, TTLocalizer.AprilToonsPhaseTopTopic, endPause=30)
        elif self.npcId == 2018 or self.npcId == 2019:
            self.d_setAnimState('ScientistLessWork', 1.0)
        self.accept('SillyMeterPhase', self.selectPhase)

    def exitPhase2_5(self):
        if self.npcId == 2020:
            if simbase.air.holidayManager.isHolidayRunning(ToontownGlobals.SILLYMETER_EXT_HOLIDAY):
                self.air.dialogueManager.leaveDialogue(self, TTLocalizer.AprilToonsExtPhaseTopTopic)
            else:
                self.air.dialogueManager.leaveDialogue(self, TTLocalizer.AprilToonsPhaseTopTopic)
        self.ignore('SillyMeterPhase')

    def enterPhase3(self):
        if self.npcId == 2020:
            if simbase.air.holidayManager.isHolidayRunning(ToontownGlobals.SILLYMETER_EXT_HOLIDAY):
                self.air.dialogueManager.requestDialogue(self, TTLocalizer.AprilToonsExtPhaseTopTopic, endPause=30)
            else:
                self.air.dialogueManager.requestDialogue(self, TTLocalizer.AprilToonsPhasePostTopTopic, endPause=30)
        elif self.npcId == 2018 or self.npcId == 2019:
            self.d_setAnimState('ScientistPlay', 1.0)
        self.accept('SillyMeterPhase', self.selectPhase)

    def exitPhase3(self):
        if self.npcId == 2020:
            if simbase.air.holidayManager.isHolidayRunning(ToontownGlobals.SILLYMETER_EXT_HOLIDAY):
                self.air.dialogueManager.leaveDialogue(self, TTLocalizer.AprilToonsExtPhaseTopTopic)
            else:
                self.air.dialogueManager.leaveDialogue(self, TTLocalizer.AprilToonsPhasePostTopTopic)
        self.ignore('SillyMeterPhase')

    def enterPhase4(self):
        if self.npcId == 2020:
            if simbase.air.holidayManager.isHolidayRunning(ToontownGlobals.SILLYMETER_EXT_HOLIDAY):
                self.air.dialogueManager.requestDialogue(self, TTLocalizer.AprilToonsExtPhaseTopTopic, endPause=30)
            else:
                self.air.dialogueManager.requestDialogue(self, TTLocalizer.AprilToonsPhasePostTopTopic, endPause=30)
        elif self.npcId == 2018 or self.npcId == 2019:
            self.d_setAnimState('ScientistPlay', 1.0)
        self.accept('SillyMeterPhase', self.selectPhase)

    def exitPhase4(self):
        if self.npcId == 2020:
            if simbase.air.holidayManager.isHolidayRunning(ToontownGlobals.SILLYMETER_EXT_HOLIDAY):
                self.air.dialogueManager.leaveDialogue(self, TTLocalizer.AprilToonsExtPhaseTopTopic)
            else:
                self.air.dialogueManager.leaveDialogue(self, TTLocalizer.AprilToonsPhasePostTopTopic)
        self.ignore('SillyMeterPhase')

    def enterPhase5(self):
        if self.npcId == 2020:
            if simbase.air.holidayManager.isHolidayRunning(ToontownGlobals.SILLYMETER_EXT_HOLIDAY):
                self.air.dialogueManager.requestDialogue(self, TTLocalizer.AprilToonsExtPhaseTopTopic, endPause=30)
            else:
                self.air.dialogueManager.requestDialogue(self, TTLocalizer.AprilToonsPhasePostTopTopic, endPause=30)
        elif self.npcId == 2018 or self.npcId == 2019:
            self.d_setAnimState('ScientistPlay', 1.0)
        self.accept('SillyMeterPhase', self.selectPhase)

    def exitPhase5(self):
        if self.npcId == 2020:
            if simbase.air.holidayManager.isHolidayRunning(ToontownGlobals.SILLYMETER_EXT_HOLIDAY):
                self.air.dialogueManager.leaveDialogue(self, TTLocalizer.AprilToonsExtPhaseTopTopic)
            else:
                self.air.dialogueManager.leaveDialogue(self, TTLocalizer.AprilToonsPhasePostTopTopic)
        self.ignore('SillyMeterPhase')

    def enterOff(self):
        pass

    def exitOff(self):
        pass

    def delete(self):
        self.scientistFSM.requestFinalState()
        if hasattr(self, 'scientistFSM'):
            del self.scientistFSM
        DistributedNPCToonBaseAI.DistributedNPCToonBaseAI.delete(self)
