from toontown.toon import ToonDNA
from pandac.PandaModules import VBase4
from toontown.toonbase import TTLocalizer, ToontownGlobals
from direct.showbase import PythonUtil
NumFields = 9
Fields = {'head': 0,
 'ears': 1,
 'nose': 2,
 'tail': 3,
 'body': 4,
 'color': 5,
 'colorScale': 6,
 'eyes': 7,
 'gender': 8}
HeadParts = ['feathers']
EarParts = ['horns',
 'antennae',
 'dogEars',
 'catEars',
 'rabbitEars']
EarTextures = {'horns': None,
 'antennae': None,
 'dogEars': None,
 'catEars': 'phase_4/maps/BeanCatEar6.jpg',
 'rabbitEars': 'phase_4/maps/BeanBunnyEar6.jpg'}
ExoticEarTextures = {'horns': None,
 'antennae': None,
 'dogEars': None,
 'catEars': 'phase_4/maps/BeanCatEar3Yellow.jpg',
 'rabbitEars': 'phase_4/maps/BeanBunnyEar6.jpg'}
NoseParts = ['clownNose',
 'dogNose',
 'ovalNose',
 'pigNose']
TailParts = ['catTail',
 'longTail',
 'birdTail',
 'bunnyTail']
TailTextures = {'catTail': 'phase_4/maps/beanCatTail6.jpg',
 'longTail': 'phase_4/maps/BeanLongTail6.jpg',
 'birdTail': None,
 'bunnyTail': None}
GiraffeTail = 'phase_4/maps/BeanLongTailGiraffe.jpg'
LeopardTail = 'phase_4/maps/BeanLongTailLepord.jpg'
GenericBodies = ['dots',
 'threeStripe',
 'tigerStripe',
 'tummy']
SpecificBodies = ['turtle', 'giraffe', 'leopard']
BodyTypes = GenericBodies + SpecificBodies
PetRarities2 = (('leopard', 0.005),
 ('giraffe', 0.015),
 ('turtle', 0.045),
 ('tigerStripe', 0.115),
 ('dots', 0.265),
 ('tummy', 0.525),
 ('threeStripe', 1.0))
PetRarities = {'body': {ToontownGlobals.ToontownCentral: {'threeStripe': 50,
                                            'tummy': 30,
                                            'dots': 20},
          ToontownGlobals.DonaldsDock: {'threeStripe': 35,
                                        'tummy': 30,
                                        'dots': 20,
                                        'tigerStripe': 15},
          ToontownGlobals.DaisyGardens: {'threeStripe': 15,
                                         'tummy': 20,
                                         'dots': 20,
                                         'tigerStripe': 20,
                                         'turtle': 15},
          ToontownGlobals.MinniesMelodyland: {'threeStripe': 10,
                                              'tummy': 15,
                                              'dots': 30,
                                              'tigerStripe': 25,
                                              'turtle': 20},
          ToontownGlobals.TheBrrrgh: {'threeStripe': 5,
                                      'tummy': 10,
                                      'dots': 20,
                                      'tigerStripe': 25,
                                      'turtle': 25,
                                      'giraffe': 15},
          ToontownGlobals.DonaldsDreamland: {'threeStripe': 5,
                                             'tummy': 5,
                                             'dots': 15,
                                             'tigerStripe': 20,
                                             'turtle': 25,
                                             'giraffe': 20,
                                             'leopard': 10}}}
BodyTextures = {'dots': 'phase_4/maps/BeanbodyDots6.jpg',
 'threeStripe': 'phase_4/maps/Beanbody3stripes6.jpg',
 'tigerStripe': 'phase_4/maps/BeanbodyZebraStripes6.jpg',
 'turtle': 'phase_4/maps/BeanbodyTurtle.jpg',
 'giraffe': 'phase_4/maps/BeanbodyGiraffe1.jpg',
 'leopard': 'phase_4/maps/BeanbodyLepord2.jpg',
 'tummy': 'phase_4/maps/BeanbodyTummy6.jpg'}
FeetTextures = {'normal': 'phase_4/maps/BeanFoot6.jpg',
 'turtle': 'phase_4/maps/BeanFootTurttle.jpg',
 'giraffe': 'phase_4/maps/BeanFootYellow3.jpg',
 'leopard': 'phase_4/maps/BeanFootYellow3.jpg'}
AllPetColors = (VBase4(1.0, 1.0, 1.0, 1.0),
 VBase4(0.96875, 0.691406, 0.699219, 1.0),
 VBase4(0.933594, 0.265625, 0.28125, 1.0),
 VBase4(0.863281, 0.40625, 0.417969, 1.0),
 VBase4(0.710938, 0.234375, 0.4375, 1.0),
 VBase4(0.570312, 0.449219, 0.164062, 1.0),
 VBase4(0.640625, 0.355469, 0.269531, 1.0),
 VBase4(0.996094, 0.695312, 0.511719, 1.0),
 VBase4(0.832031, 0.5, 0.296875, 1.0),
 VBase4(0.992188, 0.480469, 0.167969, 1.0),
 VBase4(0.996094, 0.898438, 0.320312, 1.0),
 VBase4(0.996094, 0.957031, 0.597656, 1.0),
 VBase4(0.855469, 0.933594, 0.492188, 1.0),
 VBase4(0.550781, 0.824219, 0.324219, 1.0),
 VBase4(0.242188, 0.742188, 0.515625, 1.0),
 VBase4(0.304688, 0.96875, 0.402344, 1.0),
 VBase4(0.433594, 0.90625, 0.835938, 1.0),
 VBase4(0.347656, 0.820312, 0.953125, 1.0),
 VBase4(0.191406, 0.5625, 0.773438, 1.0),
 VBase4(0.558594, 0.589844, 0.875, 1.0),
 VBase4(0.285156, 0.328125, 0.726562, 1.0),
 VBase4(0.460938, 0.378906, 0.824219, 1.0),
 VBase4(0.546875, 0.28125, 0.75, 1.0),
 VBase4(0.726562, 0.472656, 0.859375, 1.0),
 VBase4(0.898438, 0.617188, 0.90625, 1.0),
 VBase4(0.7, 0.7, 0.8, 1.0))
GenericPetColors = [0,
 1,
 3,
 5,
 6,
 7,
 8,
 9,
 10,
 11,
 12,
 13,
 14,
 15,
 16,
 17,
 18,
 19,
 21,
 22,
 23,
 24,
 25]
SpecificPetColors = [0,
 1,
 3,
 5,
 6,
 7,
 8,
 9,
 10,
 11,
 12,
 16,
 17,
 18,
 23,
 24,
 25]
ColorScales = [0.8,
 0.85,
 0.9,
 0.95,
 1.0,
 1.05,
 1.1,
 1.15,
 1.2]
PetEyeColors = (VBase4(0.29, 0.29, 0.69, 1.0),
 VBase4(0.49, 0.49, 0.99, 1.0),
 VBase4(0.69, 0.49, 0.29, 1.0),
 VBase4(0.99, 0.69, 0.49, 1.0),
 VBase4(0.29, 0.69, 0.29, 1.0),
 VBase4(0.49, 0.99, 0.49, 1.0))
PetGenders = [0, 1]

def getRandomPetDNA(zoneId = ToontownGlobals.DonaldsDreamland):
    from random import choice
    head = choice(list(range(-1, len(HeadParts))))
    ears = choice(list(range(-1, len(EarParts))))
    nose = choice(list(range(-1, len(NoseParts))))
    tail = choice(list(range(-1, len(TailParts))))
    body = getSpecies(zoneId)
    color = choice(list(range(0, len(getColors(body)))))
    colorScale = choice(list(range(0, len(ColorScales))))
    eyes = choice(list(range(0, len(PetEyeColors))))
    gender = choice(list(range(0, len(PetGenders))))
    return [head,
     ears,
     nose,
     tail,
     body,
     color,
     colorScale,
     eyes,
     gender]


def getSpecies(zoneId):
    body = PythonUtil.weightedRand(PetRarities['body'][zoneId])
    return BodyTypes.index(body)


def getColors(bodyType):
    if BodyTypes[bodyType] in GenericBodies:
        return GenericPetColors
    else:
        return SpecificPetColors


def getFootTexture(bodyType):
    if BodyTypes[bodyType] == 'turtle':
        texName = FeetTextures['turtle']
    elif BodyTypes[bodyType] == 'giraffe':
        texName = FeetTextures['giraffe']
    elif BodyTypes[bodyType] == 'leopard':
        texName = FeetTextures['leopard']
    else:
        texName = FeetTextures['normal']
    return texName


def getEarTexture(bodyType, earType):
    if BodyTypes[bodyType] == 'giraffe' or BodyTypes[bodyType] == 'leopard':
        dict = ExoticEarTextures
    else:
        dict = EarTextures
    return dict[earType]


def getBodyRarity(bodyIndex):
    bodyName = BodyTypes[bodyIndex]
    totalWeight = 0.0
    weight = {}
    for zoneId in PetRarities['body']:
        for body in PetRarities['body'][zoneId]:
            totalWeight += PetRarities['body'][zoneId][body]
            if body in weight:
                weight[body] += PetRarities['body'][zoneId][body]
            else:
                weight[body] = PetRarities['body'][zoneId][body]

    minWeight = min(weight.values())
    rarity = (weight[bodyName] - minWeight) / (totalWeight - minWeight)
    return rarity


def getRarity(dna):
    body = dna[Fields['body']]
    rarity = getBodyRarity(body)
    return rarity


def getGender(dna):
    return dna[Fields['gender']]


def setGender(dna, gender):
    dna[Fields['gender']] = gender


def getGenderString(dna = None, gender = -1):
    if dna != None:
        gender = getGender(dna)
    if gender:
        return TTLocalizer.GenderShopBoyButtonText
    else:
        return TTLocalizer.GenderShopGirlButtonText
    return
