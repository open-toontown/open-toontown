from .SCTerminal import SCTerminal
from otp.speedchat import SpeedChatGMHandler
SCGMTextMsgEvent = 'SCGMTextMsg'

class SCGMTextTerminal(SCTerminal):

    def __init__(self, textId):
        SCTerminal.__init__(self)
        gmHandler = SpeedChatGMHandler.SpeedChatGMHandler()
        self.textId = textId
        self.text = gmHandler.getPhrase(textId)

    def handleSelect(self):
        SCTerminal.handleSelect(self)
        messenger.send(self.getEventName(SCGMTextMsgEvent), [self.textId])
