#version 120

// Sun rays / god rays fragment shader
// Creates volumetric light scattering effect

uniform vec2 sunPos;
uniform vec4 rayColor;
uniform float rayIntensity;
uniform float time;
uniform float aspectRatio;

varying vec2 texcoord;

float hash(float n) {
    return fract(sin(n) * 43758.5453);
}

float noise(vec2 x) {
    vec2 p = floor(x);
    vec2 f = fract(x);
    f = f * f * (3.0 - 2.0 * f);
    float n = p.x + p.y * 57.0;
    return mix(mix(hash(n + 0.0), hash(n + 1.0), f.x),
               mix(hash(n + 57.0), hash(n + 58.0), f.x), f.y);
}

float fbm(vec2 p) {
    float f = 0.0;
    f += 0.5000 * noise(p); p *= 2.02;
    f += 0.2500 * noise(p); p *= 2.03;
    f += 0.1250 * noise(p); p *= 2.01;
    f += 0.0625 * noise(p);
    return f / 0.9375;
}

void main() {
    vec2 uv = texcoord;
    
    // Adjust for aspect ratio
    uv.x *= aspectRatio;
    vec2 lightPos = sunPos;
    lightPos.x *= aspectRatio;
    
    // Vector from pixel to light source in screen space
    vec2 delta = lightPos - uv;
    float dist = length(delta);
    
    // IMPORTANT:
    // This overlay is rendered on render2dp and does not necessarily have a
    // scene texture bound to p3d_Texture0. Sampling an unbound texture can
    // read undefined GPU memory (often seen as RGB flicker).
    //
    // Instead, generate a stable radial scattering term without sampling.
    float falloff = clamp(1.0 - dist, 0.0, 1.0);
    falloff = pow(falloff, 2.2);
    float shaft = falloff * (0.35 + 0.65 * falloff);

    // Add subtle noise for atmospheric effect (animated very slowly).
    float n = fbm(uv * 3.0 + time * 0.05) * 0.05;
    shaft = clamp(shaft + n, 0.0, 1.0);

    vec4 finalColor = vec4(rayColor.rgb * shaft, clamp(rayIntensity * shaft, 0.0, 1.0));
    
    gl_FragColor = finalColor;
}