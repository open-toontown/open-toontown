from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectGlobalAI import DistributedObjectGlobalAI


class ToontownFriendsManagerAI(DistributedObjectGlobalAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToontownFriendsManagerAI')

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
