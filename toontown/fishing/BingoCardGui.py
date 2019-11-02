from direct.directnotify import DirectNotifyGlobal
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from direct.task import Task
import random
from toontown.fishing import BingoCardCell
from toontown.fishing import BingoGlobals
from toontown.fishing import FishBase
from toontown.fishing import FishGlobals
from direct.showbase import RandomNumGen
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import ToontownTimer
from toontown.toonbase import TTLocalizer
from toontown.toontowngui import TTDialog
BG = BingoGlobals

class BingoCardGui(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('BingoCardGui')

    def __init__(self, parent = aspect2d, **kw):
        self.notify.debug('Bingo card initialized')
        self.model = loader.loadModel('phase_4/models/gui/FishBingo')
        optiondefs = (('relief', None, None),
         ('state', DGG.NORMAL, None),
         ('image', self.model.find('**/g'), None),
         ('image_color', BG.getColor(0), None),
         ('image_scale', BG.CardImageScale, None),
         ('image_hpr', (0.0, 90.0, 0.0), None),
         ('pos', BG.CardPosition, None))
        self.defineoptions(kw, optiondefs)
        DirectFrame.__init__(self, parent)
        self.initialiseoptions(BingoCardGui)
        self.game = None
        self.cellGuiList = []
        self.parent = parent
        self.load()
        self.hide()
        self.taskNameFlashFish = 'flashMatchingFishTask'
        return

    def show(self):
        DirectFrame.show(self)
        if self.game and self.game.checkForBingo():
            self.__indicateBingo(True)
            if self.game.getGameType() == BG.BLOCKOUT_CARD:
                self.showJackpot()

    def hide(self):
        self.hideTutorial()
        self.hideJackpot()
        DirectFrame.hide(self)

    def loadGameTimer(self):
        self.timer = ToontownTimer.ToontownTimer()
        self.timer.reparentTo(self)
        self.timer.setScale(0.17)
        self.timer.setPos(0.24, 0, -0.18)

    def resetGameTimer(self):
        self.timer.reset()

    def startGameCountdown(self, time):
        self.notify.debug('startGameCountdown: %s' % time)
        self.timer.countdown(time)

    def startNextGameCountdown(self, time):
        self.nextGameTimer.countdown(time)

    def hideNextGameTimer(self):
        self.nextGame['text'] = ''
        self.nextGame.hide()

    def showNextGameTimer(self, text):
        self.nextGame['text'] = text
        self.nextGame.show()

    def resetNextGameTimer(self):
        self.nextGameTimer.reset()

    def stopNextGameTimer(self):
        self.nextGameTimer.stop()

    def setNextGameText(self, text):
        self.nextGame['text'] = text

    def setJackpotText(self, text):
        if text:
            str = TTLocalizer.FishBingoJackpotWin % text
        else:
            str = ''
        self.jpText['text'] = str

    def resetGameTypeText(self):
        self.gameType['text'] = ''
        self.gameType.setFrameSize()
        self.gameType.hide()

    def loadNextGameTimer(self):
        self.nextGame = DirectLabel(parent=self, relief=None, text='', text_font=ToontownGlobals.getSignFont(), text_scale=TTLocalizer.BCGnextGame * BG.CardImageScale[2], text_fg=(1.0, 1.0, 1.0, 1), pos=(BG.GridXOffset, 0, 4 * BG.CardImageScale[2]))
        self.nextGameTimer = ToontownTimer.ToontownTimer()
        self.nextGameTimer.reparentTo(self.nextGame)
        self.nextGameTimer.setPos(0, 0, -5 * BG.CardImageScale[2])
        self.nextGameTimer.setProp('image', None)
        self.nextGameTimer.setProp('text_font', ToontownGlobals.getSignFont())
        self.nextGameTimer.setProp('text_scale', 0.2 * BG.CardImageScale[2])
        self.nextGameTimer.setFontColor(Vec4(1.0, 1.0, 1.0, 1))
        return

    def setGameOver(self, text):
        self.gameOver['text'] = text

    def load(self):
        self.notify.debug('Bingo card loading')
        self.loadGameTimer()
        self.loadNextGameTimer()
        textScale = 0.06
        textHeight = 0.38 * BG.CardImageScale[2]
        guiButton = loader.loadModel('phase_3/models/gui/quit_button')
        self.bingo = DirectButton(parent=self, pos=(BG.GridXOffset, 0, 0.305), scale=(0.0343, 0.035, 0.035), relief=None, state=DGG.DISABLED, geom=self.model.find('**/BINGObutton'), geom_pos=(0, 0, 0), geom_hpr=(0, 90, 0), image=(self.model.find('**/Gold_TTButtUP'), self.model.find('**/goldTTButtDown'), self.model.find('**/RolloverBingoButton1')), image_pos=(0, 0, 0), image_hpr=(0, 90, 0), image_color=BG.getButtonColor(0), pressEffect=False)
        guiButton.removeNode()
        arrowModel = loader.loadModel('phase_3.5/models/gui/speedChatGui')
        self.gameType = DirectButton(parent=self, pos=(BG.GridXOffset, 0, -8 * BG.CardImageScale[2] - 0.01), relief=None, image=arrowModel.find('**/chatArrow'), image_scale=-0.05, image_pos=(-0.2, 0, 0.025), text='', text_scale=0.045, text_fg=(1, 1, 1, 1), text_font=ToontownGlobals.getSignFont(), text_wordwrap=10.5, text_pos=(0.01, 0.008), pressEffect=False)
        arrowModel.removeNode()
        self.gameType.bind(DGG.ENTER, self.onMouseEnter)
        self.gameType.bind(DGG.EXIT, self.onMouseLeave)
        self.gameType.hide()
        self.jpText = DirectLabel(parent=self, pos=(BG.GridXOffset, 0, 0.22), relief=None, state=DGG.NORMAL, text='', text_scale=TTLocalizer.BCGjpText, text_pos=(0, 0, 0), text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1), text_font=ToontownGlobals.getInterfaceFont(), text_wordwrap=TTLocalizer.BCGjpTextWordwrap)
        self.gameOver = DirectLabel(parent=self, pos=(BG.GridXOffset, 0, 0), relief=None, state=DGG.NORMAL, text='', text_scale=textScale, text_fg=(1, 1, 1, 1), text_font=ToontownGlobals.getSignFont())
        self.jpSign = DirectFrame(parent=self.parent, relief=None, state=DGG.NORMAL, pos=BG.CardPosition, scale=(0.035, 0.035, 0.035), text=TTLocalizer.FishBingoJackpot, text_scale=2, text_pos=(-1.5, 18.6), text_fg=(1, 1, 1, 1), image=self.model.find('**/jackpot'), image_pos=(0, 0, 0), image_hpr=(0, 90, 0), sortOrder=DGG.BACKGROUND_SORT_INDEX)
        self.makeJackpotLights(self.jpSign)
        self.hideJackpot()
        self.makeTutorial()
        return

    def destroy(self):
        self.cleanTutorial()
        self.removeGame()
        del self.cellGuiList
        self.gameOver.destroy()
        self.destroyJackpotLights()
        self.jpSign.destroy()
        self.nextGameTimer.destroy()
        self.nextGame.destroy()
        self.timer.destroy()
        self.bingo.destroy()
        self.gameType.destroy()
        DirectFrame.destroy(self)
        self.notify.debug('Bingo card destroyed')

    def loadCard(self):
        cardSize = self.game.getCardSize()
        for index in xrange(cardSize):
            self.cellGuiList[index].generateLogo()
            if index == cardSize / 2:
                self.cellGuiList[index].generateMarkedLogo()
            elif self.game.getGameState() & 1 << index:
                self.cellGuiList[index].disable()

    def disableCard(self):
        self.stopCellBlinking()
        for index in xrange(self.game.getCardSize()):
            self.cellGuiList[index].disable()

    def enableCard(self, callback = None):
        self.notify.info('enable Bingo card')
        self.stopCellBlinking()
        for index in xrange(len(self.cellGuiList)):
            if index != self.game.getCardSize() / 2:
                self.cellGuiList[index].enable(callback)

    def generateCard(self, tileSeed, zoneId):
        rng = RandomNumGen.RandomNumGen(tileSeed)
        rowSize = self.game.getRowSize()
        fishList = FishGlobals.getPondGeneraList(zoneId)
        for i in xrange(len(fishList)):
            fishTuple = fishList.pop(0)
            weight = FishGlobals.getRandomWeight(fishTuple[0], fishTuple[1])
            fish = FishBase.FishBase(fishTuple[0], fishTuple[1], weight)
            fishList.append(fish)

        emptyCells = self.game.getCardSize() - 1 - len(fishList)
        rodId = 0
        for i in xrange(emptyCells):
            fishVitals = FishGlobals.getRandomFishVitals(zoneId, rodId, rng)
            while not fishVitals[0]:
                fishVitals = FishGlobals.getRandomFishVitals(zoneId, rodId, rng)

            fish = FishBase.FishBase(fishVitals[1], fishVitals[2], fishVitals[3])
            fishList.append(fish)
            rodId += 1
            if rodId > 4:
                rodId = 0

        for i in xrange(rowSize):
            for j in xrange(self.game.getColSize()):
                color = self.getCellColor(i * rowSize + j)
                if i * rowSize + j == self.game.getCardSize() / 2:
                    tmpFish = 'Free'
                else:
                    choice = rng.randrange(0, len(fishList))
                    tmpFish = fishList.pop(choice)
                xPos = BG.CellImageScale * (j - 2) + BG.GridXOffset
                yPos = BG.CellImageScale * (i - 2) - 0.015
                cellGui = BingoCardCell.BingoCardCell(i * rowSize + j, tmpFish, self.model, color, self, image_scale=BG.CellImageScale, pos=(xPos, 0, yPos))
                self.cellGuiList.append(cellGui)

    def cellUpdateCheck(self, id, genus, species):
        fishTuple = (genus, species)
        if self.cellGuiList[id].getFishGenus() == genus or fishTuple == FishGlobals.BingoBoot:
            self.notify.debug('Square found!  Cell disabled: %s' % id)
            self.stopCellBlinking()
            self.cellGuiList[id].disable()
            self.game.setGameState(self.game.getGameState() | 1 << id)
            if self.game.checkForBingo():
                return BG.WIN
            return BG.UPDATE
        return BG.NO_UPDATE

    def cellUpdate(self, cellId):
        self.cellGuiList[cellId].disable()

    def addGame(self, game):
        self.game = game
        type = game.getGameType()
        self.gameType.setProp('text', BG.getGameName(type))
        self.gameType.setFrameSize()
        self.gameType.show()

    def getGame(self):
        return self.game

    def removeGame(self):
        self.stopCellBlinking()
        if self.game:
            self.game.destroy()
            self.game = None
        self.setJackpotText(None)
        self.resetGameTypeText()
        for cell in self.cellGuiList:
            cell.destroy()

        self.cellGuiList = []
        return

    def getUnmarkedMatches(self, fish):
        if self.game is None:
            return []
        matches = []
        for cell in self.cellGuiList:
            if cell['state'] == DGG.NORMAL:
                if cell.getFishGenus() == fish[0] or fish == FishGlobals.BingoBoot:
                    matches.append(cell)

        return matches

    def getCellColor(self, id):
        if self.game.checkForColor(id):
            return BG.CellColorActive
        return BG.CellColorInactive

    def resetCellColors(self):
        for cell in self.cellGuiList:
            c = self.getCellColor(cell.cellId)
            cell['image'].setColor(c[0], c[1], c[2], c[3])
            cell.setImage()

    def stopCellBlinking(self):
        self.hideTutorial()
        self.resetCellColors()
        taskMgr.remove(self.taskNameFlashFish)

    def __indicateMatches(self, bFlipFlop, fish):
        unmarkedMatches = self.getUnmarkedMatches(fish)
        if len(unmarkedMatches) is 0:
            return Task.done
        if bFlipFlop:
            for cell in unmarkedMatches:
                cell['image'].setColor(1, 0, 0, 1)
                cell.setImage()

        else:
            self.resetCellColors()
        taskMgr.doMethodLater(0.5, self.__indicateMatches, self.taskNameFlashFish, extraArgs=(not bFlipFlop, fish))
        return Task.done

    def fishCaught(self, fish):
        self.stopCellBlinking()
        self.__indicateMatches(True, fish)

    def setBingo(self, state = DGG.DISABLED, callback = None):
        self.notify.debug('setBingo: %s %s' % (state, callback))
        if self.bingo['state'] == state:
            return
        if not self.game:
            return
        if state == DGG.NORMAL:
            self.__indicateBingo(True)
            if self.game.getGameType() == BG.BLOCKOUT_CARD:
                self.showJackpot()
        else:
            taskMgr.remove('bingoFlash')
            c = BG.getButtonColor(self.game.getGameType())
            self.bingo['image_color'] = Vec4(c[0], c[1], c[2], c[3])
            self.hideJackpot()
        self.bingo['state'] = state
        self.bingo['command'] = callback

    def checkForBingo(self):
        return self.game.checkForBingo()

    def __indicateBingo(self, bFlipFlop):
        if not self.game:
            return Task.done
        if bFlipFlop:
            gameType = self.game.getGameType()
            if gameType == BG.DIAGONAL_CARD:
                color = Vec4(1, 1, 1, 1)
            else:
                color = Vec4(1, 0, 0, 1)
            self.bingo['image_color'] = color
        else:
            c = BG.getButtonColor(self.game.getGameType())
            self.bingo['image_color'] = Vec4(c[0], c[1], c[2], c[3])
        taskMgr.doMethodLater(0.5, self.__indicateBingo, 'bingoFlash', extraArgs=(not bFlipFlop,))
        return Task.done

    NumLights = 32
    Off = False
    On = True

    def showJackpot(self):
        self.jpSign.show()
        for light in self.jpLights:
            light.show()

        self.flashJackpotLights(random.randrange(3))

    def hideJackpot(self):
        self.jpSign.hide()
        for light in self.jpLights:
            light.hide()

        taskMgr.remove('jackpotLightFlash')

    def getLightName(self, lightIndex, bOn):
        lightIndex += 1
        if bOn == self.On:
            return '**/LightOn_0%02d' % lightIndex
        else:
            return '**/LightOff_0%02d' % lightIndex

    def makeJackpotLights(self, parent):
        self.jpLights = []
        for nLight in range(self.NumLights):
            lightName = self.getLightName(nLight, self.Off)
            light = DirectFrame(parent=parent, relief=None, image=self.model.find(lightName), image_hpr=(0, 90, 0))
            self.jpLights.append(light)

        return

    def destroyJackpotLights(self):
        taskMgr.remove('jackpotLightFlash')
        for light in self.jpLights:
            light.destroy()

    def lightSwitch(self, bOn, lightIndex = -1):
        if lightIndex == -1:
            for nLight in range(self.NumLights):
                self.lightSwitch(bOn, nLight)

        else:
            lightIndex %= self.NumLights
            light = self.jpLights[lightIndex - 1]
            light['image'] = self.model.find(self.getLightName(lightIndex, bOn))
            light['image_hpr'] = (0, 90, 0)

    def flashJackpotLights(self, flashMode, nTimeIndex = 0):
        if flashMode == 2:
            self.lightSwitch(self.Off)
            self.lightSwitch(self.On, nTimeIndex)
            self.lightSwitch(self.On, self.NumLights - nTimeIndex)
            self.lightSwitch(self.On, self.NumLights / 2 + nTimeIndex)
            self.lightSwitch(self.On, self.NumLights / 2 - nTimeIndex)
            nTimeIndex = (nTimeIndex + 1) % (self.NumLights / 2)
            delay = 0.05
        elif flashMode == 1:
            if nTimeIndex:
                self.lightSwitch(self.On)
            else:
                self.lightSwitch(self.Off)
            nTimeIndex = not nTimeIndex
            delay = 0.5
        elif flashMode == 0:
            for nLight in range(self.NumLights):
                if nLight % 2 == nTimeIndex:
                    self.lightSwitch(self.On, nLight)
                else:
                    self.lightSwitch(self.Off, nLight)

            nTimeIndex = (nTimeIndex + 1) % 2
            delay = 0.2
        taskMgr.doMethodLater(delay, self.flashJackpotLights, 'jackpotLightFlash', extraArgs=(flashMode, nTimeIndex))
        return Task.done

    def makeTutorial(self):
        self.tutorial = TTDialog.TTDialog(fadeScreen=0, pad=(0.05, 0.05), midPad=0, topPad=0, sidePad=0, text=TTLocalizer.FishBingoHelpBlockout, style=TTDialog.NoButtons, pos=BG.TutorialPosition, scale=BG.TutorialScale)
        self.tutorial.hide()

    def cleanTutorial(self):
        self.tutorial.cleanup()
        self.tutorial = None
        return

    def showTutorial(self, messageType):
        if messageType == BG.TutorialIntro:
            self.tutorial['text'] = TTLocalizer.FishBingoHelpMain
        elif messageType == BG.TutorialMark:
            self.tutorial['text'] = TTLocalizer.FishBingoHelpFlash
        elif messageType == BG.TutorialCard:
            if self.game:
                gameType = self.game.getGameType()
                self.tutorial['text'] = BG.getHelpString(gameType)
        elif messageType == BG.TutorialBingo:
            self.tutorial['text'] = TTLocalizer.FishBingoHelpBingo
        self.tutorial.show()

    def hideTutorial(self, event = None):
        if self.tutorial:
            self.tutorial.hide()

    def onMouseEnter(self, event):
        if self.gameType['text'] is not '':
            self.showTutorial(BG.TutorialCard)

    def onMouseLeave(self, event):
        self.hideTutorial()

    def castingStarted(self):
        if taskMgr.hasTaskNamed(self.taskNameFlashFish):
            if not base.localAvatar.bFishBingoMarkTutorialDone:
                self.showTutorial(BG.TutorialMark)
                base.localAvatar.b_setFishBingoMarkTutorialDone(True)
