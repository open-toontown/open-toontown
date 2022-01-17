from direct.gui.DirectGui import *
from pandac.PandaModules import *
from toontown.toonbase.ToontownGlobals import *
from toontown.toonbase.ToonBaseGlobal import *
from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *
from direct.distributed.ClockDelta import *
from toontown.toonbase import ToontownGlobals
from direct.showbase import DirectObject
from toontown.toon import ToonDNA
from direct.fsm import ClassicFSM, State, StateData
from . import ClosetGUI
from direct.task.Task import Task
from . import ClosetGlobals
from . import DistributedFurnitureItem
from toontown.toonbase import TTLocalizer

class DistributedCloset(DistributedFurnitureItem.DistributedFurnitureItem):
    notify = directNotify.newCategory('DistributedCloset')

    def __init__(self, cr):
        DistributedFurnitureItem.DistributedFurnitureItem.__init__(self, cr)
        self.notify.debug('__init__')
        self.lastAvId = 0
        self.hasLocalAvatar = 0
        self.lastTime = 0
        self.av = None
        self.closetGUI = None
        self.closetModel = None
        self.closetSphere = None
        self.closetSphereNode = None
        self.closetSphereNodePath = None
        self.topList = []
        self.botList = []
        self.oldTopList = []
        self.oldBotList = []
        self.oldStyle = None
        self.button = None
        self.topTrashButton = None
        self.bottomTrashButton = None
        self.isLocalToon = None
        self.popupInfo = None
        self.isOwner = 0
        self.ownerId = 0
        self.customerId = 0
        self.purchaseDoneEvent = ''
        self.swapEvent = ''
        self.locked = 0
        self.gender = None
        self.topDeleted = 0
        self.bottomDeleted = 0
        self.closetTrack = None
        self.lerpCameraSeq = None
        self.avMoveTrack = None
        self.scale = 1.0
        self.fsm = ClassicFSM.ClassicFSM('Closet', [State.State('off', self.enterOff, self.exitOff, ['ready', 'open', 'closed']),
         State.State('ready', self.enterReady, self.exitReady, ['open', 'closed']),
         State.State('closed', self.enterClosed, self.exitClosed, ['open', 'off']),
         State.State('open', self.enterOpen, self.exitOpen, ['closed', 'off'])], 'off', 'off')
        self.fsm.enterInitialState()
        return

    def generate(self):
        DistributedFurnitureItem.DistributedFurnitureItem.generate(self)

    def announceGenerate(self):
        self.notify.debug('announceGenerate')
        DistributedFurnitureItem.DistributedFurnitureItem.announceGenerate(self)
        self.load()
        self.setupCollisionSphere()
        self.fsm.request('ready')

    def load(self):
        self.setTwoSided(1)
        lNode = self.find('**/door_rotate_L')
        lDoor = self.find('**/closetdoor_L')
        if lNode.isEmpty() or lDoor.isEmpty():
            self.leftDoor = None
        else:
            lDoor.wrtReparentTo(lNode)
            self.leftDoor = lNode
        rNode = self.find('**/door_rotate_R')
        rDoor = self.find('**/closetdoor_R')
        if rNode.isEmpty() or rDoor.isEmpty():
            self.rightDoor = None
        else:
            rDoor.wrtReparentTo(rNode)
            self.rightDoor = rNode
        if not lNode.isEmpty():
            self.scale = lNode.getScale()[0]
        return

    def setupCollisionSphere(self):
        if self.ownerId:
            self.closetSphereEvent = self.uniqueName('closetSphere')
            self.closetSphereEnterEvent = 'enter' + self.closetSphereEvent
            self.closetSphere = CollisionSphere(0, 0, 0, self.scale * 2.125)
            self.closetSphere.setTangible(0)
            self.closetSphereNode = CollisionNode(self.closetSphereEvent)
            self.closetSphereNode.setIntoCollideMask(WallBitmask)
            self.closetSphereNode.addSolid(self.closetSphere)
            self.closetSphereNodePath = self.attachNewNode(self.closetSphereNode)

    def disable(self):
        self.notify.debug('disable')
        self.ignore(self.closetSphereEnterEvent)
        self.ignoreAll()
        taskMgr.remove(self.uniqueName('popupChangeClothesGUI'))
        if self.lerpCameraSeq:
            self.lerpCameraSeq.finish()
            self.lerpCameraSeq = None
        taskMgr.remove(self.uniqueName('lerpToon'))
        if self.closetTrack:
            self.closetTrack.finish()
            self.closetTrack = None
        if self.closetGUI:
            self.closetGUI.resetClothes(self.oldStyle)
            self.resetCloset()
        if self.hasLocalAvatar:
            self.freeAvatar()
        self.ignoreAll()
        DistributedFurnitureItem.DistributedFurnitureItem.disable(self)
        return

    def delete(self):
        self.notify.debug('delete')
        DistributedFurnitureItem.DistributedFurnitureItem.delete(self)
        if self.popupInfo:
            self.popupInfo.destroy()
            self.popupInfo = None
        if self.av:
            del self.av
        del self.gender
        del self.closetSphere
        del self.closetSphereNode
        del self.closetSphereNodePath
        del self.closetGUI
        del self.fsm
        return

    def enterOff(self):
        pass

    def exitOff(self):
        pass

    def enterReady(self):
        if self.ownerId:
            self.accept(self.closetSphereEnterEvent, self.handleEnterSphere)

    def exitReady(self):
        pass

    def enterOpen(self):
        if self.ownerId:
            self.ignore(self.closetSphereEnterEvent)
            self._openDoors()
            if self.customerId == base.localAvatar.doId:
                camera.wrtReparentTo(self)
                quat = Quat()
                quat.setHpr((286.3, 336.8, 0))
                self.lerpCameraSeq = camera.posQuatInterval(1, Point3(-7.58, -6.02, 6.9), quat, other=self, blendType='easeOut', name=self.uniqueName('lerpCamera'))
                self.lerpCameraSeq.start()
                camera.setPosHpr(self, -7.58, -6.02, 6.9, 286.3, 336.8, 0)
            if self.av:
                if self.avMoveTrack:
                    self.avMoveTrack.finish()
                self.av.stopSmooth()
                self.avMoveTrack = Sequence(Parallel(Func(self.av.play, 'walk'), LerpPosHprInterval(nodePath=self.av, other=self, duration=1.0, pos=Vec3(1.67, -3.29, 0.025), hpr=Vec3(112, 0, 0), blendType='easeOut')), Func(self.av.loop, 'neutral'), Func(self.av.startSmooth))
                self.avMoveTrack.start()

    def exitOpen(self):
        if self.ownerId:
            self._closeDoors()

    def enterClosed(self):
        if self.ownerId:
            self.accept(self.closetSphereEnterEvent, self.handleEnterSphere)

    def exitClosed(self):
        pass

    def handleEnterSphere(self, collEntry):
        if self.smoothStarted:
            return
        if base.localAvatar.doId == self.lastAvId and globalClock.getFrameTime() <= self.lastTime + 0.5:
            self.notify.info('Ignoring duplicate entry for avatar.')
            return
        if self.hasLocalAvatar:
            self.freeAvatar()
        self.notify.debug('Entering Closet Sphere....%s' % self.closetSphereEnterEvent)
        if self.cr.playGame.getPlace() == None:
            self.notify.info('Not opening closet before place is defined.')
            return
        self.ignore(self.closetSphereEnterEvent)
        if not self.locked:
            self.cr.playGame.getPlace().fsm.request('closet')
            self.accept('closetAsleep', self._handleCancel)
            self.sendUpdate('enterAvatar', [])
            self.hasLocalAvatar = 1
        return

    def setState(self, mode, avId, ownerId, gender, topList, botList):
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
                if base.localAvatar.getDoId() == self.customerId:
                    self.gender = self.av.style.gender
                    self.topList = topList
                    self.botList = botList
                    self.oldTopList = self.topList[0:]
                    self.oldBotList = self.botList[0:]
                    print('-----------Starting closet interaction-----------')
                    self.printInfo()
                    print('-------------------------------------------------')
                    if not self.isOwner:
                        self.__popupNotOwnerPanel()
                    else:
                        taskMgr.doMethodLater(0.5, self.popupChangeClothesGUI, self.uniqueName('popupChangeClothesGUI'))
                self.fsm.request('open')
        return

    def _revertGender(self):
        if self.gender:
            self.av.style.gender = self.gender
            self.av.loop('neutral')

    def popupChangeClothesGUI(self, task):
        self.notify.debug('popupChangeClothesGUI')
        self.purchaseDoneEvent = self.uniqueName('purchaseDone')
        self.swapEvent = self.uniqueName('swap')
        self.cancelEvent = self.uniqueName('cancel')
        self.accept(self.purchaseDoneEvent, self.__proceedToCheckout)
        self.accept(self.swapEvent, self.__handleSwap)
        self.accept(self.cancelEvent, self._handleCancel)
        self.deleteEvent = self.uniqueName('delete')
        if self.isOwner:
            self.accept(self.deleteEvent, self.__handleDelete)
        if not self.closetGUI:
            self.closetGUI = ClosetGUI.ClosetGUI(self.isOwner, self.purchaseDoneEvent, self.cancelEvent, self.swapEvent, self.deleteEvent, self.topList, self.botList)
            self.closetGUI.load()
            if self.gender != self.ownerGender:
                self.closetGUI.setGender(self.ownerGender)
            self.closetGUI.enter(base.localAvatar)
            self.closetGUI.showButtons()
            style = self.av.getStyle()
            self.oldStyle = ToonDNA.ToonDNA()
            self.oldStyle.makeFromNetString(style.makeNetString())
        return Task.done

    def resetCloset(self):
        self.ignoreAll()
        taskMgr.remove(self.uniqueName('popupChangeClothesGUI'))
        if self.lerpCameraSeq:
            self.lerpCameraSeq.finish()
            self.lerpCameraSeq = None
        taskMgr.remove(self.uniqueName('lerpToon'))
        if self.closetGUI:
            self.closetGUI.hideButtons()
            self.closetGUI.exit()
            self.closetGUI.unload()
            self.closetGUI = None
            del self.av
        self.av = base.localAvatar
        style = self.av.getStyle()
        self.oldStyle = ToonDNA.ToonDNA()
        self.oldStyle.makeFromNetString(style.makeNetString())
        self.topDeleted = 0
        self.bottomDeleted = 0
        return Task.done

    def __handleButton(self):
        messenger.send('next')

    def _handleCancel(self):
        if self.oldStyle:
            self.d_setDNA(self.oldStyle.makeNetString(), 1)
        else:
            self.notify.info('avoided crash in handleCancel')
            self._handlePurchaseDone()
        if self.closetGUI:
            self.closetGUI.resetClothes(self.oldStyle)
        if self.popupInfo != None:
            self.popupInfo.destroy()
            self.popupInfo = None
        return

    def __handleSwap(self):
        self.d_setDNA(self.av.getStyle().makeNetString(), 0)

    def __handleDelete(self, t_or_b):
        if t_or_b == ClosetGlobals.SHIRT:
            itemList = self.closetGUI.tops
            trashIndex = self.closetGUI.topChoice
            swapFunc = self.closetGUI.swapTop
            removeFunc = self.closetGUI.removeTop
            self.topDeleted = self.topDeleted | 1

            def setItemChoice(i):
                self.closetGUI.topChoice = i

        else:
            itemList = self.closetGUI.bottoms
            trashIndex = self.closetGUI.bottomChoice
            swapFunc = self.closetGUI.swapBottom
            removeFunc = self.closetGUI.removeBottom
            self.bottomDeleted = self.bottomDeleted | 1

            def setItemChoice(i):
                self.closetGUI.bottomChoice = i

        if len(itemList) > 1:
            trashDNA = ToonDNA.ToonDNA()
            trashItem = self.av.getStyle().makeNetString()
            trashDNA.makeFromNetString(trashItem)
            if trashIndex == 0:
                swapFunc(1)
            else:
                swapFunc(-1)
            removeFunc(trashIndex)
            self.sendUpdate('removeItem', [trashItem, t_or_b])
            swapFunc(0)
            self.closetGUI.updateTrashButtons()
        else:
            self.notify.warning("cant delete this item(type = %s), since we don't have a replacement" % t_or_b)

    def resetItemLists(self):
        self.topList = self.oldTopList[0:]
        self.botList = self.oldBotList[0:]
        self.closetGUI.tops = self.topList
        self.closetGUI.bottoms = self.botList
        self.topDeleted = 0
        self.bottomDeleted = 0

    def __proceedToCheckout(self):
        if self.topDeleted or self.bottomDeleted:
            self.__popupAreYouSurePanel()
        else:
            self._handlePurchaseDone()

    def _handlePurchaseDone(self, timeout = 0):
        if timeout == 1:
            self.d_setDNA(self.oldStyle.makeNetString(), 1)
        else:
            which = 0
            if hasattr(self.closetGUI, 'topChoice') and hasattr(self.closetGUI, 'bottomChoice'):
                if self.closetGUI.topChoice != 0 or self.topDeleted:
                    which = which | 1
                if self.closetGUI.bottomChoice != 0 or self.bottomDeleted:
                    which = which | 2
            self.d_setDNA(self.av.getStyle().makeNetString(), 2, which)

    def d_setDNA(self, dnaString, finished, whichItems = 3):
        self.sendUpdate('setDNA', [dnaString, finished, whichItems])

    def setCustomerDNA(self, avId, dnaString):
        if avId and avId != base.localAvatar.doId:
            av = base.cr.doId2do.get(avId, None)
            if av:
                if self.av == base.cr.doId2do[avId]:
                    oldTorso = self.av.style.torso
                    self.av.style.makeFromNetString(dnaString)
                    if len(oldTorso) == 2 and len(self.av.style.torso) == 2 and self.av.style.torso[1] != oldTorso[1]:
                        self.av.swapToonTorso(self.av.style.torso, genClothes=0)
                        self.av.loop('neutral', 0)
                    self.av.generateToonClothes()
        return

    def printInfo(self):
        print('avid: %s, gender: %s' % (self.av.doId, self.av.style.gender))
        print('current top = %s,%s,%s,%s and  bot = %s,%s,' % (self.av.style.topTex,
         self.av.style.topTexColor,
         self.av.style.sleeveTex,
         self.av.style.sleeveTexColor,
         self.av.style.botTex,
         self.av.style.botTexColor))
        print('topsList = %s' % self.av.getClothesTopsList())
        print('bottomsList = %s' % self.av.getClothesBottomsList())

    def setMovie(self, mode, avId, timestamp):
        self.isLocalToon = avId == base.localAvatar.doId
        if avId != 0:
            self.lastAvId = avId
        self.lastTime = globalClock.getFrameTime()
        if mode == ClosetGlobals.CLOSET_MOVIE_CLEAR:
            return
        elif mode == ClosetGlobals.CLOSET_MOVIE_COMPLETE:
            if self.isLocalToon:
                self._revertGender()
                print('-----------ending trunk interaction-----------')
                self.printInfo()
                print('-------------------------------------------------')
                self.resetCloset()
                self.freeAvatar()
                return
        elif mode == ClosetGlobals.CLOSET_MOVIE_TIMEOUT:
            if self.lerpCameraSeq:
                self.lerpCameraSeq.finish()
                self.lerpCameraSeq = None
            taskMgr.remove(self.uniqueName('lerpToon'))
            if self.isLocalToon:
                self.ignore(self.purchaseDoneEvent)
                self.ignore(self.swapEvent)
                if self.closetGUI:
                    self.closetGUI.resetClothes(self.oldStyle)
                    self._handlePurchaseDone(timeout=1)
                    self.resetCloset()
                self._popupTimeoutPanel()
                self.freeAvatar()

    def freeAvatar(self):
        self.notify.debug('freeAvatar()')
        if self.hasLocalAvatar:
            base.localAvatar.posCamera(0, 0)
            place = base.cr.playGame.getPlace()
            if place:
                place.setState('walk')
            self.ignore('closetAsleep')
            base.localAvatar.startLookAround()
            self.hasLocalAvatar = 0
        self.lastTime = globalClock.getFrameTime()

    def setOwnerId(self, avId):
        self.ownerId = avId

    def _popupTimeoutPanel(self):
        if self.popupInfo != None:
            self.popupInfo.destroy()
            self.popupInfo = None
        buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
        okButtonImage = (buttons.find('**/ChtBx_OKBtn_UP'), buttons.find('**/ChtBx_OKBtn_DN'), buttons.find('**/ChtBx_OKBtn_Rllvr'))
        self.popupInfo = DirectFrame(parent=hidden, relief=None, state='normal', text=TTLocalizer.ClosetTimeoutMessage, frameSize=(-1, 1, -1, 1), geom=DGG.getDefaultDialogGeom(), geom_color=ToontownGlobals.GlobalDialogColor, geom_scale=(0.88, 1, 0.45), geom_pos=(0, 0, -.08), text_scale=0.08)
        DirectButton(self.popupInfo, image=okButtonImage, relief=None, text=TTLocalizer.ClosetPopupOK, text_scale=0.05, text_pos=(0.0, -0.1), textMayChange=0, pos=(0.0, 0.0, -0.16), command=self.__handleTimeoutMessageOK)
        buttons.removeNode()
        self.popupInfo.reparentTo(aspect2d)
        return

    def __handleTimeoutMessageOK(self):
        self.popupInfo.reparentTo(hidden)

    def __popupNotOwnerPanel(self):
        if self.popupInfo != None:
            self.popupInfo.destroy()
            self.popupInfo = None
        self.purchaseDoneEvent = self.uniqueName('purchaseDone')
        self.swapEvent = self.uniqueName('swap')
        self.cancelEvent = self.uniqueName('cancel')
        self.accept(self.purchaseDoneEvent, self.__proceedToCheckout)
        self.accept(self.swapEvent, self.__handleSwap)
        self.accept(self.cancelEvent, self._handleCancel)
        self.deleteEvent = self.uniqueName('delete')
        if self.isOwner:
            self.accept(self.deleteEvent, self.__handleDelete)
        buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
        okButtonImage = (buttons.find('**/ChtBx_OKBtn_UP'), buttons.find('**/ChtBx_OKBtn_DN'), buttons.find('**/ChtBx_OKBtn_Rllvr'))
        self.popupInfo = DirectFrame(parent=hidden, relief=None, state='normal', text=TTLocalizer.ClosetNotOwnerMessage, frameSize=(-1, 1, -1, 1), text_wordwrap=10, geom=DGG.getDefaultDialogGeom(), geom_color=ToontownGlobals.GlobalDialogColor, geom_scale=(0.88, 1, 0.55), geom_pos=(0, 0, -.08), text_scale=0.08, text_pos=(0, 0.06))
        DirectButton(self.popupInfo, image=okButtonImage, relief=None, text=TTLocalizer.ClosetPopupOK, text_scale=0.05, text_pos=(0.0, -0.1), textMayChange=0, pos=(0.0, 0.0, -0.21), command=self._handleNotOwnerMessageOK)
        buttons.removeNode()
        self.popupInfo.reparentTo(aspect2d)
        return

    def _handleNotOwnerMessageOK(self):
        self.popupInfo.reparentTo(hidden)
        taskMgr.doMethodLater(0.1, self.popupChangeClothesGUI, self.uniqueName('popupChangeClothesGUI'))

    def __popupAreYouSurePanel(self):
        if self.popupInfo != None:
            self.popupInfo.destroy()
            self.popupInfo = None
        buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
        okButtonImage = (buttons.find('**/ChtBx_OKBtn_UP'), buttons.find('**/ChtBx_OKBtn_DN'), buttons.find('**/ChtBx_OKBtn_Rllvr'))
        cancelButtonImage = (buttons.find('**/CloseBtn_UP'), buttons.find('**/CloseBtn_DN'), buttons.find('**/CloseBtn_Rllvr'))
        self.popupInfo = DirectFrame(parent=hidden, relief=None, state='normal', text=TTLocalizer.ClosetAreYouSureMessage, frameSize=(-1, 1, -1, 1), text_wordwrap=10, geom=DGG.getDefaultDialogGeom(), geom_color=ToontownGlobals.GlobalDialogColor, geom_scale=(0.88, 1, 0.55), geom_pos=(0, 0, -.08), text_scale=0.08, text_pos=(0, 0.08))
        DirectButton(self.popupInfo, image=okButtonImage, relief=None, text=TTLocalizer.ClosetPopupOK, text_scale=0.05, text_pos=(0.0, -0.1), textMayChange=0, pos=(-0.1, 0.0, -0.21), command=self._handleYesImSure)
        DirectButton(self.popupInfo, image=cancelButtonImage, relief=None, text=TTLocalizer.ClosetPopupCancel, text_scale=0.05, text_pos=(0.0, -0.1), textMayChange=0, pos=(0.1, 0.0, -0.21), command=self._handleNotSure)
        buttons.removeNode()
        self.popupInfo.reparentTo(aspect2d)
        return

    def _handleYesImSure(self):
        self.popupInfo.reparentTo(hidden)
        self._handlePurchaseDone()

    def _handleNotSure(self):
        self.popupInfo.reparentTo(hidden)

    def _openDoors(self):
        if self.closetTrack:
            self.closetTrack.finish()
        leftHpr = Vec3(-110, 0, 0)
        rightHpr = Vec3(110, 0, 0)
        self.closetTrack = Parallel()
        if self.rightDoor:
            self.closetTrack.append(self.rightDoor.hprInterval(0.5, rightHpr))
        if self.leftDoor:
            self.closetTrack.append(self.leftDoor.hprInterval(0.5, leftHpr))
        self.closetTrack.start()

    def _closeDoors(self):
        if self.closetTrack:
            self.closetTrack.finish()
        leftHpr = Vec3(0, 0, 0)
        rightHpr = Vec3(0, 0, 0)
        self.closetTrack = Parallel()
        if self.rightDoor:
            self.closetTrack.append(self.rightDoor.hprInterval(0.5, rightHpr))
        if self.leftDoor:
            self.closetTrack.append(self.leftDoor.hprInterval(0.5, leftHpr))
        self.closetTrack.start()
