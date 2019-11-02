from direct.interval.IntervalGlobal import *
from direct.distributed.ClockDelta import *
from toontown.toonbase import ToontownGlobals
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM
from toontown.building import DistributedDoor
from toontown.hood import ZoneUtil
from toontown.building import FADoorCodes
from toontown.building import DoorTypes
from toontown.toonbase import TTLocalizer
from toontown.toontowngui import TeaserPanel

class DistributedCogHQDoor(DistributedDoor.DistributedDoor):

    def __init__(self, cr):
        DistributedDoor.DistributedDoor.__init__(self, cr)
        self.openSfx = base.loadSfx('phase_9/audio/sfx/CHQ_door_open.mp3')
        self.closeSfx = base.loadSfx('phase_9/audio/sfx/CHQ_door_close.mp3')

    def wantsNametag(self):
        return 0

    def getRequestStatus(self):
        zoneId = self.otherZoneId
        request = {'loader': ZoneUtil.getBranchLoaderName(zoneId),
         'where': ZoneUtil.getToonWhereName(zoneId),
         'how': 'doorIn',
         'hoodId': ZoneUtil.getHoodId(zoneId),
         'zoneId': zoneId,
         'shardId': None,
         'avId': -1,
         'allowRedirect': 0,
         'doorDoId': self.otherDoId}
        return request

    def enterClosing(self, ts):
        doorFrameHoleRight = self.findDoorNode('doorFrameHoleRight')
        if doorFrameHoleRight.isEmpty():
            self.notify.warning('enterClosing(): did not find doorFrameHoleRight')
            return
        rightDoor = self.findDoorNode('rightDoor')
        if rightDoor.isEmpty():
            self.notify.warning('enterClosing(): did not find rightDoor')
            return
        otherNP = self.getDoorNodePath()
        trackName = 'doorClose-%d' % self.doId
        if self.rightSwing:
            h = 100
        else:
            h = -100
        self.finishDoorTrack()
        self.doorTrack = Parallel(Sequence(LerpHprInterval(nodePath=rightDoor, duration=1.0, hpr=VBase3(0, 0, 0), startHpr=VBase3(h, 0, 0), other=otherNP, blendType='easeInOut'), Func(doorFrameHoleRight.hide), Func(self.hideIfHasFlat, rightDoor)), Sequence(Wait(0.5), SoundInterval(self.closeSfx, node=rightDoor)), name=trackName)
        self.doorTrack.start(ts)
        if hasattr(self, 'done'):
            request = self.getRequestStatus()
            messenger.send('doorDoneEvent', [request])

    def exitDoorEnterClosing(self, ts):
        doorFrameHoleLeft = self.findDoorNode('doorFrameHoleLeft')
        if doorFrameHoleLeft.isEmpty():
            self.notify.warning('enterOpening(): did not find flatDoors')
            return
        if ZoneUtil.isInterior(self.zoneId):
            doorFrameHoleLeft.setColor(1.0, 1.0, 1.0, 1.0)
        if self.leftSwing:
            h = -100
        else:
            h = 100
        leftDoor = self.findDoorNode('leftDoor')
        if not leftDoor.isEmpty():
            otherNP = self.getDoorNodePath()
            trackName = 'doorExitTrack-%d' % self.doId
            self.doorExitTrack = Parallel(Sequence(LerpHprInterval(nodePath=leftDoor, duration=1.0, hpr=VBase3(0, 0, 0), startHpr=VBase3(h, 0, 0), other=otherNP, blendType='easeInOut'), Func(doorFrameHoleLeft.hide), Func(self.hideIfHasFlat, leftDoor)), Sequence(Wait(0.5), SoundInterval(self.closeSfx, node=leftDoor)), name=trackName)
            self.doorExitTrack.start(ts)

    def setZoneIdAndBlock(self, zoneId, block):
        self.zoneId = zoneId
        self.block = block
        canonicalZoneId = ZoneUtil.getCanonicalZoneId(zoneId)
        if canonicalZoneId in (ToontownGlobals.BossbotHQ, ToontownGlobals.BossbotLobby):
            self.doorX = 1.0

    def enterDoor(self):
        if self.allowedToEnter(self.zoneId):
            messenger.send('DistributedDoor_doorTrigger')
            self.sendUpdate('requestEnter')
        else:
            place = base.cr.playGame.getPlace()
            if place:
                place.fsm.request('stopped')
            self.dialog = TeaserPanel.TeaserPanel(pageName='cogHQ', doneFunc=self.handleOkTeaser)

    def doorTrigger(self, args = None):
        if localAvatar.hasActiveBoardingGroup():
            rejectText = TTLocalizer.BoardingCannotLeaveZone
            localAvatar.boardingParty.showMe(rejectText)
            return
        DistributedDoor.DistributedDoor.doorTrigger(self, args)
