from direct.distributed.DistributedObjectGlobal import DistributedObjectGlobal
from direct.directnotify.DirectNotifyGlobal import directNotify
from otp.otpbase import OTPGlobals
from otp.uberdog import SpeedchatRelayGlobals

class SpeedchatRelay(DistributedObjectGlobal):

    def __init__(self, cr):
        DistributedObjectGlobal.__init__(self, cr)

    def sendSpeedchat(self, receiverId, messageIndex):
        self.sendSpeedchatToRelay(receiverId, SpeedchatRelayGlobals.NORMAL, [messageIndex])

    def sendSpeedchatCustom(self, receiverId, messageIndex):
        self.sendSpeedchatToRelay(receiverId, SpeedchatRelayGlobals.CUSTOM, [messageIndex])

    def sendSpeedchatEmote(self, receiverId, messageIndex):
        self.sendSpeedchatToRelay(receiverId, SpeedchatRelayGlobals.EMOTE, [messageIndex])

    def sendSpeedchatToRelay(self, receiverId, speedchatType, parameters):
        self.sendUpdate('forwardSpeedchat', [receiverId,
         speedchatType,
         parameters,
         base.cr.accountDetailRecord.playerAccountId,
         base.cr.accountDetailRecord.playerName + ' RHFM',
         0])
