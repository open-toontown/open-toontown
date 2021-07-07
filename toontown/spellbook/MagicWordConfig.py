##################################################
# The Toontown Offline Magic Word Manager
##################################################
# Author: Benjamin Frisby
# Copyright: Copyright 2020, Toontown Offline
# Credits: Benjamin Frisby, John Cote, Ruby Lord, Frank, Nick, Little Cat, Ooowoo
# License: MIT
# Version: 1.0.0
# Email: belloqzafarian@gmail.com
##################################################

OUTGOING_CHAT_MESSAGE_NAME = 'magicWord'
CLICKED_NAMETAG_MESSAGE_NAME = 'clickedNametag'
FOCUS_OUT_MESSAGE_NAME = 'focusOut'

PREFIX_DEFAULT = '~'
PREFIX_ALLOWED = ['~', '?', '/', '<', ':', ';']
if config.GetBool('exec-chat', False):
    PREFIX_ALLOWED.append('>')

WIZARD_DEFAULT = 'Spellbook'

MAGIC_WORD_SUCCESS_PHRASES = ['Alakazam!', 'Voila!', 'Ta-da!', 'Presto!', 'Abracadabra!']
MAGIC_WORD_RESPONSES = {
    "SuccessNoResp": 'response will be randomly selected from MAGIC_WORD_SUCCESS_PHRASES',
    "Success": 'response will be provided by magic word',
    "Teleporting": 'Yikes! Don\'t use Magic words while switching zones!',
    "OtherTeleporting": 'Your target is currently switching zones!',
    "BadWord": 'Uh-oh! This Magic Word doesn\'t exist!',
    "CloseWord": 'This Magic Word doesn\'t exist! Did you mean {}?',
    "NoEffect": "This word doesn't affect anybody!",
    "BadTarget": 'Invalid target specified!',
    "NoAccessToTarget": "You don't have a high enough Access Level to target them!",
    "NoAccessSingleTarget": "You don't have a high enough Access Level to target {}! Their Access Level: {}. Your Access Level: {}.",
    "NoTarget": 'Unable to find a target!',
    "NoAccess": 'Your Toon does not have enough power to use this Magic Word!',
    "NotEnoughArgs": 'This command takes at least {}!',
    "TooManyArgs": 'This command takes at most {}!',
    "BadArgs": 'These arguments are of the wrong type!',
    "CannotTarget": 'You cannot target other players with this Magic Word!',
    "Locked": 'You are temporarily locked down and cannot use Magic Words.',
    "RestrictionOther": 'You may only target one other player with this Magic Word!',
    'NonCheaty': 'You cannot use cheaty Magic Words at this time!',
    'Tutorial': 'You cannot use Magic Words in the Toontorial!'
}
MAGIC_WORD_NO_RESPONSE = "...I don't know how to respond!"
HAS_EXTRA_MESSAGE_DATA = ["NotEnoughArgs", "TooManyArgs", "CloseWord"]

MAGIC_WORD_DEFAULT_DESC = 'A simple Magic Word.'
MAGIC_WORD_DEFAULT_ADV_DESC = 'This Magic Word does a lot of things, because reasons.'

AFFECT_TYPES = ['singular', 'zone', 'server', 'rank']
AFFECT_TYPES_NAMES = ['Everyone in this zone', 'The entire server', 'Everyone with an Access Level of']
AFFECT_NONE = -1
AFFECT_SELF = 0
AFFECT_OTHER = 1
AFFECT_BOTH = 2
AFFECT_NORMAL = 0
AFFECT_ZONE = 1
AFFECT_SERVER = 2
AFFECT_RANK = 3
GROUP_AFFECTS = [AFFECT_ZONE, AFFECT_SERVER, AFFECT_RANK]

EXEC_LOC_INVALID = -1
EXEC_LOC_CLIENT = 0
EXEC_LOC_SERVER = 1

ARGUMENT_NAME = 0
ARGUMENT_TYPE = 1
ARGUMENT_REQUIRED = 2
ARGUMENT_DEFAULT = 3

CUSTOM_SPELLBOOK_DEFAULT = '''{
    "words":
    [
        {
            "name": "SetPos",
            "access": "MODERATOR"
        },
        {
            "name": "GetPos",
            "access": "MODERATOR"
        }
    ]
}
'''
