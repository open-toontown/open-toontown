from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *
from ElevatorConstants import *

def getLeftClosePoint(type):
    width = ElevatorData[type]['width']
    return Point3(width, 0, 0)


def getRightClosePoint(type):
    width = ElevatorData[type]['width']
    return Point3(-width, 0, 0)


def getLeftOpenPoint(type):
    return Point3(0, 0, 0)


def getRightOpenPoint(type):
    return Point3(0, 0, 0)


def closeDoors(leftDoor, rightDoor, type = ELEVATOR_NORMAL):
    closedPosLeft = getLeftClosePoint(type)
    closedPosRight = getRightClosePoint(type)
    leftDoor.setPos(closedPosLeft)
    rightDoor.setPos(closedPosRight)


def openDoors(leftDoor, rightDoor, type = ELEVATOR_NORMAL):
    openPosLeft = getLeftOpenPoint(type)
    openPosRight = getRightOpenPoint(type)
    leftDoor.setPos(openPosLeft)
    rightDoor.setPos(openPosRight)


def getLeftOpenInterval(distObj, leftDoor, type):
    openTime = ElevatorData[type]['openTime']
    closedPos = getLeftClosePoint(type)
    openPos = getLeftOpenPoint(type)
    leftOpenInterval = LerpPosInterval(leftDoor, openTime, openPos, startPos=closedPos, blendType='easeOut', name=distObj.uniqueName('leftDoorOpen'))
    return leftOpenInterval


def getRightOpenInterval(distObj, rightDoor, type):
    openTime = ElevatorData[type]['openTime']
    closedPos = getRightClosePoint(type)
    openPos = getRightOpenPoint(type)
    rightOpenInterval = LerpPosInterval(rightDoor, openTime, openPos, startPos=closedPos, blendType='easeOut', name=distObj.uniqueName('rightDoorOpen'))
    return rightOpenInterval


def getOpenInterval(distObj, leftDoor, rightDoor, openSfx, finalOpenSfx, type = ELEVATOR_NORMAL):
    left = getLeftOpenInterval(distObj, leftDoor, type)
    right = getRightOpenInterval(distObj, rightDoor, type)
    openDuration = left.getDuration()
    sfxVolume = ElevatorData[type]['sfxVolume']
    if finalOpenSfx:
        sound = Sequence(SoundInterval(openSfx, duration=openDuration, volume=sfxVolume, node=leftDoor), SoundInterval(finalOpenSfx, volume=sfxVolume, node=leftDoor))
    else:
        sound = SoundInterval(openSfx, volume=sfxVolume, node=leftDoor)
    return Parallel(sound, left, right)


def getLeftCloseInterval(distObj, leftDoor, type):
    closeTime = ElevatorData[type]['closeTime']
    closedPos = getLeftClosePoint(type)
    openPos = getLeftOpenPoint(type)
    leftCloseInterval = LerpPosInterval(leftDoor, closeTime, closedPos, startPos=openPos, blendType='easeOut', name=distObj.uniqueName('leftDoorClose'))
    return leftCloseInterval


def getRightCloseInterval(distObj, rightDoor, type):
    closeTime = ElevatorData[type]['closeTime']
    closedPos = getRightClosePoint(type)
    openPos = getRightOpenPoint(type)
    rightCloseInterval = LerpPosInterval(rightDoor, closeTime, closedPos, startPos=openPos, blendType='easeOut', name=distObj.uniqueName('rightDoorClose'))
    return rightCloseInterval


def getCloseInterval(distObj, leftDoor, rightDoor, closeSfx, finalCloseSfx, type = ELEVATOR_NORMAL):
    left = getLeftCloseInterval(distObj, leftDoor, type)
    right = getRightCloseInterval(distObj, rightDoor, type)
    closeDuration = left.getDuration()
    sfxVolume = ElevatorData[type]['sfxVolume']
    if finalCloseSfx:
        sound = Sequence(SoundInterval(closeSfx, duration=closeDuration, volume=sfxVolume, node=leftDoor), SoundInterval(finalCloseSfx, volume=sfxVolume, node=leftDoor))
    else:
        sound = SoundInterval(closeSfx, volume=sfxVolume, node=leftDoor)
    return Parallel(sound, left, right)


def getRideElevatorInterval(type = ELEVATOR_NORMAL):
    if type == ELEVATOR_VP or type == ELEVATOR_CFO or type == ELEVATOR_CJ:
        yValue = 30
        zMin = 7.8
        zMid = 8
        zMax = 8.2
    elif type == ELEVATOR_BB:
        yValue = 21
        zMin = 7
        zMid = 7.2
        zMax = 7.4
    if type in (ELEVATOR_VP,
     ELEVATOR_CFO,
     ELEVATOR_CJ,
     ELEVATOR_BB):
        ival = Sequence(Wait(0.5), LerpPosInterval(camera, 0.5, Point3(0, yValue, zMin), startPos=Point3(0, yValue, zMid), blendType='easeOut'), LerpPosInterval(camera, 0.5, Point3(0, yValue, zMid), startPos=Point3(0, yValue, zMin)), Wait(1.0), LerpPosInterval(camera, 0.5, Point3(0, yValue, zMax), startPos=Point3(0, yValue, zMid), blendType='easeOut'), LerpPosInterval(camera, 1.0, Point3(0, yValue, zMid), startPos=Point3(0, yValue, zMax)))
    else:
        ival = Sequence(Wait(0.5), LerpPosInterval(camera, 0.5, Point3(0, 14, 3.8), startPos=Point3(0, 14, 4), blendType='easeOut'), LerpPosInterval(camera, 0.5, Point3(0, 14, 4), startPos=Point3(0, 14, 3.8)), Wait(1.0), LerpPosInterval(camera, 0.5, Point3(0, 14, 4.2), startPos=Point3(0, 14, 4), blendType='easeOut'), LerpPosInterval(camera, 1.0, Point3(0, 14, 4), startPos=Point3(0, 14, 4.2)))
    return ival
