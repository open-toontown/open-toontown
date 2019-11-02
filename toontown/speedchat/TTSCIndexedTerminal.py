from otp.speedchat.SCTerminal import *
from otp.otpbase.OTPLocalizer import SpeedChatStaticText
TTSCIndexedMsgEvent = 'SCIndexedMsg'

def decodeTTSCIndexedMsg(msgIndex):
    return SpeedChatStaticText.get(msgIndex, None)


class TTSCIndexedTerminal(SCTerminal):

    def __init__(self, msg, msgIndex):
        SCTerminal.__init__(self)
        self.text = msg
        self.msgIndex = msgIndex

    def handleSelect(self):
        SCTerminal.handleSelect(self)
        messenger.send(self.getEventName(TTSCIndexedMsgEvent), [self.msgIndex])
