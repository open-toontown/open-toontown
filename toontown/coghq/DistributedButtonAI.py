from direct.directnotify import DirectNotifyGlobal
from direct.task import Task
import DistributedSwitchBase, DistributedSwitchAI

class DistributedButtonAI(DistributedSwitchAI.DistributedSwitchAI):
    setColor = DistributedSwitchBase.stubFunction
    setModel = DistributedSwitchBase.stubFunction
