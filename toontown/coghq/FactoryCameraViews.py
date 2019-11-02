from pandac.PandaModules import *
from direct.showbase.PythonUtil import Functor
from toontown.toonbase import ToontownGlobals
from direct.directnotify import DirectNotifyGlobal

class FactoryCameraViews:
    notify = DirectNotifyGlobal.directNotify.newCategory('FactoryCameraViews')

    def __init__(self, factory):
        self.factory = factory
        av = base.localAvatar
        self.currentCamPos = None
        self.views = [['signatureRoomView', (Point3(0.0, -14.8419799805, 13.212685585),
           Point3(0.0, -13.9563484192, 12.749215126),
           Point3(0.0, 1.5, 15.75),
           Point3(0.0, 1.5, -3.9375),
           1), ['localToonLeftBattle']], ['lookoutTrigger', (Point3(0, -17.7, 28.8),
           Point3(0, 10, 0),
           Point3(0.0, 1.5, 15.75),
           Point3(0.0, 1.5, -3.9375),
           1), []], ['moleFieldView', (Point3(0, -17.7, 28.8),
           Point3(0, 10, 0),
           Point3(0.0, 1.5, 15.75),
           Point3(0.0, 1.5, -3.9375),
           1), []]]
        camHeight = av.getClampedAvatarHeight()
        for i in range(len(self.views)):
            camPos = self.views[i][1]
            av.auxCameraPositions.append(camPos)
            factory.accept('enter' + self.views[i][0], Functor(self.switchCamPos, i))
            for msg in self.views[i][2]:
                factory.accept(msg, self.checkCamPos)

        return

    def delete(self):
        for i in range(len(self.views)):
            base.localAvatar.auxCameraPositions.remove(self.views[i][1])
            self.factory.ignore('enter' + self.views[i][0])
            self.factory.ignore('exit' + self.views[i][0])
            for msg in self.views[i][2]:
                self.factory.ignore(msg)

        base.localAvatar.resetCameraPosition()
        del self.views

    def switchCamPos(self, viewIndex, colEntry = None):
        av = base.localAvatar
        prevView = av.cameraIndex
        self.currentCamPos = viewIndex
        av.accept('exit' + self.views[viewIndex][0], Functor(self.prevCamPos, prevView))
        self.notify.info('auto-switching to camera position %s' % viewIndex)
        av.setCameraSettings(self.views[viewIndex][1])

    def prevCamPos(self, index, colEntry = None):
        av = base.localAvatar
        if len(av.cameraPositions) > index:
            av.setCameraPositionByIndex(index)
        self.currentCamPos = None
        return

    def checkCamPos(self):
        if self.currentCamPos != None:
            av = base.localAvatar
            viewIndex = self.currentCamPos
            self.notify.info('returning to camera position %s' % viewIndex)
            av.setCameraSettings(self.views[viewIndex][1])
        return
