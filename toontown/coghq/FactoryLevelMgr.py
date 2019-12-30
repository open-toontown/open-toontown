from otp.level import LevelMgr
from . import FactoryUtil
from direct.showbase.PythonUtil import Functor
from toontown.toonbase import ToontownGlobals

class FactoryLevelMgr(LevelMgr.LevelMgr):
    InterestingLocations = [(((-866, -272, -40), -101),
      ((-662, -242, 7.5), 0),
      ((-20, -180, 20), 0),
      ((-249, 258, 111), 0),
      ((318, 241, 115), -16),
      ((-251, 241, 109), -180),
      ((296, 292, 703), 56),
      ((-740, 122, 28), 90),
      ((210, -270, 38), -90)), (((20, 21, 0), 0), ((3, 404, 39), -16), ((-496, 358, 5), 0))]

    def __init__(self, level, entId):
        LevelMgr.LevelMgr.__init__(self, level, entId)
        if base.config.GetBool('want-factory-lifter', 0):
            self.toonLifter = FactoryUtil.ToonLifter('f3')
        self.callSetters('farPlaneDistance')
        self.geom.reparentTo(render)
        oilRoomOil = self.geom.find('**/oilroom/room/geometry_oilroom/*oil')
        oilRoomFloor = self.geom.find('**/oilroom/room/geometry_oilroom/*platform')
        if oilRoomOil and not oilRoomOil.isEmpty() and oilRoomFloor and not oilRoomFloor.isEmpty():
            oilRoomOil.setBin('background', 10)
            oilRoomFloor.setBin('background', 11)

    def destroy(self):
        if hasattr(self, 'toonLifter'):
            self.toonLifter.destroy()
            del self.toonLifter
        LevelMgr.LevelMgr.destroy(self)

    def setFarPlaneDistance(self, farPlaneDistance):
        base.camLens.setNearFar(ToontownGlobals.DefaultCameraNear, farPlaneDistance)

    if __dev__:

        def setWantDoors(self, wantDoors):
            self.wantDoors = wantDoors
            messenger.send('wantDoorsChanged')
