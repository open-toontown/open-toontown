from direct.showbase.DirectObject import DirectObject
from toontown.toonbase.ToontownGlobals import *
from direct.directnotify import DirectNotifyGlobal
from direct.interval.IntervalGlobal import *
from toontown.minigame import ToonBlitzGlobals
GOING_UP = 1
GOING_DOWN = 2
STUCK_DOWN = 3

class TwoDStomper(DirectObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('TwoDStomper')

    def __init__(self, stomperMgr, index, stomperAttribs, model):
        self.game = stomperMgr.section.sectionMgr.game
        self.index = index
        stomperName = 'stomper-' + str(self.index)
        self.model = NodePath(stomperName)
        self.nodePath = model.copyTo(self.model)
        self.ival = None
        self.stashCollisionsIval = None
        self.removeHeadFloor = 0
        self.stomperState = STUCK_DOWN
        self.setupStomper(stomperAttribs)
        return

    def destroy(self):
        self.game = None
        self.ignoreAll()
        if self.ival:
            self.ival.pause()
            del self.ival
            self.ival = None
        if self.smoke:
            self.smoke.removeNode()
            del self.smoke
            self.smoke = None
        if self.stashCollisionsIval:
            self.stashCollisionsIval.finish()
            del self.stashCollisionsIval
            self.stashCollisionsIval = None
        for collSolid in self.collSolids:
            collSolid.stash()

        self.nodePath.removeNode()
        del self.nodePath
        self.model.removeNode()
        if self.model:
            self.model.removeNode()
            del self.model
            self.model = None
        return

    def setupStomper(self, stomperAttribs):
        stomperType = stomperAttribs[0]
        self.pos = Point3(stomperAttribs[1][0], stomperAttribs[1][1], stomperAttribs[1][2])
        self.period = stomperAttribs[2]
        typeAttribs = ToonBlitzGlobals.StomperTypes[stomperType]
        self.motionType = typeAttribs[0]
        self.scale = typeAttribs[1]
        self.headStartZ, self.headEndZ = typeAttribs[2]
        self.shaftStartScaleZ, self.shaftEndScaleZ = typeAttribs[3]
        self.numCollSolids = typeAttribs[4]
        self.stompSound = loader.loadSfx('phase_4/audio/sfx/CHQ_FACT_stomper_small.mp3')
        self.model.setPos(self.pos)
        self.model.setScale(self.scale)
        self.model.find('**/block').setScale(1.0 / self.scale)
        self.head = self.model.find('**/head')
        self.shaft = self.model.find('**/shaft')
        self.collisions = self.model.find('**/stomper_collision')
        originalColl = self.model.find('**/stomper_collision')
        self.range = self.headEndZ - self.headStartZ
        self.collSolids = []
        self.collSolids.append(originalColl)
        for i in xrange(self.numCollSolids - 1):
            newColl = originalColl.copyTo(self.model)
            self.collSolids.append(newColl)

        self.collSolids[-1].reparentTo(self.head)
        self.smoke = loader.loadModel('phase_4/models/props/test_clouds')
        self.smoke.setZ(self.headEndZ - 1)
        self.smoke.setColor(0.8, 0.7, 0.5, 1)
        self.smoke.setBillboardPointEye()
        self.smoke.setScale(1.0 / self.scale)
        self.smoke.setDepthWrite(False)

    def getMotionIval(self):

        def motionFunc(t, self = self):
            stickTime = 0.2
            turnaround = 0.95
            t = t % 1
            if t < stickTime:
                self.head.setFluidZ(0 + self.headEndZ)
                if self.stomperState != STUCK_DOWN:
                    self.stomperState = STUCK_DOWN
            elif t < turnaround:
                self.head.setFluidZ((t - stickTime) * -self.range / (turnaround - stickTime) + self.headEndZ)
                if self.stomperState != GOING_UP:
                    self.stomperState = GOING_UP
            elif t > turnaround:
                self.head.setFluidZ(-self.range + (t - turnaround) * self.range / (1 - turnaround) + self.headEndZ)
                if self.stomperState != GOING_DOWN:
                    self.stomperState = GOING_DOWN
                    self.checkSquashedToon()

        motionIval = Sequence(LerpFunctionInterval(motionFunc, duration=self.period))
        return motionIval

    def getSmokeTrack(self):
        smokeTrack = Sequence(Parallel(LerpScaleInterval(self.smoke, 0.2, Point3(1, 1, 1.5)), LerpColorScaleInterval(self.smoke, 0.4, VBase4(1, 1, 1, 0), VBase4(1, 1, 1, 0.5))), Func(self.smoke.reparentTo, hidden), Func(self.smoke.clearColorScale))
        return smokeTrack

    def adjustShaftScale(self, t):
        heightDiff = self.head.getZ() - self.headStartZ
        self.shaft.setScale(1, 1, self.shaftStartScaleZ + heightDiff * (self.shaftEndScaleZ - self.shaftStartScaleZ) / self.range)

    def adjustCollSolidHeight(self, t):
        heightDiff = self.head.getZ() - self.headStartZ
        for i in range(1, len(self.collSolids) - 1):
            self.collSolids[i].setZ(heightDiff * i / (self.numCollSolids - 1))

    def start(self, elapsedTime):
        if self.ival:
            self.ival.pause()
            del self.ival
            self.ival = None
        self.ival = Parallel()
        self.ival.append(Sequence(self.getMotionIval(), Func(base.playSfx, self.stompSound, node=self.model, volume=0.3), Func(self.smoke.reparentTo, self.model), self.getSmokeTrack()))
        self.ival.append(LerpFunctionInterval(self.adjustShaftScale, duration=self.period))
        self.ival.append(LerpFunctionInterval(self.adjustCollSolidHeight, duration=self.period))
        self.ival.loop()
        self.ival.setT(elapsedTime)
        return

    def enterPause(self):
        if self.ival:
            self.ival.pause()

    def exitPause(self):
        if self.ival:
            self.ival.loop()

    def checkSquashedToon(self):
        toonXDiff = (base.localAvatar.getX(render) - self.model.getX(render)) / self.scale
        toonZ = base.localAvatar.getZ(render)
        headEndZAbs = self.model.getZ(render) + self.headEndZ * self.scale
        if toonXDiff > -1.0 and toonXDiff < 1.0 and toonZ > headEndZAbs and toonZ < self.head.getZ(render):
            if not base.localAvatar.isStunned:

                def stashCollisions(self = self):
                    for collSolid in self.collSolids:
                        collSolid.stash()

                def unstashCollisions(self = self):
                    for collSolid in self.collSolids:
                        collSolid.unstash()

                self.stashCollisionsIval = Sequence(Func(stashCollisions), Wait(2.5), Func(unstashCollisions))
                self.stashCollisionsIval.start()
                self.game.localToonSquished()
