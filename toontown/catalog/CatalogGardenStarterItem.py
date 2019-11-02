import CatalogItem
import time
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from otp.otpbase import OTPLocalizer
from direct.interval.IntervalGlobal import *
from toontown.toontowngui import TTDialog
from toontown.estate import GardenTutorial

class CatalogGardenStarterItem(CatalogItem.CatalogItem):

    def makeNewItem(self):
        CatalogItem.CatalogItem.makeNewItem(self)

    def getPurchaseLimit(self):
        return 0

    def reachedPurchaseLimit(self, avatar):
        if self in avatar.onOrder or self in avatar.mailboxContents or self in avatar.onGiftOrder or self in avatar.awardMailboxContents or self in avatar.onAwardOrder or hasattr(avatar, 'gardenStarted') and avatar.getGardenStarted():
            return 1
        return 0

    def saveHistory(self):
        return 1

    def getTypeName(self):
        return TTLocalizer.GardenStarterTypeName

    def getName(self):
        return TTLocalizer.GardenStarterTypeName

    def recordPurchase(self, avatar, optional):
        print 'rental-- record purchase'
        if avatar:
            print 'starter garden-- has avater'
            estate = simbase.air.estateMgr.estate.get(avatar.doId)
            if estate:
                print 'starter garden-- has estate'
                estate.placeStarterGarden(avatar.doId)
            else:
                print 'starter garden-- something not there'
        return ToontownGlobals.P_ItemAvailable

    def getPicture(self, avatar):
        self.hasPicture = True
        scale = 1
        heading = 0
        pitch = 30
        roll = 0
        spin = 1
        down = -1
        modelParent = loader.loadModel('phase_5.5/models/estate/watering_cans')
        model = modelParent.find('**/water_canA')
        scale = 0.5
        heading = 45
        return self.makeFrameModel(model, spin)

    def output(self, store = -1):
        return 'CatalogGardenStarterItem(%s)' % self.formatOptionalData(store)

    def compareTo(self, other):
        return 0

    def getHashContents(self):
        return 0

    def getBasePrice(self):
        return 50

    def decodeDatagram(self, di, versionNumber, store):
        CatalogItem.CatalogItem.decodeDatagram(self, di, versionNumber, store)

    def encodeDatagram(self, dg, store):
        CatalogItem.CatalogItem.encodeDatagram(self, dg, store)

    def getDeliveryTime(self):
        return 1

    def isRental(self):
        return 0

    def isGift(self):
        return 0

    def acceptItem(self, mailbox, index, callback):
        self.confirmGarden = TTDialog.TTGlobalDialog(doneEvent='confirmGarden', message=TTLocalizer.MessageConfirmGarden, command=Functor(self.handleGardenConfirm, mailbox, index, callback), style=TTDialog.TwoChoice)
        self.confirmGarden.show()

    def handleGardenConfirm(self, mailbox, index, callback, choice):
        if choice > 0:

            def handleTutorialDone():
                self.gardenTutorial.destroy()
                self.gardenTutorial = None
                return

            self.gardenTutorial = GardenTutorial.GardenTutorial(callback=handleTutorialDone)
            if hasattr(mailbox, 'mailboxGui') and mailbox.mailboxGui:
                mailbox.acceptItem(self, index, callback)
                mailbox.mailboxGui.justExit()
        else:
            callback(ToontownGlobals.P_UserCancelled, self, index)
        if self.confirmGarden:
            self.confirmGarden.cleanup()
            self.confirmGarden = None
        return
