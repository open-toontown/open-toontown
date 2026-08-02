from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI

class MagicWordManagerAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory("MagicWordManagerAI")

    def setMagicWord(self, todo0, todo1, todo2, todo3):
        pass

    def setMagicWordResponse(self, todo0):
        pass

    def setWho(self, todo0):
        pass

