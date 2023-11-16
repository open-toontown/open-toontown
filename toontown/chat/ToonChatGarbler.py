import random
import string

from otp.chat import ChatGarbler
from otp.otpbase import OTPLocalizer

from toontown.toonbase import TTLocalizer


class ToonChatGarbler(ChatGarbler.ChatGarbler):
    animalSounds = {'dog': TTLocalizer.ChatGarblerDog,
     'cat': TTLocalizer.ChatGarblerCat,
     'mouse': TTLocalizer.ChatGarblerMouse,
     'horse': TTLocalizer.ChatGarblerHorse,
     'rabbit': TTLocalizer.ChatGarblerRabbit,
     'duck': TTLocalizer.ChatGarblerDuck,
     'monkey': TTLocalizer.ChatGarblerMonkey,
     'bear': TTLocalizer.ChatGarblerBear,
     'pig': TTLocalizer.ChatGarblerPig,
     'default': OTPLocalizer.ChatGarblerDefault}

    def garble(self, toon, message):
        newMessage = ''
        animalType = toon.getStyle().getType()
        if animalType in ToonChatGarbler.animalSounds:
            wordlist = ToonChatGarbler.animalSounds[animalType]
        else:
            wordlist = ToonChatGarbler.animalSounds['default']
        numWords = random.randint(1, 7)
        for i in range(1, numWords + 1):
            wordIndex = random.randint(0, len(wordlist) - 1)
            newMessage = newMessage + wordlist[wordIndex]
            if i < numWords:
                newMessage = newMessage + ' '

        return newMessage

    def garbleSingle(self, toon, message):
        newMessage = ''
        animalType = toon.getStyle().getType()
        if animalType in ToonChatGarbler.animalSounds:
            wordlist = ToonChatGarbler.animalSounds[animalType]
        else:
            wordlist = ToonChatGarbler.animalSounds['default']
        numWords = 1
        for i in range(1, numWords + 1):
            wordIndex = random.randint(0, len(wordlist) - 1)
            newMessage = newMessage + wordlist[wordIndex]
            if i < numWords:
                newMessage = newMessage + ' '

        return newMessage
