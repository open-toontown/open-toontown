from panda3d.core import *
from toontown.toontowngui import TTDialog
from toontown.toonbase import TTLocalizer
from direct.fsm import ClassicFSM, State
from direct.directnotify import DirectNotifyGlobal
from direct.showbase.MessengerGlobal import messenger

class TutorialForceAcknowledge:
    """Enhanced tutorial force acknowledge with multi-step guidance"""

    def __init__(self, doneEvent):
        self.doneEvent = doneEvent
        self.dialog = None
        self.currentStep = 0
        self.steps = []
        self.fsm = ClassicFSM.ClassicFSM('TutorialForceAcknowledge',
            [State.State('off', self.enterOff, self.exitOff, ['active']),
             State.State('active', self.enterActive, self.exitActive, ['off'])],
            'off', 'off')
        self.fsm.enterInitialState()
        self.setupSteps()
        return

    def setupSteps(self):
        """Setup tutorial guidance steps"""
        self.steps = [
            {'message': TTLocalizer.TutorialForceAcknowledgeMessage, 'next': 'complete'},
        ]

    def enter(self):
        """Enter the tutorial force acknowledge"""
        base.localAvatar.loop('neutral')
        self.doneStatus = {'mode': 'incomplete'}
        self.fsm.request('active')
        self.showStep(0)

    def enterOff(self):
        pass

    def exitOff(self):
        pass

    def enterActive(self):
        pass

    def exitActive(self):
        if self.dialog:
            self.dialog.cleanup()
            self.dialog = None

    def showStep(self, stepIndex):
        """Show a specific step"""
        if stepIndex >= len(self.steps):
            self.complete()
            return
            
        step = self.steps[stepIndex]
        msg = step['message']
        
        if self.dialog:
            self.dialog.cleanup()
            
        self.dialog = TTDialog.TTDialog(
            text=msg,
            command=self.handleOk,
            style=TTDialog.Acknowledge,
            fadeScreen=0.4,
            pos=(0, 0, 0.2),
            scale=0.9
        )

    def handleOk(self, value):
        """Handle OK button"""
        if self.currentStep < len(self.steps) - 1:
            self.currentStep += 1
            self.showStep(self.currentStep)
        else:
            self.complete()

    def complete(self):
        """Complete the tutorial"""
        self.doneStatus = {'mode': 'complete'}
        messenger.send(self.doneEvent, [self.doneStatus])
        self.fsm.request('off')

    def exit(self):
        """Exit the tutorial force acknowledge"""
        if self.dialog:
            self.dialog.cleanup()
            self.dialog = None
        self.fsm.request('off')
        return
