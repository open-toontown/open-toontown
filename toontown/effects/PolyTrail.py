from pandac.PandaModules import *
from direct.motiontrail.MotionTrail import *
import random

class PolyTrail(NodePath):

    def __init__(self, root_node_path = None, vertex_list = None, color_list = None, time_window = 0.25):
        NodePath.__init__(self, 'PolyTrail')
        self.time_window = time_window
        self.root_node_path = root_node_path
        if not self.root_node_path:
            self.root_node_path = render
        self.vertex_list = vertex_list
        if not self.vertex_list:
            self.vertex_list = [Vec4(0.0, 0.4, 0.0, 1.0), Vec4(0.0, 2.0, 0.0, 1.0)]
        self.color_list = color_list
        if not self.color_list:
            self.color_list = []
            for i in self.vertex_list:
                self.color_list.append(Vec4(0.1, 0.2, 0.4, 1.0))

        self.motion_trail = None
        self.motion_trail_vertex = None
        self.addMotionTrail()
        self.setVertexColors(self.color_list)
        self.setTimeWindow(self.time_window)
        self.motion_trail.attach_motion_trail()
        return

    def destroy(self):
        self.removeMotionTrail()
        self.removeNode()
        self.root_node_path = None
        self.motion_trail = None
        self.vertex_list = None
        self.motion_trail_vertex = None
        return

    def beginTrail(self):
        if self.motion_trail:
            self.motion_trail.begin_motion_trail()

    def endTrail(self):
        if self.motion_trail:
            self.motion_trail.end_motion_trail()
            self.motion_trail.time_window = self.time_window

    def removeMotionTrail(self):
        self.endTrail()
        if self.motion_trail:
            self.motion_trail.unregister_motion_trail()
            self.motion_trail.delete()
            self.motion_trail = None
        if self.motion_trail_vertex:
            self.motion_trail_vertex = None
        return

    def addMotionTrail(self):
        if not self.motion_trail:
            self.motion_trail = MotionTrail('motion_trail', self)
            self.motion_trail.root_node_path = self.root_node_path
            if False:
                axis = loader.loadModel('models/misc/xyzAxis')
                axis.reparentTo(self)

            def test_vertex_function(motion_trail_vertex, vertex_id, context):
                return self.vertex_list[vertex_id]

            index = 0
            total_test_vertices = len(self.vertex_list)
            while index < total_test_vertices:
                self.motion_trail_vertex = self.motion_trail.add_vertex(index, test_vertex_function, None)
                if True:
                    if index == 0:
                        self.motion_trail_vertex.start_color = Vec4(0.0, 0.25, 0.0, 1.0)
                        self.motion_trail_vertex.end_color = Vec4(0.0, 0.0, 0.0, 1.0)
                    if index == 1:
                        self.motion_trail_vertex.start_color = Vec4(0.25, 0.0, 0.0, 1.0)
                        self.motion_trail_vertex.end_color = Vec4(0.0, 0.0, 0.0, 1.0)
                    if index == 2:
                        self.motion_trail_vertex.start_color = Vec4(0.0, 0.0, 1.0, 1.0)
                        self.motion_trail_vertex.end_color = Vec4(0.0, 0.0, 0.0, 1.0)
                    if index == 3:
                        self.motion_trail_vertex.start_color = Vec4(0.0, 1.0, 1.0, 1.0)
                        self.motion_trail_vertex.end_color = Vec4(0.0, 0.0, 0.0, 1.0)
                    if index == 4:
                        self.motion_trail_vertex.start_color = Vec4(1.0, 1.0, 0.0, 1.0)
                        self.motion_trail_vertex.end_color = Vec4(0.0, 0.0, 0.0, 1.0)
                index += 1

            self.motion_trail.update_vertices()
            self.motion_trail.calculate_relative_matrix = True
            self.motion_trail.time_window = self.time_window
            self.motion_trail.continuous_motion_trail = False
            self.motion_trail.end_motion_trail()
            self.motion_trail.register_motion_trail()
            if False:
                axis = Vec3(0.0, 0.0, 1.0)
                time = 0.0
                angle = (1.0 - time) * 90.0
                matrix = Mat4.rotateMat(angle, axis)
                self.motion_trail.update_motion_trail(time, matrix)
                time = 0.2
                angle = (1.0 - time) * 90.0
                matrix = Mat4.rotateMat(angle, axis)
                self.motion_trail.update_motion_trail(time, matrix)
                time = 0.4
                angle = (1.0 - time) * 90.0
                matrix = Mat4.rotateMat(angle, axis)
                self.motion_trail.update_motion_trail(time, matrix)
                time = 0.6
                angle = (1.0 - time) * 90.0
                matrix = Mat4.rotateMat(angle, axis)
                self.motion_trail.update_motion_trail(time, matrix)
                time = 0.8
                angle = (1.0 - time) * 90.0
                matrix = Mat4.rotateMat(angle, axis)
                self.motion_trail.update_motion_trail(time, matrix)
                time = 1.0
                angle = (1.0 - time) * 90.0
                matrix = Mat4.rotateMat(angle, axis)
                self.motion_trail.update_motion_trail(time, matrix)
        return

    def setVertexColors(self, color_list):
        if self.motion_trail:
            black = Vec4(0.0, 0.0, 0.0, 1.0)
            scale_array = [0.25,
             0.4,
             0.7,
             1.0]
            total_scales = len(scale_array)
            for index in range(len(color_list)):
                color = color_list[index]
                if index < total_scales:
                    scale = scale_array[index] * 0.75
                else:
                    scale = 1.0
                scaled_color = Vec4(color[0] * scale, color[1] * scale, color[2] * scale, 1.0)
                self.motion_trail.set_vertex_color(index, scaled_color, black)

    def setUnmodifiedVertexColors(self, color_list):
        if self.motion_trail:
            for index in range(len(color_list)):
                color = color_list[index]
                self.motion_trail.set_vertex_color(index, color, color)

    def setTimeWindow(self, time_window):
        if self.motion_trail:
            self.motion_trail.time_window = time_window

    def setUseNurbs(self, val):
        self.motion_trail.use_nurbs = val

    def setTexture(self, texture):
        if self.motion_trail:
            self.motion_trail.set_texture(texture)

    def setBlendModeOn(self):
        if self.motion_trail:
            self.motion_trail.geom_node_path.node().setAttrib(ColorBlendAttrib.make(ColorBlendAttrib.MAdd, ColorBlendAttrib.OIncomingAlpha, ColorBlendAttrib.OOne))

    def setBlendModeOff(self):
        if self.motion_trail:
            self.motion_trail.geom_node_path.node().setAttrib(ColorBlendAttrib.make(ColorBlendAttrib.MNone))
