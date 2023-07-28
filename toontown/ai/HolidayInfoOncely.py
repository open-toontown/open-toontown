#################################################################
# File: HolidayInfoOncely.py
# Purpose: Coming Soon...
#################################################################

#################################################################
# Toontown Specific Modules
#################################################################
from toontown.ai.HolidayInfo import *

#################################################################
# Python Specific Modules
#################################################################
import random
import time
import datetime
import functools

#################################################################
# Class: HolidayInfo_Oncely
# Purpose: Stores all relevant information regarding an event,
#          such as the type of event.
#################################################################
class HolidayInfo_Oncely(HolidayInfo_Base):
    #############################################################
    # Method: __init__
    # Purpose: Provides initial construction of the Oncely Holiday
    #          Info object. This type of holiday only happens once!
    #   
    # Input: holidayClass - class type of the holiday, for
    #                       instance - Fireworks.
    #       dateDict - a dictionary containing the Months,
    #                  which each have a dictionary of days with
    #                  their corresponding times.
    #                  { Month.JULY: {31: [((9, 0, 0), (12, 0, 0))]} }
    #                  Holiday starts at 9am PST and ends at
    #                  12pm PST on July 31st of Every Year.
    # Output: None
    ############################################################
    def __init__(self, holidayClass, dateList, displayOnCalendar, phaseDates = None, testHolidays = None):
        """Phase dates adds a way for a ramping up holiday to go to the next phase."""
        # I briefly considered putting phase dates in the definition of the HolidayAI class
        # but then that would put when it starts, and the different phase times in two
        # separate files.  This feels much safer.
        # Implicit in this definition, if a holiday has 1 phase date, there are 2 phases
        HolidayInfo_Base.__init__(self, holidayClass, displayOnCalendar)
        dateElemIter = ModifiedIter(dateList)
        for i in range(len(dateList)//2):
            start = dateElemIter.current()
            end = next(dateElemIter)

            self.tupleList.append((start, end))
            next(dateElemIter)

        self.tupleList.sort(key=functools.cmp_to_key(cmpDates))
        self.phaseDates = None
        self.curPhase = 0
        if phaseDates:
            self.processPhaseDates(phaseDates)
            
        self.testHolidays = testHolidays

    #############################################################
    # Method: getTime
    # Purpose: This method returns the time. Overrides the base
    # definiton of HolidayInfo.
    # Input: date - the current date represented as a tuple
    # Output: returns the time in secs based on date and t
    #############################################################
    def getTime(self, date, t):
        # t is of the form (year, month, day, hour, min, sec)
        # date is of the form (year, month, day, weekday) - not used in this class
        return time.mktime((t[0], # year
                            t[1], # month
                            t[2], # day
                            t[3], # hour
                            t[4], # second
                            t[5], # minute
                            0,
                            0,
                            -1))

    #############################################################
    # Method: getNextHolidayTime
    # Purpose: This type of holiday only happens once, so just return None
    #          
    # Input: currTime - current time
    # Output: returns the next start time of the holiday
    #############################################################
    def getNextHolidayTime(self, currTime):
        """
        Purpose: This method finds the next appropriate time to
                 start this holiday. It searches through the list
                 of time tuples, and performs the necessary
                 computations for finding the time.
        Input: currTime - current time
        Output: returns the next start time of the holiday, could be None
        """
        result = None

        for i in range(len(self.tupleList)):
            if i == 0:
                # we need to setup currElem properly if we start
                # in the middle of a oncely holiday with multiple starts
                self.currElemIter.setTo(self.tupleList[0])
            startTuple = self.tupleList[i][0]
            endTuple = self.tupleList[i][1]

            startNextTime = self.getTime(None, startTuple)
            endNextTime = self.getTime(None, endTuple)
            
            if startNextTime <= currTime and \
               currTime <= endNextTime:
                # we are between a start time and end time tuple
                # start it now
                result = currTime
                break;
            
            if currTime < startNextTime and \
               currTime < endNextTime:
                # we are waiting for the next pair of start,end times to arrive
                result = startNextTime
                break;            
            next(self.currElemIter)
        return result
    
    #############################################################
    # Method: adjustDate
    # Purpose: This method adjusts the current day by a year. This
    #          is typically called when an end time is less than
    #          a start time.
    # Input: date - the date that needs to be adjusted
    # Output: None
    #############################################################
    def adjustDate(self, date):
        return (date[0]+1, date[1], date[2], date[3])

    def processPhaseDates(self, phaseDates):
        """Convert the phase dates into datetimes."""
        self.phaseDates = []
        for curDate in phaseDates:
            newTime = datetime.datetime(curDate[0], curDate[1], curDate[2], curDate[3], curDate[4], curDate[5])
            self.phaseDates.append(newTime)

    def getPhaseDates(self):
        """Returns our phase dates, should be None if not used."""
        return self.phaseDates

    def hasPhaseDates(self):
        """Returns False if we don't use phase dates."""
        if self.phaseDates:
            return True
        else:
            return False
            
    #############################################################
    # Run holiday in test mode
    # Used to invoke other holidays for debugging purposes        
    #############################################################    

    def isTestHoliday(self):
        """ Returns true if running the holiday in test mode """
        if self.testHolidays:
            return True
        else:
            return False
            
    def getTestHolidays(self):
        return self.testHolidays