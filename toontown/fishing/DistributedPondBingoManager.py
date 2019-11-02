from direct.distributed import DistributedObject
from direct.distributed.ClockDelta import *
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import FSM
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from direct.task import Task
from toontown.fishing import BingoGlobals
from toontown.fishing import BingoCardGui
from toontown.fishing import FishGlobals
from toontown.fishing import NormalBingo
from toontown.fishing import FourCornerBingo
from toontown.fishing import DiagonalBingo
from toontown.fishing import ThreewayBingo
from toontown.fishing import BlockoutBingo
from direct.showbase import RandomNumGen
from toontown.toonbase import ToontownTimer
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
import time

class DistributedPondBingoManager(DistributedObject.DistributedObject, FSM.FSM):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedPondBingoManager')
    cardTypeDict = {BingoGlobals.NORMAL_CARD: NormalBingo.NormalBingo,
     BingoGlobals.FOURCORNER_CARD: FourCornerBingo.FourCornerBingo,
     BingoGlobals.DIAGONAL_CARD: DiagonalBingo.DiagonalBingo,
     BingoGlobals.THREEWAY_CARD: ThreewayBingo.ThreewayBingo,
     BingoGlobals.BLOCKOUT_CARD: BlockoutBingo.BlockoutBingo}

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        FSM.FSM.__init__(self, 'DistributedPondBingoManager')
        self.cardId = 0
        self.jackpot = 0
        self.pond = None
        self.spot = None
        self.card = None
        self.hasEntered = 0
        self.initGameState = None
        self.lastCatch = None
        self.typeId = BingoGlobals.NORMAL_CARD
        return

    def generate(self):
        DistributedObject.DistributedObject.generate(self)
        self.card = BingoCardGui.BingoCardGui()
        self.card.reparentTo(aspect2d, 1)
        self.card.hideNextGameTimer()
        self.notify.debug('generate: DistributedPondBingoManager')

    def delete(self):
        del self.pond.pondBingoMgr
        self.pond.pondBingoMgr = None
        del self.pond
        self.pond = None
        FSM.FSM.cleanup(self)
        self.card.destroy()
        del self.card
        self.notify.debug('delete: Deleting Local PondManager %s' % self.doId)
        DistributedObject.DistributedObject.delete(self)
        return

    def d_cardUpdate(self, cellId, genus, species):
        self.sendUpdate('cardUpdate', [self.cardId,
         cellId,
         genus,
         species])

    def d_bingoCall(self):
        self.sendUpdate('handleBingoCall', [self.cardId])

    def setCardState(self, cardId, typeId, tileSeed, gameState):
        self.cardId = cardId
        self.typeId = typeId
        self.tileSeed = tileSeed
        self.jackpot = BingoGlobals.getJackpot(typeId)
        self.initGameState = gameState

    def checkForUpdate(self, cellId):
        if self.lastCatch is not None:
            genus = self.lastCatch[0]
            species = self.lastCatch[1]
            self.d_cardUpdate(cellId, genus, species)
            success = self.card.cellUpdateCheck(cellId, genus, species)
            if success == BingoGlobals.WIN:
                self.lastCatch = None
                self.enableBingo()
                self.pond.getLocalToonSpot().cleanupFishPanel()
                self.pond.getLocalToonSpot().hideBootPanel()
            elif success == BingoGlobals.UPDATE:
                self.lastCatch = None
                self.pond.getLocalToonSpot().cleanupFishPanel()
                self.pond.getLocalToonSpot().hideBootPanel()
        else:
            self.notify.warning('CheckForWin: Attempt to Play Cell without a valid catch.')
        return

    def updateGameState(self, gameState, cellId):
        game = self.card.getGame()
        if game is not None:
            game.setGameState(gameState)
            self.card.cellUpdate(cellId)
        return

    def __generateCard(self):
        self.notify.debug('__generateCard: %s' % self.typeId)
        if self.card.getGame():
            self.card.removeGame()
        game = self.__cardChoice()
        game.setGameState(self.initGameState)
        self.card.addGame(game)
        self.card.generateCard(self.tileSeed, self.pond.getArea())
        color = BingoGlobals.getColor(self.typeId)
        self.card.setProp('image_color', VBase4(color[0], color[1], color[2], color[3]))
        color = BingoGlobals.getButtonColor(self.typeId)
        self.card.bingo.setProp('image_color', VBase4(color[0], color[1], color[2], color[3]))
        if self.hasEntered:
            self.card.loadCard()
            self.card.show()
        else:
            self.card.hide()

    def showCard(self):
        if (self.state != 'Off' or self.state != 'CloseEvent') and self.card.getGame():
            self.card.loadCard()
            self.card.show()
        elif self.state == 'GameOver':
            self.card.show()
        elif self.state == 'Reward':
            self.card.show()
        elif self.state == 'WaitCountdown':
            self.card.show()
            self.card.showNextGameTimer(TTLocalizer.FishBingoNextGame)
        elif self.state == 'Intermission':
            self.card.showNextGameTimer(TTLocalizer.FishBingoIntermission)
            self.card.show()
        self.hasEntered = 1

    def __cardChoice(self):
        return self.cardTypeDict.get(self.typeId)()

    def checkForBingo(self):
        success = self.card.checkForBingo()
        if success:
            self.d_bingoCall()
            self.request('Reward')

    def enableBingo(self):
        self.card.setBingo(DGG.NORMAL, self.checkForBingo)

    def setPondDoId(self, pondId):
        self.pond = base.cr.doId2do[pondId]
        self.pond.setPondBingoManager(self)

    def setState(self, state, timeStamp):
        self.notify.debug('State change: %s -> %s' % (self.state, state))
        self.request(state, timeStamp)

    def setLastCatch(self, catch):
        self.lastCatch = catch
        self.card.fishCaught(catch)

    def castingStarted(self):
        if self.card:
            self.card.castingStarted()

    def setSpot(self, spot):
        self.spot = spot

    def setJackpot(self, jackpot):
        self.jackpot = jackpot

    def enterOff(self):
        self.notify.debug('enterOff: Enter Off State')
        del self.spot
        self.spot = None
        if self.card.getGame:
            self.card.removeGame()
        self.card.hide()
        self.card.stopNextGameTimer()
        self.hasEntered = 0
        self.lastCatch = None
        return

    def filterOff(self, request, args):
        if request == 'Intro':
            return 'Intro'
        elif request == 'WaitCountdown':
            return (request, args)
        elif request == 'Playing':
            self.__generateCard()
            self.card.setJackpotText(str(self.jackpot))
            return (request, args)
        elif request == 'Intermission':
            return (request, args)
        elif request == 'GameOver':
            return (request, args)
        elif request == 'Reward':
            return ('GameOver', args)
        else:
            self.notify.debug('filterOff: Invalid State Transition from, Off to %s' % request)

    def exitOff(self):
        self.notify.debug('exitOff: Exit Off State')

    def enterIntro(self, args = None):
        self.notify.debug('enterIntro: Enter Intro State')
        self.pond.setSpotGui()
        self.hasEntered = 1

    def filterIntro(self, request, args):
        if request == 'WaitCountdown':
            return (request, args)
        else:
            self.notify.debug('filterIntro: Invalid State Transition from Intro to %s' % request)

    def exitIntro(self):
        self.notify.debug('exitIntro: Exit Intro State')

    def enterWaitCountdown(self, timeStamp):
        self.notify.debug('enterWaitCountdown: Enter WaitCountdown State')
        time = BingoGlobals.TIMEOUT_SESSION - globalClockDelta.localElapsedTime(timeStamp[0])
        self.card.startNextGameCountdown(time)
        if self.hasEntered:
            self.card.showNextGameTimer(TTLocalizer.FishBingoNextGame)

    def filterWaitCountdown(self, request, args):
        if request == 'Playing':
            return (request, args)
        else:
            self.notify.debug('filterOff: Invalid State Transition from WaitCountdown to %s' % request)

    def exitWaitCountdown(self):
        self.notify.debug('exitWaitCountdown: Exit WaitCountdown State')
        if self.pond:
            self.__generateCard()
            self.card.setJackpotText(str(self.jackpot))
            self.card.resetGameTimer()
            self.card.hideNextGameTimer()

    def enterPlaying(self, timeStamp):
        self.notify.debug('enterPlaying: Enter Playing State')
        self.lastCatch = None
        session = BingoGlobals.getGameTime(self.typeId)
        time = session - globalClockDelta.localElapsedTime(timeStamp[0])
        self.card.startGameCountdown(time)
        self.card.enableCard(self.checkForUpdate)
        return

    def filterPlaying(self, request, args):
        if request == 'Reward':
            return (request, args)
        elif request == 'GameOver':
            return (request, args)
        else:
            self.notify.debug('filterOff: Invalid State Transition from Playing to %s' % request)

    def exitPlaying(self):
        self.notify.debug('exitPlaying: Exit Playing State')
        self.card.resetGameTimer()

    def enterReward(self, timeStamp):
        self.notify.debug('enterReward: Enter Reward State')
        if self.card:
            self.card.setBingo()
            self.card.removeGame()
            self.card.setGameOver(TTLocalizer.FishBingoVictory)
        localToonSpot = self.pond.getLocalToonSpot()
        if localToonSpot:
            localToonSpot.setJarAmount(self.jackpot)
        self.jackpot = 0

    def filterReward(self, request, args):
        if request == 'WaitCountdown':
            return (request, args)
        elif request == 'Intermission':
            return (request, args)
        elif request == 'CloseEvent':
            return 'CloseEvent'
        elif request == 'Off':
            return 'Off'
        else:
            self.notify.debug('filterOff: Invalid State Transition from Reward to %s' % request)

    def exitReward(self):
        self.notify.debug('exitReward: Exit Reward State')
        self.card.setGameOver('')

    def enterGameOver(self, timeStamp):
        self.notify.debug('enterGameOver: Enter GameOver State')
        self.card.setBingo()
        self.card.removeGame()
        self.card.setGameOver(TTLocalizer.FishBingoGameOver)

    def filterGameOver(self, request, args):
        if request == 'WaitCountdown':
            return (request, args)
        elif request == 'Intermission':
            return (request, args)
        elif request == 'CloseEvent':
            return 'CloseEvent'
        elif request == 'Off':
            return 'Off'
        else:
            self.notify.debug('filterOff: Invalid State Transition from GameOver to %s' % request)

    def exitGameOver(self):
        self.notify.debug('exitGameOver: Exit GameOver State')
        self.card.setGameOver('')
        self.card.resetGameTypeText()

    def enterIntermission(self, timeStamp):
        self.notify.debug('enterIntermission: Enter Intermission State')
        if self.hasEntered:
            self.card.showNextGameTimer(TTLocalizer.FishBingoIntermission)
        self.notify.debug('enterIntermission: timestamp %s' % timeStamp[0])
        elapsedTime = globalClockDelta.localElapsedTime(timeStamp[0])
        self.notify.debug('enterIntermission: elapsedTime %s' % elapsedTime)
        waitTime = BingoGlobals.HOUR_BREAK_SESSION - elapsedTime
        self.notify.debug('enterIntermission: waitTime %s' % waitTime)
        self.card.startNextGameCountdown(waitTime)

    def filterIntermission(self, request, args):
        if request == 'WaitCountdown':
            return (request, args)
        elif request == 'Off':
            return 'Off'
        else:
            self.notify.warning('filterOff: Invalid State Transition from GameOver to %s' % request)

    def exitIntermission(self):
        self.notify.debug('enterIntermission: Exit Intermission State')

    def enterCloseEvent(self, timestamp):
        self.notify.debug('enterCloseEvent: Enter CloseEvent State')
        self.card.hide()
        self.pond.resetSpotGui()

    def filterCloseEvent(self, request, args):
        if request == 'Off':
            return 'Off'
        else:
            self.notify.warning('filterOff: Invalid State Transition from GameOver to %s' % request)

    def exitCloseEvent(self):
        self.notify.debug('exitCloseEvent: Exit CloseEvent State')
