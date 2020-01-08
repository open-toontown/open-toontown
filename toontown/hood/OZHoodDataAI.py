from direct.directnotify import DirectNotifyGlobal
from . import HoodDataAI, ZoneUtil
from toontown.toonbase import ToontownGlobals
from toontown.safezone import OZTreasurePlannerAI
from toontown.racing import DistributedStartingBlockAI
from pandac.PandaModules import *
from libtoontown import *
from toontown.racing.RaceGlobals import *
from toontown.classicchars import DistributedGoofySpeedwayAI
from toontown.safezone import DistributedPicnicBasketAI
from toontown.classicchars import DistributedChipAI
from toontown.classicchars import DistributedDaleAI
from toontown.distributed import DistributedTimerAI
from toontown.safezone import DistributedPicnicTableAI
from toontown.safezone import DistributedChineseCheckersAI
from toontown.safezone import DistributedCheckersAI
if __debug__:
    import pdb

class OZHoodDataAI(HoodDataAI.HoodDataAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('OZHoodDataAI')

    def __init__(self, air, zoneId=None):
        hoodId = ToontownGlobals.OutdoorZone
        if zoneId == None:
            zoneId = hoodId
        HoodDataAI.HoodDataAI.__init__(self, air, zoneId, hoodId)
        self.classicChars = []
        return

    def startup(self):
        HoodDataAI.HoodDataAI.startup(self)
        if simbase.air.config.GetBool('create-chip-and-dale', 1):
            chip = DistributedChipAI.DistributedChipAI(self.air)
            chip.generateWithRequired(self.zoneId)
            chip.start()
            self.addDistObj(chip)
            self.classicChars.append(chip)
            dale = DistributedDaleAI.DistributedDaleAI(self.air, chip.doId)
            dale.generateWithRequired(self.zoneId)
            dale.start()
            self.addDistObj(dale)
            self.classicChars.append(dale)
            chip.setDaleId(dale.doId)
        self.treasurePlanner = OZTreasurePlannerAI.OZTreasurePlannerAI(self.zoneId)
        self.treasurePlanner.start()
        self.timer = DistributedTimerAI.DistributedTimerAI(self.air)
        self.timer.generateWithRequired(self.zoneId)
        self.createPicnicTables()
        if simbase.config.GetBool('want-game-tables', 0):
            self.createGameTables()

    def cleanup(self):
        self.timer.delete()
        taskMgr.removeTasksMatching(str(self) + '_leaderBoardSwitch')
        for board in self.leaderBoards:
            board.delete()

        del self.leaderBoards

    def createLeaderBoards(self):
        self.leaderBoards = []
        dnaStore = DNAStorage()
        dnaData = simbase.air.loadDNAFileAI(dnaStore, simbase.air.lookupDNAFileName('goofy_speedway_sz.dna'))
        if isinstance(dnaData, DNAData):
            self.leaderBoards = self.air.findLeaderBoards(dnaData, self.zoneId)
        for distObj in self.leaderBoards:
            if distObj:
                if distObj.getName().count('city'):
                    type = 'city'
                else:
                    if distObj.getName().count('stadium'):
                        type = 'stadium'
                    else:
                        if distObj.getName().count('country'):
                            type = 'country'
                for subscription in LBSubscription[type]:
                    distObj.subscribeTo(subscription)

                self.addDistObj(distObj)

    def __cycleLeaderBoards(self, task=None):
        messenger.send('GS_LeaderBoardSwap')
        taskMgr.doMethodLater(self.cycleDuration, self.__cycleLeaderBoards, str(self) + '_leaderBoardSwitch')

    def createStartingBlocks(self):
        self.racingPads = []
        self.viewingPads = []
        self.viewingBlocks = []
        self.startingBlocks = []
        self.foundRacingPadGroups = []
        self.foundViewingPadGroups = []
        self.golfKartPads = []
        self.golfKartPadGroups = []
        for zone in self.air.zoneTable[self.canonicalHoodId]:
            zoneId = ZoneUtil.getTrueZoneId(zone[0], self.zoneId)
            dnaData = self.air.dnaDataMap.get(zone[0], None)
            if isinstance(dnaData, DNAData):
                area = ZoneUtil.getCanonicalZoneId(zoneId)
                foundRacingPads, foundRacingPadGroups = self.air.findRacingPads(dnaData, zoneId, area, overrideDNAZone=True)
                foundViewingPads, foundViewingPadGroups = self.air.findRacingPads(dnaData, zoneId, area, type='viewing_pad', overrideDNAZone=True)
                self.racingPads += foundRacingPads
                self.foundRacingPadGroups += foundRacingPadGroups
                self.viewingPads += foundViewingPads
                self.foundViewingPadGroups += foundViewingPadGroups

        self.startingBlocks = []
        for dnaGroup, distRacePad in zip(self.foundRacingPadGroups, self.racingPads):
            startingBlocks = self.air.findStartingBlocks(dnaGroup, distRacePad)
            self.startingBlocks += startingBlocks
            for startingBlock in startingBlocks:
                distRacePad.addStartingBlock(startingBlock)

        for distObj in self.startingBlocks:
            self.addDistObj(distObj)

        for dnaGroup, distViewPad in zip(self.foundViewingPadGroups, self.viewingPads):
            startingBlocks = self.air.findStartingBlocks(dnaGroup, distViewPad)
            for viewingBlock in self.viewingBlocks:
                distViewPad.addStartingBlock(viewingBlocks)

        for distObj in self.viewingBlocks:
            self.addDistObj(distObj)

        for viewPad in self.viewingPads:
            self.addDistObj(viewPad)

        for racePad in self.racingPads:
            racePad.request('WaitEmpty')
            self.addDistObj(racePad)

        return

    def findAndCreateGameTables(self, dnaGroup, zoneId, area, overrideDNAZone = 0, type = 'game_table'):
        picnicTables = []
        picnicTableGroups = []
        if isinstance(dnaGroup, DNAGroup) and dnaGroup.getName().find(type) >= 0:
            if type == 'game_table':
                nameInfo = dnaGroup.getName().split('_')
                pos = Point3(0, 0, 0)
                hpr = Point3(0, 0, 0)
                for i in range(dnaGroup.getNumChildren()):
                    childDnaGroup = dnaGroup.at(i)
                    if childDnaGroup.getName().find('game_table') >= 0:
                        pos = childDnaGroup.getPos()
                        hpr = childDnaGroup.getHpr()
                        break

                picnicTable = DistributedPicnicTableAI.DistributedPicnicTableAI(self.air, zoneId, nameInfo[2], pos[0], pos[1], pos[2], hpr[0], hpr[1], hpr[2])
                picnicTables.append(picnicTable)
        else:
            if isinstance(dnaGroup, DNAVisGroup) and not overrideDNAZone:
                zoneId = ZoneUtil.getTrueZoneId(int(dnaGroup.getName().split(':')[0]), zoneId)
            for i in range(dnaGroup.getNumChildren()):
                childPicnicTables = self.findAndCreateGameTables(dnaGroup.at(i), zoneId, area, overrideDNAZone, type)
                picnicTables += childPicnicTables

        return picnicTables

    def findAndCreatePicnicTables(self, dnaGroup, zoneId, area, overrideDNAZone = 0, type = 'picnic_table'):
        picnicTables = []
        picnicTableGroups = []
        if isinstance(dnaGroup, DNAGroup) and dnaGroup.getName().find(type) >= 0:
            if type == 'picnic_table':
                nameInfo = dnaGroup.getName().split('_')
                pos = Point3(0, 0, 0)
                hpr = Point3(0, 0, 0)
                for i in range(dnaGroup.getNumChildren()):
                    childDnaGroup = dnaGroup.at(i)
                    if childDnaGroup.getName().find('picnic_table') >= 0:
                        pos = childDnaGroup.getPos()
                        hpr = childDnaGroup.getHpr()
                        break

                picnicTable = DistributedPicnicBasketAI.DistributedPicnicBasketAI(self.air, nameInfo[2], pos[0], pos[1], pos[2], hpr[0], hpr[1], hpr[2])
                picnicTable.generateWithRequired(zoneId)
                picnicTables.append(picnicTable)
        else:
            if isinstance(dnaGroup, DNAVisGroup) and not overrideDNAZone:
                zoneId = ZoneUtil.getTrueZoneId(int(dnaGroup.getName().split(':')[0]), zoneId)
            for i in range(dnaGroup.getNumChildren()):
                childPicnicTables = self.findAndCreatePicnicTables(dnaGroup.at(i), zoneId, area, overrideDNAZone, type)
                picnicTables += childPicnicTables

        return picnicTables

    def createGameTables(self):
        self.gameTables = []
        for zone in self.air.zoneTable[self.canonicalHoodId]:
            zoneId = ZoneUtil.getTrueZoneId(zone[0], self.zoneId)
            dnaData = self.air.dnaDataMap.get(zone[0], None)
            if isinstance(dnaData, DNAData):
                area = ZoneUtil.getCanonicalZoneId(zoneId)
                foundTables = self.findAndCreateGameTables(dnaData, zoneId, area, overrideDNAZone=True)
                self.gameTables += foundTables

        for picnicTable in self.gameTables:
            self.addDistObj(picnicTable)

        return

    def createPicnicTables(self):
        self.picnicTables = []
        for zone in self.air.zoneTable[self.canonicalHoodId]:
            zoneId = ZoneUtil.getTrueZoneId(zone[0], self.zoneId)
            dnaData = self.air.dnaDataMap.get(zone[0], None)
            if isinstance(dnaData, DNAData):
                area = ZoneUtil.getCanonicalZoneId(zoneId)
                foundTables = self.findAndCreatePicnicTables(dnaData, zoneId, area, overrideDNAZone=True)
                self.picnicTables += foundTables

        for picnicTable in self.picnicTables:
            picnicTable.start()
            self.addDistObj(picnicTable)

        return

    def findStartingBlocks(self, dnaRacingPadGroup, distRacePad):
        startingBlocks = []
        for i in range(dnaRacingPadGroup.getNumChildren()):
            dnaGroup = dnaRacingPadGroup.at(i)
            if dnaGroup.getName().find('starting_block') >= 0:
                padLocation = dnaGroup.getName().split('_')[2]
                pos = dnaGroup.getPos()
                hpr = dnaGroup.getHpr()
                if isinstance(distRacePad, DistributedRacePadAI):
                    sb = DistributedStartingBlockAI(self, distRacePad, pos[0], pos[1], pos[2], hpr[0], hpr[1], hpr[2], int(padLocation))
                else:
                    sb = DistributedViewingBlockAI(self, distRacePad, pos[0], pos[1], pos[2], hpr[0], hpr[1], hpr[2], int(padLocation))
                sb.generateWithRequired(distRacePad.zoneId)
                startingBlocks.append(sb)
            else:
                self.notify.debug('Found dnaGroup that is not a starting_block under a race pad group')

        return startingBlocks
