from panda3d.core import *
from toontown.toonbase.ToontownBattleGlobals import *
from direct.task.Timer import *
import functools
from direct.directnotify import DirectNotifyGlobal
from toontown.toon import NPCToons
from toontown.toonbase import TTLocalizer

# Constants
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
NO_ID, NO_ATTACK, UN_ATTACK, PASS_ATTACK = -1, -1, -2, -3
NO_TRAP, LURE_SUCCEEDED, PASS, SOS, NPCSOS, PETSOS, FIRE = -1, -1, 98, 99, 97, 96, 100
HEAL = HEAL_TRACK
TRAP, LURE, SOUND, THROW, SQUIRT, DROP = TRAP_TRACK, LURE_TRACK, SOUND_TRACK, THROW_TRACK, SQUIRT_TRACK, DROP_TRACK
TOON_ATTACK_TIME, SUIT_ATTACK_TIME = 3.0, 3.0
TOON_TRAP_DELAY, TOON_SOUND_DELAY, TOON_THROW_DELAY, TOON_THROW_SUIT_DELAY = 0.2, 0.25, 0.125, 0.25
TOON_SQUIRT_DELAY, TOON_SQUIRT_SUIT_DELAY, TOON_DROP_DELAY, TOON_DROP_SUIT_DELAY = 0.125, 0.25, 0.2, 0.25
TOON_RUN_T, TIMEOUT_PER_USER, TOON_FIRE_DELAY, TOON_FIRE_SUIT_DELAY = 0.825, 5, 0.125, 0.25
REWARD_TIMEOUT, FLOOR_REWARD_TIMEOUT, BUILDING_REWARD_TIMEOUT = 120, 4, 300
CLIENT_INPUT_TIMEOUT = ConfigVariableDouble('battle-input-timeout', 999999).value
SERVER_BUFFER_TIME, SERVER_INPUT_TIMEOUT, MAX_JOIN_T = 2.0, CLIENT_INPUT_TIMEOUT + 2.0, TTLocalizer.BBbattleInputTimeout
FACEOFF_TAUNT_T, FACEOFF_LOOK_AT_PROP_T, ELEVATOR_T, BATTLE_SMALL_VALUE = 1.75, 3.0, 2.0, 1e-07
MAX_EXPECTED_DISTANCE_FROM_BATTLE = 50.0

# Functions
def levelAffectsGroup(track, level):
    return attackAffectsGroup(track, level)

def attackAffectsGroup(track, level, type=None):
    if track in [NPCSOS, PETSOS] or type in [NPCSOS, PETSOS]:
        return 1
    elif 0 <= track <= DROP_TRACK:
        return AvPropTargetCat[AvPropTarget[track]][level]
    else:
        return 0

def getToonAttack(id, track=NO_ATTACK, level=-1, target=-1):
    return [id, track, level, target, [], 0, 0, [], 0, 0]

def getDefaultSuitAttacks():
    return [[NO_ID, NO_ATTACK, -1, [], 0, 0, 0] for _ in range(4)]

def getDefaultSuitAttack():
    return [NO_ID, NO_ATTACK, -1, [], 0, 0, 0]

def findToonAttack(toons, attacks, track):
    foundAttacks = []
    for t in toons:
        if t in attacks and (attack := attacks[t])[TOON_TRACK_COL] == track:
            # Check if the attack's track matches the given track
            higher_level = True
            for b in foundAttacks:
                if attack[TOON_LVL_COL] <= b[TOON_LVL_COL]:
                    higher_level = False
                    break
            if higher_level:
                foundAttacks = [attack]
    return foundAttacks

class BattleBase:
    notify = DirectNotifyGlobal.directNotify.newCategory('BattleBase')
    suitPoints = (((Point3(0, 5, 0), 179),), ((Point3(2, 5.3, 0), 170), (Point3(-2, 5.3, 0), 180)),
                  ((Point3(4, 5.2, 0), 170), (Point3(0, 6, 0), 179), (Point3(-4, 5.2, 0), 190)),
                  ((Point3(6, 4.4, 0), 160), (Point3(2, 6.3, 0), 170), (Point3(-2, 6.3, 0), 190), (Point3(-6, 4.4, 0), 200)))
    suitPendingPoints = ((Point3(-4, 8.2, 0), 190), (Point3(0, 9, 0), 179), (Point3(4, 8.2, 0), 170),
                         (Point3(8, 3.2, 0), 160))
    toonPoints = (((Point3(0, -6, 0), 0),), ((Point3(1.5, -6.5, 0), 5), (Point3(-1.5, -6.5, 0), -5)),
                   ((Point3(3, -6.75, 0), 5), (Point3(0, -7, 0), 0), (Point3(-3, -6.75, 0), -5)),
                   ((Point3(4.5, -7, 0), 10), (Point3(1.5, -7.5, 0), 5), (Point3(-1.5, -7.5, 0), -5),
                    (Point3(-4.5, -7, 0), -10)))
    toonPendingPoints = ((Point3(-3, -8, 0), -5), (Point3(0, -9, 0), 0), (Point3(3, -8, 0), 5),
                         (Point3(5.5, -5.5, 0), 20))
    posA, posB, posC, posD, posE, posF, posG, posH = Point3(0, 10, 0), Point3(-7.071, 7.071, 0), Point3(-10, 0, 0), \
                                                     Point3(-7.071, -7.071, 0), Point3(0, -10, 0), \
                                                     Point3(7.071, -7.071, 0), Point3(10, 0, 0), Point3(7.071, 7.071, 0)
    allPoints = (posA, posB, posC, posD, posE, posF, posG, posH)
    toonCwise = [posA, posB, posC, posD, posE]
    toonCCwise = [posH, posG, posF, posE]
    suitCwise = [posE, posF, posG, posH, posA]
    suitCCwise = [posD, posC, posB, posA]
    suitSpeed, toonSpeed = 4.8, 8.0

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
        self.activeToons = []  # Change activeToons to be a list
        self.runningToons = []
        self.toonGone = 0
        self.helpfulToons = []  # Ensure helpfulToons is initialized as a list

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

    def buildJoinPointList(self, avPos, destPos, toon=0):
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
        if isinstance(self.helpfulToons, int):
            # If self.helpfulToons is an integer, convert it to a list
            self.helpfulToons = [self.helpfulToons]
        
        if toonId not in self.helpfulToons:
            # Check if toonId is not in the list
            self.helpfulToons.append(toonId)