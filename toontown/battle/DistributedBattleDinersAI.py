from direct.directnotify import DirectNotifyGlobal
from toontown.battle import DistributedBattleFinalAI

class DistributedBattleDinersAI(DistributedBattleFinalAI.DistributedBattleFinalAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedBattleDinersAI')

    def __init__(self, air, bossCog, roundCallback, finishCallback, battleSide):
        DistributedBattleFinalAI.DistributedBattleFinalAI.__init__(self, air, bossCog, roundCallback, finishCallback, battleSide)

    def startBattle(self, toonIds, suits):
        self.joinableFsm.request('Joinable')
        for toonId in toonIds:
            if self.addToon(toonId):
                self.activeToons.append(toonId)

        self.d_setMembers()
        for suit in suits:
            self.pendingSuits.append(suit)

        self.d_setMembers()
        self.needAdjust = 1
        self.b_setState('ReservesJoining')
