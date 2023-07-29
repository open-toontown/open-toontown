from otp.ai.AIBaseGlobal import *
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM
from direct.distributed import ClockDelta
from direct.distributed import DistributedObjectAI
from . import DistributedFurnitureItemAI
from direct.task.Task import Task
from direct.fsm import State
from .BankGlobals import *

class DistributedBankAI(DistributedFurnitureItemAI.DistributedFurnitureItemAI):

    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedBankAI')

    def __init__(self, air, furnitureMgr, item):
        DistributedFurnitureItemAI.DistributedFurnitureItemAI.__init__(
            self, air, furnitureMgr, item)
        self.ownerId = self.furnitureMgr.house.ownerId
        self.busy = 0

    def delete(self):
        self.notify.debug("delete()")
        self.ignoreAll()
        DistributedFurnitureItemAI.DistributedFurnitureItemAI.delete(self)

    def freeAvatar(self, avId):
        # Free this avatar, probably because he requested interaction while
        # I was busy. This can happen when two avatars request interaction
        # at the same time. The AI will accept the first, sending a setMovie,
        # and free the second
        self.sendUpdateToAvatarId(avId, "freeAvatar", [])

    def avatarEnter(self):
        self.notify.debug("avatarEnter()")
        avId = self.air.getAvatarIdFromSender()
        # this avatar has come within range
        self.notify.debug("avatarEnter() ...avatarId=%s" % (avId))

        # If we are busy, free this new avatar
        if self.busy:
            self.notify.debug("avatarEnter() ...already busy with: %s" % (self.busy))
            self.freeAvatar(avId)
            return

        # Fetch the actual avatar object
        av = self.air.doId2do.get(avId)        
        if not av:
            self.air.writeServerEvent('suspicious', avId, 'DistributedBank.avatarEnter')
            self.notify.warning("av %s not in doId2do tried to transfer money" % (avId))
            return

        # Flag us as busy with this avatar Id
        self.busy = avId

        # Handle unexpected exit
        self.acceptOnce(self.air.getAvatarExitEvent(avId),
                        self.__handleUnexpectedExit, extraArgs=[avId])
        self.acceptOnce("bootAvFromEstate-"+str(avId),
                        self.__handleBootMessage, extraArgs=[avId])

        # Find the owner of the bank
        if self.ownerId:
            if self.ownerId == avId:
                # We own the bank, popup the gui and let this avatar do his banking
                assert(self.notify.debug(
                    "avatarEnter() ...setMovie: BANK_MOVIE_GUI (%s)" % (BANK_MOVIE_GUI,)))
                self.sendUpdate("setMovie", [BANK_MOVIE_GUI, avId,
                                             ClockDelta.globalClockDelta.getRealNetworkTime()])
            else:
                # You are not the owner of this bank, sorry
                assert(self.notify.debug(
                    "avatarEnter() ...setMovie: BANK_MOVIE_NOT_OWNER (%s)" % (BANK_MOVIE_NOT_OWNER,)))
                self.sendUpdate("setMovie", [BANK_MOVIE_NOT_OWNER, avId,
                                             ClockDelta.globalClockDelta.getRealNetworkTime()])
                self.sendClearMovie(None)
        else:
            # Nobody lives here, sorry
            assert(self.notify.debug(
                "avatarEnter() ...setMovie: BANK_MOVIE_NO_OWNER (%s)" % (BANK_MOVIE_NO_OWNER,)))
            self.sendUpdate("setMovie", [BANK_MOVIE_NO_OWNER, avId,
                                         ClockDelta.globalClockDelta.getRealNetworkTime()])
            self.sendClearMovie(None)

    def __handleUnexpectedExit(self, avId):
        self.notify.warning('avatar:' + str(avId) + ' has exited unexpectedly')
        self.sendClearMovie(None)

    def __handleBootMessage(self, avId):
        self.notify.warning('avatar:' + str(avId) + ' got booted ')
        self.sendClearMovie(None)
        
    def sendClearMovie(self, task):
        assert(self.notify.debug('sendClearMovie()'))
        # Ignore unexpected exits on whoever I was busy with
        self.ignoreAll()
        self.busy = 0
        self.sendUpdate("setMovie", [BANK_MOVIE_CLEAR, 0,
                                     ClockDelta.globalClockDelta.getRealNetworkTime()])
        return Task.done

    def transferMoney(self, amount):
        avId = self.air.getAvatarIdFromSender()
        assert(self.notify.debug('transferMoney(amount=%s) avatarId=%s'%(amount, avId)))
        av = self.air.doId2do.get(avId)
        
        if avId!=self.busy:
            self.notify.warning(
                "avatarId %s tried to transfer money, but we were talking with avatarId %s"
                %(avId, self.busy))
            return
        
        if not av:
            self.air.writeServerEvent('suspicious', avId, 'DistributedBank.transferMoney')
            self.notify.warning("av %s not in doId2do tried to transfer money" % (avId))
            return

        # Do the money transfer
        simbase.air.bankMgr.transferMoneyForAv(amount, av)

        if amount > 0:
            # Deposit
            assert(self.notify.debug(
                "transferMoney() ...setMovie: BANK_MOVIE_DEPOSIT (%s)" % (BANK_MOVIE_DEPOSIT,)))
            self.sendUpdate("setMovie", [BANK_MOVIE_DEPOSIT, avId,
                                         ClockDelta.globalClockDelta.getRealNetworkTime()])
            # This should be a dolater when we have animation lengths
            self.sendClearMovie(None)
        elif amount < 0:
            # Withdraw
            assert(self.notify.debug(
                "transferMoney() ...setMovie: BANK_MOVIE_WITHDRAW (%s)" % (BANK_MOVIE_WITHDRAW,)))
            self.sendUpdate("setMovie", [BANK_MOVIE_WITHDRAW, avId,
                                         ClockDelta.globalClockDelta.getRealNetworkTime()])
            # This should be a dolater when we have animation lengths
            self.sendClearMovie(None)
        else:
            # No transaction
            assert(self.notify.debug(
                "avatarEnter() ...setMovie: BANK_MOVIE_NO_OP (%s)" % (BANK_MOVIE_NO_OP,)))
            self.sendUpdate("setMovie", [BANK_MOVIE_NO_OP, avId,
                                         ClockDelta.globalClockDelta.getRealNetworkTime()])
            # This should be a dolater when we have animation lengths
            self.sendClearMovie(None)
