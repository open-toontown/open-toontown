from pandac.PandaModules import VBase4
from direct.gui.DirectGui import DirectLabel
from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.ClockDelta import globalClockDelta
from direct.distributed.DistributedObject import DistributedObject
from direct.fsm import ClassicFSM, State
from direct.fsm.StatePush import StateVar, FunctionCall
from toontown.cogdominium import CogdoGameConsts
from toontown.cogdominium.DistCogdoGameBase import DistCogdoGameBase
from toontown.minigame.MinigameRulesPanel import MinigameRulesPanel
from toontown.cogdominium.CogdoGameRulesPanel import CogdoGameRulesPanel
from toontown.minigame import MinigameGlobals
from toontown.toonbase import TTLocalizer as TTL
SCHELLGAMES_DEV = __debug__ and base.config.GetBool('schellgames-dev', False)

class DistCogdoGame(DistCogdoGameBase, DistributedObject):
    notify = directNotify.newCategory('DistCogdoGame')

    def __init__(self, cr):
        DistributedObject.__init__(self, cr)
        base.cogdoGame = self
        self._waitingStartLabel = DirectLabel(text=TTL.MinigameWaitingForOtherPlayers, text_fg=VBase4(1, 1, 1, 1), relief=None, pos=(-0.6, 0, -0.75), scale=0.075)
        self._waitingStartLabel.hide()
        self.loadFSM = ClassicFSM.ClassicFSM('DistCogdoGame.loaded', [State.State('NotLoaded', self.enterNotLoaded, self.exitNotLoaded, ['Loaded']), State.State('Loaded', self.enterLoaded, self.exitLoaded, ['NotLoaded'])], 'NotLoaded', 'NotLoaded')
        self.loadFSM.enterInitialState()
        self.fsm = ClassicFSM.ClassicFSM('DistCogdoGame', [State.State('Visible', self.enterVisible, self.exitVisible, ['Intro']),
         State.State('Intro', self.enterIntro, self.exitIntro, ['WaitServerStart']),
         State.State('WaitServerStart', self.enterWaitServerStart, self.exitWaitServerStart, ['Game']),
         State.State('Game', self.enterGame, self.exitGame, ['Finish']),
         State.State('Finish', self.enterFinish, self.exitFinish, ['Off']),
         State.State('Off', self.enterOff, self.exitOff, ['Visible'])], 'Off', 'Off')
        self.fsm.enterInitialState()
        self.difficultyOverride = None
        self.exteriorZoneOverride = None
        self._gotInterior = StateVar(False)
        self._toonsInEntranceElev = StateVar(False)
        self._wantStashElevator = StateVar(False)
        self._stashElevatorFC = FunctionCall(self._doStashElevator, self._toonsInEntranceElev, self._gotInterior, self._wantStashElevator)
        return

    def getTitle(self):
        pass

    def getInstructions(self):
        pass

    def setInteriorId(self, interiorId):
        self._interiorId = interiorId

    def setExteriorZone(self, exteriorZone):
        self.exteriorZone = exteriorZone

    def setDifficultyOverrides(self, difficultyOverride, exteriorZoneOverride):
        if difficultyOverride != CogdoGameConsts.NoDifficultyOverride:
            self.difficultyOverride = difficultyOverride / float(CogdoGameConsts.DifficultyOverrideMult)
        if exteriorZoneOverride != CogdoGameConsts.NoExteriorZoneOverride:
            self.exteriorZoneOverride = exteriorZoneOverride

    def getInterior(self):
        return self.cr.getDo(self._interiorId)

    def getEntranceElevator(self, callback):
        return self.getInterior().getEntranceElevator(callback)

    def getToonIds(self):
        interior = self.getInterior()
        if interior is not None:
            return interior.getToonIds()
        else:
            return []
        return

    def getToon(self, toonId):
        if toonId in self.cr.doId2do:
            return self.cr.doId2do[toonId]
        else:
            return None
        return None

    def getNumPlayers(self):
        return len(self.getToonIds())

    def isSinglePlayer(self):
        if self.getNumPlayers() == 1:
            return 1
        else:
            return 0

    def announceGenerate(self):
        DistributedObject.announceGenerate(self)
        self._requestInterior()
        self.loadFSM.request('Loaded')
        self.notify.info('difficulty: %s, safezoneId: %s' % (self.getDifficulty(), self.getSafezoneId()))

    def _requestInterior(self):
        self.cr.relatedObjectMgr.requestObjects([self._interiorId], allCallback=self._handleGotInterior)

    def _handleGotInterior(self, objs):
        self._gotInterior.set(True)
        self.getEntranceElevator(self.placeEntranceElev)

    def stashEntranceElevator(self):
        self._wantStashElevator.set(True)

    def placeEntranceElev(self, elev):
        pass

    def _doStashElevator(self, toonsInEntranceElev, gotInterior, wantStashElevator):
        if gotInterior:
            interior = self.getInterior()
            if interior:
                if not toonsInEntranceElev and wantStashElevator:
                    interior.stashElevatorIn()
                else:
                    interior.stashElevatorIn(False)

    def disable(self):
        base.cogdoGame = None
        self.fsm.requestFinalState()
        self.loadFSM.requestFinalState()
        self.fsm = None
        self.loadFSM = None
        DistributedObject.disable(self)
        return

    def delete(self):
        self._stashElevatorFC.destroy()
        self._wantStashElevator.destroy()
        self._toonsInEntranceElev.destroy()
        self._gotInterior.destroy()
        self._waitingStartLabel.destroy()
        self._waitingStartLabel = None
        DistributedObject.delete(self)
        return

    def getDifficulty(self):
        if self.difficultyOverride is not None:
            return self.difficultyOverride
        if hasattr(base, 'cogdoGameDifficulty'):
            return float(base.cogdoGameDifficulty)
        return CogdoGameConsts.getDifficulty(self.getSafezoneId())

    def getSafezoneId(self):
        if self.exteriorZoneOverride is not None:
            return self.exteriorZoneOverride
        if hasattr(base, 'cogdoGameSafezoneId'):
            return CogdoGameConsts.getSafezoneId(base.cogdoGameSafezoneId)
        return CogdoGameConsts.getSafezoneId(self.exteriorZone)

    def enterNotLoaded(self):
        pass

    def exitNotLoaded(self):
        pass

    def enterLoaded(self):
        pass

    def exitLoaded(self):
        pass

    def enterOff(self):
        pass

    def exitOff(self):
        pass

    def setVisible(self):
        self.fsm.request('Visible')

    def setIntroStart(self):
        self.fsm.request('Intro')

    def enterVisible(self):
        self._toonsInEntranceElev.set(True)

    def exitVisible(self):
        pass

    def enterIntro(self, duration = MinigameGlobals.rulesDuration):
        base.cr.playGame.getPlace().fsm.request('Game')
        self._rulesDoneEvent = self.uniqueName('cogdoGameRulesDone')
        self.accept(self._rulesDoneEvent, self._handleRulesDone)
        self._rulesPanel = CogdoGameRulesPanel('CogdoGameRulesPanel', self.getTitle(), '', self._rulesDoneEvent, timeout=duration)
        self._rulesPanel.load()
        self._rulesPanel.enter()

    def exitIntro(self):
        self._toonsInEntranceElev.set(False)
        self.ignore(self._rulesDoneEvent)
        if self._rulesPanel:
            self._rulesPanel.exit()
            self._rulesPanel.unload()
            self._rulesPanel = None
        return

    def _handleRulesDone(self):
        self.ignore(self._rulesDoneEvent)
        self._rulesPanel.exit()
        self._rulesPanel.unload()
        self._rulesPanel = None
        self.fsm.request('WaitServerStart')
        self.d_setAvatarReady()
        return

    def d_setAvatarReady(self):
        self.sendUpdate('setAvatarReady', [])

    def enterWaitServerStart(self):
        numToons = 1
        interior = self.getInterior()
        if interior:
            numToons = len(interior.getToonIds())
        if numToons > 1:
            msg = TTL.MinigameWaitingForOtherPlayers
        else:
            msg = TTL.MinigamePleaseWait
        self._waitingStartLabel['text'] = msg
        self._waitingStartLabel.show()

    def exitWaitServerStart(self):
        self._waitingStartLabel.hide()

    def setGameStart(self, timestamp):
        self._startTime = globalClockDelta.networkToLocalTime(timestamp)
        self.fsm.request('Game')

    def getStartTime(self):
        return self._startTime

    def enterGame(self):
        if SCHELLGAMES_DEV:
            self.acceptOnce('escape', messenger.send, ['magicWord', ['~endgame']])

    def exitGame(self):
        if SCHELLGAMES_DEV:
            self.ignore('escape')

    def setGameFinish(self, timestamp):
        self._finishTime = globalClockDelta.networkToLocalTime(timestamp)
        self.fsm.request('Finish')

    def getFinishTime(self):
        return self._finishTime

    def enterFinish(self):
        pass

    def exitFinish(self):
        pass

    def setToonSad(self, toonId):
        pass

    def setToonDisconnect(self, toonId):
        pass
