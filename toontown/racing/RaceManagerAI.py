from direct.directnotify import DirectNotifyGlobal
from . import DistributedRaceAI
from toontown.toonbase import ToontownGlobals, TTLocalizer
from toontown.coghq import MintLayout
from toontown.ai import HolidayBaseAI
from direct.showbase import DirectObject
from . import RaceGlobals
import random
import os
import pickle

def getDefaultRecord(trackId):
    """
    Get the default record for this track. Used for reseting records.
    """
    # format: time, race type, num racers, racer name
    return (RaceGlobals.getDefaultRecordTime(trackId), 0, 1, TTLocalizer.Goofy)

class RaceManagerAI(DirectObject.DirectObject):

    notify = DirectNotifyGlobal.directNotify.newCategory('RaceManagerAI')
    
    serverDataFolder = simbase.config.GetString('server-data-folder', "")

    SuspiciousPercent = 0.15 # what percent of qualifying time counts as suspicious
        
    def __init__(self, air):
        DirectObject.DirectObject.__init__(self)
        self.air = air
        self.races = []
        self.shard = str(air.districtId)
        self.filename = self.getFilename()
        self.trackRecords = self.loadRecords()
        
    def getDoId(self):
        # DistributedElevatorAI needs this
        return 0

    def createRace(self, trackId, raceType, laps, players, circuitLoop, circuitPoints, circuitTimes, qualTimes = [], circuitTimeList = {}, circuitTotalBonusTickets = {}):
        #print('Creating Race: circuit Points %s' % circuitPoints)
        assert self.notify.debug("createRace: players = %s" % players)
        raceZone = self.air.allocateZone()
        race = DistributedRaceAI.DistributedRaceAI(
            self.air, trackId, raceZone, players, laps, raceType,
            self.exitedRace, self.raceOver,
            circuitLoop, circuitPoints, circuitTimes, qualTimes, circuitTimeList, circuitTotalBonusTickets)
        race.generateWithRequired(raceZone)
        # TODO: where should this be stored?
        race.playersFinished = []
        race.lastTotalTime = 0
        self.races.append(race)
        return raceZone

    def exitedRace(self, race, playerInfo):
        # The Object returned here, playerInfo, is a Racer object,
        # and can be found in Racer.py

        self.notify.debug("exited race: %s" % playerInfo.avId)
        
        # calculate total race time 
        totalTime=playerInfo.totalTime

        entryFee = 0
        bonus = 0
        placeMultiplier=0
        qualify = 0
        winnings = 0
        trophies = []
        points = []
        newHistory = None
        suspicious = False # if True, his time is suspiciously low
        
        # determine their place
        race.playersFinished.append(playerInfo.avId)
        place = len(race.playersFinished)
        self.notify.debug( "place: %s of %s" % (place, race.toonCount) )  

        self.notify.debug("pre-tie totalTime: %s" % totalTime)
        
        # HACK: make sure they don't tie
        if totalTime <= race.lastTotalTime:
            totalTime = race.lastTotalTime + 0.01
        race.lastTotalTime = totalTime

        self.notify.debug("totalTime: %s, qualify: %s" % (totalTime, RaceGlobals.getQualifyingTime(race.trackId) ))
        
        # update this player's total time for this set of races
        circuitTime = totalTime + race.circuitTimes.get(playerInfo.avId, 0)
        race.circuitTimes[playerInfo.avId] = circuitTime
        
        # keep track of the players time
        if not race.circuitTimeList.get(playerInfo.avId):
            race.circuitTimeList[playerInfo.avId] = []
        race.circuitTimeList[playerInfo.avId].append([totalTime, 0])
        self.notify.debug("CircuitTimeList %s" % (race.circuitTimeList))

        # update circuit points
        if race.raceType == RaceGlobals.Circuit:
            points = race.circuitPoints.get(playerInfo.avId, [])
            points.append(RaceGlobals.CircuitPoints[place-1])
            race.circuitPoints[playerInfo.avId] = points

        currentTimeIndex = len(race.circuitTimeList[playerInfo.avId]) -1
        # if they qualified
        if totalTime <= RaceGlobals.getQualifyingTime(race.trackId):
            race.circuitTimeList[playerInfo.avId][currentTimeIndex][1] = 1
            self.notify.debug("Racer Qualified time: %s required: %s" % (totalTime, RaceGlobals.getQualifyingTime(race.trackId)))
            # set the flag for the gui
            qualify = 1
            
            # see if the broke a personal record
            self.checkPersonalBest(race.trackId, totalTime, race.raceType, race.toonCount, playerInfo.avId)

            # check for suspiciousTime
            qualTime = RaceGlobals.getQualifyingTime(race.trackId)
            threshold = qualTime * self.SuspiciousPercent
            if totalTime < threshold:
                self.air.writeServerEvent("kartingSuspiciousRacer", playerInfo.avId, "%s|%s" % (race.trackId,totalTime))
                suspicious = True

            # you can only place if you beat qualifying time and you are NOT practicing
            if race.raceType == RaceGlobals.Practice:
                winnings = RaceGlobals.PracticeWinnings
                self.notify.debug("GrandTouring: Checking from branch: practice %s" % (playerInfo.avId))
                trophies = self.checkForNonRaceTrophies(playerInfo.avId)
            
                if trophies:
                    # need to update the history from a list of trophiesWon
                    self.updateTrophiesFromList(playerInfo.avId, trophies)
            else:
                # keep track of placemnet for contests
                self.air.writeServerEvent("kartingPlaced", playerInfo.avId, "%s|%s" % (place, race.toonCount))

                if race.raceType != RaceGlobals.Circuit:
                    # calculate their winnings
                    entryFee = RaceGlobals.getEntryFee(race.trackId, race.raceType)
                    placeMultiplier = RaceGlobals.Winnings[(place - 1) + (RaceGlobals.MaxRacers - race.toonCount)]
                    winnings = int(entryFee * placeMultiplier)

                    # win any trophies?
                    #trophies = self.checkForTrophies(place, race.trackId, race.raceType, race.toonCount, playerInfo.avId)
                    # update history
                    newHistory = self.getNewSingleRaceHistory(race, playerInfo.avId, place)
                    av = self.air.doId2do.get(playerInfo.avId)
                    if newHistory:
                        self.notify.debug("history %s" % (newHistory))
                        av.b_setKartingHistory(newHistory)
                        # win any trophies?
                        trophies = self.checkForRaceTrophies(race, playerInfo.avId)
                    else:
                        trophies = self.checkForNonRaceTrophies(playerInfo.avId)
                    
                    if trophies:
                        # need to update the history from a list of trophiesWon
                        self.updateTrophiesFromList(playerInfo.avId, trophies)
                    

                # see if they broke a server record
                if not suspicious:
                    bonus = self.checkTimeRecord(race.trackId, totalTime, race.raceType, race.toonCount, playerInfo.avId)
                    if (race.circuitTotalBonusTickets.has_key(playerInfo.avId)):
                        race.circuitTotalBonusTickets[playerInfo.avId] += bonus
                    else:
                        race.circuitTotalBonusTickets[playerInfo.avId] = bonus                
                    
            # set the tickets on the toon
            av = self.air.doId2do.get(playerInfo.avId)
            if av:
                oldTickets = av.getTickets()
                self.notify.debug( "old tickets: %s" % oldTickets )
                newTickets = oldTickets + winnings + entryFee + bonus
                # Write to the server log
                self.air.writeServerEvent("kartingTicketsWon", playerInfo.avId, "%s" % (newTickets - oldTickets))
                self.notify.debug( "entry fee: %s" % entryFee )
                self.notify.debug( "place mult: %s" % placeMultiplier )
                self.notify.debug( "winnings: %s" % winnings )
                self.notify.debug( "bonus: %s" % bonus )
                self.notify.debug( "new tickets: %s" % newTickets )
                self.notify.debug( "circuit points: %s" % points )
                self.notify.debug( "circuit time: %s" % circuitTime )
                self.notify.debug( "circuitTotalBonusTickets: %s" % race.circuitTotalBonusTickets)
                av.b_setTickets(newTickets)
                
        else:
            race.circuitTimeList[playerInfo.avId][currentTimeIndex][1] = -1
            self.notify.debug("GrandTouring: Checking from branch: Not Qualified %s" % (playerInfo.avId))
            trophies = self.checkForNonRaceTrophies(playerInfo.avId)
            
            if trophies:
                # need to update the history from a list of trophiesWon
                self.updateTrophiesFromList(playerInfo.avId, trophies)
            
        # report the good news!
        if(race in self.races):
            race.d_setPlace(playerInfo.avId,
                            totalTime,
                            place,
                            entryFee,
                            qualify,
                            winnings,
                            bonus,
                            trophies,
                            points,
                            circuitTime)

            # handle the end of a circuit race
            if race.isCircuit():
                self.notify.debug("isCircuit")
                if race.everyoneDone():
                    self.notify.debug("everyoneDone")
                    #doing this immediately kills showing the breaking a record sequence.
                    #it's a problem only when the last player in the 3rd race breaks a record
                    if race.isLastRace():                   
                        taskMgr.doMethodLater(10,self.endCircuitRace,"DelayEndCircuitRace=%d" % race.doId , (race,bonus))
                    else:
                        self.endCircuitRace(race, bonus)
            else:
                self.notify.debug("not isCircuit")
                
              
            #trophies.extend(self.checkForNonRaceTrophies(playerInfo.avId, newHistory))

                
        
    def endCircuitRace(self, race, bonus = 0):
        self.notify.debug("endCircuitRace")
        # look at all the points and decide the standings
        pointTotals = []
        for avId in race.circuitPoints:
            pointTotals.append([avId, sum(race.circuitPoints[avId])])

        # do a quick n dirty bubble sort (first place -> last place)
        numVals = len(pointTotals)
        finalStandings = []

        def swap(x, y):
            t = pointTotals[x]
            pointTotals[x] = pointTotals[y]
            pointTotals[y] = t

        # the old bubble sort seemed wonky - grabbed this one from wikisource! =]
        
        for i in range(numVals-1,0,-1):
            for j in range(i):
                if pointTotals[j][1] < pointTotals[j+1][1]:
                    swap(j, j+1)
                elif pointTotals[j][1] == pointTotals[j+1][1]:
                    # ties are resolved via totalTimes
                    avId1 = pointTotals[j][0]
                    avId2 = pointTotals[j+1][0]
                    if race.circuitTimes[avId1] > race.circuitTimes[avId2]:
                        swap(j,j+1)

        # don't trust grabbing them out while sorting
        for i in range(numVals):
            finalStandings.append(pointTotals[i][0])

        self.notify.debug("Final standings %s" % (finalStandings))
        # check for trophies, apply winnings, etc.
        for avId in finalStandings:
            self.notify.debug("avId %s" % (avId))

            place = finalStandings.index(avId) + 1
            places = len(finalStandings)
            winnings = 0
            trophies = []

            if race.isLastRace():
                self.notify.debug("isLastRace")
                # make sure we don't reward any disconnected racers
                av = self.air.doId2do.get(avId)
                if av and (avId in race.playersFinished):
                    # keep track of placement for contests
                    self.air.writeServerEvent("kartingCircuitFinished", avId, "%s|%s|%s|%s" % (place, places, race.circuitTimes[avId], race.trackId))
                    print("kartingCircuitFinished", avId, "%s|%s|%s|%s" % (place, places, race.circuitTimes[avId], race.trackId))

                    # calculate their winnings
                    entryFee = RaceGlobals.getEntryFee(race.trackId, race.raceType)
                    placeMultiplier = RaceGlobals.Winnings[(place - 1) + (RaceGlobals.MaxRacers - places)]
                    winnings = int(entryFee * placeMultiplier)
                    
                    # update history
                    newHistory = self.getNewCircuitHistory(race, avId, place)
                    if newHistory:
                        self.notify.debug("history %s" % (newHistory))
                        # win any trophies?
                        trophies = self.checkForCircuitTrophies(race, avId, newHistory)
                        av.b_setKartingHistory(newHistory)
                        
                    else:
                        self.notify.debug("no new history") 
                        trophies = self.checkForNonRaceTrophies(avId)
                        
                    if trophies:
                        # need to update the history from a list of trophiesWon
                        self.updateTrophiesFromList(avId, trophies)    

                    oldTickets = av.getTickets()
                    self.notify.debug( "endCircuitRace: old tickets: %s" % oldTickets )
                    newTickets = oldTickets + winnings + entryFee
                    # Write to the server log
                    self.air.writeServerEvent("kartingTicketsWonCircuit", avId, "%s" % (newTickets - oldTickets))
                    self.notify.debug( "entry fee: %s" % entryFee )
                    self.notify.debug( "place mult: %s" % placeMultiplier )
                    self.notify.debug( "winnings: %s" % winnings )
                    self.notify.debug( "new tickets: %s" % newTickets )
                    self.notify.debug( "trophies: %s" % trophies )
                    self.notify.debug( "bonus: %s" % bonus)
                    av.b_setTickets(newTickets)

                    finalBonus = 0
                    if (race.circuitTotalBonusTickets.has_key(avId)):
                        finalBonus = race.circuitTotalBonusTickets[avId]
                        
                    #race.d_setCircuitPlace(avId, place, entryFee, winnings, bonus, trophies)
                    race.d_setCircuitPlace(avId, place, entryFee, winnings, finalBonus, trophies)                    

        race.playersFinished = finalStandings
        race.d_endCircuitRace()
        
    def updateTrophiesFromList(self, avId, trophies):
        self.air.writeServerEvent("Writing Trophies: Updating trophies from list", avId, "%s" % (trophies))
        av = self.air.doId2do.get(avId)
        if not av:
            return
        if not trophies:
            return
        trophyField = av.getKartingTrophies()
        for trophy in trophies:
            trophyField[trophy] = 1
        av.b_setKartingTrophies(trophyField)
        
        
    def checkForCircuitTrophies(self, race, avId, inHistory = None):
        #checks for qualify, win, and sweep trophies for curcuit races
        #returns a list of new trophies

        #check and retrieve the needed data

        av = self.air.doId2do.get(avId)
        if not av:
            return []

        trophies = av.getKartingTrophies()
        if inHistory:
            history = inHistory
        else:
            history = av.getKartingHistory()
            
        #trackGenre = RaceGlobals.getTrackGenre(race.trackId)

        #setup the test groups: wins, sweeps, and qualifies

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

        #check to see which win trophies are won
        newTrophies.extend(self.checkHistoryForTrophy(trophies, history, winIndex, winReqList, winIndices))

        #check to see which sweep trophies are won
        newTrophies.extend(self.checkHistoryForTrophy(trophies, history, sweepIndex, sweepReqList, sweepIndices))

        #check to see which qualify trophies are won
        newTrophies.extend(self.checkHistoryForTrophy(trophies, history, qualIndex, qualReqList, qualIndices))
        self.notify.debug("GrandTouring: Checking from branch: Circuit %s" % (avId))
        newTrophies.extend(self.checkForNonRaceTrophies(avId, history))
        newTrophies.sort()

        return newTrophies
        
    def checkForRaceTrophies(self, race, avId, inHistory = None):
        #checks for single race win and qualified trophies
        
        #check and retrieve the needed data
        
        av = self.air.doId2do.get(avId)
        if not av:
            return []

        trophies = av.getKartingTrophies()
        if inHistory:
            history = inHistory
        else:
            history = av.getKartingHistory()
            
        newTrophies = []
            
        #check for genre wins trophies
        numTrackGenres = len(RaceGlobals.WinsList)
        for genre in range(numTrackGenres):
            singleGenreNewTrophies = self.checkHistoryForTrophy(trophies,
                                                            history, 
                                                            RaceGlobals.WinsList[genre], 
                                                            RaceGlobals.WonRaces,
                                                            RaceGlobals.AllWinsList[genre])
            newTrophies.extend(singleGenreNewTrophies)
        
        #check for genre quals trophies
        numTrackGenres = len(RaceGlobals.QualsList)
        for genre in range(numTrackGenres):
            singleGenreNewTrophies = self.checkHistoryForTrophy(trophies,
                                                            history, 
                                                            RaceGlobals.QualsList[genre], 
                                                            RaceGlobals.QualifiedRaces,
                                                            RaceGlobals.AllQualsList[genre])
            newTrophies.extend(singleGenreNewTrophies)
            
        #check for total wins trophy
        totalWins = 0
        for genre in range(numTrackGenres):
            totalWins += history[RaceGlobals.WinsList[genre]]
        
        singleGenreNewTrophies = self.checkHistoryForTrophyByValue(trophies,
                                                history, 
                                                totalWins, 
                                                [RaceGlobals.TotalWonRaces],
                                                [RaceGlobals.TotalWins])
        newTrophies.extend(singleGenreNewTrophies)
        
        #check for total quals trophy
        totalQuals = 0
        for genre in range(numTrackGenres):
            totalQuals += history[RaceGlobals.QualsList[genre]]
        
        singleGenreNewTrophies = self.checkHistoryForTrophyByValue(trophies,
                                                history, 
                                                totalQuals, 
                                                [RaceGlobals.TotalQualifiedRaces],
                                                [RaceGlobals.TotalQuals])
        newTrophies.extend(singleGenreNewTrophies)
        self.notify.debug("GrandTouring: Checking from branch: Race %s " % (avId))
        newTrophies.extend(self.checkForNonRaceTrophies(avId, history))
        newTrophies.sort()
            
        return newTrophies
        
    def checkForNonRaceTrophies(self, avId, inHistory = None):
        #checks for race independent trophies like laff cups
        self.notify.debug("CHECKING FOR NONRACE TROPHIES")
        self.notify.debug("GrandTouring: Checking for non-race trophies %s" % (avId))
        
        #check and retrieve the needed data
        
        av = self.air.doId2do.get(avId)
        if not av:
            self.notify.debug("NO AV %s" % (avId))
            self.notify.debug("GrandTouring: can't convert avId to Av %s" % (avId))
            return []

        trophies = av.getKartingTrophies()
        if inHistory:
            history = inHistory
        else:
            history = av.getKartingHistory()
            
        newTrophies = []
        self.notify.debug("GrandTouring: history-- %s" % (history))
        self.notify.debug("GrandTouring: trophies- %s" % (trophies))
        
        addTrophyCount = 0
        
        #check for grandtouring
        if not trophies[RaceGlobals.GrandTouring]:
            self.notify.debug("checking for grand touring")
            self.notify.debug("GrandTouring: checking for grand touring %s" % (trophies[RaceGlobals.GrandTouring]))
            #import pdb; pdb.set_trace()
            best = av.getKartingPersonalBestAll()
            self.notify.debug("personal best %s" % (best))
            self.notify.debug("GrandTouring: checking personal best %s" % (best))
            counter = 0
            for time in best:
                if not time == 0:
                    counter +=1
            self.notify.debug("counter %s tracks %s" % (counter, len(RaceGlobals.TrackDict)))
            self.notify.debug("GrandTouring: bests comparison counter: %s tracks: %s" % (counter, len(RaceGlobals.TrackDict)))
            if counter >= len(RaceGlobals.TrackDict):
                newTrophies.append(RaceGlobals.GrandTouring)
                addTrophyCount += 1
                self.air.writeServerEvent("kartingTrophy", avId, "%s" % (RaceGlobals.GrandTouring))
                self.notify.debug( "trophy: " + TTLocalizer.KartTrophyDescriptions[RaceGlobals.GrandTouring] )
                self.notify.debug("GrandTouring: awarding grand touring new trophies %s" % (newTrophies))
        else:
            self.notify.debug("already has grandtouring")
            self.notify.debug("trophies %s" % (trophies))
            self.notify.debug("GrandTouring: already has grand touring %s" % (trophies[RaceGlobals.GrandTouring]))
        
        # check to see if we need a laff point
        for i in range(1, RaceGlobals.NumTrophies/RaceGlobals.TrophiesPerCup + 1):
            cupNum = (trophies[:RaceGlobals.NumTrophies].count(1) + addTrophyCount) / (i * RaceGlobals.TrophiesPerCup)
            self.notify.debug( "cupNum: %s" % cupNum)
            trophyIndex = RaceGlobals.TrophyCups[i - 1]
            if cupNum and not trophies[trophyIndex]:
                # award the cup!
                #trophies[trophyIndex] = 1
                newTrophies.append(trophyIndex)
                # laff point boost!
                oldMaxHp = av.getMaxHp()
                newMaxHp = min(ToontownGlobals.MaxHpLimit, oldMaxHp + 1)
                self.notify.debug( "cup awarded! new max laff : %s" % newMaxHp)
                av.b_setMaxHp(newMaxHp)
                # Also, give them a full heal
                av.toonUp(newMaxHp)
                # Write to the server log
                self.air.writeServerEvent("kartingTrophy", avId, "%s" % (trophyIndex))
                self.notify.debug( "trophy: " + TTLocalizer.KartTrophyDescriptions[trophyIndex] )
            
        self.notify.debug("NONRACE TROPHIES %s" % (newTrophies))
        return newTrophies
        
    def checkHistoryForTrophyByValue(self, trophies, history, historyIndexValue, trophyReqList, trophyIndices):
        #takes the index of the history we are interested in "number of wins etc.."
        #compares it to a list of required wins for each stage
        #and returns the new trophy indices won at each stage

        newTrophies = []
        self.notify.debug("Checking History for Trophy")
        self.notify.debug("Index %s Num %s ReqList %s Indices %s" % (0, historyIndexValue, trophyReqList, trophyIndices))
        for index in range(len(trophyIndices)):
            if not trophies[trophyIndices[index]]:
                if historyIndexValue >= trophyReqList[index]:
                    trophies[trophyIndices[index]] = 1
                    newTrophies.append(trophyIndices[index])
        return newTrophies
            
        
    def checkHistoryForTrophy(self, trophies, history, historyIndex, trophyReqList, trophyIndices):
        #takes the index of the history we are interested in "number of wins etc.."
        #compares it to a list of required wins for each stage
        #and returns the new trophy indices won at each stage

        newTrophies = []
        self.notify.debug("Checking History for Trophy")
        self.notify.debug("Index %s Num %s ReqList %s Indices %s" % (historyIndex, history[historyIndex], trophyReqList, trophyIndices))
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
        
        #win history
        if history[winIndex] < winReqList[-1] and positionFinished == 1:
            history[winIndex] += 1
            self.notify.debug("New History Won!")
            newHistory = 1
            
        #qual history
        if history[qualIndex] < qualReqList[-1]:
            history[qualIndex] += 1
            self.notify.debug("New History Qualified!")
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

        self.notify.debug("getNewCircuitHistory: avId=%d positionFinished=%d history =%s" % (avId, positionFinished, history))

        #win history
        if history[historyIndex] < trophyReqList[-1] and positionFinished == 1:
            history[historyIndex] += 1
            self.notify.debug("New History Won!")
            newHistory = 1


        #sweep history
        #first determine if a sweep occured ~ if the player has maximum points
        swept = 0
        totalPoints = sum(race.circuitPoints[avId])
        if totalPoints == len(race.circuitPoints[avId]) * RaceGlobals.CircuitPoints[0]:
            swept = 1

        #increment the sweep history if it's not maxed ~ reached the highest requirement
        if swept:
            if history[RaceGlobals.CircuitSweeps] < sweepReqList[-1]:
                if not history[RaceGlobals.CircuitSweeps]:
                    history[RaceGlobals.CircuitSweeps] = 0
                history[RaceGlobals.CircuitSweeps] += 1
                self.notify.debug("New History Swept!")
                newHistory = 1

        #qual history
        #first determine if the player qualified for all their circuit races
        qualified = 0
        #check to see if the avatar has a time for each race
        self.notify.debug("qual times %s" % (race.qualTimes))
        self.notify.debug("avatar times %s" % (race.circuitTimeList[avId]))
        #if len(race.qualTimes) <= len(race.circuitTimeList[avId]):
        qualified = 1
        self.notify.debug("End Race Circuit Time List %s" % (race.circuitTimeList))
        self.notify.debug("check for qualify")
        for qual in race.circuitTimeList[avId]:
            self.notify.debug("qual %s" % (qual))
            if qual[1] == -1:
                qualified = 0
                self.notify.debug("not qualified")

        #increment the qualify history if it's not maxed ~ reached the highest requirement
        if qualified:
            self.notify.debug("qualified has %s needs %s" % (history[RaceGlobals.CircuitQuals], RaceGlobals.QualifiedCircuitRaces[-1]))
            if history[RaceGlobals.CircuitQuals] < RaceGlobals.QualifiedCircuitRaces[-1]:
                history[RaceGlobals.CircuitQuals] += 1
                self.notify.debug("New History qualified!")
                newHistory = 1

        if newHistory:
            return history
        

    def raceOver(self, race, normalExit = True):
        assert self.notify.debug("raceOver: race.doId=%d normalExit=%s" % (race.doId, normalExit))
        if(race in self.races):
            if normalExit and race.isCircuit() and not race.isLastRace():
                nextTrackId = race.circuitLoop[0]
                assert self.notify.debug("raceOver: creating a new race %d" % nextTrackId)                
                continuingAvs = []
                for avId in race.avIds:
                    if not avId in race.kickedAvIds:
                        continuingAvs.append(avId)

                assert self.notify.debug("race.kickedAvIds=%s continuingAvs = %s" % (race.kickedAvIds,continuingAvs))
                lastRace = False
                if len(continuingAvs) > 0:
                    raceZone = self.createRace( nextTrackId,
                                            race.raceType,
                                            race.lapCount,
                                            continuingAvs,
                                            race.circuitLoop[1:],
                                            race.circuitPoints,
                                            race.circuitTimes,
                                            race.qualTimes,
                                            race.circuitTimeList,
                                            race.circuitTotalBonusTickets)
                
                    race.sendToonsToNextCircuitRace(raceZone, nextTrackId)
                else:
                    lastRace = True
                    assert self.notify.debug("no avatars to continue race, not creating a new one")
                
                    
                assert self.notify.debug("removing race %d" % race.doId)
                self.races.remove(race)

                
                race.requestDelete(lastRace)
            else:
                assert self.notify.debug("removing race %d" % race.doId)                
                self.races.remove(race)
                race.requestDelete()

    def checkForTrophies(self, place, trackId, raceType, numRacers, avId):
        """Update race history and award trophies if necessary"""
        
        # I have tried my best to abstract this so that checking for all trophies can be done
        # by this one for loop. By maintaining some strategic lists of indices in RaceGlobals
        # I avoided a ridiculously long cascade of if-else statements. I apologize if it
        # seems obtuse - grw


        
        av = self.air.doId2do.get(avId)
        outHistory = av.getKartingHistory()
        trophies = av.getKartingTrophies()
        trophiesWon = []
        
        # determine track type
        trackGenre = RaceGlobals.getTrackGenre(trackId)
        # win
        if place == 1:
            historyIndex = RaceGlobals.WinsList[trackGenre]
            trophyIndices = RaceGlobals.AllWinsList[trackGenre]
            trophyReqList = RaceGlobals.WonRaces
            historyTotalList = RaceGlobals.WinsList
            totalTrophyIndex = RaceGlobals.TotalWins
            totalReq = RaceGlobals.TotalWonRaces
            # check for win trophies
            trophiesWon += self.checkForTrophy(place, trackId, raceType, numRacers, avId,
                                               historyIndex, trophyIndices, trophyReqList,
                                               historyTotalList, totalTrophyIndex, totalReq)
            
        # quals
        #circuit quals cannot use checkfortrophy because it assumes you get a qual if you get anything

        historyIndex = RaceGlobals.QualsList[trackGenre]
        trophyIndices = RaceGlobals.AllQualsList[trackGenre]
        trophyReqList = RaceGlobals.QualifiedRaces
        historyTotalList = RaceGlobals.QualsList
        totalTrophyIndex = RaceGlobals.TotalQuals
        totalReq = RaceGlobals.TotalQualifiedRaces
        trophiesWon += self.checkForTrophy(place, trackId, raceType, numRacers, avId,
                                            historyIndex, trophyIndices, trophyReqList,
                                            historyTotalList, totalTrophyIndex, totalReq)

        # check for qual trophies
        
        #check for grandtouring
        if not trophies[RaceGlobals.GrandTouring]:
            self.notify.debug("checking for grand touring")
            #import pdb; pdb.set_trace()
            best = av.getKartingPersonalBestAll()
            self.notify.debug("personal best %s" % (best))
            counter = 0
            for time in best:
                if not time == 0:
                    counter +=1
            self.notify.debug("counter %s tracks %s" % (counter, len(RaceGlobals.TrackDict)))
            if counter >= len(RaceGlobals.TrackDict):
                trophiesWon.append(RaceGlobals.GrandTouring)                
            
        # set the new trophies and history if changed

        if outHistory:
            av.b_setKartingHistory(outHistory)
        if len(trophiesWon):
            for trophy in trophiesWon:
                trophies[trophy] = 1
            av.b_setKartingTrophies(trophies)
        
        trophiesWon.sort()
        return trophiesWon
            
    def checkForTrophy(self, place, trackId, raceType, numRacers, avId, historyIndex, trophyIndices, trophyReqList,
                       historyTotalList, totalTrophyIndex, totalReq):
        """Update race history and award trophies if necessary"""

        av = self.air.doId2do.get(avId)
        if not av:
            return []
        history = av.getKartingHistory()
        newHistory = 0
        trophies = av.getKartingTrophies()
        newTrophies = []

        # If the number of races the player has completed is less than the most needed for any trophy,
        # then add this race to players race history (keeps us from adding up to infinity)
        if history[historyIndex] < trophyReqList[-1]:
            history[historyIndex] += 1
            newHistory = 1

        # check for all three laff point trophies
        for i in range(0, len(trophyReqList)):
            if not trophies[trophyIndices[i]]:
                #self.notify.debug( "checking for trophy: %s == %s" %  (history[historyIndex], trophyReqList[i]))
                if history[historyIndex] == trophyReqList[i]:
                    trophies[trophyIndices[i]] = 1
                    newTrophies.append(trophyIndices[i])
                    # Write to the server log
                    self.air.writeServerEvent("kartingTrophy", avId, "%s" % (trophyIndices[i]))
                    self.notify.debug( "trophy: " + TTLocalizer.KartTrophyDescriptions[trophyIndices[i]] )
                    break

        # if this is not tourney, count toward total wins
        if not raceType == RaceGlobals.Circuit:
            # now check for total wins style trophies
            if not trophies[totalTrophyIndex]:
                total = 0
                # calculate total since its not stored explicitly
                for i in historyTotalList:
                    total += history[i]
                self.notify.debug( "checking for total trophy: %s >= %s" % (total, totalReq))
                if total >= totalReq:
                    trophies[totalTrophyIndex] = 1
                    newTrophies.append(totalTrophyIndex)
                        
                    # Write to the server log
                    self.air.writeServerEvent("kartingTrophy", avId, "%s" % (totalTrophyIndex))
                    self.notify.debug( "trophy: " + TTLocalizer.KartTrophyDescriptions[totalTrophyIndex] )
         
        # check to see if we need a laff point
        for i in range(1, RaceGlobals.NumTrophies/RaceGlobals.TrophiesPerCup + 1):
            cupNum = trophies[:RaceGlobals.NumTrophies].count(1) / (i * RaceGlobals.TrophiesPerCup)
            self.notify.debug( "cupNum: %s" % cupNum)
            trophyIndex = RaceGlobals.TrophyCups[i - 1]
            if cupNum and not trophies[trophyIndex]:
                # award the cup!
                trophies[trophyIndex] = 1
                newTrophies.append(trophyIndex)
                # laff point boost!
                oldMaxHp = av.getMaxHp()
                newMaxHp = min(ToontownGlobals.MaxHpLimit, oldMaxHp + 1)
                self.notify.debug( "cup awarded! new max laff : %s" % newMaxHp)
                av.b_setMaxHp(newMaxHp)
                # Also, give them a full heal
                av.toonUp(newMaxHp)
                # Write to the server log
                self.air.writeServerEvent("kartingTrophy", avId, "%s" % (trophyIndex))
                self.notify.debug( "trophy: " + TTLocalizer.KartTrophyDescriptions[trophyIndex] )
                
        self.notify.debug( "newTrophies: %s" % newTrophies )
        self.notify.debug( "trophies: %s" % trophies )
        self.notify.debug( "kartingHistory: %s" % history )
        
        ## set the new trophies and history if changed
        if newHistory:
            av.b_setKartingHistory(history)

        return newTrophies

    #
    # personal best methods
    #
    def checkPersonalBest(self, trackId, time, raceType, numRacers, avId):
        """Check time against top three personal best times for each track."""
        av = simbase.air.doId2do.get(avId)
        # TODO: what do we do if the av goes away?
        if av:
            bestTimes = av.getKartingPersonalBestAll()
            trackIndex = RaceGlobals.TrackIds.index(trackId)
            bestTime = bestTimes[trackIndex]
            self.notify.debug( "thisTime: %s, bestTime: %s" % (time, bestTime) )
            if (bestTime == 0.0) or (time < bestTime):
                bestTimes[trackIndex] = time
                self.notify.debug( "new personal best!" )
                av.b_setKartingPersonalBest(bestTimes)
                self.notify.debug( "personal best: %s" % bestTimes )
        
    #
    # high score file writing/reading methods
    #
    
    def checkTimeRecord(self, trackId, time, raceType, numRacers, avId):
        """Check a time against current shard record. Returns bonus tickets won if any."""
        bonus = 0
        newRecord = 0

        for period in RaceGlobals.PeriodIds:
            for record in range(0, RaceGlobals.NumRecordsPerPeriod):
                recordTime = self.trackRecords[trackId][period][record][0]
                if time < recordTime:
                    newRecord = 1
                    # new record!
                    self.notify.debug( "new %s record!" % TTLocalizer.RecordPeriodStrings[period] )
                    # TODO: alert player
                    # format: time, race type, num racers, racer name
                    av = simbase.air.doId2do.get(avId)
                    # TODO: what do we do if the av goes away?
                    if av:
                        name = av.name
                        # insert new record in this spot
                        self.trackRecords[trackId][period].insert(record, (time, raceType, numRacers, name))
                        # make sure we haven't gone over record list length
                        self.trackRecords[trackId][period] = self.trackRecords[trackId][period][:RaceGlobals.NumRecordsPerPeriod]
                        # notify the leaderboards of the update
                        self.updateLeaderboards(trackId, period)
                        bonus = RaceGlobals.PeriodDict[period]

                        # keep a log for contests, etc.
                        self.air.writeServerEvent("kartingRecord", avId, "%s|%s|%s" % (period, trackId, time))
                    else:
                        self.notify.warning("warning: av not logged in!")
                    # no need to keep checking times
                    break

        if newRecord:
            # write new record out to disk
            # TODO: does this need to be cached?
            self.updateRecordFile()

        return bonus
            
    def updateRecordFile(self):
        """Update current track record in this shard's record file"""
        # notify the leader boards that there has been an update
        try:
            backup = self.filename + '.bu'
            if os.path.exists(self.filename):
                os.rename(self.filename, backup)
            file = open(self.filename, 'w')
            file.seek(0)
            pickle.dump(self.trackRecords, file)
            file.close()
            if os.path.exists(backup):
                os.remove(backup)
        except EnvironmentError:
            self.notify.warning(str(sys.exc_info()[1]))
        
    def getFilename(self):
        """Compose the track record filename"""
        return "%s%s.trackRecords" % (self.serverDataFolder, self.shard)

    def loadRecords(self):
        """Load track record data from default location"""
        try:
            # Try to open the backup file:
            file = open(self.filename + '.bu', 'r')
            # Remove the (assumed) broken file:
            if os.path.exists(self.filename):
                os.remove(self.filename)
        except IOError:
            # OK, there's no backup file, good.
            try:
                # Open the real file:
                file = open(self.filename, 'r')
            except IOError:
                # OK, there's no file.  Grab the default times.
                return self.getRecordTimes()
        file.seek(0)
        records = self.loadFrom(file)
        file.close()

        #check for new tracks
        for trackId in RaceGlobals.TrackIds:
            if not records.has_key(trackId):
                records[trackId] = {}
                # for each recording period (daily, etc.)
                for i in RaceGlobals.PeriodIds:
                    records[trackId][i] = []
                    # for each top score
                    for j in range(0, RaceGlobals.NumRecordsPerPeriod):
                        records[trackId][i].append(getDefaultRecord(trackId))

        # update all leaderboards
        self.resetLeaderboards()
        return records

    def loadFrom(self, file):
        """Load track record data from specified file"""
        records = {}
        try:
            while 1:
                records = pickle.load(file)
        except EOFError:
            pass
        return records

    def getRecordTimes(self):
        """
        Create a set of track records from default times.
        Used when no record file can be found.
        """
        records = {}
        # for each track
        for trackId in RaceGlobals.TrackIds:
            records[trackId] = {}
            # for each recording period (daily, etc.)
            for i in RaceGlobals.PeriodIds:
                records[trackId][i] = []
                # for each top score
                for j in range(0, RaceGlobals.NumRecordsPerPeriod):
                    records[trackId][i].append(getDefaultRecord(trackId))
        return records

    # TODO: who will call this? HolidayMgrAI?
    def resetRecordPeriod(self, period):
        """
        Reset the records for a given period.
        """
        # for each track
        for trackId in RaceGlobals.TrackIds:
            # for each top score
            for i in range(0, RaceGlobals.NumRecordsPerPeriod):
                self.trackRecords[trackId][period][i] = getDefaultRecord(trackId)
            # notify the leaderboards that the records have changed
            self.updateLeaderboards(trackId, period)

        # save new records to disk
        self.updateRecordFile()

    #
    # leaderboard methods
    #
    
    def getRecords(self, trackId, period):
        return self.trackRecords[trackId][period]

    def updateLeaderboards(self, trackId, period):
        # notify the leaderboards of the update
        messenger.send("UpdateRaceRecord", [(trackId, period)])

    def resetLeaderboards(self):
        # usually done at startup
        for track in RaceGlobals.TrackIds:
            for period in RaceGlobals.PeriodIds:
                self.updateLeaderboards(track, period)


# classes for the HolidayManagerAI
class KartRecordDailyResetter(HolidayBaseAI.HolidayBaseAI):

    notify = DirectNotifyGlobal.directNotify.newCategory(
        'ResistanceEventMgrAI')

    PostName = 'kertRecordDailyReset'

    def __init__(self, air, holidayId):
        HolidayBaseAI.HolidayBaseAI.__init__(self, air, holidayId)   
    
    def start(self):
        # let the holiday system know we started
        bboard.post(KartRecordDailyResetter.PostName)
        simbase.air.raceMgr.resetRecordPeriod(RaceGlobals.Daily)
        
    def stop(self):
        # let the holiday system know we stopped
        bboard.remove(KartRecordDailyResetter.PostName)

class KartRecordWeeklyResetter(HolidayBaseAI.HolidayBaseAI):

    notify = DirectNotifyGlobal.directNotify.newCategory(
        'ResistanceEventMgrAI')

    PostName = 'kartRecordWeeklyReset'

    def __init__(self, air, holidayId):
        HolidayBaseAI.HolidayBaseAI.__init__(self, air, holidayId)

    def start(self):
        # let the holiday system know we started
        bboard.post(KartRecordWeeklyResetter.PostName)
        simbase.air.raceMgr.resetRecordPeriod(RaceGlobals.Weekly)

    def stop(self):
        # let the holiday system know we stopped
        bboard.remove(KartRecordWeeklyResetter.PostName)

class CircuitRaceHolidayMgr(HolidayBaseAI.HolidayBaseAI):

    notify = DirectNotifyGlobal.directNotify.newCategory(
        'CircuitRaceHolidayMgr')

    PostName = 'CircuitRaceHoliday'
    StartStopMsg = 'CircuitRaceHolidayStartStop'

    def __init__(self, air, holidayId):
        # Because of Silly Saturday and the Circuit Racing Event, these holidays can overlap.
        # We will use a counter to determine when to actually stop and start these events so
        # the two holidays don't stomp on each other.
        HolidayBaseAI.HolidayBaseAI.__init__(self, air, holidayId)

    def start(self):
        # let the holiday system know we started
        # note: the circuit race holidays can overlap, so we use a counter to control start/stop
        bboard.post(CircuitRaceHolidayMgr.PostName, bboard.get(CircuitRaceHolidayMgr.PostName, 0) + 1)

        if bboard.get(CircuitRaceHolidayMgr.PostName) == 1:
            # tell everyone race night is starting
            simbase.air.newsManager.circuitRaceStart()
            messenger.send(CircuitRaceHolidayMgr.StartStopMsg)

    def stop(self):
        # let the holiday system know we stopped
        # note: the circuit race holidays can overlap, so we use a counter to control start/stop
        bboard.post(CircuitRaceHolidayMgr.PostName, bboard.get(CircuitRaceHolidayMgr.PostName) - 1)

        if bboard.get(CircuitRaceHolidayMgr.PostName) == 0:
            # tell everyone race night is stopping
            simbase.air.newsManager.circuitRaceEnd()
            messenger.send(CircuitRaceHolidayMgr.StartStopMsg)
