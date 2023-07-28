from direct.directnotify import DirectNotifyGlobal
from toontown.ai import HolidayBaseAI
from toontown.ai import PhasedHolidayAI
from toontown.ai import DistributedPhaseEventMgrAI
from toontown.toonbase import ToontownGlobals

class PropBuffHolidayAI(PhasedHolidayAI.PhasedHolidayAI):

    notify = DirectNotifyGlobal.directNotify.newCategory(
        'PropBuffHolidayAI')

    # PostName = 'propBuffHoliday' # deliberately not set so child classes forced to define this
    # and we avoid a conflict of say the laff buf holiday stomping on the drop buff holiday

    def __init__(self, air, holidayId, startAndEndTimes, phaseDates):
        PhasedHolidayAI.PhasedHolidayAI.__init__(self, air, holidayId, startAndEndTimes, phaseDates)
        
    def start(self):
        # instantiate the object
        PhasedHolidayAI.PhasedHolidayAI.start(self)
        self.propBuffMgr = DistributedPhaseEventMgrAI.DistributedPhaseEventMgrAI (            
            self.air, self.startAndEndTimes, self.phaseDates)
        self.propBuffMgr.generateWithRequired(ToontownGlobals.UberZone)
        # let the holiday system know we started
        bboard.post(self.PostName)

    def stop(self):
        # let the holiday system know we stopped
        bboard.remove(self.PostName)
        # remove the object
        #self.resistanceEmoteMgr.requestDelete()
        self.propBuffMgr.requestDelete()

    def forcePhase(self, newPhase):
        """Force our holiday to a certain phase. Returns true if succesful"""
        result = False
        try:
            newPhase = int(newPhase)
        except:
            newPhase = 0
        if newPhase >= self.propBuffMgr.getNumPhases():
            self.notify.warning("newPhase %d invalid in forcePhase" % newPhase)
            return
        self.curPhase = newPhase
        self.propBuffMgr.forcePhase(newPhase)
        result = True
        return result

    def getCurPhase(self):
        """Returns the buffMgr's current phase, may return -1."""
        result = -1
        if hasattr(self,"propBuffMgr"):
            result = self.propBuffMgr.getCurPhase()
        return result
