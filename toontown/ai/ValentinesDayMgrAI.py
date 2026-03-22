from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals, TTLocalizer
from toontown.ai import HolidayBaseAI

class ValentinesDayMgrAI(HolidayBaseAI.HolidayBaseAI):

    notify = DirectNotifyGlobal.directNotify.newCategory(
        'ValentinesDayMgrAI')

    PostName = 'ValentinesDay'
    StartStopMsg = 'ValentinesDayStartStop'

    def __init__(self, air, holidayId):
        HolidayBaseAI.HolidayBaseAI.__init__(self, air, holidayId)

    def start(self):
        # Let the holiday system know we started
        bboard.post(ValentinesDayMgrAI.PostName, True)

    def stop(self):
        # Let the holiday system know we stopped
        bboard.remove(ValentinesDayMgrAI.PostName)
        