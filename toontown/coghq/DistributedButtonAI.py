from direct.directnotify import DirectNotifyGlobal
from direct.task import Task
from . import DistributedSwitchBase, DistributedSwitchAI

class DistributedButtonAI(DistributedSwitchAI.DistributedSwitchAI):
    setColor = DistributedSwitchBase.stubFunction
    setModel = DistributedSwitchBase.stubFunction
