from panda3d.core import CSDefault, ConfigVariable, ConfigVariableBool
from direct.directnotify import DirectNotifyGlobal
from direct.distributed.ClockDelta import *
from direct.interval.IntervalGlobal import *
from . import HolidayDecorator
from toontown.toonbase import ToontownGlobals
from toontown.hood import GSHood

class CrashedLeaderBoardDecorator(HolidayDecorator.HolidayDecorator):
    notify = DirectNotifyGlobal.directNotify.newCategory('CrashedLeaderBoardDecorator')

    def __init__(self):
        HolidayDecorator.HolidayDecorator.__init__(self)

    def decorate(self):
        self.updateHoodDNAStore()
        self.swapIval = self.getSwapVisibleIval()
        if self.swapIval:
            self.swapIval.start()
        holidayIds = base.cr.newsManager.getDecorationHolidayId()
        if ToontownGlobals.CRASHED_LEADERBOARD not in holidayIds:
            return
        if ConfigVariableBool('want-crashedLeaderBoard-Smoke', True).getValue():
            self.startSmokeEffect()

    def startSmokeEffect(self):
        if isinstance(base.cr.playGame.getPlace().loader.hood, GSHood.GSHood):
            base.cr.playGame.getPlace().loader.startSmokeEffect()

    def stopSmokeEffect(self):
        if isinstance(base.cr.playGame.getPlace().loader.hood, GSHood.GSHood):
            base.cr.playGame.getPlace().loader.stopSmokeEffect()

    def undecorate(self):
        if ConfigVariableBool('want-crashedLeaderBoard-Smoke', True).getValue():
            self.stopSmokeEffect()
        holidayIds = base.cr.newsManager.getDecorationHolidayId()
        if len(holidayIds) > 0:
            self.decorate()
            return
        storageFile = base.cr.playGame.hood.storageDNAFile
        if storageFile:
            loadDNAFile(self.dnaStore, storageFile, CSDefault)
        self.swapIval = self.getSwapVisibleIval()
        if self.swapIval:
            self.swapIval.start()
