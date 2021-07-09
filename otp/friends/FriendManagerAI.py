from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectGlobalAI import DistributedObjectGlobalAI


class FriendManagerAI(DistributedObjectGlobalAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('FriendManagerAI')

    # These structures record the invitations currently being handled.
    nextContext = 0
    invites = {}
    inviters = {}
    invitees = {}

    # This is the length of time that should elapse before we start to
    # forget who has declined friendships from whom.
    DeclineFriendshipTimeout = 600.0

    # This subclass is used to record currently outstanding
    # in-the-game invitation requests.
    class Invite:
        def __init__(self, context, inviterId, inviteeId):
            self.context = context
            self.inviterId = inviterId
            self.inviteeId = inviteeId
            self.inviter = None
            self.invitee = None
            self.inviteeKnows = 0
            self.sendSpecialResponse = 0

    def __init__(self, air):
        DistributedObjectGlobalAI.__init__(self, air)

        # We maintain two maps of toons who have declined
        # friendships.  We add entries to map1, and every ten
        # minutes, we roll map1 into map2.  This provides a
        # timeout of ten to twenty minutes for a particular
        # rejection, and also prevents the maps from growing very
        # large in memory.
        self.declineFriends1 = {}
        self.declineFriends2 = {}
        self.lastRollTime = 0

    ### Messages sent from inviter client to AI

    def friendQuery(self, inviteeId):
        """friendQuery(self, int inviterId, int inviteeId)

        Sent by the inviter to the AI to initiate a friendship
        request.
        """
        inviterId = self.air.getAvatarIdFromSender()
        invitee = self.air.doId2do.get(inviteeId)

        # see if the inviteeId is valid
        if not invitee:
            self.air.writeServerEvent('suspicious', inviteeId, 'FriendManagerAI.friendQuery not on list')
            return

        self.notify.debug("AI: friendQuery(%d, %d)" % (inviterId, inviteeId))
        self.newInvite(inviterId, inviteeId)

    def cancelFriendQuery(self, context):
        """cancelFriendQuery(self, int context)

        Sent by the inviter to the AI to cancel a pending friendship
        request.
        """

        avId = self.air.getAvatarIdFromSender()
        self.notify.debug("AI: cancelFriendQuery(%d)" % (context))

        try:
            invite = FriendManagerAI.invites[context]
        except:
            # The client might legitimately try to cancel a context
            # that has already been cancelled.
            #self.air.writeServerEvent('suspicious', avId, 'FriendManagerAI.cancelFriendQuery unknown context')
            #FriendManagerAI.notify.warning('Message for unknown context ' + `context`)
            return

        self.cancelInvite(invite)

    ### Messages sent from AI to invitee client

    def down_inviteeFriendQuery(self, recipient, inviterId, inviterName,
                                inviterDna, context):
        """inviteeFriendQuery(self, DistributedObject recipient,
                              int inviterId, string inviterName,
                              AvatarDNA inviterDna, int context)

        Sent by the AI to the invitee client to initiate a friendship
        request from the indiciated inviter.  The invitee client
        should respond immediately with inviteeFriendConsidering, to
        indicate whether the invitee is able to consider the
        invitation right now.
        """

        self.sendUpdateToAvatarId(recipient, "inviteeFriendQuery",
                               [inviterId, inviterName,
                                inviterDna.makeNetString(), context])
        self.notify.debug("AI: inviteeFriendQuery(%d, %s, dna, %d)" % (inviterId, inviterName, context))

    def down_inviteeCancelFriendQuery(self, recipient, context):
        """inviteeCancelFriendQuery(self, DistributedObject recipient,
                                    int context)

        Sent by the AI to the invitee client to initiate that the
        inviter has rescinded his/her previous invitation by clicking
        the cancel button.
        """

        self.sendUpdateToAvatarId(recipient, "inviteeCancelFriendQuery", [context])
        self.notify.debug("AI: inviteeCancelFriendQuery(%d)" % (context))

    ### Messages sent from AI to inviter client

    def down_friendConsidering(self, recipient, yesNoAlready, context):
        """friendConsidering(self, DistributedObject recipient,
                             int yesNoAlready, int context)

        Sent by the AI to the inviter client to indicate whether the
        invitee is able to consider the request right now.

        The responses are:
        # 0 - the invitee is busy
        # 2 - the invitee is already your friend
        # 3 - the invitee is yourself
        # 4 - the invitee is ignoring you.
        # 6 - the invitee not accepting friends
        """

        self.sendUpdateToAvatarId(recipient, "friendConsidering", [yesNoAlready, context])
        self.notify.debug("AI: friendConsidering(%d, %d)" % (yesNoAlready, context))

    ### Support methods

    def newInvite(self, inviterId, inviteeId):
        context = FriendManagerAI.nextContext
        FriendManagerAI.nextContext += 1

        invite = FriendManagerAI.Invite(context, inviterId, inviteeId)
        FriendManagerAI.invites[context] = invite

        # If the invitee has previously (recently) declined a
        # friendship from this inviter, don't ask again.
        previous = self.__previousResponse(inviteeId, inviterId)
        if previous != None:
            self.inviteeUnavailable(invite, previous + 10)
            return

        # If the invitee is presently being invited by someone else,
        # we don't even have to bother him.
        if inviteeId in FriendManagerAI.invitees:
            self.inviteeUnavailable(invite, 0)
            return

        if invite.inviterId == invite.inviteeId:
            # You can't be friends with yourself.
            self.inviteeUnavailable(invite, 3)
            return

        # If the inviter is already involved in some other context,
        # that one is now void.
        if inviterId in FriendManagerAI.inviters:
            self.cancelInvite(FriendManagerAI.inviters[inviterId])

        FriendManagerAI.inviters[inviterId] = invite
        FriendManagerAI.invitees[inviteeId] = invite

        #self.air.queryObject(inviteeId, self.gotInvitee, invite)
        #self.air.queryObject(inviterId, self.gotInviter, invite)
        invite.inviter = self.air.doId2do.get(inviterId)
        invite.invitee = self.air.doId2do.get(inviteeId)
        if invite.inviter and invite.invitee:
            self.beginInvite(invite)

    def beginInvite(self, invite):
        # Ask the invitee if he is available to consider being
        # someone's friend--that is, that he's not busy playing a
        # minigame or something.

        invite.inviteeKnows = 1
        self.down_inviteeFriendQuery(invite.inviteeId, invite.inviterId,
                                     invite.inviter.getName(),
                                     invite.inviter.dna, invite.context)

    def inviteeUnavailable(self, invite, code):
        # Cannot make the request for one of these reasons:
        #
        # 0 - the invitee is busy
        # 2 - the invitee is already your friend
        # 3 - the invitee is yourself
        # 4 - the invitee is ignoring you.
        # 6 - the invitee not accepting friends
        self.down_friendConsidering(invite.inviterId, code, invite.context)

        # That ends the invitation.
        self.clearInvite(invite)

    def __previousResponse(self, inviteeId, inviterId):
        # Return the previous rejection code if this invitee has
        # previously (recently) declined a friendship from this
        # inviter, or None if there was no previous rejection.

        now = globalClock.getRealTime()
        if now - self.lastRollTime >= self.DeclineFriendshipTimeout:
            self.declineFriends2 = self.declineFriends1
            self.declineFriends1 = {}

        # Now, is the invitee/inviter combination present in either
        # map?
        previous = None
        if inviteeId in self.declineFriends1:
            previous = self.declineFriends1[inviteeId].get(inviterId)
            if previous != None:
                return previous

        if inviteeId in self.declineFriends2:
            previous = self.declineFriends2[inviteeId].get(inviterId)
            if previous != None:
                return previous

        # Nope, go ahead and ask.
        return None

    def clearInvite(self, invite):
        try:
            del FriendManagerAI.invites[invite.context]
        except:
            pass

        try:
            del FriendManagerAI.inviters[invite.inviterId]
        except:
            pass

        try:
            del FriendManagerAI.invitees[invite.inviteeId]
        except:
            pass

    def cancelInvite(self, invite):
        if invite.inviteeKnows:
            self.down_inviteeCancelFriendQuery(invite.inviteeId, invite.context)

        invite.inviteeKnows = 0
