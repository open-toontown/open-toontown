import DateObject

class TTDateObject(DateObject.DateObject):

    def __init__(self, accountServerDate):
        self.accountServerDate = accountServerDate

    def getYear(self):
        return self.accountServerDate.getYear()

    def getMonth(self):
        return self.accountServerDate.getMonth()

    def getDay(self):
        return self.accountServerDate.getDay()

    def getDetailedAge(self, dobMonth, dobYear, dobDay = None, curMonth = None, curYear = None, curDay = None):
        return DateObject.DateObject.getDetailedAge(self, dobMonth, dobYear, dobDay, curMonth=self.getMonth(), curYear=self.getYear(), curDay=self.getDay())

    def getAge(self, dobMonth, dobYear, dobDay = None, curMonth = None, curYear = None, curDay = None):
        return TTDateObject.getDetailedAge(self, dobMonth, dobYear, dobDay=dobDay, curMonth=curMonth, curYear=curYear, curDay=curDay)[0]
