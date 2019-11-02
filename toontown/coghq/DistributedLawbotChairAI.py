from direct.directnotify import DirectNotifyGlobal
from pandac.PandaModules import *
from direct.distributed import DistributedObjectAI
from toontown.toonbase import ToontownGlobals
from otp.otpbase import OTPGlobals
from direct.fsm import FSM
import random

class DistributedLawbotChairAI(DistributedObjectAI.DistributedObjectAI, FSM.FSM):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedLawbotChairAI')

    def __init__(self, air, boss, index):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        FSM.FSM.__init__(self, 'DistributedLawbotBossChairAI')
        self.boss = boss
        self.index = index
        cn = CollisionNode('controls')
        cs = CollisionSphere(0, -6, 0, 6)
        cn.addSolid(cs)
        self.goonShield = NodePath(cn)
        self.goonShield.setPosHpr(*ToontownGlobals.LawbotBossChairPosHprs[self.index])
        self.avId = 0
        self.objectId = 0
        self.changeToCogTask = None
        self.startCogFlyTask = None
        self.toonJurorIndex = -1
        return

    def delete(self):
        self.ignoreAll()
        DistributedObjectAI.DistributedObjectAI.delete(self)
        taskName = self.uniqueName('startCogFlyTask')
        taskMgr.remove(taskName)
        changeTaskName = self.uniqueName('changeToCogJuror')
        taskMgr.remove(changeTaskName)

    def stopCogs(self):
        taskName = self.uniqueName('startCogFlyTask')
        taskMgr.remove(taskName)
        changeTaskName = self.uniqueName('changeToCogJuror')
        taskMgr.remove(changeTaskName)

    def getBossCogId(self):
        return self.boss.doId

    def getIndex(self):
        return self.index

    def getToonJurorIndex(self):
        return self.toonJurorIndex

    def setToonJurorIndex(self, newVal):
        self.toonJurorIndex = newVal

    def b_setToonJurorIndex(self, newVal):
        self.setToonJurorIndex(newVal)
        self.d_setToonJurorIndex(newVal)

    def d_setToonJurorIndex(self, newVal):
        self.sendUpdate('setToonJurorIndex', [newVal])

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
                if state == 'ToonJuror':
                    newState = 'T'
                else:
                    if state == 'SuitJuror':
                        newState = 'S'
                    else:
                        if state == 'EmptyJuror':
                            newState = 'E'
                        else:
                            if state == 'StopCogs':
                                newState = 'C'
        self.sendUpdate('setState', [newState])

    def b_setState(self, state):
        self.request(state)
        self.d_setState(state)

    def turnOn(self):
        self.b_setState('On')

    def requestStopCogs(self):
        self.b_setState('StopCogs')

    def requestControl(self):
        avId = self.air.getAvatarIdFromSender()
        if avId in self.boss.involvedToons and self.avId == 0:
            craneId = self.__getCraneId(avId)
            if craneId == 0:
                self.request('Controlled', avId)

    def requestFree(self):
        avId = self.air.getAvatarIdFromSender()
        if avId == self.avId:
            self.request('Free')

    def removeToon(self, avId):
        if avId == self.avId:
            self.request('Free')

    def __getCraneId(self, avId):
        if self.boss and self.boss.cranes != None:
            for crane in self.boss.cranes:
                if crane.avId == avId:
                    return crane.doId

        return 0

    def requestToonJuror(self):
        self.b_setState('ToonJuror')
        if self.changeToCogTask == None:
            if self.startCogFlyTask == None:
                delayTime = random.randrange(9, 19)
                self.startCogFlyTask = taskMgr.doMethodLater(delayTime, self.cogFlyAndSit, self.uniqueName('startCogFlyTask'))
        return

    def requestSuitJuror(self):
        self.b_setState('SuitJuror')

    def requestEmptyJuror(self):
        self.b_setState('EmptyJuror')
        delayTime = random.randrange(1, 20)
        self.startCogFlyTask = taskMgr.doMethodLater(delayTime, self.cogFlyAndSit, self.uniqueName('startCogFlyTask'))

    def cogFlyAndSit(self, taskName=None):
        self.notify.debug('cogFlyAndSit')
        self.sendUpdate('showCogJurorFlying', [])
        self.changeToCogTask = taskMgr.doMethodLater(ToontownGlobals.LawbotBossCogJurorFlightTime, self.changeToCogJuror, self.uniqueName('changeToCogJuror'))
        if self.startCogFlyTask:
            self.startCogFlyTask = None
        return

    def changeToCogJuror(self, task):
        self.notify.debug('changeToCogJuror')
        self.requestSuitJuror()
        self.changeToCogTask = None
        return

    def enterOn(self):
        pass

    def exitOn(slef):
        pass

    def enterOff(self):
        self.goonShield.detachNode()

    def exitOff(self):
        pass

    def enterControlled(self, avId):
        self.avId = avId
        self.d_setState('C')

    def exitControlled(self):
        if self.objectId:
            obj = self.air.doId2do[self.objectId]
            obj.request('Dropped', self.avId, self.doId)

    def enterFree(self):
        self.avId = 0
        self.d_setState('F')

    def exitFree(self):
        pass

    def enterToonJuror(self):
        pass

    def exitToonJuror(self):
        pass

    def enterStopCogs(self):
        self.__stopCogs()

    def exitStopCogs(self):
        pass
