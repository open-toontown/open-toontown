from direct.directnotify import DirectNotifyGlobal
from . import RingTrack

class RingAction:
    notify = DirectNotifyGlobal.directNotify.newCategory('RingAction')

    def __init__(self):
        pass

    def eval(self, t):
        return (0, 0)


class RingActionStaticPos(RingAction):

    def __init__(self, pos):
        RingAction.__init__(self)
        self.__pos = pos

    def eval(self, t):
        return self.__pos


class RingActionFunction(RingAction):

    def __init__(self, func, args):
        RingAction.__init__(self)
        self.__func = func
        self.__args = args

    def eval(self, t):
        return self.__func(t, *self.__args)


class RingActionRingTrack(RingAction):

    def __init__(self, ringTrack):
        RingAction.__init__(self)
        self.__track = ringTrack

    def eval(self, t):
        return self.__track.eval(t)
