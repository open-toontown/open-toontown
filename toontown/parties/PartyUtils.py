import math
import time
import datetime
from direct.directnotify import DirectNotifyGlobal
from direct.interval.LerpInterval import LerpFunc
from panda3d.core import Vec3
from toontown.toonbase import TTLocalizer
from toontown.toonbase.ToontownTimer import ToontownTimer
from toontown.parties import PartyGlobals
notify = DirectNotifyGlobal.directNotify.newCategory('PartyUtils')

def getNewToontownTimer():
    timer = ToontownTimer()
    timer.hide()
    timer.posInTopRightCorner()
    timer.setColor(1, 1, 1, 0.75)
    return timer


def getPartyActivityIcon(activityIconsModel, activityName):
    activityIconsDict = {'PartyValentineDance': 'tt_t_ara_pty_iconDanceFloorValentine',
     'PartyValentineDance20': 'tt_t_ara_pty_iconDanceFloorValentine',
     'PartyValentineJukebox': 'tt_t_ara_pty_iconJukeboxValentine',
     'PartyValentineJukebox40': 'tt_t_ara_pty_iconJukeboxValentine',
     'PartyValentineTrampoline': 'tt_t_ara_pty_iconTrampolineValentine'}
    iconName = activityIconsDict.get(activityName)
    if iconName:
        icon = activityIconsModel.find('**/%s' % iconName)
    else:
        icon = activityIconsModel.find('**/%sIcon' % activityName)
    if icon.isEmpty():
        icon = activityIconsModel.find('**/PartyClockIcon')
        notify.warning("Couldn't find %sIcon in %s, using PartyClockIcon" % (activityName, activityIconsModel.getName()))
    return icon


def arcPosInterval(duration, object, pos, arcHeight, other):
    startPos = object.getPos()
    endPos = object.getParent().getRelativePoint(other, pos)
    startX = startPos.getX()
    startY = startPos.getY()
    startZ = startPos.getZ()
    dx = endPos.getX() - startPos.getX()
    dy = endPos.getY() - startPos.getY()
    dz = endPos.getZ() - startPos.getZ()

    def setArcPos(t):
        newX = startX + dx * t
        newY = startY + dy * t
        newZ = startZ + dz * t + arcHeight * (-(2.0 * t - 1.0) ** 2 + 1.0)
        object.setPos(newX, newY, newZ)

    return LerpFunc(setArcPos, duration=duration)


def formatDate(year, month, day):
    monthString = TTLocalizer.DateOfBirthEntryMonths[month - 1]
    return TTLocalizer.PartyDateFormat % {'mm': monthString,
     'dd': day,
     'yyyy': year}


def truncateTextOfLabelBasedOnWidth(directGuiObject, textToTruncate, maxWidth):
    text0 = directGuiObject.component('text0')
    tempNode = text0.textNode
    currentText = textToTruncate[:]
    scale = text0.getScale()[0]
    width = tempNode.calcWidth(currentText) * scale
    while width > maxWidth:
        currentText = currentText[:-1]
        width = tempNode.calcWidth(currentText) * scale

    directGuiObject['text'] = currentText
    if directGuiObject['text'] != textToTruncate:
        directGuiObject['text'] = '%s...' % directGuiObject['text']


def truncateTextOfLabelBasedOnMaxLetters(directGuiObject, textToTruncate, maxLetters):
    curStr = directGuiObject['text']
    if maxLetters < len(curStr):
        curStr = curStr[:maxLetters]
        curStr += '...'
        directGuiObject['text'] = curStr


def scaleTextOfGuiObjectBasedOnWidth(directGuiObject, textToScale, maxWidth):
    width = directGuiObject.getWidth()
    scale = 0.01
    while width > maxWidth:
        directGuiObject['text_scale'] = scale
        directGuiObject.resetFrameSize()
        width = directGuiObject.getWidth()
        scale += 0.005


def formatTime(hour, minute):
    meridiemString = TTLocalizer.PartyTimeFormatMeridiemAM
    if hour == 0:
        hour = 12
    elif hour > 11:
        meridiemString = TTLocalizer.PartyTimeFormatMeridiemPM
    if hour > 12:
        hour -= 12
    return TTLocalizer.PartyTimeFormat % (hour, minute, meridiemString)


SecondsInOneDay = 60 * 60 * 24

def getTimeDeltaInSeconds(td):
    result = td.days * SecondsInOneDay + td.seconds + td.microseconds / 1000000.0
    return result


def formatDateTime(dateTimeToShow, inLocalTime = False):
    if inLocalTime:
        curServerTime = base.cr.toontownTimeManager.getCurServerDateTime()
        ltime = time.localtime()
        localTime = datetime.datetime(year=ltime.tm_year, month=ltime.tm_mon, day=ltime.tm_mday, hour=ltime.tm_hour, minute=ltime.tm_min, second=ltime.tm_sec)
        naiveServerTime = curServerTime.replace(tzinfo=None)
        newTimeDelta = localTime - naiveServerTime
        localDifference = getTimeDeltaInSeconds(newTimeDelta)
        dateTimeToShow = dateTimeToShow + datetime.timedelta(seconds=localDifference)
        return '%s %s' % (formatDate(dateTimeToShow.year, dateTimeToShow.month, dateTimeToShow.day), formatTime(dateTimeToShow.hour, dateTimeToShow.minute))
    else:
        return '%s %s' % (formatDate(dateTimeToShow.year, dateTimeToShow.month, dateTimeToShow.day), formatTime(dateTimeToShow.hour, dateTimeToShow.minute))
    return


def convertDistanceToPartyGrid(d, index):
    return int((d - PartyGlobals.PartyGridToPandaOffset[index]) / PartyGlobals.PartyGridUnitLength[index])


def convertDistanceFromPartyGrid(d, index):
    return d * PartyGlobals.PartyGridUnitLength[index] + PartyGlobals.PartyGridToPandaOffset[index] + PartyGlobals.PartyGridUnitLength[index] / 2.0


def convertDegreesToPartyGrid(h):
    while h < 0.0:
        h = h + 360.0

    h = h % 360.0
    return int(h / PartyGlobals.PartyGridHeadingConverter)


def convertDegreesFromPartyGrid(h):
    return h * PartyGlobals.PartyGridHeadingConverter


def getCenterPosFromGridSize(x, y, gridsize):
    if gridsize[0] % 2 == 0:
        xMod = PartyGlobals.PartyGridUnitLength[0] / 2.0
    else:
        xMod = 0
    if gridsize[1] % 2 == 0:
        yMod = PartyGlobals.PartyGridUnitLength[1] / 2.0
    else:
        yMod = 0
    return (x + xMod, y + yMod)


def toRadians(angle):
    return angle * math.pi / 180.0


def toDegrees(angle):
    return angle * 180.0 / math.pi


def calcVelocity(rotation, angle, initialVelocity = 1.0):
    horizVel = initialVelocity * math.cos(angle)
    xVel = horizVel * -math.sin(rotation)
    yVel = horizVel * math.cos(rotation)
    zVel = initialVelocity * math.sin(angle)
    return Vec3(xVel, yVel, zVel)


class LineSegment:

    def __init__(self, pt1, pt2):
        self.pt1 = pt1
        self.pt2 = pt2

    def isIntersecting(self, line, compare = None):
        x1 = self.pt1.getX()
        x2 = self.pt2.getX()
        x3 = line.pt1.getX()
        x4 = line.pt2.getX()
        y1 = self.pt1.getY()
        y2 = self.pt2.getY()
        y3 = line.pt1.getY()
        y4 = line.pt2.getY()
        top1 = (x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)
        top2 = (x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)
        bot = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
        if bot == 0.0:
            return False
        u1 = top1 / bot
        u2 = top2 / bot
        if compare is None:
            return 0 <= u1 and u1 <= 1 and 0 <= u2 and u2 <= 1
        elif compare == 'segment-ray':
            return 0 <= u1 and u1 <= 1 and 0 <= u2
        elif compare == 'ray-ray':
            return 0 <= u1 and 0 <= u2
        elif compare == 'ray-segment':
            return 0 <= u1 and 0 <= u2 and u2 <= 1
        return
