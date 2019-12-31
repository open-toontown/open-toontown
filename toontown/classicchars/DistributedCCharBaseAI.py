from otp.ai.AIBaseGlobal import *
from direct.distributed.ClockDelta import *
from otp.avatar import DistributedAvatarAI
from otp.avatar.DistributedPlayerAI import DistributedPlayerAI
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals
import random
import functools

class DistributedCCharBaseAI(DistributedAvatarAI.DistributedAvatarAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedCCharBaseAI')

    def __init__(self, air, name):
        DistributedAvatarAI.DistributedAvatarAI.__init__(self, air)
        self.setName(name)
        self.exitOff()
        self.transitionToCostume = 0
        self.diffPath = None
        return

    def generate(self):
        DistributedAvatarAI.DistributedAvatarAI.generate(self)
        if config.GetBool('classic-char-client-spam', 0):
            self._ccharSpamTask = taskMgr.add(self._simSpam, 'cchar-spam-%s' % serialNum())

    def _simSpam(self, task):
        AvEnter = 'avatarEnter'
        AvExit = 'avatarExit'
        SetChat = 'setNearbyAvatarChat'
        SetSC = 'setNearbyAvatarSC'
        SetSCCustom = 'setNearbyAvatarSCCustom'
        SetSCToontask = 'setNearbyAvatarSCToontask'
        msgs = (AvEnter, AvExit, SetChat, SetSC, SetSCCustom, SetSCToontask)
        msg = random.choice(msgs)
        r = random.random()
        fixedAvId = 1000000006
        if r < 0.3:
            avId = random.randrange(1 << 32)
        else:
            if r < 0.6:
                players = self.air.doFindAllOfType('DistributedToonAI')[0]
                if len(players):
                    player = random.choice(players)
                    avId = player.doId
                else:
                    avId = fixedAvId
            else:
                avId = fixedAvId
        savedIdFunc = self.air.getAvatarIdFromSender
        self.air.getAvatarIdFromSender = lambda : avId
        rrange = random.randrange
        if msg is AvEnter:
            self.avatarEnter()
        elif msg is AvExit:
            self.avatarExit()
        else:
            if msg is SetChat:
                length = rrange(1024)
                s = ''
                for i in range(length):
                    s += chr(rrange(1 << 8))

                self.setNearbyAvatarChat(s)
            else:
                if msg is SetSC:
                    self.setNearbyAvatarSC(rrange(1 << 16))
                else:
                    if msg is SetSCCustom:
                        self.setNearbyAvatarSCCustom(rrange(1 << 16))
                    else:
                        if msg is SetSCToontask:
                            self.setNearbyAvatarSCToontask(rrange(1 << 32), rrange(1 << 32), rrange(1 << 32), rrange(1 << 8))
        self.air.getAvatarIdFromSender = savedIdFunc
        return task.cont

    def delete(self):
        self.ignoreAll()
        if hasattr(self, '_ccharSpamTask'):
            taskMgr.remove(self._ccharSpamTask)
            self._ccharSpamTask = None
        DistributedAvatarAI.DistributedAvatarAI.delete(self)
        return

    def exitOff(self):
        self.__initAttentionSpan()
        self.__clearNearbyAvatars()

    def avatarEnter(self):
        avId = self.air.getAvatarIdFromSender()
        if avId not in self.air.doId2do:
            self.air.writeServerEvent('suspicious', avId, 'CCharBaseAI.avatarEnter from unknown avId')
            return
        av = self.air.getDo(avId)
        if not isinstance(av, DistributedPlayerAI):
            self.air.writeServerEvent('suspicious', avId, 'CCharBaseAI.avatarEnter from non-player object to cchar %s' % self.doId)
            return
        if av.zoneId != self.zoneId:
            self.air.writeServerEvent('suspicious', avId, 'CCharBaseAI.avatarEnter from av in zone %s, my zone is %s' % (av.zoneId, self.zoneId))
            return
        self.notify.debug('adding avatar ' + str(avId) + ' to the nearby avatar list')
        if avId not in self.nearbyAvatars:
            self.nearbyAvatars.append(avId)
        else:
            self.air.writeServerEvent('suspicious', avId, 'CCharBase.avatarEnter')
            self.notify.warning('Avatar %s already in nearby avatars!' % avId)
        self.nearbyAvatarInfoDict[avId] = {}
        self.nearbyAvatarInfoDict[avId]['enterTime'] = globalClock.getRealTime()
        self.nearbyAvatarInfoDict[avId]['lastChatTime'] = 0
        self.sortNearbyAvatars()
        self.__interestingAvatarEventOccured()
        avExitEvent = self.air.getAvatarExitEvent(avId)
        self.acceptOnce(avExitEvent, self.__handleExitedAvatar, [avId])
        self.avatarEnterNextState()

    def avatarExit(self):
        avId = self.air.getAvatarIdFromSender()
        self.__doAvatarExit(avId)

    def __doAvatarExit(self, avId):
        avId = self.air.getAvatarIdFromSender()
        self.notify.debug('removing avatar ' + str(avId) + ' from the nearby avatar list')
        if avId not in self.nearbyAvatars:
            self.notify.debug('avatar ' + str(avId) + ' not in the nearby avatar list')
        else:
            avExitEvent = self.air.getAvatarExitEvent(avId)
            self.ignore(avExitEvent)
            del self.nearbyAvatarInfoDict[avId]
            self.nearbyAvatars.remove(avId)

    def avatarEnterNextState():
        pass

    def avatarExitNextState():
        pass

    def __clearNearbyAvatars(self):
        self.nearbyAvatars = []
        self.nearbyAvatarInfoDict = {}

    def sortNearbyAvatars(self):

        def nAv_compare(a, b, nAvIDict=self.nearbyAvatarInfoDict):
            tsA = nAvIDict[a]['enterTime']
            tsB = nAvIDict[b]['enterTime']
            if tsA == tsB:
                return 0
            else:
                if tsA < tsB:
                    return -1
                else:
                    return 1

        self.nearbyAvatars.sort(key=functools.cmp_to_key(nAv_compare))

    def getNearbyAvatars(self):
        return self.nearbyAvatars

    def __avatarSpoke(self, avId):
        now = globalClock.getRealTime()
        if avId in self.nearbyAvatarInfoDict:
            self.nearbyAvatarInfoDict[avId]['lastChatTime'] = now
            self.__interestingAvatarEventOccured()

    def __initAttentionSpan(self):
        self.__avatarTimeoutBase = 0

    def __interestingAvatarEventOccured(self, t=None):
        if t == None:
            t = globalClock.getRealTime()
        self.__avatarTimeoutBase = t
        return

    def lostInterest(self):
        now = globalClock.getRealTime()
        if now > self.__avatarTimeoutBase + 50.0:
            return 1
        return 0

    def __handleExitedAvatar(self, avId):
        self.__doAvatarExit(avId)

    def setNearbyAvatarChat(self, msg):
        avId = self.air.getAvatarIdFromSender()
        self.notify.debug('setNearbyAvatarChat: avatar ' + str(avId) + ' said ' + str(msg))
        self.__avatarSpoke(avId)

    def setNearbyAvatarSC(self, msgIndex):
        avId = self.air.getAvatarIdFromSender()
        self.notify.debug('setNearbyAvatarSC: avatar %s said SpeedChat phrase %s' % (avId, msgIndex))
        self.__avatarSpoke(avId)

    def setNearbyAvatarSCCustom(self, msgIndex):
        avId = self.air.getAvatarIdFromSender()
        self.notify.debug('setNearbyAvatarSCCustom: avatar %s said custom SpeedChat phrase %s' % (avId, msgIndex))
        self.__avatarSpoke(avId)

    def setNearbyAvatarSCToontask(self, taskId, toNpcId, toonProgress, msgIndex):
        avId = self.air.getAvatarIdFromSender()
        self.notify.debug('setNearbyAvatarSCToontask: avatar %s said %s' % (avId, (taskId, toNpcId, toonProgress, msgIndex)))
        self.__avatarSpoke(avId)

    def getWalk(self):
        return ('', '', 0)

    def walkSpeed(self):
        return 0.1

    def handleHolidays(self):
        self.CCChatter = 0
        if hasattr(simbase.air, 'holidayManager'):
            if ToontownGlobals.CRASHED_LEADERBOARD in simbase.air.holidayManager.currentHolidays:
                self.CCChatter = ToontownGlobals.CRASHED_LEADERBOARD
            elif ToontownGlobals.CIRCUIT_RACING_EVENT in simbase.air.holidayManager.currentHolidays:
                self.CCChatter = ToontownGlobals.CIRCUIT_RACING_EVENT
            elif ToontownGlobals.WINTER_CAROLING in simbase.air.holidayManager.currentHolidays:
                self.CCChatter = ToontownGlobals.WINTER_CAROLING
            elif ToontownGlobals.WINTER_DECORATIONS in simbase.air.holidayManager.currentHolidays:
                self.CCChatter = ToontownGlobals.WINTER_DECORATIONS
            elif ToontownGlobals.VALENTINES_DAY in simbase.air.holidayManager.currentHolidays:
                self.CCChatter = ToontownGlobals.VALENTINES_DAY
            elif ToontownGlobals.APRIL_FOOLS_COSTUMES in simbase.air.holidayManager.currentHolidays:
                self.CCChatter = ToontownGlobals.APRIL_FOOLS_COSTUMES
            elif ToontownGlobals.SILLY_CHATTER_ONE in simbase.air.holidayManager.currentHolidays:
                self.CCChatter = ToontownGlobals.SILLY_CHATTER_ONE
            elif ToontownGlobals.SILLY_CHATTER_TWO in simbase.air.holidayManager.currentHolidays:
                self.CCChatter = ToontownGlobals.SILLY_CHATTER_TWO
            elif ToontownGlobals.SILLY_CHATTER_THREE in simbase.air.holidayManager.currentHolidays:
                self.CCChatter = ToontownGlobals.SILLY_CHATTER_THREE
            elif ToontownGlobals.SILLY_CHATTER_FOUR in simbase.air.holidayManager.currentHolidays:
                self.CCChatter = ToontownGlobals.SILLY_CHATTER_FOUR
            elif ToontownGlobals.SILLY_CHATTER_FIVE in simbase.air.holidayManager.currentHolidays:
                self.CCChatter = ToontownGlobals.SILLY_CHATTER_FOUR
            elif ToontownGlobals.HALLOWEEN_COSTUMES in simbase.air.holidayManager.currentHolidays:
                self.CCChatter = ToontownGlobals.HALLOWEEN_COSTUMES
            elif ToontownGlobals.SELLBOT_FIELD_OFFICE in simbase.air.holidayManager.currentHolidays:
                self.CCChatter = ToontownGlobals.SELLBOT_FIELD_OFFICE

    def getCCLocation(self):
        return 0

    def getCCChatter(self):
        self.handleHolidays()
        return self.CCChatter

    def fadeAway(self):
        self.sendUpdate('fadeAway', [])

    def transitionCostume(self):
        self.transitionToCostume = 1
