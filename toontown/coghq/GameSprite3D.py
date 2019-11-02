from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *
import math
import random

class GameSprite:
    colorRed = Vec4(1, 0.2, 0.2, 1)
    colorBlue = Vec4(0.7, 0.8, 1, 1)
    colorGreen = Vec4(0, 1, 0, 1)
    colorGhostRed = Vec4(1, 0.2, 0.2, 0.5)
    colorGhostBlue = Vec4(0.7, 0.8, 1, 0.5)
    colorGhostGreen = Vec4(0, 1, 0, 0.5)
    colorDisolveRed = Vec4(1, 0.2, 0.2, 0.0)
    colorDisolveBlue = Vec4(0.7, 0.8, 1, 0.0)
    colorDisolveGreen = Vec4(0, 1, 0, 0.0)
    colorWhite = Vec4(1, 1, 1, 1)
    colorBlack = Vec4(0, 0, 0, 1.0)
    colorDisolveWhite = Vec4(1, 1, 1, 0.0)
    colorDisolveBlack = Vec4(0, 0, 0, 0.0)
    colorShadow = Vec4(0, 0, 0, 0.5)
    colorPurple = Vec4(1.0, 0, 1.0, 1.0)
    colorDisolvePurple = Vec4(1.0, 0, 1.0, 0.0)
    colorYellow = Vec4(1.0, 1.0, 0.0, 1.0)
    colorDisolveYellow = Vec4(1.0, 1.0, 0.0, 0.0)
    colorOrange = Vec4(1.0, 0.5, 0.0, 1.0)
    colorDisolveOrange = Vec4(1.0, 0.5, 0.0, 0.0)
    colorAqua = Vec4(0.0, 1.0, 1.0, 1.0)
    colorDisolveAqua = Vec4(0.0, 1.0, 1.0, 0.0)
    colorSteel = Vec4(0.5, 0.5, 0.5, 1.0)
    colorSteelDissolve = Vec4(0.5, 0.5, 0.5, 0.0)
    colorList = (colorRed,
     colorBlue,
     colorGreen,
     colorWhite,
     colorBlack,
     colorPurple,
     colorYellow,
     colorOrange,
     colorAqua,
     colorSteel)
    disolveList = (colorDisolveRed,
     colorDisolveBlue,
     colorDisolveGreen,
     colorDisolveWhite,
     colorDisolveBlack,
     colorDisolvePurple,
     colorDisolveYellow,
     colorDisolveOrange,
     colorDisolveAqua,
     colorSteelDissolve)

    def __init__(self, spriteBase, size, colorType = 0, foundation = 0, facing = 0):
        self.colorType = colorType
        self.spriteBase = spriteBase
        self.frame = self.spriteBase.getParent()
        self.foundation = foundation
        self.sizeMult = 1.4
        self.velX = 0
        self.velZ = 0
        self.prevX = 0
        self.prevZ = 0
        self.isActive = 0
        self.canCollide = 1
        self.accX = None
        self.accZ = None
        self.delayRemove = 0
        self.giftId = None
        self.holdType = None
        self.multiColor = 0
        self.multiColorList = [0,
         1,
         2,
         6]
        self.multiColorIndex = 0
        self.multiColorNext = 1
        self.multiColorLevel = 0.0
        self.multiColorStep = 0.025
        self.facing = facing
        self.breakable = 1
        self.deleteFlag = 0
        self.nodeObj = None
        self.inputSize = size
        myColor = GameSprite.colorWhite
        myModel = 'phase_12/models/bossbotHQ/bust_a_cog_ball_white'
        self.setBallType(colorType)
        self.size = 0.4 * self.sizeMult
        self.isQue = 0
        self.nodeObj.setTransparency(TransparencyAttrib.MAlpha)
        self.markedForDeath = 0
        self.gridPosX = None
        self.gridPosZ = None
        return

    def setBallType(self, type, solidOverride = 0):
        if not self.nodeObj or self.nodeObj.isEmpty():
            self.nodeObj = None
        else:
            self.nodeObj.remove()
        colorType = type
        self.multiColor = 0
        self.breakable = 1
        solid = self.foundation
        if solidOverride:
            solid = 1
        myColor = GameSprite.colorWhite
        myModel = 'phase_12/models/bossbotHQ/bust_a_cog_ball_white'
        if not solid or colorType > 9:
            if colorType == 0:
                myColor = GameSprite.colorGhostRed
            elif colorType == 1:
                myColor = GameSprite.colorGhostBlue
            elif colorType == 2:
                myColor = GameSprite.colorGhostGreen
            elif colorType == 3:
                myColor = GameSprite.colorWhite
            elif colorType == 4:
                myColor = GameSprite.colorBlack
            elif colorType == 5:
                myColor = GameSprite.colorPurple
            elif colorType == 6:
                myColor = GameSprite.colorYellow
            elif colorType == 7:
                myColor = GameSprite.colorOrange
                self.multiColor = 1
                self.multiColorList = [7, 4]
                self.multiColorIndex = 0
                self.multiColorNext = 1
                self.multiColorLevel = 0.0
                self.multiColorStep = 0.1
            elif colorType == 8:
                myColor = GameSprite.colorAqua
                self.multiColor = 1
                self.multiColorList = [0,
                 1,
                 2,
                 6]
                self.multiColorIndex = 0
                self.multiColorNext = 1
                self.multiColorLevel = 0.0
                self.multiColorStep = 0.025
            elif colorType == 9:
                myColor = GameSprite.colorSteel
                self.breakable = 0
            elif colorType == 10:
                myModel = 'phase_12/models/bossbotHQ/bust_a_cog_ball_fire'
                self.giftId = 7
                self.colorType = 0
            elif colorType == 11:
                myModel = 'phase_12/models/bossbotHQ/bust_a_cog_ball_unknown'
                self.giftId = 8
                self.colorType = 1
        elif colorType == 0:
            myModel = 'phase_12/models/bossbotHQ/bust_a_cog_ball_red'
        elif colorType == 1:
            myModel = 'phase_12/models/bossbotHQ/bust_a_cog_ball_blue'
        elif colorType == 2:
            myModel = 'phase_12/models/bossbotHQ/bust_a_cog_ball_green'
        elif colorType == 3:
            myModel = 'phase_12/models/bossbotHQ/bust_a_cog_ball_cog'
        elif colorType == 4:
            myColor = GameSprite.colorBlack
        elif colorType == 5:
            myModel = 'phase_12/models/bossbotHQ/bust_a_cog_ball_purple'
        elif colorType == 6:
            myModel = 'phase_12/models/bossbotHQ/bust_a_cog_ball_yello'
        elif colorType == 7:
            myColor = GameSprite.colorOrange
            self.multiColor = 1
            self.multiColorList = [7, 4]
            self.multiColorIndex = 0
            self.multiColorNext = 1
            self.multiColorLevel = 0.0
            self.multiColorStep = 0.15
        elif colorType == 8:
            myColor = GameSprite.colorAqua
            self.multiColor = 1
            self.multiColorList = [0,
             1,
             2,
             6]
            self.multiColorIndex = 0
            self.multiColorNext = 1
            self.multiColorLevel = 0.0
            self.multiColorStep = 0.1
        elif colorType == 9:
            myModel = 'phase_12/models/bossbotHQ/bust_a_cog_ball_steel'
            if not myModel:
                import pdb
                pdb.set_trace()
            self.breakable = 0
        elif colorType == 10:
            myModel = 'phase_12/models/bossbotHQ/bust_a_cog_ball_fire'
            self.giftId = 7
            self.colorType = 0
        elif colorType == 11:
            myModel = 'phase_12/models/bossbotHQ/bust_a_cog_ball_unknown'
            self.giftId = 8
            self.colorType = 1
        self.nodeObj = loader.loadModel(myModel)
        self.nodeObj.setScale(self.inputSize)
        self.nodeObj.reparentTo(self.spriteBase)
        self.setColor(myColor)
        return

    def removeDelay(self):
        self.delayRemove = 0

    def delete(self):
        if not self.delayRemove:
            self.spriteBase.removeNode()
            self.deleteFlag = 1

    def face(self):
        frameZ = self.frame.getZ()
        tilt = -95.0 + (self.getZ() + frameZ) * 2.0
        self.nodeObj.setP(-tilt)

    def runColor(self):
        if self.multiColor:
            c1 = GameSprite.colorList[self.multiColorList[self.multiColorIndex]]
            c2 = GameSprite.colorList[self.multiColorList[self.multiColorNext]]
            iLevel = 1.0 - self.multiColorLevel
            mixColor = c1 * iLevel + c2 * self.multiColorLevel
            self.nodeObj.setColorScale(mixColor)
            self.multiColorLevel += self.multiColorStep
            if self.multiColorLevel > 1.0:
                self.multiColorLevel = 0.0
                self.multiColorIndex += 1
                if self.multiColorIndex >= len(self.multiColorList):
                    self.multiColorIndex = 0
                self.multiColorNext = self.multiColorIndex + 1
                if self.multiColorNext >= len(self.multiColorList):
                    self.multiColorNext = 0

    def run(self, timeDelta):
        if self.facing:
            self.face()
        self.runColor()
        if self.isActive and not self.isQue:
            self.prevX = self.spriteBase.getX()
            self.prevZ = self.spriteBase.getZ()
            self.setX(self.getX() + self.velX * timeDelta)
            self.setZ(self.getZ() + self.velZ * timeDelta)
            self.velX = self.velX * (1 - timeDelta * 4)
            self.velZ = self.velZ * (1 - timeDelta * 4)
            if self.accX != None:
                self.velX = self.accX
                self.velZ = self.accZ
        if self.nodeObj.isEmpty():
            self.markedForDeath = 1
        return

    def reflectX(self):
        self.velX = -self.velX
        if self.accX != None:
            self.accX = -self.accX
        return

    def reflectZ(self):
        self.velZ = -self.velZ
        if self.accZ != None:
            self.accZ = -self.accZ
        return

    def warningBump(self):
        num1 = random.random() * 2.0
        num2 = random.random() * 2.0
        num3 = random.random() * 2.0
        curr = self.nodeObj.getPos()
        dest = Point3(0 + curr[0], 0 + curr[1], 1.0 + curr[2])
        track = Sequence(Wait(num1 * 0.1), LerpPosInterval(self.nodeObj, num2 * 0.1, Point3(0.0, 0.0, 0.5)), LerpPosInterval(self.nodeObj, num3 * 0.1, Point3(0.0, 0.0, 0.0)), LerpPosInterval(self.nodeObj, num2 * 0.1, Point3(0.0, 0.0, 0.5)), LerpPosInterval(self.nodeObj, num1 * 0.1, Point3(0.0, 0.0, 0.0)))
        track.start()

    def shake(self):
        num1 = random.random() * 1.0
        num2 = random.random() * 1.0
        curr = self.nodeObj.getPos()
        dest = Point3(0 + curr[0], 0 + curr[1], 1.0 + curr[2])
        track = Sequence(LerpPosInterval(self.nodeObj, num2 * 0.1, Point3(0.0, 0.0, 0.25)), LerpPosInterval(self.nodeObj, num1 * 0.1, Point3(0.0, 0.0, 0.0)))
        track.start()

    def deathEffect(self):
        if self.spriteBase.isEmpty():
            return
        self.spriteBase.wrtReparentTo(render)
        num1 = (random.random() - 0.5) * 1.0
        num2 = random.random() * 1.0
        num3 = random.random() * 1.0
        notNum3 = 1.0 - num3
        curr = self.spriteBase.getPos()
        self.delayRemove = 1
        self.canCollide = 0
        track = Sequence(Parallel(ProjectileInterval(self.spriteBase, startVel=Vec3(-20.0 + notNum3 * 40.0, -20.0 + num3 * 40.0, 30), duration=0.5 + num2 * 1.0, gravityMult=2.0), LerpColorScaleInterval(self.spriteBase, duration=0.5 + num2 * 1.0, startColorScale=GameSprite.colorList[self.colorType], colorScale=GameSprite.disolveList[self.colorType])), Func(self.removeDelay), Func(self.delete))
        track.start()

    def wildEffect(self):
        if self.spriteBase.isEmpty():
            return
        num1 = (random.random() - 0.5) * 1.0
        num2 = random.random() * 1.0
        num3 = random.random() * 1.0
        notNum3 = 1.0 - num3
        curr = self.spriteBase.getPos()
        self.delayRemove = 1
        self.canCollide = 0
        track = Sequence(Parallel(LerpScaleInterval(self.spriteBase, 1.0, 1.5, startScale=1.0), LerpColorScaleInterval(self.spriteBase, duration=1.0, startColorScale=GameSprite.colorList[self.colorType], colorScale=Vec4(0, 0, 0, 0.0))), Func(self.removeDelay), Func(self.delete))
        track.start()

    def setActive(self, active):
        if active:
            self.isActive = 1
        else:
            self.isActive = 0
            self.velX = 0
            self.velZ = 0
            self.accX = None
            self.accZ = None
        return

    def getX(self):
        if self.nodeObj.isEmpty():
            return None
        return self.spriteBase.getX()

    def getZ(self):
        if self.nodeObj.isEmpty():
            return None
        return self.spriteBase.getZ()

    def setX(self, x):
        if self.nodeObj.isEmpty():
            return None
        self.prevX = self.spriteBase.getX()
        self.spriteBase.setX(x)
        return None

    def setZ(self, z):
        if self.nodeObj.isEmpty():
            return None
        self.prevZ = self.spriteBase.getZ()
        self.spriteBase.setZ(z)
        return None

    def addForce(self, force, direction):
        if self.isActive:
            forceX = math.cos(direction) * force
            forceZ = math.sin(direction) * force
            self.velX += forceX
            self.velZ += forceZ

    def setAccel(self, accel, direction):
        accelX = math.cos(direction) * accel
        accelZ = math.sin(direction) * accel
        self.accX = accelX
        self.accZ = accelZ

    def setColorType(self, typeIndex):
        self.colorType = typeIndex
        self.setColor(GameSprite.colorList[typeIndex])

    def setColor(self, trip):
        self.nodeObj.setColorScale(trip[0], trip[1], trip[2], trip[3])

    def collide(self):
        if self.isActive:
            self.setX(self.prevX)
            self.setZ(self.prevZ)
