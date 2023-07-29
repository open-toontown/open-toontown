from . import DistributedFurnitureItemAI
from . import PhoneGlobals
from toontown.catalog import CatalogItem
from toontown.toonbase import ToontownGlobals
from toontown.ai import DatabaseObject
from toontown.catalog import CatalogItemList
from direct.distributed import ClockDelta
from direct.directnotify.DirectNotifyGlobal import *
from pandac.PandaModules import *
from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator

class DistributedPhoneAI(DistributedFurnitureItemAI.DistributedFurnitureItemAI):

    notify = directNotify.newCategory('DistributedPhoneAI')

    defaultScale = 0.75

    def __init__(self, air, furnitureMgr, item):
        DistributedFurnitureItemAI.DistributedFurnitureItemAI.__init__(
            self, air, furnitureMgr, item)
        self.av = None
        self.busy = 0

        # Figure out the initial scale of the phone.  If the owner is
        # around, it will be scaled to match the owner; otherwise, it
        # will just be a default scale.
        scale = self.defaultScale
        ownerId = self.furnitureMgr.house.ownerId
        owner = self.air.doId2do.get(ownerId)
        if owner:
            animalStyle = owner.dna.getAnimal()
            scale = ToontownGlobals.toonBodyScales[animalStyle]

        self.initialScale = (scale, scale, scale)
        

    def getInitialScale(self):
        return self.initialScale

    def delete(self):
        self.notify.debug("delete()")
        self.ignoreAll()
        DistributedFurnitureItemAI.DistributedFurnitureItemAI.delete(self)

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
            self.air.writeServerEvent('suspicious', avId, 'DistributedPhoneAI.avatarEnter unknown')
            self.notify.warning("av %s not in doId2do tried to pick up phone" % (avId))
            return

        # Flag us as busy with this avatar Id
        self.busy = avId
        self.av = av

        # Handle unexpected exit
        self.acceptOnce(self.air.getAvatarExitEvent(avId),
                        self.__handleUnexpectedExit, extraArgs=[avId])
        self.acceptOnce("bootAvFromEstate-"+str(avId),
                        self.__handleBootMessage, extraArgs=[avId])

        # Update the quest manager. Yes, there are phone quests.
        self.air.questManager.toonUsedPhone(self.av)

        # We don't care who the owner of the phone is--anyone can use
        # any phone.
        if len(av.weeklyCatalog) + len(av.monthlyCatalog) + len(av.backCatalog) != 0:
            self.lookupHouse()
            
        else:
            # No catalog yet.
            self.d_setMovie(PhoneGlobals.PHONE_MOVIE_EMPTY, avId)
            self.sendClearMovie()

    def setNewScale(self, sx, sy, sz):
        # A client, presumably the avatar at the phone, is telling us
        # what scale the phone will be if anyone asks.
        avId = self.air.getAvatarIdFromSender()

        # Sanity check the parameters; ignore requests from unexpected
        # clients or unreasonable scales.
        if self.busy == avId:
            if (sx >= 0.25 or sy >= 0.25 or sz >= 0.25):
                # If it passes, store it.
                self.initialScale = (sx, sy, sz)
                self.sendUpdate("setInitialScale", [sx, sy, sz])

    def lookupHouse(self):
        # Looks up the avatar's house information so we can figure out
        # how much stuff is in the attic.  We need to tell this
        # information to the client so it can warn the user if he's in
        # danger of overfilling it.

        if not self.av.houseId:
            self.notify.warning("Avatar %s has no houseId." % (self.av.doId))
            self.sendCatalog(0)
            return

        # Maybe the house is already instantiated.  This will be true
        # when the avatar is calling from his own house, for instance.
        house = self.air.doId2do.get(self.av.houseId)
        if house:
            assert(self.notify.debug("House %s is already instantiated." % (self.av.houseId)))
            numAtticItems = len(house.atticItems) + len(house.atticWallpaper) + len(house.atticWindows)
            numHouseItems = numAtticItems + len(house.interiorItems)
            self.sendCatalog(numHouseItems)
            return

        # All right, we have to query the database to get the attic
        # information.  What a nuisance.
        assert(self.notify.debug("Querying database for house %s." % (self.av.houseId)))

        gotHouseEvent = self.uniqueName("gotHouse")
        self.acceptOnce(gotHouseEvent, self.__gotHouse)

        db = DatabaseObject.DatabaseObject(self.air, self.av.houseId)
        db.doneEvent = gotHouseEvent

        db.getFields(['setAtticItems', 'setAtticWallpaper',
                      'setAtticWindows', 'setInteriorItems'])
                                 
    def __gotHouse(self, db, retcode):
        assert(self.notify.debug("__gotHouse(%s, %s): %s" % (list(db.values.keys()), retcode, self.doId)))
        if retcode != 0:
            self.notify.warning("House %s for avatar %s does not exist!" % (self.av.houseId, self.av.doId))
            self.sendCatalog(0)
            return

        atticItems = []
        atticWallpaper = []
        atticWindows = []
        interiorItems = []

        dg = db.values.get('setAtticItems')
        if dg:
            di = PyDatagramIterator(dg)
            blob = di.getString()
            atticItems = CatalogItemList.CatalogItemList(blob, store = CatalogItem.Customization)
        dg = db.values.get('setAtticWallpaper')
        if dg:
            di = PyDatagramIterator(dg)
            blob = di.getString()
            atticWallpaper = CatalogItemList.CatalogItemList(blob, store = CatalogItem.Customization)
        dg = db.values.get('setAtticWindows')
        if dg:
            di = PyDatagramIterator(dg)
            blob = di.getString()
            atticWindows = CatalogItemList.CatalogItemList(blob, store = CatalogItem.Customization)
        dg = db.values.get('setInteriorItems')
        if dg:
            di = PyDatagramIterator(dg)
            blob = di.getString()
            interiorItems = CatalogItemList.CatalogItemList(blob, store = CatalogItem.Location | CatalogItem.Customization)

        # Finally we're ready to tell the user what he needs to know.
        numAtticItems = len(atticItems) + len(atticWallpaper) + len(atticWindows)
        numHouseItems = numAtticItems + len(interiorItems)
        self.sendCatalog(numHouseItems)
            

    def sendCatalog(self, numHouseItems):
        # Send the setMovie command to the user to tell him to open up
        # his catalog.  But first, tell him how much stuff he's got in
        # his house.
        self.sendUpdateToAvatarId(self.av.doId, "setLimits", [numHouseItems])

        # Now open the catalog up on the client.
        self.d_setMovie(PhoneGlobals.PHONE_MOVIE_PICKUP, self.av.doId)
        
        # The avatar has seen his catalog now.
        if self.av.catalogNotify == ToontownGlobals.NewItems:
            self.av.b_setCatalogNotify(ToontownGlobals.OldItems, self.av.mailboxNotify)


    def avatarExit(self):
        self.notify.debug("avatarExit")
        avId = self.air.getAvatarIdFromSender()

        if self.busy == avId:
            self.d_setMovie(PhoneGlobals.PHONE_MOVIE_HANGUP, self.av.doId)
            self.sendClearMovie()
        else:
            self.freeAvatar(avId)

    def __handleUnexpectedExit(self, avId):
        self.notify.warning('avatar:' + str(avId) + ' has exited unexpectedly')
        self.sendClearMovie()

    def __handleBootMessage(self, avId):
        self.notify.warning('avatar:' + str(avId) + ' got booted ')
        self.sendClearMovie()
        
    def sendClearMovie(self):
        assert(self.notify.debug('sendClearMovie()'))
        # Ignore unexpected exits on whoever I was busy with
        self.ignoreAll()
        self.busy = 0
        self.av = None
        self.d_setMovie(PhoneGlobals.PHONE_MOVIE_CLEAR, 0)

    def requestPurchaseMessage(self, context, blob, optional):
        # Sent from the client code to request a particular purchase item.
        avId = self.air.getAvatarIdFromSender()
        item = CatalogItem.getItem(blob, store = CatalogItem.Customization)
        if self.busy != avId:
            self.air.writeServerEvent('suspicious', avId, 'DistributedPhoneAI.requestPurchaseMessage busy with %s' % (self.busy))
            self.notify.warning("Got unexpected purchase request from %s while busy with %s." % (avId, self.busy))
            retcode = ToontownGlobals.P_NotShopping
        else:
            # The user is requesting purchase of one particular item.
            retcode = self.air.catalogManager.purchaseItem(self.av, item, optional)
            
        self.sendUpdateToAvatarId(avId, "requestPurchaseResponse", [context, retcode])
        
    def requestGiftPurchaseMessage(self, context, targetDoID, blob, optional):
        # print "in the AI phone"
        # Sent from the client code to request a particular purchase item. to be sent to a target doid
        sAvId = self.air.getAvatarIdFromSender()
        item = CatalogItem.getItem(blob, store = CatalogItem.Customization)
        retcode = None
        if self.busy != sAvId:
            self.air.writeServerEvent('suspicious', sAvId, 'DistributedPhoneAI.requestPurchaseMessage busy with %s' % (self.busy))
            self.notify.warning("Got unexpected purchase request from %s while busy with %s." % (sAvId, self.busy))
            retcode = ToontownGlobals.P_NotShopping
            #in this case we can send the response immediately
            self.sendUpdateToAvatarId(sAvId, "requestGiftPurchaseResponse", [context, retcode])
            
        elif self.air.catalogManager.payForGiftItem(self.av, item, retcode):
            # The user is requesting purchase of one particular item.in this case we have to wait for the purchase to go through
            # which involves waiting for a query from the database: intancing the gift receiver on the local machine
            
            self.checkAvatarThenGift(targetDoID, sAvId, item, context)
            #simbase.air.deliveryManager.sendRequestPurchaseGift(item, targetDoID, sAvId, context, self)
            
            #can't return immediately must what for the query to go through
        else:
            retcode = ToontownGlobals.P_NotEnoughMoney
            self.sendUpdateToAvatarId(sAvId, "requestGiftPurchaseResponse", [context, retcode])
            
    def checkAvatarThenGift(self, targetDoID, sAvId, item, context):
        # Requests a particular avatar.  The avatar will be requested
        # from the database and stored in self.rav when the response is
        # heard back from the database, at some time in the future.
        #self.rAv = None
        checkMessage = "gift check %s" % (targetDoID)

        self.acceptOnce(("gift check %s" % (targetDoID)), self.__gotAvGiftCheck, [targetDoID, sAvId, item, context])
       

        db = DatabaseObject.DatabaseObject(self.air, targetDoID)
        db.doneEvent = checkMessage
        fields = ['setDNAString']
        
        db.getFields(fields)
        
    def __gotAvGiftCheck(self, targetDoID, sAvId, item, context, db, data2):
        valid = 'setDNAString' in db.values
        if valid:
            simbase.air.deliveryManager.sendRequestPurchaseGift(item, targetDoID, sAvId, context, self)
        else:
            self.air.writeServerEvent('suspicious', sAvId, 'Attempted to buy a gift for %s which is not a toon' % (targetDoID))
            
        

    def d_setMovie(self, mode, avId):
        timestamp = ClockDelta.globalClockDelta.getRealNetworkTime(bits = 32)
        self.sendUpdate("setMovie", [mode, avId, timestamp])
