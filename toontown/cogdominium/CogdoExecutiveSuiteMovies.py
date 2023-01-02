from panda3d.core import NodePath, Point3, PlaneNode, TextNode
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

class CogdoExecutiveSuiteIntro(CogdoGameMovie):
    notify = DirectNotifyGlobal.directNotify.newCategory('CogdoExecutiveSuiteIntro')
    introDuration = 7
    cameraMoveDuration = 3

    def __init__(self, shopOwner):
        CogdoGameMovie.__init__(self)
        self._shopOwner = shopOwner
        self._lookAtCamTarget = False
        self._camTarget = None
        self._camHelperNode = None
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
        dialogue = TTLocalizer.CogdoExecutiveSuiteIntroMessage

        def start():
            self.frame.show()
            base.setCellsAvailable(base.bottomCells + base.leftCells + base.rightCells, 0)

        def showShopOwner():
            self._setCamTarget(self._shopOwner, -10, offset=Point3(0, 0, 5))

        def end():
            self._dialogueLabel.reparentTo(hidden)
            self.toonHead.reparentTo(hidden)
            self.frame.hide()
            base.setCellsAvailable(base.bottomCells + base.leftCells + base.rightCells, 1)
            self._stopUpdateTask()

        self._ival = Sequence(Func(start), Func(self.displayLine, dialogue), Func(showShopOwner), ParallelEndTogether(camera.posInterval(self.cameraMoveDuration, Point3(8, 0, 13), blendType='easeInOut'), camera.hprInterval(0.5, self._camHelperNode.getHpr(), blendType='easeInOut')), Wait(self.introDuration), Func(end))
        self._startUpdateTask()
        return

    def _setCamTarget(self, targetNP, distance, offset = Point3(0, 0, 0), angle = Point3(0, 0, 0)):
        camera.wrtReparentTo(render)
        self._camTarget = targetNP
        self._camOffset = offset
        self._camAngle = angle
        self._camDistance = distance
        self._camHelperNode.setPos(self._camTarget, self._camOffset)
        self._camHelperNode.setHpr(self._camTarget, 180 + self._camAngle[0], self._camAngle[1], self._camAngle[2])
        self._camHelperNode.setPos(self._camHelperNode, 0, self._camDistance, 0)

    def _updateTask(self, task):
        dt = globalClock.getDt()
        return task.cont

    def unload(self):
        self._shopOwner = None
        self._camTarget = None
        if hasattr(self, '_camHelperNode') and self._camHelperNode:
            self._camHelperNode.removeNode()
            del self._camHelperNode
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
        return
