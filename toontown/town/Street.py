from pandac.PandaModules import *
from libotp import *
from toontown.battle.BattleProps import *
from toontown.battle.BattleSounds import *
from toontown.distributed.ToontownMsgTypes import *
from direct.gui.DirectGui import cleanupDialog
from direct.directnotify import DirectNotifyGlobal
from toontown.hood import Place
from toontown.battle import BattlePlace
from direct.showbase import DirectObject
from direct.fsm import StateData
from direct.fsm import ClassicFSM, State
from direct.task import Task
from otp.distributed.TelemetryLimiter import RotationLimitToH, TLGatherAllAvs
from toontown.battle import BattleParticles
from toontown.building import Elevator
from toontown.hood import ZoneUtil
from toontown.toonbase import ToontownGlobals
from toontown.toon.Toon import teleportDebug
from toontown.estate import HouseGlobals
from toontown.toonbase import TTLocalizer
from direct.interval.IntervalGlobal import *
visualizeZones = base.config.GetBool('visualize-zones', 0)

class Street(BattlePlace.BattlePlace):
    notify = DirectNotifyGlobal.directNotify.newCategory('Street')

    def __init__(self, loader, parentFSM, doneEvent):
        BattlePlace.BattlePlace.__init__(self, loader, doneEvent)
        self.fsm = ClassicFSM.ClassicFSM('Street', [State.State('start', self.enterStart, self.exitStart, ['walk',
          'tunnelIn',
          'doorIn',
          'teleportIn',
          'elevatorIn']),
         State.State('walk', self.enterWalk, self.exitWalk, ['push',
          'sit',
          'stickerBook',
          'WaitForBattle',
          'battle',
          'DFA',
          'trialerFA',
          'doorOut',
          'elevator',
          'tunnelIn',
          'tunnelOut',
          'teleportOut',
          'quest',
          'stopped',
          'fishing',
          'purchase',
          'died']),
         State.State('sit', self.enterSit, self.exitSit, ['walk']),
         State.State('push', self.enterPush, self.exitPush, ['walk']),
         State.State('stickerBook', self.enterStickerBook, self.exitStickerBook, ['walk',
          'push',
          'sit',
          'battle',
          'DFA',
          'trialerFA',
          'doorOut',
          'elevator',
          'tunnelIn',
          'tunnelOut',
          'WaitForBattle',
          'teleportOut',
          'quest',
          'stopped',
          'fishing',
          'purchase']),
         State.State('WaitForBattle', self.enterWaitForBattle, self.exitWaitForBattle, ['battle', 'walk']),
         State.State('battle', self.enterBattle, self.exitBattle, ['walk', 'teleportOut', 'died']),
         State.State('doorIn', self.enterDoorIn, self.exitDoorIn, ['walk']),
         State.State('doorOut', self.enterDoorOut, self.exitDoorOut, ['walk']),
         State.State('elevatorIn', self.enterElevatorIn, self.exitElevatorIn, ['walk']),
         State.State('elevator', self.enterElevator, self.exitElevator, ['walk']),
         State.State('trialerFA', self.enterTrialerFA, self.exitTrialerFA, ['trialerFAReject', 'DFA']),
         State.State('trialerFAReject', self.enterTrialerFAReject, self.exitTrialerFAReject, ['walk']),
         State.State('DFA', self.enterDFA, self.exitDFA, ['DFAReject', 'teleportOut', 'tunnelOut']),
         State.State('DFAReject', self.enterDFAReject, self.exitDFAReject, ['walk']),
         State.State('teleportIn', self.enterTeleportIn, self.exitTeleportIn, ['walk',
          'teleportOut',
          'quietZone',
          'WaitForBattle',
          'battle']),
         State.State('teleportOut', self.enterTeleportOut, self.exitTeleportOut, ['teleportIn', 'quietZone', 'WaitForBattle']),
         State.State('died', self.enterDied, self.exitDied, ['quietZone']),
         State.State('tunnelIn', self.enterTunnelIn, self.exitTunnelIn, ['walk']),
         State.State('tunnelOut', self.enterTunnelOut, self.exitTunnelOut, ['final']),
         State.State('quietZone', self.enterQuietZone, self.exitQuietZone, ['teleportIn']),
         State.State('quest', self.enterQuest, self.exitQuest, ['walk', 'stopped']),
         State.State('stopped', self.enterStopped, self.exitStopped, ['walk']),
         State.State('stopped', self.enterStopped, self.exitStopped, ['walk']),
         State.State('fishing', self.enterFishing, self.exitFishing, ['walk']),
         State.State('purchase', self.enterPurchase, self.exitPurchase, ['walk']),
         State.State('final', self.enterFinal, self.exitFinal, ['start'])], 'start', 'final')
        self.parentFSM = parentFSM
        self.tunnelOriginList = []
        self.elevatorDoneEvent = 'elevatorDone'
        self.halloweenLights = []

    def enter(self, requestStatus, visibilityFlag = 1, arrowsOn = 1):
        teleportDebug(requestStatus, 'Street.enter(%s)' % (requestStatus,))
        self._ttfToken = None
        self.fsm.enterInitialState()
        base.playMusic(self.loader.music, looping=1, volume=0.8)
        self.loader.geom.reparentTo(render)
        if visibilityFlag:
            self.visibilityOn()
        base.localAvatar.setGeom(self.loader.geom)
        base.localAvatar.setOnLevelGround(1)
        self._telemLimiter = TLGatherAllAvs('Street', RotationLimitToH)
        NametagGlobals.setMasterArrowsOn(arrowsOn)

        def __lightDecorationOn__():
            geom = base.cr.playGame.getPlace().loader.geom
            self.halloweenLights = geom.findAllMatches('**/*light*')
            self.halloweenLights += geom.findAllMatches('**/*lamp*')
            self.halloweenLights += geom.findAllMatches('**/prop_snow_tree*')
            for light in self.halloweenLights:
                light.setColorScaleOff(1)

        newsManager = base.cr.newsManager
        if newsManager:
            holidayIds = base.cr.newsManager.getDecorationHolidayId()
            if (ToontownGlobals.HALLOWEEN_COSTUMES in holidayIds or ToontownGlobals.SPOOKY_COSTUMES in holidayIds) and self.loader.hood.spookySkyFile:
                lightsOff = Sequence(LerpColorScaleInterval(base.cr.playGame.hood.loader.geom, 0.1, Vec4(0.55, 0.55, 0.65, 1)), Func(self.loader.hood.startSpookySky))
                lightsOff.start()
            else:
                self.loader.hood.startSky()
                lightsOn = LerpColorScaleInterval(base.cr.playGame.hood.loader.geom, 0.1, Vec4(1, 1, 1, 1))
                lightsOn.start()
        else:
            self.loader.hood.startSky()
            lightsOn = LerpColorScaleInterval(base.cr.playGame.hood.loader.geom, 0.1, Vec4(1, 1, 1, 1))
            lightsOn.start()
        self.accept('doorDoneEvent', self.handleDoorDoneEvent)
        self.accept('DistributedDoor_doorTrigger', self.handleDoorTrigger)
        self.enterZone(requestStatus['zoneId'])
        self.tunnelOriginList = base.cr.hoodMgr.addLinkTunnelHooks(self, self.loader.nodeList, self.zoneId)
        self.fsm.request(requestStatus['how'], [requestStatus])
        self.replaceStreetSignTextures()
        return

    def exit(self, visibilityFlag = 1):
        if visibilityFlag:
            self.visibilityOff()
        self.loader.geom.reparentTo(hidden)
        self._telemLimiter.destroy()
        del self._telemLimiter

        def __lightDecorationOff__():
            for light in self.halloweenLights:
                light.reparentTo(hidden)

        newsManager = base.cr.newsManager
        NametagGlobals.setMasterArrowsOn(0)
        self.loader.hood.stopSky()
        self.loader.music.stop()
        base.localAvatar.setGeom(render)
        base.localAvatar.setOnLevelGround(0)

    def load(self):
        BattlePlace.BattlePlace.load(self)
        self.parentFSM.getStateNamed('street').addChild(self.fsm)

    def unload(self):
        self.parentFSM.getStateNamed('street').removeChild(self.fsm)
        del self.parentFSM
        del self.fsm
        self.enterZone(None)
        cleanupDialog('globalDialog')
        self.ignoreAll()
        BattlePlace.BattlePlace.unload(self)
        return

    def enterElevatorIn(self, requestStatus):
        self._eiwbTask = taskMgr.add(Functor(self._elevInWaitBldgTask, requestStatus['bldgDoId']), uniqueName('elevInWaitBldg'))

    def _elevInWaitBldgTask(self, bldgDoId, task):
        bldg = base.cr.doId2do.get(bldgDoId)
        if bldg:
            if bldg.elevatorNodePath is not None:
                self._enterElevatorGotElevator()
                return Task.done
        return Task.cont

    def _enterElevatorGotElevator(self):
        messenger.send('insideVictorElevator')

    def exitElevatorIn(self):
        taskMgr.remove(self._eiwbTask)

    def enterElevator(self, distElevator):
        base.localAvatar.cantLeaveGame = 1
        self.accept(self.elevatorDoneEvent, self.handleElevatorDone)
        self.elevator = Elevator.Elevator(self.fsm.getStateNamed('elevator'), self.elevatorDoneEvent, distElevator)
        self.elevator.load()
        self.elevator.enter()

    def exitElevator(self):
        base.localAvatar.cantLeaveGame = 0
        self.ignore(self.elevatorDoneEvent)
        self.elevator.unload()
        self.elevator.exit()
        del self.elevator

    def detectedElevatorCollision(self, distElevator):
        self.fsm.request('elevator', [distElevator])
        return None

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
        elif where in ('suitInterior', 'cogdoInterior'):
            self.doneStatus = doneStatus
            messenger.send(self.doneEvent)
        else:
            self.notify.error('Unknown mode: ' + where + ' in handleElevatorDone')

    def enterTunnelIn(self, requestStatus):
        self.enterZone(requestStatus['zoneId'])
        BattlePlace.BattlePlace.enterTunnelIn(self, requestStatus)

    def enterTeleportIn(self, requestStatus):
        teleportDebug(requestStatus, 'Street.enterTeleportIn(%s)' % (requestStatus,))
        zoneId = requestStatus['zoneId']
        self._ttfToken = self.addSetZoneCompleteCallback(Functor(self._teleportToFriend, requestStatus))
        self.enterZone(zoneId)
        BattlePlace.BattlePlace.enterTeleportIn(self, requestStatus)

    def _teleportToFriend(self, requestStatus):
        avId = requestStatus['avId']
        hoodId = requestStatus['hoodId']
        zoneId = requestStatus['zoneId']
        if avId != -1:
            if avId not in base.cr.doId2do:
                teleportDebug(requestStatus, "couldn't find friend %s" % avId)
                handle = base.cr.identifyFriend(avId)
                requestStatus = {'how': 'teleportIn',
                 'hoodId': hoodId,
                 'zoneId': hoodId,
                 'shardId': None,
                 'loader': 'safeZoneLoader',
                 'where': 'playground',
                 'avId': avId}
                self.fsm.request('final')
                self.__teleportOutDone(requestStatus)
        return

    def exitTeleportIn(self):
        self.removeSetZoneCompleteCallback(self._ttfToken)
        self._ttfToken = None
        BattlePlace.BattlePlace.exitTeleportIn(self)
        return

    def enterTeleportOut(self, requestStatus):
        if 'battle' in requestStatus:
            self.__teleportOutDone(requestStatus)
        else:
            BattlePlace.BattlePlace.enterTeleportOut(self, requestStatus, self.__teleportOutDone)

    def __teleportOutDone(self, requestStatus):
        hoodId = requestStatus['hoodId']
        zoneId = requestStatus['zoneId']
        shardId = requestStatus['shardId']
        if hoodId == self.loader.hood.id and shardId == None:
            if zoneId == self.zoneId:
                self.fsm.request('teleportIn', [requestStatus])
            elif requestStatus['where'] == 'street' and ZoneUtil.getBranchZone(zoneId) == self.loader.branchZone:
                self.fsm.request('quietZone', [requestStatus])
            else:
                self.doneStatus = requestStatus
                messenger.send(self.doneEvent)
        elif hoodId == ToontownGlobals.MyEstate:
            self.getEstateZoneAndGoHome(requestStatus)
        else:
            self.doneStatus = requestStatus
            messenger.send(self.doneEvent)
        return

    def exitTeleportOut(self):
        BattlePlace.BattlePlace.exitTeleportOut(self)

    def goHomeFailed(self, task):
        self.notifyUserGoHomeFailed()
        self.ignore('setLocalEstateZone')
        self.doneStatus['avId'] = -1
        self.doneStatus['zoneId'] = self.getZoneId()
        self.fsm.request('teleportIn', [self.doneStatus])
        return Task.done

    def renameFloorPolys(self, nodeList):
        for i in nodeList:
            collNodePaths = i.findAllMatches('**/+CollisionNode')
            numCollNodePaths = collNodePaths.getNumPaths()
            visGroupName = i.node().getName()
            for j in range(numCollNodePaths):
                collNodePath = collNodePaths.getPath(j)
                bitMask = collNodePath.node().getIntoCollideMask()
                if bitMask.getBit(1):
                    collNodePath.node().setName(visGroupName)

    def hideAllVisibles(self):
        for i in self.loader.nodeList:
            i.stash()

    def showAllVisibles(self):
        for i in self.loader.nodeList:
            i.unstash()

    def visibilityOn(self):
        self.hideAllVisibles()
        self.accept('on-floor', self.enterZone)

    def visibilityOff(self):
        self.ignore('on-floor')
        self.showAllVisibles()

    def doEnterZone(self, newZoneId):
        if self.zoneId != None:
            for i in self.loader.nodeDict[self.zoneId]:
                if newZoneId:
                    if i not in self.loader.nodeDict[newZoneId]:
                        self.loader.fadeOutDict[i].start()
                        self.loader.exitAnimatedProps(i)
                else:
                    i.stash()
                    self.loader.exitAnimatedProps(i)

        if newZoneId != None:
            for i in self.loader.nodeDict[newZoneId]:
                if self.zoneId:
                    if i not in self.loader.nodeDict[self.zoneId]:
                        self.loader.fadeInDict[i].start()
                        self.loader.enterAnimatedProps(i)
                else:
                    if self.loader.fadeOutDict[i].isPlaying():
                        self.loader.fadeOutDict[i].finish()
                    if self.loader.fadeInDict[i].isPlaying():
                        self.loader.fadeInDict[i].finish()
                    self.loader.enterAnimatedProps(i)
                    i.unstash()

        if newZoneId != self.zoneId:
            if visualizeZones:
                if self.zoneId != None:
                    self.loader.zoneDict[self.zoneId].clearColor()
                if newZoneId != None:
                    self.loader.zoneDict[newZoneId].setColor(0, 0, 1, 1, 100)
            if newZoneId != None:
                if not base.cr.astronSupport:
                    base.cr.sendSetZoneMsg(newZoneId)
                else:
                    visZones = [self.loader.node2zone[x] for x in self.loader.nodeDict[newZoneId]]
                    visZones.append(ZoneUtil.getBranchZone(newZoneId))
                    base.cr.sendSetZoneMsg(newZoneId, visZones)
                self.notify.debug('Entering Zone %d' % newZoneId)
            self.zoneId = newZoneId
        geom = base.cr.playGame.getPlace().loader.geom
        self.halloweenLights = geom.findAllMatches('**/*light*')
        self.halloweenLights += geom.findAllMatches('**/*lamp*')
        self.halloweenLights += geom.findAllMatches('**/prop_snow_tree*')
        for light in self.halloweenLights:
            light.setColorScaleOff(1)

        return

    def replaceStreetSignTextures(self):
        if not hasattr(base.cr, 'playGame'):
            return
        place = base.cr.playGame.getPlace()
        if place is None:
            return
        geom = base.cr.playGame.getPlace().loader.geom
        signs = geom.findAllMatches('**/*tunnelAheadSign*;+s')
        if signs.getNumPaths() > 0:
            streetSign = base.cr.streetSign
            signTexturePath = streetSign.StreetSignBaseDir + '/' + streetSign.StreetSignFileName
            loaderTexturePath = Filename(str(signTexturePath))
            alphaPath = 'phase_4/maps/tt_t_ara_gen_tunnelAheadSign_a.rgb'
            inDreamland = False
            if place.zoneId and ZoneUtil.getCanonicalHoodId(place.zoneId) == ToontownGlobals.DonaldsDreamland:
                inDreamland = True
            alphaPath = 'phase_4/maps/tt_t_ara_gen_tunnelAheadSign_a.rgb'
            if Filename(signTexturePath).exists():
                signTexture = loader.loadTexture(loaderTexturePath, alphaPath)
            for sign in signs:
                if Filename(signTexturePath).exists():
                    sign.setTexture(signTexture, 1)
                if inDreamland:
                    sign.setColorScale(0.525, 0.525, 0.525, 1)

        return
