from pandac.PandaModules import *
from direct.distributed.ClockDelta import *
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM
from . import DistributedEntity

class DistributedInteractiveEntity(DistributedEntity.DistributedEntity):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedInteractiveEntity')

    def __init__(self, cr):
        DistributedEntity.DistributedEntity.__init__(self, cr)
        self.fsm = ClassicFSM.ClassicFSM('DistributedInteractiveEntity', [State.State('off', self.enterOff, self.exitOff, ['playing', 'attract']), State.State('attract', self.enterAttract, self.exitAttract, ['playing']), State.State('playing', self.enterPlaying, self.exitPlaying, ['attract'])], 'off', 'off')
        self.fsm.enterInitialState()

    def generate(self):
        DistributedEntity.DistributedEntity.generate(self)

    def disable(self):
        self.fsm.request('off')
        DistributedEntity.DistributedEntity.disable(self)

    def delete(self):
        del self.fsm
        DistributedEntity.DistributedEntity.delete(self)

    def setAvatarInteract(self, avatarId):
        self.avatarId = avatarId

    def setOwnerDoId(self, ownerDoId):
        self.ownerDoId = ownerDoId

    def setState(self, state, timestamp):
        if self.isGenerated():
            self.fsm.request(state, [globalClockDelta.localElapsedTime(timestamp)])
        else:
            self.initialState = state
            self.initialStateTimestamp = timestamp

    def enterTrigger(self, args = None):
        messenger.send('DistributedInteractiveEntity_enterTrigger')
        self.sendUpdate('requestInteract')

    def exitTrigger(self, args = None):
        messenger.send('DistributedInteractiveEntity_exitTrigger')
        self.sendUpdate('requestExit')

    def rejectInteract(self):
        self.cr.playGame.getPlace().setState('walk')

    def avatarExit(self, avatarId):
        pass

    def enterOff(self):
        pass

    def exitOff(self):
        pass

    def enterAttract(self, ts):
        pass

    def exitAttract(self):
        pass

    def enterPlaying(self, ts):
        pass

    def exitPlaying(self):
        pass
