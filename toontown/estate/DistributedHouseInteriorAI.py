from toontown.toonbase.ToontownGlobals import *

from otp.ai.AIBaseGlobal import *
from direct.distributed.ClockDelta import *

from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObjectAI
from toontown.catalog import CatalogItemList
from toontown.catalog import CatalogItem
from toontown.estate.DistributedFurnitureManagerAI import DistributedFurnitureManagerAI

class DistributedHouseInteriorAI(DistributedObjectAI.DistributedObjectAI):
    """
    DistributedHouseInteriorAI class:  
    """

    if __debug__:
        notify = DirectNotifyGlobal.directNotify.newCategory('DistributedHouseInteriorAI')

    def __init__(self, houseId, air, zoneId, house):
        """blockNumber: the landmark building number (from the name)"""
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        self.zoneId = zoneId
        self.house = house
        self.houseId = houseId
        self.ownerId = self.house.ownerId
        self.wallpaper = self.house.interiorWallpaper
        self.windows = self.house.interiorWindows
        self.houseIndex = house.housePosInd
        self.furnitureManager = None

        
        assert(self.debugPrint(
                "DistributedHouseInteriorAI(air=%s, zoneId=%s, house=%s)"
                %(air, zoneId, house)))


    def generate(self):
        # Inheritors should put functions that require self.zoneId or
        # other networked info in this function.
        DistributedObjectAI.DistributedObjectAI.generate(self)

    def delete(self):
        assert(self.debugPrint("delete()"))
        self.ignoreAll()
        del self.house
        DistributedObjectAI.DistributedObjectAI.delete(self)

    def getHouseId(self):
        return self.houseId

    def getHouseIndex(self):
        return self.houseIndex

    def b_setWallpaper(self, items):
        self.setWallpaper(items)
        self.d_setWallpaper(items)

    def d_setWallpaper(self, items):
        self.sendUpdate("setWallpaper", [items.getBlob(store = CatalogItem.Customization)])

    def setWallpaper(self, items):
        self.wallpaper = CatalogItemList.CatalogItemList(items, store = CatalogItem.Customization)

    def getWallpaper(self):
        return self.wallpaper.getBlob(store = CatalogItem.Customization)

    def b_setWindows(self, items):
        self.setWindows(items)
        self.d_setWindows(items)

    def d_setWindows(self, items):
        self.sendUpdate("setWindows", [items.getBlob(store = CatalogItem.Customization | CatalogItem.WindowPlacement)])

    def setWindows(self, items):
        self.windows = CatalogItemList.CatalogItemList(items, store = CatalogItem.Customization | CatalogItem.WindowPlacement)

    def getWindows(self):
        return self.windows.getBlob(store = CatalogItem.Customization | CatalogItem.WindowPlacement)
    
    if __debug__:
        def debugPrint(self, message):
            """for debugging"""
            return self.notify.debug(
                    str(self.__dict__.get('zoneId', '?'))+' '+message)


