// Fullscreen pass-through vertex shader used for god-ray and atmospheric
// overlay effects rendered on a fullscreen CardMaker quad in render2dp.
#version 130

in vec4 p3d_Vertex;
in vec2 p3d_MultiTexCoord0;
out vec2 uv;

void main() {
    gl_Position = p3d_Vertex;
    uv = p3d_MultiTexCoord0;
}
