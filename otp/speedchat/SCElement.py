from pandac.PandaModules import *
from direct.gui.DirectGui import *
from direct.task import Task
from SCConstants import *
from SCObject import SCObject
from direct.showbase.PythonUtil import boolEqual
from otp.otpbase import OTPGlobals

class SCElement(SCObject, NodePath):
    font = OTPGlobals.getInterfaceFont()
    SerialNum = 0

    def __init__(self, parentMenu = None):
        SCObject.__init__(self)
        self.SerialNum = SCElement.SerialNum
        SCElement.SerialNum += 1
        node = hidden.attachNewNode('SCElement%s' % self.SerialNum)
        NodePath.__init__(self, node)
        self.FinalizeTaskName = 'SCElement%s_Finalize' % self.SerialNum
        self.parentMenu = parentMenu
        self.__active = 0
        self.__viewable = 1
        self.lastWidth = 0
        self.lastHeight = 0
        self.setDimensions(0, 0)
        self.padX = 0.25
        self.padZ = 0.1

    def destroy(self):
        if self.isActive():
            self.exitActive()
        SCObject.destroy(self)
        if hasattr(self, 'button'):
            self.button.destroy()
            del self.button
        self.parentMenu = None
        self.detachNode()
        return

    def setParentMenu(self, parentMenu):
        self.parentMenu = parentMenu

    def getParentMenu(self):
        return self.parentMenu

    def getDisplayText(self):
        self.notify.error('getDisplayText is pure virtual, derived class must override')

    def onMouseEnter(self, event):
        if self.parentMenu is not None:
            self.parentMenu.memberGainedInputFocus(self)
        return

    def onMouseLeave(self, event):
        if self.parentMenu is not None:
            self.parentMenu.memberLostInputFocus(self)
        return

    def onMouseClick(self, event):
        pass

    def enterActive(self):
        self.__active = 1

    def exitActive(self):
        self.__active = 0

    def isActive(self):
        return self.__active

    def hasStickyFocus(self):
        return 0

    def setViewable(self, viewable):
        if not boolEqual(self.__viewable, viewable):
            self.__viewable = viewable
            if self.parentMenu is not None:
                self.parentMenu.memberViewabilityChanged(self)
        return

    def isViewable(self):
        return self.__viewable

    def getMinDimensions(self):
        text = TextNode('SCTemp')
        text.setFont(SCElement.font)
        dText = self.getDisplayText()
        text.setText(dText)
        bounds = text.getCardActual()
        width = abs(bounds[1] - bounds[0]) + self.padX
        height = abs(bounds[3] - bounds[2]) + 2.0 * self.padZ
        return (width, height)

    def setDimensions(self, width, height):
        self.width = float(width)
        self.height = float(height)
        if (self.lastWidth, self.lastHeight) != (self.width, self.height):
            self.invalidate()

    def invalidate(self):
        SCObject.invalidate(self)
        parentMenu = self.getParentMenu()
        if parentMenu is not None:
            if not parentMenu.isFinalizing():
                parentMenu.invalidate()
        return

    def enterVisible(self):
        SCObject.enterVisible(self)
        self.privScheduleFinalize()

    def exitVisible(self):
        SCObject.exitVisible(self)
        self.privCancelFinalize()

    def privScheduleFinalize(self):

        def finalizeElement(task, self = self):
            if self.parentMenu is not None:
                if self.parentMenu.isDirty():
                    return Task.done
            self.finalize()
            return Task.done

        taskMgr.remove(self.FinalizeTaskName)
        taskMgr.add(finalizeElement, self.FinalizeTaskName, priority=SCElementFinalizePriority)

    def privCancelFinalize(self):
        taskMgr.remove(self.FinalizeTaskName)

    def finalize(self, dbArgs = {}):
        if not self.isDirty():
            return
        SCObject.finalize(self)
        if hasattr(self, 'button'):
            self.button.destroy()
            del self.button
        halfHeight = self.height / 2.0
        textX = 0
        if dbArgs.has_key('text_align'):
            if dbArgs['text_align'] == TextNode.ACenter:
                textX = self.width / 2.0
        args = {'text': self.getDisplayText(),
         'frameColor': (0, 0, 0, 0),
         'rolloverColor': self.getColorScheme().getRolloverColor() + (1,),
         'pressedColor': self.getColorScheme().getPressedColor() + (1,),
         'text_font': OTPGlobals.getInterfaceFont(),
         'text_align': TextNode.ALeft,
         'text_fg': self.getColorScheme().getTextColor() + (1,),
         'text_pos': (textX, -.25 - halfHeight, 0),
         'relief': DGG.FLAT,
         'pressEffect': 0}
        args.update(dbArgs)
        rolloverColor = args['rolloverColor']
        pressedColor = args['pressedColor']
        del args['rolloverColor']
        del args['pressedColor']
        btn = DirectButton(parent=self, frameSize=(0,
         self.width,
         -self.height,
         0), **args)
        btn.frameStyle[DGG.BUTTON_ROLLOVER_STATE].setColor(*rolloverColor)
        btn.frameStyle[DGG.BUTTON_DEPRESSED_STATE].setColor(*pressedColor)
        btn.updateFrameStyle()
        btn.bind(DGG.ENTER, self.onMouseEnter)
        btn.bind(DGG.EXIT, self.onMouseLeave)
        btn.bind(DGG.B1PRESS, self.onMouseClick)
        self.button = btn
        self.lastWidth = self.width
        self.lastHeight = self.height
        self.validate()

    def __str__(self):
        return '%s: %s' % (self.__class__.__name__, self.getDisplayText())
