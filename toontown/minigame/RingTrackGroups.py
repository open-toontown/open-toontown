import math
import RingGameGlobals
import RingAction
import RingTracks
import RingTrack
import RingTrackGroup
from direct.showbase import PythonUtil
STATIC = 0
SIMPLE = 1
COMPLEX = 2

def getRandomRingTrackGroup(type, numRings, rng):
    global trackListGenFuncs
    funcTable = trackListGenFuncs[type][numRings - 1]
    func = rng.choice(funcTable)
    tracks, tOffsets, period = func(numRings, rng)
    tracks, tOffsets = __scramble(tracks, tOffsets, rng)
    trackGroup = RingTrackGroup.RingTrackGroup(tracks, period, trackTOffsets=tOffsets, reverseFlag=rng.choice([0, 1]), tOffset=rng.random())
    return trackGroup


def __scramble(tracks, tOffsets, rng):
    newTracks = []
    if tOffsets == None:
        newTOffsets = None
    else:
        newTOffsets = []
    used = [0] * len(tracks)
    count = 0
    while count < len(tracks):
        i = rng.randint(0, len(tracks) - 1)
        if not used[i]:
            used[i] = 1
            count += 1
            newTracks.append(tracks[i])
            if newTOffsets != None:
                newTOffsets.append(tOffsets[i])

    return (newTracks, newTOffsets)


def angleToXY(angle, radius = 1.0):
    return [radius * math.sin(angle), radius * math.cos(angle)]


def getTightCircleStaticPositions(numRings):
    positions = []
    if numRings == 1:
        positions.append([0, 0])
    else:
        radius = RingGameGlobals.RING_RADIUS * 1.5 / RingGameGlobals.MAX_TOONXZ
        step = 2.0 * math.pi / float(numRings)
        for i in range(0, numRings):
            angle = i * step + step / 2.0
            positions.append(angleToXY(angle, 1.0 / 3.0))

    return positions


def get_keypad(numRings, rng):
    positions = (RingTracks.center,
     RingTracks.up,
     RingTracks.down,
     RingTracks.left,
     RingTracks.right,
     RingTracks.ul,
     RingTracks.ur,
     RingTracks.lr,
     RingTracks.ll)
    tracks = []
    usedPositions = [None]
    posScale = 0.7 + rng.random() * 0.2
    for i in range(0, numRings):
        pos = None
        while pos in usedPositions:
            pos = rng.choice(positions)

        usedPositions.append(pos)
        scaledPos = [0, 0]
        scaledPos[0] = pos[0] * posScale
        scaledPos[1] = pos[1] * posScale
        action = RingAction.RingActionStaticPos(scaledPos)
        track = RingTrack.RingTrack([action], [1.0])
        tracks.append(track)

    return (tracks, None, 1.0)


fullCirclePeriod = 6.0
plusPeriod = 4.0

def get_evenCircle(numRings, rng):
    tracks = []
    tOffsets = []
    for i in range(0, numRings):
        actions, durations = RingTracks.getCircleRingActions()
        track = RingTrack.RingTrack(actions, durations)
        tracks.append(track)
        tOffsets.append(float(i) / numRings)

    return (tracks, tOffsets, fullCirclePeriod)


def get_followCircle(numRings, rng):
    tracks = []
    tOffsets = []
    for i in range(0, numRings):
        actions, durations = RingTracks.getCircleRingActions()
        track = RingTrack.RingTrack(actions, durations)
        delay = 0.12
        tracks.append(track)
        tOffsets.append(float(i) * delay)

    return (tracks, tOffsets, fullCirclePeriod)


def get_evenCircle_withStationaryCenterRings(numRings, rng):
    tracks = []
    tOffsets = []
    numCenterRings = rng.randint(1, numRings - 1)
    positions = getTightCircleStaticPositions(numCenterRings)
    for i in range(0, numCenterRings):
        action = RingAction.RingActionStaticPos(positions[i])
        track = RingTrack.RingTrack([action])
        tracks.append(track)
        tOffsets.append(0)

    numOuterRings = numRings - numCenterRings
    for i in range(0, numOuterRings):
        actions, durations = RingTracks.getCircleRingActions()
        track = RingTrack.RingTrack(actions, durations)
        tracks.append(track)
        tOffsets.append(float(i) / numOuterRings)

    return (tracks, tOffsets, fullCirclePeriod)


def __get_Slots(numRings, rng, vertical = 1):
    tracks = []
    tOffsets = []
    fpTab = []
    for i in range(numRings):
        fpTab.append(PythonUtil.lineupPos(i, numRings, 2.0 / 3))

    offset = 1 - fpTab[-1]
    offset = rng.random() * (offset * 2) - offset
    fpTab = map(lambda x: x + offset, fpTab)
    for i in range(0, numRings):
        if vertical:
            getActionsFunc = RingTracks.getVerticalSlotActions
        else:
            getActionsFunc = RingTracks.getHorizontalSlotActions
        actions, durations = getActionsFunc(fpTab[i])
        track = RingTrack.RingTrack(actions, durations)
        tracks.append(track)
        tOffsets.append(float(i) / numRings * 0.5)

    return (tracks, tOffsets, fullCirclePeriod)


def get_verticalSlots(numRings, rng):
    return __get_Slots(numRings, rng, vertical=1)


def get_horizontalSlots(numRings, rng):
    return __get_Slots(numRings, rng, vertical=0)


def get_plus(numRings, rng):
    up = RingTracks.getPlusUpRingActions
    down = RingTracks.getPlusDownRingActions
    left = RingTracks.getPlusLeftRingActions
    right = RingTracks.getPlusRightRingActions
    actionSets = {2: [[up, down], [left, right]],
     3: [[up, left, right],
         [left, up, down],
         [down, left, right],
         [right, up, down]],
     4: [[up,
          down,
          left,
          right]]}
    tracks = []
    actionSet = rng.choice(actionSets[numRings])
    for i in range(0, numRings):
        actions, durations = actionSet[i]()
        track = RingTrack.RingTrack(actions, durations)
        tracks.append(track)

    return (tracks, [0] * numRings, plusPeriod)


infinityPeriod = 5.0
fullCirclePeriodFaster = 5.0
plusPeriodFaster = 2.5
infinityTOffsets = []

def __initInfinityTOffsets():
    global infinityTOffsets
    offsets = [[],
     [],
     [],
     []]
    offsets[0] = [0.0]
    offsets[1] = [0.0, 3.0 / 4.0]
    offsets[2] = [0.0, 1.0 / 3.0, 2.0 / 3.0]
    inc = 14.0 / 23.0
    for numRings in range(4, 5):
        o = [0] * numRings
        accum = 0.0
        for i in range(0, numRings):
            o[i] = accum % 1.0
            accum += inc

        offsets[numRings - 1] = o

    infinityTOffsets = offsets


__initInfinityTOffsets()

def get_vertInfinity(numRings, rng):
    tracks = []
    for i in range(0, numRings):
        actions, durations = RingTracks.getVerticalInfinityRingActions()
        track = RingTrack.RingTrack(actions, durations)
        tracks.append(track)

    return (tracks, infinityTOffsets[numRings - 1], infinityPeriod)


def get_horizInfinity(numRings, rng):
    tracks = []
    for i in range(0, numRings):
        actions, durations = RingTracks.getHorizontalInfinityRingActions()
        track = RingTrack.RingTrack(actions, durations)
        tracks.append(track)

    return (tracks, infinityTOffsets[numRings - 1], infinityPeriod)


def get_evenCircle_withStationaryCenterRings_FASTER(numRings, rng):
    tracks, tOffsets, period = get_evenCircle_withStationaryCenterRings(numRings, rng)
    return (tracks, tOffsets, fullCirclePeriodFaster)


def get_plus_FASTER(numRings, rng):
    tracks, tOffsets, period = get_plus(numRings, rng)
    return (tracks, tOffsets, plusPeriodFaster)


allFuncs = [[get_keypad], [get_evenCircle,
  get_followCircle,
  get_evenCircle_withStationaryCenterRings,
  get_verticalSlots,
  get_horizontalSlots,
  get_plus], [get_vertInfinity,
  get_horizInfinity,
  get_evenCircle_withStationaryCenterRings_FASTER,
  get_plus_FASTER]]
dontUseFuncs = [[get_followCircle,
  get_evenCircle_withStationaryCenterRings,
  get_evenCircle_withStationaryCenterRings_FASTER,
  get_plus,
  get_plus_FASTER],
 [],
 [],
 []]
trackListGenFuncs = []

def __listComplement(list1, list2):
    result = []
    for item in list1:
        if item not in list2:
            result.append(item)

    return result


def __initFuncTables():
    global trackListGenFuncs
    table = [[], [], []]
    for diff in range(0, len(table)):
        table[diff] = [[],
         [],
         [],
         []]
        for numRings in range(0, len(table[diff])):
            table[diff][numRings] = __listComplement(allFuncs[diff], dontUseFuncs[numRings])

    trackListGenFuncs = table


__initFuncTables()
