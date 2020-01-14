from pandac.PandaModules import *
from toontown.toonbase.ToonBaseGlobal import *
from direct.distributed.ClockDelta import *
from direct.interval.IntervalGlobal import *
from .DistributedMinigame import *
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from direct.task.Task import Task
from toontown.toonbase import ToontownTimer
from . import RaceGameGlobals
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer

class DistributedRaceGame(DistributedMinigame):

    def __init__(self, cr):
        DistributedMinigame.__init__(self, cr)
        self.gameFSM = ClassicFSM.ClassicFSM('DistributedRaceGame', [State.State('off', self.enterOff, self.exitOff, ['inputChoice']),
         State.State('inputChoice', self.enterInputChoice, self.exitInputChoice, ['waitServerChoices', 'moveAvatars', 'cleanup']),
         State.State('waitServerChoices', self.enterWaitServerChoices, self.exitWaitServerChoices, ['moveAvatars', 'cleanup']),
         State.State('moveAvatars', self.enterMoveAvatars, self.exitMoveAvatars, ['inputChoice', 'winMovie', 'cleanup']),
         State.State('winMovie', self.enterWinMovie, self.exitWinMovie, ['cleanup']),
         State.State('cleanup', self.enterCleanup, self.exitCleanup, [])], 'off', 'cleanup')
        self.addChildGameFSM(self.gameFSM)
        self.posHprArray = (((-9.03,
           0.06,
           0.025,
           -152.9),
          (-7.43,
           -2.76,
           0.025,
           -152.68),
          (-6.02,
           -5.48,
           0.025,
           -157.54),
          (-5.01,
           -8.32,
           0.025,
           -160.66),
          (-4.05,
           -11.36,
           0.025,
           -170.22),
          (-3.49,
           -14.18,
           0.025,
           -175.76),
          (-3.12,
           -17.15,
           0.025,
           -177.73),
          (-3.0,
           -20.32,
           0.025,
           178.49),
          (-3.09,
           -23.44,
           0.025,
           176.59),
          (-3.43,
           -26.54,
           0.025,
           171.44),
          (-4.07,
           -29.44,
           0.025,
           163.75),
          (-5.09,
           -32.27,
           0.025,
           158.2),
          (-6.11,
           -35.16,
           0.025,
           154.98),
          (-7.57,
           -37.78,
           0.025,
           154.98),
          (-9.28,
           -40.65,
           0.025,
           150.41)),
         ((-6.12,
           1.62,
           0.025,
           -152.9),
          (-4.38,
           -1.35,
           0.025,
           -150.92),
          (-3.08,
           -4.3,
           0.025,
           -157.9),
          (-1.85,
           -7.26,
           0.025,
           -162.54),
          (-0.93,
           -10.49,
           0.025,
           -167.71),
          (-0.21,
           -13.71,
           0.025,
           -171.79),
          (0.21,
           -17.08,
           0.025,
           -174.92),
          (0.31,
           -20.2,
           0.025,
           177.1),
          (0.17,
           -23.66,
           0.025,
           174.82),
          (-0.23,
           -26.91,
           0.025,
           170.51),
          (-0.99,
           -30.2,
           0.025,
           162.54),
          (-2.02,
           -33.28,
           0.025,
           160.48),
          (-3.28,
           -36.38,
           0.025,
           157.96),
          (-4.67,
           -39.17,
           0.025,
           154.13),
          (-6.31,
           -42.15,
           0.025,
           154.13)),
         ((-2.99,
           3.09,
           0.025,
           -154.37),
          (-1.38,
           -0.05,
           0.025,
           -154.75),
          (-0.19,
           -3.29,
           0.025,
           -159.22),
          (1.17,
           -6.51,
           0.025,
           -162.74),
          (2.28,
           -9.8,
           0.025,
           -168.73),
          (3.09,
           -13.28,
           0.025,
           -173.49),
          (3.46,
           -16.63,
           0.025,
           -176.81),
          (3.69,
           -20.38,
           0.025,
           179.14),
          (3.61,
           -24.12,
           0.025,
           175.78),
          (3.0,
           -27.55,
           0.025,
           170.87),
          (2.15,
           -30.72,
           0.025,
           167.41),
          (1.04,
           -34.26,
           0.025,
           162.11),
          (-0.15,
           -37.44,
           0.025,
           158.59),
          (-1.64,
           -40.52,
           0.025,
           153.89),
          (-3.42,
           -43.63,
           0.025,
           153.89)),
         ((0.0,
           4.35,
           0.025,
           -154.37),
          (1.52,
           1.3,
           0.025,
           -155.67),
          (3.17,
           -2.07,
           0.025,
           -155.67),
          (4.47,
           -5.41,
           0.025,
           -163.0),
          (5.56,
           -9.19,
           0.025,
           -168.89),
          (6.22,
           -12.66,
           0.025,
           -171.67),
          (6.67,
           -16.56,
           0.025,
           -176.53),
          (6.93,
           -20.33,
           0.025,
           179.87),
          (6.81,
           -24.32,
           0.025,
           175.19),
          (6.22,
           -27.97,
           0.025,
           170.81),
          (5.59,
           -31.73,
           0.025,
           167.54),
          (4.48,
           -35.42,
           0.025,
           161.92),
          (3.06,
           -38.82,
           0.025,
           158.56),
          (1.4,
           -42.0,
           0.025,
           154.32),
          (-0.71,
           -45.17,
           0.025,
           153.27)))
        self.avatarPositions = {}
        self.modelCount = 8
        self.cameraTopView = (-22.78,
         -41.65,
         31.53,
         -51.55,
         -42.68,
         -2.96)
        self.timer = None
        self.timerStartTime = None
        self.walkSeqs = {}
        self.runSeqs = {}
        return None

    def getTitle(self):
        return TTLocalizer.RaceGameTitle

    def getInstructions(self):
        return TTLocalizer.RaceGameInstructions

    def getMaxDuration(self):
        return 60

    def load(self):
        self.notify.debug('load')
        DistributedMinigame.load(self)
        self.raceBoard = loader.loadModel('phase_4/models/minigames/race')
        self.raceBoard.setPosHpr(0, 0, 0, 0, 0, 0)
        self.raceBoard.setScale(0.8)
        self.dice = loader.loadModel('phase_4/models/minigames/dice')
        self.dice1 = self.dice.find('**/dice_button1')
        self.dice2 = self.dice.find('**/dice_button2')
        self.dice3 = self.dice.find('**/dice_button3')
        self.dice4 = self.dice.find('**/dice_button4')
        self.diceList = [self.dice1,
         self.dice2,
         self.dice3,
         self.dice4]
        self.music = base.loader.loadMusic('phase_4/audio/bgm/minigame_race.ogg')
        self.posBuzzer = base.loader.loadSfx('phase_4/audio/sfx/MG_pos_buzzer.ogg')
        self.negBuzzer = base.loader.loadSfx('phase_4/audio/sfx/MG_neg_buzzer.ogg')
        self.winSting = base.loader.loadSfx('phase_4/audio/sfx/MG_win.ogg')
        self.loseSting = base.loader.loadSfx('phase_4/audio/sfx/MG_lose.ogg')
        self.diceButtonList = []
        for i in range(1, 5):
            button = self.dice.find('**/dice_button' + str(i))
            button_down = self.dice.find('**/dice_button' + str(i) + '_down')
            button_ro = self.dice.find('**/dice_button' + str(i) + '_ro')
            diceButton = DirectButton(image=(button,
             button_down,
             button_ro,
             None), relief=None, pos=(-0.9 + (i - 1) * 0.2, 0.0, -0.85), scale=0.25, command=self.handleInputChoice, extraArgs=[i])
            diceButton.hide()
            self.diceButtonList.append(diceButton)

        self.waitingChoicesLabel = DirectLabel(text=TTLocalizer.RaceGameWaitingChoices, text_fg=VBase4(1, 1, 1, 1), relief=None, pos=(-0.6, 0, -0.75), scale=0.075)
        self.waitingChoicesLabel.hide()
        self.chanceMarker = loader.loadModel('phase_4/models/minigames/question_mark')
        self.chanceCard = loader.loadModel('phase_4/models/minigames/chance_card')
        self.chanceCardText = OnscreenText('', fg=(1.0, 0, 0, 1), scale=0.14, font=ToontownGlobals.getSignFont(), wordwrap=14, pos=(0.0, 0.2), mayChange=1)
        self.chanceCardText.hide()
        self.cardSound = base.loader.loadSfx('phase_3.5/audio/sfx/GUI_stickerbook_turn.ogg')
        self.chanceMarkers = []
        return

    def unload(self):
        self.notify.debug('unload')
        DistributedMinigame.unload(self)
        self.raceBoard.removeNode()
        del self.raceBoard
        self.dice.removeNode()
        del self.dice
        self.chanceMarker.removeNode()
        del self.chanceMarker
        self.chanceCardText.removeNode()
        del self.chanceCardText
        self.chanceCard.removeNode()
        del self.chanceCard
        self.waitingChoicesLabel.destroy()
        del self.waitingChoicesLabel
        del self.music
        del self.posBuzzer
        del self.negBuzzer
        del self.winSting
        del self.loseSting
        del self.cardSound
        for button in self.diceButtonList:
            button.destroy()

        del self.diceButtonList
        for marker in self.chanceMarkers:
            marker.removeNode()
            del marker

        del self.chanceMarkers
        self.removeChildGameFSM(self.gameFSM)
        del self.gameFSM

    def onstage(self):
        self.notify.debug('onstage')
        DistributedMinigame.onstage(self)
        base.playMusic(self.music, looping=1, volume=0.8)
        self.raceBoard.reparentTo(render)
        camera.reparentTo(render)
        p = self.cameraTopView
        camera.setPosHpr(p[0], p[1], p[2], p[3], p[4], p[5])
        base.transitions.irisIn(0.4)
        base.setBackgroundColor(0.1875, 0.7929, 0)

    def offstage(self):
        self.notify.debug('offstage')
        DistributedMinigame.offstage(self)
        self.music.stop()
        base.setBackgroundColor(ToontownGlobals.DefaultBackgroundColor)
        self.raceBoard.reparentTo(hidden)
        self.chanceCard.reparentTo(hidden)
        self.chanceCardText.hide()
        if hasattr(self, 'chanceMarkers'):
            for marker in self.chanceMarkers:
                marker.reparentTo(hidden)

    def setGameReady(self):
        if not self.hasLocalToon:
            return
        self.notify.debug('setGameReady')
        if DistributedMinigame.setGameReady(self):
            return
        self.resetPositions()
        for i in range(self.numPlayers):
            avId = self.avIdList[i]
            if self.localAvId == avId:
                self.localAvLane = i
            avatar = self.getAvatar(avId)
            if avatar:
                avatar.reparentTo(render)
                avatar.setAnimState('neutral', 1)
                self.positionInPlace(avatar, i, 0)

    def setGameStart(self, timestamp):
        if not self.hasLocalToon:
            return
        self.notify.debug('setGameStart')
        DistributedMinigame.setGameStart(self, timestamp)
        self.gameFSM.request('inputChoice')

    def enterOff(self):
        self.notify.debug('enterOff')

    def exitOff(self):
        pass

    def enterInputChoice(self):
        self.notify.debug('enterInputChoice')
        for button in self.diceButtonList:
            button.show()

        self.timer = ToontownTimer.ToontownTimer()
        self.timer.hide()
        if self.timerStartTime != None:
            self.startTimer()
        return

    def startTimer(self):
        now = globalClock.getFrameTime()
        elapsed = now - self.timerStartTime
        self.timer.posInTopRightCorner()
        self.timer.setTime(RaceGameGlobals.InputTimeout)
        self.timer.countdown(RaceGameGlobals.InputTimeout - elapsed, self.handleChoiceTimeout)
        self.timer.show()

    def setTimerStartTime(self, timestamp):
        if not self.hasLocalToon:
            return
        self.timerStartTime = globalClockDelta.networkToLocalTime(timestamp)
        if self.timer != None:
            self.startTimer()
        return

    def exitInputChoice(self):
        for button in self.diceButtonList:
            button.hide()

        if self.timer != None:
            self.timer.destroy()
            self.timer = None
        self.timerStartTime = None
        self.ignore('diceButton')
        return

    def handleChoiceTimeout(self):
        self.sendUpdate('setAvatarChoice', [0])
        self.gameFSM.request('waitServerChoices')

    def handleInputChoice(self, choice):
        self.sendUpdate('setAvatarChoice', [choice])
        self.gameFSM.request('waitServerChoices')

    def enterWaitServerChoices(self):
        self.notify.debug('enterWaitServerChoices')
        self.waitingChoicesLabel.show()

    def exitWaitServerChoices(self):
        self.waitingChoicesLabel.hide()

    def localToonWon(self):
        localToonPosition = self.avatarPositions[self.localAvId]
        if localToonPosition >= RaceGameGlobals.NumberToWin:
            self.notify.debug('localToon won')
            return 1
        else:
            return 0

    def anyAvatarWon(self):
        for position in list(self.avatarPositions.values()):
            if position >= RaceGameGlobals.NumberToWin:
                self.notify.debug('anyAvatarWon: Somebody won')
                return 1

        self.notify.debug('anyAvatarWon: Nobody won')
        return 0

    def showNumbers(self, task):
        self.notify.debug('showing numbers...')
        self.diceInstanceList = []
        for i in range(len(task.choiceList)):
            avId = self.avIdList[i]
            choice = task.choiceList[i]
            if choice == 0:
                self.diceInstanceList.append(None)
            else:
                diceInstance = self.diceList[choice - 1].copyTo(self.raceBoard)
                self.diceInstanceList.append(diceInstance)
                dicePosition = self.avatarPositions[avId] + 1
                diceInstance.setScale(4.0)
                self.positionInPlace(diceInstance, i, dicePosition)
                diceInstance.setP(-90)
                diceInstance.setZ(0.05)
                diceInstance.setDepthOffset(1)

        return Task.done

    def showMatches(self, task):
        self.notify.debug('showing matches...')
        for i in range(len(task.choiceList)):
            avId = self.avIdList[i]
            choice = task.choiceList[i]
            if choice != 0:
                diceInstance = self.diceInstanceList[i]
                freq = task.choiceList.count(choice)
                if freq == 1:
                    diceInstance.setColor(0.2, 1, 0.2, 1)
                    if avId == self.localAvId:
                        base.playSfx(self.posBuzzer)
                else:
                    diceInstance.setColor(1, 0.2, 0.2, 1)
                    if avId == self.localAvId:
                        base.playSfx(self.negBuzzer)

        return Task.done

    def hideNumbers(self, task):
        self.notify.debug('hiding numbers...')
        for dice in self.diceInstanceList:
            if dice:
                dice.removeNode()

        self.diceInstanceList = []
        return Task.done

    def enterMoveAvatars(self, choiceList, positionList, rewardList):
        self.notify.debug('in enterMoveAvatars:')
        tasks = []
        self.avatarPositionsCopy = self.avatarPositions.copy()
        for i in range(0, len(choiceList) // self.numPlayers):
            startIndex = i * self.numPlayers
            endIndex = startIndex + self.numPlayers
            self.choiceList = choiceList[startIndex:endIndex]
            self.positionList = positionList[startIndex:endIndex]
            self.rewardList = rewardList[startIndex:endIndex]
            self.notify.debug('           turn: ' + str(i + 1))
            self.notify.debug('     choiceList: ' + str(self.choiceList))
            self.notify.debug('   positionList: ' + str(self.positionList))
            self.notify.debug('     rewardList: ' + str(self.rewardList))
            longestLerpTime = self.getLongestLerpTime(i > 0)
            self.notify.debug('longestLerpTime: ' + str(longestLerpTime))
            if i == 0:
                snt = Task(self.showNumbers)
                snt.choiceList = self.choiceList
                smt = Task(self.showMatches)
                smt.choiceList = self.choiceList
                tasks += [snt, Task.pause(0.5), smt]
            if longestLerpTime > 0.0:
                self.notify.debug('someone moved...')
                mat = Task(self.moveAvatars)
                mat.choiceList = self.choiceList
                mat.positionList = self.positionList
                mat.rewardList = self.rewardList
                mat.name = 'moveAvatars'
                if i == 0:
                    tasks += [Task.pause(0.75),
                     mat,
                     Task.pause(0.75),
                     Task(self.hideNumbers),
                     Task.pause(longestLerpTime - 0.5)]
                else:
                    mat.chance = 1
                    tasks += [mat, Task.pause(longestLerpTime)]
                tasks += self.showChanceRewards()
            else:
                self.notify.debug('no one moved...')
                tasks += [Task.pause(1.0), Task(self.hideNumbers)]

        self.notify.debug('task list : ' + str(tasks))
        wdt = Task(self.walkDone)
        wdt.name = 'walk done'
        tasks.append(wdt)
        moveTask = Task.sequence(*tasks)
        taskMgr.add(moveTask, 'moveAvatars')

    def walkDone(self, task):
        self.choiceList = []
        self.positionList = []
        if self.anyAvatarWon():
            self.gameFSM.request('winMovie')
        else:
            self.gameFSM.request('inputChoice')
        return Task.done

    def getLongestLerpTime(self, afterFirst):
        self.notify.debug('afterFirst: ' + str(afterFirst))
        longestTime = 0.0
        for i in range(len(self.choiceList)):
            freq = self.choiceList.count(self.choiceList[i])
            if afterFirst or freq == 1:
                oldPosition = self.avatarPositionsCopy[self.avIdList[i]]
                newPosition = self.positionList[i]
                self.avatarPositionsCopy[self.avIdList[i]] = newPosition
                squares_walked = abs(newPosition - oldPosition)
                longestTime = max(longestTime, self.getWalkDuration(squares_walked))

        return longestTime

    def showChanceRewards(self):
        tasks = []
        for reward in self.rewardList:
            self.notify.debug('showChanceRewards: reward = ' + str(reward))
            index = self.rewardList.index(reward)
            if reward != -1:
                self.notify.debug('adding tasks!')
                hcc = Task(self.hideChanceMarker)
                hcc.chanceMarkers = self.chanceMarkers
                hcc.index = index
                sct = Task(self.showChanceCard)
                sct.chanceCard = self.chanceCard
                sct.cardSound = self.cardSound
                stt = Task(self.showChanceCardText)
                rewardEntry = RaceGameGlobals.ChanceRewards[reward]
                stt.rewardIdx = reward
                if rewardEntry[0][0] < 0 or rewardEntry[0][1] > 0:
                    stt.sound = self.negBuzzer
                else:
                    stt.sound = self.posBuzzer
                stt.picker = self.avIdList[index]
                rct = Task(self.resetChanceCard)
                task = Task.sequence(hcc, sct, Task.pause(1.0), stt, Task.pause(3.0), rct, Task.pause(0.25))
                tasks.append(task)

        return tasks

    def showChanceCard(self, task):
        base.playSfx(task.cardSound)
        self.chanceCard.reparentTo(render)
        quat = Quat()
        quat.setHpr((270, 0, -85.24))
        self.chanceCard.posQuatInterval(1.0, (19.62, 13.41, 13.14), quat, other=camera, name='cardLerp').start()
        return Task.done

    def hideChanceMarker(self, task):
        task.chanceMarkers[task.index].reparentTo(hidden)
        return Task.done

    def showChanceCardText(self, task):
        self.notify.debug('showing chance reward: ' + str(task.rewardIdx))
        name = self.getAvatar(task.picker).getName()
        rewardEntry = RaceGameGlobals.ChanceRewards[task.rewardIdx]
        cardText = ''
        if rewardEntry[1] != -1:
            rewardstr_fmt = TTLocalizer.RaceGameCardText
            if rewardEntry[2] > 0:
                rewardstr_fmt = TTLocalizer.RaceGameCardTextBeans
            cardText = rewardstr_fmt % {'name': name,
             'reward': rewardEntry[1]}
        else:
            rewardstr_fmt = TTLocalizer.RaceGameCardTextHi1
            cardText = rewardstr_fmt % {'name': name}
        base.playSfx(task.sound)
        self.chanceCardText.setText(cardText)
        self.chanceCardText.show()
        return Task.done

    def resetChanceCard(self, task):
        self.chanceCardText.hide()
        self.chanceCard.reparentTo(hidden)
        self.chanceCard.setPosHpr(0, 0, 0, 0, 0, 0)
        return Task.done

    def moveCamera(self):
        bestPosIdx = list(self.avatarPositions.values())[0]
        best_lane = 0
        cur_lane = 0
        for pos in list(self.avatarPositions.values()):
            if pos > bestPosIdx:
                bestPosIdx = pos
                best_lane = cur_lane
            cur_lane = cur_lane + 1

        bestPosIdx = min(RaceGameGlobals.NumberToWin, bestPosIdx)
        localToonPosition = self.avatarPositions[self.localAvId]
        savedCamPos = camera.getPos()
        savedCamHpr = camera.getHpr()
        pos1_idx = min(RaceGameGlobals.NumberToWin - 4, localToonPosition)
        pos1 = self.posHprArray[self.localAvLane][pos1_idx]
        bestPosLookAtIdx = bestPosIdx + 1
        localToonLookAtIdx = localToonPosition + 4
        if localToonLookAtIdx >= bestPosLookAtIdx:
            pos2_idx = localToonLookAtIdx
            pos2_idx = min(RaceGameGlobals.NumberToWin, pos2_idx)
            pos2 = self.posHprArray[self.localAvLane][pos2_idx]
        else:
            pos2_idx = bestPosLookAtIdx
            pos2_idx = min(RaceGameGlobals.NumberToWin, pos2_idx)
            pos2 = self.posHprArray[best_lane][pos2_idx]
        posDeltaVecX = pos2[0] - pos1[0]
        posDeltaVecY = pos2[1] - pos1[1]
        DistanceMultiplier = 0.8
        camposX = pos2[0] + DistanceMultiplier * posDeltaVecX
        camposY = pos2[1] + DistanceMultiplier * posDeltaVecY
        race_fraction = bestPosIdx / float(RaceGameGlobals.NumberToWin)
        CamHeight = 10.0 * race_fraction + (1.0 - race_fraction) * 22.0
        CamPos = Vec3(camposX, camposY, pos2[2] + CamHeight)
        camera.setPos(CamPos)
        camera_lookat_idx = min(RaceGameGlobals.NumberToWin - 6, localToonPosition)
        posLookAt = self.posHprArray[self.localAvLane][camera_lookat_idx]
        camera.lookAt(posLookAt[0], posLookAt[1], posLookAt[2])
        CamQuat = Quat()
        CamQuat.setHpr(camera.getHpr())
        camera.setPos(savedCamPos)
        camera.setHpr(savedCamHpr)
        camera.posQuatInterval(0.75, CamPos, CamQuat).start()

    def getWalkDuration(self, squares_walked):
        walkDuration = abs(squares_walked / 1.2)
        if squares_walked > 4:
            walkDuration = walkDuration * 0.3
        return walkDuration

    def moveAvatars(self, task):
        self.notify.debug('In moveAvatars: ')
        self.notify.debug('    choiceList: ' + str(task.choiceList))
        self.notify.debug('  positionList: ' + str(task.positionList))
        self.notify.debug('  rewardList: ' + str(task.rewardList))
        for i in range(len(self.choiceList)):
            avId = self.avIdList[i]
            choice = task.choiceList[i]
            position = task.positionList[i]
            chance = max(0, hasattr(task, 'chance'))
            if choice != 0:
                oldPosition = self.avatarPositions[avId]
                self.avatarPositions[avId] = position
                self.moveCamera()
                if not chance and task.choiceList.count(choice) != 1:
                    self.notify.debug('duplicate choice!')
                else:
                    avatar = self.getAvatar(avId)
                    if avatar:
                        squares_walked = abs(position - oldPosition)
                        if squares_walked > 4:
                            self.notify.debug('running')
                            avatar.setPlayRate(1.0, 'run')
                            self.runInPlace(avatar, i, oldPosition, position, self.getWalkDuration(squares_walked))
                        else:
                            if choice > 0:
                                self.notify.debug('walking forwards')
                                avatar.setPlayRate(1.0, 'walk')
                            else:
                                self.notify.debug('walking backwards')
                                avatar.setPlayRate(-1.0, 'walk')
                            self.walkInPlace(avatar, i, position, self.getWalkDuration(squares_walked))

        return Task.done

    def exitMoveAvatars(self):
        self.notify.debug('In exitMoveAvatars: removing hooks')
        taskMgr.remove('moveAvatars')
        return None

    def gameOverCallback(self, task):
        self.gameOver()
        return Task.done

    def enterWinMovie(self):
        self.notify.debug('enterWinMovie')
        if self.localToonWon():
            base.playSfx(self.winSting)
        else:
            base.playSfx(self.loseSting)
        for avId in self.avIdList:
            avPosition = self.avatarPositions[avId]
            if avPosition >= RaceGameGlobals.NumberToWin:
                avatar = self.getAvatar(avId)
                if avatar:
                    lane = str(self.avIdList.index(avId))
                    if lane in list(self.runSeqs.keys()):
                        runSeq = self.runSeqs[lane]
                        if runSeq:
                            runSeq.finish()
                        del self.runSeqs[lane]
                    if lane in list(self.walkSeqs.keys()):
                        walkSeq = self.walkSeqs[lane]
                        if walkSeq:
                            walkSeq.finish()
                        del self.walkSeqs[lane]
                    avatar.setAnimState('jump', 1.0)

        taskMgr.doMethodLater(4.0, self.gameOverCallback, 'playMovie')

    def exitWinMovie(self):
        taskMgr.remove('playMovie')
        self.winSting.stop()
        self.loseSting.stop()

    def enterCleanup(self):
        self.notify.debug('enterCleanup')

    def exitCleanup(self):
        pass

    def positionInPlace(self, avatar, lane, place):
        place = min(place, len(self.posHprArray[lane]) - 1)
        posH = self.posHprArray[lane][place]
        avatar.setPosHpr(self.raceBoard, posH[0], posH[1], posH[2], posH[3], 0, 0)

    def walkInPlace(self, avatar, lane, place, time):
        place = min(place, len(self.posHprArray[lane]) - 1)
        posH = self.posHprArray[lane][place]

        def stopWalk(raceBoard = self.raceBoard, posH = posH):
            avatar.setAnimState('neutral', 1)
            if raceBoard.isEmpty():
                avatar.setPosHpr(0, 0, 0, 0, 0, 0)
            else:
                avatar.setPosHpr(raceBoard, posH[0], posH[1], posH[2], posH[3], 0, 0)

        posQuat = Quat()
        posQuat.setHpr((posH[3], 0, 0))
        walkSeq = Sequence(Func(avatar.setAnimState, 'walk', 1),
                           avatar.posQuatInterval(time, (posH[0], posH[1], posH[2]), posQuat, other=self.raceBoard),
                           Func(stopWalk))
        self.walkSeqs[str(lane)] = walkSeq
        walkSeq.start()

    def runInPlace(self, avatar, lane, currentPlace, newPlace, time):
        place = min(newPlace, len(self.posHprArray[lane]) - 1)
        step = (place - currentPlace) // 3
        pos1 = self.posHprArray[lane][currentPlace + step]
        pos2 = self.posHprArray[lane][currentPlace + 2 * step]
        pos3 = self.posHprArray[lane][place]

        def stopRun(raceBoard = self.raceBoard, pos3 = pos3):
            avatar.setAnimState('neutral', 1)
            avatar.setPosHpr(raceBoard, pos3[0], pos3[1], pos3[2], pos3[3], 0, 0)

        pos1Quat = Quat()
        pos1Quat.setHpr((pos1[3], 0, 0))
        pos2Quat = Quat()
        pos2Quat.setHpr((pos2[3], 0, 0))
        pos3Quat = Quat()
        pos3Quat.setHpr((pos3[3], 0, 0))
        runSeq = Sequence(Func(avatar.setAnimState, 'run', 1),
                          avatar.posQuatInterval(time / 3.0, (pos1[0], pos1[1], pos1[2]), pos1Quat, other=self.raceBoard),
                          avatar.posQuatInterval(time / 3.0, (pos2[0], pos2[1], pos2[2]), pos2Quat, other=self.raceBoard),
                          avatar.posQuatInterval(time / 3.0, (pos3[0], pos3[1], pos3[2]), pos3Quat, other=self.raceBoard),
                          Func(stopRun))
        self.runSeqs[str(lane)] = runSeq
        runSeq.start()

    def setAvatarChoice(self, choice):
        self.notify.error('setAvatarChoice should not be called on the client')

    def setAvatarChose(self, avId):
        if not self.hasLocalToon:
            return
        self.notify.debug('setAvatarChose: avatar: ' + str(avId) + ' choose a number')

    def setChancePositions(self, positions):
        if not self.hasLocalToon:
            return
        row = 0
        for pos in positions:
            marker = self.chanceMarker.copyTo(render)
            posHpr = self.posHprArray[row][pos]
            marker.setPosHpr(self.raceBoard, posHpr[0], posHpr[1], posHpr[2], posHpr[3] + 180, 0, 0.025)
            marker.setScale(0.7)
            marker.setDepthOffset(1)
            self.chanceMarkers.append(marker)
            row += 1

    def setServerChoices(self, choices, positions, rewards):
        if not self.hasLocalToon:
            return
        for i in range(len(positions)):
            if positions[i] > RaceGameGlobals.NumberToWin:
                positions[i] = RaceGameGlobals.NumberToWin
            if positions[i] < 0:
                positions[i] = 0

        self.notify.debug('setServerChoices: %s positions: %s rewards: %s ' % (choices, positions, rewards))
        self.gameFSM.request('moveAvatars', [choices, positions, rewards])

    def resetPositions(self):
        for avId in self.avIdList:
            self.avatarPositions[avId] = 0
