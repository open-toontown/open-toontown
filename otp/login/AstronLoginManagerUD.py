import json
import time
import os
from datetime import datetime

from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectGlobalUD import DistributedObjectGlobalUD
from direct.distributed.PyDatagram import *

from otp.otpbase import OTPGlobals

from toontown.makeatoon.NameGenerator import NameGenerator
from toontown.toon.ToonDNA import ToonDNA
from toontown.toonbase import TTLocalizer


class AccountDB:
    """
    AccountDB is the base class for all account database interface implementations.
    """

    def __init__(self, loginManager):
        self.loginManager = loginManager

    def lookup(self, playToken, callback):
        raise NotImplementedError('lookup')  # Must be overridden by subclass.

    def storeAccountId(self, databaseId, accountId, callback):
        raise NotImplementedError('storeAccountId')  # Must be overridden by subclass.


class DeveloperAccountDB(AccountDB):

    def __init__(self, loginManager):
        AccountDB.__init__(self, loginManager)

        # Setup the accountToId dictionary
        self.accountDbFilePath = config.GetString('accountdb-local-file', 'astron/databases/accounts.json')
        # Load the JSON file if it exists.
        if os.path.exists(self.accountDbFilePath):
            with open(self.accountDbFilePath, 'r') as file:
                self.accountToId = json.load(file)
        else:
            # If not, create a blank file.
            self.accountToId = {}
            with open(self.accountDbFilePath, 'w') as file:
                json.dump(self.accountToId, file)

    def lookup(self, playToken, callback):
        # Check if this play token exists in the accountsToId:
        if playToken not in self.accountToId:
            # It is not, so we'll associate them with a brand new account object.
            # Get the default access level from config.
            accessLevel = config.GetString('default-access-level', "SYSTEM_ADMIN")
            if accessLevel not in OTPGlobals.AccessLevelName2Int:
                self.loginManager.notify.warning(f'Access Level "{accessLevel}" isn\'t defined.  Reverting back to SYSTEM_ADMIN')
                accessLevel = "SYSTEM_ADMIN"

            callback({'success': True,
                      'accountId': 0,
                      'databaseId': playToken,
                      'accessLevel': accessLevel})
        else:
            def handleAccount(dclass, fields):
                if dclass != self.loginManager.air.dclassesByName['AstronAccountUD']:
                    result = {'success': False,
                              'reason': 'Your account object (%s) was not found in the database!' % dclass}
                else:
                    # We already have an account object, so we'll just return what we have.
                    result = {'success': True,
                              'accountId': self.accountToId[playToken],
                              'databaseId': playToken,
                              'accessLevel': fields.get('ACCESS_LEVEL', 'NO_ACCESS')}

                callback(result)

            # Query the account from Astron to verify its existance. We need to get
            # the ACCESS_LEVEL field anyways.
            # TODO: Add a timeout timer?
            self.loginManager.air.dbInterface.queryObject(self.loginManager.air.dbId,
                                                          self.accountToId[playToken], handleAccount,
                                                          self.loginManager.air.dclassesByName['AstronAccountUD'],
                                                          ('ACCESS_LEVEL',))

    def storeAccountId(self, databaseId, accountId, callback):
        if databaseId not in self.accountToId:
            self.accountToId[databaseId] = accountId
            with open(self.accountDbFilePath, 'w') as file:
                json.dump(self.accountToId, file, indent=2)
            callback(True)
        else:
            self.loginManager.notify.warning(f"Attempted to store user {databaseId} with account {accountId} even though it already exists!")
            callback(False)

class GameOperation:

    def __init__(self, loginManager, sender):
        self.loginManager = loginManager
        self.sender = sender
        self.callback = None

    def setCallback(self, callback):
        self.callback = callback

    def _handleDone(self):
        # Deletes the sender from either sender2loginOperation or account2operation
        # depending on the type of operation we are running.
        if self.__class__.__name__ == 'LoginOperation':
            del self.loginManager.sender2loginOperation[self.sender]
        else:
            del self.loginManager.account2operation[self.sender]

    def _handleCloseConnection(self, reason=''):
        # Closes either the sender connection or the sender account
        # depending on the type of operation we are running, and then
        # finishes off this operation.
        if self.__class__.__name__ == 'LoginOperation':
            self.loginManager.closeConnection(self.sender, reason=reason)
        else:
            self.loginManager.closeConnection(self.sender, reason=reason, isAccount=True)

        self._handleDone()


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
        # This is a callback function that will be called by the lookup function
        # of the AstronLoginManager's account DB interface. It processes the
        # lookup function's result & determines which operation should run next.
        if not result.get('success'):
            # The play token was rejected!
            self.loginManager.air.writeServerEvent('play-token-rejected', self.sender, self.playToken)
            self._handleCloseConnection(result.get('reason', 'The accounts database rejected your play token.'))
            return

        # Grab the databaseId, accessLevel, and the accountId from the result.
        self.databaseId = result.get('databaseId', 0)
        self.accessLevel = result.get('accessLevel', 0)
        accountId = result.get('accountId', 0)
        if accountId:
            # There is an account ID, so let's retrieve the associated account.
            self.accountId = accountId
            self.__handleRetrieveAccount()
        else:
            # There is no account ID, so let's create a new account.
            self.__handleCreateAccount()

    def __handleRetrieveAccount(self):
        self.loginManager.air.dbInterface.queryObject(self.loginManager.air.dbId, self.accountId,
                                                      self.__handleAccountRetrieved)

    def __handleAccountRetrieved(self, dclass, fields):
        # Checks if the queried object is valid and if it is, calls
        # the __handleSetAccount function. Otherwise, the connection is closed.
        if dclass != self.loginManager.air.dclassesByName['AstronAccountUD']:
            # This is not an account object! Close the connection.
            self._handleCloseConnection('Your account object (%s) was not found in the database!' % dclass)
            return

        # We can now call the __handleSetAccount function.
        self.account = fields
        self.__handleSetAccount()

    def __handleCreateAccount(self):
        self.account = {'ACCOUNT_AV_SET': [0] * 6,
                        'ESTATE_ID': 0,
                        'ACCOUNT_AV_SET_DEL': [],
                        'CREATED': time.ctime(),
                        'LAST_LOGIN': time.ctime(),
                        'ACCOUNT_ID': str(self.databaseId),
                        'ACCESS_LEVEL': self.accessLevel}

        self.loginManager.air.dbInterface.createObject(self.loginManager.air.dbId,
                                                       self.loginManager.air.dclassesByName['AstronAccountUD'],
                                                       self.account, self.__handleAccountCreated)

    def __handleAccountCreated(self, accountId):
        # This function handles successful & unsuccessful account creations.
        if not accountId:
            # If we don't have an accountId, then that means the database was unable
            # to create an account object for us, for whatever reason. Close the connection.
            self.notify.warning('Database failed to create an account object!')
            self._handleCloseConnection('Your account object could not be created in the game database.')
            return

        # Otherwise, the account object was created successfully!
        self.loginManager.air.writeServerEvent('account-created', accountId)

        # We can now call the __storeAccountId function.
        self.accountId = accountId
        self.__storeAccountId()

    def __storeAccountId(self):
        self.loginManager.accountDb.storeAccountId(self.databaseId, self.accountId, self.__handleAccountIdStored)

    def __handleAccountIdStored(self, success=True):
        if not success:
            # The account bridge was unable to store the account ID,
            # for whatever reason. Close the connection.
            self._handleCloseConnection('The account server could not save your account database ID!')
            return

        # We are all set with account creation now! It's time to call the __handleSetAccount function.
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

         # Update the last login timestamp.
        self.loginManager.air.dbInterface.updateObject(self.loginManager.air.dbId, self.accountId,
                                                       self.loginManager.air.dclassesByName['AstronAccountUD'],
                                                       {'LAST_LOGIN': time.ctime(),
                                                        'ACCOUNT_ID': str(self.databaseId),
                                                        'ACCESS_LEVEL': self.accessLevel})

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
        lastLoggedInStr = ''
        if hasattr(self.loginManager.air, 'toontownTimeManager') and self.loginManager.air.toontownTimeManager:
            lastLoggedInStr = datetime.strftime(self.loginManager.air.toontownTimeManager.getCurServerDateTime(),
                                                self.loginManager.air.toontownTimeManager.formatStr)

        return lastLoggedInStr

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
            # This is not an account object! Close the connection:
            self._handleCloseConnection('Your account object (%s) was not found in the database!' % dclass)
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
        # Now, we will query the avatars that exist in the account.
        self.pendingAvatars = set()
        self.avatarFields = {}

        # Loop through the list of avatars:
        for avId in self.avList:
            if avId:
                # This index contains an avatar! Add it to the pending avatars.
                self.pendingAvatars.add(avId)

                # This is our callback function that queryObject
                # will call when done querying each avatar object.
                def response(dclass, fields, avId=avId):
                    if dclass != self.loginManager.air.dclassesByName['DistributedToonUD']:
                        # The dclass is invalid! Close the connection:
                        self._handleCloseConnection('One of the account\'s avatars is invalid! dclass = %s, expected = %s' % (
                            dclass, self.loginManager.air.dclassesByName['DistributedToonUD'].getName()))
                        return

                    # Otherwise, we're all set! Add the queried avatar fields to the
                    # avatarFields array, remove from the pending list, and call the
                    # __handleSendAvatars function.
                    self.avatarFields[avId] = fields
                    self.pendingAvatars.remove(avId)
                    if not self.pendingAvatars:
                        self.__handleSendAvatars()

                # Query the avatar object.
                self.loginManager.air.dbInterface.queryObject(self.loginManager.air.dbId, avId, response)

        if not self.pendingAvatars:
            # No pending avatars! Call the __handleSendAvatars function:
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
        # First, perform some basic sanity checking.
        if avPosition >= 6:
            # This index is invalid! Close the connection.
            self._handleCloseConnection('Invalid index specified!')
            return

        # Check if this DNA is valid:
        dna = ToonDNA()
        valid = dna.isValidNetString(avDNA)
        if not valid:
            # This DNA is invalid! Close the connection.
            self._handleCloseConnection('Invalid DNA specified!')
            return

        # Store these values:
        self.avPosition = avPosition
        self.avDNA = avDNA

        # Now we can query their account.
        self.__handleRetrieveAccount()

    def __handleRetrieveAccount(self):
        self.loginManager.air.dbInterface.queryObject(self.loginManager.air.dbId, self.sender,
                                                      self.__handleAccountRetrieved)

    def __handleAccountRetrieved(self, dclass, fields):
        if dclass != self.loginManager.air.dclassesByName['AstronAccountUD']:
            # This is not an account object! Close the connection.
            self._handleCloseConnection('Your account object (%s) was not found in the database!' % dclass)
            return

        # Now we will get our avList.
        self.account = fields
        self.avList = self.account['ACCOUNT_AV_SET']

        # We will now sanitize the avList.
        self.avList = self.avList[:6]
        self.avList += [0] * (6 - len(self.avList))

        # Check if the index is open:
        if self.avList[self.avPosition]:
            # This index is not open! Close the connection.
            self._handleCloseConnection('This avatar slot is already taken by another avatar!')
            return

        # All set, now let's create the avatar!
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
            # The database was unable to create a new avatar object! Close the connection.
            self._handleCloseConnection('Database failed to create the new avatar object!')
            return

        # We can now store the avatar.
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
            # The new avatar was not associated with the account! Close the connection.
            self._handleCloseConnection('Database failed to associate the new avatar to your account!')
            return

        # Otherwise, we're done!
        self.loginManager.air.writeServerEvent('avatar-created', self.avId, self.sender, self.avPosition)
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
        # Retrieves the avatar from the database.
        if self.avId and self.avId not in self.avList:
            # The avatar exists, but it's not an avatar that is
            # associated with this account. Close the connection.
            self._handleCloseConnection('Tried to name an avatar not in the account!')
            return

        # Query the database for the avatar. self.__handleAvatarRetrieved is
        # our callback which will be called upon queryObject's completion.
        self.loginManager.air.dbInterface.queryObject(self.loginManager.air.dbId, self.avId,
                                                      self.__handleAvatarRetrieved)

    def __handleAvatarRetrieved(self, dclass, fields):
        if dclass != self.loginManager.air.dclassesByName['DistributedToonUD']:
            # This dclass is not a valid avatar! Close the connection.
            self._handleCloseConnection('One of the account\'s avatars is invalid!')
            return

        if fields['WishNameState'][0] != 'OPEN':
            # This avatar's wish name state is not set
            # to a nameable state. Close the connection.
            self._handleCloseConnection('Avatar is not in a nameable state!')
            return

        # Otherwise, we can set the name:
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
        # Retrieves the avatar from the database.
        if self.avId and self.avId not in self.avList:
            # The avatar exists, but it's not an avatar that is
            # associated with this account. Close the connection.
            self._handleCloseConnection('Tried to name an avatar not in the account!')
            return

        # Query the database for the avatar. self.__handleAvatarRetrieved is
        # our callback which will be called upon queryObject's completion.
        self.loginManager.air.dbInterface.queryObject(self.loginManager.air.dbId, self.avId,
                                                      self.__handleAvatarRetrieved)

    def __handleAvatarRetrieved(self, dclass, fields):
        if dclass != self.loginManager.air.dclassesByName['DistributedToonUD']:
            # This dclass is not a valid avatar! Close the connection.
            self._handleCloseConnection('One of the account\'s avatars is invalid!')
            return

        if fields['WishNameState'][0] != 'OPEN':
            # This avatar's wish name state is not set
            # to a nameable state. Close the connection.
            self._handleCloseConnection('Avatar is not in a nameable state!')
            return

        # Now we can move on to the judging!
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
        # Make sure that the target avatar is part of the account:
        if self.avId not in self.avList:
            # The sender tried to acknowledge name on an avatar not on the account!
            # Close the connection.
            self._handleCloseConnection('Tried to acknowledge name on an avatar not in the account!')
            return

        # We can now query the database for the avatar. self.__handleAvatarRetrieved is the
        # callback which will be called upon the completion of queryObject.
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
        # Make sure that the target avatar is part of the account:
        if self.avId not in self.avList:
            # The sender tried to remove an avatar not on the account! Close the connection.
            self._handleCloseConnection('Tried to remove an avatar not on the account!')
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
            # The avatar was unable to be removed from the account! Close the account.
            self._handleCloseConnection('Database failed to mark the avatar as removed!')
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
        # Get the client channel.
        channel = self.loginManager.GetAccountConnectionChannel(self.sender)

         # We will first assign a POST_REMOVE that will unload the
         # avatar in the event of them disconnecting while we are working.
        cleanupDatagram = PyDatagram()
        cleanupDatagram.addServerHeader(self.avId, channel, STATESERVER_OBJECT_DELETE_RAM)
        cleanupDatagram.addUint32(self.avId)
        datagram = PyDatagram()
        datagram.addServerHeader(channel, self.loginManager.air.ourChannel, CLIENTAGENT_ADD_POST_REMOVE)
        datagram.addUint16(cleanupDatagram.getLength())
        datagram.appendData(cleanupDatagram.getMessage())
        self.loginManager.air.send(datagram)

        # Get the avatar's "true" access (that is, the integer value that corresponds to the assigned string value).
        accessLevel = self.account.get('ACCESS_LEVEL', 'NO_ACCESS')
        accessLevel = OTPGlobals.AccessLevelName2Int.get(accessLevel, 0)

        self.loginManager.air.sendActivate(self.avId, 0, 0, self.loginManager.air.dclassesByName['DistributedToonUD'],
                                           {'setAccessLevel': (accessLevel,)})

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

    def closeConnection(self, connectionId, reason='', forOperations=False, isAccount=False):
        if forOperations:
            if isAccount:
                # Closes the account for duplicate operations.
                operation = self.account2operation.get(connectionId)
                if not operation:
                    self.notify.warning('Tried to close account %s for duplicate operations, but none exist!' % connectionId)
                    return
            else:
                # Closes the connection for duplicate operations.
                operation = self.sender2loginOperation.get(connectionId)
                if not operation:
                    self.notify.warning('Tried to close connection %s for duplicate operations, but none exist!' % connectionId)
                    return

        # Sends CLIENTAGENT_EJECT to the given connectionId with the given reason.
        datagram = PyDatagram()
        if isAccount:
            # Closes the account's connection.
            datagram.addServerHeader(self.GetAccountConnectionChannel(connectionId), self.air.ourChannel, CLIENTAGENT_EJECT)
        else:
            datagram.addServerHeader(connectionId, self.air.ourChannel, CLIENTAGENT_EJECT)
        datagram.addUint32(122)
        if forOperations and not reason:
            datagram.addString('An operation is already running: %s' % operation.__class__.__name__)
        else:
            datagram.addString(reason if reason else 'No reason specified.')
        self.air.send(datagram)

    def runLoginOperation(self, playToken):
        # Runs a login operation on the sender. First, get the sender:
        sender = self.air.getMsgSender()

        # Is the sender already logged in?
        if sender >> 32:
            self.closeConnection(sender, reason='This account is already logged in.')
            return

        # Is the sender already logging in?
        if sender in list(self.sender2loginOperation.keys()):
            self.closeConnection(sender, forOperations=True)
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
            self.closeConnection(sender, reason='Client is not logged in.', isAccount=True)
            return

        if sender in self.account2operation:
            # Sender is already currently running a game operation.
            self.closeConnection(sender, forOperations=True, isAccount=True)
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
            # An avatar has already been chosen!
            self.closeConnection(accountId, reason='An avatar is already chosen!', isAccount=True)
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
