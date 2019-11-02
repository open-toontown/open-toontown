from pandac.PandaModules import *
from toontown.toonbase.ToonBaseGlobal import *
from DistributedMinigame import *
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from toontown.toonbase import TTLocalizer, ToontownTimer
from toontown.toonbase import ToontownBattleGlobals
from toontown.minigame import PlayingCardGlobals
from toontown.minigame import PairingGameCard
from toontown.minigame import PlayingCardDeck
from toontown.minigame import PairingGameGlobals
from OrthoWalk import OrthoWalk
from OrthoDrive import OrthoDrive
from direct.interval.IntervalGlobal import Sequence, Parallel, Func, LerpColorScaleInterval, LerpScaleInterval, LerpFunctionInterval, Wait, SoundInterval
from toontown.toonbase.ToontownGlobals import GlobalDialogColor

class DistributedPairingGame(DistributedMinigame):
    TOON_SPEED = 11
    MAX_FRAME_MOVE = 1
    MAX_FACE_UP_CARDS = 2
    notify = directNotify.newCategory('DistributedPairingGame')
    bonusGlowTime = 0.5
    EndGameTaskName = 'endPairingGame'
    xCardInc = 4
    cardsPerRow = 8
    cardsPerCol = 5

    def __init__(self, cr):
        DistributedMinigame.__init__(self, cr)
        self.gameFSM = ClassicFSM.ClassicFSM('DistributedPairingGame', [State.State('off', self.enterOff, self.exitOff, ['play']), State.State('play', self.enterPlay, self.exitPlay, ['cleanup']), State.State('cleanup', self.enterCleanup, self.exitCleanup, [])], 'off', 'cleanup')
        self.addChildGameFSM(self.gameFSM)
        self.cameraTopView = (17.6, 6.18756, 43.9956, 0, -89, 0)
        self.cameraThreeQuarterView = (14.0, -8.93352, 33.4497, 0, -62.89, 0)
        self.deckSeed = 0
        self.faceUpList = []
        self.localFaceUpList = []
        self.inList = []
        self.inactiveList = []
        self.points = 0
        self.flips = 0
        self.matches = 0
        self.yCardInc = 4
        self.startingPositions = [(0, 0, 0, -45),
         ((self.cardsPerRow - 1) * self.xCardInc,
          (self.cardsPerCol - 1) * self.yCardInc,
          0,
          135),
         ((self.cardsPerRow - 1) * self.xCardInc,
          0,
          0,
          45),
         (0,
          (self.cardsPerCol - 1) * self.yCardInc,
          0,
          -135)]
        self.stageMin = Point2(0, 0)
        self.stageMax = Point2((self.cardsPerRow - 1) * self.xCardInc, (self.cardsPerCol - 1) * self.yCardInc)
        self.gameDuration = PairingGameGlobals.EasiestGameDuration

    def moveCameraToTop(self):
        camera.reparentTo(render)
        p = self.cameraThreeQuarterView
        camera.setPosHpr(p[0], p[1], p[2], p[3], p[4], p[5])

    def getTitle(self):
        return TTLocalizer.PairingGameTitle

    def getInstructions(self):
        if self.numPlayers > 1:
            return TTLocalizer.PairingGameInstructionsMulti
        else:
            return TTLocalizer.PairingGameInstructions

    def getMaxDuration(self):
        return 0

    def load(self):
        self.notify.debug('load')
        DistributedMinigame.load(self)
        self.gameDuration = PairingGameGlobals.calcGameDuration(self.getDifficulty())
        self.gameBoard = loader.loadModel('phase_4/models/minigames/memory_room')
        self.gameBoard.setPosHpr(0.5, 0, 0, 0, 0, 0)
        self.gameBoard.setScale(1.0)
        self.deck = PairingGameGlobals.createDeck(self.deckSeed, self.numPlayers)
        self.notify.debug('%s' % self.deck.cards)
        testCard = self.getDeckOrderIndex(self.cardsPerCol - 1, 0)
        if not testCard > -1:
            self.yCardInc *= 1.25
        self.cards = []
        for index in xrange(len(self.deck.cards)):
            cardValue = self.deck.cards[index]
            oneCard = PairingGameCard.PairingGameCard(cardValue)
            oneCard.load()
            xPos, yPos = self.getCardPos(index)
            oneCard.setPos(xPos, yPos, 0)
            oneCard.reparentTo(render)
            self.notify.debug('%s' % oneCard.getPos())
            self.notify.debug('suit %s rank %s value %s' % (oneCard.suit, oneCard.rank, oneCard.value))
            self.accept('entercardCollision-%d' % oneCard.value, self.enterCard)
            self.accept('exitcardCollision-%d' % oneCard.value, self.exitCard)
            oneCard.turnDown(doInterval=False)
            self.cards.append(oneCard)

        self.bonusTraversal = range(len(self.cards))
        self.bonusGlow = render.attachNewNode('bonusGlow')
        sign = loader.loadModel('phase_4/models/minigames/garden_sign_memory')
        sign.find('**/sign1').removeNode()
        sign.find('**/sign2').removeNode()
        sign.find('**/collision').removeNode()
        sign.setPos(0, 0, 0.05)
        sign.reparentTo(self.bonusGlow)
        self.bonusGlow.setScale(2.5)
        self.pointsFrame = DirectFrame(relief=None, geom=DGG.getDefaultDialogGeom(), geom_color=GlobalDialogColor, geom_scale=(4, 1, 1), pos=(-0.33, 0, 0.9), scale=0.1, text=TTLocalizer.PairingGamePoints, text_align=TextNode.ALeft, text_scale=TTLocalizer.DPGpointsFrame, text_pos=(-1.94, -0.1, 0.0))
        self.pointsLabel = DirectLabel(parent=self.pointsFrame, relief=None, text='0', text_fg=VBase4(0, 0.5, 0, 1), text_align=TextNode.ARight, text_scale=0.7, pos=(1.82, 0, -0.15))
        self.flipsFrame = DirectFrame(relief=None, geom=DGG.getDefaultDialogGeom(), geom_color=GlobalDialogColor, geom_scale=(4, 1, 1), pos=(0.33, 0, 0.9), scale=0.1, text=TTLocalizer.PairingGameFlips, text_align=TextNode.ALeft, text_scale=TTLocalizer.DPGflipsFrame, text_pos=(-1.94, -0.1, 0.0))
        self.flipsLabel = DirectLabel(parent=self.flipsFrame, relief=None, text='0', text_fg=VBase4(0, 1.0, 0, 1), text_align=TextNode.ARight, text_scale=0.7, pos=(1.82, 0, -0.15))
        self.__textGen = TextNode('ringGame')
        self.__textGen.setFont(ToontownGlobals.getSignFont())
        self.__textGen.setAlign(TextNode.ACenter)
        self.sndPerfect = base.loadSfx('phase_4/audio/sfx/MG_pairing_all_matched.mp3')
        self.calcBonusTraversal()
        self.music = base.loadMusic('phase_4/audio/bgm/MG_Pairing.mid')
        self.matchSfx = base.loadSfx('phase_4/audio/sfx/MG_pairing_match.mp3')
        self.matchWithBonusSfx = base.loadSfx('phase_4/audio/sfx/MG_pairing_match_bonus_both.mp3')
        self.signalSfx = []
        for i in range(4):
            self.signalSfx.append(base.loadSfx('phase_4/audio/sfx/MG_pairing_jumping_signal.mp3'))

        self.bonusMovesSfx = base.loadSfx('phase_4/audio/sfx/MG_pairing_bonus_moves.mp3')
        return

    def unload(self):
        self.notify.debug('unload')
        DistributedMinigame.unload(self)
        self.removeChildGameFSM(self.gameFSM)
        del self.gameFSM
        self.gameBoard.removeNode()
        del self.gameBoard
        for card in self.cards:
            card.unload()
            del card

        self.cards = []
        self.pointsFrame.removeNode()
        del self.pointsFrame
        self.flipsFrame.removeNode()
        del self.flipsFrame
        del self.__textGen
        del self.sndPerfect
        self.bonusGlow.removeNode()
        del self.bonusGlow
        del self.music
        del self.matchSfx
        del self.matchWithBonusSfx
        for i in range(4):
            del self.signalSfx[0]

        self.signalSfx = []
        del self.bonusMovesSfx

    def onstage(self):
        self.notify.debug('onstage')
        DistributedMinigame.onstage(self)
        self.gameBoard.reparentTo(render)
        for card in self.cards:
            card.reparentTo(render)

        lt = base.localAvatar
        lt.reparentTo(render)
        lt.hideName()
        self.__placeToon(self.localAvId)
        lt.setAnimState('Happy', 1.0)
        lt.setSpeed(0, 0)
        self.moveCameraToTop()

    def offstage(self):
        self.notify.debug('offstage')
        self.gameBoard.hide()
        for card in self.cards:
            card.hide()

        DistributedMinigame.offstage(self)

    def handleDisabledAvatar(self, avId):
        self.notify.debug('handleDisabledAvatar')
        self.notify.debug('avatar ' + str(avId) + ' disabled')
        DistributedMinigame.handleDisabledAvatar(self, avId)

    def setGameReady(self):
        if not self.hasLocalToon:
            return
        self.notify.debug('setGameReady')
        if DistributedMinigame.setGameReady(self):
            return
        for index in xrange(self.numPlayers):
            avId = self.avIdList[index]
            toon = self.getAvatar(avId)
            if toon:
                toon.reparentTo(render)
                self.__placeToon(avId)
                toon.setAnimState('Happy', 1.0)
                toon.startSmooth()
                toon.startLookAround()

    def setGameStart(self, timestamp):
        if not self.hasLocalToon:
            return
        self.notify.debug('setGameStart')
        DistributedMinigame.setGameStart(self, timestamp)
        for avId in self.remoteAvIdList:
            toon = self.getAvatar(avId)
            if toon:
                toon.stopLookAround()

        self.gameFSM.request('play')

    def isInPlayState(self):
        if not self.gameFSM.getCurrentState():
            return False
        if not self.gameFSM.getCurrentState().getName() == 'play':
            return False
        return True

    def enterOff(self):
        self.notify.debug('enterOff')

    def exitOff(self):
        pass

    def enterPlay(self):
        self.notify.debug('enterPlay')
        base.playMusic(self.music, looping=1, volume=0.9)
        orthoDrive = OrthoDrive(self.TOON_SPEED, maxFrameMove=self.MAX_FRAME_MOVE, customCollisionCallback=self.__doPairingGameCollisions)
        self.orthoWalk = OrthoWalk(orthoDrive, broadcast=not self.isSinglePlayer())
        self.orthoWalk.start()
        self.accept('insert', self.__flipKeyPressed)
        self.accept('delete', self.__flipKeyPressed)
        self.accept('time-control', self.__beginSignal)
        self.accept('time-control-up', self.__endSignal)
        self.bonusGlowIndex = 0
        self.bonusGlowCard = self.bonusTraversal[self.bonusGlowIndex]
        self.startBonusTask()
        self.timer = ToontownTimer.ToontownTimer()
        self.timer.posInTopRightCorner()
        self.timer.setTime(self.gameDuration)
        self.timer.countdown(self.gameDuration, self.timerExpired)
        if base.localAvatar.laffMeter:
            base.localAvatar.laffMeter.stop()

    def exitPlay(self):
        self.music.stop()
        self.orthoWalk.stop()
        self.orthoWalk.destroy()
        del self.orthoWalk
        self.bonusGlow.hide()
        self.stopBonusTask()
        self.timer.stop()
        self.timer.destroy()
        del self.timer
        self.ignoreAll()
        if base.localAvatar.laffMeter:
            base.localAvatar.laffMeter.start()
        if hasattr(self, 'perfectIval'):
            self.perfectIval.pause()
            del self.perfectIval
        taskMgr.remove(self.EndGameTaskName)
        taskMgr.remove('pairGameContinueSignal')

    def enterCleanup(self):
        self.notify.debug('enterCleanup')

    def exitCleanup(self):
        pass

    def __placeToon(self, avId):
        toon = self.getAvatar(avId)
        if self.numPlayers == 1:
            toon.setPos(0, 0, 0)
            toon.setHpr(0, 0, 0)
        else:
            posIndex = self.avIdList.index(avId)
            pos = self.startingPositions[posIndex]
            toon.setPos(pos[0], pos[1], pos[2])
            toon.setHpr(pos[3], 0, 0)

    def __doPairingGameCollisions(self, oldPos, newPos):
        x = bound(newPos[0], self.stageMin[0], self.stageMax[0])
        y = bound(newPos[1], self.stageMin[1], self.stageMax[1])
        newPos.setX(x)
        newPos.setY(y)
        if self.inList:
            newPos.setZ(0.15)
        else:
            newPos.setZ(0.0)
        if not oldPos == newPos:
            taskMgr.remove('pairGameContinueSignal')
        return newPos

    def getDeckOrderFromValue(self, value):
        for index in xrange(len(self.cards)):
            if self.cards[index].value == value:
                return index

        return -1

    def getDeckOrderFromPairingGameCard(self, into):
        try:
            index = self.cards.index(into)
        except ValueError:
            index = -1

        return index

    def enterCard(self, colEntry):
        intoName = colEntry.getIntoNodePath().getName()
        parts = intoName.split('-')
        value = int(parts[1])
        self.notify.debug('entered cardValue %d' % value)
        deckOrder = self.getDeckOrderFromValue(value)
        if deckOrder not in self.inList:
            self.inList.append(deckOrder)

    def exitCard(self, colEntry):
        intoName = colEntry.getIntoNodePath().getName()
        parts = intoName.split('-')
        value = int(parts[1])
        self.notify.debug('exited cardValue %d' % value)
        deckOrder = self.getDeckOrderFromValue(value)
        if deckOrder in self.inList:
            self.inList.remove(deckOrder)

    def handleMatch(self, cardA, cardB, withBonus):
        self.notify.debug('we got a match %d %d' % (cardA, cardB))
        self.matches += 1
        if cardA in self.faceUpList:
            self.faceUpList.remove(cardA)
        if cardB in self.faceUpList:
            self.faceUpList.remove(cardB)
        self.inactiveList.append(cardA)
        self.inactiveList.append(cardB)
        matchIval = Parallel()
        for card in [cardA, cardB]:
            self.cards[card].setTransparency(1)
            cardSeq = Sequence(LerpColorScaleInterval(self.cards[card], duration=1, colorScale=Vec4(1.0, 1.0, 1.0, 0.0)), Func(self.cards[card].hide))
            matchIval.append(cardSeq)

        if withBonus:
            matchIval.append(SoundInterval(self.matchWithBonusSfx, node=self.cards[card], listenerNode=base.localAvatar, cutOff=240))
        else:
            matchIval.append(SoundInterval(self.matchSfx, node=self.cards[card], listenerNode=base.localAvatar, cutOff=240))
        matchIval.start()
        if len(self.inactiveList) == len(self.cards):
            self.sendUpdate('reportDone')

    def turnUpCard(self, deckOrder):
        self.cards[deckOrder].turnUp()
        self.faceUpList.append(deckOrder)

    def turnDownCard(self, deckOrder):
        self.cards[deckOrder].turnDown()
        if deckOrder in self.faceUpList:
            self.faceUpList.remove(deckOrder)

    def __flipKeyPressed(self):
        if self.inList:
            shortestDistance = 10000
            cardToFlip = -1
            for deckOrder in self.inList:
                dist = base.localAvatar.getDistance(self.cards[deckOrder])
                if dist < shortestDistance:
                    shortestDistance = dist
                    cardToFlip = deckOrder

            deckOrderIndex = cardToFlip
            card = self.cards[deckOrderIndex]
            if card.isFaceDown() and deckOrderIndex not in self.inactiveList:
                self.sendUpdate('openCardRequest', [deckOrderIndex, self.bonusGlowCard])
            elif card.isFaceUp() and deckOrderIndex in self.faceUpList:
                pass

    def moveBonusGlowTask(self, task):
        if len(self.cards) == 0:
            return Task.done
        curT = self.getCurrentGameTime()
        intTime = int(curT / self.bonusGlowTime)
        newIndex = intTime % len(self.cards)
        if not newIndex == self.bonusGlowIndex:
            self.bonusGlowIndex = newIndex
            self.bonusGlowCard = self.bonusTraversal[self.bonusGlowIndex]
            card = self.cards[self.bonusGlowCard]
            self.bonusGlow.setPos(card.getPos())
            base.playSfx(self.bonusMovesSfx, node=card, volume=0.25)
        return Task.cont

    def timerExpired(self):
        self.sendUpdate('reportDone')

    def setDeckSeed(self, deckSeed):
        if not self.hasLocalToon:
            return
        self.deckSeed = deckSeed

    def updateFlipText(self):
        self.flipsLabel['text'] = str(self.flips)
        lowFlipModifier = PairingGameGlobals.calcLowFlipModifier(self.matches, self.flips)
        red = 1.0 - lowFlipModifier
        green = lowFlipModifier
        self.flipsLabel['text_fg'] = Vec4(red, green, 0, 1.0)

    def openCardResult(self, cardToTurnUp, avId, matchingCard, points, cardsToTurnDown):
        if not self.hasLocalToon:
            return
        if not self.isInPlayState():
            return
        if avId == base.localAvatar.doId:
            self.localFaceUpList.append(cardToTurnUp)
        self.turnUpCard(cardToTurnUp)
        gotBonus = False
        if points - self.points > 1:
            gotBonus = True
        if matchingCard > -1:
            self.handleMatch(cardToTurnUp, matchingCard, gotBonus)
        self.flips += 1
        self.updateFlipText()
        self.points = points
        self.pointsLabel['text'] = str(self.points)
        for card in cardsToTurnDown:
            self.turnDownCard(card)

    def startBonusTask(self):
        taskMgr.add(self.moveBonusGlowTask, self.taskName('moveBonusGlowTask'))

    def stopBonusTask(self):
        taskMgr.remove(self.taskName('moveBonusGlowTask'))

    def setEveryoneDone(self):
        if not self.hasLocalToon:
            return
        if self.gameFSM.getCurrentState().getName() != 'play':
            self.notify.warning('ignoring setEveryoneDone msg')
            return
        self.notify.debug('setEveryoneDone')

        def endGame(task, self = self):
            if not PairingGameGlobals.EndlessGame:
                self.gameOver()
            return Task.done

        self.timer.hide()
        self.bonusGlow.hide()
        if len(self.inactiveList) == len(self.cards):
            self.notify.debug('perfect game!')
            perfectTextSubnode = hidden.attachNewNode(self.__genText(TTLocalizer.PairingGamePerfect))
            perfectText = hidden.attachNewNode('perfectText')
            perfectTextSubnode.reparentTo(perfectText)
            frame = self.__textGen.getCardActual()
            offsetY = -abs(frame[2] + frame[3]) / 2.0
            perfectTextSubnode.setPos(0, 0, offsetY)
            perfectText.setColor(1, 0.1, 0.1, 1)

            def fadeFunc(t, text = perfectText):
                text.setColorScale(1, 1, 1, t)

            def destroyText(text = perfectText):
                text.removeNode()

            textTrack = Sequence(Func(perfectText.reparentTo, aspect2d), Parallel(LerpScaleInterval(perfectText, duration=0.5, scale=0.3, startScale=0.0), LerpFunctionInterval(fadeFunc, fromData=0.0, toData=1.0, duration=0.5)), Wait(2.0), Parallel(LerpScaleInterval(perfectText, duration=0.5, scale=1.0), LerpFunctionInterval(fadeFunc, fromData=1.0, toData=0.0, duration=0.5, blendType='easeIn')), Func(destroyText), WaitInterval(0.5), Func(endGame, None))
            soundTrack = SoundInterval(self.sndPerfect)
            self.perfectIval = Parallel(textTrack, soundTrack)
            self.perfectIval.start()
        else:
            taskMgr.doMethodLater(1, endGame, self.EndGameTaskName)
        return

    def __genText(self, text):
        self.__textGen.setText(text)
        return self.__textGen.generate()

    def b_setSignaling(self, avId):
        self.setSignaling(avId)
        self.sendUpdate('setSignaling', [self.localAvId])

    def setSignaling(self, avId):
        if not self.hasLocalToon:
            return
        avIndex = self.avIdList.index(avId)
        av = base.cr.doId2do.get(avId)
        if av and avIndex >= 0 and hasattr(self, 'signalSfx') and self.signalSfx:
            base.playSfx(self.signalSfx[avIndex], node=av)

    def __beginSignal(self, mouseParam):
        self.notify.debug('beginSignal')
        base.localAvatar.b_setEmoteState(1, 1.0)
        self.b_setSignaling(self.localAvId)
        taskMgr.doMethodLater(1.67, self.__continueSignal, 'pairGameContinueSignal')

    def __endSignal(self, mouseParam):
        self.notify.debug('endSignal')
        base.localAvatar.b_setEmoteState(-1, 1.0)
        taskMgr.remove('pairGameContinueSignal')

    def __continueSignal(self, task):
        base.localAvatar.b_setEmoteState(1, 1.0)
        self.b_setSignaling(self.localAvId)
        taskMgr.doMethodLater(1.67, self.__continueSignal, 'pairGameContinueSignal')

    def getCardPos(self, deckOrderIndex):
        col = deckOrderIndex % self.cardsPerRow
        row = deckOrderIndex / self.cardsPerRow
        x = col * self.xCardInc
        y = row * self.yCardInc
        return (x, y)

    def getDeckOrderIndex(self, row, col):
        retval = row * self.cardsPerRow
        retval += col
        if retval >= len(self.deck.cards):
            retval = -1
        return retval

    def calcBonusTraversal(self):
        self.bonusTraversal = []
        halfRow = self.cardsPerRow / 2
        if self.cardsPerRow % 2:
            halfRow += 1
        for i in xrange(halfRow):
            for j in xrange(2):
                col = i + j * halfRow
                for row in xrange(self.cardsPerCol):
                    card = self.getDeckOrderIndex(row, col)
                    if card > -1:
                        self.bonusTraversal.append(card)
