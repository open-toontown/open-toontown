import math

from direct.directnotify import DirectNotifyGlobal
from panda3d.core import *


class CPetBrain:
    notify = DirectNotifyGlobal.directNotify.newCategory('CPetBrain')

    def __init__(self):
        pass

    @staticmethod
    def isAttendingUs(pathA, pathB):
        v4 = pathB.getPos(pathA)
        pathAB = ((v4[1] * v4[1]) + (v4[0] * v4[0]) + (v4[2] * v4[2]))
        if not (pathAB > 100.0):
            return True

        v6 = pathA.getPos(pathB)
        pathAA = ((v6[1] * v6[1]) + (v6[0] * v6[0]) + (v6[2] * v6[2]))
        if pathAA == 0.0:
            v6 = Vec3(0, 0, 0)
        else:
            pathAB = pathAA - 1.0
            if pathAB >= 9.999999949504854e-13 or pathAB <= -9.999999949504854e-13:
                pathAD = 1.0 / math.sqrt(pathAA)
                v6 *= pathAD

        v8 = Vec3.forward()
        pathAC = ((v8[1] * v6[1]) + (v8[0] * v6[0]) + (v8[2] * v6[2]))
        if pathAC < 0.8:
            return True
        else:
            return False
