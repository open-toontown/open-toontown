from pandac.PandaModules import *
from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownGlobals
ENDLESS_GAME = config.GetBool('endless-ring-game', 0)
NUM_RING_GROUPS = 16
MAX_TOONXZ = 10.0
CollisionRadius = 1.5
CollideMask = ToontownGlobals.CatchGameBitmask
RING_RADIUS = MAX_TOONXZ / 3.0 * 0.9
ringColors = ((TTLocalizer.ColorRed, VBase4(1.0, 0.4, 0.2, 1.0)),
 (TTLocalizer.ColorGreen, VBase4(0.0, 0.9, 0.2, 1.0)),
 (TTLocalizer.ColorOrange, VBase4(1.0, 0.5, 0.25, 1.0)),
 (TTLocalizer.ColorPurple, VBase4(1.0, 0.0, 1.0, 1.0)),
 (TTLocalizer.ColorWhite, VBase4(1.0, 1.0, 1.0, 1.0)),
 (TTLocalizer.ColorBlack, VBase4(0.0, 0.0, 0.0, 1.0)),
 (TTLocalizer.ColorYellow, VBase4(1.0, 1.0, 0.2, 1.0)))
ringColorSelection = [(0, 1, 2),
 3,
 4,
 5,
 6]
