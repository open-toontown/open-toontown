from direct.showbase import PythonUtil
from otp.speedchat.SCMenu import SCMenu
from otp.speedchat.SCMenuHolder import SCMenuHolder
from otp.speedchat.SCStaticTextTerminal import SCStaticTextTerminal
from otp.otpbase import OTPLocalizer
GolfMenuGuide = [(OTPLocalizer.GolfMenuSections[1], [4100,
   4101,
   4102,
   4103,
   4104,
   4105]),
 (OTPLocalizer.GolfMenuSections[2], [4200,
   4201,
   4202,
   4203,
   4204,
   4205,
   4206,
   4207]),
 (OTPLocalizer.GolfMenuSections[3], [4300,
   4301,
   4302,
   4303,
   4304,
   4305,
   4306,
   4307]),
 (OTPLocalizer.GolfMenuSections[0], [4000, 4001, 4002])]

class TTSCGolfMenu(SCMenu):

    def __init__(self):
        SCMenu.__init__(self)
        self.accept('golfMessagesChanged', self.__golfMessagesChanged)
        self.__golfMessagesChanged()
        submenus = []

    def destroy(self):
        SCMenu.destroy(self)

    def clearMenu(self):
        SCMenu.clearMenu(self)

    def __golfMessagesChanged(self):
        self.clearMenu()
        try:
            lt = base.localAvatar
        except:
            return

        for section in GolfMenuGuide:
            if section[0] == -1:
                for phrase in section[1]:
                    if phrase not in OTPLocalizer.SpeedChatStaticText:
                        print('warning: tried to link golf phrase %s which does not seem to exist' % phrase)
                        break
                    self.append(SCStaticTextTerminal(phrase))

            else:
                menu = SCMenu()
                for phrase in section[1]:
                    if phrase not in OTPLocalizer.SpeedChatStaticText:
                        print('warning: tried to link golf phrase %s which does not seem to exist' % phrase)
                        break
                    menu.append(SCStaticTextTerminal(phrase))

                menuName = str(section[0])
                self.append(SCMenuHolder(menuName, menu))
