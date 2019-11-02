from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObject
from toontown.ai import DistributedPhaseEventMgr

class DistributedTrashcanZeroMgr(DistributedPhaseEventMgr.DistributedPhaseEventMgr):
    neverDisable = 1
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedTrashcanZeroMgr')

    def __init__(self, cr):
        DistributedPhaseEventMgr.DistributedPhaseEventMgr.__init__(self, cr)
        cr.trashcanZeroMgr = self

    def announceGenerate(self):
        DistributedPhaseEventMgr.DistributedPhaseEventMgr.announceGenerate(self)
        messenger.send('trashcanZeroIsRunning', [self.isRunning])

    def delete(self):
        self.notify.debug('deleting trashcanzeromgr')
        messenger.send('trashcanZeroIsRunning', [False])
        DistributedPhaseEventMgr.DistributedPhaseEventMgr.delete(self)
        if hasattr(self.cr, 'trashcanZeroMgr'):
            del self.cr.trashcanZeroMgr

    def setCurPhase(self, newPhase):
        DistributedPhaseEventMgr.DistributedPhaseEventMgr.setCurPhase(self, newPhase)
        messenger.send('trashcanZeroPhase', [newPhase])

    def setIsRunning(self, isRunning):
        DistributedPhaseEventMgr.DistributedPhaseEventMgr.setIsRunning(self, isRunning)
        messenger.send('trashcanZeroIsRunning', [isRunning])
