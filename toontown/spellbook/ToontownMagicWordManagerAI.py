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
from direct.distributed import DistributedObjectAI

from otp.avatar.DistributedPlayerAI import DistributedPlayerAI

from toontown.spellbook.MagicWordConfig import *
from toontown.spellbook.MagicWordIndex import *

import json
import os

# All of the data regarding our Magic Words
MagicWordIndex = magicWordIndex.copy()

# You should only concern yourself with the following code if you want to add customization features to Magic Words
# This is only really useful in Toontown Offline, so other projects shouldn't have to really worry about it

# We allow server hosters to change a few things about the Magic Words on their server
# These are the default values generated with spellbook.json to help get them started
spellbookJsonDefaultValues = CUSTOM_SPELLBOOK_DEFAULT

# If we don't have a config directory, make it
if not os.path.exists('config/'):
    os.mkdir('config/')

# If spellbook.json doesn't exist, make it
if not os.path.isfile('config/spellbook.json'):
    with open('config/spellbook.json', 'w') as data:
        data.write(spellbookJsonDefaultValues)
        data.close()

# Now load the data from spellbook.json
with open('config/spellbook.json') as data:
    spellbook = json.load(data)

# Make changes to all the Magic Words based on the data in spellbook.json
for word in spellbook['words']:
    name = word['name']
    accessLevel = word['access']

    if accessLevel not in list(OTPGlobals.AccessLevelName2Int.keys()):
        break

    try:
        wordInfo = MagicWordIndex[str(name.lower())]
        for alias in wordInfo['aliases']:
            MagicWordIndex[alias]['access'] = accessLevel
    except:
        pass


class ToontownMagicWordManagerAI(DistributedObjectAI.DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToontownMagicWordManagerAI')

    def requestExecuteMagicWord(self, affectRange, affectType, affectExtra, lastClickedAvId, magicWord):
        avId = self.air.getAvatarIdFromSender()

        # It's not good if we can't get the avId for whatever reason
        if not avId:
            self.notify.warning('requestExecuteMagicWord: Magic Word use requested but invoker avId is non-existent!')
            return

        # We also need the Toon as well, or else this Magic Word isn't going to do much good
        toon = self.air.doId2do.get(avId)
        if not toon:
            self.notify.warning('requestExecuteMagicWord: Magic Word use requested but invoker avatar is non-existent!')
            return

        # Same thing with the Toontorial. Magic Words are strictly forbidden here
        # Tell the user they can't use it because they're in the Toontorial
        if hasattr(self.air, 'tutorialManager') and avId in list(self.air.tutorialManager.avId2fsm.keys()):
            self.generateResponse(avId=avId, responseType="Tutorial")
            return

        # Our Magic Word affectRange is either SELF (the invoker) or BOTH (invoker and a target)
        # Because of this, we should add the invoker to the target list
        targetIds = []
        if affectRange in (AFFECT_SELF, AFFECT_BOTH):
            targetIds.append(avId)

        # This Magic Word's affectRange is either OTHER (a target) or BOTH (invoker and a target)
        # However, it's also a NORMAL affectType, so it's not as if we're targeting a zone or the whole server
        # In that case, let's try to grab the single target by the lastClickedAvId provided by the invoker
        lastClickedToon = None
        if (affectRange in (AFFECT_OTHER, AFFECT_BOTH)) and affectType == AFFECT_NORMAL:
            if lastClickedAvId:
                lastClickedToon = self.air.doId2do.get(lastClickedAvId)
                if lastClickedToon:
                    targetIds.append(lastClickedAvId)
            else:
                self.generateResponse(avId=avId, responseType="NoTarget")
                return

        # The affectType is ZONE (zone the invoker is in), SERVER (the entire server), or RANK (specified access level)
        # Gather all of the Toons using whichever method this Magic Word requests
        if affectType in (AFFECT_ZONE, AFFECT_SERVER, AFFECT_RANK):
            toonIds = []
            # Iterate over a copy of every single doId on the server
            for doId in list(self.air.doId2do.keys())[:]:
                do = self.air.doId2do.get(doId)
                # We only care if our DistributedObject is a player that is NOT our invoker (we dealt with that earlier)
                if isinstance(do, DistributedPlayerAI) and do.isPlayerControlled() and do != toon:
                    # Only add the Toons that are in the same zone as the invoker
                    if affectType == AFFECT_ZONE and do.zoneId == toon.zoneId:
                        toonIds.append(doId)
                    # Add every Toon regardless of zone
                    elif affectType == AFFECT_SERVER:
                        toonIds.append(doId)
                    # Only add the Toons that have the Access Level specified when the Magic Word was used
                    elif affectType == AFFECT_RANK and do.getAccessLevel() == affectExtra:
                        toonIds.append(doId)

            # There were no Toons we could perform this Magic Word on, so let the invoker know that
            if not toonIds and not targetIds:
                self.generateResponse(avId=avId, responseType="NoTarget")
                return

            # Add the found Toons to the targetId list
            targetIds += toonIds

        # If, at this point, we still don't have any targets somehow, then let the invoker know that
        if not targetIds:
            self.generateResponse(avId=avId, responseType="NoTarget")
            return

        # Access level of the invoker
        invokerAccess = int(round(toon.getAccessLevel(), -2))

        # Access level of the selected target, if we have one
        targetAccess = 0
        if lastClickedAvId and lastClickedToon:
            targetAccess = lastClickedToon.getAccessLevel()

        # Now that we have all the avIds of who we want to target with this Magic Word, let's run some sanity checks
        # First things first, let's make sure the invoker is allowed to target who they want to target
        for targetId in targetIds:
            # Of course the invoker has access to target themselves
            if targetId == avId:
                continue
            # If our target DistributedObject doesn't exist anymore for whatever reason, just ignore them
            targetToon = self.air.doId2do.get(targetId)
            if not targetToon:
                continue
            # Get the Access Level of the target and round it to the nearest 100th
            # This kind of thing is useful for roles like BUILDER, that are technically higher than USER
            # They should have more perms than USERS, but shouldn't be allowed to target them
            targetAccess = int(round(targetToon.getAccessLevel(), -2))
            # If the Access Level of the target is greater than or equal to than that of the invoker, remove them
            if targetAccess >= invokerAccess:
                targetIds.remove(targetId)
                continue

        # Function that returns a readable name in place of the Toon's Access Level
        def getAccessName(accessLevel):
            return OTPGlobals.AccessLevelDebug2Name.get(OTPGlobals.AccessLevelInt2Name.get(accessLevel))

        # If, after the previous check, we don't have any more targets, let's inform the invoker about it
        if len(targetIds) == 0:
            # If affectType is NORMAL, let the invoker know what their Access Level is compared to their target
            if (affectRange in (AFFECT_OTHER, AFFECT_BOTH)) and affectType == AFFECT_NORMAL:
                # Parse the Access Level of the invoker and target
                parsedTargetAccess = getAccessName(targetAccess)
                parsedInvokerAccess = getAccessName(invokerAccess)
                # Create a nice little message to tell the invoker the difference between the Access Levels
                returnValue = MAGIC_WORD_RESPONSES.get("NoAccessSingleTarget")
                returnValue = returnValue.format(lastClickedToon.getName(), parsedTargetAccess, parsedInvokerAccess)
                self.generateResponse(avId=avId, responseType="Success", returnValue=returnValue)
            # Otherwise, just let the invoker know that everyone who was targeted was not allowed to be
            else:
                self.generateResponse(avId=avId, responseType="NoAccessToTarget")
            return

        # We're finally done determining everything related to the targets. Finally, let's get into the word itself
        # We start by separating the word used from it's arguments
        magicWord, args = (magicWord.split(' ', 1) + [''])[:2]

        # Get the name of the word in lowercase
        magicWord = magicWord.lower()

        # Lookup the info for this word
        magicWordInfo = MagicWordIndex[magicWord]

        # Make sure the invoker has a high enough Access Level to use this Magic Word in the first place
        # If they don't, them let them know about it
        if toon.getAccessLevel() < OTPGlobals.AccessLevelName2Int.get(magicWordInfo['access']):
            self.generateResponse(avId=avId, responseType="NoAccess")
            return

        # If a config option disables cheaty Magic Words and ours is deemed cheaty, let the invoker know
        if hasattr(self.air, 'nonCheaty') and self.air.nonCheaty:
            if not magicWordInfo['administrative']:
                self.generateResponse(avId=avId, responseType="NonCheaty")
                return

        # If the affectRange circumstance made by the invoker is not allowed, let them know about it
        # This kind of thing is good to make sure that words that shouldn't really have a particular target don't end
        # up getting used in mass. For example, you don't want to use a word intended to kill a Cog Boss on other Toons
        if affectRange not in magicWordInfo['affectRange']:
            self.generateResponse(avId=avId, responseType="RestrictionOther")
            return

        # Get the arguments the Magic Word will accept
        commandArgs = magicWordInfo['args']

        # Determine the max and min amount of arguments the word will accept
        maxArgs = len(commandArgs)
        minArgs = 0
        argList = args.split(None, maxArgs-1)
        for argSet in commandArgs:
            isRequired = argSet[ARGUMENT_REQUIRED]
            if isRequired:
                minArgs += 1

        # If we have less arguments provided than are required, let the invoker know that
        messageData = "{} argument{}"
        if len(argList) < minArgs:
            messageData = messageData.format(minArgs, "s" if minArgs != 1 else '')
            self.generateResponse(avId=avId, responseType="NotEnoughArgs", extraMessageData=messageData)
            return
        # On the other hand, if we have more than what we need, tell them that instead
        elif len(argList) > maxArgs:
            messageData = messageData.format(maxArgs, "s" if maxArgs != 1 else '')
            self.generateResponse(avId=avId, responseType="TooManyArgs", extraMessageData=messageData)
            return

        # If we have less arguments provided than the max, use the defaults of the ones not provided
        if len(argList) < maxArgs:
            for x in range(minArgs, maxArgs):
                if commandArgs[x][ARGUMENT_REQUIRED] or len(argList) >= x + 1:
                    continue
                argList.append(commandArgs[x][ARGUMENT_DEFAULT])

        # Parse through all the args we had provided
        parsedArgList = []
        for x in range(len(argList)):
            arg = argList[x]
            argType = commandArgs[x][ARGUMENT_TYPE]
            try:
                parsedArg = argType(arg)
            except:
                self.generateResponse(avId=avId, responseType="BadArgs")
                return

            parsedArgList.append(parsedArg)

        # If this is a client-sided Magic Word, execute it on the client
        if magicWordInfo['execLocation'] == EXEC_LOC_CLIENT:
            # We are only allowed to target ourselves with client-sided Magic Words
            if len(targetIds) == 1 and avId in targetIds:
                self.sendClientCommand(avId, magicWord, magicWordInfo['classname'], targetIds=targetIds,
                                       parsedArgList=parsedArgList, affectRange=affectRange, affectType=affectType,
                                       affectExtra=affectExtra, lastClickedAvId=lastClickedAvId)
            else:
                self.generateResponse(avId=avId, responseType="CannotTarget")
                return
        # But if it's a server-sided one, execute it on the server
        else:
            # Find the class associated with our Magic Word and load it
            command = magicWordInfo['class']
            command.loadWord(self.air, None, avId, targetIds, parsedArgList)
            # Execute the Magic Word and grab a return value
            returnValue = command.executeWord()
            # If we have a return value, pass it over to the invoker
            if returnValue:
                self.generateResponse(avId=avId, responseType="Success", returnValue=returnValue)
            # Otherwise just throw a default response to them
            else:
                self.generateResponse(avId=avId, responseType="SuccessNoResp", magicWord=magicWord,
                                      parsedArgList=parsedArgList, affectRange=affectRange, affectType=affectType,
                                      affectExtra=affectExtra, lastClickedAvId=lastClickedAvId)

    def generateResponse(self, avId, responseType="BadWord", magicWord='', parsedArgList=(), returnValue='',
                         affectRange=0, affectType=0, affectExtra=0, lastClickedAvId=0, extraMessageData=''):
        # Pack up the arg list so it's ready to ship to the client
        parsedArgList = json.dumps(parsedArgList)
        # Send the invoker a response to their use of the word
        self.sendUpdateToAvatarId(avId, 'generateResponse',
                                  [responseType, magicWord, parsedArgList, returnValue, affectRange, affectType,
                                   affectExtra, lastClickedAvId, extraMessageData])

    def sendClientCommand(self, avId, word, commandName, targetIds=(), parsedArgList=(), affectRange=0, affectType=0,
                          affectExtra=0, lastClickedAvId=0):
        # Pack up the arg list so it's ready to ship to the client
        parsedArgList = json.dumps(parsedArgList)
        # Execute the Magic Word on the client, because it's a client-sided Magic Word
        self.sendUpdateToAvatarId(avId, "executeMagicWord", [word, commandName, targetIds, parsedArgList, affectRange,
                                                             affectType, affectExtra, lastClickedAvId])
