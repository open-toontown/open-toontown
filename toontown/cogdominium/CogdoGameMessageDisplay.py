from direct.interval.FunctionInterval import Func
from direct.interval.LerpInterval import LerpFunc
from direct.interval.MetaInterval import Sequence
from panda3d.core import TextNode
from toontown.toonbase import ToontownGlobals
from . import CogdoGameConsts

class CogdoGameMessageDisplay:
    UpdateMessageTaskName = 'MessageDisplay.updateMessage'

    def __init__(self, name, parent, pos = (0.0, 0.0, -0.5), scale = 0.09, color = (1.0, 1.0, 0, 1), sfx = None):
        self.color = color
        self._displaySfx = sfx
        textNode = TextNode('messageLabel.' + name)
        textNode.setTextColor(self.color)
        textNode.setAlign(TextNode.ACenter)
        textNode.setFont(ToontownGlobals.getSignFont())
        textNode.setShadow(0.06, 0.06)
        textNode.setShadowColor(0.5, 0.5, 0.5, 1.0)
        self.pos = pos
        self.scale = scale
        self.messageLabel = parent.attachNewNode(textNode)
        self.messageLabel.setPos(self.pos)
        self.messageLabel.setScale(self.scale)
        self.messageLabel.stash()
        self.transitionInterval = Sequence(name='%s.transitionInterval' % self.__class__.__name__)

    def destroy(self):
        taskMgr.remove(CogdoGameMessageDisplay.UpdateMessageTaskName)
        self.transitionInterval.finish()
        self.transitionInterval.clearIntervals()
        del self.transitionInterval.pythonIvals[:]
        del self.transitionInterval[:]
        self.messageLabel.removeNode()
        del self.messageLabel
        if self._displaySfx != None:
            del self._displaySfx
        return

    def updateMessage(self, message = '', color = None, transition = 'fade'):
        taskMgr.remove(CogdoGameMessageDisplay.UpdateMessageTaskName)
        if color is None:
            color = self.color
        self.transitionInterval.finish()
        self.transitionInterval.clearIntervals()
        del self.transitionInterval.pythonIvals[:]
        del self.transitionInterval[:]
        if message == '':
            if transition in ('fade', 'blink'):
                self.transitionInterval.append(LerpFunc(self.messageLabel.setAlphaScale, fromData=1.0, toData=0.0, duration=CogdoGameConsts.MessageLabelFadeTime, extraArgs=[]))
            self.transitionInterval.append(Func(self.messageLabel.stash))
        else:
            if self.messageLabel.isStashed():
                self.transitionInterval.append(Func(self.messageLabel.setAlphaScale, 0.0))
                self.transitionInterval.append(Func(self.messageLabel.unstash))
            elif transition in ('fade', 'blink'):
                self.transitionInterval.append(LerpFunc(self.messageLabel.setAlphaScale, fromData=1.0, toData=0.0, duration=CogdoGameConsts.MessageLabelFadeTime, extraArgs=[]))
            self.transitionInterval.append(Func(self.messageLabel.setPos, self.pos))
            self.transitionInterval.append(Func(self.messageLabel.node().setText, message))
            self.transitionInterval.append(Func(self.messageLabel.node().setTextColor, color))
            if self._displaySfx != None:
                self.transitionInterval.append(Func(self._displaySfx.play))
            if transition == 'fade':
                self.transitionInterval.append(LerpFunc(self.messageLabel.setAlphaScale, fromData=0.0, toData=1.0, duration=CogdoGameConsts.MessageLabelFadeTime, extraArgs=[]))
            elif transition == 'blink':
                self.transitionInterval.append(LerpFunc(self.messageLabel.setAlphaScale, fromData=0.0, toData=1.0, duration=CogdoGameConsts.MessageLabelBlinkTime, extraArgs=[]))
                self.transitionInterval.append(LerpFunc(self.messageLabel.setAlphaScale, fromData=1.0, toData=0.0, duration=CogdoGameConsts.MessageLabelBlinkTime, extraArgs=[]))
                self.transitionInterval.append(LerpFunc(self.messageLabel.setAlphaScale, fromData=0.0, toData=1.0, duration=CogdoGameConsts.MessageLabelBlinkTime, extraArgs=[]))
            else:
                self.transitionInterval.append(Func(self.messageLabel.setAlphaScale, 1.0))
        self.transitionInterval.start()
        return

    def showMessageTemporarily(self, message = '', duration = 3.0, color = None):
        self.updateMessage(message, color)
        taskMgr.doMethodLater(duration, self.updateMessage, CogdoGameMessageDisplay.UpdateMessageTaskName, extraArgs=[])
