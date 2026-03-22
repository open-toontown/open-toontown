from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObjectAI
from toontown.ai import DistributedPhaseEventMgrAI

class DistributedHydrantZeroMgrAI(DistributedPhaseEventMgrAI.DistributedPhaseEventMgrAI):
    """Distributed Object to tell the client what phase we're in."""
    
    notify = DirectNotifyGlobal.directNotify.newCategory(
        'DistributedHydrantZeroMgrAI')
    
    def __init__(self, air, startAndEndTimes, phaseDates):
        """Construct ourself and calc required fields."""
        DistributedPhaseEventMgrAI.DistributedPhaseEventMgrAI.__init__(self, air, startAndEndTimes,phaseDates)
