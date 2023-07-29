
from direct.distributed import DistributedObjectAI
from direct.directnotify import DirectNotifyGlobal

class DistributedBankMgrAI(DistributedObjectAI.DistributedObjectAI):

    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedBankMgrAI')

    def __init__(self, air):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)

    def transferMoneyForAv(self, amount, av):
        # This is meant to be called by the AI on the avatar's behalf
        # See transferMoney for a message the client is allowed to send

        # TODO: we should check the zone the avatar is in here. We may want to
        # limit where clients can send this message from, for instance only in
        # their house or at the bank, especially in the case of the withdraw

        avId = av.getDoId()

        # See what this avatar has now
        walletBalance = av.getMoney()
        maxWalletBalance = av.getMaxMoney()
        bankBalance = av.getBankMoney()
        maxBankBalance = av.getMaxBankMoney()

        # Deposit
        if amount > 0:
            if amount > walletBalance:
                self.air.writeServerEvent('suspicious', avId, 'DistributedBankMgr.transferMoneyForAv deposit more than wallet')
                self.notify.warning("av %s tried to deposit more than he was holding" % (avId))
                return 0
            elif (amount + bankBalance) > maxBankBalance:
                self.air.writeServerEvent('suspicious', avId, 'DistributedBankMgr.transferMoneyForAv deposit more than bank limit')
                self.notify.warning("av %s tried to deposit more than his bank can hold" % (avId))
                return 0
            else:
                # Everything checked out, actually do the transaction
                # Would be nice if this was atomic, but they are two separate
                # database fields. Just update them both now
                av.b_setMoney(walletBalance - amount)
                av.b_setBankMoney(bankBalance + amount)
                # Debug the new values
                self.notify.debug("av %s completed transfer: %s, oldWallet: %s, newWallet: %s, maxWallet: %s -- oldBank: %s, newBank: %s, maxBank: %s" %
                                  (avId, amount,
                                   walletBalance, av.getMoney(), maxWalletBalance,
                                   bankBalance, av.getBankMoney(), maxBankBalance))
                return 1

        # Withdraw
        elif amount < 0:
            if abs(amount) > bankBalance:
                self.air.writeServerEvent('suspicious', avId, 'DistributedBankMgr.transferMoneyForAv withdraw more than bank')
                self.notify.warning("av %s tried to withdraw more than was in bank" % (avId))
                return 0
            elif (abs(amount) + walletBalance) > maxWalletBalance:
                self.air.writeServerEvent('suspicious', avId, 'DistributedBankMgr.transferMoneyForAv withdraw more than limit')
                self.notify.warning("av %s tried to withdraw more than he can hold" % (avId))
                return 0
            else:
                # Everything checked out, actually do the transaction
                # Would be nice if this was atomic, but they are two separate
                # database fields. Just update them both now
                av.b_setMoney(walletBalance - amount)
                av.b_setBankMoney(bankBalance + amount)
                # Debug the new values
                self.notify.debug("av %s completed transfer: %s, oldWallet: %s, newWallet: %s, maxWallet: %s -- oldBank: %s, newBank: %s, maxBank: %s" %
                                  (avId, amount,
                                   walletBalance, av.getMoney(), maxWalletBalance,
                                   bankBalance, av.getBankMoney(), maxBankBalance))
                return 1
                
        else:
            # amount was 0, nothing to do here
            return 1        

    def transferMoney(self, amount):
        # A client would like to transfer money to or from his bank
        # A positive amount is a deposit to the bank, a negative
        # amount represents a withdrawal
        # This is called as a distributed message from the client
        avId = self.air.getAvatarIdFromSender()
        av = self.air.doId2do.get(avId)
        if not av:
            self.air.writeServerEvent('suspicious', avId, 'DistributedBankMgr.transferMoney unknown avatar')
            self.notify.warning("av %s not in doId2do tried to transfer money" % (avId))
            return 0
        return self.transferMoneyForAv(amount, av)
