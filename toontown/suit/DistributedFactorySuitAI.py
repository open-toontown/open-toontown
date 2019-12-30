from otp.ai.AIBaseGlobal import *
from direct.directnotify import DirectNotifyGlobal
from toontown.battle import SuitBattleGlobals
from . import DistributedSuitBaseAI, SuitDialog
from direct.showbase.PythonUtil import StackTrace

class DistributedFactorySuitAI(DistributedSuitBaseAI.DistributedSuitBaseAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedFactorySuitAI')

    def __init__(self, air, suitPlanner):
        DistributedSuitBaseAI.DistributedSuitBaseAI.__init__(self, air, suitPlanner)
        self.blocker = None
        self.battleCellIndex = None
        self.chasing = 0
        self.factoryGone = 0
        return

    def factoryIsGoingDown(self):
        self.factoryGone = 1

    def delete(self):
        if not self.factoryGone:
            try:
                self.setBattleCellIndex(None)
            except Exception as e:
                simbase.air.writeServerEvent('avoid_crash', self.doId, 'DistributedFactorySuitAI.delete, factoryIsNotGone, got Exception %s' % str(e))
                self.notify.warning('delete, factoryIsNotGone, got Exception %s' % str(e))
                self.notify.warning('stackTrace=%s' % StackTrace().compact())
                self.notify.warning('doId=%s' % self.doId)
                if hasattr(self, 'levelDoId'):
                    self.notify.warning('levelDoId=%s' % self.levelDoId)
                else:
                    self.notify.warning('no levelDoId')

        del self.blocker
        self.ignoreAll()
        DistributedSuitBaseAI.DistributedSuitBaseAI.delete(self)
        return

    def setLevelDoId(self, levelDoId):
        self.levelDoId = levelDoId

    def getLevelDoId(self):
        return self.levelDoId

    def setCogId(self, cogId):
        self.cogId = cogId

    def getCogId(self):
        return self.cogId

    def setReserve(self, reserve):
        self.reserve = reserve

    def getReserve(self):
        return self.reserve

    def requestBattle(self, x, y, z, h, p, r):
        toonId = self.air.getAvatarIdFromSender()
        if self.notify.getDebug():
            self.notify.debug(str(self.getDoId()) + str(self.zoneId) + ': request battle with toon: %d' % toonId)
        self.confrontPos = Point3(x, y, z)
        self.confrontHpr = Vec3(h, p, r)
        if self.sp.requestBattle(self, toonId):
            if self.notify.getDebug():
                self.notify.debug('Suit %d requesting battle in zone %d with toon %d' % (self.getDoId(), self.zoneId, toonId))
        else:
            if self.notify.getDebug():
                self.notify.debug('requestBattle from suit %d, toon %d- denied by battle manager' % (toonId, self.getDoId()))
            self.b_setBrushOff(SuitDialog.getBrushOffIndex(self.getStyleName()))
            self.d_denyBattle(toonId)

    def getConfrontPosHpr(self):
        return (
         self.confrontPos, self.confrontHpr)

    def setBattleCellIndex(self, battleCellIndex):
        self.sp.suitBattleCellChange(self, oldCell=self.battleCellIndex, newCell=battleCellIndex)
        self.battleCellIndex = battleCellIndex
        self.attachBattleBlocker()
        self.accept(self.sp.getBattleBlockerEvent(self.battleCellIndex), self.attachBattleBlocker)

    def getBattleCellIndex(self):
        return self.battleCellIndex

    def attachBattleBlocker(self):
        blocker = self.sp.battleMgr.battleBlockers.get(self.battleCellIndex)
        self.blocker = blocker

    def setAlert(self, avId):
        if avId == self.air.getAvatarIdFromSender():
            av = self.air.doId2do.get(avId)
            if av:
                self.chasing = avId
                if self.sp.battleMgr.cellHasBattle(self.battleCellIndex):
                    pass
                else:
                    self.sendUpdate('setConfrontToon', [avId])

    def setStrayed(self):
        if self.chasing > 0:
            self.chasing = 0
            self.sendUpdate('setReturn', [])

    def resume(self):
        self.notify.debug('Suit %s resume' % self.doId)
        if self.currHP <= 0:
            messenger.send(self.getDeathEvent())
            self.notify.debug('Suit %s dead after resume' % self.doId)
            self.requestRemoval()
        else:
            self.sendUpdate('setReturn', [])
        return None

    def isForeman(self):
        return self.boss

    def setVirtual(self, isVirtual=1):
        self.virtual = isVirtual

    def getVirtual(self):
        return self.virtual
