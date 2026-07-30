from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals
from toontown.parties.PartyGlobals import InviteStatus
from toontown.toonbase import TTLocalizer

class InviteInfoBase:

    def __init__(self, inviteKey, partyId, status):
        self.inviteKey = inviteKey
        self.partyId = partyId
        self.status = status

    def __str__(self):
        string = 'inviteKey=%d ' % self.inviteKey
        string += 'partyId=%d ' % self.partyId
        string += 'status=%s' % InviteStatus.getString(self.status)
        return string

    def __repr__(self):
        return self.__str__()


class InviteInfo(InviteInfoBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('InviteInfo')

    def __init__(self, inviteKey, partyId, status):
        InviteInfoBase.__init__(self, inviteKey, partyId, status)

    def acceptItem(self, mailbox, acceptingIndex, callback):
        InviteInfo.notify.debug('acceptItem')
        mailbox.acceptInvite(self, acceptingIndex, callback)

    def discardItem(self, mailbox, acceptingIndex, callback):
        InviteInfo.notify.debug('discardItem')
        mailbox.rejectInvite(self, acceptingIndex, callback)

    def getAcceptItemErrorText(self, retcode):
        InviteInfo.notify.debug('getAcceptItemErrorText')
        if retcode == ToontownGlobals.P_InvalidIndex:
            return TTLocalizer.InviteAcceptInvalidError
        elif retcode == ToontownGlobals.P_ItemAvailable:
            return TTLocalizer.InviteAcceptAllOk
        else:
            return TTLocalizer.CatalogAcceptGeneralError % retcode

    def getDiscardItemErrorText(self, retcode):
        InviteInfo.notify.debug('getDiscardItemErrorText')
        if retcode == ToontownGlobals.P_InvalidIndex:
            return TTLocalizer.InviteAcceptInvalidError
        elif retcode == ToontownGlobals.P_ItemAvailable:
            return TTLocalizer.InviteRejectAllOk
        else:
            return TTLocalizer.CatalogAcceptGeneralError % retcode

    def output(self, store = -1):
        return 'InviteInfo %s' % str(self)
