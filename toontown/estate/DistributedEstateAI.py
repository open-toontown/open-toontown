
from otp.ai.AIBase import *
from direct.distributed.ClockDelta import *
from toontown.toonbase.ToontownGlobals import *
from otp.otpbase import OTPGlobals
from otp.ai.AIZoneData import AIZoneData
from direct.distributed import DistributedObjectAI
from . import DistributedHouseAI
#import DistributedPlantAI
from direct.fsm import ClassicFSM
from direct.fsm import State
from direct.task import Task
import random
import pickle
from . import HouseGlobals
from toontown.safezone import DistributedButterflyAI
from toontown.safezone import ButterflyGlobals
from toontown.safezone import ETreasurePlannerAI
from toontown.safezone import DistributedPicnicTableAI
from toontown.safezone import DistributedChineseCheckersAI
from . import DistributedTargetAI
from . import GardenGlobals
from toontown.estate import DistributedFlowerAI
from toontown.estate import DistributedGagTreeAI
from toontown.estate import DistributedStatuaryAI
from toontown.estate import DistributedGardenPlotAI
from toontown.estate import DistributedGardenBoxAI
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import ToontownBattleGlobals
from toontown.estate import DistributedChangingStatuaryAI
from toontown.estate import DistributedToonStatuaryAI
from toontown.fishing.DistributedFishingPondAI import DistributedFishingPondAI
from toontown.safezone.DistributedFishingSpotAI import DistributedFishingSpotAI
from toontown.safezone import EFlyingTreasurePlannerAI
from . import DistributedCannonAI
from panda3d.toontown import *

class DistributedEstateAI(DistributedObjectAI.DistributedObjectAI):

    """
    This is the class that handles the creation of an estate and all
    things contained in an estate, including:  houses, ponds, gardens,
    mailboxes, etc.
    """

    notify = directNotify.newCategory("DistributedEstateAI")
    #notify.setDebug(True)

    printedLs = 0

    EstateModel = None

    timeToEpoch = GardenGlobals.TIME_OF_DAY_FOR_EPOCH
    epochHourInSeconds = timeToEpoch * 60 * 60
    dayInSeconds = 24 * 60 * 60

    def __init__(self, air):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)

        # the avatar currently in charge of the estate
        #self.notify.debug("created with avId = %d and zoneId = %d" % (avId, zoneId))
        #self.avId = 0
        #self.zoneId = 0

        #simbase.air.lastEstate = self inable to check the estate.
        self.houses = [None] * 6
        self.estateType = 0
        if not hasattr(self, 'avId'):
            self.avId = 0
        if not hasattr(self, 'zoneId'):
            self.zoneId = 0
        self.estateButterflies = None
        self.fishingSpots = None
        self.fishingPonds = None
        self.goons = None
        self.estateTreasurePlanner = None
        self.estateFlyingTreasurePlanner = None
        self.estateFireworks = None
        self.target = None
        self.picnicTable = None
        self.gardenList = [[],[],[],[],[],[]]
        self.gardenBoxList = [[],[],[],[],[],[]]
        self.houseList = []
        self.idList = []
        #if not hasattr(self, "decorData"):
        #    self.decorData = []

        self.cannonsEnabled = simbase.config.GetBool('estate-cannons', 0)
        self.fireworksEnabled = simbase.config.GetBool('estate-fireworks', 0)
        self.goonEnabled = simbase.config.GetBool('estate-goon', 0) #what is this 
        self.goons = None
        self.gagBarrels = None
        self.crate = None

        self.cannonFlag = 0
        self.gameTableFlag = False

        # for day/night
        #self.serverTime = ts
        self.dawnTime = 0

        #here we load in all the database fields
        #if valDict:
          #  for key in valDict:
           #     if hasattr(self, key):
           #         self.dclass.directUpdate(self, key, valDict[key])

        # keep track of generation/deletion from stateserver
        self.Estate_generated = 0

        #testFlower = DistributedFlowerAI.DistributedFlowerAI()
        #testGagTree = DistributedGagTreeAI.DistributedGagTreeAI()
        #testStatuary = DistributedStatuaryAI.DistributedStatuaryAI()

        if not hasattr(self, "lastEpochTimeStamp"):
            self.lastEpochTimeStamp = time.time()

        self.accept('gardenTest', self.placeTestGarden)
        self.accept('gardenClear', self.clearMyGarden)
        self.accept('gardenNuke', self.nukeMyGarden)
        self.accept('gardenPlant', self.plantFlower)
        self.accept('wiltGarden', self.wiltMyGarden)
        self.accept('unwiltGarden', self.unwiltMyGarden)
        self.accept('waterGarden', self.setWaterLevelMyGarden)
        self.accept('growthGarden', self.setGrowthLevelMyGarden)
        self.accept('epochGarden', self.doEpochMagicWord)

        self.maxSlots = 32
        self.toonsPerAccount = 6
        #self.timePerEpoch = 300 #five minutes
        #self.timePerEpoch = 30000 #5000 minutes #NO LONGER A VALID CONCEPT AS EPOCHS HAPPEN ONCE A DAY
        self.gardenTable = []
        for count in range(self.toonsPerAccount):

            self.gardenTable.append([0] * self.maxSlots) #ACCOUNT HAS 6 TOONS

    def announceGenerate(self):
        DistributedObjectAI.DistributedObjectAI.announceGenerate(self)
        self.initEstateData()
        self.createPetCollisions()

    def generate(self):
        DistributedEstateAI.notify.debug("DistEstate generate: %s" % self.doId)
        self.Estate_generated = 1
        DistributedObjectAI.DistributedObjectAI.generate(self)

    def generateWithRequiredAndId(self, doId, air, zoneId):
        self.notify.debug("DistributedEstateAI generateWithRequiredAndId")

        DistributedObjectAI.DistributedObjectAI.generateWithRequiredAndId(self, doId, air, zoneId)

#    def requestDelete(self):
#        taskMgr.remove(self.uniqueName("GardenEpoch"))
#        taskMgr.remove(self.uniqueName("endCannons"))
#        taskMgr.remove(self.uniqueName("endCannonsNotify"))
#        DistributedObjectAI.DistributedObjectAI.requestDelete(self)

    def delete(self):
        DistributedEstateAI.notify.debug("DistEstate delete: %s" % self.doId)
        self.ignoreAll()
        taskMgr.remove(self.uniqueName("GardenEpoch"))
        taskMgr.remove(self.uniqueName("endCannons"))
        taskMgr.remove(self.uniqueName("endCannonsNotify"))
        taskMgr.remove(self.uniqueName("endGameTable"))
        #print("Trying Delete Estate")
        try:
            #print("checking already deleted")
            self.Estate_deleted
            DistributedEstateAI.notify.debug("estate already deleted: %s" % self.Estate_deleted)
        except:
            #print("deleting Estate")
            DistributedEstateAI.notify.debug("completing estate delete: %s" % self.__dict__.get("zoneId"))
            self.Estate_deleted = self.zoneId

            if self.estateTreasurePlanner:
                self.estateTreasurePlanner.stop()
                self.estateTreasurePlanner.deleteAllTreasuresNow()
                self.estateTreasurePlanner = None

            if self.estateFlyingTreasurePlanner:
                self.estateFlyingTreasurePlanner.stop()
                self.estateFlyingTreasurePlanner.deleteAllTreasuresNow()
                self.estateFlyingTreasurePlanner = None

            if self.estateButterflies:
                for bfly in self.estateButterflies:
                    bfly.fsm.requestFinalState()
                    bfly.requestDelete()
                self.estateButterflies = None
                ButterflyGlobals.clearIndexes(self.avId)

            if self.fishingSpots:
                for spot in self.fishingSpots:
                    spot.requestDelete()
                self.fishingSpots = None

            if self.fishingPonds:
                for pond in self.fishingPonds:
                    # Remove PondBingoManager
                    if simbase.wantBingo:
                        if pond.hasPondBingoManager():
                            pond.getPondBingoManager().requestDelete()
                    pond.requestDelete()
                self.fishingPonds = None

            if self.estateFireworks:
                self.estateFireworks.requestDelete()
                del self.estateFireworks

            if hasattr(self, "target"):
                if self.target:
                    self.target.requestDelete()
                    del self.target

            if self.goons:
                for goon in self.goons:
                    goon.requestDelete()
                    del goon
                self.goons = None

            if self.gagBarrels:
                for barrel in self.gagBarrels:
                    barrel.requestDelete()
                    del barrel
                self.gagBarrels = None

            if self.crate:
                del self.crate
                self.crate = None

            if self.picnicTable:
                self.picnicTable.requestDelete()
                del self.picnicTable
                self.picnicTable = None

            del self.houseList

            self.deleteGarden()

            if hasattr(self,'gardenBoxList'):
                for index in range(len(self.gardenBoxList)):
                    for box in self.gardenBoxList[index]:
                        if box:
                            box.requestDelete()

            del self.gardenBoxList
            del self.gardenTable
            del self.estateButterflies
            del self.gardenList

            DistributedObjectAI.DistributedObjectAI.delete(self)

    def unload(self):
        self.notify.debug("unload")

    def deleteGarden(self):
        if not hasattr(self,'gardenTable'):
            return

        print("calling delete garden")

        for index in range(len(self.gardenTable)):
            for distLawnDecor in self.gardenTable[index]:
                if distLawnDecor: # and distLawnDecor.occupied:
                    distLawnDecor.requestDelete()

        self.gardenTable = []

    def destroy(self):
        for house in self.houses:
            if house is not None:
                house.requestDelete()

        del self.houses[:]
        self.requestDelete()
        
    def initEstateData(self, estateVal=None, numHouses=0, houseId=None, houseVal=None):
        # these parameters have just been read from the database..
        # now we have to do something with them.
        self.numHouses = numHouses
        self.houseType = [None] * self.numHouses
        self.housePos = [None] * self.numHouses
        self.houseId = houseId
        self.houseVal = houseVal
        self.estateVal = estateVal

        # start treasure planner
        self.estateTreasurePlanner = ETreasurePlannerAI.ETreasurePlannerAI(self.zoneId)
        self.estateTreasurePlanner.start()

        # start butterflies
        self.estateButterflies = []
        if simbase.config.GetBool('want-estate-butterflies', 0):
            ButterflyGlobals.generateIndexes(self.avId, ButterflyGlobals.ESTATE)
            for i in range(0,
                    ButterflyGlobals.NUM_BUTTERFLY_AREAS[ButterflyGlobals.ESTATE]):
                for j in range(0,
                    ButterflyGlobals.NUM_BUTTERFLIES[ButterflyGlobals.ESTATE]):
                    bfly = DistributedButterflyAI.DistributedButterflyAI(self.air,
                                         ButterflyGlobals.ESTATE, i, self.avId)
                    bfly.generateWithRequired(self.zoneId)
                    bfly.start()
                    self.estateButterflies.append(bfly)

        # Create fishing docks
        dnaStore = DNAStorage()
        dnaData = simbase.air.loadDNAFileAI(dnaStore,
                  simbase.air.lookupDNAFileName('estate_1.dna'))
        self.fishingSpots = []
        self.fishingPonds = []
        if (isinstance(dnaData, DNAData)):
            fishingPonds, fishingPondGroups = self.air.findFishingPonds(dnaData, self.zoneId, MyEstate)
            self.fishingPonds += fishingPonds
            for dnaGroup, distPond in zip(fishingPondGroups, fishingPonds):
                self.fishingSpots += self.air.findFishingSpots(dnaGroup, distPond)
        else:
            self.notify.warning("loadDNAFileAI failed for 'estate_1.dna'")

        if simbase.wantPets:

            if not DistributedEstateAI.EstateModel:
                # load up the estate model for the pets
                self.dnaStore = DNAStorage()
                simbase.air.loadDNAFile(
                    self.dnaStore,
                    self.air.lookupDNAFileName('storage_estate.dna'))
                node = simbase.air.loadDNAFile(
                    self.dnaStore,
                    self.air.lookupDNAFileName('estate_1.dna'))
                DistributedEstateAI.EstateModel = hidden.attachNewNode(
                    node)
            render = self.getRender()
            self.geom = DistributedEstateAI.EstateModel.copyTo(render)
            # for debugging, show what's in the model
            if not DistributedEstateAI.printedLs:
                DistributedEstateAI.printedLs = 1
                #self.geom.ls()

            if 0:#__dev__:
                pt.mark('loaded estate model')
                pt.off()
                pt.printTo()

        if self.fireworksEnabled:
            pos = (29.7, -1.77, 10.93)
            from . import DistributedFireworksCannonAI
            self.estateFireworks = DistributedFireworksCannonAI.DistributedFireworksCannonAI(self.air, *pos)
            self.estateFireworks.generateWithRequired(self.zoneId)

        if self.goonEnabled:
            from toontown.suit import DistributedGoonAI
            self.goons = [None]*3
            for i in range(3):
                self.goons[i] = DistributedGoonAI.DistributedGoonAI(self.air,None,i)
                self.goons[i].setupSuitDNA(1, 1, "c")
                self.goons[i].generateWithRequired(self.zoneId)

            from toontown.coghq import DistributedGagBarrelAI
            self.gagBarrels = [None]*4
            for i in range(4):
                self.gagBarrels[i] = DistributedGagBarrelAI.DistributedGagBarrelAI(self.air, None,
                                                                                   -100-10*i, 30-10*i, 0.2,i,i)
                self.gagBarrels[i].generateWithRequired(self.zoneId)
            from toontown.coghq import DistributedBeanBarrelAI
            jelly = DistributedBeanBarrelAI.DistributedBeanBarrelAI(self.air, None,-150, -20, 0.2)
            jelly.generateWithRequired(self.zoneId)
            self.gagBarrels.append(jelly)

            from toontown.coghq import DistributedCrateAI
            self.crate = DistributedCrateAI.DistributedCrateAI(self.air, -142, 0, 0.0)
            self.crate.generateWithRequired(self.zoneId)

        #self.testPlant = DistributedPlantAI.DistributedPlantAI(self.air)
        #self.testPlant.generateWithRequired(self.zoneId)
        #self.placeOnGround(self.testPlant.doId)
        simbase.estate = self
        #self.b_setDecorData([[2,[0,42,42,1],[512,1024,2048]],[1,[2,3],[512,1024,2048]]])
        #self.air.queryObjectField("DistributedEstate", "setDecorData", self.doId, None)
        #self.b_setDecorData([[1,0,16,16,0]])

    def postHouseInit(self):
        #print("post house Init")

        currentTime = time.time()
        #print("time: %s \n cts:%s" % (currentTime, self.rentalTimeStamp))
        if self.rentalTimeStamp >= currentTime:
            #print("starting cannons")
            if self.rentalType == ToontownGlobals.RentalCannon:
                self.makeCannonsUntil(self.rentalTimeStamp)
            elif self.rentalType == ToontownGlobals.RentalGameTable:
                self.makeGameTableUntil(self.rentalTimeStamp)
        else:
            self.b_setRentalTimeStamp(0)
            pass
            #print("not starting cannons")

    def startCannons(self, fool = 0):
        if self.cannonFlag:
            return
        # create flying treasures
        if not self.estateFlyingTreasurePlanner:
            self.estateFlyingTreasurePlanner = EFlyingTreasurePlannerAI.EFlyingTreasurePlannerAI(self, self.zoneId)
        self.estateFlyingTreasurePlanner.preSpawnTreasures()
        self.estateFlyingTreasurePlanner.start()

        # tell client about flying treasures
        self.updateFlyingTreasureList()

        # create the target
        if not hasattr(self, "target") or not self.target:
            self.target = DistributedTargetAI.DistributedTargetAI(self.air, -5.6, -24, 50)
            self.target.generateWithRequired(self.zoneId)
        self.target.start()

        for house in self.houseList:
            house.setCannonEnabled(1)

        self.b_setClouds(1)
        self.cannonFlag = 1

    def endCannons(self, fool = 0):
        if not self.cannonFlag:
            return
        for house in self.houseList:
            house.setCannonEnabled(0)
        self.b_setClouds(0)

        if self.estateFlyingTreasurePlanner:
            self.estateFlyingTreasurePlanner.stop()
            self.estateFlyingTreasurePlanner.deleteAllTreasuresNow()

        if hasattr(self, "target"):
            if self.target:
                self.target.requestDelete()
                del self.target

        self.b_setRentalTimeStamp(0)
        self.cannonFlag = 0

    def notifyCannonsEnd(self, arg=None):
        self.sendUpdate("cannonsOver", [])

    def bootStrapEpochs(self):
        #first update the graden data based on how much time has based
        print ("last time %s" % (self.lastEpochTimeStamp))
        currentTime = time.time()
        print ("current time %s" % (currentTime))
        timeDiff = currentTime - self.lastEpochTimeStamp
        print ("time diff %s" % (timeDiff))
        
        #self.lastEpochTimeStamp = time.mktime((2006, 8, 24, 10, 50, 31, 4, 237, 1))
        if self.lastEpochTimeStamp == 0:
            self.lastEpochTimeStamp = time.time()
        tupleNewTime = time.localtime(currentTime - self.epochHourInSeconds)
        tupleOldTime = time.localtime(self.lastEpochTimeStamp)

        #tupleOldTime = (2006, 6, 18, 0, 36, 45, 0, 170, 1)
        #tupleNewTime = (2006, 6, 19, 3, 36, 45, 0, 170, 1)

        listLastDay = list(tupleOldTime)
        listLastDay[3] = 0 #set hour to epoch time
        listLastDay[4] = 0 #set minute to epoch time
        listLastDay[5] = 0 #set second to epoch time
        tupleLastDay = tuple(listLastDay)

        randomDelay = random.random() * 5 * 60 # random five minute range
        #this isnt even used wth disney
        #secondsNextEpoch = ((time.mktimetupleLastDay) + self.epochHourInSeconds + self.dayInSeconds + randomDelay) - currentTime
        
        #should we do the epoch for the current day?
        #beforeEpoch = 1
        #if  tupleNewTime[3] >= self.timeToEpoch:
        #    beforeEpoch = 0

        epochsToDo =  int((time.time() - time.mktime(tupleLastDay)) / self.dayInSeconds)
        #epochsToDo -= beforeEpoch
        if epochsToDo < 0:
            epochsToDo = 0

        print(("epochsToDo %s" % (epochsToDo)))

        #print("tuple times")
        #print tupleNewTime
        #print tupleOldTime


        if epochsToDo:
            pass
            print("doingEpochData")
            self.doEpochData(0, epochsToDo)
        else:
            pass
            print("schedualing next Epoch")
            #print("Delaying inital epoch")
            self.scheduleNextEpoch()
            self.sendUpdate("setLastEpochTimeStamp", [self.lastEpochTimeStamp])
            #time2Epoch = self.timePerEpoch - timeDiff


    def scheduleNextEpoch(self):
        currentTime = time.time()
        tupleNewTime = time.localtime()
        tupleOldTime = time.localtime(self.lastEpochTimeStamp)

        listLastDay = list(tupleOldTime)
        listLastDay[3] = 0 #set hour to epoch time
        listLastDay[4] = 0 #set minute to epoch time
        listLastDay[5] = 0 #set second to epoch time
        tupleLastDay = tuple(listLastDay)

        randomDelay = random.random() * 5 * 60 # random five minute range
        whenNextEpoch = (time.mktime(tupleLastDay) + self.epochHourInSeconds + self.dayInSeconds + randomDelay)
        secondsNextEpoch = whenNextEpoch - currentTime
        if secondsNextEpoch >= 0:
            secondsNextEpoch += self.dayInSeconds
        taskMgr.doMethodLater((secondsNextEpoch), self.doEpochNow, self.uniqueName("GardenEpoch"))

        tupleNextEpoch = time.localtime(whenNextEpoch)

        self.notify.info("Next epoch to happen at %s %s %s %s %s %s %s %s %s" % (tupleNextEpoch))


    def setIdList(self, idList):
        self.idList = idList

    def d_setIdList(self, idList):
        self.sendUpdate('setIdList', [idList])

    def b_setIdList(self, idList):
        self.setIdList(idList)
        self.d_setIdList(idList)


    def gardenInit(self, avIdList):
        self.sendUpdate('setIdList', [avIdList])
        #self.bootStrapEpochs()


        self.avIdList = avIdList
        #check to see if the av field tags match the house owners
        for index in range(len(avIdList)):
            if self.getToonId(index) != avIdList[index]:
                self.notify.debug("Mismatching Estate Tag index %s id %s list %s" % (index, self.getToonId(index) , avIdList[index]))
            if self.getItems(index) == None:
                self.notify.debug("Items is None index %s items %s" % (index, self.getItems(index)))
            if self.getToonId(index) != avIdList[index] or self.getItems(index) == None:
                self.notify.debug("Resetting items index %s" % (index))
                self.b_setToonId(index, avIdList[index])
                #resetting the item database
                #self.b_setItems(index, [])
                self.b_setItems(index, [(255,0,-1,-1,0)]) #empty garden tag
            if self.getItems(index) == [(255,0,-1,-1,0)]:
                #case where the garden has been tagged as empty
                pass
            elif self.getItems(index) or self.getItems(index) == []:
                self.placeLawnDecor(index, self.getItems(index))
                #print "Item Check"
                #print self.getItems(index)
                pass
            self.updateToonBonusLevels(index)
        self.bootStrapEpochs()
        #self.b_setItems(1,[[49,0,16,16,0]])#get some data up for testing

    def doEpochMagicWord(self, avId, numEpoch):
        for index in range(self.toonsPerAccount):
            if self.getToonId(index) == avId:
                self.doEpochNow(numEpoch = numEpoch)
                return

    def doEpochNow(self, taskFooler = 0, onlyForThisToonIndex = None, numEpoch = 1):
        taskMgr.remove(self.uniqueName("GardenEpoch"))
        #used when a zone is active. So the garden data will be cleared and reinited
        currentTime = time.time()
        timeDiff = currentTime - self.lastEpochTimeStamp
        self.notify.info("Epoch Now! %s" % (timeDiff))
        #self.scheduleNextEpoch()
        self.doEpochData(self.dayInSeconds, numEpoch, onlyForThisToonIndex = onlyForThisToonIndex ) #make sure the epoch always happens

        #RAU the DistrbutedFlower, DistributedGardenPlot, etc, suddenly
        #disappearing on the client side is causing problems
        #We need to do some smart growing and update only the necessary
        #values, (e.g. waterLevel and growthLevel)
        #for index in range(len(self.avIdList)):
        #    if self.getToonId(index) == self.avIdList[index]:
        #        if self.getItems(index):
        #            self.clearGarden(index)
        #            self.placeLawnDecor(index, self.getItems(index))

    def doEpochData(self, time, numEpochs = 0, onlyForThisToonIndex = None):
        #this function just updates the data buit doesn't effect anything within the zone
        self.saveTime()

        # Tell the distributedLawnDecors to update themselves... and update our 'itemLists'
        #numEpochs = int(time / self.timePerEpoch)
        #print ("Epochs passed %d" % (numEpochs))
        #do the epoch based stuff here like growing, consuming water, etc....


        for index in range(len(self.gardenTable)):
            anyUpdates = False
            numWilted = 0
            numHealthy = 0
            for distLawnDecor in self.gardenTable[index]:
                if distLawnDecor and distLawnDecor.occupied:
                    if onlyForThisToonIndex and \
                       not distLawnDecor.getOwnerIndex() == onlyForThisToonIndex:
                        #print("passing for this toon")
                        continue
                    anyUpdates = True
                    #print("doing epoch %s" % (numEpochs))
                    distLawnDecor.doEpoch(numEpochs)

                    if hasattr(distLawnDecor, 'isWilted'):
                        if distLawnDecor.isWilted():
                            numWilted += 1
                        else:
                            numHealthy += 1
                else:
                    pass
                    #print("PROBLEM %s %s" % (distLawnDecor, distLawnDecor.occupied))


            if numHealthy or numWilted:
                #log how many healthy and wilted plants he has after these epochs have been run
                self.air.writeServerEvent('garden_epoch_run', self.getToonId(index),
                                          '%d|%d|%d' % (numEpochs, numHealthy, numWilted))


            if anyUpdates:
                self.b_setItems(index, self.getItems(index))
                self.updateToonBonusLevels(index)

        self.scheduleNextEpoch()
        #taskMgr.doMethodLater(self.timePerEpoch, self.doEpochNow, self.uniqueName("GardenEpoch"))

    def updateToonBonusLevels(self, index):
        # find the trees with fruit
        numTracks = len(ToontownBattleGlobals.Tracks)
        hasBonus = [[] for n in range(numTracks)]
        for distLawnDecor in self.gardenTable[index]:
            # keep track of which trees are blooming
            if distLawnDecor and distLawnDecor.hasGagBonus():
                hasBonus[distLawnDecor.gagTrack].append(distLawnDecor.gagLevel)

        # find the lowest gaglevel for each track that immediately preceeds a non-fruited tree
        # EG.  [0, 1, 2, 4, 5, 6] should find 2
        bonusLevels = [-1] * len(ToontownBattleGlobals.Tracks)
        for track in range(len(hasBonus)):
            hasBonus[track].sort()
            for gagLevel in hasBonus[track]:
                if gagLevel == (bonusLevels[track] + 1):
                    bonusLevels[track] = gagLevel
                else:
                    break

        # tell the toon
        toonId = self.getToonId(index)
        toon = simbase.air.doId2do.get(toonId)
        if toon:
            toon.b_setTrackBonusLevel(bonusLevels)

    def hasGagTree(self, ownerIndex, gagTrack, gagLevel):
        """Return true if a gag tree is already planted on the estate that matches paremeters."""
        for distLawnDecor in self.gardenTable[ownerIndex]:
            if hasattr(distLawnDecor, 'gagTrack') and hasattr(distLawnDecor, 'gagLevel'):
                if distLawnDecor.gagTrack == gagTrack and \
                   distLawnDecor.gagLevel == gagLevel:
                    return True
        return False

    def findLowestGagTreePlot(self, ownerIndex, gagTrack, gagLevel):
        """Returns the lowest plot index of a gag tree that matches paremeters.
        Returns -1 if not found"""
        for plotIndex in range(len(self.gardenTable[ownerIndex])):
            distLawnDecor = self.gardenTable[ownerIndex][plotIndex]
            if hasattr(distLawnDecor, 'gagTrack') and hasattr(distLawnDecor, 'gagLevel'):
                if distLawnDecor.gagTrack == gagTrack and \
                   distLawnDecor.gagLevel == gagLevel:
                    return plotIndex
        return -1

    def placeTestGarden(self, avId = 0):
        #print("placing test Items %s" % (avId))
        for index in range(self.toonsPerAccount):
            if self.getToonId(index) == avId:
                self.clearGarden(index)
                self.b_setItems(index,[])
                self.placeLawnDecor(index, self.getItems(index))

                #mark the toon as 'garden started'
                toon = simbase.air.doId2do.get(avId)
                if toon:
                    toon.b_setGardenStarted(True)
                    #log that they are starting the garden
                    self.air.writeServerEvent("garden_started", self.doId, '')

    def placeStarterGarden(self, avId = 0):
        #print("placing test Items %s" % (avId))
        for index in range(self.toonsPerAccount):
            if self.getToonId(index) == avId:
                #mark the toon as 'garden started'
                toon = simbase.air.doId2do.get(avId)
                if toon:
                    if not toon.getGardenStarted():
                        toon.b_setGardenStarted(True)
                        #log that they are starting the garden
                        self.air.writeServerEvent("garden_started", self.doId, '')

                if self.getItems(index) == [(255,0,-1,-1,0)]:
                    #case where the garden has been tagged as empty
                    self.clearGarden(index)
                    self.b_setItems(index,[])
                    self.placeLawnDecor(index, self.getItems(index))


    def clearGarden(self, slot):
        for entry in self.gardenTable[slot]:
            if entry and entry != 0:
                entry.requestDelete()
            entry = 0
        #self.gardenList[slot] = []

    def clearMyGarden(self, avId = 0):
        for index in range(self.toonsPerAccount):
            if self.getToonId(index) == avId:
                for hardPoint in range(len(GardenGlobals.estatePlots[index])):
                    self.removePlantAndPlaceGardenPlot(index, hardPoint)
                #self.clearGarden(index)
                #self.b_setItems(index,[])

    def nukeMyGarden(self, avId = 0):
        for index in range(self.toonsPerAccount):
            if self.getToonId(index) == avId:
                for hardPoint in range(len(GardenGlobals.estatePlots[index])):
                    self.removePlant(index, hardPoint)
                    self.removeGardenPlot(index,hardPoint)
                for box in self.gardenBoxList[index]:
                    box.requestDelete()
                self.gardenBoxList[index] = []

                self.b_setItems(index, [(255,0,-1,-1,0)]) #empty garden tag

    def setWaterLevelMyGarden(self, avId, waterLevel, specificHardPoint = -1):
        """
        sets the water level for all the plants in my garden
        """
        assert self.notify.debugStateCall(self)
        for index in range(self.toonsPerAccount):
            if self.getToonId(index) == avId:
                items = self.getItems(index)
                if specificHardPoint == -1:
                    for plot in range(len(self.gardenTable[index])):
                        someLawnDecor = self.gardenTable[index][plot]
                        if someLawnDecor and hasattr(someLawnDecor,'b_setWaterLevel'):
                            someLawnDecor.b_setWaterLevel(waterLevel, False)

                    itemList = self.getItems(index)
                    self.d_setItems(index, itemList)
                else:
                    someLawnDecor = self.gardenTable[index][specificHardPoint]
                    if someLawnDecor and hasattr(someLawnDecor,'b_setWaterLevel'):
                        someLawnDecor.b_setWaterLevel(waterLevel)

    def setGrowthLevelMyGarden(self, avId, growthLevel, specificHardPoint = -1):
        """
        sets the growth level for all the plants in my garden
        """
        assert self.notify.debugStateCall(self)
        for index in range(self.toonsPerAccount):
            if self.getToonId(index) == avId:
                items = self.getItems(index)
                if specificHardPoint == -1:
                    for plot in range(len(self.gardenTable[index])):
                        someLawnDecor = self.gardenTable[index][plot]
                        if someLawnDecor and hasattr(someLawnDecor,'b_setGrowthLevel'):
                            someLawnDecor.b_setGrowthLevel(growthLevel, False)

                    itemList = self.getItems(index)
                    self.d_setItems(index, itemList)
                else:
                    someLawnDecor = self.gardenTable[index][specificHardPoint]
                    if someLawnDecor and hasattr(someLawnDecor,'b_setGrowthLevel'):
                        someLawnDecor.b_setGrowthLevel(growthLevel)                        

    def wiltMyGarden(self, avId, specificHardPoint = -1):
        self.notify.debug("wilting my garden %s" % (avId))
        self.setWaterLevelMyGarden( avId, -1, specificHardPoint)

    def unwiltMyGarden(self, avId, specificHardPoint = -1):
        self.notify.debug("unwilting my garden %s" % (avId))
        self.setWaterLevelMyGarden( avId, 0, specificHardPoint)

    def plantFlower(self, avId, type, plot, water, growth, optional = 0):
            for index in range(self.toonsPerAccount):
                if self.getToonId(index) == avId:
                    self.removePlant(index, plot)
                    itemId = self.addLawnDecorItem(index, type, plot, water, growth,optional)
                    itemList = self.getItems(index)
                    itemList.append((type, plot, water, growth, optional))
                    self.b_setItems(index, itemList)
            return itemId

    def plantTree(self, avId, type, plot, water, growth, optional = 0):
            for index in range(self.toonsPerAccount):
                if self.getToonId(index) == avId:
                    self.removePlant(index, plot)
                    itemDoId = self.addLawnDecorItem(index, type, plot, water, growth,optional)
                    itemList = self.getItems(index)
                    itemList.append((type, plot, water, growth, optional))
                    self.b_setItems(index, itemList)
            return itemDoId

    def removePlant(self, slot, plot):
        itemList = self.getItems(slot)
        for item in self.getItems(slot):
            if item[1] == plot:
                if self.gardenTable[slot][plot]:
                    self.gardenTable[slot][plot].requestDelete()
                    self.gardenTable[slot][plot] = None
                itemList.remove(item)
                #we need to do a b_setItems to save the change in database
                self.b_setItems(slot, itemList)
                self.updateToonBonusLevels(slot)

    def addLawnDecorItem(self, slot, type, hardPoint, waterLevel, growthLevel, optional = 0):
            #Hard coding MickeyStatue1 to be my toon statue
            plantClass = DistributedFlowerAI.DistributedFlowerAI
            plantType = GardenGlobals.PlantAttributes[type]['plantType']
            if plantType == GardenGlobals.GAG_TREE_TYPE:
                #print("print")
                plantClass = DistributedGagTreeAI.DistributedGagTreeAI
                testPlant = DistributedGagTreeAI.DistributedGagTreeAI(type, waterLevel, growthLevel, optional, slot, hardPoint)
                postion = GardenGlobals.estatePlots[slot][hardPoint]
                testPlant.setPosition(postion[0], postion[1], 0)
                testPlant.setH(postion[2])
            elif plantType == GardenGlobals.FLOWER_TYPE:
                #print("FLOWER")
                plantClass =  DistributedFlowerAI.DistributedFlowerAI
                testPlant = DistributedFlowerAI.DistributedFlowerAI(type, waterLevel, growthLevel, optional, slot, hardPoint)
                plot = GardenGlobals.estatePlots[slot][hardPoint]
                #postion = GardenGlobals.estateBoxes[slot][plot[0]]
                postion = self.gardenBoxList[slot][plot[0]].getBoxPos(plot[1])
                heading = self.gardenBoxList[slot][plot[0]].getH()
                testPlant.setPosition(postion[0], postion[1], postion[2])
                testPlant.setH(heading)
            elif plantType == GardenGlobals.STATUARY_TYPE:
                #print("STATUARY")
                plantClass = DistributedStatuaryAI.DistributedStatuaryAI
                if type in GardenGlobals.ToonStatuaryTypeIndices: 
                    # Some hardcoded optional values for testing
                    # optional = 2325 #Pig = 3861 #Bear = 3349 #Monkey = 2837 #Duck = 2325 #Rabbit = 1813 #Mouse = 1557 #Horse = 1045 #Cat = 533 #Dog = 21
                    testPlant = DistributedToonStatuaryAI.DistributedToonStatuaryAI(type, waterLevel, growthLevel, optional, slot, hardPoint)
                elif type in GardenGlobals.ChangingStatuaryTypeIndices:
                    testPlant = DistributedChangingStatuaryAI.DistributedChangingStatuaryAI(type, waterLevel, growthLevel, optional, slot, hardPoint)
                else:
                    testPlant = DistributedStatuaryAI.DistributedStatuaryAI(type, waterLevel, growthLevel, optional, slot, hardPoint)
                postion = GardenGlobals.estatePlots[slot][hardPoint]
                testPlant.setPosition(postion[0], postion[1], 0)
                testPlant.setH(postion[2])

            testPlant.generateWithRequired(self.zoneId)
            testPlant.setEstateId(self.doId)

            #print ("Placing at Position %s %s %s" % (postion[0], postion[1], postion[2]))
            #self.placeOnGround(testPlant.doId)
            self.gardenTable[slot][hardPoint] = testPlant
            self.notify.debug('testPlant.doId : %s' %testPlant.doId)
            return testPlant.doId

    def placeLawnDecor(self, toonIndex, itemList):
        boxList = GardenGlobals.estateBoxes[toonIndex]
        for boxPlace in boxList:
            newBox = DistributedGardenBoxAI.DistributedGardenBoxAI(boxPlace[3])
            newBox.setPosition(boxPlace[0], boxPlace[1], 16)
            newBox.setH(boxPlace[2])
            newBox.generateWithRequired(self.zoneId)
            newBox.setEstateId(self.doId)
            newBox.setupPetCollision()
            self.gardenBoxList[toonIndex].append(newBox)
        plotList = GardenGlobals.estatePlots[toonIndex]
        for plotPointIndex in (list(range(len(plotList)))):
            item = self.findItemAtHardPoint(itemList, plotPointIndex)
            if not item or not GardenGlobals.PlantAttributes.get(item[0]):
                item = None
            if item:
                type = item[0]
                if type not in list(GardenGlobals.PlantAttributes.keys()):
                    self.notify.warning('type %d not found in PlantAttributes, forcing it to 48' % type)
                    type = 48
                hardPoint = item[1]
                waterLevel = item[2]
                growthLevel = item[3]
                optional = item[4] #all fields are 8bit except optional which is 16bits
                itemdoId = self.addLawnDecorItem(toonIndex, type, hardPoint, waterLevel, growthLevel, optional)
            else:
                #pass
                self.addGardenPlot(toonIndex, plotPointIndex)

    def removePlantAndPlaceGardenPlot(self, slot, hardPoint):
        """
        This removes it on the AI side, places a gardenPlot, then updates the client
        """
        self.removePlant(slot, hardPoint)
        itemId = self.addGardenPlot(slot,hardPoint)
        return itemId
    
    def addGardenPlot(self, slot, hardPoint):

            #print("HARDPOINT")
            plot = GardenGlobals.estatePlots[slot][hardPoint]
            #print(plot)
            if plot[3] == GardenGlobals.FLOWER_TYPE:
                #print("flower type")
                postion = self.gardenBoxList[slot][plot[0]].getBoxPos(plot[1])
                heading = self.gardenBoxList[slot][plot[0]].getH()
            else:
                #print("not flower type")
                postion = plot
                heading = postion[2]
            plantClass = DistributedGardenPlotAI.DistributedGardenPlotAI
            testPlant = DistributedGardenPlotAI.DistributedGardenPlotAI(plot[2], slot, hardPoint)
            testPlant.setPosition(postion[0], postion[1], 16)
            testPlant.setH(heading)
            testPlant.generateWithRequired(self.zoneId)

            #print ("Placing at Position %s %s" % (postion[0], postion[1]))
            self.placeOnGround(testPlant.doId)
            self.gardenTable[slot][hardPoint] = testPlant
            return testPlant.doId

    def removeGardenPlot(self, slot, plot):
        if self.gardenTable[slot][plot]:
            self.gardenTable[slot][plot].requestDelete()
            self.gardenTable[slot][plot] = None

    def findItemAtHardPoint(self, itemList, hardPoint):
        for item in itemList:
            if hardPoint == item[1]:
                return item
        return None

    def findItemPositionInItemList(self, itemList, hardPointIndex):
        for itemListIndex in range(len(itemList)):
            if hardPointIndex == itemList[itemListIndex][1]:
                return itemListIndex
        return -1

    def placeOnGround(self, doId):
        self.sendUpdate('placeOnGround', [doId])

    def setPetIds(self, petIds):
        self.petIds = petIds

    if simbase.wantPets:
        def createPetCollisions(self):
            # call this after the world geom is all set up
            render=self.getRender()
            # find the collisions and make copies of them, centered at Z=0
            self.petColls = render.attachNewNode('petColls')
            colls = self.geom.findAllMatches('**/+CollisionNode')
            for coll in colls:
                bitmask = coll.node().getIntoCollideMask()
                if not (bitmask & BitMask32(OTPGlobals.WallBitmask)).isZero():
                    newColl = coll.copyTo(self.petColls)
                    # make sure it's still in the correct position relative
                    # to the world
                    newColl.setTransform(coll.getTransform(self.geom))
                    """
                    bounds = coll.getBounds()
                    height = abs(bounds.getMax()[2] - bounds.getMin()[2])
                    """
                    # move down two feet to account for collisions that are
                    # not at Z=0
                    newColl.setZ(render, -2)
            self.geom.stash()
            # set up the collision traverser for this zone
            self.getZoneData().startCollTrav()

    def destroyEstateData(self):
        if hasattr(self, "Estate_deleted"):
            DistributedEstateAI.notify.debug("destroyEstateData: estate already deleted: %s" % self.Estate_deleted)
            return

        DistributedEstateAI.notify.debug("destroyEstateData: %s" % self.__dict__.get("zoneId"))

        #if hasattr(self, 'zoneId'):
        #    DistributedEstateAI.notify.debug('destroyEstateData: %s' % self.zoneId)
        #else:
        #    DistributedEstateAI.notify.debug('destroyEstateData: zoneID reference deleted')

        if hasattr(self, 'geom'):
            self.petColls.removeNode()
            del self.petColls
            self.geom.removeNode()
            del self.geom
            self.releaseZoneData()
        else:
            DistributedEstateAI.notify.debug('estateAI has no geom...')

    def updateFlyingTreasureList(self):
        treasures = self.estateFlyingTreasurePlanner.treasures

        doIdList = []
        for t in treasures:
            if t != None:
                doIdList.append(t.doId)
        self.sendUpdate("setTreasureIds", [doIdList])

    def getEstateType(self):
        assert(self.notify.debug("getEstateType"))
        return self.estateType

    def getDawnTime(self):
        return self.dawnTime

    def requestServerTime(self):
        #print ("requestServerTime")
        requesterId = self.air.getAvatarIdFromSender()
        self.serverTime = time.time() % HouseGlobals.DAY_NIGHT_PERIOD
        self.sendUpdateToAvatarId(requesterId, "setServerTime", [self.serverTime])

    def b_setDecorData(self, decorData):
        self.setDecorData(decorData)
        self.d_setDecorData(decorData)

    def setDecorData(self, decorData):
        self.decorData = decorData
        #print ("setDecorData %s" % (self.doId))

    def d_setDecorData(self, decorData):
        print("FIXME when correct toon.dc is checked in")
        #self.sendUpdate("setDecorData", [decorData])

    def getDecorData(self):
        if hasattr(self, "decorData"):
            return self.decorData
        else:
            return []

# lots of get and set functions, not really the prettiest way to do this but it works

    def getToonId(self, slot):
        if slot == 0:
            if hasattr(self, "slot0ToonId"):
                return self.slot0ToonId
        elif slot == 1:
            if hasattr(self, "slot1ToonId"):
                return self.slot1ToonId
        elif slot == 2:
            if hasattr(self, "slot2ToonId"):
                return self.slot2ToonId
        elif slot == 3:
            if hasattr(self, "slot3ToonId"):
                return self.slot3ToonId
        elif slot == 4:
            if hasattr(self, "slot4ToonId"):
                return self.slot4ToonId
        elif slot == 5:
            if hasattr(self, "slot5ToonId"):
                return self.slot5ToonId
        else:
            return None

    def setToonId(self, slot, tag):
        if slot == 0:
            self.slot0ToonId = tag
        elif slot == 1:
            self.slot1ToonId = tag
        elif slot == 2:
            self.slot2ToonId = tag
        elif slot == 3:
            self.slot3ToonId = tag
        elif slot == 4:
            self.slot4ToonId = tag
        elif slot == 5:
            self.slot5ToonId = tag

    def d_setToonId(self, slot, avId):
        if avId:
            if slot == 0:
                self.sendUpdate("setSlot0ToonId", [avId])
            elif slot == 1:
                self.sendUpdate("setSlot1ToonId", [avId])
            elif slot == 2:
                self.sendUpdate("setSlot2ToonId", [avId])
            elif slot == 3:
                self.sendUpdate("setSlot3ToonId", [avId])
            elif slot == 4:
                self.sendUpdate("setSlot4ToonId", [avId])
            elif slot == 5:
                self.sendUpdate("setSlot5ToonId", [avId])

    def b_setToonId(self, slot, avId):
        self.setToonId(slot, avId)
        self.d_setToonId(slot, avId)

    def getItems(self, slot):
        if slot == 0:
            if hasattr(self, "slot0Items"):
                return self.slot0Items
        elif slot == 1:
            if hasattr(self, "slot1Items"):
                return self.slot1Items
        elif slot == 2:
            if hasattr(self, "slot2Items"):
                return self.slot2Items
        elif slot == 3:
            if hasattr(self, "slot3Items"):
                return self.slot3Items
        elif slot == 4:
            if hasattr(self, "slot4Items"):
                return self.slot4Items
        elif slot == 5:
            if hasattr(self, "slot5Items"):
                return self.slot5Items
        else:
            return None

    def setOneItem(self, ownerIndex, hardPointIndex, gardenItemType=-1, waterLevel=None, growthLevel=-1, variety=-1):
        assert ownerIndex >= 0 and ownerIndex < 6
        itemList = self.getItems(ownerIndex)
        itemsIndex = self.findItemPositionInItemList(itemList, hardPointIndex)
        if itemsIndex != -1 and gardenItemType == -1:
            gardenItemType = itemList[itemsIndex][0]
        if itemsIndex != -1  and waterLevel == None:
            waterLevel = itemList[itemsIndex][2]
        if itemsIndex != -1  and growthLevel == -1:
            growthLevel = itemList[itemsIndex][3]
        if itemsIndex != -1  and variety == -1:
            variety = itemList[itemsIndex][4]
        newInfo = (gardenItemType, hardPointIndex, waterLevel, growthLevel, variety)
        #since itemList is a reference, just update it
        if itemsIndex != -1 :
            itemList[itemsIndex] = newInfo
        else:
            itemList.append(newInfo)

    # Note there is no d_setOneItem, since the whole itemList gets updated

    def b_setOneItem(self, ownerIndex, hardPointIndex, gardenItemType=-1,
                    waterLevel=-1, growthLevel=-1, variety=-1):
       """
       If you're changing multiple items, it's better to call b_setItems than
       multiple calls to b_setOneItem
       """
       self.setOneItem(ownerIndex, hardPointIndex, gardenItemType,
                       waterLevel, growthLevel, variety)
       self.d_setItems(ownerIndex, self.getItems(ownerIndex))




    def setItems(self, slot, items):
        if slot == 0:
            self.slot0Items = items
        elif slot == 1:
            self.slot1Items = items
        elif slot == 2:
            self.slot2Items = items
        elif slot == 3:
            self.slot3Items = items
        elif slot == 4:
            self.slot4Items = items
        elif slot == 5:
            self.slot5Items = items

    def d_setItems(self, slot, items):
        items = self.checkItems(items)
        if slot == 0:
            self.sendUpdate("setSlot0Items", [items])
        elif slot == 1:
            self.sendUpdate("setSlot1Items", [items])
        elif slot == 2:
            self.sendUpdate("setSlot2Items", [items])
        elif slot == 3:
            self.sendUpdate("setSlot3Items", [items])
        elif slot == 4:
            self.sendUpdate("setSlot4Items", [items])
        elif slot == 5:
            self.sendUpdate("setSlot5Items", [items])

    def checkItems(self, items, slot = 0):
        toonId = self.getToonId(slot)
        for item in items:
            if (item[0] < 0) or (item[1] < 0) or (item[4] < 0):
                self.air.writeServerEvent("Removing_Invalid_Garden_Item_on_Toon ", toonId, " item %s" % str(item))
                items.remove(item)
        return items


    def b_setItems(self, slot, items):
        items = self.checkItems(items)
        self.setItems(slot, items)
        self.d_setItems(slot, items)

    def setSlot0ToonId(self, avId):
        self.slot0ToonId = avId

    def setSlot1ToonId(self, avId):
        self.slot1ToonId = avId

    def setSlot2ToonId(self, avId):
        self.slot2ToonId = avId

    def setSlot3ToonId(self, avId):
        self.slot3ToonId = avId

    def setSlot4ToonId(self, avId):
        self.slot4ToonId = avId

    def setSlot5ToonId(self, avId):
        self.slot5ToonId = avId

    def setSlot0Items(self, items):
        self.slot0Items = items

    def setSlot1Items(self, items):
        self.slot1Items = items

    def setSlot2Items(self, items):
        self.slot2Items = items

    def setSlot3Items(self, items):
        self.slot3Items = items

    def setSlot4Items(self, items):
        self.slot4Items = items

    def setSlot5Items(self, items):
        self.slot5Items = items


    def getSlot0ToonId(self):
        if hasattr(self, "slot0ToonId"):
            return self.slot0ToonId
        else:
            return 0

    def getSlot1ToonId(self):
        if hasattr(self, "slot1ToonId"):
            return self.slot1ToonId
        else:
            return 0

    def getSlot2ToonId(self):
        if hasattr(self, "slot2ToonId"):
            return self.slot2ToonId
        else:
            return 0

    def getSlot3ToonId(self):
        if hasattr(self, "slot3ToonId"):
            return self.slot3ToonId
        else:
            return 0

    def getSlot4ToonId(self):
        if hasattr(self, "slot4ToonId"):
            return self.slot4ToonId
        else:
            return 0

    def getSlot5ToonId(self):
        if hasattr(self, "slot5ToonId"):
            return self.slot5ToonId
        else:
            return 0

    def getSlot0Items(self):
        if hasattr(self, "slot0Items"):
            return self.slot0Items
        else:
            return []

    def getSlot1Items(self):
        if hasattr(self, "slot1Items"):
            return self.slot1Items
        else:
            return []

    def getSlot2Items(self):
        if hasattr(self, "slot2Items"):
            return self.slot2Items
        else:
            return []

    def getSlot3Items(self):
        if hasattr(self, "slot3Items"):
            return self.slot3Items
        else:
            return []

    def getSlot4Items(self):
        if hasattr(self, "slot4Items"):
            return self.slot4Items
        else:
            return []

    def getSlot5Items(self):
        if hasattr(self, "slot5Items"):
            return self.slot5Items
        else:
            return []

    def getLastEpochTimeStamp(self):
        return self.lastEpochTimeStamp

    def setLastEpochTimeStamp(self, ts):
        self.lastEpochTimeStamp = ts

    def saveTime(self):
        currentTime = time.time()
        self.setLastEpochTimeStamp(currentTime)
        self.sendUpdate("setLastEpochTimeStamp", [currentTime])

    def completeFlowerSale(self,sell):
        assert self.notify.debug('completeFlowerSale()')
        avId = self.air.getAvatarIdFromSender()

        if sell:
            av = simbase.air.doId2do.get(avId)
            if av:
                # this function sells the fish, clears the tank, and
                # updates the collection, trophies, and maxhp. One stop shopping!
                trophyResult = self.creditFlowerBasket(av)

                #if trophyResult:
                #    movieType = NPCToons.SELL_MOVIE_TROPHY
                #    extraArgs = [len(av.fishCollection), FishGlobals.getTotalNumFish()]
                #else:
                #    movieType = NPCToons.SELL_MOVIE_COMPLETE
                #    extraArgs = []

                # Send a movie to reward the avatar
                #self.d_setMovie(avId, movieType, extraArgs)
            else:
                # perhaps the avatar got disconnected, just leave the fish
                # in his tank and let him resell them next time
                pass
        else:
            av = simbase.air.doId2do.get(avId)
            if av:
                # Send a movie to say goodbye
                #self.d_setMovie(avId, NPCToons.SELL_MOVIE_NOFISH)
                pass
        #self.sendClearMovie(None)
        return


    def creditFlowerBasket(self, av):
        """
        Do all the work of selling the basket and updating the collection.
        Also updates your trophy status and maxHP if needed.
        Returns 1 if you earned a trophy, 0 if you did not.
        """
        assert(self.notify.debug("creditFlowerBasket av: %s is selling all flower" % (av.getDoId())))
        oldBonus = int(len(av.flowerCollection)/GardenGlobals.FLOWERS_PER_BONUS)

        # give the avatar jellybeans in exchange for his flower
        value = av.flowerBasket.getTotalValue()
        av.addMoney(value)

        #log selling flowers, how many and for how much
        self.air.writeServerEvent("garden_flower_sell", av.getDoId(), '%d|%d' % (value, len(av.flowerBasket.flowerList)))

        # update the avatar collection for each flower
        for flower in av.flowerBasket.flowerList:
            retval = av.flowerCollection.collectFlower(flower)
            if retval == GardenGlobals.COLLECT_NEW_ENTRY:
                #log we are adding a new flower to our collection
                self.air.writeServerEvent("garden_collection_add", av.getDoId(),
                                          '%d|%d' % (flower.species,flower.variety))

        # clear out the flowerBasket
        av.b_setFlowerBasket([],[])

        # update the collection in the database
        av.d_setFlowerCollection(*av.flowerCollection.getNetLists())

        newBonus = int(len(av.flowerCollection)/GardenGlobals.FLOWERS_PER_BONUS)
        if newBonus > oldBonus:
            self.notify.info("avatar %s gets a bonus: old: %s, new: %s" % (av.doId, oldBonus, newBonus))
            oldMaxHp = av.getMaxHp()
            newMaxHp = min(ToontownGlobals.MaxHpLimit, oldMaxHp + newBonus - oldBonus)
            av.b_setMaxHp(newMaxHp)
            # Also, give them a full heal
            av.toonUp(newMaxHp)
            # update the av's trophy list

            newTrophies = av.getGardenTrophies()
            trophyId = len(newTrophies)
            newTrophies.append(trophyId)
            av.b_setGardenTrophies(newTrophies)

            #log garden trophy
            self.air.writeServerEvent("garden_trophy", av.doId, "%s" % (trophyId))

            self.sendUpdate('awardedTrophy',[av.doId])

            return 1
        else:
            assert(self.notify.debug("avatar %s no bonus: old: %s, new: %s" % (av.doId, oldBonus, newBonus)))
            return 0

    def setClouds(self, clouds):
        self.clouds = clouds

    def getClouds(self):
        if hasattr(self, "clouds"):
            return self.clouds
        else:
            return 0

    def d_setClouds(self, clouds):
        self.sendUpdate("setClouds", [clouds])

    def b_setClouds(self, clouds):
        self.setClouds(clouds)
        self.d_setClouds(clouds)

    def setRentalTimeStamp(self, rentalTimeStamp):
        self.rentalTimeStamp = rentalTimeStamp

    def getRentalTimeStamp(self):
        if hasattr(self, "rentalTimeStamp"):
            return self.rentalTimeStamp
        else:
            self.rentalTimeStamp = 0
            return 0

    def d_setRentalTimeStamp(self, rentalTimeStamp):
        self.sendUpdate("setRentalTimeStamp", [rentalTimeStamp])

    def b_setRentalTimeStamp(self, rentalTimeStamp):
        self.setRentalTimeStamp(rentalTimeStamp)
        self.d_setRentalTimeStamp(rentalTimeStamp)


    def setRentalType(self, rentalType):
        self.rentalType = rentalType

    def getRentalType(self):
        if hasattr(self, "rentalType"):
            return self.rentalType
        else:
            self.rentalType = 0
            return 0

    def d_setRentalType(self, rentalType):
        self.sendUpdate("setRentalType", [rentalType])

    def b_setRentalType(self, rentalType):
        self.setRentalType(rentalType)
        self.d_setRentalType(rentalType)

    def giveCannonTime(self, seconds):
        timeleft = 0
        if self.rentalType == ToontownGlobals.RentalCannon:
            timeleft = self.rentalTimeStamp - currentTime
            if timeleft < 0:
                timeleft = 0
        currentTime = time.time()
        newTime = currentTime + seconds + timeleft
        self.b_setRentalTimeStamp(newTime)
        self.makeCannonsUntil(newTime)


    def makeCannonsUntil(self, endTime):
        #print("makeing cannons until")
        self.startCannons()
        currentTime = time.time()
        secondsUntil = endTime - currentTime
        taskMgr.remove(self.uniqueName("endCannons"))
        taskMgr.doMethodLater(secondsUntil, self.endCannons, self.uniqueName("endCannons"))
        taskMgr.remove(self.uniqueName("endCannonsNotify"))
        taskMgr.doMethodLater(secondsUntil, self.notifyCannonsEnd, self.uniqueName("endCannonsNotify"))

    def makeGameTableUntil(self, endTime):
        self.notify.debug('making game table until')
        self.startGameTable()
        currentTime = time.time()
        secondsUntil = endTime - currentTime
        taskMgr.remove(self.uniqueName("endGameTable"))
        taskMgr.doMethodLater(secondsUntil, self.endGameTable, self.uniqueName("endGameTable"))
        
    def startGameTable(self, avatar = 0):
        if self.gameTableFlag:
            return        
        if not self.picnicTable:
            self.notify.debug('creating game table')
            # Create the game table
            pos = Point3(55, -20, 8.8)
            hpr = Point3(0, 0, 0)
            self.picnicTable = DistributedPicnicTableAI.DistributedPicnicTableAI(self.air, self.zoneId, 'gameTable',
                                                                                 pos[0], pos[1], pos[2],
                                                                                 hpr[0], hpr[1], hpr[2])
        self.gameTableFlag = True
    
    def endGameTable(self, avatar = 0):
        self.notify.debug('endGameTable')
        if not self.gameTableFlag:
            return
        if self.picnicTable:
            # delete the game table
            self.picnicTable.requestDelete()
            del self.picnicTable
            self.picnicTable = None
            
        # Tell the client that the game table rental is over
        self.sendUpdate("gameTableOver", [])
        
        self.gameTableFlag = False
    
    def rentItem(self, type, duration):
        timeleft = 0        
        currentTime = time.time()
        if self.rentalType == type:
            timeleft = self.rentalTimeStamp - currentTime
            if timeleft < 0:
                timeleft = 0
        newTime = currentTime + (duration * 60) + timeleft
        self.air.writeServerEvent('rental', self.doId, "New rental end time %s." % (newTime))
        
        self.b_setRentalTimeStamp(newTime)
        self.b_setRentalType(type)
        if type == ToontownGlobals.RentalCannon:
            self.makeCannonsUntil(newTime)
        elif type == ToontownGlobals.RentalGameTable:
            self.makeGameTableUntil(newTime)

    def movePlanter(self, slot, index, x, y, heading):
        box = self.gardenBoxList[slot][index]

        if box != None:
            box.b_setPosition(x,y,0)
            box.b_setH(heading)

    def printPlanterPos(self, slot, index):
        box = self.gardenBoxLispdb; t[slot][index]
        print(("X %s Y%s Heading %s" % (box.getX(), box.getY, box.getH())))
