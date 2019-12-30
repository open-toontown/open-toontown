from direct.distributed.DistributedObject import DistributedObject
from direct.distributed.DistributedObjectGlobal import DistributedObjectGlobal
from pandac.PandaModules import *
from otp.otpbase import OTPGlobals

class DistributedChatManager(DistributedObjectGlobal):

    def __init__(self, cr):
        DistributedObjectGlobal.__init__(self, cr)
        self.notify.warning('ChatManager going online')

    def delete(self):
        self.ignoreAll()
        self.notify.warning('ChatManager going offline')
        self.cr.chatManager = None
        DistributedObjectGlobal.delete(self)
        return

    def online(self):
        pass

    def adminChat(self, aboutId, message):
        self.notify.warning('Admin Chat(%s): %s' % (aboutId, message))
        messenger.send('adminChat', [aboutId, message])

    def sendChatTo(self, message, chatFlags):
        self.sendUpdate('chatTo', [message, chatFlags])

    def chatFrom(self, fromId, message, chatFlags):
        pass

    def sendSpeedChatTo(self, msgIndex):
        self.sendUpdate('speedChatTo', [msgIndex])

    def speedChatFrom(self, fromId, msgIndex):
        pass

    def sendSpeedChatCustomTo(self, msgIndex):
        self.sendUpdate('speedChatCustomTo', [msgIndex])

    def speedChatCustomFrom(self, fromId, msgIndex):
        pass

    def sendWhisperTo(self, toId, message):
        self.sendUpdate('whisperTo', [toId, message])

    def whisperFrom(self, fromId, message):
        if base.cr.wantSwitchboardHacks:
            print('received whisper on avatar: %s' % message)
            whisper = WhisperPopup(message, OTPGlobals.getInterfaceFont(), WhisperPopup.WTNormal)
            whisper.manage(base.marginManager)

    def sendWhisperSCTo(self, toId, msgIndex):
        self.sendUpdate('whisperSCTo', [toId, msgIndex])

    def whisperSCFrom(self, fromId, msgIndex):
        pass

    def sendWhisperSCCustomTo(self, toId, msgIndex):
        self.sendUpdate('whisperSCCustomTo', [toId, msgIndex])

    def whisperSCCustomFrom(self, fromId, msgIndex):
        pass

    def sendWhisperSCEmoteTo(self, toId, emoteId):
        self.sendUpdate('whisperSCEmoteTo', [toId, emoteId])

    def whisperSCEmoteFrom(self, fromId, emoteId):
        pass

    def whisperIgnored(self, fromId):
        pass

    def sendCrewChatTo(self, message):
        self.sendUpdate('crewChatTo', [message])

    def crewChatFrom(self, fromId, message):
        pass

    def sendGuildChatTo(self, message):
        self.sendUpdate('guildChatTo', [message])

    def guildChatFrom(self, fromId, message):
        pass
