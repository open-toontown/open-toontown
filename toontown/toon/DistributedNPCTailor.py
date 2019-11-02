from pandac.PandaModules import *
from DistributedNPCToonBase import *
from direct.gui.DirectGui import *
from pandac.PandaModules import *
import NPCToons
from direct.task.Task import Task
import TailorClothesGUI
from toontown.toonbase import TTLocalizer
import ToonDNA
from toontown.estate import ClosetGlobals

class DistributedNPCTailor(DistributedNPCToonBase):

    def __init__(self, cr):
        DistributedNPCToonBase.__init__(self, cr)
        self.isLocalToon = 0
        self.clothesGUI = None
        self.av = None
        self.oldStyle = None
        self.browsing = 0
        self.roomAvailable = 0
        self.button = None
        self.popupInfo = None
        return

    def disable(self):
        self.ignoreAll()
        taskMgr.remove(self.uniqueName('popupPurchaseGUI'))
        taskMgr.remove(self.uniqueName('lerpCamera'))
        if self.clothesGUI:
            self.clothesGUI.exit()
            self.clothesGUI.unload()
            self.clothesGUI = None
            if self.button != None:
                self.button.destroy()
                del self.button
            self.cancelButton.destroy()
            del self.cancelButton
            del self.gui
            self.counter.show()
            del self.counter
        if self.popupInfo:
            self.popupInfo.destroy()
            self.popupInfo = None
        self.av = None
        self.oldStyle = None
        base.localAvatar.posCamera(0, 0)
        DistributedNPCToonBase.disable(self)
        return

    def handleCollisionSphereEnter(self, collEntry):
        base.cr.playGame.getPlace().fsm.request('purchase')
        self.sendUpdate('avatarEnter', [])

    def __handleUnexpectedExit(self):
        self.notify.warning('unexpected exit')
        self.av = None
        self.oldStyle = None
        return

    def resetTailor(self):
        self.ignoreAll()
        taskMgr.remove(self.uniqueName('popupPurchaseGUI'))
        taskMgr.remove(self.uniqueName('lerpCamera'))
        if self.clothesGUI:
            self.clothesGUI.hideButtons()
            self.clothesGUI.exit()
            self.clothesGUI.unload()
            self.clothesGUI = None
            if self.button != None:
                self.button.destroy()
                del self.button
            self.cancelButton.destroy()
            del self.cancelButton
            del self.gui
            self.counter.show()
            del self.counter
            self.show()
        self.startLookAround()
        self.detectAvatars()
        self.clearMat()
        if self.isLocalToon:
            self.freeAvatar()
        return Task.done

    def setMovie(self, mode, npcId, avId, timestamp):
        timeStamp = ClockDelta.globalClockDelta.localElapsedTime(timestamp)
        self.remain = NPCToons.CLERK_COUNTDOWN_TIME - timeStamp
        self.npcId = npcId
        self.isLocalToon = avId == base.localAvatar.doId
        if mode == NPCToons.PURCHASE_MOVIE_CLEAR:
            return
        if mode == NPCToons.PURCHASE_MOVIE_TIMEOUT:
            taskMgr.remove(self.uniqueName('lerpCamera'))
            if self.isLocalToon:
                self.ignore(self.purchaseDoneEvent)
                self.ignore(self.swapEvent)
                if self.popupInfo:
                    self.popupInfo.reparentTo(hidden)
            if self.clothesGUI:
                self.clothesGUI.resetClothes(self.oldStyle)
                self.__handlePurchaseDone(timeout=1)
            self.setChatAbsolute(TTLocalizer.STOREOWNER_TOOKTOOLONG, CFSpeech | CFTimeout)
            self.resetTailor()
        elif mode == NPCToons.PURCHASE_MOVIE_START or mode == NPCToons.PURCHASE_MOVIE_START_BROWSE or mode == NPCToons.PURCHASE_MOVIE_START_NOROOM:
            if mode == NPCToons.PURCHASE_MOVIE_START:
                self.browsing = 0
                self.roomAvailable = 1
            elif mode == NPCToons.PURCHASE_MOVIE_START_BROWSE:
                self.browsing = 1
                self.roomAvailable = 1
            elif mode == NPCToons.PURCHASE_MOVIE_START_NOROOM:
                self.browsing = 0
                self.roomAvailable = 0
            self.av = base.cr.doId2do.get(avId)
            if self.av is None:
                self.notify.warning('Avatar %d not found in doId' % avId)
                return
            else:
                self.accept(self.av.uniqueName('disable'), self.__handleUnexpectedExit)
            style = self.av.getStyle()
            self.oldStyle = ToonDNA.ToonDNA()
            self.oldStyle.makeFromNetString(style.makeNetString())
            self.setupAvatars(self.av)
            if self.isLocalToon:
                camera.wrtReparentTo(render)
                camera.lerpPosHpr(-5, 9, self.getHeight() - 0.5, -150, -2, 0, 1, other=self, blendType='easeOut', task=self.uniqueName('lerpCamera'))
            if self.browsing == 0:
                if self.roomAvailable == 0:
                    self.setChatAbsolute(TTLocalizer.STOREOWNER_NOROOM, CFSpeech | CFTimeout)
                else:
                    self.setChatAbsolute(TTLocalizer.STOREOWNER_GREETING, CFSpeech | CFTimeout)
            else:
                self.setChatAbsolute(TTLocalizer.STOREOWNER_BROWSING, CFSpeech | CFTimeout)
            if self.isLocalToon:
                taskMgr.doMethodLater(3.0, self.popupPurchaseGUI, self.uniqueName('popupPurchaseGUI'))
                print '-----------Starting tailor interaction-----------'
                print 'avid: %s, gender: %s' % (self.av.doId, self.av.style.gender)
                print 'current top = %s,%s,%s,%s and  bot = %s,%s,' % (self.av.style.topTex,
                 self.av.style.topTexColor,
                 self.av.style.sleeveTex,
                 self.av.style.sleeveTexColor,
                 self.av.style.botTex,
                 self.av.style.botTexColor)
                print 'topsList = %s' % self.av.getClothesTopsList()
                print 'bottomsList = %s' % self.av.getClothesBottomsList()
                print '-------------------------------------------------'
        elif mode == NPCToons.PURCHASE_MOVIE_COMPLETE:
            self.setChatAbsolute(TTLocalizer.STOREOWNER_GOODBYE, CFSpeech | CFTimeout)
            if self.av and self.isLocalToon:
                print '-----------ending tailor interaction-----------'
                print 'avid: %s, gender: %s' % (self.av.doId, self.av.style.gender)
                print 'current top = %s,%s,%s,%s and  bot = %s,%s,' % (self.av.style.topTex,
                 self.av.style.topTexColor,
                 self.av.style.sleeveTex,
                 self.av.style.sleeveTexColor,
                 self.av.style.botTex,
                 self.av.style.botTexColor)
                print 'topsList = %s' % self.av.getClothesTopsList()
                print 'bottomsList = %s' % self.av.getClothesBottomsList()
                print '-------------------------------------------------'
            self.resetTailor()
        elif mode == NPCToons.PURCHASE_MOVIE_NO_MONEY:
            self.notify.warning('PURCHASE_MOVIE_NO_MONEY should not be called')
            self.resetTailor()
        return

    def popupPurchaseGUI(self, task):
        self.setChatAbsolute('', CFSpeech)
        self.purchaseDoneEvent = 'purchaseDone'
        self.swapEvent = 'swap'
        self.acceptOnce(self.purchaseDoneEvent, self.__handlePurchaseDone)
        self.accept(self.swapEvent, self.__handleSwap)
        self.clothesGUI = TailorClothesGUI.TailorClothesGUI(self.purchaseDoneEvent, self.swapEvent, self.npcId)
        self.clothesGUI.load()
        self.clothesGUI.enter(self.av)
        self.clothesGUI.showButtons()
        self.gui = loader.loadModel('phase_3/models/gui/create_a_toon_gui')
        if self.browsing == 0:
            self.button = DirectButton(relief=None, image=(self.gui.find('**/CrtAtoon_Btn1_UP'), self.gui.find('**/CrtAtoon_Btn1_DOWN'), self.gui.find('**/CrtAtoon_Btn1_RLLVR')), pos=(-0.15, 0, -0.85), command=self.__handleButton, text=('', TTLocalizer.MakeAToonDone, TTLocalizer.MakeAToonDone), text_font=ToontownGlobals.getInterfaceFont(), text_scale=0.08, text_pos=(0, -0.03), text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1))
        else:
            self.button = None
        self.cancelButton = DirectButton(relief=None, image=(self.gui.find('**/CrtAtoon_Btn2_UP'), self.gui.find('**/CrtAtoon_Btn2_DOWN'), self.gui.find('**/CrtAtoon_Btn2_RLLVR')), pos=(0.15, 0, -0.85), command=self.__handleCancel, text=('', TTLocalizer.MakeAToonCancel, TTLocalizer.MakeAToonCancel), text_font=ToontownGlobals.getInterfaceFont(), text_scale=0.08, text_pos=(0, -0.03), text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1))
        camera.setPosHpr(base.localAvatar, -4.16, 8.25, 2.47, -152.89, 0.0, 0.0)
        self.counter = render.find('**/*mo1_TI_counter')
        self.counter.hide()
        self.hide()
        return Task.done

    def __handleButton(self):
        messenger.send('next')

    def __handleCancel(self):
        self.clothesGUI.resetClothes(self.oldStyle)
        messenger.send('last')

    def __handleSwap(self):
        self.d_setDNA(self.av.getStyle().makeNetString(), 0)

    def __handlePurchaseDone(self, timeout = 0):
        if self.clothesGUI.doneStatus == 'last' or timeout == 1:
            self.d_setDNA(self.oldStyle.makeNetString(), 1)
        else:
            which = 0
            if self.clothesGUI.topChoice != -1:
                which = which | ClosetGlobals.SHIRT
            if self.clothesGUI.bottomChoice != -1:
                which = which | ClosetGlobals.SHORTS
            print 'setDNA: which = %d, top = %d, bot = %d' % (which, self.clothesGUI.topChoice, self.clothesGUI.bottomChoice)
            if self.roomAvailable == 0:
                if self.isLocalToon:
                    if self.av.isClosetFull() or which & ClosetGlobals.SHIRT and which & ClosetGlobals.SHORTS:
                        self.__enterConfirmLoss(2, which)
                        self.clothesGUI.hideButtons()
                        self.button.hide()
                        self.cancelButton.hide()
                    else:
                        self.d_setDNA(self.av.getStyle().makeNetString(), 2, which)
            else:
                self.d_setDNA(self.av.getStyle().makeNetString(), 2, which)

    def __enterConfirmLoss(self, finished, which):
        if self.popupInfo == None:
            buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
            okButtonImage = (buttons.find('**/ChtBx_OKBtn_UP'), buttons.find('**/ChtBx_OKBtn_DN'), buttons.find('**/ChtBx_OKBtn_Rllvr'))
            cancelButtonImage = (buttons.find('**/CloseBtn_UP'), buttons.find('**/CloseBtn_DN'), buttons.find('**/CloseBtn_Rllvr'))
            self.popupInfo = DirectFrame(
                parent=hidden,
                relief=None,
                state='normal',
                text=TTLocalizer.STOREOWNER_CONFIRM_LOSS,
                text_wordwrap=10,
                textMayChange=0,
                frameSize=(-1, 1, -1, 1),
                text_pos=(0, -0.05),
                geom=DGG.getDefaultDialogGeom(),
                geom_color=ToontownGlobals.GlobalDialogColor,
                geom_scale=(0.88, 1, 0.55),
                geom_pos=(0, 0, -.18),
                text_scale=0.08)

            DirectButton(
                self.popupInfo,
                image=okButtonImage,
                relief=None,
                text=TTLocalizer.STOREOWNER_OK,
                text_scale=0.05,
                text_pos=(0.0, -0.1),
                textMayChange=0,
                pos=(-0.08, 0.0, -0.31),
                command=self.__handleConfirmLossOK,
                extraArgs=[finished, which])

            DirectButton(
                self.popupInfo,
                image=cancelButtonImage,
                relief=None,
                text=TTLocalizer.STOREOWNER_CANCEL,
                text_scale=0.05,
                text_pos=(0.0, -0.1),
                textMayChange=0,
                pos=(0.08, 0.0, -0.31),
                command=self.__handleConfirmLossCancel)

            buttons.removeNode()

        self.popupInfo.reparentTo(aspect2d)

    def __handleConfirmLossOK(self, finished, which):
        self.d_setDNA(self.av.getStyle().makeNetString(), finished, which)
        self.popupInfo.reparentTo(hidden)

    def __handleConfirmLossCancel(self):
        self.d_setDNA(self.oldStyle.makeNetString(), 1)
        self.popupInfo.reparentTo(hidden)

    def d_setDNA(self, dnaString, finished, whichItems = ClosetGlobals.SHIRT | ClosetGlobals.SHORTS):
        self.sendUpdate('setDNA', [dnaString, finished, whichItems])

    def setCustomerDNA(self, avId, dnaString):
        if avId != base.localAvatar.doId:
            av = base.cr.doId2do.get(avId, None)
            if av:
                if self.av == av:
                    oldTorso = self.av.style.torso
                    self.av.style.makeFromNetString(dnaString)
                    if len(oldTorso) == 2 and len(self.av.style.torso) == 2 and self.av.style.torso[1] != oldTorso[1]:
                        self.av.swapToonTorso(self.av.style.torso, genClothes=0)
                        self.av.loop('neutral', 0)
                    self.av.generateToonClothes()
        return
