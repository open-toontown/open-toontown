from otp.ai.AIBaseGlobal import *
from panda3d.core import *
from panda3d.toontown import *
from direct.distributed import DistributedObjectAI
from direct.directnotify import DirectNotifyGlobal
from toontown.building import TutorialBuildingAI
from toontown.building import TutorialHQBuildingAI
from . import SuitPlannerTutorialAI
from toontown.toonbase import ToontownBattleGlobals
from toontown.toon import NPCToons
from toontown.ai import BlackCatHolidayMgrAI
from toontown.ai import DistributedBlackCatMgrAI

class TutorialManagerAI(DistributedObjectAI.DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory("TutorialManagerAI")

    # how many seconds do we wait for the toon to appear on AI before we
    # nuke his skip tutorial request
    WaitTimeForSkipTutorial = 5.0

    def __init__(self, air):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        # This is a dictionary of all the players who are currently in
        # tutorials. We need to create things when someone requests
        # a tutorial, and destroy them when they leave.
        self.playerDict = {}

        # There are only two blocks in the tutorial. One for the gag shop
        # building, and one for the Toon HQ. If there aren't, something
        # is wrong. 
        self.dnaStore = DNAStorage()

        dnaFile = simbase.air.lookupDNAFileName("tutorial_street.dna")
        self.air.loadDNAFileAI(self.dnaStore, dnaFile)
        numBlocks = self.dnaStore.getNumBlockNumbers()
        assert numBlocks == 2
        # Assumption: the only block that isn't an HQ is the gag shop block.
        self.hqBlock = None
        self.gagBlock = None
        for blockIndex in range (0, numBlocks):
            blockNumber = self.dnaStore.getBlockNumberAt(blockIndex)
            buildingType = self.dnaStore.getBlockBuildingType(blockNumber)
            if (buildingType == 'hq'):
                self.hqBlock = blockNumber
            else:
                self.gagBlock = blockNumber
                
        assert self.hqBlock and self.gagBlock

        # key is avId, value is real time when the request was made
        self.avIdsRequestingSkip = {}
        self.accept("avatarEntered", self.waitingToonEntered )
                                                                  
        return None

    def requestTutorial(self):
        # TODO: possible security breach: what if client is repeatedly
        # requesting tutorial? can client request tutorial from playground?
        # can client request tutorial if hp is at least 16? How do we
        # handle these cases?
        avId = self.air.getAvatarIdFromSender()
        # Handle unexpected exits
        self.acceptOnce(self.air.getAvatarExitEvent(avId),
                        self.__handleUnexpectedExit,
                        extraArgs=[avId])
        # allocate tutorial objects and zones
        zoneDict = self.__createTutorial(avId)
        # Tell the player to enter the zone
        self.d_enterTutorial(avId,
                             zoneDict["branchZone"],
                             zoneDict["streetZone"],
                             zoneDict["shopZone"],
                             zoneDict["hqZone"]
                             )
        self.air.writeServerEvent('startedTutorial', avId, '')

    def toonArrived(self):
        avId = self.air.getAvatarIdFromSender()
        # Make sure the avatar exists
        av = self.air.doId2do.get(avId)
        # Clear out the avatar's quests, hp, inventory, and everything else in case
        # he made it half way through the tutorial last time.
        if av:
            # No quests
            av.b_setQuests([])
            av.b_setQuestHistory([])
            av.b_setRewardHistory(0, [])
            av.b_setQuestCarryLimit(1)
            # Starting HP
            av.b_setMaxHp(15)
            av.b_setHp(15)
            # No exp
            av.experience.zeroOutExp()
            av.d_setExperience(av.experience.makeNetString())
            # One cupcake and one squirting flower
            av.inventory.zeroInv()
            av.inventory.addItem(ToontownBattleGlobals.THROW_TRACK, 0)
            av.inventory.addItem(ToontownBattleGlobals.SQUIRT_TRACK, 0)
            av.d_setInventory(av.inventory.makeNetString())
            # No cogs defeated
            av.b_setCogStatus([1] * 32)
            av.b_setCogCount([0] * 32)
        return

    def allDone(self):
        avId = self.air.getAvatarIdFromSender()
        # No need to worry further about unexpected exits
        self.ignore(self.air.getAvatarExitEvent(avId))
        # Make sure the avatar exists
        av = self.air.doId2do.get(avId)
        if av:
            self.air.writeServerEvent('finishedTutorial', avId, '')
            av.b_setTutorialAck(1)
            self.__destroyTutorial(avId)
        else:
            self.notify.warning(
                "Toon " +
                str(avId) +
                " isn't here, but just finished a tutorial. " +
                "I will ignore this."
                )
        return

    def __createTutorial(self, avId):
        if self.playerDict.get(avId):
            self.notify.warning(str(avId) + " is already in the playerDict!")
        
        branchZone = self.air.allocateZone()
        streetZone = self.air.allocateZone()
        shopZone = self.air.allocateZone()
        hqZone = self.air.allocateZone()
        # Create a building object
        building = TutorialBuildingAI.TutorialBuildingAI(self.air,
                                                         streetZone,
                                                         shopZone,
                                                         self.gagBlock)
        # Create an HQ object
        hqBuilding = TutorialHQBuildingAI.TutorialHQBuildingAI(self.air,
                                                               streetZone,
                                                               hqZone,
                                                               self.hqBlock)

        def battleOverCallback(zoneId):
            hqBuilding.battleOverCallback()
            building.battleOverCallback()
        
        # Create a suit planner
        suitPlanner = SuitPlannerTutorialAI.SuitPlannerTutorialAI(
            self.air,
            streetZone,
            battleOverCallback)

        # Create the NPC blocking the tunnel to the playground
        blockerNPC = NPCToons.createNPC(self.air, 20001, NPCToons.NPCToonDict[20001], streetZone,
                                        questCallback=self.__handleBlockDone)
        blockerNPC.setTutorial(1)

        # is the black cat holiday enabled?
        blackCatMgr = None
        if bboard.has(BlackCatHolidayMgrAI.BlackCatHolidayMgrAI.PostName):
            blackCatMgr = DistributedBlackCatMgrAI.DistributedBlackCatMgrAI(
                self.air, avId)
            blackCatMgr.generateWithRequired(streetZone)
            
        zoneDict={"branchZone" : branchZone,
                  "streetZone" : streetZone,
                  "shopZone" : shopZone,
                  "hqZone" : hqZone,
                  "building" : building,
                  "hqBuilding" : hqBuilding,
                  "suitPlanner" : suitPlanner,
                  "blockerNPC" : blockerNPC,
                  "blackCatMgr" : blackCatMgr,
                  }
        self.playerDict[avId] = zoneDict
        return zoneDict

    def __handleBlockDone(self):
        return None

    def __destroyTutorial(self, avId):
        zoneDict = self.playerDict.get(avId)
        if zoneDict:
            zoneDict["building"].cleanup()
            zoneDict["hqBuilding"].cleanup()
            zoneDict["blockerNPC"].requestDelete()
            if zoneDict["blackCatMgr"]:
                zoneDict["blackCatMgr"].requestDelete()
            self.air.deallocateZone(zoneDict["branchZone"])
            self.air.deallocateZone(zoneDict["streetZone"])
            self.air.deallocateZone(zoneDict["shopZone"])
            self.air.deallocateZone(zoneDict["hqZone"])
            zoneDict["suitPlanner"].cleanup()
            del self.playerDict[avId]
        else:
            self.notify.warning("Tried to deallocate zones for " +
                                str(avId) +
                                " but none were present in playerDict.")

    def rejectTutorial(self):
        avId = self.air.getAvatarIdFromSender()
        # Make sure the avatar exists
        av = self.air.doId2do.get(avId)
        if av:
            # Acknowlege that the player has seen a tutorial
            self.air.writeServerEvent('finishedTutorial', avId, '')
            av.b_setTutorialAck(1)

            self.sendUpdateToAvatarId(avId, "skipTutorialResponse", [1])
        else:
            self.notify.warning(
                "Toon " +
                str(avId) +
                " isn't here, but just rejected a tutorial. " +
                "I will ignore this."
                )
        return

    def respondToSkipTutorial(self, avId, av):
        """Reply to the client if we let him skip the tutorial."""
        self.notify.debugStateCall(self)
        assert avId
        assert av
        response = 1
        if av:
            if av.tutorialAck:
                self.air.writeServerEvent('suspicious', avId, 'requesting skip tutorial, but tutorialAck is 1')
                response = 0

        if av and response:
            # Acknowlege that the player has seen a tutorial
            self.air.writeServerEvent('skippedTutorial', avId, '')
            av.b_setTutorialAck(1)
            # these values were taken by running a real tutorial            
            self.air.questManager.assignQuest(avId,
                                              20000,
                                              101,
                                              100,
                                              1000,
                                              1
                                              )
            
            self.air.questManager.completeAllQuestsMagically(av)
            av.removeQuest(101)
            self.air.questManager.assignQuest(avId,
                                              1000,
                                              110,
                                              2,
                                              1000,
                                              0
                                              )
            self.air.questManager.completeAllQuestsMagically(av)

            # do whatever needs to be done to make his quest state good
        elif av:
            self.notify.debug("%s requestedSkipTutorial, but tutorialAck is 1")
        else:
            response = 0
            self.notify.warning(
                "Toon " +
                str(avId) +
                " isn't here, but requested to skip tutorial. " +
                "I will ignore this."
                )
        self.sendUpdateToAvatarId(avId, "skipTutorialResponse", [response])
        return

    def waitingToonEntered(self, av):
        """Check if the avatar is someone who's requested to skip, then proceed accordingly."""
        avId = av.doId
        if avId in self.avIdsRequestingSkip:
            requestTime = self.avIdsRequestingSkip[avId]
            
            curTime = globalClock.getFrameTime()
            if (curTime - requestTime) <= self.WaitTimeForSkipTutorial:
                self.respondToSkipTutorial(avId, av)
            else:
                self.notify.warning("waited too long for toon %d responding no to skip tutorial request" % avId)
                self.sendUpdateToAvatarId(avId, "skipTutorialResponse", [0])
            del self.avIdsRequestingSkip[avId]
            self.removeTask("skipTutorialToon-%d" % avId)
                

    def waitForToonToEnter(self,avId):
        """Mark our toon as requesting to skip, and start a task to timeout for it."""
        self.notify.debugStateCall(self)
        self.avIdsRequestingSkip[avId] = globalClock.getFrameTime()
        self.doMethodLater(self.WaitTimeForSkipTutorial, self.didNotGetToon, "skipTutorialToon-%d" % avId, [avId])

    def didNotGetToon(self, avId):
        """Just say no since the AI didn't get it."""
        self.notify.debugStateCall(self)
        if avId in self.avIdsRequestingSkip:
            del self.avIdsRequestingSkip[avId]
        self.sendUpdateToAvatarId(avId, "skipTutorialResponse", [0])
        return Task.done

    def requestSkipTutorial(self):
        """We are requesting to skip tutorial,  add other quest history to be consistent."""
        self.notify.debugStateCall(self)
        avId = self.air.getAvatarIdFromSender()
        # Make sure the avatar exists
        av = self.air.doId2do.get(avId)        
        if av:
            self.respondToSkipTutorial(avId,av)
        else:
            self.waitForToonToEnter(avId)
    
    def d_enterTutorial(self, avId, branchZone, streetZone, shopZone, hqZone):
        self.sendUpdateToAvatarId(avId, "enterTutorial", [branchZone,
                                                          streetZone,
                                                          shopZone,
                                                          hqZone])
        return

    def __handleUnexpectedExit(self, avId):
        self.notify.warning("Avatar: " + str(avId) +
                            " has exited unexpectedly")
        self.__destroyTutorial(avId)
        return
    
        