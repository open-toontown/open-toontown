from toontown.toonbase.ToontownGlobals import *
from otp.otpbase import OTPGlobals

# these are array indexs
# since there are no structs
GROUPMEMBER = 0
GROUPINVITE = 1

class ToontownGroupManager:
    
    def __init__(self):
        self.groupLists = []
        self.avIdDict = {}
        #group is [[members],[invitees]]
        
    def cleanup(self):
        self.groupLists = []
        self.avIdDict = {}
        
    def inviteToGroup(self, memberId, joinerId):
        #print("Group Manager Invite to group")
        group = self.getGroup(memberId)
        joinerGroup = self.getGroup(joinerId)
        if group and ((joinerId in group[GROUPMEMBER]) or (joinerId in group[GROUPINVITE])):
            #joiner is already in the group
            #print ("joiner in same group")
            return None
        elif joinerGroup and len(joinerGroup) > 1:
            #joiner is in another group
            #print ("joiner in another group")
            return None
        if group:
            # lookup the member's group and add the joiner
            group[GROUPINVITE].append(joinerId)
            #self.avIdDict[joiner] = group
            #print ("added joiner to group")
        else:
            # there is no group so add a new one
            newGroupList = [[memberId],[joinerId]]
            self.avIdDict[memberId] = newGroupList
            self.groupLists.append(newGroupList)
            group = newGroupList
            #print ("creating new group")
        #tell each group member that the joiner has been invited
        for avId in group[GROUPMEMBER]:
            if avId != joinerId:
                avatar = simbase.air.doId2do.get(avId)
                if avatar:
                    avatar.sendUpdate("receiveInvitePosted", [joinerId])
        
        #send the invite message to joinerId
        avatar = simbase.air.doId2do.get(joinerId)
        if avatar:
            avatar.sendUpdate("receiveGroupInvite", [group[GROUPMEMBER]])
        return group
        
    def useInviteToJoin(self, memberIdList, joinerId):
        memberId = memberIdList[0]
        joinerGroup = self.getGroup(joinerId)
        if joinerGroup:
            if len(joinerGroup) > 1:
                return
            else:
                # if the joiner is in a group by themselves, remove that group
                self.removeFromGroup(joinerId)
            
        group = self.getGroup(memberId)
        if group and (joinerId in group[GROUPINVITE]):
            group[GROUPINVITE].remove(joinerId)
            group[GROUPMEMBER].append(joinerId)
            self.avIdDict[joinerId] = group
            
            for avId in group[GROUPMEMBER]:
                avatar = simbase.air.doId2do.get(avId)
                if avatar:
                    if avId != joinerId:
                        avatar.sendUpdate("receiveJoinGroup", [[joinerId]])
                    else:
                        avatar.sendUpdate("receiveJoinGroup", [group[GROUPMEMBER]])
        else:
            #TODO tell the joiner that the group invitee was invalid
            return
            
    def removeInvitation(self, memberId, joinerId):
        group = self.getGroup(memberId) 
        if group: 
            #tell each group member that the invitation has been retracted
            for avId in group[GROUPMEMBER]:
                if avId != joinerId:
                    avatar = simbase.air.doId2do.get(avId)
                    if avatar:
                        avatar.sendUpdate("receiveInviteRemoved", [joinerId])
            
            #tell the joiner that the invitation has been retracted
            avatar = simbase.air.doId2do.get(joinerId)
            if avatar:
                avatar.sendUpdate("receiveGroupInviteRetract", [memberId])
                
                
            if (joinerId in group[GROUPMEMBER]):
                #joiner is already in the group do nothing
                pass
            elif (joinerId in group[GROUPINVITE]):
                group[GROUPINVITE].remove(joinerId)
        else:
            #there was no invitation
            pass
        
            
    def removeFromGroup(self, leaverId):
        print("removeFromGroup")
        group = self.getGroup(leaverId)
        if group and (leaverId in group[GROUPMEMBER]):
            print("Group found for %s" % (leaverId))
            #send everyone in the group a message memberId has left
            for avId in group[GROUPMEMBER]:
                if avId != leaverId:
                    avatar = simbase.air.doId2do.get(avId)
                    if avatar:
                        avatar.sendUpdate("receiveLeaveGroup", [[leaverId]])
                else:
                    avatar = simbase.air.doId2do.get(avId)
                    if avatar:
                        avatar.sendUpdate("receiveLeaveGroup", [group[GROUPMEMBER]])
            #remove the memberId from the groupList
            group[GROUPMEMBER].remove(leaverId)
        else:
            #print("No group found for %s" % (leaverId))
            pass
                
            
        # if the group is empty remove it
        if group and len(group[GROUPMEMBER]) <= 1:
            self.groupLists.remove(group)
            for member in group[GROUPMEMBER]:
                if self.avIdDict.has_key(member):
                    self.avIdDict.pop(member)
        # clear the member's group affiliation
        if self.avIdDict.has_key(leaverId):
            self.avIdDict.pop(leaverId)
        
    def getGroup(self, memberId):
        if self.avIdDict.has_key(memberId):
            return self.avIdDict[memberId]
        else:
            return None
            

            
            
                
            
        
        