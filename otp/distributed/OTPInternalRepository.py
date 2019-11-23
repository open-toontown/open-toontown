from direct.directnotify import DirectNotifyGlobal
from direct.distributed.AstronInternalRepository import AstronInternalRepository
if not astronSupport:
    from otp.ai.AIMsgTypes import *
    from panda3d.direct import DCPacker
from direct.distributed.PyDatagram import PyDatagram

class OTPInternalRepository(AstronInternalRepository):
    notify = DirectNotifyGlobal.directNotify.newCategory('OTPInternalRepository')
    dbId = 4003

    def __init__(self, baseChannel, serverId, dcFileNames, dcSuffix, connectMethod, threadedNet):
        AstronInternalRepository.__init__(self, baseChannel, serverId=serverId, dcFileNames=dcFileNames, dcSuffix=dcSuffix, connectMethod=connectMethod, threadedNet=threadedNet)

    def handleConnected(self):
        AstronInternalRepository.handleConnected(self)

    def getAccountIdFromSender(self):
        return (self.getMsgSender() >> 32) & 0xFFFFFFFF

    def getAvatarIdFromSender(self):
        return self.getMsgSender() & 0xFFFFFFFF

    def sendSetZone(self, distObj, zoneId):
        distObj.setLocation(distObj.parentId, zoneId)
        self.sendSetLocation(distObj, distObj.parentId, zoneId)

    # The functions below will be overriding functions from AstronInternalRepository
    # if astron support id disabled to make way for OTP backwards compatibility.
    # (For original function definitions, look at AstronInternalRepository).
    if not astronSupport:

        def addServerControlHeader(self, dg, msgType):
            dg.addUint8(1)
            dg.addUint64(CONTROL_MESSAGE)
            dg.addUint16(msgType)

        def handleConnected(self):
            self.setHandleDatagramsInternally(True)
            if self.serverId:
                self.clearPostRemove()
                dg = PyDatagram()
                dg.addServerHeader(self.serverId, self.ourChannel, STATESERVER_SHARD_REST)
                dg.addChannel(self.ourChannel)
                self.addPostRemove(dg)


        def registerForChannel(self, channel):
            """
            Register for messages on a specific Message Director channel.
            If the channel is already open by this AIR, nothing will happen.
            """

            if channel in self._registeredChannels:
                return
            self._registeredChannels.add(channel)

            dg = PyDatagram()
            self.addServerControlHeader(dg, CONTROL_SET_CHANNEL)
            dg.addChannel(channel)
            self.send(dg)

        def unRegisterChannel(self, channel):
            """
            Unregister a channel subscription on the Message Director. The Message
            Director will cease to relay messages to this AIR sent on the channel.
            """

            if channel not in self._registeredChannels:
                return
            self._registeredChannels.remove(channel)

            dg = PyDatagram()
            self.addServerControlHeader(dg, CONTROL_REMOVE_CHANNEL)
            dg.addChannel(channel)
            self.send(dg)

        def addPostRemove(self, dg):
            """
            Register a datagram with the Message Director that gets sent out if the
            connection is ever lost.
            This is useful for registering cleanup messages: If the Panda3D process
            ever crashes unexpectedly, the Message Director will detect the socket
            close and automatically process any post-remove datagrams.
            """

            dg2 = PyDatagram()
            self.addServerControlHeader(dg2, CONTROL_ADD_POST_REMOVE)
            dg2.addUint64(self.ourChannel)
            dg2.addString(dg.getMessage())
            self.send(dg2)

        def setAI(self, doId, aiChannel):
            """
            Sets the AI of the specified DistributedObjectAI to be the specified channel.
            Generally, you should not call this method, and instead call DistributedObjectAI.setAI.
            """

            dg = PyDatagram()
            dg.addServerHeader(doId, aiChannel, STATESERVER_OBJECT_SET_AI)
            dg.addUint64(aiChannel)
            self.send(dg)

        def handleDatagram(self, di):
            msgType = self.getMsgType()

            if msgType == STATESERVER_OBJECT_ENTER_AI_RECV:
                self.handleObjEntry(di, False)
            elif msgType in (STATESERVER_OBJECT_CHANGING_AI_RECV,
                             STATESERVER_OBJECT_DELETE_RAM):
                self.handleObjExit(di)
            elif msgType == STATESERVER_OBJECT_CHANGE_LOCATION:
                self.handleObjLocation(di)
            #elif msgType in (DBSERVER_CREATE_OBJECT_RESP,
            #                 DBSERVER_OBJECT_GET_ALL_RESP,
            #                 DBSERVER_OBJECT_GET_FIELDS_RESP,
            #                 DBSERVER_OBJECT_GET_FIELD_RESP,
            #                 DBSERVER_OBJECT_SET_FIELD_IF_EQUALS_RESP,
            #                 DBSERVER_OBJECT_SET_FIELDS_IF_EQUALS_RESP):
            #    self.dbInterface.handleDatagram(msgType, di)
            #elif msgType == DBSS_OBJECT_GET_ACTIVATED_RESP:
            #    self.handleGetActivatedResp(di)
            #elif msgType == STATESERVER_OBJECT_GET_LOCATION_RESP:
            #    self.handleGetLocationResp(di)
            #elif msgType == STATESERVER_OBJECT_GET_ALL_RESP:
            #    self.handleGetObjectResp(di)
            #elif msgType == CLIENTAGENT_GET_NETWORK_ADDRESS_RESP:
            #    self.handleGetNetworkAddressResp(di)
            elif msgType >= 20000:
                # These messages belong to the NetMessenger:
                self.netMessenger.handle(msgType, di)
            else:
                self.notify.warning('Received message with unknown MsgType=%d' % msgType)

        def handleObjEntry(self, di, other):
            parentId = di.getUint32()
            zoneId = di.getUint32()
            doId = di.getUint32()
            classId = di.getUint16()

            if classId not in self.dclassesByNumber:
                self.notify.warning('Received entry for unknown dclass=%d! (Object %d)' % (classId, doId))
                return

            if doId in self.doId2do:
                self.notify.info('we already know {}'.format(doId))
                return # We already know about this object; ignore the entry.

            dclass = self.dclassesByNumber[classId]

            self.notify.info('{} now entering'.format(dclass.getName()))

            do = dclass.getClassDef()(self)
            do.dclass = dclass
            do.doId = doId
            # The DO came in off the server, so we do not unregister the channel when
            # it dies:
            do.doNotDeallocateChannel = True
            self.addDOToTables(do, location=(parentId, zoneId))

            # Now for generation:
            do.generate()
            if other:
                do.updateAllRequiredOtherFields(dclass, di)
            else:
                do.updateAllRequiredFields(dclass, di)

        # END if not astronSupport
