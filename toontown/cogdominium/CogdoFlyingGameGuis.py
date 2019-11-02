from direct.interval.IntervalGlobal import LerpFunctionInterval
from direct.gui.DirectGui import DirectLabel, DirectFrame, DGG
from direct.showbase.PythonUtil import bound as clamp
from pandac.PandaModules import TextNode, NodePath
from toontown.toonbase import ToontownGlobals
import CogdoUtil
import CogdoFlyingGameGlobals as Globals

class CogdoFlyingProgressGui(DirectFrame):

    def __init__(self, parent, level, pos2d = Globals.Gui.ProgressPos2D):
        DirectFrame.__init__(self, relief=None, state=DGG.NORMAL, sortOrder=DGG.BACKGROUND_SORT_INDEX)
        self._parent = parent
        self._level = level
        self.reparentTo(self._parent)
        self.setPos(pos2d[0], 0.0, pos2d[1])
        self._levelStartY = self._level.startPlatform.getModel().getY()
        self._levelEndY = self._level.endPlatform.getModel().getY()
        self._levelDistance = abs(self._levelEndY - self._levelStartY)
        self._toonMarkers = {}
        self._initModel()
        return

    def destroy(self):
        self._laffMeterModel.removeNode()
        del self._laffMeterModel
        DirectFrame.destroy(self)

    def _initModel(self):
        self._laffMeterModel = loader.loadModel('phase_3/models/gui/laff_o_meter')
        self._model = CogdoUtil.loadFlyingModel('progressMeter', group='gui')
        self._model.reparentTo(self)
        self._model.setBin('fixed', 0)
        self._lineStart = self._model.find('**/start_loc').getZ()
        self._lineEnd = self._model.find('**/end_loc').getZ()
        self._lineDistance = abs(self._lineEnd - self._lineStart)

    def addToon(self, toon):
        marker = NodePath('toon_marker-%i' % toon.doId)
        marker.reparentTo(self)
        self._getToonMarker(toon).copyTo(marker)
        marker.setColor(toon.style.getHeadColor())
        if toon.isLocal():
            marker.setScale(Globals.Gui.LocalMarkerScale)
            marker.setBin('fixed', 10)
        else:
            marker.setScale(Globals.Gui.MarkerScale)
            marker.setBin('fixed', 5)
        marker.flattenStrong()
        self._toonMarkers[toon] = marker

    def removeToon(self, toon):
        marker = self._toonMarkers.get(toon, None)
        if marker is not None:
            marker.removeNode()
            del self._toonMarkers[toon]
        return

    def _getToonMarker(self, toon):
        return self._laffMeterModel.find('**/' + toon.style.getType() + 'head')

    def update(self):
        for toon, marker in self._toonMarkers.items():
            progress = clamp((toon.getY() - self._levelStartY) / self._levelDistance, self._levelStartY, self._levelEndY)
            marker.setZ(clamp(self._lineStart + self._lineDistance * progress, self._lineStart, self._lineEnd))


class CogdoFlyingFuelGui(DirectFrame):

    def __init__(self, parent):
        DirectFrame.__init__(self, relief=None, state=DGG.NORMAL, sortOrder=DGG.BACKGROUND_SORT_INDEX)
        self.reparentTo(parent)
        self.active = 0
        self._initModel()
        self._initIntervals()
        return

    def _initModel(self):
        self.setPos(Globals.Gui.FuelPos2D[0], 0.0, Globals.Gui.FuelPos2D[1])
        self.gui = CogdoUtil.loadFlyingModel('propellerMeter', group='gui')
        self.gui.reparentTo(self)
        self.gui.setBin('fixed', 0)
        self.healthBar = self.gui.find('**/healthBar')
        self.healthBar.setBin('fixed', 1)
        self.healthBar.setColor(*Globals.Gui.FuelNormalColor)
        bottomBarLocator = self.gui.find('**/bottomOfBar_loc')
        bottomBarPos = bottomBarLocator.getPos(render)
        topBarLocator = self.gui.find('**/topOfBar_loc')
        topBarPos = topBarLocator.getPos(render)
        zDist = topBarPos.getZ() - bottomBarPos.getZ()
        self.fuelLowIndicator = self.gui.find('**/fuelLowIndicator')
        self.fuelLowIndicator.setBin('fixed', 2)
        pos = self.fuelLowIndicator.getPos(render)
        newPos = pos
        newPos.setZ(bottomBarPos.getZ() + zDist * Globals.Gameplay.FuelLowAmt)
        self.fuelLowIndicator.setPos(render, newPos)
        self.fuelVeryLowIndicator = self.gui.find('**/fuelVeryLowIndicator')
        self.fuelVeryLowIndicator.setBin('fixed', 2)
        pos = self.fuelVeryLowIndicator.getPos(render)
        newPos = pos
        newPos.setZ(bottomBarPos.getZ() + zDist * Globals.Gameplay.FuelVeryLowAmt)
        self.fuelVeryLowIndicator.setPos(render, newPos)
        self.propellerMain = self.gui.find('**/propellers')
        self.propellerMain.setBin('fixed', 3)
        self.propellerHead = self.gui.find('**/propellerHead')
        self.propellerHead.setBin('fixed', 4)
        self.blades = []
        self.activeBlades = []
        index = 1
        blade = self.propellerMain.find('**/propeller%d' % index)
        while not blade.isEmpty():
            self.blades.append(blade)
            index += 1
            blade = self.propellerMain.find('**/propeller%d' % index)

        for blade in self.blades:
            self.activeBlades.append(blade)

        self.bladeNumberLabel = DirectLabel(parent=self.propellerHead, relief=None, pos=(Globals.Gui.FuelNumBladesPos2D[0], 0, Globals.Gui.FuelNumBladesPos2D[1]), scale=Globals.Gui.FuelNumBladesScale, text=str(len(self.activeBlades)), text_align=TextNode.ACenter, text_fg=(0.0,
         0.0,
         -0.002,
         1), text_shadow=(0.75, 0.75, 0.75, 1), text_font=ToontownGlobals.getInterfaceFont())
        self.bladeNumberLabel.setBin('fixed', 5)
        return

    def _initIntervals(self):
        self._healthIval = LerpFunctionInterval(self.healthBar.setSz, fromData=0.0, toData=1.0, duration=2.0)
        self.baseSpinDuration = 2.0
        self._spinIval = LerpFunctionInterval(self.propellerMain.setR, fromData=0.0, toData=-360.0, duration=self.baseSpinDuration)

    def show(self):
        DirectFrame.show(self)
        self._spinIval.loop()

    def hide(self):
        DirectFrame.hide(self)
        self._spinIval.pause()

    def resetBlades(self):
        self.setBlades(len(self.blades))

    def setBlades(self, fuelState):
        if fuelState not in Globals.Gameplay.FuelStates:
            return
        numBlades = fuelState - 1
        if len(self.activeBlades) != numBlades:
            for i in range(len(self.activeBlades)):
                blade = self.activeBlades.pop()
                blade.stash()

            if numBlades > len(self.blades):
                numBlades = len(self.blades)
            for i in range(numBlades):
                blade = self.blades[i]
                self.activeBlades.append(blade)
                blade.unstash()

            self.bladeNumberLabel['text'] = str(len(self.activeBlades))
            self.bladeNumberLabel.setText()
        self.updateHealthBarColor()

    def bladeLost(self):
        if len(self.activeBlades) > 0:
            blade = self.activeBlades.pop()
            blade.stash()
            self.bladeNumberLabel['text'] = str(len(self.activeBlades))
            self.bladeNumberLabel.setText()
        self.updateHealthBarColor()

    def updateHealthBarColor(self):
        color = Globals.Gui.NumBlades2FuelColor[len(self.activeBlades)]
        self.healthBar.setColor(*color)

    def setPropellerSpinRate(self, newRate):
        self._spinIval.setPlayRate(newRate)

    def setRefuelLerpFromData(self):
        startScale = self.healthBar.getSz()
        self._healthIval.fromData = startScale

    def setFuel(self, fuel):
        self.fuel = fuel

    def update(self):
        self.healthBar.setSz(self.fuel)

    def destroy(self):
        self.bladeNumberLabel.removeNode()
        self.bladeNumberLabel = None
        self._healthIval.clearToInitial()
        del self._healthIval
        self.healthBar = None
        self.fuelLowIndicator = None
        self.fuelVeryLowIndicator = None
        self.propellerMain = None
        self.propellerHead = None
        del self.blades[:]
        del self.activeBlades[:]
        self.gui.detachNode()
        self.gui = None
        DirectFrame.destroy(self)
        return
