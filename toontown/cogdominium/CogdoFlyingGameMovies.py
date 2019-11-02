from pandac.PandaModules import Point3, PlaneNode
from direct.showbase.ShowBase import Plane
from direct.showbase.RandomNumGen import RandomNumGen
from direct.interval.MetaInterval import Sequence, Parallel
from direct.interval.FunctionInterval import Func, Wait
from toontown.toonbase import TTLocalizer
from toontown.toon import Toon, ToonHead, ToonDNA
from toontown.suit import Suit, SuitDNA
import CogdoFlyingGameGlobals as Globals
from CogdoUtil import CogdoGameMovie
import CogdoUtil

class CogdoFlyingGameIntro(CogdoGameMovie):

    def __init__(self, level, rng):
        CogdoGameMovie.__init__(self)
        self._level = level
        self._rng = RandomNumGen(rng)
        self._exit = self._level.getExit()

    def _getRandomLine(self, lineList):
        return CogdoUtil.getRandomDialogueLine(lineList, self._rng)

    def displayLine(self, who, text):
        self._dialogueLabel.node().setText(text)
        if who == 'toon':
            self.toonHead.reparentTo(aspect2d)
            self.cogHead.reparentTo(hidden)
            self._toonDialogueSfx.play()
            self.toonHead.setClipPlane(self.clipPlane)
        else:
            self.toonHead.reparentTo(hidden)
            self.cogHead.reparentTo(aspect2d)
            self._cogDialogueSfx.play()
            self.cogHead.setClipPlane(self.clipPlane)

    def makeSuit(self, suitType):
        suit = Suit.Suit()
        dna = SuitDNA.SuitDNA()
        dna.newSuit(suitType)
        suit.setStyle(dna)
        suit.isDisguised = 1
        suit.generateSuit()
        suit.setScale(1, 1, 2)
        suit.setPos(0, 0, -4.4)
        suit.reparentTo(self.toonHead)
        for part in suit.getHeadParts():
            part.hide()

        suit.loop('neutral')

    def load(self):
        CogdoGameMovie.load(self)
        self.toonDNA = ToonDNA.ToonDNA()
        self.toonDNA.newToonFromProperties('dss', 'ss', 'm', 'm', 2, 0, 2, 2, 1, 8, 1, 8, 1, 14)
        self.toonHead = Toon.Toon()
        self.toonHead.setDNA(self.toonDNA)
        self.makeSuit('sc')
        self.toonHead.getGeomNode().setDepthWrite(1)
        self.toonHead.getGeomNode().setDepthTest(1)
        self.toonHead.loop('neutral')
        self.toonHead.setPosHprScale(-0.73, 0, -1.27, 180, 0, 0, 0.18, 0.18, 0.18)
        self.toonHead.reparentTo(hidden)
        self.toonHead.startBlink()
        self.cogHead = Suit.Suit()
        self.cogDNA = SuitDNA.SuitDNA()
        self.cogDNA.newSuit('le')
        self.cogHead.setDNA(self.cogDNA)
        self.cogHead.getGeomNode().setDepthWrite(1)
        self.cogHead.getGeomNode().setDepthTest(1)
        self.cogHead.loop('neutral')
        self.cogHead.setPosHprScale(-0.74, 0, -1.79, 180, 0, 0, 0.12, 0.14, 0.14)
        self.cogHead.reparentTo(hidden)
        self.clipPlane = self.toonHead.attachNewNode(PlaneNode('clip'))
        self.clipPlane.node().setPlane(Plane(0, 0, 1, 0))
        self.clipPlane.setPos(0, 0, 2.45)
        audioMgr = base.cogdoGameAudioMgr
        self._cogDialogueSfx = audioMgr.createSfx('cogDialogue')
        self._toonDialogueSfx = audioMgr.createSfx('toonDialogue')

        def start():
            camera.wrtReparentTo(render)
            self._startUpdateTask()

        def end():
            self._stopUpdateTask()

        introDuration = Globals.Gameplay.IntroDurationSeconds
        dialogue = TTLocalizer.CogdoFlyingIntroMovieDialogue
        waitDur = introDuration / len(dialogue)
        flyDur = introDuration - waitDur * 0.5
        flyThroughIval = Parallel(camera.posInterval(flyDur, self._exit.getPos(render) + Point3(0, -22, 1), blendType='easeInOut'), camera.hprInterval(flyDur, Point3(0, 5, 0), blendType='easeInOut'))
        self._ival = Sequence(Func(start), Parallel(flyThroughIval, Sequence(Func(self.displayLine, 'cog', self._getRandomLine(dialogue[0])), Wait(waitDur), Func(self.displayLine, 'toon', self._getRandomLine(dialogue[1])), Wait(waitDur), Func(self.displayLine, 'cog', self._getRandomLine(dialogue[2])), Wait(waitDur))), Func(end))

    def _updateTask(self, task):
        dt = globalClock.getDt()
        self._level.update(dt)
        return task.cont

    def unload(self):
        CogdoGameMovie.unload(self)
        del self._cogDialogueSfx
        del self._toonDialogueSfx
        self.toonHead.stopBlink()
        self.toonHead.stop()
        self.toonHead.removeNode()
        self.toonHead.delete()
        del self.toonHead
        self.cogHead.stop()
        self.cogHead.removeNode()
        self.cogHead.delete()
        del self.cogHead
        self._exit = None
        self._level = None
        return


class CogdoFlyingGameFinish(CogdoGameMovie):

    def __init__(self, level, players):
        CogdoGameMovie.__init__(self)
        self._exit = level.getExit()
        self._players = players

    def load(self):
        CogdoGameMovie.load(self)

        def showDoor():
            camera.wrtReparentTo(render)
            camera.setPos(self._exit, 0, -55, 40)
            camera.lookAt(self._exit, 0, 0, -20)
            self._exit.open()

        exitDur = 1.0
        showExitIval = Sequence(Func(camera.wrtReparentTo, render), Parallel(camera.posInterval(exitDur, Point3(0, -55, 40), other=self._exit, blendType='easeInOut'), camera.hprInterval(exitDur, Point3(0, -45, 0), blendType='easeInOut')))

        def showPlayersLeaving():
            for player in self._players:
                self._exit.toonEnters(player.toon)

        self._ival = Sequence(showExitIval, Func(self._exit.open), Func(showPlayersLeaving), Wait(Globals.Gameplay.FinishDurationSeconds - exitDur - 1.0), Func(base.transitions.irisOut), Wait(1.0))

    def unload(self):
        CogdoGameMovie.unload(self)
