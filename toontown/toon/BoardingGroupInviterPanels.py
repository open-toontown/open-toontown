from panda3d.core import *
from toontown.toonbase.ToontownGlobals import *
from direct.showbase import DirectObject
from direct.directnotify import DirectNotifyGlobal
from toontown.toontowngui import TTDialog
from otp.otpbase import OTPLocalizer
from toontown.toontowngui import ToonHeadDialog
from direct.gui.DirectGui import DGG
from otp.otpbase import OTPGlobals
from toontown.toonbase import TTLocalizer

class BoardingGroupInviterPanels:
    notify = DirectNotifyGlobal.directNotify.newCategory('BoardingGroupInviterPanels')

    def __init__(self):
        self.__invitingPanel = None
        self.__invitationRejectedPanel = None
        return

    def cleanup(self):
        self.destroyInvitingPanel()
        self.destroyInvitationRejectedPanel()

    def createInvitingPanel(self, boardingParty, inviteeId, **kw):
        self.destroyInvitingPanel()
        self.destroyInvitationRejectedPanel()
        self.notify.debug('Creating Inviting Panel.')
        self.__invitingPanel = BoardingGroupInvitingPanel(boardingParty, inviteeId, **kw)

    def createInvitationRejectedPanel(self, boardingParty, inviteeId, **kw):
        self.destroyInvitingPanel()
        self.destroyInvitationRejectedPanel()
        self.notify.debug('Creating Invititation Rejected Panel.')
        self.__invitationRejectedPanel = BoardingGroupInvitationRejectedPanel(boardingParty, inviteeId, **kw)

    def destroyInvitingPanel(self):
        if self.isInvitingPanelUp():
            self.__invitingPanel.cleanup()
            self.__invitingPanel = None
        return

    def destroyInvitationRejectedPanel(self):
        if self.isInvitationRejectedPanelUp():
            self.__invitationRejectedPanel.cleanup()
            self.__invitationRejectedPanel = None
        return

    def isInvitingPanelIdCorrect(self, inviteeId):
        if self.isInvitingPanelUp():
            if inviteeId == self.__invitingPanel.avId:
                return True
            else:
                self.notify.warning('Got a response back from an invitee, but a different invitee panel was open. Maybe lag?')
        return False

    def isInvitingPanelUp(self):
        if self.__invitingPanel:
            if not self.__invitingPanel.isEmpty():
                return True
            self.__invitingPanel = None
        return False

    def isInvitationRejectedPanelUp(self):
        if self.__invitationRejectedPanel:
            if not self.__invitationRejectedPanel.isEmpty():
                return True
            self.__invitationRejectedPanel = None
        return False

    def forceCleanup(self):
        if self.isInvitingPanelUp():
            self.__invitingPanel.forceCleanup()
            self.__invitingPanel = None
        if self.isInvitationRejectedPanelUp():
            self.__invitationRejectedPanel.forceCleanup()
            self.__invitationRejectedPanel = None
        return


class BoardingGroupInviterPanelBase(ToonHeadDialog.ToonHeadDialog):
    notify = DirectNotifyGlobal.directNotify.newCategory('BoardingGroupInviterPanelBase')

    def __init__(self, boardingParty, inviteeId, **kw):
        self.boardingParty = boardingParty
        self.avId = inviteeId
        avatar = base.cr.doId2do.get(self.avId)
        self.avatarName = ''
        if avatar:
            self.avatar = avatar
            self.avatarName = avatar.getName()
            avatarDNA = avatar.getStyle()
        self.defineParams()
        command = self.handleButton
        optiondefs = (('dialogName', self.dialogName, None),
         ('text', self.inviterText, None),
         ('style', self.panelStyle, None),
         ('buttonTextList', self.buttonTextList, None),
         ('command', command, None),
         ('image_color', (1.0, 0.89, 0.77, 1.0), None),
         ('geom_scale', 0.2, None),
         ('geom_pos', (-0.1, 0, -0.025), None),
         ('pad', (0.075, 0.075), None),
         ('topPad', 0, None),
         ('midPad', 0, None),
         ('pos', (0.45, 0, 0.75), None),
         ('scale', 0.75, None))
        self.defineoptions(kw, optiondefs)
        ToonHeadDialog.ToonHeadDialog.__init__(self, avatarDNA)
        self.show()
        return

    def defineParams(self):
        self.notify.error('setupParams: This method should not be called from the base class. Derived class should override this method')

    def cleanup(self):
        self.notify.debug('Destroying Panel.')
        ToonHeadDialog.ToonHeadDialog.cleanup(self)

    def forceCleanup(self):
        self.handleButton(0)

    def handleButton(self, value):
        self.cleanup()


class BoardingGroupInvitingPanel(BoardingGroupInviterPanelBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('BoardingGroupInvitingPanel')

    def __init__(self, boardingParty, inviteeId, **kw):
        BoardingGroupInviterPanelBase.__init__(self, boardingParty, inviteeId, **kw)
        self.initialiseoptions(BoardingGroupInvitingPanel)
        self.setupUnexpectedExitHooks()

    def defineParams(self):
        self.dialogName = 'BoardingGroupInvitingPanel'
        self.inviterText = TTLocalizer.BoardingInvitingMessage % self.avatarName
        self.panelStyle = TTDialog.CancelOnly
        self.buttonTextList = [OTPLocalizer.GuildInviterCancel]

    def handleButton(self, value):
        self.boardingParty.requestCancelInvite(self.avId)
        BoardingGroupInviterPanelBase.cleanup(self)

    def setupUnexpectedExitHooks(self):
        if self.avId in base.cr.doId2do:
            toon = base.cr.doId2do[self.avId]
            self.unexpectedExitEventName = toon.uniqueName('disable')
            self.accept(self.unexpectedExitEventName, self.forceCleanup)

    def forceCleanup(self):
        self.ignore(self.unexpectedExitEventName)
        BoardingGroupInviterPanelBase.forceCleanup(self)


class BoardingGroupInvitationRejectedPanel(BoardingGroupInviterPanelBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('BoardingGroupInvitationRejectedPanel')

    def __init__(self, boardingParty, inviteeId, **kw):
        BoardingGroupInviterPanelBase.__init__(self, boardingParty, inviteeId, **kw)
        self.initialiseoptions(BoardingGroupInvitationRejectedPanel)

    def defineParams(self):
        self.dialogName = 'BoardingGroupInvitationRejectedPanel'
        self.inviterText = TTLocalizer.BoardingInvitationRejected % self.avatarName
        self.panelStyle = TTDialog.Acknowledge
        self.buttonTextList = [OTPLocalizer.GuildInviterOK]
