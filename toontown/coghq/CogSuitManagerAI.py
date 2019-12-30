from otp.ai.AIBaseGlobal import *
from direct.directnotify import DirectNotifyGlobal
import random
from toontown.suit import SuitDNA
from . import CogDisguiseGlobals

class CogSuitManagerAI:
    notify = DirectNotifyGlobal.directNotify.newCategory('CogSuitManagerAI')

    def __init__(self, air):
        self.air = air

    def recoverPart(self, av, factoryType, suitTrack, zoneId, avList):
        partsRecovered = [
         0, 0, 0, 0]
        part = av.giveGenericCogPart(factoryType, suitTrack)
        if part:
            partsRecovered[CogDisguiseGlobals.dept2deptIndex(suitTrack)] = part
            self.air.questManager.toonRecoveredCogSuitPart(av, zoneId, avList)
        return partsRecovered
