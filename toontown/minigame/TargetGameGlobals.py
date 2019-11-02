from pandac.PandaModules import *
from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownGlobals
ENDLESS_GAME = config.GetBool('endless-ring-game', 0)
NUM_RING_GROUPS = 16
MAX_TOONXZ = 15.0
MAX_LAT = 5
MAX_FIELD_SPAN = 135
CollisionRadius = 1.5
CollideMask = ToontownGlobals.CatchGameBitmask
TARGET_RADIUS = MAX_TOONXZ / 3.0 * 0.9
targetColors = ((TTLocalizer.ColorRed, VBase4(1.0, 0.4, 0.2, 1.0)),
 (TTLocalizer.ColorGreen, VBase4(0.0, 0.9, 0.2, 1.0)),
 (TTLocalizer.ColorOrange, VBase4(1.0, 0.5, 0.25, 1.0)),
 (TTLocalizer.ColorPurple, VBase4(1.0, 0.0, 1.0, 1.0)),
 (TTLocalizer.ColorWhite, VBase4(1.0, 1.0, 1.0, 1.0)),
 (TTLocalizer.ColorBlack, VBase4(0.0, 0.0, 0.0, 1.0)),
 (TTLocalizer.ColorYellow, VBase4(1.0, 1.0, 0.2, 1.0)))
ENVIRON_LENGTH = 300
ENVIRON_WIDTH = 150.0
ringColorSelection = [(0, 1, 2),
 3,
 4,
 5,
 6]
colorRed = {}
colorRed['Red'] = 1.0
colorRed['Green'] = 0.0
colorRed['Blue'] = 0.0
colorRed['Alpha'] = 0.5
colorBlue = {}
colorBlue['Red'] = 0.0
colorBlue['Green'] = 0.0
colorBlue['Blue'] = 1.0
colorBlue['Alpha'] = 0.5
colorGreen = {}
colorGreen['Red'] = 0.0
colorGreen['Green'] = 1.0
colorGreen['Blue'] = 0.0
colorGreen['Alpha'] = 0.5
colorYellow = {}
colorYellow['Red'] = 1.0
colorYellow['Green'] = 1.0
colorYellow['Blue'] = 0.0
colorYellow['Alpha'] = 0.5
colorPurple = {}
colorPurple['Red'] = 0.75
colorPurple['Green'] = 0.0
colorPurple['Blue'] = 1.0
colorPurple['Alpha'] = 0.5
colorOrange = {}
colorOrange['Red'] = 1.0
colorOrange['Green'] = 0.6
colorOrange['Blue'] = 0.0
colorOrange['Alpha'] = 0.5
colorBlack = {}
colorBlack['Red'] = 0.0
colorBlack['Green'] = 0.0
colorBlack['Blue'] = 0.0
colorBlack['Alpha'] = 1.0
colorWhite = {}
colorWhite['Red'] = 1.0
colorWhite['Green'] = 1.0
colorWhite['Blue'] = 1.0
colorWhite['Alpha'] = 1.0
difficultyPatterns = {ToontownGlobals.ToontownCentral: [[8,
                                    4,
                                    2,
                                    0],
                                   [10,
                                    16,
                                    21,
                                    28],
                                   [31,
                                    15,
                                    7,
                                    3.5],
                                   [colorRed,
                                    colorGreen,
                                    colorBlue,
                                    colorYellow],
                                   [2,
                                    2,
                                    2,
                                    1],
                                   10,
                                   2],
 ToontownGlobals.DonaldsDock: [[7,
                                4,
                                2,
                                0],
                               [11,
                                17,
                                23,
                                32],
                               [29,
                                13,
                                6.5,
                                3.2],
                               [colorRed,
                                colorGreen,
                                colorBlue,
                                colorYellow],
                               [2,
                                2,
                                2,
                                1],
                               9,
                               2],
 ToontownGlobals.DaisyGardens: [[6,
                                 4,
                                 2,
                                 0],
                                [11,
                                 18,
                                 25,
                                 34],
                                [29,
                                 13,
                                 6.5,
                                 3.1],
                                [colorRed,
                                 colorGreen,
                                 colorBlue,
                                 colorYellow],
                                [2,
                                 2,
                                 2,
                                 1],
                                8,
                                2],
 ToontownGlobals.MinniesMelodyland: [[6,
                                      4,
                                      2,
                                      0],
                                     [12,
                                      19,
                                      27,
                                      37],
                                     [28,
                                      12,
                                      6,
                                      3.0],
                                     [colorGreen,
                                      colorBlue,
                                      colorYellow,
                                      colorPurple],
                                     [2,
                                      2,
                                      2,
                                      1],
                                     8,
                                     2],
 ToontownGlobals.TheBrrrgh: [[5,
                              4,
                              2,
                              0],
                             [12,
                              20,
                              29,
                              40],
                             [25,
                              12,
                              5.5,
                              2.5],
                             [colorGreen,
                              colorBlue,
                              colorYellow,
                              colorPurple],
                             [2,
                              2,
                              2,
                              1],
                             7,
                             2],
 ToontownGlobals.DonaldsDreamland: [[4,
                                     3,
                                     1,
                                     0],
                                    [12,
                                     21,
                                     31,
                                     42],
                                    [20,
                                     10,
                                     4.5,
                                     2.0],
                                    [colorBlue,
                                     colorYellow,
                                     colorPurple,
                                     colorOrange],
                                    [2,
                                     2,
                                     2,
                                     1],
                                    7,
                                    2]}
