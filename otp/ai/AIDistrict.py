from pandac.PandaModules import *
from otp.otpbase import OTPGlobals
from .AIMsgTypes import *
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM
from direct.fsm import State
from direct.task import Task
from direct.distributed import ParentMgr
from otp.ai.AIRepository import AIRepository
from otp.ai.AIZoneData import AIZoneData, AIZoneDataStore
import sys
import os
import copy
from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator

if __debug__:
    import pdb

class AIDistrict(AIRepository):
    notify = DirectNotifyGlobal.directNotify.newCategory("AIDistrict")

    def __init__(
            self, mdip, mdport, esip, esport, dcFileNames,
            districtId, districtName, districtType, serverId,
            minChannel, maxChannel, dcSuffix = 'AI'):
        assert self.notify.debugStateCall(self)
        
        # Save the district Id (needed for calculations in AIRepository code)
        self.districtId = districtId
        self.districtName = districtName
        self.districtType = districtType
        
        AIRepository.__init__(
            self, mdip, mdport, esip, esport, dcFileNames,
            serverId,
            minChannel, maxChannel, dcSuffix)
        self.setClientDatagram(0)
        assert minChannel > districtId
        if hasattr(self, 'setVerbose'):
            if self.config.GetBool('verbose-airepository'):
                self.setVerbose(1)

        # Save the state server id
        self.serverId = serverId

        # Record the reason each client leaves the shard, according to
        # the client.
        self._avatarDisconnectReasons = {}

        # A list of avIds to pretend to disconnect at the next poll
        # cycle, for debugging purposes only.
        self._debugDisconnectIds = []

        # player avatars will increment and decrement this count
        self._population = 0

        # The AI State machine
        self.fsm = ClassicFSM.ClassicFSM('AIDistrict',
                       [State.State('off',
                                    self.enterOff,
                                    self.exitOff,
                                    ['connect']),
                        State.State('connect',
                                    self.enterConnect,
                                    self.exitConnect,
                                    ['districtReset', 'noConnection',
                                     # I added this because Skyler removed the transition to
                                     # districtReset -- Joe
                                     'playGame',
                                     ]),
                        State.State('districtReset',
                                    self.enterDistrictReset,
                                    self.exitDistrictReset,
                                    ['playGame','noConnection']),
                        State.State('playGame',
                                    self.enterPlayGame,
                                    self.exitPlayGame,
                                    ['noConnection']),
                        State.State('noConnection',
                                    self.enterNoConnection,
                                    self.exitNoConnection,
                                    ['connect'])],
                       # initial state
                       'off',
                       # final state
                       'off',
                       )

        self.fsm.enterInitialState()

        self.fsm.request("connect")

    def uniqueName(self, desc):
        return desc+"-"+str(self.districtId)

    def getGameDoId(self):
        self.notify.error('derived must override')

    def incrementPopulation(self):
        self._population += 1
    def decrementPopulation(self):
        if __dev__:
            assert self._population > 0
        self._population = max(0, self._population - 1)

    def getPopulation(self):
        if simbase.fakeDistrictPopulations:
            if not hasattr(self, '_fakePopulation'):
                import random
                self._fakePopulation = random.randrange(1000)
            return self._fakePopulation
        return self._population

    def printPopulationToLog(self, task):
        self.notify.info("district-name %s | district-id %s | population %s" % (self.districtName, self.districtId, self._population))
        return Task.again

    # check if this is a player avatar in a location where they should not be
    def _isValidPlayerLocation(self, parentId, zoneId):
        return True

    #### Init ####

    def writeServerEvent(self, eventType, who, description):
        AIRepository.writeServerEvent(self, eventType, who, description,
                                      serverId=self.districtId)

    #### DistrictReset ####
    def enterDistrictReset(self):
        self.handler = self.handleDistrictReset
        self.deleteDistrict(self.districtId)

    def exitDistrictReset(self):
        self.handler = None

    def handleDistrictReset(self, msgType, di):
        if msgType == STATESERVER_OBJECT_DELETE_RAM:
            doId = di.getUint32()
            self.notify.info("Got request to delete doId: " +str(doId))
            if(doId == self.districtId):
                self.fsm.request("playGame")
        elif msgType == STATESERVER_OBJECT_NOTFOUND:
            doId = di.getUint32()
            self.notify.info("Got Not Found For  doId: " +str(doId))
            if(doId == self.districtId):
                self.fsm.request("playGame")
        else:
            self.handleMessageType(msgType, di)

    #### DistrictReset ####
    def enterPlayGame(self):
        self._zoneDataStore = AIZoneDataStore()
        AIRepository.enterPlayGame(self)
        if simbase.config.GetBool('game-server-tests', 0):
            from otp.distributed import DistributedTestObjectAI
            self.testObject = DistributedTestObjectAI.DistributedTestObjectAI(self)
            self.testObject.generateOtpObject(self.getGameDoId(), 3)
        
        taskMgr.doMethodLater(300, self.printPopulationToLog, self.uniqueName("printPopulationTask"))


    def getZoneDataStore(self):
        """This will crash (as designed) if called outside of the PlayGame state."""
        return self._zoneDataStore

    def getRender(self, parentId, zoneId):
        # distributed objects should call getRender on themselves rather than
        # call this function. Only call this for zones that are actively being
        # used, otherwise the zone data will be destroyed before this function
        # returns
        zd = AIZoneData(self, parentId, zoneId)
        render = zd.getRender()
        zd.destroy()
        return render

    def getNonCollidableParent(self, parentId, zoneId):
        # distributed objects should call getNonCollidableParent on themselves rather than
        # call this function. Only call this for zones that are actively being
        # used, otherwise the zone data will be destroyed before this function
        # returns
        zd = AIZoneData(self, parentId, zoneId)
        ncParent = zd.getNonCollidableParent()
        zd.destroy()
        return ncParent

    def getCollTrav(self, parentId, zoneId, *args, **kArgs):
        # see comment in getRender
        zd = AIZoneData(self, parentId, zoneId)
        collTrav = zd.getCollTrav(*args, **kArgs)
        zd.destroy()
        return collTrav

    def getParentMgr(self, parentId, zoneId):
        # see comment in getRender
        zd = AIZoneData(self, parentId, zoneId)
        parentMgr = zd.getParentMgr()
        zd.destroy()
        return parentMgr

    def exitPlayGame(self):
        if simbase.config.GetBool('game-server-tests', 0):
            self.testObject.requestDelete()
            del self.testObject
        self._zoneDataStore.destroy()
        del self._zoneDataStore
        taskMgr.remove(self.uniqueName("printPopulationTask"))
        AIRepository.exitPlayGame(self)

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
        self.setConnectionName(self.districtName)
        AIRepository._connected(self)
        self.registerShardDownMessage(self.serverId)
        if self.districtType is not None:
            self.fsm.request("districtReset")

    def _handleValidDistrictDown(self, msgType, di):
        downDistrictId = di.getUint32()
        if (downDistrictId != self.districtId):
            self.notify.error("Tried to bring down " +
                              str(self.districtId) +
                              " but " +
                              str(downDistrictId) +
                              " came down instead!")
        else:
            # We don't really need to do anything here.
            pass

    def _handleIgnorableObjectDelete(self, msgType, di):
        doId = di.getUint32()
        self.notify.debug("Ignoring request to delete doId: " +
                          str(doId))

    def _handleValidDistrictUp(self, msgType, di):
        if msgType == STATESERVER_DISTRICT_UP:
            upDistrictId = di.getUint32()
            if (upDistrictId != self.districtId):
                self.notify.error("Tried to bring up " +
                                  str(self.districtId) +
                                  " but " +
                                  str(downDistrictId) +
                                  " came up instead!")
            else:
                self.notify.info("District %s %s is up. Creating objects..." %
                                 (self.districtId, self.districtName))
                self.fsm.request("playGame")

    def exitConnect(self):
        self.handler = None
        # Clean up the create district tasks
        taskMgr.remove(self.uniqueName("newDistrictWait"))
        del self.lastMessageTime

    def readerPollUntilEmpty(self, task):
        # This overrides AIRepository.readerPollUntilEmpty()
        # to provide an additional debugging hook.

        while self._debugDisconnectIds:
            avId = self._debugDisconnectIds.pop()
            self._doDebugDisconnectAvatar(avId)

        try:
            return AIRepository.readerPollUntilEmpty(self, task)
        except Exception as e:
            appendStr(e, '\nSENDER ID: %s' % self.getAvatarIdFromSender())
            raise

    def handleReaderOverflow(self):
        # may as well delete the shard at this point
        self.deleteDistrict(self.districtId)
        raise StandardError("incoming-datagram buffer overflowed, "
                            "aborting AI process")

    ##### General Purpose functions #####

    def getAvatarExitEvent(self, avId):
        return ("districtExit-" + str(avId))

    def debugDisconnectAvatar(self, avId):
        # This function will pretend to disconnect the indicated
        # avatar at the next poll cycle, as if the avatar suddenly
        # disconnected.  This is for the purposes of debugging only.
        # It makes the AI totally forget who this avatar is, but the
        # avatar is still connected to the server.
        self._debugDisconnectIds.append(avId)

    def _doDebugDisconnectAvatar(self, avId):
        obj = self.doId2do.get(avId)
        if obj:
            self.deleteDistObject(obj)
        self._announceDistObjExit(avId)

    def _announceDistObjExit(self, avId):
        # This announces the exiting of this particular avatar
        messenger.send(self.getAvatarExitEvent(avId))

        # This announces generally that an avatar has left.
        #messenger.send("avatarExited")

        # Now we don't need to store the disconnect reason any more.
        try:
            del self._avatarDisconnectReasons[avId]
        except:
            pass

    def setAvatarDisconnectReason(self, avId, disconnectReason):
        # This is told us by the client just before he disconnects.
        self._avatarDisconnectReasons[avId] = disconnectReason

    def getAvatarDisconnectReason(self, avId):
        # Returns the reason (as reported by the client) for an
        # avatar's unexpected exit, or 0 if the reason is unknown.  It
        # is only valid to query this during the handler for the
        # avatar's unexpected-exit event.
        return self._avatarDisconnectReasons.get(avId, 0)

    def _handleUnexpectedDistrictDown(self, di):
        # Get the district Id
        downDistrict = di.getUint32()
        if downDistrict == self.districtId:
            self.notify.warning("Somebody brought my district(" +
                                str(self.districtId) +
                                ") down! I'm shutting down!")
            sys.exit()
        else:
            self.notify.warning("Weird... My district is " +
                                str(self.districtId) +
                                " and I just got a message that district " +
                                str(downDistrict) +
                                " is going down. I'm ignoring it."
                                )

    def _handleUnexpectedDistrictUp(self, di):
        # Get the district Id
        upDistrict = di.getUint32()
        if upDistrict == self.districtId:
            self.notify.warning("Somebody brought my district(" +
                                str(self.districtId) +
                                ") up! I'm shutting down!")
            sys.exit()
        else:
            self.notify.warning("Weird... My district is " +
                                str(self.districtId) +
                                " and I just got a message that district " +
                                str(upDistrict) +
                                " is coming up. I'm ignoring it."
                                )

    def _handleMakeFriendsReply(self, di):
        result = di.getUint8()
        context = di.getUint32()
        messenger.send("makeFriendsReply", [result, context])

    def _handleRequestSecretReply(self, di):
        result = di.getUint8()
        secret = di.getString()
        requesterId = di.getUint32()
        messenger.send("requestSecretReply", [result, secret, requesterId])

    def _handleSubmitSecretReply(self, di):
        result = di.getUint8()
        secret = di.getString()
        requesterId = di.getUint32()
        avId = di.getUint32()
        self.writeServerEvent('entered-secret', requesterId, '%s|%s|%s' % (result, secret, avId))
        messenger.send("submitSecretReply", [result, secret, requesterId, avId])

    def registerShardDownMessage(self, stateserverid):
        datagram = PyDatagram()
        datagram.addServerHeader(
            stateserverid, self.ourChannel, STATESERVER_SHARD_REST)
        datagram.addChannel(self.ourChannel)
        # schedule for execution on socket close
        self.addPostSocketClose(datagram)
            
    def sendSetZone(self, distobj, zoneId):
        datagram = PyDatagram()
        datagram.addServerHeader(
            distobj.doId, self.ourChannel, STATESERVER_OBJECT_SET_ZONE)        
        # Add the zone parent id
        # HACK:
        parentId = oldParentId = self.districtId
        datagram.addUint32(parentId)
        # Put in the zone id
        datagram.addUint32(zoneId)
        # Send it
        self.send(datagram)
        # The servers don't inform us of this zone change, because we're the
        # one that requested it. Update immediately.
        # TODO: pass in the old parent and old zone
        distobj.setLocation(parentId, zoneId) #, oldParentId, distobj.zoneId)

    def deleteDistrict(self, districtId):
        # Create a message
        datagram = PyDatagram()
        datagram.addServerHeader(
            self.serverId, self.ourChannel, STATESERVER_OBJECT_DELETE_RAM)
        # The Id of the object in question
        datagram.addUint32(districtId)
        # Send the message
        self.send(datagram)
        # Make sure the message gets there.
        self.flush()

    def makeFriends(self, avatarAId, avatarBId, flags, context):
        """
        Requests to make a friendship between avatarA and avatarB with
        the indicated flags (or upgrade an existing friendship with
        the indicated flags).  The context is any arbitrary 32-bit
        integer.  When the friendship is made, or the operation fails,
        the "makeFriendsReply" event is generated, with two
        parameters: an integer result code, and the supplied context.
        """
        datagram = PyDatagram()
        datagram.addServerHeader(
            DBSERVER_ID, self.ourChannel, DBSERVER_MAKE_FRIENDS)        
        
        # Indicate the two avatars who are making friends
        datagram.addUint32(avatarAId)
        datagram.addUint32(avatarBId)
        datagram.addUint8(flags)
        datagram.addUint32(context)
        self.send(datagram)

    def requestSecret(self, requesterId):
        """
        Requests a "secret" from the database server.  This is a
        unique string that will be associated with the indicated
        requesterId, for the purposes of authenticating true-life
        friends.

        When the secret is ready, a "requestSecretReply" message will
        be thrown with three parameters: the result code (0 or 1,
        indicating failure or success), the generated secret, and the
        requesterId again.
        """
        datagram = PyDatagram()
        datagram.addServerHeader(
            DBSERVER_ID,self.ourChannel,DBSERVER_REQUEST_SECRET)        
        
        # Indicate the number we want to associate with the new secret.
        datagram.addUint32(requesterId)
        # Send it off!
        self.send(datagram)

    def submitSecret(self, requesterId, secret):
        """
        Submits a "secret" back to the database server for validation.
        This attempts to match the indicated string, entered by the
        user, to a string returned by a previous call to
        requestSecret().

        When the response comes back from the server, a
        "submitSecretReply" message will be thrown with four
        parameters: the result code (0 or 1, indicating failure or
        success), the secret again, the requesterId again, and the
        number associated with the original secret (that is, the
        original requesterId).
        """
        datagram = PyDatagram()
        datagram.addServerHeader(
            DBSERVER_ID, self.ourChannel, DBSERVER_SUBMIT_SECRET)
        # Pass in our identifying number, and the string.
        datagram.addUint32(requesterId)
        datagram.addString(secret)
        self.send(datagram)

    def replaceMethod(self, oldMethod, newFunction):
        return 0
