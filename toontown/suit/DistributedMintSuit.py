from direct.directnotify import DirectNotifyGlobal

from toontown.suit import DistributedFactorySuit


class DistributedMintSuit(DistributedFactorySuit.DistributedFactorySuit):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedMintSuit')
