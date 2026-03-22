from direct.directnotify import DirectNotifyGlobal
from toontown.ai import HolidayBaseAI

class BlackCatHolidayMgrAI(HolidayBaseAI.HolidayBaseAI):
    notify = DirectNotifyGlobal.directNotify.newCategory(
        'BlackCatHolidayMgrAI')

    PostName = 'blackCatHoliday'

    def __init__(self, air, holidayId):
        HolidayBaseAI.HolidayBaseAI.__init__(self, air, holidayId)

    def start(self):
        bboard.post(BlackCatHolidayMgrAI.PostName)

    def stop(self):
        bboard.remove(BlackCatHolidayMgrAI.PostName)
