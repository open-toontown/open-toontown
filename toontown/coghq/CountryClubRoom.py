from pandac.PandaModules import *
from direct.showbase import DirectObject
from direct.fsm import ClassicFSM, State
from toontown.toonbase import ToontownGlobals
from toontown.coghq import CountryClubRoomSpecs
from direct.directnotify import DirectNotifyGlobal
import random

class CountryClubRoom(DirectObject.DirectObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('CountryClubRoom')
    FloorCollPrefix = 'mintFloorColl'
    CashbotMintDoorFrame = 'phase_10/models/cashbotHQ/DoorFrame'

    def __init__(self, path = None):
        if path is not None:
            if path in CountryClubRoomSpecs.BossbotCountryClubConnectorRooms:
                loadFunc = loader.loadModelCopy
            else:
                loadFunc = loader.loadModel
            self.setGeom(loadFunc(path))
        self.localToonFSM = ClassicFSM.ClassicFSM('CountryClubRoomLocalToonPresent', [State.State('off', self.enterLtOff, self.exitLtOff, ['notPresent']), State.State('notPresent', self.enterLtNotPresent, self.exitLtNotPresent, ['present']), State.State('present', self.enterLtPresent, self.exitLtPresent, ['notPresent'])], 'notPresent', 'notPresent')
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
        if geom == None:
            import pdb
            pdb.set_trace()
        self.__geom = geom
        return

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
        self.notify.debug('thisDoor = %s' % thisDoor)
        self.notify.debug('otherDoor = %s' % otherDoor)
        self.notify.debug('thisGeom = %s' % geom)
        self.notify.debug('otherGeom = %s' % otherGeom)
        debugAxis1 = None
        if debugAxis1:
            debugAxis1.reparentTo(thisDoor)
        debugAxis2 = None
        if debugAxis2:
            debugAxis2.reparentTo(otherDoor)
            debugAxis2.setColorScale(0.5, 0.5, 0.5, 1)
        tempNode = otherDoor.attachNewNode('tempRotNode')
        geom.reparentTo(tempNode)
        geom.clearMat()
        newGeomPos = Vec3(0) - thisDoor.getPos(geom)
        self.notify.debug('newGeomPos = %s' % newGeomPos)
        geom.setPos(newGeomPos)
        newTempNodeH = -thisDoor.getH(otherDoor)
        self.notify.debug('newTempNodeH =%s' % newTempNodeH)
        tempNode.setH(newTempNodeH)
        geom.wrtReparentTo(otherGeom.getParent())
        tempNode.removeNode()
        return

    def getFloorCollName(self):
        return '%s%s' % (CountryClubRoom.FloorCollPrefix, self.roomNum)

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
