#################################################################
# File: HolidayInfo.py
# Purpose: Coming Soon...
#################################################################

#################################################################
# Python Specific Modules
#################################################################
import random
import time

#################################################################
# Global Methods
#################################################################

#############################################################
# Method: cmpTime
# Purpose: This method is used when sorting a list based
#          on two time tuples. For the HolidayInfo tuples,
#          we would like the list of tuples to be ordered
#          in a chronological sequence for easy of transition
#          from one holiday date to the next.
# Input: None
# Output: returns the comparison value
#############################################################
def cmpDates(tuple1, tuple2):
    numValues = len(tuple1)

    for i in range(numValues):
        if tuple1[i] > tuple2[i]:
            return 1
        elif tuple1[i] < tuple2[i]:
            return -1

    return 0  

#################################################################
# Class: ModfiedIter
# Purpose: The python iterator only allows one to go forward
#          and ends
# NOTE: Implementation for this will likely change so that it
#       will handle removals from the sequence gracefully. This
#       currently does not do so.
#################################################################
class ModifiedIter:
    def __init__(self, seq):
       self._seq = seq
       self._idx = 0
       self._storedIndex = 0

    #############################################################
    # Method: current
    # Purpose: This method returns the current element that the
    #          iterator references.
    # Input: None
    # Output: returns the current element
    #############################################################
    def current(self):
        try:
            return self._seq[self._idx]
        except IndexError:
            raise StopIteration

    #############################################################
    # Method: next
    # Purpose: This method emulates the python next method in that
    #          it updates the reference to the next element in
    #          the sequence. Unlike the python next method, it
    #          wraps around the sequence.
    # Input: None
    # Output: returns the new current element
    #############################################################
    def __next__(self):
        try:
            lastIdx = len(self._seq) - 1
            self._idx = ((lastIdx == self._idx) and [0] or [self._idx+1])[0]
            return self._seq[self._idx]
        except IndexError:
            raise StopIteration

    #############################################################
    # Method: prev
    # Purpose: This method is similar to the python next method
    #          except that it updates the reference to the previous
    #          element in the sequence. This method wraps around
    #          around the sequence.
    # Input: None
    # Output: returns the new current element
    #############################################################
    def prev(self):
        try:
            lastIdx = len(self._seq) - 1
            self._idx = ((self._idx == 0) and [lastIdx] or [self._idx-1])[0]
            return self._seq[self._idx]
        except IndexError:
            raise StopIteration

    #############################################################
    # Method: peekNext
    # Purpose: This method provides a look at functionality to
    #          see the next element in the list.
    # Input: None
    # Output: returns the next element
    #############################################################
    def peekNext(self):
        try:
            idx = self._idx
            lastIdx = len(self._seq) - 1
            idx = ((lastIdx == idx) and [0] or [idx+1])[0]
            return self._seq[idx]
        except:
            raise StopIteration

    #############################################################
    # Method: peekPrev
    # Purpose: This method provides a look at functionality to
    #          see the previous element in the list.
    # Input: None
    # Output: returns the next element
    #############################################################
    def peekPrev(self):
        try:
            idx = self._idx
            lastIdx = len(self._seq) - 1
            idx = ((idx == 0) and [lastIdx] or [idx-1])[0]
            return self._seq[idx]
        except IndexError:
            raise StopIteration

    #############################################################
    # Method: setTo
    # Purpose: This method sets the iterator to a known element
    # Input: an element
    # Output: true if element was found, false otherwise
    #############################################################
    def setTo(self, element):
        try:
            index = self._seq.index(element)
            self._idx = index
            return True
        except ValueError:
            return False

    #############################################################
    # Method: store
    # Purpose: This method stores the iterator state
    # Input: None
    # Output: None
    #############################################################
    def store(self):
        self._storedIndex = self._idx

    #############################################################
    # Method: store
    # Purpose: This method restores the iterator state
    # Input: None
    # Output: None
    #############################################################
    def restore(self):
        self._idx = self._storedIndex

#################################################################
# Class: HolidayInfo_Base
# Purpose: A Base Class for all derived.
#################################################################
class HolidayInfo_Base:
    #############################################################
    # Method: __init__
    # Purpose: Provides initial construction of the HolidayInfo
    #          instance.
    # Input: holidayClass - class type of the holiday, for
    #                       instance - Fireworks.
    # Output: None
    #############################################################
    def __init__(self, holidayClass, displayOnCalendar):
        self.__holidayClass = holidayClass
        self.tupleList = []
        self.currElemIter = ModifiedIter(self.tupleList)
        self.displayOnCalendar = displayOnCalendar

    #############################################################
    # Method: getClass
    # Purpose: This method returns the class type of the
    #          Holiday.
    # Input: None
    # Output: returns Holiday Class Type
    #############################################################
    def getClass(self):
        return self.__holidayClass

    #############################################################
    # Method: getStartTime
    # Purpose: This method returns the current start time of
    #          the holiday.
    # Input: date - the current date represented as a tuple
    # Output: returns current start time
    #############################################################
    def getStartTime(self, date):
        startTuple = self.currElemIter.current()[0]
        return self.getTime(date, startTuple)

    #############################################################
    # Method: getEndTime
    # Purpose: This method returns the current end time of
    #          the holiday.
    # Input: date - the current date represented as a tuple
    # Output: returns current end time
    #############################################################
    def getEndTime(self, date):
        endTuple = self.currElemIter.current()[1]
        return self.getTime(date, endTuple)

    #############################################################
    # Method: getDate
    # Purpose: This method returns the current date in a known format
    # Input: None
    # Output: date represented as a tuple
    #############################################################
    def getDate(self):
        localtime = time.localtime()
        date = (localtime[0], # Year
                localtime[1], # Month
                localtime[2], # Day
                localtime[6]) # WDay

        return date

    #############################################################
    # Method: getTime
    # Purpose: This method returns the time based on the supplied
    #          date and t.
    # Input: date - the current date represented as a tuple
    #        t - the current time tuple
    # Output: returns the time in secs based on date and t
    #############################################################
    def getTime(self, date, t):
        return time.mktime((date[0],
                            date[1],
                            date[2],
                            t[0],
                            t[1],
                            t[2],
                            0,
                            0,
                            -1))

    #############################################################
    # Method: getNumHolidays
    # Purpose: This method returns the number of dates on which
    #          the holiday will be played.
    # Input: None
    # Output: returns the number of dates
    #############################################################
    def getNumHolidays(self):
        return len(self.tupleList)

    def hasPhaseDates(self):
        """Returns true if the holiday ramps us over time to several different phases."""
        return False

    def getPhaseDates(self):
        """Used when the holiday ramps us over time to several different phases.
        Returns None when the holiday does not use phases"""
        return None
