from direct.directnotify import DirectNotifyGlobal
from toontown.ai import HolidayBaseAI
from toontown.ai import PhasedHolidayAI
from toontown.ai import DistributedTrashcanZeroMgrAI
from toontown.toonbase import ToontownGlobals

class TrashcanZeroHolidayAI(PhasedHolidayAI.PhasedHolidayAI):

    notify = DirectNotifyGlobal.directNotify.newCategory(
        'TrashcanZeroHolidayAI')

    PostName = 'trashcanZeroHoliday'

    def __init__(self, air, holidayId, startAndEndTimes, phaseDates):
        PhasedHolidayAI.PhasedHolidayAI.__init__(self, air, holidayId, startAndEndTimes, phaseDates)
        
    def start(self):
        # instantiate the object
        PhasedHolidayAI.PhasedHolidayAI.start(self)
        self.trashcanZeroMgr = DistributedTrashcanZeroMgrAI.DistributedTrashcanZeroMgrAI (
            self.air, self.startAndEndTimes, self.phaseDates)
        self.trashcanZeroMgr.generateWithRequired(ToontownGlobals.UberZone)
        # let the holiday system know we started
        bboard.post(self.PostName)

    def stop(self):
        # let the holiday system know we stopped
        bboard.remove(self.PostName)
        # remove the object
        #self.resistanceEmoteMgr.requestDelete()
        self.trashcanZeroMgr.requestDelete()

    def forcePhase(self, newPhase):
        """Force our holiday to a certain phase. Returns true if succesful"""
        result = False
        try:
            newPhase = int(newPhase)
        except:
            newPhase = 0
        if newPhase >= self.trashcanZeroMgr.getNumPhases():
            self.notify.warning("newPhase %d invalid in forcePhase" % newPhase)
            return
        self.curPhase = newPhase
        self.trashcanZeroMgr.forcePhase(newPhase)
        result = True
        return result
        
