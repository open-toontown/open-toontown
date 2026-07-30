from toontown.toonbase import TTLocalizer
from math import ceil, pow
import random
from toontown.toonbase import ToontownGlobals
import copy
NoMovie = 0
EnterMovie = 1
ExitMovie = 2
CastMovie = 3
PullInMovie = 4
CastTimeout = 45.0
Nothing = 0
QuestItem = 1
FishItem = 2
JellybeanItem = 3
BootItem = 4
GagItem = 5
OverTankLimit = 8
FishItemNewEntry = 9
FishItemNewRecord = 10
BingoBoot = (BootItem, 99)
ProbabilityDict = {93: FishItem,
 94: JellybeanItem,
 100: BootItem}
SortedProbabilityCutoffs = list(ProbabilityDict.keys())
SortedProbabilityCutoffs.sort()
Rod2JellybeanDict = {0: 10,
 1: 20,
 2: 30,
 3: 75,
 4: 150}
HealAmount = 1
JellybeanFishingHolidayScoreMultiplier = 2
MAX_RARITY = 10
GlobalRarityDialBase = 4.3
FishingAngleMax = 50.0
OVERALL_VALUE_SCALE = 15
RARITY_VALUE_SCALE = 0.2
WEIGHT_VALUE_SCALE = 0.05 / 16.0
COLLECT_NO_UPDATE = 0
COLLECT_NEW_ENTRY = 1
COLLECT_NEW_RECORD = 2
RodFileDict = {0: 'phase_4/models/props/pole_treebranch-mod',
 1: 'phase_4/models/props/pole_bamboo-mod',
 2: 'phase_4/models/props/pole_wood-mod',
 3: 'phase_4/models/props/pole_steel-mod',
 4: 'phase_4/models/props/pole_gold-mod'}
RodPriceDict = {0: 0,
 1: 400,
 2: 800,
 3: 1200,
 4: 2000}
RodRarityFactor = {0: 1.0 / (GlobalRarityDialBase * 1),
 1: 1.0 / (GlobalRarityDialBase * 0.975),
 2: 1.0 / (GlobalRarityDialBase * 0.95),
 3: 1.0 / (GlobalRarityDialBase * 0.9),
 4: 1.0 / (GlobalRarityDialBase * 0.85)}
MaxRodId = 4
FishAudioFileDict = {-1: ('Clownfish.ogg',
      1,
      1.5,
      1.0),
 0: ('BalloonFish.ogg',
     1,
     0,
     1.23),
 2: ('CatFish.ogg',
     1,
     0,
     1.26),
 4: ('Clownfish.ogg',
     1,
     1.5,
     1.0),
 6: ('Frozen_Fish.ogg',
     1,
     0,
     1.0),
 8: ('Starfish.ogg',
     0,
     0,
     1.25),
 10: ('Holy_Mackerel.ogg',
      1,
      0.9,
      1.0),
 12: ('Dog_Fish.ogg',
      1,
      0,
      1.25),
 14: ('AmoreEel.ogg',
      1,
      0,
      1.0),
 16: ('Nurse_Shark.ogg',
      0,
      0,
      1.0),
 18: ('King_Crab.ogg',
      0,
      0,
      1.0),
 20: ('Moon_Fish.ogg',
      0,
      1.0,
      1.0),
 22: ('Seahorse.ogg',
      1,
      0,
      1.26),
 24: ('Pool_Shark.ogg',
      1,
      2.0,
      1.0),
 26: ('Bear_Acuda.ogg',
      1,
      0,
      1.0),
 28: ('CutThroatTrout.ogg',
      1,
      0,
      1.0),
 30: ('Piano_Tuna.ogg',
      0,
      0,
      1.0),
 32: ('PBJ_Fish.ogg',
      1,
      0,
      1.25),
 34: ('DevilRay.ogg',
      0,
      0,
      1.0)}
FishFileDict = {-1: (4,
      'clownFish-zero',
      'clownFish-swim',
      'clownFish-swim',
      None,
      (0.12, 0, -0.15),
      0.38,
      -35,
      20),
 0: (4,
     'balloonFish-zero',
     'balloonFish-swim',
     'balloonFish-swim',
     None,
     (0.0, 0, 0.0),
     1.0,
     0,
     0),
 2: (4,
     'catFish-zero',
     'catFish-swim',
     'catFish-swim',
     None,
     (1.2, -2.0, 0.5),
     0.22,
     -35,
     10),
 4: (4,
     'clownFish-zero',
     'clownFish-swim',
     'clownFish-swim',
     None,
     (0.12, 0, -0.15),
     0.38,
     -35,
     20),
 6: (4,
     'frozenFish-zero',
     'frozenFish-swim',
     'frozenFish-swim',
     None,
     (0, 0, 0),
     0.5,
     -35,
     20),
 8: (4,
     'starFish-zero',
     'starFish-swim',
     'starFish-swimLOOP',
     None,
     (0, 0, -0.38),
     0.36,
     -35,
     20),
 10: (4,
      'holeyMackerel-zero',
      'holeyMackerel-swim',
      'holeyMackerel-swim',
      None,
      None,
      0.4,
      0,
      0),
 12: (4,
      'dogFish-zero',
      'dogFish-swim',
      'dogFish-swim',
      None,
      (0.8, -1.0, 0.275),
      0.33,
      -38,
      10),
 14: (4,
      'amoreEel-zero',
      'amoreEel-swim',
      'amoreEel-swim',
      None,
      (0.425, 0, 1.15),
      0.5,
      0,
      60),
 16: (4,
      'nurseShark-zero',
      'nurseShark-swim',
      'nurseShark-swim',
      None,
      (0, 0, -0.15),
      0.3,
      -40,
      10),
 18: (4,
      'kingCrab-zero',
      'kingCrab-swim',
      'kingCrab-swimLOOP',
      None,
      None,
      0.4,
      0,
      0),
 20: (4,
      'moonFish-zero',
      'moonFish-swim',
      'moonFish-swimLOOP',
      None,
      (-1.2, 14, -2.0),
      0.33,
      0,
      -10),
 22: (4,
      'seaHorse-zero',
      'seaHorse-swim',
      'seaHorse-swim',
      None,
      (-0.57, 0.0, -2.1),
      0.23,
      33,
      -10),
 24: (4,
      'poolShark-zero',
      'poolShark-swim',
      'poolShark-swim',
      None,
      (-0.45, 0, -1.8),
      0.33,
      45,
      0),
 26: (4,
      'BearAcuda-zero',
      'BearAcuda-swim',
      'BearAcuda-swim',
      None,
      (0.65, 0, -3.3),
      0.2,
      -35,
      20),
 28: (4,
      'cutThroatTrout-zero',
      'cutThroatTrout-swim',
      'cutThroatTrout-swim',
      None,
      (-0.2, 0, -0.1),
      0.5,
      35,
      20),
 30: (4,
      'pianoTuna-zero',
      'pianoTuna-swim',
      'pianoTuna-swim',
      None,
      (0.3, 0, 0.0),
      0.6,
      40,
      30),
 32: (4,
      'PBJfish-zero',
      'PBJfish-swim',
      'PBJfish-swim',
      None,
      (0, 0, 0.72),
      0.31,
      -35,
      10),
 34: (4,
      'devilRay-zero',
      'devilRay-swim',
      'devilRay-swim',
      None,
      (0, 0, 0),
      0.4,
      -35,
      20)}
FISH_PER_BONUS = 10
TrophyDict = {0: (TTLocalizer.FishTrophyNameDict[0],),
 1: (TTLocalizer.FishTrophyNameDict[1],),
 2: (TTLocalizer.FishTrophyNameDict[2],),
 3: (TTLocalizer.FishTrophyNameDict[3],),
 4: (TTLocalizer.FishTrophyNameDict[4],),
 5: (TTLocalizer.FishTrophyNameDict[5],),
 6: (TTLocalizer.FishTrophyNameDict[6],)}
WEIGHT_MIN_INDEX = 0
WEIGHT_MAX_INDEX = 1
RARITY_INDEX = 2
ZONE_LIST_INDEX = 3
Anywhere = 1
TTG = ToontownGlobals
__fishDict = {0: ((1,
      3,
      1,
      (Anywhere,)),
     (1,
      1,
      4,
      (TTG.ToontownCentral, Anywhere)),
     (3,
      5,
      5,
      (TTG.PunchlinePlace, TTG.TheBrrrgh)),
     (3,
      5,
      3,
      (TTG.SillyStreet, TTG.DaisyGardens)),
     (1,
      5,
      2,
      (TTG.LoopyLane, TTG.ToontownCentral))),
 2: ((2,
      6,
      1,
      (TTG.DaisyGardens, Anywhere)),
     (2,
      6,
      9,
      (TTG.ElmStreet, TTG.DaisyGardens)),
     (5,
      11,
      4,
      (TTG.LullabyLane,)),
     (2,
      6,
      3,
      (TTG.DaisyGardens, TTG.MyEstate)),
     (5,
      11,
      2,
      (TTG.DonaldsDreamland, TTG.MyEstate))),
 4: ((2,
      8,
      1,
      (TTG.ToontownCentral, Anywhere)),
     (2,
      8,
      4,
      (TTG.ToontownCentral, Anywhere)),
     (2,
      8,
      2,
      (TTG.ToontownCentral, Anywhere)),
     (2,
      8,
      6,
      (TTG.ToontownCentral, TTG.MinniesMelodyland))),
 6: ((8,
      12,
      1,
      (TTG.TheBrrrgh,)),),
 8: ((1,
      5,
      1,
      (Anywhere,)),
     (2,
      6,
      2,
      (TTG.MinniesMelodyland, Anywhere)),
     (5,
      10,
      5,
      (TTG.MinniesMelodyland, Anywhere)),
     (1,
      5,
      7,
      (TTG.MyEstate, Anywhere)),
     (1,
      5,
      10,
      (TTG.MyEstate, Anywhere))),
 10: ((6,
       10,
       9,
       (TTG.MyEstate, Anywhere)),),
 12: ((7,
       15,
       1,
       (TTG.DonaldsDock, Anywhere)),
      (18,
       20,
       6,
       (TTG.DonaldsDock, TTG.MyEstate)),
      (1,
       5,
       5,
       (TTG.DonaldsDock, TTG.MyEstate)),
      (3,
       7,
       4,
       (TTG.DonaldsDock, TTG.MyEstate)),
      (1,
       2,
       2,
       (TTG.DonaldsDock, Anywhere))),
 14: ((2,
       6,
       1,
       (TTG.DaisyGardens, TTG.MyEstate, Anywhere)), (2,
       6,
       3,
       (TTG.DaisyGardens, TTG.MyEstate))),
 16: ((4,
       12,
       5,
       (TTG.MinniesMelodyland, Anywhere)), (4,
       12,
       7,
       (TTG.BaritoneBoulevard, TTG.MinniesMelodyland)), (4,
       12,
       8,
       (TTG.TenorTerrace, TTG.MinniesMelodyland))),
 18: ((2,
       4,
       3,
       (TTG.DonaldsDock, Anywhere)), (5,
       8,
       7,
       (TTG.TheBrrrgh,)), (4,
       6,
       8,
       (TTG.LighthouseLane,))),
 20: ((4,
       6,
       1,
       (TTG.DonaldsDreamland,)),
      (14,
       18,
       10,
       (TTG.DonaldsDreamland,)),
      (6,
       10,
       8,
       (TTG.LullabyLane,)),
      (1,
       1,
       3,
       (TTG.DonaldsDreamland,)),
      (2,
       6,
       6,
       (TTG.LullabyLane,)),
      (10,
       14,
       4,
       (TTG.DonaldsDreamland, TTG.DaisyGardens))),
 22: ((12,
       16,
       2,
       (TTG.MyEstate, TTG.DaisyGardens, Anywhere)),
      (14,
       18,
       3,
       (TTG.MyEstate, TTG.DaisyGardens, Anywhere)),
      (14,
       20,
       5,
       (TTG.MyEstate, TTG.DaisyGardens)),
      (14,
       20,
       7,
       (TTG.MyEstate, TTG.DaisyGardens))),
 24: ((9,
       11,
       3,
       (Anywhere,)),
      (8,
       12,
       5,
       (TTG.DaisyGardens, TTG.DonaldsDock)),
      (8,
       12,
       6,
       (TTG.DaisyGardens, TTG.DonaldsDock)),
      (8,
       16,
       7,
       (TTG.DaisyGardens, TTG.DonaldsDock))),
 26: ((10,
       18,
       2,
       (TTG.TheBrrrgh,)),
      (10,
       18,
       3,
       (TTG.TheBrrrgh,)),
      (10,
       18,
       4,
       (TTG.TheBrrrgh,)),
      (10,
       18,
       5,
       (TTG.TheBrrrgh,)),
      (12,
       20,
       6,
       (TTG.TheBrrrgh,)),
      (14,
       20,
       7,
       (TTG.TheBrrrgh,)),
      (14,
       20,
       8,
       (TTG.SleetStreet, TTG.TheBrrrgh)),
      (16,
       20,
       10,
       (TTG.WalrusWay, TTG.TheBrrrgh))),
 28: ((2,
       10,
       2,
       (TTG.DonaldsDock, Anywhere)), (4,
       10,
       6,
       (TTG.BarnacleBoulevard, TTG.DonaldsDock)), (4,
       10,
       7,
       (TTG.SeaweedStreet, TTG.DonaldsDock))),
 30: ((13,
       17,
       5,
       (TTG.MinniesMelodyland, Anywhere)),
      (16,
       20,
       10,
       (TTG.AltoAvenue, TTG.MinniesMelodyland)),
      (12,
       18,
       9,
       (TTG.TenorTerrace, TTG.MinniesMelodyland)),
      (12,
       18,
       6,
       (TTG.MinniesMelodyland,)),
      (12,
       18,
       7,
       (TTG.MinniesMelodyland,))),
 32: ((1,
       5,
       2,
       (TTG.ToontownCentral, TTG.MyEstate, Anywhere)),
      (1,
       5,
       3,
       (TTG.TheBrrrgh, TTG.MyEstate, Anywhere)),
      (1,
       5,
       4,
       (TTG.DaisyGardens, TTG.MyEstate)),
      (1,
       5,
       5,
       (TTG.DonaldsDreamland, TTG.MyEstate)),
      (1,
       5,
       10,
       (TTG.TheBrrrgh, TTG.DonaldsDreamland))),
 34: ((1,
       20,
       10,
       (TTG.DonaldsDreamland, Anywhere)),)}

def getSpecies(genus):
    return __fishDict[genus]


def getGenera():
    return list(__fishDict.keys())


ROD_WEIGHT_MIN_INDEX = 0
ROD_WEIGHT_MAX_INDEX = 1
ROD_CAST_COST_INDEX = 2
__rodDict = {0: (0, 4, 1),
 1: (0, 8, 2),
 2: (0, 12, 3),
 3: (0, 16, 4),
 4: (0, 20, 5)}

def getNumRods():
    return len(__rodDict)


def getCastCost(rodId):
    return __rodDict[rodId][ROD_CAST_COST_INDEX]


def getEffectiveRarity(rarity, offset):
    return min(MAX_RARITY, rarity + offset)


def canBeCaughtByRod(genus, species, rodIndex):
    minFishWeight, maxFishWeight = getWeightRange(genus, species)
    minRodWeight, maxRodWeight = getRodWeightRange(rodIndex)
    if minRodWeight <= maxFishWeight and maxRodWeight >= minFishWeight:
        return 1
    else:
        return 0


def getRodWeightRange(rodIndex):
    rodProps = __rodDict[rodIndex]
    return (rodProps[ROD_WEIGHT_MIN_INDEX], rodProps[ROD_WEIGHT_MAX_INDEX])


def __rollRarityDice(rodId, rNumGen):
    if rNumGen is None:
        diceRoll = random.random()
    else:
        diceRoll = rNumGen.random()
    exp = RodRarityFactor[rodId]
    rarity = int(ceil(10 * (1 - pow(diceRoll, exp))))
    if rarity <= 0:
        rarity = 1
    return rarity


def getRandomWeight(genus, species, rodIndex = None, rNumGen = None):
    minFishWeight, maxFishWeight = getWeightRange(genus, species)
    if rodIndex is None:
        minWeight = minFishWeight
        maxWeight = maxFishWeight
    else:
        minRodWeight, maxRodWeight = getRodWeightRange(rodIndex)
        minWeight = max(minFishWeight, minRodWeight)
        maxWeight = min(maxFishWeight, maxRodWeight)
    if rNumGen is None:
        randNumA = random.random()
        randNumB = random.random()
    else:
        randNumA = rNumGen.random()
        randNumB = rNumGen.random()
    randNum = (randNumA + randNumB) / 2.0
    randWeight = minWeight + (maxWeight - minWeight) * randNum
    return int(round(randWeight * 16))


def getRandomFishVitals(zoneId, rodId, rNumGen = None):
    rarity = __rollRarityDice(rodId, rNumGen)
    rodDict = __pondInfoDict.get(zoneId)
    rarityDict = rodDict.get(rodId)
    fishList = rarityDict.get(rarity)
    if fishList:
        if rNumGen is None:
            genus, species = random.choice(fishList)
        else:
            genus, species = rNumGen.choice(fishList)
        weight = getRandomWeight(genus, species, rodId, rNumGen)
        return (1,
         genus,
         species,
         weight)
    else:
        return (0, 0, 0, 0)
    return


def getWeightRange(genus, species):
    fishInfo = __fishDict[genus][species]
    return (fishInfo[WEIGHT_MIN_INDEX], fishInfo[WEIGHT_MAX_INDEX])


def getRarity(genus, species):
    return __fishDict[genus][species][RARITY_INDEX]


def getValue(genus, species, weight):
    rarity = getRarity(genus, species)
    rarityValue = pow(RARITY_VALUE_SCALE * rarity, 1.5)
    weightValue = pow(WEIGHT_VALUE_SCALE * weight, 1.1)
    value = OVERALL_VALUE_SCALE * (rarityValue + weightValue)
    finalValue = int(ceil(value))
    base = getBase()
    if hasattr(base, 'cr') and base.cr:
        if hasattr(base.cr, 'newsManager') and base.cr.newsManager:
            holidayIds = base.cr.newsManager.getHolidayIdList()
            if ToontownGlobals.JELLYBEAN_FISHING_HOLIDAY in holidayIds or ToontownGlobals.JELLYBEAN_FISHING_HOLIDAY_MONTH in holidayIds:
                finalValue *= JellybeanFishingHolidayScoreMultiplier
    elif ToontownGlobals.JELLYBEAN_FISHING_HOLIDAY in simbase.air.holidayManager.currentHolidays or ToontownGlobals.JELLYBEAN_FISHING_HOLIDAY_MONTH in simbase.air.holidayManager.currentHolidays:
        finalValue *= JellybeanFishingHolidayScoreMultiplier
    return finalValue


__totalNumFish = 0
__emptyRodDict = {}
for rodIndex in __rodDict:
    __emptyRodDict[rodIndex] = {}

__anywhereDict = copy.deepcopy(__emptyRodDict)
__pondInfoDict = {}
for genus, speciesList in list(__fishDict.items()):
    for species in range(len(speciesList)):
        __totalNumFish += 1
        speciesDesc = speciesList[species]
        rarity = speciesDesc[RARITY_INDEX]
        zoneList = speciesDesc[ZONE_LIST_INDEX]
        for zoneIndex in range(len(zoneList)):
            zone = zoneList[zoneIndex]
            effectiveRarity = getEffectiveRarity(rarity, zoneIndex)
            if zone == Anywhere:
                for rodIndex, rarityDict in list(__anywhereDict.items()):
                    if canBeCaughtByRod(genus, species, rodIndex):
                        fishList = rarityDict.setdefault(effectiveRarity, [])
                        fishList.append((genus, species))

            else:
                pondZones = [zone]
                subZones = ToontownGlobals.HoodHierarchy.get(zone)
                if subZones:
                    pondZones.extend(subZones)
                for pondZone in pondZones:
                    if pondZone in __pondInfoDict:
                        rodDict = __pondInfoDict[pondZone]
                    else:
                        rodDict = copy.deepcopy(__emptyRodDict)
                        __pondInfoDict[pondZone] = rodDict
                    for rodIndex, rarityDict in list(rodDict.items()):
                        if canBeCaughtByRod(genus, species, rodIndex):
                            fishList = rarityDict.setdefault(effectiveRarity, [])
                            fishList.append((genus, species))

for zone, rodDict in list(__pondInfoDict.items()):
    for rodIndex, anywhereRarityDict in list(__anywhereDict.items()):
        for rarity, anywhereFishList in list(anywhereRarityDict.items()):
            rarityDict = rodDict[rodIndex]
            fishList = rarityDict.setdefault(rarity, [])
            fishList.extend(anywhereFishList)

def getPondDict(zoneId):
    print(__pondInfoDict[zoneId])


def getTotalNumFish():
    return __totalNumFish


def testRarity(rodId = 0, numIter = 100000):
    d = {1: 0,
     2: 0,
     3: 0,
     4: 0,
     5: 0,
     6: 0,
     7: 0,
     8: 0,
     9: 0,
     10: 0}
    for i in range(numIter):
        v = __rollRarityDice(rodId)
        d[v] += 1

    for rarity, count in list(d.items()):
        percentage = count / float(numIter) * 100
        d[rarity] = percentage

    print(d)


def getRandomFish():
    genus = random.choice(list(__fishDict.keys()))
    species = random.randint(0, len(__fishDict[genus]) - 1)
    return (genus, species)


def getPondInfo():
    return __pondInfoDict


def getSimplePondInfo():
    info = {}
    for pondId, pondInfo in list(__pondInfoDict.items()):
        pondFishList = []
        for rodId, rodInfo in list(pondInfo.items()):
            for rarity, fishList in list(rodInfo.items()):
                for fish in fishList:
                    if fish not in pondFishList:
                        pondFishList.append(fish)

        pondFishList.sort()
        info[pondId] = pondFishList

    return info


def getPondGeneraList(pondId):
    tmpList = []
    generaList = []
    pondInfo = getSimplePondInfo()
    for fish in pondInfo[pondId]:
        if fish[0] not in tmpList:
            tmpList.append(fish[0])
            generaList.append(fish)

    return generaList


def printNumGeneraPerPond():
    pondInfo = getSimplePondInfo()
    for pondId, fishList in list(pondInfo.items()):
        generaList = []
        for fish in fishList:
            if fish[0] not in generaList:
                generaList.append(fish[0])

        print('Pond %s has %s Genera' % (pondId, len(generaList)))


def generateFishingReport(numCasts = 10000, hitRate = 0.8):
    totalPondMoney = {}
    totalRodMoney = {}
    totalPondBaitCost = {}
    for pond in __pondInfoDict:
        totalPondMoney[pond] = 0
        totalPondBaitCost[pond] = 0
        for rod in range(MaxRodId + 1):
            totalRodMoney.setdefault(rod, 0)
            baitCost = getCastCost(rod)
            for cast in range(numCasts):
                totalPondBaitCost[pond] += baitCost
                if random.random() > hitRate:
                    continue
                rand = random.random() * 100.0
                for cutoff in SortedProbabilityCutoffs:
                    if rand <= cutoff:
                        itemType = ProbabilityDict[cutoff]
                        break

                if itemType == FishItem:
                    success, genus, species, weight = getRandomFishVitals(pond, rod)
                    if success:
                        value = getValue(genus, species, weight)
                        totalPondMoney[pond] += value
                        totalRodMoney[rod] += value
                elif itemType == JellybeanItem:
                    value = Rod2JellybeanDict[rod]
                    totalPondMoney[pond] += value
                    totalRodMoney[rod] += value

    numPonds = len(totalPondMoney)
    for pond, money in list(totalPondMoney.items()):
        baitCost = 0
        for rod in range(MaxRodId + 1):
            baitCost += getCastCost(rod)

        totalCastCost = baitCost * numCasts
        print(('pond: %s  totalMoney: %s profit: %s perCast: %s' % (pond,
          money,
          money - totalCastCost,
          (money - totalCastCost) / float(numCasts * (MaxRodId + 1))),))

    for rod, money in list(totalRodMoney.items()):
        baitCost = getCastCost(rod)
        totalCastCost = baitCost * (numCasts * numPonds)
        print(('rod: %s totalMoney: %s castCost: %s profit: %s perCast: %s' % (rod,
          money,
          totalCastCost,
          money - totalCastCost,
          (money - totalCastCost) / float(numCasts * numPonds)),))
