"""Advanced cinematic outdoor lighting system for Toontown.

Zone lighting profiles – each zone (and street variant) captures a real-world
atmospheric feel:
  tt / tt_street – Toontown Central:    warm Nebraska afternoon ~3 PM golden hour
  dd / dd_street – Donald's Dock:       heavy overcast maritime fog, diffuse daylight
  dg / dg_street – Daisy's Gardens:     blazing Virginia spring noon, intense blue sky
  mm / mm_street – Minnie's Melodyland: deep California sunset, orange-purple sky
  br / br_street – The Brrrgh:          arctic blizzard, pale powder-blue light
  dl / dl_street – Donald's Dreamland:  moonlit midnight, cool blue-purple starry sky
  gs             – Goofy Speedway:      hazy mid-morning race day, light dusty haze
  sellbot_hq     – dark purple factory smog
  cashbot_hq     – sickly green money trainyard
  lawbot_hq      – cold steel-blue overcast courtroom evening
  bossbot_hq     – near-pitch-black boardroom with brown ember undertones
  factory_int    – Sellbot / Lawbot factory interior: dim green-tinted machinery light
  mint_int       – Cashbot Mint interior: cold metallic pale-green vaults
  office_int     – Lawbot Office interior: harsh white corridor fluorescents
  bossbot_cc     – Bossbot Country Club interior: mahogany dimness + warm lamp fill
  golf_course    – Bossbot Golf Course exterior: verdant sunlit fairway

New / upgraded systems
────────────────────────
POST-PROCESS (no full-scene RTT compositor)
  • CommonFilters bloom on the main window (adds glow on bright areas).
  • Screen-space sun shafts via a lightweight render2dp overlay (sunrays shaders).
  • Avoids the custom FilterManager “scene → texture → fullscreen quad” path that
    triggered bottom-left viewport bugs on some drivers.
  Controlled by lighting-bloom-enabled, lighting-god-rays, zone bloom/ray params.

PROCEDURAL SKY
  • ProceduralSky replaces hood.sky model with a shader-driven atmospheric sky
    dome: Rayleigh + Mie scattering, FBM cumulus clouds that react to sunlight,
    night-time star field, optional moon disc (Donald's Dreamland).
  • Toggle: want-procedural-sky (default True).  Falls back to model sky if
    shaders unavailable.

SHADOW SYSTEM
  • Full-zone coverage: shadow film size computed from actual scene geometry.
  • 2D card / billboard geometry is excluded from the shadow PASS (shadow
    camera mask) so flat foliage planes don't cast false block shadows.  They
    still *receive* shadows normally.
  • Transparent texture planes (foliage, building facades) receive and cast
    shadows correctly via clearLightOff + a dedicated shadow mask BitMask32.
  • Per-zone shadowDarknessFloor prevents pitch-black even in deep shadow.

DAY / NIGHT CYCLE
  • Per-zone keyframe tables; all parameters smoothly interpolated.
  • All new parameters (cloud coverage, star brightness, Mie turbidity, etc.)
    are also interpolated across the day/night cycle.
  • Toggle: want-day-night-cycle.

BACKWARD COMPATIBILITY
  Public API unchanged: begin(), end(), shadeExtraSubtree(),
  clearExtraSubtree(), refreshSettings().
  New: setTimeOfDay(), setupWaterReflection(), setWaterReflectionQuality().
"""

from __future__ import annotations

import math
import os
from typing import Any

from panda3d.core import (
    AmbientLight,
    BitMask32,
    BillboardEffect,
    CardMaker,
    ColorBlendAttrib,
    ConfigVariableBool,
    DepthOffsetAttrib,
    DirectionalLight,
    Filename,
    Fog,
    LightAttrib,
    Material,
    NodePath,
    PlaneNode,
    PointLight,
    RenderState,
    Shader,
    Texture,
    TransparencyAttrib,
    Vec3,
    Vec4,
)

from direct.showbase.ShowBaseGlobal import globalClock
from direct.task.TaskManagerGlobal import taskMgr

from toontown.toonbase.ToonBaseGlobal import base

# Shader bisect — increment to add the next custom GLSL subsystem:
#   0 = modern outdoor stack off (begin() no-ops; legacy model sky in SkyUtil).
#   1 = procedural sky GLSL only (light rig + fog/tint/bg + sky dome; no HDR post,
#       bloom, god rays, or water GLSL).
#   2 = + post-process (see _LEVEL2_POST_SINGLE; one subsystem at a time for debugging).
#   3 = + water reflection GLSL (full pipeline).
_OUTDOOR_SHADER_BISECT_LEVEL = 3

# When bisect level is 2, enable exactly one post FX:
#   'full' / 'stack' — bloom + sun-ray overlay (default cinematic post).
#   'bloom'          — CommonFilters bloom only.
#   'godrays'        — sunrays card on render2dp only.
# Level 3+ always uses full post (bloom + god rays).
_LEVEL2_POST_SINGLE = 'full'


def _fixPostProcessRttViewports() -> None:
    """Normalize every DisplayRegion on FilterManager offscreen buffers.

    Stock FilterManager.renderSceneInto uses ``buffer.makeDisplayRegion()`` with no
    bounds; on some GL drivers that yields a sub-rectangle (often bottom-left
    quarter).  The scene is then rendered into only part of the colour texture,
    while the compositing quad still samples the full texture — exactly the
    broken layout players see.  Forcing (0,1)×(0,1) on those regions fixes it.

    NOTE: _bloomFilters is a CommonFilters instance, NOT a FilterManager.
    CommonFilters stores its FilterManager at _bloomFilters.manager — so
    buffers live at _bloomFilters.manager.buffers, not _bloomFilters.buffers.
    Getting this wrong means the bloom RTT buffers are never repaired.
    """
    # Collect FilterManager instances that own offscreen buffers (bloom, etc.).
    fms_to_fix = []
    if _bloomFilters is not None:
        # _bloomFilters is a CommonFilters whose internal FilterManager is at .manager
        inner = getattr(_bloomFilters, 'manager', None)
        if inner is not None:
            fms_to_fix.append(inner)

    for fm in fms_to_fix:
        try:
            for buf in getattr(fm, 'buffers', None) or []:
                if buf is None:
                    continue
                n = buf.getNumDisplayRegions()
                for i in range(n):
                    dr = buf.getDisplayRegion(i)
                    if not dr:
                        continue
                    dr.setDimensions(0.0, 1.0, 0.0, 1.0)
                    if dr.supportsPixelZoom():
                        dr.setPixelZoom(1)
                    try:
                        dr.setScissorEnabled(False)
                    except Exception:
                        pass
        except Exception:
            pass

# ─────────────────────────────────────────────────────────────────────────────
# Zone lighting profiles
# ─────────────────────────────────────────────────────────────────────────────
_ZONE_PROFILES: dict[str, dict] = {

    # ── Toontown Central playground ───────────────────────────────────────────
    'tt': {
        'ambient':          (0.22, 0.27, 0.40, 1.0),
        'key':              (1.22, 1.08, 0.78, 1.0),
        'keyHpr':           (135, -42, 0),
        'fill':             (0.24, 0.32, 0.50, 1.0),
        'fillHpr':          (-45, -18, 0),
        'rim':              None,
        'shadowCaster':     True,
        'shadowRes':        4096,
        'shadowArea':       160,
        'shadowResScale':   0.75,
        'shadowAreaScale':  1.40,
        'shadowFollowDist': 280.0,
        'shadowDarknessFloor': 0.18,
        'fogColor':         (0.72, 0.80, 0.92, 1.0),
        'fogNear':          80.0,
        'fogFar':           440.0,
        'fogExponent':      None,
        'skyScale':         (1.04, 1.01, 0.91, 1.0),
        'clearColor':       (0.50, 0.68, 0.90, 1.0),
        'sunUV':            (0.65, 0.78),
        'rayColor':         (1.00, 0.94, 0.68, 1.0),
        'rayIntensity':     0.38,
        'bloomIntensity':   0.32,
        'bloomThreshold':   0.62,
        'exposure':         1.00,
        'hasWater':         True,
        'waterColor':       (0.28, 0.52, 0.72, 0.88),
        'waterReflQuality': 'medium',
        'dayNightEnabled':  True,
        'cloudCoverage':    0.42,
        'cloudSpeed':       0.70,
        'cloudSharpness':   0.55,
        'turbidity':        2.5,
        'starBrightness':   0.0,
        'moonEnabled':      False,
    },

    # ── TT streets ────────────────────────────────────────────────────────────
    'tt_street': {
        'ambient':          (0.20, 0.25, 0.38, 1.0),
        'key':              (1.18, 1.05, 0.75, 1.0),
        'keyHpr':           (140, -40, 0),
        'fill':             (0.22, 0.30, 0.48, 1.0),
        'fillHpr':          (-50, -20, 0),
        'rim':              None,
        'shadowCaster':     True,
        'shadowRes':        2048,
        'shadowArea':       140,
        'shadowResScale':   1.00,
        'shadowAreaScale':  1.20,
        'shadowFollowDist': 220.0,
        'shadowDarknessFloor': 0.16,
        'fogColor':         (0.70, 0.78, 0.90, 1.0),
        'fogNear':          70.0,
        'fogFar':           380.0,
        'fogExponent':      None,
        'skyScale':         (1.04, 1.01, 0.91, 1.0),
        'clearColor':       (0.48, 0.66, 0.88, 1.0),
        'sunUV':            (0.65, 0.78),
        'rayColor':         (1.00, 0.92, 0.66, 1.0),
        'rayIntensity':     0.30,
        'bloomIntensity':   0.28,
        'bloomThreshold':   0.64,
        'exposure':         1.00,
        'hasWater':         False,
        'dayNightEnabled':  True,
        'cloudCoverage':    0.40,
        'cloudSpeed':       0.68,
        'cloudSharpness':   0.55,
        'turbidity':        2.4,
        'starBrightness':   0.0,
        'moonEnabled':      False,
    },

    # ── Donald's Dock playground ──────────────────────────────────────────────
    'dd': {
        'ambient':          (0.60, 0.63, 0.68, 1.0),
        'key':              (0.70, 0.74, 0.80, 1.0),
        'keyHpr':           (0,   -80,  0),
        'fill':             (0.52, 0.56, 0.62, 1.0),
        'fillHpr':          (180, -55,  0),
        'rim':              None,
        'shadowCaster':     False,
        'shadowRes':        512,
        'shadowArea':       180,
        'shadowDarknessFloor': 0.22,
        'fogColor':         (0.72, 0.76, 0.82, 1.0),
        'fogNear':          0.0,
        'fogFar':           None,
        'fogExponent':      0.011,
        'skyScale':         (0.84, 0.87, 0.92, 1.0),
        'clearColor':       (0.70, 0.74, 0.80, 1.0),
        'sunUV':            (0.50, 0.88),
        'rayColor':         (0.90, 0.93, 0.98, 1.0),
        'rayIntensity':     0.00,
        'bloomIntensity':   0.18,
        'bloomThreshold':   0.68,
        'exposure':         0.95,
        'hasWater':         True,
        'waterColor':       (0.22, 0.32, 0.44, 0.90),
        'waterReflQuality': 'high',
        'dayNightEnabled':  True,
        'cloudCoverage':    0.88,
        'cloudSpeed':       1.10,
        'cloudSharpness':   0.20,
        'turbidity':        5.5,
        'starBrightness':   0.0,
        'moonEnabled':      False,
    },

    # ── DD streets ────────────────────────────────────────────────────────────
    'dd_street': {
        'ambient':          (0.58, 0.61, 0.66, 1.0),
        'key':              (0.68, 0.72, 0.78, 1.0),
        'keyHpr':           (0,   -78,  0),
        'fill':             (0.50, 0.54, 0.60, 1.0),
        'fillHpr':          (180, -52,  0),
        'rim':              None,
        'shadowCaster':     False,
        'shadowRes':        512,
        'shadowArea':       140,
        'shadowDarknessFloor': 0.20,
        'fogColor':         (0.70, 0.74, 0.80, 1.0),
        'fogNear':          0.0,
        'fogFar':           None,
        'fogExponent':      0.014,
        'skyScale':         (0.84, 0.87, 0.92, 1.0),
        'clearColor':       (0.68, 0.72, 0.78, 1.0),
        'sunUV':            (0.50, 0.85),
        'rayColor':         (0.88, 0.92, 0.96, 1.0),
        'rayIntensity':     0.00,
        'bloomIntensity':   0.15,
        'bloomThreshold':   0.70,
        'exposure':         0.93,
        'hasWater':         False,
        'dayNightEnabled':  True,
        'cloudCoverage':    0.90,
        'cloudSpeed':       1.20,
        'cloudSharpness':   0.18,
        'turbidity':        5.8,
        'starBrightness':   0.0,
        'moonEnabled':      False,
    },

    # ── Daisy's Gardens playground ────────────────────────────────────────────
    'dg': {
        'ambient':          (0.18, 0.25, 0.42, 1.0),
        'key':              (1.18, 1.08, 0.88, 1.0),
        'keyHpr':           (170, -68, 0),
        'fill':             (0.22, 0.32, 0.52, 1.0),
        'fillHpr':          (-10, -22, 0),
        'rim':              (0.10, 0.16, 0.30, 1.0),
        'rimHpr':           (0,    55,  0),
        'shadowCaster':     True,
        'shadowRes':        4096,
        'shadowArea':       155,
        'shadowResScale':   1.00,
        'shadowAreaScale':  0.95,
        'shadowFollowDist': 260.0,
        'shadowDarknessFloor': 0.16,
        'fogColor':         (0.62, 0.80, 1.00, 1.0),
        'fogNear':          120.0,
        'fogFar':           540.0,
        'fogExponent':      None,
        'skyScale':         (0.88, 0.96, 1.14, 1.0),
        'clearColor':       (0.36, 0.62, 1.00, 1.0),
        'sunUV':            (0.54, 0.90),
        'rayColor':         (1.00, 1.00, 0.88, 1.0),
        'rayIntensity':     0.58,
        'bloomIntensity':   0.42,
        'bloomThreshold':   0.58,
        'exposure':         1.05,
        'hasWater':         True,
        'waterColor':       (0.24, 0.54, 0.36, 0.84),
        'waterReflQuality': 'medium',
        'dayNightEnabled':  True,
        'cloudCoverage':    0.28,
        'cloudSpeed':       0.55,
        'cloudSharpness':   0.70,
        'turbidity':        1.8,
        'starBrightness':   0.0,
        'moonEnabled':      False,
    },

    # ── DG streets ────────────────────────────────────────────────────────────
    'dg_street': {
        'ambient':          (0.16, 0.23, 0.40, 1.0),
        'key':              (1.15, 1.05, 0.85, 1.0),
        'keyHpr':           (172, -66, 0),
        'fill':             (0.20, 0.30, 0.50, 1.0),
        'fillHpr':          (-12, -20, 0),
        'rim':              (0.08, 0.14, 0.28, 1.0),
        'rimHpr':           (0,    52,  0),
        'shadowCaster':     True,
        'shadowRes':        2048,
        'shadowArea':       130,
        'shadowResScale':   1.00,
        'shadowAreaScale':  1.10,
        'shadowFollowDist': 220.0,
        'shadowDarknessFloor': 0.14,
        'fogColor':         (0.60, 0.78, 0.98, 1.0),
        'fogNear':          100.0,
        'fogFar':           480.0,
        'fogExponent':      None,
        'skyScale':         (0.88, 0.96, 1.14, 1.0),
        'clearColor':       (0.34, 0.60, 0.98, 1.0),
        'sunUV':            (0.54, 0.88),
        'rayColor':         (1.00, 1.00, 0.88, 1.0),
        'rayIntensity':     0.50,
        'bloomIntensity':   0.38,
        'bloomThreshold':   0.60,
        'exposure':         1.05,
        'hasWater':         False,
        'dayNightEnabled':  True,
        'cloudCoverage':    0.24,
        'cloudSpeed':       0.52,
        'cloudSharpness':   0.72,
        'turbidity':        1.8,
        'starBrightness':   0.0,
        'moonEnabled':      False,
    },

    # ── Minnie's Melodyland playground ───────────────────────────────────────
    'mm': {
        'ambient':          (0.42, 0.28, 0.30, 1.0),
        'key':              (1.10, 0.50, 0.18, 1.0),
        'keyHpr':           (260, -14, 0),
        'fill':             (0.22, 0.18, 0.40, 1.0),
        'fillHpr':          (80,  -28, 0),
        'rim':              (0.90, 0.40, 0.12, 1.0),
        'rimHpr':           (258, -8,  0),
        'shadowCaster':     True,
        'shadowRes':        2048,
        'shadowArea':       200,
        'shadowResScale':   0.85,
        'shadowAreaScale':  1.55,
        'shadowFollowDist': 260.0,
        'shadowDarknessFloor': 0.20,
        'fogColor':         (0.80, 0.44, 0.20, 1.0),
        'fogNear':          10.0,
        'fogFar':           330.0,
        'fogExponent':      None,
        'skyScale':         (1.30, 0.72, 0.48, 1.0),
        'clearColor':       (0.88, 0.46, 0.18, 1.0),
        'sunUV':            (0.10, 0.43),
        'rayColor':         (1.00, 0.58, 0.22, 1.0),
        'rayIntensity':     0.70,
        'bloomIntensity':   0.55,
        'bloomThreshold':   0.55,
        'exposure':         1.02,
        'hasWater':         False,
        'dayNightEnabled':  True,
        'cloudCoverage':    0.55,
        'cloudSpeed':       0.85,
        'cloudSharpness':   0.45,
        'turbidity':        3.5,
        'starBrightness':   0.0,
        'moonEnabled':      False,
    },

    # ── MM streets ────────────────────────────────────────────────────────────
    'mm_street': {
        'ambient':          (0.40, 0.26, 0.28, 1.0),
        'key':              (1.06, 0.48, 0.16, 1.0),
        'keyHpr':           (258, -12, 0),
        'fill':             (0.20, 0.16, 0.38, 1.0),
        'fillHpr':          (78,  -26, 0),
        'rim':              (0.86, 0.38, 0.10, 1.0),
        'rimHpr':           (256, -6,  0),
        'shadowCaster':     True,
        'shadowRes':        2048,
        'shadowArea':       160,
        'shadowResScale':   0.85,
        'shadowAreaScale':  1.40,
        'shadowFollowDist': 220.0,
        'shadowDarknessFloor': 0.18,
        'fogColor':         (0.78, 0.42, 0.18, 1.0),
        'fogNear':          8.0,
        'fogFar':           280.0,
        'fogExponent':      None,
        'skyScale':         (1.30, 0.72, 0.48, 1.0),
        'clearColor':       (0.86, 0.44, 0.16, 1.0),
        'sunUV':            (0.10, 0.42),
        'rayColor':         (1.00, 0.56, 0.20, 1.0),
        'rayIntensity':     0.62,
        'bloomIntensity':   0.50,
        'bloomThreshold':   0.56,
        'exposure':         1.02,
        'hasWater':         False,
        'dayNightEnabled':  True,
        'cloudCoverage':    0.52,
        'cloudSpeed':       0.88,
        'cloudSharpness':   0.42,
        'turbidity':        3.6,
        'starBrightness':   0.0,
        'moonEnabled':      False,
    },

    # ── The Brrrgh playground ─────────────────────────────────────────────────
    'br': {
        'ambient':          (0.42, 0.50, 0.68, 1.0),
        'key':              (0.62, 0.72, 0.90, 1.0),
        'keyHpr':           (180, -18, 0),
        'fill':             (0.38, 0.46, 0.62, 1.0),
        'fillHpr':          (0,   -12, 0),
        'rim':              (0.48, 0.56, 0.74, 1.0),
        'rimHpr':           (178, -6,   0),
        'shadowCaster':     False,
        'shadowRes':        512,
        'shadowArea':       180,
        'shadowDarknessFloor': 0.24,
        'fogColor':         (0.68, 0.78, 0.94, 1.0),
        'fogNear':          0.0,
        'fogFar':           None,
        'fogExponent':      0.016,
        'skyScale':         (0.78, 0.88, 1.08, 1.0),
        'clearColor':       (0.62, 0.74, 0.92, 1.0),
        'sunUV':            (0.50, 0.44),
        'rayColor':         (0.82, 0.90, 1.00, 1.0),
        'rayIntensity':     0.08,
        'bloomIntensity':   0.20,
        'bloomThreshold':   0.70,
        'exposure':         0.90,
        'hasWater':         False,
        'dayNightEnabled':  True,
        'cloudCoverage':    0.78,
        'cloudSpeed':       1.40,
        'cloudSharpness':   0.15,
        'turbidity':        6.0,
        'starBrightness':   0.0,
        'moonEnabled':      False,
    },

    # ── BR streets ────────────────────────────────────────────────────────────
    'br_street': {
        'ambient':          (0.40, 0.48, 0.66, 1.0),
        'key':              (0.60, 0.70, 0.88, 1.0),
        'keyHpr':           (180, -16, 0),
        'fill':             (0.36, 0.44, 0.60, 1.0),
        'fillHpr':          (0,   -10, 0),
        'rim':              (0.46, 0.54, 0.72, 1.0),
        'rimHpr':           (178, -4,   0),
        'shadowCaster':     False,
        'shadowRes':        512,
        'shadowArea':       140,
        'shadowDarknessFloor': 0.22,
        'fogColor':         (0.66, 0.76, 0.92, 1.0),
        'fogNear':          0.0,
        'fogFar':           None,
        'fogExponent':      0.020,
        'skyScale':         (0.78, 0.88, 1.08, 1.0),
        'clearColor':       (0.60, 0.72, 0.90, 1.0),
        'sunUV':            (0.50, 0.42),
        'rayColor':         (0.80, 0.88, 1.00, 1.0),
        'rayIntensity':     0.06,
        'bloomIntensity':   0.16,
        'bloomThreshold':   0.72,
        'exposure':         0.88,
        'hasWater':         False,
        'dayNightEnabled':  True,
        'cloudCoverage':    0.80,
        'cloudSpeed':       1.50,
        'cloudSharpness':   0.12,
        'turbidity':        6.2,
        'starBrightness':   0.0,
        'moonEnabled':      False,
    },

    # ── Donald's Dreamland playground ─────────────────────────────────────────
    'dl': {
        'ambient':          (0.06, 0.08, 0.16, 1.0),
        'key':              (0.40, 0.46, 0.68, 1.0),
        'keyHpr':           (225, -55, 0),
        'fill':             (0.04, 0.06, 0.12, 1.0),
        'fillHpr':          (45,  -15, 0),
        'rim':              (0.30, 0.36, 0.58, 1.0),
        'rimHpr':           (220, -50, 0),
        'shadowCaster':     True,
        'shadowRes':        2048,
        'shadowArea':       170,
        'shadowResScale':   0.75,
        'shadowAreaScale':  1.45,
        'shadowFollowDist': 260.0,
        'shadowDarknessFloor': 0.08,
        'fogColor':         (0.05, 0.07, 0.14, 1.0),
        'fogNear':          0.0,
        'fogFar':           None,
        'fogExponent':      0.006,
        'skyScale':         (0.42, 0.48, 0.74, 1.0),
        'clearColor':       (0.03, 0.04, 0.10, 1.0),
        'sunUV':            (0.30, 0.82),
        'rayColor':         (0.58, 0.70, 1.00, 1.0),
        'rayIntensity':     0.32,
        'bloomIntensity':   0.22,
        'bloomThreshold':   0.70,
        'exposure':         1.20,
        'hasWater':         False,
        'dayNightEnabled':  True,
        'cloudCoverage':    0.22,
        'cloudSpeed':       0.25,
        'cloudSharpness':   0.50,
        'turbidity':        1.5,
        'starBrightness':   0.92,
        'moonEnabled':      True,
        'moonDir':          (225, -55, 0),
    },

    # ── DL streets ────────────────────────────────────────────────────────────
    'dl_street': {
        'ambient':          (0.05, 0.07, 0.14, 1.0),
        'key':              (0.38, 0.44, 0.65, 1.0),
        'keyHpr':           (225, -52, 0),
        'fill':             (0.03, 0.05, 0.10, 1.0),
        'fillHpr':          (42,  -14, 0),
        'rim':              (0.28, 0.34, 0.55, 1.0),
        'rimHpr':           (222, -48, 0),
        'shadowCaster':     True,
        'shadowRes':        2048,
        'shadowArea':       140,
        'shadowResScale':   0.75,
        'shadowAreaScale':  1.30,
        'shadowFollowDist': 220.0,
        'shadowDarknessFloor': 0.06,
        'fogColor':         (0.04, 0.06, 0.12, 1.0),
        'fogNear':          0.0,
        'fogFar':           None,
        'fogExponent':      0.008,
        'skyScale':         (0.42, 0.48, 0.74, 1.0),
        'clearColor':       (0.03, 0.04, 0.10, 1.0),
        'sunUV':            (0.30, 0.80),
        'rayColor':         (0.56, 0.68, 1.00, 1.0),
        'rayIntensity':     0.26,
        'bloomIntensity':   0.18,
        'bloomThreshold':   0.72,
        'exposure':         1.22,
        'hasWater':         False,
        'dayNightEnabled':  True,
        'cloudCoverage':    0.20,
        'cloudSpeed':       0.22,
        'cloudSharpness':   0.48,
        'turbidity':        1.5,
        'starBrightness':   0.88,
        'moonEnabled':      True,
        'moonDir':          (225, -55, 0),
    },

    # ── Goofy Speedway ────────────────────────────────────────────────────────
    'gs': {
        'ambient':          (0.30, 0.32, 0.40, 1.0),
        'key':              (1.10, 1.00, 0.82, 1.0),
        'keyHpr':           (130, -48, 0),
        'fill':             (0.24, 0.28, 0.40, 1.0),
        'fillHpr':          (-50, -30, 0),
        'rim':              None,
        'shadowCaster':     True,
        'shadowRes':        2048,
        'shadowArea':       180,
        'shadowResScale':   0.90,
        'shadowAreaScale':  1.20,
        'shadowFollowDist': 240.0,
        'shadowDarknessFloor': 0.20,
        'fogColor':         (0.78, 0.76, 0.68, 1.0),
        'fogNear':          60.0,
        'fogFar':           380.0,
        'fogExponent':      None,
        'skyScale':         (1.06, 1.02, 0.84, 1.0),
        'clearColor':       (0.56, 0.64, 0.72, 1.0),
        'sunUV':            (0.60, 0.74),
        'rayColor':         (1.00, 0.92, 0.70, 1.0),
        'rayIntensity':     0.26,
        'bloomIntensity':   0.24,
        'bloomThreshold':   0.64,
        'exposure':         1.00,
        'hasWater':         False,
        'dayNightEnabled':  True,
        'cloudCoverage':    0.32,
        'cloudSpeed':       0.90,
        'cloudSharpness':   0.50,
        'turbidity':        3.0,
        'starBrightness':   0.0,
        'moonEnabled':      False,
    },

    # ── Golf Course (Bossbot) exterior ────────────────────────────────────────
    'golf_course': {
        'ambient':          (0.24, 0.32, 0.28, 1.0),
        'key':              (1.20, 1.12, 0.88, 1.0),
        'keyHpr':           (160, -58, 0),
        'fill':             (0.20, 0.30, 0.22, 1.0),
        'fillHpr':          (-20, -28, 0),
        'rim':              (0.12, 0.18, 0.10, 1.0),
        'rimHpr':           (0,    48,  0),
        'shadowCaster':     True,
        'shadowRes':        2048,
        'shadowArea':       200,
        'shadowResScale':   1.00,
        'shadowAreaScale':  1.30,
        'shadowFollowDist': 280.0,
        'shadowDarknessFloor': 0.18,
        'fogColor':         (0.60, 0.78, 0.60, 1.0),
        'fogNear':          100.0,
        'fogFar':           520.0,
        'fogExponent':      None,
        'skyScale':         (0.88, 1.00, 0.82, 1.0),
        'clearColor':       (0.40, 0.68, 0.44, 1.0),
        'sunUV':            (0.56, 0.88),
        'rayColor':         (1.00, 1.00, 0.80, 1.0),
        'rayIntensity':     0.50,
        'bloomIntensity':   0.38,
        'bloomThreshold':   0.60,
        'exposure':         1.05,
        'hasWater':         True,
        'waterColor':       (0.28, 0.60, 0.40, 0.82),
        'waterReflQuality': 'medium',
        'dayNightEnabled':  False,
        'cloudCoverage':    0.30,
        'cloudSpeed':       0.65,
        'cloudSharpness':   0.60,
        'turbidity':        2.2,
        'starBrightness':   0.0,
        'moonEnabled':      False,
    },

    # ── Sellbot HQ (exterior) ─────────────────────────────────────────────────
    'sellbot_hq': {
        'ambient':          (0.08, 0.05, 0.14, 1.0),
        'key':              (0.22, 0.15, 0.34, 1.0),
        'keyHpr':           (135, -65, 0),
        'fill':             (0.06, 0.04, 0.10, 1.0),
        'fillHpr':          (-60, -30, 0),
        'rim':              (0.14, 0.08, 0.22, 1.0),
        'rimHpr':           (130, -60, 0),
        'shadowCaster':     False,
        'shadowRes':        512,
        'shadowArea':       180,
        'shadowDarknessFloor': 0.06,
        'fogColor':         (0.12, 0.08, 0.18, 1.0),
        'fogNear':          0.0,
        'fogFar':           None,
        'fogExponent':      0.020,
        'skyScale':         (0.58, 0.38, 0.80, 1.0),
        'clearColor':       (0.08, 0.05, 0.14, 1.0),
        'sunUV':            (0.50, 0.50),
        'rayColor':         (0.60, 0.38, 0.92, 1.0),
        'rayIntensity':     0.04,
        'bloomIntensity':   0.06,
        'bloomThreshold':   0.82,
        'exposure':         1.30,
        'hasWater':         False,
        'dayNightEnabled':  False,
        'cloudCoverage':    0.95,
        'cloudSpeed':       0.30,
        'cloudSharpness':   0.05,
        'turbidity':        8.0,
        'starBrightness':   0.0,
        'moonEnabled':      False,
    },

    # ── Sellbot Factory interior ──────────────────────────────────────────────
    'factory_int': {
        'ambient':          (0.08, 0.12, 0.06, 1.0),
        'key':              (0.35, 0.50, 0.28, 1.0),
        'keyHpr':           (90, -75, 0),
        'fill':             (0.06, 0.10, 0.04, 1.0),
        'fillHpr':          (-80, -40, 0),
        'rim':              (0.12, 0.20, 0.08, 1.0),
        'rimHpr':           (88, -70, 0),
        'shadowCaster':     False,
        'shadowRes':        512,
        'shadowArea':       120,
        'shadowDarknessFloor': 0.06,
        'fogColor':         (0.04, 0.08, 0.02, 1.0),
        'fogNear':          0.0,
        'fogFar':           None,
        'fogExponent':      0.030,
        'skyScale':         (0.42, 0.62, 0.30, 1.0),
        'clearColor':       (0.03, 0.05, 0.02, 1.0),
        'sunUV':            (0.50, 0.50),
        'rayColor':         (0.40, 0.70, 0.20, 1.0),
        'rayIntensity':     0.02,
        'bloomIntensity':   0.10,
        'bloomThreshold':   0.60,
        'exposure':         1.40,
        'hasWater':         False,
        'dayNightEnabled':  False,
        'cloudCoverage':    0.0,
        'cloudSpeed':       0.0,
        'cloudSharpness':   0.0,
        'turbidity':        1.0,
        'starBrightness':   0.0,
        'moonEnabled':      False,
    },

    # ── Cashbot HQ (exterior) ─────────────────────────────────────────────────
    'cashbot_hq': {
        'ambient':          (0.06, 0.10, 0.06, 1.0),
        'key':              (0.28, 0.40, 0.18, 1.0),
        'keyHpr':           (90, -50, 0),
        'fill':             (0.04, 0.08, 0.04, 1.0),
        'fillHpr':          (-80, -25, 0),
        'rim':              (0.24, 0.32, 0.10, 1.0),
        'rimHpr':           (88, -45, 0),
        'shadowCaster':     True,
        'shadowRes':        1024,
        'shadowArea':       160,
        'shadowResScale':   0.75,
        'shadowAreaScale':  1.20,
        'shadowFollowDist': 210.0,
        'shadowDarknessFloor': 0.06,
        'fogColor':         (0.08, 0.14, 0.06, 1.0),
        'fogNear':          0.0,
        'fogFar':           None,
        'fogExponent':      0.012,
        'skyScale':         (0.48, 0.82, 0.38, 1.0),
        'clearColor':       (0.06, 0.12, 0.04, 1.0),
        'sunUV':            (0.50, 0.65),
        'rayColor':         (0.68, 1.00, 0.38, 1.0),
        'rayIntensity':     0.08,
        'bloomIntensity':   0.24,
        'bloomThreshold':   0.58,
        'exposure':         1.25,
        'hasWater':         False,
        'dayNightEnabled':  False,
        'cloudCoverage':    0.85,
        'cloudSpeed':       0.40,
        'cloudSharpness':   0.10,
        'turbidity':        7.0,
        'starBrightness':   0.0,
        'moonEnabled':      False,
    },

    # ── Cashbot Mint interior ─────────────────────────────────────────────────
    'mint_int': {
        'ambient':          (0.06, 0.10, 0.08, 1.0),
        'key':              (0.32, 0.50, 0.38, 1.0),
        'keyHpr':           (90, -80, 0),
        'fill':             (0.04, 0.08, 0.06, 1.0),
        'fillHpr':          (-80, -40, 0),
        'rim':              (0.10, 0.16, 0.12, 1.0),
        'rimHpr':           (88, -75, 0),
        'shadowCaster':     False,
        'shadowRes':        512,
        'shadowArea':       100,
        'shadowDarknessFloor': 0.05,
        'fogColor':         (0.02, 0.06, 0.04, 1.0),
        'fogNear':          0.0,
        'fogFar':           None,
        'fogExponent':      0.025,
        'skyScale':         (0.38, 0.68, 0.48, 1.0),
        'clearColor':       (0.02, 0.05, 0.03, 1.0),
        'sunUV':            (0.50, 0.50),
        'rayColor':         (0.30, 0.80, 0.50, 1.0),
        'rayIntensity':     0.02,
        'bloomIntensity':   0.08,
        'bloomThreshold':   0.55,
        'exposure':         1.45,
        'hasWater':         False,
        'dayNightEnabled':  False,
        'cloudCoverage':    0.0,
        'cloudSpeed':       0.0,
        'cloudSharpness':   0.0,
        'turbidity':        1.0,
        'starBrightness':   0.0,
        'moonEnabled':      False,
    },

    # ── Lawbot HQ (exterior) ──────────────────────────────────────────────────
    'lawbot_hq': {
        'ambient':          (0.08, 0.10, 0.22, 1.0),
        'key':              (0.28, 0.36, 0.58, 1.0),
        'keyHpr':           (180, -55, 0),
        'fill':             (0.06, 0.08, 0.18, 1.0),
        'fillHpr':          (0, -30, 0),
        'rim':              (0.10, 0.14, 0.30, 1.0),
        'rimHpr':           (178, -50, 0),
        'shadowCaster':     False,
        'shadowRes':        512,
        'shadowArea':       180,
        'shadowDarknessFloor': 0.08,
        'fogColor':         (0.18, 0.22, 0.42, 1.0),
        'fogNear':          0.0,
        'fogFar':           None,
        'fogExponent':      0.014,
        'skyScale':         (0.50, 0.62, 0.94, 1.0),
        'clearColor':       (0.12, 0.16, 0.34, 1.0),
        'sunUV':            (0.50, 0.70),
        'rayColor':         (0.58, 0.78, 1.00, 1.0),
        'rayIntensity':     0.04,
        'bloomIntensity':   0.09,
        'bloomThreshold':   0.75,
        'exposure':         1.20,
        'hasWater':         False,
        'dayNightEnabled':  False,
        'cloudCoverage':    0.92,
        'cloudSpeed':       0.20,
        'cloudSharpness':   0.10,
        'turbidity':        7.5,
        'starBrightness':   0.0,
        'moonEnabled':      False,
    },

    # ── Lawbot Office interior ────────────────────────────────────────────────
    'office_int': {
        'ambient':          (0.18, 0.22, 0.28, 1.0),
        'key':              (0.65, 0.72, 0.88, 1.0),
        'keyHpr':           (0, -85, 0),
        'fill':             (0.14, 0.18, 0.24, 1.0),
        'fillHpr':          (180, -60, 0),
        'rim':              (0.10, 0.14, 0.20, 1.0),
        'rimHpr':           (90, -45, 0),
        'shadowCaster':     False,
        'shadowRes':        512,
        'shadowArea':       100,
        'shadowDarknessFloor': 0.15,
        'fogColor':         (0.12, 0.16, 0.24, 1.0),
        'fogNear':          0.0,
        'fogFar':           None,
        'fogExponent':      0.018,
        'skyScale':         (0.56, 0.68, 0.88, 1.0),
        'clearColor':       (0.10, 0.14, 0.22, 1.0),
        'sunUV':            (0.50, 0.50),
        'rayColor':         (0.70, 0.82, 1.00, 1.0),
        'rayIntensity':     0.03,
        'bloomIntensity':   0.12,
        'bloomThreshold':   0.65,
        'exposure':         1.15,
        'hasWater':         False,
        'dayNightEnabled':  False,
        'cloudCoverage':    0.0,
        'cloudSpeed':       0.0,
        'cloudSharpness':   0.0,
        'turbidity':        1.0,
        'starBrightness':   0.0,
        'moonEnabled':      False,
    },

    # ── Bossbot HQ (exterior) ─────────────────────────────────────────────────
    'bossbot_hq': {
        'ambient':          (0.03, 0.02, 0.02, 1.0),
        'key':              (0.12, 0.07, 0.03, 1.0),
        'keyHpr':           (90, -8, 0),
        'fill':             (0.04, 0.03, 0.06, 1.0),
        'fillHpr':          (-90, -15, 0),
        'rim':              (0.06, 0.06, 0.11, 1.0),
        'rimHpr':           (270, -20, 0),
        'shadowCaster':     False,
        'shadowRes':        512,
        'shadowArea':       180,
        'shadowDarknessFloor': 0.02,
        'fogColor':         (0.02, 0.01, 0.01, 1.0),
        'fogNear':          0.0,
        'fogFar':           None,
        'fogExponent':      0.024,
        'skyScale':         (0.20, 0.14, 0.10, 1.0),
        'clearColor':       (0.01, 0.01, 0.02, 1.0),
        'sunUV':            (0.50, 0.50),
        'rayColor':         (0.40, 0.22, 0.10, 1.0),
        'rayIntensity':     0.00,
        'bloomIntensity':   0.00,
        'bloomThreshold':   0.99,
        'exposure':         1.50,
        'hasWater':         False,
        'dayNightEnabled':  False,
        'cloudCoverage':    0.99,
        'cloudSpeed':       0.10,
        'cloudSharpness':   0.05,
        'turbidity':        8.0,
        'starBrightness':   0.0,
        'moonEnabled':      False,
    },

    # ── Bossbot Country Club interior ─────────────────────────────────────────
    'bossbot_cc': {
        'ambient':          (0.10, 0.06, 0.04, 1.0),
        'key':              (0.50, 0.38, 0.22, 1.0),
        'keyHpr':           (90, -60, 0),
        'fill':             (0.08, 0.05, 0.03, 1.0),
        'fillHpr':          (-80, -35, 0),
        'rim':              (0.18, 0.12, 0.06, 1.0),
        'rimHpr':           (88, -55, 0),
        'shadowCaster':     False,
        'shadowRes':        512,
        'shadowArea':       100,
        'shadowDarknessFloor': 0.08,
        'fogColor':         (0.08, 0.04, 0.02, 1.0),
        'fogNear':          0.0,
        'fogFar':           None,
        'fogExponent':      0.018,
        'skyScale':         (0.40, 0.28, 0.16, 1.0),
        'clearColor':       (0.05, 0.03, 0.01, 1.0),
        'sunUV':            (0.50, 0.50),
        'rayColor':         (0.80, 0.55, 0.25, 1.0),
        'rayIntensity':     0.06,
        'bloomIntensity':   0.14,
        'bloomThreshold':   0.60,
        'exposure':         1.35,
        'hasWater':         False,
        'dayNightEnabled':  False,
        'cloudCoverage':    0.0,
        'cloudSpeed':       0.0,
        'cloudSharpness':   0.0,
        'turbidity':        1.0,
        'starBrightness':   0.0,
        'moonEnabled':      False,
    },

    # ── Generic fallbacks ─────────────────────────────────────────────────────
    'playground': {
        'ambient':          (0.28, 0.32, 0.44, 1.0),
        'key':              (0.98, 0.92, 0.76, 1.0),
        'keyHpr':           (118, -52, 0),
        'fill':             (0.18, 0.25, 0.38, 1.0),
        'fillHpr':          (-48, -42, 0),
        'rim':              None,
        'shadowCaster':     True,
        'shadowRes':        2048,
        'shadowArea':       180,
        'shadowResScale':   0.90,
        'shadowAreaScale':  1.20,
        'shadowFollowDist': 240.0,
        'shadowDarknessFloor': 0.18,
        'fogColor':         (0.65, 0.78, 0.94, 1.0),
        'fogNear':          100.0,
        'fogFar':           460.0,
        'fogExponent':      None,
        'skyScale':         (1.00, 1.00, 1.00, 1.0),
        'clearColor':       (0.42, 0.62, 0.84, 1.0),
        'sunUV':            (0.62, 0.76),
        'rayColor':         (1.00, 0.95, 0.74, 1.0),
        'rayIntensity':     0.28,
        'bloomIntensity':   0.28,
        'bloomThreshold':   0.64,
        'exposure':         1.00,
        'hasWater':         False,
        'dayNightEnabled':  True,
        'cloudCoverage':    0.35,
        'cloudSpeed':       0.65,
        'cloudSharpness':   0.50,
        'turbidity':        2.4,
        'starBrightness':   0.0,
        'moonEnabled':      False,
    },
    'estate': {
        'ambient':          (0.30, 0.30, 0.40, 1.0),
        'key':              (1.00, 0.94, 0.80, 1.0),
        'keyHpr':           (105, -48, 0),
        'fill':             (0.22, 0.28, 0.38, 1.0),
        'fillHpr':          (-55, -38, 0),
        'rim':              None,
        'shadowCaster':     True,
        'shadowRes':        2048,
        'shadowArea':       180,
        'shadowResScale':   0.90,
        'shadowAreaScale':  1.20,
        'shadowFollowDist': 240.0,
        'shadowDarknessFloor': 0.20,
        'fogColor':         (0.68, 0.80, 0.94, 1.0),
        'fogNear':          100.0,
        'fogFar':           470.0,
        'fogExponent':      None,
        'skyScale':         (1.00, 1.00, 1.00, 1.0),
        'clearColor':       (0.44, 0.64, 0.86, 1.0),
        'sunUV':            (0.58, 0.74),
        'rayColor':         (1.00, 0.95, 0.80, 1.0),
        'rayIntensity':     0.22,
        'bloomIntensity':   0.22,
        'bloomThreshold':   0.66,
        'exposure':         1.00,
        'hasWater':         True,
        'waterColor':       (0.26, 0.46, 0.64, 0.86),
        'waterReflQuality': 'low',
        'dayNightEnabled':  True,
        'cloudCoverage':    0.38,
        'cloudSpeed':       0.60,
        'cloudSharpness':   0.55,
        'turbidity':        2.2,
        'starBrightness':   0.0,
        'moonEnabled':      False,
    },
    'cog': {
        'ambient':          (0.32, 0.34, 0.40, 1.0),
        'key':              (0.82, 0.84, 0.92, 1.0),
        'keyHpr':           (90,  -45, 0),
        'fill':             (0.16, 0.20, 0.28, 1.0),
        'fillHpr':          (-75, -30, 0),
        'rim':              None,
        'shadowCaster':     False,
        'shadowRes':        512,
        'shadowArea':       180,
        'shadowDarknessFloor': 0.18,
        'fogColor':         (0.40, 0.42, 0.50, 1.0),
        'fogNear':          80.0,
        'fogFar':           360.0,
        'fogExponent':      None,
        'skyScale':         (0.82, 0.84, 0.90, 1.0),
        'clearColor':       (0.32, 0.36, 0.46, 1.0),
        'sunUV':            (0.50, 0.70),
        'rayColor':         (0.88, 0.90, 1.00, 1.0),
        'rayIntensity':     0.12,
        'bloomIntensity':   0.10,
        'bloomThreshold':   0.70,
        'exposure':         1.00,
        'hasWater':         False,
        'dayNightEnabled':  False,
        'cloudCoverage':    0.75,
        'cloudSpeed':       0.50,
        'cloudSharpness':   0.20,
        'turbidity':        6.0,
        'starBrightness':   0.0,
        'moonEnabled':      False,
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# Day / Night keyframe tables (unchanged from previous version)
# ─────────────────────────────────────────────────────────────────────────────
_DAY_NIGHT_KEYFRAMES: dict[str, list[tuple]] = {
    'tt': [
        (0.0,  {'ambient': (0.04,0.06,0.14,1), 'key': (0.13,0.16,0.34,1),
                'keyHpr': (225,-38,0), 'fill': (0.03,0.04,0.10,1),
                'rim': (0.18,0.22,0.48,1), 'rimHpr': (222,-35,0),
                'fogColor': (0.04,0.06,0.14,1), 'fogNear': 20.0, 'fogFar': 290.0,
                'clearColor': (0.03,0.05,0.12,1), 'skyScale': (0.40,0.45,0.70,1),
                'rayColor': (0.58,0.70,1.00,1), 'rayIntensity': 0.20,
                'bloomIntensity': 0.14, 'shadowCaster': False,
                'starBrightness': 0.88, 'moonEnabled': True, 'moonDir': (180,-52,0),
                'exposure': 1.35}),
        (5.5,  {'ambient': (0.08,0.08,0.16,1), 'key': (0.22,0.18,0.36,1),
                'keyHpr': (80,-5,0), 'fill': (0.06,0.06,0.14,1),
                'rim': (0.20,0.16,0.38,1), 'rimHpr': (82,-4,0),
                'fogColor': (0.10,0.12,0.28,1), 'fogNear': 40.0, 'fogFar': 330.0,
                'clearColor': (0.08,0.10,0.24,1), 'skyScale': (0.50,0.52,0.78,1),
                'rayColor': (0.70,0.62,0.90,1), 'rayIntensity': 0.10,
                'bloomIntensity': 0.12, 'shadowCaster': False,
                'starBrightness': 0.28, 'moonEnabled': True, 'moonDir': (265,-38,0),
                'exposure': 1.20}),
        (6.5,  {'ambient': (0.22,0.16,0.18,1), 'key': (0.90,0.48,0.28,1),
                'keyHpr': (90,-10,0), 'fill': (0.18,0.14,0.28,1),
                'rim': (0.72,0.36,0.18,1), 'rimHpr': (88,-8,0),
                'fogColor': (0.82,0.52,0.32,1), 'fogNear': 60.0, 'fogFar': 390.0,
                'clearColor': (0.72,0.40,0.22,1), 'skyScale': (1.20,0.80,0.58,1),
                'rayColor': (1.00,0.62,0.30,1), 'rayIntensity': 0.52,
                'bloomIntensity': 0.46, 'shadowCaster': True,
                'starBrightness': 0.0, 'exposure': 1.05}),
        (9.0,  {'ambient': (0.20,0.24,0.36,1), 'key': (1.10,0.96,0.74,1),
                'keyHpr': (120,-36,0), 'fill': (0.20,0.28,0.44,1), 'rim': None,
                'fogColor': (0.68,0.78,0.92,1), 'fogNear': 90.0, 'fogFar': 450.0,
                'clearColor': (0.48,0.66,0.88,1), 'skyScale': (1.04,1.00,0.92,1),
                'rayColor': (1.00,0.90,0.64,1), 'rayIntensity': 0.30,
                'bloomIntensity': 0.30, 'shadowCaster': True,
                'starBrightness': 0.0, 'exposure': 1.00}),
        (12.0, {'ambient': (0.24,0.30,0.46,1), 'key': (1.28,1.18,0.98,1),
                'keyHpr': (180,-86,0), 'fill': (0.24,0.34,0.52,1), 'rim': None,
                'fogColor': (0.74,0.83,0.95,1), 'fogNear': 100.0, 'fogFar': 510.0,
                'clearColor': (0.52,0.72,0.96,1), 'skyScale': (1.00,1.00,0.96,1),
                'rayColor': (1.00,0.96,0.80,1), 'rayIntensity': 0.28,
                'bloomIntensity': 0.36, 'shadowCaster': True,
                'starBrightness': 0.0, 'exposure': 1.00}),
        (15.0, {'ambient': (0.22,0.27,0.40,1), 'key': (1.22,1.08,0.78,1),
                'keyHpr': (135,-42,0), 'fill': (0.24,0.32,0.50,1), 'rim': None,
                'fogColor': (0.72,0.80,0.92,1), 'fogNear': 80.0, 'fogFar': 440.0,
                'clearColor': (0.50,0.68,0.90,1), 'skyScale': (1.04,1.01,0.91,1),
                'rayColor': (1.00,0.94,0.68,1), 'rayIntensity': 0.38,
                'bloomIntensity': 0.32, 'shadowCaster': True,
                'starBrightness': 0.0, 'exposure': 1.00}),
        (17.5, {'ambient': (0.32,0.24,0.26,1), 'key': (1.20,0.72,0.32,1),
                'keyHpr': (230,-22,0), 'fill': (0.22,0.18,0.36,1),
                'rim': (0.82,0.40,0.16,1), 'rimHpr': (228,-18,0),
                'fogColor': (0.86,0.58,0.34,1), 'fogNear': 50.0, 'fogFar': 370.0,
                'clearColor': (0.80,0.50,0.24,1), 'skyScale': (1.22,0.84,0.58,1),
                'rayColor': (1.00,0.64,0.26,1), 'rayIntensity': 0.64,
                'bloomIntensity': 0.56, 'shadowCaster': True,
                'starBrightness': 0.0, 'exposure': 1.02}),
        (19.0, {'ambient': (0.22,0.14,0.28,1), 'key': (0.62,0.30,0.42,1),
                'keyHpr': (262,-8,0), 'fill': (0.16,0.10,0.28,1),
                'rim': (0.50,0.22,0.36,1), 'rimHpr': (260,-5,0),
                'fogColor': (0.40,0.20,0.36,1), 'fogNear': 20.0, 'fogFar': 270.0,
                'clearColor': (0.30,0.14,0.32,1), 'skyScale': (0.90,0.58,0.80,1),
                'rayColor': (0.90,0.46,0.72,1), 'rayIntensity': 0.36,
                'bloomIntensity': 0.42, 'shadowCaster': False,
                'starBrightness': 0.12, 'moonEnabled': False, 'exposure': 1.15}),
        (21.0, {'ambient': (0.05,0.07,0.16,1), 'key': (0.14,0.18,0.38,1),
                'keyHpr': (225,-40,0), 'fill': (0.03,0.04,0.10,1),
                'rim': (0.20,0.24,0.52,1), 'rimHpr': (222,-38,0),
                'fogColor': (0.04,0.06,0.14,1), 'fogNear': 20.0, 'fogFar': 285.0,
                'clearColor': (0.03,0.04,0.11,1), 'skyScale': (0.38,0.42,0.68,1),
                'rayColor': (0.56,0.68,1.00,1), 'rayIntensity': 0.22,
                'bloomIntensity': 0.15, 'shadowCaster': False,
                'starBrightness': 0.84, 'moonEnabled': True, 'moonDir': (90,-55,0),
                'exposure': 1.32}),
        (24.0, None),
    ],
    'dd': [
        (0.0,  {'ambient': (0.38,0.40,0.46,1), 'key': (0.42,0.46,0.52,1),
                'keyHpr': (0,-70,0), 'fogColor': (0.30,0.34,0.42,1),
                'fogExponent': 0.014, 'clearColor': (0.28,0.32,0.40,1),
                'skyScale': (0.58,0.62,0.70,1), 'bloomIntensity': 0.10}),
        (7.0,  {'ambient': (0.52,0.54,0.58,1), 'key': (0.60,0.64,0.70,1),
                'keyHpr': (0,-75,0), 'fogColor': (0.60,0.64,0.70,1),
                'fogExponent': 0.011, 'clearColor': (0.58,0.62,0.70,1),
                'skyScale': (0.78,0.82,0.88,1), 'bloomIntensity': 0.15}),
        (13.0, {'ambient': (0.62,0.65,0.70,1), 'key': (0.72,0.76,0.82,1),
                'keyHpr': (0,-80,0), 'fogColor': (0.72,0.76,0.82,1),
                'fogExponent': 0.010, 'clearColor': (0.70,0.74,0.80,1),
                'skyScale': (0.84,0.87,0.92,1), 'bloomIntensity': 0.20}),
        (20.0, {'ambient': (0.44,0.46,0.52,1), 'key': (0.50,0.52,0.60,1),
                'keyHpr': (270,-72,0), 'fogColor': (0.42,0.46,0.54,1),
                'fogExponent': 0.013, 'clearColor': (0.40,0.44,0.52,1),
                'skyScale': (0.70,0.72,0.80,1), 'bloomIntensity': 0.12}),
        (24.0, None),
    ],
    'dg': [
        (0.0,  {'ambient': (0.04,0.07,0.12,1), 'key': (0.16,0.20,0.40,1),
                'keyHpr': (225,-38,0), 'fill': (0.03,0.05,0.09,1),
                'rim': (0.14,0.18,0.36,1), 'rimHpr': (222,-34,0),
                'fogColor': (0.05,0.08,0.18,1), 'fogNear': 10.0, 'fogFar': 280.0,
                'clearColor': (0.04,0.06,0.14,1), 'skyScale': (0.34,0.42,0.68,1),
                'rayColor': (0.56,0.70,1.00,1), 'rayIntensity': 0.18,
                'bloomIntensity': 0.14, 'shadowCaster': False,
                'starBrightness': 0.76, 'moonEnabled': True, 'moonDir': (180,-55,0)}),
        (6.0,  {'ambient': (0.20,0.16,0.18,1), 'key': (0.86,0.46,0.22,1),
                'keyHpr': (90,-8,0), 'fill': (0.16,0.12,0.26,1),
                'rim': (0.68,0.34,0.14,1), 'rimHpr': (88,-6,0),
                'fogColor': (0.80,0.50,0.28,1), 'fogNear': 50.0, 'fogFar': 360.0,
                'clearColor': (0.70,0.38,0.18,1), 'skyScale': (1.18,0.76,0.52,1),
                'rayColor': (1.00,0.60,0.28,1), 'rayIntensity': 0.50,
                'bloomIntensity': 0.44, 'shadowCaster': True,
                'starBrightness': 0.0, 'moonEnabled': False}),
        (11.0, {'ambient': (0.18,0.25,0.42,1), 'key': (1.20,1.10,0.90,1),
                'keyHpr': (180,-82,0), 'fill': (0.22,0.32,0.52,1),
                'rim': (0.10,0.16,0.30,1), 'rimHpr': (0,55,0),
                'fogColor': (0.62,0.80,1.00,1), 'fogNear': 120.0, 'fogFar': 540.0,
                'clearColor': (0.36,0.62,1.00,1), 'skyScale': (0.88,0.96,1.14,1),
                'rayColor': (1.00,1.00,0.88,1), 'rayIntensity': 0.58,
                'bloomIntensity': 0.44, 'shadowCaster': True,
                'starBrightness': 0.0, 'moonEnabled': False}),
        (17.0, {'ambient': (0.28,0.22,0.24,1), 'key': (1.10,0.70,0.30,1),
                'keyHpr': (235,-20,0), 'fill': (0.20,0.16,0.32,1),
                'rim': (0.78,0.36,0.14,1), 'rimHpr': (232,-16,0),
                'fogColor': (0.84,0.56,0.32,1), 'fogNear': 40.0, 'fogFar': 360.0,
                'clearColor': (0.76,0.46,0.20,1), 'skyScale': (1.18,0.82,0.54,1),
                'rayColor': (1.00,0.62,0.24,1), 'rayIntensity': 0.60,
                'bloomIntensity': 0.52, 'shadowCaster': True,
                'starBrightness': 0.0, 'moonEnabled': False}),
        (20.0, {'ambient': (0.06,0.08,0.18,1), 'key': (0.18,0.22,0.44,1),
                'keyHpr': (225,-40,0), 'fill': (0.04,0.06,0.12,1),
                'rim': (0.22,0.26,0.52,1), 'rimHpr': (222,-38,0),
                'fogColor': (0.05,0.08,0.18,1), 'fogNear': 10.0, 'fogFar': 280.0,
                'clearColor': (0.04,0.06,0.14,1), 'skyScale': (0.36,0.44,0.70,1),
                'rayColor': (0.56,0.70,1.00,1), 'rayIntensity': 0.20,
                'bloomIntensity': 0.16, 'shadowCaster': False,
                'starBrightness': 0.42, 'moonEnabled': True, 'moonDir': (120,-48,0)}),
        (24.0, None),
    ],
    'mm': [
        (0.0,  {'ambient': (0.24,0.10,0.22,1), 'key': (0.26,0.14,0.36,1),
                'keyHpr': (270,-5,0), 'fill': (0.12,0.06,0.22,1),
                'rim': (0.30,0.14,0.28,1), 'rimHpr': (268,-3,0),
                'fogColor': (0.22,0.10,0.28,1), 'fogNear': 5.0, 'fogFar': 200.0,
                'clearColor': (0.16,0.08,0.24,1), 'skyScale': (0.60,0.28,0.56,1),
                'rayColor': (0.72,0.32,0.80,1), 'rayIntensity': 0.24,
                'bloomIntensity': 0.28, 'shadowCaster': False,
                'starBrightness': 0.58, 'moonEnabled': True, 'moonDir': (220,-42,0)}),
        (6.0,  {'ambient': (0.36,0.22,0.16,1), 'key': (0.80,0.38,0.10,1),
                'keyHpr': (90,-10,0), 'fill': (0.18,0.12,0.26,1),
                'rim': (0.60,0.28,0.10,1), 'rimHpr': (88,-8,0),
                'fogColor': (0.72,0.36,0.14,1), 'fogNear': 10.0, 'fogFar': 290.0,
                'clearColor': (0.66,0.32,0.12,1), 'skyScale': (1.14,0.60,0.34,1),
                'rayColor': (1.00,0.52,0.18,1), 'rayIntensity': 0.60,
                'bloomIntensity': 0.52, 'shadowCaster': True,
                'starBrightness': 0.0, 'moonEnabled': False}),
        (14.0, {'ambient': (0.42,0.28,0.30,1), 'key': (1.10,0.50,0.18,1),
                'keyHpr': (260,-14,0), 'fill': (0.22,0.18,0.40,1),
                'rim': (0.90,0.40,0.12,1), 'rimHpr': (258,-8,0),
                'fogColor': (0.80,0.44,0.20,1), 'fogNear': 10.0, 'fogFar': 330.0,
                'clearColor': (0.88,0.46,0.18,1), 'skyScale': (1.30,0.72,0.48,1),
                'rayColor': (1.00,0.58,0.22,1), 'rayIntensity': 0.70,
                'bloomIntensity': 0.56, 'shadowCaster': True,
                'starBrightness': 0.0, 'moonEnabled': False}),
        (20.0, {'ambient': (0.28,0.12,0.32,1), 'key': (0.52,0.22,0.50,1),
                'keyHpr': (270,-6,0), 'fill': (0.14,0.08,0.28,1),
                'rim': (0.44,0.18,0.42,1), 'rimHpr': (268,-4,0),
                'fogColor': (0.34,0.14,0.38,1), 'fogNear': 5.0, 'fogFar': 220.0,
                'clearColor': (0.26,0.10,0.34,1), 'skyScale': (0.80,0.40,0.80,1),
                'rayColor': (0.80,0.38,0.90,1), 'rayIntensity': 0.32,
                'bloomIntensity': 0.38, 'shadowCaster': False,
                'starBrightness': 0.24, 'moonEnabled': True, 'moonDir': (240,-36,0)}),
        (24.0, None),
    ],
    'br': [
        (0.0,  {'ambient': (0.28,0.36,0.54,1), 'key': (0.40,0.50,0.70,1),
                'keyHpr': (180,-10,0), 'fogColor': (0.40,0.52,0.70,1),
                'fogExponent': 0.020, 'clearColor': (0.36,0.46,0.66,1),
                'skyScale': (0.60,0.72,0.94,1), 'bloomIntensity': 0.12}),
        (12.0, {'ambient': (0.44,0.52,0.70,1), 'key': (0.64,0.74,0.92,1),
                'keyHpr': (180,-18,0), 'fogColor': (0.68,0.78,0.94,1),
                'fogExponent': 0.016, 'clearColor': (0.62,0.74,0.92,1),
                'skyScale': (0.78,0.88,1.08,1), 'bloomIntensity': 0.22}),
        (18.0, {'ambient': (0.32,0.38,0.58,1), 'key': (0.48,0.56,0.78,1),
                'keyHpr': (270,-12,0), 'fogColor': (0.50,0.60,0.80,1),
                'fogExponent': 0.018, 'clearColor': (0.46,0.58,0.78,1),
                'skyScale': (0.68,0.80,1.02,1), 'bloomIntensity': 0.16}),
        (24.0, None),
    ],
    'dl': [
        (0.0,  {'ambient': (0.06,0.08,0.16,1), 'key': (0.40,0.46,0.68,1),
                'keyHpr': (225,-55,0), 'fill': (0.04,0.06,0.12,1),
                'rim': (0.30,0.36,0.58,1), 'rimHpr': (220,-50,0),
                'fogColor': (0.05,0.07,0.14,1), 'fogExponent': 0.006,
                'clearColor': (0.03,0.04,0.10,1), 'skyScale': (0.42,0.48,0.74,1),
                'rayColor': (0.58,0.70,1.00,1), 'rayIntensity': 0.32,
                'bloomIntensity': 0.20, 'shadowCaster': True}),
        (3.5,  {'ambient': (0.04,0.05,0.12,1), 'key': (0.20,0.24,0.48,1),
                'keyHpr': (270,-20,0), 'fill': (0.02,0.03,0.08,1),
                'rim': (0.16,0.20,0.44,1), 'rimHpr': (268,-18,0),
                'fogColor': (0.03,0.04,0.10,1), 'fogExponent': 0.008,
                'clearColor': (0.02,0.02,0.07,1), 'skyScale': (0.28,0.34,0.60,1),
                'rayColor': (0.46,0.58,0.90,1), 'rayIntensity': 0.16,
                'bloomIntensity': 0.12, 'shadowCaster': False}),
        (5.0,  {'ambient': (0.08,0.06,0.16,1), 'key': (0.24,0.18,0.44,1),
                'keyHpr': (80,-6,0), 'fill': (0.06,0.04,0.12,1),
                'rim': (0.20,0.14,0.40,1), 'rimHpr': (78,-4,0),
                'fogColor': (0.08,0.06,0.18,1), 'fogExponent': 0.007,
                'clearColor': (0.06,0.05,0.16,1), 'skyScale': (0.40,0.36,0.70,1),
                'rayColor': (0.62,0.52,0.90,1), 'rayIntensity': 0.14,
                'bloomIntensity': 0.14, 'shadowCaster': False}),
        (12.0, {'ambient': (0.10,0.12,0.22,1), 'key': (0.38,0.42,0.64,1),
                'keyHpr': (180,-50,0), 'fill': (0.06,0.08,0.16,1),
                'rim': (0.28,0.32,0.56,1), 'rimHpr': (178,-46,0),
                'fogColor': (0.07,0.09,0.18,1), 'fogExponent': 0.006,
                'clearColor': (0.06,0.07,0.16,1), 'skyScale': (0.48,0.54,0.80,1),
                'rayColor': (0.56,0.68,1.00,1), 'rayIntensity': 0.28,
                'bloomIntensity': 0.18, 'shadowCaster': True}),
        (20.0, {'ambient': (0.06,0.08,0.16,1), 'key': (0.38,0.44,0.66,1),
                'keyHpr': (135,-42,0), 'fill': (0.04,0.06,0.12,1),
                'rim': (0.28,0.34,0.56,1), 'rimHpr': (132,-38,0),
                'fogColor': (0.05,0.07,0.14,1), 'fogExponent': 0.006,
                'clearColor': (0.03,0.04,0.10,1), 'skyScale': (0.42,0.48,0.74,1),
                'rayColor': (0.58,0.70,1.00,1), 'rayIntensity': 0.30,
                'bloomIntensity': 0.20, 'shadowCaster': True}),
        (24.0, None),
    ],
    'gs': [
        (0.0,  {'ambient': (0.10,0.12,0.20,1), 'key': (0.18,0.20,0.36,1),
                'keyHpr': (225,-32,0), 'fogColor': (0.14,0.16,0.26,1),
                'fogNear': 20.0, 'fogFar': 280.0, 'clearColor': (0.12,0.14,0.22,1),
                'bloomIntensity': 0.12, 'shadowCaster': False,
                'starBrightness': 0.78, 'moonEnabled': True, 'moonDir': (0,-60,0)}),
        (7.0,  {'ambient': (0.28,0.26,0.24,1), 'key': (0.88,0.58,0.26,1),
                'keyHpr': (90,-12,0), 'fogColor': (0.72,0.60,0.42,1),
                'fogNear': 50.0, 'fogFar': 320.0, 'clearColor': (0.62,0.50,0.34,1),
                'bloomIntensity': 0.36, 'shadowCaster': True,
                'starBrightness': 0.0, 'moonEnabled': False}),
        (11.0, {'ambient': (0.30,0.32,0.40,1), 'key': (1.10,1.00,0.82,1),
                'keyHpr': (130,-48,0), 'fogColor': (0.78,0.76,0.68,1),
                'fogNear': 60.0, 'fogFar': 380.0, 'clearColor': (0.56,0.64,0.72,1),
                'bloomIntensity': 0.26, 'shadowCaster': True,
                'starBrightness': 0.0, 'moonEnabled': False}),
        (18.0, {'ambient': (0.28,0.22,0.18,1), 'key': (1.00,0.58,0.22,1),
                'keyHpr': (240,-18,0), 'fogColor': (0.72,0.46,0.24,1),
                'fogNear': 40.0, 'fogFar': 320.0, 'clearColor': (0.66,0.40,0.18,1),
                'bloomIntensity': 0.44, 'shadowCaster': True,
                'starBrightness': 0.0, 'moonEnabled': False}),
        (21.0, {'ambient': (0.10,0.12,0.20,1), 'key': (0.20,0.22,0.40,1),
                'keyHpr': (225,-34,0), 'fogColor': (0.12,0.14,0.24,1),
                'fogNear': 20.0, 'fogFar': 280.0, 'clearColor': (0.10,0.12,0.20,1),
                'bloomIntensity': 0.14, 'shadowCaster': False,
                'starBrightness': 0.68, 'moonEnabled': True, 'moonDir': (60,-56,0)}),
        (24.0, None),
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
# Hood ID + Zone ID → profile key mapping
# ─────────────────────────────────────────────────────────────────────────────

_HOOD_ID_MAP: dict[int, str] | None = None
_ZONE_ID_MAP: dict[int, str]  = {}   # populated lazily


def _buildHoodIdMap() -> dict[int, str]:
    from toontown.toonbase import ToontownGlobals as TG
    m = {
        TG.ToontownCentral:   'tt',
        TG.DonaldsDock:       'dd',
        TG.MinniesMelodyland: 'mm',
        TG.DaisyGardens:      'dg',
        TG.TheBrrrgh:         'br',
        TG.DonaldsDreamland:  'dl',
        TG.GoofySpeedway:     'gs',
        TG.BossbotHQ:         'bossbot_hq',
        TG.SellbotHQ:         'sellbot_hq',
        TG.CashbotHQ:         'cashbot_hq',
        TG.LawbotHQ:          'lawbot_hq',
    }
    for attr in ('MyEstate', 'Estate', 'ToonEstate'):
        val = getattr(TG, attr, None)
        if val is not None:
            m[val] = 'estate'
    return m


def _buildZoneIdMap() -> dict[int, str]:
    """Map individual zone IDs to specific sub-profiles."""
    from toontown.toonbase import ToontownGlobals as TG

    def _zr(tg_attr: str) -> int | None:
        return getattr(TG, tg_attr, None)

    z: dict[int, str] = {}

    # TT streets
    for attr in ('SillyStreet', 'LoopyLane', 'PunchlinePlace'):
        v = _zr(attr)
        if v: z[v] = 'tt_street'

    # DD streets
    for attr in ('BarnacleBoulevard', 'SeaweedStreet', 'LighthouseLane'):
        v = _zr(attr)
        if v: z[v] = 'dd_street'

    # BR streets
    for attr in ('SleetStreet', 'WalrusWay', 'PolarPlace'):
        v = _zr(attr)
        if v: z[v] = 'br_street'

    # MM streets
    for attr in ('AltoAvenue', 'BaritoneBoulevard', 'TenorTerrace'):
        v = _zr(attr)
        if v: z[v] = 'mm_street'

    # DG streets
    for attr in ('ElmStreet', 'MapleStreet', 'OakStreet'):
        v = _zr(attr)
        if v: z[v] = 'dg_street'

    # DDL streets
    for attr in ('LullabyLane', 'PajamaPlace'):
        v = _zr(attr)
        if v: z[v] = 'dl_street'

    # Interiors
    for attr in ('SellbotFactoryInt', 'SellbotLegFactoryInt',
                 'LawbotFactoryInt'):
        v = _zr(attr)
        if v: z[v] = 'factory_int'

    for attr in ('CashbotMintIntA', 'CashbotMintIntB', 'CashbotMintIntC'):
        v = _zr(attr)
        if v: z[v] = 'mint_int'

    for attr in ('LawbotOfficeInt',):
        v = _zr(attr)
        if v: z[v] = 'office_int'

    for attr in ('BossbotCountryClubIntA', 'BossbotCountryClubIntB',
                 'BossbotCountryClubIntC'):
        v = _zr(attr)
        if v: z[v] = 'bossbot_cc'

    for attr in ('GolfZone',):
        v = _zr(attr)
        if v: z[v] = 'golf_course'

    return z


def _resolveStyle(style: str, hoodId: int | None,
                  zoneId: int | None = None) -> str:
    global _HOOD_ID_MAP, _ZONE_ID_MAP

    # Zone ID takes priority (most specific).
    if zoneId is not None:
        if not _ZONE_ID_MAP:
            try:
                _ZONE_ID_MAP = _buildZoneIdMap()
            except Exception:
                pass
        res = _ZONE_ID_MAP.get(zoneId)
        if res and res in _ZONE_PROFILES:
            return res

    # Hood ID next.
    if hoodId is not None:
        if _HOOD_ID_MAP is None:
            try:
                _HOOD_ID_MAP = _buildHoodIdMap()
            except Exception:
                _HOOD_ID_MAP = {}
        res = _HOOD_ID_MAP.get(hoodId)
        if res and res in _ZONE_PROFILES:
            return res

    return style if style in _ZONE_PROFILES else 'playground'


# ─────────────────────────────────────────────────────────────────────────────
# Module-level shared state
# ─────────────────────────────────────────────────────────────────────────────

_refCount            = 0
_activeStyle         = 'playground'

# Light rig
_lightRig: NodePath | None = None
_renderLights: list[NodePath] = []
_keyLightNp: NodePath | None  = None
_keyCastsShadows               = False
_shadowFocusPos: Vec3 | None  = None
_shadowSceneRadius             = 180.0
_shadowMapRes                  = 1024
_shadowFilmArea                = 180.0
_shadowFollowDist              = 220.0
_prevShadowCasterState: bool | None = None

# Fog
_fogNode: Fog | None = None

# Sky / window
_skyWasDimmed    = False
_prevClearColor: tuple | None = None

# Post-process: CommonFilters bloom + render2dp sun-ray overlay (no scene RTT compositor)
_godRaysCard: NodePath | None = None
_godRaysShader: Shader | None = None
_bloomFilters: Any = None

# Water reflections
_waterSetups: list[dict] = []
_waterShader: Shader | None = None

# Procedural sky
_proceduralSky: Any = None  # ProceduralSky instance

# Day / night
_timeOfDay         = 12.0
_dayNightSpeed     = 1.0 / 60.0
_dayNightAccum     = 0.0
_godRaysTime       = 0.0

_godRaysTaskName   = 'outdoorLightingTask'

# Street lamp / lantern point lights (active at night)
_lampLights: list[NodePath]   = []   # PointLight NodePaths attached to _lightRig
_lampGeomNps: list[NodePath]  = []   # Cached lamp post positions scanned from geometry
_lampLightsActive: bool        = False

# Lamp node name keywords – any node whose name contains one of these is treated as a light source
_LAMP_KEYWORDS: tuple = (
    'lamp', 'lantern', 'streetlight', 'lightpole', 'lamp_post', 'lamppost',
    'prop_lamp', 'prop_lantern', 'light_pole', 'gazebo_lamp', 'post_lamp',
    'street_lamp', 'streetlamp', 'gas_lamp', 'gaslight', 'torch',
    'light_fixture', 'park_lamp', 'lampshade', 'bulb',
)
_LAMP_LIGHT_LIMIT = 60   # max point lights to create (performance guard)

_SHADOW_CAM_MASK   = BitMask32.bit(5)

_SHADER_DIR        = os.path.join(os.path.dirname(__file__), '..', 'shaders')
_LEGACY_VERT       = os.path.join(_SHADER_DIR, 'sunrays.vert.glsl')
_LEGACY_FRAG       = os.path.join(_SHADER_DIR, 'sunrays.frag.glsl')
_WATER_VERT        = os.path.join(_SHADER_DIR, 'water.vert.glsl')
_WATER_FRAG        = os.path.join(_SHADER_DIR, 'water.frag.glsl')

_WATER_PATTERNS = (
    'water', 'pond', 'ocean', 'sea', 'lake', 'fountain',
    'puddle', 'river', 'stream', 'brook', 'lagoon', 'tide',
)

_rigRebuildPending: dict | None = None

# ─────────────────────────────────────────────────────────────────────────────
# Settings helpers
# ─────────────────────────────────────────────────────────────────────────────

def _wantFx() -> bool:
    if _OUTDOOR_SHADER_BISECT_LEVEL < 1:
        return False
    try:
        val = base.settings.getSetting('want-modern-outdoor-lighting', None)
        if val is not None:
            return bool(val)
    except Exception:
        pass
    return ConfigVariableBool('want-modern-outdoor-lighting', True).value


def _settingsBool(key: str, default: bool) -> bool:
    try:
        return bool(base.settings.getSetting(key, default))
    except Exception:
        return default


def _settingsFloat(key: str, default: float) -> float:
    try:
        return float(base.settings.getSetting(key, default))
    except Exception:
        return default


def _settingsStr(key: str, default: str) -> str:
    try:
        v = base.settings.getSetting(key, default)
        return str(v) if v is not None else default
    except Exception:
        return default


def _wantDayNight() -> bool:
    try:
        val = base.settings.getSetting('want-day-night-cycle', None)
        if val is not None:
            return bool(val)
    except Exception:
        pass
    return ConfigVariableBool('want-day-night-cycle', False).value


def _wantBloom() -> bool:
    return _settingsBool('lighting-bloom-enabled', True)


def _wantWater() -> bool:
    return _settingsBool('want-water-reflections', True)


def _wantDynamicShadows() -> bool:
    return _settingsBool('dynamic-shadows', True)


def _wantSpecularHighlights() -> bool:
    return _settingsBool('lighting-specular-enabled', True)


def _wantTonemap() -> bool:
    return _settingsBool('lighting-tonemap-enabled', True)


def _wantProceduralSky() -> bool:
    if _OUTDOOR_SHADER_BISECT_LEVEL < 1:
        return False
    return _settingsBool('want-procedural-sky', True)


def _wantVignette() -> bool:
    return _settingsBool('lighting-vignette-enabled', False)


def _intensityScale() -> float:
    return max(0.1, min(2.0, _settingsFloat('lighting-intensity', 1.0)))


def _colorTempBias() -> float:
    return max(-1.0, min(1.0, _settingsFloat('lighting-color-temp', 0.0)))


def _dayNightSpeedMultiplier() -> float:
    return max(0.0, _settingsFloat('day-night-speed', 1.0))


def _vignetteStrength() -> float:
    if not _wantVignette():
        return 0.0
    return max(0.0, min(1.0, _settingsFloat('lighting-vignette-strength', 0.25)))


def _shadowQuality() -> str:
    return _settingsStr('shadow-quality', 'high')   # 'off' | 'low' | 'medium' | 'high'


def _cloudQuality() -> str:
    return _settingsStr('sky-cloud-quality', 'high')  # 'off' | 'low' | 'medium' | 'high'


def _fogDensityMult() -> float:
    return max(0.1, min(3.0, _settingsFloat('fog-density-multiplier', 1.0)))


# ─────────────────────────────────────────────────────────────────────────────
# Math / colour helpers
# ─────────────────────────────────────────────────────────────────────────────

def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _lerpF(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _lerpT(a: tuple | None, b: tuple | None, t: float) -> tuple | None:
    if a is None and b is None:
        return None
    if a is None:
        a = tuple(0.0 for _ in b)
    if b is None:
        b = tuple(0.0 for _ in a)
    return tuple(_lerpF(float(ai), float(bi), t) for ai, bi in zip(a, b))


def _applyColorTemp(color: tuple) -> tuple:
    bias = _colorTempBias()
    r, g, b, a = color
    if bias > 0:
        r = min(1.0, r + bias * 0.08)
        b = max(0.0, b - bias * 0.06)
    elif bias < 0:
        b = min(1.0, b - bias * 0.08)
        r = max(0.0, r + bias * 0.06)
    return (r, g, b, a)


def _scaleColor(color: tuple, scale: float) -> tuple:
    return (color[0] * scale, color[1] * scale, color[2] * scale, color[3])


def _scaledShadowRes(spec: dict) -> int:
    q = _shadowQuality()
    if q == 'off':
        return 0
    base_res = int(spec.get('shadowRes', 1024))
    scale = float(spec.get('shadowResScale', 1.0))
    if q == 'low':
        scale *= 0.25
    elif q == 'medium':
        scale *= 0.50
    res = int(round(base_res * _clamp(scale, 0.25, 2.0)))
    res = int(_clamp(res, 512, 4096))
    valid = (512, 1024, 2048, 4096)
    return min(valid, key=lambda v: abs(v - res))


# ─────────────────────────────────────────────────────────────────────────────
# Specular + lighting fix helpers
# ─────────────────────────────────────────────────────────────────────────────

_SPEC_TAG         = 'osl_added_material'
_LIGHTON_TAG      = 'osl_cleared_lightoff'
_SHADOW_HIDE_TAG  = 'osl_hide_from_shadow'


def _applyDefaultSpecularMaterial(np: NodePath) -> None:
    if not _wantSpecularHighlights() or np is None or np.isEmpty():
        return
    try:
        if np.hasMaterial():
            return
    except Exception:
        try:
            if np.getMaterial() is not None:
                return
        except Exception:
            pass
    try:
        if np.getPythonTag(_SPEC_TAG):
            return
    except Exception:
        pass
    try:
        m = Material()
        m.setSpecular(Vec4(0.22, 0.22, 0.22, 1.0))
        m.setShininess(18.0)
        np.setMaterial(m, 1)
        np.setPythonTag(_SPEC_TAG, True)
    except Exception:
        pass


def _clearDefaultSpecularMaterial(np: NodePath) -> None:
    if np is None or np.isEmpty():
        return
    try:
        if not np.getPythonTag(_SPEC_TAG):
            return
    except Exception:
        return
    try:
        np.clearMaterial()
    except Exception:
        pass
    try:
        np.clearPythonTag(_SPEC_TAG)
    except Exception:
        pass


def _forceLightingOnSubtree(root: NodePath) -> None:
    """Clear LightAttrib overrides that disable per-pixel lighting.

    Some geometry has baked vertex colours and explicit "light off" attribs
    that prevent the dynamic sun from reaching them.  Clearing those lets
    the key/fill/rim lights illuminate the full zone.
    """
    if root is None or root.isEmpty():
        return
    try:
        if hasattr(root, 'clearLightOff'):
            root.clearLightOff()
        try:
            root.clearAttrib(LightAttrib.getClassType())
        except Exception:
            pass
    except Exception:
        pass


def _hidePlaneLikeCastersFromShadow(root: NodePath) -> None:
    """Exclude 2D billboard / card geometry from the shadow CAMERA PASS only.

    2D foliage planes, building facades, and billboard sprites should NOT
    cast sun-blocking shadows (they would create giant flat shadow rectangles).
    They still RECEIVE shadows, and they are still lit by the sun.

    We use the dedicated _SHADOW_CAM_MASK so the shadow camera skips them
    while the regular render camera sees them normally.
    """
    if root is None or root.isEmpty():
        return

    try:
        nodes = root.findAllMatches('**/+GeomNode')
        for i in range(nodes.getNumPaths()):
            np = nodes.getPath(i)
            try:
                if np.getPythonTag(_SHADOW_HIDE_TAG):
                    continue
            except Exception:
                pass

            name = np.getName().lower()
            looks_like_card = any(k in name for k in (
                'card', 'billboard', 'plane', 'sprite', 'foliage',
                'leaf', 'treecard', 'tree', 'bush', 'grass', 'facade',
            ))
            try:
                has_billboard = np.hasEffect(BillboardEffect.getClassType())
            except Exception:
                has_billboard = False
            try:
                has_transparency = np.hasAttrib(TransparencyAttrib.getClassType())
            except Exception:
                has_transparency = False

            if looks_like_card or has_billboard or has_transparency:
                try:
                    np.hide(_SHADOW_CAM_MASK)
                    np.setPythonTag(_SHADOW_HIDE_TAG, True)
                except Exception:
                    pass
    except Exception:
        pass

    # Second pass: clear light-off overrides so every geom node IS lit.
    try:
        nodes = root.findAllMatches('**/+GeomNode')
        for i in range(nodes.getNumPaths()):
            np = nodes.getPath(i)
            try:
                if np.getPythonTag(_LIGHTON_TAG):
                    continue
            except Exception:
                pass
            try:
                if hasattr(np, 'clearLightOff'):
                    np.clearLightOff()
                try:
                    np.clearAttrib(LightAttrib.getClassType())
                except Exception:
                    pass
                np.setPythonTag(_LIGHTON_TAG, True)
            except Exception:
                pass
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Street lamp / lantern night lights
# ─────────────────────────────────────────────────────────────────────────────

def _scanForLampNodes(geom) -> list[NodePath]:
    """Walk scene geometry and collect lamp/lantern NodePaths for night lights."""
    if geom is None or geom.isEmpty():
        return []
    results: list[NodePath] = []
    try:
        nodes = geom.findAllMatches('**/*')
        for i in range(nodes.getNumPaths()):
            np = nodes.getPath(i)
            name = np.getName().lower()
            if any(k in name for k in _LAMP_KEYWORDS):
                results.append(np)
            if len(results) >= _LAMP_LIGHT_LIMIT:
                break
    except Exception:
        pass
    return results


def _enableLampLights(style: str) -> None:
    """Create PointLights at all cached lamp positions (call at dusk/night)."""
    global _lampLights, _lampLightsActive
    if _lampLightsActive or not _lampGeomNps:
        return
    if not _lightRig or _lightRig.isEmpty():
        return

    # Zone-specific lamp colour (warm for regular areas, cool-blue for DL / midnight)
    nightZones = ('dl', 'dl_street', 'sellbot_hq', 'cashbot_hq', 'lawbot_hq',
                  'bossbot_hq', 'cog')
    if style in nightZones:
        lampColor = Vec4(0.75, 0.82, 1.00, 1.0)   # cool blue-white (sodium arc / fantasy)
    else:
        lampColor = Vec4(1.00, 0.80, 0.48, 1.0)   # warm yellow-orange street lamp

    for idx, lampNp in enumerate(_lampGeomNps):
        try:
            # Get world-space light-head position (try tight bounds top, else Z+offset)
            try:
                mins, maxs = lampNp.getTightBounds(base.render)
                lightPos = Vec3(
                    (mins[0] + maxs[0]) * 0.5,
                    (mins[1] + maxs[1]) * 0.5,
                    maxs[2] - 0.25,
                )
            except Exception:
                wp = lampNp.getPos(base.render)
                lightPos = Vec3(wp.x, wp.y, wp.z + 3.2)

            pl = PointLight(f'outdoorLampLight_{idx}')
            pl.setColor(lampColor)
            # Attenuation: reaches ~10 units comfortably, falls off by 14 units
            pl.setAttenuation(Vec3(0.4, 0.0, 0.032))

            plNp = _lightRig.attachNewNode(pl)
            plNp.setPos(base.render, lightPos)
            base.render.setLight(plNp)
            _lampLights.append(plNp)
        except Exception:
            pass

    _lampLightsActive = True


def _disableLampLights() -> None:
    """Remove all street-lamp PointLights (call at sunrise/day)."""
    global _lampLights, _lampLightsActive
    for plNp in _lampLights:
        try:
            base.render.clearLight(plNp)
        except Exception:
            pass
        try:
            if not plNp.isEmpty():
                plNp.removeNode()
        except Exception:
            pass
    _lampLights.clear()
    _lampLightsActive = False


# ─────────────────────────────────────────────────────────────────────────────
# Day / night interpolation
# ─────────────────────────────────────────────────────────────────────────────

def _evalKeyframes(zone: str, hour: float) -> dict:
    frames = _DAY_NIGHT_KEYFRAMES.get(zone)
    if not frames:
        return {}
    hour   = hour % 24.0
    valid  = [(h, d) for h, d in frames if d is not None]
    if not valid:
        return {}
    if len(valid) == 1:
        return dict(valid[0][1])

    prev_h, prev_d = valid[-1]
    next_h, next_d = valid[0]
    for i in range(len(valid)):
        kh, kd = valid[i]
        if kh <= hour:
            prev_h, prev_d = kh, kd
            nxt_i = (i + 1) % len(valid)
            next_h, next_d = valid[nxt_i]

    span = next_h - prev_h
    if span <= 0:
        span   = (24.0 - prev_h) + next_h
        t_prog = (hour - prev_h) % 24.0
    else:
        t_prog = hour - prev_h
    t = _clamp(t_prog / span if span > 0 else 0.0, 0.0, 1.0)

    result: dict = {}
    all_keys = set(prev_d.keys()) | set(next_d.keys())
    for key in all_keys:
        av = prev_d.get(key)
        bv = next_d.get(key)
        if isinstance(av, bool) or isinstance(bv, bool):
            result[key] = bv if t >= 0.5 else av
        elif isinstance(av, (int, float)) and isinstance(bv, (int, float)):
            result[key] = _lerpF(float(av), float(bv), t)
        elif isinstance(av, (tuple, list)) or isinstance(bv, (tuple, list)):
            result[key] = _lerpT(
                tuple(av) if av is not None else None,
                tuple(bv) if bv is not None else None,
                t,
            )
        else:
            result[key] = bv if t >= 0.5 else av
    return result


def _getActiveSpec() -> dict:
    base_spec = _ZONE_PROFILES.get(_activeStyle, _ZONE_PROFILES['playground'])
    if not _wantDayNight() or not base_spec.get('dayNightEnabled', True):
        return base_spec
    overrides = _evalKeyframes(_activeStyle, _timeOfDay)
    if not overrides:
        return base_spec
    merged = dict(base_spec)
    merged.update(overrides)
    return merged


# ─────────────────────────────────────────────────────────────────────────────
# Sky helpers
# ─────────────────────────────────────────────────────────────────────────────

def _getHood():
    hood = getattr(getattr(base, 'cr', None), 'playGame', None)
    return getattr(hood, 'hood', None) if hood else None


def _dimSkyForLights() -> None:
    global _skyWasDimmed
    hood = _getHood()
    if _proceduralSky and _proceduralSky.isActive():
        # Procedural sky manages its own lighting — hide the model sky.
        if hood and getattr(hood, 'sky', None) and not hood.sky.isEmpty():
            hood.sky.hide()
        _skyWasDimmed = False
        return
    if hood and getattr(hood, 'sky', None) and not hood.sky.isEmpty():
        hood.sky.setLightOff(1)
        _skyWasDimmed = True


def _restoreSkyLighting() -> None:
    global _skyWasDimmed
    if not _skyWasDimmed:
        return
    hood = _getHood()
    if hood and getattr(hood, 'sky', None) and not hood.sky.isEmpty():
        if hasattr(hood.sky, 'clearLightOff'):
            hood.sky.clearLightOff()
        else:
            try:
                hood.sky.clearAttrib(LightAttrib.getClassType())
            except Exception:
                try:
                    hood.sky.setLightOff(0)
                except Exception:
                    pass
        hood.sky.show()
    _skyWasDimmed = False


def _tintSky(spec: dict) -> None:
    if _proceduralSky and _proceduralSky.isActive():
        return  # Sky handled by procedural system
    hood = _getHood()
    if hood and getattr(hood, 'sky', None) and not hood.sky.isEmpty():
        sc = spec.get('skyScale', (1, 1, 1, 1))
        hood.sky.setColorScale(Vec4(*sc))


def _clearSkyTint() -> None:
    hood = _getHood()
    if hood and getattr(hood, 'sky', None) and not hood.sky.isEmpty():
        hood.sky.clearColorScale()
        hood.sky.show()


# ─────────────────────────────────────────────────────────────────────────────
# Window background colour
# ─────────────────────────────────────────────────────────────────────────────

def _applyBackgroundColor(spec: dict) -> None:
    global _prevClearColor
    try:
        cc = spec.get('clearColor', (0.2, 0.4, 0.6, 1.0))
        if hasattr(base, 'win') and base.win:
            if _prevClearColor is None:
                _prevClearColor = tuple(base.win.getClearColor())
            base.win.setClearColor(Vec4(*cc))
    except Exception:
        pass


def _restoreBackgroundColor() -> None:
    global _prevClearColor
    try:
        if _prevClearColor and hasattr(base, 'win') and base.win:
            base.win.setClearColor(Vec4(*_prevClearColor))
    except Exception:
        pass
    _prevClearColor = None


# ─────────────────────────────────────────────────────────────────────────────
# Shadow / scene bounds
# ─────────────────────────────────────────────────────────────────────────────

def _computeFullZoneShadowBounds(geom, defaultArea: float) -> tuple[Vec3, float, float]:
    focus = Vec3(0.0, 0.0, 0.0)
    half  = max(100.0, float(defaultArea))
    if geom is None or geom.isEmpty():
        return (focus, half, half)
    try:
        bounds = geom.getTightBounds()
        if bounds and len(bounds) == 2:
            mins, maxs = bounds
            center = (mins + maxs) * 0.5
            size   = maxs - mins
            focus  = Vec3(center[0], center[1], center[2])
            half   = max(half, max(float(size[0]), float(size[1])) * 0.55)
    except Exception:
        pass
    return (focus, half * 0.8, half)


# ─────────────────────────────────────────────────────────────────────────────
# Light rig
# ─────────────────────────────────────────────────────────────────────────────

def _positionShadowCaster() -> None:
    if not (_keyCastsShadows and _keyLightNp and not _keyLightNp.isEmpty()
            and _shadowFocusPos is not None):
        return
    try:
        target = Vec3(_shadowFocusPos[0], _shadowFocusPos[1], _shadowFocusPos[2])
        texel  = max(0.25, _shadowFilmArea / max(1.0, float(_shadowMapRes)))
        # Only snap X and Y to the texel grid to prevent shadow edge swimming.
        # Snapping Z too causes the shadow frustum to stutter vertically, which
        # manifests as sharp spike-like seam artifacts along geometry silhouettes.
        target = Vec3(
            round(target[0] / texel) * texel,
            round(target[1] / texel) * texel,
            target[2],   # Z intentionally not snapped – vertical snap = spike artifacts
        )
        sunDir       = _keyLightNp.getQuat(base.render).getForward()
        shadowCamPos = target - sunDir * _shadowFollowDist
        _keyLightNp.setPos(base.render, shadowCamPos)
    except Exception:
        pass


def _spawnLightRig(spec: dict, geom=None,
                   shadowBounds: tuple[Vec3, float] | None = None) -> None:
    global _lightRig, _renderLights, _keyLightNp, _shadowFollowDist
    global _keyCastsShadows, _shadowFocusPos, _shadowSceneRadius
    global _shadowMapRes, _shadowFilmArea, _prevShadowCasterState

    intensity          = _intensityScale()
    _lightRig          = base.render.attachNewNode('outdoorLightRig')
    _renderLights      = []
    _keyLightNp        = None
    _keyCastsShadows   = False
    _shadowFocusPos    = None
    _shadowSceneRadius = 180.0
    _shadowMapRes      = 1024
    _shadowFilmArea    = 180.0
    _shadowFollowDist  = float(spec.get('shadowFollowDist', 220.0))
    defaultArea        = float(spec.get('shadowArea', 180))

    if shadowBounds is not None:
        _shadowFocusPos    = Vec3(*shadowBounds[0])
        _shadowSceneRadius = max(60.0, float(shadowBounds[1]))
        fullHalf           = float(shadowBounds[1])
    else:
        focus, radius, fullHalf = _computeFullZoneShadowBounds(geom, defaultArea)
        _shadowFocusPos    = focus
        _shadowSceneRadius = radius

    # ── Ambient ──────────────────────────────────────────────────────────────
    floor    = float(spec.get('shadowDarknessFloor', 0.18))
    rawAmb   = _applyColorTemp(_scaleColor(spec['ambient'], intensity))
    ambColor = (
        max(rawAmb[0], floor * 0.8),
        max(rawAmb[1], floor * 0.7),
        max(rawAmb[2], floor * 0.9),
        rawAmb[3],
    )
    amb   = AmbientLight('outdoorAmbient')
    amb.setColor(Vec4(*ambColor))
    ambNp = _lightRig.attachNewNode(amb)
    base.render.setLight(ambNp)
    _renderLights.append(ambNp)

    # ── Key / sun ─────────────────────────────────────────────────────────────
    keyColor      = _applyColorTemp(_scaleColor(spec['key'], intensity))
    key           = DirectionalLight('outdoorKey')
    key.setColor(Vec4(*keyColor))
    wants_shadow  = (spec.get('shadowCaster', False)
                     and _wantDynamicShadows()
                     and _shadowQuality() != 'off')
    _prevShadowCasterState = wants_shadow

    if wants_shadow:
        try:
            res = _scaledShadowRes(spec)
            key.setShadowCaster(True, res, res)
            try:
                key.setCameraMask(_SHADOW_CAM_MASK)
            except Exception:
                pass
            _shadowMapRes = res

            # Integer depth bias only.  The 3-arg DepthOffsetAttrib.make(off, a, b) is
            # NOT (offset, slope, maxBias) — it clamps projected Z to [min_value, max_value]
            # in *normalized* depth, both in [0, 1].  Passing 2.5 triggers assertions and
            # breaks shadow maps (see logs: depthOffsetAttrib.cxx min_value 0..1 check).
            depthOffset = int(spec.get('shadowDepthOffset', 7))
            depthOffset = max(0, min(16, depthOffset))
            key.setInitialState(RenderState.make(DepthOffsetAttrib.make(depthOffset)))

            areaScale = float(spec.get('shadowAreaScale', 1.0))
            area      = fullHalf * 2.0 * _clamp(areaScale, 0.75, 2.00)
            maxScale  = float(spec.get('shadowMaxAreaScale', 3.0))
            area      = _clamp(area, defaultArea,
                               defaultArea * _clamp(maxScale, 1.5, 4.0))
            key.getLens().setFilmSize(area, area)
            _shadowFilmArea = float(area)

            nearClip = max(4.0, _shadowFollowDist - (_shadowSceneRadius * 1.35))
            farClip  = (_shadowFollowDist + (_shadowSceneRadius * 1.85)
                        + max(80.0, area * 0.30))
            if farClip <= nearClip + 32.0:
                farClip = nearClip + 32.0
            key.getLens().setNearFar(float(nearClip), float(farClip))
            _keyCastsShadows = True
        except Exception:
            try:
                key.setShadowCaster(True, 1024, 1024)
                _shadowMapRes = 1024
                key.setInitialState(RenderState.make(DepthOffsetAttrib.make(4)))
                fallArea = float(spec.get('shadowArea', 180))
                key.getLens().setFilmSize(fallArea, fallArea)
                key.getLens().setNearFar(10, int(_shadowFollowDist * 2.0 + 500))
                _shadowFilmArea   = fallArea
                _keyCastsShadows  = True
            except Exception:
                pass

    keyNp = _lightRig.attachNewNode(key)
    keyNp.setHpr(*spec['keyHpr'])
    base.render.setLight(keyNp)
    _renderLights.append(keyNp)
    _keyLightNp = keyNp
    _positionShadowCaster()

    # ── Fill ──────────────────────────────────────────────────────────────────
    fillColor = _applyColorTemp(_scaleColor(spec['fill'], intensity * 0.85))
    fill      = DirectionalLight('outdoorFill')
    fill.setColor(Vec4(*fillColor))
    fillNp = _lightRig.attachNewNode(fill)
    fillNp.setHpr(*spec['fillHpr'])
    base.render.setLight(fillNp)
    _renderLights.append(fillNp)

    # ── Rim ───────────────────────────────────────────────────────────────────
    if spec.get('rim'):
        rimColor = _applyColorTemp(_scaleColor(spec['rim'], intensity * 0.70))
        rim      = DirectionalLight('outdoorRim')
        rim.setColor(Vec4(*rimColor))
        rimNp = _lightRig.attachNewNode(rim)
        rimNp.setHpr(*spec['rimHpr'])
        base.render.setLight(rimNp)
        _renderLights.append(rimNp)


def _destroyLightRig() -> None:
    global _lightRig, _renderLights, _keyLightNp, _keyCastsShadows
    global _shadowFocusPos, _shadowSceneRadius, _shadowMapRes, _shadowFilmArea
    global _prevShadowCasterState
    _disableLampLights()
    for ln in _renderLights:
        try:
            base.render.clearLight(ln)
        except Exception:
            pass
    _renderLights         = []
    _keyLightNp           = None
    _keyCastsShadows      = False
    _shadowFocusPos       = None
    _shadowSceneRadius    = 180.0
    _shadowMapRes         = 1024
    _shadowFilmArea       = 180.0
    _prevShadowCasterState = None
    if _lightRig and not _lightRig.isEmpty():
        _lightRig.removeNode()
    _lightRig = None


def _applyProfileLive(spec: dict) -> None:
    if not (_lightRig and not _lightRig.isEmpty()):
        return

    intensity = _intensityScale()
    floor     = float(spec.get('shadowDarknessFloor', 0.18))

    for np in _renderLights:
        node = np.getNode(0)
        name = node.getName()

        if isinstance(node, AmbientLight):
            raw = _applyColorTemp(_scaleColor(
                spec.get('ambient', (0.2, 0.2, 0.3, 1)), intensity))
            c   = (max(raw[0], floor * 0.8), max(raw[1], floor * 0.7),
                   max(raw[2], floor * 0.9), raw[3])
            node.setColor(Vec4(*c))

        elif name == 'outdoorKey':
            c = _applyColorTemp(_scaleColor(
                spec.get('key', (1, 1, 1, 1)), intensity))
            node.setColor(Vec4(*c))
            np.setHpr(*spec.get('keyHpr', (0, -45, 0)))

        elif name == 'outdoorFill':
            c = _applyColorTemp(_scaleColor(
                spec.get('fill', (0.5, 0.5, 0.5, 1)), intensity * 0.85))
            node.setColor(Vec4(*c))

        elif name == 'outdoorRim':
            rim = spec.get('rim')
            if rim:
                c = _applyColorTemp(_scaleColor(rim, intensity * 0.70))
                node.setColor(Vec4(*c))

    # Fog live update
    if _fogNode:
        fc  = spec.get('fogColor', (0.5, 0.6, 0.8, 1))
        exp = spec.get('fogExponent')
        dm  = _fogDensityMult()
        _fogNode.setColor(Vec4(*fc))
        if exp is not None:
            _fogNode.setExpDensity(exp * dm)
        elif spec.get('fogFar'):
            near_v = spec.get('fogNear', 80.0)
            far_v  = spec.get('fogFar', 450.0)
            adjusted_near = near_v / dm
            adjusted_far  = far_v  / dm
            _fogNode.setLinearRange(adjusted_near, adjusted_far)

    _tintSky(spec)
    _applyBackgroundColor(spec)

    # God rays overlay (render2dp)
    if _godRaysCard and not _godRaysCard.isEmpty():
        rawI = spec.get('rayIntensity', 0.0)
        eff  = rawI * _intensityScale()
        if _settingsBool('lighting-god-rays', True) and eff > 0.001:
            _godRaysCard.setShaderInput('rayIntensity', eff)
            _godRaysCard.setShaderInput('rayColor',
                                        Vec4(*spec.get('rayColor', (1, 1, 1, 1))))
            _godRaysCard.show()
        else:
            _godRaysCard.hide()

    # Shadow-caster state transition
    global _prevShadowCasterState
    wants = (spec.get('shadowCaster', False)
             and _wantDynamicShadows()
             and _shadowQuality() != 'off')
    if wants != _prevShadowCasterState:
        _scheduleRigRebuild(spec)


def _scheduleRigRebuild(spec: dict) -> None:
    global _rigRebuildPending
    _rigRebuildPending = spec


def _flushRigRebuild() -> None:
    global _rigRebuildPending
    if _rigRebuildPending is None:
        return
    spec = _rigRebuildPending
    _rigRebuildPending = None
    savedBounds = None
    if _shadowFocusPos is not None:
        savedBounds = (Vec3(_shadowFocusPos), float(_shadowSceneRadius))
    _destroyLightRig()
    _spawnLightRig(spec, shadowBounds=savedBounds)


# ─────────────────────────────────────────────────────────────────────────────
# Atmospheric fog
# ─────────────────────────────────────────────────────────────────────────────

def _applyFog(spec: dict) -> None:
    global _fogNode
    if not _settingsBool('lighting-fog-enabled', True):
        return
    fogColor = spec.get('fogColor')
    if not fogColor:
        return
    dm       = _fogDensityMult()
    _fogNode = Fog('outdoorFog')
    _fogNode.setColor(Vec4(*fogColor))
    exponent = spec.get('fogExponent')
    if exponent is not None:
        _fogNode.setExpDensity(exponent * dm)
    else:
        near_v = spec.get('fogNear', 80.0)
        far_v  = spec.get('fogFar', 450.0)
        _fogNode.setLinearRange(near_v / dm, far_v / dm)
    base.render.setFog(_fogNode)


def _clearFog() -> None:
    global _fogNode
    try:
        base.render.clearFog()
    except Exception:
        pass
    _fogNode = None


# ─────────────────────────────────────────────────────────────────────────────
# Post-process (bloom + 2D sun-ray overlay — no custom scene→texture compositor)
# ─────────────────────────────────────────────────────────────────────────────

def _maintainOutdoorLightingViewport() -> None:
    """Keep the main window's DisplayRegions at full size and pixel_zoom=1.

    Two separate issues produce the same “3D in the bottom-left quarter” look:
    (1) per-DisplayRegion **pixel_zoom** > 1, or (2) normalized **dimensions**
    smaller than the full window on the compositor / 3D region.  Stock
    FilterManager does not always keep those in sync on every GL driver.

    When outdoor FX is active we therefore reset **every** main-window
    DisplayRegion to (0,1)×(0,1) and pixel_zoom 1 each frame.  That can break
    rare sub-rectangle DR tricks (e.g. picture-in-picture) while the rig runs.

    Each operation is individually guarded so that a threading assertion on
    win.setPixelZoom (observed on the custom Panda3D build) cannot abort the
    entire repair and leave the DR dimensions uncorrected.
    """
    win = getattr(base, 'win', None)
    if not win:
        return

    # Window-level pixel zoom — may raise assertion on some builds; keep isolated.
    try:
        win.setPixelZoom(1)
    except Exception:
        pass

    # Per-DR dimensions and pixel zoom.
    try:
        n = win.getNumDisplayRegions()
    except Exception:
        n = 0
    for i in range(n):
        try:
            dr = win.getDisplayRegion(i)
            if not dr:
                continue
            dr.setDimensions(0.0, 1.0, 0.0, 1.0)
            try:
                if dr.supportsPixelZoom():
                    dr.setPixelZoom(1)
            except Exception:
                pass
        except Exception:
            pass

    # RTT buffer DisplayRegions (scene capture buffers, bloom passes, etc.)
    _fixPostProcessRttViewports()


def _setupCinematicPost(spec: dict) -> None:
    """Bloom plus additive sun shafts — no full-window scene RTT compositor."""
    _setupBloom(spec)
    _createGodRaysOverlay(spec)


def _setupPostProcess(spec: dict) -> None:
    _destroyPostProcess()

    if not _wantFx():
        return

    mode = 'full'
    if _OUTDOOR_SHADER_BISECT_LEVEL == 2:
        mode = _LEVEL2_POST_SINGLE
    if mode not in ('full', 'bloom', 'godrays', 'stack'):
        mode = 'full'

    if mode == 'godrays':
        _createGodRaysOverlay(spec)
        return
    if mode == 'bloom':
        _setupBloom(spec)
        return
    # 'full' and 'stack': bloom + god rays
    _setupCinematicPost(spec)


def _destroyPostProcess() -> None:
    _destroyBloom()
    _destroyGodRaysOverlay()


# ─────────────────────────────────────────────────────────────────────────────
# Bloom (CommonFilters)
# ─────────────────────────────────────────────────────────────────────────────

def _setupBloom(spec: dict) -> None:
    global _bloomFilters
    if not _wantBloom():
        return
    intensity = float(spec.get('bloomIntensity', 0.0))
    if intensity <= 0.001:
        return
    try:
        from direct.filter.CommonFilters import CommonFilters
        _bloomFilters = CommonFilters(base.win, base.cam)
        threshold     = float(spec.get('bloomThreshold', 0.65))
        size = 'large' if intensity >= 0.55 else ('medium' if intensity >= 0.25 else 'small')
        _bloomFilters.setBloom(
            size=size,
            intensity=intensity,
            mintrigger=threshold,
            maxtrigger=min(1.0, threshold + 0.30),
            desat=-0.4,
        )
        # CommonFilters uses the base FilterManager.renderSceneInto which calls
        # buffer.makeDisplayRegion() without explicit bounds.  On some GL drivers
        # (including the custom OpenToontown build) that defaults to a bottom-left
        # sub-rectangle, causing the scene to render into only part of the colour
        # texture — the root cause of the "3D view in the bottom-left" bug.
        # Force full-window bounds on every offscreen DR immediately after setup.
        _fixPostProcessRttViewports()
    except Exception:
        _bloomFilters = None


def _destroyBloom() -> None:
    global _bloomFilters
    if _bloomFilters is not None:
        try:
            _bloomFilters.cleanup()
        except Exception:
            pass
        _bloomFilters = None


def _updateBloomLive(spec: dict) -> None:
    if _bloomFilters is None:
        return
    try:
        intensity = float(spec.get('bloomIntensity', 0.0)) * _intensityScale()
        if intensity <= 0.001:
            _bloomFilters.delBloom()
            return
        threshold = float(spec.get('bloomThreshold', 0.65))
        size = 'large' if intensity >= 0.55 else ('medium' if intensity >= 0.25 else 'small')
        _bloomFilters.setBloom(
            size=size, intensity=intensity,
            mintrigger=threshold, maxtrigger=min(1.0, threshold + 0.30),
            desat=-0.4,
        )
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Sun-ray overlay (render2dp)
# ─────────────────────────────────────────────────────────────────────────────

def _loadGodRaysShader() -> Shader | None:
    global _godRaysShader
    if _godRaysShader is not None:
        return _godRaysShader
    try:
        vp_os = os.path.normpath(_LEGACY_VERT)
        fp_os = os.path.normpath(_LEGACY_FRAG)
        if not (os.path.isfile(vp_os) and os.path.isfile(fp_os)):
            return None
        vp = Filename.fromOsSpecific(vp_os)
        fp = Filename.fromOsSpecific(fp_os)
        try:
            vp.makeTrueCase()
            fp.makeTrueCase()
        except Exception:
            pass
        _godRaysShader = Shader.load(Shader.SL_GLSL, vp, fp)
        return _godRaysShader
    except Exception:
        return None


def _createGodRaysOverlay(spec: dict) -> None:
    global _godRaysCard
    if not _settingsBool('lighting-god-rays', True):
        return
    rawI = spec.get('rayIntensity', 0.0)
    if rawI <= 0.0:
        return
    shader = _loadGodRaysShader()
    if shader is None:
        return
    try:
        cm   = CardMaker('outdoorGodRays')
        cm.setFrameFullscreenQuad()
        card = base.render2dp.attachNewNode(cm.generate())
        card.setDepthTest(False)
        card.setDepthWrite(False)
        card.setTransparency(TransparencyAttrib.MAlpha)
        card.setAttrib(ColorBlendAttrib.make(
            ColorBlendAttrib.MAdd,
            ColorBlendAttrib.OIncomingAlpha,
            ColorBlendAttrib.OOne,
        ))
        card.setShader(shader)

        su, sv = spec.get('sunUV', (0.5, 0.75))
        rc     = spec.get('rayColor', (1.0, 1.0, 1.0, 1.0))
        eff    = rawI * _intensityScale()
        card.setShaderInput('sunPos',       (su, sv))
        card.setShaderInput('rayColor',     Vec4(*rc))
        card.setShaderInput('rayIntensity', eff)
        card.setShaderInput('time',          0.0)
        try:
            props = base.win.getProperties()
            ar    = props.getXSize() / max(1, props.getYSize())
        except Exception:
            ar = 1.333
        card.setShaderInput('aspectRatio', ar)
        _godRaysCard = card
    except Exception:
        _godRaysCard = None


def _destroyGodRaysOverlay() -> None:
    global _godRaysCard
    if _godRaysCard and not _godRaysCard.isEmpty():
        _godRaysCard.removeNode()
    _godRaysCard = None


# ─────────────────────────────────────────────────────────────────────────────
# Procedural sky
# ─────────────────────────────────────────────────────────────────────────────

def _setupProceduralSky(spec: dict) -> None:
    global _proceduralSky
    if not _wantProceduralSky():
        return
    try:
        from toontown.hood.ProceduralSky import ProceduralSky
        _proceduralSky = ProceduralSky()
        # Parent to the lens NodePath (base.cam) so the dome shares the same
        # transform as the camera FilterManager renders with; base.camera can sit
        # slightly off the lens on third-person rigs.
        _skyParent = base.cam if (getattr(base, 'cam', None) and not base.cam.isEmpty()) else base.camera
        _proceduralSky.attach(_skyParent, style=_activeStyle)
        _proceduralSky.update(spec, _timeOfDay)
        hood = _getHood()
        if hood and getattr(hood, 'sky', None) and not hood.sky.isEmpty():
            # If the procedural sky failed to attach (shader missing, etc),
            # keep the legacy model sky visible as a fallback.
            if _proceduralSky and _proceduralSky.isActive():
                hood.sky.hide()
            else:
                hood.sky.show()
    except Exception:
        _proceduralSky = None


def _destroyProceduralSky() -> None:
    global _proceduralSky
    if _proceduralSky is not None:
        try:
            _proceduralSky.detach()
        except Exception:
            pass
        _proceduralSky = None


# ─────────────────────────────────────────────────────────────────────────────
# Water reflection system (unchanged from previous version)
# ─────────────────────────────────────────────────────────────────────────────

def _loadWaterShader() -> Shader | None:
    global _waterShader
    if _waterShader is not None:
        return _waterShader
    try:
        vp_os = os.path.normpath(_WATER_VERT)
        fp_os = os.path.normpath(_WATER_FRAG)
        if not (os.path.isfile(vp_os) and os.path.isfile(fp_os)):
            return None
        vp = Filename.fromOsSpecific(vp_os)
        fp = Filename.fromOsSpecific(fp_os)
        try:
            vp.makeTrueCase()
            fp.makeTrueCase()
        except Exception:
            pass
        _waterShader = Shader.load(Shader.SL_GLSL, vp, fp)
        return _waterShader
    except Exception:
        return None


def _isWaterNode(name: str) -> bool:
    nl = name.lower()
    return any(p in nl for p in _WATER_PATTERNS)


def _findWaterNodes(geom) -> list[NodePath]:
    if geom is None or geom.isEmpty():
        return []
    results: list[NodePath] = []
    try:
        all_nodes = geom.findAllMatches('**/*')
        for i in range(all_nodes.getNumPaths()):
            np = all_nodes.getPath(i)
            if _isWaterNode(np.getName()):
                results.append(np)
    except Exception:
        pass
    return results


def _setupWaterNode(waterNp: NodePath, spec: dict) -> dict | None:
    if not _wantWater():
        return None
    shader = _loadWaterShader()
    if shader is None:
        wc = spec.get('waterColor', (0.22, 0.38, 0.55, 0.85))
        try:
            waterNp.setColorScale(Vec4(*wc))
        except Exception:
            pass
        return None

    quality  = spec.get('waterReflQuality', 'medium')
    bufW, bufH = {'high': (1024, 1024), 'low': (256, 256)}.get(quality, (512, 512))

    try:
        buf = base.win.makeTextureBuffer('waterRefl', bufW, bufH)
        buf.setClearColor(Vec4(0.1, 0.2, 0.3, 1.0))
        reflTex  = buf.getTexture()
        reflCamNp = base.makeCamera(buf)
        reflCamNp.reparentTo(base.render)

        waterHeight = waterNp.getZ(base.render)
        taskName    = f'waterReflTask_{id(waterNp)}'

        def _syncReflCam(task, rnp=reflCamNp, wh=waterHeight):
            if rnp.isEmpty() or base.camera.isEmpty():
                return task.done
            cp  = base.camera.getPos(base.render)
            ch  = base.camera.getHpr(base.render)
            mz  = 2.0 * wh - cp.z
            rnp.setPos(base.render, cp.x, cp.y, mz)
            rnp.setHpr(base.render, ch.x, -ch.y, ch.z)
            try:
                rnp.node().getLens().setNearFar(
                    base.camNode.getLens().getNear(),
                    base.camNode.getLens().getFar(),
                )
            except Exception:
                pass
            return task.cont

        taskMgr.add(_syncReflCam, taskName, sort=44)

        wc   = spec.get('waterColor', (0.22, 0.38, 0.55, 0.85))
        sdir = Vec3(0, -1, -1)
        if _keyLightNp and not _keyLightNp.isEmpty():
            try:
                sdir = _keyLightNp.getQuat(base.render).getForward()
                sdir.normalize()
            except Exception:
                pass

        waterNp.setShaderAuto(False)
        waterNp.setShader(shader)
        waterNp.setShaderInput('osl_ReflectionTex',      reflTex)
        waterNp.setShaderInput('osl_WaterColor',         Vec4(*wc))
        waterNp.setShaderInput('osl_SunColor',           Vec4(1.0, 0.95, 0.80, 1.0))
        waterNp.setShaderInput('osl_SunDir',             sdir)
        waterNp.setShaderInput('osl_CameraPos',          base.camera.getPos(base.render))
        waterNp.setShaderInput('osl_Time',               0.0)
        waterNp.setShaderInput('osl_WaveScale',          1.4)
        waterNp.setShaderInput('osl_WaveSpeed',          0.8)
        waterNp.setShaderInput('osl_FresnelPower',       3.5)
        waterNp.setShaderInput('osl_Roughness',          0.35)
        waterNp.setShaderInput('osl_ReflectionStrength', 0.72)
        waterNp.setTransparency(TransparencyAttrib.MAlpha)

        return {
            'np':       waterNp,
            'buffer':   buf,
            'camera':   reflCamNp,
            'taskName': taskName,
        }
    except Exception:
        return None


def _setupAllWater(geom, spec: dict) -> None:
    global _waterSetups
    if not spec.get('hasWater', False) or not _wantWater():
        return
    for np in _findWaterNodes(geom):
        setup = _setupWaterNode(np, spec)
        if setup:
            _waterSetups.append(setup)


def _cleanupAllWater() -> None:
    global _waterSetups, _waterShader
    for ws in _waterSetups:
        try:
            taskMgr.remove(ws['taskName'])
        except Exception:
            pass
        try:
            cam = ws.get('camera')
            if cam and not cam.isEmpty():
                cam.removeNode()
        except Exception:
            pass
        try:
            buf = ws.get('buffer')
            if buf:
                base.graphicsEngine.removeWindow(buf)
        except Exception:
            pass
        try:
            np = ws.get('np')
            if np and not np.isEmpty():
                np.clearShader()
                np.clearColorScale()
        except Exception:
            pass
    _waterSetups = []
    _waterShader = None


def _tickWaterUniforms(dt: float) -> None:
    if not _waterSetups:
        return
    camPos = None
    sunDir = Vec3(0, -1, -1)
    try:
        camPos = base.camera.getPos(base.render)
    except Exception:
        pass
    if _keyLightNp and not _keyLightNp.isEmpty():
        try:
            sunDir = _keyLightNp.getQuat(base.render).getForward()
            sunDir.normalize()
        except Exception:
            pass
    for ws in _waterSetups:
        np = ws.get('np')
        if not np or np.isEmpty():
            continue
        try:
            np.setShaderInput('osl_Time', _godRaysTime)
            if camPos:
                np.setShaderInput('osl_CameraPos', camPos)
            np.setShaderInput('osl_SunDir', sunDir)
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# Per-frame update task
# ─────────────────────────────────────────────────────────────────────────────

def _lightingUpdateTask(task):
    global _godRaysTime, _timeOfDay, _dayNightAccum

    dt            = globalClock.getDt()
    _godRaysTime += dt

    if _refCount > 0:
        _maintainOutdoorLightingViewport()

    # ── Shadow camera positioning ─────────────────────────────────────────────
    _positionShadowCaster()

    # ── Water uniforms ────────────────────────────────────────────────────────
    _tickWaterUniforms(dt)

    # ── Procedural sky update ─────────────────────────────────────────────────
    if _proceduralSky and _proceduralSky.isActive():
        spec = _getActiveSpec()
        _proceduralSky.update(spec, _timeOfDay)

    # ── Day / night cycle ─────────────────────────────────────────────────────
    if _wantDayNight() and _refCount > 0:
        spec = _ZONE_PROFILES.get(_activeStyle, _ZONE_PROFILES['playground'])
        if spec.get('dayNightEnabled', True):
            _dayNightAccum += dt
            if _dayNightAccum >= 0.25:  # 4 Hz update rate
                gameHours  = (_dayNightAccum
                              * _dayNightSpeed
                              * _dayNightSpeedMultiplier())
                _timeOfDay      = (_timeOfDay + gameHours) % 24.0
                _dayNightAccum  = 0.0
                cur_spec        = _getActiveSpec()
                _applyProfileLive(cur_spec)
                _updateBloomLive(cur_spec)

    # ── Street lamp lights: on at night, off during day ───────────────────────
    if _lampGeomNps and _lightRig and not _lightRig.isEmpty():
        try:
            cur_spec = _getActiveSpec()
            kHpr     = cur_spec.get('keyHpr', (135, -42, 0))
            # Derive sun elevation: the key-light pitch angle p gives us:
            #   lightFwd.z = -sin(p),  sunDirWorld.z = sin(p)
            # p=-42 → sin(-42°)=-0.669 → sunDirWorld.z = -0.669 → below horizon
            # p=+42 → sin(+42°)=+0.669 → sunDirWorld.z = +0.669 → above horizon
            sunDirZ = math.sin(math.radians(kHpr[1]))
            if sunDirZ > 0.10:   # sun more than ~6° below horizon → enable lamps
                _enableLampLights(_activeStyle)
            else:
                _disableLampLights()
        except Exception:
            pass

    # ── Sun-ray overlay shimmer ───────────────────────────────────────────────
    if _godRaysCard and not _godRaysCard.isEmpty():
        _godRaysCard.setShaderInput('time', _godRaysTime)

    # ── Deferred rig rebuild ──────────────────────────────────────────────────
    _flushRigRebuild()

    return task.cont


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def begin(geom, style: str = 'playground',
          hoodId: int | None = None,
          zoneId: int | None = None) -> None:
    """Activate the outdoor lighting rig for the given geometry.

    Parameters
    ----------
    geom:
        Scene-geometry NodePath; receives per-pixel auto-shading.
    style:
        Fallback profile key (``'playground'``, ``'estate'``, ``'cog'``, etc.).
    hoodId:
        ToontownGlobals hood constant – overrides *style* for zone lookup.
    zoneId:
        Specific zone constant (e.g. SillyStreet) – used for street-level
        profiles.  Takes priority over *hoodId*.
    """
    global _refCount, _activeStyle
    if not _wantFx():
        return

    resolvedStyle = _resolveStyle(style, hoodId, zoneId)
    spec          = _ZONE_PROFILES[resolvedStyle]

    if _refCount == 0:
        _activeStyle = resolvedStyle
        cur_spec     = _getActiveSpec() if spec.get('dayNightEnabled', True) else spec
        _spawnLightRig(cur_spec, geom)
        _applyFog(cur_spec)
        _tintSky(cur_spec)
        _applyBackgroundColor(cur_spec)
        _setupProceduralSky(cur_spec)
        if _OUTDOOR_SHADER_BISECT_LEVEL >= 2:
            _setupPostProcess(cur_spec)
        if _OUTDOOR_SHADER_BISECT_LEVEL >= 3:
            _setupAllWater(geom, cur_spec)
        _dimSkyForLights()
        # Full-window + per-DisplayRegion pixel_zoom (see _maintainOutdoorLightingViewport).
        _maintainOutdoorLightingViewport()
        # Run before most gameplay (low sort = earlier): keep viewports patched pre-cull.
        taskMgr.add(_lightingUpdateTask, _godRaysTaskName, sort=-60)

    _refCount += 1

    if geom is not None and not geom.isEmpty():
        geom.setShaderAuto()
        _forceLightingOnSubtree(geom)
        _hidePlaneLikeCastersFromShadow(geom)
        _applyDefaultSpecularMaterial(geom)
        # Scan for lamp/lantern nodes to use as night-light emitters.
        # Only scan on first begin() (refCount was 0 before increment).
        if _refCount == 1:
            global _lampGeomNps
            _lampGeomNps = _scanForLampNodes(geom)

    lav = getattr(base, 'localAvatar', None)
    if lav is not None and not lav.isEmpty():
        lav.setShaderAuto()


def end(geom=None) -> None:
    """Deactivate the outdoor lighting rig."""
    global _refCount
    if not _wantFx():
        return

    if geom is not None and not geom.isEmpty():
        geom.clearShader()
        _clearDefaultSpecularMaterial(geom)
    lav = getattr(base, 'localAvatar', None)
    if lav is not None and not lav.isEmpty():
        lav.clearShader()

    if _refCount > 0:
        _refCount -= 1

    if _refCount == 0:
        taskMgr.remove(_godRaysTaskName)
        _destroyPostProcess()
        _cleanupAllWater()
        _clearFog()
        _clearSkyTint()
        _restoreBackgroundColor()
        _destroyLightRig()
        _restoreSkyLighting()
        _destroyProceduralSky()
        global _lampGeomNps
        _lampGeomNps = []


def shadeExtraSubtree(np) -> None:
    """Enable auto-shading on an extra outdoor NodePath."""
    if not _wantFx() or np is None or np.isEmpty():
        return
    np.setShaderAuto()
    _forceLightingOnSubtree(np)
    _hidePlaneLikeCastersFromShadow(np)
    _applyDefaultSpecularMaterial(np)


def clearExtraSubtree(np) -> None:
    """Remove auto-shading from an extra outdoor NodePath."""
    if not _wantFx() or np is None or np.isEmpty():
        return
    np.clearShader()
    _clearDefaultSpecularMaterial(np)


def refreshSettings() -> None:
    """Hot-reload all active lighting parameters from current user settings.

    Called by the Lighting settings tab whenever the player changes a slider
    or toggle.  All systems are updated in-place where possible.
    """
    if _refCount == 0:
        return

    spec = _getActiveSpec()

    # Rebuild light rig (picks up resolution / shadow quality changes).
    savedBounds = None
    if _shadowFocusPos is not None:
        savedBounds = (Vec3(_shadowFocusPos), float(_shadowSceneRadius))
    _destroyLightRig()
    _spawnLightRig(spec, shadowBounds=savedBounds)

    _clearFog()
    _applyFog(spec)
    _tintSky(spec)
    _applyBackgroundColor(spec)

    # Procedural sky toggle.
    if _wantProceduralSky():
        if _proceduralSky is None:
            _setupProceduralSky(spec)
        elif _proceduralSky is not None:
            _proceduralSky.setStyle(_activeStyle)
            _proceduralSky.update(spec, _timeOfDay)
    else:
        _destroyProceduralSky()
        _tintSky(spec)

    # Bloom + sun-ray overlay
    _destroyPostProcess()
    if _OUTDOOR_SHADER_BISECT_LEVEL >= 2:
        _setupPostProcess(spec)


def setTimeOfDay(hours: float) -> None:
    """Set the current in-game time of day (0–24)."""
    global _timeOfDay
    _timeOfDay = float(hours) % 24.0
    if _refCount > 0:
        cur = _getActiveSpec()
        savedBounds = None
        if _shadowFocusPos is not None:
            savedBounds = (Vec3(_shadowFocusPos), float(_shadowSceneRadius))
        _destroyLightRig()
        _spawnLightRig(cur, shadowBounds=savedBounds)
        _clearFog()
        _applyFog(cur)
        _tintSky(cur)
        _applyBackgroundColor(cur)
        _updateBloomLive(cur)
        if _proceduralSky:
            _proceduralSky.update(cur, _timeOfDay)


def setupWaterReflection(waterNodePath, profile: dict | None = None) -> None:
    """Manually set up planar reflections on a specific water NodePath."""
    if not _wantFx() or waterNodePath is None or waterNodePath.isEmpty():
        return
    base_spec = _ZONE_PROFILES.get(_activeStyle, _ZONE_PROFILES['playground'])
    merged    = dict(base_spec)
    if profile:
        merged.update(profile)
    setup = _setupWaterNode(waterNodePath, merged)
    if setup:
        _waterSetups.append(setup)


def setWaterReflectionQuality(level: str) -> None:
    """Adjust reflection quality for all active water surfaces."""
    if level == 'off':
        _cleanupAllWater()
        return
    spec      = _getActiveSpec()
    spec_copy = dict(spec)
    spec_copy['waterReflQuality'] = level
    for ws in list(_waterSetups):
        np = ws.get('np')
        try:
            taskMgr.remove(ws['taskName'])
        except Exception:
            pass
        try:
            cam = ws.get('camera')
            if cam and not cam.isEmpty():
                cam.removeNode()
        except Exception:
            pass
        try:
            buf = ws.get('buffer')
            if buf:
                base.graphicsEngine.removeWindow(buf)
        except Exception:
            pass
        if np and not np.isEmpty():
            new_setup = _setupWaterNode(np, spec_copy)
            if new_setup:
                _waterSetups.append(new_setup)
    _waterSetups[:] = [ws for ws in _waterSetups
                       if ws.get('taskName', '').startswith('waterReflTask_')]
