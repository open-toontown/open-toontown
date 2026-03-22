from direct.directnotify import DirectNotifyGlobal
from toontown.ai import DistributedPhaseEventMgr


class DistributedTrashcanZeroMgr(DistributedPhaseEventMgr.DistributedPhaseEventMgr):
    """Class to manage the trashcan zero manager"""
    neverDisable = 1
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedTrashcanZeroMgr')

    # tempted to change this to have mailbox, hydrant, and trashcan as fields
    # but for holiday and magic word convenience, we'll use 3 separate classes

    def __init__(self, cr):
        DistributedPhaseEventMgr.DistributedPhaseEventMgr.__init__(self, cr)
        cr.trashcanZeroMgr = self

    def announceGenerate(self):
        """Tell other objects we're here."""
        DistributedPhaseEventMgr.DistributedPhaseEventMgr.announceGenerate(self)
        messenger.send('trashcanZeroIsRunning', [self.isRunning])

    def delete(self):
        self.notify.debug("Deleting TrashcanZeroMgr")
        messenger.send('trashcanZeroIsRunning', [False])
        DistributedPhaseEventMgr.DistributedPhaseEventMgr.delete(self)
        if hasattr(self.cr, "trashcanZeroMgr"):
            del self.cr.trashcanZeroMgr

    def setCurPhase(self, newPhase):
        """We've gotten a new phase lets, tell the trashcans."""
        assert self.notify.debugStateCall(self)
        DistributedPhaseEventMgr.DistributedPhaseEventMgr.setCurPhase(self, newPhase)
        messenger.send('trashcanZeroPhase', [newPhase])

    def setIsRunning(self, isRunning):
        """We've gotten a new phase lets, tell the trashcans."""
        assert self.notify.debugStateCall(self)
        DistributedPhaseEventMgr.DistributedPhaseEventMgr.setIsRunning(self, isRunning)
        messenger.send('trashcanZeroIsRunning', [isRunning])

