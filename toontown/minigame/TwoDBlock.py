from panda3d.core import *
from direct.distributed.ClockDelta import *
from direct.interval.IntervalGlobal import *
from direct.fsm import ClassicFSM, State
from otp.level import BasicEntities
from toontown.coghq import MovingPlatform
from direct.distributed import DistributedObject
from direct.directnotify import DirectNotifyGlobal
from toontown.minigame import ToonBlitzGlobals

class TwoDBlock(DistributedObject.DistributedObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('TwoDBlock')

    def __init__(self, model, index, blockAttribs):
        self.moveIval = None
        self.isMovingBlock = False
        self.index = index
        self.createNewBlock(model, blockAttribs)
        return

    def destroy(self):
        if self.moveIval:
            self.moveIval.pause()
            del self.moveIval
        if self.platform:
            if self.isMovingBlock:
                self.platform.destroy()
            del self.platform

    def createNewBlock(self, model, blockAttribs):
        initX, initY, initZ, initH, initP, initR = (0, 0, 0, 0, 0, 0)
        finalX, finalY, finalZ, finalH, finalP, finalR = (0, 0, 0, 0, 0, 0)
        blockType = blockAttribs[0]
        typeAttribs = ToonBlitzGlobals.BlockTypes[blockType]
        blockName = blockType + '-' + str(self.index)
        self.model = NodePath(blockName)
        typeX, typeY, typeZ = typeAttribs[1]
        typeH, typeP, typeR = typeAttribs[2]
        scaleX, scaleY, scaleZ = typeAttribs[3]
        model.setScale(scaleX, scaleY, scaleZ)
        blockPosAttribs = blockAttribs[1]
        initX, initY, initZ = blockPosAttribs[0]
        if len(blockPosAttribs) == 3:
            self.isMovingBlock = True
            finalX, finalY, finalZ = blockPosAttribs[1]
            posIvalDuration = blockPosAttribs[2]
        if len(blockAttribs) == 3:
            blockHprAttribs = blockAttribs[2]
            initH, initP, initR = blockHprAttribs[0]
            if len(blockHprAttribs) == 3:
                self.isMovingBlock = True
                finalH, finalP, finalR = blockHprAttribs[1]
                hprIvalDuration = blockHprAttribs[2]
        if self.isMovingBlock:
            self.platform = MovingPlatform.MovingPlatform()
            self.platform.setupCopyModel(blockName, model)
            self.platform.reparentTo(self.model)
            self.clearMoveIval()
            forwardIval = LerpPosInterval(self.model, posIvalDuration, pos=Point3(finalX, finalY, finalZ), startPos=Point3(initX, initY, initZ), name='%s-moveFront' % self.platform.name, fluid=1)
            backwardIval = LerpPosInterval(self.model, posIvalDuration, pos=Point3(initX, initY, initZ), startPos=Point3(finalX, finalY, finalZ), name='%s-moveBack' % self.platform.name, fluid=1)
            self.moveIval = Sequence(forwardIval, backwardIval)
        else:
            self.platform = model.copyTo(self.model)
        self.model.flattenLight()
        self.model.setPos(typeX + initX, typeY + initY, typeZ + initZ)
        self.model.setHpr(typeH + initH, typeP + initP, typeR + initR)

    def clearMoveIval(self):
        if self.moveIval:
            self.moveIval.pause()
            del self.moveIval
        self.moveIval = None
        return

    def start(self, elapsedTime):
        if self.moveIval:
            self.moveIval.loop()
            self.moveIval.setT(elapsedTime)

    def enterPause(self):
        if self.moveIval:
            self.moveIval.pause()

    def exitPause(self):
        if self.moveIval:
            self.moveIval.resume()
