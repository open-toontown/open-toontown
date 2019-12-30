from . import TTLocalizer
from otp.otpbase.OTPGlobals import *
from direct.showbase.PythonUtil import Enum, invertDict
from pandac.PandaModules import BitMask32, Vec4
MapHotkeyOn = 'alt'
MapHotkeyOff = 'alt-up'
MapHotkey = 'alt'
AccountDatabaseChannelId = 4008
ToonDatabaseChannelId = 4021
DoodleDatabaseChannelId = 4023
DefaultDatabaseChannelId = AccountDatabaseChannelId
DatabaseIdFromClassName = {'Account': AccountDatabaseChannelId}
CogHQCameraFov = 60.0
BossBattleCameraFov = 72.0
MakeAToonCameraFov = 52.0
CeilingBitmask = BitMask32(256)
FloorEventBitmask = BitMask32(16)
PieBitmask = BitMask32(256)
PetBitmask = BitMask32(8)
CatchGameBitmask = BitMask32(16)
CashbotBossObjectBitmask = BitMask32(16)
FurnitureSideBitmask = BitMask32(32)
FurnitureTopBitmask = BitMask32(64)
FurnitureDragBitmask = BitMask32(128)
PetLookatPetBitmask = BitMask32(256)
PetLookatNonPetBitmask = BitMask32(512)
BanquetTableBitmask = BitMask32(1024)
FullPies = 65535
CogHQCameraFar = 900.0
CogHQCameraNear = 1.0
CashbotHQCameraFar = 2000.0
CashbotHQCameraNear = 1.0
LawbotHQCameraFar = 3000.0
LawbotHQCameraNear = 1.0
BossbotHQCameraFar = 3000.0
BossbotHQCameraNear = 1.0
SpeedwayCameraFar = 8000.0
SpeedwayCameraNear = 1.0
MaxMailboxContents = 30
MaxHouseItems = 45
MaxAccessories = 50
ExtraDeletedItems = 5
DeletedItemLifetime = 7 * 24 * 60
CatalogNumWeeksPerSeries = 13
CatalogNumWeeks = 78
PetFloorCollPriority = 5
PetPanelProximityPriority = 6
P_NoTrunk = -28
P_AlreadyOwnBiggerCloset = -27
P_ItemAlreadyRented = -26
P_OnAwardOrderListFull = -25
P_AwardMailboxFull = -24
P_ItemInPetTricks = -23
P_ItemInMyPhrases = -22
P_ItemOnAwardOrder = -21
P_ItemInAwardMailbox = -20
P_ItemAlreadyWorn = -19
P_ItemInCloset = -18
P_ItemOnGiftOrder = -17
P_ItemOnOrder = -16
P_ItemInMailbox = -15
P_PartyNotFound = 14
P_WillNotFit = -13
P_NotAGift = -12
P_OnOrderListFull = -11
P_MailboxFull = -10
P_NoPurchaseMethod = -9
P_ReachedPurchaseLimit = -8
P_NoRoomForItem = -7
P_NotShopping = -6
P_NotAtMailbox = -5
P_NotInCatalog = -4
P_NotEnoughMoney = -3
P_InvalidIndex = -2
P_UserCancelled = -1
P_ItemAvailable = 1
P_ItemOnOrder = 2
P_ItemUnneeded = 3
GIFT_user = 0
GIFT_admin = 1
GIFT_RAT = 2
GIFT_mobile = 3
GIFT_cogs = 4
GIFT_partyrefund = 5
FM_InvalidItem = -7
FM_NondeletableItem = -6
FM_InvalidIndex = -5
FM_NotOwner = -4
FM_NotDirector = -3
FM_RoomFull = -2
FM_HouseFull = -1
FM_MovedItem = 1
FM_SwappedItem = 2
FM_DeletedItem = 3
FM_RecoveredItem = 4
SPDonaldsBoat = 3
SPMinniesPiano = 4
CEVirtual = 14
MaxHpLimit = 137
MaxCarryLimit = 80
MaxQuestCarryLimit = 4
MaxCogSuitLevel = 50 - 1
CogSuitHPLevels = (15 - 1,
 20 - 1,
 30 - 1,
 40 - 1,
 50 - 1)
setInterfaceFont(TTLocalizer.InterfaceFont)
setSignFont(TTLocalizer.SignFont)
from toontown.toontowngui import TTDialog
setDialogClasses(TTDialog.TTDialog, TTDialog.TTGlobalDialog)
ToonFont = None
BuildingNametagFont = None
MinnieFont = None
SuitFont = None

def getToonFont():
    global ToonFont
    if ToonFont == None:
        ToonFont = loader.loadFont(TTLocalizer.ToonFont, lineHeight=1.0)
    return ToonFont


def getBuildingNametagFont():
    global BuildingNametagFont
    if BuildingNametagFont == None:
        BuildingNametagFont = loader.loadFont(TTLocalizer.BuildingNametagFont)
    return BuildingNametagFont


def getMinnieFont():
    global MinnieFont
    if MinnieFont == None:
        MinnieFont = loader.loadFont(TTLocalizer.MinnieFont)
    return MinnieFont


def getSuitFont():
    global SuitFont
    if SuitFont == None:
        SuitFont = loader.loadFont(TTLocalizer.SuitFont, pixelsPerUnit=40, spaceAdvance=0.25, lineHeight=1.0)
    return SuitFont


DonaldsDock = 1000
ToontownCentral = 2000
TheBrrrgh = 3000
MinniesMelodyland = 4000
DaisyGardens = 5000
OutdoorZone = 6000
FunnyFarm = 7000
GoofySpeedway = 8000
DonaldsDreamland = 9000
BarnacleBoulevard = 1100
SeaweedStreet = 1200
LighthouseLane = 1300
SillyStreet = 2100
LoopyLane = 2200
PunchlinePlace = 2300
WalrusWay = 3100
SleetStreet = 3200
PolarPlace = 3300
AltoAvenue = 4100
BaritoneBoulevard = 4200
TenorTerrace = 4300
ElmStreet = 5100
MapleStreet = 5200
OakStreet = 5300
LullabyLane = 9100
PajamaPlace = 9200
ToonHall = 2513
HoodHierarchy = {ToontownCentral: (SillyStreet, LoopyLane, PunchlinePlace),
 DonaldsDock: (BarnacleBoulevard, SeaweedStreet, LighthouseLane),
 TheBrrrgh: (WalrusWay, SleetStreet, PolarPlace),
 MinniesMelodyland: (AltoAvenue, BaritoneBoulevard, TenorTerrace),
 DaisyGardens: (ElmStreet, MapleStreet, OakStreet),
 DonaldsDreamland: (LullabyLane, PajamaPlace),
 GoofySpeedway: ()}
WelcomeValleyToken = 0
BossbotHQ = 10000
BossbotLobby = 10100
BossbotCountryClubIntA = 10500
BossbotCountryClubIntB = 10600
BossbotCountryClubIntC = 10700
SellbotHQ = 11000
SellbotLobby = 11100
SellbotFactoryExt = 11200
SellbotFactoryInt = 11500
CashbotHQ = 12000
CashbotLobby = 12100
CashbotMintIntA = 12500
CashbotMintIntB = 12600
CashbotMintIntC = 12700
LawbotHQ = 13000
LawbotLobby = 13100
LawbotOfficeExt = 13200
LawbotOfficeInt = 13300
LawbotStageIntA = 13300
LawbotStageIntB = 13400
LawbotStageIntC = 13500
LawbotStageIntD = 13600
Tutorial = 15000
MyEstate = 16000
GolfZone = 17000
PartyHood = 18000
HoodsAlwaysVisited = [17000, 18000]
WelcomeValleyBegin = 22000
WelcomeValleyEnd = 61000
DynamicZonesBegin = 61000
DynamicZonesEnd = 1 << 20
cogDept2index = {'c': 0,
 'l': 1,
 'm': 2,
 's': 3}
cogIndex2dept = invertDict(cogDept2index)
HQToSafezone = {SellbotHQ: DaisyGardens,
 CashbotHQ: DonaldsDreamland,
 LawbotHQ: TheBrrrgh,
 BossbotHQ: DonaldsDock}
CogDeptNames = [TTLocalizer.Bossbot,
 TTLocalizer.Lawbot,
 TTLocalizer.Cashbot,
 TTLocalizer.Sellbot]

def cogHQZoneId2deptIndex(zone):
    if zone >= 13000 and zone <= 13999:
        return 1
    elif zone >= 12000:
        return 2
    elif zone >= 11000:
        return 3
    else:
        return 0


def cogHQZoneId2dept(zone):
    return cogIndex2dept[cogHQZoneId2deptIndex(zone)]


def dept2cogHQ(dept):
    dept2hq = {'c': BossbotHQ,
     'l': LawbotHQ,
     'm': CashbotHQ,
     's': SellbotHQ}
    return dept2hq[dept]


MockupFactoryId = 0
MintNumFloors = {CashbotMintIntA: 20,
 CashbotMintIntB: 20,
 CashbotMintIntC: 20}
CashbotMintCogLevel = 10
CashbotMintSkelecogLevel = 11
CashbotMintBossLevel = 12
MintNumBattles = {CashbotMintIntA: 4,
 CashbotMintIntB: 6,
 CashbotMintIntC: 8}
MintCogBuckRewards = {CashbotMintIntA: 8,
 CashbotMintIntB: 14,
 CashbotMintIntC: 20}
MintNumRooms = {CashbotMintIntA: 2 * (6,) + 5 * (7,) + 5 * (8,) + 5 * (9,) + 3 * (10,),
 CashbotMintIntB: 3 * (8,) + 6 * (9,) + 6 * (10,) + 5 * (11,),
 CashbotMintIntC: 4 * (10,) + 10 * (11,) + 6 * (12,)}
BossbotCountryClubCogLevel = 11
BossbotCountryClubSkelecogLevel = 12
BossbotCountryClubBossLevel = 12
CountryClubNumRooms = {BossbotCountryClubIntA: (4,),
 BossbotCountryClubIntB: 3 * (8,) + 6 * (9,) + 6 * (10,) + 5 * (11,),
 BossbotCountryClubIntC: 4 * (10,) + 10 * (11,) + 6 * (12,)}
CountryClubNumBattles = {BossbotCountryClubIntA: 3,
 BossbotCountryClubIntB: 2,
 BossbotCountryClubIntC: 3}
CountryClubCogBuckRewards = {BossbotCountryClubIntA: 8,
 BossbotCountryClubIntB: 14,
 BossbotCountryClubIntC: 20}
LawbotStageCogLevel = 10
LawbotStageSkelecogLevel = 11
LawbotStageBossLevel = 12
StageNumBattles = {LawbotStageIntA: 0,
 LawbotStageIntB: 0,
 LawbotStageIntC: 0,
 LawbotStageIntD: 0}
StageNoticeRewards = {LawbotStageIntA: 75,
 LawbotStageIntB: 150,
 LawbotStageIntC: 225,
 LawbotStageIntD: 300}
StageNumRooms = {LawbotStageIntA: 2 * (6,) + 5 * (7,) + 5 * (8,) + 5 * (9,) + 3 * (10,),
 LawbotStageIntB: 3 * (8,) + 6 * (9,) + 6 * (10,) + 5 * (11,),
 LawbotStageIntC: 4 * (10,) + 10 * (11,) + 6 * (12,),
 LawbotStageIntD: 4 * (10,) + 10 * (11,) + 6 * (12,)}
FT_FullSuit = 'fullSuit'
FT_Leg = 'leg'
FT_Arm = 'arm'
FT_Torso = 'torso'
factoryId2factoryType = {MockupFactoryId: FT_FullSuit,
 SellbotFactoryInt: FT_FullSuit,
 LawbotOfficeInt: FT_FullSuit}
StreetNames = TTLocalizer.GlobalStreetNames
StreetBranchZones = list(StreetNames.keys())
Hoods = (DonaldsDock,
 ToontownCentral,
 TheBrrrgh,
 MinniesMelodyland,
 DaisyGardens,
 OutdoorZone,
 FunnyFarm,
 GoofySpeedway,
 DonaldsDreamland,
 BossbotHQ,
 SellbotHQ,
 CashbotHQ,
 LawbotHQ,
 GolfZone)
HoodsForTeleportAll = (DonaldsDock,
 ToontownCentral,
 TheBrrrgh,
 MinniesMelodyland,
 DaisyGardens,
 OutdoorZone,
 GoofySpeedway,
 DonaldsDreamland,
 BossbotHQ,
 SellbotHQ,
 CashbotHQ,
 LawbotHQ,
 GolfZone)
NoPreviousGameId = 0
RaceGameId = 1
CannonGameId = 2
TagGameId = 3
PatternGameId = 4
RingGameId = 5
MazeGameId = 6
TugOfWarGameId = 7
CatchGameId = 8
DivingGameId = 9
TargetGameId = 10
PairingGameId = 11
VineGameId = 12
IceGameId = 13
CogThiefGameId = 14
TwoDGameId = 15
PhotoGameId = 16
TravelGameId = 100
MinigameNames = {'race': RaceGameId,
 'cannon': CannonGameId,
 'tag': TagGameId,
 'pattern': PatternGameId,
 'minnie': PatternGameId,
 'match': PatternGameId,
 'matching': PatternGameId,
 'ring': RingGameId,
 'maze': MazeGameId,
 'tug': TugOfWarGameId,
 'catch': CatchGameId,
 'diving': DivingGameId,
 'target': TargetGameId,
 'pairing': PairingGameId,
 'vine': VineGameId,
 'ice': IceGameId,
 'thief': CogThiefGameId,
 '2d': TwoDGameId,
 'photo': PhotoGameId,
 'travel': TravelGameId}
MinigameTemplateId = -1
MinigameIDs = (RaceGameId,
 CannonGameId,
 TagGameId,
 PatternGameId,
 RingGameId,
 MazeGameId,
 TugOfWarGameId,
 CatchGameId,
 DivingGameId,
 TargetGameId,
 PairingGameId,
 VineGameId,
 IceGameId,
 CogThiefGameId,
 TwoDGameId,
 PhotoGameId,
 TravelGameId)
MinigamePlayerMatrix = {1: (CannonGameId,
     RingGameId,
     MazeGameId,
     TugOfWarGameId,
     CatchGameId,
     DivingGameId,
     TargetGameId,
     PairingGameId,
     VineGameId,
     CogThiefGameId,
     TwoDGameId),
 2: (CannonGameId,
     PatternGameId,
     RingGameId,
     TagGameId,
     MazeGameId,
     TugOfWarGameId,
     CatchGameId,
     DivingGameId,
     TargetGameId,
     PairingGameId,
     VineGameId,
     IceGameId,
     CogThiefGameId,
     TwoDGameId),
 3: (CannonGameId,
     PatternGameId,
     RingGameId,
     TagGameId,
     RaceGameId,
     MazeGameId,
     TugOfWarGameId,
     CatchGameId,
     DivingGameId,
     TargetGameId,
     PairingGameId,
     VineGameId,
     IceGameId,
     CogThiefGameId,
     TwoDGameId),
 4: (CannonGameId,
     PatternGameId,
     RingGameId,
     TagGameId,
     RaceGameId,
     MazeGameId,
     TugOfWarGameId,
     CatchGameId,
     DivingGameId,
     TargetGameId,
     PairingGameId,
     VineGameId,
     IceGameId,
     CogThiefGameId,
     TwoDGameId)}
MinigameReleaseDates = {IceGameId: (2008, 8, 5),
 PhotoGameId: (2008, 8, 13),
 TwoDGameId: (2008, 8, 20),
 CogThiefGameId: (2008, 8, 27)}
KeyboardTimeout = 300
phaseMap = {Tutorial: 4,
 ToontownCentral: 4,
 MyEstate: 5.5,
 DonaldsDock: 6,
 MinniesMelodyland: 6,
 GoofySpeedway: 6,
 TheBrrrgh: 8,
 DaisyGardens: 8,
 FunnyFarm: 8,
 DonaldsDreamland: 8,
 OutdoorZone: 8,
 BossbotHQ: 12,
 SellbotHQ: 9,
 CashbotHQ: 10,
 LawbotHQ: 11,
 GolfZone: 8,
 PartyHood: 13}
streetPhaseMap = {ToontownCentral: 5,
 DonaldsDock: 6,
 MinniesMelodyland: 6,
 GoofySpeedway: 6,
 TheBrrrgh: 8,
 DaisyGardens: 8,
 FunnyFarm: 8,
 DonaldsDreamland: 8,
 OutdoorZone: 8,
 BossbotHQ: 12,
 SellbotHQ: 9,
 CashbotHQ: 10,
 LawbotHQ: 11,
 PartyHood: 13}
dnaMap = {Tutorial: 'toontown_central',
 ToontownCentral: 'toontown_central',
 DonaldsDock: 'donalds_dock',
 MinniesMelodyland: 'minnies_melody_land',
 GoofySpeedway: 'goofy_speedway',
 TheBrrrgh: 'the_burrrgh',
 DaisyGardens: 'daisys_garden',
 FunnyFarm: 'not done yet',
 DonaldsDreamland: 'donalds_dreamland',
 OutdoorZone: 'outdoor_zone',
 BossbotHQ: 'cog_hq_bossbot',
 SellbotHQ: 'cog_hq_sellbot',
 CashbotHQ: 'cog_hq_cashbot',
 LawbotHQ: 'cog_hq_lawbot',
 GolfZone: 'golf_zone'}
hoodNameMap = {DonaldsDock: TTLocalizer.DonaldsDock,
 ToontownCentral: TTLocalizer.ToontownCentral,
 TheBrrrgh: TTLocalizer.TheBrrrgh,
 MinniesMelodyland: TTLocalizer.MinniesMelodyland,
 DaisyGardens: TTLocalizer.DaisyGardens,
 OutdoorZone: TTLocalizer.OutdoorZone,
 FunnyFarm: TTLocalizer.FunnyFarm,
 GoofySpeedway: TTLocalizer.GoofySpeedway,
 DonaldsDreamland: TTLocalizer.DonaldsDreamland,
 BossbotHQ: TTLocalizer.BossbotHQ,
 SellbotHQ: TTLocalizer.SellbotHQ,
 CashbotHQ: TTLocalizer.CashbotHQ,
 LawbotHQ: TTLocalizer.LawbotHQ,
 Tutorial: TTLocalizer.Tutorial,
 MyEstate: TTLocalizer.MyEstate,
 GolfZone: TTLocalizer.GolfZone,
 PartyHood: TTLocalizer.PartyHood}
safeZoneCountMap = {MyEstate: 8,
 Tutorial: 6,
 ToontownCentral: 6,
 DonaldsDock: 10,
 MinniesMelodyland: 5,
 GoofySpeedway: 500,
 TheBrrrgh: 8,
 DaisyGardens: 9,
 FunnyFarm: 500,
 DonaldsDreamland: 5,
 OutdoorZone: 500,
 GolfZone: 500,
 PartyHood: 500}
townCountMap = {MyEstate: 8,
 Tutorial: 40,
 ToontownCentral: 37,
 DonaldsDock: 40,
 MinniesMelodyland: 40,
 GoofySpeedway: 40,
 TheBrrrgh: 40,
 DaisyGardens: 40,
 FunnyFarm: 40,
 DonaldsDreamland: 40,
 OutdoorZone: 40,
 PartyHood: 20}
hoodCountMap = {MyEstate: 2,
 Tutorial: 2,
 ToontownCentral: 2,
 DonaldsDock: 2,
 MinniesMelodyland: 2,
 GoofySpeedway: 2,
 TheBrrrgh: 2,
 DaisyGardens: 2,
 FunnyFarm: 2,
 DonaldsDreamland: 2,
 OutdoorZone: 2,
 BossbotHQ: 2,
 SellbotHQ: 43,
 CashbotHQ: 2,
 LawbotHQ: 2,
 GolfZone: 2,
 PartyHood: 2}
TrophyStarLevels = (10,
 20,
 30,
 50,
 75,
 100)
TrophyStarColors = (Vec4(0.9, 0.6, 0.2, 1),
 Vec4(0.9, 0.6, 0.2, 1),
 Vec4(0.8, 0.8, 0.8, 1),
 Vec4(0.8, 0.8, 0.8, 1),
 Vec4(1, 1, 0, 1),
 Vec4(1, 1, 0, 1))
MickeySpeed = 5.0
VampireMickeySpeed = 1.15
MinnieSpeed = 3.2
WitchMinnieSpeed = 1.8
DonaldSpeed = 3.68
FrankenDonaldSpeed = 0.9
DaisySpeed = 2.3
GoofySpeed = 5.2
SuperGoofySpeed = 1.6
PlutoSpeed = 5.5
WesternPlutoSpeed = 3.2
ChipSpeed = 3
DaleSpeed = 3.5
DaleOrbitDistance = 3
SuitWalkSpeed = 4.8
PieCodeBossCog = 1
PieCodeNotBossCog = 2
PieCodeToon = 3
PieCodeBossInsides = 4
PieCodeDefensePan = 5
PieCodeProsecutionPan = 6
PieCodeLawyer = 7
PieCodeColors = {PieCodeBossCog: None,
 PieCodeNotBossCog: (0.8,
                     0.8,
                     0.8,
                     1),
 PieCodeToon: None}
BossCogRollSpeed = 7.5
BossCogTurnSpeed = 20
BossCogTreadSpeed = 3.5
BossCogDizzy = 0
BossCogElectricFence = 1
BossCogSwatLeft = 2
BossCogSwatRight = 3
BossCogAreaAttack = 4
BossCogFrontAttack = 5
BossCogRecoverDizzyAttack = 6
BossCogDirectedAttack = 7
BossCogStrafeAttack = 8
BossCogNoAttack = 9
BossCogGoonZap = 10
BossCogSlowDirectedAttack = 11
BossCogDizzyNow = 12
BossCogGavelStomp = 13
BossCogGavelHandle = 14
BossCogLawyerAttack = 15
BossCogMoveAttack = 16
BossCogGolfAttack = 17
BossCogGolfAreaAttack = 18
BossCogGearDirectedAttack = 19
BossCogOvertimeAttack = 20
BossCogAttackTimes = {BossCogElectricFence: 0,
 BossCogSwatLeft: 5.5,
 BossCogSwatRight: 5.5,
 BossCogAreaAttack: 4.21,
 BossCogFrontAttack: 2.65,
 BossCogRecoverDizzyAttack: 5.1,
 BossCogDirectedAttack: 4.84,
 BossCogNoAttack: 6,
 BossCogSlowDirectedAttack: 7.84,
 BossCogMoveAttack: 3,
 BossCogGolfAttack: 6,
 BossCogGolfAreaAttack: 7,
 BossCogGearDirectedAttack: 4.84,
 BossCogOvertimeAttack: 5}
BossCogDamageLevels = {BossCogElectricFence: 1,
 BossCogSwatLeft: 5,
 BossCogSwatRight: 5,
 BossCogAreaAttack: 10,
 BossCogFrontAttack: 3,
 BossCogRecoverDizzyAttack: 3,
 BossCogDirectedAttack: 3,
 BossCogStrafeAttack: 2,
 BossCogGoonZap: 5,
 BossCogSlowDirectedAttack: 10,
 BossCogGavelStomp: 20,
 BossCogGavelHandle: 2,
 BossCogLawyerAttack: 5,
 BossCogMoveAttack: 20,
 BossCogGolfAttack: 15,
 BossCogGolfAreaAttack: 15,
 BossCogGearDirectedAttack: 15,
 BossCogOvertimeAttack: 10}
BossCogBattleAPosHpr = (0,
 -25,
 0,
 0,
 0,
 0)
BossCogBattleBPosHpr = (0,
 25,
 0,
 180,
 0,
 0)
SellbotBossMaxDamage = 100
SellbotBossMaxDamageNerfed = 100
SellbotBossBattleOnePosHpr = (0,
 -35,
 0,
 -90,
 0,
 0)
SellbotBossBattleTwoPosHpr = (0,
 60,
 18,
 -90,
 0,
 0)
SellbotBossBattleThreeHpr = (180, 0, 0)
SellbotBossBottomPos = (0, -110, -6.5)
SellbotBossDeathPos = (0, -175, -6.5)
SellbotBossDooberTurnPosA = (-20, -50, 0)
SellbotBossDooberTurnPosB = (20, -50, 0)
SellbotBossDooberTurnPosDown = (0, -50, 0)
SellbotBossDooberFlyPos = (0, -135, -6.5)
SellbotBossTopRampPosA = (-80, -35, 18)
SellbotBossTopRampTurnPosA = (-80, 10, 18)
SellbotBossP3PosA = (-50, 40, 18)
SellbotBossTopRampPosB = (80, -35, 18)
SellbotBossTopRampTurnPosB = (80, 10, 18)
SellbotBossP3PosB = (50, 60, 18)
CashbotBossMaxDamage = 500
CashbotBossOffstagePosHpr = (120,
 -195,
 0,
 0,
 0,
 0)
CashbotBossBattleOnePosHpr = (120,
 -230,
 0,
 90,
 0,
 0)
CashbotRTBattleOneStartPosHpr = (94,
 -220,
 0,
 110,
 0,
 0)
CashbotBossBattleThreePosHpr = (120,
 -315,
 0,
 180,
 0,
 0)
CashbotToonsBattleThreeStartPosHpr = [(105,
  -285,
  0,
  208,
  0,
  0),
 (136,
  -342,
  0,
  398,
  0,
  0),
 (105,
  -342,
  0,
  333,
  0,
  0),
 (135,
  -292,
  0,
  146,
  0,
  0),
 (93,
  -303,
  0,
  242,
  0,
  0),
 (144,
  -327,
  0,
  64,
  0,
  0),
 (145,
  -302,
  0,
  117,
  0,
  0),
 (93,
  -327,
  0,
  -65,
  0,
  0)]
CashbotBossSafePosHprs = [(120,
  -315,
  30,
  0,
  0,
  0),
 (77.2,
  -329.3,
  0,
  -90,
  0,
  0),
 (77.1,
  -302.7,
  0,
  -90,
  0,
  0),
 (165.7,
  -326.4,
  0,
  90,
  0,
  0),
 (165.5,
  -302.4,
  0,
  90,
  0,
  0),
 (107.8,
  -359.1,
  0,
  0,
  0,
  0),
 (133.9,
  -359.1,
  0,
  0,
  0,
  0),
 (107.0,
  -274.7,
  0,
  180,
  0,
  0),
 (134.2,
  -274.7,
  0,
  180,
  0,
  0)]
CashbotBossCranePosHprs = [(97.4,
  -337.6,
  0,
  -45,
  0,
  0),
 (97.4,
  -292.4,
  0,
  -135,
  0,
  0),
 (142.6,
  -292.4,
  0,
  135,
  0,
  0),
 (142.6,
  -337.6,
  0,
  45,
  0,
  0)]
CashbotBossToMagnetTime = 0.2
CashbotBossFromMagnetTime = 1
CashbotBossSafeKnockImpact = 0.5
CashbotBossSafeNewImpact = 0.0
CashbotBossGoonImpact = 0.1
CashbotBossKnockoutDamage = 15
TTWakeWaterHeight = -4.79
DDWakeWaterHeight = 1.669
EstateWakeWaterHeight = -.3
OZWakeWaterHeight = -0.5
WakeRunDelta = 0.1
WakeWalkDelta = 0.2
NoItems = 0
NewItems = 1
OldItems = 2
SuitInvasionBegin = 0
SuitInvasionUpdate = 1
SuitInvasionEnd = 2
SuitInvasionBulletin = 3
NO_HOLIDAY = 0
JULY4_FIREWORKS = 1
NEWYEARS_FIREWORKS = 2
HALLOWEEN = 3
WINTER_DECORATIONS = 4
SKELECOG_INVASION = 5
MR_HOLLYWOOD_INVASION = 6
FISH_BINGO_NIGHT = 7
ELECTION_PROMOTION = 8
BLACK_CAT_DAY = 9
RESISTANCE_EVENT = 10
KART_RECORD_DAILY_RESET = 11
KART_RECORD_WEEKLY_RESET = 12
TRICK_OR_TREAT = 13
CIRCUIT_RACING = 14
POLAR_PLACE_EVENT = 15
CIRCUIT_RACING_EVENT = 16
TROLLEY_HOLIDAY = 17
TROLLEY_WEEKEND = 18
SILLY_SATURDAY_BINGO = 19
SILLY_SATURDAY_CIRCUIT = 20
SILLY_SATURDAY_TROLLEY = 21
ROAMING_TRIALER_WEEKEND = 22
BOSSCOG_INVASION = 23
MARCH_INVASION = 24
MORE_XP_HOLIDAY = 25
HALLOWEEN_PROPS = 26
HALLOWEEN_COSTUMES = 27
DECEMBER_INVASION = 28
APRIL_FOOLS_COSTUMES = 29
CRASHED_LEADERBOARD = 30
OCTOBER31_FIREWORKS = 31
NOVEMBER19_FIREWORKS = 32
SELLBOT_SURPRISE_1 = 33
SELLBOT_SURPRISE_2 = 34
SELLBOT_SURPRISE_3 = 35
SELLBOT_SURPRISE_4 = 36
CASHBOT_CONUNDRUM_1 = 37
CASHBOT_CONUNDRUM_2 = 38
CASHBOT_CONUNDRUM_3 = 39
CASHBOT_CONUNDRUM_4 = 40
LAWBOT_GAMBIT_1 = 41
LAWBOT_GAMBIT_2 = 42
LAWBOT_GAMBIT_3 = 43
LAWBOT_GAMBIT_4 = 44
TROUBLE_BOSSBOTS_1 = 45
TROUBLE_BOSSBOTS_2 = 46
TROUBLE_BOSSBOTS_3 = 47
TROUBLE_BOSSBOTS_4 = 48
JELLYBEAN_DAY = 49
FEBRUARY14_FIREWORKS = 51
JULY14_FIREWORKS = 52
JUNE22_FIREWORKS = 53
BIGWIG_INVASION = 54
COLD_CALLER_INVASION = 53
BEAN_COUNTER_INVASION = 54
DOUBLE_TALKER_INVASION = 55
DOWNSIZER_INVASION = 56
WINTER_CAROLING = 57
HYDRANT_ZERO_HOLIDAY = 58
VALENTINES_DAY = 59
SILLYMETER_HOLIDAY = 60
MAILBOX_ZERO_HOLIDAY = 61
TRASHCAN_ZERO_HOLIDAY = 62
SILLY_SURGE_HOLIDAY = 63
HYDRANTS_BUFF_BATTLES = 64
MAILBOXES_BUFF_BATTLES = 65
TRASHCANS_BUFF_BATTLES = 66
SILLY_CHATTER_ONE = 67
SILLY_CHATTER_TWO = 68
SILLY_CHATTER_THREE = 69
SILLY_CHATTER_FOUR = 70
SILLY_TEST = 71
YES_MAN_INVASION = 72
TIGHTWAD_INVASION = 73
TELEMARKETER_INVASION = 74
HEADHUNTER_INVASION = 75
SPINDOCTOR_INVASION = 76
MONEYBAGS_INVASION = 77
TWOFACES_INVASION = 78
MINGLER_INVASION = 79
LOANSHARK_INVASION = 80
CORPORATE_RAIDER_INVASION = 81
ROBBER_BARON_INVASION = 82
LEGAL_EAGLE_INVASION = 83
BIG_WIG_INVASION = 84
BIG_CHEESE_INVASION = 85
DOWN_SIZER_INVASION = 86
MOVER_AND_SHAKER_INVASION = 87
DOUBLETALKER_INVASION = 88
PENNY_PINCHER_INVASION = 89
NAME_DROPPER_INVASION = 90
AMBULANCE_CHASER_INVASION = 91
MICROMANAGER_INVASION = 92
NUMBER_CRUNCHER_INVASION = 93
SILLY_CHATTER_FIVE = 94
VICTORY_PARTY_HOLIDAY = 95
SELLBOT_NERF_HOLIDAY = 96
JELLYBEAN_TROLLEY_HOLIDAY = 97
JELLYBEAN_FISHING_HOLIDAY = 98
JELLYBEAN_PARTIES_HOLIDAY = 99
BANK_UPGRADE_HOLIDAY = 100
TOP_TOONS_MARATHON = 101
SELLBOT_INVASION = 102
SELLBOT_FIELD_OFFICE = 103
SELLBOT_INVASION_MOVER_AND_SHAKER = 104
IDES_OF_MARCH = 105
EXPANDED_CLOSETS = 106
TAX_DAY_INVASION = 107
KARTING_TICKETS_HOLIDAY = 109
PRE_JULY_4_DOWNSIZER_INVASION = 110
PRE_JULY_4_BIGWIG_INVASION = 111
COMBO_FIREWORKS = 112
JELLYBEAN_TROLLEY_HOLIDAY_MONTH = 113
JELLYBEAN_FISHING_HOLIDAY_MONTH = 114
JELLYBEAN_PARTIES_HOLIDAY_MONTH = 115
SILLYMETER_EXT_HOLIDAY = 116
SPOOKY_BLACK_CAT = 117
SPOOKY_TRICK_OR_TREAT = 118
SPOOKY_PROPS = 119
SPOOKY_COSTUMES = 120
WACKY_WINTER_DECORATIONS = 121
WACKY_WINTER_CAROLING = 122
TOT_REWARD_JELLYBEAN_AMOUNT = 100
TOT_REWARD_END_OFFSET_AMOUNT = 0
LawbotBossMaxDamage = 2700
LawbotBossWinningTilt = 40
LawbotBossInitialDamage = 1350
LawbotBossBattleOnePosHpr = (-2.798,
 -60,
 0,
 0,
 0,
 0)
LawbotBossBattleTwoPosHpr = (-2.798,
 89,
 19.145,
 0,
 0,
 0)
LawbotBossTopRampPosA = (-80, -35, 18)
LawbotBossTopRampTurnPosA = (-80, 10, 18)
LawbotBossP3PosA = (55, -9, 0)
LawbotBossTopRampPosB = (80, -35, 18)
LawbotBossTopRampTurnPosB = (80, 10, 18)
LawbotBossP3PosB = (55, -9, 0)
LawbotBossBattleThreePosHpr = LawbotBossBattleTwoPosHpr
LawbotBossBottomPos = (50, 39, 0)
LawbotBossDeathPos = (50, 40, 0)
LawbotBossGavelPosHprs = [(35,
  78.328,
  0,
  -135,
  0,
  0),
 (68.5,
  78.328,
  0,
  135,
  0,
  0),
 (47,
  -33,
  0,
  45,
  0,
  0),
 (-50,
  -39,
  0,
  -45,
  0,
  0),
 (-9,
  -37,
  0,
  0,
  0,
  0),
 (-9,
  49,
  0,
  -180,
  0,
  0),
 (32,
  0,
  0,
  45,
  0,
  0),
 (33,
  56,
  0,
  135,
  0,
  0)]
LawbotBossGavelTimes = [(0.2, 0.9, 0.6),
 (0.25, 1, 0.5),
 (1.0, 6, 0.5),
 (0.3, 3, 1),
 (0.26, 0.9, 0.45),
 (0.24, 1.1, 0.65),
 (0.27, 1.2, 0.45),
 (0.25, 0.95, 0.5)]
LawbotBossGavelHeadings = [(0,
  -15,
  4,
  -70 - 45,
  5,
  45),
 (0,
  -45,
  -4,
  -35,
  -45,
  -16,
  32),
 (0,
  -8,
  19,
  -7,
  5,
  23),
 (0,
  -4,
  8,
  -16,
  32,
  -45,
  7,
  7,
  -30,
  19,
  -13,
  25),
 (0,
  -45,
  -90,
  45,
  90),
 (0,
  -45,
  -90,
  45,
  90),
 (0, -45, 45),
 (0, -45, 45)]
LawbotBossCogRelBattleAPosHpr = (-25,
 -10,
 0,
 0,
 0,
 0)
LawbotBossCogRelBattleBPosHpr = (-25,
 10,
 0,
 0,
 0,
 0)
LawbotBossCogAbsBattleAPosHpr = (-5,
 -2,
 0,
 0,
 0,
 0)
LawbotBossCogAbsBattleBPosHpr = (-5,
 0,
 0,
 0,
 0,
 0)
LawbotBossWitnessStandPosHpr = (54,
 100,
 0,
 -90,
 0,
 0)
LawbotBossInjusticePosHpr = (-3,
 12,
 0,
 90,
 0,
 0)
LawbotBossInjusticeScale = (1.75, 1.75, 1.5)
LawbotBossDefensePanDamage = 1
LawbotBossLawyerPosHprs = [(-57,
  -24,
  0,
  -90,
  0,
  0),
 (-57,
  -12,
  0,
  -90,
  0,
  0),
 (-57,
  0,
  0,
  -90,
  0,
  0),
 (-57,
  12,
  0,
  -90,
  0,
  0),
 (-57,
  24,
  0,
  -90,
  0,
  0),
 (-57,
  36,
  0,
  -90,
  0,
  0),
 (-57,
  48,
  0,
  -90,
  0,
  0),
 (-57,
  60,
  0,
  -90,
  0,
  0),
 (-3,
  -37.3,
  0,
  0,
  0,
  0),
 (-3,
  53,
  0,
  -180,
  0,
  0)]
LawbotBossLawyerCycleTime = 6
LawbotBossLawyerToPanTime = 2.5
LawbotBossLawyerChanceToAttack = 50
LawbotBossLawyerHeal = 2
LawbotBossLawyerStunTime = 5
LawbotBossDifficultySettings = [(38,
  4,
  8,
  1,
  0,
  0),
 (36,
  5,
  8,
  1,
  0,
  0),
 (34,
  5,
  8,
  1,
  0,
  0),
 (32,
  6,
  8,
  2,
  0,
  0),
 (30,
  6,
  8,
  2,
  0,
  0),
 (28,
  7,
  8,
  3,
  0,
  0),
 (26,
  7,
  9,
  3,
  1,
  1),
 (24,
  8,
  9,
  4,
  1,
  1),
 (22,
  8,
  10,
  4,
  1,
  0)]
LawbotBossCannonPosHprs = [(-40,
  -12,
  0,
  -90,
  0,
  0),
 (-40,
  0,
  0,
  -90,
  0,
  0),
 (-40,
  12,
  0,
  -90,
  0,
  0),
 (-40,
  24,
  0,
  -90,
  0,
  0),
 (-40,
  36,
  0,
  -90,
  0,
  0),
 (-40,
  48,
  0,
  -90,
  0,
  0),
 (-40,
  60,
  0,
  -90,
  0,
  0),
 (-40,
  72,
  0,
  -90,
  0,
  0)]
LawbotBossCannonPosA = (-80, -51.48, 0)
LawbotBossCannonPosB = (-80, 70.73, 0)
LawbotBossChairPosHprs = [(60,
  72,
  0,
  -90,
  0,
  0),
 (60,
  62,
  0,
  -90,
  0,
  0),
 (60,
  52,
  0,
  -90,
  0,
  0),
 (60,
  42,
  0,
  -90,
  0,
  0),
 (60,
  32,
  0,
  -90,
  0,
  0),
 (60,
  22,
  0,
  -90,
  0,
  0),
 (70,
  72,
  5,
  -90,
  0,
  0),
 (70,
  62,
  5,
  -90,
  0,
  0),
 (70,
  52,
  5,
  -90,
  0,
  0),
 (70,
  42,
  5,
  -90,
  0,
  0),
 (70,
  32,
  5,
  -90,
  0,
  0),
 (70,
  22,
  5,
  -90,
  0,
  0)]
LawbotBossChairRow1PosB = (59.3, 48, 14.05)
LawbotBossChairRow1PosA = (59.3, -18.2, 14.05)
LawbotBossChairRow2PosB = (75.1, 48, 28.2)
LawbotBossChairRow2PosA = (75.1, -18.2, 28.2)
LawbotBossCannonBallMax = 12
LawbotBossJuryBoxStartPos = (94, -8, 5)
LawbotBossJuryBoxRelativeEndPos = (30, 0, 12.645)
LawbotBossJuryBoxMoveTime = 70
LawbotBossJurorsForBalancedScale = 8
LawbotBossDamagePerJuror = 68
LawbotBossCogJurorFlightTime = 10
LawbotBossCogJurorDistance = 75
LawbotBossBaseJurorNpcId = 2001
LawbotBossWitnessEpiloguePosHpr = (-3,
 0,
 0,
 180,
 0,
 0)
LawbotBossChanceForTaunt = 25
LawbotBossBonusWaitTime = 60
LawbotBossBonusDuration = 20
LawbotBossBonusToonup = 10
LawbotBossBonusWeightMultiplier = 2
LawbotBossChanceToDoAreaAttack = 11
LOW_POP_JP = 0
MID_POP_JP = 100
HIGH_POP_JP = 200
LOW_POP_INTL = 399
MID_POP_INTL = 499
HIGH_POP_INTL = -1
LOW_POP = 399
MID_POP = 599
HIGH_POP = -1
PinballCannonBumper = 0
PinballCloudBumperLow = 1
PinballCloudBumperMed = 2
PinballCloudBumperHigh = 3
PinballTarget = 4
PinballRoof = 5
PinballHouse = 6
PinballFence = 7
PinballBridge = 8
PinballStatuary = 9
PinballScoring = [(100, 1),
 (150, 1),
 (200, 1),
 (250, 1),
 (350, 1),
 (100, 1),
 (50, 1),
 (25, 1),
 (100, 1),
 (10, 1)]
PinballCannonBumperInitialPos = (0, -20, 40)
RentalCop = 0
RentalCannon = 1
RentalGameTable = 2
GlitchKillerZones = [13300,
 13400,
 13500,
 13600]
ColorPlayer = (0.3,
 0.7,
 0.3,
 1)
ColorAvatar = (0.3,
 0.3,
 0.7,
 1)
ColorPet = (0.6,
 0.4,
 0.2,
 1)
ColorFreeChat = (0.3,
 0.3,
 0.8,
 1)
ColorSpeedChat = (0.2,
 0.6,
 0.4,
 1)
ColorNoChat = (0.8,
 0.5,
 0.1,
 1)
FactoryLaffMinimums = [(0, 31),
 (0, 66, 71),
 (0,
  81,
  86,
  96),
 (0, 101, 106)]
PICNIC_COUNTDOWN_TIME = 60
BossbotRTIntroStartPosHpr = (0,
 -64,
 0,
 180,
 0,
 0)
BossbotRTPreTwoPosHpr = (0,
 -20,
 0,
 180,
 0,
 0)
BossbotRTEpiloguePosHpr = (0,
 90,
 0,
 180,
 0,
 0)
BossbotBossBattleOnePosHpr = (0,
 355,
 0,
 0,
 0,
 0)
BossbotBossPreTwoPosHpr = (0,
 20,
 0,
 0,
 0,
 0)
BossbotElevCamPosHpr = (0,
 -100.544,
 7.18258,
 0,
 0,
 0)
BossbotFoodModelScale = 0.75
BossbotNumFoodToExplode = 3
BossbotBossServingDuration = 300
BossbotPrepareBattleThreeDuration = 20
WaiterBattleAPosHpr = (20,
 -400,
 0,
 0,
 0,
 0)
WaiterBattleBPosHpr = (-20,
 -400,
 0,
 0,
 0,
 0)
BossbotBossBattleThreePosHpr = (0,
 355,
 0,
 0,
 0,
 0)
DinerBattleAPosHpr = (20,
 -240,
 0,
 0,
 0,
 0)
DinerBattleBPosHpr = (-20,
 -240,
 0,
 0,
 0,
 0)
BossbotBossMaxDamage = 500
BossbotMaxSpeedDamage = 90
BossbotSpeedRecoverRate = 20
BossbotBossDifficultySettings = [(8,
  4,
  11,
  3,
  30,
  25),
 (9,
  5,
  12,
  6,
  28,
  26),
 (10,
  6,
  11,
  7,
  26,
  27),
 (8,
  8,
  12,
  8,
  24,
  28),
 (13,
  5,
  12,
  9,
  22,
  29)]
BossbotRollSpeedMax = 22
BossbotRollSpeedMin = 7.5
BossbotTurnSpeedMax = 60
BossbotTurnSpeedMin = 20
BossbotTreadSpeedMax = 10.5
BossbotTreadSpeedMin = 3.5
CalendarFilterShowAll = 0
CalendarFilterShowOnlyHolidays = 1
CalendarFilterShowOnlyParties = 2
TTC = 1
DD = 2
MM = 3
GS = 4
DG = 5
BR = 6
OZ = 7
DL = 8
DefaultWantNewsPageSetting = 1
gmMagicWordList = ['restock',
 'restockUber',
 'autoRestock',
 'resistanceRestock',
 'restockSummons',
 'uberDrop',
 'rich',
 'maxBankMoney',
 'toonUp',
 'rod',
 'cogPageFull',
 'pinkSlips',
 'Tickets',
 'newSummons',
 'who',
 'who all']
NewsPageScaleAdjust = 0.85
AnimPropTypes = Enum(('Unknown',
 'Hydrant',
 'Mailbox',
 'Trashcan'), start=-1)
EmblemTypes = Enum(('Silver', 'Gold'))
NumEmblemTypes = 2
DefaultMaxBankMoney = 12000
DefaultBankItemId = 1350
ToonAnimStates = set(['off',
 'neutral',
 'victory',
 'Happy',
 'Sad',
 'Catching',
 'CatchEating',
 'Sleep',
 'walk',
 'jumpSquat',
 'jump',
 'jumpAirborne',
 'jumpLand',
 'run',
 'swim',
 'swimhold',
 'dive',
 'cringe',
 'OpenBook',
 'ReadBook',
 'CloseBook',
 'TeleportOut',
 'Died',
 'TeleportedOut',
 'TeleportIn',
 'Emote',
 'SitStart',
 'Sit',
 'Push',
 'Squish',
 'FallDown',
 'GolfPuttLoop',
 'GolfRotateLeft',
 'GolfRotateRight',
 'GolfPuttSwing',
 'GolfGoodPutt',
 'GolfBadPutt',
 'Flattened',
 'CogThiefRunning',
 'ScientistJealous',
 'ScientistEmcee',
 'ScientistWork',
 'ScientistLessWork',
 'ScientistPlay'])
AV_FLAG_REASON_TOUCH = 1
AV_FLAG_HISTORY_LEN = 500
AV_TOUCH_CHECK_DELAY_AI = 3.0
AV_TOUCH_CHECK_DELAY_CL = 1.0
AV_TOUCH_CHECK_DIST = 2.0
AV_TOUCH_CHECK_DIST_Z = 5.0
AV_TOUCH_CHECK_TIMELIMIT_CL = 0.002
AV_TOUCH_COUNT_LIMIT = 5
AV_TOUCH_COUNT_TIME = 300
