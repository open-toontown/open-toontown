from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI

class ToontownDistrictAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToontownDistrictAI')
