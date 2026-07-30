from direct.interval.MetaInterval import Sequence
from direct.interval.FunctionInterval import Wait, Func
PULSE_GUI_DURATION = 0.2
PULSE_GUI_CHANGE = 0.333

def cleanup(name):
    taskMgr.remove(name)


def start(ival):
    cleanup(ival.getName())
    ival.start()
    return ival


def loop(ival):
    cleanup(ival.getName())
    ival.loop()
    return ival


def getPulseLargerIval(np, name, duration = PULSE_GUI_DURATION, scale = 1):
    return getPulseIval(np, name, 1 + PULSE_GUI_CHANGE, duration=duration, scale=scale)


def getPulseSmallerIval(np, name, duration = PULSE_GUI_DURATION, scale = 1):
    return getPulseIval(np, name, 1 - PULSE_GUI_CHANGE, duration=duration, scale=scale)


def getPulseIval(np, name, change, duration = PULSE_GUI_CHANGE, scale = 1):
    return Sequence(np.scaleInterval(duration, scale * change, blendType='easeOut'), np.scaleInterval(duration, scale, blendType='easeIn'), name=name, autoFinish=1)


def getPresentGuiIval(np, name, waitDuration = 0.5, moveDuration = 1.0, parent = aspect2d, startPos = (0, 0, 0)):
    endPos = np.getPos()
    np.setPos(parent, startPos[0], startPos[1], startPos[2])
    return Sequence(Func(np.show), getPulseLargerIval(np, '', scale=np.getScale()), Wait(waitDuration), np.posInterval(moveDuration, endPos, blendType='easeInOut'), name=name, autoFinish=1)
