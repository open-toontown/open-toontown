from pandac.PandaModules import NodePath, Point3, PlaneNode
from direct.showbase.ShowBase import Plane
from direct.showbase.RandomNumGen import RandomNumGen
from direct.interval.MetaInterval import Sequence, Parallel
from direct.interval.FunctionInterval import Func, Wait
from toontown.toonbase import TTLocalizer
from toontown.suit import Suit, SuitDNA
from toontown.toon import Toon, ToonHead, ToonDNA
from .CogdoUtil import CogdoGameMovie
from . import CogdoMazeGameGlobals as Globals
from . import CogdoUtil

class CogdoMazeGameIntro(CogdoGameMovie):

    def __init__(self, maze, exit, rng):
        CogdoGameMovie.__init__(self)
        self._maze = maze
        self._exit = exit
        self._rng = RandomNumGen(rng)
        self._camTarget = None
        self._state = 0
        self._suits = []
        return

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
        self.cogDNA.newSuit('ms')
        self.cogHead.setDNA(self.cogDNA)
        self.cogHead.getGeomNode().setDepthWrite(1)
        self.cogHead.getGeomNode().setDepthTest(1)
        self.cogHead.loop('neutral')
        self.cogHead.setPosHprScale(-0.73, 0, -1.46, 180, 0, 0, 0.14, 0.14, 0.14)
        self.cogHead.reparentTo(hidden)
        self.clipPlane = self.toonHead.attachNewNode(PlaneNode('clip'))
        self.clipPlane.node().setPlane(Plane(0, 0, 1, 0))
        self.clipPlane.setPos(0, 0, 2.45)
        audioMgr = base.cogdoGameAudioMgr
        self._cogDialogueSfx = audioMgr.createSfx('cogDialogue')
        self._toonDialogueSfx = audioMgr.createSfx('toonDialogue')
        suitData = Globals.SuitData[Globals.SuitTypes.Boss]
        bossSuit = Suit.Suit()
        d = SuitDNA.SuitDNA()
        d.newSuit(suitData['dnaName'])
        bossSuit.setDNA(d)
        bossSuit.setScale(suitData['scale'])
        bossSuit.loop('neutral')
        bossSuit.reparentTo(render)
        bossSuit.setPos(self._exit, -5, -5, 0)
        bossSuit.lookAt(self._exit)
        self._suits.append(bossSuit)
        self._camHelperNode = NodePath('CamHelperNode')
        self._camHelperNode.reparentTo(render)
        dialogue = TTLocalizer.CogdoMazeIntroMovieDialogue
        introDuration = Globals.IntroDurationSeconds
        waitDuration = introDuration / len(dialogue)

        def start():
            camera.wrtReparentTo(render)
            self._exit.open(animate=False)

        def showBoss():
            self._setCamTarget(bossSuit, 20, offset=Point3(0, 0, 7), angle=Point3(0, 15, 0))
            bossSuit.loop('victory')
            self._state = 1

        def showExit():
            self._setCamTarget(self._exit, 10, offset=Point3(0, 0, 0), angle=Point3(0, 60, 0))
            self._exit.close()
            self._state = 2

        showExitIval = Parallel(camera.posInterval(waitDuration * 0.5, (10, -25, 20), other=self._exit, blendType='easeInOut'), Sequence(Wait(waitDuration * 0.25), Func(bossSuit.play, 'effort'), camera.hprInterval(waitDuration * 0.25, (30, -30, 0), blendType='easeInOut'), Func(self._exit.close), Wait(waitDuration * 0.5)))

        def showWaterCooler():
            wc = self._maze.getWaterCoolers()[0]
            self._setCamTarget(wc, 25, angle=Point3(-30, 60, 0))
            camera.wrtReparentTo(self._camHelperNode)
            self._state = 3

        def end():
            self._stopUpdateTask()

        self._ival = Sequence(Func(start), Func(self.displayLine, 'toon', self._getRandomLine(dialogue[0])), showExitIval, Func(showWaterCooler), Func(self.displayLine, 'toon', self._getRandomLine(dialogue[1])), Wait(waitDuration), Func(showBoss), bossSuit.hprInterval(1.0, bossSuit.getHpr() + Point3(180, 0, 0), blendType='easeInOut'), Func(self.displayLine, 'toon', self._getRandomLine(dialogue[2])), Wait(waitDuration - 1.0), Func(end))
        self._startUpdateTask()

    def _setCamTarget(self, targetNP, distance, offset = Point3(0, 0, 0), angle = Point3(0, 0, 0)):
        camera.wrtReparentTo(render)
        self._camTarget = targetNP
        self._camOffset = offset
        self._camAngle = angle
        self._camDistance = distance
        self._camHelperNode.setPos(self._camTarget, self._camOffset)
        self._camHelperNode.setHpr(self._camTarget, 180 + self._camAngle[0], self._camAngle[1], self._camAngle[2])
        camera.setPos(self._camHelperNode, 0, self._camDistance, 0)

    def _updateTask(self, task):
        dt = globalClock.getDt()
        if self._state == 1:
            self._camHelperNode.setPos(self._camTarget.getPos() + self._camOffset)
            camera.setPos(self._camHelperNode, 0, self._camDistance, 0)
            camera.lookAt(self._camTarget, 0, 0, 4)
        elif self._state == 2:
            camera.lookAt(self._camTarget, 0, 0, 5)
        elif self._state == 3:
            self._camHelperNode.setHpr(self._camHelperNode, dt, dt, 0)
            camera.setY(camera, 0.8 * dt)
            camera.lookAt(self._camTarget, 0, 0, 3)
        return task.cont

    def unload(self):
        self._exit = None
        self._camTarget = None
        self._camHelperNode.removeNode()
        del self._camHelperNode
        for suit in self._suits:
            suit.cleanup()
            suit.removeNode()
            suit.delete()

        self._suits = []
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
        return


class CogdoMazeGameFinish(CogdoGameMovie):

    def __init__(self, localPlayer, exit):
        CogdoGameMovie.__init__(self)
        self._localPlayer = localPlayer
        self._exit = exit

    def load(self):
        CogdoGameMovie.load(self)
        self._ival = Sequence()
        if not self._exit.hasPlayer(self._localPlayer):
            loseSfx = base.cogdoGameAudioMgr.createSfx('lose')
            self._ival.append(Sequence(Func(loseSfx.play), Func(self._localPlayer.toon.setAnimState, 'Sad')))
        self._ival.append(Sequence(Wait(Globals.FinishDurationSeconds - 1.0), Func(base.transitions.irisOut), Wait(1.0)))

    def unload(self):
        CogdoGameMovie.unload(self)
