// Procedural physically-based sky fragment shader – MASSIVE REWRITE
//
// Implements (new and improved):
//   • Rayleigh + Mie scattering – accurate wavelength-dependent blue-sky gradient
//   • Wide sunset/sunrise horizon corona (orange-pink band near horizon)
//   • Ozone absorption – cyan/yellow sky transition near sunset
//   • Horizon haze / atmospheric extinction with turbidity control
//   • VISIBLE SUN DISC with:
//       – Physical angular radius (~0.27°)
//       – Limb darkening (edges slightly darker than centre)
//       – Colour shifts noon→white-yellow, sunset→deep orange-red
//       – Multi-layer exponential corona / aureole
//       – Subtle vertical lens-flare streak
//       – BLINDING GLARE when staring directly into the sun (chromatic aberration glow)
//   • Volumetric-looking FBM cumulus clouds with domain warping:
//       – Two-pass domain warp (organic, non-repetitive shapes)
//       – Multi-layer depth sampling (distinct top/middle/base layers)
//       – Sun back-lighting (silver lining on edges facing sun)
//       – Sunset orange-pink underbelly glow
//       – Moon-lit night-time clouds (cool blue-grey)
//       – Per-zone coverage, speed, sharpness
//   • Twinkling star field:
//       – Per-star unique twinkle frequency & phase
//       – Four spectral classes: blue-white / white / yellow-white / warm
//       – Occasional "sparkle" diffraction cross on bright stars
//       – Fades behind clouds and near the sun
//   • MOON disc with:
//       – Surface noise detail (craters)
//       – Limb darkening
//       – Multi-layer corona glow
//       – Cloud occlusion
//   • Zone colour scale (skyScale) applied to final output
//   • Reinhard tonemapping + gamma lift for natural HDR-to-LDR
//
// Uniforms set by ProceduralSky.update():
//   sunDir           – world-space direction TOWARD the sun (normalised)
//   sunColor         – key light colour; used for Mie glow tint
//   zenithColor      – deep sky colour at zenith                       (zone)
//   horizonColor     – sky colour at horizon                           (zone)
//   fogColor         – atmospheric haze/fog tint                       (zone)
//   cloudCoverage    – 0.0 (clear) … 1.0 (overcast)                   (zone)
//   cloudSpeed       – cloud animation multiplier                      (zone)
//   cloudSharpness   – edge sharpness 0.0 (fluffy) … 1.0 (sharp)      (zone)
//   turbidity        – Mie strength 1.0 (crisp) … 8.0 (hazy)          (zone)
//   starBrightness   – star intensity; 0 in day, up to 1 at night      (zone)
//   moonEnabled      – 1.0 = draw a moon disc
//   moonDir          – world-space direction toward moon
//   moonColor        – moon disc tint
//   time             – animation seconds (drives cloud drift + star twinkle)
//   skyScale         – vec4 colour multiplier (zone tint)
//   sunDiscEnabled   – 1.0 = draw visible sun disc (default 1)
//   sunBlindStrength – 0.0–1.0 blinding glare when staring into sun
//   sunWorldElev     – sun direction Z in *world* space [-1..1] (time-of-day);
//                      separate from sunDir so atmosphere does not swim when the camera tilts
#version 130

// ── Atmosphere uniforms ────────────────────────────────────────────────────
uniform vec3  sunDir;
uniform float sunWorldElev;
uniform vec4  sunColor;
uniform vec3  zenithColor;
uniform vec3  horizonColor;
uniform vec3  fogColor;
// ── Cloud uniforms ─────────────────────────────────────────────────────────
uniform float cloudCoverage;
uniform float cloudSpeed;
uniform float cloudSharpness;
// ── Scattering ────────────────────────────────────────────────────────────
uniform float turbidity;
// ── Night sky ─────────────────────────────────────────────────────────────
uniform float starBrightness;
uniform float moonEnabled;
uniform vec3  moonDir;
uniform vec4  moonColor;
// ── Animation ─────────────────────────────────────────────────────────────
uniform float time;
uniform vec4  skyScale;
// ── New features ──────────────────────────────────────────────────────────
uniform float sunDiscEnabled;    // 1.0 = render sun disc + corona
uniform float sunBlindStrength;  // 0–1 glare when staring at sun

in  vec3 vDir;
in  vec2 vUV;
out vec4 fragColor;

// ─────────────────────────────────────────────────────────────────────────
// Noise / hash utilities
// ─────────────────────────────────────────────────────────────────────────

float _hash(vec2 p) {
    p  = fract(p * vec2(127.1, 311.7));
    p += dot(p, p + 19.19);
    return fract(p.x * p.y);
}

float _vnoise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(
        mix(_hash(i),                _hash(i + vec2(1.0, 0.0)), u.x),
        mix(_hash(i + vec2(0.0, 1.0)), _hash(i + vec2(1.0, 1.0)), u.x),
        u.y
    );
}

// 8-octave FBM with per-octave rotation (breaks axis-aligned repetition)
float _fbm(vec2 p) {
    float v   = 0.0;
    float amp = 0.5;
    mat2  rot = mat2(1.6, 1.2, -1.2, 1.6);
    for (int i = 0; i < 8; ++i) {
        v   += amp * _vnoise(p);
        p    = rot * p * 2.1;
        amp *= 0.46;
    }
    return v;
}

// ─────────────────────────────────────────────────────────────────────────
// Phase functions
// ─────────────────────────────────────────────────────────────────────────

float _mie(float cosA, float g) {
    float g2 = g * g;
    return (1.0 - g2) / pow(max(1.0e-4, 1.0 + g2 - 2.0 * g * cosA), 1.5) * 0.25;
}

float _rayleigh(float cosA) {
    return 0.75 * (1.0 + cosA * cosA);
}

// ─────────────────────────────────────────────────────────────────────────
// Main
// ─────────────────────────────────────────────────────────────────────────

void main() {
    vec3  dir      = normalize(vDir);
    float elev     = dir.z;
    float elevAbs  = abs(elev);
    float cosTheta = dot(dir, sunDir);
    // World-space sun height (stable when camera pitches/yaws); sunDir is camera-space for dots.
    float sunElevW = sunWorldElev;
    // sunPower: 0 when sun is on or below horizon, rises to 1 near zenith
    float sunPower = clamp(sunElevW * 3.5 + 0.28, 0.0, 1.0);

    // ── Rayleigh scattering ──────────────────────────────────────────────
    // Wavelength-dependent (shorter λ = blue scatters more)
    vec3  rayleigh_wl   = vec3(0.26, 0.50, 1.00);
    float rayleighPhase = _rayleigh(cosTheta);
    vec3  rayleighCol   = rayleigh_wl * rayleighPhase * mix(0.28, 1.05, sunPower);

    // ── Mie scattering (turbidity-driven forward halo) ───────────────────
    float g        = max(0.58, 0.84 - turbidity * 0.020);
    float mieStr   = turbidity * 0.13;
    float mieGlow  = _mie(cosTheta, g) * mieStr;
    vec3  mieCol   = sunColor.rgb * mieGlow;

    // ── Wide horizon corona at sunset/sunrise ────────────────────────────
    // Horizontal dot: measures how closely dir aligns with sun's azimuth at horizon
    vec2  sunAz    = vec2(sunDir.x, sunDir.y);
    float sunAzLen = max(0.001, length(sunAz));
    float horizDot = dot(vec2(dir.x, dir.y), sunAz / sunAzLen);
    float horizBand = pow(max(0.0, horizDot), 3.5)
                    * max(0.0, 1.0 - abs(sunElevW) * 3.8)   // only near horizon
                    * (1.0 - abs(elev) * 3.0)               // fade away from horizon line
                    * 0.70;
    vec3  horizGlowCol = mix(
        vec3(1.00, 0.42, 0.06),   // deep orange at low elevation
        vec3(1.00, 0.80, 0.42),   // golden higher up
        clamp(sunPower * 1.5, 0.0, 1.0)
    ) * horizBand;

    // ── Ozone absorption ─────────────────────────────────────────────────
    float ozone     = max(0.0, 1.0 - elevAbs * 1.55);
    vec3  ozoneCol  = vec3(0.00, 0.13, 0.22) * ozone * sunPower;

    // ── Sky gradient (zenith → horizon) ──────────────────────────────────
    float horizonT  = pow(clamp(elev * 1.25 + 0.14, 0.0, 1.0), 0.50);
    vec3  gradCol   = mix(horizonColor, zenithColor, horizonT);

    // Sunset/sunrise band: orange-pink near horizon, purple higher up
    float sunsetBand = max(0.0, 1.0 - abs(sunElevW) * 2.2) * (1.0 - horizonT * 0.75);
    vec3  sunsetTint = mix(
        vec3(1.00, 0.38, 0.05),    // near-horizon orange
        vec3(0.55, 0.25, 0.72),    // purple higher
        horizonT
    ) * sunsetBand * 0.62;
    gradCol += sunsetTint;

    // Assemble base sky
    vec3 sky = gradCol
             + rayleighCol  * 0.42
             + mieCol
             + ozoneCol
             + horizGlowCol;

    // ── Horizon haze (atmospheric extinction) ────────────────────────────
    float hazeT = exp(-max(0.0, elev) * 5.2 * turbidity * 0.27);
    sky = mix(sky, fogColor, hazeT * 0.52);

    // ── Below horizon: fade to dark fog ──────────────────────────────────
    if (elev < 0.0) {
        float below = clamp(-elev * 9.5, 0.0, 1.0);
        sky = mix(sky, fogColor * 0.48, below);
    }

    // ─────────────────────────────────────────────────────────────────────
    // Volumetric clouds
    // ─────────────────────────────────────────────────────────────────────

    float cloudAlpha = 0.0;
    vec3  cloudRGB   = vec3(1.0);

    if (cloudCoverage > 0.02 && elev > -0.07) {
        // Perspective projection onto cloud layer at ~1 km altitude
        float layerScale = 1.0 / max(0.05, elev + 0.05);
        vec2  cloudUV = vec2(dir.x, dir.y) * layerScale * 0.36
                      + vec2(time * cloudSpeed * 0.00115, time * cloudSpeed * 0.00045);

        // ── Domain warping pass 1 (large-scale organic distortion) ───────
        vec2 warp1 = vec2(
            _fbm(cloudUV * 1.55),
            _fbm(cloudUV * 1.55 + vec2(5.20, 1.30))
        ) * 0.32;

        // ── Domain warping pass 2 (medium-scale detail) ──────────────────
        vec2 warp2 = vec2(
            _fbm(cloudUV * 0.82 + vec2(1.70, 9.20)),
            _fbm(cloudUV * 0.82 + vec2(8.30, 2.80))
        ) * 0.14;

        vec2 warpedUV = cloudUV + warp1 + warp2;

        // Primary cloud density field
        float density = _fbm(warpedUV * 2.35);

        // Coverage → threshold
        float threshold = 1.0 - cloudCoverage * 0.76;
        float raw       = density - threshold;
        float edgeWidth = mix(0.32, 0.045, cloudSharpness);
        float shaped    = smoothstep(0.0, edgeWidth, raw);

        // Horizon fade (perspective stretch makes low-angle clouds blur badly)
        shaped *= smoothstep(-0.04, 0.18, elev);

        // ── Multi-layer depth sampling for 3-D cloud body feel ──────────
        float densityMid  = _fbm(warpedUV * 4.00 + vec2(1.70, 3.10));
        float densityFine = _fbm(warpedUV * 8.50 + vec2(-2.30, 0.80));
        // volDepth: 0 = outer edge, 1 = deep interior
        float volDepth = clamp(densityMid * 0.45 + densityFine * 0.18, 0.0, 1.0);

        // ── Cloud illumination ───────────────────────────────────────────
        float sunDot    = max(0.0, dot(dir, sunDir));
        float shadowing = clamp(1.0 - shaped * 0.68, 0.16, 1.0);

        // Top surface: brightly lit by direct sun
        vec3  litTop    = mix(vec3(0.96, 0.97, 1.00), sunColor.rgb * 1.20, 0.20);

        // Cloud base: deeper interior → darker grey-blue shadow
        float depthSh   = mix(0.36, 0.62, volDepth);
        vec3  litBase   = litTop * vec3(depthSh * 0.88, depthSh * 0.93, depthSh * 1.04);

        // Sunset underbelly: orange-pink glow when sun is near horizon
        float sunsetC   = max(0.0, 1.0 - abs(sunElevW) * 4.0) * sunPower;
        vec3  sunsetBelly = mix(
            vec3(1.0, 0.55, 0.22),
            vec3(1.0, 0.78, 0.52),
            clamp(sunDot, 0.0, 1.0)
        ) * sunsetC * 0.75;
        litBase += sunsetBelly;

        // Second FBM sample for vertical shading variation
        float baseShade = _fbm(warpedUV * 2.35 + vec2(0.30, 0.15)) * 0.72 + 0.28;
        cloudRGB = mix(litBase, litTop, baseShade * shadowing);

        // Silver lining: bright backlit halo on sun-facing cloud edges
        float silverEdge = smoothstep(edgeWidth * 0.55, 0.0, raw) * sunDot;
        cloudRGB += vec3(0.72, 0.64, 0.46) * silverEdge * sunPower * 0.70;

        // Night / moon-lit clouds (cool dim blue-grey)
        if (moonEnabled > 0.5 && sunPower < 0.30) {
            float mnFade  = clamp((0.30 - sunPower) * 4.0, 0.0, 1.0);
            float mnDot   = max(0.0, dot(dir, normalize(moonDir)));
            vec3  mnLight = vec3(0.35, 0.42, 0.60) * mnDot * 0.38;
            float nDepth  = mix(0.06, 0.52, shaped);
            cloudRGB = mix(cloudRGB, vec3(0.05, 0.07, 0.14) + mnLight * shaped,
                           mnFade * nDepth);
        }

        cloudAlpha = shaped;
    }

    sky = mix(sky, cloudRGB, cloudAlpha);

    // ─────────────────────────────────────────────────────────────────────
    // Twinkling star field
    // ─────────────────────────────────────────────────────────────────────

    if (starBrightness > 0.004 && elev > 0.02) {
        // Quantise direction → star cells (each has at most 1 star)
        vec3  snap     = floor(dir * 210.0) / 210.0;
        float seed     = _hash(snap.xy * vec2(43.0, 127.0) + snap.z * 59.0);

        // Star brightness / size (varies per cell)
        float szSeed   = _hash(snap.yx * vec2(71.0, 23.0) + snap.z * 17.0);
        float exponent = mix(430.0, 680.0, szSeed);
        float rawBrt   = pow(seed, exponent) * mix(2.4, 5.2, szSeed);

        // ── Twinkle: per-star unique frequency and phase ─────────────────
        float twSeed   = _hash(snap.xy * 33.0 + snap.z * 71.0);
        float twFreq   = mix(0.35, 4.0, twSeed);
        float twPhase  = twSeed * 6.28318530;
        // Primary twinkle
        float twinkle  = 0.62 + 0.38 * sin(time * twFreq + twPhase);
        // Secondary high-frequency shimmer on bright stars
        float shimmer  = 1.0 + 0.15 * sin(time * twFreq * 3.3 + twPhase * 1.7);
        float star     = rawBrt * twinkle * shimmer;

        // ── Star spectral class ──────────────────────────────────────────
        float colSeed = _hash(snap.yz * vec2(37.0, 53.0));
        vec3  starCol;
        if      (colSeed < 0.22) starCol = vec3(0.76, 0.84, 1.00);  // O/B  blue-white
        else if (colSeed < 0.48) starCol = vec3(1.00, 1.00, 0.94);  // A/F  white
        else if (colSeed < 0.74) starCol = vec3(1.00, 0.95, 0.70);  // G    yellow-white
        else                     starCol = vec3(1.00, 0.75, 0.55);  // K/M  warm orange

        // Dim near sun's position in sky
        float nearSun = max(0.0, dot(dir, sunDir));
        star *= max(0.0, 1.0 - nearSun * nearSun * 4.0);

        // Fade behind clouds
        star *= max(0.0, 1.0 - cloudAlpha * 1.2);

        sky += starCol * star * starBrightness;

        // ── Occasional bright "sparkle" with diffraction cross ───────────
        if (seed > 0.9982) {
            float sparkle = (seed - 0.9982) / 0.0018;
            sparkle       = sparkle * sparkle * twinkle * twinkle;
            // Cross arms: exponential falloff from snap position
            float crossW  = 0.0055;
            float arm_h   = exp(-abs(dir.x - snap.x) / crossW);
            float arm_v   = exp(-abs(dir.y - snap.y) / crossW);
            float cross2  = (arm_h + arm_v) * 0.5;
            sky += starCol * cross2 * sparkle * starBrightness * 0.50
                 * max(0.0, 1.0 - cloudAlpha * 1.5);
        }
    }

    // ─────────────────────────────────────────────────────────────────────
    // Sun disc + corona + blinding glare
    // ─────────────────────────────────────────────────────────────────────

    if (sunDiscEnabled > 0.5 && sunElevW > -0.14) {
        float angDist = acos(clamp(cosTheta, -1.0, 1.0));
        float sunR    = 0.0048;  // angular radius of sun disc (~0.275°)

        // ── Solar disc with limb darkening ───────────────────────────────
        float limbT   = clamp(1.0 - angDist / sunR, 0.0, 1.0);
        float limb    = smoothstep(0.0, 1.0, limbT) * step(angDist, sunR * 1.30);
        float limbDrk = mix(0.68, 1.0, limbT);   // edges 32% darker than centre

        // Colour: white-yellow at noon → deep orange-red at horizon
        float sunsetT = clamp(1.0 - sunElevW * 5.5, 0.0, 1.0);
        vec3  discCol = mix(
            vec3(1.00, 0.97, 0.82) * 5.0,   // noon: brilliant white-yellow
            vec3(1.00, 0.44, 0.05) * 2.8,   // sunset: deep orange-red
            sunsetT
        ) * limbDrk;

        // ── Multi-layer corona / aureole ─────────────────────────────────
        float c1 = exp(-angDist * 340.0) * 1.60;
        float c2 = exp(-angDist *  95.0) * 0.70;
        float c3 = exp(-angDist *  30.0) * 0.32;
        float c4 = exp(-angDist *   8.5) * 0.12;
        vec3  coronaCol = sunColor.rgb * (c1 + c2 + c3 + c4) * sunPower;

        // ── Vertical diffraction streak ──────────────────────────────────
        float streak = exp(-abs(dir.z - sunDir.z) * 90.0)
                     * exp(-max(0.0, 1.0 - cosTheta) * 150.0)
                     * 0.28 * sunPower;
        vec3  streakCol = sunColor.rgb * streak;

        // ── Blinding glare + chromatic aberration ────────────────────────
        float blindAmt  = pow(max(0.0, cosTheta), 55.0) * sunBlindStrength * sunPower;
        // Slightly wider red channel for chromatic effect
        vec3  blindCol  = vec3(
            pow(max(0.0, cosTheta), 38.0) * sunBlindStrength * sunPower * 1.35,
            blindAmt * 0.90,
            blindAmt * 0.65
        );

        // ── Visibility: blocked by clouds, clipped below horizon ─────────
        float sunVis = (1.0 - cloudAlpha * 0.93)
                     * clamp((sunElevW + 0.12) * 7.5, 0.0, 1.0);

        sky += (discCol * limb + coronaCol + streakCol + blindCol) * sunVis;
    }

    // ─────────────────────────────────────────────────────────────────────
    // Moon disc + surface detail + corona
    // ─────────────────────────────────────────────────────────────────────

    if (moonEnabled > 0.5) {
        vec3  mDir     = normalize(moonDir);
        float moonDot  = dot(dir, mDir);
        float moonR    = 0.9990;  // cos(~2.56°)
        float moonDisc = smoothstep(moonR, moonR + 0.0008, moonDot);

        // Surface noise → subtle crater/mare variation
        vec3  mTang    = normalize(dir - mDir * moonDot);
        float mDetail  = _vnoise(vec2(mTang.x * 550.0 + 30.0,
                                      mTang.z * 550.0 + 70.0)) * 0.18 + 0.82;

        // Limb darkening
        float mLimb    = mix(0.65, 1.0,
                             clamp(1.0 - max(0.0, 1.0 - moonDot) * 3.0, 0.0, 1.0));
        vec3  moonSurf = vec3(0.88, 0.88, 0.80) * mDetail * mLimb;

        // Multi-layer glow
        float mH1 = exp(-max(0.0, 1.0 - moonDot) * 110.0) * 0.30;
        float mH2 = exp(-max(0.0, 1.0 - moonDot) *  24.0) * 0.09;
        float mH3 = exp(-max(0.0, 1.0 - moonDot) *   6.0) * 0.03;
        vec3  moonGlow = moonColor.rgb * (mH1 + mH2 + mH3) * 0.85;

        float moonVis = max(0.0, 1.0 - cloudAlpha * 0.90);
        sky = mix(sky, moonSurf * 1.55, moonDisc * moonVis);
        sky += moonGlow * moonVis;
    }

    // ── Zone colour scale ─────────────────────────────────────────────────
    sky *= skyScale.rgb;

    // ── Tonemapping: Reinhard + mild gamma lift ───────────────────────────
    sky  = sky / (sky + vec3(0.72));                          // soft knee HDR clamp
    sky  = pow(clamp(sky, 0.0, 1.0), vec3(1.0 / 1.15));     // slight gamma lift

    fragColor = vec4(sky, 1.0);
}
