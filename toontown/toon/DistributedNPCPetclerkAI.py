from otp.ai.AIBaseGlobal import *
from pandac.PandaModules import *
from DistributedNPCToonBaseAI import *
from toontown.toonbase import TTLocalizer
from direct.task import Task
from toontown.fishing import FishGlobals
from toontown.pets import PetUtil, PetDNA, PetConstants

class DistributedNPCPetclerkAI(DistributedNPCToonBaseAI):

    def __init__(self, air, npcId):
        DistributedNPCToonBaseAI.__init__(self, air, npcId)
        self.givesQuests = 0
        self.busy = 0

    def delete(self):
        taskMgr.remove(self.uniqueName('clearMovie'))
        self.ignoreAll()
        DistributedNPCToonBaseAI.delete(self)

    def avatarEnter(self):
        avId = self.air.getAvatarIdFromSender()
        if not self.air.doId2do.has_key(avId):
            self.notify.warning('Avatar: %s not found' % avId)
            return
        if self.isBusy():
            self.freeAvatar(avId)
            return
        self.petSeeds = simbase.air.petMgr.getAvailablePets(3, 2)
        numGenders = len(PetDNA.PetGenders)
        self.petSeeds *= numGenders
        self.petSeeds.sort()
        self.sendUpdateToAvatarId(avId, 'setPetSeeds', [self.petSeeds])
        self.transactionType = ''
        av = self.air.doId2do[avId]
        self.busy = avId
        self.acceptOnce(self.air.getAvatarExitEvent(avId), self.__handleUnexpectedExit, extraArgs=[avId])
        flag = NPCToons.SELL_MOVIE_START
        self.d_setMovie(avId, flag)
        taskMgr.doMethodLater(PetConstants.PETCLERK_TIMER, self.sendTimeoutMovie, self.uniqueName('clearMovie'))
        DistributedNPCToonBaseAI.avatarEnter(self)

    def rejectAvatar(self, avId):
        self.notify.warning('rejectAvatar: should not be called by a fisherman!')

    def d_setMovie(self, avId, flag, extraArgs = []):
        self.sendUpdate('setMovie', [flag,
         self.npcId,
         avId,
         extraArgs,
         ClockDelta.globalClockDelta.getRealNetworkTime()])

    def sendTimeoutMovie(self, task):
        self.d_setMovie(self.busy, NPCToons.SELL_MOVIE_TIMEOUT)
        self.sendClearMovie(None)
        return Task.done

    def sendClearMovie(self, task):
        self.ignore(self.air.getAvatarExitEvent(self.busy))
        taskMgr.remove(self.uniqueName('clearMovie'))
        self.busy = 0
        self.d_setMovie(0, NPCToons.SELL_MOVIE_CLEAR)
        return Task.done

    def fishSold(self):
        avId = self.air.getAvatarIdFromSender()
        if self.busy != avId:
            self.air.writeServerEvent('suspicious', avId, 'DistributedNPCPetshopAI.fishSold busy with %s' % self.busy)
            self.notify.warning('somebody called fishSold that I was not busy with! avId: %s' % avId)
            return
        av = simbase.air.doId2do.get(avId)
        if av:
            trophyResult = self.air.fishManager.creditFishTank(av)
            if trophyResult:
                movieType = NPCToons.SELL_MOVIE_TROPHY
                extraArgs = [len(av.fishCollection), FishGlobals.getTotalNumFish()]
            else:
                movieType = NPCToons.SELL_MOVIE_COMPLETE
                extraArgs = []
            self.d_setMovie(avId, movieType, extraArgs)
            self.transactionType = 'fish'
        self.sendClearMovie(None)
        return

    def petAdopted(self, petNum, nameIndex):
        avId = self.air.getAvatarIdFromSender()
        if self.busy != avId:
            self.air.writeServerEvent('suspicious', avId, 'DistributedNPCPetshopAI.petAdopted busy with %s' % self.busy)
            self.notify.warning('somebody called petAdopted that I was not busy with! avId: %s' % avId)
            return
        av = simbase.air.doId2do.get(avId)
        if av:
            from toontown.hood import ZoneUtil
            zoneId = ZoneUtil.getCanonicalSafeZoneId(self.zoneId)
            if petNum not in range(0, len(self.petSeeds)):
                self.air.writeServerEvent('suspicious', avId, 'DistributedNPCPetshopAI.petAdopted and no such pet!')
                self.notify.warning('somebody called petAdopted on a non-existent pet! avId: %s' % avId)
                return
            cost = PetUtil.getPetCostFromSeed(self.petSeeds[petNum], zoneId)
            if cost > av.getTotalMoney():
                self.air.writeServerEvent('suspicious', avId, "DistributedNPCPetshopAI.petAdopted and toon doesn't have enough money!")
                self.notify.warning("somebody called petAdopted and didn't have enough money to adopt! avId: %s" % avId)
                return
            if av.petId != 0:
                simbase.air.petMgr.deleteToonsPet(avId)
            gender = petNum % len(PetDNA.PetGenders)
            if nameIndex not in range(0, TTLocalizer.PetNameIndexMAX):
                self.air.writeServerEvent('avoid_crash', avId, "DistributedNPCPetclerkAI.petAdopted and didn't have valid nameIndex!")
                self.notify.warning("somebody called petAdopted and didn't have valid nameIndex to adopt! avId: %s" % avId)
                return
            simbase.air.petMgr.createNewPetFromSeed(avId, self.petSeeds[petNum], nameIndex=nameIndex, gender=gender, safeZoneId=zoneId)
            self.transactionType = 'adopt'
            bankPrice = min(av.getBankMoney(), cost)
            walletPrice = cost - bankPrice
            av.b_setBankMoney(av.getBankMoney() - bankPrice)
            av.b_setMoney(av.getMoney() - walletPrice)

    def petReturned(self):
        avId = self.air.getAvatarIdFromSender()
        if self.busy != avId:
            self.air.writeServerEvent('suspicious', avId, 'DistributedNPCPetshopAI.petReturned busy with %s' % self.busy)
            self.notify.warning('somebody called petReturned that I was not busy with! avId: %s' % avId)
            return
        av = simbase.air.doId2do.get(avId)
        if av:
            simbase.air.petMgr.deleteToonsPet(avId)
            self.transactionType = 'return'

    def transactionDone(self):
        avId = self.air.getAvatarIdFromSender()
        if self.busy != avId:
            self.air.writeServerEvent('suspicious', avId, 'DistributedNPCPetshopAI.transactionDone busy with %s' % self.busy)
            self.notify.warning('somebody called transactionDone that I was not busy with! avId: %s' % avId)
            return
        av = simbase.air.doId2do.get(avId)
        if av:
            if self.transactionType == 'adopt':
                self.d_setMovie(avId, NPCToons.SELL_MOVIE_PETADOPTED)
            elif self.transactionType == 'return':
                self.d_setMovie(avId, NPCToons.SELL_MOVIE_PETRETURNED)
            elif self.transactionType == '':
                self.d_setMovie(avId, NPCToons.SELL_MOVIE_PETCANCELED)
        self.sendClearMovie(None)
        return

    def __handleUnexpectedExit(self, avId):
        self.notify.warning('avatar:' + str(avId) + ' has exited unexpectedly')
        self.notify.warning('not busy with avId: %s, busy: %s ' % (avId, self.busy))
        taskMgr.remove(self.uniqueName('clearMovie'))
        self.sendClearMovie(None)
        return
