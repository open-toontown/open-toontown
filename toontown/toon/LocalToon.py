import random
import math
import time
import re
import zlib
from direct.interval.IntervalGlobal import *
from direct.distributed.ClockDelta import *
from direct.showbase.PythonUtil import *
from direct.gui.DirectGui import *
from direct.task import Task
from direct.showbase import PythonUtil
from direct.directnotify import DirectNotifyGlobal
from direct.gui import DirectGuiGlobals
from pandac.PandaModules import *
from otp.avatar import LocalAvatar
from otp.login import LeaveToPayDialog
from otp.avatar import PositionExaminer
from otp.otpbase import OTPGlobals
from otp.avatar import DistributedPlayer
from toontown.shtiker import ShtikerBook
from toontown.shtiker import InventoryPage
from toontown.shtiker import MapPage
from toontown.shtiker import OptionsPage
from toontown.shtiker import ShardPage
from toontown.shtiker import QuestPage
from toontown.shtiker import TrackPage
from toontown.shtiker import KartPage
from toontown.shtiker import GardenPage
from toontown.shtiker import GolfPage
from toontown.shtiker import SuitPage
from toontown.shtiker import DisguisePage
from toontown.shtiker import PhotoAlbumPage
from toontown.shtiker import FishPage
from toontown.shtiker import NPCFriendPage
from toontown.shtiker import EventsPage
from toontown.shtiker import TIPPage
from toontown.quest import Quests
from toontown.quest import QuestParser
from toontown.toonbase.ToontownGlobals import *
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from toontown.catalog import CatalogNotifyDialog
from toontown.chat import ToontownChatManager
from toontown.chat import TTTalkAssistant
from toontown.estate import GardenGlobals
from toontown.battle.BattleSounds import *
from toontown.battle import Fanfare
from toontown.parties import PartyGlobals
from toontown.toon import ElevatorNotifier
from toontown.toon import ToonDNA
import DistributedToon
import Toon
import LaffMeter
from toontown.quest import QuestMap
from toontown.toon.DistributedNPCToonBase import DistributedNPCToonBase
WantNewsPage = base.config.GetBool('want-news-page', ToontownGlobals.DefaultWantNewsPageSetting)
from toontown.toontowngui import NewsPageButtonManager
if WantNewsPage:
    from toontown.shtiker import NewsPage
AdjustmentForNewsButton = -0.275
ClaraBaseXPos = 1.45
if (__debug__):
    import pdb

class LocalToon(DistributedToon.DistributedToon, LocalAvatar.LocalAvatar):
    neverDisable = 1
    piePowerSpeed = base.config.GetDouble('pie-power-speed', 0.2)
    piePowerExponent = base.config.GetDouble('pie-power-exponent', 0.75)

    def __init__(self, cr):
        try:
            self.LocalToon_initialized
        except:
            self.LocalToon_initialized = 1
            self.numFlowers = 0
            self.maxFlowerBasket = 0
            DistributedToon.DistributedToon.__init__(self, cr)
            chatMgr = ToontownChatManager.ToontownChatManager(cr, self)
            talkAssistant = TTTalkAssistant.TTTalkAssistant()
            LocalAvatar.LocalAvatar.__init__(self, cr, chatMgr, talkAssistant, passMessagesThrough=True)
            self.soundRun = base.loadSfx('phase_3.5/audio/sfx/AV_footstep_runloop.wav')
            self.soundWalk = base.loadSfx('phase_3.5/audio/sfx/AV_footstep_walkloop.wav')
            self.soundWhisper = base.loadSfx('phase_3.5/audio/sfx/GUI_whisper_3.mp3')
            self.soundPhoneRing = base.loadSfx('phase_3.5/audio/sfx/telephone_ring.mp3')
            self.soundSystemMessage = base.loadSfx('phase_3/audio/sfx/clock03.mp3')
            self.positionExaminer = PositionExaminer.PositionExaminer()
            friendsGui = loader.loadModel('phase_3.5/models/gui/friendslist_gui')
            friendsButtonNormal = friendsGui.find('**/FriendsBox_Closed')
            friendsButtonPressed = friendsGui.find('**/FriendsBox_Rollover')
            friendsButtonRollover = friendsGui.find('**/FriendsBox_Rollover')
            newScale = oldScale = 0.8
            if WantNewsPage:
                newScale = oldScale * ToontownGlobals.NewsPageScaleAdjust
            self.bFriendsList = DirectButton(image=(friendsButtonNormal, friendsButtonPressed, friendsButtonRollover), relief=None, pos=(1.192, 0, 0.875), scale=newScale, text=('', TTLocalizer.FriendsListLabel, TTLocalizer.FriendsListLabel), text_scale=0.09, text_fg=Vec4(1, 1, 1, 1), text_shadow=Vec4(0, 0, 0, 1), text_pos=(0, -0.18), text_font=ToontownGlobals.getInterfaceFont(), command=self.sendFriendsListEvent)
            self.bFriendsList.hide()
            self.friendsListButtonActive = 0
            self.friendsListButtonObscured = 0
            self.moveFurnitureButtonObscured = 0
            self.clarabelleButtonObscured = 0
            friendsGui.removeNode()
            self.__furnitureGui = None
            self.__clarabelleButton = None
            self.__clarabelleFlash = None
            self.furnitureManager = None
            self.furnitureDirector = None
            self.gotCatalogNotify = 0
            self.__catalogNotifyDialog = None
            self.accept('phaseComplete-5.5', self.loadPhase55Stuff)
            Toon.loadDialog()
            self.isIt = 0
            self.cantLeaveGame = 0
            self.tunnelX = 0.0
            self.estate = None
            self.__pieBubble = None
            self.allowPies = 0
            self.__pieButton = None
            self.__piePowerMeter = None
            self.__piePowerMeterSequence = None
            self.__pieButtonType = None
            self.__pieButtonCount = None
            self.tossPieStart = None
            self.__presentingPie = 0
            self.__pieSequence = 0
            self.wantBattles = base.config.GetBool('want-battles', 1)
            self.seeGhosts = base.config.GetBool('see-ghosts', 0)
            wantNameTagAvIds = base.config.GetBool('want-nametag-avids', 0)
            if wantNameTagAvIds:
                messenger.send('nameTagShowAvId', [])
                base.idTags = 1
            self.glitchX = 0
            self.glitchY = 0
            self.glitchZ = 0
            self.glitchCount = 0
            self.ticker = 0
            self.glitchOkay = 1
            self.tempGreySpacing = 0
            self.wantStatePrint = base.config.GetBool('want-statePrint', 0)
            self.__gardeningGui = None
            self.__gardeningGuiFake = None
            self.__shovelButton = None
            self.shovelRelatedDoId = 0
            self.shovelAbility = ''
            self.plantToWater = 0
            self.shovelButtonActiveCount = 0
            self.wateringCanButtonActiveCount = 0
            self.showingWateringCan = 0
            self.showingShovel = 0
            self.touchingPlantList = []
            self.inGardenAction = None
            self.guiConflict = 0
            self.lastElevatorLeft = 0
            self.elevatorNotifier = ElevatorNotifier.ElevatorNotifier()
            self.accept(OTPGlobals.AvatarFriendAddEvent, self.sbFriendAdd)
            self.accept(OTPGlobals.AvatarFriendUpdateEvent, self.sbFriendUpdate)
            self.accept(OTPGlobals.AvatarFriendRemoveEvent, self.sbFriendRemove)
            self._zoneId = None
            self.accept('system message aknowledge', self.systemWarning)
            self.systemMsgAckGuiDoneEvent = 'systemMsgAckGuiDoneEvent'
            self.accept(self.systemMsgAckGuiDoneEvent, self.hideSystemMsgAckGui)
            self.systemMsgAckGui = None
            self.createSystemMsgAckGui()
            if not hasattr(base.cr, 'lastLoggedIn'):
                base.cr.lastLoggedIn = self.cr.toontownTimeManager.convertStrToToontownTime('')
            self.setLastTimeReadNews(base.cr.lastLoggedIn)
            self.acceptingNewFriends = Settings.getAcceptingNewFriends() and base.config.GetBool('accepting-new-friends-default', True)
            self.acceptingNonFriendWhispers = Settings.getAcceptingNonFriendWhispers() and base.config.GetBool('accepting-non-friend-whispers-default', True)
            self.physControls.event.addAgainPattern('again%in')
            self.oldPos = None
            self.questMap = None
            self.prevToonIdx = 0

    def wantLegacyLifter(self):
        return True

    def startGlitchKiller(self):
        if localAvatar.getZoneId() not in GlitchKillerZones:
            return
        if __dev__:
            self.glitchMessage = 'START GLITCH KILLER'
            randChoice = random.randint(0, 3)
            if randChoice == 0:
                self.glitchMessage = 'START GLITCH KILLER'
            elif randChoice == 1:
                self.glitchMessage = 'GLITCH KILLER ENGAGED'
            elif randChoice == 2:
                self.glitchMessage = 'GLITCH KILLER GO!'
            elif randChoice == 3:
                self.glitchMessage = 'GLITCH IN YO FACE FOOL!'
            self.notify.debug(self.glitchMessage)
        taskMgr.remove(self.uniqueName('glitchKiller'))
        taskMgr.add(self.glitchKiller, self.uniqueName('glitchKiller'))
        self.glitchOkay = 1

    def pauseGlitchKiller(self):
        self.tempGreySpacing = 1

    def unpauseGlitchKiller(self):
        self.tempGreySpacing = 0

    def stopGlitchKiller(self):
        if __dev__ and hasattr(self, 'glitchMessage'):
            if self.glitchMessage == 'START GLITCH KILLER':
                self.notify.debug('STOP GLITCH KILLER')
            elif self.glitchMessage == 'GLITCH KILLER ENGAGED':
                self.notify.debug('GLITCH KILLER DISENGAGED')
            elif self.glitchMessage == 'GLITCH KILLER GO!':
                self.notify.debug('GLITCH KILLER NO GO!')
            elif self.glitchMessage == 'GLITCH IN YO FACE FOOL!':
                self.notify.debug('GLITCH OFF YO FACE FOOL!')
        taskMgr.remove(self.uniqueName('glitchKiller'))
        self.glitchOkay = 1

    def glitchKiller(self, taskFooler = 0):
        if base.greySpacing or self.tempGreySpacing:
            return Task.cont
        self.ticker += 1
        if not self.physControls.lifter.hasContact() and not self.glitchOkay:
            self.glitchCount += 1
        else:
            self.glitchX = self.getX()
            self.glitchY = self.getY()
            self.glitchZ = self.getZ()
            self.glitchCount = 0
            if self.physControls.lifter.hasContact():
                self.glitchOkay = 0
        if hasattr(self, 'physControls'):
            if self.ticker >= 10:
                self.ticker = 0
        if self.glitchCount >= 7:
            print 'GLITCH MAXED!!! resetting pos'
            self.setX(self.glitchX - 1 * (self.getX() - self.glitchX))
            self.setY(self.glitchY - 1 * (self.getY() - self.glitchY))
            self.glitchCount = 0
        return Task.cont

    def announceGenerate(self):
        self.startLookAround()
        if base.wantNametags:
            self.nametag.manage(base.marginManager)
        self.startHackObservation()
        DistributedToon.DistributedToon.announceGenerate(self)
        from otp.friends import FriendInfo

    def toonPosCheck(self, task = None):
        toon = random.choice(self.cr.toons.values())
        if toon and toon is not self and not isinstance(toon, DistributedNPCToonBase):
            self.notify.debug('checking position for %s' % toon.doId)
            realTimeStart = globalClock.getRealTime()
            numOtherToons = len(self.cr.toons.values())
            for otherToonIdxBase in range(numOtherToons):
                otherToonIdx = otherToonIdxBase + self.prevToonIdx
                if otherToonIdx >= numOtherToons:
                    otherToonIdx = otherToonIdx % numOtherToons
                if globalClock.getRealTime() > realTimeStart + AV_TOUCH_CHECK_TIMELIMIT_CL:
                    self.notify.debug('too much time, exiting at index %s' % otherToonIdx)
                    self.prevToonIdx = otherToonIdx
                    break
                otherToon = self.cr.toons.values()[otherToonIdx]
                self.notify.debug('comparing with toon %s at index %s' % (otherToon.doId, otherToonIdx))
                if otherToon and otherToon is not toon and otherToon is not self and not isinstance(otherToon, DistributedNPCToonBase):
                    toonPos = toon.getPos(render)
                    otherToonPos = otherToon.getPos(render)
                    self.notify.debug('pos1: %s pos2: %s' % (toonPos, otherToonPos))
                    zDist = otherToonPos.getZ() - toonPos.getZ()
                    toonPos.setZ(0)
                    otherToonPos.setZ(0)
                    moveVec = otherToonPos - toonPos
                    dist = moveVec.length()
                    self.notify.debug('distance to %s is %s %s' % (otherToon.doId, dist, zDist))
                    if dist < AV_TOUCH_CHECK_DIST and zDist < AV_TOUCH_CHECK_DIST_Z:
                        self.notify.debug('inappropriate touching!!!')
                        if toon.getParent() == render:
                            toonToMoveId = toon.doId
                            toonToNotMoveId = otherToon.doId
                        else:
                            toonToMoveId = otherToon.doId
                            toonToNotMoveId = toon.doId
                        self.sendUpdate('flagAv', [toonToMoveId, AV_FLAG_REASON_TOUCH, [str(toonToNotMoveId)]])
                        self.prevToonIdx = otherToonIdx
                        break
                self.notify.debug('spent %s seconds doing pos check for %s' % (globalClock.getRealTime() - realTimeStart, toon.doId))

        return Task.again

    def tmdcc(self, task = None):
        toon = random.choice(self.cr.toons.values())
        result = self._tmdcc(toon)
        if task:
            if result:
                task.setDelay(5.0)
            else:
                task.setDelay(1.5)
        return Task.again

    def _tmdcc(self, toon, checks = []):
        result = None
        if isinstance(toon, DistributedNPCToonBase) or toon is localAvatar or toon.isEmpty() or toon.bFake or toon._delayDeleteForceAllow:
            return result
        startTime = globalClock.getRealTime()

        def delayedSend(toon, msg):
            if toon:
                toon.sendLogSuspiciousEvent(msg)
            return Task.done

        def sendT(header, msg, sToon, sendFooter = False, sendLs = True):
            uid = '[' + str(globalClock.getRealTime()) + ']'
            msgSize = 800 - (len(header) + len(uid) + 1)
            uname = self.uniqueName('ioorrd234')
            currCounter = 0

            def sendAsParts(message, counter):
                for currBlock in range(0, len(message) / msgSize + 1):
                    fmsg = '%s %02d: ' % (uid, currBlock + counter) + header + ': "%s"' % message[currBlock * msgSize:currBlock * msgSize + msgSize]
                    taskMgr.doMethodLater(0.08 * (currBlock + counter), delayedSend, uname + str(currBlock + counter), extraArgs=[sToon, fmsg])

                return currBlock + counter + 1

            currCounter = sendAsParts(msg, currCounter)
            if sendLs:
                sstream = StringStream.StringStream()
                sToon.ls(sstream)
                sdata = sstream.getData()
                currCounter = sendAsParts(sdata, currCounter)
            if sendFooter:
                sstream.clearData()
                if hasattr(sToon, 'suitGeom'):
                    sToon.suitGeom.ls(sstream)
                bs = ''
                nodeNames = config.GetString('send-suspicious-bam', 'to_head')
                if nodeNames != '':
                    bs = ' bam ' + nodeNames + ': '
                    nodesToLog = []
                    for currName in nodeNames.split():
                        nodesToLog.append(sToon.find('**/' + currName))

                    for currNode in nodesToLog:
                        bs += zlib.compress(currNode.encodeToBamStream()).encode('hex') + '_'

                footer = 'loc: %s dna: %s gmname: %s ntag: %s ceffect: %s disguise: %s sstyle: %s sgeom: %s %s' % (str(sToon.getLocation()),
                 str(sToon.style.asTuple()),
                 sToon.gmNameTagEnabled,
                 str(sToon.nametag and sToon.nametag.getContents()),
                 str(sToon.cheesyEffect),
                 sToon.isDisguised,
                 hasattr(sToon, 'suit') and str(sToon.suit.style),
                 hasattr(sToon, 'suitGeom') and sstream.getData(),
                 bs)
                currCounter = sendAsParts(footer, currCounter)

        self.sendUpdate('requestPing', [toon.doId])
        if not checks:
            numChecks = 6
            checks = [random.choice(range(1, numChecks + 1))]

        def findParentAv(node):
            avId = 0
            topParent = node
            while topParent and not topParent.getTag('avatarDoId'):
                topParent = topParent.getParent()

            if topParent:
                avIdStr = topParent.getTag('avatarDoId')
                if avIdStr:
                    avId = int(avIdStr)
            return (self.cr.getDo(avId), avId)

        msgHeader = 'AvatarHackWarning!'

        def hacker_detect_immediate(cbdata):
            action = cbdata.getAction()
            node = cbdata.getNode()
            np = NodePath(node)
            if not self.cr or not self.cr.distributedDistrict or not self.cr.distributedDistrict.getAllowAHNNLog():
                if self.cr and self.cr.distributedDistrict:
                    sToon, avId = findParentAv(np)
                    if sToon is localAvatar:
                        return
                    if sToon and isinstance(sToon, DistributedToon.DistributedToon):
                        msg = "Blocking '%s' '%s' '%s'" % (self.cr.distributedDistrict.getAllowAHNNLog(), np, re.sub('<', '[', StackTrace(start=1).compact()))
                        sendT(msgHeader, msg, sToon, sendFooter=False, sendLs=False)
                return
            try:
                parentNames = ['__Actor_modelRoot', 'to_head']
                newParent = np.getParent()
                if newParent and newParent.getName() in parentNames:
                    newParentParent = newParent.getParent()
                    parentParentNames = ['actorGeom', '__Actor_modelRoot']
                    if newParentParent and newParentParent.getName() in parentParentNames:
                        sToon, avId = findParentAv(newParentParent.getParent())
                        if sToon is localAvatar:
                            return
                        header = msgHeader + ' nodename'
                        avInfo = "hacker activity '%s' avatar %s node name '%s' with parents '%s' and '%s'!" % (action,
                         avId,
                         np.getName(),
                         newParent.getName(),
                         newParentParent.getName())
                        if sToon and isinstance(sToon, DistributedToon.DistributedToon):
                            avInfo += ' trace: '
                            avInfo += re.sub('<', '[', StackTrace(start=1).compact())
                            sendT(header, avInfo, sToon=sToon, sendFooter=True)
                        else:
                            sendLogSuspiciousEvent(header, 'got non-toon or missing parent %s...' % sToon + avInfo)
            except:
                pass

        if config.GetBool('detect-suspicious-nodename', True):
            PandaNode.setDetectCallback(PythonCallbackObject(hacker_detect_immediate))

        def trackChat(chattingToon):

            def _spoke(cbdata):
                avId = cbdata.getId()
                av = self.cr.getDo(avId)
                chat = cbdata.getChat()
                if avId != localAvatar.doId and av:
                    avInfo = 'suspicious chat "%s" trace: ' % chat
                    avInfo += re.sub('<', '[', StackTrace(start=1).compact())
                    sendT(msgHeader + ' chat', avInfo, chattingToon, sendFooter=False, sendLs=False)

            chattingToon.nametag.setChatCallback(PythonCallbackObject(_spoke))
            chattingToon.nametag.setChatCallbackId(chattingToon.doId)

        if 1 in checks:
            if base.config.GetBool('tmdcc-headcheck', 1):
                headNodes = toon.findAllMatches('**/__Actor_head')
                if len(headNodes) != 3 or not toon.getGeomNode().isHidden() and filter(lambda x: x.isHidden(), headNodes):
                    sendT(msgHeader, 'missing head node', toon)
                    result = toon
                    if base.config.GetBool('tmdcc-chatcheck', 1):
                        trackChat(toon)
            else:
                checks.append(2)
        if 2 in checks:
            if base.config.GetBool('tmdcc-handcheck', 1):
                if not toon.getGeomNode().isHidden():
                    handNodes = toon.findAllMatches('**/hands')
                    for currHandNode in handNodes:
                        if currHandNode.hasColor() and currHandNode.getColor() != VBase4(1, 1, 1, 1):
                            sendT(msgHeader, 'invalid hand color: %s' % currHandNode.getColor(), toon)
                            result = toon
                            break

            else:
                checks.append(3)
        if 3 in checks:
            if base.config.GetBool('tmdcc-namecheck', 1):
                nameNode = toon.find('**/nametag3d')
                if not nameNode or nameNode.isHidden() and not toon.getGeomNode().isHidden() and toon.ghostMode == 0:
                    sendT(msgHeader, 'missing nametag for name: %s' % toon.getName(), toon)
                    result = toon
            else:
                checks.append(4)
        if 4 in checks:
            if base.config.GetBool('tmdcc-animcheck', 1):
                if toon.zoneId in [ToontownGlobals.DonaldsDock,
                 ToontownGlobals.OutdoorZone,
                 ToontownGlobals.ToontownCentral,
                 ToontownGlobals.TheBrrrgh,
                 ToontownGlobals.MinniesMelodyland,
                 ToontownGlobals.DaisyGardens,
                 ToontownGlobals.FunnyFarm,
                 ToontownGlobals.GoofySpeedway,
                 ToontownGlobals.DonaldsDreamland]:
                    currAnim = toon.animFSM.getCurrentState().getName()
                    if currAnim != None and currAnim not in ['neutral',
                     'Happy',
                     'off',
                     'Sad',
                     'TeleportIn',
                     'jumpAirborne',
                     'CloseBook',
                     'run',
                     'OpenBook',
                     'TeleportOut',
                     'TeleportedOut',
                     'ReadBook',
                     'walk',
                     'Sit',
                     'jumpLand',
                     'Sleep',
                     'cringe',
                     'jumpSquat',
                     'Died']:
                        sendT(msgHeader, 'invalid animation playing: %s' % currAnim, toon)
                        result = toon
            else:
                checks.append(5)
        if 5 in checks:
            if base.config.GetBool('tmdcc-cogsuit', 1):
                if toon.zoneId in [ToontownGlobals.DonaldsDock,
                 ToontownGlobals.OutdoorZone,
                 ToontownGlobals.ToontownCentral,
                 ToontownGlobals.TheBrrrgh,
                 ToontownGlobals.MinniesMelodyland,
                 ToontownGlobals.DaisyGardens,
                 ToontownGlobals.FunnyFarm,
                 ToontownGlobals.GoofySpeedway,
                 ToontownGlobals.DonaldsDreamland]:
                    if toon.isDisguised:
                        sendT(msgHeader, 'toon %s is in a cog suit' % toon.getName(), toon)
                        result = toon
            else:
                checks.append(6)
        if 6 in checks:
            if base.config.GetBool('tmdcc-colorcheck', 1):
                torsoPieces = toon.getPieces(('torso', ('arms', 'neck')))
                legPieces = toon.getPieces(('legs', ('legs', 'feet')))
                headPieces = toon.getPieces(('head', '*head*'))
                if (filter(lambda x: x.hasColor() and x.getColor() not in ToonDNA.allowedColors,
                           torsoPieces) or
                filter(lambda x: x.hasColor() and x.getColor() not in ToonDNA.allowedColors,
                       legPieces) or
                filter(lambda x: x.hasColor() and x.getColor() not in ToonDNA.allowedColors,
                       headPieces)) and toon.cheesyEffect == ToontownGlobals.CENormal:
                    torsoColors = str(map(lambda x: not x.hasColor() and 'clear' or x.getColor() in ToonDNA.allowedColors and 'ok' or x.getColor(), torsoPieces))
                    legColors = str(map(lambda x: not x.hasColor() and 'clear' or x.getColor() in ToonDNA.allowedColors and 'ok' or x.getColor(), legPieces))
                    headColors = str(map(lambda x: not x.hasColor() and 'clear' or x.getColor() in ToonDNA.allowedColors and 'ok' or x.getColor(), headPieces))
                    sendT(msgHeader, 'invalid color...arm: %s leg: %s head: %s' % (torsoColors, legColors, headColors), toon)
                    result = toon
            else:
                checks.append(7)
        endTime = globalClock.getRealTime()
        return result

    def startHackObservation(self):
        taskMgr.doMethodLater(AV_TOUCH_CHECK_DELAY_CL, self.toonPosCheck, self.uniqueName('toonPosCheck'))
        taskMgr.doMethodLater(config.GetDouble('tmdcc-delay', 5.0), self.tmdcc, self.uniqueName('tmdcc'))
        if __dev__ and base.config.GetBool('tmdcc-keys', 0):
            from toontown.testenv import safezoneAutoVisit
            safezoneAutoVisit.setupKeys()
            from toontown.testenv import watchDistObj
            watchDistObj.watchObj.setupKeys()

    def stopHackObservation(self):
        taskMgr.remove(self.uniqueName('toonPosCheck'))
        taskMgr.remove(self.uniqueName('tmdcc'))

    def disable(self):
        self.stopHackObservation()
        self.laffMeter.destroy()
        del self.laffMeter
        self.questMap.destroy()
        self.questMap = None
        if hasattr(self, 'purchaseButton'):
            self.purchaseButton.destroy()
            del self.purchaseButton
        self.newsButtonMgr.request('Off')
        base.whiteList.unload()
        self.book.unload()
        del self.optionsPage
        del self.shardPage
        del self.mapPage
        del self.invPage
        del self.questPage
        del self.suitPage
        del self.sosPage
        del self.disguisePage
        del self.fishPage
        del self.gardenPage
        del self.trackPage
        del self.book
        if base.wantKarts:
            if hasattr(self, 'kartPage'):
                del self.kartPage
        if base.wantNametags:
            self.nametag.unmanage(base.marginManager)
        taskMgr.removeTasksMatching('*ioorrd234*')
        self.ignoreAll()
        DistributedToon.DistributedToon.disable(self)
        return

    def disableBodyCollisions(self):
        pass

    def delete(self):
        try:
            self.LocalToon_deleted
        except:
            self.LocalToon_deleted = 1
            Toon.unloadDialog()
            QuestParser.clear()
            DistributedToon.DistributedToon.delete(self)
            LocalAvatar.LocalAvatar.delete(self)
            self.bFriendsList.destroy()
            del self.bFriendsList
            if self.__pieButton:
                self.__pieButton.destroy()
                self.__pieButton = None
            if self.__piePowerMeter:
                self.__piePowerMeter.destroy()
                self.__piePowerMeter = None
            taskMgr.remove('unlockGardenButtons')
            taskMgr.remove('lerpFurnitureButton')
            if self.__furnitureGui:
                self.__furnitureGui.destroy()
            del self.__furnitureGui
            if self.__gardeningGui:
                self.__gardeningGui.destroy()
            del self.__gardeningGui
            if self.__gardeningGuiFake:
                self.__gardeningGuiFake.destroy()
            del self.__gardeningGuiFake
            if self.__clarabelleButton:
                self.__clarabelleButton.destroy()
            del self.__clarabelleButton
            if self.__clarabelleFlash:
                self.__clarabelleFlash.finish()
            del self.__clarabelleFlash
            if self.__catalogNotifyDialog:
                self.__catalogNotifyDialog.cleanup()
            del self.__catalogNotifyDialog

        return

    def initInterface(self):
        self.newsButtonMgr = NewsPageButtonManager.NewsPageButtonManager()
        self.newsButtonMgr.request('Hidden')
        self.book = ShtikerBook.ShtikerBook('bookDone')
        self.book.load()
        self.book.hideButton()
        self.optionsPage = OptionsPage.OptionsPage()
        self.optionsPage.load()
        self.book.addPage(self.optionsPage, pageName=TTLocalizer.OptionsPageTitle)
        self.shardPage = ShardPage.ShardPage()
        self.shardPage.load()
        self.book.addPage(self.shardPage, pageName=TTLocalizer.ShardPageTitle)
        self.mapPage = MapPage.MapPage()
        self.mapPage.load()
        self.book.addPage(self.mapPage, pageName=TTLocalizer.MapPageTitle)
        self.invPage = InventoryPage.InventoryPage()
        self.invPage.load()
        self.book.addPage(self.invPage, pageName=TTLocalizer.InventoryPageTitle)
        self.questPage = QuestPage.QuestPage()
        self.questPage.load()
        self.book.addPage(self.questPage, pageName=TTLocalizer.QuestPageToonTasks)
        self.trackPage = TrackPage.TrackPage()
        self.trackPage.load()
        self.book.addPage(self.trackPage, pageName=TTLocalizer.TrackPageShortTitle)
        self.suitPage = SuitPage.SuitPage()
        self.suitPage.load()
        self.book.addPage(self.suitPage, pageName=TTLocalizer.SuitPageTitle)
        if base.config.GetBool('want-photo-album', 0):
            self.photoAlbumPage = PhotoAlbumPage.PhotoAlbumPage()
            self.photoAlbumPage.load()
            self.book.addPage(self.photoAlbumPage, pageName=TTLocalizer.PhotoPageTitle)
        self.fishPage = FishPage.FishPage()
        self.fishPage.setAvatar(self)
        self.fishPage.load()
        self.book.addPage(self.fishPage, pageName=TTLocalizer.FishPageTitle)
        if base.wantKarts:
            self.addKartPage()
        if self.disguisePageFlag:
            self.loadDisguisePages()
        if self.sosPageFlag:
            self.loadSosPages()
        if self.gardenStarted:
            self.loadGardenPages()
        self.addGolfPage()
        self.addEventsPage()
        if WantNewsPage:
            self.addNewsPage()
        self.book.setPage(self.mapPage, enterPage=False)
        self.laffMeter = LaffMeter.LaffMeter(self.style, self.hp, self.maxHp)
        self.laffMeter.setAvatar(self)
        self.laffMeter.setScale(0.075)
        if self.style.getAnimal() == 'monkey':
            self.laffMeter.setPos(-1.18, 0.0, -0.87)
        else:
            self.laffMeter.setPos(-1.2, 0.0, -0.87)
        self.laffMeter.stop()
        self.questMap = QuestMap.QuestMap(self)
        self.questMap.stop()
        if not base.cr.isPaid():
            guiButton = loader.loadModel('phase_3/models/gui/quit_button')
            self.purchaseButton = DirectButton(parent=aspect2d, relief=None, image=(guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR')), image_scale=0.9, text=TTLocalizer.OptionsPagePurchase, text_scale=0.05, text_pos=(0, -0.01), textMayChange=0, pos=(0.885, 0, -0.94), sortOrder=100, command=self.__handlePurchase)
            base.setCellsAvailable([base.bottomCells[4]], 0)
        self.accept('time-insert', self.__beginTossPie)
        self.accept('time-insert-up', self.__endTossPie)
        self.accept('time-delete', self.__beginTossPie)
        self.accept('time-delete-up', self.__endTossPie)
        self.accept('pieHit', self.__pieHit)
        self.accept('interrupt-pie', self.interruptPie)
        self.accept('InputState-jump', self.__toonMoved)
        self.accept('InputState-forward', self.__toonMoved)
        self.accept('InputState-reverse', self.__toonMoved)
        self.accept('InputState-turnLeft', self.__toonMoved)
        self.accept('InputState-turnRight', self.__toonMoved)
        self.accept('InputState-slide', self.__toonMoved)
        QuestParser.init()
        return

    def __handlePurchase(self):
        self.purchaseButton.hide()
        if (base.cr.isWebPlayToken() or __dev__):
            if base.cr.isPaid():
                if base.cr.productName in ['DisneyOnline-UK', 'DisneyOnline-AP', 'JP', 'DE', 'BR', 'FR']:
                    paidNoParentPassword = launcher and launcher.getParentPasswordSet()
                else:
                    paidNoParentPassword = launcher and not launcher.getParentPasswordSet()
            else:
                paidNoParentPassword = 0
            self.leaveToPayDialog = LeaveToPayDialog.LeaveToPayDialog(paidNoParentPassword, self.purchaseButton.show)
            self.leaveToPayDialog.show()
        else:
            self.notify.error('You should not get here without a PlayToken')

    if base.wantKarts:

        def addKartPage(self):
            if self.hasKart():
                if hasattr(self, 'kartPage') and self.kartPage != None:
                    return
                if not launcher.getPhaseComplete(6):
                    self.acceptOnce('phaseComplete-6', self.addKartPage)
                    return
                self.kartPage = KartPage.KartPage()
                self.kartPage.setAvatar(self)
                self.kartPage.load()
                self.book.addPage(self.kartPage, pageName=TTLocalizer.KartPageTitle)
            return

    def setWantBattles(self, wantBattles):
        self.wantBattles = wantBattles

    def loadDisguisePages(self):
        if self.disguisePage != None:
            return
        if not launcher.getPhaseComplete(9):
            self.acceptOnce('phaseComplete-9', self.loadDisguisePages)
            return
        self.disguisePage = DisguisePage.DisguisePage()
        self.disguisePage.load()
        self.book.addPage(self.disguisePage, pageName=TTLocalizer.DisguisePageTitle)
        self.loadSosPages()
        return

    def loadSosPages(self):
        if self.sosPage != None:
            return
        self.sosPage = NPCFriendPage.NPCFriendPage()
        self.sosPage.load()
        self.book.addPage(self.sosPage, pageName=TTLocalizer.NPCFriendPageTitle)
        return

    def loadGardenPages(self):
        if self.gardenPage != None:
            return
        if not launcher.getPhaseComplete(5.5):
            self.acceptOnce('phaseComplete-5.5', self.loadPhase55Stuff)
            return
        self.gardenPage = GardenPage.GardenPage()
        self.gardenPage.load()
        self.book.addPage(self.gardenPage, pageName=TTLocalizer.GardenPageTitle)
        return

    def loadPhase55Stuff(self):
        if self.gardenPage == None:
            self.gardenPage = GardenPage.GardenPage()
            self.gardenPage.load()
            self.book.addPage(self.gardenPage, pageName=TTLocalizer.GardenPageTitle)
        elif not launcher.getPhaseComplete(5.5):
            self.acceptOnce('phaseComplete-5.5', self.loadPhase55Stuff)
        self.refreshOnscreenButtons()
        return

    def setAsGM(self, state):
        self.notify.debug('Setting GM State: %s in LocalToon' % state)
        DistributedToon.DistributedToon.setAsGM(self, state)
        if self.gmState:
            if base.config.GetString('gm-nametag-string', '') != '':
                self.gmNameTagString = base.config.GetString('gm-nametag-string')
            if base.config.GetString('gm-nametag-color', '') != '':
                self.gmNameTagColor = base.config.GetString('gm-nametag-color')
            if base.config.GetInt('gm-nametag-enabled', 0):
                self.gmNameTagEnabled = 1
            self.d_updateGMNameTag()

    def displayTalkWhisper(self, fromId, avatarName, rawString, mods):
        sender = base.cr.identifyAvatar(fromId)
        if sender:
            chatString, scrubbed = sender.scrubTalk(rawString, mods)
        else:
            chatString, scrubbed = self.scrubTalk(rawString, mods)
        sender = self
        sfx = self.soundWhisper
        chatString = avatarName + ': ' + chatString
        whisper = WhisperPopup(chatString, OTPGlobals.getInterfaceFont(), WhisperPopup.WTNormal)
        whisper.setClickable(avatarName, fromId)
        whisper.manage(base.marginManager)
        base.playSfx(sfx)

    def displayTalkAccount(self, fromId, senderName, rawString, mods):
        sender = None
        playerInfo = None
        sfx = self.soundWhisper
        playerInfo = base.cr.playerFriendsManager.playerId2Info.get(fromId, None)
        if playerInfo == None:
            return
        senderAvId = base.cr.playerFriendsManager.findAvIdFromPlayerId(fromId)
        if not senderName and base.cr.playerFriendsManager.playerId2Info.get(fromId):
            senderName = base.cr.playerFriendsManager.playerId2Info.get(fromId).playerName
        senderAvatar = base.cr.identifyAvatar(senderAvId)
        if sender:
            chatString, scrubbed = senderAvatar.scrubTalk(rawString, mods)
        else:
            chatString, scrubbed = self.scrubTalk(rawString, mods)
        chatString = senderName + ': ' + chatString
        whisper = WhisperPopup(chatString, OTPGlobals.getInterfaceFont(), WhisperPopup.WTNormal)
        if playerInfo != None:
            whisper.setClickable(senderName, fromId, 1)
        whisper.manage(base.marginManager)
        base.playSfx(sfx)
        return

    def isLocal(self):
        return 1

    def canChat(self):
        if not self.cr.allowAnyTypedChat():
            return 0
        if self.commonChatFlags & (ToontownGlobals.CommonChat | ToontownGlobals.SuperChat):
            return 1
        if base.cr.whiteListChatEnabled:
            return 1
        for friendId, flags in self.friendsList:
            if flags & ToontownGlobals.FriendChat:
                return 1

        return 0

    def startChat(self):
        if self.tutorialAck:
            self.notify.info('calling LocalAvatar.startchat')
            LocalAvatar.LocalAvatar.startChat(self)
            self.accept('chatUpdateSCToontask', self.b_setSCToontask)
            self.accept('chatUpdateSCResistance', self.d_reqSCResistance)
            self.accept('chatUpdateSCSinging', self.b_setSCSinging)
            self.accept('whisperUpdateSCToontask', self.whisperSCToontaskTo)
        else:
            self.notify.info('NOT calling LocalAvatar.startchat, in tutorial')

    def stopChat(self):
        LocalAvatar.LocalAvatar.stopChat(self)
        self.ignore('chatUpdateSCToontask')
        self.ignore('chatUpdateSCResistance')
        self.ignore('chatUpdateSCSinging')
        self.ignore('whisperUpdateSCToontask')

    def tunnelIn(self, tunnelOrigin):
        self.b_setTunnelIn(self.tunnelX * 0.8, tunnelOrigin)

    def tunnelOut(self, tunnelOrigin):
        self.tunnelX = self.getX(tunnelOrigin)
        tunnelY = self.getY(tunnelOrigin)
        self.b_setTunnelOut(self.tunnelX * 0.95, tunnelY, tunnelOrigin)

    def handleTunnelIn(self, startTime, endX, x, y, z, h):
        self.notify.debug('LocalToon.handleTunnelIn')
        tunnelOrigin = render.attachNewNode('tunnelOrigin')
        tunnelOrigin.setPosHpr(x, y, z, h, 0, 0)
        self.b_setAnimState('run', self.animMultiplier)
        self.stopLookAround()
        self.reparentTo(render)
        self.runSound()
        camera.reparentTo(render)
        camera.setPosHpr(tunnelOrigin, 0, 20, 12, 180, -20, 0)
        base.transitions.irisIn(0.4)
        toonTrack = self.getTunnelInToonTrack(endX, tunnelOrigin)

        def cleanup(self = self, tunnelOrigin = tunnelOrigin):
            self.stopSound()
            tunnelOrigin.removeNode()
            messenger.send('tunnelInMovieDone')

        self.tunnelTrack = Sequence(toonTrack, Func(cleanup))
        self.tunnelTrack.start(globalClock.getFrameTime() - startTime)

    def handleTunnelOut(self, startTime, startX, startY, x, y, z, h):
        self.notify.debug('LocalToon.handleTunnelOut')
        tunnelOrigin = render.attachNewNode('tunnelOrigin')
        tunnelOrigin.setPosHpr(x, y, z, h, 0, 0)
        self.b_setAnimState('run', self.animMultiplier)
        self.runSound()
        self.stopLookAround()
        tracks = Parallel()
        camera.wrtReparentTo(render)
        startPos = camera.getPos(tunnelOrigin)
        startHpr = camera.getHpr(tunnelOrigin)
        camLerpDur = 1.0
        reducedCamH = fitDestAngle2Src(startHpr[0], 180)
        tracks.append(LerpPosHprInterval(camera, camLerpDur, pos=Point3(0, 20, 12), hpr=Point3(reducedCamH, -20, 0), startPos=startPos, startHpr=startHpr, other=tunnelOrigin, blendType='easeInOut', name='tunnelOutLerpCamPos'))
        toonTrack = self.getTunnelOutToonTrack(startX, startY, tunnelOrigin)
        tracks.append(toonTrack)
        irisDur = 0.4
        tracks.append(Sequence(Wait(toonTrack.getDuration() - (irisDur + 0.1)), Func(base.transitions.irisOut, irisDur)))

        def cleanup(self = self, tunnelOrigin = tunnelOrigin):
            self.stopSound()
            self.detachNode()
            tunnelOrigin.removeNode()
            messenger.send('tunnelOutMovieDone')

        self.tunnelTrack = Sequence(tracks, Func(cleanup))
        self.tunnelTrack.start(globalClock.getFrameTime() - startTime)

    def getPieBubble(self):
        if self.__pieBubble == None:
            bubble = CollisionSphere(0, 0, 0, 1)
            node = CollisionNode('pieBubble')
            node.addSolid(bubble)
            node.setFromCollideMask(ToontownGlobals.PieBitmask | ToontownGlobals.CameraBitmask | ToontownGlobals.FloorBitmask)
            node.setIntoCollideMask(BitMask32.allOff())
            self.__pieBubble = NodePath(node)
            self.pieHandler = CollisionHandlerEvent()
            self.pieHandler.addInPattern('pieHit')
            self.pieHandler.addInPattern('pieHit-%in')
        return self.__pieBubble

    def __beginTossPieMouse(self, mouseParam):
        self.__beginTossPie(globalClock.getFrameTime())

    def __endTossPieMouse(self, mouseParam):
        self.__endTossPie(globalClock.getFrameTime())

    def __beginTossPie(self, time):
        if self.tossPieStart != None:
            return
        if not self.allowPies:
            return
        if self.numPies == 0:
            messenger.send('outOfPies')
            return
        if self.__pieInHand():
            return
        if getattr(self.controlManager.currentControls, 'isAirborne', 0):
            return
        messenger.send('wakeup')
        self.localPresentPie(time)
        taskName = self.uniqueName('updatePiePower')
        taskMgr.add(self.__updatePiePower, taskName)
        return

    def __endTossPie(self, time):
        if self.tossPieStart == None:
            return
        taskName = self.uniqueName('updatePiePower')
        taskMgr.remove(taskName)
        messenger.send('wakeup')
        power = self.__getPiePower(time)
        self.tossPieStart = None
        self.localTossPie(power)
        return

    def localPresentPie(self, time):
        import TTEmote
        from otp.avatar import Emote
        self.__stopPresentPie()
        if self.tossTrack:
            tossTrack = self.tossTrack
            self.tossTrack = None
            tossTrack.finish()
        self.interruptPie()
        self.tossPieStart = time
        self.__pieSequence = self.__pieSequence + 1 & 255
        sequence = self.__pieSequence
        self.__presentingPie = 1
        pos = self.getPos()
        hpr = self.getHpr()
        timestamp32 = globalClockDelta.getFrameNetworkTime(bits=32)
        self.sendUpdate('presentPie', [pos[0],
         pos[1],
         pos[2],
         hpr[0] % 360.0,
         hpr[1],
         hpr[2],
         timestamp32])
        Emote.globalEmote.disableBody(self)
        messenger.send('begin-pie')
        ival = self.getPresentPieInterval(pos[0], pos[1], pos[2], hpr[0], hpr[1], hpr[2])
        ival = Sequence(ival, name=self.uniqueName('localPresentPie'))
        self.tossTrack = ival
        ival.start()
        self.makePiePowerMeter()
        self.__piePowerMeter.show()
        self.__piePowerMeterSequence = sequence
        self.__piePowerMeter['value'] = 0
        return

    def __stopPresentPie(self):
        if self.__presentingPie:
            import TTEmote
            from otp.avatar import Emote
            Emote.globalEmote.releaseBody(self)
            messenger.send('end-pie')
            self.__presentingPie = 0
        taskName = self.uniqueName('updatePiePower')
        taskMgr.remove(taskName)

    def __getPiePower(self, time):
        elapsed = max(time - self.tossPieStart, 0.0)
        t = elapsed / self.piePowerSpeed
        t = math.pow(t, self.piePowerExponent)
        power = int(t * 100) % 200
        if power > 100:
            power = 200 - power
        return power

    def __updatePiePower(self, task):
        if not self.__piePowerMeter:
            return Task.done
        self.__piePowerMeter['value'] = self.__getPiePower(globalClock.getFrameTime())
        return Task.cont

    def interruptPie(self):
        self.cleanupPieInHand()
        self.__stopPresentPie()
        if self.__piePowerMeter:
            self.__piePowerMeter.hide()
        pie = self.pieTracks.get(self.__pieSequence)
        if pie and pie.getT() < 14.0 / 24.0:
            del self.pieTracks[self.__pieSequence]
            pie.pause()

    def __pieInHand(self):
        pie = self.pieTracks.get(self.__pieSequence)
        return pie and pie.getT() < 15.0 / 24.0

    def __toonMoved(self, isSet):
        if isSet:
            self.interruptPie()

    def localTossPie(self, power):
        if not self.__presentingPie:
            return
        pos = self.getPos()
        hpr = self.getHpr()
        timestamp32 = globalClockDelta.getFrameNetworkTime(bits=32)
        sequence = self.__pieSequence
        if self.tossTrack:
            tossTrack = self.tossTrack
            self.tossTrack = None
            tossTrack.finish()
        if self.pieTracks.has_key(sequence):
            pieTrack = self.pieTracks[sequence]
            del self.pieTracks[sequence]
            pieTrack.finish()
        if self.splatTracks.has_key(sequence):
            splatTrack = self.splatTracks[sequence]
            del self.splatTracks[sequence]
            splatTrack.finish()
        self.makePiePowerMeter()
        self.__piePowerMeter['value'] = power
        self.__piePowerMeter.show()
        self.__piePowerMeterSequence = sequence
        pieBubble = self.getPieBubble().instanceTo(NodePath())

        def pieFlies(self = self, pos = pos, hpr = hpr, sequence = sequence, power = power, timestamp32 = timestamp32, pieBubble = pieBubble):
            self.sendUpdate('tossPie', [pos[0],
             pos[1],
             pos[2],
             hpr[0] % 360.0,
             hpr[1],
             hpr[2],
             sequence,
             power,
             timestamp32])
            if self.numPies != ToontownGlobals.FullPies:
                self.setNumPies(self.numPies - 1)
            base.cTrav.addCollider(pieBubble, self.pieHandler)

        toss, pie, flyPie = self.getTossPieInterval(pos[0], pos[1], pos[2], hpr[0], hpr[1], hpr[2], power, beginFlyIval=Func(pieFlies))
        pieBubble.reparentTo(flyPie)
        flyPie.setTag('pieSequence', str(sequence))
        toss = Sequence(toss)
        self.tossTrack = toss
        toss.start()
        pie = Sequence(pie, Func(base.cTrav.removeCollider, pieBubble), Func(self.pieFinishedFlying, sequence))
        self.pieTracks[sequence] = pie
        pie.start()
        return

    def pieFinishedFlying(self, sequence):
        DistributedToon.DistributedToon.pieFinishedFlying(self, sequence)
        if self.__piePowerMeterSequence == sequence:
            self.__piePowerMeter.hide()

    def __finishPieTrack(self, sequence):
        if self.pieTracks.has_key(sequence):
            pieTrack = self.pieTracks[sequence]
            del self.pieTracks[sequence]
            pieTrack.finish()

    def __pieHit(self, entry):
        if not entry.hasSurfacePoint() or not entry.hasInto():
            return
        if not entry.getInto().isTangible():
            return
        sequence = int(entry.getFromNodePath().getNetTag('pieSequence'))
        self.__finishPieTrack(sequence)
        if self.splatTracks.has_key(sequence):
            splatTrack = self.splatTracks[sequence]
            del self.splatTracks[sequence]
            splatTrack.finish()
        pieCode = 0
        pieCodeStr = entry.getIntoNodePath().getNetTag('pieCode')
        if pieCodeStr:
            pieCode = int(pieCodeStr)
        pos = entry.getSurfacePoint(render)
        timestamp32 = globalClockDelta.getFrameNetworkTime(bits=32)
        self.sendUpdate('pieSplat', [pos[0],
         pos[1],
         pos[2],
         sequence,
         pieCode,
         timestamp32])
        splat = self.getPieSplatInterval(pos[0], pos[1], pos[2], pieCode)
        splat = Sequence(splat, Func(self.pieFinishedSplatting, sequence))
        self.splatTracks[sequence] = splat
        splat.start()
        messenger.send('pieSplat', [self, pieCode])
        messenger.send('localPieSplat', [pieCode, entry])

    def beginAllowPies(self):
        self.allowPies = 1
        self.updatePieButton()

    def endAllowPies(self):
        self.allowPies = 0
        self.updatePieButton()

    def makePiePowerMeter(self):
        from direct.gui.DirectGui import DirectWaitBar, DGG
        if self.__piePowerMeter == None:
            self.__piePowerMeter = DirectWaitBar(frameSize=(-0.2,
             0.2,
             -0.03,
             0.03), relief=DGG.SUNKEN, borderWidth=(0.005, 0.005), barColor=(0.4, 0.6, 1.0, 1), pos=(0, 0.1, 0.8))
            self.__piePowerMeter.hide()
        return

    def updatePieButton(self):
        from toontown.toonbase import ToontownBattleGlobals
        from direct.gui.DirectGui import DirectButton, DGG
        wantButton = 0
        if self.allowPies and self.numPies > 0:
            wantButton = 1
        if not launcher.getPhaseComplete(5):
            wantButton = 0
        haveButton = self.__pieButton != None
        if not haveButton and not wantButton:
            return
        if haveButton and not wantButton:
            self.__pieButton.destroy()
            self.__pieButton = None
            self.__pieButtonType = None
            self.__pieButtonCount = None
            return
        if self.__pieButtonType != self.pieType:
            if self.__pieButton:
                self.__pieButton.destroy()
                self.__pieButton = None
        if self.__pieButton == None:
            inv = self.inventory
            if self.pieType >= len(inv.invModels[ToontownBattleGlobals.THROW_TRACK]):
                gui = loader.loadModel('phase_3.5/models/gui/stickerbook_gui')
                pieGui = gui.find('**/summons')
                pieScale = 0.1
            else:
                gui = None
                pieGui = (inv.invModels[ToontownBattleGlobals.THROW_TRACK][self.pieType],)
                pieScale = 0.85
            self.__pieButton = DirectButton(image=(inv.upButton, inv.downButton, inv.rolloverButton), geom=pieGui, text='50', text_scale=0.04, text_align=TextNode.ARight, geom_scale=pieScale, geom_pos=(-0.01, 0, 0), text_fg=Vec4(1, 1, 1, 1), text_pos=(0.07, -0.04), relief=None, image_color=(0, 0.6, 1, 1), pos=(0, 0.1, 0.9))
            self.__pieButton.bind(DGG.B1PRESS, self.__beginTossPieMouse)
            self.__pieButton.bind(DGG.B1RELEASE, self.__endTossPieMouse)
            self.__pieButtonType = self.pieType
            self.__pieButtonCount = None
            if gui:
                del gui
        if self.__pieButtonCount != self.numPies:
            if self.numPies == ToontownGlobals.FullPies:
                self.__pieButton['text'] = ''
            else:
                self.__pieButton['text'] = str(self.numPies)
            self.__pieButtonCount = self.numPies
        return

    def displayWhisper(self, fromId, chatString, whisperType):
        sender = None
        sfx = self.soundWhisper
        if fromId == TTLocalizer.Clarabelle:
            chatString = TTLocalizer.Clarabelle + ': ' + chatString
            sfx = self.soundPhoneRing
        elif fromId != 0:
            sender = base.cr.identifyAvatar(fromId)
        if whisperType == WhisperPopup.WTNormal or whisperType == WhisperPopup.WTQuickTalker:
            if sender == None:
                return
            chatString = sender.getName() + ': ' + chatString
        elif whisperType == WhisperPopup.WTSystem:
            sfx = self.soundSystemMessage
        whisper = WhisperPopup(chatString, OTPGlobals.getInterfaceFont(), whisperType)
        if sender != None:
            whisper.setClickable(sender.getName(), fromId)
        whisper.manage(base.marginManager)
        base.playSfx(sfx)
        return

    def displaySystemClickableWhisper(self, fromId, chatString, whisperType):
        sender = None
        sfx = self.soundWhisper
        if fromId == TTLocalizer.Clarabelle:
            chatString = TTLocalizer.Clarabelle + ': ' + chatString
            sfx = self.soundPhoneRing
        elif fromId != 0:
            sender = base.cr.identifyAvatar(fromId)
        if whisperType == WhisperPopup.WTNormal or whisperType == WhisperPopup.WTQuickTalker:
            if sender == None:
                return
            chatString = sender.getName() + ': ' + chatString
        elif whisperType == WhisperPopup.WTSystem:
            sfx = self.soundSystemMessage
        whisper = WhisperPopup(chatString, OTPGlobals.getInterfaceFont(), whisperType)
        whisper.setClickable('', fromId)
        whisper.manage(base.marginManager)
        base.playSfx(sfx)
        return

    def clickedWhisper(self, doId, isPlayer = None):
        if doId > 0:
            LocalAvatar.LocalAvatar.clickedWhisper(self, doId, isPlayer)
        else:
            foundCanStart = False
            for partyInfo in self.hostedParties:
                if partyInfo.status == PartyGlobals.PartyStatus.CanStart:
                    foundCanStart = True
                    break

            if base.cr and base.cr.playGame and base.cr.playGame.getPlace() and base.cr.playGame.getPlace().fsm:
                fsm = base.cr.playGame.getPlace().fsm
                curState = fsm.getCurrentState().getName()
                if curState == 'walk':
                    if hasattr(self, 'eventsPage'):
                        desiredMode = -1
                        if doId == -1:
                            desiredMode = EventsPage.EventsPage_Invited
                        elif foundCanStart:
                            desiredMode = EventsPage.EventsPage_Host
                        if desiredMode >= 0:
                            self.book.setPage(self.eventsPage)
                            self.eventsPage.setMode(desiredMode)
                            fsm.request('stickerBook')

    def loadFurnitureGui(self):
        if self.__furnitureGui:
            return
        guiModels = loader.loadModel('phase_5.5/models/gui/house_design_gui')
        self.__furnitureGui = DirectFrame(relief=None, pos=(-1.19, 0.0, 0.33), scale=0.04, image=guiModels.find('**/attic'))
        DirectLabel(parent=self.__furnitureGui, relief=None, image=guiModels.find('**/rooftile'))
        bMoveStartUp = guiModels.find('**/bu_attic/bu_attic_up')
        bMoveStartDown = guiModels.find('**/bu_attic/bu_attic_down')
        bMoveStartRollover = guiModels.find('**/bu_attic/bu_attic_rollover')
        DirectButton(parent=self.__furnitureGui, relief=None, image=[bMoveStartUp,
         bMoveStartDown,
         bMoveStartRollover,
         bMoveStartUp], text=['', TTLocalizer.HDMoveFurnitureButton, TTLocalizer.HDMoveFurnitureButton], text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1), text_font=ToontownGlobals.getInterfaceFont(), pos=(-0.3, 0, 9.4), command=self.__startMoveFurniture)
        self.__furnitureGui.hide()
        guiModels.removeNode()
        return

    def showFurnitureGui(self):
        self.loadFurnitureGui()
        self.__furnitureGui.show()

    def hideFurnitureGui(self):
        if self.__furnitureGui:
            self.__furnitureGui.hide()

    def clarabelleNewsPageCollision(self, show = True):
        if self.__clarabelleButton == None:
            return
        claraXPos = ClaraBaseXPos
        notifyXPos = CatalogNotifyDialog.CatalogNotifyBaseXPos
        if show:
            claraXPos += AdjustmentForNewsButton
            notifyXPos += AdjustmentForNewsButton
        newPos = (claraXPos - 0.1, 1.0, 0.45)
        self.__clarabelleButton.setPos(newPos)
        if self.__catalogNotifyDialog == None or self.__catalogNotifyDialog.frame == None:
            return
        notifyPos = self.__catalogNotifyDialog.frame.getPos()
        notifyPos[0] = notifyXPos
        self.__catalogNotifyDialog.frame.setPos(notifyPos)
        return

    def loadClarabelleGui(self):
        if self.__clarabelleButton:
            return
        guiItems = loader.loadModel('phase_5.5/models/gui/catalog_gui')
        circle = guiItems.find('**/cover/blue_circle')
        icon = guiItems.find('**/cover/clarabelle')
        icon.reparentTo(circle)
        rgba = VBase4(0.71589, 0.784547, 0.974, 1.0)
        white = VBase4(1.0, 1.0, 1.0, 1.0)
        icon.setColor(white)
        claraXPos = ClaraBaseXPos
        newScale = oldScale = 0.5
        newPos = (claraXPos, 1.0, 0.37)
        if WantNewsPage:
            claraXPos += AdjustmentForNewsButton
            oldPos = ((claraXPos, 1.0, 0.37),)
            newScale = oldScale * ToontownGlobals.NewsPageScaleAdjust
            newPos = (claraXPos - 0.1, 1.0, 0.45)
        self.__clarabelleButton = DirectButton(relief=None, image=circle, text='', text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1), text_scale=0.1, text_pos=(-1.06, 1.06), text_font=ToontownGlobals.getInterfaceFont(), pos=newPos, scale=newScale, command=self.__handleClarabelleButton)
        self.__clarabelleButton.reparentTo(aspect2d, DGG.BACKGROUND_SORT_INDEX - 1)
        button = self.__clarabelleButton.stateNodePath[0]
        self.__clarabelleFlash = Sequence(LerpColorInterval(button, 2, white, blendType='easeInOut'), LerpColorInterval(button, 2, rgba, blendType='easeInOut'))
        self.__clarabelleFlash.loop()
        self.__clarabelleFlash.pause()
        return

    def showClarabelleGui(self, mailboxItems):
        self.loadClarabelleGui()
        if mailboxItems:
            self.__clarabelleButton['text'] = ['', TTLocalizer.CatalogNewDeliveryButton, TTLocalizer.CatalogNewDeliveryButton]
        else:
            self.__clarabelleButton['text'] = ['', TTLocalizer.CatalogNewCatalogButton, TTLocalizer.CatalogNewCatalogButton]
        if not self.mailboxNotify and not self.awardNotify and self.catalogNotify == ToontownGlobals.OldItems and (self.simpleMailNotify != ToontownGlobals.NoItems or self.inviteMailNotify != ToontownGlobals.NoItems):
            self.__clarabelleButton['text'] = ['', TTLocalizer.MailNewMailButton, TTLocalizer.MailNewMailButton]
        if self.newsButtonMgr.isNewIssueButtonShown():
            self.clarabelleNewsPageCollision(True)
        self.__clarabelleButton.show()
        self.__clarabelleFlash.resume()

    def hideClarabelleGui(self):
        if self.__clarabelleButton:
            self.__clarabelleButton.hide()
            self.__clarabelleFlash.pause()

    def __handleClarabelleButton(self):
        self.stopMoveFurniture()
        place = base.cr.playGame.getPlace()
        if place == None:
            self.notify.warning('Tried to go home, but place is None.')
            return
        if self.__catalogNotifyDialog:
            self.__catalogNotifyDialog.cleanup()
            self.__catalogNotifyDialog = None
        if base.config.GetBool('want-qa-regression', 0):
            self.notify.info('QA-REGRESSION: VISITESTATE: Visit estate')
        place.goHomeNow(self.lastHood)
        return

    def __startMoveFurniture(self):
        self.oldPos = self.getPos()
        if base.config.GetBool('want-qa-regression', 0):
            self.notify.info('QA-REGRESSION: ESTATE:  Furniture Placement')
        if self.cr.furnitureManager != None:
            self.cr.furnitureManager.d_suggestDirector(self.doId)
        elif self.furnitureManager != None:
            self.furnitureManager.d_suggestDirector(self.doId)
        return

    def stopMoveFurniture(self):
        if self.oldPos:
            self.setPos(self.oldPos)
        if self.furnitureManager != None:
            self.furnitureManager.d_suggestDirector(0)
        return

    def setFurnitureDirector(self, avId, furnitureManager):
        if avId == 0:
            if self.furnitureManager == furnitureManager:
                messenger.send('exitFurnitureMode', [furnitureManager])
                self.furnitureManager = None
                self.furnitureDirector = None
        elif avId != self.doId:
            if self.furnitureManager == None or self.furnitureDirector != avId:
                self.furnitureManager = furnitureManager
                self.furnitureDirector = avId
                messenger.send('enterFurnitureMode', [furnitureManager, 0])
        else:
            if self.furnitureManager != None:
                messenger.send('exitFurnitureMode', [self.furnitureManager])
                self.furnitureManager = None
            self.furnitureManager = furnitureManager
            self.furnitureDirector = avId
            messenger.send('enterFurnitureMode', [furnitureManager, 1])
        self.refreshOnscreenButtons()
        return

    def getAvPosStr(self):
        pos = self.getPos()
        hpr = self.getHpr()
        serverVersion = base.cr.getServerVersion()
        districtName = base.cr.getShardName(base.localAvatar.defaultShard)
        if hasattr(base.cr.playGame.hood, 'loader') and hasattr(base.cr.playGame.hood.loader, 'place') and base.cr.playGame.getPlace() != None:
            zoneId = base.cr.playGame.getPlace().getZoneId()
        else:
            zoneId = '?'
        strPosCoordText = 'X: %.3f' % pos[0] + ', Y: %.3f' % pos[1] + '\nZ: %.3f' % pos[2] + ', H: %.3f' % hpr[0] + '\nZone: %s' % str(zoneId) + ', Ver: %s, ' % serverVersion + 'District: %s' % districtName
        return strPosCoordText
        self.refreshOnscreenButtons()
        return

    def thinkPos(self):
        pos = self.getPos()
        hpr = self.getHpr()
        serverVersion = base.cr.getServerVersion()
        districtName = base.cr.getShardName(base.localAvatar.defaultShard)
        if hasattr(base.cr.playGame.hood, 'loader') and hasattr(base.cr.playGame.hood.loader, 'place') and base.cr.playGame.getPlace() != None:
            zoneId = base.cr.playGame.getPlace().getZoneId()
        else:
            zoneId = '?'
        strPos = '(%.3f' % pos[0] + '\n %.3f' % pos[1] + '\n %.3f)' % pos[2] + '\nH: %.3f' % hpr[0] + '\nZone: %s' % str(zoneId) + ',\nVer: %s, ' % serverVersion + '\nDistrict: %s' % districtName
        print 'Current position=', strPos.replace('\n', ', ')
        self.setChatAbsolute(strPos, CFThought | CFTimeout)
        return

    def __placeMarker(self):
        pos = self.getPos()
        hpr = self.getHpr()
        chest = loader.loadModel('phase_4/models/props/coffin')
        chest.reparentTo(render)
        chest.setColor(1, 0, 0, 1)
        chest.setPosHpr(pos, hpr)
        chest.setScale(0.5)

    def setFriendsListButtonActive(self, active):
        self.friendsListButtonActive = active
        self.refreshOnscreenButtons()

    def obscureFriendsListButton(self, increment):
        self.friendsListButtonObscured += increment
        self.refreshOnscreenButtons()

    def obscureMoveFurnitureButton(self, increment):
        self.moveFurnitureButtonObscured += increment
        self.refreshOnscreenButtons()

    def obscureClarabelleButton(self, increment):
        self.clarabelleButtonObscured += increment
        self.refreshOnscreenButtons()

    def refreshOnscreenButtons(self):
        self.bFriendsList.hide()
        self.hideFurnitureGui()
        self.hideClarabelleGui()
        clarabelleHidden = 1
        self.ignore(ToontownGlobals.FriendsListHotkey)
        if self.friendsListButtonActive and self.friendsListButtonObscured <= 0:
            self.bFriendsList.show()
            self.accept(ToontownGlobals.FriendsListHotkey, self.sendFriendsListEvent)
            if self.clarabelleButtonObscured <= 0 and self.isTeleportAllowed():
                if self.catalogNotify == ToontownGlobals.NewItems or self.mailboxNotify == ToontownGlobals.NewItems or self.simpleMailNotify == ToontownGlobals.NewItems or self.inviteMailNotify == ToontownGlobals.NewItems or self.awardNotify == ToontownGlobals.NewItems:
                    showClarabelle = not launcher or launcher.getPhaseComplete(5.5)
                    for quest in self.quests:
                        if quest[0] in Quests.PreClarabelleQuestIds and self.mailboxNotify != ToontownGlobals.NewItems and self.awardNotify != ToontownGlobals.NewItems:
                            showClarabelle = 0

                    if base.cr.playGame.getPlace().getState() == 'stickerBook':
                        showClarabelle = 0
                    if showClarabelle:
                        newItemsInMailbox = self.mailboxNotify == ToontownGlobals.NewItems or self.awardNotify == ToontownGlobals.NewItems
                        self.showClarabelleGui(newItemsInMailbox)
                        clarabelleHidden = 0
        if clarabelleHidden:
            if self.__catalogNotifyDialog:
                self.__catalogNotifyDialog.cleanup()
                self.__catalogNotifyDialog = None
        else:
            self.newCatalogNotify()
        if self.moveFurnitureButtonObscured <= 0:
            if self.furnitureManager != None and self.furnitureDirector == self.doId:
                self.loadFurnitureGui()
                self.__furnitureGui.setPos(-1.16, 0, -0.03)
                self.__furnitureGui.setScale(0.06)
            elif self.cr.furnitureManager != None:
                self.showFurnitureGui()
                taskMgr.remove('lerpFurnitureButton')
                self.__furnitureGui.lerpPosHprScale(pos=Point3(-1.19, 0.0, 0.33), hpr=Vec3(0.0, 0.0, 0.0), scale=Vec3(0.04, 0.04, 0.04), time=1.0, blendType='easeInOut', task='lerpFurnitureButton')
        if hasattr(self, 'inEstate') and self.inEstate:
            self.loadGardeningGui()
            self.hideGardeningGui()
        else:
            self.hideGardeningGui()
        return

    def setGhostMode(self, flag):
        if flag == 2:
            self.seeGhosts = 1
        DistributedToon.DistributedToon.setGhostMode(self, flag)

    def newCatalogNotify(self):
        if not self.gotCatalogNotify:
            return
        hasPhase = not launcher or launcher.getPhaseComplete(5.5)
        if not hasPhase:
            return
        if not self.friendsListButtonActive or self.friendsListButtonObscured > 0:
            return
        self.gotCatalogNotify = 0
        currentWeek = self.catalogScheduleCurrentWeek - 1
        if currentWeek < 57:
            seriesNumber = currentWeek / ToontownGlobals.CatalogNumWeeksPerSeries + 1
            weekNumber = currentWeek % ToontownGlobals.CatalogNumWeeksPerSeries + 1
        elif currentWeek < 65:
            seriesNumber = 6
            weekNumber = currentWeek - 56
        else:
            seriesNumber = currentWeek / ToontownGlobals.CatalogNumWeeksPerSeries + 2
            weekNumber = currentWeek % ToontownGlobals.CatalogNumWeeksPerSeries + 1
        message = None
        if self.mailboxNotify == ToontownGlobals.NoItems:
            if self.catalogNotify == ToontownGlobals.NewItems:
                if self.catalogScheduleCurrentWeek == 1:
                    message = (TTLocalizer.CatalogNotifyFirstCatalog, TTLocalizer.CatalogNotifyInstructions)
                else:
                    message = (TTLocalizer.CatalogNotifyNewCatalog % weekNumber,)
        elif self.mailboxNotify == ToontownGlobals.NewItems:
            if self.catalogNotify == ToontownGlobals.NewItems:
                message = (TTLocalizer.CatalogNotifyNewCatalogNewDelivery % weekNumber,)
            else:
                message = (TTLocalizer.CatalogNotifyNewDelivery,)
        elif self.mailboxNotify == ToontownGlobals.OldItems:
            if self.catalogNotify == ToontownGlobals.NewItems:
                message = (TTLocalizer.CatalogNotifyNewCatalogOldDelivery % weekNumber,)
            else:
                message = (TTLocalizer.CatalogNotifyOldDelivery,)
        if self.awardNotify == ToontownGlobals.NoItems:
            pass
        elif self.awardNotify == ToontownGlobals.NewItems:
            oldStr = ''
            if message:
                oldStr = message[0] + ' '
            oldStr += TTLocalizer.AwardNotifyNewItems
            message = (oldStr,)
        elif self.awardNotify == ToontownGlobals.OldItems:
            oldStr = ''
            if message:
                oldStr = message[0] + ' '
            oldStr += TTLocalizer.AwardNotifyOldItems
            message = (oldStr,)
        if self.simpleMailNotify == ToontownGlobals.NewItems or self.inviteMailNotify == ToontownGlobals.NewItems:
            oldStr = ''
            if message:
                oldStr = message[0] + ' '
            oldStr += TTLocalizer.MailNotifyNewItems
            message = (oldStr,)
        if message == None:
            return
        if self.__catalogNotifyDialog:
            self.__catalogNotifyDialog.cleanup()
        self.__catalogNotifyDialog = CatalogNotifyDialog.CatalogNotifyDialog(message)
        base.playSfx(self.soundPhoneRing)
        return

    def allowHardLand(self):
        retval = LocalAvatar.LocalAvatar.allowHardLand(self)
        return retval and not self.isDisguised

    def setShovelGuiLevel(self, level = 0):
        pass

    def setWateringCanGuiLevel(self, level = 0):
        pass

    def loadGardeningGui(self):
        if self.__gardeningGui:
            return
        gardenGuiCard = loader.loadModel('phase_5.5/models/gui/planting_gui')
        self.__gardeningGui = DirectFrame(relief=None, geom=gardenGuiCard, geom_color=GlobalDialogColor, geom_scale=(0.17, 1.0, 0.3), pos=(-1.2, 0, 0.5), scale=1.0)
        self.__gardeningGui.setName('gardeningFrame')
        self.__gardeningGuiFake = DirectFrame(relief=None, geom=None, geom_color=GlobalDialogColor, geom_scale=(0.17, 1.0, 0.3), pos=(-1.2, 0, 0.5), scale=1.0)
        self.__gardeningGuiFake.setName('gardeningFrameFake')
        iconScale = 1
        iconColorWhite = Vec4(1.0, 1.0, 1.0, 1.0)
        iconColorGrey = Vec4(0.7, 0.7, 0.7, 1.0)
        iconColorBrown = Vec4(0.7, 0.4, 0.3, 1.0)
        iconColorBlue = Vec4(0.2, 0.3, 1.0, 1.0)
        shovelCardP = loader.loadModel('phase_5.5/models/gui/planting_but_shovel_P')
        shovelCardY = loader.loadModel('phase_5.5/models/gui/planting_but_shovel_Y')
        wateringCanCardP = loader.loadModel('phase_5.5/models/gui/planting_but_can_P')
        wateringCanCardY = loader.loadModel('phase_5.5/models/gui/planting_but_can_Y')
        backCard = loader.loadModel('phase_5.5/models/gui/planting_gui')
        iconImage = None
        iconModels = loader.loadModel('phase_3.5/models/gui/sos_textures')
        iconGeom = iconModels.find('**/fish')
        buttonText = TTLocalizer.GardeningPlant
        self.shovelText = ('',
         '',
         buttonText,
         '')
        self.__shovelButtonFake = DirectLabel(parent=self.__gardeningGuiFake, relief=None, text=self.shovelText, text_align=TextNode.ALeft, text_pos=(0.0, -0.0), text_scale=0.07, text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1), image_scale=(0.18, 1.0, 0.36), geom=None, geom_scale=iconScale, geom_color=iconColorWhite, pos=(0.15, 0, 0.2), scale=0.775)
        self.shovelButtonFake = self.__shovelButtonFake
        self.shovelText = ('',
         '',
         buttonText,
         '')
        self.__shovelButton = DirectButton(parent=self.__gardeningGui, relief=None, text=self.shovelText, text_align=TextNode.ACenter, text_pos=(0.0, -0.0), text_scale=0.1, text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1), image=(shovelCardP,
         shovelCardY,
         shovelCardY,
         shovelCardY), image_scale=(0.18, 1.0, 0.36), geom=None, geom_scale=iconScale, geom_color=iconColorWhite, pos=(0, 0, 0.2), scale=0.775, command=self.__shovelButtonClicked)
        self.shovelButton = self.__shovelButton
        iconGeom = iconModels.find('**/teleportIcon')
        buttonText = TTLocalizer.GardeningWater
        self.waterText = (buttonText,
         buttonText,
         buttonText,
         '')
        self.__wateringCanButtonFake = DirectLabel(parent=self.__gardeningGuiFake, relief=None, text=self.waterText, text_align=TextNode.ALeft, text_pos=(0.0, -0.0), text_scale=0.07, text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1), image_scale=(0.18, 1.0, 0.36), geom=None, geom_scale=iconScale, geom_color=iconColorWhite, pos=(0.15, 0, 0.01), scale=0.775)
        self.wateringCanButtonFake = self.__wateringCanButtonFake
        self.__wateringCanButton = DirectButton(parent=self.__gardeningGui, relief=None, text=self.waterText, text_align=TextNode.ACenter, text_pos=(0.0, -0.0), text_scale=0.1, text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1), image=(wateringCanCardP,
         wateringCanCardY,
         wateringCanCardY,
         wateringCanCardY), image_scale=(0.18, 1.0, 0.36), geom=None, geom_scale=iconScale, geom_color=iconColorWhite, pos=(0, 0, 0.01), scale=0.775, command=self.__wateringCanButtonClicked)
        self.wateringCanButton = self.__wateringCanButton
        self.basketText = '%s / %s' % (self.numFlowers, self.maxFlowerBasket)
        self.basketButton = DirectLabel(parent=self.__gardeningGui, relief=None, text=self.basketText, text_align=TextNode.ALeft, text_pos=(0.82, -1.4), text_scale=0.2, text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1), image=None, image_scale=iconScale, geom=None, geom_scale=iconScale, geom_color=iconColorWhite, pos=(-0.34, 0, 0.16), scale=0.3, textMayChange=1)
        if hasattr(self, 'shovel'):
            self.setShovelGuiLevel(self.shovel)
        if hasattr(self, 'wateringCan'):
            self.setWateringCanGuiLevel(self.wateringCan)
        self.__shovelButton.hide()
        self.__wateringCanButton.hide()
        self.__shovelButtonFake.hide()
        self.__wateringCanButtonFake.hide()
        return

    def changeButtonText(self, button, text):
        button['text'] = text

    def resetWaterText(self):
        self.wateringCanButton['text'] = self.waterText

    def resetShovelText(self):
        self.shovelButton['text'] = self.holdShovelText

    def showGardeningGui(self):
        self.loadGardeningGui()
        self.__gardeningGui.show()
        base.setCellsAvailable([base.leftCells[2]], 0)

    def hideGardeningGui(self):
        if self.__gardeningGui:
            self.__gardeningGui.hide()
            base.setCellsAvailable([base.leftCells[2]], 1)

    def showShovelButton(self, add = 0):
        if add:
            self.shovelButtonActiveCount += add
        else:
            self.showingShovel = 1
        self.notify.debug('showing shovel %s' % self.shovelButtonActiveCount)
        self.__gardeningGui.show()
        self.__shovelButton.show()

    def hideShovelButton(self, deduct = 0):
        self.shovelButtonActiveCount -= deduct
        if deduct == 0:
            self.showingShovel = 0
        if self.shovelButtonActiveCount < 1:
            self.shovelButtonActiveCount = 0
            if self.showingShovel == 0:
                self.__shovelButton.hide()
            self.handleAllGardeningButtonsHidden()
        self.notify.debug('hiding shovel %s' % self.shovelButtonActiveCount)

    def showWateringCanButton(self, add = 0):
        if add:
            self.wateringCanButtonActiveCount += add
        else:
            self.showingWateringCan = 1
        self.__gardeningGui.show()
        self.__wateringCanButton.show()
        self.basketButton.show()

    def hideWateringCanButton(self, deduct = 0):
        self.wateringCanButtonActiveCount -= deduct
        if deduct == 0:
            self.showingWateringCan = 0
        if self.wateringCanButtonActiveCount < 1:
            wateringCanButtonActiveCount = 0
            if self.showingWateringCan == 0:
                self.__wateringCanButton.hide()
            self.handleAllGardeningButtonsHidden()

    def showWateringCanButtonFake(self, add = 0):
        self.__wateringCanButtonFake.show()

    def hideWateringCanButtonFake(self, deduct = 0):
        self.__wateringCanButtonFake.hide()

    def showShovelButtonFake(self, add = 0):
        self.__shovelButtonFake.show()

    def hideShovelButtonFake(self, deduct = 0):
        self.__shovelButtonFake.hide()

    def levelWater(self, change = 1):
        if change < 0:
            return
        self.showWateringCanButtonFake(1)
        if change < 1:
            changeString = TTLocalizer.GardeningNoSkill
        else:
            changeString = '+%s %s' % (change, TTLocalizer.GardeningWaterSkill)
        self.waterTrack = Sequence(Wait(0.0), Func(self.changeButtonText, self.wateringCanButtonFake, changeString), SoundInterval(globalBattleSoundCache.getSound('GUI_balloon_popup.mp3'), node=self), Wait(1.0), Func(self.hideWateringCanButtonFake, 1))
        self.waterTrack.start()

    def levelShovel(self, change = 1):
        if change < 1:
            return
        self.showShovelButtonFake(1)
        if change < 1:
            changeString = TTLocalizer.GardeningNoSkill
        else:
            changeString = '+%s %s' % (change, TTLocalizer.GardeningShovelSkill)
        plant = base.cr.doId2do.get(self.shovelRelatedDoId)
        if plant:
            self.holdShovelText = plant.getShovelAction()
        self.shovelTrack = Sequence(Wait(0.0), Func(self.changeButtonText, self.shovelButtonFake, changeString), SoundInterval(globalBattleSoundCache.getSound('GUI_balloon_popup.mp3'), node=self), Wait(1.0), Func(self.hideShovelButtonFake, 1))
        self.shovelTrack.start()

    def setGuiConflict(self, con):
        self.guiConflict = con

    def getGuiConflict(self, con):
        return self.guiConflict

    def verboseState(self):
        self.lastPlaceState = 'None'
        taskMgr.add(self.__expressState, 'expressState', extraArgs=[])

    def __expressState(self, task = None):
        place = base.cr.playGame.getPlace()
        if place:
            state = place.fsm.getCurrentState()
            if state.getName() != self.lastPlaceState:
                print 'Place State Change From %s to %s' % (self.lastPlaceState, state.getName())
                self.lastPlaceState = state.getName()
        return Task.cont

    def addShovelRelatedDoId(self, doId):
        if hasattr(base.cr.playGame.getPlace(), 'detectedGardenPlotDone'):
            place = base.cr.playGame.getPlace()
            state = place.fsm.getCurrentState()
            if state.getName() == 'stopped':
                return
        self.touchingPlantList.append(doId)
        self.autoSetActivePlot()

    def removeShovelRelatedDoId(self, doId):
        if doId in self.touchingPlantList:
            self.touchingPlantList.remove(doId)
        self.autoSetActivePlot()

    def autoSetActivePlot(self):
        if self.guiConflict:
            return
        if len(self.touchingPlantList) > 0:
            minDist = 10000
            minDistPlot = 0
            for plot in self.touchingPlantList:
                plant = base.cr.doId2do.get(plot)
                if plant:
                    if self.getDistance(plant) < minDist:
                        minDist = self.getDistance(plant)
                        minDistPlot = plot
                else:
                    self.touchingPlantList.remove(plot)

            if len(self.touchingPlantList) == 0:
                self.setActivePlot(None)
            else:
                self.setActivePlot(minDistPlot)
        else:
            self.setActivePlot(None)
        return

    def setActivePlot(self, doId):
        if not self.gardenStarted:
            return
        self.shovelRelatedDoId = doId
        plant = base.cr.doId2do.get(doId)
        if plant:
            self.startStareAt(plant, Point3(0, 0, 1))
            self.__shovelButton['state'] = DGG.NORMAL
            if not plant.canBePicked():
                self.hideShovelButton()
            else:
                self.showShovelButton()
                self.setShovelAbility(TTLocalizer.GardeningPlant)
                if plant.getShovelAction():
                    self.setShovelAbility(plant.getShovelAction())
                    if plant.getShovelAction() == TTLocalizer.GardeningPick:
                        if not plant.unlockPick():
                            self.__shovelButton['state'] = DGG.DISABLED
                            self.setShovelAbility(TTLocalizer.GardeningFull)
                self.notify.debug('self.shovelRelatedDoId = %d' % self.shovelRelatedDoId)
                if plant.getShovelCommand():
                    self.extraShovelCommand = plant.getShovelCommand()
                    self.__shovelButton['command'] = self.__shovelButtonClicked
            if plant.canBeWatered():
                self.showWateringCanButton()
            else:
                self.hideWateringCanButton()
        else:
            self.stopStareAt()
            self.shovelRelatedDoId = 0
            if self.__shovelButton:
                self.__shovelButton['command'] = None
                self.hideShovelButton()
                self.hideWateringCanButton()
                self.handleAllGardeningButtonsHidden()
                if not self.inGardenAction:
                    if hasattr(base.cr.playGame.getPlace(), 'detectedGardenPlotDone'):
                        place = base.cr.playGame.getPlace()
                        if place:
                            place.detectedGardenPlotDone()
        return

    def setPlantToWater(self, plantId):
        import pdb
        pdb.set_trace()
        if self.plantToWater == None:
            self.plantToWater = plantId
            self.notify.debug('setting plant to water %s' % plantId)
        return

    def clearPlantToWater(self, plantId):
        if not hasattr(self, 'secondaryPlant'):
            self.secondaryWaterPlant = None
        if self.plantToWater == plantId:
            self.plantToWater = None
            self.hideWateringCanButton()
        return

    def hasPlant(self):
        if self.plantToWater != None:
            return 1
        else:
            return 0
        return

    def handleAllGardeningButtonsHidden(self):
        somethingVisible = False
        if not self.__shovelButton.isHidden():
            somethingVisible = True
        if not self.__wateringCanButton.isHidden():
            somethingVisible = True
        if not somethingVisible:
            self.hideGardeningGui()

    def setShovelAbility(self, ability):
        self.shovelAbility = ability
        if self.__shovelButton:
            self.__shovelButton['text'] = ability

    def setFlowerBasket(self, speciesList, varietyList):
        DistributedToon.DistributedToon.setFlowerBasket(self, speciesList, varietyList)
        self.numFlowers = len(self.flowerBasket.flowerList)
        self.maxFlowerBasket
        if hasattr(self, 'basketButton'):
            self.basketText = '%s / %s' % (self.numFlowers, self.maxFlowerBasket)
            self.basketButton['text'] = self.basketText

    def setShovelSkill(self, skillLevel):
        if hasattr(self, 'shovelSkill') and hasattr(self, 'shovelButton'):
            if self.shovelSkill != None:
                self.levelShovel(skillLevel - self.shovelSkill)
        oldShovelSkill = self.shovelSkill
        DistributedToon.DistributedToon.setShovelSkill(self, skillLevel)
        if hasattr(self, 'shovel'):
            oldShovelPower = GardenGlobals.getShovelPower(self.shovel, oldShovelSkill)
            newShovelPower = GardenGlobals.getShovelPower(self.shovel, self.shovelSkill)
            almostMaxedSkill = GardenGlobals.ShovelAttributes[GardenGlobals.MAX_SHOVELS - 1]['skillPts'] - 2
            if skillLevel >= GardenGlobals.ShovelAttributes[self.shovel]['skillPts']:
                self.promoteShovel()
            elif oldShovelSkill and oldShovelPower < newShovelPower:
                self.promoteShovelSkill(self.shovel, self.shovelSkill)
            elif oldShovelSkill == almostMaxedSkill and newShovelPower == GardenGlobals.getNumberOfShovelBoxes():
                self.promoteShovelSkill(self.shovel, self.shovelSkill)
        return

    def setWateringCanSkill(self, skillLevel):
        skillDelta = skillLevel - self.wateringCanSkill
        if skillDelta or 1:
            if hasattr(self, 'wateringCanSkill') and hasattr(self, 'wateringCanButton'):
                if self.wateringCanSkill != None:
                    self.levelWater(skillDelta)
            DistributedToon.DistributedToon.setWateringCanSkill(self, skillLevel)
            if hasattr(self, 'wateringCan'):
                if skillLevel >= GardenGlobals.WateringCanAttributes[self.wateringCan]['skillPts']:
                    self.promoteWateringCan()
        return

    def unlockGardeningButtons(self, task = None):
        if hasattr(self, '_LocalToon__shovelButton'):
            try:
                self.__shovelButton['state'] = DGG.NORMAL
            except TypeError:
                self.notify.warning('Could not unlock the shovel button- Type Error')

        if hasattr(self, '_LocalToon__wateringCanButton'):
            try:
                self.__wateringCanButton['state'] = DGG.NORMAL
            except TypeError:
                self.notify.warning('Could not unlock the watering can button - Type Error')

        taskMgr.remove('unlockGardenButtons')
        return None

    def lockGardeningButtons(self, task = None):
        if hasattr(self, '_LocalToon__shovelButton'):
            try:
                self.__shovelButton['state'] = DGG.DISABLED
            except TypeError:
                self.notify.warning('Could not lock the shovel button- Type Error')

        if hasattr(self, '_LocalToon__wateringCanButton'):
            try:
                self.__wateringCanButton['state'] = DGG.DISABLED
            except TypeError:
                self.notify.warning('Could not lock the watering can button - Type Error')

        self.accept('endPlantInteraction', self.__handleEndPlantInteraction)
        return None

    def reactivateShovel(self, task = None):
        if hasattr(self, '_LocalToon__shovelButton'):
            self.__shovelButton['state'] = DGG.NORMAL
        taskMgr.remove('reactShovel')
        return None

    def reactivateWater(self, task = None):
        if hasattr(self, '_LocalToon__wateringCanButton'):
            self.__wateringCanButton['state'] = DGG.NORMAL
        taskMgr.remove('reactWater')
        return None

    def handleEndPlantInteraction(self, object = None, replacement = 0):
        if not replacement:
            self.setInGardenAction(None, object)
            self.autoSetActivePlot()
        return

    def __handleEndPlantInteraction(self, task = None):
        self.setInGardenAction(None)
        self.autoSetActivePlot()
        return

    def promoteShovelSkill(self, shovelLevel, shovelSkill):
        shovelName = GardenGlobals.ShovelAttributes[shovelLevel]['name']
        shovelBeans = GardenGlobals.getShovelPower(shovelLevel, shovelSkill)
        oldShovelBeans = GardenGlobals.getShovelPower(shovelLevel, shovelSkill - 1)
        doPartyBall = False
        message = TTLocalizer.GardenShovelSkillLevelUp % {'shovel': shovelName,
         'oldbeans': oldShovelBeans,
         'newbeans': shovelBeans}
        if shovelBeans == GardenGlobals.getNumberOfShovelBoxes():
            if shovelSkill == GardenGlobals.ShovelAttributes[shovelLevel]['skillPts'] - 1:
                doPartyBall = True
                message = TTLocalizer.GardenShovelSkillMaxed % {'shovel': shovelName,
                 'oldbeans': oldShovelBeans,
                 'newbeans': shovelBeans}
        messagePos = Vec2(0, 0.2)
        messageScale = 0.07
        image = loader.loadModel('phase_5.5/models/gui/planting_but_shovel_P')
        imagePos = Vec3(0, 0, -0.13)
        imageScale = Vec3(0.28, 0, 0.56)
        if doPartyBall:
            go = Fanfare.makeFanfareWithMessageImage(0, base.localAvatar, 1, message, Vec2(0, 0.2), 0.08, image, Vec3(0, 0, -0.1), Vec3(0.35, 0, 0.7), wordwrap=23)
            Sequence(go[0], Func(go[1].show), LerpColorScaleInterval(go[1], duration=0.5, startColorScale=Vec4(1, 1, 1, 0), colorScale=Vec4(1, 1, 1, 1)), Wait(10), LerpColorScaleInterval(go[1], duration=0.5, startColorScale=Vec4(1, 1, 1, 1), colorScale=Vec4(1, 1, 1, 0)), Func(go[1].remove)).start()
        else:
            go = Fanfare.makePanel(base.localAvatar, 1)
            Fanfare.makeMessageBox(go, message, messagePos, messageScale, wordwrap=24)
            Fanfare.makeImageBox(go.itemFrame, image, imagePos, imageScale)
            Sequence(Func(go.show), LerpColorScaleInterval(go, duration=0.5, startColorScale=Vec4(1, 1, 1, 0), colorScale=Vec4(1, 1, 1, 1)), Wait(10), LerpColorScaleInterval(go, duration=0.5, startColorScale=Vec4(1, 1, 1, 1), colorScale=Vec4(1, 1, 1, 0)), Func(go.remove)).start()

    def promoteShovel(self, shovelLevel = 0):
        shovelName = GardenGlobals.ShovelAttributes[shovelLevel]['name']
        shovelBeans = GardenGlobals.getShovelPower(shovelLevel, 0)
        message = TTLocalizer.GardenShovelLevelUp % {'shovel': shovelName,
         'oldbeans': shovelBeans - 1,
         'newbeans': shovelBeans}
        messagePos = Vec2(0, 0.2)
        messageScale = 0.07
        image = loader.loadModel('phase_5.5/models/gui/planting_but_shovel_P')
        imagePos = Vec3(0, 0, -0.13)
        imageScale = Vec3(0.28, 0, 0.56)
        go = Fanfare.makePanel(base.localAvatar, 1)
        Fanfare.makeMessageBox(go, message, messagePos, messageScale, wordwrap=24)
        Fanfare.makeImageBox(go.itemFrame, image, imagePos, imageScale)
        Sequence(Func(go.show), LerpColorScaleInterval(go, duration=0.5, startColorScale=Vec4(1, 1, 1, 0), colorScale=Vec4(1, 1, 1, 1)), Wait(10), LerpColorScaleInterval(go, duration=0.5, startColorScale=Vec4(1, 1, 1, 1), colorScale=Vec4(1, 1, 1, 0)), Func(go.remove)).start()

    def promoteWateringCan(self, wateringCanlevel = 0):
        message = TTLocalizer.GardenWateringCanLevelUp + ' \n' + GardenGlobals.WateringCanAttributes[wateringCanlevel]['name']
        messagePos = Vec2(0, 0.2)
        messageScale = 0.08
        image = loader.loadModel('phase_5.5/models/gui/planting_but_can_P')
        imagePos = Vec3(0, 0, -0.1)
        imageScale = Vec3(0.35, 0, 0.7)
        if wateringCanlevel >= GardenGlobals.MAX_WATERING_CANS - 1:
            go = Fanfare.makeFanfareWithMessageImage(0, base.localAvatar, 1, message, Vec2(0, 0.2), 0.08, image, Vec3(0, 0, -0.1), Vec3(0.35, 0, 0.7))
            Sequence(go[0], Func(go[1].show), LerpColorScaleInterval(go[1], duration=0.5, startColorScale=Vec4(1, 1, 1, 0), colorScale=Vec4(1, 1, 1, 1)), Wait(5), LerpColorScaleInterval(go[1], duration=0.5, startColorScale=Vec4(1, 1, 1, 1), colorScale=Vec4(1, 1, 1, 0)), Func(go[1].remove)).start()
        else:
            go = Fanfare.makePanel(base.localAvatar, 1)
            Fanfare.makeMessageBox(go, message, messagePos, messageScale)
            Fanfare.makeImageBox(go.itemFrame, image, imagePos, imageScale)
            Sequence(Func(go.show), LerpColorScaleInterval(go, duration=0.5, startColorScale=Vec4(1, 1, 1, 0), colorScale=Vec4(1, 1, 1, 1)), Wait(5), LerpColorScaleInterval(go, duration=0.5, startColorScale=Vec4(1, 1, 1, 1), colorScale=Vec4(1, 1, 1, 0)), Func(go.remove)).start()

    def setInGardenAction(self, actionObject, fromObject = None):
        if actionObject:
            self.lockGardeningButtons()
        elif fromObject:
            self.unlockGardeningButtons()
        else:
            self.unlockGardeningButtons()
        self.inGardenAction = actionObject

    def __wateringCanButtonClicked(self):
        self.notify.debug('wateringCanButtonClicked')
        if self.inGardenAction:
            return
        plant = base.cr.doId2do.get(self.shovelRelatedDoId)
        if plant:
            if hasattr(plant, 'handleWatering'):
                plant.handleWatering()
        messenger.send('wakeup')

    def __shovelButtonClicked(self):
        if self.inGardenAction:
            return
        self.notify.debug('shovelButtonClicked')
        messenger.send('wakeup')
        thingId = self.shovelRelatedDoId
        thing = base.cr.doId2do.get(thingId)
        if hasattr(self, 'extraShovelCommand'):
            self.extraShovelCommand()
            self.setActivePlot(thingId)

    def setShovel(self, shovelId):
        DistributedToon.DistributedToon.setShovel(self, shovelId)
        if self.__gardeningGui:
            self.setShovelGuiLevel(shovelId)

    def setWateringCan(self, wateringCanId):
        DistributedToon.DistributedToon.setWateringCan(self, wateringCanId)
        if self.__gardeningGui:
            self.setWateringCanGuiLevel(wateringCanId)

    def setGardenStarted(self, bStarted):
        self.gardenStarted = bStarted
        if self.gardenStarted and not self.gardenPage and hasattr(self, 'book'):
            self.loadGardenPages()

    def b_setAnimState(self, animName, animMultiplier = 1.0, callback = None, extraArgs = []):
        if self.wantStatePrint:
            print 'Local Toon Anim State %s' % animName
        DistributedToon.DistributedToon.b_setAnimState(self, animName, animMultiplier, callback, extraArgs)

    def swimTimeoutAction(self):
        self.ignore('wakeup')
        self.takeOffSuit()
        base.cr.playGame.getPlace().fsm.request('final')
        self.b_setAnimState('TeleportOut', 1, self.__handleSwimExitTeleport, [0])
        return Task.done

    def __handleSwimExitTeleport(self, requestStatus):
        self.notify.info('closing shard...')
        base.cr.gameFSM.request('closeShard', ['afkTimeout'])

    def sbFriendAdd(self, id, info):
        print 'sbFriendAdd'

    def sbFriendUpdate(self, id, info):
        print 'sbFriendUpdate'

    def sbFriendRemove(self, id):
        print 'sbFriendRemove'

    def addGolfPage(self):
        if self.hasPlayedGolf():
            if hasattr(self, 'golfPage') and self.golfPage != None:
                return
            if not launcher.getPhaseComplete(6):
                self.acceptOnce('phaseComplete-6', self.addGolfPage)
                return
            self.golfPage = GolfPage.GolfPage()
            self.golfPage.setAvatar(self)
            self.golfPage.load()
            self.book.addPage(self.golfPage, pageName=TTLocalizer.GolfPageTitle)
        return

    def addEventsPage(self):
        if hasattr(self, 'eventsPage') and self.eventsPage != None:
            return
        if not launcher.getPhaseComplete(4):
            self.acceptOnce('phaseComplete-4', self.addEventsPage)
            return
        self.eventsPage = EventsPage.EventsPage()
        self.eventsPage.load()
        self.book.addPage(self.eventsPage, pageName=TTLocalizer.EventsPageName)
        return

    def addNewsPage(self):
        self.newsPage = NewsPage.NewsPage()
        self.newsPage.load()
        self.book.addPage(self.newsPage, pageName=TTLocalizer.NewsPageName)

    def addTIPPage(self):
        self.tipPage = TIPPage.TIPPage()
        self.tipPage.load()
        self.book.addPage(self.tipPage, pageName=TTLocalizer.TIPPageTitle)

    def setPinkSlips(self, pinkSlips):
        DistributedToon.DistributedToon.setPinkSlips(self, pinkSlips)
        self.inventory.updateTotalPropsText()

    def getAccountDays(self):
        days = 0
        defaultDays = base.cr.config.GetInt('account-days', -1)
        if defaultDays >= 0:
            days = defaultDays
        elif hasattr(base.cr, 'accountDays'):
            days = base.cr.accountDays
        return days

    def hasActiveBoardingGroup(self):
        if hasattr(localAvatar, 'boardingParty') and localAvatar.boardingParty:
            return localAvatar.boardingParty.hasActiveGroup(localAvatar.doId)
        else:
            return False

    def getZoneId(self):
        return self._zoneId

    def setZoneId(self, value):
        if value == -1:
            self.notify.error('zoneId should not be set to -1, tell Redmond')
        self._zoneId = value

    zoneId = property(getZoneId, setZoneId)

    def systemWarning(self, warningText = 'Acknowledge this system message.'):
        self.createSystemMsgAckGui()
        self.systemMsgAckGui['text'] = warningText
        self.systemMsgAckGui.show()

    def createSystemMsgAckGui(self):
        if self.systemMsgAckGui == None or self.systemMsgAckGui.isEmpty():
            message = 'o' * 100
            self.systemMsgAckGui = TTDialog.TTGlobalDialog(doneEvent=self.systemMsgAckGuiDoneEvent, message=message, style=TTDialog.Acknowledge)
            self.systemMsgAckGui.hide()
        return

    def hideSystemMsgAckGui(self):
        if self.systemMsgAckGui != None and not self.systemMsgAckGui.isEmpty():
            self.systemMsgAckGui.hide()
        return

    def setSleepAutoReply(self, fromId):
        av = base.cr.identifyAvatar(fromId)
        if isinstance(av, DistributedToon.DistributedToon):
            base.localAvatar.setSystemMessage(0, TTLocalizer.sleep_auto_reply % av.getName(), WhisperPopup.WTToontownBoardingGroup)
        elif av is not None:
            self.notify.warning('setSleepAutoReply from non-toon %s' % fromId)
        return

    def setLastTimeReadNews(self, newTime):
        self.lastTimeReadNews = newTime

    def getLastTimeReadNews(self):
        return self.lastTimeReadNews

    def cheatCogdoMazeGame(self, kindOfCheat = 0):
        if base.config.GetBool('allow-cogdo-maze-suit-hit-cheat'):
            maze = base.cr.doFind('DistCogdoMazeGame')
            if maze:
                if kindOfCheat == 0:
                    for suitNum in maze.game.suitsById.keys():
                        suit = maze.game.suitsById[suitNum]
                        maze.sendUpdate('requestSuitHitByGag', [suit.type, suitNum])

                elif kindOfCheat == 1:
                    for joke in maze.game.pickups:
                        maze.sendUpdate('requestPickUp', [joke.serialNum])

        else:
            self.sendUpdate('logSuspiciousEvent', ['cheatCogdoMazeGame'])

    def isReadingNews(self):
        result = False
        if base.cr and base.cr.playGame and base.cr.playGame.getPlace() and hasattr(base.cr.playGame.getPlace(), 'fsm') and base.cr.playGame.getPlace().fsm:
            fsm = base.cr.playGame.getPlace().fsm
            curState = fsm.getCurrentState().getName()
            if curState == 'stickerBook' and WantNewsPage:
                if hasattr(self, 'newsPage'):
                    if self.book.isOnPage(self.newsPage):
                        result = True
        return result

    def doTeleportResponse(self, fromAvatar, toAvatar, avId, available, shardId, hoodId, zoneId, sendToId):
        localAvatar.d_teleportResponse(avId, available, shardId, hoodId, zoneId, sendToId)

    def d_teleportResponse(self, avId, available, shardId, hoodId, zoneId, sendToId = None):
        if base.config.GetBool('want-tptrack', False):
            if available == 1:
                self.notify.debug('sending teleportResponseToAI')
                self.sendUpdate('teleportResponseToAI', [avId,
                 available,
                 shardId,
                 hoodId,
                 zoneId,
                 sendToId])
            else:
                self.sendUpdate('teleportResponse', [avId,
                 available,
                 shardId,
                 hoodId,
                 zoneId], sendToId)
        else:
            DistributedPlayer.DistributedPlayer.d_teleportResponse(self, avId, available, shardId, hoodId, zoneId, sendToId)

    def startQuestMap(self):
        if self.questMap:
            self.questMap.start()

    def stopQuestMap(self):
        if self.questMap:
            self.questMap.stop()

    def _startZombieCheck(self):
        pass

    def _stopZombieCheck(self):
        pass
