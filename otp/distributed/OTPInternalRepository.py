from direct.directnotify import DirectNotifyGlobal
from direct.distributed.AstronInternalRepository import AstronInternalRepository

# TODO: Remove Astron dependence.

class OTPInternalRepository(AstronInternalRepository):
    notify = DirectNotifyGlobal.directNotify.newCategory('OTPInternalRepository')
    dbId = 4003

    def __init__(self, baseChannel, serverId, dcFileNames, dcSuffix, connectMethod, threadedNet):
        AstronInternalRepository.__init__(self, baseChannel, serverId=serverId, dcFileNames=dcFileNames, dcSuffix=dcSuffix, connectMethod=connectMethod, threadedNet=threadedNet)

    def handleConnected(self):
        AstronInternalRepository.handleConnected(self)

    def getAccountIdFromSender(self):
        return (self.getMsgSender() >> 32) & 0xFFFFFFFF

    def getAvatarIdFromSender(self):
        return self.getMsgSender() & 0xFFFFFFFF
