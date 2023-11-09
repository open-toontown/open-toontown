from direct.directnotify import DirectNotifyGlobal
from toontown.ai import HolidayBaseAI
from toontown.ai import PropBuffHolidayAI
from toontown.ai import DistributedPhaseEventMgrAI
from toontown.toonbase import ToontownGlobals

class HydrantBuffHolidayAI(PropBuffHolidayAI.PropBuffHolidayAI):

    notify = DirectNotifyGlobal.directNotify.newCategory(
        'HydrantBuffHolidayAI')

    PostName = 'HydrantBuffHoliday'

    def __init__(self, air, holidayId, startAndEndTimes, phaseDates):
        PropBuffHolidayAI.PropBuffHolidayAI.__init__(self, air, holidayId, startAndEndTimes, phaseDates)
        
