from direct.directnotify import DirectNotifyGlobal
import random
MAX_PLAYERS_PER_HOLE = 4
GOLF_BALL_RADIUS = 0.25
GOLF_BALL_VOLUME = 4.0 / 3.0 * 3.14159 * GOLF_BALL_RADIUS ** 3
GOLF_BALL_MASS = 0.5
GOLF_BALL_DENSITY = GOLF_BALL_MASS / GOLF_BALL_VOLUME
GRASS_SURFACE = 0
BALL_SURFACE = 1
HARD_SURFACE = 2
HOLE_SURFACE = 3
SLICK_SURFACE = 4
OOB_RAY_COLLIDE_ID = -1
GRASS_COLLIDE_ID = 2
HARD_COLLIDE_ID = 3
TOON_RAY_COLLIDE_ID = 4
MOVER_COLLIDE_ID = 7
WINDMILL_BASE_COLLIDE_ID = 8
CAMERA_RAY_COLLIDE_ID = 10
BALL_COLLIDE_ID = 42
HOLE_CUP_COLLIDE_ID = 64
SKY_RAY_COLLIDE_ID = 78
SLICK_COLLIDE_ID = 13
BALL_CONTACT_FRAME = 9
BALL_CONTACT_TIME = (BALL_CONTACT_FRAME + 1) / 24.0
AIM_DURATION = 60
TEE_DURATION = 15
RANDOM_HOLES = True
KICKOUT_SWINGS = 2
TIME_TIE_BREAKER = True
CourseInfo = {0: {'name': '',
     'numHoles': 3,
     'holeIds': (2,
                 3,
                 4,
                 5,
                 6,
                 7,
                 8,
                 12,
                 13,
                 15,
                 16)},
 1: {'name': '',
     'numHoles': 6,
     'holeIds': ((0, 5),
                 (1, 5),
                 2,
                 3,
                 4,
                 5,
                 6,
                 7,
                 8,
                 9,
                 10,
                 (11, 5),
                 12,
                 13,
                 (14, 5),
                 15,
                 16,
                 (17, 5),
                 (20, 5),
                 (21, 5),
                 (22, 5),
                 (23, 5),
                 (24, 5),
                 (25, 5),
                 (26, 5),
                 (28, 5),
                 (30, 5),
                 (31, 5),
                 (33, 5),
                 (34, 5))},
 2: {'name': '',
     'numHoles': 9,
     'holeIds': ((1, 5),
                 4,
                 5,
                 6,
                 7,
                 8,
                 9,
                 10,
                 11,
                 12,
                 13,
                 (14, 5),
                 15,
                 (17, 5),
                 (18, 20),
                 (19, 20),
                 (20, 20),
                 (21, 5),
                 (22, 5),
                 (23, 20),
                 (24, 20),
                 (25, 20),
                 (26, 20),
                 (27, 20),
                 (28, 20),
                 (29, 20),
                 (30, 5),
                 (31, 20),
                 (32, 20),
                 (33, 5),
                 (34, 20),
                 (35, 20))}}
HoleInfo = {0: {'name': '',
     'par': 3,
     'maxSwing': 6,
     'terrainModel': 'phase_6/models/golf/hole18.bam',
     'physicsData': 'golfGreen18',
     'blockers': (),
     'optionalMovers': ()},
 1: {'name': '',
     'par': 3,
     'maxSwing': 6,
     'terrainModel': 'phase_6/models/golf/hole1.bam',
     'physicsData': 'golfGreen1',
     'blockers': ()},
 2: {'name': '',
     'par': 3,
     'maxSwing': 6,
     'terrainModel': 'phase_6/models/golf/hole2.bam',
     'physicsData': 'golfGreen2',
     'blockers': ()},
 3: {'name': '',
     'par': 2,
     'maxSwing': 6,
     'terrainModel': 'phase_6/models/golf/hole3.bam',
     'physicsData': 'golfGreen3',
     'blockers': ()},
 4: {'name': '',
     'par': 3,
     'maxSwing': 6,
     'terrainModel': 'phase_6/models/golf/hole4.bam',
     'physicsData': 'golfGreen4',
     'blockers': ()},
 5: {'name': '',
     'par': 3,
     'maxSwing': 6,
     'terrainModel': 'phase_6/models/golf/hole5.bam',
     'physicsData': 'golfGreen2',
     'blockers': ()},
 6: {'name': '',
     'par': 3,
     'maxSwing': 6,
     'terrainModel': 'phase_6/models/golf/hole6.bam',
     'physicsData': 'golfGreen6',
     'blockers': ()},
 7: {'name': '',
     'par': 3,
     'maxSwing': 6,
     'terrainModel': 'phase_6/models/golf/hole7.bam',
     'physicsData': 'golfGreen7',
     'blockers': ()},
 8: {'name': '',
     'par': 3,
     'maxSwing': 6,
     'terrainModel': 'phase_6/models/golf/hole8.bam',
     'physicsData': 'golfGreen8',
     'blockers': ()},
 9: {'name': '',
     'par': 3,
     'maxSwing': 6,
     'terrainModel': 'phase_6/models/golf/hole9.bam',
     'physicsData': 'golfGreen9',
     'blockers': 2},
 10: {'name': '',
      'par': 3,
      'maxSwing': 6,
      'terrainModel': 'phase_6/models/golf/hole10.bam',
      'physicsData': 'golfGreen10',
      'blockers': ()},
 11: {'name': '',
      'par': 3,
      'maxSwing': 6,
      'terrainModel': 'phase_6/models/golf/hole11.bam',
      'physicsData': 'golfGreen11',
      'blockers': ()},
 12: {'name': '',
      'par': 3,
      'maxSwing': 6,
      'terrainModel': 'phase_6/models/golf/hole12.bam',
      'physicsData': 'golfGreen12',
      'blockers': ()},
 13: {'name': '',
      'par': 3,
      'maxSwing': 6,
      'terrainModel': 'phase_6/models/golf/hole13.bam',
      'physicsData': 'golfGreen13',
      'blockers': ()},
 14: {'name': '',
      'par': 3,
      'maxSwing': 6,
      'terrainModel': 'phase_6/models/golf/hole14.bam',
      'physicsData': 'golfGreen14',
      'blockers': ()},
 15: {'name': '',
      'par': 3,
      'maxSwing': 6,
      'terrainModel': 'phase_6/models/golf/hole15.bam',
      'physicsData': 'golfGreen15',
      'blockers': ()},
 16: {'name': '',
      'par': 3,
      'maxSwing': 6,
      'terrainModel': 'phase_6/models/golf/hole16.bam',
      'physicsData': 'golfGreen16',
      'blockers': ()},
 17: {'name': '',
      'par': 3,
      'maxSwing': 6,
      'terrainModel': 'phase_6/models/golf/hole17.bam',
      'physicsData': 'golfGreen17',
      'blockers': ()},
 18: {'name': '',
      'par': 3,
      'maxSwing': 6,
      'terrainModel': 'phase_6/models/golf/hole18.bam',
      'physicsData': 'golfGreen18',
      'blockers': (1, 2),
      'optionalMovers': 1},
 19: {'name': '',
      'par': 3,
      'maxSwing': 6,
      'terrainModel': 'phase_6/models/golf/hole1.bam',
      'physicsData': 'golfGreen1',
      'blockers': (2, 5)},
 20: {'name': '',
      'par': 3,
      'maxSwing': 6,
      'terrainModel': 'phase_6/models/golf/hole2.bam',
      'physicsData': 'golfGreen2',
      'blockers': (1, 3)},
 21: {'name': '',
      'par': 3,
      'maxSwing': 6,
      'terrainModel': 'phase_6/models/golf/hole3.bam',
      'physicsData': 'golfGreen3',
      'blockers': (1, 2, 3)},
 22: {'name': '',
      'par': 3,
      'maxSwing': 6,
      'terrainModel': 'phase_6/models/golf/hole4.bam',
      'physicsData': 'golfGreen4',
      'blockers': 2},
 23: {'name': '',
      'par': 3,
      'maxSwing': 6,
      'terrainModel': 'phase_6/models/golf/hole5.bam',
      'physicsData': 'golfGreen5',
      'blockers': (3, 4),
      'optionalMovers': 1},
 24: {'name': '',
      'par': 3,
      'maxSwing': 6,
      'terrainModel': 'phase_6/models/golf/hole6.bam',
      'physicsData': 'golfGreen6',
      'blockers': 1,
      'optionalMovers': 1},
 25: {'name': '',
      'par': 3,
      'maxSwing': 6,
      'terrainModel': 'phase_6/models/golf/hole7.bam',
      'physicsData': 'golfGreen7',
      'blockers': 3,
      'optionalMovers': 1},
 26: {'name': '',
      'par': 3,
      'maxSwing': 6,
      'terrainModel': 'phase_6/models/golf/hole8.bam',
      'physicsData': 'golfGreen8',
      'blockers': (),
      'optionalMovers': 1},
 27: {'name': '',
      'par': 3,
      'maxSwing': 6,
      'terrainModel': 'phase_6/models/golf/hole9.bam',
      'physicsData': 'golfGreen9',
      'blockers': (),
      'optionalMovers': (1, 2)},
 28: {'name': '',
      'par': 3,
      'maxSwing': 6,
      'terrainModel': 'phase_6/models/golf/hole10.bam',
      'physicsData': 'golfGreen10',
      'blockers': (),
      'optionalMovers': (1, 2)},
 29: {'name': '',
      'par': 3,
      'maxSwing': 6,
      'terrainModel': 'phase_6/models/golf/hole11.bam',
      'physicsData': 'golfGreen11',
      'blockers': (),
      'optionalMovers': 1},
 30: {'name': '',
      'par': 3,
      'maxSwing': 6,
      'terrainModel': 'phase_6/models/golf/hole12.bam',
      'physicsData': 'golfGreen12',
      'blockers': (1, 2, 3)},
 31: {'name': '',
      'par': 4,
      'maxSwing': 7,
      'terrainModel': 'phase_6/models/golf/hole13.bam',
      'physicsData': 'golfGreen13',
      'blockers': (3, 4),
      'optionalMovers': 1},
 32: {'name': '',
      'par': 3,
      'maxSwing': 6,
      'terrainModel': 'phase_6/models/golf/hole14.bam',
      'physicsData': 'golfGreen14',
      'blockers': 1,
      'optionalMovers': 1},
 33: {'name': '',
      'par': 3,
      'maxSwing': 6,
      'terrainModel': 'phase_6/models/golf/hole15.bam',
      'physicsData': 'golfGreen15',
      'blockers': (1, 2, 3),
      'optionalMovers': (1, 2)},
 34: {'name': '',
      'par': 3,
      'maxSwing': 6,
      'terrainModel': 'phase_6/models/golf/hole16.bam',
      'physicsData': 'golfGreen16',
      'blockers': (1,
                   2,
                   5,
                   6),
      'optionalMovers': 1},
 35: {'name': '',
      'par': 4,
      'maxSwing': 7,
      'terrainModel': 'phase_6/models/golf/hole17.bam',
      'physicsData': 'golfGreen17',
      'blockers': (3, 4, 5)}}
for holeId in HoleInfo:
    if type(HoleInfo[holeId]['blockers']) == type(0):
        blockerNum = HoleInfo[holeId]['blockers']
        HoleInfo[holeId]['blockers'] = (blockerNum,)
    if HoleInfo[holeId].has_key('optionalMovers'):
        if type(HoleInfo[holeId]['optionalMovers']) == type(0):
            blockerNum = HoleInfo[holeId]['optionalMovers']
            HoleInfo[holeId]['optionalMovers'] = (blockerNum,)

DistanceToBeInHole = 0.75
CoursesCompleted = 0
CoursesUnderPar = 1
HoleInOneShots = 2
EagleOrBetterShots = 3
BirdieOrBetterShots = 4
ParOrBetterShots = 5
MultiPlayerCoursesCompleted = 6
CourseZeroWins = 7
CourseOneWins = 8
CourseTwoWins = 9
TwoPlayerWins = 10
ThreePlayerWins = 11
FourPlayerWins = 12
MaxHistoryIndex = 9
NumHistory = MaxHistoryIndex + 1
CalcOtherHoleBest = False
CalcOtherCourseBest = False
TrophyRequirements = {CoursesCompleted: (4, 40, 400),
 CoursesUnderPar: (1, 10, 100),
 HoleInOneShots: (1, 10, 100),
 EagleOrBetterShots: (2, 20, 200),
 BirdieOrBetterShots: (3, 30, 300),
 ParOrBetterShots: (4, 40, 400),
 MultiPlayerCoursesCompleted: (6, 60, 600),
 CourseZeroWins: (1, 10, 100),
 CourseOneWins: (1, 10, 100),
 CourseTwoWins: (1, 10, 100)}
PlayerColors = [(0.925,
  0.168,
  0.168,
  1),
 (0.13,
  0.59,
  0.973,
  1),
 (0.973,
  0.809,
  0.129,
  1),
 (0.598,
  0.402,
  0.875,
  1)]
KartColors = [[[0, 50], [90, 255], [0, 85]], [[160, 255], [-15, 15], [0, 120]], [[160, 255], [0, 110], [0, 110]]]
NumTrophies = 0
for key in TrophyRequirements:
    NumTrophies += len(TrophyRequirements[key])

NumCups = 3
TrophiesPerCup = NumTrophies / NumCups

def calcTrophyListFromHistory(history):
    retval = []
    historyIndex = 0
    for trophyIndex in xrange(NumHistory):
        requirements = TrophyRequirements[trophyIndex]
        for amountNeeded in requirements:
            if history[historyIndex] >= amountNeeded:
                retval.append(True)
            else:
                retval.append(False)

        historyIndex += 1

    return retval


def calcCupListFromHistory(history):
    retval = [False] * NumCups
    trophyList = calcTrophyListFromHistory(history)
    numTrophiesWon = 0
    for gotTrophy in trophyList:
        if gotTrophy:
            numTrophiesWon += 1

    for cupIndex in xrange(len(retval)):
        threshold = (cupIndex + 1) * TrophiesPerCup
        if threshold <= numTrophiesWon:
            retval[cupIndex] = True

    return retval


def getCourseName(courseId):
    from toontown.toonbase import TTLocalizer
    if courseId in CourseInfo:
        if not CourseInfo[courseId]['name']:
            CourseInfo[courseId]['name'] = TTLocalizer.GolfCourseNames[courseId]
        return CourseInfo[courseId]['name']
    else:
        return ''


def getHoleName(holeId):
    from toontown.toonbase import TTLocalizer
    if holeId in HoleInfo:
        if not HoleInfo[holeId]['name']:
            HoleInfo[holeId]['name'] = TTLocalizer.GolfHoleNames[holeId]
        return HoleInfo[holeId]['name']
    else:
        return ''


def getHistoryIndexForTrophy(trophyIndex):
    retval = -1
    divBy3 = int(trophyIndex / 3)
    if divBy3 < NumHistory:
        retval = divBy3
    return retval


def packGolfHoleBest(holeBest):
    retval = []
    shiftLeft = False
    for hole in holeBest:
        hole &= 15
        if shiftLeft:
            retval[-1] |= hole << 4
            shiftLeft = False
        else:
            retval.append(hole)
            shiftLeft = True

    return retval


def unpackGolfHoleBest(packedHoleBest):
    retval = []
    for packedHole in packedHoleBest:
        lowbitHole = packedHole & 15
        retval.append(lowbitHole)
        highBitHole = (packedHole & 240) >> 4
        retval.append(highBitHole)

    return retval
