from panda3d.core import *
ELEVATOR_NORMAL = 0
ELEVATOR_VP = 1
ELEVATOR_MINT = 2
ELEVATOR_CFO = 3
ELEVATOR_CJ = 4
ELEVATOR_OFFICE = 5
ELEVATOR_STAGE = 6
ELEVATOR_BB = 7
ELEVATOR_COUNTRY_CLUB = 8
REJECT_NOREASON = 0
REJECT_SHUFFLE = 1
REJECT_MINLAFF = 2
REJECT_NOSEAT = 3
REJECT_PROMOTION = 4
REJECT_BLOCKED_ROOM = 5
REJECT_NOT_YET_AVAILABLE = 6
REJECT_BOARDINGPARTY = 7
REJECT_NOTPAID = 8
MAX_GROUP_BOARDING_TIME = 6.0
if __dev__:
    try:
        config = simbase.config
    except:
        config = base.config

    elevatorCountdown = config.GetFloat('elevator-countdown', -1)
    if elevatorCountdown != -1:
        bboard.post('elevatorCountdown', elevatorCountdown)
ElevatorData = {ELEVATOR_NORMAL: {'openTime': 2.0,
                   'closeTime': 2.0,
                   'width': 3.5,
                   'countdown': bboard.get('elevatorCountdown', 15.0),
                   'sfxVolume': 1.0,
                   'collRadius': 5},
 ELEVATOR_VP: {'openTime': 4.0,
               'closeTime': 4.0,
               'width': 11.5,
               'countdown': bboard.get('elevatorCountdown', 30.0),
               'sfxVolume': 0.7,
               'collRadius': 7.5},
 ELEVATOR_MINT: {'openTime': 2.0,
                 'closeTime': 2.0,
                 'width': 5.875,
                 'countdown': bboard.get('elevatorCountdown', 15.0),
                 'sfxVolume': 1.0,
                 'collRadius': 5},
 ELEVATOR_OFFICE: {'openTime': 2.0,
                   'closeTime': 2.0,
                   'width': 5.875,
                   'countdown': bboard.get('elevatorCountdown', 15.0),
                   'sfxVolume': 1.0,
                   'collRadius': 5},
 ELEVATOR_CFO: {'openTime': 3.0,
                'closeTime': 3.0,
                'width': 8.166,
                'countdown': bboard.get('elevatorCountdown', 30.0),
                'sfxVolume': 0.7,
                'collRadius': 7.5},
 ELEVATOR_CJ: {'openTime': 4.0,
               'closeTime': 4.0,
               'width': 15.8,
               'countdown': bboard.get('elevatorCountdown', 30.0),
               'sfxVolume': 0.7,
               'collRadius': 7.5},
 ELEVATOR_STAGE: {'openTime': 4.0,
                  'closeTime': 4.0,
                  'width': 6.5,
                  'countdown': bboard.get('elevatorCountdown', 42.0),
                  'sfxVolume': 1.0,
                  'collRadius': 9.5},
 ELEVATOR_BB: {'openTime': 4.0,
               'closeTime': 4.0,
               'width': 6.3,
               'countdown': bboard.get('elevatorCountdown', 30.0),
               'sfxVolume': 0.7,
               'collRadius': 7.5},
 ELEVATOR_COUNTRY_CLUB: {'openTime': 2.0,
                         'closeTime': 2.0,
                         'width': 5.875,
                         'countdown': bboard.get('elevatorCountdown', 15.0),
                         'sfxVolume': 1.0,
                         'collRadius': 4}}
TOON_BOARD_ELEVATOR_TIME = 1.0
TOON_EXIT_ELEVATOR_TIME = 1.0
TOON_VICTORY_EXIT_TIME = 1.0
SUIT_HOLD_ELEVATOR_TIME = 1.0
SUIT_LEAVE_ELEVATOR_TIME = 2.0
INTERIOR_ELEVATOR_COUNTDOWN_TIME = 90
LIGHT_OFF_COLOR = Vec4(0.5, 0.5, 0.5, 1.0)
LIGHT_ON_COLOR = Vec4(1.0, 1.0, 1.0, 1.0)
ElevatorPoints = [[-1.5, 5, 0.1],
 [1.5, 5, 0.1],
 [-2.5, 3, 0.1],
 [2.5, 3, 0.1],
 [-3.5, 5, 0.1],
 [3.5, 5, 0.1],
 [-4, 3, 0.1],
 [4, 3, 0.1]]
JumpOutOffsets = [[-1.5, -5, -0],
 [1.5, -5, -0],
 [-2.5, -7, -0],
 [2.5, -7, -0],
 [-3.5, -5, -0],
 [3.5, -5, -0],
 [-4, -7, -0],
 [4, -7, -0]]
BigElevatorPoints = [[-2.5, 9, 0.1],
 [2.5, 9, 0.1],
 [-8.0, 9, 0.1],
 [8.0, 9, 0.1],
 [-2.5, 4, 0.1],
 [2.5, 4, 0.1],
 [-8.0, 4, 0.1],
 [8.0, 4, 0.1]]
BossbotElevatorPoints = [[-2.5, 7.5, 0.1],
 [2.5, 7.5, 0.1],
 [-5.5, 7.5, 0.1],
 [5.5, 7.5, 0.1],
 [-2.5, 3.5, 0.1],
 [2.5, 3.5, 0.1],
 [-5.5, 3.5, 0.1],
 [5.5, 3.5, 0.1]]
ElevatorOutPoints = [[-4.6, -5.2, 0.1],
 [4.6, -5.2, 0.1],
 [-1.6, -6.2, 0.1],
 [1.6, -6.2, 0.1]]
ElevatorOutPointsFar = [[-4.6, -12.2, 0.1],
 [4.6, -12.2, 0.1],
 [-1.6, -13.2, 0.1],
 [1.6, -13.2, 0.1]]
