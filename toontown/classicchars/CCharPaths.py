from pandac.PandaModules import Point3
from pandac.PandaModules import Vec3
import copy
from toontown.toonbase import TTLocalizer
__mickeyPaths = {'a': (Point3(17, -17, 4.025), ('b', 'e')),
 'b': (Point3(17.5, 7.6, 4.025), ('c', 'e')),
 'c': (Point3(85, 11.5, 4.025), ('d',)),
 'd': (Point3(85, -13, 4.025), ('a',)),
 'e': (Point3(-27.5, -5.25, 0.0), ('a', 'b', 'f')),
 'f': (Point3(-106.15, -4.0, -2.5), ('e',
        'g',
        'h',
        'i')),
 'g': (Point3(-89.5, 93.5, 0.5), ('f', 'h')),
 'h': (Point3(-139.95, 1.69, 0.5), ('f', 'g', 'i')),
 'i': (Point3(-110.95, -68.57, 0.5), ('f', 'h'))}
__mickeyWaypoints = (('a',
  'e',
  1,
  []),
 ('b',
  'e',
  1,
  []),
 ('e',
  'f',
  1,
  [Point3(-76.87, -7.85, -1.85), Point3(-80.57, -4.0, -1.85)]),
 ('f',
  'g',
  1,
  [Point3(-106.62, 28.65, -1.5)]),
 ('g',
  'h',
  1,
  [Point3(-128.38, 60.27, 0.5)]),
 ('h',
  'f',
  1,
  []),
 ('h',
  'i',
  1,
  [Point3(-137.13, -42.79, 0.5)]),
 ('i',
  'f',
  1,
  []))
__minniePaths = {'a': (Point3(53.334, 71.057, 6.525), ('b', 'r')),
 'b': (Point3(127.756, 58.665, -11.75), ('a', 's', 'c')),
 'c': (Point3(130.325, 15.174, -2.003), ('b', 'd')),
 'd': (Point3(126.173, 7.057, 0.522), ('c', 'e')),
 'e': (Point3(133.843, -6.618, 4.71), ('d',
        'f',
        'g',
        'h')),
 'f': (Point3(116.876, 1.119, 3.304), 'e'),
 'g': (Point3(116.271, -41.568, 3.304), ('e', 'h')),
 'h': (Point3(128.983, -49.656, -0.231), ('e',
        'g',
        'i',
        'j')),
 'i': (Point3(106.024, -75.249, -4.498), 'h'),
 'j': (Point3(135.016, -93.072, -13.376), ('h', 'k', 'z')),
 'k': (Point3(123.966, -100.242, -10.879), ('j', 'l')),
 'l': (Point3(52.859, -109.081, 6.525), ('k', 'm')),
 'm': (Point3(-32.071, -107.049, 6.525), ('l', 'n')),
 'n': (Point3(-40.519, -99.685, 6.525), ('m', 'o')),
 'o': (Point3(-40.245, -88.634, 6.525), ('n', 'p')),
 'p': (Point3(-66.3, -62.192, 6.525), ('o', 'q')),
 'q': (Point3(-66.212, 23.069, 6.525), ('p', 'r')),
 'r': (Point3(-18.344, 69.532, 6.525), ('q', 'a')),
 's': (Point3(91.357, 44.546, -13.475), ('b', 't')),
 't': (Point3(90.355, 6.279, -13.475), ('s', 'u')),
 'u': (Point3(-13.765, 42.362, -14.553), ('t', 'v')),
 'v': (Point3(-52.627, 7.428, -14.553), ('u', 'w')),
 'w': (Point3(-50.654, -54.879, -14.553), ('v', 'x')),
 'x': (Point3(-3.711, -81.819, -14.553), ('w', 'y')),
 'y': (Point3(90.777, -49.714, -13.475), ('z', 'x')),
 'z': (Point3(90.059, -79.426, -13.475), ('j', 'y'))}
__minnieWaypoints = (('a',
  'b',
  1,
  []),
 ('k',
  'l',
  1,
  []),
 ('b',
  'c',
  1,
  []),
 ('c',
  'd',
  1,
  []),
 ('d',
  'e',
  1,
  []),
 ('e',
  'f',
  1,
  []),
 ('e',
  'g',
  1,
  []),
 ('e',
  'h',
  1,
  []),
 ('g',
  'h',
  1,
  []),
 ('h',
  'i',
  1,
  []),
 ('h',
  'j',
  1,
  []),
 ('s',
  'b',
  1,
  []),
 ('t',
  'u',
  1,
  []),
 ('x',
  'y',
  1,
  []))
__goofyPaths = {'a': (Point3(64.995, 169.665, 10.027), ('b', 'q')),
 'b': (Point3(48.893, 208.912, 10.027), ('a', 'c')),
 'c': (Point3(5.482, 210.479, 10.03), ('b', 'd')),
 'd': (Point3(-34.153, 203.284, 10.029), ('c', 'e')),
 'e': (Point3(-66.656, 174.334, 10.026), ('d', 'f')),
 'f': (Point3(-55.994, 162.33, 10.026), ('e', 'g')),
 'g': (Point3(-84.554, 142.099, 0.027), ('f', 'h')),
 'h': (Point3(-92.215, 96.446, 0.027), ('g', 'i')),
 'i': (Point3(-63.168, 60.055, 0.027), ('h', 'j')),
 'j': (Point3(-37.637, 69.974, 0.027), ('i', 'k')),
 'k': (Point3(-3.018, 26.157, 0.027), ('j', 'l', 'm')),
 'l': (Point3(-0.711, 46.843, 0.027), 'k'),
 'm': (Point3(26.071, 46.401, 0.027), ('k', 'n')),
 'n': (Point3(30.87, 67.432, 0.027), ('m', 'o')),
 'o': (Point3(93.903, 90.685, 0.027), ('n', 'p')),
 'p': (Point3(88.129, 140.575, 0.027), ('o', 'q')),
 'q': (Point3(53.988, 158.232, 10.027), ('p', 'a'))}
__goofyWaypoints = (('f',
  'g',
  1,
  []), ('p',
  'q',
  1,
  []))
__goofySpeedwayPaths = {'a': (Point3(-9.0, -19.517, -0.323), ('b', 'k')),
 'b': (Point3(-30.047, -1.578, -0.373), ('a', 'c')),
 'c': (Point3(-10.367, 49.042, -0.373), ('b', 'd')),
 'd': (Point3(38.439, 44.348, -0.373), ('c', 'e')),
 'e': (Point3(25.527, -2.395, -0.373), ('d', 'f')),
 'f': (Point3(-4.043, -59.865, -0.003), ('e', 'g')),
 'g': (Point3(0.39, -99.475, -0.009), ('f', 'h')),
 'h': (Point3(21.147, -109.127, -0.013), ('g', 'i')),
 'i': (Point3(5.981, -147.606, -0.013), ('h', 'j')),
 'j': (Point3(-24.898, -120.618, -0.013), ('i', 'k')),
 'k': (Point3(-2.71, -90.315, -0.011), ('j', 'a'))}
__goofySpeedwayWaypoints = (('a',
  'k',
  1,
  []), ('k',
  'a',
  1,
  []))
__donaldPaths = {'a': (Point3(-94.883, -94.024, 0.025), 'b'),
 'b': (Point3(-13.962, -92.233, 0.025), ('a', 'h')),
 'c': (Point3(68.417, -91.929, 0.025), ('m', 'g')),
 'd': (Point3(68.745, 91.227, 0.025), ('k', 'i')),
 'e': (Point3(4.047, 94.26, 0.025), ('i', 'j')),
 'f': (Point3(-91.271, 90.987, 0.025), 'j'),
 'g': (Point3(43.824, -94.129, 0.025), ('c', 'h')),
 'h': (Point3(13.905, -91.334, 0.025), ('b', 'g')),
 'i': (Point3(43.062, 88.152, 0.025), ('d', 'e')),
 'j': (Point3(-48.96, 88.565, 0.025), ('e', 'f')),
 'k': (Point3(75.118, 52.84, -16.62), ('d', 'l')),
 'l': (Point3(44.677, 27.091, -15.385), ('k', 'm')),
 'm': (Point3(77.009, -16.022, -14.975), ('l', 'c'))}
__donaldWaypoints = (('d',
  'k',
  1,
  []),
 ('k',
  'l',
  1,
  []),
 ('l',
  'm',
  1,
  []),
 ('m',
  'c',
  1,
  []),
 ('b',
  'a',
  1,
  [Point3(-55.883, -89.0, 0.025)]))
__plutoPaths = {'a': (Point3(-110.0, -37.8, 8.6), ('b', 'c')),
 'b': (Point3(-11.9, -128.2, 6.2), ('a', 'c')),
 'c': (Point3(48.9, -14.4, 6.2), ('b', 'a', 'd')),
 'd': (Point3(0.25, 80.5, 6.2), ('c', 'e')),
 'e': (Point3(-83.3, 36.1, 6.2), ('d', 'a'))}
__plutoWaypoints = (('a',
  'b',
  1,
  [Point3(-90.4, -57.2, 3.0), Point3(-63.6, -79.8, 3.0), Point3(-50.1, -89.1, 6.2)]),
 ('c',
  'a',
  1,
  [Point3(-15.6, -25.6, 6.2),
   Point3(-37.5, -38.5, 3.0),
   Point3(-55.0, -55.0, 3.0),
   Point3(-85.0, -46.4, 3.0)]),
 ('d',
  'e',
  0,
  [Point3(-25.8, 60.0, 6.2), Point3(-61.9, 64.5, 6.2)]),
 ('e',
  'a',
  1,
  [Point3(-77.2, 28.5, 6.2), Point3(-76.4, 12.0, 3.0), Point3(-93.2, -21.2, 3.0)]))
__daisyPaths = {'a': (Point3(64.995, 169.665, 10.027), ('b', 'q')),
 'b': (Point3(48.893, 208.912, 10.027), ('a', 'c')),
 'c': (Point3(5.482, 210.479, 10.03), ('b', 'd')),
 'd': (Point3(-34.153, 203.284, 10.029), ('c', 'e')),
 'e': (Point3(-66.656, 174.334, 10.026), ('d', 'f')),
 'f': (Point3(-55.994, 162.33, 10.026), ('e', 'g')),
 'g': (Point3(-84.554, 142.099, 0.027), ('f', 'h')),
 'h': (Point3(-92.215, 96.446, 0.027), ('g', 'i')),
 'i': (Point3(-63.168, 60.055, 0.027), ('h', 'j')),
 'j': (Point3(-37.637, 69.974, 0.027), ('i', 'k')),
 'k': (Point3(-3.018, 26.157, 0.027), ('j', 'l', 'm')),
 'l': (Point3(-0.711, 46.843, 0.027), 'k'),
 'm': (Point3(26.071, 46.401, 0.027), ('k', 'n')),
 'n': (Point3(30.87, 67.432, 0.027), ('m', 'o')),
 'o': (Point3(93.903, 90.685, 0.027), ('n', 'p')),
 'p': (Point3(88.129, 140.575, 0.027), ('o', 'q')),
 'q': (Point3(53.988, 158.232, 10.027), ('p', 'a'))}
__daisyWaypoints = (('f',
  'g',
  1,
  []), ('p',
  'q',
  1,
  []))
__chipPaths = {'a': (Point3(50.004, 102.725, 0.6), ('b', 'k')),
 'b': (Point3(-29.552, 112.531, 0.6), ('c', 'a')),
 'c': (Point3(-51.941, 146.155, 0.025), ('d', 'b')),
 'd': (Point3(-212.334, -3.639, 0.025), ('e', 'c')),
 'e': (Point3(-143.466, -67.526, 0.025), ('f', 'd', 'i')),
 'f': (Point3(-107.556, -62.257, 0.025), ('g', 'e', 'j')),
 'g': (Point3(-43.103, -71.518, 0.2734), ('h', 'f', 'j')),
 'h': (Point3(-40.605, -125.124, 0.025), ('i', 'g')),
 'i': (Point3(-123.05, -124.542, 0.025), ('h', 'e')),
 'j': (Point3(-40.092, 2.784, 1.268), ('k',
        'b',
        'f',
        'g')),
 'k': (Point3(75.295, 26.715, 1.4), ('a', 'j'))}
__chipWaypoints = (('a',
  'b',
  1,
  []),
 ('a',
  'k',
  1,
  []),
 ('b',
  'c',
  1,
  []),
 ('b',
  'j',
  1,
  []),
 ('c',
  'd',
  1,
  []),
 ('d',
  'e',
  1,
  []),
 ('e',
  'f',
  1,
  []),
 ('e',
  'i',
  1,
  []),
 ('f',
  'g',
  1,
  []),
 ('f',
  'j',
  1,
  []),
 ('g',
  'h',
  1,
  []),
 ('g',
  'j',
  1,
  []),
 ('h',
  'i',
  1,
  []),
 ('j',
  'k',
  1,
  []))
DaleOrbitDistanceOverride = {('b', 'c'): 2.5,
 ('e', 'f'): 2.5}
startNode = 'a'

def getPaths(charName, location = 0):
    if charName == TTLocalizer.Mickey:
        return __mickeyPaths
    elif charName == TTLocalizer.VampireMickey:
        return __mickeyPaths
    elif charName == TTLocalizer.Minnie:
        return __minniePaths
    elif charName == TTLocalizer.WitchMinnie:
        return __minniePaths
    elif charName == TTLocalizer.Daisy or charName == TTLocalizer.SockHopDaisy:
        return __daisyPaths
    elif charName == TTLocalizer.Goofy:
        if location == 0:
            return __goofyPaths
        else:
            return __goofySpeedwayPaths
    elif charName == TTLocalizer.SuperGoofy:
        return __goofySpeedwayPaths
    elif charName == TTLocalizer.Donald or charName == TTLocalizer.FrankenDonald:
        return __donaldPaths
    elif charName == TTLocalizer.Pluto:
        return __plutoPaths
    elif charName == TTLocalizer.WesternPluto:
        return __plutoPaths
    elif charName == TTLocalizer.Chip or charName == TTLocalizer.PoliceChip:
        return __chipPaths
    elif charName == TTLocalizer.Dale or charName == TTLocalizer.JailbirdDale:
        return __chipPaths
    elif charName == TTLocalizer.DonaldDock:
        return {'a': (Point3(0, 0, 0), 'a')}


def __getWaypointList(paths):
    if paths == __mickeyPaths:
        return __mickeyWaypoints
    elif paths == __minniePaths:
        return __minnieWaypoints
    elif paths == __daisyPaths:
        return __daisyWaypoints
    elif paths == __goofyPaths:
        return __goofyWaypoints
    elif paths == __goofySpeedwayPaths:
        return __goofySpeedwayWaypoints
    elif paths == __donaldPaths:
        return __donaldWaypoints
    elif paths == __plutoPaths:
        return __plutoWaypoints
    elif paths == __chipPaths:
        return __chipWaypoints
    elif paths == __dalePaths:
        return __chipWaypoints


def getNodePos(node, paths):
    return paths[node][0]


def getAdjacentNodes(node, paths):
    return paths[node][1]


def getWayPoints(fromNode, toNode, paths, wpts = None):
    list = []
    if fromNode != toNode:
        if wpts == None:
            wpts = __getWaypointList(paths)
        for path in wpts:
            if path[0] == fromNode and path[1] == toNode:
                for point in path[3]:
                    list.append(Point3(point))

                break
            elif path[0] == toNode and path[1] == fromNode:
                for point in path[3]:
                    list = [Point3(point)] + list

                break

    return list


def getRaycastFlag(fromNode, toNode, paths):
    result = 0
    if fromNode != toNode:
        wpts = __getWaypointList(paths)
        for path in wpts:
            if path[0] == fromNode and path[1] == toNode:
                if path[2]:
                    result = 1
                    break
            elif path[0] == toNode and path[1] == fromNode:
                if path[2]:
                    result = 1
                    break

    return result


def getPointsFromTo(fromNode, toNode, paths):
    startPoint = Point3(getNodePos(fromNode, paths))
    endPoint = Point3(getNodePos(toNode, paths))
    return [startPoint] + getWayPoints(fromNode, toNode, paths) + [endPoint]


def getWalkDuration(fromNode, toNode, velocity, paths):
    posPoints = getPointsFromTo(fromNode, toNode, paths)
    duration = 0
    for pointIndex in range(len(posPoints) - 1):
        startPoint = posPoints[pointIndex]
        endPoint = posPoints[pointIndex + 1]
        distance = Vec3(endPoint - startPoint).length()
        duration += distance / velocity

    return duration


def getWalkDistance(fromNode, toNode, velocity, paths):
    posPoints = getPointsFromTo(fromNode, toNode, paths)
    retval = 0
    for pointIndex in range(len(posPoints) - 1):
        startPoint = posPoints[pointIndex]
        endPoint = posPoints[pointIndex + 1]
        distance = Vec3(endPoint - startPoint).length()
        retval += distance

    return retval
