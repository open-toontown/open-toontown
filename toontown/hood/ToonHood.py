from pandac.PandaModules import *
from toontown.toonbase.ToonBaseGlobal import *
from toontown.toonbase.ToontownGlobals import *
from toontown.distributed.ToontownMsgTypes import *
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from toontown.minigame import Purchase
from otp.avatar import DistributedAvatar
from . import Hood
from toontown.building import SuitInterior
from toontown.cogdominium import CogdoInterior
from toontown.toon.Toon import teleportDebug

class ToonHood(Hood.Hood):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToonHood')

    def __init__(self, parentFSM, doneEvent, dnaStore, hoodId):
        Hood.Hood.__init__(self, parentFSM, doneEvent, dnaStore, hoodId)
        self.suitInteriorDoneEvent = 'suitInteriorDone'
        self.minigameDoneEvent = 'minigameDone'
        self.safeZoneLoaderClass = None
        self.townLoaderClass = None
        self.fsm = ClassicFSM.ClassicFSM('Hood', [State.State('start', self.enterStart, self.exitStart, ['townLoader', 'safeZoneLoader']),
         State.State('townLoader', self.enterTownLoader, self.exitTownLoader, ['quietZone',
          'safeZoneLoader',
          'suitInterior',
          'cogdoInterior']),
         State.State('safeZoneLoader', self.enterSafeZoneLoader, self.exitSafeZoneLoader, ['quietZone',
          'suitInterior',
          'cogdoInterior',
          'townLoader',
          'minigame']),
         State.State('purchase', self.enterPurchase, self.exitPurchase, ['quietZone', 'minigame', 'safeZoneLoader']),
         State.State('suitInterior', self.enterSuitInterior, self.exitSuitInterior, ['quietZone', 'townLoader', 'safeZoneLoader']),
         State.State('cogdoInterior', self.enterCogdoInterior, self.exitCogdoInterior, ['quietZone', 'townLoader', 'safeZoneLoader']),
         State.State('minigame', self.enterMinigame, self.exitMinigame, ['purchase']),
         State.State('quietZone', self.enterQuietZone, self.exitQuietZone, ['safeZoneLoader',
          'townLoader',
          'suitInterior',
          'cogdoInterior',
          'minigame']),
         State.State('final', self.enterFinal, self.exitFinal, [])], 'start', 'final')
        self.fsm.enterInitialState()
        return

    def load(self):
        Hood.Hood.load(self)

    def unload(self):
        del self.safeZoneLoaderClass
        del self.townLoaderClass
        Hood.Hood.unload(self)

    def loadLoader(self, requestStatus):
        loaderName = requestStatus['loader']
        if loaderName == 'safeZoneLoader':
            self.loader = self.safeZoneLoaderClass(self, self.fsm.getStateNamed('safeZoneLoader'), self.loaderDoneEvent)
            self.loader.load()
        elif loaderName == 'townLoader':
            self.loader = self.townLoaderClass(self, self.fsm.getStateNamed('townLoader'), self.loaderDoneEvent)
            self.loader.load(requestStatus['zoneId'])

    def enterTownLoader(self, requestStatus):
        teleportDebug(requestStatus, 'ToonHood.enterTownLoader, status=%s' % (requestStatus,))
        self.accept(self.loaderDoneEvent, self.handleTownLoaderDone)
        self.loader.enter(requestStatus)
        self.spawnTitleText(requestStatus['zoneId'])

    def exitTownLoader(self):
        taskMgr.remove('titleText')
        self.hideTitleText()
        self.ignore(self.loaderDoneEvent)
        self.loader.exit()
        self.loader.unload()
        del self.loader

    def handleTownLoaderDone(self):
        doneStatus = self.loader.getDoneStatus()
        teleportDebug(doneStatus, 'handleTownLoaderDone, doneStatus=%s' % (doneStatus,))
        if self.isSameHood(doneStatus):
            teleportDebug(doneStatus, 'same hood')
            self.fsm.request('quietZone', [doneStatus])
        else:
            teleportDebug(doneStatus, 'different hood')
            self.doneStatus = doneStatus
            messenger.send(self.doneEvent)

    def enterPurchase(self, pointsAwarded, playerMoney, playerIds, playerStates, remain, metagameRound = -1, votesArray = None):
        messenger.send('enterSafeZone')
        DistributedAvatar.DistributedAvatar.HpTextEnabled = 0
        base.localAvatar.laffMeter.start()
        self.purchaseDoneEvent = 'purchaseDone'
        self.accept(self.purchaseDoneEvent, self.handlePurchaseDone)
        self.purchase = Purchase.Purchase(base.localAvatar, pointsAwarded, playerMoney, playerIds, playerStates, remain, self.purchaseDoneEvent, metagameRound, votesArray)
        self.purchase.load()
        self.purchase.enter()

    def exitPurchase(self):
        messenger.send('exitSafeZone')
        DistributedAvatar.DistributedAvatar.HpTextEnabled = 1
        base.localAvatar.laffMeter.stop()
        self.ignore(self.purchaseDoneEvent)
        self.purchase.exit()
        self.purchase.unload()
        del self.purchase

    def handlePurchaseDone(self):
        doneStatus = self.purchase.getDoneStatus()
        if doneStatus['where'] == 'playground':
            self.fsm.request('quietZone', [{'loader': 'safeZoneLoader',
              'where': 'playground',
              'how': 'teleportIn',
              'hoodId': self.hoodId,
              'zoneId': self.hoodId,
              'shardId': None,
              'avId': -1}])
        elif doneStatus['loader'] == 'minigame':
            self.fsm.request('minigame')
        else:
            self.notify.error('handlePurchaseDone: unknown mode')
        return

    def enterSuitInterior(self, requestStatus = None):
        self.placeDoneEvent = 'suit-interior-done'
        self.acceptOnce(self.placeDoneEvent, self.handleSuitInteriorDone)
        self.place = SuitInterior.SuitInterior(self, self.fsm, self.placeDoneEvent)
        self.place.load()
        self.place.enter(requestStatus)
        base.cr.playGame.setPlace(self.place)

    def exitSuitInterior(self):
        self.ignore(self.placeDoneEvent)
        del self.placeDoneEvent
        self.place.exit()
        self.place.unload()
        self.place = None
        base.cr.playGame.setPlace(self.place)
        return

    def handleSuitInteriorDone(self):
        doneStatus = self.place.getDoneStatus()
        if self.isSameHood(doneStatus):
            self.fsm.request('quietZone', [doneStatus])
        else:
            self.doneStatus = doneStatus
            messenger.send(self.doneEvent)

    def enterCogdoInterior(self, requestStatus = None):
        self.placeDoneEvent = 'cogdo-interior-done'
        self.acceptOnce(self.placeDoneEvent, self.handleCogdoInteriorDone)
        self.place = CogdoInterior.CogdoInterior(self, self.fsm, self.placeDoneEvent)
        self.place.load()
        self.place.enter(requestStatus)
        base.cr.playGame.setPlace(self.place)

    def exitCogdoInterior(self):
        self.ignore(self.placeDoneEvent)
        del self.placeDoneEvent
        self.place.exit()
        self.place.unload()
        self.place = None
        base.cr.playGame.setPlace(self.place)
        return

    def handleCogdoInteriorDone(self):
        doneStatus = self.place.getDoneStatus()
        if self.isSameHood(doneStatus):
            self.fsm.request('quietZone', [doneStatus])
        else:
            self.doneStatus = doneStatus
            messenger.send(self.doneEvent)

    def enterMinigame(self, ignoredParameter = None):
        messenger.send('enterSafeZone')
        DistributedAvatar.DistributedAvatar.HpTextEnabled = 0
        base.localAvatar.laffMeter.start()
        base.cr.forbidCheesyEffects(1)
        self.acceptOnce(self.minigameDoneEvent, self.handleMinigameDone)
        return None

    def exitMinigame(self):
        messenger.send('exitSafeZone')
        DistributedAvatar.DistributedAvatar.HpTextEnabled = 1
        base.localAvatar.laffMeter.stop()
        base.cr.forbidCheesyEffects(0)
        self.ignore(self.minigameDoneEvent)
        minigameState = self.fsm.getStateNamed('minigame')
        for childFSM in minigameState.getChildren():
            minigameState.removeChild(childFSM)

    def handleMinigameDone(self):
        return None
