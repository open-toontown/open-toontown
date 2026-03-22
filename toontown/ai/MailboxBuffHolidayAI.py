from direct.directnotify import DirectNotifyGlobal
from toontown.ai import PropBuffHolidayAI

class MailboxBuffHolidayAI(PropBuffHolidayAI.PropBuffHolidayAI):

    notify = DirectNotifyGlobal.directNotify.newCategory(
        'MailboxBuffHolidayAI')

    PostName = 'MailboxBuffHoliday'

    def __init__(self, air, holidayId, startAndEndTimes, phaseDates):
        PropBuffHolidayAI.PropBuffHolidayAI.__init__(self, air, holidayId, startAndEndTimes, phaseDates)
        
