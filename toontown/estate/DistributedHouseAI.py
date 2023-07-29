from otp.ai.AIBase import *
from direct.distributed.ClockDelta import *
from pandac.PandaModules import *
from toontown.ai.ToontownAIMsgTypes import *
from direct.distributed import DistributedObjectAI
from . import DistributedHouseAI
# import DistributedGardenAI

from . import DistributedCannonAI
from . import DistributedHouseInteriorAI
from . import DistributedHouseDoorAI
from . import DistributedMailboxAI
from . import DistributedFurnitureManagerAI
from toontown.toon import DistributedToonAI
from toontown.catalog import CatalogItemList
from toontown.catalog import CatalogItem
from toontown.catalog import CatalogFurnitureItem
from toontown.catalog import CatalogWallpaperItem
from toontown.catalog import CatalogFlooringItem
from toontown.catalog import CatalogMouldingItem
from toontown.catalog import CatalogWainscotingItem
from toontown.catalog import CatalogWindowItem
from toontown.building import DoorTypes
from direct.fsm import ClassicFSM
from direct.fsm import State
from direct.task import Task
import random
from . import HouseGlobals
from . import CannonGlobals
from toontown.ai import DatabaseObject
from otp.otpbase import PythonUtil
from toontown.toonbase import ToontownGlobals
from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator


class DistributedHouseAI(DistributedObjectAI.DistributedObjectAI):

    """
    This is the class that handles the creation of a house and all
    things contained in an house, including:  rooms, furniture,
    piggy bank, posters, decorations, etc.
    """

    notify = directNotify.newCategory("DistributedHouseAI")

    HouseModel = None

    def __init__(self, air):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        self.doId = 0
        #self.estateId = 0
        self.zoneId = 0
        self.housePos = 0
        # self.garden = None
        self.cannon = None
        self.housePosInd = 0

        # these members are stored in the db and initialized in the
        # initFromServerResponse function (called by the estateAI).
        # These are the default values until they are initialized by
        # the database.  (It is more convenient here not to depend on
        # initial value settings in the dc file.)

        self.houseType = HouseGlobals.HOUSE_DEFAULT
        self.gardenPosInd = 0
        self.gardenPos = self.gardenPosInd

        self.ownerId = 0
        self.name = ""
        self.colorIndex = 0
        self.atticItems = CatalogItemList.CatalogItemList()
        self.interiorItems = CatalogItemList.CatalogItemList()
        self.atticWallpaper = CatalogItemList.CatalogItemList()
        self.interiorWallpaper = CatalogItemList.CatalogItemList()
        self.atticWindows = CatalogItemList.CatalogItemList()
        self.interiorWindows = CatalogItemList.CatalogItemList()
        self.deletedItems = CatalogItemList.CatalogItemList()
        self.cannonEnabled = 0

        # initialize the stuff that doesn't need a response from the database
        self.interior = None
        self.interiorManager = None
        self.mailbox = None



    def delete(self):
        self.notify.debug("delete")
        self.ignoreAll()
        try:
            self.House_deleted
            self.notify.debug("house already deleted")
        except:
            self.notify.debug("completing delete")
            self.House_deleted = 1
            if hasattr(self, 'houseNode'):
                self.houseNode.removeNode()
                del self.houseNode
            # clean up the doors
            if self.interior:
                del simbase.air.estateMgr.houseZone2estateZone[
                    self.interiorZoneId]
                self.air.deallocateZone(self.interiorZoneId)
                self.interior.requestDelete()
                self.interior = None
                self.door.requestDelete()
                del self.door
                self.insideDoor.requestDelete()
                del self.insideDoor
                #if self.garden:
                #    self.garden.requestDelete()
                #    del self.garden
                if self.cannon:
                    self.cannon.requestDelete()
                    del self.cannon
                    self.cannon = None
            if self.mailbox:
                self.mailbox.requestDelete()
                self.mailbox = None
            if self.interiorManager:
                self.interiorManager.requestDelete()
                self.interiorManager = None
            DistributedObjectAI.DistributedObjectAI.delete(self)

    def announceGenerate(self):
        DistributedObjectAI.DistributedObjectAI.announceGenerate(self)
        self.setupEnvirons()

    def setupEnvirons(self):
        self.doId = self.getDoId()
        # This method is called by the EstateManager as it is creating
        # the house.  It sets up the doors, mailbox, furniture, etc.,
        # for the house.
        self.notify.debug("setupEnvirons")

        if self.ownerId and len(self.interiorWallpaper) == 0 and len(self.interiorWindows) == 0:
            # This is a newly-occupied house.  We should set up initial
            # furniture for it.
            self.notify.debug("Resetting furniture for now-occupied house %s." % (self.doId))
            self.setInitialFurniture()

        # Toon interior:
        self.interiorZoneId = self.air.allocateZone()

        # Outside mailbox (if we have one)
        if self.ownerId:
            self.mailbox = DistributedMailboxAI.DistributedMailboxAI(self.air, self)
            self.mailbox.generateWithRequired(self.zoneId)

        # Outside door:
        self.door = DistributedHouseDoorAI.DistributedHouseDoorAI(
            self.air, self.doId, DoorTypes.EXT_STANDARD)

        # Inside door of the same door (different zone, and different distributed object):
        self.insideDoor = DistributedHouseDoorAI.DistributedHouseDoorAI(
            self.air, self.doId, DoorTypes.INT_STANDARD)

        # Tell them about each other:
        self.door.setOtherDoor(self.insideDoor)
        self.insideDoor.setOtherDoor(self.door)
        self.door.zoneId = self.zoneId
        self.insideDoor.zoneId = self.interiorZoneId
        # Now that they both now about each other, generate them:
        self.door.generateWithRequired(self.zoneId)
        self.insideDoor.generateWithRequired(self.interiorZoneId)

        # create the garden in our zone
        # gardenPos = HouseGlobals.gardenDrops[self.gardenPosInd]
        # self.garden = DistributedGardenAI.DistributedGardenAI(self.air, gardenPos, 10)
        # self.garden.generateWithRequired(self.zoneId)
        # self.garden.start()
        # self.garden_created = 1

        # create a cannon

        if self.interior != None:
            self.interior.requestDelete()
            self.interior = None

        self.interior = DistributedHouseInteriorAI.DistributedHouseInteriorAI(
            self.doId, self.air, self.interiorZoneId, self)
        self.interior.generateWithRequired(self.interiorZoneId)
        # add this house to the map of house zone to estate zone
        simbase.air.estateMgr.houseZone2estateZone[
            self.interiorZoneId] = self.zoneId

        # This is a temporary hack, to ensure the user has a phone.
        # It's only necessary because some players on the test server
        # started playing before we had a phone as one of the
        # furniture items.
        #if self.ownerId != 0 and not self.__hasPhone():
         #   self.notify.info("Creating default phone for %s." % (self.ownerId))
          #  item = CatalogFurnitureItem.CatalogFurnitureItem(1399, posHpr = (-12, 3, 0.025, 180, 0, 0))
           # self.interiorItems.append(item)
            #self.d_setInteriorItems(self.interiorItems)

        self.resetFurniture()

        #if simbase.wantPets:
            #if 0:#__dev__:
                #pt = ProfileTimer()
                #pt.init('house model load')
                #pt.on()

            # add ourselves to the estate model


            #if 0:#__dev__:
               # pt.mark('loaded house model')
                #pt.off()
                #pt.printTo()
        self.d_setHouseReady()

    def __hasPhone(self):
        for item in self.interiorItems:
            if (item.getFlags() & CatalogFurnitureItem.FLPhone) != 0:
                return 1

        for item in self.atticItems:
            if (item.getFlags() & CatalogFurnitureItem.FLPhone) != 0:
                return 1

        return 0

    def resetFurniture(self):
        # Deletes all of the furniture, wallpaper, and window items, and
        # recreates it all.

        if self.interiorManager != None:
            self.interiorManager.requestDelete()
            self.interiorManager = None

        # Create a furniture manager for the interior furniture.
        self.interiorManager = DistributedFurnitureManagerAI.DistributedFurnitureManagerAI(self.air, self, 1)
        self.interiorManager.generateWithRequired(self.interiorZoneId)

        # Create all of the furniture items inside the house.
        for item in self.interiorItems:
            self.interiorManager.manifestInteriorItem(item)

        # Force the wallpaper and windows to be reissued to the
        # interior.
        self.interior.b_setWallpaper(self.interiorWallpaper)
        self.interior.b_setWindows(self.interiorWindows)

    def setInitialFurniture(self):
        # Resets the furniture to the initial default furniture for an
        # avatar.  Normally this is called only when the house is
        # first assigned, and for debugging.

        avatar = self.air.doId2do.get(self.ownerId)

        # Boys are given the boy wardrobe initially, while girls are
        # given the girl wardrobe.

        trunkItem = 4000
        wardrobeItem = 500
        if avatar and avatar.getStyle().getGender() == 'f':
            wardrobeItem = 510
            trunkItem = 4010
        

        InitialFurnitureA = CatalogItemList.CatalogItemList([
            CatalogFurnitureItem.CatalogFurnitureItem(200, posHpr = (-23.618, 16.1823, 0.025, 90, 0, 0)),
            CatalogFurnitureItem.CatalogFurnitureItem(wardrobeItem, posHpr = (-22.5835, 21.8784, 0.025, 90, 0, 0)),
            CatalogFurnitureItem.CatalogFurnitureItem(trunkItem, posHpr = (-18.5835, 21.8784, 0.025, 90, 0, 0)),
            CatalogFurnitureItem.CatalogFurnitureItem(1300, posHpr = (-21.4932, 5.76027, 0.025, 120, 0, 0)),
            CatalogFurnitureItem.CatalogFurnitureItem(400, posHpr = (-18.6, -12.0, 0.025, 90.0, 0.0, 0.0)),
            CatalogFurnitureItem.CatalogFurnitureItem(100, posHpr = (-18.9, -20.5, 0.025, 90.0, 0.0, 0.0)),
            CatalogFurnitureItem.CatalogFurnitureItem(100, posHpr = (-18.9, -3.5, 0.025, 90.0, 0.0, 0.0)),
            CatalogFurnitureItem.CatalogFurnitureItem(700, posHpr = (-3.34375, 22.3644, 0.025, -90, 0, 0)),
            CatalogFurnitureItem.CatalogFurnitureItem(710, posHpr = (0, -23, 0.025, 180, 0, 0)),
            CatalogFurnitureItem.CatalogFurnitureItem(700, posHpr = (4.44649, -0.463924, 0.025, 0, 0, 0)),
            CatalogFurnitureItem.CatalogFurnitureItem(1399, posHpr = (-10.1, 2.0, 0.1, 0, 0, 0)),
            ])

        InitialFurnitureB = CatalogItemList.CatalogItemList([
            CatalogFurnitureItem.CatalogFurnitureItem(200, posHpr = (-3.2, 17.0, 0.025, -0.2, 0.0, 0.0)),
            CatalogFurnitureItem.CatalogFurnitureItem(400, posHpr = (-18.6, -7.1, 0.025, 90.0, 0.0, 0.0)),
            CatalogFurnitureItem.CatalogFurnitureItem(700, posHpr = (3.6, -23.7, 0.025, 179.9, 0.0, 0.0)),
            CatalogFurnitureItem.CatalogFurnitureItem(710, posHpr = (-16.6, -19.1, 0.025, 90.0, 0.0, 0.0)),
            CatalogFurnitureItem.CatalogFurnitureItem(700, posHpr = (-1.8, -23.6, 0.025, 179.9, 0.0, 0.0)),
            CatalogFurnitureItem.CatalogFurnitureItem(wardrobeItem, posHpr = (-20.1, 4.4, 0.025, -180.0, 0.0, 0.0)),
            CatalogFurnitureItem.CatalogFurnitureItem(trunkItem, posHpr = (-15, 4.4, 0.025, -180.0, 0.0, 0.0)),
            CatalogFurnitureItem.CatalogFurnitureItem(100, posHpr = (-1.1, 22.4, 0.025, -90.2, 0.0, 0.0)),
            CatalogFurnitureItem.CatalogFurnitureItem(1300, posHpr = (-21.7, 19.5, 0.025, 90.0, 0.0, 0.0)),
            CatalogFurnitureItem.CatalogFurnitureItem(100, posHpr = (4.0, 1.9, 0.025, -0.1, 0.0, 0.0)),
            CatalogFurnitureItem.CatalogFurnitureItem(1399, posHpr = (-10.1, 2.0, 0.1, 0, 0, 0)),
            ])

        InitialFurnitureC = CatalogItemList.CatalogItemList([
            CatalogFurnitureItem.CatalogFurnitureItem(200, posHpr = (-22.1, 6.5, 0.025, 90.0, 0.0, 0.0)),
            CatalogFurnitureItem.CatalogFurnitureItem(400, posHpr = (-0.2, -25.7, 0.025, 179.9, 0.0, 0.0)),
            CatalogFurnitureItem.CatalogFurnitureItem(710, posHpr = (-16.6, -12.2, 0.025, 90.0, 0.0, 0.0)),
            CatalogFurnitureItem.CatalogFurnitureItem(wardrobeItem, posHpr = (-4.7, 24.5, 0.025, 0.0, 0.0, 0.0)),
            CatalogFurnitureItem.CatalogFurnitureItem(trunkItem, posHpr = (-10.7, 24.5, 0.025, 0.0, 0.0, 0.0)),

            CatalogFurnitureItem.CatalogFurnitureItem(1300, posHpr = (-20.5, 22.3, 0.025, 45.0, 0.0, 0.0)),
            CatalogFurnitureItem.CatalogFurnitureItem(100, posHpr = (-12.0, 25.9, 0.025, 0.0, 0.0, 0.0)),
            CatalogFurnitureItem.CatalogFurnitureItem(700, posHpr = (9.4, -8.6, 0.025, 67.5, 0.0, 0.0)),
            CatalogFurnitureItem.CatalogFurnitureItem(700, posHpr = (9.7, -15.1, 0.025, 112.5, 0.0, 0.0)),
            CatalogFurnitureItem.CatalogFurnitureItem(100, posHpr = (-14.7, 1.88, 0.025, 0.0, 0.0, 0.0)),
            CatalogFurnitureItem.CatalogFurnitureItem(1399, posHpr = (-10.1, 2.0, 0.1, 0, 0, 0)),
        ])

        self.b_setDeletedItems(CatalogItemList.CatalogItemList())
        self.b_setAtticItems(CatalogItemList.CatalogItemList())
        self.b_setInteriorItems(random.choice((InitialFurnitureA,
                                               InitialFurnitureB,
                                               InitialFurnitureC,
                                               )))
        self.b_setAtticWallpaper(CatalogItemList.CatalogItemList())

        # Choose a random set of wallpapers, and use the same set for
        # both rooms.
        wallpaper = [
            # Wallpaper
            random.choice(CatalogWallpaperItem.getWallpaperRange(1000,1299)),
            # Moulding
            random.choice(CatalogMouldingItem.getAllMouldings(1000, 1010)),
            # Flooring
            random.choice(CatalogFlooringItem.getAllFloorings(1000, 1010)),
            # Wainscoting
            random.choice(CatalogWainscotingItem.getAllWainscotings(1000, 1010)),
            ]

        self.b_setInteriorWallpaper(CatalogItemList.CatalogItemList(wallpaper + wallpaper))
        self.b_setAtticWindows(CatalogItemList.CatalogItemList())

        # Everyone starts out with a simple garden view, twice.
        self.b_setInteriorWindows(CatalogItemList.CatalogItemList([
            CatalogWindowItem.CatalogWindowItem(20, placement = 2),
            CatalogWindowItem.CatalogWindowItem(20, placement = 4),
            ]))


    def b_setHouseType(self, houseType):
        self.setHouseType(houseType)
        self.d_setHouseType(houseType)

    def d_setHouseType(self, houseType):
        self.sendUpdate("setHouseType", [houseType])

    def setHouseType(self, houseType):
        self.notify.debug("setHouseType(%s): %s" % (houseType, self.doId))
        self.houseType = houseType

    def getHouseType(self):
        self.notify.debug("getHouseType")
        return self.houseType

    def setGardenPos(self, gardenPosInd):
        self.notify.debug("setGardenPos(%s): %s" % (gardenPosInd, self.doId))
        self.gardenPosInd = gardenPosInd

        gardenPos = HouseGlobals.gardenDrops[self.gardenPosInd]
        self.notify.debug("(%s) self.gardenPos = %s" % (self.doId, gardenPos))

    def getGardenPos(self):
        self.notify.debug('getGardenPos')
        return self.gardenPosInd

    def setHousePos(self, housePosInd):
        self.notify.debug("setHousePos(%s): %s" % (housePosInd, self.doId))
        self.housePosInd = housePosInd

    def getHousePos(self):
        self.notify.debug('getHousePos')
        return self.housePosInd

    def b_setAvatarId(self, avId):
        self.notify.debug("b_setAvatarId(%s) = %s" % (self.doId, avId))
        self.setAvatarId(avId)
        self.d_setAvatarId(avId)

    def d_setAvatarId(self, avId):
        self.sendUpdate("setAvatarId", [avId])

    def setAvatarId(self, avId):
        self.notify.debug("setAvatarId(%s) = %s" % (self.doId, avId))
        self.ownerId = avId
        # set the avatars houseId also
        try:
            av = self.air.doId2do[avId]
            av.b_setHouseId(self.doId)
        except:
            self.notify.debug("unable to set av(%s)'s houseId" % avId)

    def getAvatarId(self):
        self.notify.debug("getAvatarId(%s)" % (self.doId))
        return self.ownerId

    def b_setName(self, name):
        self.setName(name)
        self.d_setName(name)

    def setName(self, name):
        self.name = name

    def d_setName(self, name):
        self.sendUpdate("setName", [name])

    def getName(self):
        return self.name

    def b_setColor(self, colorInd):
        self.setColor(colorInd)
        self.d_setColor(colorInd)

    def d_setColor(self, colorInd):
        self.sendUpdate("setColor", [colorInd])

    def setColor(self, colorInd):
        self.colorIndex = colorInd

    def getColor(self):
        return self.colorIndex

    def b_setAtticItems(self, items):
        self.setAtticItems(items)
        self.d_setAtticItems(items)

    def d_setAtticItems(self, items):
        self.sendUpdate("setAtticItems", [items.getBlob(store = CatalogItem.Customization)])

    def setAtticItems(self, items):
        self.atticItems = CatalogItemList.CatalogItemList(items, store = CatalogItem.Customization)

    def getAtticItems(self):
        return self.atticItems.getBlob(store = CatalogItem.Customization)

    def addAtticItem(self, item):
        # Called when a new attic item has been purchased, this
        # appends the item to all the appropriate places.

        # Make sure that we only have one of a couple of special
        # items.
        if item.getFlags() & CatalogFurnitureItem.FLBank:
            self.removeOldItem(CatalogFurnitureItem.FLBank)
        if item.getFlags() & CatalogFurnitureItem.FLCloset:
            self.removeOldItem(CatalogFurnitureItem.FLCloset)

        self.makeRoomFor(1)

        self.atticItems.append(item)
        self.d_setAtticItems(self.atticItems)
        if self.interiorManager:
            self.interiorManager.d_setAtticItems(self.atticItems)

    def removeOldItem(self, flag):
        # Called when we are about to add a new bank or closet to the
        # attic, this searches for and removes the previous bank or
        # closet.  It actually removes any items found whose
        # item.getFlags() member matches the bits in flag.
        self.notify.info("Removing old item matching %x from house %s" % (flag, self.doId))

        newAtticItems = CatalogItemList.CatalogItemList([], store = CatalogItem.Customization)
        for item in self.atticItems:
            if (item.getFlags() & flag) == 0:
                # This item doesn't match; preserve it.
                newAtticItems.append(item)
            else:
                self.notify.info("removing %s from attic" % (item))

        newInteriorItems = CatalogItemList.CatalogItemList([], store = CatalogItem.Location | CatalogItem.Customization)
        for item in self.interiorItems:
            if (item.getFlags() & flag) == 0:
                # This item doesn't match; preserve it.
                newInteriorItems.append(item)
            else:
                self.notify.info("removing %s from interior" % (item))

        self.b_setAtticItems(newAtticItems)
        self.b_setInteriorItems(newInteriorItems)

        if self.interiorManager:
            self.interiorManager.d_setAtticItems(self.atticItems)

            # Also remove any corresponding dfitems from the interior.
            newDfitems = []
            for dfitem in self.interiorManager.dfitems:
                if (dfitem.item.getFlags() & flag) == 0:
                    # This item doesn't match; preserve it.
                    newDfitems.append(dfitem)
                else:
                    # This item does match, remove it.
                    dfitem.requestDelete()
            self.interiorManager.dfitems = newDfitems

    def b_setInteriorItems(self, items):
        self.setInteriorItems(items)
        self.d_setInteriorItems(items)

    def d_setInteriorItems(self, items):
        self.sendUpdate("setInteriorItems", [items.getBlob(store = CatalogItem.Location | CatalogItem.Customization)])

    def setInteriorItems(self, items):
        # This should only be called once, to fill the data from the
        # database.  Subsequently, we should modify the list directly,
        # so we don't break the connection between items on the list
        # and manifested DistributedFurnitureItems.
        self.interiorItems = CatalogItemList.CatalogItemList(items, store = CatalogItem.Location | CatalogItem.Customization)

    def getInteriorItems(self):
        return self.interiorItems.getBlob(store = CatalogItem.Location | CatalogItem.Customization)

    def addWallpaper(self, item):
        # Called when a new wallpaper item has been purchased.

        self.makeRoomFor(1)

        # Just add the new wallpaper to the attic.
        self.atticWallpaper.append(item)

        # Update the database and the interior.
        self.d_setAtticWallpaper(self.atticWallpaper)

    def b_setAtticWallpaper(self, items):
        self.setAtticWallpaper(items)
        self.d_setAtticWallpaper(items)

    def d_setAtticWallpaper(self, items):
        self.sendUpdate("setAtticWallpaper", [items.getBlob(store = CatalogItem.Customization)])
        if self.interiorManager:
            self.interiorManager.d_setAtticWallpaper(items)

    def setAtticWallpaper(self, items):
        self.atticWallpaper = CatalogItemList.CatalogItemList(items, store = CatalogItem.Customization)

    def getAtticWallpaper(self):
        return self.atticWallpaper.getBlob(store = CatalogItem.Customization)

    def b_setInteriorWallpaper(self, items):
        self.setInteriorWallpaper(items)
        self.d_setInteriorWallpaper(items)

    def d_setInteriorWallpaper(self, items):
        self.sendUpdate("setInteriorWallpaper", [items.getBlob(store = CatalogItem.Customization)])
        if self.interior:
            self.interior.b_setWallpaper(items)

    def setInteriorWallpaper(self, items):
        self.interiorWallpaper = CatalogItemList.CatalogItemList(items, store = CatalogItem.Customization)

    def getInteriorWallpaper(self):
        return self.interiorWallpaper.getBlob(store = CatalogItem.Customization)

    def b_setDeletedItems(self, items):
        self.setDeletedItems(items)
        self.d_setDeletedItems(items)

    def d_setDeletedItems(self, items):
        self.sendUpdate("setDeletedItems", [items.getBlob(store = CatalogItem.Customization | CatalogItem.DeliveryDate)])

    def setDeletedItems(self, items):
        self.deletedItems = CatalogItemList.CatalogItemList(items, store = CatalogItem.Customization | CatalogItem.DeliveryDate)

        if self.air.doLiveUpdates:
            deleted = self.reconsiderDeletedItems()

            # If we removed any deleted items, immediately send the new
            # list back to the database.
            if deleted:
                self.d_setDeletedItems(self.deletedItems)

                if self.interiorManager:
                    self.interiorManager.d_setDeletedItems(self.deletedItems)

    def getDeletedItems(self):
        return self.deletedItems.getBlob(store = CatalogItem.Customization | CatalogItem.DeliveryDate)

    def reconsiderDeletedItems(self):
        # Removes items from the deletedItems list whose expiration
        # time has expired.  Returns the list of deleted items.

        # Get the current time in minutes.
        now = (int)(time.time() / 60 + 0.5)

        deleted, remaining = self.deletedItems.extractDeliveryItems(now)
        if deleted:
            self.notify.info("Aging out deleted items for %s, eliminated %s" % (self.doId, deleted))

        self.deletedItems = remaining

        return deleted

    def addToDeleted(self, item):
        # Adds the indicated item to the deleted item list.

        now = (int)(time.time() / 60 + 0.5)
        item.deliveryDate = now + ToontownGlobals.DeletedItemLifetime
        self.deletedItems.append(item)
        self.reconsiderDeletedItems()

        self.d_setDeletedItems(self.deletedItems)

    def makeRoomFor(self, count):
        # Ensures there is room for at least count items to be added
        # to the house by eliminated old items from the deleted list.
        # Returns the list of eliminated items, if any.  The deleted
        # items list is automatically updated to the database if
        # necessary.

        numAtticItems = len(self.atticItems) + len(self.atticWallpaper) + len(self.atticWindows)
        numHouseItems = numAtticItems + len(self.interiorItems)

        needHouseItems = numHouseItems + len(self.deletedItems) + count
        maxHouseItems = ToontownGlobals.MaxHouseItems + ToontownGlobals.ExtraDeletedItems
        eliminateCount = max(needHouseItems - maxHouseItems, 0)

        extracted, remaining = self.deletedItems.extractOldestItems(eliminateCount)
        if extracted:
            self.notify.info("Making room for %s items for %s, eliminated %s" % (eliminateCount, self.ownerId, extracted))
            self.deletedItems = remaining
            self.d_setDeletedItems(self.deletedItems)

            if self.interiorManager:
                self.interiorManager.d_setDeletedItems(self.deletedItems)

        return extracted





  

    def addWindow(self, item):
        # Called when a new window item has been purchased, this
        # appends the item to all the appropriate places.

        self.makeRoomFor(1)

        # Just put it in the attic.
        self.atticWindows.append(item)
        self.d_setAtticWindows(self.atticWindows)

    def b_setAtticWindows(self, items):
        self.setAtticWindows(items)
        self.d_setAtticWindows(items)

    def d_setAtticWindows(self, items):
        self.sendUpdate("setAtticWindows", [items.getBlob(store = CatalogItem.Customization)])
        if self.interiorManager:
            self.interiorManager.d_setAtticWindows(items)

    def setAtticWindows(self, items):
        self.atticWindows = CatalogItemList.CatalogItemList(items, store = CatalogItem.Customization)

    def getAtticWindows(self):
        return self.atticWindows.getBlob(store = CatalogItem.Customization)

    def b_setInteriorWindows(self, items):
        self.setInteriorWindows(items)
        self.d_setInteriorWindows(items)

    def d_setInteriorWindows(self, items):
        self.sendUpdate("setInteriorWindows", [items.getBlob(store = CatalogItem.Customization | CatalogItem.WindowPlacement)])
        if self.interior:
            self.interior.b_setWindows(items)

    def setInteriorWindows(self, items):
        self.interiorWindows = CatalogItemList.CatalogItemList(items, store = CatalogItem.Customization | CatalogItem.WindowPlacement)

    def getInteriorWindows(self):
        return self.interiorWindows.getBlob(store = CatalogItem.Customization | CatalogItem.WindowPlacement)

    def checkOwner(self):
        # Checks whether the owner still exists, and checks whether
        # he's got stuff waiting in his mailbox.

        self.notify.debug("__checkOwner: %s" % (self.doId))

        if self.ownerId == 0:
            # No owner.  Duh.
            self.d_setHouseReady()
            return

        owner = self.air.doId2do.get(self.ownerId)
        if owner and hasattr(owner, "onOrder"):
            # The avatar is in the live database.
            hp = owner.getMaxHp()
            #self.b_setCannonEnabled(1)
            self.__checkMailbox(owner.onOrder, owner.mailboxContents, 1, owner.awardMailboxContents, owner.numMailItems, owner.getNumInvitesToShowInMailbox())

        else:
            # We have to go query the database for the avatar's info.
            gotAvEvent = self.uniqueName("gotAvatar")
            self.acceptOnce(gotAvEvent, self.__gotOwnerAv)

            db = DatabaseObject.DatabaseObject(self.air, self.ownerId)
            db.doneEvent = gotAvEvent

            db.getFields(['setDeliverySchedule', 'setMailboxContents', 'setMaxHp', 'setAwardMailboxContents'])

    def __gotOwnerAv(self, db, retcode):
        assert(self.notify.debug("__gotOwnerAv(%s, %s): %s" % (list(db.values.keys()), retcode, self.doId)))
        if retcode != 0:
            self.notify.warning("Avatar %s for house %s does not exist!" % (self.ownerId, self.doId))
            return

        # The avatar still exists, so check its properties.
        onOrder = None
        mailboxContents = None
        awardMailboxContents = None

        dg = db.values.get('setDeliverySchedule')
        if dg:
            di = PyDatagramIterator(dg)
            blob = di.getString()
            onOrder = CatalogItemList.CatalogItemList(blob, store = CatalogItem.Customization | CatalogItem.DeliveryDate)

        dg = db.values.get('setMailboxContents')
        if dg:
            di = PyDatagramIterator(dg)
            blob = di.getString()
            mailboxContents = CatalogItemList.CatalogItemList(blob, store = CatalogItem.Customization)

        dg = db.values.get('setMaxHp')
        if dg:
            di = PyDatagramIterator(dg)
            hp = di.getUint16()

        dg = db.values.get('setAwardMailboxContents')
        if dg:
            di = PyDatagramIterator(dg)
            blob = di.getString()
            awardMailboxContents = CatalogItemList.CatalogItemList(blob, store = CatalogItem.Customization)

        #self.b_setCannonEnabled(1)
        self.__checkMailbox(onOrder, mailboxContents, 0, awardMailboxContents)

    def __checkMailbox(self, onOrder, mailboxContents, liveDatabase, awardMailboxContents, numMailItems=0, numPartyInvites=0):
        # We have gotten the above data for the owner of this house.
        # Check whether we should raise the flag because he has
        # something in his mailbox.

        assert(self.notify.debug("__checkMailbox(%s, %s, %s): %s" %
                                 (onOrder, mailboxContents, liveDatabase,
                                  self.doId)))

        # Is the mailbox full?
        if mailboxContents or (numMailItems > 0) or (numPartyInvites > 0) or awardMailboxContents:
            self.notify.debug("mailbox is full; raising flag: %s" % (self.doId))
            self.mailbox.b_setFullIndicator(1)

        elif onOrder:
            # Maybe we have something coming soon.
            nextTime = onOrder.getNextDeliveryDate()
            if nextTime != None:
                duration = nextTime * 60 - time.time()
                if (duration > 0):
                    if not liveDatabase:
                        # If the toon is expecting a delivery later,
                        # set a timer to raise the flag at that
                        # time--but don't bother if the toon was found
                        # in the live database (because in that case,
                        # the DistributedToonAI will raise the flag).
                        self.notify.debug("expecting delivery in %s, will raise flag later: %s" % (PythonUtil.formatElapsedSeconds(duration), self.doId))
                        self.mailbox.raiseFlagLater(duration)
                else:
                    self.notify.debug("delivery has been completed, raising flag: %s" % (self.doId))
                    self.mailbox.b_setFullIndicator(1)

        # Now tell the client that the house is ready.
        self.d_setHouseReady()

    def b_setCannonEnabled(self, index):
        self.setCannonEnabled(index)
        self.d_setCannonEnabled(index)

    def d_setCannonEnabled(self, index):
        self.sendUpdate("setCannonEnabled", [index])

    def setCannonEnabled(self, index):
        self.cannonEnabled = index
        if  self.cannonEnabled and not self.cannon:
            # create the cannon now
            posHpr = CannonGlobals.cannonDrops[self.housePosInd]
            estate = simbase.air.doId2do[self.doId]
            targetId = estate.target.doId
            self.cannon = DistributedCannonAI.DistributedCannonAI(self.air, self.estateId,
                                                                  targetId, *posHpr)
            self.cannon.generateWithRequired(self.zoneId)
        elif self.cannon and not self.cannonEnabled:
            # delete the cannon
            self.cannon.requestDelete()
            del self.cannon
            self.cannon = None

    def getCannonEnabled(self):
        return self.cannonEnabled

    def d_setHouseReady(self):
        self.notify.debug("setHouseReady: %s" % (self.doId))
        self.sendUpdate("setHouseReady", [])

