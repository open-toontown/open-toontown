// Scene post-processing composite fragment shader.
//
// Single-pass pipeline that reads a FilterManager-captured scene and applies:
//   1. Depth-buffer-occluded screen-space god rays (Kenny Mitchell technique,
//      GPU Gems 3 Ch. 13).  Sky pixels (depth ≈ 1.0) let light through;
//      solid geometry pixels block it, creating real geometry-cast light shafts.
//   2. Approximate single-pass bloom (bright-pass + large kernel box blur
//      at multiple offsets — not physically perfect but fast and convincing).
//   3. ACES filmic tonemapping with per-zone exposure adjustment.
//
// Uniforms set by OutdoorLighting._setupPostProcess():
//   sceneColor      – RGBA scene texture (float16 or RGBA8 offscreen; exposure+ACES below)
//   sceneDepth      – depth texture matching sceneColor dimensions
//   sunScreenPos    – sun position in [0,1] screen UV space
//   rayColor        – god-ray tint (RGBA)
//   rayIntensity    – master ray strength  (0 = off)
//   bloomIntensity  – bloom strength  (0 = off)
//   bloomThreshold  – luminance threshold for bright-pass
//   exposure        – scene exposure scalar (default 1.0)
//   tonemapEnabled  – 0 = bypass tonemap (linear output), 1 = ACES
//   vignetteStrength – 0 = off, 0.25 = subtle, 1 = strong
//   time            – animation seconds (unused here; reserved for shimmer)
//   texelSize       – vec2(1/width, 1/height) for blur offsets
#version 130

uniform sampler2D sceneColor;
uniform sampler2D sceneDepth;
uniform vec2  sunScreenPos;
uniform vec4  rayColor;
uniform float rayIntensity;
// Bloom is temporarily disabled in code to avoid a Panda3D shader input
// assertion on some drivers; keep the effect path available for later.
uniform float exposure;
uniform float tonemapEnabled;
uniform float vignetteStrength;
uniform float time;
uniform vec2  texelSize;

in vec2 uv;
out vec4 fragColor;

// ── ACES filmic tonemapper ───────────────────────────────────────────────────
// Fitted curve by Krzysztof Narkowicz (2015).  Very close to the full ACES
// reference at a fraction of the cost.
vec3 acesTonemap(vec3 x) {
    const float a = 2.51;
    const float b = 0.03;
    const float c = 2.43;
    const float d = 0.59;
    const float e = 0.14;
    return clamp((x * (a * x + b)) / (x * (c * x + d) + e), 0.0, 1.0);
}

// ── Reinhard (per-channel) ───────────────────────────────────────────────────
vec3 reinhardTonemap(vec3 x) {
    return x / (1.0 + x);
}

// ── Luminance helper ─────────────────────────────────────────────────────────
float luminance(vec3 c) {
    return dot(c, vec3(0.2126, 0.7152, 0.0722));
}

// ── Screen-space depth-occluded god rays ─────────────────────────────────────
//
// Algorithm: march from the current pixel toward the sun position in screen
// space (NUM_SAMPLES steps).  At each step sample the depth buffer.
//   depth == 1.0 (or very close) → sky pixel → sun is visible → accumulate
//   depth < DEPTH_THRESHOLD      → geometry pixel → occluded → skip
//
// The accumulated value is weighted by an exponential decay so samples nearer
// the sun contribute more.  The classic GPU Gems 3 weighting applies.
vec3 godRays(vec2 pixelUV, float intensity) {
    if (intensity <= 0.001) return vec3(0.0);

    const int   NUM_SAMPLES    = 96;
    const float DECAY          = 0.966;
    const float DENSITY        = 0.84;
    const float WEIGHT         = 0.45;
    const float EXPOSURE_RAY   = 0.16;
    const float DEPTH_THRESHOLD = 0.9998; // sky depth threshold

    // Cull when the sun is completely off-screen to avoid aliasing artefacts.
    vec2 sunEdgeDist = min(sunScreenPos, 1.0 - sunScreenPos);
    float edgeFade   = smoothstep(0.0, 0.08, min(sunEdgeDist.x, sunEdgeDist.y));
    if (edgeFade <= 0.0) return vec3(0.0);

    vec2  delta   = (pixelUV - sunScreenPos) * (DENSITY / float(NUM_SAMPLES));
    vec2  sampleUV = pixelUV;
    float illum    = 0.0;
    float decay    = 1.0;

    for (int i = 0; i < NUM_SAMPLES; ++i) {
        sampleUV -= delta;
        // Clamp so we don't sample outside the texture.
        vec2 cUV = clamp(sampleUV, vec2(0.001), vec2(0.999));
        float d   = texture(sceneDepth, cUV).r;
        // Sky pixels (d ≥ DEPTH_THRESHOLD) are unoccluded → contribute.
        float sky = step(DEPTH_THRESHOLD, d);
        illum    += sky * decay * WEIGHT;
        decay    *= DECAY;
    }
    illum *= EXPOSURE_RAY * intensity * edgeFade;

    return rayColor.rgb * illum;
}

// ── Single-pass approximate bloom ───────────────────────────────────────────
//
// Extracts bright pixels then blurs with a two-ring sample pattern (Poisson
// disc approximation).  Not as smooth as multi-pass Gaussian but avoids the
// need for ping-pong buffers, keeping us in one FilterManager pass.
vec3 bloom(vec2 pixUV, float threshold, float intensity) {
    if (intensity <= 0.001) return vec3(0.0);

    vec3 acc = vec3(0.0);
    float total = 0.0;

    // Two rings: inner (4 samples) + outer (8 samples)
    // Offsets are in texel units; scale drives blur radius.
    float blurRadius = mix(3.0, 9.0, intensity);

    vec2 offsets[12];
    // Inner ring
    offsets[0]  = vec2( 1.0,  0.0);
    offsets[1]  = vec2(-1.0,  0.0);
    offsets[2]  = vec2( 0.0,  1.0);
    offsets[3]  = vec2( 0.0, -1.0);
    // Mid ring
    offsets[4]  = vec2( 1.5,  1.5);
    offsets[5]  = vec2(-1.5,  1.5);
    offsets[6]  = vec2( 1.5, -1.5);
    offsets[7]  = vec2(-1.5, -1.5);
    // Outer ring
    offsets[8]  = vec2( 3.0,  0.0);
    offsets[9]  = vec2(-3.0,  0.0);
    offsets[10] = vec2( 0.0,  3.0);
    offsets[11] = vec2( 0.0, -3.0);

    float weights[12];
    weights[0]  = 1.00; weights[1]  = 1.00;
    weights[2]  = 1.00; weights[3]  = 1.00;
    weights[4]  = 0.70; weights[5]  = 0.70;
    weights[6]  = 0.70; weights[7]  = 0.70;
    weights[8]  = 0.35; weights[9]  = 0.35;
    weights[10] = 0.35; weights[11] = 0.35;

    for (int i = 0; i < 12; ++i) {
        vec2  sUV   = pixUV + offsets[i] * texelSize * blurRadius;
        vec3  col   = texture(sceneColor, sUV).rgb;
        float lum   = luminance(col);
        float bright = max(0.0, lum - threshold);
        acc   += col * bright * weights[i];
        total += weights[i];
    }
    if (total > 0.0) acc /= total;

    return acc * intensity * 1.4;
}

// ── Vignette ────────────────────────────────────────────────────────────────
float vignette(vec2 u, float strength) {
    vec2 d = u - 0.5;
    return 1.0 - dot(d, d) * strength * 3.2;
}

// ── Main ─────────────────────────────────────────────────────────────────────
void main() {
    vec4  sceneRGBA = texture(sceneColor, uv);
    vec3  col       = sceneRGBA.rgb * exposure;

    // ── God rays ─────────────────────────────────────────────────────────────
    col += godRays(uv, rayIntensity);

    // ── Bloom ────────────────────────────────────────────────────────────────
    // Disabled for now (see note above).
    col += bloom(uv, 1.0, 0.0);

    // ── Tonemapping ──────────────────────────────────────────────────────────
    if (tonemapEnabled > 0.5) {
        col = acesTonemap(col);
    } else {
        col = clamp(col, 0.0, 1.0);
    }

    // ── Vignette ─────────────────────────────────────────────────────────────
    if (vignetteStrength > 0.001) {
        col *= clamp(vignette(uv, vignetteStrength), 0.0, 1.0);
    }

    fragColor = vec4(col, sceneRGBA.a);
}
