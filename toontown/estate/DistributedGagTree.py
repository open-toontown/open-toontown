from toontown.estate import DistributedPlantBase
from direct.interval.IntervalGlobal import *
from direct.directnotify import DirectNotifyGlobal
from direct.showbase import PythonUtil
from toontown.toonbase import ToontownBattleGlobals
from toontown.toontowngui import TTDialog
from toontown.toontowngui.TeaserPanel import TeaserPanel
from toontown.toonbase import TTLocalizer
import GardenGlobals
import HouseGlobals
from direct.task import Task
from pandac.PandaModules import *
from otp.otpbase import OTPGlobals
from toontown.estate import DistributedLawnDecor
DIRT_AS_WATER_INDICATOR = True

class DistributedGagTree(DistributedPlantBase.DistributedPlantBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedGagTree')

    def __init__(self, cr):
        DistributedPlantBase.DistributedPlantBase.__init__(self, cr)
        base.tree = self
        self.collSphereRadius = 4.2
        self.confirmDialog = None
        self.resultDialog = None
        self.dirtMound = None
        self.sandMound = None
        self.needToPlant = 0
        self.needToLoad = 0
        self.backupFruits = []
        self.signHasBeenStuck2Ground = False
        self._teaserPanel = None
        self.setName('DistributedGagTree')
        return

    def delete(self):
        DistributedPlantBase.DistributedPlantBase.delete(self)
        if self._teaserPanel:
            self._teaserPanel.destroy()
            self._teaserPanel = None
        del self.prop
        del self.prop2
        del self.dirtMound
        del self.sandMound
        self.signModel.removeNode()
        self.signModel = None
        return

    def setTypeIndex(self, typeIndex):
        DistributedPlantBase.DistributedPlantBase.setTypeIndex(self, typeIndex)
        track, level = GardenGlobals.getTreeTrackAndLevel(typeIndex)
        self.gagTrack = track
        self.gagLevel = level
        invModel = loader.loadModel('phase_3.5/models/gui/inventory_icons')
        propName = ToontownBattleGlobals.AvPropsNew[track][level]
        self.prop = invModel.find('**/' + propName)
        self.prop.setScale(7)
        invModel.removeNode()
        invModel2 = loader.loadModel('phase_3.5/models/gui/inventory_icons')
        propName = ToontownBattleGlobals.AvPropsNew[track][level]
        self.prop2 = invModel2.find('**/' + propName)
        self.prop2.setScale(7)
        self.filename = self.attributes['filename']
        self.maxFruit = self.attributes['maxFruit']
        if hasattr(self, 'needToLoad'):
            if self.needToLoad:
                self.loadModel()

    def loadModel(self):
        if not hasattr(self, 'filename'):
            self.needToLoad = 1
            return
        if not self.rotateNode:
            self.rotateNode = self.plantPath.attachNewNode('rotate')
        all = loader.loadModel(self.filename)
        self.modelName = self.getModelName()
        if self.isWilted():
            self.modelName += '_wilt'
        self.model = all.find('**/' + self.modelName)
        all.detachNode()
        shadow = self.model.find('**/shadow1')
        if shadow:
            shadow.hide()
        self.model.reparentTo(self.rotateNode)
        if self.isFruiting() and not self.isWilted():
            self.fruits = []
            for i in range(1, self.maxFruit + 1):
                pos = self.model.find('**/locator' + str(i))
                if pos and not pos.isEmpty():
                    fruit = self.prop.copyTo(self.model)
                    fruit.setPos(pos, 0, 0, 0)
                    fruit.setScale(13)
                    self.fruits.append(fruit)

            self.createBackupFruits()
        if DIRT_AS_WATER_INDICATOR:
            self.dirtMound = loader.loadModel('phase_5.5/models/estate/dirt_mound')
            self.dirtMound.reparentTo(self.model)
            self.sandMound = loader.loadModel('phase_5.5/models/estate/sand_mound')
            self.sandMound.reparentTo(self.model)
        self.adjustGrowth()
        self.signModel = loader.loadModel('phase_5.5/models/estate/garden_sign.bam')
        self.signModel.setPos(3.5, 0, 0.025)
        self.signModel.reparentTo(self.rotateNode)
        owner = self.getOwnerIndex()
        color = HouseGlobals.houseColors[owner]
        for geomName in ('sign', 'sign1'):
            sign = self.signModel.find('**/' + geomName)
            if sign:
                sign.setColor(*color)

        self.prop.setPos(0.1, -0.17, 1.63)
        self.prop.reparentTo(self.signModel)
        self.prop2.setPos(0.15, 0.17, 1.63)
        self.prop2.setH(self.prop.getH() + 180)
        self.prop2.reparentTo(self.signModel)
        self.needToLoad = 0
        if self.needToPlant:
            self.stickParts()

    def setupShadow(self):
        DistributedPlantBase.DistributedPlantBase.setupShadow(self)
        self.adjustGrowth()

    def makeMovieNode(self):
        self.movieNode = self.rotateNode.attachNewNode('moviePos')
        self.movieNode.setPos(0, -5, 0)
        self.createBackupFruits()

    def handlePicking(self):
        messenger.send('wakeup')
        if self.isFruiting() and self.canBeHarvested():
            if self.velvetRoped():
                self._teaserPanel = TeaserPanel(pageName='pickGags')
                localAvatar._gagTreeVelvetRoped = None
            else:
                self.startInteraction()
                self.doHarvesting()
            return
        fullName = self.name
        text = TTLocalizer.ConfirmRemoveTree % {'tree': fullName}
        if self.hasDependentTrees():
            text += TTLocalizer.ConfirmWontBeAbleToHarvest
        self.confirmDialog = TTDialog.TTDialog(style=TTDialog.YesNo, text=text, command=self.confirmCallback)
        self.confirmDialog.show()
        self.startInteraction()
        return

    def confirmCallback(self, value):
        self.confirmDialog.destroy()
        self.confirmDialog = None
        if value > 0:
            self.doPicking()
        else:
            self.finishInteraction()
        return

    def doPicking(self):
        if not self.canBePicked():
            return
        self.sendUpdate('removeItem', [])

    def createBackupFruits(self):
        if not hasattr(self, 'fruits'):
            return
        if not self.fruits:
            return
        if not hasattr(self, 'movieNode'):
            return
        if not self.movieNode:
            return
        if self.movieNode.isEmpty():
            return
        if not self.signHasBeenStuck2Ground:
            return
        if not self.backupFruits:
            for fruit in self.fruits:
                newFruit = fruit.copyTo(render)
                newFruit.setPos(fruit.getPos(render))
                newFruit.setH(self.movieNode.getH(render))
                newFruit.hide()
                self.backupFruits.append(newFruit)

    def clearBackupFruits(self):
        self.backupFruits = []

    def doHarvesting(self):
        if not self.canBePicked():
            return
        if hasattr(self, 'backupFruits'):
            for fruit in self.backupFruits:
                fruit.show()

        self.sendUpdate('requestHarvest', [])

    def getTrack(self):
        return self.gagTrack

    def getGagLevel(self):
        return self.gagLevel

    def setWaterLevel(self, waterLevel):
        self.waterLevel = waterLevel
        self.adjustWaterIndicator()

    def setGrowthLevel(self, growthLevel):
        self.growthLevel = growthLevel
        if self.model:
            newModelName = self.getModelName()
            if True:
                self.model.removeNode()
                self.loadModel()
                self.adjustWaterIndicator()
                self.stick2Ground()
            else:
                self.adjustGrowth()

    def adjustGrowth(self):
        newScale = self.growthLevel + 1
        if newScale > 1:
            newScale = 1
        shadowScale = 2.5
        collScale = 1.5
        if self.isSeedling():
            shadowScale = 1
            collScale = 1
        if self.shadowJoint:
            self.shadowJoint.setScale(shadowScale)
        if DIRT_AS_WATER_INDICATOR:
            dirtMoundScale = shadowScale * 1.5
            dirtMoundDepth = 2.0
            if self.isEstablished():
                dirtMoundScale = shadowScale * 1.2
            self.dirtMound.setScale(dirtMoundScale, dirtMoundScale, dirtMoundDepth)
            self.sandMound.setScale(dirtMoundScale, dirtMoundScale, dirtMoundDepth)
            self.adjustWaterIndicator()

    def setWilted(self, wilted):
        self.wilted = wilted

    def isWilted(self):
        return self.wilted

    def setMovie(self, mode, avId):
        if mode == GardenGlobals.MOVIE_HARVEST:
            self.doHarvestTrack(avId)
        elif mode == GardenGlobals.MOVIE_WATER:
            self.doWaterTrack(avId)
        elif mode == GardenGlobals.MOVIE_FINISHPLANTING:
            self.doFinishPlantingTrack(avId)
        elif mode == GardenGlobals.MOVIE_REMOVE:
            self.doDigupTrack(avId)

    def doFinishPlantingTrack(self, avId):
        toon = base.cr.doId2do.get(avId)
        if not toon:
            return
        self.finishMovies()
        self.movie = Sequence()
        if self.model:
            self.model.setTransparency(1)
            self.model.setAlphaScale(0)
            self.movie.append(LerpFunc(self.model.setAlphaScale, fromData=0, toData=1, duration=3))
        if self.signModel:
            self.signModel.hide()
            self.movie.append(Func(self.signModel.show))
            self.movie.append(LerpScaleInterval(self.signModel, 1, 1, 0))
        self.movie.append(Func(toon.loop, 'neutral'))
        if avId == localAvatar.doId:
            self.movie.append(Func(self.finishInteraction))
            self.movie.append(Func(self.movieDone))
            self.movie.append(Func(self.doResultDialog))
        self.movie.start()

    def doHarvestTrack(self, avId):
        toon = base.cr.doId2do.get(avId)
        if not toon:
            return
        self.finishMovies()
        moveTrack = self.generateToonMoveTrack(toon)
        harvestTrack = self.generateHarvestTrack(toon)
        self.movie = Sequence(self.startCamIval(avId), moveTrack, harvestTrack, self.stopCamIval(avId))
        if avId == localAvatar.doId:
            self.movie.append(Func(self.finishInteraction))
            self.movie.append(Func(self.movieDone))
        self.movie.start()

    def setupShadow(self):
        if DIRT_AS_WATER_INDICATOR:
            pass
        else:
            DistributedPlantBase.DistributedPlantBase.setupShadow(self)

    def generateHarvestTrack(self, toon):
        pos = toon.getPos(render)
        pos.setZ(pos.getZ() + 2)
        fruitTrack = Parallel()
        for fruit in self.backupFruits:
            fruitTrack.append(Sequence(Func(fruit.show), LerpPosInterval(fruit, 1.5, pos, startPos=Point3(fruit.getX(), fruit.getY(), fruit.getZ() + self.model.getZ())), Func(fruit.removeNode)))

        self.fruits = None
        harvestTrack = Sequence(fruitTrack, Func(self.clearBackupFruits))
        return harvestTrack

    def adjustWaterIndicator(self):
        DistributedPlantBase.DistributedPlantBase.adjustWaterIndicator(self)
        if self.dirtMound:
            curWaterLevel = self.waterLevel
            if curWaterLevel > self.maxWaterLevel:
                curWaterLevel = self.maxWaterLevel
            if curWaterLevel > 0:
                darkestColorScale = 0.4
                lightestColorScale = 1.0
                scaleRange = lightestColorScale - darkestColorScale
                scaleIncrement = scaleRange / self.maxWaterLevel
                darker = lightestColorScale - scaleIncrement * curWaterLevel
                self.dirtMound.setColorScale(darker, darker, darker, 1.0)
                self.sandMound.hide()
                self.dirtMound.show()
            else:
                self.sandMound.show()
                self.dirtMound.hide()

    def stickParts(self):
        if not hasattr(self, 'signModel'):
            self.needToPlant = 1
            return Task.done
        if self.signModel.isEmpty():
            return Task.done
        testPath = NodePath('testPath')
        testPath.reparentTo(render)
        cRay = CollisionRay(0.0, 0.0, 40000.0, 0.0, 0.0, -1.0)
        cRayNode = CollisionNode(self.uniqueName('estate-FloorRay'))
        cRayNode.addSolid(cRay)
        cRayNode.setFromCollideMask(OTPGlobals.FloorBitmask)
        cRayNode.setIntoCollideMask(BitMask32.allOff())
        cRayNodePath = testPath.attachNewNode(cRayNode)
        queue = CollisionHandlerQueue()
        picker = CollisionTraverser()
        picker.addCollider(cRayNodePath, queue)
        testPath.setPos(self.signModel.getX(render), self.signModel.getY(render), 0)
        picker.traverse(render)
        if queue.getNumEntries() > 0:
            queue.sortEntries()
            for index in range(queue.getNumEntries()):
                entry = queue.getEntry(index)
                if DistributedLawnDecor.recurseParent(entry.getIntoNode(), 'terrain_DNARoot'):
                    self.signModel.wrtReparentTo(render)
                    self.signModel.setZ(entry.getSurfacePoint(render)[2] + self.stickUp + 0.1)
                    self.signModel.wrtReparentTo(self.rotateNode)
                    self.signHasBeenStuck2Ground = True
                    self.createBackupFruits()
                    return Task.done

        return Task.done

    def canBeHarvested(self):
        if not base.cr.isPaid():
            if self.velvetRoped():
                if hasattr(localAvatar, '_gagTreeVelvetRoped'):
                    return False
        myTrack, myLevel = GardenGlobals.getTreeTrackAndLevel(self.typeIndex)
        levelsInTrack = []
        levelTreeDict = {}
        allGagTrees = base.cr.doFindAll('DistributedGagTree')
        for gagTree in allGagTrees:
            if gagTree.getOwnerId() == localAvatar.doId:
                curTrack, curLevel = GardenGlobals.getTreeTrackAndLevel(gagTree.typeIndex)
                if curTrack == myTrack:
                    levelsInTrack.append(curLevel)
                    levelTreeDict[curLevel] = gagTree

        for levelToTest in range(myLevel):
            if levelToTest not in levelsInTrack:
                return False
            curTree = levelTreeDict[levelToTest]
            if not curTree.isGTEFullGrown():
                return False

        return True

    def hasDependentTrees(self):
        myTrack, myLevel = GardenGlobals.getTreeTrackAndLevel(self.typeIndex)
        allGagTrees = base.cr.doFindAll('DistributedGagTree')
        for gagTree in allGagTrees:
            if gagTree.getOwnerId() == localAvatar.doId:
                curTrack, curLevel = GardenGlobals.getTreeTrackAndLevel(gagTree.typeIndex)
                if curTrack == myTrack:
                    if myLevel < curLevel:
                        return True

        return False

    def doResultDialog(self):
        self.startInteraction()
        curTrack, curLevel = GardenGlobals.getTreeTrackAndLevel(self.typeIndex)
        species = GardenGlobals.getTreeTypeIndex(curTrack, curLevel)
        treeName = GardenGlobals.PlantAttributes[species]['name']
        stringToShow = TTLocalizer.getResultPlantedSomethingSentence(treeName)
        self.resultDialog = TTDialog.TTDialog(style=TTDialog.Acknowledge, text=stringToShow, command=self.resultsCallback)

    def resultsCallback(self, value):
        if self.resultDialog:
            self.resultDialog.destroy()
            self.resultDialog = None
        self.finishInteraction()
        return

    def velvetRoped(self):
        return not base.cr.isPaid() and ToontownBattleGlobals.gagIsPaidOnly(self.gagTrack, self.gagLevel)

    def allowedToPick(self):
        retval = True
        if self.velvetRoped():
            retval = False
        return retval

    def unlockPick(self):
        retval = True
        toon = base.localAvatar
        inventory = toon.inventory
        load = inventory.totalProps
        maxCarry = toon.getMaxCarry()
        if load >= maxCarry and not self.gagLevel > ToontownBattleGlobals.LAST_REGULAR_GAG_LEVEL:
            retval = False
        if inventory.numItem(self.gagTrack, self.gagLevel) >= inventory.getMax(self.gagTrack, self.gagLevel):
            retval = False
        return retval
