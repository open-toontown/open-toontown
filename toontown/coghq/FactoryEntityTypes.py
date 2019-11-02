from otp.level.EntityTypes import *

class FactoryLevelMgr(LevelMgr):
    type = 'levelMgr'
    attribs = (('cogLevel',
      0,
      'int',
      {'min': 0,
       'max': 11}), ('wantDoors', 1, 'bool'), ('farPlaneDistance', 1500, 'float'))


class BarrelBase(Nodepath):
    abstract = 1
    attribs = (('rewardPerGrab', 5, 'int'), ('rewardPerGrabMax', 0, 'int'))


class BeanBarrel(BarrelBase):
    type = 'beanBarrel'


class GagBarrel(BarrelBase):
    type = 'gagBarrel'
    attribs = (('gagLevel',
      0,
      'int',
      {'min': 0,
       'max': 5}), ('gagLevelMax',
      0,
      'int',
      {'min': 0,
       'max': 5}), ('gagTrack',
      0,
      'choice',
      {'choiceSet': ('heal', 'trap', 'lure', 'sound', 'throw', 'squirt', 'drop', 'random'),
       'valueDict': {'heal': 0,
                     'trap': 1,
                     'lure': 2,
                     'sound': 3,
                     'throw': 4,
                     'squirt': 5,
                     'drop': 6,
                     'random': 'random'}}))


class HealBarrel(BarrelBase):
    type = 'healBarrel'


class Switch(Nodepath):
    abstract = 1
    output = 'bool'
    attribs = (('isOnEvent',
      0,
      'entId',
      {'output': 'bool'}), ('isOn', 0, 'bool'), ('secondsOn', 1, 'float'))


class Button(Switch):
    type = 'button'
    attribs = (('scale', Vec3(3), 'scale'), ('color', Vec4(1, 1, 1, 1), 'color'))


class Trigger(Switch):
    type = 'trigger'
    attribs = (('scale', Vec3(10), 'scale'), ('triggerName', ''))


class ConveyorBelt(Nodepath):
    type = 'conveyorBelt'
    attribs = (('speed', 1.0, 'float'),
     ('length', 1.0, 'float'),
     ('widthScale', 1.0, 'float'),
     ('treadLength', 10.0, 'float'),
     ('treadModelPath', 'phase_9/models/cogHQ/platform1', 'bamfilename'),
     ('floorName', 'platformcollision'))


class Door(Nodepath):
    type = 'door'
    output = 'bool'
    attribs = (('color', Vec4(1, 1, 1, 1), 'color'),
     ('isVisBlocker', 1, 'bool'),
     ('unlock0Event',
      0,
      'entId',
      {'output': 'bool'}),
     ('unlock1Event',
      0,
      'entId',
      {'output': 'bool'}),
     ('unlock2Event',
      0,
      'entId',
      {'output': 'bool'}),
     ('unlock3Event',
      0,
      'entId',
      {'output': 'bool'}),
     ('isOpenEvent',
      0,
      'entId',
      {'output': 'bool'}),
     ('isLock0Unlocked', 1, 'bool'),
     ('isLock1Unlocked', 1, 'bool'),
     ('isLock2Unlocked', 1, 'bool'),
     ('isLock3Unlocked', 1, 'bool'),
     ('isOpen', 0, 'bool'),
     ('secondsOpen', 1, 'float'))


class Grid(Nodepath):
    type = 'grid'
    blockAttribs = ('hpr',)
    attribs = (('cellSize', 3, 'float'), ('numCol', 3, 'int'), ('numRow', 3, 'int'))


class Crushable(Entity):
    abstract = 1
    attribs = (('pos', Point3(0, 0, 0), 'pos'),
     ('hpr', Vec3(0, 0, 0), 'hpr'),
     ('crushCellId',
      None,
      'entId',
      {'type': 'crusherCell'}),
     ('gridId',
      None,
      'entId',
      {'type': 'grid'}))


class Crusher(Nodepath):
    abstract = 1
    attribs = (('crushCellId',
      None,
      'entId',
      {'type': 'crusherCell'}),)


class Crate(Crushable):
    type = 'crate'
    blockAttribs = ('hpr',)
    attribs = (('modelType',
      0,
      'int',
      {'min': 0,
       'max': 1}), ('scale', 0.92, 'float'), ('pushable', 1, 'bool'))


class Goon(Crushable):
    type = 'goon'
    attribs = (('goonType',
      'pg',
      'choice',
      {'choiceSet': ['pg', 'sg']}),
     ('strength',
      5,
      'int',
      {'min': 0,
       'max': 105}),
     ('velocity',
      4,
      'float',
      {'min': 0,
       'max': 10}),
     ('attackRadius',
      15,
      'float',
      {'min': 1,
       'max': 20}),
     ('scale', 1.5, 'float'),
     ('hFov',
      70,
      'float',
      {'min': 0,
       'max': 179}))


class GridGoon(Goon):
    type = 'gridGoon'
    attribs = ()


class GoonClipPlane(Nodepath):
    type = 'goonClipPlane'
    attribs = (('goonId',
      None,
      'entId',
      {'type': 'goon'}),)


class ActiveCell(Nodepath):
    type = 'activeCell'
    attribs = (('row', 0, 'int'), ('col', 0, 'int'), ('gridId',
      None,
      'entId',
      {'type': 'grid'}))


class CrusherCell(ActiveCell):
    type = 'crusherCell'
    attribs = ()


class DirectionalCell(ActiveCell):
    type = 'directionalCell'
    attribs = (('dir',
      [0, 0],
      'choice',
      {'choiceSet': ['l',
                     'r',
                     'up',
                     'dn'],
       'valueDict': {'l': [-1, 0],
                     'r': [1, 0],
                     'up': [0, 1],
                     'dn': [0, -1]}}),)


class GolfGreenGame(Nodepath):
    type = 'golfGreenGame'
    output = 'bool'
    attribs = (('pos', Point3(0, 0, 0), 'pos'),
     ('hpr', Vec3(0, 0, 0), 'hpr'),
     ('cellId', 0, 'int'),
     ('switchId',
      0,
      'entId',
      {'type': 'button'}),
     ('timeToPlay', 120, 'int'),
     ('puzzleBase', 4, 'int'),
     ('puzzlePerPlayer', 1, 'int'))


class LaserField(Nodepath):
    type = 'laserField'
    output = 'bool'
    attribs = (('laserFactor', 3, 'float'),
     ('gridScaleX', 32.0, 'float'),
     ('gridScaleY', 32.0, 'float'),
     ('projector', Point3(6, 6, 25), 'pos'),
     ('modelPath',
      0,
      'choice',
      {'choiceSet': ['square'],
       'valueDict': {'square': 0}}),
     ('pos', Point3(0, 0, 0), 'pos'),
     ('hpr', Vec3(0, 0, 0), 'hpr'),
     ('cellId', 0, 'int'),
     ('switchId',
      0,
      'entId',
      {'type': 'button'}),
     ('gridGame',
      'Random',
      'choice',
      {'choiceSet': ['MineSweeper',
                     'Roll',
                     'Avoid',
                     'Random']}))


class SecurityCamera(Nodepath):
    type = 'securityCamera'
    attribs = (('damPow', 3, 'int'),
     ('radius', 5, 'float'),
     ('accel', 1, 'float'),
     ('maxVel', 5, 'float'),
     ('projector', Point3(6, 6, 25), 'pos'),
     ('modelPath',
      0,
      'choice',
      {'choiceSet': ['square'],
       'valueDict': {'square': 0}}),
     ('hideModel', 0, 'bool'),
     ('pos', Point3(0, 0, 0), 'pos'),
     ('hpr', Vec3(0, 0, 0), 'hpr'),
     ('switchId',
      0,
      'entId',
      {'type': 'button'}),
     ('trackTarget1',
      0,
      'entId',
      {'type': 'button'}),
     ('trackTarget2',
      0,
      'entId',
      {'type': 'button'}),
     ('trackTarget3',
      0,
      'entId',
      {'type': 'button'}))


class ElevatorMarker(Nodepath):
    type = 'elevatorMarker'
    attribs = (('modelPath',
      0,
      'choice',
      {'choiceSet': ['square'],
       'valueDict': {'square': 0}}), ('pos', Point3(0, 0, 0), 'pos'), ('hpr', Vec3(0, 0, 0), 'hpr'))


class Lift(Nodepath):
    type = 'lift'
    attribs = (('duration', 1, 'float'),
     ('startPos', Point3(0, 0, 0), 'pos'),
     ('endPos', Point3(0, 0, 0), 'pos'),
     ('modelPath', 'phase_9/models/cogHQ/Elevator.bam', 'bamfilename'),
     ('floorName', 'elevator_floor', 'string'),
     ('modelScale', Vec3(1), 'scale'),
     ('startGuardName', '', 'string'),
     ('endGuardName', '', 'string'),
     ('startBoardSides', ['front',
       'back',
       'left',
       'right']),
     ('endBoardSides', ['front',
       'back',
       'left',
       'right']),
     ('moveDelay',
      1,
      'float',
      {'min': 0}),
     ('autoMoveDelay',
      5,
      'float',
      {'min': 0}))


class Mover(Nodepath):
    type = 'mover'
    attribs = (('modelPath',
      0,
      'choice',
      {'choiceSet': ['square'],
       'valueDict': {'square': 0}}),
     ('pos', Point3(0, 0, 0), 'pos'),
     ('hpr', Vec3(0, 0, 0), 'hpr'),
     ('switchId',
      0,
      'entId',
      {'type': 'button'}),
     ('entity2Move',
      0,
      'entId',
      {'type': 'button'}),
     ('moveTarget',
      0,
      'entId',
      {'type': 'button'}),
     ('pos0Move', 2, 'float'),
     ('pos0Wait', 2, 'float'),
     ('pos1Move', 2, 'float'),
     ('pos1Wait', 2, 'float'),
     ('startOn', 0, 'bool'),
     ('cycleType',
      'return',
      'choice',
      {'choiceSet': ['return',
                     'linear',
                     'loop',
                     'oneWay']}))


class Platform(Nodepath):
    type = 'platform'
    attribs = (('modelPath', 'phase_9/models/cogHQ/platform1', 'bamfilename'),
     ('modelScale', Vec3(1, 1, 1), 'scale'),
     ('floorName', 'platformcollision', 'string'),
     ('offset', Point3(0, 0, 0), 'pos'),
     ('period', 2, 'float'),
     ('waitPercent',
      0.1,
      'float',
      {'min': 0,
       'max': 1}),
     ('phaseShift',
      0.0,
      'float',
      {'min': 0,
       'max': 1}),
     ('motion',
      'noBlend',
      'choice',
      {'choiceSet': ['noBlend',
                     'easeInOut',
                     'easeIn',
                     'easeOut']}))


class SinkingPlatform(Nodepath):
    type = 'sinkingPlatform'
    attribs = (('verticalRange', 1, 'float'),
     ('sinkDuration', 1, 'float'),
     ('pauseBeforeRise', 1, 'float'),
     ('riseDuration', 1, 'float'))


class Stomper(Crusher):
    type = 'stomper'
    attribs = (('damage', 3, 'int'),
     ('style',
      'vertical',
      'choice',
      {'choiceSet': ['horizontal', 'vertical']}),
     ('period', 2.0, 'float'),
     ('phaseShift',
      0.0,
      'float',
      {'min': 0,
       'max': 1}),
     ('range', 6, 'float'),
     ('motion',
      3,
      'choice',
      {'choiceSet': ['linear',
                     'sinus',
                     'half sinus',
                     'slow fast',
                     'crush',
                     'switched'],
       'valueDict': {'linear': 0,
                     'sinus': 1,
                     'half sinus': 2,
                     'slow fast': 3,
                     'crush': 4,
                     'switched': 5}}),
     ('headScale', Vec3(1, 1, 1), 'scale'),
     ('shaftScale', Vec3(1, 1, 1), 'scale'),
     ('wantSmoke', 1, 'bool'),
     ('wantShadow', 1, 'bool'),
     ('animateShadow', 1, 'bool'),
     ('soundOn', 0, 'bool'),
     ('soundPath',
      0,
      'choice',
      {'choiceSet': ['small', 'medium', 'large'],
       'valueDict': {'small': 0,
                     'medium': 1,
                     'large': 2}}),
     ('soundLen', 0, 'float'),
     ('zOffset', 0, 'float'),
     ('switchId',
      0,
      'entId',
      {'type': 'button'}),
     ('modelPath',
      0,
      'choice',
      {'choiceSet': ['square'],
       'valueDict': {'square': 0}}),
     ('cogStyle',
      0,
      'choice',
      {'choiceSet': ['default', 'lawbot'],
       'valueDict': {'default': 0,
                     'lawbot': 1}}),
     ('removeHeadFloor', 0, 'bool'),
     ('removeCamBarrierCollisions', 0, 'bool'))


class StomperPair(Nodepath):
    type = 'stomperPair'
    attribs = (('headScale', Vec3(1, 1, 1), 'scale'),
     ('motion',
      3,
      'choice',
      {'choiceSet': ['linear',
                     'sinus',
                     'half sinus',
                     'slow fast',
                     'crush',
                     'switched'],
       'valueDict': {'linear': 0,
                     'sinus': 1,
                     'half sinus': 2,
                     'slow fast': 3,
                     'crush': 4,
                     'switched': 5}}),
     ('period', 2.0, 'float'),
     ('phaseShift',
      0.0,
      'float',
      {'min': 0,
       'max': 1}),
     ('range', 6, 'float'),
     ('shaftScale', Vec3(1, 1, 1), 'scale'),
     ('soundLen', 0, 'float'),
     ('soundOn', 0, 'bool'),
     ('stomperIds',
      [],
      'entId',
      {'type': 'stomper',
       'num': 2}),
     ('style',
      'horizontal',
      'choice',
      {'choiceSet': ['horizontal', 'vertical']}))


class Gear(Nodepath):
    type = 'gear'
    attribs = (('modelType',
      'factory',
      'choice',
      {'choiceSet': ['factory', 'mint']}),
     ('gearScale', 1, 'float'),
     ('orientation',
      'horizontal',
      'choice',
      {'choiceSet': ['horizontal', 'vertical']}),
     ('degreesPerSec', 0, 'float'),
     ('phaseShift',
      0,
      'float',
      {'min': 0,
       'max': 1}))


class BattleBlocker(Nodepath):
    type = 'battleBlocker'
    attribs = (('radius', 10, 'float'), ('cellId', 0, 'int'))


class PaintMixer(Platform):
    type = 'paintMixer'
    attribs = (('modelPath', 'phase_9/models/cogHQ/PaintMixer', 'const'), ('floorName', 'PaintMixerFloorCollision', 'const'), ('shaftScale', 1, 'float'))


class MintProduct(Nodepath):
    type = 'mintProduct'
    attribs = (('mintId',
      12500,
      'choice',
      {'choiceSet': ('coin', 'dollar', 'bullion'),
       'valueDict': {'coin': 12500,
                     'dollar': 12600,
                     'bullion': 12700}}),)


class MintProductPallet(Nodepath):
    type = 'mintProductPallet'
    attribs = (('mintId',
      12500,
      'choice',
      {'choiceSet': ('coin', 'dollar', 'bullion'),
       'valueDict': {'coin': 12500,
                     'dollar': 12600,
                     'bullion': 12700}}),)


class MintShelf(Nodepath):
    type = 'mintShelf'
    attribs = (('mintId',
      12500,
      'choice',
      {'choiceSet': ('coin', 'dollar', 'bullion'),
       'valueDict': {'coin': 12500,
                     'dollar': 12600,
                     'bullion': 12700}}),)


class PathMaster(Nodepath):
    type = 'pathMaster'
    attribs = (('pathIndex', 0, 'int'),
     ('pathScale', 1.0, 'float'),
     ('pathTarget0',
      0,
      'entId',
      {'type': 'button'}),
     ('pathTarget1',
      0,
      'entId',
      {'type': 'button'}),
     ('pathTarget2',
      0,
      'entId',
      {'type': 'button'}),
     ('pathTarget3',
      0,
      'entId',
      {'type': 'button'}),
     ('pathTarget4',
      0,
      'entId',
      {'type': 'button'}),
     ('pathTarget5',
      0,
      'entId',
      {'type': 'button'}),
     ('pathTarget6',
      0,
      'entId',
      {'type': 'button'}),
     ('pathTarget7',
      0,
      'entId',
      {'type': 'button'}))


class Rendering(Nodepath):
    type = 'rendering'
    attribs = (('pos', Point3(0, 0, 0), 'pos'),
     ('hpr', Vec3(0, 0, 0), 'hpr'),
     ('colorR', 1.0, 'float'),
     ('colorG', 1.0, 'float'),
     ('colorB', 1.0, 'float'),
     ('colorA', 1.0, 'float'),
     ('blending',
      'Normal',
      'choice',
      {'choiceSet': ['Normal', 'Additive', 'Alpha']}),
     ('fogOn', 0, 'bool'),
     ('renderBin',
      'default',
      'choice',
      {'choiceSet': ['default', 'fixed', 'transparent']}))


class MoleField(Nodepath):
    type = 'moleField'
    attribs = (('numSquaresX', 5, 'int'),
     ('numSquaresY', 5, 'int'),
     ('spacingX', 5.0, 'float'),
     ('spacingY', 5.0, 'float'),
     ('timeToPlay', 60, 'int'),
     ('molesBase', 4, 'int'),
     ('molesPerPlayer', 1, 'int'))


class Maze(Nodepath):
    type = 'maze'
    attribs = (('numSections', 4, 'int'),)
