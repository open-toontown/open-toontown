from direct.directnotify import DirectNotifyGlobal

from toontown.suit import DistributedFactorySuitAI


class DistributedMintSuitAI(DistributedFactorySuitAI.DistributedFactorySuitAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedMintSuitAI')

    def isForeman(self):
        return 0

    def isSupervisor(self):
        return self.boss

    def isVirtual(self):
        return 0
