from otp.speedchat.SCMenu import SCMenu
from otp.speedchat import SCMenuHolder
from otp.speedchat.SCStaticTextTerminal import SCStaticTextTerminal
from otp.otpbase import OTPLocalizer
ZoneToMsgs = {3: [1803, 1903],
 4: [1804, 1904],
 5: [1805, 1905],
 6: [1806, 1906],
 7: [1807, 1907],
 8: [1808, 1908],
 9: [1809, 1909],
 10: [1810, 1910],
 11: [1811, 1911],
 12: [1812, 1912],
 13: [1813, 1913],
 14: [1814, 1914],
 15: [1815, 1915],
 16: [1816, 1916],
 17: [1817, 1917],
 18: [1818, 1918],
 19: [1819, 1919],
 20: [1820, 1920],
 21: [1821, 1921],
 22: [1822, 1922],
 23: [1823, 1923],
 24: [1824, 1924],
 25: [1825, 1925],
 27: [1827, 1927],
 30: [1830, 1930],
 31: [1831, 1931],
 32: [1832, 1932],
 33: [1833, 1933],
 34: [1834, 1934],
 35: [1835, 1935],
 36: [1836, 1936],
 37: [1837, 1937],
 38: [1838, 1938],
 40: [1840, 1940],
 41: [1841, 1941],
 60: [1860, 1960],
 61: [1861, 1961]}
GLOBAL_MSGS = [1700,
 1701,
 1702,
 1703,
 1704]

class TTSCFactoryMenu(SCMenu):

    def __init__(self):
        SCMenu.__init__(self)
        self.meetMenuHolder = None
        zoneId = base.cr.playGame.getPlaceId()
        if zoneId and zoneId == 11000:
            meetMenu = SCMenu()
            for msgIndex in OTPLocalizer.SCFactoryMeetMenuIndexes:
                term = SCStaticTextTerminal(msgIndex)
                meetMenu.append(term)

            self.meetMenuHolder = SCMenuHolder.SCMenuHolder(OTPLocalizer.SCMenuFactoryMeet, meetMenu)
            self[0:0] = [self.meetMenuHolder]
        self.accept('factoryZoneChanged', self.__zoneChanged)
        self.__zoneChanged()
        return

    def destroy(self):
        self.ignore('factoryZoneChanged')
        SCMenu.destroy(self)

    def __zoneChanged(self, zoneId = 0):
        if self.meetMenuHolder:
            del self[0]
        self.clearMenu()
        try:
            lt = base.localAvatar
        except:
            return

        phrases = []

        def addTerminal(terminal, self = self, phrases = phrases):
            displayText = terminal.getDisplayText()
            if displayText not in phrases:
                self.append(terminal)
                phrases.append(displayText)

        for msg in GLOBAL_MSGS + ZoneToMsgs.get(zoneId, []):
            addTerminal(SCStaticTextTerminal(msg))

        if self.meetMenuHolder:
            self[0:0] = [self.meetMenuHolder]
