from pandac.PandaModules import VBase3, BitMask32
GameTime = 60
NumBarrels = 4
BarrelStartingPositions = (VBase3(4.3, 4, 0),
 VBase3(4.3, -4, 0),
 VBase3(-4.3, 4, 0),
 VBase3(-4.3, -4, 0))
ToonStartingPositions = (VBase3(0, 16, 0),
 VBase3(0, -16, 0),
 VBase3(-16, 0, 0),
 VBase3(16, 0, 0))
CogStartingPositions = (VBase3(35, 18, 0),
 VBase3(35, 0, 0),
 VBase3(35, -18, 0),
 VBase3(-35, 18, 0),
 VBase3(-35, 0, 0),
 VBase3(-35, -18, 0),
 VBase3(0, 27, 0),
 VBase3(0, -27, 0),
 VBase3(35, 9, 0),
 VBase3(-35, 9, 0),
 VBase3(35, -9, 0),
 VBase3(-35, -9, 0))
CogReturnPositions = (VBase3(-35, 28, 0),
 VBase3(-14, 28, 0),
 VBase3(14, 28, 0),
 VBase3(35, 28, 0),
 VBase3(35, 0, 0),
 VBase3(35, -28, 0),
 VBase3(-14, -28, 0),
 VBase3(14, -28, 0),
 VBase3(-35, -28, 0),
 VBase3(-35, 0, 0))
StageHalfWidth = 25
StageHalfHeight = 18
NoGoal = 0
BarrelGoal = 1
ToonGoal = 2
RunAwayGoal = 3
InvalidGoalId = -1
GoalStr = {NoGoal: 'NoGoal',
 BarrelGoal: 'BarrelGoal',
 ToonGoal: 'ToonGoal',
 RunAwayGoal: 'RunAwayGoal',
 InvalidGoalId: 'InvalidGoa'}
BarrelBitmask = BitMask32(512)
BarrelOnGround = -1
NoBarrelCarried = -1
LyingDownDuration = 2.0
MAX_SCORE = 20
MIN_SCORE = 3

def calcScore(t):
    range = MAX_SCORE - MIN_SCORE
    score = range * (float(t) / GameTime) + MIN_SCORE
    return int(score + 0.5)


def getMaxScore():
    result = calcScore(GameTime)
    return result


NumCogsTable = [{2000: 5,
  1000: 5,
  5000: 5,
  4000: 5,
  3000: 5,
  9000: 5},
 {2000: 7,
  1000: 7,
  5000: 7,
  4000: 7,
  3000: 7,
  9000: 7},
 {2000: 9,
  1000: 9,
  5000: 9,
  4000: 9,
  3000: 9,
  9000: 9},
 {2000: 11,
  1000: 11,
  5000: 11,
  4000: 11,
  3000: 11,
  9000: 11}]
CogSpeedTable = [{2000: 6.0,
  1000: 6.4,
  5000: 6.8,
  4000: 7.2,
  3000: 7.6,
  9000: 8.0},
 {2000: 6.0,
  1000: 6.4,
  5000: 6.8,
  4000: 7.2,
  3000: 7.6,
  9000: 8.0},
 {2000: 6.0,
  1000: 6.4,
  5000: 6.8,
  4000: 7.2,
  3000: 7.6,
  9000: 8.0},
 {2000: 6.0,
  1000: 6.4,
  5000: 6.8,
  4000: 7.2,
  3000: 7.6,
  9000: 8.0}]
ToonSpeed = 9.0
PerfectBonus = [8,
 6,
 4,
 2]

def calculateCogs(numPlayers, safezone):
    result = 5
    if numPlayers <= len(NumCogsTable):
        if safezone in NumCogsTable[numPlayers - 1]:
            result = NumCogsTable[numPlayers - 1][safezone]
    return result


def calculateCogSpeed(numPlayers, safezone):
    result = 6.0
    if numPlayers <= len(NumCogsTable):
        if safezone in CogSpeedTable[numPlayers - 1]:
            result = CogSpeedTable[numPlayers - 1][safezone]
    return result
