from direct.showbase import PythonUtil
from otp.speedchat.SCMenu import SCMenu
from otp.speedchat.SCMenuHolder import SCMenuHolder
from otp.speedchat.SCStaticTextTerminal import SCStaticTextTerminal
from otp.otpbase import OTPLocalizer
BoardingMenuGuide = [(OTPLocalizer.BoardingMenuSections[0], []),
 (OTPLocalizer.BoardingMenuSections[1], []),
 (OTPLocalizer.BoardingMenuSections[2], []),
 (OTPLocalizer.BoardingMenuSections[3], [5005,
   5006,
   5007,
   5008,
   5009])]
GroupPhrases = [5000,
 5001,
 5002,
 5003,
 5004]
ZoneIdsToMsgs = {10000: [GroupPhrases, [5100, 5101, 5102], [5200, 5201, 5202]],
 10100: [GroupPhrases, [5103], [5203]],
 11100: [GroupPhrases, [5104], [5204]],
 11200: [GroupPhrases, [5105, 5106], [5205, 5206]],
 12000: [GroupPhrases, [5107, 5108, 5109], [5207, 5208, 5209]],
 12100: [GroupPhrases, [5110], [5210]],
 13100: [GroupPhrases, [5111], [5211]],
 13200: [GroupPhrases, [5112,
          5113,
          5114,
          5115], [5212,
          5213,
          5214,
          5215]]}

class TTSCBoardingMenu(SCMenu):

    def __init__(self, zoneId):
        SCMenu.__init__(self)
        self.__boardingMessagesChanged(zoneId)

    def destroy(self):
        SCMenu.destroy(self)

    def clearMenu(self):
        SCMenu.clearMenu(self)

    def __boardingMessagesChanged(self, zoneId):
        self.clearMenu()
        try:
            lt = base.localAvatar
        except:
            return

        for count in range(len(BoardingMenuGuide)):
            section = BoardingMenuGuide[count]
            if section[0] == -1:
                for phrase in section[1]:
                    if phrase not in OTPLocalizer.SpeedChatStaticText:
                        print('warning: tried to link boarding phrase %s which does not seem to exist' % phrase)
                        break
                    self.append(SCStaticTextTerminal(phrase))

            else:
                menu = SCMenu()
                phrases = ZoneIdsToMsgs[zoneId][count]
                for phrase in phrases:
                    if phrase not in OTPLocalizer.SpeedChatStaticText:
                        print('warning: tried to link boarding phrase %s which does not seem to exist' % phrase)
                        break
                    menu.append(SCStaticTextTerminal(phrase))

                menuName = str(section[0])
                self.append(SCMenuHolder(menuName, menu))
