from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObjectAI
from toontown.ai import DistributedPhaseEventMgrAI

class DistributedSillyMeterMgrAI(DistributedPhaseEventMgrAI.DistributedPhaseEventMgrAI):
    """Distributed Object to tell the client what phase we're in."""

    notify = DirectNotifyGlobal.directNotify.newCategory(
        'DistributedSillyMeterMgrAI')

    def __init__(self, air, startAndEndTimes, phaseDates):
        """Construct ourself and calc required fields."""
        DistributedPhaseEventMgrAI.DistributedPhaseEventMgrAI.__init__(self, air, startAndEndTimes,phaseDates)
        air.SillyMeterMgr = self

    def setCurPhase(self, newPhase):
        DistributedPhaseEventMgrAI.DistributedPhaseEventMgrAI.setCurPhase(self,newPhase)
        messenger.send('SillyMeterPhase', [newPhase])

    def calcCurPhase(self):
        DistributedPhaseEventMgrAI.DistributedPhaseEventMgrAI.calcCurPhase(self)
        messenger.send('SillyMeterPhase', [self.curPhase])

    def end(self):
        messenger.send('SillyMeterPhase', [len(self.phaseDates)+1])
