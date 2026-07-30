from direct.distributed import DistributedObjectAI
from direct.fsm import FSM
from direct.directnotify import DirectNotifyGlobal
from toontown.coghq import FoodBeltBase

class DistributedFoodBeltAI(DistributedObjectAI.DistributedObjectAI, FSM.FSM, FoodBeltBase.FoodBeltBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedFoodBeltAI')

    def __init__(self, air, boss, index):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        FSM.FSM.__init__(self, 'DistributedFoodBeltAI')
        self.boss = boss
        self.index = index

    def delete(self):
        DistributedObjectAI.DistributedObjectAI.delete(self)

    def getBossCogId(self):
        return self.boss.doId

    def getIndex(self):
        return self.index

    def setState(self, state):
        self.request(state)

    def d_setState(self, state):
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
                    if state == 'Toonup':
                        newState = 'T'
        self.sendUpdate('setState', [newState])

    def b_setState(self, state):
        self.request(state)
        self.d_setState(state)

    def turnOn(self):
        self.b_setState('On')

    def goInactive(self):
        self.b_setState('Inactive')

    def goToonup(self):
        self.b_setState('Toonup')

    def enterOn(self):
        pass

    def exitOn(slef):
        pass

    def enterOff(self):
        pass

    def exitOff(self):
        pass

    def enterInactive(self):
        pass

    def exitInactive(slef):
        pass
