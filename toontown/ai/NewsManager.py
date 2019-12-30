from pandac.PandaModules import *
from direct.distributed import DistributedObject
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import ToontownBattleGlobals
from toontown.battle import SuitBattleGlobals
from toontown.toonbase import TTLocalizer
from . import HolidayDecorator
from . import HalloweenHolidayDecorator
from . import CrashedLeaderBoardDecorator
from direct.interval.IntervalGlobal import *
import calendar
from copy import deepcopy
from toontown.speedchat import TTSCJellybeanJamMenu
decorationHolidays = [ToontownGlobals.WINTER_DECORATIONS,
 ToontownGlobals.WACKY_WINTER_DECORATIONS,
 ToontownGlobals.HALLOWEEN_PROPS,
 ToontownGlobals.SPOOKY_PROPS,
 ToontownGlobals.HALLOWEEN_COSTUMES,
 ToontownGlobals.SPOOKY_COSTUMES,
 ToontownGlobals.CRASHED_LEADERBOARD]
promotionalSpeedChatHolidays = [ToontownGlobals.ELECTION_PROMOTION]

class NewsManager(DistributedObject.DistributedObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('NewsManager')
    neverDisable = 1
    YearlyHolidayType = 1
    OncelyHolidayType = 2
    RelativelyHolidayType = 3
    OncelyMultipleStartHolidayType = 4

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        self.population = 0
        self.invading = 0
        self.decorationHolidayIds = []
        self.holidayDecorator = None
        self.holidayIdList = []
        base.cr.newsManager = self
        base.localAvatar.inventory.setInvasionCreditMultiplier(1)
        self.weeklyCalendarHolidays = []
        return

    def delete(self):
        self.cr.newsManager = None
        if self.holidayDecorator:
            self.holidayDecorator.exit()
        DistributedObject.DistributedObject.delete(self)
        return

    def setPopulation(self, population):
        self.population = population
        messenger.send('newPopulation', [population])

    def getPopulation(self):
        return population

    def sendSystemMessage(self, message, style):
        base.localAvatar.setSystemMessage(style, message)

    def setInvasionStatus(self, msgType, cogType, numRemaining, skeleton):
        self.notify.info('setInvasionStatus: msgType: %s cogType: %s, numRemaining: %s, skeleton: %s' % (msgType,
         cogType,
         numRemaining,
         skeleton))
        cogName = SuitBattleGlobals.SuitAttributes[cogType]['name']
        cogNameP = SuitBattleGlobals.SuitAttributes[cogType]['pluralname']
        if skeleton:
            cogName = TTLocalizer.Skeleton
            cogNameP = TTLocalizer.SkeletonP
        if msgType == ToontownGlobals.SuitInvasionBegin:
            msg1 = TTLocalizer.SuitInvasionBegin1
            msg2 = TTLocalizer.SuitInvasionBegin2 % cogNameP
            self.invading = 1
        elif msgType == ToontownGlobals.SuitInvasionUpdate:
            msg1 = TTLocalizer.SuitInvasionUpdate1 % numRemaining
            msg2 = TTLocalizer.SuitInvasionUpdate2 % cogNameP
            self.invading = 1
        elif msgType == ToontownGlobals.SuitInvasionEnd:
            msg1 = TTLocalizer.SuitInvasionEnd1 % cogName
            msg2 = TTLocalizer.SuitInvasionEnd2
            self.invading = 0
        elif msgType == ToontownGlobals.SuitInvasionBulletin:
            msg1 = TTLocalizer.SuitInvasionBulletin1
            msg2 = TTLocalizer.SuitInvasionBulletin2 % cogNameP
            self.invading = 1
        else:
            self.notify.warning('setInvasionStatus: invalid msgType: %s' % msgType)
            return
        if self.invading:
            mult = ToontownBattleGlobals.getInvasionMultiplier()
        else:
            mult = 1
        base.localAvatar.inventory.setInvasionCreditMultiplier(mult)
        Sequence(Wait(1.0), Func(base.localAvatar.setSystemMessage, 0, msg1), Wait(5.0), Func(base.localAvatar.setSystemMessage, 0, msg2), name='newsManagerWait', autoPause=1).start()

    def getInvading(self):
        return self.invading

    def startHoliday(self, holidayId):
        if holidayId not in self.holidayIdList:
            self.notify.info('setHolidayId: Starting Holiday %s' % holidayId)
            self.holidayIdList.append(holidayId)
            if holidayId in decorationHolidays:
                self.decorationHolidayIds.append(holidayId)
                if holidayId == ToontownGlobals.HALLOWEEN_PROPS:
                    if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                        base.localAvatar.chatMgr.chatInputSpeedChat.addHalloweenMenu()
                        self.setHalloweenPropsHolidayStart()
                elif holidayId == ToontownGlobals.SPOOKY_PROPS:
                    if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                        base.localAvatar.chatMgr.chatInputSpeedChat.addHalloweenMenu()
                        self.setSpookyPropsHolidayStart()
                elif holidayId == ToontownGlobals.WINTER_DECORATIONS:
                    if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                        base.localAvatar.chatMgr.chatInputSpeedChat.addWinterMenu()
                        self.setWinterDecorationsStart()
                elif holidayId == ToontownGlobals.WACKY_WINTER_DECORATIONS:
                    if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                        base.localAvatar.chatMgr.chatInputSpeedChat.addWinterMenu()
                        self.setWackyWinterDecorationsStart()
                if hasattr(base.cr.playGame, 'dnaStore') and hasattr(base.cr.playGame, 'hood') and hasattr(base.cr.playGame.hood, 'loader'):
                    if holidayId == ToontownGlobals.HALLOWEEN_COSTUMES or holidayId == ToontownGlobals.SPOOKY_COSTUMES:
                        self.holidayDecorator = HalloweenHolidayDecorator.HalloweenHolidayDecorator()
                    elif holidayId == ToontownGlobals.CRASHED_LEADERBOARD:
                        self.holidayDecorator = CrashedLeaderBoardDecorator.CrashedLeaderBoardDecorator()
                    else:
                        self.holidayDecorator = HolidayDecorator.HolidayDecorator()
                    self.holidayDecorator.decorate()
                    messenger.send('decorator-holiday-%d-starting' % holidayId)
            elif holidayId in promotionalSpeedChatHolidays:
                if hasattr(base, 'TTSCPromotionalMenu'):
                    base.TTSCPromotionalMenu.startHoliday(holidayId)
            elif holidayId == ToontownGlobals.MORE_XP_HOLIDAY:
                self.setMoreXpHolidayStart()
            elif holidayId == ToontownGlobals.JELLYBEAN_DAY:
                pass
            elif holidayId == ToontownGlobals.CIRCUIT_RACING_EVENT:
                self.setGrandPrixWeekendStart()
            elif holidayId == ToontownGlobals.HYDRANT_ZERO_HOLIDAY:
                self.setHydrantZeroHolidayStart()
            elif holidayId == ToontownGlobals.APRIL_FOOLS_COSTUMES:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    base.localAvatar.chatMgr.chatInputSpeedChat.addAprilToonsMenu()
            elif holidayId == ToontownGlobals.WINTER_CAROLING:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    base.localAvatar.chatMgr.chatInputSpeedChat.addCarolMenu()
                    self.setWinterCarolingStart()
            elif holidayId == ToontownGlobals.WACKY_WINTER_CAROLING:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    base.localAvatar.chatMgr.chatInputSpeedChat.addCarolMenu()
            elif holidayId == ToontownGlobals.VALENTINES_DAY:
                messenger.send('ValentinesDayStart')
                base.localAvatar.setSystemMessage(0, TTLocalizer.ValentinesDayStart)
            elif holidayId == ToontownGlobals.SILLY_CHATTER_ONE:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    base.localAvatar.chatMgr.chatInputSpeedChat.addSillyPhaseOneMenu()
            elif holidayId == ToontownGlobals.SILLY_CHATTER_TWO:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    base.localAvatar.chatMgr.chatInputSpeedChat.addSillyPhaseTwoMenu()
            elif holidayId == ToontownGlobals.SILLY_CHATTER_THREE:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    base.localAvatar.chatMgr.chatInputSpeedChat.addSillyPhaseThreeMenu()
            elif holidayId == ToontownGlobals.SILLY_CHATTER_FOUR:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    base.localAvatar.chatMgr.chatInputSpeedChat.addSillyPhaseFourMenu()
            elif holidayId == ToontownGlobals.SILLY_CHATTER_FIVE:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    base.localAvatar.chatMgr.chatInputSpeedChat.addSillyPhaseFiveMenu()
            elif holidayId == ToontownGlobals.VICTORY_PARTY_HOLIDAY:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    base.localAvatar.chatMgr.chatInputSpeedChat.addVictoryPartiesMenu()
            elif holidayId == ToontownGlobals.SELLBOT_NERF_HOLIDAY:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    self.setSellbotNerfHolidayStart()
                    base.localAvatar.chatMgr.chatInputSpeedChat.addSellbotNerfMenu()
            elif holidayId == ToontownGlobals.JELLYBEAN_TROLLEY_HOLIDAY or holidayId == ToontownGlobals.JELLYBEAN_TROLLEY_HOLIDAY_MONTH:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    base.localAvatar.chatMgr.chatInputSpeedChat.addJellybeanJamMenu(TTSCJellybeanJamMenu.JellybeanJamPhases.TROLLEY)
            elif holidayId == ToontownGlobals.JELLYBEAN_FISHING_HOLIDAY or holidayId == ToontownGlobals.JELLYBEAN_FISHING_HOLIDAY_MONTH:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    base.localAvatar.chatMgr.chatInputSpeedChat.addJellybeanJamMenu(TTSCJellybeanJamMenu.JellybeanJamPhases.FISHING)
            elif holidayId == ToontownGlobals.JELLYBEAN_PARTIES_HOLIDAY:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    self.setJellybeanPartiesHolidayStart()
            elif holidayId == ToontownGlobals.JELLYBEAN_PARTIES_HOLIDAY_MONTH:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    self.setJellybeanMonthHolidayStart()
            elif holidayId == ToontownGlobals.BANK_UPGRADE_HOLIDAY:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    self.setBankUpgradeHolidayStart()
            elif holidayId == ToontownGlobals.BLACK_CAT_DAY:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    self.setBlackCatHolidayStart()
            elif holidayId == ToontownGlobals.SPOOKY_BLACK_CAT:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    self.setSpookyBlackCatHolidayStart()
            elif holidayId == ToontownGlobals.TOP_TOONS_MARATHON:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    self.setTopToonsMarathonStart()
            elif holidayId == ToontownGlobals.SELLBOT_INVASION:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    base.localAvatar.chatMgr.chatInputSpeedChat.addSellbotInvasionMenu()
            elif holidayId == ToontownGlobals.SELLBOT_FIELD_OFFICE:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    base.localAvatar.chatMgr.chatInputSpeedChat.addSellbotFieldOfficeMenu()
            elif holidayId == ToontownGlobals.IDES_OF_MARCH:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    self.setIdesOfMarchStart()
                    base.localAvatar.chatMgr.chatInputSpeedChat.addIdesOfMarchMenu()
            elif holidayId == ToontownGlobals.EXPANDED_CLOSETS:
                self.setExpandedClosetsStart()
            elif holidayId == ToontownGlobals.KARTING_TICKETS_HOLIDAY:
                self.setKartingTicketsHolidayStart()

    def endHoliday(self, holidayId):
        if holidayId in self.holidayIdList:
            self.notify.info('setHolidayId: Ending Holiday %s' % holidayId)
            self.holidayIdList.remove(holidayId)
            if holidayId in self.decorationHolidayIds:
                self.decorationHolidayIds.remove(holidayId)
                if holidayId == ToontownGlobals.HALLOWEEN_PROPS:
                    if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                        base.localAvatar.chatMgr.chatInputSpeedChat.removeHalloweenMenu()
                        self.setHalloweenPropsHolidayEnd()
                elif holidayId == ToontownGlobals.SPOOKY_PROPS:
                    if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                        base.localAvatar.chatMgr.chatInputSpeedChat.removeHalloweenMenu()
                        self.setSpookyPropsHolidayEnd()
                elif holidayId == ToontownGlobals.WINTER_DECORATIONS:
                    if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                        base.localAvatar.chatMgr.chatInputSpeedChat.removeWinterMenu()
                        self.setWinterDecorationsEnd()
                elif holidayId == ToontownGlobals.WACKY_WINTER_DECORATIONS:
                    if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                        base.localAvatar.chatMgr.chatInputSpeedChat.removeWinterMenu()
                if hasattr(base.cr.playGame, 'dnaStore') and hasattr(base.cr.playGame, 'hood') and hasattr(base.cr.playGame.hood, 'loader'):
                    if holidayId == ToontownGlobals.HALLOWEEN_COSTUMES or holidayId == ToontownGlobals.SPOOKY_COSTUMES:
                        self.holidayDecorator = HalloweenHolidayDecorator.HalloweenHolidayDecorator()
                    elif holidayId == ToontownGlobals.CRASHED_LEADERBOARD:
                        self.holidayDecorator = CrashedLeaderBoardDecorator.CrashedLeaderBoardDecorator()
                    else:
                        self.holidayDecorator = HolidayDecorator.HolidayDecorator()
                    self.holidayDecorator.undecorate()
                    messenger.send('decorator-holiday-%d-ending' % holidayId)
            elif holidayId in promotionalSpeedChatHolidays:
                if hasattr(base, 'TTSCPromotionalMenu'):
                    base.TTSCPromotionalMenu.endHoliday(holidayId)
            elif holidayId == ToontownGlobals.MORE_XP_HOLIDAY:
                self.setMoreXpHolidayEnd()
            elif holidayId == ToontownGlobals.JELLYBEAN_DAY:
                pass
            elif holidayId == ToontownGlobals.CIRCUIT_RACING_EVENT:
                self.setGrandPrixWeekendEnd()
            elif holidayId == ToontownGlobals.APRIL_FOOLS_COSTUMES:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    base.localAvatar.chatMgr.chatInputSpeedChat.removeAprilToonsMenu()
            elif holidayId == ToontownGlobals.VALENTINES_DAY:
                messenger.send('ValentinesDayStop')
                base.localAvatar.setSystemMessage(0, TTLocalizer.ValentinesDayEnd)
            elif holidayId == ToontownGlobals.SILLY_CHATTER_ONE:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    base.localAvatar.chatMgr.chatInputSpeedChat.removeSillyPhaseOneMenu()
            elif holidayId == ToontownGlobals.SILLY_CHATTER_TWO:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    base.localAvatar.chatMgr.chatInputSpeedChat.removeSillyPhaseTwoMenu()
            elif holidayId == ToontownGlobals.SILLY_CHATTER_THREE:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    base.localAvatar.chatMgr.chatInputSpeedChat.removeSillyPhaseThreeMenu()
            elif holidayId == ToontownGlobals.SILLY_CHATTER_FOUR:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    base.localAvatar.chatMgr.chatInputSpeedChat.removeSillyPhaseFourMenu()
            elif holidayId == ToontownGlobals.SILLY_CHATTER_FIVE:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    base.localAvatar.chatMgr.chatInputSpeedChat.removeSillyPhaseFiveMenu()
            elif holidayId == ToontownGlobals.VICTORY_PARTY_HOLIDAY:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    base.localAvatar.chatMgr.chatInputSpeedChat.removeVictoryPartiesMenu()
            elif holidayId == ToontownGlobals.WINTER_CAROLING:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    base.localAvatar.chatMgr.chatInputSpeedChat.removeCarolMenu()
            elif holidayId == ToontownGlobals.WACKY_WINTER_CAROLING:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    base.localAvatar.chatMgr.chatInputSpeedChat.removeCarolMenu()
            elif holidayId == ToontownGlobals.SELLBOT_NERF_HOLIDAY:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    self.setSellbotNerfHolidayEnd()
                    base.localAvatar.chatMgr.chatInputSpeedChat.removeSellbotNerfMenu()
            elif holidayId == ToontownGlobals.JELLYBEAN_TROLLEY_HOLIDAY or holidayId == ToontownGlobals.JELLYBEAN_TROLLEY_HOLIDAY_MONTH:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    base.localAvatar.chatMgr.chatInputSpeedChat.removeJellybeanJamMenu()
            elif holidayId == ToontownGlobals.JELLYBEAN_FISHING_HOLIDAY or holidayId == ToontownGlobals.JELLYBEAN_FISHING_HOLIDAY_MONTH:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    base.localAvatar.chatMgr.chatInputSpeedChat.removeJellybeanJamMenu()
            elif holidayId == ToontownGlobals.JELLYBEAN_PARTIES_HOLIDAY or holidayId == ToontownGlobals.JELLYBEAN_PARTIES_HOLIDAY_MONTH:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    self.setJellybeanPartiesHolidayEnd()
                    base.localAvatar.chatMgr.chatInputSpeedChat.removeJellybeanJamMenu()
            elif holidayId == ToontownGlobals.BLACK_CAT_DAY:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    self.setBlackCatHolidayEnd()
            elif holidayId == ToontownGlobals.SPOOKY_BLACK_CAT:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    self.setSpookyBlackCatHolidayEnd()
            elif holidayId == ToontownGlobals.TOP_TOONS_MARATHON:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    self.setTopToonsMarathonEnd()
            elif holidayId == ToontownGlobals.SELLBOT_INVASION:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    base.localAvatar.chatMgr.chatInputSpeedChat.removeSellbotInvasionMenu()
            elif holidayId == ToontownGlobals.SELLBOT_FIELD_OFFICE:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    base.localAvatar.chatMgr.chatInputSpeedChat.removeSellbotFieldOfficeMenu()
            elif holidayId == ToontownGlobals.IDES_OF_MARCH:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    base.localAvatar.chatMgr.chatInputSpeedChat.removeIdesOfMarchMenu()

    def setHolidayIdList(self, holidayIdList):

        def isEnding(id):
            return id not in holidayIdList

        def isStarting(id):
            return id not in self.holidayIdList

        toEnd = list(filter(isEnding, self.holidayIdList))
        for endingHolidayId in toEnd:
            self.endHoliday(endingHolidayId)

        toStart = list(filter(isStarting, holidayIdList))
        for startingHolidayId in toStart:
            self.startHoliday(startingHolidayId)

        messenger.send('setHolidayIdList', [holidayIdList])

    def getDecorationHolidayId(self):
        return self.decorationHolidayIds

    def getHolidayIdList(self):
        return self.holidayIdList

    def setBingoWin(self, zoneId):
        base.localAvatar.setSystemMessage(0, 'Bingo congrats!')

    def setBingoStart(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.FishBingoStart)

    def setBingoOngoing(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.FishBingoOngoing)

    def setBingoEnd(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.FishBingoEnd)

    def setCircuitRaceStart(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.CircuitRaceStart)

    def setCircuitRaceOngoing(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.CircuitRaceOngoing)

    def setCircuitRaceEnd(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.CircuitRaceEnd)

    def setTrolleyHolidayStart(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.TrolleyHolidayStart)

    def setTrolleyHolidayOngoing(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.TrolleyHolidayOngoing)

    def setTrolleyHolidayEnd(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.TrolleyHolidayEnd)

    def setTrolleyWeekendStart(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.TrolleyWeekendStart)

    def setTrolleyWeekendEnd(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.TrolleyWeekendEnd)

    def setRoamingTrialerWeekendStart(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.RoamingTrialerWeekendStart)
        base.roamingTrialers = True

    def setRoamingTrialerWeekendOngoing(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.RoamingTrialerWeekendOngoing)
        base.roamingTrialers = True

    def setRoamingTrialerWeekendEnd(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.RoamingTrialerWeekendEnd)
        base.roamingTrialers = False

    def setMoreXpHolidayStart(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.MoreXpHolidayStart)

    def setMoreXpHolidayOngoing(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.MoreXpHolidayOngoing)

    def setMoreXpHolidayEnd(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.MoreXpHolidayEnd)

    def setJellybeanDayStart(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.JellybeanDayHolidayStart)

    def setJellybeanDayEnd(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.JellybeanDayHolidayEnd)

    def setGrandPrixWeekendStart(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.GrandPrixWeekendHolidayStart)

    def setGrandPrixWeekendEnd(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.GrandPrixWeekendHolidayEnd)

    def setHydrantZeroHolidayStart(self):
        messenger.send('HydrantZeroIsRunning', [True])

    def setSellbotNerfHolidayStart(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.SellbotNerfHolidayStart)

    def setSellbotNerfHolidayEnd(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.SellbotNerfHolidayEnd)

    def setJellybeanTrolleyHolidayStart(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.JellybeanTrolleyHolidayStart)

    def setJellybeanTrolleyHolidayEnd(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.JellybeanTrolleyHolidayEnd)

    def setJellybeanFishingHolidayStart(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.JellybeanFishingHolidayStart)

    def setJellybeanFishingHolidayEnd(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.JellybeanFishingHolidayEnd)

    def setJellybeanPartiesHolidayStart(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.JellybeanPartiesHolidayStart)

    def setJellybeanMonthHolidayStart(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.JellybeanMonthHolidayStart)

    def setJellybeanPartiesHolidayEnd(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.JellybeanPartiesHolidayEnd)

    def setBankUpgradeHolidayStart(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.BankUpgradeHolidayStart)

    def setHalloweenPropsHolidayStart(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.HalloweenPropsHolidayStart)

    def setHalloweenPropsHolidayEnd(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.HalloweenPropsHolidayEnd)

    def setSpookyPropsHolidayStart(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.SpookyPropsHolidayStart)

    def setSpookyPropsHolidayEnd(self):
        pass

    def setBlackCatHolidayStart(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.BlackCatHolidayStart)

    def setBlackCatHolidayEnd(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.BlackCatHolidayEnd)

    def setSpookyBlackCatHolidayStart(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.SpookyBlackCatHolidayStart)
        for currToon in list(base.cr.toons.values()):
            currToon.setDNA(currToon.style.clone())

    def setSpookyBlackCatHolidayEnd(self):
        for currToon in list(base.cr.toons.values()):
            currToon.setDNA(currToon.style.clone())

    def setTopToonsMarathonStart(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.TopToonsMarathonStart)

    def setTopToonsMarathonEnd(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.TopToonsMarathonEnd)

    def setWinterDecorationsStart(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.WinterDecorationsStart)

    def setWinterDecorationsEnd(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.WinterDecorationsEnd)

    def setWackyWinterDecorationsStart(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.WackyWinterDecorationsStart)

    def setWinterCarolingStart(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.WinterCarolingStart)

    def setExpandedClosetsStart(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.ExpandedClosetsStart)

    def setKartingTicketsHolidayStart(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.KartingTicketsHolidayStart)

    def setIdesOfMarchStart(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.IdesOfMarchStart)

    def holidayNotify(self):
        for id in self.holidayIdList:
            if id == 19:
                self.setBingoOngoing()
            elif id == 20:
                self.setCircuitRaceOngoing()
            elif id == 21:
                self.setTrolleyHolidayOngoing()
            elif id == 22:
                self.setRoamingTrialerWeekendOngoing()

    def setWeeklyCalendarHolidays(self, weeklyCalendarHolidays):
        self.weeklyCalendarHolidays = weeklyCalendarHolidays

    def getHolidaysForWeekday(self, day):
        result = []
        for item in self.weeklyCalendarHolidays:
            if item[1] == day:
                result.append(item[0])

        return result

    def setYearlyCalendarHolidays(self, yearlyCalendarHolidays):
        self.yearlyCalendarHolidays = yearlyCalendarHolidays

    def getYearlyHolidaysForDate(self, theDate):
        result = []
        for item in self.yearlyCalendarHolidays:
            if item[1][0] == theDate.month and item[1][1] == theDate.day:
                newItem = [self.YearlyHolidayType] + list(item)
                result.append(tuple(newItem))
                continue
            if item[2][0] == theDate.month and item[2][1] == theDate.day:
                newItem = [self.YearlyHolidayType] + list(item)
                result.append(tuple(newItem))

        return result

    def setMultipleStartHolidays(self, multipleStartHolidays):
        self.multipleStartHolidays = multipleStartHolidays

    def getMultipleStartHolidaysForDate(self, theDate):
        result = []
        for theHoliday in self.multipleStartHolidays:
            times = theHoliday[1:]
            tempTimes = times[0]
            for startAndStopTimes in tempTimes:
                startTime = startAndStopTimes[0]
                endTime = startAndStopTimes[1]
                if startTime[0] == theDate.year and startTime[1] == theDate.month and startTime[2] == theDate.day:
                    fakeOncelyHoliday = [theHoliday[0], startTime, endTime]
                    newItem = [self.OncelyMultipleStartHolidayType] + fakeOncelyHoliday
                    result.append(tuple(newItem))
                    continue
                if endTime[0] == theDate.year and endTime[1] == theDate.month and endTime[2] == theDate.day:
                    fakeOncelyHoliday = [theHoliday[0], startTime, endTime]
                    newItem = [self.OncelyMultipleStartHolidayType] + fakeOncelyHoliday
                    result.append(tuple(newItem))

        return result

    def setOncelyCalendarHolidays(self, oncelyCalendarHolidays):
        self.oncelyCalendarHolidays = oncelyCalendarHolidays

    def getOncelyHolidaysForDate(self, theDate):
        result = []
        for item in self.oncelyCalendarHolidays:
            if item[1][0] == theDate.year and item[1][1] == theDate.month and item[1][2] == theDate.day:
                newItem = [self.OncelyHolidayType] + list(item)
                result.append(tuple(newItem))
                continue
            if item[2][0] == theDate.year and item[2][1] == theDate.month and item[2][2] == theDate.day:
                newItem = [self.OncelyHolidayType] + list(item)
                result.append(tuple(newItem))

        return result

    def setRelativelyCalendarHolidays(self, relativelyCalendarHolidays):
        self.relativelyCalendarHolidays = relativelyCalendarHolidays

    def getRelativelyHolidaysForDate(self, theDate):
        result = []
        self.weekDaysInMonth = []
        self.numDaysCorMatrix = [(28, 0), (29, 1), (30, 2), (31, 3)]

        for i in range(7):
            self.weekDaysInMonth.append((i, 4))

        for holidayItem in self.relativelyCalendarHolidays:
            item = deepcopy(holidayItem)

            newItem = []
            newItem.append(item[0])

            i = 1
            while i < len(item):
                sRepNum = item[i][1]
                sWeekday = item[i][2]
                eWeekday = item[i+1][2]

                while 1:
                    eRepNum = item[i+1][1]

                    self.initRepMatrix(theDate.year, item[i][0])
                    while self.weekDaysInMonth[sWeekday][1] < sRepNum:
                        sRepNum -= 1

                    sDay = self.dayForWeekday(theDate.year, item[i][0], sWeekday, sRepNum)

                    self.initRepMatrix(theDate.year, item[i+1][0])
                    while self.weekDaysInMonth[eWeekday][1] < eRepNum:
                        eRepNum -= 1

                    nDay = self.dayForWeekday(theDate.year, item[i+1][0], eWeekday, eRepNum)

                    if ((nDay > sDay and
                        item[i+1][0] == item[i][0] and
                        (item[i+1][1] - item[i][1]) <= (nDay - sDay + abs(eWeekday - sWeekday))/7) or
                        item[i+1][0] != item[i][0]):
                        break

                    if self.weekDaysInMonth[eWeekday][1] > eRepNum:
                        eRepNum += 1
                    else:
                        item[i+1][0] += 1
                        item[i+1][1] = 1

                newItem.append([item[i][0], sDay, item[i][3], item[i][4], item[i][5]])

                newItem.append([item[i+1][0], nDay, item[i+1][3], item[i+1][4], item[i+1][5]])

                i += 2

            if item[1][0] == theDate.month and newItem[1][1] == theDate.day:
                nItem = [self.RelativelyHolidayType] + list(newItem)
                result.append(tuple(nItem))
                continue

            if item[2][0] == theDate.month and newItem[2][1] == theDate.day:
                nItem = [self.RelativelyHolidayType] + list(newItem)
                result.append(tuple(nItem))

        return result

    def dayForWeekday(self, year, month, weekday, repNum):
        monthDays = calendar.monthcalendar(year, month)
        if monthDays[0][weekday] == 0:
            repNum += 1
        return monthDays[repNum - 1][weekday]

    def initRepMatrix(self, year, month):
        for i in range(7):
            self.weekDaysInMonth[i] = (i, 4)

        startingWeekDay, numDays = calendar.monthrange(year, month)
        if startingWeekDay > 6:
            import pdb
            pdb.set_trace()
        for i in range(4):
            if numDays == self.numDaysCorMatrix[i][0]:
                break

        for j in range(self.numDaysCorMatrix[i][1]):
            self.weekDaysInMonth[startingWeekDay] = (self.weekDaysInMonth[startingWeekDay][0], self.weekDaysInMonth[startingWeekDay][1] + 1)
            startingWeekDay = (startingWeekDay + 1) % 7

    def isHolidayRunning(self, holidayId):
        result = holidayId in self.holidayIdList
        return result
