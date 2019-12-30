from direct.distributed import DistributedObjectAI
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals
from pandac.PandaModules import *
from . import BuildGeometry
import random, time
from math import *
import math
from toontown.golf import PhysicsWorldBase

class DistributedPhysicsWorldAI(DistributedObjectAI.DistributedObjectAI, PhysicsWorldBase.PhysicsWorldBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedPhysicsWorldAI')

    def __init__(self, air):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        PhysicsWorldBase.PhysicsWorldBase.__init__(self, 0)
        self.commonHoldData = None
        self.storeAction = None
        self.holdingUpObjectData = 0
        return

    def generate(self):
        DistributedObjectAI.DistributedObjectAI.generate(self)
        self.loadLevel()
        self.setupSimulation()

    def delete(self):
        self.notify.debug('Calling DistributedObjectAI.delete')
        DistributedObjectAI.DistributedObjectAI.delete(self)
        self.notify.debug('Calling PhysicsWorldBase.delete')
        PhysicsWorldBase.PhysicsWorldBase.delete(self)

    def loadLevel(self):
        pass

    def createCommonObject(self, type, pos, hpr, sizeX = 0, sizeY = 0, moveDistance = 0):
        commonObjectDatam = PhysicsWorldBase.PhysicsWorldBase.createCommonObject(self, type, None, pos, hpr, sizeX, sizeY, moveDistance)
        self.sendUpdate('clientCommonObject', commonObjectDatam)
        return

    def updateCommonObjects(self):
        self.sendUpdate('setCommonObjects', [self.getCommonObjectData()])

    def doAction(self):
        print('doing Action')
        print('before performReadyAction')
        self.performReadyAction()
        self.storeAction = None
        self.commonHoldData = None
        return

    def upSetCommonObjects(self, objectData):
        self.holdingUpObjectData = 1
        self.commonHoldData = objectData
        if self.storeAction:
            self.doAction()

    def setupCommonObjects(self):
        print('setupCommonObjects')
        print(self.commonHoldData)
        if not self.commonHoldData:
            return
        elif self.commonHoldData[0][1] == 99:
            print('no common objects')
        else:
            self.useCommonObjectData(self.commonHoldData, 0)

    def performReadyAction(self):
        print('Wrong performReadyAction')
