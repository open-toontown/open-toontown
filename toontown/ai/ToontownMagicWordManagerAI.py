# python imports
import string
import time
import random
import datetime

# panda3d imports
from pandac.PandaModules import *
from direct.showbase import PythonUtil
from direct.task import Task

# toontown imports
from otp.ai.AIBaseGlobal import *
from otp.ai.AIZoneData import AIZoneData
from direct.distributed import DistributedObjectAI
from direct.directnotify import DirectNotifyGlobal
from toontown.toon import InventoryBase
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import ToontownBattleGlobals
from toontown.suit import DistributedSuitPlannerAI
from toontown.battle import DistributedBattleBaseAI
from toontown.toon import DistributedToonAI
from . import WelcomeValleyManagerAI
from toontown.hood import ZoneUtil
from toontown.battle import SuitBattleGlobals
from toontown.quest import Quests
from toontown.minigame import MinigameCreatorAI
from toontown.estate import DistributedPhoneAI
from toontown.suit import DistributedBossCogAI
from toontown.suit import DistributedSellbotBossAI
from toontown.suit import DistributedCashbotBossAI
from toontown.suit import DistributedLawbotBossAI
from toontown.suit import DistributedBossbotBossAI
from toontown.catalog import CatalogItemList
from toontown.pets import PetTricks
from toontown.suit import SuitDNA
from toontown.toon import ToonDNA
from toontown.toonbase import TTLocalizer
from otp.ai import MagicWordManagerAI
from toontown.estate import GardenGlobals
from otp.otpbase import OTPGlobals
from toontown.golf import GolfManagerAI
from toontown.golf import GolfGlobals
from toontown.parties import PartyGlobals
from toontown.parties import PartyUtils
from toontown.uberdog.DataStoreAIClient import DataStoreAIClient
from toontown.uberdog import DataStoreGlobals

if (simbase.wantKarts):
    from toontown.racing.KartDNA import *

class ToontownMagicWordManagerAI(MagicWordManagerAI.MagicWordManagerAI):
    notify = DirectNotifyGlobal.directNotify.newCategory("ToontownMagicWordManagerAI")

    GameAvatarClass = DistributedToonAI.DistributedToonAI

    # is it a safezone?
    Str2szId = {
        'ttc': ToontownGlobals.ToontownCentral,
        'tt':  ToontownGlobals.ToontownCentral,
        'tc':  ToontownGlobals.ToontownCentral,
        'dd':  ToontownGlobals.DonaldsDock,
        'dg':  ToontownGlobals.DaisyGardens,
        'mml': ToontownGlobals.MinniesMelodyland,
        'mm':  ToontownGlobals.MinniesMelodyland,
        'br':  ToontownGlobals.TheBrrrgh,
        'ddl': ToontownGlobals.DonaldsDreamland,
        'dl':  ToontownGlobals.DonaldsDreamland,
        }


    def __init__(self, air):
        MagicWordManagerAI.MagicWordManagerAI.__init__(self, air)
        self.__bossBattleZoneId = [None, None, None, None]
        self.__bossCog = [None, None, None, None]

    def doMagicWord(self, word, av, zoneId, senderId):
        def wordIs(w, word=word):
            return word[:(len(w)+1)] == ('%s ' % w) or word == w

        if (MagicWordManagerAI.MagicWordManagerAI.doMagicWord(self, word, av,
                                                zoneId, senderId) == 1):
            pass
        elif word == "~allstuff":
            av.inventory.maxOutInv()
            av.d_setInventory(av.inventory.makeNetString())
            self.notify.debug("Maxing out inventory for " + av.name)
        elif word == "~nostuff":
            av.inventory.zeroInv(1)
            av.d_setInventory(av.inventory.makeNetString())
            self.notify.debug("Zeroing inventory for " + av.name)
        elif word == "~restock":
            av.doRestock(1)
        elif word == "~restockUber":
            av.doRestock(0)
                
        elif word == "~rich":
            av.b_setMoney(av.maxMoney)
            av.b_setBankMoney(av.maxBankMoney)
            self.notify.debug(av.name + " is now rich")
        elif word == "~poor":
            av.b_setMoney(0)
            av.b_setBankMoney(0)
            self.notify.debug(av.name + " is now poor")
        elif wordIs("~jelly"):
            args = word.split()
            if len(args) > 1:
                count = int(args[1])
                # this will just fill up the pocketbook,
                # but wont add to the bank
                av.b_setMoney(min(count, av.getMaxMoney()))
            else:
                av.b_setMoney(av.getMaxMoney())
        elif wordIs("~bank"):
            args = word.split()
            if len(args) > 1:
                count = int(args[1])
                av.b_setBankMoney(count)
            else:
                av.b_setBankMoney(av.getMaxBankMoney())
        elif wordIs("~maxBankMoney"):
            args = word.split()
            if len(args) > 1:
                count = int(args[1])
                av.b_setMaxBankMoney(count)
                response = "Max bank money set to %s" % (av.getMaxBankMoney())
                self.down_setMagicWordResponse(senderId, response)
            else:
                response = "Max bank money is %s" % (av.getMaxBankMoney())
                self.down_setMagicWordResponse(senderId, response)

        elif wordIs("~pie"):
            # Give ourselves a pie.  Or four.
            count = 0
            type = None
            args = word.split()
            if len(args) == 1:
                count = 1
            for arg in args[1:]:
                from toontown.toonbase import ToontownBattleGlobals
                if arg in ToontownBattleGlobals.pieNames:
                    type = ToontownBattleGlobals.pieNames.index(arg)
                else:
                    try:
                        count = int(arg)
                    except:
                        response = "Invalid pie argument: %s" % (arg)
                        self.down_setMagicWordResponse(senderId, response)
                        return

            if type != None:
                av.b_setPieType(type)
            av.b_setNumPies(av.numPies + count)

        elif word == "~amateur":
            av.b_setTrackAccess([0, 0, 0, 0, 1, 1, 0])
            av.b_setMaxCarry(20)
            av.b_setQuestCarryLimit(1)
            av.experience.zeroOutExp()
            av.d_setExperience(av.experience.makeNetString())
            av.b_setMaxHp(15)
            av.b_setHp(15)
            newInv = InventoryBase.InventoryBase(av)
            newInv.maxOutInv()
            av.inventory.setToMin(newInv.inventory)
            av.d_setInventory(av.inventory.makeNetString())
            self.notify.debug("Default exp for " + av.name)
        elif word == "~amateur+":
            av.experience.setAllExp(9)
            av.d_setExperience(av.experience.makeNetString())
            av.b_setMaxHp(30)
            av.b_setHp(30)
            # make sure we're not over maxProps too
            newInv = InventoryBase.InventoryBase(av)
            newInv.maxOutInv()
            av.inventory.setToMin(newInv.inventory)
            av.d_setInventory(av.inventory.makeNetString())
            self.notify.debug("Setting exp to 9 for " + av.name)                
        elif word == "~professional":
            av.b_setTrackAccess([1, 1, 1, 1, 1, 1, 1])
            av.b_setMaxCarry(ToontownGlobals.MaxCarryLimit)
            av.b_setQuestCarryLimit(ToontownGlobals.MaxQuestCarryLimit)
            av.experience.maxOutExp()
            av.d_setExperience(av.experience.makeNetString())
            av.b_setMaxHp(ToontownGlobals.MaxHpLimit)
            av.b_setHp(ToontownGlobals.MaxHpLimit)
            self.notify.debug("Max exp for " + av.name)
        elif word == "~professional--":
            av.b_setTrackAccess([1, 1, 1, 1, 1, 1, 1])
            av.b_setMaxCarry(ToontownGlobals.MaxCarryLimit)
            av.b_setQuestCarryLimit(ToontownGlobals.MaxQuestCarryLimit)
            av.experience.makeExpHigh()
            av.d_setExperience(av.experience.makeNetString())
            av.b_setMaxHp(ToontownGlobals.MaxHpLimit-15)
            av.b_setHp(ToontownGlobals.MaxHpLimit-15)
            self.notify.debug("High exp for " + av.name)
        elif word == "~regularToon":
            pickTrack = ([1, 1, 1, 1, 1, 1, 0],
                           [1, 1, 1, 0, 1, 1, 1],
                           [0, 1, 1, 1, 1, 1, 1],
                           [1, 0, 1, 1, 1, 1, 1])
            av.b_setTrackAccess(random.choice(pickTrack))
            av.b_setMaxCarry(ToontownGlobals.MaxCarryLimit)
            av.b_setQuestCarryLimit(ToontownGlobals.MaxQuestCarryLimit)
            av.experience.makeExpRegular()
            av.d_setExperience(av.experience.makeNetString())
            laughminus = int(random.random() * 20.0) + 10.0
            av.b_setMaxHp(ToontownGlobals.MaxHpLimit-laughminus)
            av.b_setHp(ToontownGlobals.MaxHpLimit-laughminus)
            self.notify.debug("regular exp for " + av.name)
        elif word == "~maxexp--":
            av.b_setTrackAccess([1, 1, 1, 1, 1, 1, 1])
            av.b_setMaxCarry(ToontownGlobals.MaxCarryLimit)
            av.b_setQuestCarryLimit(ToontownGlobals.MaxQuestCarryLimit)
            av.experience.maxOutExpMinusOne()
            av.d_setExperience(av.experience.makeNetString())
            av.b_setMaxHp(ToontownGlobals.MaxHpLimit)
            av.b_setHp(ToontownGlobals.MaxHpLimit)
            self.notify.debug("Max exp-- for " + av.name)
        elif wordIs('~mintRaider'):
            av.experience.maxOutExp()
            av.d_setExperience(av.experience.makeNetString())
            av.b_setQuestHistory([])
            av.b_setRewardHistory(Quests.DL_TIER+2, [])
            av.fixAvatar()
            # 7LP for fishing, + 5LP for SellbotHQ, /2
            av.b_setMaxHp(av.getMaxHp()+6)
            av.b_setHp(av.getMaxHp())
            trackAccess = [1, 1, 1, 1, 1, 1, 1]
            trackAccess[random.choice((0, 1, 2, 3, 6))] = 0
            av.b_setTrackAccess(trackAccess)

        elif word[:4] == "~exp":
            self.doExp(word, av, zoneId, senderId)
            
        elif word[:7] == "~trophy":
            self.doTrophy(word, av, zoneId, senderId)

        elif word == "~trophies":
            # Report the top 10 trophy holders.
            scores = self.air.trophyMgr.getSortedScores()
            response = ''
            for i in range(min(len(scores), 10)):
                score, avId = scores[i]
                av = self.air.doId2do.get(avId, None)
                if av:
                    avName = av.name
                else:
                    avName = avId
                response += '%s %s\n' % (score, avName)

            self.down_setMagicWordResponse(senderId, response)

        elif word[:8] == "~effect ":
            # Apply a cheesy rendering effect.
            self.doCheesyEffect(word, av, zoneId, senderId)

        elif word[:12] == "~cogTakeOver":
            self.doCogTakeOver(word, av, zoneId, senderId)

        elif wordIs("~cogdoTakeOver"):
            if simbase.air.wantCogdominiums:
                self.doCogdoTakeOver(word, av, zoneId, senderId)

        elif word[:13] == "~toonTakeOver":
            self.doToonTakeOver(word, av, zoneId, senderId)

        elif word[:8] == "~welcome":
            self.doWelcome(word, av, zoneId, senderId)

        elif word == "~finishTutorial":
            av.b_setTutorialAck(1)
            av.b_setQuests([])
            av.b_setQuestHistory([])
            av.b_setRewardHistory(2, [])
            av.fixAvatar()
            self.down_setMagicWordResponse(senderId, "Finished tutorial.")
                    
        elif word == "~finishQuests":
            self.air.questManager.completeAllQuestsMagically(av)
            self.down_setMagicWordResponse(senderId, "Finished quests.")

        elif word[:12] == "~finishQuest":
            args = word.split()
            index = int(args[1])
            result = self.air.questManager.completeQuestMagically(av, index)
            if result:
                self.down_setMagicWordResponse(senderId, ("Finished quest %s." % (index)))
            else:
                self.down_setMagicWordResponse(senderId, ("Quest %s not found." % (index)))

        elif word == "~clearQuests":
            # Reset all quest fields as if this were a new toon
            av.b_setQuests([])
            av.b_setQuestHistory([])
            currentTier = av.getRewardTier()
            av.b_setRewardHistory(currentTier, [])
            self.down_setMagicWordResponse(senderId, "Cleared quests.")

        elif word == "~getQuestTier":
            # Report the current quest tier
            response = "tier %d" % (av.getRewardTier())
            self.down_setMagicWordResponse(senderId, response)

        elif word[:13] == "~setQuestTier":
            # Sets reward tier and optionally index
            args = word.split()
            tier = int(args[1])
            tier = min(tier, Quests.getNumTiers())
            av.b_setQuestHistory([])
            av.b_setRewardHistory(tier, [])
            av.fixAvatar()

        elif word[:12] == "~assignQuest":
            # Intelligently assigns a quest
            args = word.split()
            questId = int(args[1])

            # Make sure this quest exists
            questDesc = Quests.QuestDict.get(questId)
            if questDesc is None:
                self.down_setMagicWordResponse(senderId, "Quest %s not found" % (questId))
                return

            # Make sure the av is in that tier
            avTier = av.getRewardTier()
            tier = questDesc[Quests.QuestDictTierIndex]
            if tier != avTier:
                self.down_setMagicWordResponse(senderId, "Avatar not in that tier: %s. You can ~setQuestTier %s, if you want." % (tier, tier))
                return

            # Make sure the av has room for this quest
            if not self.air.questManager.needsQuest(av):
                self.down_setMagicWordResponse(senderId, "Quests are already full")
                return

            # Make sure the av does not already have this quest
            for questDesc in av.quests:
                if questId == questDesc[0]:
                    self.down_setMagicWordResponse(senderId, "Already has quest: %s" % (questId))
                    return

            # Should we check your reward history too?
            
            fromNpcId = Quests.ToonHQ # A reasonable default

            rewardId = Quests.getQuestReward(questId, av)
            # Some quests do not have a reward specified. Instead they have
            # the keyword <Any> which tells the quest system to try to
            # match something up. In our case, we are not going through
            # normal channels, so just pick some reward so things do not
            # crash. How about some jellybeans?
            if rewardId == Quests.Any:
                # Just give 100 jellybeans (rewardId = 604 from Quests.py)
                rewardId = 604
                
            toNpcId = Quests.getQuestToNpcId(questId)
            # Account for some trickery in the quest description
            # If the toNpcId is marked <Any> or <Same> let's just use ToonHQ
            if toNpcId == Quests.Any:
                toNpcId = Quests.ToonHQ
            elif toNpcId == Quests.Same:
                toNpcId = Quests.ToonHQ
            
            startingQuest = Quests.isStartingQuest(questId)
            self.air.questManager.assignQuest(av.doId,
                                              fromNpcId,
                                              questId,
                                              rewardId,
                                              toNpcId,
                                              startingQuest,
                                              )
            self.down_setMagicWordResponse(senderId, "Quest %s assigned" % (questId))

        elif wordIs("~nextQuest"):
            # forces NPCs to offer you a particular quest
            args = word.split()
            if len(args) == 1:
                # clear any existing request
                questId = self.air.questManager.cancelNextQuest(av.doId)
                if questId:
                    self.down_setMagicWordResponse(
                        senderId, "Cancelled request for quest %s" % (questId))
                return
            
            questId = int(args[1])

            # Make sure this quest exists
            questDesc = Quests.QuestDict.get(questId)
            if questDesc is None:
                self.down_setMagicWordResponse(
                    senderId, "Quest %s not found" % (questId))
                return

            # Make sure the av is in that tier
            avTier = av.getRewardTier()
            tier = questDesc[Quests.QuestDictTierIndex]
            if tier != avTier:
                self.down_setMagicWordResponse(senderId, "Avatar not in that tier: %s. You can ~setQuestTier %s, if you want." % (tier, tier))
                return

            # Make sure the av does not already have this quest
            for questDesc in av.quests:
                if questId == questDesc[0]:
                    self.down_setMagicWordResponse(
                        senderId, "Already has quest: %s" % (questId))
                    return

            self.air.questManager.setNextQuest(av.doId, questId)
            self.down_setMagicWordResponse(senderId,
                                           "Quest %s queued" % (questId))

        elif word == "~visitHQ":
            # Sets quests to return to HQ Officer instead of whomever.
            # Saves walking all over the map to test quests.
            for quest in av.quests:
                quest[2] = Quests.ToonHQ
            av.b_setQuests(av.quests)
            
        elif wordIs('~teleportAll'):
            av.b_setHoodsVisited(ToontownGlobals.HoodsForTeleportAll)
            av.b_setTeleportAccess(ToontownGlobals.HoodsForTeleportAll)
            
        elif word[:10] == "~buildings":
            self.doBuildings(word, av, zoneId, senderId)

        elif word[:16] == "~buildingPercent":
            self.doBuildingPercent(word, av, zoneId, senderId)

        elif wordIs('~call'):
            self.doCall(word, av, zoneId, senderId)

        elif wordIs('~battle'):
            self.doBattle(word, av, zoneId, senderId)

        elif word[:5] == "~cogs":
            self.doCogs(word, av, zoneId, senderId)

        # Suit Invasions
        elif word[:12] == "~getInvasion":
            self.getCogInvasion(word, av, zoneId, senderId)
        elif word[:14] == "~startInvasion":
            self.doCogInvasion(word, av, zoneId, senderId)
        elif word[:13] == "~stopInvasion":
            self.stopCogInvasion(word, av, zoneId, senderId)

        # Fireworks
        elif word[:18] == "~startAllFireworks":
            self.startAllFireworks(word, av, zoneId, senderId)
        elif word[:15] == "~startFireworks":
            self.startFireworks(word, av, zoneId, senderId)
        elif word[:14] == "~stopFireworks":
            self.stopFireworks(word, av, zoneId, senderId)
        elif word[:17] == "~stopAllFireworks":
            self.stopAllFireworks(word, av, zoneId, senderId)

        elif word == "~save":
            # Save the AI state.  Presently, this is just the set of
            # buildings.
            self.air.saveBuildings()

            response = "Building state saved."
            self.down_setMagicWordResponse(senderId, response)

        elif word[:9] == "~minigame":
            self.doMinigame(word, av, zoneId, senderId)

        elif wordIs('~factory'):
            # select which factory to enter
            # AI-global for now
            from toontown.coghq import FactoryManagerAI
            args = word.split()
            if len(args) == 1:
                # no arguments given
                if FactoryManagerAI.FactoryManagerAI.factoryId is None:
                    self.down_setMagicWordResponse(
                        senderId, "usage: ~factory [id]")
                else:
                    fId = FactoryManagerAI.FactoryManagerAI.factoryId
                    FactoryManagerAI.FactoryManagerAI.factoryId = None
                    self.down_setMagicWordResponse(
                        senderId, "cancelled request for factory %s" % fId)
            else:
                factoryId = int(args[1])
                if not factoryId in ToontownGlobals.factoryId2factoryType:
                    self.down_setMagicWordResponse(
                        senderId,
                        "unknown factory '%s'" % factoryId)
                else:
                    FactoryManagerAI.FactoryManagerAI.factoryId = factoryId
                    self.down_setMagicWordResponse(
                        senderId,
                        "selected factory %s" % factoryId)

        elif wordIs('~mintId'):
            args = word.split()
            postName = 'mintId-%s' % av.doId
            if len(args) < 2:
                if bboard.has(postName):
                    bboard.remove(postName)
                    response = 'cleared mint request'
                else:
                    response = '~mintId id'
            else:
                try:
                    id = int(args[1])
                    # make sure it's a valid id
                    foo = ToontownGlobals.MintNumRooms[id]
                except:
                    response = 'bad mint id: %s' % args[1]
                else:
                    bboard.post(postName, id)
                    response = 'selected mint %s' % id
            self.down_setMagicWordResponse(senderId, response)
            
        elif wordIs('~mintFloor'):
            args = word.split()
            postName = 'mintFloor-%s' % av.doId
            if len(args) < 2:
                if bboard.has(postName):
                    bboard.remove(postName)
                    response = 'cleared mint floor request'
                else:
                    response = '~mintFloor num'
            else:
                try:
                    floor = int(args[1])
                except:
                    response = 'bad floor index: %s' % args[1]
                else:
                    bboard.post(postName, floor)
                    response = 'selected floor %s' % floor
            self.down_setMagicWordResponse(senderId, response)

        elif wordIs('~mintRoom'):
            args = word.split()
            postName = 'mintRoom-%s' % av.doId
            if len(args) < 2:
                if bboard.has(postName):
                    bboard.remove(postName)
                    response = 'cleared mint room request'
                else:
                    response = '~mintRoom <id|name>'
            else:
                from toontown.coghq import MintRoomSpecs
                id = None
                name = None
                try:
                    id = int(args[1])
                    name = MintRoomSpecs.CashbotMintRoomId2RoomName[id]
                except:
                    if args[1] in MintRoomSpecs.CashbotMintRoomName2RoomId:
                        name = args[1]
                        id = MintRoomSpecs.CashbotMintRoomName2RoomId[name]
                    else:
                        response = 'invalid room: %s' % args[1]
                bboard.post(postName, id)
                response = 'selected mint room %s: %s' % (id, name)
            self.down_setMagicWordResponse(senderId, response)
            
        elif wordIs('~stageRoom'):
            args = word.split()
            postName = 'stageRoom-%s' % av.doId
            if len(args) < 2:
                if bboard.has(postName):
                    bboard.remove(postName)
                    response = 'cleared stage room request'
                else:
                    response = '~stageRoom <id|name>'
            else:
                from toontown.coghq import StageRoomSpecs
                id = None
                name = None
                try:
                    id = int(args[1])
                    name = StageRoomSpecs.CashbotStageRoomId2RoomName[id]
                except:
                    if args[1] in StageRoomSpecs.CashbotStageRoomName2RoomId:
                        name = args[1]
                        id = StageRoomSpecs.CashbotStageRoomName2RoomId[name]
                    else:
                        response = 'invalid room: %s' % args[1]
                bboard.post(postName, id)
                response = 'selected stage room %s: %s' % (id, name)
            self.down_setMagicWordResponse(senderId, response)
            
        elif wordIs("~autoRestock"):
            args = word.split()
            postName = 'autoRestock-%s' % av.doId
            enable = not bboard.get(postName, 0)
            # are they explicitly setting the state?
            if len(args) > 1:
                try:
                    enable = int(args[1])
                except:
                    self.down_setMagicWordResponse(senderId,
                                                   'invalid state flag: %s' %
                                                   args[1])
                    return
            if enable:
                state = 'ON'
                bboard.post(postName, 1)
            else:
                state = 'OFF'
                bboard.remove(postName)
            self.down_setMagicWordResponse(senderId, 'autoRestock %s' % state)
        
        elif wordIs("~resistanceRestock"):
            from toontown.chat import ResistanceChat
            args = word.split()
            if len(args) < 2:
                charges = 10
            else:
                charges = int(args[1])
            msgs = []
            for menuIndex in ResistanceChat.resistanceMenu:
                for itemIndex in ResistanceChat.getItems(menuIndex):
                    textId = ResistanceChat.encodeId(menuIndex, itemIndex)
                    msgs.append([textId, charges])
            av.b_setResistanceMessages(msgs)
            response = 'Resistance phrases restocked - %d charges' % charges
            self.down_setMagicWordResponse(senderId, response)

        elif wordIs("~restockSummons"):
            numSuits = len(SuitDNA.suitHeadTypes)
            fullSetForSuit = 0x01 | 0x02 | 0x04
            allSummons = numSuits * [fullSetForSuit]
            av.b_setCogSummonsEarned(allSummons)
            self.down_setMagicWordResponse(senderId, "Summons restocked")

        elif wordIs("~clearSummons"):
            numSuits = len(SuitDNA.suitHeadTypes)
            allSummons = numSuits * [0]
            av.b_setCogSummonsEarned(allSummons)
            self.down_setMagicWordResponse(senderId, "Summons emptied")

        elif wordIs("~newSummons"):
            args = word.split()

            level = None
            if len(args) > 1:
                level = int(args[1])

            if level and (level < 0 or level >= SuitDNA.suitsPerDept):
                self.down_setMagicWordResponse(
                    senderId, "usage: ~newSummons [level:0-11]")
            else:
                (suitIndex, type) = av.assignNewCogSummons(level)
                suitName = SuitDNA.suitHeadTypes[suitIndex]
                suitFullName = SuitBattleGlobals.SuitAttributes[suitName]['name']
                self.down_setMagicWordResponse(
                    senderId, "%s summons added for %s" % (type, suitFullName))

        elif wordIs("~treasures"):
            self.doTreasures(word, av, zoneId, senderId)

        elif wordIs("~emote"):
            self.doEmotes(word, av, zoneId, senderId)

        elif wordIs("~catalog"):
            self.doCatalog(word, av, zoneId, senderId)

        elif word == "~resetFurniture":
            house = None
            if av.houseId:
                house = self.air.doId2do.get(av.houseId)
            if house:
                house.setInitialFurniture()
                house.resetFurniture()
                response = "Furniture reset."
            else:
                response = "Could not find house."
            self.down_setMagicWordResponse(senderId, response)
            
        # Fishing
        elif word == "~clearFishTank":
            av.b_setFishTank([], [], [])
            self.down_setMagicWordResponse(senderId, "Cleared fish tank.")
            
        elif word == "~sellFishTank":
            # Add up the total value of all the fish
            totalValue = 0
            totalValue = av.fishTank.getTotalValue()
            # Credit the money
            av.addMoney(totalValue)
            # Clear the fish tank
            av.b_setFishTank([], [], [])
            # Feedback to sender
            self.down_setMagicWordResponse(senderId, ("Sold fish in tank for %s jellbeans." % totalValue))
            
        elif word == "~clearFishCollection":
            av.b_setFishCollection([], [], [])
            av.b_setFishingTrophies([])
            self.down_setMagicWordResponse(senderId, "Cleared fish collection.")
            
        elif word == "~completeFishCollection":
            from toontown.fishing import FishGlobals
            genusList = []
            speciesList = []
            weightList = []
            for genus in FishGlobals.getGenera():
                numSpecies = len(FishGlobals.getSpecies(genus))
                for species in range(numSpecies):
                    weight = FishGlobals.getRandomWeight(genus, species)
                    genusList.append(genus)
                    speciesList.append(species)
                    weightList.append(weight)
            
            av.b_setFishCollection(genusList, speciesList, weightList)
            self.down_setMagicWordResponse(senderId, "Complete fish collection.")

        elif word == "~randomFishTank":
            av.makeRandomFishTank()
            self.down_setMagicWordResponse(senderId, "Created random fishtank")

        elif word == "~allFishingTrophies":
            from toontown.fishing import FishGlobals
            allTrophyList = FishGlobals.TrophyDict.keys()
            av.b_setFishingTrophies(allTrophyList)
            self.down_setMagicWordResponse(senderId, "All fishing trophies")

        elif word[:4] == "~rod":
            from toontown.fishing import FishGlobals
            # Sets reward tier and optionally index
            args = word.split()
            rodId = int(args[1])
            if ((rodId > FishGlobals.MaxRodId) or
                (rodId < 0)):
                self.down_setMagicWordResponse(senderId, ("Invalid rod: %s" % (rodId)))
            else:
                av.b_setFishingRod(rodId)
                self.down_setMagicWordResponse(senderId, ("New fishing rod: %s" % (rodId)))

            
        elif wordIs('~inGameEdit'):
            # edit a level in the game engine
            # Note - do not call this as a toon - call ~edit instead. That
            # will automatically append your level doId so the AI knows
            # which one you want to edit, along with your edit username

            # make sure this AI is set up for editing
            if not __dev__:
                self.down_setMagicWordResponse(senderId,
                                               "AI not running in dev mode")
                return
            from otp.level import EditorGlobals
            msg = EditorGlobals.checkNotReadyToEdit()
            if msg is not None:
                self.down_setMagicWordResponse(senderId, msg)
                return

            args = word.split()
            levelDoId = int(args[1])
            editUsername = args[2]

            level = self.air.doId2do.get(levelDoId)
            if not level:
                self.down_setMagicWordResponse(
                    senderId, ("Level %s not found" % levelDoId))
                return

            from toontown.coghq import DistributedInGameEditorAI
            editor = DistributedInGameEditorAI.DistributedInGameEditorAI(
                self.air, level, senderId, editUsername)

            self.down_setMagicWordResponse(
                senderId, ("Editing level %s as %s" % (
                levelDoId, editUsername)))

        elif word[:13] == "~setNPCFriend":
            args = word.split()
            npcId = int(args[1])
            numCalls = int(args[2])
            if self.doNpcFriend(av, npcId, numCalls):
                self.down_setMagicWordResponse(senderId, "added NPC friend")
            else:
                self.down_setMagicWordResponse(senderId, "invalid NPC name")

        elif wordIs("~pianos"):
            if self.doNpcFriend(av, 1116, 100):
                self.down_setMagicWordResponse(senderId, "got pianos")
            else:
                self.down_setMagicWordResponse(senderId, "error getting pianos")

        elif wordIs("~resetNPCFriendsDict"):
            av.resetNPCFriendsDict()
            self.down_setMagicWordResponse(senderId, "Reset NPC Friends Dict")

        elif wordIs('~uberDrop'):
            from toontown.toon import NPCToons
            if (av.attemptAddNPCFriend(
                1116, DistributedToonAI.DistributedToonAI.maxCallsPerNPC
                ) == 1):
                self.down_setMagicWordResponse(senderId, "added NPC friend")
            else:
                self.down_setMagicWordResponse(senderId, "failed")

        elif wordIs("~bossBattle"):
            self.doBossBattle(word, av, zoneId, senderId)

        elif wordIs('~disguisePage'):
            args = word.split()
            flag = 1
            if len(args) >= 2:
                flag = int(args[1])
            av.b_setDisguisePageFlag(flag)
            self.down_setMagicWordResponse(senderId, "Disguise page = %s" % (flag))

        elif wordIs("~allParts"):
            from toontown.coghq import CogDisguiseGlobals
            args = word.split()
            for dept in self.getDepts(args):
                parts = av.getCogParts()
                parts[dept] = CogDisguiseGlobals.PartsPerSuitBitmasks[dept]

            av.b_setCogParts(parts)
            self.down_setMagicWordResponse(senderId, "Set cog parts: %s" % (parts))

        elif wordIs("~noParts"):
            args = word.split()
            for dept in self.getDepts(args):
                parts = av.getCogParts()
                parts[dept] = 0

            av.b_setCogParts(parts)
            self.down_setMagicWordResponse(senderId, "Set cog parts: %s" % (parts))

        elif wordIs("~part"):
            args = word.split()
            depts = self.getDepts(args)
            if len(args) > 1:
                # trust that user typed the factory type correctly...
                factoryType = args[1]
            else:
                factoryType = ToontownGlobals.FT_FullSuit
                
            for dept in depts:
                av.giveGenericCogPart(factoryType, dept)

            self.down_setMagicWordResponse(senderId, "Set cog parts: %s" % (av.getCogParts()))

        elif wordIs("~merits"):
            args = word.split()
            depts = self.getDepts(args)
            if len(args) > 1:
                numMerits = int(args[1])
                if numMerits > 32767:
                    numMerits = 32767
            else:
                self.down_setMagicWordResponse(senderId, "Specify number of merits to set.")
                return

            merits = av.getCogMerits()[:]
            for dept in depts:
                merits[dept] = numMerits
            av.b_setCogMerits(merits)

            self.down_setMagicWordResponse(senderId, "Set cog merits: %s" % (merits))

        elif wordIs("~promote"):
            args = word.split()
            depts = self.getDepts(args)

            for dept in depts:
                av.b_promote(dept)

            self.down_setMagicWordResponse(senderId, "Set cogTypes: %s and cogLevels: %s" % (av.getCogTypes(), av.getCogLevels()))

        elif wordIs("~cogSuit"):
            args = word.split()
            if len(args) > 1:
                cogType = args[1]
            else:
                self.down_setMagicWordResponse(senderId, "Specify cog type, or 'clear'.")
                return

            if cogType == 'clear':
                av.b_setCogTypes([0, 0, 0, 0])
                av.b_setCogLevels([0, 0, 0, 0])

            elif cogType == 'on':
                if len(args) > 2 and args[2] in SuitDNA.suitDepts:
                    dept = SuitDNA.suitDepts.index(args[2])
                    av.b_setCogIndex(dept)
                else:
                    self.down_setMagicWordResponse(senderId, "Specify dept.")
                return

            elif cogType == 'off':
                av.b_setCogIndex(-1)
                return
                                
            else:
                dept = SuitDNA.getSuitDept(cogType)
                if dept == None:
                    self.down_setMagicWordResponse(senderId, "Unknown cog type: %s" % (cogType))
                    return

                deptIndex = SuitDNA.suitDepts.index(dept)
                type = SuitDNA.getSuitType(cogType)
                minLevel = SuitBattleGlobals.SuitAttributes[cogType]['level']

                # determine max level (usually minLevel + 4, but 50 for last cog)
                if type >= (SuitDNA.suitsPerDept - 1):
                    maxLevel = ToontownGlobals.MaxCogSuitLevel + 1
                else:
                    maxLevel = minLevel + 4
                
                if len(args) > 2:
                    level = int(args[2]) - 1
                    if level < minLevel or level > maxLevel:
                        self.down_setMagicWordResponse(senderId, "Invalid level for %s (should be %s to %s)" % (cogType, minLevel + 1, minLevel + 5))
                        return
                else:
                    level = minLevel

                cogTypes = av.getCogTypes()[:]
                cogLevels = av.getCogLevels()[:]
                cogTypes[deptIndex] = type - 1
                cogLevels[deptIndex] = level
                av.b_setCogTypes(cogTypes)
                av.b_setCogLevels(cogLevels)

            self.down_setMagicWordResponse(senderId, "Set cogTypes: %s and cogLevels: %s" % (av.getCogTypes(), av.getCogLevels()))

        elif wordIs("~pinkSlips"):
            args = word.split()
            depts = self.getDepts(args)
            if len(args) > 1:
                numSlips = int(args[1])
                if numSlips > 255:
                    numSlips = 255
            else:
                self.down_setMagicWordResponse(senderId, "Specify number of pinkSlips to set.")
                return

            av.b_setPinkSlips(numSlips)

            self.down_setMagicWordResponse(senderId, "Set PinkSlips: %s" % (numSlips))
            
            
        elif wordIs("~setPaid"):
            args = word.split()
            depts = self.getDepts(args)
            if len(args) > 1:
                paid = int(args[1])
                if paid:
                    paid = 1
                    av.b_setAccess(OTPGlobals.AccessFull)
                else:
                    paid = 0
                    av.b_setAccess(OTPGlobals.AccessVelvetRope)
            else:
                self.down_setMagicWordResponse(senderId, "0 for unpaid 1 for paid")
                return

            self.down_setMagicWordResponse(senderId, "setPaid: %s" % (paid))



        elif wordIs("~holiday"):
            # Start or stop a holiday
            holiday = 5
            fStart = 1
            args = word.split()
            if len(args) == 1:
                self.down_setMagicWordResponse(
                    senderId, "Usage:\n~holiday id\n~holiday id start\n~holiday id end\n~holiday list")
                return
            elif len(args) > 1:
                if args[1] == 'list':
                    self.down_setMagicWordResponse(
                        senderId,
                        "1: July 4\n2: New Years\n3: Halloween\n4: Winter Decorations\n5: Skelecog Invades\n6: Mr. Holly Invades\n7: Fish Bingo\n8: Species Election\n9: Black Cat\n10: Resistance Event\n11: Reset Daily Recs\n12: Reset Weekly Recs\n13: Trick-or-Treat\n14: Grand Prix\n17: Trolley Metagame")
                    return
                else:
                    holiday = int(args[1])
            doPhase = None
            stopForever = False
            if len(args) > 2:
                if args[2] == 'start':
                    fStart = 1
                elif args[2] == 'end':
                    fStart = 0
                    if len(args) > 3:
                        if args[3] == 'forever':
                            stopForever = True
                elif args[2] == 'phase':
                    if len(args) >3 :
                        doPhase = args[3]
                    else:
                        self.down_setMagicWordResponce(senderId,"need a number after phase")
                else:
                    self.down_setMagicWordResponse(
                        senderId, 'Arg 2 should be "start" or "end" or "end forever" or "phase"')
                    return
            if doPhase:
                result = self.air.holidayManager.forcePhase(holiday, doPhase)
                self.down_setMagicWordResponse(senderId, "succeeded=%s forcing holiday %d to phase %s" %(result,holiday,doPhase))
            elif fStart:
                self.down_setMagicWordResponse(
                    senderId, "Starting holiday %d" % holiday)
                self.air.holidayManager.startHoliday(holiday)
            else:
                self.down_setMagicWordResponse(
                    senderId, "Ending holiday %d stopForever=%s" % (holiday, stopForever))
                self.air.holidayManager.endHoliday(holiday, stopForever)

        elif wordIs('~pet') and simbase.wantPets:
            def summonPet(petId, callback=None, zoneId=zoneId):
                def handleGetPet(success, pet, petId=petId, zoneId=zoneId):
                    if success:
                        pet.generateWithRequiredAndId(petId, self.air.districtId, zoneId)
                    if callback is not None:
                        callback(success, pet)
                self.air.petMgr.getPetObject(petId, handleGetPet)

            petId = av.getPetId()
            if petId == 0:
                def handleCreate(success, petId, zoneId=zoneId):
                    if success:
                        self.air.petMgr.assignPetToToon(petId, av.doId)
                        def handlePetGenerated(success, pet, avId=av.doId,
                                               zoneId=zoneId):
                            if success:
                                pet._initDBVals(
                                    avId,
                                    traitSeed=PythonUtil.randUint31())
                                pet.sendSetZone(zoneId)
                                pet.delete()
                        # since this is the first time the pet is being
                        # created, and we're going to be setting properties
                        # on the pet, generate it in the Quiet zone first,
                        # then move it to the requested zone.
                        summonPet(petId, callback=handlePetGenerated,
                                  zoneId=ToontownGlobals.QuietZone)
                self.air.petMgr.createNewPetObject(handleCreate)
                response = 'creating new pet...'
            else:
                if petId in self.air.doId2do:
                    response = 'pet %s already active' % petId
                else:
                    summonPet(petId)
                    response = 'summoning pet %s...' % petId
            
            self.down_setMagicWordResponse(senderId, response)

        elif wordIs('~dismiss') and simbase.wantPets:
            pet, response = self.getPet(av)
            if pet:
                pet.requestDelete()
                response = "pet %s dismissed" % pet.doId
            self.down_setMagicWordResponse(senderId, response)

        elif wordIs('~deletePet') and simbase.wantPets:
            petId = av.getPetId()
            if petId == 0:
                response = "don't have a pet"
            else:
                # if the pet is active, dismiss it
                pet = self.air.doId2do.get(petId)
                if pet is not None:
                    pet.requestDelete()
                self.air.petMgr.deleteToonsPet(av.doId)
                response = "deleted pet %s" % petId
            self.down_setMagicWordResponse(senderId, response)

        elif wordIs('~petName') and simbase.wantPets:
            pet, response = self.getPet(av)
            if pet:
                args = word.split()
                if len(args) < 2:
                    response = "~petName name"
                else:
                    pet.b_setPetName(args[1])
                    response = 'name changed'
            self.down_setMagicWordResponse(senderId, response)


        elif wordIs('~feed') and simbase.wantPets:
            pet, response = self.getPet(av)
            if pet:
                pet.feed(av)
                response = "fed pet"
            self.down_setMagicWordResponse(senderId, response)

        elif wordIs('~attend') and simbase.wantPets:
            pet, response = self.getPet(av)
            if pet:
                pet.scratch(av)
                response = "attended pet"
            self.down_setMagicWordResponse(senderId, response)

        elif wordIs('~callPet') and simbase.wantPets:
            pet, response = self.getPet(av)
            if pet:
                pet.call(av)
                response = "called pet"
            self.down_setMagicWordResponse(senderId, response)

        elif wordIs('~stay') and simbase.wantPets:
            pet, response = self.getPet(av)
            if pet:
                pet.handleStay(av)
                response = "Stay, %s." % pet.getPetName()
            self.down_setMagicWordResponse(senderId, response)

        elif wordIs('~shoo') and simbase.wantPets:
            pet, response = self.getPet(av)
            if pet:
                pet.handleShoo(av)
                response = "Shoo, %s." % pet.getPetName()
            self.down_setMagicWordResponse(senderId, response)

        elif wordIs('~maxMood') and simbase.wantPets:
            pet, response = self.getPet(av)
            if pet:
                pet.maxMood()
                response = "pet mood maxed"
            self.down_setMagicWordResponse(senderId, response)

        elif wordIs('~minMood') and simbase.wantPets:
            pet, response = self.getPet(av)
            if pet:
                pet.minMood()
                response = "pet mood minimized"
            self.down_setMagicWordResponse(senderId, response)

        elif wordIs('~petMood') and simbase.wantPets:
            pet, response = self.getPet(av)
            if pet:
                args = word.split()
                if len(args) < 3:
                    response = '~petMood component value'
                else:
                    from toontown.pets import PetMood
                    comp = args[1]
                    value = float(args[2])
                    if comp not in PetMood.PetMood.Components:
                        response = "unknown mood '%s'" % comp
                    else:
                        pet.mood.setComponent(comp, value)
                        response = "mood set"
            self.down_setMagicWordResponse(senderId, response)

        elif wordIs('~moodTimescale') and simbase.wantPets:
            pet, response = self.getPet(av)
            if pet:
                args = word.split()
                if len(args) < 2:
                    response = '~moodTimescale timescale'
                else:
                    simbase.petMoodTimescale = float(args[1])
                    # make the new timescale take effect immediately
                    pet.mood._driftMoodTask()
                    response = 'pet mood timescale = %s' % args[1]
            self.down_setMagicWordResponse(senderId, response)

        elif wordIs('~typicalTraits') and simbase.wantPets:
            szId = None
            args = word.split()
            if len(args) > 1:
                szId = self.Str2szId.get(args[1])
            if szId == None:
                szId = ToontownGlobals.ToontownCentral

            pet, response = self.getPet(av)
            if pet:
                pet._setTypicalTraits(szId)
                # delete him to make sure we don't have a pet whose
                # internal state is out-of-sync
                pet.requestDelete()
                response = 'set typical traits for %s' % szId
            self.down_setMagicWordResponse(senderId, response)

        elif wordIs('~medianTraits') and simbase.wantPets:
            szId = None
            args = word.split()
            if len(args) > 1:
                szId = self.Str2szId.get(args[1])
            if szId == None:
                szId = ToontownGlobals.ToontownCentral

            pet, response = self.getPet(av)
            if pet:
                pet._setMedianTraits(szId)
                # delete him to make sure we don't have a pet whose
                # internal state is out-of-sync
                pet.requestDelete()
                response = 'set median traits for %s' % szId
            self.down_setMagicWordResponse(senderId, response)

        elif wordIs('~lowTraits') and simbase.wantPets:
            szId = None
            args = word.split()
            if len(args) > 1:
                szId = self.Str2szId.get(args[1])
            if szId == None:
                szId = ToontownGlobals.ToontownCentral

            pet, response = self.getPet(av)
            if pet:
                pet._setLowTraits(szId)
                # delete him to make sure we don't have a pet whose
                # internal state is out-of-sync
                pet.requestDelete()
                response = 'set low traits for %s' % szId
            self.down_setMagicWordResponse(senderId, response)

        elif wordIs('~highTraits') and simbase.wantPets:
            szId = None
            args = word.split()
            if len(args) > 1:
                szId = self.Str2szId.get(args[1])
            if szId == None:
                szId = ToontownGlobals.ToontownCentral

            pet, response = self.getPet(av)
            if pet:
                pet._setHighTraits(szId)
                # delete him to make sure we don't have a pet whose
                # internal state is out-of-sync
                pet.requestDelete()
                response = 'set high traits for %s' % szId
            self.down_setMagicWordResponse(senderId, response)

        elif wordIs('~leash') and simbase.wantPets:
            pet, response = self.getPet(av)
            if pet:
                response = pet.toggleLeash(av.doId)
            self.down_setMagicWordResponse(senderId, response)

        elif wordIs('~lockPet') and simbase.wantPets:
            pet, response = self.getPet(av)
            if pet:
                if pet.isLockedDown():
                    response = 'pet already locked down'
                else:
                    pet.lockPet()
                    response = 'pet locked down'
            self.down_setMagicWordResponse(senderId, response)

        elif wordIs('~unlockPet') and simbase.wantPets:
            pet, response = self.getPet(av)
            if pet:
                if not pet.isLockedDown():
                    response = 'pet already not locked down'
                else:
                    pet.unlockPet()
                    response = 'pet no longer locked down'
            self.down_setMagicWordResponse(senderId, response)

        elif wordIs('~attendPet') and simbase.wantPets:
            pet, response = self.getPet(av)
            if pet:
                response = 'attendPet'
                pet.handleAvPetInteraction(4, av.getDoId())
            self.down_setMagicWordResponse(senderId, response)

        elif wordIs('~feedPet') and simbase.wantPets:
            pet, response = self.getPet(av)
            if pet:
                response = 'feedPet'
                pet.handleAvPetInteraction(3, av.getDoId())
            self.down_setMagicWordResponse(senderId, response)

        elif wordIs('~petStress') and simbase.wantPets:
            from toontown.pets import DistributedPetAI
            args = word.split()
            numPets = 56 # 50 friends, six Toons/acct #100 * 3 # 500 toons, 100 at estate, 3 pets per
            if len(args) > 1:
                numPets = int(args[1])
            for i in xrange(numPets):
                pet = DistributedPetAI.DistributedPetAI(self.air)
                # make up a fake owner doId
                pet._initFakePet(100+i, 'StressPet%s' % i)
                pet.generateWithRequired(zoneId)
                pet.setPos(randFloat(-30, 30),
                           randFloat(-30, 30), 0)
                pet.b_setParent(ToontownGlobals.SPRender)

        elif wordIs('~petTricks') and simbase.wantPets:
            from toontown.pets import PetConstants, PetTricks
            args = word.split()
            trickIds = []
            invalid = 0
            for num in args[1:]:
                id = int(num)
                if id not in PetTricks.Tricks:
                    invalid = 1
                    response = 'invalid trick ID: %s' % id
                    break
                trickIds.append(id)
            if not invalid:
                av.b_setPetTrickPhrases(trickIds)
                response = 'set pet trick phrases: %s' % trickIds
            self.down_setMagicWordResponse(senderId, response)

        elif wordIs('~trickAptitude') and simbase.wantPets:
            pet, response = self.getPet(av)
            if pet:
                args = word.split()
                if len(args) < 2:
                    response = '~trickAptitude aptitude'
                else:
                    from toontown.pets import PetTricks
                    pet.b_setTrickAptitudes([float(args[1])] *
                                            (len(PetTricks.Tricks)-1))
                    response = 'trick aptitude = %s' % args[1]
            self.down_setMagicWordResponse(senderId, response)

        elif wordIs('~spamTrick'):
            # spam the nearby pets with N commands to do the 'jump' trick
            from toontown.pets import PetObserve
            for i in xrange(20):
                PetObserve.send(av.zoneId,
                                PetObserve.getSCObserve(21200, av.doId))

        elif wordIs('~blackCat'):
            response = 'done'
            error = av.makeBlackCat()
            if error:
                response = error
            self.down_setMagicWordResponse(senderId, response)

        elif wordIs('~bingoCheat') and simbase.wantBingo:
            av.bingoCheat = not av.bingoCheat
            if av.bingoCheat:
                response = "Bingo cheating turned on.  You will always catch boots."
            else:
                response = "Bingo cheating turned off"

            self.down_setMagicWordResponse(senderId, response)

        elif __dev__ and wordIs('~airender'):
            showZone = zoneId
            args = word.split()
            if len(args) > 1:
                showZone = int(args[1])
            from otp.ai import ShowBaseAI
            base = ShowBaseAI.ShowBaseAI('zone %s' % showZone)
            base.zoneData = AIZoneData(self.air.districtId, showZone)
            render = base.zoneData.getRender()
            base.camNode.setScene(render)
            base.camera.reparentTo(render)
            render.showCS()
            axis = loader.loadModel('models/misc/xyzAxis')
            axis.reparentTo(render)
            axis.setPosHpr(render, 0, 0, 0, 0, 0, 0)
            self.down_setMagicWordResponse(
                senderId, 'rendering AI zone %s' % showZone)

        elif __dev__ and wordIs("~aics"):
            showZone = zoneId
            args = word.split()
            if len(args) > 1:
                showZone = int(args[1])
            zoneData = AIZoneData(self.air.districtId, showZone)
            render = zoneData.getRender(showZone)

            csVisible = 0
            if hasattr(render, 'csVisible'):
                csVisible = render.csVisible

            if csVisible:
                render.hideCS()
                action = 'hidden'
            else:
                render.showCS()
                action = 'shown'

            render.csVisible = not csVisible
            self.down_setMagicWordResponse(
                senderId, 'collisions %s for %s' % (action, showZone))

        ### Karting ###            
        elif(word[:8] == '~BuyKart'):
            if (simbase.wantKarts):                
                accList = av.getKartAccessoriesOwned()
                #accList[-1] = getDefaultColor()
                accList[-2] = getDefaultRim()

                response = "Av %s now owns accessories: %s" % (av.getDoId(), accList)                
                av.b_setKartAccessoriesOwned(accList)
                self.down_setMagicWordResponse(senderId, response)

        elif(word[:13] == '~BuyAccessory'):
            if (simbase.wantKarts):
                response = "Av %s attempting to buy accessory %s" % (av.getDoId(), word[14:])
                av.addOwnedAccessory(int(word[14:]))                
                self.down_setMagicWordResponse(senderId, response)

        elif(word[:8] == '~Tickets'):
            if (simbase.wantKarts):
                response = "Av %s now has %s tickets" % (av.getDoId(), word[9:])
                av.b_setTickets(int(word[9:]))
                self.down_setMagicWordResponse(senderId, response)
        
        elif wordIs('~allowSoloRace'):
            if (simbase.wantKarts):
                av.setAllowSoloRace(not av.allowSoloRace)
                if av.allowSoloRace:
                    response = "Av %s can now race solo" % (av.getDoId())
                else:
                    response = "Av %s can no longer Race solo" % (av.getDoId())
                self.down_setMagicWordResponse(senderId, response)
        
        elif wordIs('~allowRaceTimeout'):
            if (simbase.wantKarts):
                av.setAllowRaceTimeout(not av.allowRaceTimeout)
                if av.allowRaceTimeout:
                    response = "Av %s can timeout of races" % (av.getDoId())
                else:
                    response = "Av %s can not timeout of races" % (av.getDoId())
                self.down_setMagicWordResponse(senderId, response)
        
        elif wordIs('~drive'):
            # Execute an arbitrary Python command on the AI.
            av.takeOutKart()
            self.down_setMagicWordResponse(
                senderId, "I feel the need... the need for SPEED!")

        # Golf
        elif wordIs("~golf"):
            self.doGolf(word, av, zoneId, senderId)

        # Mail
        elif wordIs("~mail"):
            self.doMail(word, av, zoneId, senderId)

        # Parties
        elif wordIs("~party"):
            self.doParty(word, av, zoneId, senderId)

        #Gardening
        elif wordIs("~garden"):
            self.doGarden(word, av, zoneId, senderId)        

        elif word == "~clearGardenSpecials":
            newWord = '~garden clearCarriedSpecials'
            self.doGarden(newWord, av, zoneId, senderId)

        elif word == "~clearFlowerCollection":
            newWord = '~garden clearCollection'
            self.doGarden(newWord, av, zoneId, senderId)
            
        elif word == "~completeFlowerCollection":
            newWord = '~garden completeCollection'
            self.doGarden(newWord, av, zoneId, senderId)

        elif wordIs('~startGarden'):
            newWord = '~garden start'
            self.doGarden(newWord, av, zoneId, senderId)
            
        elif wordIs('~clearGarden'):
            newWord = '~garden clear'
            self.doGarden(newWord, av, zoneId, senderId)
            
        elif wordIs('~cannons'):
            sender = simbase.air.doId2do.get(senderId)
            if sender:
                zoneId = sender.zoneId
                estateOwnerDoId = simbase.air.estateMgr.zone2owner.get(zoneId)
                estate = simbase.air.estateMgr.estate.get(estateOwnerDoId)

                if hasattr(estate, "cannonFlag"):
                    if estate.cannonFlag:
                        estate.endCannons()
                        response = "Cannons Ended"
                    else:
                        estate.startCannons()
                        response = "Cannons Started"

        elif wordIs('~gameTable'):
            sender = simbase.air.doId2do.get(senderId)
            if sender:
                zoneId = sender.zoneId
                estateOwnerDoId = simbase.air.estateMgr.zone2owner.get(zoneId)
                estate = simbase.air.estateMgr.estate.get(estateOwnerDoId)
                
                if hasattr(estate, 'gameTableFlag'):
                    if estate.gameTableFlag:
                        estate.endGameTable()
                        response = 'Game Table Ended'
                    else:
                        estate.startGameTable()
                        response = 'Game Table Started'
        
        elif wordIs('~plantGarden'):
            newWord = '~garden plant'
            args = word.split()
            for i in range(1, len(args)):
                newWord += ' '
                newWord += args[i]
            self.doGarden(newWord, av, zoneId, senderId)
        
        elif wordIs('~trialerCount'):
            total = 0
            trialer =0
            paid = 0
            unknown = 0
            allToons = simbase.air.doFindAll('DistributedToonAI')
            for toon in allToons:
                total += 1
                if toon.getGameAccess() == ToontownGlobals.AccessFull:
                    paid += 1
                elif toon.getGameAccess() == ToontownGlobals.AccessVelvetRope:
                    trialer += 1
                else:
                    unknown += 1
            response = "%d trialers, %d paid, %d total" % (trialer, paid, total)
            if unknown:
                response += "%d unknown" % unknown
            self.down_setMagicWordResponse(senderId, response)
            
        elif wordIs('~deleteBackupStores'):
            storeClient = DataStoreAIClient(self.air, DataStoreGlobals.GEN, None)
            storeClient.deleteBackupStores()
            storeClient.closeStore() 
            
        elif wordIs("~autoRich"):
            # Available only __dev__ and GMs. Guard against hacked clients sending this. If a non-GM
            # needs to do this on LIVE, simply use ~rich instead.
            if __dev__ or av.hasGMName():
                # Basically this is a signal that a GM has logged in.
                if av.hasGMName():
                    self.air.writeServerEvent('GM', av.doId, 'GM %s used auto-rich' % av.getName())
                    assert self.notify.debug('GM %s %s used auto-rich' % (av.doId, av.getName()))
            
                args = word.split()
                postName = 'autoRich-%s' % av.doId
                enable = not bboard.get(postName, 0)
                # are they explicitly setting the state?
                if len(args) > 1:
                    try:
                        enable = int(args[1])
                    except:
                        self.down_setMagicWordResponse(senderId,
                                                       'invalid state flag: %s' %
                                                       args[1])
                        return
                if enable:
                    state = 'ON'
                    av.b_setMoney(av.maxMoney)
                    av.b_setBankMoney(av.maxBankMoney)
                    bboard.post(postName, 1)
                else:
                    state = 'OFF'
                    bboard.remove(postName)
                self.down_setMagicWordResponse(senderId, 'autoRich %s' % state)
            else:
                self.air.writeServerEvent('suspicious', av.doId, 'non-GM toon with name %s using ~autoRich' % av.getName())
            
        else:
            # The word is not an AI-side magic word.  If the sender is
            # different than the target avatar, then pass the magic
            # word down to the target client-side MagicWordManager to
            # execute a client-side magic word.
            if (senderId != av.doId):
                self.sendUpdateToAvatarId(av.doId, 'setMagicWord', [word, av.doId, zoneId])                  

    def doNpcFriend(self, av, npcId, numCalls):
        return av.attemptAddNPCFriend(npcId, numCalls) == 1

    def getDepts(self, args):
        # Returns a list of the dept indices specified by args[1], or
        # all depts if nothing is specified.  If a dept is specified,
        # args[1] is removed from the list.

        depts = []
        if len(args) > 1:
            if args[1] == 'all':
                depts = [0, 1, 2, 3]
                del args[1]
            else:
                allLettersGood = 1
                for letter in args[1]:
                    if letter in SuitDNA.suitDepts:
                        dept = SuitDNA.suitDepts.index(letter)
                        depts.append(dept)
                    else:
                        allLettersGood = 0
                        break

                if allLettersGood:
                    del args[1]
                else:
                    depts = []

        if depts:
            return depts
        else:
            return [0, 1, 2, 3]
        

    def doExp(self, word, av, zoneId, senderId):
        """Handle the ~exp magic word."""
        track = None
        args=word.split()
        trackIndex = -1
        increment = 0
        gotIncrement = 0
        
        if len(args) > 1:
            trackStr = args[1]
            if trackStr != "all":
                trackIndex = ToontownBattleGlobals.Tracks.index(trackStr)

        if len(args) > 2:
            increment = int(args[2])
            gotIncrement = 1

        if trackIndex == -1:
            for trackIndex in range(ToontownBattleGlobals.MAX_TRACK_INDEX + 1):
                if av.hasTrackAccess(trackIndex):
                    if not gotIncrement:
                        # No increment specified; the default is whatever
                        # it takes to get to the next track.
                        increment = av.experience.getNextExpValue(trackIndex) - av.experience.getExp(trackIndex)
                
                    self.notify.debug("Adding %d to %s track for %s." % (increment, ToontownBattleGlobals.Tracks[trackIndex], av.name))
                    av.experience.addExp(trackIndex, increment)
        else:
            if not gotIncrement:
                # No increment specified; the default is whatever
                # it takes to get to the next track.
                increment = av.experience.getNextExpValue(trackIndex) - av.experience.getExp(trackIndex)
                
            self.notify.debug("Adding %d to %s track for %s." % (increment, ToontownBattleGlobals.Tracks[trackIndex], av.name))
            av.experience.addExp(trackIndex, increment)
                
        av.d_setExperience(av.experience.makeNetString())


    def doTrophy(self, word, av, zoneId, senderId):
        """Handle the ~trophy magic word: artificially set (or
        restore) the trophy score."""

        args = word.split()
        if len(args) > 1:
            score = int(args[1])

            response = "Set trophy score to %s." % (score)
            self.down_setMagicWordResponse(senderId, response)
        else:
            # No score specified; restore the actual trophy score.
            score = self.air.trophyMgr.getTrophyScore(av.doId)

            response = "Trophy score is %s." % (score)
            self.down_setMagicWordResponse(senderId, response)

        av.d_setTrophyScore(score)


    def doCheesyEffect(self, word, av, zoneId, senderId):
        effect = None
        if zoneId >= ToontownGlobals.DynamicZonesBegin:
            hoodId = 1
        else:
            hoodId = ZoneUtil.getCanonicalHoodId(zoneId)
        timeLimit = 10
        
        args = word.split()
        try:
            effect = eval("ToontownGlobals.CE" + args[1])
        except:
            try:
                effect = eval(args[1])
            except:
                effect = None

        if effect == None:
            self.down_setMagicWordResponse(senderId, "Unknown effect %s." % (args[1]))
            return

        if len(args) > 2:
            timeLimit = int(args[2])
        
        # Let it expire in timeLimit minutes.
        expireTime = (int)(time.time() / 60 + 0.5) + timeLimit
        av.b_setCheesyEffect(effect, hoodId, expireTime)

    def doCogTakeOver(self, word, av, zoneId, senderId):
        """Handle the ~cogTakeOver magic word."""
        track = None
        level = None
        streetId = ZoneUtil.getBranchZone(zoneId)
        args = word.split()

        now = args.count("now")
        if now:
            args.remove("now")
        slow = args.count("slow")
        if slow:
            args.remove("slow")

        if len(args)>1:
            track=args[1]
            if track == 'x':
                track = None

        if len(args)>2:
            if args[2] != 'x':
                level=int(args[2])
                level = max(min(level, 9), 1)

        if len(args)>4:
            if args[4] == 'all':
                streetId = 'all'
            else:
                streetId=int(args[4])

                if not self.air.suitPlanners.has_key(streetId):
                    response = "Street %d is not known." % (streetId)
                    self.down_setMagicWordResponse(senderId, response)
                    return

        if streetId == 'all':
            # All buildings, everywhere.
            blockMap = {}
            for sp in self.air.suitPlanners.values():
                if sp.buildingMgr:
                    blockMap[sp.buildingMgr] = sp.buildingMgr.getToonBlocks()

        else:
            # Just the buildings on this street.
            sp = self.air.suitPlanners[streetId]
            bm = sp.buildingMgr

            blocks = None
            if len(args)>3:
                if (args[3] == "all"):
                    blocks = bm.getToonBlocks()
                elif (args[3] == "this"):
                    blocks = None
                else:
                    blocks=[int(args[3])]

            if blocks == None:
                # Try to figure out what doors we're standing in front
                # of.
                blocks = []
                for i in bm.getToonBlocks():
                    building = bm.getBuilding(i)
                    if hasattr(building, "door"):
                        if building.door.zoneId == zoneId:
                            blocks.append(i)

            blockMap = { bm: blocks }

        points = sp.streetPointList[:]
        failureCount = 0
        minPathLen = 2
        maxPathLen = 10
        if slow:
            minPathLen = None
            maxPathLen = None

        total = 0
        for bm, blocks in blockMap.items():
            total += len(blocks)
            for i in blocks:
                if now:
                    # Take over the building immediately.
                    level, type, track = \
                           sp.pickLevelTypeAndTrack(level, None, track)
                    building = bm.getBuilding(i)
                    building.suitTakeOver(track, level - 1, None)

                else:
                    # Dispatch a suit to take over the building.
                    if not slow:
                        # Let the suit take its time.
                        points = sp.getStreetPointsForBuilding(i)

                    suit = None
                    retryCount = 0
                    while suit == None and len(points) > 0 and retryCount < 20:
                        suit = sp.createNewSuit([], points,
                                                suitTrack = track,
                                                suitLevel = level,
                                                toonBlockTakeover = i,
                                                minPathLen = minPathLen,
                                                maxPathLen = maxPathLen)
                        retryCount += 1
                    if suit == None:
                        failureCount += 1

                self.notify.debug("cogTakeOver %s %s %d %d" % 
                                  (track, level, i, zoneId))

        response = "%d buildings." % (total)
        if (failureCount > 0):
            response += "  %d failed." % (failureCount)
            
        self.down_setMagicWordResponse(senderId, response)

    def doCogdoTakeOver(self, word, av, zoneId, senderId):
        """Handle the ~cogdoTakeOver magic word."""
        level = None
        streetId = ZoneUtil.getBranchZone(zoneId)
        args = word.split()

        now = args.count("now")
        if now:
            args.remove("now")
        slow = args.count("slow")
        if slow:
            args.remove("slow")

        if len(args)>1:
            if args[1] != 'x':
                level=int(args[2])
                level = max(min(level, 9), 1)

        if len(args)>4:
            if args[4] == 'all':
                streetId = 'all'
            else:
                streetId=int(args[4])

                if not self.air.suitPlanners.has_key(streetId):
                    response = "Street %d is not known." % (streetId)
                    self.down_setMagicWordResponse(senderId, response)
                    return

        if streetId == 'all':
            # All buildings, everywhere.
            blockMap = {}
            for sp in self.air.suitPlanners.values():
                if sp.buildingMgr:
                    blockMap[sp.buildingMgr] = sp.buildingMgr.getToonBlocks()

        else:
            # Just the buildings on this street.
            sp = self.air.suitPlanners[streetId]
            bm = sp.buildingMgr

            blocks = None
            if len(args)>3:
                if (args[3] == "all"):
                    blocks = bm.getToonBlocks()
                elif (args[3] == "this"):
                    blocks = None
                else:
                    blocks=[int(args[3])]

            if blocks == None:
                # Try to figure out what doors we're standing in front
                # of.
                blocks = []
                for i in bm.getToonBlocks():
                    building = bm.getBuilding(i)
                    if hasattr(building, "door"):
                        if building.door.zoneId == zoneId:
                            blocks.append(i)

            blockMap = { bm: blocks }

        points = sp.streetPointList[:]
        failureCount = 0
        minPathLen = 2
        maxPathLen = 10
        if slow:
            minPathLen = None
            maxPathLen = None

        total = 0
        for bm, blocks in blockMap.items():
            total += len(blocks)
            for i in blocks:
                if now:
                    # Take over the building immediately.
                    level, type, track = \
                           sp.pickLevelTypeAndTrack(level, None, track)
                    building = bm.getBuilding(i)
                    building.cogdoTakeOver(level - 1, None)

                else:
                    # Dispatch a suit to take over the building.
                    if not slow:
                        # Let the suit take its time.
                        points = sp.getStreetPointsForBuilding(i)

                    suit = None
                    retryCount = 0
                    while suit == None and len(points) > 0 and retryCount < 20:
                        track = random.choice(SuitDNA.suitDepts)
                        suit = sp.createNewSuit([], points,
                                                suitTrack = track,
                                                suitLevel = level,
                                                toonBlockTakeover = i,
                                                cogdoTakeover = True,
                                                minPathLen = minPathLen,
                                                maxPathLen = maxPathLen)
                        retryCount += 1
                    if suit == None:
                        failureCount += 1

                self.notify.debug("cogdoTakeOver %s %s %d %d" % 
                                  (track, level, i, zoneId))

        response = "%d cogdos." % (total)
        if (failureCount > 0):
            response += "  %d failed." % (failureCount)
            
        self.down_setMagicWordResponse(senderId, response)

    def doToonTakeOver(self, word, av, zoneId, senderId):
        """Handle the ~toonTakeOver magic word."""
        streetId = ZoneUtil.getBranchZone(zoneId)
        args=word.split()
        if len(args)>2:
            if args[2] == 'all':
                streetId = 'all'
            else:
                streetId=int(args[2])

                if not self.air.suitPlanners.has_key(streetId):
                    response = "Street %d is not known." % (streetId)
                    self.down_setMagicWordResponse(senderId, response)
                    return

        if streetId == 'all':
            # All buildings, everywhere.
            blockMap = {}
            for sp in self.air.suitPlanners.values():
                if sp.buildingMgr:
                    blockMap[sp.buildingMgr] = sp.buildingMgr.getSuitBlocks()

        else:
            # Just the buildings on this street.
            bm=self.air.buildingManagers[streetId]
            blocks = None
            if len(args)>1:
                if (args[1] == "all"):
                    blocks = bm.getSuitBlocks()
                elif (args[1] == "this"):
                    blocks = None
                else:
                    blocks=[int(args[1])]

            if blocks == None:
                # Try to figure out what doors we're standing in front
                # of.
                blocks = []
                for i in bm.getSuitBlocks():
                    building = bm.getBuilding(i)
                    if hasattr(building, "elevator"):
                        if building.elevator.zoneId == zoneId and \
                               building.elevator.fsm.getCurrentState().getName() == 'waitEmpty':
                            blocks.append(i)
            blockMap = { bm: blocks }

        total = 0
        for bm, blocks in blockMap.items():
            total += len(blocks)
            for i in blocks:
                building = bm.getBuilding(i)
                building.b_setVictorList([0, 0, 0, 0])
                building.updateSavedBy([(av.doId, av.name, av.dna.asTuple())])
                building.toonTakeOver()
                self.notify.debug("Toon take over %s %s" % (i, streetId))

        response = "%d buildings." % (total)
        self.down_setMagicWordResponse(senderId, response)

    def formatWelcomeValley(self, hood):
        mgr = self.air.welcomeValleyManager

        if hood == mgr.newHood:
            return "%s N" % (hood[0].zoneId)
        elif hood in mgr.removingHoods:
            return "%s R" % (hood[0].zoneId)
        else:
            return "%s" % (hood[0].zoneId)
        
    def doWelcome(self, word, av, zoneId, senderId):
        """Handle the ~welcome magic word, for managing Welcome Valley."""
        args = word.split()

        hoodId = ZoneUtil.getHoodId(zoneId)
        mgr = self.air.welcomeValleyManager

        # if this is a GS hoodId, just grab the TT hood
        if (hoodId % 2000) < 1000:
            hood = mgr.welcomeValleys.get(hoodId)
        else:
            hood = mgr.welcomeValleys.get(hoodId - 1000)

        if len(args) == 1:
            # No parameter: report the current zone and population.
            if hood == None:
                response = "Not in Welcome Valley."
            else:
                response = "%s, pg = %s, hood = %s" % (
                    self.formatWelcomeValley(hood),
                    hood[0].getPgPopulation(),
                    hood[0].getHoodPopulation())

        elif args[1] == "pg":
            # ~welcome pg: list the playground population of all
            # Welcome Valleys.

            response = ""
            hoodIds = mgr.welcomeValleys.keys()
            hoodIds.sort()
            for hoodId in hoodIds:
                hood = mgr.welcomeValleys[hoodId]
                response += "\n%s %s" % (
                    self.formatWelcomeValley(hood),
                    hood[0].getPgPopulation())

            if response == "":
                response = "No Welcome Valleys."
            else:
                response = response[1:]

        elif args[1] == "hood":
            # ~welcome hood: list the hood population of all
            # Welcome Valleys.

            response = ""
            hoodIds = mgr.welcomeValleys.keys()
            hoodIds.sort()
            for hoodId in hoodIds:
                hood = mgr.welcomeValleys[hoodId]
                response += "\n%s %s" % (
                    self.formatWelcomeValley(hood),
                    hood[0].getHoodPopulation())

            if response == "":
                response = "No Welcome Valleys."
            else:
                response = response[1:]

        elif args[1] == "login":
            # ~welcome login avId: simulate a new player logging in.
            # avId is an arbitrary number which should probably not
            # match any real avatars.
            avId = int(args[2])
            
            zoneId = mgr.avatarRequestZone(avId, ToontownGlobals.WelcomeValleyToken)
            response = "%s assigned to %s." % (avId, zoneId)

        elif args[1] == "logout":
            # ~welcome logout avId: simulate a player logging out.
            # avId is an arbitrary number which should probably not
            # match any real avatars.
            avId = int(args[2])

            avZoneId = mgr.avatarZones.get(avId)
            if avZoneId:
                mgr.avatarLogout(avId)
                response = "%s logged out from %s." % (avId, avZoneId)
            else:
                response = "%s is unknown." % (avId)

        elif args[1] == "zone":
            # ~welcome zone avId [zoneId]: simulate a player switching
            # zones.  avId is an arbitrary number which should
            # probably not match any real avatars.
            avId = int(args[2])
            if len(args) > 3:
                newZoneId = int(args[3])
            else:
                newZoneId = zoneId

            zoneId = mgr.avatarRequestZone(avId, newZoneId)
            response = "%s redirected to %s." % (avId, zoneId)

        elif args[1] == "new":
            # ~welcome new [hoodId]: immediately move the indicated
            # (or current) hood to the New pool.
            if len(args) > 2:
                hoodId = int(args[2])
            else:
                hoodId = zoneId
            response = mgr.makeNew(hoodId)

        elif args[1] == "stable":
            # ~welcome stable [hoodId]: immediately move the indicated
            # (or current) hood to the Stable pool.
            if len(args) > 2:
                hoodId = int(args[2])
            else:
                hoodId = zoneId
            response = mgr.makeStable(hoodId)

        elif args[1] == "remove":
            # ~welcome remove [hoodId]: immediately move the indicated
            # (or current) hood to the Removing pool.
            if len(args) > 2:
                hoodId = int(args[2])
            else:
                hoodId = zoneId
            response = mgr.makeRemoving(hoodId)

        elif args[1] == "check":
            # ~welcome check: check that our record logged-in avatars
            # are actually real avatars; logs out any others.
            removed = mgr.checkAvatars()
            if removed:
                response = "Logged out %s phony avatars." % (len(removed))
            else:
                response = "All avatars real."

        elif args[1] == "parms":
            # ~welcome parms [min stable max]: report or adjust the
            # balancing parameters.
            if len(args) == 5:
                PGminimum = int(args[2])
                PGstable = int(args[3])
                PGmaximum = int(args[4])
                WelcomeValleyManagerAI.PGminimum = PGminimum
                WelcomeValleyManagerAI.PGstable = PGstable
                WelcomeValleyManagerAI.PGmaximum = PGmaximum

            response = "min = %s, stable = %s, max = %s" % (
                WelcomeValleyManagerAI.PGminimum,
                WelcomeValleyManagerAI.PGstable,
                WelcomeValleyManagerAI.PGmaximum)

        else:
            response = "Invalid welcome command: %s" % (args[1])
            
        self.down_setMagicWordResponse(senderId, response)

    def __sortBuildingDist(self, a, b):
        return a[0] - b[0]

    def doBuildings(self, word, av, zoneId, senderId):
        """Handle the ~buildings magic word."""
        streetId = ZoneUtil.getBranchZone(zoneId)

        if word == "~buildings where":
            # "~buildings where": report the distribution of buildings.
            dist = {}
            for sp in self.air.suitPlanners.values():
                if sp.buildingMgr:
                    numActual = len(sp.buildingMgr.getSuitBlocks())
                    if not dist.has_key(numActual):
                        dist[numActual] = []
                    dist[numActual].append(sp.zoneId)

            # Sort the distribution by number of buildings.
            sorted = []
            for tuple in dist.items():
                sorted.append(tuple)
            sorted.sort(self.__sortBuildingDist)
                
            # Now format the distribution into a text response.
            response = ""
            for numActual, zones in sorted:
                if numActual != 0:
                    response += "\n%s: %d" % (zones, numActual)

            if response == "":
                response = "No cog buildings."
            else:
                response = response[1:]
                
        else:
            # "~buildings zoneId" or "~buildings all"

            args=word.split()
            if len(args) > 1:
                if args[1] == "all":
                    streetId = "all"
                else:
                    streetId = int(args[1])

            if streetId == "all":
                numTarget = 0
                numActual = 0
                numTotalBuildings = 0
                numAttempting = 0
                numPerTrack = {}
                numPerHeight = {}
                for sp in self.air.suitPlanners.values():
                    numTarget += sp.targetNumSuitBuildings
                    if sp.buildingMgr:
                        numActual += len(sp.buildingMgr.getSuitBlocks())
                    numTotalBuildings += len(sp.frontdoorPointList)
                    numAttempting += sp.numAttemptingTakeover
                    sp.countNumBuildingsPerTrack(numPerTrack)
                    sp.countNumBuildingsPerHeight(numPerHeight)

                response = "Overall, %d cog buildings (%s, %s) out of %d; target is %d.  %d cogs are attempting takeover." % (
                    numActual, sp.formatNumSuitsPerTrack(numPerTrack),
                    sp.formatNumSuitsPerTrack(numPerHeight),
                    numTotalBuildings, numTarget, numAttempting)

            elif not self.air.suitPlanners.has_key(streetId):
                response = "Street %d is not known." % (streetId)

            else:
                sp = self.air.suitPlanners[streetId]

                numTarget = sp.targetNumSuitBuildings
                if sp.buildingMgr:
                    numActual = len(sp.buildingMgr.getSuitBlocks())
                else:
                    numActual = 0
                numTotalBuildings = len(sp.frontdoorPointList)
                numAttempting = sp.numAttemptingTakeover
                numPerTrack = {}
                numPerHeight = {}
                sp.countNumBuildingsPerTrack(numPerTrack)
                sp.countNumBuildingsPerHeight(numPerHeight)

                response = "Street %d has %d cog buildings (%s, %s) out of %d; target is %d.  %d cogs are attempting takeover." % (
                    streetId, numActual,
                    sp.formatNumSuitsPerTrack(numPerTrack),
                    sp.formatNumSuitsPerTrack(numPerHeight),
                    numTotalBuildings, numTarget, numAttempting)
            
        self.down_setMagicWordResponse(senderId, response)

    def doBuildingPercent(self, word, av, zoneId, senderId):
        """Handle the ~buildingPercent magic word."""
        percent = None
        
        args=word.split()
        if len(args) > 1:
            percent = int(args[1])

        if percent == None:
            response = "Suit building target percentage is %d" % (DistributedSuitPlannerAI.DistributedSuitPlannerAI.TOTAL_SUIT_BUILDING_PCT)
        else:
            DistributedSuitPlannerAI.DistributedSuitPlannerAI.TOTAL_SUIT_BUILDING_PCT = percent
            sp = self.air.suitPlanners.values()[0]
            sp.assignInitialSuitBuildings()
            response = "Reset target percentage to %d" % (percent)

        self.down_setMagicWordResponse(senderId, response)
        
        
    def doCall(self, word, av, zoneId, senderId):
        """Handle the ~call magic word."""
        streetId = ZoneUtil.getBranchZone(zoneId)

        args=word.split()
        name = None
        level = None
        skelecog = None
        revives = None
        
        if len(args) > 1:
            name = args[1]
            if name == 'x':
                name = None
                
        if len(args) > 2:
            level = int(args[2])

        if len(args) > 3:
            skelecog = int(args[3])

        if len(args) > 4:
            revives = int(args[4])

        if not self.air.suitPlanners.has_key(streetId):
            response = "Street %d is not known." % (streetId)

        else:
            sp = self.air.suitPlanners[streetId]
            map = sp.getZoneIdToPointMap()
            canonicalZoneId = ZoneUtil.getCanonicalZoneId(zoneId)
            if not map.has_key(canonicalZoneId):
                response = "Zone %d isn't near a suit point." % (canonicalZoneId)
            else:
                points = map[canonicalZoneId][:]
                suit = sp.createNewSuit([], points,
                                        suitName = name,
                                        suitLevel = level,
                                        skelecog = skelecog,
                                        revives = revives)
                if suit:
                    response = "Here comes %s." % (SuitBattleGlobals.SuitAttributes[suit.dna.name]['name'])
                else:
                    response = "Could not create suit."

        self.down_setMagicWordResponse(senderId, response)

        
    def doBattle(self, word, av, zoneId, senderId):
        """Handle the ~battle magic word."""

        # There's no easy way to find the battle that the caller is
        # near or involved in.  We'll have to walk through all the
        # battles currently in the doId2do map.
        battle = self.__findInvolvedBattle(av.doId)
        if battle == None:
            battle = self.__findBattleInZone(zoneId)

        if battle == None:
            response = "No battle in zone %s." % (zoneId)
        else:
            args = word.split()
            if len(args) < 2:
                response = "Battle %s in state %s" % (battle.doId, battle.fsm.getCurrentState().getName())

            elif args[1] == 'abort':
                battle.abortBattle()
                response = "Battle %s aborted." % (battle.doId)

            else:
                response = "Uknown battle command %s" % (args[1])

        self.down_setMagicWordResponse(senderId, response)

    def __findInvolvedBattle(self, avId):
        """Returns the battle, if any, in which the indicated avatar
        is a participant, or None if the avatar is not involved in any
        battles."""

        for dobj in self.air.doId2do.values():
            if (isinstance(dobj, DistributedBattleBaseAI.DistributedBattleBaseAI)):
                if avId in dobj.toons:
                    return dobj

    def __findBattleInZone(self, zoneId):
        """Returns the battle, if any, in the indicated zoneId, or
        None if no battle is occurring in the indicated zone."""

        for dobj in self.air.doId2do.values():
            if (isinstance(dobj, DistributedBattleBaseAI.DistributedBattleBaseAI)):
                if dobj.zoneId == zoneId:
                    return dobj
        
        


    def doCogInvasion(self, word, av, zoneId, senderId):
        """Handle the ~invasion magic word."""

        invMgr = self.air.suitInvasionManager

        if invMgr.getInvading():
            cogType = invMgr.getCogType()
            numRemaining = invMgr.getNumCogsRemaining()
            cogName = SuitBattleGlobals.SuitAttributes[cogType[0]]['name']
            response = ("Invasion already in progress: %s, %s" % (cogName, numRemaining))
        else:
            args=word.split()
            if len(args) < 3 or len(args) > 4:
                response = "Error: Must specify cogType and numCogs"
            else:
                cogType = args[1]
                numCogs = int(args[2])
                if len(args) == 4:
                    skeleton = int(args[3])
                else:
                    skeleton = 0
                cogNameDict = SuitBattleGlobals.SuitAttributes.get(cogType)
                if cogNameDict:
                    cogName = cogNameDict['name']
                    if skeleton:
                        cogName = TTLocalizer.Skeleton + " " + cogName
                    if invMgr.startInvasion(cogType, numCogs, skeleton):
                        response = ("Invasion started: %s, %s" % (cogName, numCogs))
                    else:
                        response = ("Invasion failed: %s, %s" % (cogName, numCogs))
                else:
                    response = ("Unknown cogType: %s" % (cogType))

        self.down_setMagicWordResponse(senderId, response)

    def stopCogInvasion(self, word, av, zoneId, senderId):
        invMgr = self.air.suitInvasionManager

        if invMgr.getInvading():
            self.air.suitInvasionManager.stopInvasion()
            response = ("Invasion stopped.")
        else:
            response = ("No invasion found.")

        self.down_setMagicWordResponse(senderId, response)
            
    def getCogInvasion(self, word, av, zoneId, senderId):
        invMgr = self.air.suitInvasionManager

        if invMgr.getInvading():
            cogType, skeleton = invMgr.getCogType()
            numRemaining = invMgr.getNumCogsRemaining()
            cogName = SuitBattleGlobals.SuitAttributes[cogType]['name']
            if skeleton:
                cogName = TTLocalizer.Skeleton + " " + cogName
            response = ("Invasion is in progress: %s, %s remaining" % (cogName, numRemaining))
        else:
            response = ("No invasion found.")

        self.down_setMagicWordResponse(senderId, response)

    def startAllFireworks(self, word, av, zoneId, senderId):
        fMgr = self.air.fireworkManager
        fMgr.stopAllShows()
        fMgr.startAllShows(None)
        response = "Shows started in all hoods."
        self.down_setMagicWordResponse(senderId, response)

    def startFireworks(self, word, av, zoneId, senderId):
        fMgr = self.air.fireworkManager
        if fMgr.isShowRunning(zoneId):
            response = ("Show already running in zone: %s" % (zoneId))
        else:
            args=word.split()
            if len(args) == 2:
                showType = int(args[1])
                if fMgr.startShow(zoneId, showType, 1):
                    response = ("Show started, showType: %s" % showType)
                else:
                    response = ("Show failed, showType: %s" % showType)
            else:
                # Default to showType 0
                response = (TTLocalizer.startFireworksResponse \
                    %( ToontownGlobals.NEWYEARS_FIREWORKS, \
                    PartyGlobals.FireworkShows.Summer, \
                    ToontownGlobals.JULY4_FIREWORKS))
        self.down_setMagicWordResponse(senderId, response)

    def stopFireworks(self, word, av, zoneId, senderId):
        if self.air.fireworkManager.stopShow(zoneId):
            response = ("Show stopped, zoneId: %s" % zoneId)
        else:
            response = ("Show stop failed, zoneId: %s" % zoneId)
        self.down_setMagicWordResponse(senderId, response)

    def stopAllFireworks(self, word, av, zoneId, senderId):
        numStopped = self.air.fireworkManager.stopAllShows()
        response = ("Stopped %s firework show(s)" % (numStopped))
        self.down_setMagicWordResponse(senderId, response)

    def doCogs(self, word, av, zoneId, senderId):
        """Handle the ~cogs magic word."""
        streetId = ZoneUtil.getBranchZone(zoneId)
        
        args=word.split()
        firstKeyword = 1

        sync = 0
        fly = 0
        count = -1
        
        if len(args) > 1:
            if args[1] == "all":
                streetId = "all"
                firstKeyword = 2
            else:
                try:
                    streetId = int(args[1])
                    firstKeyword = 2
                except:
                    pass

        # Check for extra keywords.
        for k in range(firstKeyword, len(args)):
            word = args[k]
            if word == "sync":
                sync = 1
            elif word == "fly":
                fly = 1
            elif word == "count=x":
                count = None
            elif word[:6] == "count=":
                count = int(word[6:])
            else:
                self.down_setMagicWordResponse(senderId, "invalid keyword %s" % (word))
                return

        if streetId == "all":
            numTarget = 0
            numActual = 0
            numPerTrack = {}
            sp = None
            for sp in self.air.suitPlanners.values():
                numTarget += sp.calcDesiredNumFlyInSuits() + sp.calcDesiredNumBuildingSuits()
                numActual += sp.numFlyInSuits + sp.numBuildingSuits
                sp.countNumSuitsPerTrack(numPerTrack)
                if sync:
                    sp.resyncSuits()
                if fly:
                    sp.flySuits()
                if count != -1:
                    sp.currDesired = count

            if sp == None:
                response = "No cogs active."
            else:
                response = "Overall, %d cogs (%s); target is %d." % (
                    numActual, sp.formatNumSuitsPerTrack(numPerTrack), numTarget)
                
        elif not self.air.suitPlanners.has_key(streetId):
            response = "Street %d is not known." % (streetId)

        else:
            sp = self.air.suitPlanners[streetId]

            numTarget = sp.calcDesiredNumFlyInSuits() + sp.calcDesiredNumBuildingSuits()
            numActual = sp.numFlyInSuits + sp.numBuildingSuits
            numPerTrack = {}
            sp.countNumSuitsPerTrack(numPerTrack)
            
            if sync:
                sp.resyncSuits()
            if fly:
                sp.flySuits()
            if count != -1:
                sp.currDesired = count
            response = "Street %d has %d cogs (%s); target is %d." % (
                streetId, numActual, sp.formatNumSuitsPerTrack(numPerTrack),
                numTarget)
            
        self.down_setMagicWordResponse(senderId, response)
        

    def doMinigame(self, word, av, zoneId, senderId):
        """Handle the ~minigame magic word: request a particular minigame."""
        args = word.split()
        if len(args) == 1:
            # No minigame parameter specified: clear the request.
            mgRequest = MinigameCreatorAI.RequestMinigame.get(av.doId)
            if mgRequest != None:
                mgId = mgRequest[0]
                del MinigameCreatorAI.RequestMinigame[av.doId]
                response = "Request for minigame %d cleared." % (mgId)
            else:
                response = "Usage: ~minigame [<name|id> [difficulty] [safezone]]"
        else:
            # Try to determine the minigame id, keep flag, and the difficulty
            # and safezone overrides, if any
            name = args[1]
            mgId = None
            mgKeep = 0
            mgDiff = None
            mgSzId = None

            try:
                mgId = int(name)
                numMgs = len(ToontownGlobals.MinigameIDs)
                if mgId < 1 or mgId > numMgs or mgId not in ToontownGlobals.MinigameIDs:
                    response = "minigame ID '%s' is out of range" % mgId
                    mgId = None
            except:
                name = string.lower(name)
                if name[-4:] == "game":
                    name = name[:-4]
                if name[:11] == "distributed":
                    name = name[11:]
                mgId = ToontownGlobals.MinigameNames.get(name)
                if mgId == None:
                    response = "Unknown minigame '%s'." % (name)

            argIndex = 2
            while argIndex < len(args):
                arg = args[argIndex]
                arg = string.lower(arg)
                argIndex += 1

                # it's either a difficulty (float), 'keep',
                # or a safezone (string)

                # is it 'keep'?
                if arg == 'keep':
                    mgKeep = 1
                    continue

                # is it a difficulty?
                try:
                    mgDiff = float(arg)
                    continue
                except:
                    pass

                mgSzId = self.Str2szId.get(arg)
                if mgSzId is not None:
                    continue

                # it's a string, but it's not a safezone.
                response = ("unknown safezone '%s'; use "
                            "tt, dd, dg, mm, br, dl" % arg)
                mgId = None
                break

            if mgId != None:
                # mdId must be the first element
                MinigameCreatorAI.RequestMinigame[av.doId] = (
                    mgId, mgKeep, mgDiff, mgSzId)
                response = "Selected minigame %d" % mgId
                if mgDiff is not None:
                    response += ", difficulty %s" % mgDiff
                if mgSzId is not None:
                    response += ", safezone %s" % mgSzId
                if mgKeep:
                    response += ", keep=true"
                
        self.down_setMagicWordResponse(senderId, response)

    def doTreasures(self, word, av, zoneId, senderId):
        """Handle the ~treasures magic word: fill up the safezone with
        treasures."""
        args = word.split()

        hood = None
        for h in self.air.hoods:
            if h.zoneId == zoneId:
                hood = h
                break

        if hood == None or hood.treasurePlanner == None:
            self.down_setMagicWordResponse(senderId, "Not in a safezone.")
            return

        tp = hood.treasurePlanner
            
        if len(args) == 1:
            # No parameter: report the current treasure count.
            response = "%s treasures." % (tp.numTreasures())

        elif args[1] == "all":
            # ~treasures all: fill up all available treasures.
            tp.placeAllTreasures()
            response = "now %s treasures." % (tp.numTreasures())

        else:
            response = "Invalid treasures command: %s" % (args[1])
            
        self.down_setMagicWordResponse(senderId, response)


    def doEmotes(self, word, av, zoneId, senderId):
        """Handle the ~emote magic word:  turns on/off the specified emotion"""
        args = word.split()
        if len(args) == 1:
            # No parameter specified: clear the request.
            response = "No emote specified."
        elif len(args) == 2:
            # No parameter specified: clear the request.
            response = "Need to specify 0 or 1."
        else:
            emoteId = int(args[1])
            on = int(args[2])
            if emoteId > len(av.emoteAccess) or emoteId < 0:
                response = "Not a valid emote"
            elif on not in [0, 1]:
                response = "Not a valid bit"
            else:
                av.setEmoteAccessId(emoteId, on)
                if on:
                    response = "Emote %d enabled" % emoteId
                else:
                    response = "Emote %d disabled" % emoteId
        self.down_setMagicWordResponse(senderId, response)
            

    def doCatalog(self, word, av, zoneId, senderId):
        """Handle the ~catalog magic word: manage catalogs"""
        now = time.time()
        args = word.split()

        # There may be an optional "after" parameter on many of these
        # commands, which specifies the number of minutes to delay
        # before doing the action.
        afterMinutes = 0
        if "after" in args:
            a = args.index("after")
            afterMinutes = int(args[a + 1])
            del args[a + 1]
            del args[a]
            
        if len(args) == 1:
            # No parameter: report the current catalog.
            duration = (av.catalogScheduleNextTime * 60) - time.time()
            response = "Week %d, next catalog in %s." % \
                       (av.catalogScheduleCurrentWeek,
                        PythonUtil.formatElapsedSeconds(duration))

        elif args[1] == "next":
            # ~catalog next: advance to the next catalog.
            week = av.catalogScheduleCurrentWeek + 1
            self.air.catalogManager.forceCatalog(av, week, afterMinutes)
            response = "Issued catalog for week %s." % (week)

        elif args[1] == "week":
            # ~catalog week n: force to the catalog of the nth week.
            # Note: need to have catalog-skip-seeks set to true to jump
            # more than one week
            week = int(args[2])
            if week > 0:
                self.air.catalogManager.forceCatalog(av, week, afterMinutes)
                response = "Forced to catalog week %s." % (week)
            else:
                response = "Invalid catalog week %s." % (week)

        elif args[1] == "season":
            # ~catalog season mm/dd: regenerate the monthly catalog
            # items as if it were the indicated month and day.
            if len(args) == 3:
                mmdd = args[2].split('/')
                mm = int(mmdd[0])
                dd = int(mmdd[1])
            else:
                mm = int(args[2])
                dd = int(args[3])
                
            self.air.catalogManager.forceMonthlyCatalog(av, mm, dd)
            response = "%s items for %d/%0d." % (len(av.monthlyCatalog), mm, dd)

        elif (args[1] == "clear") or (args[1] == "reset"):
            # ~catalog clear: reset the catalog (and the back catalog)
            # to its initial state.
            av.b_setCatalog(CatalogItemList.CatalogItemList(),
                            CatalogItemList.CatalogItemList(),
                            CatalogItemList.CatalogItemList())
            av.catalogScheduleCurrentWeek = 0
            av.catalogScheduleNextTime = 0
            self.air.catalogManager.deliverCatalogFor(av)
            response = "Catalog reset."

        elif args[1] == "deliver":
            # ~catalog deliver: force the immediate delivery of all
            # of the on-order item(s).

            now = (int)(time.time() / 60 + 0.5)
            deliveryTime = now + afterMinutes

            for item in av.onOrder:
                item.deliveryDate = deliveryTime
            av.onOrder.markDirty()
            av.b_setDeliverySchedule(av.onOrder)
            
            response = "Delivered %s item(s)." % (len(av.onOrder))

        elif args[1] in ["reload", "dump"]:
            # These commands are handled by the client; we ignore them.
            return
            
        else:
            response = "Invalid catalog command: %s" % (args[1])
            
        self.down_setMagicWordResponse(senderId, response)

    def doDna(self, word, av, zoneId, senderId):
        """Handle the ~dna magic word: change your dna"""

        # Strip of the "~dna" part; everything else is parameters to
        # AvatarDNA.updateToonProperties.
        parms = string.strip(word[4:])

        # Get a copy of the avatar's current DNA.
        dna = ToonDNA.ToonDNA(av.dna.makeNetString())

        # Modify it according to the user's parameter selection.
        eval("dna.updateToonProperties(%s)" % (parms))

        av.b_setDNAString(dna.makeNetString())
        response = "%s" % (dna.asTuple(),)

        self.down_setMagicWordResponse(senderId, response)

    def getPet(self, av):
        response = None
        pet = None

        petId = av.getPetId()
        if petId == 0:
            response = "don't have a pet"
        else:
            pet = self.air.doId2do.get(petId)
            if pet is None:
                response = "pet not active, use ~pet"
        return pet, response

    def doBossBattle(self, word, av, zoneId, senderId):
        """Handle the ~bossBattle magic word: manage a final boss
        battle."""

        args = word.split()

        # Find the particular Boss Cog that's in the same zone with
        # the avatar.
        bossCog = None
        for distObj in self.air.doId2do.values():
            if isinstance(distObj, DistributedBossCogAI.DistributedBossCogAI):
                if distObj.zoneId == zoneId:
                    bossCog = distObj
                    break

        if bossCog == None:
            # The caller isn't in a zone with a Boss Cog; use the
            # default Boss zone.

            # In this case, we must accept a dept indicator.
            if len(args) < 2 or args[1] not in SuitDNA.suitDepts:
                response = "Error: Must specify boss dept: s, m, l, c"
                self.down_setMagicWordResponse(senderId, response)
                return

            dept = args[1]
            del args[1]
            deptIndex = SuitDNA.suitDepts.index(dept)
            
            if self.__bossBattleZoneId[deptIndex] == None:
                # Make up a new zone for the battle.
                zoneId = self.air.allocateZone()
                self.__bossBattleZoneId[deptIndex] = zoneId

                bossCog = self.makeBossCog(dept, zoneId)
                bossCog.b_setState('Frolic')
                self.__bossCog[deptIndex] = bossCog

            else:
                bossCog = self.__bossCog[deptIndex]

        response = None
        if len(args) == 1:
            # No parameter: send the avatar to the battle zone.
            self.sendUpdateToAvatarId(av.doId, 'requestTeleport',
                                      ["cogHQLoader", "cogHQBossBattle",
                                       bossCog.getHoodId(),
                                       bossCog.zoneId, 0])

        elif args[1] == "list":
            # ~bossBattle [smlc] list: list the current boss battles
            # underway for the indicated type of suit.
            response = ""
            for bc in DistributedBossCogAI.AllBossCogs:
                if bc.dept == bossCog.dept and bc != bossCog:
                    response += ", %s %s %s" % (bc.zoneId, bc.state, len(bc.involvedToons))
            if response:
                response = response[2:]
            else:
                response = "No boss battles."
            
        elif args[1] == "spy":
            # ~bossBattle spy [smlc] <zoneId>: go visit the indicated
            # boss battle in ghost mode.
            zoneId = int(args[2])
            bc = bossCog
            for bc in DistributedBossCogAI.AllBossCogs:
                if bc.zoneId == zoneId:
                    break
            if bc.zoneId == zoneId:
                self.sendUpdateToAvatarId(av.doId, 'requestTeleport',
                                          ["cogHQLoader", "cogHQBossBattle",
                                           bc.getHoodId(),
                                           bc.zoneId, 0])
                av.b_setGhostMode(2)
            else:
                response = "No boss battle in zone %s" % (zoneId)
                

        elif args[1] == "start":
            # ~bossBattle start: restart the boss battle.
            if not bossCog.hasToons():
                response = "No toons."
            else:
                response = "Elevator started."
                bossCog.acceptNewToons()
                bossCog.b_setState('WaitForToons')

        elif args[1] == "one":
            # ~bossBattle one: straight to battle one.
            if not bossCog.hasToons():
                response = "No toons."
            else:
                response = "Battle one started."
                bossCog.acceptNewToons()
                bossCog.makeBattleOneBattles()
                bossCog.b_setState('BattleOne')

        elif args[1] == "preTwo":
            # ~bossBattle preTwo: preview to battle two.
            if not bossCog.hasToons():
                response = "No toons."
            elif not hasattr(bossCog, 'enterRollToBattleTwo'):
                response = "Battle two preview."
                bossCog.acceptNewToons()
                bossCog.b_setState('PrepareBattleTwo')
            else:
                response = "Battle two preview."
                bossCog.acceptNewToons()
                bossCog.b_setState('RollToBattleTwo')

        elif args[1] == "two":
            # ~bossBattle two: straight to battle two.
            if not bossCog.hasToons():
                response = "No toons."
            else:
                response = "Battle two started."
                bossCog.acceptNewToons()
                if hasattr(bossCog, 'makeBattleTwoBattles'):
                    bossCog.makeBattleTwoBattles()
                bossCog.b_setState('BattleTwo')

        elif args[1] == "preThree":
            # ~bossBattle preThree: preview to battle three.
            if not bossCog.hasToons():
                response = "No toons."
            else:
                response = "Battle three preview."
                bossCog.acceptNewToons()
                bossCog.b_setState('PrepareBattleThree')

        elif args[1] == "three":
            # ~bossBattle three: straight to battle three.
            if not bossCog.hasToons():
                response = "No toons."
            else:
                response = "Battle three started."
                bossCog.acceptNewToons()
                bossCog.b_setState('BattleThree')
                
        elif args[1] == "preFour":
            # ~bossBattle preFour: preview to battle four.
            if not bossCog.hasToons():
                response = "No toons."
            else:
                response = "Battle four preview."
                bossCog.acceptNewToons()
                bossCog.b_setState('PrepareBattleFour')

        elif args[1] == "four":
            # ~bossBattle four: straight to battle four.
            if not bossCog.hasToons():
                response = "No toons."
            else:
                response = "Battle four started."
                bossCog.acceptNewToons()
                bossCog.b_setState('BattleFour')                

        elif args[1] == "victory":
            # ~bossBattle victory: straight to the victory sequence.
            if not bossCog.hasToons():
                response = "No toons."
            else:
                response = "Victory sequence started."
                bossCog.acceptNewToons()
                bossCog.b_setState('Victory')

        elif args[1] == "fsm":
            # ~bossBattle fsm state: directly to named state.
            if len(args) <= 2:
                response = "No state specified."
            else:
                response = "Requested state %s." % (args[2])
                bossCog.b_setState(args[2])

        elif args[1] == "stop":
            # ~bossBattle start: stop the boss battle.
            response = "Battle stopped."
            bossCog.acceptNewToons()
            bossCog.b_setState('Frolic')

        elif args[1] == "hit":
            # ~bossBattle hit [damage]: hit the boss cog during the
            # pie scene.  This will make him dizzy first if he is not
            # already dizzy (as if we successfully lobbed a pie into
            # the undercarriage) and then applies the indicated damage
            # (as if we hit his upper body the indicated number of
            # times).
            
            if len(args) <= 2:
                damage = 1
            else:
                damage = int(args[2])

            ##
            ## this is very suspect .. it is reasigning a internal var(msgSender).. 
            ## it is trying to make the message look like it came from a difrent avatarID 
            ##  to other areas of the code .. ???
            self.air.msgSender = av.doId
            bossCog.magicWordHit(damage, av.doId)

        elif args[1] == "safe":
            # ~bossBattle safe: Ignore hits to the toon during the pie
            # scene.  This magic word is handled by the client.
            pass

        elif args[1] == "avatarEnter":
            # ~bossBattle avatarEnter: Force a call to d_avatarEnter
            #This magic word is handled by the client.
            pass        

        elif args[1] == "stun":
            # ~bossBattle stun: stun all of the goons in the CFO
            # battle.  This magic word is handled by the client.
            pass

        elif args[1] == "destroy":
            # ~bossBattle destroy: destroy all of the goons in the CFO
            # battle.  This magic word is handled by the client.
            pass

        elif args[1] == "reset":
            # ~bossBattle reset: reset all of the goons, cranes, and
            # safes in the CFO sequence.
            bossCog.magicWordReset()

        elif args[1] == "goons":
            # ~bossBattle goons [num]: reset all of the goons and set
            # the number to the indicated value.
            if len(args) > 2:
                bossCog.maxGoons = int(args[2])
            
            bossCog.magicWordResetGoons()
        elif args[1] == "toggleMove":
            # make the ceo toggle doing move attacks
            if hasattr(bossCog, 'toggleMove'):
                doingMoveAttack = bossCog.toggleMove()
                response = "doing move attack = %s"  % doingMoveAttack
            else:
                response = "toggleMove is only for CEO"
        else:
            response = "Invalid bossBattle command: %s" % (args[1])

        if response:
            self.down_setMagicWordResponse(senderId, response)

    def makeBossCog(self, dept, zoneId):
        bossCog = None
        
        if dept == 's':
            bossCog = DistributedSellbotBossAI.DistributedSellbotBossAI(self.air)
            bossCog.generateWithRequired(zoneId)
            bossCog.b_setState('Frolic')

        elif dept == 'm':
            bossCog = DistributedCashbotBossAI.DistributedCashbotBossAI(self.air)
            bossCog.generateWithRequired(zoneId)
            
        elif dept == 'l':
            bossCog = DistributedLawbotBossAI.DistributedLawbotBossAI(self.air)
            bossCog.generateWithRequired(zoneId)
            bossCog.b_setState('Frolic')
        elif dept == 'c':
            bossCog = DistributedBossbotBossAI.DistributedBossbotBossAI(self.air)
            bossCog.generateWithRequired(zoneId)
            bossCog.b_setState('Frolic')            

        else:
            raise StandardError('Not implemented: boss cog %s' % (dept))

        return bossCog
    
        
    def doGarden(self, word, av, zoneId, senderId):
        """Handle the ~garden magic worde."""

        args = word.split()

        response = None
        action = None
        if len(args) == 1:
            # No parameter: change it to usage
            self.down_setMagicWordResponse(
                senderId,
                "Usage:\n~garden action <optional paremeters>\n'~garden help' for more info ")
            return

        action = args[1]
        if action == 'help':
            response = 'start\nclear\nwilt <plot>\nunwilt <plot>\nplant <plantKey> <plot> <water> <growth> <variety>\nclearCarriedSpecials\nclearCollection\ncompleteCollection\nwater <waterLevel>\nshovel <0-3> <shovelSkill>\nrandomBasket\nnuke\nepoch <opt num>\nwateringCan <0-3> <skill>'
        elif action == 'start':
            messenger.send("gardenTest", [senderId])
            response =  "Test Garden Planted"
        elif action == 'clear':
            messenger.send("gardenClear", [senderId])
            response = "Garden Cleared"
        elif action == 'nuke':
            #clear the garden and remove the planters
            #clear the garden started flag
            messenger.send("gardenNuke", [senderId])
            av.b_setGardenStarted(False)
            response = "Garden Nuked"            
        elif action == 'specials':
            #messenger.send("gardenSpecials", [senderId])
            receiver = self.air.doId2do.get(senderId)
            if receiver:
                receiver.giveMeSpecials()
            response = "Garden Specials Added"
        elif action == 'wilt':
            if len(args) >= 3:
                messenger.send("wiltGarden", [senderId, int(args[2])] )
            else:
                messenger.send("wiltGarden", [senderId])
            response = "Garden wilted"
        elif action == 'unwilt':
            if len(args) >= 3:
                messenger.send("unwiltGarden", [senderId, int(args[2])] )
            else:
                messenger.send("unwiltGarden", [senderId])
            response = "Garden unwilted"
        elif action == 'water':
            waterLevel = 1
            if len(args) > 2:
                waterLevel = int(args[2])
            specificHardPoint = -1
            if len(args) > 3:
                specificHardPoint = int(args[3])
            
            messenger.send("waterGarden", [senderId, waterLevel, specificHardPoint] )
            
            response = "water level changed to %d" % waterLevel
        elif action == 'growth':
            waterLevel = 1
            if len(args) > 2:
                waterLevel = int(args[2])
            specificHardPoint = -1
            if len(args) > 3:
                specificHardPoint = int(args[3])
            
            messenger.send("growthGarden", [senderId, waterLevel, specificHardPoint] )
            
            response = "growth level changed to %d" % waterLevel                
        elif action == 'plant':
            type = 0
            plot = 0
            water = 0
            growth = 1
            variety = 0
            if len(args) > 2:
                type = int(args[2])
            if len(args) > 3:
                plot = int(args[3])
            if len(args) > 4:
                water = int(args[4])
            if len(args) > 5:
                growth = int(args[5])
            if len(args) > 6:
                variety = int(args[6])
                
            response = "Planting type=%d plot=%d water=%d growth=%d" % (type,plot,water,growth)
            messenger.send("gardenPlant", [senderId, type, plot, water, growth, variety])            
        elif action == 'clearCarriedSpecials':
            av.b_setGardenSpecials( [])
            response = "Cleared garden specials carried by toon"
        elif action == 'clearCollection':
            av.b_setFlowerCollection( [], [])
            response = "Cleared flower collection."
        elif action == 'completeCollection':
            #from toontown.estate import GardenGlobals
            varietyList = []
            speciesList = []
            flowerSpecies = GardenGlobals.getFlowerSpecies()
            for species in flowerSpecies:
                numVarieties = len(GardenGlobals.getFlowerVarieties(species))
                for variety in range(numVarieties):
                    speciesList.append(species)
                    varietyList.append(variety)
            
            av.b_setFlowerCollection( speciesList, varietyList)
            av.b_setGardenTrophies([])
            response = "Complete flower collection."
        elif action == 'epoch':
            numEpoch = 1
            if len(args) > 2:
                numEpoch = int(args[2])            
            messenger.send("epochGarden", [senderId, numEpoch])
            response = "%d garden epoch has been run" % numEpoch
        elif action == 'shovel':
            if len(args) < 3:
                response = "specify a shovel (0-3)"
            else:
                shovel = 0
                passedShovel = int(args[2])
                if passedShovel >= 0 and \
                   passedShovel < GardenGlobals.MAX_SHOVELS:
                    shovel = passedShovel
                skill =0
                if len(args) >= 4:
                    passedSkill = int(args[3])
                    skill = min (passedSkill, GardenGlobals.ShovelAttributes[shovel]['skillPts'] - 1)
                    skill = max (skill, 0)

                av.b_setShovel(shovel)
                av.b_setShovelSkill(skill)
                response = "Set shovel=%d shovelSkill=%d" % (shovel,skill)
        elif action == 'wateringCan':
            if len(args) < 3:
                response = "specify a watering can (0-3)"
            else:
                wateringCan = 0
                passedWateringCan = int(args[2])
                if passedWateringCan >= 0 and \
                   passedWateringCan < GardenGlobals.MAX_WATERING_CANS:
                    wateringCan = passedWateringCan
                skill =0
                if len(args) >= 4:
                    passedSkill = int(args[3])
                    skill = min (passedSkill, GardenGlobals.WateringCanAttributes[wateringCan]['skillPts'] - 1)
                    skill = max (skill, 0)

                av.b_setWateringCan(wateringCan)
                av.b_setWateringCanSkill(skill)
                response = "Set wateringCan=%d wateringCanSkill=%d" % (wateringCan,skill)                
        elif action == 'randomBasket':
            av.makeRandomFlowerBasket()
            self.down_setMagicWordResponse(senderId, "Created random flower basket")
        elif action == "allTrophies":
            allTrophyList = GardenGlobals.TrophyDict.keys()
            av.b_setGardenTrophies(allTrophyList)
            self.down_setMagicWordResponse(senderId, "All garden trophies")
        else:
            response = 'Invalid garden command.'
        if response:
            self.down_setMagicWordResponse(senderId, response)

    def doGolf(self, word, av, zoneId, senderId):
        """Handle the ~golf magic words."""
        args = word.split()
        response = None        
        action = None
        
        if len(args) == 1:
            # No parameter: change it to usage
            self.down_setMagicWordResponse(
                senderId,
                "Usage:\n~golf action <optional paremeters>\n'~golf help' for more info ")
            return
        
        action = args[1]
        if action == 'help':
            response = 'endHole\nendcourse\ntest\nclearHistory\nMaxHistory'
        elif action == 'drive':
            course = GolfManagerAI.GolfManagerAI().findGolfCourse(senderId)
            response = "drive failed."
            if course:
                result = course.toggleDrivePermission(senderId)
                if result:
                    response = "Press up, down, left&right simultaneously to drive."
                else:
                    response = "Toon is no longer driving."
        elif action == 'endhole' or action == 'endHole':
            course = GolfManagerAI.GolfManagerAI().findGolfCourse(senderId)
            if course:
                holeId, holeDoId = course.abortCurrentHole()
                response = "Aborting holeId %d, doId=%d" % (holeId, holeDoId)
            else:
                response =  "Couldn't find golf course"            
        elif action == 'endcourse' or action == 'endCourse':
            course = GolfManagerAI.GolfManagerAI().findGolfCourse(senderId)
            if course:
                course.setCourseAbort()
                response = "Aborting course %d" % course.doId
            else:
                response =  "Couldn't find golf course"
        elif action == 'test':
            #messenger.send("gardenTest", [senderId])
            response =  "golf test"
            avList = [senderId];
            args = word.split()
            import string
            for i in range(2, len(args)):
                avList.append(string.atoi(args[i]))
            manager = GolfManagerAI.GolfManagerAI()
            #simbase.golfGoer.generateWithRequired(OTPGlobals.UberZone)
            courseId = 0
            zoneId = manager.readyGolfCourse(avList, courseId)
            for avId in avList:
                golfer = simbase.air.doId2do.get(avId)
                if golfer:
                    golfer.sendUpdate("sendToGolfCourse", [zoneId])
                    response = 'sending to golf course %d courseId=%d' % \
                               (zoneId, courseId)
        elif action == 'clearBest':
            response = 'clearBest failed'
            av = simbase.air.doId2do.get(senderId)
            if av:
                emptyHoleBest = [0] * 18
                av.b_setGolfHoleBest(emptyHoleBest)
                emptyCourseBest = [0] * 3
                av.b_setGolfCourseBest(emptyCourseBest)
                response = 'golf best cleared'
        elif action == 'maxBest':
            response = 'maxBest failed'
            av = simbase.air.doId2do.get(senderId)
            if av:
                emptyHoleBest = [1] * 18
                av.b_setGolfHoleBest(emptyHoleBest)
                emptyCourseBest = [1] * 3
                av.b_setGolfCourseBest(emptyCourseBest)
                response = 'golf best maxed'                 
        elif action == 'clearHistory':
            response = 'clearHistory failed'
            emptyHistory = [0] * 18
            av = simbase.air.doId2do.get(senderId)
            if av:
                av.b_setGolfHistory(emptyHistory)
                response = 'golf history cleared'
        elif action == 'maxHistory':
            response = 'maxHistory failed'
            maxHistory = [600] * 18
            av = simbase.air.doId2do.get(senderId)
            if av:
                av.b_setGolfHistory(maxHistory)
                response = 'golf history maxeded'
        elif action == 'midHistory':
            # set it up so that we just need one more course complete to get a cup
            response = 'midHistory failed'
            midHistory = [0] * 18
            midHistory[GolfGlobals.CoursesCompleted] = GolfGlobals.TrophyRequirements[GolfGlobals.CoursesCompleted][1] - 1
            #midHistory = [GolfGlobals.CoursesUnderPar] = GolfGlobals.TrophyRequirements[GolfGlobals.CoursesUnderPar][0]
            midHistory[GolfGlobals.HoleInOneShots] = GolfGlobals.TrophyRequirements[GolfGlobals.HoleInOneShots][0]
            midHistory[GolfGlobals.EagleOrBetterShots] = GolfGlobals.TrophyRequirements[GolfGlobals.EagleOrBetterShots][0]
            midHistory[GolfGlobals.BirdieOrBetterShots] = GolfGlobals.TrophyRequirements[GolfGlobals.BirdieOrBetterShots][0]
            midHistory[GolfGlobals.ParOrBetterShots] = GolfGlobals.TrophyRequirements[GolfGlobals.ParOrBetterShots][0]
            midHistory[GolfGlobals.MultiPlayerCoursesCompleted] = GolfGlobals.TrophyRequirements[GolfGlobals.MultiPlayerCoursesCompleted][0]
            midHistory[GolfGlobals.CourseZeroWins] = GolfGlobals.TrophyRequirements[GolfGlobals.CourseZeroWins][0]
            midHistory[GolfGlobals.CourseOneWins] = GolfGlobals.TrophyRequirements[GolfGlobals.CourseOneWins][0]
            midHistory[GolfGlobals.CourseTwoWins] = GolfGlobals.TrophyRequirements[GolfGlobals.CourseTwoWins][0]                
            
            av = simbase.air.doId2do.get(senderId)
            if av:
                av.b_setGolfHistory(midHistory)
                response = 'golf history midded'
        elif action == 'unlimitedSwing' or action == "us":
            av.b_setUnlimitedSwing(not av.getUnlimitedSwing())
            if av.getUnlimitedSwing():
                response = "Av %s has an unlimited swing" % (av.getDoId())
            else:
                response = "Av %s does NOT have unlimited swings" % (av.getDoId())
        elif action == 'hole':
            import string
            manager = GolfManagerAI.GolfManagerAI()
            if len(args) <= 2:
                # No minigame parameter specified: clear the request.
                holeRequest = GolfManagerAI.RequestHole.get(av.doId)
                if holeRequest != None:
                    holeId =  holeRequest[0]
                    del GolfManagerAI.RequestHole[av.doId]
                    response = "Request for hole %d cleared." % (holeId)
                else:
                    response = "Usage: ~golf hole [<holeId>]"
            else:
                holeId = None
                holeKeep = 0
                name = args[2]
                try:
                    holeId = int(name)
                    if holeId not in GolfGlobals.HoleInfo:
                        response = "hole ID '%s' is out of range" % holeId
                        holeId = None
                except:
                    #name = string.lower(name)
                    #for testHoleId in GolfGlobals.HoleInfo:
                    #    holeName = string.lower(GolfGlobals.getHoleName(testHoleId))
                    #    if name == holeName:
                    #        holeId = testHoleId
                    #        break;
                    if holeId == None:
                        response = "Unknown hole '%s'." % (name)

                argIndex = 2
                while argIndex < len(args):
                    arg = args[argIndex]
                    arg = string.lower(arg)
                    argIndex += 1

                    # it's either a difficulty (float), 'keep',
                    # or a safezone (string)

                    # is it 'keep'?
                    if arg == 'keep':
                        holeKeep = 1
                        continue

                if holeId != None:
                    # hoId must be the first element
                    GolfManagerAI.RequestHole[av.doId] = (
                        holeId, holeKeep)
                    response = "Selected hole %d as 1st hole" % holeId
                    if holeKeep:
                        response += ", keep=true"
                
            
        if response:
            self.down_setMagicWordResponse(senderId, response)

    
    def doMail(self,word, av, zoneId, senderId):
        """Handle mail magic words."""
        args = word.split()
        response = None        
        action = None
        
        if len(args) == 1:
            # No parameter: change it to usage
            self.down_setMagicWordResponse(
                senderId,
                "Usage:\n~mail action <optional paremeters>\n'~mail help' for more info ")
            return
        
        action = args[1]

        if action == 'simple':
            if len(args) < 4:
                response = "~mail simple <recipient avId> 'text'"
            else:
                recipient = int(args[2])
                text = args[3]
                for i in xrange(4, len(args)):
                    text += ' ' + args[i]
                self.air.mailManager.sendSimpleMail(
                    senderId, recipient, text)

        if response:
            self.down_setMagicWordResponse(senderId, response)


    def doParty(self,word, av, zoneId, senderId):
        """Handle mail magic words."""
        args = word.split()
        response = None        
        action = None
        
        if len(args) == 1:
            # No parameter: change it to usage
            self.down_setMagicWordResponse(
                senderId,
                "Available commands: plan, new, update, checkStart, end, debugGrid")
            return
        
        action = args[1]

        if action == 'new':
            if len(args) < 2:
                response = "~party new <inviteeAvId1> <inviteeAvId2> <inviteeAvId3> ... <inviteeAvIdX>"
            else:
                invitees = []
                for i in xrange(2, len(args)):
                    invitees.append( int(args[i]))
                # start the party 1 minute from now
                startTime = datetime.datetime.now(self.air.toontownTimeManager.serverTimeZone) + datetime.timedelta(minutes=-1)
                endTime = startTime + datetime.timedelta(hours=PartyGlobals.DefaultPartyDuration)
                
                from toontown.parties.PartyEditorGrid import PartyEditorGrid

                # Make the avatar rich.
                av.b_setMaxBankMoney(5000)
                av.b_setMoney(av.maxMoney)
                av.b_setBankMoney(av.maxBankMoney)
                
                gridEditor = PartyEditorGrid(None)
                
                # Flip on the Y so it matches the grid in-game.
                gridEditor.grid.reverse()
                
                # Given a center coord (x or y) and a size (w or h), returns a list of indices in
                # in the grid on that axis. (WARNING: Can return invalid indices.)
                def gridComputeRange(centerGrid, size):
                    result = []
                    if size == 1:
                        result = [centerGrid]
                    else:
                        # Need to round with negative values otherwise for center=0, size=3, the 
                        # result will be [1, 0] when we expect [1, 0, -1].
                        #   The range without rounding: range(int(1.5), int(-1.5), -1)
                        #   The range with rounding:    range(int(1.5), int(-2), -1)
                        # Not a problem with center>=2 in this example:
                        #   The range without rounding: range(int(3.5), int(0.5), -1)
                        #   The range with rounding:    range(int(3.5), int(0), -1)
                        result =  range(int(centerGrid + size/2.0),
                                        int(centerGrid - round(size/2.0)), -1)
                    
                    # The result list should be the same size as given.
                    assert len(result) == size, "Bad result range: c=%s s=%s result=%s" % (centerGrid, size, result)
                    
                    return result

                # Returns true if the given space is available centered at x,y with dims w,h.
                def gridIsAvailable(x, y, w, h):
                    for j in gridComputeRange(y, h):
                        if 0 > j or j >= len(gridEditor.grid):
                            return False
                        for i in gridComputeRange(x, w):
                            if 0 > i or i >= len(gridEditor.grid[0]):
                                return False
                            if gridEditor.grid[j][i] == None:
                                return False
                    
                    #print("grid available: xy(%s %s) wh(%s %s)" % (x, y, w, h))
                    return True
                    
                # Returns the first x,y (centered) that has space for w,h.
                def gridGetAvailable(w, h):
                    for y in range(len(gridEditor.grid)):
                        for x in range(len(gridEditor.grid[0])):
                            if gridIsAvailable(x, y, w, h):
                                return x, y
                    return None, None
                
                # Returns True and an x,y (centered) coord for the given space. Marks that space used.
                def gridTryPlace(w, h):
                    x, y = gridGetAvailable(w, h)
                    if not x == None:
                        for j in gridComputeRange(y, h):
                            for i in gridComputeRange(x, w):
                                gridEditor.grid[j][i] = None
                        return True, x, y
                    else:
                        return False, None, None
                
                actualActIdsToAdd = [
                    #PartyGlobals.ActivityIds.PartyJukebox,             # mut.ex: PartyJukebox40
                    PartyGlobals.ActivityIds.PartyCannon,
                    #PartyGlobals.ActivityIds.PartyTrampoline,
                    PartyGlobals.ActivityIds.PartyCatch,
                    #PartyGlobals.ActivityIds.PartyDance,               # mut.ex: PartyDance20
                    PartyGlobals.ActivityIds.PartyTugOfWar,
                    PartyGlobals.ActivityIds.PartyFireworks,
                    PartyGlobals.ActivityIds.PartyClock,
                    PartyGlobals.ActivityIds.PartyJukebox40,
                    PartyGlobals.ActivityIds.PartyDance20,
                    PartyGlobals.ActivityIds.PartyCog,
                    PartyGlobals.ActivityIds.PartyVictoryTrampoline,    # victory party
                ]

                actualDecorIdsToAdd = [
                    PartyGlobals.DecorationIds.BalloonAnvil,
                    PartyGlobals.DecorationIds.BalloonStage,
                    PartyGlobals.DecorationIds.Bow,
                    PartyGlobals.DecorationIds.Cake,
                    PartyGlobals.DecorationIds.Castle,
                    PartyGlobals.DecorationIds.GiftPile,
                    PartyGlobals.DecorationIds.Horn,
                    PartyGlobals.DecorationIds.MardiGras,
                    PartyGlobals.DecorationIds.NoiseMakers,
                    PartyGlobals.DecorationIds.Pinwheel,
                    PartyGlobals.DecorationIds.GagGlobe,
                    #PartyGlobals.DecorationIds.BannerJellyBean,
                    PartyGlobals.DecorationIds.CakeTower,
                    #PartyGlobals.DecorationIds.HeartTarget,        # valentoons
                    #PartyGlobals.DecorationIds.HeartBanner,        # valentoons
                    #PartyGlobals.DecorationIds.FlyingHeart,        # valentoons
                    PartyGlobals.DecorationIds.Hydra,                # 16: victory party
                    PartyGlobals.DecorationIds.BannerVictory,        # 17: victory party
                    PartyGlobals.DecorationIds.CannonVictory,        # 18: victory party
                    PartyGlobals.DecorationIds.CogStatueVictory,     # 19: victory party
                    PartyGlobals.DecorationIds.TubeCogVictory,       # 20: victory party
                    PartyGlobals.DecorationIds.cogIceCreamVictory,   # 21: victory party
                ]

                activities = []
                
                for itemId in actualActIdsToAdd:
                    item = PartyGlobals.ActivityInformationDict[itemId]
                    success, x, y = gridTryPlace(*item['gridsize'])
                    if success:
                        print("~party new ADDED: Activity %s %s at %s, %s" % (itemId, str(item['gridsize']), x, y))
                        # item index, grid x, grid y, heading
                        partyItem = (itemId, x, y, 0)
                        activities.append(partyItem)
                    else:
                        print("~party new SKIPPED: No room for activity %s" % itemId)
                
                decorations = []

                for itemId in actualDecorIdsToAdd:
                    item = PartyGlobals.DecorationInformationDict[itemId]
                    success, x, y = gridTryPlace(*item['gridsize'])
                    if success:
                        print("~party new ADDED: Decoration %s %s at %s, %s" % (itemId, str(item['gridsize']), x, y))
                        # item index, grid x, grid y, heading
                        partyItem = (itemId, x, y, 0)
                        decorations.append(partyItem)
                    else:
                        print("~party new SKIPPED: No room for decoration %s" % itemId)
                
                isPrivate = False
                inviteTheme = PartyGlobals.InviteTheme.Birthday
                self.air.partyManager.addPartyRequest(
                    senderId,
                    startTime.strftime("%Y-%m-%d %H:%M:%S"),
                    endTime.strftime("%Y-%m-%d %H:%M:%S"),
                    isPrivate,
                    inviteTheme,
                    activities,
                    decorations,
                    invitees,
                )
                # force an immediate check of which parties can start
                self.air.partyManager.forceCheckStart()   

        elif action == 'update':
            # simulate this avatarLogging in, which forces invites
            # and party updates from the dbs
            self.air.partyManager.partyUpdate(senderId)

        elif action == 'checkStart':
            # force an immediate check of which parties can start
            self.air.partyManager.forceCheckStart()            

        elif action == 'unreleasedServer':
            newVal = self.air.partyManager.toggleAllowUnreleasedServer()
            response = "Allow Unreleased Server= %s" % newVal

        elif action == 'canBuy':
            newVal = self.air.partyManager.toggleCanBuyParties()
            response = "can buy parties= %s" % newVal

        elif action == 'end':
            response = self.air.partyManager.magicWordEnd(senderId)

        elif action == 'plan':
            response = "Going to party grounds to plan"
            
            # hoodId determines the loading
            hoodId = ToontownGlobals.PartyHood
            
            self.sendUpdateToAvatarId(av.doId, 'requestTeleport',
                          ["safeZoneLoader", "party",
                           hoodId, 0, 0])

        if response:
            self.down_setMagicWordResponse(senderId, response)
