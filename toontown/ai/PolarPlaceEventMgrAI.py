from direct.directnotify import DirectNotifyGlobal
from toontown.ai import HolidayBaseAI
from toontown.toonbase import ToontownGlobals
from toontown.ai import DistributedPolarPlaceEffectMgrAI

EVENT_ZONE = 3821 # 'Hibernation Vacations' interior

class PolarPlaceEventMgrAI(HolidayBaseAI.HolidayBaseAI):

    notify = DirectNotifyGlobal.directNotify.newCategory(
        'PolarPlaceEventMgrAI')

    PostName = 'polarPlaceEvent'

    def __init__(self, air, holidayId):
        HolidayBaseAI.HolidayBaseAI.__init__(self, air, holidayId)
        self.polarPlaceEmoteMgr = None
        
    def start(self):
        # instantiate the object
        self.polarPlaceEmoteMgr = DistributedPolarPlaceEffectMgrAI.DistributedPolarPlaceEffectMgrAI(
            self.air)
        self.polarPlaceEmoteMgr.generateWithRequired(EVENT_ZONE)
        # let the holiday system know we started
        bboard.post(PolarPlaceEventMgrAI.PostName)

    def stop(self):
        # let the holiday system know we stopped
        bboard.remove(PolarPlaceEventMgrAI.PostName)
        # remove the object
        self.polarPlaceEmoteMgr.requestDelete()
