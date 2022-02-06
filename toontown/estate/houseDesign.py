from direct.directtools.DirectSelection import *
from direct.directtools.DirectUtil import ROUND_TO
from direct.directtools.DirectGeometry import LineNodePath
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from direct.showbase.DirectObject import DirectObject
from toontown.toonbase import ToontownGlobals
from direct.directnotify import DirectNotifyGlobal
from direct.task import Task
from toontown.catalog import CatalogFurnitureItem
from toontown.catalog import CatalogItemTypes
from direct.showbase import PythonUtil
from toontown.toontowngui import TTDialog
from toontown.toonbase import TTLocalizer
from otp.otpbase import OTPLocalizer
camPos50 = (Point3(0.0, -10.0, 50.0),
 Point3(0.0, -9.66, 49.06),
 Point3(0.0, 1.5, 12.38),
 Point3(0.0, 1.5, -3.1),
 1)
camPos40 = (Point3(0.0, -15.0, 40.0),
 Point3(0.0, -14.5, 39.13),
 Point3(0.0, 1.5, 12.38),
 Point3(0.0, 1.5, -3.1),
 1)
camPos30 = (Point3(0.0, -20.0, 30.0),
 Point3(0.0, -19.29, 29.29),
 Point3(0.0, 1.5, 12.38),
 Point3(0.0, 1.5, -3.1),
 1)
camPos20 = (Point3(0.0, -20.0, 20.0),
 Point3(0.0, -19.13, 19.5),
 Point3(0.0, 1.5, 12.38),
 Point3(0.0, 1.5, -3.1),
 1)
camPosList = [camPos20,
 camPos30,
 camPos40,
 camPos50]
DEFAULT_CAM_INDEX = 2
NormalPickerPanelColor = (1, 0.9, 0.745, 1)
DisabledPickerPanelColor = (0.7, 0.65, 0.58, 1)
DeletePickerPanelColor = (1, 0.4, 0.4, 1)
DisabledDeletePickerPanelColor = (0.7, 0.3, 0.3, 1)

class FurnitureItemPanel(DirectButton):

    def __init__(self, item, itemId, command = None, deleteMode = 0, withinFunc = None, helpCategory = None):
        self.item = item
        self.itemId = itemId
        self.command = command
        self.origHelpCategory = helpCategory
        self.deleteMode = deleteMode
        if self.deleteMode:
            framePanelColor = DeletePickerPanelColor
        else:
            framePanelColor = NormalPickerPanelColor
        DirectButton.__init__(self, relief=DGG.RAISED, frameSize=(-0.25,
         0.25,
         -0.2,
         0.2), frameColor=framePanelColor, borderWidth=(0.02, 0.02), command=self.clicked)
        if self.deleteMode:
            helpCategory = 'FurnitureItemPanelDelete'
        self.bindHelpText(helpCategory)
        if withinFunc:
            self.bind(DGG.WITHIN, lambda event: withinFunc(self.itemId))
        self.initialiseoptions(FurnitureItemPanel)
        self.load()

    def show(self):
        DirectFrame.show(self)
        if self.ival:
            self.ival.resume()

    def hide(self):
        DirectFrame.hide(self)
        if self.ival:
            self.ival.pause()

    def load(self):
        panelWidth = 7
        panelCenter = 0
        self.picture, self.ival = self.item.getPicture(base.localAvatar)
        if self.picture:
            self.picture.reparentTo(self)
            self.picture.setScale(0.14)
            self.picture.setPos(0, 0, -0.02)
            text = self.item.getName()
            text_pos = (0, -0.1, 0)
        else:
            text = self.item.getTypeName() + ': ' + self.item.getName()
            text_pos = (0, -0.3, 0)
        if self.ival:
            self.ival.loop()
            self.ival.pause()
        self.nameLabel = DirectLabel(parent=self, relief=None, pos=(0, 0, 0.17), scale=0.45, text=text, text_scale=0.15, text_fg=(0, 0, 0, 1), text_pos=text_pos, text_font=ToontownGlobals.getInterfaceFont(), text_wordwrap=panelWidth)
        return

    def clicked(self):
        self.command(self.item, self.itemId)

    def unload(self):
        if self.item.hasPicture:
            self.item.cleanupPicture()
        del self.item
        self.nameLabel.destroy()
        del self.nameLabel
        if self.ival:
            self.ival.finish()
        del self.ival
        del self.picture
        self.command = None
        return

    def destroy(self):
        self.unload()
        DirectButton.destroy(self)

    def bindHelpText(self, category):
        self.unbind(DGG.ENTER)
        self.unbind(DGG.EXIT)
        if category is None:
            category = self.origHelpCategory
        self.bind(DGG.ENTER, base.cr.objectManager.showHelpText, extraArgs=[category, self.item.getName()])
        self.bind(DGG.EXIT, base.cr.objectManager.hideHelpText)
        return

    def setDeleteMode(self, deleteMode):
        self.deleteMode = deleteMode
        self.__updateAppearance()

    def enable(self, enabled):
        if enabled:
            self['state'] = DGG.NORMAL
        else:
            self['state'] = DGG.DISABLED
        self.__updateAppearance()

    def __updateAppearance(self):
        color = NormalPickerPanelColor
        relief = DGG.RAISED
        if self.deleteMode:
            if self['state'] == DGG.DISABLED:
                color = DisabledDeletePickerPanelColor
                relief = DGG.SUNKEN
            else:
                color = DeletePickerPanelColor
                relief = DGG.RAISED
        elif self['state'] == DGG.DISABLED:
            color = DisabledPickerPanelColor
            relief = DGG.SUNKEN
        else:
            color = NormalPickerPanelColor
            relief = DGG.RAISED
        self['frameColor'] = color


class MovableObject(NodePath, DirectObject):

    def __init__(self, dfitem, parent = render):
        NodePath.__init__(self)
        self.assign(dfitem)
        self.dfitem = dfitem
        dfitem.transmitRelativeTo = dfitem.getParent()
        self.reparentTo(parent)
        self.setTag('movableObject', '1')
        self.builtInCNodes = self.findAllMatches('**/+CollisionNode')
        self.numBuiltInNodes = self.builtInCNodes.getNumPaths()
        self.stashBuiltInCollisionNodes()
        shadows = self.findAllMatches('**/*shadow*')
        shadows.addPathsFrom(self.findAllMatches('**/*Shadow*'))
        shadows.stash()
        flags = self.dfitem.item.getFlags()
        if flags & CatalogFurnitureItem.FLPainting:
            self.setOnFloor(0)
            self.setOnWall(1)
        else:
            self.setOnFloor(1)
            self.setOnWall(0)
        if flags & CatalogFurnitureItem.FLOnTable:
            self.setOnTable(1)
        else:
            self.setOnTable(0)
        if flags & CatalogFurnitureItem.FLRug:
            self.setIsRug(1)
        else:
            self.setIsRug(0)
        if flags & CatalogFurnitureItem.FLIsTable:
            self.setIsTable(1)
        else:
            self.setIsTable(0)
        m = self.getTransform()
        self.setPosHpr(0, 0, 0, 0, 0, 0)
        bMin, bMax = self.bounds = self.getTightBounds()
        bMin -= Vec3(0.1, 0.1, 0)
        bMax += Vec3(0.1, 0.1, 0)
        self.c0 = Point3(bMin[0], bMin[1], 0.2)
        self.c1 = Point3(bMax[0], bMin[1], 0.2)
        self.c2 = Point3(bMax[0], bMax[1], 0.2)
        self.c3 = Point3(bMin[0], bMax[1], 0.2)
        self.center = (bMin + bMax) / 2.0
        if flags & CatalogFurnitureItem.FLPainting:
            self.dragPoint = Vec3(self.center[0], bMax[1], self.center[2])
        else:
            self.dragPoint = Vec3(self.center[0], self.center[1], bMin[2])
        delta = self.dragPoint - self.c0
        self.radius = min(delta[0], delta[1])
        if self.getOnWall():
            self.setWallOffset(0.1)
        else:
            self.setWallOffset(self.radius + 0.1)
        self.makeCollisionBox()
        self.setTransform(m)
        self.unstashBuiltInCollisionNodes()
        shadows.unstash()

    def resetMovableObject(self):
        self.unstashBuiltInCollisionNodes()
        self.collisionNodePath.removeNode()
        self.clearTag('movableObject')

    def setOnFloor(self, fOnFloor):
        self.fOnFloor = fOnFloor

    def getOnFloor(self):
        return self.fOnFloor

    def setOnWall(self, fOnWall):
        self.fOnWall = fOnWall

    def getOnWall(self):
        return self.fOnWall

    def setOnTable(self, fOnTable):
        self.fOnTable = fOnTable

    def getOnTable(self):
        return self.fOnTable

    def setIsRug(self, fIsRug):
        self.fIsRug = fIsRug

    def getIsRug(self):
        return self.fIsRug

    def setIsTable(self, fIsTable):
        self.fIsTable = fIsTable

    def getIsTable(self):
        return self.fIsTable

    def setWallOffset(self, offset):
        self.wallOffset = offset

    def getWallOffset(self):
        return self.wallOffset

    def destroy(self):
        self.removeNode()

    def stashBuiltInCollisionNodes(self):
        self.builtInCNodes.stash()

    def unstashBuiltInCollisionNodes(self):
        self.builtInCNodes.unstash()

    def getFloorBitmask(self):
        if self.getOnTable():
            return ToontownGlobals.FloorBitmask | ToontownGlobals.FurnitureTopBitmask
        else:
            return ToontownGlobals.FloorBitmask

    def getWallBitmask(self):
        if self.getIsRug() or self.getOnWall():
            return ToontownGlobals.WallBitmask
        else:
            return ToontownGlobals.WallBitmask | ToontownGlobals.FurnitureSideBitmask

    def makeCollisionBox(self):
        self.collisionNodePath = self.attachNewNode('furnitureCollisionNode')
        if self.getIsRug() or self.getOnWall():
            return
        mx = self.bounds[0][0] - 0.01
        Mx = self.bounds[1][0] + 0.01
        my = self.bounds[0][1] - 0.01
        My = self.bounds[1][1] + 0.01
        mz = self.bounds[0][2]
        Mz = self.bounds[1][2]
        cn = CollisionNode('sideCollisionNode')
        cn.setIntoCollideMask(ToontownGlobals.FurnitureSideBitmask)
        self.collisionNodePath.attachNewNode(cn)
        cp = CollisionPolygon(Point3(mx, My, mz), Point3(mx, my, mz), Point3(mx, my, Mz), Point3(mx, My, Mz))
        cn.addSolid(cp)
        cp = CollisionPolygon(Point3(Mx, my, mz), Point3(Mx, My, mz), Point3(Mx, My, Mz), Point3(Mx, my, Mz))
        cn.addSolid(cp)
        cp = CollisionPolygon(Point3(mx, my, mz), Point3(Mx, my, mz), Point3(Mx, my, Mz), Point3(mx, my, Mz))
        cn.addSolid(cp)
        cp = CollisionPolygon(Point3(Mx, My, mz), Point3(mx, My, mz), Point3(mx, My, Mz), Point3(Mx, My, Mz))
        cn.addSolid(cp)
        if self.getIsTable():
            cn = CollisionNode('topCollisionNode')
            cn.setIntoCollideMask(ToontownGlobals.FurnitureTopBitmask)
            self.collisionNodePath.attachNewNode(cn)
            cp = CollisionPolygon(Point3(mx, my, Mz), Point3(Mx, my, Mz), Point3(Mx, My, Mz), Point3(mx, My, Mz))
            cn.addSolid(cp)


class ObjectManager(NodePath, DirectObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('ObjectManager')

    def __init__(self):
        NodePath.__init__(self)
        self.assign(render.attachNewNode('objectManager'))
        self.objectDict = {}
        self.selectedObject = None
        self.movingObject = 0
        self.deselectEvent = None
        self.startPose = render.attachNewNode('startPose')
        self.dragPointNP = self.attachNewNode('dragPoint')
        self.gridSnapNP = self.dragPointNP.attachNewNode('gridSnap')
        self.collisionOffsetNP = self.gridSnapNP.attachNewNode('collisionResponse')
        self.iRay = SelectionRay()
        self.iSegment = SelectionSegment(numSegments=6)
        self.iSegment4 = SelectionSegment(numSegments=4)
        self.iSphere = SelectionSphere()
        self.houseExtents = None
        self.doorBlocker = None
        cp = CollisionPolygon(Point3(-100, -100, 0), Point3(100, -100, 0), Point3(100, 100, 0), Point3(-100, 100, 0))
        cn = CollisionNode('dragCollisionNode')
        cn.addSolid(cp)
        cn.setIntoCollideMask(ToontownGlobals.FurnitureDragBitmask)
        self.collisionNP = NodePath(cn)
        self.lnp = LineNodePath()
        self.fRecenter = 0
        self.gridSpacing = None
        self.firstTime = 0
        guiModels = loader.loadModel('phase_5.5/models/gui/house_design_gui')
        self.createSelectedObjectPanel(guiModels)
        self.createMainControls(guiModels)
        self.furnitureManager = None
        self.atticPicker = None
        self.inRoomPicker = None
        self.inTrashPicker = None
        self.dialog = None
        self.deleteMode = 0
        self.nonDeletableItem = None
        self.verifyFrame = None
        self.deleteItemText = None
        self.okButton = None
        self.cancelButton = None
        self.itemIval = None
        self.itemPanel = None
        self.guiInterval = None
        self.accept('enterFurnitureMode', self.enterFurnitureMode)
        self.accept('exitFurnitureMode', self.exitFurnitureMode)
        return

    def enterFurnitureMode(self, furnitureManager, fDirector):
        if not fDirector:
            if self.furnitureManager:
                self.exitFurnitureMode(self.furnitureManager)
            return
        if furnitureManager == self.furnitureManager:
            return
        if self.furnitureManager != None:
            self.exitFurnitureMode(self.furnitureManager)
        self.notify.info('enterFurnitureMode, fDirector = %s' % fDirector)
        self.furnitureManager = furnitureManager
        self.furnitureManager.d_avatarEnter()
        house = furnitureManager.getInteriorObject()
        house.hideExteriorWindows()
        self.setTargetNodePath(house.interior)
        self.createAtticPicker()
        self.initializeDistributedFurnitureItems(furnitureManager.dfitems)
        self.setCamPosIndex(DEFAULT_CAM_INDEX)
        base.localAvatar.setGhostMode(1)
        taskMgr.remove('editModeTransition')
        self.orientCamH(base.localAvatar.getH(self.targetNodePath))
        self.accept('mouse1', self.moveObjectStart)
        self.accept('mouse1-up', self.moveObjectStop)
        self.furnitureGui.show()
        self.deleteMode = 0
        self.__updateDeleteButtons()
        self.showAtticPicker()
        base.localAvatar.laffMeter.stop()
        base.setCellsAvailable(base.leftCells + [base.bottomCells[0]], 0)
        if self.guiInterval:
            self.guiInterval.finish()
        self.guiInterval = self.furnitureGui.posHprScaleInterval(1.0, Point3(-1.16, 1, -0.03), Vec3(0), Vec3(0.06), startPos=Point3(-1.19, 1, 0.33), startHpr=Vec3(0), startScale=Vec3(0.04), blendType='easeInOut', name='lerpFurnitureButton')
        self.guiInterval.start()
        taskMgr.add(self.recenterButtonFrameTask, 'recenterButtonFrameTask', 10)
        messenger.send('wakeup')
        return

    def exitFurnitureMode(self, furnitureManager):
        if furnitureManager != self.furnitureManager:
            return
        self.notify.info('exitFurnitureMode')
        house = furnitureManager.getInteriorObject()
        if house:
            house.showExteriorWindows()
        self.furnitureManager.d_avatarExit()
        self.furnitureManager = None
        base.localAvatar.setCameraPositionByIndex(0)
        self.exitDeleteMode()
        self.houseExtents.detachNode()
        self.doorBlocker.detachNode()
        self.deselectObject()
        self.ignore('mouse1')
        self.ignore('mouse1-up')
        if self.atticPicker:
            self.atticPicker.destroy()
            self.atticPicker = None
        if self.inRoomPicker:
            self.inRoomPicker.destroy()
            self.inRoomPicker = None
        if self.inTrashPicker:
            self.inTrashPicker.destroy()
            self.inTrashPicker = None
        self.__cleanupVerifyDelete()
        self.furnitureGui.hide()
        base.setCellsAvailable(base.leftCells + [base.bottomCells[0]], 1)
        base.localAvatar.laffMeter.start()
        taskMgr.remove('recenterButtonFrameTask')
        self.cleanupDialog()
        taskMgr.remove('showHelpTextDoLater')
        messenger.send('wakeup')
        return

    def initializeDistributedFurnitureItems(self, dfitems):
        self.objectDict = {}
        for item in dfitems:
            mo = MovableObject(item, parent=self.targetNodePath)
            self.objectDict[mo.id()] = mo

    def setCamPosIndex(self, index):
        self.camPosIndex = index
        base.localAvatar.setCameraSettings(camPosList[index])

    def zoomCamIn(self):
        self.setCamPosIndex(max(0, self.camPosIndex - 1))
        messenger.send('wakeup')

    def zoomCamOut(self):
        self.setCamPosIndex(min(len(camPosList) - 1, self.camPosIndex + 1))
        messenger.send('wakeup')

    def rotateCamCW(self):
        self.orientCamH(base.localAvatar.getH(self.targetNodePath) - 90)
        messenger.send('wakeup')

    def rotateCamCCW(self):
        self.orientCamH(base.localAvatar.getH(self.targetNodePath) + 90)
        messenger.send('wakeup')

    def orientCamH(self, toonH):
        targetH = ROUND_TO(toonH, 90)
        base.localAvatar.hprInterval(duration=1, hpr=Vec3(targetH, 0, 0), other=self.targetNodePath, blendType='easeInOut', name='editModeTransition').start()

    def setTargetNodePath(self, nodePath):
        self.targetNodePath = nodePath
        if self.houseExtents:
            self.houseExtents.removeNode()
        if self.doorBlocker:
            self.doorBlocker.removeNode()
        self.makeHouseExtentsBox()
        self.makeDoorBlocker()
        self.collisionNP.reparentTo(self.targetNodePath)

    def loadObject(self, filename):
        mo = MovableObject(filename, parent=self.targetNodePath)
        self.objectDict[mo.id()] = mo
        self.selectObject(mo)
        return mo

    def pickObject(self):
        self.iRay.setParentNP(base.cam)
        entry = self.iRay.pickGeom(targetNodePath=self.targetNodePath, skipFlags=SKIP_ALL)
        if entry:
            nodePath = entry.getIntoNodePath()
            if self.isMovableObject(nodePath):
                self.selectObject(self.findObject(nodePath))
                return
        self.deselectObject()

    def pickInRoom(self, objectId):
        self.selectObject(self.objectDict.get(objectId))

    def selectObject(self, selectedObject):
        messenger.send('wakeup')
        if self.selectedObject:
            self.deselectObject()
        if selectedObject:
            self.selectedObject = selectedObject
            self.deselectEvent = self.selectedObject.dfitem.uniqueName('disable')
            self.acceptOnce(self.deselectEvent, self.deselectObject)
            self.lnp.reset()
            self.lnp.reparentTo(selectedObject)
            self.lnp.moveTo(selectedObject.c0)
            self.lnp.drawTo(selectedObject.c1)
            self.lnp.drawTo(selectedObject.c2)
            self.lnp.drawTo(selectedObject.c3)
            self.lnp.drawTo(selectedObject.c0)
            self.lnp.create()
            self.buttonFrame.show()
            self.enableButtonFrameTask()
            self.sendToAtticButton.show()
            self.atticRoof.hide()

    def deselectObject(self):
        self.moveObjectStop()
        if self.deselectEvent:
            self.ignore(self.deselectEvent)
            self.deselectEvent = None
        self.selectedObject = None
        self.lnp.detachNode()
        self.buttonFrame.hide()
        self.disableButtonFrameTask()
        self.sendToAtticButton.hide()
        self.atticRoof.show()
        return

    def isMovableObject(self, nodePath):
        return nodePath.hasNetTag('movableObject')

    def findObject(self, nodePath):
        np = nodePath.findNetTag('movableObject')
        if np.isEmpty():
            return None
        else:
            return self.objectDict.get(np.id(), None)
        return None

    def moveObjectStop(self, *args):
        if self.movingObject:
            self.movingObject = 0
            taskMgr.remove('moveObjectTask')
            if self.selectedObject:
                self.selectedObject.wrtReparentTo(self.targetNodePath)
                self.selectedObject.collisionNodePath.unstash()
                self.selectedObject.dfitem.stopAdjustPosHpr()
            for object in list(self.objectDict.values()):
                object.unstashBuiltInCollisionNodes()

            self.centerMarker['image'] = [self.grabUp, self.grabDown, self.grabRollover]
            self.centerMarker.configure(text=['', TTLocalizer.HDMoveLabel], text_pos=(0, 1), text_scale=0.7, text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1), image_scale=0.3)

    def moveObjectStart(self):
        self.moveObjectStop()
        self.pickObject()
        self.moveObjectContinue()

    def moveObjectContinue(self, *args):
        messenger.send('wakeup')
        if self.selectedObject:
            for object in list(self.objectDict.values()):
                object.stashBuiltInCollisionNodes()

            self.selectedObject.collisionNodePath.stash()
            self.selectedObject.dfitem.startAdjustPosHpr()
            self.firstTime = 1
            self.setPosHpr(0, 0, 0, 0, 0, 0)
            self.startPoseValid = 0
            self.centerMarker['image'] = self.grabDown
            self.centerMarker.configure(text=TTLocalizer.HDMoveLabel, text_pos=(0, 1), text_scale=0.7, text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1), image_scale=0.3)
            taskMgr.add(self.moveObjectTask, 'moveObjectTask')
            self.movingObject = 1

    def setLnpColor(self, r, g, b):
        for i in range(5):
            self.lnp.lineSegs.setVertexColor(i, r, g, b)

    def markNewPosition(self, isValid):
        if not isValid:
            if self.startPoseValid:
                self.collisionOffsetNP.setPosHpr(self.startPose, self.selectedObject.dragPoint, Vec3(0))
        else:
            self.startPoseValid = 1

    def moveObjectTask(self, state):
        so = self.selectedObject
        target = self.targetNodePath
        self.startPose.setPosHpr(so, 0, 0, 0, 0, 0, 0)
        self.iRay.setParentNP(base.cam)
        entry = self.iRay.pickBitMask(bitMask=ToontownGlobals.FurnitureDragBitmask, targetNodePath=target, skipFlags=SKIP_BACKFACE | SKIP_CAMERA | SKIP_UNPICKABLE)
        if not entry:
            return Task.cont
        self.setPos(base.cam, entry.getSurfacePoint(base.cam))
        if self.firstTime:
            self.moveObjectInit()
            self.firstTime = 0
        else:
            self.gridSnapNP.setPos(0, 0, 0)
            self.collisionOffsetNP.setPosHpr(0, 0, 0, 0, 0, 0)
        if self.gridSpacing:
            pos = self.dragPointNP.getPos(target)
            self.gridSnapNP.setPos(target, ROUND_TO(pos[0], self.gridSpacing), ROUND_TO(pos[1], self.gridSpacing), pos[2])
        self.iRay.setParentNP(base.cam)
        entry = self.iRay.pickBitMask3D(bitMask=so.getWallBitmask(), targetNodePath=target, dir=Vec3(self.getNearProjectionPoint(self.gridSnapNP)), skipFlags=SKIP_BACKFACE | SKIP_CAMERA | SKIP_UNPICKABLE)
        fWall = 0
        if not so.getOnTable():
            while entry:
                intoMask = entry.getIntoNodePath().node().getIntoCollideMask()
                fClosest = (intoMask & ToontownGlobals.WallBitmask).isZero()
                if self.alignObject(entry, target, fClosest=fClosest):
                    fWall = 1
                    break
                entry = self.iRay.findNextCollisionEntry(skipFlags=SKIP_BACKFACE | SKIP_CAMERA | SKIP_UNPICKABLE)

        if so.getOnWall():
            self.markNewPosition(fWall)
            return Task.cont
        self.iRay.setParentNP(target)
        entry = self.iRay.pickBitMask3D(bitMask=so.getFloorBitmask(), targetNodePath=target, origin=Point3(self.gridSnapNP.getPos(target) + Vec3(0, 0, 10)), dir=Vec3(0, 0, -1), skipFlags=SKIP_BACKFACE | SKIP_CAMERA | SKIP_UNPICKABLE)
        if not entry:
            self.markNewPosition(0)
            return Task.cont
        nodePath = entry.getIntoNodePath()
        if self.isMovableObject(nodePath):
            self.gridSnapNP.setPos(target, Point3(entry.getSurfacePoint(target)))
        else:
            self.gridSnapNP.setPos(target, Point3(entry.getSurfacePoint(target) + Vec3(0, 0, ToontownGlobals.FloorOffset)))
            if not fWall:
                self.iSphere.setParentNP(self.gridSnapNP)
                self.iSphere.setCenterRadius(0, Point3(0), so.radius * 1.25)
                entry = self.iSphere.pickBitMask(bitMask=so.getWallBitmask(), targetNodePath=target, skipFlags=SKIP_CAMERA | SKIP_UNPICKABLE)
                if entry:
                    self.alignObject(entry, target, fClosest=1)
        isValid = self.collisionTest()
        self.markNewPosition(isValid)
        return Task.cont

    def collisionTest(self):
        so = self.selectedObject
        target = self.targetNodePath
        entry = self.segmentCollision()
        if not entry:
            return 1
        offsetDict = {}
        while entry:
            offset = self.computeSegmentOffset(entry)
            if offset:
                eid = entry.getInto()
                maxOffsetVec = offsetDict.get(eid, Vec3(0))
                if offset.length() > maxOffsetVec.length():
                    maxOffsetVec.assign(offset)
                offsetDict[eid] = maxOffsetVec
            entry = self.iSegment.findNextCollisionEntry(skipFlags=SKIP_CAMERA | SKIP_UNPICKABLE)

        if offsetDict:
            keys = list(offsetDict.keys())
            ortho1 = offsetDict[keys[0]]
            ortho2 = Vec3(0)
            v1 = Vec3(ortho1)
            v1.normalize()
            for key in keys[1:]:
                offset = offsetDict[key]
                v2 = Vec3(offset)
                v2.normalize()
                dp = v1.dot(v2)
                if abs(dp) > 0.95:
                    if offset.length() > ortho1.length():
                        ortho1.assign(offset)
                elif abs(dp) < 0.05:
                    if offset.length() > ortho2.length():
                        ortho2.assign(offset)
                else:
                    o1Len = ortho1.length()
                    parallelVec = Vec3(ortho1 * offset.dot(ortho1) / (o1Len * o1Len))
                    perpVec = Vec3(offset - parallelVec)
                    if parallelVec.length() > o1Len:
                        ortho1.assign(parallelVec)
                    if perpVec.length() > ortho2.length():
                        ortho2.assign(perpVec)

            totalOffset = ortho1 + ortho2
            self.collisionOffsetNP.setPos(self.collisionOffsetNP, totalOffset)
            if not self.segmentCollision():
                return 1
        m = self.startPose.getMat(so)
        deltaMove = Vec3(m.getRow3(3))
        if deltaMove.length() == 0:
            return 1
        self.iSegment4.setParentNP(so)
        entry = self.iSegment4.pickBitMask(bitMask=so.getWallBitmask(), targetNodePath=target, endPointList=[(so.c0, Point3(m.xformPoint(so.c0))),
         (so.c1, Point3(m.xformPoint(so.c1))),
         (so.c2, Point3(m.xformPoint(so.c2))),
         (so.c3, Point3(m.xformPoint(so.c3)))], skipFlags=SKIP_CAMERA | SKIP_UNPICKABLE)
        maxLen = 0
        maxOffset = None
        while entry:
            offset = Vec3(entry.getSurfacePoint(entry.getFromNodePath()) - entry.getFrom().getPointA())
            offsetLen = Vec3(offset).length()
            if offsetLen > maxLen:
                maxLen = offsetLen
                maxOffset = offset
            entry = self.iSegment4.findNextCollisionEntry(skipFlags=SKIP_CAMERA | SKIP_UNPICKABLE)

        if maxOffset:
            self.collisionOffsetNP.setPos(self.collisionOffsetNP, maxOffset)
        if not self.segmentCollision():
            return 1
        return 0

    def segmentCollision(self):
        so = self.selectedObject
        self.iSegment.setParentNP(so)
        entry = self.iSegment.pickBitMask(bitMask=so.getWallBitmask(), targetNodePath=self.targetNodePath, endPointList=[(so.c0, so.c1),
         (so.c1, so.c2),
         (so.c2, so.c3),
         (so.c3, so.c0),
         (so.c0, so.c2),
         (so.c1, so.c3)], skipFlags=SKIP_CAMERA | SKIP_UNPICKABLE)
        return entry

    def computeSegmentOffset(self, entry):
        fromNodePath = entry.getFromNodePath()
        if entry.hasSurfaceNormal():
            normal = entry.getSurfaceNormal(fromNodePath)
        else:
            return None
        hitPoint = entry.getSurfacePoint(fromNodePath)
        m = self.selectedObject.getMat(self.startPose)
        hp = Point3(m.xformPoint(hitPoint))
        hpn = Vec3(m.xformVec(normal))
        hitPointVec = Vec3(hp - self.selectedObject.dragPoint)
        if hitPointVec.dot(hpn) > 0:
            return None
        nLen = normal.length()
        offsetVecA = hitPoint - entry.getFrom().getPointA()
        offsetA = normal * offsetVecA.dot(normal) / (nLen * nLen)
        if offsetA.dot(normal) > 0:
            return offsetA * 1.01
        else:
            offsetVecB = hitPoint - entry.getFrom().getPointB()
            offsetB = normal * offsetVecB.dot(normal) / (nLen * nLen)
            return offsetB * 1.01
        return None

    def alignObject(self, entry, target, fClosest = 0, wallOffset = None):
        if not entry.hasSurfaceNormal():
            return 0
        normal = entry.getSurfaceNormal(target)
        if abs(normal.dot(Vec3(0, 0, 1))) < 0.1:
            tempNP = target.attachNewNode('temp')
            normal.setZ(0)
            normal.normalize()
            lookAtNormal = Point3(normal)
            lookAtNormal *= -1
            tempNP.lookAt(lookAtNormal)
            realAngle = ROUND_TO(self.gridSnapNP.getH(tempNP), 90.0)
            if fClosest:
                angle = realAngle
            else:
                angle = 0
            self.gridSnapNP.setHpr(tempNP, angle, 0, 0)
            hitPoint = entry.getSurfacePoint(target)
            tempNP.setPos(hitPoint)
            if wallOffset == None:
                wallOffset = self.selectedObject.getWallOffset()
            self.gridSnapNP.setPos(tempNP, 0, -wallOffset, 0)
            tempNP.removeNode()
            if realAngle == 180.0:
                self.gridSnapNP.setH(self.gridSnapNP.getH() + 180.0)
            return 1
        return 0

    def rotateLeft(self):
        if not self.selectedObject:
            return
        so = self.selectedObject
        so.dfitem.startAdjustPosHpr()
        self.setPosHpr(so, 0, 0, 0, 0, 0, 0)
        self.moveObjectInit()
        if so.getOnWall():
            startR = self.gridSnapNP.getR()
            newR = ROUND_TO(startR + 22.5, 22.5)
            self.gridSnapNP.setR(newR)
        else:
            startH = self.gridSnapNP.getH(self.targetNodePath)
            newH = ROUND_TO(startH - 22.5, 22.5)
            self.iSphere.setParentNP(self.gridSnapNP)
            self.iSphere.setCenterRadius(0, Point3(0), so.radius * 1.25)
            entry = self.iSphere.pickBitMask(bitMask=so.getWallBitmask(), targetNodePath=self.targetNodePath, skipFlags=SKIP_CAMERA | SKIP_UNPICKABLE)
            if not entry:
                self.gridSnapNP.setHpr(self.targetNodePath, newH, 0, 0)
                self.collisionTest()
        so.wrtReparentTo(self.targetNodePath)
        self.disableButtonFrameTask()
        so.dfitem.stopAdjustPosHpr()

    def rotateRight(self):
        if not self.selectedObject:
            return
        so = self.selectedObject
        so.dfitem.startAdjustPosHpr()
        self.setPosHpr(so, 0, 0, 0, 0, 0, 0)
        self.moveObjectInit()
        if so.getOnWall():
            startR = self.gridSnapNP.getR()
            newR = ROUND_TO(startR - 22.5, 22.5)
            self.gridSnapNP.setR(newR)
        else:
            startH = self.gridSnapNP.getH(self.targetNodePath)
            newH = ROUND_TO(startH + 22.5, 22.5) % 360.0
            self.iSphere.setParentNP(self.gridSnapNP)
            self.iSphere.setCenterRadius(0, Point3(0), so.radius * 1.25)
            entry = self.iSphere.pickBitMask(bitMask=so.getWallBitmask(), targetNodePath=self.targetNodePath, skipFlags=SKIP_CAMERA | SKIP_UNPICKABLE)
            if not entry:
                self.gridSnapNP.setHpr(self.targetNodePath, newH, 0, 0)
                self.collisionTest()
        so.wrtReparentTo(self.targetNodePath)
        self.disableButtonFrameTask()
        so.dfitem.stopAdjustPosHpr()

    def moveObjectInit(self):
        self.dragPointNP.setPosHpr(self.selectedObject, self.selectedObject.dragPoint, Vec3(0))
        self.gridSnapNP.setPosHpr(0, 0, 0, 0, 0, 0)
        self.collisionOffsetNP.setPosHpr(0, 0, 0, 0, 0, 0)
        self.selectedObject.wrtReparentTo(self.collisionOffsetNP)

    def resetFurniture(self):
        for o in list(self.objectDict.values()):
            o.resetMovableObject()

        self.objectDict = {}
        self.deselectObject()
        self.buttonFrame.hide()

    def destroy(self):
        self.ignore('enterFurnitureMode')
        self.ignore('exitFurnitureMode')
        if self.guiInterval:
            self.guiInterval.finish()
        if self.furnitureManager:
            self.exitFurnitureMode(self.furnitureManager)
        self.cleanupDialog()
        self.resetFurniture()
        self.buttonFrame.destroy()
        self.furnitureGui.destroy()
        if self.houseExtents:
            self.houseExtents.removeNode()
        if self.doorBlocker:
            self.doorBlocker.removeNode()
        self.removeNode()
        if self.verifyFrame:
            self.verifyFrame.destroy()
            self.verifyFrame = None
            self.deleteItemText = None
            self.okButton = None
            self.cancelButton = None
        return

    def createSelectedObjectPanel(self, guiModels):
        self.buttonFrame = DirectFrame(scale=0.5)
        self.grabUp = guiModels.find('**/handup')
        self.grabDown = guiModels.find('**/handdown')
        self.grabRollover = guiModels.find('**/handrollover')
        self.centerMarker = DirectButton(parent=self.buttonFrame, text=['', TTLocalizer.HDMoveLabel], text_pos=(0, 1), text_scale=0.7, text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1), image=[self.grabUp, self.grabDown, self.grabRollover], image_scale=0.3, relief=None, scale=0.12)
        self.centerMarker.bind(DGG.B1PRESS, self.moveObjectContinue)
        self.centerMarker.bind(DGG.B1RELEASE, self.moveObjectStop)
        guiCCWArrowUp = guiModels.find('**/LarrowUp')
        guiCCWArrowDown = guiModels.find('**/LarrowDown')
        guiCCWArrowRollover = guiModels.find('**/LarrowRollover')
        self.rotateLeftButton = DirectButton(parent=self.buttonFrame, relief=None, image=(guiCCWArrowUp,
         guiCCWArrowDown,
         guiCCWArrowRollover,
         guiCCWArrowUp), image_pos=(0, 0, 0.1), image_scale=0.15, image3_color=Vec4(0.5, 0.5, 0.5, 0.75), text=('',
         TTLocalizer.HDRotateCCWLabel,
         TTLocalizer.HDRotateCCWLabel,
         ''), text_pos=(0.135, -0.1), text_scale=0.1, text_align=TextNode.ARight, text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1), pos=(-.125, 0, -.2), scale=0.7, command=self.rotateLeft)
        self.rotateLeftButton.bind(DGG.EXIT, self.enableButtonFrameTask)
        guiCWArrowUp = guiModels.find('**/RarrowUp')
        guiCWArrowDown = guiModels.find('**/RarrowDown')
        guiCWArrowRollover = guiModels.find('**/RarrowRollover')
        self.rotateRightButton = DirectButton(parent=self.buttonFrame, relief=None, image=(guiCWArrowUp,
         guiCWArrowDown,
         guiCWArrowRollover,
         guiCWArrowUp), image_pos=(0, 0, 0.1), image_scale=0.15, image3_color=Vec4(0.5, 0.5, 0.5, 0.75), text=('',
         TTLocalizer.HDRotateCWLabel,
         TTLocalizer.HDRotateCWLabel,
         ''), text_pos=(-0.135, -0.1), text_scale=0.1, text_align=TextNode.ALeft, text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1), pos=(0.125, 0, -0.2), scale=0.7, command=self.rotateRight)
        self.rotateRightButton.bind(DGG.EXIT, self.enableButtonFrameTask)
        self.buttonFrame.hide()
        return

    def recenterButtonFrameTask(self, state):
        if self.selectedObject and self.fRecenter:
            self.buttonFrame.setPos(self.getSelectedObjectScreenXY())
        return Task.cont

    def disableButtonFrameTask(self, event = None):
        self.fRecenter = 0

    def enableButtonFrameTask(self, event = None):
        self.fRecenter = 1

    def getNearProjectionPoint(self, nodePath):
        origin = nodePath.getPos(camera)
        if origin[1] != 0.0:
            return origin * (base.camLens.getNear() / origin[1])
        else:
            return Point3(0, base.camLens.getNear(), 0)

    def getSelectedObjectScreenXY(self):
        tNodePath = self.selectedObject.attachNewNode('temp')
        tNodePath.setPos(self.selectedObject.center)
        nearVec = self.getNearProjectionPoint(tNodePath)
        nearVec *= base.camLens.getFocalLength() / base.camLens.getNear()
        render2dX = CLAMP(nearVec[0] / (base.camLens.getFilmSize()[0] / 2.0), -.9, 0.9)
        aspect2dX = render2dX * base.getAspectRatio()
        aspect2dZ = CLAMP(nearVec[2] / (base.camLens.getFilmSize()[1] / 2.0), -.8, 0.9)
        tNodePath.removeNode()
        return Vec3(aspect2dX, 0, aspect2dZ)

    def createMainControls(self, guiModels):
        attic = guiModels.find('**/attic')
        self.furnitureGui = DirectFrame(relief=None, pos=(-1.19, 1, 0.33), scale=0.04, image=attic)
        bMoveStopUp = guiModels.find('**/bu_atticX/bu_attic_up')
        bMoveStopDown = guiModels.find('**/bu_atticX/bu_attic_down')
        bMoveStopRollover = guiModels.find('**/bu_atticX/bu_attic_rollover')
        self.bStopMoveFurniture = DirectButton(parent=self.furnitureGui, relief=None, image=[bMoveStopUp,
         bMoveStopDown,
         bMoveStopRollover,
         bMoveStopUp], text=['', TTLocalizer.HDStopMoveFurnitureButton, TTLocalizer.HDStopMoveFurnitureButton], text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1), text_font=ToontownGlobals.getInterfaceFont(), pos=(-0.3, 0, 9.4), command=base.localAvatar.stopMoveFurniture)
        self.bindHelpText(self.bStopMoveFurniture, 'DoneMoving')
        self.atticRoof = DirectLabel(parent=self.furnitureGui, relief=None, image=guiModels.find('**/rooftile'))
        self.itemBackgroundFrame = DirectFrame(parent=self.furnitureGui, relief=None, image=guiModels.find('**/item_backgroun'), image_pos=(0, 0, -22), image_scale=(1, 1, 5))
        self.scrollUpFrame = DirectFrame(parent=self.furnitureGui, relief=None, image=guiModels.find('**/scrollup'), pos=(0, 0, -0.58))
        self.camButtonFrame = DirectFrame(parent=self.furnitureGui, relief=None, image=guiModels.find('**/low'), pos=(0, 0, -11.69))
        tagUp = guiModels.find('**/tag_up')
        tagDown = guiModels.find('**/tag_down')
        tagRollover = guiModels.find('**/tag_rollover')
        self.inAtticButton = DirectButton(parent=self.itemBackgroundFrame, relief=None, text=TTLocalizer.HDInAtticLabel, text_pos=(-0.1, -0.25), image=[tagUp, tagDown, tagRollover], pos=(2.85, 0, 4), scale=0.8, command=self.showAtticPicker)
        self.bindHelpText(self.inAtticButton, 'Attic')
        self.inRoomButton = DirectButton(parent=self.itemBackgroundFrame, relief=None, text=TTLocalizer.HDInRoomLabel, text_pos=(-0.1, -0.25), image=[tagUp, tagDown, tagRollover], pos=(2.85, 0, 1.1), scale=0.8, command=self.showInRoomPicker)
        self.bindHelpText(self.inRoomButton, 'Room')
        self.inTrashButton = DirectButton(parent=self.itemBackgroundFrame, relief=None, text=TTLocalizer.HDInTrashLabel, text_pos=(-0.1, -0.25), image=[tagUp, tagDown, tagRollover], pos=(2.85, 0, -1.8), scale=0.8, command=self.showInTrashPicker)
        self.bindHelpText(self.inTrashButton, 'Trash')
        for i in range(4):
            self.inAtticButton.component('text%d' % i).setR(-90)
            self.inRoomButton.component('text%d' % i).setR(-90)
            self.inTrashButton.component('text%d' % i).setR(-90)

        backInAtticUp = guiModels.find('**/bu_backinattic_up1')
        backInAtticDown = guiModels.find('**/bu_backinattic_down1')
        backInAtticRollover = guiModels.find('**/bu_backinattic_rollover2')
        self.sendToAtticButton = DirectButton(parent=self.furnitureGui, relief=None, pos=(0.4, 0, 12.8), text=['', TTLocalizer.HDToAtticLabel], text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1), text_pos=(1.2, -0.3), image=[backInAtticUp, backInAtticDown, backInAtticRollover], command=self.sendItemToAttic)
        self.sendToAtticButton.hide()
        self.bindHelpText(self.sendToAtticButton, 'SendToAttic')
        zoomInUp = guiModels.find('**/bu_RzoomOut_up')
        zoomInDown = guiModels.find('**/bu_RzoomOut_down')
        zoomInRollover = guiModels.find('**/bu_RzoomOut_rollover')
        self.zoomInButton = DirectButton(parent=self.camButtonFrame, image=[zoomInUp, zoomInDown, zoomInRollover], relief=None, pos=(0.9, 0, -0.75), command=self.zoomCamIn)
        self.bindHelpText(self.zoomInButton, 'ZoomIn')
        zoomOutUp = guiModels.find('**/bu_LzoomIn_up')
        zoomOutDown = guiModels.find('**/bu_LzoomIn_down')
        zoomOutRollover = guiModels.find('**/buLzoomIn_rollover')
        self.zoomOutButton = DirectButton(parent=self.camButtonFrame, image=[zoomOutUp, zoomOutDown, zoomOutRollover], relief=None, pos=(-1.4, 0, -0.75), command=self.zoomCamOut)
        self.bindHelpText(self.zoomOutButton, 'ZoomOut')
        camCCWUp = guiModels.find('**/bu_Rarrow_up1')
        camCCWDown = guiModels.find('**/bu_Rarrow_down1')
        camCCWRollover = guiModels.find('**/bu_Rarrow_orllover')
        self.rotateCamLeftButton = DirectButton(parent=self.camButtonFrame, image=[camCCWUp, camCCWDown, camCCWRollover], relief=None, pos=(0.9, 0, -3.0), command=self.rotateCamCCW)
        self.bindHelpText(self.rotateCamLeftButton, 'RotateLeft')
        camCWUp = guiModels.find('**/bu_Larrow_up1')
        camCWDown = guiModels.find('**/bu_Larrow_down1')
        camCWRollover = guiModels.find('**/bu_Larrow_rollover2')
        self.rotateCamRightButton = DirectButton(parent=self.camButtonFrame, image=[camCWUp, camCWDown, camCWRollover], relief=None, pos=(-1.4, 0, -3.0), command=self.rotateCamCW)
        self.bindHelpText(self.rotateCamRightButton, 'RotateRight')
        trashcanGui = loader.loadModel('phase_3/models/gui/trashcan_gui')
        trashcanUp = trashcanGui.find('**/TrashCan_CLSD')
        trashcanDown = trashcanGui.find('**/TrashCan_OPEN')
        trashcanRollover = trashcanGui.find('**/TrashCan_RLVR')
        self.deleteEnterButton = DirectButton(parent=self.furnitureGui, image=(trashcanUp,
         trashcanDown,
         trashcanRollover,
         trashcanUp), text=['',
         TTLocalizer.InventoryDelete,
         TTLocalizer.InventoryDelete,
         ''], text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1), text_scale=0.1, text_align=TextNode.ACenter, text_pos=(0, -0.12), text_font=ToontownGlobals.getInterfaceFont(), textMayChange=0, relief=None, pos=(3.7, 0.0, -13.8), scale=7.13, command=self.enterDeleteMode)
        self.bindHelpText(self.deleteEnterButton, 'DeleteEnter')
        self.deleteExitButton = DirectButton(parent=self.furnitureGui, image=(trashcanUp,
         trashcanDown,
         trashcanRollover,
         trashcanUp), text=('',
         TTLocalizer.InventoryDone,
         TTLocalizer.InventoryDone,
         ''), text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1), text_scale=0.1, text_align=TextNode.ACenter, text_pos=(0, -0.12), text_font=ToontownGlobals.getInterfaceFont(), textMayChange=0, relief=None, pos=(3.7, 0.0, -13.8), scale=7.13, command=self.exitDeleteMode)
        self.bindHelpText(self.deleteExitButton, 'DeleteExit')
        self.deleteExitButton.hide()
        self.trashcanBase = DirectLabel(parent=self.furnitureGui, image=guiModels.find('**/trashcan_base'), relief=None, pos=(0, 0, -11.64))
        self.furnitureGui.hide()
        self.helpText = DirectLabel(parent=self.furnitureGui, relief=DGG.SUNKEN, frameSize=(-0.5,
         10,
         -3,
         0.9), frameColor=(0.2, 0.2, 0.2, 0.5), borderWidth=(0.01, 0.01), text='', text_wordwrap=12, text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1), text_scale=0.8, pos=(3, 0.0, -7), scale=1, text_align=TextNode.ALeft)
        self.helpText.hide()
        return

    def createAtticPicker(self):
        self.atticItemPanels = []
        for itemIndex in range(len(self.furnitureManager.atticItems)):
            panel = FurnitureItemPanel(self.furnitureManager.atticItems[itemIndex], itemIndex, command=self.bringItemFromAttic, deleteMode=self.deleteMode, helpCategory='FurnitureItemPanelAttic')
            self.atticItemPanels.append(panel)

        self.atticWallpaperPanels = []
        for itemIndex in range(len(self.furnitureManager.atticWallpaper)):
            panel = FurnitureItemPanel(self.furnitureManager.atticWallpaper[itemIndex], itemIndex, command=self.bringWallpaperFromAttic, deleteMode=self.deleteMode, helpCategory='FurnitureItemPanelAttic')
            self.atticWallpaperPanels.append(panel)

        self.atticWindowPanels = []
        for itemIndex in range(len(self.furnitureManager.atticWindows)):
            panel = FurnitureItemPanel(self.furnitureManager.atticWindows[itemIndex], itemIndex, command=self.bringWindowFromAttic, deleteMode=self.deleteMode, helpCategory='FurnitureItemPanelAttic')
            self.atticWindowPanels.append(panel)

        self.regenerateAtticPicker()

    def regenerateAtticPicker(self):
        selectedIndex = 0
        if self.atticPicker:
            selectedIndex = self.atticPicker.getSelectedIndex()
            for panel in self.atticItemPanels:
                panel.detachNode()

            for panel in self.atticWallpaperPanels:
                panel.detachNode()

            for panel in self.atticWindowPanels:
                panel.detachNode()

            self.atticPicker.destroy()
            self.atticPicker = None
        itemList = self.atticItemPanels + self.atticWallpaperPanels + self.atticWindowPanels
        if self.deleteMode:
            text = TTLocalizer.HDDeletePickerLabel
        else:
            text = TTLocalizer.HDAtticPickerLabel
        self.atticPicker = self.createScrolledList(itemList, text, 'atticPicker', selectedIndex)
        if self.inRoomPicker or self.inTrashPicker:
            self.atticPicker.hide()
        else:
            self.atticPicker.show()
        return

    def createInRoomPicker(self):
        self.inRoomPanels = []
        for objectId, object in list(self.objectDict.items()):
            panel = FurnitureItemPanel(object.dfitem.item, objectId, command=self.requestReturnToAttic, deleteMode=self.deleteMode, withinFunc=self.pickInRoom, helpCategory='FurnitureItemPanelRoom')
            self.inRoomPanels.append(panel)

        self.regenerateInRoomPicker()

    def regenerateInRoomPicker(self):
        selectedIndex = 0
        if self.inRoomPicker:
            selectedIndex = self.inRoomPicker.getSelectedIndex()
            for panel in self.inRoomPanels:
                panel.detachNode()

            self.inRoomPicker.destroy()
            self.inRoomPicker = None
        if self.deleteMode:
            text = TTLocalizer.HDDeletePickerLabel
        else:
            text = TTLocalizer.HDInRoomPickerLabel
        self.inRoomPicker = self.createScrolledList(self.inRoomPanels, text, 'inRoomPicker', selectedIndex)
        return

    def createInTrashPicker(self):
        self.inTrashPanels = []
        for itemIndex in range(len(self.furnitureManager.deletedItems)):
            panel = FurnitureItemPanel(self.furnitureManager.deletedItems[itemIndex], itemIndex, command=self.requestReturnToAtticFromTrash, helpCategory='FurnitureItemPanelTrash')
            self.inTrashPanels.append(panel)

        self.regenerateInTrashPicker()

    def regenerateInTrashPicker(self):
        selectedIndex = 0
        if self.inTrashPicker:
            selectedIndex = self.inTrashPicker.getSelectedIndex()
            for panel in self.inTrashPanels:
                panel.detachNode()

            self.inTrashPicker.destroy()
            self.inTrashPicker = None
        text = TTLocalizer.HDInTrashPickerLabel
        self.inTrashPicker = self.createScrolledList(self.inTrashPanels, text, 'inTrashPicker', selectedIndex)
        return

    def createScrolledList(self, itemList, text, name, selectedIndex):
        gui = loader.loadModel('phase_3.5/models/gui/friendslist_gui')
        picker = DirectScrolledList(parent=self.furnitureGui, pos=(-0.38, 0.0, 3), scale=7.125, relief=None, items=itemList, numItemsVisible=5, text=text, text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1), text_scale=0.1, text_pos=(0, 0.4), decButton_image=(gui.find('**/FndsLst_ScrollUp'),
         gui.find('**/FndsLst_ScrollDN'),
         gui.find('**/FndsLst_ScrollUp_Rllvr'),
         gui.find('**/FndsLst_ScrollUp')), decButton_relief=None, decButton_scale=(1.5, 1.5, 1.5), decButton_pos=(0, 0, 0.3), decButton_image3_color=Vec4(1, 1, 1, 0.1), incButton_image=(gui.find('**/FndsLst_ScrollUp'),
         gui.find('**/FndsLst_ScrollDN'),
         gui.find('**/FndsLst_ScrollUp_Rllvr'),
         gui.find('**/FndsLst_ScrollUp')), incButton_relief=None, incButton_scale=(1.5, 1.5, -1.5), incButton_pos=(0, 0, -1.878), incButton_image3_color=Vec4(1, 1, 1, 0.1))
        picker.setName(name)
        picker.scrollTo(selectedIndex)
        return picker

    def reset():
        self.destroy()
        furnitureMenu.destroy()

    def showAtticPicker(self):
        if self.inRoomPicker:
            self.inRoomPicker.destroy()
            self.inRoomPicker = None
        if self.inTrashPicker:
            self.inTrashPicker.destroy()
            self.inTrashPicker = None
        self.atticPicker.show()
        self.inAtticButton['image_color'] = Vec4(1, 1, 1, 1)
        self.inRoomButton['image_color'] = Vec4(0.8, 0.8, 0.8, 1)
        self.inTrashButton['image_color'] = Vec4(0.8, 0.8, 0.8, 1)
        self.deleteExitButton['state'] = 'normal'
        self.deleteEnterButton['state'] = 'normal'
        return

    def showInRoomPicker(self):
        messenger.send('wakeup')
        if not self.inRoomPicker:
            self.createInRoomPicker()
        self.atticPicker.hide()
        if self.inTrashPicker:
            self.inTrashPicker.destroy()
            self.inTrashPicker = None
        self.inAtticButton['image_color'] = Vec4(0.8, 0.8, 0.8, 1)
        self.inRoomButton['image_color'] = Vec4(1, 1, 1, 1)
        self.inTrashButton['image_color'] = Vec4(0.8, 0.8, 0.8, 1)
        self.deleteExitButton['state'] = 'normal'
        self.deleteEnterButton['state'] = 'normal'
        return

    def showInTrashPicker(self):
        messenger.send('wakeup')
        if not self.inTrashPicker:
            self.createInTrashPicker()
        self.atticPicker.hide()
        if self.inRoomPicker:
            self.inRoomPicker.destroy()
            self.inRoomPicker = None
        self.inAtticButton['image_color'] = Vec4(0.8, 0.8, 0.8, 1)
        self.inRoomButton['image_color'] = Vec4(0.8, 0.8, 0.8, 1)
        self.inTrashButton['image_color'] = Vec4(1, 1, 1, 1)
        self.deleteExitButton['state'] = 'disabled'
        self.deleteEnterButton['state'] = 'disabled'
        return

    def sendItemToAttic(self):
        if base.config.GetBool('want-qa-regression', 0):
            self.notify.info('QA-REGRESSION: ESTATE:  Send Item to Attic')
        messenger.send('wakeup')
        if self.selectedObject:
            callback = PythonUtil.Functor(self.__sendItemToAtticCallback, self.selectedObject.id())
            self.furnitureManager.moveItemToAttic(self.selectedObject.dfitem, callback)
            self.deselectObject()

    def __sendItemToAtticCallback(self, objectId, retcode, item):
        self.__enableItemButtons(1)
        if retcode < 0:
            self.notify.info('Unable to send item %s to attic, reason %s.' % (item.getName(), retcode))
            return
        del self.objectDict[objectId]
        if self.selectedObject != None and self.selectedObject.id() == objectId:
            self.selectedObject.detachNode()
            self.deselectObject()
        itemIndex = len(self.atticItemPanels)
        panel = FurnitureItemPanel(item, itemIndex, command=self.bringItemFromAttic, deleteMode=self.deleteMode, helpCategory='FurnitureItemPanelAttic')
        self.atticItemPanels.append(panel)
        self.regenerateAtticPicker()
        if self.inRoomPicker:
            for i in range(len(self.inRoomPanels)):
                if self.inRoomPanels[i].itemId == objectId:
                    del self.inRoomPanels[i]
                    self.regenerateInRoomPicker()
                    return

        return

    def cleanupDialog(self, buttonValue = None):
        if self.dialog:
            self.dialog.cleanup()
            self.dialog = None
            self.__enableItemButtons(1)
        return

    def enterDeleteMode(self):
        self.deleteMode = 1
        self.__updateDeleteMode()

    def exitDeleteMode(self):
        self.deleteMode = 0
        self.__updateDeleteMode()

    def __updateDeleteMode(self):
        if not self.atticPicker:
            return
        self.notify.debug('__updateDeleteMode deleteMode=%s' % self.deleteMode)
        if self.deleteMode:
            framePanelColor = DeletePickerPanelColor
            atticText = TTLocalizer.HDDeletePickerLabel
            inRoomText = TTLocalizer.HDDeletePickerLabel
            helpCategory = 'FurnitureItemPanelDelete'
        else:
            framePanelColor = NormalPickerPanelColor
            atticText = TTLocalizer.HDAtticPickerLabel
            inRoomText = TTLocalizer.HDInRoomPickerLabel
            helpCategory = None
        if self.inRoomPicker:
            self.inRoomPicker['text'] = inRoomText
            for panel in self.inRoomPicker['items']:
                panel.setDeleteMode(self.deleteMode)
                panel.bindHelpText(helpCategory)

        if self.atticPicker:
            self.atticPicker['text'] = atticText
            for panel in self.atticPicker['items']:
                panel.setDeleteMode(self.deleteMode)
                panel.bindHelpText(helpCategory)

        self.__updateDeleteButtons()
        return

    def __updateDeleteButtons(self):
        if self.deleteMode:
            self.deleteExitButton.show()
            self.deleteEnterButton.hide()
        else:
            self.deleteEnterButton.show()
            self.deleteExitButton.hide()

    def deleteItemFromRoom(self, dfitem, objectId, itemIndex):
        messenger.send('wakeup')
        callback = PythonUtil.Functor(self.__deleteItemFromRoomCallback, objectId, itemIndex)
        self.furnitureManager.deleteItemFromRoom(dfitem, callback)

    def __deleteItemFromRoomCallback(self, objectId, itemIndex, retcode, item):
        self.__enableItemButtons(1)
        if retcode < 0:
            self.notify.info('Unable to delete item %s from room, reason %s.' % (item.getName(), retcode))
            return
        del self.objectDict[objectId]
        if self.selectedObject != None and self.selectedObject.id() == objectId:
            self.selectedObject.detachNode()
            self.deselectObject()
        if self.inRoomPicker and itemIndex is not None:
            del self.inRoomPanels[itemIndex]
            self.regenerateInRoomPicker()
        return

    def bringItemFromAttic(self, item, itemIndex):
        if base.config.GetBool('want-qa-regression', 0):
            self.notify.info('QA-REGRESSION: ESTATE: Place Item in Room')
        messenger.send('wakeup')
        self.__enableItemButtons(0)
        if self.deleteMode:
            self.requestDelete(item, itemIndex, self.deleteItemFromAttic)
            return
        pos = self.targetNodePath.getRelativePoint(base.localAvatar, Point3(0, 2, 0))
        hpr = Point3(0, 0, 0)
        if abs(pos[0]) > 3000 or abs(pos[1]) > 3000 or abs(pos[2]) > 300:
            self.notify.warning('bringItemFromAttic extreme pos targetNodePath=%s avatar=%s %s' % (repr(self.targetNodePath.getPos(render)), repr(base.localAvatar.getPos(render)), repr(pos)))
        if item.getFlags() & CatalogFurnitureItem.FLPainting:
            for object in list(self.objectDict.values()):
                object.stashBuiltInCollisionNodes()

            self.gridSnapNP.setPosHpr(0, 0, 0, 0, 0, 0)
            target = self.targetNodePath
            self.iRay.setParentNP(base.localAvatar)
            entry = self.iRay.pickBitMask3D(bitMask=ToontownGlobals.WallBitmask, targetNodePath=target, origin=Point3(0, 0, 6), dir=Vec3(0, 1, 0), skipFlags=SKIP_BACKFACE | SKIP_CAMERA | SKIP_UNPICKABLE)
            for object in list(self.objectDict.values()):
                object.unstashBuiltInCollisionNodes()

            if entry:
                self.alignObject(entry, target, fClosest=0, wallOffset=0.1)
                pos = self.gridSnapNP.getPos(target)
                hpr = self.gridSnapNP.getHpr(target)
            else:
                self.notify.warning('wall not found for painting')
        self.furnitureManager.moveItemFromAttic(itemIndex, (pos[0],
         pos[1],
         pos[2],
         hpr[0],
         hpr[1],
         hpr[2]), self.__bringItemFromAtticCallback)

    def __bringItemFromAtticCallback(self, retcode, dfitem, itemIndex):
        self.__enableItemButtons(1)
        if retcode < 0:
            self.notify.info('Unable to bring furniture item %s into room, reason %s.' % (itemIndex, retcode))
            return
        mo = self.loadObject(dfitem)
        objectId = mo.id()
        self.atticItemPanels[itemIndex].destroy()
        del self.atticItemPanels[itemIndex]
        for i in range(itemIndex, len(self.atticItemPanels)):
            self.atticItemPanels[i].itemId -= 1

        self.regenerateAtticPicker()
        if self.inRoomPicker:
            panel = FurnitureItemPanel(dfitem.item, objectId, command=self.requestReturnToAttic, helpCategory='FurnitureItemPanelRoom')
            self.inRoomPanels.append(panel)
            self.regenerateInRoomPicker()

    def deleteItemFromAttic(self, item, itemIndex):
        messenger.send('wakeup')
        self.furnitureManager.deleteItemFromAttic(item, itemIndex, self.__deleteItemFromAtticCallback)

    def __deleteItemFromAtticCallback(self, retcode, item, itemIndex):
        self.__enableItemButtons(1)
        if retcode < 0:
            self.notify.info('Unable to delete furniture item %s, reason %s.' % (itemIndex, retcode))
            return
        self.atticItemPanels[itemIndex].destroy()
        del self.atticItemPanels[itemIndex]
        for i in range(itemIndex, len(self.atticItemPanels)):
            self.atticItemPanels[i].itemId -= 1

        self.regenerateAtticPicker()

    def bringWallpaperFromAttic(self, item, itemIndex):
        messenger.send('wakeup')
        self.__enableItemButtons(0)
        if self.deleteMode:
            self.requestDelete(item, itemIndex, self.deleteWallpaperFromAttic)
            return
        if base.localAvatar.getY() < 2.3:
            room = 0
        else:
            room = 1
        self.furnitureManager.moveWallpaperFromAttic(itemIndex, room, self.__bringWallpaperFromAtticCallback)

    def __bringWallpaperFromAtticCallback(self, retcode, itemIndex, room):
        self.__enableItemButtons(1)
        if retcode < 0:
            self.notify.info('Unable to bring wallpaper %s into room %s, reason %s.' % (itemIndex, room, retcode))
            return
        self.atticWallpaperPanels[itemIndex].destroy()
        item = self.furnitureManager.atticWallpaper[itemIndex]
        panel = FurnitureItemPanel(item, itemIndex, command=self.bringWallpaperFromAttic, deleteMode=self.deleteMode, helpCategory='FurnitureItemPanelAttic')
        self.atticWallpaperPanels[itemIndex] = panel
        self.regenerateAtticPicker()

    def deleteWallpaperFromAttic(self, item, itemIndex):
        messenger.send('wakeup')
        self.furnitureManager.deleteWallpaperFromAttic(item, itemIndex, self.__deleteWallpaperFromAtticCallback)

    def __deleteWallpaperFromAtticCallback(self, retcode, item, itemIndex):
        self.__enableItemButtons(1)
        if retcode < 0:
            self.notify.info('Unable to delete wallpaper %s, reason %s.' % (itemIndex, retcode))
            return
        self.atticWallpaperPanels[itemIndex].destroy()
        del self.atticWallpaperPanels[itemIndex]
        for i in range(itemIndex, len(self.atticWallpaperPanels)):
            self.atticWallpaperPanels[i].itemId -= 1

        self.regenerateAtticPicker()

    def bringWindowFromAttic(self, item, itemIndex):
        messenger.send('wakeup')
        self.__enableItemButtons(0)
        if self.deleteMode:
            self.requestDelete(item, itemIndex, self.deleteWindowFromAttic)
            return
        if base.localAvatar.getY() < 2.3:
            slot = 2
        else:
            slot = 4
        self.furnitureManager.moveWindowFromAttic(itemIndex, slot, self.__bringWindowFromAtticCallback)

    def __bringWindowFromAtticCallback(self, retcode, itemIndex, slot):
        self.__enableItemButtons(1)
        if retcode < 0:
            self.notify.info('Unable to bring window %s into slot %s, reason %s.' % (itemIndex, slot, retcode))
            return
        if retcode == ToontownGlobals.FM_SwappedItem:
            self.atticWindowPanels[itemIndex].destroy()
            item = self.furnitureManager.atticWindows[itemIndex]
            panel = FurnitureItemPanel(item, itemIndex, command=self.bringWindowFromAttic, deleteMode=self.deleteMode, helpCategory='FurnitureItemPanelAttic')
            self.atticWindowPanels[itemIndex] = panel
        else:
            self.atticWindowPanels[itemIndex].destroy()
            del self.atticWindowPanels[itemIndex]
            for i in range(itemIndex, len(self.atticWindowPanels)):
                self.atticWindowPanels[i].itemId -= 1

        self.regenerateAtticPicker()

    def deleteWindowFromAttic(self, item, itemIndex):
        messenger.send('wakeup')
        self.furnitureManager.deleteWindowFromAttic(item, itemIndex, self.__deleteWindowFromAtticCallback)

    def __deleteWindowFromAtticCallback(self, retcode, item, itemIndex):
        self.__enableItemButtons(1)
        if retcode < 0:
            self.notify.info('Unable to delete window %s, reason %s.' % (itemIndex, retcode))
            return
        self.atticWindowPanels[itemIndex].destroy()
        del self.atticWindowPanels[itemIndex]
        for i in range(itemIndex, len(self.atticWindowPanels)):
            self.atticWindowPanels[i].itemId -= 1

        self.regenerateAtticPicker()

    def setGridSpacingString(self, spacingStr):
        spacing = eval(spacingStr)
        self.setGridSpacing(spacing)

    def setGridSpacing(self, gridSpacing):
        self.gridSpacing = gridSpacing

    def makeHouseExtentsBox(self):
        houseGeom = self.targetNodePath.findAllMatches('**/group*')
        targetBounds = houseGeom.getTightBounds()
        self.houseExtents = self.targetNodePath.attachNewNode('furnitureCollisionNode')
        mx = targetBounds[0][0]
        Mx = targetBounds[1][0]
        my = targetBounds[0][1]
        My = targetBounds[1][1]
        mz = targetBounds[0][2]
        Mz = targetBounds[1][2]
        cn = CollisionNode('extentsCollisionNode')
        cn.setIntoCollideMask(ToontownGlobals.GhostBitmask)
        self.houseExtents.attachNewNode(cn)
        cp = CollisionPolygon(Point3(mx, my, mz), Point3(mx, My, mz), Point3(mx, My, Mz), Point3(mx, my, Mz))
        cn.addSolid(cp)
        cp = CollisionPolygon(Point3(Mx, My, mz), Point3(Mx, my, mz), Point3(Mx, my, Mz), Point3(Mx, My, Mz))
        cn.addSolid(cp)
        cp = CollisionPolygon(Point3(Mx, my, mz), Point3(mx, my, mz), Point3(mx, my, Mz), Point3(Mx, my, Mz))
        cn.addSolid(cp)
        cp = CollisionPolygon(Point3(mx, My, mz), Point3(Mx, My, mz), Point3(Mx, My, Mz), Point3(mx, My, Mz))
        cn.addSolid(cp)

    def makeDoorBlocker(self):
        self.doorBlocker = self.targetNodePath.attachNewNode('doorBlocker')
        cn = CollisionNode('doorBlockerCollisionNode')
        cn.setIntoCollideMask(ToontownGlobals.FurnitureSideBitmask)
        self.doorBlocker.attachNewNode(cn)
        cs = CollisionSphere(Point3(-12, -33, 0), 7.5)
        cn.addSolid(cs)

    def createVerifyDialog(self, item, verifyText, okFunc, cancelFunc):
        if self.verifyFrame == None:
            buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
            okButtonImage = (buttons.find('**/ChtBx_OKBtn_UP'), buttons.find('**/ChtBx_OKBtn_DN'), buttons.find('**/ChtBx_OKBtn_Rllvr'))
            cancelButtonImage = (buttons.find('**/CloseBtn_UP'), buttons.find('**/CloseBtn_DN'), buttons.find('**/CloseBtn_Rllvr'))
            self.verifyFrame = DirectFrame(pos=(-0.4, 0.1, 0.3), scale=0.75, relief=None, image=DGG.getDefaultDialogGeom(), image_color=ToontownGlobals.GlobalDialogColor, image_scale=(1.2, 1, 1.3), text='', text_wordwrap=19, text_scale=0.06, text_pos=(0, 0.5), textMayChange=1, sortOrder=DGG.NO_FADE_SORT_INDEX)
            self.okButton = DirectButton(parent=self.verifyFrame, image=okButtonImage, relief=None, text=OTPLocalizer.DialogOK, text_scale=0.05, text_pos=(0.0, -0.1), textMayChange=0, pos=(-0.22, 0.0, -0.5))
            self.cancelButton = DirectButton(parent=self.verifyFrame, image=cancelButtonImage, relief=None, text=OTPLocalizer.DialogCancel, text_scale=0.05, text_pos=(0.0, -0.1), textMayChange=0, pos=(0.22, 0.0, -0.5))
            self.deleteItemText = DirectLabel(parent=self.verifyFrame, relief=None, text='', text_wordwrap=16, pos=(0.0, 0.0, -0.4), scale=0.09)
        self.verifyFrame['text'] = verifyText
        self.deleteItemText['text'] = item.getName()
        self.okButton['command'] = okFunc
        self.cancelButton['command'] = cancelFunc
        self.verifyFrame.show()
        self.itemPanel, self.itemIval = item.getPicture(base.localAvatar)
        if self.itemPanel:
            self.itemPanel.reparentTo(self.verifyFrame, -1)
            self.itemPanel.setPos(0, 0, 0.05)
            self.itemPanel.setScale(0.35)
            self.deleteItemText.setPos(0.0, 0.0, -0.4)
        else:
            self.deleteItemText.setPos(0, 0, 0.07)
        if self.itemIval:
            self.itemIval.loop()
        return

    def __handleVerifyDeleteOK(self):
        if base.config.GetBool('want-qa-regression', 0):
            self.notify.info('QA-REGRESSION: ESTATE:  Send Item to Trash')
        deleteFunction = self.verifyItems[0]
        deleteFunctionArgs = self.verifyItems[1:]
        self.__cleanupVerifyDelete()
        deleteFunction(*deleteFunctionArgs)

    def __cleanupVerifyDelete(self, *args):
        if self.nonDeletableItem:
            self.nonDeletableItem.cleanup()
            self.nonDeletableItem = None
        if self.verifyFrame:
            self.verifyFrame.hide()
        if self.itemIval:
            self.itemIval.finish()
            self.itemIval = None
        if self.itemPanel:
            self.itemPanel.destroy()
            self.itemPanel = None
        self.verifyItems = None
        return

    def __enableItemButtons(self, enabled):
        self.notify.debug('__enableItemButtons %d' % enabled)
        if enabled:
            buttonState = DGG.NORMAL
        else:
            buttonState = DGG.DISABLED
        if hasattr(self, 'inAtticButton'):
            self.inAtticButton['state'] = buttonState
        if hasattr(self, 'inRoomButton'):
            self.inRoomButton['state'] = buttonState
        if hasattr(self, 'inTrashButton'):
            self.inTrashButton['state'] = buttonState
        pickers = [self.atticPicker, self.inRoomPicker, self.inTrashPicker]
        for picker in pickers:
            if picker:
                for panel in picker['items']:
                    if not panel.isEmpty():
                        panel.enable(enabled)

    def __resetAndCleanup(self, *args):
        self.__enableItemButtons(1)
        self.__cleanupVerifyDelete()

    def requestDelete(self, item, itemIndex, deleteFunction):
        self.__cleanupVerifyDelete()
        if self.furnitureManager.ownerId != base.localAvatar.doId or not item.isDeletable():
            self.warnNonDeletableItem(item)
            return
        self.createVerifyDialog(item, TTLocalizer.HDDeleteItem, self.__handleVerifyDeleteOK, self.__resetAndCleanup)
        self.verifyItems = (deleteFunction, item, itemIndex)

    def requestRoomDelete(self, dfitem, objectId, itemIndex):
        self.__cleanupVerifyDelete()
        item = dfitem.item
        if self.furnitureManager.ownerId != base.localAvatar.doId or not item.isDeletable():
            self.warnNonDeletableItem(item)
            return
        self.createVerifyDialog(item, TTLocalizer.HDDeleteItem, self.__handleVerifyDeleteOK, self.__resetAndCleanup)
        self.verifyItems = (self.deleteItemFromRoom,
         dfitem,
         objectId,
         itemIndex)

    def warnNonDeletableItem(self, item):
        message = TTLocalizer.HDNonDeletableItem
        if not item.isDeletable():
            if item.getFlags() & CatalogFurnitureItem.FLBank:
                message = TTLocalizer.HDNonDeletableBank
            elif item.getFlags() & CatalogFurnitureItem.FLCloset:
                message = TTLocalizer.HDNonDeletableCloset
            elif item.getFlags() & CatalogFurnitureItem.FLPhone:
                message = TTLocalizer.HDNonDeletablePhone
            elif item.getFlags() & CatalogFurnitureItem.FLTrunk:
                message = TTLocalizer.HDNonDeletableTrunk
        if self.furnitureManager.ownerId != base.localAvatar.doId:
            message = TTLocalizer.HDNonDeletableNotOwner % self.furnitureManager.ownerName
        self.nonDeletableItem = TTDialog.TTDialog(text=message, style=TTDialog.Acknowledge, fadeScreen=0, command=self.__resetAndCleanup)
        self.nonDeletableItem.show()

    def requestReturnToAttic(self, item, objectId):
        self.__cleanupVerifyDelete()
        itemIndex = None
        for i in range(len(self.inRoomPanels)):
            if self.inRoomPanels[i].itemId == objectId:
                itemIndex = i
                self.__enableItemButtons(0)
                break

        if self.deleteMode:
            dfitem = self.objectDict[objectId].dfitem
            self.requestRoomDelete(dfitem, objectId, itemIndex)
            return
        self.createVerifyDialog(item, TTLocalizer.HDReturnVerify, self.__handleVerifyReturnOK, self.__resetAndCleanup)
        self.verifyItems = (item, objectId)
        return

    def __handleVerifyReturnOK(self):
        item, objectId = self.verifyItems
        self.__cleanupVerifyDelete()
        self.pickInRoom(objectId)
        self.sendItemToAttic()

    def requestReturnToAtticFromTrash(self, item, itemIndex):
        self.__cleanupVerifyDelete()
        self.__enableItemButtons(0)
        self.createVerifyDialog(item, TTLocalizer.HDReturnFromTrashVerify, self.__handleVerifyReturnFromTrashOK, self.__resetAndCleanup)
        self.verifyItems = (item, itemIndex)

    def __handleVerifyReturnFromTrashOK(self):
        if base.config.GetBool('want-qa-regression', 0):
            self.notify.info('QA-REGRESSION: ESTATE:  Send Item to Attic')
        item, itemIndex = self.verifyItems
        self.__cleanupVerifyDelete()
        self.recoverDeletedItem(item, itemIndex)

    def recoverDeletedItem(self, item, itemIndex):
        messenger.send('wakeup')
        self.furnitureManager.recoverDeletedItem(item, itemIndex, self.__recoverDeletedItemCallback)

    def __recoverDeletedItemCallback(self, retcode, item, itemIndex):
        self.__cleanupVerifyDelete()
        if retcode < 0:
            if retcode == ToontownGlobals.FM_HouseFull:
                self.showHouseFullDialog()
            self.notify.info('Unable to recover deleted item %s, reason %s.' % (itemIndex, retcode))
            return
        self.__enableItemButtons(1)
        self.inTrashPanels[itemIndex].destroy()
        del self.inTrashPanels[itemIndex]
        for i in range(itemIndex, len(self.inTrashPanels)):
            self.inTrashPanels[i].itemId -= 1

        self.regenerateInTrashPicker()
        itemType = item.getTypeCode()
        if itemType == CatalogItemTypes.WALLPAPER_ITEM or itemType == CatalogItemTypes.FLOORING_ITEM or itemType == CatalogItemTypes.MOULDING_ITEM or itemType == CatalogItemTypes.WAINSCOTING_ITEM:
            itemIndex = len(self.atticWallpaperPanels)
            bringCommand = self.bringWallpaperFromAttic
        elif itemType == CatalogItemTypes.WINDOW_ITEM:
            itemIndex = len(self.atticWindowPanels)
            bringCommand = self.bringWindowFromAttic
        else:
            itemIndex = len(self.atticItemPanels)
            bringCommand = self.bringItemFromAttic
        panel = FurnitureItemPanel(item, itemIndex, command=bringCommand, deleteMode=self.deleteMode, helpCategory='FurnitureItemPanelAttic')
        if itemType == CatalogItemTypes.WALLPAPER_ITEM or itemType == CatalogItemTypes.FLOORING_ITEM or itemType == CatalogItemTypes.MOULDING_ITEM or itemType == CatalogItemTypes.WAINSCOTING_ITEM:
            self.atticWallpaperPanels.append(panel)
        elif itemType == CatalogItemTypes.WINDOW_ITEM:
            self.atticWindowPanels.append(panel)
        else:
            self.atticItemPanels.append(panel)
        self.regenerateAtticPicker()

    def showHouseFullDialog(self):
        self.cleanupDialog()
        self.dialog = TTDialog.TTDialog(style=TTDialog.Acknowledge, text=TTLocalizer.HDHouseFull, text_wordwrap=15, command=self.cleanupDialog)
        self.dialog.show()

    def bindHelpText(self, button, category):
        button.bind(DGG.ENTER, self.showHelpText, extraArgs=[category, None])
        button.bind(DGG.EXIT, self.hideHelpText)
        return

    def showHelpText(self, category, itemName, xy):

        def showIt(task):
            helpText = TTLocalizer.HDHelpDict.get(category)
            if helpText:
                if itemName:
                    helpText = helpText % itemName
                self.helpText['text'] = helpText
                self.helpText.show()
            else:
                print('category: %s not found')

        taskMgr.doMethodLater(0.75, showIt, 'showHelpTextDoLater')

    def hideHelpText(self, xy):
        taskMgr.remove('showHelpTextDoLater')
        self.helpText['text'] = ''
        self.helpText.hide()
