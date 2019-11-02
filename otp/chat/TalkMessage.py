

class TalkMessage:

    def __init__(self, messageId, timeStamp, body, senderAvatarId, senderAvatarName, senderAccountId, senderAccountName, receiverAvatarId, receiverAvatarName, receiverAccountId, receiverAccountName, talkType, extraInfo = None):
        self.timeStamp = timeStamp
        self.body = body
        self.senderAvatarId = senderAvatarId
        self.senderAvatarName = senderAvatarName
        self.senderAccountId = senderAccountId
        self.senderAccountName = senderAccountName
        self.receiverAvatarId = receiverAvatarId
        self.receiverAvatarName = receiverAvatarName
        self.receiverAccountId = receiverAccountId
        self.receiverAccountName = receiverAccountName
        self.talkType = talkType
        self.extraInfo = extraInfo
        self.messageId = messageId

    def getMessageId(self):
        return self.messageId

    def setMessageId(self, id):
        self.messageId = id

    def getTimeStamp(self):
        return self.timeStamp

    def setTimeStamp(self, timeStamp):
        self.timeStamp = timeStamp

    def getBody(self):
        return self.body

    def setBody(self, body):
        self.body = body

    def getSenderAvatarId(self):
        return self.senderAvatarId

    def setSenderAvatarId(self, senderAvatarId):
        self.senderAvatarId = senderAvatarId

    def getSenderAvatarName(self):
        return self.senderAvatarName

    def setSenderAvatarName(self, senderAvatarName):
        self.senderAvatarName = senderAvatarName

    def getSenderAccountId(self):
        return self.senderAccountId

    def setSenderAccountId(self, senderAccountId):
        self.senderAccountId = senderAccountId

    def getSenderAccountName(self):
        return self.senderAccountName

    def setSenderAccountName(self, senderAccountName):
        self.senderAccountName = senderAccountName

    def getReceiverAvatarId(self):
        return self.receiverAvatarId

    def setReceiverAvatarId(self, receiverAvatarId):
        self.receiverAvatarId = receiverAvatarId

    def getReceiverAvatarName(self):
        return self.receiverAvatarName

    def setReceiverAvatarName(self, receiverAvatarName):
        self.receiverAvatarName = receiverAvatarName

    def getReceiverAccountId(self):
        return self.receiverAccountId

    def setReceiverAccountId(self, receiverAccountId):
        self.receiverAccountId = receiverAccountId

    def getReceiverAccountName(self):
        return self.receiverAccountName

    def setReceiverAccountName(self, receiverAccountName):
        self.receiverAccountName = receiverAccountName

    def getTalkType(self):
        return self.talkType

    def setTalkType(self, talkType):
        self.talkType = talkType

    def getExtraInfo(self):
        return self.extraInfo

    def setExtraInfo(self, extraInfo):
        self.extraInfo = extraInfo
