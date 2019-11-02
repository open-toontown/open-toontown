from pandac.PandaModules import *
from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownGlobals
GAME_TIME = 60
MAX_SCORE = 23
MIN_SCORE = 5
NUMSTARS = 5
ONSCREENASSIGNMENTS = 5
PHOTO_ROTATION_MIN = -20
PHOTO_ROTATION_MAX = 20
PHOTO_ROTATION_VEL = 25.0
PHOTO_ANGLE_MIN = -15
PHOTO_ANGLE_MAX = 10
PHOTO_ANGLE_VEL = 25.0

def calcScore(t):
    range = MAX_SCORE - MIN_SCORE
    score = MAX_SCORE - range * (float(t) / GAME_TIME)
    return int(score + 0.5)


AREA_DATA = {}
AREA_DATA[ToontownGlobals.ToontownCentral] = {}
AREA_DATA[ToontownGlobals.ToontownCentral]['FILMCOUNT'] = 32
AREA_DATA[ToontownGlobals.ToontownCentral]['TIME'] = 120
AREA_DATA[ToontownGlobals.ToontownCentral]['CAMERA_INTIAL_POSTION'] = Point3(0, 50, 20)
AREA_DATA[ToontownGlobals.ToontownCentral]['DNA_TRIO'] = ('phase_4/dna/storage_TT_sz.dna', 'phase_4/dna/storage_TT.dna', 'phase_4/dna/toontown_central_sz.dna')
AREA_DATA[ToontownGlobals.ToontownCentral]['TRIPOD_OFFSET'] = Point3(0, 0, 7.0)
AREA_DATA[ToontownGlobals.ToontownCentral]['START_HPR'] = Point3(-87.8752, -0.378549, 0)
AREA_DATA[ToontownGlobals.ToontownCentral]['PATHS'] = ([Point3(10, 20, 4.025),
  Point3(10, -3, 4.025),
  Point3(32, -5, 4.025),
  Point3(32, 12, 4.025)],
 [Point3(-58.396, -51.972, -1.386),
  Point3(-59.967, -66.906, 0.025),
  Point3(-56.416, -77.651, 0.025),
  Point3(-26.619, -74.156, 0.025),
  Point3(-10.664, -73.82, 0.025),
  Point3(5.421, -81.282, 2.525),
  Point3(5.421, -57.383, 0.025),
  Point3(-27.497, -34.525, 0.025),
  Point3(-41.784, -48.023, 0.025)],
 [Point3(-29.015, 36.498, 0.028),
  Point3(-45.701, 42.963, -0.904),
  Point3(-54.659, 65.987, 0.025),
  Point3(-45.458, 81.478, 0.025),
  Point3(-17.325, 83.591, 0.525),
  Point3(4.169, 69.942, 1.133),
  Point3(-10.625, 38.357, 0.036)],
 [Point3(-84.761, -74.52, 0.034),
  Point3(-101.685, -75.619, 0.525),
  Point3(-113.606, -71.806, 0.525),
  Point3(-111.463, -63.672, 0.525),
  Point3(-102.072, -60.867, 0.525),
  Point3(-94.049, -60.519, 0.035),
  Point3(-66.868, -64.715, 0.025)])
AREA_DATA[ToontownGlobals.ToontownCentral]['PATHANIMREL'] = (0,
 0,
 1,
 2)
AREA_DATA[ToontownGlobals.ToontownCentral]['ANIMATIONS'] = ([('wave', 2.0), (None, 1.0), (None, 1.0)], [('slip-forward', 2.0), (None, 1.0), (None, 1.0)], [('shrug', 2.0), (None, 1.0)])
AREA_DATA[ToontownGlobals.ToontownCentral]['MOVEMODES'] = ([('walk', 1.0), ('run', 0.4)], [('run', 0.4)], [('walk', 1.0), ('sad-walk', 2.5)])
AREA_DATA[ToontownGlobals.DonaldsDock] = {}
AREA_DATA[ToontownGlobals.DonaldsDock]['FILMCOUNT'] = 28
AREA_DATA[ToontownGlobals.DonaldsDock]['TIME'] = 110
AREA_DATA[ToontownGlobals.DonaldsDock]['CAMERA_INTIAL_POSTION'] = Point3(0, 50, 20)
AREA_DATA[ToontownGlobals.DonaldsDock]['DNA_TRIO'] = ('phase_6/dna/storage_DD_sz.dna', 'phase_6/dna/storage_DD.dna', 'phase_6/dna/donalds_dock_sz.dna')
AREA_DATA[ToontownGlobals.DonaldsDock]['TRIPOD_OFFSET'] = Point3(0, -4.0, 9.0)
AREA_DATA[ToontownGlobals.DonaldsDock]['START_HPR'] = Point3(218.211, -6.7879, 0)
AREA_DATA[ToontownGlobals.DonaldsDock]['PATHS'] = ([Point3(-115.6, 39.4, 5.692),
  Point3(-109.9, -14, 5.692),
  Point3(-112.652, -46.7, 5.692),
  Point3(-68.9, -74.7, 5.692),
  Point3(-0.2, -82.0, 5.692),
  Point3(-73.5, -72.2, 5.692),
  Point3(-112.0, -45, 5.692),
  Point3(-110.3, 17.5, 5.692)],
 [Point3(-67.143, 131.117, 3.28),
  Point3(-56.4, 101.4, 3.279),
  Point3(-51.425, 80.1, 3.279),
  Point3(-87.632, 56.718, 2.392),
  Point3(-114.1, 54.7, 3.28),
  Point3(-108.5, 80.5, 3.281),
  Point3(-82.672, 68.971, 3.28),
  Point3(-83.122, 101.9, 3.28)],
 [Point3(11.456, -82.521, 3.28),
  Point3(49.735, -70.46, 3.28),
  Point3(60.666, -42.735, 3.28),
  Point3(40.81, -76.633, 3.28)],
 [Point3(68.924, -33.681, 5.692),
  Point3(60.51, -31.574, 5.692),
  Point3(58.672, 12.253, 5.692),
  Point3(69.809, 48.261, 5.692),
  Point3(57.857, 46.134, 5.692),
  Point3(66.057, -22.476, 5.692)],
 [Point3(-24.439, 37.429, 0.2),
  Point3(-3.549, 19.343, 0.2),
  Point3(3.218, -1.475, 0.2),
  Point3(-12.292, -25.318, 0.2),
  Point3(-42.954, -25.706, 0.2),
  Point3(-55.102, 4.041, 0.2),
  Point3(-54.247, 16.051, 0.2)])
AREA_DATA[ToontownGlobals.DonaldsDock]['PATHANIMREL'] = (0,
 0,
 1,
 2,
 3)
AREA_DATA[ToontownGlobals.DonaldsDock]['ANIMATIONS'] = ([('wave', 2.0), (None, 1.0)],
 [('slip-forward', 2.0), (None, 1.0), (None, 1.0)],
 [('shrug', 2.0), (None, 1.0)],
 [(None, 1.0)])
AREA_DATA[ToontownGlobals.DonaldsDock]['MOVEMODES'] = ([('walk', 1.0)],
 [('run', 0.4)],
 [('walk', 1.0), ('sad-walk', 2.5)],
 [('swim', 1.0)])
AREA_DATA[ToontownGlobals.DaisyGardens] = {}
AREA_DATA[ToontownGlobals.DaisyGardens]['FILMCOUNT'] = 26
AREA_DATA[ToontownGlobals.DaisyGardens]['TIME'] = 100
AREA_DATA[ToontownGlobals.DaisyGardens]['CAMERA_INTIAL_POSTION'] = Point3(0, 50, 20)
AREA_DATA[ToontownGlobals.DaisyGardens]['DNA_TRIO'] = ('phase_8/dna/storage_DG_sz.dna', 'phase_8/dna/storage_DG.dna', 'phase_8/dna/daisys_garden_sz.dna')
AREA_DATA[ToontownGlobals.DaisyGardens]['TRIPOD_OFFSET'] = Point3(0, 0, 6.0)
AREA_DATA[ToontownGlobals.DaisyGardens]['START_HPR'] = Point3(0.0, 0.0, 0.0)
AREA_DATA[ToontownGlobals.DaisyGardens]['PATHS'] = ([Point3(-37.252, 25.513, 0.025),
  Point3(-30.032, 37.9, 0.025),
  Point3(-38.694, 50.631, 0.025),
  Point3(-52.1, 52.926, 0.025),
  Point3(-62.807, 43.957, 0.025)],
 [Point3(36.214, 117.447, 5.0),
  Point3(3.534, 137.083, 5.0),
  Point3(-9.384, 136.973, 5.0),
  Point3(-26.377, 120.564, 5.0),
  Point3(-43.268, 122.335, 5.0),
  Point3(-26.377, 120.564, 5.0),
  Point3(-9.384, 136.973, 5.0),
  Point3(3.534, 137.083, 5.0)],
 [Point3(15.675, 111.21, 0.025),
  Point3(21.261, 119.429, 0.025),
  Point3(6.201, 129.047, 0.025),
  Point3(-10.984, 124.684, 0.025),
  Point3(4.039, 130.275, 0.025),
  Point3(22.645, 118.204, 0.025)],
 [Point3(27.348, 16.836, 0.025),
  Point3(47.152, 18.038, 0.025),
  Point3(65.325, 22.322, 0.025),
  Point3(73.063, 43.545, 0.025),
  Point3(75.228, 66.869, 0.025),
  Point3(69.468, 23.798, 0.025),
  Point3(46.43, 20.473, 0.025)])
AREA_DATA[ToontownGlobals.DaisyGardens]['PATHANIMREL'] = (0,
 0,
 1,
 2)
AREA_DATA[ToontownGlobals.DaisyGardens]['ANIMATIONS'] = ([('wave', 2.0), (None, 1.0)], [('jump', 2.0), (None, 1.0), (None, 1.0)], [('bow', 2.0), ('happy-dance', 2.0), (None, 1.0)])
AREA_DATA[ToontownGlobals.DaisyGardens]['MOVEMODES'] = ([('walk', 1.0), ('run', 0.4)], [('run', 0.4)], [('walk', 1.0), ('run', 0.4)])
AREA_DATA[ToontownGlobals.MinniesMelodyland] = {}
AREA_DATA[ToontownGlobals.MinniesMelodyland]['FILMCOUNT'] = 23
AREA_DATA[ToontownGlobals.MinniesMelodyland]['TIME'] = 95
AREA_DATA[ToontownGlobals.MinniesMelodyland]['CAMERA_INTIAL_POSTION'] = Point3(0, -50, 20)
AREA_DATA[ToontownGlobals.MinniesMelodyland]['DNA_TRIO'] = ('phase_6/dna/storage_MM_sz.dna', 'phase_6/dna/storage_MM.dna', 'phase_6/dna/minnies_melody_land_sz.dna')
AREA_DATA[ToontownGlobals.MinniesMelodyland]['TRIPOD_OFFSET'] = Point3(0, 0, 6.0)
AREA_DATA[ToontownGlobals.MinniesMelodyland]['START_HPR'] = Point3(71.3028, -3.12932, 0)
AREA_DATA[ToontownGlobals.MinniesMelodyland]['PATHS'] = ([Point3(-42.35, -16.0, -12.476),
  Point3(-23.7, -49.0, -12.476),
  Point3(12.4, -62.1, -12.476),
  Point3(37.8, -31.163, -12.476),
  Point3(29.5, 8.9, -12.476),
  Point3(-11.1, 19.6, -12.476),
  Point3(-34.4, -3.4, -12.476)],
 [Point3(133.976, -67.686, -6.618),
  Point3(126.749, -47.351, 0.404),
  Point3(130.493, -33.429, 4.534),
  Point3(126.239, -15.853, 5.25),
  Point3(129.774, -0.535, 3.114),
  Point3(130.83, 25.08, -5.688),
  Point3(128.077, -5.33, 4.291),
  Point3(128.399, -23.142, 5.457),
  Point3(129.239, -39.886, 2.914),
  Point3(133.063, -78.315, -10.756)],
 [Point3(50.757, -102.705, 6.725),
  Point3(-23.276, -108.546, 6.725),
  Point3(-57.283, -72.081, 6.725),
  Point3(-21.699, -109.808, 6.725),
  Point3(19.614, -108.591, 6.725)],
 [Point3(51.761, -36.129, -14.627),
  Point3(26.374, -73.664, -14.645),
  Point3(14.322, -89.378, -14.562),
  Point3(61.594, -91.931, -14.524)])
AREA_DATA[ToontownGlobals.MinniesMelodyland]['PATHANIMREL'] = (0,
 0,
 1,
 2)
AREA_DATA[ToontownGlobals.MinniesMelodyland]['ANIMATIONS'] = ([('wave', 2.0), (None, 1.0)], [('jump', 2.0),
  ('slip-forward', 2.0),
  (None, 1.0),
  (None, 1.0)], [('shrug', 2.0), ('confused', 2.0), (None, 1.0)])
AREA_DATA[ToontownGlobals.MinniesMelodyland]['MOVEMODES'] = ([('walk', 1.0), ('run', 0.4)], [('run', 0.4)], [('walk', 1.0), ('sad-walk', 2.5)])
AREA_DATA[ToontownGlobals.TheBrrrgh] = {}
AREA_DATA[ToontownGlobals.TheBrrrgh]['FILMCOUNT'] = 21
AREA_DATA[ToontownGlobals.TheBrrrgh]['TIME'] = 90
AREA_DATA[ToontownGlobals.TheBrrrgh]['CAMERA_INTIAL_POSTION'] = Point3(0, 50, 20)
AREA_DATA[ToontownGlobals.TheBrrrgh]['DNA_TRIO'] = ('phase_8/dna/storage_BR_sz.dna', 'phase_8/dna/storage_BR.dna', 'phase_8/dna/the_burrrgh_sz.dna')
AREA_DATA[ToontownGlobals.TheBrrrgh]['TRIPOD_OFFSET'] = Point3(0, 0, 6.0)
AREA_DATA[ToontownGlobals.TheBrrrgh]['START_HPR'] = Point3(-49.401, -11.6266, 0)
AREA_DATA[ToontownGlobals.TheBrrrgh]['PATHS'] = ([Point3(-82.52, -28.727, 3.009),
  Point3(-77.642, -4.616, 3.009),
  Point3(-51.006, 1.05, 3.009),
  Point3(-28.618, -28.449, 4.026),
  Point3(-37.948, -64.705, 4.714)],
 [Point3(-74.672, 62.15, 6.192),
  Point3(-92.602, 38.734, 6.192),
  Point3(-126.887, 34.757, 6.192),
  Point3(-138.12, 56.002, 6.192),
  Point3(-113.968, 32.661, 6.192),
  Point3(-84.717, 46.837, 6.192)],
 [Point3(-55.239, -126.921, 6.192),
  Point3(-20.35, -108.696, 6.192),
  Point3(5.028, -61.737, 6.192),
  Point3(27.967, -19.683, 6.192),
  Point3(11.487, 2.913, 6.192),
  Point3(-23.727, -47.344, 6.192)],
 [Point3(-143.22, -104.727, 6.192),
  Point3(-152.989, -64.372, 6.192),
  Point3(-139.328, -6.628, 4.018),
  Point3(-135.815, -39.935, 3.009)])
AREA_DATA[ToontownGlobals.TheBrrrgh]['PATHANIMREL'] = (0,
 0,
 1,
 2)
AREA_DATA[ToontownGlobals.TheBrrrgh]['ANIMATIONS'] = ([('wave', 2.0), (None, 1.0)], [('applause', 2.0),
  ('slip-forward', 2.0),
  (None, 1.0),
  (None, 1.0)], [('shrug', 2.0),
  ('confused', 2.0),
  ('angry', 2.0),
  (None, 1.0)])
AREA_DATA[ToontownGlobals.TheBrrrgh]['MOVEMODES'] = ([('walk', 1.0), ('running-jump', 0.4)], [('run', 0.4)], [('walk', 1.0), ('sad-walk', 2.5)])
AREA_DATA[ToontownGlobals.DonaldsDreamland] = {}
AREA_DATA[ToontownGlobals.DonaldsDreamland]['FILMCOUNT'] = 18
AREA_DATA[ToontownGlobals.DonaldsDreamland]['TIME'] = 85
AREA_DATA[ToontownGlobals.DonaldsDreamland]['CAMERA_INTIAL_POSTION'] = Point3(0, 50, 20)
AREA_DATA[ToontownGlobals.DonaldsDreamland]['DNA_TRIO'] = ('phase_8/dna/storage_DL_sz.dna', 'phase_8/dna/storage_DL.dna', 'phase_8/dna/donalds_dreamland_sz.dna')
AREA_DATA[ToontownGlobals.DonaldsDreamland]['TRIPOD_OFFSET'] = Point3(0, 0, 6.0)
AREA_DATA[ToontownGlobals.DonaldsDreamland]['START_HPR'] = Point3(-137.183, -9.06236, 0)
AREA_DATA[ToontownGlobals.DonaldsDreamland]['PATHS'] = ([Point3(-51.222, 90.874, 0.025),
  Point3(0.715, 94.789, 0.025),
  Point3(30.715, 94.0, 0.025),
  Point3(69.181, 93.45, 0.025),
  Point3(30.715, 94.0, 0.025),
  Point3(-8.696, 91.799, 0.025)],
 [Point3(-70.403, 29.575, 2.125),
  Point3(-68.829, -21.076, 2.125),
  Point3(-104.669, -24.758, 2.125),
  Point3(-114.801, 21.777, 2.125)],
 [Point3(15.923, -41.824, -16.089),
  Point3(18.217, 34.322, -14.732),
  Point3(7.087, 61.964, -16.058),
  Point3(50.447, 8.17, -13.975),
  Point3(-15.793, -19.916, -14.041),
  Point3(-26.41, 26.786, -14.371),
  Point3(20.853, 1.639, -13.975)],
 [Point3(-35.391, -24.112, -14.241),
  Point3(-54.364, -12.996, -13.975),
  Point3(-51.578, 21.964, -14.139),
  Point3(-10.49, 15.537, -13.974),
  Point3(-25.728, -14.665, -13.975),
  Point3(-43.923, -32.324, -14.634)])
AREA_DATA[ToontownGlobals.DonaldsDreamland]['PATHANIMREL'] = (0,
 0,
 1,
 2)
AREA_DATA[ToontownGlobals.DonaldsDreamland]['ANIMATIONS'] = ([('wave', 2.0), (None, 1.0)], [('applause', 2.0),
  ('jump', 2.0),
  ('slip-forward', 2.0),
  (None, 1.0),
  (None, 1.0)], [('shrug', 2.0), ('angry', 2.0), (None, 1.0)])
AREA_DATA[ToontownGlobals.DonaldsDreamland]['MOVEMODES'] = ([('walk', 1.0), ('catch-run', 0.4)], [('run', 0.4), ('running-jump', 0.4)], [('walk', 1.0), ('sad-walk', 2.5)])
