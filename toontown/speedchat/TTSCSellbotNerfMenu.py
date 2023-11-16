from direct.showbase import PythonUtil

from otp.otpbase import OTPLocalizer
from otp.speedchat.SCMenu import SCMenu
from otp.speedchat.SCMenuHolder import SCMenuHolder
from otp.speedchat.SCStaticTextTerminal import SCStaticTextTerminal

SellbotNerfMenu = [(OTPLocalizer.SellbotNerfMenuSections[0], [30150,
   30151,
   30152,
   30153,
   30154,
   30155,
   30156]), (OTPLocalizer.SellbotNerfMenuSections[1], [30157,
   30158,
   30159,
   30160,
   30161,
   30162,
   30163,
   30164]), (OTPLocalizer.SellbotNerfMenuSections[2], [30165,
   30166,
   30167,
   30168,
   30169,
   30170,
   30171,
   30172,
   30173,
   30174,
   30175])]

class TTSCSellbotNerfMenu(SCMenu):

    def __init__(self):
        SCMenu.__init__(self)
        self.__messagesChanged()

    def destroy(self):
        SCMenu.destroy(self)

    def clearMenu(self):
        SCMenu.clearMenu(self)

    def __messagesChanged(self):
        self.clearMenu()
        try:
            lt = base.localAvatar
        except:
            return

        for section in SellbotNerfMenu:
            if section[0] == -1:
                for phrase in section[1]:
                    if phrase not in OTPLocalizer.SpeedChatStaticText:
                        print('warning: tried to link Sellbot Nerf phrase %s which does not seem to exist' % phrase)
                        break
                    self.append(SCStaticTextTerminal(phrase))

            else:
                menu = SCMenu()
                for phrase in section[1]:
                    if phrase not in OTPLocalizer.SpeedChatStaticText:
                        print('warning: tried to link Sellbot Nerf phrase %s which does not seem to exist' % phrase)
                        break
                    menu.append(SCStaticTextTerminal(phrase))

                menuName = str(section[0])
                self.append(SCMenuHolder(menuName, menu))
