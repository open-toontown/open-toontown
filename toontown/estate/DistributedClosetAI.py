from otp.ai.AIBaseGlobal import *
from pandac.PandaModules import *
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM
from direct.distributed import ClockDelta
from . import DistributedFurnitureItemAI
from direct.task.Task import Task
from direct.fsm import State
from toontown.toon import ToonDNA
from toontown.ai import DatabaseObject
from toontown.toon import DistributedToonAI
from . import ClosetGlobals
from toontown.toon import InventoryBase

class DistributedClosetAI(DistributedFurnitureItemAI.DistributedFurnitureItemAI):

    if __debug__:
        notify = DirectNotifyGlobal.directNotify.newCategory('DistributedClosetAI')

    def __init__(self, air, furnitureMgr, item):
        DistributedFurnitureItemAI.DistributedFurnitureItemAI.__init__(
            self, air, furnitureMgr, item)
        self.ownerId = self.furnitureMgr.house.ownerId
        self.ownerAv = None
        self.timedOut = 0
        self.busy = 0
        self.customerDNA = None
        self.customerId = None
        self.deletedTops = []
        self.deletedBottoms = []
        self.dummyToonAI = None #in case we open a closet of someone not online, keep track of it

    def delete(self):
        self.notify.debug("delete()")
        self.ignoreAll()
        self.customerDNA = None
        self.customerId = None
        del self.deletedTops
        del self.deletedBottoms
        taskMgr.remove(self.uniqueName('clearMovie'))
        DistributedFurnitureItemAI.DistributedFurnitureItemAI.delete(self)

    def freeAvatar(self, avId):
        self.notify.debug("freeAvatar %d" % avId)
        # Free this avatar, probably because he requested interaction while
        # I was busy. This can happen when two avatars request interaction
        # at the same time. The AI will accept the first, sending a setMovie,
        # and free the second
        self.sendUpdateToAvatarId(avId, "freeAvatar", [])

    def enterAvatar(self):
        self.notify.debug("enterAvatar")
        avId = self.air.getAvatarIdFromSender()
        # this avatar has come within range
        assert(self.debugPrint("avatar opening closet: " + str(avId)))

        # If the closet is already being used, free this avatar
        if self.busy > 0:
            self.freeAvatar(avId)
            return
        
        # Store the original customer DNA so we can revert if a disconnect
        # happens
        av = self.air.doId2do.get(avId)
        if not av:
            return #something has gone horridly wrong lets not crash the ai
        self.customerDNA = ToonDNA.ToonDNA()
        self.customerDNA.makeFromNetString(av.getDNAString())
        self.customerId = avId
        self.busy = avId
        print(("av %s: entering closet with shirt(%s,%s,%s,%s) and shorts(%s,%s)" % (avId,
                                                                                     self.customerDNA.topTex,
                                                                                     self.customerDNA.topTexColor, 
                                                                                     self.customerDNA.sleeveTex, 
                                                                                     self.customerDNA.sleeveTexColor,
                                                                                     self.customerDNA.botTex,
                                                                                     self.customerDNA.botTexColor)))
        
        # Handle unexpected exit
        self.acceptOnce(self.air.getAvatarExitEvent(avId),
                        self.__handleUnexpectedExit, extraArgs=[avId])
        self.acceptOnce("bootAvFromEstate-"+str(avId),
                        self.__handleBootMessage, extraArgs=[avId])

        # Find the owner of the closet
        if self.ownerId:
            self.ownerAv = None
            if self.ownerId in self.air.doId2do:
                self.ownerAv = self.air.doId2do[self.ownerId]
                self.__openCloset()
            else:
                self.air.dbInterface.queryObject(self.air.dbId, self.ownerId, self.__handleOwnerQuery,
                                             self.air.dclassesByName['DistributedToonAI'])
        else:
            print("this house has no owner, therefore we can't use the closet")
            # send a reset message to the client.  same as a completed purchase
            self.completePurchase(avId)

        
    def __openCloset(self):
        self.notify.debug("__openCloset")
        topList = self.ownerAv.getClothesTopsList()
        botList = self.ownerAv.getClothesBottomsList()
        
        self.sendUpdate("setState", [ClosetGlobals.OPEN,
                                     self.customerId, self.ownerAv.doId,
                                     self.ownerAv.dna.getGender(),
                                     topList, botList])

        # Start the timer
        taskMgr.doMethodLater(ClosetGlobals.TIMEOUT_TIME, 
                              self.sendTimeoutMovie,
                              self.uniqueName('clearMovie'))
        
    def __gotOwnerAv(self, db, retCode):
        print ("gotOwnerAv information")
        if retCode == 0 and 'setDNAString' in db.values:
            aidc = self.air.dclassesByName['DistributedToonAI']
            self.ownerAv = DistributedToonAI.DistributedToonAI(self.air)
            self.ownerAv.doId = db.doId
            print(("owner doId = %d" % db.doId))
            self.ownerAv.inventory = InventoryBase.InventoryBase(self.ownerAv)
            self.ownerAv.teleportZoneArray = []
            
            try:
                db.fillin(self.ownerAv, aidc)
            except Exception as theException:
                assert(self.notify.debug('suspicious: customer %s, owner %s: Exception = %s: DistributedClosetAI.__gotOwnerAv: invalid db' %(self.customerId, db.doId, str(theException))))
                assert(self.notify.debug("FIXME: %s: DistributedClosetAI.__gotOwnerAv: This toon's DB is so broken: look at setClothesBottomsList." %(db.doId)))
                self.air.writeServerEvent('suspicious', self.customerId, 'DistributedClosetAI.__gotOwnerAv: invalid db. ownerId %s' % (db.doId))
                self.air.writeServerEvent('FIXME', db.doId, "DistributedClosetAI.__gotOwnerAv: This toon's DB is so broken: look at setClothesBottomsList.")
                return
            
            self.__openCloset()
            self.dummyToonAI = self.ownerAv

    def removeItem(self, trashBlob, which):
        trashedDNA = ToonDNA.ToonDNA()
       
        # AI side verify trashBlob
        if not trashedDNA.isValidNetString(trashBlob):
            self.air.writeServerEvent('suspicious', avId, 'DistributedClosetAI.removeItem: invalid dna: %s' % trashBlob)
            return

        trashedDNA.makeFromNetString(trashBlob)
        # make a list of things to be deleted later, when user is "finished"
        if which & ClosetGlobals.SHIRT:
            self.deletedTops.append([trashedDNA.topTex, trashedDNA.topTexColor,
                                     trashedDNA.sleeveTex, trashedDNA.sleeveTexColor])
        if which & ClosetGlobals.SHORTS:
            self.deletedBottoms.append([trashedDNA.botTex, trashedDNA.botTexColor])

    def __finalizeDelete(self, avId):
        av = self.air.doId2do[avId]
        for top in self.deletedTops:
            av.removeItemInClothesTopsList(top[0], top[1], top[2], top[3])
        for bot in self.deletedBottoms:
            av.removeItemInClothesBottomsList(bot[0], bot[1])
        # empty the delete lists
        self.deletedTops = []
        self.deletedBottoms = []
        av.b_setClothesTopsList(av.getClothesTopsList())
        av.b_setClothesBottomsList(av.getClothesBottomsList())

    def updateToonClothes(self, av, blob):
        # This is what the client has told us the new DNA should be
        proposedDNA = ToonDNA.ToonDNA()
        proposedDNA.makeFromNetString(blob)

        # Don't completely trust the client.  Enforce that only the clothes
        # change here.  This eliminates the possibility of the gender, species, etc
        # of the toon changing, or a bug being exploited.
        updatedDNA = ToonDNA.ToonDNA()
        updatedDNA.makeFromNetString(self.customerDNA.makeNetString())
        updatedDNA.topTex = proposedDNA.topTex
        updatedDNA.topTexColor = proposedDNA.topTexColor
        updatedDNA.sleeveTex = proposedDNA.sleeveTex
        updatedDNA.sleeveTexColor = proposedDNA.sleeveTexColor
        updatedDNA.botTex = proposedDNA.botTex
        updatedDNA.botTexColor = proposedDNA.botTexColor
        updatedDNA.torso = proposedDNA.torso

        av.b_setDNAString(updatedDNA.makeNetString())
        return updatedDNA
        
    def setDNA(self, blob, finished, which):
        assert(self.notify.debug('setDNA(): %s, finished=%s' % (self.timedOut, finished)))
        avId = self.air.getAvatarIdFromSender()
        if avId != self.customerId:
            if self.customerId:
                self.air.writeServerEvent('suspicious', avId, 'DistributedClosetAI.setDNA current customer %s' % (self.customerId))
                self.notify.warning("customerId: %s, but got setDNA for: %s" % (self.customerId, avId))
            return
        if (avId in self.air.doId2do):
            av = self.air.doId2do[avId]

            # make sure the DNA is valid
            testDNA = ToonDNA.ToonDNA()
            if not testDNA.isValidNetString(blob):
                self.air.writeServerEvent('suspicious', avId, 'DistributedClosetAI.setDNA: invalid dna: %s' % blob)
                return
            
            if (finished == 2):
                # Set the DNA string now, since we haven't done it yet
                newDNA = self.updateToonClothes(av, blob)

                # SDN:  only add clothes if they have been changed (i.e. if (which & n) == 1)
                if which & ClosetGlobals.SHIRT:
                    self.notify.debug ("changing to shirt(%s,%s,%s,%s) and putting old shirt(%s,%s,%s,%s) in closet" % (newDNA.topTex,
                                                                                                                        newDNA.topTexColor,
                                                                                                                        newDNA.sleeveTex,
                                                                                                                        newDNA.sleeveTexColor,
                                                                                                                        self.customerDNA.topTex,
                                                                                                                        self.customerDNA.topTexColor, 
                                                                                                                        self.customerDNA.sleeveTex, 
                                                                                                                        self.customerDNA.sleeveTexColor))
                    # replace newDNA in closet with customerDNA (since we are now wearing newDNA)
                    if av.replaceItemInClothesTopsList(newDNA.topTex,
                                                       newDNA.topTexColor,
                                                       newDNA.sleeveTex,
                                                       newDNA.sleeveTexColor,
                                                       self.customerDNA.topTex,
                                                       self.customerDNA.topTexColor, 
                                                       self.customerDNA.sleeveTex, 
                                                       self.customerDNA.sleeveTexColor) == 1:
                        av.b_setClothesTopsList(av.getClothesTopsList())
                    else:
                        self.notify.warning('Closet: setDNA() - unable to save old tops - we exceeded the tops list length')
                if which & ClosetGlobals.SHORTS:
                    self.notify.debug("changing to bottom(%s,%s) and putting old bottom (%s,%s) in closet" % (newDNA.botTex,
                                                                                                              newDNA.botTexColor,
                                                                                                              self.customerDNA.botTex,
                                                                                                              self.customerDNA.botTexColor))
                    if av.replaceItemInClothesBottomsList(newDNA.botTex,
                                                          newDNA.botTexColor,
                                                          self.customerDNA.botTex,
                                                          self.customerDNA.botTexColor) == 1:
                        self.notify.debug("changing shorts and putting old shorts in closet")
                        av.b_setClothesBottomsList(av.getClothesBottomsList())
                    else:
                        self.notify.warning('Closet: setDNA() - unable to save old bottoms - we exceeded the bottoms list length')

                # remove any queued deleted items now
                self.__finalizeDelete(avId)

            elif (finished == 1):
                # Purchase cancelled - make sure DNA gets reset, but don't
                # burn the clothing ticket
                if self.customerDNA:
                    av.b_setDNAString(self.customerDNA.makeNetString())
                    # empty the delete lists
                    self.deletedTops = []
                    self.deletedBottoms = []

                    # tell the client to reset it's lists..
                    # on second thought, we don't need to do this, since we
                    # are exiting the closet.  the lists will be reset automatically
                    # on re-enter
                    # self.sendUpdate("resetItemLists")
                
            else:
                # Warning - we are trusting the client to set their DNA here
                # This is a big security hole. Either the client should just send
                # indexes into the clothing choices or the tailor should verify
                #av.b_setDNAString(blob)
                # Don't set the avatars DNA.  Instead, send a message back to the
                # all the clients in this zone telling them them the dna of the localToon
                # so they can set it themselves.
                self.sendUpdate("setCustomerDNA", [avId, blob])
        else:
            self.notify.warning('no av for avId: %d' % avId)
        if (self.timedOut == 1 or finished == 0 or finished == 4):
            return
        if (self.busy == avId):
            self.notify.debug("sending complete purchase movie")
            taskMgr.remove(self.uniqueName('clearMovie'))
            self.completePurchase(avId)
        else:
            self.air.writeServerEvent('suspicious', avId, 'DistributedCloset.setDNA busy with %s' % (self.busy))
            self.notify.warning('setDNA from unknown avId: %s busy: %s' % (avId, self.busy))

    def __handleUnexpectedExit(self, avId):
        self.notify.warning('avatar:' + str(avId) + ' has exited unexpectedly')

        # Only do customer work with the busy id
        if (self.customerId == avId):
            taskMgr.remove(self.uniqueName('clearMovie'))
            toon = self.air.doId2do.get(avId)
            if (toon == None):
                toon = DistributedToonAI.DistributedToonAI(self.air)
                toon.doId = avId

            if self.customerDNA:
                toon.b_setDNAString(self.customerDNA.makeNetString())
                # Force a database write since the toon is gone and might
                # have missed the distributed update.
                #TODO 

        else:
            self.notify.warning('invalid customer avId: %s, customerId: %s ' % (avId, self.customerId))

        # Only do busy work with the busy id
        # Warning: send the clear movie at the end of this transaction because
        # it clears out all the useful values needed here
        if (self.busy == avId):
            self.sendClearMovie(None)
        else:
            self.notify.warning('not busy with avId: %s, busy: %s ' % (avId, self.busy))

    def __handleBootMessage(self, avId):
        self.notify.warning('avatar:' + str(avId) + ' got booted ')
        # Only do customer work with the busy id
        if (self.customerId == avId):
            if self.customerDNA:
                toon = self.air.doId2do.get(avId)
                if toon:
                    toon.b_setDNAString(self.customerDNA.makeNetString())
        self.sendClearMovie(None)
        
        
    def completePurchase(self, avId):
        assert(self.notify.debug('completePurchase()'))
        self.busy = avId
        # Send a movie to reward the avatar
        self.sendUpdate("setMovie", [ClosetGlobals.CLOSET_MOVIE_COMPLETE,
                        avId,
                        ClockDelta.globalClockDelta.getRealNetworkTime()])
        self.sendClearMovie(None)
        return

    def sendTimeoutMovie(self, task):
        assert(self.notify.debug('sendTimeoutMovie()'))
        # The timeout has expired.  Restore the client back to his
        # original DNA automatically (instead of waiting for the
        # client to request this).
        
        toon = self.air.doId2do.get(self.customerId)
        # On second thought, we're better off not asserting this.
        if (toon != None and self.customerDNA):
            toon.b_setDNAString(self.customerDNA.makeNetString())
            # Hmm, suppose the toon has logged out at the same time?
            # Is it possible to miss this update due to a race
            # condition?

        self.timedOut = 1
        self.sendUpdate("setMovie", [ClosetGlobals.CLOSET_MOVIE_TIMEOUT,
                                     self.busy,
                                     ClockDelta.globalClockDelta.getRealNetworkTime()])
        
        self.sendClearMovie(None)
        return Task.done


    def sendClearMovie(self, task):
        assert(self.notify.debug('sendClearMovie()'))
        # Ignore unexpected exits on whoever I was busy with
        self.ignoreAll()
        self.customerDNA = None
        self.customerId = None
        self.busy = 0
        self.timedOut = 0
        self.sendUpdate("setMovie", [ClosetGlobals.CLOSET_MOVIE_CLEAR,
                                     0,
                                     ClockDelta.globalClockDelta.getRealNetworkTime()])
        self.sendUpdate("setState", [0, 0, 0, '', [], []])
        self.sendUpdate("setCustomerDNA", [0, ''])

        #RAU kill mem leak when opening closet that's not yours
        if self.dummyToonAI:
            self.dummyToonAI.deleteDummy()
            self.dummyToonAI = None
        self.ownerAv = None
        return Task.done

    def isClosetOwner(self):
        return self.ownerId == self.customerId

    def getOwnerId(self):
        return self.ownerId

    
    if __debug__:
        def debugPrint(self, message):
            """for debugging"""
            return self.notify.debug(
                    str(self.__dict__.get('block', '?'))+' '+message)

    def __handleOwnerQuery(self, dclass, fields):
        self.topList = fields['setClothesTopsList'][0]
        self.bottomList = fields['setClothesBottomsList'][0]
        style = ToonDNA.ToonDNA()
        style.makeFromNetString(fields['setDNAString'][0])
        self.gender = style.gender

        self.d_setState(ClosetGlobals.OPEN, self.customerId, self.ownerId, self.gender, self.topList, self.bottomList)


        taskMgr.doMethodLater(ClosetGlobals.TIMEOUT_TIME, self.__handleClosetTimeout,
                              'closet-timeout-%d' % self.customerId, extraArgs=[self.customerId])