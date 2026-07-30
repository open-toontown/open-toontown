from direct.showbase.PythonUtil import invertDict
from toontown.toonbase import ToontownGlobals
from toontown.coghq import BossbotCountryClubFairwayRoom_Battle00_Cogs
from toontown.coghq import BossbotCountryClubMazeRoom_Battle00_Cogs
from toontown.coghq import BossbotCountryClubMazeRoom_Battle01_Cogs
from toontown.coghq import BossbotCountryClubMazeRoom_Battle02_Cogs
from toontown.coghq import BossbotCountryClubMazeRoom_Battle03_Cogs
from toontown.coghq import NullCogs
from toontown.coghq import BossbotCountryClubKartRoom_Battle00_Cogs
from toontown.coghq import BossbotCountryClubPresidentRoom_Battle00_Cogs

def getCountryClubRoomSpecModule(roomId):
    return CashbotMintSpecModules[roomId]


def getCogSpecModule(roomId):
    roomName = BossbotCountryClubRoomId2RoomName[roomId]
    return CogSpecModules.get(roomName, NullCogs)


def getNumBattles(roomId):
    return roomId2numBattles[roomId]


BossbotCountryClubRoomId2RoomName = {0: 'BossbotCountryClubEntrance_Action00',
 2: 'BossbotCountryClubTeeOffRoom_Action00',
 4: 'BossbotCountryClubFairwayRoom_Battle00',
 5: 'BossbotCountryClubMazeRoom_Battle00',
 6: 'BossbotCountryClubMazeRoom_Battle01',
 7: 'BossbotCountryClubMazeRoom_Battle02',
 9: 'BossbotCountryClubGreenRoom_Action00',
 17: 'BossbotCountryClubKartRoom_Battle00',
 18: 'BossbotCountryClubPresidentRoom_Battle00',
 22: 'BossbotCountryClubTeeOffRoom_Action01',
 32: 'BossbotCountryClubTeeOffRoom_Action02',
 29: 'BossbotCountryClubGreenRoom_Action01',
 39: 'BossbotCountryClubGreenRoom_Action02'}
BossbotCountryClubRoomName2RoomId = invertDict(BossbotCountryClubRoomId2RoomName)
BossbotCountryClubEntranceIDs = (0,)
BossbotCountryClubMiddleRoomIDs = (2, 5, 6)
BossbotCountryClubFinalRoomIDs = (18,)
BossbotCountryClubConnectorRooms = ('phase_12/models/bossbotHQ/Connector_Tunnel_A', 'phase_12/models/bossbotHQ/Connector_Tunnel_B')
CashbotMintSpecModules = {}
if not __debug__ or __execWarnings__:
    print('EXECWARNING CountryClubRoomSpecs: %s' % BossbotCountryClubRoomName2RoomId)
    printStack()
for roomName, roomId in list(BossbotCountryClubRoomName2RoomId.items()):
    exec('from toontown.coghq import %s' % roomName)
    CashbotMintSpecModules[roomId] = eval(roomName)

CogSpecModules = {'BossbotCountryClubFairwayRoom_Battle00': BossbotCountryClubFairwayRoom_Battle00_Cogs,
 'BossbotCountryClubMazeRoom_Battle00': BossbotCountryClubMazeRoom_Battle00_Cogs,
 'BossbotCountryClubMazeRoom_Battle01': BossbotCountryClubMazeRoom_Battle01_Cogs,
 'BossbotCountryClubMazeRoom_Battle02': BossbotCountryClubMazeRoom_Battle02_Cogs,
 'BossbotCountryClubKartRoom_Battle00': BossbotCountryClubKartRoom_Battle00_Cogs,
 'BossbotCountryClubPresidentRoom_Battle00': BossbotCountryClubPresidentRoom_Battle00_Cogs}
roomId2numBattles = {}
for roomName, roomId in list(BossbotCountryClubRoomName2RoomId.items()):
    if roomName not in CogSpecModules:
        roomId2numBattles[roomId] = 0
    else:
        cogSpecModule = CogSpecModules[roomName]
        roomId2numBattles[roomId] = len(cogSpecModule.BattleCells)

name2id = BossbotCountryClubRoomName2RoomId
roomId2numBattles[name2id['BossbotCountryClubTeeOffRoom_Action00']] = 1
del name2id
middleRoomId2numBattles = {}
for roomId in BossbotCountryClubMiddleRoomIDs:
    middleRoomId2numBattles[roomId] = roomId2numBattles[roomId]
