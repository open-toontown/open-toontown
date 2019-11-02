from pandac.PandaModules import *
from direct.showbase.PythonUtil import Enum, invertDictLossless
import math
from toontown.toonbase import ToontownGlobals
OurPetsMoodChangedKey = 'OurPetsMoodChanged'
ThinkPeriod = 1.5
MoodDriftPeriod = 300.0
MovePeriod = 1.0 / 4
PosBroadcastPeriod = 1.0 / 5
LonelinessUpdatePeriod = 100.0
SubmergeDistance = 0.7
MaxAvatarAwareness = 3
NonPetSphereRadius = 5.0
PetSphereRadius = 3.0
UnstickSampleWindow = 20
UnstickCollisionThreshold = int(0.5 * UnstickSampleWindow)
PriorityFleeFromAvatar = 0.6
PriorityDefault = 1.0
PriorityChaseAv = 1.0
PriorityDebugLeash = 50.0
PriorityDoTrick = 100.0
PrimaryGoalDecayDur = 60.0
PrimaryGoalScale = 1.3
HungerChaseToonScale = 1.2
FleeFromOwnerScale = 0.5
GettingAttentionGoalScale = 1.2
GettingAttentionGoalScaleDur = 7.0
AnimMoods = Enum('EXCITED, SAD, NEUTRAL')
FwdSpeed = 12.0
RotSpeed = 360.0
_HappyMult = 1.0
HappyFwdSpeed = FwdSpeed * _HappyMult
HappyRotSpeed = RotSpeed * _HappyMult
_SadMult = 0.3
SadFwdSpeed = FwdSpeed * _SadMult
SadRotSpeed = RotSpeed * _SadMult
PETCLERK_TIMER = 180
PET_MOVIE_CLEAR = 0
PET_MOVIE_START = 1
PET_MOVIE_COMPLETE = 2
PET_MOVIE_FEED = 3
PET_MOVIE_SCRATCH = 4
PET_MOVIE_CALL = 5
FEED_TIME = 10.0
SCRATCH_TIME = 8.042
CALL_TIME = 8.0 / 3
FEED_DIST = {'long': 4.0,
 'medium': 4.0,
 'short': 4.0}
FEED_AMOUNT = 1
SCRATCH_DIST = {'long': 2.0,
 'medium': 1.5,
 'short': 1.0}
TELEPORT_IN_DURATION = 2.34
TELEPORT_OUT_DURATION = 4.5
ZoneToCostRange = {ToontownGlobals.ToontownCentral: (100, 500),
 ToontownGlobals.DonaldsDock: (600, 1700),
 ToontownGlobals.DaisyGardens: (1000, 2500),
 ToontownGlobals.MinniesMelodyland: (1500, 3000),
 ToontownGlobals.TheBrrrgh: (2500, 4000),
 ToontownGlobals.DonaldsDreamland: (3000, 5000)}
