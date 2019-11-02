from otp.ai.AIBaseGlobal import *
from direct.distributed.ClockDelta import *
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM
import DistributedAnimatedPropAI
from direct.task.Task import Task
from direct.fsm import State

class DistributedKnockKnockDoorAI(DistributedAnimatedPropAI.DistributedAnimatedPropAI):

    def __init__(self, air, propId):
        DistributedAnimatedPropAI.DistributedAnimatedPropAI.__init__(self, air, propId)
        self.fsm.setName('DistributedKnockKnockDoor')
        self.propId = propId
        self.doLaterTask = None
        return

    def enterOff(self):
        DistributedAnimatedPropAI.DistributedAnimatedPropAI.enterOff(self)

    def exitOff(self):
        DistributedAnimatedPropAI.DistributedAnimatedPropAI.exitOff(self)

    def attractTask(self, task):
        self.fsm.request('attract')
        return Task.done

    def enterAttract(self):
        DistributedAnimatedPropAI.DistributedAnimatedPropAI.enterAttract(self)

    def exitAttract(self):
        DistributedAnimatedPropAI.DistributedAnimatedPropAI.exitAttract(self)

    def enterPlaying(self):
        DistributedAnimatedPropAI.DistributedAnimatedPropAI.enterPlaying(self)
        self.doLaterTask = taskMgr.doMethodLater(9, self.attractTask, self.uniqueName('knockKnock-timer'))

    def exitPlaying(self):
        DistributedAnimatedPropAI.DistributedAnimatedPropAI.exitPlaying(self)
        taskMgr.remove(self.doLaterTask)
        self.doLaterTask = None
        return
