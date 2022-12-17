##########################################################################
# Module: DistributedKartPadAI.py
# Purpose: This class provides the basic methods and data members for
#          derived classes which need to handle a number of karts for
#          racing or viewing.
# Date: 6/28/05
# Author: jjtaylor
##########################################################################

##########################################################################
# Panda Import Modules
##########################################################################
from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI
from toontown.racing.KartShopGlobals import KartGlobals

if(__debug__):
    import pdb

class DistributedKartPadAI(DistributedObjectAI):
    """
    Purpose: ...
    """

    ######################################################################
    # Class Variables
    ######################################################################
    notify = DirectNotifyGlobal.directNotify.newCategory("DistributedKartPadAI")
    #notify.setDebug(True)

    def __init__(self, air, area):
        """
        Purpose: The __init__ Method handles the base initialization of
        the DistributedKartPadAI object.

        Params: air - The Toontown AIRepository
                area - The area in which the object is located.
        Return: None
        """

        # Initialize the Super Class
        DistributedObjectAI.__init__(self, air)

        # Initialize Instance variables
        self.area = area
        self.startingBlocks = []
        self.avId2BlockDict = {}
        self.waitingForMovies = False

    def delete(self):
        """
        Comment
        """
        for i in range(len(self.startingBlocks)):
            # LIKELY SHOULD DELETE ASSOCIATED KART BLOCK
            # DISTRIBUTED OBJECTS HERE.
            self.startingBlocks.pop(0)

        # Perform necessary cleanup for Super Class
        DistributedObjectAI.delete(self)

    def getArea(self):
        """
        Purpose: The getArea Method returns the area for which the
        object is located.

        Params: None
        Return: Int - area id
        """
        return self.area

    def addStartingBlock(self, block):
        """
        Comment
        """
        self.startingBlocks.append(block)

    def addAvBlock(self, avId, block, paid):
        """
        Purpose: The addAvBlock Method updates the starting block of the avatar which
        has requested entry to the block.

        Params: avId - the id of the avatar entering the block.
                block - the Starting Block object that the avatar will enter.
        Return: None
        """
        self.notify.debug("addAvBlock: adding avId: %s to a starting block" %(avId))

        # Retrieve the avatar
        av = self.air.doId2do.get(avId, None)
        if(av and not av.hasKart()):
            self.notify.debug("Avatar %s does not own a kart, don't let him into the spot!")
            return KartGlobals.ERROR_CODE.eNoKart

        # Make certain that the avatar is not currently in another block.
        currentBlock = self.avId2BlockDict.get(avId, None)
        if(currentBlock):
            self.notify.warning("addAvBlock: avId: %s already in a block" % (avId))
            return KartGlobals.ERROR_CODE.eGeneric

        # The avatar is not currently in a kart block, which is what
        # should be expected.
        self.avId2BlockDict[avId] = block
        self.notify.debug("RacePad %s has added Toon %s to block %s" % (self.doId, avId, block.doId))
        return KartGlobals.ERROR_CODE.success

    def removeAvBlock(self, avId, block):
        """
        Purpose: The removeAvBlock Method updates the starting block of the avatar
        which has requested removal from the starting block.

        Params: avId - the id of the avatar to remove from the block.
                block - the starting block object that the avatar will exit.
        Return: None
        """

        currentBlock = self.avId2BlockDict.get(avId, None)
        if(currentBlock):
            if(currentBlock == block):
                self.notify.debug("removeAvBlock: removing avId %s from a starting block" % (avId))
                del self.avId2BlockDict[avId]
            else:
                self.notify.warning("removeAvBlock: blocks do not match, remove av anyways")
                del self.avId2BlockDict[avId]

            self.notify.debug("RacePad %s has removed Toon %s from block %s" % (self.doId, avId, block.doId))
        else:
            self.notify.warning("removeAvBlock: avId %s not found" % (avId))

    def startCountdown(self, name, callback, time, params = []):
        """
        Purpose: The __startCountdown Method generates a task that acts as
        a timer. It calls a specified callback method after the time period
        expires, and it additionally records a timestamp for when the timer
        began.

        Params: name - a unique name for the task.
                callback - method to handle the case when the timer expires.
                time - amount of time before the timer expires.
                params - extra arguments for the callback method.
        Return: task
        """

        countdownTask = taskMgr.doMethodLater(time, callback,
                                               self.taskName(name),
                                               params)
        return countdownTask

    def stopCountdown(self, task = None):
        """
        Comment:
        """
        if(task is not None):
            taskMgr.remove(task.name)
        return None

    def allMoviesDone(self):
        # check all of these flags.  If everyone is done
        # pulling out their kart, go on to the next state
        allDone = True
        for block in self.startingBlocks:
            if block.currentMovie:
                allDone = False

        return allDone

    def kartMovieDone(self):
        # we only care if we are currently waiting for movies to finish
        if not self.waitingForMovies:
            return

        if self.allMoviesDone():
            self.stopCountdown(self.timerTask)
            self.handleWaitTimeout('AllAboard')


