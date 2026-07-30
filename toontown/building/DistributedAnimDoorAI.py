from direct.directnotify import DirectNotifyGlobal
from toontown.building import DistributedDoorAI

class DistributedAnimDoorAI(DistributedDoorAI.DistributedDoorAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedAnimDoorAI')

    def __init__(self, air, blockNumber, doorType, doorIndex=0, lockValue=0, swing=3):
        DistributedDoorAI.DistributedDoorAI.__init__(self, air, blockNumber, doorType, doorIndex, lockValue, swing)
