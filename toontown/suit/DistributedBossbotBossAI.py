import random, math
from pandac.PandaModules import Point3
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import FSM
from direct.interval.IntervalGlobal import LerpPosInterval
from toontown.coghq import DistributedFoodBeltAI
from toontown.coghq import DistributedBanquetTableAI
from toontown.coghq import DistributedGolfSpotAI
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import ToontownBattleGlobals
from toontown.suit import DistributedBossCogAI
from toontown.suit import DistributedSuitAI
from toontown.suit import SuitDNA
from toontown.building import SuitBuildingGlobals
from toontown.battle import DistributedBattleWaitersAI
from toontown.battle import DistributedBattleDinersAI
from toontown.battle import BattleExperienceAI
from direct.distributed.ClockDelta import globalClockDelta

class DistributedBossbotBossAI(DistributedBossCogAI.DistributedBossCogAI, FSM.FSM):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedBossbotBossAI')
    maxToonLevels = 77
    toonUpLevels = [1, 2, 3, 4]

    def __init__(self, air):
        DistributedBossCogAI.DistributedBossCogAI.__init__(self, air, 'c')
        FSM.FSM.__init__(self, 'DistributedBossbotBossAI')
        self.battleOneBattlesMade = False
        self.battleThreeBattlesMade = False
        self.battleFourSetup = False
        self.foodBelts = []
        self.numTables = 1
        self.numDinersPerTable = 3
        self.tables = []
        self.numGolfSpots = 4
        self.golfSpots = []
        self.toonFoodStatus = {}
        self.bossMaxDamage = ToontownGlobals.BossbotBossMaxDamage
        self.threatDict = {}
        self.keyStates.append('BattleFour')
        self.battleFourStart = 0
        self.battleDifficulty = 0
        self.movingToTable = False
        self.tableDest = -1
        self.curTable = -1
        self.speedDamage = 0
        self.maxSpeedDamage = ToontownGlobals.BossbotMaxSpeedDamage
        self.speedRecoverRate = ToontownGlobals.BossbotSpeedRecoverRate
        self.speedRecoverStartTime = 0
        self.battleFourTimeStarted = 0
        self.numDinersExploded = 0
        self.numMoveAttacks = 0
        self.numGolfAttacks = 0
        self.numGearAttacks = 0
        self.numGolfAreaAttacks = 0
        self.numToonupGranted = 0
        self.totalLaffHealed = 0
        self.toonupsGranted = []
        self.doneOvertimeOneAttack = False
        self.doneOvertimeTwoAttack = False
        self.overtimeOneTime = simbase.air.config.GetInt('overtime-one-time', 1200)
        self.battleFourDuration = simbase.air.config.GetInt('battle-four-duration', 1800)
        self.overtimeOneStart = float(self.overtimeOneTime) / self.battleFourDuration
        self.moveAttackAllowed = True

    def delete(self):
        self.notify.debug('DistributedBossbotBossAI.delete')
        self.deleteBanquetTables()
        self.deleteFoodBelts()
        self.deleteGolfSpots()
        return DistributedBossCogAI.DistributedBossCogAI.delete(self)

    def enterElevator(self):
        DistributedBossCogAI.DistributedBossCogAI.enterElevator(self)
        self.makeBattleOneBattles()

    def enterIntroduction(self):
        self.arenaSide = None
        self.makeBattleOneBattles()
        self.barrier = self.beginBarrier('Introduction', self.involvedToons, 45, self.doneIntroduction)
        return

    def makeBattleOneBattles(self):
        if not self.battleOneBattlesMade:
            self.postBattleState = 'PrepareBattleTwo'
            self.initializeBattles(1, ToontownGlobals.BossbotBossBattleOnePosHpr)
            self.battleOneBattlesMade = True

    def getHoodId(self):
        return ToontownGlobals.LawbotHQ

    def generateSuits(self, battleNumber):
        if battleNumber == 1:
            weakenedValue = (
             (1, 1), (2, 2), (2, 2), (1, 1), (1, 1, 1, 1, 1))
            listVersion = list(SuitBuildingGlobals.SuitBuildingInfo)
            if simbase.config.GetBool('bossbot-boss-cheat', 0):
                listVersion[14] = weakenedValue
                SuitBuildingGlobals.SuitBuildingInfo = tuple(listVersion)
            retval = self.invokeSuitPlanner(14, 0)
            return retval
        else:
            suits = self.generateDinerSuits()
            return suits

    def invokeSuitPlanner(self, buildingCode, skelecog):
        suits = DistributedBossCogAI.DistributedBossCogAI.invokeSuitPlanner(self, buildingCode, skelecog)
        activeSuits = suits['activeSuits'][:]
        reserveSuits = suits['reserveSuits'][:]
        if len(activeSuits) + len(reserveSuits) >= 4:
            while len(activeSuits) < 4:
                activeSuits.append(reserveSuits.pop()[0])

        retval = {'activeSuits': activeSuits, 'reserveSuits': reserveSuits}
        return retval

    def makeBattle(self, bossCogPosHpr, battlePosHpr, roundCallback, finishCallback, battleNumber, battleSide):
        if battleNumber == 1:
            battle = DistributedBattleWaitersAI.DistributedBattleWaitersAI(self.air, self, roundCallback, finishCallback, battleSide)
        else:
            battle = DistributedBattleDinersAI.DistributedBattleDinersAI(self.air, self, roundCallback, finishCallback, battleSide)
        self.setBattlePos(battle, bossCogPosHpr, battlePosHpr)
        battle.suitsKilled = self.suitsKilled
        battle.battleCalc.toonSkillPtsGained = self.toonSkillPtsGained
        battle.toonExp = self.toonExp
        battle.toonOrigQuests = self.toonOrigQuests
        battle.toonItems = self.toonItems
        battle.toonOrigMerits = self.toonOrigMerits
        battle.toonMerits = self.toonMerits
        battle.toonParts = self.toonParts
        battle.helpfulToons = self.helpfulToons
        mult = ToontownBattleGlobals.getBossBattleCreditMultiplier(battleNumber)
        battle.battleCalc.setSkillCreditMultiplier(mult)
        activeSuits = self.activeSuitsA
        if battleSide:
            activeSuits = self.activeSuitsB
        for suit in activeSuits:
            battle.addSuit(suit)

        battle.generateWithRequired(self.zoneId)
        return battle

    def initializeBattles(self, battleNumber, bossCogPosHpr):
        self.resetBattles()
        if not self.involvedToons:
            self.notify.warning('initializeBattles: no toons!')
            return
        self.battleNumber = battleNumber
        suitHandles = self.generateSuits(battleNumber)
        self.suitsA = suitHandles['activeSuits']
        self.activeSuitsA = self.suitsA[:]
        self.reserveSuits = suitHandles['reserveSuits']
        if battleNumber == 3:
            if self.toonsB:
                movedSuit = self.suitsA.pop()
                self.suitsB = [movedSuit]
                self.activeSuitsB = [movedSuit]
                self.activeSuitsA.remove(movedSuit)
            else:
                self.suitsB = []
                self.activeSuitsB = []
        else:
            suitHandles = self.generateSuits(battleNumber)
            self.suitsB = suitHandles['activeSuits']
            self.activeSuitsB = self.suitsB[:]
            self.reserveSuits += suitHandles['reserveSuits']
        if self.toonsA:
            if battleNumber == 1:
                self.battleA = self.makeBattle(bossCogPosHpr, ToontownGlobals.WaiterBattleAPosHpr, self.handleRoundADone, self.handleBattleADone, battleNumber, 0)
                self.battleAId = self.battleA.doId
            else:
                self.battleA = self.makeBattle(bossCogPosHpr, ToontownGlobals.DinerBattleAPosHpr, self.handleRoundADone, self.handleBattleADone, battleNumber, 0)
                self.battleAId = self.battleA.doId
        else:
            self.moveSuits(self.activeSuitsA)
            self.suitsA = []
            self.activeSuitsA = []
            if self.arenaSide == None:
                self.b_setArenaSide(0)
        if self.toonsB:
            if battleNumber == 1:
                self.battleB = self.makeBattle(bossCogPosHpr, ToontownGlobals.WaiterBattleBPosHpr, self.handleRoundBDone, self.handleBattleBDone, battleNumber, 1)
                self.battleBId = self.battleB.doId
            else:
                self.battleB = self.makeBattle(bossCogPosHpr, ToontownGlobals.DinerBattleBPosHpr, self.handleRoundBDone, self.handleBattleBDone, battleNumber, 1)
                self.battleBId = self.battleB.doId
        else:
            self.moveSuits(self.activeSuitsB)
            self.suitsB = []
            self.activeSuitsB = []
            if self.arenaSide == None:
                self.b_setArenaSide(1)
        self.sendBattleIds()
        return

    def enterPrepareBattleTwo(self):
        self.barrier = self.beginBarrier('PrepareBattleTwo', self.involvedToons, 45, self.__donePrepareBattleTwo)
        self.createFoodBelts()
        self.createBanquetTables()

    def __donePrepareBattleTwo(self, avIds):
        self.b_setState('BattleTwo')

    def exitPrepareBattleTwo(self):
        self.ignoreBarrier(self.barrier)

    def createFoodBelts(self):
        if self.foodBelts:
            return
        for i in range(2):
            newBelt = DistributedFoodBeltAI.DistributedFoodBeltAI(self.air, self, i)
            self.foodBelts.append(newBelt)
            newBelt.generateWithRequired(self.zoneId)

    def deleteFoodBelts(self):
        for belt in self.foodBelts:
            belt.requestDelete()

        self.foodBelts = []

    def createBanquetTables(self):
        if self.tables:
            return
        self.calcAndSetBattleDifficulty()
        diffInfo = ToontownGlobals.BossbotBossDifficultySettings[self.battleDifficulty]
        self.diffInfo = diffInfo
        self.numTables = diffInfo[0]
        self.numDinersPerTable = diffInfo[1]
        dinerLevel = diffInfo[2]
        for i in range(self.numTables):
            newTable = DistributedBanquetTableAI.DistributedBanquetTableAI(self.air, self, i, self.numDinersPerTable, dinerLevel)
            self.tables.append(newTable)
            newTable.generateWithRequired(self.zoneId)

    def deleteBanquetTables(self):
        for table in self.tables:
            table.requestDelete()

        self.tables = []

    def enterBattleTwo(self):
        self.resetBattles()
        self.createFoodBelts()
        self.createBanquetTables()
        for belt in self.foodBelts:
            belt.turnOn()

        for table in self.tables:
            table.turnOn()

        self.barrier = self.beginBarrier('BattleTwo', self.involvedToons, ToontownGlobals.BossbotBossServingDuration + 1, self.__doneBattleTwo)

    def exitBattleTwo(self):
        self.ignoreBarrier(self.barrier)
        for table in self.tables:
            table.goInactive()

        for belt in self.foodBelts:
            belt.goInactive()

    def __doneBattleTwo(self, avIds):
        self.b_setState('PrepareBattleThree')

    def requestGetFood(self, beltIndex, foodIndex, foodNum):
        grantRequest = False
        avId = self.air.getAvatarIdFromSender()
        if self.state != 'BattleTwo':
            grantRequest = False
        else:
            if (
             beltIndex, foodNum) not in list(self.toonFoodStatus.values()):
                if avId not in self.toonFoodStatus:
                    grantRequest = True
                elif self.toonFoodStatus[avId] == None:
                    grantRequest = True
        if grantRequest:
            self.toonFoodStatus[avId] = (
             beltIndex, foodNum)
            self.sendUpdate('toonGotFood', [avId, beltIndex, foodIndex, foodNum])
        return

    def requestServeFood(self, tableIndex, chairIndex):
        grantRequest = False
        avId = self.air.getAvatarIdFromSender()
        if self.state != 'BattleTwo':
            grantRequest = False
        else:
            if tableIndex < len(self.tables):
                table = self.tables[tableIndex]
                dinerStatus = table.getDinerStatus(chairIndex)
                if dinerStatus in (table.HUNGRY, table.ANGRY):
                    if self.toonFoodStatus[avId]:
                        grantRequest = True
        if grantRequest:
            self.toonFoodStatus[avId] = None
            table.foodServed(chairIndex)
            self.sendUpdate('toonServeFood', [avId, tableIndex, chairIndex])
        return

    def enterPrepareBattleThree(self):
        self.barrier = self.beginBarrier('PrepareBattleThree', self.involvedToons, ToontownGlobals.BossbotBossServingDuration + 1, self.__donePrepareBattleThree)
        self.divideToons()
        self.makeBattleThreeBattles()

    def exitPrepareBattleThree(self):
        self.ignoreBarrier(self.barrier)

    def __donePrepareBattleThree(self, avIds):
        self.b_setState('BattleThree')

    def makeBattleThreeBattles(self):
        if not self.battleThreeBattlesMade:
            if not self.tables:
                self.createBanquetTables()
                for table in self.tables:
                    table.turnOn()
                    table.goInactive()

            notDeadList = []
            for table in self.tables:
                tableInfo = table.getNotDeadInfo()
                notDeadList += tableInfo

            self.notDeadList = notDeadList
            self.postBattleState = 'PrepareBattleFour'
            self.initializeBattles(3, ToontownGlobals.BossbotBossBattleThreePosHpr)
            self.battleThreeBattlesMade = True

    def generateDinerSuits(self):
        diners = []
        for i in range(len(self.notDeadList)):
            if simbase.config.GetBool('bossbot-boss-cheat', 0):
                suit = self.__genSuitObject(self.zoneId, 2, 'c', 2, 0)
            else:
                info = self.notDeadList[i]
                suitType = info[2] - 4
                suitLevel = info[2]
                suit = self.__genSuitObject(self.zoneId, suitType, 'c', suitLevel, 1)
            diners.append((suit, 100))

        active = []
        for i in range(2):
            if simbase.config.GetBool('bossbot-boss-cheat', 0):
                suit = self.__genSuitObject(self.zoneId, 2, 'c', 2, 0)
            else:
                suitType = 8
                suitLevel = 12
                suit = self.__genSuitObject(self.zoneId, suitType, 'c', suitLevel, 1)
            active.append(suit)

        return {'activeSuits': active, 'reserveSuits': diners}

    def __genSuitObject(self, suitZone, suitType, bldgTrack, suitLevel, revives=0):
        newSuit = DistributedSuitAI.DistributedSuitAI(simbase.air, None)
        skel = self.__setupSuitInfo(newSuit, bldgTrack, suitLevel, suitType)
        if skel:
            newSuit.setSkelecog(1)
        newSuit.setSkeleRevives(revives)
        newSuit.generateWithRequired(suitZone)
        newSuit.node().setName('suit-%s' % newSuit.doId)
        return newSuit

    def __setupSuitInfo(self, suit, bldgTrack, suitLevel, suitType):
        dna = SuitDNA.SuitDNA()
        dna.newSuitRandom(suitType, bldgTrack)
        suit.dna = dna
        self.notify.debug('Creating suit type ' + suit.dna.name + ' of level ' + str(suitLevel) + ' from type ' + str(suitType) + ' and track ' + str(bldgTrack))
        suit.setLevel(suitLevel)
        return False

    def enterBattleThree(self):
        self.makeBattleThreeBattles()
        self.notify.debug('self.battleA = %s' % self.battleA)
        if self.battleA:
            self.battleA.startBattle(self.toonsA, self.suitsA)
        if self.battleB:
            self.battleB.startBattle(self.toonsB, self.suitsB)

    def exitBattleThree(self):
        self.resetBattles()

    def enterPrepareBattleFour(self):
        self.resetBattles()
        self.setupBattleFourObjects()
        self.barrier = self.beginBarrier('PrepareBattleFour', self.involvedToons, 45, self.__donePrepareBattleFour)

    def __donePrepareBattleFour(self, avIds):
        self.b_setState('BattleFour')

    def exitPrepareBattleFour(self):
        self.ignoreBarrier(self.barrier)

    def enterBattleFour(self):
        self.battleFourTimeStarted = globalClock.getFrameTime()
        self.numToonsAtStart = len(self.involvedToons)
        self.resetBattles()
        self.setupBattleFourObjects()
        self.battleFourStart = globalClock.getFrameTime()
        self.waitForNextAttack(5)

    def exitBattleFour(self):
        self.recordCeoInfo()
        for belt in self.foodBelts:
            belt.goInactive()

    def recordCeoInfo(self):
        didTheyWin = 0
        if self.bossDamage == self.bossMaxDamage:
            didTheyWin = 1
        self.battleFourTimeInMin = globalClock.getFrameTime() - self.battleFourTimeStarted
        self.battleFourTimeInMin /= 60.0
        self.numToonsAtEnd = 0
        toonHps = []
        for toonId in self.involvedToons:
            toon = simbase.air.doId2do.get(toonId)
            if toon:
                self.numToonsAtEnd += 1
                toonHps.append(toon.hp)

        self.air.writeServerEvent('ceoInfo', self.doId, '%d|%.2f|%d|%d|%d|%d|%d|%d|%s|%s|%.1f|%d|%d|%d|%d|%d}%d|%s|' % (didTheyWin, self.battleFourTimeInMin, self.battleDifficulty, self.numToonsAtStart, self.numToonsAtEnd, self.numTables, self.numTables * self.numDinersPerTable, self.numDinersExploded, toonHps, self.involvedToons, self.speedDamage, self.numMoveAttacks, self.numGolfAttacks, self.numGearAttacks, self.numGolfAreaAttacks, self.numToonupGranted, self.totalLaffHealed, 'ceoBugfixes'))

    def setupBattleFourObjects(self):
        if self.battleFourSetup:
            return
        if not self.tables:
            self.createBanquetTables()
        for table in self.tables:
            table.goFree()

        if not self.golfSpots:
            self.createGolfSpots()
        self.createFoodBelts()
        for belt in self.foodBelts:
            belt.goToonup()

        self.battleFourSetup = True

    def hitBoss(self, bossDamage):
        avId = self.air.getAvatarIdFromSender()
        if not self.validate(avId, avId in self.involvedToons, 'DistributedBossbotBossAI.hitBoss from unknown avatar'):
            return
        self.validate(avId, bossDamage <= 3, 'invalid bossDamage %s' % bossDamage)
        if bossDamage < 1:
            return
        currState = self.getCurrentOrNextState()
        if currState != 'BattleFour':
            return
        bossDamage *= 2
        bossDamage = min(self.getBossDamage() + bossDamage, self.bossMaxDamage)
        self.b_setBossDamage(bossDamage, 0, 0)
        if self.bossDamage >= self.bossMaxDamage:
            self.b_setState('Victory')
        else:
            self.__recordHit(bossDamage)

    def __recordHit(self, bossDamage):
        now = globalClock.getFrameTime()
        self.hitCount += 1
        avId = self.air.getAvatarIdFromSender()
        self.addThreat(avId, bossDamage)

    def getBossDamage(self):
        return self.bossDamage

    def b_setBossDamage(self, bossDamage, recoverRate, recoverStartTime):
        self.d_setBossDamage(bossDamage, recoverRate, recoverStartTime)
        self.setBossDamage(bossDamage, recoverRate, recoverStartTime)

    def setBossDamage(self, bossDamage, recoverRate, recoverStartTime):
        self.bossDamage = bossDamage
        self.recoverRate = recoverRate
        self.recoverStartTime = recoverStartTime

    def d_setBossDamage(self, bossDamage, recoverRate, recoverStartTime):
        timestamp = globalClockDelta.localToNetworkTime(recoverStartTime)
        self.sendUpdate('setBossDamage', [bossDamage, recoverRate, timestamp])

    def getSpeedDamage(self):
        now = globalClock.getFrameTime()
        elapsed = now - self.speedRecoverStartTime
        self.notify.debug('elapsed=%s' % elapsed)
        floatSpeedDamage = max(self.speedDamage - self.speedRecoverRate * elapsed / 60.0, 0)
        self.notify.debug('floatSpeedDamage = %s' % floatSpeedDamage)
        return int(max(self.speedDamage - self.speedRecoverRate * elapsed / 60.0, 0))

    def getFloatSpeedDamage(self):
        now = globalClock.getFrameTime()
        elapsed = now - self.speedRecoverStartTime
        floatSpeedDamage = max(self.speedDamage - self.speedRecoverRate * elapsed / 60.0, 0)
        self.notify.debug('floatSpeedDamage = %s' % floatSpeedDamage)
        return max(self.speedDamage - self.speedRecoverRate * elapsed / 60.0, 0)

    def b_setSpeedDamage(self, speedDamage, recoverRate, recoverStartTime):
        self.d_setSpeedDamage(speedDamage, recoverRate, recoverStartTime)
        self.setSpeedDamage(speedDamage, recoverRate, recoverStartTime)

    def setSpeedDamage(self, speedDamage, recoverRate, recoverStartTime):
        self.speedDamage = speedDamage
        self.speedRecoverRate = recoverRate
        self.speedRecoverStartTime = recoverStartTime

    def d_setSpeedDamage(self, speedDamage, recoverRate, recoverStartTime):
        timestamp = globalClockDelta.localToNetworkTime(recoverStartTime)
        self.sendUpdate('setSpeedDamage', [speedDamage, recoverRate, timestamp])

    def createGolfSpots(self):
        if self.golfSpots:
            return
        for i in range(self.numGolfSpots):
            newGolfSpot = DistributedGolfSpotAI.DistributedGolfSpotAI(self.air, self, i)
            self.golfSpots.append(newGolfSpot)
            newGolfSpot.generateWithRequired(self.zoneId)
            newGolfSpot.forceFree()

    def deleteGolfSpots(self):
        for spot in self.golfSpots:
            spot.requestDelete()

        self.golfSpots = []

    def ballHitBoss(self, speedDamage):
        avId = self.air.getAvatarIdFromSender()
        if not self.validate(avId, avId in self.involvedToons, 'DistributedBossbotBossAI.ballHitBoss from unknown avatar'):
            return
        if speedDamage < 1:
            return
        currState = self.getCurrentOrNextState()
        if currState != 'BattleFour':
            return
        now = globalClock.getFrameTime()
        newDamage = self.getSpeedDamage() + speedDamage
        self.notify.debug('newDamage = %s' % newDamage)
        speedDamage = min(self.getFloatSpeedDamage() + speedDamage, self.maxSpeedDamage)
        self.b_setSpeedDamage(speedDamage, self.speedRecoverRate, now)
        self.addThreat(avId, 0.1)

    def enterVictory(self):
        self.resetBattles()
        for table in self.tables:
            table.turnOff()

        for golfSpot in self.golfSpots:
            golfSpot.turnOff()

        self.suitsKilled.append({'type': None, 'level': None, 'track': self.dna.dept, 'isSkelecog': 0, 'isForeman': 0, 'isVP': 1, 'isCFO': 0, 'isSupervisor': 0, 'isVirtual': 0, 'activeToons': self.involvedToons[:]})
        self.barrier = self.beginBarrier('Victory', self.involvedToons, 30, self.__doneVictory)
        return

    def __doneVictory(self, avIds):
        self.d_setBattleExperience()
        self.b_setState('Reward')
        BattleExperienceAI.assignRewards(self.involvedToons, self.toonSkillPtsGained, self.suitsKilled, ToontownGlobals.dept2cogHQ(self.dept), self.helpfulToons)
        for toonId in self.involvedToons:
            toon = self.air.doId2do.get(toonId)
            if toon:
                self.givePinkSlipReward(toon)
                toon.b_promote(self.deptIndex)

    def givePinkSlipReward(self, toon):
        self.notify.debug('TODO give pink slip to %s' % toon)
        toon.addPinkSlips(self.battleDifficulty + 1)

    def getThreat(self, toonId):
        if toonId in self.threatDict:
            return self.threatDict[toonId]
        else:
            return 0

    def addThreat(self, toonId, threat):
        if toonId in self.threatDict:
            self.threatDict[toonId] += threat
        else:
            self.threatDict[toonId] = threat

    def subtractThreat(self, toonId, threat):
        if toonId in self.threatDict:
            self.threatDict[toonId] -= threat
        else:
            self.threatDict[toonId] = 0
        if self.threatDict[toonId] < 0:
            self.threatDict[toonId] = 0

    def waitForNextAttack(self, delayTime):
        currState = self.getCurrentOrNextState()
        if currState == 'BattleFour':
            taskName = self.uniqueName('NextAttack')
            taskMgr.remove(taskName)
            taskMgr.doMethodLater(delayTime, self.doNextAttack, taskName)

    def doNextAttack(self, task):
        attackCode = -1
        optionalParam = None
        if self.movingToTable:
            self.waitForNextAttack(5)
        elif self.attackCode == ToontownGlobals.BossCogDizzyNow:
            attackCode = ToontownGlobals.BossCogRecoverDizzyAttack
        elif self.getBattleFourTime() > self.overtimeOneStart and not self.doneOvertimeOneAttack:
            attackCode = ToontownGlobals.BossCogOvertimeAttack
            self.doneOvertimeOneAttack = True
            optionalParam = 0
        elif self.getBattleFourTime() > 1.0 and not self.doneOvertimeTwoAttack:
            attackCode = ToontownGlobals.BossCogOvertimeAttack
            self.doneOvertimeTwoAttack = True
            optionalParam = 1
        else:
            attackCode = random.choice([ToontownGlobals.BossCogGolfAreaAttack,
             ToontownGlobals.BossCogDirectedAttack,
             ToontownGlobals.BossCogDirectedAttack,
             ToontownGlobals.BossCogDirectedAttack,
             ToontownGlobals.BossCogDirectedAttack])
        if attackCode == ToontownGlobals.BossCogAreaAttack:
            self.__doAreaAttack()
        if attackCode == ToontownGlobals.BossCogGolfAreaAttack:
            self.__doGolfAreaAttack()
        elif attackCode == ToontownGlobals.BossCogDirectedAttack:
            self.__doDirectedAttack()
        elif attackCode >= 0:
            self.b_setAttackCode(attackCode, optionalParam)
        return

    def progressValue(self, fromValue, toValue):
        t0 = float(self.bossDamage) / float(self.bossMaxDamage)
        elapsed = globalClock.getFrameTime() - self.battleFourStart
        t1 = elapsed / float(self.battleThreeDuration)
        t = max(t0, t1)
        progVal = fromValue + (toValue - fromValue) * min(t, 1)
        self.notify.debug('progVal=%s' % progVal)
        import pdb
        pdb.set_trace()
        return progVal

    def __doDirectedAttack(self):
        toonId = self.getMaxThreatToon()
        self.notify.debug('toonToAttack=%s' % toonId)
        unflattenedToons = self.getUnflattenedToons()
        attackTotallyRandomToon = random.random() < 0.1
        if unflattenedToons and (attackTotallyRandomToon or toonId == 0):
            toonId = random.choice(unflattenedToons)
        if toonId:
            toonThreat = self.getThreat(toonId)
            toonThreat *= 0.25
            threatToSubtract = max(toonThreat, 10)
            self.subtractThreat(toonId, threatToSubtract)
            if self.isToonRoaming(toonId):
                self.b_setAttackCode(ToontownGlobals.BossCogGolfAttack, toonId)
                self.numGolfAttacks += 1
            elif self.isToonOnTable(toonId):
                doesMoveAttack = simbase.air.config.GetBool('ceo-does-move-attack', 1)
                if doesMoveAttack:
                    chanceToShoot = 0.25
                else:
                    chanceToShoot = 1.0
                if not self.moveAttackAllowed:
                    self.notify.debug('moveAttack is not allowed, doing gearDirectedAttack')
                    chanceToShoot = 1.0
                if random.random() < chanceToShoot:
                    self.b_setAttackCode(ToontownGlobals.BossCogGearDirectedAttack, toonId)
                    self.numGearAttacks += 1
                else:
                    tableIndex = self.getToonTableIndex(toonId)
                    self.doMoveAttack(tableIndex)
            else:
                self.b_setAttackCode(ToontownGlobals.BossCogGolfAttack, toonId)
        else:
            uprightTables = self.getUprightTables()
            if uprightTables:
                tableToMoveTo = random.choice(uprightTables)
                self.doMoveAttack(tableToMoveTo)
            else:
                self.waitForNextAttack(4)

    def doMoveAttack(self, tableIndex):
        self.numMoveAttacks += 1
        self.movingToTable = True
        self.tableDest = tableIndex
        self.b_setAttackCode(ToontownGlobals.BossCogMoveAttack, tableIndex)

    def getUnflattenedToons(self):
        result = []
        uprightTables = self.getUprightTables()
        for toonId in self.involvedToons:
            toonTable = self.getToonTableIndex(toonId)
            if toonTable >= 0 and toonTable not in uprightTables:
                pass
            else:
                result.append(toonId)

        return result

    def getMaxThreatToon(self):
        returnedToonId = 0
        maxThreat = 0
        maxToons = []
        for toonId in self.threatDict:
            curThreat = self.threatDict[toonId]
            tableIndex = self.getToonTableIndex(toonId)
            if tableIndex > -1 and self.tables[tableIndex].state == 'Flat':
                pass
            elif curThreat > maxThreat:
                maxToons = [
                 toonId]
                maxThreat = curThreat
            elif curThreat == maxThreat:
                maxToons.append(toonId)

        if maxToons:
            returnedToonId = random.choice(maxToons)
        return returnedToonId

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

    def calcAndSetBattleDifficulty(self):
        self.toonLevels = self.getToonDifficulty()
        numDifficultyLevels = len(ToontownGlobals.BossbotBossDifficultySettings)
        battleDifficulty = int(self.toonLevels / self.maxToonLevels * numDifficultyLevels)
        if battleDifficulty >= numDifficultyLevels:
            battleDifficulty = numDifficultyLevels - 1
        self.b_setBattleDifficulty(battleDifficulty)

    def b_setBattleDifficulty(self, batDiff):
        self.setBattleDifficulty(batDiff)
        self.d_setBattleDifficulty(batDiff)

    def setBattleDifficulty(self, batDiff):
        self.battleDifficulty = batDiff

    def d_setBattleDifficulty(self, batDiff):
        self.sendUpdate('setBattleDifficulty', [batDiff])

    def getUprightTables(self):
        tableList = []
        for table in self.tables:
            if table.state != 'Flat':
                tableList.append(table.index)

        return tableList

    def getToonTableIndex(self, toonId):
        tableIndex = -1
        for table in self.tables:
            if table.avId == toonId:
                tableIndex = table.index
                break

        return tableIndex

    def getToonGolfSpotIndex(self, toonId):
        golfSpotIndex = -1
        for golfSpot in self.golfSpots:
            if golfSpot.avId == toonId:
                golfSpotIndex = golfSpot.index
                break

        return golfSpotIndex

    def isToonOnTable(self, toonId):
        result = self.getToonTableIndex(toonId) != -1
        return result

    def isToonOnGolfSpot(self, toonId):
        result = self.getToonGolfSpotIndex(toonId) != -1
        return result

    def isToonRoaming(self, toonId):
        result = not self.isToonOnTable(toonId) and not self.isToonOnGolfSpot(toonId)
        return result

    def reachedTable(self, tableIndex):
        if self.movingToTable and self.tableDest == tableIndex:
            self.movingToTable = False
            self.curTable = self.tableDest
            self.tableDest = -1

    def hitTable(self, tableIndex):
        self.notify.debug('hitTable tableIndex=%d' % tableIndex)
        if tableIndex < len(self.tables):
            table = self.tables[tableIndex]
            if table.state != 'Flat':
                table.goFlat()

    def awayFromTable(self, tableIndex):
        self.notify.debug('awayFromTable tableIndex=%d' % tableIndex)
        if tableIndex < len(self.tables):
            taskName = 'Unflatten-%d' % tableIndex
            unflattenTime = self.diffInfo[3]
            taskMgr.doMethodLater(unflattenTime, self.unflattenTable, taskName, extraArgs=[tableIndex])

    def unflattenTable(self, tableIndex):
        if tableIndex < len(self.tables):
            table = self.tables[tableIndex]
            if table.state == 'Flat':
                if table.avId and table.avId in self.involvedToons:
                    table.forceControl(table.avId)
                else:
                    table.goFree()

    def incrementDinersExploded(self):
        self.numDinersExploded += 1

    def magicWordHit(self, damage, avId):
        self.hitBoss(damage)

    def __doAreaAttack(self):
        self.b_setAttackCode(ToontownGlobals.BossCogAreaAttack)

    def __doGolfAreaAttack(self):
        self.numGolfAreaAttacks += 1
        self.b_setAttackCode(ToontownGlobals.BossCogGolfAreaAttack)

    def hitToon(self, toonId):
        avId = self.air.getAvatarIdFromSender()
        if not self.validate(avId, avId != toonId, 'hitToon on self'):
            return
        if avId not in self.involvedToons or toonId not in self.involvedToons:
            return
        toon = self.air.doId2do.get(toonId)
        if toon:
            self.healToon(toon, 1)
            self.sendUpdate('toonGotHealed', [toonId])

    def requestGetToonup(self, beltIndex, toonupIndex, toonupNum):
        grantRequest = False
        avId = self.air.getAvatarIdFromSender()
        if self.state != 'BattleFour':
            grantRequest = False
        else:
            if (
             beltIndex, toonupNum) not in self.toonupsGranted:
                toon = simbase.air.doId2do.get(avId)
                if toon:
                    grantRequest = True
        if grantRequest:
            self.toonupsGranted.insert(0, (beltIndex, toonupNum))
            if len(self.toonupsGranted) > 8:
                self.toonupsGranted = self.toonupsGranted[0:8]
            self.sendUpdate('toonGotToonup', [avId, beltIndex, toonupIndex, toonupNum])
            if toonupIndex < len(self.toonUpLevels):
                self.healToon(toon, self.toonUpLevels[toonupIndex])
                self.numToonupGranted += 1
                self.totalLaffHealed += self.toonUpLevels[toonupIndex]
            else:
                self.notify.warning('requestGetToonup this should not happen')
                self.healToon(toon, 1)

    def toonLeftTable(self, tableIndex):
        if self.movingToTable and self.tableDest == tableIndex:
            if random.random() < 0.5:
                self.movingToTable = False
                self.waitForNextAttack(0)

    def getBattleFourTime(self):
        if self.state != 'BattleFour':
            t1 = 0
        else:
            elapsed = globalClock.getFrameTime() - self.battleFourStart
            t1 = elapsed / float(self.battleFourDuration)
        return t1

    def getDamageMultiplier(self):
        mult = 1.0
        if self.doneOvertimeOneAttack and not self.doneOvertimeTwoAttack:
            mult = 1.25
        if self.getBattleFourTime() > 1.0:
            mult = self.getBattleFourTime() + 1
        return mult

    def toggleMove(self):
        self.moveAttackAllowed = not self.moveAttackAllowed
        return self.moveAttackAllowed
