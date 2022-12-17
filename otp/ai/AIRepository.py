from pandac.PandaModules import *
from otp.otpbase import OTPGlobals
from .AIMsgTypes import *
from direct.showbase.PythonUtil import Functor
from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.fsm import ClassicFSM
from direct.fsm import State
from direct.task import Task
from direct.distributed.AsyncRequest import cleanupAsyncRequests
from direct.distributed import ParentMgr
from direct.distributed.ConnectionRepository import ConnectionRepository
import sys
import os
import copy
import types
from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator
from direct.distributed.NetMessenger import NetMessenger
from direct.showbase.ContainerLeakDetector import ContainerLeakDetector
from direct.showbase import MessengerLeakDetector
from direct.showbase import LeakDetectors
from direct.showbase.GarbageReportScheduler import GarbageReportScheduler
from otp.avatar.DistributedPlayerAI import DistributedPlayerAI
from otp.distributed import OtpDoGlobals
from otp.ai.GarbageLeakServerEventAggregatorAI import GarbageLeakServerEventAggregatorAI
import time
import gc

class AIRepository(ConnectionRepository):
    """
    The new AIRepository base class
    
    It does not have:
      - district or shard code (see AIDistrict.py)
      - friends or secret friends code
      - a collision traverser
      
    of course, a derived class may add those.
    
    It does have:
      + object creation code
      + channel listening code
      + context allocator/manager
    """
    notify = directNotify.newCategory("AIRepository")

    InitialContext = 100000

    def __init__(
            self, mdip, mdport, esip, esport, dcFileNames,
            serverId,
            minChannel, maxChannel, dcSuffix = 'AI'):
        assert self.notify.debugStateCall(self)
        self._channels={}
        self.AIRunningNetYield = simbase.config.GetBool('ai-running-net-yield', 0)        
        
        self._msgBundleNames = []

        # doId->requestDeleted object
        self._requestDeletedDOs = {}
        
        ConnectionRepository.__init__(
                self, ConnectionRepository.CM_NATIVE, simbase.config)
        self.dcSuffix = dcSuffix
        
        simbase.setupCpuAffinities(minChannel)

        self.distributedObjectRequests=set()

        self.context=self.InitialContext
        self.contextToClassName={}
        self.setClientDatagram(0)

        self.readDCFile(dcFileNames = dcFileNames)

        # Save the state server id
        self.serverId = serverId

        # Save the connect info
        self.mdurl = URLSpec(mdip, 1)
        self.esurl = URLSpec(esip, 1)

        if not self.mdurl.hasPort():
            self.mdurl.setPort(mdport)

        if not self.esurl.empty() and not self.esurl.hasPort():
            self.esurl.setPort(esport)

        self.notify.info("event server at %s." % (repr(self.esurl)))

        # UDP socket for sending events to the event server.
        self.udpSock = None
        
        if not self.esurl.empty():
            udpEventServer = SocketAddress()
            if not udpEventServer.setHost(self.esurl.getServer(), self.esurl.getPort()):
                self.notify.warning("Invalid host for event server: %s" % (self.esurl))

            self.udpSock = SocketUDPOutgoing()
            self.udpSock.InitToAddress(udpEventServer)

        # Save the ranges of channels that the AI controls
        self.minChannel = minChannel
        self.maxChannel = maxChannel
        self.notify.info("dynamic doIds in range [%s, %s], total %s" % (
            minChannel, maxChannel, maxChannel - minChannel + 1))
        assert maxChannel >= minChannel

        # initialize the channel allocation
        self.channelAllocator = UniqueIdAllocator(minChannel, maxChannel)

        # Define the ranges of zones.
        self.minZone = self.getMinDynamicZone()
        self.maxZone = self.getMaxDynamicZone()
        self.notify.info("dynamic zoneIds in range [%s, %s], total %s" % (
            self.minZone, self.maxZone, self.maxZone - self.minZone + 1))
        assert self.maxZone >= self.minZone
        self.zoneAllocator = UniqueIdAllocator(self.minZone, self.maxZone)

        if config.GetBool('detect-leaks', 0) or config.GetBool('ai-detect-leaks', 0):
            self.startLeakDetector()

        if config.GetBool('detect-messenger-leaks', 0) or config.GetBool('ai-detect-messenger-leaks', 0):
            self.messengerLeakDetector = MessengerLeakDetector.MessengerLeakDetector(
                'AI messenger leak detector')
            if config.GetBool('leak-messages', 0):
                MessengerLeakDetector._leakMessengerObject()

        if config.GetBool('run-garbage-reports', 0) or config.GetBool('ai-run-garbage-reports', 0):
            noneValue = -1.
            reportWait = config.GetFloat('garbage-report-wait', noneValue)
            reportWaitScale = config.GetFloat('garbage-report-wait-scale', noneValue)
            if reportWait == noneValue:
                reportWait = None
            if reportWaitScale == noneValue:
                reportWaitScale = None
            self.garbageReportScheduler = GarbageReportScheduler(waitBetween=reportWait,
                                                                 waitScale=reportWaitScale)

        self._proactiveLeakChecks = (config.GetBool('proactive-leak-checks', 1) and
                                     config.GetBool('ai-proactive-leak-checks', 1))
        self._crashOnProactiveLeakDetect = config.GetBool('crash-on-proactive-leak-detect', 1)

        # Give ourselves the first channel in the range
        self.ourChannel = self.allocateChannel()

        # These are used to query database objects directly; currently
        # used only for offline utilities.
        self.dbObjContext = 0
        self.dbObjMap = {}

        # The UtilityAIRepository sets this to 0 to indicate we should
        # not do things like issue new catalogs to toons that we load
        # in.  However, in the normal AI repository, we should do
        # these things.
        self.doLiveUpdates = 1
        
        #for generating unqiue names for non-dos, manly used for tasks
        self.keyCounter = 0
        
        self.MaxEpockSpeed = self.config.GetFloat('ai-net-yield-epoch', 1.0/30.0)        
        
        if self.AIRunningNetYield :
            taskMgr.doYield =self.taskManagerDoYieldNetwork

        # use this for time yields without sleeps        
        #taskMgr.doYield = self.taskManagerDoYield

        # Used for moderation of report-a-player feature
        self.centralLogger = self.generateGlobalObject(
            OtpDoGlobals.OTP_DO_ID_CENTRAL_LOGGER,
            "CentralLogger")

        self.garbageLeakLogger = GarbageLeakServerEventAggregatorAI(self)

        taskMgr.add(self._checkBundledMsgs, 'checkBundledMsgs', priority=-100)

        # skip a bit so we miss the startup sequence (it has very long frames as things are set up)
        taskMgr.doMethodLater(2 * 60., self._startPerformanceLogging,
                              'startPerformanceLogging')

        self.connectionName = None
        self.connectionURL = None

    def _startPerformanceLogging(self, task=None):
        period = self.config.GetFloat(
            'ai-performance-log-period',
            self.config.GetFloat('server-performance-log-period',
                                 choice(__dev__, 60. * 10., 60.)
                                 )
            )
        self._sampledMaxFrameDuration = 0.
        self._sampleMaxFrameDuration()
        self._numPyObjs = None
        self._getNumObjCounterLimit = int(max(1, (60 * 60.) / period))
        self._getNumObjCounter = 0
        taskMgr.doMethodLater(period, self._logPerformanceData, 'logPerformanceData')
        return Task.done

    def _sampleMaxFrameDuration(self, task=None):
        self._sampledMaxFrameDuration = max(self._sampledMaxFrameDuration,
                                            globalClock.getMaxFrameDuration())
        # call this at a higher frequency than the frequency at which the global
        # clock completely replaces its frame duration samples. that should ensure that
        # we don't miss a slow frame in the performance logging
        taskMgr.doMethodLater(globalClock.getAverageFrameRateInterval() * .75,
                              self._sampleMaxFrameDuration, 'sampleMaxFrameDuration')
        return Task.done

    def _logPerformanceData(self, task=None):
        avgFrameDur = 1. / globalClock.getAverageFrameRate()
        maxFrameDur = max(self._sampledMaxFrameDuration,
                          globalClock.getMaxFrameDuration())
        self._sampledMaxFrameDuration = 0.
        # gc.get_objects can be slow. only sample object count every once in a while
        self._getNumObjCounter -= 1
        if self._getNumObjCounter <= 0:
            self._numPyObjs = len(gc.get_objects())
            self._getNumObjCounter = self._getNumObjCounterLimit
        self.notify.info(
            'avg frame duration=%fs, max frame duration=%fs, num Python objects=%s' % (
            avgFrameDur, maxFrameDur, self._numPyObjs))
        return Task.again

    def startLeakDetector(self):
        if hasattr(self, 'leakDetector'):
            return False
        firstCheckDelay = config.GetFloat('leak-detector-first-check-delay', -1)
        if firstCheckDelay == -1:
            firstCheckDelay = None
        self.leakDetector = ContainerLeakDetector(
            'AI container leak detector', firstCheckDelay = firstCheckDelay)
        self.accept(self.leakDetector.getLeakEvent(), self._handleLeak)
        self.objectTypesLeakDetector = LeakDetectors.ObjectTypesLeakDetector()
        self.garbageLeakDetector = LeakDetectors.GarbageLeakDetector()
        self.cppMemoryUsageLeakDetector = LeakDetectors.CppMemoryUsage()
        self.taskLeakDetector = LeakDetectors.TaskLeakDetector()
        self.messageListenerTypesLeakDetector = LeakDetectors.MessageListenerTypesLeakDetector()
        # this isn't necessary with the current messenger implementation
        #self.messageTypesLeakDetector = LeakDetectors.MessageTypesLeakDetector()
        return True

    def _getMsgName(self, msgId):
        # we might get a list of message names, use the first one
        return makeList(AIMsgId2Names.get(msgId, 'UNKNOWN MESSAGE: %s' % msgId))[0]

    def _handleLeak(self, container, containerName):
        # TODO: send email with warning
        self.notify.info('sending memory leak server event')
        self.writeServerEvent('memoryLeak', self.ourChannel, '%s|%s|%s|%s' % (
            containerName, len(container), itype(container),
            fastRepr(container, maxLen=1, strFactor=50)))

    def getPlayerAvatars(self):
        return [i for i in self.doId2do.values()
                  if isinstance(i, DistributedPlayerAI)]

    def uniqueName(self, desc):
        return desc+"-"+str(self.serverId)
        
    def trueUniqueName(self, desc):
        self.keyCounter += 1
        return desc+"-"+str(self.serverId)+"-"+str(self.keyCounter)

    def allocateContext(self):
        self.context+=1
        if self.context >= (1<<32):
            self.context=self.InitialContext
        return self.context

    #### Init ####

    def writeServerEvent(self, eventType, who, description, serverId=None):
        """
        Sends the indicated event data to the event server via UDP for
        recording and/or statistics gathering.  All related events
        should be given the same eventType (some arbitrary string).
        The who field should be the numeric or alphanumeric
        representation of who generated this activity; generally this
        will be an avatarId or the doId of the AI or something.  The
        description is a one-line description of the event, possibly
        with embedded vertical bars as separators.
        """
        if not self.udpSock:
            self.notify.debug("Unable to log server event: no udpSock.")
            return

        # Make who be a string (it might be passed in as an integer)
        who = str(who)

        # log the access string for avatar-related messages
        doId = None
        try:
            doId = int(who)
        except:
            pass
        if doId is not None and doId in self.doId2do:
            av = self.getDo(doId)
            if hasattr(av, 'getAccess'):
                description = '%s|%s' % (description, av.getAccess())

        # break it up into chunks that will fit in a UDP packet (max 1024 bytes)
        # leave some room for the header/eventType/who
        maxLen = 900
        breakCount = 0
        # always run this loop at least once
        while True:
            if breakCount > 0:
                eventType = '%s-continued%s' % (eventType, breakCount)

            # Count up the number of bytes in the packet
            length = 2 + 2 + 4 + 2 + len(eventType) + 2 + len(who) + 2 + len(description)
            dg = PyDatagram()
            dg.addUint16(length)
            dg.addUint16(1)  # message type 1: server event
            dg.addUint16(6)  # server type 6: AI server
            dg.addUint32(self.ourChannel)
            dg.addString(eventType)
            dg.addString(who)
            dg.addString(description[:maxLen])
            description = description[maxLen:]

            self.notify.debug('%s|AIevent:%s|%s|%s' % (eventType, self.serverId, who, description))

            if not self.udpSock.Send(dg.getMessage()):
                self.notify.warning("Unable to log server event: %s" % (self.udpSock.GetLastError()))

            if len(description) == 0:
                break
            breakCount += 1

            
    def writeServerStatus(self, who, avatar_count, object_count):
        """
        Sends the Status Packet to the event server via UDP for
        recording. Used to monito the health of a AI Server.
        """
        if not self.udpSock:
            self.notify.debug("Unable to log server Status: no udpSock.")
            return

        # Make who be a string (it might be passed in as an integer)
        #who = str(who)
        who="";

        # Count up the number of bytes in the packet
        length = 2 + 2 + 4 + (len(who)+2) + 4 +4
        dg = PyDatagram()
        dg.addUint16(length)
        dg.addUint16(2)  # message type 2: server event
        dg.addUint16(6)  # server type 6: AI server
        dg.addUint32(self.ourChannel)
        dg.addString(who)
        dg.addUint32(avatar_count)
        dg.addUint32(object_count)

        if not self.udpSock.Send(dg.getMessage()):
            self.notify.warning("Unable to log server status: %s" % (self.udpSock.GetLastError()))

    def writeServerStatus2(self, who, avatar_count, object_count):
        """
        Sends the Status Packet to the event server via UDP for
        recording. Used to monito the health of a AI Server.
        ServerStatus2 has an additional channel code added for a ping message
        We can consolidate the two writeServerStatus messages when toontown can
        adopt the new otp_server
        """
        if not self.udpSock:
            self.notify.debug("Unable to log server Status: no udpSock.")
            return

        # Make who be a string (it might be passed in as an integer)
        #who = str(who)
        who="";

        # Count up the number of bytes in the packet
        length = 2 + 2 + 4 + (len(who)+2) + 8 + 4 + 4
        dg = PyDatagram()
        dg.addUint16(length)
        dg.addUint16(3)  # message type 2: server event
        dg.addUint16(6)  # server type 6: AI server
        dg.addUint32(self.ourChannel)
        dg.addString(who)
        dg.addUint64(self.ourChannel)
        dg.addUint32(avatar_count)
        dg.addUint32(object_count)

        if not self.udpSock.Send(dg.getMessage()):
            self.notify.warning("Unable to log server status: %s" % (self.udpSock.GetLastError()))

    ##### Off #####
    def enterOff(self):
        self.handler = None

    def exitOff(self):
        self.handler = None

    #### connect #####
    def enterConnect(self):
        self.handler = self.handleConnect
        self.lastMessageTime = 0

        self.connect([self.mdurl],
                     successCallback = self._connected,
                     failureCallback = self._failedToConnect)

    def _failedToConnect(self, statusCode, statusString):
        self.fsm.request("noConnection")

    def _connected(self):
        # Register our channel
        self.registerForChannel(self.ourChannel)
        self.netMessenger = NetMessenger(self, (OTP_NET_MSGR_CHANNEL_ID_ALL_AI,))
        ## self.netMessenger.accept("transferDo", self, self.handleTransferDo)

    def _handleIgnorableObjectDelete(self, msgType, di):
        doId = di.getUint32()
        self.notify.debug("Ignoring request to delete doId: " +
                          str(doId))

    def exitConnect(self):
        self.handler = None
        # Clean up the create district tasks
        taskMgr.remove(self.uniqueName("newDistrictWait"))
        del self.lastMessageTime

    ##### PlayGame #####

    def enterPlayGame(self):
        self.handler = self.handlePlayGame
        self.createObjects()

    def handleConnect(self, msgType, di):
        self.lastMessageTime = globalClock.getRealTime()

        if msgType == STATESERVER_DISTRICT_DOWN:
            self._handleValidDistrictDown(msgType, di)
        elif msgType == STATESERVER_DISTRICT_UP:
            self._handleValidDistrictUp(msgType, di)
        elif msgType == STATESERVER_OBJECT_DELETE_RAM:
            self._handleIgnorableObjectDelete(msgType, di)
        else:
            self.handleMessageType(msgType, di)

    def handlePlayGame(self, msgType, di):
        # NOTE: Inheritors may override this to check their
        # own message types before calling this handler
        # See ToontownAIRepository.py for example.
        if msgType == STATESERVER_OBJECT_UPDATE_FIELD:
            self._handleUpdateField(di)
        elif msgType == STATESERVER_OBJECT_CHANGE_ZONE:
            self._handleObjectChangeZone(di)
        elif msgType == STATESERVER_OBJECT_DELETE_RAM:
            self._handleDeleteObject(di)
        elif msgType == DBSERVER_MAKE_FRIENDS_RESP:
            self._handleMakeFriendsReply(di)
        elif msgType == DBSERVER_REQUEST_SECRET_RESP:
            self._handleRequestSecretReply(di)
        elif msgType == DBSERVER_SUBMIT_SECRET_RESP:
            self._handleSubmitSecretReply(di)
        else:
            self.handleMessageType(msgType, di)

    def handleAvatarUsage(self, di):
        """
        Should only be handled by the UD process containing the AvatarManagerUD 
        """
        pass
    
    def handleAccountUsage(self, di):
        """
        Should only be handled by the UD process containing the AvatarManagerUD 
        """
        pass
    
    def handleObjectDeleteDisk(self, di):
        pass
    
    def handleObjectQueryField(self, di):
        assert self.notify.debugStateCall(self)

        doId = di.getUint32()
        fieldId = di.getUint16()
        context = di.getUint32()
        success = di.getUint8()
        if success and context:
            className = self.contextToClassName.pop(context, None)
            # This prevents a crash that occurs when an AI sends a query,
            # crashes, comes back up, then receives the response
            if className:
                dclass = self.dclassesByName.get(className)
                interface = dclass.getFieldByIndex(fieldId)
                packer = DCPacker()
                packer.setUnpackData(di.getRemainingBytes())
                packer.beginUnpack(interface)
                value = packer.unpackObject()
                messenger.send(
                    "doFieldResponse-%s"%(context,), [context, value])
                
    def handleObjectQueryFields(self, di):
        assert self.notify.debugStateCall(self)

        doId = di.getUint32()
        context = di.getUint32()
        success = di.getUint8()
        if success and context:
            className = self.contextToClassName.pop(context)
            # This prevents a crash that occurs when an AI sends a query,
            # crashes, comes back up, then receives the response
            if className:
                dclass = self.dclassesByName.get(className)
                packer = DCPacker()
                objData = {}

                while di.getRemainingSize() > 0:
                    fieldId = di.getUint16()
                    interface = dclass.getFieldByIndex(fieldId)
                    packer.setUnpackData(di.getRemainingBytes())
                    packer.beginUnpack(interface)
                    value = packer.unpackObject()
                    packer.endUnpack()
                    objData[interface.getName()] = value
                    di.skipBytes(packer.getNumUnpackedBytes())

                messenger.send("doFieldResponse-%s"%(context,),[context,objData])
            else:
                self.notify.warning("STATESERVER_OBJECT_QUERY_FIELDS_RESP received with invalid context: %s" % context)
                messenger.send("doFieldQueryFailed-%s"%(context),[context])
        else:
            messenger.send("doFieldQueryFailed-%s"%(context),[context])

    def handleServerPing(self, di):
        assert self.notify.debugStateCall(self)
        # Deconstruct ping message from stateserver
        sec = di.getUint32()
        usec = di.getUint32()
        url = di.getString()
        channel = di.getUint32()

        # Send ping back to state server
        datagram = PyDatagram()
        sender=self.getMsgSender()
        datagram.addServerHeader(
            sender, self.ourChannel, SERVER_PING)           
        # A context that can be used to index the response if needed
        datagram.addUint32(sec)
        datagram.addUint32(usec)
        datagram.addString(url)
        datagram.addUint32(channel)
        self.send(datagram)
        
        

    def handleMessageType(self, msgType, di):
        if msgType == CLIENT_GET_STATE_RESP:
            # This one comes back after we sendSetAvatarIdMsg()
            pass
        elif msgType == DBSERVER_GET_STORED_VALUES_RESP:
            self._handleDatabaseGetStoredValuesResp(di)
        elif msgType == DBSERVER_CREATE_STORED_OBJECT_RESP:
            self._handleDatabaseCreateStoredObjectResp(di)
        elif msgType == STATESERVER_OBJECT_CREATE_WITH_REQUIRED_CONTEXT_RESP:
            self._handleDatabaseGenerateResponse(di)
        elif msgType == STATESERVER_OBJECT_SET_ZONE:
            # import pdb;pdb.set_trace()
            self.handleSetLocation(di)
        elif msgType == STATESERVER_OBJECT_LEAVING_AI_INTEREST:
            # import pdb;pdb.set_trace()
            self.handleDistObjExit(di)
        elif msgType == STATESERVER_QUERY_OBJECT_ALL_RESP:
            self.handleDistObjRequestResponse(di)
        elif msgType == STATESERVER_OBJECT_ENTER_AI_RECV:
            self.handleDistObjEnter(di)
        elif msgType == STATESERVER_OBJECT_ENTERZONE_WITH_REQUIRED_OTHER:
            self.handleDistObjEnterZone(di)
        elif msgType == STATESERVER_QUERY_OBJECT_CHILDREN_RESP:
            # This acts much like a generate with required and other
            self.handleDistObjEnter(di)
        elif msgType == STATESERVER_QUERY_OBJECT_CHILDREN_LOCAL_DONE:
            # This acts much like a generate with required and other
            self.handleQueryObjectChildrenLocalDone(di)
        elif msgType == STATESERVER_OBJECT_ENTER_OWNER_RECV:
            # This message is sent at some stage during avatar creation.
            self.handleDistObjEnterOwner(di)
        elif msgType == STATESERVER_OBJECT_CHANGE_OWNER_RECV:
            self.handleDistObjChangeOwner(di)
        elif msgType == ACCOUNT_AVATAR_USAGE:
            self.handleAvatarUsage(di)
        elif msgType == ACCOUNT_ACCOUNT_USAGE:
            self.handleAccountUsage(di)
        elif msgType == STATESERVER_OBJECT_DELETE_DISK:
            self.handleObjectDeleteDisk(di)
        elif msgType == STATESERVER_OBJECT_QUERY_FIELD_RESP:
            self.handleObjectQueryField(di)
        elif msgType == STATESERVER_OBJECT_QUERY_FIELDS_RESP:
            self.handleObjectQueryFields(di)
        elif msgType == STATESERVER_OBJECT_QUERY_MANAGING_AI:
            pass
        elif msgType == SERVER_PING:
            self.handleServerPing(di)
        else:
            AIRepository.notify.warning(
                "Ignoring unexpected message type: %s in state: %s" %
                (msgType, self.fsm.getCurrentState().getName()))
            if __dev__:
                import pdb
                pdb.set_trace()
    
    def exitPlayGame(self):
        self.handler = None
        self.stopReaderPollTask()
        
        self.deleteDistributedObjects()
        cleanupAsyncRequests()

        # Make sure there are no leftover tasks that shouldn't be here.
        for task in taskMgr.getTasks():
            if (task.name in ("igLoop",
                                "aiSleep",
                                "doLaterProcessor",
                                "eventManager",
                                "tkLoop",
                                )):
                # These tasks are ok
                continue
            else:
                print(taskMgr)
                self.notify.error("You can't leave otp until you clean up your tasks.")

        # Make sure there are no event hooks still hanging.
        if not messenger.isEmpty():
            print(messenger)
            self.notify.error("Messenger should not have any events in it.")

    ##### NoConnection #####

    def enterNoConnection(self):
        self.handler = self.handleMessageType

        AIRepository.notify.warning(
            "Failed to connect to message director at %s." % (repr(self.mdurl)))
        # Wait five seconds, then try to reconnect
        taskMgr.doMethodLater(5, self.reconnect, self.uniqueName("waitToReconnect"))

    def reconnect(self, task):
        self.fsm.request("connect")
        return Task.done

    def exitNoConnection(self):
        self.handler = None
        taskMgr.remove(self.uniqueName("waitToReconnect"))

    ##### General Purpose functions #####

    def createObjects(self):
        # This is meant to be a pure virtual function that gets
        # overridden by inheritors. This is where you should create
        # DistributedObjectAI's (and generate them), create the objects
        # that manage them, as well as spawn
        # any tasks that will create DistributedObjectAI's in the future.
        pass

    def getHandleClassNames(self):
        # This is meant to be a pure virtual function that gets
        # overridden by inheritors.

        # This function should return a tuple or list of string names
        # that represent distributed object classes for which we want
        # to make a special 'handle' class available.  For instance,
        # to make the DistributedToonHandleAI class available, this
        # function should return ('DistributedToon',).
        return ()

    def handleDistObjRequestResponse(self, di):
        assert self.notify.debugStateCall(self)
        context = di.getUint32()
        parentId = di.getUint32()
        zoneId = di.getUint32()
        classId = di.getUint16()
        doId = di.getUint32()
        # if there's no context, there's no point in doing anything else
        if context:
            # Look up the dclass
            dclass = self.dclassesByNumber[classId]
            # Create a new distributed object
            distObj = self._generateFromDatagram(
                parentId, zoneId, dclass, doId, di, addToTables=False)
            #distObj.isQueryAllResponse = True

            self.writeServerEvent('doRequestResponse', doId, '%s'%(context,))
            messenger.send("doRequestResponse-%s"%(context,), [context, distObj])

    def postGenerate(self, context, distObj):
        parentId = distObj.parentId
        zoneId = distObj.zoneId
        doId = distObj.doId
        self.distributedObjectRequests.discard(doId)
        distObj.setLocation(parentId, zoneId)
        self.writeServerEvent('distObjEnter', doId, '')
    
    def handleDistObjEnter(self, di):       
        assert self.notify.debugStateCall(self)
        context = di.getUint32()
        parentId = di.getUint32()
        zoneId = di.getUint32()
        classId = di.getUint16()
        doId = di.getUint32()
        # Look up the dclass
        dclass = self.dclassesByNumber[classId]
        # Is it in our dictionary?
        if self.doId2do.has_key(doId):
            self.notify.warning("Object Entered " + str(doId) +
                                " re-entered without exiting")
        # Create a new distributed object
        distObj = self._generateFromDatagram(
            parentId, zoneId, dclass, doId, di)
        self.postGenerate(context, distObj)

        # Put it in the dictionary - Is it already in our dictionary?  Not
        # sure why or how this happens, but it does come up from time to
        # time in production
        # Asad Todo take out this security check for now don't publish to toontown!!!
##         if self.doId2do.has_key(doId):
##             self.writeServerEvent('suspicious', doId, 'Avatar re-entered without exiting')
##             # Note: until we figure out what is causing this bug, it will be an error
##             # This is listed as bug 50608 in the production remarks db
##             self.notify.error("Avatar %s re-entered without exiting" % doId)


    def handleDistObjEnterZone(self, di):       
        assert self.notify.debugStateCall(self)
        parentId = di.getUint32()
        zoneId = di.getUint32()
        classId = di.getUint16()
        doId = di.getUint32()
        # Look up the dclass
        dclass = self.dclassesByNumber[classId]
        # Is it in our dictionary?
        if self.doId2do.has_key(doId):
            self.notify.warning("Object Entered " + str(doId) +
                                " re-entered without exiting")
        # Create a new distributed object
        distObj = self._generateFromDatagram(
            parentId, zoneId, dclass, doId, di)
        # self.postGenerate(context, distObj)

        # Put it in the dictionary - Is it already in our dictionary?  Not
        # sure why or how this happens, but it does come up from time to
        # time in production
        # Asad Todo take out this security check for now don't publish to toontown!!!
##         if self.doId2do.has_key(doId):
##             self.writeServerEvent('suspicious', doId, 'Avatar re-entered without exiting')
##             # Note: until we figure out what is causing this bug, it will be an error
##             # This is listed as bug 50608 in the production remarks db
##             self.notify.error("Avatar %s re-entered without exiting" % doId)


    def handleDistObjEnterOwner(self, di):
        # TEMP
        return self.handleDistObjEnter(di)
    """
        assert self.notify.debugStateCall(self)
        # The context is bogus
        context = di.getUint32()
        # The zone the avatar is in
        parentId = di.getUint32()
        zoneId = di.getUint32()
        # Get the class Id
        classId = di.getUint16()
        # Get the DO Id
        doId = di.getUint32()
        # Look up the dclass
        dclass = self.dclassesByNumber[classId]
        self.notify.info(
            'ignoring owner create, context=%s, parentId=%s, '
            'zoneId=%s, doId=%s, dclass=%s' % (
            context, parentId, zoneId, doId, dclass.getName()))
            """

    def handleDistObjChangeOwner(self, di):
        assert self.notify.debugStateCall(self)
        doId = di.getUint32()
        newOwnerId = di.getUint32()
        oldOwnerId = di.getUint32()
        self.notify.info(
            'ignoring owner change, '
            'doId=%s, newOwnerId=%s, oldOwnerID=%s' % (
            doId, newOwnerId, oldOwnerId))

    def getDeleteDoIdEvent(self, doId):
        # this event is sent after the object is deleted,
        # and is sent even if the object was not in the tables.
        return 'AIRDeleteDoId-%s' % doId

    def handleDistObjExit(self, di):
        # Get the distributed object id
        doId = di.getUint32()
        self.notify.debug("handleDistObjExit %s" % doId)

        # If it is in the dictionary, remove it.
        obj = self.doId2do.get(doId)
        if obj:
            self.deleteDistObject(obj)
        else:
            self.notify.warning("DistObj " + str(doId) +
                                " exited, but never entered.")

        # announce delete event for this doId, even if obj doesn't exist
        # send it after we delete any existing object
        messenger.send(self.getDeleteDoIdEvent(doId))

        # TODO: remove this in favor of getDeleteDoIdEvent
        # Throw an event telling everyone that the distObj is gone
        self._announceDistObjExit(doId)

    def _announceDistObjExit(self, doId):
        pass

    def _generateFromDatagram(self, parentId, zoneId, dclass, doId, di, addToTables=True):
        if (self.doId2do.has_key(doId)):
            # added to prevent objects already generated from being generated again (was
            # happening with some traded inventory objects, quests specfically)
            return self.doId2do[doId]
        # We got a datagram telling us to create a new DO instance
        classDef = dclass.getClassDef()
        try:
            distObj = classDef(self)
        except TypeError as e:
            self.notify.error('%s (class %s, parentId %d, zoneId %d, doId %d)' % \
                              (e, dclass.getName(), parentId, zoneId, doId))
        distObj.dclass = dclass
        # Assign it an Id
        distObj.doId = doId
        # Since the distObj has been created explicitly from the
        # server, we do not own its doId, and hence we shouldn't try
        # to deallocate it.
        distObj.doNotDeallocateChannel = 1

        # init the parentId and zoneId
        if addToTables:
            # add the new DO to the tables
            # let addDoToTables set the parentId and zoneId, it ignores
            # the location if it matches what's already on the object
            distObj.parentId = None
            distObj.zoneId = None
            self.addDOToTables(distObj, location = (parentId,zoneId))
        else:
            distObj.parentId = parentId
            distObj.zoneId = zoneId

        # Generate this Object
        distObj.generate()

        # Update the required fields
        distObj.updateAllRequiredOtherFields(dclass, di)

        return distObj

    def _handleUpdateField(self, di):
        # Get the Do Id
        doId = di.getUint32()
        # Find the do
        do = self.doId2do[doId]
        # Let the dclass finish the job
        do.dclass.receiveUpdate(do, di)

    def _handleObjectChangeZone(self, di):
        # Get the Do Id
        doId = di.getUint32()
        newParentId = di.getUint32()
        newZoneId = di.getUint32()
        oldParentId = di.getUint32()
        oldZoneId = di.getUint32()
        # Find the do
        do = self.doId2do.get(doId)
        if do is None:
            self.notify.warning(
                'handleObjectChangeZone: (NOT PRESENT) %s:(%s, %s)->(%s, %s)' %(
                doId, oldParentId, oldZoneId, newParentId, newZoneId))
        else:
            self.notify.debug('handleObjectChangeZone: %s:(%s, %s)->(%s, %s)' %(
                doId, oldParentId, oldZoneId, newParentId, newZoneId))
            # TODO: pass in the old parent and old zone
            do.setLocation(newParentId, newZoneId) #, oldParentId, oldZoneId)

    def _handleDeleteObject(self, di):
        # Get the DO Id
        doId = di.getUint32()
        obj = self.doId2do.get(doId)
        if obj:
            # If it is in the dictionary, remove it.
            self.deleteDistObject(obj)
        else:
            # Otherwise ignore it
            AIRepository.notify.warning(
                "Asked to delete non-existent DistObjAI " + str(doId))

        # announce delete event for this doId, even if obj doesn't exist
        messenger.send(self.getDeleteDoIdEvent(doId))

    def sendUpdate(self, do, fieldName, args):
        #print("---------------sendUpdate--")
        #print(do)
        #print(do.doId)
        #print(fieldName)
        #print(args)
        dg = do.dclass.aiFormatUpdate(
                fieldName, do.doId, do.doId, self.ourChannel, args)
        self.sendDatagram(dg)        

    def sendUpdateToDoId(self, dclassName, fieldName, doId, args,
                         channelId=None):
        """
        channelId can be used as a recipient if you want to bypass the normal
        airecv, ownrecv, broadcast, etc.  If you don't include a channelId
        or if channelId == doId, then the normal broadcast options will
        be used.
        
        See Also: def queryObjectField
        """
        dclass=self.dclassesByName.get(dclassName+self.dcSuffix)
        assert dclass is not None
        if channelId is None:
            channelId=doId
        if dclass is not None:
            dg = dclass.aiFormatUpdate(
                    fieldName, doId, channelId, self.ourChannel, args)
            self.send(dg)

    def createDgUpdateToDoId(self, dclassName, fieldName, doId, args,
                         channelId=None):
        """
        channelId can be used as a recipient if you want to bypass the normal
        airecv, ownrecv, broadcast, etc.  If you don't include a channelId
        or if channelId == doId, then the normal broadcast options will
        be used.
        
        This is just like sendUpdateToDoId, but just returns
        the datagram instead of immediately sending it.
        """
        result = None
        dclass=self.dclassesByName.get(dclassName+self.dcSuffix)
        assert dclass is not None
        if channelId is None:
            channelId=doId
        if dclass is not None:
            dg = dclass.aiFormatUpdate(
                    fieldName, doId, channelId, self.ourChannel, args)
            result = dg
        return result

    def sendUpdateToGlobalDoId(self, dclassName, fieldName, doId, args):
        """
        Used for sending messages from an AI directly to an
        uber object.
        """
        dclass = self.dclassesByName.get(dclassName)
        assert dclass, 'dclass %s not found in DC files' % dclassName
        dg = dclass.aiFormatUpdate(
            fieldName, doId, doId, self.ourChannel, args)
        self.send(dg)
        
    def sendUpdateToChannel(self, do, channelId, fieldName, args):
        dg = do.dclass.aiFormatUpdate(
                fieldName, do.doId, channelId, self.ourChannel, args)
        self.sendDatagram(dg)

    def sendUpdateToChannelFrom(self, do, channelId, fieldName, fromid, args):
        dg = do.dclass.aiFormatUpdate(fieldName, do.doId, channelId,
                                      fromid, args)
        self.send(dg)

    def startMessageBundle(self, name):
        # start bundling messages together. Use this for instance if you want to
        # make sure that location and position of an object are processed atomically
        # on the state server, to prevent clients from getting the new location and an
        # old position (relative to old location) on client generate of the object
        self._msgBundleNames.append(name)
        ConnectionRepository.startMessageBundle(self)
    def sendMessageBundle(self, senderChannel):
        # stop bundling messages and send the bundle
        # senderChannel is typically the doId of the object affected by the messages
        ConnectionRepository.sendMessageBundle(self, self.districtId, senderChannel)
        self._msgBundleNames.pop()

    def _checkBundledMsgs(self, task=None):
        # message bundles should not last across frames
        num = len(self._msgBundleNames)
        while len(self._msgBundleNames):
            self.notify.warning('abandoning message bundle: %s' % self._msgBundleNames.pop())
        if num > 0:
            self.abandonMessageBundles()
            self.notify.error('message bundling leak, see warnings above (most recent first)')
        return task.cont
        
    def registerForChannel(self, channelNumber):
        if self._channels.get(channelNumber):
            # We are already registered for this channel.
            return
        self._channels[channelNumber]=1
        # Time to send a register for channel message to the msgDirector
        datagram = PyDatagram()
#        datagram.addServerControlHeader(CONTROL_SET_CHANNEL)
        datagram.addInt8(1)
        datagram.addChannel(CONTROL_MESSAGE)
        datagram.addUint16(CONTROL_SET_CHANNEL)
        
        datagram.addChannel(channelNumber)
        self.send(datagram)

    def addPostSocketClose(self, themessage):
        # Time to send a register for channel message to the msgDirector
        datagram = PyDatagram()
#        datagram.addServerControlHeader(CONTROL_ADD_POST_REMOVE)        
        datagram.addInt8(1)
        datagram.addChannel(CONTROL_MESSAGE)
        datagram.addUint16(CONTROL_ADD_POST_REMOVE)

        datagram.addString(themessage.getMessage())
        self.send(datagram)

    def addPostSocketCloseUD(self, dclassName, fieldName, doId, args):
        dclass = self.dclassesByName.get(dclassName)
        assert dclass, 'dclass %s not found in DC files' % dclassName
        dg = dclass.aiFormatUpdate(
            fieldName, doId, doId, self.ourChannel, args)
        self.addPostSocketClose(dg)

    def unregisterForChannel(self, channelNumber):
        if self._channels.get(channelNumber) is None:
            # We are already unregistered for this channel.
            return
        del self._channels[channelNumber]
        # Time to send a unregister for channel message to the msgDirector
        datagram = PyDatagram()
#        datagram.addServerControlHeader(CONTROL_REMOVE_CHANNEL)                
        datagram.addInt8(1)
        datagram.addChannel(CONTROL_MESSAGE)
        datagram.addUint16(CONTROL_REMOVE_CHANNEL)

        datagram.addChannel(channelNumber)
        self.send(datagram)

    #----------------------------------
    
    def addAvatarToChannels(self, avatarId, listOfChannels):
        """
        avatarId is a 32 bit doId
        """
        assert self.notify.debugCall()
        self.addConnectionToChannels((1<<32)+avatarId, listOfChannels)

    def removeAvatarFromChannels(self, avatarId, listOfChannels):
        """
        avatarId is a 32 bit doId
        """
        assert self.notify.debugCall()
        self.removeConnectionToChannels((1<<32)+avatarId, listOfChannels)

    def addConnectionToChannels(self, targetConnection, listOfChannels):
        """
        avatarId is a 32 bit doId
        """
        assert self.notify.debugCall()
        dg = PyDatagram()
        dg.addServerHeader(
            targetConnection, self.serverId, CLIENT_AGENT_OPEN_CHANNEL)             
        for i in listOfChannels:
            dg.addUint64(i)
        self.send(dg)

    def removeConnectionToChannels(self, targetConnection, listOfChannels):
        """
        avatarId is a 32 bit doId
        """
        assert self.notify.debugCall()
        dg = PyDatagram()
        dg.addServerHeader(
            targetConnection, self.serverId, CLIENT_AGENT_CLOSE_CHANNEL)                
        for i in listOfChannels:
            dg.addUint64(i)
        self.send(dg)

    def addInterestToConnection(self, targetConnection, interestId,
            contextId, parentDoId, zoneIdList):
        """
        Allows the AIRepository to initiate interest on the client.
        See otp.ai.AIInterestHandles for a list of interestId's to use.
        """
        assert self.notify.debugCall()
        dg = PyDatagram()
        dg.addServerHeader(
            (1<<32)+targetConnection, self.serverId,
            CLIENT_AGENT_SET_INTEREST)

        # Set the high bit to indicate that the interest is being governed by
        # the AI and not the client
        dg.addUint16((1<<15)+interestId)
        dg.addUint32(contextId)
        dg.addUint32(parentDoId)
        dg.addUint32(contextId)
        if isinstance(zoneIdList, types.ListType):
            # sort and remove repeated entries
            zIdSet = set(zoneIdList)
            for zoneId in zIdSet:
                dg.addUint32(zoneId)
        else:
            dg.addUint32(zoneIdList)
        self.send(dg)

    def removeInterestFromConnection(self, targetConnection, interestId,
            contextId=0):
        """
        Allows the AIRepository to remove interest on the client.
        See otp.ai.AIInterestHandles for a list of interestId's to use.
        """
        assert self.notify.debugCall()
        dg = PyDatagram()
        dg.addServerHeader(
            (1<<32)+targetConnection, self.serverId,
            CLIENT_AGENT_REMOVE_INTEREST)
        # set the high bit to indicate that the interest is being governed by
        # the AI and not the client
        dg.addUint16((1<<15)+interestId)
        dg.addUint32(contextId)
        self.send(dg)        

    def setAllowClientSend(self, avatarId,
                           dObject, fieldNameList = []):
        """
        Allow an AI to temporarily give a client 'clsend' privileges
        on a particular fields on a particular object.  This should
        be used on fields that are 'ownsend' by default. When you want
        to revoke these privileges, use clearAllowClientSend() to end
        these privileges.
        """
        assert self.notify.debugCall()
        dg = PyDatagram()
        dg.addServerHeader(
            (1<<32)+avatarId, self.serverId,
            CLIENT_SET_FIELD_SENDABLE)

        # Set the high bit to indicate that the interest is being governed by
        # the AI and not the client
        dg.addUint32(dObject.doId)
        assert isinstance(fieldNameList, types.ListType)

        dclass = dObject.dclass
        # sort and remove repeated entries as we discover the field
        # ids for the specified names
        fieldIdSet = set(dclass.getFieldByName(name).getNumber() \
                         for name in fieldNameList)

        # insert the fieldIds into the datagram
        for fieldId in sorted(fieldIdSet):
            dg.addUint16(fieldId)          
        self.send(dg)

    def clearAllowClientSend(self, avatarId, dObject):
        self.setAllowClientSend(avatarId, dObject)
        
    # ----------------------------------
    
    def setConnectionName(self, name):
        self.connectionName = name
        # Time to send a register for channel message to the msgDirector
        datagram = PyDatagram()
        # datagram.addServerControlHeader(CONTROL_SET_CON_NAME)                        
        datagram.addInt8(1)
        datagram.addChannel(CONTROL_MESSAGE)
        datagram.addUint16(CONTROL_SET_CON_NAME)
        
        datagram.addString(name)
        self.send(datagram)

    def setConnectionURL(self, url):
        self.connectionURL = url
        # Time to send a register for channel message to the msgDirector
        datagram = PyDatagram()
        # datagram.addServerControlHeader(CONTROL_SET_CON_NAME)                        
        datagram.addInt8(1)
        datagram.addChannel(CONTROL_MESSAGE)
        datagram.addUint16(CONTROL_SET_CON_URL)
        
        datagram.addString(url)
        self.send(datagram)

    def deleteObjects(self):
        # This is meant to be a pure virtual function that gets
        # overridden by inheritors.
        # This function is where objects that manage DistributedObjectAI's
        # should be cleaned up. Since this is only called during a district
        # shutdown of some kind, it is not useful to delete the existing
        # DistributedObjectAI's, but rather to just make sure that they
        # are no longer referenced, and no new ones are created.
        pass

    def allocateChannel(self):
        channel=self.channelAllocator.allocate()
        if channel==-1:
            raise RuntimeError("channelAllocator.allocate() is out of channels")
        if self.channelAllocator.fractionUsed()>0.75:
            # There is some debate about how bad it is to run out of
            # channels.  Being ignorant about what exactly will happen
            # if a channel is reused too quickly, we decided to bail
            # out if we got low on channels.  By the way, being low on
            # channels is not the real problem.  The problem is reusing
            # a channel too soon after it's freed.  There is an assumption
            # here that if there are a lot of free channels and the
            # channels are reused in the same order that they are freed,
            # then there is a good chance that any allocated channel has
            # "aged" properly.
            # Schuyler has daydreamed about a system that will track the age
            # of freed ids and sleep or flag an error as apropriate.  See him
            # for details (esp. if you want to write a cross-platform version
            # of said feature).
            raise RuntimeError("Dangerously low on channels.")
        # Sanity check
        assert (channel >= self.minChannel) and (channel <= self.maxChannel)

        if 0:              ## used to debug the channel code
            import traceback
            if not hasattr(self, "debug_dictionary"):
                self.debug_dictionary = {}
                __builtins__["debug_dictionary"] = self.debug_dictionary

            for id in   self.debug_dictionary.keys():
                if not self.doId2do.has_key(id):
                    print("--------------------- Not In DOID table")
                    print(id)
                    #traceback.print_list(self.debug_dictionary[id])
                    print(self.debug_dictionary[id])
                    del self.debug_dictionary[id] # never report it again ..

            self.debug_dictionary[channel] = traceback.extract_stack(None,7)

        return channel

    def deallocateChannel(self, channel):
        if 0:      ## used to debug the channel code   .. see above
            del self.debug_dictionary[channel]

        self.channelAllocator.free(channel)

    def getMinDynamicZone(self):
        # Override this to return the minimum allowable value for a
        # dynamically-allocated zone id.
        return 0

    def getMaxDynamicZone(self):
        # Override this to return the maximum allowable value for a
        # dynamically-allocated zone id.
        return 0

    def allocateZone(self):
        zoneId=self.zoneAllocator.allocate()
        if zoneId==-1:
            raise RuntimeError("zoneAllocator.allocate() is out of zoneIds")
        # Sanity check
        assert (zoneId >= self.minZone) and (zoneId <= self.maxZone)
        return zoneId

    def deallocateZone(self, zoneId):
        self.zoneAllocator.free(zoneId)

    # NOTE: the public API for this is in DistributedObjectAI.b_setLocation()
    # @report(types = ['args'], dConfigParam = 'avatarmgr')
    def sendSetLocation(self, distobj, parentId, zoneId, owner=None):
        datagram = PyDatagram()
        datagram.addServerHeader(
            distobj.doId, self.ourChannel, STATESERVER_OBJECT_SET_ZONE)
        datagram.addUint32(parentId)
        datagram.addUint32(zoneId)
        self.send(datagram)

    @report(types = ['args'], dConfigParam = 'avatarmgr')
    def sendSetLocationDoId(self, doId, parentId, zoneId, owner=None):
        datagram = PyDatagram()
        datagram.addServerHeader(
            doId, self.ourChannel, STATESERVER_OBJECT_SET_ZONE)
        datagram.addUint32(parentId)
        datagram.addUint32(zoneId)
        self.send(datagram)

    @report(types = ['args'], dConfigParam = 'avatarmgr')
    def sendSetOwnerDoId(self, doId, ownerId):
        # allowed channels are (from http://aspen.online.disney.com/mediawiki/index.php/P2P%2C_OWNERSHIP_STUFF):
        # account<<32 + avatar
        #       1<<32 + avatar
        #       1<<32 + account
        datagram = PyDatagram()
        datagram.addServerHeader(
            doId, self.ourChannel, STATESERVER_OBJECT_SET_OWNER_RECV)
        datagram.addChannel((1<<32) + ownerId)
        self.send(datagram)

    @report(types = ['args'], dConfigParam = 'avatarmgr')
    def sendClearOwnerDoId(self, doId):
        datagram = PyDatagram()
        datagram.addServerHeader(
            doId, self.ourChannel, STATESERVER_OBJECT_SET_OWNER_RECV)
        datagram.addChannel(0)
        self.send(datagram)
            
    def sendSetZone(self, distobj, zoneId):
        self.notify.error("non-district types should not call sendSetZone")

    def startTrackRequestDeletedDO(self, obj):
        if obj.doId in self._requestDeletedDOs:
            self.notify.warning('duplicate requestDelete for %s %s' % (obj.__class__.__name__, obj.doId))
        # store object and time of requestDelete
        self._requestDeletedDOs[obj.doId] = (obj, globalClock.getRealTime())

    def stopTrackRequestDeletedDO(self, obj):
        # sometimes objects are deleted without having requested a delete
        #assert obj.doId in self._requestDeletedDOs
        if (hasattr(obj,'doId')) and (obj.doId in self._requestDeletedDOs):
            del self._requestDeletedDOs[obj.doId]

    def getRequestDeletedDOs(self):
        # returns list of (obj, age of delete request), sorted by descending age
        response = []
        now = globalClock.getRealTime()
        for obj, requestTime in self._requestDeletedDOs.values():
            # calculate how long it has been since delete was requested
            age = now - requestTime
            index = 0
            while index < len(response):
                if age > response[index][1]:
                    break
                index += 1
            response.insert(index, (obj, age))
        return response

    @report(types = ['args'], dConfigParam = 'avatarmgr')
    def requestDelete(self, distobj):
        # Create a message
        datagram = PyDatagram()
        datagram.addServerHeader(
            distobj.doId, self.ourChannel, STATESERVER_OBJECT_DELETE_RAM)        
        # The Id of the object in question
        datagram.addUint32(distobj.doId)
        self.send(datagram)

    @report(types = ['args'], dConfigParam = 'avatarmgr')
    def requestDeleteDoId(self, doId):
        # Create a message
        datagram = PyDatagram()
        datagram.addServerHeader(
            doId, self.ourChannel, STATESERVER_OBJECT_DELETE_RAM)        
        # The Id of the object in question
        datagram.addUint32(doId)
        self.send(datagram)

    def requestDeleteDoIdFromDisk(self, doId):
        # Create a message
        datagram = PyDatagram()
        datagram.addServerHeader(
            doId, self.ourChannel, STATESERVER_OBJECT_DELETE_DISK)
        # The Id of the object in question
        datagram.addUint32(doId)
        self.send(datagram)

    def getDatabaseGenerateResponseEvent(self, context):
        # handler must accept (doId)
        return 'DBGenResponse-%s' % context

    def _handleDatabaseGenerateResponse(self, di):
        assert self.notify.debugCall(self)
        context = di.getUint32()
        doId = di.getUint32()
        self.notify.debug(
            '_handleDatabaseGenerateResponse, context=%s, doId=%s' %
            (context, doId))
        messenger.send(
            self.getDatabaseGenerateResponseEvent(context), [doId])
            
    def getDatabaseIdForClassName(self, className):
        assert 0
        # You probably want to override this to return something better.
        return 0

    def requestDatabaseGenerate(
            self, classId, context,
            parentId=0, zoneId=0,
            ownerChannel=0, ownerAvId=None,
            databaseId=None, values = None):
        """
        context is any 32 bit integer to be used a reference
            for this message (and its reply).
        parentId may be 0 or a valid distributed object ID.
        zoneId may be 0 or a valid zone ID (int32).
        ownerChannel may be 0 or a valid owner channel (int64)
          OR
            ownerAvId may be None or a player doId
        databaseId is a distributed object ID for the database
            (maybe a constant).
        values is a dictionary of other member values (or None)

        To get doId of new object, listen for this event:
          air.getDatabaseGenerateResponseEvent(context)
        If object location was provided, and the location is on this
        district, the object will be generated shortly after the
        above message is sent.
        """
        AIRepository.notify.debugCall()
        #self.notify.info('requestDatabaseGenerate, class=%s, context=%s' %
        #                 (classId, context))
        if ownerChannel == 0 and ownerAvId is not None:
            ownerChannel = (1<<32) + ownerAvId
        if self.dclassesByNumber.has_key(classId):
            dclass = self.dclassesByNumber[classId]
        else:
            if self.dclassesByName.has_key(classId):
                dclass = self.dclassesByName[classId]
            elif self.dclassesByName.has_key(classId+self.dcSuffix):
                dclass = self.dclassesByName[classId+self.dcSuffix]
            elif self.dclassesByName.has_key(classId+'AI'):
                dclass = self.dclassesByName[classId+'AI']
            else:
                self.notify.warning("dclass not found %s"%(classId,))
                if __dev__:
                    import pdb; pdb.set_trace()
        if databaseId is None:
            databaseId=self.getDatabaseIdForClassName(dclass.getName())
        if values is None:
            if simbase.newDBRequestGen:
                dg = dclass.aiDatabaseGenerateContext(
                    context, parentId, zoneId, ownerChannel,
                    databaseId, self.ourChannel)
            else:
                dg = dclass.aiDatabaseGenerateContextOld(
                    context, parentId, zoneId,
                    databaseId, self.ourChannel)
            self.send(dg)
        else:
            packer = DCPacker()
            packer.rawPackUint8(1)                
            packer.rawPackUint64(databaseId)
            packer.rawPackUint64(self.ourChannel)
            packer.rawPackUint16(
                STATESERVER_OBJECT_CREATE_WITH_REQUIRED_CONTEXT)
            ## packer.rawPackUint16(
            ##     STATESERVER_OBJECT_CREATE_WITH_REQUIR_OTHER_CONTEXT)
            packer.rawPackUint32(parentId)
            packer.rawPackUint32(zoneId)
            if simbase.newDBRequestGen:
                packer.rawPackUint64(ownerChannel)
            packer.rawPackUint16(dclass.getNumber())
            packer.rawPackUint32(context)

            optionalFields = []

            for i in range(dclass.getNumInheritedFields()):
                field = dclass.getInheritedField(i)
                if field.asMolecularField() == None:
                    if field.isRequired():
                        # Packs Required Fields
                        value = values.get(field.getName(), None)
                        packer.beginPack(field)

                        if value == None:
                            packer.packDefaultValue()
                        else:
                            if not field.packArgs(packer, value):
                                raise StandardError
                        packer.endPack()
                    else:
                        value = values.get(field.getName(), None)

                        if value != None:
                            fieldDec = {}
                            fieldDec['field'] = field
                            fieldDec['value'] = value
                            optionalFields.append(fieldDec)

            packer.rawPackUint16(len(optionalFields))

            # Packs Optional Fields
            for i in optionalFields:
                field = i['field']
                value = i['value']

                packer.rawPackUint16(field.getNumber())
                packer.beginPack(field)
                field.packArgs(packer, value)
                packer.endPack()

            if packer.hadError():
                raise StandardError

            dg = Datagram(packer.getString())
            self.send(dg)
            
    def lostConnection(self):
        ConnectionRepository.lostConnection(self)
        sys.exit()

    def handleDatagram(self, di):
        if self.notify.getDebug():
            print("AIRepository received datagram:")
            di.getDatagram().dumpHex(ostream)

        channel=self.getMsgChannel()
        if channel in self.netMessenger.channels:
            self.netMessenger.handle(di.getString())
        else:
            self.handler(self.getMsgType(), di)

    def deleteDistObject(self, do):
        assert self.notify.debugCall()

        # if not hasattr(do, "isQueryAllResponse") or not do.isQueryAllResponse:
        do.sendDeleteEvent()
        # Remove it from the dictionary
        self.removeDOFromTables(do)
        # Delete the object itself
        do.delete()
        if self._proactiveLeakChecks:
            # make sure we're not leaking
            do.detectLeaks()

    def sendAnotherGenerate(self, distObj, toChannel):
        assert self.notify.debugCall()
        dg = distObj.dclass.aiFormatGenerate(
                distObj, distObj.doId, distObj.parentId, distObj.zoneId,
                toChannel, self.ourChannel, [])
        self.send(dg)
        
    def generateWithRequired(self, distObj, parentId, zoneId, optionalFields=[]):
        assert self.notify.debugStateCall(self)
        # Assign it an id
        distObj.doId = self.allocateChannel()
        # Put the new DO in the dictionaries
        self.addDOToTables(distObj, location = (parentId,zoneId))
        # Send a generate message
        distObj.sendGenerateWithRequired(self, parentId, zoneId, optionalFields)


    # this is a special generate used for estates, or anything else that
    # needs to have a hard coded doId as assigned by the server
    def generateWithRequiredAndId(
            self, distObj, doId, parentId, zoneId, optionalFields=[]):
        assert self.notify.debugStateCall(self)
        # Assign it an id
        distObj.doId = doId
        # Since the distObj has been created explicitly from the
        # server, we do not own its doId, and hence we shouldn't try
        # to deallocate it.
        distObj.doNotDeallocateChannel = 1
        # Put the new DO in the dictionaries
        self.addDOToTables(distObj, location = (parentId,zoneId))
        # Send a generate message
        distObj.sendGenerateWithRequired(self, parentId, zoneId, optionalFields)
        
    def queryObjectAll(self, doId, context=0):
        """
        Get a one-time snapshot look at the object.
        """
        assert self.notify.debugStateCall(self)
        # Create a message
        datagram = PyDatagram()
        datagram.addServerHeader(
            doId, self.ourChannel, STATESERVER_QUERY_OBJECT_ALL)           
        # A context that can be used to index the response if needed
        datagram.addUint32(context)
        self.send(datagram)
        # Make sure the message gets there.
        self.flush()

    def queryObjectZoneIds(self, stateServerId, obj2ZoneDict):
        # obj2ZoneDict should be a dict looking like this:
        #    { objId : [zoneId, zoneId, ...],
        #      objId : [zoneId, zoneId, ...],
        #    }
        assert self.notify.debugStateCall(self)        
        # Create a message
        datagram = PyDatagram()
        datagram.addServerHeader(
            stateServerId, self.ourChannel, STATESERVER_QUERY_ZONE_OBJECT_ALL)
        numObjs = len(obj2ZoneDict.keys())
        datagram.addUint16(numObjs)
        for objId, zoneIds in obj2ZoneDict.values():
            datagram.addUint32(objId)
            datagram.addUint16(len(zoneIds))
            for zoneId in zoneIds:
                datagram.addUint32(zoneId)
        # This is for a forwarding system that I did not hook up.
        # Ask Roger for details.
        datagram.addUint16(0)
        self.send(datagram)
        # Make sure the message gets there.
        self.flush()

    def queryObjectChildrenLocal(self, parentId, context=0):
        assert self.notify.debugStateCall(self)        
        # Create a message
        datagram = PyDatagram()
        datagram.addServerHeader(
            self.serverId, self.ourChannel, STATESERVER_QUERY_OBJECT_CHILDREN_LOCAL)
        datagram.addUint32(parentId)
        datagram.addUint32(context)
        self.send(datagram)
        # Make sure the message gets there.
        self.flush()

    def handleQueryObjectChildrenLocalDone(self, di):
        # We asked to get generates for all objects that are children of
        # us. This is the callback that says the server is done sending all
        # those generates.
        assert self.notify.debugCall()
        parentId = di.getUint16()
        context = di.getUint32()
        parent = self.doId2do.get(parentId)
        if parent:
            parent.handleQueryObjectChildrenLocalDone(context)
        else:
            self.notify.warning('handleQueryObjectChildrenLocalDone: parentId %s not found' %
                                parentId)

    @report(types = ['args'], dConfigParam = 'avatarmgr')
    def queryObjectFieldId(self, doId, fieldId, context=0):
        """
        Get a one-time snapshot look at the object.
        """
        assert self.notify.debugStateCall(self)
        # Create a message
        datagram = PyDatagram()
        datagram.addServerHeader(
            doId, self.ourChannel, STATESERVER_OBJECT_QUERY_FIELD)           
        datagram.addUint32(doId)
        datagram.addUint16(fieldId)
        # A context that can be used to index the response if needed
        datagram.addUint32(context)
        self.send(datagram)
        # Make sure the message gets there.
        self.flush()

    @report(types = ['args'], dConfigParam = 'avatarmgr')
    def queryObjectFieldIds(self, doId, fieldIds, context=0):
        """
        Get a one-time snapshot look at the object.
        Query multiple field IDs from the same object.
        """
        assert self.notify.debugStateCall(self)
        # Create a message
        datagram = PyDatagram()
        datagram.addServerHeader(
            doId, self.ourChannel, STATESERVER_OBJECT_QUERY_FIELDS)           
        datagram.addUint32(doId)
        datagram.addUint32(context)
        for x in fieldIds:
            datagram.addUint16(x)
        self.send(datagram)
        # Make sure the message gets there.
        self.flush()

    @report(types = ['args'], dConfigParam = 'avatarmgr')
    def queryObjectStringFieldIds(self, dbId, objString, fieldIds, context=0):
        """
        Get a one-time snapshot look at the object.
        Query multiple field IDs from the same object, by object string.
        """
        assert self.notify.debugStateCall(self)
        # Create a message
        dg = PyDatagram()
        dg.addServerHeader(
            dbId, self.ourChannel, STATESERVER_OBJECT_QUERY_FIELDS_STRING)           
        dg.addString(objString)
        dg.addUint32(context)
        for x in fieldIds:
            dg.addUint16(x)
        self.send(dg)
        # Make sure the message gets there.
        self.flush()

    @report(types = ['args'], dConfigParam = 'avatarmgr')
    def queryObjectStringFields(
            self, dbId, dclassName, objString, fieldNames, context=0):
        """
        Get a one-time snapshot look at the object.
        Query multiple field names from the same object, by object string.
        """
        assert self.notify.debugStateCall(self)
        assert len(dclassName) > 0
        for fn in fieldNames:
            assert len(fn) > 0
        dclass = self.dclassesByName.get(dclassName)
        assert dclass is not None
        if not dclass:
            self.notify.error(
                "queryObjectStringFields invalid dclassName %s"%(dclassName))
            return
        if dclass is not None:
            fieldIds = []
            for fn in fieldNames:
                id = dclass.getFieldByName(fn).getNumber()
                assert id
                if not id:
                    self.notify.error(
                        "queryObjectStrongFields invalid field %s, %s"%(doId,fn))
                    return
                fieldIds.append(id)
            self.queryObjectStringFieldIds(dbId,objString,fieldIds,context)

    @report(types = ['args'], dConfigParam = 'avatarmgr')
    def queryObjectField(self, dclassName, fieldName, doId, context=0):
        """
        See Also: def sendUpdateToDoId
        """
        assert self.notify.debugStateCall(self)
        assert len(dclassName) > 0
        assert len(fieldName) > 0
        assert doId > 0
        dclass = self.dclassesByName.get(dclassName)
        assert dclass is not None
        if not dclass:
            self.notify.error(
                "queryObjectField invalid dclassName %s, %s"%(doId, fieldName))
            return
        if dclass is not None:
            fieldId = dclass.getFieldByName(fieldName).getNumber()
            assert fieldId # is 0 a valid value?
            if not fieldId:
                self.notify.error(
                    "queryObjectField invalid field %s, %s"%(doId, fieldName))
                return
            self.queryObjectFieldId(doId, fieldId, context)

    @report(types = ['args'], dConfigParam = 'avatarmgr')
    def queryObjectFields(self, dclassName, fieldNames, doId, context=0):
        """
        See Also: def sendUpdateToDoId
        """
        assert self.notify.debugStateCall(self)
        assert len(dclassName) > 0
        assert len(fieldNames) > 0
        for fieldName in fieldNames:
            assert len(fieldName) > 0
        assert doId > 0
        dclass = self.dclassesByName.get(dclassName)
        assert dclass is not None
        if not dclass:
            self.notify.error(
                "queryObjectField invalid dclassName %s, %s"%(doId, fieldName))
            return
        if dclass is not None:
            fieldIds = [dclass.getFieldByName(fieldName).getNumber() \
                        for fieldName in fieldNames]
            # is 0 a valid value?
            assert 0 not in fieldIds
            if 0 not in fieldIds:
                self.queryObjectFieldIds(doId, fieldIds, context)
            else:
                assert self.notify.error(
                        "queryObjectFields invalid field in %s, %s"%(doId, repr(fieldNames)))
                
        
    def requestDistributedObject(self, doId):
        """
        Ask for the object to be added to the private
        distributed object cache.

        Normally a query object all does not actually enter the object
        returned into the doId2do table.  This function will change a query
        request to a distributed object that is part of the normal set of
        objects on this server. 
        """
        assert self.notify.debugCall()
        distObj = self.doId2do.get(doId)
        if distObj is not None:
            # Already have it
            return
        if doId in self.distributedObjectRequests:
            # Already requested it
            return
        #todo: add timeout for to remove request
        self.distributedObjectRequests.add(doId)
        context=self.allocateContext()
        self.acceptOnce(
            "doRequestResponse-%s"%(context,), 
            self.postGenerate, [])
        self.registerForChannel(doId)
        self.queryObjectAll(doId, context)

    # If you want to set the airecv you should set the location
    def setAIReceiver(self, objectId, aiChannel=None):
        # Create a message
        datagram = PyDatagram()
        datagram.addServerHeader(
            self.ourChannel, self.ourChannel, STATESERVER_ADD_AI_RECV)                       
        # The Id of the object in question
        datagram.addUint32(objectId)
        if aiChannel is None:
            aiChannel = self.ourChannel
        datagram.addUint32(aiChannel)
        # Send the message
        self.send(datagram)
        # Make sure the message gets there.
        self.flush()

    def replaceMethod(self, oldMethod, newFunction):
        return 0

    def sendUpdate(self, distObj, fieldName, args):
        dg = distObj.dclass.aiFormatUpdate(
            fieldName, distObj.doId, distObj.doId, self.ourChannel, args)
        self.sendDatagram(dg)

    def _handleDatabaseGetStoredValuesResp(self, di):
        context = di.getUint32()
        dbObj = self.dbObjMap.get(context)
        if dbObj:
            del self.dbObjMap[context]
            dbObj.getFieldsResponse(di)
        else:
            AIRepository.notify.warning(
                "Ignoring unexpected context %d for DBSERVER_GET_STORED_VALUES" %
                context)

    def _handleDatabaseCreateStoredObjectResp(self, di):
        context = di.getUint32()
        dbObj = self.dbObjMap.get(context)
        if dbObj:
            del self.dbObjMap[context]
            dbObj.handleCreateObjectResponse(di)
        else:
            AIRepository.notify.warning(
                "Ignoring unexpected context %d for DBSERVER_CREATE_STORED_OBJECT" %
                 context)

    # LEADERBOARD
    def setLeaderboardValue(self, category, whoId, whoName, value, senderId=None):
        self.writeServerEvent('setLeaderboardValue', whoId,
                              '%s|%s|%s' % (whoName, category, value))
        dcfile = self.getDcFile()
        dclass = dcfile.getClassByName('LeaderBoard')
        if senderId is None:
            senderId = self.districtId
        dg = dclass.aiFormatUpdate('setValue',
                                   OtpDoGlobals.OTP_DO_ID_LEADERBOARD_MANAGER,
                                   OtpDoGlobals.OTP_DO_ID_LEADERBOARD_MANAGER,
                                   senderId,
                                   [[category], whoId, whoName, value])
        self.send(dg)

    ##################################################################
    # msgsend is set by the C code  on the repository.. These Functions
    # will let you parse the special encoded sender id  if you want to
    # know the AvatarID or The AccountID of the Sender..

    def getAccountIdFromSender(self):
        """
        only works on the dc updates from the client agent
        """
        return self.getMsgSender() >> 32

    def getAvatarIdFromSender(self):
        """
        only works on the dc updates from the client agent
        """
        return self.getMsgSender() & 0xffffffff

    def getSenderReturnChannel(self):
        return self.getMsgSender()


    ########################################
    #  Network reading and time device.. for ai's
    def  taskManagerDoYieldNetwork(self , frameStartTime, nextScheuledTaksTime):
        minFinTime = frameStartTime + self.MaxEpockSpeed
        if nextScheuledTaksTime > 0 and nextScheuledTaksTime < minFinTime:
            minFinTime = nextScheuledTaksTime
                                    
        self.networkBasedReaderAndYielder(self.handleDatagram,globalClock,minFinTime)                           

        if not self.isConnected():
            self.stopReaderPollTask()
            self.lostConnection()
     
    ############################################################### 
    # Optimized version of old behavior..
    def readerPollUntilEmpty(self, task):
        self.checkDatagramAi(self.handleDatagram)                   
        if not self.isConnected():
            self.stopReaderPollTask()
            self.lostConnection()

        return Task.cont

    
    ############################################################### 
    # This can be used to do time based yielding instead of the sleep task.
    def  taskManagerDoYield(self , frameStartTime, nextScheuledTaksTime):
        minFinTime = frameStartTime + self.MaxEpockSpeed
        if nextScheuledTaksTime > 0 and nextScheuledTaksTime < minFinTime:
            minFinTime = nextScheuledTaksTime
            
        delta = minFinTime - globalClock.getRealTime()
        while(delta > 0.002):
            time.sleep(delta)           
            delta = minFinTime - globalClock.getRealTime()
            
            
    ############################################################### 
    # This can be used to do time based yielding instead of the sleep task.
    def startReaderPollTask(self):
        if not self.AIRunningNetYield:
            ConnectionRepository.startReaderPollTask(self)
        else:                    
            print('########## startReaderPollTask New ')
            self.stopReaderPollTask()
            self.accept(CConnectionRepository.getOverflowEventName(),self.handleReaderOverflow)
