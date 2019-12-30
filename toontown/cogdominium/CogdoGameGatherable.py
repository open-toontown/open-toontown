from pandac.PandaModules import CollisionSphere, CollisionNode
from pandac.PandaModules import NodePath, BitMask32
from direct.showbase.DirectObject import DirectObject
from direct.interval.MetaInterval import Sequence
from direct.interval.FunctionInterval import Func, Wait
from direct.interval.IntervalGlobal import LerpFunc
from toontown.toonbase import ToontownGlobals
from . import CogdoUtil

class CogdoGameGatherable(NodePath, DirectObject):
    EnterEventName = 'CogdoGameGatherable_Enter'

    def __init__(self, serialNum, model, triggerRadius, triggerOffset = (0, 0, 0), animate = True, animDuration = 0.2, instanceModel = True, name = 'CogdoGameGatherable'):
        NodePath.__init__(self, '%s-%d' % (name, serialNum))
        self.serialNum = serialNum
        self._animate = animate
        if instanceModel:
            model.instanceTo(self)
            self._model = self
        else:
            self._model = model
            self._model.reparentTo(self)
            self._model.setPosHpr(0, 0, 0, 0, 0, 0)
        self._animDuration = animDuration
        self._animSeq = None
        self._initCollisions(triggerRadius, triggerOffset)
        self._update = None
        self._wasPickedUp = False
        return

    def _initCollisions(self, triggerRadius, triggerOffset):
        self.collSphere = CollisionSphere(triggerOffset[0], triggerOffset[1], triggerOffset[2], triggerRadius)
        self.collSphere.setTangible(0)
        self.collNode = CollisionNode(self.getName())
        self.collNode.addSolid(self.collSphere)
        self.collNodePath = self.attachNewNode(self.collNode)

    def destroy(self):
        self.disable()
        del self._model
        if self._animSeq is not None:
            self._animSeq.finish()
            self._animSeq = None
        self.collNodePath.removeNode()
        self.removeNode()
        return

    def enable(self):
        self.accept('enter' + self.getName(), self._handleEnterCollision)
        self.collNode.setIntoCollideMask(ToontownGlobals.WallBitmask)

    def disable(self):
        self.ignoreAll()
        self.collNode.setIntoCollideMask(BitMask32(0))

    def show(self):
        if not self.wasPickedUp():
            NodePath.show(self)
            self.enable()

    def hide(self):
        self.disable()
        NodePath.hide(self)

    def _handleEnterCollision(self, collEntry):
        messenger.send(CogdoGameGatherable.EnterEventName, [self])

    def wasPickedUp(self):
        return self._wasPickedUp

    def wasPickedUpByToon(self):
        pass

    def update(self, dt):
        pass

    def getModel(self):
        return self._model

    def pickUp(self, toon, elapsedSeconds = 0.0):
        self._wasPickedUp = True
        if self._animSeq is not None:
            self._animSeq.finish()
            self._animSeq = None
        if self._animate:

            def lerpFlyToToon(t):
                vec = toon.getPos(render) - self.getPos(render)
                vec[2] += toon.getHeight()
                self.setPos(self.getPos() + vec * t)
                self.setScale(1.0 - t * 0.8)

            self._animSeq = Sequence(LerpFunc(lerpFlyToToon, fromData=0.0, toData=1.0, duration=self._animDuration), Wait(0.1), Func(self.hide))
            self._animSeq.start(elapsedSeconds)
        else:
            self.hide()
        return


class CogdoMemo(CogdoGameGatherable):
    EnterEventName = 'CogdoMemo_Enter'

    def __init__(self, serialNum, model = None, pitch = 0, triggerRadius = 1.0, spinRate = 60):
        if model is None:
            node = CogdoUtil.loadModel('memo', 'shared')
            model = node.find('**/memo')
            model.detachNode()
            node.removeNode()
        model.setP(pitch)
        self._spinRate = spinRate
        CogdoGameGatherable.__init__(self, serialNum, model, triggerRadius, name='CogdoMemo')
        return

    def destroy(self):
        del self._spinRate
        CogdoGameGatherable.destroy(self)

    def update(self, dt):
        CogdoGameGatherable.update(self, dt)
        self.setH(self.getH() + self._spinRate * dt)

    def _handleEnterCollision(self, collEntry):
        messenger.send(CogdoMemo.EnterEventName, [self])
