from panda3d.core import *

from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObject


class SafeZoneManager(DistributedObject.DistributedObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('SafeZoneManager')
    neverDisable = 1

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)

    def generate(self):
        DistributedObject.DistributedObject.generate(self)
        self.accept('enterSafeZone', self.d_enterSafeZone)
        self.accept('exitSafeZone', self.d_exitSafeZone)

    def disable(self):
        self.ignoreAll()
        DistributedObject.DistributedObject.disable(self)

    def d_enterSafeZone(self):
        self.sendUpdate('enterSafeZone', [])

    def d_exitSafeZone(self):
        self.sendUpdate('exitSafeZone', [])
