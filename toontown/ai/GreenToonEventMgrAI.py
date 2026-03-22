from direct.directnotify import DirectNotifyGlobal
from toontown.ai import HolidayBaseAI
from toontown.toonbase import ToontownGlobals
from toontown.ai import DistributedGreenToonEffectMgrAI

EVENT_ZONE = 5819 # 'Green Bean Jeans' interior

class GreenToonEventMgrAI(HolidayBaseAI.HolidayBaseAI):

    notify = DirectNotifyGlobal.directNotify.newCategory(
        'GreenToonEventMgrAI')

    PostName = 'greenToonEvent'

    def __init__(self, air, holidayId):
        HolidayBaseAI.HolidayBaseAI.__init__(self, air, holidayId)
        self.greenToonEmoteMgr = None

    def start(self):
        # instantiate the object
        self.greenToonEmoteMgr = DistributedGreenToonEffectMgrAI.DistributedGreenToonEffectMgrAI(
            self.air)
        self.greenToonEmoteMgr.generateWithRequired(EVENT_ZONE)
        # let the holiday system know we started
        bboard.post(GreenToonEventMgrAI.PostName)

    def stop(self):
        # let the holiday system know we stopped
        bboard.remove(GreenToonEventMgrAI.PostName)
        # remove the object
        self.greenToonEmoteMgr.requestDelete()
