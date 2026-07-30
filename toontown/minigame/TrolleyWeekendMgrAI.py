from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals, TTLocalizer
from toontown.ai import HolidayBaseAI

class TrolleyWeekendMgrAI(HolidayBaseAI.HolidayBaseAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('TrolleyWeekendMgrAI')
    PostName = 'TrolleyWeekend'
    StartStopMsg = 'TrolleyWeekendStartStop'

    def __init__(self, air, holidayId):
        HolidayBaseAI.HolidayBaseAI.__init__(self, air, holidayId)

    def start(self):
        bboard.post(TrolleyWeekendMgrAI.PostName, True)
        simbase.air.newsManager.trolleyWeekendStart()
        messenger.send(TrolleyWeekendMgrAI.StartStopMsg)

    def stop(self):
        bboard.remove(TrolleyWeekendMgrAI.PostName)
        simbase.air.newsManager.trolleyWeekendEnd()
        messenger.send(TrolleyWeekendMgrAI.StartStopMsg)
