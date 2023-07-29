from toontown.toonbase.ToontownGlobals import *
from otp.ai.AIBase import *
from direct.task.Task import Task
from .HouseGlobals import *
from toontown.effects import DistributedFireworkShowAI
from direct.fsm import ClassicFSM
from direct.distributed import ClockDelta

class DistributedFireworksCannonAI(DistributedFireworkShowAI.DistributedFireworkShowAI):

    """
    DistributedFireworksCannon is derived from DistributedFireworkShow so
    we can add a collision object to bring up a gui:
    When a user bumps into a fireworks cannon, an interface will pop up
    giving the user a choice of which firework/color he wants to shoot.
    """

    notify = directNotify.newCategory("DistributedFireworksCannonAI")

    def __init__(self, air, x, y, z):
        DistributedFireworkShowAI.DistributedFireworkShowAI.__init__(self, air)
        self.pos = [x,y,z]
        self.busy = 0

    def delete(self):
        assert(self.notify.debug("delete()"))
        self.ignoreAll()
        DistributedFireworkShowAI.DistributedFireworkShowAI.delete(self)

    def freeAvatar(self, avId):
        # Free this avatar, probably because he requested interaction while
        # I was busy. This can happen when two avatars request interaction
        # at the same time. The AI will accept the first, sending a setMovie,
        # and free the second
        self.sendUpdateToAvatarId(avId, "freeAvatar", [])
        return

    def avatarEnter(self):
        self.notify.debug("avatarEnter")
        avId = self.air.getAvatarIdFromSender()
        # this avatar has come within range
        self.notify.debug("avatarEnter: %s" % (avId))

        # If we are busy, free this new avatar
        if self.busy:
            self.notify.debug("already busy with: %s" % (self.busy))
            self.freeAvatar(avId)
            return

        # Fetch the actual avatar object
        av = self.air.doId2do.get(avId)        
        if not av:
            self.notify.warning("av %s not in doId2do tried to transfer money" % (avId))
            return

        # Flag us as busy with this avatar Id
        self.busy = avId

        # Handle unexpected exit
        self.acceptOnce(self.air.getAvatarExitEvent(avId),
                        self.__handleUnexpectedExit, extraArgs=[avId])
        self.acceptOnce("bootAvFromEstate-"+str(avId),
                        self.__handleBootMessage, extraArgs=[avId])

        # Tell the client how to react
        # We need to eventually restrict this to the estate owners
        self.sendUpdate("setMovie", [FIREWORKS_MOVIE_GUI, avId,
                                     ClockDelta.globalClockDelta.getRealNetworkTime()])

    def avatarExit(self):
        self.notify.debug("avatarExit")
        avId = self.air.getAvatarIdFromSender()

        if self.busy == avId:
            self.sendClearMovie(None)
        self.freeAvatar(avId)

        
    def __handleUnexpectedExit(self, avId):
        self.notify.warning('avatar:' + str(avId) + ' has exited unexpectedly')
        self.sendClearMovie(None)

    def __handleBootMessage(self, avId):
        self.notify.warning('avatar:' + str(avId) + ' got booted ')
        self.sendClearMovie(None)

    def sendClearMovie(self, task):
        assert(self.notify.debug('sendClearMovie()'))
        # Ignore unexpected exits on whoever I was busy with
        self.ignoreAll()
        self.busy = 0
        self.sendUpdate("setMovie", [FIREWORKS_MOVIE_CLEAR, 0,
                                     ClockDelta.globalClockDelta.getRealNetworkTime()])
        return Task.done

    def doneShooting(self):
        avId = self.air.getAvatarIdFromSender()
        av = self.air.doId2do.get(avId)
        
        if not av:
            self.notify.warning("av %s not in doId2do tried to transfer money" % (avId))
            return
        
        self.sendClearMovie(None)
        self.freeAvatar(avId)

    def getPosition(self):
        # This is needed because setPosition is a required field.
        return self.pos

    
    
