from direct.distributed.DistributedObject import DistributedObject
from direct.distributed.DistributedObjectGlobal import DistributedObjectGlobal
from libotp import CFSpeech, CFTimeout
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from toontown.toon import ToonDNA
from toontown.parties import PartyGlobals

class DistributedPartyManager(DistributedObject):
    neverDisable = 1
    notify = directNotify.newCategory('DistributedPartyManager')
    PartyStatusChangedEvent = 'changePartyStatusResponseReceived'

    def __init__(self, cr):
        DistributedObject.__init__(self, cr)
        base.cr.partyManager = self
        self.allowUnreleased = False
        self.partyPlannerStyle = None
        self.partyPlannerName = None
        self.showDoid = False
        return

    def delete(self):
        DistributedObject.delete(self)
        self.cr.partyManager = None
        return

    def disable(self):
        self.notify.debug("i'm disabling DistributedPartyManager rightnow.")
        self.ignore('deallocateZoneIdFromPlannedParty')
        self.ignoreAll()
        DistributedObject.disable(self)

    def generate(self):
        self.notify.debug('BASE: generate')
        DistributedObject.generate(self)
        self.accept('deallocateZoneIdFromPlannedParty', self.deallocateZoneIdFromPlannedParty)
        self.announceGenerateName = self.uniqueName('generate')

    def deallocateZoneIdFromPlannedParty(self, zoneId):
        self.sendUpdate('freeZoneIdFromPlannedParty', [base.localAvatar.doId, zoneId])

    def allowUnreleasedClient(self):
        return self.allowUnreleased

    def setAllowUnreleaseClient(self, newValue):
        self.allowUnreleased = newValue

    def toggleAllowUnreleasedClient(self):
        self.allowUnreleased = not self.allowUnreleased
        return self.allowUnreleased

    def sendAddParty(self, hostId, startTime, endTime, isPrivate, inviteTheme, activities, decorations, inviteeIds):
        self.sendUpdate('addPartyRequest', [hostId,
         startTime,
         endTime,
         isPrivate,
         inviteTheme,
         activities,
         decorations,
         inviteeIds])

    def addPartyResponse(self, hostId, errorCode):
        messenger.send('addPartyResponseReceived', [hostId, errorCode])
        if hasattr(base.localAvatar, 'creatingNewPartyWithMagicWord'):
            if base.localAvatar.creatingNewPartyWithMagicWord:
                base.localAvatar.creatingNewPartyWithMagicWord = False
                if errorCode == PartyGlobals.AddPartyErrorCode.AllOk:
                    base.localAvatar.setChatAbsolute('New party entered into database successfully.', CFSpeech | CFTimeout)
                else:
                    base.localAvatar.setChatAbsolute('New party creation failed : %s' % PartyGlobals.AddPartyErrorCode.getString(errorCode), CFSpeech | CFTimeout)

    def requestPartyZone(self, avId, zoneId, callback):
        if zoneId < 0:
            zoneId = 0
        self.acceptOnce('requestPartyZoneComplete', callback)
        if hasattr(base.localAvatar, 'aboutToPlanParty'):
            if base.localAvatar.aboutToPlanParty:
                self.sendUpdate('getPartyZone', [avId, zoneId, True])
                return
        self.sendUpdate('getPartyZone', [avId, zoneId, False])

    def receivePartyZone(self, hostId, partyId, zoneId):
        if partyId != 0 and zoneId != 0:
            if base.localAvatar.doId == hostId:
                for partyInfo in base.localAvatar.hostedParties:
                    if partyInfo.partyId == partyId:
                        partyInfo.status == PartyGlobals.PartyStatus.Started

        messenger.send('requestPartyZoneComplete', [hostId, partyId, zoneId])

    def sendChangePrivateRequest(self, partyId, newPrivateStatus):
        self.sendUpdate('changePrivateRequest', [partyId, newPrivateStatus])

    def changePrivateResponse(self, partyId, newPrivateStatus, errorCode):
        if errorCode == PartyGlobals.ChangePartyFieldErrorCode.AllOk:
            self.notify.info('succesfully changed private field for the party')
            for partyInfo in localAvatar.hostedParties:
                if partyInfo.partyId == partyId:
                    partyInfo.isPrivate = newPrivateStatus

            messenger.send('changePartyPrivateResponseReceived', [partyId, newPrivateStatus, errorCode])
        else:
            messenger.send('changePartyPrivateResponseReceived', [partyId, newPrivateStatus, errorCode])
            self.notify.info('FAILED changing private field for the party')

    def sendChangePartyStatusRequest(self, partyId, newPartyStatus):
        self.sendUpdate('changePartyStatusRequest', [partyId, newPartyStatus])

    def changePartyStatusResponse(self, partyId, newPartyStatus, errorCode, beansRefunded):
        self.notify.debug('changePartyStatusResponse : partyId=%s newPartyStatus=%s errorCode=%s' % (partyId, newPartyStatus, errorCode))
        for partyInfo in localAvatar.hostedParties:
            if partyInfo.partyId == partyId:
                partyInfo.status = newPartyStatus

        messenger.send(self.PartyStatusChangedEvent, [partyId,
         newPartyStatus,
         errorCode,
         beansRefunded])

    def setNeverStartedPartyRefunded(self, partyId, newStatus, refund):
        partyInfo = None
        for pInfo in localAvatar.hostedParties:
            if pInfo.partyId == partyId:
                partyInfo = pInfo
                break

        if partyInfo:
            partyInfo.status = newStatus
            messenger.send(self.PartyStatusChangedEvent, [partyId,
             newStatus,
             0,
             refund])
        return

    def sendAvToPlayground(self, avId, retCode):
        messenger.send(PartyGlobals.KICK_TO_PLAYGROUND_EVENT, [retCode])
        self.notify.debug('sendAvToPlayground: %d' % avId)

    def leaveParty(self):
        if self.isDisabled():
            self.notify.warning('DistributedPartyManager disabled; unable to leave party.')
            return
        self.sendUpdate('exitParty', [localAvatar.zoneId])

    def removeGuest(self, ownerId, avId):
        self.notify.debug('removeGuest ownerId = %s, avId = %s' % (ownerId, avId))
        self.sendUpdate('removeGuest', [ownerId, avId])

    def isToonAllowedAtParty(self, avId, partyId):
        return PartyGlobals.GoToPartyStatus.AllowedToGo

    def getGoToPartyFailedMessage(self, reason):
        return ''

    def sendAvatarToParty(self, hostId):
        DistributedPartyManager.notify.debug('sendAvatarToParty hostId = %s' % hostId)
        self.sendUpdate('requestShardIdZoneIdForHostId', [hostId])

    def sendShardIdZoneIdToAvatar(self, shardId, zoneId):
        DistributedPartyManager.notify.debug('sendShardIdZoneIdToAvatar shardId = %s  zoneId = %s' % (shardId, zoneId))
        if shardId == 0 or zoneId == 0:
            base.cr.playGame.getPlace().handleBookClose()
            return
        hoodId = ToontownGlobals.PartyHood
        if shardId == base.localAvatar.defaultShard:
            shardId = None
        base.cr.playGame.getPlace().requestLeave({'loader': 'safeZoneLoader',
         'where': 'party',
         'how': 'teleportIn',
         'hoodId': hoodId,
         'zoneId': zoneId,
         'shardId': shardId,
         'avId': -1})
        return

    def setPartyPlannerStyle(self, dna):
        self.partyPlannerStyle = dna

    def getPartyPlannerStyle(self):
        if self.partyPlannerStyle:
            return self.partyPlannerStyle
        else:
            dna = ToonDNA.ToonDNA()
            dna.newToonRandom()
            return dna

    def setPartyPlannerName(self, name):
        self.partyPlannerName = name

    def getPartyPlannerName(self):
        if self.partyPlannerName:
            return self.partyPlannerName
        else:
            return TTLocalizer.PartyPlannerGenericName

    def toggleShowDoid(self):
        self.showDoid = not self.showDoid
        return self.showDoid

    def getShowDoid(self):
        return self.showDoid
