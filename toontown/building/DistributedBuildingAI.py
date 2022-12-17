""" DistributedBuildingAI module: contains the DistributedBuildingAI
    class, the server side representation of a 'building'."""


from otp.ai.AIBaseGlobal import *
from direct.distributed.ClockDelta import *

import types
from direct.task.Task import Task
from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObjectAI
from direct.fsm import State
from direct.fsm import ClassicFSM, State
from toontown.toonbase.ToontownGlobals import ToonHall
from . import DistributedToonInteriorAI
from . import DistributedToonHallInteriorAI
from . import DistributedSuitInteriorAI
from . import DistributedDoorAI
from . import DoorTypes
from . import DistributedElevatorExtAI
from . import DistributedKnockKnockDoorAI
from . import SuitPlannerInteriorAI
from . import SuitBuildingGlobals
from . import FADoorCodes
from toontown.hood import ZoneUtil
import random
import time
from toontown.cogdominium.DistributedCogdoInteriorAI import DistributedCogdoInteriorAI
from toontown.cogdominium.SuitPlannerCogdoInteriorAI import SuitPlannerCogdoInteriorAI
from toontown.cogdominium.CogdoLayout import CogdoLayout
from toontown.cogdominium.DistributedCogdoElevatorExtAI import DistributedCogdoElevatorExtAI

class DistributedBuildingAI(DistributedObjectAI.DistributedObjectAI):
    """
    DistributedBuildingAI class:  The server side representation of a
    single building.  This is the object that remember who 'owns' the
    associated building (either the bad guys or the toons).  The child
    of this object, the DistributedBuilding object, is the client side
    version and updates the display that client's display based on who
    'owns' the building.
    """

    if __debug__:
        notify = DirectNotifyGlobal.directNotify.newCategory('DistributedBuildingAI')

    FieldOfficeNumFloors = 1

    def __init__(self, air, blockNumber, zoneId, trophyMgr):
        """blockNumber: the landmark building number (from the name)"""
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        self.block = blockNumber
        assert(self.debugPrint("DistributedBuildingAI(%s, %s)" % ("the air", str(blockNumber))))
        self.zoneId = zoneId
        self.canonicalZoneId = ZoneUtil.getCanonicalZoneId(zoneId)
        self.trophyMgr = trophyMgr
        self.victorResponses = None
        self.fsm = ClassicFSM.ClassicFSM('DistributedBuildingAI',
                           [State.State('off',
                                        self.enterOff,
                                        self.exitOff,
                                        ['waitForVictors',
                                         'becomingToon',
                                         'toon',
                                         'clearOutToonInterior',
                                         'becomingSuit',
                                         'suit',
                                         'clearOutToonInteriorForCogdo',
                                         'becomingCogdo',
                                         'becomingCogdoFromCogdo',
                                         'cogdo',
                                         ]),
                            State.State('waitForVictors',
                                        self.enterWaitForVictors,
                                        self.exitWaitForVictors,
                                        ['becomingToon',
                                         ]),
                            State.State('waitForVictorsFromCogdo',
                                        self.enterWaitForVictorsFromCogdo,
                                        self.exitWaitForVictorsFromCogdo,
                                        ['becomingToonFromCogdo',
                                         'becomingCogdoFromCogdo'
                                         ]),
                            State.State('becomingToon',
                                        self.enterBecomingToon,
                                        self.exitBecomingToon,
                                        ['toon']),
                            State.State('becomingToonFromCogdo',
                                        self.enterBecomingToonFromCogdo,
                                        self.exitBecomingToonFromCogdo,
                                        ['toon']),
                            State.State('toon',
                                        self.enterToon,
                                        self.exitToon,
                                        ['clearOutToonInterior', 'clearOutToonInteriorForCogdo']),
                            State.State('clearOutToonInterior',
                                        self.enterClearOutToonInterior,
                                        self.exitClearOutToonInterior,
                                        ['becomingSuit']),
                            State.State('becomingSuit',
                                        self.enterBecomingSuit,
                                        self.exitBecomingSuit,
                                        ['suit']),
                            State.State('suit',
                                        self.enterSuit,
                                        self.exitSuit,
                                        ['waitForVictors',
                                         'becomingToon',        # debug only
                                         ]),
                            State.State('clearOutToonInteriorForCogdo',
                                        self.enterClearOutToonInteriorForCogdo,
                                        self.exitClearOutToonInteriorForCogdo,
                                        ['becomingCogdo']),
                            State.State('becomingCogdo',
                                        self.enterBecomingCogdo,
                                        self.exitBecomingCogdo,
                                        ['cogdo']),
                            State.State('becomingCogdoFromCogdo',
                                        self.enterBecomingCogdoFromCogdo,
                                        self.exitBecomingCogdoFromCogdo,
                                        ['cogdo']),
                            State.State('cogdo',
                                        self.enterCogdo,
                                        self.exitCogdo,
                                        ['waitForVictorsFromCogdo',
                                         'becomingToonFromCogdo',        # debug only
                                         ])],
                           # Initial State
                           'off',
                           # Final State
                           'off',
                          )
        self.fsm.enterInitialState()
        self.track='c'
        self.difficulty=1
        self.numFloors=0
        self.savedBy=None
        self.becameSuitTime=0
        self.frontDoorPoint=None
        self.suitPlannerExt=None
        self.fSkipElevatorOpening = False

    def cleanup(self):
        if self.isDeleted():
            return
        
        self.fsm.requestFinalState()

        if hasattr(self, "interior"):
            self.interior.requestDelete()
            del self.interior

        if hasattr(self, "door"):
            self.door.requestDelete()
            del self.door
            self.insideDoor.requestDelete()
            del self.insideDoor
            self.knockKnock.requestDelete()
            del self.knockKnock

        if hasattr(self, "elevator"):
            self.elevator.requestDelete()
            del self.elevator

        self.requestDelete()
        

    def delete( self ):
        """
        ////////////////////////////////////////////////////////////////////
        // Function:   clean up tasks that might still be running for this
        //             building
        // Parameters:
        // Changes:
        ////////////////////////////////////////////////////////////////////
        """
        # make sure to remove any tasks we might have created
        taskMgr.remove(self.taskName('suitbldg-time-out'))

        # remove the doLater associated with the state transition of
        # a suit building becoming a toon building
        taskMgr.remove(self.taskName(str(self.block) + '_becomingToon-timer'))

        # remove the doLater associated with the state transition of
        # a toon building becoming a suit building
        taskMgr.remove(self.taskName(str(self.block) + '_becomingSuit-timer'))
        
        DistributedObjectAI.DistributedObjectAI.delete(self)
        
        del self.fsm

    def getPickleData(self):
        assert(self.debugPrint("getPickleData()"))
        pickleData={
            'state': str(self.fsm.getCurrentState().getName()),
            'block': str(self.block),
            'track': str(self.track),
            'difficulty': str(self.difficulty),
            'numFloors': str(self.numFloors),
            'savedBy': self.savedBy,
            'becameSuitTime' : self.becameSuitTime,
            }
        return pickleData

    def _getMinMaxFloors(self, difficulty):
        return SuitBuildingGlobals.SuitBuildingInfo[difficulty][0]
    
    def suitTakeOver(self, suitTrack, difficulty, buildingHeight):
        """Switch from toon to suit building
        suitTrack: one of 'c', 'l', 'm', or 's'
        difficulty: 0+
        buildingHeight: 0..4, or None to choose based on the difficulty.
        """
        if not self.isToonBlock():
            return
        assert(suitTrack in ['c', 'l', 'm', 's'])

        # Remove the old saved by credit with the old number of floors
        self.updateSavedBy(None)

        difficulty = min(difficulty, len(SuitBuildingGlobals.SuitBuildingInfo) - 1)
        minFloors, maxFloors = self._getMinMaxFloors(difficulty)
        if buildingHeight == None:
            # Pick a random floor number from the appropriate range.
            numFloors = random.randint(minFloors, maxFloors)
        else:
            # The number of floors is specified.
            numFloors = buildingHeight + 1

            if (numFloors < minFloors or numFloors > maxFloors):
                # Hmm, the number of floors is out of range for this
                # suit.  There must be an invasion in effect.  In that
                # case, go ahead and make a building of any height
                # appropriate to the suit.
                numFloors = random.randint(minFloors, maxFloors)

        assert(self.debugPrint("suitTakeOver(%s, %s, %s)" % (suitTrack, difficulty, numFloors - 1)))

        self.track=suitTrack
        self.difficulty=difficulty
        self.numFloors=numFloors
        self.becameSuitTime = time.time()
        self.fsm.request('clearOutToonInterior')

    def cogdoTakeOver(self, suitTrack, difficulty, buildingHeight):
        if not self.isToonBlock():
            return

        # Remove the old saved by credit with the old number of floors
        self.updateSavedBy(None)

        numFloors = self.FieldOfficeNumFloors

        assert(self.debugPrint("cogdoTakeOver(%s, %s)" % (difficulty, numFloors - 1)))

        self.track = suitTrack
        self.difficulty=difficulty
        self.numFloors=numFloors
        self.becameSuitTime = time.time()
        self.fsm.request('clearOutToonInteriorForCogdo')

    def toonTakeOver(self):
        """Switch from suit to toon building
        savedBy: a list of 1 to 4 avatar [name, style] lists."""
        assert(self.debugPrint("toonTakeOver(savedBy=%s)"%(self.savedBy)))
        isCogdo = 'cogdo' in self.fsm.getCurrentState().getName().lower()
        takenOver = True
        if isCogdo:
            if self.buildingDefeated:
                self.fsm.request('becomingToonFromCogdo')
            else:
                self.fsm.request('becomingCogdoFromCogdo')
                takenOver = False
        else:
            self.fsm.request('becomingToon')
        if takenOver and self.suitPlannerExt:
            self.suitPlannerExt.recycleBuilding(isCogdo)
        if hasattr(self, "interior"):
            self.interior.requestDelete()
            del self.interior
    
    def getFrontDoorPoint(self):
        """get any associated path point for this building, useful for
           suits to know where to go when exiting from a building"""
        assert(self.debugPrint("getFrontDoorPoint()"))
        return self.frontDoorPoint

    def setFrontDoorPoint(self, point):
        """set the associated front door point with this building"""
        assert(self.debugPrint("setFrontDoorPoint(%s)" % (str(point))))
        self.frontDoorPoint = point

    def getBlock(self):
        assert(self.debugPrint("getBlock()"))
        dummy, interiorZoneId = self.getExteriorAndInteriorZoneId()
        return [self.block, interiorZoneId]
        
    def getSuitData(self):
        assert(self.debugPrint("getSuitData()"))
        return [ord(self.track), self.difficulty, self.numFloors]
    
    def getState(self):
        assert(self.debugPrint("getState()"))
        return [self.fsm.getCurrentState().getName(),
                globalClockDelta.getRealNetworkTime()]
    
    def setState(self, state, timestamp=0):
        assert(self.notify.debug(str(self.block)+" setState(state="+str(state)+")"))
        self.fsm.request(state)
    
    def isSuitBuilding(self):
        """return true if that block is a suit building"""
        assert(self.debugPrint("isSuitBlock()"))
        state=self.fsm.getCurrentState().getName()
        return state=='suit' or state=='becomingSuit' or \
               state=='clearOutToonInterior'
    
    def isCogdo(self):
        """return true if that block is a cogdo"""
        assert(self.debugPrint("isSuitBlock()"))
        state=self.fsm.getCurrentState().getName()
        return state=='cogdo' or state=='becomingCogdo' or \
               state=='becomingCogdoFromCogdo' or state=='clearOutToonInteriorForCogdo'
    
    def isSuitBlock(self):
        """return true if that block is a suit block/building/cogdo"""
        assert(self.debugPrint("isSuitBlock()"))
        state=self.fsm.getCurrentState().getName()
        return self.isSuitBuilding() or self.isCogdo()
    
    def isEstablishedSuitBlock(self):
        """return true if that block is a fully established suit building"""
        assert(self.debugPrint("isEstablishedSuitBlock()"))
        state=self.fsm.getCurrentState().getName()
        return state=='suit'

    def isToonBlock(self):
        """return true if that block is a toon block/building"""
        assert(self.debugPrint("isToonBlock()"))
        state=self.fsm.getCurrentState().getName()
        return state in ('toon', 'becomingToon', 'becomingToonFromCogdo', )

    def getExteriorAndInteriorZoneId(self):
        assert(self.notify.debug(str(self.block)+" getInteriorZoneId()"))
        blockNumber = self.block
        assert(blockNumber<100) # this may cause trouble for the interiorZoneId, 
                                # it may bump into the next higher zone range.
        dnaStore = self.air.dnaStoreMap[self.canonicalZoneId]
        zoneId = dnaStore.getZoneFromBlockNumber(blockNumber)
        zoneId = ZoneUtil.getTrueZoneId(zoneId, self.zoneId)
        interiorZoneId = (zoneId - zoneId % 100) + 500 + blockNumber
        assert(self.notify.debug(str(self.block)+" getInteriorZoneId() returning"
                +str(interiorZoneId)))
        return zoneId, interiorZoneId
    
    def d_setState(self, state):
        assert(self.notify.debug(str(self.block)+" d_setState(state="+str(state)+")"))
        self.sendUpdate('setState', [state, globalClockDelta.getRealNetworkTime()])
    
    def b_setVictorList(self, victorList):
        self.setVictorList(victorList)
        self.d_setVictorList(victorList)
        return
    
    def d_setVictorList(self, victorList):
        self.sendUpdate("setVictorList", [victorList])
        return
    
    def setVictorList(self, victorList):
        self.victorList = victorList
        return

    def findVictorIndex(self, avId):
        for i in range(len(self.victorList)):
            if self.victorList[i] == avId:
                return i
        return None

    def recordVictorResponse(self, avId):
        index = self.findVictorIndex(avId)
        if index == None:
            self.air.writeServerEvent('suspicious', avId, 'DistributedBuildingAI.setVictorReady from toon not in %s.' % (self.victorList))
            return
            
        assert(self.victorResponses[index] == 0 or self.victorResponses[index] == avId)
        self.victorResponses[index] = avId

    def allVictorsResponded(self):
        if self.victorResponses == self.victorList:
            return 1
        else:
            return 0

    def setVictorReady(self):
        avId = self.air.getAvatarIdFromSender()
        if self.victorResponses == None:
            self.air.writeServerEvent('suspicious', avId, 'DistributedBuildingAI.setVictorReady in state %s.' % (self.fsm.getCurrentState().getName()))
            return

        # Don't tell us about this avatar exiting any more.
        event = self.air.getAvatarExitEvent(avId)
        self.ignore(event)

        if self.allVictorsResponded():
            return

        assert(self.notify.debug("victor %d is ready for bldg %d" % (avId, self.doId)))
        self.recordVictorResponse(avId)

        if self.allVictorsResponded():
            self.toonTakeOver()

    def setVictorExited(self, avId):
        print("victor %d exited unexpectedly for bldg %d" % (avId, self.doId))
        self.recordVictorResponse(avId)
        if self.allVictorsResponded():
            self.toonTakeOver()

    def victorsTimedOutTask(self, task):
        if self.allVictorsResponded():
            return
        if hasattr(self, 'interior'):
            self.notify.info('victorsTimedOutTask: ejecting players by deleting interior.')
            self.interior.requestDelete()
            del self.interior
            task.delayTime = 15.0
            return task.again
        self.notify.info('victorsTimedOutTask: suspicious players remaining, advancing state.')
        for i in range(len(self.victorList)):
            if self.victorList[i] and self.victorResponses[i] == 0:
                self.air.writeServerEvent('suspicious', self.victorList[i], 'DistributedBuildingAI toon client refused to leave building.')
                self.recordVictorResponse(self.victorList[i])
                event = self.air.getAvatarExitEvent(self.victorList[i])
                self.ignore(event)

        self.toonTakeOver()
        return Task.done

    ##### off state #####
    
    def enterOff(self):
        assert(self.debugPrint("enterOff()"))
    
    def exitOff(self):
        assert(self.debugPrint("exitOff()"))

    ##### waitForVictors state #####

    def getToon(self, toonId):
        if (toonId in self.air.doId2do):
            return self.air.doId2do[toonId]
        else:
            self.notify.warning('getToon() - toon: %d not in repository!' \
                % toonId)
        return None

    def updateSavedBy(self, savedBy):
        # Clear the old savedBy from the trophy manager
        if self.savedBy:
            for avId, name, dna in self.savedBy:
                # Don't change building take over score when the toon is in the welcome valley.
                if not ZoneUtil.isWelcomeValley(self.zoneId):
                    self.trophyMgr.removeTrophy(avId, self.numFloors)
        # Update the new saved by list
        self.savedBy = savedBy
        if self.savedBy:
            for avId, name, dna in self.savedBy:
                # Don't change building take over score when the toon is in the welcome valley.
                if not ZoneUtil.isWelcomeValley(self.zoneId):
                    self.trophyMgr.addTrophy(avId, name, self.numFloors)

    def enterWaitForVictors(self, victorList, savedBy):
        assert(len(victorList) == 4)

        # Grab the list of active toons to pass in for each toon
        # (this is used by the quest system)
        activeToons = []
        for t in victorList:
            toon = None
            if (t):
                toon = self.getToon(t)
            if (toon != None):
                activeToons.append(toon)
        # Tell the quest manager that these toons defeated this building
        for t in victorList:
            toon = None
            if t:
                toon = self.getToon(t)
                self.air.writeServerEvent(
                    'buildingDefeated', t, "%s|%s|%s|%s" % (self.track, self.numFloors, self.zoneId, victorList))

            if toon != None:
                self.air.questManager.toonKilledBuilding(
                    toon, self.track, self.difficulty,
                    self.numFloors, self.zoneId, activeToons)

        # Convert the list to all ints. 0 means no one is there.
        # Also, if a toon has disconnected, remove him from the list.
        for i in range(0, 4):
            victor = victorList[i]
            if victor == None or victor not in self.air.doId2do:
                victorList[i] = 0

            else:
                # Handle unexpected exit messages for everyone else.
                event = self.air.getAvatarExitEvent(victor)
                self.accept(event, self.setVictorExited, extraArgs=[victor])

        # Save the list and also tell it to all the clients.
        self.b_setVictorList(victorList)
        self.updateSavedBy(savedBy)
        # List of victor responses
        self.victorResponses = [0, 0, 0, 0]
        # Tell the client to go into waitForVictors state
        self.d_setState("waitForVictors")
        return

    def exitWaitForVictors(self):
        # Stop waiting for unexpected exits.
        self.victorResponses = None
        for victor in self.victorList:
            event = simbase.air.getAvatarExitEvent(victor)
            self.ignore(event)            
        return
    
    def enterWaitForVictorsFromCogdo(self, victorList, savedBy):
        assert(len(victorList) == 4)

        # Grab the list of active toons to pass in for each toon
        # (this is used by the quest system)
        activeToons = []
        for t in victorList:
            toon = None
            if (t):
                toon = self.getToon(t)
            if (toon != None):
                activeToons.append(toon)
        # Tell the quest manager that these toons defeated this building
        self.buildingDefeated = len(savedBy) > 0
        if self.buildingDefeated:
            for t in victorList:
                toon = None
                if t:
                    toon = self.getToon(t)
                    self.air.writeServerEvent(
                        'buildingDefeated', t, "%s|%s|%s|%s" % (self.track, self.numFloors, self.zoneId, victorList))

                if toon != None:
                    self.air.questManager.toonKilledCogdo(
                        toon, self.difficulty,
                        self.numFloors, self.zoneId, activeToons)

        # Convert the list to all ints. 0 means no one is there.
        # Also, if a toon has disconnected, remove him from the list.
        for i in range(0, 4):
            victor = victorList[i]
            if victor == None or victor not in self.air.doId2do:
                victorList[i] = 0

            else:
                # Handle unexpected exit messages for everyone else.
                event = self.air.getAvatarExitEvent(victor)
                self.accept(event, self.setVictorExited, extraArgs=[victor])

        # Save the list and also tell it to all the clients.
        self.b_setVictorList(victorList)
        self.updateSavedBy(savedBy)
        # List of victor responses
        self.victorResponses = [0, 0, 0, 0]
        taskMgr.doMethodLater(30, self.victorsTimedOutTask, self.taskName(str(self.block) + '_waitForVictors-timer'))
        # Tell the client to go into waitForVictors state
        self.d_setState("waitForVictorsFromCogdo")
        return

    def exitWaitForVictorsFromCogdo(self):
        taskMgr.remove(self.taskName(str(self.block) + '_waitForVictors-timer'))
        # Stop waiting for unexpected exits.
        self.victorResponses = None
        for victor in self.victorList:
            event = simbase.air.getAvatarExitEvent(victor)
            self.ignore(event)            
        return
    
    ##### becomingToon state #####
    
    def enterBecomingToon(self):
        assert(self.debugPrint("enterBecomingToon()"))
        self.d_setState('becomingToon')
        name = self.taskName(str(self.block)+'_becomingToon-timer')
        taskMgr.doMethodLater(
            SuitBuildingGlobals.VICTORY_SEQUENCE_TIME,
            self.becomingToonTask,
            name)
    
    def exitBecomingToon(self):
        assert(self.debugPrint("exitBecomingToon()"))
        name = self.taskName(str(self.block)+'_becomingToon-timer')
        taskMgr.remove(name)
    
    ##### becomingToonFromCogdo state #####
    
    def enterBecomingToonFromCogdo(self):
        assert(self.debugPrint("enterBecomingToonFromCogdo()"))
        self.d_setState('becomingToonFromCogdo')
        name = self.taskName(str(self.block)+'_becomingToonFromCogdo-timer')
        taskMgr.doMethodLater(
            SuitBuildingGlobals.VICTORY_SEQUENCE_TIME,
            self.becomingToonTask,
            name)
    
    def exitBecomingToonFromCogdo(self):
        assert(self.debugPrint("exitBecomingToonFromCogdo()"))
        name = self.taskName(str(self.block)+'_becomingToonFromCogdo-timer')
        taskMgr.remove(name)
    
    ##### toon state #####

    def becomingToonTask(self, task):
        assert(self.debugPrint("becomingToonTask()"))
        self.fsm.request("toon")

        # Save the building state whenever we convert a building to
        # toonness.
        self.suitPlannerExt.buildingMgr.save()
        
        return Task.done
    
    def enterToon(self):
        assert(self.debugPrint("enterToon()"))
        self.d_setState('toon')
        # Create the DistributedDoor:
        exteriorZoneId, interiorZoneId=self.getExteriorAndInteriorZoneId()
        # Toon interior:
        if simbase.config.GetBool("want-new-toonhall",1) and \
           ZoneUtil.getCanonicalZoneId(interiorZoneId)== ToonHall:
            self.interior=DistributedToonHallInteriorAI.DistributedToonHallInteriorAI(
                    self.block, self.air, interiorZoneId, self)
        else:
            self.interior=DistributedToonInteriorAI.DistributedToonInteriorAI(
                    self.block, self.air, interiorZoneId, self)
        self.interior.generateWithRequired(interiorZoneId)

        # Outside door:
        door=self.createExteriorDoor()
        # Inside of the same door (different zone, and different distributed object):
        insideDoor=DistributedDoorAI.DistributedDoorAI(self.air, self.block,
                                                       DoorTypes.INT_STANDARD)
        # Tell them about each other:
        door.setOtherDoor(insideDoor)
        insideDoor.setOtherDoor(door)
        door.zoneId=exteriorZoneId
        insideDoor.zoneId=interiorZoneId
        # Now that they both now about each other, generate them:
        door.generateWithRequired(exteriorZoneId)
        insideDoor.generateWithRequired(interiorZoneId)
        # keep track of them:
        self.door=door
        self.insideDoor=insideDoor
        self.becameSuitTime = 0
        
        self.knockKnock=DistributedKnockKnockDoorAI.DistributedKnockKnockDoorAI(
                self.air, self.block)
        self.knockKnock.generateWithRequired(exteriorZoneId)

        self.air.writeServerEvent(
            'building-toon', self.doId,
            "%s|%s" % (self.zoneId, self.block))

    def createExteriorDoor(self):
        """Return the DistributedDoor for the exterior, with correct door type set"""
        # Created so animated buildings can over ride this function
        result = DistributedDoorAI.DistributedDoorAI(self.air, self.block,
                                                 DoorTypes.EXT_STANDARD)
        return result
    
    def exitToon(self):
        assert(self.debugPrint("exitToon()"))
        self.door.setDoorLock(FADoorCodes.BUILDING_TAKEOVER)
        # The door doesn't get unlocked, because 
        # it will be distroyed and recreated.
    
    ##### clearOutToonInterior state #####
    
    def enterClearOutToonInterior(self):
        assert(self.debugPrint("enterClearOutToonInterior()"))
        self.d_setState('clearOutToonInterior')
        if hasattr(self, "interior"):
            self.interior.setState("beingTakenOver")
        name = self.taskName(str(self.block)+'_clearOutToonInterior-timer')
        taskMgr.doMethodLater(
            SuitBuildingGlobals.CLEAR_OUT_TOON_BLDG_TIME,
            self.clearOutToonInteriorTask,
            name)
    
    def exitClearOutToonInterior(self):
        assert(self.debugPrint("exitClearOutToonInterior()"))
        name = self.taskName(str(self.block)+'_clearOutToonInterior-timer')
        taskMgr.remove(name)
    
    ##### becomingSuit state #####

    def clearOutToonInteriorTask(self, task):
        assert(self.debugPrint("clearOutToonInteriorTask()"))
        self.fsm.request("becomingSuit")
        return Task.done
    
    def enterBecomingSuit(self):
        assert(self.debugPrint("enterBecomingSuit()"))

        # We have to send this message before we send the distributed
        # update to becomingSuit state, because the clients depend on
        # knowing what kind of suit building we're becoming.
        self.sendUpdate('setSuitData', 
            [ord(self.track), self.difficulty, self.numFloors])
        
        self.d_setState('becomingSuit')
        name = self.taskName(str(self.block)+'_becomingSuit-timer')
        taskMgr.doMethodLater(
            SuitBuildingGlobals.TO_SUIT_BLDG_TIME,
            self.becomingSuitTask,
            name)
    
    def exitBecomingSuit(self):
        assert(self.debugPrint("exitBecomingSuit()"))
        name = self.taskName(str(self.block)+'_becomingSuit-timer')
        taskMgr.remove(name)
        # Clean up the toon distributed objects:
        if hasattr(self, "interior"):
            self.interior.requestDelete()
            del self.interior
            self.door.requestDelete()
            del self.door
            self.insideDoor.requestDelete()
            del self.insideDoor
            self.knockKnock.requestDelete()
            del self.knockKnock
            
    ##### suit state #####

    def becomingSuitTask(self, task):
        assert(self.debugPrint("becomingSuitTask()"))
        self.fsm.request("suit")

        # Save the building state whenever we convert a building to
        # suitness.
        self.suitPlannerExt.buildingMgr.save()

        return Task.done
    
    def enterSuit(self):
        assert(self.debugPrint("enterSuit()"))

        # We have to send this message again, even though we've
        # already sent it in becomingSuit, because we might have come
        # to this state directly on startup.
        self.sendUpdate('setSuitData', 
            [ord(self.track), self.difficulty, self.numFloors])

        # Create the suit planner for the interior
        zoneId, interiorZoneId = self.getExteriorAndInteriorZoneId()
        self.planner = SuitPlannerInteriorAI.SuitPlannerInteriorAI(
            self.numFloors, self.difficulty, self.track, interiorZoneId)

        self.d_setState('suit')
        # Create the DistributedDoor:
        exteriorZoneId, interiorZoneId=self.getExteriorAndInteriorZoneId()
        #todo: ...create the elevator.
        self.elevator = DistributedElevatorExtAI.DistributedElevatorExtAI(
            self.air,
            self)
        self.elevator.generateWithRequired(exteriorZoneId)

        self.air.writeServerEvent(
            'building-cog', self.doId,
            "%s|%s|%s|%s" % (self.zoneId, self.block, self.track, self.numFloors))

    def exitSuit(self):
        assert(self.debugPrint("exitSuit()"))
        del self.planner
        # Clean up the suit distributed objects:
        if hasattr(self, "elevator"):
            self.elevator.requestDelete()
            del self.elevator

    ##### clearOutToonInteriorForCogdo state #####
    
    def enterClearOutToonInteriorForCogdo(self):
        assert(self.debugPrint("enterClearOutToonInteriorForCogdo()"))
        self.d_setState('clearOutToonInteriorForCogdo')
        if hasattr(self, "interior"):
            self.interior.setState("beingTakenOver")
        name = self.taskName(str(self.block)+'_clearOutToonInteriorForCogdo-timer')
        taskMgr.doMethodLater(
            SuitBuildingGlobals.CLEAR_OUT_TOON_BLDG_TIME,
            self.clearOutToonInteriorForCogdoTask,
            name)
    
    def exitClearOutToonInteriorForCogdo(self):
        assert(self.debugPrint("exitClearOutToonInteriorForCogdo()"))
        name = self.taskName(str(self.block)+'_clearOutToonInteriorForCogdo-timer')
        taskMgr.remove(name)
    
    ##### becomingCogdo state #####

    def clearOutToonInteriorForCogdoTask(self, task):
        assert(self.debugPrint("clearOutToonInteriorForCogdoTask()"))
        self.fsm.request("becomingCogdo")
        return Task.done
    
    def enterBecomingCogdo(self):
        assert(self.debugPrint("enterBecomingCogdo()"))

        # We have to send this message before we send the distributed
        # update to becomingCogdo state, because the clients depend on
        # knowing what kind of cogdo building we're becoming.
        self.sendUpdate('setSuitData', 
            [ord(self.track), self.difficulty, self.numFloors])
        
        self.d_setState('becomingCogdo')
        name = self.taskName(str(self.block)+'_becomingCogdo-timer')
        taskMgr.doMethodLater(
            SuitBuildingGlobals.TO_SUIT_BLDG_TIME,
            self.becomingCogdoTask,
            name)
    
    def exitBecomingCogdo(self):
        assert(self.debugPrint("exitBecomingCogdo()"))
        name = self.taskName(str(self.block)+'_becomingCogdo-timer')
        taskMgr.remove(name)
        # Clean up the toon distributed objects:
        if hasattr(self, "interior"):
            self.interior.requestDelete()
            del self.interior
            self.door.requestDelete()
            del self.door
            self.insideDoor.requestDelete()
            del self.insideDoor
            self.knockKnock.requestDelete()
            del self.knockKnock

    ##### becomingCogdoFromCogdo state #####

    def enterBecomingCogdoFromCogdo(self):
        self.d_setState('becomingCogdoFromCogdo')
        name = self.taskName(str(self.block) + '_becomingCogdoFromCogdo-timer')
        taskMgr.doMethodLater(SuitBuildingGlobals.VICTORY_RUN_TIME, self.becomingCogdoTask, name)

    def exitBecomingCogdoFromCogdo(self):
        self.fSkipElevatorOpening = True
        name = self.taskName(str(self.block) + '_becomingCogdoFromCogdo-timer')
        taskMgr.remove(name)

    ##### cogdo state #####

    def becomingCogdoTask(self, task):
        assert(self.debugPrint("becomingCogdoTask()"))
        self.fsm.request("cogdo")

        # Save the building state whenever we convert a building to
        # cogdoness.
        self.suitPlannerExt.buildingMgr.save()

        return Task.done
    
    def enterCogdo(self):
        assert(self.debugPrint("enterCogdo()"))

        # We have to send this message again, even though we've
        # already sent it in becomingCogdo, because we might have come
        # to this state directly on startup.
        self.sendUpdate('setSuitData', 
            [ord(self.track), self.difficulty, self.numFloors])

        # Create the suit planner for the interior
        zoneId, interiorZoneId = self.getExteriorAndInteriorZoneId()
        self._cogdoLayout = CogdoLayout(self.numFloors)
        self.planner = SuitPlannerCogdoInteriorAI(
            self._cogdoLayout, self.difficulty, self.track, interiorZoneId)

        self.d_setState('cogdo')
        # Create the DistributedDoor:
        exteriorZoneId, interiorZoneId=self.getExteriorAndInteriorZoneId()
        #todo: ...create the elevator.
        self.elevator = DistributedCogdoElevatorExtAI(self.air, self, fSkipOpening=self.fSkipElevatorOpening)
        self.fSkipElevatorOpening = False
        self.elevator.generateWithRequired(exteriorZoneId)

        self.air.writeServerEvent(
            'building-cogdo', self.doId,
            "%s|%s|%s" % (self.zoneId, self.block, self.numFloors))

    def exitCogdo(self):
        assert(self.debugPrint("exitCogdo()"))
        del self.planner
        # Clean up the cogdo distributed objects:
        if hasattr(self, "elevator"):
            self.elevator.requestDelete()
            del self.elevator

    def setSuitPlannerExt( self, planner ):
        """
        ////////////////////////////////////////////////////////////////////
        // Function:   let the building know which suit planner contains
        //             its building manager
        // Parameters: planner, the governing suit planner for this bldg
        // Changes:
        ////////////////////////////////////////////////////////////////////
        """
        self.suitPlannerExt = planner

    def _createSuitInterior(self):
        return DistributedSuitInteriorAI.DistributedSuitInteriorAI(self.air, self.elevator)

    def _createCogdoInterior(self):
        return DistributedCogdoInteriorAI(self.air, self.elevator)
    
    def createSuitInterior(self):
        # Create a building interior in the new (interior) zone
        self.interior = self._createSuitInterior()
        dummy, interiorZoneId = self.getExteriorAndInteriorZoneId()
        self.interior.fsm.request('WaitForAllToonsInside')
        self.interior.generateWithRequired(interiorZoneId)

    def createCogdoInterior(self):
        # Create a building interior in the new (interior) zone
        self.interior = self._createCogdoInterior()
        dummy, interiorZoneId = self.getExteriorAndInteriorZoneId()
        self.interior.fsm.request('WaitForAllToonsInside')
        self.interior.generateWithRequired(interiorZoneId)

    def deleteSuitInterior(self):
        if hasattr(self, "interior"):
            self.interior.requestDelete()
            del self.interior
        if hasattr(self, "elevator"):
            # -1 means the lobby.
            self.elevator.d_setFloor(-1)
            self.elevator.open()

    def deleteCogdoInterior(self):
        self.deleteSuitInterior()

    if __debug__:
        def debugPrint(self, message):
            """for debugging"""
            return self.notify.debug(
                    str(self.__dict__.get('block', '?'))+' '+message)

# history
#
# 10May01  jlbutler  added frontDoorPoint to the building so a suit or
#                    the suit planner can get from a building to a suit
#                    path point which is in front of the building
#

