from direct.showbase import PythonUtil
from otp.speedchat.SCMenu import SCMenu
from otp.speedchat.SCMenuHolder import SCMenuHolder
from otp.speedchat.SCStaticTextTerminal import SCStaticTextTerminal
from otp.otpbase import OTPLocalizer
JellybeanJamMenu = [(OTPLocalizer.JellybeanJamMenuSections[0], [30180,
   30181,
   30182,
   30183,
   30184,
   30185]), (OTPLocalizer.JellybeanJamMenuSections[1], [30186,
   30187,
   30188,
   30189,
   30190])]
JellybeanJamPhases = PythonUtil.Enum('TROLLEY, FISHING, PARTIES')
PhaseSpecifPhrases = [30180, 30181, 30182]

class TTSCJellybeanJamMenu(SCMenu):

    def __init__(self, phase):
        SCMenu.__init__(self)
        if phase in JellybeanJamPhases:
            self.__messagesChanged(phase)
        else:
            print('warning: tried to add Jellybean Jam phase %s which does not seem to exist' % phase)

    def destroy(self):
        SCMenu.destroy(self)

    def clearMenu(self):
        SCMenu.clearMenu(self)

    def __messagesChanged(self, phase):
        self.clearMenu()
        try:
            lt = base.localAvatar
        except:
            return

        for section in JellybeanJamMenu:
            if section[0] == -1:
                for phrase in section[1]:
                    if phrase not in OTPLocalizer.SpeedChatStaticText:
                        print('warning: tried to link Jellybean Jam phrase %s which does not seem to exist' % phrase)
                        break
                    self.append(SCStaticTextTerminal(phrase))

            else:
                menu = SCMenu()
                for phrase in section[1]:
                    if phrase not in OTPLocalizer.SpeedChatStaticText:
                        print('warning: tried to link Jellybean Jam phrase %s which does not seem to exist' % phrase)
                        break
                    menu.append(SCStaticTextTerminal(phrase))

                menuName = str(section[0])
                self.append(SCMenuHolder(menuName, menu))
