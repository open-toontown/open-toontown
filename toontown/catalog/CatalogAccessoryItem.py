import CatalogItem
from CatalogAccessoryItemGlobals import *
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from toontown.toon import ToonDNA
import random, types
from direct.showbase import PythonUtil
from direct.gui.DirectGui import *
from pandac.PandaModules import *

class CatalogAccessoryItem(CatalogItem.CatalogItem):

    def makeNewItem(self, accessoryType, loyaltyDays = 0):
        self.accessoryType = accessoryType
        self.loyaltyDays = loyaltyDays
        CatalogItem.CatalogItem.makeNewItem(self)

    def storedInTrunk(self):
        return 1

    def notOfferedTo(self, avatar):
        article = AccessoryTypes[self.accessoryType][ATArticle]
        if article in [AHat,
         AGlasses,
         ABackpack,
         AShoes]:
            return 0
        forBoys = article in [ABoysHat,
         ABoysGlasses,
         ABoysBackpack,
         ABoysShoes]
        if avatar.getStyle().getGender() == 'm':
            return not forBoys
        else:
            return forBoys

    def forBoysOnly(self):
        article = AccessoryTypes[self.accessoryType][ATArticle]
        if article in [ABoysHat,
         ABoysGlasses,
         ABoysBackpack,
         ABoysShoes]:
            return 1
        else:
            return 0

    def forGirlsOnly(self):
        article = AccessoryTypes[self.accessoryType][ATArticle]
        if article in [AGirlsHat,
         AGirlsGlasses,
         AGirlsBackpack,
         AGirlsShoes]:
            return 1
        else:
            return 0

    def getPurchaseLimit(self):
        return 1

    def reachedPurchaseLimit(self, avatar):
        if avatar.onOrder.count(self) != 0:
            return 1
        if avatar.onGiftOrder.count(self) != 0:
            return 1
        if avatar.mailboxContents.count(self) != 0:
            return 1
        if self in avatar.awardMailboxContents or self in avatar.onAwardOrder:
            return 1
        str = AccessoryTypes[self.accessoryType][ATString]
        if self.isHat():
            defn = ToonDNA.HatStyles[str]
            hat = avatar.getHat()
            if hat[0] == defn[0] and hat[1] == defn[1] and hat[2] == defn[2]:
                return 1
            l = avatar.hatList
            for i in range(0, len(l), 3):
                if l[i] == defn[0] and l[i + 1] == defn[1] and l[i + 2] == defn[2]:
                    return 1

        elif self.areGlasses():
            defn = ToonDNA.GlassesStyles[str]
            glasses = avatar.getGlasses()
            if glasses[0] == defn[0] and glasses[1] == defn[1] and glasses[2] == defn[2]:
                return 1
            l = avatar.glassesList
            for i in range(0, len(l), 3):
                if l[i] == defn[0] and l[i + 1] == defn[1] and l[i + 2] == defn[2]:
                    return 1

        elif self.isBackpack():
            defn = ToonDNA.BackpackStyles[str]
            backpack = avatar.getBackpack()
            if backpack[0] == defn[0] and backpack[1] == defn[1] and backpack[2] == defn[2]:
                return 1
            l = avatar.backpackList
            for i in range(0, len(l), 3):
                if l[i] == defn[0] and l[i + 1] == defn[1] and l[i + 2] == defn[2]:
                    return 1

        else:
            defn = ToonDNA.ShoesStyles[str]
            shoes = avatar.getShoes()
            if shoes[0] == defn[0] and shoes[1] == defn[1] and shoes[2] == defn[2]:
                return 1
            l = avatar.shoesList
            for i in range(0, len(l), 3):
                if l[i] == defn[0] and l[i + 1] == defn[1] and l[i + 2] == defn[2]:
                    return 1

        return 0

    def getTypeName(self):
        return TTLocalizer.AccessoryTypeName

    def getName(self):
        typeName = TTLocalizer.AccessoryTypeNames.get(self.accessoryType, 0)
        if typeName:
            return typeName
        else:
            article = AccessoryTypes[self.accessoryType][ATArticle]
            return TTLocalizer.AccessoryArticleNames[article]

    def recordPurchase(self, avatar, optional):
        if avatar.isTrunkFull():
            if avatar.getMaxAccessories() == 0:
                return ToontownGlobals.P_NoTrunk
            else:
                return ToontownGlobals.P_NoRoomForItem
        str = AccessoryTypes[self.accessoryType][ATString]
        if self.isHat():
            defn = ToonDNA.HatStyles[str]
            if not avatar.checkAccessorySanity(ToonDNA.HAT, defn[0], defn[1], defn[2]):
                self.notify.warning('Avatar %s lost hat %d %d %d; invalid item.' % (avatar.doId,
                 defn[0],
                 defn[1],
                 defn[2]))
                return ToontownGlobals.P_ItemAvailable
            hat = avatar.getHat()
            added = avatar.addToAccessoriesList(ToonDNA.HAT, hat[0], hat[1], hat[2])
            if added:
                avatar.b_setHatList(avatar.getHatList())
                self.notify.info('Avatar %s put hat %d,%d,%d in trunk.' % (avatar.doId,
                 hat[0],
                 hat[1],
                 hat[2]))
            else:
                self.notify.warning('Avatar %s lost current hat %d %d %d; trunk full.' % (avatar.doId,
                 hat[0],
                 hat[1],
                 hat[2]))
            avatar.b_setHat(defn[0], defn[1], defn[2])
        elif self.areGlasses():
            defn = ToonDNA.GlassesStyles[str]
            if not avatar.checkAccessorySanity(ToonDNA.GLASSES, defn[0], defn[1], defn[2]):
                self.notify.warning('Avatar %s lost glasses %d %d %d; invalid item.' % (avatar.doId,
                 defn[0],
                 defn[1],
                 defn[2]))
                return ToontownGlobals.P_ItemAvailable
            glasses = avatar.getGlasses()
            added = avatar.addToAccessoriesList(ToonDNA.GLASSES, glasses[0], glasses[1], glasses[2])
            if added:
                avatar.b_setGlassesList(avatar.getGlassesList())
                self.notify.info('Avatar %s put glasses %d,%d,%d in trunk.' % (avatar.doId,
                 glasses[0],
                 glasses[1],
                 glasses[2]))
            else:
                self.notify.warning('Avatar %s lost current glasses %d %d %d; trunk full.' % (avatar.doId,
                 glasses[0],
                 glasses[1],
                 glasses[2]))
            avatar.b_setGlasses(defn[0], defn[1], defn[2])
        elif self.isBackpack():
            defn = ToonDNA.BackpackStyles[str]
            if not avatar.checkAccessorySanity(ToonDNA.BACKPACK, defn[0], defn[1], defn[2]):
                self.notify.warning('Avatar %s lost backpack %d %d %d; invalid item.' % (avatar.doId,
                 defn[0],
                 defn[1],
                 defn[2]))
                return ToontownGlobals.P_ItemAvailable
            backpack = avatar.getBackpack()
            added = avatar.addToAccessoriesList(ToonDNA.BACKPACK, backpack[0], backpack[1], backpack[2])
            if added:
                avatar.b_setBackpackList(avatar.getBackpackList())
                self.notify.info('Avatar %s put backpack %d,%d,%d in trunk.' % (avatar.doId,
                 backpack[0],
                 backpack[1],
                 backpack[2]))
            else:
                self.notify.warning('Avatar %s lost current backpack %d %d %d; trunk full.' % (avatar.doId,
                 backpack[0],
                 backpack[1],
                 backpack[2]))
            avatar.b_setBackpack(defn[0], defn[1], defn[2])
        else:
            defn = ToonDNA.ShoesStyles[str]
            if not avatar.checkAccessorySanity(ToonDNA.SHOES, defn[0], defn[1], defn[2]):
                self.notify.warning('Avatar %s lost shoes %d %d %d; invalid item.' % (avatar.doId,
                 defn[0],
                 defn[1],
                 defn[2]))
                return ToontownGlobals.P_ItemAvailable
            shoes = avatar.getShoes()
            added = avatar.addToAccessoriesList(ToonDNA.SHOES, shoes[0], shoes[1], shoes[2])
            if added:
                avatar.b_setShoesList(avatar.getShoesList())
                self.notify.info('Avatar %s put shoes %d,%d,%d in trunk.' % (avatar.doId,
                 shoes[0],
                 shoes[1],
                 shoes[2]))
            else:
                self.notify.warning('Avatar %s lost current shoes %d %d %d; trunk full.' % (avatar.doId,
                 shoes[0],
                 shoes[1],
                 shoes[2]))
            avatar.b_setShoes(defn[0], defn[1], defn[2])
        avatar.d_catalogGenAccessories()
        return ToontownGlobals.P_ItemAvailable

    def getDeliveryTime(self):
        return 60

    def getPicture(self, avatar):
        model = self.loadModel()
        spin = 1
        model.setBin('unsorted', 0, 1)
        self.hasPicture = True
        return self.makeFrameModel(model, spin)

    def applyColor(self, model, color):
        if model == None or color == None:
            return
        if isinstance(color, types.StringType):
            tex = loader.loadTexture(color)
            tex.setMinfilter(Texture.FTLinearMipmapLinear)
            tex.setMagfilter(Texture.FTLinear)
            model.setTexture(tex, 1)
        else:
            needsAlpha = color[3] != 1
            color = VBase4(color[0], color[1], color[2], color[3])
            model.setColorScale(color, 1)
            if needsAlpha:
                model.setTransparency(1)
        return

    def loadModel(self):
        modelPath = self.getFilename()
        if self.areShoes():
            str = AccessoryTypes[self.accessoryType][ATString]
            defn = ToonDNA.ShoesStyles[str]
            legModel = loader.loadModel('phase_3/models/char/tt_a_chr_dgm_shorts_legs_1000')
            model = legModel.find('**/' + modelPath)
        else:
            model = loader.loadModel(modelPath)
        texture = self.getTexture()
        if texture:
            self.applyColor(model, texture)
        colorVec4 = self.getColor()
        if colorVec4:
            modelColor = (colorVec4.getX(), colorVec4.getY(), colorVec4.getZ())
            self.applyColor(model, modelColor)
        model.flattenLight()
        return model

    def requestPurchase(self, phone, callback):
        from toontown.toontowngui import TTDialog
        avatar = base.localAvatar
        accessoriesOnOrder = 0
        for item in avatar.onOrder + avatar.mailboxContents:
            if item.storedInTrunk():
                accessoriesOnOrder += 1

        if avatar.isTrunkFull(accessoriesOnOrder):
            self.requestPurchaseCleanup()
            buttonCallback = PythonUtil.Functor(self.__handleFullPurchaseDialog, phone, callback)
            if avatar.getMaxAccessories() == 0:
                text = TTLocalizer.CatalogPurchaseNoTrunk
            else:
                text = TTLocalizer.CatalogPurchaseTrunkFull
            self.dialog = TTDialog.TTDialog(style=TTDialog.YesNo, text=text, text_wordwrap=15, command=buttonCallback)
            self.dialog.show()
        else:
            CatalogItem.CatalogItem.requestPurchase(self, phone, callback)

    def requestPurchaseCleanup(self):
        if hasattr(self, 'dialog'):
            self.dialog.cleanup()
            del self.dialog

    def __handleFullPurchaseDialog(self, phone, callback, buttonValue):
        from toontown.toontowngui import TTDialog
        self.requestPurchaseCleanup()
        if buttonValue == DGG.DIALOG_OK:
            CatalogItem.CatalogItem.requestPurchase(self, phone, callback)
        else:
            callback(ToontownGlobals.P_UserCancelled, self)

    def getAcceptItemErrorText(self, retcode):
        if retcode == ToontownGlobals.P_ItemAvailable:
            if self.isHat():
                return TTLocalizer.CatalogAcceptHat
            elif self.areGlasses():
                return TTLocalizer.CatalogAcceptGlasses
            elif self.isBackpack():
                return TTLocalizer.CatalogAcceptBackpack
            else:
                return TTLocalizer.CatalogAcceptShoes
        elif retcode == ToontownGlobals.P_NoRoomForItem:
            return TTLocalizer.CatalogAcceptTrunkFull
        elif retcode == ToontownGlobals.P_NoTrunk:
            return TTLocalizer.CatalogAcceptNoTrunk
        return CatalogItem.CatalogItem.getAcceptItemErrorText(self, retcode)

    def isHat(self):
        article = AccessoryTypes[self.accessoryType][ATArticle]
        return article in [AHat, ABoysHat, AGirlsHat]

    def areGlasses(self):
        article = AccessoryTypes[self.accessoryType][ATArticle]
        return article in [AGlasses, ABoysGlasses, AGirlsGlasses]

    def isBackpack(self):
        article = AccessoryTypes[self.accessoryType][ATArticle]
        return article in [ABackpack, ABoysBackpack, AGirlsBackpack]

    def areShoes(self):
        article = AccessoryTypes[self.accessoryType][ATArticle]
        return article in [AShoes, ABoysShoes, AGirlsShoes]

    def output(self, store = -1):
        return 'CatalogAccessoryItem(%s, %s)' % (self.accessoryType, self.formatOptionalData(store))

    def getFilename(self):
        str = AccessoryTypes[self.accessoryType][ATString]
        if self.isHat():
            defn = ToonDNA.HatStyles[str]
            modelPath = ToonDNA.HatModels[defn[0]]
        elif self.areGlasses():
            defn = ToonDNA.GlassesStyles[str]
            modelPath = ToonDNA.GlassesModels[defn[0]]
        elif self.isBackpack():
            defn = ToonDNA.BackpackStyles[str]
            modelPath = ToonDNA.BackpackModels[defn[0]]
        else:
            defn = ToonDNA.ShoesStyles[str]
            modelPath = ToonDNA.ShoesModels[defn[0]]
        return modelPath

    def getTexture(self):
        str = AccessoryTypes[self.accessoryType][ATString]
        if self.isHat():
            defn = ToonDNA.HatStyles[str]
            modelPath = ToonDNA.HatTextures[defn[1]]
        elif self.areGlasses():
            defn = ToonDNA.GlassesStyles[str]
            modelPath = ToonDNA.GlassesTextures[defn[1]]
        elif self.isBackpack():
            defn = ToonDNA.BackpackStyles[str]
            modelPath = ToonDNA.BackpackTextures[defn[1]]
        else:
            defn = ToonDNA.ShoesStyles[str]
            modelPath = ToonDNA.ShoesTextures[defn[1]]
        return modelPath

    def getColor(self):
        return None

    def compareTo(self, other):
        return self.accessoryType - other.accessoryType

    def getHashContents(self):
        return self.accessoryType

    def getBasePrice(self):
        return AccessoryTypes[self.accessoryType][ATBasePrice]

    def getEmblemPrices(self):
        result = ()
        info = AccessoryTypes[self.accessoryType]
        if ATEmblemPrices <= len(info) - 1:
            result = info[ATEmblemPrices]
        return result

    def decodeDatagram(self, di, versionNumber, store):
        CatalogItem.CatalogItem.decodeDatagram(self, di, versionNumber, store)
        self.accessoryType = di.getUint16()
        if versionNumber >= 6:
            self.loyaltyDays = di.getUint16()
        else:
            self.loyaltyDays = 0
        str = AccessoryTypes[self.accessoryType][ATString]
        if self.isHat():
            defn = ToonDNA.HatStyles[str]
        elif self.areGlasses():
            defn = ToonDNA.GlassesStyles[str]
        elif self.isBackpack():
            defn = ToonDNA.BackpackStyles[str]
        else:
            defn = ToonDNA.ShoesStyles[str]
        color = ToonDNA.ClothesColors[defn[2]]

    def encodeDatagram(self, dg, store):
        CatalogItem.CatalogItem.encodeDatagram(self, dg, store)
        dg.addUint16(self.accessoryType)
        dg.addUint16(self.loyaltyDays)

    def isGift(self):
        if self.getEmblemPrices():
            return 0
        if self.loyaltyRequirement() > 0:
            return 0
        elif self.accessoryType in LoyaltyAccessoryItems:
            return 0
        else:
            return 1


def getAllAccessories(*accessoryTypes):
    list = []
    for accessoryType in accessoryTypes:
        base = CatalogAccessoryItem(accessoryType)
        list.append(base)

    return list
