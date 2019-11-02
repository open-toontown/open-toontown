from otp.level import DistributedEntityAI
from direct.directnotify import DirectNotifyGlobal

class BattleBlockerAI(DistributedEntityAI.DistributedEntityAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('BattleBlockerAI')

    def __init__(self, level, entId):
        DistributedEntityAI.DistributedEntityAI.__init__(self, level, entId)
        self.suitIds = []
        self.active = 1

    def destroy(self):
        self.notify.debug('delete')
        self.ignoreAll()
        DistributedEntityAI.DistributedEntityAI.destroy(self)

    def generate(self):
        DistributedEntityAI.DistributedEntityAI.generate(self)
        self.accept('plannerCreated-' + str(self.level.doId), self.registerBlocker)

    def registerBlocker(self):
        if hasattr(self.level, 'planner'):
            self.level.planner.battleMgr.addBattleBlocker(self, self.cellId)

    def deactivate(self):
        if self.isDeleted():
            return
        self.active = 0
        self.sendUpdate('setActive', [self.active])

    def getActive(self):
        return self.active

    def addSuit(self, suit):
        self.suitIds.append(suit.doId)
        self.d_setSuits()

    def removeSuit(self, suit):
        try:
            self.suitIds.remove(suit.doId)
            self.d_setSuits()
        except:
            self.notify.debug("didn't have suitId %d" % suit.doId)

    def d_setSuits(self):
        self.sendUpdate('setSuits', [self.suitIds])

    def b_setBattle(self, battleId):
        self.battle = battleId
        self.d_setBattle(battleId)

    def d_setBattle(self, battleId):
        self.sendUpdate('setBattle', [battleId])

    def b_setBattleFinished(self):
        self.deactivate()
        self.setBattleFinished()
        self.d_setBattleFinished()

    def setBattleFinished(self):
        self.notify.debug('setBattleFinished: %s' % self.entId)
        messenger.send('battleBlockerFinished-' + str(self.entId))
        messenger.send(self.getOutputEventName(), [1])

    def d_setBattleFinished(self):
        self.sendUpdate('setBattleFinished', [])

    if __dev__:

        def attribChanged(self, *args):
            self.suitIds = []
            suits = self.level.planner.battleCellId2suits.get(self.cellId)
            if suits:
                for suit in suits:
                    self.suitIds.append(suit.doId)

            else:
                self.notify.warning("Couldn't find battle cell id %d in battleCellId2suits" % self.cellId)
            self.d_setSuits()
            self.registerBlocker()
