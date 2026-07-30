import string
NORMAL_CHAT = 1
WHISPER_CHAT = 2
GUILD_CHAT = 3
CREW_CHAT = 4
SHIPPVP_CHAT = 5
ERROR_NONE = None
ERROR_NO_OPEN_CHAT = 1
ERROR_NOT_FRIENDS = 2
ERROR_NO_RECEIVER = 3
ERROR_NO_GUILD_CHAT = 4
ERROR_NO_CREW_CHAT = 5
ERROR_NO_SHIPPVP_CHAT = 6
TYPEDCHAT = 0
SPEEDCHAT_NORMAL = 1
SPEEDCHAT_EMOTE = 2
SPEEDCHAT_CUSTOM = 3
SYSTEMCHAT = 4
GAMECHAT = 5
GUILDCHAT = 6
PARTYCHAT = 7
SPEEDCHAT_QUEST = 8
FRIEND_UPDATE = 9
CREW_UPDATE = 10
GUILD_UPDATE = 11
AVATAR_UNAVAILABLE = 12
SHIPPVPCHAT = 13
GMCHAT = 14
ChatEvent = 'ChatEvent'
NormalChatEvent = 'NormalChatEvent'
SCChatEvent = 'SCChatEvent'
SCCustomChatEvent = 'SCCustomChatEvent'
SCEmoteChatEvent = 'SCEmoteChatEvent'
SCQuestEvent = 'SCQuestEvent'
OnScreen = 0
OffScreen = 1
Thought = 2
ThoughtPrefix = '.'

def isThought(message):
    if len(message) == 0:
        return 0
    elif string.find(message, ThoughtPrefix, 0, len(ThoughtPrefix)) >= 0:
        return 1
    else:
        return 0


def removeThoughtPrefix(message):
    if isThought(message):
        return message[len(ThoughtPrefix):]
    else:
        return message
