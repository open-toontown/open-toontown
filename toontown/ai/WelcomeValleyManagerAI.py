from pandac.PandaModules import *

from direct.distributed import DistributedObjectAI
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals
from toontown.hood import ZoneUtil
from toontown.hood import TTHoodDataAI
from toontown.hood import GSHoodDataAI
from direct.task import Task
import random

# These are the population thresholds we use to balance our automatic
# creation of WelcomeValleys.

# The minimum number of people that should be in the playground before
# we start to phase out the hood.
PGminimum   = 1

# The "stable" watermark; the first time we reach this number of
# people in the playground, we consider the hood to be in a stable
# state.
PGstable    = 15

# The maximum number of people in the playground before we stop adding
# people to the hood.
PGmaximum   = 20

# How often, in seconds, to report the current WelcomeValley state to
# the log.
LogInterval = 300


# The basic balancing algorithm for creating and destroying
# WelcomeValley hoods is as follows.

# There are three classes of hoods: New, Stable, and Removing.
# At any given time, there may be either zero or one New hoods, any
# number of Stable hoods, and any number of Removing hoods.
# Initially there are no hoods.

# When a new avatar arrives, it will be assigned to the New hood if
# there is one; otherwise, it will be assigned to the Stable hood with
# the smallest playground population, unless there are no Stable hoods
# with a population less than PGmaximum (in which case a New hood will
# be created).

# When a New hood is created, it will continue to be considered New
# (and thus receive all newly arriving avatars), until its playground
# population reaches PGstable, at which point the hood is moved into
# the Stable pool.

# If at any point the playground population of a hood in the Stable
# pool decreases below PGminimum (and it is not the only hood
# remaining), it is moved to the Removing pool.  A suitable
# replacement hood is chosen using the algorithm for a new avatar,
# above, and this new hood is associated with the Removing hood.  Any
# avatar that requests a zone change to or within a Removing hood is
# instead redirected the hood's replacement.  (Note that clients who
# are teleporting to a friend in a Removing hood do not request this
# zone change via the AI, and so will not be redirected to a different
# hood--they will still arrive in the same hood with their friend.)
# For the purposes of balancing, we consider the replacement hood 
# immediately contains its population plus that of the Removing
# hood.

# Finally, if the total population of any hood reaches zero, the hood
# is completely removed.

# There are a few considerations that have led to this algorithm.
# Firstly, we want to minimize the amount of time a playground is
# nearly empty; you should always be able to enter the game and see
# several people in the playground.  Thus, we aggressively fill a New
# hood up quickly, instead of distributing new avatars evenly among
# all available hoods; and once we decide to remove a hood we
# aggressively move avatars off it at the first opportunity.
# Secondly, we would like to keep avatars together whenever possible;
# thus, when we decide to remove a hood, we choose only one hood to be
# its replacement, and all avatars are moved from the source hood to
# the same replacement hood (even if this will result in an overfull
# replacement hood).


class WelcomeValleyManagerAI(DistributedObjectAI.DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory("WelcomeValleyManagerAI")

    def __init__(self, air):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        
        self.welcomeValleyAllocator = UniqueIdAllocator(
            ToontownGlobals.WelcomeValleyBegin // 2000,
            ToontownGlobals.WelcomeValleyEnd // 2000 - 1)
        self.welcomeValleys = {}
        self.avatarZones = {}

        self.newHood = None
        self.stableHoods = []
        self.removingHoods = []

    def generate(self):
        DistributedObjectAI.DistributedObjectAI.generate(self)

        if simbase.config.GetBool('report-welcome-valleys', 0):
            self.doReportLater()

    def delete(self):
        name = self.taskName("WelcomeValleyLog")
        taskMgr.remove(name)
        self.ignoreAll()
        DistributedObjectAI.DistributedObjectAI.delete(self)

# now done locally on the AI
##     def clientSetZone(self, zoneId):
##         """
##         This is used by the client to inform the AI which zone he is
##         going to.  It is mainly used to balance the WelcomeValley zones,
##         so the AI can know how many avatars are in each WelcomeValley.
##         """
##         avId = self.air.getAvatarIdFromSender()
##         lastZoneId = self.avatarSetZone(avId, zoneId)

##         # Temporary kludge to ensure ghost mode doesn't remain on
##         # longer than it should--that's probably the result of an
##         # unintended bug.  If ghost mode is on, we turn it off
##         # whenever the client switches zones.  Note that this is not a
##         # real solution, since a hacked client can simply not send the
##         # clientSetZone messages.
##         avatar = self.air.doId2do.get(avId)
##         if avatar and avatar.ghostMode:
##             self.air.writeServerEvent('suspicious', avId, 'has ghost mode %s transitioning from zone %s to %s' % (avatar.ghostMode, lastZoneId, zoneId))
##             if avatar.ghostMode == 1:
##                 avatar.b_setGhostMode(0)

##         if avatar and avatar.cogIndex >= 0:
##             if (lastZoneId != 11100 and lastZoneId != 12100 and lastZoneId != 13100 ) or \
##                (zoneId < 61000 and zoneId != 11000 and zoneId != 12000 and zoneId != 13000):
##                 self.air.writeServerEvent('suspicious', avId, 'has cogIndex %s transitioning from zone %s to %s' % (avatar.cogIndex, lastZoneId, zoneId))
##                 avatar.b_setCogIndex(-1)
        
    def toonSetZone(self, avId, zoneId):
        lastZoneId = self.avatarSetZone(avId, zoneId)

        # Temporary kludge to ensure ghost mode doesn't remain on
        # longer than it should--that's probably the result of an
        # unintended bug.  If ghost mode is on, we turn it off
        # whenever the client switches zones.  Note that this is not a
        # real solution, since a hacked client can simply not send the
        # clientSetZone messages.
        avatar = self.air.doId2do.get(avId)
        if avatar and avatar.ghostMode:
            if avatar.ghostMode == 1:
                avatar.b_setGhostMode(0)

        if avatar and avatar.cogIndex >= 0:
            if (lastZoneId != 11100 and lastZoneId != 12100 and lastZoneId != 13100 ) or \
               (zoneId < 61000 and zoneId != 11000 and zoneId != 12000 and zoneId != 13000):
                avatar.b_setCogIndex(-1)

    def avatarSetZone(self, avId, zoneId):
        lastZoneId = self.avatarZones.get(avId)
        if lastZoneId == zoneId:
            return lastZoneId

        if zoneId == None:
            self.notify.debug("Avatar %s has left the shard." % (avId))
            del self.avatarZones[avId]
            self.ignore(self.air.getAvatarExitEvent(avId))
        else:
            self.notify.debug("Avatar %s is now in zone %s." % (avId, zoneId))

            # First, add the avatar into his/her new zone.  We must do
            # this first so we don't risk momentarily bringing the
            # hood population to 0.
            hoodId = ZoneUtil.getHoodId(zoneId)
            
            # if this is a GS hoodId, just grab the TT hood
            if (hoodId % 2000) < 1000:
                hood = self.welcomeValleys.get(hoodId)
            else:
                hood = self.welcomeValleys.get(hoodId - 1000)

            if hood:
                hood[0].incrementPopulation(zoneId, 1)
                if (hood == self.newHood) and hood[0].getPgPopulation() >= PGstable:
                    # This is now a stable hood.
                    self.__newToStable(hood)
                    
            self.avatarZones[avId] = zoneId

        if lastZoneId == None:
            # This is the first time we have heard from this avatar.
            self.acceptOnce(self.air.getAvatarExitEvent(avId),
                            self.avatarLogout, extraArgs=[avId])
        else:
            # Now, remove the avatar from his/her previous zone.
            lastHoodId = ZoneUtil.getHoodId(lastZoneId)

            # if this is a GS hoodId, just grab the TT hood
            if (lastHoodId % 2000) < 1000:
                hood = self.welcomeValleys.get(lastHoodId)
            else:
                hood = self.welcomeValleys.get(lastHoodId - 1000)

            if hood:
                hood[0].incrementPopulation(lastZoneId, -1)
                if hood[0].getHoodPopulation() == 0:
                    self.__hoodIsEmpty(hood)

                elif (hood != self.newHood) and not hood[0].hasRedirect() and \
                     hood[0].getPgPopulation() < PGminimum:
                    self.__stableToRemoving(hood)

        return lastZoneId

    def avatarLogout(self, avId):
        self.avatarSetZone(avId, None)

    def makeNew(self, hoodId):
        # Makes the indicated hoodId new, if possible.  Used for magic
        # word purposes only.  Returns a string describing the action.
        hood = self.welcomeValleys.get(hoodId)
        if hood == None:
            return "Hood %s is unknown." % (hoodId)
        if hood == self.newHood:
            return "Hood %s is already new." % (hoodId)
        if self.newHood != None:
            self.__newToStable(self.newHood)

        if hood in self.removingHoods:
            self.removingHoods.remove(hood)
            hood[0].setRedirect(None)
        else:
            self.stableHoods.remove(hood)

        self.newHood = hood
        return "Hood %s is now New." % (hoodId)

    def makeStable(self, hoodId):
        # Moves the indicated hoodId to the Stable pool, if possible.
        # Used for magic word purposes only.  Returns a string
        # describing the action.
        hood = self.welcomeValleys.get(hoodId)
        if hood == None:
            return "Hood %s is unknown." % (hoodId)
        if hood in self.stableHoods:
            return "Hood %s is already Stable." % (hoodId)

        if hood == self.newHood:
            self.__newToStable(hood)
        else:
            self.removingHoods.remove(hood)
            hood[0].setRedirect(None)
            self.stableHoods.append(hood)

        return "Hood %s is now Stable." % (hoodId)

    def makeRemoving(self, hoodId):
        # Moves the indicated hoodId to the Removing pool, if possible.
        # Used for magic word purposes only.  Returns a string
        # describing the action.
        hood = self.welcomeValleys.get(hoodId)
        if hood == None:
            return "Hood %s is unknown." % (hoodId)
        if hood in self.removingHoods:
            return "Hood %s is already Removing." % (hoodId)

        if hood == self.newHood:
            self.__newToStable(hood)

        self.__stableToRemoving(hood)

        return "Hood %s is now Removing." % (hoodId)

    def checkAvatars(self):
        # Checks that all of the avatars recorded as being logged in
        # are actually still in the doId2do map, and logs out any that
        # are not.  Returns a list of the removed avId's.  This is
        # normally used for magic word purposes only.
        removed = []
        for avId in self.avatarZones.keys():
            if avId not in self.air.doId2do:
                # Here's one for removing.
                removed.append(avId)
                self.avatarLogout(avId)

        return removed

    def __newToStable(self, hood):
        # This New hood's population has reached the stable limit;
        # mark it as a Stable hood.
        self.notify.info("Hood %s moved to Stable." % (hood[0].zoneId))

        assert(hood == self.newHood)
        self.newHood = None
        self.stableHoods.append(hood)

    def __stableToRemoving(self, hood):
        # This hood's population has dropped too low;
        # schedule it for removal.
        self.notify.info("Hood %s moved to Removing." % (hood[0].zoneId))

        assert(hood in self.stableHoods)
        self.stableHoods.remove(hood)
        replacementHood = self.chooseWelcomeValley(allowCreateNew = 0)
        if replacementHood == None:
            # Hmm, we couldn't find a suitable
            # replacement, so just keep this one.
            self.stableHoods.append(hood)
        else:
            hood[0].setRedirect(replacementHood)
            self.removingHoods.append(hood)

    def __hoodIsEmpty(self, hood):
        self.notify.info("Hood %s is now empty." % (hood[0].zoneId))

        replacementHood = hood[0].replacementHood
        self.destroyWelcomeValley(hood)

        # Also check the hood this one is redirecting to; we might
        # have just emptied it too.
        if replacementHood and replacementHood[0].getHoodPopulation() == 0:
            self.__hoodIsEmpty(replacementHood)
        
            

    def avatarRequestZone(self, avId, origZoneId):
        # This services a redirect-zone request for a particular
        # avatar.  The client is requesting to go to the indicated
        # zoneId, which should be a WelcomeValley zoneId; the AI
        # should choose which particular WelcomeValley to direct the
        # client to.
        
        if not ZoneUtil.isWelcomeValley(origZoneId):
            # All requests for static zones are returned unchanged.
            return origZoneId
        
        origHoodId = ZoneUtil.getHoodId(origZoneId)
        hood = self.welcomeValleys.get(origHoodId)
        if not hood:
            # If we don't know this hood, choose a new one.
            hood = self.chooseWelcomeValley()
        
        if not hood:
            self.notify.warning("Could not create new WelcomeValley hood for avatar %s." % (avId))
            zoneId = ZoneUtil.getCanonicalZoneId(origZoneId)
        else:
            # use TTC hoodId
            hoodId = hood[0].getRedirect().zoneId
            zoneId = ZoneUtil.getTrueZoneId(origZoneId, hoodId)

        # Even though the client might choose not to go to the
        # indicated zoneId for some reason, we will consider the
        # client as having gone there immediately, for the purposes of
        # balancing.  If the client goes somewhere else instead, it
        # will tell us that and we can correct this.
        self.avatarSetZone(avId, zoneId)

        return zoneId
        

    def requestZoneIdMessage(self, origZoneId, context):
        """

        This message is sent from the client to request a new zoneId
        for a transition to WelcomeValley.

        """
        avId = self.air.getAvatarIdFromSender()
        zoneId = self.avatarRequestZone(avId, origZoneId)
            
        self.sendUpdateToAvatarId(avId, "requestZoneIdResponse",
                                  [zoneId, context])


    def chooseWelcomeValley(self, allowCreateNew = 1):
        # Picks a hood to assign a new avatar to.  If allowCreateNew
        # is 1, a new hood may be created if necessary.

        # First, if we have a New hood, prefer that one.
        if self.newHood:
            return self.newHood

        # Next, choose the Stable hood with the smallest playground
        # population.
        bestHood = None
        bestPopulation = None
        for hood in self.stableHoods:
            population = hood[0].getPgPopulation()
            if bestHood == None or population < bestPopulation:
                bestHood = hood
                bestPopulation = population

        # Unless there are no hoods with a small-enough population, in
        # which case we create another New hood.
        if allowCreateNew and (bestHood == None or bestPopulation >= PGmaximum):
            self.newHood = self.createWelcomeValley()
            if self.newHood:
                self.notify.info("Hood %s is New." % self.newHood[0].zoneId)
                return self.newHood

        return bestHood

    def createWelcomeValley(self):
        # Creates new copy of ToontownCentral and Goofy Speedway and returns
        # thier HoodDataAI.  Returns None if no new hoods can be created.
        
        index = self.welcomeValleyAllocator.allocate()
        if index == -1:
            return None

        # TTC
        ttHoodId = index * 2000
        ttHood = TTHoodDataAI.TTHoodDataAI(self.air, ttHoodId)
        self.air.startupHood(ttHood)

        # GS
        gsHoodId = index * 2000 + 1000
        gsHood = GSHoodDataAI.GSHoodDataAI(self.air, gsHoodId)
        self.air.startupHood(gsHood)

        # both hoods are stored in a tuple and referenced by the TTC hoodId
        self.welcomeValleys[ttHoodId] = (ttHood, gsHood)
                
        # create a pond bingo manager ai for the new WV
        if simbase.wantBingo:
            self.notify.info('creating bingo mgr for Welcome Valley %s' %  ttHoodId)
            self.air.createPondBingoMgrAI(ttHood)

        return (ttHood, gsHood)

    def destroyWelcomeValley(self, hood):
        hoodId = hood[0].zoneId
        assert((hoodId % 2000) == 0)

        del self.welcomeValleys[hoodId]
        self.welcomeValleyAllocator.free(hoodId / 2000)
        self.air.shutdownHood(hood[0])
        self.air.shutdownHood(hood[1])

        if self.newHood == hood:
            self.newHood = None
        elif hood in self.removingHoods:
            self.removingHoods.remove(hood)
        elif hood in self.stableHoods:
            self.stableHoods.remove(hood)

    def doReportLater(self):
        name = self.taskName("WelcomeValleyLog")
        taskMgr.remove(name)
        taskMgr.doMethodLater(LogInterval, self.doReportTask, name)

    def doReportTask(self, task):
        self.reportWelcomeValleys()
        self.doReportLater()
        return Task.done

    def getAvatarCount(self):
        # Players
        # the Welcome Valley hoods.
        if simbase.fakeDistrictPopulations:
            return 0
        answer = 0
        hoodIds = self.welcomeValleys.keys()
        for hoodId in hoodIds:
            hood = self.welcomeValleys[hoodId]
            answer += hood[0].getHoodPopulation()

        return answer

    def reportWelcomeValleys(self):
        # Writes a message to the log file showing the current state
        # of the Welcome Valley hoods.

        self.notify.info("Current Welcome Valleys:")
        hoodIds = self.welcomeValleys.keys()
        hoodIds.sort()
        for hoodId in hoodIds:
            hood = self.welcomeValleys[hoodId]
            if hood == self.newHood:
                flag = "N"
            elif hood in self.removingHoods:
                flag = "R"
            else:
                flag = " "

            self.notify.info("%s %s %s/%s" % (
                hood[0].zoneId, flag,
                hood[0].getPgPopulation(), hood[0].getHoodPopulation()))
            
