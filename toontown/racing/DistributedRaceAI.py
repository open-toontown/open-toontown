from direct.distributed import DistributedObjectAI
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals
from otp.otpbase.PythonUtil import nonRepeatingRandomList
from . import DistributedGagAI
from . import DistributedProjectileAI
from direct.task import Task
import random
import time
from . import Racer
from . import RaceGlobals
from direct.distributed.ClockDelta import *
from toontown.toonbase import TTLocalizer

class DistributedRaceAI(DistributedObjectAI.DistributedObjectAI):

    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedRaceAI')
    #notify.setDebug(1)

    def __init__(self, air, trackId, zoneId, avIds, laps, raceType, racerFinishedFunc, raceDoneFunc, circuitLoop, circuitPoints, circuitTimes, qualTimes = [], circuitTimeList = {}, circuitTotalBonusTickets = {}):

        DistributedObjectAI.DistributedObjectAI.__init__(self, air)

        self.trackId = trackId
        # infer direction (odd id's are rev)
        self.direction = self.trackId % 2
        self.zoneId = zoneId
        self.racers = {}
        self.avIds=[]
        self.kickedAvIds = []
        self.circuitPoints = circuitPoints
        self.circuitTimes = circuitTimes
        self.finishPending = []
        self.flushPendingTask = None
        self.kickSlowRacersTask = None
        #Create the list of avatars that we will potentially cull from
        for avId in avIds:
            if(avId) and avId in self.air.doId2do:
                self.avIds.append(avId)
                #Create each racer info, which also generates the karts
                self.racers[avId] = Racer.Racer(self, air, avId, zoneId)

        #At this point, we have karts on the AI
        self.toonCount = len(self.racers)
        self.startingPlaces = nonRepeatingRandomList(self.toonCount, 4)
        self.thrownGags = []

        self.ready = False
        self.setGo = False

        self.racerFinishedFunc = racerFinishedFunc
        self.raceDoneFunc = raceDoneFunc
        self.lapCount = laps
        self.raceType = raceType
        if(raceType==RaceGlobals.Practice):
            self.gagList=[]
        else:
            self.gagList = [0]*len(RaceGlobals.TrackDict[trackId][4])

        self.circuitLoop = circuitLoop
        self.qualTimes = qualTimes
        self.circuitTimeList = circuitTimeList

        self.qualTimes.append(RaceGlobals.TrackDict[trackId][1])

        self.circuitTotalBonusTickets = circuitTotalBonusTickets

        #print("QUALTIMES %s" % (self.qualTimes))
        #print("CIRCUITLOOP %s" % (self.circuitLoop))
        #print("circuitTotalBonusTickets %s" % self.circuitTotalBonusTickets)
        #import pdb; pdb.set_trace()

    def generate(self):
        DistributedObjectAI.DistributedObjectAI.generate(self)
        self.notify.debug('generate %s, id=%s, ' %
                         (self.doId, self.trackId))

        if __debug__:
            simbase.race = self


        trackFilepath = RaceGlobals.TrackDict[self.trackId][0]

        #self.geom = loader.loadModel(trackFilepath)
        #self.numItemPos = self.geom.findAllMatches("**/item*").getNumPaths()

        #self.positions=[]
        #for i in range(4):
        #    strIndex=str(i+1)
        #    np=self.geom.find("**/start_pos_"+strIndex)
        #    self.positions.append([np.getX(), np.getY(), np.getZ(), 0, 0, 0])
        #count=0
        #for i in self.racers:
        #    self.racers[i].startingPlace=self.startingPlaces[count]
        #    count+=1
        # log that toons entered the race
        #description = '%s|%s' % (
        #    self.trackId, self.avIds)
        #for avId in self.avIds:
        #    self.air.writeServerEvent('raceEntered', avId, description)

        taskMgr.doMethodLater(.5, self.enableEntryBarrier, "enableWaitingBarrier")

    def enableEntryBarrier(self, task):
        self.enterRaceBarrier=self.beginBarrier("waitingForJoin", self.avIds, TTLocalizer.DRAwaitingForJoin, self.b_racersJoined)
        self.notify.debug("Waiting for Joins!!!!")
        self.sendUpdate("waitingForJoin", [])



    #A utility function for doing safe removals of DistributedObjects
    #Mainly used for karts.
    def removeObject(self, object):
        if(object):
            self.notify.debug("deleting object: %s" %object.doId)
            object.requestDelete()


    def requestDelete(self, lastRace = True):
        self.notify.debug('requestDelete: %s' % self.doId)
        self.ignoreAll()
        self.ignoreBarrier("waitingForExit")
        for i in self.thrownGags:
            i.requestDelete()
        del self.thrownGags

        if lastRace:
            for i in self.racers:
                racer=self.racers[i]
                self.ignore(racer.exitEvent)
                if(racer.kart):
                    racer.kart.requestDelete()
                    racer.kart=None
                if(racer.avatar):
                    racer.avatar.kart=None
                    racer.avatar=None

        self.racers={}

        if self.flushPendingTask:
            taskMgr.remove(self.flushPendingTask)
            self.flushPendingTask = None

        if self.kickSlowRacersTask:
            taskMgr.remove(self.kickSlowRacersTask)
            self.kickSlowRacersTask = None

        DistributedObjectAI.DistributedObjectAI.requestDelete(self)


    def delete(self):
        self.notify.debug('delete: %s' % self.doId)
        DistributedObjectAI.DistributedObjectAI.delete(self)
        del self.raceDoneFunc
        del self.racerFinishedFunc

    def getTaskZoneId(self):
        return self.zoneId

    def allToonsGone(self):
        # the race room objs clean themselves up; in fact, the first race
        # room will call this for us when it detects that all toons have
        # left
        self.notify.debug('allToonsGone')
        self.requestDelete()

    #########################################
    # required-field getters
    #########################################

    def getZoneId(self):
        return self.zoneId

    def getTrackId(self):
        return self.trackId

    def getRaceType(self):
        return self.raceType

    def getCircuitLoop(self):
        return self.circuitLoop

    def getAvatars(self):
        avIds=[]
        for i in self.racers:
            avIds.append(i)
        return avIds

    def getStartingPlaces(self):
        return self.startingPlaces

    def getLapCount(self):
        return self.lapCount


    ################################################
    #requestKart:
    #    This function is only used to set
    #    controlled on the kart.
    #################################################

    def requestKart(self):
        avId=self.air.getAvatarIdFromSender()
        if (avId in self.racers):
            kart=self.racers[avId].kart
            if(kart):
                kart.request("Controlled", avId)


    #############################################
    #Clear out players who didn't join yet
    #Set up Toon/Kart linking on client
    #############################################

    def b_racersJoined(self, avIds):
        assert self.notify.debug("b_racersJoined %s" % avIds)
        self.ignoreBarrier("waitingForJoin")

        racersOut=[]
        for i in self.avIds:
            if i not in avIds:
                racersOut.append(i)

        if(len(avIds)==0):
            #The racers are too slow. Make sure they know to leave, then exit
            self.exitBarrier=self.beginBarrier("waitingForExit", self.avIds, 10, self.endRace)
            for i in self.avIds:
                self.d_kickRacer(i)
            return

        for i in racersOut:
            self.d_kickRacer(i)

        self.avIds=avIds
        self.waitingForPrepBarrier=self.beginBarrier("waitingForPrep", self.avIds, 30, self.b_prepForRace)
        avAndKarts=[]
        for i in self.racers:
            avAndKarts.append([self.racers[i].avId, self.racers[i].kart.doId])
        self.sendUpdate("setEnteredRacers", [avAndKarts])

    ##############################################
    #Clear out users who didn't make it
    #request Prep state on client
    ##############################################


    def b_prepForRace(self, avIds):
        self.notify.debug("Prepping!!!")
        self.ignoreBarrier("waitingForPrep")

        racersOut=[]
        for i in self.avIds:
            if i not in avIds:
                racersOut.append(i)


        if(len(avIds)==0):
            self.exitBarrier=self.beginBarrier("waitingForExit", self.avIds, 10, self.endRace)
        for i in racersOut:
            self.d_kickRacer(i)
        if(len(avIds)==0):
            return
        self.avIds=avIds
        #first gen the gags
        for i in range(len(self.gagList)):
            self.d_genGag(i)


        self.waitingForReadyBarrier=self.beginBarrier("waitingForReady", self.avIds, 20, self.b_startTutorial)
        self.sendUpdate("prepForRace", [])

    ###########################################
    #Clear out any players who didn't make it,
    #request Tutorial State on client
    #Iris in on client
    ###########################################

    def b_startTutorial(self, avIds):
        self.ignoreBarrier("waitingForReady")

        racersOut=[]
        for i in self.avIds:
            if i not in avIds:
                racersOut.append(i)

        if(len(avIds)==0):
            self.exitBarrier=self.beginBarrier("waitingForExit", self.avIds, 10, self.endRace)

        for i in racersOut:
            self.d_kickRacer(i)

        if(len(avIds)==0):
            return

        # need to check and deduct tickets here.  We're not really
        # set up to handle errors, but at least throw a warning
        # if somehow the toon got here without enough tix
        # We check this here since this is when the irisIn happens...
        # if they Alt-F4 after the irisIn, we will deduct
        for avId in avIds:
            av = self.air.doId2do.get(avId, None)
            if(not av):
                self.notify.warning("b_racersJoined: Avatar not found with id %s" %(avId))
            elif not (self.raceType == RaceGlobals.Practice):
                # circuit race only pays entry on the first race!
                if self.isCircuit() and not self.isFirstRace():
                    continue
                raceFee = RaceGlobals.getEntryFee(self.trackId, self.raceType)
                avTickets = av.getTickets()

                if(avTickets < raceFee):
                    self.notify.warning("b_racersJoined: Avatar %s does not own enough tickets for the race!")
                    av.b_setTickets(0)
                else:
                    # Okay, toon has enough tickets so now we must subtract them.
                    av.b_setTickets(avTickets - raceFee)

        self.avIds=avIds
        self.readRulesBarrier=self.beginBarrier("readRules", self.avIds, 10, self.b_startRace)
        self.sendUpdate("startTutorial", [])

    ##############################################
    #Start Countdown
    #Request Start state on client
    ##############################################

    def b_startRace(self, avIds):
        self.ignoreBarrier("readRules")

        # has the race has been deleted for some reason?
        if self.isDeleted():
            return

        self.notify.debug("Going!!!!!!")
        self.ignoreBarrier(self.waitingForReadyBarrier)

        #re-set this for 'winnings'
        self.toonCount = len(self.avIds)

        # don't start the race until the message has arrived on the client and countdown has finished
        self.baseTime = globalClock.getFrameTime() + 0.5 + RaceGlobals.RaceCountdown
        for i in self.racers:
            self.racers[i].baseTime=self.baseTime
        self.sendUpdate("startRace", [globalClockDelta.localToNetworkTime(self.baseTime)])

        # kickout racers who are taking too long
        qualTime = RaceGlobals.getQualifyingTime(self.trackId)
        timeout = qualTime + TTLocalizer.DRAwaitingForJoin + 3     # 3 is for the 'countdown'
        self.kickSlowRacersTask = taskMgr.doMethodLater(timeout, self.kickSlowRacers, "kickSlowRacers")

    def kickSlowRacers(self, task):
        assert self.notify.debug("in kickSlowRacers")
        self.kickSlowRacersTask = None

        # has the race has been deleted for some reason?
        if self.isDeleted():
            return

        for racer in self.racers.values():
            avId = racer.avId

            # racers can be tagged to 'not allow timeout'
            av = simbase.air.doId2do.get(avId,None)
            if av and not av.allowRaceTimeout:
                continue

            if (not racer.finished) and (not avId in self.kickedAvIds):
                self.notify.info('Racer %s timed out - kicking.' % racer.avId)
                self.d_kickRacer(avId, RaceGlobals.Exit_Slow)
                self.ignore(racer.exitEvent)
                racer.exited=True
                racer.finished = True
                taskMgr.doMethodLater(10, self.removeObject, "removeKart-%s"%racer.kart.doId, extraArgs=[racer.kart])

                #Make them invincible in the eyes of the anvil dropper
                taskMgr.remove("make %s invincible" % avId)
                self.racers[avId].anvilTarget=True

        self.checkForEndOfRace()

    def d_kickRacer(self, avId, reason = RaceGlobals.Exit_Barrier):
        if not avId in self.kickedAvIds:
            self.kickedAvIds.append(avId)

            # this kick will tell them they are not getting a refund
            if self.isCircuit() and not self.isFirstRace() and reason == RaceGlobals.Exit_Barrier:
                reason = RaceGlobals.Exit_BarrierNoRefund

            self.sendUpdate("goToSpeedway", [self.kickedAvIds, reason])


    def d_genGag(self, slot):
        index=random.randint(0, 5)
        self.gagList[slot]=index
        #TODO random gen the pos from a subset of total gag positions
        pos=slot
        self.sendUpdate("genGag", [slot, pos, index])


    def d_dropAnvil(self, ownerId):
        possibleTargets=[]
        for i in self.racers:
            #if(i != avId):
            if (not self.racers[i].anvilTarget):
                possibleTargets.append(self.racers[i])

        while(len(possibleTargets)>1):
            if(possibleTargets[0].lapT<=possibleTargets[1].lapT):
                possibleTargets = possibleTargets[1:]
            else:
                possibleTargets= possibleTargets[1:] + possibleTargets[:1]
        if(len(possibleTargets)):
            id=possibleTargets[0].avId
            if(id!=ownerId):
                #if the anvil is gonna crush someone, make them invincible
                #untill they unflatten
                possibleTargets[0].anvilTarget=True
                taskMgr.doMethodLater(4, setattr, "make %s invincible" % id, extraArgs=[self.racers[id], "anvilTarget", False])

                #This only happens when the player tries to drop on themselves
            self.sendUpdate("dropAnvilOn", [ownerId, id, globalClockDelta.getFrameNetworkTime()])
    def d_makeBanana(self, avId, x, y, z):
        gag=DistributedGagAI.DistributedGagAI(simbase.air, avId, self, 3, x, y, z, 0)
        self.thrownGags.append(gag)
        gag.generateWithRequired(self.zoneId)

    def d_launchPie(self, avId):
        ownerRacer = simbase.air.doId2do.get(avId, None)
        #self.racers[]
        targetId = 0
        type = 0
        #print("start launch pie")
        #print(avId)
        targetDist = 10000 #arbitrary large number
        #searching for targets ahead of us
        for iiId in self.racers:
            targetRacer =  simbase.air.doId2do.get(iiId, None)
            #print("Dist Calc")
            #print(targetRacer.kart.getPos(ownerRacer.kart))

            # some error checking to prevent frequent AI crashes
            if not (targetRacer and targetRacer.kart and ownerRacer and ownerRacer.kart):
                continue

            if ((targetRacer.kart.getPos(ownerRacer.kart)[1] < 500) #getting the y value of the position
                and (targetRacer.kart.getPos(ownerRacer.kart)[1] >= 0)
                and (abs(targetRacer.kart.getPos(ownerRacer.kart)[0]) < 50)
                and (avId != iiId)
                and (targetDist > targetRacer.kart.getPos(ownerRacer.kart)[1])):
                targetId = iiId
                targetDist = targetRacer.kart.getPos(ownerRacer.kart)[1]
                #print("found target forward")
                #print(iiId)
                #print(avId)
                #import pdb; pdb.set_trace()
        #searching for targets behind us
        if targetId == 0:
            for iiId in self.racers:
                targetRacer =  simbase.air.doId2do.get(iiId, None)
                #print("Dist Calc neg")
                #print(targetRacer.kart.getPos(ownerRacer.kart))

                # some error checking to prevent frequent AI crashes
                if not (targetRacer and targetRacer.kart and ownerRacer and ownerRacer.kart):
                    continue

                if ((targetRacer.kart.getPos(ownerRacer.kart)[1] > -80) #getting the y value of the position
                    and (targetRacer.kart.getPos(ownerRacer.kart)[1] <= 0)
                    and (abs(targetRacer.kart.getPos(ownerRacer.kart)[0]) < 50)
                    and (avId != iiId)):
                    targetId = iiId
                    #print("found target back")
                    #print(iiId)
                    #print(avId)
                    #import pdb; pdb.set_trace()

        #print("end launch pie")
        self.sendUpdate("shootPiejectile", [avId, targetId, type])


    def d_makePie(self, avId, x, y, z):
        #gag=DistributedGagAI.DistributedGagAI(simbase.air, avId, self, 3, x, y, z, 1)
        gag=DistributedProjectileAI.DistributedProjectileAI(simbase.air, self, avId)
        self.thrownGags.append(gag)
        gag.generateWithRequired(self.zoneId)

    def endRace(self, avIds):
        if hasattr(self, "raceDoneFunc"):
            self.raceDoneFunc(self, False)


    #######################################
    #Client->AI Functions
    #######################################

    def racerLeft(self, avIdFromClient):
        avId=self.air.getAvatarIdFromSender()
        if(self.racers.has_key(avId) and avId==avIdFromClient):
             self.notify.debug("Removing %d from race %d" % (avId, self.doId))
             #Clear out the players kart
             racer=self.racers[avId]

             taskMgr.doMethodLater(10, self.removeObject, racer.kart.uniqueName("removeIt"), extraArgs=[racer.kart])
             if(racer.avatar):
                 racer.avatar.kart=None
             #we're not calling this here, cause if a player has left
             #prematurely, they don't get their info passed to the manager
             self.racers[avId].exited=True

             #Make them invincible in the eyes of the anvil dropper
             taskMgr.remove("make %s invincible" % id)
             self.racers[avId].anvilTarget=True

             raceDone=True
             for i in self.racers:
                 if(not self.racers[i].exited):
                     raceDone=False
             if(raceDone):
                 self.notify.debug("race over, sending callback to raceMgr")

                 self.raceDoneFunc(self)

             if avId in self.finishPending:
                 self.finishPending.remove(avId)


    def hasGag(self, slot, type, index):
        avId=self.air.getAvatarIdFromSender()
        print("has gag")
        if index < 0 or index > (len(self.gagList) - 1): #check for cheaters
            self.air.writeServerEvent('suspicious', avId, 'Player checking for non-existant karting gag index %s type %s index %s' % (slot, type, index))
            self.notify.warning("somebody is trying to check for a non-existant karting gag %s %s %s! avId: %s" % (slot, type, index, avId))

        if slot < 0 or slot > (len(self.gagList) - 1): #crash from TTInjector hack
            self.air.writeServerEvent('suspicious', avId, 'Player checking for non-existant karting gag slot %s type %s index %s' % (slot, type, index))
            self.notify.warning("somebody is trying to check for a non-existant karting gag %s %s %s! avId: %s" % (slot, type, index, avId))
            return
            
        if avId in self.racers:
            if(self.racers[avId].hasGag):
                #Bad thing
                return
            if(self.gagList[slot]==index):
                self.gagList[slot]=None
                taskMgr.doMethodLater(5, self.d_genGag, "remakeGag-"+str(slot), extraArgs=[slot])
                self.racers[avId].hasGag=True
                self.racers[avId].gagType=type
            else:
                #problem
                return

    def requestThrow(self, x, y, z):
        avId=self.air.getAvatarIdFromSender()
        if avId in self.racers:
            racer=self.racers[avId]
            if(racer.hasGag):
                if(racer.gagType==1):
                    self.d_makeBanana(avId, x, y, z)
                if(racer.gagType==2):
                    #self.d_announceTurbo
                    pass
                if(racer.gagType==3):
                    self.d_dropAnvil(avId)
                if(racer.gagType==4):
                    #self.d_makePie(avId, x, y, z)
                    self.d_launchPie(avId)
                racer.hasGag=False
                racer.gagType=0
                #TODO self.sendUpdate("threwGag", [type, avatarToHit]

    ##########################################
    #Sent by players to announce their current
    #time on the track
    ##########################################

    def heresMyT(self, inputAvId, numLaps, t, timestamp):
        avId=self.air.getAvatarIdFromSender()
        if avId in self.racers and avId==inputAvId:
            me = self.racers[avId]

            me.setLapT(numLaps, t, timestamp)
            if(me.maxLap==self.lapCount and not me.finished):
                me.finished=True

                #Make them invincible in the eyes of the anvil dropper
                taskMgr.remove("make %s invincible" % id)
                me.anvilTarget=True

                # see if anyone's close
                someoneIsClose = False
                for racer in self.racers.values():
                    if (not racer.exited) and (not racer.finished):
                        if (me.lapT - racer.lapT) < 0.15:
                            someoneIsClose = True
                            break

                # add the racer to the pendingFinish array, sorted by totalTime
                index = 0
                for racer in self.finishPending:
                    if me.totalTime < racer.totalTime:
                        break
                    index += 1
                self.finishPending.insert(index, me)

                if self.flushPendingTask:
                    taskMgr.remove(self.flushPendingTask)
                    self.flushPendingTask = None

                if someoneIsClose:
                    task = taskMgr.doMethodLater(3, self.flushPending,
                                                 self.uniqueName("flushPending"))
                    self.flushPendingTask = task
                else:
                    self.flushPending()


    # we've waited long enough... flush the finishPending array
    def flushPending(self, task = None):
        for racer in self.finishPending:
            self.racerFinishedFunc(self, racer)

        self.finishPending = []
        self.flushPendingTask = None


    ####################################
    #TODO: Rename
    #sent after a player finishes a race
    #Sets their standing and winnings
    ####################################

    def d_setPlace(self, avId, totalTime, place, entryFee, qualify, winnings, bonus, trophies, circuitPoints, circuitTime):
        self.sendUpdate("setPlace", [avId, totalTime, place, entryFee, qualify, winnings, bonus, trophies, circuitPoints, circuitTime])

    def d_setCircuitPlace(self, avId, place, entryFee, winnings, bonus,trophies):
        self.sendUpdate("setCircuitPlace", [avId, place, entryFee, winnings, bonus,trophies])

    def d_endCircuitRace(self):
        self.sendUpdate("endCircuitRace")

    ####################################
    #Racer.py calls this function on
    #an unexpected exit
    ####################################

    def unexpectedExit(self, avId):
        self.notify.debug("racer disconnected: %s" %avId)
        racer=self.racers.get(avId, None)
        if(racer):
            self.sendUpdate("racerDisconnected", [avId])
            self.ignore(racer.exitEvent)
            racer.exited=True
            taskMgr.doMethodLater(10, self.removeObject, "removeKart-%s"%racer.kart.doId, extraArgs=[racer.kart])

            #Make them invincible in the eyes of the anvil dropper
            taskMgr.remove("make %s invincible" % id)
            self.racers[avId].anvilTarget=True

            self.checkForEndOfRace()

    def checkForEndOfRace(self):
        if self.isCircuit() and self.everyoneDone():
            simbase.air.raceMgr.endCircuitRace(self)

        raceOver=True
        for i in self.racers:
            if(not self.racers[i].exited):
                raceOver=False

        if(raceOver):
            self.raceDoneFunc(self)

    def sendToonsToNextCircuitRace(self, raceZone, trackId):
        for avId in self.avIds:
            self.notify.debug("Handling Circuit Race transisiton for avatar %s" % (avId))
            # Tell each player that they should go to the next race
            self.sendUpdateToAvatarId(avId, "setRaceZone", [raceZone, trackId])

    def isCircuit(self):
        return self.raceType == RaceGlobals.Circuit

    def isLastRace(self):
        return len(self.circuitLoop) == 0

    def isFirstRace(self):
        return len(self.circuitLoop) == 2

    def everyoneDone(self):
        done = True
        for racer in self.racers.values():
            if (not racer.exited and (not racer.avId in self.playersFinished) and
                (not racer.avId in self.kickedAvIds)):
                # there is a racer who hasn't exited and who hasn't finished
                done = False
                break

        return done
