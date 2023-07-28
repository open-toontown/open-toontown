import datetime
import time
from direct.directnotify import DirectNotifyGlobal
from toontown.ai import HolidayBaseAI
from toontown.toonbase import ToontownGlobals
from toontown.ai import DistributedResistanceEmoteMgrAI


class StartAndEndTime:
    def __init__(self, startTime, endTime):
        """Keep track of start and end datetimes, in a struct."""
        self.start = startTime
        self.end = endTime

    def isInBetween(self, phaseTime):
        """Returns true if phaseTime is in between start and end times.
        Note that it returns false if it is equal."""
        result = False
        if self.start < phaseTime and phaseTime < self.end:
            result = True
        return result

    def isInBetweenInclusive(self, phaseTime):
        """Returns true if phaseTime is in between start and end times.
        Note that it returns true if it is equal."""
        result = False
        if self.start <= phaseTime and phaseTime <= self.end:
            result = True
        return True

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return ("(%s %s)" % (self.start, self.end))

class PhasedHolidayAI(HolidayBaseAI.HolidayBaseAI):
    """This is the base class for holidays which have different phases.
    
    They ramp up over time, such as hydrant zero, silly meter.
    While each phase could have been implemented as a different holiday,
    this makes sure the start and end times for each phase match up."""

    # WARNING phased holidays with multiple start and end times have not been fully tested
    # RAU coded with it in mind, but edge cases can easily slip through

    notify = DirectNotifyGlobal.directNotify.newCategory(
        'PhasedHolidayAI')

    def __init__(self, air, holidayId, startAndEndTupleList, phaseDates):
        HolidayBaseAI.HolidayBaseAI.__init__(self, air, holidayId)
        self.oldPhase = 0
        self.curPhase = 0
        self.phaseDates = phaseDates
        self.startAndEndTimes = self.convertStartAndEndListToDateTimes(startAndEndTupleList)
        self.sanityCheckPhaseDates()
        # we assume phase 0 is before phaseDates[0],
        # phase 1 is between phaseDates[0], phaseDates[1]
        # the last phase is after phaseDates[-1]
        # TODO should we have the FSM here or in the child class?
        # Lets leave it in the child class in case it's really simple

    def convertStartAndEndListToDateTimes(self, startAndEndTupleList):
        """Convert start and end times to a more manageable class."""
        result = []
        for startAndEnd in startAndEndTupleList:
            startInfo = startAndEnd[0]
            startTime = datetime.datetime(startInfo[0], startInfo[1], startInfo[2],
                                          startInfo[3], startInfo[4], startInfo[5])
            endInfo = startAndEnd[1]
            endTime = datetime.datetime(endInfo[0], endInfo[1], endInfo[2],
                                          endInfo[3], endInfo[4], endInfo[5])
            result.append(StartAndEndTime(startTime, endTime))
        return result


    def sanityCheckPhaseDates(self):
        """Do some sanity checking on our phase dates."""
        #Check phase dates are between end and start times."""
        for phaseDate in self.phaseDates:
            foundInBetween = False
            for startAndEnd in self.startAndEndTimes:
                if startAndEnd.isInBetween(phaseDate):
                    foundInBetween = True
                    break
            if not foundInBetween:
                self.notify.error("holiday %d, phaseDate=%s not in between start and end times" %
                                  (self.holidayId, phaseDate))
        # check the phase dates are ascending
        for index in range( len(self.phaseDates) -1):
            if not (self.phaseDates[index] < self.phaseDates[index +1]):
                    self.notify.error("phaseDate=%s coming before phaseDate=%s" %
                                      (self.phaseDates[index], self.phaseDates[index+1]))
    
    def calcPhase(self, myTime):
        """Return which phase we should be given parameter time.

        Will return 0 if it's way before the start time,
        and return the last phase if its way after the end time
        """
        result = self.getNumPhases()
        for index, phaseDate in enumerate( self.phaseDates):
            if myTime < phaseDate:
                result = index
                break
        return result
            
    def getNumPhases(self):
        """Return how many phases we have."""
        result =  len(self.phaseDates) + 1
        return result        

    def isValidStart(self, curStartTime):
        """Print out a message if we're starting at a valid time.

        We could start early or later if it's forced by magic words."""
        result = False
        for startAndEnd in self.startAndEndTimes:
            if startAndEnd.isInBetweenInclusive(curStartTime):
                result = True
                break
        
    def start(self):
        """Start the holiday and set us to the correct phase."""
        # start the holiday
        # this equivalent to the same bit of code we use in HolidayManagerAI.createHolidays
        curTime = datetime.datetime.today()
        isValidStart = self.isValidStart(curTime)
        if not isValidStart:
            self.notify.warning("starting holiday %d at %s but self.startAndEndTimes= %s " %
                                (self.holidayId, curTime, self.startAndEndTimes))
        
        pass
    
    
    def stop(self):
        pass
    
    def forcePhase(self, newPhase):
        self.notify.warning("Child class must defined forcePhase")
