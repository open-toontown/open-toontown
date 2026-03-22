from direct.directnotify import DirectNotifyGlobal
from toontown.ai import DistributedPhaseEventMgr


class DistributedMailboxZeroMgr(DistributedPhaseEventMgr.DistributedPhaseEventMgr):
    """Class to manage the mailbox zero manager"""
    neverDisable = 1
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedMailboxZeroMgr')

    # tempted to change this to have mailbox, hydrant, and trashcan as fields
    # but for holiday and magic word convenience, we'll use 3 separate classes

    def __init__(self, cr):
        DistributedPhaseEventMgr.DistributedPhaseEventMgr.__init__(self, cr)
        cr.mailboxZeroMgr = self

    def announceGenerate(self):
        """Tell other objects we're here."""
        DistributedPhaseEventMgr.DistributedPhaseEventMgr.announceGenerate(self)
        messenger.send('mailboxZeroIsRunning', [self.isRunning])

    def delete(self):
        self.notify.debug("deleting mailboxzeromgr")
        messenger.send('mailboxZeroIsRunning', [False])
        DistributedPhaseEventMgr.DistributedPhaseEventMgr.delete(self)
        if hasattr(self.cr, "mailboxZeroMgr"):
            del self.cr.mailboxZeroMgr

    def setCurPhase(self, newPhase):
        """We've gotten a new phase lets, tell the mailboxs."""
        assert self.notify.debugStateCall(self)
        DistributedPhaseEventMgr.DistributedPhaseEventMgr.setCurPhase(self, newPhase)
        messenger.send('mailboxZeroPhase', [newPhase])

    def setIsRunning(self, isRunning):
        """We've gotten a new phase lets, tell the mailboxs."""
        assert self.notify.debugStateCall(self)
        DistributedPhaseEventMgr.DistributedPhaseEventMgr.setIsRunning(self, isRunning)
        messenger.send('mailboxZeroIsRunning', [isRunning])
