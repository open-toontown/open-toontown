##########################################################################
# Module: DistributedViewPadAI.py
# Purpose: This class provides the necessary functionality for 
# Date: 7/21/05
# Author: jjtaylor
##########################################################################

##########################################################################
# Panda Import Modules
##########################################################################
from direct.directnotify import DirectNotifyGlobal
from direct.distributed.ClockDelta import *
from direct.task import Task
from pandac.PandaModules import *

##########################################################################
# Toontown Import Modules
##########################################################################
from toontown.racing.DistributedKartPadAI import DistributedKartPadAI
from toontown.racing.KartShopGlobals import KartGlobals

if( __debug__ ):
    import pdb


class DistributedViewPadAI( DistributedKartPadAI ):
    """
    Purpose: Must fill out... DO NOT FORGET TO COMMENT CODE.
    """

    ######################################################################
    # Class Variables
    ######################################################################
    notify = DirectNotifyGlobal.directNotify.newCategory( "DistributedViewPadAI" )
    #notify.setDebug(True)
    id = 0

    def __init__( self, air, area ):
        """
        COMMENT
        """

        # Initialize the KartPadAI Super Classes
        DistributedKartPadAI.__init__( self, air, area )

        # Initialize Instance Variables
        self.id = DistributedViewPadAI.id
        DistributedViewPadAI.id += 1
        self.kickAvDict = {}
        self.lastEntered = 0

    def delete( self ):
        # Remove any outstanding tasks
        for avId in self.kickAvDict.keys():
            self.stopTimeout( self.kickAvDict.get( avId ) )
            del self.kickAvDict[ avId ]
        del self.kickAvDict

        # Perform the Remaining Delete on the Super Class
        DistributedKartPadAI.delete( self )        

    def addAvBlock( self, avId, block, paid ):
        """
        Purpose: The addAvBlock Method updates the starting block of the
        avatar that has requested entry to the block.

        Params: avId - the id of the avatar entering the block.
                block - the Starting Block object that the avatar will enter.
        Return: None
        """

        # Call the Super Class Method
        success = DistributedKartPadAI.addAvBlock( self, avId, block, paid )
        if( success != KartGlobals.ERROR_CODE.success ):
            return success

        # Need to store information here....
        timeStamp = globalClockDelta.getRealNetworkTime()
        #self.d_setAvEnterPad( avId, timeStamp )
        self.d_setLastEntered( timeStamp )

        # Start the countdown to kick the avatar out of the spot...
        self.kickAvDict[ avId ] = self.startCountdown( self.uniqueName( 'ExitViewPadTask|%s'%(avId) ),
                                                       self.__handleKickTimeout,
                                                       KartGlobals.COUNTDOWN_TIME,
                                                       params = [ avId ] )

        return success

    def removeAvBlock( self, avId, block ):
        """
        The removeAvBlock Method updates the starting block of the avatar
        which has requested removal from the starting block.

        Params: avId - the id of the avatar to remove from the block.
                block - the starting block object that the avatar will exit.
        Return: None
        """

        # Call the SuperClass Method
        DistributedKartPadAI.removeAvBlock( self, avId, block )

        # Remove the avatar from the kick dictionary and update the
        # local client dictionary as well.
        if( self.kickAvDict.has_key( avId ) ):
            self.stopCountdown(self.kickAvDict[avId])
            del self.kickAvDict[ avId ]
            #self.d_setAvExitPad( avId )
        

    def __handleKickTimeout( self, avId ):
        """
        """
        block = self.avId2BlockDict.get( avId )
        self.notify.debug( "__handleKickTimeout: Timer Expired for Av %s, kicking from View Block %s" % ( avId, block ) )

        # Tell the block to release the avatar from the block, which in
        # turn will play the appropriate exit movie.
        block.normalExit()

    def d_setLastEntered( self, timeStamp ):
        """
        """
        self.lastEntered = timeStamp
        self.sendUpdate( 'setLastEntered', [ timeStamp ] )

    def getLastEntered(self):
        return self.lastEntered
    """
    def d_setAvEnterPad( self, avId, timeStamp ):
        self.sendUpdate( 'setAvEnterPad', [ avId, timeStamp ] )

    def d_setAvExitPad( self, avId ):
        self.sendUpdate( 'setAvExitPad', [ avId ] )
    """
        
