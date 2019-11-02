from toontown.toonbase import TTLocalizer
from direct.directnotify import DirectNotifyGlobal
import random
FLOWERS_PER_BONUS = 10
ACCELERATOR_USED_FROM_SHTIKER_BOOK = True
COLLECT_NO_UPDATE = 0
COLLECT_NEW_ENTRY = 1
gardenNotify = DirectNotifyGlobal.directNotify.newCategory('GardenGlobals')
FlowerItem = 2
FlowerItemNewEntry = 9
INVALID_TYPE = -1
GAG_TREE_TYPE = 0
FLOWER_TYPE = 1
STATUARY_TYPE = 2
WATERING_CAN_SMALL = 0
WATERING_CAN_MEDIUM = 1
WATERING_CAN_LARGE = 2
WATERING_CAN_HUGE = 3
MAX_WATERING_CANS = 4
WateringCanAttributes = {0: {'numBoxes': 2,
     'skillPts': 100,
     'name': TTLocalizer.WateringCanSmall},
 1: {'numBoxes': 2,
     'skillPts': 200,
     'name': TTLocalizer.WateringCanMedium},
 2: {'numBoxes': 2,
     'skillPts': 400,
     'name': TTLocalizer.WateringCanLarge},
 3: {'numBoxes': 2,
     'skillPts': 1000,
     'name': TTLocalizer.WateringCanHuge}}
WateringMult = 2

def getWateringCanPower(wateringCan, wateringCanSkill):
    numBoxes = 0
    for curWateringCan in range(wateringCan + 1):
        wateringCanAttrib = WateringCanAttributes[curWateringCan]
        curBoxes = wateringCanAttrib['numBoxes']
        skill = wateringCanAttrib['skillPts']
        if wateringCanSkill >= skill:
            if curWateringCan == wateringCan:
                gardenNotify.warning("this shouldn't happen wateringCanSkill %d >= skill %d" % (wateringCanSkill, skill))
            wateringCanSkill = skill - 1
        if curWateringCan == wateringCan:
            skillPtPerBox = skill / curBoxes
            numBoxes += 1 + int(wateringCanSkill) / int(skillPtPerBox)
        else:
            numBoxes += curBoxes

    return numBoxes * WateringMult


def getMaxWateringCanPower():
    retval = 0
    for wateringCanAttrib in WateringCanAttributes.values():
        retval += wateringCanAttrib['numBoxes']

    return retval * WateringMult


FlowerColors = [(0.804, 0.2, 0.2),
 (0.922, 0.463, 0.0),
 (0.5, 0.2, 1.0),
 (0.4, 0.4, 1.0),
 (0.953, 0.545, 0.757),
 (0.992, 0.843, 0.392),
 (1.0, 1.0, 1.0),
 (0.5, 0.8, 0.5)]
FLOWER_RED = 0
FLOWER_ORANGE = 1
FLOWER_VIOLET = 2
FLOWER_BLUE = 3
FLOWER_PINK = 4
FLOWER_YELLOW = 5
FLOWER_WHITE = 6
FLOWER_GREEN = 7
ToonStatuaryTypeIndices = xrange(205, 209)
ChangingStatuaryTypeIndices = xrange(230, 232)
AnimatedStatuaryTypeIndices = xrange(234, 238)
PlantAttributes = {49: {'name': TTLocalizer.FlowerSpeciesNames[49],
      'plantType': FLOWER_TYPE,
      'growthThresholds': (1, 1, 1),
      'maxWaterLevel': getMaxWateringCanPower(),
      'minWaterLevel': -2,
      'seedlingModel': 'phase_5.5/models/estate/seedling.bam',
      'establishedModel': 'phase_5.5/models/estate/daisy.bam',
      'fullGrownModel': 'phase_5.5/models/estate/daisy.bam',
      'photoPos': (0.0, -0.35, -0.361882),
      'photoScale': 1,
      'photoHeading': 0,
      'photoPitch': 35,
      'varieties': ((10, FLOWER_YELLOW, 1),
                    (11, FLOWER_PINK, 2),
                    (12, FLOWER_WHITE, 3),
                    (13, FLOWER_RED, 4),
                    (14, FLOWER_ORANGE, 5),
                    (15, FLOWER_BLUE, 6),
                    (16, FLOWER_GREEN, 7),
                    (17, FLOWER_VIOLET, 8))},
 50: {'name': TTLocalizer.FlowerSpeciesNames[50],
      'plantType': FLOWER_TYPE,
      'growthThresholds': (1, 1, 1),
      'maxWaterLevel': getMaxWateringCanPower(),
      'minWaterLevel': -2,
      'seedlingModel': 'phase_5.5/models/estate/seedling.bam',
      'establishedModel': 'phase_5.5/models/estate/tulip.bam',
      'fullGrownModel': 'phase_5.5/models/estate/tulip.bam',
      'photoPos': (0.0, -0.35, -0.35),
      'photoScale': 1,
      'photoHeading': 0,
      'photoPitch': 35,
      'varieties': ((20, FLOWER_VIOLET, 5), (21, FLOWER_RED, 6), (22, FLOWER_YELLOW, 8))},
 51: {'name': TTLocalizer.FlowerSpeciesNames[51],
      'plantType': FLOWER_TYPE,
      'growthThresholds': (1, 1, 1),
      'maxWaterLevel': getMaxWateringCanPower(),
      'minWaterLevel': -2,
      'seedlingModel': 'phase_5.5/models/estate/seedling.bam',
      'establishedModel': 'phase_5.5/models/estate/carnation.bam',
      'fullGrownModel': 'phase_5.5/models/estate/carnation.bam',
      'photoPos': (0.0, -0.35, -0.4),
      'photoScale': 1,
      'photoHeading': 0,
      'photoPitch': 35,
      'varieties': ((30, FLOWER_PINK, 1),
                    (31, FLOWER_YELLOW, 2),
                    (32, FLOWER_RED, 3),
                    (33, FLOWER_WHITE, 5),
                    (34, FLOWER_GREEN, 7))},
 52: {'name': TTLocalizer.FlowerSpeciesNames[52],
      'plantType': FLOWER_TYPE,
      'growthThresholds': (1, 1, 1),
      'maxWaterLevel': getMaxWateringCanPower(),
      'minWaterLevel': -2,
      'seedlingModel': 'phase_5.5/models/estate/seedling.bam',
      'establishedModel': 'phase_5.5/models/estate/lily.bam',
      'fullGrownModel': 'phase_5.5/models/estate/lily.bam',
      'photoPos': (0.0174745, -0.05, -0.670513),
      'photoScale': 1,
      'photoHeading': 0,
      'photoPitch': 35,
      'varieties': ((40, FLOWER_WHITE, 1),
                    (41, FLOWER_GREEN, 2),
                    (42, FLOWER_ORANGE, 3),
                    (43, FLOWER_PINK, 4),
                    (44, FLOWER_RED, 5),
                    (45, FLOWER_VIOLET, 6),
                    (46, FLOWER_BLUE, 7),
                    (47, FLOWER_YELLOW, 8))},
 53: {'name': TTLocalizer.FlowerSpeciesNames[53],
      'plantType': FLOWER_TYPE,
      'growthThresholds': (1, 1, 1),
      'maxWaterLevel': getMaxWateringCanPower(),
      'minWaterLevel': -2,
      'seedlingModel': 'phase_5.5/models/estate/seedling.bam',
      'establishedModel': 'phase_5.5/models/estate/narcissi.bam',
      'fullGrownModel': 'phase_5.5/models/estate/narcissi.bam',
      'photoPos': (-0.0403175, 0.060933, -0.548368),
      'photoScale': 1,
      'photoHeading': 20,
      'photoPitch': 0,
      'varieties': ((50, FLOWER_GREEN, 1),
                    (51, FLOWER_WHITE, 2),
                    (52, FLOWER_YELLOW, 4),
                    (53, FLOWER_PINK, 5))},
 54: {'name': TTLocalizer.FlowerSpeciesNames[54],
      'plantType': FLOWER_TYPE,
      'growthThresholds': (1, 1, 1),
      'maxWaterLevel': getMaxWateringCanPower(),
      'minWaterLevel': -2,
      'seedlingModel': 'phase_5.5/models/estate/seedling.bam',
      'establishedModel': 'phase_5.5/models/estate/pansy.bam',
      'fullGrownModel': 'phase_5.5/models/estate/pansy.bam',
      'photoScale': 2.5,
      'photoHeading': 0,
      'photoPitch': 0,
      'varieties': ((60, FLOWER_ORANGE, 1),
                    (61, FLOWER_WHITE, 2),
                    (62, FLOWER_RED, 3),
                    (63, FLOWER_YELLOW, 4),
                    (64, FLOWER_PINK, 6))},
 55: {'name': TTLocalizer.FlowerSpeciesNames[55],
      'plantType': FLOWER_TYPE,
      'growthThresholds': (1, 1, 1),
      'maxWaterLevel': getMaxWateringCanPower(),
      'minWaterLevel': -2,
      'seedlingModel': 'phase_5.5/models/estate/seedling.bam',
      'establishedModel': 'phase_5.5/models/estate/petunia.bam',
      'fullGrownModel': 'phase_5.5/models/estate/petunia.bam',
      'photoPos': (0.02, -0.0324585, -0.167735),
      'photoScale': 1.5,
      'photoHeading': -20,
      'photoPitch': 35,
      'varieties': ((70, FLOWER_BLUE, 7), (71, FLOWER_PINK, 8))},
 56: {'name': TTLocalizer.FlowerSpeciesNames[56],
      'plantType': FLOWER_TYPE,
      'growthThresholds': (1, 1, 1),
      'maxWaterLevel': getMaxWateringCanPower(),
      'minWaterLevel': -1,
      'seedlingModel': 'phase_5.5/models/estate/seedling.bam',
      'establishedModel': 'phase_5.5/models/estate/rose.bam',
      'fullGrownModel': 'phase_5.5/models/estate/rose.bam',
      'photoPos': (0.04396, 0.124797, -0.877291),
      'photoScale': 1,
      'photoHeading': 0,
      'photoPitch': 35,
      'varieties': ((0, FLOWER_RED, 3),
                    (1, FLOWER_YELLOW, 4),
                    (2, FLOWER_PINK, 6),
                    (3, FLOWER_WHITE, 7),
                    (4, FLOWER_BLUE, 8))},
 200: {'name': TTLocalizer.StatuaryDonald,
       'plantType': STATUARY_TYPE,
       'model': 'phase_5.5/models/estate/garden_donald.bam',
       'worldScale': 0.05,
       'varieties': ((1000, 1, 0),),
       'pinballScore': (10, 1)},
 201: {'name': TTLocalizer.StatuaryMickey1,
       'plantType': STATUARY_TYPE,
       'model': 'phase_5.5/models/estate/garden_mickey_flute',
       'worldScale': 0.05,
       'varieties': ((1001, 1, 0),),
       'pinballScore': (50, 1)},
 202: {'name': TTLocalizer.StatuaryGardenAccelerator,
       'plantType': STATUARY_TYPE,
       'model': 'phase_4/models/props/goofy_statue',
       'varieties': ((1002, 1, 0),)},
 203: {'name': TTLocalizer.StatuaryMinnie,
       'plantType': STATUARY_TYPE,
       'model': 'phase_5.5/models/estate/garden_minnie',
       'worldScale': 0.05,
       'varieties': ((1003, 1, 0),),
       'pinballScore': (150, 1)},
 204: {'name': TTLocalizer.StatuaryMickey2,
       'plantType': STATUARY_TYPE,
       'model': 'phase_5.5/models/estate/garden_mickey_shovel',
       'worldScale': 0.05,
       'varieties': ((1004, 1, 0),),
       'pinballScore': (250, 1)},
 205: {'name': TTLocalizer.StatuaryToonWave,
       'plantType': STATUARY_TYPE,
       'model': 'phase_5.5/models/estate/garden_pedestal',
       'worldScale': 0.05,
       'varieties': ((1005, 1, 0),),
       'pinballScore': (500, 1)},
 206: {'name': TTLocalizer.StatuaryToonVictory,
       'plantType': STATUARY_TYPE,
       'model': 'phase_5.5/models/estate/garden_pedestal',
       'worldScale': 0.05,
       'varieties': ((1006, 1, 0),),
       'pinballScore': (500, 1)},
 207: {'name': TTLocalizer.StatuaryToonCrossedArms,
       'plantType': STATUARY_TYPE,
       'model': 'phase_5.5/models/estate/garden_pedestal',
       'worldScale': 0.05,
       'varieties': ((1007, 1, 0),),
       'pinballScore': (500, 1)},
 208: {'name': TTLocalizer.StatuaryToonThinking,
       'plantType': STATUARY_TYPE,
       'model': 'phase_5.5/models/estate/garden_pedestal',
       'worldScale': 0.05,
       'varieties': ((1008, 1, 0),),
       'pinballScore': (500, 1)},
 230: {'name': TTLocalizer.StatuaryMeltingSnowman,
       'plantType': STATUARY_TYPE,
       'model': 'phase_5.5/models/estate/tt_m_prp_ext_snowman',
       'worldScale': 1.0,
       'varieties': ((1030, 1, 0),),
       'pinballScore': (500, 1),
       'growthThresholds': (1, 2)},
 231: {'name': TTLocalizer.StatuaryMeltingSnowDoodle,
       'plantType': STATUARY_TYPE,
       'model': 'phase_5.5/models/estate/tt_m_prp_ext_snowDoodle',
       'worldScale': 1.0,
       'varieties': ((1031, 1, 0),),
       'pinballScore': (500, 1),
       'growthThresholds': (1, 2)},
 234: {'name': TTLocalizer.AnimatedStatuaryFlappyCog,
       'plantType': STATUARY_TYPE,
       'model': 'phase_5.5/models/estate/tt_a_ara_pty_tubeCogVictory_',
       'anims': ['default', 'wave'],
       'worldScale': 0.5,
       'varieties': ((1035, 1, 0),),
       'pinballScore': (500, 1)},
 254: {'name': 'reserved tag',
       'plantType': STATUARY_TYPE,
       'model': 'phase_5.5/models/estate/garden_minnie',
       'worldScale': 0.05,
       'varieties': ((2001, 1, 0),),
       'pinballScore': (15, 1)},
 255: {'name': 'reserved tag',
       'plantType': STATUARY_TYPE,
       'model': 'phase_5.5/models/estate/garden_minnie',
       'worldScale': 0.05,
       'varieties': ((2002, 1, 0),),
       'pinballScore': (15, 1)}}
if ACCELERATOR_USED_FROM_SHTIKER_BOOK:
    del PlantAttributes[202]

def getTreeTrackAndLevel(typeIndex):
    track = typeIndex / 7
    level = typeIndex % 7
    return (track, level)


def getTreeTypeIndex(track, level):
    return track * 7 + level


NUM_GAGS = 7 * 7
for i in range(NUM_GAGS):
    track, level = getTreeTrackAndLevel(i)
    if level <= 6:
        name = TTLocalizer.BattleGlobalAvPropStrings[track][level] + TTLocalizer.GardenGagTree
    else:
        name = TTLocalizer.GardenUberGag
    attr = {'name': name,
     'plantType': GAG_TREE_TYPE,
     'growthThresholds': (level + 1, (level + 1) * 2, (level + 1) * 3),
     'maxWaterLevel': getMaxWateringCanPower(),
     'minWaterLevel': -1,
     'maxFruit': 9,
     'filename': 'phase_5.5/models/estate/gag_tree_stages.bam',
     'seedlingModel': 'gag_tree_small',
     'establishedModel': 'gag_tree_med',
     'fullGrownModel': 'gag_tree_large',
     'varieties': ((),)}
    PlantAttributes[i] = attr

BeanColors = [(255, 0, 0),
 (0, 255, 0),
 (255, 165, 0),
 (148, 0, 211),
 (0, 0, 255),
 (255, 192, 203),
 (255, 255, 0),
 (0, 255, 255),
 (192, 192, 192)]
BeanColorLetters = ['R',
 'G',
 'O',
 'V',
 'B',
 'P',
 'Y',
 'C',
 'S']
Recipes = {0: {'beans': 'RRR',
     'special': -1},
 1: {'beans': 'RYOY',
     'special': -1},
 2: {'beans': 'RPOROP',
     'special': -1},
 3: {'beans': 'RCOPVCC',
     'special': -1},
 4: {'beans': 'RBVVBBPB',
     'special': -1},
 10: {'beans': 'Y',
      'special': -1},
 11: {'beans': 'YR',
      'special': -1},
 12: {'beans': 'YRG',
      'special': -1},
 13: {'beans': 'YRCO',
      'special': -1},
 14: {'beans': 'YROOO',
      'special': -1},
 15: {'beans': 'YBCVBB',
      'special': -1},
 16: {'beans': 'YGROGGG',
      'special': -1},
 17: {'beans': 'YBVCVROV',
      'special': -1},
 20: {'beans': 'VRBVV',
      'special': -1},
 21: {'beans': 'VRRRVV',
      'special': -1},
 22: {'beans': 'VYYVYOVY',
      'special': -1},
 30: {'beans': 'P',
      'special': -1},
 31: {'beans': 'PY',
      'special': -1},
 32: {'beans': 'PRR',
      'special': -1},
 33: {'beans': 'PRGBR',
      'special': -1},
 34: {'beans': 'PGGGGYG',
      'special': -1},
 40: {'beans': 'C',
      'special': -1},
 41: {'beans': 'CG',
      'special': -1},
 42: {'beans': 'COO',
      'special': -1},
 43: {'beans': 'COOP',
      'special': -1},
 44: {'beans': 'CRRRR',
      'special': -1},
 45: {'beans': 'CRVVVV',
      'special': -1},
 46: {'beans': 'CVCBCBB',
      'special': -1},
 47: {'beans': 'CBYYCBYY',
      'special': -1},
 50: {'beans': 'G',
      'special': -1},
 51: {'beans': 'GC',
      'special': -1},
 52: {'beans': 'GPYY',
      'special': -1},
 53: {'beans': 'GPBPP',
      'special': -1},
 60: {'beans': 'O',
      'special': -1},
 61: {'beans': 'OC',
      'special': -1},
 62: {'beans': 'ORR',
      'special': -1},
 63: {'beans': 'OYYR',
      'special': -1},
 64: {'beans': 'OPPOBP',
      'special': -1},
 70: {'beans': 'BVBVCBB',
      'special': -1},
 71: {'beans': 'BPPBROYY',
      'special': -1},
 1000: {'beans': 'GG',
        'special': 100},
 1001: {'beans': 'SSSS',
        'special': 101},
 1002: {'beans': 'S',
        'special': 102},
 1003: {'beans': 'VVVVVV',
        'special': 103},
 1004: {'beans': 'OOOOOOOO',
        'special': 104},
 1005: {'beans': 'RRRRRRRR',
        'special': 105},
 1006: {'beans': 'GGGGGGGG',
        'special': 106},
 1007: {'beans': 'BBBBBBBB',
        'special': 107},
 1008: {'beans': 'SSSSSSSS',
        'special': 108},
 1030: {'beans': 'S',
        'special': 130},
 1031: {'beans': 'S',
        'special': 131},
 1035: {'beans': 'S',
        'special': 135},
 2001: {'beans': 'ZVOVOVO',
        'special': -1},
 2002: {'beans': 'ZOVOVOV',
        'special': -1}}

def getRecipeKey(beans, special):
    testDict = {'beans': beans,
     'special': special}
    for key in Recipes.keys():
        recipe = Recipes[key]
        if testDict == recipe:
            return key

    return -1


def getRecipeKeyUsingSpecial(special):
    for key in Recipes.keys():
        recipe = Recipes[key]
        if recipe['special'] == special:
            return key

    return -1


SHOVEL_TIN = 0
SHOVEL_STEEL = 1
SHOVEL_SILVER = 2
SHOVEL_GOLD = 3
MAX_SHOVELS = 4
ShovelAttributes = {0: {'numBoxes': 2,
     'skillPts': 80,
     'name': TTLocalizer.ShovelTin},
 1: {'numBoxes': 2,
     'skillPts': 160,
     'name': TTLocalizer.ShovelSteel},
 2: {'numBoxes': 2,
     'skillPts': 320,
     'name': TTLocalizer.ShovelSilver},
 3: {'numBoxes': 2,
     'skillPts': 640,
     'name': TTLocalizer.ShovelGold}}

def getShovelPower(shovel, shovelSkill):
    numBoxes = 0
    for curShovel in range(shovel + 1):
        shovelAttrib = ShovelAttributes[curShovel]
        curBoxes = shovelAttrib['numBoxes']
        skill = shovelAttrib['skillPts']
        if curShovel == shovel:
            if shovelSkill >= skill:
                gardenNotify.warning("this shouldn't happen shovelSkill %d >= skill %d" % (shovelSkill, skill))
                shovelSkill = skill - 1
            skillPtPerBox = skill / curBoxes
            numBoxes += 1 + int(shovelSkill) / int(skillPtPerBox)
        else:
            numBoxes += curBoxes

    return numBoxes


def getMaxShovelSkill():
    retVal = 0
    retVal += ShovelAttributes[MAX_SHOVELS - 1]['skillPts'] - 1
    return retVal


def getNumberOfShovelBoxes():
    retVal = 0
    for attrib in ShovelAttributes.values():
        retVal += attrib['numBoxes']

    return retVal


def getNumberOfWateringCanBoxes():
    retVal = 0
    for attrib in WateringCanAttributes.values():
        retVal += attrib['numBoxes']

    return retVal


def getNumberOfFlowerVarieties():
    retVal = 0
    for attrib in PlantAttributes.values():
        if attrib['plantType'] == FLOWER_TYPE:
            retVal += len(attrib['varieties'])

    return retVal


def getNumberOfFlowerSpecies():
    retVal = 0
    for attrib in PlantAttributes.values():
        if attrib['plantType'] == FLOWER_TYPE:
            retVal += 1

    return retVal


def getFlowerVarieties(species):
    retval = ()
    if species in PlantAttributes.keys():
        attrib = PlantAttributes[species]
        if attrib['plantType'] == FLOWER_TYPE:
            retval = attrib['varieties']
    return retval


def getFlowerSpecies():
    retVal = []
    for key in PlantAttributes.keys():
        attrib = PlantAttributes[key]
        if attrib['plantType'] == FLOWER_TYPE:
            retVal.append(key)

    return retVal


def getRandomFlower():
    species = random.choice(getFlowerSpecies())
    variety = random.randint(0, len(PlantAttributes[species]['varieties']) - 1)
    return (species, variety)


def getFlowerVarietyName(species, variety):
    retVal = TTLocalizer.FlowerUnknown
    if species in PlantAttributes.keys():
        attrib = PlantAttributes[species]
        if variety < len(attrib['varieties']):
            funnySpeciesNameList = TTLocalizer.FlowerFunnyNames.get(species)
            if funnySpeciesNameList:
                if variety < len(funnySpeciesNameList):
                    retVal = TTLocalizer.FlowerFunnyNames[species][variety]
        else:
            gardenNotify.warning('warning unknown species=%d variety= %d' % (species, variety))
    else:
        gardenNotify.warning('warning unknown species %d' % species)
    return retVal


def getSpeciesVarietyGivenRecipe(recipeKey):
    for species in PlantAttributes.keys():
        attrib = PlantAttributes[species]
        if attrib['plantType'] == GAG_TREE_TYPE:
            continue
        if attrib.has_key('varieties'):
            for variety in range(len(attrib['varieties'])):
                if attrib['varieties'][variety][0] == recipeKey:
                    return (species, variety)

    return (-1, -1)


def getNumBeansRequired(species, variety):
    retval = -1
    if not PlantAttributes.get(species):
        return retval
    if not PlantAttributes[species].has_key('varieties'):
        return retval
    if variety >= len(PlantAttributes[species]['varieties']):
        return -1
    recipeKey = PlantAttributes[species]['varieties'][variety][0]
    recipe = Recipes.get(recipeKey)
    if recipe:
        if recipe.has_key('beans'):
            retval = len(recipe['beans'])
    return retval


def validateRecipes(notify):
    uniqueRecipes = []
    uniqueBeans = []
    numBoxes = getNumberOfShovelBoxes()
    uniqueSpecials = []
    for key in Recipes.keys():
        recipe = Recipes[key]
        beans = recipe['beans']
        if len(beans) > numBoxes:
            notify.warning('numBoxes=%d beans=%s, truncating to %s' % (numBoxes, beans, beans[:numBoxes]))
            beans = beans[:numBoxes]
        for letter in beans:
            if key not in (2001, 2002):
                pass

        testTuple = (beans, recipe['special'])
        uniqueRecipes.append(testTuple)
        if beans:
            if beans in uniqueBeans:
                notify.warning('duplicate beans=%s in key=%d' % (beans, key))
            else:
                uniqueBeans.append(beans)
        special = recipe['special']
        if special != -1:
            uniqueSpecials.append(special)

    notify.debug('recipes are ok')


def validatePlantAttributes(notify):
    uniqueRecipes = []
    flowerRecipeDistribution = []
    for i in range(getNumberOfShovelBoxes() + 1):
        flowerRecipeDistribution.append([])

    for key in PlantAttributes.keys():
        plant = PlantAttributes[key]
        notify.debug('now validating %s' % plant['name'])
        if plant['plantType'] in (GAG_TREE_TYPE, FLOWER_TYPE):
            growthThresholds = plant['growthThresholds']
            lastValue = 0
            for testValue in growthThresholds:
                lastValue = testValue

        if plant['plantType'] in (STATUARY_TYPE, FLOWER_TYPE):
            varieties = plant['varieties']
            for variety in varieties:
                recipeNum = variety[0]
                uniqueRecipes.append(recipeNum)
                if plant['plantType'] == FLOWER_TYPE:
                    recipeLength = len(Recipes[recipeNum]['beans'])
                    newInfo = (getFlowerVarietyName(key, list(varieties).index(variety)), Recipes[recipeNum]['beans'], TTLocalizer.FlowerColorStrings[variety[1]])
                    flowerRecipeDistribution[recipeLength].append(newInfo)

    for numBeans in range(len(flowerRecipeDistribution)):
        notify.debug('%d flowers with %d beans' % (len(flowerRecipeDistribution[numBeans]), numBeans))
        for flower in flowerRecipeDistribution[numBeans]:
            notify.debug('    %s,  beans = %s, color=%s' % (flower[0], flower[1], flower[2]))

    notify.debug('plant attributes are ok')


plots0 = ((0,
  0,
  0.0,
  FLOWER_TYPE),
 (1,
  0,
  0.0,
  FLOWER_TYPE),
 (2,
  0,
  0.0,
  FLOWER_TYPE),
 (2,
  1,
  0.0,
  FLOWER_TYPE),
 (2,
  2,
  0.0,
  FLOWER_TYPE),
 (3,
  0,
  0.0,
  FLOWER_TYPE),
 (3,
  1,
  0.0,
  FLOWER_TYPE),
 (3,
  2,
  0.0,
  FLOWER_TYPE),
 (4,
  0,
  0.0,
  FLOWER_TYPE),
 (4,
  1,
  0.0,
  FLOWER_TYPE),
 (-54,
  -13.5,
  276.0,
  GAG_TREE_TYPE),
 (-7,
  -48,
  343.0,
  GAG_TREE_TYPE),
 (-40,
  -75,
  27.0,
  GAG_TREE_TYPE),
 (-78,
  -44,
  309.0,
  GAG_TREE_TYPE),
 (-72,
  -15,
  260.0,
  GAG_TREE_TYPE),
 (-24,
  -19,
  294.0,
  GAG_TREE_TYPE),
 (11,
  -26,
  0.0,
  GAG_TREE_TYPE),
 (-92,
  -4,
  0.0,
  GAG_TREE_TYPE),
 (-100,
  -43,
  -90.0,
  STATUARY_TYPE))
plots1 = ((0,
  0,
  0.0,
  FLOWER_TYPE),
 (1,
  0,
  0.0,
  FLOWER_TYPE),
 (2,
  0,
  0.0,
  FLOWER_TYPE),
 (2,
  1,
  0.0,
  FLOWER_TYPE),
 (2,
  2,
  0.0,
  FLOWER_TYPE),
 (3,
  0,
  0.0,
  FLOWER_TYPE),
 (3,
  1,
  0.0,
  FLOWER_TYPE),
 (3,
  2,
  0.0,
  FLOWER_TYPE),
 (4,
  0,
  0.0,
  FLOWER_TYPE),
 (4,
  1,
  0.0,
  FLOWER_TYPE),
 (62,
  -81,
  194.0,
  GAG_TREE_TYPE),
 (101,
  -52,
  250.0,
  GAG_TREE_TYPE),
 (93,
  -104,
  214.0,
  GAG_TREE_TYPE),
 (69,
  -122,
  188.0,
  GAG_TREE_TYPE),
 (92,
  -120,
  184.0,
  GAG_TREE_TYPE),
 (113,
  -29,
  250.0,
  GAG_TREE_TYPE),
 (125,
  -57,
  0.0,
  GAG_TREE_TYPE),
 (114,
  -40,
  0.0,
  GAG_TREE_TYPE),
 (47,
  -82,
  -30.0,
  STATUARY_TYPE))
plots2 = ((0,
  0,
  0.0,
  FLOWER_TYPE),
 (1,
  0,
  0.0,
  FLOWER_TYPE),
 (2,
  0,
  0.0,
  FLOWER_TYPE),
 (2,
  1,
  0.0,
  FLOWER_TYPE),
 (2,
  2,
  0.0,
  FLOWER_TYPE),
 (3,
  0,
  0.0,
  FLOWER_TYPE),
 (3,
  1,
  0.0,
  FLOWER_TYPE),
 (3,
  2,
  0.0,
  FLOWER_TYPE),
 (4,
  0,
  0.0,
  FLOWER_TYPE),
 (4,
  1,
  0.0,
  FLOWER_TYPE),
 (-40,
  -114,
  176.0,
  GAG_TREE_TYPE),
 (-44,
  -148,
  162.0,
  GAG_TREE_TYPE),
 (-97,
  -99,
  138.0,
  GAG_TREE_TYPE),
 (-82,
  -94,
  134.0,
  GAG_TREE_TYPE),
 (-27,
  -106,
  195.0,
  GAG_TREE_TYPE),
 (-76,
  -147,
  110.0,
  GAG_TREE_TYPE),
 (-29,
  -164,
  0.0,
  GAG_TREE_TYPE),
 (-107,
  -94,
  0.0,
  GAG_TREE_TYPE),
 (-97,
  -114,
  -60.0,
  STATUARY_TYPE))
plots3 = ((0,
  0,
  0.0,
  FLOWER_TYPE),
 (1,
  0,
  0.0,
  FLOWER_TYPE),
 (2,
  0,
  0.0,
  FLOWER_TYPE),
 (2,
  1,
  0.0,
  FLOWER_TYPE),
 (2,
  2,
  0.0,
  FLOWER_TYPE),
 (3,
  0,
  0.0,
  FLOWER_TYPE),
 (3,
  1,
  0.0,
  FLOWER_TYPE),
 (3,
  2,
  0.0,
  FLOWER_TYPE),
 (4,
  0,
  0.0,
  FLOWER_TYPE),
 (4,
  1,
  0.0,
  FLOWER_TYPE),
 (59,
  35,
  187.0,
  GAG_TREE_TYPE),
 (87,
  28,
  114.0,
  GAG_TREE_TYPE),
 (67,
  -16,
  78.0,
  GAG_TREE_TYPE),
 (24,
  19,
  155.0,
  GAG_TREE_TYPE),
 (18,
  31,
  172.0,
  GAG_TREE_TYPE),
 (74,
  36,
  133.0,
  GAG_TREE_TYPE),
 (35,
  -34,
  0.0,
  GAG_TREE_TYPE),
 (116,
  17,
  0.0,
  GAG_TREE_TYPE),
 (117,
  27,
  102.0,
  STATUARY_TYPE))
plots4 = ((0,
  0,
  0.0,
  FLOWER_TYPE),
 (1,
  0,
  0.0,
  FLOWER_TYPE),
 (2,
  0,
  0.0,
  FLOWER_TYPE),
 (2,
  1,
  0.0,
  FLOWER_TYPE),
 (2,
  2,
  0.0,
  FLOWER_TYPE),
 (3,
  0,
  0.0,
  FLOWER_TYPE),
 (3,
  1,
  0.0,
  FLOWER_TYPE),
 (3,
  2,
  0.0,
  FLOWER_TYPE),
 (4,
  0,
  0.0,
  FLOWER_TYPE),
 (4,
  1,
  0.0,
  FLOWER_TYPE),
 (37,
  101,
  350.0,
  GAG_TREE_TYPE),
 (15,
  100,
  342.0,
  GAG_TREE_TYPE),
 (73,
  92,
  0.0,
  GAG_TREE_TYPE),
 (74,
  69,
  347.0,
  GAG_TREE_TYPE),
 (102,
  62,
  334.0,
  GAG_TREE_TYPE),
 (86,
  76,
  350.0,
  GAG_TREE_TYPE),
 (100,
  78,
  327.0,
  GAG_TREE_TYPE),
 (15,
  73,
  50.0,
  GAG_TREE_TYPE),
 (16,
  87,
  -140.0,
  STATUARY_TYPE))
plots5 = ((0,
  0,
  0.0,
  FLOWER_TYPE),
 (1,
  0,
  0.0,
  FLOWER_TYPE),
 (2,
  0,
  0.0,
  FLOWER_TYPE),
 (2,
  1,
  0.0,
  FLOWER_TYPE),
 (2,
  2,
  0.0,
  FLOWER_TYPE),
 (3,
  0,
  0.0,
  FLOWER_TYPE),
 (3,
  1,
  0.0,
  FLOWER_TYPE),
 (3,
  2,
  0.0,
  FLOWER_TYPE),
 (4,
  0,
  0.0,
  FLOWER_TYPE),
 (4,
  1,
  0.0,
  FLOWER_TYPE),
 (-26,
  92,
  41.0,
  GAG_TREE_TYPE),
 (-71,
  58,
  37.0,
  GAG_TREE_TYPE),
 (-67,
  21,
  243.0,
  GAG_TREE_TYPE),
 (-10,
  -2.6,
  178.0,
  GAG_TREE_TYPE),
 (-60,
  13.7,
  250.0,
  GAG_TREE_TYPE),
 (-13,
  84,
  2.0,
  GAG_TREE_TYPE),
 (-62,
  65,
  0.0,
  GAG_TREE_TYPE),
 (-16.6,
  52.7,
  0.0,
  GAG_TREE_TYPE),
 (-55,
  70,
  213.0,
  STATUARY_TYPE))
estatePlots = (plots0,
 plots1,
 plots2,
 plots3,
 plots4,
 plots5)
BOX_ONE = 1
BOX_TWO = 2
BOX_THREE = 3
flowerBoxes0 = ((-62.5,
  -52.5,
  182.0,
  BOX_ONE),
 (-52,
  -52,
  182,
  BOX_ONE),
 (-64.5,
  -42,
  92.0,
  BOX_THREE),
 (-49,
  -43,
  266.0,
  BOX_THREE),
 (-57,
  -33,
  0.0,
  BOX_TWO))
flowerBoxes1 = ((85.0,
  -67.0,
  26.0,
  BOX_ONE),
 (75,
  -72,
  26.0,
  BOX_ONE),
 (91.0,
  -74.0,
  -63.0,
  BOX_THREE),
 (77,
  -81,
  117.0,
  BOX_THREE),
 (88,
  -86,
  206.0,
  BOX_TWO))
flowerBoxes2 = ((-62,
  -112,
  350.0,
  BOX_ONE),
 (-72,
  -110,
  350.0,
  BOX_ONE),
 (-62,
  -122,
  257.0,
  BOX_THREE),
 (-76,
  -118,
  79.0,
  BOX_THREE),
 (-71,
  -129,
  169.0,
  BOX_TWO))
flowerBoxes3 = ((72,
  5,
  265.0,
  BOX_ONE),
 (72.5,
  16,
  265.0,
  BOX_ONE),
 (63,
  3,
  178.0,
  BOX_THREE),
 (64,
  19,
  355.0,
  BOX_THREE),
 (54,
  12,
  86.0,
  BOX_TWO))
flowerBoxes4 = ((35.5,
  70,
  152.0,
  BOX_ONE),
 (46,
  66,
  152.0,
  BOX_ONE),
 (36.5,
  79.5,
  71.0,
  BOX_THREE),
 (51.5,
  74,
  247.0,
  BOX_THREE),
 (47,
  86,
  -19.0,
  BOX_TWO))
flowerBoxes5 = ((-26.5,
  37.5,
  318.0,
  BOX_ONE),
 (-33,
  46,
  318.0,
  BOX_ONE),
 (-32,
  30,
  217.0,
  BOX_THREE),
 (-42,
  42,
  37.0,
  BOX_THREE),
 (-45,
  31,
  124.0,
  BOX_TWO))
estateBoxes = (flowerBoxes0,
 flowerBoxes1,
 flowerBoxes2,
 flowerBoxes3,
 flowerBoxes4,
 flowerBoxes5)

def whatCanBePlanted(plotIndex, hardPointIndex):
    retval = INVALID_TYPE
    if plotIndex < len(estatePlots) and plotIndex >= 0:
        if hardPointIndex < len(estatePlots[plotIndex]) and hardPointIndex >= 0:
            if len(estatePlots[plotIndex][hardPointIndex]) >= 4:
                retval = estatePlots[plotIndex][hardPointIndex][3]
    return retval


MAGIC_BEAN_SUBTYPE = 0
GARDEN_ITEM_SUBTYPE = 1
Specials = {0: {'subtype': MAGIC_BEAN_SUBTYPE,
     'gagbonus': 1,
     'photoModel': 'phase_4/models/props/goofy_statue',
     'photoScale': 0.1,
     'photoPos': (0, 0, -1),
     'photoName': TTLocalizer.GardenTextMagicBeans,
     'description': TTLocalizer.GardenSpecialDiscription,
     'beanCost': 125},
 1: {'subtype': MAGIC_BEAN_SUBTYPE,
     'gagbonus': 2,
     'photoModel': 'phase_4/models/props/goofy_statue',
     'photoScale': 0.1,
     'photoPos': (0, 0, -1),
     'photoName': TTLocalizer.GardenTextMagicBeansB,
     'description': TTLocalizer.GardenSpecialDiscriptionB,
     'beanCost': 125},
 2: {'subtype': MAGIC_BEAN_SUBTYPE,
     'gagbonus': 1,
     'photoModel': 'phase_4/models/props/goofy_statue',
     'photoScale': 0.1,
     'photoPos': (0, 0, -1),
     'photoName': TTLocalizer.GardenTextMagicBeans,
     'description': TTLocalizer.GardenSpecialDiscription,
     'beanCost': 125},
 3: {'subtype': MAGIC_BEAN_SUBTYPE,
     'gagbonus': 2,
     'photoModel': 'phase_4/models/props/goofy_statue',
     'photoScale': 0.1,
     'photoPos': (0, 0, -1),
     'photoName': TTLocalizer.GardenTextMagicBeansB,
     'description': TTLocalizer.GardenSpecialDiscriptionB,
     'beanCost': 125},
 4: {'subtype': MAGIC_BEAN_SUBTYPE,
     'gagbonus': 1,
     'photoModel': 'phase_4/models/props/goofy_statue',
     'photoScale': 0.1,
     'photoPos': (0, 0, -1),
     'photoName': TTLocalizer.GardenTextMagicBeans,
     'description': TTLocalizer.GardenSpecialDiscription,
     'beanCost': 125},
 5: {'subtype': MAGIC_BEAN_SUBTYPE,
     'gagbonus': 2,
     'photoModel': 'phase_4/models/props/goofy_statue',
     'photoScale': 0.1,
     'photoPos': (0, 0, -1),
     'photoName': TTLocalizer.GardenTextMagicBeansB,
     'description': TTLocalizer.GardenSpecialDiscriptionB,
     'beanCost': 125},
 6: {'subtype': MAGIC_BEAN_SUBTYPE,
     'gagbonus': 2,
     'photoModel': 'phase_4/models/props/goofy_statue',
     'photoScale': 0.1,
     'photoPos': (0, 0, -1),
     'photoName': TTLocalizer.GardenTextMagicBeansB,
     'description': TTLocalizer.GardenSpecialDiscription,
     'beanCost': 125},
 7: {'subtype': MAGIC_BEAN_SUBTYPE,
     'gagbonus': 2,
     'photoModel': 'phase_4/models/props/goofy_statue',
     'photoScale': 0.1,
     'photoPos': (0, 0, -1),
     'photoName': TTLocalizer.GardenTextMagicBeansB,
     'description': TTLocalizer.GardenSpecialDiscriptionB,
     'beanCost': 125},
 100: {'subtype': GARDEN_ITEM_SUBTYPE,
       'photoModel': 'phase_5.5/models/estate/garden_donald',
       'photoScale': 0.04,
       'photoPos': (0, 0, -1),
       'photoName': TTLocalizer.StatuaryDonald,
       'description': TTLocalizer.GardenSpecialDiscription,
       'isCatalog': True,
       'beanCost': 125},
 101: {'subtype': GARDEN_ITEM_SUBTYPE,
       'photoModel': 'phase_5.5/models/estate/garden_mickey_flute',
       'photoScale': 0.025,
       'photoPos': (0, 0, -1.05),
       'photoName': TTLocalizer.StatuaryMickey1,
       'description': TTLocalizer.GardenSpecialDiscription,
       'isCatalog': True,
       'beanCost': 250},
 102: {'subtype': GARDEN_ITEM_SUBTYPE,
       'photoModel': 'phase_5.5/models/estate/sack',
       'photoScale': 1.0,
       'photoPos': (0, 0, -1.0),
       'photoName': TTLocalizer.StatuaryGardenAccelerator,
       'description': TTLocalizer.GardenSpecialDiscription,
       'isCatalog': True,
       'beanCost': 7500,
       'useFromShtiker': False},
 103: {'subtype': GARDEN_ITEM_SUBTYPE,
       'photoModel': 'phase_5.5/models/estate/garden_minnie',
       'photoScale': 0.02,
       'photoPos': (0, 0, -1.05),
       'photoName': TTLocalizer.StatuaryMinnie,
       'description': TTLocalizer.GardenSpecialDiscription,
       'isCatalog': True,
       'beanCost': 500},
 104: {'subtype': GARDEN_ITEM_SUBTYPE,
       'photoModel': 'phase_5.5/models/estate/garden_mickey_shovel',
       'photoScale': 0.02,
       'photoPos': (0, 0, -1.05),
       'photoName': TTLocalizer.StatuaryMickey2,
       'description': TTLocalizer.GardenSpecialDiscription,
       'isCatalog': True,
       'beanCost': 1000},
 105: {'subtype': GARDEN_ITEM_SUBTYPE,
       'photoModel': 'phase_5.5/models/estate/garden_pedestal',
       'photoScale': 0.02,
       'photoPos': (0, 0, -1.05),
       'photoName': TTLocalizer.StatuaryToonWave,
       'description': TTLocalizer.GardenSpecialDiscription,
       'isCatalog': True,
       'beanCost': 5000,
       'minSkill': 639},
 106: {'subtype': GARDEN_ITEM_SUBTYPE,
       'photoModel': 'phase_5.5/models/estate/garden_pedestal',
       'photoScale': 0.02,
       'photoPos': (0, 0, -1.05),
       'photoName': TTLocalizer.StatuaryToonVictory,
       'description': TTLocalizer.GardenSpecialDiscription,
       'isCatalog': True,
       'beanCost': 5000,
       'minSkill': 639},
 107: {'subtype': GARDEN_ITEM_SUBTYPE,
       'photoModel': 'phase_5.5/models/estate/garden_pedestal',
       'photoScale': 0.02,
       'photoPos': (0, 0, -1.05),
       'photoName': TTLocalizer.StatuaryToonCrossedArms,
       'description': TTLocalizer.GardenSpecialDiscription,
       'isCatalog': True,
       'beanCost': 5000,
       'minSkill': 639},
 108: {'subtype': GARDEN_ITEM_SUBTYPE,
       'photoModel': 'phase_5.5/models/estate/garden_pedestal',
       'photoScale': 0.02,
       'photoPos': (0, 0, -1.05),
       'photoName': TTLocalizer.StatuaryToonThinking,
       'description': TTLocalizer.GardenSpecialDiscription,
       'isCatalog': True,
       'beanCost': 5000,
       'minSkill': 639},
 130: {'subtype': GARDEN_ITEM_SUBTYPE,
       'photoModel': 'phase_5.5/models/estate/tt_m_prp_ext_snowman_icon',
       'photoScale': 90.0,
       'photoPos': (0, 0, 0.0),
       'photoName': TTLocalizer.StatuaryMeltingSnowman,
       'description': TTLocalizer.GardenSpecialDiscription,
       'isCatalog': True,
       'beanCost': 25,
       'minSkill': 0},
 131: {'subtype': GARDEN_ITEM_SUBTYPE,
       'photoModel': 'phase_5.5/models/estate/tt_m_prp_ext_snowDoodle_icon',
       'photoScale': 90.0,
       'photoPos': (0, 0, 0.0),
       'photoName': TTLocalizer.StatuaryMeltingSnowDoodle,
       'description': TTLocalizer.GardenSpecialDiscription,
       'isCatalog': True,
       'beanCost': 50,
       'minSkill': 0},
 135: {'subtype': GARDEN_ITEM_SUBTYPE,
       'photoModel': 'phase_5.5/models/estate/tt_a_ara_pty_tubeCogVictory_',
       'photoAnimation': ['default', 'wave'],
       'photoScale': 1.25,
       'photoPos': (0, 0, -0.04),
       'photoName': TTLocalizer.AnimatedStatuaryFlappyCog,
       'description': TTLocalizer.GardenSpecialDiscription,
       'isCatalog': True,
       'beanCost': 50,
       'minSkill': 1}}
GardenAcceleratorSpecial = 102
GardenAcceleratorSpecies = 202
if ACCELERATOR_USED_FROM_SHTIKER_BOOK:
    Specials[GardenAcceleratorSpecial]['useFromShtiker'] = True

def getPlantItWithString(special):
    retval = ''
    recipeKey = getRecipeKeyUsingSpecial(special)
    if not recipeKey == -1:
        beanTuple = []
        beanStr = Recipes[recipeKey]['beans']
        for letter in beanStr:
            index = BeanColorLetters.index(letter)
            beanTuple.append(index)

        beanText = TTLocalizer.getRecipeBeanText(beanTuple)
        retval += TTLocalizer.PlantItWith % beanText
    return retval


for specialKey in Specials.keys():
    recipeKey = getRecipeKeyUsingSpecial(specialKey)
    if not recipeKey == -1:
        Specials[specialKey]['description'] = getPlantItWithString(specialKey)
        if specialKey == GardenAcceleratorSpecial:
            if ACCELERATOR_USED_FROM_SHTIKER_BOOK:
                Specials[specialKey]['description'] = TTLocalizer.UseFromSpecialsTab
            Specials[specialKey]['description'] += TTLocalizer.MakeSureWatered

TIME_OF_DAY_FOR_EPOCH = 3
MOVIE_HARVEST = 0
MOVIE_PLANT = 1
MOVIE_REMOVE = 2
MOVIE_WATER = 3
MOVIE_FINISHPLANTING = 4
MOVIE_FINISHREMOVING = 5
MOVIE_CLEAR = 6
MOVIE_PLANT_REJECTED = 7
TrophyDict = {0: (TTLocalizer.GardenTrophyNameDict[0],),
 1: (TTLocalizer.GardenTrophyNameDict[1],),
 2: (TTLocalizer.GardenTrophyNameDict[2],),
 3: (TTLocalizer.GardenTrophyNameDict[3],)}
