from direct.directnotify import DirectNotifyGlobal
from toontown.racing import DistributedRaceAI
from toontown.toonbase import ToontownGlobals, TTLocalizer
from toontown.coghq import MintLayout
from toontown.ai import HolidayBaseAI
from direct.showbase import DirectObject
from toontown.racing import RaceGlobals
import os, pickle

class RaceManagerAI(DirectObject.DirectObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('RaceManagerAI')
    serverDataFolder = simbase.config.GetString('server-data-folder', '')

    def __init__(self, air):
        DirectObject.DirectObject.__init__(self)
        self.air = air
        self.races = []
        self.shard = str(air.districtId)
        self.filename = self.getFilename()
        self.trackRecords = self.loadRecords()

    def getDoId(self):
        return 0

    def createRace(self, trackId, raceType, laps, players, circuitLoop, circuitPoints, circuitTimes, qualTimes=[], circuitTimeList={}, circuitTotalBonusTickets={}):
        raceZone = self.air.allocateZone()
        race = DistributedRaceAI.DistributedRaceAI(self.air, trackId, raceZone, players, laps, raceType, self.exitedRace, self.raceOver, circuitLoop, circuitPoints, circuitTimes, qualTimes, circuitTimeList, circuitTotalBonusTickets)
        race.generateWithRequired(raceZone)
        race.playersFinished = []
        race.lastTotalTime = 0
        self.races.append(race)
        return raceZone

    def exitedRace(self, race, playerInfo):
        self.notify.debug('exited race: %s' % playerInfo.avId)
        totalTime = playerInfo.totalTime
        entryFee = 0
        bonus = 0
        placeMultiplier = 0
        qualify = 0
        winnings = 0
        trophies = []
        points = []
        newHistory = None
        race.playersFinished.append(playerInfo.avId)
        place = len(race.playersFinished)
        self.notify.debug('place: %s of %s' % (place, race.toonCount))
        self.notify.debug('pre-tie totalTime: %s' % totalTime)
        if totalTime <= race.lastTotalTime:
            totalTime = race.lastTotalTime + 0.01
        race.lastTotalTime = totalTime
        self.notify.debug('totalTime: %s, qualify: %s' % (totalTime, RaceGlobals.getQualifyingTime(race.trackId)))
        circuitTime = totalTime + race.circuitTimes.get(playerInfo.avId, 0)
        race.circuitTimes[playerInfo.avId] = circuitTime
        if not race.circuitTimeList.get(playerInfo.avId):
            race.circuitTimeList[playerInfo.avId] = []
        race.circuitTimeList[playerInfo.avId].append([totalTime, 0])
        self.notify.debug('CircuitTimeList %s' % race.circuitTimeList)
        if race.raceType == RaceGlobals.Circuit:
            points = race.circuitPoints.get(playerInfo.avId, [])
            points.append(RaceGlobals.CircuitPoints[place - 1])
            race.circuitPoints[playerInfo.avId] = points
        currentTimeIndex = len(race.circuitTimeList[playerInfo.avId]) - 1
        if totalTime <= RaceGlobals.getQualifyingTime(race.trackId):
            race.circuitTimeList[playerInfo.avId][currentTimeIndex][1] = 1
            self.notify.debug('Racer Qualified time: %s required: %s' % (totalTime, RaceGlobals.getQualifyingTime(race.trackId)))
            qualify = 1
            self.checkPersonalBest(race.trackId, totalTime, race.raceType, race.toonCount, playerInfo.avId)
            if race.raceType == RaceGlobals.Practice:
                winnings = RaceGlobals.PracticeWinnings
                self.notify.debug('GrandTouring: Checking from branch: practice %s' % playerInfo.avId)
                trophies = self.checkForNonRaceTrophies(playerInfo.avId)
                if trophies:
                    self.updateTrophiesFromList(playerInfo.avId, trophies)
            else:
                self.air.writeServerEvent('kartingPlaced', playerInfo.avId, '%s|%s' % (place, race.toonCount))
                if race.raceType != RaceGlobals.Circuit:
                    entryFee = RaceGlobals.getEntryFee(race.trackId, race.raceType)
                    placeMultiplier = RaceGlobals.Winnings[place - 1 + (RaceGlobals.MaxRacers - race.toonCount)]
                    winnings = int(entryFee * placeMultiplier)
                    newHistory = self.getNewSingleRaceHistory(race, playerInfo.avId, place)
                    av = self.air.doId2do.get(playerInfo.avId)
                    if newHistory:
                        self.notify.debug('history %s' % newHistory)
                        av.b_setKartingHistory(newHistory)
                        trophies = self.checkForRaceTrophies(race, playerInfo.avId)
                    else:
                        trophies = self.checkForNonRaceTrophies(playerInfo.avId)
                    if trophies:
                        self.updateTrophiesFromList(playerInfo.avId, trophies)
                bonus = self.checkTimeRecord(race.trackId, totalTime, race.raceType, race.toonCount, playerInfo.avId)
                if playerInfo.avId in race.circuitTotalBonusTickets:
                    race.circuitTotalBonusTickets[playerInfo.avId] += bonus
                else:
                    race.circuitTotalBonusTickets[playerInfo.avId] = bonus
            av = self.air.doId2do.get(playerInfo.avId)
            if av:
                oldTickets = av.getTickets()
                self.notify.debug('old tickets: %s' % oldTickets)
                newTickets = oldTickets + winnings + entryFee + bonus
                self.air.writeServerEvent('kartingTicketsWon', playerInfo.avId, '%s' % (newTickets - oldTickets))
                self.notify.debug('entry fee: %s' % entryFee)
                self.notify.debug('place mult: %s' % placeMultiplier)
                self.notify.debug('winnings: %s' % winnings)
                self.notify.debug('bonus: %s' % bonus)
                self.notify.debug('new tickets: %s' % newTickets)
                self.notify.debug('circuit points: %s' % points)
                self.notify.debug('circuit time: %s' % circuitTime)
                self.notify.debug('circuitTotalBonusTickets: %s' % race.circuitTotalBonusTickets)
                av.b_setTickets(newTickets)
        else:
            race.circuitTimeList[playerInfo.avId][currentTimeIndex][1] = -1
            self.notify.debug('GrandTouring: Checking from branch: Not Qualified %s' % playerInfo.avId)
            trophies = self.checkForNonRaceTrophies(playerInfo.avId)
            if trophies:
                self.updateTrophiesFromList(playerInfo.avId, trophies)
        if race in self.races:
            race.d_setPlace(playerInfo.avId, totalTime, place, entryFee, qualify, winnings, bonus, trophies, points, circuitTime)
            if race.isCircuit():
                self.notify.debug('isCircuit')
                if race.everyoneDone():
                    self.notify.debug('everyoneDone')
                    if race.isLastRace():
                        taskMgr.doMethodLater(10, self.endCircuitRace, 'DelayEndCircuitRace=%d' % race.doId, (race, bonus))
                    else:
                        self.endCircuitRace(race, bonus)
            else:
                self.notify.debug('not isCircuit')
        return

    def endCircuitRace(self, race, bonus=0):
        self.notify.debug('endCircuitRace')
        pointTotals = []
        for avId in race.circuitPoints:
            pointTotals.append([avId, sum(race.circuitPoints[avId])])

        numVals = len(pointTotals)
        finalStandings = []

        def swap(x, y):
            t = pointTotals[x]
            pointTotals[x] = pointTotals[y]
            pointTotals[y] = t

        for i in range(numVals - 1, 0, -1):
            for j in range(i):
                if pointTotals[j][1] < pointTotals[j + 1][1]:
                    swap(j, j + 1)
                elif pointTotals[j][1] == pointTotals[j + 1][1]:
                    avId1 = pointTotals[j][0]
                    avId2 = pointTotals[j + 1][0]
                    if race.circuitTimes[avId1] > race.circuitTimes[avId2]:
                        swap(j, j + 1)

        for i in range(numVals):
            finalStandings.append(pointTotals[i][0])

        self.notify.debug('Final standings %s' % finalStandings)
        for avId in finalStandings:
            self.notify.debug('avId %s' % avId)
            place = finalStandings.index(avId) + 1
            places = len(finalStandings)
            winnings = 0
            trophies = []
            if race.isLastRace():
                self.notify.debug('isLastRace')
                av = self.air.doId2do.get(avId)
                if av and avId in race.playersFinished:
                    self.air.writeServerEvent('kartingCircuitFinished', avId, '%s|%s' % (place, places))
                    print('kartingCircuitFinished', avId, '%s|%s' % (place, places))
                    entryFee = RaceGlobals.getEntryFee(race.trackId, race.raceType)
                    placeMultiplier = RaceGlobals.Winnings[place - 1 + (RaceGlobals.MaxRacers - places)]
                    winnings = int(entryFee * placeMultiplier)
                    newHistory = self.getNewCircuitHistory(race, avId, place)
                    if newHistory:
                        self.notify.debug('history %s' % newHistory)
                        trophies = self.checkForCircuitTrophies(race, avId, newHistory)
                        av.b_setKartingHistory(newHistory)
                        if trophies:
                            self.updateTrophiesFromList(avId, trophies)
                    else:
                        self.notify.debug('no new history')
                        trophies = self.checkForNonRaceTrophies(avId)
                    oldTickets = av.getTickets()
                    self.notify.debug('endCircuitRace: old tickets: %s' % oldTickets)
                    newTickets = oldTickets + winnings + entryFee
                    self.air.writeServerEvent('kartingTicketsWonCircuit', avId, '%s' % (newTickets - oldTickets))
                    self.notify.debug('entry fee: %s' % entryFee)
                    self.notify.debug('place mult: %s' % placeMultiplier)
                    self.notify.debug('winnings: %s' % winnings)
                    self.notify.debug('new tickets: %s' % newTickets)
                    self.notify.debug('trophies: %s' % trophies)
                    self.notify.debug('bonus: %s' % bonus)
                    av.b_setTickets(newTickets)
                    finalBonus = 0
                    if avId in race.circuitTotalBonusTickets:
                        finalBonus = race.circuitTotalBonusTickets[avId]
                    race.d_setCircuitPlace(avId, place, entryFee, winnings, finalBonus, trophies)

        race.playersFinished = finalStandings
        race.d_endCircuitRace()

    def updateTrophiesFromList(self, avId, trophies):
        self.air.writeServerEvent('Writing Trophies: Updating trophies from list', avId, '%s' % trophies)
        av = self.air.doId2do.get(avId)
        if not av:
            return
        if not trophies:
            return
        trophyField = av.getKartingTrophies()
        for trophy in trophies:
            trophyField[trophy] = 1

        av.b_setKartingTrophies(trophyField)

    def checkForCircuitTrophies(self, race, avId, inHistory=None):
        av = self.air.doId2do.get(avId)
        if not av:
            return []
        trophies = av.getKartingTrophies()
        if inHistory:
            history = inHistory
        else:
            history = av.getKartingHistory()
        winIndex = RaceGlobals.CircuitWins
        winReqList = RaceGlobals.WonCircuitRaces
        winIndices = RaceGlobals.CircuitWinsList
        sweepIndex = RaceGlobals.CircuitSweeps
        sweepReqList = RaceGlobals.SweptCircuitRaces
        sweepIndices = RaceGlobals.CircuitSweepsList
        qualIndex = RaceGlobals.CircuitQuals
        qualReqList = RaceGlobals.QualifiedCircuitRaces
        qualIndices = RaceGlobals.CircuitQualList
        trophies = av.getKartingTrophies()
        newTrophies = []
        newTrophies.extend(self.checkHistoryForTrophy(trophies, history, winIndex, winReqList, winIndices))
        newTrophies.extend(self.checkHistoryForTrophy(trophies, history, sweepIndex, sweepReqList, sweepIndices))
        newTrophies.extend(self.checkHistoryForTrophy(trophies, history, qualIndex, qualReqList, qualIndices))
        self.notify.debug('GrandTouring: Checking from branch: Circuit %s' % avId)
        newTrophies.extend(self.checkForNonRaceTrophies(avId, history))
        newTrophies.sort()
        return newTrophies

    def checkForRaceTrophies(self, race, avId, inHistory=None):
        av = self.air.doId2do.get(avId)
        if not av:
            return []
        trophies = av.getKartingTrophies()
        if inHistory:
            history = inHistory
        else:
            history = av.getKartingHistory()
        newTrophies = []
        numTrackGenres = len(RaceGlobals.WinsList)
        for genre in range(numTrackGenres):
            singleGenreNewTrophies = self.checkHistoryForTrophy(trophies, history, RaceGlobals.WinsList[genre], RaceGlobals.WonRaces, RaceGlobals.AllWinsList[genre])
            newTrophies.extend(singleGenreNewTrophies)

        numTrackGenres = len(RaceGlobals.QualsList)
        for genre in range(numTrackGenres):
            singleGenreNewTrophies = self.checkHistoryForTrophy(trophies, history, RaceGlobals.QualsList[genre], RaceGlobals.QualifiedRaces, RaceGlobals.AllQualsList[genre])
            newTrophies.extend(singleGenreNewTrophies)

        totalWins = 0
        for genre in range(numTrackGenres):
            totalWins += history[RaceGlobals.WinsList[genre]]

        singleGenreNewTrophies = self.checkHistoryForTrophyByValue(trophies, history, totalWins, [
         RaceGlobals.TotalWonRaces], [
         RaceGlobals.TotalWins])
        newTrophies.extend(singleGenreNewTrophies)
        totalQuals = 0
        for genre in range(numTrackGenres):
            totalQuals += history[RaceGlobals.QualsList[genre]]

        singleGenreNewTrophies = self.checkHistoryForTrophyByValue(trophies, history, totalQuals, [
         RaceGlobals.TotalQualifiedRaces], [
         RaceGlobals.TotalQuals])
        newTrophies.extend(singleGenreNewTrophies)
        self.notify.debug('GrandTouring: Checking from branch: Race %s ' % avId)
        newTrophies.extend(self.checkForNonRaceTrophies(avId, history))
        newTrophies.sort()
        return newTrophies

    def checkForNonRaceTrophies(self, avId, inHistory=None):
        self.notify.debug('CHECKING FOR NONRACE TROPHIES')
        self.notify.debug('GrandTouring: Checking for non-race trophies %s' % avId)
        av = self.air.doId2do.get(avId)
        if not av:
            self.notify.debug('NO AV %s' % avId)
            self.notify.debug("GrandTouring: can't convert avId to Av %s" % avId)
            return []
        trophies = av.getKartingTrophies()
        if inHistory:
            history = inHistory
        else:
            history = av.getKartingHistory()
        newTrophies = []
        self.notify.debug('GrandTouring: history-- %s' % history)
        self.notify.debug('GrandTouring: trophies- %s' % trophies)
        addTrophyCount = 0
        if not trophies[RaceGlobals.GrandTouring]:
            self.notify.debug('checking for grand touring')
            self.notify.debug('GrandTouring: checking for grand touring %s' % trophies[RaceGlobals.GrandTouring])
            best = av.getKartingPersonalBestAll()
            self.notify.debug('personal best %s' % best)
            self.notify.debug('GrandTouring: checking personal best %s' % best)
            counter = 0
            for time in best:
                if not time == 0:
                    counter += 1

            self.notify.debug('counter %s tracks %s' % (counter, len(RaceGlobals.TrackDict)))
            self.notify.debug('GrandTouring: bests comparison counter: %s tracks: %s' % (counter, len(RaceGlobals.TrackDict)))
            if counter >= len(RaceGlobals.TrackDict):
                newTrophies.append(RaceGlobals.GrandTouring)
                addTrophyCount += 1
                self.air.writeServerEvent('kartingTrophy', avId, '%s' % RaceGlobals.GrandTouring)
                self.notify.debug('trophy: ' + TTLocalizer.KartTrophyDescriptions[RaceGlobals.GrandTouring])
                self.notify.debug('GrandTouring: awarding grand touring new trophies %s' % newTrophies)
        else:
            self.notify.debug('already has grandtouring')
            self.notify.debug('trophies %s' % trophies)
            self.notify.debug('GrandTouring: already has grand touring %s' % trophies[RaceGlobals.GrandTouring])
        for i in range(1, RaceGlobals.NumTrophies // RaceGlobals.TrophiesPerCup + 1):
            cupNum = (trophies[:RaceGlobals.NumTrophies].count(1) + addTrophyCount) // (i * RaceGlobals.TrophiesPerCup)
            self.notify.debug('cupNum: %s' % cupNum)
            trophyIndex = RaceGlobals.TrophyCups[i - 1]
            if cupNum and not trophies[trophyIndex]:
                newTrophies.append(trophyIndex)
                oldMaxHp = av.getMaxHp()
                newMaxHp = min(ToontownGlobals.MaxHpLimit, oldMaxHp + 1)
                self.notify.debug('cup awarded! new max laff : %s' % newMaxHp)
                av.b_setMaxHp(newMaxHp)
                av.toonUp(newMaxHp)
                self.air.writeServerEvent('kartingTrophy', avId, '%s' % trophyIndex)
                self.notify.debug('trophy: ' + TTLocalizer.KartTrophyDescriptions[trophyIndex])

        self.notify.debug('NONRACE TROPHIES %s' % newTrophies)
        return newTrophies

    def checkHistoryForTrophyByValue(self, trophies, history, historyIndexValue, trophyReqList, trophyIndices):
        newTrophies = []
        self.notify.debug('Checking History for Trophy')
        self.notify.debug('Index %s Num %s ReqList %s Indices %s' % (0, historyIndexValue, trophyReqList, trophyIndices))
        for index in range(len(trophyIndices)):
            if not trophies[trophyIndices[index]]:
                if historyIndexValue >= trophyReqList[index]:
                    trophies[trophyIndices[index]] = 1
                    newTrophies.append(trophyIndices[index])

        return newTrophies

    def checkHistoryForTrophy(self, trophies, history, historyIndex, trophyReqList, trophyIndices):
        newTrophies = []
        self.notify.debug('Checking History for Trophy')
        self.notify.debug('Index %s Num %s ReqList %s Indices %s' % (historyIndex, history[historyIndex], trophyReqList, trophyIndices))
        for index in range(len(trophyIndices)):
            if not trophies[trophyIndices[index]]:
                if history[historyIndex] >= trophyReqList[index]:
                    trophies[trophyIndices[index]] = 1
                    newTrophies.append(trophyIndices[index])

        return newTrophies

    def mergeHistories(self, historyA, historyB):
        newHistorySize = len(historyA)
        if len(historyB) > len(historyA):
            newHistorySize = historyB
        mergedHistory = []
        for index in range(newHistorySize):
            mergedHistory[index] = 0
            if len(historyA) > index:
                if historyA[index] > mergedHistory[index]:
                    historyA[index] = mergedHistory[index]
            if len(historyB) > index:
                if historyB[index] > mergedHistory[index]:
                    historyB[index] = mergedHistory[index]

        return mergedHistory

    def getNewSingleRaceHistory(self, race, avId, positionFinished):
        newHistory = 0
        av = self.air.doId2do.get(avId)
        if not av:
            return []
        history = av.getKartingHistory()
        trackGenre = RaceGlobals.getTrackGenre(race.trackId)
        winIndex = RaceGlobals.WinsList[trackGenre]
        winReqList = RaceGlobals.WonRaces
        qualIndex = RaceGlobals.QualsList[trackGenre]
        qualReqList = RaceGlobals.QualifiedRaces
        if history[winIndex] < winReqList[-1] and positionFinished == 1:
            history[winIndex] += 1
            self.notify.debug('New History Won!')
            newHistory = 1
        if history[qualIndex] < qualReqList[-1]:
            history[qualIndex] += 1
            self.notify.debug('New History Qualified!')
            newHistory = 1
        if newHistory:
            return history

    def getNewCircuitHistory(self, race, avId, positionFinished):
        newHistory = 0
        av = self.air.doId2do.get(avId)
        if not av:
            return []
        history = av.getKartingHistory()
        trackGenre = RaceGlobals.getTrackGenre(race.trackId)
        historyIndex = RaceGlobals.CircuitWins
        trophyReqList = RaceGlobals.WonCircuitRaces
        sweepIndices = RaceGlobals.CircuitSweepsList
        sweepReqList = RaceGlobals.SweptCircuitRaces
        self.notify.debug('getNewCircuitHistory: avId=%d positionFinished=%d history =%s' % (avId, positionFinished, history))
        if history[historyIndex] < trophyReqList[-1] and positionFinished == 1:
            history[historyIndex] += 1
            self.notify.debug('New History Won!')
            newHistory = 1
        swept = 0
        totalPoints = sum(race.circuitPoints[avId])
        if totalPoints == len(race.circuitPoints[avId]) * RaceGlobals.CircuitPoints[0]:
            swept = 1
        if swept:
            if history[RaceGlobals.CircuitSweeps] < sweepReqList[-1]:
                if not history[RaceGlobals.CircuitSweeps]:
                    history[RaceGlobals.CircuitSweeps] = 0
                history[RaceGlobals.CircuitSweeps] += 1
                self.notify.debug('New History Swept!')
                newHistory = 1
        qualified = 0
        self.notify.debug('qual times %s' % race.qualTimes)
        self.notify.debug('avatar times %s' % race.circuitTimeList[avId])
        qualified = 1
        self.notify.debug('End Race Circuit Time List %s' % race.circuitTimeList)
        self.notify.debug('check for qualify')
        for qual in race.circuitTimeList[avId]:
            self.notify.debug('qual %s' % qual)
            if qual[1] == -1:
                qualified = 0
                self.notify.debug('not qualified')

        if qualified:
            self.notify.debug('qualified has %s needs %s' % (history[RaceGlobals.CircuitQuals], RaceGlobals.QualifiedCircuitRaces[-1]))
            if history[RaceGlobals.CircuitQuals] < RaceGlobals.QualifiedCircuitRaces[-1]:
                history[RaceGlobals.CircuitQuals] += 1
                self.notify.debug('New History qualified!')
                newHistory = 1
        if newHistory:
            return history

    def raceOver(self, race, normalExit=True):
        if race in self.races:
            if normalExit and race.isCircuit() and not race.isLastRace():
                nextTrackId = race.circuitLoop[0]
                continuingAvs = []
                for avId in race.avIds:
                    if avId not in race.kickedAvIds:
                        continuingAvs.append(avId)

                lastRace = False
                if len(continuingAvs) > 0:
                    raceZone = self.createRace(nextTrackId, race.raceType, race.lapCount, continuingAvs, race.circuitLoop[1:], race.circuitPoints, race.circuitTimes, race.qualTimes, race.circuitTimeList, race.circuitTotalBonusTickets)
                    race.sendToonsToNextCircuitRace(raceZone, nextTrackId)
                else:
                    lastRace = True
                self.races.remove(race)
                race.requestDelete(lastRace)
            else:
                self.races.remove(race)
                race.requestDelete()

    def checkForTrophies(self, place, trackId, raceType, numRacers, avId):
        av = self.air.doId2do.get(avId)
        outHistory = av.getKartingHistory()
        trophies = av.getKartingTrophies()
        trophiesWon = []
        trackGenre = RaceGlobals.getTrackGenre(trackId)
        if place == 1:
            historyIndex = RaceGlobals.WinsList[trackGenre]
            trophyIndices = RaceGlobals.AllWinsList[trackGenre]
            trophyReqList = RaceGlobals.WonRaces
            historyTotalList = RaceGlobals.WinsList
            totalTrophyIndex = RaceGlobals.TotalWins
            totalReq = RaceGlobals.TotalWonRaces
            trophiesWon += self.checkForTrophy(place, trackId, raceType, numRacers, avId, historyIndex, trophyIndices, trophyReqList, historyTotalList, totalTrophyIndex, totalReq)
        historyIndex = RaceGlobals.QualsList[trackGenre]
        trophyIndices = RaceGlobals.AllQualsList[trackGenre]
        trophyReqList = RaceGlobals.QualifiedRaces
        historyTotalList = RaceGlobals.QualsList
        totalTrophyIndex = RaceGlobals.TotalQuals
        totalReq = RaceGlobals.TotalQualifiedRaces
        trophiesWon += self.checkForTrophy(place, trackId, raceType, numRacers, avId, historyIndex, trophyIndices, trophyReqList, historyTotalList, totalTrophyIndex, totalReq)
        if not trophies[RaceGlobals.GrandTouring]:
            self.notify.debug('checking for grand touring')
            best = av.getKartingPersonalBestAll()
            self.notify.debug('personal best %s' % best)
            counter = 0
            for time in best:
                if not time == 0:
                    counter += 1

            self.notify.debug('counter %s tracks %s' % (counter, len(RaceGlobals.TrackDict)))
            if counter >= len(RaceGlobals.TrackDict):
                trophiesWon.append(RaceGlobals.GrandTouring)
        if outHistory:
            av.b_setKartingHistory(outHistory)
        if len(trophiesWon):
            for trophy in trophiesWon:
                trophies[trophy] = 1

            av.b_setKartingTrophies(trophies)
        trophiesWon.sort()
        return trophiesWon

    def checkForTrophy(self, place, trackId, raceType, numRacers, avId, historyIndex, trophyIndices, trophyReqList, historyTotalList, totalTrophyIndex, totalReq):
        av = self.air.doId2do.get(avId)
        if not av:
            return []
        history = av.getKartingHistory()
        newHistory = 0
        trophies = av.getKartingTrophies()
        newTrophies = []
        if history[historyIndex] < trophyReqList[-1]:
            history[historyIndex] += 1
            newHistory = 1
        for i in range(0, len(trophyReqList)):
            if not trophies[trophyIndices[i]]:
                if history[historyIndex] == trophyReqList[i]:
                    trophies[trophyIndices[i]] = 1
                    newTrophies.append(trophyIndices[i])
                    self.air.writeServerEvent('kartingTrophy', avId, '%s' % trophyIndices[i])
                    self.notify.debug('trophy: ' + TTLocalizer.KartTrophyDescriptions[trophyIndices[i]])
                    break

        if not raceType == RaceGlobals.Circuit:
            if not trophies[totalTrophyIndex]:
                total = 0
                for i in historyTotalList:
                    total += history[i]

                self.notify.debug('checking for total trophy: %s >= %s' % (total, totalReq))
                if total >= totalReq:
                    trophies[totalTrophyIndex] = 1
                    newTrophies.append(totalTrophyIndex)
                    self.air.writeServerEvent('kartingTrophy', avId, '%s' % totalTrophyIndex)
                    self.notify.debug('trophy: ' + TTLocalizer.KartTrophyDescriptions[totalTrophyIndex])
        for i in range(1, RaceGlobals.NumTrophies // RaceGlobals.TrophiesPerCup + 1):
            cupNum = trophies[:RaceGlobals.NumTrophies].count(1) // (i * RaceGlobals.TrophiesPerCup)
            self.notify.debug('cupNum: %s' % cupNum)
            trophyIndex = RaceGlobals.TrophyCups[i - 1]
            if cupNum and not trophies[trophyIndex]:
                trophies[trophyIndex] = 1
                newTrophies.append(trophyIndex)
                oldMaxHp = av.getMaxHp()
                newMaxHp = min(ToontownGlobals.MaxHpLimit, oldMaxHp + 1)
                self.notify.debug('cup awarded! new max laff : %s' % newMaxHp)
                av.b_setMaxHp(newMaxHp)
                av.toonUp(newMaxHp)
                self.air.writeServerEvent('kartingTrophy', avId, '%s' % trophyIndex)
                self.notify.debug('trophy: ' + TTLocalizer.KartTrophyDescriptions[trophyIndex])

        self.notify.debug('newTrophies: %s' % newTrophies)
        self.notify.debug('trophies: %s' % trophies)
        self.notify.debug('kartingHistory: %s' % history)
        if newHistory:
            av.b_setKartingHistory(history)
        return newTrophies

    def checkPersonalBest(self, trackId, time, raceType, numRacers, avId):
        av = simbase.air.doId2do.get(avId)
        if av:
            bestTimes = av.getKartingPersonalBestAll()
            trackIndex = RaceGlobals.TrackIds.index(trackId)
            bestTime = bestTimes[trackIndex]
            self.notify.debug('thisTime: %s, bestTime: %s' % (time, bestTime))
            if bestTime == 0.0 or time < bestTime:
                bestTimes[trackIndex] = time
                self.notify.debug('new personal best!')
                av.b_setKartingPersonalBest(bestTimes)
                self.notify.debug('personal best: %s' % bestTimes)

    def checkTimeRecord(self, trackId, time, raceType, numRacers, avId):
        bonus = 0
        newRecord = 0
        for period in RaceGlobals.PeriodIds:
            for record in range(0, RaceGlobals.NumRecordsPerPeriod):
                recordTime = self.trackRecords[trackId][period][record][0]
                if time < recordTime:
                    newRecord = 1
                    self.notify.debug('new %s record!' % TTLocalizer.RecordPeriodStrings[period])
                    av = simbase.air.doId2do.get(avId)
                    if av:
                        name = av.name
                        self.trackRecords[trackId][period].insert(record, (time, raceType, numRacers, name))
                        self.trackRecords[trackId][period] = self.trackRecords[trackId][period][:RaceGlobals.NumRecordsPerPeriod]
                        self.updateLeaderboards(trackId, period)
                        bonus = RaceGlobals.PeriodDict[period]
                        self.air.writeServerEvent('kartingRecord', avId, '%s|%s|%s' % (period, trackId, time))
                    else:
                        self.notify.warning('warning: av not logged in!')
                    break

        if newRecord:
            self.updateRecordFile()
        return bonus

    def updateRecordFile(self):
        try:
            backup = self.filename + '.bu'
            if os.path.exists(self.filename):
                os.rename(self.filename, backup)
            file = open(self.filename, 'wb')
            file.seek(0)
            pickle.dump(self.trackRecords, file)
            file.close()
            if os.path.exists(backup):
                os.remove(backup)
        except EnvironmentError:
            self.notify.warning(str(sys.exc_info()[1]))

    def getFilename(self):
        return '%s%s.trackRecords' % (self.serverDataFolder, self.shard)

    def loadRecords(self):
        try:
            file = open(self.filename + '.bu', 'rb')
            if os.path.exists(self.filename):
                os.remove(self.filename)
        except IOError:
            try:
                file = open(self.filename, 'rb')
            except IOError:
                return self.getRecordTimes()

        file.seek(0)
        records = self.loadFrom(file)
        file.close()
        for trackId in RaceGlobals.TrackIds:
            if trackId not in records:
                records[trackId] = {}
                for i in RaceGlobals.PeriodIds:
                    records[trackId][i] = []
                    for j in range(0, RaceGlobals.NumRecordsPerPeriod):
                        records[trackId][i].append(RaceGlobals.getDefaultRecord(trackId))

        self.resetLeaderboards()
        return records

    def loadFrom(self, file):
        records = {}
        try:
            while 1:
                records = pickle.load(file)

        except EOFError:
            pass

        return records

    def getRecordTimes(self):
        records = {}
        for trackId in RaceGlobals.TrackIds:
            records[trackId] = {}
            for i in RaceGlobals.PeriodIds:
                records[trackId][i] = []
                for j in range(0, RaceGlobals.NumRecordsPerPeriod):
                    records[trackId][i].append(RaceGlobals.getDefaultRecord(trackId))

        return records

    def resetRecordPeriod(self, period):
        for trackId in RaceGlobals.TrackIds:
            for i in range(0, RaceGlobals.NumRecordsPerPeriod):
                self.trackRecords[trackId][period][i] = RaceGlobals.getDefaultRecord(trackId)

            self.updateLeaderboards(trackId, period)

        self.updateRecordFile()

    def getRecords(self, trackId, period):
        return self.trackRecords[trackId][period]

    def updateLeaderboards(self, trackId, period):
        messenger.send('UpdateRaceRecord', [(trackId, period)])

    def resetLeaderboards(self):
        for track in RaceGlobals.TrackIds:
            for period in RaceGlobals.PeriodIds:
                self.updateLeaderboards(track, period)


class KartRecordDailyResetter(HolidayBaseAI.HolidayBaseAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('ResistanceEventMgrAI')
    PostName = 'kertRecordDailyReset'

    def __init__(self, air, holidayId):
        HolidayBaseAI.HolidayBaseAI.__init__(self, air, holidayId)

    def start(self):
        bboard.post(KartRecordDailyResetter.PostName)
        simbase.air.raceMgr.resetRecordPeriod(RaceGlobals.Daily)

    def stop(self):
        bboard.remove(KartRecordDailyResetter.PostName)


class KartRecordWeeklyResetter(HolidayBaseAI.HolidayBaseAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('ResistanceEventMgrAI')
    PostName = 'kartRecordWeeklyReset'

    def __init__(self, air, holidayId):
        HolidayBaseAI.HolidayBaseAI.__init__(self, air, holidayId)

    def start(self):
        bboard.post(KartRecordWeeklyResetter.PostName)
        simbase.air.raceMgr.resetRecordPeriod(RaceGlobals.Weekly)

    def stop(self):
        bboard.remove(KartRecordWeeklyResetter.PostName)


class CircuitRaceHolidayMgr(HolidayBaseAI.HolidayBaseAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('CircuitRaceHolidayMgr')
    PostName = 'CircuitRaceHoliday'
    StartStopMsg = 'CircuitRaceHolidayStartStop'

    def __init__(self, air, holidayId):
        HolidayBaseAI.HolidayBaseAI.__init__(self, air, holidayId)

    def start(self):
        bboard.post(CircuitRaceHolidayMgr.PostName, True)
        simbase.air.newsManager.circuitRaceStart()
        messenger.send(CircuitRaceHolidayMgr.StartStopMsg)

    def stop(self):
        bboard.remove(CircuitRaceHolidayMgr.PostName)
        simbase.air.newsManager.circuitRaceEnd()
        messenger.send(CircuitRaceHolidayMgr.StartStopMsg)
