from DistributedMinigameAI import *
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from toontown.minigame import PlayingCardGlobals
from toontown.minigame import PlayingCard
from toontown.minigame.PlayingCard import PlayingCardBase
from toontown.minigame import PlayingCardDeck
from toontown.minigame import PairingGameGlobals
from toontown.ai.ToonBarrier import ToonBarrier

class DistributedPairingGameAI(DistributedMinigameAI):
    notify = directNotify.newCategory('DistributedPairingGameAI')
    OneCardInMultiplayer = True
    TurnDownTwoAtATime = True

    def __init__(self, air, minigameId):
        try:
            self.DistributedPairingGameAI_initialized
        except:
            self.DistributedPairingGameAI_initialized = 1
            DistributedMinigameAI.__init__(self, air, minigameId)
            self.gameFSM = ClassicFSM.ClassicFSM('DistributedPairingGameAI', [State.State('inactive', self.enterInactive, self.exitInactive, ['play']), State.State('play', self.enterPlay, self.exitPlay, ['cleanup']), State.State('cleanup', self.enterCleanup, self.exitCleanup, ['inactive'])], 'inactive', 'inactive')
            self.addChildGameFSM(self.gameFSM)
            self.gameFSM.enterInitialState()
            self.deckSeed = random.randint(0, 4000000)
            self.faceUpDict = {}
            self.inactiveList = []
            self.maxOpenCards = 2
            self.points = 0
            self.flips = 0
            self.matches = 0
            self.cards = []
            self.gameDuration = 90

    def generate(self):
        self.notify.debug('generate')
        DistributedMinigameAI.generate(self)

    def delete(self):
        self.notify.debug('delete')
        del self.gameFSM
        DistributedMinigameAI.delete(self)

    def setGameReady(self):
        self.notify.debug('setGameReady')
        if self.OneCardInMultiplayer and len(self.avIdList) > 1:
            self.maxOpenCards = 1
        self.sendUpdate('setMaxOpenCards', [self.maxOpenCards])
        DistributedMinigameAI.setGameReady(self)
        for avId in self.avIdList:
            self.faceUpDict[avId] = []

        self.deck = PairingGameGlobals.createDeck(self.deckSeed, self.numPlayers)
        for index in xrange(len(self.deck.cards)):
            cardValue = self.deck.cards[index]
            oneCard = PlayingCardBase(cardValue)
            self.cards.append(oneCard)

    def setGameStart(self, timestamp):
        self.notify.debug('setGameStart')
        DistributedMinigameAI.setGameStart(self, timestamp)
        self.gameFSM.request('play')

    def setGameAbort(self):
        self.notify.debug('setGameAbort')
        if self.gameFSM.getCurrentState():
            self.gameFSM.request('cleanup')
        DistributedMinigameAI.setGameAbort(self)

    def calcLowFlipBonus(self):
        lowFlipModifier = PairingGameGlobals.calcLowFlipModifier(self.matches, self.flips)
        bonus = lowFlipModifier * self.matches
        self.notify.debug('low flip bonus = %d' % bonus)
        return bonus

    def gameOver(self):
        self.notify.debug('gameOver')
        lowFlipBonus = 0
        for avId in self.avIdList:
            self.scoreDict[avId] = max(1, self.points)
            lowFlipBonus = self.calcLowFlipBonus()
            self.scoreDict[avId] += lowFlipBonus
            if self.matches == len(self.cards) / 2:
                self.scoreDict[avId] += round(len(self.cards) / 4.0)
                self.logAllPerfect()

        logAvId = self.avIdList[0]
        self.air.writeServerEvent('minigame_pairing', self.doId, '%s|%s|%s|%s|%s|%s|%s|%s' % (ToontownGlobals.PairingGameId,
         self.getSafezoneId(),
         self.avIdList,
         self.scoreDict[logAvId],
         self.gameDuration,
         self.matches,
         self.flips,
         lowFlipBonus))
        self.gameFSM.request('cleanup')
        DistributedMinigameAI.gameOver(self)

    def enterInactive(self):
        self.notify.debug('enterInactive')

    def exitInactive(self):
        pass

    def enterPlay(self):
        self.notify.debug('enterPlay')

        def allToonsDone(self = self):
            self.notify.debug('allToonsDone')
            self.sendUpdate('setEveryoneDone')
            if not PairingGameGlobals.EndlessGame:
                self.gameOver()

        def handleTimeout(avIds, self = self):
            self.notify.debug('handleTimeout: avatars %s did not report "done"' % avIds)
            self.setGameAbort()

        self.gameDuration = PairingGameGlobals.calcGameDuration(self.getDifficulty())
        self.doneBarrier = ToonBarrier('waitClientsDone', self.uniqueName('waitClientsDone'), self.avIdList, self.gameDuration + MinigameGlobals.latencyTolerance, allToonsDone, handleTimeout)

    def exitPlay(self):
        self.doneBarrier.cleanup()
        del self.doneBarrier

    def enterCleanup(self):
        self.notify.debug('enterCleanup')
        self.gameFSM.request('inactive')

    def exitCleanup(self):
        pass

    def getDeckSeed(self):
        return self.deckSeed

    def isCardFaceUp(self, deckOrderIndex):
        retval = False
        for key in self.faceUpDict.keys():
            if deckOrderIndex in self.faceUpDict[key]:
                retval = True
                break

        return retval

    def isCardFaceDown(self, deckOrderIndex):
        return not self.isCardFaceUp(deckOrderIndex)

    def checkForMatch(self):
        faceUpList = []
        for oneToonFaceUpList in self.faceUpDict.values():
            faceUpList += oneToonFaceUpList

        for i in range(len(faceUpList)):
            cardA = faceUpList[i]
            for j in range(i + 1, len(faceUpList)):
                cardB = faceUpList[j]
                if self.cards[cardA].rank == self.cards[cardB].rank:
                    return (cardA, cardB)

        return (-1, -1)

    def handleMatch(self, cardA, cardB):
        self.notify.debug('we got a match %d %d' % (cardA, cardB))
        for key in self.faceUpDict.keys():
            if cardA in self.faceUpDict[key]:
                self.faceUpDict[key].remove(cardA)
            if cardB in self.faceUpDict[key]:
                self.faceUpDict[key].remove(cardB)

        self.inactiveList.append(cardA)
        self.inactiveList.append(cardB)

    def turnDownCard(self, cardA):
        self.notify.debug('turning down card %d' % cardA)
        for key in self.faceUpDict.keys():
            if cardA in self.faceUpDict[key]:
                self.faceUpDict[key].remove(cardA)

    def openCardRequest(self, deckOrderIndex, bonusGlowCard):
        if self.isCardFaceUp(deckOrderIndex):
            return
        if self.gameFSM.getCurrentState().getName() != 'play':
            return
        avId = self.air.getAvatarIdFromSender()
        if avId not in self.avIdList:
            self.air.writeServerEvent('suspicious', avId, 'openCardRequest from non-player av %s' % avId)
            return
        if deckOrderIndex < 0 or deckOrderIndex >= len(self.cards):
            self.logSuspicious(avId, 'openCardRequest: invalid deckOrderIndex: %s' % deckOrderIndex)
            return
        if bonusGlowCard < 0 or bonusGlowCard >= len(self.cards):
            self.logSuspicious(avId, 'openCardRequest: invalid bonusGlowCard: %s' % bonusGlowCard)
            return
        cardsToTurnDown = []
        faceUpList = self.faceUpDict[avId]
        numCardsFaceUpAtStart = len(faceUpList)
        if len(faceUpList) >= self.maxOpenCards:
            oldestCard = faceUpList.pop(0)
            cardsToTurnDown.append(oldestCard)
        if self.TurnDownTwoAtATime and numCardsFaceUpAtStart == 2:
            secondOldestCard = faceUpList.pop(0)
            cardsToTurnDown.append(secondOldestCard)
        cardToTurnUp = deckOrderIndex
        self.faceUpDict[avId].append(cardToTurnUp)
        cardA, cardB = self.checkForMatch()
        matchingCard = -1
        if cardA > -1:
            self.handleMatch(cardA, cardB)
            if cardA == deckOrderIndex:
                matchingCard = cardB
            else:
                matchingCard = cardA
            pointsToGive = 1
            if bonusGlowCard in [cardA, cardB]:
                pointsToGive += 1
            self.points += pointsToGive
            self.matches += 1
        self.flips += 1
        self.sendUpdate('openCardResult', [cardToTurnUp,
         avId,
         matchingCard,
         self.points,
         cardsToTurnDown])

    def reportDone(self):
        if self.gameFSM.getCurrentState().getName() != 'play':
            return
        avId = self.air.getAvatarIdFromSender()
        self.notify.debug('reportDone: avatar %s is done' % avId)
        self.doneBarrier.clear(avId)
