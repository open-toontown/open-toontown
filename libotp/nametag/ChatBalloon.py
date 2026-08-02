from direct.directnotify import DirectNotifyGlobal
from panda3d.core import *

from . import NametagGlobals


class ChatBalloon:
    notify = DirectNotifyGlobal.directNotify.newCategory('ChatBalloon')

    def __init__(self, node=None):
        self.m_copy_node = None
        self.m_top_node = None
        self.m_top_mat = None
        self.m_middle_node = None
        self.m_middle_mat = None
        self.m_bottom_node = None
        self.m_bottom_mat = None

        self.m_hscale = 0
        self.m_text_height = 0
        self.m_text_frame = Vec4(0)

        self.scan(node)

    @staticmethod
    def find_geom_node(node):
        if node.isGeomNode():
            return node

        for i in range(node.getNumChildren()):
            n = ChatBalloon.find_geom_node(node.getChild(i))
            if n:
                return n

        return None

    @staticmethod
    def find_middle_geom(node):
        if not node.getNumChildren():
            return None

        child = None
        for i in range(node.getNumChildren()):
            child = node.getChild(i)
            if child.getName() == 'middle':
                return n

            n = ChatBalloon.find_middle_geom(child)
            if n:
                return n

        return ChatBalloon.find_geom_node(child)

    def scan(self, node):
        if node.getName() == 'chatBalloon':
            return self.scan_balloon(node)

        for i in range(node.getNumChildren()):
            if self.scan(node.getChild(i)):
                return True

        return False

    def scan_balloon(self, node):
        self.m_copy_node = node.copySubgraph()

        for i in range(node.getNumChildren()):
            child = node.getChild(i)
            if child.getName() == 'top':
                self.m_top_node = child
                self.m_top_mat = child.getTransform().getMat()

            elif child.getName() == 'middle':
                self.m_middle_node = child
                self.m_middle_mat = child.getTransform().getMat()

            elif child.getName() == 'bottom':
                self.m_bottom_node = child
                self.m_bottom_mat = child.getTransform().getMat()

        if self.m_top_node and self.m_middle_node and self.m_bottom_node:
            return True

        else:
            self.notify.warning('ChatBalloon geometry does not include top, middle, and bottom nodes.')
            return False

    def generate(self, text, font, wordwrap, text_color, balloon_color, for_3d,
                 has_draw_order, draw_order, page_button, space_for_button,
                 reversed, new_button):  # new_button is a pointer, let's use a list hack here
        chat_node = PandaNode('chat')
        chat_node.setAttrib(CullFaceAttrib.make(0))
        text_node = NametagGlobals.getTextNode()
        text_node.setFont(font)
        text_node.setWordwrap(wordwrap)
        text_node.setAlign(TextNode.ALeft)
        text_node.setText(text)

        v116 = NametagGlobals._balloon_text_origin[0]
        if reversed:
            v116 = v116 + 9.0

        v27 = (text_node.getRight() - text_node.getLeft()) * 0.11111111
        self.m_hscale = v27

        if v27 < 0.25:
            self.m_hscale = 0.25
            text_node.setAlign(TextNode.ACenter)

            v29 = v116
            if not reversed:
                v116 = v29 + 4.5

            else:
                v116 = v29 - 4.5

        elif reversed:
            self.m_hscale = -self.m_hscale

        self.m_text_frame = text_node.getCardActual()
        _space = 0.2 if space_for_button else 0.0
        num_rows = max(1, text_node.getNumRows())
        _num_rows = num_rows
        line_h = text_node.getFont().getLineHeight()

        num_rows_minus_1 = num_rows - 1
        subgraph_copy_mat = Mat4(self.m_hscale, 0, 0, 0,
                                 0, 1.0, 0, 0,
                                 0, 0, 1.0, 0,
                                 0, 0, 0, 1.0)
        text_h = _num_rows * line_h + _space
        self.m_text_height = text_h

        v132 = num_rows_minus_1 * line_h + _space

        middle_mat = Mat4(1, 0, 0, 0,
                          0, 1, 0, 0,
                          0, 0, text_h, 0,
                          0, 0, 0, 1) * self.m_middle_mat
        top_mat = Mat4(1, 0, 0, 0,
                       0, 1, 0, 0,
                       0, 0, 1, 0,
                       0, 0, text_h - 1.0, 1) * self.m_top_mat

        v137 = v116 * self.m_hscale
        v138 = 0.0
        v139 = NametagGlobals._balloon_text_origin[2] + v132 + 0.2

        self.m_text_frame += Vec4(v137, v137, v139, v139)

        '''
        Correct code:
        Python won't let us edit this transform, we'll have to copy it all

        if self.m_top_node:
            self.m_top_node.setTransform(TransformState.makeMat(top_mat))

        if self.m_middle_node:
            self.m_middle_node.setTransform(TransformState.makeMat(middle_mat))

        subgraph_copy = self.m_copy_node.copySubgraph()
        chat_node.addChild(subgraph_copy)
        subgraph_copy.setTransform(TransformState.makeMat(subgraph_copy_mat))
        '''

        # BEGIN PYTHON CODE
        subgraph_copy = self.m_copy_node.copySubgraph()
        NodePath.anyPath(subgraph_copy).find('**/top').node().setTransform(TransformState.makeMat(top_mat))
        NodePath.anyPath(subgraph_copy).find('**/middle').node().setTransform(TransformState.makeMat(middle_mat))

        chat_node.addChild(subgraph_copy)
        subgraph_copy.setTransform(TransformState.makeMat(subgraph_copy_mat))
        # END PYTHON CODE

        if has_draw_order:
            bin = config.GetString('nametag-fixed-bin', 'fixed')
            subgraph_copy.setAttrib(CullBinAttrib.make(bin, draw_order))

        subgraph_copy.setAttrib(ColorAttrib.makeFlat(balloon_color))
        if balloon_color[3] != 1.0:
            subgraph_copy.setAttrib(TransparencyAttrib.make(1))

        reducer = SceneGraphReducer()
        reducer.applyAttribs(subgraph_copy)
        reducer.flatten(chat_node, -1)

        generated_text = text_node.generate()
        if for_3d:
            v86 = ChatBalloon.find_middle_geom(chat_node)
            if not v86:
                v86 = ChatBalloon.find_geom_node(chat_node)

            v86.setEffect(DecalEffect.make())

        else:
            v86 = chat_node
            if has_draw_order:
                bin = config.GetString('nametag-fixed-bin', 'fixed')
                generated_text.setAttrib(CullBinAttrib.make(bin, draw_order + 1))

        np = NodePath.anyPath(v86)
        v144 = np.attachNewNode(generated_text)
        v144.setPos((v137, v138, v139))
        v144.setColor(text_color)
        v144.setY(-0.01)  # Panda3D 1.10 hack to prevent z-fighting.
        if text_color[3] != 1.0:
            v144.setTransparency(1)

        if page_button:
            v116 = ModelNode('button')
            new_button[0] = np.attachNewNode(v116)
            button_copy = page_button.copyTo(new_button[0])
            if reversed:
                button_copy.setPos(self.m_hscale * 1.7, 0, 1.8)

            else:
                button_copy.setPos(self.m_hscale * 9.0, 0, 1.8)

            button_copy.setScale(8.0, 8.0, 8.0)
            button_copy.setY(-0.01)  # Panda3D 1.10 hack to prevent z-fighting.

        reducer = SceneGraphReducer()
        reducer.applyAttribs(generated_text)
        reducer.flatten(chat_node, 1)

        return chat_node
