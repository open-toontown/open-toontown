from direct.showbase import PythonUtil
from otp.speedchat.SCMenu import SCMenu
from otp.speedchat.SCMenuHolder import SCMenuHolder
from otp.speedchat.SCStaticTextTerminal import SCStaticTextTerminal
from otp.otpbase import OTPLocalizer
AprilToonsMenu = [(OTPLocalizer.AprilToonsMenuSections[1], [30100, 30102]),
 (OTPLocalizer.AprilToonsMenuSections[2], [30110,
   30111,
   30112,
   30113,
   30114,
   30115]),
 (OTPLocalizer.AprilToonsMenuSections[3], [30120,
   30121,
   30122,
   30123,
   30124,
   30125,
   30126]),
 (OTPLocalizer.AprilToonsMenuSections[4], [30130,
   30131,
   30132,
   30133]),
 (OTPLocalizer.AprilToonsMenuSections[0], [30140, 30141])]

class TTSCAprilToonsMenu(SCMenu):

    def __init__(self):
        SCMenu.__init__(self)
        self.__aprilToonsMessagesChanged()
        submenus = []

    def destroy(self):
        SCMenu.destroy(self)

    def clearMenu(self):
        SCMenu.clearMenu(self)

    def __aprilToonsMessagesChanged(self):
        self.clearMenu()
        try:
            lt = base.localAvatar
        except:
            return

        for section in AprilToonsMenu:
            if section[0] == -1:
                for phrase in section[1]:
                    if phrase not in OTPLocalizer.SpeedChatStaticText:
                        print 'warning: tried to link April Toons phrase %s which does not seem to exist' % phrase
                        break
                    self.append(SCStaticTextTerminal(phrase))

            else:
                menu = SCMenu()
                for phrase in section[1]:
                    if phrase not in OTPLocalizer.SpeedChatStaticText:
                        print 'warning: tried to link April Toons phrase %s which does not seem to exist' % phrase
                        break
                    menu.append(SCStaticTextTerminal(phrase))

                menuName = str(section[0])
                self.append(SCMenuHolder(menuName, menu))
