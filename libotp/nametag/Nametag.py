from direct.interval.IntervalGlobal import *

from .ClickablePopup import *
from ._constants import *


class Nametag(ClickablePopup):
    CName = 1
    CSpeech = 2
    CThought = 4

    def __init__(self, wordwrap):
        ClickablePopup.__init__(self)

        self.m_avatar = None
        self.m_ival = None
        self.m_popup_region = None
        self.m_seq = 0
        self.m_mouse_watcher = None
        self.m_draw_order = 0
        self.m_has_draw_order = False

        self.m_contents = CFSpeech | CFThought | CFQuicktalker
        self.m_active = True
        self.m_field_12 = 0
        self.m_group = None
        self.m_wordwrap = wordwrap
        self.m_has_region = False
        self.m_ival_name = 'flash-%d' % id(self)

    def clearAvatar(self):
        self.m_avatar = None

    def clearDrawOrder(self):
        self.m_has_draw_order = False
        self.updateContents()

    def click(self):
        if self.m_group:
            self.m_group.click()

    def deactivate(self):
        if self.m_has_region:
            if self.m_mouse_watcher:
                self.m_popup_region.deactivate()
                self.m_mouse_watcher.removeRegion(self.m_popup_region)
                self.m_mouse_watcher = None

            self.m_has_region = None

        self.m_seq = 0

    def determineContents(self):
        if self.m_group and self.m_group.isManaged():
            v3 = self.m_contents & self.m_group.getContents()
            v4 = self.m_group.m_chat_flags

            if v4 & CFSpeech:
                if v3 & Nametag.CSpeech:
                    return Nametag.CSpeech

            elif v4 & CFThought and v3 & Nametag.CThought:
                return Nametag.CThought

            if v3 & Nametag.CName and self.m_group.getName() and NametagGlobals._master_nametags_visible:
                return Nametag.CName

        return 0

    def displayAsActive(self):
        if not self.m_active:
            return 0

        if self.m_group:
            return self.m_group.displayAsActive()

        else:
            return NametagGlobals._master_nametags_active

    def setAvatar(self, avatar):
        self.m_avatar = avatar

    def getAvatar(self):
        return self.m_avatar

    def setChatWordwrap(self, wordwrap):
        self.m_wordwrap = wordwrap

    def getChatWordwrap(self):
        return self.m_wordwrap

    def getGroup(self):
        return self.m_group

    def getState(self):
        if self.m_group:
            if not (self.m_active and self.m_group.displayAsActive()):
                return PGButton.SInactive

        elif not (self.m_active and NametagGlobals._master_nametags_active):
            return PGButton.SInactive

        return self.m_state

    def hasGroup(self):
        return self.m_group is not None

    def setActive(self, active):
        self.m_active = active
        self.updateContents()

    def isActive(self):
        return self.m_active

    def isGroupManaged(self):
        return self.m_group and self.m_group.isManaged()

    def keepRegion(self):
        if self.m_popup_region:
            self.m_seq = self.m_group.getRegionSeq()

    def manage(self, manager):
        self.updateContents()

    def unmanage(self, manager):
        self.updateContents()
        self.deactivate()

    def setContents(self, contents):
        self.m_contents = contents
        self.updateContents()

    def setDrawOrder(self, draw_order):
        self.m_draw_order = draw_order
        self.m_has_draw_order = True
        self.updateContents()

    def setRegion(self, frame, sort):
        if self.m_popup_region:
            self.m_popup_region.setFrame(frame)

        else:
            self.m_popup_region = self._createRegion(frame)

        self.m_popup_region.setSort(int(sort))
        self.m_seq = self.m_group.getRegionSeq()

    def startFlash(self, np):
        self.stopFlash()
        self.m_ival = Sequence(
            np.colorInterval(0.5, Vec4(1.0, 1.0, 1.0, 0.5), startColor=Vec4(1.0, 1.0, 1.0, 1.0), blendType='easeOut'),
            np.colorInterval(0.5, Vec4(1.0, 1.0, 1.0, 1.0), startColor=Vec4(1.0, 1.0, 1.0, 0.5), blendType='easeIn'))
        self.m_ival.loop()

    def stopFlash(self):
        if self.m_ival:
            self.m_ival.finish()
            self.m_ival = None

    def updateRegion(self, seq):
        if seq == self.m_seq:
            is_active = self.displayAsActive()

        else:
            is_active = False

        if self.m_has_region:
            if self.m_mouse_watcher != NametagGlobals._mouse_watcher:
                if self.m_mouse_watcher:
                    self.m_popup_region.deactivate()
                    self.m_mouse_watcher.removeRegion(self.m_popup_region)

                self.m_has_region = False
                self.setState(PGButton.SReady)

        if is_active:
            if (not self.m_has_region) and self.m_popup_region:
                if self.m_mouse_watcher != NametagGlobals._mouse_watcher:
                    self.m_mouse_watcher = NametagGlobals._mouse_watcher

                if self.m_mouse_watcher:
                    self.m_popup_region.activate()
                    self.m_mouse_watcher.addRegion(self.m_popup_region)

                self.m_has_region = True

        elif self.m_has_region:
            if self.m_mouse_watcher and self.m_popup_region:
                self.m_popup_region.deactivate()
                self.m_mouse_watcher.removeRegion(self.m_popup_region)

            self.m_has_region = False
            self.m_mouse_watcher = None
            self.setState(PGButton.SReady)

    def upcastToPandaNode(self):
        return self
