from direct.distributed import DistributedObjectAI
from toontown.toonbase import TTLocalizer
from direct.directnotify import DirectNotifyGlobal
from . import DistributedFishingTargetAI
from . import FishingTargetGlobals
from toontown.hood import ZoneUtil
import random

class DistributedFishingPondAI(DistributedObjectAI.DistributedObjectAI):

    notify = DirectNotifyGlobal.directNotify.newCategory("DistributedFishingPondAI")

    def __init__(self, air, area):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        self.notify.debug("init")
        self.avId2SpotDict = {}
        self.area = area
        self.pondBingoMgr = None

    def generate(self):
        DistributedObjectAI.DistributedObjectAI.generate(self)
        self.notify.debug("generate: zoneId: %s, area: %s" % (self.zoneId, self.area))
        # Fishing Targets
        self.targets = {}
        for i in range(FishingTargetGlobals.getNumTargets(self.area)):
            hunger = (FishingTargetGlobals.MinimumHunger +
                      (random.random() * (1 - FishingTargetGlobals.MinimumHunger)))
            target = DistributedFishingTargetAI.DistributedFishingTargetAI(self.air, self, hunger)
            target.generateWithRequired(self.zoneId)
            self.targets[target.getDoId()] = target

    def delete(self):
        self.notify.debug("delete")
        # Delete all the targets
        for target in self.targets.values():
            target.requestDelete()
        del self.targets
        DistributedObjectAI.DistributedObjectAI.delete(self)

    def getArea(self):
        return self.area

    def addAvSpot(self, avId, spot):
        self.notify.debug("addAvSpot: adding avId: %s to spot" % (avId))
        currentSpot = self.avId2SpotDict.get(avId)
        if currentSpot:
            self.notify.warning("addAvSpot: avId: %s already in a spot" % (avId))
        self.avId2SpotDict[avId] = spot
        if simbase.wantBingo:
            self.__addAvToGame(avId)
        return 1

    def removeAvSpot(self, avId, spot):
        currentSpot = self.avId2SpotDict.get(avId)
        if currentSpot:
            if currentSpot == spot:
                self.notify.debug("removeAvSpot: removing avId: %s from spot" % (avId))
                del self.avId2SpotDict[avId]
                if simbase.wantBingo:
                    self.__removeAvFromGame(avId)
                return 1
            else:
                self.notify.warning("removeAvSpot: spots do not match, removing av anyways")
                del self.avId2SpotDict[avId]
                if simbase.wantBingo:
                    self.__removeAvFromGame(avId)
                return 1
        else:
            self.notify.warning("removeAvSpot: avId: %s not found" % (avId))
            # Really, if the avId is not in the avId2Spot Dict, then it should
            # not be in the pondBingoMgr either. However, for precaution, check
            # for it anyway.
            if simbase.wantBingo:
                self.__removeAvFromGame(avId)
        return 0

    def hitTarget(self, targetId):
        avId = self.air.getAvatarIdFromSender()
        av = self.air.doId2do.get(avId)
        if not av:
            return
        
        self.notify.debug("hitTarget: targetId: %s avId: %s" % (targetId, avId))
        # You must be fishing at a spot to hit a target
        spot = self.avId2SpotDict.get(avId)
        if not spot:
            self.notify.warning("hitTarget: spot not found for avId: %s" % (avId))
            return
        target = self.targets.get(targetId)
        # See if the target bites
        if (not target):
            self.air.writeServerEvent('suspicious', targetId, 'FishingPondAI.hitTarget unknown target')
        elif target.isHungry():
            self.notify.debug("hitTarget: targetId: %s is hungry" % (targetId))
            code, item = self.air.fishManager.recordCatch(avId, self.area, self.zoneId)
            # make sure we didn't trip an error condition and return None
            if code:
                # Tell the fishing spot so it can send a movie to the client
                spot.hitTarget(code, item)
        else:
            self.notify.debug("hitTarget: targetId: %s not hungry" % (targetId))

    ############################################################
    # Method:  setPondBingoManager
    # Purpose: This method sets the reference to a
    #          PondBingoManagerAI instance.
    # Input: pondBingoMgr - The pondBingoManagerAI object that 
    #                       is associated with the pond instance.
    # Output: None
    ############################################################
    def setPondBingoManager(self, pondBingoMgr):
        self.pondBingoMgr = pondBingoMgr

    ############################################################
    # Method:  getPondBingoManager
    # Purpose: This method sets the reference to a
    #          PondBingoManagerAI instance.
    # Input: None
    # Output: pondBingoMgr - The pondBingoManagerAI object that 
    #                        is associated with the pond
    #                        instance.
    ############################################################
    def getPondBingoManager(self):
        return self.pondBingoMgr

    ############################################################
    # Method:  hasPondBingoManager
    # Purpose: This method determines if the pond has a PBMgrAI
    #          and returns the result.
    # Input: None
    # Output: result 1 if there is a PBMgrAI or 0
    ############################################################
    def hasPondBingoManager(self):
        return ((self.pondBingoMgr) and [1] or [0])[0]

    ############################################################
    # Method:  __addAvToGame
    # Purpose: This method tells to PondBingoManagerAI to add
    #          an avatar ID to the game because a client has
    #          entered a FishingSpot. 
    # Input: avId - Avatar ID of the client who entered the
    #               Fishing Spot.
    # Output: None
    ############################################################
    def __addAvToGame(self, avId):
        if self.pondBingoMgr:
            self.pondBingoMgr.addAvToGame(avId)
            
    ############################################################
    # Method:  __addAvToGame
    # Purpose: This method tells to PondBingoManagerAI to 
    #          remove an avatar ID to the game because a client 
    #          has exited a FishingSpot. 
    # Input: avId - Avatar ID of the client who exited the
    #               Fishing Spot.
    # Output: None
    ############################################################
    def __removeAvFromGame(self, avId):
        if self.pondBingoMgr:
            self.pondBingoMgr.removeAvFromGame(avId)
