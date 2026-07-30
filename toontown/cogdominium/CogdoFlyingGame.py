from direct.showbase.DirectObject import DirectObject
from direct.task.Task import Task
from direct.showbase.RandomNumGen import RandomNumGen
from direct.interval.FunctionInterval import Wait
from direct.interval.IntervalGlobal import Func
from direct.interval.MetaInterval import Sequence, Parallel
from toontown.toonbase import TTLocalizer
from . import CogdoFlyingGameGlobals as Globals
from .CogdoFlyingLocalPlayer import CogdoFlyingLocalPlayer
from .CogdoGameAudioManager import CogdoGameAudioManager
from .CogdoFlyingPlayer import CogdoFlyingPlayer
from .CogdoFlyingObjects import CogdoFlyingGatherable
from .CogdoFlyingObstacles import CogdoFlyingObstacle
from .CogdoFlyingLegalEagle import CogdoFlyingLegalEagle
from .CogdoFlyingGuiManager import CogdoFlyingGuiManager
from .CogdoFlyingLevel import CogdoFlyingLevelFactory
from .CogdoFlyingGameMovies import CogdoFlyingGameIntro, CogdoFlyingGameFinish

class CogdoFlyingGame(DirectObject):
    notify = directNotify.newCategory('CogdoFlyingGame')
    UpdateTaskName = 'CogdoFlyingGameUpdate'
    FirstPressOfCtrlTaskName = 'FirstPressOfCtrlTask'

    def __init__(self, distGame):
        self.distGame = distGame
        self.toonId2Player = {}
        self.players = []
        self.index2LegalEagle = {}
        self.legalEagles = []
        self.isGameComplete = False
        self._hints = {'targettedByEagle': False,
         'invulnerable': False}

    def _initLegalEagles(self):
        nestIndex = 1
        nests = self.level.root.findAllMatches('**/%s;+s' % Globals.Level.LegalEagleNestName)
        for nest in nests:
            legalEagle = CogdoFlyingLegalEagle(nest, nestIndex)
            self.legalEagles.append(legalEagle)
            self.index2LegalEagle[nestIndex] = legalEagle
            nestIndex += 1

    def initPlayers(self):
        for toonId in self.distGame.getToonIds():
            toon = self.distGame.getToon(toonId)
            i = self.distGame.getToonIds().index(toon.doId)
            if toon is not None:
                if toon.isLocal():
                    player = CogdoFlyingLocalPlayer(toon, self, self.level, self.guiMgr)
                    self.localPlayer = player
                    self.localPlayer.setPlayerNumber(i)
                else:
                    player = CogdoFlyingPlayer(toon)
                player.enable()
                self._addPlayer(player)
                self.guiMgr.addToonToProgressMeter(toon)

        return

    def placeEntranceElevator(self, elevator):
        loc = self.level.startPlatform._model.find('**/door_loc')
        offset = loc.getPos(render)
        elevator.setPos(render, offset)

    def load(self):
        self.accept(self.distGame.getRemoteActionEventName(), self.handleRemoteAction)
        self.audioMgr = CogdoGameAudioManager(Globals.Audio.MusicFiles, Globals.Audio.SfxFiles, base.localAvatar, cutoff=Globals.Audio.Cutoff)
        factory = CogdoFlyingLevelFactory(render, Globals.Level.QuadLengthUnits, Globals.Level.QuadVisibilityAhead, Globals.Level.QuadVisibilityBehind, rng=RandomNumGen(self.distGame.doId))
        self.level = factory.createLevel(self.distGame.getSafezoneId())
        self.level.setCamera(camera)
        self.guiMgr = CogdoFlyingGuiManager(self.level)
        self.levelFog = factory.createLevelFog()
        self._initLegalEagles()

    def unload(self):
        self.guiMgr.destroy()
        del self.guiMgr
        self.__stopUpdateTask()
        for player in self.players:
            player.unload()

        del self.players[:]
        self.toonId2Player.clear()
        del self.localPlayer
        for eagle in self.legalEagles:
            eagle.destroy()

        del self.legalEagles[:]
        self.index2LegalEagle.clear()
        self.levelFog.destroy()
        del self.levelFog
        self.level.destroy()
        del self.level
        self.audioMgr.destroy()
        del self.audioMgr
        self.ignoreAll()
        del self.distGame

    def onstage(self):
        self.level.onstage()
        self.levelFog.setVisible(True)
        for eagle in self.legalEagles:
            eagle.onstage()

        self.localPlayer.request('Inactive')

    def offstage(self):
        self.__stopUpdateTask()
        for eagle in self.legalEagles:
            eagle.offstage()

        self.level.offstage()
        self.levelFog.setVisible(False)

    def startIntro(self):
        self._movie = CogdoFlyingGameIntro(self.level, RandomNumGen(self.distGame.doId))
        self._movie.load()
        self._movie.play()
        self.audioMgr.playMusic('normal')

    def endIntro(self):
        self._movie.end()
        self._movie.unload()
        del self._movie
        self.localPlayer.ready()
        self.level.update(0.0)

    def startFinish(self):
        self._movie = CogdoFlyingGameFinish(self.level, self.players)
        self._movie.load()
        self._movie.play()
        self.audioMgr.playMusic('end')

    def endFinish(self):
        self._movie.end()
        self._movie.unload()
        del self._movie
        self.audioMgr.stopMusic()

    def start(self):
        self.level.start(self.distGame.getStartTime())
        self.accept(CogdoFlyingObstacle.EnterEventName, self.handleLocalToonEnterObstacle)
        self.accept(CogdoFlyingObstacle.ExitEventName, self.handleLocalToonExitObstacle)
        self.accept(CogdoFlyingGatherable.EnterEventName, self.handleLocalToonEnterGatherable)
        self.accept(CogdoFlyingLegalEagle.RequestAddTargetEventName, self.handleLocalToonEnterLegalEagleInterest)
        self.accept(CogdoFlyingLegalEagle.RequestAddTargetAgainEventName, self.handleLocalToonAgainLegalEagleInterest)
        self.accept(CogdoFlyingLegalEagle.RequestRemoveTargetEventName, self.handleLocalToonExitLegalEagleInterest)
        self.accept(CogdoFlyingLegalEagle.EnterLegalEagle, self.handleLocalToonEnterLegalEagle)
        self.accept(CogdoFlyingLegalEagle.ChargingToAttackEventName, self.handlePlayerBackpackAttacked)
        self.accept(CogdoFlyingLegalEagle.LockOnToonEventName, self.handlePlayerBackpackTargeted)
        self.accept(CogdoFlyingLegalEagle.CooldownEventName, self.handlePlayerBackpackNormal)
        self.accept(CogdoFlyingGuiManager.EagleTargetingLocalPlayerEventName, self.handleLocalPlayerTargetedByEagle)
        self.accept(CogdoFlyingGuiManager.EagleAttackingLocalPlayerEventName, self.handleLocalPlayerAttackedByEagle)
        self.accept(CogdoFlyingGuiManager.ClearMessageDisplayEventName, self.handleClearGuiMessage)
        self.accept(CogdoFlyingGuiManager.InvulnerableEventName, self.handleLocalPlayerInvulnerable)
        self.acceptOnce(CogdoFlyingGuiManager.FirstPressOfCtrlEventName, self.handleLocalPlayerFirstPressOfCtrl)
        self.acceptOnce(CogdoFlyingGuiManager.PickedUpFirstPropellerEventName, self.handleLocalPlayerPickedUpFirstPropeller)
        self.acceptOnce(CogdoFlyingGuiManager.StartRunningOutOfTimeMusicEventName, self.handleTimeRunningOut)
        self.acceptOnce(CogdoFlyingLocalPlayer.PlayWaitingMusicEventName, self.handlePlayWaitingMusic)
        self.acceptOnce(CogdoFlyingLocalPlayer.RanOutOfTimeEventName, self.handleLocalPlayerRanOutOfTime)
        self.__startUpdateTask()
        self.isGameComplete = False
        if __debug__ and base.config.GetBool('schellgames-dev', True):
            self.acceptOnce('end', self.guiMgr.forceTimerDone)

            def toggleFog():
                self.levelFog.setVisible(not self.levelFog.isVisible())

            self.accept('home', toggleFog)
        for eagle in self.legalEagles:
            eagle.gameStart(self.distGame.getStartTime())

        for player in self.players:
            player.start()

        self.guiMgr.onstage()
        if not Globals.Dev.InfiniteTimeLimit:
            self.guiMgr.startTimer(Globals.Gameplay.SecondsUntilGameOver, self._handleTimerExpired, keepHidden=True)

    def exit(self):
        self.ignore(CogdoFlyingObstacle.EnterEventName)
        self.ignore(CogdoFlyingObstacle.ExitEventName)
        self.ignore(CogdoFlyingGatherable.EnterEventName)
        self.ignore(CogdoFlyingLegalEagle.ChargingToAttackEventName)
        self.ignore(CogdoFlyingLegalEagle.LockOnToonEventName)
        self.ignore(CogdoFlyingLegalEagle.CooldownEventName)
        self.ignore(CogdoFlyingLocalPlayer.RanOutOfTimeEventName)
        taskMgr.remove(CogdoFlyingGame.FirstPressOfCtrlTaskName)
        self.__stopUpdateTask()
        self.ignore(CogdoFlyingLegalEagle.EnterLegalEagle)
        self.ignore(CogdoFlyingLegalEagle.RequestAddTargetEventName)
        self.ignore(CogdoFlyingLegalEagle.RequestAddTargetAgainEventName)
        self.ignore(CogdoFlyingLegalEagle.RequestRemoveTargetEventName)
        self.ignore(CogdoFlyingLocalPlayer.PlayWaitingMusicEventName)
        if __debug__ and base.config.GetBool('schellgames-dev', True):
            self.ignore('end')
            self.ignore('home')
        self.level.update(0.0)
        for eagle in self.legalEagles:
            eagle.gameEnd()

        for player in self.players:
            player.exit()

        self.guiMgr.offstage()

    def _handleTimerExpired(self):
        self.localPlayer.handleTimerExpired()

    def _addPlayer(self, player):
        self.players.append(player)
        self.toonId2Player[player.toon.doId] = player
        toon = player.toon
        self.accept(toon.uniqueName('disable'), self._removePlayer, extraArgs=[toon.doId])

    def _removePlayer(self, toonId):
        if toonId in self.toonId2Player:
            player = self.toonId2Player[toonId]
            self.players.remove(player)
            del self.toonId2Player[toonId]
            self.guiMgr.removeToonFromProgressMeter(player.toon)
            player.exit()
            player.unload()

    def setToonSad(self, toonId):
        player = self.toonId2Player[toonId]
        self.forceClearLegalEagleInterestInToon(toonId)
        if player == self.localPlayer:
            player.goSad()
            self.exit()
        else:
            player.exit()

    def setToonDisconnect(self, toonId):
        player = self.toonId2Player[toonId]
        self.forceClearLegalEagleInterestInToon(toonId)
        if player == self.localPlayer:
            self.exit()
        else:
            player.exit()

    def handleRemoteAction(self, action, data):
        if data != self.localPlayer.toon.doId:
            if action == Globals.AI.GameActions.GotoWinState:
                if self.localPlayer.state in ['WaitingForWin']:
                    self.localPlayer.request('Win')

    def toonDied(self, toonId, elapsedTime):
        player = self.toonId2Player[toonId]
        if player is not None:
            player.died(elapsedTime)
        return

    def toonSpawn(self, toonId, elapsedTime):
        player = self.toonId2Player[toonId]
        if player is not None:
            player.spawn(elapsedTime)
        return

    def toonResetBlades(self, toonId):
        player = self.toonId2Player[toonId]
        if player is not None:
            player.resetBlades()
        return

    def toonSetBlades(self, toonId, fuelState):
        player = self.toonId2Player[toonId]
        if player is not None:
            player.setBlades(fuelState)
        return

    def toonBladeLost(self, toonId):
        player = self.toonId2Player[toonId]
        if player is not None:
            player.bladeLost()
        return

    def handleLocalToonEnterGatherable(self, gatherable):
        if gatherable.wasPickedUp():
            return
        if gatherable.isPowerUp() and gatherable.wasPickedUpByToon(self.localPlayer.toon):
            return
        if gatherable.type in [Globals.Level.GatherableTypes.LaffPowerup, Globals.Level.GatherableTypes.InvulPowerup]:
            self.distGame.d_sendRequestPickup(gatherable.serialNum, gatherable.type)
        elif gatherable.type == Globals.Level.GatherableTypes.Memo:
            self.distGame.d_sendRequestPickup(gatherable.serialNum, gatherable.type)
            gatherable.disable()
        elif gatherable.type == Globals.Level.GatherableTypes.Propeller and self.localPlayer.fuel < 1.0:
            self.distGame.d_sendRequestPickup(gatherable.serialNum, gatherable.type)

    def pickUp(self, toonId, pickupNum, elapsedTime = 0.0):
        self.notify.debugCall()
        player = self.toonId2Player[toonId]
        gatherable = self.level.getGatherable(pickupNum)
        if gatherable is not None:
            if not gatherable.isPowerUp() and not gatherable.wasPickedUp() or gatherable.isPowerUp() and not gatherable.wasPickedUpByToon(player.toon):
                gatherable.pickUp(player.toon, elapsedTime)
                player.handleEnterGatherable(gatherable, elapsedTime)
                if gatherable.type in [Globals.Level.GatherableTypes.InvulPowerup]:
                    if player.toon.isLocal():
                        self.audioMgr.playMusic('invul')
        else:
            self.notify.warning('Trying to pickup gatherable nonetype:%s' % pickupNum)
        return

    def debuffPowerup(self, toonId, pickupType, elapsedTime):
        self.notify.debugCall()
        player = self.toonId2Player[toonId]
        if player.isBuffActive(pickupType):
            if pickupType in [Globals.Level.GatherableTypes.InvulPowerup]:
                if self.guiMgr.isTimeRunningOut():
                    self.audioMgr.playMusic('timeRunningOut')
                else:
                    self.audioMgr.playMusic('normal')
                player.handleDebuffPowerup(pickupType, elapsedTime)

    def handleLocalToonEnterLegalEagle(self, eagle, collEntry):
        if not self.localPlayer.isEnemyHitting() and not self.localPlayer.isInvulnerable():
            collPos = collEntry.getSurfacePoint(render)
            self.localPlayer.handleEnterEnemyHit(eagle, collPos)
            self.distGame.d_sendRequestAction(Globals.AI.GameActions.HitLegalEagle, 0)

    def handleLocalToonEnterObstacle(self, obstacle, collEntry):
        if self.localPlayer.isInvulnerable():
            return
        if obstacle.type == Globals.Level.ObstacleTypes.Whirlwind:
            self.localPlayer.handleEnterWhirlwind(obstacle)
            self.distGame.d_sendRequestAction(Globals.AI.GameActions.HitWhirlwind, 0)
        if obstacle.type == Globals.Level.ObstacleTypes.Fan:
            self.localPlayer.handleEnterFan(obstacle)
        if obstacle.type == Globals.Level.ObstacleTypes.Minion:
            if not self.localPlayer.isEnemyHitting():
                collPos = collEntry.getSurfacePoint(render)
                self.localPlayer.handleEnterEnemyHit(obstacle, collPos)
                self.distGame.d_sendRequestAction(Globals.AI.GameActions.HitMinion, 0)

    def handleLocalToonExitObstacle(self, obstacle, collEntry):
        if obstacle.type == Globals.Level.ObstacleTypes.Fan:
            self.localPlayer.handleExitFan(obstacle)

    def __startUpdateTask(self):
        self.__stopUpdateTask()
        taskMgr.add(self.__updateTask, CogdoFlyingGame.UpdateTaskName, 45)

    def __stopUpdateTask(self):
        taskMgr.remove(CogdoFlyingGame.UpdateTaskName)

    def handleTimeRunningOut(self):
        if self.localPlayer.state not in ['WaitingForWin']:
            self.audioMgr.playMusic('timeRunningOut')
        self.guiMgr.presentTimerGui()
        self.guiMgr.setTemporaryMessage(TTLocalizer.CogdoFlyingGameTimeIsRunningOut)

    def handlePlayWaitingMusic(self):
        self.audioMgr.playMusic('waiting')

    def handleLocalPlayerFirstPressOfCtrl(self):
        self.doMethodLater(3.0, self.guiMgr.setMessage, CogdoFlyingGame.FirstPressOfCtrlTaskName, extraArgs=[''])

    def handleLocalPlayerRanOutOfTime(self):
        self.guiMgr.setMemoCount(0)
        self.distGame.d_sendRequestAction(Globals.AI.GameActions.RanOutOfTimePenalty, 0)
        self.guiMgr.setMessage(TTLocalizer.CogdoFlyingGameTakingMemos)

    def handleClearGuiMessage(self):
        if not self.localPlayer.isInvulnerable():
            self.guiMgr.setMessage('')

    def handleLocalPlayerInvulnerable(self):
        if not self._hints['invulnerable']:
            self.guiMgr.setMessage(TTLocalizer.CogdoFlyingGameYouAreInvincible)
            self._hints['invulnerable'] = True

    def handleLocalPlayerPickedUpFirstPropeller(self):
        self.guiMgr.setMessage(TTLocalizer.CogdoFlyingGamePressCtrlToFly)
        self.guiMgr.presentRefuelGui()

    def handleLocalPlayerTargetedByEagle(self):
        if not self.localPlayer.isInvulnerable() and not self._hints['targettedByEagle']:
            self.guiMgr.setMessage(TTLocalizer.CogdoFlyingGameLegalEagleTargeting)
            self._hints['targettedByEagle'] = True

    def handleLocalPlayerAttackedByEagle(self):
        if not self.localPlayer.isInvulnerable():
            self.guiMgr.setMessage(TTLocalizer.CogdoFlyingGameLegalEagleAttacking)

    def handlePlayerBackpackAttacked(self, toonId):
        if toonId in self.toonId2Player:
            player = self.toonId2Player[toonId]
            player.setBackpackState(Globals.Gameplay.BackpackStates.Attacked)

    def handlePlayerBackpackTargeted(self, toonId):
        if toonId in self.toonId2Player:
            player = self.toonId2Player[toonId]
            player.setBackpackState(Globals.Gameplay.BackpackStates.Targeted)

    def handlePlayerBackpackNormal(self, toonId):
        if toonId in self.toonId2Player:
            player = self.toonId2Player[toonId]
            player.setBackpackState(Globals.Gameplay.BackpackStates.Normal)

    def handleLocalToonEnterLegalEagleInterest(self, index):
        if index in self.index2LegalEagle:
            legalEagle = self.index2LegalEagle[index]
            if not self.localPlayer.isLegalEagleInterestRequestSent(index) and not self.localPlayer.isLegalEagleTarget():
                if self.localPlayer.state in ['WaitingForWin', 'Win']:
                    return
                self.localPlayer.setLegalEagleInterestRequest(index)
                self.distGame.d_sendRequestAction(Globals.AI.GameActions.RequestEnterEagleInterest, index)
        else:
            self.notify.warning("Legal eagle %i isn't in index2LegalEagle dict" % index)

    def handleLocalToonAgainLegalEagleInterest(self, index):
        self.handleLocalToonEnterLegalEagleInterest(index)

    def handleLocalToonExitLegalEagleInterest(self, index):
        if index in self.index2LegalEagle:
            legalEagle = self.index2LegalEagle[index]
            if self.localPlayer.isLegalEagleInterestRequestSent(index):
                self.localPlayer.clearLegalEagleInterestRequest(index)
                self.distGame.d_sendRequestAction(Globals.AI.GameActions.RequestExitEagleInterest, index)
        else:
            self.notify.warning("Legal eagle %i isn't in index2LegalEagle dict" % index)

    def forceClearLegalEagleInterestInToon(self, toonId):
        player = self.toonId2Player[toonId]
        if player:
            for legalEagle in self.legalEagles:
                index = legalEagle.index
                if player.toon.isLocal():
                    if self.localPlayer.isLegalEagleInterestRequestSent(index):
                        self.localPlayer.clearLegalEagleInterestRequest(index)
                        self.distGame.d_sendRequestAction(Globals.AI.GameActions.RequestExitEagleInterest, index)
                self.toonClearAsEagleTarget(toonId, index, 0)

    def toonSetAsEagleTarget(self, toonId, eagleId, elapsedTime):
        if eagleId in self.index2LegalEagle:
            legalEagle = self.index2LegalEagle[eagleId]
            if toonId in self.toonId2Player:
                player = self.toonId2Player[toonId]
                player.setAsLegalEagleTarget(legalEagle)
                legalEagle.setTarget(player.toon, elapsedTime)

    def toonClearAsEagleTarget(self, toonId, eagleId, elapsedTime):
        if eagleId in self.index2LegalEagle:
            legalEagle = self.index2LegalEagle[eagleId]
            if toonId in self.toonId2Player:
                player = self.toonId2Player[toonId]
                player.removeAsLegalEagleTarget(legalEagle)
                if legalEagle.getTarget() == player.toon:
                    legalEagle.clearTarget(elapsedTime)

    def eagleExitCooldown(self, eagleId, elapsedTime):
        if eagleId in self.index2LegalEagle:
            legalEagle = self.index2LegalEagle[eagleId]
            legalEagle.leaveCooldown(elapsedTime)

    def gameComplete(self):
        self.localPlayer.request('Win')

    def __updateTask(self, task):
        dt = globalClock.getDt()
        self.localPlayer.update(dt)
        self.level.update(dt)
        for eagle in self.legalEagles:
            eagle.update(dt, self.localPlayer)

        self.guiMgr.update()
        return Task.cont
