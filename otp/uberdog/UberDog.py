"""
The Uber Distributed Obeject Globals server.
"""

from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.fsm.ClassicFSM import ClassicFSM
from direct.fsm.State import State
from otp.otpbase import OTPGlobals
from otp.distributed import OtpDoGlobals
from otp.distributed.OtpDoGlobals import *
from otp.ai.AIRepository import AIRepository
from otp.ai import TimeManagerAI
from pandac.PandaModules import *
from otp.uberdog.AccountDetailRecord import AccountDetailRecord, SubDetailRecord

from otp.ai.AIMsgTypes import *


class UberDog(AIRepository):
    notify = directNotify.newCategory("UberDog")

    def __init__(
            self, mdip, mdport, esip, esport, dcFileNames,
            serverId, minChannel, maxChannel):
        AIRepository.__init__(
            self, mdip, mdport, esip, esport, dcFileNames,
            serverId, minChannel, maxChannel, dcSuffix = 'UD')

        # We're responsible for keeping track of who's online with which avatar
        self.onlineAccountDetails = {}
        self.onlineAvatars = {}
        self.onlinePlayers = {}

        self.pending={}
        self.doId2doCache={}

        if hasattr(self, 'setVerbose'):
            if self.config.GetBool('verbose-uberrepository'):
                self.setVerbose(1)

        # The AI State machine
        self.fsm = ClassicFSM(
            'UberDog', [
            State('off',
                self.enterOff,
                self.exitOff,
                ['connect']),
            State('connect',
                self.enterConnect,
                self.exitConnect,
                ['noConnection', 'playGame',]),
            State('playGame',
                self.enterPlayGame,
                self.exitPlayGame,
                ['noConnection']),
            State('noConnection',
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

    def _connected(self):
        """
        Callback for when we successfully connect to the otp_server cluster.
        """
        self.setConnectionName("UberDog")
        AIRepository._connected(self)
        # Listen for Account and Avatar online/offline messages
        self.registerForChannel(CHANNEL_PUPPET_ACTION)
        self.fsm.request("playGame")

    def dispatchUpdateToDoId(self, dclassName, fieldName, doId, args, channelId=None):
        # dispatch immediately to local object if it's local, otherwise send
        # it over the wire
        obj = self.doId2do.get(doId)
        if obj is not None:
            assert obj.__class__.__name__ == (dclassName + self.dcSuffix)
            method = getattr(obj, fieldName)
            apply(method, args)
        else:
            self.sendUpdateToDoId(dclassName, fieldName, doId, args, channelId)

    def dispatchUpdateToGlobalDoId(self, dclassName, fieldName, doId, args):
        # dispatch immediately to local object if it's local, otherwise send
        # it over the wire
        obj = self.doId2do.get(doId)
        if obj is not None:
            assert obj.__class__.__name__ == dclassName
            method = getattr(obj, fieldName)
            apply(method, args)
        else:
            self.sendUpdateToGlobalDoId(dclassName, fieldName, doId, args)

    @report(types = ['args'], dConfigParam = 'avatarmgr')
    def handleAccountUsage(self, di):
        priorAccount = di.getUint32() # Historic - used only in __dev__ atm
        newAccount = di.getUint32()

        if priorAccount == 0 and newAccount == 0:
            assert self.notify.debug("priorAccount==0 and newAccount==0, ignoring accountUsage message")
            return

        accountDetailRecord = AccountDetailRecord()
        accountDetailRecord.openChatEnabled = (di.getString() == "YES")
        accountDetailRecord.createFriendsWithChat = (di.getString() == "YES")
        accountDetailRecord.chatCodeCreation = (di.getString() == "YES")
        access = di.getString()
        if access == "VELVET":
            access = OTPGlobals.AccessVelvetRope
        elif access == "FULL":
            access = OTPGlobals.AccessFull
        else:
            access = OTPGlobals.AccessUnknown
        accountDetailRecord.piratesAccess = access
        accountDetailRecord.familyAccountId = di.getInt32()
        accountDetailRecord.playerAccountId = di.getInt32()
        accountDetailRecord.playerName = di.getString()
        accountDetailRecord.playerNameApproved = di.getInt8()
        accountDetailRecord.maxAvatars = di.getInt32()
        accountDetailRecord.numFamilyMembers = di.getInt16()
        accountDetailRecord.familyMembers = []
        for i in range(accountDetailRecord.numFamilyMembers):
            accountDetailRecord.familyMembers.append(di.getInt32())
            
        logoutReason = di.getInt32()

        # Now retrieve the subscription information
        accountDetailRecord.numSubs = di.getUint16()

        for i in range(accountDetailRecord.numSubs):
            subDetailRecord = SubDetailRecord()
            subDetailRecord.subId = di.getUint32()
            subDetailRecord.subOwnerId = di.getUint32()
            subDetailRecord.subName = di.getString()
            subDetailRecord.subActive = di.getString()
            access = di.getString()
            if access == "VELVET":
                access = OTPGlobals.AccessVelvetRope
            elif access == "FULL":
                access = OTPGlobals.AccessFull
            else:
                access = OTPGlobals.AccessUnknown
            subDetailRecord.subAccess = access
            subDetailRecord.subLevel = di.getUint8()
            subDetailRecord.subNumAvatars = di.getUint8()
            subDetailRecord.subNumConcur = di.getUint8()
            subDetailRecord.subFounder = (di.getString() == "YES")
            # Add this subscription to the dict on the account record
            accountDetailRecord.subDetails[subDetailRecord.subId] = subDetailRecord

        # How many avatar slots total do you get in this game?
        accountDetailRecord.maxAvatarSlots = di.getInt8()
            
        assert self.notify.debug("accountDetailRecord: %s" % accountDetailRecord)

        if priorAccount:
            # Send any previous account offline
            self.accountOffline(priorAccount)
            pass
        
        if newAccount:
            # Set up the new guy
            self.accountOnline(newAccount, accountDetailRecord)
            pass
        pass

    @report(types = ['args'], dConfigParam = 'avatarmgr')
    def handleAvatarUsage(self, di):
        priorAvatar = di.getUint32()
        newAvatar = di.getUint32()

        if priorAvatar == 0 and newAvatar == 0:
            assert self.notify.debug("priorAvatar==0 and newAvatar==0, ignoring avatarUsage message")
            return

        newAvatarType = di.getUint16()

        accountId = di.getUint32()

        openChatEnabled = di.getString()
        createFriendsWithChat = di.getString()
        chatCodeCreation = di.getString()
        piratesAccess = di.getString()
        familyAccountId = di.getInt32()
        playerAccountId = di.getInt32()
        playerName = di.getString()
        playerNameApproved = di.getInt8()
        maxAvatars = di.getInt32()
        numFamilyMembers = di.getInt16()
        familyMembers = []
        for i in range(numFamilyMembers):
            familyMembers.append(di.getInt32())

        if openChatEnabled == "YES":
            openChatEnabled = 1
        else:
            openChatEnabled = 0
            
        if priorAvatar:
            # Send any previous avatar offline
            self.avatarOffline(accountId, priorAvatar)
            pass
        
        if newAvatar:
            # Set up the new guy
            self.avatarOnline(newAvatar, newAvatarType,
                              playerAccountId,
                              playerName,
                              playerNameApproved,
                              openChatEnabled,
                              createFriendsWithChat,
                              chatCodeCreation)
            pass
        pass
    
        

    @report(types = ['args'], dConfigParam = 'avatarmgr')
    def accountOnline(self, accountId, accountDetailRecord):
        self.writeServerEvent('accountOnline', accountId, '')
        self.onlineAccountDetails[accountId] = accountDetailRecord
        messenger.send('accountOnline', [accountId])
        pass
    
    @report(types = ['args'], dConfigParam = 'avatarmgr')
    def accountOffline(self, accountId):
        self.writeServerEvent('accountOffline', accountId, '')
        self.onlineAccountDetails.pop(accountId, None)
        self.onlinePlayers.pop(accountId, None)
        messenger.send('accountOffline', [accountId])
        pass

    @report(types = ['args'], dConfigParam = 'avatarmgr')
    def getAccountDetails(self, accountId):
        return self.onlineAccountDetails.get(accountId)

    @report(types = ['args'], dConfigParam = 'avatarmgr')
    def isAccountOnline(self, accountId):
        return accountId in self.onlineAccountDetails

    @report(types = ['args'], dConfigParam = 'avatarmgr')
    def isAvatarOnline(self, avatarId):
        return avatarId in self.onlineAvatars

    @report(types = ['args'], dConfigParam = 'avatarmgr')
    def getAvatarAccountOnline(self, avatarId):
        return self.onlineAvatars.get(avatarId, 0)

    @report(types = ['args'], dConfigParam = 'avatarmgr')
    def getAccountOnlineAvatar(self, accountId):
        return self.onlinePlayers.get(accountId, 0)

    @report(types = ['args'], dConfigParam = 'avatarmgr')
    def checkAccountId(self, accountId):
        if not accountId:
            # SUSPICIOUS
            self.notify.warning("Bogus accountId: %s" % accountId)
            self.writeServerEvent('suspicious', accountId, 'bogus accountId in OtpAvatarManagerUD')
        elif not self.isAccountOnline(accountId):
            # SUSPICIOUS
            self.notify.warning("Got request from account not online: %s" % accountId)
            self.writeServerEvent('suspicious', accountId, 'request from offline account in OtpAvatarManagerUD')
        else:
            # Everything checks out
            return True
        return False

    @report(types = ['args'], dConfigParam = 'avatarmgr')
    def avatarOnline(self, avatarId, avatarType, accountId, playerName, playerNameApproved,
                     openChatEnabled, createFriendsWithChat, chatCodeCreation):
        self.writeServerEvent('avatarOnline', avatarId, '%s|%s|%s|%s|%s|%s' % (
            accountId, playerName, playerNameApproved, openChatEnabled,
            createFriendsWithChat, chatCodeCreation))

        self.onlineAvatars[avatarId] = accountId
        self.onlinePlayers[accountId] = avatarId

        simpleInfo = [avatarId, avatarType]
        fullInfo = [avatarId,
                    accountId,
                    playerName,
                    playerNameApproved,
                    openChatEnabled,
                    createFriendsWithChat,
                    chatCodeCreation]
        
        # necessary for local UD manager objects
        messenger.send("avatarOnline", simpleInfo)
        messenger.send("avatarOnlinePlusAccountInfo", fullInfo)
        pass

    @report(types = ['args'], dConfigParam = 'avatarmgr')
    def avatarOffline(self, accountId, avatarId):
        self.writeServerEvent('avatarOffline', avatarId, '')

        self.onlinePlayers.pop(accountId, None)
        self.onlineAvatars.pop(avatarId, None)

        # necessary for local UD manager objects
        messenger.send("avatarOffline", [avatarId])
        pass
        
    ###################################
    # Assumed Obsolete as of 6/29/09
    #
    # If you're reading this and there
    # haven't been any strange UD crashes
    # here lately, you can probably delete 
    # the next few functions.
    ###################################
    def _addObject(self, context, distributedObject):
        """
        Handle a new distributed object arriving by adding
        it to the cache calling self.handleGotDo().
        """
        assert False, 'JCW: Testing for obsolete functions. If this crashes, let Josh know'
        doId=distributedObject.getDoId()
        assert not self.doId2doCache.has_key(doId)
        if not self.doId2doCache.has_key(doId):
            self.doId2doCache[doId]=distributedObject
            self.handleGotDo(distributedObject)

    def handleGotDo(self, distributedObject):
        """
        This allows derived classes to override the handling
        of new distributed objects arriving in the cache.
        By default, this will loop through the pending calls
        for that object and make the function calls.  It
        will also remove the handled calls from the pending set.
        """
        assert False, 'JCW: Testing for obsolete functions. If this crashes, let Josh know'
        assert self.doId2doCache.has_key(doId)
        pending=self.pending.get(doId)
        if pending is not None:
            del self.pending[doId]
            for i in pending:
                apply(i[0], i[2])

    def deleteObject(self, doId):
        """
        Ask for the object to be removed from the private
        distributed object cache.
        """
        assert False, 'JCW: Testing for obsolete functions. If this crashes, let Josh know'
        if self.doId2doCache.had_key(doId):
            self.unregisterForChannel(doId)
            #self.deleteObject(doId)
            del self.doId2doCache[doId]
        #HACK:
        self.unregisterForChannel(doId)
        AIRepository.deleteObject(self.doId)
        
    def uniqueName(self, desc):
        return desc

    if __dev__:
        """
        Early warning system for unsupported use of the Uberdog Repository
        """
        def deleteObjects(self):
            assert 0
    
        def createDistrict(self, districtId, districtName):
            assert 0
    
        def deleteDistrict(self, districtId):
            assert 0
    
        def enterDistrictReset(self):
            assert 0
    
        def exitDistrictReset(self):
            assert 0
    
