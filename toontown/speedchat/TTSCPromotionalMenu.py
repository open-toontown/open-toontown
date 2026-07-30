from direct.directnotify import DirectNotifyGlobal
from otp.speedchat.SCMenu import SCMenu
from otp.speedchat import SCMenuHolder
from otp.speedchat.SCStaticTextTerminal import SCStaticTextTerminal
from otp.otpbase import OTPLocalizer
from toontown.toonbase import ToontownGlobals
holidayId2menuInfo = {ToontownGlobals.ELECTION_PROMOTION: (OTPLocalizer.SCMenuElection, [10000,
                                       10001,
                                       10006,
                                       10007])}

class TTSCPromotionalMenu(SCMenu):
    notify = DirectNotifyGlobal.directNotify.newCategory('TTSCPromotionalMenu')

    def __init__(self):
        SCMenu.__init__(self)
        base.TTSCPromotionalMenu = self
        self.curHolidayId = None
        self.clearMenu()
        return

    def destroy(self):
        del base.TTSCPromotionalMenu
        SCMenu.destroy(self)

    def startHoliday(self, holidayId):
        if self.curHolidayId is not None:
            TTSCPromotionalMenu.notify.warning('overriding existing holidayId %s with %s' % (self.curHolidayId, holidayId))
        self.curHolidayId = holidayId
        title, structure = holidayId2menuInfo[holidayId]
        self.rebuildFromStructure(structure, title=title)
        return

    def endHoliday(self, holidayId):
        if holidayId != self.curHolidayId:
            TTSCPromotionalMenu.notify.warning('unexpected holidayId: %s' % holidayId)
            return
        self.curHolidayId = None
        self.clearMenu()
        return
