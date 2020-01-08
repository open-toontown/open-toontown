from pandac.PandaModules import *
from direct.showbase import DirectObject
from toontown.suit import SuitDNA
from direct.directnotify import DirectNotifyGlobal
from toontown.coghq import LevelBattleManagerAI
import random
import functools

class LevelSuitPlannerAI(DirectObject.DirectObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('LevelSuitPlannerAI')

    def __init__(self, air, level, cogCtor, battleCtor, cogSpecs, reserveCogSpecs, battleCellSpecs, battleExpAggreg=None):
        self.air = air
        self.level = level
        self.cogCtor = cogCtor
        self.cogSpecs = cogSpecs
        if simbase.config.GetBool('level-reserve-suits', 0):
            self.reserveCogSpecs = reserveCogSpecs
        else:
            self.reserveCogSpecs = []
        self.battleCellSpecs = battleCellSpecs
        self.__genSuitInfos(self.level.getCogLevel(), self.level.getCogTrack())
        self.battleMgr = LevelBattleManagerAI.LevelBattleManagerAI(self.air, self.level, battleCtor, battleExpAggreg)
        self.battleCellId2suits = {}
        for id in list(self.battleCellSpecs.keys()):
            self.battleCellId2suits[id] = []

    def destroy(self):
        self.battleMgr.destroyBattleMgr()
        del self.battleMgr
        self.battleCellId2suits = {}
        self.ignoreAll()
        del self.cogSpecs
        del self.cogCtor
        del self.level
        del self.air

    def __genJoinChances(self, num):
        joinChances = []
        for currChance in range(num):
            joinChances.append(random.randint(1, 100))

        joinChances.sort(key=functools.cmp_to_key(cmp))
        return joinChances

    def __genSuitInfos(self, level, track):
        if __dev__:
            pass

        def getSuitDict(spec, cogId, level=level, track=track):
            suitDict = {}
            suitDict['track'] = track
            suitDict.update(spec)
            suitDict['zoneId'] = self.level.getEntityZoneId(spec['parentEntId'])
            suitDict['level'] += level
            suitDict['cogId'] = cogId
            return suitDict

        self.suitInfos = {}
        self.suitInfos['activeSuits'] = []
        for i in range(len(self.cogSpecs)):
            spec = self.cogSpecs[i]
            self.suitInfos['activeSuits'].append(getSuitDict(spec, i))

        numReserve = len(self.reserveCogSpecs)
        joinChances = self.__genJoinChances(numReserve)
        self.suitInfos['reserveSuits'] = []
        for i in range(len(self.reserveCogSpecs)):
            spec = self.reserveCogSpecs[i]
            suitDict = getSuitDict(spec, i)
            suitDict['joinChance'] = joinChances[i]
            self.suitInfos['reserveSuits'].append(suitDict)

    def __genSuitObject(self, suitDict, reserve):
        suit = self.cogCtor(simbase.air, self)
        dna = SuitDNA.SuitDNA()
        dna.newSuitRandom(level=SuitDNA.getRandomSuitType(suitDict['level']), dept=suitDict['track'])
        suit.dna = dna
        suit.setLevel(suitDict['level'])
        suit.setSkeleRevives(suitDict.get('revives'))
        suit.setLevelDoId(self.level.doId)
        suit.setCogId(suitDict['cogId'])
        suit.setReserve(reserve)
        if suitDict['skeleton']:
            suit.setSkelecog(1)
        suit.generateWithRequired(suitDict['zoneId'])
        suit.boss = suitDict['boss']
        return suit

    def genSuits(self):
        suitHandles = {}
        activeSuits = []
        for activeSuitInfo in self.suitInfos['activeSuits']:
            suit = self.__genSuitObject(activeSuitInfo, 0)
            suit.setBattleCellIndex(activeSuitInfo['battleCell'])
            activeSuits.append(suit)

        suitHandles['activeSuits'] = activeSuits
        reserveSuits = []
        for reserveSuitInfo in self.suitInfos['reserveSuits']:
            suit = self.__genSuitObject(reserveSuitInfo, 1)
            reserveSuits.append([suit, reserveSuitInfo['joinChance'], reserveSuitInfo['battleCell']])

        suitHandles['reserveSuits'] = reserveSuits
        return suitHandles

    def __suitCanJoinBattle(self, cellId):
        battle = self.battleMgr.getBattle(cellId)
        if not battle.suitCanJoin():
            return 0
        return 1

    def requestBattle(self, suit, toonId):
        cellIndex = suit.getBattleCellIndex()
        cellSpec = self.battleCellSpecs[cellIndex]
        pos = cellSpec['pos']
        zone = self.level.getZoneId(self.level.getEntityZoneEntId(cellSpec['parentEntId']))
        maxSuits = 4
        self.battleMgr.newBattle(cellIndex, zone, pos, suit, toonId, self.__handleRoundFinished, self.__handleBattleFinished, maxSuits)
        for otherSuit in self.battleCellId2suits[cellIndex]:
            if otherSuit is not suit:
                if self.__suitCanJoinBattle(cellIndex):
                    self.battleMgr.requestBattleAddSuit(cellIndex, otherSuit)
                else:
                    battle = self.battleMgr.getBattle(cellIndex)
                    if battle:
                        self.notify.warning('battle not joinable: numSuits=%s, joinable=%s, fsm=%s, toonId=%s' % (len(battle.suits), battle.isJoinable(), battle.fsm.getCurrentState().getName(), toonId))
                    else:
                        self.notify.warning('battle not joinable: no battle for cell %s, toonId=%s' % (cellIndex, toonId))
                    return 0

        return 1

    def __handleRoundFinished(self, cellId, toonIds, totalHp, deadSuits):
        totalMaxHp = 0
        level = self.level
        battle = self.battleMgr.cellId2battle[cellId]
        for suit in battle.suits:
            totalMaxHp += suit.maxHP

        for suit in deadSuits:
            level.suits.remove(suit)

        cellReserves = []
        for info in level.reserveSuits:
            if info[2] == cellId:
                cellReserves.append(info)

        numSpotsAvailable = 4 - len(battle.suits)
        if len(cellReserves) > 0 and numSpotsAvailable > 0:
            self.joinedReserves = []
            if __dev__:
                pass
            if len(battle.suits) == 0:
                hpPercent = 100
            else:
                hpPercent = 100 - totalHp / totalMaxHp * 100.0
            for info in cellReserves:
                if info[1] <= hpPercent and len(self.joinedReserves) < numSpotsAvailable:
                    level.suits.append(info[0])
                    self.joinedReserves.append(info)
                    info[0].setBattleCellIndex(cellId)

            for info in self.joinedReserves:
                level.reserveSuits.remove(info)

            if len(self.joinedReserves) > 0:
                self.reservesJoining(battle)
                level.d_setSuits()
                return
        if len(battle.suits) == 0:
            if battle:
                battle.resume()
        else:
            battle = self.battleMgr.cellId2battle.get(cellId)
            if battle:
                battle.resume()

    def __handleBattleFinished(self, zoneId):
        pass

    def reservesJoining(self, battle):
        for info in self.joinedReserves:
            battle.suitRequestJoin(info[0])

        battle.resume()
        self.joinedReserves = []

    def getDoId(self):
        return 0

    def removeSuit(self, suit):
        suit.requestDelete()

    def suitBattleCellChange(self, suit, oldCell, newCell):
        if oldCell is not None:
            if oldCell in self.battleCellId2suits:
                self.battleCellId2suits[oldCell].remove(suit)
            else:
                self.notify.warning('FIXME crash bandaid suitBattleCellChange suit.doId =%s, oldCell=%s not in battleCellId2Suits.keys %s' % (suit.doId, oldCell, list(self.battleCellId2suits.keys())))
            blocker = self.battleMgr.battleBlockers.get(oldCell)
            if blocker:
                blocker.removeSuit(suit)
        if newCell is not None:
            self.battleCellId2suits[newCell].append(suit)

            def addSuitToBlocker(self=self):
                blocker = self.battleMgr.battleBlockers.get(newCell)
                if blocker:
                    blocker.addSuit(suit)
                    return 1
                return 0

            if not addSuitToBlocker():
                self.accept(self.getBattleBlockerEvent(newCell), addSuitToBlocker)
        return

    def getBattleBlockerEvent(self, cellId):
        return 'battleBlockerAdded-' + str(self.level.doId) + '-' + str(cellId)
