import datetime
import os
import socket

from direct.distributed.DistributedObject import DistributedObject
from direct.distributed.DistributedObjectGlobal import DistributedObjectGlobal

from toontown.toonbase import ToontownGlobals


class DistributedWhitelistMgr(DistributedObject):
    notify = directNotify.newCategory('WhitelistMgr')
    neverDisable = 1

    def __init__(self, cr):
        DistributedObject.__init__(self, cr)
        base.cr.whitelistMgr = self

    def delete(self):
        DistributedObject.delete(self)
        self.cr.whitelistMgr = None
        return

    def disable(self):
        self.notify.debug("i'm disabling WhitelistMgr right now.")
        DistributedObject.disable(self)

    def generate(self):
        self.notify.debug('BASE: generate')
        DistributedObject.generate(self)

    def updateWhitelist(self):
        messenger.send('updateWhitelist')
        self.notify.info('Updating white list')
