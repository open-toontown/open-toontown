from pandac.PandaModules import Vec3, Vec4, Point3, TextNode, VBase4, NodePath
from direct.gui.DirectGui import DirectFrame, DirectButton, DirectLabel, DirectScrolledList, DirectCheckButton
from direct.gui import DirectGuiGlobals
from direct.showbase import DirectObject
from direct.showbase import PythonUtil
from direct.task.Task import Task
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from toontown.parties import PartyGlobals
from toontown.parties.PartyInfo import PartyInfo
from toontown.parties import PartyUtils

class PartyEditorGridElement(DirectButton):
    notify = directNotify.newCategory('PartyEditorGridElement')

    def __init__(self, partyEditor, id, isDecoration, checkSoldOutAndPaidStatusAndAffordability, **kw):
        self.partyEditor = partyEditor
        self.id = id
        self.isDecoration = isDecoration
        self.checkSoldOutAndPaidStatusAndAffordability = checkSoldOutAndPaidStatusAndAffordability
        if self.isDecoration:
            self.name = TTLocalizer.PartyDecorationNameDict[self.id]['editor']
            colorList = ((1.0, 1.0, 1.0, 1.0),
             (0.0, 0.0, 1.0, 1.0),
             (0.0, 1.0, 1.0, 1.0),
             (0.5, 0.5, 0.5, 1.0))
            self.geom = self.partyEditor.partyPlanner.gui.find('**/%s' % PartyGlobals.DecorationInformationDict[self.id]['gridAsset'])
        else:
            self.name = TTLocalizer.PartyActivityNameDict[self.id]['editor']
            colorList = ((1.0, 1.0, 1.0, 1.0),
             (0.0, 1.0, 0.0, 1.0),
             (1.0, 1.0, 0.0, 1.0),
             (0.5, 0.5, 0.5, 1.0))
            self.geom = self.partyEditor.partyPlanner.gui.find('**/%s' % PartyGlobals.ActivityInformationDict[self.id]['gridAsset'])
        optiondefs = (('geom', self.geom, None),
         ('geom_scale', 1.0, None),
         ('geom_color', colorList[0], None),
         ('geom1_color', colorList[0], None),
         ('geom2_color', colorList[0], None),
         ('geom3_color', colorList[0], None),
         ('relief', None, None))
        self.defineoptions(kw, optiondefs)
        DirectButton.__init__(self, self.partyEditor.parent)
        self.initialiseoptions(PartyEditorGridElement)
        self.setName('%sGridElement' % self.name)
        self.bind(DirectGuiGlobals.B1PRESS, self.clicked)
        self.bind(DirectGuiGlobals.B1RELEASE, self.released)
        self.bind(DirectGuiGlobals.ENTER, self.mouseEnter)
        self.bind(DirectGuiGlobals.EXIT, self.mouseExit)
        self.uprightNodePath = NodePath('%sUpright' % self.name)
        self.uprightNodePath.reparentTo(self)
        rollOverZOffset = self.getGridSize()[1] / 30.0
        self.rolloverTitle = DirectLabel(relief=None, parent=self.uprightNodePath, pos=Point3(0.0, 0.0, rollOverZOffset), text=self.name, text_fg=(1.0, 1.0, 1.0, 1.0), text_shadow=(0.0, 0.0, 0.0, 1.0), text_scale=0.075)
        self.rolloverTitle.stash()
        self.stash()
        self.overValidSquare = False
        self.lastValidPosition = None
        self.setColorScale(0.9, 0.9, 0.9, 0.7)
        self.setTransparency(True)
        self.mouseOverTrash = False
        self.centerGridSquare = None
        return

    def getCorrectRotation(self):
        r = self.getR()
        if r == 90.0:
            r = 270.0
        elif r == 270.0:
            r = 90.0
        if self.id == PartyGlobals.ActivityIds.PartyCannon:
            return PartyUtils.convertDegreesToPartyGrid(r + 180.0)
        return PartyUtils.convertDegreesToPartyGrid(r)

    def getDecorationTuple(self, x, y):
        return (self.id,
         self.centerGridSquare.x,
         PartyGlobals.PartyEditorGridSize[1] - 1 - self.centerGridSquare.y,
         self.getCorrectRotation())

    def getActivityTuple(self, x, y):
        return (self.id,
         self.centerGridSquare.x,
         PartyGlobals.PartyEditorGridSize[1] - 1 - self.centerGridSquare.y,
         self.getCorrectRotation())

    def attach(self, mouseEvent):
        PartyEditorGridElement.notify.debug('attached grid element %s' % self.name)
        taskMgr.remove('gridElementDragTask%s' % self.name)
        vWidget2render2d = self.getPos(render2d)
        vMouse2render2d = Point3(mouseEvent.getMouse()[0], 0, mouseEvent.getMouse()[1])
        taskMgr.add(self.elementDragTask, 'gridElementDragTask%s' % self.name)
        self.unstash()
        self.rolloverTitle.unstash()
        self.uprightNodePath.reparentTo(self)
        self.setPosHprToDefault()

    def elementDragTask(self, state):
        mwn = base.mouseWatcherNode
        if mwn.hasMouse():
            vMouse2render2d = Point3(mwn.getMouse()[0], 0, mwn.getMouse()[1])
            newPos = vMouse2render2d
            if newPos[0] > PartyGlobals.PartyEditorGridBounds[0][0] and newPos[0] < PartyGlobals.PartyEditorGridBounds[1][0] and newPos[2] < PartyGlobals.PartyEditorGridBounds[0][1] and newPos[2] > PartyGlobals.PartyEditorGridBounds[1][1]:
                centerGridSquare = self.snapToGrid(newPos)
                if centerGridSquare is not None:
                    self.centerGridSquare = centerGridSquare
                    if not self.overValidSquare:
                        self.setOverValidSquare(True)
                    if self.mouseOverTrash:
                        self.setOverTrash(False)
                    return Task.cont
            if self.id != PartyGlobals.ActivityIds.PartyClock and newPos[0] > PartyGlobals.PartyEditorTrashBounds[0][0] and newPos[0] < PartyGlobals.PartyEditorTrashBounds[1][0] and newPos[2] < PartyGlobals.PartyEditorTrashBounds[0][1] and newPos[2] > PartyGlobals.PartyEditorTrashBounds[1][1]:
                if not self.mouseOverTrash:
                    self.setOverTrash(True)
            elif self.mouseOverTrash:
                self.setOverTrash(False)
            self.setPos(render2d, newPos)
            if self.overValidSquare:
                self.setOverValidSquare(False)
        return Task.cont

    def setOverTrash(self, value):
        self.mouseOverTrash = value
        if value:
            self.partyEditor.trashCanButton['state'] = DirectGuiGlobals.DISABLED
            self.setColorScale(1.0, 0.0, 0.0, 1.0)
        else:
            self.partyEditor.trashCanButton['state'] = DirectGuiGlobals.NORMAL
            self.setColorScale(0.9, 0.9, 0.9, 0.7)

    def setOverValidSquare(self, value):
        self.overValidSquare = value
        if value:
            self.setColorScale(1.0, 1.0, 1.0, 1.0)
        else:
            self.setColorScale(0.9, 0.9, 0.9, 0.7)

    def removeFromGrid(self):
        if self.centerGridSquare is not None:
            self.partyEditor.partyEditorGrid.removeElement(self.centerGridSquare, self.getGridSize())
        self.setOverValidSquare(False)
        self.lastValidPosition = None
        self.stash()
        return

    def snapToGrid(self, newPos):
        gridSquare = self.getGridSquareFromPosition(newPos)
        if gridSquare == None:
            self.setPosHprToDefault()
            self.setPos(render2d, newPos)
            return
        elif not self.partyEditor.partyEditorGrid.checkGridSquareForAvailability(gridSquare, self.getGridSize()):
            self.setPos(render2d, newPos)
            return
        self.setPosHprBasedOnGridSquare(gridSquare)
        return gridSquare

    def getGridSize(self):
        if self.isDecoration:
            return PartyGlobals.DecorationInformationDict[self.id]['gridsize']
        else:
            return PartyGlobals.ActivityInformationDict[self.id]['gridsize']

    def setPosHprToDefault(self):
        self.setR(0.0)
        self.uprightNodePath.setR(0.0)

    def setPosHprBasedOnGridSquare(self, gridSquare):
        gridPos = gridSquare.getPos()
        if self.getGridSize()[0] % 2 == 0:
            gridPos.setX(gridPos[0] + PartyGlobals.PartyEditorGridSquareSize[0] / 2.0)
        if self.getGridSize()[1] % 2 == 0:
            gridPos.setZ(gridPos[2] + PartyGlobals.PartyEditorGridSquareSize[1] / 2.0)
        if self.id != PartyGlobals.ActivityIds.PartyFireworks:
            if gridPos[0] > PartyGlobals.PartyEditorGridCenter[0] + PartyGlobals.PartyEditorGridRotateThreshold:
                self.setR(90.0)
                self.uprightNodePath.setR(-90.0)
            elif gridPos[0] < PartyGlobals.PartyEditorGridCenter[0] - PartyGlobals.PartyEditorGridRotateThreshold:
                self.setR(270.0)
                self.uprightNodePath.setR(-270.0)
            elif gridPos[2] < PartyGlobals.PartyEditorGridCenter[1] - PartyGlobals.PartyEditorGridRotateThreshold:
                self.setR(180.0)
                self.uprightNodePath.setR(-180.0)
            else:
                self.setR(0.0)
                self.uprightNodePath.setR(0.0)
        else:
            self.setR(270.0)
            self.uprightNodePath.setR(-270.0)
        self.setPos(render2d, gridPos)
        self.lastValidPosition = gridPos

    def getGridSquareFromPosition(self, newPos):
        localX = newPos[0] - PartyGlobals.PartyEditorGridBounds[0][0]
        localY = newPos[2] - PartyGlobals.PartyEditorGridBounds[1][1]
        x = int(localX / PartyGlobals.PartyEditorGridSquareSize[0])
        y = int(localY / PartyGlobals.PartyEditorGridSquareSize[1])
        y = PartyGlobals.PartyEditorGridSize[1] - 1 - y
        return self.partyEditor.partyEditorGrid.getGridSquare(x, y)

    def detach(self, mouseEvent):
        taskMgr.remove('gridElementDragTask%s' % self.name)
        self.rolloverTitle.stash()
        if self.overValidSquare:
            self.partyEditor.partyEditorGrid.registerNewElement(self, self.centerGridSquare, self.getGridSize())
            self.partyEditor.updateCostsAndBank()
            self.partyEditor.handleMutuallyExclusiveActivities()
        elif self.lastValidPosition is not None:
            if self.mouseOverTrash:
                self.partyEditor.trashCanButton['state'] = DirectGuiGlobals.NORMAL
                self.lastValidPosition = None
                self.partyEditor.updateCostsAndBank()
                self.stash()
            else:
                self.setPos(render2d, self.lastValidPosition)
                self.setOverValidSquare(True)
                self.partyEditor.partyEditorGrid.registerNewElement(self, self.centerGridSquare, self.getGridSize())
                self.partyEditor.updateCostsAndBank()
                self.partyEditor.handleMutuallyExclusiveActivities()
        else:
            self.stash()
        self.checkSoldOutAndPaidStatusAndAffordability()
        return

    def placeInPartyGrounds(self, desiredXY = None):
        self.centerGridSquare = self.partyEditor.partyEditorGrid.getClearGridSquare(self.getGridSize(), desiredXY)
        if self.centerGridSquare is not None:
            self.setOverValidSquare(True)
            self.unstash()
            self.setPosHprBasedOnGridSquare(self.centerGridSquare)
            self.partyEditor.partyEditorGrid.registerNewElement(self, self.centerGridSquare, self.getGridSize())
            self.partyEditor.updateCostsAndBank()
            self.partyEditor.partyPlanner.instructionLabel['text'] = TTLocalizer.PartyPlannerEditorInstructionsPartyGrounds
            self.checkSoldOutAndPaidStatusAndAffordability()
            return True
        else:
            return False
        return

    def clicked(self, mouseEvent):
        PartyEditorGridElement.notify.debug('clicked grid element %s' % self.name)
        if self.centerGridSquare is not None:
            self.attach(mouseEvent)
            self.partyEditor.partyEditorGrid.removeElement(self.centerGridSquare, self.getGridSize())
        return

    def released(self, mouseEvent):
        PartyEditorGridElement.notify.debug('released grid element %s' % self.name)
        self.detach(mouseEvent)

    def mouseEnter(self, mouseEvent):
        parent = self.getParent()
        self.reparentTo(parent)
        self.rolloverTitle.unstash()

    def mouseExit(self, mouseEvent):
        self.rolloverTitle.stash()

    def destroy(self):
        self.unbind(DirectGuiGlobals.B1PRESS)
        self.unbind(DirectGuiGlobals.B1RELEASE)
        self.unbind(DirectGuiGlobals.ENTER)
        self.unbind(DirectGuiGlobals.EXIT)
        DirectButton.destroy(self)
