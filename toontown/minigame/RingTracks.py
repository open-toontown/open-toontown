import math
import RingTrack
import RingAction
center = (0, 0)
up = (0, 1)
down = (0, -1)
left = (-1, 0)
right = (1, 0)
ul = (-1, 1)
ur = (1, 1)
lr = (1, -1)
ll = (-1, -1)

def ringLerp(t, a, b):
    omT = 1.0 - t
    return (float(a[0]) * omT + float(b[0]) * t, float(a[1]) * omT + float(b[1]) * t)


def ringClerp(t, a, b):
    return ringLerp(t * t * (3 - 2 * t), a, b)


def getSquareRingActions():
    return ([RingAction.RingActionFunction(ringClerp, [ul, ur]),
      RingAction.RingActionFunction(ringClerp, [ur, lr]),
      RingAction.RingActionFunction(ringClerp, [lr, ll]),
      RingAction.RingActionFunction(ringClerp, [ll, ul])], [0.25,
      0.25,
      0.25,
      0.25])


def getVerticalSlotActions(x):
    return ([RingAction.RingActionFunction(ringClerp, [(x, 1), (x, -1)]), RingAction.RingActionFunction(ringClerp, [(x, -1), (x, 1)])], [0.5, 0.5])


def getHorizontalSlotActions(y):
    return ([RingAction.RingActionFunction(ringClerp, [(1, y), (-1, y)]), RingAction.RingActionFunction(ringClerp, [(-1, y), (1, y)])], [0.5, 0.5])


def getCircleRingActions():

    def circlePos(t):
        return (math.sin(t * 2.0 * math.pi), math.cos(t * 2.0 * math.pi))

    return ([RingAction.RingActionFunction(circlePos, [])], [1.0])


def getVerticalInfinityRingActions():

    def vertInfPos(t):
        return (0.5 * math.sin(2.0 * t * 2.0 * math.pi), math.cos(t * 2.0 * math.pi))

    return ([RingAction.RingActionFunction(vertInfPos, [])], [1.0])


def getHorizontalInfinityRingActions():

    def horizInfPos(t):
        return (math.sin(t * 2.0 * math.pi), 0.5 * math.sin(2.0 * t * 2.0 * math.pi))

    return ([RingAction.RingActionFunction(horizInfPos, [])], [1.0])


RingOffset = 0.4

def getPlusUpRingActions():
    return ([RingAction.RingActionFunction(ringClerp, [(0, RingOffset), (0, 1)]), RingAction.RingActionFunction(ringClerp, [(0, 1), (0, RingOffset)])], [0.5, 0.5])


def getPlusDownRingActions():
    return ([RingAction.RingActionFunction(ringClerp, [(0, -RingOffset), (0, -1)]), RingAction.RingActionFunction(ringClerp, [(0, -1), (0, -RingOffset)])], [0.5, 0.5])


def getPlusRightRingActions():
    return ([RingAction.RingActionFunction(ringClerp, [(RingOffset, 0), (1, 0)]), RingAction.RingActionFunction(ringClerp, [(1, 0), (RingOffset, 0)])], [0.5, 0.5])


def getPlusLeftRingActions():
    return ([RingAction.RingActionFunction(ringClerp, [(-RingOffset, 0), (-1, 0)]), RingAction.RingActionFunction(ringClerp, [(-1, 0), (-RingOffset, 0)])], [0.5, 0.5])


def getHalfDomeRingActions():

    def halfDome(t):
        return (math.cos(t * math.pi), -math.sin(t * math.pi))

    x1 = -1.0
    x2 = -1.0 / 3.0
    x3 = 1.0 / 3.0
    x4 = 1.0
    return ([RingAction.RingActionFunction(ringClerp, [(x1, 0), (x2, 0)]),
      RingAction.RingActionFunction(ringClerp, [(x2, 0), (x3, 0)]),
      RingAction.RingActionFunction(ringClerp, [(x3, 0), (x4, 0)]),
      RingAction.RingActionFunction(halfDome, [])], [0.25,
      0.25,
      0.25,
      0.25])
