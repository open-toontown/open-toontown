import socket
import datetime
import os
from direct.distributed.DistributedObjectGlobal import DistributedObjectGlobal
from direct.distributed.DistributedObject import DistributedObject
from toontown.toonbase import ToontownGlobals
from toontown.uberdog import InGameNewsResponses

class DistributedInGameNewsMgr(DistributedObject):
    notify = directNotify.newCategory('InGameNewsMgr')
    neverDisable = 1

    def __init__(self, cr):
        DistributedObject.__init__(self, cr)
        base.cr.inGameNewsMgr = self

    def delete(self):
        DistributedObject.delete(self)
        self.cr.inGameNewsMgr = None
        return

    def disable(self):
        self.notify.debug("i'm disabling InGameNewsMgr  rightnow.")
        DistributedObject.disable(self)

    def generate(self):
        self.notify.debug('BASE: generate')
        DistributedObject.generate(self)

    def setLatestIssueStr(self, issueStr):
        self.latestIssueStr = issueStr
        self.latestIssue = base.cr.toontownTimeManager.convertUtcStrToToontownTime(issueStr)
        messenger.send('newIssueOut')
        self.notify.info('latestIssue=%s' % self.latestIssue)

    def getLatestIssueStr(self):
        pass

    def getLatestIssue(self):
        return self.latestIssue
