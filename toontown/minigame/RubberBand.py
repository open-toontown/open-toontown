from pandac.PandaModules import *
from toontown.toonbase.ToonBaseGlobal import *
from direct.interval.IntervalGlobal import *
from direct.distributed.ClockDelta import *
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from direct.task import Task
from toontown.toonbase import ToontownGlobals
import math
from math import *
import random

class RubberBand:
    SomeCounter = 0

    def __init__(self, heldObject = None, heldOffset = None, taskPriority = 0):
        self.heldObject = heldObject
        self.heldOffset = heldOffset
        self.bandNumber = self.SomeCounter
        self._taskPriority = taskPriority
        self.SomeCounter += 1
        if not heldOffset:
            self.heldOffset = [0, 0, 0]
        self.setup()

    def setup(self):
        self.baseNode = render.attachNewNode('targetGameTargets')
        target = CollisionSphere(0, 0, 0, 5.0)
        target.setTangible(0)
        targetNode = CollisionNode('thing')
        targetNode.addSolid(target)
        targetNodePath = self.baseNode.attachNewNode(targetNode)
        self.slingModel = loader.loadModel('phase_4/models/minigames/slingshot_game_sling.bam')
        self.slingModel.reparentTo(self.baseNode)
        self.slingModel.setScale(1.0)
        self.slingModel.setZ(-1.0)
        self.bandGN = GeomNode('Band Geometry')
        self.bandNodePathGeom = self.baseNode.attachNewNode(self.bandGN)
        self.bandNodePathGeom.setTwoSided(True)
        height = 13
        width = 5.5
        self.bandHeight = 1.0
        self.post1Pos = Point3(-width, 0, height)
        self.post2Pos = Point3(width, 0, height)
        taskMgr.add(self.redraw, 'recreateBand %s' % self.bandNumber, priority=self._taskPriority)
        self.colorRelax = {}
        self.colorRelax['Red'] = 1.0
        self.colorRelax['Green'] = 0.3
        self.colorRelax['Blue'] = 0.2
        self.colorRelax['Alpha'] = 1.0
        self.colorStrecth = {}
        self.colorStrecth['Red'] = 1.0
        self.colorStrecth['Green'] = 0.6
        self.colorStrecth['Blue'] = 0.4
        self.colorStrecth['Alpha'] = 1.0

    def setPos(self, pos):
        self.baseNode.setPos(pos[0], pos[1], pos[2])

    def delete(self):
        taskMgr.remove('recreateBand %s' % self.bandNumber)
        self.bandGN.removeAllGeoms()
        self.baseNode.removeNode()

    def redraw(self, task):
        color = {}
        color['Red'] = 1.0
        color['Green'] = 0.3
        color['Blue'] = 0.2
        color['Alpha'] = 0.5
        self.bandGN.removeAllGeoms()
        objPosX = self.heldObject.getX(self.baseNode) + self.heldOffset[0]
        objPosY = self.heldObject.getY(self.baseNode) + self.heldOffset[1]
        objPosZ = self.heldObject.getZ(self.baseNode) + self.heldOffset[2] + 1.5
        if objPosY > 0:
            objPosY = 0
            objPosX = 0
            objPosZ = self.post1Pos[2]
        objPosYSecondary = objPosY + 0.25
        if objPosYSecondary > 0:
            objPosYSecondary = 0
        midPosY = objPosY + math.sqrt(abs(objPosY))
        midPosX = objPosX + 2
        maxStretch = 25.0
        bandThickness = self.bandHeight + objPosY * (1 / maxStretch)
        if bandThickness < 0.2:
            bandThickness = 0.2
        colorProp = bandThickness / self.bandHeight
        color = {}
        color['Red'] = colorProp * self.colorRelax['Red'] + (1 - colorProp) * self.colorStrecth['Red']
        color['Green'] = colorProp * self.colorRelax['Green'] + (1 - colorProp) * self.colorStrecth['Green']
        color['Blue'] = colorProp * self.colorRelax['Blue'] + (1 - colorProp) * self.colorStrecth['Blue']
        color['Alpha'] = colorProp * self.colorRelax['Alpha'] + (1 - colorProp) * self.colorStrecth['Alpha']
        bandBottomOrigin = self.post1Pos[2] - 0.5 * bandThickness
        bandTopOrigin = self.post1Pos[2] + 0.5 * bandThickness
        bandBottomHeld = objPosZ - 0.5 * bandThickness
        bandTopHeld = objPosZ + 0.5 * bandThickness
        midSegs = 12
        colorMultList = []
        colorHigh = 1.0
        colorLow = 0.5
        shapeVertexs = []
        shapeVertexs.append((self.post1Pos[0], self.post1Pos[1], bandBottomOrigin + 0.45))
        shapeVertexs.append((self.post1Pos[0], self.post1Pos[1], bandTopOrigin + 0.45))
        colorMultList.append(colorLow)
        colorMultList.append(colorHigh)
        s2 = pow(2, 0.5)
        s2dif = s2 - 1
        objPosXSecondary = objPosX - 0.5
        shapeVertexs.append((objPosXSecondary, objPosYSecondary, bandBottomHeld))
        shapeVertexs.append((objPosXSecondary, objPosYSecondary, bandTopHeld))
        colorMultList.append(colorLow)
        colorMultList.append(colorHigh)
        shapeVertexs.append((objPosX, objPosY, bandBottomHeld))
        shapeVertexs.append((objPosX, objPosY, bandTopHeld))
        colorMultList.append(colorLow)
        colorMultList.append(colorHigh)
        objPosXSecondary = objPosX + 0.5
        shapeVertexs.append((objPosXSecondary, objPosYSecondary, bandBottomHeld))
        shapeVertexs.append((objPosXSecondary, objPosYSecondary, bandTopHeld))
        colorMultList.append(colorLow)
        colorMultList.append(colorHigh)
        shapeVertexs.append((self.post2Pos[0], self.post2Pos[1], bandBottomOrigin + 0.45))
        shapeVertexs.append((self.post2Pos[0], self.post2Pos[1], bandTopOrigin + 0.45))
        colorMultList.append(colorLow)
        colorMultList.append(colorHigh)
        gFormat = GeomVertexFormat.getV3cp()
        bandVertexData = GeomVertexData('holds my vertices', gFormat, Geom.UHDynamic)
        bandVertexWriter = GeomVertexWriter(bandVertexData, 'vertex')
        bandColorWriter = GeomVertexWriter(bandVertexData, 'color')
        for index in range(len(shapeVertexs)):
            bandVertexWriter.addData3f(shapeVertexs[index][0], shapeVertexs[index][1], shapeVertexs[index][2])
            bandColorWriter.addData4f(color['Red'] * colorMultList[index], color['Green'] * colorMultList[index], color['Blue'] * colorMultList[index], color['Alpha'] * colorMultList[index])

        bandTris = GeomTristrips(Geom.UHStatic)
        for index in range(len(shapeVertexs)):
            bandTris.addVertex(index)

        bandTris.closePrimitive()
        bandGeom = Geom(bandVertexData)
        bandGeom.addPrimitive(bandTris)
        self.bandGN.addGeom(bandGeom)
        return task.cont
