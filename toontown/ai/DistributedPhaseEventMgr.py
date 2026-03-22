from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObject
import datetime


class DistributedPhaseEventMgr(DistributedObject.DistributedObject):
    """Base Class to manage the hydrant/mailbox/trashcan zero manager"""
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedPhaseEventMgr')

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        self.holidayDates = []

    def setIsRunning(self, isRunning):
        self.isRunning = isRunning

    def setNumPhases(self, numPhases):
        self.numPhases = numPhases

    def setCurPhase(self, curPhase):
        self.curPhase = curPhase

    def getIsRunning(self):
        return self.isRunning

    def getNumPhases(self):
        return self.numPhases

    def getCurPhase(self):
        return self.curPhase

    def setDates(self, holidayDates):
        """
        Provide the client with the phase date information
        """
        for holidayDate in holidayDates:
            # year, month, day, hour, min, sec
            self.holidayDates.append(datetime.datetime(holidayDate[0], holidayDate[1], holidayDate[2],
                                                       holidayDate[3], holidayDate[4], holidayDate[5]))
