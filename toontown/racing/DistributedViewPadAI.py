from direct.directnotify import DirectNotifyGlobal
from direct.distributed.ClockDelta import globalClockDelta

from toontown.racing.DistributedKartPadAI import DistributedKartPadAI
from toontown.racing.KartShopGlobals import KartGlobals


class DistributedViewPadAI(DistributedKartPadAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedViewPadAI')

    def __init__(self, air):
        DistributedKartPadAI.__init__(self, air)
        self.lastEntered = 0

    def announceGenerate(self):
        DistributedKartPadAI.announceGenerate(self)
        self.lastEntered = globalClockDelta.getRealNetworkTime()

    def setLastEntered(self, lastEntered):
        self.lastEntered = lastEntered

    def d_setLastEntered(self, lastEntered):
        self.sendUpdate('setLastEntered', [lastEntered])

    def b_setLastEntered(self, lastEntered):
        self.setLastEntered(lastEntered)
        self.d_setLastEntered(lastEntered)

    def getLastEntered(self):
        return self.lastEntered

    def addAvBlock(self, avId, startingBlock, paid):
        av = self.air.doId2do.get(avId)
        if not av:
            return

        if not av.hasKart():
            return KartGlobals.ERROR_CODE.eNoKart

        if not startingBlock.avId:
            self.b_setLastEntered(globalClockDelta.getRealNetworkTime())
            taskMgr.doMethodLater(KartGlobals.COUNTDOWN_TIME, self.kickAvatar,
                                  startingBlock.uniqueName('viewTimer'),
                                  extraArgs=[avId, startingBlock])
            return KartGlobals.ERROR_CODE.success
        else:
            return KartGlobals.ERROR_CODE.eOccupied

    def removeAvBlock(self, avId, startingBlock):
        if avId == startingBlock.avId:
            taskMgr.remove(startingBlock.uniqueName('viewTimer'))

    def kickAvatar(self, avId, startingBlock):
        if avId == startingBlock.avId and not startingBlock.currentMovie:
            startingBlock.normalExit()
