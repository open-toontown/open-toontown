from direct.distributed import DistributedObject
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import TTLocalizer

class DistributedBankMgr(DistributedObject.DistributedObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedBankMgr')
    neverDisable = 1

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)

    def generate(self):
        if base.cr.bankManager != None:
            base.cr.bankManager.delete()
        base.cr.bankManager = self
        DistributedObject.DistributedObject.generate(self)
        return

    def disable(self):
        base.cr.bankManager = None
        DistributedObject.DistributedObject.disable(self)
        return

    def delete(self):
        base.cr.bankManager = None
        DistributedObject.DistributedObject.delete(self)
        return

    def d_transferMoney(self, amount):
        self.sendUpdate('transferMoney', [amount])
