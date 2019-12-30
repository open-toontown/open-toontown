from direct.distributed import DistributedObject
from toontown.catalog import CatalogItem
from toontown.catalog import CatalogItemList
from direct.directnotify.DirectNotifyGlobal import *

class DistributedFurnitureManager(DistributedObject.DistributedObject):
    notify = directNotify.newCategory('DistributedFurnitureManager')

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        self.director = 0
        self.dfitems = []

    def generate(self):
        DistributedObject.DistributedObject.generate(self)
        self.accept('releaseDirector', self.releaseDirector)

    def disable(self):
        self.ignoreAll()
        if self.cr.furnitureManager == self:
            self.cr.furnitureManager = None
        base.localAvatar.setFurnitureDirector(0, self)
        self.director = 0
        self.notify.debug('disable')
        DistributedObject.DistributedObject.disable(self)
        return

    def delete(self):
        self.notify.debug('delete')
        DistributedObject.DistributedObject.delete(self)

    def setOwnerId(self, ownerId):
        self.ownerId = ownerId
        if self.ownerId == base.localAvatar.doId:
            self.cr.furnitureManager = self
            if self.cr.objectManager == None:
                from . import houseDesign
                self.cr.objectManager = houseDesign.ObjectManager()
        return

    def setOwnerName(self, name):
        self.ownerName = name

    def setInteriorId(self, interiorId):
        self.interiorId = interiorId

    def getInteriorObject(self):
        return self.cr.doId2do.get(self.interiorId)

    def setAtticItems(self, items):
        self.atticItems = CatalogItemList.CatalogItemList(items, store=CatalogItem.Customization)

    def setAtticWallpaper(self, items):
        self.atticWallpaper = CatalogItemList.CatalogItemList(items, store=CatalogItem.Customization)

    def setAtticWindows(self, items):
        self.atticWindows = CatalogItemList.CatalogItemList(items, store=CatalogItem.Customization)

    def setDeletedItems(self, items):
        self.deletedItems = CatalogItemList.CatalogItemList(items, store=CatalogItem.Customization)

    def releaseDirector(self):
        if self.director == base.localAvatar.doId:
            self.d_suggestDirector(0)
            self.setDirector(0)

    def d_suggestDirector(self, avId):
        self.sendUpdate('suggestDirector', [avId])

    def setDirector(self, avId):
        self.notify.info('Furniture director is now %s' % avId)
        base.localAvatar.setFurnitureDirector(avId, self)
        self.director = avId

    def d_avatarEnter(self):
        self.sendUpdate('avatarEnter', [])

    def d_avatarExit(self):
        self.sendUpdate('avatarExit', [])

    def moveItemToAttic(self, dfitem, callback):
        context = self.getCallbackContext(callback, [dfitem.item])
        self.sendUpdate('moveItemToAtticMessage', [dfitem.doId, context])

    def moveItemFromAttic(self, index, posHpr, callback):
        context = self.getCallbackContext(callback, [index])
        self.sendUpdate('moveItemFromAtticMessage', [index,
         posHpr[0],
         posHpr[1],
         posHpr[2],
         posHpr[3],
         posHpr[4],
         posHpr[5],
         context])

    def deleteItemFromAttic(self, item, index, callback):
        context = self.getCallbackContext(callback, [item, index])
        blob = item.getBlob(store=CatalogItem.Customization)
        self.sendUpdate('deleteItemFromAtticMessage', [blob, index, context])

    def deleteItemFromRoom(self, dfitem, callback):
        context = self.getCallbackContext(callback, [dfitem.item])
        blob = dfitem.item.getBlob(store=CatalogItem.Customization)
        self.sendUpdate('deleteItemFromRoomMessage', [blob, dfitem.doId, context])

    def moveWallpaperFromAttic(self, index, room, callback):
        context = self.getCallbackContext(callback, [index, room])
        self.sendUpdate('moveWallpaperFromAtticMessage', [index, room, context])

    def deleteWallpaperFromAttic(self, item, index, callback):
        context = self.getCallbackContext(callback, [item, index])
        blob = item.getBlob(store=CatalogItem.Customization)
        self.sendUpdate('deleteWallpaperFromAtticMessage', [blob, index, context])

    def moveWindowToAttic(self, slot, callback):
        context = self.getCallbackContext(callback, [slot])
        self.sendUpdate('moveWindowToAtticMessage', [slot, context])

    def moveWindowFromAttic(self, index, slot, callback):
        context = self.getCallbackContext(callback, [index, slot])
        self.sendUpdate('moveWindowFromAtticMessage', [index, slot, context])

    def moveWindow(self, fromSlot, toSlot, callback):
        context = self.getCallbackContext(callback, [fromSlot, toSlot])
        self.sendUpdate('moveWindowMessage', [fromSlot, toSlot, context])

    def deleteWindowFromAttic(self, item, index, callback):
        context = self.getCallbackContext(callback, [item, index])
        blob = item.getBlob(store=CatalogItem.Customization)
        self.sendUpdate('deleteWindowFromAtticMessage', [blob, index, context])

    def recoverDeletedItem(self, item, index, callback):
        context = self.getCallbackContext(callback, [item, index])
        blob = item.getBlob(store=CatalogItem.Customization)
        self.sendUpdate('recoverDeletedItemMessage', [blob, index, context])

    def moveItemToAtticResponse(self, retcode, context):
        self.doCallbackContext(context, [retcode])

    def moveItemFromAtticResponse(self, retcode, objectId, context):
        if retcode >= 0:
            dfitem = base.cr.doId2do[objectId]
        else:
            dfitem = None
        self.doCallbackContext(context, [retcode, dfitem])
        return

    def deleteItemFromAtticResponse(self, retcode, context):
        self.doCallbackContext(context, [retcode])

    def deleteItemFromRoomResponse(self, retcode, context):
        self.doCallbackContext(context, [retcode])

    def moveWallpaperFromAtticResponse(self, retcode, context):
        self.doCallbackContext(context, [retcode])

    def deleteWallpaperFromAtticResponse(self, retcode, context):
        self.doCallbackContext(context, [retcode])

    def moveWindowToAtticResponse(self, retcode, context):
        self.doCallbackContext(context, [retcode])

    def moveWindowFromAtticResponse(self, retcode, context):
        self.doCallbackContext(context, [retcode])

    def moveWindowResponse(self, retcode, context):
        self.doCallbackContext(context, [retcode])

    def deleteWindowFromAtticResponse(self, retcode, context):
        self.doCallbackContext(context, [retcode])

    def recoverDeletedItemResponse(self, retcode, context):
        self.doCallbackContext(context, [retcode])
