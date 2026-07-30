from direct.showbase import PythonUtil
from otp.speedchat.SCMenu import SCMenu
from otp.speedchat.SCMenuHolder import SCMenuHolder
from otp.speedchat.SCStaticTextTerminal import SCStaticTextTerminal
from toontown.speedchat.TTSCIndexedTerminal import TTSCIndexedTerminal
from otp.otpbase import OTPLocalizer
from toontown.cogdominium import CogdoInterior
SellbotFieldOfficeMenu = [(OTPLocalizer.SellbotFieldOfficeMenuSections[0], list(range(30404, 30409))), (OTPLocalizer.SellbotFieldOfficeMenuSections[1], list(range(30409, 30419)))]

class TTSCSellbotFieldOfficeMenu(SCMenu):

    def __init__(self):
        SCMenu.__init__(self)
        self.accept('sellbotFieldOfficeChanged', self.__messagesChanged)
        self.__messagesChanged(False)

    def destroy(self):
        SCMenu.destroy(self)

    def clearMenu(self):
        SCMenu.clearMenu(self)

    def __messagesChanged(self, inSellbotFieldOffice):
        self.clearMenu()
        try:
            lt = base.localAvatar
        except:
            return

        for section in SellbotFieldOfficeMenu:
            if section[0] == -1:
                for phrase in section[1]:
                    if phrase not in OTPLocalizer.SpeedChatStaticText:
                        print('warning: tried to link Winter phrase %s which does not seem to exist' % phrase)
                        break
                    self.append(SCStaticTextTerminal(phrase))

            elif inSellbotFieldOffice:
                menu = SCMenu()
                for phrase in section[1]:
                    if phrase not in OTPLocalizer.SpeedChatStaticText:
                        print('warning: tried to link Halloween phrase %s which does not seem to exist' % phrase)
                        break
                    menu.append(SCStaticTextTerminal(phrase))

                menuName = str(section[0])
                self.append(SCMenuHolder(menuName, menu))
