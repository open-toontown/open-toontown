from panda3d.core import *
from panda3d.toontown import *

from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM, State, StateData
from direct.showbase.PythonUtil import Functor, PriorityCallbacks
from direct.task import Task

from otp.otpbase import OTPGlobals

from toontown.distributed.ToontownMsgTypes import *
from toontown.toonbase import ToontownGlobals

from . import ZoneUtil


class QuietZoneState(StateData.StateData):
    notify = DirectNotifyGlobal.directNotify.newCategory('QuietZoneState')
    Disable = False
    Queue = []

    def __init__(self, doneEvent):
        StateData.StateData.__init__(self, doneEvent)
        self.fsm = ClassicFSM.ClassicFSM('QuietZoneState', [State.State('off', self.enterOff, self.exitOff, ['waitForQuietZoneResponse']),
         State.State('waitForQuietZoneResponse', self.enterWaitForQuietZoneResponse, self.exitWaitForQuietZoneResponse, ['waitForZoneRedirect']),
         State.State('waitForZoneRedirect', self.enterWaitForZoneRedirect, self.exitWaitForZoneRedirect, ['waitForSetZoneResponse']),
         State.State('waitForSetZoneResponse', self.enterWaitForSetZoneResponse, self.exitWaitForSetZoneResponse, ['waitForSetZoneComplete']),
         State.State('waitForSetZoneComplete', self.enterWaitForSetZoneComplete, self.exitWaitForSetZoneComplete, ['waitForLocalAvatarOnShard']),
         State.State('waitForLocalAvatarOnShard', self.enterWaitForLocalAvatarOnShard, self.exitWaitForLocalAvatarOnShard, ['off'])], 'off', 'off')
        self._enqueueCount = 0
        self.fsm.enterInitialState()

    def load(self):
        self.notify.debug('load()')

    def unload(self):
        self._dequeue()
        self.notify.debug('unload()')
        del self.fsm

    @classmethod
    def enqueueState(cls, state, requestStatus):
        cls.Queue = [(state, requestStatus)] + cls.Queue
        state._enqueueCount += 1
        if len(cls.Queue) == 1:
            cls.startNextQueuedState()

    @classmethod
    def dequeueState(cls, state):
        s, requestStatus = cls.Queue.pop()
        s._enqueueCount -= 1
        if len(cls.Queue) > 0:
            cls.startNextQueuedState()

    @classmethod
    def startNextQueuedState(cls):
        state, requestStatus = cls.Queue[-1]
        state._start(requestStatus)

    def _dequeue(self):
        newQ = []
        for item in self.__class__.Queue:
            state, requestStatus = item
            if state is not self:
                newQ.append(item)

        self.__class__.Queue = newQ

    def getEnterWaitForSetZoneResponseMsg(self):
        return 'enterWaitForSetZoneResponse-%s' % (id(self),)

    def getQuietZoneLeftEvent(self):
        return '%s-%s' % (base.cr.getQuietZoneLeftEvent(), id(self))

    def getSetZoneCompleteEvent(self):
        return 'setZoneComplete-%s' % (id(self),)

    def enter(self, requestStatus):
        self.notify.debug('enter(requestStatus=' + str(requestStatus) + ')')
        self._requestStatus = requestStatus
        self._leftQuietZoneCallbacks = None
        self._setZoneCompleteCallbacks = None
        self._leftQuietZoneLocalCallbacks = {}
        self._setZoneCompleteLocalCallbacks = {}
        self.enqueueState(self, requestStatus)
        return

    def _start(self, requestStatus):
        base.transitions.fadeScreen(1.0)
        self.fsm.request('waitForQuietZoneResponse')

    def getRequestStatus(self):
        return self._requestStatus

    def exit(self):
        self.notify.debug('exit()')
        del self._requestStatus
        base.transitions.noTransitions()
        self.fsm.request('off')
        self._dequeue()

    def waitForDatabase(self, description):
        if base.endlessQuietZone:
            return
        base.cr.waitForDatabaseTimeout(requestName='quietZoneState-%s' % description)

    def clearWaitForDatabase(self):
        base.cr.cleanupWaitingForDatabase()

    def addLeftQuietZoneCallback(self, callback, priority = None):
        if self._leftQuietZoneCallbacks:
            return self._leftQuietZoneCallbacks.add(callback, priority)
        else:
            token = PriorityCallbacks.GetToken()
            fdc = SubframeCall(callback, taskMgr.getCurrentTask().getPriority() - 1)
            self._leftQuietZoneLocalCallbacks[token] = fdc
            return token

    def removeLeftQuietZoneCallback(self, token):
        if token is not None:
            lc = self._leftQuietZoneLocalCallbacks.pop(token, None)
            if lc:
                lc.cleanup()
            if self._leftQuietZoneCallbacks:
                self._leftQuietZoneCallbacks.remove(token)
        return

    def addSetZoneCompleteCallback(self, callback, priority = None):
        if self._setZoneCompleteCallbacks:
            return self._setZoneCompleteCallbacks.add(callback, priority)
        else:
            token = PriorityCallbacks.GetToken()
            fdc = SubframeCall(callback, taskMgr.getCurrentTask().getPriority() - 1)
            self._setZoneCompleteLocalCallbacks[token] = fdc
            return token

    def removeSetZoneCompleteCallback(self, token):
        if token is not None:
            lc = self._setZoneCompleteLocalCallbacks.pop(token, None)
            if lc:
                lc.cleanup()
            if self._setZoneCompleteCallbacks:
                self._setZoneCompleteCallbacks.remove(token)
        return

    if not __astron__:
        def handleWaitForQuietZoneResponse(self, msgType, di):
            # self.notify.debug('handleWaitForQuietZoneResponse(' + 'msgType=' + str(msgType) + ', di=' + str(di) + ')')
            if msgType == CLIENT_CREATE_OBJECT_REQUIRED:
                base.cr.handleQuietZoneGenerateWithRequired(di)
            elif msgType == CLIENT_CREATE_OBJECT_REQUIRED_OTHER:
                base.cr.handleQuietZoneGenerateWithRequiredOther(di)
            elif msgType == CLIENT_OBJECT_UPDATE_FIELD:
                base.cr.handleQuietZoneUpdateField(di)
            elif msgType in QUIET_ZONE_IGNORED_LIST:
                self.notify.debug('ignoring unwanted message from previous zone')
            else:
                base.cr.handlePlayGame(msgType, di)
    else:
        def handleWaitForQuietZoneResponse(self, msgType, di):
            # self.notify.debug('handleWaitForQuietZoneResponse(' + 'msgType=' + str(msgType) + ', di=' + str(di) + ')')
            if msgType == CLIENT_ENTER_OBJECT_REQUIRED:
                base.cr.handleQuietZoneGenerateWithRequired(di)
            elif msgType == CLIENT_ENTER_OBJECT_REQUIRED_OTHER:
                base.cr.handleQuietZoneGenerateWithRequiredOther(di)
            elif msgType == CLIENT_OBJECT_SET_FIELD:
                base.cr.handleQuietZoneUpdateField(di)
            elif msgType in QUIET_ZONE_IGNORED_LIST:
                self.notify.debug('ignoring unwanted message from previous zone')
            else:
                base.cr.handlePlayGame(msgType, di)

    if not __astron__:
        def handleWaitForZoneRedirect(self, msgType, di):
            # self.notify.debug('handleWaitForZoneRedirect(' + 'msgType=' + str(msgType) + ', di=' + str(di) + ')')
            if msgType == CLIENT_CREATE_OBJECT_REQUIRED:
                base.cr.handleQuietZoneGenerateWithRequired(di)
            elif msgType == CLIENT_CREATE_OBJECT_REQUIRED_OTHER:
                base.cr.handleQuietZoneGenerateWithRequiredOther(di)
            elif msgType == CLIENT_OBJECT_UPDATE_FIELD:
                base.cr.handleQuietZoneUpdateField(di)
            else:
                base.cr.handlePlayGame(msgType, di)
    else:
        def handleWaitForZoneRedirect(self, msgType, di):
            # self.notify.debug('handleWaitForZoneRedirect(' + 'msgType=' + str(msgType) + ', di=' + str(di) + ')')
            if msgType == CLIENT_ENTER_OBJECT_REQUIRED:
                base.cr.handleQuietZoneGenerateWithRequired(di)
            elif msgType == CLIENT_ENTER_OBJECT_REQUIRED_OTHER:
                base.cr.handleQuietZoneGenerateWithRequiredOther(di)
            elif msgType == CLIENT_OBJECT_SET_FIELD:
                base.cr.handleQuietZoneUpdateField(di)
            else:
                base.cr.handlePlayGame(msgType, di)

    def enterOff(self):
        self.notify.debug('enterOff()')

    def exitOff(self):
        self.notify.debug('exitOff()')
        self._leftQuietZoneCallbacks = PriorityCallbacks()
        self._setZoneCompleteCallbacks = PriorityCallbacks()
        self._leftQuietZoneLocalCallbacks = {}
        self._setZoneCompleteLocalCallbacks = {}

    def enterWaitForQuietZoneResponse(self):
        # self.notify.debug('enterWaitForQuietZoneResponse(doneStatus=' + str(self._requestStatus) + ')')
        if not self.Disable:
            base.cr.handler = self.handleWaitForQuietZoneResponse
            base.cr.handlerArgs = self._requestStatus
            base.cr.setInQuietZone(True)
        self.setZoneDoneEvent = base.cr.getNextSetZoneDoneEvent()
        self.acceptOnce(self.setZoneDoneEvent, self._handleQuietZoneComplete)
        self.waitForDatabase('WaitForQuietZoneResponse')
        if base.slowQuietZone:

            def sQZR(task):
                base.cr.sendQuietZoneRequest()
                return Task.done

            taskMgr.doMethodLater(base.slowQuietZoneDelay, sQZR, 'slowQuietZone-sendQuietZoneRequest')
        else:
            base.cr.sendQuietZoneRequest()

    def _handleQuietZoneComplete(self):
        self.fsm.request('waitForZoneRedirect')

    def exitWaitForQuietZoneResponse(self):
        self.notify.debug('exitWaitForQuietZoneResponse()')
        self.clearWaitForDatabase()
        base.cr.handler = base.cr.handlePlayGame
        base.cr.handlerArgs = None
        base.cr.setInQuietZone(False)
        self.ignore(self.setZoneDoneEvent)
        del self.setZoneDoneEvent
        return

    def enterWaitForZoneRedirect(self):
        # self.notify.debug('enterWaitForZoneRedirect(requestStatus=' + str(self._requestStatus) + ')')
        if not self.Disable:
            base.cr.handler = self.handleWaitForZoneRedirect
            base.cr.handlerArgs = self._requestStatus
            base.cr.setInQuietZone(True)
        self.waitForDatabase('WaitForZoneRedirect')
        zoneId = self._requestStatus['zoneId']
        avId = self._requestStatus.get('avId', -1)
        allowRedirect = self._requestStatus.get('allowRedirect', 1)
        if avId != -1:
            allowRedirect = 0
        if not base.cr.welcomeValleyManager:
            newZoneId = ZoneUtil.getCanonicalZoneId(zoneId)
            if newZoneId != zoneId:
                self.gotZoneRedirect(newZoneId)
                return
        if allowRedirect and ZoneUtil.isWelcomeValley(zoneId):
            self.notify.info('Requesting AI redirect from zone %s.' % zoneId)
            if base.slowQuietZone:

                def rZI(task, zoneId = zoneId, self = self):
                    base.cr.welcomeValleyManager.requestZoneId(zoneId, self.gotZoneRedirect)
                    return Task.done

                taskMgr.doMethodLater(base.slowQuietZoneDelay, rZI, 'slowQuietZone-welcomeValleyRedirect')
            else:
                base.cr.welcomeValleyManager.requestZoneId(zoneId, self.gotZoneRedirect)
        else:
            self.fsm.request('waitForSetZoneResponse')

    def gotZoneRedirect(self, zoneId):
        if hasattr(self, 'fsm'):
            self.notify.info('Redirecting to zone %s.' % zoneId)
            base.cr.handlerArgs['zoneId'] = zoneId
            base.cr.handlerArgs['hoodId'] = ZoneUtil.getHoodId(zoneId)
            self.fsm.request('waitForSetZoneResponse')

    def exitWaitForZoneRedirect(self):
        self.notify.debug('exitWaitForZoneRedirect()')
        self.clearWaitForDatabase()
        base.cr.handler = base.cr.handlePlayGame
        base.cr.handlerArgs = None
        base.cr.setInQuietZone(False)
        return

    def enterWaitForSetZoneResponse(self):
        # self.notify.debug('enterWaitForSetZoneResponse(requestStatus=' + str(self._requestStatus) + ')')
        if not self.Disable:
            messenger.send(self.getEnterWaitForSetZoneResponseMsg(), [self._requestStatus])
            base.cr.handlerArgs = self._requestStatus
            zoneId = self._requestStatus['zoneId']
            where = self._requestStatus['where']
            base.cr.dumpAllSubShardObjects()
            base.cr.resetDeletedSubShardDoIds()
            if __astron__:
                # Add viszones to streets and Cog HQs:
                visZones = []
                if where == 'street':
                    visZones = self.getStreetViszones(zoneId)
                    if zoneId not in visZones:
                        visZones.append(zoneId)
                    base.cr.sendSetZoneMsg(zoneId, visZones)
                elif where in ('cogHQExterior', 'factoryExterior'):
                    visZones = self.getCogHQViszones(zoneId)
                    if zoneId not in visZones:
                        visZones.append(zoneId)
                if len(visZones) < 1 or (len(visZones) == 1 and visZones[0] == zoneId):
                    base.cr.sendSetZoneMsg(zoneId)
                else:
                    base.cr.sendSetZoneMsg(zoneId, visZones)
            else:
                base.cr.sendSetZoneMsg(zoneId)
            self.waitForDatabase('WaitForSetZoneResponse')
            self.fsm.request('waitForSetZoneComplete')

    if __astron__:
        def getStreetViszones(self, zoneId):
            visZones = [ZoneUtil.getBranchZone(zoneId)]
            # Assuming that the DNA have been loaded by bulk load before this (see Street.py).
            loader = base.cr.playGame.hood.loader
            visZones += [loader.node2zone[x] for x in loader.nodeDict[zoneId]]
            self.notify.debug(f'getStreetViszones(zoneId={zoneId}): returning visZones: {visZones}')
            return visZones

        def getCogHQViszones(self, zoneId):
            loader = base.cr.playGame.hood.loader

            if zoneId in (ToontownGlobals.LawbotOfficeExt, ToontownGlobals.BossbotHQ):
                # There are no viszones for these zones, just return an empty list.
                return []

            # First, we need to load the DNA file for this Cog HQ.
            dnaStore = DNAStorage()
            dnaFileName = loader.genDNAFileName(zoneId)
            loadDNAFileAI(dnaStore, dnaFileName)

            # Next, we need to collect all of the visgroup zone IDs.
            loader.zoneVisDict = {}
            for i in range(dnaStore.getNumDNAVisGroupsAI()):
                visGroup = dnaStore.getDNAVisGroupAI(i)
                groupFullName = visGroup.getName()
                visZoneId = int(base.cr.hoodMgr.extractGroupName(groupFullName))
                visZoneId = ZoneUtil.getTrueZoneId(visZoneId, zoneId)
                visibles = []
                for i in range(visGroup.getNumVisibles()):
                    visibles.append(int(visGroup.getVisibleName(i)))

                # Now we'll store it in the loader since we need them when we enter a Cog battle.
                loader.zoneVisDict[visZoneId] = visibles

            # Finally, we want interest in all visgroups due to this being a Cog HQ.
            visZones = list(loader.zoneVisDict.values())[0]
            self.notify.debug(f'getCogHQViszones(zoneId={zoneId}): returning visZones: {visZones}')
            return visZones

    def exitWaitForSetZoneResponse(self):
        self.notify.debug('exitWaitForSetZoneResponse()')
        self.clearWaitForDatabase()
        base.cr.handler = base.cr.handlePlayGame
        base.cr.handlerArgs = None
        return

    def enterWaitForSetZoneComplete(self):
        # self.notify.debug('enterWaitForSetZoneComplete(requestStatus=' + str(self._requestStatus) + ')')
        if not self.Disable:
            base.cr.handlerArgs = self._requestStatus
            if base.slowQuietZone:

                def delayFunc(self = self):

                    def hSZC(task):
                        self._handleSetZoneComplete()
                        return Task.done

                    taskMgr.doMethodLater(base.slowQuietZoneDelay, hSZC, 'slowQuietZone-sendSetZoneComplete')

                nextFunc = delayFunc
            else:
                nextFunc = self._handleSetZoneComplete
            self.waitForDatabase('WaitForSetZoneComplete')
            self.setZoneDoneEvent = base.cr.getLastSetZoneDoneEvent()
            self.acceptOnce(self.setZoneDoneEvent, nextFunc)
            if base.placeBeforeObjects:
                self._leftQuietZoneCallbacks()
                self._leftQuietZoneCallbacks = None
                fdcs = list(self._leftQuietZoneLocalCallbacks.values())
                self._leftQuietZoneLocalCallbacks = {}
                for fdc in fdcs:
                    if not fdc.isFinished():
                        fdc.finish()

                messenger.send(self.getQuietZoneLeftEvent())
        return

    def _handleSetZoneComplete(self):
        self.fsm.request('waitForLocalAvatarOnShard')

    def exitWaitForSetZoneComplete(self):
        self.notify.debug('exitWaitForSetZoneComplete()')
        self.clearWaitForDatabase()
        base.cr.handler = base.cr.handlePlayGame
        base.cr.handlerArgs = None
        self.ignore(self.setZoneDoneEvent)
        del self.setZoneDoneEvent
        return

    def enterWaitForLocalAvatarOnShard(self):
        self.notify.debug('enterWaitForLocalAvatarOnShard()')
        if not self.Disable:
            base.cr.handlerArgs = self._requestStatus
            self._onShardEvent = localAvatar.getArrivedOnDistrictEvent()
            self.waitForDatabase('WaitForLocalAvatarOnShard')
            if localAvatar.isGeneratedOnDistrict(localAvatar.defaultShard):
                self._announceDone()
            else:
                self.acceptOnce(self._onShardEvent, self._announceDone)

    def _announceDone(self):
        base.localAvatar.startChat()
        if base.endlessQuietZone:
            self._dequeue()
            return
        doneEvent = self.doneEvent
        requestStatus = self._requestStatus
        self._setZoneCompleteCallbacks()
        self._setZoneCompleteCallbacks = None
        fdcs = list(self._setZoneCompleteLocalCallbacks.values())
        self._setZoneCompleteLocalCallbacks = {}
        for fdc in fdcs:
            if not fdc.isFinished():
                fdc.finish()

        messenger.send(self.getSetZoneCompleteEvent(), [requestStatus])
        messenger.send(doneEvent)
        self._dequeue()
        return

    def exitWaitForLocalAvatarOnShard(self):
        self.notify.debug('exitWaitForLocalAvatarOnShard()')
        self.clearWaitForDatabase()
        self.ignore(self._onShardEvent)
        base.cr.handlerArgs = None
        del self._onShardEvent
        return
