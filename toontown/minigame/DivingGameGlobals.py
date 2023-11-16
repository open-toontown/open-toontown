from panda3d.core import ConfigVariableBool
from toontown.toonbase import ToontownGlobals

ENDLESS_GAME = ConfigVariableBool('endless-maze-game', 0).getValue()
NUM_SPAWNERS = 6
GAME_DURATION = 60.0
CollideMask = ToontownGlobals.CatchGameBitmask
