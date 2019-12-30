from . import CatalogItem
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from otp.otpbase import OTPLocalizer
from direct.interval.IntervalGlobal import *
from toontown.estate import GardenGlobals
from direct.actor import Actor
from pandac.PandaModules import NodePath

class CatalogGardenItem(CatalogItem.CatalogItem):
    sequenceNumber = 0

    def makeNewItem(self, itemIndex = 0, count = 3, tagCode = 1):
        self.gardenIndex = itemIndex
        self.numItems = count
        self.giftCode = tagCode
        CatalogItem.CatalogItem.makeNewItem(self)

    def getPurchaseLimit(self):
        if self.gardenIndex == GardenGlobals.GardenAcceleratorSpecial:
            return 1
        else:
            return 100

    def reachedPurchaseLimit(self, avatar):
        if self in avatar.onOrder or self in avatar.mailboxContents or self in avatar.onGiftOrder or self in avatar.awardMailboxContents or self in avatar.onAwardOrder:
            return 1
        return 0

    def getAcceptItemErrorText(self, retcode):
        if retcode == ToontownGlobals.P_ItemAvailable:
            return TTLocalizer.CatalogAcceptGarden
        return CatalogItem.CatalogItem.getAcceptItemErrorText(self, retcode)

    def saveHistory(self):
        return 1

    def getTypeName(self):
        return TTLocalizer.GardenTypeName

    def getName(self):
        name = GardenGlobals.Specials[self.gardenIndex]['photoName']
        return name

    def recordPurchase(self, avatar, optional):
        if avatar:
            avatar.addGardenItem(self.gardenIndex, self.numItems)
        if 1:
            return ToontownGlobals.P_ItemAvailable

    def getPicture(self, avatar):
        photoModel = GardenGlobals.Specials[self.gardenIndex]['photoModel']
        if 'photoAnimation' in GardenGlobals.Specials[self.gardenIndex]:
            modelPath = photoModel + GardenGlobals.Specials[self.gardenIndex]['photoAnimation'][0]
            animationName = GardenGlobals.Specials[self.gardenIndex]['photoAnimation'][1]
            animationPath = photoModel + animationName
            self.model = Actor.Actor()
            self.model.loadModel(modelPath)
            self.model.loadAnims(dict([[animationName, animationPath]]))
            frame, ival = self.makeFrameModel(self.model, 0)
            ival = ActorInterval(self.model, animationName, 2.0)
            photoPos = GardenGlobals.Specials[self.gardenIndex]['photoPos']
            frame.setPos(photoPos)
            photoScale = GardenGlobals.Specials[self.gardenIndex]['photoScale']
            self.model.setScale(photoScale)
            self.hasPicture = True
            return (frame, ival)
        else:
            self.model = loader.loadModel(photoModel)
            frame = self.makeFrame()
            self.model.reparentTo(frame)
            photoPos = GardenGlobals.Specials[self.gardenIndex]['photoPos']
            self.model.setPos(*photoPos)
            photoScale = GardenGlobals.Specials[self.gardenIndex]['photoScale']
            self.model.setScale(photoScale)
            self.hasPicture = True
            return (frame, None)
        return None

    def cleanupPicture(self):
        CatalogItem.CatalogItem.cleanupPicture(self)
        self.model.detachNode()
        self.model = None
        return

    def output(self, store = -1):
        return 'CatalogGardenItem(%s%s)' % (self.gardenIndex, self.formatOptionalData(store))

    def compareTo(self, other):
        return 0

    def getHashContents(self):
        return self.gardenIndex

    def getBasePrice(self):
        beanCost = GardenGlobals.Specials[self.gardenIndex]['beanCost']
        return beanCost

    def decodeDatagram(self, di, versionNumber, store):
        CatalogItem.CatalogItem.decodeDatagram(self, di, versionNumber, store)
        self.gardenIndex = di.getUint8()
        self.numItems = di.getUint8()

    def encodeDatagram(self, dg, store):
        CatalogItem.CatalogItem.encodeDatagram(self, dg, store)
        dg.addUint8(self.gardenIndex)
        dg.addUint8(self.numItems)

    def getRequestPurchaseErrorText(self, retcode):
        retval = CatalogItem.CatalogItem.getRequestPurchaseErrorText(self, retcode)
        origText = retval
        if retval == TTLocalizer.CatalogPurchaseItemAvailable or retval == TTLocalizer.CatalogPurchaseItemOnOrder:
            recipeKey = GardenGlobals.getRecipeKeyUsingSpecial(self.gardenIndex)
            if not recipeKey == -1:
                retval += GardenGlobals.getPlantItWithString(self.gardenIndex)
                if self.gardenIndex == GardenGlobals.GardenAcceleratorSpecial:
                    if GardenGlobals.ACCELERATOR_USED_FROM_SHTIKER_BOOK:
                        retval = origText
                        retval += TTLocalizer.UseFromSpecialsTab
                    retval += TTLocalizer.MakeSureWatered
        return retval

    def getRequestPurchaseErrorTextTimeout(self):
        return 20

    def getDeliveryTime(self):
        if self.gardenIndex == GardenGlobals.GardenAcceleratorSpecial:
            return 24 * 60
        else:
            return 0

    def getPurchaseLimit(self):
        if self.gardenIndex == GardenGlobals.GardenAcceleratorSpecial:
            return 1
        else:
            return 0

    def compareTo(self, other):
        if self.gardenIndex != other.gardenIndex:
            return self.gardenIndex - other.gardenIndex
        return self.gardenIndex - other.gardenIndex

    def reachedPurchaseLimit(self, avatar):
        if avatar.onOrder.count(self) != 0:
            return 1
        if avatar.mailboxContents.count(self) != 0:
            return 1
        for specials in avatar.getGardenSpecials():
            if specials[0] == self.gardenIndex:
                if self.gardenIndex == GardenGlobals.GardenAcceleratorSpecial:
                    return 1

        return 0

    def isSkillTooLow(self, avatar):
        recipeKey = GardenGlobals.getRecipeKeyUsingSpecial(self.gardenIndex)
        recipe = GardenGlobals.Recipes[recipeKey]
        numBeansRequired = len(recipe['beans'])
        canPlant = avatar.getBoxCapability()
        result = False
        if canPlant < numBeansRequired:
            result = True
        if not result and self.gardenIndex in GardenGlobals.Specials and 'minSkill' in GardenGlobals.Specials[self.gardenIndex]:
            minSkill = GardenGlobals.Specials[self.gardenIndex]['minSkill']
            if avatar.shovelSkill < minSkill:
                result = True
            else:
                result = False
        return result

    def noGarden(self, avatar):
        return not avatar.getGardenStarted()

    def isGift(self):
        return 0
