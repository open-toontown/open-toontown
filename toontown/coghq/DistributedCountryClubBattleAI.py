from toontown.toonbase import ToontownGlobals
from toontown.coghq import DistributedLevelBattleAI
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import State
from direct.fsm import ClassicFSM, State
from toontown.battle.BattleBase import *
from . import CogDisguiseGlobals
from toontown.toonbase.ToontownBattleGlobals import getCountryClubCreditMultiplier
from direct.showbase.PythonUtil import addListsByValue

class DistributedCountryClubBattleAI(DistributedLevelBattleAI.DistributedLevelBattleAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedCountryClubBattleAI')

    def __init__(self, air, battleMgr, pos, suit, toonId, zoneId, level, battleCellId, roundCallback=None, finishCallback=None, maxSuits=4):
        DistributedLevelBattleAI.DistributedLevelBattleAI.__init__(self, air, battleMgr, pos, suit, toonId, zoneId, level, battleCellId, 'CountryClubReward', roundCallback, finishCallback, maxSuits)
        self.battleCalc.setSkillCreditMultiplier(1)
        if self.bossBattle:
            self.level.d_setBossConfronted(toonId)
        self.fsm.addState(State.State('CountryClubReward', self.enterCountryClubReward, self.exitCountryClubReward, [
         'Resume']))
        playMovieState = self.fsm.getStateNamed('PlayMovie')
        playMovieState.addTransition('CountryClubReward')

    def getTaskZoneId(self):
        return self.level.countryClubId

    def handleToonsWon(self, toons):
        extraMerits = [
         0, 0, 0, 0]
        amount = ToontownGlobals.CountryClubCogBuckRewards[self.level.countryClubId]
        index = ToontownGlobals.cogHQZoneId2deptIndex(self.level.countryClubId)
        extraMerits[index] = amount
        for toon in toons:
            recovered, notRecovered = self.air.questManager.recoverItems(toon, self.suitsKilled, self.getTaskZoneId())
            self.toonItems[toon.doId][0].extend(recovered)
            self.toonItems[toon.doId][1].extend(notRecovered)
            meritArray = self.air.promotionMgr.recoverMerits(toon, self.suitsKilled, self.getTaskZoneId(), getCountryClubCreditMultiplier(self.getTaskZoneId()), extraMerits=extraMerits)
            if toon.doId in self.helpfulToons:
                self.toonMerits[toon.doId] = addListsByValue(self.toonMerits[toon.doId], meritArray)
            else:
                self.notify.debug('toon %d not helpful list, skipping merits' % toon.doId)

    def enterCountryClubReward(self):
        self.joinableFsm.request('Unjoinable')
        self.runableFsm.request('Unrunable')
        self.resetResponses()
        self.assignRewards()
        self.bossDefeated = 1
        self.level.setVictors(self.activeToons[:])
        self.timer.startCallback(BUILDING_REWARD_TIMEOUT, self.serverRewardDone)
        return None

    def exitCountryClubReward(self):
        return None

    def enterResume(self):
        DistributedLevelBattleAI.DistributedLevelBattleAI.enterResume(self)
        if self.bossBattle and self.bossDefeated:
            self.battleMgr.level.b_setDefeated()

    def enterReward(self):
        DistributedLevelBattleAI.DistributedLevelBattleAI.enterReward(self)
        roomDoId = self.getLevelDoId()
        room = simbase.air.doId2do.get(roomDoId)
        if room:
            room.challengeDefeated()
