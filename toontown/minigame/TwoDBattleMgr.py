from pandac.PandaModules import *
from direct.showbase.DirectObject import DirectObject
from toontown.toonbase.ToonBaseGlobal import *
from direct.directnotify import DirectNotifyGlobal
from direct.interval.IntervalGlobal import *
from toontown.battle.BattleProps import *
from toontown.battle import MovieUtil
import math

class TwoDBattleMgr(DirectObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('TwoDBattleMgr')

    def __init__(self, game, toon):
        self.game = game
        self.toon = toon
        self.waterBulletIval = None
        self.shootTrack = None
        self.showCollSpheres = False
        self.WATER_SPRAY_COLOR = Point4(1, 1, 1, 1)
        self.WATER_BULLET_SCALE = 0.2
        self.SHOOT_DISTANCE = 10
        self.WATER_BULLET_START_POINT = Point3(0, 1, 3)
        self.WATER_BULLET_END_POINT = Point3(0, self.WATER_BULLET_START_POINT.getY() + self.SHOOT_DISTANCE, self.WATER_BULLET_START_POINT.getZ())
        self.WATER_BULLET_HIDE_POINT = Point3(0, 0, 1.5)
        self.sprayProp = self.game.assetMgr.sprayProp.copyTo(self.game.assetMgr.world)
        self.setupPistol()
        if self.toon == base.localAvatar:
            self.createShootCollision()
        return

    def destroy(self):
        if self.toon == base.localAvatar:
            if self.waterBulletIval:
                self.waterBulletIval.finish()
                del self.waterBulletIval
                self.waterBulletIval = None
            self.ignore('enter' + self.collSphereName)
            base.localAvatar.controlManager.currentControls.cTrav.removeCollider(self.waterBullet)
            self.waterBullet.removeNode()
            del self.waterBullet
        self.hand_jointpath0.removeNode()
        MovieUtil.removeProp(self.pistol)
        if self.shootTrack != None:
            self.shootTrack.finish()
            self.shootTrack = None
        self.game = None
        self.toon = None
        return

    def start(self):
        pass

    def stop(self):
        pass

    def setupPistol(self):
        self.pistol = globalPropPool.getProp('water-gun')
        hands = self.toon.getRightHands()
        self.hand_jointpath0 = hands[0].attachNewNode('handJoint0-path')
        pistolPos = Point3(0.28, 0.1, 0.08)
        pistolHpr = VBase3(85.6, -4.44, 94.43)
        MovieUtil.showProp(self.pistol, self.hand_jointpath0, pistolPos, pistolHpr)

    def shoot(self):
        if not self.shootTrack:
            self.shootTrack = Parallel(self.getToonShootTrack(), self.getSprayTrack())
            if self.toon == base.localAvatar:
                self.shootTrack.append(Func(self.game.assetMgr.playWatergunSound))
                self.shootTrack.append(self.getWaterBulletIval())
            self.shootTrack.start()
            return
        elif self.shootTrack.isStopped():
            self.shootTrack = Parallel(self.getToonShootTrack(), self.getSprayTrack())
            if self.toon == base.localAvatar:
                self.shootTrack.append(Func(self.game.assetMgr.playWatergunSound))
                self.shootTrack.append(self.getWaterBulletIval())
            self.shootTrack.start()

    def createShootCollision(self):
        self.notify.debug('entering createShootCollision')
        collSphere = CollisionSphere(0, 0, 0, 1)
        collSphere.setTangible(0)
        self.collSphereName = self.game.uniqueName('waterBullet')
        collNode = CollisionNode(self.collSphereName)
        collNode.setFromCollideMask(ToontownGlobals.WallBitmask)
        collNode.addSolid(collSphere)
        self.waterBullet = base.localAvatar.attachNewNode(collNode)
        self.waterBullet.setPos(self.WATER_BULLET_HIDE_POINT)
        self.waterBullet.setScale(self.WATER_BULLET_SCALE)
        self.waterBullet.hide()
        if self.showCollSpheres:
            self.waterBullet.show()
        bulletEvent = CollisionHandlerEvent()
        bulletEvent.addInPattern('enter%fn')
        bulletEvent.addOutPattern('exit%fn')
        cTrav = base.localAvatar.controlManager.currentControls.cTrav
        cTrav.addCollider(self.waterBullet, bulletEvent)
        self.accept('enter' + self.collSphereName, self.handleBulletCollision)
        self.waterBulletIval = Sequence(Wait(0.15))
        self.waterBulletIval.append(LerpPosInterval(self.waterBullet, 0.25, pos=Point3(self.WATER_BULLET_END_POINT), startPos=Point3(self.WATER_BULLET_START_POINT), name='waterBulletMoveFront'))
        self.waterBulletIval.append(Func(self.waterBullet.setPos, self.WATER_BULLET_HIDE_POINT))

    def getToonShootTrack(self):

        def returnToLastAnim(toon):
            if hasattr(toon, 'playingAnim') and toon.playingAnim:
                toon.loop(toon.playingAnim)
            else:
                toon.loop('neutral')

        torso = self.toon.getPart('torso', '1000')
        toonTrack = Sequence(ActorInterval(self.toon, 'water-gun', startFrame=48, endFrame=58, partName='torso'), ActorInterval(self.toon, 'water-gun', startFrame=107, endFrame=126, playRate=2, partName='torso'), Func(returnToLastAnim, self.toon))
        return toonTrack

    def calcSprayStartPos(self):
        if self.toon:
            self.toon.update(0)
        joint = self.pistol.find('**/joint_nozzle')
        p = joint.getPos(render)
        self.origin = p

    def calcSprayEndPos(self):
        if self.toon:
            xDirection = -math.sin(self.toon.getH())
        else:
            xDirection = -math.sin(-90)
        endPos = Point3(self.origin.getX() + self.SHOOT_DISTANCE * xDirection, self.origin.getY(), self.origin.getZ())
        self.target = endPos

    def getSprayTrack(self):
        dSprayScale = 0.15
        dSprayHold = 0.035
        color = self.WATER_SPRAY_COLOR
        parent = render
        horizScale = 1.0
        vertScale = 1.0

        def showSpray(sprayScale, sprayRot, sprayProp, parent):
            sprayRot.reparentTo(parent)
            sprayRot.clearMat()
            sprayScale.reparentTo(sprayRot)
            sprayScale.clearMat()
            sprayProp.reparentTo(sprayScale)
            sprayProp.clearMat()
            sprayRot.setPos(self.origin)
            sprayRot.lookAt(Point3(self.target))

        def calcTargetScale(horizScale = horizScale, vertScale = vertScale):
            distance = Vec3(self.target - self.origin).length()
            yScale = distance / MovieUtil.SPRAY_LEN
            targetScale = Point3(yScale * horizScale, yScale, yScale * vertScale)
            return targetScale

        def prepareToShrinkSpray(spray, sprayProp):
            sprayProp.setPos(Point3(0.0, -MovieUtil.SPRAY_LEN, 0.0))
            spray.setPos(self.target)

        def hideSpray(spray, sprayScale, sprayRot, sprayProp, propPool):
            sprayProp.detachNode()
            sprayRot.removeNode()
            sprayScale.removeNode()

        sprayProp = self.sprayProp
        sprayScale = hidden.attachNewNode('spray-parent')
        sprayRot = hidden.attachNewNode('spray-rotate')
        spray = sprayRot
        spray.setColor(color)
        if color[3] < 1.0:
            spray.setTransparency(1)
        track = Sequence(Wait(0.1), Func(self.calcSprayStartPos), Func(self.calcSprayEndPos), Func(showSpray, sprayScale, sprayRot, sprayProp, parent), LerpScaleInterval(sprayScale, dSprayScale, calcTargetScale, startScale=MovieUtil.PNT3_NEARZERO), Wait(dSprayHold), Func(prepareToShrinkSpray, spray, sprayProp), LerpScaleInterval(sprayScale, dSprayScale, MovieUtil.PNT3_NEARZERO), Func(hideSpray, spray, sprayScale, sprayRot, sprayProp, globalPropPool))
        return track

    def handleBulletCollision(self, cevent):
        if cevent.getIntoNodePath().getName()[:5] == 'Enemy':
            sectionIndex = int(cevent.getIntoNodePath().getName()[6:8])
            enemyIndex = int(cevent.getIntoNodePath().getName()[9:11])
            messenger.send('enemyShot', [sectionIndex, enemyIndex])

    def clearWaterBulletIval(self):
        if self.waterBulletIval:
            self.waterBulletIval.finish()
            del self.waterBulletIval
        self.waterBulletIval = None
        return

    def getWaterBulletIval(self):
        if not self.waterBulletIval.isPlaying():
            return self.waterBulletIval
