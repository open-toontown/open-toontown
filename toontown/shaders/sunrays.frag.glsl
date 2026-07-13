// Procedural radial god-ray / sun-shaft overlay.
//
// Renders additive volumetric light streaks radiating from a sun or moon
// position in screen-space UV.  Designed for Panda3D additive blending on a
// fullscreen CardMaker quad in render2dp.
//
// Uniforms (set by OutdoorLighting._createGodRaysOverlay / _applyProfileLive):
//   sunPos       – sun/moon position in [0,1] screen UV space
//   rayColor     – base tint colour of the rays (RGBA)
//   rayIntensity – master scale (0..1+, boosted during golden hour / sunset)
//   aspectRatio  – window width / height (keeps rays radially symmetric)
//   time         – seconds since scene start (drives subtle shimmer)
#version 130

uniform vec2  sunPos;
uniform vec4  rayColor;
uniform float rayIntensity;
uniform float aspectRatio;
uniform float time;

in vec2 uv;
out vec4 fragColor;

// ── Fast hash functions (no trig) ────────────────────────────────────────────
float hash11(float p) {
    p = fract(p * 0.1031);
    p *= p + 33.33;
    p *= p + p;
    return fract(p);
}
float hash12(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

void main() {
    // Aspect-correct delta from sun position.
    vec2  aspect  = vec2(aspectRatio, 1.0);
    vec2  delta   = (uv - sunPos) * aspect;
    float dist    = length(delta);
    float angle   = atan(delta.y, delta.x);

    // ── Radial streaks ───────────────────────────────────────────────────
    // 20 streaks with per-streak random angular width, stretch and shimmer.
    const int NUM_STREAKS = 20;
    float streaks = 0.0;
    for (int i = 0; i < NUM_STREAKS; i++) {
        float fi = float(i);

        float streakAngle  = fi / float(NUM_STREAKS) * 6.28318530;
        float baseWidth    = 0.010 + hash11(fi * 3.71) * 0.024;
        float stretch      = 2.2  + hash11(fi * 7.43) * 5.0;

        // Each streak breathes independently at a different frequency.
        float shimmer      = 1.0 + 0.07 * sin(time * (1.0 + hash11(fi) * 2.4) + fi * 1.3);
        float angularWidth = baseWidth * shimmer;

        // Wrap angular difference to [-π, π].
        float diff = angle - streakAngle;
        diff = diff - 6.28318530 * floor((diff + 3.14159265) / 6.28318530);

        float gaussian = exp(-(diff * diff) / (2.0 * angularWidth * angularWidth));
        float lenFade  = exp(-dist * stretch);

        streaks += gaussian * lenFade;
    }

    // ── Diffuse halo + tight corona ──────────────────────────────────────
    float halo   = exp(-dist *  8.5) * 0.70;
    float corona = pow(max(0.0, 1.0 - dist * 4.2), 3.8) * 0.40;

    float total = streaks + halo + corona;

    // ── Feathering ───────────────────────────────────────────────────────
    // Suppress artefacts immediately around the source and at screen edges.
    float nearFade = smoothstep(0.0, 0.05, dist);

    vec2  edgeDist = min(sunPos, 1.0 - sunPos);
    float edgeFade = smoothstep(0.0, 0.10, min(edgeDist.x, edgeDist.y));

    total *= nearFade * edgeFade * rayIntensity;

    // ── Subtle chromatic fringe ──────────────────────────────────────────
    // The RGB channels are sampled at slightly offset radii, producing a
    // thin prismatic ring around the corona.  It adds cinematic atmosphere
    // without being garish.  The effect is strongest near the source and
    // fades with distance.
    float fringeMask = exp(-dist * 12.0) * 0.18;
    float rOffset    =  0.004 * aspectRatio;
    float bOffset    = -0.004 * aspectRatio;
    vec2  rDir       = normalize(delta + vec2(0.001)) * rOffset;
    vec2  bDir       = normalize(delta + vec2(0.001)) * bOffset;

    // Re-evaluate total at offset positions for R and B channels.
    vec2  deltaR     = (uv + rDir - sunPos) * aspect;
    float distR      = length(deltaR);
    float coronaR    = pow(max(0.0, 1.0 - distR * 4.2), 3.8) * 0.40;
    float haloR      = exp(-distR * 8.5) * 0.70;

    vec2  deltaB     = (uv + bDir - sunPos) * aspect;
    float distB      = length(deltaB);
    float coronaB    = pow(max(0.0, 1.0 - distB * 4.2), 3.8) * 0.40;
    float haloB      = exp(-distB * 8.5) * 0.70;

    float fringeR = (coronaR + haloR) * nearFade * edgeFade * rayIntensity;
    float fringeB = (coronaB + haloB) * nearFade * edgeFade * rayIntensity;

    // Blend chromatic fringe into main signal.
    vec3 colour;
    colour.r = rayColor.r * mix(total, fringeR, fringeMask);
    colour.g = rayColor.g * total;
    colour.b = rayColor.b * mix(total, fringeB, fringeMask);

    // Premultiplied alpha for the additive blend mode.
    float alpha = (colour.r + colour.g + colour.b) / 3.0 * rayColor.a;

    fragColor = vec4(colour, alpha);
}
