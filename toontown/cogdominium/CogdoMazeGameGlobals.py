from direct.showbase import PythonUtil
from pandac.PandaModules import VBase4
GameActions = PythonUtil.Enum(('EnterDoor',
 'RevealDoor',
 'OpenDoor',
 'Countdown',
 'TimeAlert'))
SecondsUntilTimeout = 4.0 * 60.0
SecondsUntilGameEnds = 60.0
SecondsForTimeAlert = 60.0
MaxPlayers = 4
IntroDurationSeconds = 24.0
FinishDurationSeconds = 5.0
PlayerCollisionName = 'CogdoMazePlayer_Collision'
LocalPlayerCollisionName = 'CogdoMazeLocalPlayer_Collision'
PlayerCollisionRadius = 1.0
HitCooldownTime = 2.0
HintTimeout = 6.0
NumQuadrants = (3, 3)
FrameWallThickness = 1
QuadrantUnitGap = 3
TotalBarriers = 12
NumBarriers = 3
MazeBarriers = ([(7, 34),
  (8, 34),
  (9, 34),
  (10, 34)],
 [(24, 34),
  (25, 34),
  (26, 34),
  (27, 34)],
 [(41, 34),
  (42, 34),
  (43, 34),
  (44, 34)],
 [(7, 17),
  (8, 17),
  (9, 17),
  (10, 17)],
 [(24, 17),
  (25, 17),
  (26, 17),
  (27, 17)],
 [(41, 17),
  (42, 17),
  (43, 17),
  (44, 17)],
 [(17, 41),
  (17, 42),
  (17, 43),
  (17, 44)],
 [(17, 24),
  (17, 25),
  (17, 26),
  (17, 27)],
 [(17, 7),
  (17, 8),
  (17, 9),
  (17, 10)],
 [(34, 41),
  (34, 42),
  (34, 43),
  (34, 44)],
 [(34, 24),
  (34, 25),
  (34, 26),
  (34, 27)],
 [(34, 7),
  (34, 8),
  (34, 9),
  (34, 10)])
ToonRunSpeed = 11.2
CameraAngle = 60
CameraRemoteToonRadius = 6
CameraMinDistance = 40
CameraMaxDistance = 61
CamCutoffFactor = 1.34
ToonAnimationInfo = {'hit': ('slip-backward', 2.25, 12)}
NumPickups = 256
PickupsUntilDoorOpens = int(NumPickups * 0.6)
SuitCollisionName = 'CogdoMazeSuit_Collision'
SuitWalkSameDirectionProb = 1
SuitWalkTurnAroundProb = 100
SuitTypes = PythonUtil.Enum(('Boss', 'FastMinion', 'SlowMinion'))
SuitData = {}
SuitData[SuitTypes.Boss] = {'dnaName': 'ms',
 'cellWalkPeriod': 192,
 'toonDamage': 3.0,
 'scale': 2.5,
 'hp': 2,
 'memos': 0}
SuitData[SuitTypes.FastMinion] = {'dnaName': 'nd',
 'cellWalkPeriod': 64,
 'toonDamage': 1.0,
 'scale': 1.3,
 'hp': 1,
 'memos': 3}
SuitData[SuitTypes.SlowMinion] = {'dnaName': 'cc',
 'cellWalkPeriod': 160,
 'toonDamage': 2.0,
 'scale': 1.33,
 'hp': 1,
 'memos': 2}
NumSuits = (4, 5, 5)
BossSpinTime = 1.0
BossSpinCount = 2
BlinkFrequency = 1.0
BlinkSpeed = 0.5
BlinkColor = VBase4(1.0, 0.4, 0.4, 1.0)
SuitsModifier = (0, 6, 9)
DamageModifier = 9.0
DropShakeEnabled = True
BossShakeEnabled = True
DropShakeStrength = 4.0
DropMaxDistance = 20.0
BossShakeStrength = 1.2
BossMaxDistance = 25.0
BossShakeTime = 0.53
BossStompSfxCutoff = 70.0
BossCogStompAnimationPlayrateFactor = 0.75
CameraShakeFalloff = 2.2
CameraShakeMax = 5.0
QuakeSfxFalloff = 0.01
QuakeSfxMax = 2.0
QuakeSfxEnabled = True
DropFrequency = 3
DropDamage = 0
DropTime = 1.0
ShadowTime = 2.0
DropHeight = 70
DropFadeTime = 1.0
DropCollisionRadius = 1.0
DropCollisionName = 'DropCollision'
DroppedCollisionRadius = 2.0
DropChance = 0.25
GagChance = 0.5
GagSitTime = 15.0
BalloonDelay = 1.2
ThrowDistance = 18
ThrowDuration = 0.5
ThrowStartFrame = 61
ThrowEndFrame = 64
ThrowPlayRate = 1.5
GagPickupScale = 2.0
GagPickupCollisionRadius = 1.0
GagPickupCollisionName = 'PickUpCollision'
GagColors = ((1.0,
  0.27,
  0.27,
  1.0),
 (1.0,
  0.66,
  0.15,
  1.0),
 (0.31,
  1.0,
  0.29,
  1.0),
 (0.31,
  0.62,
  1.0,
  1.0),
 (0.91,
  0.32,
  1.0,
  1.0))
GagCollisionName = 'Gag_Collision'
WaterCoolerTriggerRadius = 2.5
WaterCoolerTriggerOffset = (0, -1.5, 0)
WaterCoolerCollisionName = 'WaterCooler_Collision'
WaterCoolerShowEventName = 'CogdoMazeWaterCooler_Show'
WaterCoolerHideEventName = 'CogdoMazeWaterCooler_Hide'
AudioCutoff = 75.0
MusicFiles = {'normal': 'phase_9/audio/bgm/CHQ_FACT_bg.mid',
 'timeRunningOut': 'phase_7/audio/bgm/encntr_suit_winning_indoor.mid'}
SfxFiles = {'toonHitByDrop': 'phase_5/audio/sfx/tt_s_ara_cmg_toonHit.mp3',
 'toonHit': 'phase_4/audio/sfx/MG_cannon_hit_dirt.mp3',
 'getMemo': 'phase_4/audio/sfx/MG_maze_pickup.mp3',
 'drop': 'phase_5/audio/sfx/tt_s_ara_cmg_itemHitsFloor.mp3',
 'throw': 'phase_3.5/audio/sfx/AA_pie_throw_only.mp3',
 'splat': 'phase_5/audio/sfx/SA_watercooler_spray_only.mp3',
 'cogSpin': 'phase_3.5/audio/sfx/Cog_Death.mp3',
 'cogDeath': 'phase_3.5/audio/sfx/ENC_cogfall_apart.mp3',
 'bossCogAngry': 'phase_5/audio/sfx/tt_s_ara_cmg_bossCogAngry.mp3',
 'cogStomp': 'phase_5/audio/sfx/tt_s_ara_cmg_cogStomp.mp3',
 'quake': 'phase_5/audio/sfx/tt_s_ara_cmg_groundquake.mp3',
 'waterCoolerFill': 'phase_5/audio/sfx/tt_s_ara_cmg_waterCoolerFill.mp3',
 'lose': 'phase_4/audio/sfx/MG_lose.mp3',
 'win': 'phase_4/audio/sfx/MG_win.mp3',
 'cogDialogue': 'phase_3.5/audio/dial/COG_VO_statement.mp3',
 'toonDialogue': 'phase_3.5/audio/dial/AV_dog_long.mp3'}
MessageLabelPos = (0.0, 0.0, -0.4)
MemoGuiPos = (-0.85, 0, -0.9)
MemoGuiTextScale = 0.1
MemoGuiTextColor = (0.95,
 0.95,
 0,
 1)
MapGuiBgColor = (0.9, 0.9, 0.9)
MapGuiFgColor = (0.5,
 0.5,
 0.5,
 1)
MapGuiPos = (1.05, 0.0, -0.71)
MapGuiScale = 0.225
MapGuiSuitMarkerFlashColor = (1.0, 0.0, 0.0)
MapGuiSuitMarkerSize = 0.075
MapGuiWaterCoolerMarkerSize = 0.08
QuestArrowScale = 5
QuestArrowColor = (1,
 1,
 0,
 1)
CoolerArrowScale = 8
CoolerArrowColor = (1,
 1,
 0,
 1)
CoolerArrowZ = 10
CoolerArrowBounce = 2
CoolerArrowSpeed = 2
BossGuiScale = 0.8
BossGuiPos = (0, 0, -0.83)
BossGuiTitleLabelScale = 0.055
BossCodeFrameWidth = 0.13
BossCodeFrameGap = 0.005
BossCodeFrameLabelScale = 0.12
BossCodeFrameLabelNormalColor = (0,
 0,
 0,
 1)
BossCodeFrameLabelHighlightColor = (0,
 0.5,
 0,
 1)
