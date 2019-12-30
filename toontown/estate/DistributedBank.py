from direct.gui.DirectGui import *
from pandac.PandaModules import *
from toontown.toonbase.ToontownGlobals import *
from toontown.toonbase.ToonBaseGlobal import *
from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *
from direct.distributed.ClockDelta import *
from toontown.toonbase import ToontownGlobals
from . import DistributedFurnitureItem
from toontown.toonbase import TTLocalizer
from . import BankGUI
from .BankGlobals import *
from toontown.toontowngui import TTDialog
from toontown.catalog.CatalogFurnitureItem import FurnitureTypes
from toontown.catalog.CatalogFurnitureItem import FTScale

class DistributedBank(DistributedFurnitureItem.DistributedFurnitureItem):
    notify = directNotify.newCategory('DistributedBank')

    def __init__(self, cr):
        DistributedFurnitureItem.DistributedFurnitureItem.__init__(self, cr)
        self.bankGui = None
        self.bankTrack = None
        self.bankDialog = None
        self.hasLocalAvatar = 0
        self.hasJarOut = 0
        self.jarLods = []
        return

    def generate(self):
        DistributedFurnitureItem.DistributedFurnitureItem.generate(self)
        self.bankSphereEvent = 'bankSphere'
        self.bankSphereEnterEvent = 'enter' + self.bankSphereEvent
        self.bankSphereExitEvent = 'exit' + self.bankSphereEvent
        self.bankGuiDoneEvent = 'bankGuiDone'

    def announceGenerate(self):
        self.notify.debug('announceGenerate')
        DistributedFurnitureItem.DistributedFurnitureItem.announceGenerate(self)
        self.accept(self.bankSphereEnterEvent, self.__handleEnterSphere)

    def loadModel(self):
        model = DistributedFurnitureItem.DistributedFurnitureItem.loadModel(self)
        bowl = model.find('**/bowl')
        if bowl:
            bowl.setBin('fixed', 40)
        return model

    def disable(self):
        self.notify.debug('disable')
        self.ignore(self.bankSphereEnterEvent)
        self.ignore(self.bankSphereExitEvent)
        self.ignore(self.bankGuiDoneEvent)
        if self.bankTrack:
            self.bankTrack.pause()
            self.bankTrack = None
        if self.bankGui:
            self.bankGui.destroy()
            self.bankGui = None
        if self.bankDialog:
            self.bankDialog.cleanup()
            self.bankDialog = None
        if self.hasLocalAvatar:
            self.freeAvatar()
        self.__removeToonJar()
        self.ignoreAll()
        DistributedFurnitureItem.DistributedFurnitureItem.disable(self)
        return

    def delete(self):
        self.notify.debug('delete')
        DistributedFurnitureItem.DistributedFurnitureItem.delete(self)

    def __handleEnterSphere(self, collEntry):
        if self.smoothStarted:
            return
        if self.hasLocalAvatar:
            self.freeAvatar()
        self.notify.debug('Entering Bank Sphere....')
        self.acceptOnce(self.bankSphereExitEvent, self.__handleExitSphere)
        self.ignore(self.bankSphereEnterEvent)
        self.cr.playGame.getPlace().fsm.request('banking')
        self.hasLocalAvatar = 1
        self.sendUpdate('avatarEnter', [])

    def __handleExitSphere(self, collEntry):
        self.notify.debug('Exiting Bank Sphere....')
        if self.bankTrack is not None:
            self.bankTrack.pause()
            self.bankTrack = None
        if self.bankDialog is not None:
            self.bankDialog.cleanup()
            self.bankDialog = None
        self.__handleBankDone(0)
        return

    def __handleBankDone(self, transactionAmount):
        self.notify.debug('__handleBankDone(transactionAmount=%s' % (transactionAmount,))
        self.sendUpdate('transferMoney', [transactionAmount])
        self.ignore(self.bankGuiDoneEvent)
        self.ignore(self.bankSphereExitEvent)
        if self.bankGui is not None:
            self.bankGui.destroy()
            self.bankGui = None
        return

    def freeAvatar(self):
        self.notify.debug('freeAvatar()')
        if self.hasLocalAvatar:
            base.localAvatar.posCamera(0, 0)
            if base.cr.playGame.place != None:
                base.cr.playGame.getPlace().setState('walk')
            self.hasLocalAvatar = 0
        self.accept(self.bankSphereEnterEvent, self.__handleEnterSphere)
        return

    def showBankGui(self):
        if self.bankGui:
            self.bankGui.destroy()
        self.bankGui = BankGUI.BankGui(self.bankGuiDoneEvent)
        self.accept(self.bankGuiDoneEvent, self.__handleBankDone)

    def setMovie(self, mode, avId, timestamp):
        self.notify.debug('setMovie(mode=%s, avId=%s, timestamp=%s)' % (mode, avId, timestamp))
        timeStamp = globalClockDelta.localElapsedTime(timestamp)
        isLocalToon = avId == base.localAvatar.doId
        self.notify.info('setMovie: mode=%s, avId=%s, timeStamp=%s, isLocalToon=%s' % (mode,
         avId,
         timeStamp,
         isLocalToon))
        if mode == BANK_MOVIE_CLEAR:
            self.notify.debug('setMovie: clear')
        elif mode == BANK_MOVIE_GUI:
            self.notify.debug('setMovie: gui')
            track = Sequence()
            track.append(Func(self.__takeOutToonJar, avId))
            if isLocalToon:
                track.append(Wait(3.0))
                track.append(Func(self.showBankGui))
            track.start()
            self.bankTrack = track
        elif mode == BANK_MOVIE_DEPOSIT:
            self.notify.debug('setMovie: deposit')
            self.__putAwayToonJar(avId)
        elif mode == BANK_MOVIE_WITHDRAW:
            self.notify.debug('setMovie: withdraw')
            self.__putAwayToonJar(avId)
        elif mode == BANK_MOVIE_NO_OP:
            self.notify.debug('setMovie: no op')
            self.__putAwayToonJar(avId)
        elif mode == BANK_MOVIE_NOT_OWNER:
            self.notify.debug('setMovie: not owner')
            if isLocalToon:
                self.bankDialog = TTDialog.TTDialog(dialogName='BankNotOwner', style=TTDialog.Acknowledge, text=TTLocalizer.DistributedBankNotOwner, text_wordwrap=15, fadeScreen=1, command=self.__clearDialog)
        elif mode == BANK_MOVIE_NO_OWNER:
            self.notify.debug('setMovie: no owner')
            if isLocalToon:
                self.bankDialog = TTDialog.TTDialog(dialogName='BankNoOwner', style=TTDialog.Acknowledge, text=TTLocalizer.DistributedBankNoOwner, text_wordwrap=15, fadeScreen=1, command=self.__clearDialog)
        else:
            self.notify.warning('unknown mode in setMovie: %s' % mode)

    def __clearDialog(self, event):
        self.notify.debug('__clearDialog(event=%s)' % (event,))
        if self.bankDialog is not None:
            self.bankDialog.cleanup()
            self.bankDialog = None
        self.freeAvatar()
        return

    def __attachToonJar(self, toon):
        self.__removeToonJar()
        for hand in toon.getRightHands():
            self.jarLods.append(toon.jar.instanceTo(hand))

    def __removeToonJar(self):
        for jar in self.jarLods:
            jar.removeNode()

        self.jarLods = []

    def __takeOutToonJar(self, avId):
        self.notify.debug('__takeOutToonJar(avId=%s)' % (avId,))
        toon = base.cr.doId2do.get(avId)
        if toon == None:
            return
        track = Sequence()
        index = self.item.furnitureType
        scale = FurnitureTypes[index][FTScale]
        walkToBank = Sequence(Func(toon.stopSmooth), Func(toon.loop, 'walk'), toon.posHprInterval(0.5, Point3(0, -3.125 * (scale + 0.2), 0), Point3(0, 0, 0), other=self, blendType='easeInOut'), Func(toon.loop, 'neutral'), Func(toon.startSmooth))
        track.append(walkToBank)
        if not toon.jar:
            toon.getJar()
        self.__attachToonJar(toon)
        jarAndBank = Parallel(LerpScaleInterval(toon.jar, 1.5, 1.0, blendType='easeOut'), ActorInterval(base.cr.doId2do[avId], 'bank', endTime=3.8))
        track.append(jarAndBank)
        track.append(Func(base.cr.doId2do[avId].pingpong, 'bank', fromFrame=48, toFrame=92))
        track.start()
        self.hasJarOut = 1
        return

    def __putAwayToonJar(self, avId):
        self.notify.debug('__putAwayToonJar(avId=%s)' % (avId,))
        toon = base.cr.doId2do.get(avId)
        if toon is None:
            return
        if not self.hasJarOut:
            return
        self.hasJarOut = 0
        if not toon.jar:
            toon.getJar()
        track = Sequence()
        jarAndBank = Parallel(ActorInterval(base.cr.doId2do[avId], 'bank', startTime=2.0, endTime=0.0), LerpScaleInterval(toon.jar, 2.0, 0.0, blendType='easeIn'))
        track.append(jarAndBank)
        track.append(Func(self.__removeToonJar))
        track.append(Func(toon.removeJar))
        track.append(Func(toon.loop, 'neutral'))
        if avId == base.localAvatar.doId:
            track.append(Func(self.freeAvatar))
        track.start()
        self.bankTrack = track
        return
