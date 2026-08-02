#version 120

// Water vertex shader with wave animation

attribute vec4 p3d_Vertex;
attribute vec3 p3d_Normal;
attribute vec2 p3d_MultiTexCoord0;

uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelMatrix;
uniform mat3 p3d_NormalMatrix;

uniform float time;
uniform float waveHeight;
uniform float waveSpeed;
uniform vec4 waterColor;
uniform sampler2D reflectionTex;

varying vec3 normal;
varying vec3 worldPos;
varying vec2 texcoord;
varying vec4 reflectionColor;
varying float depth;

// Simple sine wave function
float wave(vec2 position, float frequency, float speed) {
    return sin(dot(position, vec2(frequency, frequency * 1.7)) + time * speed);
}

void main() {
    vec4 vertex = p3d_Vertex;
    
    // Generate wave displacement
    vec2 pos = vertex.xz;
    float height = 0.0;
    
    // Multiple octaves for realistic waves
    height += wave(pos, 0.1, waveSpeed) * 0.5;
    height += wave(pos, 0.2, waveSpeed * 1.3) * 0.25;
    height += wave(pos, 0.4, waveSpeed * 1.7) * 0.125;
    height += wave(pos, 0.8, waveSpeed * 2.1) * 0.0625;
    
    // Apply wave height
    vertex.y += height * waveHeight;
    
    // Calculate normals from wave function derivatives
    vec3 waveNormal = vec3(
        -waveHeight * 0.1 * cos(dot(pos, vec2(0.1, 0.17)) + time * waveSpeed),
        1.0,
        -waveHeight * 0.1 * cos(dot(pos, vec2(0.17, 0.1)) + time * waveSpeed * 1.3)
    );
    waveNormal = normalize(waveNormal);
    
    // Transform vertex
    gl_Position = p3d_ModelViewProjectionMatrix * vertex;
    
    // Pass data to fragment shader
    normal = normalize(p3d_NormalMatrix * waveNormal);
    worldPos = (p3d_ModelMatrix * vertex).xyz;
    texcoord = p3d_MultiTexCoord0;
    
    // Simple depth calculation
    depth = gl_Position.z / gl_Position.w;
}