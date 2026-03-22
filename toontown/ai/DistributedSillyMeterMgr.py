from direct.directnotify import DirectNotifyGlobal
from toontown.ai import DistributedPhaseEventMgr
import time


class DistributedSillyMeterMgr(DistributedPhaseEventMgr.DistributedPhaseEventMgr):
    """Class to manage the SillyOMeter"""
    neverDisable = 1
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedSillyMeterMgr')

    def __init__(self, cr):
        DistributedPhaseEventMgr.DistributedPhaseEventMgr.__init__(self, cr)
        cr.SillyMeterMgr = self

    def announceGenerate(self):
        """Tell other objects we're here."""
        DistributedPhaseEventMgr.DistributedPhaseEventMgr.announceGenerate(self)
        messenger.send('SillyMeterIsRunning', [self.isRunning])

    def delete(self):
        self.notify.debug("deleting SillyMetermgr")
        messenger.send('SillyMeterIsRunning', [False])
        DistributedPhaseEventMgr.DistributedPhaseEventMgr.delete(self)
        if hasattr(self.cr, "SillyMeterMgr"):
            del self.cr.SillyMeterMgr

    def setCurPhase(self, newPhase):
        """We've gotten a new phase lets, tell the silly meter."""
        assert self.notify.debugStateCall(self)
        DistributedPhaseEventMgr.DistributedPhaseEventMgr.setCurPhase(self, newPhase)
        messenger.send('SillyMeterPhase', [newPhase])

    def setIsRunning(self, isRunning):
        assert self.notify.debugStateCall(self)
        DistributedPhaseEventMgr.DistributedPhaseEventMgr.setIsRunning(self, isRunning)
        messenger.send('SillyMeterIsRunning', [isRunning])

    def getCurPhaseDuration(self):
        """return the duration in time of the current phase"""

        if len(self.holidayDates) > 0:
            startHolidayDate = self.holidayDates[self.curPhase]
            if (self.curPhase + 1) >= len(self.holidayDates):
                self.notify.error(f"No end date for phase {self.curPhase}")
                return -1
            else:
                endHolidayDate = self.holidayDates[(self.curPhase + 1)]
            startHolidayTime = time.mktime(startHolidayDate.timetuple())
            endHolidayTime = time.mktime(endHolidayDate.timetuple())
            holidayDuration = endHolidayTime - startHolidayTime
            if holidayDuration < 0:
                self.notify.error(f"Duration not set for phase {self.curPhase}")
                return -1
            else:
                return holidayDuration
        else:
            self.notify.warning("Phase dates not yet known")
            return -1

    def getCurPhaseStartDate(self):
        """return the start date of the current phase"""
        if len(self.holidayDates) > 0:
            return self.holidayDates[self.curPhase]
