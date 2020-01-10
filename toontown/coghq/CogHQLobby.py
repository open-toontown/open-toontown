from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from toontown.hood import Place
from toontown.building import Elevator
from toontown.toonbase import ToontownGlobals
from pandac.PandaModules import *
from libotp import *
from otp.distributed.TelemetryLimiter import RotationLimitToH, TLGatherAllAvs

class CogHQLobby(Place.Place):
    notify = DirectNotifyGlobal.directNotify.newCategory('CogHQLobby')

    def __init__(self, hood, parentFSM, doneEvent):
        Place.Place.__init__(self, hood, doneEvent)
        self.parentFSM = parentFSM
        self.elevatorDoneEvent = 'elevatorDone'
        self.fsm = ClassicFSM.ClassicFSM('CogHQLobby', [State.State('start', self.enterStart, self.exitStart, ['walk',
          'tunnelIn',
          'teleportIn',
          'doorIn']),
         State.State('walk', self.enterWalk, self.exitWalk, ['elevator',
          'DFA',
          'doorOut',
          'stopped']),
         State.State('stopped', self.enterStopped, self.exitStopped, ['walk', 'teleportOut', 'elevator']),
         State.State('doorIn', self.enterDoorIn, self.exitDoorIn, ['walk']),
         State.State('doorOut', self.enterDoorOut, self.exitDoorOut, ['walk']),
         State.State('teleportIn', self.enterTeleportIn, self.exitTeleportIn, ['walk']),
         State.State('elevator', self.enterElevator, self.exitElevator, ['walk', 'stopped']),
         State.State('DFA', self.enterDFA, self.exitDFA, ['DFAReject']),
         State.State('DFAReject', self.enterDFAReject, self.exitDFAReject, ['walk']),
         State.State('final', self.enterFinal, self.exitFinal, ['start'])], 'start', 'final')

    def load(self):
        self.parentFSM.getStateNamed('cogHQLobby').addChild(self.fsm)
        Place.Place.load(self)

    def unload(self):
        self.parentFSM.getStateNamed('cogHQLobby').removeChild(self.fsm)
        Place.Place.unload(self)
        self.fsm = None
        return

    def enter(self, requestStatus):
        self.zoneId = requestStatus['zoneId']
        Place.Place.enter(self)
        self.fsm.enterInitialState()
        base.playMusic(self.loader.music, looping=1, volume=0.8)
        self.loader.geom.reparentTo(render)
        self.accept('doorDoneEvent', self.handleDoorDoneEvent)
        self.accept('DistributedDoor_doorTrigger', self.handleDoorTrigger)
        NametagGlobals.setMasterArrowsOn(1)
        how = requestStatus['how']
        self.fsm.request(how, [requestStatus])
        self._telemLimiter = TLGatherAllAvs('CogHQLobby', RotationLimitToH)

    def exit(self):
        self._telemLimiter.destroy()
        del self._telemLimiter
        self.fsm.requestFinalState()
        self.ignoreAll()
        self.loader.music.stop()
        if self.loader.geom != None:
            self.loader.geom.reparentTo(hidden)
        Place.Place.exit(self)
        return

    def enterWalk(self, teleportIn = 0):
        Place.Place.enterWalk(self, teleportIn)
        self.ignore('teleportQuery')
        base.localAvatar.setTeleportAvailable(0)

    def enterElevator(self, distElevator, skipDFABoard = 0):
        self.accept(self.elevatorDoneEvent, self.handleElevatorDone)
        self.elevator = Elevator.Elevator(self.fsm.getStateNamed('elevator'), self.elevatorDoneEvent, distElevator)
        if skipDFABoard:
            self.elevator.skipDFABoard = 1
        distElevator.elevatorFSM = self.elevator
        self.elevator.load()
        self.elevator.enter()

    def exitElevator(self):
        self.ignore(self.elevatorDoneEvent)
        self.elevator.unload()
        self.elevator.exit()
        del self.elevator

    def detectedElevatorCollision(self, distElevator):
        self.fsm.request('elevator', [distElevator])

    def handleElevatorDone(self, doneStatus):
        self.notify.debug('handling elevator done event')
        where = doneStatus['where']
        if where == 'reject':
            if hasattr(base.localAvatar, 'elevatorNotifier') and base.localAvatar.elevatorNotifier.isNotifierOpen():
                pass
            else:
                self.fsm.request('walk')
        elif where == 'exit':
            self.fsm.request('walk')
        elif where == 'cogHQBossBattle':
            self.doneStatus = doneStatus
            messenger.send(self.doneEvent)
        else:
            self.notify.error('Unknown mode: ' + where + ' in handleElevatorDone')

    def enterTeleportIn(self, requestStatus):
        base.localAvatar.setPosHpr(render, 0, 0, 0, 0, 0, 0)
        Place.Place.enterTeleportIn(self, requestStatus)
