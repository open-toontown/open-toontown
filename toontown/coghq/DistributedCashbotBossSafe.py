from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals
from otp.otpbase import OTPGlobals
from . import DistributedCashbotBossObject

class DistributedCashbotBossSafe(DistributedCashbotBossObject.DistributedCashbotBossObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedCashbotBossSafe')
    grabPos = (0, 0, -8.2)
    craneFrictionCoef = 0.2
    craneSlideSpeed = 11
    craneRotateSpeed = 16
    wantsWatchDrift = 0

    def __init__(self, cr):
        DistributedCashbotBossObject.DistributedCashbotBossObject.__init__(self, cr)
        NodePath.__init__(self, 'object')
        self.index = None
        self.flyToMagnetSfx = loader.loadSfx('phase_5/audio/sfx/TL_rake_throw_only.ogg')
        self.hitMagnetSfx = loader.loadSfx('phase_5/audio/sfx/AA_drop_safe.ogg')
        self.toMagnetSoundInterval = Parallel(SoundInterval(self.flyToMagnetSfx, duration=ToontownGlobals.CashbotBossToMagnetTime, node=self), Sequence(Wait(ToontownGlobals.CashbotBossToMagnetTime - 0.02), SoundInterval(self.hitMagnetSfx, duration=1.0, node=self)))
        self.hitFloorSfx = loader.loadSfx('phase_5/audio/sfx/AA_drop_bigweight_miss.ogg')
        self.hitFloorSoundInterval = SoundInterval(self.hitFloorSfx, node=self)
        return

    def announceGenerate(self):
        DistributedCashbotBossObject.DistributedCashbotBossObject.announceGenerate(self)
        self.name = 'safe-%s' % self.doId
        self.setName(self.name)
        self.boss.safe.copyTo(self)
        self.shadow = self.find('**/shadow')
        self.collisionNode.setName('safe')
        cs = CollisionSphere(0, 0, 4, 4)
        self.collisionNode.addSolid(cs)
        if self.index == 0:
            self.collisionNode.setIntoCollideMask(ToontownGlobals.PieBitmask | OTPGlobals.WallBitmask)
            self.collisionNode.setFromCollideMask(ToontownGlobals.PieBitmask)
        self.boss.safes[self.index] = self
        self.setupPhysics('safe')
        self.resetToInitialPosition()

    def disable(self):
        del self.boss.safes[self.index]
        DistributedCashbotBossObject.DistributedCashbotBossObject.disable(self)

    def hideShadows(self):
        self.shadow.hide()

    def showShadows(self):
        self.shadow.show()

    def getMinImpact(self):
        if self.boss.heldObject:
            return ToontownGlobals.CashbotBossSafeKnockImpact
        else:
            return ToontownGlobals.CashbotBossSafeNewImpact

    def doHitGoon(self, goon):
        goon.b_destroyGoon()

    def resetToInitialPosition(self):
        posHpr = ToontownGlobals.CashbotBossSafePosHprs[self.index]
        self.setPosHpr(*posHpr)
        self.physicsObject.setVelocity(0, 0, 0)

    def fellOut(self):
        self.deactivatePhysics()
        self.d_requestInitial()

    def setIndex(self, index):
        self.index = index

    def setObjectState(self, state, avId, craneId):
        if state == 'I':
            self.demand('Initial')
        else:
            DistributedCashbotBossObject.DistributedCashbotBossObject.setObjectState(self, state, avId, craneId)

    def d_requestInitial(self):
        self.sendUpdate('requestInitial')

    def enterInitial(self):
        self.resetToInitialPosition()
        self.showShadows()
        if self.index == 0:
            self.stash()

    def exitInitial(self):
        if self.index == 0:
            self.unstash()
