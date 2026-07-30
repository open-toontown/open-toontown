from direct.directnotify import DirectNotifyGlobal
from panda3d.core import *
from math import *

class Trajectory:
    notify = DirectNotifyGlobal.directNotify.newCategory('Trajectory')
    gravity = 32.0
    __radius = 2.0

    def __init__(self, startTime, startPos, startVel, gravMult = 1.0):
        self.setStartTime(startTime)
        self.setStartPos(startPos)
        self.setStartVel(startVel)
        self.setGravityMult(gravMult)

    def setStartTime(self, t):
        self.__startTime = t

    def setStartPos(self, sp):
        self.__startPos = sp

    def setStartVel(self, sv):
        self.__startVel = sv

    def setGravityMult(self, mult):
        self.__zAcc = mult * -Trajectory.gravity

    def getStartTime(self):
        return self.__startTime

    def __str__(self):
        return 'startTime: %s, startPos: %s, startVel: %s, zAcc: %s' % (self.__startTime,
         repr(self.__startPos),
         repr(self.__startVel),
         self.__zAcc)

    def __calcTimeOfHighestPoint(self):
        t = -self.__startVel[2] / self.__zAcc
        if t < 0:
            t = 0
        return t + self.__startTime

    def calcTimeOfImpactOnPlane(self, height = 0):
        a = self.__zAcc * 0.5
        b = self.__startVel[2]
        c = self.__startPos[2] - height
        D = b * b - 4.0 * a * c
        if D < 0:
            return -1.0
        elif D == 0:
            t = -b / (2.0 * a)
        else:
            t = (-b - sqrt(D)) / (2.0 * a)
        if t < 0:
            return -1.0
        return t + self.__startTime

    def calcZ(self, t):
        tt = t - self.__startTime
        return self.__startPos[2] + self.__startVel[2] * tt + 0.5 * self.__zAcc * tt * tt

    def __reachesHeight(self, height):
        if self.calcZ(self.__calcTimeOfHighestPoint()) < height:
            return 0
        return 1

    def getPos(self, t):
        tt = t - self.__startTime
        return Point3(self.__startPos[0] + self.__startVel[0] * tt, self.__startPos[1] + self.__startVel[1] * tt, self.calcZ(t))

    def getVel(self, t):
        tt = t - self.__startTime
        return Vec3(self.__startVel[0], self.__startVel[1], self.__startVel[2] + self.__zAcc * tt)

    def getStartTime(self):
        return self.__startTime

    def checkCollisionWithGround(self, height = 0):
        return self.calcTimeOfImpactOnPlane(height)

    def checkCollisionWithDisc(self, discCenter, discRadius):
        if self.__reachesHeight(discCenter[2]) == 0:
            return -1.0
        t_atDiscHeight = self.calcTimeOfImpactOnPlane(discCenter[2])
        if t_atDiscHeight < 0:
            return -1.0
        p_atDiscHeight = self.getPos(t_atDiscHeight)
        offset_x = p_atDiscHeight[0] - discCenter[0]
        offset_y = p_atDiscHeight[1] - discCenter[1]
        offset_from_center_SQUARED = offset_x * offset_x + offset_y * offset_y
        max_offset = discRadius
        max_offset_SQUARED = max_offset * max_offset
        if offset_from_center_SQUARED < max_offset_SQUARED:
            return t_atDiscHeight
        else:
            return -1.0

    def calcEnterAndLeaveCylinderXY(self, cylBottomCenter, cylRadius):
        v = Vec2(cylBottomCenter[0], cylBottomCenter[1])
        o = Vec2(self.__startPos[0], self.__startPos[1])
        d = Vec2(self.__startVel[0], self.__startVel[1])
        d.normalize()
        b = d.dot(o - v)
        c = (o - v).dot(o - v) - cylRadius * cylRadius
        bsmc = b * b - c
        if bsmc <= 0.0:
            return (-1.0, -1.0)
        sqrt_bsmc = sqrt(bsmc)
        t1 = -b - sqrt_bsmc
        t2 = -b + sqrt_bsmc
        if t1 > t2:
            self.notify.debug('calcEnterAndLeaveCylinderXY: t1 > t2??')
        mag = Vec2(self.__startVel[0], self.__startVel[1]).length()
        t1 = t1 / mag
        t2 = t2 / mag
        return (t1 + self.__startTime, t2 + self.__startTime)

    def checkCollisionWithCylinderSides(self, cylBottomCenter, cylRadius, cylHeight):
        if self.__reachesHeight(cylBottomCenter[2]) == 0:
            return -1.0
        t1, t2 = self.calcEnterAndLeaveCylinderXY(cylBottomCenter, cylRadius)
        p1 = self.getPos(t1)
        p2 = self.getPos(t2)
        cylTopHeight = cylBottomCenter[2] + cylHeight
        if p1[2] > cylTopHeight and p2[2] > cylTopHeight:
            return -1.0
        if p1[2] < cylTopHeight and p1[2] > cylBottomCenter[2]:
            if t1 > self.__startTime:
                return t1
        return -1.0

    def checkCollisionWithProjectile(self, projectile):
        return -1.0
