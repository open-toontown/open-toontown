from pandac.PandaModules import *
from toontown.toonbase import ToontownGlobals
from direct.distributed import DistributedObject
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import TTLocalizer

class LobbyManager(DistributedObject.DistributedObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('LobbyManager')
    SetFactoryZoneMsg = 'setFactoryZone'

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)

    def generate(self):
        self.notify.debug('generate')
        DistributedObject.DistributedObject.generate(self)

    def disable(self):
        self.notify.debug('disable')
        self.ignoreAll()
        DistributedObject.DistributedObject.disable(self)

    def getSuitDoorOrigin(self):
        return 1

    def getBossLevel(self):
        return 0
