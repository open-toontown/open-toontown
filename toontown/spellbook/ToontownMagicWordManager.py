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

from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObject

from panda3d.otp import WhisperPopup
from otp.otpbase.OTPGlobals import *

from toontown.friends import FriendHandle
from toontown.spellbook.MagicWordConfig import *
from toontown.spellbook.MagicWordIndex import *
from toontown.toon import Toon

import json
import random
import string


MagicWordIndex = magicWordIndex.copy()


class ToontownMagicWordManager(DistributedObject.DistributedObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToontownMagicWordManager')
    neverDisable = 1

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        base.cr.magicWordManager = self

        # The default chat prefix we use to determine if said phrase is a Magic Word
        self.chatPrefix = PREFIX_DEFAULT

        # The default name of the "wizard" that returns responses when executing Magic Words
        self.wizardName = WIZARD_DEFAULT

        # Keep track of the last clicked avatar for targeting purposes
        self.lastClickedAvId = 0

    def announceGenerate(self):
        DistributedObject.DistributedObject.announceGenerate(self)

        # Only use a custom Magic Word activator if the index is allowed
        activatorIndex = base.settings.getSetting('magic-word-activator', 0)
        if 0 <= activatorIndex <= (len(PREFIX_ALLOWED) - 1):
            self.chatPrefix = PREFIX_ALLOWED[activatorIndex]

        # Accept events such as outgoing chat messages and clicking on nametags
        self.accept(OUTGOING_CHAT_MESSAGE_NAME, self.checkMagicWord)
        self.accept(CLICKED_NAMETAG_MESSAGE_NAME, self.__handleClickedNametag)
        self.accept(FOCUS_OUT_MESSAGE_NAME, self.__handleFocusOutNametag)

    def disable(self):
        DistributedObject.DistributedObject.disable(self)

        # Ignore the events we were accepting earlier
        self.ignore(OUTGOING_CHAT_MESSAGE_NAME)
        self.ignore(CLICKED_NAMETAG_MESSAGE_NAME)
        self.ignore(FOCUS_OUT_MESSAGE_NAME)

    def setChatPrefix(self, chatPrefix):
        self.chatPrefix = chatPrefix

    def __handleClickedNametag(self, avatar):
        if avatar:
            # Make sure the nametag we clicked on is a Toon
            if isinstance(avatar, Toon.Toon) or isinstance(avatar, FriendHandle.FriendHandle):
                # Store the avId of our target
                self.lastClickedAvId = avatar.getDoId()
                return
        # Clear our target avId
        self.lastClickedAvId = 0

    def __handleFocusOutNametag(self):
        # We've clicked off of a nametag, so reset the target avId
        self.lastClickedAvId = 0

    def checkMagicWord(self, magicWord):
        # Well, this obviously isn't a Magic Word if it doesn't begin with our prefix
        if not magicWord.startswith(self.chatPrefix):
            return

        # We don't even have access to be using Magic Words in the first place
        if base.localAvatar.getAccessLevel() < OTPGlobals.AccessLevelName2Int.get('MODERATOR'):
            self.generateResponse(responseType="NoAccess")
            return

        # Using Magic Words while teleporting or going through tunnels is scary
        if base.localAvatar.getTransitioning():
            self.generateResponse(responseType="Teleporting")
            return

        # We're allowed to use the Magic Word then, so let's proceed
        self.handleMagicWord(magicWord)

    def generateResponse(self, responseType, magicWord='', args=None, returnValue=None, affectRange=None,
                         affectType=None, affectExtra=None, lastClickedAvId=None, extraMessageData = None):
        # Generate and send the response to the use of our Magic Word
        response = self.generateMagicWordResponse(responseType, magicWord, args, returnValue, affectRange, affectType,
                                                  affectExtra, lastClickedAvId, extraMessageData)
        base.localAvatar.setSystemMessage(0, self.wizardName + ': ' + response, WhisperPopup.WTSystem)
        self.notify.info(response)

    def generateMagicWordResponse(self, responseType, magicWord, args, returnValue, affectRange, affectType,
                                  affectExtra, lastClickedAvId, extraMessageData):
        # Start out with a blank response
        response = ''

        # If our Magic Word was a success but has no return value, just send a randomized success phrase
        if responseType == "SuccessNoResp" and magicWord:
            successExclaim = random.choice(MAGIC_WORD_SUCCESS_PHRASES)
            response += successExclaim
            return response
        # We had a successful Magic Word and also got a return value, so let's just use that
        elif responseType == "Success":
            response += returnValue
            return response

        # Guess it wasn't a success, so let's grab our response via the given code
        response += MAGIC_WORD_RESPONSES.get(responseType, MAGIC_WORD_NO_RESPONSE)

        # If we want to provide extra info, format the response
        if responseType in MagicWordConfig.HAS_EXTRA_MESSAGE_DATA:
            response = response.format(extraMessageData)

        return response

    def handleMagicWord(self, magicWord):
        # By default, our Magic Word affects nobody- not even ourself!
        affectRange = AFFECT_NONE

        # A normal affect type-  we aren't trying to target all Toons in the zone, server, or a specific Access Level
        affectType = AFFECT_NORMAL

        # Only used for determining what Access Level will be targeted, if we decide to target a specific one
        affectExtra = -1

        # Used for determining what the affectRange is- it counts the amount of activators uses (ranges 1-3)
        for x in range(3):
            if magicWord.startswith(self.chatPrefix * (3 - x)):
                affectRange = 2 - x
                break

        # If so some reason our affectRange is still none, we can't go any further
        if affectRange == AFFECT_NONE:
            self.generateResponse(responseType="NoEffect")
            return
        # Our affectRange is other, meaning we want to target someone- let's make sure we're allowed to
        elif affectRange == AFFECT_OTHER:
            # If they don't exist, why would we want to continue?
            toon = base.cr.doId2do.get(self.lastClickedAvId)
            if not toon:
                return

            # Like earlier, Magic Words are no good if used while moving between zones
            if toon.getTransitioning():
                self.generateResponse(responseType="OtherTeleporting")
                return

        # Get how many activators were used in this Magic Word execution
        activatorLength = affectRange + 1

        # The Magic word without the activators
        magicWordNoPrefix = magicWord[activatorLength:]

        # Iterate through the affectType strings and see if any of them were used (e.g. zone, server, or rank)
        for type in AFFECT_TYPES:
            if magicWordNoPrefix.startswith(type):
                magicWordNoPrefix = magicWordNoPrefix[len(type):]
                affectType = AFFECT_TYPES.index(type)
                break

        # Calculate the Access Level to affect if affectType is RANK
        if affectType == AFFECT_RANK:
            # Iterate over all the possible Access Level integers and see if any match with the one provided
            for level in list(OTPGlobals.AccessLevelName2Int.values()):
                # It matches, woohoo!
                if magicWordNoPrefix.startswith(str(level)):
                    # Sorry, I'm commenting this way after the fact, so not even I know why there is a try/except here
                    # My guess is that sometimes this doesn't work for whatever reason, but I'm not too sure
                    # It typically works fine for me but I will keep it here just in-case
                    try:
                        int(magicWordNoPrefix[len(str(level)):][:1])
                        self.generateResponse(responseType="BadTarget")
                        return
                    except:
                        pass

                    # Strip the Access Level integer from the Magic Word string
                    magicWordNoPrefix = magicWordNoPrefix[len(str(level)):]

                    # Store the Access Level integer here instead
                    affectExtra = level
                    break

            # The invoker wanted to target an Access Level but provided an invalid integer, so let them know
            if affectExtra == -1:
                self.generateResponse(responseType="BadTarget")
                return

        # Finally, we can get the name of the Magic Word used
        word = magicWordNoPrefix.split(' ', 1)[0].lower()

        # The Magic Word the invoker used doesn't exist
        if word not in MagicWordIndex:
            # Iterate over all Magic Word names and see if the one provided is close to any of them
            for magicWord in list(MagicWordIndex.keys()):
                # If it is close, suggest to the invoker that they made a typo
                if word in magicWord:
                    self.generateResponse(responseType="CloseWord", extraMessageData=magicWord)
                    return
            # Couldn't find any Magic Word close to what was provided, so let them know the word doesn't exist
            self.generateResponse(responseType="BadWord")
            return

        # Grab the Magic Word info based off of it's name
        magicWordInfo = MagicWordIndex[word]

        # The location of the Magic Word's execution was not specified, so raise an error
        if magicWordInfo['execLocation'] == EXEC_LOC_INVALID:
            raise ValueError("execLocation not set for magic word {}!".format(magicWordInfo['classname']))
        # The execLocation is valid, so let's finally send data over to the server to execute our Magic Word
        elif magicWordInfo['execLocation'] in (EXEC_LOC_SERVER, EXEC_LOC_CLIENT):
            self.sendUpdate('requestExecuteMagicWord', [affectRange, affectType, affectExtra, self.lastClickedAvId,
                                                        magicWordNoPrefix])

    def executeMagicWord(self, word, commandName, targetIds, args, affectRange, affectType, affectExtra, lastClickedAvId):
        # We have have a target avId and the affectRange isn't ourself, we want to execute this Magic Word on the target
        # This is alright, but we should only execute it on the target if they are visible on our client
        if self.lastClickedAvId and affectRange != AFFECT_SELF:
            toon = base.cr.doId2do.get(self.lastClickedAvId)
            if not toon:
                self.generateResponse(responseType="NoTarget")
                return

        # Get the Magic Word info based off of it's name
        magicWord = commandName.lower()
        magicWordInfo = MagicWordIndex[magicWord]

        # Load the class tied to the Magic Word
        command = magicWordInfo['class']
        command.loadWord(None, self.cr, base.localAvatar.getDoId(), targetIds, args)

        # Execute the Magic Word and store the return value
        returnValue = command.executeWord()

        # If we have a return value, route it through
        if returnValue:
            self.generateResponse(responseType="Success", returnValue=returnValue)
        # If not just route a generic response through
        else:
            self.generateResponse(responseType="SuccessNoResp", magicWord=word, args=args, affectRange=affectRange,
                                  affectType=affectType, affectExtra=affectExtra, lastClickedAvId=lastClickedAvId)
