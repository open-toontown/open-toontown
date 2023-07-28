#################################################################
# File: HolidayInfoMonthly.py
# Purpose: Coming Soon...
#################################################################

#################################################################
# Toontown Specific Modules
#################################################################
from toontown.ai.HolidayInfo import *

#################################################################
# Python Specific Modules
#################################################################
import calendar
import random
import time
import functools
#################################################################
# Class: HolidayInfo_Monthly
# Purpose: Stores all relevant information regarding an event,
#          such as the type of event.
#################################################################
class HolidayInfo_Monthly(HolidayInfo_Base):
    #############################################################
    # Method: __init__
    # Purpose: Provides initial construction of the Monthly Holiday
    #          Info object. It generates the list of times that
    #          the holiday should be run every week.
    # Input: holidayClass - class type of the holiday, for
    #                       instance - Fireworks.
    #       dateDict - a dictionary containing the days
    #                  and their corresponding time tuples.
    #                  { 31: [((9, 0, 0), (12, 0, 0))] }
    #                  Holiday starts at 9am PST and ends at
    #                  12pm PST on the 31st of Every Month.
    # Output: None
    ############################################################
    def __init__(self, holidayClass, dateList, displayOnCalendar):
        HolidayInfo_Base.__init__(self, holidayClass, displayOnCalendar)

        dateElemIter = ModifiedIter(dateList)
        for i in range(len(dateList)//2):
            start = dateElemIter.current()
            end = next(dateElemIter)

            finalTuple = self.__setTuplesMonthly(start, end)
            self.tupleList.append(finalTuple)
            next(dateElemIter)

        self.tupleList.sort(key=functools.cmp_to_key(cmpDates))
      
    #############################################################
    # Method: __clampTimeTuples(self, sTuple, eTuple)
    # Purpose: This method clamps any dates that go above the
    #          number of days in the particular month.
    #          For example, suppose the holiday ends on the 31st
    #          of every month. What about February? This clamps
    #          the holiday to the last day of February.
    # Input: date - the current date represented as a tuple
    # Output: returns the adjusted tuple pairing
    #
    # NOTE: This method also adjusts the start tuple day if
    #       the end date needs to be clamped. The adjustment is
    #       by the number of days that the end date is clamped.
    #       The reason for this is that it is assumed that the
    #       holiday should spand x number of days. We merely shift
    #       the days down if a clamping occurs.
    #############################################################
    def __clampTimeTuples(self, sTuple, eTuple):
        year = time.localtime()[0]
        month = time.localtime()[1]
        wday, numDays = calendar.monthrange(year, month)

        if (eTuple[0] > numDays) and (eTuple[0] > sTuple[0]):
            dayOffset = (numDays - eTuple[0])

            # This snippet of code emulates the C++ Ternary operator '?'
            # Clamp the startTuple day to 1 if the offset takes it below 0.
            day = ((sTuple[0]+dayOffset > 0) and [sTuple[0]+dayOffset] or [1])[0]
          
            sTuple  = (day, sTuple[1], sTuple[2], sTuple[3])
            eTuple  = (eTuple[0]+dayOffset, eTuple[1], eTuple[2], eTuple[3])
       
        return (sTuple, eTuple)

    # date comes in the form of date[year, month, day]
    # only day is relevant.

    #############################################################
    # Method: getTime
    # Purpose: This method returns the time. Overrides the base
    # definiton of HolidayInfo.
    # Input: date - the current date represented as a tuple
    # Output: returns the time in secs based on date and t
    #############################################################
    def getTime(self, date, t):
        # t is of the form (day, hour, min, sec)
        # date is of the form (year, month, day, weekday)
        return time.mktime((date[0], # year
                            date[1], # month
                            t[0], # day
                            t[1], # hour
                            t[2], # second
                            t[3], # minute
                            0,
                            0,
                            -1))

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
        currYear = time.localtime()[0]
        sCurrMonth = time.localtime()[1]
        eCurrMonth = sCurrMonth
        
        for i in range(len(self.tupleList)):
            sDay = self.currElemIter.current()[0][0]
            nDay = self.currElemIter.peekNext()[0][0]

            startTuple, endTuple = self.currElemIter.peekNext()

            # If the end day is less than the start day, it is
            # in the proceeding month. Adjust the end month accordingly.
            # This assures that the proper time tuple will be chosen from
            # the list.
            if endTuple[0] < startTuple[0]:
                eCurrMonth += 1

            if sDay > nDay:
                # Since the next day is less than the current day,
                # then we have reached the end of the list and the next
                # date should be in the proceeding month.
                sTime = self.getTime((currYear, sCurrMonth+1,), startTuple)
                eTime = self.getTime((currYear, eCurrMonth+1,), endTuple)                
            elif sDay == nDay:
                # Since the next tuple is of the same day, we must check
                # the time tuples to see if the next time is greater than
                # the current. If it is, that means we have reached the end
                # of the list and should go into the next month.
                curr = self.currElemIter.current()[0]
                time1 = (curr[1], curr[2], curr[3])
                time2 = (startTuple[1], startTuple[2], startTuple[3])
                if time1 > time2:
                    sTime = self.getTime((currYear, sCurrMonth+1,), startTuple)
                    eTime = self.getTime((currYear, eCurrMonth+1,), endTuple)
                else:
                    sTime = self.getTime((currYear, sCurrMonth,), startTuple)
                    eTime = self.getTime((currYear, eCurrMonth,), endTuple)
            else:
                # We have not reached the end of the list, calculate times
                # accordingly.
                sTime = self.getTime((currYear, sCurrMonth,), startTuple)
                eTime = self.getTime((currYear, eCurrMonth,), endTuple)

            next(self.currElemIter)
            if (currTime < eTime):
                return sTime

        # We are back to the original element, thus we should schedule it
        # for the next month.
        start = self.currElemIter.current()[0]
        return self.getTime((currYear, currMonth+1,), start)

    #############################################################
    # Method: adjustDate
    # Purpose: This method adjusts the current day by a month. This
    #          is typically called when an end time is less than
    #          a start time.
    # Input: date - the date that needs to be adjusted
    # Output: None
    #############################################################
    def adjustDate(self, date):
        return (date[0], date[1]+1, date[2], date[3])
  


 

 
