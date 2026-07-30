from direct.directnotify import DirectNotifyGlobal
from otp.speedchat.SCMenu import SCMenu
from otp.speedchat import SCMenuHolder
from otp.speedchat.SCStaticTextTerminal import SCStaticTextTerminal
from otp.otpbase import OTPLocalizer
from toontown.pets import PetTricks

class TTSCPetTrickMenu(SCMenu):
    notify = DirectNotifyGlobal.directNotify.newCategory('TTSCPetTrickMenu')

    def __init__(self):
        SCMenu.__init__(self)
        self.accept('petTrickPhrasesChanged', self.__phrasesChanged)
        self.__phrasesChanged()

    def destroy(self):
        self.ignore('petTrickPhrasesChanged')
        SCMenu.destroy(self)

    def __phrasesChanged(self, zoneId = 0):
        self.clearMenu()
        try:
            lt = base.localAvatar
        except:
            return

        for trickId in lt.petTrickPhrases:
            if trickId not in PetTricks.TrickId2scIds:
                TTSCPetTrickMenu.notify.warning('unknown trick ID: %s' % trickId)
            else:
                for msg in PetTricks.TrickId2scIds[trickId]:
                    self.append(SCStaticTextTerminal(msg))
