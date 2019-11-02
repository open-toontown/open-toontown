from pandac.PandaModules import *
from direct.directnotify import DirectNotifyGlobal
from direct.showbase.DirectObject import DirectObject
from toontown.minigame import ToonBlitzGlobals
from toontown.minigame import TwoDBlock
from toontown.minigame import TwoDEnemyMgr
from toontown.minigame import TwoDTreasureMgr
from toontown.minigame import TwoDSpawnPointMgr
from toontown.minigame import TwoDStomperMgr

class TwoDSection(DirectObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('TwoDSection')

    def __init__(self, indexNum, sectionInfo, sectionNP, sectionMgr):
        self.indexNum = indexNum
        self.sectionNP = sectionNP
        self.sectionMgr = sectionMgr
        self.blocks = []
        self.load(sectionInfo)

    def destroy(self):
        for block in self.blocks:
            block.destroy()

        self.enemyMgr.destroy()
        del self.enemyMgr
        self.treasureMgr.destroy()
        del self.treasureMgr
        self.spawnPointMgr.destroy()
        del self.spawnPointMgr
        self.stomperMgr.destroy()
        del self.stomperMgr
        self.sectionMgr = None
        self.sectionNP = None
        self.blockList = []
        self.enemyList = []
        self.treasureList = []
        self.spawnPointList = []
        return

    def load(self, sectionInfo):
        self.sectionTypeNum = sectionInfo[0]
        enemyIndicesSelected = sectionInfo[1]
        treasureIndicesSelected = sectionInfo[2]
        spawnPointIndicesSelected = sectionInfo[3]
        stomperIndicesSelected = sectionInfo[4]
        attribs = ToonBlitzGlobals.SectionTypes[self.sectionTypeNum]
        self.length = attribs[1]
        self.blockList = attribs[2]
        enemiesPool = attribs[3]
        treasuresPool = attribs[4]
        spawnPointsPool = attribs[5]
        stompersPool = attribs[6]
        self.enemyList = []
        for enemyIndex in enemyIndicesSelected:
            self.enemyList.append(enemiesPool[enemyIndex])

        self.treasureList = []
        for treasure in treasureIndicesSelected:
            treasureIndex = treasure[0]
            treasureValue = treasure[1]
            treasureAttribs = treasuresPool[treasureIndex]
            self.treasureList.append((treasureAttribs, treasureValue))

        self.spawnPointList = []
        for spawnPointIndex in spawnPointIndicesSelected:
            self.spawnPointList.append(spawnPointsPool[spawnPointIndex])

        self.stomperList = []
        for stomperIndex in stomperIndicesSelected:
            self.stomperList.append(stompersPool[stomperIndex])

        self.blocksNP = NodePath('Blocks')
        self.blocksNP.reparentTo(self.sectionNP)
        if self.blockList[0][1][0] != (0, 0, 12):
            self.notify.warning('First block of section %s does not start at (0, 0, 12)' % self.sectionTypeNum)
        for index in range(0, len(self.blockList)):
            blockAttribs = self.blockList[index]
            fileName = ToonBlitzGlobals.BlockTypes[blockAttribs[0]][0]
            blockIndex = int(fileName[-1])
            blockType = self.sectionMgr.game.assetMgr.blockTypes[blockIndex]
            sectionizedId = self.getSectionizedId(index)
            newBlock = TwoDBlock.TwoDBlock(blockType, sectionizedId, blockAttribs)
            newBlock.model.reparentTo(self.blocksNP)
            self.blocks.append(newBlock)

        self.enemyMgr = TwoDEnemyMgr.TwoDEnemyMgr(self, self.enemyList)
        self.treasureMgr = TwoDTreasureMgr.TwoDTreasureMgr(self, self.treasureList, self.enemyList)
        self.spawnPointMgr = TwoDSpawnPointMgr.TwoDSpawnPointMgr(self, self.spawnPointList)
        self.stomperMgr = TwoDStomperMgr.TwoDStomperMgr(self, self.stomperList)
        if self.sectionTypeNum == 'end':
            self.spawnPointMgr.setupLastSavePointHandle()

    def enterPlay(self, elapsedTime):
        for block in self.blocks:
            block.start(elapsedTime)

        self.enemyMgr.enterPlay(elapsedTime)
        self.stomperMgr.enterPlay(elapsedTime)

    def exitPlay(self):
        pass

    def enterPause(self):
        for block in self.blocks:
            block.enterPause()

        self.enemyMgr.enterPause()
        self.stomperMgr.enterPause()

    def exitPause(self):
        for block in self.blocks:
            block.exitPause()

        self.enemyMgr.exitPause()
        self.stomperMgr.exitPause()

    def getSectionizedId(self, num):

        def getTwoDigitString(index):
            if index < 10:
                output = '0' + str(index)
            else:
                output = str(index)
            return output

        return getTwoDigitString(self.indexNum) + '-' + getTwoDigitString(num)
