import math

class GameSprite:
    colorRed = (1, 0, 0, 1)
    colorBlue = (0, 0, 1, 1)
    colorGreen = (0, 1, 0, 1)
    colorGhostRed = (1, 0, 0, 0.5)
    colorGhostBlue = (0, 0, 1, 0.5)
    colorGhostGreen = (0, 1, 0, 0.5)
    colorWhite = (1, 1, 1, 1)
    colorBlack = (0, 0, 0, 1.0)
    colorShadow = (0, 0, 0, 0.5)

    def __init__(self, nodeObj, colorType = 0, foundation = 0):
        self.nodeObj = nodeObj
        self.foundation = foundation
        self.velX = 0
        self.velZ = 0
        self.prevX = 0
        self.prevZ = 0
        self.isActive = 1
        self.size = 0.04
        self.isQue = 0
        self.colorType = colorType
        if not foundation:
            if colorType == 0:
                self.setColor(GameSprite.colorGhostRed)
            elif colorType == 1:
                self.setColor(GameSprite.colorGhostBlue)
            elif colorType == 2:
                self.setColor(GameSprite.colorGhostGreen)
        elif colorType == 0:
            self.setColor(GameSprite.colorRed)
        elif colorType == 1:
            self.setColor(GameSprite.colorBlue)
        elif colorType == 2:
            self.setColor(GameSprite.colorGreen)
        self.markedForDeath = 0

    def delete(self):
        self.nodeObj.destroy()

    def run(self, timeDelta):
        if self.isActive and not self.isQue:
            self.prevX = self.nodeObj.getX()
            self.prevZ = self.nodeObj.getZ()
            self.setX(self.getX() + self.velX * timeDelta)
            self.setZ(self.getZ() + self.velZ * timeDelta)
            self.velX = self.velX * (1 - timeDelta * 4)
            self.velZ = self.velZ * (1 - timeDelta * 4)

    def setActive(self, active):
        if active:
            self.isActive = 1
        else:
            self.isActive = 0
            self.velX = 0
            self.velZ = 0

    def getX(self):
        return self.nodeObj.getX()

    def getZ(self):
        return self.nodeObj.getZ()

    def setX(self, x):
        self.prevX = self.nodeObj.getX()
        self.nodeObj.setX(x)

    def setZ(self, z):
        self.prevZ = self.nodeObj.getZ()
        self.nodeObj.setZ(z)

    def addForce(self, force, direction):
        if self.isActive:
            forceX = math.cos(direction) * force
            forceZ = math.sin(direction) * force
            self.velX += forceX
            self.velZ += forceZ

    def setColor(self, trip):
        self.nodeObj.setColorScale(trip[0], trip[1], trip[2], trip[3])

    def collide(self):
        if self.isActive:
            self.setX(self.prevX)
            self.setZ(self.prevZ)
