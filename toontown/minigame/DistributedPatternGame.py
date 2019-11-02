from pandac.PandaModules import *
from toontown.toonbase.ToonBaseGlobal import *
from direct.interval.IntervalGlobal import *
from DistributedMinigame import *
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from toontown.toonbase import ToontownTimer
import PatternGameGlobals
from toontown.toon import ToonHead
from toontown.char import CharDNA
from toontown.char import Char
import ArrowKeys
import random
from toontown.toonbase import ToontownGlobals
import string
from toontown.toonbase import TTLocalizer

class DistributedPatternGame(DistributedMinigame):
    phase4snd = 'phase_4/audio/sfx/'
    ButtonSoundNames = (phase4snd + 'm_match_trumpet.mp3',
     phase4snd + 'm_match_guitar.mp3',
     phase4snd + 'm_match_drums.mp3',
     phase4snd + 'm_match_piano.mp3')
    bgm = 'phase_4/audio/bgm/m_match_bg1.mid'
    strWatch = TTLocalizer.PatternGameWatch
    strGo = TTLocalizer.PatternGameGo
    strRight = TTLocalizer.PatternGameRight
    strWrong = TTLocalizer.PatternGameWrong
    strPerfect = TTLocalizer.PatternGamePerfect
    strBye = TTLocalizer.PatternGameBye
    strWaitingOtherPlayers = TTLocalizer.PatternGameWaitingOtherPlayers
    strPleaseWait = TTLocalizer.PatternGamePleaseWait
    strRound = TTLocalizer.PatternGameRound
    minnieAnimNames = ['up',
     'left',
     'down',
     'right']
    toonAnimNames = ['up',
     'left',
     'down',
     'right',
     'slip-forward',
     'slip-backward',
     'victory']

    def __init__(self, cr):
        DistributedMinigame.__init__(self, cr)
        self.gameFSM = ClassicFSM.ClassicFSM('DistributedPatternGame', [State.State('off', self.enterOff, self.exitOff, ['waitForServerPattern']),
         State.State('waitForServerPattern', self.enterWaitForServerPattern, self.exitWaitForServerPattern, ['showServerPattern', 'cleanup']),
         State.State('showServerPattern', self.enterShowServerPattern, self.exitShowServerPattern, ['getUserInput', 'playBackPatterns', 'cleanup']),
         State.State('getUserInput', self.enterGetUserInput, self.exitGetUserInput, ['waitForPlayerPatterns', 'playBackPatterns', 'cleanup']),
         State.State('waitForPlayerPatterns', self.enterWaitForPlayerPatterns, self.exitWaitForPlayerPatterns, ['playBackPatterns', 'cleanup', 'checkGameOver']),
         State.State('playBackPatterns', self.enterPlayBackPatterns, self.exitPlayBackPatterns, ['checkGameOver', 'cleanup']),
         State.State('checkGameOver', self.enterCheckGameOver, self.exitCheckGameOver, ['waitForServerPattern', 'cleanup']),
         State.State('cleanup', self.enterCleanup, self.exitCleanup, [])], 'off', 'cleanup')
        self.addChildGameFSM(self.gameFSM)
        self.arrowColor = VBase4(1, 0, 0, 1)
        self.xColor = VBase4(1, 0, 0, 1)
        self.celebrate = 0
        self.oldBgColor = None
        self.trans = VBase4(1, 0, 0, 0)
        self.opaq = VBase4(1, 0, 0, 1)
        self.normalTextColor = VBase4(0.537, 0.84, 0.33, 1.0)
        self.__otherToonIndex = {}
        return

    def getTitle(self):
        return TTLocalizer.PatternGameTitle

    def getInstructions(self):
        return TTLocalizer.PatternGameInstructions

    def getMaxDuration(self):
        inputDur = PatternGameGlobals.NUM_ROUNDS * PatternGameGlobals.InputTime
        return inputDur * 1.3

    def load(self):
        self.notify.debug('load')
        DistributedMinigame.load(self)
        self.timer = ToontownTimer.ToontownTimer()
        self.timer.posInTopRightCorner()
        self.timer.hide()
        self.room = loader.loadModel('phase_4/models/minigames/matching_room')
        self.buttonSounds = []
        for soundName in self.ButtonSoundNames:
            self.buttonSounds.append(base.loadSfx(soundName))

        self.correctSound = base.loadSfx('phase_4/audio/sfx/MG_pos_buzzer.wav')
        self.incorrectSound = base.loadSfx('phase_4/audio/sfx/MG_neg_buzzer.wav')
        self.perfectSound = base.loadSfx('phase_4/audio/sfx/MG_win.mp3')
        self.fallSound = base.loadSfx('phase_4/audio/sfx/MG_Tag_A.mp3')
        self.music = base.loadMusic(self.bgm)
        self.waitingText = DirectLabel(text=self.strPleaseWait, text_fg=(0.9, 0.9, 0.9, 1.0), frameColor=(1, 1, 1, 0), text_font=ToontownGlobals.getSignFont(), pos=(0, 0, -.78), scale=0.12)
        self.roundText = DirectLabel(text=self.strRound % 1, text_fg=self.normalTextColor, frameColor=(1, 1, 1, 0), text_font=ToontownGlobals.getSignFont(), pos=(0.014, 0, -.84), scale=0.12)
        self.roundText.hide()
        self.waitingText.hide()
        matchingGameGui = loader.loadModel('phase_3.5/models/gui/matching_game_gui')
        minnieArrow = matchingGameGui.find('**/minnieArrow')
        minnieX = matchingGameGui.find('**/minnieX')
        minnieCircle = matchingGameGui.find('**/minnieCircle')
        self.arrows = [None] * 5
        for x in range(0, 5):
            self.arrows[x] = minnieArrow.copyTo(hidden)
            self.arrows[x].hide()

        self.xs = [None] * 5
        for x in range(0, 5):
            self.xs[x] = minnieX.copyTo(hidden)
            self.xs[x].hide()

        self.statusBalls = []
        self.totalMoves = PatternGameGlobals.INITIAL_ROUND_LENGTH + PatternGameGlobals.ROUND_LENGTH_INCREMENT * (PatternGameGlobals.NUM_ROUNDS - 1)
        for x in range(0, 4):
            self.statusBalls.append([None] * self.totalMoves)

        for x in range(0, 4):
            for y in range(0, self.totalMoves):
                self.statusBalls[x][y] = minnieCircle.copyTo(hidden)
                self.statusBalls[x][y].hide()

        minnieArrow.removeNode()
        minnieX.removeNode()
        minnieCircle.removeNode()
        matchingGameGui.removeNode()
        self.minnie = Char.Char()
        m = self.minnie
        dna = CharDNA.CharDNA()
        dna.newChar('mn')
        m.setDNA(dna)
        m.setName(TTLocalizer.Minnie)
        m.reparentTo(hidden)
        self.backRowHome = Point3(3, 11, 0)
        self.backRowXSpacing = 1.8
        self.frontRowHome = Point3(0, 18, 0)
        self.frontRowXSpacing = 3.0
        self.stdNumDanceStepPingFrames = self.minnie.getNumFrames(self.minnieAnimNames[0])
        self.stdNumDanceStepPingPongFrames = self.__numPingPongFrames(self.stdNumDanceStepPingFrames)
        self.buttonPressDelayPercent = (self.stdNumDanceStepPingFrames - 1.0) / self.stdNumDanceStepPingPongFrames
        self.animPlayRates = []
        animPlayRate = 1.4
        animPlayRateMult = 1.06
        for i in range(PatternGameGlobals.NUM_ROUNDS):
            self.animPlayRates.append(animPlayRate)
            animPlayRate *= animPlayRateMult

        return

    def unload(self):
        self.notify.debug('unload')
        DistributedMinigame.unload(self)
        self.timer.destroy()
        del self.timer
        del self.lt
        del self.buttonSounds
        del self.music
        del self.__otherToonIndex
        del self.correctSound
        del self.incorrectSound
        del self.perfectSound
        del self.fallSound
        self.waitingText.destroy()
        del self.waitingText
        self.roundText.destroy()
        del self.roundText
        for x in self.arrowDict.values():
            x[0].removeNode()
            x[1].removeNode()
            if len(x) == 3:
                for y in x[2]:
                    y.removeNode()

        del self.arrowDict
        for x in self.arrows:
            if x:
                x.removeNode()

        del self.arrows
        for x in self.xs:
            if x:
                x.removeNode()

        del self.xs
        for x in self.statusBalls:
            if x:
                for y in x:
                    if y:
                        y.removeNode()
                        del y

        del self.statusBalls
        self.room.removeNode()
        del self.room
        self.minnie.delete()
        del self.minnie
        self.removeChildGameFSM(self.gameFSM)
        del self.gameFSM

    def onstage(self):
        self.notify.debug('onstage')
        DistributedMinigame.onstage(self)
        self.arrowDict = {}
        self.lt = base.localAvatar
        camera.reparentTo(render)
        camera.setPosHpr(0.0, -14.59, 10.56, 0.0, -16.39, 0.0)
        base.camLens.setFov(24.66)
        NametagGlobals.setGlobalNametagScale(0.6)
        self.arrowKeys = ArrowKeys.ArrowKeys()
        self.room.reparentTo(render)
        self.room.setPosHpr(0.0, 18.39, -ToontownGlobals.FloorOffset, 0.0, 0.0, 0.0)
        self.room.setScale(1)
        for anim in self.minnieAnimNames:
            self.minnie.pose(anim, 0)

        for anim in self.toonAnimNames:
            self.lt.pose(anim, 0)

        self.minnieAnimSpeedMult = {}
        self.toonAnimSpeedMult = {}
        for anim in self.minnieAnimNames:
            numFrames = self.minnie.getNumFrames(anim)
            self.minnieAnimSpeedMult[anim] = float(self.__numPingPongFrames(numFrames)) / float(self.stdNumDanceStepPingPongFrames)

        for anim in self.toonAnimNames:
            numFrames = self.lt.getNumFrames(anim)
            self.toonAnimSpeedMult[anim] = float(self.__numPingPongFrames(numFrames)) / float(self.stdNumDanceStepPingPongFrames)

        lt = self.lt
        lt.reparentTo(render)
        lt.useLOD(1000)
        lt.setPos(-3.5, 11, 0.0)
        lt.setScale(1)
        self.makeToonLookatCamera(lt)
        lt.loop('neutral')
        lt.startBlink()
        lt.startLookAround()
        self.arrowDict['lt'] = [self.arrows.pop(), self.xs.pop(), self.statusBalls.pop()]
        jj = self.lt.nametag3d
        for k in range(0, 2):
            self.arrowDict['lt'][k].setBillboardAxis()
            self.arrowDict['lt'][k].setBin('fixed', 100)
            self.arrowDict['lt'][k].reparentTo(jj)
            if k == 0:
                self.arrowDict['lt'][k].setScale(2.5)
                self.arrowDict['lt'][k].setColor(self.arrowColor)
            else:
                self.arrowDict['lt'][k].setScale(4, 4, 4)
                self.arrowDict['lt'][k].setColor(self.xColor)
            self.arrowDict['lt'][k].setPos(0, 0, 1)

        self.formatStatusBalls(self.arrowDict['lt'][2], jj)
        m = self.minnie
        m.reparentTo(render)
        m.setPos(-1.6, 20, 0)
        m.setScale(1)
        self.makeToonLookatCamera(m)
        m.loop('neutral')
        m.startBlink()
        self.minnie.nametag.manage(base.marginManager)
        self.minnie.startEarTask()
        self.minnie.setPickable(0)
        self.minnie.nametag.getNametag3d().setChatWordwrap(8)
        self.arrowDict['m'] = [self.arrows.pop(), self.xs.pop()]
        jj = self.minnie.nametag3d
        for k in range(0, 2):
            self.arrowDict['m'][k].setBillboardAxis()
            self.arrowDict['m'][k].setBin('fixed', 100)
            self.arrowDict['m'][k].setColor(self.arrowColor)
            self.arrowDict['m'][k].reparentTo(jj)
            self.arrowDict['m'][k].setScale(4)
            self.arrowDict['m'][k].setPos(0, 0, 1.7)

        base.playMusic(self.music, looping=1, volume=1)

    def offstage(self):
        self.notify.debug('offstage')
        DistributedMinigame.offstage(self)
        self.music.stop()
        base.camLens.setFov(ToontownGlobals.DefaultCameraFov)
        NametagGlobals.setGlobalNametagScale(1.0)
        self.arrowKeys.destroy()
        del self.arrowKeys
        self.room.reparentTo(hidden)
        self.roundText.hide()
        self.minnie.nametag.unmanage(base.marginManager)
        self.minnie.stopEarTask()
        self.minnie.stop()
        self.minnie.stopBlink()
        self.minnie.reparentTo(hidden)
        self.lt.setScale(1)
        for avId in self.remoteAvIdList:
            toon = self.getAvatar(avId)
            if toon:
                toon.setScale(1)

        for avId in self.avIdList:
            av = self.getAvatar(avId)
            if av:
                av.resetLOD()
                for anim in self.toonAnimNames:
                    av.setPlayRate(1.0, anim)

    def setGameReady(self):
        if not self.hasLocalToon:
            return
        self.notify.debug('setGameReady')
        if DistributedMinigame.setGameReady(self):
            return
        for avId in self.remoteAvIdList:
            toon = self.getAvatar(avId)
            if toon:
                self.arrowDict[avId] = [self.arrows.pop(), self.xs.pop(), self.statusBalls.pop()]
                jj = toon.nametag3d
                for k in range(0, 2):
                    self.arrowDict[avId][k].setBillboardAxis()
                    self.arrowDict[avId][k].setBin('fixed', 100)
                    self.arrowDict[avId][k].reparentTo(jj)
                    if k == 0:
                        self.arrowDict[avId][k].setScale(2.5)
                        self.arrowDict[avId][k].setColor(self.arrowColor)
                    else:
                        self.arrowDict[avId][k].setScale(4, 4, 4)
                        self.arrowDict[avId][k].setColor(self.xColor)
                    self.arrowDict[avId][k].setPos(0, 0, 1)

                self.formatStatusBalls(self.arrowDict[avId][2], jj)
                toon.reparentTo(render)
                toon.useLOD(1000)
                toon.setPos(self.getBackRowPos(avId))
                toon.setScale(0.9)
                self.makeToonLookatCamera(toon)
                for anim in self.toonAnimNames:
                    toon.pose(anim, 0)

                toon.loop('neutral')

        if self.isSinglePlayer():
            self.waitingText['text'] = self.strPleaseWait
        else:
            self.waitingText['text'] = self.strWaitingOtherPlayers
        self.animTracks = {}
        for avId in self.avIdList:
            self.animTracks[avId] = None

        self.__initGameVars()
        return

    def setGameStart(self, timestamp):
        if not self.hasLocalToon:
            return
        self.notify.debug('setGameStart')
        DistributedMinigame.setGameStart(self, timestamp)
        self.gameFSM.request('waitForServerPattern')

    def __initGameVars(self):
        self.round = 0
        self.perfectGame = 1

    def __numPingPongFrames(self, numFrames):
        return numFrames * 2 - 1

    def makeToonLookatCamera(self, toon):
        toon.headsUp(camera)

    def setText(self, t, newtext):
        t['text'] = newtext

    def setTextFG(self, t, fg):
        t['text_fg'] = fg

    def getWalkTrack(self, toon, posList, startPos = None, lookAtCam = 1, endHeading = 180):
        walkSpeed = 7
        origPos = toon.getPos()
        origHpr = toon.getHpr()
        track = Sequence(Func(toon.loop, 'run'))
        if startPos:
            toon.setPos(startPos)
            track.append(Func(toon.setPos, startPos))
        for endPos in posList:
            toon.headsUp(Point3(endPos))
            track.append(Func(toon.setHpr, Point3(toon.getH(), 0, 0)))
            lastPos = toon.getPos()
            distance = Vec3(endPos - lastPos).length()
            duration = distance / walkSpeed
            toon.setPos(endPos)
            track.append(LerpPosInterval(toon, duration=duration, pos=Point3(endPos), startPos=Point3(lastPos)))

        if lookAtCam:
            saveHpr = toon.getHpr()
            toon.headsUp(camera)
            endHeading = toon.getHpr()[0]
            toon.setHpr(saveHpr)
        curHeading = toon.getH()
        if endHeading - curHeading > 180.0:
            endHeading -= 360
        elif endHeading - curHeading < -180.0:
            endHeading += 360
        endHpr = Point3(endHeading, 0, 0)
        duration = abs(endHeading - curHeading) / 180.0 * 0.3
        track.extend([Func(toon.loop, 'walk'), LerpHprInterval(toon, duration, endHpr), Func(toon.loop, 'neutral')])
        toon.setPos(origPos)
        toon.setHpr(origHpr)
        return track

    def getDanceStepDuration(self):
        numFrames = self.stdNumDanceStepPingPongFrames
        return numFrames / abs(self.animPlayRate * self.minnieAnimSpeedMult[self.minnieAnimNames[0]] * self.minnie.getFrameRate(self.minnieAnimNames[0]))

    def __getDanceStepAnimTrack(self, toon, anim, speedScale):
        numFrames = toon.getNumFrames(anim)
        return Sequence(Func(toon.pingpong, anim, fromFrame=0, toFrame=numFrames - 1), Wait(self.getDanceStepDuration()))

    def __getMinnieDanceStepAnimTrack(self, minnie, direction):
        animName = self.minnieAnimNames[direction]
        return self.__getDanceStepAnimTrack(minnie, animName, self.minnieAnimSpeedMult[animName])

    def __getToonDanceStepAnimTrack(self, toon, direction):
        animName = self.toonAnimNames[direction]
        return self.__getDanceStepAnimTrack(toon, animName, self.toonAnimSpeedMult[animName])

    def getDanceStepButtonSoundTrack(self, index):
        duration = self.getDanceStepDuration()
        wait = duration * self.buttonPressDelayPercent
        return Sequence(Wait(wait), Func(base.playSfx, self.__getButtonSound(index)), Wait(duration - wait))

    def getDanceArrowAnimTrack(self, toonID, pattern, speedy):
        track = Sequence()
        track.append(Func(self.showArrow, toonID))
        for buttonIndex in pattern:
            track.append(self.getDanceArrowSingleTrack(toonID, buttonIndex, speedy))

        track.append(Func(self.hideArrow, toonID))
        return track

    def changeArrow(self, toonID, index):
        self.arrowDict[toonID][0].setR(-(90 - 90 * index))

    def showArrow(self, toonID):
        self.arrowDict[toonID][0].show()

    def hideArrow(self, toonID):
        self.arrowDict[toonID][0].hide()

    def showX(self, toonID):
        self.arrowDict[toonID][1].show()

    def hideX(self, toonID):
        self.arrowDict[toonID][1].hide()

    def celebrated(self):
        self.celebrate = 1

    def returnCelebrationIntervals(self, turnOn):
        ri = []
        if turnOn:
            ri.append(ActorInterval(actor=self.lt, animName='victory', duration=5.5))
        else:
            ri.append(Func(self.lt.loop, 'neutral'))
        for avId in self.remoteAvIdList:
            toon = self.getAvatar(avId)
            if toon:
                if turnOn:
                    ri.append(ActorInterval(actor=toon, animName='victory', duration=5.5))
                else:
                    ri.append(Func(toon.loop, 'neutral'))

        if len(self.remoteAvIdList) == 0:
            return ri
        else:
            return Parallel(ri)

    def formatStatusBalls(self, sb, jj):
        for x in range(0, self.totalMoves):
            sb[x].setBillboardAxis()
            sb[x].setBin('fixed', 100)
            sb[x].reparentTo(jj)
            sb[x].setScale(1)
            xpos = +(int(self.totalMoves / 2) * 0.25) - 0.25 * x
            sb[x].setPos(xpos, 0, 0.3)

    def showStatusBalls(self, toonID):
        sb = self.arrowDict[toonID][2]
        for x in range(0, len(self.__serverPattern)):
            sb[x].setColor(1, 1, 1, 1)
            sb[x].show()

    def hideStatusBalls(self, toonID):
        sb = self.arrowDict[toonID][2]
        for x in range(0, len(sb)):
            sb[x].hide()

    def colorStatusBall(self, toonID, which, good):
        if good:
            self.arrowDict[toonID][2][which].setColor(0, 1, 0, 1)
        else:
            self.arrowDict[toonID][2][which].setColor(1, 0, 0, 1)

    def getDanceArrowSingleTrack(self, toonID, index, speedy):
        duration = self.getDanceStepDuration()
        wait = duration * self.buttonPressDelayPercent
        d = duration - wait
        if speedy:
            track = Sequence(Func(self.changeArrow, toonID, index), Wait(wait))
        else:
            track = Sequence(Func(self.changeArrow, toonID, index), Wait(wait), LerpColorInterval(self.arrowDict[toonID][0], d, self.trans, self.opaq))
        return track

    def getDanceSequenceAnimTrack(self, toon, pattern):
        getDanceStepTrack = self.__getToonDanceStepAnimTrack
        if toon == self.minnie:
            getDanceStepTrack = self.__getMinnieDanceStepAnimTrack
        tracks = Sequence()
        for direction in pattern:
            tracks.append(getDanceStepTrack(toon, direction))

        if len(pattern):
            tracks.append(Func(toon.loop, 'neutral'))
        return tracks

    def getDanceSequenceButtonSoundTrack(self, pattern):
        track = Sequence()
        for buttonIndex in pattern:
            track.append(self.getDanceStepButtonSoundTrack(buttonIndex))

        return track

    def __getRowPos(self, rowHome, xSpacing, index, numSpots):
        xOffset = xSpacing * index - xSpacing * (numSpots - 1) / 2.0
        return rowHome + Point3(xOffset, 0, 0)

    def getBackRowPos(self, avId):
        index = self.remoteAvIdList.index(avId)
        return self.__getRowPos(self.backRowHome, self.backRowXSpacing, index, len(self.remoteAvIdList))

    def getFrontRowPos(self, avId):
        index = self.avIdList.index(avId)
        return self.__getRowPos(self.frontRowHome, self.frontRowXSpacing, index, len(self.avIdList))

    def __setMinnieChat(self, str, giggle):
        str = string.replace(str, '%s', self.getAvatar(self.localAvId).getName())
        self.minnie.setChatAbsolute(str, CFSpeech)
        if giggle:
            self.minnie.playDialogue('statementA', 1)

    def __clearMinnieChat(self):
        self.minnie.clearChat()

    def enterOff(self):
        self.notify.debug('enterOff')

    def exitOff(self):
        pass

    def enterWaitForServerPattern(self):
        self.notify.debug('enterWaitForServerPattern')
        self.sendUpdate('reportPlayerReady', [])

    def setPattern(self, pattern):
        if not self.hasLocalToon:
            return
        self.notify.debug('setPattern: ' + str(pattern))
        self.__serverPattern = pattern
        self.gameFSM.request('showServerPattern')

    def exitWaitForServerPattern(self):
        pass

    def enterShowServerPattern(self):
        self.notify.debug('enterShowServerPattern')
        self.round += 1
        self.roundText.show()
        self.roundText.setScale(0.12)
        self.roundText['text'] = self.strRound % self.round
        self.animPlayRate = self.animPlayRates[self.round - 1]
        for avId in self.avIdList:
            toon = self.getAvatar(avId)
            if toon:
                for anim in self.toonAnimNames:
                    toon.setPlayRate(self.animPlayRate * self.toonAnimSpeedMult[anim], anim)

        for anim in self.minnieAnimNames:
            self.minnie.setPlayRate(self.animPlayRate * self.minnieAnimSpeedMult[anim], anim)

        text = self.strWatch
        danceTrack = self.getDanceSequenceAnimTrack(self.minnie, self.__serverPattern)
        arrowTrack = self.getDanceArrowAnimTrack('m', self.__serverPattern, 0)
        soundTrack = self.getDanceSequenceButtonSoundTrack(self.__serverPattern)
        self.showTrack = Sequence(Func(self.__setMinnieChat, text, 1), Wait(0.5), Parallel(danceTrack, soundTrack, arrowTrack), Wait(0.2), Func(self.__clearMinnieChat), Func(self.gameFSM.request, 'getUserInput'))
        self.showTrack.start()

    def exitShowServerPattern(self):
        if self.showTrack.isPlaying():
            self.showTrack.pause()
        del self.showTrack

    def enterGetUserInput(self):
        self.notify.debug('enterGetUserInput')
        self.setupTrack = None
        self.proceedTrack = None

        def startTimer(self = self):
            self.currentStartTime = globalClock.getFrameTime()
            self.timer.show()
            self.timer.countdown(PatternGameGlobals.InputTime, self.__handleInputTimeout)

        def enableKeys(self = self):

            def keyPress(self, index):
                self.__pressHandler(index)

            def keyRelease(self, index):
                self.__releaseHandler(index)

            self.arrowKeys.setPressHandlers([lambda self = self, keyPress = keyPress: keyPress(self, 0),
             lambda self = self, keyPress = keyPress: keyPress(self, 2),
             lambda self = self, keyPress = keyPress: keyPress(self, 3),
             lambda self = self, keyPress = keyPress: keyPress(self, 1)])
            self.arrowKeys.setReleaseHandlers([lambda self = self, keyRelease = keyRelease: keyRelease(self, 0),
             lambda self = self, keyRelease = keyRelease: keyRelease(self, 2),
             lambda self = self, keyRelease = keyRelease: keyRelease(self, 3),
             lambda self = self, keyRelease = keyRelease: keyRelease(self, 1)])

        self.__localPattern = []
        self.__otherToonIndex.clear()
        self.showStatusBalls('lt')
        for avId in self.remoteAvIdList:
            self.showStatusBalls(avId)
            self.__otherToonIndex[avId] = 0

        self.setupTrack = Sequence(Func(self.__setMinnieChat, self.strGo, 0), Func(self.setText, self.roundText, TTLocalizer.PatternGameGo), Func(self.roundText.setScale, 0.3), Func(enableKeys), Func(startTimer), Wait(0.8), Func(self.__clearMinnieChat), Func(self.setText, self.roundText, ' '), Func(self.roundText.setScale, 0.12), Func(self.setTextFG, self.roundText, self.normalTextColor))
        self.setupTrack.start()
        return

    def __handleInputTimeout(self):
        self.__doneGettingInput(self.__localPattern)

    def __pressHandler(self, index):
        self.__buttonPressed(index)

    def __releaseHandler(self, index):
        pass

    def remoteButtonPressed(self, avId, index, wrong):
        if not self.hasLocalToon:
            return
        if self.gameFSM.getCurrentState().getName() not in ['getUserInput', 'waitForPlayerPatterns']:
            return
        if avId != self.localAvId:
            if self.animTracks[avId]:
                self.animTracks[avId].finish()
            av = self.getAvatar(avId)
            if wrong:
                acts = ['slip-forward', 'slip-backward']
                ag = random.choice(acts)
                self.arrowDict[avId][0].hide()
                self.animTracks[avId] = Sequence(Func(self.showX, avId), Func(self.colorStatusBall, avId, self.__otherToonIndex[avId], 0), ActorInterval(actor=av, animName=ag, duration=2.35), Func(av.loop, 'neutral'), Func(self.hideX, avId))
            else:
                self.colorStatusBall(avId, self.__otherToonIndex[avId], 1)
                arrowTrack = self.getDanceArrowAnimTrack(avId, [index], 1)
                potTrack = self.getDanceSequenceAnimTrack(av, [index])
                self.animTracks[avId] = Parallel(potTrack, arrowTrack)
            self.__otherToonIndex[avId] += 1
            self.animTracks[avId].start()

    def __getButtonSound(self, index):
        return self.buttonSounds[index]

    def __buttonPressed(self, index):
        if len(self.__localPattern) >= len(self.__serverPattern):
            return
        if self.animTracks[self.localAvId]:
            self.animTracks[self.localAvId].finish()
        badd = 0
        if index != self.__serverPattern[len(self.__localPattern)]:
            badd = 1
            acts = ['slip-forward', 'slip-backward']
            ag = random.choice(acts)
            self.animTracks[self.localAvId] = Sequence(Func(self.showX, 'lt'), Func(self.colorStatusBall, 'lt', len(self.__localPattern), 0), ActorInterval(actor=self.lt, animName=ag, duration=2.35), Func(self.lt.loop, 'neutral'), Func(self.hideX, 'lt'))
            self.arrowDict['lt'][0].hide()
            base.playSfx(self.fallSound)
        else:
            self.colorStatusBall('lt', len(self.__localPattern), 1)
            base.playSfx(self.__getButtonSound(index))
            arrowTrack = self.getDanceArrowAnimTrack('lt', [index], 1)
            potTrack = self.getDanceSequenceAnimTrack(self.lt, [index])
            self.animTracks[self.localAvId] = Parallel(potTrack, arrowTrack)
        self.sendUpdate('reportButtonPress', [index, badd])
        self.animTracks[self.localAvId].start()
        self.__localPattern.append(index)
        if len(self.__localPattern) == len(self.__serverPattern) or badd:
            self.__doneGettingInput(self.__localPattern)

    def __doneGettingInput(self, pattern):
        self.arrowKeys.setPressHandlers(self.arrowKeys.NULL_HANDLERS)
        self.currentTotalTime = globalClock.getFrameTime() - self.currentStartTime
        self.proceedTrack = Sequence(Wait(self.getDanceStepDuration()), Func(self.sendUpdate, 'reportPlayerPattern', [pattern, self.currentTotalTime]), Func(self.gameFSM.request, 'waitForPlayerPatterns'))
        self.proceedTrack.start()

    def exitGetUserInput(self):
        self.timer.stop()
        self.timer.hide()
        self.arrowKeys.setPressHandlers(self.arrowKeys.NULL_HANDLERS)
        self.arrowKeys.setReleaseHandlers(self.arrowKeys.NULL_HANDLERS)
        if self.setupTrack and self.setupTrack.isPlaying():
            self.setupTrack.pause()
        if self.proceedTrack and self.proceedTrack.isPlaying():
            self.proceedTrack.pause()
        del self.setupTrack
        del self.proceedTrack
        self.__clearMinnieChat()

    def enterWaitForPlayerPatterns(self):
        self.notify.debug('enterWaitForPlayerPatterns')

    def setPlayerPatterns(self, pattern1, pattern2, pattern3, pattern4, fastestAvId):
        if not self.hasLocalToon:
            return
        self.fastestAvId = fastestAvId
        self.notify.debug('setPlayerPatterns:' + ' pattern1:' + str(pattern1) + ' pattern2:' + str(pattern2) + ' pattern3:' + str(pattern3) + ' pattern4:' + str(pattern4))
        self.playerPatterns = {}
        patterns = [pattern1,
         pattern2,
         pattern3,
         pattern4]
        for i in range(len(self.avIdList)):
            self.playerPatterns[self.avIdList[i]] = patterns[i]

        self.gameFSM.request('playBackPatterns')

    def exitWaitForPlayerPatterns(self):
        self.waitingText.hide()

    def enterPlayBackPatterns(self):
        self.notify.debug('enterPlayBackPatterns')
        if self.fastestAvId == self.localAvId:
            self.roundText.setScale(0.1)
            if self.numPlayers != 2:
                self.roundText['text'] = TTLocalizer.PatternGameFastest
            else:
                self.roundText['text'] = TTLocalizer.PatternGameFaster
            jumpTrack = Sequence(ActorInterval(actor=self.lt, animName='jump', duration=1.7), Func(self.lt.loop, 'neutral'))
        elif self.fastestAvId == 0:
            if self.round == PatternGameGlobals.NUM_ROUNDS:
                self.roundText['text'] = ' '
            else:
                self.roundText.setScale(0.1)
                self.roundText['text'] = TTLocalizer.PatternGameYouCanDoIt
            jumpTrack = Sequence(Wait(0.5), Wait(0.5))
        elif self.fastestAvId == 1:
            self.roundText.setScale(0.1)
            self.roundText['text'] = TTLocalizer.PatternGameGreatJob
            jumpTrack = Sequence(Wait(0.5), Wait(0.5))
        else:
            self.roundText.setScale(0.08)
            av = self.getAvatar(self.fastestAvId)
            jumpTrack = Sequence(ActorInterval(actor=av, animName='jump', duration=1.7), Func(av.loop, 'neutral'))
            if self.numPlayers != 2:
                rewardStr = TTLocalizer.PatternGameOtherFastest
            else:
                rewardStr = TTLocalizer.PatternGameOtherFaster
            self.roundText['text'] = av.getName() + rewardStr
        success = self.playerPatterns[self.localAvId] == self.__serverPattern
        self.hideStatusBalls('lt')
        for avId in self.remoteAvIdList:
            self.hideStatusBalls(avId)

        if success:
            sound = self.correctSound
            text = self.strRight
        else:
            self.perfectGame = 0
            sound = self.incorrectSound
            text = self.strWrong
        soundTrack = Sequence(Func(base.playSfx, sound), Wait(1.6))
        textTrack = Sequence(Wait(0.2), Func(self.__setMinnieChat, text, 0), Wait(1.3), Func(self.__clearMinnieChat))
        self.playBackPatternsTrack = Sequence(Parallel(soundTrack, textTrack, jumpTrack), Func(self.gameFSM.request, 'checkGameOver'))
        self.playBackPatternsTrack.start()

    def exitPlayBackPatterns(self):
        if self.playBackPatternsTrack.isPlaying():
            self.playBackPatternsTrack.pause()
        del self.playBackPatternsTrack

    def enterCheckGameOver(self):
        self.notify.debug('enterCheckGameOver')
        self.__winTrack = None
        if self.round < PatternGameGlobals.NUM_ROUNDS:
            self.gameFSM.request('waitForServerPattern')
        else:
            text = self.strBye
            sound = None
            delay = 2.0
            if self.perfectGame:
                text = self.strPerfect
                sound = self.perfectSound
                delay = 2.2
            if self.celebrate:
                text = TTLocalizer.PatternGameImprov
                self.__winTrack = Sequence(Func(self.__setMinnieChat, text, 1), Func(base.playSfx, self.perfectSound), Sequence(self.returnCelebrationIntervals(1)), Sequence(self.returnCelebrationIntervals(0)), Func(self.__clearMinnieChat), Func(self.gameOver))
            else:
                self.__winTrack = Sequence(Func(self.__setMinnieChat, text, 1), Func(base.playSfx, sound), Wait(delay), Func(self.__clearMinnieChat), Func(self.gameOver))
            self.__winTrack.start()
        return

    def exitCheckGameOver(self):
        if self.__winTrack and self.__winTrack.isPlaying():
            self.__winTrack.pause()
        del self.__winTrack

    def enterCleanup(self):
        self.notify.debug('enterCleanup')
        for track in self.animTracks.values():
            if track and track.isPlaying():
                track.pause()

        del self.animTracks

    def exitCleanup(self):
        pass
