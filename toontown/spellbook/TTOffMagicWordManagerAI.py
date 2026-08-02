from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObjectAI

from otp.avatar.DistributedPlayerAI import DistributedPlayerAI
from otp.otpbase import OTPGlobals

from toontown.spellbook.MagicWordConfig import *
from toontown.spellbook.MagicWordIndex import *

import json
import os


MagicWordIndex = magicWordIndex.copy()

spellbookJsonDefaultValues = '''{
    "words":
    [
        {
            "name": "SetPos",
            "access": "USER"
        },
        {
            "name": "GetPos",
            "access": "USER"
        }
    ]
}
'''

if not os.path.exists('config/'):
    os.mkdir('config/')

if not os.path.isfile('config/spellbook.json'):
    with open('config/spellbook.json', 'w') as data:
        data.write(spellbookJsonDefaultValues)
        data.close()

with open('config/spellbook.json') as data:
    spellbook = json.load(data)

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


class TTOffMagicWordManagerAI(DistributedObjectAI.DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('TTOffMagicWordManagerAI')

    def requestExecuteMagicWord(self, affectRange, affectType, affectExtra, lastClickedAvId, magicWord):
        avId = self.air.getAvatarIdFromSender()
        toon = self.air.doId2do.get(avId)
        if not toon:
            self.notify.warning('requestExecuteMagicWord: Magic Word use requested but invoker avatar is non-existant!')
            return

        targetIds = []
        if affectRange in [AFFECT_SINGLE, AFFECT_BOTH]:
            targetIds.append(avId)

        if (affectRange in [AFFECT_OTHER, AFFECT_BOTH]) and affectType == AFFECT_SINGULAR:
            if lastClickedAvId:
                targetIds.append(lastClickedAvId)
            else:
                self.generateResponse(avId=avId, responseType = "NoTarget")
                return

        if affectType in [AFFECT_ZONE, AFFECT_SERVER, AFFECT_RANK]:
            toonIds = []
            for doId in list(self.air.doId2do.keys())[:]:
                do = self.air.doId2do.get(doId)
                if isinstance(do, DistributedPlayerAI) and do.isPlayerControlled() and do != toon:
                    if affectType == AFFECT_ZONE and do.zoneId == toon.zoneId:
                        toonIds.append(doId)
                    elif affectType == AFFECT_SERVER:
                        toonIds.append(doId)
                    elif affectType == AFFECT_RANK and do.getAccessLevel() == affectExtra:
                        toonIds.append(doId)

            if not toonIds and not targetIds:
                self.generateResponse(avId=avId, responseType = "NoTarget")
                return

            targetIds += toonIds

        if not targetIds:
            self.generateResponse(avId=avId, responseType = "NoTarget")
            return

        for targetId in targetIds:
            if targetId == avId:
                continue
            targetToon = self.air.doId2do.get(targetId)
            if not targetToon:
                continue
            # if targetToon.getAccessLevel() >= toon.getAccessLevel():
            #     targetIds.remove(targetId)
            #     continue

        if len(targetIds) == 0:
            self.generateResponse(avId=avId, responseType="NoAccessToTarget")

        magicWord, args = (magicWord.split(' ', 1) + [''])[:2]
        magicWord = magicWord.lower()
        magicWordInfo = MagicWordIndex.get(magicWord)
        
        # Is the client out of sync with the server?
        if magicWordInfo is None:
            self.generateResponse(avId=avId, responseType="BadWord")
            return

        if affectRange not in magicWordInfo['affectRange']:
            self.generateResponse(avId=avId, responseType="RestrictionOther")
            return

        if toon.getAccessLevel() < OTPGlobals.AccessLevelName2Int.get(magicWordInfo['access'], 0):
            if toon.getAccessLevel() == OTPGlobals.AccessLevelName2Int.get("NO_ACCESS") and \
               OTPGlobals.AccessLevelName2Int.get(magicWordInfo['access'], 0) == OTPGlobals.AccessLevelName2Int.get("USER"):
                self.generateResponse(avId=avId, responseType="NoCheatAccess")
                return
            self.generateResponse(avId=avId, responseType="NoAccess")
            return

        if self.air.defaultAccessLevel == 'NO_ACCESS':
            if not magicWordInfo['administrative']:
                self.generateResponse(avId=avId, responseType="LegitServer")
                return
        
        commandArgs = magicWordInfo['args']
        maxArgs = len(commandArgs)
        minArgs = 0
        argList = args.split(None, maxArgs-1)
        for argSet in commandArgs:
            isRequired = argSet[ARGUMENT_REQUIRED]
            if isRequired:
                minArgs += 1

        if len(argList) < minArgs:
            self.generateResponse(avId=avId, responseType = "NotEnoughArgs", extraMessageData = "{} argument{}".format(minArgs, "s" if minArgs != 1 else ''))
            return
        elif len(argList) > maxArgs:
            self.generateResponse(avId=avId, responseType = "TooManyArgs", extraMessageData = "{} argument{}".format(maxArgs, "s" if maxArgs != 1 else ''))
            return

        parsedArgList = []
        
        if len(argList) < maxArgs:
            for x in range(minArgs,maxArgs):
                if commandArgs[x][ARGUMENT_REQUIRED] or len(argList) >= x+1:
                    continue
                argList.append(commandArgs[x][ARGUMENT_DEFAULT])

        for x in range(len(argList)):
            arg = argList[x]
            argType = commandArgs[x][ARGUMENT_TYPE]
            try:
                parsedArg = argType(arg)
            except:
                self.generateResponse(avId=avId, responseType = "BadArgs")
                return

            parsedArgList.append(parsedArg)

        if magicWordInfo['execLocation'] == EXEC_LOC_CLIENT:
            self.sendClientCommand(avId, magicWord, magicWordInfo['classname'], targetIds=targetIds, parsedArgList=parsedArgList, affectRange=affectRange,
                                         affectType=affectType, affectExtra=affectExtra, lastClickedAvId=lastClickedAvId)
        else:
            command = getMagicWord(magicWordInfo['classname'])
            command = command(self.air, None, avId, targetIds, parsedArgList)
            returnValue = command.executeWord()
            if returnValue:
                self.generateResponse(avId=avId, responseType = "Success", returnValue=returnValue)
            else:
                self.generateResponse(avId=avId, responseType = "SuccessNoResp", magicWord=magicWord, parsedArgList=parsedArgList,
                                    affectRange=affectRange, affectType=affectType, affectExtra=affectExtra,
                                    lastClickedAvId=lastClickedAvId)

    def generateResponse(self, avId, responseType = "BadWord", magicWord='', parsedArgList=None, returnValue='', affectRange=0,
                         affectType=0, affectExtra=0, lastClickedAvId=0, extraMessageData=''):
        if not parsedArgList:
            parsedArgList = []

        parsedArgList = json.dumps(parsedArgList)
        self.sendUpdateToAvatarId(avId, 'generateResponse',
                                  [responseType, magicWord, parsedArgList, returnValue, affectRange, affectType,
                                   affectExtra, lastClickedAvId, extraMessageData])

    def sendClientCommand(self, avId, word, commandName, targetIds=[], parsedArgList=None, affectRange=0,
                          affectType=0, affectExtra=0, lastClickedAvId=0):
        if not parsedArgList:
            parsedArgList = []

        parsedArgList = json.dumps(parsedArgList)
        self.sendUpdateToAvatarId(avId, "executeMagicWord", [word, commandName, targetIds, parsedArgList, affectRange, affectType, affectExtra, lastClickedAvId])
