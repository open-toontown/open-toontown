from direct.showbase import PythonUtil
from otp.speedchat.SCMenu import SCMenu
from otp.speedchat.SCMenuHolder import SCMenuHolder
from otp.speedchat.SCStaticTextTerminal import SCStaticTextTerminal
from otp.otpbase.OTPLocalizer import SpeedChatStaticText
from toontown.speedchat.TTSCIndexedTerminal import TTSCIndexedTerminal
from otp.otpbase import OTPLocalizer
VictoryPartiesMenu = [(OTPLocalizer.VictoryPartiesMenuSections[1], [30350,
   30351,
   30352,
   30353,
   30354]), (OTPLocalizer.VictoryPartiesMenuSections[2], [30355,
   30356,
   30357,
   30358,
   30359,
   30360,
   30361]), (OTPLocalizer.VictoryPartiesMenuSections[0], [])]

class TTSCVictoryPartiesMenu(SCMenu):

    def __init__(self):
        SCMenu.__init__(self)
        self.__messagesChanged()
        submenus = []

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

        for section in VictoryPartiesMenu:
            if section[0] == -1:
                for phrase in section[1]:
                    if phrase not in OTPLocalizer.SpeedChatStaticText:
                        print('warning: tried to link Victory Parties phrase %s which does not seem to exist' % phrase)
                        break
                    self.append(SCStaticTextTerminal(phrase))

            else:
                menu = SCMenu()
                for phrase in section[1]:
                    if phrase not in OTPLocalizer.SpeedChatStaticText:
                        print('warning: tried to link Victory Parties phrase %s which does not seem to exist' % phrase)
                        break
                    menu.append(SCStaticTextTerminal(phrase))

                menuName = str(section[0])
                self.append(SCMenuHolder(menuName, menu))
