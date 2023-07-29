from toontown.toonbase import ToontownGlobals
from direct.distributed.ClockDelta import *
from direct.fsm import ClassicFSM
from direct.fsm import State
from direct.task import Task
from toontown.minigame import CannonGameGlobals
from direct.distributed import DistributedObjectAI
from toontown.minigame import Trajectory
from . import CannonGlobals

class DistributedCannonAI(DistributedObjectAI.DistributedObjectAI):

    notify = directNotify.newCategory("DistributedCannonAI")

    def __init__(self, air, estateId, targetId, x, y, z, h, p, r):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)

        self.posHpr = [x, y, z, h, p, r]
        self.avId = 0
        self.estateId = estateId
        self.timeoutTask = None
        self.targetId = targetId
        self.cannonBumperPos = list(ToontownGlobals.PinballCannonBumperInitialPos)

    def delete(self):
        self.ignoreAll()
        self.__stopTimeout()
        DistributedObjectAI.DistributedObjectAI.delete(self)
        
    # Generate is never called on the AI so we do not define one
    # Disable is never called on the AI so we do not define one



    def requestEnter(self):
        avId = self.air.getAvatarIdFromSender()
        if (self.avId == 0):
            self.avId = avId
            self.__stopTimeout()
            self.setMovie(CannonGlobals.CANNON_MOVIE_LOAD, self.avId)

            # Handle unexpected exit
            self.acceptOnce(self.air.getAvatarExitEvent(avId),
                            self.__handleUnexpectedExit, extraArgs=[avId])
            self.acceptOnce("bootAvFromEstate-"+str(avId),
                            self.__handleBootMessage, extraArgs=[avId])

            # Start timeout timer
            self.__startTimeout(CannonGlobals.CANNON_TIMEOUT)
        else:
            self.air.writeServerEvent('suspicious', avId, 'DistributedCannonAI.requestEnter cannon already occupied')
            self.notify.warning("requestEnter() - cannon already occupied")
            self.sendUpdateToAvatarId(avId, "requestExit", [])
            
    def setMovie(self, mode, avId):
        self.avId = avId
        self.sendUpdate("setMovie", [mode, avId])

    def getCannonBumperPos(self):
        self.notify.debug ('---------getCannonBumperPos %s' % self.cannonBumperPos)
        return self.cannonBumperPos

    def requestBumperMove(self, x, y, z):
        #do security check here
        self.cannonBumperPos = [x,y,z]
        self.sendUpdate('setCannonBumperPos',[x,y,z])

    def getPosHpr(self):
        return self.posHpr

    def getEstateId(self):
        # need this because setEstateId is required
        assert(self.notify.debug("getEstateId"))
        return self.estateId

    def getTargetId(self):
        # need this because setTargetId is required        
        return self.targetId
    

    def setCannonPosition(self, zRot, angle):
        avId = self.air.getAvatarIdFromSender()
        # a client is sending a position update for their cannon
        self.notify.debug("setCannonPosition: " + str(avId) +
                          ": zRot=" + str(zRot) + ", angle=" + str(angle))
        self.sendUpdate("updateCannonPosition", [avId, zRot, angle])

    def setCannonLit(self, zRot, angle):
        avId = self.air.getAvatarIdFromSender()
        self.__stopTimeout()
        # a client is telling us that their cannon's fuse is lit
        self.notify.debug("setCannonLit: " + str(avId) + ": zRot=" +
                          str(zRot) + ", angle=" + str(angle))
        fireTime = CannonGameGlobals.FUSE_TIME
        # set the cannon to go off in the near future
        self.sendUpdate("setCannonWillFire", [avId, fireTime, zRot, angle,
                                globalClockDelta.getRealNetworkTime()])

    def setLanded(self):
        assert(self.notify.debug("%s setLanded" % self.doId))
        self.ignore(self.air.getAvatarExitEvent(self.avId))
        self.setMovie(CannonGlobals.CANNON_MOVIE_LANDED, 0)
        self.avId = 0

    def setActive(self, active):
        # Called when the contra code is entered.  Tell the other
        # clients in the zone to toggle on/off the cannons
        assert(self.notify.debug("setActive"))
        if active < 0 or active > 1:
            self.air.writeServerEvent('suspicious', active, 'DistributedCannon.setActive value should be 0-1 range')
            return
        self.active = active
        self.sendUpdate("setActiveState", [active])

    def __startTimeout(self, timeLimit):
        # Sets the timeout counter running.  If __stopTimeout() is not
        # called before the time expires, we'll exit the avatar.  This
        # prevents avatars from hanging out in the fishing spot all
        # day.
        
        self.__stopTimeout()
        self.timeoutTask = taskMgr.doMethodLater(timeLimit,
                                                 self.__handleTimeout,
                                                 self.taskName("timeout"))

    def __stopTimeout(self):
        # Stops a previously-set timeout from expiring.
        if self.timeoutTask != None:
            taskMgr.remove(self.timeoutTask)
            self.timeoutTask = None

    def __handleTimeout(self, task):
        # Called when a timeout expires, this sends the avatar home
        self.notify.debug('Timeout expired!')
        self.__doExit()
        return Task.done

    def __handleUnexpectedExit(self, avId):
        self.notify.warning('avatar:' + str(avId) + ' has exited unexpectedly')
        self.__doExit()

    def __handleBootMessage(self, avId):
        self.notify.warning('avatar:' + str(avId) + ' got booted ')
        self.__doExit()

    def __doExit(self):
        # Take the avatar out of the cannon because he's been in it
        # too long without firing.
        self.setMovie(CannonGlobals.CANNON_MOVIE_FORCE_EXIT, self.avId)
        # this seems like a potential race condition - the ai cannon could accept new boarders before the client is cleared
        #self.avId = 0
        
