"""Procedural code-generated sky system for Toontown.

Replaces the hood.sky model-based sky with a GLSL-driven atmospheric sky dome
that includes:
  • Rayleigh + Mie scattering sky gradient
  • Wide sunset/sunrise horizon corona
  • Visible SUN DISC with corona, limb darkening, blinding glare
  • Volumetric-looking FBM cumulus clouds with domain warping
  • Twinkling star field with spectral colour variation
  • Moon disc with surface detail and corona (all night zones)
  • Full day/night cycle integration

Usage (from SkyUtil / OutdoorLighting)
──────────────────────────────────────
    from toontown.hood.ProceduralSky import ProceduralSky

    sky = ProceduralSky()
    # Prefer the lens NodePath (e.g. base.cam) so the dome matches the view matrix
    # used for rendering; base.camera is fine when it coincides with the lens.
    sky.attach(base.cam)
    sky.update(spec, timeOfDay) # call each frame (or at least on spec changes)
    sky.detach()                # cleanup on zone exit

The ProceduralSky.update() signature accepts the same 'spec' dict as
OutdoorLighting zone profiles, so integration is zero-cost.

Per-zone sky parameters (added to _ZONE_PROFILES by OutdoorLighting):
    cloudCoverage   – 0.0–1.0
    cloudSpeed      – relative speed multiplier
    cloudSharpness  – 0.0 (soft) – 1.0 (sharp)
    turbidity       – 1.0–8.0 (Mie haze)
    starBrightness  – 0.0–1.0
    moonEnabled     – bool (all night zones, not just DL)
    moonDir         – (h,p,r) HPR for moon direction (matches keyHpr format)
    skyExposure     – scalar (passed to post-process; default 1.0)
    sunBlindStrength– 0.0–1.0 blinding glare when looking at sun (default 0.85)
"""

from __future__ import annotations

import math
import os

from panda3d.core import (
    Geom,
    GeomNode,
    GeomTriangles,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexWriter,
    Filename,
    NodePath,
    Shader,
    Vec3,
    Vec4,
)

from direct.showbase.ShowBaseGlobal import globalClock
from direct.task.TaskManagerGlobal import taskMgr

import builtins
base = getattr(builtins, 'base', None)

_SHADER_DIR_CANDIDATES = (
    os.path.join(os.path.dirname(__file__), '..', 'shaders'),
    os.path.join(os.path.dirname(__file__), 'shaders'),
    os.path.join(os.path.dirname(__file__), '..', '..', 'shaders'),
)
_SHADER_DIR = next((d for d in _SHADER_DIR_CANDIDATES if os.path.exists(d)), _SHADER_DIR_CANDIDATES[0])
_SKY_VERT   = os.path.join(_SHADER_DIR, 'sky.vert.glsl')
_SKY_FRAG   = os.path.join(_SHADER_DIR, 'sky.frag.glsl')

_SKY_RADIUS       = 950.0    # units – large enough to contain all Toontown geometry
_CLOUD_BASE_SPEED = 0.60     # base cloud animation speed (modified per zone)

_sky_shader: Shader | None = None


def _loadSkyShader() -> Shader | None:
    global _sky_shader
    if _sky_shader is not None:
        return _sky_shader
    print(f"[DEBUG VideoSettings] _loadSkyShader: starting...")
    try:
        try:
            from toontown.hood import OutdoorLighting as osl
            print(f"[DEBUG VideoSettings] _loadSkyShader: imported from toontown.hood")
        except ImportError:
            import OutdoorLighting as osl
            print(f"[DEBUG VideoSettings] _loadSkyShader: imported from root")
        bisect_level = getattr(osl, '_OUTDOOR_SHADER_BISECT_LEVEL', 0)
        print(f"[DEBUG VideoSettings] _loadSkyShader: osl._OUTDOOR_SHADER_BISECT_LEVEL={bisect_level}")
        if bisect_level < 1:
            print(f"[DEBUG VideoSettings] _loadSkyShader: bisect level < 1, returning None")
            return None
    except Exception as e:
        print(f"[DEBUG VideoSettings] _loadSkyShader: exception in osl import/check: {e!r}")
        pass
    try:
        vp_os = os.path.normpath(_SKY_VERT)
        fp_os = os.path.normpath(_SKY_FRAG)
        print(f"[DEBUG VideoSettings] _loadSkyShader: vp_os={vp_os}, fp_os={fp_os}")
        vp_exists = os.path.isfile(vp_os)
        fp_exists = os.path.isfile(fp_os)
        print(f"[DEBUG VideoSettings] _loadSkyShader: vp_exists={vp_exists}, fp_exists={fp_exists}")
        if not (vp_exists and fp_exists):
            print(f"[DEBUG VideoSettings] _loadSkyShader: file missing, returning None")
            return None
        # On Windows, Panda3D's shader loader expects Panda-style paths (eg
        # `/c/Users/...`) rather than raw OS paths with backslashes.
        vp = Filename.fromOsSpecific(vp_os)
        fp = Filename.fromOsSpecific(fp_os)
        try:
            vp.makeTrueCase()
            fp.makeTrueCase()
        except Exception:
            pass
        print(f"[DEBUG VideoSettings] _loadSkyShader: loading shader...")
        _sky_shader = Shader.load(Shader.SL_GLSL, vp, fp)
        print(f"[DEBUG VideoSettings] _loadSkyShader: load returned {_sky_shader}")
        return _sky_shader
    except Exception as e:
        print(f"[DEBUG VideoSettings] _loadSkyShader: exception: {e!r}")
        import traceback; traceback.print_exc()
        _sky_shader = None
        return None


def _makeSkySphereMesh(radius: float = _SKY_RADIUS,
                       latSegs: int = 18,
                       lonSegs: int = 36) -> NodePath:
    """Build an inward-facing UV sphere NodePath.

    The sphere is centred at the origin in model space.  When attached to the
    camera NodePath the camera is always at the sphere centre, so every vertex
    position is a ray direction from the camera.
    """
    vfmt  = GeomVertexFormat.getV3()
    vdata = GeomVertexData('skyDomeMesh', vfmt, Geom.UHStatic)
    vdata.setNumRows((latSegs + 1) * (lonSegs + 1))
    vwrite = GeomVertexWriter(vdata, 'vertex')

    for lat in range(latSegs + 1):
        phi = math.pi * lat / latSegs          # 0 → π  (north pole → south pole)
        sp  = math.sin(phi)
        cp  = math.cos(phi)
        for lon in range(lonSegs + 1):
            theta = 2.0 * math.pi * lon / lonSegs
            x = radius * sp * math.cos(theta)
            y = radius * sp * math.sin(theta)
            z = radius * cp
            vwrite.addData3(x, y, z)

    tris  = GeomTriangles(Geom.UHStatic)
    stride = lonSegs + 1
    for lat in range(latSegs):
        for lon in range(lonSegs):
            v0 = lat       * stride + lon
            v1 = lat       * stride + lon + 1
            v2 = (lat + 1) * stride + lon
            v3 = (lat + 1) * stride + lon + 1
            # Inward-facing: flip winding compared to outward sphere.
            tris.addVertices(v0, v2, v1)
            tris.addVertices(v1, v2, v3)
    tris.closePrimitive()

    geom = Geom(vdata)
    geom.addPrimitive(tris)
    gnode = GeomNode('skyDomeGeom')
    gnode.addGeom(geom)
    return NodePath(gnode)


def _dir_world_to_cam(world_dir: Vec3) -> Vec3:
    """Map a world-space *direction* into the active camera's local space.

    The sky dome is parented to ``base.cam``, so ``vDir`` in the GLSL fragment
    shader is in **camera space**.  ``sunDir`` / ``moonDir`` must match that
    space or dot products (sun disc, clouds, Mie) are wrong and the sky looks
    like a flat clear colour with no sun or clouds.
    """
    try:
        cam = getattr(base, 'cam', None)
        rnp = getattr(base, 'render', None)
        if cam is None or rnp is None or cam.isEmpty() or rnp.isEmpty():
            return Vec3(world_dir)
        v = cam.getRelativeVector(rnp, Vec3(world_dir))
        ln = v.length()
        if ln > 1.0e-7:
            v /= ln
        return v
    except Exception:
        return Vec3(world_dir)


def _hprToDir(h_deg: float, p_deg: float) -> Vec3:
    """Convert a Panda3D HPR heading/pitch to a world-space direction vector.

    The direction returned is the *forward* vector that a node with (H, P, 0)
    orientation points toward.  For the sun key light this is the direction the
    light shines (scene ← sun); for sun position in the sky pass the negated
    result.
    """
    h = math.radians(h_deg)
    p = math.radians(p_deg)
    # Panda3D right-hand Y-forward Z-up:
    #   H rotates around Z (clockwise from above, i.e. left-hand around Z)
    #   P rotates around X after H
    x =  math.sin(h) * math.cos(p)
    y = -math.cos(h) * math.cos(p)
    z = -math.sin(p)
    return Vec3(x, y, z)


# ─────────────────────────────────────────────────────────────────────────────
# Per-zone cloud + sky parameters defaults
# (OutdoorLighting zones may override any of these in their profile dict)
# ─────────────────────────────────────────────────────────────────────────────

_ZONE_SKY_DEFAULTS: dict[str, dict] = {
    'tt':          {'cloudCoverage': 0.42, 'cloudSpeed': 0.70, 'cloudSharpness': 0.55,
                    'turbidity': 2.5,  'starBrightness': 0.0, 'moonEnabled': False},
    'dd':          {'cloudCoverage': 0.88, 'cloudSpeed': 1.10, 'cloudSharpness': 0.20,
                    'turbidity': 5.5,  'starBrightness': 0.0, 'moonEnabled': False},
    'dg':          {'cloudCoverage': 0.28, 'cloudSpeed': 0.55, 'cloudSharpness': 0.70,
                    'turbidity': 1.8,  'starBrightness': 0.0, 'moonEnabled': False},
    'mm':          {'cloudCoverage': 0.55, 'cloudSpeed': 0.85, 'cloudSharpness': 0.45,
                    'turbidity': 3.5,  'starBrightness': 0.0, 'moonEnabled': False},
    'br':          {'cloudCoverage': 0.78, 'cloudSpeed': 1.40, 'cloudSharpness': 0.15,
                    'turbidity': 6.0,  'starBrightness': 0.0, 'moonEnabled': False},
    'dl':          {'cloudCoverage': 0.22, 'cloudSpeed': 0.25, 'cloudSharpness': 0.50,
                    'turbidity': 1.5,  'starBrightness': 0.92, 'moonEnabled': True,
                    'moonDir': (225, -55, 0)},
    'gs':          {'cloudCoverage': 0.32, 'cloudSpeed': 0.90, 'cloudSharpness': 0.50,
                    'turbidity': 3.0,  'starBrightness': 0.0, 'moonEnabled': False},
    'estate':      {'cloudCoverage': 0.38, 'cloudSpeed': 0.60, 'cloudSharpness': 0.55,
                    'turbidity': 2.2,  'starBrightness': 0.0, 'moonEnabled': False},
    'playground':  {'cloudCoverage': 0.35, 'cloudSpeed': 0.65, 'cloudSharpness': 0.50,
                    'turbidity': 2.4,  'starBrightness': 0.0, 'moonEnabled': False},
    # HQ zones: minimal sky (player rarely sees it indoors/dense area)
    'sellbot_hq':  {'cloudCoverage': 0.95, 'cloudSpeed': 0.30, 'cloudSharpness': 0.05,
                    'turbidity': 8.0,  'starBrightness': 0.0, 'moonEnabled': False},
    'cashbot_hq':  {'cloudCoverage': 0.85, 'cloudSpeed': 0.40, 'cloudSharpness': 0.10,
                    'turbidity': 7.0,  'starBrightness': 0.0, 'moonEnabled': False},
    'lawbot_hq':   {'cloudCoverage': 0.92, 'cloudSpeed': 0.20, 'cloudSharpness': 0.10,
                    'turbidity': 7.5,  'starBrightness': 0.0, 'moonEnabled': False},
    'bossbot_hq':  {'cloudCoverage': 0.99, 'cloudSpeed': 0.10, 'cloudSharpness': 0.05,
                    'turbidity': 8.0,  'starBrightness': 0.0, 'moonEnabled': False},
    'cog':         {'cloudCoverage': 0.75, 'cloudSpeed': 0.50, 'cloudSharpness': 0.20,
                    'turbidity': 6.0,  'starBrightness': 0.0, 'moonEnabled': False},
    # Street variants
    'tt_street':   {'cloudCoverage': 0.40, 'cloudSpeed': 0.68, 'cloudSharpness': 0.55,
                    'turbidity': 2.4,  'starBrightness': 0.0, 'moonEnabled': False},
    'dd_street':   {'cloudCoverage': 0.90, 'cloudSpeed': 1.20, 'cloudSharpness': 0.18,
                    'turbidity': 5.8,  'starBrightness': 0.0, 'moonEnabled': False},
    'dg_street':   {'cloudCoverage': 0.24, 'cloudSpeed': 0.52, 'cloudSharpness': 0.72,
                    'turbidity': 1.8,  'starBrightness': 0.0, 'moonEnabled': False},
    'mm_street':   {'cloudCoverage': 0.52, 'cloudSpeed': 0.88, 'cloudSharpness': 0.42,
                    'turbidity': 3.6,  'starBrightness': 0.0, 'moonEnabled': False},
    'br_street':   {'cloudCoverage': 0.80, 'cloudSpeed': 1.50, 'cloudSharpness': 0.12,
                    'turbidity': 6.2,  'starBrightness': 0.0, 'moonEnabled': False},
    'dl_street':   {'cloudCoverage': 0.20, 'cloudSpeed': 0.22, 'cloudSharpness': 0.48,
                    'turbidity': 1.5,  'starBrightness': 0.88, 'moonEnabled': True,
                    'moonDir': (225, -55, 0)},
    'golf_course': {'cloudCoverage': 0.30, 'cloudSpeed': 0.65, 'cloudSharpness': 0.60,
                    'turbidity': 2.2,  'starBrightness': 0.0, 'moonEnabled': False},
}


# ─────────────────────────────────────────────────────────────────────────────
# ProceduralSky class
# ─────────────────────────────────────────────────────────────────────────────

class ProceduralSky:
    """Manages a GLSL-driven procedural sky sphere.

    One instance per hood / zone.  OutdoorLighting creates and destroys it
    alongside the light rig.
    """

    _TASK_NAME = 'proceduralSkyTask'

    def __init__(self) -> None:
        self._skyNp: NodePath | None = None
        self._time: float = 0.0
        self._activeStyle: str = 'playground'
        self._attached: bool = False

    # ── Public API ────────────────────────────────────────────────────────────

    def attach(self, parent: NodePath, style: str = 'playground') -> None:
        """Create the sky sphere and attach it to *parent* (usually camera)."""
        if self._attached:
            return
        shader = _loadSkyShader()
        if shader is None:
            return  # graceful fallback – sky model will be used instead

        try:
            self._skyNp = _makeSkySphereMesh()
            self._skyNp.reparentTo(parent)
            self._skyNp.setDepthTest(False)
            self._skyNp.setDepthWrite(False)
            self._skyNp.setLightOff(1)
            # Ensure the procedural sky is drawn after any legacy/model sky that
            # might also live in the background bin.
            self._skyNp.setBin('background', 1000)
            self._skyNp.setTwoSided(True)
            self._skyNp.setShader(shader)
            self._skyNp.setShaderAuto(False)

            self._activeStyle = style
            self._attached = True
            self._time = 0.0

            # No update task here – OutdoorLighting's main task calls update().
        except Exception as e:
            import traceback; traceback.print_exc()
            self._skyNp = None

    def update(self, spec: dict, timeOfDay: float = 12.0) -> None:
        """Push zone spec parameters as shader uniforms."""
        if not self._attached or self._skyNp is None or self._skyNp.isEmpty():
            return

        self._time += globalClock.getDt()

        # Resolve sky sub-parameters (check spec first, fall back to defaults).
        style  = self._activeStyle
        skyDef = _ZONE_SKY_DEFAULTS.get(style, _ZONE_SKY_DEFAULTS['playground'])
        cov    = float(spec.get('cloudCoverage',  skyDef.get('cloudCoverage', 0.4)))
        spd    = float(spec.get('cloudSpeed',     skyDef.get('cloudSpeed', 0.6)))
        sharp  = float(spec.get('cloudSharpness', skyDef.get('cloudSharpness', 0.5)))
        turb   = float(spec.get('turbidity',      skyDef.get('turbidity', 2.5)))
        stars  = float(spec.get('starBrightness', skyDef.get('starBrightness', 0.0)))
        moonOn = float(1 if spec.get('moonEnabled', skyDef.get('moonEnabled', False)) else 0)
        moonHpr = spec.get('moonDir', skyDef.get('moonDir', (0, -45, 0)))

        # Sun direction: forward vector of key light (direction light shines).
        keyHpr     = spec.get('keyHpr', (135, -42, 0))
        lightFwd   = _hprToDir(keyHpr[0], keyHpr[1])
        # Sun position in sky = opposite of light direction (world space).
        sunDirWorld = Vec3(-lightFwd.x, -lightFwd.y, -lightFwd.z)

        moonDirWorld = Vec3(0, 0, 1)
        if moonOn > 0.5:
            mfwd = _hprToDir(moonHpr[0], moonHpr[1])
            moonDirWorld = Vec3(-mfwd.x, -mfwd.y, -mfwd.z)

        # Must match camera-space ``vDir`` in the shader (dome is under base.cam).
        sunDirCam  = _dir_world_to_cam(sunDirWorld)
        moonDirCam = _dir_world_to_cam(moonDirWorld)

        keyColor   = Vec4(*spec.get('key', (1, 1, 1, 1)))
        clearColor = spec.get('clearColor', (0.4, 0.6, 0.85, 1.0))
        fogColorV  = spec.get('fogColor', (0.6, 0.7, 0.85, 1.0))
        skyScaleV  = spec.get('skyScale', (1, 1, 1, 1))

        # Derive zenith and horizon colours from clearColor and fogColor.
        # zenith = clearColor (the "perfect overhead blue")
        # horizon = blend clearColor → fogColor
        zenith  = Vec3(clearColor[0], clearColor[1], clearColor[2])
        horizon = Vec3(fogColorV[0] * 0.85, fogColorV[1] * 0.85, fogColorV[2] * 0.85)

        # Day/night: fade stars from *world* sun elevation (stable when camera tilts).
        isDaytime = max(0.0, min(1.0, (sunDirWorld.z + 0.2) * 4.0))
        effectiveStars = stars * (1.0 - isDaytime)

        # Sun blind strength: default 0.85 (strong cinematic glare), clamped 0–1
        blindStr = float(spec.get('sunBlindStrength', 0.85))
        blindStr = max(0.0, min(1.0, blindStr))

        try:
            np = self._skyNp
            np.setShaderInput('sunDir',          sunDirCam)
            np.setShaderInput('sunWorldElev',    float(sunDirWorld.z))
            np.setShaderInput('sunColor',        keyColor)
            np.setShaderInput('zenithColor',     zenith)
            np.setShaderInput('horizonColor',    horizon)
            np.setShaderInput('fogColor',        Vec3(fogColorV[0], fogColorV[1], fogColorV[2]))
            np.setShaderInput('cloudCoverage',   cov)
            np.setShaderInput('cloudSpeed',      spd * _CLOUD_BASE_SPEED)
            np.setShaderInput('cloudSharpness',  sharp)
            np.setShaderInput('turbidity',       turb)
            np.setShaderInput('starBrightness',  effectiveStars)
            np.setShaderInput('moonEnabled',     moonOn)
            np.setShaderInput('moonDir',         moonDirCam)
            np.setShaderInput('moonColor',       Vec4(*spec.get('key', (0.5, 0.6, 1, 1))))
            np.setShaderInput('time',            self._time)
            np.setShaderInput('skyScale',        Vec4(*skyScaleV))
            # New feature uniforms
            np.setShaderInput('sunDiscEnabled',   1.0)
            np.setShaderInput('sunBlindStrength', blindStr)
        except Exception:
            pass

    def setStyle(self, style: str) -> None:
        """Update which zone sky defaults to use."""
        self._activeStyle = style

    def isActive(self) -> bool:
        return self._attached and self._skyNp is not None and not self._skyNp.isEmpty()

    def detach(self) -> None:
        """Remove the sky sphere and clean up."""
        if self._skyNp and not self._skyNp.isEmpty():
            self._skyNp.removeNode()
        self._skyNp   = None
        self._attached = False
        self._time     = 0.0
