from direct.directnotify import DirectNotifyGlobal
from direct.showbase.PythonUtil import list2dict, Enum
from toontown.pets import PetTricks
import types
notify = DirectNotifyGlobal.directNotify.newCategory('PetObserve')

def getEventName(zoneId):
    return 'PetObserve-%s' % zoneId


def send(zoneIds, petObserve):
    if petObserve.isValid():
        if type(zoneIds) not in (types.ListType, types.TupleType):
            zoneIds = [zoneIds]
        for zoneId in zoneIds:
            messenger.send(getEventName(zoneId), [petObserve])


Phrases = Enum('HI, BYE, YES, NO, SOOTHE, PRAISE, CRITICISM, HAPPY,SAD, ANGRY, HURRY, QUESTION, FRIENDLY, LETS_PLAY,COME, FOLLOW_ME, STAY, NEED_LAFF, NEED_GAGS, NEED_JB,GO_AWAY, DO_TRICK,')
Actions = Enum('FEED, SCRATCH,ATTENDED_START, ATTENDED_STOP,ATTENDING_START, ATTENDING_STOP,CHANGE_ZONE, LOGOUT,GARDEN')

class PetObserve:

    def isValid(self):
        return 1

    def isForgettable(self):
        return 0

    def _influence(self, petBrain):
        petBrain._handleGenericObserve(self)

    def __repr__(self):
        return '%s()' % self.__class__.__name__


class PetActionObserve(PetObserve):

    def __init__(self, action, avId, data = None):
        self.action = action
        self.avId = avId
        self.data = data

    def getAction(self):
        return self.action

    def getAvId(self):
        return self.avId

    def getData(self):
        return self.data

    def _influence(self, petBrain):
        petBrain._handleActionObserve(self)

    def __repr__(self):
        return '%s(%s,%s)' % (self.__class__.__name__, Actions.getString(self.action), self.avId)


class PetPhraseObserve(PetObserve):

    def __init__(self, petPhrase, avId):
        self.petPhrase = petPhrase
        self.avId = avId

    def getPetPhrase(self):
        return self.petPhrase

    def getAvId(self):
        return self.avId

    def isForgettable(self):
        return 1

    def _influence(self, petBrain):
        petBrain._handlePhraseObserve(self)

    def __repr__(self):
        return '%s(%s,%s)' % (self.__class__.__name__, Phrases.getString(self.petPhrase), self.avId)


class SCObserve(PetPhraseObserve):

    def __init__(self, msgId, petPhrase, avId):
        self.msgId = msgId
        PetPhraseObserve.__init__(self, petPhrase, avId)

    def isValid(self):
        return self.petPhrase is not None


class TrickRequestObserve(PetPhraseObserve):

    def __init__(self, trickId, avId):
        self.trickId = trickId
        PetPhraseObserve.__init__(self, Phrases.DO_TRICK, avId)

    def isForgettable(self):
        return 0

    def getTrickId(self):
        return self.trickId


OP = Phrases
_scPhrase2petPhrase = {1: OP.YES,
 2: OP.NO,
 3: OP.SOOTHE,
 100: OP.HI,
 101: OP.HI,
 102: OP.HI,
 103: OP.HI,
 104: OP.HI,
 105: OP.HI,
 107: OP.HI,
 108: OP.HI,
 200: OP.BYE,
 201: OP.BYE,
 202: OP.BYE,
 203: OP.BYE,
 204: OP.BYE,
 205: OP.BYE,
 206: OP.BYE,
 207: OP.BYE,
 300: OP.HAPPY,
 301: OP.HAPPY,
 302: OP.HAPPY,
 303: OP.HAPPY,
 304: OP.HAPPY,
 305: OP.HAPPY,
 306: OP.HAPPY,
 307: OP.HAPPY,
 308: OP.HAPPY,
 309: OP.HAPPY,
 310: OP.HAPPY,
 311: OP.HAPPY,
 312: OP.HAPPY,
 313: OP.HAPPY,
 314: OP.HAPPY,
 315: OP.HAPPY,
 400: OP.SAD,
 401: OP.SAD,
 402: OP.SAD,
 403: OP.SAD,
 404: OP.SAD,
 405: OP.SAD,
 406: OP.SAD,
 407: OP.NO,
 410: OP.NEED_LAFF,
 500: OP.FRIENDLY,
 505: OP.PRAISE,
 506: OP.HAPPY,
 507: OP.FRIENDLY,
 508: OP.FRIENDLY,
 509: OP.FRIENDLY,
 510: OP.QUESTION,
 511: OP.QUESTION,
 513: OP.QUESTION,
 514: OP.NEED_LAFF,
 600: OP.PRAISE,
 601: OP.PRAISE,
 602: OP.PRAISE,
 603: OP.PRAISE,
 700: OP.PRAISE,
 701: OP.PRAISE,
 900: OP.CRITICISM,
 901: OP.CRITICISM,
 902: OP.CRITICISM,
 903: OP.CRITICISM,
 904: OP.CRITICISM,
 905: OP.CRITICISM,
 1006: OP.FOLLOW_ME,
 1007: OP.STAY,
 1010: OP.STAY,
 1015: OP.STAY,
 1201: OP.CRITICISM,
 1300: OP.NEED_LAFF,
 1400: OP.HURRY,
 1404: OP.PRAISE,
 1405: OP.PRAISE,
 1413: OP.NEED_GAGS,
 1414: OP.NEED_LAFF,
 1601: OP.NEED_JB,
 1603: OP.HURRY,
 1605: OP.LETS_PLAY,
 1606: OP.LETS_PLAY,
 21000: OP.COME,
 21001: OP.COME,
 21002: OP.STAY,
 21003: OP.PRAISE,
 21004: OP.PRAISE,
 21005: OP.PRAISE}
for scId in PetTricks.ScId2trickId:
    _scPhrase2petPhrase[scId] = OP.DO_TRICK

del OP

def getSCObserve(msgId, speakerDoId):
    phrase = _scPhrase2petPhrase.get(msgId)
    if phrase == Phrases.DO_TRICK:
        trickId = PetTricks.ScId2trickId[msgId]
        return TrickRequestObserve(trickId, speakerDoId)
    return SCObserve(msgId, phrase, speakerDoId)
