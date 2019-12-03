from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectGlobal import DistributedObjectGlobal


class AstronLoginManager(DistributedObjectGlobal):
    notify = DirectNotifyGlobal.directNotify.newCategory('AstronLoginManager')

    def __init__(self, cr):
        DistributedObjectGlobal.__init__(self, cr)
        self._callback = None

    def handleRequestLogin(self):
        playToken = self.cr.playToken or 'dev'
        self.sendRequestLogin(playToken)

    def sendRequestLogin(self, playToken):
        self.sendUpdate('requestLogin', [playToken])

    def loginResponse(self, responseBlob):
        self.cr.loginScreen.handleLoginToontownResponse(responseBlob)

    def sendRequestAvatarList(self):
        self.sendUpdate('requestAvatarList')

    def avatarListResponse(self, avatarList):
        self.cr.handleAvatarListResponse(avatarList)

    def sendCreateAvatar(self, avDNA, avName, avPosition):
        # avName isn't used. Sad!
        self.sendUpdate('createAvatar', [avDNA.makeNetString(), avPosition])

    def createAvatarResponse(self, avId):
        messenger.send('nameShopCreateAvatarDone', [avId])

    def sendSetNamePattern(self, avId, p1, f1, p2, f2, p3, f3, p4, f4, callback):
        self._callback = callback
        self.sendUpdate('setNamePattern', [avId, p1, f1, p2, f2, p3, f3, p4, f4])

    def namePatternAnswer(self, avId, status):
        self._callback(avId, status)

    def sendSetNameTyped(self, avId, name, callback):
        self._callback = callback
        self.sendUpdate('setNameTyped', [avId, name])

    def nameTypedResponse(self, avId, status):
        self._callback(avId, status)

    def sendAcknowledgeAvatarName(self, avId, callback):
        self._callback = callback
        self.sendUpdate('acknowledgeAvatarName', [avId])

    def acknowledgeAvatarNameResponse(self):
        self._callback()

    def sendRequestRemoveAvatar(self, avId):
        self.sendUpdate('requestRemoveAvatar', [avId])

    def sendRequestPlayAvatar(self, avId):
        self.sendUpdate('requestPlayAvatar', [avId])
