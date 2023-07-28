from direct.directnotify import DirectNotifyGlobal
from toontown.ai import HolidayBaseAI
from toontown.ai import PhasedHolidayAI
from toontown.ai import DistributedSillyMeterMgrAI
from toontown.toonbase import ToontownGlobals

class SillyMeterHolidayAI(PhasedHolidayAI.PhasedHolidayAI):

    notify = DirectNotifyGlobal.directNotify.newCategory(
        'SillyMeterHolidayAI')

    PostName = 'SillyMeterHoliday'

    def __init__(self, air, holidayId, startAndEndTimes, phaseDates):
        PhasedHolidayAI.PhasedHolidayAI.__init__(self, air, holidayId, startAndEndTimes, phaseDates)
        
        self.runningState = 1
        
    def start(self):
        # instantiate the object
        PhasedHolidayAI.PhasedHolidayAI.start(self)
        self.SillyMeterMgr = DistributedSillyMeterMgrAI.DistributedSillyMeterMgrAI(
            self.air, self.startAndEndTimes, self.phaseDates)
        self.SillyMeterMgr.generateWithRequired(ToontownGlobals.UberZone)
        # let the holiday system know we started
        bboard.post(self.PostName)

    def stop(self):
        # let the holiday system know we stopped
        self.runningState = 0
        bboard.remove(self.PostName)
        self.SillyMeterMgr.end()
        self.SillyMeterMgr.requestDelete()

    def forcePhase(self, newPhase):
        """Force our holiday to a certain phase."""
        try:
            newPhase = int(newPhase)
        except:
            newPhase = 0
        if newPhase >= self.SillyMeterMgr.getNumPhases():
            self.notify.warning("newPhase %d invalid in forcePhase" % newPhase)
            return
        self.curPhase = newPhase
        self.SillyMeterMgr.forcePhase(newPhase)
        
    def getRunningState(self):
        return self.runningState
