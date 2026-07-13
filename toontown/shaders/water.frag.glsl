// Water surface fragment shader.
//
// Technique overview
// ──────────────────
// 1. Two-layer procedural gradient noise builds a per-pixel wave normal.
//    No texture atlas required – the entire effect is analytic.
// 2. Fresnel equation (Schlick approximation) blends between:
//      • deep-water refraction colour (zone-specific waterColor tint)
//      • planar reflection texture sampled with distortion
// 3. Phong specular on top gives the sun-glint / sparkle.
// 4. A subtle edge-foam brightening is derived from world-space position
//    (no depth buffer needed – approximated by a modulated wave term).
// 5. Alpha is 0.88 so the reflection isn't opaque and water stays readable
//    even without depth sorting.
//
// Uniforms set by OutdoorLighting._setupWaterNode / _tickWaterUniforms:
//   osl_ReflectionTex      – planar reflection render-to-texture
//   osl_WaterColor         – (r,g,b,a) zone water tint / refraction base
//   osl_SunColor           – key light colour for specular
//   osl_SunDir             – normalised direction *toward* the sun (world space)
//   osl_CameraPos          – camera world position (for Fresnel / specular)
//   osl_Time               – seconds (animation)
//   osl_WaveScale          – UV tiling scale matching the vertex stage
//   osl_WaveSpeed          – animation speed multiplier
//   osl_FresnelPower       – Fresnel exponent (3–5 is physically plausible)
//   osl_Roughness          – wave normal perturbation strength (0.2–0.6)
//   osl_ReflectionStrength – master reflection blend weight (0.0–1.0)
#version 130

uniform sampler2D osl_ReflectionTex;
uniform vec4      osl_WaterColor;
uniform vec4      osl_SunColor;
uniform vec3      osl_SunDir;
uniform vec3      osl_CameraPos;
uniform float     osl_Time;
uniform float     osl_WaveScale;
uniform float     osl_WaveSpeed;
uniform float     osl_FresnelPower;
uniform float     osl_Roughness;
uniform float     osl_ReflectionStrength;

in vec2 vTexCoord;
in vec3 vWorldPos;
in vec3 vWorldNormal;
in vec4 vClipPos;
out vec4 fragColor;

// ── Gradient noise ───────────────────────────────────────────────────────────
// Returns a value in [-1, 1] using smooth gradient noise (Perlin-like).

vec2 _hash2(vec2 p) {
    p = vec2(dot(p, vec2(127.1, 311.7)),
             dot(p, vec2(269.5, 183.3)));
    return -1.0 + 2.0 * fract(sin(p) * 43758.5453);
}

float _noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);  // Hermite smooth step
    return mix(
        mix(dot(_hash2(i),              f),
            dot(_hash2(i + vec2(1,0)),  f - vec2(1,0)), u.x),
        mix(dot(_hash2(i + vec2(0,1)),  f - vec2(0,1)),
            dot(_hash2(i + vec2(1,1)),  f - vec2(1,1)), u.x),
        u.y
    ) * 0.5 + 0.5;   // remap to [0,1]
}

// ── Procedural wave normal ───────────────────────────────────────────────────
// Samples noise at two UV layers, computes gradients, and returns a
// perturbed surface normal in world space.
vec3 _waveNormal(vec2 baseUV, float t) {
    float scale = osl_WaveScale;
    float spd   = osl_WaveSpeed;
    float rough = osl_Roughness;

    vec2 uv1 = baseUV * scale        + vec2(t * spd * 0.024, t * spd * 0.016);
    vec2 uv2 = baseUV * scale * 0.65 - vec2(t * spd * 0.019, t * spd * 0.028);

    const float eps = 0.025;

    // First wave layer gradient
    float h00 = _noise(uv1);
    float hdx = _noise(uv1 + vec2(eps, 0.0));
    float hdy = _noise(uv1 + vec2(0.0, eps));

    // Second wave layer gradient
    float h00b = _noise(uv2);
    float hdxb = _noise(uv2 + vec2(eps, 0.0));
    float hdyb = _noise(uv2 + vec2(0.0, eps));

    // Combined gradient (normalised by eps)
    vec2 grad = vec2(
        ((hdx - h00) + (hdxb - h00b)),
        ((hdy - h00) + (hdyb - h00b))
    ) * (rough / eps);

    // Blend gradient with the geometry's up-normal
    // We assume the water surface is approximately horizontal so vWorldNormal ≈ (0,0,1).
    // The gradient perturbs the XZ plane (in Panda3D Y-up convention that is XY).
    vec3 perturbed = normalize(vWorldNormal + vec3(-grad.x, -grad.y, 0.0));
    return perturbed;
}

void main() {
    float t = osl_Time;

    // ── Wave-perturbed normal ────────────────────────────────────────────
    vec3 N = _waveNormal(vTexCoord, t);

    // ── View direction ───────────────────────────────────────────────────
    vec3 V = normalize(osl_CameraPos - vWorldPos);

    // ── Fresnel (Schlick approximation) ──────────────────────────────────
    // F0 for water-air interface ≈ 0.02
    float NdotV  = max(0.0, dot(N, V));
    float f0     = 0.020;
    float fresnel = f0 + (1.0 - f0) * pow(1.0 - NdotV, osl_FresnelPower);
    fresnel       = clamp(fresnel, 0.0, 1.0);

    // ── Planar reflection lookup (distorted by wave normal) ──────────────
    vec2 screenUV = (vClipPos.xy / vClipPos.w) * 0.5 + 0.5;
    // Distort reflection UV by the wave normal's XY deviation.
    vec2 distort  = (N.xy - vWorldNormal.xy) * 0.055;
    vec2 reflUV   = vec2(screenUV.x + distort.x,
                         1.0 - screenUV.y + distort.y);
    reflUV        = clamp(reflUV, 0.001, 0.999);
    vec4 reflColor = texture(osl_ReflectionTex, reflUV);

    // ── Deep-water / refraction colour ───────────────────────────────────
    // Modulate water base colour with a subtle depth-derived darkening.
    // We approximate depth by projecting the fragment onto the vertical axis.
    float depthFade = clamp(1.0 - abs(N.z - 0.9) * 6.0, 0.0, 1.0);
    vec4 waterBase  = osl_WaterColor * (0.80 + 0.20 * depthFade);

    // ── Blend refraction and reflection ──────────────────────────────────
    vec4 surface = mix(waterBase, reflColor, fresnel * osl_ReflectionStrength);

    // ── Sun specular (Blinn-Phong glint) ─────────────────────────────────
    // osl_SunDir points FROM the scene TOWARD the sun.
    vec3  sunToward = normalize(osl_SunDir);
    vec3  H         = normalize(V + sunToward);
    float NdotH     = max(0.0, dot(N, H));
    // High shininess (128) = tight glint; spread by roughness.
    float shininess = mix(256.0, 32.0, osl_Roughness);
    float spec      = pow(NdotH, shininess);
    // Attenuate specular when sun is below the wave horizon.
    float NdotL     = max(0.0, dot(N, sunToward));
    spec           *= NdotL;
    vec3 specColor  = osl_SunColor.rgb * spec * 0.55;

    // ── Edge foam (approximated by wave crest detection) ──────────────────
    // High wave crests (large upward normal component) get a slight white tinge.
    float crestFactor = smoothstep(0.80, 1.0, N.z);
    vec3  foamColor   = vec3(0.92, 0.96, 1.0);
    surface.rgb       = mix(surface.rgb, foamColor, crestFactor * 0.18);

    // ── Final composition ────────────────────────────────────────────────
    vec3 finalRGB = surface.rgb + specColor;

    // Soft alpha: more transparent near horizonal viewing angles (grazing).
    float alpha = mix(0.72, 0.92, fresnel);

    fragColor = vec4(finalRGB, alpha);
}
