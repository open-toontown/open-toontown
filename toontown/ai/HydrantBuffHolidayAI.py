from direct.directnotify import DirectNotifyGlobal
from toontown.ai import PropBuffHolidayAI

class HydrantBuffHolidayAI(PropBuffHolidayAI.PropBuffHolidayAI):

    notify = DirectNotifyGlobal.directNotify.newCategory(
        'HydrantBuffHolidayAI')

    PostName = 'HydrantBuffHoliday'

    def __init__(self, air, holidayId, startAndEndTimes, phaseDates):
        PropBuffHolidayAI.PropBuffHolidayAI.__init__(self, air, holidayId, startAndEndTimes, phaseDates)
        
