import string
import sys
import time

from panda3d.core import *

from direct.directnotify import DirectNotifyGlobal
from direct.showbase import DirectObject

from otp.chat.ChatGlobals import *
from otp.chat.TalkAssistant import TalkAssistant
from otp.chat.TalkGlobals import *
from otp.chat.TalkMessage import TalkMessage
from otp.otpbase import OTPGlobals, OTPLocalizer
from otp.speedchat import SCDecoders, SpeedChatGlobals

from toontown.speedchat import TTSCDecoders
from toontown.toonbase import TTLocalizer


class TTTalkAssistant(TalkAssistant):
    notify = DirectNotifyGlobal.directNotify.newCategory('TTTalkAssistant')

    def __init__(self):
        TalkAssistant.__init__(self)

    def clearHistory(self):
        TalkAssistant.clearHistory(self)

    def sendPlayerWhisperToonTaskSpeedChat(self, taskId, toNpcId, toonProgress, msgIndex, receiverId):
        error = None
        base.cr.speedchatRelay.sendSpeedchatToonTask(receiverId, taskId, toNpcId, toonProgress, msgIndex)
        message = TTSCDecoders.decodeTTSCToontaskMsg(taskId, toNpcId, toonProgress, msgIndex)
        if self.logWhispers:
            receiverName = self.findName(receiverId, 1)
            newMessage = TalkMessage(self.countMessage(), self.stampTime(), message, localAvatar.doId, localAvatar.getName(), localAvatar.DISLid, localAvatar.DISLname, None, None, receiverId, receiverName, TALK_ACCOUNT, None)
            self.historyComplete.append(newMessage)
            self.addToHistoryDoId(newMessage, localAvatar.doId)
            self.addToHistoryDISLId(newMessage, base.cr.accountDetailRecord.playerAccountId)
            messenger.send('NewOpenMessage', [newMessage])
        return error

    def sendToonTaskSpeedChat(self, taskId, toNpcId, toonProgress, msgIndex):
        error = None
        messenger.send(SCChatEvent)
        messenger.send('chatUpdateSCToontask', [taskId,
         toNpcId,
         toonProgress,
         msgIndex])
        return error
