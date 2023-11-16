from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.DistributedObjectGlobal import DistributedObjectGlobal

from otp.friends.PlayerFriendsManager import PlayerFriendsManager
from otp.otpbase import OTPGlobals


class TTPlayerFriendsManager(PlayerFriendsManager):

    def __init__(self, cr):
        PlayerFriendsManager.__init__(self, cr)

    def sendRequestInvite(self, playerId):
        self.sendUpdate('requestInvite', [0, playerId, False])
