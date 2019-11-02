import CatalogItem
import CatalogAtticItem
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from CatalogSurfaceColors import *
STWallpaper = 0
STMoulding = 1
STFlooring = 2
STWainscoting = 3
NUM_ST_TYPES = 4

class CatalogSurfaceItem(CatalogAtticItem.CatalogAtticItem):

    def makeNewItem(self):
        CatalogAtticItem.CatalogAtticItem.makeNewItem(self)

    def setPatternIndex(self, patternIndex):
        self.patternIndex = patternIndex

    def setColorIndex(self, colorIndex):
        self.colorIndex = colorIndex

    def saveHistory(self):
        return 1

    def recordPurchase(self, avatar, optional):
        self.giftTag = None
        house, retcode = self.getHouseInfo(avatar)
        if retcode >= 0:
            house.addWallpaper(self)
        return retcode

    def getDeliveryTime(self):
        return 60
