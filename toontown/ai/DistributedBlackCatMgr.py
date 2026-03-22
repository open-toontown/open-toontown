from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObject
from direct.interval.IntervalGlobal import *
from toontown.effects import DustCloud


def getDustCloudIval(toon):
    dustCloud = DustCloud.DustCloud(fBillboard=0)
    dustCloud.setBillboardAxis(2)
    dustCloud.setZ(3)
    dustCloud.setScale(0.4)
    dustCloud.createTrack()
    toon.laffMeter.color = toon.style.getBlackColor()
    return Sequence(
        Wait(.5),
        Func(dustCloud.reparentTo, toon),
        dustCloud.track,
        Func(dustCloud.detachNode),
        Func(toon.laffMeter.adjustFace, toon.hp, toon.maxHp)
    )


class DistributedBlackCatMgr(DistributedObject.DistributedObject):
    """Black cat client implementation; turn a cat into a black cat if
    they say 'Toontastic!' to Flippy in the tutorial on Halloween."""
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedBlackCatMgr')

    ActivateEvent = 'DistributedBlackCatMgr-activate'

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)

    def setAvId(self, avId):
        self.avId = avId

    def announceGenerate(self):
        self.notify.debug("announceGenerate()")
        DistributedObject.DistributedObject.announceGenerate(self)
        self.acceptOnce(DistributedBlackCatMgr.ActivateEvent,
                        self.doBlackCatTransformation)
        self.dustCloudIval = None

    def delete(self):
        if self.dustCloudIval:
            self.dustCloudIval.finish()
        del self.dustCloudIval
        self.ignore(DistributedBlackCatMgr.ActivateEvent)
        DistributedObject.DistributedObject.delete(self)

    def doBlackCatTransformation(self):
        self.notify.debug("doBlackCatTransformation()")
        toon = base.cr.doId2do[self.avId]
        if not toon:
            self.notify.warning(f"Couldn't find Toon {self.avId}")
            return
        # are they a cat?
        if toon.style.getAnimal() != 'cat':
            self.notify.warning(f"Not a cat: {self.avId}")
            return
        self.sendUpdate('doBlackCatTransformation', [])

        # kick off a dust cloud.
        # If a player has a LOT of lag, the dust cloud will disappear before
        # the cat turns black.
        self.dustCloudIval = getDustCloudIval(toon)
        self.dustCloudIval.start()
