from direct.directnotify import DirectNotifyGlobal
from otp.avatar import DistributedAvatarAI
from toontown.battle import BattleExperienceAI
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import ToontownBattleGlobals
from toontown.toon import InventoryBase
from toontown.battle import DistributedBattleFinalAI
from toontown.building import SuitPlannerInteriorAI
from toontown.battle import BattleBase
from toontown.coghq import CogDisguiseGlobals
from pandac.PandaModules import *
from toontown.suit import SuitDNA
import random
AllBossCogs = []

class DistributedBossCogAI(DistributedAvatarAI.DistributedAvatarAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedBossCogAI')

    def __init__(self, air, dept):
        DistributedAvatarAI.DistributedAvatarAI.__init__(self, air)
        self.dept = dept
        self.dna = SuitDNA.SuitDNA()
        self.dna.newBossCog(self.dept)
        self.deptIndex = SuitDNA.suitDepts.index(self.dept)
        self.resetBattleCounters()
        self.looseToons = []
        self.involvedToons = []
        self.toonsA = []
        self.toonsB = []
        self.nearToons = []
        self.suitsA = []
        self.activeSuitsA = []
        self.suitsB = []
        self.activeSuitsB = []
        self.reserveSuits = []
        self.barrier = None
        self.keyStates = [
         'BattleOne', 'BattleTwo', 'BattleThree', 'Victory']
        self.bossDamage = 0
        self.battleThreeStart = 0
        self.battleThreeDuration = 1800
        self.attackCode = None
        self.attackAvId = 0
        self.hitCount = 0
        self.nerfed = False
        self.numRentalDiguises = 0
        self.numNormalDiguises = 0
        AllBossCogs.append(self)
        return

    def generateWithRequired(self, zoneId):
        self.numRentalDiguises, self.numNormalDiguises = self.countDisguises()
        DistributedAvatarAI.DistributedAvatarAI.generateWithRequired(self, zoneId)

    def delete(self):
        self.ignoreAll()
        if self in AllBossCogs:
            i = AllBossCogs.index(self)
            del AllBossCogs[i]
        return DistributedAvatarAI.DistributedAvatarAI.delete(self)

    def getDNAString(self):
        return self.dna.makeNetString()

    def avatarEnter(self):
        avId = self.air.getAvatarIdFromSender()
        self.addToon(avId)

    def avatarExit(self):
        avId = self.air.getAvatarIdFromSender()
        self.removeToon(avId)

    def avatarNearEnter(self):
        avId = self.air.getAvatarIdFromSender()
        if avId not in self.nearToons:
            self.nearToons.append(avId)

    def avatarNearExit(self):
        avId = self.air.getAvatarIdFromSender()
        try:
            self.nearToons.remove(avId)
        except:
            pass

    def __handleUnexpectedExit(self, avId):
        self.removeToon(avId)

    def addToon(self, avId):
        if avId not in self.looseToons and avId not in self.involvedToons:
            self.looseToons.append(avId)
            event = self.air.getAvatarExitEvent(avId)
            self.acceptOnce(event, self.__handleUnexpectedExit, extraArgs=[avId])

    def removeToon(self, avId):
        resendIds = 0
        try:
            self.looseToons.remove(avId)
        except:
            pass

        try:
            self.involvedToons.remove(avId)
            resendIds = 1
        except:
            pass

        try:
            self.toonsA.remove(avId)
        except:
            pass

        try:
            self.toonsB.remove(avId)
        except:
            pass

        try:
            self.nearToons.remove(avId)
        except:
            pass

        event = self.air.getAvatarExitEvent(avId)
        self.ignore(event)
        if not self.hasToons():
            taskMgr.doMethodLater(10, self.__bossDone, self.uniqueName('BossDone'))

    def __bossDone(self, task):
        if self.air:
            self.air.writeServerEvent('bossBattleDone', self.doId, '%s' % self.dept)
        self.b_setState('Off')
        messenger.send(self.uniqueName('BossDone'))
        self.ignoreAll()

    def hasToons(self):
        return self.looseToons or self.involvedToons

    def hasToonsAlive(self):
        alive = 0
        for toonId in self.involvedToons:
            toon = self.air.doId2do.get(toonId)
            if toon:
                hp = toon.getHp()
                if hp > 0:
                    alive = 1

        return alive

    def isToonKnown(self, toonId):
        return toonId in self.involvedToons or toonId in self.looseToons

    def isToonWearingRentalSuit(self, toonId):
        if not self.isToonKnown(toonId):
            self.notify.warning('isToonWearingRentalSuit: unknown toonId %s' % toonId)
            return False
        toon = self.air.doId2do.get(toonId)
        if toon:
            if hasattr(toon, 'forceRentalDisguise') and toon.forceRentalDisguise:
                return True
            else:
                return not CogDisguiseGlobals.isPaidSuitComplete(toon, toon.getCogParts(), self.dept)
        else:
            self.notify.warning('isToonWearingRentalSuit: toonId %s does not exist' % toonId)
            return False

    def __countNormalDisguiseToons(self):
        return len(self.involvedToons) + len(self.looseToons) - self.__countRentalDisguiseToons()

    def __countRentalDisguiseToons(self):
        count = 0
        for toonId in self.involvedToons + self.looseToons:
            if self.isToonWearingRentalSuit(toonId):
                count += 1

        return count

    def countDisguises(self):
        rentals = self.__countRentalDisguiseToons()
        normals = self.__countNormalDisguiseToons()
        return (
         rentals, normals)

    def sendBattleIds(self):
        self.sendUpdate('setBattleIds', [self.battleNumber, self.battleAId, self.battleBId])

    def sendToonIds(self):
        self.sendUpdate('setToonIds', [self.involvedToons, self.toonsA, self.toonsB])

    def damageToon(self, toon, deduction):
        toon.takeDamage(deduction)
        if toon.getHp() <= 0:
            self.sendUpdate('toonDied', [toon.doId])
            empty = InventoryBase.InventoryBase(toon)
            toon.b_setInventory(empty.makeNetString())
            self.removeToon(toon.doId)

    def healToon(self, toon, increment):
        toon.toonUp(increment)

    def d_setBattleExperience(self):
        self.sendUpdate('setBattleExperience', self.getBattleExperience())

    def getBattleExperience(self):
        result = BattleExperienceAI.getBattleExperience(8, self.involvedToons, self.toonExp, self.toonSkillPtsGained, self.toonOrigQuests, self.toonItems, self.toonOrigMerits, self.toonMerits, self.toonParts, self.suitsKilled, self.helpfulToons)
        return result

    def b_setArenaSide(self, arenaSide):
        self.setArenaSide(arenaSide)
        self.d_setArenaSide(arenaSide)

    def setArenaSide(self, arenaSide):
        self.arenaSide = arenaSide

    def d_setArenaSide(self, arenaSide):
        self.sendUpdate('setArenaSide', [arenaSide])

    def b_setState(self, state):
        self.setState(state)
        self.d_setState(state)

    def d_setState(self, state):
        self.sendUpdate('setState', [state])

    def setState(self, state):
        self.demand(state)
        if self.air:
            if state in self.keyStates:
                self.air.writeServerEvent('bossBattle', self.doId, '%s|%s|%s|%s|%s|%s' % (self.dept, state, self.involvedToons, self.formatReward(), self.formatLaffLevels(), self.formatSuitType()))

    def getState(self):
        return self.state

    def formatReward(self):
        return 'unspecified'

    def formatLaffLevels(self):
        try:
            return [simbase.air.doId2do.get(id).getMaxHp() for id in self.involvedToons]
        except Exception as e:
            self.notify.warning(e)
            return []

    def formatSuitType(self):
        try:

            def hasSuit(id):
                if not self.isToonWearingRentalSuit(id):
                    return 1
                else:
                    return 0

            return list(map(hasSuit, self.involvedToons))
        except Exception as e:
            self.notify.warning(e)
            return []

    def enterOff(self):
        self.resetBattles()
        self.resetToons()
        self.resetBattleCounters()

    def exitOff(self):
        pass

    def enterWaitForToons(self):
        self.acceptNewToons()
        self.barrier = self.beginBarrier('WaitForToons', self.involvedToons, 5, self.__doneWaitForToons)

    def __doneWaitForToons(self, toons):
        self.b_setState('Elevator')

    def exitWaitForToons(self):
        self.ignoreBarrier(self.barrier)

    def enterElevator(self):
        if self.notify.getDebug():
            for toonId in self.involvedToons:
                toon = simbase.air.doId2do.get(toonId)
                if toon:
                    self.notify.debug('%s. involved toon %s, %s/%s' % (self.doId, toonId, toon.getHp(), toon.getMaxHp()))

        self.resetBattles()
        self.barrier = self.beginBarrier('Elevator', self.involvedToons, 30, self.__doneElevator)

    def __doneElevator(self, avIds):
        self.b_setState('Introduction')

    def exitElevator(self):
        self.ignoreBarrier(self.barrier)

    def enterIntroduction(self):
        self.resetBattles()
        self.arenaSide = None
        self.makeBattleOneBattles()
        self.barrier = self.beginBarrier('Introduction', self.involvedToons, 45, self.doneIntroduction)
        return

    def doneIntroduction(self, avIds):
        self.b_setState('BattleOne')

    def exitIntroduction(self):
        self.ignoreBarrier(self.barrier)
        for toonId in self.involvedToons:
            toon = simbase.air.doId2do.get(toonId)
            if toon:
                toon.b_setCogIndex(-1)

    def enterBattleOne(self):
        if self.battleA:
            self.battleA.startBattle(self.toonsA, self.suitsA)
        if self.battleB:
            self.battleB.startBattle(self.toonsB, self.suitsB)

    def exitBattleOne(self):
        self.resetBattles()

    def enterReward(self):
        self.resetBattles()
        self.barrier = self.beginBarrier('Reward', self.involvedToons, BattleBase.BUILDING_REWARD_TIMEOUT, self.__doneReward)

    def __doneReward(self, avIds):
        self.b_setState('Epilogue')

    def exitReward(self):
        pass

    def enterEpilogue(self):
        pass

    def exitEpilogue(self):
        pass

    def enterFrolic(self):
        self.resetBattles()

    def exitFrolic(self):
        pass

    def resetBattleCounters(self):
        self.battleNumber = 0
        self.battleA = None
        self.battleAId = 0
        self.battleB = None
        self.battleBId = 0
        self.arenaSide = None
        self.toonSkillPtsGained = {}
        self.toonExp = {}
        self.toonOrigQuests = {}
        self.toonItems = {}
        self.toonOrigMerits = {}
        self.toonMerits = {}
        self.toonParts = {}
        self.suitsKilled = []
        self.helpfulToons = []
        return

    def resetBattles(self):
        sendReset = 0
        if self.battleA:
            self.battleA.requestDelete()
            self.battleA = None
            self.battleAId = 0
            sendReset = 1
        if self.battleB:
            self.battleB.requestDelete()
            self.battleB = None
            self.battleBId = 0
            sendReset = 1
        for suit in self.suitsA + self.suitsB:
            suit.requestDelete()

        for suit, joinChance in self.reserveSuits:
            suit.requestDelete()

        self.suitsA = []
        self.activeSuitsA = []
        self.suitsB = []
        self.activeSuitsB = []
        self.reserveSuits = []
        self.battleNumber = 0
        if sendReset:
            self.sendBattleIds()
        return

    def resetToons(self):
        if self.toonsA or self.toonsB:
            self.looseToons = self.looseToons + self.involvedToons
            self.involvedToons = []
            self.toonsA = []
            self.toonsB = []
            self.sendToonIds()

    def divideToons(self):
        if self.nerfed:
            splitMethod = self.__balancedDivide
        else:
            splitMethod = self.__randomDivide
        self.toonsA, self.toonsB, loose = splitMethod()
        self.looseToons += loose
        self.sendToonIds()

    def __randomDivide(self):
        toons = self.involvedToons[:]
        random.shuffle(toons)
        numToons = min(len(toons), 8)
        if numToons < 4:
            numToonsB = numToons // 2
        else:
            numToonsB = (numToons + random.choice([0, 1])) // 2
        teamA = toons[numToonsB:numToons]
        teamB = toons[:numToonsB]
        loose = toons[numToons:]
        return (
         teamA, teamB, loose)

    def __balancedDivide(self):
        toons = self.involvedToons[:]
        random.shuffle(toons)
        teamA, teamB, loose = [], [], []
        for i, toon in enumerate(sorted(toons, key=self.isToonWearingRentalSuit)):
            if i < 8:
                if i % 2 == 0:
                    teamA.append(toon)
                else:
                    teamB.append(toon)
            else:
                loose.append(toon)

        return (
         teamA, teamB, loose)

    def acceptNewToons(self):
        sourceToons = self.looseToons
        self.looseToons = []
        for toonId in sourceToons:
            toon = self.air.doId2do.get(toonId)
            if toon and not toon.ghostMode:
                self.involvedToons.append(toonId)
            else:
                self.looseToons.append(toonId)

        for avId in self.involvedToons:
            toon = self.air.doId2do.get(avId)
            if toon:
                p = []
                for t in ToontownBattleGlobals.Tracks:
                    p.append(toon.experience.getExp(t))

                self.toonExp[avId] = p
                self.toonOrigMerits[avId] = toon.cogMerits[:]

        self.divideToons()

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
        suitHandles = self.generateSuits(battleNumber)
        self.suitsB = suitHandles['activeSuits']
        self.activeSuitsB = self.suitsB[:]
        self.reserveSuits += suitHandles['reserveSuits']
        if self.toonsA:
            self.battleA = self.makeBattle(bossCogPosHpr, ToontownGlobals.BossCogBattleAPosHpr, self.handleRoundADone, self.handleBattleADone, battleNumber, 0)
            self.battleAId = self.battleA.doId
        else:
            self.moveSuits(self.activeSuitsA)
            self.suitsA = []
            self.activeSuitsA = []
            if self.arenaSide == None:
                self.b_setArenaSide(0)
        if self.toonsB:
            self.battleB = self.makeBattle(bossCogPosHpr, ToontownGlobals.BossCogBattleBPosHpr, self.handleRoundBDone, self.handleBattleBDone, battleNumber, 1)
            self.battleBId = self.battleB.doId
        else:
            self.moveSuits(self.activeSuitsB)
            self.suitsB = []
            self.activeSuitsB = []
            if self.arenaSide == None:
                self.b_setArenaSide(1)
        self.sendBattleIds()
        return

    def makeBattle(self, bossCogPosHpr, battlePosHpr, roundCallback, finishCallback, battleNumber, battleSide):
        battle = DistributedBattleFinalAI.DistributedBattleFinalAI(self.air, self, roundCallback, finishCallback, battleSide)
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
        battle.generateWithRequired(self.zoneId)
        return battle

    def setBattlePos(self, battle, cogPosHpr, battlePosHpr):
        bossNode = NodePath('bossNode')
        bossNode.setPosHpr(*cogPosHpr)
        battleNode = bossNode.attachNewNode('battleNode')
        battleNode.setPosHpr(*battlePosHpr)
        suitNode = battleNode.attachNewNode('suitNode')
        suitNode.setPos(0, 1, 0)
        battle.pos = battleNode.getPos(NodePath())
        battle.initialSuitPos = suitNode.getPos(NodePath())

    def moveSuits(self, active):
        for suit in active:
            self.reserveSuits.append((suit, 0))

    def handleRoundADone(self, toonIds, totalHp, deadSuits):
        if self.battleA:
            self.handleRoundDone(self.battleA, self.suitsA, self.activeSuitsA, toonIds, totalHp, deadSuits)

    def handleRoundBDone(self, toonIds, totalHp, deadSuits):
        if self.battleB:
            self.handleRoundDone(self.battleB, self.suitsB, self.activeSuitsB, toonIds, totalHp, deadSuits)

    def handleBattleADone(self, zoneId, toonIds):
        if self.battleA:
            self.battleA.requestDelete()
            self.battleA = None
            self.battleAId = 0
            self.sendBattleIds()
        if self.arenaSide == None:
            self.b_setArenaSide(0)
        if not self.battleB and self.hasToons() and self.hasToonsAlive():
            self.b_setState(self.postBattleState)
        return

    def handleBattleBDone(self, zoneId, toonIds):
        if self.battleB:
            self.battleB.requestDelete()
            self.battleB = None
            self.battleBId = 0
            self.sendBattleIds()
        if self.arenaSide == None:
            self.b_setArenaSide(1)
        if not self.battleA and self.hasToons() and self.hasToonsAlive():
            self.b_setState(self.postBattleState)
        return

    def invokeSuitPlanner(self, buildingCode, skelecog):
        planner = SuitPlannerInteriorAI.SuitPlannerInteriorAI(1, buildingCode, self.dna.dept, self.zoneId)
        planner.respectInvasions = 0
        suits = planner.genFloorSuits(0)
        if skelecog:
            for suit in suits['activeSuits']:
                suit.b_setSkelecog(1)

            for reserve in suits['reserveSuits']:
                suit = reserve[0]
                suit.b_setSkelecog(1)

        return suits

    def generateSuits(self, battleNumber):
        raise Exception('generateSuits unimplemented')

    def handleRoundDone(self, battle, suits, activeSuits, toonIds, totalHp, deadSuits):
        totalMaxHp = 0
        for suit in suits:
            totalMaxHp += suit.maxHP

        for suit in deadSuits:
            activeSuits.remove(suit)

        joinedReserves = []
        if len(self.reserveSuits) > 0 and len(activeSuits) < 4:
            hpPercent = 100 - totalHp // totalMaxHp * 100.0
            for info in self.reserveSuits:
                if info[1] <= hpPercent and len(activeSuits) < 4:
                    suits.append(info[0])
                    activeSuits.append(info[0])
                    joinedReserves.append(info)

            for info in joinedReserves:
                self.reserveSuits.remove(info)

        battle.resume(joinedReserves)

    def getBattleThreeTime(self):
        elapsed = globalClock.getFrameTime() - self.battleThreeStart
        t1 = elapsed / float(self.battleThreeDuration)
        return t1

    def progressValue(self, fromValue, toValue):
        t0 = float(self.bossDamage) / float(self.bossMaxDamage)
        elapsed = globalClock.getFrameTime() - self.battleThreeStart
        t1 = elapsed / float(self.battleThreeDuration)
        t = max(t0, t1)
        return fromValue + (toValue - fromValue) * min(t, 1)

    def progressRandomValue(self, fromValue, toValue, radius=0.2):
        t = self.progressValue(0, 1)
        radius = radius * (1.0 - abs(t - 0.5) * 2.0)
        t += radius * random.uniform(-1, 1)
        t = max(min(t, 1.0), 0.0)
        return fromValue + (toValue - fromValue) * t

    def reportToonHealth(self):
        if self.notify.getDebug():
            str = ''
            for toonId in self.involvedToons:
                toon = self.air.doId2do.get(toonId)
                if toon:
                    str += ', %s (%s/%s)' % (toonId, toon.getHp(), toon.getMaxHp())

            self.notify.debug('%s.toons = %s' % (self.doId, str[2:]))

    def getDamageMultiplier(self):
        return 1.0

    def zapToon(self, x, y, z, h, p, r, bpx, bpy, attackCode, timestamp):
        avId = self.air.getAvatarIdFromSender()
        if not self.validate(avId, avId in self.involvedToons, 'zapToon from unknown avatar'):
            return
        if attackCode == ToontownGlobals.BossCogLawyerAttack and self.dna.dept != 'l':
            self.notify.warning('got lawyer attack but not in CJ boss battle')
            return
        toon = simbase.air.doId2do.get(avId)
        if toon:
            self.d_showZapToon(avId, x, y, z, h, p, r, attackCode, timestamp)
            damage = ToontownGlobals.BossCogDamageLevels.get(attackCode)
            if damage == None:
                self.notify.warning('No damage listed for attack code %s' % attackCode)
                damage = 5
            damage *= self.getDamageMultiplier()
            damage = max(int(damage), 1)
            self.damageToon(toon, damage)
            currState = self.getCurrentOrNextState()
            if attackCode == ToontownGlobals.BossCogElectricFence and (currState == 'RollToBattleTwo' or currState == 'BattleThree'):
                if bpy < 0 and abs(bpx / bpy) > 0.5:
                    if bpx < 0:
                        self.b_setAttackCode(ToontownGlobals.BossCogSwatRight)
                    else:
                        self.b_setAttackCode(ToontownGlobals.BossCogSwatLeft)
        return

    def d_showZapToon(self, avId, x, y, z, h, p, r, attackCode, timestamp):
        self.sendUpdate('showZapToon', [avId, x, y, z, h, p, r, attackCode, timestamp])

    def b_setAttackCode(self, attackCode, avId=0):
        self.d_setAttackCode(attackCode, avId)
        self.setAttackCode(attackCode, avId)

    def setAttackCode(self, attackCode, avId=0):
        self.attackCode = attackCode
        self.attackAvId = avId
        if attackCode == ToontownGlobals.BossCogDizzy or attackCode == ToontownGlobals.BossCogDizzyNow:
            delayTime = self.progressValue(20, 5)
            self.hitCount = 0
        else:
            if attackCode == ToontownGlobals.BossCogSlowDirectedAttack:
                delayTime = ToontownGlobals.BossCogAttackTimes.get(attackCode)
                delayTime += self.progressValue(10, 0)
            else:
                delayTime = ToontownGlobals.BossCogAttackTimes.get(attackCode)
                if delayTime == None:
                    return
        self.waitForNextAttack(delayTime)
        return

    def d_setAttackCode(self, attackCode, avId=0):
        self.sendUpdate('setAttackCode', [attackCode, avId])

    def waitForNextAttack(self, delayTime):
        currState = self.getCurrentOrNextState()
        if currState == 'BattleThree':
            taskName = self.uniqueName('NextAttack')
            taskMgr.remove(taskName)
            taskMgr.doMethodLater(delayTime, self.doNextAttack, taskName)

    def stopAttacks(self):
        taskName = self.uniqueName('NextAttack')
        taskMgr.remove(taskName)

    def doNextAttack(self, task):
        self.b_setAttackCode(ToontownGlobals.BossCogNoAttack)
