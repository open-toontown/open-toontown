import dbm
import json
import time
from datetime import datetime

from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectGlobalUD import DistributedObjectGlobalUD
from direct.distributed.PyDatagram import *

from toontown.makeatoon.NameGenerator import NameGenerator
from toontown.toon.ToonDNA import ToonDNA
from toontown.toonbase import TTLocalizer


class AccountDB:
    """
    AccountDB is the base class for all account database interface implementations.
    """

    def __init__(self, loginManager):
        self.loginManager = loginManager

        # Setup the dbm:
        accountDbFile = config.GetString('accountdb-local-file', 'astron/databases/accounts.db')
        self.dbm = dbm.open(accountDbFile, 'c')

    def lookup(self, playToken, callback):
        raise NotImplementedError('lookup')  # Must be overridden by subclass.

    def storeAccountId(self, databaseId, accountId, callback):
        self.dbm[databaseId] = str(accountId)
        if hasattr(self.dbm, 'sync') and self.dbm.sync:
            self.dbm.sync()
            callback(True)
        else:
            self.loginManager.notify.warning('Unable to associate user %s with account %s!' % (databaseId, accountId))
            callback(False)


class DeveloperAccountDB(AccountDB):

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


class GameOperation:

    def __init__(self, loginManager, sender):
        self.loginManager = loginManager
        self.sender = sender
        self.callback = None

    def setCallback(self, callback):
        self.callback = callback

    def _handleDone(self):
        if self.__class__.__name__ == 'LoginOperation':
            del self.loginManager.sender2loginOperation[self.sender]
        else:
            del self.loginManager.account2operation[self.sender]


class LoginOperation(GameOperation):

    def __init__(self, loginManager, sender):
        GameOperation.__init__(self, loginManager, sender)
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
        self.loginManager.air.dbInterface.queryObject(self.loginManager.air.dbId, self.accountId,
                                                      self.__handleAccountRetrieved)

    def __handleAccountRetrieved(self, dclass, fields):
        if dclass != self.loginManager.air.dclassesByName['AstronAccountUD']:
            # TODO: Kill the connection
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

        self.loginManager.air.dbInterface.createObject(self.loginManager.air.dbId,
                                                       self.loginManager.air.dclassesByName['AstronAccountUD'],
                                                       self.account, self.__handleAccountCreated)

    def __handleAccountCreated(self, accountId):
        if not accountId:
            # TODO: Kill the connection
            return

        self.accountId = accountId
        self.__storeAccountId()

    def __storeAccountId(self):
        self.loginManager.accountDb.storeAccountId(self.databaseId, self.accountId, self.__handleAccountIdStored)

    def __handleAccountIdStored(self, success=True):
        if not success:
            # TODO: Kill the connection
            return

        self.__handleSetAccount()

    def __handleSetAccount(self):
        # if somebody's already logged into this account, disconnect them
        datagram = PyDatagram()
        datagram.addServerHeader(self.loginManager.GetAccountConnectionChannel(self.accountId),
                                 self.loginManager.air.ourChannel, CLIENTAGENT_EJECT)
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
        datagram.addChannel(self.accountId << 32)  # accountId is in high 32 bits, 0 in low (no avatar).
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
        self._handleDone()

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


class AvatarOperation(GameOperation):

    def __init__(self, loginManager, sender):
        GameOperation.__init__(self, loginManager, sender)
        self.account = None
        self.avList = []

    def start(self):
        self.__handleRetrieveAccount()

    def __handleRetrieveAccount(self):
        self.loginManager.air.dbInterface.queryObject(self.loginManager.air.dbId, self.sender,
                                                      self.__handleAccountRetrieved)

    def __handleAccountRetrieved(self, dclass, fields):
        if dclass != self.loginManager.air.dclassesByName['AstronAccountUD']:
            # TODO: Kill the connection
            return

        # Set the account & avList:
        self.account = fields
        self.avList = self.account['ACCOUNT_AV_SET']

        # Sanitize the avList, just in case it is too long/short:
        self.avList = self.avList[:6]
        self.avList += [0] * (6 - len(self.avList))

        # We're done; run the callback, if any:
        if self.callback is not None:
            self.callback()


class GetAvatarsOperation(AvatarOperation):

    def __init__(self, loginManager, sender):
        AvatarOperation.__init__(self, loginManager, sender)
        self.setCallback(self._handleQueryAvatars)
        self.pendingAvatars = None
        self.avatarFields = None

    def _handleQueryAvatars(self):
        self.pendingAvatars = set()
        self.avatarFields = {}
        for avId in self.avList:
            if avId:
                self.pendingAvatars.add(avId)

                def response(dclass, fields, avId=avId):
                    if dclass != self.loginManager.air.dclassesByName['DistributedToonUD']:
                        # TODO: Kill the connection
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
        for avId, fields in list(self.avatarFields.items()):
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
        self._handleDone()


class CreateAvatarOperation(GameOperation):

    def __init__(self, loginManager, sender):
        GameOperation.__init__(self, loginManager, sender)
        self.avPosition = None
        self.avDNA = None

    def start(self, avDNA, avPosition):
        if avPosition >= 6:
            # TODO: Kill the connection
            return

        dna = ToonDNA()
        valid = dna.isValidNetString(avDNA)
        if not valid:
            # TODO: Kill the connection
            return

        self.avPosition = avPosition
        self.avDNA = avDNA

        self.__handleRetrieveAccount()

    def __handleRetrieveAccount(self):
        self.loginManager.air.dbInterface.queryObject(self.loginManager.air.dbId, self.sender,
                                                      self.__handleAccountRetrieved)

    def __handleAccountRetrieved(self, dclass, fields):
        if dclass != self.loginManager.air.dclassesByName['AstronAccountUD']:
            # TODO: Kill the connection
            return

        self.account = fields
        self.avList = self.account['ACCOUNT_AV_SET']
        self.avList = self.avList[:6]
        self.avList += [0] * (6 - len(self.avList))
        if self.avList[self.avPosition]:
            # TODO: Kill the connection
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

        self.loginManager.air.dbInterface.createObject(self.loginManager.air.dbId,
                                                       self.loginManager.air.dclassesByName['DistributedToonUD'],
                                                       toonFields, self.__handleToonCreated)

    def __handleToonCreated(self, avId):
        if not avId:
            # TODO: Kill the connection
            return

        self.avId = avId
        self.__handleStoreAvatar()

    def __handleStoreAvatar(self):
        self.avList[self.avPosition] = self.avId
        self.loginManager.air.dbInterface.updateObject(self.loginManager.air.dbId, self.sender,
                                                       self.loginManager.air.dclassesByName['AstronAccountUD'],
                                                       {'ACCOUNT_AV_SET': self.avList},
                                                       {'ACCOUNT_AV_SET': self.account['ACCOUNT_AV_SET']},
                                                       self.__handleAvatarStored)

    def __handleAvatarStored(self, fields):
        if fields:
            # TODO: Kill the connection
            return

        self.loginManager.sendUpdateToAccountId(self.sender, 'createAvatarResponse', [self.avId])
        self._handleDone()


class SetNamePatternOperation(AvatarOperation):

    def __init__(self, loginManager, sender):
        AvatarOperation.__init__(self, loginManager, sender)
        self.setCallback(self.__handleRetrieveAvatar)
        self.avId = None
        self.pattern = None

    def start(self, avId, pattern):
        self.avId = avId
        self.pattern = pattern
        AvatarOperation.start(self)

    def __handleRetrieveAvatar(self):
        if self.avId and self.avId not in self.avList:
            # TODO: Kill the connection
            return

        self.loginManager.air.dbInterface.queryObject(self.loginManager.air.dbId, self.avId,
                                                      self.__handleAvatarRetrieved)

    def __handleAvatarRetrieved(self, dclass, fields):
        if dclass != self.loginManager.air.dclassesByName['DistributedToonUD']:
            # TODO: Kill the connection
            return

        if fields['WishNameState'][0] != 'OPEN':
            # TODO: Kill the connection
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

        self.loginManager.air.dbInterface.updateObject(self.loginManager.air.dbId, self.avId,
                                                       self.loginManager.air.dclassesByName['DistributedToonUD'],
                                                       {'WishNameState': ('LOCKED',),
                                                        'WishName': ('',),
                                                        'setName': (name,)})

        self.loginManager.sendUpdateToAccountId(self.sender, 'namePatternAnswer', [self.avId, 1])
        self._handleDone()


class SetNameTypedOperation(AvatarOperation):

    def __init__(self, loginManager, sender):
        AvatarOperation.__init__(self, loginManager, sender)
        self.setCallback(self.__handleRetrieveAvatar)
        self.avId = None
        self.name = None

    def start(self, avId, name):
        self.avId = avId
        self.name = name
        if self.avId:
            AvatarOperation.start(self)
            return

        self.__handleJudgeName()

    def __handleRetrieveAvatar(self):
        if self.avId and self.avId not in self.avList:
            # TODO: Kill the connection
            return

        self.loginManager.air.dbInterface.queryObject(self.loginManager.air.dbId, self.avId,
                                                      self.__handleAvatarRetrieved)

    def __handleAvatarRetrieved(self, dclass, fields):
        if dclass != self.loginManager.air.dclassesByName['DistributedToonUD']:
            # TODO: Kill the connection
            return

        if fields['WishNameState'][0] != 'OPEN':
            # TODO: Kill the connection
            return

        self.__handleJudgeName()

    def __handleJudgeName(self):
        status = 1  # TODO Make this useful
        if self.avId and status:
            self.loginManager.air.dbInterface.updateObject(self.loginManager.air.dbId, self.avId,
                                                           self.loginManager.air.dclassesByName['DistributedToonUD'],
                                                           {'WishNameState': ('PENDING',),
                                                            'WishName': (self.name,)})

        self.loginManager.sendUpdateToAccountId(self.sender, 'nameTypedResponse', [self.avId, status])
        self._handleDone()


class AcknowledgeNameOperation(AvatarOperation):

    def __init__(self, loginManager, sender):
        AvatarOperation.__init__(self, loginManager, sender)
        self.setCallback(self.__handleGetTargetAvatar)
        self.avId = None

    def start(self, avId):
        self.avId = avId
        AvatarOperation.start(self)

    def __handleGetTargetAvatar(self):
        if self.avId not in self.avList:
            # TODO: Kill the connection
            return

        self.loginManager.air.dbInterface.queryObject(self.loginManager.air.dbId, self.avId,
                                                      self.__handleAvatarRetrieved)

    def __handleAvatarRetrieved(self, dclass, fields):
        if dclass != self.loginManager.air.dclassesByName['DistributedToonUD']:
            return

        wishNameState = fields['WishNameState'][0]
        wishName = fields['WishName'][0]
        name = fields['setName'][0]
        if wishNameState == 'APPROVED':
            wishNameState = 'LOCKED'
            name = wishName
            wishName = ''
        elif wishNameState == 'REJECTED':
            wishNameState = 'OPEN'
            wishName = ''
        else:
            return

        self.loginManager.air.dbInterface.updateObject(self.loginManager.air.dbId, self.avId,
                                                       self.loginManager.air.dclassesByName['DistributedToonUD'],
                                                       {'WishNameState': (wishNameState,),
                                                        'WishName': (wishName,),
                                                        'setName': (name,)},
                                                       {'WishNameState': fields['WishNameState'],
                                                        'WishName': fields['WishName'],
                                                        'setName': fields['setName']})

        self.loginManager.sendUpdateToAccountId(self.sender, 'acknowledgeAvatarNameResponse', [])
        self._handleDone()


class RemoveAvatarOperation(GetAvatarsOperation):

    def __init__(self, loginManager, sender):
        GetAvatarsOperation.__init__(self, loginManager, sender)
        self.setCallback(self.__handleRemoveAvatar)
        self.avId = None

    def start(self, avId):
        self.avId = avId
        GetAvatarsOperation.start(self)

    def __handleRemoveAvatar(self):
        if self.avId not in self.avList:
            # TODO: Kill the connection
            return

        index = self.avList.index(self.avId)
        self.avList[index] = 0
        avatarsRemoved = list(self.account.get('ACCOUNT_AV_SET_DEL', []))
        avatarsRemoved.append([self.avId, int(time.time())])
        estateId = self.account.get('ESTATE_ID', 0)
        if estateId != 0:
            self.loginManager.air.dbInterface.updateObject(self.loginManager.air.dbId, estateId,
                                                           self.loginManager.air.dclassesByName['DistributedEstateAI'],
                                                           {'setSlot%sToonId' % index: [0],
                                                            'setSlot%sItems' % index: [[]]})

        self.loginManager.air.dbInterface.updateObject(self.loginManager.air.dbId, self.sender,
                                                       self.loginManager.air.dclassesByName['AstronAccountUD'],
                                                       {'ACCOUNT_AV_SET': self.avList,
                                                        'ACCOUNT_AV_SET_DEL': avatarsRemoved},
                                                       {'ACCOUNT_AV_SET': self.account['ACCOUNT_AV_SET'],
                                                        'ACCOUNT_AV_SET_DEL': self.account['ACCOUNT_AV_SET_DEL']},
                                                       self.__handleAvatarRemoved)

    def __handleAvatarRemoved(self, fields):
        if fields:
            # TODO: Kill the connection
            return

        self._handleQueryAvatars()


class LoadAvatarOperation(AvatarOperation):

    def __init__(self, loginManager, sender):
        AvatarOperation.__init__(self, loginManager, sender)
        self.setCallback(self.__handleGetTargetAvatar)
        self.avId = None

    def start(self, avId):
        self.avId = avId
        AvatarOperation.start(self)

    def __handleGetTargetAvatar(self):
        if self.avId not in self.avList:
            return

        self.loginManager.air.dbInterface.queryObject(self.loginManager.air.dbId, self.avId,
                                                      self.__handleAvatarRetrieved)

    def __handleAvatarRetrieved(self, dclass, fields):
        if dclass != self.loginManager.air.dclassesByName['DistributedToonUD']:
            return

        self.avatar = fields
        self.__handleSetAvatar()

    def __handleSetAvatar(self):
        channel = self.loginManager.GetAccountConnectionChannel(self.sender)

        cleanupDatagram = PyDatagram()
        cleanupDatagram.addServerHeader(self.avId, channel, STATESERVER_OBJECT_DELETE_RAM)
        cleanupDatagram.addUint32(self.avId)
        datagram = PyDatagram()
        datagram.addServerHeader(channel, self.loginManager.air.ourChannel, CLIENTAGENT_ADD_POST_REMOVE)
        datagram.addUint16(cleanupDatagram.getLength())
        datagram.appendData(cleanupDatagram.getMessage())
        self.loginManager.air.send(datagram)

        self.loginManager.air.sendActivate(self.avId, 0, 0, self.loginManager.air.dclassesByName['DistributedToonUD'])

        datagram = PyDatagram()
        datagram.addServerHeader(channel, self.loginManager.air.ourChannel, CLIENTAGENT_OPEN_CHANNEL)
        datagram.addChannel(self.loginManager.GetPuppetConnectionChannel(self.avId))
        self.loginManager.air.send(datagram)

        self.loginManager.air.clientAddSessionObject(channel, self.avId)

        datagram = PyDatagram()
        datagram.addServerHeader(channel, self.loginManager.air.ourChannel, CLIENTAGENT_SET_CLIENT_ID)
        datagram.addChannel(self.sender << 32 | self.avId)  # accountId in high 32 bits, avatar in low.
        self.loginManager.air.send(datagram)

        self.loginManager.air.setOwner(self.avId, channel)

        self._handleDone()


class UnloadAvatarOperation(GameOperation):

    def __init__(self, loginManager, sender):
        GameOperation.__init__(self, loginManager, sender)
        self.avId = None

    def start(self, avId):
        self.avId = avId
        self.__handleUnloadAvatar()

    def __handleUnloadAvatar(self):
        channel = self.loginManager.GetAccountConnectionChannel(self.sender)

        datagram = PyDatagram()
        datagram.addServerHeader(channel, self.loginManager.air.ourChannel, CLIENTAGENT_CLEAR_POST_REMOVES)
        self.loginManager.air.send(datagram)

        datagram = PyDatagram()
        datagram.addServerHeader(channel, self.loginManager.air.ourChannel, CLIENTAGENT_CLOSE_CHANNEL)
        datagram.addChannel(self.loginManager.GetPuppetConnectionChannel(self.avId))
        self.loginManager.air.send(datagram)

        datagram = PyDatagram()
        datagram.addServerHeader(channel, self.loginManager.air.ourChannel, CLIENTAGENT_SET_CLIENT_ID)
        datagram.addChannel(self.sender << 32)  # accountId in high 32 bits, no avatar in low.
        self.loginManager.air.send(datagram)

        datagram = PyDatagram()
        datagram.addServerHeader(channel, self.loginManager.air.ourChannel, CLIENTAGENT_REMOVE_SESSION_OBJECT)
        datagram.addUint32(self.avId)
        self.loginManager.air.send(datagram)

        datagram = PyDatagram()
        datagram.addServerHeader(self.avId, channel, STATESERVER_OBJECT_DELETE_RAM)
        datagram.addUint32(self.avId)
        self.loginManager.air.send(datagram)

        self._handleDone()


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

    def runLoginOperation(self, playToken):
        # Runs a login operation on the sender. First, get the sender:
        sender = self.air.getMsgSender()

        # Is the sender already logged in?
        if sender >> 32:
            # TODO kill connection
            return

        # Is the sender already logging in?
        if sender in list(self.sender2loginOperation.keys()):
            # TODO kill connection
            return

        # Run the login operation:
        newLoginOperation = LoginOperation(self, sender)
        self.sender2loginOperation[sender] = newLoginOperation
        newLoginOperation.start(playToken)

    def runGameOperation(self, operationType, *args):
        # Runs a game operation on the sender. First, get the sender:
        sender = self.air.getAccountIdFromSender()
        if not sender:
            # Sender doesn't exist; not logged in.
            # TODO KILL CONNECTION
            return

        if sender in self.account2operation:
            # Sender is already currently running a game operation.
            # TODO KILL CONNECTION
            return

        # Run the game operation:
        newOperation = operationType(self, sender)
        self.account2operation[sender] = newOperation
        newOperation.start(*args)

    def requestLogin(self, playToken):
        # Someone wants to log in to the game; run a LoginOperation:
        self.runLoginOperation(playToken)

    def requestAvatarList(self):
        # Someone wants their avatar list; run a GetAvatarsOperation:
        self.runGameOperation(GetAvatarsOperation)

    def createAvatar(self, avDNA, avPosition):
        # Someone wants to create a new avatar; run a CreateAvatarOperation:
        self.runGameOperation(CreateAvatarOperation, avDNA, avPosition)

    def setNamePattern(self, avId, p1, f1, p2, f2, p3, f3, p4, f4):
        # Someone wants to use a pattern name; run a SetNamePatternOperation:
        self.runGameOperation(SetNamePatternOperation, avId, [(p1, f1), (p2, f2),
                                                              (p3, f3), (p4, f4)])

    def setNameTyped(self, avId, name):
        # Someone has typed a name; run a SetNameTypedOperation:
        self.runGameOperation(SetNameTypedOperation, avId, name)

    def acknowledgeAvatarName(self, avId):
        # Someone has acknowledged their name; run an AcknowledgeNameOperation:
        self.runGameOperation(AcknowledgeNameOperation, avId)

    def requestRemoveAvatar(self, avId):
        # Someone is requesting to have an avatar removed; run a RemoveAvatarOperation:
        self.runGameOperation(RemoveAvatarOperation, avId)

    def requestPlayAvatar(self, avId):
        # Someone is requesting to play on an avatar.
        # First, let's get the sender's avId & accId:
        currentAvId = self.air.getAvatarIdFromSender()
        accId = self.air.getAccountIdFromSender()
        if currentAvId and avId:
            # todo: kill the connection
            return
        elif not currentAvId and not avId:
            # I don't think we need to do anything extra here
            return

        if avId:
            # If the avId is not a NoneType, that means the client wants
            # to load an avatar; run a LoadAvatarOperation.
            self.runGameOperation(LoadAvatarOperation, avId)
        else:
            # Otherwise, the client wants to unload the avatar; run an UnloadAvatarOperation.
            self.runGameOperation(UnloadAvatarOperation, currentAvId)
