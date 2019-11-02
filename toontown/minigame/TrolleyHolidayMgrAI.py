from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals, TTLocalizer
from toontown.ai import HolidayBaseAI

class TrolleyHolidayMgrAI(HolidayBaseAI.HolidayBaseAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('TrolleyHolidayMgrAI')
    PostName = 'TrolleyHoliday'
    StartStopMsg = 'TrolleyHolidayStartStop'

    def __init__(self, air, holidayId):
        HolidayBaseAI.HolidayBaseAI.__init__(self, air, holidayId)

    def start(self):
        bboard.post(TrolleyHolidayMgrAI.PostName, True)
        simbase.air.newsManager.trolleyHolidayStart()
        messenger.send(TrolleyHolidayMgrAI.StartStopMsg)

    def stop(self):
        bboard.remove(TrolleyHolidayMgrAI.PostName)
        simbase.air.newsManager.trolleyHolidayEnd()
        messenger.send(TrolleyHolidayMgrAI.StartStopMsg)
