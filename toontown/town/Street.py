from panda3d.core import *
from panda3d.otp import *
from toontown.battle.BattleProps import *
from toontown.battle.BattleSounds import *
from toontown.distributed.ToontownMsgTypes import *
from direct.gui.DirectGui import cleanupDialog
from direct.directnotify import DirectNotifyGlobal
from toontown.battle import BattlePlace
from direct.fsm import ClassicFSM, State
from direct.task import Task
import time
import traceback
from otp.distributed.TelemetryLimiter import RotationLimitToH, TLGatherAllAvs
from toontown.building import Elevator
from toontown.hood import OutdoorLighting
from toontown.hood import ZoneUtil
from toontown.toonbase import ToontownGlobals
from toontown.toon.Toon import teleportDebug
from direct.interval.IntervalGlobal import *
visualizeZones = ConfigVariableBool('visualize-zones', 0).value
wholeStreetLoading = ConfigVariableBool('street-load-whole', 1).value
streetWholeStaggerProps = ConfigVariableBool('street-load-whole-stagger-props', 1)
streetWholeVisgroupsPerFrame = ConfigVariableInt('street-load-whole-visgroups-per-frame', 2)
streetPerfDebug = ConfigVariableBool('street-debug-perf', 0)
streetPerfDebugIntervalFrames = ConfigVariableInt('street-debug-perf-interval-frames', 60)
streetPerfDebugThresholdMs = ConfigVariableInt('street-debug-perf-threshold-ms', 8)
streetPerfDebugTrace = ConfigVariableBool('street-debug-perf-trace', 0)
streetPerfDebugTopN = ConfigVariableInt('street-debug-perf-topn', 8)


class _PerfAgg(object):

    def __init__(self, notify, prefix):
        self.notify = notify
        self.prefix = prefix
        self.frame = 0
        self._lastFlushFrame = 0
        self._stats = {}

    def add(self, name, dt):
        s = self._stats.get(name)
        if s is None:
            self._stats[name] = [dt, dt, dt, 1]
        else:
            s[0] += dt
            if dt < s[1]:
                s[1] = dt
            if dt > s[2]:
                s[2] = dt
            s[3] += 1

    def maybeFlush(self, intervalFrames, topN):
        if intervalFrames <= 0:
            return
        if (self.frame - self._lastFlushFrame) < intervalFrames:
            return
        self._lastFlushFrame = self.frame
        if not self._stats:
            return
        items = sorted(self._stats.items(), key=lambda kv: kv[1][0], reverse=True)
        lines = []
        for name, s in items[:max(1, topN)]:
            total, mn, mx, cnt = s
            avg = total / float(max(1, cnt))
            lines.append('%s: total=%.2fms avg=%.2fms min=%.2fms max=%.2fms n=%d' % (name, total * 1000.0, avg * 1000.0, mn * 1000.0, mx * 1000.0, cnt))
        self.notify.info('%s perf (last %d frames):\n  %s' % (self.prefix, intervalFrames, '\n  '.join(lines)))
        self._stats.clear()

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
         State.State('doorOut', self.enterDoorOut, self.exitDoorOut, ['walk', 'stopped']),
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
        self._wholeStreetPropTaskName = None
        self._perfAgg = None

    def enter(self, requestStatus, visibilityFlag = 1, arrowsOn = 1):
        teleportDebug(requestStatus, 'Street.enter(%s)' % (requestStatus,))
        self._ttfToken = None
        self._spawnStreetZoneId = requestStatus.get('zoneId') if wholeStreetLoading else None
        self.fsm.enterInitialState()
        base.playMusic(self.loader.music, looping=1, volume=0.8)
        self.loader.geom.reparentTo(render)
        _hoodId = getattr(getattr(self.loader, 'hood', None), 'id', None)
        OutdoorLighting.begin(self.loader.geom, 'playground', hoodId=_hoodId)
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
        if base.cr.wantStreetSign:
            self.replaceStreetSignTextures()
        if hasattr(self, '_spawnStreetZoneId'):
            del self._spawnStreetZoneId
        return

    def exit(self, visibilityFlag = 1):
        if visibilityFlag:
            self.visibilityOff()
        self.loader.geom.reparentTo(hidden)
        OutdoorLighting.end(self.loader.geom)
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
        self._cancelWholeStreetPropTask()
        self._perfAgg = None
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

    def _refreshStreetHolidayLights(self):
        geom = base.cr.playGame.getPlace().loader.geom
        self.halloweenLights = geom.findAllMatches('**/*light*')
        self.halloweenLights += geom.findAllMatches('**/*lamp*')
        self.halloweenLights += geom.findAllMatches('**/prop_snow_tree*')
        for light in self.halloweenLights:
            light.setColorScaleOff(1)

    def _cancelWholeStreetPropTask(self):
        if self._wholeStreetPropTaskName:
            taskMgr.remove(self._wholeStreetPropTaskName)
            self._wholeStreetPropTaskName = None
        if hasattr(self, '_wholeStreetPropNodes'):
            del self._wholeStreetPropNodes
        if hasattr(self, '_wholeStreetPropIndex'):
            del self._wholeStreetPropIndex

    def _orderedWholeStreetVisgroups(self):
        nodes = list(self.loader.nodeList)
        zid = getattr(self, '_spawnStreetZoneId', None)
        if zid is not None:
            zn = self.loader.zoneDict.get(zid)
            if zn is not None:
                try:
                    nodes.remove(zn)
                except ValueError:
                    pass
                else:
                    nodes.insert(0, zn)
        return nodes

    def _wholeStreetPropStep(self, task):
        if not getattr(self, 'loader', None) or not hasattr(self, '_wholeStreetPropNodes'):
            self._wholeStreetPropTaskName = None
            return task.done
        perfOn = streetPerfDebug.getValue()
        threshold = max(0, streetPerfDebugThresholdMs.getValue()) / 1000.0
        topN = streetPerfDebugTopN.getValue()
        if perfOn and self._perfAgg is None:
            self._perfAgg = _PerfAgg(self.notify, 'Street(%s)' % (getattr(self, 'zoneId', '?'),))
        t0 = time.perf_counter() if perfOn else None
        nodes = self._wholeStreetPropNodes
        per = max(1, streetWholeVisgroupsPerFrame.getValue())
        i = self._wholeStreetPropIndex
        end = min(i + per, len(nodes))
        for j in range(i, end):
            if perfOn:
                t1 = time.perf_counter()
                self.loader.enterAnimatedProps(nodes[j])
                dt = time.perf_counter() - t1
                self._perfAgg.add('enterAnimatedProps', dt)
                if dt >= threshold:
                    self.notify.warning('street perf hitch: enterAnimatedProps visgroup=%s dt=%.2fms' % (nodes[j].getName(), dt * 1000.0))
                    if streetPerfDebugTrace.getValue():
                        self.notify.warning('street perf trace (enterAnimatedProps):\n%s' % ''.join(traceback.format_stack(limit=20)))
            else:
                self.loader.enterAnimatedProps(nodes[j])
        if end >= len(nodes):
            self._wholeStreetPropTaskName = None
            del self._wholeStreetPropNodes
            del self._wholeStreetPropIndex
            return task.done
        self._wholeStreetPropIndex = end
        if perfOn:
            self._perfAgg.frame += 1
            dt = time.perf_counter() - t0
            self._perfAgg.add('_wholeStreetPropStep', dt)
            if dt >= threshold:
                self.notify.warning('street perf hitch: _wholeStreetPropStep dt=%.2fms per=%d (%d->%d of %d)' % (dt * 1000.0, per, i, end, len(nodes)))
                if streetPerfDebugTrace.getValue():
                    self.notify.warning('street perf trace (_wholeStreetPropStep):\n%s' % ''.join(traceback.format_stack(limit=20)))
            self._perfAgg.maybeFlush(streetPerfDebugIntervalFrames.getValue(), topN)
        return task.cont

    def visibilityOn(self):
        if wholeStreetLoading:
            self._cancelWholeStreetPropTask()
            perfOn = streetPerfDebug.getValue()
            threshold = max(0, streetPerfDebugThresholdMs.getValue()) / 1000.0
            topN = streetPerfDebugTopN.getValue()
            if perfOn and self._perfAgg is None:
                self._perfAgg = _PerfAgg(self.notify, 'Street(%s)' % (getattr(self, 'zoneId', '?'),))
            if perfOn:
                t0 = time.perf_counter()
                self.showAllVisibles()
                dt = time.perf_counter() - t0
                self._perfAgg.add('showAllVisibles', dt)
                if dt >= threshold:
                    self.notify.warning('street perf hitch: showAllVisibles dt=%.2fms nodeList=%d' % (dt * 1000.0, len(getattr(self.loader, 'nodeList', ()) or ())))  # noqa: E501
                    if streetPerfDebugTrace.getValue():
                        self.notify.warning('street perf trace (showAllVisibles):\n%s' % ''.join(traceback.format_stack(limit=20)))
                self._perfAgg.maybeFlush(streetPerfDebugIntervalFrames.getValue(), topN)
            else:
                self.showAllVisibles()
            if streetWholeStaggerProps.getValue() and self.loader.nodeList:
                self._wholeStreetPropTaskName = uniqueName('wholeStreetProps')
                self._wholeStreetPropNodes = self._orderedWholeStreetVisgroups()
                self._wholeStreetPropIndex = 0
                taskMgr.add(self._wholeStreetPropStep, self._wholeStreetPropTaskName)
            else:
                for node in self._orderedWholeStreetVisgroups():
                    if perfOn:
                        t1 = time.perf_counter()
                        self.loader.enterAnimatedProps(node)
                        dt = time.perf_counter() - t1
                        self._perfAgg.add('enterAnimatedProps', dt)
                        if dt >= threshold:
                            self.notify.warning('street perf hitch: enterAnimatedProps visgroup=%s dt=%.2fms' % (node.getName(), dt * 1000.0))
                            if streetPerfDebugTrace.getValue():
                                self.notify.warning('street perf trace (enterAnimatedProps):\n%s' % ''.join(traceback.format_stack(limit=20)))
                    else:
                        self.loader.enterAnimatedProps(node)
                if perfOn:
                    self._perfAgg.maybeFlush(streetPerfDebugIntervalFrames.getValue(), topN)
            # Still track the local avatar's zone transitions for gameplay logic,
            # but keep visibility/network interest for the whole street.
            self.accept('on-floor', self.enterZone)
        else:
            self.hideAllVisibles()
            self.accept('on-floor', self.enterZone)

    def visibilityOff(self):
        self._cancelWholeStreetPropTask()
        self.ignore('on-floor')
        self.showAllVisibles()

    def doEnterZone(self, newZoneId):
        if wholeStreetLoading:
            perfOn = streetPerfDebug.getValue()
            threshold = max(0, streetPerfDebugThresholdMs.getValue()) / 1000.0
            topN = streetPerfDebugTopN.getValue()
            if perfOn and self._perfAgg is None:
                self._perfAgg = _PerfAgg(self.notify, 'Street(%s)' % (getattr(self, 'zoneId', '?'),))
            if newZoneId != self.zoneId:
                if newZoneId is not None:
                    if perfOn:
                        t0 = time.perf_counter()
                    if not __astron__:
                        base.cr.sendSetZoneMsg(newZoneId)
                    else:
                        # Request interest in all visgroups for this street, not just the adjacency list.
                        tSet0 = time.perf_counter() if perfOn else None
                        allZones = set(self.loader.zoneDict.keys())
                        allZones.add(ZoneUtil.getBranchZone(newZoneId))
                        allZones.add(newZoneId)
                        if perfOn:
                            dtSet = time.perf_counter() - tSet0
                            self._perfAgg.add('buildAllZonesInterestSet', dtSet)
                            if dtSet >= threshold:
                                self.notify.warning('street perf hitch: buildAllZonesInterestSet dt=%.2fms size=%d' % (dtSet * 1000.0, len(allZones)))
                        base.cr.sendSetZoneMsg(newZoneId, sorted(allZones))
                    if perfOn:
                        dt = time.perf_counter() - t0
                        self._perfAgg.add('sendSetZoneMsg', dt)
                        if dt >= threshold:
                            self.notify.warning('street perf hitch: sendSetZoneMsg newZoneId=%s dt=%.2fms (whole street interests=%d)' % (newZoneId, dt * 1000.0, len(getattr(self.loader, "zoneDict", {}) or {})))  # noqa: E501
                            if streetPerfDebugTrace.getValue():
                                self.notify.warning('street perf trace (sendSetZoneMsg):\n%s' % ''.join(traceback.format_stack(limit=20)))
                    self.notify.debug('Entering Zone %d' % newZoneId)
                self.zoneId = newZoneId
                if perfOn:
                    t1 = time.perf_counter()
                    self._refreshStreetHolidayLights()
                    dt = time.perf_counter() - t1
                    self._perfAgg.add('_refreshStreetHolidayLights', dt)
                    if dt >= threshold:
                        self.notify.warning('street perf hitch: _refreshStreetHolidayLights dt=%.2fms' % (dt * 1000.0))
                    self._perfAgg.maybeFlush(streetPerfDebugIntervalFrames.getValue(), topN)
                else:
                    self._refreshStreetHolidayLights()
            return

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
                if not __astron__:
                    base.cr.sendSetZoneMsg(newZoneId)
                else:
                    visZones = [ZoneUtil.getBranchZone(newZoneId)]
                    visZones += [self.loader.node2zone[x] for x in self.loader.nodeDict[newZoneId]]
                    if newZoneId not in visZones:
                        visZones.append(newZoneId)
                    base.cr.sendSetZoneMsg(newZoneId, visZones)
                self.notify.debug('Entering Zone %d' % newZoneId)
            self.zoneId = newZoneId
        self._refreshStreetHolidayLights()

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
            inDreamland = False
            if place.zoneId and ZoneUtil.getCanonicalHoodId(place.zoneId) == ToontownGlobals.DonaldsDreamland:
                inDreamland = True
            if Filename(signTexturePath).exists():
                signTexture = loader.loadTexture(loaderTexturePath)
            for sign in signs:
                if Filename(signTexturePath).exists():
                    sign.setTexture(signTexture, 1)
                if inDreamland:
                    sign.setColorScale(0.525, 0.525, 0.525, 1)

        return
