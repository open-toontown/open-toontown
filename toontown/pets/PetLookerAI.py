from pandac.PandaModules import *
from direct.directnotify import DirectNotifyGlobal
from direct.showbase import DirectObject
from otp.ai.AIZoneData import AIZoneData
from toontown.toonbase import ToontownGlobals
from toontown.pets import PetConstants

def getStartLookingAtOtherEvent(lookingAvId):
    return 'PetLookerAI-%s-startLookingAtOther' % lookingAvId


def getStopLookingAtOtherEvent(lookingAvId):
    return 'PetLookerAI-%s-stopLookingAtOther' % lookingAvId


def getStartLookedAtByOtherEvent(lookedAtAvId):
    return 'PetLookerAI-%s-startLookedAtByOther' % lookedAtAvId


def getStopLookedAtByOtherEvent(lookedAtAvId):
    return 'PetLookerAI-%s-stopLookedAtByOther' % lookedAtAvId


class PetLookerAI:
    notify = DirectNotifyGlobal.directNotify.newCategory('PetLookerAI')

    def __init__(self):
        self.__active = 0
        self.others = {}

    def destroy(self):
        if self.__active:
            self.exitPetLook()
        if len(self.others):
            PetLookerAI.notify.warning('%s: self.others not empty: %s' % (self.doId, self.others.keys()))
            self.others = {}

    def _getPetLookerBodyNode(self):
        return self

    def _isPet(self):
        return 0

    def enterPetLook(self):
        PetLookerAI.notify.debug('enterPetLook: %s' % self.doId)
        if self.__active:
            PetLookerAI.notify.warning('enterPetLook: %s already active!' % self.doId)
            return
        if len(self.others):
            PetLookerAI.notify.warning('%s: len(self.others) != 0: %s' % (self.doId, self.others.keys()))
            self.others = {}
        self.__active = 1
        self.__collNode = self._getPetLookerBodyNode().attachNewNode('PetLookerCollNode')
        self._createPetLookSphere()

    def exitPetLook(self):
        PetLookerAI.notify.debug('exitPetLook: %s' % self.doId)
        if not self.__active:
            PetLookerAI.notify.warning('exitPetLook: %s not active!' % self.doId)
            return
        if len(self.others):
            otherIds = self.others.keys()
            PetLookerAI.notify.warning('%s: still in otherIds: %s' % (self.doId, otherIds))
            for otherId in otherIds:
                self._handleLookingAtOtherStop(otherId)

            if len(self.others):
                PetLookerAI.notify.warning('%s: self.others still not empty: %s' % (self.doId, self.others.keys()))
                self.others = {}
        self._destroyPetLookSphere()
        self.__collNode.removeNode()
        del self.__collNode
        self.__active = 0

    def _createPetLookSphere(self):
        isPet = self._isPet()
        if isPet:
            radius = PetConstants.PetSphereRadius
        else:
            radius = PetConstants.NonPetSphereRadius
        lookSphere = CollisionSphere(0, 0, 0, radius)
        lookSphereNode = CollisionNode('petLookSphere-%s' % self.doId)
        lookSphereNode.addSolid(lookSphere)
        lookSphereNode.setFromCollideMask(BitMask32.allOff())
        if isPet:
            intoCollideMask = ToontownGlobals.PetLookatPetBitmask
            fromCollideMask = ToontownGlobals.PetLookatPetBitmask | ToontownGlobals.PetLookatNonPetBitmask
        else:
            intoCollideMask = ToontownGlobals.PetLookatNonPetBitmask
            fromCollideMask = ToontownGlobals.PetLookatPetBitmask
        lookSphereNode.setIntoCollideMask(intoCollideMask)
        lookSphereNode.setFromCollideMask(fromCollideMask)
        self.lookSphereNodePath = self.__collNode.attachNewNode(lookSphereNode)
        self.lookSphereNodePath.setTag('petLooker', '%s' % self.doId)
        self._cHandler = CollisionHandlerEvent()
        self._cHandler.addInPattern(self._getLookingStartEvent())
        self._cHandler.addOutPattern(self._getLookingStopEvent())
        collTrav = self.getCollTrav()
        if collTrav:
            collTrav.addCollider(self.lookSphereNodePath, self._cHandler)
        self.accept(self._getLookingStartEvent(), self._handleLookingAtOtherStart)
        self.accept(self._getLookingStopEvent(), self._handleLookingAtOtherStop)
        if hasattr(self, 'eventProxy'):
            PetLookerAI.notify.warning('%s: already have an eventProxy!' % self.doId)
        else:
            self.eventProxy = DirectObject.DirectObject()
            self.eventProxy.accept(self.getZoneChangeEvent(), self._handleZoneChange)

    def _destroyPetLookSphere(self):
        collTrav = self.getCollTrav()
        if collTrav:
            collTrav.removeCollider(self.lookSphereNodePath)
        del self._cHandler
        self.lookSphereNodePath.removeNode()
        del self.lookSphereNodePath
        self.ignore(self._getLookingStartEvent())
        self.ignore(self._getLookingStopEvent())
        self.eventProxy.ignoreAll()
        del self.eventProxy

    def _handleZoneChange(self, newZoneId, oldZoneId):
        PetLookerAI.notify.debug('_handleZoneChange: %s' % self.doId)
        if not self.__active:
            PetLookerAI.notify.warning('%s: _handleZoneChange: not active!' % self.doId)
            return
        oldZoneData = AIZoneData(self.air, self.parentId, oldZoneId)
        if oldZoneData.hasCollTrav():
            oldZoneData.getCollTrav().removeCollider(self.lookSphereNodePath)
        oldZoneData.destroy()
        newZoneData = AIZoneData(self.air, self.parentId, newZoneId)
        if newZoneData.hasCollTrav():
            newZoneData.getCollTrav().addCollider(self.lookSphereNodePath, self._cHandler)
        newZoneData.destroy()

    def _getLookingStartEvent(self):
        return 'PetLookerAI-lookingStart-%s' % self.doId

    def _getLookingStopEvent(self):
        return 'PetLookerAI-lookingStop-%s' % self.doId

    def __getOtherLookerDoIdFromCollEntry(self, collEntry):
        into = collEntry.getIntoNodePath()
        if not into.hasTag('petLooker'):
            return 0
        return int(into.getTag('petLooker'))

    def _handleLookingAtOtherStart(self, other):
        if not self.__active:
            PetLookerAI.notify.warning('%s: _handleLookingAtOtherStart: not active!' % self.doId)
            return
        if isinstance(other, CollisionEntry):
            other = self.__getOtherLookerDoIdFromCollEntry(other)
            if other == 0:
                PetLookerAI.notify.warning('%s: looking at unknown other avatar' % self.doId)
                return
        PetLookerAI.notify.debug('_handleLookingAtOtherStart: %s looking at %s' % (self.doId, other))
        if other in self.others:
            PetLookerAI.notify.warning('%s: other (%s) is already in self.others!' % (self.doId, other))
            if not hasattr(self, '_cHandler'):
                PetLookerAI.notify.warning('-->The looker sphere has already been destroyed')
        else:
            self.others[other] = None
            messenger.send(getStartLookingAtOtherEvent(self.doId), [other])
            messenger.send(getStartLookedAtByOtherEvent(other), [self.doId])
        return

    def _handleLookingAtOtherStop(self, other):
        if not self.__active:
            PetLookerAI.notify.warning('%s: _handleLookingAtOtherStop: not active!' % self.doId)
            return
        if isinstance(other, CollisionEntry):
            other = self.__getOtherLookerDoIdFromCollEntry(other)
            if other == 0:
                PetLookerAI.notify.warning('%s: stopped looking at unknown other avatar' % self.doId)
                return
        PetLookerAI.notify.debug('_handleLookingAtOtherStop: %s no longer looking at %s' % (self.doId, other))
        if other not in self.others:
            PetLookerAI.notify.warning('%s: other (%s) is not in self.others!' % (self.doId, other))
            if not hasattr(self, '_cHandler'):
                PetLookerAI.notify.warning('-->The looker sphere has already been destroyed')
        else:
            del self.others[other]
            messenger.send(getStopLookingAtOtherEvent(self.doId), [other])
            messenger.send(getStopLookedAtByOtherEvent(other), [self.doId])
