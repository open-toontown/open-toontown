from direct.directnotify import DirectNotifyGlobal
from direct.showbase import PythonUtil
from toontown.toonbase import TTLocalizer
from pandac.PandaModules import *
from KartShopGlobals import *
import types
if (__debug__):
    import pdb
import copy
KartDNA = PythonUtil.Enum('bodyType, bodyColor, accColor,                             ebType, spType, fwwType,                             bwwType, rimsType, decalType')
InvalidEntry = -1
KartInfo = PythonUtil.Enum('name, model, cost, viewDist, decalId, LODmodel1, LODmodel2')
AccInfo = PythonUtil.Enum('name, model, cost, texCard, attach')
kNames = TTLocalizer.KartDNA_KartNames
KartDict = {0: (kNames[0],
     'phase_6/models/karting/Kart1_Final',
     100,
     7.0,
     'kart1',
     'phase_6/models/karting/Kart1_LOD_Final',
     'phase_6/models/karting/Kart1_LOD_Final',
     (Point3(1.5, 8.0, -0.5), Point3(1.5, 0.0, 2.0))),
 1: (kNames[1],
     'phase_6/models/karting/Kart2_Final',
     7500,
     7.0,
     'kart2',
     'phase_6/models/karting/Kart2_LOD2_Final',
     'phase_6/models/karting/Kart2_LOD3_Final',
     (Point3(0.25, 7, -2), Point3(1.25, -3, 0))),
 2: (kNames[2],
     'phase_6/models/karting/Kart3_Final',
     2500,
     8.5,
     'kart3',
     'phase_6/models/karting/Kart3_Final_LOD2',
     'phase_6/models/karting/Kart3_Final_LOD3',
     (Point3(1.25, 4.0, 1.0), Point3(1.25, -3.0, 2.5)))}
aNames = TTLocalizer.KartDNA_AccNames
AccessoryDict = {0: (aNames[1000],
     'phase_6/models/karting/accessory_frontMiddle_0',
     200,
     'accessory_frontMiddle_0_gui',
     'ebNode_0'),
 1: (aNames[1001],
     'phase_6/models/karting/accessory_frontMiddle_1',
     1250,
     'accessory_frontMiddle_1_gui',
     'ebNode_0'),
 2: (aNames[1002],
     'phase_6/models/karting/accessory_frontMiddle_2',
     450,
     'accessory_frontMiddle_2_gui',
     'ebNode_1'),
 3: (aNames[1003],
     'phase_6/models/karting/accessory_frontMiddle_3',
     5000,
     'accessory_frontMiddle_3_gui',
     'ebNode_1'),
 4: (aNames[1004],
     'phase_6/models/karting/accessory_frontMiddle_4',
     800,
     'accessory_frontMiddle_4_gui',
     'ebNode_0'),
 5: (aNames[1005],
     'phase_6/models/karting/accessory_frontMiddle_5',
     200,
     'accessory_frontMiddle_5_gui',
     'ebNode_0'),
 6: (aNames[1006],
     'phase_6/models/karting/accessory_frontMiddle_6',
     450,
     'accessory_frontMiddle_6_gui',
     'ebNode_0'),
 7: (aNames[1007],
     'phase_6/models/karting/accessory_frontMiddle_7',
     800,
     'accessory_frontMiddle_7_gui',
     'ebNode_0'),
 8: (aNames[1008],
     'phase_6/models/karting/accessory_frontMiddle_8',
     200,
     'accessory_frontMiddle_8_gui',
     'ebNode_1'),
 9: (aNames[1009],
     'phase_6/models/karting/accessory_frontMiddle_9',
     800,
     'accessory_frontMiddle_9_gui',
     'ebNode_1'),
 10: (aNames[1010],
      'phase_6/models/karting/accessory_frontMiddle_10',
      1250,
      'accessory_frontMiddle_10_gui',
      'ebNode_0'),
 11: (aNames[2000],
      'phase_6/models/karting/accessory_backMiddle_0',
      450,
      'accessory_backMiddle_0_gui',
      'spNode_1'),
 12: (aNames[2001],
      'phase_6/models/karting/accessory_backMiddle_1',
      200,
      'accessory_backMiddle_1_gui',
      'spNode_0'),
 13: (aNames[2002],
      'phase_6/models/karting/accessory_backMiddle_2',
      800,
      'accessory_backMiddle_2_gui',
      'spNode_1'),
 14: (aNames[2003],
      'phase_6/models/karting/accessory_backMiddle_3',
      1250,
      'accessory_backMiddle_3_gui',
      'spNode_1'),
 15: (aNames[2004],
      'phase_6/models/karting/accessory_backMiddle_4',
      5000,
      'accessory_backMiddle_4_gui',
      'spNode_1'),
 16: (aNames[2005],
      'phase_6/models/karting/accessory_backMiddle_5',
      800,
      'accessory_backMiddle_5_gui',
      'spNode_1'),
 17: (aNames[2006],
      'phase_6/models/karting/accessory_backMiddle_6',
      450,
      'accessory_backMiddle_6_gui',
      'spNode_0'),
 18: (aNames[2007],
      'phase_6/models/karting/accessory_backMiddle_7',
      1250,
      'accessory_backMiddle_7_gui',
      'spNode_1'),
 19: (aNames[3000],
      'phase_6/models/karting/accessory_front_ww_0',
      200,
      'accessory_front_ww_0_gui',
      '%sFWWNode_0'),
 20: (aNames[3001],
      'phase_6/models/karting/accessory_front_ww_1',
      200,
      'accessory_front_ww_1_gui',
      '%sFWWNode_1'),
 21: (aNames[3002],
      'phase_6/models/karting/accessory_front_ww_2',
      800,
      'accessory_front_ww_2_gui',
      '%sFWWNode_2'),
 22: (aNames[3003],
      'phase_6/models/karting/accessory_front_ww_3',
      5000,
      'accessory_front_ww_3_gui',
      '%sFWWNode_2'),
 23: (aNames[3004],
      'phase_6/models/karting/accessory_front_ww_4',
      1250,
      'accessory_front_ww_4_gui',
      '%sFWWNode_2'),
 24: (aNames[3005],
      'phase_6/models/karting/accessory_front_ww_5',
      800,
      'accessory_front_ww_5_gui',
      '%sFWWNode_1'),
 25: (aNames[3006],
      'phase_6/models/karting/accessory_front_ww_6',
      1250,
      'accessory_front_ww_6_gui',
      '%sFWWNode_2'),
 26: (aNames[3007],
      'phase_6/models/karting/accessory_front_ww_7',
      450,
      'accessory_front_ww_7_gui',
      '%sFWWNode_2'),
 27: (aNames[4000],
      'phase_6/models/karting/accessory_rear_ww_0',
      800,
      'accessory_rear_ww_0_gui',
      '%sBWWNode_0'),
 28: (aNames[4001],
      'phase_6/models/karting/accessory_rear_ww_1',
      200,
      'accessory_rear_ww_1_gui',
      '%sBWWNode_1'),
 29: (aNames[4002],
      'phase_6/models/karting/accessory_rear_ww_2',
      200,
      'accessory_rear_ww_2_gui',
      '%sBWWNode_2'),
 30: (aNames[4003],
      'phase_6/models/karting/accessory_rear_ww_3',
      1250,
      'accessory_rear_ww_3_gui',
      '%sBWWNode_0'),
 31: (aNames[4004],
      'phase_6/models/karting/accessory_rear_ww_4',
      200,
      'accessory_rear_ww_4_gui',
      '%sBWWNode_2'),
 32: (aNames[4005],
      'phase_6/models/karting/accessory_rear_ww_5',
      800,
      'accessory_rear_ww_5_gui',
      '%sBWWNode_2'),
 33: (aNames[4006],
      'phase_6/models/karting/accessory_rear_ww_6',
      450,
      'accessory_rear_ww_6_gui',
      '%sBWWNode_2'),
 34: (aNames[4007],
      'phase_6/models/karting/accessory_rear_ww_7',
      5000,
      'accessory_rear_ww_7_gui',
      '%sBWWNode_2'),
 35: (aNames[4008],
      'phase_6/models/karting/accessory_rear_ww_8',
      1250,
      'accessory_rear_ww_8_gui',
      '%sBWWNode_0'),
 36: (aNames[4009],
      'phase_6/models/karting/accessory_rear_ww_9',
      1250,
      'accessory_rear_ww_9_gui',
      '%sBWWNode_0'),
 37: (aNames[4010],
      'phase_6/models/karting/accessory_rear_ww_10',
      450,
      'accessory_rear_ww_10_gui',
      '%sBWWNode_2'),
 38: (aNames[4011],
      'phase_6/models/karting/accessory_rear_ww_11',
      800,
      'accessory_rear_ww_11_gui',
      '%sBWWNode_2'),
 39: (aNames[4012],
      'phase_6/models/karting/accessory_rear_ww_12',
      1250,
      'accessory_rear_ww_12_gui',
      '%sBWWNode_2'),
 40: (aNames[5000],
      'phase_6/maps/kart_Rim_1',
      InvalidEntry,
      'kart_Rim_1'),
 41: (aNames[5001],
      'phase_6/maps/kart_Rim_2',
      450,
      'kart_Rim_2'),
 42: (aNames[5002],
      'phase_6/maps/kart_Rim_3',
      100,
      'kart_Rim_3'),
 43: (aNames[5003],
      'phase_6/maps/kart_Rim_4',
      800,
      'kart_Rim_4'),
 44: (aNames[5004],
      'phase_6/maps/kart_Rim_5',
      100,
      'kart_Rim_5'),
 45: (aNames[5005],
      'phase_6/maps/kart_Rim_6',
      200,
      'kart_Rim_6'),
 46: (aNames[5006],
      'phase_6/maps/kart_Rim_7',
      200,
      'kart_Rim_7'),
 47: (aNames[5007],
      'phase_6/maps/kart_Rim_8',
      200,
      'kart_Rim_8'),
 48: (aNames[5008],
      'phase_6/maps/kart_Rim_9',
      200,
      'kart_Rim_9'),
 49: (aNames[5009],
      'phase_6/maps/kart_Rim_10',
      200,
      'kart_Rim_10'),
 50: (aNames[5010],
      'phase_6/maps/kart_Rim_11',
      200,
      'kart_Rim_11'),
 51: (aNames[5011],
      'phase_6/maps/kart_Rim_12',
      800,
      'kart_Rim_12'),
 52: (aNames[5012],
      'phase_6/maps/kart_Rim_13',
      450,
      'kart_Rim_13'),
 53: (aNames[5013],
      'phase_6/maps/kart_Rim_14',
      1250,
      'kart_Rim_14'),
 54: (aNames[5014],
      'phase_6/maps/kart_Rim_15',
      5000,
      'kart_Rim_15'),
 55: (aNames[6000],
      1,
      200,
      '%s_SideDecal_1'),
 56: (aNames[6001],
      2,
      450,
      '%s_SideDecal_2'),
 57: (aNames[6002],
      3,
      100,
      '%s_SideDecal_3'),
 58: (aNames[6003],
      4,
      5000,
      '%s_SideDecal_4'),
 59: (aNames[6004],
      5,
      200,
      '%s_SideDecal_5'),
 60: (aNames[6005],
      6,
      200,
      '%s_SideDecal_6'),
 61: (aNames[6006],
      7,
      450,
      '%s_SideDecal_7'),
 62: (aNames[6007],
      8,
      100,
      '%s_SideDecal_8'),
 63: (aNames[6008],
      9,
      1250,
      '%s_SideDecal_9'),
 64: (aNames[6009],
      10,
      800,
      '%s_SideDecal_10'),
 65: (aNames[7000], VBase4(0.8, 1.0, 0.5, 1.0), 100),
 66: (aNames[7001], VBase4(0.96875, 0.691406, 0.699219, 1.0), 100),
 67: (aNames[7002], VBase4(0.933594, 0.265625, 0.28125, 1.0), 2500),
 68: (aNames[7003], VBase4(0.863281, 0.40625, 0.417969, 1.0), 900),
 69: (aNames[7004], VBase4(0.710938, 0.234375, 0.4375, 1.0), 1600),
 70: (aNames[7005], VBase4(0.570312, 0.449219, 0.164062, 1.0), 1600),
 71: (aNames[7006], VBase4(0.640625, 0.355469, 0.269531, 1.0), 1600),
 72: (aNames[7007], VBase4(0.996094, 0.695312, 0.511719, 1.0), 100),
 73: (aNames[7008], VBase4(0.832031, 0.5, 0.296875, 1.0), 1600),
 74: (aNames[7009], VBase4(0.992188, 0.480469, 0.167969, 1.0), 1600),
 75: (aNames[7010], VBase4(0.996094, 0.898438, 0.320312, 1.0), 2500),
 76: (aNames[7011], VBase4(0.996094, 0.957031, 0.597656, 1.0), 900),
 77: (aNames[7012], VBase4(0.855469, 0.933594, 0.492188, 1.0), 900),
 78: (aNames[7013], VBase4(0.550781, 0.824219, 0.324219, 1.0), 900),
 79: (aNames[7014], VBase4(0.242188, 0.742188, 0.515625, 1.0), 1600),
 80: (aNames[7015], VBase4(0.304688, 0.96875, 0.402344, 1.0), 2500),
 81: (aNames[7016], VBase4(0.433594, 0.90625, 0.835938, 1.0), 900),
 82: (aNames[7017], VBase4(0.347656, 0.820312, 0.953125, 1.0), 900),
 83: (aNames[7018], VBase4(0.191406, 0.5625, 0.773438, 1.0), 1600),
 84: (aNames[7019], VBase4(0.558594, 0.589844, 0.875, 1.0), 900),
 85: (aNames[7020], VBase4(0.285156, 0.328125, 0.726562, 1.0), 2500),
 86: (aNames[7021], VBase4(0.460938, 0.378906, 0.824219, 1.0), 900),
 87: (aNames[7022], VBase4(0.546875, 0.28125, 0.75, 1.0), 1600),
 88: (aNames[7023], VBase4(0.726562, 0.472656, 0.859375, 1.0), 1600),
 89: (aNames[7024], VBase4(0.898438, 0.617188, 0.90625, 1.0), 1600),
 90: (aNames[7025], VBase4(0.7, 0.7, 0.8, 1.0), 2500),
 91: (aNames[7026], VBase4(0.3, 0.3, 0.35, 1.0), 10000)}
AccessoryTypeDict = {KartDNA.ebType: [0,
                  1,
                  2,
                  3,
                  4,
                  5,
                  6,
                  7,
                  8,
                  9,
                  10],
 KartDNA.spType: [11,
                  12,
                  13,
                  14,
                  15,
                  16,
                  17,
                  18],
 KartDNA.fwwType: [19,
                   20,
                   21,
                   22,
                   23,
                   24,
                   25,
                   26],
 KartDNA.bwwType: [27,
                   28,
                   29,
                   30,
                   31,
                   32,
                   33,
                   34,
                   35,
                   36,
                   37,
                   38,
                   39],
 KartDNA.rimsType: [40,
                    41,
                    42,
                    43,
                    44,
                    45,
                    46,
                    47,
                    48,
                    49,
                    50,
                    51,
                    52,
                    53,
                    54],
 KartDNA.decalType: [55,
                     56,
                     57,
                     58,
                     59,
                     60,
                     61,
                     62,
                     63,
                     64],
 KartDNA.bodyColor: [65,
                     66,
                     67,
                     68,
                     69,
                     70,
                     71,
                     72,
                     73,
                     74,
                     75,
                     76,
                     77,
                     78,
                     79,
                     80,
                     81,
                     82,
                     83,
                     84,
                     85,
                     86,
                     87,
                     88,
                     89,
                     90,
                     91]}
AccessoryTypeNameDict = [None,
 'KartShtikerBodyColor',
 'KartShtikerAccColor',
 'KartShtikerEngineBlock',
 'KartShtikerSpoiler',
 'KartShtikerFrontWheelWell',
 'KartShtikerBackWheelWell',
 'KartShtikerRim',
 'KartShtikerDecal']

def checkNumFieldsValidity(numFields):
    return KartDNA.decalType == numFields - 1


def checkKartFieldValidity(field):
    if field < KartDNA.bodyType or field > KartDNA.decalType:
        return 0
    return 1


def getNumFields():
    return KartDNA.decalType + 1


def getKartModelPath(kartType, lodLevel = 0):
    if lodLevel == 1:
        return KartDict.get(kartType)[KartInfo.LODmodel1]
    if lodLevel == 2:
        return KartDict.get(kartType)[KartInfo.LODmodel2]
    return KartDict.get(kartType)[KartInfo.model]


def getKartViewDist(kartType):
    return KartDict.get(kartType)[KartInfo.viewDist]


def getDecalId(kartType):
    return KartDict.get(kartType)[KartInfo.decalId]


def getAccessory(accId):
    return AccessoryDict.get(accId)[KartInfo.model]


def getAccessoryAttachNode(accId):
    accInfo = AccessoryDict.get(accId)
    if len(accInfo) == 5:
        return accInfo[4]
    return None


def getTexCardNode(accId):
    accInfo = AccessoryDict.get(accId)
    if len(accInfo) <= 5:
        return accInfo[3]
    return None


def checkKartDNAValidity(dna):
    if not checkNumFieldsValidity(len(dna)):
        return 0
    for field in xrange(len(dna)):
        if field == KartDNA.bodyType:
            if dna[field] not in KartDict.keys():
                return 0
        elif field == KartDNA.bodyColor or field == KartDNA.accColor:
            accList = [InvalidEntry] + AccessoryTypeDict.get(KartDNA.bodyColor)
            if dna[field] not in accList:
                return 0
        else:
            accList = [InvalidEntry] + AccessoryTypeDict.get(field)
            if dna[field] not in accList:
                return 0

    return 1


def getDefaultColor():
    return VBase4(1, 1, 1, 1)


def getDefaultRim():
    return AccessoryTypeDict[KartDNA.rimsType][0]


def getDefaultAccessory(category):
    if category in [KartDNA.bodyColor, KartDNA.accColor]:
        return getDefaultColor()
    elif category == KartDNA.rimsType:
        return getDefaultRim()
    else:
        return InvalidEntry


def getAccessoryItemList(accessoryType):
    return [ AccessoryDict[itemId] for itemId in AccessoryTypeDict[accessoryType] ]


def getKartTypeInfo(type):
    if type in KartDict.keys():
        return KartDict[type]
    return InvalidEntry


def getAccessoryInfo(index):
    if index in AccessoryDict.keys():
        return AccessoryDict[index]
    return InvalidEntry


def getAccessoryType(accessoryId):
    for key in AccessoryTypeDict.keys():
        if accessoryId in AccessoryTypeDict[key]:
            return key

    return InvalidEntry


def getAccessoryDictFromOwned(accessoryOwnedList, pType = -1):
    accessDict = copy.deepcopy(AccessoryTypeDict)
    accessDict[KartDNA.rimsType].remove(getDefaultRim())
    for accOwnedId in accessoryOwnedList:
        type = getAccessoryType(accOwnedId)
        if type != InvalidEntry and accOwnedId in accessDict[type]:
            accessDict[type].remove(accOwnedId)

    if pType != -1:
        return accessDict[pType]
    else:
        return accessDict


def getAccessDictByType(accessoryOwnedList):
    accessDict = {}
    if type(accessoryOwnedList) == types.ListType:
        for accOwnedId in accessoryOwnedList:
            accType = getAccessoryType(accOwnedId)
            if accType != InvalidEntry:
                if not accessDict.has_key(accType):
                    accessDict[accType] = []
                accessDict[accType].append(accOwnedId)

    else:
        print 'KartDNA: getAccessDictByType: bad accessory list: ', accessoryOwnedList
    return accessDict


def getKartCost(kartID):
    if KartDict.has_key(kartID):
        return KartDict[kartID][KartInfo.cost]
    else:
        return 'key error'


def getAccCost(accID):
    return AccessoryDict[accID][AccInfo.cost]


def getAccName(accID):
    try:
        return AccessoryDict[accID][AccInfo.name]
    except:
        return TTLocalizer.KartShtikerDefault
