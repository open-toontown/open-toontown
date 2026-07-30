from toontown.toonbase import ToontownGlobals
from toontown.coghq import DistributedLevelBattleAI
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import State
from direct.fsm import ClassicFSM, State
from toontown.battle.BattleBase import *
from . import CogDisguiseGlobals
from toontown.toonbase.ToontownBattleGlobals import getStageCreditMultiplier
from direct.showbase.PythonUtil import addListsByValue
from otp.otpbase.PythonUtil import enumerate

class DistributedStageBattleAI(DistributedLevelBattleAI.DistributedLevelBattleAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedStageBattleAI')

    def __init__(self, air, battleMgr, pos, suit, toonId, zoneId, level, battleCellId, roundCallback=None, finishCallback=None, maxSuits=4):
        DistributedLevelBattleAI.DistributedLevelBattleAI.__init__(self, air, battleMgr, pos, suit, toonId, zoneId, level, battleCellId, 'StageReward', roundCallback, finishCallback, maxSuits)
        self.battleCalc.setSkillCreditMultiplier(1)
        if self.bossBattle:
            self.level.d_setBossConfronted(toonId)
        self.fsm.addState(State.State('StageReward', self.enterStageReward, self.exitStageReward, [
         'Resume']))
        playMovieState = self.fsm.getStateNamed('PlayMovie')
        playMovieState.addTransition('StageReward')

    def getTaskZoneId(self):
        return self.level.stageId

    def storeSuitsKilledThisBattle(self):
        floor = self.level.getFloorNum()
        if len(self.suitsKilledPerFloor) < floor + 1:
            self.suitsKilledPerFloor.append(self.suitsKilledThisBattle)
        else:
            self.suitsKilledPerFloor[floor].extend(self.suitsKilledThisBattle)

    def handleToonsWon(self, toons):
        extraMerits = [
         0, 0, 0, 0]
        amount = ToontownGlobals.StageNoticeRewards[self.level.stageId]
        index = ToontownGlobals.cogHQZoneId2deptIndex(self.level.stageId)
        extraMerits[index] = amount
        for toon in toons:
            mult = 1.0
            meritArray = self.air.promotionMgr.recoverMerits(toon, [], self.getTaskZoneId(), mult, extraMerits=extraMerits)
            if toon.doId in self.helpfulToons:
                self.toonMerits[toon.doId] = addListsByValue(self.toonMerits[toon.doId], meritArray)
            else:
                self.notify.debug('toon %d not helpful list, skipping merits' % toon.doId)

        for floorNum, cogsThisFloor in enumerate(self.suitsKilledPerFloor):
            self.notify.info('merits for floor %s' % floorNum)
            for toon in toons:
                recovered, notRecovered = self.air.questManager.recoverItems(toon, cogsThisFloor, self.getTaskZoneId())
                self.toonItems[toon.doId][0].extend(recovered)
                self.toonItems[toon.doId][1].extend(notRecovered)
                meritArray = self.air.promotionMgr.recoverMerits(toon, cogsThisFloor, self.getTaskZoneId(), getStageCreditMultiplier(floorNum))
                self.notify.info('toon %s: %s' % (toon.doId, meritArray))
                if toon.doId in self.helpfulToons:
                    self.toonMerits[toon.doId] = addListsByValue(self.toonMerits[toon.doId], meritArray)
                else:
                    self.notify.debug('toon %d not helpful list, skipping merits' % toon.doId)

    def enterStageReward(self):
        self.joinableFsm.request('Unjoinable')
        self.runableFsm.request('Unrunable')
        self.resetResponses()
        self.assignRewards()
        self.bossDefeated = 1
        self.level.setVictors(self.activeToons[:])
        self.timer.startCallback(BUILDING_REWARD_TIMEOUT, self.serverRewardDone)
        return None

    def exitStageReward(self):
        return None

    def enterResume(self):
        DistributedLevelBattleAI.DistributedLevelBattleAI.enterResume(self)
        if self.bossBattle and self.bossDefeated:
            self.battleMgr.level.b_setDefeated()
