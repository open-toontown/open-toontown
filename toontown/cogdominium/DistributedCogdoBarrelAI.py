import random
from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObjectAI
from toontown.cogdominium import CogdoBarrelRoomConsts

class DistributedCogdoBarrelAI(DistributedObjectAI.DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedCogdoBarrelAI')

    def __init__(self, air, index, collectedCallback):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        self.grabbedBy = []
        self.index = index
        self.state = CogdoBarrelRoomConsts.StateHidden
        self.interactive = False
        self.collectedCallback = collectedCallback
        self.laff = random.randint(*CogdoBarrelRoomConsts.ToonUp)

    def generate(self):
        DistributedObjectAI.DistributedObjectAI.generate(self)

    def delete(self):
        DistributedObjectAI.DistributedObjectAI.delete(self)

    def getIndex(self):
        return self.index

    def getState(self):
        return self.state

    def d_setState(self, state):
        self.state = state
        self.sendUpdate('setState', [
            self.state])
        if self.state == CogdoBarrelRoomConsts.StateAvailable:
            self.grabbedBy = []

    def requestGrab(self):
        avId = self.air.getAvatarIdFromSender()
        av = self.air.doId2do.get(avId)
        if not av:
            self.notify.warning('requestGrab found no avatar with id %s' % avId)
            return

        if self.__canGrab(av):
            self.d_setGrab(avId)
        else:
            self.d_setReject()

    def __canGrab(self, av):
        return self.state == CogdoBarrelRoomConsts.StateAvailable and self.interactive and not av.isToonedUp() and av.doId not in self.grabbedBy

    def d_setGrab(self, avId):
        self.collectedCallback(self, avId)
        self.grabbedBy.append(avId)
        self.sendUpdate('setGrab', [
            avId])
        av = self.air.doId2do.get(avId)
        if av:
            av.toonUp(self.laff)

    def d_setReject(self):
        self.sendUpdate('setReject', [])

    def __str__(self):
        return 'Barrel %s' % self.index
