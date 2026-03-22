from direct.directnotify import DirectNotifyGlobal
from toontown.ai import DistributedPhaseEventMgr


class DistributedHydrantZeroMgr(DistributedPhaseEventMgr.DistributedPhaseEventMgr):
    """Class to manage the hydrant zero manager"""
    neverDisable = 1
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedHydrantZeroMgr')

    def __init__(self, cr):
        DistributedPhaseEventMgr.DistributedPhaseEventMgr.__init__(self, cr)
        cr.hydrantZeroMgr = self

    def announceGenerate(self):
        """Tell other objects we're here."""
        DistributedPhaseEventMgr.DistributedPhaseEventMgr.announceGenerate(self)
        messenger.send('hydrantZeroIsRunning', [self.isRunning])

    def delete(self):
        self.notify.debug("deleting hydrantzeromgr")
        messenger.send('hydrantZeroIsRunning', [False])
        DistributedPhaseEventMgr.DistributedPhaseEventMgr.delete(self)
        if hasattr(self.cr, "hydrantZeroMgr"):
            del self.cr.hydrantZeroMgr

    def setCurPhase(self, newPhase):
        """We've gotten a new phase lets, tell the hydrants."""
        assert self.notify.debugStateCall(self)
        DistributedPhaseEventMgr.DistributedPhaseEventMgr.setCurPhase(self, newPhase)
        messenger.send('hydrantZeroPhase', [newPhase])

    def setIsRunning(self, isRunning):
        """We've gotten a new phase lets, tell the hydrants."""
        assert self.notify.debugStateCall(self)
        DistributedPhaseEventMgr.DistributedPhaseEventMgr.setIsRunning(self, isRunning)
        messenger.send('hydrantZeroIsRunning', [isRunning])
