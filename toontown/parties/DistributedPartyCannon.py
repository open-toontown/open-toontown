from pandac.PandaModules import *
from direct.distributed.DistributedObject import DistributedObject
from direct.task.Task import Task
from toontown.minigame import CannonGameGlobals
from toontown.minigame.CannonGameGlobals import *
from toontown.parties.Cannon import Cannon
from toontown.parties.CannonGui import CannonGui
from toontown.parties import PartyGlobals
from toontown.parties.DistributedPartyCannonActivity import DistributedPartyCannonActivity
LAND_TIME = 2
WORLD_SCALE = 2.0
GROUND_SCALE = 1.4 * WORLD_SCALE
CANNON_SCALE = 1.0
FAR_PLANE_DIST = 600 * WORLD_SCALE
GROUND_PLANE_MIN = -15
CANNON_Y = -int(CannonGameGlobals.TowerYRange / 2 * 1.3)
CANNON_X_SPACING = 12
CANNON_Z = 20
CANNON_ROTATION_MIN = -55
CANNON_ROTATION_MAX = 50
CANNON_ROTATION_VEL = 15.0
ROTATIONCANNON_ANGLE_MIN = 15
CANNON_ANGLE_MAX = 85
CANNON_ANGLE_VEL = 15.0
CANNON_MOVE_UPDATE_FREQ = 0.5
CAMERA_PULLBACK_MIN = 20
CAMERA_PULLBACK_MAX = 40
MAX_LOOKAT_OFFSET = 80
TOON_TOWER_THRESHOLD = 150
SHADOW_Z_OFFSET = 0.5
TOWER_HEIGHT = 43.85
TOWER_RADIUS = 10.5
BUCKET_HEIGHT = 36
TOWER_Y_RANGE = CannonGameGlobals.TowerYRange
TOWER_X_RANGE = int(TOWER_Y_RANGE / 2.0)
INITIAL_VELOCITY = 80.0
WHISTLE_SPEED = INITIAL_VELOCITY * 0.35

class DistributedPartyCannon(DistributedObject, Cannon):
    notify = directNotify.newCategory('DistributedPartyCannon')
    LOCAL_CANNON_MOVE_TASK = 'localCannonMoveTask'

    def __init__(self, cr):
        DistributedObject.__init__(self, cr)
        Cannon.__init__(self, parent=self.getParentNodePath())
        self.localCannonMoving = False
        self.active = False
        self.activityDoId = 0
        self.activity = None
        self.gui = None
        self.toonInsideAvId = 0
        self.sign = None
        self.controllingToonAvId = None
        return

    def generateInit(self):
        self.load()
        self.activate()

    def load(self):
        self.notify.debug('load')
        Cannon.load(self, self.uniqueName('Cannon'))
        if base.cr and base.cr.partyManager and base.cr.partyManager.getShowDoid():
            nameText = TextNode('nameText')
            nameText.setCardAsMargin(0.1, 0.1, 0.1, 0.1)
            nameText.setCardDecal(True)
            nameText.setCardColor(1.0, 1.0, 1.0, 0.0)
            r = 232.0 / 255.0
            g = 169.0 / 255.0
            b = 23.0 / 255.0
            nameText.setTextColor(r, g, b, 1)
            nameText.setAlign(nameText.ACenter)
            nameText.setShadowColor(0, 0, 0, 1)
            nameText.setText(str(self.doId))
            namePlate = self.parentNode.attachNewNode(nameText)
            namePlate.setDepthWrite(0)
            namePlate.setPos(0, 0, 8)
            namePlate.setScale(3)

    def announceGenerate(self):
        self.sign = self.activity.sign.instanceUnderNode(self.activity.getParentNodePath(), self.uniqueName('sign'))
        self.sign.reparentTo(self.activity.getParentNodePath())
        self.sign.setPos(self.parentNode, self.sign.getPos())

    def unload(self):
        self.notify.debug('unload')
        if self.gui is not None:
            self.gui.unload()
            del self.gui
        Cannon.unload(self)
        if self.sign is not None:
            self.sign.removeNode()
            self.sign = None
        self.ignoreAll()
        return

    def getParentNodePath(self):
        if hasattr(base.cr.playGame, 'hood') and base.cr.playGame.hood and hasattr(base.cr.playGame.hood, 'loader') and base.cr.playGame.hood.loader and hasattr(base.cr.playGame.hood.loader, 'geom') and base.cr.playGame.hood.loader.geom:
            return base.cr.playGame.hood.loader.geom
        else:
            self.notify.warning('Hood or loader not created, defaulting to render')
            return render

    def disable(self):
        self.notify.debug('disable')
        self.ignoreAll()
        self.__disableCannonControl()
        self.setMovie(PartyGlobals.CANNON_MOVIE_CLEAR, 0)

    def delete(self):
        self.deactivate()
        self.unload()
        DistributedObject.delete(self)

    def destroy(self):
        self.notify.debug('destroy')
        DistributedObject.destroy(self)

    def setPosHpr(self, x, y, z, h, p, r):
        self.parentNode.setPosHpr(x, y, z, h, p, r)

    def setActivityDoId(self, doId):
        self.activityDoId = doId
        self.activity = base.cr.doId2do[doId]

    def activate(self):
        self.accept(self.getEnterCollisionName(), self.__handleToonCollisionWithCannon)
        Cannon.show(self)
        self.active = True

    def deactivate(self):
        self.ignore(self.getEnterCollisionName())
        Cannon.hide(self)
        self.active = False

    def setMovie(self, mode, avId):
        self.notify.debug('%s setMovie(%s, %s)' % (self.doId, avId, mode))
        if mode == PartyGlobals.CANNON_MOVIE_CLEAR:
            self.setClear()
        elif mode == PartyGlobals.CANNON_MOVIE_FORCE_EXIT:
            self.exitCannon(avId)
            self.setClear()
        elif mode == PartyGlobals.CANNON_MOVIE_LOAD:
            self.enterCannon(avId)
        elif mode == PartyGlobals.CANNON_MOVIE_LANDED:
            self.setLanded(avId)
        else:
            self.notify.error('setMovie Unhandled case mode=%d avId=%d' % (mode, avId))

    def __handleToonCollisionWithCannon(self, collEntry):
        self.notify.debug('collEntry: %s' % collEntry)
        if base.cr.playGame.getPlace().getState() == 'walk' and self.toonInsideAvId == 0:
            base.cr.playGame.getPlace().setState('activity')
            self.d_requestEnter()

    def d_requestEnter(self):
        self.sendUpdate('requestEnter', [])

    def requestExit(self):
        self.notify.debug('requestExit')
        base.localAvatar.reparentTo(render)
        base.cr.playGame.getPlace().setState('walk')

    def __avatarGone(self, avId):
        if self.toonInsideAvId == avId:
            self.notify.debug('__avatarGone in if')
            if self.toonInside and not self.toonInside.isEmpty():
                self.removeToonDidNotFire()
            self.setMovie(PartyGlobals.CANNON_MOVIE_CLEAR, 0)
        else:
            self.notify.debug('__avatarGone in else, self.toonInsideAvId=%s avId=%s' % (self.toonInsideAvId, avId))

    def enterCannon(self, avId):
        if avId == base.localAvatar.doId:
            base.localAvatar.pose('lose', 110)
            base.localAvatar.pose('slip-forward', 25)
            base.cr.playGame.getPlace().setState('activity')
            base.localAvatar.collisionsOff()
            camera.reparentTo(self.barrelNode)
            camera.setPos(0, -2, 5)
            camera.setP(-20)
            if not self.activity.hasPlayedBefore():
                self.activity.displayRules()
                self.acceptOnce(DistributedPartyCannonActivity.RULES_DONE_EVENT, self.__enableCannonControl)
            else:
                self.__enableCannonControl()
            self.controllingToonAvId = avId
        if avId in self.cr.doId2do:
            self.toonInsideAvId = avId
            self.notify.debug('enterCannon self.toonInsideAvId=%d' % self.toonInsideAvId)
            toon = base.cr.doId2do[avId]
            if toon:
                self.acceptOnce(toon.uniqueName('disable'), self.__avatarGone, extraArgs=[avId])
                toon.stopSmooth()
                toon.dropShadow.hide()
                self.placeToonInside(toon)
            else:
                self.__avatarGone(avId)
        else:
            self.notify.warning('Unknown avatar %d in cannon %d' % (avId, self.doId))

    def exitCannon(self, avId):
        if avId == base.localAvatar.doId:
            self.activity.finishRules()
            self.ignore(DistributedPartyCannonActivity.RULES_DONE_EVENT)
        self.ignoreDisableForAvId(avId)
        if self.gui and avId == base.localAvatar.doId:
            self.gui.unload()
        toon = base.cr.doId2do.get(avId)
        if toon and self.getToonInside() == toon:
            self.resetToon()
        else:
            self.notify.debug('not resetting toon, toon=%s, self.getToonInside()=%s' % (toon, self.getToonInside()))

    def resetToon(self, pos = None):
        self.notify.debug('resetToon')
        toon = self.getToonInside()
        toonInsideAvId = self.toonInsideAvId
        self.notify.debug('%d resetToon self.toonInsideAvId=%d' % (self.doId, self.toonInsideAvId))
        self.removeToonDidNotFire()
        self.__setToonUpright(toon, pos)
        if toonInsideAvId == base.localAvatar.doId:
            self.notify.debug('%d resetToon toonInsideAvId ==localAvatar.doId' % self.doId)
            if pos:
                self.notify.debug('toon setting position to %s' % pos)
                base.localAvatar.setPos(pos)
            camera.reparentTo(base.localAvatar)
            base.localAvatar.collisionsOn()
            base.localAvatar.startPosHprBroadcast()
            base.localAvatar.enableAvatarControls()
            self.notify.debug('currentState=%s, requesting walk' % base.cr.playGame.getPlace().getState())
            base.cr.playGame.getPlace().setState('walk')
            self.notify.debug('after request walk currentState=%s,' % base.cr.playGame.getPlace().getState())
        toon.dropShadow.show()
        self.d_setLanded()

    def __setToonUpright(self, toon, pos = None):
        if not pos:
            pos = toon.getPos(render)
        toon.setPos(render, pos)
        toon.loop('neutral')
        toon.lookAt(self.parentNode)
        toon.setP(0)
        toon.setR(0)
        toon.setScale(1, 1, 1)

    def d_setLanded(self):
        self.notify.debugStateCall(self)
        if self.toonInsideAvId == base.localAvatar.doId:
            self.sendUpdate('setLanded', [base.localAvatar.doId])

    def setLanded(self, avId):
        self.removeAvFromCannon(avId)
        self.ignoreDisableForAvId(avId)

    def removeAvFromCannon(self, avId):
        place = base.cr.playGame.getPlace()
        av = base.cr.doId2do.get(avId)
        print('removeAvFromCannon')
        if place:
            if not hasattr(place, 'fsm'):
                return
            placeState = place.fsm.getCurrentState().getName()
            print(placeState)
            if placeState != 'fishing':
                if av != None:
                    av.startSmooth()
                    self.__destroyToonModels(avId)
                    return
        self.notify.debug('%s removeAvFromCannon' % self.doId)
        if av != None:
            self.notify.debug('%d removeAvFromCannon: destroying toon models' % self.doId)
            av.resetLOD()
            if av == base.localAvatar:
                if place:
                    place.fsm.request('walk')
            av.setPlayRate(1.0, 'run')
            if av.nametag and self.toonHead:
                av.nametag.removeNametag(self.toonHead.tag)
            if av.getParent().getName() == 'toonOriginChange':
                av.wrtReparentTo(render)
                self.__setToonUpright(av)
            if av == base.localAvatar:
                av.startPosHprBroadcast()
            av.startSmooth()
            av.setScale(1, 1, 1)
            self.ignore(av.uniqueName('disable'))
            self.__destroyToonModels(avId)
        return

    def __destroyToonModels(self, avId):
        av = base.cr.doId2do.get(avId)
        if not av:
            return
        if av != None:
            av.dropShadow.show()
            self.hitBumper = 0
            self.hitTarget = 0
            self.angularVel = 0
            self.vel = Vec3(0, 0, 0)
            self.lastVel = Vec3(0, 0, 0)
            self.lastPos = Vec3(0, 0, 0)
            self.landingPos = Vec3(0, 0, 0)
            self.t = 0
            self.lastT = 0
            self.deltaT = 0
            av = None
            self.lastWakeTime = 0
            self.localToonShooting = 0
        if self.toonHead != None:
            self.toonHead.reparentTo(hidden)
            self.toonHead.stopBlink()
            self.toonHead.stopLookAroundNow()
            self.toonHead.delete()
            self.toonHead = None
        self.model_Created = 0
        return

    def setClear(self):
        toon = base.cr.doId2do.get(self.toonInsideAvId)
        toonName = 'None'
        self.ignoreDisableForAvId(self.toonInsideAvId)
        if toon and self.isToonInside():
            toonName = toon.getName()
            toon.resetLOD()
            toon.setPlayRate(1.0, 'run')
            if toon.getParent().getName() == 'toonOriginChange':
                toon.wrtReparentTo(render)
                self.__setToonUpright(toon)
            toon.startSmooth()
            toon.setScale(1, 1, 1)
            self.ignore(toon.uniqueName('disable'))
            if self.toonInsideAvId == base.localAvatar.doId:
                toon.startPosHprBroadcast()
                try:
                    base.localAvatar.enableAvatarControls()
                except:
                    self.notify.warning("couldn't enable avatar controls")

                base.cr.playGame.getPlace().setState('walk')
        else:
            self.notify.debug('setClear in else toon=%s, self.isToonInsde()=%s' % (toonName, self.isToonInside()))
        self.toonInsideAvId = 0
        self.notify.debug('setClear self.toonInsideAvId=%d' % self.toonInsideAvId)
        if self.controllingToonAvId == base.localAvatar.doId:
            self.notify.debug('set_clear turning off cannon control')
            self.__disableCannonControl()
        self.controllingToonAvId = 0

    def __enableCannonControl(self):
        if not self.gui:
            self.gui = self.activity.gui
        self.gui.load()
        self.gui.enable(timer=PartyGlobals.CANNON_TIMEOUT)
        self.d_setTimeout()
        self.accept(CannonGui.FIRE_PRESSED, self.__handleFirePressed)
        self.__startLocalCannonMoveTask()

    def d_setTimeout(self):
        self.sendUpdate('setTimeout')

    def __disableCannonControl(self):
        if self.gui:
            self.gui.unload()
        self.ignore(CannonGui.FIRE_PRESSED)
        self.__stopLocalCannonMoveTask()

    def __startLocalCannonMoveTask(self):
        self.localCannonMoving = False
        task = Task(self.__localCannonMoveTask)
        task.lastPositionBroadcastTime = 0.0
        taskMgr.add(task, self.LOCAL_CANNON_MOVE_TASK)

    def __stopLocalCannonMoveTask(self):
        taskMgr.remove(self.LOCAL_CANNON_MOVE_TASK)
        if self.localCannonMoving:
            self.localCannonMoving = False
            self.stopMovingSound()

    def __localCannonMoveTask(self, task):
        rotVel = 0
        if self.gui.leftPressed:
            rotVel += CANNON_ROTATION_VEL
        if self.gui.rightPressed:
            rotVel -= CANNON_ROTATION_VEL
        self.setRotation(self.getRotation() + rotVel * globalClock.getDt())
        angVel = 0
        if self.gui.upPressed:
            angVel += CANNON_ANGLE_VEL
        if self.gui.downPressed:
            angVel -= CANNON_ANGLE_VEL
        self.setAngle(self.getAngle() + angVel * globalClock.getDt())
        if self.hasMoved():
            if not self.localCannonMoving:
                self.localCannonMoving = True
                self.loopMovingSound()
            self.updateModel()
            if task.time - task.lastPositionBroadcastTime > CANNON_MOVE_UPDATE_FREQ:
                self.notify.debug('Broadcast local cannon %s position' % self.doId)
                task.lastPositionBroadcastTime = task.time
                self.__broadcastLocalCannonPosition()
        elif self.localCannonMoving:
            self.localCannonMoving = False
            self.stopMovingSound()
            self.__broadcastLocalCannonPosition()
            self.notify.debug('Cannon Rot = %s, Angle = %s' % (self._rotation, self._angle))
        return Task.cont

    def __broadcastLocalCannonPosition(self):
        self.d_setCannonPosition(self._rotation, self._angle)

    def d_setCannonPosition(self, zRot, angle):
        self.sendUpdate('setCannonPosition', [zRot, angle])

    def updateCannonPosition(self, avId, zRot, angle):
        if avId and avId == self.toonInsideAvId and avId != base.localAvatar.doId:
            self.notify.debug('update cannon %s position zRot = %d, angle = %d' % (self.doId, zRot, angle))
            self.setRotation(zRot)
            self.setAngle(angle)
            self.updateModel()

    def __handleFirePressed(self):
        self.notify.debug('fire pressed')
        self.__disableCannonControl()
        self.__broadcastLocalCannonPosition()
        self.d_setCannonLit(self._rotation, self._angle)

    def d_setCannonLit(self, zRot, angle):
        self.sendUpdate('setCannonLit', [zRot, angle])

    def fire(self):
        if base.localAvatar.doId == self.controllingToonAvId:
            self.__disableCannonControl()
            self.d_setFired()
        self.playFireSequence()
        self.controllingToonAvId = None
        return

    def d_setFired(self):
        self.sendUpdate('setFired', [])

    def ignoreDisableForAvId(self, avId):
        toon = base.cr.doId2do.get(avId)
        if toon:
            self.notify.debug('ignoring %s' % toon.uniqueName('disable'))
            self.ignore(toon.uniqueName('disable'))
        else:
            self.notify.debug('ignoring disable-%s' % self.toonInsideAvId)
            self.ignore('disable-%s' % self.toonInsideAvId)
