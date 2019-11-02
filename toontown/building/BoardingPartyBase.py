from otp.otpbase import OTPGlobals
from toontown.toonbase import ToontownGlobals
import copy
BOARDCODE_OKAY = 1
BOARDCODE_MISSING = 0
BOARDCODE_MINLAFF = -1
BOARDCODE_PROMOTION = -2
BOARDCODE_BATTLE = -3
BOARDCODE_SPACE = -4
BOARDCODE_NOT_PAID = -5
BOARDCODE_DIFF_GROUP = -6
BOARDCODE_PENDING_INVITE = -7
BOARDCODE_IN_ELEVATOR = -8
INVITE_ACCEPT_FAIL_GROUP_FULL = -1

class BoardingPartyBase:

    def __init__(self):
        self.groupListDict = {}
        self.avIdDict = {}

    def cleanup(self):
        del self.groupListDict
        del self.avIdDict

    def getGroupSize(self):
        return self.maxSize

    def setGroupSize(self, groupSize):
        self.maxSize = groupSize

    def getGroupLeader(self, avatarId):
        if self.avIdDict.has_key(avatarId):
            leaderId = self.avIdDict[avatarId]
            return leaderId
        else:
            return None
        return None

    def isGroupLeader(self, avatarId):
        leaderId = self.getGroupLeader(avatarId)
        if avatarId == leaderId:
            return True
        else:
            return False

    def getGroupMemberList(self, avatarId):
        if self.avIdDict.has_key(avatarId):
            leaderId = self.avIdDict[avatarId]
            group = self.groupListDict.get(leaderId)
            if group:
                returnList = copy.copy(group[0])
                if 0 in returnList:
                    returnList.remove(0)
                return returnList
        return []

    def getGroupInviteList(self, avatarId):
        if self.avIdDict.has_key(avatarId):
            leaderId = self.avIdDict[avatarId]
            group = self.groupListDict.get(leaderId)
            if group:
                returnList = copy.copy(group[1])
                if 0 in returnList:
                    returnList.remove(0)
                return returnList
        return []

    def getGroupKickList(self, avatarId):
        if self.avIdDict.has_key(avatarId):
            leaderId = self.avIdDict[avatarId]
            group = self.groupListDict.get(leaderId)
            if group:
                returnList = copy.copy(group[2])
                if 0 in returnList:
                    returnList.remove(0)
                return returnList
        return []

    def hasActiveGroup(self, avatarId):
        memberList = self.getGroupMemberList(avatarId)
        if avatarId in memberList:
            if len(memberList) > 1:
                return True
        return False

    def hasPendingInvite(self, avatarId):
        pendingInvite = False
        if self.avIdDict.has_key(avatarId):
            leaderId = self.avIdDict[avatarId]
            leaderInviteList = self.getGroupInviteList(leaderId)
            if leaderId == avatarId:
                if len(leaderInviteList):
                    pendingInvite = True
                else:
                    pendingInvite = False
            elif avatarId in leaderInviteList:
                pendingInvite = True
            else:
                pendingInvite = False
        if pendingInvite:
            return True
        else:
            return False

    def isInGroup(self, memberId, leaderId):
        if memberId in self.getGroupMemberList(leaderId) or memberId in self.getGroupInviteList(leaderId):
            return True
        else:
            return False
