from direct.showbase.DirectObject import DirectObject
from direct.interval.MetaInterval import Parallel
from direct.interval.LerpInterval import LerpPosInterval, LerpHprInterval
from direct.showbase.RandomNumGen import RandomNumGen
from pandac.PandaModules import Point3, WaitInterval
from pandac.PandaModules import CollisionSphere, CollisionNode
from toontown.suit import Suit
from toontown.suit import SuitDNA
from toontown.toonbase import ToontownGlobals
import MazeGameGlobals

class MazeSuit(DirectObject):
    COLL_SPHERE_NAME = 'MazeSuitSphere'
    COLLISION_EVENT_NAME = 'MazeSuitCollision'
    MOVE_IVAL_NAME = 'moveMazeSuit'
    DIR_UP = 0
    DIR_DOWN = 1
    DIR_LEFT = 2
    DIR_RIGHT = 3
    oppositeDirections = [DIR_DOWN,
     DIR_UP,
     DIR_RIGHT,
     DIR_LEFT]
    directionHs = [0,
     180,
     90,
     270]
    DEFAULT_SPEED = 4.0
    SUIT_Z = 0.1

    def __init__(self, serialNum, maze, randomNumGen, cellWalkPeriod, difficulty, suitDnaName = 'f', startTile = None, ticFreq = MazeGameGlobals.SUIT_TIC_FREQ, walkSameDirectionProb = MazeGameGlobals.WALK_SAME_DIRECTION_PROB, walkTurnAroundProb = MazeGameGlobals.WALK_TURN_AROUND_PROB, uniqueRandomNumGen = True, walkAnimName = None):
        self.serialNum = serialNum
        self.maze = maze
        if uniqueRandomNumGen:
            self.rng = RandomNumGen(randomNumGen)
        else:
            self.rng = randomNumGen
        self.difficulty = difficulty
        self._walkSameDirectionProb = walkSameDirectionProb
        self._walkTurnAroundProb = walkTurnAroundProb
        self._walkAnimName = walkAnimName or 'walk'
        self.suit = Suit.Suit()
        d = SuitDNA.SuitDNA()
        d.newSuit(suitDnaName)
        self.suit.setDNA(d)
        if startTile is None:
            defaultStartPos = MazeGameGlobals.SUIT_START_POSITIONS[self.serialNum]
            self.startTile = (defaultStartPos[0] * self.maze.width, defaultStartPos[1] * self.maze.height)
        else:
            self.startTile = startTile
        self.ticFreq = ticFreq
        self.ticPeriod = int(cellWalkPeriod)
        self.cellWalkDuration = float(self.ticPeriod) / float(self.ticFreq)
        self.turnDuration = 0.6 * self.cellWalkDuration
        return

    def destroy(self):
        self.suit.delete()

    def uniqueName(self, str):
        return str + `(self.serialNum)`

    def gameStart(self, gameStartTime):
        self.gameStartTime = gameStartTime
        self.initCollisions()
        self.startWalkAnim()
        self.occupiedTiles = [(self.nextTX, self.nextTY)]
        n = 20
        self.nextThinkTic = self.serialNum * self.ticFreq / n
        self.fromPos = Point3(0, 0, 0)
        self.toPos = Point3(0, 0, 0)
        self.fromHpr = Point3(0, 0, 0)
        self.toHpr = Point3(0, 0, 0)
        self.moveIval = WaitInterval(1.0)

    def gameEnd(self):
        self.moveIval.pause()
        del self.moveIval
        self.shutdownCollisions()
        self.suit.loop('neutral')

    def initCollisions(self):
        self.collSphere = CollisionSphere(0, 0, 0, 2.0)
        self.collSphere.setTangible(0)
        self.collNode = CollisionNode(self.uniqueName(self.COLL_SPHERE_NAME))
        self.collNode.setIntoCollideMask(ToontownGlobals.WallBitmask)
        self.collNode.addSolid(self.collSphere)
        self.collNodePath = self.suit.attachNewNode(self.collNode)
        self.collNodePath.hide()
        self.accept(self.uniqueName('enter' + self.COLL_SPHERE_NAME), self.handleEnterSphere)

    def shutdownCollisions(self):
        self.ignore(self.uniqueName('enter' + self.COLL_SPHERE_NAME))
        del self.collSphere
        self.collNodePath.removeNode()
        del self.collNodePath
        del self.collNode

    def handleEnterSphere(self, collEntry):
        messenger.send(self.COLLISION_EVENT_NAME, [self.serialNum])

    def __getWorldPos(self, sTX, sTY):
        wx, wy = self.maze.tile2world(sTX, sTY)
        return Point3(wx, wy, self.SUIT_Z)

    def onstage(self):
        sTX = int(self.startTile[0])
        sTY = int(self.startTile[1])
        c = 0
        lim = 0
        toggle = 0
        direction = 0
        while not self.maze.isWalkable(sTX, sTY):
            if 0 == direction:
                sTX -= 1
            elif 1 == direction:
                sTY -= 1
            elif 2 == direction:
                sTX += 1
            elif 3 == direction:
                sTY += 1
            c += 1
            if c > lim:
                c = 0
                direction = (direction + 1) % 4
                toggle += 1
                if not toggle & 1:
                    lim += 1

        self.TX = sTX
        self.TY = sTY
        self.direction = self.DIR_DOWN
        self.lastDirection = self.direction
        self.nextTX = self.TX
        self.nextTY = self.TY
        self.suit.setPos(self.__getWorldPos(self.TX, self.TY))
        self.suit.setHpr(self.directionHs[self.direction], 0, 0)
        self.suit.reparentTo(render)
        self.suit.pose(self._walkAnimName, 0)
        self.suit.loop('neutral')

    def offstage(self):
        self.suit.reparentTo(hidden)

    def startWalkAnim(self):
        self.suit.loop(self._walkAnimName)
        speed = float(self.maze.cellWidth) / self.cellWalkDuration
        self.suit.setPlayRate(speed / self.DEFAULT_SPEED, self._walkAnimName)

    def __applyDirection(self, dir, TX, TY):
        if self.DIR_UP == dir:
            TY += 1
        elif self.DIR_DOWN == dir:
            TY -= 1
        elif self.DIR_LEFT == dir:
            TX -= 1
        elif self.DIR_RIGHT == dir:
            TX += 1
        return (TX, TY)

    def __chooseNewWalkDirection(self, unwalkables):
        if not self.rng.randrange(self._walkSameDirectionProb):
            newTX, newTY = self.__applyDirection(self.direction, self.TX, self.TY)
            if self.maze.isWalkable(newTX, newTY, unwalkables):
                return self.direction
        if self.difficulty >= 0.5:
            if not self.rng.randrange(self._walkTurnAroundProb):
                oppositeDir = self.oppositeDirections[self.direction]
                newTX, newTY = self.__applyDirection(oppositeDir, self.TX, self.TY)
                if self.maze.isWalkable(newTX, newTY, unwalkables):
                    return oppositeDir
        candidateDirs = [self.DIR_UP,
         self.DIR_DOWN,
         self.DIR_LEFT,
         self.DIR_RIGHT]
        candidateDirs.remove(self.oppositeDirections[self.direction])
        while len(candidateDirs):
            dir = self.rng.choice(candidateDirs)
            newTX, newTY = self.__applyDirection(dir, self.TX, self.TY)
            if self.maze.isWalkable(newTX, newTY, unwalkables):
                return dir
            candidateDirs.remove(dir)

        return self.oppositeDirections[self.direction]

    def getThinkTimestampTics(self, curTic):
        if curTic < self.nextThinkTic:
            return []
        else:
            r = range(self.nextThinkTic, curTic + 1, self.ticPeriod)
            self.lastTicBeforeRender = r[-1]
            return r

    def prepareToThink(self):
        self.occupiedTiles = [(self.nextTX, self.nextTY)]

    def think(self, curTic, curT, unwalkables):
        self.TX = self.nextTX
        self.TY = self.nextTY
        self.lastDirection = self.direction
        self.direction = self.__chooseNewWalkDirection(unwalkables)
        self.nextTX, self.nextTY = self.__applyDirection(self.direction, self.TX, self.TY)
        self.occupiedTiles = [(self.TX, self.TY), (self.nextTX, self.nextTY)]
        if curTic == self.lastTicBeforeRender:
            fromCoords = self.maze.tile2world(self.TX, self.TY)
            toCoords = self.maze.tile2world(self.nextTX, self.nextTY)
            self.fromPos.set(fromCoords[0], fromCoords[1], self.SUIT_Z)
            self.toPos.set(toCoords[0], toCoords[1], self.SUIT_Z)
            self.moveIval = LerpPosInterval(self.suit, self.cellWalkDuration, self.toPos, startPos=self.fromPos, name=self.uniqueName(self.MOVE_IVAL_NAME))
            if self.direction != self.lastDirection:
                self.fromH = self.directionHs[self.lastDirection]
                toH = self.directionHs[self.direction]
                if self.fromH == 270 and toH == 0:
                    self.fromH = -90
                elif self.fromH == 0 and toH == 270:
                    self.fromH = 360
                self.fromHpr.set(self.fromH, 0, 0)
                self.toHpr.set(toH, 0, 0)
                turnIval = LerpHprInterval(self.suit, self.turnDuration, self.toHpr, startHpr=self.fromHpr, name=self.uniqueName('turnMazeSuit'))
                self.moveIval = Parallel(self.moveIval, turnIval, name=self.uniqueName(self.MOVE_IVAL_NAME))
            else:
                self.suit.setH(self.directionHs[self.direction])
            moveStartT = float(self.nextThinkTic) / float(self.ticFreq)
            self.moveIval.start(curT - (moveStartT + self.gameStartTime))
        self.nextThinkTic += self.ticPeriod

    @staticmethod
    def thinkSuits(suitList, startTime, ticFreq = MazeGameGlobals.SUIT_TIC_FREQ):
        curT = globalClock.getFrameTime() - startTime
        curTic = int(curT * float(ticFreq))
        suitUpdates = []
        for i in xrange(len(suitList)):
            updateTics = suitList[i].getThinkTimestampTics(curTic)
            suitUpdates.extend(zip(updateTics, [i] * len(updateTics)))

        suitUpdates.sort(lambda a, b: a[0] - b[0])
        if len(suitUpdates) > 0:
            curTic = 0
            for i in xrange(len(suitUpdates)):
                update = suitUpdates[i]
                tic = update[0]
                suitIndex = update[1]
                suit = suitList[suitIndex]
                if tic > curTic:
                    curTic = tic
                    j = i + 1
                    while j < len(suitUpdates):
                        if suitUpdates[j][0] > tic:
                            break
                        suitList[suitUpdates[j][1]].prepareToThink()
                        j += 1

                unwalkables = []
                for si in xrange(suitIndex):
                    unwalkables.extend(suitList[si].occupiedTiles)

                for si in xrange(suitIndex + 1, len(suitList)):
                    unwalkables.extend(suitList[si].occupiedTiles)

                suit.think(curTic, curT, unwalkables)
