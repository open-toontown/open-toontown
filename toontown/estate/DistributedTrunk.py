from pandac.PandaModules import *
from direct.gui.DirectGui import *
from direct.task.Task import Task
from direct.interval.IntervalGlobal import *
import DistributedCloset
import ClosetGlobals
import TrunkGUI
from toontown.toon import ToonDNA
from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownGlobals
N_A = 0

class DistributedTrunk(DistributedCloset.DistributedCloset):
    notify = directNotify.newCategory('DistributedTrunk')

    def __init__(self, cr):
        DistributedCloset.DistributedCloset.__init__(self, cr)
        self.hatList = []
        self.glassesList = []
        self.backpackList = []
        self.shoesList = []
        self.oldHatList = []
        self.oldGlassesList = []
        self.oldBackpackList = []
        self.oldShoesList = []
        self.swapHatEvent = ''
        self.swapGlassesEvent = ''
        self.swapBackpackEvent = ''
        self.swapShoesEvent = ''
        self.hatDeleted = 0
        self.glassesDeleted = 0
        self.backpackDeleted = 0
        self.shoesDeleted = 0
        self.isFreePlayer = 0

    def printInfo(self):
        print 'avid: %s, gender: %s' % (self.av.doId, self.av.style.gender)
        print 'current hat = %s, glasses = %s, backpack = %s, shoes = %s' % (self.av.getHat(),
         self.av.getGlasses(),
         self.av.getBackpack(),
         self.av.getShoes())
        print 'hatList = %s' % self.av.getHatList()
        print 'glassesList = %s' % self.av.getGlassesList()
        print 'backpackList = %s' % self.av.getBackpackList()
        print 'shoesList = %s' % self.av.getShoesList()

    def setState(self, mode, avId, ownerId, gender, hatList, glassesList, backpackList, shoesList):
        self.notify.debug('setState, mode=%s, avId=%s, ownerId=%d' % (mode, avId, ownerId))
        self.isOwner = avId == ownerId
        self.ownerGender = gender
        if mode == ClosetGlobals.CLOSED:
            self.fsm.request('closed')
            return
        elif mode == ClosetGlobals.OPEN:
            self.customerId = avId
            self.av = self.cr.doId2do.get(self.customerId, None)
            if self.av:
                if self.av.getGameAccess() != ToontownGlobals.AccessFull:
                    self.isOwner = 0
                    self.isFreePlayer = 1
                else:
                    self.isFreePlayer = 0
                if base.localAvatar.getDoId() == self.customerId:
                    self.gender = self.av.style.gender
                    self.hatList = hatList
                    self.glassesList = glassesList
                    self.backpackList = backpackList
                    self.shoesList = shoesList
                    self.oldHatList = self.hatList[0:]
                    self.oldGlassesList = self.glassesList[0:]
                    self.oldBackpackList = self.backpackList[0:]
                    self.oldShoesList = self.shoesList[0:]
                    print '-----------Starting trunk interaction-----------'
                    self.printInfo()
                    print '-------------------------------------------------'
                    if not self.isOwner:
                        self.__popupNotOwnerPanel()
                    else:
                        taskMgr.doMethodLater(0.5, self.popupChangeClothesGUI, self.uniqueName('popupChangeClothesGUI'))
                self.fsm.request('open')
        return

    def load(self):
        lNode = self.find('**/lid_origin')
        lLid = self.find('**/lid')
        if lNode.isEmpty() or lLid.isEmpty():
            self.lid = None
        else:
            lLid.wrtReparentTo(lNode)
            self.lid = lNode
        if not lNode.isEmpty():
            self.scale = lLid.getScale()[0] * 0.6
        return

    def popupChangeClothesGUI(self, task):
        self.notify.debug('popupChangeClothesGUI')
        self.purchaseDoneEvent = self.uniqueName('purchaseDone')
        self.swapHatEvent = self.uniqueName('swapHat')
        self.swapGlassesEvent = self.uniqueName('swapGlasses')
        self.swapBackpackEvent = self.uniqueName('swapBackpack')
        self.swapShoesEvent = self.uniqueName('swapShoes')
        self.cancelEvent = self.uniqueName('cancel')
        self.accept(self.purchaseDoneEvent, self.__proceedToCheckout)
        self.accept(self.swapHatEvent, self.__handleSwapHat)
        self.accept(self.swapGlassesEvent, self.__handleSwapGlasses)
        self.accept(self.swapBackpackEvent, self.__handleSwapBackpack)
        self.accept(self.swapShoesEvent, self.__handleSwapShoes)
        self.accept(self.cancelEvent, self._handleCancel)
        self.deleteEvent = self.uniqueName('delete')
        if self.isOwner:
            self.accept(self.deleteEvent, self.__handleDelete)
        if not self.closetGUI:
            self.closetGUI = TrunkGUI.TrunkGUI(self.isOwner, self.purchaseDoneEvent, self.cancelEvent, self.swapHatEvent, self.swapGlassesEvent, self.swapBackpackEvent, self.swapShoesEvent, self.deleteEvent, self.hatList, self.glassesList, self.backpackList, self.shoesList)
            self.closetGUI.load()
            if self.gender != self.ownerGender:
                self.closetGUI.setGender(self.ownerGender)
            self.closetGUI.enter(base.localAvatar)
            self.closetGUI.showButtons()
            oldHat = self.av.getHat()
            oldGlasses = self.av.getGlasses()
            oldBackpack = self.av.getBackpack()
            oldShoes = self.av.getShoes()
            self.oldStyle = {ToonDNA.HAT: oldHat,
             ToonDNA.GLASSES: oldGlasses,
             ToonDNA.BACKPACK: oldBackpack,
             ToonDNA.SHOES: oldShoes}
        return Task.done

    def resetCloset(self):
        self.ignoreAll()
        taskMgr.remove(self.uniqueName('popupChangeClothesGUI'))
        taskMgr.remove(self.uniqueName('lerpCamera'))
        taskMgr.remove(self.uniqueName('lerpToon'))
        if self.closetGUI:
            self.closetGUI.hideButtons()
            self.closetGUI.exit()
            self.closetGUI.unload()
            self.closetGUI = None
            del self.av
        self.av = base.localAvatar
        oldHat = self.av.getHat()
        oldGlasses = self.av.getGlasses()
        oldBackpack = self.av.getBackpack()
        oldShoes = self.av.getShoes()
        self.oldStyle = {ToonDNA.HAT: oldHat,
         ToonDNA.GLASSES: oldGlasses,
         ToonDNA.BACKPACK: oldBackpack,
         ToonDNA.SHOES: oldShoes}
        self.hatDeleted = 0
        self.glassesDeleted = 0
        self.backpackDeleted = 0
        self.shoesDeleted = 0
        return Task.done

    def _handleCancel(self):
        if self.oldStyle:
            oldHat = self.oldStyle[ToonDNA.HAT]
            oldGlasses = self.oldStyle[ToonDNA.GLASSES]
            oldBackpack = self.oldStyle[ToonDNA.BACKPACK]
            oldShoes = self.oldStyle[ToonDNA.SHOES]
            self.d_setDNA(oldHat[0], oldHat[1], oldHat[2], oldGlasses[0], oldGlasses[1], oldGlasses[2], oldBackpack[0], oldBackpack[1], oldBackpack[2], oldShoes[0], oldShoes[1], oldShoes[2], 1)
        else:
            self.notify.info('avoided crash in handleCancel')
            self._handlePurchaseDone()
        if self.closetGUI:
            self.closetGUI.resetClothes(self.oldStyle)
        if self.popupInfo != None:
            self.popupInfo.destroy()
            self.popupInfo = None
        return

    def __handleSwapHat(self):
        item = self.av.getHat()
        self.d_setDNA(item[0], item[1], item[2], N_A, N_A, N_A, N_A, N_A, N_A, N_A, N_A, N_A, 0, ToonDNA.HAT)
        if self.closetGUI:
            self.closetGUI.updateTrashButtons()

    def __handleSwapGlasses(self):
        item = self.av.getGlasses()
        self.d_setDNA(N_A, N_A, N_A, item[0], item[1], item[2], N_A, N_A, N_A, N_A, N_A, N_A, 0, ToonDNA.GLASSES)
        if self.closetGUI:
            self.closetGUI.updateTrashButtons()

    def __handleSwapBackpack(self):
        item = self.av.getBackpack()
        self.d_setDNA(N_A, N_A, N_A, N_A, N_A, N_A, item[0], item[1], item[2], N_A, N_A, N_A, 0, ToonDNA.BACKPACK)
        if self.closetGUI:
            self.closetGUI.updateTrashButtons()

    def __handleSwapShoes(self):
        item = self.av.getShoes()
        self.d_setDNA(N_A, N_A, N_A, N_A, N_A, N_A, N_A, N_A, N_A, item[0], item[1], item[2], 0, ToonDNA.SHOES)
        if self.closetGUI:
            self.closetGUI.updateTrashButtons()

    def __handleDelete(self, which):
        if which == ToonDNA.HAT:
            itemList = self.closetGUI.hats
            trashIndex = self.closetGUI.hatChoice
            swapFunc = self.closetGUI.swapHat
            removeFunc = self.closetGUI.removeHat
            trashItem = self.av.getHat()
            self.hatDeleted = self.hatDeleted | 1
        elif which == ToonDNA.GLASSES:
            itemList = self.closetGUI.glasses
            trashIndex = self.closetGUI.glassesChoice
            swapFunc = self.closetGUI.swapGlasses
            removeFunc = self.closetGUI.removeGlasses
            trashItem = self.av.getGlasses()
            self.glassesDeleted = self.glassesDeleted | 1
        elif which == ToonDNA.BACKPACK:
            itemList = self.closetGUI.backpacks
            trashIndex = self.closetGUI.backpackChoice
            swapFunc = self.closetGUI.swapBackpack
            removeFunc = self.closetGUI.removeBackpack
            trashItem = self.av.getBackpack()
            self.backpackDeleted = self.backpackDeleted | 1
        elif which == ToonDNA.SHOES:
            itemList = self.closetGUI.shoes
            trashIndex = self.closetGUI.shoesChoice
            swapFunc = self.closetGUI.swapShoes
            removeFunc = self.closetGUI.removeShoes
            trashItem = self.av.getShoes()
            self.shoesDeleted = self.shoesDeleted | 1
        else:
            self.notify.warning("we don't know about this item(type = %s)" % which)
            return
        if len(itemList) > 1:
            if trashIndex == 0:
                swapFunc(1)
            else:
                swapFunc(-1)
            removeFunc(trashIndex)
            self.sendUpdate('removeItem', [trashItem[0],
             trashItem[1],
             trashItem[2],
             which])
            swapFunc(0)
            self.closetGUI.updateTrashButtons()
        else:
            self.notify.warning("cant delete this item(type = %s), since we don't have a replacement" % which)

    def resetItemLists(self):
        self.hatList = self.oldHatList[0:]
        self.glassesList = self.oldGlassesList[0:]
        self.backpackList = self.oldBackpackList[0:]
        self.shoesList = self.oldShoesList[0:]
        self.closetGUI.hat = self.hatList
        self.closetGUI.glasses = self.glassesList
        self.closetGUI.backpack = self.backpackList
        self.closetGUI.shoes = self.shoesList
        self.hatDeleted = 0
        self.glassesDeleted = 0
        self.backpackDeleted = 0
        self.shoesDeleted = 0

    def __proceedToCheckout(self):
        if self.hatDeleted or self.glassesDeleted or self.backpackDeleted or self.shoesDeleted:
            self.__popupAreYouSurePanel()
        else:
            self._handlePurchaseDone()

    def _handlePurchaseDone(self, timeout = 0):
        if timeout == 1:
            oldHat = self.oldStyle[ToonDNA.HAT]
            oldGlasses = self.oldStyle[ToonDNA.GLASSES]
            oldBackpack = self.oldStyle[ToonDNA.BACKPACK]
            oldShoes = self.oldStyle[ToonDNA.SHOES]
            self.d_setDNA(oldHat[0], oldHat[1], oldHat[2], oldGlasses[0], oldGlasses[1], oldGlasses[2], oldBackpack[0], oldBackpack[1], oldBackpack[2], oldShoes[0], oldShoes[1], oldShoes[2], 1)
        else:
            which = 0
            if hasattr(self.closetGUI, 'hatChoice') and hasattr(self.closetGUI, 'glassesChoice') and hasattr(self.closetGUI, 'backpackChoice') and hasattr(self.closetGUI, 'shoesChoice'):
                if self.closetGUI.hatChoice != 0 or self.hatDeleted:
                    which = which | ToonDNA.HAT
                if self.closetGUI.glassesChoice != 0 or self.glassesDeleted:
                    which = which | ToonDNA.GLASSES
                if self.closetGUI.backpackChoice != 0 or self.backpackDeleted:
                    which = which | ToonDNA.BACKPACK
                if self.closetGUI.shoesChoice != 0 or self.shoesDeleted:
                    which = which | ToonDNA.SHOES
            hat = self.av.getHat()
            glasses = self.av.getGlasses()
            backpack = self.av.getBackpack()
            shoes = self.av.getShoes()
            self.d_setDNA(hat[0], hat[1], hat[2], glasses[0], glasses[1], glasses[2], backpack[0], backpack[1], backpack[2], shoes[0], shoes[1], shoes[2], 2, which)

    def d_setDNA(self, hatIdx, hatTexture, hatColor, glassesIdx, glassesTexture, glassesColor, backpackIdx, backpackTexture, backpackColor, shoesIdx, shoesTexture, shoesColor, finished, which = ToonDNA.HAT | ToonDNA.GLASSES | ToonDNA.BACKPACK | ToonDNA.SHOES):
        self.sendUpdate('setDNA', [hatIdx,
         hatTexture,
         hatColor,
         glassesIdx,
         glassesTexture,
         glassesColor,
         backpackIdx,
         backpackTexture,
         backpackColor,
         shoesIdx,
         shoesTexture,
         shoesColor,
         finished,
         which])

    def setCustomerDNA(self, avId, hatIdx, hatTexture, hatColor, glassesIdx, glassesTexture, glassesColor, backpackIdx, backpackTexture, backpackColor, shoesIdx, shoesTexture, shoesColor, which):
        if avId and avId != base.localAvatar.doId:
            av = base.cr.doId2do.get(avId, None)
            if av:
                if self.av == base.cr.doId2do[avId]:
                    if which & ToonDNA.HAT:
                        self.av.setHat(hatIdx, hatTexture, hatColor)
                    if which & ToonDNA.GLASSES:
                        self.av.setGlasses(glassesIdx, glassesTexture, glassesColor)
                    if which & ToonDNA.BACKPACK:
                        self.av.setBackpack(backpackIdx, backpackTexture, backpackColor)
                    if which & ToonDNA.SHOES:
                        self.av.setShoes(shoesIdx, shoesTexture, shoesColor)
                    self.av.generateToonAccessories()
        return

    def __popupNotOwnerPanel(self):
        if self.popupInfo != None:
            self.popupInfo.destroy()
            self.popupInfo = None
        self.purchaseDoneEvent = self.uniqueName('purchaseDone')
        self.swapHatEvent = self.uniqueName('swapHat')
        self.swapGlassesEvent = self.uniqueName('swapGlasses')
        self.swapBackpackEvent = self.uniqueName('swapBackpack')
        self.swapShoesEvent = self.uniqueName('swapShoes')
        self.cancelEvent = self.uniqueName('cancel')
        self.accept(self.purchaseDoneEvent, self.__proceedToCheckout)
        self.accept(self.swapHatEvent, self.__handleSwapHat)
        self.accept(self.swapGlassesEvent, self.__handleSwapGlasses)
        self.accept(self.swapBackpackEvent, self.__handleSwapBackpack)
        self.accept(self.swapShoesEvent, self.__handleSwapShoes)
        self.accept(self.cancelEvent, self._handleCancel)
        self.deleteEvent = self.uniqueName('delete')
        if self.isOwner:
            self.accept(self.deleteEvent, self.__handleDelete)
        buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
        okButtonImage = (buttons.find('**/ChtBx_OKBtn_UP'), buttons.find('**/ChtBx_OKBtn_DN'), buttons.find('**/ChtBx_OKBtn_Rllvr'))
        if self.isFreePlayer:
            textMsg = TTLocalizer.TrunkNotPaidMessage
        else:
            textMsg = TTLocalizer.TrunkNotOwnerMessage
        self.popupInfo = DirectFrame(parent=hidden, relief=None, state='normal', text=textMsg, frameSize=(-1, 1, -1, 1), text_wordwrap=10, geom=DGG.getDefaultDialogGeom(), geom_color=ToontownGlobals.GlobalDialogColor, geom_scale=(0.88, 1, 0.55), geom_pos=(0, 0, -.08), text_scale=0.08, text_pos=(0, 0.06))
        DirectButton(self.popupInfo, image=okButtonImage, relief=None, text=TTLocalizer.ClosetPopupOK, text_scale=0.05, text_pos=(0.0, -0.1), textMayChange=0, pos=(0.0, 0.0, -0.21), command=self._handleNotOwnerMessageOK)
        buttons.removeNode()
        self.popupInfo.reparentTo(aspect2d)
        return

    def __popupAreYouSurePanel(self):
        if self.popupInfo != None:
            self.popupInfo.destroy()
            self.popupInfo = None
        buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
        okButtonImage = (buttons.find('**/ChtBx_OKBtn_UP'), buttons.find('**/ChtBx_OKBtn_DN'), buttons.find('**/ChtBx_OKBtn_Rllvr'))
        cancelButtonImage = (buttons.find('**/CloseBtn_UP'), buttons.find('**/CloseBtn_DN'), buttons.find('**/CloseBtn_Rllvr'))
        self.popupInfo = DirectFrame(parent=hidden, relief=None, state='normal', text=TTLocalizer.TrunkAreYouSureMessage, frameSize=(-1, 1, -1, 1), text_wordwrap=10, geom=DGG.getDefaultDialogGeom(), geom_color=ToontownGlobals.GlobalDialogColor, geom_scale=(0.88, 1, 0.55), geom_pos=(0, 0, -.08), text_scale=0.08, text_pos=(0, 0.08))
        DirectButton(self.popupInfo, image=okButtonImage, relief=None, text=TTLocalizer.ClosetPopupOK, text_scale=0.05, text_pos=(0.0, -0.1), textMayChange=0, pos=(-0.1, 0.0, -0.21), command=self._handleYesImSure)
        DirectButton(self.popupInfo, image=cancelButtonImage, relief=None, text=TTLocalizer.ClosetPopupCancel, text_scale=0.05, text_pos=(0.0, -0.1), textMayChange=0, pos=(0.1, 0.0, -0.21), command=self._handleNotSure)
        buttons.removeNode()
        self.popupInfo.reparentTo(aspect2d)
        return

    def _openDoors(self):
        if self.closetTrack:
            self.closetTrack.finish()
        openHpr = Vec3(0, -80, 0)
        if self.av:
            self.av.applyCheesyEffect(ToontownGlobals.CENormal)
        self.closetTrack = Parallel()
        if self.lid:
            self.closetTrack.append(self.lid.hprInterval(0.5, openHpr))
        self.closetTrack.start()

    def _closeDoors(self):
        if self.closetTrack:
            self.closetTrack.finish()
        closeHpr = Vec3(0, 0, 0)
        if self.av:
            self.av.reconsiderCheesyEffect()
        self.closetTrack = Parallel()
        if self.lid:
            self.closetTrack.append(self.lid.hprInterval(0.5, closeHpr))
        self.closetTrack.start()
