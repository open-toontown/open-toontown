from otp.ai.AIBase import *
from direct.directnotify import DirectNotifyGlobal
from otp.level import DistributedEntityAI
from . import SinkingPlatformGlobals

class DistributedSinkingPlatformAI(DistributedEntityAI.DistributedEntityAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedSinkingPlatformAI')

    def __init__(self, levelDoId, entId):
        DistributedEntityAI.DistributedEntityAI.__init__(self, levelDoId, entId)
        self.numStanding = 0

    def setOnOff(self, on, timestamp):
        avId = self.air.getAvatarIdFromSender()
        self.notify.debug('setOnOff %s' % on)
        if on:
            self.numStanding += 1
        else:
            self.numStanding -= 1
        self.notify.debug('numStanding = %s' % self.numStanding)
        if self.numStanding > 0:
            self.sendUpdate('setSinkMode', [avId, SinkingPlatformGlobals.SINKING, timestamp])
        else:
            self.sendUpdate('setSinkMode', [avId, SinkingPlatformGlobals.RISING, timestamp])
