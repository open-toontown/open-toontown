// Water surface vertex shader.
// Passes world-space position, surface normal, texture coords and clip-space
// position to the fragment stage.  Gentle vertex-displacement is applied to
// break up the perfectly flat water surface and sell the wave motion.
//
// Uniforms (set by OutdoorLighting._setupWaterNode):
//   osl_Time      – seconds since scene start (drives wave animation)
//   osl_WaveScale – UV tiling scale for procedural waves
//   osl_WaveSpeed – wave animation speed multiplier
#version 130

uniform mat4  p3d_ModelViewProjectionMatrix;
uniform mat4  p3d_ModelMatrix;
uniform float osl_Time;
uniform float osl_WaveScale;
uniform float osl_WaveSpeed;

in vec4 p3d_Vertex;
in vec3 p3d_Normal;
in vec2 p3d_MultiTexCoord0;

out vec2 vTexCoord;
out vec3 vWorldPos;
out vec3 vWorldNormal;
out vec4 vClipPos;

// Minimal cheap hash for vertex-level displacement (not the same as the
// higher-quality noise used in the fragment stage).
float vhash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

void main() {
    float t    = osl_Time * osl_WaveSpeed;
    float scale = osl_WaveScale;

    // Two-layer vertex displacement along the surface normal.
    // Kept intentionally small (~0.15 u max) so the geometry stays close
    // to the water plane and shadow/reflection cameras are not confused.
    vec2 uv   = p3d_MultiTexCoord0 * scale;
    float d1  = sin(uv.x * 6.28 + t * 1.1) * cos(uv.y * 4.71 + t * 0.9) * 0.08;
    float d2  = sin(uv.x * 3.14 - t * 0.7) * sin(uv.y * 7.85 + t * 1.3) * 0.06;
    float disp = d1 + d2;

    vec4 displaced = p3d_Vertex + vec4(p3d_Normal * disp, 0.0);

    vec4 worldPos4 = p3d_ModelMatrix * displaced;
    vWorldPos      = worldPos4.xyz;
    vWorldNormal   = normalize(mat3(p3d_ModelMatrix) * p3d_Normal);
    vTexCoord      = p3d_MultiTexCoord0;
    vClipPos       = p3d_ModelViewProjectionMatrix * displaced;
    gl_Position    = vClipPos;
}
