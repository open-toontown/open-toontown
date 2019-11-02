from direct.directnotify import DirectNotifyGlobal
from direct.showbase.PythonUtil import invertDictLossless
from toontown.coghq import CountryClubRoomSpecs
from toontown.toonbase import ToontownGlobals
from direct.showbase.PythonUtil import normalDistrib, lerp
import random

def printAllBossbotInfo():
    print 'roomId: roomName'
    for roomId, roomName in CountryClubRoomSpecs.BossbotCountryClubRoomId2RoomName.items():
        print '%s: %s' % (roomId, roomName)

    print '\nroomId: numBattles'
    for roomId, numBattles in CountryClubRoomSpecs.roomId2numBattles.items():
        print '%s: %s' % (roomId, numBattles)

    print '\ncountryClubId floor roomIds'
    printCountryClubRoomIds()
    print '\ncountryClubId floor numRooms'
    printNumRooms()
    print '\ncountryClubId floor numForcedBattles'
    printNumBattles()


def iterateBossbotCountryClubs(func):
    from toontown.toonbase import ToontownGlobals
    for countryClubId in [ToontownGlobals.BossbotCountryClubIntA, ToontownGlobals.BossbotCountryClubIntB, ToontownGlobals.BossbotCountryClubIntC]:
        for floorNum in xrange(ToontownGlobals.CountryClubNumFloors[countryClubId]):
            func(CountryClubLayout(countryClubId, floorNum))


def printCountryClubInfo():

    def func(ml):
        print ml

    iterateBossbotCountryClubs(func)


def printCountryClubRoomIds():

    def func(ml):
        print ml.getCountryClubId(), ml.getFloorNum(), ml.getRoomIds()

    iterateBossbotCountryClubs(func)


def printCountryClubRoomNames():

    def func(ml):
        print ml.getCountryClubId(), ml.getFloorNum(), ml.getRoomNames()

    iterateBossbotCountryClubs(func)


def printNumRooms():

    def func(ml):
        print ml.getCountryClubId(), ml.getFloorNum(), ml.getNumRooms()

    iterateBossbotCountryClubs(func)


def printNumBattles():

    def func(ml):
        print ml.getCountryClubId(), ml.getFloorNum(), ml.getNumBattles()

    iterateBossbotCountryClubs(func)


ClubLayout3_0 = [(0, 2, 5, 9, 17), (0, 2, 4, 9, 17), (0, 2, 5, 9, 18)]
ClubLayout3_1 = [(0, 2, 5, 9, 17), (0, 2, 4, 9, 17), (0, 2, 5, 9, 18)]
ClubLayout3_2 = [(0, 2, 4, 9, 17), (0, 2, 4, 9, 17), (0, 2, 6, 9, 18)]
ClubLayout6_0 = [(0, 22, 4, 29, 17),
 (0, 22, 5, 29, 17),
 (0, 22, 6, 29, 17),
 (0, 22, 5, 29, 17),
 (0, 22, 6, 29, 17),
 (0, 22, 5, 29, 18)]
ClubLayout6_1 = [(0, 22, 4, 29, 17),
 (0, 22, 6, 29, 17),
 (0, 22, 4, 29, 17),
 (0, 22, 6, 29, 17),
 (0, 22, 4, 29, 17),
 (0, 22, 6, 29, 18)]
ClubLayout6_2 = [(0, 22, 4, 29, 17),
 (0, 22, 6, 29, 17),
 (0, 22, 5, 29, 17),
 (0, 22, 6, 29, 17),
 (0, 22, 5, 29, 17),
 (0, 22, 7, 29, 18)]
ClubLayout9_0 = [(0, 32, 4, 39, 17),
 (0, 32, 5, 39, 17),
 (0, 32, 6, 39, 17),
 (0, 32, 7, 39, 17),
 (0, 32, 5, 39, 17),
 (0, 32, 6, 39, 17),
 (0, 32, 7, 39, 17),
 (0, 32, 7, 39, 17),
 (0, 32, 6, 39, 18)]
ClubLayout9_1 = [(0, 32, 4, 39, 17),
 (0, 32, 5, 39, 17),
 (0, 32, 6, 39, 17),
 (0, 32, 7, 39, 17),
 (0, 32, 5, 39, 17),
 (0, 32, 6, 39, 17),
 (0, 32, 7, 39, 17),
 (0, 32, 7, 39, 17),
 (0, 32, 7, 39, 18)]
ClubLayout9_2 = [(0, 32, 5, 39, 17),
 (0, 32, 5, 39, 17),
 (0, 32, 6, 39, 17),
 (0, 32, 6, 39, 17),
 (0, 32, 5, 39, 17),
 (0, 32, 5, 39, 17),
 (0, 32, 6, 39, 17),
 (0, 32, 6, 39, 17),
 (0, 32, 7, 39, 18)]
countryClubLayouts = [ClubLayout3_0,
 ClubLayout3_1,
 ClubLayout3_2,
 ClubLayout6_0,
 ClubLayout6_1,
 ClubLayout6_2,
 ClubLayout9_0,
 ClubLayout9_1,
 ClubLayout9_2]
testLayout = [ClubLayout3_0,
 ClubLayout3_0,
 ClubLayout3_0,
 ClubLayout6_0,
 ClubLayout6_0,
 ClubLayout6_0,
 ClubLayout9_0,
 ClubLayout9_0,
 ClubLayout9_0]
countryClubLayouts = testLayout

class CountryClubLayout:
    notify = DirectNotifyGlobal.directNotify.newCategory('CountryClubLayout')

    def __init__(self, countryClubId, floorNum, layoutIndex):
        self.countryClubId = countryClubId
        self.floorNum = floorNum
        self.layoutIndex = layoutIndex
        self.roomIds = []
        self.hallways = []
        self.numRooms = 1 + ToontownGlobals.CountryClubNumRooms[self.countryClubId][0]
        self.numHallways = self.numRooms - 1 + 1
        self.roomIds = countryClubLayouts[layoutIndex][floorNum]
        hallwayRng = self.getRng()
        connectorRoomNames = CountryClubRoomSpecs.BossbotCountryClubConnectorRooms
        for i in xrange(self.numHallways):
            self.hallways.append(hallwayRng.choice(connectorRoomNames))

    def _genFloorLayout(self):
        rng = self.getRng()
        startingRoomIDs = CountryClubRoomSpecs.BossbotCountryClubEntranceIDs
        middleRoomIDs = CountryClubRoomSpecs.BossbotCountryClubMiddleRoomIDs
        finalRoomIDs = CountryClubRoomSpecs.BossbotCountryClubFinalRoomIDs

        numBattlesLeft = ToontownGlobals.CountryClubNumBattles[self.countryClubId]

        finalRoomId = rng.choice(finalRoomIDs)
        numBattlesLeft -= CountryClubRoomSpecs.getNumBattles(finalRoomId)

        middleRoomIds = []
        middleRoomsLeft = self.numRooms - 2

        numBattles2middleRoomIds = invertDictLossless(CountryClubRoomSpecs.middleRoomId2numBattles)

        allBattleRooms = []
        for num, roomIds in numBattles2middleRoomIds.items():
            if num > 0:
                allBattleRooms.extend(roomIds)
        while 1:
            allBattleRoomIds = list(allBattleRooms)
            rng.shuffle(allBattleRoomIds)
            battleRoomIds = self._chooseBattleRooms(numBattlesLeft,
                                                    allBattleRoomIds)
            if battleRoomIds is not None:
                break

            CountryClubLayout.notify.info('could not find a valid set of battle rooms, trying again')

        middleRoomIds.extend(battleRoomIds)
        middleRoomsLeft -= len(battleRoomIds)

        if middleRoomsLeft > 0:
            actionRoomIds = numBattles2middleRoomIds[0]
            for i in xrange(middleRoomsLeft):
                roomId = rng.choice(actionRoomIds)
                actionRoomIds.remove(roomId)
                middleRoomIds.append(roomId)

        roomIds = []

        roomIds.append(rng.choice(startingRoomIDs))

        middleRoomIds.sort()
        print 'middleRoomIds=%s' % middleRoomIds
        roomIds.extend(middleRoomIds)

        roomIds.append(finalRoomId)

        return roomIds

    def getNumRooms(self):
        return len(self.roomIds)

    def getRoomId(self, n):
        return self.roomIds[n]

    def getRoomIds(self):
        return self.roomIds[:]

    def getRoomNames(self):
        names = []
        for roomId in self.roomIds:
            names.append(CountryClubRoomSpecs.BossbotCountryClubRoomId2RoomName[roomId])

        return names

    def getNumHallways(self):
        return len(self.hallways)

    def getHallwayModel(self, n):
        return self.hallways[n]

    def getNumBattles(self):
        numBattles = 0
        for roomId in self.getRoomIds():
            numBattles += CountryClubRoomSpecs.roomId2numBattles[roomId]

        return numBattles

    def getCountryClubId(self):
        return self.countryClubId

    def getFloorNum(self):
        return self.floorNum

    def getRng(self):
        return random.Random(self.countryClubId * self.floorNum)

    def _chooseBattleRooms(self, numBattlesLeft, allBattleRoomIds, baseIndex = 0, chosenBattleRooms = None):
        if chosenBattleRooms is None:
            chosenBattleRooms = []
        while baseIndex < len(allBattleRoomIds):
            nextRoomId = allBattleRoomIds[baseIndex]
            baseIndex += 1
            newNumBattlesLeft = numBattlesLeft - CountryClubRoomSpecs.middleRoomId2numBattles[nextRoomId]
            if newNumBattlesLeft < 0:
                continue
            elif newNumBattlesLeft == 0:
                chosenBattleRooms.append(nextRoomId)
                return chosenBattleRooms
            chosenBattleRooms.append(nextRoomId)
            result = self._chooseBattleRooms(newNumBattlesLeft, allBattleRoomIds, baseIndex, chosenBattleRooms)
            if result is not None:
                return result
            else:
                del chosenBattleRooms[-1:]
        else:
            return

        return

    def __str__(self):
        return 'CountryClubLayout: id=%s, layoutIndex=%s, floor=%s, numRooms=%s, numBattles=%s' % (self.countryClubId,
         self.layoutIndex,
         self.floorNum,
         self.getNumRooms(),
         self.getNumBattles())

    def __repr__(self):
        return str(self)
