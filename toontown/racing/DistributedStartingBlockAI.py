from otp.ai.AIBase import *
from toontown.toonbase import ToontownGlobals
from direct.distributed.ClockDelta import *
from direct.distributed import DistributedObjectAI
from toontown.building.ElevatorConstants import *
from toontown.building import DistributedElevatorExtAI
from direct.fsm import ClassicFSM
from direct.fsm import State

from direct.showbase.DirectObject import DirectObject
from toontown.racing.KartShopGlobals import KartGlobals

if( __debug__ ):
    import pdb

##########################################################################
# Temporary Class for Working with DistributedRacePad
# Modeling startblock after Pond->FishingSpot relationship so the
# startblocks can be placed via the level editor. Also going this route
# since kart viewing (Big Boy-esque) area will have more than 4 starting
# blocks and this can be changed easily in the level editor. Starting
# blocks will be props.
#
# Using temp class so that the current startingblock implementation isn't
# broken so that you can still get to the race instances.
##########################################################################

###### NOTE
###### If RacePad / Starting Block implementation changes, moving it
###### more towards an elevator or trolley system. Remember that the
###### DistributedViewingBlockAI code is derived from the Starting Block!
###### See bottom class.

class DistributedStartingBlockAI( DistributedObjectAI.DistributedObjectAI ):
    """
    Purpose: MUST ADD COMMENTS HERE.
    """
    
    ######################################################################
    # Class Variables
    ######################################################################
    notify = DirectNotifyGlobal.directNotify.newCategory( "DistributedStartingBlockAI" )
    #notify.setDebug(True)
   
    
    def __init__( self, air, kartPad, x, y, z, h, p, r, padLocationId ):
        """
        Comments go here
        """
        
        # Initialize the Super Class
        DistributedObjectAI.DistributedObjectAI.__init__( self, air )
        
        # Initialize Instance Variables
        self.avId = 0
        self.isActive = True
        self.kartPad = kartPad
        self.unexpectedEvent = None
        self.padLocationId = padLocationId
        self.posHpr = ( x, y, z, h, p, r )
        self.currentMovie = None
           
    def delete( self ):
        """
        Comments go here
        """
        
        self.avId = 0
        self.kartPad = None
        
        # Perform Super Class Delete call
        DistributedObjectAI.DistributedObjectAI.delete( self )
   
    def getPadDoId( self ):
        """
        Comment:
        """
        return self.kartPad.getDoId()
   
    def getPadLocationId( self ):
        """
        Comment:
        """
        return self.padLocationId
 
    def getPosHpr( self ):
        """
        Comment:
        """
        return self.posHpr
   
    def setActive( self, isActive ):
        """
        Comment:
        """
        self.isActive = isActive
 
    def requestEnter( self, paid ):
        """
        comment
        """

        avId = self.air.getAvatarIdFromSender()
        if( self.isActive and ( self.avId == 0 ) ):
            # Obtain the Avatar Id and attempt to add the avatar to the
            # kart pad.
            success = self.kartPad.addAvBlock( avId, self, paid )
           

            # Debug Notification of request entry.
            self.notify.debug( "requestEnter: avId %s wants to enter the kart block." % ( avId ) )
            
            if( success == KartGlobals.ERROR_CODE.success ):
                # There is not currently an avatar occupying this kart block.
                self.avId = avId
                self.isActive = False
                
                # Handle an unexpected exit by the avatar.
                self.unexpectedEvent = self.air.getAvatarExitEvent( self.avId )
                self.acceptOnce( self.unexpectedEvent, self.unexpectedExit )
                
                # Perform other operations here.
                self.d_setOccupied( self.avId )
                self.d_setMovie( KartGlobals.ENTER_MOVIE )
            else:
                # The request for entry has been denied.
                self.sendUpdateToAvatarId( avId, "rejectEnter", [ success ] )
        else:
            if( hasattr( self.kartPad, 'state' ) and self.kartPad.state in [ 'WaitBoarding', 'AllAboard' ] ):
                errorCode = KartGlobals.ERROR_CODE.eBoardOver
            else:
                errorCode = KartGlobals.ERROR_CODE.eOccupied
            
            # The request for entry has been denied because the blocks are
            self.sendUpdateToAvatarId( avId, "rejectEnter", [ errorCode ] )
   
    def requestExit( self ):
        """
        Comment:
        """
        
        # Obtain the avatar id who is requesting the exit.
        avId = self.air.getAvatarIdFromSender()
        
        # Debug Notification of exit request
        self.notify.debug( "requestExit: avId %s wants to exit the Kart Block." % ( avId ) )
        
        success = self.validate( avId, ( self.avId == avId ), "requestExit: avId is not occupying this kart block." )
        if( not success ):
            return
        
        self.normalExit()

   # this should be called either when the avatar finishes a movie, or the AI
   # has detected an unexpected exit
    def movieFinished(self):
        if self.currentMovie == KartGlobals.EXIT_MOVIE:
            self.cleanupAvatar()
            
        self.currentMovie = None
        self.kartPad.kartMovieDone()
        
    def cleanupAvatar( self ):
        """
        Comment:
        """
   
        # Tell the KartPad that the toon is exiting the block.
        
        self.ignore( self.unexpectedEvent )
        self.kartPad.removeAvBlock( self.avId, self )
        self.avId = 0
        self.isActive = True
        self.d_setOccupied( 0 )
        
    def normalExit( self ):
        """
        Comment:
        """
        
        self.d_setMovie( KartGlobals.EXIT_MOVIE )
   
    def raceExit( self ):
        """
        Comment:
        """
        self.cleanupAvatar()
        self.movieFinished()
 
    def unexpectedExit( self ):
        """
        Comment:
        """
        self.cleanupAvatar()
        self.movieFinished()
   
        self.unexpectedEvent = None
 
    ######################################################################
    # Distributed Methods
    ######################################################################
    def d_setOccupied( self, avId ):
        """
        Comment:
        """
        self.sendUpdate( "setOccupied", [ avId ] )
 
    def d_setMovie( self, mode ):
        """
        Comment:
        """
        self.currentMovie = mode
        self.sendUpdate( "setMovie", [ mode ] )

class DistributedViewingBlockAI( DistributedStartingBlockAI ):
    """
    Derived from the Starting Block, mainly for use on the client-side
    since it will need different movies for the Viewer than it will
    for the Race Starting block. Not much should be handled here... most
    changes will occur on client DistributedViewingBlock class.
    """
    ######################################################################
    # Class Variables
    ######################################################################
    notify = DirectNotifyGlobal.directNotify.newCategory( "DistributedViewingBlockAI" )
   
    def __init__( self, air, kartPad, x, y, z, h, p, r, padLocationId ):
        """
        """
        # Initialize the Super Class
        DistributedStartingBlockAI.__init__( self, air, kartPad,
                                             x, y, z, h, p, r,
                                             padLocationId )

    def delete( self ):
        """
        """
        # Call the Super Class delete
        DistributedStartingBlockAI.delete( self )
            
