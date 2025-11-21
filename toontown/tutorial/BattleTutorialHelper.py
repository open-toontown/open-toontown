from panda3d.core import *
from direct.gui.DirectGui import *
from direct.directnotify import DirectNotifyGlobal
from direct.showbase.DirectObject import DirectObject
from direct.showbase.MessengerGlobal import messenger
from direct.task.TaskManagerGlobal import taskMgr
from toontown.toonbase import TTLocalizer
from toontown.toontowngui import TTDialog

class BattleTutorialHelper(DirectObject):
    """Helper class to provide battle tutorial explanations during tutorial battles"""
    notify = DirectNotifyGlobal.directNotify.newCategory('BattleTutorialHelper')
    
    def __init__(self, battle):
        DirectObject.__init__(self)
        self.battle = battle
        self.currentExplanation = 0
        self.explanations = []
        self.explanationDialog = None
        self.setupExplanations()
        
    def setupExplanations(self):
        """Setup battle explanations"""
        self.explanations = [
            {'trigger': 'battle-start', 'message': TTLocalizer.TutorialBattleExplanation1, 'auto': True},
            {'trigger': 'gag-selected', 'message': TTLocalizer.TutorialBattleExplanation2, 'auto': False},
            {'trigger': 'attack-executed', 'message': TTLocalizer.TutorialBattleExplanation3, 'auto': True},
            {'trigger': 'cog-attack', 'message': TTLocalizer.TutorialBattleExplanation4, 'auto': True},
            {'trigger': 'toon-up-used', 'message': TTLocalizer.TutorialBattleExplanation5, 'auto': False},
            {'trigger': 'cog-defeated', 'message': TTLocalizer.TutorialBattleExplanation6, 'auto': True},
        ]
        
    def start(self):
        """Start battle tutorial"""
        self.accept('battle-start', self.onBattleStart)
        self.accept('gag-selected', self.onGagSelected)
        self.accept('attack-executed', self.onAttackExecuted)
        self.accept('cog-attack', self.onCogAttack)
        self.accept('toon-up-used', self.onToonUpUsed)
        self.accept('cog-defeated', self.onCogDefeated)
        messenger.send('battle-started')
        
    def stop(self):
        """Stop battle tutorial"""
        self.ignoreAll()
        # Remove any pending tasks
        taskMgr.remove('battle-tutorial-auto')
        taskMgr.remove('battle-start-delay')
        # Clean up dialog
        if self.explanationDialog:
            self.explanationDialog.cleanup()
            self.explanationDialog = None
            
    def showExplanation(self, message, autoAdvance=True):
        """Show a battle explanation"""
        # Clean up any existing dialog first
        if self.explanationDialog:
            self.explanationDialog.cleanup()
            self.explanationDialog = None
        
        # Remove any pending auto-advance tasks
        taskMgr.remove('battle-tutorial-auto')
        
        def handleAck(value):
            if self.explanationDialog:
                self.explanationDialog.cleanup()
                self.explanationDialog = None
            taskMgr.remove('battle-tutorial-auto')
            
        # Position dialog at top to avoid blocking gag selection
        # Use lower z-position and smaller scale to not interfere with battle UI
        from direct.gui.DirectGui import DGG
        self.explanationDialog = TTDialog.TTDialog(
            text=message,
            command=handleAck,
            style=TTDialog.Acknowledge,
            fadeScreen=0.05,
            pos=(0, 0, 0.55),
            scale=0.65,
            text_scale=0.05,
            text_wordwrap=28,
            sortOrder=DGG.NO_FADE_SORT_INDEX - 1
        )
        
        if autoAdvance:
            # Auto-advance after 4 seconds
            taskMgr.doMethodLater(4.0, lambda x: handleAck(0), 'battle-tutorial-auto')
            
    def onBattleStart(self):
        """Called when battle starts"""
        # Delay slightly to let battle UI load
        taskMgr.doMethodLater(1.0, lambda x: self.showExplanation(TTLocalizer.TutorialBattleExplanation1, autoAdvance=True), 'battle-start-delay')
        
    def onGagSelected(self, track, level):
        """Called when a gag is selected"""
        if track == 0:  # Throw
            self.showExplanation(TTLocalizer.TutorialBattleExplanation2, autoAdvance=False)
        elif track == 1:  # Squirt
            self.showExplanation(TTLocalizer.TutorialBattleExplanation2, autoAdvance=False)
            
    def onAttackExecuted(self):
        """Called when attack is executed"""
        self.showExplanation(TTLocalizer.TutorialBattleExplanation3)
        
    def onCogAttack(self):
        """Called when cog attacks"""
        self.showExplanation(TTLocalizer.TutorialBattleExplanation4)
        
    def onToonUpUsed(self):
        """Called when toon-up is used"""
        self.showExplanation(TTLocalizer.TutorialBattleExplanation5, autoAdvance=False)
        
    def onCogDefeated(self):
        """Called when cog is defeated"""
        self.showExplanation(TTLocalizer.TutorialBattleExplanation6)

