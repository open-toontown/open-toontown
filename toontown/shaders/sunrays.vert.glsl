#version 120

// Simple sunrays vertex shader
// Renders full-screen quad for sun shaft effect

attribute vec4 p3d_Vertex;
attribute vec2 p3d_MultiTexCoord0;

varying vec2 texcoord;

void main() {
    gl_Position = p3d_Vertex;
    texcoord = p3d_MultiTexCoord0;
}