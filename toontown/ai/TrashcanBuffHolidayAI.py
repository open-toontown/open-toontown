from direct.directnotify import DirectNotifyGlobal
from toontown.ai import HolidayBaseAI
from toontown.ai import PropBuffHolidayAI
from toontown.ai import DistributedPhaseEventMgrAI
from toontown.toonbase import ToontownGlobals

class TrashcanBuffHolidayAI(PropBuffHolidayAI.PropBuffHolidayAI):

    notify = DirectNotifyGlobal.directNotify.newCategory(
        'TrashcanBuffHolidayAI')

    PostName = 'TrashcanBuffHoliday'

    def __init__(self, air, holidayId, startAndEndTimes, phaseDates):
        PropBuffHolidayAI.PropBuffHolidayAI.__init__(self, air, holidayId, startAndEndTimes, phaseDates)
        
