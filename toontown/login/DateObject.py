import time

class DateObject:

    def getYear(self):
        return time.localtime(time.time())[0]

    def getMonth(self):
        return time.localtime(time.time())[1]

    def getDay(self):
        return time.localtime(time.time())[2]

    def getDetailedAge(self, dobMonth, dobYear, dobDay = None, curMonth = None, curYear = None, curDay = None):
        if curMonth is None:
            curMonth = self.getMonth()
        if curYear is None:
            curYear = self.getYear()
        if curDay is None:
            curDay = self.getDay()
        curMonths = curYear * 12 + (curMonth - 1)
        dobMonths = dobYear * 12 + (dobMonth - 1)
        if dobMonth == curMonth:
            if dobDay is not None:
                if dobDay > curDay:
                    curMonths -= 1
        ageMonths = curMonths - dobMonths
        return (int(ageMonths / 12), ageMonths % 12)

    def getAge(self, dobMonth, dobYear, dobDay = None, curMonth = None, curYear = None, curDay = None):
        return self.getDetailedAge(dobMonth, dobYear, dobDay=dobDay, curMonth=curMonth, curYear=curYear, curDay=curDay)[0]

    def getNumDaysInMonth(self, month = None, year = None):

        def isLeapYear(year):
            if year % 4 == 0:
                if year % 100 == 0:
                    if year % 400 == 0:
                        return 1
                    else:
                        return 0
                else:
                    return 1
            else:
                return 0

        if month is None:
            m = self.getMonth()
        else:
            m = month
        if year is None:
            y = self.getYear()
        else:
            y = year
        if m == 2:
            if isLeapYear(y):
                return 29
            else:
                return 28
        elif m in (1, 3, 5, 7, 8, 10, 12):
            return 31
        else:
            return 30
        return
