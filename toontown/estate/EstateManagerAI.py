import functools
import random

from . import DistributedEstateAI
from . import HouseGlobals

from dataclasses import fields
from direct.distributed import DistributedObjectAI
from direct.directnotify import DirectNotifyGlobal
from direct.fsm.FSM import FSM
from direct.task.Task import Task

from otp.ai.AIBaseGlobal import *
from direct.showbase.PythonUtil import Functor
from panda3d.core import *

from toontown.estate.DistributedHouseAI import DistributedHouseAI
from toontown.toon import ToonDNA
from toontown.toonbase.ToontownGlobals import MAX_NUM_OF_TOONS

def getAvatarName(toon):
    # Based on toon dict get the avatar name

    name = toon.get('setName')[0]
    return (name)

def getAvatarId(toon):
    # Based on toon dict get the avatar id

    avatarId = toon.get('avId')
    return avatarId

class LoadHouseFSM(FSM):
    def __init__(self ,callback, estate, index, mgr, toon ):
        FSM.__init__(self, 'LoadHouseFSM')
        self.callback = callback
        self.done = False
        self.estate = estate
        self.gender = None
        self.house = None
        self.houseId = 0
        self.index = index
        self.mgr = mgr
        self.toon = toon

    def start(self):
        # We have a few different cases here:
        # 1. The toon has no house. We need to create one.
        # 2. The toon has a house, but it's not loaded. We need to load it.
        # 3 There isnt a toon in the estate slot. Make an empty house
        self.mgr.notify.debug('starting loadhousefsm')
        if self.toon is None:
            taskMgr.doMethodLater(
                0.0, self.demand, f'makeEmptyHouse-{id(self)}', extraArgs=['MakeEmptyHouse'])
            return
        toonStyle = ToonDNA.ToonDNA()
        dnaString = self.toon.get('setDNAString')[0]
        toonStyle.makeFromNetString(dnaString)
        self.gender = toonStyle.gender
        self.houseId = self.toon.get('setHouseId', [0])[0]
        if self.houseId is not 0:
            self.demand('LoadHouse')

        else:
            # Make the house
            self.demand('MakeHouseDB')
            
    def enterMakeEmptyHouse(self):
        # Make a empty new  house for our toon
        self.mgr.notify.debug('making empty house')
        self.house = DistributedHouseAI(self.mgr.air)
        self.house.setHousePos(self.index)
        self.house.setColor(self.index)
        self.house.estate = self.estate
        zoneId = self.estate.zoneId
        # Generate the house onto the server
        self.house.generateWithRequired(zoneId)
        self.estate.houses[self.index] = self.house
        # We are finished
        self.demand('Off')

    def enterMakeHouseDB(self):
        # We need to get the name and avatar id of the toon
        self.mgr.notify.debug('making house db object')
        name = getAvatarName(self.toon)
        avatarId = getAvatarId(self.toon)
        # Make the house in the database
        # if astron is enabled
        if __astron__:
            self.mgr.air.dbInterface.createObject(self.mgr.air.dbId,
                                              self.mgr.air.dclassesByName['DistributedHouseAI'],
                                              {'setName': [name],
                                               'setAvatarId': [avatarId],
                                               },
                                              self.__handleHouseMade)
        else:
            # TODO add the house to the database via openotp 
            pass 

    def __handleHouseMade(self, houseId):
        self.mgr.notify.debug('handling house made')
        # safety check
        if self.state == 'MakeHouseDB':
            avatarId = getAvatarId(self.toon)
            toon = self.mgr.air.doId2do.get(avatarId)
            if toon:
                # Set the house id for the toon
                toon.b_setHouseId(houseId)

            else:
                if __astron__:
                    self.mgr.air.dbInterface.updateObject(
                        self.mgr.air.dbId , avatarId,
                        self.mgr.air.dclassesByName['DistributedToonAI'],
                        {'setHouseId': [houseId]})
                else:
                    # TODO update the toon in the database via openotp
                    pass
            self.houseId = houseId
            # Load the house
            self.demand('LoadHouse')

    def enterLoadHouse(self):
        # We need to get the name and avatar id of the toon
        self.mgr.notify.debug('loading house')
        name = getAvatarName(self.toon)
        avatarId = getAvatarId(self.toon)
        self.mgr.air.sendActivate(self.houseId, self.mgr.air.districtId, self.estate.zoneId,
                                  self.mgr.air.dclassesByName['DistributedHouseAI'],
                                  {'setHousePos': [self.index],
                                   'setColor': [self.index],
                                   'setName': [name],
                                   'setAvatarId': [avatarId],
                                   }
                                  )

        # Wait for the house to generate:
        self.acceptOnce(f'generate-{self.houseId}',
                        self.__handleHouseGenerated)

    def __handleHouseGenerated(self, house):
        # The house will need to be able to reference
        # the estate for setting up gardens, so:
        self.mgr.notify.debug('handling house generated')
        house.estate = self.estate
        # We can now set the house:
        self.house = house

        self.estate.houses[self.index] = self.house

        # Initialize our interior:
        self.house.interior.gender = self.gender
        self.house.interior.generate()
        # Initialize our garden:
        # We are done
        self.demand('Off')

    def exitLoadHouse(self):
        # We no longer need to listen for the house to generate:
        self.mgr.notify.debug('exiting the load of the house')
        self.ignore(f'generate-{self.houseId}')

    def enterOff(self):
        self.mgr.notify.debug('done')
        self.done = True
        self.callback(self.house)


class LoadEstateFSM(FSM):
    def __init__(self, callback, mgr):
        # Initialize the FSM:
        FSM.__init__(self, 'LoadEstateOperation')
        self.accountId = 0 # The account id of the account
        self.estateId = None # The estate id of the estate
        self.callback = callback # The callback to call when we are done
        self.estate = None # The estate object
        self.houseFSMs = [] # The house FSMs for the estate
        self.mgr = mgr # The estate manager 
        self.petFSMs = [] # The pet FSMs for the estate
        self.toons = []     # The toons in the estate
        self.avIds = []  # The av ids in the estate 
        self.zoneId = 0 # The zone id of the estate

    def start(self, accountId, zoneId):
        self.mgr.notify.debug('starting load estate fsm')
        # Store the account id and zone id:
        self.accountId = accountId
        self.zoneId = zoneId
        # Enter the query state
        self.demand('QueryAccount')

    def enterQueryAccount(self):
        # Query the account:
        self.mgr.notify.debug(f'querying account {self.accountId}')
        if __astron__:
            self.mgr.air.dbInterface.queryObject(
                self.mgr.air.dbId, self.accountId, self.__handleQueryAccount)
        else:
            # TODO query the account via openotp
            pass

    def __handleQueryAccount(self, dclass, fields):
        # Safety check:
        self.mgr.notify.debug(f'handling query account {self.accountId}')
        if self.state == 'QueryAccount':
            # We have the account:
            if dclass == self.mgr.air.dclassesByName['AstronAccountAI']:
                self.accountFields = fields
                self.estateId = fields.get('ESTATE_ID', 0)
                self.demand('QueryToons')
            else:
                # we have a problem
                self.mgr.notify.warning(
                    f'Account {self.accountId} has a non-account dclass {dclass}')
                self.demand('Failed')

    def enterQueryToons(self):
        # Query the toons:
        self.mgr.notify.debug(f'querying toons {self.avIds}')
        self.avIds = self.accountFields.get(
            'ACCOUNT_AV_SET', [0] * MAX_NUM_OF_TOONS)
        self.toons = {}
        for index, avId in enumerate(self.avIds):
            if avId == 0:
                self.toons[index] = None
                continue
            if __astron__:
                self.mgr.air.dbInterface.queryObject(self.mgr.air.dbId, avId,
                                                 functools.partial(self.__handleQueryToon,
                                                                   index=index))
            else:
                # TODO query the toon via openotp
                pass


    def __handleQueryToon(self, dclass, fields, index):
        # We have a toon:
        self.mgr.notify.debug(f'handling query toon {self.avIds[index]}')
        if self.state == 'QueryToons':
            if dclass != self.mgr.air.dclassesByName['DistributedToonAI']:
                self.mgr.notify.warning(f'''Account {self.accountId} has toon
                                            {self.avIds[index]}  with a non-toon dclass 
                                            {dclass}''')
            fields['avId'] = self.avIds[index]
            self.toons[index] = fields
            if len(self.toons) == MAX_NUM_OF_TOONS:
                self.__gotAllToons()

    def __gotAllToons(self):
        # We have all of our toons, so now we can handle the estate loading or creating.
        if not self.estateId:
            self.mgr.notify.debug('no estate id, making estate')
            # We need to make the estate:
            self.demand('MakeEstate')
        else:
            self.mgr.notify.debug('estate id found, loading estate')
            # We need to load the estate:
            self.demand('LoadEstate')

    def enterMakeEstate(self):
        # Make an empty estate object in the database:
        self.mgr.notify.debug('making estate')
        if __astron__:
            self.mgr.air.dbInterface.createObject(self.mgr.air.dbId,
                                              self.mgr.air.dclassesByName['DistributedEstateAI'],
                                              {},
                                              self.__handleEstateMade)
        else:
            # TODO add the estate to the database via openotp
            pass

    def __handleEstateMade(self, estateId):
        # We have the estate:
        self.mgr.notify.debug(f'handling estate made {estateId}')
        if self.state == 'MakeEstate':
            # We have the estate:
            self.estateId = estateId
            # Update the account in the database:
            if __astron__:
                self.mgr.air.dbInterface.updateObject(self.mgr.air.dbId, self.accountId,
                                                  self.mgr.air.dclassesByName['AstronAccountAI'],
                                                  {'ESTATE_ID': self.estateId})
            else:
                # TODO update the account via openotp
                pass
            # Load the estate:
            self.demand('LoadEstate')

    def enterLoadEstate(self):
        # Set the fields:
        self.mgr.notify.debug('loading estate')
        self.estateFields = {}
        for i, avId in enumerate(self.avIds):
            if avId:
                self.estateFields[f'setSlot{i}ToonId'] = [avId]

        # Activate the estate:
        self.mgr.notify.debug('activating estate')
        self.mgr.air.sendActivate(self.estateId, self.mgr.air.districtId, self.zoneId,
                                  self.mgr.air.dclassesByName['DistributedEstateAI'],
                                  self.estateFields)

        # Listen once for the estate to generate:
        self.mgr.notify.debug('waiting for estate to generate')
        self.acceptOnce(f'generate-{self.estateId}',
                        self.__handleEstateGenerated)

    def __handleEstateGenerated(self, estate):
        # Get the estate:
        self.mgr.notify.debug(f'handling estate generated {estate}')
        self.estate = estate

        # For keeping track of doodles in this estate:
        self.estate.pets = []
        # For keeping track of the zoneId of the estate
        zoneId = self.estate.zoneId

        # Setup owner to estate mapping:
        owner = self.mgr.air.doId2do.get(self.mgr.getOwnerFromZone(zoneId))
        if owner:
            # Set the estate's owner:
            self.mgr.toonToEstate[owner] = self.estate

        # Set the estate's ID list:
        self.estate.b_setIdList(self.avIds)
        # Start the garden initialization
        self.estate.gardenInit(self.avIds)

        # Load the houses of the toons in this estate:
        self.demand('LoadHouses')

    def exitLoadEstate(self):
        self.mgr.notify.debug('exiting load estate')
        # Stop listening for the estate to generate:
        self.ignore('generate-%d' % self.estateId)

    def enterLoadHouses(self):
        self.mgr.notify.debug('loading houses')
       # Load the houses:
        self.houseFSMs = []
        # We need to keep track of the house FSMs:
        for index in range(MAX_NUM_OF_TOONS):
            # Create the FSM:
            houseFSM = LoadHouseFSM(self.__handleHouseLoaded,  self.estate, index, self.mgr, self.toons[index]
                                    )
            # Add it to the list:
            self.houseFSMs.append(houseFSM)
            # Start the FSM:
            houseFSM.start()

    def __handleHouseLoaded(self, house):
        self.mgr.notify.debug(f'handling house loaded {house}')
        if self.state == 'LoadHouses':
            if all(houseFSM.done for houseFSM in self.houseFSMs):
                # All of the houses are loaded!
                # We can now load the doodles:
                self.demand('LoadPets')
                self.mgr.notify.debug('all houses loaded, loading pets')
        else:
            # We don't want this house  Delete it:
            house.requestDelete()
            self.mgr.notify.debug('house deleted')

    def enterLoadPets(self):
        self.mgr.notify.debug('loading pets')
        # Load the doodles:
        self.petFSMs = []
        for index in range(MAX_NUM_OF_TOONS):
            toon = self.toons[index]
            if toon and toon['setPetId'][0] != 0:
                # Create the FSM:
                petFSM = LoadPetFSM(self.mgr, self.estate, toon,
                                    self.__handlePetLoaded)
                # Add it to the list:
                self.petFSMs.append(petFSM)
                # Start the FSM:
                petFSM.start()
        if not self.petFSMs:
            # We don't have any pets to load, so we can go to the finished state:
            self.demand('Finished')

    def __handlePetLoaded(self, pet):
        self.mgr.notify.debug(f'handling pet loaded {pet}')
        if self.state == 'LoadPets':
            if all(petFSM.done for petFSM in self.petFSMs):
                # All of the doodles are loaded!
                # We can go to the finished state:
                self.demand('Finished')
        else:
            # We don't want this pet  Delete it:
            pet.requestDelete()

    def enterFinished(self):
        # We're done!
        self.mgr.notify.debug('estate loaded')
        # Call the callback:
        self.callback(self.estate)
        # Clean up:
        self.petFSMs.clear()

    def enterFailed(self):
        # We failed to load the estate:
        self.mgr.notify.debug('estate failed to load')
        self.cancel()
        self.callback(False)

    def cancel(self):
        # Cancel the FSM:
        self.mgr.notify.debug('cancelling estate load')
        if self.estate:
            self.estate.destroy()
        self.estate = None

        self.demand('Off')


class LoadPetFSM(FSM):
    def __init__(self, callback, estate,  mgr, toon):
        FSM.__init__(self, 'LoadPetFSM')
        self.callback = callback
        self.done = False
        self.estate = estate
        self.mgr = mgr
        self.petId = 0
        self.toon = toon

    def start(self):
       # Start the FSM:
        if type(self.toon) != dict:
            # We have a regular toon object:
            self.petId = self.toon.getPetId()
        else:
            # We have a toon dictionary:
            self.petId = self.toon['setPetId'][0]
        if self.pet in self.mgr.air.doId2do:
            # The pet is already generated:
            self.__generated(self.mgr.air.doId2do[self.petId])
        else:
            # Listen for the pet to generate and activate it:
            self.mgr.air.sendActivate(
                self.petId, self.mgr.air.districtId, self.estate.zoneId)
            self.acceptOnce(f'generate-{self.petId}', self.__generated)

    def __generated(self, pet):
        # We have a pet:
        self.pet = pet
        # Add it to the estate's doodle list:
        self.estate.pets.append(pet)
        self.demand('Off')

    def enterOff(self):
        # Ignore generation
        self.ignore(f'generate-{self.petId}')

        # We're done:
        self.done = True
        # Call the callback:
        self.callback(self.pet)


TELEPORT_TO_OWNER_ONLY = 0


class EstateManagerAI(DistributedObjectAI.DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory("EstateManagerAI")
    # notify.setDebug(True)

    def __init__(self, air):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        self.previousZone = None
        # dict of lists containing avId's visiting an estate. keyed on owner's avId
        self.refCount = {} 
        # dict of tuple of [zoneId, isOwner, userName] keyed on avId
        self.estateZone = {}
        self.estate = {}        # dict of DistributedEstateAI's keyed on avId
        self.house = {}         # dict of lists of DistributedHouseAI's keyed on avId
        self.account2avId = {}  # mapping of userName to avId that created estate
        self.toBeDeleted = {}   # temporary list of av's to be deleted after a delay
        self.zone2owner = {}    # get the owner of a zone
        self.houseZone2estateZone = {}
        self.avId2pendingEnter = {}  # table of avatars that are on their way to an estate
        self.petFSMs = [] # list of pet FSMs for the estate
        # Number of seconds between spontaneous heals
        self.healFrequency = 30  # seconds
        self.estateToTimeout = {} # dict of avId to timeout task
        self.estateToToons = {} # dict of avId to list of toons in estate
        self.toonToEstate = {} # dict of avId to estate avId
        self.zoneToToons = {} # dict of zoneId to list of toons in the zone

        self.randomGenerator = random.Random()

        return None

    # def delete(self):
        #self.notify.debug("BASE: delete: deleting EstateManagerAI object")
        # self.ignoreAll()
        # DistributedObjectAI.DistributedObjectAI.delete(self)
        # for estate in list(self.estate.values()):
        #   estate.requestDelete()
        # This automatically gets called by the server
        # estate.delete()
        # for hList in list(self.house.values()):
        #  for house in hList:
        #       house.requestDelete()
        # This automatically gets called by the server
        # house.delete()
        #del self.account2avId
        #del self.avId2pendingEnter
        #del self.refCount
        #del self.estateZone
        #del self.randomGenerator

    def getOwnerFromZone(self, zoneId):
        # returns doId of estate owner given a zoneId
        # zoneId can be estate exterior or house interior
        # returns None if zone not found
        estateZoneId = self.houseZone2estateZone.get(zoneId, zoneId)
        return self.zone2owner.get(estateZoneId)

    # -----------------------------------------------------------
    # Zone allocation and enter code
    # -----------------------------------------------------------

    def getEstateZone(self, avId=None, name=None):
        senderAvId = self.air.getAvatarIdFromSender()
        accountId = self.air.getAccountIdFromSender()
        senderToon = self.air.doId2do.get(senderAvId)
        petId = senderToon.getPetId()
        if not senderToon:
            self.air.writeServerEvent(
                'suspicious', senderAvId, 'EstateManagerAI.getEstateZone: senderToon not found')
            return
        # if a toon id is provided, then we want to visit a friend
        # In that case , we just need to check the estate exists
        if avId and avId != senderAvId:
            toon = self.air.doId2do.get(avId)
            if toon and toon.dclass == self.air.dclassesByName['DistributedToonAI']:
                # check if the toon has an estate
                estate = self.toonToEstate.get(toon)
                if estate:
                    # Found the estate
                    avId = estate.owner.doId
                    zoneId = estate.zoneId
                    self._mapToEstate(senderToon, estate)
                    # If the sender is coming from their own estate,
                    # we need to unload their own estate
                    self._unloadEstate(senderToon)
                    if senderToon and petId != 0:
                        # Grab the pet based on the senderToon's petId
                        pet = self.air.doId2do.get(petId)
                        if not pet:
                            # If the pet is not loaded, we need to load it
                            self.__handleLoadPet(estate, senderToon)
                        else:
                            # If the pet is already loaded, we need to unload it
                            self.acceptOnce(self.air.getAvatarExitEvent(petId),
                                            self.__handleUnloadPet, extraArgs=[estate, senderToon])
                            pet.requestDelete()
                    # Now send them to the estate
                    if hasattr(senderToon, 'enterEstate'):
                        senderToon.enterEstate(avId, zoneId)
                    # Send the update to the client
                    self.sendUpdateToAvatarId(
                        senderAvId, 'setEstateZone', [avId, zoneId])

                # we couldn't find the given avId's estate
                self.sendUpdateToAvatarId(
                    senderAvId, 'setEstateZone', [0, 0])
                return
            # We are going to our own estate
            estate = getattr(senderToon, 'estate', None)
            if estate:
                # We already have the estate loaded, so send them there
                self._mapToEstate(senderToon, senderToon.estate)
                if senderToon and petId != 0:
                    # Grab the pet based on the senderToon's petId
                    pet = self.air.doId2do.get(petId)
                    if not pet:
                        # If the pet is not loaded, we need to load it
                        self.__handleLoadPet(estate, senderToon)
                    else:
                        # Load the pet on exit
                        self.acceptOnce(self.air.getAvatarExitEvent(petId),
                                        self.__handleLoadPet, extraArgs=[estate, senderToon])
                if hasattr(senderToon, 'enterEstate'):
                    senderToon.enterEstate(avId, estate.zoneId)
                # Send the update to the client
                self.sendUpdateToAvatarId(
                    senderAvId, 'setEstateZone', [avId, estate.zoneId])

            # If we have a timeout , cancel it
            if estate in self.estateToTimeout:
                taskMgr.remove(self.estateToTimeout[estate])
                self.estateToTimeout.remove()
                del self.estateToTimeout[estate]
            return

        if getattr(senderToon, 'loadEstateFSM', None):
            # We are already loading the estate
            return
        # allocate the zone on the ai server
        zoneId = self.air.allocateZone()
        # assign this specific zone of  zone2towner dictionary to the client
        self.zone2owner[zoneId] = senderAvId

        def estateLoaded(success):
            # This is called when the estate is loaded

            # If the estate is not loaded, we need to send the client a 0,0
            if not success:
                # Estate failed to load
                self.sendUpdateToAvatarId(
                    senderAvId, 'setEstateZone', [0, 0])
                # Free up the zone
                self.air.deallocateZone(zoneId)
                del self.zone2owner[zoneId]
            else:
                # Success loading the estate
                senderToon.estate = senderToon.loadEstateFSM.estate
                senderToon.estate.owner = senderToon
                self._mapToEstate(senderToon, senderToon.estate)
                if hasattr(senderToon, 'enterEstate'):
                    # Send the client to the estate
                    senderToon.enterEstate(avId, zoneId)
                # Send the update to the client
                self.sendUpdateToAvatarId(
                    senderAvId, 'setEstateZone', [avId, zoneId])
            senderToon.loadEstateFSM = None
        self.acceptOnce(self.air.getAvatarExitEvent(senderAvId),
                        self.__handleUnexpectedExit, extraArgs=[senderToon])

        if senderToon and petId != 0:
            # Grab the pet based on the senderToon's petId
            pet = self.air.doId2do.get(petId)
            if pet:
                # If the pet is already loaded, we need to load the estate
                self.acceptOnce(self.air.getAvatarExitEvent(petId), self.__handleLoadEstate,
                                extraArgs=[senderToon, estateLoaded, accountId, zoneId])
                # Delete the pet
                pet.requestDelete()
                return

        self.__handleLoadEstate(senderToon, estateLoaded, accountId, zoneId)

    def getAvEnterEvent(self):
        return 'avatarEnterEstate'

    def getAvExitEvent(self, avId=None):
        # listen for all exits or a particular exit
        # event args:
        #  if avId given: none
        #  if avId not given: avId, ownerId, zoneId
        if avId is None:
            return 'avatarExitEstate'
        else:
            return 'avatarExitEstate-%s' % avId

    def __enterEstate(self, avId, ownerId):
        # Tasks that should always get called when entering an estate

        # Handle unexpected exit
        self.acceptOnce(self.air.getAvatarExitEvent(avId),
                        self.__handleUnexpectedExit, extraArgs=[avId])

        # Toonup
        try:
            av = self.air.doId2do[avId]
            av.startToonUp(self.healFrequency)
        except:
            self.notify.info("couldn't start toonUpTask for av %s" % avId)

    def _listenForToonEnterEstate(self, avId, ownerId, zoneId):
        #self.notify.debug('_listenForToonEnterEstate(avId=%s, ownerId=%s, zoneId=%s)' % (avId, ownerId, zoneId))
        if avId in self.avId2pendingEnter:
            self.notify.warning(
                '_listenForToonEnterEstate(avId=%s, ownerId=%s, zoneId=%s): '
                '%s already in avId2pendingEnter. overwriting' % (
                    avId, ownerId, zoneId, avId))
        self.avId2pendingEnter[avId] = (ownerId, zoneId)
        self.accept(DistributedObjectAI.
                    DistributedObjectAI.staticGetLogicalZoneChangeEvent(avId),
                    Functor(self._toonChangedZone, avId))

    def _toonLeftBeforeArrival(self, avId):
        #self.notify.debug('_toonLeftBeforeArrival(avId=%s)' % avId)
        if avId not in self.avId2pendingEnter:
            self.notify.warning('_toonLeftBeforeArrival: av %s not in table' %
                                avId)
            return
        ownerId, zoneId = self.avId2pendingEnter[avId]
        self.notify.warning(
            '_toonLeftBeforeArrival: av %s left server before arriving in '
            'estate (owner=%s, zone=%s)' % (avId, ownerId, zoneId))
        del self.avId2pendingEnter[avId]

    def _toonChangedZone(self, avId, newZoneId, oldZoneId):
        #self.notify.debug('_toonChangedZone(avId=%s, newZoneId=%s, oldZoneId=%s)' % (avId, newZoneId, oldZoneId))
        if avId not in self.avId2pendingEnter:
            self.notify.warning('_toonChangedZone: av %s not in table' %
                                avId)
            return
        av = self.air.doId2do.get(avId)
        if not av:
            self.notify.warning('_toonChangedZone(%s): av not present' % avId)
            return
        ownerId, estateZoneId = self.avId2pendingEnter[avId]
        estateZoneIds = self.getEstateZones(ownerId)
        if newZoneId in estateZoneIds:
            del self.avId2pendingEnter[avId]
            self.ignore(DistributedObjectAI.
                        DistributedObjectAI.staticGetLogicalZoneChangeEvent(avId))
            self.announceToonEnterEstate(avId, ownerId, estateZoneId)

    def announceToonEnterEstate(self, avId, ownerId, zoneId):
        """ announce to the rest of the system that a toon is entering
        an estate """
        EstateManagerAI.notify.debug('announceToonEnterEstate: %s %s %s' %
                                     (avId, ownerId, zoneId))
        messenger.send(self.getAvEnterEvent(), [avId, ownerId, zoneId])

    def announceToonExitEstate(self, avId, ownerId, zoneId):
        """ announce to the rest of the system that a toon is exiting
        an estate """
        EstateManagerAI.notify.debug('announceToonExitEstate: %s %s %s' %
                                     (avId, ownerId, zoneId))
        messenger.send(self.getAvExitEvent(avId))
        messenger.send(self.getAvExitEvent(), [avId, ownerId, zoneId])

    def getEstateZones(self, ownerId):
        # returns all zoneIds that belong to this estate
        zones = []
        estate = self.estate.get(ownerId)
        if estate is not None:
            if not hasattr(estate, 'zoneId'):
                self.notify.warning('getEstateZones: estate %s (owner %s) has no \'zoneId\'' %
                                    (estate.doId, ownerId))
            else:
                zones.append(estate.zoneId)
        houses = self.house.get(ownerId)
        if houses is not None:
            for house in houses:
                if not hasattr(house, 'interiorZoneId'):
                    self.notify.warning(
                        'getEstateZones: estate %s (owner %s) house has no interiorZoneId')
                else:
                    zones.append(house.interiorZoneId)
        return zones

    def getEstateHouseZones(self, ownerId):
        # returns all zoneIds that belong to houses on this estate
        zones = []
        houses = self.house.get(ownerId)
        if houses is not None:
            for house in houses:
                if not hasattr(house, 'interiorZoneId'):
                    self.notify.warning(
                        'getEstateHouseZones: (owner %s) house has no interiorZoneId')
                else:
                    zones.append(house.interiorZoneId)
        return zones

    def __sendZoneToClient(self, recipient, ownerId):
        try:
            zone = self.estateZone[ownerId][0]
            owner = self.zone2owner[zone]
            self.sendUpdateToAvatarId(
                recipient, "setEstateZone", [owner, zone])
        except:
            self.notify.warning(
                "zone did not exist for estate owner %d, and visitor %d" % (ownerId, recipient))
            self.sendUpdateToAvatarId(recipient, "setEstateZone", [0, 0])

    def __createEstateZoneAndObjects(self, avId, isOwner, ownerId, name):
        # assume this is only called when isOwner == 1

        # stop any cleanup tasks that might be pending for this avId
        # (note: we might be in a case where we aren't in the toBeDeleted list
        # and still have a cleanup task pending.  this happens when we switch
        # shards)
        self.__stopCleanupTask(avId)

        # first check that we aren't in the toBeDeleted list
        avZone = self.toBeDeleted.get(avId)
        if avZone:

            # move our info back to estateZone
            self.setEstateZone(avId, avZone)
            del self.toBeDeleted[avId]
            return

        # check if our account has an estate created under a different avatar
        if self.__checkAccountSwitchedAvatars(name, avId):
            return

        # request the zone for the owners estate
        zoneId = self.air.allocateZone()
        # [zoneId, isOwner, userName (if owner)]
        self.setEstateZone(avId, [zoneId, isOwner, name])
        self.account2avId[name] = avId
        self.zone2owner[zoneId] = avId

        # start a ref count for this zone id
        self.refCount[zoneId] = []

        # don't send a message back yet since the estate is not filled
        # in.  Do this later.
        #self.sendUpdateToAvatarId(avId, "setEstateZone", [avId, zoneId])

        # create the estate and generate the zone
        #callback = PythonUtil.Functor(self.handleGetEstate, avId, ownerId)
        #self.air.getEstate(avId, zoneId, callback)

    def __removeReferences(self, avId, zoneId):
        try:
            self.clearEstateZone(avId)
            self.refCount[zoneId].remove(avId)
        except:
            self.notify.debug("we weren't in the refcount for %s." % zoneId)
            pass

    def setEstateZone(self, index, info):
        self.estateZone[index] = info

        # print some debug info
        frame = sys._getframe(1)
        lineno = frame.f_lineno
        defName = frame.f_code.co_name
        #str = "%s(%s):Added %s:estateZone=%s" % (defName, lineno, index, self.estateZone)
        str = "%s(%s):Added %s:%s" % (defName, lineno, index, info)
        self.notify.debug(str)

    def clearEstateZone(self, index):
        assert index in self.estateZone

        # print some debug info
        frame = sys._getframe(1)
        lineno = frame.f_lineno
        defName = frame.f_code.co_name
        #str = "%s(%s):Removed %s:estateZone=%s" % (defName, lineno, index, self.estateZone)
        str = "%s(%s):Removed %s:%s" % (
            defName, lineno, index, self.estateZone[index])
        self.notify.debug(str)

        del self.estateZone[index]

    def __addReferences(self, avId, ownerId):
        avZone = self.estateZone.get(ownerId)
        if avZone:
            zoneId = avZone[0]
            # [zoneId, isOwner, userName (if owner)]
            self.setEstateZone(avId, [zoneId, 0, ""])
            ref = self.refCount.get(zoneId)
            if ref:
                ref.append(avId)
            else:
                self.refCount[zoneId] = [avId]

    def __checkAccountSwitchedAvatars(self, name, ownerId):
        self.notify.debug("__checkAccountSwitchedAvatars")
        prevAvId = self.account2avId.get(name)
        if prevAvId:
            self.notify.debug("we indeed did switch avatars")
            # the estate exists, remap all references from prevAvId
            # to ownerId

            # first stop the cleanup task
            self.__stopCleanupTask(prevAvId)

            # now remap references
            self.account2avId[name] = ownerId

            # if self.estateZone.has_key(prevAvId):
            if prevAvId in self.toBeDeleted:
                self.setEstateZone(ownerId, self.toBeDeleted[prevAvId])
                del self.toBeDeleted[prevAvId]
            return 1
        return 0

    def handleGetEstate(self, avId, ownerId, estateId, estateVal,
                        numHouses, houseId, houseVal, petIds, valDict=None):
        self.notify.debug("handleGetEstate %s" % avId)
        # this function is called after the estate data is pulled
        # from the database.  the houseAI object is initialized
        # here, and if values don't exist for certain db fields
        # default values are given.

        # Note:  this is the place where randomized default values
        # should be assigned to the toons house.  For example:
        # door types, windows, colors, house selection, garden placement
        # etc.  The first time the toon visits his house, these
        # defaults will be computed and stored.

        # Note:  this function is only called by the owner of the estate

        # there is a chance that the owner will already have left (by
        # closing the window).  We need to handle that gracefully.

        if ownerId not in self.estateZone:
            self.notify.warning(
                "Estate info was requested, but the owner left before it could be recived: %d" % estateId)
            return
        elif not avId in self.air.doId2do:
            self.notify.warning(
                "Estate owner %s in self.estateZone, but not in doId2do" % avId)
            return

        # create the DistributedEstateAI object for this avId
        if avId in self.estateZone:
            if estateId in self.air.doId2do:
                self.notify.warning(
                    "Already have distobj %s, not generating again" % (estateId))
            else:
                self.notify.info('start estate %s init, owner=%s, frame=%s' %
                                 (estateId, ownerId, globalClock.getFrameCount()))

                # give the estate a time seed
                estateZoneId = self.estateZone[avId][0]
                ts = time.time() % HouseGlobals.DAY_NIGHT_PERIOD
                self.randomGenerator.seed(estateId)
                dawn = HouseGlobals.DAY_NIGHT_PERIOD * self.randomGenerator.random()
                estateAI = DistributedEstateAI.DistributedEstateAI(self.air, avId,
                                                                   estateZoneId, ts, dawn, valDict)
                # MPG - We should make sure this works across districts
                estateAI.dbObject = 1
                estateAI.generateWithRequiredAndId(estateId,
                                                   self.air.districtId,
                                                   estateZoneId)

                estateAI.initEstateData(
                    estateVal, numHouses, houseId, houseVal)
                estateAI.setPetIds(petIds)
                self.estate[avId] = estateAI

                # create the DistributedHouseAI's.  This was originally done by the EstateAI
                # but we need to move it here so we can explicitly control when the
                # DistributedHouse objects get deleted from the stateserver.
                self.house[avId] = [None] * numHouses
                for i in range(numHouses):
                    if houseId[i] in self.air.doId2do:
                        self.notify.warning("doId of house %s conflicts with a %s!" % (
                            houseId[i], self.air.doId2do[houseId[i]].__class__.__name__))

                    else:
                        house = DistributedHouseAI.DistributedHouseAI(self.air,
                                                                      houseId[i],
                                                                      estateId, estateZoneId, i)

                        # get house information
                        house.initFromServerResponse(houseVal[i])
                        self.house[avId][i] = house

                        # Now that we have all the data loaded, officially
                        # generate the distributed object

                        house.dbObject = 1

                        # MPG - We should make sure this works across districts
                        house.generateWithRequiredAndId(houseId[i],
                                                        self.air.districtId,
                                                        estateZoneId)

                        house.setupEnvirons()

                        # Finally, make sure that the house has a good owner,
                        # and then tell the client the house is ready.
                        house.checkOwner()

                        estateAI.houseList.append(house)

                estateAI.postHouseInit()

                # get us a list of the owners of the houses
                avIdList = []
                for id in houseId:
                    avHouse = simbase.air.doId2do.get(id)
                    avIdList.append(avHouse.ownerId)

                if simbase.wantPets:
                    self.notify.debug('creating pet collisions for estate %s' %
                                      estateId)
                    estateAI.createPetCollisions()

                # create a pond bingo manager ai for the new estate
                if simbase.wantBingo:
                    self.notify.info('creating bingo mgr for estate %s' %
                                     estateId)
                    self.air.createPondBingoMgrAI(estateAI)

                self.notify.info('finish estate %s init, owner=%s' %
                                 (estateId, ownerId))

                estateAI.gardenInit(avIdList)

        # Now that the zone is set up, send the notification back to
        # the client.
        self.__sendZoneToClient(avId, ownerId)
        zoneId = self.estateZone[ownerId][0]
        self._listenForToonEnterEstate(avId, ownerId, zoneId)

    # -----------------------------------------------------------
    # Cleanup and exit functions
    # -----------------------------------------------------------

    def exitEstate(self, avId= ''):
        # this function is called when a toon leaves
        if not avId:
            avId = self.air.getAvatarIdFromSender()
        av = self.air.doId2do.get(avId)
        if not av:
            return
        self._unmapFromEstate(av)
        self._unloadEstate(av) 

    def __handleUnexpectedExit(self, avId):
        # this function is called when a toon in the estate leaves
        # unexpectedly
        self.exitEstate(avId)



    def _cleanupEstate(self, estate):
        self.notify.debug(
            f"cleanupEstate {estate.doId}") 
        # we should always be cleaning up things from the toBeDeleted list,
        # not directly from estateZone

        # remove all 'hanging' entries left in estateZone
        # this is caused by:
        #   friend A is visting friend B
        #   friend B exits his estate
        #   friend C attempts to visit friend A at the same time

        # Send all toons back to the playground
        self._sendAvsToPlayground(estate, 0)
        
        # Clean up toons to estate mappings
        for toon in self.estateToToons[estate]:
            # Check to make sure the toon is in the toonToEstate dict before deleting
            if toon in self.toonToEstate.keys():
                del self.toonToEstate[toon]
        # Clean up estate in estateToTimeout if it exists
        if estate in self.estateToTimeout:
            del self.estateToTimeout[estate]
        # delete the estate and the unload the owner
        estate.destroy()
        estate.owner.estate = None

        # Destroy the doodles
        for pet in estate.pets:
            pet.requestDelete()
        estate.pets = []

        # Free the zone that is occupied by the estate
        self.air.deallocateZone(estate.zoneId)
        del self.zone2owner[estate.zoneId]
            


    def __stopCleanupTask(self, avId):
        self.notify.debug("stopCleanupTask %s" % avId)
        taskMgr.remove("cleanupEstate-"+str(avId))
        taskMgr.remove("bootVisitorsAndCleanup-"+str(avId))
        self.acceptOnce(self.air.getAvatarExitEvent(avId),
                        self.__handleUnexpectedExit, extraArgs=[avId])

    def __deleteEstate(self, avId):
        # remove all our objects from the stateserver
        self.notify.debug("__deleteEstate(avId=%s)" % avId)

        # delete from state server
        if avId in self.estate:
            if self.estate[avId] != None:
                self.estate[avId].destroyEstateData()
                self.notify.debug('DistEstate requestDelete, doId=%s' %
                                  getattr(self.estate[avId], 'doId'))
                self.estate[avId].requestDelete()
                # This automatically gets called by the server
                # self.estate[avId].delete()
                del self.estate[avId]
        # delete the houses
        houses = self.house.get(avId)
        if houses:
            for i in range(len(houses)):
                if self.house[avId][i]:
                    self.house[avId][i].requestDelete()
                    # This automatically gets called by the server
                    # self.house[avId][i].delete()
            del self.house[avId]

    """
    def __bootVisitors(self, zoneId, task):
        try:
            visitors = self.refCount[zoneId][:]
            for avId in visitors:
                self.__bootAv(avId, zoneId)
        except:
            # refCount might have already gotten deleted
            pass
        return Task.done
    """


    def __bootAv(self, avId, zoneId, ownerId, retCode=1):
        messenger.send("bootAvFromEstate-"+str(avId))
        self.sendUpdateToAvatarId(avId, "sendAvToPlayground", [avId, retCode])
        if avId in self.toBeDeleted:
            del self.toBeDeleted[avId]
        try:
            self.refCount[zoneId].remove(avId)
        except:
            self.notify.debug("didn't have refCount[%s][%s]" % (zoneId, avId))
            pass

    def __warnVisitors(self, zoneId):
        visitors = self.refCount.get(zoneId)
        if visitors:
            for avId in visitors:
                self.sendUpdateToAvatarId(
                    avId, "sendAvToPlayground", [avId, 0])

    def removeFriend(self, ownerId, avId):
        self.notify.debug(
            "removeFriend ownerId = %s, avId = %s" % (ownerId, avId))
        # check if ownerId is in an estate
        ownZone = self.estateZone.get(ownerId)
        if ownZone:
            if ownZone[1]:
                # owner is in his own estate.  kick out avId if he is
                # in the owner's estate.
                avZone = self.estateZone.get(avId)
                if avZone:
                    if avZone[0] == ownZone[0]:
                        # avId is indeed in owner's estate.  boot him
                        self.__bootAv(avId, ownZone[0], ownerId, retCode=2)
                    else:
                        print("visitor not in owners estate")
                else:
                    print("av is not in an estate")

        else:
            print("owner not in estate")

    # -----------------------------------------------------------
    # April fools stuff
    # -----------------------------------------------------------

    def startAprilFools(self):
        self.sendUpdate("startAprilFools", [])

    def stopAprilFools(self):
        self.sendUpdate("stopAprilFools", [])

# New functions to handle loading of estates and unloading of estates

    def __handleLoadEstate(self, toon, callback, accountId, zoneId):
        # If we're already loading an estate, don't load another one.
        self._unmapFromEstate(toon)
        # Create a new LoadEstateFSM
        toon.loadEstateFSM = LoadEstateFSM(callback, self)
        # start the estate loading process
        toon.loadEstateFSM.start(accountId, zoneId)

    def _unloadEstate(self, toon):
        # unload the estate
        if getattr(toon, 'estate', None):
            # Unload the estate
            estate = toon.estate
            avId = estate.owner.doId
            zoneId = estate.zoneId
            if estate not in self.estateToTimeout:
                self.estateToTimeout[estate] = taskMgr.doMethodLater(HouseGlobals.BOOT_GRACE_PERIOD,
                                                                     self._cleanupEstate,
                                                                     f"cleanupEstate-{str(avId)}",
                                                                     extraArgs=[estate]
                                                            )
            # send all the guests back to the playground
            self._sendAvsToPlayground(toon.estate, 0)

    def _mapToEstate(self, toon, estate):
        self._unmapFromEstate(toon)

        # Now map the avatar to the new estate.
        self.estate[toon.doId] = estate
        self.estateToToons.setdefault(estate, []).append(toon)
        if toon not in self.toonToEstate:
            # Add the avatar to the toonToEstate dictionary.
            self.toonToEstate[toon] = estate

        self.zoneToToons.setdefault(estate.zoneId, []).append(toon.doId)

    def _unmapFromEstate(self, toon):
        # Unmap the avatar from the estate.
        estate = self.toonToEstate.get(toon)
        if estate:
            if toon.doId in self.estate:
                # Remove the avatar from the estate dictionary.
                del self.estate[toon.doId]

            # Remove the avatar from the estateToToons dictionary.x
            if toon in self.estateToToons.values():
                self.estateToToons[estate].remove(toon)
            if toon.doId in self.zoneToToons.values():
                # Remove the avatar from the zoneToToons dictionary.
                self.zoneToToons[estate.zoneId].remove(toon.doId)
            # Remove the avatar from the toonToEstate dictionary.
            del self.toonToEstate[toon]

    def __handleLoadPet(self, estate, toon):
        # load the petfsm
        petFSM = LoadPetFSM(self.__handlePetLoaded, estate, self, toon)
        # add the petfsm to the list of petfsm's
        self.petFSMs.append(petFSM)
        # start the petfsm
        petFSM.start()

    def __handlePetLoaded(self, _):
        # check if all the petfsm's are done
        if all(petFSM.done for petFSM in self.petFSMs):
            # all the petfsm's are done
            # remove all the petfsm's
            self.petFSMs = []

    def _sendAvsToPlayground(self, estate, reason):
        # send all the toons in the estate to the playground
        for toon in self.estateToToons[estate]:
            # send the toon to their previous zone
           self.sendUpdateToAvatarId(toon.doId, 'sendAvToPlayground', [toon.doId, reason])