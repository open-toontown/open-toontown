from pandac.PandaModules import *
from direct.directnotify import DirectNotifyGlobal
from . import Quests
from toontown.toonbase import ToontownGlobals
from toontown.fishing import FishGlobals
from toontown.suit import SuitDNA
from toontown.racing import RaceGlobals
from toontown.estate import GardenGlobals
from toontown.golf import GolfGlobals

class QuestRewardCounter:
    notify = directNotify.newCategory('QuestRewardCounter')

    def __init__(self):
        self.reset()

    def reset(self):
        self.maxHp = 15
        self.maxCarry = 20
        self.maxMoney = 40
        self.questCarryLimit = 1
        self.teleportAccess = []
        self.trackAccess = [0,
         0,
         0,
         0,
         1,
         1,
         0]
        self.trackProgressId = -1
        self.trackProgress = 0

    def addTeleportAccess(self, zoneId):
        if zoneId not in self.teleportAccess:
            self.teleportAccess.append(zoneId)

    def addTrackAccess(self, track):
        self.trackAccess[track] = 1

    def addTrackProgress(self, trackId, progressIndex):
        if self.trackProgressId != trackId:
            self.notify.warning('tried to update progress on a track toon is not training')
        self.trackProgress = self.trackProgress | 1 << progressIndex

    def getTrackProgress(self):
        return (self.trackProgressId, self.trackProgress)

    def clearTrackProgress(self):
        self.trackProgressId = -1
        self.trackProgress = 0

    def setFromAvatar(self, av):
        rewardIds = []
        for q in av.quests:
            questId, fromNpcId, toNpcId, rewardId, toonProgress = q
            if rewardId == Quests.NA:
                rewardId = Quests.getFinalRewardId(questId, fAll=1)
            rewardIds.append(rewardId)

        self.notify.debug('Ignoring rewards: %s' % rewardIds)
        self.setRewardIndex(av.rewardTier, rewardIds, av.rewardHistory)
        fishHp = int(len(av.fishCollection) / FishGlobals.FISH_PER_BONUS)
        self.notify.debug('Adding %s hp for fish collection' % fishHp)
        self.maxHp += fishHp
        flowerHp = int(len(av.flowerCollection) / GardenGlobals.FLOWERS_PER_BONUS)
        self.notify.debug('Adding %s hp for fish collection' % flowerHp)
        self.maxHp += flowerHp
        HQdepts = (ToontownGlobals.cogHQZoneId2deptIndex(ToontownGlobals.SellbotHQ), ToontownGlobals.cogHQZoneId2deptIndex(ToontownGlobals.LawbotHQ), ToontownGlobals.cogHQZoneId2deptIndex(ToontownGlobals.CashbotHQ))
        levels = av.getCogLevels()
        cogTypes = av.getCogTypes()
        suitHp = 0
        for dept in HQdepts:
            level = levels[dept]
            type = cogTypes[dept]
            if type >= SuitDNA.suitsPerDept - 1:
                for milestoneLevel in ToontownGlobals.CogSuitHPLevels:
                    if level >= milestoneLevel:
                        suitHp += 1
                    else:
                        break

        self.notify.debug('Adding %s hp for cog suits' % suitHp)
        self.maxHp += suitHp
        kartingHp = int(av.kartingTrophies.count(1) / RaceGlobals.TrophiesPerCup)
        self.notify.debug('Adding %s hp for karting trophies' % kartingHp)
        self.maxHp += kartingHp
        golfHp = int(av.golfTrophies.count(True) / GolfGlobals.TrophiesPerCup)
        self.notify.debug('Adding %s hp for golf trophies' % golfHp)
        self.maxHp += golfHp

    def setRewardIndex(self, tier, rewardIds, rewardHistory):
        self.reset()
        for tierNum in range(tier):
            for rewardId in Quests.getRewardsInTier(tierNum):
                reward = Quests.getReward(rewardId)
                reward.countReward(self)
                self.notify.debug('Assigning reward %d' % rewardId)

        for rewardId in rewardHistory:
            if rewardId in Quests.getRewardsInTier(tier):
                if rewardIds.count(rewardId) != 0:
                    rewardIds.remove(rewardId)
                    self.notify.debug('Ignoring reward %d' % rewardId)
                else:
                    reward = Quests.getReward(rewardId)
                    reward.countReward(self)
                    self.notify.debug('Assigning reward %d' % rewardId)

        self.notify.debug('Remaining rewardIds %s' % rewardIds)
        self.maxHp = min(ToontownGlobals.MaxHpLimit, self.maxHp)

    def assignReward(self, rewardId, rewardIds):
        if rewardIds.count(rewardId) != 0:
            rewardIds.remove(rewardId)
            self.notify.debug('Ignoring reward %d' % rewardId)
        else:
            reward = Quests.getReward(rewardId)
            reward.countReward(self)
            self.notify.debug('Assigning reward %d' % rewardId)

    def fixAvatar(self, av):
        self.setFromAvatar(av)
        anyChanged = 0
        if self.maxHp != av.maxHp:
            self.notify.info('Changed avatar %d to have maxHp %d instead of %d' % (av.doId, self.maxHp, av.maxHp))
            av.b_setMaxHp(self.maxHp)
            anyChanged = 1
        if self.maxCarry != av.maxCarry:
            self.notify.info('Changed avatar %d to have maxCarry %d instead of %d' % (av.doId, self.maxCarry, av.maxCarry))
            av.b_setMaxCarry(self.maxCarry)
            anyChanged = 1
        if self.maxMoney != av.maxMoney:
            self.notify.info('Changed avatar %d to have maxMoney %d instead of %d' % (av.doId, self.maxMoney, av.maxMoney))
            av.b_setMaxMoney(self.maxMoney)
            anyChanged = 1
        if self.questCarryLimit != av.questCarryLimit:
            self.notify.info('Changed avatar %d to have questCarryLimit %d instead of %d' % (av.doId, self.questCarryLimit, av.questCarryLimit))
            av.b_setQuestCarryLimit(self.questCarryLimit)
            anyChanged = 1
        if self.teleportAccess != av.teleportZoneArray:
            self.notify.info('Changed avatar %d to have teleportAccess %s instead of %s' % (av.doId, self.teleportAccess, av.teleportZoneArray))
            av.b_setTeleportAccess(self.teleportAccess)
            anyChanged = 1
        if self.trackAccess != av.trackArray:
            self.notify.info('Changed avatar %d to have trackAccess %s instead of %s' % (av.doId, self.trackAccess, av.trackArray))
            av.b_setTrackAccess(self.trackAccess)
            anyChanged = 1
        if av.fixTrackAccess():
            anyChanged = 1
        return anyChanged
