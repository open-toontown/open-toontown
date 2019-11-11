from direct.distributed.DistributedObjectGlobal import DistributedObjectGlobal
from direct.directnotify import DirectNotifyGlobal

class AstronLoginManager(DistributedObjectGlobal):
    notify = DirectNotifyGlobal.directNotify.newCategory('AstronLoginManager')

    def __init__(self, cr):
        DistributedObjectGlobal.__init__(self, cr)
        self.doneEvent = None

    def handleRequestLogin(self, doneEvent):
        self.doneEvent = doneEvent
        playToken = self.cr.playToken or 'dev'
        self.sendRequestLogin(playToken)

    def sendRequestLogin(self, playToken):
        self.sendUpdate('requestLogin', [playToken])

    def loginResponse(self, responseBlob):
        # TODO HANDLE THIS PROPERLY
        messenger.send(self.doneEvent, [{'mode': 'success'}])
