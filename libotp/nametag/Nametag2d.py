import math

from panda3d.core import *

from . import NametagGlobals
from .MarginPopup import MarginPopup
from .Nametag import Nametag
from ._constants import *


class Nametag2d(Nametag, MarginPopup):
    def __init__(self):
        Nametag.__init__(self, 8.075)
        MarginPopup.__init__(self)

        self.m_copied_np = None
        self.m_attached_np = None
        self.m_arrow = None
        self.m_unknown_np = None

        # self.setCullCallback()
        self.cbNode = CallbackNode(self.getName() + '-cbNode')
        self.cbNode.setCullCallback(PythonCallbackObject(self.cullCallback))
        self.addChild(self.cbNode)

        self.setName('unnamed')

        self.m_contents = 3
        self.m_chat_contents = 0
        self.updateContents()
        self.m_on = NametagGlobals._master_arrows_on
        self.m_seq2d = 0

        self.m_trans_vec = Vec3(0, 0, 0)

    def setVisible(self, value):
        self.m_visible = value
        self.updateContents()

    def manage(self, manager):
        self.updateContents()
        manager.managePopup(self)

    def unmanage(self, manager):
        Nametag.unmanage(self, manager)
        manager.unmanagePopup(self)

    def setObjectCode(self, objcode):
        if self.m_group:
            self.m_group.setObjectCode(objcode)

    def getObjectCode(self):
        if self.m_group:
            return self.m_group.getObjectCode()

        return 0

    def getScore(self):
        if self.m_group:
            return 1000 - self.getDistance2()

        return 0

    def getDistance2(self):
        if self.m_avatar:
            np = self.m_avatar

        else:
            np = self.m_group.getAvatar()

        if np.isEmpty():
            return 0

        return np.getPos(NametagGlobals._toon).lengthSquared()

    def considerVisible(self):
        from .NametagGroup import NametagGroup

        v2 = 0
        do_update = True
        if self.m_on != NametagGlobals._master_arrows_on:
            self.m_on = NametagGlobals._master_arrows_on
            v2 = 1

        if self.m_seq2d == NametagGlobals._margin_prop_seq:
            if not v2:
                do_update = False

        else:
            self.m_seq2d = NametagGlobals._margin_prop_seq

        if do_update:
            self.updateContents()

        if not self.m_chat_contents:
            return 0

        result = self.m_group.m_nametag3d_flag != 2
        if NametagGlobals._onscreen_chat_forced and self.m_chat_contents & (Nametag.CSpeech | Nametag.CThought):
            result = 1

        self.m_group.setNametag3dFlag(0)
        if result and self.m_group.getColorCode() in (NametagGroup.CCToonBuilding,
                                                      NametagGroup.CCSuitBuilding,
                                                      NametagGroup.CCHouseBuilding):
            return self.getDistance2() < 1600

        return result

    def updateContents(self):
        self.stopFlash()
        if self.m_group:
            self.setName(self.m_group.getName())

        else:
            self.setName('unnamed')

        if self.m_copied_np:
            self.m_copied_np.removeNode()

        if self.m_attached_np:
            self.m_attached_np.removeNode()

        if self.m_arrow:
            self.m_arrow.removeNode()

        if self.m_unknown_np:
            self.m_unknown_np.removeNode()

        self.m_chat_contents = self.determineContents()
        if not NametagGlobals._master_arrows_on:
            self.m_chat_contents = self.m_chat_contents & ~1

        if self.m_visible and self.isGroupManaged():
            v10 = self.m_chat_contents
            if v10 & Nametag.CSpeech:
                self.generateChat(NametagGlobals._speech_balloon_2d)

            elif v10 & Nametag.CThought:
                self.generateChat(NametagGlobals._thought_balloon_2d)

            elif v10 & Nametag.CName:
                self.generateName()

    def frameCallback(self):
        if self.m_visible and self.m_popup_region:
            self.m_seq = self.m_group.m_region_seq

        if self.m_group:
            self.m_group.updateRegions()

    def rotateArrow(self):
        if not self.m_arrow:
            return

        if self.m_avatar:
            np = self.m_avatar

        else:
            np = self.m_group.getAvatar()

        if not np:
            return

        relpos = np.getPos(NametagGlobals._camera) - NametagGlobals._toon.getPos(NametagGlobals._camera)
        hpr = Vec3(0, 0, -math.atan2(relpos[1], relpos[0]) * 180 / math.pi)
        scale = Vec3(0.5, 0.5, 0.5)
        shear = Vec3(0, 0, 0)

        temp_mat_3 = Mat3()
        composeMatrix(temp_mat_3, scale, shear, hpr)
        arrow_mat = Mat4(temp_mat_3, self.m_trans_vec)
        self.m_arrow.setMat(arrow_mat)

    def generateName(self):
        v4 = self.getState()
        v84 = Vec4(NametagGlobals.getNameFg(self.m_group.getColorCode(), v4))
        v75 = Vec4(NametagGlobals.getNameBg(self.m_group.getColorCode(), v4))
        v75[3] = max(v75[3], NametagGlobals._min_2d_alpha)
        v75[3] = min(v75[3], NametagGlobals._max_2d_alpha)

        v67 = NametagGlobals._card_pad[3] + self.m_group.m_name_frame[3]
        v68 = self.m_group.m_name_frame[2] - NametagGlobals._card_pad[2]

        wordwrap = self.m_group.getNameWordwrap()
        v17 = self.m_cell_width / wordwrap * 2.0
        v66 = 0.333 * (1.0 / v17) - (v68 + v67) * 0.5
        v18 = min(1.0 / v17 - v67, v66)

        v69 = Mat4(v17, 0, 0, 0,
                   0, v17, 0, 0,
                   0, 0, v17, 0,
                   0, 0, v18 * v17, 1.0)
        a3 = v69

        if v75[3] != 0.0:
            card = CardMaker('nametag')
            card.setFrame(self.m_group.m_name_frame[0] - NametagGlobals._card_pad[0],
                          self.m_group.m_name_frame[1] + NametagGlobals._card_pad[1],
                          v68, v67)
            card.setColor(v75)
            if NametagGlobals._nametag_card:
                card.setSourceGeometry(NametagGlobals._nametag_card.node(),
                                       NametagGlobals._nametag_card_frame)

            self.m_attached_np = self.m_np.attachNewNode(card.generate())
            self.m_attached_np.setMat(v69)
            if v75[3] != 1.0:
                self.m_attached_np.setTransparency(1)

            if self.m_has_draw_order:
                bin = config.GetString('nametag-fixed-bin', 'fixed')
                self.m_attached_np.setBin(bin, self.m_draw_order)

        self.m_copied_np = self.m_group.copyNameTo(self.m_np)
        self.m_copied_np.setMat(a3)
        if self.m_has_draw_order:
            bin = config.GetString('nametag-fixed-bin', 'fixed')
            self.m_copied_np.setBin(bin, self.m_draw_order)

        self.m_copied_np.setColor(v84)
        if v84[3] != 1.0:
            self.m_copied_np.setTransparency(1)

        reducer = SceneGraphReducer()
        reducer.applyAttribs(self.m_copied_np.node())
        reducer.applyAttribs(self.m_attached_np.node())

        if NametagGlobals._arrow_model:
            self.m_arrow = NametagGlobals._arrow_model.copyTo(self.m_np)
            if self.m_has_draw_order:
                bin = config.GetString('nametag-fixed-bin', 'fixed')
                self.m_arrow.setBin(bin, self.m_draw_order)

            self.m_trans_vec = a3.xformPoint(Point3(0, 0, v68 - 1.0))

            color = Vec4(NametagGlobals.getArrowColor(self.m_group.getColorCode()))
            self.m_arrow.setColor(color)
            if color[3] != 1.0:
                self.m_arrow.setTransparency(1)

            self.rotateArrow()

        elif self.m_arrow:
            self.m_arrow.removeNode()

        v69 = self.m_np.getNetTransform().getMat()
        v69 = a3 * v69

        v77 = v69.xformPoint(Point3(self.m_group.m_name_frame[0] - NametagGlobals._card_pad[0], 0, v68))
        v80 = v69.xformPoint(Point3(self.m_group.m_name_frame[1] + NametagGlobals._card_pad[1], 0, v67))

        frame = Vec4(v77[0], v80[0], v77[2], v80[2])
        self.setRegion(frame, 0)

    def generateChat(self, balloon):
        v5 = self.getState()
        text_color = Vec4(NametagGlobals.getChatFg(self.m_group.getColorCode(), v5))
        balloon_color = Vec4(NametagGlobals.getChatBg(self.m_group.getColorCode(), v5))

        if self.m_group.m_chat_flags & CFQuicktalker:
            balloon_color = Vec4(self.m_group.getQtColor())

        balloon_color[3] = max(balloon_color[3], NametagGlobals._min_2d_alpha)
        balloon_color[3] = min(balloon_color[3], NametagGlobals._max_2d_alpha)

        text = self.m_group.getChat()
        if self.m_group.m_name:
            text = '%s: %s' % (self.m_group.m_name, text)

        has_page_button = False
        has_quit_button = False
        if not self.m_group.m_has_timeout:
            has_page_button = self.m_group.m_chat_flags & CFPageButton
            if self.m_group.getPageNumber() >= self.m_group.getNumChatPages() - 1:
                if self.m_group.m_chat_flags & CFQuitButton:
                    has_page_button = False
                    has_quit_button = True

        page_button = None
        if has_page_button:
            page_button = NametagGlobals.getPageButton(v5)

        elif has_quit_button:
            page_button = NametagGlobals.getQuitButton(v5)

        reversed = self.m_group.m_chat_flags & CFReversed
        new_button = [None]
        balloon_result = balloon.generate(text, self.m_group.getChatFont(), self.m_wordwrap,
                                          text_color, balloon_color, False,
                                          self.m_has_draw_order, self.m_draw_order,
                                          page_button, self.m_group.willHaveButton(),
                                          reversed, new_button)

        self.m_unknown_np = self.m_np.attachNewNode(balloon_result)

        v88 = 8.0  # XXX THIS IS A GUESS
        v49 = 2 * self.m_cell_width
        a6 = v49 / (v88 + 1.0)
        v50 = balloon.m_text_height * balloon.m_hscale
        v85 = balloon.m_hscale * 5.0
        v88 = v50 * 0.5
        v113 = -(balloon.m_hscale * 0.5 + v85)
        v51 = -(NametagGlobals._balloon_text_origin[2] + v88)
        v118 = Mat4(a6, 0, 0, 0,
                    0, a6, 0, 0,
                    0, 0, a6, 0,
                    v113 * a6, 0, v51 * a6, 1.0)

        self.m_unknown_np.setMat(v118)

        reducer = SceneGraphReducer()
        reducer.applyAttribs(self.m_unknown_np.node())

        v66 = self.m_np.getNetTransform().getMat()

        # XXX THE LINES BELOW ARE A GUESS
        v67 = v113 * a6
        v68 = v51 * a6
        v94 = v66.xformPoint(Point3(v67, 0.0, v68))
        v97 = v66.xformPoint(Point3(-v67, 0.0, -v68))

        frame = Vec4(v94[0], v97[0], v94[2], v97[2])
        self.setRegion(frame, 0)

    def cullCallback(self, *args):
        self.rotateArrow()
        if self.m_visible and self.m_popup_region:
            self.m_seq = self.m_group.getRegionSeq()
