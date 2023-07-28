#################################################################
# File: HolidayInfoDaily.py
# Purpose: Contains the class implementation for daily Holidays.
#################################################################

#################################################################
# Python Specific Modules
#################################################################
from toontown.ai.HolidayInfo import *

#################################################################
# Python Specific Modules
#################################################################
import random
import time

#################################################################
# Class: HolidayInfo_Daily
# Purpose: This HolidayInfo Derived Class is used for holidays
#          that occur on a daily basis. For instance, running
#          a holiday every day at 9 am to 12 pm.
#################################################################
class HolidayInfo_Daily(HolidayInfo_Base):
    #############################################################
    # Method: __init__
    # Purpose: Provides initial construction of the Daily Holiday
    #          Info object. It generates the list of times that
    #          the holiday should be run every day.
    # Input: holidayClass - class type of the holiday, for
    #                       instance - Fireworks.
    #        timeList - a list of tuples containing the start
    #                   and end dates for this holiday.
    # Output: None
    #############################################################
    def __init__(self, holidayClass, dateList, displayOnCalendar):
        HolidayInfo_Base.__init__(self, holidayClass, displayOnCalendar)
        dateElemIter = ModifiedIter(dateList)
        for i in range(len(dateList)//2):
            start = dateElemIter.current()
            end = next(dateElemIter)

            self.tupleList.append((start, end))
            next(dateElemIter)

    #############################################################
    # Method: getNextHolidayTime
    # Purpose: This method finds the next appropriate time to
    #          start this holiday. It searches through the list
    #          of time tuples, and performs the necessary
    #          computations for finding the time.
    # Input: currTime - current time
    # Output: returns the next start time of the holiday
    #############################################################
    def getNextHolidayTime(self, currTime):
        localTime = time.localtime()
        date = (localTime[0],  # year
                 localTime[1],  # month
                 localTime[2],  # day
                 )
        
        for i in range(len(self.tupleList)):
            # Retrieve the Start/End Tuples for the next time
            # the holiday should be scheduled.
            startTuple, endTuple = self.currElemIter.peekNext()
            
            # Retrieve the current Start Time and
            # the next Start Time.
            cStartTime = self.currElemIter.current()[0]
            nStartTime = self.currElemIter.peekNext()[0]

            # If the current Start Time is larger than the
            # next, we have reached the end of the list so
            # we must schedule the 
            if cStartTime > nStartTime:
                sTime = self.getTime((date[0], date[1], date[2]+1,), startTuple)
                eTime = self.getTime((date[0], date[1], date[2]+1,), endTuple)
            else:
                sTime = self.getTime(date, startTuple)
                eTime = self.getTime(date, endTuple)
                if startTuple > endTuple:
                    eTime = self.getTime((date[0], date[1], date[2]+1,), endTuple)
                else:
                    eTime = self.getTime(date, endTuple)

            # Iterate to the next time before we check validity
            # of the time.
            next(self.currElemIter)
            if (currTime < eTime):
                return sTime
                
        # We are back to the original element, thus we should
        # schedule it for the next day.
        start = self.currElemIter.current()[0]
        return self.getTime((date[0], date[1], date[2]+1,), start)

    #############################################################
    # Method: adjustDate
    # Purpose: This method adjusts the current day by one. This
    #          is typically called when an end time is less than
    #          a start time.
    # Input: date - the date that needs to be adjusted
    # Output: None
    #############################################################
    def adjustDate(self, date):
        return (date[0], date[1], date[2]+1, date[3])

