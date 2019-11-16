import anydbm
import dumbdbm
import json
import sys
from datetime import datetime
import time

from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectGlobalUD import DistributedObjectGlobalUD
from direct.distributed.PyDatagram import *
from toontown.toon.ToonDNA import ToonDNA
from toontown.toonbase import TTLocalizer
from toontown.makeatoon.NameGenerator import NameGenerator

class AccountDB:
    """
    AccountDB is the base class for all account database interface implementations.
    """
    notify = DirectNotifyGlobal.directNotify.newCategory('AccountDB')

    def __init__(self, loginManager):
        self.loginManager = loginManager

        # Setup the dbm:
        accountDbFile = config.GetString('accountdb-local-file', 'astron/databases/accounts.db')
        if sys.platform == 'darwin':  # macOS
            dbm = dumbdbm
        else:
            dbm = anydbm

        self.dbm = dbm.open(accountDbFile, 'c')

    def lookup(self, playToken, callback):
        raise NotImplementedError('lookup')  # Must be overridden by subclass.

    def storeAccountId(self, databaseId, accountId, callback):
        self.dbm[databaseId] = str(accountId)
        if hasattr(self.dbm, 'sync') and self.dbm.sync:
            self.dbm.sync()
            callback(True)
        else:
            self.notify.warning('Unable to associate user %s with account %s!' % (databaseId, accountId))
            callback(False)


class DeveloperAccountDB(AccountDB):
    notify = DirectNotifyGlobal.directNotify.newCategory('DeveloperAccountDB')

    def lookup(self, playToken, callback):
        # Check if this play token exists in the dbm:
        if str(playToken) not in self.dbm:
            # It is not, so we'll associate them with a brand new account object.
            callback({'success': True,
                      'accountId': 0,
                      'databaseId': playToken})
        else:
            # We already have an account object, so we'll just return what we have.
            callback({'success': True,
                      'accountId': int(self.dbm[playToken]),
                      'databaseId': playToken})


class LoginOperation:
    notify = DirectNotifyGlobal.directNotify.newCategory('LoginOperation')

    def __init__(self, loginManager, sender):
        self.loginManager = loginManager
        self.sender = sender
        self.playToken = ''
        self.databaseId = 0
        self.accountId = 0
        self.account = None

    def start(self, playToken):
        self.playToken = playToken
        self.loginManager.accountDb.lookup(playToken, self.__handleLookup)

    def __handleLookup(self, result):
        if not result.get('success'):
            # TODO: Kill the connection
            return

        self.databaseId = result.get('databaseId', 0)
        accountId = result.get('accountId', 0)
        if accountId:
            self.accountId = accountId
            self.__handleRetrieveAccount()
        else:
            self.__handleCreateAccount()

    def __handleRetrieveAccount(self):
        self.loginManager.air.dbInterface.queryObject(self.loginManager.air.dbId, self.accountId, self.__handleAccountRetrieved)

    def __handleAccountRetrieved(self, dclass, fields):
        if dclass != self.loginManager.air.dclassesByName['AstronAccountUD']:
            print 'no uwu'
            return

        self.account = fields
        self.__handleSetAccount()

    def __handleCreateAccount(self):
        self.account = {'ACCOUNT_AV_SET': [0] * 6,
                        'ESTATE_ID': 0,
                        'ACCOUNT_AV_SET_DEL': [],
                        'CREATED': time.ctime(),
                        'LAST_LOGIN': time.ctime(),
                        'ACCOUNT_ID': str(self.databaseId)}

        self.loginManager.air.dbInterface.createObject(self.loginManager.air.dbId, self.loginManager.air.dclassesByName['AstronAccountUD'], self.account, self.__handleAccountCreated)

    def __handleAccountCreated(self, accountId):
        if not accountId:
            # FAILURE!!!!!
            return

        self.accountId = accountId
        self.__storeAccountId()

    def __storeAccountId(self):
        self.loginManager.accountDb.storeAccountId(self.databaseId, self.accountId, self.__handleAccountIdStored)

    def __handleAccountIdStored(self, success=True):
        if not success:
            # FAILURE!!!!!!!!!!!!
            return

        self.__handleSetAccount()

    def __handleSetAccount(self):
        # if somebody's already logged into this account, disconnect them
        datagram = PyDatagram()
        datagram.addServerHeader(self.loginManager.GetAccountConnectionChannel(self.accountId), self.loginManager.air.ourChannel, CLIENTAGENT_EJECT)
        datagram.addUint16(100)
        datagram.addString('This account has been logged in elsewhere.')
        self.loginManager.air.send(datagram)

        # add connection to account channel
        datagram = PyDatagram()
        datagram.addServerHeader(self.sender, self.loginManager.air.ourChannel, CLIENTAGENT_OPEN_CHANNEL)
        datagram.addChannel(self.loginManager.GetAccountConnectionChannel(self.accountId))
        self.loginManager.air.send(datagram)

        # set sender channel to represent account affiliation
        datagram = PyDatagram()
        datagram.addServerHeader(self.sender, self.loginManager.air.ourChannel, CLIENTAGENT_SET_CLIENT_ID)
        datagram.addChannel(self.accountId << 32) # accountId is in high 32 bits, 0 in low (no avatar).
        self.loginManager.air.send(datagram)

        # set client state to established, thus un-sandboxing the sender
        self.loginManager.air.setClientState(self.sender, 2)

        responseData = {
            'returnCode': 0,
            'respString': '',
            'accountNumber': self.sender,
            'createFriendsWithChat': 'YES',
            'chatCodeCreationRule': 'YES',
            'access': 'FULL',
            'WhiteListResponse': 'YES',
            'lastLoggedInStr': self.getLastLoggedInStr(),
            'accountDays': self.getAccountDays(),
            'serverTime': int(time.time()),
            'toonAccountType': 'NO_PARENT_ACCOUNT',
            'userName': str(self.databaseId)
        }
        responseBlob = json.dumps(responseData)
        self.loginManager.sendUpdateToChannel(self.sender, 'loginResponse', [responseBlob])
        del self.loginManager.sender2loginOperation[self.sender]

    def getLastLoggedInStr(self):
        return ''  # TODO

    def getAccountCreationDate(self):
        accountCreationDate = self.account.get('CREATED', '')
        try:
            accountCreationDate = datetime.fromtimestamp(time.mktime(time.strptime(accountCreationDate)))
        except ValueError:
            accountCreationDate = ''

        return accountCreationDate

    def getAccountDays(self):
        accountCreationDate = self.getAccountCreationDate()
        accountDays = -1
        if accountCreationDate:
            now = datetime.fromtimestamp(time.mktime(time.strptime(time.ctime())))
            accountDays = abs((now - accountCreationDate).days)

        return accountDays


class GetAvatarsOperation:

    def __init__(self, loginManager, sender):
        self.loginManager = loginManager
        self.sender = sender
        self.account = None
        self.avList = []
        self.pendingAvatars = None
        self.avatarFields = None

    def start(self):
        self.loginManager.air.dbInterface.queryObject(self.loginManager.air.dbId, self.sender, self.__handleAccountRetrieved)

    def __handleAccountRetrieved(self, dclass, fields):
        if dclass != self.loginManager.air.dclassesByName['AstronAccountUD']:
            # no uwu
            return

        self.account = fields
        self.avList = self.account['ACCOUNT_AV_SET']
        self.avList = self.avList[:6]
        self.avList += [0] * (6 - len(self.avList))
        self.__handleQueryAvatars()

    def __handleQueryAvatars(self):
        self.pendingAvatars = set()
        self.avatarFields = {}
        for avId in self.avList:
            if avId:
                self.pendingAvatars.add(avId)
                def response(dclass, fields, avId=avId):
                    if dclass != self.loginManager.air.dclassesByName['DistributedToonUD']:
                        # mayonnaise
                        return

                    self.avatarFields[avId] = fields
                    self.pendingAvatars.remove(avId)
                    if not self.pendingAvatars:
                        self.__handleSendAvatars()

                self.loginManager.air.dbInterface.queryObject(self.loginManager.air.dbId, avId, response)

        if not self.pendingAvatars:
            self.__handleSendAvatars()

    def __handleSendAvatars(self):
        potentialAvatars = []
        for avId, fields in self.avatarFields.items():
            index = self.avList.index(avId)
            wishNameState = fields.get('WishNameState', [''])[0]
            name = fields['setName'][0]
            nameState = 0
            if wishNameState == 'OPEN':
                nameState = 1
            elif wishNameState == 'PENDING':
                nameState = 2
            elif wishNameState == 'APPROVED':
                nameState = 3
                name = fields['WishName'][0]
            elif wishNameState == 'REJECTED':
                nameState = 4
            elif wishNameState == 'LOCKED':
                nameState = 0
            else:
                # unknown name state.
                nameState = 0

            potentialAvatars.append([avId, name, fields['setDNAString'][0], index, nameState])

        self.loginManager.sendUpdateToAccountId(self.sender, 'avatarListResponse', [potentialAvatars])
        del self.loginManager.account2operation[self.sender]


class CreateAvatarOperation:
    notify = DirectNotifyGlobal.directNotify.newCategory('CreateAvatarOperation')

    def __init__(self, loginManager, sender):
        self.loginManager = loginManager
        self.sender = sender
        self.avPosition = None
        self.avDNA = None

    def start(self, avDNA, avPosition):
        if avPosition >= 6:
            # NO!!!!!!!
            return

        valid = ToonDNA().isValidNetString(avDNA)
        if not valid:
            # time to eat paste
            return

        self.avPosition = avPosition
        self.avDNA = avDNA

        self.__handleRetrieveAccount()

    def __handleRetrieveAccount(self):
        self.loginManager.air.dbInterface.queryObject(self.loginManager.air.dbId, self.sender, self.__handleAccountRetrieved)

    def __handleAccountRetrieved(self, dclass, fields):
        if dclass != self.loginManager.air.dclassesByName['AstronAccountUD']:
            # no uwu
            return

        self.account = fields
        self.avList = self.account['ACCOUNT_AV_SET']
        self.avList = self.avList[:6]
        self.avList += [0] * (6 - len(self.avList))
        if self.avList[self.avPosition]:
            # my leg
            return

        self.__handleCreateAvatar()

    def __handleCreateAvatar(self):
        dna = ToonDNA()
        dna.makeFromNetString(self.avDNA)
        colorString = TTLocalizer.NumToColor[dna.headColor]
        animalType = TTLocalizer.AnimalToSpecies[dna.getAnimal()]
        name = ' '.join((colorString, animalType))
        toonFields = {'setName': (name,),
                      'WishNameState': ('OPEN',),
                      'WishName': ('',),
                      'setDNAString': (self.avDNA,),
                      'setDISLid': (self.sender,)}

        self.loginManager.air.dbInterface.createObject(self.loginManager.air.dbId, self.loginManager.air.dclassesByName['DistributedToonUD'], toonFields, self.__handleToonCreated)

    def __handleToonCreated(self, avId):
        if not avId:
            # WHAT!
            return

        self.avId = avId
        self.__handleStoreAvatar()

    def __handleStoreAvatar(self):
        self.avList[self.avPosition] = self.avId
        self.loginManager.air.dbInterface.updateObject(self.loginManager.air.dbId, self.sender, self.loginManager.air.dclassesByName['AstronAccountUD'],
                                                   {'ACCOUNT_AV_SET': self.avList},
                                                   {'ACCOUNT_AV_SET': self.account['ACCOUNT_AV_SET']},
                                                   self.__handleAvatarStored)

    def __handleAvatarStored(self, fields):
        if fields:
            # What happen!
            # Someone set up us the bomb.
            # We get signal.
            # What!
            return

        self.loginManager.sendUpdateToAccountId(self.sender, 'createAvatarResponse', [self.avId])
        del self.loginManager.account2operation[self.sender]


class SetNamePatternOperation:
    notify = DirectNotifyGlobal.directNotify.newCategory('SetNamePatternOperation')

    def __init__(self, loginManager, sender):
        self.loginManager = loginManager
        self.sender = sender
        self.avId = None
        self.pattern = None

    def start(self, avId, pattern):
        self.avId = avId
        self.pattern = pattern
        self.__handleRetrieveAccount()

    def __handleRetrieveAccount(self):
        self.loginManager.air.dbInterface.queryObject(self.loginManager.air.dbId, self.sender, self.__handleAccountRetrieved)

    def __handleAccountRetrieved(self, dclass, fields):
        if dclass != self.loginManager.air.dclassesByName['AstronAccountUD']:
            # no uwu
            return

        self.account = fields
        self.avList = self.account['ACCOUNT_AV_SET']
        self.avList = self.avList[:6]
        self.avList += [0] * (6 - len(self.avList))
        self.__handleRetrieveAvatar()

    def __handleRetrieveAvatar(self):
        if self.avId and self.avId not in self.avList:
            # Main screen turn on.
            # It's you!
            return

        self.loginManager.air.dbInterface.queryObject(self.loginManager.air.dbId, self.avId, self.__handleAvatarRetrieved)

    def __handleAvatarRetrieved(self, dclass, fields):
        if dclass != self.loginManager.air.dclassesByName['DistributedToonUD']:
            # How are you gentlemen?
            # All your base are belong to us
            return

        if fields['WishNameState'][0] != 'OPEN':
            # You are on your way to destruction
            # What you say?
            return

        self.__handleSetName()

    def __handleSetName(self):
        parts = []
        for p, f in self.pattern:
            part = self.loginManager.nameGenerator.nameDictionary.get(p, ('', ''))[1]
            if f:
                part = part[:1].upper() + part[1:]
            else:
                part = part.lower()

            parts.append(part)

        parts[2] += parts.pop(3)
        while '' in parts:
            parts.remove('')

        name = ' '.join(parts)

        self.loginManager.air.dbInterface.updateObject(self.loginManager.air.dbId, self.avId, self.loginManager.air.dclassesByName['DistributedToonUD'],
                                                       {'WishNameState': ('LOCKED',),
                                                        'WishName': ('',),
                                                        'setName': (name,)})

        self.loginManager.sendUpdateToAccountId(self.sender, 'namePatternAnswer', [self.avId, 1])
        del self.loginManager.account2operation[self.sender]


class AstronLoginManagerUD(DistributedObjectGlobalUD):
    notify = DirectNotifyGlobal.directNotify.newCategory('AstronLoginManagerUD')

    def __init__(self, air):
        DistributedObjectGlobalUD.__init__(self, air)
        self.nameGenerator = None
        self.accountDb = None
        self.sender2loginOperation = {}
        self.account2operation = {}

    def announceGenerate(self):
        DistributedObjectGlobalUD.announceGenerate(self)

        # This is for processing name patterns.
        self.nameGenerator = NameGenerator()

        # Instantiate the account database backend.
        # TODO: In the future, add more database interfaces & make this configurable.
        self.accountDb = DeveloperAccountDB(self)

    def requestLogin(self, playToken):
        # Get the connection ID:
        sender = self.air.getMsgSender()

        if sender in self.sender2loginOperation.keys():
            # BAD!!!!
            return

        newLoginOperation = LoginOperation(self, sender)
        self.sender2loginOperation[sender] = newLoginOperation
        newLoginOperation.start(playToken)

    # TODO: CLEAN UP ALL THIS CODE!!!!!!!!

    def requestAvatarList(self):
        sender = self.air.getAccountIdFromSender()
        if not sender:
            # TODO KILL CONNECTION
            return

        if sender in self.account2operation:
            # BAD!!!!
            return

        newOperation = GetAvatarsOperation(self, sender)
        self.account2operation[sender] = newOperation
        newOperation.start()

    def createAvatar(self, avDNA, avPosition):
        sender = self.air.getAccountIdFromSender()
        if not sender:
            # TODO KILL CONNECTION
            return

        if sender in self.account2operation:
            # BAD!!!!
            return

        newOperation = CreateAvatarOperation(self, sender)
        self.account2operation[sender] = newOperation
        newOperation.start(avDNA, avPosition)

    def setNamePattern(self, avId, p1, f1, p2, f2, p3, f3, p4, f4):
        sender = self.air.getAccountIdFromSender()
        if not sender:
            # TODO KILL CONNECTION
            return

        if sender in self.account2operation:
            # BAD!!!!
            return

        newOperation = SetNamePatternOperation(self, sender)
        self.account2operation[sender] = newOperation
        newOperation.start(avId, [(p1, f1), (p2, f2),
                                  (p3, f3), (p4, f4)])
