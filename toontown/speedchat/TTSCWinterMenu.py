from direct.showbase import PythonUtil
from otp.speedchat.SCMenu import SCMenu
from otp.speedchat.SCMenuHolder import SCMenuHolder
from otp.speedchat.SCStaticTextTerminal import SCStaticTextTerminal
from toontown.speedchat.TTSCIndexedTerminal import TTSCIndexedTerminal
from otp.otpbase import OTPLocalizer
WinterMenu = [(OTPLocalizer.WinterMenuSections[0], {30200: 30220,
   30201: 30221,
   30202: 30222,
   30203: 30223,
   30204: 30224,
   30205: 30225}), (OTPLocalizer.WinterMenuSections[1], [30275, 30276, 30277])]

class TTSCWinterMenu(SCMenu):

    def __init__(self, carol):
        SCMenu.__init__(self)
        self.__messagesChanged(carol)

    def destroy(self):
        SCMenu.destroy(self)

    def clearMenu(self):
        SCMenu.clearMenu(self)

    def __messagesChanged(self, carol):
        self.clearMenu()
        try:
            lt = base.localAvatar
        except:
            return

        winterMenu = []
        if carol:
            winterMenu.append(WinterMenu[0])
        winterMenu.append(WinterMenu[1])
        for section in winterMenu:
            if section[0] == -1:
                for phrase in section[1]:
                    if phrase not in OTPLocalizer.SpeedChatStaticText:
                        print 'warning: tried to link Winter phrase %s which does not seem to exist' % phrase
                        break
                    self.append(SCStaticTextTerminal(phrase))

            else:
                menu = SCMenu()
                for phrase in section[1].keys():
                    blatherTxt = section[1][phrase]
                    if blatherTxt not in OTPLocalizer.SpeedChatStaticText:
                        print 'warning: tried to link Winter phrase %s which does not seem to exist' % phrase
                        break
                    menu.append(TTSCIndexedTerminal(OTPLocalizer.SpeedChatStaticText.get(phrase, None), blatherTxt))

                menuName = str(section[0])
                self.append(SCMenuHolder(menuName, menu))

        return
