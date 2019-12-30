from panda3d.core import *


class PopupHandle:
    def __init__(self, popup):
        self.m_popup = popup  # 12
        self.m_cell = -1  # 16
        self.m_wants_visible = False  # 20
        self.m_score = 0  # 24
        self.m_objcode = id(self)  # 28
        popup.setObjectCode(self.m_objcode)


class MarginCell:
    def __init__(self):
        self.m_mat = Mat4()  # 0
        self.m_cell_width = 0  # 64
        self.m_popup = None  # 68
        self.m_np = None  # 72
        self.m_visible = False  # 84
        self.m_objcode = 0  # 88
        self.m_time = 0  # 96


class MarginManager(PandaNode):
    def __init__(self):
        PandaNode.__init__(self, 'popups')

        # self.setCullCallback()
        self.cbNode = CallbackNode(self.getName() + '-cbNode')
        self.cbNode.setCullCallback(PythonCallbackObject(self.cullCallback))
        self.addChild(self.cbNode)

        self.m_cells = []
        self.m_popups = {}  # MarginPopup*: PopupHandle
        self.m_code_map = {}  # code: MarginPopup*
        self.m_num_available = 0

    def addGridCell(self, a2, a3, a4, a5, a6, a7):
        v7 = (a5 - a4) * 0.16666667
        v8 = (a7 - a6) * 0.16666667
        v15 = v7 * a2 + a4
        v9 = a3 * v8 + a6
        v10 = v9 + v8 - 0.01
        v11 = v9 + 0.01
        v12 = v15 + v7 - 0.01
        v13 = v15 + 0.01
        return self.addCell(v13, v12, v11, v10)

    def addCell(self, left, right, bottom, top):
        v5 = (top - bottom) * 0.5
        v19 = Vec3(v5, 0, 0)
        scale = Vec3(v5, v5, v5)
        shear = Vec3(0, 0, 0)
        trans = Vec3((left + right) * 0.5, 0, (bottom + top) * 0.5)

        v18 = len(self.m_cells)
        v9 = MarginCell()
        self.m_cells.append(v9)
        v9.m_available = True

        mat3 = Mat3()
        composeMatrix(mat3, scale, shear, Vec3(0, 0, 0), 0)
        v9.m_mat = Mat4(mat3, trans)

        v9.m_cell_width = (right - left) * 0.5 / v19[0]
        v9.m_np = None
        v9.m_popup = None
        v9.m_objcode = 0
        v9.m_time = 0.0

        self.m_num_available += 1
        return v18

    def setCellAvailable(self, a2, a3):
        v5 = self.m_cells[a2]
        if v5.m_available:
            self.m_num_available -= 1

        v5.m_available = a3
        if v5.m_available:
            self.m_num_available += 1

        if v5.m_np:
            self.hide(a2)
            v5.m_popup = None
            v5.m_objcode = 0

    def getCellAvailable(self, a2):
        return self.m_cells[a2].m_available

    def cullCallback(self, *args):
        self.update()

    def managePopup(self, a2):
        a2.setManaged(True)
        self.m_popups[a2] = PopupHandle(a2)
        self.m_code_map[a2.getObjectCode()] = a2

    def unmanagePopup(self, a2):
        v9 = self.m_popups.get(a2)
        if v9:
            if v9.m_cell >= 0:
                self.hide(v9.m_cell)
                v9.m_cell = -1

            a2.setManaged(False)
            del self.m_popups[a2]
            del self.m_code_map[v9.m_objcode]

    def hide(self, a2):
        cell = self.m_cells[a2]
        cell.m_np.removeNode()
        cell.m_time = globalClock.getFrameTime()
        if cell.m_popup:
            cell.m_popup.setVisible(False)

    def show(self, popup, cell_index):
        v12 = self.m_cells[cell_index]
        v12.m_popup = popup
        v12.m_objcode = popup.getObjectCode()
        v12.m_np = NodePath.anyPath(self).attachNewNode(popup)
        v12.m_np.setMat(v12.m_mat)
        self.m_popups[popup].m_cell = cell_index
        popup.m_cell_width = v12.m_cell_width
        popup.setVisible(True)

    def chooseCell(self, a2, a3):
        now = globalClock.getFrameTime()
        objcode = a2.getObjectCode()

        for cell in a3:
            v7 = self.m_cells[cell]
            if (v7.m_popup == a2 or v7.m_objcode == objcode) and (now - v7.m_time) <= 30.0:
                result = cell
                break

        else:
            for cell in a3[::-1][1:]:  # Iterate backwards, skip last item
                v10 = self.m_cells[cell]
                if (not v10.m_popup) or (now - v10.m_time) > 30.0:
                    result = cell
                    break

            else:
                result = a3[-1]

        a3.remove(result)
        return result

    def showVisibleNoConflict(self):
        cells = []
        for i, cell in enumerate(self.m_cells):
            if cell.m_available and not cell.m_np:
                cells.append(i)

        for handle in list(self.m_popups.values()):
            v7 = handle.m_popup
            if handle.m_wants_visible and not v7.isVisible():
                v8 = self.chooseCell(v7, cells)
                self.show(v7, v8)

    def showVisibleResolveConflict(self):
        v4 = []

        for handle in list(self.m_popups.values()):
            score = 0
            if handle.m_wants_visible:
                score = handle.m_score

            v4.append((handle, -score))

        v4 = sorted(v4, key=lambda a: a[-1])
        for handle in v4[self.m_num_available:]:
            if handle[0].m_popup.isVisible():
                self.hide(handle[0].m_cell)
                handle[0].m_cell = -1

        cells = []
        for i, cell in enumerate(self.m_cells):
            if cell.m_available and not cell.m_np:
                cells.append(i)

        for handle in v4[:self.m_num_available]:
            v7 = handle[0].m_popup
            if handle[0].m_wants_visible and not v7.isVisible():
                v8 = self.chooseCell(v7, cells)
                self.show(v7, v8)

    def update(self):
        num_want_visible = 0

        for handle in list(self.m_popups.values()):
            popup = handle.m_popup
            handle.m_wants_visible = popup.considerVisible()
            if handle.m_wants_visible and handle.m_objcode:
                handle.m_score = popup.getScore()
                num_want_visible += 1

            elif popup.isVisible():
                self.hide(handle.m_cell)
                handle.m_cell = -1

        if num_want_visible > self.m_num_available:
            self.showVisibleResolveConflict()

        else:
            self.showVisibleNoConflict()

        for popup in list(self.m_popups.keys()):
            popup.frameCallback()
