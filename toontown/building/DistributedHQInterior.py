from toontown.toonbase.ToonBaseGlobal import *
from pandac.PandaModules import *
from panda3d.toontown import *
from toontown.toonbase.ToontownGlobals import *
import random
from direct.task.Task import Task
from direct.distributed import DistributedObject
from direct.directnotify import DirectNotifyGlobal
from . import ToonInteriorColors
import pickle
from toontown.toonbase import TTLocalizer

class DistributedHQInterior(DistributedObject.DistributedObject):

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        self.dnaStore = cr.playGame.dnaStore
        self.leaderAvIds = []
        self.leaderNames = []
        self.leaderScores = []
        self.numLeaders = 10
        self.tutorial = 0

    def generate(self):
        DistributedObject.DistributedObject.generate(self)
        self.interior = loader.loadModel('phase_3.5/models/modules/HQ_interior')
        self.interior.reparentTo(render)
        self.interior.find('**/cream').hide()
        self.interior.find('**/crashed_piano').hide()
        self.buildLeaderBoard()

    def announceGenerate(self):
        DistributedObject.DistributedObject.announceGenerate(self)
        self.setupDoors()
        self.interior.flattenMedium()
        emptyBoard = self.interior.find('**/empty_board')
        self.leaderBoard.reparentTo(emptyBoard.getChild(0))

    def setTutorial(self, flag):
        if self.tutorial == flag:
            return
        else:
            self.tutorial = flag
        if self.tutorial:
            self.interior.find('**/periscope').hide()
            self.interior.find('**/speakers').hide()
        else:
            self.interior.find('**/periscope').show()
            self.interior.find('**/speakers').show()

    def setZoneIdAndBlock(self, zoneId, block):
        self.zoneId = zoneId
        self.block = block

    def buildLeaderBoard(self):
        self.leaderBoard = hidden.attachNewNode('leaderBoard')
        self.leaderBoard.setPosHprScale(0.1, 0, 4.5, 90, 0, 0, 0.9, 0.9, 0.9)
        z = 0
        row = self.buildTitleRow()
        row.reparentTo(self.leaderBoard)
        row.setPos(0, 0, z)
        z -= 1
        self.nameTextNodes = []
        self.scoreTextNodes = []
        self.trophyStars = []
        for i in range(self.numLeaders):
            row, nameText, scoreText, trophyStar = self.buildLeaderRow()
            self.nameTextNodes.append(nameText)
            self.scoreTextNodes.append(scoreText)
            self.trophyStars.append(trophyStar)
            row.reparentTo(self.leaderBoard)
            row.setPos(0, 0, z)
            z -= 1

    def updateLeaderBoard(self):
        taskMgr.remove(self.uniqueName('starSpinHQ'))
        for i in range(len(self.leaderNames)):
            name = self.leaderNames[i]
            score = self.leaderScores[i]
            self.nameTextNodes[i].setText(name)
            self.scoreTextNodes[i].setText(str(score))
            self.updateTrophyStar(self.trophyStars[i], score)

        for i in range(len(self.leaderNames), self.numLeaders):
            self.nameTextNodes[i].setText('-')
            self.scoreTextNodes[i].setText('-')
            self.trophyStars[i].hide()

    def buildTitleRow(self):
        row = hidden.attachNewNode('leaderRow')
        nameText = TextNode('titleRow')
        nameText.setFont(ToontownGlobals.getSignFont())
        nameText.setAlign(TextNode.ACenter)
        nameText.setTextColor(0.5, 0.75, 0.7, 1)
        nameText.setText(TTLocalizer.LeaderboardTitle)
        namePath = row.attachNewNode(nameText)
        namePath.setPos(0, 0, 0)
        return row

    def buildLeaderRow(self):
        row = hidden.attachNewNode('leaderRow')
        nameText = TextNode('nameText')
        nameText.setFont(ToontownGlobals.getToonFont())
        nameText.setAlign(TextNode.ALeft)
        nameText.setTextColor(1, 1, 1, 0.7)
        nameText.setText('-')
        namePath = row.attachNewNode(nameText)
        namePath.setPos(*TTLocalizer.DHQInamePathPos)
        namePath.setScale(TTLocalizer.DHQInamePath)
        scoreText = TextNode('scoreText')
        scoreText.setFont(ToontownGlobals.getToonFont())
        scoreText.setAlign(TextNode.ARight)
        scoreText.setTextColor(1, 1, 0.1, 0.7)
        scoreText.setText('-')
        scorePath = row.attachNewNode(scoreText)
        scorePath.setPos(*TTLocalizer.DHQIscorePathPos)
        trophyStar = self.buildTrophyStar()
        trophyStar.reparentTo(row)
        return (row,
         nameText,
         scoreText,
         trophyStar)

    def setLeaderBoard(self, leaderData):
        avIds, names, scores = pickle.loads(leaderData)
        self.notify.debug('setLeaderBoard: avIds: %s, names: %s, scores: %s' % (avIds, names, scores))
        self.leaderAvIds = avIds
        self.leaderNames = names
        self.leaderScores = scores
        self.updateLeaderBoard()

    def chooseDoor(self):
        doorModelName = 'door_double_round_ul'
        if doorModelName[-1:] == 'r':
            doorModelName = doorModelName[:-1] + 'l'
        else:
            doorModelName = doorModelName[:-1] + 'r'
        door = self.dnaStore.findNode(doorModelName)
        return door

    def setupDoors(self):
        self.randomGenerator = random.Random()
        self.randomGenerator.seed(self.zoneId)
        self.colors = ToonInteriorColors.colors[ToontownCentral]
        door = self.chooseDoor()
        doorOrigins = render.findAllMatches('**/door_origin*')
        numDoorOrigins = doorOrigins.getNumPaths()
        for npIndex in range(numDoorOrigins):
            doorOrigin = doorOrigins[npIndex]
            doorOriginNPName = doorOrigin.getName()
            doorOriginIndexStr = doorOriginNPName[len('door_origin_'):]
            newNode = ModelNode('door_' + doorOriginIndexStr)
            newNodePath = NodePath(newNode)
            newNodePath.reparentTo(self.interior)
            doorNP = door.copyTo(newNodePath)
            doorOrigin.setScale(0.8, 0.8, 0.8)
            doorOrigin.setPos(doorOrigin, 0, -0.025, 0)
            doorColor = self.randomGenerator.choice(self.colors['TI_door'])
            triggerId = str(self.block) + '_' + doorOriginIndexStr
            DNADoor.setupDoor(doorNP, newNodePath, doorOrigin, self.dnaStore, triggerId, doorColor)
            doorFrame = doorNP.find('door_*_flat')
            doorFrame.setColor(doorColor)

        del self.dnaStore
        del self.randomGenerator

    def disable(self):
        self.leaderBoard.removeNode()
        del self.leaderBoard
        self.interior.removeNode()
        del self.interior
        del self.nameTextNodes
        del self.scoreTextNodes
        del self.trophyStars
        taskMgr.remove(self.uniqueName('starSpinHQ'))
        DistributedObject.DistributedObject.disable(self)

    def buildTrophyStar(self):
        trophyStar = loader.loadModel('phase_3.5/models/gui/name_star')
        trophyStar.hide()
        trophyStar.setPos(*TTLocalizer.DHQItrophyStarPos)
        return trophyStar

    def updateTrophyStar(self, trophyStar, score):
        scale = 0.8
        if score >= ToontownGlobals.TrophyStarLevels[4]:
            trophyStar.show()
            trophyStar.setScale(scale)
            trophyStar.setColor(ToontownGlobals.TrophyStarColors[4])
            if score >= ToontownGlobals.TrophyStarLevels[5]:
                task = taskMgr.add(self.__starSpin, self.uniqueName('starSpinHQ'))
                task.trophyStarSpeed = 15
                task.trophyStar = trophyStar
        elif score >= ToontownGlobals.TrophyStarLevels[2]:
            trophyStar.show()
            trophyStar.setScale(0.75 * scale)
            trophyStar.setColor(ToontownGlobals.TrophyStarColors[2])
            if score >= ToontownGlobals.TrophyStarLevels[3]:
                task = taskMgr.add(self.__starSpin, self.uniqueName('starSpinHQ'))
                task.trophyStarSpeed = 10
                task.trophyStar = trophyStar
        elif score >= ToontownGlobals.TrophyStarLevels[0]:
            trophyStar.show()
            trophyStar.setScale(0.75 * scale)
            trophyStar.setColor(ToontownGlobals.TrophyStarColors[0])
            if score >= ToontownGlobals.TrophyStarLevels[1]:
                task = taskMgr.add(self.__starSpin, self.uniqueName('starSpinHQ'))
                task.trophyStarSpeed = 8
                task.trophyStar = trophyStar
        else:
            trophyStar.hide()

    def __starSpin(self, task):
        now = globalClock.getFrameTime()
        r = now * task.trophyStarSpeed % 360.0
        task.trophyStar.setR(r)
        return Task.cont
