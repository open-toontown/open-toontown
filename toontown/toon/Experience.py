from pandac.PandaModules import *
from toontown.toonbase.ToontownBattleGlobals import *
from direct.directnotify import DirectNotifyGlobal
from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator
from otp.otpbase import OTPGlobals

class Experience:
    notify = DirectNotifyGlobal.directNotify.newCategory('Experience')

    def __init__(self, expStr = None, owner = None):
        self.owner = owner
        if expStr == None:
            self.experience = []
            for track in range(0, len(Tracks)):
                self.experience.append(StartingLevel)

        else:
            self.experience = self.makeFromNetString(expStr)
        return

    def __str__(self):
        return str(self.experience)

    def makeNetString(self):
        dataList = self.experience
        datagram = PyDatagram()
        for track in range(0, len(Tracks)):
            datagram.addUint16(dataList[track])

        dgi = PyDatagramIterator(datagram)
        return dgi.getRemainingBytes()

    def makeFromNetString(self, netString):
        dataList = []
        dg = PyDatagram(netString)
        dgi = PyDatagramIterator(dg)
        for track in range(0, len(Tracks)):
            dataList.append(dgi.getUint16())

        return dataList

    def addExp(self, track, amount = 1):
        if type(track) == type(''):
            track = Tracks.index(track)
        self.notify.debug('adding %d exp to track %d' % (amount, track))
        if self.owner.getGameAccess() == OTPGlobals.AccessFull:
            if self.experience[track] + amount <= MaxSkill:
                self.experience[track] += amount
            else:
                self.experience[track] = MaxSkill
        elif self.experience[track] + amount <= UnpaidMaxSkills[track]:
            self.experience[track] += amount
        elif self.experience[track] > UnpaidMaxSkills[track]:
            self.experience[track] += 0
        else:
            self.experience[track] = UnpaidMaxSkills[track]

    def maxOutExp(self):
        for track in range(0, len(Tracks)):
            self.experience[track] = MaxSkill - UberSkill

    def maxOutExpMinusOne(self):
        for track in range(0, len(Tracks)):
            self.experience[track] = MaxSkill - 1

    def makeExpHigh(self):
        for track in range(0, len(Tracks)):
            self.experience[track] = Levels[track][len(Levels[track]) - 1] - 1

    def makeExpRegular(self):
        import random
        for track in range(0, len(Tracks)):
            rank = random.choice((0, int(random.random() * 1500.0), int(random.random() * 2000.0)))
            self.experience[track] = Levels[track][len(Levels[track]) - 1] - rank

    def zeroOutExp(self):
        for track in range(0, len(Tracks)):
            self.experience[track] = StartingLevel

    def setAllExp(self, num):
        for track in range(0, len(Tracks)):
            self.experience[track] = num

    def getExp(self, track):
        if type(track) == type(''):
            track = Tracks.index(track)
        return self.experience[track]

    def setExp(self, track, exp):
        if type(track) == type(''):
            track = Tracks.index(track)
        self.experience[track] = exp

    def getExpLevel(self, track):
        if type(track) == type(''):
            track = Tracks.index(track)
        level = 0
        for amount in Levels[track]:
            if self.experience[track] >= amount:
                level = Levels[track].index(amount)

        return level

    def getTotalExp(self):
        total = 0
        for level in self.experience:
            total += level

        return total

    def getNextExpValue(self, track, curSkill = None):
        if curSkill == None:
            curSkill = self.experience[track]
        retVal = Levels[track][len(Levels[track]) - 1]
        for amount in Levels[track]:
            if curSkill < amount:
                retVal = amount
                return retVal

        return retVal

    def getNewGagIndexList(self, track, extraSkill):
        retList = []
        curSkill = self.experience[track]
        nextExpValue = self.getNextExpValue(track, curSkill)
        finalGagFlag = 0
        while curSkill + extraSkill >= nextExpValue and curSkill < nextExpValue and not finalGagFlag:
            retList.append(Levels[track].index(nextExpValue))
            newNextExpValue = self.getNextExpValue(track, nextExpValue)
            if newNextExpValue == nextExpValue:
                finalGagFlag = 1
            else:
                nextExpValue = newNextExpValue

        return retList
