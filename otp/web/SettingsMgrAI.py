from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI

class SettingsMgrAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('SettingsMgrAI')
