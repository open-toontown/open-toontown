""" SuitPlannerTutorial module: contains the SuitPlannerTutorial class
    which handles management of the suit you will fight during the
    tutorial."""

from otp.ai.AIBaseGlobal import *

from direct.directnotify import DirectNotifyGlobal
from toontown.suit import DistributedTutorialSuitAI
from . import TutorialBattleManagerAI

class SuitPlannerTutorialAI:
    """
    SuitPlannerTutorialAI: manages the single suit that you fight during
    the tutorial.
    """

    notify = DirectNotifyGlobal.directNotify.newCategory(
        'SuitPlannerTutorialAI')

    def __init__(self, air, zoneId, battleOverCallback):
        # Store these things
        self.zoneId = zoneId
        self.air = air
        self.battle = None
        # This callback will be used to open the HQ doors when the
        # battle is over.
        self.battleOverCallback = battleOverCallback

        # Create a battle manager
        self.battleMgr = TutorialBattleManagerAI.TutorialBattleManagerAI(
            self.air)

        # Create a flunky
        newSuit = DistributedTutorialSuitAI.DistributedTutorialSuitAI(self.air, self)
        newSuit.setupSuitDNA(1, 1, "c")
        # This is a special tutorial path state
        newSuit.generateWithRequired(self.zoneId)
        self.suit = newSuit

    def cleanup(self):
        self.zoneId = None
        self.air = None
        if self.suit:
            self.suit.requestDelete()
            self.suit = None
        if self.battle:
            #self.battle.requestDelete()
            #RAU made to kill the mem leak when you close the window in the middle of the battle tutorial
            cellId = self.battle.battleCellId
            battleMgr = self.battle.battleMgr
            if cellId in battleMgr.cellId2battle:
                battleMgr.destroy(self.battle)
            
            self.battle = None

    def getDoId(self):
        # This is here because the suit expects the suit planner to be
        # a distributed object, if it has a suit planner. We want it to
        # have a suit planner, but not a distributed one, so we return
        # 0 when asked what our DoId is. Kind of hackful, I guess.
        return 0

    def requestBattle(self, zoneId, suit, toonId):
        # 70, 20, 0 is a battle cell position that I just made up.
        self.battle = self.battleMgr.newBattle(
            zoneId, zoneId, Vec3(35, 20, 0),
            suit, toonId,
            finishCallback=self.battleOverCallback)
        return 1

    def removeSuit(self, suit):
        # Get rid of the suit.
        suit.requestDelete()
        self.suit = None
