from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals, TTLocalizer
from toontown.ai import HolidayBaseAI

class RoamingTrialerWeekendMgrAI(HolidayBaseAI.HolidayBaseAI):

    notify = DirectNotifyGlobal.directNotify.newCategory(
        'RoamingTrialerWeekendMgrAI')

    PostName = 'RoamingTrialerWeekend'
    StartStopMsg = 'RoamingTrialerWeekendStartStop'

    def __init__(self, air, holidayId):
        HolidayBaseAI.HolidayBaseAI.__init__(self, air, holidayId)

    def start(self):
        # let the holiday system know we started
        bboard.post(RoamingTrialerWeekendMgrAI.PostName, True)

        # tell everyone race night is starting
        simbase.air.newsManager.roamingTrialerWeekendStart()

        messenger.send(RoamingTrialerWeekendMgrAI.StartStopMsg)

    def stop(self):
        # let the holiday system know we stopped
        bboard.remove(RoamingTrialerWeekendMgrAI.PostName)

        # tell everyone race night is stopping
        simbase.air.newsManager.roamingTrialerWeekendEnd()

        messenger.send(RoamingTrialerWeekendMgrAI.StartStopMsg)
