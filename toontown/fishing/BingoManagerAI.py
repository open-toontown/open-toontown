#################################################################
# class: BingoManagerAI.py
#
# Purpose: Manages the Bingo Night Holiday for all ponds in all
#          hoods. It generates PondBingoManagerAI objects for
#          every pond and shuts them down respectively. In
#          addition, it should handle all Stat collection such
#          as top jackpot of the night, top bingo players, and
#          so forth.
#
# Note: Eventually, this will derive from the HolidayBase class
#       and run each and ever Bingo Night, whenever that has
#       been decided upon.
#################################################################

#################################################################
# Direct Specific Modules
#################################################################
from direct.distributed import DistributedObjectAI
from direct.distributed.ClockDelta import *
from direct.directnotify import DirectNotifyGlobal
from otp.otpbase import PythonUtil
from direct.task import Task

#################################################################
# Toontown Specific Modules
#################################################################
from toontown.estate import DistributedEstateAI
from toontown.fishing import BingoGlobals
from toontown.fishing import DistributedFishingPondAI
from toontown.fishing import DistributedPondBingoManagerAI
from direct.showbase import RandomNumGen
from toontown.toonbase import ToontownGlobals
from toontown.hood import ZoneUtil

#################################################################
# Python Specific Modules
#################################################################
import pickle
import os
import time

#################################################################
# Globals and Constants
#################################################################
TTG = ToontownGlobals
BG = BingoGlobals

class BingoManagerAI(object):
#    __metaclass__ = PythonUtil.Singleton
    notify = DirectNotifyGlobal.directNotify.newCategory("BingoManagerAI")
    #notify.setDebug(True)
    #notify.setInfo(True)
    serverDataFolder = simbase.config.GetString('server-data-folder', "dependencies/backups/bingo")

    DefaultReward = { TTG.DonaldsDock: [BG.MIN_SUPER_JACKPOT, 1],
                      TTG.ToontownCentral: [BG.MIN_SUPER_JACKPOT, 1],
                      TTG.TheBrrrgh: [BG.MIN_SUPER_JACKPOT, 1],
                      TTG.MinniesMelodyland: [BG.MIN_SUPER_JACKPOT, 1],
                      TTG.DaisyGardens: [BG.MIN_SUPER_JACKPOT, 1],
                      TTG.DonaldsDreamland: [BG.MIN_SUPER_JACKPOT, 1],
                      TTG.MyEstate: [BG.MIN_SUPER_JACKPOT, 1] }

    ############################################################
    # Method:  __init__
    # Purpose: This method initializes the BingoManagerAI object
    #          and generates the PondBingoManagerAI.
    # Input: air - The AI Repository.
    # Output: None
    ############################################################
    def __init__(self, air):
        self.air = air

        # Dictionaries for quick reference to the DPMAI
        self.doId2do = {}
        self.zoneId2do = {}
        self.hood2doIdList = { TTG.DonaldsDock: [],
                               TTG.ToontownCentral: [],
                               TTG.TheBrrrgh: [],
                               TTG.MinniesMelodyland: [],
                               TTG.DaisyGardens: [],
                               TTG.DonaldsDreamland: [],
                               TTG.MyEstate: [] }

        self.__hoodJackpots = {}
        self.finalGame = BG.NORMAL_GAME
        self.shard = str(air.districtId)
        self.waitTaskName = 'waitForIntermission'

        # Generate the Pond Bingo Managers
        self.generateBingoManagers()

    ############################################################
    # Method:  start
    # Purpose: This method "starts" each PondBingoManager for
    #          the Bingo Night Holidy.
    # Input: None
    # Output: None
    ############################################################
    def start(self):
        # Iterate through keys and change into "active" state
        # for the pondBingoManagerAI
        self.notify.info("Starting Bingo Night Event: %s" % (time.ctime()))
        self.air.bingoMgr = self
        # Determine current time so that we can gracefully handle
        # an AI crash or reboot during Bingo Night.
        currentMin = time.localtime()[4]
        self.timeStamp = globalClockDelta.getRealNetworkTime()
        initState = ((currentMin < BG.HOUR_BREAK_MIN) and ['Intro'] or ['Intermission'])[0]

        # CHEATS
        #initState = 'Intermission'
        for do in list(self.doId2do.values()):
            do.startup(initState)
        self.waitForIntermission()

        # tell everyone bingo night is starting
        simbase.air.newsManager.bingoStart()

    ############################################################
    # Method:  stop
    # Purpose: This method begins the process of shutting down
    #          bingo night. It is called whenever the
    #          BingoNightHolidayAI is told to close for the
    #          evening.
    # Input: None
    # Output: None
    ############################################################
    def stop(self):
        self.__startCloseEvent()

    ############################################################
    # Method:  __shutdown
    # Purpose: This method performs the actual shutdown sequence
    #          for the pond bingo manager. By this point, all
    #          of the PondBingoManagerAIs should have shutdown
    #          so we can safely close.
    # Input: None
    # Output: None
    ############################################################
    def shutdown(self):
        self.notify.info('__shutdown: Shutting down BingoManager')

        # tell everyone bingo night is stopping
        simbase.air.newsManager.bingoEnd()

        if self.doId2do:
            #self.notify.warning('__shutdown: Not all PondBingoManagers have shutdown! Manual Shutdown for Memory sake.')
            for bingoMgr in list(self.doId2do.values()):
                self.notify.info("__shutdown: shutting down PondBinfoManagerAI in zone %s" % bingoMgr.zoneId)
                bingoMgr.shutdown()
            self.doId2do.clear()
        del self.doId2do

        self.air.bingoMgr = None
        del self.air
        del self.__hoodJackpots

    ############################################################
    # Method:  __resumeBingoNight
    # Purpose: This method resumes Bingo Night after an
    #          an intermission has taken place. This should
    #          start on the hour.
    # Input: None
    # Output: None
    ############################################################
    def __resumeBingoNight(self, task):
        self.__hoodJackpots = self.load()
        for bingoMgr in list(self.doId2do.values()):
            if bingoMgr.isGenerated():
                if self.finalGame:
                    bingoMgr.setFinalGame(self.finalGame)
                bingoMgr.resumeBingoNight()
        timeToWait = BG.getGameTime(BG.BLOCKOUT_CARD) + BG.TIMEOUT_SESSION + 5.0
        taskMgr.doMethodLater(timeToWait, self.__handleSuperBingoClose, 'SuperBingoClose')

        # If we have another game after this, then do not want to generate a
        # new task to wait for the next intermission.
        return Task.done

    ############################################################
    # Method:  __handleSuperBingoClose
    # Purpose: This method is responsible for logging the
    #          current hood jackpot amounts to the .jackpot
    #          "database" file. In addition, it initiates the
    #          shutdown of the BingoManagerAI if the final
    #          game of the evening has been played.
    # Input: task - a task that is spawned by a doMethodLater
    # Output: None
    ############################################################
    def __handleSuperBingoClose(self, task):
        # Save Jackpot Data to File
        self.notify.info("handleSuperBingoClose: Saving Hood Jackpots to DB")
        self.notify.info("handleSuperBingoClose: hoodJackpots %s" %(self.__hoodJackpots))
        for hood in list(self.__hoodJackpots.keys()):
            if self.__hoodJackpots[hood][1]:
                self.__hoodJackpots[hood][0] += BG.ROLLOVER_AMOUNT
                # clamp it if it exceeds jackpot total
                if self.__hoodJackpots[hood][0] > BG.MAX_SUPER_JACKPOT:
                    self.__hoodJackpots[hood][0] = BG.MAX_SUPER_JACKPOT
            else:
                self.__hoodJackpots[hood][1] = BG.MIN_SUPER_JACKPOT

        taskMgr.remove(task)
        self.save()
        if self.finalGame:
            self.shutdown()
            return

        self.waitForIntermission()

    ############################################################
    # Method:  __handleIntermission
    # Purpose: This wrapper method tells the intermission to
    #          start.
    # Input: task - a task that is spawned by a doMethodLater
    # Output: None
    ############################################################
    def __handleIntermission(self, task):
        self.__startIntermission()

    ############################################################
    # Method:  getIntermissionTime
    # Purpose: This method returns the time of when an
    #          intermission began. It is meant to provide a
    #          fairly accurate time countdown for the clients.
    # Input: None
    # Output: returns the timestamp of intermission start
    ############################################################
    def getIntermissionTime(self):
        return self.timeStamp

    ############################################################
    # Method:  __startIntermission
    # Purpose: This method is responsible for starting the
    #          hourly intermission for bingo night.
    # Input: None
    # Output: None
    ############################################################
    def __startIntermission(self):
        for bingoMgr in list(self.doId2do.values()):
            bingoMgr.setFinalGame(BG.INTERMISSION)

        if not self.finalGame:
            currentTime = time.localtime()
            currentMin = currentTime[4]
            currentSec = currentTime[5]

            # Calculate time until the next hour
            waitTime = (60-currentMin)*60 - currentSec
            sec = (currentMin - BG.HOUR_BREAK_MIN)*60 + currentSec
            self.timeStamp = globalClockDelta.getRealNetworkTime() - sec
            self.notify.info('__startIntermission: Timestamp %s'%(self.timeStamp))
        else:
            # In case someone should decide that bingo night does not end on the hour, ie 30 past,
            # then this will allow a five minute intermission to sync up the PBMgrAIs for the
            # final game.
            waitTime = BG.HOUR_BREAK_SESSION
            self.timeStamp = globalClockDelta.getRealNetworkTime()

        self.waitTaskName = 'waitForEndOfIntermission'
        self.notify.info('__startIntermission: Waiting %s seconds until Bingo Night resumes.' %(waitTime))
        taskMgr.doMethodLater(waitTime, self.__resumeBingoNight, self.waitTaskName)
        return Task.done

    ############################################################
    # Method:  __waitForIntermission
    # Purpose: This method is responsible for calculating the
    #          wait time for the hourly intermission for bingo
    #          night.
    # Input: None
    # Output: None
    ############################################################
    def waitForIntermission(self):
        currentTime = time.localtime()
        currentMin = currentTime[4]
        currentSec = currentTime[5]

        # Calculate Amount of time needed for one normal game of Bingo from the
        # Waitcountdown all the way to the gameover. (in secs)
        if currentMin >= BG.HOUR_BREAK_MIN:
            # If the AI starts during bingo night and after the intermission start(a crash or scheduled downtime),
            # then immediately start the intermission to sync all the clients up for the next hour.
            self.__startIntermission()
        else:
            waitTime = ((BG.HOUR_BREAK_MIN - currentMin)*60) - currentSec
            self.waitTaskName = 'waitForIntermission'
            self.notify.info("Waiting %s seconds until Final Game of the Hour should be announced." % (waitTime))
            taskMgr.doMethodLater(waitTime, self.__handleIntermission, self.waitTaskName)

    ############################################################
    # Method:  generateBingoManagers
    # Purpose: This method creates a PondBingoManager for each
    #          pond that is found within the hoods. It searches
    #          through each hood for pond objects and generates
    #          the corresponding ManagerAI objects.
    # Input: None
    # Output: None
    ############################################################
    def generateBingoManagers(self):
        # Create DPBMAI for all ponds in all hoods.
        for hood in self.air.hoods:
            self.createPondBingoMgrAI(hood)

        # Create DPBMAI for every pond in every active estate.
        for estateAI in list(self.air.estateMgr.estate.values()):
            self.createPondBingoMgrAI(estateAI)

    ############################################################
    # Method:  addDistObj
    # Purpose: This method adds the newly created Distributed
    #          object to the BingoManagerAI doId2do list for
    #          easy reference.
    # Input: distObj
    # Output: None
    ############################################################
    def addDistObj(self, distObj):
        self.notify.debug("addDistObj: Adding %s : %s" % (distObj.getDoId(), distObj.zoneId))
        self.doId2do[distObj.getDoId()] = distObj
        self.zoneId2do[distObj.zoneId] = distObj

    def __hoodToUse(self, zoneId):
        hood = ZoneUtil.getCanonicalHoodId(zoneId)
        if hood >= TTG.DynamicZonesBegin:
            hood = TTG.MyEstate

        return hood

    ############################################################
    # Method:  createPondBingoMgrAI
    # Purpose: This method generates PBMgrAI instances for
    #          each pond found in the specified hood. A hood
    #          may be an estate or an actual hood.
    # Input: hood - HoodDataAI or EstateAI object.
    #        dynamic - Will be 1 only if an Estate was generated
    #                  after Bingo Night has started.
    # Output: None
    ############################################################
    def createPondBingoMgrAI(self, hood, dynamic=0):
        if hood.fishingPonds == None:
            self.notify.warning("createPondBingoMgrAI: hood doesn't have any ponds... were they deleted? %s" % hood)
            return

        for pond in hood.fishingPonds:
            # First, optain hood id based on zone id that the pond is located in.
            hoodId = self.__hoodToUse(pond.zoneId)
            if hoodId not in self.hood2doIdList:
                # for now don't start it for minigolf zone and outdoor zone
                continue

            bingoMgr = DistributedPondBingoManagerAI.DistributedPondBingoManagerAI(self.air, pond)
            bingoMgr.generateWithRequired(pond.zoneId)

            self.addDistObj(bingoMgr)
            if hasattr(hood, "addDistObj"):
                hood.addDistObj(bingoMgr)
            pond.setPondBingoManager(bingoMgr)

            # Add the PBMgrAI reference to the hood2doIdList.
            self.hood2doIdList[hoodId].append(bingoMgr.getDoId())

            # Dynamic if this method was called when an estate was generated after
            # Bingo Night has started.
            if dynamic:
                self.startDynPondBingoMgrAI(bingoMgr)

    ############################################################
    # Method:  startDynPondBingoMgrAI
    # Purpose: This method determines what state a Dynamic
    #          Estate PBMgrAI should start in, and then it tells
    #          the PBMgrAI to start.
    # Input: bingoMgr - PondBongoMgrAI Instance
    # Output: None
    ############################################################
    def startDynPondBingoMgrAI(self, bingoMgr):
        currentMin = time.localtime()[4]

        # If the dynamic estate is generated before the intermission starts
        # and it is not the final game of the night, then the PBMgrAI should start
        # in the WaitCountdown state. Otherwise, it should start in the intermission
        # state so that it can sync up with all of the other Estate PBMgrAIs for the
        # super bingo game.
        initState = (((currentMin < BG.HOUR_BREAK_MIN) and (not self.finalGame)) and ['WaitCountdown'] or ['Intermission'])[0]
        bingoMgr.startup(initState)

    ############################################################
    # Method:  removePondBingoMgrAI
    # Purpose: This method generates PBMgrAI instances for
    #          each pond found in the specified hood. A hood
    #          may be an estate or an actual hood.
    # Input: doId - the doId of the PBMgrAI that should be
    #               removed from the dictionaries.
    # Output: None
    ############################################################
    def removePondBingoMgrAI(self, doId):
        if doId in self.doId2do:
            zoneId = self.doId2do[doId].zoneId
            self.notify.info('removePondBingoMgrAI: Removing PondBingoMgrAI %s' %(zoneId))
            hood = self.__hoodToUse(zoneId)
            self.hood2doIdList[hood].remove(doId)
            del self.zoneId2do[zoneId]
            del self.doId2do[doId]
        else:
            self.notify.debug('removeBingoManager: Attempt to remove invalid PondBingoManager %s' % (doId))

    ############################################################
    # Method:  SetFishForPlayer
    # Purpose: This method adds the newly created Distributed
    #          object to the BingoManagerAI doId2do list for
    #          easy reference.
    # Input: distObj
    # Output: None
    ############################################################
    def setAvCatchForPondMgr(self, avId, zoneId, catch):
        self.notify.info('setAvCatchForPondMgr: zoneId %s' %(zoneId))
        if zoneId in self.zoneId2do:
            self.zoneId2do[zoneId].setAvCatch(avId, catch)
        else:
            self.notify.info('setAvCatchForPondMgr Failed: zoneId %s' %(zoneId))

    ############################################################
    # Method:  getFileName
    # Purpose: This method constructs the jackpot filename for
    #          a particular shard.
    # Input: None
    # Output: returns jackpot filename
    ############################################################
    def getFileName(self):
        """Figure out the path to the saved state"""
        f = "%s%s.jackpot" % (self.serverDataFolder, self.shard)
        return f

    ############################################################
    # Method:  saveTo
    # Purpose: This method saves the current jackpot ammounts
    #          to the specified file.
    # Input: file - file to save jackpot amounts
    # Output: None
    ############################################################
    def saveTo(self, file):
        pickle.dump(self.__hoodJackpots, file)

    ############################################################
    # Method:  save
    # Purpose: This method determines where to save the jackpot
    #          amounts.
    # Input: None
    # Output: None
    ############################################################
    def save(self):
        """Save data to default location"""
        try:
            fileName = self.getFileName()
            backup = fileName+ '.jbu'
            if os.path.exists(fileName):
                os.rename(fileName, backup)
            
            file = open(fileName, 'wb')
            file.seek(0)
            self.saveTo(file)
            file.close()
            if os.path.exists(backup):
                os.remove(backup)
        except EnvironmentError:
            self.notify.warning(str(sys.exc_info()[1]))

    ############################################################
    # Method:  loadFrom
    # Purpose: This method loads the jackpot amounts from the
    #          specified file.
    # Input: File - file to load amount from
    # Output: returns a dictionary of the jackpots for this shard
    ############################################################
    def loadFrom(self, file):
        # Default Jackpot Amount
        jackpots = self.DefaultReward
        try:
            jackpots = pickle.load(file)
        except EOFError:
            pass
        return jackpots

    ############################################################
    # Method:  load
    # Purpose: This method determines where to load the jackpot
    #          amounts.
    # Input: None
    # Output: None
    ############################################################
    def load(self):
        """Load Jackpot data from default location"""
        fileName = self.getFileName()
        try:
            file = open(fileName+'.jbu', 'rb')
            if os.path.exists(fileName):
                os.remove(fileName)
        except IOError:
            try:
                file = open(fileName)
            except IOError:
                # Default Jackpot Amount
                return self.DefaultReward

        file.seek(0)
        jackpots = self.loadFrom(file)
        file.close()
        return jackpots

    ############################################################
    # Method:  getSuperJackpot
    # Purpose: This method returns the super jackpot amount for
    #          the specified zone. It calculates which hood
    #          the zone is in and returns the shared jackpot
    #          amount for that hood.
    # Input: zoneId - retrieve jackpot for this zone's hood
    # Output: returns jackpot for hood that zoneid is found in
    ############################################################
    def getSuperJackpot(self, zoneId):
        hood = self.__hoodToUse(zoneId)
        self.notify.info('getSuperJackpot: hoodJackpots %s \t hood %s' % (self.__hoodJackpots, hood))
        return self.__hoodJackpots.get(hood, [BG.MIN_SUPER_JACKPOT])[0]

    ############################################################
    # Method:  __startCloseEvent
    # Purpose: This method starts to close Bingo Night down. One
    #          more super card game will be played at the end
    #          of the hour(unless the times are changed).
    # Input: None
    # Output: None
    ############################################################
    def __startCloseEvent(self):
        self.finalGame = BG.CLOSE_EVENT

        if self.waitTaskName == 'waitForIntermission':
            taskMgr.remove(self.waitTaskName)
            self.__startIntermission()

    ############################################################
    # Method:  handleSuperBingoWin
    # Purpose: This method handles a victory when a super
    #          bingo game has been one. It updates the jackpot
    #          amount and tells each of the other ponds in that
    #          hood that they did not win.
    # Input: zoneId - pond who won the bingo game.
    # Output: None
    ############################################################
    def handleSuperBingoWin(self, zoneId):
        # Reset the Jackpot and unmark the dirty bit.

        hood = self.__hoodToUse(zoneId)
        self.__hoodJackpots[hood][0] = self.DefaultReward[hood][0]
        self.__hoodJackpots[hood][1] = 0

        # tell everyone who won
        #simbase.air.newsManager.bingoWin(zoneId)

        # Tell the other ponds that they did not win and should handle the loss
        for doId in self.hood2doIdList[hood]:
            distObj = self.doId2do[doId]
            if distObj.zoneId != zoneId:
                self.notify.info("handleSuperBingoWin: Did not win in zone %s" %(distObj.zoneId))
                distObj.handleSuperBingoLoss()


