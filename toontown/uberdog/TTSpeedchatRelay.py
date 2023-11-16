from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.DistributedObjectGlobal import DistributedObjectGlobal

from otp.otpbase import OTPGlobals
from otp.uberdog import SpeedchatRelayGlobals
from otp.uberdog.SpeedchatRelay import SpeedchatRelay


class TTSpeedchatRelay(SpeedchatRelay):

    def __init__(self, cr):
        SpeedchatRelay.__init__(self, cr)

    def sendSpeedchatToonTask(self, receiverId, taskId, toNpcId, toonProgress, msgIndex):
        self.sendSpeedchatToRelay(receiverId, SpeedchatRelayGlobals.TOONTOWN_QUEST, [taskId,
         toNpcId,
         toonProgress,
         msgIndex])
