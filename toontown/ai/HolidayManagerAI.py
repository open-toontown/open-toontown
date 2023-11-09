#################################################################
# File: HolidayManagerAI.py
# Purpose: Coming Soon...
#################################################################
import datetime
from datetime import timedelta
from enum import IntEnum

#################################################################
# Direct Specific Modules
#################################################################
from direct.directnotify import DirectNotifyGlobal
from direct.showbase.PythonUtil import SingletonError
from direct.task import Task

#################################################################
# Toontown Specific Modules
#################################################################
from toontown.ai.HolidayInfoOncely import *
from toontown.ai.HolidayInfoDaily import *
from toontown.ai.HolidayInfoWeekly import *
from toontown.ai.HolidayInfoMonthly import *
from toontown.ai.HolidayInfoYearly import *
from toontown.ai.HolidayInfoRelatively import *
from toontown.ai import HolidayRepeaterAI
from toontown.effects import FireworkManagerAI
from toontown.fishing import BingoNightHolidayAI
from toontown.suit import HolidaySuitInvasionManagerAI
from toontown.ai import BlackCatHolidayMgrAI
from toontown.ai import ScavengerHuntMgrAI
from toontown.ai import TrickOrTreatMgrAI
from toontown.ai import WinterCarolingMgrAI
from toontown.ai import ResistanceEventMgrAI
from toontown.ai import PolarPlaceEventMgrAI
from toontown.toonbase import ToontownGlobals
from toontown.racing import RaceManagerAI
from toontown.minigame import TrolleyHolidayMgrAI
from toontown.minigame import TrolleyWeekendMgrAI
from toontown.ai import RoamingTrialerWeekendMgrAI
from toontown.ai import CostumeManagerAI
from toontown.ai import AprilFoolsManagerAI
from toontown.ai import HydrantZeroHolidayAI
from toontown.ai import MailboxZeroHolidayAI
from toontown.ai import TrashcanZeroHolidayAI
from toontown.ai import HydrantBuffHolidayAI
from toontown.ai import MailboxBuffHolidayAI
from toontown.ai import TrashcanBuffHolidayAI
from toontown.ai import ValentinesDayMgrAI
from toontown.ai import SillyMeterHolidayAI
#################################################################
# Python Specific Modules
#################################################################
import random
import time

#################################################################
# Global Enumerations and Constants
#################################################################
Month = IntEnum('Month', ('JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', \
              'MAY', 'JUNE', 'JULY', 'AUGUST', 'SEPTEMBER', \
              'OCTOBER', 'NOVEMBER', 'DECEMBER'))

Day = IntEnum('Day', 'MONDAY TUESDAY WEDNESDAY THURSDAY \
            FRIDAY SATURDAY SUNDAY')

OncelyMultipleStartHolidays = (ToontownGlobals.COLD_CALLER_INVASION,
                               ToontownGlobals.BEAN_COUNTER_INVASION,
                               ToontownGlobals.DOUBLE_TALKER_INVASION,
                               ToontownGlobals.DOWNSIZER_INVASION,
                               ToontownGlobals.DOWN_SIZER_INVASION,
                               ToontownGlobals.MOVER_AND_SHAKER_INVASION,
                               ToontownGlobals.DOUBLETALKER_INVASION,
                               ToontownGlobals.YES_MAN_INVASION,
                               ToontownGlobals.PENNY_PINCHER_INVASION,
                               ToontownGlobals.TIGHTWAD_INVASION,
                               ToontownGlobals.TELEMARKETER_INVASION,
                               ToontownGlobals.HEADHUNTER_INVASION,
                               ToontownGlobals.SPINDOCTOR_INVASION,
                               ToontownGlobals.MONEYBAGS_INVASION,
                               ToontownGlobals.TWOFACES_INVASION,
                               ToontownGlobals.NAME_DROPPER_INVASION,
                               ToontownGlobals.MICROMANAGER_INVASION,
                               ToontownGlobals.NUMBER_CRUNCHER_INVASION,
                               ToontownGlobals.AMBULANCE_CHASER_INVASION,
                               ToontownGlobals.MINGLER_INVASION,
                               ToontownGlobals.LOANSHARK_INVASION,
                               ToontownGlobals.CORPORATE_RAIDER_INVASION,
                               ToontownGlobals.LEGAL_EAGLE_INVASION,
                               ToontownGlobals.MR_HOLLYWOOD_INVASION,
                               ToontownGlobals.ROBBER_BARON_INVASION,
                               ToontownGlobals.BIG_WIG_INVASION,
                               ToontownGlobals.BIG_CHEESE_INVASION,                               
                               )

# These variables are too useful in debugging holidays, keeping them around
# StartMinute = 19
# StartHour = 19

# we are creating this system so it's easier to start holidays on the test server ahead of schedule
TestServerHolidayDaysAhead = simbase.config.GetInt("test-server-holiday-days-ahead", 0)
TestServerHolidayTimeDelta = timedelta(days = TestServerHolidayDaysAhead)

# TODO figure out how to make this work for more than just oncely holidays
OriginalHolidays = {
    ToontownGlobals.HYDRANT_ZERO_HOLIDAY: 
    { 'startAndEndPairs':       [datetime.datetime( 2010, Month.MAY.value, 5, 8, 0), # firstMoveArmUp1
                                          datetime.datetime( 2010, Month.JUNE,   12,  11, 55),],
      'phaseDates': [datetime.datetime( 2010, Month.MAY, 9,  11, 0o5), # firstMoveStruggle
                     datetime.datetime( 2010, Month.MAY,    13,  11, 0o5), # firstMoveArmUp2
                     datetime.datetime( 2010, Month.MAY,    18,  11, 0o5), # firstMoveJump hydrants around hydrant zero animate
                     datetime.datetime( 2010, Month.MAY,   21,  16, 0o5), # firstMoveJumpBalance
                     datetime.datetime( 2010, Month.MAY,   22,  15, 30), # firstMoveArmUp3 Hydrant Zero and his hydrant pals get more elaborate animations
                     datetime.datetime( 2010, Month.JUNE,   3,  15, 30), # firstMoveJumpSpin 
                    ],
    },

    ToontownGlobals.TRASHCAN_ZERO_HOLIDAY: 
    { 'startAndEndPairs':       [datetime.datetime( 2010, Month.MAY, 8,  12, 15), # firstMoveLidFLip1
                                          datetime.datetime( 2010, Month.JUNE,  12,  11, 55),],
      'phaseDates': [datetime.datetime( 2010, Month.MAY, 11,  11, 0o5), # firstMoveStruggle
                     datetime.datetime( 2010, Month.MAY,    15,  11, 0o5), # firstMoveLidFlip2
                     datetime.datetime( 2010, Month.MAY,   20,  11, 0o5), # firstMoveJump trashcans around trashcan zero animate
                     datetime.datetime( 2010, Month.MAY,   23,  11, 0o5), # firstMoveLidFlip3
                     datetime.datetime( 2010, Month.MAY,   29,  14, 10), # firstMoveJumpHit Trashcan Zero and his trashcan pals get more elaborate animations
                     datetime.datetime( 2010, Month.JUNE,   6,  14, 0o1), # firstMoveJumpJuggle
                     ],
    },    

    ToontownGlobals.MAILBOX_ZERO_HOLIDAY: 
    { 'startAndEndPairs':       [datetime.datetime( 2010, Month.MAY,    9,  12, 00), # firstMoveFlagSpin1
                       datetime.datetime( 2010, Month.JUNE,  12,  11, 55),],
      'phaseDates': [datetime.datetime( 2010, Month.MAY,    16,  16, 55), # firstMoveStruggle & Jump
                     datetime.datetime( 2010, Month.MAY,   21,  16, 55), # firstMoveFlagSpin2
                     datetime.datetime( 2010, Month.MAY,   23,  17, 0o5), # firstMoveFlagSpin3 mailboxs around mailbox zero animate
                     datetime.datetime( 2010, Month.JUNE,   1,  11, 0o5), # firstMoveJumpSummersault
                     datetime.datetime( 2010, Month.JUNE,   5,  12, 0o1), # firstMoveJumpFall Mailbox Zero and his mailbox pals get more elaborate animations
                     datetime.datetime( 2010, Month.JUNE,   8,  11, 45), # firstMoveJump3Summersaults
                     ],
    },
    
    ToontownGlobals.SILLYMETER_HOLIDAY: 
    { 'startAndEndPairs':       [datetime.datetime( 2010, Month.MAY,    14,   0,  0o1),          # Stage 1 animates
                                         datetime.datetime( 2010, Month.JULY,  14,   0,  0o1),],
      'phaseDates': [datetime.datetime( 2010, Month.MAY,   17,   16,  0o1),    # Stage 1 animates, stage 2 built
                     datetime.datetime( 2010, Month.MAY,   19,   00,  0o1),           # Stage 1 loc 2
                     datetime.datetime( 2010, Month.MAY,   22,   14,  0o1),           # Stage 1 loc 3                     
                     datetime.datetime( 2010, Month.MAY,   24,   17,  0o1),           # Stage 1 loc 4
                     
                     datetime.datetime( 2010, Month.MAY,   26,   00,  0o1),           # Stage 2 loc 5
                     datetime.datetime( 2010, Month.MAY,   30,   10,  0o1),           # Stage 2 loc 6
                     
                     datetime.datetime( 2010, Month.JUNE,   2,   0,  0o1),           # Stage 3 is added and animates
                     datetime.datetime( 2010, Month.JUNE,   5,  12,  00),           # Stage 3 loc 8
                     datetime.datetime( 2010, Month.JUNE,   8,   10,  0o1),            # Stage 3 loc 9
                     
                     datetime.datetime( 2010, Month.JUNE,   9,   00,  0o1),            # Stage 4 animates
                     datetime.datetime( 2010, Month.JUNE,   12,   10,  0o1),          # Stage 4 loc 11
                     datetime.datetime( 2010, Month.JUNE,   12,  12,  0o1),           # Stage 4 loc 12
                     
                     datetime.datetime( 2010, Month.JUNE,   13,   13, 30),          # Stage 5 silly meter plummets
                     
                     datetime.datetime( 2010, Month.JUNE,   14,   0, 0o1),          # Scientist chatter change
                     
                     datetime.datetime( 2010, Month.JUNE, 28, 0, 0o1),                  # Silly meter shuts down
                     ],
    },

    ToontownGlobals.SILLY_SURGE_HOLIDAY: 
    { 'startAndEndPairs':       [datetime.datetime( 2010, Month.MAY,    14,   0,  0o1), 
                                         datetime.datetime( 2010, Month.JUNE,   13,   13,  30), ],     # Cogs invade and silly surges fizzle out
    },
    
    ToontownGlobals.TROUBLE_BOSSBOTS_4: # Down sizer
    { 'startAndEndPairs' : [datetime.datetime( 2009, Month.FEBRUARY, 1, 18, 0),
                                     datetime.datetime( 2009, Month.FEBRUARY, 1, 23, 0), ],
    },
    
    ToontownGlobals.DOWN_SIZER_INVASION: # Down sizer
    { 'startAndEndPairs' : [datetime.datetime( 2010, Month.JUNE, 13, 13, 30),
                                     datetime.datetime( 2010, Month.JUNE, 13, 17, 30), ],
    },
    
    ToontownGlobals.SELLBOT_SURPRISE_4:  # Mover & shaker
    { 'startAndEndPairs' : [datetime.datetime( 2009, Month.JANUARY, 11, 18, 0),
                                     datetime.datetime( 2009, Month.JANUARY, 11, 23, 0), ],
    },
    
    ToontownGlobals.MOVER_AND_SHAKER_INVASION:  # Mover & shaker
    { 'startAndEndPairs' : [datetime.datetime( 2010, Month.JUNE, 13, 18, 30),
                                     datetime.datetime( 2010, Month.JUNE, 13, 22, 30), ],
    },
    
    ToontownGlobals.LAWBOT_GAMBIT_2:    # Double talker
    { 'startAndEndPairs' : [datetime.datetime( 2009, Month.JANUARY, 24, 18, 0),
                                     datetime.datetime( 2009, Month.JANUARY, 24, 23, 0),],
    },
    
    ToontownGlobals.DOUBLETALKER_INVASION:    # Double talker
    { 'startAndEndPairs' : [datetime.datetime( 2010, Month.JUNE, 14, 2, 00),
                                     datetime.datetime( 2010, Month.JUNE, 14, 6, 00),
                                     
                                     datetime.datetime( 2010, Month.JUNE, 14, 10, 00),
                                     datetime.datetime( 2010, Month.JUNE, 14, 14, 00),
                                     
                                     datetime.datetime( 2010, Month.JUNE, 14, 18, 00),
                                     datetime.datetime( 2010, Month.JUNE, 14, 22, 00),],
    },    
    
    ToontownGlobals.YES_MAN_INVASION:    
    { 'startAndEndPairs' : [datetime.datetime( 2010, Month.JUNE, 15, 2, 00),
                                     datetime.datetime( 2010, Month.JUNE, 15, 6, 00),
                                     
                                     datetime.datetime( 2010, Month.JUNE, 15, 10, 00),
                                     datetime.datetime( 2010, Month.JUNE, 15, 14, 00),

                                     datetime.datetime( 2010, Month.JUNE, 15, 18, 00),
                                     datetime.datetime( 2010, Month.JUNE, 15, 22, 00),],
    },

    ToontownGlobals.CASHBOT_CONUNDRUM_2:    # Penny Pincher
    { 'startAndEndPairs' : [
                                     datetime.datetime( 2009, Month.JANUARY, 17, 18, 00),
                                     datetime.datetime( 2009, Month.JANUARY, 17, 23, 00),],
    },
    
    ToontownGlobals.PENNY_PINCHER_INVASION:    # Penny Pincher
    { 'startAndEndPairs' : [datetime.datetime( 2010, Month.JUNE, 16, 2, 00),
                                     datetime.datetime( 2010, Month.JUNE, 16, 6, 00),
                                     
                                     datetime.datetime( 2010, Month.JUNE, 16, 10, 00),
                                     datetime.datetime( 2010, Month.JUNE, 16, 14, 00),

                                     datetime.datetime( 2010, Month.JUNE, 16, 18, 00),
                                     datetime.datetime( 2010, Month.JUNE, 16, 22, 00),],
    },
    
    ToontownGlobals.TIGHTWAD_INVASION: 
    { 'startAndEndPairs' : [datetime.datetime( 2010, Month.JUNE, 17, 2, 00),
                                     datetime.datetime( 2010, Month.JUNE, 17, 6, 00),
                                     
                                     datetime.datetime( 2010, Month.JUNE, 17, 10, 00),
                                     datetime.datetime( 2010, Month.JUNE, 17, 14, 00),

                                     datetime.datetime( 2010, Month.JUNE, 17, 18, 00),
                                     datetime.datetime( 2010, Month.JUNE, 17, 22, 00),],
    },
    
    ToontownGlobals.TELEMARKETER_INVASION: 
    { 'startAndEndPairs' : [datetime.datetime( 2010, Month.JUNE, 18, 2, 00),
                                     datetime.datetime( 2010, Month.JUNE, 18, 6, 00),
                                     
                                     datetime.datetime( 2010, Month.JUNE, 18, 10, 00),
                                     datetime.datetime( 2010, Month.JUNE, 18, 14, 00),

                                     datetime.datetime( 2010, Month.JUNE, 18, 18, 00),
                                     datetime.datetime( 2010, Month.JUNE, 18, 22, 00),],
    },
    
    ToontownGlobals.HEADHUNTER_INVASION: 
    { 'startAndEndPairs' : [datetime.datetime( 2010, Month.JUNE, 19, 2, 00),
                                     datetime.datetime( 2010, Month.JUNE, 19, 4, 59),
                                     
                                     datetime.datetime( 2010, Month.JUNE, 19, 10, 00),
                                     datetime.datetime( 2010, Month.JUNE, 19, 12, 59),

                                     datetime.datetime( 2010, Month.JUNE, 19, 18, 00),
                                     datetime.datetime( 2010, Month.JUNE, 19, 20, 59),],
    },
    
    ToontownGlobals.SPINDOCTOR_INVASION: 
    { 'startAndEndPairs' : [datetime.datetime( 2010, Month.JUNE, 19, 5, 00),
                                     datetime.datetime( 2010, Month.JUNE, 19, 8, 00),
                                     
                                     datetime.datetime( 2010, Month.JUNE, 19, 13, 00),
                                     datetime.datetime( 2010, Month.JUNE, 19, 16, 00),

                                     datetime.datetime( 2010, Month.JUNE, 19, 21, 00),
                                     datetime.datetime( 2010, Month.JUNE, 19, 23, 59),],
    },
    
    ToontownGlobals.MONEYBAGS_INVASION: 
    { 'startAndEndPairs' : [datetime.datetime( 2010, Month.JUNE, 20, 2, 00),
                                     datetime.datetime( 2010, Month.JUNE, 20, 4, 59),
                                     
                                     datetime.datetime( 2010, Month.JUNE, 20, 10, 00),
                                     datetime.datetime( 2010, Month.JUNE, 20, 12, 59),

                                     datetime.datetime( 2010, Month.JUNE, 20, 18, 00),
                                     datetime.datetime( 2010, Month.JUNE, 20, 20, 59),],
    },
    
    ToontownGlobals.TWOFACES_INVASION: 
    { 'startAndEndPairs' : [datetime.datetime( 2010, Month.JUNE, 20, 5, 00),
                                     datetime.datetime( 2010, Month.JUNE, 20, 8, 00),
                                     
                                     datetime.datetime( 2010, Month.JUNE, 20, 13, 00),
                                     datetime.datetime( 2010, Month.JUNE, 20, 16, 00),

                                     datetime.datetime( 2010, Month.JUNE, 20, 21, 00),
                                     datetime.datetime( 2010, Month.JUNE, 20, 23, 59),],
    },
    
    ToontownGlobals.SELLBOT_SURPRISE_2:     # Name dropper
    { 'startAndEndPairs' : [datetime.datetime( 2009, Month.JANUARY, 10, 18, 00),
                                     datetime.datetime( 2009, Month.JANUARY, 10, 23, 00),],    
    },
    
    ToontownGlobals.NAME_DROPPER_INVASION:     # Name dropper
    { 'startAndEndPairs' : [datetime.datetime( 2010, Month.JUNE, 21, 2, 00),
                                     datetime.datetime( 2010, Month.JUNE, 21, 6, 00),
                                     
                                     datetime.datetime( 2010, Month.JUNE, 21, 10, 00),
                                     datetime.datetime( 2010, Month.JUNE, 21, 14, 00),

                                     datetime.datetime( 2010, Month.JUNE, 21, 18, 00),
                                     datetime.datetime( 2010, Month.JUNE, 21, 22, 00),],    
    },
    
    ToontownGlobals.TROUBLE_BOSSBOTS_3:     # Micromanager
    { 'startAndEndPairs' : [datetime.datetime( 2009, Month.FEBRUARY, 10, 0, 00),
                                     datetime.datetime( 2009, Month.FEBRUARY, 15, 0, 00),],    
    },
    
    ToontownGlobals.MICROMANAGER_INVASION:     # Micromanager
    { 'startAndEndPairs' : [datetime.datetime( 2010, Month.JUNE, 22, 2, 00),
                                     datetime.datetime( 2010, Month.JUNE, 22, 6, 00),
                                     
                                     datetime.datetime( 2010, Month.JUNE, 22, 10, 00),
                                     datetime.datetime( 2010, Month.JUNE, 22, 14, 00),

                                     datetime.datetime( 2010, Month.JUNE, 22, 18, 00),
                                     datetime.datetime( 2010, Month.JUNE, 22, 22, 00),],    
    },
    
    ToontownGlobals.CASHBOT_CONUNDRUM_4:    # Number cruncher
    { 'startAndEndPairs' : [datetime.datetime( 2009, Month.JANUARY, 18, 18, 00),
                                     datetime.datetime( 2009, Month.JANUARY, 18, 23, 00),],    
    },
    
    ToontownGlobals.NUMBER_CRUNCHER_INVASION:    # Number cruncher
    { 'startAndEndPairs' : [datetime.datetime( 2010, Month.JUNE, 23, 2, 00),
                                     datetime.datetime( 2010, Month.JUNE, 23, 6, 00),
                                     
                                     datetime.datetime( 2010, Month.JUNE, 23, 10, 00),
                                     datetime.datetime( 2010, Month.JUNE, 23, 14, 00),

                                     datetime.datetime( 2010, Month.JUNE, 23, 18, 00),
                                     datetime.datetime( 2010, Month.JUNE, 23, 22, 00),],    
    },
    
    ToontownGlobals.LAWBOT_GAMBIT_3:    # Ambulance chaser
    { 'startAndEndPairs' : [datetime.datetime( 2009, Month.JANUARY, 25, 10, 00),
                                     datetime.datetime( 2009, Month.JANUARY, 25, 15, 00),],    
    },
    
    ToontownGlobals.AMBULANCE_CHASER_INVASION:    # Ambulance chaser
    { 'startAndEndPairs' : [datetime.datetime( 2010, Month.JUNE, 24, 2, 00),
                                     datetime.datetime( 2010, Month.JUNE, 24, 6, 00),
                                     
                                     datetime.datetime( 2010, Month.JUNE, 24, 10, 00),
                                     datetime.datetime( 2010, Month.JUNE, 24, 14, 00),

                                     datetime.datetime( 2010, Month.JUNE, 24, 18, 00),
                                     datetime.datetime( 2010, Month.JUNE, 24, 22, 00),],    
    },
    
    ToontownGlobals.MINGLER_INVASION: 
    { 'startAndEndPairs' : [datetime.datetime( 2010, Month.JUNE, 25, 2, 00),
                                     datetime.datetime( 2010, Month.JUNE, 25, 4, 59),
                                     
                                     datetime.datetime( 2010, Month.JUNE, 25, 10, 00),
                                     datetime.datetime( 2010, Month.JUNE, 25, 12, 59),

                                     datetime.datetime( 2010, Month.JUNE, 25, 18, 00),
                                     datetime.datetime( 2010, Month.JUNE, 25, 20, 59),],    
    },
    
    ToontownGlobals.LOANSHARK_INVASION: 
    { 'startAndEndPairs' : [datetime.datetime( 2010, Month.JUNE, 25, 5, 00),
                                     datetime.datetime( 2010, Month.JUNE, 25, 8, 00),
                                     
                                     datetime.datetime( 2010, Month.JUNE, 25, 13, 00),
                                     datetime.datetime( 2010, Month.JUNE, 25, 16, 00),

                                     datetime.datetime( 2010, Month.JUNE, 25, 21, 00),
                                     datetime.datetime( 2010, Month.JUNE, 25, 23, 59),],    
    },    
    
    ToontownGlobals.CORPORATE_RAIDER_INVASION:
    { 'startAndEndPairs' : [datetime.datetime( 2010, Month.JUNE, 26, 2, 00),
                                     datetime.datetime( 2010, Month.JUNE, 26, 4, 59),
                                     
                                     datetime.datetime( 2010, Month.JUNE, 26, 10, 00),
                                     datetime.datetime( 2010, Month.JUNE, 26, 12, 59),

                                     datetime.datetime( 2010, Month.JUNE, 26, 18, 00),
                                     datetime.datetime( 2010, Month.JUNE, 26, 20, 59),],    
    },    
    
    ToontownGlobals.LEGAL_EAGLE_INVASION:
    { 'startAndEndPairs' : [datetime.datetime( 2010, Month.JUNE, 26, 5, 00),
                                     datetime.datetime( 2010, Month.JUNE, 26, 8, 00),
                                     
                                     datetime.datetime( 2010, Month.JUNE, 26, 13, 00),
                                     datetime.datetime( 2010, Month.JUNE, 26, 16, 00),

                                     datetime.datetime( 2010, Month.JUNE, 26, 21, 00),
                                     datetime.datetime( 2010, Month.JUNE, 26, 23, 59),],    
    },    
    
    ToontownGlobals.MR_HOLLYWOOD_INVASION:
    { 'startAndEndPairs' : [datetime.datetime( 2010, Month.JUNE, 27, 0, 00),
                                     datetime.datetime( 2010, Month.JUNE, 27, 2, 00),
                                     
                                     datetime.datetime( 2010, Month.JUNE, 27, 8, 00),
                                     datetime.datetime( 2010, Month.JUNE, 27, 10, 00),

                                     datetime.datetime( 2010, Month.JUNE, 27, 16, 00),
                                     datetime.datetime( 2010, Month.JUNE, 27, 18, 00),],    
    },    
    
    ToontownGlobals.ROBBER_BARON_INVASION:
    { 'startAndEndPairs' : [datetime.datetime( 2010, Month.JUNE, 27, 2, 0o1),
                                     datetime.datetime( 2010, Month.JUNE, 27, 4, 00),
                                     
                                     datetime.datetime( 2010, Month.JUNE, 27, 10, 0o1),
                                     datetime.datetime( 2010, Month.JUNE, 27, 12, 00),

                                     datetime.datetime( 2010, Month.JUNE, 27, 18, 0o1),
                                     datetime.datetime( 2010, Month.JUNE, 27, 20, 00),],    
    },    
    
    ToontownGlobals.BIG_WIG_INVASION:
    { 'startAndEndPairs' : [datetime.datetime( 2010, Month.JUNE, 27, 4, 0o1),
                                     datetime.datetime( 2010, Month.JUNE, 27, 6, 00),
                                     
                                     datetime.datetime( 2010, Month.JUNE, 27, 12, 0o1),
                                     datetime.datetime( 2010, Month.JUNE, 27, 14, 00),

                                     datetime.datetime( 2010, Month.JUNE, 27, 20, 0o1),
                                     datetime.datetime( 2010, Month.JUNE, 27, 22, 00),],    
    },    
    
    ToontownGlobals.BIG_CHEESE_INVASION:
    { 'startAndEndPairs' : [datetime.datetime( 2010, Month.JUNE, 27, 6, 0o1),
                                     datetime.datetime( 2010, Month.JUNE, 27, 8, 00),
                                     
                                     datetime.datetime( 2010, Month.JUNE, 27, 14, 0o1),
                                     datetime.datetime( 2010, Month.JUNE, 27, 16, 00),

                                     datetime.datetime( 2010, Month.JUNE, 27, 22, 0o1),
                                     datetime.datetime( 2010, Month.JUNE, 27, 23, 59),],    
    },    
    
    ToontownGlobals.HYDRANTS_BUFF_BATTLES: 
    { 'startAndEndPairs':    [datetime.datetime( 2010, Month.JUNE,   12,  12, 0o1), # they just animate but don't help
                                        datetime.datetime( 2031, Month.JUNE,   7,   3,  0),],
      'phaseDates': [datetime.datetime( 2010, Month.JUNE,   14,   3,  0),], # they're actually helping now
    },

    ToontownGlobals.MAILBOXES_BUFF_BATTLES: 
    { 'startAndEndPairs':       [datetime.datetime( 2010, Month.JUNE,   12,  12, 0o1), # they just animate but don't help
                                           datetime.datetime( 2031, Month.JUNE,  11,   3,  0),], #forever, impressive if we hit this!
      'phaseDates': [datetime.datetime( 2010, Month.JUNE,  18,   00,  0o1),], # they're actually helping now      
    },

    ToontownGlobals.TRASHCANS_BUFF_BATTLES: 
    { 'startAndEndPairs':       [datetime.datetime( 2010, Month.JUNE,   12,  12, 0o1), # they just animate but don't help
                                          datetime.datetime( 2031, Month.JUNE,  11,   3,  0), ], #forever, impressive if we hit this!
      'phaseDates': [datetime.datetime( 2010, Month.JUNE,  18,  00,  0o1),], # they're actually helping now 
    },
    
}

AdjustedHolidays = {}

def adjustHolidaysForTestServer():
    for holidayId in OriginalHolidays:
        AdjustedHolidays[holidayId] = {'startAndEndPairs':[], 'phaseDates': []}
        newStartAndEndPairs = []
        
        for curDate in OriginalHolidays[holidayId]['startAndEndPairs']:
            adjusted = curDate - TestServerHolidayTimeDelta
            newStartAndEndPairs.append((adjusted.year, adjusted.month, adjusted.day, adjusted.hour, adjusted.minute, adjusted.second))
        AdjustedHolidays[holidayId]['startAndEndPairs'] = newStartAndEndPairs
        newPhaseDates = []
        if 'phaseDates' in OriginalHolidays[holidayId]:
            for curDate in OriginalHolidays[holidayId]['phaseDates']:
                adjusted = curDate - TestServerHolidayTimeDelta
                newPhaseDates.append((adjusted.year, adjusted.month, adjusted.day,
                                      adjusted.hour, adjusted.minute, adjusted.second))
        AdjustedHolidays[holidayId]['phaseDates'] = newPhaseDates

adjustHolidaysForTestServer()
# TODO put this in a notify? although it should be an info if done so
print("AdjustedHolidays = %s" % AdjustedHolidays)        

class HolidayManagerAI:
    notify = DirectNotifyGlobal.directNotify.newCategory('HolidayManagerAI')

    # { Month: [days] }, (startTime), (endTime)]

    holidaysCommon = {
        ToontownGlobals.NEWYEARS_FIREWORKS: HolidayInfo_Yearly(
        FireworkManagerAI.FireworkManagerAI,
        [(Month.DECEMBER, 31, 0, 30, 0),
          (Month.JANUARY, 2, 0, 30, 0)],
        displayOnCalendar = True,
        ),

#        ToontownGlobals.SKELECOG_INVASION: HolidayInfo_Yearly(
#        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
#        [(Month.APRIL, 15, 10, 0, 0),        # 10am-3pm PST, 1pm-6pm EST
#          (Month.APRIL, 15, 15, 0, 0),

#          (Month.APRIL, 15, 18, 0, 0),       # 6pm-11pm PST, 9pm-2am EST
#          (Month.APRIL, 15, 23, 0, 0)],
#        displayOnCalendar = True,
#        ),

#        ToontownGlobals.MR_HOLLYWOOD_INVASION: HolidayInfo_Yearly(
#        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
#        [(Month.MAY, 24, 0, 0, 1),
#          (Month.MAY, 24, 8, 59, 59),
#          (Month.MAY, 24, 15, 0, 1),
#          (Month.MAY, 24, 23, 59, 59),

#          (Month.MAY, 25, 6, 0, 1),
#          (Month.MAY, 25, 14, 59, 59),
#          (Month.MAY, 25, 21, 0, 1),
#          (Month.MAY, 26, 5, 59, 59),

#          (Month.MAY, 26, 12, 0, 1),
#          (Month.MAY, 26, 20, 59, 59)],
#        displayOnCalendar = True,
#        ),

        ToontownGlobals.HALLOWEEN: HolidayInfo_Yearly(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        [ (Month.OCTOBER, 31, 0o2, 0, 0),         # 2am-6am PST
          (Month.OCTOBER, 31, 0o7, 0, 0),
        
          (Month.OCTOBER, 31, 10, 0, 0),        # 10am-3pm PST, 1pm-6pm EST
          (Month.OCTOBER, 31, 15, 0, 0),

          (Month.OCTOBER, 31, 18, 0, 0),        # 6pm-10pm PST, 9pm-1am EST
          (Month.OCTOBER, 31, 23, 0, 0),
          
          (Month.NOVEMBER, 1, 0o2, 0, 0),        # 2am-6am PST
          (Month.NOVEMBER, 1, 0o7, 0, 0),

          (Month.NOVEMBER, 1, 10, 0, 0),        # 10am-2pm PST, 1pm-5pm EST
          (Month.NOVEMBER, 1, 15, 0, 0),

          (Month.NOVEMBER, 1, 18, 0, 0),        # 6pm-10pm PST, 9pm-1am EST
          (Month.NOVEMBER, 1, 23, 0, 0)],
        displayOnCalendar = True,
        ),

        #To occur at the same time as Halloween
        ToontownGlobals.HALLOWEEN_PROPS: HolidayInfo_Yearly(
        None,
        [(Month.OCTOBER, 20, 0, 0, 1),
         (Month.NOVEMBER, 1, 23, 59, 59),
         ],
        displayOnCalendar = False,
        ),

        # Valentines Day
        ToontownGlobals.VALENTINES_DAY: HolidayInfo_Yearly(
        ValentinesDayMgrAI.ValentinesDayMgrAI,
        [(Month.FEBRUARY, 8, 0, 0, 1),
         (Month.FEBRUARY, 16, 23, 59, 59),
         ],
        displayOnCalendar = True,
        ),
        
        #To occur at the same time as april fools 2009
        ToontownGlobals.CRASHED_LEADERBOARD: HolidayInfo_Oncely(
        None,
        [(2009, Month.APRIL, 1, 0, 0, 1),
         (2009, Month.MAY, 21, 23, 58, 59),
         ],
        displayOnCalendar = False,
        ),

        #To occur at the same time as Halloween
        #TODO: better way to have intervals with holiday events
        #instead of defining it per hour each day
        ToontownGlobals.HALLOWEEN_COSTUMES: HolidayInfo_Yearly(
        CostumeManagerAI.CostumeManagerAI,
        [(Month.OCTOBER, 27, 0, 0, 1),          # 12am-1am PST, 3am-4am EST
          (Month.OCTOBER, 27, 0, 59, 59),

          (Month.OCTOBER, 27, 2, 0, 1),
          (Month.OCTOBER, 27, 2, 59, 59),

          (Month.OCTOBER, 27, 4, 0, 1),
          (Month.OCTOBER, 27, 4, 59, 59),

          (Month.OCTOBER, 27, 6, 0, 1),
          (Month.OCTOBER, 27, 6, 59, 59),

          (Month.OCTOBER, 27, 8, 0, 1),
          (Month.OCTOBER, 27, 8, 59, 59),

          (Month.OCTOBER, 27, 10, 0, 1),
          (Month.OCTOBER, 27, 10, 59, 59),

          (Month.OCTOBER, 27, 12, 0, 1),        # 12pm-1pm PST, 3pm-4pm EST
          (Month.OCTOBER, 27, 12, 59, 59),

          (Month.OCTOBER, 27, 14, 0, 1),
          (Month.OCTOBER, 27, 14, 59, 59),

          (Month.OCTOBER, 27, 16, 0, 1),
          (Month.OCTOBER, 27, 16, 59, 59),

          (Month.OCTOBER, 27, 18, 0, 1),
          (Month.OCTOBER, 27, 18, 59, 59),

          (Month.OCTOBER, 27, 20, 0, 1),
          (Month.OCTOBER, 27, 20, 59, 59),

          (Month.OCTOBER, 27, 22, 0, 1),
          (Month.OCTOBER, 27, 22, 59, 59),
          
          (Month.OCTOBER, 28, 0, 0, 1),          # 12am-1am PST, 3am-4am EST
          (Month.OCTOBER, 28, 0, 59, 59),

          (Month.OCTOBER, 28, 2, 0, 1),
          (Month.OCTOBER, 28, 2, 59, 59),

          (Month.OCTOBER, 28, 4, 0, 1),
          (Month.OCTOBER, 28, 4, 59, 59),

          (Month.OCTOBER, 28, 6, 0, 1),
          (Month.OCTOBER, 28, 6, 59, 59),

          (Month.OCTOBER, 28, 8, 0, 1),
          (Month.OCTOBER, 28, 8, 59, 59),

          (Month.OCTOBER, 28, 10, 0, 1),
          (Month.OCTOBER, 28, 10, 59, 59),

          (Month.OCTOBER, 28, 12, 0, 1),        # 12pm-1pm PST, 3pm-4pm EST
          (Month.OCTOBER, 28, 12, 59, 59),

          (Month.OCTOBER, 28, 14, 0, 1),
          (Month.OCTOBER, 28, 14, 59, 59),

          (Month.OCTOBER, 28, 16, 0, 1),
          (Month.OCTOBER, 28, 16, 59, 59),

          (Month.OCTOBER, 28, 18, 0, 1),
          (Month.OCTOBER, 28, 18, 59, 59),

          (Month.OCTOBER, 28, 20, 0, 1),
          (Month.OCTOBER, 28, 20, 59, 59),

          (Month.OCTOBER, 28, 22, 0, 1),
          (Month.OCTOBER, 28, 22, 59, 59),       
        
          (Month.OCTOBER, 29, 0, 0, 1),          # 12am-1am PST, 3am-4am EST
          (Month.OCTOBER, 29, 0, 59, 59),

          (Month.OCTOBER, 29, 2, 0, 1),
          (Month.OCTOBER, 29, 2, 59, 59),

          (Month.OCTOBER, 29, 4, 0, 1),
          (Month.OCTOBER, 29, 4, 59, 59),

          (Month.OCTOBER, 29, 6, 0, 1),
          (Month.OCTOBER, 29, 6, 59, 59),

          (Month.OCTOBER, 29, 8, 0, 1),
          (Month.OCTOBER, 29, 8, 59, 59),

          (Month.OCTOBER, 29, 10, 0, 1),
          (Month.OCTOBER, 29, 10, 59, 59),

          (Month.OCTOBER, 29, 12, 0, 1),        # 12pm-1pm PST, 3pm-4pm EST
          (Month.OCTOBER, 29, 12, 59, 59),

          (Month.OCTOBER, 29, 14, 0, 1),
          (Month.OCTOBER, 29, 14, 59, 59),

          (Month.OCTOBER, 29, 16, 0, 1),
          (Month.OCTOBER, 29, 16, 59, 59),

          (Month.OCTOBER, 29, 18, 0, 1),
          (Month.OCTOBER, 29, 18, 59, 59),

          (Month.OCTOBER, 29, 20, 0, 1),
          (Month.OCTOBER, 29, 20, 59, 59),

          (Month.OCTOBER, 29, 22, 0, 1),
          (Month.OCTOBER, 29, 22, 59, 59),

          (Month.OCTOBER, 30, 0, 0, 1),         # 12am-1am PST, 3am-4am EST
          (Month.OCTOBER, 30, 0, 59, 59),

          (Month.OCTOBER, 30, 2, 0, 1),
          (Month.OCTOBER, 30, 2, 59, 59),

          (Month.OCTOBER, 30, 4, 0, 1),
          (Month.OCTOBER, 30, 4, 59, 59),

          (Month.OCTOBER, 30, 6, 0, 1),
          (Month.OCTOBER, 30, 6, 59, 59),

          (Month.OCTOBER, 30, 8, 0, 1),
          (Month.OCTOBER, 30, 8, 59, 59),

          (Month.OCTOBER, 30, 10, 0, 1),
          (Month.OCTOBER, 30, 10, 59, 59),

          (Month.OCTOBER, 30, 12, 0, 1),        # 12pm-1pm PST, 3pm-4pm EST
          (Month.OCTOBER, 30, 12, 59, 59),

          (Month.OCTOBER, 30, 14, 0, 1),
          (Month.OCTOBER, 30, 14, 59, 59),

          (Month.OCTOBER, 30, 16, 0, 1),
          (Month.OCTOBER, 30, 16, 59, 59),

          (Month.OCTOBER, 30, 18, 0, 1),
          (Month.OCTOBER, 30, 18, 59, 59),

          (Month.OCTOBER, 30, 20, 0, 1),
          (Month.OCTOBER, 30, 20, 59, 59),

          (Month.OCTOBER, 30, 22, 0, 1),
          (Month.OCTOBER, 30, 22, 59, 59),

          (Month.OCTOBER, 31, 0, 0, 1),         # 12am-1am PST, 3am-4am EST
          (Month.OCTOBER, 31, 0, 59, 59),

          (Month.OCTOBER, 31, 2, 0, 1),
          (Month.OCTOBER, 31, 2, 59, 59),

          (Month.OCTOBER, 31, 4, 0, 1),
          (Month.OCTOBER, 31, 4, 59, 59),

          (Month.OCTOBER, 31, 6, 0, 1),
          (Month.OCTOBER, 31, 6, 59, 59),

          (Month.OCTOBER, 31, 8, 0, 1),
          (Month.OCTOBER, 31, 8, 59, 59),

          (Month.OCTOBER, 31, 10, 0, 1),
          (Month.OCTOBER, 31, 10, 59, 59),

          (Month.OCTOBER, 31, 12, 0, 1),        # 12pm-1pm PST, 3pm-4pm EST
          (Month.OCTOBER, 31, 12, 59, 59),

          (Month.OCTOBER, 31, 14, 0, 1),
          (Month.OCTOBER, 31, 14, 59, 59),

          (Month.OCTOBER, 31, 16, 0, 1),
          (Month.OCTOBER, 31, 16, 59, 59),

          (Month.OCTOBER, 31, 18, 0, 1),
          (Month.OCTOBER, 31, 18, 59, 59),

          (Month.OCTOBER, 31, 20, 0, 1),
          (Month.OCTOBER, 31, 20, 59, 59),

          (Month.OCTOBER, 31, 22, 0, 1),
          (Month.OCTOBER, 31, 22, 59, 59),

          (Month.NOVEMBER, 1, 0, 0, 1),         # 12am-1am PST, 3am-4am EST
          (Month.NOVEMBER, 1, 0, 59, 59),

          (Month.NOVEMBER, 1, 2, 0, 1),
          (Month.NOVEMBER, 1, 2, 59, 59),

          (Month.NOVEMBER, 1, 4, 0, 1),
          (Month.NOVEMBER, 1, 4, 59, 59),

          (Month.NOVEMBER, 1, 6, 0, 1),
          (Month.NOVEMBER, 1, 6, 59, 59),

          (Month.NOVEMBER, 1, 8, 0, 1),
          (Month.NOVEMBER, 1, 8, 59, 59),

          (Month.NOVEMBER, 1, 10, 0, 1),
          (Month.NOVEMBER, 1, 10, 59, 59),

          (Month.NOVEMBER, 1, 12, 0, 1),        # 12pm-1pm PST, 3pm-4pm EST
          (Month.NOVEMBER, 1, 12, 59, 59),

          (Month.NOVEMBER, 1, 14, 0, 1),
          (Month.NOVEMBER, 1, 14, 59, 59),

          (Month.NOVEMBER, 1, 16, 0, 1),
          (Month.NOVEMBER, 1, 16, 59, 59),

          (Month.NOVEMBER, 1, 18, 0, 1),
          (Month.NOVEMBER, 1, 18, 59, 59),

          (Month.NOVEMBER, 1, 20, 0, 1),
          (Month.NOVEMBER, 1, 20, 59, 59),

          (Month.NOVEMBER, 1, 22, 0, 1),
          (Month.NOVEMBER, 1, 23, 59, 59),],
        displayOnCalendar = False,
        ),

        ToontownGlobals.APRIL_FOOLS_COSTUMES: HolidayInfo_Yearly(
        AprilFoolsManagerAI.AprilFoolsManagerAI,
        [(Month.MARCH, 31, 0, 0, 1),
          (Month.APRIL, 7, 23, 59, 59)],
        displayOnCalendar = True,
        ),

        ToontownGlobals.BLACK_CAT_DAY: HolidayInfo_Yearly(
        BlackCatHolidayMgrAI.BlackCatHolidayMgrAI,
        #[(Month.SEPTEMBER, 31, 0, 0, 1),
        #  (Month.NOVEMBER, 31, 23, 59, 59)]
        [(Month.OCTOBER, 31, 0, 0, 1),
          (Month.OCTOBER, 31, 23, 59, 59)],
        displayOnCalendar = True,
        ),

        # Winter Decorations - runs for fifteen days.
        # time1: 12:01am PST on December 19th to 11:59pm PST on January 2nd
        ToontownGlobals.WINTER_DECORATIONS: HolidayInfo_Yearly(
        None,
        [(Month.DECEMBER, 8, 0, 0, 1),
          (Month.JANUARY, 3, 23, 58, 00)],
        displayOnCalendar = True,
        ),

        ToontownGlobals.MORE_XP_HOLIDAY: HolidayInfo_Oncely(
        None,
        # Double XP Holiday, set in the future to be manually triggered
        [(2029, Month.JANUARY, 1,  0, 0, 1),
         (2029, Month.JANUARY, 1,  23, 59, 59)],
        displayOnCalendar = False,
        ),
        
        ToontownGlobals.HYDRANT_ZERO_HOLIDAY: HolidayInfo_Oncely(
        HydrantZeroHolidayAI.HydrantZeroHolidayAI,
        # Hydrant zero animating
        AdjustedHolidays[ToontownGlobals.HYDRANT_ZERO_HOLIDAY]['startAndEndPairs'],
        displayOnCalendar = False,
        phaseDates = AdjustedHolidays[ToontownGlobals.HYDRANT_ZERO_HOLIDAY]['phaseDates'],
        ),

        ToontownGlobals.MAILBOX_ZERO_HOLIDAY: HolidayInfo_Oncely(
        MailboxZeroHolidayAI.MailboxZeroHolidayAI,
        # Mailbox zero animating
        AdjustedHolidays[ToontownGlobals.MAILBOX_ZERO_HOLIDAY]['startAndEndPairs'],
        displayOnCalendar = False,
        phaseDates = AdjustedHolidays[ToontownGlobals.MAILBOX_ZERO_HOLIDAY]['phaseDates'],        
        ),           

        ToontownGlobals.TRASHCAN_ZERO_HOLIDAY: HolidayInfo_Oncely(
        TrashcanZeroHolidayAI.TrashcanZeroHolidayAI,
        # Trashcan zero animating
        AdjustedHolidays[ToontownGlobals.TRASHCAN_ZERO_HOLIDAY]['startAndEndPairs'],        
        displayOnCalendar = False,
        phaseDates = AdjustedHolidays[ToontownGlobals.TRASHCAN_ZERO_HOLIDAY]['phaseDates'],        
        ),           

        ToontownGlobals.SILLYMETER_HOLIDAY: HolidayInfo_Oncely(
        SillyMeterHolidayAI.SillyMeterHolidayAI,
        # Silly Meter animating
        AdjustedHolidays[ToontownGlobals.SILLYMETER_HOLIDAY]['startAndEndPairs'], 
        displayOnCalendar = False,
        phaseDates = AdjustedHolidays[ToontownGlobals.SILLYMETER_HOLIDAY]['phaseDates'],
        ), 
		
        ToontownGlobals.SILLY_SURGE_HOLIDAY: HolidayInfo_Oncely(
        None,
        # Silly Surge text appearing when cog gets damaged
        AdjustedHolidays[ToontownGlobals.SILLY_SURGE_HOLIDAY]['startAndEndPairs'], 
        displayOnCalendar = False,
        phaseDates = AdjustedHolidays[ToontownGlobals.SILLY_SURGE_HOLIDAY]['phaseDates'],        
        ),         
        
        ToontownGlobals.SILLY_CHATTER_ONE: HolidayInfo_Oncely(
        None,
        [(2010, Month.MAY, 14, 0, 0, 1),
          (2010, Month.MAY, 25, 23, 59, 59)],
        displayOnCalendar = False,
        ),          
        
        ToontownGlobals.SILLY_CHATTER_TWO: HolidayInfo_Oncely(
        None,
        [(2010, Month.MAY, 26, 0, 0, 1),
          (2010, Month.JUNE, 1, 23, 59, 59)],
        displayOnCalendar = False,
        ),     
        
        ToontownGlobals.SILLY_CHATTER_THREE: HolidayInfo_Oncely(
        None,
        [(2010, Month.JUNE, 2, 0, 0, 1),
          (2010, Month.JUNE, 17, 23, 59, 59)],
        displayOnCalendar = False,
        ),     
        
        ToontownGlobals.SILLY_CHATTER_FOUR: HolidayInfo_Oncely(
        None,
        [(2010, Month.JUNE, 18, 0, 0, 1),
          (2010, Month.JUNE, 27, 23, 59, 59)],
        displayOnCalendar = False,
        ),
        
        ToontownGlobals.SILLY_CHATTER_FIVE: HolidayInfo_Oncely(
        None,
        [(2010, Month.JUNE, 28, 0, 0, 1),
          (2010, Month.JULY, 13, 23, 59, 59)],
        displayOnCalendar = False,
        ),
        
        ToontownGlobals.SILLY_TEST : HolidayInfo_Oncely(
        HolidayRepeaterAI.HolidayRepeaterAI,
        [(2010, Month.APRIL, 2 , 0, 0, 1),
          (2020, Month.APRIL, 2, 0, 0, 1)],
        displayOnCalendar = False,
        testHolidays = { ToontownGlobals.SILLYMETER_HOLIDAY : [60, 90, 110, 150, 190, 200, 220, 240, 260, 290, 310, 320, 330, 340, 420, 610, 620], \
                                ToontownGlobals.SILLY_CHATTER_ONE : [60, 195] , \
                                ToontownGlobals.SILLY_CHATTER_TWO : [200, 235], ToontownGlobals.SILLY_CHATTER_THREE : [240, 325], \
                                ToontownGlobals.SILLY_CHATTER_FOUR : [330, 610], \
                                ToontownGlobals.HYDRANT_ZERO_HOLIDAY : [0, 20, 50, 100, 130, 160, 250, 325],  \
                                ToontownGlobals.MAILBOX_ZERO_HOLIDAY : [30, 80, 140, 180, 230, 270, 300, 325], \
                                ToontownGlobals.TRASHCAN_ZERO_HOLIDAY : [10, 40, 70, 120, 170, 210, 280, 325], \
                                ToontownGlobals.SILLY_SURGE_HOLIDAY : [60, 340],  \
                                ToontownGlobals.HYDRANTS_BUFF_BATTLES : [330, 350], \
                                ToontownGlobals.MAILBOXES_BUFF_BATTLES : [330, 420, ],
                                ToontownGlobals.TRASHCANS_BUFF_BATTLES : [330, 420, ],
                                ToontownGlobals.DOWN_SIZER_INVASION: [360, 369],
                                ToontownGlobals.MOVER_AND_SHAKER_INVASION: [370, 379],
                                ToontownGlobals.DOUBLETALKER_INVASION: [380, 389],
                                ToontownGlobals.YES_MAN_INVASION: [390, 399],
                                ToontownGlobals.PENNY_PINCHER_INVASION: [400, 409],
                                ToontownGlobals.TIGHTWAD_INVASION: [410, 419],
                                ToontownGlobals.TELEMARKETER_INVASION : [430, 439],
                                ToontownGlobals.HEADHUNTER_INVASION : [440, 449],
                                ToontownGlobals.SPINDOCTOR_INVASION : [450, 459],
                                ToontownGlobals.MONEYBAGS_INVASION : [460, 469],
                                ToontownGlobals.TWOFACES_INVASION : [470, 479],
                                ToontownGlobals.NAME_DROPPER_INVASION : [480, 489],
                                ToontownGlobals.MICROMANAGER_INVASION : [490, 499],
                                ToontownGlobals.NUMBER_CRUNCHER_INVASION : [500, 509],
                                ToontownGlobals.AMBULANCE_CHASER_INVASION : [510, 519],
                                ToontownGlobals.MINGLER_INVASION : [520, 529],
                                ToontownGlobals.LOANSHARK_INVASION : [530, 539],
                                ToontownGlobals.CORPORATE_RAIDER_INVASION : [540, 549],
                                ToontownGlobals.LEGAL_EAGLE_INVASION : [550, 559],
                                ToontownGlobals.MR_HOLLYWOOD_INVASION : [560, 569],
                                ToontownGlobals.ROBBER_BARON_INVASION : [570, 579],
                                ToontownGlobals.BIG_WIG_INVASION : [580, 589],
                                ToontownGlobals.BIG_CHEESE_INVASION : [590, 599],
                                 },
        ),

        ToontownGlobals.HYDRANTS_BUFF_BATTLES: HolidayInfo_Oncely(
        HydrantBuffHolidayAI.HydrantBuffHolidayAI,
        AdjustedHolidays[ToontownGlobals.HYDRANTS_BUFF_BATTLES]['startAndEndPairs'], 
        displayOnCalendar = False,
        phaseDates = AdjustedHolidays[ToontownGlobals.HYDRANTS_BUFF_BATTLES]['phaseDates'],        
        ),

        ToontownGlobals.MAILBOXES_BUFF_BATTLES: HolidayInfo_Oncely(
        MailboxBuffHolidayAI.MailboxBuffHolidayAI,
        AdjustedHolidays[ToontownGlobals.MAILBOXES_BUFF_BATTLES]['startAndEndPairs'], 
        displayOnCalendar = False,
        phaseDates = AdjustedHolidays[ToontownGlobals.MAILBOXES_BUFF_BATTLES]['phaseDates'],        
        ),

        ToontownGlobals.TRASHCANS_BUFF_BATTLES: HolidayInfo_Oncely(
        TrashcanBuffHolidayAI.TrashcanBuffHolidayAI,
        AdjustedHolidays[ToontownGlobals.TRASHCANS_BUFF_BATTLES]['startAndEndPairs'], 
        displayOnCalendar = False,
        phaseDates = AdjustedHolidays[ToontownGlobals.TRASHCANS_BUFF_BATTLES]['phaseDates'],        
        ),
    }
    
    if not simbase.config.GetBool('want-silly-test', False):
        del holidaysCommon[ToontownGlobals.SILLY_TEST]

    holidaysEnglish = {
        ToontownGlobals.JULY4_FIREWORKS: HolidayInfo_Yearly(
        FireworkManagerAI.FireworkManagerAI,
        # Fourth of July Fireworks - for 16 days
        # Time1: 12am PST on June 30th to 11:59pm PST on July 15th
        [(Month.JUNE, 30, 0, 0, 1),
          (Month.JULY, 15, 23, 59, 59)],
        displayOnCalendar = True,
        ),

        ToontownGlobals.TRICK_OR_TREAT: HolidayInfo_Yearly(
        TrickOrTreatMgrAI.TrickOrTreatMgrAI,
        [(Month.OCTOBER, 27, 0, 0, 1),
          (Month.NOVEMBER, 1, 23, 59, 59)],
        displayOnCalendar = True,
        ),
        
        ToontownGlobals.WINTER_CAROLING: HolidayInfo_Yearly(
        WinterCarolingMgrAI.WinterCarolingMgrAI,
        [(Month.DECEMBER, 22, 0, 0, 1),
          (Month.JANUARY, 1, 23, 59, 59)],
        displayOnCalendar = True,
        ),

        ToontownGlobals.RESISTANCE_EVENT: HolidayInfo_Yearly(
        ResistanceEventMgrAI.ResistanceEventMgrAI,
        # HACK! TODO: make this last indefinately
        [(Month.JANUARY, 1, 0, 0, 1),
          (Month.DECEMBER, 31, 23, 59, 59)],
        displayOnCalendar = False,
        ),

        ToontownGlobals.POLAR_PLACE_EVENT: HolidayInfo_Yearly(
        PolarPlaceEventMgrAI.PolarPlaceEventMgrAI,
        # HACK! TODO: make this last indefinately
        [(Month.JANUARY, 1, 0, 0, 1),
          (Month.DECEMBER, 31, 23, 59, 59)],
        displayOnCalendar = False,
        ),

        ToontownGlobals.ELECTION_PROMOTION: HolidayInfo_Oncely(
        None,
        # Toon Election phrases
        [(2007, Month.JANUARY, 1,  0, 0, 1),
         (2007, Month.JANUARY, 22,  23, 59, 59)],
        displayOnCalendar = True,
        ),

        ToontownGlobals.TROLLEY_WEEKEND : HolidayInfo_Oncely(
        TrolleyWeekendMgrAI.TrolleyWeekendMgrAI,
        [(2007, Month.APRIL, 14,  0, 0, 1),
         (2007, Month.APRIL, 15,  23, 59, 59)],
        displayOnCalendar = False,
        ),

        ToontownGlobals.BOSSCOG_INVASION: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        [(2007, Month.DECEMBER, 15, 0, 0, 1),
          (2007, Month.DECEMBER, 15, 0, 59, 59),
          (2007, Month.DECEMBER, 15, 2, 0, 1),
          (2007, Month.DECEMBER, 15, 2, 59, 59),
          (2007, Month.DECEMBER, 15, 4, 0, 1),
          (2007, Month.DECEMBER, 15, 4, 59, 59),
          (2007, Month.DECEMBER, 15, 6, 0, 1),
          (2007, Month.DECEMBER, 15, 6, 59, 59),
          (2007, Month.DECEMBER, 15, 8, 0, 1),
          (2007, Month.DECEMBER, 15, 8, 59, 59),
          (2007, Month.DECEMBER, 15, 10, 0, 1),
          (2007, Month.DECEMBER, 15, 10, 59, 59),
          (2007, Month.DECEMBER, 15, 12, 0, 1),
          (2007, Month.DECEMBER, 15, 12, 59, 59),
          (2007, Month.DECEMBER, 15, 14, 0, 1),
          (2007, Month.DECEMBER, 15, 14, 59, 59),
          (2007, Month.DECEMBER, 15, 16, 0, 1),
          (2007, Month.DECEMBER, 15, 16, 59, 59),
          (2007, Month.DECEMBER, 15, 18, 0, 1),
          (2007, Month.DECEMBER, 15, 18, 59, 59),
          (2007, Month.DECEMBER, 15, 20, 0, 1),
          (2007, Month.DECEMBER, 15, 20, 59, 59),
          (2007, Month.DECEMBER, 15, 22, 0, 1),
          (2007, Month.DECEMBER, 15, 22, 59, 59),

          (2007, Month.DECEMBER, 16, 0, 0, 1),
          (2007, Month.DECEMBER, 16, 0, 59, 59),
          (2007, Month.DECEMBER, 16, 2, 0, 1),
          (2007, Month.DECEMBER, 16, 2, 59, 59),
          (2007, Month.DECEMBER, 16, 4, 0, 1),
          (2007, Month.DECEMBER, 16, 4, 59, 59),
          (2007, Month.DECEMBER, 16, 6, 0, 1),
          (2007, Month.DECEMBER, 16, 6, 59, 59),
          (2007, Month.DECEMBER, 16, 8, 0, 1),
          (2007, Month.DECEMBER, 16, 8, 59, 59),
          (2007, Month.DECEMBER, 16, 10, 0, 1),
          (2007, Month.DECEMBER, 16, 10, 59, 59),
          (2007, Month.DECEMBER, 16, 12, 0, 1),
          (2007, Month.DECEMBER, 16, 12, 59, 59),
          (2007, Month.DECEMBER, 16, 14, 0, 1),
          (2007, Month.DECEMBER, 16, 14, 59, 59),
          (2007, Month.DECEMBER, 16, 16, 0, 1),
          (2007, Month.DECEMBER, 16, 16, 59, 59),
          (2007, Month.DECEMBER, 16, 18, 0, 1),
          (2007, Month.DECEMBER, 16, 18, 59, 59),
          (2007, Month.DECEMBER, 16, 20, 0, 1),
          (2007, Month.DECEMBER, 16, 20, 59, 59),
          (2007, Month.DECEMBER, 16, 22, 0, 1),
          (2007, Month.DECEMBER, 16, 22, 59, 59)],
        displayOnCalendar = False,
        ),

        ToontownGlobals.MARCH_INVASION: HolidayInfo_Yearly(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        [ (Month.MARCH, 14, 2, 0, 1),
          (Month.MARCH, 14, 4, 59, 59),
          (Month.MARCH, 14, 10, 0, 1),
          (Month.MARCH, 14, 12, 59, 59),
          (Month.MARCH, 14, 18, 0, 1),
          (Month.MARCH, 14, 20, 59, 59),

          (Month.MARCH, 15, 2, 0, 1),
          (Month.MARCH, 15, 4, 59, 59),
          (Month.MARCH, 15, 10, 0, 1),
          (Month.MARCH, 15, 12, 59, 59),
          (Month.MARCH, 15, 18, 0, 1),
          (Month.MARCH, 15, 20, 59, 59)],
        displayOnCalendar = True,
        ),

        ToontownGlobals.DECEMBER_INVASION: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        [ (2008, Month.DECEMBER, 27, 10, 0, 1),
          (2008, Month.DECEMBER, 27, 14, 59, 59),

          (2008, Month.DECEMBER, 27, 18, 0, 1),
          (2008, Month.DECEMBER, 27, 22, 59, 59),

          (2008, Month.DECEMBER, 28, 10, 0, 1),
          (2008, Month.DECEMBER, 28, 14, 59, 59),

          (2008, Month.DECEMBER, 28, 18, 0, 1),
          (2008, Month.DECEMBER, 28, 22, 59, 59)],
        displayOnCalendar = True,
        ),

        ToontownGlobals.SELLBOT_SURPRISE_1: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        [ (2009, Month.JANUARY, 10, 10, 0, 0),
          (2009, Month.JANUARY, 10, 15, 0, 0),
          ],
        displayOnCalendar = True,
        ),

        ToontownGlobals.SELLBOT_SURPRISE_2: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        AdjustedHolidays[ToontownGlobals.SELLBOT_SURPRISE_2]['startAndEndPairs'], 
        displayOnCalendar = True,
        ),
        
        ToontownGlobals.NAME_DROPPER_INVASION: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        AdjustedHolidays[ToontownGlobals.NAME_DROPPER_INVASION]['startAndEndPairs'], 
        displayOnCalendar = True,
        ),

        ToontownGlobals.SELLBOT_SURPRISE_3: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        [ (2009, Month.JANUARY, 11, 10, 0, 0),
          (2009, Month.JANUARY, 11, 15, 0, 0),
          ],
        displayOnCalendar = True,
        ),

        ToontownGlobals.SELLBOT_SURPRISE_4: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        AdjustedHolidays[ToontownGlobals.SELLBOT_SURPRISE_4]['startAndEndPairs'], 
        displayOnCalendar = True,
        ),
        
        ToontownGlobals.MOVER_AND_SHAKER_INVASION: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        AdjustedHolidays[ToontownGlobals.MOVER_AND_SHAKER_INVASION]['startAndEndPairs'], 
        displayOnCalendar = True,
        ),
        
        ToontownGlobals.MR_HOLLYWOOD_INVASION: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        AdjustedHolidays[ToontownGlobals.MR_HOLLYWOOD_INVASION]['startAndEndPairs'], 
        displayOnCalendar = True,
        ),
        
        ToontownGlobals.MINGLER_INVASION: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        AdjustedHolidays[ToontownGlobals.MINGLER_INVASION]['startAndEndPairs'], 
        displayOnCalendar = True,
        ),
        
        ToontownGlobals.TWOFACES_INVASION: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        AdjustedHolidays[ToontownGlobals.TWOFACES_INVASION]['startAndEndPairs'], 
        displayOnCalendar = True,
        ),
        
        ToontownGlobals.TELEMARKETER_INVASION: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        AdjustedHolidays[ToontownGlobals.TELEMARKETER_INVASION]['startAndEndPairs'], 
        displayOnCalendar = True,
        ),
        
        ToontownGlobals.HEADHUNTER_INVASION: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        AdjustedHolidays[ToontownGlobals.HEADHUNTER_INVASION]['startAndEndPairs'], 
        displayOnCalendar = True,
        ),

        ToontownGlobals.CASHBOT_CONUNDRUM_1: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        [ (2009, Month.JANUARY, 17, 10, 0, 0),
          (2009, Month.JANUARY, 17, 15, 0, 0),
          ],
        displayOnCalendar = True,
        ),

        ToontownGlobals.CASHBOT_CONUNDRUM_2: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        AdjustedHolidays[ToontownGlobals.CASHBOT_CONUNDRUM_2]['startAndEndPairs'], 
        displayOnCalendar = True,
        ),
        
        ToontownGlobals.PENNY_PINCHER_INVASION: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        AdjustedHolidays[ToontownGlobals.PENNY_PINCHER_INVASION]['startAndEndPairs'], 
        displayOnCalendar = True,
        ),

        ToontownGlobals.CASHBOT_CONUNDRUM_3: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        [ (2009, Month.JANUARY, 18, 10, 0, 0),
          (2009, Month.JANUARY, 18, 15, 0, 0),
          ],
        displayOnCalendar = True,
        ),

        ToontownGlobals.CASHBOT_CONUNDRUM_4: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        AdjustedHolidays[ToontownGlobals.CASHBOT_CONUNDRUM_4]['startAndEndPairs'], 
        displayOnCalendar = True,
        ),
        
        ToontownGlobals.NUMBER_CRUNCHER_INVASION: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        AdjustedHolidays[ToontownGlobals.NUMBER_CRUNCHER_INVASION]['startAndEndPairs'], 
        displayOnCalendar = True,
        ),
        
        ToontownGlobals.ROBBER_BARON_INVASION: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        AdjustedHolidays[ToontownGlobals.ROBBER_BARON_INVASION]['startAndEndPairs'], 
        displayOnCalendar = True,
        ),
        
        ToontownGlobals.LOANSHARK_INVASION : HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        AdjustedHolidays[ToontownGlobals.LOANSHARK_INVASION]['startAndEndPairs'], 
        displayOnCalendar = True,
        ),
        
        ToontownGlobals.MONEYBAGS_INVASION: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        AdjustedHolidays[ToontownGlobals.MONEYBAGS_INVASION]['startAndEndPairs'], 
        displayOnCalendar = True,
        ),
        
        ToontownGlobals.TIGHTWAD_INVASION: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        AdjustedHolidays[ToontownGlobals.TIGHTWAD_INVASION]['startAndEndPairs'], 
        displayOnCalendar = True,
        ),       

        ToontownGlobals.LAWBOT_GAMBIT_1: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        [ (2009, Month.JANUARY, 24, 10, 0, 0),
          (2009, Month.JANUARY, 24, 15, 0, 0),
          ],
        displayOnCalendar = True,
        ),

        ToontownGlobals.LAWBOT_GAMBIT_2: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        AdjustedHolidays[ToontownGlobals.LAWBOT_GAMBIT_2]['startAndEndPairs'], 
        displayOnCalendar = True,
        ),
        
        ToontownGlobals.DOUBLETALKER_INVASION: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        AdjustedHolidays[ToontownGlobals.DOUBLETALKER_INVASION]['startAndEndPairs'], 
        displayOnCalendar = True,
        ),

        ToontownGlobals.LAWBOT_GAMBIT_3: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        AdjustedHolidays[ToontownGlobals.LAWBOT_GAMBIT_3]['startAndEndPairs'],
        displayOnCalendar = True,
        ),
        
        ToontownGlobals.AMBULANCE_CHASER_INVASION: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        AdjustedHolidays[ToontownGlobals.AMBULANCE_CHASER_INVASION]['startAndEndPairs'],
        displayOnCalendar = True,
        ),

        ToontownGlobals.LAWBOT_GAMBIT_4: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        [ (2009, Month.JANUARY, 25, 18, 0, 0),
          (2009, Month.JANUARY, 25, 23, 0, 0),
          ],
        displayOnCalendar = True,
        ),
        
        ToontownGlobals.LEGAL_EAGLE_INVASION: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        AdjustedHolidays[ToontownGlobals.LEGAL_EAGLE_INVASION]['startAndEndPairs'],
        displayOnCalendar = True,
        ),
        
        ToontownGlobals.SPINDOCTOR_INVASION: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        AdjustedHolidays[ToontownGlobals.SPINDOCTOR_INVASION]['startAndEndPairs'], 
        displayOnCalendar = True,
        ),

        ToontownGlobals.TROUBLE_BOSSBOTS_1: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        [ (2009, Month.JANUARY, 31, 10, 0, 0),
          (2009, Month.JANUARY, 31, 15, 0, 0),
          ],
        displayOnCalendar = True,
        ),

        ToontownGlobals.TROUBLE_BOSSBOTS_2: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        [ (2009, Month.JANUARY, 31, 18, 0, 0),
          (2009, Month.JANUARY, 31, 23, 0, 0),
          ],
        displayOnCalendar = True,
        ),

        ToontownGlobals.TROUBLE_BOSSBOTS_3: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        AdjustedHolidays[ToontownGlobals.TROUBLE_BOSSBOTS_3]['startAndEndPairs'], 
        displayOnCalendar = True,
        ),
        
        ToontownGlobals.MICROMANAGER_INVASION: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        AdjustedHolidays[ToontownGlobals.MICROMANAGER_INVASION]['startAndEndPairs'], 
        displayOnCalendar = True,
        ),

        ToontownGlobals.TROUBLE_BOSSBOTS_4: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
          # Silly Meter animating
        AdjustedHolidays[ToontownGlobals.TROUBLE_BOSSBOTS_4]['startAndEndPairs'], 
        displayOnCalendar = True,
        ),
        
        ToontownGlobals.DOWN_SIZER_INVASION: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
          # Silly Meter animating
        AdjustedHolidays[ToontownGlobals.DOWN_SIZER_INVASION]['startAndEndPairs'], 
        displayOnCalendar = True,
        ),
        
        ToontownGlobals.CORPORATE_RAIDER_INVASION: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
          # Silly Meter animating
        AdjustedHolidays[ToontownGlobals.CORPORATE_RAIDER_INVASION]['startAndEndPairs'], 
        displayOnCalendar = True,
        ),
        
        ToontownGlobals.YES_MAN_INVASION: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
          # Silly Meter animating
        AdjustedHolidays[ToontownGlobals.YES_MAN_INVASION]['startAndEndPairs'], 
        displayOnCalendar = True,
        ),
        
        ToontownGlobals.BIG_WIG_INVASION: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
          # Silly Meter animating
        AdjustedHolidays[ToontownGlobals.BIG_WIG_INVASION]['startAndEndPairs'], 
        displayOnCalendar = True,
        ),
        
        ToontownGlobals.BIG_CHEESE_INVASION: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
          # Silly Meter animating
        AdjustedHolidays[ToontownGlobals.BIG_CHEESE_INVASION]['startAndEndPairs'], 
        displayOnCalendar = True,
        ),

        ToontownGlobals.JELLYBEAN_DAY: HolidayInfo_Yearly(
        None,
        [ (Month.APRIL, 22, 0, 0, 1),
          (Month.APRIL, 22, 23, 59, 59),
          ],
        displayOnCalendar = True,
        ),

        ToontownGlobals.COLD_CALLER_INVASION: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        [ (2009, Month.AUGUST, 21, 2, 0, 0),
          (2009, Month.AUGUST, 21, 5, 0, 0),

          (2009, Month.AUGUST, 21, 10, 0, 0),
          (2009, Month.AUGUST, 21, 13, 0, 0),

          (2009, Month.AUGUST, 21, 18, 0, 0),
          (2009, Month.AUGUST, 21, 21, 0, 0),          
          ],
        displayOnCalendar = True,
        ),

        ToontownGlobals.BEAN_COUNTER_INVASION: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        [ (2009, Month.AUGUST, 22, 2, 0, 0),
          (2009, Month.AUGUST, 22, 5, 0, 0),

          (2009, Month.AUGUST, 22, 10, 0, 0),
          (2009, Month.AUGUST, 22, 13, 0, 0),

          (2009, Month.AUGUST, 22, 18, 0, 0),
          (2009, Month.AUGUST, 22, 21, 0, 0),          
          ],
        displayOnCalendar = True,
        ),

        ToontownGlobals.DOUBLE_TALKER_INVASION: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        [ (2009, Month.AUGUST, 23, 2, 0, 0),
          (2009, Month.AUGUST, 23, 5, 0, 0),

          (2009, Month.AUGUST, 23, 10, 0, 0),
          (2009, Month.AUGUST, 23, 13, 0, 0),

          (2009, Month.AUGUST, 23, 18, 0, 0),
          (2009, Month.AUGUST, 23, 21, 0, 0),          
          ],
        displayOnCalendar = True,
        ),

        ToontownGlobals.DOWNSIZER_INVASION: HolidayInfo_Oncely(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        [ (2009, Month.AUGUST, 24, 2, 0, 0),
          (2009, Month.AUGUST, 24, 5, 0, 0),

          (2009, Month.AUGUST, 24, 10, 0, 0),
          (2009, Month.AUGUST, 24, 13, 0, 0),

          (2009, Month.AUGUST, 24, 18, 0, 0),
          (2009, Month.AUGUST, 24, 21, 0, 0),          
          ],
        displayOnCalendar = True,
        ),
        
        ToontownGlobals.VICTORY_PARTY_HOLIDAY: HolidayInfo_Oncely(
        None,
        [(2010, Month.JULY, 21, 0, 0, 1),
         (2010, Month.AUGUST, 17, 23, 59, 59)],
        displayOnCalendar = True,
        ),
    }


    holidaysJapanese = {
        ToontownGlobals.NEWYEARS_FIREWORKS: HolidayInfo_Yearly(
        FireworkManagerAI.FireworkManagerAI,
        [(Month.DECEMBER, 30, 6, 0, 0),
          (Month.JANUARY, 1, 5, 0, 0) ],
        displayOnCalendar = False,
        ),

        ToontownGlobals.JULY4_FIREWORKS: HolidayInfo_Yearly(
        FireworkManagerAI.FireworkManagerAI,
        # 7pm-9pm JPN
        [(Month.JULY, 23, 18, 0, 0),
          (Month.JULY, 23, 20, 30, 0),

          (Month.JULY, 25, 18, 0, 0),
          (Month.JULY, 25, 20, 30, 0),

          (Month.JULY, 30, 18, 0, 0),
          (Month.JULY, 30, 20, 30, 0),

          (Month.JULY, 31, 18, 0, 0),
          (Month.JULY, 31, 20, 30, 0),

          (Month.AUGUST, 4, 0o1, 0, 0),
          (Month.AUGUST, 4, 0o5, 30, 0),

          (Month.AUGUST, 5, 0o1, 0, 0),
          (Month.AUGUST, 5, 0o5, 30, 0),

          (Month.AUGUST, 6, 0o1, 0, 0),
          (Month.AUGUST, 6, 0o5, 30, 0),

          (Month.AUGUST, 7, 0o1, 0, 0),
          (Month.AUGUST, 7, 0o5, 30, 0),

          (Month.AUGUST, 8, 0o1, 0, 0),
          (Month.AUGUST, 8, 0o5, 30, 0),

          (Month.AUGUST, 9, 0o1, 0, 0),
          (Month.AUGUST, 9, 0o5, 30, 0),

          (Month.AUGUST, 10, 0o1, 0, 0),
          (Month.AUGUST, 10, 0o5, 30, 0),

          (Month.AUGUST, 11, 0o1, 0, 0),
          (Month.AUGUST, 11, 0o5, 30, 0)],
        displayOnCalendar = False,
        ),

        ToontownGlobals.WINTER_DECORATIONS: HolidayInfo_Yearly(
        None,
        [ (Month.NOVEMBER, 30, 6, 0, 0),
          (Month.JANUARY, 14, 5, 0, 0) ],
        displayOnCalendar = False,
        ),

        ToontownGlobals.HALLOWEEN: HolidayInfo_Yearly(
        HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI,
        [ (Month.OCTOBER, 30, 17, 0, 0),        # 10am-3pm PST, 1pm-6pm EST
          (Month.OCTOBER, 30, 22, 0, 0),

          (Month.OCTOBER, 31, 1, 0, 0),        # 6pm-11pm PST, 9pm-2am EST
          (Month.OCTOBER, 31, 6, 0, 0) ],
        displayOnCalendar = False,
        ),

        ToontownGlobals.BLACK_CAT_DAY: HolidayInfo_Yearly(
        BlackCatHolidayMgrAI.BlackCatHolidayMgrAI,
        [ (Month.OCTOBER, 30, 7, 0, 1),
          (Month.OCTOBER, 31, 6, 59, 59) ],
        displayOnCalendar = False,
        ),

        #ToontownGlobals.TRICK_OR_TREAT: HolidayInfo_Yearly(
        #TrickOrTreatMgrAI.TrickOrTreatMgrAI,
        #[ (Month.OCTOBER, 27, 7, 0, 1),
        #  (Month.OCTOBER, 30, 14, 59, 59) ]
        #),

        ToontownGlobals.FISH_BINGO_NIGHT: HolidayInfo_Weekly(
        BingoNightHolidayAI.BingoNightHolidayAI,
        # Fish Bingo Night - runs once a week
        # Time1: 3pm PST to 9pm PST on Wednesdays
        [ (Day.TUESDAY, 20, 0, 0),
          (Day.WEDNESDAY, 5, 0, 0),

          (Day.SATURDAY, 20, 0, 0),
          (Day.SUNDAY, 5, 0, 0) ],
        displayOnCalendar = False,
        ),

        ToontownGlobals.KART_RECORD_DAILY_RESET: HolidayInfo_Daily(
            RaceManagerAI.KartRecordDailyResetter,
            [ (7, 24, 1),
              (7, 24, 30),
              ],
            displayOnCalendar = False,
            ),
        ToontownGlobals.KART_RECORD_WEEKLY_RESET: HolidayInfo_Weekly(
            RaceManagerAI.KartRecordWeeklyResetter,
            [ (Day.SUNDAY, 7, 25, 1),
              (Day.SUNDAY, 7, 25, 30),
             ],
            displayOnCalendar = False,
            ),
        ToontownGlobals.CIRCUIT_RACING: HolidayInfo_Weekly(
            RaceManagerAI.CircuitRaceHolidayMgr,
            [ (Day.MONDAY, 7, 0, 1),
              (Day.TUESDAY, 6, 59, 59),

              (Day.FRIDAY, 7, 0, 1),
              (Day.SATURDAY, 6, 59, 59),
             ],
            displayOnCalendar = False,
            ),
        ToontownGlobals.TROLLEY_HOLIDAY: HolidayInfo_Weekly(
            TrolleyHolidayMgrAI.TrolleyHolidayMgrAI,
            [ (Day.SATURDAY, 19, 0, 0),
              (Day.SUNDAY, 6, 59, 59),
             ],
            displayOnCalendar = False,
            )
    }

    holidaysGerman = {
        ToontownGlobals.JULY4_FIREWORKS: HolidayInfo_Yearly(
        FireworkManagerAI.FireworkManagerAI,
        [(Month.OCTOBER, 3, 0, 0, 0),
        # Stop them in the middle of the final hour so we do not interrupt a show in the middle
          (Month.OCTOBER, 4, 0, 30, 0)],
        displayOnCalendar = False,
        ),

        ToontownGlobals.WINTER_DECORATIONS: HolidayInfo_Yearly(
        None, # No class defined, we just want the news manager to be called
        # 4pm December 1st - Midnight December 29th
        [(Month.DECEMBER, 1, 0, 0, 0),
          (Month.DECEMBER, 30, 0, 0, 0)],
        displayOnCalendar = False,
        )
    }

    holidaysPortuguese = {

    }

    holidaysFrench = {
        ToontownGlobals.JULY4_FIREWORKS: HolidayInfo_Yearly(
        FireworkManagerAI.FireworkManagerAI,
        # Bastille Day
        [(Month.JULY, 14, 0, 0, 0),
        # Stop them in the middle of the final hour so we do not interrupt a show in the middle
          (Month.JULY, 15, 0, 30, 0)],
        displayOnCalendar = False,
        ),

        ToontownGlobals.WINTER_DECORATIONS: HolidayInfo_Yearly(
        None, # No class defined, we just want the news manager to be called
        # 4pm December 1st - Midnight December 29th
        [(Month.DECEMBER, 1, 0, 0, 0),
          (Month.DECEMBER, 30, 0, 0, 0)],
        displayOnCalendar = False,
        )
    }

    language = simbase.config.GetString('language', 'english')
    if language == 'english':
        holidaysCommon.update(holidaysEnglish)
    elif language == 'japanese':
        holidaysCommon.update(holidaysJapanese)
    elif language == 'german':
        holidaysCommon.update(holidaysGerman)
    elif language == 'french':
        holidaysCommon.update(holidaysFrench)
    else:
        holidaysCommon.update(holidaysEnglish)
    holidays = holidaysCommon

    if not language in ['japanese', 'german', 'portuguese', 'french'] :
        if simbase.wantBingo:
            holidays[ToontownGlobals.FISH_BINGO_NIGHT] = HolidayInfo_Weekly(
                BingoNightHolidayAI.BingoNightHolidayAI,
                # Fish Bingo Night - runs once a week
                # Time: 12:00:01 am PST to 11:59:59 pm PST on Wednesdays
                [(Day.WEDNESDAY, 0, 0, 1),
                  (Day.WEDNESDAY, 23, 59, 59),
                  ],
                displayOnCalendar = True,
                )

        if simbase.wantKarts:
            holidays[ToontownGlobals.KART_RECORD_DAILY_RESET] = HolidayInfo_Daily(
                RaceManagerAI.KartRecordDailyResetter,
                [(0, 24, 1),
                  (0, 24, 30),
                  ],
                displayOnCalendar = False,
                )
            holidays[ToontownGlobals.KART_RECORD_WEEKLY_RESET] = HolidayInfo_Weekly(
                RaceManagerAI.KartRecordWeeklyResetter,
                [(Day.MONDAY, 0, 25, 1),
                  (Day.MONDAY, 0, 25, 30),
                 ],
                displayOnCalendar = False,
                )
            holidays[ToontownGlobals.CIRCUIT_RACING] = HolidayInfo_Weekly(
                RaceManagerAI.CircuitRaceHolidayMgr,
                [(Day.MONDAY, 0, 0, 1),
                  (Day.MONDAY, 23, 59, 59),
                  ],
                displayOnCalendar = True,
                )
            holidays[ToontownGlobals.CIRCUIT_RACING_EVENT] = HolidayInfo_Yearly(
                RaceManagerAI.CircuitRaceHolidayMgr,
                [(Month.MAY, 21, 0, 0, 1),
                  (Month.MAY, 24, 23, 59, 59),
                  ],
                displayOnCalendar = True,
                )

        if simbase.config.GetBool('want-trolley-holiday', 1):
            holidays[ToontownGlobals.TROLLEY_HOLIDAY] = HolidayInfo_Weekly(
                TrolleyHolidayMgrAI.TrolleyHolidayMgrAI,
                [(Day.THURSDAY, 0, 0, 1),
                  (Day.THURSDAY, 23, 59, 59),
                  ],
                displayOnCalendar = True,
                )

        if simbase.config.GetBool('want-trolley-holiday-everyday', 0):
            holidays[ToontownGlobals.TROLLEY_HOLIDAY] = HolidayInfo_Daily(
                TrolleyHolidayMgrAI.TrolleyHolidayMgrAI,
                [(12, 0, 1),
                  (17, 59, 59),
                  ],
                displayOnCalendar = False,
                )

        # Silly Saturday is a compound holiday - it is composed of alternating 2-hour blocks
        # of Fish Bingo, Circuit Racing, and Trolley Holiday for 24 hours

        if simbase.config.GetBool('want-silly-saturday', 1):
            holidays[ToontownGlobals.SILLY_SATURDAY_BINGO] = HolidayInfo_Weekly(
                BingoNightHolidayAI.BingoNightHolidayAI,
                [(Day.SATURDAY, 0, 0, 1),
                 (Day.SATURDAY, 1, 59, 59),
    
                 (Day.SATURDAY, 6, 0, 0),
                 (Day.SATURDAY, 7, 59, 59),

                 (Day.SATURDAY, 12, 0, 0),
                 (Day.SATURDAY, 13, 59, 59),

                 (Day.SATURDAY, 18, 0, 0),
                 (Day.SATURDAY, 19, 59, 59),
                 ],
                displayOnCalendar = True,
                )
            holidays[ToontownGlobals.SILLY_SATURDAY_CIRCUIT] = HolidayInfo_Weekly(
                RaceManagerAI.CircuitRaceHolidayMgr,
                [(Day.SATURDAY, 2, 0, 0),
                 (Day.SATURDAY, 3, 59, 59),

                 (Day.SATURDAY, 8, 0, 0),
                 (Day.SATURDAY, 9, 59, 59),

                 (Day.SATURDAY, 14, 0, 0),
                 (Day.SATURDAY, 15, 59, 59),
    
                 (Day.SATURDAY, 20, 0, 0),
                 (Day.SATURDAY, 21, 59, 59),
                 ],
                displayOnCalendar = False,
                )
            holidays[ToontownGlobals.SILLY_SATURDAY_TROLLEY] = HolidayInfo_Weekly(
                TrolleyHolidayMgrAI.TrolleyHolidayMgrAI,
                [(Day.SATURDAY, 4, 0, 0),
                 (Day.SATURDAY, 5, 59, 59),

                 (Day.SATURDAY, 10, 0, 0),
                 (Day.SATURDAY, 11, 59, 59),

                 (Day.SATURDAY, 16, 0, 0),
                 (Day.SATURDAY, 17, 59, 59),

                 (Day.SATURDAY, 22, 0, 0),
                 (Day.SATURDAY, 23, 59, 59),
                 ],
                displayOnCalendar = False,
                )

        holidays[ToontownGlobals.ROAMING_TRIALER_WEEKEND] = HolidayInfo_Oncely(
            RoamingTrialerWeekendMgrAI.RoamingTrialerWeekendMgrAI,
            [(2007,Month.DECEMBER, 3, 0, 0, 1),
             (2007,Month.DECEMBER, 9, 23, 59, 59),
             ],
            displayOnCalendar = False,
            )

    def __init__(self, air):
        self.air = air
        # Dictionary of holidays in progress
        # Maps holidayId: holidayObj
        self.currentHolidays = {}
        self.createHolidays()
        self.parseCalendarHolidays()

    def createHolidays(self):
        currentTime = time.time()
        localTime = time.localtime()
        date = (localTime[0],  # Current Year
                 localTime[1],  # Current Month
                 localTime[2],  # Current Day
                 localTime[6]) # Current WDay
        for holidayId, holidayInfo in list(self.holidays.items()):
            startTime = holidayInfo.getStartTime(date)
            endTime = holidayInfo.getEndTime(date)

            self.notify.debug("holidayId = %s" % holidayId)
            self.notify.debug("startTime = %s" % startTime)
            self.notify.debug("endTime = %s" % endTime)

            try:
                # See if we need to wrap the endTime around to next year
                # For instance, a holiday that starts in December and ends
                # in January would use this
                if endTime < startTime:
                    end = time.localtime(endTime)
                    start = time.localtime(startTime)

                    if end[2] == start[2]:
                        raise ValueError("createEvents: Invalid Start/End Tuple combination in holiday %s" %(holidayId))

                    newDate = holidayInfo.adjustDate(date)
                    endTime = holidayInfo.getEndTime(newDate)
                    self.notify.debug("wrapped: endTime = %s" % endTime)

                # Has the holiday not come yet?
                if currentTime < startTime:
                    self.waitForHolidayStart(holidayId, startTime)
                # Or, are we in the holiday now?
                elif (currentTime >= startTime) and (currentTime < endTime):
                    self.startHoliday(holidayId)
                # If the holiday already passed this year,
                # wait for next years holiday
                elif (currentTime >= startTime) and (currentTime >= endTime):
                    sTime = holidayInfo.getNextHolidayTime(currentTime)

                    self.notify.debug("next: sTime = %s" % sTime)
                    # make sure it is not a one-time only event
                    if sTime != None:
                        if (currentTime >= sTime):
                            self.startHoliday(holidayId)
                        else:
                            self.waitForHolidayStart(holidayId, sTime)
                    else:
                        self.notify.info("One time holiday %s has passed" % holidayId)

            except ValueError as error:
                self.notify.warning(str(error))

    def waitForHolidayStart(self, holidayId, startTime):
        currentTime = time.time()
        waitTime = startTime - currentTime
        taskName = "waitHoliday-start-" + str(holidayId)
        task = taskMgr.doMethodLater(waitTime, self.startHolidayDoLater, taskName)
        task.holidayId = holidayId
        self.notify.info("Waiting until %s (- %s = %s) for holiday %s start" %
                          (time.ctime(startTime), time.ctime(currentTime), waitTime, holidayId))

    def waitForHolidayEnd(self, holidayId, endTime):
        self.notify.info("Waiting until %s for holiday %s end" %
                          (time.ctime(endTime), holidayId))
        waitTime = endTime - time.time()
        taskName = "waitHoliday-end-" + str(holidayId)
        task = taskMgr.doMethodLater(waitTime, self.endHolidayDoLater, taskName)
        task.holidayId = holidayId

    def startHolidayDoLater(self, task):
        self.startHoliday(task.holidayId)
        return Task.done
        
    def nullifyDates(self, dates):
        """This is a hacky way to get holidays not to intefere with the repeater
            Needs to be changed by 2015"""
        newDateTimes = []
        for item in dates:
            if isinstance(item, datetime.datetime):
                year = item.year+15
                if year>2030:
                        year = 2030
                newDateTimes.append(datetime.datetime(year, item.month, item.day, item.hour, item.second))
            else:
                # These are start and end tuples
                newDates = []
                for i in item:
                    year = i[0]+15
                    if year>2030:
                        year = 2030
                    newDates.append((year, i[1], i[2], i[3], i[4], i[5]))
                return [(newDates[0], newDates[1])]
        return newDateTimes

    def startHoliday(self, holidayId, testMode = 0):
        self.notify.info("startHoliday: %s" % holidayId)
        self.air.writeServerEvent('holiday', holidayId, 'start')
        # Create the holiday object
        holidayInfo = self.holidays[holidayId]
        holidayClass = holidayInfo.getClass()
        if holidayClass:
            if holidayInfo.hasPhaseDates():
                if testMode == 0:
                    holidayObj = holidayClass(self.air, holidayId,
                                          holidayInfo.tupleList,
                                          holidayInfo.getPhaseDates())        
                else:
                    startAndEndDates = self.nullifyDates(holidayInfo.tupleList)
                    phaseDates = self.nullifyDates(holidayInfo.getPhaseDates())
                    holidayObj = holidayClass(self.air, holidayId,
                                          startAndEndDates,
                                          phaseDates) 
            elif hasattr(holidayInfo, 'isTestHoliday') and holidayInfo.isTestHoliday():
                testHolidays = holidayInfo.getTestHolidays()
                holidayObj = holidayClass(self.air, holidayId, holidayInfo.tupleList, testHolidays)
            else:
                holidayObj = holidayClass(self.air, holidayId)
            try:
                # Start the holiday
                holidayObj.start()
            except SingletonError as error:
                self.notify.warning("startHoliday: " + str(error))
                del holidayObj
                return
            # Store the current holiday for later reference
            self.currentHolidays[holidayId] = holidayObj
        else:
            # Just store None, at least it will still indicate
            # that a holiday was started
            self.currentHolidays[holidayId] = None

        # Update the news manager, which in turn updates all the clients
        self.updateNewsManager(list(self.currentHolidays.keys()))

        # Spawn a do later for the end of the holiday
        currentTime = time.time()
        localTime = time.localtime()
        date = (localTime[0],  # Current Year
                 localTime[1],  # Current Month
                 localTime[2],  # Current Day
                 localTime[6]) # Current WDay

        endTime = holidayInfo.getEndTime(date)
        # Handle the case that the start and end times straddle the new year
        if endTime < currentTime:
            # Go to next year/month/week
            date = holidayInfo.adjustDate(date)
            endTime = holidayInfo.getEndTime(date)
        self.waitForHolidayEnd(holidayId, endTime)

    def forcePhase(self, holidayId, newPhase):
        """Force a phased holidy to go to a new phase. Returns True if succesful"""
        result = False
        holidayObj = self.currentHolidays.get(holidayId)
        if holidayObj:
            if hasattr(holidayObj, 'forcePhase'):
                result = holidayObj.forcePhase(newPhase)
            else:
                self.notify.warning("%s does not have forcePhase" % holidayObj)
        return result

    def endHolidayDoLater(self, task):
        self.endHoliday(task.holidayId)
        return Task.done

    def endHoliday(self, holidayId, stopForever = False):
        self.notify.info("endHoliday: %s" % holidayId)
        self.air.writeServerEvent('holiday', holidayId, 'end')
        holidayInfo = self.holidays[holidayId]

        if holidayId in self.currentHolidays:
            # Note - if the holiday does not define a class,
            # the None object will be stored here
            holidayObj = self.currentHolidays[holidayId]
            if hasattr(holidayObj, 'goingToStop'):
                holidayObj.goingToStop(stopForever)
                return
            else:
                if holidayObj:
                    holidayObj.stop()
                del self.currentHolidays[holidayId]
        else:
            self.notify.warning("Tried to stop a holiday that was not started")

        # Update the news manager, which in turn updates all the clients
        # Send the negative of the holiday ID signifying the end of the holiday
        self.updateNewsManager(list(self.currentHolidays.keys()))

        # Start the same holiday for the next time
        currentTime = time.time()
        startTime = holidayInfo.getNextHolidayTime(currentTime)

        self.notify.debug("currentTime = %s" % currentTime)
        self.notify.debug("startTime = %s" % startTime)

        if isinstance (holidayInfo, HolidayInfo_Daily):
            localTime = time.localtime()
            date = (localTime[0],  # Current Year
                     localTime[1],  # Current Month
                     localTime[2],  # Current Day
                     localTime[6]) # Current WDay
            startTimeForToday = holidayInfo.getStartTime(date)
            endTimeForToday = holidayInfo.getEndTime(date)
            if (startTimeForToday < currentTime) and (currentTime < endTimeForToday):
                #the task manager can sometimes end the task some seconds before we expected it
                #avoid the case where we start it again for a few seconds then end it
                oldStartTime = startTime
                startTime = holidayInfo.getNextHolidayTime(endTimeForToday)
                self.notify.debug("oldStart = %s newStart=%s" %(time.ctime(oldStartTime), time.ctime(startTime)))

        # if we are stopping the holiday prematurely, kill the task that waits for it to end
        taskName = "waitHoliday-end-" + str(holidayId)
        taskMgr.remove(taskName)

        # make sure it is not a one-time only event
        if startTime != None:
            # Handle the case that the start and end times straddle the new year
            if startTime < currentTime:
                # Go to next year
                if not stopForever:
                    self.startHoliday(holidayId)
            else:
                if not stopForever:
                    self.waitForHolidayStart(holidayId, startTime)


                    
    #######################################################################
    # This function is required for those holidays that required some
    # time for cleanup.
    #######################################################################

    def delayedEnd(self, holidayId, stopForever = False):
        self.notify.info("delayedEnd: %s" % holidayId)
        holidayInfo = self.holidays[holidayId]

        if holidayId in self.currentHolidays:
            # Note - if the holiday does not define a class,
            # the None object will be stored here
            holidayObj = self.currentHolidays[holidayId]
            if holidayObj:
                holidayObj.stop()
            del self.currentHolidays[holidayId]
        else:
            self.notify.warning("Tried to stop a holiday that was not started")

        # Update the news manager, which in turn updates all the clients
        # Send the negative of the holiday ID signifying the end of the holiday
        self.updateNewsManager(list(self.currentHolidays.keys()))

        # Start the same holiday for the next time
        currentTime = time.time()
        startTime = holidayInfo.getNextHolidayTime(currentTime)

        self.notify.debug("currentTime = %s" % currentTime)
        self.notify.debug("startTime = %s" % startTime)

        if isinstance (holidayInfo, HolidayInfo_Daily):
            localTime = time.localtime()
            date = (localTime[0],  # Current Year
                     localTime[1],  # Current Month
                     localTime[2],  # Current Day
                     localTime[6]) # Current WDay
            startTimeForToday = holidayInfo.getStartTime(date)
            endTimeForToday = holidayInfo.getEndTime(date)
            if (startTimeForToday < currentTime) and (currentTime < endTimeForToday):
                #the task manager can sometimes end the task some seconds before we expected it
                #avoid the case where we start it again for a few seconds then end it
                oldStartTime = startTime
                startTime = holidayInfo.getNextHolidayTime(endTimeForToday)
                self.notify.debug("oldStart = %s newStart=%s" %(time.ctime(oldStartTime), time.ctime(startTime)))

        # make sure it is not a one-time only event
        if startTime != None:
            # Handle the case that the start and end times straddle the new year
            if startTime < currentTime:
                # Go to next year
                if not stopForever:
                    self.startHoliday(holidayId)
            else:
                if not stopForever:
                    self.waitForHolidayStart(holidayId, startTime)

    def updateNewsManager(self, holidayIdList):
        self.air.newsManager.d_setHolidayIdList(holidayIdList)

    def isMoreXpHolidayRunning(self):
        """Return True if the double XP holiday is running."""
        keysList = list(self.currentHolidays.keys())
        result = False
        if ToontownGlobals.MORE_XP_HOLIDAY in keysList:
            result = True
        return result

    def isHolidayRunning(self, holidayId):
        """Return true if the indicated holidayId is running."""
        keysList = list(self.currentHolidays.keys())
        result = False
        if holidayId in keysList:
            result = True
        return result

    def getCurPhase(self, holidayId):
        """Return the current phase of the holiday, may return -1 if it doesn't know about phases."""
        result = -1
        if holidayId in  self.currentHolidays:
            holidayObj = self.currentHolidays[holidayId]
            if holidayObj and hasattr(holidayObj,"getCurPhase"):
                result = holidayObj.getCurPhase()
        return result    

    def parseCalendarHolidays(self):
        """Tell the client of the toontown holidays displayed in the calendar."""
        for key in self.holidays:
            holidayInfo = self.holidays[key]
            if holidayInfo.displayOnCalendar:
                if isinstance (holidayInfo, HolidayInfo_Weekly):
                    self.air.newsManager.addWeeklyCalendarHoliday(key, holidayInfo.tupleList[0][0][0])
                elif isinstance (holidayInfo, HolidayInfo_Yearly):
                    # we can have multiple start times and end times, just pick the bookends
                    firstStartTime = holidayInfo.tupleList[0][0]
                    lastEndTime = holidayInfo.tupleList[-1][-1]
                    self.air.newsManager.addYearlyCalendarHoliday(key, firstStartTime, lastEndTime)
                elif isinstance (holidayInfo, HolidayInfo_Oncely):
                    if key in OncelyMultipleStartHolidays:
                        startAndEndList = []
                        for times in holidayInfo.tupleList:
                            startAndEndList.append( (times[0], times[1]))
                        self.air.newsManager.addMultipleStartHoliday(key, startAndEndList)
                    else:
                        # we can have multiple start times and end times, just pick the bookends
                        firstStartTime = holidayInfo.tupleList[0][0]
                        lastEndTime = holidayInfo.tupleList[-1][-1]
                        self.air.newsManager.addOncelyCalendarHoliday(key, firstStartTime, lastEndTime)
                elif isinstance (holidayInfo, HolidayInfo_Relatively):
                    # we can have multiple start times and end times, just pick the bookends
                    firstStartTime = holidayInfo.tupleList[0][0]
                    lastEndTime = holidayInfo.tupleList[-1][-1]
                    self.air.newsManager.addRelativelyCalendarHoliday(key, firstStartTime, lastEndTime)

        self.air.newsManager.sendWeeklyCalendarHolidays()
        self.air.newsManager.sendYearlyCalendarHolidays()
        self.air.newsManager.sendOncelyCalendarHolidays()
        self.air.newsManager.sendMultipleStartHolidays()
