from direct.distributed import DistributedObjectAI
from . import DistributedFurnitureItemAI
from . import DistributedBankAI
from . import DistributedClosetAI
from . import DistributedPhoneAI
from . import DistributedTrunkAI
from toontown.catalog import CatalogFurnitureItem
from toontown.catalog import CatalogSurfaceItem
from toontown.catalog import CatalogWindowItem
from toontown.catalog import CatalogItem
from toontown.toonbase import ToontownGlobals
from direct.directnotify.DirectNotifyGlobal import *

class DistributedFurnitureManagerAI(DistributedObjectAI.DistributedObjectAI):

    notify = directNotify.newCategory('DistributedFurnitureManagerAI')

    def __init__(self, air, house, isInterior):
        self.house = house
        self.isInterior = isInterior
        self.director = 0
        self.dfitems = []
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)

    def delete(self):
        for dfitem in self.dfitems:
            dfitem.requestDelete()
        self.dfitems = None
        self.director = None
        
        self.notify.debug("delete()")
        self.ignoreAll()
        DistributedObjectAI.DistributedObjectAI.delete(self)

    def getOwnerId(self):
        return self.house.ownerId

    def getOwnerName(self):
        return self.house.name

    def getInteriorId(self):
        return self.house.interior.doId

    def getAtticItems(self):
        return self.house.getAtticItems()

    def d_setAtticItems(self, items):
        self.sendUpdate("setAtticItems", [items.getBlob(store = CatalogItem.Customization)])

    def d_setAtticWallpaper(self, items):
        self.sendUpdate("setAtticWallpaper", [items.getBlob(store = CatalogItem.Customization)])

    def getAtticWallpaper(self):
        return self.house.getAtticWallpaper()

    def d_setAtticWindows(self, items):
        self.sendUpdate("setAtticWindows", [items.getBlob(store = CatalogItem.Customization)])

    def getAtticWindows(self):
        return self.house.getAtticWindows()

    def getDeletedItems(self):
        deleted = self.house.reconsiderDeletedItems()
        if deleted:
            self.house.d_setDeletedItems(self.house.deletedItems)
            
        return self.house.deletedItems.getBlob(store = CatalogItem.Customization)

    def d_setDeletedItems(self, items):
        self.sendUpdate("setDeletedItems", [items.getBlob(store = CatalogItem.Customization)])

    def suggestDirector(self, avId):
        # This method is sent by the client to request the right to
        # manipulate the controls, for the requestor or for another.
        # The AI decides whether to honor the request or ignore it.

        if self.dfitems == None:
            return

        # validate the avId
        avatar = simbase.air.doId2do.get(avId)
        if (avId != 0) and (not avatar):
            # Note: avId == 0 OK since that signals end of furniture arranging
            self.air.writeServerEvent('suspicious', avId, 'FurnitureManager.suggestDirector invalid avId')
            return

        # The request is honored if the sender is the owner or is the
        # current director
        senderId = self.air.getAvatarIdFromSender()
        if senderId == self.house.ownerId or senderId == self.director:
            self.b_setDirector(avId)

    def b_setDirector(self, avId):
        self.setDirector(avId)
        self.d_setDirector(avId)

    def d_setDirector(self, avId):
        self.sendUpdate("setDirector", [avId])

    def setDirector(self, avId):
        if self.director != avId:
            # Go through the dfitems list and stop accepting
            # messages from the current director, if any.
            for dfitem in self.dfitems:
                dfitem.removeDirector()
                
            self.director = avId

    def avatarEnter(self):
        # Sent from the client when he enters furniture moving mode.
        avId = self.air.getAvatarIdFromSender()
        self.notify.debug("avatarEnter: %s, %s" % (self.doId, avId))
        avatar = simbase.air.doId2do.get(avId)
        if avatar:
            avatar.b_setGhostMode(1)
        else:
            self.notify.warning("%s got avatarEnter for unknown avatar %s" % (self.doId, avId))
            

    def avatarExit(self):
        # Sent from the client when he enters furniture moving mode.
        avId = self.air.getAvatarIdFromSender()
        self.notify.debug("avatarExit: %s, %s" % (self.doId, avId))
        avatar = simbase.air.doId2do.get(avId)
        if avatar:
            avatar.b_setGhostMode(0)
        else:
            self.notify.warning("%s got avatarEnter for unknown avatar %s" % (self.doId, avId))

    def moveItemToAtticMessage(self, doId, context):
        avId = self.air.getAvatarIdFromSender()
        retcode = self.__doMoveItemToAttic(avId, doId)
        self.sendUpdateToAvatarId(avId, "moveItemToAtticResponse",
                                  [retcode, context])

    def isHouseFull(self):
        numAtticItems = len(self.house.atticItems) + len(self.house.atticWallpaper) + len(self.house.atticWindows)
        numHouseItems = numAtticItems + len(self.house.interiorItems)
        return numHouseItems >= ToontownGlobals.MaxHouseItems

    def __doMoveItemToAttic(self, avId, doId):
        # A request by the client to move the indicated
        # DistributedFurnitureItem into the attic.
        if avId != self.director:
            self.notify.warning("Ignoring request from non-director %s." % (avId))
            return ToontownGlobals.FM_NotDirector

        dfitem = simbase.air.doId2do.get(doId)
        if dfitem == None or dfitem not in self.dfitems:
            self.notify.warning("Ignoring request for unknown dfitem %s." % (doId))
            return ToontownGlobals.FM_InvalidIndex

        item = dfitem.item
        self.house.atticItems.append(item)

        # Find the item in self.house.interiorItems.  We have to check for
        # exact equivalence.
        for i in range(len(self.house.interiorItems)):
            if self.house.interiorItems[i] is item:
                del self.house.interiorItems[i]
                break

        # Also remove it from self.dfitems.
        self.dfitems.remove(dfitem)
        item.dfitem = None

        self.house.d_setAtticItems(self.house.atticItems)
        self.house.d_setInteriorItems(self.house.interiorItems)
        dfitem.requestDelete()

        # Tell the client our new list of attic items.
        self.d_setAtticItems(self.house.atticItems)
        return ToontownGlobals.FM_MovedItem
        

    def moveItemFromAtticMessage(self, index, x, y, z, h, p, r, context):
        # A request by the client to move the indicated
        # item out of the attic and to the given position.
        avId = self.air.getAvatarIdFromSender()
        retcode, objectId = self.__doMoveItemFromAttic(avId, index, (x, y, z, h, p, r))
        self.sendUpdateToAvatarId(avId, "moveItemFromAtticResponse", [retcode, objectId, context])        

    def __doMoveItemFromAttic(self, avId, index, posHpr):
        if avId != self.director:
            self.notify.warning("Ignoring request from non-director %s." % (avId))
            return (ToontownGlobals.FM_NotDirector, 0)

        if index < 0 or index >= len(self.house.atticItems):
            self.notify.warning("Ignoring request for invalid index %s." % (index))
            return (ToontownGlobals.FM_InvalidIndex, 0)

        item = self.house.atticItems[index]
        del self.house.atticItems[index]
        item.posHpr = posHpr
        self.house.interiorItems.append(item)
        self.house.d_setInteriorItems(self.house.interiorItems)
        self.house.d_setAtticItems(self.house.atticItems)
        dfitem = self.manifestInteriorItem(item)
        if not dfitem:
            return (ToontownGlobals.FM_InvalidItem, 0)

        self.d_setAtticItems(self.house.atticItems)
        return (ToontownGlobals.FM_MovedItem, dfitem.doId)

    def deleteItemFromAtticMessage(self, blob, index, context):
        # A request by the client to delete the indicated
        # item from the attic altogether.
        avId = self.air.getAvatarIdFromSender()
        item = CatalogItem.getItem(blob, store = CatalogItem.Customization)
        retcode = self.__doDeleteItemFromAttic(avId, item, index)
        self.sendUpdateToAvatarId(avId, "deleteItemFromAtticResponse", [retcode, context])        

    def __doDeleteItemFromAttic(self, avId, item, index):
        if avId != self.director:
            self.notify.warning("Ignoring request from non-director %s." % (avId))
            return ToontownGlobals.FM_NotDirector

        # You must be the owner in order to delete objects.
        if avId != self.house.ownerId:
            self.notify.warning("Ignoring request to delete from non-owner %s." % (avId))
            return ToontownGlobals.FM_NotOwner

        if index < 0 or index >= len(self.house.atticItems):
            self.notify.warning("Ignoring request for invalid index %s." % (index))
            return ToontownGlobals.FM_InvalidIndex

        if self.house.atticItems[index] != item:
            self.notify.warning("Request to delete item %s does not match %s." % (index, item))
            return ToontownGlobals.FM_InvalidIndex

        if not item.isDeletable():
            self.notify.warning("Ignoring request to delete special item %s." % (item))
            return ToontownGlobals.FM_NondeletableItem

        # Not really necessary, but there may be some subtle differences.
        item = self.house.atticItems[index]

        self.house.addToDeleted(item)

        del self.house.atticItems[index]
        self.house.d_setAtticItems(self.house.atticItems)
        self.d_setAtticItems(self.house.atticItems)
        self.d_setDeletedItems(self.house.deletedItems)
        return ToontownGlobals.FM_DeletedItem
        

    def deleteItemFromRoomMessage(self, blob, doId, context):
        # A request by the client to delete the indicated
        # item directly from the room.
        avId = self.air.getAvatarIdFromSender()
        item = CatalogItem.getItem(blob, store = CatalogItem.Customization)
        retcode = self.__doDeleteItemFromRoom(avId, item, doId)
        self.sendUpdateToAvatarId(avId, "deleteItemFromRoomResponse", [retcode, context])        
        
    def __doDeleteItemFromRoom(self, avId, item, doId):
        if avId != self.director:
            self.notify.warning("Ignoring request from non-director %s." % (avId))
            return ToontownGlobals.FM_NotDirector

        # You must be the owner in order to delete objects.
        if avId != self.house.ownerId:
            self.notify.warning("Ignoring request to delete from non-owner %s." % (avId))
            return ToontownGlobals.FM_NotOwner

        dfitem = simbase.air.doId2do.get(doId)
        if dfitem == None or dfitem not in self.dfitems:
            self.notify.warning("Ignoring request for unknown dfitem %s." % (doId))
            return ToontownGlobals.FM_InvalidIndex

        if dfitem.item != item:
            self.notify.warning("Request to delete item %s does not match %s." % (doId, item))
            return ToontownGlobals.FM_InvalidIndex

        if not item.isDeletable():
            self.notify.warning("Ignoring request to delete special item %s." % (item))
            return ToontownGlobals.FM_NondeletableItem

        item = dfitem.item
        # Find the item in self.house.interiorItems.  We have to check for
        # exact equivalence.
        for i in range(len(self.house.interiorItems)):
            if self.house.interiorItems[i] is item:
                del self.house.interiorItems[i]
                break

        # Also remove it from self.dfitems.
        self.dfitems.remove(dfitem)
        item.dfitem = None

        self.house.addToDeleted(item)
        self.house.d_setInteriorItems(self.house.interiorItems)
        dfitem.requestDelete()

        # Tell the client our new list of deleted items.
        self.d_setDeletedItems(self.house.deletedItems)
        return ToontownGlobals.FM_DeletedItem


    def moveWallpaperFromAtticMessage(self, index, room, context):
        # A request by the client to swap the given wallpaper from the
        # attic with the interior wallpaper for the indicated room.
        avId = self.air.getAvatarIdFromSender()
        retcode = self.__doMoveWallpaperFromAttic(avId, index, room)
        self.sendUpdateToAvatarId(avId, "moveWallpaperFromAtticResponse", [retcode, context])        

    def __doMoveWallpaperFromAttic(self, avId, index, room):
        if avId != self.director:
            self.notify.warning("Ignoring request from non-director %s." % (avId))
            return ToontownGlobals.FM_NotDirector

        if index < 0 or index >= len(self.house.atticWallpaper):
            self.notify.warning("Ignoring request for invalid index %s." % (index))
            return ToontownGlobals.FM_InvalidIndex

        item = self.house.atticWallpaper[index]
        surface = item.getSurfaceType()
        slot = room * CatalogSurfaceItem.NUM_ST_TYPES + surface

        if slot < 0 or slot >= len(self.house.interiorWallpaper):
            self.notify.warning("Ignoring request for invalid wallpaper room %s, surface %s." % (room, surface))
            return ToontownGlobals.FM_InvalidIndex

        repl = self.house.interiorWallpaper[slot]

        self.house.interiorWallpaper[slot] = item
        self.house.atticWallpaper[index] = repl
        self.house.d_setAtticWallpaper(self.house.atticWallpaper)
        self.house.d_setInteriorWallpaper(self.house.interiorWallpaper)
        return ToontownGlobals.FM_SwappedItem

    def deleteWallpaperFromAtticMessage(self, blob, index, context):
        # A request by the client to delete the indicated
        # wallpaper from the attic altogether.
        avId = self.air.getAvatarIdFromSender()
        item = CatalogItem.getItem(blob, store = CatalogItem.Customization)
        retcode = self.__doDeleteWallpaperFromAttic(avId, item, index)
        self.sendUpdateToAvatarId(avId, "deleteWallpaperFromAtticResponse", [retcode, context])        

    def __doDeleteWallpaperFromAttic(self, avId, item, index):
        if avId != self.director:
            self.notify.warning("Ignoring request from non-director %s." % (avId))
            return ToontownGlobals.FM_NotDirector

        # You must be the owner in order to delete objects.
        if avId != self.house.ownerId:
            self.notify.warning("Ignoring request to delete from non-owner %s." % (avId))
            return ToontownGlobals.FM_NotOwner

        if index < 0 or index >= len(self.house.atticWallpaper):
            self.notify.warning("Ignoring request for invalid index %s." % (index))
            return ToontownGlobals.FM_InvalidIndex

        if self.house.atticWallpaper[index] != item:
            self.notify.warning("Request to delete wallpaper %s does not match %s." % (index, item))
            return ToontownGlobals.FM_InvalidIndex

        # Not really necessary, but there may be some subtle differences.
        item = self.house.atticWallpaper[index]

        self.house.addToDeleted(item)

        del self.house.atticWallpaper[index]
        self.house.d_setAtticWallpaper(self.house.atticWallpaper)
        self.d_setAtticWallpaper(self.house.atticWallpaper)
        self.d_setDeletedItems(self.house.deletedItems)
        return ToontownGlobals.FM_DeletedItem

    def moveWindowToAtticMessage(self, slot, context):
        # A request by the client to move the interior window
        # occupying the indicated placement slot into the attic.
        avId = self.air.getAvatarIdFromSender()
        retcode = self.__doMoveWindowToAttic(avId, slot)
        self.sendUpdateToAvatarId(avId, "moveWindowToAtticResponse", [retcode, context])
    def __doMoveWindowToAttic(self, avId, slot):
        if avId != self.director:
            self.notify.warning("Ignoring request from non-director %s." % (avId))
            return ToontownGlobals.FM_NotDirector

        index = self.__findWindow(slot)
        if index == None:
            self.notify.warning("Ignoring request for invalid placement slot %s." % (slot))
            return ToontownGlobals.FM_InvalidIndex

        if self.isHouseFull():
            return ToontownGlobals.FM_HouseFull

        self.house.makeRoomFor(1)

        self.house.atticWindows.append(self.house.interiorWindows[index])
        del self.house.interiorWindows[index]
            
        self.house.d_setAtticWindows(self.house.atticWindows)
        self.house.d_setInteriorWindows(self.house.interiorWindows)
        return ToontownGlobals.FM_MovedItem

    def moveWindowFromAtticMessage(self, index, slot, context):
        # A request by the client to swap the given window from the
        # attic with the interior window at the indicated slot.
        avId = self.air.getAvatarIdFromSender()
        retcode = self.__doMoveWindowFromAttic(avId, index, slot)
        self.sendUpdateToAvatarId(avId, "moveWindowFromAtticResponse", [retcode, context])
        

    def __doMoveWindowFromAttic(self, avId, index, slot):
        if avId != self.director:
            self.notify.warning("Ignoring request from non-director %s." % (avId))
            return ToontownGlobals.FM_NotDirector

        if index < 0 or index >= len(self.house.atticWindows):
            self.notify.warning("Ignoring request for invalid index %s." % (index))
            return ToontownGlobals.FM_InvalidIndex

        item = self.house.atticWindows[index]
        item.placement = slot

        # Is there already a window placed at the indicated slot?
        windowIndex = self.__findWindow(slot)
        
        if windowIndex == None:
            # Create a new window.
            self.house.interiorWindows.append(item)
            del self.house.atticWindows[index]
            retcode = ToontownGlobals.FM_MovedItem

        else:
            # We have a window already; it moves into the attic.
            self.house.atticWindows[index] = self.house.interiorWindows[windowIndex]
            self.house.interiorWindows[windowIndex] = item
            retcode = ToontownGlobals.FM_SwappedItem
            
        self.house.d_setAtticWindows(self.house.atticWindows)
        self.house.d_setInteriorWindows(self.house.interiorWindows)
        return retcode

    def moveWindowMessage(self, fromSlot, toSlot, context):
        # A request by the client to move the interior window
        # occupying the indicated placement slot to another location
        # within the interior.
        
        avId = self.air.getAvatarIdFromSender()
        retcode = self.__doMoveWindow(avId, fromSlot, toSlot)
        self.sendUpdateToAvatarId(avId, "moveWindowResponse", [retcode, context])
    def __doMoveWindow(self, avId, fromSlot, toSlot):
        if avId != self.director:
            self.notify.warning("Ignoring request from non-director %s." % (avId))
            return ToontownGlobals.FM_NotDirector

        fromIndex = self.__findWindow(fromSlot)
        if fromIndex == None:
            self.notify.warning("Ignoring request for invalid placement slot %s." % (fromSlot))
            return ToontownGlobals.FM_InvalidIndex

        item = self.house.interiorWindows[fromIndex]

        # Is there already a window placed at the destination slot?
        toIndex = self.__findWindow(toSlot)
        
        if toIndex == None:
            # Nope, just move the window.
            item.placement = toSlot

            # This is necessary because we have changed an element
            # without changing any other properties of the list, so we
            # have to explicitly tell the list to update its cache.
            self.house.interiorWindows.markDirty()
            
            retcode = ToontownGlobals.FM_MovedItem

        else:
            # We have a window there already; it moves into the attic.
            if self.isHouseFull():
                return ToontownGlobals.FM_HouseFull

            self.house.makeRoomFor(1)

            item.placement = toSlot
            self.house.atticWindows.append(self.house.interiorWindows[toIndex])
            del self.house.interiorWindows[toIndex]
            retcode = ToontownGlobals.FM_SwappedItem
            
            self.house.d_setAtticWindows(self.house.atticWindows)
            
        self.house.d_setInteriorWindows(self.house.interiorWindows)
        return retcode

    def __findWindow(self, placement):
        # Searches for the window with the indicated slot placement
        # and returns its index within the self.house.interiorWindows
        # list if it is found, or None if there is no such window.
        windows = self.house.interiorWindows
        for i in range(len(windows)):
            if windows[i].placement == placement:
                return i
        return None

    def deleteWindowFromAtticMessage(self, blob, index, context):
        # A request by the client to delete the indicated
        # window from the attic altogether.
        avId = self.air.getAvatarIdFromSender()
        item = CatalogItem.getItem(blob, store = CatalogItem.Customization)
        retcode = self.__doDeleteWindowFromAttic(avId, item, index)
        self.sendUpdateToAvatarId(avId, "deleteWindowFromAtticResponse", [retcode, context])        

    def __doDeleteWindowFromAttic(self, avId, item, index):
        if avId != self.director:
            self.notify.warning("Ignoring request from non-director %s." % (avId))
            return ToontownGlobals.FM_NotDirector

        # You must be the owner in order to delete objects.
        if avId != self.house.ownerId:
            self.notify.warning("Ignoring request to delete from non-owner %s." % (avId))
            return ToontownGlobals.FM_NotOwner

        if index < 0 or index >= len(self.house.atticWindows):
            self.notify.warning("Ignoring request for invalid index %s." % (index))
            return ToontownGlobals.FM_InvalidIndex

        if self.house.atticWindows[index] != item:
            self.notify.warning("Request to delete window %s does not match %s." % (index, item))
            return ToontownGlobals.FM_InvalidIndex

        # Not really necessary, but there may be some subtle differences.
        item = self.house.atticWindows[index]

        self.house.addToDeleted(item)

        del self.house.atticWindows[index]
        self.house.d_setAtticWindows(self.house.atticWindows)
        self.d_setAtticWindows(self.house.atticWindows)
        self.d_setDeletedItems(self.house.deletedItems)
        return ToontownGlobals.FM_DeletedItem

    def recoverDeletedItemMessage(self, blob, index, context):
        # A request by the client to recover the indicated item from
        # the deleted-item list.
        avId = self.air.getAvatarIdFromSender()
        item = CatalogItem.getItem(blob, store = CatalogItem.Customization)
        retcode = self.__doRecoverDeletedItem(avId, item, index)
        self.sendUpdateToAvatarId(avId, "recoverDeletedItemResponse", [retcode, context])        

    def __doRecoverDeletedItem(self, avId, item, index):
        if avId != self.director:
            self.notify.warning("Ignoring request from non-director %s." % (avId))
            return ToontownGlobals.FM_NotDirector

        # You must be the owner in order to delete (or recover) objects.
        if avId != self.house.ownerId:
            self.notify.warning("Ignoring request to recover from non-owner %s." % (avId))
            return ToontownGlobals.FM_NotOwner

        if index < 0 or index >= len(self.house.deletedItems):
            self.notify.warning("Ignoring request for invalid index %s." % (index))
            return ToontownGlobals.FM_InvalidIndex

        if self.house.deletedItems[index] != item:
            self.notify.warning("Request to recover item %s does not match %s." % (index, item))
            return ToontownGlobals.FM_InvalidIndex

        if self.isHouseFull():
            return ToontownGlobals.FM_HouseFull

        # Not really necessary, but there may be some subtle differences.
        item = self.house.deletedItems[index]

        if isinstance(item, CatalogFurnitureItem.CatalogFurnitureItem):
            self.house.atticItems.append(item)
            self.house.d_setAtticItems(self.house.atticItems)
            self.d_setAtticItems(self.house.atticItems)

        elif isinstance(item, CatalogSurfaceItem.CatalogSurfaceItem):
            self.house.atticWallpaper.append(item)
            self.house.d_setAtticWallpaper(self.house.atticWallpaper)
            self.d_setAtticWallpaper(self.house.atticWallpaper)

        elif item.__class__ == CatalogWindowItem.CatalogWindowItem:
            self.house.atticWindows.append(item)
            self.house.d_setAtticWindows(self.house.atticWindows)
            self.d_setAtticWindows(self.house.atticWindows)

        else:
            self.notify.warning("Ignoring request to recover invalid item type %s." % (item.__class__.__name__))
            return ToontownGlobals.FM_InvalidIndex

        del self.house.deletedItems[index]
        self.house.d_setDeletedItems(self.house.deletedItems)
        self.d_setDeletedItems(self.house.deletedItems)

        return ToontownGlobals.FM_RecoveredItem


    def saveItemPosition(self, dfitem):
        # Saves the position of the DistributedFurnitureItem in the
        # interior.
        assert(dfitem in self.dfitems)
        dfitem.item.posHpr = dfitem.posHpr
        self.house.interiorItems.markDirty()
        self.house.d_setInteriorItems(self.house.interiorItems)

    def requestControl(self, dfitem, directorAvId):
        # Returns true if the indicated director is allowed to move
        # the item, false otherwise.
        if self.dfitems == None or dfitem not in self.dfitems:
            return 0
        return directorAvId == self.director
        
    def manifestInteriorItem(self, item):
        # Creates and returns a DistributedFurnitureItem for the
        # indicated furniture item.

        if not hasattr(item, "getFlags"):
            self.notify.warning("Ignoring attempt to manifest %s as a furniture item." % (item))
            return None

        # Choose the appropriate kind of object to create.  Usually it
        # is just a DistributedFurnitureItemAI, but sometimes we have
        # to be more specific.
        if item.getFlags() & CatalogFurnitureItem.FLBank:
            cl = DistributedBankAI.DistributedBankAI
        elif item.getFlags() & CatalogFurnitureItem.FLCloset:
            cl = DistributedClosetAI.DistributedClosetAI
        elif item.getFlags() & CatalogFurnitureItem.FLPhone:
            cl = DistributedPhoneAI.DistributedPhoneAI
        elif item.getFlags() & CatalogFurnitureItem.FLTrunk:
            cl = DistributedTrunkAI.DistributedTrunkAI
        else:
            cl = DistributedFurnitureItemAI.DistributedFurnitureItemAI
        
        dfitem = cl(self.air, self, item)
        dfitem.generateWithRequired(self.house.interiorZoneId)
        item.dfitem = dfitem
        self.dfitems.append(dfitem)

        # Send the initial position.
        dfitem.d_setPosHpr(*item.posHpr)
        return dfitem
