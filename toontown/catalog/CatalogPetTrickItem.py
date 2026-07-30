from . import CatalogItem
from toontown.pets import PetTricks
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from otp.otpbase import OTPLocalizer
from direct.interval.IntervalGlobal import *

class CatalogPetTrickItem(CatalogItem.CatalogItem):
    sequenceNumber = 0
    petPicture = None

    def makeNewItem(self, trickId):
        self.trickId = trickId
        CatalogItem.CatalogItem.makeNewItem(self)

    def getPurchaseLimit(self):
        return 1

    def reachedPurchaseLimit(self, avatar):
        if self in avatar.onOrder or self in avatar.mailboxContents or self in avatar.onGiftOrder or self in avatar.awardMailboxContents or self in avatar.onAwardOrder:
            return 1
        return self.trickId in avatar.petTrickPhrases

    def getAcceptItemErrorText(self, retcode):
        if retcode == ToontownGlobals.P_ItemAvailable:
            return TTLocalizer.CatalogAcceptPet
        return CatalogItem.CatalogItem.getAcceptItemErrorText(self, retcode)

    def saveHistory(self):
        return 1

    def getTypeName(self):
        return TTLocalizer.PetTrickTypeName

    def getName(self):
        phraseId = PetTricks.TrickId2scIds[self.trickId][0]
        return OTPLocalizer.SpeedChatStaticText[phraseId]

    def recordPurchase(self, avatar, optional):
        avatar.petTrickPhrases.append(self.trickId)
        avatar.d_setPetTrickPhrases(avatar.petTrickPhrases)
        return ToontownGlobals.P_ItemAvailable

    def getPicture(self, avatar):
        from toontown.pets import PetDNA, Pet
        pet = Pet.Pet(forGui=1)
        dna = avatar.petDNA
        if dna == None:
            dna = PetDNA.getRandomPetDNA()
        pet.setDNA(dna)
        pet.setH(180)
        model, ival = self.makeFrameModel(pet, 0)
        pet.setScale(2.0)
        pet.setP(-40)
        track = PetTricks.getTrickIval(pet, self.trickId)
        name = 'petTrick-item-%s' % self.sequenceNumber
        CatalogPetTrickItem.sequenceNumber += 1
        if track != None:
            track = Sequence(Sequence(track), ActorInterval(pet, 'neutral', duration=2), name=name)
        else:
            pet.animFSM.request('neutral')
            track = Sequence(Wait(4), name=name)
        self.petPicture = pet
        self.hasPicture = True
        return (model, track)

    def cleanupPicture(self):
        CatalogItem.CatalogItem.cleanupPicture(self)
        self.petPicture.delete()
        self.petPicture = None
        return

    def output(self, store = -1):
        return 'CatalogPetTrickItem(%s%s)' % (self.trickId, self.formatOptionalData(store))

    def compareTo(self, other):
        return self.trickId - other.trickId

    def getHashContents(self):
        return self.trickId

    def getBasePrice(self):
        return 500

    def decodeDatagram(self, di, versionNumber, store):
        CatalogItem.CatalogItem.decodeDatagram(self, di, versionNumber, store)
        self.trickId = di.getUint8()
        self.dna = None
        if self.trickId not in PetTricks.TrickId2scIds:
            raise ValueError
        return

    def encodeDatagram(self, dg, store):
        CatalogItem.CatalogItem.encodeDatagram(self, dg, store)
        dg.addUint8(self.trickId)


def getAllPetTricks():
    list = []
    for trickId in list(PetTricks.TrickId2scIds.keys()):
        list.append(CatalogPetTrickItem(trickId))

    return list
