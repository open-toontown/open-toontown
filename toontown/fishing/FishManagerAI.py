from otp.ai.AIBaseGlobal import *
from direct.task import Task
from direct.directnotify import DirectNotifyGlobal
from toontown.quest import Quests
from toontown.toon import NPCToons
import random
from direct.showbase import PythonUtil
from . import FishGlobals
from toontown.toonbase import TTLocalizer
from . import FishBase
from . import FishGlobals
from toontown.hood import ZoneUtil
from toontown.toonbase import ToontownGlobals


class FishManagerAI:

    notify = DirectNotifyGlobal.directNotify.newCategory("FishManagerAI")

    def __init__(self, air):
        self.air = air

    def __chooseItem(self, av, zoneId):
        rodId = av.getFishingRod()
        rand = random.random() * 100.0
        for cutoff in FishGlobals.SortedProbabilityCutoffs:
            if rand <= cutoff:
                itemType = FishGlobals.ProbabilityDict[cutoff]
                self.notify.debug("__chooseItem: %s" % (itemType))
                return itemType
        self.notify.warning("Somehow we did not choose an item, returning boot")
        return FishGlobals.BootItem

    def __chooseFish(self, av, zoneId):
        rodId = av.getFishingRod()
        branchZone = ZoneUtil.getCanonicalBranchZone(zoneId)
        success, genus, species, weight = FishGlobals.getRandomFishVitals(branchZone, rodId)
        return (success, genus, species, weight)

    def recordCatch(self, avId, zoneId, pondZoneId):
        # Chooses an item to find in the water.  Returns a (code,
        # item) pair where code indicates the type of item, and item
        # is the particular item id.
        av = self.air.doId2do.get(avId)
        if not av:
            return (None, None)

        #check to see if bingo cheating is turned on
        if av.bingoCheat:
            # Fished up a boot
            self.notify.debug("av: %s caught the boot" % (avId))
            rodId = av.getFishingRod()
            self.air.writeServerEvent("fishedBoot", avId, "%s|%s" % (rodId, zoneId))
            self.air.handleAvCatch(avId, pondZoneId, FishGlobals.BingoBoot)
            return (FishGlobals.BootItem, None)

        # First, check for a quest item.
        item = self.air.questManager.findItemInWater(av, zoneId)
        if item:
            self.notify.debug("av: %s caught quest item: %s" % (avId, item))
            # Write to server logs
            rodId = av.getFishingRod()
            self.air.writeServerEvent("fishedQuestItem", avId, "%s|%s|%s" % (rodId, zoneId, item))
            return (FishGlobals.QuestItem, item)

        # Ok, no quest item, now let's see what you pull out
        # Could be a fish, jellybeans, a boot, shirts, etc
        itemType = self.__chooseItem(av, zoneId)
        
        if itemType == FishGlobals.FishItem:
            # Choose which fish (this may come back with the boot too)
            success, genus, species, weight = self.__chooseFish(av, zoneId)
            if success:
                # Ok, you found a fish
                self.air.handleAvCatch(avId, pondZoneId, (genus, species))
                fish = FishBase.FishBase(genus, species, weight)
                # do you already have one like it?
                inTank = av.fishTank.hasFish(genus, species)
                if inTank:
                    # TODO: This is a bit wasteful to loop through the fish tank twice
                    hasBiggerAlready = av.fishTank.hasBiggerFish(genus, species, weight)
                else:
                    # If we already know it is not in the tank, no sense searching around
                    # to see if we have one bigger
                    hasBiggerAlready = 0
                added = av.addFishToTank(fish)
                if added:
                    self.notify.debug("av: %s caught fish: %s %s %s" %
                                      (avId, genus, species, weight))
                    # See what the collect result will be
                    # NOTE: this does not actually collect the fish. The NPC
                    # fisherman does that work
                    collectResult = av.fishCollection.getCollectResult(fish)
                    
                    # Catch a fish, get a heal
                    # Nope - changed my mind. Fishing does not heal anymore
                    # It is strange to be able to heal out on the streets, and while
                    # you are in the playground you heal anyways
                    # av.toonUp(FishGlobals.HealAmount)
                    
                    # Write to server logs
                    rodId = av.getFishingRod()
                    self.air.writeServerEvent("fishedFish", avId, "%s|%s|%s|%s|%s|%s" %
                                              (rodId, zoneId, genus, species, weight, fish.getValue()))
                    if collectResult == FishGlobals.COLLECT_NO_UPDATE:
                        return (FishGlobals.FishItem, fish)
                    elif collectResult == FishGlobals.COLLECT_NEW_ENTRY:
                        # If it is not in our tank also, it really is a new entry
                        if not inTank:
                            return (FishGlobals.FishItemNewEntry, fish)
                        # Ok, we already have one in our tank. If we do not already
                        # have a bigger one it is a new record
                        elif not hasBiggerAlready:
                            return (FishGlobals.FishItemNewRecord, fish)
                        # Otherwise, just a normal catch
                        else:
                            return (FishGlobals.FishItem, fish)
                    elif collectResult == FishGlobals.COLLECT_NEW_RECORD:
                        # If we have one of these in our tank, check to see if
                        # it is bigger. If the one we already have in our tank is bigger
                        # then we do not get a new record set.
                        if hasBiggerAlready:
                            # No new record, we already have this fish
                            # beat, but it is still in our tank - we have
                            # not sold it yet so it is not in our
                            # collection.
                            return (FishGlobals.FishItem, fish)
                        else:
                            return (FishGlobals.FishItemNewRecord, fish)
                    else:
                        self.notify.error("unrecognized collectResult: %s" % (collectResult))
                else:
                    self.notify.debug("av: %s is over the tank limit" % (avId))
                    return (FishGlobals.OverTankLimit, None)
            else:
                # If you did not choose a fish, you get the boot
                self.notify.debug("av: %s tried to catch fish, but got the boot" % (avId))
                rodId = av.getFishingRod()
                self.air.writeServerEvent("fishedBoot", avId, "%s|%s" % (rodId, zoneId))
                self.air.handleAvCatch(avId, pondZoneId, FishGlobals.BingoBoot)
                return (FishGlobals.BootItem, None)
        elif itemType == FishGlobals.BootItem:
            # Fished up a boot
            self.notify.debug("av: %s caught the boot" % (avId))
            rodId = av.getFishingRod()
            self.air.writeServerEvent("fishedBoot", avId, "%s|%s" % (rodId, zoneId))
            self.air.handleAvCatch(avId, pondZoneId, FishGlobals.BingoBoot)
            return (FishGlobals.BootItem, None)
        elif itemType == FishGlobals.JellybeanItem:
            # Fished up some jellybeans
            rodId = av.getFishingRod()
            jellybeanAmount = FishGlobals.Rod2JellybeanDict[rodId]
            av.addMoney(jellybeanAmount)
            self.notify.debug("av: %s caught %s jellybeans" % (avId, jellybeanAmount))
            self.air.writeServerEvent("fishedJellybeans", avId, "%s|%s|%s" % (rodId, zoneId, jellybeanAmount))
            return (FishGlobals.JellybeanItem, jellybeanAmount)
        
    def creditFishTank(self, av):
        """
        Do all the work of selling the tank and updating the collection.
        Also updates your trophy status and maxHP if needed.
        Returns 1 if you earned a trophy, 0 if you did not.
        """
        assert(self.notify.debug("creditFishTank av: %s is selling all fish" % (av.getDoId())))
        oldBonus = int(len(av.fishCollection)/FishGlobals.FISH_PER_BONUS)

        # give the avatar jellybeans in exchange for his fish
        value = av.fishTank.getTotalValue()
        av.addMoney(value)

        # update the avatar collection for each fish
        for fish in av.fishTank.fishList:
            av.fishCollection.collectFish(fish)
            
        # clear out the fishTank
        av.b_setFishTank([],[],[])
        
        # update the collection in the database
        av.d_setFishCollection(*av.fishCollection.getNetLists())
        
        newBonus = int(len(av.fishCollection)/FishGlobals.FISH_PER_BONUS)
        if newBonus > oldBonus:
            self.notify.info("avatar %s gets a bonus: old: %s, new: %s" % (av.doId, oldBonus, newBonus))
            oldMaxHp = av.getMaxHp()
            newMaxHp = min(ToontownGlobals.MaxHpLimit, oldMaxHp + newBonus - oldBonus)
            av.b_setMaxHp(newMaxHp)
            # Also, give them a full heal
            av.toonUp(newMaxHp)
            # update the av's trophy list
            newTrophies = av.getFishingTrophies()
            trophyId = len(newTrophies)
            newTrophies.append(trophyId)
            av.b_setFishingTrophies(newTrophies)
            self.air.writeServerEvent("fishTrophy", av.doId, "%s" % (trophyId))
            return 1
        else:
            assert(self.notify.debug("avatar %s no bonus: old: %s, new: %s" % (av.doId, oldBonus, newBonus)))
            return 0
