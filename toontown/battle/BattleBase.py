from pandac.PandaModules import *
from toontown.toonbase.ToontownBattleGlobals import *
from direct.task.Timer import *
import math
import functools
from direct.directnotify import DirectNotifyGlobal
from toontown.toon import NPCToons
from toontown.toonbase import TTLocalizer
TOON_ID_COL = 0
TOON_TRACK_COL = 1
TOON_LVL_COL = 2
TOON_TGT_COL = 3
TOON_HP_COL = 4
TOON_ACCBONUS_COL = 5
TOON_HPBONUS_COL = 6
TOON_KBBONUS_COL = 7
SUIT_DIED_COL = 8
SUIT_REVIVE_COL = 9
SUIT_ID_COL = 0
SUIT_ATK_COL = 1
SUIT_TGT_COL = 2
SUIT_HP_COL = 3
TOON_DIED_COL = 4
SUIT_BEFORE_TOONS_COL = 5
SUIT_TAUNT_COL = 6
NO_ID = -1
NO_ATTACK = -1
UN_ATTACK = -2
PASS_ATTACK = -3
NO_TRAP = -1
LURE_SUCCEEDED = -1
PASS = 98
SOS = 99
NPCSOS = 97
PETSOS = 96
FIRE = 100
HEAL = HEAL_TRACK
TRAP = TRAP_TRACK
LURE = LURE_TRACK
SOUND = SOUND_TRACK
THROW = THROW_TRACK
SQUIRT = SQUIRT_TRACK
DROP = DROP_TRACK
TOON_ATTACK_TIME = 12.0
SUIT_ATTACK_TIME = 12.0
TOON_TRAP_DELAY = 0.8
TOON_SOUND_DELAY = 1.0
TOON_THROW_DELAY = 0.5
TOON_THROW_SUIT_DELAY = 1.0
TOON_SQUIRT_DELAY = 0.5
TOON_SQUIRT_SUIT_DELAY = 1.0
TOON_DROP_DELAY = 0.8
TOON_DROP_SUIT_DELAY = 1.0
TOON_RUN_T = 3.3
TIMEOUT_PER_USER = 5
TOON_FIRE_DELAY = 0.5
TOON_FIRE_SUIT_DELAY = 1.0
REWARD_TIMEOUT = 120
FLOOR_REWARD_TIMEOUT = 4
BUILDING_REWARD_TIMEOUT = 300
try:
    CLIENT_INPUT_TIMEOUT = base.config.GetFloat('battle-input-timeout', TTLocalizer.BBbattleInputTimeout)
except:
    CLIENT_INPUT_TIMEOUT = simbase.config.GetFloat('battle-input-timeout', TTLocalizer.BBbattleInputTimeout)

def levelAffectsGroup(track, level):
    return attackAffectsGroup(track, level)


def attackAffectsGroup(track, level, type = None):
    if track == NPCSOS or type == NPCSOS or track == PETSOS or type == PETSOS:
        return 1
    elif track >= 0 and track <= DROP_TRACK:
        return AvPropTargetCat[AvPropTarget[track]][level]
    else:
        return 0


def getToonAttack(id, track = NO_ATTACK, level = -1, target = -1):
    return [id,
     track,
     level,
     target,
     [],
     0,
     0,
     [],
     0,
     0]


def getDefaultSuitAttacks():
    suitAttacks = [[NO_ID,
      NO_ATTACK,
      -1,
      [],
      0,
      0,
      0],
     [NO_ID,
      NO_ATTACK,
      -1,
      [],
      0,
      0,
      0],
     [NO_ID,
      NO_ATTACK,
      -1,
      [],
      0,
      0,
      0],
     [NO_ID,
      NO_ATTACK,
      -1,
      [],
      0,
      0,
      0]]
    return suitAttacks


def getDefaultSuitAttack():
    return [NO_ID,
     NO_ATTACK,
     -1,
     [],
     0,
     0,
     0]


def findToonAttack(toons, attacks, track):
    foundAttacks = []
    for t in toons:
        if t in attacks:
            attack = attacks[t]
            local_track = attack[TOON_TRACK_COL]
            if track != NPCSOS and attack[TOON_TRACK_COL] == NPCSOS:
                local_track = NPCToons.getNPCTrack(attack[TOON_TGT_COL])
            if local_track == track:
                if local_track == FIRE:
                    canFire = 1
                    for attackCheck in foundAttacks:
                        if attackCheck[TOON_TGT_COL] == attack[TOON_TGT_COL]:
                            canFire = 0

                    if canFire:
                        foundAttacks.append(attack)
                else:
                    foundAttacks.append(attack)

    def compFunc(a, b):
        if a[TOON_LVL_COL] > b[TOON_LVL_COL]:
            return 1
        elif a[TOON_LVL_COL] < b[TOON_LVL_COL]:
            return -1
        return 0

    foundAttacks.sort(key=functools.cmp_to_key(compFunc))
    return foundAttacks


SERVER_BUFFER_TIME = 2.0
SERVER_INPUT_TIMEOUT = CLIENT_INPUT_TIMEOUT + SERVER_BUFFER_TIME
MAX_JOIN_T = TTLocalizer.BBbattleInputTimeout
FACEOFF_TAUNT_T = 3.5
FACEOFF_LOOK_AT_PROP_T = 6
ELEVATOR_T = 4.0
BATTLE_SMALL_VALUE = 1e-07
MAX_EXPECTED_DISTANCE_FROM_BATTLE = 50.0

class BattleBase:
    notify = DirectNotifyGlobal.directNotify.newCategory('BattleBase')
    suitPoints = (((Point3(0, 5, 0), 179),),
     ((Point3(2, 5.3, 0), 170), (Point3(-2, 5.3, 0), 180)),
     ((Point3(4, 5.2, 0), 170), (Point3(0, 6, 0), 179), (Point3(-4, 5.2, 0), 190)),
     ((Point3(6, 4.4, 0), 160),
      (Point3(2, 6.3, 0), 170),
      (Point3(-2, 6.3, 0), 190),
      (Point3(-6, 4.4, 0), 200)))
    suitPendingPoints = ((Point3(-4, 8.2, 0), 190),
     (Point3(0, 9, 0), 179),
     (Point3(4, 8.2, 0), 170),
     (Point3(8, 3.2, 0), 160))
    toonPoints = (((Point3(0, -6, 0), 0),),
     ((Point3(1.5, -6.5, 0), 5), (Point3(-1.5, -6.5, 0), -5)),
     ((Point3(3, -6.75, 0), 5), (Point3(0, -7, 0), 0), (Point3(-3, -6.75, 0), -5)),
     ((Point3(4.5, -7, 0), 10),
      (Point3(1.5, -7.5, 0), 5),
      (Point3(-1.5, -7.5, 0), -5),
      (Point3(-4.5, -7, 0), -10)))
    toonPendingPoints = ((Point3(-3, -8, 0), -5),
     (Point3(0, -9, 0), 0),
     (Point3(3, -8, 0), 5),
     (Point3(5.5, -5.5, 0), 20))
    posA = Point3(0, 10, 0)
    posB = Point3(-7.071, 7.071, 0)
    posC = Point3(-10, 0, 0)
    posD = Point3(-7.071, -7.071, 0)
    posE = Point3(0, -10, 0)
    posF = Point3(7.071, -7.071, 0)
    posG = Point3(10, 0, 0)
    posH = Point3(7.071, 7.071, 0)
    allPoints = (posA,
     posB,
     posC,
     posD,
     posE,
     posF,
     posG,
     posH)
    toonCwise = [posA,
     posB,
     posC,
     posD,
     posE]
    toonCCwise = [posH,
     posG,
     posF,
     posE]
    suitCwise = [posE,
     posF,
     posG,
     posH,
     posA]
    suitCCwise = [posD,
     posC,
     posB,
     posA]
    suitSpeed = 4.8
    toonSpeed = 8.0

    def __init__(self):
        self.pos = Point3(0, 0, 0)
        self.initialSuitPos = Point3(0, 1, 0)
        self.timer = Timer()
        self.resetLists()

    def resetLists(self):
        self.suits = []
        self.pendingSuits = []
        self.joiningSuits = []
        self.activeSuits = []
        self.luredSuits = []
        self.suitGone = 0
        self.toons = []
        self.joiningToons = []
        self.pendingToons = []
        self.activeToons = []
        self.runningToons = []
        self.toonGone = 0
        self.helpfulToons = []

    def calcFaceoffTime(self, centerpos, suitpos):
        facing = Vec3(centerpos - suitpos)
        facing.normalize()
        suitdest = Point3(centerpos - Point3(facing * 6.0))
        dist = Vec3(suitdest - suitpos).length()
        return dist / BattleBase.suitSpeed

    def calcSuitMoveTime(self, pos0, pos1):
        dist = Vec3(pos0 - pos1).length()
        return dist / BattleBase.suitSpeed

    def calcToonMoveTime(self, pos0, pos1):
        dist = Vec3(pos0 - pos1).length()
        return dist / BattleBase.toonSpeed

    def buildJoinPointList(self, avPos, destPos, toon = 0):
        minDist = 999999.0
        nearestP = None
        for p in BattleBase.allPoints:
            dist = Vec3(avPos - p).length()
            if dist < minDist:
                nearestP = p
                minDist = dist

        self.notify.debug('buildJoinPointList() - avp: %s nearp: %s' % (avPos, nearestP))
        dist = Vec3(avPos - destPos).length()
        if dist < minDist:
            self.notify.debug('buildJoinPointList() - destPos is nearest')
            return []
        if toon == 1:
            if nearestP == BattleBase.posE:
                self.notify.debug('buildJoinPointList() - posE')
                plist = [BattleBase.posE]
            elif BattleBase.toonCwise.count(nearestP) == 1:
                self.notify.debug('buildJoinPointList() - clockwise')
                index = BattleBase.toonCwise.index(nearestP)
                plist = BattleBase.toonCwise[index + 1:]
            else:
                self.notify.debug('buildJoinPointList() - counter-clockwise')
                index = BattleBase.toonCCwise.index(nearestP)
                plist = BattleBase.toonCCwise[index + 1:]
        elif nearestP == BattleBase.posA:
            self.notify.debug('buildJoinPointList() - posA')
            plist = [BattleBase.posA]
        elif BattleBase.suitCwise.count(nearestP) == 1:
            self.notify.debug('buildJoinPointList() - clockwise')
            index = BattleBase.suitCwise.index(nearestP)
            plist = BattleBase.suitCwise[index + 1:]
        else:
            self.notify.debug('buildJoinPointList() - counter-clockwise')
            index = BattleBase.suitCCwise.index(nearestP)
            plist = BattleBase.suitCCwise[index + 1:]
        self.notify.debug('buildJoinPointList() - plist: %s' % plist)
        return plist

    def addHelpfulToon(self, toonId):
        if toonId not in self.helpfulToons:
            self.helpfulToons.append(toonId)
