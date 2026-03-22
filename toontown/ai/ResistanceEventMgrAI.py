from direct.directnotify import DirectNotifyGlobal
from toontown.ai import HolidayBaseAI
from toontown.toonbase import ToontownGlobals
from toontown.ai import DistributedResistanceEmoteMgrAI

EVENT_ZONE = 9720 # 'Talking in Your Sleep Voiceover Training' interior

class ResistanceEventMgrAI(HolidayBaseAI.HolidayBaseAI):

    notify = DirectNotifyGlobal.directNotify.newCategory(
        'ResistanceEventMgrAI')

    PostName = 'resistanceEvent'

    def __init__(self, air, holidayId):
        HolidayBaseAI.HolidayBaseAI.__init__(self, air, holidayId)
        self.resistanceEmoteMgr = None
        
    def start(self):
        # instantiate the object
        self.resistanceEmoteMgr = DistributedResistanceEmoteMgrAI.DistributedResistanceEmoteMgrAI(
            self.air)
        self.resistanceEmoteMgr.generateWithRequired(EVENT_ZONE)
        # let the holiday system know we started
        bboard.post(ResistanceEventMgrAI.PostName)

    def stop(self):
        # let the holiday system know we stopped
        bboard.remove(ResistanceEventMgrAI.PostName)
        # remove the object
        self.resistanceEmoteMgr.requestDelete()
