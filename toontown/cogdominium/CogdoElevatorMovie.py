from pandac.PandaModules import NodePath, Point3, PlaneNode, TextNode
from direct.interval.IntervalGlobal import *
from direct.showbase.ShowBase import Plane
from direct.directnotify import DirectNotifyGlobal
from direct.showbase.RandomNumGen import RandomNumGen
from direct.interval.MetaInterval import Sequence, Parallel
from direct.interval.FunctionInterval import Func, Wait
from direct.gui.DirectGui import *
from toontown.toonbase.ToontownGlobals import *
from toontown.toonbase import TTLocalizer
from toontown.suit import Suit, SuitDNA
from toontown.toon import Toon, ToonHead, ToonDNA
from .CogdoUtil import CogdoGameMovie
from . import CogdoUtil

class CogdoElevatorMovie(CogdoGameMovie):
    notify = DirectNotifyGlobal.directNotify.newCategory('CogdoElevatorMovie')
    elevatorDuration = 5

    def __init__(self):
        CogdoGameMovie.__init__(self)
        self._toonDialogueSfx = None
        self.toonHead = None
        self.frame = None
        return

    def displayLine(self, text):
        self.notify.debug('displayLine')
        self._dialogueLabel.node().setText(text)
        self.toonHead.reparentTo(aspect2d)
        self._toonDialogueSfx.play()
        self.toonHead.setClipPlane(self.clipPlane)

    def makeSuit(self, suitType):
        self.notify.debug('makeSuit()')
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
        self.notify.debug('load()')
        CogdoGameMovie.load(self)
        backgroundGui = loader.loadModel('phase_5/models/cogdominium/tt_m_gui_csa_flyThru')
        self.bg = backgroundGui.find('**/background')
        self.chatBubble = backgroundGui.find('**/chatBubble')
        self.chatBubble.setScale(6.5, 6.5, 7.3)
        self.chatBubble.setPos(0.32, 0, -0.78)
        self.bg.setScale(5.2)
        self.bg.setPos(0.14, 0, -0.6667)
        self.bg.reparentTo(aspect2d)
        self.chatBubble.reparentTo(aspect2d)
        self.frame = DirectFrame(geom=self.bg, relief=None, pos=(0.2, 0, -0.6667))
        self.bg.wrtReparentTo(self.frame)
        self.gameTitleText = DirectLabel(parent=self.frame, text=TTLocalizer.CogdoExecutiveSuiteTitle, scale=TTLocalizer.MRPgameTitleText * 0.8, text_align=TextNode.ACenter, text_font=getSignFont(), text_fg=(1.0, 0.33, 0.33, 1.0), pos=TTLocalizer.MRgameTitleTextPos, relief=None)
        self.chatBubble.wrtReparentTo(self.frame)
        self.frame.hide()
        backgroundGui.removeNode()
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
        self.clipPlane = self.toonHead.attachNewNode(PlaneNode('clip'))
        self.clipPlane.node().setPlane(Plane(0, 0, 1, 0))
        self.clipPlane.setPos(0, 0, 2.45)
        self._toonDialogueSfx = loader.loadSfx('phase_3.5/audio/dial/AV_dog_long.ogg')
        self._camHelperNode = NodePath('CamHelperNode')
        self._camHelperNode.reparentTo(render)
        dialogue = TTLocalizer.CogdoElevatorRewardLaff

        def start():
            self.frame.show()
            base.setCellsAvailable(base.bottomCells + base.leftCells + base.rightCells, 0)

        def end():
            self._dialogueLabel.reparentTo(hidden)
            self.toonHead.reparentTo(hidden)
            self.frame.hide()
            base.setCellsAvailable(base.bottomCells + base.leftCells + base.rightCells, 1)
            self._stopUpdateTask()

        self._ival = Sequence(Func(start), Func(self.displayLine, dialogue), Wait(self.elevatorDuration), Func(end))
        self._startUpdateTask()
        return

    def _updateTask(self, task):
        dt = globalClock.getDt()
        return task.cont

    def unload(self):
        self.frame.destroy()
        del self.frame
        self.bg.removeNode()
        del self.bg
        self.chatBubble.removeNode()
        del self.chatBubble
        self.toonHead.stopBlink()
        self.toonHead.stop()
        self.toonHead.removeNode()
        self.toonHead.delete()
        del self.toonHead
        CogdoGameMovie.unload(self)
