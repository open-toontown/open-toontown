from otp.ai.AIBaseGlobal import *
from pandac.PandaModules import *
from DistributedNPCToonBaseAI import *
from toontown.fishing import FishGlobals
from toontown.toonbase import TTLocalizer
from toontown.fishing import FishGlobals
from direct.task import Task

class DistributedNPCFishermanAI(DistributedNPCToonBaseAI):

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
        av = self.air.doId2do[avId]
        self.busy = avId
        self.acceptOnce(self.air.getAvatarExitEvent(avId), self.__handleUnexpectedExit, extraArgs=[avId])
        value = av.fishTank.getTotalValue()
        if value > 0:
            flag = NPCToons.SELL_MOVIE_START
            self.d_setMovie(avId, flag)
            taskMgr.doMethodLater(30.0, self.sendTimeoutMovie, self.uniqueName('clearMovie'))
        else:
            flag = NPCToons.SELL_MOVIE_NOFISH
            self.d_setMovie(avId, flag)
            self.sendClearMovie(None)
        DistributedNPCToonBaseAI.avatarEnter(self)
        return

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

    def completeSale(self, sell):
        avId = self.air.getAvatarIdFromSender()
        if self.busy != avId:
            self.air.writeServerEvent('suspicious', avId, 'DistributedNPCFishermanAI.completeSale busy with %s' % self.busy)
            self.notify.warning('somebody called setMovieDone that I was not busy with! avId: %s' % avId)
            return
        if sell:
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
        else:
            av = simbase.air.doId2do.get(avId)
            if av:
                self.d_setMovie(avId, NPCToons.SELL_MOVIE_NOFISH)
        self.sendClearMovie(None)
        return

    def __handleUnexpectedExit(self, avId):
        self.notify.warning('avatar:' + str(avId) + ' has exited unexpectedly')
        self.notify.warning('not busy with avId: %s, busy: %s ' % (avId, self.busy))
        taskMgr.remove(self.uniqueName('clearMovie'))
        self.sendClearMovie(None)
        return
