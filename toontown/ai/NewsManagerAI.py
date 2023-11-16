from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI


class NewsManagerAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('NewsManagerAI')

    def getWeeklyCalendarHolidays(self):
        return []

    def getYearlyCalendarHolidays(self):
        return []

    def getOncelyCalendarHolidays(self):
        return []

    def getRelativelyCalendarHolidays(self):
        return []

    def getMultipleStartHolidays(self):
        return []
