from panda3d.core import *
from direct.gui.DirectGui import *
from direct.fsm import ClassicFSM, State
from direct.directnotify import DirectNotifyGlobal
from direct.interval.IntervalGlobal import *
from direct.showbase.DirectObject import DirectObject
from direct.showbase.MessengerGlobal import messenger
from direct.task.TaskManagerGlobal import taskMgr
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from toontown.toonbase.ToonBaseGlobal import base
from toontown.toontowngui import TTDialog
from toontown.quest import BlinkingArrows

class TutorialGuide(DirectObject):
    """Comprehensive tutorial guide system with step-by-step guidance"""
    notify = DirectNotifyGlobal.directNotify.newCategory('TutorialGuide')
    
    def __init__(self):
        DirectObject.__init__(self)
        self.currentStep = 0
        self.steps = []
        self.arrow = None
        self.hintDialog = None
        self.progressDialog = None
        self.fsm = ClassicFSM.ClassicFSM('TutorialGuide',
            [State.State('off', self.enterOff, self.exitOff, ['active', 'waiting']),
             State.State('active', self.enterActive, self.exitActive, ['waiting', 'off']),
             State.State('waiting', self.enterWaiting, self.exitWaiting, ['active', 'off'])],
            'off', 'off')
        self.fsm.enterInitialState()
        self.setupSteps()
        
    def setupSteps(self):
        """Define all tutorial steps"""
        self.steps = [
            {'name': 'welcome', 'message': TTLocalizer.TutorialStepWelcome, 'target': None, 'action': None},
            {'name': 'chat', 'message': TTLocalizer.TutorialStepChat, 'target': 'chatNormalButton', 'action': 'click_chat'},
            {'name': 'friends', 'message': TTLocalizer.TutorialStepFriends, 'target': 'friendsButton', 'action': 'make_friend'},
            {'name': 'shticker', 'message': TTLocalizer.TutorialStepShticker, 'target': 'bookOpenButton', 'action': 'open_book'},
            {'name': 'laff', 'message': TTLocalizer.TutorialStepLaff, 'target': None, 'action': 'explain_laff'},
            {'name': 'gagshop', 'message': TTLocalizer.TutorialStepGagShop, 'target': None, 'action': 'visit_gagshop'},
            {'name': 'battle', 'message': TTLocalizer.TutorialStepBattle, 'target': None, 'action': 'explain_battle'},
            {'name': 'complete', 'message': TTLocalizer.TutorialStepComplete, 'target': None, 'action': None}
        ]
        
    def start(self):
        """Start the tutorial guide"""
        self.fsm.request('active')
        self.showStep(0)
        
    def stop(self):
        """Stop the tutorial guide"""
        self.fsm.request('off')
        self.cleanup()
        
    def enterOff(self):
        pass
        
    def exitOff(self):
        pass
        
    def enterActive(self):
        pass
        
    def exitActive(self):
        if self.hintDialog:
            self.hintDialog.cleanup()
            self.hintDialog = None
            
    def enterWaiting(self):
        pass
        
    def exitWaiting(self):
        pass
        
    def showStep(self, stepIndex):
        """Show a specific tutorial step"""
        if stepIndex >= len(self.steps):
            self.complete()
            return
            
        self.currentStep = stepIndex
        step = self.steps[stepIndex]
        
        # Show progress dialog
        progressText = TTLocalizer.TutorialProgress % (stepIndex + 1, len(self.steps))
        if self.progressDialog:
            self.progressDialog.cleanup()
        from panda3d.core import TextNode
        self.progressDialog = DirectLabel(
            text=progressText,
            text_scale=0.06,
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0.7),
            frameSize=(-1, 1, -0.3, 0.1),
            pos=(0, 0, 0.85),
            relief=DGG.FLAT,
            text_align=TextNode.ACenter
        )
        self.progressDialog.setBin('gui-popup', 100)
        
        # Show hint dialog
        if self.hintDialog:
            self.hintDialog.cleanup()
        self.hintDialog = TTDialog.TTDialog(
            text=step['message'],
            command=self.handleStepAcknowledge,
            style=TTDialog.Acknowledge,
            fadeScreen=0.3,
            pos=(0, 0, 0.3),
            scale=0.9
        )
        
        # Show arrow pointing to target
        if step['target']:
            self.showArrow(step['target'])
        else:
            self.hideArrow()
            
        # Set up action listeners
        if step['action']:
            self.setupActionListener(step['action'])
            
    def showArrow(self, targetName):
        """Show arrow pointing to a UI element"""
        self.hideArrow()
        
        # Try to find the target element
        target = None
        if hasattr(base.localAvatar, targetName):
            target = getattr(base.localAvatar, targetName)
        elif hasattr(base.localAvatar.book, targetName):
            target = getattr(base.localAvatar.book, targetName)
        elif hasattr(base.localAvatar.chatMgr, targetName):
            target = getattr(base.localAvatar.chatMgr, targetName)
            
        if target and hasattr(target, 'getPos'):
            # Create blinking arrow
            from direct.showbase.ShowBase import aspect2d
            self.arrow = BlinkingArrows.BlinkingArrows()
            pos = target.getPos(aspect2d)
            self.arrow.setPos(pos[0], pos[1], pos[2] + 0.3)
            self.arrow.setScale(1.5)
            self.arrow.show()
            
    def hideArrow(self):
        """Hide the arrow"""
        if self.arrow:
            self.arrow.hide()
            self.arrow = None
            
    def setupActionListener(self, action):
        """Set up listener for specific action"""
        if action == 'click_chat':
            self.acceptOnce('chat-normal-button', self.onActionComplete)
        elif action == 'make_friend':
            self.acceptOnce('friend-made', self.onActionComplete)
        elif action == 'open_book':
            self.acceptOnce('book-open', self.onActionComplete)
        elif action == 'explain_laff':
            # Auto-advance after showing explanation
            taskMgr.doMethodLater(3.0, self.onActionComplete, 'tutorial-laff-explain')
        elif action == 'visit_gagshop':
            self.acceptOnce('entered-gagshop', self.onActionComplete)
        elif action == 'explain_battle':
            self.acceptOnce('battle-started', self.onBattleStart)
            
    def onActionComplete(self, *args):
        """Called when an action is completed"""
        taskMgr.remove('tutorial-laff-explain')
        self.nextStep()
        
    def onBattleStart(self):
        """Called when battle starts"""
        self.showBattleTutorial()
        
    def showBattleTutorial(self):
        """Show comprehensive battle tutorial"""
        battleSteps = [
            TTLocalizer.TutorialBattleStep1,
            TTLocalizer.TutorialBattleStep2,
            TTLocalizer.TutorialBattleStep3,
            TTLocalizer.TutorialBattleStep4
        ]
        
        def showNextBattleStep(stepIndex=0):
            if stepIndex < len(battleSteps):
                if self.hintDialog:
                    self.hintDialog.cleanup()
                self.hintDialog = TTDialog.TTDialog(
                    text=battleSteps[stepIndex],
                    command=lambda x: showNextBattleStep(stepIndex + 1),
                    style=TTDialog.Acknowledge,
                    fadeScreen=0.2,
                    pos=(0, 0, 0.2),
                    scale=0.85
                )
            else:
                self.nextStep()
                
        showNextBattleStep()
        
    def handleStepAcknowledge(self, value):
        """Handle acknowledgment of current step"""
        step = self.steps[self.currentStep]
        
        # If step has an action, wait for it
        if step['action'] and step['action'] not in ['explain_laff', 'explain_battle']:
            self.fsm.request('waiting')
        else:
            self.nextStep()
            
    def nextStep(self):
        """Move to next step"""
        self.currentStep += 1
        if self.currentStep < len(self.steps):
            self.showStep(self.currentStep)
        else:
            self.complete()
            
    def complete(self):
        """Complete the tutorial"""
        if self.hintDialog:
            self.hintDialog.cleanup()
            self.hintDialog = None
        if self.progressDialog:
            self.progressDialog.cleanup()
            self.progressDialog = None
        self.hideArrow()
        self.fsm.request('off')
        messenger.send('tutorial-guide-complete')
        
    def cleanup(self):
        """Clean up all resources"""
        self.ignoreAll()
        if self.arrow:
            self.arrow.hide()
            self.arrow = None
        if self.hintDialog:
            self.hintDialog.cleanup()
            self.hintDialog = None
        if self.progressDialog:
            self.progressDialog.cleanup()
            self.progressDialog = None
        taskMgr.remove('tutorial-laff-explain')
        
    def skipCurrentStep(self):
        """Skip current step"""
        self.nextStep()

