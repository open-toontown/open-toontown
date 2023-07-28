#################################################################
# File: HolidayInfoWeekly.py
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
import functools

#################################################################
# Class: HolidayInfo_Weekly
# Purpose: Stores all relevant information regarding a holiday.
# Note: Monday is designated as the first day of the week.
#################################################################
class HolidayInfo_Weekly(HolidayInfo_Base):
    #############################################################
    # Method: __init__
    # Purpose: Provides initial construction of the Weekly Holiday
    #          Info object. It generates the list of times that
    #          the holiday should be run every week.
    # Input: holidayClass - class type of the holiday, for
    #                       instance - Fireworks.
    #       dateDict - a dictionary containing the weekdays
    #                  and their corresponding time tuples.
    #                  { Day.Monday: [((9, 0, 0), (12, 0, 0))] }
    #                  Holiday starts at 9am PST and ends at
    #                  12pm PST every Monday.
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

        self.tupleList.sort(key=functools.cmp_to_key(cmpDates))

    #############################################################
    # Method: getStartTime
    # Purpose: This method returns the current start time of
    #          the holiday. Overrides the base definiton of
    #          HolidayInfo.
    # Input: date - the current date represented as a tuple
    # Output: returns current start time
    #############################################################
    def getStartTime(self, date):
        startTuple = self.currElemIter.current()[0]
        return self.getTime(date, startTuple, True)

    #############################################################
    # Method: getEndTime
    # Purpose: This method returns the current end time of
    #          the holiday. Overrides the base definiton of
    #          HolidayInfo.
    # Input: date - the current date represented as a tuple
    # Output: returns current end time
    #############################################################
    def getEndTime(self, date):
        endTuple = self.currElemIter.current()[1]
        return self.getTime(date, endTuple, False)

    #############################################################
    # Method: getTime
    # Purpose: This method returns the time. Overrides the base
    # definiton of HolidayInfo.
    # Input: date - the current date represented as a tuple
    #        t - the current time tuple
    #        isStart - True if we want starting time,
    #                  False if we want end time.
    #        isNextWeek - True if time should be computed for
    #                     the next week, false if it should be
    #                     computed for this week.
    # Output: returns the time in secs based on date and t
    #############################################################
    def getTime(self, date, t, isStart = True, isNextWeek=False):
        #print "Getting time for date = %s and t = %s" % (date, t)
        cWDay = date[3]
        sWDay = t[0]
        dayOffset = sWDay - cWDay
        if isNextWeek:
            dayOffset += 7
            
        day = date[2] + dayOffset
        
        actualTime = time.mktime((date[0], date[1], day,
                             t[1], t[2], t[3],
                             0, 0, -1))

        #print time.ctime(actualTime)

        return actualTime

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
        date = self.getDate()

        foundTime = None
        # look through the list of holidays for the first one we haven't hit
        # (don't attempt to increment the week)
        for start, end in self.tupleList:
            nextStartTime = self.getTime(date, start, True, False)
            nextEndTime = self.getTime(date, end, False, False)
            # We add a one minute fudge factor to prevent the current
            # holiday from restarting if its endHoliday doLater fires early.
            # This has the side effect that if the AI starts within one minute
            # of a holiday ending, it will NOT start the holiday.
            if currTime + 59 < nextEndTime:
                foundTime = nextStartTime
                break

        if not foundTime:
            # we have already passed the start time for all of these,
            # add one week to the first one and use that
            start, end = self.tupleList[0]
            date = self.adjustDate(date)
            foundTime = self.getTime(date, start, True, False)

        self.currElemIter.setTo((start, end))
        return foundTime

        """
        for i in xrange(len((self.tupleList))):
            # Retrieve Starting WDay for the current Element
            # and the next element in the sequence.
            sWDay = self.currElemIter.current()[0][0]
            nWDay = self.currElemIter.peekNext()[0][0]

            if sWDay > nWDay:
                # The next date is in the following week. There
                # are two cases that can exist and they follow:
                # Case 1: [(1, 2), 3, 5]
                #  - Here, we have ended on a
                #    Saturday(5). The next time the holiday
                #    should fire up is on a Tuesday(1) of the
                #    next week.
                # Case 2: [(6, 1), 3]
                # - Here, we have ended on a Tuesday(1). The
                #  next time the holiday should fire will be
                # on the Thursday(3) of the same week.
            
                # Check to see if we are already in the next
                # week due to overlapping holiday.
                cWDay = date[3]

                startTuple, endTuple = self.currElemIter.next()
                if cWDay > nWDay:
                    # We have not started the new week as found
                    # in case 1.
                    sTime = self.getTime(date, startTuple, True, False)
                else:
                    # We have already started the new week as found
                    # in case 2. Adjust time normally.
                    sTime = self.getTime(date, startTuple, True)
                    
            else:
                startTuple, endTuple = self.currElemIter.next()
                sTime = self.getTime(date, startTuple, True)

            # Perform Check
            if (currTime < sTime):
                # Found next holiday day
                return sTime                           

        # This means that we arrived back to the original
        # starting place. Update date and find time for
        # next starting of holiday.
        date = (date[0], date[1], date[2]+7, date[3])
        startTuple = self.currElemIter.current()[0]
        sTime = self.getTime(date, startTuple, True, True)
        return sTime
        """

    #############################################################
    # Method: adjustDate
    # Purpose: This method adjusts the current day by a week. This
    #          is typically called when an end time is less than
    #          a start time.
    # Input: date - the date that needs to be adjusted
    # Output: None
    #############################################################    
    def adjustDate(self, date):
        return (date[0], date[1], date[2]+7, date[3])
            
