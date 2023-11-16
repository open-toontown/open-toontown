from direct.directnotify import DirectNotifyGlobal

from toontown.suit import DistributedFactorySuitAI


class DistributedStageSuitAI(DistributedFactorySuitAI.DistributedFactorySuitAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedStageSuitAI')

    def isForeman(self):
        return 0

    def isSupervisor(self):
        return self.boss

    def isVirtual(self):
        return self.virtual
