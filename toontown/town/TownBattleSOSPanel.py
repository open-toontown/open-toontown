from pandac.PandaModules import *
from toontown.toonbase.ToontownGlobals import *
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from direct.showbase import DirectObject
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import StateData
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
import types
from toontown.toon import NPCToons
from toontown.toon import NPCFriendPanel
from toontown.toonbase import ToontownBattleGlobals

class TownBattleSOSPanel(DirectFrame, StateData.StateData):
    notify = DirectNotifyGlobal.directNotify.newCategory('TownBattleSOSPanel')

    def __init__(self, doneEvent):
        DirectFrame.__init__(self, relief=None)
        self.initialiseoptions(TownBattleSOSPanel)
        StateData.StateData.__init__(self, doneEvent)
        self.friends = {}
        self.NPCFriends = {}
        self.textRolloverColor = Vec4(1, 1, 0, 1)
        self.textDownColor = Vec4(0.5, 0.9, 1, 1)
        self.textDisabledColor = Vec4(0.4, 0.8, 0.4, 1)
        self.bldg = 0
        self.chosenNPCToons = []
        return

    def load(self):
        if self.isLoaded == 1:
            return None
        self.isLoaded = 1
        bgd = loader.loadModel('phase_3.5/models/gui/frame')
        gui = loader.loadModel('phase_3.5/models/gui/frame4names')
        scrollGui = loader.loadModel('phase_3.5/models/gui/friendslist_gui')
        backGui = loader.loadModel('phase_3.5/models/gui/battle_gui')
        self['image'] = bgd
        self['image_pos'] = (0.0, 0.1, -0.08)
        self.setScale(0.3)
        self.title = DirectLabel(parent=self, relief=None, text=TTLocalizer.TownBattleSOSNoFriends, text_scale=0.4, text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1), pos=(0.0, 0.0, 1.5))
        self.NPCFriendPanel = NPCFriendPanel.NPCFriendPanel(parent=self, doneEvent=self.doneEvent)
        self.NPCFriendPanel.setPos(-0.75, 0, -0.15)
        self.NPCFriendPanel.setScale(0.325)
        self.NPCFriendsLabel = DirectLabel(parent=self, relief=None, text=TTLocalizer.TownBattleSOSNPCFriends, text_scale=0.3, text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1), pos=(-0.75, 0.0, -2.0))
        self.scrollList = DirectScrolledList(parent=self, relief=None, image=gui.find('**/frame4names'), image_scale=(0.11, 1, 0.1), text=TTLocalizer.FriendsListPanelOnlineFriends, text_scale=0.04, text_pos=(-0.02, 0.275), text_fg=(0, 0, 0, 1), incButton_image=(scrollGui.find('**/FndsLst_ScrollUp'),
         scrollGui.find('**/FndsLst_ScrollDN'),
         scrollGui.find('**/FndsLst_ScrollUp_Rllvr'),
         scrollGui.find('**/FndsLst_ScrollUp')), incButton_relief=None, incButton_pos=(0.0, 0.0, -0.3), incButton_image3_color=Vec4(0.6, 0.6, 0.6, 0.6), incButton_scale=(1.0, 1.0, -1.0), decButton_image=(scrollGui.find('**/FndsLst_ScrollUp'),
         scrollGui.find('**/FndsLst_ScrollDN'),
         scrollGui.find('**/FndsLst_ScrollUp_Rllvr'),
         scrollGui.find('**/FndsLst_ScrollUp')), decButton_relief=None, decButton_pos=(0.0, 0.0, 0.175), decButton_image3_color=Vec4(0.6, 0.6, 0.6, 0.6), itemFrame_pos=(-0.17, 0.0, 0.11), itemFrame_relief=None, numItemsVisible=9, items=[], pos=(2.4, 0.0, 0.025), scale=3.5)
        clipper = PlaneNode('clipper')
        clipper.setPlane(Plane(Vec3(-1, 0, 0), Point3(0.32, 0, 0)))
        clipNP = self.scrollList.component('itemFrame').attachNewNode(clipper)
        self.scrollList.component('itemFrame').setClipPlane(clipNP)
        self.close = DirectButton(parent=self, relief=None, image=(backGui.find('**/PckMn_BackBtn'), backGui.find('**/PckMn_BackBtn_Dn'), backGui.find('**/PckMn_BackBtn_Rlvr')), pos=(2.3, 0.0, -1.65), scale=3, text=TTLocalizer.TownBattleSOSBack, text_scale=0.05, text_pos=(0.01, -0.012), text_fg=Vec4(0, 0, 0.8, 1), command=self.__close)
        gui.removeNode()
        scrollGui.removeNode()
        backGui.removeNode()
        bgd.removeNode()
        self.hide()
        return

    def unload(self):
        if self.isLoaded == 0:
            return None
        self.isLoaded = 0
        self.exit()
        del self.title
        del self.scrollList
        del self.close
        del self.friends
        del self.NPCFriends
        DirectFrame.destroy(self)
        return None

    def makeFriendButton(self, friendPair):
        friendId, flags = friendPair
        handle = base.cr.playerFriendsManager.identifyFriend(friendId)
        if handle == None:
            base.cr.fillUpFriendsMap()
            return
        friendName = handle.getName()
        fg = Vec4(0.0, 0.0, 0.0, 1.0)
        if handle.isPet():
            com = self.__chosePet
        else:
            com = self.__choseFriend
        return DirectButton(relief=None, text=friendName, text_scale=0.04, text_align=TextNode.ALeft, text_fg=fg, text1_bg=self.textDownColor, text2_bg=self.textRolloverColor, text3_fg=self.textDisabledColor, command=com, extraArgs=[friendId, friendName])

    def makeNPCFriendButton(self, NPCFriendId, numCalls):
        if not TTLocalizer.NPCToonNames.has_key(NPCFriendId):
            return None
        friendName = TTLocalizer.NPCToonNames[NPCFriendId]
        friendName += ' %d' % numCalls
        fg = Vec4(0.0, 0.0, 0.0, 1.0)
        return DirectButton(relief=None, text=friendName, text_scale=0.04, text_align=TextNode.ALeft, text_fg=fg, text1_bg=self.textDownColor, text2_bg=self.textRolloverColor, text3_fg=self.textDisabledColor, command=self.__choseNPCFriend, extraArgs=[NPCFriendId])

    def enter(self, canLure = 1, canTrap = 1):
        if self.isEntered == 1:
            return None
        self.isEntered = 1
        if self.isLoaded == 0:
            self.load()
        self.canLure = canLure
        self.canTrap = canTrap
        self.factoryToonIdList = None
        messenger.send('SOSPanelEnter', [self])
        self.__updateScrollList()
        self.__updateNPCFriendsPanel()
        self.__updateTitleText()
        self.show()
        self.accept('friendOnline', self.__friendOnline)
        self.accept('friendOffline', self.__friendOffline)
        self.accept('friendsListChanged', self.__friendsListChanged)
        self.accept('friendsMapComplete', self.__friendsListChanged)
        return

    def exit(self):
        if self.isEntered == 0:
            return None
        self.isEntered = 0
        self.hide()
        self.ignore('friendOnline')
        self.ignore('friendOffline')
        self.ignore('friendsListChanged')
        self.ignore('friendsMapComplete')
        messenger.send(self.doneEvent)
        return None

    def __close(self):
        doneStatus = {}
        doneStatus['mode'] = 'Back'
        messenger.send(self.doneEvent, [doneStatus])

    def __choseFriend(self, friendId, friendName):
        doneStatus = {}
        doneStatus['mode'] = 'Friend'
        doneStatus['friend'] = friendId
        messenger.send(self.doneEvent, [doneStatus])

    def __chosePet(self, petId, petName):
        doneStatus = {}
        doneStatus['mode'] = 'Pet'
        doneStatus['petId'] = petId
        doneStatus['petName'] = petName
        messenger.send(self.doneEvent, [doneStatus])

    def __choseNPCFriend(self, friendId):
        doneStatus = {}
        doneStatus['mode'] = 'NPCFriend'
        doneStatus['friend'] = friendId
        self.chosenNPCToons.append(friendId)
        messenger.send(self.doneEvent, [doneStatus])

    def setFactoryToonIdList(self, toonIdList):
        self.factoryToonIdList = toonIdList[:]

    def __updateScrollList(self):
        newFriends = []
        battlePets = base.config.GetBool('want-pets-in-battle', 1)
        if base.wantPets and battlePets == 1 and base.localAvatar.hasPet():
            newFriends.append((base.localAvatar.getPetId(), 0))
        if not self.bldg or self.factoryToonIdList is not None:
            for friendPair in base.localAvatar.friendsList:
                if base.cr.isFriendOnline(friendPair[0]):
                    if self.factoryToonIdList is None or friendPair[0] in self.factoryToonIdList:
                        newFriends.append(friendPair)

            if hasattr(base.cr, 'playerFriendsManager'):
                for avatarId in base.cr.playerFriendsManager.getAllOnlinePlayerAvatars():
                    if not base.cr.playerFriendsManager.askAvatarKnownElseWhere(avatarId):
                        newFriends.append((avatarId, 0))

        for friendPair in self.friends.keys():
            if friendPair not in newFriends:
                friendButton = self.friends[friendPair]
                self.scrollList.removeItem(friendButton)
                if not friendButton.isEmpty():
                    friendButton.destroy()
                del self.friends[friendPair]

        for friendPair in newFriends:
            if not self.friends.has_key(friendPair):
                friendButton = self.makeFriendButton(friendPair)
                if friendButton:
                    self.scrollList.addItem(friendButton)
                    self.friends[friendPair] = friendButton

        return

    def __updateNPCFriendsPanel(self):
        self.NPCFriends = {}
        for friend, count in base.localAvatar.NPCFriendsDict.items():
            track = NPCToons.getNPCTrack(friend)
            if track == ToontownBattleGlobals.LURE_TRACK and self.canLure == 0 or track == ToontownBattleGlobals.TRAP_TRACK and self.canTrap == 0:
                self.NPCFriends[friend] = 0
            else:
                self.NPCFriends[friend] = count

        self.NPCFriendPanel.update(self.NPCFriends, fCallable=1)

    def __updateTitleText(self):
        isEmpty = (len(self.friends) == 0 and len(self.NPCFriends) == 0)
        if isEmpty:
            self.title['text'] = TTLocalizer.TownBattleSOSNoFriends
        else:
            self.title['text'] = TTLocalizer.TownBattleSOSWhichFriend

    def __friendOnline(self, doId, commonChatFlags, whitelistChatFlags):
        self.__updateScrollList()
        self.__updateTitleText()

    def __friendOffline(self, doId):
        self.__updateScrollList()
        self.__updateTitleText()

    def __friendsListChanged(self):
        self.__updateScrollList()
        self.__updateTitleText()
