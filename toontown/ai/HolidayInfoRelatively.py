#################################################################
# File: HolidayInfoRelatively.py
# Purpose: To have a means of specifying a holiday as
# the position of a specific weekday in a month.
# For instance Halloween is the 5th Friday of October.
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
from copy import deepcopy
import functools
from enum import IntEnum


Day = IntEnum("Day", ('MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', \
            'FRIDAY', 'SATURDAY', 'SUNDAY'), start=0)
            
#################################################################
# Class: HolidayInfo_Relatively
# Purpose: Stores all relevant information regarding an event,
#          such as the type of event.
#################################################################
class HolidayInfo_Relatively(HolidayInfo_Base):
    #############################################################
    # Method: __init__
    # Purpose: Provides initial construction of the Monthly Holiday
    #          Info object. It generates the list of times that
    #          the holiday should be run every week.
    # Input: holidayClass - class type of the holiday, for
    #                       instance - Halloween.
    #       dateList - The date is specified as a pair of the
    #                   following:
    #                   [(Month.OCTOBER, 5, Day.FRIDAY, 10, 0, 0),
    #                    (Month.OCTOBER, 5, Day.FRIDAY, 15, 0, 0) ]
    #       This means that the holiday is on the 5th Friday of October
    #       between 10am and 3pm.
    # Output: None
    ############################################################
    def __init__(self, holidayClass, dateList, displayOnCalendar):
        HolidayInfo_Base.__init__(self, holidayClass, displayOnCalendar)

        dateElemIter = ModifiedIter(dateList)
        for i in range(len(dateList)//2):
            start = dateElemIter.current()
            end = next(dateElemIter)

            self.tupleList.append((start, end))
            next(dateElemIter)

        self.tupleList.sort(key=functools.cmp_to_key(cmpDates))
        self.weekDaysInMonth = []                       # A matrix of the number of times a weekday repeats in a month
        self.numDaysCorMatrix = [(28,0), (29, 1),
                            (30, 2), (31, 3)]           # A matrix of the number of weekdays that repeat one extra
                                                        # time based on the number of days in the month. For instance
                                                        # in a month with 31 days, the first two week days occur
                                                        # one more time than the other days.
        for i in range(7):                              # The minimum number of times a day repeats in a month
            self.weekDaysInMonth.append((i,4))
            
    ############################################################
    # Method: initRepMatrix
    # Initialize the number of times weekdays get
    # repeated in a month method.
    ############################################################
    def initRepMatrix(self, year, month):
        
        for i in range(7):
            self.weekDaysInMonth[i] = (i,4)

        startingWeekDay, numDays = calendar.monthrange(year, month)

        for i in range(4):
            if(numDays == self.numDaysCorMatrix[i][0]):
                break

        for j in range(self.numDaysCorMatrix[i][1]):                                                  # At this point we have a matrix of the weekdays and
            self.weekDaysInMonth[startingWeekDay] = (self.weekDaysInMonth[startingWeekDay][0],
                                                     self.weekDaysInMonth[startingWeekDay][1]+1)   # the number of times they repeat for the current month
            startingWeekDay = (startingWeekDay+1)%7

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
         repNum = t[1]
         weekday = t[2]
         self.initRepMatrix(date[0],t[0])
         while(self.weekDaysInMonth[weekday][1] < repNum):
            repNum -= 1

         day = self.dayForWeekday(date[0], t[0], weekday, repNum)

         return time.mktime((date[0], # year
                            t[0], # month
                            day,  # day
                            t[3], # hour
                            t[4], # second
                            t[5], # minute
                            0,
                            0,
                            -1))
                            
    #############################################################
    # Method: getStartTime
    # Purpose: This method returns the current start time of
    #          the holiday.
    # Input: date - the current date represented as a tuple
    # Output: returns current start time
    #############################################################
    def getStartTime(self, date):
        startTuple, endTuple = self.getUpdatedTuples(self.currElemIter.current())
        return self.getTime(date, startTuple)

    #############################################################
    # Method: getEndTime
    # Purpose: This method returns the current end time of
    #          the holiday.
    # Input: date - the current date represented as a tuple
    # Output: returns current end time
    #############################################################
    def getEndTime(self, date):
        startTuple, endTuple = self.getUpdatedTuples(self.currElemIter.current())
        return self.getTime(date, endTuple)

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
        sCurrYear = time.localtime()[0]
        eCurrYear = sCurrYear
                
        for i in range(len(self.tupleList)):
            startTuple, endTuple = self.getUpdatedTuples(self.currElemIter.peekNext())
            sMonth = startTuple[0]
            nMonth = endTuple[0]
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
                cMonth = time.localtime()[1]
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

                    time1 = (curr[3], curr[4], curr[5])
                    time2 = (startTuple[3], startTuple[4], startTuple[5])

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

    ############################################################
    # Method: getUpdatedTuples
    # Returns the corrected pair of tuples based on
    # the current month and year information
    ############################################################
    def getUpdatedTuples(self, tuples):
        sTuple = list(deepcopy(tuples[0]))
        eTuple = list(deepcopy(tuples[1]))
        sRepNum = sTuple[1]
        sWeekday = sTuple[2]
        eWeekday = eTuple[2]
        while(1):
            eRepNum = eTuple[1]
            self.initRepMatrix(time.localtime()[0], sTuple[0])
            while(self.weekDaysInMonth[sWeekday][1] < sRepNum):
                sRepNum -= 1
            sDay = self.dayForWeekday(time.localtime()[0], sTuple[0], sWeekday, sRepNum)

            self.initRepMatrix(time.localtime()[0], eTuple[0])
            while(self.weekDaysInMonth[eWeekday][1] < eRepNum):
                eRepNum -= 1
            nDay = self.dayForWeekday(time.localtime()[0], eTuple[0], eWeekday, eRepNum)
            if(((nDay>sDay) and (eTuple[0] == sTuple[0]) \
                and ((eTuple[1] - sTuple[1]) <= (nDay-sDay+abs(eWeekday-sWeekday))/7)) \
                or (eTuple[0] != sTuple[0])):
                    break

            # Handles the case when the end weekday is less than the start
            if(self.weekDaysInMonth[eWeekday][1] > eRepNum):
                eRepNum += 1
            else:
                eTuple[0] += 1
                eTuple[1] = 1
        return sTuple, eTuple
    
    ############################################################
    # Method: dayForWeekday(month, weekday, repNum)
    # Returns the day for a given weekday that has repeated
    # repNum times for that month
    ############################################################
    def dayForWeekday(self, year, month, weekday, repNum):
        monthDays = calendar.monthcalendar(year, month)
        if(monthDays[0][weekday] == 0):
            repNum += 1
        return monthDays[(repNum-1)][weekday]