from otp.speedchat.SCTerminal import SCTerminal
from otp.otpbase.OTPLocalizer import SpeedChatStaticText
TTSCSingingMsgEvent = 'SCSingingMsg'

def decodeSCStaticTextMsg(textId):
    return SpeedChatStaticText.get(textId, None)


class TTSCSingingTerminal(SCTerminal):

    def __init__(self, textId):
        SCTerminal.__init__(self)
        self.textId = textId
        self.text = SpeedChatStaticText[self.textId]

    def handleSelect(self):
        SCTerminal.handleSelect(self)
        messenger.send(self.getEventName(TTSCSingingMsgEvent), [self.textId])

    def finalize(self):
        args = {'rolloverSound': None,
         'clickSound': None}
        SCTerminal.finalize(self, args)
        return
