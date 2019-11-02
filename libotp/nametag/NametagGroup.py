from panda3d.core import *

import NametagGlobals
from Nametag2d import Nametag2d
from Nametag3d import Nametag3d
from _constants import *


class NametagGroup:
    CCNormal = 0
    CCNoChat = 1
    CCNonPlayer = 2
    CCSuit = 3
    CCToonBuilding = 4
    CCSuitBuilding = 5
    CCHouseBuilding = 6
    CCSpeedChat = 7
    CCFreeChat = 8

    _unique_index = 0

    def __init__(self):
        self.m_nametags = []

        self.m_name_font = None
        self.m_chat_font = None

        self.m_avatar = None
        self.m_node = None

        self.m_name = ''
        self.m_display_name = ''

        self.m_chat_pages = []
        self.m_stomp_text = ''
        self.m_unique_name = ''

        self.m_region_seq = 0

        self.m_name_icon = NodePath.anyPath(PandaNode('icon'))
        self.m_name_frame = Vec4(0, 0, 0, 0)

        self.m_wordwrap = -1.0
        self.m_color_code = 0
        self.m_qt_color = Vec4(NametagGlobals._default_qt_color)
        self.m_balloon_color = Vec4(NametagGlobals._balloon_modulation_color)
        self.m_shadow = (0, 0)
        self.m_has_shadow = False

        self.m_timeout = 0.0
        self.m_timeout_start = 0.0
        self.m_has_timeout = False
        self.m_stomp_time = 0.0
        self.m_stomp_chat_flags = None
        self.m_chat_flags = 0
        self.m_page_number = 0
        self.m_stomp_delay = 0.5
        self.m_chat_stomp = 0

        self.m_unique_name = 'nametag-%d' % NametagGroup._unique_index
        NametagGroup._unique_index += 1

        self.m_object_code = 0
        self.m_nametag3d_flag = 0
        self.m_manager = None

        self.m_region_seq += 1

        self.m_contents = CFSpeech | CFThought | CFQuicktalker
        self.m_is_active = 1
        self.m_active = NametagGlobals._master_nametags_active
        self.m_visible = NametagGlobals._master_nametags_visible

        self.m_tag2d = Nametag2d()
        self.m_tag3d = Nametag3d()
        self.addNametag(self.m_tag2d)
        self.addNametag(self.m_tag3d)

    def setFont(self, font):
        self.setNameFont(font)
        self.setChatFont(font)

    def setNameFont(self, font):
        self.m_name_font = font

    def getNameFont(self):
        return self.m_name_font

    def setChatFont(self, font):
        self.m_chat_font = font

    def getChatFont(self):
        return self.m_chat_font

    def setAvatar(self, avatar):
        self.m_avatar = avatar

    def getAvatar(self):
        return self.m_avatar

    def setNameIcon(self, icon):
        self.m_name_icon = icon

    def getNameIcon(self):
        return self.m_name_icon

    def setColorCode(self, code):
        self.m_color_code = code

    def getColorCode(self):
        return self.m_color_code

    def setContents(self, contents):
        self.m_contents = contents

    def getContents(self):
        return self.m_contents

    def setDisplayName(self, name):
        self.m_display_name = name

        if name and self.m_name_font:
            text_node = NametagGlobals.getTextNode()
            text_node.setFont(self.m_name_font)
            text_node.setWordwrap(self.getNameWordwrap())
            text_node.setAlign(TextNode.ACenter)
            text_node.setText(name)
            gen = text_node.generate()
            self.m_node = gen
            self.m_name_frame = text_node.getCardActual()

            if self.m_has_shadow:
                self.m_node = PandaNode('name')
                self.m_node.addChild(gen)

                pos = Point3(self.m_shadow[0], 0, -self.m_shadow[1])
                attached = NodePath.anyPath(self.m_node).attachNewNode(gen.copySubgraph())
                attached.setPos(pos)
                attached.setColor(0, 0, 0, 1)

        else:
            self.m_node = None

        self.updateContentsAll()

    def getDisplayName(self):
        return self.m_display_name

    def setName(self, name):
        self.m_name = name
        self.setDisplayName(name)

    def getName(self):
        return self.m_name

    def getNameFrame(self):
        return self.m_name_frame

    def setNameWordwrap(self, wordwrap):
        self.m_wordwrap = wordwrap
        self.setDisplayName(self.m_display_name)

    def getNameWordwrap(self):
        if self.m_wordwrap > 0.0:
            return self.m_wordwrap

        wordwrap = NametagGlobals.getNameWordwrap()
        return {self.CCNoChat: 7.8,
                self.CCToonBuilding: 8.5,
                self.CCSuitBuilding: 8.5,
                self.CCHouseBuilding: 10.0}.get(self.m_color_code, wordwrap)

    def getNametag(self, index):
        return self.m_nametags[index]

    def getNametag2d(self):
        return self.m_tag2d

    def getNametag3d(self):
        return self.m_tag3d

    def setNametag3dFlag(self, flag):
        self.m_nametag3d_flag = flag

    def getNametag3dFlag(self):
        return self.m_nametag3d_flag

    def getNumChatPages(self):
        return len(self.m_chat_pages)

    def getNumNametags(self):
        return len(self.m_nametags)

    def setObjectCode(self, code):
        self.m_object_code = code

    def getObjectCode(self):
        return self.m_object_code

    def setPageNumber(self, page):
        if self.m_page_number == page:
            return

        self.m_page_number = page
        if self.willHaveButton():
            self.m_timeout_start = globalClock.getFrameTime() + 0.2
            self.m_has_timeout = True

        self.updateContentsAll()

    def getPageNumber(self):
        return self.m_page_number

    def getBalloonModulationColor(self):
        return self.m_balloon_color

    def setQtColor(self, color):
        self.m_qt_color = color

    def getQtColor(self):
        return self.m_qt_color

    def getRegionSeq(self):
        return self.m_region_seq

    def setShadow(self, shadow):
        self.m_shadow = shadow

    def getShadow(self):
        return self.m_shadow

    def getStompDelay(self):
        return self.m_stomp_delay

    def getStompText(self):
        return self.m_stomp_text

    def setUniqueId(self, name):
        self.m_unique_name = name

    def getUniqueId(self):
        return self.m_unique_name

    def hasButton(self):
        if self.m_has_timeout:
            return False

        return self.willHaveButton()

    def hasNoQuitButton(self):
        return (not self.m_has_timeout) and self.m_chat_flags & CFSpeech

    def hasQuitButton(self):
        return (not self.m_has_timeout) and self.m_chat_flags & CFQuitButton

    def hasPageButton(self):
        return (not self.m_has_timeout) and self.m_chat_flags & CFPageButton

    def hasShadow(self):
        return self.m_has_shadow

    def clearShadow(self):
        self.m_has_shadow = False

    def incrementNametag3dFlag(self, flag):
        self.m_nametag3d_flag = max(self.m_nametag3d_flag, flag)

    def isManaged(self):
        return self.m_manager is not None

    def manage(self, manager):
        if not self.m_manager:
            self.m_manager = manager
            for nametag in self.m_nametags:
                nametag.manage(manager)

    def unmanage(self, manager):
        if self.m_manager:
            self.m_manager = None
            for nametag in self.m_nametags:
                nametag.unmanage(manager)

    def addNametag(self, nametag):
        if nametag.m_group:
            print 'Attempt to add %s twice to %s.' % (nametag.__class__.__name__, self.m_name)
            return

        nametag.m_group = self
        nametag.updateContents()
        self.m_nametags.append(nametag)

        if self.m_manager:
            nametag.manage(self.m_manager)

    def removeNametag(self, nametag):
        if not nametag.m_group:
            print 'Attempt to removed %s twice from %s.' % (nametag.__class__.__name__, self.m_name)
            return

        if self.m_manager:
            nametag.unmanage(self.m_manager)

        nametag.m_group = None
        nametag.updateContents()
        self.m_nametags.remove(nametag)

    def setActive(self, active):
        self.m_is_active = active

    def isActive(self):
        return self.m_active

    def updateContentsAll(self):
        for nametag in self.m_nametags:
            nametag.updateContents()

    def updateRegions(self):
        for nametag in self.m_nametags:
            nametag.updateRegion(self.m_region_seq)

        self.m_region_seq += 1

        now = globalClock.getFrameTime()
        if self.m_stomp_time < now and self.m_chat_stomp > 1:
            self.m_chat_stomp = 0
            self.setChat(self.m_stomp_text, self.m_stomp_chat_flags, self.m_page_number)

        if self.m_chat_flags & CFTimeout and now >= self.m_timeout:
            self.clearChat()
            self.m_chat_stomp = 0

        v7 = False
        if self.m_has_timeout and now >= self.m_timeout_start:
            self.m_has_timeout = 0
            v7 = True

        if self.m_active != NametagGlobals._master_nametags_active:
            self.m_active = NametagGlobals._master_nametags_active
            v7 = True

        if self.m_visible == NametagGlobals._master_nametags_visible:
            if not v7:
                return

        else:
            self.m_visible = NametagGlobals._master_nametags_visible

        self.updateContentsAll()

    def willHaveButton(self):
        return self.m_chat_flags & (CFPageButton | CFQuitButton)

    def setChat(self, chat, chat_flags, page_number=0):
        self.m_chat_flags = chat_flags
        self.m_page_number = page_number

        now = globalClock.getFrameTime()
        must_split = True
        if chat_flags and chat:
            self.m_chat_stomp += 1
            if self.m_chat_stomp >= 2 and self.m_stomp_delay >= 0.05:
                self.m_stomp_text = chat
                self.m_stomp_chat_flags = self.m_chat_flags
                self.m_stomp_time = now + self.m_stomp_delay
                self.m_chat_flags = 0
                must_split = False

        else:
            self.m_chat_flags = 0
            self.m_chat_stomp = 0
            must_split = False

        if must_split:
            self.m_chat_pages = chat.split('\x07')
        else:
            self.m_chat_pages = []

        if self.m_chat_flags & CFTimeout and self.m_stomp_time < now:
            timeout = len(chat) * 0.5
            timeout = min(12.0, max(timeout, 4.0))
            self.m_timeout = timeout + now

        if self.willHaveButton():
            self.m_has_timeout = True
            self.m_timeout_start = now + 0.2

        else:
            self.m_has_timeout = False
            self.m_timeout_start = 0.0

        self.updateContentsAll()

    def getChat(self):
        if self.m_chat_pages:
            return self.m_chat_pages[self.m_page_number]

        return ''

    def clearChat(self):
        self.setChat('', 0, 0)

    def getChatStomp(self):
        return self.m_chat_stomp

    def clearAuxNametags(self):
        for nametag in self.nametags[:]:
            if nametag not in (self.m_tag2d, self.m_tag3d):
                self.removeNametag(nametag)

    def click(self):
        messenger.send(self.m_unique_name)

    def copyNameTo(self, to):
        return to.attachNewNode(self.m_node.copySubgraph())

    def displayAsActive(self):
        if self.m_is_active and NametagGlobals._master_nametags_active:
            return 1

        return self.hasButton()

    def frameCallback(self):
        # This should be in Nametag2d
        # I have no idea where libotp called it
        # so I'm doing it in MarginManager.update
        self.updateRegions()
