from pandac.PandaModules import *
from direct.directnotify import DirectNotifyGlobal
from direct.showbase.DirectObject import DirectObject
from toontown.minigame import ToonBlitzGlobals
from toontown.minigame import TwoDSection
from toontown.minigame import TwoDSpawnPointMgr
from toontown.minigame import TwoDBlock
from direct.gui import DirectGui
from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownGlobals

class TwoDSectionMgr(DirectObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('TwoDSectionMgr')

    def __init__(self, game, sectionsSelected):
        self.game = game
        self.sectionsPool = []
        self.sectionsSelected = []
        self.sections = []
        self.sectionNPList = []
        self.activeSection = 0
        self.setupStartSection()
        self.setupSections(sectionsSelected)
        self.setupEndSection(len(sectionsSelected))

    def destroy(self):
        while len(self.sections):
            section = self.sections[0]
            section.destroy()
            self.sections.remove(section)

        self.sections = []
        self.sectionsPool = []
        self.sectionsSelected = []
        self.sectionNPList = []
        self.startWall.removeNode()
        del self.startWall
        self.startPipe.removeNode()
        del self.startPipe
        self.startArrow.removeNode()
        del self.startArrow
        self.endArrow.removeNode()
        del self.endArrow
        self.game = None
        self.activeSection = 0
        return

    def setupStartSection(self):
        self.startSectionNP = NodePath('StartSection')
        self.startSectionNP.reparentTo(self.game.assetMgr.world)
        self.startSectionNP.setX(-48)
        self.startWall = self.game.assetMgr.startingWall.copyTo(self.startSectionNP)
        self.startWall.setPos(-28, 0, 4)
        self.startWall.setScale(0.8)
        self.startPipe = self.game.assetMgr.startingPipe.copyTo(self.startSectionNP)
        self.startPipe.setPos(12, 0, 44)
        self.startArrow = self.game.assetMgr.arrow.copyTo(self.startSectionNP)
        self.startArrow.setPos(23, 1.5, 12.76)
        for index in range(len(ToonBlitzGlobals.BlockListStart)):
            blockAttribs = ToonBlitzGlobals.BlockListStart[index]
            fileName = ToonBlitzGlobals.BlockTypes[blockAttribs[0]][0]
            blockIndex = int(fileName[-1])
            blockType = self.game.assetMgr.blockTypes[blockIndex]
            sectionizedId = 'start-' + str(index)
            newBlock = TwoDBlock.TwoDBlock(blockType, sectionizedId, blockAttribs)
            newBlock.model.reparentTo(self.startSectionNP)

    def setupEndSection(self, index):
        aspectSF = 0.7227
        self.endSectionNP = NodePath('EndSection')
        self.endSectionNP.reparentTo(self.game.assetMgr.world)
        self.endSectionNP.setX(self.incrementX)
        self.endWall = self.game.assetMgr.startingWall.copyTo(self.endSectionNP)
        self.endWall.setPos(100, 0, 4)
        self.endWall.setScale(0.8)
        self.endArrow = self.game.assetMgr.arrow.copyTo(self.endSectionNP)
        self.endArrow.setPos(6, 1.5, 12.76)
        self.exitElevator = self.game.assetMgr.exitElevator.copyTo(self.endSectionNP)
        self.exitElevator.setPos(52, -2, 12.7)
        cogSignModel = loader.loadModel('phase_4/models/props/sign_sellBotHeadHQ')
        cogSign = cogSignModel.find('**/sign_sellBotHeadHQ')
        cogSignSF = 23
        elevatorSignSF = 15
        sideDoor = self.exitElevator.find('**/doorway2')
        sdSign = cogSign.copyTo(sideDoor)
        sdSign.setPosHprScale(0, 1.9, 15, 0, 0, 0, elevatorSignSF, elevatorSignSF, elevatorSignSF * aspectSF)
        sdSign.node().setEffect(DecalEffect.make())
        sdText = DirectGui.OnscreenText(text=TTLocalizer.TwoDGameElevatorExit, font=ToontownGlobals.getSuitFont(), pos=(0, -0.34), scale=0.15, mayChange=False, parent=sdSign)
        sdText.setDepthWrite(0)
        self.sectionNPList.append(self.endSectionNP)
        endSectionInfo = ('end',
         [],
         [],
         [0],
         [])
        endSection = TwoDSection.TwoDSection(index, endSectionInfo, self.endSectionNP, self)
        self.sections.append(endSection)
        self.incrementX += endSection.length

    def setupSections(self, sectionsSelected):
        self.incrementX = -24
        for index in range(0, len(sectionsSelected)):
            sectionNP = NodePath('Section' + str(index))
            sectionNP.reparentTo(self.game.assetMgr.world)
            sectionNP.setX(self.incrementX)
            self.sectionNPList.append(sectionNP)
            section = TwoDSection.TwoDSection(index, sectionsSelected[index], sectionNP, self)
            self.sections.append(section)
            self.incrementX += section.length

    def enterPlay(self, elapsedTime):
        for section in self.sections:
            section.enterPlay(elapsedTime)

    def exitPlay(self):
        pass

    def enterPause(self):
        for section in self.sections:
            section.enterPause()

    def exitPause(self):
        for section in self.sections:
            section.exitPause()

    def updateActiveSection(self, sectionIndex):
        if self.activeSection != sectionIndex:
            self.activeSection = sectionIndex
            self.notify.debug('Toon is in section %s.' % sectionIndex)

    def getLastSpawnPoint(self):
        relativePoint = Point3(self.sections[self.activeSection].spawnPointMgr.getSpawnPoint())
        relativePoint.setX(relativePoint.getX() + self.sectionNPList[self.activeSection].getX())
        return relativePoint
