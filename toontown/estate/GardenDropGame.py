from pandac.PandaModules import *
from toontown.toonbase.ToonBaseGlobal import *
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from direct.gui.DirectScrolledList import *
from direct.distributed.ClockDelta import *
from toontown.toontowngui import TTDialog
import math
from direct.task.Task import Task
from toontown.toonbase import ToontownGlobals
from direct.distributed import DistributedObject
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM
from direct.fsm import State
from toontown.toon import Toon
from direct.showbase import RandomNumGen
from toontown.toonbase import TTLocalizer
import random
import random
import cPickle
from direct.showbase import PythonUtil
import GameSprite
from math import pi
import GardenProgressMeter

class GardenDropGame(DirectObject.DirectObject):

    def __init__(self):
        self.acceptErrorDialog = None
        self.doneEvent = 'game Done'
        self.sprites = []
        self.load()
        thing = self.model.find('**/item_board')
        self.block = self.model1.find('**/minnieCircle')
        self.colorRed = (1, 0, 0, 1)
        self.colorBlue = (0, 0, 1, 1)
        self.colorGreen = (0, 1, 0, 1)
        self.colorGhostRed = (1, 0, 0, 0.5)
        self.colorGhostBlue = (0, 0, 1, 0.5)
        self.colorGhostGreen = (0, 1, 0, 0.5)
        self.colorWhite = (1, 1, 1, 1)
        self.colorBlack = (0, 0, 0, 1.0)
        self.colorShadow = (0, 0, 0, 0.5)
        self.lastTime = None
        self.running = 0
        self.massCount = 0
        self.foundCount = 0
        self.maxX = 0.47
        self.minX = -0.47
        self.maxZ = 0.65
        self.minZ = -0.1
        self.newBallX = 0.0
        self.newBallZ = 0.6
        self.rangeX = self.maxX - self.minX
        self.rangeZ = self.maxZ - self.minZ
        size = 0.085
        sizeZ = size * 0.8
        gX = int(self.rangeX / size)
        gZ = int(self.rangeZ / sizeZ)
        self.maxX = self.minX + gX * size
        self.maxZ = self.minZ + gZ * sizeZ
        self.controlOffsetX = 0.0
        self.controlOffsetZ = 0.0
        self.queExtent = 3
        print 'Grid Dimensions X%s Z%s' % (gX, gZ)
        self.grid = []
        self.gridDimX = gX
        self.gridDimZ = gZ
        self.gridBrick = False
        base.gardenGame = self
        for countX in range(self.gridDimX):
            newRow = []
            for countZ in range(self.gridDimZ):
                offset = 0
                if countZ % 2 == 0:
                    offset = size / 2
                newRow.append([None, countX * size + self.minX + offset, countZ * sizeZ + self.minZ])

            self.grid.append(newRow)

        self.controlSprite = None
        self.cogSprite = self.addUnSprite(self.block, posX=0.25, posZ=0.5)
        self.cogSprite.setColor(self.colorShadow)
        for ball in range(0, 3):
            place = random.random() * self.rangeX
            newSprite = self.addSprite(self.block, size=0.5, posX=self.minX + place, posZ=0.0, found=1)
            self.stickInGrid(newSprite, 1)

        self.queBall = self.addSprite(self.block, posX=0.25, posZ=0.5, found=0)
        self.queBall.setColor(self.colorWhite)
        self.queBall.isQue = 1
        self.matchList = []
        self.newBallTime = 1.0
        self.newBallCountUp = 0.0
        self.cogX = 0
        self.cogZ = 0
        self.__run()
        return

    def findGrid(self, x, z, force = 0):
        currentClosest = None
        currentDist = 10000000
        for countX in range(self.gridDimX):
            for countZ in range(self.gridDimZ):
                testDist = self.testPointDistanceSquare(x, z, self.grid[countX][countZ][1], self.grid[countX][countZ][2])
                if self.grid[countX][countZ][0] == None and testDist < currentDist and (force or self.hasNeighbor(countX, countZ)):
                    currentClosest = self.grid[countX][countZ]
                    self.closestX = countX
                    self.closestZ = countZ
                    currentDist = testDist

        return currentClosest

    def hasNeighbor(self, cellX, cellZ):
        gotNeighbor = 0
        if cellZ % 2 == 0:
            if self.testGridfull(self.getValidGrid(cellX - 1, cellZ)):
                gotNeighbor = 1
            elif self.testGridfull(self.getValidGrid(cellX + 1, cellZ)):
                gotNeighbor = 1
            elif self.testGridfull(self.getValidGrid(cellX, cellZ + 1)):
                gotNeighbor = 1
            elif self.testGridfull(self.getValidGrid(cellX + 1, cellZ + 1)):
                gotNeighbor = 1
            elif self.testGridfull(self.getValidGrid(cellX, cellZ - 1)):
                gotNeighbor = 1
            elif self.testGridfull(self.getValidGrid(cellX + 1, cellZ - 1)):
                gotNeighbor = 1
        elif self.testGridfull(self.getValidGrid(cellX - 1, cellZ)):
            gotNeighbor = 1
        elif self.testGridfull(self.getValidGrid(cellX + 1, cellZ)):
            gotNeighbor = 1
        elif self.testGridfull(self.getValidGrid(cellX, cellZ + 1)):
            gotNeighbor = 1
        elif self.testGridfull(self.getValidGrid(cellX - 1, cellZ + 1)):
            gotNeighbor = 1
        elif self.testGridfull(self.getValidGrid(cellX, cellZ - 1)):
            gotNeighbor = 1
        elif self.testGridfull(self.getValidGrid(cellX - 1, cellZ - 1)):
            gotNeighbor = 1
        return gotNeighbor

    def clearMatchList(self):
        for entry in self.matchList:
            gridEntry = self.grid[entry[0]][entry[1]]
            sprite = gridEntry[0]
            gridEntry[0] = None
            sprite.markedForDeath = 1

        return

    def createMatchList(self, x, z):
        self.matchList = []
        self.fillMatchList(x, z)

    def fillMatchList(self, cellX, cellZ):
        if (cellX, cellZ) in self.matchList:
            return
        self.matchList.append((cellX, cellZ))
        colorType = self.grid[cellX][cellZ][0].colorType
        if cellZ % 2 == 0:
            if self.getColorType(cellX - 1, cellZ) == colorType:
                self.fillMatchList(cellX - 1, cellZ)
            if self.getColorType(cellX + 1, cellZ) == colorType:
                self.fillMatchList(cellX + 1, cellZ)
            if self.getColorType(cellX, cellZ + 1) == colorType:
                self.fillMatchList(cellX, cellZ + 1)
            if self.getColorType(cellX + 1, cellZ + 1) == colorType:
                self.fillMatchList(cellX + 1, cellZ + 1)
            if self.getColorType(cellX, cellZ - 1) == colorType:
                self.fillMatchList(cellX, cellZ - 1)
            if self.getColorType(cellX + 1, cellZ - 1) == colorType:
                self.fillMatchList(cellX + 1, cellZ - 1)
        else:
            if self.getColorType(cellX - 1, cellZ) == colorType:
                self.fillMatchList(cellX - 1, cellZ)
            if self.getColorType(cellX + 1, cellZ) == colorType:
                self.fillMatchList(cellX + 1, cellZ)
            if self.getColorType(cellX, cellZ + 1) == colorType:
                self.fillMatchList(cellX, cellZ + 1)
            if self.getColorType(cellX - 1, cellZ + 1) == colorType:
                self.fillMatchList(cellX - 1, cellZ + 1)
            if self.getColorType(cellX, cellZ - 1) == colorType:
                self.fillMatchList(cellX, cellZ - 1)
            if self.getColorType(cellX - 1, cellZ - 1) == colorType:
                self.fillMatchList(cellX - 1, cellZ - 1)

    def testGridfull(self, cell):
        if not cell:
            return 0
        elif cell[0] != None:
            return 1
        else:
            return 0
        return

    def getValidGrid(self, x, z):
        if x < 0 or x >= self.gridDimX:
            return None
        elif z < 0 or z >= self.gridDimZ:
            return None
        else:
            return self.grid[x][z]
        return None

    def getColorType(self, x, z):
        if x < 0 or x >= self.gridDimX:
            return -1
        elif z < 0 or z >= self.gridDimZ:
            return -1
        elif self.grid[x][z][0] == None:
            return -1
        else:
            return self.grid[x][z][0].colorType
        return

    def findGridCog(self):
        self.cogX = 0
        self.cogZ = 0
        self.massCount = 0
        for row in self.grid:
            for cell in row:
                if cell[0] != None:
                    self.cogX += cell[1]
                    self.cogZ += cell[2]
                    self.massCount += 1

        if self.massCount > 0:
            self.cogX = self.cogX / self.massCount
            self.cogZ = self.cogZ / self.massCount
            self.cogSprite.setX(self.cogX)
            self.cogSprite.setZ(self.cogZ)
        else:
            self.doOnClearGrid()
        return

    def doOnClearGrid(self):
        secondSprite = self.addSprite(self.block, posX=self.newBallX, posZ=0.0, found=1)
        secondSprite.addForce(0, 1.55 * pi)
        self.stickInGrid(secondSprite, 1)

    def findGrid2(self, x, z):
        rangeX = self.maxX - self.minX
        rangeZ = self.maxZ - self.minZ
        framedX = x - self.minX
        framedZ = z - self.minZ
        tileDimX = rangeX / self.gridDimX
        tileDimZ = rangeZ / self.gridDimZ
        tileX = int(framedX / tileDimX)
        tileZ = int(framedZ / tileDimZ)
        print 'find Grid tileX%s tileZ%s' % (tileX, tileZ)
        return (tileX, tileZ)

    def findPos(self, x, z):
        rangeX = self.maxX - self.minX
        rangeZ = self.maxZ - self.minZ
        tileDimX = rangeX / self.gridDimX
        tileDimZ = rangeZ / self.gridDimZ
        posX = tileDimX * x + self.minX
        posZ = tileDimZ * z + self.minZ
        print 'find Pos X%s Z%s' % (posX, posZ)
        return (posX, posZ)

    def placeIntoGrid(self, sprite, x, z):
        if self.grid[x][z][0] == None:
            self.grid[x][z][0] = sprite
            sprite.setActive(0)
            newX, newZ = self.findPos(x, z)
            sprite.setX(newX)
            sprite.setZ(newZ)
            print 'Setting Final Pos X%s Z%s' % (newX, newZ)
        else:
            self.placeIntoGrid(sprite, x + 1, z - 1)
        return

    def stickInGrid(self, sprite, force = 0):
        if sprite.isActive and not sprite.isQue:
            gridCell = self.findGrid(sprite.getX(), sprite.getZ(), force)
            if gridCell:
                gridCell[0] = sprite
                sprite.setActive(0)
                sprite.setX(gridCell[1])
                sprite.setZ(gridCell[2])
                self.createMatchList(self.closestX, self.closestZ)
                if len(self.matchList) >= 3:
                    self.clearMatchList()
                self.findGridCog()

    def stickInGrid2(self, sprite):
        if sprite.isActive and not sprite.isQue:
            tileX, tileZ = self.findGrid(sprite.getX(), sprite.getZ())
            self.placeIntoGrid(sprite, tileX, tileZ)
            sprite.isActive = 0

    def load(self):
        model = loader.loadModel('phase_5.5/models/gui/package_delivery_panel')
        model1 = loader.loadModel('phase_3.5/models/gui/matching_game_gui')
        self.model = model
        self.model1 = model1
        background = model.find('**/bg')
        itemBoard = model.find('**/item_board')
        self.frame = DirectFrame(scale=1.1, relief=DGG.FLAT, frameSize=(-0.5,
         0.5,
         -0.45,
         -0.05), frameColor=(0.737, 0.573, 0.345, 1.0))
        self.background = DirectFrame(self.frame, image=background, image_scale=0.05, relief=None, pos=(0, 1, 0))
        self.itemBoard = DirectFrame(parent=self.frame, image=itemBoard, image_scale=0.05, image_color=(0.922, 0.922, 0.753, 1), relief=None, pos=(0, 1, 0))
        gui2 = loader.loadModel('phase_3/models/gui/quit_button')
        self.quitButton = DirectButton(parent=self.frame, relief=None, image=(gui2.find('**/QuitBtn_UP'), gui2.find('**/QuitBtn_DN'), gui2.find('**/QuitBtn_RLVR')), pos=(0.5, 1.0, -0.42), scale=0.9, text='Exit Mini Game', text_font=ToontownGlobals.getSignFont(), text0_fg=(1, 1, 1, 1), text1_fg=(1, 1, 1, 1), text2_fg=(1, 1, 1, 1), text_scale=0.045, text_pos=(0, -0.01), command=self.__handleExit)
        return

    def unload(self):
        self.frame.destroy()
        del self.frame
        if self.acceptErrorDialog:
            self.acceptErrorDialog.cleanup()
            self.acceptErrorDialog = None
        taskMgr.remove('gameTask')
        self.ignoreAll()
        return

    def show(self):
        self.frame.show()

    def hide(self):
        self.frame.hide()

    def __handleExit(self):
        self.__acceptExit()

    def __acceptExit(self, buttonValue = None):
        if hasattr(self, 'frame'):
            self.hide()
            self.unload()
            messenger.send(self.doneEvent)

    def addSprite(self, image, size = 0.5, posX = 0, posZ = 0, found = 0):
        nodeObj = DirectLabel(parent=self.frame, relief=None, image=image, pos=(posX, 0.0, posZ), scale=size, image_color=(1.0, 1.0, 1.0, 1))
        colorChoice = random.choice(range(0, 3))
        newSprite = GameSprite.GameSprite(nodeObj, colorChoice, found)
        self.sprites.append(newSprite)
        if found:
            self.foundCount += 1
        return newSprite

    def addUnSprite(self, image, size = 0.5, posX = 0, posZ = 0):
        nodeObj = DirectLabel(parent=self.frame, relief=None, image=image, pos=(posX, 0.0, posZ), scale=size, image_color=(1.0, 1.0, 1.0, 1))
        newSprite = GameSprite.GameSprite(nodeObj)
        newSprite = GameSprite.GameSprite(nodeObj)
        return newSprite

    def __run(self, cont = 1):
        if self.lastTime == None:
            self.lastTime = globalClock.getRealTime()
        timeDelta = globalClock.getRealTime() - self.lastTime
        self.lastTime = globalClock.getRealTime()
        self.newBallCountUp += timeDelta
        if base.mouseWatcherNode.hasMouse():
            x = base.mouseWatcherNode.getMouseX()
            y = base.mouseWatcherNode.getMouseY()
            self.queBall.setX(x)
            self.queBall.setZ(y)
        for sprite in self.sprites:
            sprite.run(timeDelta)
            if sprite.getX() > self.maxX:
                sprite.setX(self.maxX)
                sprite.velX = -sprite.velX
            if sprite.getX() < self.minX:
                sprite.setX(self.minX)
                sprite.velX = -sprite.velX
            if sprite.getZ() > self.maxZ:
                sprite.setZ(self.maxZ)
                sprite.velZ = -sprite.velZ
            if sprite.getZ() < self.minZ:
                self.stickInGrid(sprite, 1)
            if sprite.isActive:
                sprite.addForce(timeDelta * 0.9, pi * 1.5)

        self.queBall.velX = (self.queBall.getX() - self.queBall.prevX) / timeDelta
        self.queBall.velZ = (self.queBall.getZ() - self.queBall.prevZ) / timeDelta
        self.__colTest()
        for sprite in self.sprites:
            if sprite.markedForDeath:
                if sprite.foundation:
                    self.foundCount -= 1
                self.sprites.remove(sprite)
                sprite.delete()

        if self.controlSprite == None:
            self.addControlSprite(self.newBallX, self.newBallZ)
            self.newBallCountUp = 0.0
        if self.newBallCountUp >= self.newBallTime:
            self.addControlSprite(self.newBallX, self.newBallZ)
            self.newBallCountUp = 0.0
        if not self.controlSprite.isActive:
            self.controlSprite = None
        if self.foundCount <= 0:
            self.__handleWin()
        if cont and not self.running:
            taskMgr.add(self.__run, 'gameTask')
            self.running = 1
        return Task.cont

    def __handleWin(self):
        GardenProgressMeter.GardenProgressMeter()
        self.__handleExit()

    def addControlSprite(self, x = 0.0, z = 0.0):
        newSprite = self.addSprite(self.block, posX=x, posZ=z)
        self.controlSprite = newSprite

    def __colTest(self):
        if not hasattr(self, 'tick'):
            self.tick = 0
        self.tick += 1
        if self.tick > 5:
            self.tick = 0
        sizeSprites = len(self.sprites)
        for movingSpriteIndex in range(len(self.sprites)):
            for testSpriteIndex in range(movingSpriteIndex, len(self.sprites)):
                movingSprite = self.getSprite(movingSpriteIndex)
                testSprite = self.getSprite(testSpriteIndex)
                if testSprite and movingSprite:
                    if movingSpriteIndex != testSpriteIndex and (movingSprite.isActive or testSprite.isActive):
                        if movingSprite.isQue or testSprite.isQue:
                            if self.testDistance(movingSprite.nodeObj, testSprite.nodeObj) < self.queExtent * (movingSprite.size + testSprite.size):
                                self.push(movingSprite, testSprite)
                        elif self.testDistance(movingSprite.nodeObj, testSprite.nodeObj) < movingSprite.size + testSprite.size:
                            if not (movingSprite.isActive and testSprite.isActive):
                                self.__collide(movingSprite, testSprite)
                        if self.tick == 5:
                            pass

    def getSprite(self, spriteIndex):
        if spriteIndex >= len(self.sprites) or self.sprites[spriteIndex].markedForDeath:
            return None
        else:
            return self.sprites[spriteIndex]
        return None

    def testDistance(self, nodeA, nodeB):
        distX = nodeA.getX() - nodeB.getX()
        distZ = nodeA.getZ() - nodeB.getZ()
        distC = distX * distX + distZ * distZ
        dist = math.sqrt(distC)
        return dist

    def testPointDistance(self, x1, z1, x2, z2):
        distX = x1 - x2
        distZ = z1 - z2
        distC = distX * distX + distZ * distZ
        dist = math.sqrt(distC)
        if dist == 0:
            dist = 1e-10
        return dist

    def testPointDistanceSquare(self, x1, z1, x2, z2):
        distX = x1 - x2
        distZ = z1 - z2
        distC = distX * distX + distZ * distZ
        if distC == 0:
            distC = 1e-10
        return distC

    def angleTwoSprites(self, sprite1, sprite2):
        x1 = sprite1.getX()
        z1 = sprite1.getZ()
        x2 = sprite2.getX()
        z2 = sprite2.getZ()
        x = x2 - x1
        z = z2 - z1
        angle = math.atan2(-x, z)
        return angle + pi * 0.5

    def angleTwoPoints(self, x1, z1, x2, z2):
        x = x2 - x1
        z = z2 - z1
        angle = math.atan2(-x, z)
        return angle + pi * 0.5

    def __collide(self, move, test):
        queHit = 0
        if move.isQue:
            que = move
            hit = test
            queHit = 1
        elif test.isQue:
            que = test
            hit = move
            queHit = 1
        else:
            test.velX = 0
            test.velZ = 0
            move.velX = 0
            move.velZ = 0
            test.collide()
            move.collide()
            self.stickInGrid(move)
            self.stickInGrid(test)
        if queHit:
            forceM = 0.1
            distX = que.getX() - hit.getX()
            distZ = que.getZ() - hit.getZ()

    def push(self, move, test):
        queHit = 0
        if move.isQue:
            que = move
            hit = test
            queHit = 1
        elif test.isQue:
            que = test
            hit = move
            queHit = 1
        if queHit:
            forceM = 0.1
            dist = self.testDistance(move.nodeObj, test.nodeObj)
            if abs(dist) < self.queExtent * que.size and abs(dist) > 0:
                scaleSize = self.queExtent * que.size * 0.5
                distFromPara = abs(abs(dist) - scaleSize)
                force = (scaleSize - distFromPara) / scaleSize * (dist / abs(dist))
                angle = self.angleTwoSprites(que, hit)
                if angle < 0:
                    angle = angle + 2 * pi
                if angle > pi * 2.0:
                    angle = angle - 2 * pi
                newAngle = pi * 1.0
                if angle > pi * 1.5 or angle < pi * 0.5:
                    newAngle = pi * 0.0
                hit.addForce(forceM * force, newAngle)
