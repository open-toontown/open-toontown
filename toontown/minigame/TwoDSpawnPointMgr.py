from panda3d.core import *
from direct.directnotify import DirectNotifyGlobal
from direct.showbase.DirectObject import DirectObject
from toontown.minigame import ToonBlitzGlobals
from toontown.toonbase import ToontownGlobals

class TwoDSpawnPointMgr(DirectObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('TwoDSpawnPointMgr')

    def __init__(self, section, spawnPointList):
        self.section = section
        self.game = self.section.sectionMgr.game
        self.spawnPointList = spawnPointList
        self.lastSavePoint = 0
        self.showCollSpheres = False
        self.savePoints = []
        self.loadPoints = []
        self.collNPList = []
        self.collDict = {}
        self.load()

    def destroy(self):
        while len(self.collNPList):
            item = self.collNPList[0]
            self.ignore('enter' + self.collNPList[0].node().getName())
            self.collNPList.remove(item)
            item.removeNode()

        self.section = None
        self.game = None
        self.savePoints = None
        self.loadPoints = None
        self.collNPList = None
        self.collDict = None
        return

    def load(self):
        if len(self.spawnPointList):
            self.spawnPointsNP = NodePath('SpawnPoints')
            self.spawnPointsNP.reparentTo(self.section.sectionNP)
        for point in self.spawnPointList:
            if len(point) == 1:
                savePoint = point[0]
                loadPoint = point[0]
            else:
                savePoint = point[0]
                loadPoint = point[1]
            index = len(self.savePoints)
            self.savePoints.append(savePoint)
            self.loadPoints.append(loadPoint)
            self.setupCollision(index)

    def setupCollision(self, index):
        collSphere = CollisionSphere(0, 0, 0, 3)
        collSphereName = 'savePoint%s' % self.section.getSectionizedId(index)
        collSphere.setTangible(0)
        collNode = CollisionNode(self.game.uniqueName(collSphereName))
        collNode.setIntoCollideMask(ToontownGlobals.WallBitmask)
        collNode.addSolid(collSphere)
        collNodePath = self.spawnPointsNP.attachNewNode(collNode)
        collNodePath.hide()
        if self.showCollSpheres:
            collNodePath.show()
        posX, posY, posZ = self.savePoints[index]
        collNodePath.setPos(posX, posY, posZ)
        self.collNPList.append(collNodePath)
        self.collDict[collNodePath.getName()] = index
        self.accept(self.game.uniqueName('enter' + collSphereName), self.handleSavePointCollision)

    def handleSavePointCollision(self, cevent):
        savePointName = cevent.getIntoNodePath().getName()
        self.lastSavePoint = self.collDict[savePointName]
        self.section.sectionMgr.updateActiveSection(self.section.indexNum)

    def getSpawnPoint(self):
        if len(self.loadPoints) > 0:
            point = self.loadPoints[self.lastSavePoint]
            return Point3(point[0], point[1], point[2])
        else:
            return Point3(ToonBlitzGlobals.ToonStartingPosition[0], ToonBlitzGlobals.ToonStartingPosition[1], ToonBlitzGlobals.ToonStartingPosition[2])

    def setupLastSavePointHandle(self):
        if len(self.collNPList) > 0:
            self.accept('enter' + self.collNPList[-1].getName(), self.handleLastSavePointCollision)
            self.gameEndX = self.collNPList[-1].getX(render)

    def handleLastSavePointCollision(self, cevent):
        self.game.localToonVictory()
