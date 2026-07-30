from otp.ai.AIBase import *
from direct.interval.IntervalGlobal import *
from direct.directnotify import DirectNotifyGlobal
from direct.distributed import ClockDelta
from direct.task import Task
from otp.level import DistributedEntityAI
from otp.level import BasicEntities
from direct.directnotify import DirectNotifyGlobal
from toontown.coghq import BattleBlockerAI
from toontown.coghq import LaserGameMineSweeper
from toontown.coghq import LaserGameRoll
from toontown.coghq import LaserGameAvoid
from toontown.coghq import LaserGameDrag
import random

class DistributedLaserFieldAI(BattleBlockerAI.BattleBlockerAI, NodePath, BasicEntities.NodePathAttribs):

    def __init__(self, level, entId):
        BattleBlockerAI.BattleBlockerAI.__init__(self, level, entId)
        node = hidden.attachNewNode('DistributedLaserFieldAI')
        NodePath.__init__(self, node)
        if not hasattr(self, 'switchId'):
            self.switchId = 0
        self.gridScale = 1
        self.game = LaserGameRoll.LaserGameRoll(self.trapDisable, self.trapFire, self.sendField, self.setGrid)
        if not hasattr(self, 'gridGame'):
            self.gridGame = 'Roll'
        self.enabled = 1
        self.hasShownSuits = 0
        self.healReady = 1
        self.playedSound = 0
        self.canButton = 1
        self.title = 'MemTag: This is a laserField %s' % random.random()

    def setGridGame(self, gameName):
        if gameName == 'Random':
            gameName = random.choice(['MineSweeper', 'Roll', 'Avoid', 'Drag'])
        self.gridGame = gameName
        if hasattr(self, 'game'):
            self.game.delete()
            self.game = None
        if gameName == 'Drag':
            self.game = LaserGameDrag.LaserGameDrag(self.trapDisable, self.trapFire, self.sendField, self.setGrid)
        else:
            if gameName == 'MineSweeper':
                self.game = LaserGameMineSweeper.LaserGameMineSweeper(self.trapDisable, self.trapFire, self.sendField, self.setGrid)
            else:
                if gameName == 'Roll':
                    self.game = LaserGameRoll.LaserGameRoll(self.trapDisable, self.trapFire, self.sendField, self.setGrid)
                else:
                    if gameName == 'Avoid':
                        self.game = LaserGameAvoid.LaserGameAvoid(self.trapDisable, self.trapFire, self.sendField, self.setGrid)
                    else:
                        self.game = LaserGameMineSweeper.LaserGameMineSweeper(self.trapDisable, self.trapFire, self.sendField, self.setGrid)
        self.game.startGrid()
        self.sendField()
        self.sendUpdate('setGridGame', [gameName])
        return

    def generate(self):
        BattleBlockerAI.BattleBlockerAI.generate(self)
        if self.switchId != 0:
            self.accept(self.getOutputEventName(self.switchId), self.reactToSwitch)
        self.detectName = 'laserField %s' % self.doId
        taskMgr.doMethodLater(1.0, self.__detect, self.detectName)
        self.setPos(self.pos)
        self.setHpr(self.hpr)
        self.setGridGame(self.gridGame)

    def registerBlocker(self):
        BattleBlockerAI.BattleBlockerAI.registerBlocker(self)
        self.hideSuits()

    def delete(self):
        taskMgr.remove(self.detectName)
        self.ignoreAll()
        self.game.delete()
        self.game = None
        BattleBlockerAI.BattleBlockerAI.delete(self)
        return

    def destroy(self):
        self.notify.info('destroy entity(laserField) %s' % self.entId)
        BattleBlockerAI.BattleBlockerAI.destroy(self)

    def setGrid(self, gridNumX, gridNumY):
        self.game.setGridSize(gridNumX, gridNumY)

    def getGrid(self):
        return (
         self.game.gridNumX, self.game.gridNumY)

    def getField(self):
        fieldData = []
        fieldData.append(self.game.gridNumX)
        fieldData.append(self.game.gridNumY)
        for column in range(0, self.game.gridNumX):
            for row in range(0, self.game.gridNumY):
                fieldData.append(self.game.gridData[column][row])

        return fieldData

    def sendField(self):
        self.sendUpdate('setField', [self.getField()])

    def __detect(self, task):
        isThereAnyToons = False
        if hasattr(self, 'level'):
            toonInRange = 0
            for avId in self.level.presentAvIds:
                if avId in self.air.doId2do:
                    av = self.air.doId2do[avId]
                    isThereAnyToons = True
                    distance = self.getDistance(av)

            if isThereAnyToons:
                taskMgr.doMethodLater(1.0, self.__detect, self.detectName)
                self.__run()
        return Task.done

    def hit(self, hitX, hitY, oldX, oldY):
        if self.enabled:
            self.game.hit(hitX, hitY, oldX, oldY)

    def __run(self):
        pass

    def __toonHit(self):
        self.gridNumX = random.randint(1, 4)
        self.gridNumY = random.randint(1, 4)
        self.gridScale = random.randint(1, 4)
        self.sendUpdate('setGrid', [self.gridNumX, self.gridNumY, self.gridScale])

    def reactToSwitch(self, on):
        if on and self.canButton:
            self.trapDisable()
            self.game.win()

    def trapFire(self):
        if not self.enabled:
            return
        self.enabled = 0
        self.game.lose()
        self.showSuits()
        stage = self.air.getDo(self.level.stageDoId)
        stage.resetPuzzelReward()
        self.healReady = 0
        if not __dev__ and 1:
            self.canButton = 0
        self.sendUpdate('setActiveLF', [0])
        if not self.playedSound:
            self.sendUpdate('setSuccess', [0])
        self.playedSound = 1

    def setBattleFinished(self):
        print('battle Finished')
        BattleBlockerAI.BattleBlockerAI.setBattleFinished(self)
        messenger.send(self.getOutputEventName(), [1])
        self.switchFire()

    def switchFire(self):
        print('switchFire')
        if self.switchId != 0:
            switch = self.level.getEntity(self.switchId)
            if switch:
                switch.setIsOn(1)

    def trapDisable(self):
        if not self.enabled:
            return
        self.enabled = 0
        suits = self.level.planner.battleCellId2suits.get(self.cellId)
        messenger.send(self.getOutputEventName(), [1])
        if self.hasShownSuits == 0:
            for suit in suits:
                suit.requestRemoval()

        self.sendUpdate('setActiveLF', [0])
        stage = self.air.getDo(self.level.stageDoId)
        reward = stage.getPuzzelReward()
        if self.healReady:
            for avId in self.level.presentAvIds:
                av = self.air.doId2do.get(avId)
                if av:
                    av.toonUp(reward)

            stage.increasePuzzelReward()
        self.healReady = 0
        if not self.playedSound:
            self.sendUpdate('setSuccess', [1])
        self.playedSound = 1
        self.switchFire()

    def hideSuits(self):
        suits = self.level.planner.battleCellId2suits.get(self.cellId)
        suitArray = []
        for suit in suits:
            suitArray.append(suit.doId)

        if suitArray:
            self.sendUpdate('hideSuit', [suitArray])

    def showSuits(self):
        if self.hasShownSuits == 0:
            suits = self.level.planner.battleCellId2suits.get(self.cellId)
            suitArray = []
            for suit in suits:
                suit.setVirtual()
                suitArray.append(suit.doId)

            if suitArray:
                self.sendUpdate('showSuit', [suitArray])
        self.hasShownSuits = 1

    def addSuit(self, suit):
        print('Adding Suit %s' % suit.doId)
        BattleBlockerAI.BattleBlockerAI.addSuit(self, suit)
