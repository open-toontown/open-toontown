from otp.ai.AIBaseGlobal import *
from direct.task import Task
from direct.directnotify import DirectNotifyGlobal
from . import Quests
from toontown.toon import NPCToons
import random

"""
TODO: (done, tested)
 + + Jellybean reward
 + + Max Jellybean reward
 + + Quest combos
 + + Required and optional reward pool
 + + Quest page class
 + + Integrate chat next buttons
 + + Quest multiple choice AI
 + + Quest multiple choice gui
 + + Quest multiple choice choosing
 + + clean up NPC Toon dicts
 + + Stolen item list
 + + Stolen item quests
 + + Stolen item integration into reward panel
 + + Stolen item integration into battle
 + + Trolley quest
 + + Make friend quest
 + + sticker book reward
 + + non-rejectable quest tiers
 + + customize how many quests to choose from
 + + gui movies in quest movies
 + + Choose track access quest
 + + Track access partial rewards
 + + Toon HQ integration
 + + Multiple NPCs indoors
 + + Integrate quest page artwork
 + + Cog logos for posters
 + + Trolley reward in playground
 - - Dynamic timeout lengths based on movie

 New Track order:
 Choice 1: Sound or Heal
 Choice 2: Drop or Lure
 Choice 3: 1' or Trap
 Choice 4: 2' or 3'
"""

class QuestManagerAI:

    notify = DirectNotifyGlobal.directNotify.newCategory("QuestManagerAI")

    # Immediately complete all quests and all visits are to ToonHQ
    QuestCheat = simbase.config.GetBool("quest-cheat", 0)

    # table of requests for quests from specific avatars
    NextQuestDict = {}

    def __init__(self, air):
        self.air = air

    def requestInteract(self, avId, npc):
        self.notify.debug("requestInteract: avId: %s npcId: %s" % (avId, npc.getNpcId()))
        av = self.air.doId2do.get(avId)

        # Sanity check
        if av is None:
            self.notify.warning("some toon did a requestInteract but is not here: %s" % (avId))
            return

        # If this NPC is busy, free the avatar
        if npc.isBusy():
            self.notify.debug("freeing avatar %s because NPC is busy" % (avId))
            npc.freeAvatar(avId)
            return

       # handle unusual cases such as NPC specific quests
        # interactionComplete = self.handleSpecialCases(avId, npc)

        # if interactionComplete:
            # return

        # First, see if any quests are completed before checking for incomplete
        # Since the ToonHQ could match multiple quests on the av list, we need
        # to prioritize what they give their attention to first. I think it
        # makes sense for them to clear complete quests first
        for questDesc in av.quests:

            # Sanity check for rogue quests
            if not Quests.questExists(questDesc[0]):
                av.removeAllTracesOfQuest(questDesc[0], questDesc[3])
                self.rejectAvatar(av, npc)
                return

            if (self.isQuestComplete(av, npc, questDesc) == Quests.COMPLETE):
                self.completeQuest(av, npc, questDesc[0])
                return

        needsQuestButNoneLeft = 0
        if (self.needsQuest(av) and npc.getGivesQuests()):
            # bestQuests is a nested list of [questId, rewardId, toNpcId] lists
            quests = self.getNextQuestIds(npc, av)
            if quests:
                if (Quests.getNumChoices(av.getRewardTier()) == 0):
                    assert(len(quests) == 1) # There should only be one
                    if npc.getHq():
                        fromNpcId = Quests.ToonHQ
                    else:
                        fromNpcId = npc.getNpcId()
                    self.assignQuest(avId, fromNpcId, *quests[0])
                    npc.assignQuest(av.getDoId(), *quests[0])
                else:
                    # if this avatar requested a quest, include it
                    if avId in self.NextQuestDict:
                        questId = self.NextQuestDict[avId]
                        # if it's already in the list of quests,
                        # we're all set
                        ids = []
                        for q in quests:
                            ids.append(q[0])
                        if questId not in ids:
                            # add the quest as the first choice
                            questDesc = Quests.QuestDict[questId]
                            reward = questDesc[Quests.QuestDictRewardIndex]
                            toNpcId = questDesc[Quests.QuestDictToNpcIndex]
                            if reward is Quests.Any:
                                reward = 604 # some jbs
                            if toNpcId is Quests.Any:
                                toNpcId = Quests.ToonHQ
                            quests[0] = [questId, reward, toNpcId]

                    npc.presentQuestChoice(av.getDoId(), quests)
                return
            else:
                needsQuestButNoneLeft = 1

        # Now see if this npc has any incomplete quests with av
        questDesc = self.hasQuest(av, npc)
        if questDesc:
            completeStatus = self.isQuestComplete(av, npc, questDesc)
            questId, fromNpcId, toNpcId, rewardId, toonProgress = questDesc
            self.incompleteQuest(av, npc, questId, completeStatus, toNpcId)
            return
        else:
            if needsQuestButNoneLeft:
                # If they have quests, tell them to finish their tier
                if av.quests:
                    self.rejectAvatarTierNotDone(av, npc)
                # If they do not have any quests, advance their tier
                else:
                    if self.incrementReward(av):
                        # quests is a nested list of [questId, rewardId, toNpcId] lists
                        quests = self.getNextQuestIds(npc, av)
                        if quests:
                            if (Quests.getNumChoices(av.getRewardTier()) == 0):
                                assert(len(quests) == 1) # There should only be one
                                if npc.getHq():
                                    fromNpcId = Quests.ToonHQ
                                else:
                                    fromNpcId = npc.getNpcId()
                                self.assignQuest(avId, fromNpcId, *quests[0])
                                npc.assignQuest(av.getDoId(), *quests[0])
                            else:
                                npc.presentQuestChoice(av.getDoId(), quests)
                            return
                    else:
                        # No more quests, sorry
                        # TODO: put some more meaningful dialog here
                        self.rejectAvatar(av, npc)
                return
            else:
                # Avatar does not need a quest, goodbye
                self.rejectAvatar(av, npc)
                return

    def handleSpecialCases(self, avId, npc):
        """ handle unusual cases such as NPC specific quests"""

        av = self.air.doId2do.get(avId)

        if npc.getNpcId() == 2018:
            # See if this npc has the TIP quest
            for questDesc in av.quests:
                # Do not use doId, use the NpcId because the doId is different across shards
                questId = questDesc[0]
                if (questId == 103):
                    completeStatus = self.isQuestComplete(av, npc, questDesc)
                    questId, fromNpcId, toNpcId, rewardId, toonProgress = questDesc
                    self.incompleteQuest(av, npc, questId, completeStatus, toNpcId)
                    return 1

            if self.needsQuest(av):
                self.assignQuest(avId, npc.npcId, 103, Quests.QuestDict[103][5], Quests.QuestDict[103][4])
                npc.assignQuest(avId, 103, Quests.QuestDict[103][5], Quests.QuestDict[103][4])
                return 1

        return 0

    def rejectAvatar(self, av, npc):
        self.notify.debug("rejecting avatar: avId: %s" % (av.getDoId()))
        npc.rejectAvatar(av.getDoId())
        return

    def rejectAvatarTierNotDone(self, av, npc):
        self.notify.debug("rejecting avatar because tier not done: avId: %s" % (av.getDoId()))
        npc.rejectAvatarTierNotDone(av.getDoId())
        return

    def hasQuest(self, av, npc):
        # Check if this avId has a quest on this npcId
        for questDesc in av.quests:
            # Do not use doId, use the NpcId because the doId is different across shards
            questId = questDesc[0]
            fromNpcId = questDesc[1]
            toNpcId = questDesc[2]
            # If the fromNpc that gave you the quest is involved, or
            # if you have a toNpc then return this questId
            if (fromNpcId == npc.getNpcId()):
                self.notify.debug("hasQuest: found quest: %s avId: %s fromNpcId: %s" %
                                  (questId, av.getDoId(), fromNpcId))
                return questDesc
            elif (toNpcId == npc.getNpcId()):
                # If the quest has this npc as the toNpc, then we are done
                self.notify.debug("hasQuest: found quest with toNpc: %s avId: %s toNpcId: %s" %
                                  (questId, av.getDoId(), toNpcId))
                return questDesc
            elif (toNpcId == Quests.Any):
                # If the quest has "any" as the toNpc, than this guy will do
                self.notify.debug("hasQuest: found quest with any toNpc: %s avId: %s toNpcId: %s" %
                                  (questId, av.getDoId(), toNpcId))
                return questDesc
            elif ((toNpcId == Quests.ToonHQ) and (npc.getHq())):
                # If the quest is for the HQ, and this toon has HQ powers, its a match
                self.notify.debug("hasQuest: found quest with HQ toNpc: %s avId: %s toNpcId: %s" %
                                  (questId, av.getDoId(), toNpcId))
                return questDesc
            elif ((toNpcId == Quests.ToonTailor) and (npc.getTailor())):
                # If the quest is for a tailor, and this toon is a tailor, its a match
                self.notify.debug("hasQuest: found quest with Tailor toNpc: %s avId: %s toNpcId: %s" %
                                  (questId, av.getDoId(), toNpcId))
                return questDesc
        self.notify.debug("hasQuest: did not find quest for avId: %s npcId: %s" %
                          (av.getDoId(), npc.getNpcId()))
        return None

    def isQuestComplete(self, av, npc, questDesc):
        # The quest in question
        quest = Quests.getQuest(questDesc[0])
        if quest == None:
            return 0
        self.notify.debug("isQuestComplete: avId: %s, quest: %s" %
                          (av.getDoId(), quest))
        return quest.getCompletionStatus(av, questDesc, npc)

    def completeQuest(self, av, npc, questId):
        self.notify.info("completeQuest: avId: %s, npcId: %s, questId: %s" %
                          (av.getDoId(), npc.getNpcId(), questId))

        # If this is a track choice, we do not actually complete the quest,
        # We present the track choice gui. This can be cancelled which will
        # not complete the quest.
        questClass = Quests.getQuestClass(questId)
        if questClass == Quests.TrackChoiceQuest:
            self.notify.debug("completeQuest: presentTrackChoice avId: %s, npcId: %s, questId: %s" %
                              (av.getDoId(), npc.getNpcId(), questId))
            quest = Quests.getQuest(questId)
            tracks = quest.getChoices()
            npc.presentTrackChoice(av.getDoId(), questId, tracks)
            # Do not increment reward until avatar has chosen track
            # This happens in avatarChoseTrack
            return

        # If this is a deliver gag quest, we need to actually remove the
        # gags delivered from the player's inventory
        if questClass == Quests.DeliverGagQuest:
            self.notify.debug("completeQuest: presentTrackChoice avId: %s, npcId: %s, questId: %s" %
                              (av.getDoId(), npc.getNpcId(), questId))
            # Use the items from the inventory now
            quest = Quests.getQuest(questId)
            track, level = quest.getGagType()
            for i in range(0, quest.getNumGags()):
                av.inventory.useItem(track, level)
            av.d_setInventory(av.inventory.makeNetString())


        # See if this quest is part of a multiquest. If it is, we assign
        # the next part of the multiquest.
        nextQuestId, nextToNpcId = Quests.getNextQuest(questId, npc, av)
        eventLogMessage = "%s|%s|%s|%s" % (
            questId, npc.getNpcId(), questClass.__name__, nextQuestId)

        if nextQuestId == Quests.NA:
            rewardId = Quests.getAvatarRewardId(av, questId)
            # Update the toon with the reward
            reward = Quests.getReward(rewardId)

            # Clothing quests should have been handled by the Tailor.
            # Just to make sure
            if (reward.getType() == Quests.ClothingTicketReward):
                self.notify.warning("completeQuest: rogue ClothingTicketReward avId: %s, npcId: %s, questId: %s" %
                                    (av.getDoId(), npc.getNpcId(), questId))
                npc.freeAvatar(av.getDoId())
                return

            # Nope, this is the end, dish out the reward
            av.removeQuest(questId)
            # TODO: put this in the movie
            reward.sendRewardAI(av)
            # Full heal for completing a quest
            av.toonUp(av.maxHp)
            # Tell the npc to deliver the movie which will
            # complete the quest, display the reward, and do nothing else
            npc.completeQuest(av.getDoId(), questId, rewardId)
            # Bump the reward
            self.incrementReward(av)

            eventLogMessage += "|%s|%s" % (
                reward.__class__.__name__, reward.getAmount())

        else:
            # Full heal for completing part of a multistage quest
            av.toonUp(av.maxHp)
            # The user is not presented with a choice here
            av.removeQuest(questId)
            nextRewardId = Quests.getQuestReward(nextQuestId, av)
            if npc.getHq():
                fromNpcId = Quests.ToonHQ
            else:
                fromNpcId = npc.getNpcId()
            self.assignQuest(av.getDoId(), fromNpcId, nextQuestId, nextRewardId, nextToNpcId, startingQuest = 0)
            npc.assignQuest(av.getDoId(), nextQuestId, nextRewardId, nextToNpcId)
            eventLogMessage += "|next %s" % (nextQuestId)

        self.air.writeServerEvent('questComplete', av.getDoId(), eventLogMessage)

    def incompleteQuest(self, av, npc, questId, completeStatus, toNpcId):
        self.notify.debug("incompleteQuest: avId: %s questId: %s" %
                          (av.getDoId(), questId))
        npc.incompleteQuest(av.getDoId(), questId, completeStatus, toNpcId)
        return

    def needsQuest(self, av):
        # Return 0 if this avatar does not need a new quest, 1 if he does
        quests = av.quests
        carryLimit = av.getQuestCarryLimit()
        if (len(quests) >= carryLimit):
            self.notify.debug("needsQuest: avId: %s is already full with %s/%s quest(s)" %
                              (av.getDoId(), len(quests), carryLimit))
            return 0
        else:
            self.notify.debug("needsQuest: avId: %s only has %s/%s quest(s), needs another" %
                              (av.getDoId(), len(quests), carryLimit))
            return 1

    def getNextQuestIds(self, npc, av):
        # Return the quest id, reward id for the next quest
        # Return None, None if the search fails for some reason
        return Quests.chooseBestQuests(av.getRewardTier(), npc, av)

    def incrementReward(self, av):
        # See if we finished a tier
        rewardTier = av.getRewardTier()
        # Make sure all the rewards have been handed out and
        # Make sure we have completed them all
        # First, make sure that the list is at least as big as the number of rewards
        # Then, make sure we have completed them all
        # Then, make sure all the rewards in the tier are in our history
        rewardHistory = av.getRewardHistory()[1]
        if (
            # We cannot do this short-circuit test anymore because having
            # cog suit parts counts as a reward in cashbot
            # HQ. Unfortunately we are losing a pretty nice optimization
            # here. TODO: revisit and optimize.
            # (len(rewardHistory) >= Quests.getNumRewardsInTier(rewardTier)) and

            # We cannot do this because they might still be working on a few
            # optional quests from the old tier.
            # (len(av.quests) == 0) and

            # Make sure they have all the required rewards
            (Quests.avatarHasAllRequiredRewards(av, rewardTier)) and

            # Make sure they are not still working on required rewards
            (not Quests.avatarWorkingOnRequiredRewards(av))
            ):

            if not Quests.rewardTierExists(rewardTier+1):
                self.notify.info("incrementReward: avId %s, at end of rewards" %
                                  (av.getDoId()))
                return 0

            rewardTier += 1
            self.notify.info("incrementReward: avId %s, new rewardTier: %s" %
                              (av.getDoId(), rewardTier))

            # If we have just moved on to the next tier, blow away the
            # old history, which is no longer needed.
            av.b_setQuestHistory([])
            av.b_setRewardHistory(rewardTier, [])

            # The above will clear the quest history the *first* time
            # we cross into the next tier.  There may still be some
            # quest id's hiding behind visit quests that belong to the
            # previous tier; these will find their way onto the quest
            # history when we eventually reveal them, but they will
            # still be associated with the previous tier.  This does
            # no harm, so we won't worry about it; but it does mean
            # that the questHistory list is not guaranteed to only
            # list quests on the current tier.  It is simply
            # guaranteed to list all the completed and in-progress
            # quests on the current tier, with maybe one or two others
            # thrown in.
            return 1
        else:
            self.notify.debug("incrementReward: avId %s, not ready for new tier" %
                              (av.getDoId()))
            return 0


    def avatarCancelled(self, avId):
        # This is a message that came from the client, through the NPCToonAI.
        # It is in response to the avatar picking from a multiple choice menu
        self.notify.debug("avatarCancelled: avId: %s" % (avId))
        return

    def avatarChoseTrack(self, avId, npc, questId, trackId):
        # This is a message that came from the client, through the NPCToonAI.
        # It is in response to the avatar picking from a multiple choice menu
        # of track options, along with a cancel option
        self.notify.info("avatarChoseTrack: avId: %s trackId: %s" % (avId, trackId))
        av = self.air.doId2do.get(avId)
        if av:
            # Remove the track choice quest
            av.removeQuest(questId)
            # Update the toon with the reward
            rewardId = Quests.getRewardIdFromTrackId(trackId)
            reward = Quests.getReward(rewardId)
            reward.sendRewardAI(av)
            # Tell the npc to deliver the movie which will
            # complete the quest, display the reward, and do nothing else
            npc.completeQuest(av.getDoId(), questId, rewardId)
            self.incrementReward(av)
        else:
            self.notify.warning("avatarChoseTrack: av is gone.")

    def avatarChoseQuest(self, avId, npc, questId, rewardId, toNpcId):
        # This is a message that came from the client, through the NPCToonAI.
        # It is in response to the avatar picking from a multiple choice menu
        # of quest options, along with a cancel option
        self.notify.debug("avatarChooseQuest: avId: %s questId: %s" % (avId, questId))
        av = self.air.doId2do.get(avId)
        if av:
            if npc.getHq():
                fromNpcId = Quests.ToonHQ
            else:
                fromNpcId = npc.getNpcId()
            self.assignQuest(avId, fromNpcId, questId, rewardId, toNpcId)
            npc.assignQuest(avId, questId, rewardId, toNpcId)
            # Do not increment the reward until the quest is completed
        else:
            self.notify.warning("avatarChoseQuest: av is gone.")

    def assignQuest(self, avId, npcId, questId, rewardId, toNpcId, startingQuest = 1):
        self.notify.info("assignQuest: avId: %s npcId: %s questId: %s rewardId: %s toNpcId: %s startingQuest: %s" %
                          (avId, npcId, questId, rewardId, toNpcId, startingQuest))
        # assign quest to avatar
        # A quest is a list with (questId, npcId, toNpcId, rewardId, progress)
        av = self.air.doId2do.get(avId)
        if av:
            if startingQuest:
                # Since the first parts or multipart quests have NA for their
                # rewardIds, we need to get the final reward of this quest by searching
                # down the chain. If this questId is not the start of a multipart
                # quest, finalRewardId will come back None, and addQuest will handle it
                if rewardId == Quests.NA:
                    finalRewardId = Quests.getFinalRewardId(questId)
                else:
                    # Do not count the end of multipart quests, even though they
                    # have a valid rewardId. That rewardId would have been counted
                    # when the initial quest was given out
                    if not Quests.isStartingQuest(questId):
                        finalRewardId = None
                    else:
                        finalRewardId = rewardId
            # If this was not handed out as a starting quest, make sure you do not
            # count the reward twice
            else:
                finalRewardId = None
            # 0 for initial progress
            initialProgress = 0
            # To make it easy for testing purposes.
            # This should never be on in production
            if self.QuestCheat:
                # Quest is already compelte
                initialProgress = 1000
                # Clothing quests must be handled by the Tailor.
                if ((rewardId == Quests.NA) or
                    (Quests.getRewardClass(rewardId) != Quests.ClothingTicketReward)):
                    # Visit npc is the HQ
                    toNpcId = Quests.ToonHQ
            if Quests.isLoopingFinalTier(av.getRewardTier()):
                # Do not record the history if this is the final looping tier
                recordHistory = 0
            else:
                recordHistory = 1
            av.addQuest((questId, npcId, toNpcId, rewardId, initialProgress), finalRewardId, recordHistory)
            # if this was a requested quest, clear it
            if self.NextQuestDict.get(avId) == questId:
                del self.NextQuestDict[avId]
        else:
            self.notify.warning("assignQuest: avatar not found: avId: %s" % (avId))
        return


    def toonDefeatedFactory(self, av, location, avList):
        # factory is telling us that this avatar just defeated it.
        # see if this toon has a quest on this factory. If so,
        # update the progress.
        avQuests = av.quests
        avId = av.getDoId()
        changed = 0

        for questDesc in avQuests:
            quest = Quests.getQuest(questDesc[0])
            num = quest.doesFactoryCount(avId, location, avList)
            if num > 0:
                questDesc[4] += num
                changed = 1

        # Now send the quests back to the avatar if the status changed
        if changed:
            self.notify.debug("toonDefeatedFactory: av made progress")
            av.b_setQuests(avQuests)
        else:
            self.notify.debug("toonDefeatedFactory: av made NO progress")

    def toonDefeatedStage(self, av, location, avList):
        self.notify.debug("toonDefeatedStage: av made NO progress")

    def toonRecoveredCogSuitPart(self, av, location, avList):
        avQuests = av.quests
        avId = av.getDoId()
        changed = 0

        for questDesc in avQuests:
            quest = Quests.getQuest(questDesc[0])
            num = quest.doesCogPartCount(avId, location, avList)
            if num > 0:
                questDesc[4] += num
                changed = 1

        # Now send the quests back to the avatar if the status changed
        if changed:
            self.notify.debug("toonRecoveredCogSuitPart: av made progress")
            av.b_setQuests(avQuests)
        else:
            self.notify.debug("toonRecoveredCogSuitPart: av made NO progress")

    def toonDefeatedMint(self, av, mintId, avList):
        # mint is telling us that this avatar just defeated it.
        # see if this toon has a quest on this mint. If so,
        # update the progress.
        avQuests = av.quests
        avId = av.getDoId()
        changed = 0

        for questDesc in avQuests:
            quest = Quests.getQuest(questDesc[0])
            num = quest.doesMintCount(avId, mintId, avList)
            if num > 0:
                questDesc[4] += num
                changed = 1

        # Now send the quests back to the avatar if the status changed
        if changed:
            self.notify.debug("toonDefeatedMint: av made progress")
            av.b_setQuests(avQuests)
        else:
            self.notify.debug("toonDefeatedMint: av made NO progress")

    def toonDefeatedStage(self, av, stageId, avList):
        self.notify.debug("toonDefeatedStage")
        pass

    def toonKilledBuilding(self, av, track, difficulty, numFloors, zoneId, avList):
        # This is the battle notifying us that a toon has defeated a
        # building.  See if this toon has a quest on this building.
        # If so, update the progress.
        avQuests = av.quests
        avId = av.getDoId()
        changed = 0

        #self.notify.debug("toonKilledBuilding: avId: %s, track: %s, diff: %s, numFloors: %s, zoneId: %s" %
        #                  (avId, track, difficulty, numFloors, zoneId))
        for questDesc in avQuests:
            questClass = Quests.getQuestClass(questDesc[0])
            if ((questClass == Quests.BuildingQuest) or
                (questClass == Quests.BuildingNewbieQuest)):
                quest = Quests.getQuest(questDesc[0])
                matchedTrack = ((quest.getBuildingTrack() == Quests.Any) or (quest.getBuildingTrack() == track))
                matchedNumFloors = (quest.getNumFloors() <= numFloors)
                matchedLocation = quest.isLocationMatch(zoneId)
                if matchedTrack and matchedNumFloors and matchedLocation:
                    num = quest.doesBuildingCount(avId, avList)
                    if (num > 0):
                        questDesc[4] += num
                        changed = 1
            else:
                # Do not care about this quest here
                continue

        # Now send the quests back to the avatar if the status changed
        if changed:
            self.notify.debug("toonKilledBuilding: av made progress")
            av.b_setQuests(avQuests)
        else:
            self.notify.debug("toonKilledBuilding: av made NO progress")
        return

    def toonKilledCogdo(self, av, difficulty, numFloors, zoneId, avList):
        # This is the battle notifying us that a toon has defeated a
        # cogdo.  See if this toon has a quest on this cogdo.
        # If so, update the progress.
        avQuests = av.quests
        avId = av.getDoId()
        changed = 0

        #self.notify.debug("toonKilledBuilding: avId: %s, track: %s, diff: %s, numFloors: %s, zoneId: %s" %
        #                  (avId, track, difficulty, numFloors, zoneId))
        for questDesc in avQuests:
            questClass = Quests.getQuestClass(questDesc[0])
            """ TODO
            if ((questClass == Quests.BuildingQuest) or
                (questClass == Quests.BuildingNewbieQuest)):
                quest = Quests.getQuest(questDesc[0])
                matchedTrack = ((quest.getBuildingTrack() == Quests.Any) or (quest.getBuildingTrack() == track))
                matchedNumFloors = (quest.getNumFloors() <= numFloors)
                matchedLocation = quest.isLocationMatch(zoneId)
                if matchedTrack and matchedNumFloors and matchedLocation:
                    num = quest.doesBuildingCount(avId, avList)
                    if (num > 0):
                        questDesc[4] += num
                        changed = 1
            else:
                # Do not care about this quest here
                continue
                """

        # Now send the quests back to the avatar if the status changed
        if changed:
            self.notify.debug("toonKilledCogdo: av made progress")
            av.b_setQuests(avQuests)
        else:
            self.notify.debug("toonKilledCogdo: av made NO progress")
        return

    def toonKilledCogs(self, av, cogList, zoneId, avList):
        # This is the battle notifying us that a toon killed some cogs
        # See if this toon has a quest on these cogs. If so, update the progress.
        avQuests = av.quests
        avId = av.getDoId()
        changed = 0

        self.notify.debug("toonKilledCogs: avId: %s, avQuests: %s, cogList: %s, zoneId: %s" %
                          (avId, avQuests, cogList, zoneId))

        for questDesc in avQuests:
            quest = Quests.getQuest(questDesc[0])
            if quest != None:
                for cogDict in cogList:
                    if cogDict['isVP']:
                        num = quest.doesVPCount(avId, cogDict, zoneId, avList)
                    elif cogDict['isCFO']:
                        num = quest.doesCFOCount(avId, cogDict, zoneId, avList)
                    else:
                        num = quest.doesCogCount(avId, cogDict, zoneId, avList)
                    if (num > 0):
                        questDesc[4] += num
                        changed = 1

        # Now send the quests back to the avatar if the status changed
        if changed:
            self.notify.debug("toonKilledCogs: av %s made progress" % (avId))
            av.b_setQuests(avQuests)
        else:
            self.notify.debug("toonKilledCogs: av %s made NO progress" % (avId))
        return

    def toonRodeTrolleyFirstTime(self, av):
        # This is notifying us that a toon has gotten on the
        # trolley for the first time. See if this toon has a
        # trolley quest. If so, update the progress.
        avQuests = av.quests
        avId = av.getDoId()
        changed = 0

        for questDesc in avQuests:
            questClass = Quests.getQuestClass(questDesc[0])
            if (questClass == Quests.TrolleyQuest):
                # Set progress
                questDesc[4] = 1
                changed = 1
            else:
                # Do not care about this quest here
                pass

        # Now send the quests back to the avatar if the status changed
        if changed:
            self.notify.debug("toonRodeTrolleyFirstTime: av %s made progress" % (avId))
            av.b_setQuests(avQuests)
            # log this event
            self.air.writeServerEvent('firstTrolleyGame', avId, '')
        else:
            self.notify.debug("toonRodeTrolleyFirstTime: av %s made NO progress" % (avId))
        return

    def toonPlayedMinigame(self, av, avList):
        # This is notifying us that a toon has entered a minigame.
        # See if this toon has a minigame quest.  If so, update the progress.
        avQuests = av.quests
        avId = av.getDoId()
        changed = 0

        for questDesc in avQuests:
            questClass = Quests.getQuestClass(questDesc[0])
            if (questClass == Quests.MinigameNewbieQuest):
                quest = Quests.getQuest(questDesc[0])
                num = quest.doesMinigameCount(av, avList)
                if (num > 0):
                    # Set progress
                    questDesc[4] += num
                    changed = 1

        # Now send the quests back to the avatar if the status changed
        if changed:
            self.notify.debug("toonPlayedMinigame: av %s made progress" % (avId))
            av.b_setQuests(avQuests)
        else:
            self.notify.debug("toonPlayedMinigame: av %s made NO progress" % (avId))
        return

    def toonOpenedMailbox(self, av):
        # This is notifying us that a toon has opened his mailbox
        # See if this toon has a mailbox quest.  If so, update the progress.
        avQuests = av.quests
        avId = av.getDoId()
        changed = 0
        for questDesc in avQuests:
            questClass = Quests.getQuestClass(questDesc[0])
            if (questClass == Quests.MailboxQuest):
                # Set progress
                questDesc[4] = 1
                changed = 1
        # Now send the quests back to the avatar if the status changed
        if changed:
            self.notify.debug("toonOpenedMailbox: av %s made progress" % (avId))
            av.b_setQuests(avQuests)
        else:
            self.notify.debug("toonOpenedMailbox: av %s made NO progress" % (avId))
        return

    def toonUsedPhone(self, av):
        # This is notifying us that a toon used his phone
        # See if this toon has a phone quest.  If so, update the progress.
        avQuests = av.quests
        avId = av.getDoId()
        changed = 0
        for questDesc in avQuests:
            questClass = Quests.getQuestClass(questDesc[0])
            if (questClass == Quests.PhoneQuest):
                # Set progress
                questDesc[4] = 1
                changed = 1
        # Now send the quests back to the avatar if the status changed
        if changed:
            self.notify.debug("toonUsedPhone: av %s made progress" % (avId))
            av.b_setQuests(avQuests)
        else:
            self.notify.debug("toonUsedPhone: av %s made NO progress" % (avId))
        return

    def recoverItems(self, av, cogList, zoneId):
        avQuests = av.quests
        avId = av.getDoId()
        itemsRecovered = []
        itemsNotRecovered = []
        changed = 0

        for questDesc in avQuests:
            questClass = Quests.getQuestClass(questDesc[0])
            if (questClass == Quests.RecoverItemQuest):
                quest = Quests.getQuest(questDesc[0])
                # See if the cog that stole the item is in the cogList
                questCogType = quest.getHolder()
                qualifier = quest.getHolderType()
                for cogDict in cogList:
                    # If the cogType is Quests.Any, that means any cog
                    # Ok, now check to see if we recovered the item based
                    # on the percent chance of finding it stored in the quest
                    # Only find items if we still need them
                    self.notify.debug("recoverItems: checking against cogDict: %s" % (cogDict))
                    if ((questCogType == Quests.Any) or
                        (questCogType == cogDict[qualifier]) or
                        # If it is level based, count those higher too
                        ((qualifier == 'level') and (questCogType <= cogDict[qualifier]))
                        ):
                        if avId in cogDict['activeToons']:
                            if not quest.testDone(questDesc[4]):#if questDesc[4] < quest.getNumItems():
                                if quest.isLocationMatch(zoneId):
                                    #rand = random.random() * 100
                                    #if rand <= quest.getPercentChance():
                                    check, count = quest.testRecover(questDesc[4])
                                    if check:
                                        # FOUND IT! Increment progress by one item
                                        #questDesc[4] += 1
                                        # Keep track of all the items recovered
                                        itemsRecovered.append(quest.getItem())
                                        #changed = 1
                                        self.notify.debug("recoverItems: av %s made progress: %s" % (avId, questDesc[4]))
                                    else:
                                        self.notify.debug("recoverItems: av %s made NO progress (item not found) [%s > %s])" % (avId, check, quest.getPercentChance()))
                                        itemsNotRecovered.append(quest.getItem())
                                    #keeping track of missed items
                                    changed = 1
                                    questDesc[4] = count
                                else:
                                    self.notify.debug("recoverItems: av %s made NO progress (wrong location)" % (avId))
                            else:
                                self.notify.debug("recoverItems: av %s made NO progress (have enough already)" % (avId))
                        else:
                            self.notify.debug("recoverItems: av %s made NO progress (av not active)" % (avId))
                    else:
                        self.notify.debug("recoverItems: av %s made NO progress (wrong cog type)" % (avId))
            else:
                # Do not care about this quest here
                continue

        # Now send the quests back to the avatar if the status changed

        # Note: this means that an avatar will immediately get credit
        # for finding an item, even if the item is found in the middle
        # floor of a building and the avatar later is killed on a
        # later floor, thus failing the building.
        if changed:
            av.b_setQuests(avQuests)

        return (itemsRecovered, itemsNotRecovered)

    def findItemInWater(self, av, zoneId):
        # Similar to recoverItems, but this is called from the
        # DistributedFishingSpot to see if there are any quest items
        # in the water.  No cogs are involved; hence, the only valid
        # questCogType is Quests.AnyFish.

        # Only one item at a time is returned by this function; the
        # function either returns the item found, or None.
        # Note: this does not support two quests with same item
        avQuests = av.quests
        avId = av.getDoId()

        for questDesc in avQuests:
            questClass = Quests.getQuestClass(questDesc[0])
            if (questClass == Quests.RecoverItemQuest):
                quest = Quests.getQuest(questDesc[0])
                if ((quest.getType() == Quests.RecoverItemQuest) and
                    (quest.getHolder() == Quests.AnyFish) and
                    ((random.random() * 100) <= quest.getPercentChance()) and
                    (questDesc[4] < quest.getNumItems()) and
                    quest.isLocationMatch(zoneId)
                    ):
                    # FOUND IT! Increment progress by one item
                    questDesc[4] += 1
                    self.notify.debug("findItemInWater: av %s made progress" % (avId))
                    av.b_setQuests(avQuests)
                    # Return the item recovered
                    return quest.getItem()
            else:
                # Do not care about this quest here
                continue

        self.notify.debug("findItemInWater: av %s made NO progress" % (avId))
        return None

    def completeAllQuestsMagically(self, av):
        avQuests = av.quests
        for quest in avQuests:
            # Make sure the progress is really high so the quest will seem completed
            quest[4] = 1000
        av.b_setQuests(avQuests)
        return 1

    def completeQuestMagically(self, av, index):
        avQuests = av.quests
        # Make sure we are in range
        if index < len(av.quests):
            # Make sure the progress is really high so the quest will seem completed
            avQuests[index][4] = 1000
            av.b_setQuests(avQuests)
            return 1
        else:
            return 0

    def toonMadeFriend(self, av, otherAv):
        # This is notifying us that a toon has made a friend.
        # See if this toon has a friend quest.
        # If so, update the progress.
        avQuests = av.quests
        avId = av.getDoId()
        changed = 0
        for questDesc in avQuests:
            questClass = Quests.getQuestClass(questDesc[0])
            if ((questClass == Quests.FriendQuest) or
                (questClass == Quests.FriendNewbieQuest)):
                quest = Quests.getQuest(questDesc[0])
                if (quest.doesFriendCount(av, otherAv)):
                    # Set progress
                    questDesc[4] += 1
                    changed = 1
            else:
                # Do not care about this quest here
                continue
        # Now send the quests back to the avatar if the status changed
        if changed:
            self.notify.debug("toonMadeFriend: av %s made progress" % (avId))
            av.b_setQuests(avQuests)
        else:
            self.notify.debug("toonMadeFriend: av %s made NO progress" % (avId))

    def hasTailorClothingTicket(self, av, npc):
        for questDesc in av.quests:
            questId, fromNpcId, toNpcId, rewardId, toonProgress = questDesc
            questType = Quests.getQuestClass(questId)
            # See if this NPC is the one we are supposed to deliver to
            # You by definition have the item
            if (questType == Quests.DeliverItemQuest):
                if Quests.npcMatches(toNpcId, npc):
                    rewardId = Quests.getAvatarRewardId(av, questId)
                    rewardType = Quests.getRewardClass(rewardId)
                    if (rewardType == Quests.ClothingTicketReward):
                        return 1
                    elif(rewardType == Quests.TIPClothingTicketReward):
                        return 2
                    else:
                        # Reward was not a clothing ticket
                        continue
                else:
                    # NPC does not match
                    continue
            else:
                # Not a deliver item quest
                continue
        # Did not find it, avId does not have clothing ticket on this tailor
        return 0

    def removeClothingTicket(self, av, npc):
        for questDesc in av.quests:
            questId, fromNpcId, toNpcId, rewardId, toonProgress = questDesc
            questClass = Quests.getQuestClass(questId)
            # See if this NPC is the one we are supposed to deliver to
            # You by definition have the item
            if (questClass == Quests.DeliverItemQuest):
                if Quests.npcMatches(toNpcId, npc):
                    rewardId = Quests.getAvatarRewardId(av, questId)
                    rewardClass = Quests.getRewardClass(rewardId)
                    if (rewardClass == Quests.ClothingTicketReward or rewardClass == Quests.TIPClothingTicketReward):
                        # This section is much like completeQuest()
                        av.removeQuest(questId)
                        # Update the toon with the reward. This reward does nothing right
                        # now but it may in the future, so it is the right thing to do
                        reward = Quests.getReward(rewardId)
                        reward.sendRewardAI(av)
                        # Bump the reward
                        self.incrementReward(av)
                        return 1
                    else:
                        # Reward was not a clothing ticket
                        continue
                else:
                    # NPC does not match
                    continue
            else:
                # Not a deliver item quest
                continue
        # Did not find it, avId does not have clothing ticket on this tailor
        return 0

    def setNextQuest(self, avId, questId):
        # for ~nextQuest: queue up a quest for this avatar
        self.NextQuestDict[avId] = questId

    def cancelNextQuest(self, avId):
        # cancel any pending quest for this avatar
        oldQuest = self.NextQuestDict.get(avId)
        if oldQuest:
            del self.NextQuestDict[avId]
        return oldQuest
