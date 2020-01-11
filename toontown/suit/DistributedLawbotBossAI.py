from otp.ai.AIBaseGlobal import *
from direct.distributed.ClockDelta import *
from toontown.suit import DistributedBossCogAI
from direct.directnotify import DirectNotifyGlobal
from otp.avatar import DistributedAvatarAI
from toontown.suit import DistributedSuitAI
from toontown.battle import BattleExperienceAI
from direct.fsm import FSM
from toontown.toonbase import ToontownGlobals
from toontown.toon import InventoryBase
from toontown.toonbase import TTLocalizer
from toontown.battle import BattleBase
from toontown.toon import NPCToons
from toontown.building import SuitBuildingGlobals
from toontown.suit import SuitDNA
import random
from toontown.coghq import DistributedLawbotBossGavelAI
from toontown.suit import DistributedLawbotBossSuitAI
from toontown.coghq import DistributedLawbotCannonAI
from toontown.coghq import DistributedLawbotChairAI
from toontown.toonbase import ToontownBattleGlobals

class DistributedLawbotBossAI(DistributedBossCogAI.DistributedBossCogAI, FSM.FSM):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedLawbotBossAI')
    limitHitCount = 6
    hitCountDamage = 35
    numPies = 10
    maxToonLevels = 77

    def __init__(self, air):
        DistributedBossCogAI.DistributedBossCogAI.__init__(self, air, 'l')
        FSM.FSM.__init__(self, 'DistributedLawbotBossAI')
        self.lawyers = []
        self.cannons = None
        self.chairs = None
        self.gavels = None
        self.cagedToonNpcId = random.choice(list(NPCToons.npcFriends.keys()))
        self.bossMaxDamage = ToontownGlobals.LawbotBossMaxDamage
        self.recoverRate = 0
        self.recoverStartTime = 0
        self.bossDamage = ToontownGlobals.LawbotBossInitialDamage
        self.useCannons = 1
        self.numToonJurorsSeated = 0
        self.cannonBallsLeft = {}
        self.toonLevels = 0
        if 'Defeat' not in self.keyStates:
            self.keyStates.append('Defeat')
        self.toonupValue = 1
        self.bonusState = False
        self.bonusTimeStarted = 0
        self.numBonusStates = 0
        self.battleThreeTimeStarted = 0
        self.battleThreeTimeInMin = 0
        self.numAreaAttacks = 0
        self.lastAreaAttackTime = 0
        self.weightPerToon = {}
        self.cannonIndexPerToon = {}
        self.battleDifficulty = 0
        return

    def delete(self):
        self.notify.debug('DistributedLawbotBossAI.delete')
        self.__deleteBattleThreeObjects()
        self.__deleteBattleTwoObjects()
        taskName = self.uniqueName('clearBonus')
        taskMgr.remove(taskName)
        return DistributedBossCogAI.DistributedBossCogAI.delete(self)

    def getHoodId(self):
        return ToontownGlobals.LawbotHQ

    def getCagedToonNpcId(self):
        return self.cagedToonNpcId

    def magicWordHit(self, damage, avId):
        if self.attackCode != ToontownGlobals.BossCogDizzyNow:
            self.hitBossInsides()
        self.hitBoss(damage)

    def hitBoss(self, bossDamage):
        avId = self.air.getAvatarIdFromSender()
        if not self.validate(avId, avId in self.involvedToons, 'DistributedLawbotbossAI.hitBoss from unknown avatar'):
            return
        self.validate(avId, bossDamage == 1, 'invalid bossDamage %s' % bossDamage)
        if bossDamage < 1:
            return
        currState = self.getCurrentOrNextState()
        if currState != 'BattleThree':
            return
        if bossDamage <= 12:
            newWeight = self.weightPerToon.get(avId)
            if newWeight:
                bossDamage = newWeight
        if self.bonusState and bossDamage <= 12:
            bossDamage *= ToontownGlobals.LawbotBossBonusWeightMultiplier
        bossDamage = min(self.getBossDamage() + bossDamage, self.bossMaxDamage)
        self.b_setBossDamage(bossDamage, 0, 0)
        if self.bossDamage >= self.bossMaxDamage:
            self.b_setState('Victory')
        else:
            self.__recordHit()

    def healBoss(self, bossHeal):
        bossDamage = -bossHeal
        avId = self.air.getAvatarIdFromSender()
        currState = self.getCurrentOrNextState()
        if currState != 'BattleThree':
            return
        bossDamage = min(self.getBossDamage() + bossDamage, self.bossMaxDamage)
        bossDamage = max(bossDamage, 0)
        self.b_setBossDamage(bossDamage, 0, 0)
        if self.bossDamage == 0:
            self.b_setState('Defeat')
        else:
            self.__recordHit()

    def hitBossInsides(self):
        avId = self.air.getAvatarIdFromSender()
        if not self.validate(avId, avId in self.involvedToons, 'hitBossInsides from unknown avatar'):
            return
        currState = self.getCurrentOrNextState()
        if currState != 'BattleThree':
            return
        self.b_setAttackCode(ToontownGlobals.BossCogDizzyNow)
        self.b_setBossDamage(self.getBossDamage(), 0, 0)

    def hitToon(self, toonId):
        avId = self.air.getAvatarIdFromSender()
        if not self.validate(avId, avId != toonId, 'hitToon on self'):
            return
        if avId not in self.involvedToons or toonId not in self.involvedToons:
            return
        toon = self.air.doId2do.get(toonId)
        if toon:
            self.healToon(toon, self.toonupValue)
            self.sendUpdate('toonGotHealed', [toonId])

    def touchCage(self):
        avId = self.air.getAvatarIdFromSender()
        currState = self.getCurrentOrNextState()
        if currState != 'BattleThree' and currState != 'NearVictory':
            return
        if not self.validate(avId, avId in self.involvedToons, 'touchCage from unknown avatar'):
            return
        toon = simbase.air.doId2do.get(avId)
        if toon:
            toon.b_setNumPies(self.numPies)
            toon.__touchedCage = 1

    def touchWitnessStand(self):
        self.touchCage()

    def finalPieSplat(self):
        self.notify.debug('finalPieSplat')
        if self.state != 'NearVictory':
            return
        self.b_setState('Victory')

    def doTaunt(self):
        if not self.state == 'BattleThree':
            return
        tauntIndex = random.randrange(len(TTLocalizer.LawbotBossTaunts))
        extraInfo = 0
        if tauntIndex == 0 and self.involvedToons:
            extraInfo = random.randrange(len(self.involvedToons))
        self.sendUpdate('setTaunt', [tauntIndex, extraInfo])

    def doNextAttack(self, task):
        for lawyer in self.lawyers:
            lawyer.doNextAttack(self)
            
        self.waitForNextAttack(ToontownGlobals.LawbotBossLawyerCycleTime)
        timeSinceLastAttack = globalClock.getFrameTime() - self.lastAreaAttackTime
        allowedByTime = 15 < timeSinceLastAttack or self.lastAreaAttackTime == 0
        doAttack = random.randrange(1,101)
        self.notify.debug('allowedByTime=%d doAttack=%d' % (allowedByTime, doAttack))
        if doAttack <= ToontownGlobals.LawbotBossChanceToDoAreaAttack and allowedByTime:
            self.__doAreaAttack()
            self.numAreaAttacks += 1
            self.lastAreaAttackTime = globalClock.getFrameTime()
        else:
            chanceToDoTaunt = ToontownGlobals.LawbotBossChanceForTaunt
            action = random.randrange(1,101)
            if action <= chanceToDoTaunt:
                self.doTaunt()
                pass
        return
        if self.attackCode == ToontownGlobals.BossCogDizzyNow:
            attackCode = ToontownGlobals.BossCogRecoverDizzyAttack
        else:
            attackCode = random.choice([ToontownGlobals.BossCogAreaAttack,
             ToontownGlobals.BossCogFrontAttack,
             ToontownGlobals.BossCogDirectedAttack,
             ToontownGlobals.BossCogDirectedAttack,
             ToontownGlobals.BossCogDirectedAttack,
             ToontownGlobals.BossCogDirectedAttack])
        if attackCode == ToontownGlobals.BossCogAreaAttack: 
            self.__doAreaAttack()
        elif attackCode == ToontownGlobals.BossCogDirectedAttack:
            self.__doDirectedAttack()
        else:
            self.b_setAttackCode(attackCode)

    def __doAreaAttack(self):
        self.b_setAttackCode(ToontownGlobals.BossCogAreaAttack)

    def __doDirectedAttack(self):
        if self.nearToons:
            toonId = random.choice(self.nearToons)
            self.b_setAttackCode(ToontownGlobals.BossCogDirectedAttack, toonId)
        else:
            self.__doAreaAttack()

    def b_setBossDamage(self, bossDamage, recoverRate, recoverStartTime):
        self.d_setBossDamage(bossDamage, recoverRate, recoverStartTime)
        self.setBossDamage(bossDamage, recoverRate, recoverStartTime)

    def setBossDamage(self, bossDamage, recoverRate, recoverStartTime):
        self.bossDamage = bossDamage
        self.recoverRate = recoverRate
        self.recoverStartTime = recoverStartTime

    def getBossDamage(self):
        now = globalClock.getFrameTime()
        elapsed = now - self.recoverStartTime
        return int(max(self.bossDamage - self.recoverRate * elapsed / 60.0, 0))

    def d_setBossDamage(self, bossDamage, recoverRate, recoverStartTime):
        timestamp = globalClockDelta.localToNetworkTime(recoverStartTime)
        self.sendUpdate('setBossDamage', [bossDamage, recoverRate, timestamp])

    def waitForNextStrafe(self, delayTime):
        currState = self.getCurrentOrNextState()
        if currState == 'BattleThree':
            taskName = self.uniqueName('NextStrafe')
            taskMgr.remove(taskName)
            taskMgr.doMethodLater(delayTime, self.doNextStrafe, taskName)

    def stopStrafes(self):
        taskName = self.uniqueName('NextStrafe')
        taskMgr.remove(taskName)

    def doNextStrafe(self, task):
        if self.attackCode != ToontownGlobals.BossCogDizzyNow:
            side = random.choice([0, 1])
            direction = random.choice([0, 1])
            self.sendUpdate('doStrafe', [side, direction])
        delayTime = 9
        self.waitForNextStrafe(delayTime)

    def __sendLawyerIds(self):
        lawyerIds = []
        for suit in self.lawyers:
            lawyerIds.append(suit.doId)

        self.sendUpdate('setLawyerIds', [lawyerIds])

    def d_cagedToonBattleThree(self, index, avId):
        self.sendUpdate('cagedToonBattleThree', [index, avId])

    def formatReward(self):
        return str(self.cagedToonNpcId)

    def makeBattleOneBattles(self):
        self.postBattleState = 'RollToBattleTwo'
        self.initializeBattles(1, ToontownGlobals.LawbotBossBattleOnePosHpr)

    def generateSuits(self, battleNumber):
        if battleNumber == 1:
            weakenedValue = (
             (1, 1), (2, 2), (2, 2), (1, 1), (1, 1, 1, 1, 1))
            listVersion = list(SuitBuildingGlobals.SuitBuildingInfo)
            if simbase.config.GetBool('lawbot-boss-cheat', 0):
                listVersion[13] = weakenedValue
                SuitBuildingGlobals.SuitBuildingInfo = tuple(listVersion)
            return self.invokeSuitPlanner(13, 0)
        else:
            return self.invokeSuitPlanner(13, 1)

    def removeToon(self, avId):
        toon = simbase.air.doId2do.get(avId)
        if toon:
            toon.b_setNumPies(0)
        DistributedBossCogAI.DistributedBossCogAI.removeToon(self, avId)

    def enterOff(self):
        self.notify.debug('enterOff')
        DistributedBossCogAI.DistributedBossCogAI.enterOff(self)
        self.__deleteBattleThreeObjects()
        self.__resetLawyers()

    def enterElevator(self):
        self.notify.debug('enterElevatro')
        DistributedBossCogAI.DistributedBossCogAI.enterElevator(self)
        self.b_setBossDamage(ToontownGlobals.LawbotBossInitialDamage, 0, 0)

    def enterIntroduction(self):
        self.notify.debug('enterIntroduction')
        DistributedBossCogAI.DistributedBossCogAI.enterIntroduction(self)
        self.b_setBossDamage(ToontownGlobals.LawbotBossInitialDamage, 0, 0)
        self.__makeChairs()

    def exitIntroduction(self):
        self.notify.debug('exitIntroduction')
        DistributedBossCogAI.DistributedBossCogAI.exitIntroduction(self)

    def enterRollToBattleTwo(self):
        self.divideToons()
        self.__makeCannons()
        self.barrier = self.beginBarrier('RollToBattleTwo', self.involvedToons, 50, self.__doneRollToBattleTwo)

    def __doneRollToBattleTwo(self, avIds):
        self.b_setState('PrepareBattleTwo')

    def exitRollToBattleTwo(self):
        self.ignoreBarrier(self.barrier)

    def enterPrepareBattleTwo(self):
        self.__makeCannons()
        self.barrier = self.beginBarrier('PrepareBattleTwo', self.involvedToons, 45, self.__donePrepareBattleTwo)
        self.makeBattleTwoBattles()

    def __donePrepareBattleTwo(self, avIds):
        self.b_setState('BattleTwo')

    def exitPrepareBattleTwo(self):
        self.ignoreBarrier(self.barrier)

    def __makeCannons(self):
        if self.cannons == None:
            self.cannons = []
            startPt = Point3(*ToontownGlobals.LawbotBossCannonPosA)
            endPt = Point3(*ToontownGlobals.LawbotBossCannonPosB)
            totalDisplacement = endPt - startPt
            self.notify.debug('totalDisplacement=%s' % totalDisplacement)
            numToons = len(self.involvedToons)
            stepDisplacement = totalDisplacement / (numToons + 1)
            for index in range(numToons):
                newPos = stepDisplacement * (index + 1)
                self.notify.debug('curDisplacement = %s' % newPos)
                newPos += startPt
                self.notify.debug('newPos = %s' % newPos)
                cannon = DistributedLawbotCannonAI.DistributedLawbotCannonAI(self.air, self, index, newPos[0], newPos[1], newPos[2], -90, 0, 0)
                cannon.generateWithRequired(self.zoneId)
                self.cannons.append(cannon)

        return

    def __makeChairs(self):
        if self.chairs == None:
            self.chairs = []
            for index in range(12):
                chair = DistributedLawbotChairAI.DistributedLawbotChairAI(self.air, self, index)
                chair.generateWithRequired(self.zoneId)
                self.chairs.append(chair)

        return

    def __makeBattleTwoObjects(self):
        self.__makeCannons()
        self.__makeChairs()

    def __deleteCannons(self):
        if self.cannons != None:
            for cannon in self.cannons:
                cannon.requestDelete()

            self.cannons = None
        return

    def __deleteChairs(self):
        if self.chairs != None:
            for chair in self.chairs:
                chair.requestDelete()

            self.chairs = None
        return

    def __stopChairs(self):
        if self.chairs != None:
            for chair in self.chairs:
                chair.stopCogs()

        return

    def __deleteBattleTwoObjects(self):
        self.__deleteCannons()
        self.__deleteChairs()

    def getCannonBallsLeft(self, avId):
        if avId in self.cannonBallsLeft:
            return self.cannonBallsLeft[avId]
        else:
            self.notify.warning('getCannonBalsLeft invalid avId: %d' % avId)
            return 0

    def decrementCannonBallsLeft(self, avId):
        if avId in self.cannonBallsLeft:
            self.cannonBallsLeft[avId] -= 1
            if self.cannonBallsLeft[avId] < 0:
                self.notify.warning('decrementCannonBallsLeft <0 cannonballs for %d' % avId)
                self.cannonBallsLeft[avId] = 0
        else:
            self.notify.warning('decrementCannonBallsLeft invalid avId: %d' % avId)

    def makeBattleTwoBattles(self):
        self.postBattleState = 'RollToBattleThree'
        if self.useCannons:
            self.__makeBattleTwoObjects()
        else:
            self.initializeBattles(2, ToontownGlobals.LawbotBossBattleTwoPosHpr)

    def enterBattleTwo(self):
        if self.useCannons:
            self.cannonBallsLeft = {}
            for toonId in self.involvedToons:
                self.cannonBallsLeft[toonId] = ToontownGlobals.LawbotBossCannonBallMax

            for chair in self.chairs:
                chair.requestEmptyJuror()

            self.barrier = self.beginBarrier('BattleTwo', self.involvedToons, ToontownGlobals.LawbotBossJuryBoxMoveTime + 1, self.__doneBattleTwo)
        if not self.useCannons:
            if self.battleA:
                self.battleA.startBattle(self.toonsA, self.suitsA)
            if self.battleB:
                self.battleB.startBattle(self.toonsB, self.suitsB)

    def __doneBattleTwo(self, avIds):
        if self.useCannons:
            self.b_setState('PrepareBattleThree')
        else:
            self.b_setState('RollToBattleThree')

    def exitBattleTwo(self):
        self.resetBattles()
        self.numToonJurorsSeated = 0
        for chair in self.chairs:
            self.notify.debug('chair.state==%s' % chair.state)
            if chair.state == 'ToonJuror':
                self.numToonJurorsSeated += 1

        self.notify.debug('numToonJurorsSeated=%d' % self.numToonJurorsSeated)
        self.air.writeServerEvent('jurorsSeated', self.doId, '%s|%s|%s' % (self.dept, self.involvedToons, self.numToonJurorsSeated))
        self.__deleteCannons()
        self.__stopChairs()

    def enterRollToBattleThree(self):
        self.divideToons()
        self.barrier = self.beginBarrier('RollToBattleThree', self.involvedToons, 20, self.__doneRollToBattleThree)

    def __doneRollToBattleThree(self, avIds):
        self.b_setState('PrepareBattleThree')

    def exitRollToBattleThree(self):
        self.ignoreBarrier(self.barrier)

    def enterPrepareBattleThree(self):
        self.calcAndSetBattleDifficulty()
        self.barrier = self.beginBarrier('PrepareBattleThree', self.involvedToons, 45, self.__donePrepareBattleThree)

    def __donePrepareBattleThree(self, avIds):
        self.b_setState('BattleThree')

    def exitPrepareBattleThree(self):
        self.ignoreBarrier(self.barrier)

    def enterBattleThree(self):
        self.battleThreeTimeStarted = globalClock.getFrameTime()
        self.calcAndSetBattleDifficulty()
        self.calculateWeightPerToon()
        diffSettings = ToontownGlobals.LawbotBossDifficultySettings[self.battleDifficulty]
        self.ammoCount = diffSettings[0]
        self.numGavels = diffSettings[1]
        if self.numGavels >= len(ToontownGlobals.LawbotBossGavelPosHprs):
            self.numGavels = len(ToontownGlobals.LawbotBossGavelPosHprs)
        self.numLawyers = diffSettings[2]
        if self.numLawyers >= len(ToontownGlobals.LawbotBossLawyerPosHprs):
            self.numLawyers = len(ToontownGlobals.LawbotBossLawyerPosHprs)
        self.toonupValue = diffSettings[3]
        self.notify.debug('diffLevel=%d ammoCount=%d gavels=%d lawyers = %d, toonup=%d' % (self.battleDifficulty, self.ammoCount, self.numGavels, self.numLawyers, self.toonupValue))
        self.air.writeServerEvent('lawbotBossSettings', self.doId, '%s|%s|%s|%s|%s|%s' % (self.dept, self.battleDifficulty, self.ammoCount, self.numGavels, self.numLawyers, self.toonupValue))
        self.__makeBattleThreeObjects()
        self.__makeLawyers()
        self.numPies = self.ammoCount
        self.resetBattles()
        self.setPieType()
        jurorsOver = self.numToonJurorsSeated - ToontownGlobals.LawbotBossJurorsForBalancedScale
        dmgAdjust = jurorsOver * ToontownGlobals.LawbotBossDamagePerJuror
        self.b_setBossDamage(ToontownGlobals.LawbotBossInitialDamage + dmgAdjust, 0, 0)
        if simbase.config.GetBool('lawbot-boss-cheat', 0):
            self.b_setBossDamage(ToontownGlobals.LawbotBossMaxDamage - 1, 0, 0)
        self.battleThreeStart = globalClock.getFrameTime()
        for toonId in self.involvedToons:
            toon = simbase.air.doId2do.get(toonId)
            if toon:
                toon.__touchedCage = 0

        for aGavel in self.gavels:
            aGavel.turnOn()

        self.waitForNextAttack(5)
        self.notify.debug('battleDifficulty = %d' % self.battleDifficulty)
        self.numToonsAtStart = len(self.involvedToons)

    def getToonDifficulty(self):
        highestCogSuitLevel = 0
        totalCogSuitLevels = 0.0
        totalNumToons = 0.0
        for toonId in self.involvedToons:
            toon = simbase.air.doId2do.get(toonId)
            if toon:
                toonLevel = toon.getNumPromotions(self.dept)
                totalCogSuitLevels += toonLevel
                totalNumToons += 1
                if toonLevel > highestCogSuitLevel:
                    highestCogSuitLevel = toonLevel

        if not totalNumToons:
            totalNumToons = 1.0
        averageLevel = totalCogSuitLevels / totalNumToons
        self.notify.debug('toons average level = %f, highest level = %d' % (averageLevel, highestCogSuitLevel))
        retval = min(averageLevel, self.maxToonLevels)
        return retval

    def __saySomething(self, task=None):
        index = None
        avId = 0
        if len(self.involvedToons) == 0:
            return
        avId = random.choice(self.involvedToons)
        toon = simbase.air.doId2do.get(avId)
        if toon.__touchedCage:
            if self.cagedToonDialogIndex <= TTLocalizer.CagedToonBattleThreeMaxAdvice:
                index = self.cagedToonDialogIndex
                self.cagedToonDialogIndex += 1
            elif random.random() < 0.2:
                index = random.randrange(100, TTLocalizer.CagedToonBattleThreeMaxAdvice + 1)
        else:
            index = random.randrange(20, TTLocalizer.CagedToonBattleThreeMaxTouchCage + 1)
        if index:
            self.d_cagedToonBattleThree(index, avId)
        self.__saySomethingLater()
        return

    def __saySomethingLater(self, delayTime=15):
        taskName = self.uniqueName('CagedToonSaySomething')
        taskMgr.remove(taskName)
        taskMgr.doMethodLater(delayTime, self.__saySomething, taskName)

    def __goodJump(self, avId):
        currState = self.getCurrentOrNextState()
        if currState != 'BattleThree':
            return
        index = random.randrange(10, TTLocalizer.CagedToonBattleThreeMaxGivePies + 1)
        self.d_cagedToonBattleThree(index, avId)
        self.__saySomethingLater()

    def __makeBattleThreeObjects(self):
        if self.gavels == None:
            self.gavels = []
            for index in range(self.numGavels):
                gavel = DistributedLawbotBossGavelAI.DistributedLawbotBossGavelAI(self.air, self, index)
                gavel.generateWithRequired(self.zoneId)
                self.gavels.append(gavel)

        return

    def __deleteBattleThreeObjects(self):
        if self.gavels != None:
            for gavel in self.gavels:
                gavel.request('Off')
                gavel.requestDelete()

            self.gavels = None
        return

    def doBattleThreeInfo(self):
        didTheyWin = 0
        if self.bossDamage == ToontownGlobals.LawbotBossMaxDamage:
            didTheyWin = 1
        self.battleThreeTimeInMin = globalClock.getFrameTime() - self.battleThreeTimeStarted
        self.battleThreeTimeInMin /= 60.0
        self.numToonsAtEnd = 0
        toonHps = []
        for toonId in self.involvedToons:
            toon = simbase.air.doId2do.get(toonId)
            if toon:
                self.numToonsAtEnd += 1
                toonHps.append(toon.hp)

        self.air.writeServerEvent('b3Info', self.doId, '%d|%.2f|%d|%d|%d|%d|%d|%d|%d|%d|%d|%d|%s|%s' % (didTheyWin, self.battleThreeTimeInMin, self.numToonsAtStart, self.numToonsAtEnd, self.numToonJurorsSeated, self.battleDifficulty, self.ammoCount, self.numGavels, self.numLawyers, self.toonupValue, self.numBonusStates, self.numAreaAttacks, toonHps, self.weightPerToon))

    def exitBattleThree(self):
        self.doBattleThreeInfo()
        self.stopAttacks()
        self.stopStrafes()
        taskName = self.uniqueName('CagedToonSaySomething')
        taskMgr.remove(taskName)
        self.__resetLawyers()
        self.__deleteBattleThreeObjects()

    def enterNearVictory(self):
        self.resetBattles()

    def exitNearVictory(self):
        pass

    def enterVictory(self):
        self.resetBattles()
        self.suitsKilled.append({'type': None, 'level': None, 'track': self.dna.dept, 'isSkelecog': 0, 'isForeman': 0, 'isVP': 1, 'isCFO': 0, 'isSupervisor': 0, 'isVirtual': 0, 'activeToons': self.involvedToons[:]})
        self.barrier = self.beginBarrier('Victory', self.involvedToons, 30, self.__doneVictory)
        return

    def __doneVictory(self, avIds):
        self.d_setBattleExperience()
        self.b_setState('Reward')
        BattleExperienceAI.assignRewards(self.involvedToons, self.toonSkillPtsGained, self.suitsKilled, ToontownGlobals.dept2cogHQ(self.dept), self.helpfulToons)
        preferredDept = random.randrange(len(SuitDNA.suitDepts))
        typeWeights = ['single'] * 70 + ['building'] * 27 + ['invasion'] * 3
        preferredSummonType = random.choice(typeWeights)
        for toonId in self.involvedToons:
            toon = self.air.doId2do.get(toonId)
            if toon:
                self.giveCogSummonReward(toon, preferredDept, preferredSummonType)
                toon.b_promote(self.deptIndex)

    def giveCogSummonReward(self, toon, prefDeptIndex, prefSummonType):
        cogLevel = int(self.toonLevels / self.maxToonLevels * SuitDNA.suitsPerDept)
        cogLevel = min(cogLevel, SuitDNA.suitsPerDept - 1)
        deptIndex = prefDeptIndex
        summonType = prefSummonType
        hasSummon = toon.hasParticularCogSummons(prefDeptIndex, cogLevel, prefSummonType)
        if hasSummon:
            self.notify.debug('trying to find another reward')
            if not toon.hasParticularCogSummons(prefDeptIndex, cogLevel, 'single'):
                summonType = 'single'
            elif not toon.hasParticularCogSummons(prefDeptIndex, cogLevel, 'building'):
                summonType = 'building'
            elif not toon.hasParticularCogSummons(prefDeptIndex, cogLevel, 'invasion'):
                summonType = 'invasion'
            else:
                foundOne = False
                for curDeptIndex in range(len(SuitDNA.suitDepts)):
                    if not toon.hasParticularCogSummons(curDeptIndex, cogLevel, prefSummonType):
                        deptIndex = curDeptIndex
                        foundOne = True
                        break
                    elif not toon.hasParticularCogSummons(curDeptIndex, cogLevel, 'single'):
                        deptIndex = curDeptIndex
                        summonType = 'single'
                        foundOne = True
                        break
                    elif not toon.hasParticularCogSummons(curDeptIndex, cogLevel, 'building'):
                        deptIndex = curDeptIndex
                        summonType = 'building'
                        foundOne = True
                        break
                    elif not toon.hasParticularCogSummons(curDeptIndex, cogLevel, 'invasion'):
                        summonType = 'invasion'
                        deptIndex = curDeptIndex
                        foundOne = True
                        break

                possibleCogLevel = list(range(SuitDNA.suitsPerDept))
                possibleDeptIndex = list(range(len(SuitDNA.suitDepts)))
                possibleSummonType = ['single', 'building', 'invasion']
                typeWeights = [
                 'single'] * 70 + ['building'] * 27 + ['invasion'] * 3
                if not foundOne:
                    for i in range(5):
                        randomCogLevel = random.choice(possibleCogLevel)
                        randomSummonType = random.choice(typeWeights)
                        randomDeptIndex = random.choice(possibleDeptIndex)
                        if not toon.hasParticularCogSummons(randomDeptIndex, randomCogLevel, randomSummonType):
                            foundOne = True
                            cogLevel = randomCogLevel
                            summonType = randomSummonType
                            deptIndex = randomDeptIndex
                            break

                for curType in possibleSummonType:
                    if foundOne:
                        break
                    for curCogLevel in possibleCogLevel:
                        if foundOne:
                            break
                        for curDeptIndex in possibleDeptIndex:
                            if foundOne:
                                break
                            if not toon.hasParticularCogSummons(curDeptIndex, curCogLevel, curType):
                                foundOne = True
                                cogLevel = curCogLevel
                                summonType = curType
                                deptIndex = curDeptIndex

                if not foundOne:
                    cogLevel = None
                    summonType = None
                    deptIndex = None
        toon.assignNewCogSummons(cogLevel, summonType, deptIndex)
        return

    def exitVictory(self):
        self.takeAwayPies()

    def enterDefeat(self):
        self.resetBattles()
        self.barrier = self.beginBarrier('Defeat', self.involvedToons, 10, self.__doneDefeat)

    def __doneDefeat(self, avIds):
        for toonId in self.involvedToons:
            toon = self.air.doId2do.get(toonId)
            if toon:
                toon.b_setHp(0)

    def exitDefeat(self):
        self.takeAwayPies()

    def enterFrolic(self):
        DistributedBossCogAI.DistributedBossCogAI.enterFrolic(self)
        self.b_setBossDamage(0, 0, 0)

    def setPieType(self):
        for toonId in self.involvedToons:
            toon = simbase.air.doId2do.get(toonId)
            if toon:
                toon.d_setPieType(ToontownBattleGlobals.MAX_TRACK_INDEX + 1)

    def takeAwayPies(self):
        for toonId in self.involvedToons:
            toon = simbase.air.doId2do.get(toonId)
            if toon:
                toon.b_setNumPies(0)

    def __recordHit(self):
        now = globalClock.getFrameTime()
        self.hitCount += 1
        if self.hitCount < self.limitHitCount or self.bossDamage < self.hitCountDamage:
            return

    def __resetLawyers(self):
        for suit in self.lawyers:
            suit.requestDelete()

        self.lawyers = []

    def __makeLawyers(self):
        self.__resetLawyers()
        lawCogChoices = [
         'b', 'dt', 'ac', 'bs', 'sd', 'le', 'bw']
        for i in range(self.numLawyers):
            suit = DistributedLawbotBossSuitAI.DistributedLawbotBossSuitAI(self.air, None)
            suit.dna = SuitDNA.SuitDNA()
            lawCog = random.choice(lawCogChoices)
            suit.dna.newSuit(lawCog)
            suit.setPosHpr(*ToontownGlobals.LawbotBossLawyerPosHprs[i])
            suit.setBoss(self)
            suit.generateWithRequired(self.zoneId)
            self.lawyers.append(suit)

        self.__sendLawyerIds()
        return

    def hitChair(self, chairIndex, npcToonIndex):
        avId = self.air.getAvatarIdFromSender()
        if not self.validate(avId, avId in self.involvedToons, 'hitChair from unknown avatar'):
            return
        if not self.chairs:
            return
        if chairIndex < 0 or chairIndex >= len(self.chairs):
            self.notify.warning('invalid chairIndex = %d' % chairIndex)
            return
        if not self.state == 'BattleTwo':
            return
        self.chairs[chairIndex].b_setToonJurorIndex(npcToonIndex)
        self.chairs[chairIndex].requestToonJuror()

    def clearBonus(self, taskName):
        if self and hasattr(self, 'bonusState'):
            self.bonusState = False

    def startBonusState(self):
        self.notify.debug('startBonusState')
        self.bonusTimeStarted = globalClock.getFrameTime()
        self.bonusState = True
        self.numBonusStates += 1
        for toonId in self.involvedToons:
            toon = self.air.doId2do.get(toonId)
            if toon:
                self.healToon(toon, ToontownGlobals.LawbotBossBonusToonup)

        taskMgr.doMethodLater(ToontownGlobals.LawbotBossBonusDuration, self.clearBonus, self.uniqueName('clearBonus'))
        self.sendUpdate('enteredBonusState', [])

    def areAllLawyersStunned(self):
        for lawyer in self.lawyers:
            if not lawyer.stunned:
                return False

        return True

    def checkForBonusState(self):
        if self.bonusState:
            return
        if not self.areAllLawyersStunned():
            return
        curTime = globalClock.getFrameTime()
        delta = curTime - self.bonusTimeStarted
        if ToontownGlobals.LawbotBossBonusWaitTime < delta:
            self.startBonusState()

    def toonEnteredCannon(self, toonId, cannonIndex):
        self.cannonIndexPerToon[toonId] = cannonIndex

    def numJurorsSeatedByCannon(self, cannonIndex):
        retVal = 0
        for chair in self.chairs:
            if chair.state == 'ToonJuror':
                if chair.toonJurorIndex == cannonIndex:
                    retVal += 1

        return retVal

    def calculateWeightPerToon(self):
        for toonId in self.involvedToons:
            defaultWeight = 1
            bonusWeight = 0
            cannonIndex = self.cannonIndexPerToon.get(toonId)
            if not cannonIndex == None:
                diffSettings = ToontownGlobals.LawbotBossDifficultySettings[self.battleDifficulty]
                if diffSettings[4]:
                    bonusWeight = self.numJurorsSeatedByCannon(cannonIndex) - diffSettings[5]
                    if bonusWeight < 0:
                        bonusWeight = 0
            newWeight = defaultWeight + bonusWeight
            self.weightPerToon[toonId] = newWeight
            self.notify.debug('toon %d has weight of %d' % (toonId, newWeight))

        return

    def b_setBattleDifficulty(self, batDiff):
        self.setBattleDifficulty(batDiff)
        self.d_setBattleDifficulty(batDiff)

    def setBattleDifficulty(self, batDiff):
        self.battleDifficulty = batDiff

    def d_setBattleDifficulty(self, batDiff):
        self.sendUpdate('setBattleDifficulty', [batDiff])

    def calcAndSetBattleDifficulty(self):
        self.toonLevels = self.getToonDifficulty()
        numDifficultyLevels = len(ToontownGlobals.LawbotBossDifficultySettings)
        battleDifficulty = int(self.toonLevels / self.maxToonLevels * numDifficultyLevels)
        if battleDifficulty >= numDifficultyLevels:
            battleDifficulty = numDifficultyLevels - 1
        self.b_setBattleDifficulty(battleDifficulty)
