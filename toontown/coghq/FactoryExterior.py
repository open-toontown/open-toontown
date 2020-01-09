from direct.directnotify import DirectNotifyGlobal
from toontown.battle import BattlePlace
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from otp.distributed.TelemetryLimiter import RotationLimitToH, TLGatherAllAvs
from toontown.toonbase import ToontownGlobals
from toontown.hood import ZoneUtil
from toontown.building import Elevator
from pandac.PandaModules import *
from libotp import *
from libtoontown import *

class FactoryExterior(BattlePlace.BattlePlace):
    notify = DirectNotifyGlobal.directNotify.newCategory('FactoryExterior')

    def __init__(self, loader, parentFSM, doneEvent):
        BattlePlace.BattlePlace.__init__(self, loader, doneEvent)
        self.parentFSM = parentFSM
        self.elevatorDoneEvent = 'elevatorDone'

    def load(self):
        self.fsm = ClassicFSM.ClassicFSM('FactoryExterior', [State.State('start', self.enterStart, self.exitStart, ['walk',
          'tunnelIn',
          'teleportIn',
          'doorIn']),
         State.State('walk', self.enterWalk, self.exitWalk, ['stickerBook',
          'teleportOut',
          'tunnelOut',
          'DFA',
          'doorOut',
          'elevator',
          'stopped',
          'WaitForBattle',
          'battle']),
         State.State('stopped', self.enterStopped, self.exitStopped, ['walk', 'teleportOut', 'elevator']),
         State.State('stickerBook', self.enterStickerBook, self.exitStickerBook, ['walk',
          'DFA',
          'WaitForBattle',
          'battle',
          'elevator']),
         State.State('WaitForBattle', self.enterWaitForBattle, self.exitWaitForBattle, ['battle', 'walk']),
         State.State('battle', self.enterBattle, self.exitBattle, ['walk', 'teleportOut', 'died']),
         State.State('DFA', self.enterDFA, self.exitDFA, ['DFAReject', 'teleportOut', 'tunnelOut']),
         State.State('DFAReject', self.enterDFAReject, self.exitDFAReject, ['walk']),
         State.State('teleportIn', self.enterTeleportIn, self.exitTeleportIn, ['walk']),
         State.State('teleportOut', self.enterTeleportOut, self.exitTeleportOut, ['teleportIn', 'final', 'WaitForBattle']),
         State.State('doorIn', self.enterDoorIn, self.exitDoorIn, ['walk']),
         State.State('doorOut', self.enterDoorOut, self.exitDoorOut, ['walk']),
         State.State('died', self.enterDied, self.exitDied, ['quietZone']),
         State.State('tunnelIn', self.enterTunnelIn, self.exitTunnelIn, ['walk']),
         State.State('tunnelOut', self.enterTunnelOut, self.exitTunnelOut, ['final']),
         State.State('elevator', self.enterElevator, self.exitElevator, ['walk', 'stopped']),
         State.State('final', self.enterFinal, self.exitFinal, ['start'])], 'start', 'final')
        self.parentFSM.getStateNamed('factoryExterior').addChild(self.fsm)
        BattlePlace.BattlePlace.load(self)

    def unload(self):
        self.parentFSM.getStateNamed('factoryExterior').removeChild(self.fsm)
        del self.fsm
        BattlePlace.BattlePlace.unload(self)

    def enter(self, requestStatus):
        self.zoneId = requestStatus['zoneId']
        BattlePlace.BattlePlace.enter(self)
        self.fsm.enterInitialState()
        base.playMusic(self.loader.music, looping=1, volume=0.8)
        self.loader.geom.reparentTo(render)
        self.nodeList = [self.loader.geom]
        self.loader.hood.startSky()
        self._telemLimiter = TLGatherAllAvs('FactoryExterior', RotationLimitToH)
        self.accept('doorDoneEvent', self.handleDoorDoneEvent)
        self.accept('DistributedDoor_doorTrigger', self.handleDoorTrigger)
        NametagGlobals.setMasterArrowsOn(1)
        self.tunnelOriginList = base.cr.hoodMgr.addLinkTunnelHooks(self, self.nodeList, self.zoneId)
        how = requestStatus['how']
        self.fsm.request(how, [requestStatus])
        if base.cr.astronSupport and self.zoneId != ToontownGlobals.LawbotOfficeExt:
            self.handleInterests()

    def exit(self):
        self._telemLimiter.destroy()
        del self._telemLimiter
        self.loader.hood.stopSky()
        self.fsm.requestFinalState()
        self.loader.music.stop()
        for node in self.tunnelOriginList:
            node.removeNode()

        del self.tunnelOriginList
        del self.nodeList
        self.ignoreAll()
        BattlePlace.BattlePlace.exit(self)

    def enterTunnelOut(self, requestStatus):
        fromZoneId = self.zoneId - self.zoneId % 100
        tunnelName = base.cr.hoodMgr.makeLinkTunnelName(self.loader.hood.id, fromZoneId)
        requestStatus['tunnelName'] = tunnelName
        BattlePlace.BattlePlace.enterTunnelOut(self, requestStatus)

    def enterTeleportIn(self, requestStatus):
        base.localAvatar.setPosHpr(-34, -350, 0, -28, 0, 0)
        BattlePlace.BattlePlace.enterTeleportIn(self, requestStatus)

    def enterTeleportOut(self, requestStatus):
        BattlePlace.BattlePlace.enterTeleportOut(self, requestStatus, self.__teleportOutDone)

    def __teleportOutDone(self, requestStatus):
        hoodId = requestStatus['hoodId']
        zoneId = requestStatus['zoneId']
        avId = requestStatus['avId']
        shardId = requestStatus['shardId']
        if hoodId == self.loader.hood.hoodId and zoneId == self.zoneId and shardId == None:
            self.fsm.request('teleportIn', [requestStatus])
        elif hoodId == ToontownGlobals.MyEstate:
            self.getEstateZoneAndGoHome(requestStatus)
        else:
            self.doneStatus = requestStatus
            messenger.send(self.doneEvent)
        return

    def exitTeleportOut(self):
        BattlePlace.BattlePlace.exitTeleportOut(self)

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
        elif where == 'factoryInterior':
            self.doneStatus = doneStatus
            messenger.send(self.doneEvent)
        elif where == 'stageInterior':
            self.doneStatus = doneStatus
            messenger.send(self.doneEvent)
        else:
            self.notify.error('Unknown mode: ' + where + ' in handleElevatorDone')

    if config.GetBool('astron-support', True):
        def handleInterests(self):
            # First, we need to load the DNA file for this Cog HQ.
            dnaStore = DNAStorage()
            dnaFileName = self.genDNAFileName(self.zoneId)
            loadDNAFileAI(dnaStore, dnaFileName)

            # Next, we need to collect all of the visgroup zone IDs.
            self.zoneVisDict = {}
            for i in range(dnaStore.getNumDNAVisGroupsAI()):
                groupFullName = dnaStore.getDNAVisGroupName(i)
                visGroup = dnaStore.getDNAVisGroupAI(i)
                visZoneId = int(base.cr.hoodMgr.extractGroupName(groupFullName))
                visZoneId = ZoneUtil.getTrueZoneId(visZoneId, self.zoneId)
                visibles = []
                for i in range(visGroup.getNumVisibles()):
                    visibles.append(int(visGroup.getVisibleName(i)))

                visibles.append(ZoneUtil.getBranchZone(visZoneId))
                self.zoneVisDict[visZoneId] = visibles

            # Finally, we want interest in all visgroups due to this being a Cog HQ.
            base.cr.sendSetZoneMsg(self.zoneId, list(self.zoneVisDict.values())[0])
