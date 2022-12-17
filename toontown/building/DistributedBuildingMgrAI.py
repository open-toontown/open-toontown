""" DistributedBuildingMgrAI module: contains the DistributedBuildingMgrAI
    class, the server side handler of all buildings in a neighborhood."""

# AI code should not import ShowBaseGlobal because it creates a graphics window
# Use AIBaseGlobal instead
# from ShowBaseGlobal import *

import os
from direct.task.Task import Task
import pickle
from otp.ai.AIBaseGlobal import *
from . import DistributedBuildingAI
from . import HQBuildingAI
from . import GagshopBuildingAI
from . import PetshopBuildingAI
from toontown.building.KartShopBuildingAI import KartShopBuildingAI
from toontown.building import DistributedAnimBuildingAI
#import DistributedDoorAI
from direct.directnotify import DirectNotifyGlobal
from toontown.hood import ZoneUtil
import time
import random


class DistributedBuildingMgrAI:
    """
    DistributedBuildingMgrAI class:  a server side object, keeps track of
    all buildings within a single neighborhood (street), handles
    converting them from good to bad, and hands out information about
    buildings to whoever asks.

    Landmark data will be saved to an AI Server local file.
    
    *How landmark building info gets loaded:
        load list from dna;

        look for backup .buildings file;
        if present:
            load from backup buildings file;
            #if buildings file is present:
            #    remove buildings file;
        else:
            load .buildings file;

        compare dna list with saved list;
        if they are different:
            make reasonable matches for suit blocks;

        create the building AI dictionary
            
    *Saving building data:
        check for backup buildings file;
        if present:
            remove buildings file;
        else:
            move buildings file to backup file;
        write new buildings file;
        remove backup buildings file;
    """

    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedBuildingMgrAI')
    serverDatafolder = simbase.config.GetString('server-data-folder', "")

    def __init__(self, air, branchID, dnaStore, trophyMgr):
        """
        branchID: The street number.  Such as 2200.
        """
        self.branchID = branchID
        self.canonicalBranchID = ZoneUtil.getCanonicalZoneId(branchID)
        assert(self.debugPrint("__init__(air, branchID, dnaStore, trophyMgr)"))
        self.air = air
        self.__buildings = {}
        self.dnaStore = dnaStore
        self.trophyMgr = trophyMgr
        self.shard = str(air.districtId)
        self.backupExtension = '.bu'
        self.findAllLandmarkBuildings()
        self.doLaterTask = None


    def cleanup(self):
        taskMgr.remove(str(self.branchID)+'_delayed_save-timer')

        for building in self.__buildings.values():
            building.cleanup()
        self.__buildings = {}
        
    def isValidBlockNumber(self, blockNumber):
        """return true if that block refers to a real block"""
        assert(self.debugPrint("isValidBlockNumber(blockNumber="+str(blockNumber)+")"))
        return blockNumber in self.__buildings

    def delayedSaveTask(self, task):
        assert(self.debugPrint("delayedSaveTask()"))
        self.save()
        self.doLaterTask=None
        return Task.done

    def isSuitBlock(self, blockNumber):
        """return true if that block is a suit block/building"""
        assert(self.debugPrint("isSuitBlock(blockNumber="+str(blockNumber)+")"))
        assert(blockNumber in self.__buildings)
        return self.__buildings[blockNumber].isSuitBlock()

    def getSuitBlocks(self):
        assert(self.debugPrint("getSuitBlocks()"))
        blocks=[]
        for i in self.__buildings.values():
            if i.isSuitBlock():
                blocks.append(i.getBlock()[0])
        return blocks

    def isCogdoBlock(self, blockNumber):
        return self.__buildings[blockNumber].isCogdo()

    def getCogdoBlocks(self):
        blocks = []
        for i in list(self.__buildings.values()):
            if i.isCogdo():
                blocks.append(i.getBlock()[0])

        return blocks

    def getEstablishedSuitBlocks(self):
        assert(self.debugPrint("getEstablishedSuitBlocks()"))
        blocks=[]
        for i in self.__buildings.values():
            if i.isEstablishedSuitBlock():
                blocks.append(i.getBlock()[0])
        return blocks

    def getToonBlocks(self):
        assert(self.debugPrint("getToonBlocks()"))
        blocks=[]
        for i in self.__buildings.values():
            if isinstance(i, HQBuildingAI.HQBuildingAI):
                continue
            if not i.isSuitBlock():
                blocks.append(i.getBlock()[0])
        return blocks

    def getBuildings(self):
        return self.__buildings.values()

    def getFrontDoorPoint(self, blockNumber):
        """get any associated path point for the specified building,
           useful for suits to know where to go when exiting from a
           building"""
        assert(self.debugPrint("getFrontDoorPoint(blockNumber="+str(blockNumber)+")"))
        assert(blockNumber in self.__buildings)
        return self.__buildings[blockNumber].getFrontDoorPoint()

    def getBuildingTrack(self, blockNumber):
        """get any associated path point for the specified building,
           useful for suits to know where to go when exiting from a
           building"""
        assert(self.debugPrint("getBuildingTrack(blockNumber="+str(blockNumber)+")"))
        assert(blockNumber in self.__buildings)
        return self.__buildings[blockNumber].track

    def getBuilding( self, blockNumber ):
        assert(self.debugPrint("getBuilding(%s)" %(str(blockNumber),)))
        assert(blockNumber in self.__buildings)
        return self.__buildings[blockNumber]
        
    def setFrontDoorPoint(self, blockNumber, point):
        """get any associated path point for the specified building,
           useful for suits to know where to go when exiting from a
           building"""
        assert(self.debugPrint("setFrontDoorPoint(blockNumber="+str(blockNumber)
                +", point="+str(point)+")"))
        assert(blockNumber in self.__buildings)
        return self.__buildings[blockNumber].setFrontDoorPoint(point)
    
    def getDNABlockLists(self):
        blocks=[]
        hqBlocks=[]
        gagshopBlocks=[]
        petshopBlocks=[]
        kartshopBlocks = []
        animBldgBlocks = []
        for i in range(self.dnaStore.getNumBlockNumbers()):
            blockNumber = self.dnaStore.getBlockNumberAt(i)
            buildingType = self.dnaStore.getBlockBuildingType(blockNumber)
            if (buildingType == 'hq'):
                hqBlocks.append(blockNumber)  
            elif (buildingType == 'gagshop'):
                gagshopBlocks.append(blockNumber)
            elif (buildingType == 'petshop'):
                petshopBlocks.append(blockNumber)
            elif( buildingType == 'kartshop' ):
                kartshopBlocks.append( blockNumber )
            elif( buildingType == 'animbldg' ):
                animBldgBlocks.append( blockNumber )
            else:
                blocks.append(blockNumber)
        return blocks, hqBlocks, gagshopBlocks, petshopBlocks, kartshopBlocks, animBldgBlocks
    
    def findAllLandmarkBuildings(self):
        assert(self.debugPrint("findAllLandmarkBuildings()"))
        # Load the saved buildings:
        buildings=self.load()
        # Create the distributed buildings:
        blocks, hqBlocks, gagshopBlocks, petshopBlocks, kartshopBlocks, animBldgBlocks = self.getDNABlockLists()
        for block in blocks:
            # Used saved data, if appropriate:
            self.newBuilding(block, buildings.get(block, None))
        for block in animBldgBlocks:
            # Used saved data, if appropriate:
            self.newAnimBuilding(block, buildings.get(block, None))
        for block in hqBlocks:
            self.newHQBuilding(block)
        for block in gagshopBlocks:
            self.newGagshopBuilding(block)
            
        if simbase.wantPets:
            for block in petshopBlocks:
                self.newPetshopBuilding(block)

        if( simbase.wantKarts ):
            for block in kartshopBlocks:
                self.newKartShopBuilding( block )

    def newBuilding(self, blockNumber, blockData=None):
        """Create a new building and keep track of it."""
        assert(self.debugPrint("newBuilding(blockNumber="+str(blockNumber)
                +", blockData="+str(blockData)+")"))
        assert(blockNumber not in self.__buildings)

        building=DistributedBuildingAI.DistributedBuildingAI(
            self.air, blockNumber, self.branchID, self.trophyMgr)
        building.generateWithRequired(self.branchID)
        if blockData:
            building.track = blockData.get("track", "c")
            building.difficulty = int(blockData.get("difficulty", 1))
            building.numFloors = int(blockData.get("numFloors", 1))
            building.numFloors = max(1, min(5, building.numFloors))
            if not ZoneUtil.isWelcomeValley(building.zoneId):                
                building.updateSavedBy(blockData.get("savedBy"))
            else:
                self.notify.warning('we had a cog building in welcome valley %d' % building.zoneId)
            building.becameSuitTime = blockData.get("becameSuitTime", time.time())

            # Double check the state becuase we have seen the building
            # saved out with other states (like waitForVictor). If we
            # get one of these weird states, just make it a toon bldg
            if blockData["state"] == "suit":
                building.setState("suit")
            elif blockData['state'] == 'cogdo':
                if simbase.air.wantCogdominiums:
                    building.numFloors = DistributedBuildingAI.DistributedBuildingAI.FieldOfficeNumFloors
                    building.setState("cogdo")
            else:
                building.setState("toon")
        else:
            building.setState("toon")
        self.__buildings[blockNumber] = building
        return building

    def newAnimBuilding(self, blockNumber, blockData=None):
        """Create a new building and keep track of it."""
        assert(self.debugPrint("newBuilding(blockNumber="+str(blockNumber)
                +", blockData="+str(blockData)+")"))
        assert(blockNumber not in self.__buildings)

        building=DistributedAnimBuildingAI.DistributedAnimBuildingAI(
                self.air, blockNumber, self.branchID, self.trophyMgr)
        building.generateWithRequired(self.branchID)
        if blockData:
            building.track = blockData.get("track", "c")
            building.difficulty = int(blockData.get("difficulty", 1))
            building.numFloors = int(blockData.get("numFloors", 1))
            if not ZoneUtil.isWelcomeValley(building.zoneId):                
                building.updateSavedBy(blockData.get("savedBy"))
            else:
                self.notify.warning('we had a cog building in welcome valley %d' % building.zoneId)
            building.becameSuitTime = blockData.get("becameSuitTime", time.time())

            # Double check the state becuase we have seen the building
            # saved out with other states (like waitForVictor). If we
            # get one of these weird states, just make it a toon bldg
            if blockData["state"] == "suit":
                building.setState("suit")
            else:
                building.setState("toon")
        else:
            building.setState("toon")
        self.__buildings[blockNumber] = building
        return building    

    def newHQBuilding(self, blockNumber):
        """Create a new HQ building and keep track of it."""
        assert(blockNumber not in self.__buildings)
        dnaStore = self.air.dnaStoreMap[self.canonicalBranchID]
        exteriorZoneId = dnaStore.getZoneFromBlockNumber(blockNumber)
        exteriorZoneId = ZoneUtil.getTrueZoneId(exteriorZoneId, self.branchID)
        interiorZoneId = (self.branchID-self.branchID%100)+500+blockNumber
        assert(self.debugPrint("newHQBuilding(blockNumber=%s exteriorZoneId=%s interiorZoneId=%s" %
                               (blockNumber, exteriorZoneId, interiorZoneId)))
        building=HQBuildingAI.HQBuildingAI(self.air, exteriorZoneId, interiorZoneId, blockNumber)
        self.__buildings[blockNumber] = building
        return building

    def newGagshopBuilding(self, blockNumber):
        """Create a new Gagshop building and keep track of it."""
        assert(self.debugPrint("newGagshopBuilding(blockNumber="+str(blockNumber)+")"))
        assert(blockNumber not in self.__buildings)
        dnaStore = self.air.dnaStoreMap[self.canonicalBranchID]
        exteriorZoneId = dnaStore.getZoneFromBlockNumber(blockNumber)
        exteriorZoneId = ZoneUtil.getTrueZoneId(exteriorZoneId, self.branchID)
        interiorZoneId = (self.branchID-self.branchID%100)+500+blockNumber
        building=GagshopBuildingAI.GagshopBuildingAI(self.air, exteriorZoneId, interiorZoneId, blockNumber)
        self.__buildings[blockNumber] = building
        return building
    
    def newPetshopBuilding(self, blockNumber):
        """Create a new Petshop building and keep track of it."""
        assert(self.debugPrint("newPetshopBuilding(blockNumber="+str(blockNumber)+")"))
        assert(blockNumber not in self.__buildings)
        dnaStore = self.air.dnaStoreMap[self.canonicalBranchID]
        exteriorZoneId = dnaStore.getZoneFromBlockNumber(blockNumber)
        exteriorZoneId = ZoneUtil.getTrueZoneId(exteriorZoneId, self.branchID)
        interiorZoneId = (self.branchID-self.branchID%100)+500+blockNumber
        building=PetshopBuildingAI.PetshopBuildingAI(self.air, exteriorZoneId, interiorZoneId, blockNumber)
        self.__buildings[blockNumber] = building
        return building

    def newKartShopBuilding( self, blockNumber ):
        """
        Purpose: The newKartShopBuilding Method creates a new KartShop
        building and keeps track of it.

        Params: blockNumber - block that the shop is on.
        Return: None
        """
        assert( self.debugPrint( "newKartShopBuilding(blockNumber=" + str( blockNumber ) + ")" ) )
        assert( blockNumber not in self.__buildings )

        dnaStore = self.air.dnaStoreMap[ self.canonicalBranchID ]

        # Retrieve the Exterior and Interior ZoneIds
        exteriorZoneId = dnaStore.getZoneFromBlockNumber( blockNumber )
        exteriorZoneId = ZoneUtil.getTrueZoneId( exteriorZoneId, self.branchID )
        interiorZoneId = ( self.branchID - self.branchID%100 ) + 500 + blockNumber

        building = KartShopBuildingAI( self.air, exteriorZoneId, interiorZoneId, blockNumber )
        self.__buildings[ blockNumber ] = building

        return building
    
    def getFileName(self):
        """Figure out the path to the saved state"""
        f = "%s%s_%d.buildings" % (self.serverDatafolder, self.shard, self.branchID)
        assert(self.debugPrint("getFileName() returning \""+str(f)+"\""))
        return f
    
    def saveTo(self, file, block=None):
        """Save data to specified file"""
        assert(self.debugPrint("saveTo(file="+str(file)+", block="+str(block)+")"))
        if block:
            # Save just this one block to the file:
            pickleData=block.getPickleData()
            pickle.dump(pickleData, file)
        else:
            # Save them all:
            for i in self.__buildings.values():
                # HQs do not need to be saved
                if isinstance(i, HQBuildingAI.HQBuildingAI):
                    continue
                pickleData=i.getPickleData()
                pickle.dump(pickleData, file)
    
    def fastSave(self, block):
        """Save data to default location"""
        return
        # This code has not been tested or connected.  If the normal save takes
        # too long on the AI server, this fastSave should be considered.
        assert(0)
        assert(self.debugPrint("fastSave(block="+str(block)+")"))
        try:
            fileName=self.getFileName()+'.delta'
            working=fileName+'.temp'
            # Change the name to flag the work in progress:
            if os.path.exists(working):
                os.remove(working)
            os.rename(fileName, working)
            file=open(working, 'w')
            file.seek(0, 2)
            self.saveTo(file, block)
            file.close()
            # Change the name to flag the work complete:
            os.rename(working, fileName)
        except IOError:
            self.notify.error(str(sys.exc_info()[1]))
            # Even if it's just the rename that failed, we don't want to 
            # clobber the prior file.
    
    def save(self):
        """Save data to default location"""
        assert(self.debugPrint("save()"))
        try:
            fileName=self.getFileName()
            backup=fileName+self.backupExtension
            # Move current file as the backup file:
            if os.path.exists(fileName):
                os.rename(fileName, backup)
            file=open(fileName, 'w')
            file.seek(0)
            self.saveTo(file)
            file.close()
            if os.path.exists(backup):
                os.remove(backup)
        except EnvironmentError:
            self.notify.warning(str(sys.exc_info()[1]))
            # Even if it's just the rename that failed, we don't want to 
            # clobber the prior file.
    
    def loadFrom(self, file):
        """Load data from specified file"""
        assert(self.debugPrint("loadFrom(file="+str(file)+")"))
        blocks={}
        try:
            while 1:
                pickleData=pickle.load(file)
                blocks[int(pickleData['block'])]=pickleData
        except EOFError:
            pass
        return blocks
    
    def load(self):
        """Load data from default location"""
        assert(self.debugPrint("load()"))
        fileName=self.getFileName()
        try:
            # Try to open the backup file:
            file=open(fileName+self.backupExtension, 'r')
            # Remove the (assumed) broken file:
            if os.path.exists(fileName):
                os.remove(fileName)
        except IOError:
            # OK, there's no backup file, good.
            try:
                # Open the real file:
                file=open(fileName, 'r')
            except IOError:
                # OK, there's no file.  Start new list:
                return {}
        file.seek(0)
        blocks=self.loadFrom(file)
        file.close()
        return blocks
    
    if __debug__:
        def debugPrint(self, message):
            """for debugging"""
            return self.notify.debug(
                    str(self.__dict__.get('branchID', '?'))+' '+message)

