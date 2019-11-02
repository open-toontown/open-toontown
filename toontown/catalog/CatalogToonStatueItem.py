import CatalogGardenItem
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from otp.otpbase import OTPLocalizer
from direct.interval.IntervalGlobal import *
from toontown.estate import GardenGlobals

class CatalogToonStatueItem(CatalogGardenItem.CatalogGardenItem):
    pictureToonStatue = None

    def makeNewItem(self, itemIndex = 105, count = 1, tagCode = 1, endPoseIndex = 108):
        self.startPoseIndex = itemIndex
        self.endPoseIndex = endPoseIndex
        CatalogGardenItem.CatalogGardenItem.makeNewItem(self, itemIndex, count, tagCode)

    def needsCustomize(self):
        return self.endPoseIndex - self.startPoseIndex > 0

    def getPicture(self, avatar):
        from toontown.estate import DistributedToonStatuary
        toonStatuary = DistributedToonStatuary.DistributedToonStatuary(None)
        toonStatuary.setupStoneToon(base.localAvatar.style)
        toonStatuary.poseToonFromSpecialsIndex(self.gardenIndex)
        toonStatuary.toon.setZ(0)
        model, ival = self.makeFrameModel(toonStatuary.toon, 1)
        self.pictureToonStatue = toonStatuary
        self.hasPicture = True
        return (model, ival)

    def cleanupPicture(self):
        self.pictureToonStatue.deleteToon()
        self.pictureToonStatue = None
        CatalogGardenItem.CatalogGardenItem.cleanupPicture(self)
        return

    def decodeDatagram(self, di, versionNumber, store):
        CatalogGardenItem.CatalogGardenItem.decodeDatagram(self, di, versionNumber, store)
        self.startPoseIndex = di.getUint8()
        self.endPoseIndex = di.getUint8()

    def encodeDatagram(self, dg, store):
        CatalogGardenItem.CatalogGardenItem.encodeDatagram(self, dg, store)
        dg.addUint8(self.startPoseIndex)
        dg.addUint8(self.endPoseIndex)

    def compareTo(self, other):
        if self.gardenIndex >= self.startPoseIndex and self.gardenIndex <= self.endPoseIndex:
            return 0
        return 1

    def getAllToonStatues(self):
        self.statueList = []
        for index in range(self.startPoseIndex, self.endPoseIndex + 1):
            self.statueList.append(CatalogToonStatueItem(index, 1, endPoseIndex=index))

        return self.statueList

    def deleteAllToonStatues(self):
        while len(self.statueList):
            item = self.statueList[0]
            if item.pictureToonStatue:
                item.pictureToonStatue.deleteToon()
            self.statueList.remove(item)
