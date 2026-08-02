from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObject

from libotp import WhisperPopup
from libotp.nametag.WhisperGlobals import WhisperType
from otp.otpbase.OTPGlobals import *

from toontown.spellbook.MagicWordConfig import *
from toontown.spellbook.MagicWordIndex import *

import json
import random
import string

class TTOffMagicWordManager(DistributedObject.DistributedObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('TTOffMagicWordManager')
    neverDisable = 1

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        base.cr.magicWordManager = self
        self.chatPrefix = PREFIX_DEFAULT
        self.wizardName = WIZARD_DEFAULT
        self.lastClickedAvId = 0

    def announceGenerate(self):
        DistributedObject.DistributedObject.announceGenerate(self)
        activatorIndex = base.settings.get('magic-word-activator')
        if 0 <= activatorIndex <= (len(PREFIX_ALLOWED) - 1):
            self.chatPrefix = PREFIX_ALLOWED[activatorIndex]

        self.accept(INCOMING_CHAT_MESSAGE_NAME, self.checkMagicWord)
        self.accept('clickedNametag', self.__handleClickedNametag)

    def disable(self):
        DistributedObject.DistributedObject.disable(self)
        self.ignore(INCOMING_CHAT_MESSAGE_NAME)
        self.ignore('clickedNametag')

    def setChatPrefix(self, chatPrefix):
        self.chatPrefix = chatPrefix

    def __handleClickedNametag(self, avatar):
        if avatar:
            self.lastClickedAvId = avatar.getDoId()

    def checkMagicWord(self, magicWord):
        if not magicWord.startswith(self.chatPrefix):
            return

        if base.localAvatar.getAccessLevel() < AccessLevelName2Int.get('NO_ACCESS'):
            self.generateResponse(responseType="NoAccess")
            return

        self.handleMagicWord(magicWord)

    def generateResponse(self, responseType, magicWord='', args=None, returnValue=None, affectRange=None,
                         affectType=None, affectExtra=None, lastClickedAvId=None, extraMessageData = None):
        response = self.generateMagicWordResponse(responseType, magicWord, args, returnValue, affectRange, affectType,
                                                  affectExtra, lastClickedAvId, extraMessageData)
        base.localAvatar.setSystemMessage(0, response, WhisperType.WTMagicWord)
        self.notify.info(response)

    def generateMagicWordResponse(self, responseType, magicWord, args, returnValue, affectRange, affectType,
                                  affectExtra, lastClickedAvId, extraMessageData):
        response = ''
        if responseType == "SuccessNoResp" and magicWord:
            response = ''
            successExclaim = random.choice(MAGIC_WORD_SUCCESS_PHRASES)
            response += successExclaim
            return response
        elif responseType == "Success":
            response += returnValue
            return response
        response += MAGIC_WORD_RESPONSES.get(responseType, "...I don't know how to respond!")
        if responseType in MagicWordConfig.HAS_EXTRA_MESSAGE_DATA:
            response = response.format(extraMessageData)
        return response

    def handleMagicWord(self, magicWord):
        affectRange = AFFECT_NONE
        affectType = AFFECT_SINGULAR
        affectExtra = -1
        for x in range(3):
            if magicWord.startswith(self.chatPrefix * (3 - x)):
                affectRange = 2 - x
                break

        if affectRange == AFFECT_NONE:
            self.generateResponse(responseType = "NoEffect")
            return
        elif affectRange == AFFECT_OTHER:
            toon = base.cr.doId2do.get(self.lastClickedAvId)
            if not toon:
                self.generateResponse(responseType = "NoTarget")
                return
            if toon.getTransitioning():
                self.generateResponse(responseType = "OtherTeleporting")
                return

        activatorLength = affectRange + 1
        magicWordNoPrefix = magicWord[activatorLength:]
        for type in AFFECT_TYPES:
            if magicWordNoPrefix.startswith(type):
                magicWordNoPrefix = magicWordNoPrefix[len(type):]
                affectType = AFFECT_TYPES.index(type)
                break

        if affectType == AFFECT_RANK:
            for level in list(OTPGlobals.AccessLevelName2Int.values()):
                if magicWordNoPrefix.startswith(str(level)):
                    try: # FIXME: !?!?!?!?!??!?!
                        int(magicWordNoPrefix[len(str(level)):][:1])
                        self.generateResponse(responseType = "BadTarget") # ????
                        return
                    except:
                        pass

                    magicWordNoPrefix = magicWordNoPrefix[len(str(level)):]
                    affectExtra = level
                    break

            if affectExtra == -1:
                self.generateResponse(responseType = "BadTarget")
                return

        word = magicWordNoPrefix.split(' ', 1)[0].lower()
        if word not in magicWordIndex:
            for magicWord in list(magicWordIndex.keys()):
                if word in magicWord:
                    self.generateResponse(responseType = "CloseWord", extraMessageData = magicWord)
                    return
            self.generateResponse(responseType = "BadWord")
            return

        magicWordInfo = magicWordIndex[word]
        if magicWordInfo['execLocation'] == EXEC_LOC_INVALID:
            raise ValueError("execLocation not set for magic word {}!".format(magicWordInfo['classname']))
        elif magicWordInfo['execLocation'] in [EXEC_LOC_SERVER, EXEC_LOC_CLIENT]:
            self.sendUpdate('requestExecuteMagicWord',
                            [affectRange, affectType, affectExtra, self.lastClickedAvId, magicWordNoPrefix])
    
    def executeMagicWord(self, word, commandName, targetIds, args, affectRange, affectType, affectExtra, lastClickedAvId):
        command = getMagicWord(commandName)
        command = command(None, self.cr, base.localAvatar.getDoId(), targetIds, args)

        returnValue = command.executeWord()
        if returnValue:
            self.generateResponse(responseType = "Success", returnValue=returnValue)
        else:
            self.generateResponse(responseType = "SuccessNoResp", magicWord=word, args=args,
                                  affectRange=affectRange, affectType=affectType, affectExtra=affectExtra,
                                  lastClickedAvId=lastClickedAvId)
