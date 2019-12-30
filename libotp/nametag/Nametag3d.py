import math

from panda3d.core import *

from . import NametagGlobals
from .Nametag import Nametag
from ._constants import *


class Nametag3d(Nametag, PandaNode):
    def __init__(self):
        Nametag.__init__(self, 10.5)
        PandaNode.__init__(self, 'unnamed')

        self.m_np_360 = None
        self.m_np_372 = None
        self.m_np_balloon = None

        # self.setCullCallback()
        # safe_to_flatten_below: 0
        self.cbNode = CallbackNode(self.getName() + '-cbNode')
        self.cbNode.setCullCallback(PythonCallbackObject(self.cullCallback))
        self.addChild(self.cbNode)

        self.m_billboard_offset = 3.0

        self.m_np_top = NodePath.anyPath(PandaNode('top'))
        self.m_is_3d = 1
        self.m_field_396 = 0
        self.m_name_frame = Vec4(0, 0, 0, 0)
        self.m_chat_contents = None

        self.setBounds(BoundingSphere((0, 0, 0), 2.0))

    def setBillboardOffset(self, billboard_offset):
        self.m_billboard_offset = billboard_offset

    def getBillboardOffset(self):
        return self.m_billboard_offset

    def cullCallback(self, traverse_data):
        if self.isGroupManaged():
            # sort = CullBinManager.getGlobalPtr().getBinSort(traverse_data._state.getBinIndex())
            # np = traverse_data._node_path.getNodePath()
            traverser = traverse_data.getTrav()
            np = NodePath.anyPath(self)
            sort = CullBinManager.getGlobalPtr().getBinSort(traverser.getInitialState().getBinIndex())
            self.adjustToCamera(np, sort)

    def manage(self, manager):
        self.m_np_top.reparentTo(NodePath.anyPath(self))
        self.updateContents()

    def unmanage(self, manager):
        self.m_np_top.detachNode()
        Nametag.unmanage(self, manager)

    def updateContents(self):
        self.stopFlash()

        if self.m_has_draw_order:
            bin = config.GetString('nametag-fixed-bin', 'fixed')
            self.m_np_top.setBin(bin, self.m_draw_order)

        else:
            self.m_np_top.clearBin()

        if self.m_group:
            self.setName(self.m_group.getName())

        else:
            self.setName('unnamed')

        if self.m_np_360:
            self.m_np_360.removeNode()

        if self.m_np_372:
            self.m_np_372.removeNode()

        if self.m_np_balloon:
            self.m_np_balloon.removeNode()

        self.m_np_top.node().removeAllChildren()

        self.m_chat_contents = self.determineContents()
        if self.isGroupManaged():
            if self.m_chat_contents & 2:
                self.generateChat(NametagGlobals._speech_balloon_3d)

            elif self.m_chat_contents & 4:
                self.generateChat(NametagGlobals._thought_balloon_3d)

            elif self.m_chat_contents & 1:
                self.generateName()

    def release(self, arg):
        if arg.getButton() == MouseButton.one():
            self.setState(PGButton.SRollover)
            if self.m_group:
                self.m_group.click()

    def generateChat(self, balloon):
        v5 = self.getState()
        text_color = Vec4(NametagGlobals.getChatFg(self.m_group.getColorCode(), v5))
        balloon_color = Vec4(NametagGlobals.getChatBg(self.m_group.getColorCode(), v5))

        if self.m_group.m_chat_flags & CFQuicktalker:
            balloon_color = Vec4(self.m_group.getQtColor())

        text = self.m_group.getChat()
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
                                          text_color, balloon_color, self.m_is_3d,
                                          self.m_has_draw_order, self.m_draw_order,
                                          page_button, self.m_group.willHaveButton(),
                                          reversed, new_button)

        self.m_np_balloon = self.m_np_top.attachNewNode(balloon_result)
        if new_button[0]:
            self.startFlash(new_button[0])

        self.m_name_frame = balloon.m_text_frame
        self.m_field_396 = 1

    def generateName(self):
        v4 = self.getState()
        v56 = Vec4(NametagGlobals.getNameFg(self.m_group.getColorCode(), v4))
        v54 = Vec4(NametagGlobals.getNameBg(self.m_group.getColorCode(), v4))

        self.m_name_frame = Vec4(*self.m_group.getNameFrame())
        self.m_name_frame[0] -= NametagGlobals._card_pad[0]
        self.m_name_frame[1] += NametagGlobals._card_pad[1]
        self.m_name_frame[2] -= NametagGlobals._card_pad[2]
        self.m_name_frame[3] += NametagGlobals._card_pad[3]
        self.m_field_396 = 1

        v47 = None
        if v54[3] != 0.0:
            card = CardMaker('nametag')
            card.setFrame(self.m_name_frame)
            card.setColor(v54)
            if NametagGlobals._nametag_card:
                card.setSourceGeometry(NametagGlobals._nametag_card.node(),
                                       NametagGlobals._nametag_card_frame)

            self.m_np_372 = self.m_np_top.attachNewNode(card.generate())
            self.m_np_372.setTransparency(1)
            v47 = self.m_np_372.find('**/+GeomNode')

        label86 = False
        if self.m_is_3d:
            if self.m_group.m_name_icon:
                self.m_group.m_name_icon.instanceTo(self.m_np_top)

            if v47:
                self.m_np_360 = self.m_group.copyNameTo(v47)
                self.m_np_360.setDepthWrite(0)
                self.m_np_360.setY(-0.01)  # Panda3D 1.10 hack to prevent z-fighting.
                v47.node().setEffect(DecalEffect.make())

            else:
                label86 = True

        else:
            label86 = True

        if label86:
            self.m_np_360 = self.m_group.copyNameTo(self.m_np_top)
            if self.m_has_draw_order:
                bin = config.GetString('nametag-fixed-bin', 'fixed')
                self.m_name_icon.setBin(bin, self.m_draw_order + 1)
                self.m_np_360.setBin(bin, self.m_draw_order + 2)

        self.m_np_360.setColor(v56)
        if v56[3] != 1.0:
            self.m_np_360.setTransparency(1)

    def adjustToCamera(self, np, sort):
        if self.m_is_3d:
            lens = NametagGlobals._camera.node().getLens(0)
            if self.m_avatar or not self.m_group:
                v131 = self.m_avatar

            else:
                v131 = self.m_group.m_avatar

            v130 = NametagGlobals._camera.getTransform(np)
            v25 = v130.getMat()
            v204 = v25.xformVec(Vec3.up())
            v203 = v25.xformVec(Vec3.forward())

            v193 = Mat3()
            lookAt(v193, Vec3(v203), Vec3(v204))
            v177 = Mat4(v193)
            v177_3_0 = v177[3][0]
            v177_3_1 = v177[3][1]

            a3 = np.getTransform(NametagGlobals._camera).getMat()
            v122 = a3[3][1]
            v30 = max(v122, 0.1)
            v31 = v30 * 0.02
            v121 = (v31 ** 0.5) * NametagGlobals.getGlobalNametagScale() * 0.56
            if self.m_billboard_offset == 0.0:
                v42 = 0

            else:
                v32 = v25[0][1]
                v33 = v25[0][0]
                v136 = v25[0][2]
                v134 = v33
                v127 = self.m_billboard_offset
                v144 = math.sqrt(v136 * v136 + v32 * v32 + v134 * v134)
                v129 = self.m_billboard_offset / v144
                if v122 > 0.0:
                    if isinstance(lens, PerspectiveLens):
                        v37 = lens.getNear() + 0.001
                        if v122 - v129 < v37:
                            v129 = v122 - v37
                            v127 = v129 * v144

                        v121 = (v122 - v129) / v122 * v121

                v38 = v25[3][0]
                v39 = v25[3][1]
                v126 = v25[3][2]
                v125 = v39
                v129 = v126 * v126 + v39 * v39 + v38 * v38
                if v129 == 0.0:
                    v125 = 0.0
                    v38 = 0.0
                    v126 = 0.0

                else:
                    v40 = v129 - 1.0
                    if abs(v40) > 0.0:  # if ( v40 >= 1.0e-12 || v40 <= -1.0e-12 ) NOT ALMOST ZERO
                        v41 = 1.0 / math.sqrt(v129)
                        v38 *= v41
                        v125 *= v41
                        v126 *= v41

                v126 *= v127
                v177_3_0 = v38 * v127
                v177_3_1 = v125 * v127
                v42 = v126

            v205 = Mat4(v177[0][0] * v121, v177[0][1] * v121, v177[0][2] * v121, v177[0][3] * v121,
                        v177[1][0] * v121, v177[1][1] * v121, v177[1][2] * v121, v177[1][3] * v121,
                        v177[2][0] * v121, v177[2][1] * v121, v177[2][2] * v121, v177[2][3] * v121,
                        v177_3_0, v177_3_1, v42, v177[3][3])
            self.m_np_top.setMat(v205)

            v51 = 0
            if self.displayAsActive():
                if not self.m_chat_contents & (2 | 4):
                    v51 = 1

                elif not self.m_group:
                    v51 = 1

                elif self.m_group.m_has_timeout:
                    v51 = 1

                elif not self.m_group.willHaveButton():
                    v51 = 1

                elif self.m_group.getPageNumber() >= self.m_group.getNumChatPages() - 1:
                    v51 = 1

            v123 = 0
            sorta = 0
            frame = Vec4(0, 0, 0, 0)
            v150 = lens.getProjectionMat()

            if v51:
                v138, v139, v140 = v205.xformVec(Vec3(-2.5, 0.0, 1.0))
                v124, v125, v126 = v205.xformVec(Vec3(2.5, 0.0, 1.0))

                v121 = np.getTransform(v131)
                if v121.isInvalid():
                    return

                v64 = v121.getMat()
                v138, v139, v140 = v64.xformPoint(Point3(v138, v139, v140))
                v124, v125, v126 = v64.xformPoint(Point3(v124, v125, v126))

                v122 = v131.getTransform(NametagGlobals._camera)
                if v122.isInvalid():
                    return

                v124, v125, v126 = v122.getMat().xformPoint(Point3(v124, v125, v126))
                v134, v135, v136 = v122.getMat().xformPoint(Point3(v138, v139, 0.0))

                a2 = v150.xform(Vec4(v124, v125, v126, 1.0))
                frame = v150.xform(Vec4(v134, v135, v136, 1.0))

                if a2[3] <= 0.0 or frame[3] <= 0.0:
                    self.m_group.m_nametag3d_flag &= (self.m_group.m_nametag3d_flag <= 0) - 1
                    self.deactivate()
                    return

                v123 = 1
                v133 = 1.0 / frame[3]
                v128 = 1.0 / a2[3]
                frame = Vec4(frame[0] * v133, a2[0] * v128, frame[1] * v133, a2[1] * v128)

            v89 = 0
            if self.m_field_396:
                v124, v125, v126 = v205.xformPoint(Point3(self.m_name_frame[0] - 0.5, 0.0, self.m_name_frame[2] - 1.0))
                v138, v139, v140 = v205.xformPoint(Point3(self.m_name_frame[1] + 0.5, 0.0, self.m_name_frame[3] + 1.0))

                v124, v125, v126 = a3.xformPoint(Point3(v124, v125, v126))
                v138, v139, v140 = a3.xformPoint(Point3(v138, v139, v140))

                a2 = v150.xform(Vec4(v138, v139, v140, 1.0))
                v134, v135, v136, v137 = v150.xform(Vec4(v124, v125, v126, 1.0))

                if v137 <= 0.0 or a2[3] <= 0.0:
                    v89 = 1

                else:
                    v133 = 1.0 / v137
                    v109 = 1.0 / a2[3]
                    v110 = v109 * a2[1]
                    v127 = v133 * v135
                    v131 = v109 * a2[0]
                    v111 = v133 * v134
                    v146 = v111
                    if v111 < -1.0 or v131 > 1.0 or v127 < -1.0 or v110 > 1.0:
                        v89 = 1

                    if v123:
                        if frame[3] > v110:
                            v110 = frame[3]
                        if frame[2] >= v127:
                            v115 = v127
                        else:
                            v115 = frame[2]
                        if frame[1] <= v131:
                            v116 = v131
                        else:
                            v116 = frame[1]
                        if frame[0] >= v146:
                            frame[0] = v146

                        frame[1] = v116
                        frame[2] = v115

                    else:
                        frame[0] = v146
                        frame[1] = v131
                        frame[2] = v127
                        v123 = 1

                    frame[3] = v110
                    sorta = int(v125 * -100.0)

            if v123 and self.displayAsActive():
                self.setRegion(frame, sorta)

            v118 = self.m_group.m_nametag3d_flag
            if v89:
                v118 = max(v118, 1)

            elif v118 <= 2:
                v118 = 2

            self.m_group.setNametag3dFlag(v118)
            return

        self.m_group.incrementNametag3dFlag(2)
        if not self.displayAsActive():
            return

        if not self.m_field_396:
            return

        v12 = np.getNetTransform().getMat()
        v124 = v12.xformPoint(Point3(self.m_name_frame[0] - 0.5, 0, self.m_name_frame[2] - 1.0))
        v16 = v12.xformPoint(Point3(self.m_name_frame[1] + 0.5, 0, self.m_name_frame[3] + 1.0))

        v131 = Vec4(v124[0], v16[0], v124[2], v16[2])
        self.setRegion(v131, sort)
