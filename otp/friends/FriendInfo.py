from otp.avatar.AvatarHandle import AvatarHandle

class FriendInfo(AvatarHandle):

    def __init__(self, avatarName = '', playerName = '', onlineYesNo = 0, openChatEnabledYesNo = 0, openChatFriendshipYesNo = 0, wlChatEnabledYesNo = 0, location = '', sublocation = '', timestamp = 0, avatarId = 0, friendPrivs = 0, tokenPrivs = 0):
        self.avatarName = avatarName
        self.playerName = playerName
        self.onlineYesNo = onlineYesNo
        self.openChatEnabledYesNo = openChatEnabledYesNo
        self.openChatFriendshipYesNo = openChatFriendshipYesNo
        self.wlChatEnabledYesNo = wlChatEnabledYesNo
        self.location = location
        self.sublocation = sublocation
        self.timestamp = timestamp
        self.avatarId = avatarId
        self.friendPrivs = friendPrivs
        self.tokenPrivs = tokenPrivs
        self.understandableYesNo = self.isUnderstandable()

    def calcUnderstandableYesNo(self):
        self.understandableYesNo = self.isUnderstandable()

    def getName(self):
        if self.avatarName:
            return self.avatarName
        elif self.playerName:
            return self.playerName
        else:
            return ''

    def isUnderstandable(self):
        result = False
        try:
            if self.openChatFriendshipYesNo:
                result = True
            elif self.openChatEnabledYesNo and base.cr.openChatEnabled:
                result = True
            elif self.wlChatEnabledYesNo and base.cr.whiteListChatEnabled:
                result = True
        except:
            pass

        return result

    def isOnline(self):
        return self.onlineYesNo
