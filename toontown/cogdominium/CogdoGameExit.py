from pandac.PandaModules import NodePath, Point3
from direct.interval.MetaInterval import Parallel, Sequence
from direct.interval.SoundInterval import SoundInterval
from direct.interval.FunctionInterval import Wait, Func
from toontown.building import ElevatorConstants
from toontown.building import ElevatorUtils
from . import CogdoUtil
from . import CogdoGameConsts

class CogdoGameExit(NodePath):

    def __init__(self, openSfx = None, closeSfx = None):
        NodePath.__init__(self, 'CogdoGameExit')
        self._model = CogdoUtil.loadModel('exitDoor')
        self._model.reparentTo(self)
        self._leftDoor = self._model.find('**/left_door')
        self._rightDoor = self._model.find('**/right_door')
        self._openSfx = openSfx or base.loader.loadSfx('phase_9/audio/sfx/CHQ_VP_door_open.ogg')
        self._closeSfx = closeSfx or base.loader.loadSfx('phase_9/audio/sfx/CHQ_VP_door_close.ogg')
        self._elevatorPoints = []
        for point in ElevatorConstants.ElevatorPoints:
            self._elevatorPoints.append(point[0])

        self._currentSlot = 0
        self._ival = None
        self._open = True
        self._toon2track = {}
        self.close(animate=False)
        return

    def destroy(self):
        self._cleanToonTracks()
        if self._ival is not None:
            self._ival.clearToInitial()
        del self._ival
        self._model.removeNode()
        del self._leftDoor
        del self._rightDoor
        del self._model
        del self._openSfx
        del self._closeSfx
        del self._elevatorPoints
        return

    def isOpen(self):
        return self._open

    def uniqueName(self, name):
        return self.getName() + name

    def open(self, animate = True):
        if self._open:
            return
        if animate:
            self._finishIval()
            self._ival = Sequence(Parallel(SoundInterval(self._closeSfx), self._leftDoor.posInterval(self.getOpenCloseDuration(), ElevatorUtils.getLeftOpenPoint(ElevatorConstants.ELEVATOR_NORMAL), startPos=ElevatorUtils.getLeftClosePoint(ElevatorConstants.ELEVATOR_NORMAL), blendType='easeInOut'), self._rightDoor.posInterval(self.getOpenCloseDuration(), ElevatorUtils.getRightOpenPoint(ElevatorConstants.ELEVATOR_NORMAL), startPos=ElevatorUtils.getRightClosePoint(ElevatorConstants.ELEVATOR_NORMAL), blendType='easeInOut')))
            self._ival.start()
        else:
            ElevatorUtils.openDoors(self._leftDoor, self._rightDoor, type=ElevatorConstants.ELEVATOR_NORMAL)
        self._open = True

    def getOpenCloseDuration(self):
        return CogdoGameConsts.ExitDoorMoveDuration

    def close(self, animate = True):
        if not self._open:
            return
        if animate:
            self._finishIval()
            self._ival = Sequence(Parallel(SoundInterval(self._closeSfx), self._leftDoor.posInterval(self.getOpenCloseDuration(), ElevatorUtils.getLeftClosePoint(ElevatorConstants.ELEVATOR_NORMAL), startPos=ElevatorUtils.getLeftOpenPoint(ElevatorConstants.ELEVATOR_NORMAL), blendType='easeIn'), self._rightDoor.posInterval(self.getOpenCloseDuration(), ElevatorUtils.getRightClosePoint(ElevatorConstants.ELEVATOR_NORMAL), startPos=ElevatorUtils.getRightOpenPoint(ElevatorConstants.ELEVATOR_NORMAL), blendType='easeIn')))
            self._ival.start()
        else:
            ElevatorUtils.closeDoors(self._leftDoor, self._rightDoor, type=ElevatorConstants.ELEVATOR_NORMAL)
        self._open = False

    def _finishIval(self):
        if self._ival is not None and self._ival.isPlaying():
            self._ival.finish()
        return

    def toonEnters(self, toon, goInside = True):
        self._runToonThroughSlot(toon, self._currentSlot, goInside=goInside)
        self._currentSlot += 1
        if self._currentSlot > len(self._elevatorPoints):
            self._currentSlot = 0

    def _runToonThroughSlot(self, toon, slot, goInside = True):
        helperNode = NodePath('helper')
        helperNode.reparentTo(toon.getParent())
        helperNode.lookAt(self)
        lookAtH = helperNode.getH(self._model)
        toonH = toon.getH(self._model)
        hDiff = abs(lookAtH - toonH)
        distanceFromElev = toon.getDistance(self._model)
        moveSpeed = 9.778
        anim = 'run'
        if toon.animFSM.getCurrentState() == 'Sad':
            moveSpeed *= 0.5
            anim = 'sad-walk'
        runInsideDistance = 20
        track = Sequence(Func(toon.stopSmooth), Func(toon.loop, anim, 1.0), Parallel(toon.hprInterval(hDiff / 360.0, Point3(lookAtH, 0, 0), other=self._model, blendType='easeIn'), toon.posInterval(distanceFromElev / moveSpeed, Point3(self._elevatorPoints[slot], 0, 0), other=self._model, blendType='easeIn')), name=toon.uniqueName('runThroughExit'), autoPause=1)
        if goInside:
            track.append(Parallel(toon.hprInterval(lookAtH / 360.0, Point3(0, 0, 0), other=self._model, blendType='easeOut'), toon.posInterval(runInsideDistance / moveSpeed, Point3(self._elevatorPoints[slot], runInsideDistance, 0), other=self._model, blendType='easeOut')))
        track.append(Func(self._clearToonTrack, toon))
        track.append(Func(toon.setAnimState, 'Happy', 1.0))
        self._storeToonTrack(toon, track)
        track.start()

    def _cleanToonTracks(self):
        toons = [ toon for toon in self._toon2track ]
        for toon in toons:
            self._clearToonTrack(toon)

    def _clearToonTrack(self, toon):
        oldTrack = self._toon2track.get(toon)
        if oldTrack is not None:
            oldTrack.pause()
            del self._toon2track[toon]
        return

    def _storeToonTrack(self, toon, track):
        self._clearToonTrack(toon)
        self._toon2track[toon] = track
