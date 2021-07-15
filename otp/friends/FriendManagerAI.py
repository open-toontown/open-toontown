from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectGlobalAI import DistributedObjectGlobalAI
from direct.distributed.PyDatagram import *

from otp.otpbase import OTPGlobals


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
            #FriendManagerAI.notify.warning('Message for unknown context ' + repr(context))
            return

        self.cancelInvite(invite)

    ### Messages sent from invitee client to AI

    def inviteeFriendConsidering(self, response, context):
        """inviteeFriendConsidering(self, int response, int context)

        Sent by the invitee to the AI to indicate whether the invitee
        is able to consider the request right now.

        The responses are:
          0 - no
          1 - yes
          4 - the invitee is ignoring you.
        """
        self.notify.debug("AI: inviteeFriendConsidering(%d, %d)" % (response, context))
        avId = self.air.getAvatarIdFromSender()

        try:
            invite = FriendManagerAI.invites[context]
        except:
            self.air.writeServerEvent('suspicious', avId, 'FriendManagerAI.inviteeFriendConsidering unknown context')
            FriendManagerAI.notify.warning('Message for unknown context ' + repr(context))
            return

        if response == 1:
            self.inviteeAvailable(invite)
        else:
            self.inviteeUnavailable(invite, response)

    def inviteeFriendResponse(self, yesNoMaybe, context):
        """inviteeFriendResponse(self, int yesNoMaybe, int context)

        Sent by the invitee to the AI, following an affirmative
        response in inviteeFriendConsidering, to indicate whether or
        not the user decided to accept the friendship.
        """

        self.notify.debug("AI: inviteeFriendResponse(%d, %d)" % (yesNoMaybe, context))
        avId = self.air.getAvatarIdFromSender()

        try:
            invite = FriendManagerAI.invites[context]
        except:
            self.air.writeServerEvent('suspicious', avId, 'FriendManagerAI.inviteeFriendResponse unknown context')
            FriendManagerAI.notify.warning('Message for unknown context ' + repr(context))
            return

        if yesNoMaybe == 1:
            self.makeFriends(invite)
        else:
            self.noFriends(invite, yesNoMaybe)

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

    ### Messages involving secrets

    def requestSecret(self):
        """requestSecret(self)

        Sent by the client to the AI to request a new "secret" for the
        user.
        """
        # TODO
        self.notify.info('TODO: requestSecret')

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

    def down_friendResponse(self, recipient, yesNoMaybe, context):
        """friendResponse(self, DistributedOBject recipient,
                          int yesNoMaybe, int context)

        Sent by the AI to the inviter client, following an affirmitive
        response in friendConsidering, to indicate whether or not the
        user decided to accept the friendship.
        """

        self.sendUpdateToAvatarId(recipient, "friendResponse", [yesNoMaybe, context])
        self.notify.debug("AI: friendResponse(%d, %d)" % (yesNoMaybe, context))

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

    def inviteeAvailable(self, invite):
        # The invitee is considering our friendship request.
        self.down_friendConsidering(invite.inviterId, 1, invite.context)

    def noFriends(self, invite, yesNoMaybe):
        # The invitee declined to make friends.
        #
        # 0 - no
        # 2 - unable to answer; e.g. entered a minigame or something.
        # 3 - the invitee has too many friends already.

        if yesNoMaybe == 0 or yesNoMaybe == 3:
            # The user explictly said no or has too many friends.
            # Disallow this guy from asking again for the next ten
            # minutes or so.

            if invite.inviteeId not in self.declineFriends1:
                self.declineFriends1[invite.inviteeId] = {}
            self.declineFriends1[invite.inviteeId][invite.inviterId] = yesNoMaybe

        self.down_friendResponse(invite.inviterId, yesNoMaybe, invite.context)
        self.clearInvite(invite)

    def makeFriends(self, invite):
        # The invitee agreed to make friends.
        self.__handleMakeFriends(invite.inviteeId, invite.inviterId, 0,
                                 invite.context)
        self.down_friendResponse(invite.inviterId, 1, invite.context)
        # The reply will clear the context out when it comes in.

    def __handleMakeFriends(self, avatarAId, avatarBId, flags, context):
        # And now the magic begins.
        avatarA = self.air.doId2do.get(avatarAId)  # invitee
        avatarB = self.air.doId2do.get(avatarBId)  # inviter
        if avatarA and avatarB:
            datagram = PyDatagram()
            datagram.addServerHeader(self.GetPuppetConnectionChannel(avatarA.getDoId()), self.air.ourChannel,
                                                                     CLIENTAGENT_DECLARE_OBJECT)
            datagram.addUint32(avatarB.getDoId())
            datagram.addUint16(self.air.dclassesByName['DistributedToonAI'].getNumber())
            self.air.send(datagram)

            datagram = PyDatagram()
            datagram.addServerHeader(self.GetPuppetConnectionChannel(avatarB.getDoId()), self.air.ourChannel,
                                                                     CLIENTAGENT_DECLARE_OBJECT)
            datagram.addUint32(avatarA.getDoId())
            datagram.addUint16(self.air.dclassesByName['DistributedToonAI'].getNumber())
            self.air.send(datagram)

        if avatarA:
            avatarAFriendsList = avatarA.getFriendsList()
            if len(avatarAFriendsList) >= OTPGlobals.MaxFriends:
                self.makeFriendsReply(0, context)
                return

            avatarANewFriend = (avatarBId, flags)
            if avatarANewFriend in avatarAFriendsList:
                self.makeFriendsReply(0, context)
                return

            avatarAFriendsList.append(avatarANewFriend)
            avatarA.d_setFriendsList(avatarAFriendsList)
        else:
            def handleAvatarA(dclass, fields):
                if dclass != self.air.dclassesByName['DistributedToonAI']:
                    return

                avatarAFriendsList = fields['setFriendsList'][0]
                if len(avatarAFriendsList) >= OTPGlobals.MaxFriends:
                    self.makeFriendsReply(0, context)
                    return

                avatarANewFriend = (avatarBId, flags)
                if avatarANewFriend in avatarAFriendsList:
                    self.makeFriendsReply(0, context)
                    return

                avatarAFriendsList.append(avatarANewFriend)
                self.air.dbInterface.updateObject(self.air.dbId, avatarAId, self.air.dclassesByName['DistributedToonAI'],
                                                  {'setFriendsList': [avatarAFriendsList]})

            self.air.dbInterface.queryObject(self.air.dbId, avatarAId, handleAvatarA)

        if avatarB:
            avatarBFriendsList = avatarB.getFriendsList()
            if len(avatarBFriendsList) >= OTPGlobals.MaxFriends:
                self.makeFriendsReply(0, context)
                return

            avatarBNewFriend = (avatarAId, flags)
            if avatarBNewFriend in avatarBFriendsList:
                self.makeFriendsReply(0, context)
                return

            avatarBFriendsList.append(avatarBNewFriend)
            avatarB.d_setFriendsList(avatarBFriendsList)
        else:
            def handleAvatarB(dclass, fields):
                if dclass != self.air.dclassesByName['DistributedToonAI']:
                    return

                avatarBFriendsList = fields['setFriendsList'][0]
                if len(avatarBFriendsList) >= OTPGlobals.MaxFriends:
                    self.makeFriendsReply(0, context)
                    return

                avatarBNewFriend = (avatarAId, flags)
                if avatarBNewFriend in avatarBFriendsList:
                    self.makeFriendsReply(0, context)
                    return

                avatarBFriendsList.append(avatarBNewFriend)
                self.air.dbInterface.updateObject(self.air.dbId, avatarBId, self.air.dclassesByName['DistributedToonAI'],
                                                  {'setFriendsList': [avatarBFriendsList]})

            self.air.dbInterface.queryObject(self.air.dbId, avatarBId, handleAvatarB)

        self.makeFriendsReply(1, context)

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

    def makeFriendsReply(self, result, context):
        try:
            invite = FriendManagerAI.invites[context]
        except:
            FriendManagerAI.notify.warning('Message for unknown context ' + repr(context))
            return

        if result:
            # By now, the server has OK'ed the friends transaction.
            # Update our internal bookkeeping so we remember who's
            # friends with whom.  This is mainly useful for correct
            # accounting of the make-a-friend quest.
            invitee = self.air.doId2do.get(invite.inviteeId)
            inviter = self.air.doId2do.get(invite.inviterId)
            if invitee != None:
                invitee.extendFriendsList(invite.inviterId, invite.sendSpecialResponse)
                self.air.questManager.toonMadeFriend(invitee, inviter)

            #inviter = self.air.doId2do.get(invite.inviterId)
            if inviter != None:
                inviter.extendFriendsList(invite.inviteeId, invite.sendSpecialResponse)
                self.air.questManager.toonMadeFriend(inviter, invitee)

        if invite.sendSpecialResponse:
            # If this flag is set, the "invite" was generated via the
            # codeword system, instead of through the normal path.  In
            # this case, we need to send the acknowledgement back to
            # the client.

            if result:
                # Success!  Send a result code of 1.
                result = 1
            else:
                # Failure, some friends list problem.  Result code of 2.
                result = 2

            self.down_submitSecretResponse(invite.inviterId, result,
                                           invite.inviteeId)

            # Also send a notification to the other avatar, if he's on.
            avatar = DistributedAvatarAI.DistributedAvatarAI(self.air)
            avatar.doId = invite.inviteeId
            avatar.d_friendsNotify(invite.inviterId, 2)

        self.clearInvite(invite)
