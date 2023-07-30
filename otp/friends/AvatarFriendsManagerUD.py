from direct.distributed.DistributedObjectGlobalUD import DistributedObjectGlobalUD
from otp.otpbase import OTPGlobals
from otp.ai import AIMsgTypes
from otp.uberdog.UberDogUtil import ManagedAsyncRequest
from otp.uberdog.RejectCode import RejectCode

from direct.directnotify.DirectNotifyGlobal import directNotify

from otp.friends.AvatarFriendInfo import AvatarFriendInfo

       
class AvatarFriendsManagerUD(DistributedObjectGlobalUD):
    """
    The Avatar Friends Manager is a global object.
    This object handles client requests on avatar-level (as opposed to player-level) friends.

    See Also:
        "otp/src/friends/AvatarFriendsManager.py"
        "otp/src/friends/PlayerFriendsManager.py"
        "pirates/src/friends/PiratesFriendsList.py"
        "otp/src/configfiles/otp.dc"
        "pirates/src/configfiles/pirates.dc"
    """
    notify = directNotify.newCategory('AvatarFriendsManagerUD')

    def __init__(self, air):
        assert self.notify.debugCall()
        DistributedObjectGlobalUD.__init__(self, air)
        self.DBuser = config.GetString("mysql-user", "ud_rw")
        self.DBpassword = config.GetString("mysql-password", "r3adwr1te")

        self.DBhost = config.GetString("avatarfriends-db-host","localhost")
        self.DBport = config.GetInt("avatarfriends-db-port",3306)
        self.DBname = config.GetString("avatarfriends-db-name","avatar_friends")
        self.friends = None
        self.friendsList = None
        self.wantMysql = config.GetBool('want-mysql-db', 0)
        if self.wantMysql:
            from otp.friends.AvatarFriendsDB import AvatarFriendsDB

            self.db = AvatarFriendsDB(host=self.DBhost,
                                  port=self.DBport,
                                  user=self.DBuser,
                                  password=self.DBpassword,
                                  dbname=self.DBname)
        else:
            # lets use the astron db or openotp db
            if __astron__:
                self.db = self.air.dbInterface
            else:
                # TODO
                self.db = None 
              
            

        self.avatarId2FriendsList = {}
        self.avatarId2Invitations = {}
        self.avatarId2Unvitations = {} #an unvitation is a rejected (but not retracted) invitation
        #self.avatarId2Name = {}
        self.avatarId2Info = {}

        self.asyncRequests = {}
        self.isAvatarOnline = {}

    
    def announceGenerate(self):
        assert self.notify.debugCall()
        #self.accept("avatarOnline", self.avatarOnline, [])
        self.accept("avatarOnlinePlusAccountInfo", self.avatarOnlinePlusAccountInfo, [])
        self.accept("avatarOffline", self.avatarOffline, [])
        DistributedObjectGlobalUD.announceGenerate(self)
        self.sendUpdateToChannel(
            AIMsgTypes.CHANNEL_CLIENT_BROADCAST, "online", [])
        self.sendUpdateToChannel(
            AIMsgTypes.OTP_CHANNEL_AI_AND_UD_BROADCAST, "online", [])


    def delete(self):
        assert self.notify.debugCall()
        self.ignoreAll()
        for i in list(self.asyncRequests.values()):
            i.delete()
        DistributedObjectGlobalUD.delete(self)

    #----------------------------------

    def avatarOnlinePlusAccountInfo(self,avatarId,accountId,playerName,
                                    playerNameApproved,openChatEnabled,
                                    createFriendsWithChat,chatCodeCreation):    
        assert self.notify.debugCall()
        assert avatarId

        self.notify.debug("avatarOnlinePlusAccountInfo")
        if avatarId in self.isAvatarOnline:
            assert self.notify.debug(
                "\n\nWe got a duplicate avatar online notice %s"%(avatarId,))
        if avatarId and avatarId not in self.isAvatarOnline:
            self.isAvatarOnline[avatarId]=True
            self.avatarId2Info[avatarId] = AvatarFriendInfo(avatarName=str(avatarId),
                                                            playerName = playerName,
                                                            playerId = accountId,
                                                            onlineYesNo=1,
                                                            openChatEnabledYesNo=openChatEnabled,)

            # Get my friends list from the SQL DB
            if self.wantMysql:
                self.friends = self.db.getFriends(avatarId)
            else:
                self.db.queryObject(self.air.dbId, avatarId, self.__gotFriendsList)

            self.avatarId2FriendsList[avatarId]=self.friends
            
            if not hasattr(self.friends, "keys"): #check for error
                self.notify.warning("self.db.getFriends(avatarId) has no keys %s" % (self.friends))
                return

            # Callback function for asynchronous avatar name fetch
            def setName(avatarId, avatarId2info, friends, context, name):
                if avatarId in avatarId2info:
                    avatarId2info[avatarId].avatarName = name[0]
                    for friendId in friends:
                        if friendId in self.isAvatarOnline:
                            if (friendId in self.avatarId2FriendsList) and (avatarId in self.avatarId2FriendsList[friendId]):
                                self.sendUpdateToAvatarId(friendId,"updateAvatarFriend",
                                                          [avatarId,self.getFriendView(friendId,avatarId)])
                            self.sendExtraUpdates(friendId,avatarId)

            # Get my friends' info to me
            for friend in list(self.friends.keys()):
                friendId = friend
                if friendId not in self.isAvatarOnline:
                    if friendId not in self.avatarId2Info:
                        self.avatarId2Info[friendId] = AvatarFriendInfo()
                        #fetch this friend's name from the gameDB since we don't have it yet
                        context=self.air.allocateContext()
                        dclassName="DistributedAvatarUD"
                        self.air.contextToClassName[context]=dclassName
                        self.acceptOnce(
                            "doFieldResponse-%s"%context,setName,[friendId,self.avatarId2Info,[avatarId,]])
                        self.air.queryObjectField(dclassName,"setName",friendId,context)
                    else:
                        #print "AFMUD warning: info entry found for offline friend"
                        self.sendUpdateToAvatarId(avatarId,"updateAvatarFriend",[friendId,self.getFriendView(avatarId,friendId)])
                        self.sendExtraUpdates(avatarId,friendId)
                else:
                    assert friendId in self.avatarId2Info
                    self.sendUpdateToAvatarId(avatarId,"updateAvatarFriend",[friendId,self.getFriendView(avatarId,friendId)])
                    self.sendExtraUpdates(avatarId,friendId)


            # Get my info to my friends
            context=self.air.allocateContext()
            dclassName="DistributedAvatarUD"
            self.air.contextToClassName[context]=dclassName
            self.acceptOnce(
                "doFieldResponse-%s"%(context,), 
                setName, [avatarId, self.avatarId2Info, list(self.friends.keys())])
            self.air.queryObjectField(
                dclassName, "setName", avatarId, context)
    
    def __gotFriendsList(self, dclass, fields):
        self.friends = fields.get('setFriendsList', [])
        self.friendsList = self.friends
        


    def getFriendView(self, viewerId, friendId):
        info = self.avatarId2Info[friendId]
        assert viewerId in self.avatarId2FriendsList, "avatarId2FriendsList has no key %d" % viewerId
        assert friendId in self.avatarId2FriendsList[viewerId], "avatarId2FriendsList[%d] has no key %d" % (viewerId, friendId)
        info.openChatFriendshipYesNo = self.avatarId2FriendsList[viewerId][friendId]
        if info.openChatFriendshipYesNo or \
           (info.openChatEnabledYesNo and \
            self.avatarId2Info[viewerId].openChatEnabledYesNo):
            info.understandableYesNo = 1
        else:
            info.understandableYesNo = 0
        return info

    def sendExtraUpdates(self,destId,aboutId):
        pass

    @report(types = ['args'], dConfigParam = 'orphanedavatar')
    def avatarOffline(self, avatarId):
        """
        Is called from handleAvatarUsage when the avatar leaves the game.

        Also is called from DistributedAvatarManagerUD when it detects
        an orphaned avatar in the world.
        """
        assert self.notify.debugCall()
        self.isAvatarOnline.pop(avatarId,None)

        if avatarId in self.avatarId2Info:
            self.avatarId2Info[avatarId].onlineYesNo = 0
        
        if avatarId:
            friendsList = self.avatarId2FriendsList.get(avatarId, None)
            if friendsList is not None and avatarId in self.avatarId2Info:
                for friend in friendsList:
                    self.sendUpdateToAvatarId(
                        friend, "updateAvatarFriend", [avatarId,self.avatarId2Info[avatarId]])
            invitations = self.avatarId2Invitations.pop(avatarId, [])
            for invitee in invitations:
                self.sendUpdateToAvatarId(
                    invitee, "retractInvite", [avatarId])

        self.avatarId2FriendsList.pop(avatarId,None)
        self.avatarId2Info.pop(avatarId,None)


#----------------------------------------------------------------------


    # Functions called by the client

    def requestInvite(self, otherAvatarId):
        avatarId = self.air.getAvatarIdFromSender()
        assert self.notify.debugCall("avatarId:%s"%(avatarId,))
        invitations = self.avatarId2Invitations.setdefault(avatarId, [])
        othersInvitations = self.avatarId2Invitations.setdefault(
            otherAvatarId, [])
        friendsList = self.avatarId2FriendsList.get(avatarId)
        otherFriendsList = self.avatarId2FriendsList.get(otherAvatarId)
        
        def reject(reason):
            self.sendUpdateToAvatarId(
                avatarId, "rejectInvite", [otherAvatarId, reason])
                
        
        #clear unvitations
        unvitations = self.avatarId2Unvitations.setdefault(avatarId, [])
        if otherAvatarId in unvitations:
            unvitations.remove(otherAvatarId)
            
        if friendsList is None:
            reject(RejectCode.FRIENDS_LIST_NOT_HANDY)
        elif otherFriendsList is None:
            reject(RejectCode.INVITEE_NOT_ONLINE)
        elif avatarId in self.avatarId2Unvitations.setdefault(otherAvatarId, []): #check for unvitation
            reject(RejectCode.INVITATION_DECLINED)
        elif otherAvatarId in invitations:
            reject(RejectCode.ALREADY_INVITED)
        elif avatarId == otherAvatarId:
            reject(RejectCode.ALREADY_FRIENDS_WITH_SELF)
        elif otherAvatarId in friendsList:
            reject(RejectCode.ALREADY_YOUR_FRIEND)
        elif avatarId in otherFriendsList:
            reject(RejectCode.ALREADY_YOUR_FRIEND)
            self.notify.error(
                "Friends lists out of sync %s %s"%(avatarId, otherAvatarId))
        #should be adding player friends list?

        elif (len(friendsList)
                + 0
                > OTPGlobals.MaxFriends):
            reject(RejectCode.FRIENDS_LIST_FULL)
        #should be adding player friends list?
        elif (len(otherFriendsList)
                + 0
                > OTPGlobals.MaxFriends):
            reject(RejectCode.OTHER_FRIENDS_LIST_FULL)
        elif avatarId in othersInvitations:
            othersInvitations.remove(avatarId)
            assert otherAvatarId not in invitations

            self.avatarId2FriendsList[avatarId][otherAvatarId] = 0
            if otherAvatarId in self.avatarId2FriendsList:
                self.avatarId2FriendsList[otherAvatarId][avatarId] = 0

            #update the friends database
            try:
                if self.wantMysql:
                    self.db.addFriendship(avatarId,otherAvatarId)
                else:
                    if __astron__:
                        # update setFriendsList field in the distributedtoon dclass to include the new friend
                        friendsList = self.avatarId2FriendsList[avatarId]
                        friendsList.append(otherAvatarId)
                        self.db.updateObject(self.air.dbId, avatarId,  self.air.dclassesByName['DistributedToonUD'], {'setFriendsList': [friendsList]} )
                    else:
                        # TODO openotp: update setFriendsList field in the distributedtoon dclass to include the new friend
                        pass 
            except:
                pass #HACK for testing

            self.air.writeServerEvent('friendAccept', avatarId, '%s' % otherAvatarId)

            #tell them they're friends and give presence info, includes online status
            self.sendUpdateToAvatarId(otherAvatarId,"updateAvatarFriend",[avatarId,self.getFriendView(otherAvatarId,avatarId)])
            self.sendUpdateToAvatarId(avatarId,"updateAvatarFriend",[otherAvatarId,self.getFriendView(avatarId,otherAvatarId)])
            self.sendExtraUpdates(avatarId,otherAvatarId)
            self.sendExtraUpdates(otherAvatarId,avatarId)

        else:
            invitations.append(otherAvatarId)
            # Tell the other guy we're inviting him!
            self.air.writeServerEvent('friendInvite', avatarId, '%s' % otherAvatarId)
            self.sendUpdateToAvatarId(avatarId, "friendConsidering", [otherAvatarId])
            self.sendUpdateToAvatarId(otherAvatarId, "invitationFrom", [avatarId,self.avatarId2Info[avatarId].avatarName])


    def requestRemove(self, otherAvatarId):
        """
        Call this function if you want to retract an invitation you've
        made, or to decline an invitation from otherAvatarId, or to
        remove an existing friend from your friends list.
        
        otherAvatarId may be online or offline.
        """
        avatarId = self.air.getAvatarIdFromSender()
        self.air.writeServerEvent('friendRemove', avatarId, '%s' % otherAvatarId)
        self.friendsList = self.avatarId2FriendsList.get(avatarId,None)

        if self.friendsList is None:
            if self.wantMysql:
                self.friendsList = self.db.getFriends(avatarId)
                self.avatarId2FriendsList[avatarId] = self.friendsList
            else:
                if __astron__:
                    self.db.queryObject(self.air.dbId, avatarId, self.__gotFriendsList)
                    self.avatarId2FriendsList[avatarId] = self.friendsList
                else:
                    # TODO openotp: queryObject
                    pass
        assert self.notify.debugCall("avatarId:%s"%(avatarId,))
        
        def reject(reason):
            self.sendUpdateToAvatarId(
                avatarId, "rejectRemove", [otherAvatarId, reason])
        
        invitations = self.avatarId2Invitations.setdefault(avatarId, [])
        if otherAvatarId in invitations:
            # The other avatar was only invited and had not yet accepted
            self.sendUpdateToAvatarId(otherAvatarId, "retractInvite", [avatarId])
            invitations.remove(otherAvatarId)
            assert otherAvatarId not in invitations
            assert otherAvatarId not in friendsList
            return
        else: # create an unvitation
            unvitations = self.avatarId2Unvitations.setdefault(avatarId, [])
            if otherAvatarId in unvitations:
                pass
            else:
                unvitations.append(otherAvatarId)

        othersInvitations = self.avatarId2Invitations.setdefault(otherAvatarId, [])
        if avatarId in othersInvitations:
            # I was only invited and had not yet accepted
            self.sendUpdateToAvatarId(
                otherAvatarId, "rejectInvite",
                [avatarId, RejectCode.INVITATION_DECLINED])
            othersInvitations.remove(avatarId)
            assert avatarId not in othersInvitations
            assert otherAvatarId not in friendsList
            return

        if otherAvatarId not in friendsList:
            reject(RejectCode.ALREADY_NOT_YOUR_FRIEND)
        else:
            if avatarId in self.avatarId2FriendsList:
                self.avatarId2FriendsList[avatarId].pop(otherAvatarId,None)
            if otherAvatarId in self.avatarId2FriendsList:
                self.avatarId2FriendsList[otherAvatarId].pop(avatarId,None)
            if self.wantMysql:
                self.db.removeFriendship(avatarId,otherAvatarId)
            else:
                if __astron__:
                    # update setFriendsList field in the distributedtoon dclass to remove the friend
                    friendsList = self.avatarId2FriendsList[avatarId]
                    friendsList.remove(otherAvatarId)
                    self.db.updateObject(self.air.dbId, avatarId,  self.air.dclassesByName['DistributedToonUD'], {'setFriendsList': [friendsList]} )
                else:
                    # TODO openotp: update setFriendsList field in the distributedtoon dclass to remove the friend
                    pass
            self.sendUpdateToAvatarId(avatarId,"removeAvatarFriend",[otherAvatarId])
            self.sendUpdateToAvatarId(otherAvatarId,"removeAvatarFriend",[avatarId])
    

    def updateAvatarName(self, avatarId, avatarName):
        if avatarId in self.avatarId2Info:
            self.avatarId2Info[avatarId].avatarName = avatarName
            friends = self.avatarId2FriendsList.get(avatarId,[])
            for friendId in friends:
                if friendId in self.isAvatarOnline:
                    self.sendUpdateToAvatarId(friendId,"updateAvatarFriend",
                                              [avatarId,self.getFriendView(friendId,avatarId)])
                    self.sendExtraUpdates(friendId,avatarId)
