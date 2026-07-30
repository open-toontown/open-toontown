import datetime
import os
import socket

from direct.distributed.DistributedObject import DistributedObject
from direct.distributed.DistributedObjectGlobal import DistributedObjectGlobal

from toontown.toonbase import ToontownGlobals


class DistributedSecurityMgr(DistributedObject):
    notify = directNotify.newCategory('SecurityMgr')
    neverDisable = 1

    def __init__(self, cr):
        DistributedObject.__init__(self, cr)
        base.cr.whitelistMgr = self

    def delete(self):
        DistributedObject.delete(self)
        self.cr.whitelistMgr = None
        return

    def disable(self):
        self.notify.debug("i'm disabling SecurityMgr right now.")
        DistributedObject.disable(self)

    def generate(self):
        self.notify.debug('BASE: generate')
        DistributedObject.generate(self)

    def updateWhitelist(self):
        messenger.send('updateWhitelist')
        self.notify.info('Updating white list')
