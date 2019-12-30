import random
from direct.distributed import DistributedObjectAI
from direct.fsm import FSM
from direct.directnotify import DirectNotifyGlobal
from toontown.coghq import BanquetTableBase
from toontown.toonbase import ToontownGlobals

class DistributedBanquetTableAI(DistributedObjectAI.DistributedObjectAI, FSM.FSM, BanquetTableBase.BanquetTableBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedBanquetTableAI')

    def __init__(self, air, boss, index, numDiners, dinerLevel):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        FSM.FSM.__init__(self, 'DistributedBanquetTableAI')
        self.boss = boss
        self.index = index
        self.numDiners = numDiners
        self.numChairs = 8
        self.dinerStatus = {}
        self.dinerInfo = {}
        for i in range(self.numDiners):
            self.dinerStatus[i] = self.INACTIVE
            diffSettings = ToontownGlobals.BossbotBossDifficultySettings[self.boss.battleDifficulty]
            hungryDuration = diffSettings[4]
            eatingDuration = diffSettings[5]
            hungryDuration += random.uniform(-5, 5)
            eatingDuration += random.uniform(-5, 5)
            level = 12
            if type(dinerLevel) == type(0):
                level = dinerLevel
            else:
                level = random.choice(dinerLevel)
            self.dinerInfo[i] = (hungryDuration, eatingDuration, level)

        self.transitionTasks = {}
        self.numFoodEaten = {}
        self.avId = 0

    def delete(self):
        DistributedObjectAI.DistributedObjectAI.delete(self)

    def getBossCogId(self):
        return self.boss.doId

    def getIndex(self):
        return self.index

    def getNumDiners(self):
        return self.numDiners

    def getDinerStatus(self, chairIndex):
        retval = self.DEAD
        if chairIndex in self.dinerStatus:
            retval = self.dinerStatus[chairIndex]
        return retval

    def setDinerStatus(self, chairIndex, newStatus):
        self.dinerStatus[chairIndex] = newStatus

    def getDinerInfo(self):
        hungryDurations = []
        eatingDurations = []
        dinerLevels = []
        for i in range(self.numDiners):
            hungryDurations.append(self.dinerInfo[i][0])
            eatingDurations.append(self.dinerInfo[i][1])
            dinerLevels.append(self.dinerInfo[i][2])

        return (hungryDurations, eatingDurations, dinerLevels)

    def d_setDinerStatus(self, chairIndex, newStatus):
        self.sendUpdate('setDinerStatus', [chairIndex, newStatus])

    def b_setDinerStatus(self, chairIndex, newStatus):
        self.setDinerStatus(chairIndex, newStatus)
        self.d_setDinerStatus(chairIndex, newStatus)

    def setState(self, state):
        self.request(state)

    def d_setState(self, state, avId=0, extraInfo=0):
        newState = state
        if state == 'On':
            newState = 'N'
        else:
            if state == 'Off':
                newState = 'F'
            else:
                if state == 'Inactive':
                    newState = 'I'
                else:
                    if state == 'Free':
                        newState = 'R'
                    else:
                        if state == 'Controlled':
                            newState = 'C'
                        else:
                            if state == 'Flat':
                                newState = 'L'
        self.sendUpdate('setState', [newState, avId, extraInfo])

    def b_setState(self, state, avId=0, extraInfo=0):
        if state == 'Controlled' or state == 'Flat':
            self.request(state, avId)
        else:
            self.request(state)
        self.d_setState(state, avId, extraInfo)

    def turnOn(self):
        self.b_setState('On')

    def turnOff(self):
        self.b_setState('Off')

    def foodServed(self, chairIndex):
        self.b_setDinerStatus(chairIndex, self.EATING)
        eatingDur = self.dinerInfo[chairIndex][1]
        if chairIndex in self.transitionTasks:
            self.removeTask(self.transitionTasks[chairIndex])
        taskName = self.uniqueName('transition-%d' % chairIndex)
        newTask = self.doMethodLater(eatingDur, self.finishedEating, taskName, extraArgs=[chairIndex])
        self.transitionTasks[chairIndex] = newTask

    def finishedEating(self, chairIndex):
        if chairIndex in self.transitionTasks:
            self.removeTask(self.transitionTasks[chairIndex])
        self.incrementFoodEaten(chairIndex)
        if self.numFoodEaten[chairIndex] >= ToontownGlobals.BossbotNumFoodToExplode:
            self.b_setDinerStatus(chairIndex, self.DEAD)
            self.boss.incrementDinersExploded()
        else:
            self.b_setDinerStatus(chairIndex, self.HUNGRY)
            taskName = self.uniqueName('transition-%d' % chairIndex)
            hungryDur = self.dinerInfo[chairIndex][0]
            newTask = self.doMethodLater(hungryDur, self.finishedHungry, taskName, extraArgs=[chairIndex])
            self.transitionTasks[chairIndex] = newTask

    def incrementFoodEaten(self, chairIndex):
        numFood = 0
        if chairIndex in self.numFoodEaten:
            numFood = self.numFoodEaten[chairIndex]
        self.numFoodEaten[chairIndex] = numFood + 1

    def finishedHungry(self, chairIndex):
        self.b_setDinerStatus(chairIndex, self.ANGRY)
        self.numFoodEaten[chairIndex] = 0
        if chairIndex in self.transitionTasks:
            self.removeTask(self.transitionTasks[chairIndex])

    def goInactive(self):
        self.b_setState('Inactive')

    def goFree(self):
        self.b_setState('Free')

    def goFlat(self):
        self.b_setState('Flat', self.avId)

    def getNotDeadInfo(self):
        notDeadList = []
        for i in range(self.numDiners):
            if self.dinerStatus[i] != self.DEAD:
                notDeadList.append((self.index, i, self.dinerInfo[i][2]))

        return notDeadList

    def requestControl(self):
        avId = self.air.getAvatarIdFromSender()
        if avId in self.boss.involvedToons and self.avId == 0 and self.state == 'Free':
            tableId = self.__getTableId(avId)
            if tableId == 0:
                grantRequest = True
                if self.boss and not self.boss.isToonRoaming(avId):
                    grantRequest = False
                if grantRequest:
                    self.b_setState('Controlled', avId)

    def forceControl(self, avId):
        self.notify.debug('forceContrl  tableIndex=%d avId=%d' % (self.index, avId))
        tableId = self.__getTableId(avId)
        if tableId == self.doId:
            if self.state == 'Flat':
                self.b_setState('Controlled', avId)
            else:
                self.notify.warning('invalid forceControl from state %s' % self.state)
        else:
            self.notify.warning('tableId %d  != self.doId %d ' % (tableId, self.doId))

    def requestFree(self, gotHitByBoss):
        avId = self.air.getAvatarIdFromSender()
        if avId == self.avId:
            if self.state == 'Controlled':
                self.b_setState('Free', extraInfo=gotHitByBoss)
                if self.boss:
                    self.boss.toonLeftTable(self.index)
            else:
                self.notify.debug('requestFree denied in state %s' % self.state)

    def __getTableId(self, avId):
        if self.boss and self.boss.tables != None:
            for table in self.boss.tables:
                if table.avId == avId:
                    return table.doId

        return 0

    def enterOn(self):
        for i in range(self.numDiners):
            self.b_setDinerStatus(i, self.HUNGRY)

    def exitOn(slef):
        pass

    def enterOff(self):
        pass

    def exitOff(self):
        pass

    def enterInactive(self):
        for task in list(self.transitionTasks.values()):
            self.removeTask(task)

        self.transitionTasks = {}

    def exitInactive(self):
        pass

    def enterFree(self):
        self.notify.debug('enterFree tableIndex=%d' % self.index)
        self.avId = 0

    def exitFree(self):
        pass

    def enterControlled(self, avId):
        self.notify.debug('enterControlled tableIndex=%d' % self.index)
        self.avId = avId

    def exitControlled(self):
        pass

    def enterFlat(self, avId):
        self.notify.debug('enterFlat tableIndex=%d' % self.index)

    def exitFlat(self):
        pass
