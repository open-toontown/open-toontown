from toontown.toonbase.ToontownGlobals import *
from direct.directnotify import DirectNotifyGlobal
zoneUtilNotify = DirectNotifyGlobal.directNotify.newCategory('ZoneUtil')
tutorialDict = None

def isGoofySpeedwayZone(zoneId):
    return zoneId == 8000


def isCogHQZone(zoneId):
    return zoneId >= 10000 and zoneId < 15000


def isMintInteriorZone(zoneId):
    return zoneId in (CashbotMintIntA, CashbotMintIntB, CashbotMintIntC)


def isDynamicZone(zoneId):
    return zoneId >= DynamicZonesBegin and zoneId < DynamicZonesEnd


def getStreetName(branchId):
    global tutorialDict
    if tutorialDict:
        return StreetNames[20000][-1]
    else:
        return StreetNames[branchId][-1]


def getLoaderName(zoneId):
    if tutorialDict:
        if zoneId == ToontownCentral:
            loaderName = 'safeZoneLoader'
        else:
            loaderName = 'townLoader'
    else:
        suffix = zoneId % 1000
        if suffix >= 500:
            suffix -= 500
        if isCogHQZone(zoneId):
            loaderName = 'cogHQLoader'
        elif suffix < 100:
            loaderName = 'safeZoneLoader'
        else:
            loaderName = 'townLoader'
    return loaderName


def getBranchLoaderName(zoneId):
    return getLoaderName(getBranchZone(zoneId))


def getSuitWhereName(zoneId):
    where = getWhereName(zoneId, 0)
    return where


def getToonWhereName(zoneId):
    where = getWhereName(zoneId, 1)
    return where


def isPlayground(zoneId):
    whereName = getWhereName(zoneId, False)
    if whereName == 'cogHQExterior':
        return True
    else:
        return zoneId % 1000 == 0 and zoneId < DynamicZonesBegin


def isPetshop(zoneId):
    if zoneId == 2522 or zoneId == 1510 or zoneId == 3511 or zoneId == 4508 or zoneId == 5505 or zoneId == 9508:
        return True
    return False


def getWhereName(zoneId, isToon):
    if tutorialDict:
        if zoneId in tutorialDict['interiors']:
            where = 'toonInterior'
        elif zoneId in tutorialDict['exteriors']:
            where = 'street'
        elif zoneId == ToontownCentral or zoneId == WelcomeValleyToken:
            where = 'playground'
        else:
            zoneUtilNotify.error('No known zone: ' + str(zoneId))
    else:
        suffix = zoneId % 1000
        suffix = suffix - suffix % 100
        if isCogHQZone(zoneId):
            if suffix == 0:
                where = 'cogHQExterior'
            elif suffix == 100:
                where = 'cogHQLobby'
            elif suffix == 200:
                where = 'factoryExterior'
            elif getHoodId(zoneId) == LawbotHQ and suffix in (300, 400, 500, 600):
                where = 'stageInterior'
            elif getHoodId(zoneId) == BossbotHQ and suffix in (500, 600, 700):
                where = 'countryClubInterior'
            elif suffix >= 500:
                if getHoodId(zoneId) == SellbotHQ:
                    where = 'factoryInterior'
                elif getHoodId(zoneId) == CashbotHQ:
                    where = 'mintInterior'
                else:
                    zoneUtilNotify.error('unknown cogHQ interior for hood: ' + str(getHoodId(zoneId)))
            else:
                zoneUtilNotify.error('unknown cogHQ where: ' + str(zoneId))
        elif suffix == 0:
            where = 'playground'
        elif suffix >= 500:
            if isToon:
                where = 'toonInterior'
            else:
                where = 'suitInterior'
        else:
            where = 'street'
    return where


def getBranchZone(zoneId):
    if tutorialDict:
        branchId = tutorialDict['branch']
    else:
        branchId = zoneId - zoneId % 100
        if not isCogHQZone(zoneId):
            if zoneId % 1000 >= 500:
                branchId -= 500
    return branchId


def getCanonicalBranchZone(zoneId):
    return getBranchZone(getCanonicalZoneId(zoneId))


def isWelcomeValley(zoneId):
    return zoneId == WelcomeValleyToken or zoneId >= WelcomeValleyBegin and zoneId < WelcomeValleyEnd


def getCanonicalZoneId(zoneId):
    if zoneId == WelcomeValleyToken:
        zoneId = ToontownCentral
    elif zoneId >= WelcomeValleyBegin and zoneId < WelcomeValleyEnd:
        zoneId = zoneId % 2000
        if zoneId < 1000:
            zoneId = zoneId + ToontownCentral
        else:
            zoneId = zoneId - 1000 + GoofySpeedway
    return zoneId


def getTrueZoneId(zoneId, currentZoneId):
    if zoneId >= WelcomeValleyBegin and zoneId < WelcomeValleyEnd or zoneId == WelcomeValleyToken:
        zoneId = getCanonicalZoneId(zoneId)
    if currentZoneId >= WelcomeValleyBegin and currentZoneId < WelcomeValleyEnd:
        hoodId = getHoodId(zoneId)
        offset = currentZoneId - currentZoneId % 2000
        if hoodId == ToontownCentral:
            return zoneId - ToontownCentral + offset
        elif hoodId == GoofySpeedway:
            return zoneId - GoofySpeedway + offset + 1000
    return zoneId


def getHoodId(zoneId):
    if tutorialDict:
        hoodId = Tutorial
    else:
        hoodId = zoneId - zoneId % 1000
    return hoodId


def getSafeZoneId(zoneId):
    hoodId = getHoodId(zoneId)
    if hoodId in HQToSafezone:
        hoodId = HQToSafezone[hoodId]
    return hoodId


def getCanonicalHoodId(zoneId):
    return getHoodId(getCanonicalZoneId(zoneId))


def getCanonicalSafeZoneId(zoneId):
    return getSafeZoneId(getCanonicalZoneId(zoneId))


def isInterior(zoneId):
    if tutorialDict:
        if zoneId in tutorialDict['interiors']:
            r = 1
        else:
            r = 0
    else:
        r = zoneId % 1000 >= 500
    return r


def overrideOn(branch, exteriorList, interiorList):
    global tutorialDict
    if tutorialDict:
        zoneUtilNotify.warning('setTutorialDict: tutorialDict is already set!')
    tutorialDict = {'branch': branch,
     'exteriors': exteriorList,
     'interiors': interiorList}


def overrideOff():
    global tutorialDict
    tutorialDict = None
    return


def getWakeInfo(hoodId = None, zoneId = None):
    wakeWaterHeight = 0
    showWake = 0
    try:
        if hoodId is None:
            hoodId = base.cr.playGame.getPlaceId()
        if zoneId is None:
            zoneId = base.cr.playGame.getPlace().getZoneId()
        canonicalZoneId = getCanonicalZoneId(zoneId)
        if canonicalZoneId == DonaldsDock:
            wakeWaterHeight = DDWakeWaterHeight
            showWake = 1
        elif canonicalZoneId == ToontownCentral:
            wakeWaterHeight = TTWakeWaterHeight
            showWake = 1
        elif canonicalZoneId == OutdoorZone:
            wakeWaterHeight = OZWakeWaterHeight
            showWake = 1
        elif hoodId == MyEstate:
            wakeWaterHeight = EstateWakeWaterHeight
            showWake = 1
    except AttributeError:
        pass

    return (showWake, wakeWaterHeight)
