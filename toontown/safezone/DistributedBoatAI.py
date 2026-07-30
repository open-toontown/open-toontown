from otp.ai.AIBase import *
from toontown.toonbase.ToontownGlobals import *
from direct.distributed.ClockDelta import *
from direct.distributed import DistributedObjectAI
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from direct.task import Task

class DistributedBoatAI(DistributedObjectAI.DistributedObjectAI):

    def __init__(self, air):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        self.fsm = ClassicFSM.ClassicFSM('DistributedBoatAI', [
         State.State('off', self.enterOff, self.exitOff, [
          'DockedEast']),
         State.State('DockedEast', self.enterDockedEast, self.exitDockedEast, [
          'SailingWest']),
         State.State('SailingWest', self.enterSailingWest, self.exitSailingWest, [
          'DockedWest']),
         State.State('DockedWest', self.enterDockedWest, self.exitDockedWest, [
          'SailingEast']),
         State.State('SailingEast', self.enterSailingEast, self.exitSailingEast, [
          'DockedEast'])], 'off', 'off')
        self.fsm.enterInitialState()
        return None

    def delete(self):
        self.fsm.request('off')
        DistributedObjectAI.DistributedObjectAI.delete(self)

    def b_setState(self, state):
        self.sendUpdate('setState', [state, globalClockDelta.getRealNetworkTime()])
        self.fsm.request(state)

    def getState(self):
        return [
         self.fsm.getCurrentState().getName(), globalClockDelta.getRealNetworkTime()]

    def start(self):
        self.b_setState('DockedEast')
        return None

    def enterOff(self):
        return None

    def exitOff(self):
        return None

    def enterDockedEast(self):
        taskMgr.doMethodLater(10.0, self.__departEast, 'depart-east')
        return None

    def exitDockedEast(self):
        taskMgr.remove('depart-east')
        return None

    def __departEast(self, task):
        self.b_setState('SailingWest')
        return Task.done

    def enterSailingWest(self):
        taskMgr.doMethodLater(20.0, self.__dockWest, 'dock-west')
        return None

    def exitSailingWest(self):
        taskMgr.remove('dock-west')
        return None

    def __dockWest(self, task):
        self.b_setState('DockedWest')
        return Task.done

    def enterDockedWest(self):
        taskMgr.doMethodLater(10.0, self.__departWest, 'depart-west')
        return None

    def exitDockedWest(self):
        taskMgr.remove('depart-west')
        return None

    def __departWest(self, task):
        self.b_setState('SailingEast')
        return Task.done

    def enterSailingEast(self):
        taskMgr.doMethodLater(20.0, self.__dockEast, 'dock-east')
        return None

    def exitSailingEast(self):
        taskMgr.remove('dock-east')
        return None

    def __dockEast(self, task):
        self.b_setState('DockedEast')
        return Task.done
