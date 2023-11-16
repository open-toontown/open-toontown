from toontown.coghq.SpecImports import *

GlobalEntities = {
    1000: {
        'type': 'levelMgr',
        'name': 'LevelMgr',
        'comment': '',
        'parentEntId': 0,
        'cogLevel': 0,
        'farPlaneDistance': 1500,
        'modelFilename': 'phase_10/models/lawbotHQ/LawbotCourtroom3',
        'wantDoors': 1},
    1001: {
        'type': 'editMgr',
        'name': 'EditMgr',
        'parentEntId': 0,
        'insertEntity': None,
        'removeEntity': None,
        'requestNewEntity': None,
        'requestSave': None},
    0: {
        'type': 'zone',
        'name': 'UberZone',
        'comment': '',
        'parentEntId': 0,
        'scale': 1,
        'description': '',
        'visibility': []},
    100000: {
        'type': 'stomper',
        'name': '<unnamed>',
        'comment': '',
        'parentEntId': 0,
        'pos': Point3(3.80022, -32.6574, 70),
        'hpr': Vec3(0, 0, 0),
        'scale': Vec3(1, 1, 1),
        'animateShadow': 1,
        'crushCellId': None,
        'damage': 3,
        'headScale': Vec3(1, 1, 1),
        'modelPath': 0,
        'motion': 3,
        'period': 2.0,
        'phaseShift': 0.0,
        'range': 6,
        'removeCamBarrierCollisions': 0,
        'removeHeadFloor': 0,
        'shaftScale': Vec3(1, 1, 1),
        'soundLen': 0,
        'soundOn': 0,
        'soundPath': 0,
        'style': 'vertical',
        'switchId': 0,
        'wantShadow': 1,
        'wantSmoke': 1,
        'zOffset': 0}}
Scenario0 = {}
levelSpec = {
    'globalEntities': GlobalEntities,
    'scenarios': [
        Scenario0]}
