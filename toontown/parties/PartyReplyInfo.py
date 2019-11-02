

class SingleReply:

    def __init__(self, inviteeId, status):
        self.inviteeId = inviteeId
        self.status = status


class PartyReplyInfoBase:

    def __init__(self, partyId, partyReplies):
        self.partyId = partyId
        self.replies = []
        for oneReply in partyReplies:
            self.replies.append(SingleReply(*oneReply))

    def __str__(self):
        string = 'partyId=%d ' % self.partyId
        for reply in self.replies:
            string += '(%d:%d) ' % (reply.inviteeId, reply.status)

        return string
