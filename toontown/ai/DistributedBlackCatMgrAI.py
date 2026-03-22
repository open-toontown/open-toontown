from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObjectAI

class DistributedBlackCatMgrAI(DistributedObjectAI.DistributedObjectAI):
    """This object sits in the tutorial zone with Flippy and listens for
    the avatar to say 'Toontastic!' when prompted to say something. At that
    point, if the avatar is a cat, it gives them the 'black cat' DNA."""
    notify = DirectNotifyGlobal.directNotify.newCategory(
        'DistributedBlackCatMgrAI')
    
    def __init__(self, air, avId):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        self.avId = avId

    def getAvId(self):
        return self.avId

    def doBlackCatTransformation(self):
        avId = self.avId
        if self.air.getAvatarIdFromSender() != avId:
            self.air.writeServerEvent(
                'suspicious', avId,
                '%s: expected msg from %s, got msg from %s' % (
                self.__class__.__name__, avId, self.air.getAvatarIdFromSender()))
            return

        av = self.air.doId2do.get(self.avId)
        if not av:
            DistributedBlackCatMgrAI.notify.warning(
                'tried to turn av %s into a black cat, but they left' % avId)
        else:
            self.air.writeServerEvent('blackCatMade', avId, 'turning av %s into a black cat' % avId)
            DistributedBlackCatMgrAI.notify.warning(
                'turning av %s into a black cat' % avId)
            av.makeBlackCat()
