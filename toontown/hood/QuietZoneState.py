from pandac.PandaModules import *
from direct.showbase.PythonUtil import Functor, PriorityCallbacks
from direct.task import Task
from toontown.distributed.ToontownMsgTypes import *
from otp.otpbase import OTPGlobals
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import StateData
from direct.fsm import ClassicFSM, State
from direct.fsm import State
import ZoneUtil

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

    def handleWaitForQuietZoneResponse(self, msgType, di):
        self.notify.debug('handleWaitForQuietZoneResponse(' + 'msgType=' + str(msgType) + ', di=' + str(di) + ')')
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

    def handleWaitForZoneRedirect(self, msgType, di):
        self.notify.debug('handleWaitForZoneRedirect(' + 'msgType=' + str(msgType) + ', di=' + str(di) + ')')
        if msgType == CLIENT_CREATE_OBJECT_REQUIRED:
            base.cr.handleQuietZoneGenerateWithRequired(di)
        elif msgType == CLIENT_CREATE_OBJECT_REQUIRED_OTHER:
            base.cr.handleQuietZoneGenerateWithRequiredOther(di)
        elif msgType == CLIENT_OBJECT_UPDATE_FIELD:
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
        self.notify.debug('enterWaitForQuietZoneResponse(doneStatus=' + str(self._requestStatus) + ')')
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
        self.notify.debug('enterWaitForZoneRedirect(requestStatus=' + str(self._requestStatus) + ')')
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
        self.notify.debug('enterWaitForSetZoneResponse(requestStatus=' + str(self._requestStatus) + ')')
        if not self.Disable:
            messenger.send(self.getEnterWaitForSetZoneResponseMsg(), [self._requestStatus])
            base.cr.handlerArgs = self._requestStatus
            zoneId = self._requestStatus['zoneId']
            base.cr.dumpAllSubShardObjects()
            base.cr.resetDeletedSubShardDoIds()
            base.cr.sendSetZoneMsg(zoneId)
            self.waitForDatabase('WaitForSetZoneResponse')
            self.fsm.request('waitForSetZoneComplete')

    def exitWaitForSetZoneResponse(self):
        self.notify.debug('exitWaitForSetZoneResponse()')
        self.clearWaitForDatabase()
        base.cr.handler = base.cr.handlePlayGame
        base.cr.handlerArgs = None
        return

    def enterWaitForSetZoneComplete(self):
        self.notify.debug('enterWaitForSetZoneComplete(requestStatus=' + str(self._requestStatus) + ')')
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
                fdcs = self._leftQuietZoneLocalCallbacks.values()
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
        fdcs = self._setZoneCompleteLocalCallbacks.values()
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
