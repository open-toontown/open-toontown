from pandac.PandaModules import *
from toontown.toonbase.ToonBaseGlobal import *
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from direct.distributed.ClockDelta import *
from toontown.minigame.OrthoWalk import *
from string import *
from toontown.toonbase import ToontownGlobals
from direct.distributed import DistributedObject
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM
from direct.fsm import State
from toontown.toon import Toon
from direct.showbase import RandomNumGen
from toontown.toonbase import TTLocalizer
import random
from direct.showbase import PythonUtil
from toontown.hood import Place
import HouseGlobals
from toontown.building import ToonInteriorColors
from direct.showbase.MessengerGlobal import messenger

class DistributedHouse(DistributedObject.DistributedObject):
    notify = directNotify.newCategory('DistributedHouse')

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        self.houseType = None
        self.avId = -1
        self.ownerId = 0
        self.colorIndex = 0
        self.house = None
        self.name = ''
        self.namePlate = None
        self.nameText = None
        self.nametag = None
        self.floorMat = None
        self.matText = None
        self.randomGenerator = None
        self.housePosInd = 0
        self.house_loaded = 0
        return

    def disable(self):
        DistributedObject.DistributedObject.disable(self)

    def delete(self):
        self.notify.debug('delete')
        self.unload()
        self.clearNametag()
        if self.namePlate:
            self.namePlate.removeNode()
            del self.namePlate
            self.namePlate = None
        if self.floorMat:
            self.floorMat.removeNode()
            del self.floorMat
            self.floorMat = None
        if self.house:
            self.house.removeNode()
            del self.house
        self.house_loaded = 0
        del self.randomGenerator
        DistributedObject.DistributedObject.delete(self)
        return

    def clearNametag(self):
        if self.nametag != None:
            self.nametag.unmanage(base.marginManager)
            self.nametag.setAvatar(NodePath())
            self.nametag = None
        return

    def load(self):
        self.notify.debug('load')
        if not self.house_loaded:
            if self.housePosInd == 1:
                houseModelIndex = base.config.GetInt('want-custom-house', HouseGlobals.HOUSE_DEFAULT)
            else:
                houseModelIndex = HouseGlobals.HOUSE_DEFAULT
            houseModelIndex = base.config.GetInt('want-custom-house-all', houseModelIndex)
            houseModel = self.cr.playGame.hood.loader.houseModels[houseModelIndex]
            self.house = houseModel.copyTo(self.cr.playGame.hood.loader.houseNode[self.housePosInd])
            self.house_loaded = 1
            self.cr.playGame.hood.loader.houseId2house[self.doId] = self.house
            if houseModelIndex == HouseGlobals.HOUSE_DEFAULT:
                self.__setHouseColor()
            if houseModelIndex == HouseGlobals.HOUSE_DEFAULT:
                self.__setupDoor()
            else:
                self.__setupDoorCustom()
            messenger.send('houseLoaded-%d' % self.doId)

    def announceGenerate(self):
        DistributedObject.DistributedObject.announceGenerate(self)
        messenger.send('setBuilding-' + str(self.doId))

    def __setupDoor(self):
        self.notify.debug('setupDoor')
        self.dnaStore = self.cr.playGame.dnaStore
        doorModelName = 'door_double_round_ul'
        if doorModelName[-1:] == 'r':
            doorModelName = doorModelName[:-1] + 'l'
        else:
            doorModelName = doorModelName[:-1] + 'r'
        door = self.dnaStore.findNode(doorModelName)
        door_origin = self.house.find('**/door_origin')
        door_origin.setHpr(90, 0, 0)
        door_origin.setScale(0.6, 0.6, 0.8)
        door_origin.setPos(door_origin, 0.5, 0, 0.0)
        doorNP = door.copyTo(door_origin)
        self.door_origin = door_origin
        self.randomGenerator = random.Random()
        self.randomGenerator.seed(self.doId)
        houseColor = HouseGlobals.stairWood
        color = Vec4(houseColor[0], houseColor[1], houseColor[2], 1)
        DNADoor.setupDoor(doorNP, door_origin, door_origin, self.dnaStore, str(self.doId), color)
        self.__setupNamePlate()
        self.__setupFloorMat()
        self.__setupNametag()

    def __setupDoorCustom(self):
        self.randomGenerator = random.Random()
        self.randomGenerator.seed(self.doId)
        self.notify.debug('setupDoorCustom')
        self.dnaStore = self.cr.playGame.dnaStore
        door = self.house.find('**/door_0')
        door_origin = self.house.find('**/door_origin')
        door_origin.setHpr(90, 0, 0)
        door_origin.setScale(0.6, 0.6, 0.8)
        doorNP = door
        self.door_origin = door_origin
        color = Vec4(1, 1, 1, 1)
        parent = door_origin
        rightDoor = door.find('**/rightDoor')
        rightDoor.setHpr(door_origin, Vec3(0, 0, 0))
        leftDoor = door.find('**/leftDoor')
        leftDoor.setHpr(door_origin, Vec3(0, 0, 0))
        doorTrigger = doorNP.find('**/door_*_trigger')
        doorTrigger.wrtReparentTo(door_origin)
        doorTrigger.node().setName('door_trigger_' + str(self.doId))
        self.__setupFloorMat(changeColor=False)
        self.__setupNametag()
        self.__setupNamePlateCustom()

    def __setupNamePlate(self):
        self.notify.debug('__setupNamePlate')
        if self.namePlate:
            self.namePlate.removeNode()
            del self.namePlate
            self.namePlate = None
        nameText = TextNode('nameText')
        r = self.randomGenerator.random()
        g = self.randomGenerator.random()
        b = self.randomGenerator.random()
        nameText.setTextColor(r, g, b, 1)
        nameText.setAlign(nameText.ACenter)
        nameText.setFont(ToontownGlobals.getBuildingNametagFont())
        nameText.setShadowColor(0, 0, 0, 1)
        nameText.setBin('fixed')
        if TTLocalizer.BuildingNametagShadow:
            nameText.setShadow(*TTLocalizer.BuildingNametagShadow)
        nameText.setWordwrap(16.0)
        xScale = 1.0
        numLines = 0
        if self.name == '':
            return
        else:
            houseName = TTLocalizer.AvatarsHouse % TTLocalizer.GetPossesive(self.name)
        nameText.setText(houseName)
        self.nameText = nameText
        textHeight = nameText.getHeight() - 2
        textWidth = nameText.getWidth()
        xScale = 1.0
        if textWidth > 16:
            xScale = 16.0 / textWidth
        sign_origin = self.house.find('**/sign_origin')
        pos = sign_origin.getPos()
        sign_origin.setPosHpr(pos[0], pos[1], pos[2] + 0.15 * textHeight, 90, 0, 0)
        self.namePlate = sign_origin.attachNewNode(self.nameText)
        self.namePlate.setDepthWrite(0)
        self.namePlate.setPos(0, -0.05, 0)
        self.namePlate.setScale(xScale)
        return nameText

    def __setupFloorMat(self, changeColor = True):
        if self.floorMat:
            self.floorMat.removeNode()
            del self.floorMat
            self.floorMat = None
        mat = self.house.find('**/mat')
        if changeColor:
            mat.setColor(0.4, 0.357, 0.259, 1.0)
        color = HouseGlobals.houseColors[self.housePosInd]
        matText = TextNode('matText')
        matText.setTextColor(color[0], color[1], color[2], 1)
        matText.setAlign(matText.ACenter)
        matText.setFont(ToontownGlobals.getBuildingNametagFont())
        matText.setShadowColor(0, 0, 0, 1)
        matText.setBin('fixed')
        if TTLocalizer.BuildingNametagShadow:
            matText.setShadow(*TTLocalizer.BuildingNametagShadow)
        matText.setWordwrap(10.0)
        xScale = 1.0
        numLines = 0
        if self.name == '':
            return
        else:
            houseName = TTLocalizer.AvatarsHouse % TTLocalizer.GetPossesive(self.name)
        matText.setText(houseName)
        self.matText = matText
        textHeight = matText.getHeight() - 2
        textWidth = matText.getWidth()
        xScale = 1.0
        if textWidth > 8:
            xScale = 8.0 / textWidth
        mat_origin = self.house.find('**/mat_origin')
        pos = mat_origin.getPos()
        mat_origin.setPosHpr(pos[0] - 0.15 * textHeight, pos[1], pos[2], 90, -90, 0)
        self.floorMat = mat_origin.attachNewNode(self.matText)
        self.floorMat.setDepthWrite(0)
        self.floorMat.setPos(0, -.025, 0)
        self.floorMat.setScale(0.45 * xScale)
        return

    def __setupNametag(self):
        if self.nametag:
            self.clearNametag()
        if self.name == '':
            houseName = ''
        else:
            houseName = TTLocalizer.AvatarsHouse % TTLocalizer.GetPossesive(self.name)
        self.nametag = NametagGroup()
        self.nametag.setFont(ToontownGlobals.getBuildingNametagFont())
        if TTLocalizer.BuildingNametagShadow:
            self.nametag.setShadow(*TTLocalizer.BuildingNametagShadow)
        self.nametag.setContents(Nametag.CName)
        self.nametag.setColorCode(NametagGroup.CCHouseBuilding)
        self.nametag.setActive(0)
        self.nametag.setAvatar(self.house)
        self.nametag.setObjectCode(self.doId)
        self.nametag.setName(houseName)
        self.nametag.manage(base.marginManager)

    def unload(self):
        self.notify.debug('unload')
        self.ignoreAll()

    def setHouseReady(self):
        self.notify.debug('setHouseReady')
        try:
            self.House_initialized
        except:
            self.House_initialized = 1
            self.load()

    def setHousePos(self, index):
        self.notify.debug('setHousePos')
        self.housePosInd = index
        self.__setHouseColor()

    def setHouseType(self, index):
        self.notify.debug('setHouseType')
        self.houseType = index

    def setFavoriteNum(self, index):
        self.notify.debug('setFavoriteNum')
        self.favoriteNum = index

    def __setHouseColor(self):
        if self.house:
            bwall = self.house.find('**/*back')
            rwall = self.house.find('**/*right')
            fwall = self.house.find('**/*front')
            lwall = self.house.find('**/*left')
            kd = 0.8
            color = HouseGlobals.houseColors[self.colorIndex]
            dark = (kd * color[0], kd * color[1], kd * color[2])
            if not bwall.isEmpty():
                bwall.setColor(color[0], color[1], color[2], 1)
            if not fwall.isEmpty():
                fwall.setColor(color[0], color[1], color[2], 1)
            if not rwall.isEmpty():
                rwall.setColor(dark[0], dark[1], dark[2], 1)
            if not lwall.isEmpty():
                lwall.setColor(dark[0], dark[1], dark[2], 1)
            aColor = HouseGlobals.atticWood
            attic = self.house.find('**/attic')
            if not attic.isEmpty():
                attic.setColor(aColor[0], aColor[1], aColor[2], 1)
            color = HouseGlobals.houseColors2[self.colorIndex]
            chimneyList = self.house.findAllMatches('**/chim*')
            for chimney in chimneyList:
                chimney.setColor(color[0], color[1], color[2], 1)

    def setAvId(self, id):
        self.avId = id

    def setAvatarId(self, avId):
        self.notify.debug('setAvatarId = %s' % avId)
        self.ownerId = avId

    def getAvatarId(self):
        self.notify.debug('getAvatarId')
        return self.ownerId

    def setName(self, name):
        self.name = name
        if self.nameText and self.nameText.getText() != self.name:
            if self.name == '':
                self.nameText.setText('')
            else:
                self.nameText.setText(self.name + "'s\n House")

    def getName(self):
        return self.name

    def b_setColor(self, colorInd):
        self.setColor(colorInd)
        self.d_setColor(colorInd)

    def d_setColor(self, colorInd):
        self.sendUpdate('setColor', [colorInd])

    def setColor(self, colorInd):
        self.colorIndex = colorInd
        if self.house:
            self.__setHouseColor()

    def getColor(self):
        return self.colorIndex

    def __setupNamePlateCustom(self):
        self.notify.debug('__setupNamePlateCustom')
        if self.namePlate:
            self.namePlate.removeNode()
            del self.namePlate
            self.namePlate = None
        nameText = TextNode('nameText')
        nameText.setCardAsMargin(0.1, 0.1, 0.1, 0.1)
        nameText.setCardDecal(True)
        nameText.setCardColor(1.0, 1.0, 1.0, 0.0)
        r = self.randomGenerator.random()
        g = self.randomGenerator.random()
        b = self.randomGenerator.random()
        nameText.setTextColor(r, g, b, 1)
        nameText.setAlign(nameText.ACenter)
        nameText.setFont(ToontownGlobals.getBuildingNametagFont())
        nameText.setShadowColor(0, 0, 0, 1)
        nameText.setBin('fixed')
        if TTLocalizer.BuildingNametagShadow:
            nameText.setShadow(*TTLocalizer.BuildingNametagShadow)
        nameText.setWordwrap(16.0)
        xScale = 1.0
        numLines = 0
        if self.name == '':
            return
        else:
            houseName = TTLocalizer.AvatarsHouse % TTLocalizer.GetPossesive(self.name)
        nameText.setText(houseName)
        self.nameText = nameText
        textHeight = nameText.getHeight() - 2
        textWidth = nameText.getWidth()
        xScale = 1.0
        if textWidth > 16:
            xScale = 16.0 / textWidth
        sign_origin = self.house.find('**/sign_origin')
        pos = sign_origin.getPos()
        sign_origin.setPosHpr(pos[0], pos[1], pos[2] + 0.15 * textHeight, 90, 0, 0)
        self.namePlate = sign_origin.attachNewNode(self.nameText)
        self.namePlate.setDepthWrite(0)
        self.namePlate.setPos(0, -0.05, 0)
        self.namePlate.setScale(xScale)
        return nameText
