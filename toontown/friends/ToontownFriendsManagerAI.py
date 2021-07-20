from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectGlobalAI import DistributedObjectGlobalAI
from direct.distributed.PyDatagram import *


class ToontownFriendsManagerAI(DistributedObjectGlobalAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToontownFriendsManagerAI')

    def sendFriendOnline(self, avId, friendId, commonChatFlags, whitelistChatFlags):
        datagram = PyDatagram()
        datagram.addUint32(friendId)  # doId
        datagram.addUint8(commonChatFlags)  # commonChatFlags
        datagram.addUint8(whitelistChatFlags)  # whitelistChatFlags
        self.sendUpdateToAvatarId(avId, 'friendOnline', [datagram.getMessage()])

    def makeFriends(self, avatarAId, avatarBId, flags, context):
        """
        Requests to make a friendship between avatarA and avatarB with
        the indicated flags (or upgrade an existing friendship with
        the indicated flags).  The context is any arbitrary 32-bit
        integer.  When the friendship is made, or the operation fails,
        the "makeFriendsReply" event is generated, with two
        parameters: an integer result code, and the supplied context.
        """
        self.sendUpdate('makeFriends', [avatarAId, avatarBId, flags, context])

    def makeFriendsResponse(self, avatarAId, avatarBId, result, context):
        if result == 1:
            self.sendFriendOnline(avatarAId, avatarBId, 0, 1)
            self.sendFriendOnline(avatarBId, avatarAId, 0, 1)

        messenger.send("makeFriendsReply", [result, context])
