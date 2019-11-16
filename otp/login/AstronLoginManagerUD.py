import anydbm
import dumbdbm
import sys
import time

from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectGlobalUD import DistributedObjectGlobalUD
from direct.distributed.PyDatagram import *

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

        # send dummy login response
        import json
        a = json.dumps({})
        self.loginManager.sendUpdateToChannel(self.sender, 'loginResponse', [a])


class AstronLoginManagerUD(DistributedObjectGlobalUD):
    notify = DirectNotifyGlobal.directNotify.newCategory('AstronLoginManagerUD')

    def __init__(self, air):
        DistributedObjectGlobalUD.__init__(self, air)
        self.accountDb = None
        self.sender2loginOperation = {}

    def announceGenerate(self):
        DistributedObjectGlobalUD.announceGenerate(self)

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
