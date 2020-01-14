from pandac.PandaModules import Point3, CollisionSphere, CollisionNode, BitMask32, Vec3, NodePath, TextNode, Vec4
from otp.otpbase import OTPGlobals
from otp.otpbase import OTPLocalizer
from direct.interval.IntervalGlobal import Sequence, Parallel, SoundInterval
from direct.interval.FunctionInterval import Wait
from direct.distributed import DistributedObject
from direct.directnotify import DirectNotifyGlobal
from direct.gui import DirectLabel
from toontown.toontowngui import TTDialog
from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownGlobals
from toontown.parties.ServerTimeGui import ServerTimeGui
from toontown.parties.PublicPartyGui import PublicPartyGui
from toontown.parties import PartyGlobals

class DistributedPartyGate(DistributedObject.DistributedObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedPartyGate')

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        self.publicPartyChooseGuiDoneEvent = 'doneChoosingPublicParty'
        self.publicPartyGui = PublicPartyGui(self.publicPartyChooseGuiDoneEvent)
        self.publicPartyGui.stash()
        self.loadClockSounds()
        self.hourSoundInterval = Sequence()
        self.accept('stoppedAsleep', self.handleSleep)

    def loadClockSounds(self):
        self.clockSounds = []
        for i in range(1, 13):
            if i < 10:
                si = '0%d' % i
            else:
                si = '%d' % i
            self.clockSounds.append(base.loader.loadSfx('phase_4/audio/sfx/clock%s.ogg' % si))

    def generate(self):
        DistributedObject.DistributedObject.generate(self)
        loader = self.cr.playGame.hood.loader
        partyGate = loader.geom.find('**/partyGate_grp')
        if partyGate.isEmpty():
            self.notify.warning('Could not find partyGate_grp in loader.geom')
            return
        self.clockFlat = partyGate.find('**/clock_flat')
        collSphere = CollisionSphere(0, 0, 0, 6.9)
        collSphere.setTangible(1)
        self.partyGateSphere = CollisionNode('PartyGateSphere')
        self.partyGateSphere.addSolid(collSphere)
        self.partyGateCollNodePath = partyGate.find('**/partyGate_stepsLocator').attachNewNode(self.partyGateSphere)
        self.__enableCollisions()
        self.toontownTimeGui = ServerTimeGui(partyGate, hourCallback=self.hourChange)
        self.toontownTimeGui.setPos(partyGate.find('**/clockText_locator').getPos() + Point3(0.0, 0.0, -0.2))
        self.toontownTimeGui.setHpr(partyGate.find('**/clockText_locator').getHpr())
        self.toontownTimeGui.setScale(12.0, 1.0, 26.0)
        self.toontownTimeGui.amLabel.setPos(-0.035, 0, -0.032)
        self.toontownTimeGui.amLabel.setScale(0.5)
        self.toontownTimeGui.updateTime()
        self.setupSignText()

    def setupSignText(self):
        loader = self.cr.playGame.hood.loader
        partyGate = loader.geom.find('**/partyGateSignGroup')
        if partyGate.isEmpty():
            self.notify.warning('Could not find partyGate_grp in loader.geom')
            return
        gateFont = ToontownGlobals.getMinnieFont()
        leftSign = partyGate.find('**/signTextL_locatorBack')
        signScale = 0.35
        wordWrap = 8
        leftText = DirectLabel.DirectLabel(parent=leftSign, pos=(0, 0.0, 0.0), relief=None, text=TTLocalizer.PartyGateLeftSign, text_align=TextNode.ACenter, text_font=gateFont, text_wordwrap=wordWrap, text_fg=Vec4(0.7, 0.3, 0.3, 1.0), scale=signScale)
        rightSign = partyGate.find('**/signTextR_locatorFront')
        rightText = DirectLabel.DirectLabel(parent=rightSign, pos=(0, 0.0, 0.0), relief=None, text=TTLocalizer.PartyGateRightSign, text_align=TextNode.ACenter, text_font=gateFont, text_wordwrap=wordWrap, text_fg=Vec4(0.7, 0.3, 0.3, 1.0), scale=signScale)
        return

    def announceGenerate(self):
        DistributedObject.DistributedObject.announceGenerate(self)
        if self.zoneId in ToontownGlobals.dnaMap:
            playground = ToontownGlobals.dnaMap[self.zoneId]
        else:
            playground = ToontownGlobals.dnaMap[2000]
        self.toontownTimeGui.hourLabel['text_fg'] = PartyGlobals.PlayGroundToPartyClockColors[playground]
        self.toontownTimeGui.colonLabel['text_fg'] = PartyGlobals.PlayGroundToPartyClockColors[playground]
        self.toontownTimeGui.minutesLabel['text_fg'] = PartyGlobals.PlayGroundToPartyClockColors[playground]
        self.toontownTimeGui.amLabel['text_fg'] = PartyGlobals.PlayGroundToPartyClockColors[playground]

    def disable(self):
        DistributedObject.DistributedObject.disable(self)
        self.__disableCollisions()
        self.toontownTimeGui.ival.finish()
        self.hourSoundInterval.finish()
        if self.publicPartyGui:
            self.publicPartyGui.stash()
            self.publicPartyGui.destroy()
            self.publicPartyGui = None
        return

    def delete(self):
        DistributedObject.DistributedObject.delete(self)
        self.toontownTimeGui.destroy()
        del self.toontownTimeGui
        self.hourSoundInterval.finish()
        del self.hourSoundInterval
        del self.clockFlat
        if self.publicPartyGui:
            self.publicPartyGui.destroy()
            del self.publicPartyGui
        self.partyGateCollNodePath.removeNode()
        del self.partyGateCollNodePath
        self.ignoreAll()

    def showMessage(self, message):
        self.messageDoneEvent = self.uniqueName('messageDoneEvent')
        self.acceptOnce(self.messageDoneEvent, self.__handleMessageDone)
        self.messageGui = TTDialog.TTGlobalDialog(doneEvent=self.messageDoneEvent, message=message, style=TTDialog.Acknowledge)

    def __handleMessageDone(self):
        self.ignore(self.messageDoneEvent)
        self.freeAvatar()
        self.messageGui.cleanup()
        self.messageGui = None
        return

    def __handleAskDone(self):
        DistributedPartyGate.notify.debug('__handleAskDone')
        self.ignore(self.publicPartyChooseGuiDoneEvent)
        doneStatus = self.publicPartyGui.doneStatus
        self.publicPartyGui.stash()
        if doneStatus is None:
            self.freeAvatar()
            return
        self.sendUpdate('partyChoiceRequest', [base.localAvatar.doId, doneStatus[0], doneStatus[1]])
        return

    def partyRequestDenied(self, reason):
        DistributedPartyGate.notify.debug('partyRequestDenied( reason=%s )' % PartyGlobals.PartyGateDenialReasons.getString(reason))
        if reason == PartyGlobals.PartyGateDenialReasons.Unavailable:
            self.showMessage(TTLocalizer.PartyGatePartyUnavailable)
        elif reason == PartyGlobals.PartyGateDenialReasons.Full:
            self.showMessage(TTLocalizer.PartyGatePartyFull)

    def setParty(self, partyInfoTuple):
        DistributedPartyGate.notify.debug('setParty')
        self.freeAvatar()
        if partyInfoTuple[0] == 0:
            DistributedPartyGate.notify.debug('Public Party closed before toon could get to it.')
            return
        shardId, zoneId, numberOfGuests, hostName, activityIds, lane = partyInfoTuple
        if base.localAvatar.defaultShard == shardId:
            shardId = None
        base.cr.playGame.getPlace().requestLeave({'loader': 'safeZoneLoader',
         'where': 'party',
         'how': 'teleportIn',
         'hoodId': ToontownGlobals.PartyHood,
         'zoneId': zoneId,
         'shardId': shardId,
         'avId': -1})
        return

    def freeAvatar(self):
        base.localAvatar.posCamera(0, 0)
        base.cr.playGame.getPlace().setState('walk')

    def hourChange(self, currentHour):
        currentHour = currentHour % 12
        if currentHour == 0:
            currentHour = 12
        self.hourSoundInterval = Parallel()
        seq1 = Sequence()
        for i in range(currentHour):
            seq1.append(SoundInterval(self.clockSounds[i]))
            seq1.append(Wait(0.2))

        timeForEachDeformation = seq1.getDuration() / currentHour
        seq2 = Sequence()
        for i in range(currentHour):
            seq2.append(self.clockFlat.scaleInterval(timeForEachDeformation / 2.0, Vec3(0.9, 1.0, 1.2), blendType='easeInOut'))
            seq2.append(self.clockFlat.scaleInterval(timeForEachDeformation / 2.0, Vec3(1.2, 1.0, 0.9), blendType='easeInOut'))

        seq2.append(self.clockFlat.scaleInterval(timeForEachDeformation / 2.0, Vec3(1.0, 1.0, 1.0), blendType='easeInOut'))
        self.hourSoundInterval.append(seq1)
        self.hourSoundInterval.append(seq2)
        self.hourSoundInterval.start()

    def handleEnterGateSphere(self, collEntry):
        self.notify.debug('Entering steps Sphere....')
        base.cr.playGame.getPlace().fsm.request('stopped')
        self.sendUpdate('getPartyList', [base.localAvatar.doId])

    def listAllPublicParties(self, publicPartyInfo):
        self.notify.debug('listAllPublicParties : publicPartyInfo = %s' % publicPartyInfo)
        self.acceptOnce(self.publicPartyChooseGuiDoneEvent, self.__handleAskDone)
        self.publicPartyGui.refresh(publicPartyInfo)
        self.publicPartyGui.unstash()

    def __enableCollisions(self):
        self.accept('enterPartyGateSphere', self.handleEnterGateSphere)
        self.partyGateSphere.setCollideMask(OTPGlobals.WallBitmask)

    def __disableCollisions(self):
        self.ignore('enterPartyGateSphere')
        self.partyGateSphere.setCollideMask(BitMask32(0))

    def handleSleep(self):
        if hasattr(self, 'messageGui') and self.messageGui:
            self.__handleMessageDone()
