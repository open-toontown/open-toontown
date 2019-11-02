from pandac.PandaModules import *
from direct.showbase import DirectObject
from direct.fsm import ClassicFSM, State
from toontown.toonbase import ToontownGlobals
from toontown.coghq import StageRoomSpecs
import random

class StageRoom(DirectObject.DirectObject):
    FloorCollPrefix = 'stageFloorColl'
    CashbotStageDoorFrame = 'phase_10/models/cashbotHQ/DoorFrame'

    def __init__(self, path = None):
        if path is not None:
            if path in StageRoomSpecs.CashbotStageConnectorRooms:
                loadFunc = loader.loadModelCopy
            else:
                loadFunc = loader.loadModel
            self.setGeom(loadFunc(path))
        self.localToonFSM = ClassicFSM.ClassicFSM('StageRoomLocalToonPresent', [State.State('off', self.enterLtOff, self.exitLtOff, ['notPresent']), State.State('notPresent', self.enterLtNotPresent, self.exitLtNotPresent, ['present']), State.State('present', self.enterLtPresent, self.exitLtPresent, ['notPresent'])], 'notPresent', 'notPresent')
        self.localToonFSM.enterInitialState()
        return

    def delete(self):
        del self.localToonFSM

    def enter(self):
        self.localToonFSM.request('notPresent')

    def exit(self):
        self.localToonFSM.requestFinalState()

    def setRoomNum(self, num):
        self.roomNum = num

    def getRoomNum(self):
        return self.roomNum

    def setGeom(self, geom):
        self.__geom = geom
        ug = self.__geom.find('**/underground')
        if not ug.isEmpty():
            ug.setBin('ground', -10)

    def getGeom(self):
        return self.__geom

    def _getEntrances(self):
        return self.__geom.findAllMatches('**/ENTRANCE*')

    def _getExits(self):
        return self.__geom.findAllMatches('**/EXIT*')

    def attachTo(self, other, rng):
        otherExits = other._getExits()
        entrances = self._getEntrances()
        otherDoor = otherExits[0]
        thisDoor = rng.choice(entrances)
        geom = self.getGeom()
        otherGeom = other.getGeom()
        tempNode = otherDoor.attachNewNode('tempRotNode')
        geom.reparentTo(tempNode)
        geom.clearMat()
        geom.setPos(Vec3(0) - thisDoor.getPos(geom))
        tempNode.setH(-thisDoor.getH(otherDoor))
        geom.wrtReparentTo(otherGeom.getParent())
        tempNode.removeNode()

    def getFloorCollName(self):
        return '%s%s' % (StageRoom.FloorCollPrefix, self.roomNum)

    def initFloorCollisions(self):
        allColls = self.getGeom().findAllMatches('**/+CollisionNode')
        floorColls = []
        for coll in allColls:
            bitmask = coll.node().getIntoCollideMask()
            if not (bitmask & ToontownGlobals.FloorBitmask).isZero():
                floorColls.append(coll)

        if len(floorColls) > 0:
            floorCollName = self.getFloorCollName()
            others = self.getGeom().findAllMatches('**/%s' % floorCollName)
            for other in others:
                other.setName('%s_renamed' % floorCollName)

            for floorColl in floorColls:
                floorColl.setName(floorCollName)

    def enterLtOff(self):
        pass

    def exitLtOff(self):
        pass

    def enterLtNotPresent(self):
        pass

    def exitLtNotPresent(self):
        pass

    def enterLtPresent(self):
        pass

    def exitLtPresent(self):
        pass
