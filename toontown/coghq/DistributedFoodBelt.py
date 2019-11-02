from pandac.PandaModules import NodePath, Point3, CollisionTube, CollisionNode
from direct.fsm import FSM
from direct.distributed import DistributedObject
from direct.directnotify import DirectNotifyGlobal
from direct.interval.IntervalGlobal import Sequence, Wait, LerpPosInterval, ProjectileInterval, Func, SoundInterval
from direct.actor import Actor
from toontown.toonbase import ToontownGlobals
from toontown.coghq.FoodBeltBase import FoodBeltBase

class DistributedFoodBelt(DistributedObject.DistributedObject, FSM.FSM, FoodBeltBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedFoodBelt')
    BeltSpeed = 5
    OnDuration = 300
    ToonupBeltSpeed = 1.0
    BeltActorPlayRate = 5.35
    ToonupBeltActorPlayRate = BeltActorPlayRate * ToonupBeltSpeed / BeltSpeed
    ToonupModels = ['phase_6/models/golf/picnic_apple.bam',
     'phase_6/models/golf/picnic_cupcake.bam',
     'phase_6/models/golf/picnic_sandwich.bam',
     'phase_6/models/golf/picnic_chocolate_cake.bam']
    ToonupScales = [5,
     5,
     5,
     4]
    ToonupZOffsets = [-0.25,
     -0.25,
     -0,
     -0.25]

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        FSM.FSM.__init__(self, 'DistributedFoodBelt')
        self.boss = None
        self.bossCogId = 0
        self.index = -1
        self.foodNodes = []
        self.foodIvals = []
        self.foodWaitTimes = []
        self.foodModelDict = {}
        self.foodNum = 0
        self.beltActor = None
        self.toonupIvals = []
        self.toonupWaitTimes = []
        self.toonupModelDict = {}
        self.toonupNum = 0
        return

    def delete(self):
        DistributedObject.DistributedObject.delete(self)
        self.cleanup()

    def announceGenerate(self):
        DistributedObject.DistributedObject.announceGenerate(self)
        if self.boss:
            self.boss.setBelt(self, self.index)
            self.loadAssets()
        else:
            self.notify.warning('announceGenerate self.boss is None, self.bossCogId = %d' % self.bossCogId)

    def setBossCogId(self, bossCogId):
        self.bossCogId = bossCogId
        self.boss = base.cr.doId2do.get(bossCogId)

    def setIndex(self, index):
        self.index = index

    def setState(self, state):
        if state == 'F':
            self.demand('Off')
        elif state == 'N':
            self.demand('On')
        elif state == 'I':
            self.demand('Inactive')
        elif state == 'T':
            self.demand('Toonup')
        else:
            self.notify.error('Invalid state from AI: %s' % state)

    def enterOn(self):
        self.beltSoundInterval.loop()
        for i in xrange(len(self.foodNodes)):
            self.doMethodLater(self.foodWaitTimes[i], self.startFoodMoving, 'start-%d-%d' % (self.index, i), extraArgs=[i])

    def exitOn(self):
        self.beltSoundInterval.finish()
        for i in xrange(len(self.foodNodes)):
            taskName = 'start-%d-%d' % (self.index, i)
            self.removeTask(taskName)

    def enterToonup(self):
        self.beltSound.setPlayRate(self.ToonupBeltSpeed / self.BeltSpeed)
        self.beltSoundInterval.loop()
        for i in xrange(len(self.foodNodes)):
            self.removeFood(i)
            self.beltActor.setPlayRate(self.ToonupBeltActorPlayRate, 'idle')
            self.doMethodLater(self.toonupWaitTimes[i], self.startToonupMoving, 'startToonup-%d-%d' % (self.index, i), extraArgs=[i])

    def exitToonup(self):
        self.beltSoundInterval.finish()
        for i in xrange(len(self.foodNodes)):
            taskName = 'startToonup-%d-%d' % (self.index, i)
            self.removeTask(taskName)

    def enterInactive(self):
        for ival in self.foodIvals:
            ival.finish()

        for ival in self.toonupIvals:
            ival.finish()

        for i in xrange(len(self.foodNodes)):
            self.removeFood(i)
            self.removeToonup(i)

        if self.beltActor:
            self.beltActor.stop()

    def exitInactive(self):
        pass

    def startFoodMoving(self, foodIndex):
        if foodIndex < len(self.foodIvals):
            self.foodIvals[foodIndex].loop()
        else:
            self.notify.warning('startFoodMoving invalid index %d' % foodIndex)
        if self.beltActor:
            self.beltActor.loop('idle')

    def startToonupMoving(self, toonupIndex):
        if toonupIndex < len(self.toonupIvals):
            self.toonupIvals[toonupIndex].loop()
        else:
            self.notify.warning('startToonupMoving invalid index %d' % toonupIndex)
        if self.beltActor:
            self.beltActor.loop('idle')

    def loadAssets(self):
        self.beltModel = NodePath('beltModel')
        self.beltModel.reparentTo(self.boss.geom)
        self.startLocator = self.boss.geom.find('**/conveyer_belt_start_%d' % (self.index + 1))
        self.endLocator = self.boss.geom.find('**/conveyer_belt_end_%d' % (self.index + 1))
        center = (self.startLocator.getPos() + self.endLocator.getPos()) / 2.0
        self.beltHeight = center.getZ()
        self.beltHeight += 0.1
        center.setZ(0)
        self.beltLength = (self.endLocator.getPos() - self.startLocator.getPos()).length()
        self.distBetweenFoodNodes = self.beltLength / self.NumFoodNodes
        self.notify.debug('setting beltModelPos to %s' % center)
        self.beltModel.setPos(center)
        self.setupFoodNodes()
        self.setupFoodIvals()
        self.setupToonupIvals()
        if self.index == 0:
            self.beltActorModel = loader.loadModel('phase_12/models/bossbotHQ/food_belt1_model')
        else:
            self.beltActorModel = loader.loadModel('phase_12/models/bossbotHQ/food_belt2_model')
        if self.beltActorModel:
            self.beltActor = Actor.Actor(self.beltActorModel)
            if self.index == 0:
                self.beltActor.loadAnims({'idle': 'phase_12/models/bossbotHQ/food_belt1'})
            else:
                self.beltActor.loadAnims({'idle': 'phase_12/models/bossbotHQ/food_belt2'})
            self.beltActor.reparentTo(render)
            self.beltActor.setPlayRate(self.BeltActorPlayRate, 'idle')
            mesh = self.beltActor.find('**/mesh_tide1')
            joint = self.beltActor.find('**/uvj_WakeWhiteTide1')
            mesh.setTexProjector(mesh.findTextureStage('default'), joint, self.beltActor)
            self.beltActor.setPos(self.startLocator.getPos())
        self.beltSound = base.loadSfx('phase_12/audio/sfx/CHQ_FACT_conveyor_belt.wav')
        self.beltSound.setLoop(1)
        self.beltSoundInterval = SoundInterval(self.beltSound, node=self.beltModel, listenerNode=base.localAvatar, seamlessLoop=True, volume=0.25, cutOff=100)

    def cleanup(self):
        for i in xrange(len(self.foodNodes)):
            taskName = 'start-%d-%d' % (self.index, i)
            self.removeTask(taskName)

        for i in xrange(len(self.foodNodes)):
            taskName = 'startToonup-%d-%d' % (self.index, i)
            self.removeTask(taskName)

        for ival in self.foodIvals:
            ival.finish()

        self.foodIvals = []
        for ival in self.toonupIvals:
            ival.finish()

        self.toonupIvals = []
        self.beltSoundInterval.finish()
        self.beltActor.delete()
        self.beltModel = None
        self.removeAllTasks()
        self.ignoreAll()
        return

    def setupFoodNodes(self):
        for i in xrange(self.NumFoodNodes):
            newPosIndex = self.NumFoodNodes - 1 - i
            yPos = -(self.beltLength / 2.0) + newPosIndex * self.distBetweenFoodNodes
            newFoodNode = NodePath('foodNode-%d-%d' % (self.index, i))
            newFoodNode.reparentTo(self.beltModel)
            newFoodNode.setPos(0, yPos, self.beltHeight)
            debugFood = None
            if debugFood:
                debugFood.setScale(0.1)
                debugFood.reparentTo(newFoodNode)
            newFoodNode.setH(180)
            self.foodNodes.append(newFoodNode)

        return

    def setupFoodIvals(self):
        for i in xrange(len(self.foodNodes)):
            foodIval = self.createOneFoodIval(self.foodNodes[i])
            self.foodIvals.append(foodIval)

    def createOneFoodIval(self, foodNode):
        foodIndex = self.foodNodes.index(foodNode)
        waitTimeForOne = self.distBetweenFoodNodes / self.BeltSpeed
        waitTime = waitTimeForOne * foodIndex
        self.foodWaitTimes.append(waitTime)
        totalTimeToTraverseBelt = self.beltLength / self.BeltSpeed
        startPosY = -(self.beltLength / 2.0)
        endPosY = self.beltLength / 2.0
        retval = Sequence(Func(self.loadFood, foodIndex), LerpPosInterval(foodNode, duration=totalTimeToTraverseBelt, startPos=Point3(0, startPosY, self.beltHeight), pos=Point3(0, endPosY, self.beltHeight)), ProjectileInterval(foodNode, startPos=Point3(0, endPosY, self.beltHeight), startVel=Point3(0, self.BeltSpeed, 0), endZ=0), Func(self.removeFood, foodIndex))
        return retval

    def loadFood(self, foodIndex):
        self.foodNum += 1
        if foodIndex in self.foodModelDict:
            foodModel = self.foodModelDict[foodIndex]
            foodModel.reparentTo(self.foodNodes[foodIndex])
            colNp = foodModel.find('**/FoodCol*')
            colNp.setTag('foodNum', str(self.foodNum))
        else:
            foodModelScale = ToontownGlobals.BossbotFoodModelScale
            foodModel = loader.loadModel('phase_12/models/bossbotHQ/canoffood')
            foodModel.setScale(foodModelScale)
            foodModel.reparentTo(self.foodNodes[foodIndex])
            target = CollisionTube(4, 0, 0, -4, 0, 0, 2)
            target.setTangible(0)
            colName = 'FoodCol-%d-%d' % (self.index, foodIndex)
            targetNode = CollisionNode(colName)
            targetNode.addSolid(target)
            targetNode.setCollideMask(ToontownGlobals.WallBitmask)
            targetNodePath = foodModel.attachNewNode(targetNode)
            targetNodePath.setScale(1.0 / foodModelScale)
            targetNodePath.setTag('foodIndex', str(foodIndex))
            targetNodePath.setTag('beltIndex', str(self.index))
            targetNodePath.setTag('foodNum', str(self.foodNum))
            targetNodePath.setZ(targetNodePath.getZ() - 1.5)
            self.accept('enter' + colName, self.touchedFood)
            self.foodModelDict[foodIndex] = foodModel

    def removeFood(self, foodIndex):
        if foodIndex in self.foodModelDict:
            foodModel = self.foodModelDict[foodIndex]
            foodModel.stash()

    def touchedFood(self, colEntry):
        into = colEntry.getIntoNodePath()
        try:
            beltIndex = int(into.getTag('beltIndex'))
        except:
            beltIndex = 0

        try:
            foodIndex = int(into.getTag('foodIndex'))
        except:
            foodIndex = 0

        try:
            foodNum = int(into.getTag('foodNum'))
        except:
            foodNum = 0

        if self.boss:
            self.boss.localToonTouchedBeltFood(beltIndex, foodIndex, foodNum)

    def setupToonupIvals(self):
        for i in xrange(len(self.foodNodes)):
            toonupIval = self.createOneToonupIval(self.foodNodes[i])
            self.toonupIvals.append(toonupIval)

    def createOneToonupIval(self, foodNode):
        toonupIndex = self.foodNodes.index(foodNode)
        waitTimeForOne = self.distBetweenFoodNodes / self.ToonupBeltSpeed
        waitTime = waitTimeForOne * toonupIndex
        self.toonupWaitTimes.append(waitTime)
        totalTimeToTraverseBelt = self.beltLength / self.ToonupBeltSpeed
        startPosY = -(self.beltLength / 2.0)
        endPosY = self.beltLength / 2.0
        retval = Sequence(Func(self.loadToonup, toonupIndex), LerpPosInterval(foodNode, duration=totalTimeToTraverseBelt, startPos=Point3(0, startPosY, self.beltHeight), pos=Point3(0, endPosY, self.beltHeight)), ProjectileInterval(foodNode, startPos=Point3(0, endPosY, self.beltHeight), startVel=Point3(0, self.BeltSpeed, 0), endZ=0), Func(self.removeToonup, toonupIndex))
        return retval

    def loadToonup(self, toonupIndex):
        self.toonupNum += 1
        if toonupIndex in self.toonupModelDict:
            toonupModel = self.toonupModelDict[toonupIndex]
            toonupModel.reparentTo(self.foodNodes[toonupIndex])
            colNp = toonupModel.find('**/ToonupCol*')
            colNp.setTag('toonupNum', str(self.toonupNum))
        else:
            toonupModelScale = self.ToonupScales[toonupIndex]
            modelName = self.ToonupModels[toonupIndex]
            toonupModel = loader.loadModel(modelName)
            self.foodNodes[toonupIndex].setZ(self.beltHeight - 0.1)
            toonupModel.setZ(self.ToonupZOffsets[toonupIndex])
            toonupModel.setScale(toonupModelScale)
            toonupModel.reparentTo(self.foodNodes[toonupIndex])
            target = CollisionTube(4, 0, 0, -4, 0, 0, 2)
            target.setTangible(0)
            colName = 'ToonupCol-%d-%d' % (self.index, toonupIndex)
            targetNode = CollisionNode(colName)
            targetNode.addSolid(target)
            targetNode.setCollideMask(ToontownGlobals.WallBitmask)
            targetNodePath = toonupModel.attachNewNode(targetNode)
            targetNodePath.setScale(1.0 / toonupModelScale)
            targetNodePath.setTag('toonupIndex', str(toonupIndex))
            targetNodePath.setTag('beltIndex', str(self.index))
            targetNodePath.setTag('toonupNum', str(self.toonupNum))
            targetNodePath.setZ(targetNodePath.getZ() - 1.5 / toonupModelScale)
            self.accept('enter' + colName, self.touchedToonup)
            self.toonupModelDict[toonupIndex] = toonupModel

    def removeToonup(self, toonupIndex):
        if toonupIndex in self.toonupModelDict:
            toonupModel = self.toonupModelDict[toonupIndex]
            toonupModel.stash()

    def touchedToonup(self, colEntry):
        if base.localAvatar.hp >= base.localAvatar.maxHp:
            return
        into = colEntry.getIntoNodePath()
        try:
            beltIndex = int(into.getTag('beltIndex'))
        except:
            beltIndex = 0

        try:
            toonupIndex = int(into.getTag('toonupIndex'))
        except:
            toonupIndex = 0

        try:
            toonupNum = int(into.getTag('toonupNum'))
        except:
            toonupNum = 0

        if self.boss:
            self.boss.localToonTouchedBeltToonup(beltIndex, toonupIndex, toonupNum)
