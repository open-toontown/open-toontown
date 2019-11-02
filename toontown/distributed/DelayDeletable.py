from direct.distributed.DistributedObject import ESGenerating, ESGenerated, ESNum2Str

class DelayDeletable:
    DelayDeleteSerialGen = SerialNumGen()

    def delayDelete(self):
        pass

    def acquireDelayDelete(self, name):
        global ESGenerating
        global ESGenerated
        if not self._delayDeleteForceAllow and self.activeState not in (ESGenerating, ESGenerated):
            self.notify.error('cannot acquire DelayDelete "%s" on %s because it is in state %s' % (name, self.__class__.__name__, ESNum2Str[self.activeState]))
        if self.getDelayDeleteCount() == 0:
            self.cr._addDelayDeletedDO(self)
        token = DelayDeletable.DelayDeleteSerialGen.next()
        self._token2delayDeleteName[token] = name
        return token

    def releaseDelayDelete(self, token):
        name = self._token2delayDeleteName.pop(token)
        if len(self._token2delayDeleteName) == 0:
            self.cr._removeDelayDeletedDO(self)
            if self._delayDeleted:
                self.disableAnnounceAndDelete()

    def getDelayDeleteNames(self):
        return self._token2delayDeleteName.values()

    def forceAllowDelayDelete(self):
        self._delayDeleteForceAllow = True
