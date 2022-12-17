##########################################################################
# Module: DistributedRacePadAI.py
# Purpose: This class provides the necessary functionality for 
# Date: 6/28/05
# Author: jjtaylor
##########################################################################

##########################################################################
# Panda Import Modules
##########################################################################
from direct.directnotify import DirectNotifyGlobal
from direct.distributed.ClockDelta import *
from direct.fsm.FSM import FSM
from direct.task import Task
from pandac.PandaModules import *

##########################################################################
# Toontown Import Modules
##########################################################################
from toontown.racing.DistributedKartPadAI import DistributedKartPadAI
from toontown.racing.KartShopGlobals import KartGlobals
from toontown.racing import RaceGlobals
from toontown.racing.RaceManagerAI import CircuitRaceHolidayMgr
from toontown.toonbase import ToontownGlobals

if( __debug__ ):
    import pdb

class DistributedRacePadAI( DistributedKartPadAI, FSM ):
    """
    Purpose: Must fill out... DO NOT FORGET TO COMMENT CODE!
    """

    ######################################################################
    # Class Variables
    ######################################################################
    notify = DirectNotifyGlobal.directNotify.newCategory( "DistributedRacePadAI" )
    #notify.setDebug(True)
    #notify.setInfo(True)
    defaultTransitions = {
        'Off'           : [ 'WaitEmpty' ],
        'WaitEmpty'     : [ 'Off', 'WaitCountdown' ],
        'WaitCountdown' : [ 'WaitEmpty', 'WaitBoarding', 'AllAboard' ],
        'WaitBoarding'  : [ 'AllAboard', 'WaitEmpty' ],
        'AllAboard'     : [ 'WaitEmpty' ],
    }
    id = 0

    def __init__( self, air, area, tunnelGenre, tunnelId ):
        """
        COMMENT
        """

        # Initialize the KartPadAI and FSM Super Classes
        DistributedKartPadAI.__init__( self, air, area )
        FSM.__init__( self, "RacePad_%s_FSM" % ( DistributedRacePadAI.id ) )

        # Initialize Instance Variables
        self.id = DistributedRacePadAI.id
        DistributedRacePadAI.id += 1

        self.tunnelId = tunnelId
        self.tunnelGenre = tunnelGenre
        self.timerTask = None
        raceInfo = RaceGlobals.getNextRaceInfo( -1, tunnelGenre, tunnelId )
        self.trackId = raceInfo[0]
        self.trackType = raceInfo[1]
        self.numLaps = raceInfo[2]
        self.raceMgr = self.air.raceMgr

    def delete(self):
        DistributedKartPadAI.delete(self)
        FSM.cleanup(self)

    def cycleTrack(self, task = None):
        self.notify.debug("Cycling track - %s" % self.doId)
        raceInfo = RaceGlobals.getNextRaceInfo( self.trackId, self.tunnelGenre, self.tunnelId )
        self.trackId = raceInfo[0]
        self.trackType = raceInfo[1]

        #determine if this should be a Circuit race
        if self.trackType == RaceGlobals.ToonBattle:
            if bboard.get(CircuitRaceHolidayMgr.PostName):
                self.trackType = RaceGlobals.Circuit

        self.numLaps = raceInfo[2]
        self.sendUpdate("setTrackInfo", [[self.trackId, self.trackType]])
        self.cycleTrackTask = taskMgr.doMethodLater(RaceGlobals.TrackSignDuration,
                                                    self.cycleTrack,
                                                    self.uniqueName("cycleTrack"))

    def getTrackInfo( self ):
        return [ self.trackId, self.trackType ]

    def addAvBlock( self, avId, block, paid ):
        """
        Purpose: The addAvBlock Method updates the starting block of the
        avatar that has requested entry to the block.

        Params: avId - the id of the avatar entering the block.
                block - the Starting Block object that the avatar will enter.
        Return: None
        """

        # Grab the avatar and make certain its valid
        av = self.air.doId2do.get( avId, None )
        if( not av ):
            self.notify.warning( "addAvBlock: Avatar not found with id %s" %( avId ) )
            return KartGlobals.ERROR_CODE.eGeneric


        # Make sure this track is open
        #if (self.trackId in (RaceGlobals.RT_Urban_1, RaceGlobals.RT_Urban_1_rev) and
        #    not simbase.config.GetBool('test-urban-track', 0)):
        #    return KartGlobals.ERROR_CODE.eTrackClosed

        grandPrixWeekendRunning = self.air.holidayManager.isHolidayRunning(
            ToontownGlobals.CIRCUIT_RACING_EVENT)
        
        # trialer restriction - only Speedway Practice races
        if not paid and not grandPrixWeekendRunning:
            genre = RaceGlobals.getTrackGenre(self.trackId)
            if not ( (genre == RaceGlobals.Speedway) and (self.trackType == RaceGlobals.Practice) ):
                return KartGlobals.ERROR_CODE.eUnpaid

        if not(self.state == 'WaitEmpty' or self.state == 'WaitCountdown'):
            #you can only join a racepad in one of these states
            return KartGlobals.ERROR_CODE.eTooLate            
        
        # Only check for non-practice races
        if( av.hasKart() and  (not self.trackType == RaceGlobals.Practice) ):
            # Check if the toon owns enough tickets for the race
            raceFee = RaceGlobals.getEntryFee(self.trackId, self.trackType)
            avTickets = av.getTickets()
       
            if( avTickets < raceFee ):
                self.notify.debug( "addAvBlock: Avatar %s does not own enough tickets for the race!" )           
                return KartGlobals.ERROR_CODE.eTickets

        # Call the Super Class Method
        success = DistributedKartPadAI.addAvBlock( self, avId, block, paid )
        if( success != KartGlobals.ERROR_CODE.success ):
            return success

        # A valid avatar has entered a starting block, now enter wait
        # countdown state. If already in the WaitCountdown state this
        # will not cause any harm.
        if( self.isOccupied() ):
            self.request( 'WaitCountdown' )

        return success

    def removeAvBlock( self, avId, block ):
        """
        The removeAvBlock Method updates the starting block of the avatar
        which has requested removal from the starting block.

        Params: avId - the id of the avatar to remove from the block.
                block - the starting block object that the avatar will exit.
        Return: None
        """

        # Call the Super Class Method
        DistributedKartPadAI.removeAvBlock( self, avId, block )

        if( not self.isOccupied() and ( self.timerTask is not None ) ):
            # Remove the TimerTask from the taskMgr and request
            # a state transition to the WaitEmpty since there are no
            # longer any toons occupying the kart.
            taskMgr.remove( self.timerTask )
            self.timerTask = None

            self.request( 'WaitEmpty' )
            
    def __startCountdown( self, name, callback, time, params = [] ):
        """
        Purpose: The __startCountdown Method generates a task that acts as
        a timer. It calls a specified callback method after the time period
        expires, and it additionally records a timestamp for when the timer
        began.

        Params: name - a unique name for the task.
                callback - method to handle the case when the timer expires.
                time - amount of time before the timer expires.
                params - extra arguments for the callback method.
        Return: None
        """
        self.timerTask = self.stopCountdown( self.timerTask )
        self.timerTask = DistributedKartPadAI.startCountdown( self, name, callback, time, params )

    def handleWaitTimeout( self, nextState ):
        """
        Comment:
        """
        if( self.isOccupied() ):
            self.request( nextState )
        else:
            self.request( 'WaitEmpty' )

        #self.timerTask = None
        return Task.done

    def __handleSetRaceCountdownTimeout( self, params = [] ):
        """
        Comment:
        """
        # set the timer task to off, because raceExit calls removeAvBlock and
        # shouldn't call. SHOULD BREAK UP THOSE CALLS.
        self.timerTask = None
        players = self.avId2BlockDict.keys()
        circuitLoop = []
        if self.trackType == RaceGlobals.Circuit:
            circuitLoop = RaceGlobals.getCircuitLoop(self.trackId)

        raceZone = self.raceMgr.createRace( self.trackId,
                                            self.trackType,
                                            self.numLaps,
                                            players,
                                            circuitLoop[1:],
                                            {},{}, [], {},
                                            circuitTotalBonusTickets = {})
        for avId in self.avId2BlockDict.keys():
            if( avId ):
                self.notify.debug( "Handling Race Launch Countdown for avatar %s" % ( avId ) )
                # Tell each player that they should enter
                # the mint, and which zone it is in.
                self.sendUpdateToAvatarId( avId, "setRaceZone", [ raceZone ] )
                self.avId2BlockDict[ avId ].raceExit()

        # Let's now restart for a new race.
        self.request( 'WaitEmpty' )            
        return Task.done

    def isOccupied( self ):
        """
        Commnet:
        """
        return ( self.avId2BlockDict.keys() != [] )

    def enableStartingBlocks( self ):
        """
        Comment
        """
        for block in self.startingBlocks:
            block.setActive( True )
    
    def disableStartingBlocks( self ):
        """
        Comment:
        """
        for block in self.startingBlocks:
            block.setActive( False )

    def getState( self ):
        """
        Comment:
        """
        return self.state, globalClockDelta.getRealNetworkTime()
            
    ######################################################################
    # Distributed Methods
    ######################################################################
    def d_setState( self, state ):
        """
        Comment:
        """
        timeStamp = globalClockDelta.getRealNetworkTime()
        self.sendUpdate( 'setState', [ state, timeStamp ] )

    ######################################################################
    # FSM State Methods
    ######################################################################
    def enterOff( self ):
        """
        Comment
        """
        self.notify.debug( "enterOff: Entering Off State for RacePad %s" % ( self.id ) )

        self.ignore(CircuitRaceHolidayMgr.StartStopMsg)

    def exitOff( self ):
        """
        Comment
        """
        self.notify.debug( "exitOff: Exiting Off state for RacePad %s" % ( self.id ) )

        def handleCircuitHolidayStartStop(args = None):
            if self.state == "WaitEmpty":
                taskMgr.remove(self.cycleTrackTask)
                self.cycleTrack()

        self.accept(CircuitRaceHolidayMgr.StartStopMsg,
                    handleCircuitHolidayStartStop)

    def enterWaitEmpty( self ):
        """
        Comment
        """
        self.notify.debug( "enterWaitEmpty: Entering WaitEmpty State for RacePad %s" % ( self.id ) )

        # What needs to occur at this point.
        #  - Enable Accepting of Toons for the next race.
        #  - Signal to the client that we are in wait empty state.

        self.d_setState( 'WaitEmpty' )       
        self.enableStartingBlocks()
        self.cycleTrack()
        
    def exitWaitEmpty( self ):
        """
        Comment
        """
        self.notify.debug( "exitWaitEmpty: Exiting WaitEmpty State for RacePad %s" % ( self.id ) )
        taskMgr.remove(self.cycleTrackTask)
        
    def enterWaitCountdown( self ):
        """
        Comment
        """
        self.notify.debug( "enterWaitCountdown: Entering WaitCountdown State for RacePad %s" % ( self.id ) )

        # Allow toons to enter the spot and tell the client object that
        # the AI object has entered the WaitCountdown State.
        self.d_setState( 'WaitCountdown' )

        # Now, handle the actual countdown timer setup.
        self.__startCountdown( self.uniqueName( 'CountdownTimer-%s' % ( self.doId ) ),
                               self.handleWaitTimeout,
                               KartGlobals.COUNTDOWN_TIME,
                               [ 'WaitBoarding' ] )
        
    def filterWaitCountdown( self, request, args ):
        """
        Comment
        """
        if request == 'WaitBoarding' and self.allMoviesDone():
            return 'AllAboard'
        elif( request in DistributedRacePadAI.defaultTransitions.get( 'WaitCountdown' ) ):
            return request       
        elif( request is 'WaitCountdown' ):
            # If in the WaitCountdown state, no need to loop back into
            # itself since it is already counting down to the race.
            return None
        else:
            return self.defaultFilter( request, args )

    def exitWaitCountdown( self ):
        """
        Comment
        """
        self.notify.debug( "exitWaitCountdown: Exiting WaitCountdown State for RacePad %s" % ( self.id ) )

    def enterWaitBoarding( self ):
        """
        Comment: State to wait for avatars to finish boarding.
        """
        self.notify.debug( "enterWaitBoarding: Entering WaitBoarding State for RacePad %s" %( self.id ) )

        # No longer allow toons to enter the starting blocks because the
        # race is doesn't accept more boarders.
        self.disableStartingBlocks()
        self.d_setState( 'WaitBoarding' )
        self.waitingForMovies = True

        # Allow the toons enough time to play the movie, then we
        # play the enter race movie in the AllBoarded state.
        self.__startCountdown( self.uniqueName( 'CountdownTimer-%s' % ( self.doId ) ),
                               self.handleWaitTimeout,
                               KartGlobals.BOARDING_TIME,
                               [ 'AllAboard' ] )
        
    def exitWaitBoarding( self ):
        """
        Comment
        """
        self.notify.debug( "exitWaitBoarding: Exiting WaitBoarding State for RacePad %s" % ( self.id ) )
        self.waitingForMovies = False

    def enterAllAboard( self ):
        """
        Comment
        """
        self.notify.debug( "enterAllAboard: Entering AllAboard State for RacePad %s" % ( self.id ) )

        # make certain the starting blocks are turned off
        self.disableStartingBlocks()

        # Make certain that there are toons onboard, they might have
        # left the district.
        players = self.avId2BlockDict.keys()

        # check to see if we need to kick a solo racer
        kickSoloRacer = False
        if (self.trackType != RaceGlobals.Practice) and (len(players) == 1):
            av = self.air.doId2do.get(players[0])
            if av and not av.allowSoloRace:
                kickSoloRacer = True

        if kickSoloRacer:
            # only one left... kick him off.  When he's done, the
            # removeAvBlock call will reset us back to 'WaitEmpty'
            self.notify.info("enterAllAboard: only one toon, kicking him: %s" % players[0])
            block = self.avId2BlockDict[players[0]]
            block.normalExit()
        elif len(players) > 0:
            # Update the State
            self.d_setState( 'AllAboard' )

            # Generate the Race
            self.__startCountdown( "setRaceZoneTask",
                                   self.__handleSetRaceCountdownTimeout,
                                   KartGlobals.ENTER_RACE_TIME,
                                   [] )     
        else:
            self.notify.warning( "The RacePad was empty, so no one entered a race. Returning to WaitEmpty State." )
            self.d_setState( 'WaitEmpty' )

    def exitAllAboard( self ):
        """
        Comment
        """
        self.notify.debug( "exitAllAboard: Exiting AllAboard State for RacePad %s" % ( self.id ) )
