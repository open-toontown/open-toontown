"""
# File: HolidayInfoYearly.py
# Purpose: Coming Soon...
"""

# Toontown Specific Modules
from toontown.ai.HolidayInfo import *

# Python Specific Modules
import random
import time
import functools


class HolidayInfo_Yearly(HolidayInfo_Base):
    """
    Stores all relevant information regarding an event,
    such as the type of event.
    """

    def __init__(self, holidayClass, dateList, displayOnCalendar):
        """
        Purpose: Provides initial construction of the Monthly Holiday
                 Info object. It generates the list of times that
                 the holiday should be run every week.
        Input: holidayClass - class type of the holiday, for
                              instance - Fireworks.
              dateDict - a dictionary containing the Months,
                         which each have a dictionary of days with
                         their corresponding times.
                         { Month.JULY: {31: [((9, 0, 0), (12, 0, 0))]} }
                         Holiday starts at 9am PST and ends at
                         12pm PST on July 31st of Every Year.
        Output: None
        """
        HolidayInfo_Base.__init__(self, holidayClass, displayOnCalendar)
        dateElemIter = ModifiedIter(dateList)
        for i in range(len(dateList)//2):
            start = dateElemIter.current()
            end = next(dateElemIter)

            self.tupleList.append((start, end))
            next(dateElemIter)

        self.tupleList.sort(key=functools.cmp_to_key(cmpDates))

    def getTime(self, date, t):
        """
        Purpose: This method returns the time. Overrides the base
                 definiton of HolidayInfo.
        Input: date - the current date represented as a tuple
        Output: returns the time in secs based on date and t
        """
        # t is of the form (month, day, hour, min, sec)
        # date is of the form (year, month, day, weekday)
        return time.mktime((date[0], # year
                            t[0], # month
                            t[1], # day
                            t[2], # hour
                            t[3], # second
                            t[4], # minute
                            0,
                            0,
                            -1))

    def getNextHolidayTime(self, currTime):
        """
        Purpose: This method finds the next appropriate time to
                 start this holiday. It searches through the list
                 of time tuples, and performs the necessary
                 computations for finding the time.
        Input: currTime - current time
        Output: returns the next start time of the holiday
        """
        sCurrYear = time.localtime()[0]
        eCurrYear = sCurrYear

        for i in range(len(self.tupleList)):
            sMonth = self.currElemIter.current()[0][0]
            nMonth = self.currElemIter.peekNext()[0][0]

            startTuple, endTuple = self.currElemIter.peekNext()
            # If the end month is less than the start month, it is
            # in the proceeding year. Adjust the end year accordingly.
            # This assures that the proper time tuple will be chosen from
            # the list.
            if endTuple[0] < startTuple[0]:
                eCurrYear += 1

            if sMonth > nMonth:
                # The holiday should be scheduled in the
                # following year. There are two cases that
                # may exist and they follow:
                # Case 1: { May: [31], July: [(31)] }
                #  - Here, we end on July 31. The next
                #    time the holiday should start is on
                #    May 31, which would be in the following
                #    year.
                # Case 2: { December: [(31, 1)], May: [31] }
                #  - Here, we end on January 1 of the new year,
                #    because this holiday spans from December
                #    to January. The next time the holiday should
                #    start is on May 31, which would be in the
                #    same year.

                # Check to see if we are already in the next
                # year due to overlapping holiday.
                cMonth = time.localtime()[0]
                if cMonth > nMonth:
                    # We have not crossed over into the new week
                    # as found in case 1.
                    sTime = self.getTime((sCurrYear+1,), startTuple)
                    eTime = self.getTime((eCurrYear+1,), endTuple)
                else:
                    # We have already started the new year as found
                    # in case 2. Adjust time normally.
                    sTime = self.getTime((sCurrYear,), startTuple)
                    eTime = self.getTime((eCurrYear,), endTuple)
            elif sMonth == nMonth:
                sDay = self.currElemIter.current()[0][1]
                nDay = self.currElemIter.peekNext()[0][1]

                if sDay > nDay:
                    # Since the next day is less than the current day,
                    # then we have reached the end of the list and the next
                    # date should be in the proceeding year.
                    sTime = self.getTime((sCurrYear+1,), startTuple)
                    eTime = self.getTime((eCurrYear+1,), endTuple)
                elif sDay == nDay:
                    # Since the next tuple is of the same day, we must check
                    # the time tuples to see if the next time is greater than
                    # the current. If it is, that means we have reached the end
                    # of the list and should go into the next year..
                    curr = self.currElemIter.current()[0]

                    time1 = (curr[2], curr[3], curr[4])
                    time2 = (startTuple[2], startTuple[3], startTuple[4])

                    if time1 > time2:
                        sTime = self.getTime((sCurrYear+1,), startTuple)
                        eTime = self.getTime((eCurrYear+1,), endTuple)
                    else:
                        sTime = self.getTime((sCurrYear,), startTuple)
                        eTime = self.getTime((eCurrYear,), endTuple)
                else:
                    # We have not reached the end of the list, calculate times
                    # accordingly.
                    sTime = self.getTime((sCurrYear,), startTuple)
                    eTime = self.getTime((eCurrYear,), endTuple)
            else:
                # We have not reached the end of the list, calculate times
                # accordingly.
                sTime = self.getTime((sCurrYear,), startTuple)
                eTime = self.getTime((eCurrYear,), endTuple)

            next(self.currElemIter)
            if (currTime < eTime):
                return sTime

        # We are back to the original element, thus we should
        # schedule it for the next year.
        start = self.currElemIter.current()[0]
        return self.getTime((sCurrYear+1,), start)

    def adjustDate(self, date):
        """
        Purpose: This method adjusts the current day by a year. This
                 is typically called when an end time is less than
                 a start time.
        Input: date - the date that needs to be adjusted
        Output: None
        """
        return (date[0]+1, date[1], date[2], date[3])

