from direct.distributed.DistributedObjectGlobal import DistributedObjectGlobal
from direct.directnotify.DirectNotifyGlobal import directNotify
from otp.otpbase import OTPGlobals
from otp.friends.PlayerFriendsManager import PlayerFriendsManager

class TTPlayerFriendsManager(PlayerFriendsManager):

    def __init__(self, cr):
        PlayerFriendsManager.__init__(self, cr)

    def sendRequestInvite(self, playerId):
        self.sendUpdate('requestInvite', [0, playerId, False])
