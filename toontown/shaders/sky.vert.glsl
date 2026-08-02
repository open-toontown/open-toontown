// Procedural sky sphere vertex shader.
//
// The sky is rendered on a large sphere (~950 unit radius) that follows the
// camera.  Because the sphere is centred at the camera in model space, every
// vertex position is already a world-space ray direction.  The fragment shader
// uses that direction to compute atmospheric scattering colour and clouds.
//
// Panda3D coordinate convention:  Y = forward,  Z = up,  X = right.
#version 130

in vec4 p3d_Vertex;
uniform mat4 p3d_ModelViewProjectionMatrix;

out vec3 vDir;      // unnormalised model-space direction (normalised in frag)
out vec2 vUV;       // model-space polar UV for cloud tiling

void main() {
    gl_Position = (p3d_ModelViewProjectionMatrix * p3d_Vertex).xyww;
    // xyww trick forces depth to 1.0 (far clip) in NDC so sky is always behind
    // geometry — no depth write needed, but this makes the depth test pass even
    // without disabling depth write on the NodePath.

    vDir = p3d_Vertex.xyz;

    // Spherical UV: longitude (azimuth) on X, latitude (elevation) on Y.
    // Used for cloud layer texture-coordinate calculation in the fragment shader.
    float len   = length(p3d_Vertex.xyz);
    vec3  d     = p3d_Vertex.xyz / max(len, 0.001);
    float phi   = atan(d.x, d.y);          // azimuth [-π, π]
    float theta = asin(clamp(d.z, -1.0, 1.0));  // elevation [-π/2, π/2]
    vUV = vec2(phi / 6.28318530 + 0.5, theta / 3.14159265 + 0.5);
}
