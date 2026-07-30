from toontown.toonbase import ToontownGlobals
from toontown.coghq import DistributedLevelBattleAI
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import State
from direct.fsm import ClassicFSM, State
from toontown.battle.BattleBase import *
from . import CogDisguiseGlobals
from toontown.toonbase.ToontownBattleGlobals import getMintCreditMultiplier
from direct.showbase.PythonUtil import addListsByValue

class DistributedMintBattleAI(DistributedLevelBattleAI.DistributedLevelBattleAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedMintBattleAI')

    def __init__(self, air, battleMgr, pos, suit, toonId, zoneId, level, battleCellId, roundCallback=None, finishCallback=None, maxSuits=4):
        DistributedLevelBattleAI.DistributedLevelBattleAI.__init__(self, air, battleMgr, pos, suit, toonId, zoneId, level, battleCellId, 'MintReward', roundCallback, finishCallback, maxSuits)
        self.battleCalc.setSkillCreditMultiplier(1)
        if self.bossBattle:
            self.level.d_setBossConfronted(toonId)
        self.fsm.addState(State.State('MintReward', self.enterMintReward, self.exitMintReward, [
         'Resume']))
        playMovieState = self.fsm.getStateNamed('PlayMovie')
        playMovieState.addTransition('MintReward')

    def getTaskZoneId(self):
        return self.level.mintId

    def handleToonsWon(self, toons):
        extraMerits = [
         0, 0, 0, 0]
        amount = ToontownGlobals.MintCogBuckRewards[self.level.mintId]
        index = ToontownGlobals.cogHQZoneId2deptIndex(self.level.mintId)
        extraMerits[index] = amount
        for toon in toons:
            recovered, notRecovered = self.air.questManager.recoverItems(toon, self.suitsKilled, self.getTaskZoneId())
            self.toonItems[toon.doId][0].extend(recovered)
            self.toonItems[toon.doId][1].extend(notRecovered)
            meritArray = self.air.promotionMgr.recoverMerits(toon, self.suitsKilled, self.getTaskZoneId(), getMintCreditMultiplier(self.getTaskZoneId()), extraMerits=extraMerits)
            if toon.doId in self.helpfulToons:
                self.toonMerits[toon.doId] = addListsByValue(self.toonMerits[toon.doId], meritArray)
            else:
                self.notify.debug('toon %d not helpful list, skipping merits' % toon.doId)

    def enterMintReward(self):
        self.joinableFsm.request('Unjoinable')
        self.runableFsm.request('Unrunable')
        self.resetResponses()
        self.assignRewards()
        self.bossDefeated = 1
        self.level.setVictors(self.activeToons[:])
        self.timer.startCallback(BUILDING_REWARD_TIMEOUT, self.serverRewardDone)
        return None

    def exitMintReward(self):
        return None

    def enterResume(self):
        DistributedLevelBattleAI.DistributedLevelBattleAI.enterResume(self)
        if self.bossBattle and self.bossDefeated:
            self.battleMgr.level.b_setDefeated()
