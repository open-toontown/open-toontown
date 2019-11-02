import CatalogItem
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from otp.otpbase import OTPLocalizer
from direct.interval.IntervalGlobal import *
from direct.gui.DirectGui import *

class CatalogNametagItem(CatalogItem.CatalogItem):
    sequenceNumber = 0

    def makeNewItem(self, nametagStyle):
        self.nametagStyle = nametagStyle
        CatalogItem.CatalogItem.makeNewItem(self)

    def getPurchaseLimit(self):
        return 1

    def reachedPurchaseLimit(self, avatar):
        if self in avatar.onOrder or self in avatar.mailboxContents or self in avatar.onGiftOrder or self in avatar.awardMailboxContents or self in avatar.onAwardOrder:
            return 1
        if avatar.nametagStyle == self.nametagStyle:
            return 1
        return 0

    def getAcceptItemErrorText(self, retcode):
        if retcode == ToontownGlobals.P_ItemAvailable:
            return TTLocalizer.CatalogAcceptNametag
        return CatalogItem.CatalogItem.getAcceptItemErrorText(self, retcode)

    def saveHistory(self):
        return 1

    def getTypeName(self):
        return TTLocalizer.NametagTypeName

    def getName(self):
        if self.nametagStyle == 100:
            name = TTLocalizer.UnpaidNameTag
        else:
            name = TTLocalizer.NametagFontNames[self.nametagStyle]
        if TTLocalizer.NametagReverse:
            name = TTLocalizer.NametagLabel + name
        else:
            name = name + TTLocalizer.NametagLabel
        return name
        if self.nametagStyle == 0:
            name = TTLocalizer.NametagPaid
        elif self.nametagStyle == 1:
            name = TTLocalizer.NametagAction
        elif self.nametagStyle == 2:
            name = TTLocalizer.NametagFrilly

    def recordPurchase(self, avatar, optional):
        if avatar:
            avatar.b_setNametagStyle(self.nametagStyle)
        return ToontownGlobals.P_ItemAvailable

    def getPicture(self, avatar):
        frame = self.makeFrame()
        if self.nametagStyle == 100:
            inFont = ToontownGlobals.getToonFont()
        else:
            inFont = ToontownGlobals.getNametagFont(self.nametagStyle)
        nameTagDemo = DirectLabel(parent=frame, relief=None, pos=(0, 0, 0.24), scale=0.5, text=localAvatar.getName(), text_fg=(1.0, 1.0, 1.0, 1), text_shadow=(0, 0, 0, 1), text_font=inFont, text_wordwrap=9)
        self.hasPicture = True
        return (frame, None)

    def output(self, store = -1):
        return 'CatalogNametagItem(%s%s)' % (self.nametagStyle, self.formatOptionalData(store))

    def compareTo(self, other):
        return self.nametagStyle - other.nametagStyle

    def getHashContents(self):
        return self.nametagStyle

    def getBasePrice(self):
        return 500
        cost = 500
        if self.nametagStyle == 0:
            cost = 600
        elif self.nametagStyle == 1:
            cost = 600
        elif self.nametagStyle == 2:
            cost = 600
        elif self.nametagStyle == 100:
            cost = 50
        return cost

    def decodeDatagram(self, di, versionNumber, store):
        CatalogItem.CatalogItem.decodeDatagram(self, di, versionNumber, store)
        self.nametagStyle = di.getUint16()

    def encodeDatagram(self, dg, store):
        CatalogItem.CatalogItem.encodeDatagram(self, dg, store)
        dg.addUint16(self.nametagStyle)

    def isGift(self):
        return 0

    def getBackSticky(self):
        itemType = 1
        numSticky = 4
        return (itemType, numSticky)
