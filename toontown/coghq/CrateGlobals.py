from panda3d.core import *
CRATE_CLEAR = 0
CRATE_POWERUP = 1
CRATE_PUSH = 2
CrateNormals = [Vec3(1, 0, 0),
 Vec3(-1, 0, 0),
 Vec3(0, 1, 0),
 Vec3(0, -1, 0)]
CrateHprs = [Vec3(90, 0, 0),
 Vec3(270, 0, 0),
 Vec3(180, 0, 0),
 Vec3(0, 0, 0)]
T_PUSH = 1.5
T_PAUSE = 0.1
TorsoToOffset = {'ss': 0.17,
 'ms': 0.18,
 'ls': 0.75,
 'sd': 0.17,
 'md': 0.18,
 'ld': 0.75,
 's': 0.17,
 'm': 0.18,
 'l': 0.75}
