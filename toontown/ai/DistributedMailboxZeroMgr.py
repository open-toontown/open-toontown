from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObject
from toontown.ai import DistributedPhaseEventMgr

class DistributedMailboxZeroMgr(DistributedPhaseEventMgr.DistributedPhaseEventMgr):
    neverDisable = 1
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedMailboxZeroMgr')

    def __init__(self, cr):
        DistributedPhaseEventMgr.DistributedPhaseEventMgr.__init__(self, cr)
        cr.mailboxZeroMgr = self

    def announceGenerate(self):
        DistributedPhaseEventMgr.DistributedPhaseEventMgr.announceGenerate(self)
        messenger.send('mailboxZeroIsRunning', [self.isRunning])

    def delete(self):
        self.notify.debug('deleting mailboxzeromgr')
        messenger.send('mailboxZeroIsRunning', [False])
        DistributedPhaseEventMgr.DistributedPhaseEventMgr.delete(self)
        if hasattr(self.cr, 'mailboxZeroMgr'):
            del self.cr.mailboxZeroMgr

    def setCurPhase(self, newPhase):
        DistributedPhaseEventMgr.DistributedPhaseEventMgr.setCurPhase(self, newPhase)
        messenger.send('mailboxZeroPhase', [newPhase])

    def setIsRunning(self, isRunning):
        DistributedPhaseEventMgr.DistributedPhaseEventMgr.setIsRunning(self, isRunning)
        messenger.send('mailboxZeroIsRunning', [isRunning])
