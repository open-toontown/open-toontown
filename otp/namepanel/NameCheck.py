import string
from otp.otpbase import OTPLocalizer
from direct.directnotify import DirectNotifyGlobal
from pandac.PandaModules import NSError
from pandac.PandaModules import TextEncoder, TextNode
notify = DirectNotifyGlobal.directNotify.newCategory('NameCheck')

def filterString(str, filter):
    result = ''
    for char in str:
        if char in filter:
            result = result + char

    return result


def justLetters(str):
    letters = ''
    for c in str:
        if c.isalpha():
            letters = letters + c

    return letters


def justUpper(str):
    upperCaseLetters = ''
    for c in str:
        if c.upper() != c.lower():
            if c == c.upper():
                upperCaseLetters = upperCaseLetters + c

    return upperCaseLetters


def wordList(str):
    words = str.split()
    result = []
    for word in words:
        subWords = word.split('-')
        for sw in subWords:
            if sw:
                result.append(sw)

    return result


def checkName(name, otherCheckFuncs = [], font = None):

    def longEnough(name):
        if len(name) < 2:
            notify.info('name is too short')
            return OTPLocalizer.NCTooShort

    def emptyName(name):
        if name.strip() == '':
            notify.info('name is empty')
            return OTPLocalizer.NCTooShort

    def printableChars(name):
        for char in name:
            if ord(char) < 128 and char not in string.printable:
                notify.info('name contains non-printable char #%s' % ord(char))
                return OTPLocalizer.NCGeneric

    validAsciiChars = set(".,'-" + string.ascii_letters + string.whitespace)

    def _validCharacter(c, validAsciiChars = validAsciiChars, font = font):
        if c in validAsciiChars:
            return True
        if c.isalpha() or c.isspace():
            return True
        return False

    def badCharacters(name, _validCharacter = _validCharacter):
        for char in name:
            if not _validCharacter(char):
                if char in string.digits:
                    notify.info('name contains digits')
                    return OTPLocalizer.NCNoDigits
                else:
                    notify.info('name contains bad char: %s' % TextEncoder().encodeWtext(char))
                    return OTPLocalizer.NCBadCharacter % TextEncoder().encodeWtext(char)

    def fontHasCharacters(name, font = font):
        if font:
            tn = TextNode('NameCheck')
            tn.setFont(font)
            for c in name:
                if not tn.hasCharacter(str(c)):
                    notify.info('name contains bad char: %s' % TextEncoder().encodeWtext(c))
                    return OTPLocalizer.NCBadCharacter % TextEncoder().encodeWtext(c)

    def hasLetters(name):
        words = wordList(name)
        for word in words:
            letters = justLetters(word)
            if len(letters) == 0:
                notify.info('word "%s" has no letters' % TextEncoder().encodeWtext(word))
                return OTPLocalizer.NCNeedLetters

    def hasVowels(name):

        def perWord(word):
            if '.' in word:
                return None
            for char in word:
                if ord(char) >= 128:
                    return None

            letters = filterString(word, string.ascii_letters)
            if len(letters) > 2:
                vowels = filterString(letters, 'aeiouyAEIOUY')
                if len(vowels) == 0:
                    notify.info('word "%s" has no vowels' % TextEncoder().encodeWtext(word))
                    return OTPLocalizer.NCNeedVowels
            return None

        for word in wordList(name):
            problem = perWord(word)
            if problem:
                return problem

    def monoLetter(name):

        def perWord(word):
            word = word
            letters = justLetters(word)
            if len(letters) > 2:
                letters = TextEncoder().decodeText(TextEncoder.lower(TextEncoder().encodeWtext(letters).decode('utf-8')).encode('utf-8'))
                filtered = filterString(letters, letters[0])
                if filtered == letters:
                    notify.info('word "%s" uses only one letter' % TextEncoder().encodeWtext(word))
                    return OTPLocalizer.NCGeneric

        for word in wordList(name):
            problem = perWord(word)
            if problem:
                return problem

    def checkDashes(name):
        def validDash(index, name=name):
            if index == 0 or i == len(name)-1:
                return 0
            if not name[i-1].isalpha():
                return 0
            if not name[i+1].isalpha():
                return 0
            return 1

        i=0
        while 1:
            i = name.find('-', i, len(name))
            if i < 0:
                return None
            if not validDash(i):
                notify.info('name makes invalid use of dashes')
                return OTPLocalizer.NCDashUsage
            i += 1

    def checkCommas(name):
        def validComma(index, name=name):
            if index == 0 or i == len(name)-1:
                return OTPLocalizer.NCCommaEdge
            if name[i-1].isspace():
                return OTPLocalizer.NCCommaAfterWord
            if not name[i+1].isspace():
                return OTPLocalizer.NCCommaUsage
            return None

        i=0
        while 1:
            i = name.find(',', i, len(name))
            if i < 0:
                return None
            problem = validComma(i)
            if problem:
                notify.info('name makes invalid use of commas')
                return problem
            i += 1

    def checkPeriods(name):
        words = wordList(name)
        for word in words:
            if word[-1] == ',':
                word = word[:-1]
            numPeriods = word.count('.')
            if not numPeriods:
                continue
            letters = justLetters(word)
            numLetters = len(letters)
            if word[-1] != '.':
                notify.info('word "%s" does not end in a period' % TextEncoder().encodeWtext(word))
                return OTPLocalizer.NCPeriodUsage
            if numPeriods > 2:
                notify.info('word "%s" has too many periods' % TextEncoder().encodeWtext(word))
                return OTPLocalizer.NCPeriodUsage
            if numPeriods == 2:
                if not (word[1] == '.' and word[3] == '.'):
                    notify.info('word "%s" does not fit the J.T. pattern' % TextEncoder().encodeWtext(word))
                    return OTPLocalizer.NCPeriodUsage

        return None

    def checkApostrophes(name):
        words = wordList(name)
        for word in words:
            numApos = word.count("'")
            if numApos > 2:
                notify.info('word "%s" has too many apostrophes.' % TextEncoder().encodeWtext(word))
                return OTPLocalizer.NCApostrophes

        numApos = name.count("'")
        if numApos > 3:
            notify.info('name has too many apostrophes.')
            return OTPLocalizer.NCApostrophes

    def tooManyWords(name):
        if len(wordList(name)) > 4:
            notify.info('name has too many words')
            return OTPLocalizer.NCTooManyWords

    def allCaps(name):
        letters = justLetters(name)
        if len(letters) > 2:
            upperLetters = TextEncoder().decodeText(TextEncoder.upper(TextEncoder().encodeWtext(letters).decode('utf-8')).encode('utf-8'))
            for i in range(len(upperLetters)):
                if not upperLetters[0].isupper():
                    return

            if upperLetters == letters:
                notify.info('name is all caps')
                return OTPLocalizer.NCAllCaps

    def mixedCase(name):
        words = wordList(name)
        for word in words:
            if len(word) > 2:
                capitals = justUpper(word)
                if len(capitals) > 2:
                    notify.info('name has mixed case')
                    return OTPLocalizer.NCMixedCase

    def checkJapanese(name):
        asciiSpace = list(range(32, 33))
        asciiDigits = list(range(48, 64))
        hiragana = list(range(12353, 12448))
        katakana = list(range(12449, 12544))
        halfwidthKatakana = list(range(65381, 65440))
        halfwidthCharacter = set(asciiSpace + halfwidthKatakana)
        allowedUtf8 = set(asciiSpace + hiragana + katakana + halfwidthKatakana)

        te = TextEncoder()
        dc = 0.0

        for char in (ord(char) for char in te.decodeText(name)):
            if char not in allowedUtf8:
                if char in asciiDigits:
                    notify.info('name contains not allowed ascii digits')
                    return OTPLocalizer.NCNoDigits
                else:
                    notify.info('name contains not allowed utf8 char: 0x%04x' % char)
                    return OTPLocalizer.NCBadCharacter % te.encodeWtext(chr(char))
            elif char in halfwidthCharacter:
                dc += 0.5
            else:
                dc += 1

        if dc < 2:
            notify.info('name is too short: %0.1f' % dc)
            return OTPLocalizer.NCTooShort
        elif dc > 8:
            notify.info('name has been occupied more than eight display cells: %0.1f' % dc)
            return OTPLocalizer.NCGeneric

    def repeatedChars(name):
        count = 1
        lastChar = None
        i = 0
        while i < len(name):
            char = name[i]
            i += 1
            if char == lastChar:
                count += 1
            else:
                count = 1
            lastChar = char
            if count > 2:
                notify.info('character %s is repeated too many times' % TextEncoder().encodeWtext(char))
                return OTPLocalizer.NCRepeatedChar % TextEncoder().encodeWtext(char)

        return

    checks = [printableChars,
     badCharacters,
     fontHasCharacters,
     longEnough,
     emptyName,
     hasLetters,
     hasVowels,
     monoLetter,
     checkDashes,
     checkCommas,
     checkPeriods,
     checkApostrophes,
     tooManyWords,
     allCaps,
     mixedCase,
     repeatedChars] + otherCheckFuncs
    symmetricChecks = []
    name = TextEncoder().decodeText(name.encode('utf-8'))
    notify.info('checking name "%s"...' % TextEncoder().encodeWtext(name).decode('utf-8'))
    for check in checks:
        problem = check(name[:])
        if not problem and check in symmetricChecks:
            nName = name[:]
            bName.reverse()
            problem = check(bName)
            print('problem = %s' % problem)
        if problem:
            return problem

    return None


severity = notify.getSeverity()
notify.setSeverity(NSError)
for i in range(32):
    pass

for c in '!"#$%&()*+/:;<=>?@[\\]^_`{|}~':
    pass

notify.setSeverity(severity)
del severity
