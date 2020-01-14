from direct.showbase import PythonUtil
from pandac.PandaModules import VBase4, Vec3, Point3
from .CogdoUtil import VariableContainer, DevVariableContainer
AI = VariableContainer()
AI.GameActions = PythonUtil.Enum(('LandOnWinPlatform', 'WinStateFinished', 'GotoWinState', 'HitWhirlwind', 'HitLegalEagle', 'HitMinion', 'DebuffInvul', 'RequestEnterEagleInterest', 'RequestExitEagleInterest', 'RanOutOfTimePenalty', 'Died', 'Spawn', 'SetBlades', 'BladeLost'))
AI.BroadcastPeriod = 0.3
AI.SafezoneId2DeathDamage = {2000: 1,
 1000: 2,
 5000: 4,
 4000: 8,
 3000: 12,
 9000: 16}
AI.SafezoneId2WhirlwindDamage = {2000: 1,
 1000: 2,
 5000: 4,
 4000: 8,
 3000: 12,
 9000: 16}
AI.SafezoneId2LegalEagleDamage = {2000: 2,
 1000: 4,
 5000: 8,
 4000: 16,
 3000: 24,
 9000: 32}
AI.SafezoneId2MinionDamage = {2000: 1,
 1000: 2,
 5000: 4,
 4000: 8,
 3000: 12,
 9000: 16}
Camera = VariableContainer()
Camera.Angle = 12.5
Camera.Distance = 20
Camera.LookAtToonHeightOffset = 1.0
Camera.LeewayX = 0.5
Camera.MinLeewayZ = 0.5
Camera.MaxLeewayZ = 15.0
Camera.CatchUpRateZ = 3.0
Camera.LevelBoundsFactor = (0.6, 1.0, 0.9)
Camera.AlphaBetweenToon = 0.35
Camera.SpinRadius = 9.0
Camera.MaxSpinAngle = 20.0
Camera.MaxSpinX = 16.0
Gameplay = VariableContainer()
Gameplay.SecondsUntilGameOver = 60.0 * 3.0
Gameplay.TimeRunningOutSeconds = 45.0
Gameplay.IntroDurationSeconds = 24.0
Gameplay.FinishDurationSeconds = 10.0
Gameplay.GatherableFlashTime = 1.0
Gameplay.ToonAcceleration = {'forward': 40.0,
 'backward': 40.0,
 'turning': 40.0,
 'boostUp': 15.0,
 'fall': 10.0,
 'activeDropDown': 20.0,
 'activeDropBack': 40.0,
 'fan': 80.0}
Gameplay.ToonDeceleration = {'forward': 5.0,
 'backward': 3.0,
 'turning': 10.0,
 'fan': 25.0}
Gameplay.ToonVelMax = {'forward': 15.0,
 'backward': 6.0,
 'turning': 10.0,
 'boost': 5.5,
 'fall': 10.0,
 'fallNoFuel': 70.0,
 'fan': 55.0}
Gameplay.ToonTurning = {'turningSpeed': 15.0,
 'maxTurningAngle': 45.0}
Gameplay.RayPlatformCollisionThreshold = 0.2
Gameplay.UseVariableFanPower = True
Gameplay.FanMaxPower = 1.0
Gameplay.FanMinPower = 0.4
Gameplay.FanCollisionTubeRadius = 4.0
Gameplay.FanCollisionTubeHeight = 35.0
Gameplay.FanStreamerMinDuration = 0.2
Gameplay.FanStreamerMaxDuration = 0.5
Gameplay.WhirlwindCollisionTubeHeight = 100
Gameplay.WhirlwindCollisionTubeRadius = 4.0
Gameplay.WhirlwindMoveBackDist = 15.0
Gameplay.WhirlwindSpinTime = 1.0
Gameplay.WhirlwindMoveBackTime = 0.5
Gameplay.FlyingMinionCollisionRadius = 2.5
Gameplay.FlyingMinionCollisionHeightOffset = 5.0
Gameplay.FlyingMinionFloatOffset = 1.0
Gameplay.FlyingMinionFloatTime = 1.0
Gameplay.WalkingMinionCollisionRadius = 2.5
Gameplay.WalkingMinionCollisionHeightOffset = 2.0
Gameplay.MemoCollisionRadius = 1.5
Gameplay.MemoSpinRate = 60.0
Gameplay.DoesToonDieWithFuel = True
Gameplay.SafezoneId2LaffPickupHealAmount = {2000: 1,
 1000: 2,
 5000: 4,
 4000: 8,
 3000: 12,
 9000: 16}
Gameplay.InvulBuffTime = 15.0
Gameplay.InvulBlinkTime = 5.0
Gameplay.InvulSingleBlinkTime = 0.5
Gameplay.PropellerCollisionRadius = 3.0
Gameplay.PropellerRespawnTime = 5.0
Gameplay.FuelBurnRate = 0.1
Gameplay.DepleteFuelStates = ['FlyingUp']
Gameplay.FuelNormalAmt = 1.0
Gameplay.FuelLowAmt = 0.66
Gameplay.FuelVeryLowAmt = 0.33
Gameplay.FuelStates = PythonUtil.Enum(('FuelNoPropeller', 'FuelEmpty', 'FuelVeryLow', 'FuelLow', 'FuelNormal'))
Gameplay.RefuelPropSpeed = 5.0
Gameplay.OverdrivePropSpeed = 2.5
Gameplay.NormalPropSpeed = 1.5
Gameplay.TargetedWarningLabelScale = 3.5
Gameplay.TargetedWarningSingleBlinkTime = 0.25
Gameplay.TargetedWarningBlinkTime = 3.0
Gameplay.HitKnockbackDist = 15.0
Gameplay.HitKnockbackTime = 0.5
Gameplay.HitCooldownTime = 2.0
Gameplay.BackpackStates = PythonUtil.Enum(('Normal', 'Targeted', 'Attacked', 'Refuel'))
Gameplay.BackpackRefuelDuration = 4.0
Gameplay.BackpackState2TextureName = {Gameplay.BackpackStates.Normal: 'tt_t_ara_cfg_propellerPack',
 Gameplay.BackpackStates.Targeted: 'tt_t_ara_cfg_propellerPack_eagleTarget',
 Gameplay.BackpackStates.Attacked: 'tt_t_ara_cfg_propellerPack_eagleAttack',
 Gameplay.BackpackStates.Refuel: 'tt_t_ara_cfg_propellerPack_flash'}
Gameplay.MinionDnaName = 'bf'
Gameplay.MinionScale = 0.8
Gui = VariableContainer()
Gui.FuelNumBladesPos2D = (-0.005, -0.017)
Gui.FuelNumBladesScale = 0.07
Gui.FuelPos2D = (-1.19, -0.24)
Gui.NumBlades2FuelColor = {0: (0.9, 0.15, 0.15, 1.0),
 1: (0.9, 0.15, 0.15, 1.0),
 2: (0.9, 0.9, 0.15, 1.0),
 3: (0.25, 0.65, 0.25, 1.0)}
Gui.FuelNormalColor = (0.25, 0.65, 0.25, 1.0)
Gui.FuelLowColor = (0.9, 0.9, 0.15, 1.0)
Gui.FuelVeryLowColor = (0.9, 0.15, 0.15, 1.0)
Gui.ProgressPos2D = (1.15, -0.15)
Gui.ProgressHPos2D = (0, 0.82)
Gui.MarkerScale = 0.03
Gui.LocalMarkerScale = 0.0425
LegalEagle = VariableContainer()
LegalEagle.EagleAndTargetDistCameraTrackThreshold = 30.0
LegalEagle.InterestConeLength = 80
LegalEagle.InterestConeOffset = 5.0
LegalEagle.InterestConeAngle = 60
LegalEagle.DamageSphereRadius = 3.0
LegalEagle.OnNestDamageSphereRadius = 6.0
LegalEagle.VerticalOffset = -6.0
LegalEagle.PlatformVerticalOffset = 0.0
LegalEagle.LiftOffTime = 0.5
LegalEagle.LiftOffHeight = 5.0
LegalEagle.LockOnSpeed = 3.0
LegalEagle.LockOnTime = 2.0
LegalEagle.ExtraPostCooldownTime = 2.0
LegalEagle.LockOnDistanceFromNest = -7.0
LegalEagle.ChargeUpTime = 0.75
LegalEagle.RetreatToNestTime = 2.0
LegalEagle.PreAttackTime = 0.75
LegalEagle.PostAttackTime = 0.5
LegalEagle.RetreatToSkyTime = 1.25
LegalEagle.EagleAttackShouldXCorrect = True
LegalEagle.AttackRateOfChangeVec = Vec3(1.0, 1.0, 2.0)
LegalEagle.PostAttackLength = 5.0
LegalEagle.CooldownTime = 5.0
LegalEagle.PostCooldownHeightOffNest = 40.0
Dev = DevVariableContainer('cogdoflying')
Dev.DisableDeath = False
Dev.InfiniteFuel = False
Dev.InfiniteTimeLimit = True
Dev.Invincibility = False
Dev.NoLegalEagleAttacks = False
Audio = VariableContainer()
Audio.Cutoff = 75.0
Audio.MusicFiles = {'normal': 'phase_4/audio/bgm/MG_cannon_game.ogg',
 'end': 'phase_4/audio/bgm/FF_safezone.ogg',
 'waiting': 'phase_4/audio/bgm/m_match_bg2.ogg',
 'invul': 'phase_4/audio/bgm/MG_CogThief.ogg',
 'timeRunningOut': 'phase_7/audio/bgm/encntr_suit_winning_indoor.ogg'}
Audio.SfxFiles = {'propeller': 'phase_4/audio/sfx/TB_propeller.ogg',
 'propeller_damaged': 'phase_5/audio/sfx/tt_s_ara_cfg_propellers_damaged.ogg',
 'fan': 'phase_4/audio/sfx/target_wind_float_loop.ogg',
 'getMemo': 'phase_4/audio/sfx/MG_maze_pickup.ogg',
 'getLaff': 'phase_4/audio/sfx/avatar_emotion_laugh.ogg',
 'getRedTape': 'phase_5/audio/sfx/SA_red_tape.ogg',
 'invulBuff': 'phase_4/audio/sfx/ring_get.ogg',
 'invulDebuff': 'phase_4/audio/sfx/ring_miss.ogg',
 'refuel': 'phase_5/audio/sfx/LB_receive_evidence.ogg',
 'bladeBreak': 'phase_5/audio/sfx/tt_s_ara_cfg_propellerBreaks.ogg',
 'popupHelpText': 'phase_3/audio/sfx/GUI_balloon_popup.ogg',
 'collide': 'phase_3.5/audio/sfx/AV_collision.ogg',
 'whirlwind': 'phase_5/audio/sfx/tt_s_ara_cfg_whirlwind.ogg',
 'toonInWhirlwind': 'phase_5/audio/sfx/tt_s_ara_cfg_toonInWhirlwind.ogg',
 'death': 'phase_5/audio/sfx/tt_s_ara_cfg_toonFalls.ogg',
 'legalEagleScream': 'phase_5/audio/sfx/tt_s_ara_cfg_eagleCry.ogg',
 'toonHit': 'phase_5/audio/sfx/tt_s_ara_cfg_toonHit.ogg',
 'lose': 'phase_4/audio/sfx/MG_lose.ogg',
 'win': 'phase_4/audio/sfx/MG_win.ogg',
 'refuelSpin': 'phase_4/audio/sfx/clock12.ogg',
 'cogDialogue': 'phase_3.5/audio/dial/COG_VO_statement.ogg',
 'toonDialogue': 'phase_3.5/audio/dial/AV_dog_long.ogg'}
Level = VariableContainer()
Level.GatherableTypes = PythonUtil.Enum(('Memo', 'Propeller', 'LaffPowerup', 'InvulPowerup'))
Level.ObstacleTypes = PythonUtil.Enum(('Whirlwind', 'Fan', 'Minion'))
Level.PlatformTypes = PythonUtil.Enum(('Platform', 'StartPlatform', 'EndPlatform'))
Level.PlatformType2SpawnOffset = {Level.PlatformTypes.Platform: 2.5,
 Level.PlatformTypes.StartPlatform: 5.0,
 Level.PlatformTypes.EndPlatform: 5.0}
Level.QuadLengthUnits = 170
Level.QuadVisibilityAhead = 1
Level.QuadVisibilityBehind = 0
Level.StartPlatformLength = 55
Level.StartPlatformHeight = 20
Level.EndPlatformLength = 55
Level.EndPlatformHeight = 0
Level.FogColor = VBase4(0.18, 0.19, 0.32, 1.0)
Level.RenderFogStartFactor = 0.22
Level.GatherablesDefaultSpread = 1.0
Level.NumMemosInRing = 6
Level.PropellerSpinDuration = 10.0
Level.QuadsByDifficulty = {1: (2, 4, 5),
 2: (1, 3, 7),
 3: (6, 8)}
Level.DifficultyOrder = {2000: (1, 1, 1, 2, 1),
 1000: (1, 1, 2, 2, 1),
 5000: (1, 2, 1, 2, 2),
 4000: (1, 2, 1, 2, 3, 2),
 3000: (1, 2, 2, 3, 2, 3),
 9000: (2, 3, 2, 3, 2, 3, 2)}
Dev.WantTempLevel = True
Dev.DevQuadsOrder = (1, 2, 3, 4, 5, 6, 7, 8)
Level.AddSparkleToPowerups = True
Level.AddParticlesToStreamers = True
Level.IgnoreLaffPowerups = False
Level.SpawnLaffPowerupsInNests = True
Level.LaffPowerupNestOffset = Point3(0.0, 2.0, 3.0)
Level.PlatformName = '*lightFixture'
Level.GatherablesPathName = 'gatherables_path*'
Level.GatherablesRingName = 'gatherables_ring_path*'
Level.PropellerName = '*propeller_loc*'
Level.PowerupType2Loc = {Level.GatherableTypes.LaffPowerup: 'laff_powerup_loc*',
 Level.GatherableTypes.InvulPowerup: 'invul_powerup_loc*'}
Level.PowerupType2Model = {Level.GatherableTypes.LaffPowerup: 'legalEagleFeather',
 Level.GatherableTypes.InvulPowerup: 'redTapePickup'}
Level.PowerupType2Node = {Level.GatherableTypes.LaffPowerup: 'feather',
 Level.GatherableTypes.InvulPowerup: 'redTape'}
Level.GatherableType2TextureName = {Level.GatherableTypes.LaffPowerup: 'tt_t_ara_cfg_legalEagleFeather_flash',
 Level.GatherableTypes.InvulPowerup: 'tt_t_ara_cfg_redTapePickup_flash',
 Level.GatherableTypes.Memo: 'tt_t_ara_csa_memo_flash',
 Level.GatherableTypes.Propeller: 'tt_t_ara_cfg_propellers_flash'}
Level.WhirlwindName = '*whirlwindPlaceholder'
Level.WhirlwindPathName = '_path*'
Level.StreamerName = '*streamerPlaceholder'
Level.MinionWalkingPathName = '*minion_walking_path*'
Level.MinionFlyingPathName = '*minion_flying_path*'
Level.LegalEagleNestName = '*eagleNest_loc*'
