from direct.gui.DirectGui import *
from direct.directnotify import DirectNotifyGlobal
from pandac.PandaModules import *
import NPCToons
import ToonHead
import ToonDNA
from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import ToontownBattleGlobals

class NPCFriendPanel(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('NPCFriendPanel')

    def __init__(self, parent = aspect2d, **kw):
        optiondefs = (('relief', None, None), ('doneEvent', None, None))
        self.defineoptions(kw, optiondefs)
        DirectFrame.__init__(self, parent=parent)
        self.cardList = []
        self.updateLayout()
        self.initialiseoptions(NPCFriendPanel)
        self.accept(localAvatar.uniqueName('maxNPCFriendsChange'), self.updateLayout)
        return None

    def update(self, friendDict, fCallable = 0):
        friendList = friendDict.keys()
        for i in range(self.maxNPCFriends):
            card = self.cardList[i]
            try:
                NPCID = friendList[i]
                count = friendDict[NPCID]
            except IndexError:
                NPCID = None
                count = 0

            card.update(NPCID, count, fCallable)

        return

    def updateLayout(self):
        for card in self.cardList:
            card.destroy()

        self.cardList = []
        self.maxNPCFriends = localAvatar.getMaxNPCFriends()
        rotateCard = False
        if self.maxNPCFriends == 8:
            rotateCard = True
            xOffset = -5.25
            yOffset = 2.3
            yOffset2 = -4.7
        elif self.maxNPCFriends == 16:
            xOffset = -5.2
            yOffset = 3.5
            yOffset2 = -2.45
        else:
            self.notify.error('got wrong max SOS cards %s' % self.maxNPCFriends)
        count = 0
        for i in range(self.maxNPCFriends):
            card = NPCFriendCard(parent=self, rotateCard=rotateCard, doneEvent=self['doneEvent'])
            self.cardList.append(card)
            card.setPos(xOffset, 1, yOffset)
            card.setScale(0.75)
            xOffset += 3.5
            count += 1
            if count % 4 == 0:
                xOffset = -5.25
                yOffset += yOffset2


class NPCFriendCard(DirectFrame):
    normalTextColor = (0.3, 0.25, 0.2, 1)
    maxRarity = 5
    sosTracks = ToontownBattleGlobals.Tracks + ToontownBattleGlobals.NPCTracks

    def __init__(self, parent = aspect2dp, rotateCard = False, **kw):
        optiondefs = (('NPCID', 'Uninitialized', None), ('relief', None, None), ('doneEvent', None, None))
        self.defineoptions(kw, optiondefs)
        DirectFrame.__init__(self, parent=parent)
        self.initialiseoptions(NPCFriendCard)
        cardModel = loader.loadModel('phase_3.5/models/gui/playingCard')
        self.front = DirectFrame(parent=self, relief=None, image=cardModel.find('**/card_front'))
        self.front.hide()
        self.back = DirectFrame(parent=self, relief=None, image=cardModel.find('**/card_back'), geom=cardModel.find('**/logo'))
        callButtonPosZ = -0.9
        textWordWrap = 16.0
        textScale = 0.35
        textPosZ = 1.15
        nameScale = 0.4
        namePosZ = -0.45
        rarityScale = 0.2
        rarityPosZ = -1.2
        self.NPCHeadDim = 1.2
        self.NPCHeadPosZ = 0.45
        self.sosCountInfoPosZ = -0.9
        self.sosCountInfoScale = 0.4
        self.sosCountInfo2PosZ = -0.9
        self.sosCountInfo2Scale = 0.5
        if rotateCard:
            self.front.component('image0').configure(pos=(0, 0, 0.22), hpr=(0, 0, -90), scale=1.35)
            self.back.component('image0').configure(hpr=(0, 0, -90), scale=(-1.35, 1.35, 1.35))
            callButtonPosZ = -2.1
            textWordWrap = 7.0
            textScale = 0.5
            textPosZ = 2.0
            nameScale = 0.5
            namePosZ = -0.89
            rarityScale = 0.25
            rarityPosZ = -2.4
            self.NPCHeadDim = 1.8
            self.NPCHeadPosZ = 0.4
            self.sosCountInfoPosZ = -2.1
            self.sosCountInfoScale = 0.4
            self.sosCountInfo2PosZ = -2.0
            self.sosCountInfo2Scale = 0.55
        self.sosTypeInfo = DirectLabel(parent=self.front, relief=None, text='', text_font=ToontownGlobals.getMinnieFont(), text_fg=self.normalTextColor, text_scale=textScale, text_align=TextNode.ACenter, text_wordwrap=textWordWrap, pos=(0, 0, textPosZ))
        self.NPCHead = None
        self.NPCName = DirectLabel(parent=self.front, relief=None, text='', text_fg=self.normalTextColor, text_scale=nameScale, text_align=TextNode.ACenter, text_wordwrap=8.0, pos=(0, 0, namePosZ))
        buttonModels = loader.loadModel('phase_3.5/models/gui/inventory_gui')
        upButton = buttonModels.find('**/InventoryButtonUp')
        downButton = buttonModels.find('**/InventoryButtonDown')
        rolloverButton = buttonModels.find('**/InventoryButtonRollover')
        self.sosCallButton = DirectButton(parent=self.front, relief=None, text=TTLocalizer.NPCCallButtonLabel, text_fg=self.normalTextColor, text_scale=0.28, text_align=TextNode.ACenter, image=(upButton,
         downButton,
         rolloverButton,
         upButton), image_color=(1.0, 0.2, 0.2, 1), image0_color=Vec4(1.0, 0.4, 0.4, 1), image3_color=Vec4(1.0, 0.4, 0.4, 0.4), image_scale=(4.4, 1, 3.6), image_pos=Vec3(0, 0, 0.08), pos=(-1.15, 0, callButtonPosZ), scale=1.25, command=self.__chooseNPCFriend)
        self.sosCallButton.hide()
        self.sosCountInfo = DirectLabel(parent=self.front, relief=None, text='', text_fg=self.normalTextColor, text_scale=0.75, text_align=TextNode.ALeft, textMayChange=1, pos=(0.0, 0, -1.0))
        star = loader.loadModel('phase_3.5/models/gui/name_star')
        self.rarityStars = []
        for i in range(self.maxRarity):
            label = DirectLabel(parent=self.front, relief=None, image=star, image_scale=rarityScale, image_color=Vec4(0.502, 0.251, 0.251, 1.0), pos=(1.1 - i * 0.24, 0, rarityPosZ))
            label.hide()
            self.rarityStars.append(label)

        return

    def __chooseNPCFriend(self):
        if self['NPCID'] and self['doneEvent']:
            doneStatus = {}
            doneStatus['mode'] = 'NPCFriend'
            doneStatus['friend'] = self['NPCID']
            messenger.send(self['doneEvent'], [doneStatus])

    def destroy(self):
        if self.NPCHead:
            self.NPCHead.detachNode()
            self.NPCHead.delete()
        DirectFrame.destroy(self)

    def update(self, NPCID, count = 0, fCallable = 0):
        oldNPCID = self['NPCID']
        self['NPCID'] = NPCID
        if NPCID != oldNPCID:
            if self.NPCHead:
                self.NPCHead.detachNode()
                self.NPCHead.delete()
            if NPCID is None:
                self.showBack()
                return
            self.front.show()
            self.back.hide()
            self.NPCName['text'] = TTLocalizer.NPCToonNames[NPCID]
            self.NPCHead = self.createNPCToonHead(NPCID, dimension=self.NPCHeadDim)
            self.NPCHead.reparentTo(self.front)
            self.NPCHead.setZ(self.NPCHeadPosZ)
            track, level, hp, rarity = NPCToons.getNPCTrackLevelHpRarity(NPCID)
            sosText = self.sosTracks[track]
            if track == ToontownBattleGlobals.NPC_RESTOCK_GAGS:
                if level == -1:
                    sosText += ' All'
                else:
                    sosText += ' ' + self.sosTracks[level]
            sosText = TextEncoder.upper(sosText)
            self.sosTypeInfo['text'] = sosText
            for i in range(self.maxRarity):
                if i < rarity:
                    self.rarityStars[i].show()
                else:
                    self.rarityStars[i].hide()

        if fCallable:
            self.sosCallButton.show()
            self.sosCountInfo.setPos(-0.4, 0, self.sosCountInfoPosZ)
            self.sosCountInfo['text_scale'] = self.sosCountInfoScale
            self.sosCountInfo['text_align'] = TextNode.ALeft
        else:
            self.sosCallButton.hide()
            self.sosCountInfo.setPos(0, 0, self.sosCountInfo2PosZ)
            self.sosCountInfo['text_scale'] = self.sosCountInfo2Scale
            self.sosCountInfo['text_align'] = TextNode.ACenter
        if count > 0:
            countText = TTLocalizer.NPCFriendPanelRemaining % count
            self.sosCallButton['state'] = DGG.NORMAL
        else:
            countText = 'Unavailable'
            self.sosCallButton['state'] = DGG.DISABLED
        self.sosCountInfo['text'] = countText
        return

    def showFront(self):
        self.front.show()
        self.back.hide()

    def showBack(self):
        self.front.hide()
        self.back.show()

    def createNPCToonHead(self, NPCID, dimension = 0.5):
        NPCInfo = NPCToons.NPCToonDict[NPCID]
        dnaList = NPCInfo[2]
        gender = NPCInfo[3]
        if dnaList == 'r':
            dnaList = NPCToons.getRandomDNA(NPCID, gender)
        dna = ToonDNA.ToonDNA()
        dna.newToonFromProperties(*dnaList)
        head = ToonHead.ToonHead()
        head.setupHead(dna, forGui=1)
        self.fitGeometry(head, fFlip=1, dimension=dimension)
        return head

    def fitGeometry(self, geom, fFlip = 0, dimension = 0.5):
        p1 = Point3()
        p2 = Point3()
        geom.calcTightBounds(p1, p2)
        if fFlip:
            t = p1[0]
            p1.setX(-p2[0])
            p2.setX(-t)
        d = p2 - p1
        biggest = max(d[0], d[2])
        s = dimension / biggest
        mid = (p1 + d / 2.0) * s
        geomXform = hidden.attachNewNode('geomXform')
        for child in geom.getChildren():
            child.reparentTo(geomXform)

        geomXform.setPosHprScale(-mid[0], -mid[1] + 1, -mid[2], 180, 0, 0, s, s, s)
        geomXform.reparentTo(geom)
