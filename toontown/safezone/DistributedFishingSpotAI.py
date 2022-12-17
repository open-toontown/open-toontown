from otp.ai.AIBase import *

from direct.distributed import DistributedObjectAI
import random

from toontown.toonbase import ToontownAccessAI
from toontown.toonbase import TTLocalizer
from direct.directnotify import DirectNotifyGlobal
from toontown.fishing import FishGlobals

class DistributedFishingSpotAI(DistributedObjectAI.DistributedObjectAI):

    notify = DirectNotifyGlobal.directNotify.newCategory("DistributedFishingSpotAI")
                    
    def __init__(self, air, pond, x, y, z, h, p, r):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        self.notify.debug("init")
        self.posHpr = (x, y, z, h, p, r)
        self.avId = 0
        self.timeoutTask = None
        self.pond = pond
        self.wantTimeouts = simbase.config.GetBool("want-fishing-timeouts", 1)

    def delete(self):
        self.notify.debug("delete")
        taskMgr.remove(self.taskName("clearEmpty"))
        self.ignore(self.air.getAvatarExitEvent(self.avId))
        self.__stopTimeout()
        self.d_setMovie(FishGlobals.ExitMovie)
        self.avId = 0
        self.pond = None
        DistributedObjectAI.DistributedObjectAI.delete(self)

    def getPondDoId(self):
        return self.pond.getDoId()

    def requestEnter(self):
        # A client is requesting sole use of the fishing spot.  If
        # it's available, he can have it.
        avId = self.air.getAvatarIdFromSender()
        self.notify.debug("requestEnter: avId: %s" % (avId))
        if self.avId == avId:
            # This seems to happen in the estates when we get a double request
            # coming out of fishing directly onto the dock
            self.notify.debug("requestEnter: avId %s is already fishing here" % (avId))
            return
        
        # Check that player has full access
        if not ToontownAccessAI.canAccess(avId, self.zoneId):
            self.sendUpdateToAvatarId(avId, "rejectEnter", [])
            return
        
        if self.avId == 0:
            self.avId = avId
            # Tell the pond we are here
            self.pond.addAvSpot(avId, self)
            self.acceptOnce(self.air.getAvatarExitEvent(self.avId),
                            self.unexpectedExit)
            self.__stopTimeout()
            self.d_setOccupied(self.avId)
            self.d_setMovie(FishGlobals.EnterMovie)
            self.__startTimeout(FishGlobals.CastTimeout)
            self.air.writeServerEvent("fished_enter",self.avId, "%s" % (self.zoneId))
        else:
            self.sendUpdateToAvatarId(avId, "rejectEnter", [])

    def requestExit(self):
        # The client within the spot is ready to leave.
        avId = self.air.getAvatarIdFromSender()
        self.notify.debug("requestExit: avId: %s" % (avId))
        if not self.validate(avId, (self.avId == avId), "requestExit: avId is not fishing in this spot"):
            return
        self.normalExit()

    def d_setOccupied(self, avId):
        self.notify.debug("setOccupied: %s" % (avId))
        self.sendUpdate("setOccupied", [avId])

    def doCast(self, power, heading):
        # The client begins a cast.
        avId = self.air.getAvatarIdFromSender()
        self.notify.debug("doCast: avId: %s" % (avId))
        if not self.validate(avId, (self.avId == avId),
                             "doCast: avId is not fishing in this spot"):
            return
        if not self.validate(avId, (0.0 <= power <= 1.0),
                             ("doCast: power: %s is out of range" % power)):
            return
        if not self.validate(avId,
                             (-FishGlobals.FishingAngleMax <= heading <= FishGlobals.FishingAngleMax),
                             ("doCast: heading: %s is out of range" % heading)):
            return

        av = self.air.doId2do.get(self.avId)
        if not self.validate(avId, (av), "doCast: avId not currently logged in to this AI"):
            return
        
        self.__stopTimeout()
        money = av.getMoney()
        # cast cost is based on rod now
        castCost = FishGlobals.getCastCost(av.getFishingRod())
        
        if money < castCost:
            # Not enough money to cast
            self.normalExit()
            return
        
        self.air.writeServerEvent("fished_cast", avId, "%s|%s" %(av.getFishingRod(), castCost))
        av.b_setMoney(money - castCost)
        self.d_setMovie(FishGlobals.CastMovie, power=power, h=heading)
        self.__startTimeout(FishGlobals.CastTimeout)
                    
    def d_setMovie(self, mode, code=0, itemDesc1=0, itemDesc2=0, itemDesc3=0,  power=0, h=0):
        self.notify.debug(
            "setMovie: mode:%s code:%s itemDesc1:%s itemDesc2:%s itemDesc3:%s power:%s h:%s" %
            (mode, code, itemDesc1, itemDesc2, itemDesc3, power, h))
        self.sendUpdate("setMovie", [mode, code, itemDesc1, itemDesc2, itemDesc3, power, h])

    def getPosHpr(self):
        # This is needed because setPosHpr is a required field.
        return self.posHpr

    def __startTimeout(self, timeLimit):
        self.notify.debug("__startTimeout")
        # Sets the timeout counter running.  If __stopTimeout() is not
        # called before the time expires, we'll exit the avatar.  This
        # prevents avatars from hanging out in the fishing spot all
        # day.
        self.__stopTimeout()
        if self.wantTimeouts:
            self.timeoutTask = taskMgr.doMethodLater(timeLimit,
                                                     self.__handleTimeout,
                                                     self.taskName("timeout"))
            
    def __stopTimeout(self):
        self.notify.debug("__stopTimeout")
        # Stops a previously-set timeout from expiring.
        if self.timeoutTask:
            taskMgr.remove(self.timeoutTask)
            self.timeoutTask = None

    def __handleTimeout(self, task):
        self.notify.debug("__handleTimeout")
        # Called when a timeout expires, this sends the avatar home.
        self.normalExit()

    def cleanupAvatar(self):
        # Tell the pond we are leaving
        self.air.writeServerEvent("fished_exit",self.avId, "%s" % (self.zoneId))
        self.pond.removeAvSpot(self.avId, self)
        self.ignore(self.air.getAvatarExitEvent(self.avId))
        self.__stopTimeout()
        self.avId = 0

    def normalExit(self):
        self.notify.debug("normalExit")
        # Send the avatar out of the fishing spot, either because of
        # his own request or due to some other cause (like a timeout).
        self.cleanupAvatar()
        self.d_setMovie(FishGlobals.ExitMovie)
        # Give everyone enough time to play the goodbye movie,
        # then dump the avatar.
        taskMgr.doMethodLater(1.2, self.__clearEmpty,
                              self.taskName("clearEmpty"))

    def __clearEmpty(self, task=None):
        self.notify.debug("__clearEmpty")
        self.d_setOccupied(0)

    def unexpectedExit(self):
        self.notify.debug("unexpectedExit")
        # Called when the avatar in the fishing spot vanishes.
        # Tell the pond we are leaving
        self.cleanupAvatar()
        self.d_setOccupied(0)

    def hitTarget(self, code, item):
        self.notify.debug("hitTarget: code: %s item: %s" % (code, item))
        if code == FishGlobals.QuestItem:
            self.d_setMovie(FishGlobals.PullInMovie, code, item)
        elif code in (FishGlobals.FishItem,
                      FishGlobals.FishItemNewEntry,
                      FishGlobals.FishItemNewRecord):
            genus, species, weight = item.getVitals()
            self.d_setMovie(FishGlobals.PullInMovie, code, genus, species, weight)
        elif code == FishGlobals.BootItem:
            self.d_setMovie(FishGlobals.PullInMovie, code)
        elif code == FishGlobals.JellybeanItem:
            self.d_setMovie(FishGlobals.PullInMovie, code, item)
        else:
            self.d_setMovie(FishGlobals.PullInMovie, code)
        self.__startTimeout(FishGlobals.CastTimeout)

    def d_sellFishComplete(self, avId, trophyResult, numFishCaught):
        self.sendUpdateToAvatarId(avId, "sellFishComplete", [trophyResult, numFishCaught])

    def sellFish(self):
        # The client asks to sell his fish
        gotTrophy = -1
        avId = self.air.getAvatarIdFromSender()
        av = self.air.doId2do.get(self.avId)
        self.notify.debug("sellFish: avId: %s" % (avId))
        if not self.validate(avId, (simbase.wantBingo), "sellFish: Currently, you can only do this if bingo is turned on"):
            gotTrophy = False
        elif not self.validate(avId, (self.pond.hasPondBingoManager()), "sellFish: Currently, you can only do this during bingo night"):
            gotTrophy = False
        elif not self.validate(avId, (self.avId == avId), "sellFish: avId is not fishing in this spot"):
            gotTrophy = False
        elif not self.validate(avId, (av), "sellFish: avId not currently logged in to this AI"):
            gotTrophy = False

        if gotTrophy is -1:
            gotTrophy = self.air.fishManager.creditFishTank(av)
            self.d_sellFishComplete(avId, gotTrophy, len(av.fishCollection))
        else:
            self.d_sellFishComplete(avId, False, 0)
            
