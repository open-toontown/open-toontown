TrackSignDuration = 15
RaceCountdown = 3
MaxRacers = 4
MaxTickets = 99999
Practice = 0
ToonBattle = 1
Circuit = 2
Speedway = 0
Rural = 1
Urban = 2
RT_Speedway_1 = 0
RT_Speedway_1_rev = 1
RT_Rural_1 = 20
RT_Rural_1_rev = 21
RT_Urban_1 = 40
RT_Urban_1_rev = 41
RT_Speedway_2 = 60
RT_Speedway_2_rev = 61
RT_Rural_2 = 62
RT_Rural_2_rev = 63
RT_Urban_2 = 64
RT_Urban_2_rev = 65
KARTING_TICKETS_HOLIDAY_MULTIPLIER = 2

def getTrackGenre(trackId):
    if trackId in (RT_Speedway_1,
     RT_Speedway_1_rev,
     RT_Speedway_2,
     RT_Speedway_2_rev):
        return Speedway
    elif trackId in (RT_Rural_1,
     RT_Rural_1_rev,
     RT_Rural_2,
     RT_Rural_2_rev):
        return Rural
    else:
        return Urban


RT_Speedway_1_Gags = ((923.052, -1177.431, 0.024),
 (926.099, -1187.345, 0.024),
 (925.68, -1197.327, 0.024),
 (925.169, -1209.502, 0.024),
 (394.009, 209.219, 0.025),
 (279.109, 279.744, 0.025),
 (204.366, 316.238, 0.025),
 (118.646, 358.009, 0.025),
 (-1462.098, 791.722, 0.025),
 (-1459.446, 730.064, 0.025),
 (-1450.731, 666.811, 0.025),
 (-1438.388, 615.1, 0.025))
RT_Speedway_2_Gags = ((-355.18, -2430.1, -0.126728),
 (-343.456, -2421.43, -0.0116951),
 (-329.644, -2411.06, -0.0169053),
 (-315.054, -2402.91, -0.0800667),
 (243.293, -906.412, 0.021832),
 (216.555, -910.885, -0.146125),
 (192.16, -915.93, -0.242366),
 (165.941, -922.381, -0.247588),
 (-840.626, 2405.96, 58.4195),
 (-868.154, 2370.54, 56.7396),
 (-896.126, 2332.55, 53.8607),
 (-921.952, 2291.16, 49.8209))
RT_Speedway_1_rev_Gags = ((1364.601, -664.452, 0.025),
 (1312.491, -588.218, 0.025),
 (1251.775, -509.556, 0.025),
 (1214.052, -461.743, 0.025),
 (-976.044, 995.072, 0.025),
 (-1043.917, 1018.78, 0.025),
 (-1124.555, 1038.362, 0.025),
 (-1187.95, 1047.006, 0.025),
 (-1174.542, -208.968, 0.025),
 (-1149.34, -270.698, 0.025),
 (-1121.2, -334.367, 0.025),
 (-1090.627, -392.662, 0.026))
RT_Rural_1_Gags = ((814.276, -552.928, 2.107),
 (847.738, -551.97, 2.106),
 (889.265, -549.569, 2.107),
 (922.022, -554.813, 2.106),
 (1791.42, 2523.91, 2.106),
 (1754.14, 2540.25, 2.107),
 (1689.66, 2557.28, 2.107),
 (1614.01, 2577.16, 2.106),
 (-1839.0, 654.477, 86.83),
 (-1894.33, 640.125, 80.39),
 (-1955.3, 625.09, 73.07),
 (-2016.99, 611.746, 65.86))
RT_Rural_2_Gags = ((2001.53, 560.532, 198.912),
 (2002.45, 574.292, 198.912),
 (2003.42, 588.612, 198.912),
 (2004, 602.849, 198.912),
 (-2107.4, 2209.67, 198.913),
 (-2086.13, 2224.31, 198.913),
 (-2058.11, 2244.31, 198.912),
 (-2023.85, 2268.77, 198.912),
 (-331.746, -1010.57, 222.332),
 (-358.595, -1007.68, 225.129),
 (-388.556, -1004.87, 228.239),
 (-410.122, -1003.03, 230.482),
 (69.763, -2324.5, 198.912),
 (63.5314, -2334.02, 198.913),
 (57.9662, -2349.14, 198.913),
 (51.8838, -2363.87, 198.913))
RT_Urban_1_Gags = ((51.9952, 2431.62, 55.7053),
 (39.5407, 2421.64, 65.7053),
 (27.7504, 2411.67, 55.7053),
 (15.55, 2401.65, 65.7053),
 (-1008.36, 2116.41, 0.0246798),
 (-1050.31, 2099.78, 0.025),
 (-1092.26, 2083.15, 0.0253202),
 (-1134.21, 2066.52, 0.0256404),
 (-1966.68, 1139.32, 1.76981),
 (-1970.46, 1120.57, 1.76981),
 (-1974.18, 1101.82, 1.76981),
 (-1977.93, 1084.07, 1.76981),
 (1419.05, -2987.18, 0.025),
 (1411.09, -3004.09, 0.025),
 (1403.13, -3021.01, 0.025),
 (1395.17, -3037.92, 0.025),
 (948.131, -1216.77, 0.025),
 (935.545, -1204.09, 0.025),
 (922.959, -1191.41, 0.025),
 (909.959, -1177.41, 0.025))
RT_Urban_2_Gags = ((-2761.49, -3070.97, -0.255122),
 (-2730.18, -3084.09, -0.255153),
 (-2701.45, -3096.26, -0.255669),
 (-2669.81, -3108.9, -0.255252),
 (735.479, -423.828, 23.7334),
 (759.026, -427.198, 23.0068),
 (783.232, -430.659, 22.2569),
 (809.914, -434.476, 21.4326),
 (3100.09, 240.411, 23.4672),
 (3089.09, 242.019, 23.5251),
 (3077.68, 243.688, 23.6857),
 (3064.82, 245.567, 23.8771),
 (-10.7389, 2980.48, -0.255609),
 (-41.2644, 2974.53, -0.255122),
 (-69.8423, 2989.98, -0.255682),
 (-102.331, 2986.1, -0.255637),
 (-1978.67, 588.981, -0.255685),
 (-1977.07, 560.797, -0.255415),
 (-1948.58, 544.782, -0.255122),
 (-1943.42, 510.262, -0.255866))
RT_Urban_1_rev_Gags = ((1034.43, -366.371, 0.025),
 (1051.84, -360.473, 0.025),
 (1069.25, -354.575, 0.025),
 (1086.66, -348.677, 0.025),
 (1849.66, -2807.21, 0.0246158),
 (1858.55, -2795.99, 0.0246158),
 (1867.44, -2784.76, 0.0246158),
 (1876.33, -2773.53, 0.0246158),
 (316.342, -44.9529, 0.025),
 (305.173, -63.4405, 0.025),
 (294.004, -81.9281, 0.025),
 (282.835, -100.416, 0.025),
 (-762.377, 2979.25, 0.025),
 (-753.029, 2995.69, 0.025),
 (-743.681, 3012.14, 0.025),
 (-734.333, 3028.58, 0.025),
 (470.628, 1828.32, 55.0),
 (481.284, 1836.89, 55.0),
 (491.941, 1845.47, 55.0),
 (502.597, 1854.04, 55.0))
Speedway_1_Boosts = (((-320, 685, 1), (415, 0, 0)),)
Speedway_1_Rev_Boosts = (((-320, 685, 0.1), (235, 0, 0)),)
Speedway_2_Boosts = (((-120, 430, 1.0), (-50, 0, 0)),)
Speedway_2_Rev_Boosts = (((176, 625, 1.0), (130, 0, 0)),)
Rural_1_Boosts = (((3132.64, 859.56, 5.0), (384.44, 363.5, 0)), ((-3050.33, -1804.97, 207.7), (229.4, 353.25, 342.9)))
Rural_1_Rev_Boosts = (((3132.64, 859.56, 5.0), (197.1, -2.25, 0)), ((-3151.34, -1569.56, 200.621), (189.46, 182.75, 195.255)))
Rural_2_Boosts = (((873.255, -593.664, 199.5), (87.715, 0, 0)), ((-1747.62, 801.56, 199.5), (-126.516, 0, 0)))
Rural_2_Rev_Boosts = (((-428.004, -243.692, 324.516), (51.428, 6, 1)), ((-384.043, 211.62, 193.5), (-127.859, 1, 0)))
Urban_1_Boosts = (((677.057, 1618.24, 0.025), (35.9995, 0, 0)), ((-2250.35, 1618.1, 0.0241526), (-154.8, 0, 0)), ((400.13, -1090.26, 0.025), (-175.204, 0, 0)))
Urban_1_Rev_Boosts = (((488.739, -2055.07, 0.025), (3.59753, 0, 0)), ((-1737.29, 588.138, 0.025), (26.3975, 0, 0)), ((-212.314, 2638.34, 0.025), (-128.404, 0, 0)))
Urban_2_Boosts = (((358.134, -1655.42, 0.3), (-4.95, 1, 0)), ((2058.77, 2560.03, 0.3), (77.31, 0, 0)), ((-3081.33, -1037.55, 0.25), (177.359, 0, 0)))
Urban_2_Rev_Boosts = (((-2007.38, 484.878, 0.25), (30.9102, 0, 0)), ((2646.51, 1455.15, 0.25), (-120.172, 0, 0)), ((-472.215, -2048.21, 0.25), (136.192, 0, 0)))

def RaceInfo2RacePadId(trackId, trackType):
    rev = trackId % 2
    if not rev:
        if trackType == Practice:
            padId = 0
        else:
            padId = 2
    elif trackType == Practice:
        padId = 1
    else:
        padId = 3
    return padId


def getTrackGenreString(genreId):
    genreStrings = ['Speedway', 'Country', 'City']
    return genreStrings[genreId].lower()


def getTunnelSignName(genreId, padId):
    if genreId == 2 and padId == 0:
        return 'tunne1l_citysign'
    elif genreId == 1 and padId == 0:
        return 'tunnel_countrysign1'
    else:
        return 'tunnel%s_%ssign' % (padId + 1, getTrackGenreString(genreId))


RacePadId2RaceInfo = {0: (0, Practice, 3),
 1: (1, Practice, 3),
 2: (0, ToonBattle, 3),
 3: (1, ToonBattle, 3)}

def getGenreFromString(string):
    if string == 'town':
        return Urban
    elif string == 'stadium':
        return Speedway
    else:
        return Rural


def getTrackListByType(genre, type):
    return Rural


def getTrackListByType(genre, type):
    genreDict = {Urban: [[RT_Urban_1, RT_Urban_2], [RT_Urban_1_rev, RT_Urban_2_rev]],
     Rural: [[RT_Rural_1, RT_Rural_2], [RT_Rural_1_rev, RT_Rural_2_rev]],
     Speedway: [[RT_Speedway_1, RT_Speedway_2], [RT_Speedway_1_rev, RT_Speedway_2_rev]]}
    trackIdList = genreDict.get(genre)
    return trackIdList[type]


def getCanonicalPadId(padId):
    return padId % 4


def getNextRaceInfo(prevTrackId, genreString, padId):
    genre = getGenreFromString(genreString)
    cPadId = getCanonicalPadId(padId)
    raceInfo = RacePadId2RaceInfo.get(cPadId)
    trackList = getTrackListByType(genre, raceInfo[0])
    if trackList.count(prevTrackId) == 0:
        trackId = trackList[1]
    else:
        index = trackList.index(prevTrackId)
        index += 1
        index %= len(trackList)
        trackId = trackList[index]
    return (trackId, raceInfo[1], raceInfo[2])


TrackPath = 'phase_6/models/karting/'
TrackDict = {RT_Speedway_1: (TrackPath + 'RT_SpeedwayA',
                 240.0,
                 115.0,
                 (50, 500),
                 RT_Speedway_1_Gags,
                 Speedway_1_Boosts,
                 1.0,
                 'GS_Race_SS.ogg',
                 (0.01, 0.015)),
 RT_Speedway_1_rev: (TrackPath + 'RT_SpeedwayA',
                     240.0,
                     115.0,
                     (50, 500),
                     RT_Speedway_1_rev_Gags,
                     Speedway_1_Rev_Boosts,
                     1.0,
                     'GS_Race_SS.ogg',
                     (0.01, 0.015)),
 RT_Speedway_2: (TrackPath + 'RT_SpeedwayB',
                 335.0,
                 210.0,
                 (75, 1000),
                 RT_Speedway_2_Gags,
                 Speedway_2_Boosts,
                 1.0,
                 'GS_Race_SS.ogg',
                 (0.01, 0.015)),
 RT_Speedway_2_rev: (TrackPath + 'RT_SpeedwayB',
                     335.0,
                     210.0,
                     (75, 1000),
                     RT_Speedway_2_Gags,
                     Speedway_2_Rev_Boosts,
                     1.0,
                     'GS_Race_SS.ogg',
                     (0.01, 0.015)),
 RT_Rural_1: (TrackPath + 'RT_RuralB',
              360.0,
              230.0,
              (100, 500),
              RT_Rural_1_Gags,
              Rural_1_Boosts,
              0.75,
              'GS_Race_RR.ogg',
              (0.003, 0.004)),
 RT_Rural_1_rev: (TrackPath + 'RT_RuralB',
                  360.0,
                  230.0,
                  (100, 500),
                  RT_Rural_1_Gags,
                  Rural_1_Rev_Boosts,
                  0.75,
                  'GS_Race_RR.ogg',
                  (0.003, 0.004)),
 RT_Rural_2: (TrackPath + 'RT_RuralB2',
              480.0,
              360.0,
              (150, 1000),
              RT_Rural_2_Gags,
              Rural_2_Boosts,
              0.75,
              'GS_Race_RR.ogg',
              (0.003, 0.004)),
 RT_Rural_2_rev: (TrackPath + 'RT_RuralB2',
                  480.0,
                  360.0,
                  (150, 1000),
                  RT_Rural_2_Gags,
                  Rural_2_Rev_Boosts,
                  0.75,
                  'GS_Race_RR.ogg',
                  (0.003, 0.004)),
 RT_Urban_1: (TrackPath + 'RT_UrbanA',
              480.0,
              305.0,
              (300, 500),
              RT_Urban_1_Gags,
              Urban_1_Boosts,
              1.0,
              'GS_Race_CC.ogg',
              (0.002, 0.003)),
 RT_Urban_1_rev: (TrackPath + 'RT_UrbanA',
                  480.0,
                  305.0,
                  (300, 500),
                  RT_Urban_1_rev_Gags,
                  Urban_1_Rev_Boosts,
                  1.0,
                  'GS_Race_CC.ogg',
                  (0.002, 0.003)),
 RT_Urban_2: (TrackPath + 'RT_UrbanB',
              480.0,
              280.0,
              (400, 1000),
              RT_Urban_2_Gags,
              Urban_2_Boosts,
              1.0,
              'GS_Race_CC.ogg',
              (0.002, 0.003)),
 RT_Urban_2_rev: (TrackPath + 'RT_UrbanB',
                  480.0,
                  280.0,
                  (400, 1000),
                  RT_Urban_2_Gags,
                  Urban_2_Rev_Boosts,
                  1.0,
                  'GS_Race_CC.ogg',
                  (0.002, 0.003))}
TrackIds = list(TrackDict.keys())
TrackIds.sort()

def getEntryFee(trackId, raceType):
    fee = 0
    if raceType == ToonBattle:
        fee = TrackDict[trackId][3][0]
    elif raceType == Circuit:
        fee = TrackDict[trackId][3][1]
    return fee


def getQualifyingTime(trackId):
    return TrackDict[trackId][1]


def getDefaultRecordTime(trackId):
    return TrackDict[trackId][2]


def getDefaultRecord(trackId):
    return getDefaultRecordTime(trackId), 0, 1, 'Goofy'


Daily = 0
Weekly = 1
AllTime = 2
PeriodDict = {Daily: 10,
 Weekly: 100,
 AllTime: 1000}
PeriodIds = list(PeriodDict.keys())
NumRecordPeriods = len(PeriodIds)
NumRecordsPerPeriod = 10
Winnings = [3.0,
 1.0,
 0.5,
 0.15]
PracticeWinnings = 20
SpeedwayQuals = 0
RuralQuals = 1
UrbanQuals = 2
SpeedwayWins = 3
RuralWins = 4
UrbanWins = 5
CircuitWins = 6
TwoPlayerWins = 7
ThreePlayerWins = 8
FourPlayerWins = 9
CircuitSweeps = 10
CircuitQuals = 11
QualsList = [SpeedwayQuals, RuralQuals, UrbanQuals]
WinsList = [SpeedwayWins, RuralWins, UrbanWins]
SpeedwayQuals1 = 0
SpeedwayQuals2 = 1
SpeedwayQuals3 = 2
RuralQuals1 = 3
RuralQuals2 = 4
RuralQuals3 = 5
UrbanQuals1 = 6
UrbanQuals2 = 7
UrbanQuals3 = 8
TotalQuals = 9
SpeedwayWins1 = 10
SpeedwayWins2 = 11
SpeedwayWins3 = 12
RuralWins1 = 13
RuralWins2 = 14
RuralWins3 = 15
UrbanWins1 = 16
UrbanWins2 = 17
UrbanWins3 = 18
TotalWins = 19
CircuitQuals1 = 20
CircuitQuals2 = 21
CircuitQuals3 = 22
CircuitWins1 = 23
CircuitWins2 = 24
CircuitWins3 = 25
CircuitSweeps1 = 26
CircuitSweeps2 = 27
CircuitSweeps3 = 28
GrandTouring = 29
NumTrophies = 30
TenTrophyCup = 30
TwentyTrophyCup = 31
ThirtyTrophyCup = 32
TrophyCups = [TenTrophyCup, TwentyTrophyCup, ThirtyTrophyCup]
NumCups = 3
SpeedwayQualsList = [SpeedwayQuals1, SpeedwayQuals2, SpeedwayQuals3]
RuralQualsList = [RuralQuals1, RuralQuals2, RuralQuals3]
UrbanQualsList = [UrbanQuals1, UrbanQuals2, UrbanQuals3]
SpeedwayWinsList = [SpeedwayWins1, SpeedwayWins2, SpeedwayWins3]
RuralWinsList = [RuralWins1, RuralWins2, RuralWins3]
UrbanWinsList = [UrbanWins1, UrbanWins2, UrbanWins3]
CircuitWinsList = [CircuitWins1, CircuitWins2, CircuitWins3]
CircuitSweepsList = [CircuitSweeps1, CircuitSweeps2, CircuitSweeps3]
CircuitQualList = [CircuitQuals1, CircuitQuals2, CircuitQuals3]
AllQualsList = [SpeedwayQualsList, RuralQualsList, UrbanQualsList]
AllWinsList = [SpeedwayWinsList, RuralWinsList, UrbanWinsList]
TrophiesPerCup = NumTrophies // NumCups
QualifiedRaces = [1, 10, 100]
TotalQualifiedRaces = 100
WonRaces = [1, 10, 100]
TotalWonRaces = 100
WonCircuitRaces = [1, 5, 25]
SweptCircuitRaces = [1, 5, 25]
QualifiedCircuitRaces = [1, 5, 25]
LBSubscription = {'stadium': [(RT_Speedway_1, Daily),
             (RT_Speedway_1, Weekly),
             (RT_Speedway_1, AllTime),
             (RT_Speedway_1_rev, Daily),
             (RT_Speedway_1_rev, Weekly),
             (RT_Speedway_1_rev, AllTime),
             (RT_Speedway_2, Daily),
             (RT_Speedway_2, Weekly),
             (RT_Speedway_2, AllTime),
             (RT_Speedway_2_rev, Daily),
             (RT_Speedway_2_rev, Weekly),
             (RT_Speedway_2_rev, AllTime)],
 'country': [(RT_Rural_1, Daily),
             (RT_Rural_1, Weekly),
             (RT_Rural_1, AllTime),
             (RT_Rural_1_rev, Daily),
             (RT_Rural_1_rev, Weekly),
             (RT_Rural_1_rev, AllTime),
             (RT_Rural_2, Daily),
             (RT_Rural_2, Weekly),
             (RT_Rural_2, AllTime),
             (RT_Rural_2_rev, Daily),
             (RT_Rural_2_rev, Weekly),
             (RT_Rural_2_rev, AllTime)],
 'city': [(RT_Urban_1, Daily),
          (RT_Urban_1, Weekly),
          (RT_Urban_1, AllTime),
          (RT_Urban_1_rev, Daily),
          (RT_Urban_1_rev, Weekly),
          (RT_Urban_1_rev, AllTime),
          (RT_Urban_2, Daily),
          (RT_Urban_2, Weekly),
          (RT_Urban_2, AllTime),
          (RT_Urban_2_rev, Daily),
          (RT_Urban_2_rev, Weekly),
          (RT_Urban_2_rev, AllTime)]}
BANANA = 1
TURBO = 2
ANVIL = 3
PIE = 4
GagFreq = [[PIE,
  BANANA,
  BANANA,
  BANANA,
  TURBO,
  PIE],
 [PIE,
  BANANA,
  BANANA,
  TURBO,
  ANVIL,
  PIE],
 [PIE,
  BANANA,
  TURBO,
  TURBO,
  ANVIL,
  PIE],
 [BANANA,
  TURBO,
  TURBO,
  TURBO,
  ANVIL,
  PIE]]
CircuitLoops = [[RT_Speedway_1, RT_Rural_1, RT_Urban_1],
 [RT_Speedway_1_rev, RT_Rural_1_rev, RT_Urban_1_rev],
 [RT_Speedway_2, RT_Rural_2, RT_Urban_2],
 [RT_Speedway_2_rev, RT_Rural_2_rev, RT_Urban_2_rev]]
CircuitPoints = [10,
 8,
 6,
 4]

def getCircuitLoop(startingTrack):
    circuitLoop = [startingTrack]
    for loop in CircuitLoops:
        if startingTrack in loop:
            print(loop)
            numTracks = len(loop)
            tempLoop = loop * 2
            startingIndex = tempLoop.index(startingTrack)
            circuitLoop = tempLoop[startingIndex:startingIndex + numTracks]
            break

    return circuitLoop


Exit_UserReq = 0
Exit_Barrier = 1
Exit_Slow = 2
Exit_BarrierNoRefund = 3
