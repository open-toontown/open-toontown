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
import sys
from typing import Any

from panda3d.core import (
    AmbientLight,
    BitMask32,
    BillboardEffect,
    CardMaker,
    ColorBlendAttrib,
    ConfigVariableBool,
    ConfigVariableString,
    DepthOffsetAttrib,
    DirectionalLight,
    Filename,
    Fog,
    Geom,
    GeomEnums,
    GeomNode,
    GeomPrimitive,
    GeomTriangles,
    GeomVertexArrayFormat,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexReader,
    GeomVertexWriter,
    LightAttrib,
    Material,
    NodePath,
    PlaneNode,
    PointLight,
    PandaSystem,
    Quat,
    RenderState,
    Shader,
    ShaderAttrib,
    Texture,
    TransparencyAttrib,
    Vec3,
    Vec4,
)

try:
    from otp.avatar import ShadowCaster as _OTPDropshadow
except Exception:
    _OTPDropshadow = None

from direct.showbase.ShowBaseGlobal import globalClock
from direct.task.TaskManagerGlobal import taskMgr
try:
    # Optional: for debug hotkeys (ShowBase provides .accept)
    from direct.showbase.DirectObject import DirectObject  # type: ignore
except Exception:
    DirectObject = None  # type: ignore
try:
    from otp.otpbase import OTPRender as _OTPRender  # type: ignore
except Exception:
    _OTPRender = None  # type: ignore
from panda3d.core import ConfigVariableBool

# `base` can be unavailable early in boot. Resolve safely.
try:
    from direct.showbase.ShowBaseGlobal import base  # type: ignore
except Exception:
    base = None  # type: ignore

if base is None:
    try:
        import builtins
        base = getattr(builtins, 'base', None)  # type: ignore
    except Exception:
        base = None  # type: ignore


def _syncBase() -> None:
    """Refresh the module-global `base` reference.

    This module can be imported before ShowBase/ToonBase is constructed, in which
    case `base` is None at import time. Later, callers wrap begin()/end() in
    try/except (to keep loading robust), which can silently swallow AttributeError
    and make it look like OutdoorLighting never ran. Keep `base` synced at runtime.
    """
    global base
    try:
        if base is not None and getattr(base, 'render', None) is not None:
            return
    except Exception:
        pass
    try:
        from direct.showbase import ShowBaseGlobal as _SBG  # type: ignore
        b = getattr(_SBG, 'base', None)
        if b is not None:
            base = b  # type: ignore
            return
    except Exception:
        pass
    try:
        import builtins
        b = getattr(builtins, 'base', None)
        if b is not None:
            base = b  # type: ignore
    except Exception:
        pass


def _getSettingValue(key: str, default):
    """Fetch a setting from either Settings.getSetting(key, default) or Settings.get(key).
    Falls back to Panda3D ConfigVariable if base.settings is missing or does not have the key.
    """
    _syncBase()
    settings = getattr(base, 'settings', None)
    if settings is not None:
        getter = getattr(settings, 'getSetting', None) or getattr(settings, 'get', None)
        if getter is not None:
            try:
                # Try getting the setting directly first
                v = getter(key)
                if v is not None:
                    return v
            except TypeError:
                try:
                    v = getter(key, default)
                    if v is not None:
                        return v
                except Exception:
                    pass
            except Exception:
                pass
    
    # Fallback to Panda3D ConfigVariable
    if isinstance(default, bool):
        return ConfigVariableBool(key, default).value
    elif isinstance(default, (int, float)):
        return ConfigVariableDouble(key, float(default)).value
    else:
        return ConfigVariableString(key, str(default)).value


def _debugEnabled() -> bool:
    try:
        v = _getSettingValue('lighting-debug', None)
        if v is not None:
            return bool(v)
    except Exception:
        pass
    return ConfigVariableBool('lighting-debug', False).value


def _dbg(msg: str) -> None:
    if not _debugEnabled():
        return
    try:
        print(f"[OutdoorLighting] {msg}")
    except Exception:
        pass


# Bisect defaults back to normal behavior: everything enabled.
_DEFAULT_BISECT_STEP = 2  # TEMP: bisect crash — testing shaderAuto + lights with sky setLightOff(101) fix
_BISECT_STEP = int(_DEFAULT_BISECT_STEP)
_DIR_LIGHT_MODE = 'all'  # 'key' | 'key_fill' | 'all'


def setBisectStep(step: int) -> None:
    """Set the runtime feature-bisect step (script-controlled).

    This intentionally does NOT read PRC/config, so it cannot be overridden by
    external settings while we're isolating artifacts.
    """
    global _BISECT_STEP
    try:
        _BISECT_STEP = max(0, int(step))
    except Exception:
        _BISECT_STEP = 0


def setDirectionalMode(mode: str) -> None:
    """Control which directional lights are spawned (bisect within step 3/4).

    - 'key': key directional only
    - 'key_fill': key + fill
    - 'all': key + fill + rim (if profile has rim)
    """
    global _DIR_LIGHT_MODE
    m = (mode or '').strip().lower()
    _DIR_LIGHT_MODE = m if m in ('key', 'key_fill', 'all') else 'all'


_HOTKEYS_TAG = 'osl_bisect_hotkeys_bound'
_HOTKEYS_ENABLED = False


def _maybeBindBisectHotkeys() -> None:
    """Bind debug hotkeys to control bisect at runtime.

    This avoids needing any external injector. Only binds when lighting-debug is on.
    """
    if (not _HOTKEYS_ENABLED) or (not _debugEnabled()):
        return
    _syncBase()
    if base is None:
        return
    try:
        if getattr(base, 'render', None) is None:
            return
        if base.render.getPythonTag(_HOTKEYS_TAG):
            return
    except Exception:
        pass

    # ShowBase implements .accept. Bind on base itself.
    try:
        accept = getattr(base, 'accept', None)
        if accept is None:
            return
    except Exception:
        return

    def _set_step(s: int):
        setBisectStep(s)
        _dbg(f"hotkey: setBisectStep({s}) (re-enter zone to apply)")

    def _cycle_dir():
        global _DIR_LIGHT_MODE
        order = ('key', 'key_fill', 'all')
        try:
            idx = order.index(_DIR_LIGHT_MODE)
        except Exception:
            idx = 2
        _DIR_LIGHT_MODE = order[(idx + 1) % len(order)]
        _dbg(f"hotkey: setDirectionalMode('{_DIR_LIGHT_MODE}') (re-enter zone to apply)")

    try:
        # Bisect steps 0-9 on number keys.
        for s in range(10):
            accept(str(s), _set_step, [s])
        # Directional mode cycle.
        accept('f6', _cycle_dir)
        accept('shift-f6', _cycle_dir)
        try:
            base.render.setPythonTag(_HOTKEYS_TAG, True)
        except Exception:
            pass
        _dbg("bound bisect hotkeys: [0-9]=step, [F6]=cycle dir mode key->key_fill->all")
    except Exception:
        pass


def _bisectStep() -> int:
    """Runtime subsystem bisect for isolating rendering artifacts.

    Default: `_DEFAULT_BISECT_STEP` (script-controlled).

    Enable order:
      0: light rig only
      1: + fog + sky tint + background clear color
      2: + procedural sky
      3: + postprocess bloom
      4: + godrays overlay
      5: + water shader/reflection
    """
    try:
        return int(_BISECT_STEP)
    except Exception:
        return int(_DEFAULT_BISECT_STEP)


def _bisectAllows(step: int) -> bool:
    return _bisectStep() >= step


def _dbgBisectState() -> None:
    if not _debugEnabled():
        return
    s = _bisectStep()
    _dbg(
        "bisect "
        f"step={s} "
        f"shaderAuto={_bisectAllows(1)} "
        f"lights={_bisectAllows(2)} "
        f"sunNoShadows={_bisectAllows(3)} "
        f"sunShadows={_bisectAllows(4)} "
        f"fog_bg_tint={_bisectAllows(5)} "
        f"proceduralSky={_bisectAllows(6)} "
        f"bloom={_bisectAllows(7)} "
        f"godrays={_bisectAllows(8)} "
        f"water={_bisectAllows(9)}"
    )


def _spawnShadowTestScene() -> None:
    """Spawn a simple cube+ground that should cast a visible shadow."""
    if not _debugEnabled():
        return
    # The shadow test scene is useful while developing shadow-map logic, but
    # should never appear in normal gameplay even if lighting-debug is enabled.
    # Enable explicitly via PRC or settings.
    try:
        if not ConfigVariableBool('lighting-shadow-test-scene', False).value:
            return
    except Exception:
        return
    _syncBase()
    try:
        if base is None or getattr(base, 'render', None) is None:
            return
    except Exception:
        return
    try:
        if base.render.getPythonTag('osl_shadow_test_spawned'):
            return
    except Exception:
        pass

    try:
        root = base.render.attachNewNode('OutdoorLightingShadowTest')
        try:
            root.wrtReparentTo(base.camera)
        except Exception:
            root.reparentTo(base.camera)
        root.setPos(0, 25, -2)

        cm = CardMaker('shadowTestGround')
        cm.setFrame(-10, 10, -10, 10)
        ground = root.attachNewNode(cm.generate())
        ground.setP(-90)
        ground.setZ(0)
        ground.setColor(0.6, 0.6, 0.6, 1)
        ground.setShaderAuto()

        # Procedural cube (no external model dependency).
        try:
            fmt = GeomVertexFormat.getV3n3()
            vdata = GeomVertexData('shadowTestCube', fmt, Geom.UHStatic)
            vwriter = GeomVertexWriter(vdata, 'vertex')
            nwriter = GeomVertexWriter(vdata, 'normal')

            # Build a cube with 6 faces (24 verts so normals are per-face).
            # Cube centered at origin, size 2.
            faces = [
                (Vec3(0, 0, 1), [Vec3(-1, -1, 1), Vec3(1, -1, 1), Vec3(1, 1, 1), Vec3(-1, 1, 1)]),   # top
                (Vec3(0, 0, -1), [Vec3(-1, 1, -1), Vec3(1, 1, -1), Vec3(1, -1, -1), Vec3(-1, -1, -1)]), # bottom
                (Vec3(0, 1, 0), [Vec3(-1, 1, 1), Vec3(1, 1, 1), Vec3(1, 1, -1), Vec3(-1, 1, -1)]),   # front
                (Vec3(0, -1, 0), [Vec3(1, -1, 1), Vec3(-1, -1, 1), Vec3(-1, -1, -1), Vec3(1, -1, -1)]), # back
                (Vec3(1, 0, 0), [Vec3(1, 1, 1), Vec3(1, -1, 1), Vec3(1, -1, -1), Vec3(1, 1, -1)]),   # right
                (Vec3(-1, 0, 0), [Vec3(-1, -1, 1), Vec3(-1, 1, 1), Vec3(-1, 1, -1), Vec3(-1, -1, -1)]), # left
            ]

            tris = GeomTriangles(Geom.UHStatic)
            vidx = 0
            for nrm, verts in faces:
                for v in verts:
                    vwriter.addData3(v)
                    nwriter.addData3(nrm)
                # two triangles per quad (0,1,2) and (0,2,3)
                tris.addVertices(vidx + 0, vidx + 1, vidx + 2)
                tris.addVertices(vidx + 0, vidx + 2, vidx + 3)
                vidx += 4

            geom = Geom(vdata)
            geom.addPrimitive(tris)
            gnode = GeomNode('shadowTestCubeGeom')
            gnode.addGeom(geom)
            cube = root.attachNewNode(gnode)
            cube.setPos(0, 0, 2.5)
            cube.setScale(2)
            cube.setColor(1, 0.2, 0.2, 1)
            cube.setShaderAuto()
        except Exception as e:
            _dbg(f"shadow test cube build failed: {e!r}")

        base.render.setShaderAuto()
        base.render.setPythonTag('osl_shadow_test_spawned', True)
        _dbg("spawned shadow test scene near camera")
    except Exception as e:
        _dbg(f"shadow test spawn failed: {e!r}")


_NORMALS_TAG = 'osl_normals_generated'


def preprocessGeometry(root: NodePath) -> None:
    """Prepare geometry before flattening.
    
    Sets setLightOff(101) on foliage/trees so they are not merged with lit
    geometry during flattenMedium, preserving their unlit status.
    """
    if root is None or root.isEmpty():
        return
    try:
        nodes = root.findAllMatches('**')
        for i in range(nodes.getNumPaths()):
            np = nodes.getPath(i)
            if _isFoliageOrTree(np):
                try:
                    np.setLightOff(101)
                except Exception:
                    pass
    except Exception:
        pass


def _ensureNormals(root: NodePath) -> None:
    """Generate vertex normals for geometry that has none or has zeroed normals.

    Some zone meshes in this project ship without a 'normal' column or have zeroed
    normals after flattening, which makes all lighting/shadows appear flat or pitch black.
    This generates/recomputes normals for those geoms.
    """
    if root is None or root.isEmpty():
        return
    try:
        if root.getPythonTag(_NORMALS_TAG):
            return
    except Exception:
        pass

    nodes = root.findAllMatches('**/+GeomNode')
    if nodes.getNumPaths() <= 0:
        return

    _dbg(f"Scanning and generating normals for {nodes.getNumPaths()} GeomNodes...")

    def _formatWithNormals(old_fmt: GeomVertexFormat) -> GeomVertexFormat:
        # Copy all arrays/columns and append a normal column to the first array.
        nf = GeomVertexFormat()
        added = False
        for ai in range(old_fmt.getNumArrays()):
            old_arr = old_fmt.getArray(ai)
            arr = GeomVertexArrayFormat()
            for ci in range(old_arr.getNumColumns()):
                col = old_arr.getColumn(ci)
                arr.addColumn(col.getName(), col.getNumComponents(),
                               col.getNumericType(), col.getContents())
            if not added:
                arr.addColumn('normal', 3, GeomEnums.NT_float32, GeomEnums.C_normal)
                added = True
            nf.addArray(arr)
        return GeomVertexFormat.registerFormat(nf)

    def _vdataWithFormat(old_vdata: GeomVertexData, new_fmt: GeomVertexFormat) -> GeomVertexData | None:
        try:
            if hasattr(old_vdata, 'convertTo'):
                return old_vdata.convertTo(new_fmt)
        except Exception:
            pass

        try:
            num_rows = old_vdata.getNumRows()
        except Exception:
            return None

        try:
            new_vdata = GeomVertexData(old_vdata)
            new_vdata.setFormat(new_fmt)
            new_vdata.setNumRows(num_rows)
        except Exception:
            try:
                new_vdata = GeomVertexData('with_normals', new_fmt, old_vdata.getUsageHint())
                new_vdata.setNumRows(num_rows)
            except Exception:
                return None

        try:
            old_fmt = old_vdata.getFormat()
            for ai in range(old_fmt.getNumArrays()):
                arr = old_fmt.getArray(ai)
                for ci in range(arr.getNumColumns()):
                    col = arr.getColumn(ci)
                    name = col.getName()
                    if name == 'normal':
                        continue
                    try:
                        if not old_vdata.hasColumn(name) or not new_vdata.hasColumn(name):
                            continue
                    except Exception:
                        continue

                    r = GeomVertexReader(old_vdata, name)
                    w = GeomVertexWriter(new_vdata, name)
                    comps = int(col.getNumComponents())
                    for row in range(num_rows):
                        r.setRow(row)
                        w.setRow(row)
                        if comps == 1:
                            w.setData1(r.getData1())
                        elif comps == 2:
                            w.setData2(r.getData2())
                        elif comps == 3:
                            w.setData3(r.getData3())
                        else:
                            w.setData4(r.getData4())
        except Exception:
            pass

        return new_vdata

    # Iterate each Geom and compute normals.
    for ni in range(nodes.getNumPaths()):
        np = nodes.getPath(ni)
        gnode = np.node()
        if not isinstance(gnode, GeomNode):
            continue
        for gi in range(gnode.getNumGeoms()):
            try:
                geom = gnode.modifyGeom(gi)
            except Exception:
                continue
            if not isinstance(geom, Geom):
                continue
            try:
                vdata = geom.modifyVertexData()
            except Exception:
                continue
            if vdata is None:
                continue

            try:
                if vdata.hasColumn('normal'):
                    continue
            except Exception:
                continue

            try:
                new_fmt = _formatWithNormals(vdata.getFormat())
                new_vdata = _vdataWithFormat(vdata, new_fmt)
                if new_vdata is None:
                    continue
                geom.setVertexData(new_vdata)
                vdata = geom.modifyVertexData()
            except Exception:
                continue

            try:
                num_rows = vdata.getNumRows()
            except Exception:
                continue
            if num_rows <= 0:
                continue

            # Accumulate normals in Python list.
            acc = [Vec3(0, 0, 0) for _ in range(num_rows)]
            vr = GeomVertexReader(vdata, 'vertex')

            def _getPos(row: int) -> Vec3:
                vr.setRow(row)
                return vr.getData3()

            try:
                for pi in range(geom.getNumPrimitives()):
                    prim = geom.getPrimitive(pi)
                    if prim is None:
                        continue
                    try:
                        decomp = prim.decompose()
                    except Exception:
                        decomp = prim
                    try:
                        decomp = decomp.decompose()
                    except Exception:
                        pass
                    try:
                        npr = decomp.getNumPrimitives()
                    except Exception:
                        npr = 0
                    for t in range(npr):
                        start = decomp.getPrimitiveStart(t)
                        end = decomp.getPrimitiveEnd(t)
                        if end - start < 3:
                            continue
                        try:
                            i0 = decomp.getVertex(start + 0)
                            i1 = decomp.getVertex(start + 1)
                            i2 = decomp.getVertex(start + 2)
                        except Exception:
                            continue
                        if i0 >= num_rows or i1 >= num_rows or i2 >= num_rows:
                            continue
                        p0 = _getPos(i0)
                        p1 = _getPos(i1)
                        p2 = _getPos(i2)
                        n = (p1 - p0).cross(p2 - p0)
                        if n.lengthSquared() <= 1e-12:
                            continue
                        acc[i0] += n
                        acc[i1] += n
                        acc[i2] += n
            except Exception:
                continue

            vw = GeomVertexWriter(vdata, 'normal')
            try:
                for r in range(num_rows):
                    n = acc[r]
                    if n.lengthSquared() <= 1e-12:
                        n = Vec3(0, 0, 1)
                    else:
                        n.normalize()
                    vw.setRow(r)
                    vw.setData3(n)
            except Exception:
                pass

    try:
        root.setPythonTag(_NORMALS_TAG, True)
    except Exception:
        pass


def _forceShaderRegen(np: NodePath) -> None:
    """Force shader generator to rebuild shaders after vertex format changes."""
    if np is None or np.isEmpty():
        return
    try:
        np.clearShader()
    except Exception:
        pass
    try:
        np.setShaderAuto()
    except Exception:
        pass


def _forceShadersOnSubtree(root: NodePath) -> None:
    """Clear shader/shader-off attribs that can block auto-shaders (and shadows)."""
    if root is None or root.isEmpty():
        return
    try:
        nodes = root.findAllMatches('**')
        for i in range(nodes.getNumPaths()):
            np = nodes.getPath(i)
            try:
                # Clear explicit shader attribs (including shader-off).
                try:
                    np.clearAttrib(ShaderAttrib.getClassType())
                except Exception:
                    pass
                # Clear any fixed shader and re-enable auto.
                try:
                    np.clearShader()
                except Exception:
                    pass
                try:
                    np.setShaderAuto()
                except Exception:
                    pass
            except Exception:
                pass
    except Exception:
        pass

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
        'ambient':          (0.32, 0.38, 0.54, 1.0),
        'key':              (1.45, 1.28, 0.96, 1.0),
        'keyHpr':           (135, -42, 0),
        'fill':             (0.32, 0.42, 0.62, 1.0),
        'fillHpr':          (-45, -18, 0),
        'rim':              (0.18, 0.24, 0.40, 1.0),
        'rimHpr':           (315, -30, 0),
        'shadowCaster':     True,
        'shadowRes':        4096,
        'shadowArea':       160,
        'shadowResScale':   0.75,
        'shadowAreaScale':  1.40,
        'shadowFollowDist': 280.0,
        'shadowDarknessFloor': 0.22,
        'fogColor':         (0.72, 0.80, 0.92, 1.0),
        'fogNear':          110.0,
        'fogFar':           560.0,
        'fogExponent':      None,
        'skyScale':         (1.04, 1.01, 0.91, 1.0),
        'clearColor':       (0.50, 0.68, 0.90, 1.0),
        'sunUV':            (0.65, 0.78),
        'rayColor':         (1.00, 0.94, 0.68, 1.0),
        'rayIntensity':     0.48,
        'bloomIntensity':   0.40,
        'bloomThreshold':   0.56,
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
        'ambient':          (0.28, 0.34, 0.48, 1.0),
        'key':              (1.38, 1.22, 0.90, 1.0),
        'keyHpr':           (140, -40, 0),
        'fill':             (0.30, 0.40, 0.58, 1.0),
        'fillHpr':          (-50, -20, 0),
        'rim':              (0.15, 0.22, 0.38, 1.0),
        'rimHpr':           (310, -28, 0),
        'shadowCaster':     True,
        'shadowRes':        2048,
        'shadowArea':       140,
        'shadowResScale':   1.00,
        'shadowAreaScale':  1.20,
        'shadowFollowDist': 220.0,
        'shadowDarknessFloor': 0.20,
        'fogColor':         (0.70, 0.78, 0.90, 1.0),
        'fogNear':          95.0,
        'fogFar':           480.0,
        'fogExponent':      None,
        'skyScale':         (1.04, 1.01, 0.91, 1.0),
        'clearColor':       (0.48, 0.66, 0.88, 1.0),
        'sunUV':            (0.65, 0.78),
        'rayColor':         (1.00, 0.92, 0.66, 1.0),
        'rayIntensity':     0.38,
        'bloomIntensity':   0.36,
        'bloomThreshold':   0.58,
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
        'ambient':          (0.28, 0.36, 0.56, 1.0),
        'key':              (1.48, 1.36, 1.10, 1.0),
        'keyHpr':           (170, -68, 0),
        'fill':             (0.34, 0.46, 0.68, 1.0),
        'fillHpr':          (-10, -22, 0),
        'rim':              (0.18, 0.28, 0.48, 1.0),
        'rimHpr':           (0,    55,  0),
        'shadowCaster':     True,
        'shadowRes':        4096,
        'shadowArea':       155,
        'shadowResScale':   1.00,
        'shadowAreaScale':  0.95,
        'shadowFollowDist': 260.0,
        'shadowDarknessFloor': 0.22,
        'fogColor':         (0.62, 0.80, 1.00, 1.0),
        'fogNear':          145.0,
        'fogFar':           660.0,
        'fogExponent':      None,
        'skyScale':         (0.88, 0.96, 1.14, 1.0),
        'clearColor':       (0.36, 0.62, 1.00, 1.0),
        'sunUV':            (0.54, 0.90),
        'rayColor':         (1.00, 1.00, 0.88, 1.0),
        'rayIntensity':     0.68,
        'bloomIntensity':   0.52,
        'bloomThreshold':   0.52,
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
        'ambient':          (0.24, 0.32, 0.50, 1.0),
        'key':              (1.40, 1.28, 1.04, 1.0),
        'keyHpr':           (172, -66, 0),
        'fill':             (0.30, 0.42, 0.62, 1.0),
        'fillHpr':          (-12, -20, 0),
        'rim':              (0.15, 0.24, 0.42, 1.0),
        'rimHpr':           (0,    52,  0),
        'shadowCaster':     True,
        'shadowRes':        2048,
        'shadowArea':       130,
        'shadowResScale':   1.00,
        'shadowAreaScale':  1.10,
        'shadowFollowDist': 220.0,
        'shadowDarknessFloor': 0.20,
        'fogColor':         (0.60, 0.78, 0.98, 1.0),
        'fogNear':          125.0,
        'fogFar':           580.0,
        'fogExponent':      None,
        'skyScale':         (0.88, 0.96, 1.14, 1.0),
        'clearColor':       (0.34, 0.60, 0.98, 1.0),
        'sunUV':            (0.54, 0.88),
        'rayColor':         (1.00, 1.00, 0.88, 1.0),
        'rayIntensity':     0.60,
        'bloomIntensity':   0.46,
        'bloomThreshold':   0.55,
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
        'ambient':          (0.11, 0.15, 0.32, 1.0),
        'key':              (0.58, 0.65, 0.92, 1.0),
        'keyHpr':           (225, -55, 0),
        'fill':             (0.07, 0.10, 0.24, 1.0),
        'fillHpr':          (45,  -15, 0),
        'rim':              (0.38, 0.46, 0.72, 1.0),
        'rimHpr':           (220, -50, 0),
        'shadowCaster':     True,
        'shadowRes':        2048,
        'shadowArea':       170,
        'shadowResScale':   0.75,
        'shadowAreaScale':  1.45,
        'shadowFollowDist': 260.0,
        'shadowDarknessFloor': 0.14,
        'fogColor':         (0.07, 0.10, 0.22, 1.0),
        'fogNear':          0.0,
        'fogFar':           None,
        'fogExponent':      0.004,
        'skyScale':         (0.42, 0.48, 0.74, 1.0),
        'clearColor':       (0.04, 0.06, 0.14, 1.0),
        'sunUV':            (0.30, 0.82),
        'rayColor':         (0.58, 0.70, 1.00, 1.0),
        'rayIntensity':     0.42,
        'bloomIntensity':   0.32,
        'bloomThreshold':   0.62,
        'exposure':         1.30,
        'hasWater':         False,
        'dayNightEnabled':  True,
        'cloudCoverage':    0.22,
        'cloudSpeed':       0.25,
        'cloudSharpness':   0.50,
        'turbidity':        1.5,
        'starBrightness':   0.96,
        'moonEnabled':      True,
        'moonDir':          (225, -55, 0),
    },

    # ── DL streets ────────────────────────────────────────────────────────────
    'dl_street': {
        'ambient':          (0.09, 0.13, 0.28, 1.0),
        'key':              (0.54, 0.62, 0.86, 1.0),
        'keyHpr':           (225, -52, 0),
        'fill':             (0.06, 0.09, 0.20, 1.0),
        'fillHpr':          (42,  -14, 0),
        'rim':              (0.35, 0.44, 0.68, 1.0),
        'rimHpr':           (222, -48, 0),
        'shadowCaster':     True,
        'shadowRes':        2048,
        'shadowArea':       140,
        'shadowResScale':   0.75,
        'shadowAreaScale':  1.30,
        'shadowFollowDist': 220.0,
        'shadowDarknessFloor': 0.12,
        'fogColor':         (0.06, 0.09, 0.20, 1.0),
        'fogNear':          0.0,
        'fogFar':           None,
        'fogExponent':      0.005,
        'skyScale':         (0.42, 0.48, 0.74, 1.0),
        'clearColor':       (0.04, 0.06, 0.14, 1.0),
        'sunUV':            (0.30, 0.80),
        'rayColor':         (0.56, 0.68, 1.00, 1.0),
        'rayIntensity':     0.36,
        'bloomIntensity':   0.28,
        'bloomThreshold':   0.65,
        'exposure':         1.32,
        'hasWater':         False,
        'dayNightEnabled':  True,
        'cloudCoverage':    0.20,
        'cloudSpeed':       0.22,
        'cloudSharpness':   0.48,
        'turbidity':        1.5,
        'starBrightness':   0.92,
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
        'ambient':          (0.34, 0.40, 0.54, 1.0),
        'key':              (1.22, 1.14, 0.94, 1.0),
        'keyHpr':           (118, -52, 0),
        'fill':             (0.26, 0.34, 0.48, 1.0),
        'fillHpr':          (-48, -42, 0),
        'rim':              (0.14, 0.20, 0.34, 1.0),
        'rimHpr':           (300, -30, 0),
        'shadowCaster':     True,
        'shadowRes':        2048,
        'shadowArea':       180,
        'shadowResScale':   0.90,
        'shadowAreaScale':  1.20,
        'shadowFollowDist': 240.0,
        'shadowDarknessFloor': 0.22,
        'fogColor':         (0.65, 0.78, 0.94, 1.0),
        'fogNear':          120.0,
        'fogFar':           560.0,
        'fogExponent':      None,
        'skyScale':         (1.00, 1.00, 1.00, 1.0),
        'clearColor':       (0.42, 0.62, 0.84, 1.0),
        'sunUV':            (0.62, 0.76),
        'rayColor':         (1.00, 0.95, 0.74, 1.0),
        'rayIntensity':     0.38,
        'bloomIntensity':   0.36,
        'bloomThreshold':   0.58,
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
        'ambient':          (0.36, 0.36, 0.48, 1.0),
        'key':              (1.20, 1.12, 0.96, 1.0),
        'keyHpr':           (105, -48, 0),
        'fill':             (0.28, 0.34, 0.46, 1.0),
        'fillHpr':          (-55, -38, 0),
        'rim':              (0.12, 0.18, 0.30, 1.0),
        'rimHpr':           (285, -28, 0),
        'shadowCaster':     True,
        'shadowRes':        2048,
        'shadowArea':       180,
        'shadowResScale':   0.90,
        'shadowAreaScale':  1.20,
        'shadowFollowDist': 240.0,
        'shadowDarknessFloor': 0.24,
        'fogColor':         (0.68, 0.80, 0.94, 1.0),
        'fogNear':          120.0,
        'fogFar':           560.0,
        'fogExponent':      None,
        'skyScale':         (1.00, 1.00, 1.00, 1.0),
        'clearColor':       (0.44, 0.64, 0.86, 1.0),
        'sunUV':            (0.58, 0.74),
        'rayColor':         (1.00, 0.95, 0.80, 1.0),
        'rayIntensity':     0.32,
        'bloomIntensity':   0.30,
        'bloomThreshold':   0.60,
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
        (0.0,  {'ambient': (0.08,0.12,0.28,1), 'key': (0.20,0.24,0.52,1),
                'keyHpr': (225,-38,0), 'fill': (0.05,0.08,0.18,1),
                'rim': (0.28,0.36,0.68,1), 'rimHpr': (222,-35,0),
                'fogColor': (0.08,0.12,0.28,1), 'fogNear': 30.0, 'fogFar': 340.0,
                'clearColor': (0.06,0.09,0.22,1), 'skyScale': (0.42,0.48,0.75,1),
                'rayColor': (0.58,0.70,1.00,1), 'rayIntensity': 0.22,
                'bloomIntensity': 0.18, 'shadowCaster': False,
                'starBrightness': 0.96, 'moonEnabled': True, 'moonDir': (180,-52,0),
                'exposure': 1.40}),
        (5.5,  {'ambient': (0.10,0.11,0.22,1), 'key': (0.28,0.22,0.46,1),
                'keyHpr': (80,-5,0), 'fill': (0.08,0.08,0.18,1),
                'rim': (0.24,0.20,0.46,1), 'rimHpr': (82,-4,0),
                'fogColor': (0.14,0.18,0.36,1), 'fogNear': 50.0, 'fogFar': 370.0,
                'clearColor': (0.12,0.15,0.30,1), 'skyScale': (0.52,0.55,0.80,1),
                'rayColor': (0.70,0.62,0.90,1), 'rayIntensity': 0.12,
                'bloomIntensity': 0.14, 'shadowCaster': False,
                'starBrightness': 0.32, 'moonEnabled': True, 'moonDir': (265,-38,0),
                'exposure': 1.25}),
        (6.5,  {'ambient': (0.26,0.18,0.20,1), 'key': (1.00,0.54,0.32,1),
                'keyHpr': (90,-10,0), 'fill': (0.22,0.16,0.32,1),
                'rim': (0.82,0.40,0.20,1), 'rimHpr': (88,-8,0),
                'fogColor': (0.88,0.56,0.35,1), 'fogNear': 70.0, 'fogFar': 420.0,
                'clearColor': (0.78,0.44,0.25,1), 'skyScale': (1.22,0.82,0.60,1),
                'rayColor': (1.00,0.64,0.30,1), 'rayIntensity': 0.56,
                'bloomIntensity': 0.50, 'shadowCaster': True,
                'starBrightness': 0.0, 'exposure': 1.05}),
        (9.0,  {'ambient': (0.28,0.32,0.46,1), 'key': (1.28,1.10,0.84,1),
                'keyHpr': (120,-36,0), 'fill': (0.28,0.36,0.52,1), 'rim': (0.14,0.20,0.34,1),
                'rimHpr': (300,-28,0),
                'fogColor': (0.70,0.80,0.94,1), 'fogNear': 100.0, 'fogFar': 500.0,
                'clearColor': (0.50,0.68,0.90,1), 'skyScale': (1.04,1.00,0.92,1),
                'rayColor': (1.00,0.90,0.64,1), 'rayIntensity': 0.36,
                'bloomIntensity': 0.36, 'shadowCaster': True,
                'starBrightness': 0.0, 'exposure': 1.00}),
        (12.0, {'ambient': (0.34,0.40,0.54,1), 'key': (1.48,1.32,1.02,1),
                'keyHpr': (180,-86,0), 'fill': (0.34,0.44,0.62,1), 'rim': (0.18,0.24,0.40,1),
                'rimHpr': (315,-30,0),
                'fogColor': (0.76,0.85,0.96,1), 'fogNear': 115.0, 'fogFar': 580.0,
                'clearColor': (0.52,0.72,0.96,1), 'skyScale': (1.00,1.00,0.96,1),
                'rayColor': (1.00,0.96,0.80,1), 'rayIntensity': 0.34,
                'bloomIntensity': 0.42, 'shadowCaster': True,
                'starBrightness': 0.0, 'exposure': 1.00}),
        (15.0, {'ambient': (0.32,0.38,0.54,1), 'key': (1.45,1.28,0.96,1),
                'keyHpr': (135,-42,0), 'fill': (0.32,0.42,0.62,1), 'rim': (0.18,0.24,0.40,1),
                'rimHpr': (315,-30,0),
                'fogColor': (0.72,0.80,0.92,1), 'fogNear': 110.0, 'fogFar': 560.0,
                'clearColor': (0.50,0.68,0.90,1), 'skyScale': (1.04,1.01,0.91,1),
                'rayColor': (1.00,0.94,0.68,1), 'rayIntensity': 0.48,
                'bloomIntensity': 0.40, 'shadowCaster': True,
                'starBrightness': 0.0, 'exposure': 1.00}),
        (17.5, {'ambient': (0.36,0.26,0.28,1), 'key': (1.32,0.80,0.36,1),
                'keyHpr': (230,-22,0), 'fill': (0.26,0.20,0.40,1),
                'rim': (0.90,0.44,0.18,1), 'rimHpr': (228,-18,0),
                'fogColor': (0.90,0.62,0.36,1), 'fogNear': 60.0, 'fogFar': 410.0,
                'clearColor': (0.84,0.54,0.26,1), 'skyScale': (1.24,0.86,0.60,1),
                'rayColor': (1.00,0.66,0.28,1), 'rayIntensity': 0.70,
                'bloomIntensity': 0.60, 'shadowCaster': True,
                'starBrightness': 0.0, 'exposure': 1.02}),
        (19.0, {'ambient': (0.26,0.16,0.32,1), 'key': (0.70,0.35,0.48,1),
                'keyHpr': (262,-8,0), 'fill': (0.18,0.12,0.32,1),
                'rim': (0.56,0.25,0.40,1), 'rimHpr': (260,-5,0),
                'fogColor': (0.44,0.22,0.40,1), 'fogNear': 30.0, 'fogFar': 310.0,
                'clearColor': (0.34,0.16,0.36,1), 'skyScale': (0.92,0.60,0.82,1),
                'rayColor': (0.90,0.46,0.72,1), 'rayIntensity': 0.40,
                'bloomIntensity': 0.46, 'shadowCaster': False,
                'starBrightness': 0.16, 'moonEnabled': False, 'exposure': 1.18}),
        (21.0, {'ambient': (0.08,0.10,0.24,1), 'key': (0.20,0.26,0.54,1),
                'keyHpr': (225,-40,0), 'fill': (0.05,0.07,0.16,1),
                'rim': (0.28,0.34,0.66,1), 'rimHpr': (222,-38,0),
                'fogColor': (0.07,0.10,0.24,1), 'fogNear': 30.0, 'fogFar': 340.0,
                'clearColor': (0.06,0.08,0.20,1), 'skyScale': (0.40,0.44,0.72,1),
                'rayColor': (0.56,0.68,1.00,1), 'rayIntensity': 0.24,
                'bloomIntensity': 0.18, 'shadowCaster': False,
                'starBrightness': 0.92, 'moonEnabled': True, 'moonDir': (90,-55,0),
                'exposure': 1.36}),
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
        # Fallback to the canonical branch zone (e.g. street segment zone 4101 -> branch 4100)
        branchZone = zoneId - (zoneId % 100)
        res = _ZONE_ID_MAP.get(branchZone)
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
_activeGeom: NodePath | None = None

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
_sunDirWorld: Vec3 | None = None

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
    # Additional Toontown prop/DNA names that serve as light sources
    'prop_street_lamp', 'prop_gas_lamp', 'streetlamp_post',
    'light_post', 'prop_lightpost', 'lamp_base', 'glowing', 'glow',
    'firefly', 'moonflower', 'lanternpost', 'hanging_lamp', 'ceiling_light',
    'wall_light', 'window_light', 'neon', 'sign_light',
)
_LAMP_LIGHT_LIMIT = 80   # max point lights to create (performance guard)

# IMPORTANT:
# In this codebase, BitMask32.bit(5) is OTPRender.EnviroCameraBitmask and
# `OTPBase.setupEnviroCamera()` does `render.hide(EnviroCameraBitmask)`.
# Using bit(5) for shadow cameras makes the shadow pass see an empty scene.
_SHADOW_CAM_MASK = getattr(_OTPRender, 'ShadowCameraBitmask', BitMask32.bit(2))

# Temporary safety: do not rely on ShadowCameraBitmask-only visibility for the
# shadow map camera. Some scenes use draw masks in ways that can make the
# shadow pass see nothing when restricted to a single bit. We keep the mask
# constant for future use, but avoid forcing the shadow camera to use it.

_SHADER_DIR_CANDIDATES = (
    os.path.join(os.path.dirname(__file__), '..', 'shaders'),
    os.path.join(os.path.dirname(__file__), 'shaders'),
    os.path.join(os.path.dirname(__file__), '..', '..', 'shaders'),
)
_SHADER_DIR = next((d for d in _SHADER_DIR_CANDIDATES if os.path.exists(d)), _SHADER_DIR_CANDIDATES[0])
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
    _syncBase()
    if _OUTDOOR_SHADER_BISECT_LEVEL < 1:
        return False
    try:
        val = _getSettingValue('want-modern-outdoor-lighting', None)
        if val is not None:
            return bool(val)
    except Exception:
        pass
    return ConfigVariableBool('want-modern-outdoor-lighting', True).value


def _settingsBool(key: str, default: bool) -> bool:
    try:
        return bool(_getSettingValue(key, default))
    except Exception:
        return default


def _settingsFloat(key: str, default: float) -> float:
    try:
        return float(_getSettingValue(key, default))
    except Exception:
        return default


def _settingsStr(key: str, default: str) -> str:
    try:
        v = _getSettingValue(key, default)
        return str(v) if v is not None else default
    except Exception:
        return default


def _wantDayNight() -> bool:
    try:
        val = _getSettingValue('want-day-night-cycle', None)
        if val is not None:
            return bool(val)
    except Exception:
        pass
    return ConfigVariableBool('want-day-night-cycle', False).value


def _wantBloom() -> bool:
    return _bisectAllows(7) and _settingsBool('lighting-bloom-enabled', True)


def _wantWater() -> bool:
    return _settingsBool('want-water-reflections', True)


_cachedSupportsBasicShaders: bool | None = None


def _supportsBasicShaders() -> bool:
    """Returns whether the active GSG reports basic shader support.

    Shadow mapping requires shader support; when unavailable, we fall back to
    OTP drop-shadows (blob shadows) instead of attempting shadow buffers.
    """
    global _cachedSupportsBasicShaders
    if _cachedSupportsBasicShaders is not None:
        return _cachedSupportsBasicShaders
    
    # FIRST: If we have an active GSG, it is the absolute source of truth.
    # If the C++ engine reports False (due to e.g. missing Cg support in build),
    # we MUST respect it because the C++ engine won't allocate shadow buffers.
    try:
        if getattr(base, 'win', None):
            gsg = base.win.getGsg()
            if gsg:
                supports_basic = bool(gsg.getSupportsBasicShaders())
                _cachedSupportsBasicShaders = supports_basic
                if _debugEnabled():
                    _dbg(f"Active GSG reports getSupportsBasicShaders() = {supports_basic}")
                return supports_basic
    except Exception:
        pass
    
    # Check Panda3D version - 1.11.0 has known shader API bugs
    panda_version = ''
    try:
        from panda3d.core import PandaSystem
        panda_version = PandaSystem.getGlobalPtr().getVersionString()
        if _debugEnabled():
            _dbg(f"Panda3D version: {panda_version}")
    except Exception:
        pass
    
    # SECOND: Standard detection for other versions / fallback when GSG is not yet open
    gpu_vendor = ''
    gpu_renderer = ''
    
    try:
        if getattr(base, 'win', None):
            gsg = base.win.getGsg()
            if gsg:
                for vendor_attr in ['getVendor', 'getDriverVendor']:
                    try:
                        gpu_vendor = str(getattr(gsg, vendor_attr, lambda: '')())
                        if gpu_vendor and gpu_vendor != 'unknown':
                            break
                    except Exception:
                        pass
                
                for renderer_attr in ['getRenderer', 'getDriverRenderer']:
                    try:
                        gpu_renderer = str(getattr(gsg, renderer_attr, lambda: '')())
                        if gpu_renderer and gpu_renderer != 'unknown':
                            break
                    except Exception:
                        pass
                        
                if _debugEnabled():
                    _dbg(f"GPU Detection: vendor='{gpu_vendor}', renderer='{gpu_renderer}'")
    except Exception as e:
        if _debugEnabled():
            _dbg(f"GPU detection error: {e}")
    
    # NVIDIA RTX GPUs definitely support shaders physically
    if 'NVIDIA' in gpu_vendor and 'RTX' in gpu_renderer:
        if _debugEnabled():
            _dbg(f"NVIDIA RTX GPU DETECTED: {gpu_renderer}")
        return True
    
    is_modern_gpu = ('NVIDIA' in gpu_vendor or 'AMD' in gpu_vendor or 'Intel' in gpu_vendor)
    if is_modern_gpu:
        return True
    
    # Optimistic default when GSG is not yet initialized
    if gpu_vendor or gpu_renderer:
        return True
    
    return True


def _wantDynamicShadows() -> bool:
    """Determine if dynamic shadow maps should be used.
    
    ULTRA-AGGRESSIVE VERSION: Always enable shadows for modern GPUs.
    """
    # Check user preference first
    want_shadows = _settingsBool('dynamic-shadows', True)
    if not want_shadows:
        if _debugEnabled():
            _dbg("Dynamic shadows disabled by user setting")
        return False
    
    # Check shadow quality setting
    shadow_quality = _shadowQuality()
    if shadow_quality == 'off':
        if _debugEnabled():
            _dbg(f"Dynamic shadows disabled: shadow-quality={shadow_quality}")
        return False
    
    # With our aggressive _supportsBasicShaders(), this should return True for RTX GPUs
    shaders_supported = _supportsBasicShaders()
    
    if not shaders_supported:
        # Last resort: check config force options
        force_shaders = _settingsBool('force-shader-support', False)
        bypass_check = _settingsBool('shadow-bypass-shader-check', False)
        
        if force_shaders or bypass_check:
            if _debugEnabled():
                _dbg(f"FORCING shadow maps: force-shader-support={force_shaders}, shadow-bypass-shader-check={bypass_check}")
            return True
        
        if _debugEnabled():
            _dbg("Dynamic shadows disabled: shaders not supported and no force options enabled")
        return False
    
    return True


def _wantSpecularHighlights() -> bool:
    # Specular in Panda3D auto-shaders can produce camera-dependent color shifts
    # on some legacy content/shader-generator combinations (often perceived as
    # an RGB "sheen" on flat vertical surfaces). Keep it opt-in by default.
    return _settingsBool('lighting-specular-enabled', False)


def _wantTonemap() -> bool:
    return _settingsBool('lighting-tonemap-enabled', True)


def _wantProceduralSky() -> bool:
    if _OUTDOOR_SHADER_BISECT_LEVEL < 1:
        return False
    return _bisectAllows(6) and _settingsBool('want-procedural-sky', True)


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


def _desaturateRGBA(c: tuple, amt: float) -> tuple:
    """Desaturate an RGBA tuple toward gray by amt in [0,1]."""
    try:
        r, g, b, a = float(c[0]), float(c[1]), float(c[2]), float(c[3])
    except Exception:
        return c
    amt = _clamp(float(amt), 0.0, 1.0)
    gray = (r + g + b) / 3.0
    r = r * (1.0 - amt) + gray * amt
    g = g * (1.0 - amt) + gray * amt
    b = b * (1.0 - amt) + gray * amt
    return (r, g, b, a)


def _clampChromaRGBA(c: tuple, max_chroma: float) -> tuple:
    """Clamp chroma to avoid extreme channel separation on directionals.

    This reduces camera-dependent RGB banding on flat/billboarded geometry when
    multiple colored directionals overlap (key/fill/rim).
    """
    try:
        r, g, b, a = float(c[0]), float(c[1]), float(c[2]), float(c[3])
    except Exception:
        return c
    max_chroma = max(0.0, float(max_chroma))
    gray = (r + g + b) / 3.0
    dr, dg, db = r - gray, g - gray, b - gray
    chroma = max(abs(dr), abs(dg), abs(db))
    if chroma <= max_chroma or chroma <= 1e-8:
        return (r, g, b, a)
    s = max_chroma / chroma
    return (gray + dr * s, gray + dg * s, gray + db * s, a)


def _sunDirFromHpr(hpr: tuple[float, float, float]) -> Vec3:
    """Compute a stable sun direction from (H, P, R).

    This project’s zone profiles historically use a sign convention where a
    *negative* pitch indicates a sun above the horizon. Panda3D DirectionalLight
    expects a direction vector pointing *where the light shines* (rays travel),
    so we flip pitch when converting profile HPR -> direction.
    """
    try:
        h, p, r = float(hpr[0]), float(hpr[1]), float(hpr[2])
    except Exception:
        h, p, r = 0.0, -45.0, 0.0

    # Enforce a minimum downward pitch so ground/roads receive light.
    # Negative pitch points downward (shining down on the scene).
    if p > -18.0:
        p = -18.0

    q = Quat()
    q.setHpr(Vec3(h, p, r))
    d = q.getForward()
    try:
        d.normalize()
    except Exception:
        pass
    return d


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


def _isFoliageOrTree(np: NodePath) -> bool:
    if np is None or np.isEmpty():
        return False
    try:
        p = np
        while p and not p.isEmpty():
            name = p.getName().lower()
            if any(k in name for k in ['tree', 'foliage', 'flower', 'shrub', 'plant', 'grass', 'leaf', 'leaves', 'prop_green_tree', 'bark', 'trunk', 'prop_dg_flower', 'prop_tree']):
                return True
            if p.getName() == 'render':
                break
            p = p.getParent()
    except Exception:
        pass
    return False


def _forceLightingOnSubtree(root: NodePath) -> None:
    """Clear LightAttrib overrides that disable per-pixel lighting.

    Some geometry has baked vertex colours and explicit "light off" attribs
    that prevent the dynamic sun from reaching them.  Clearing those lets
    the key/fill/rim lights illuminate the full zone.
    """
    if root is None or root.isEmpty():
        return
    # Clear on the full subtree (not just the root). Some DNA content attaches
    # LightAttrib / LightOff overrides on intermediate nodes, which will still
    # cancel our lights if we only clear at the top.
    try:
        nodes = root.findAllMatches('**')
        for i in range(nodes.getNumPaths()):
            np = nodes.getPath(i)
            try:
                if _isFoliageOrTree(np):
                    try:
                        np.setLightOff(101)
                    except Exception:
                        pass
                    continue
                # IMPORTANT:
                # Billboarded/card geometry will change orientation with the camera.
                # Directional lighting on such geometry is therefore inherently
                # camera-dependent and can appear as an RGB "shift" as the camera turns.
                # Do not forcibly clear LightOff/LightAttrib on these nodes.
                try:
                    if np.hasEffect(BillboardEffect.getClassType()):
                        continue
                except Exception:
                    pass
                if hasattr(np, 'clearLightOff'):
                    np.clearLightOff()
                try:
                    np.clearAttrib(LightAttrib.getClassType())
                except Exception:
                    pass
            except Exception:
                pass
    except Exception:
        # Fallback: at least try the root.
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

    # NOTE:
    # This project uses OTP camera bitmasks, and restricting the shadow camera to a
    # single bitmask can result in an empty shadow pass on some scenes. Until we
    # have confirmed stable shadow visibility everywhere, we avoid hiding geometry
    # from the shadow pass via bitmask tricks. (We'll reintroduce this once base
    # shadows are confirmed working.)

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
                if _isFoliageOrTree(np):
                    try:
                        np.setLightOff(101)
                    except Exception:
                        pass
                    continue
                # Same reasoning as _forceLightingOnSubtree: don't force lighting on
                # billboarded geometry (camera-dependent normals/lighting artifacts).
                try:
                    if np.hasEffect(BillboardEffect.getClassType()):
                        continue
                except Exception:
                    pass
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
        # Cool blue-white sodium arc / fantasy lamp (night areas)
        lampColor   = Vec4(0.85, 0.92, 1.00, 1.0)
        lampColor2  = Vec4(0.60, 0.75, 1.00, 1.0)  # secondary soft fill
    else:
        # Warm yellow-orange street lamp (day/evening areas)
        lampColor   = Vec4(1.00, 0.85, 0.52, 1.0)
        lampColor2  = Vec4(1.00, 0.70, 0.30, 1.0)  # secondary warm glow

    for idx, lampNp in enumerate(_lampGeomNps):
        try:
            # Get world-space light-head position (try tight bounds top, else Z+offset)
            try:
                mins, maxs = lampNp.getTightBounds(base.render)
                lightPos = Vec3(
                    (mins[0] + maxs[0]) * 0.5,
                    (mins[1] + maxs[1]) * 0.5,
                    maxs[2] + 0.5,   # slightly above the top of the lamp geometry
                )
            except Exception:
                wp = lampNp.getPos(base.render)
                lightPos = Vec3(wp.x, wp.y, wp.z + 4.5)

            pl = PointLight(f'outdoorLampLight_{idx}')
            pl.setColor(lampColor)
            # Realistic bright lamp: constant=0.1, linear=0, quadratic=0.005
            # This gives ~15 units of bright light and ~35 units of fall-off
            # (quadratic 0.005 => radius where intensity = 0.5*peak is ~14 units)
            pl.setAttenuation(Vec3(0.10, 0.0, 0.005))
            # Make shadows from lamp optional but enable bright illumination
            try:
                pl.setMaxDistance(45.0)
            except Exception:
                pass

            plNp = _lightRig.attachNewNode(pl)
            plNp.setPos(base.render, lightPos)
            base.render.setLight(plNp)
            _lampLights.append(plNp)

            # Add a subtle secondary fill light slightly lower for volumetric feel
            pl2 = PointLight(f'outdoorLampFill_{idx}')
            pl2.setColor(Vec4(lampColor2[0]*0.4, lampColor2[1]*0.4,
                              lampColor2[2]*0.4, 1.0))
            pl2.setAttenuation(Vec3(0.20, 0.0, 0.012))
            plNp2 = _lightRig.attachNewNode(pl2)
            plNp2.setPos(base.render, Vec3(lightPos.x, lightPos.y, lightPos.z - 1.8))
            base.render.setLight(plNp2)
            _lampLights.append(plNp2)
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
        # Keep the shadow frustum centered near the camera so it doesn't "pop"
        # on/off as the player turns around (looking at areas outside the film
        # size centered on a fixed zone origin).
        target = Vec3(_shadowFocusPos[0], _shadowFocusPos[1], _shadowFocusPos[2])
        try:
            cam_np = getattr(base, 'camera', None)
            if cam_np is not None and not cam_np.isEmpty():
                cam_pos = cam_np.getPos(base.render)
                # Follow camera in XY, but clamp so we don't chase too far and
                # lose overall zone coverage.
                dx = float(cam_pos[0] - target[0])
                dy = float(cam_pos[1] - target[1])
                # Maximum offset from the zone focus we allow the shadow center.
                max_off = max(40.0, float(_shadowSceneRadius) * 0.60)
                d2 = dx * dx + dy * dy
                if d2 > (max_off * max_off):
                    inv_len = max_off / math.sqrt(d2)
                    dx *= inv_len
                    dy *= inv_len
                # Blend toward the camera so the frustum tracks view direction.
                follow = 0.75
                target = Vec3(
                    target[0] + dx * follow,
                    target[1] + dy * follow,
                    target[2],
                )
        except Exception:
            pass
        texel  = max(0.25, _shadowFilmArea / max(1.0, float(_shadowMapRes)))
        # Only snap X and Y to the texel grid to prevent shadow edge swimming.
        # Snapping Z too causes the shadow frustum to stutter vertically, which
        # manifests as sharp spike-like seam artifacts along geometry silhouettes.
        target = Vec3(
            round(target[0] / texel) * texel,
            round(target[1] / texel) * texel,
            target[2],   # Z intentionally not snapped – vertical snap = spike artifacts
        )
        sunDir = None
        try:
            sunDir = Vec3(_sunDirWorld) if _sunDirWorld is not None else None
        except Exception:
            sunDir = None
        if sunDir is None:
            sunDir = _keyLightNp.getQuat(base.render).getForward()
        shadowCamPos = target - sunDir * _shadowFollowDist
        _keyLightNp.setPos(base.render, shadowCamPos)
    except Exception:
        pass


def _spawnLightRig(spec: dict, geom=None,
                   shadowBounds: tuple[Vec3, float] | None = None,
                   enable_ambient: bool = True,
                   enable_key: bool = True,
                   enable_fill: bool = True,
                   enable_rim: bool = True,
                   enable_shadows: bool = True) -> None:
    global _lightRig, _renderLights, _keyLightNp, _shadowFollowDist
    global _keyCastsShadows, _shadowFocusPos, _shadowSceneRadius
    global _shadowMapRes, _shadowFilmArea, _prevShadowCasterState, _sunDirWorld

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
    try:
        _dbg(f"shadowBounds focus={_shadowFocusPos} radius={_shadowSceneRadius} fullHalf={fullHalf}")
    except Exception:
        pass

    # ── Ambient ──────────────────────────────────────────────────────────────
    if enable_ambient:
        floor    = float(spec.get('shadowDarknessFloor', 0.18))
        rawAmb   = _applyColorTemp(_scaleColor(spec['ambient'], intensity))
        # Raise the floor slightly so ground planes are never pitch-black.
        # We use a stronger floor multiplier on all channels so shadows
        # don't swallow the ground geometry.
        ambColor = (
            max(rawAmb[0], floor * 1.0),
            max(rawAmb[1], floor * 0.90),
            max(rawAmb[2], floor * 1.1),
            rawAmb[3],
        )
        amb   = AmbientLight('outdoorAmbient')
        amb.setColor(Vec4(*ambColor))
        ambNp = _lightRig.attachNewNode(amb)
        # Apply lights both globally AND to the zone root.
        # Critically, apply with priority 100 so zone-level clearLightOff
        # calls can't accidentally block this ambient.
        base.render.setLight(ambNp, 100)
        try:
            if geom is not None and not geom.isEmpty():
                geom.setLight(ambNp, 100)
        except Exception:
            pass
        _renderLights.append(ambNp)

    # ── Key / sun ─────────────────────────────────────────────────────────────
    if not enable_key:
        return
    keyColor      = _applyColorTemp(_scaleColor(spec['key'], intensity))
    key           = DirectionalLight('outdoorKey')
    key.setColor(Vec4(*keyColor))
    wants_shadow  = (enable_shadows
                     and spec.get('shadowCaster', False)
                     and _wantDynamicShadows()
                     and _shadowQuality() != 'off')
    _prevShadowCasterState = wants_shadow

    if wants_shadow:
        try:
            res = _scaledShadowRes(spec)
            # Clamp requested shadow resolution to GPU limits.
            try:
                gsg = base.win.getGsg() if getattr(base, 'win', None) else None
                if gsg:
                    try:
                        max_dim = int(gsg.getMaxTextureDimension())
                    except Exception:
                        max_dim = 0
                    # Depth textures / shadow maps often fail silently if too large.
                    if max_dim and res > max_dim:
                        _dbg(f"clamping shadowRes {res} -> {max_dim} (GPU max texture dim)")
                        res = max_dim
                    # Snap down to a sane power-of-two bucket.
                    if res >= 4096:
                        res = 4096
                    elif res >= 2048:
                        res = 2048
                    elif res >= 1024:
                        res = 1024
                    else:
                        res = 512
                    try:
                        _dbg(
                            "gsg caps "
                            f"supportsFBO={gsg.getSupportsFramebuffer()} "
                            f"supportsBasicShaders={gsg.getSupportsBasicShaders()} "
                            f"supportsDepthTex={getattr(gsg, 'getSupportsDepthTexture', lambda: 'n/a')()} "
                            f"maxTexDim={gsg.getMaxTextureDimension()}"
                        )
                    except Exception:
                        pass
            except Exception:
                pass
            # Try to create shadow caster with error handling
            try:
                print(f"[DEBUG VideoSettings] _spawnLightRig: calling key.setShadowCaster(True, {res}, {res})...")
                key.setShadowCaster(True, res, res)
                print(f"[DEBUG VideoSettings] _spawnLightRig: key.setShadowCaster(True, {res}, {res}) returned.")
                try:
                    is_caster = getattr(key, 'isShadowCaster', lambda: 'n/a')()
                    print(f"[DEBUG VideoSettings] _spawnLightRig: key.isShadowCaster={is_caster}")
                except Exception:
                    pass
                _shadowMapRes = res
                _keyCastsShadows = True
                try:
                    key.setCameraMask(_SHADOW_CAM_MASK)
                except Exception:
                    pass
            except Exception as e:
                print(f"[DEBUG VideoSettings] _spawnLightRig: setShadowCaster({res}) failed with exception: {e!r}")
                _keyCastsShadows = False
                return  # Skip the rest of shadow setup

            # Integer depth bias only.  The 3-arg DepthOffsetAttrib.make(off, a, b) is
            # NOT (offset, slope, maxBias) — it clamps projected Z to [min_value, max_value]
            # in *normalized* depth, both in [0, 1].  Passing 2.5 triggers assertions and
            # breaks shadow maps (see logs: depthOffsetAttrib.cxx min_value 0..1 check).
            # A too-large depth offset bias can cause *everything* to evaluate as
            # "in shadow" (overly dark world) depending on driver/build. Keep the
            # default conservative and allow per-zone override.
            depthOffset = int(spec.get('shadowDepthOffset', 2))
            depthOffset = max(0, min(8, depthOffset))
            key.setInitialState(key.getInitialState().addAttrib(DepthOffsetAttrib.make(depthOffset)))

            # Soften blocky shadow edges where supported by the build by setting
            # shadow map texture filtering to linear.
            try:
                sm = None
                if hasattr(key, 'getShadowMap'):
                    try:
                        sm = key.getShadowMap(0)
                    except Exception:
                        sm = None
                if sm:
                    try:
                        sm.setMinfilter(Texture.FTShadow)
                        sm.setMagfilter(Texture.FTShadow)
                    except Exception:
                        pass
            except Exception:
                pass

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
            try:
                _dbg(f"shadowLens film={key.getLens().getFilmSize()} nearFar={key.getLens().getNearFar()}")
            except Exception:
                pass

            # NOTE:
            # This "force huge frustum" debug knob makes shadow texel density so low
            # that it can look like blocky square lighting across the whole scene.
            # Do NOT enable it just because lighting-debug is on.
            try:
                if ConfigVariableBool('lighting-shadow-force-huge-frustum', False).value:
                    key.getLens().setFilmSize(max(2000.0, float(area)), max(2000.0, float(area)))
                    key.getLens().setNearFar(1.0, 20000.0)
                    _dbg(f"shadowLens(huge frustum) film={key.getLens().getFilmSize()} nearFar={key.getLens().getNearFar()}")
                    _shadowFilmArea = max(2000.0, float(area))
            except Exception:
                pass
            try:
                # Some builds expose shadow buffer/texture accessors.
                for attr in ('getNumShadowMaps', 'getNumShadowBuffers'):
                    if hasattr(key, attr):
                        _dbg(f"key.{attr}()={getattr(key, attr)()}")
                for attr in ('getShadowBuffer', 'getShadowMap'):
                    if hasattr(key, attr):
                        try:
                            v = getattr(key, attr)(0)
                            _dbg(f"key.{attr}(0)={'ok' if v else 'none'}")
                        except Exception:
                            pass
            except Exception:
                pass
        except Exception as outer_e:
            print(f"[DEBUG VideoSettings] _spawnLightRig: outer exception in primary shadow setup: {outer_e!r}. Attempting fallback 1024 shadow setup...")
            try:
                print("[DEBUG VideoSettings] _spawnLightRig: calling fallback key.setShadowCaster(True, 1024, 1024)...")
                key.setShadowCaster(True, 1024, 1024)
                print("[DEBUG VideoSettings] _spawnLightRig: fallback key.setShadowCaster returned.")
                try:
                    key.setCameraMask(_SHADOW_CAM_MASK)
                except Exception:
                    pass
                _shadowMapRes = 1024
                key.setInitialState(key.getInitialState().addAttrib(DepthOffsetAttrib.make(4)))
                fallArea = float(spec.get('shadowArea', 180))
                key.getLens().setFilmSize(fallArea, fallArea)
                key.getLens().setNearFar(10, int(_shadowFollowDist * 2.0 + 500))
                _shadowFilmArea   = fallArea
                _keyCastsShadows  = True
            except Exception as fallback_e:
                print(f"[DEBUG VideoSettings] _spawnLightRig: fallback setShadowCaster failed: {fallback_e!r}")

    # Compute and set the directional light vector explicitly.
    # In some Panda3D builds, the DirectionalLight's printed direction and the
    # shader generator use the node's internal direction (not the NodePath's HPR).
    # If we only rotate the NodePath, the light can remain at the default (0,1,0),
    # producing "sunlight only on edges" and a dark world.
    try:
        kh, kp, kr = spec.get('keyHpr', (0, -45, 0))
        _sunDirWorld = _sunDirFromHpr((kh, kp, kr))
        key.setDirection(_sunDirWorld)
    except Exception:
        _sunDirWorld = Vec3(0, 0, -1)
        try:
            key.setDirection(_sunDirWorld)
        except Exception:
            pass

    keyNp = _lightRig.attachNewNode(key)
    # Also set the NodePath HPR so the shadow camera uses a consistent basis.
    try:
        keyNp.setHpr(float(kh), float(kp), float(kr))
    except Exception:
        pass
    base.render.setLight(keyNp, 100)
    try:
        if geom is not None and not geom.isEmpty():
            geom.setLight(keyNp, 100)
    except Exception:
        pass
    _renderLights.append(keyNp)
    _keyLightNp = keyNp
    _positionShadowCaster()

    # ── Fill ──────────────────────────────────────────────────────────────────
    if enable_fill:
        fillColor = _applyColorTemp(_scaleColor(spec['fill'], intensity * 0.90))
        # IMPORTANT:
        # A *directional* fill light is view-independent in theory, but in practice
        # Toontown content contains camera-facing cards / special effects / odd
        # transforms that make directional multi-light shading show camera-dependent
        # RGB artifacts (your "RGB vertical surfaces" issue).
        #
        # We therefore implement fill as a *soft ambient* contribution. This preserves
        # the overall mood and lifts shadows without introducing view-dependent hue
        # banding, and also avoids the TransformState/normal-matrix singular crashes
        # observed when adding extra directionals.
        # Increased contribution from 0.70 to 0.80 for a brighter scene.
        fillColor = _clampChromaRGBA(_desaturateRGBA(fillColor, 0.45), 0.45)
        fill      = AmbientLight('outdoorFillAmbient')
        fill.setColor(Vec4(fillColor[0] * 0.80, fillColor[1] * 0.80, fillColor[2] * 0.80, fillColor[3]))
        fillNp = _lightRig.attachNewNode(fill)
        base.render.setLight(fillNp, 100)
        try:
            if geom is not None and not geom.isEmpty():
                geom.setLight(fillNp, 100)
        except Exception:
            pass
        _renderLights.append(fillNp)

    # ── Rim ───────────────────────────────────────────────────────────────────
    if enable_rim and spec.get('rim'):
        rimColor = _applyColorTemp(_scaleColor(spec['rim'], intensity * 0.75))
        # Same reasoning as fill: keep rim as a subtle ambient tint to avoid
        # view-dependent color banding on flat/camera-facing geometry.
        # Increased contribution from 0.22 to 0.32 for more visible rim light.
        rimColor = _clampChromaRGBA(_desaturateRGBA(rimColor, 0.45), 0.45)
        rim      = AmbientLight('outdoorRimAmbient')
        rim.setColor(Vec4(rimColor[0] * 0.32, rimColor[1] * 0.32, rimColor[2] * 0.32, rimColor[3]))
        rimNp = _lightRig.attachNewNode(rim)
        base.render.setLight(rimNp, 100)
        try:
            if geom is not None and not geom.isEmpty():
                geom.setLight(rimNp, 100)
        except Exception:
            pass
        _renderLights.append(rimNp)


def _destroyLightRig() -> None:
    global _lightRig, _renderLights, _keyLightNp, _keyCastsShadows
    global _shadowFocusPos, _shadowSceneRadius, _shadowMapRes, _shadowFilmArea
    # NOTE: _prevShadowCasterState is intentionally NOT reset here.
    # Resetting it to None causes _applyProfileLive (day/night tick) to
    # immediately detect a state change (True != None) and call
    # _scheduleRigRebuild, which triggers a second setShadowCaster() call
    # while the first shadow FBO is still live in the render thread.
    # That double-FBO creation causes a GL context deadlock / permanent freeze.
    _disableLampLights()
    if _keyLightNp and not _keyLightNp.isEmpty():
        try:
            k = _keyLightNp.getNode(0)
            if hasattr(k, 'setShadowCaster') and getattr(k, 'isShadowCaster', lambda: False)():
                print("[DEBUG VideoSettings] _destroyLightRig: explicitly disabling shadow caster on key light to free offscreen FBO...")
                k.setShadowCaster(False)
                print("[DEBUG VideoSettings] _destroyLightRig: key.setShadowCaster(False) returned.")
        except Exception as e:
            print(f"[DEBUG VideoSettings] _destroyLightRig: failed to disable shadow caster: {e!r}")
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
    if _lightRig and not _lightRig.isEmpty():
        _lightRig.removeNode()
    _lightRig = None


def _applyProfileLive(spec: dict) -> None:
    print(f"[DEBUG VideoSettings] _applyProfileLive: called.")
    if not (_lightRig and not _lightRig.isEmpty()):
        print(f"[DEBUG VideoSettings] _applyProfileLive: lightRig is empty/None. Returning.")
        return

    intensity = _intensityScale()
    floor     = float(spec.get('shadowDarknessFloor', 0.18))

    for np in _renderLights:
        node = np.getNode(0)
        name = node.getName()

        if name == 'outdoorAmbient':
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

        elif name == 'outdoorFillAmbient':
            raw = _applyColorTemp(_scaleColor(
                spec.get('fill', (0.5, 0.5, 0.5, 1)), intensity * 0.90))
            fillColor = _clampChromaRGBA(_desaturateRGBA(raw, 0.45), 0.45)
            node.setColor(Vec4(fillColor[0] * 0.80, fillColor[1] * 0.80, fillColor[2] * 0.80, fillColor[3]))

        elif name == 'outdoorRimAmbient':
            rim = spec.get('rim')
            if rim:
                raw = _applyColorTemp(_scaleColor(rim, intensity * 0.75))
                rimColor = _clampChromaRGBA(_desaturateRGBA(raw, 0.45), 0.45)
                node.setColor(Vec4(rimColor[0] * 0.32, rimColor[1] * 0.32, rimColor[2] * 0.32, rimColor[3]))

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
    print(f"[DEBUG VideoSettings] _applyProfileLive: wants shadow={wants}, _prevShadowCasterState={_prevShadowCasterState}")
    # Only trigger a rebuild when the state has actually changed from a known
    # prior value. If _prevShadowCasterState is None it means the rig was just
    # destroyed and _spawnLightRig hasn't run yet - skip the rebuild to avoid
    # a double setShadowCaster() / double FBO creation deadlock.
    if _prevShadowCasterState is not None and wants != _prevShadowCasterState:
        print(f"[DEBUG VideoSettings] _applyProfileLive: shadow caster state mismatch! Scheduling rig rebuild...")
        _scheduleRigRebuild(spec)
    print(f"[DEBUG VideoSettings] _applyProfileLive: complete.")


def _scheduleRigRebuild(spec: dict) -> None:
    global _rigRebuildPending
    print(f"[DEBUG VideoSettings] _scheduleRigRebuild: scheduling rig rebuild.")
    _rigRebuildPending = spec


def _flushRigRebuild() -> None:
    global _rigRebuildPending, _activeGeom
    if _rigRebuildPending is None:
        return
    print(f"[DEBUG VideoSettings] _flushRigRebuild: starting pending rebuild...")
    # During feature bisect, avoid rebuilding/spawning the light rig on steps
    # that are meant to have no lights (eg step 1 = shader-auto only).
    try:
        if not _bisectAllows(2):
            print(f"[DEBUG VideoSettings] _flushRigRebuild: bisect step does not allow lights. Cancelling rebuild.")
            _rigRebuildPending = None
            return
    except Exception:
        pass
    spec = _rigRebuildPending
    _rigRebuildPending = None
    savedBounds = None
    if _shadowFocusPos is not None:
        savedBounds = (Vec3(_shadowFocusPos), float(_shadowSceneRadius))
    print(f"[DEBUG VideoSettings] _flushRigRebuild: destroying old light rig...")
    _destroyLightRig()
    print(f"[DEBUG VideoSettings] _flushRigRebuild: spawning new light rig...")
    _spawnLightRig(spec, geom=_activeGeom, shadowBounds=savedBounds)
    if _activeGeom is not None and not _activeGeom.isEmpty():
        try:
            _activeGeom.setShaderAuto()
            _forceShadersOnSubtree(_activeGeom)
            _forceShaderRegen(_activeGeom)
            _forceLightingOnSubtree(_activeGeom)
            _hidePlaneLikeCastersFromShadow(_activeGeom)
        except Exception as e:
            print(f"[DEBUG VideoSettings] _flushRigRebuild: geom shader regen exception: {e!r}")
    lav = getattr(base, 'localAvatar', None)
    if lav is not None and not lav.isEmpty():
        try:
            _forceShaderRegen(lav)
        except Exception as e:
            print(f"[DEBUG VideoSettings] _flushRigRebuild: localAvatar shader regen exception: {e!r}")
    print(f"[DEBUG VideoSettings] _flushRigRebuild: complete.")


# ─────────────────────────────────────────────────────────────────────────────
# Atmospheric fog
# ─────────────────────────────────────────────────────────────────────────────

def _applyFog(spec: dict) -> None:
    global _fogNode
    if not _bisectAllows(5):
        return
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
    if _bisectAllows(8):
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
        if not _bisectAllows(8):
            return
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
    if not _bisectAllows(8):
        return
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
        # Many zone profiles use very warm/orange rayColor which can turn
        # blown-out highlights into "red sunlight". Prefer a neutral color that
        # matches the actual key light.
        try:
            if _keyLightNp is not None and not _keyLightNp.isEmpty():
                k = _keyLightNp.getNode(0)
                if k and hasattr(k, 'getColor'):
                    kc = k.getColor()
                    # Clamp and slightly desaturate toward white.
                    r = max(0.0, min(1.0, float(kc[0])))
                    g = max(0.0, min(1.0, float(kc[1])))
                    b = max(0.0, min(1.0, float(kc[2])))
                    desat = 0.55
                    lum = (r + g + b) / 3.0
                    r = r * (1.0 - desat) + lum * desat
                    g = g * (1.0 - desat) + lum * desat
                    b = b * (1.0 - desat) + lum * desat
                    rc = (r, g, b, float(rc[3]) if len(rc) >= 4 else 1.0)
        except Exception:
            pass
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
        try:
            from toontown.hood.ProceduralSky import ProceduralSky
        except ImportError:
            from ProceduralSky import ProceduralSky
        _proceduralSky = ProceduralSky()
        # Parent to the lens NodePath (base.cam) so the dome shares the same
        # transform as the camera FilterManager renders with; base.camera can sit
        # slightly off the lens on third-person rigs.
        _skyParent = base.cam if (getattr(base, 'cam', None) and not base.cam.isEmpty()) else base.camera
        _proceduralSky.attach(_skyParent, style=_activeStyle)
        if _proceduralSky and _proceduralSky.isActive():
            try:
                _proceduralSky._skyNp.hide(_SHADOW_CAM_MASK)
            except Exception:
                pass
        _proceduralSky.update(spec, _timeOfDay)
        hood = _getHood()
        if hood and getattr(hood, 'sky', None) and not hood.sky.isEmpty():
            # If the procedural sky failed to attach (shader missing, etc),
            # keep the legacy model sky visible as a fallback.
            if _proceduralSky and _proceduralSky.isActive():
                hood.sky.hide(BitMask32.allOn())
            else:
                hood.sky.show(BitMask32.allOn())
    except Exception as e:
        import traceback
        print(f"[DEBUG VideoSettings] _setupProceduralSky exception: {e!r}")
        traceback.print_exc()
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
        try:
            np.hide(_SHADOW_CAM_MASK)
        except Exception:
            pass


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
    if _sunDirWorld is not None:
        try:
            sunDir = Vec3(_sunDirWorld)
            sunDir.normalize()
        except Exception:
            pass
    elif _keyLightNp and not _keyLightNp.isEmpty():
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

    # Teleport/zone transitions can temporarily tear down the scene graph in ways
    # that make TransformState matrices non-invertible, which can crash inside
    # Panda3D when we query transforms. We should *not* permanently stop this task
    # on a transient bad frame, because that can leave the shadow caster frozen
    # and make the whole world look incorrectly shadowed. Instead, keep the task
    # alive and just skip frames that hit assertions.
    import sys as _sys_ol; _sys_ol.stderr.write('[CRASH-DIAG] _lightingUpdateTask: tick start\n'); _sys_ol.stderr.flush()
    print(f"[DEBUG VideoSettings] _lightingUpdateTask: tick start.", flush=True)
    try:
        _syncBase()
        if base is None or getattr(base, 'render', None) is None:
            print(f"[DEBUG VideoSettings] _lightingUpdateTask: base or base.render is None, returning task.done.", flush=True)
            return task.done
        if _refCount <= 0 or _lightRig is None or (_lightRig and _lightRig.isEmpty()):
            print(f"[DEBUG VideoSettings] _lightingUpdateTask: refCount={_refCount} or lightRig is None/empty, returning task.done.", flush=True)
            return task.done
    except Exception as e:
        print(f"[DEBUG VideoSettings] _lightingUpdateTask: exception in initial checks: {e!r}, returning task.done.")
        return task.done

    dt            = globalClock.getDt()
    _godRaysTime += dt

    if _refCount > 0:
        _sys_ol.stderr.write('[CRASH-DIAG] _lightingUpdateTask: maintainViewport\n'); _sys_ol.stderr.flush()
        print(f"[DEBUG VideoSettings] _lightingUpdateTask: calling _maintainOutdoorLightingViewport...", flush=True)
        _maintainOutdoorLightingViewport()
        print(f"[DEBUG VideoSettings] _lightingUpdateTask: _maintainOutdoorLightingViewport returned.", flush=True)

    # ── Shadow camera positioning ─────────────────────────────────────────────
    try:
        _sys_ol.stderr.write('[CRASH-DIAG] _lightingUpdateTask: positionShadowCaster\n'); _sys_ol.stderr.flush()
        print(f"[DEBUG VideoSettings] _lightingUpdateTask: calling _positionShadowCaster...", flush=True)
        _positionShadowCaster()
        print(f"[DEBUG VideoSettings] _lightingUpdateTask: _positionShadowCaster returned.", flush=True)
    except AssertionError as ae:
        print(f"[DEBUG VideoSettings] _lightingUpdateTask: _positionShadowCaster assertion error: {ae!r}")
        return task.cont
    except Exception as e:
        print(f"[DEBUG VideoSettings] _lightingUpdateTask: _positionShadowCaster exception: {e!r}")
        return task.cont

    # ── Water uniforms ────────────────────────────────────────────────────────
    try:
        _sys_ol.stderr.write('[CRASH-DIAG] _lightingUpdateTask: tickWaterUniforms\n'); _sys_ol.stderr.flush()
        print(f"[DEBUG VideoSettings] _lightingUpdateTask: calling _tickWaterUniforms...", flush=True)
        _tickWaterUniforms(dt)
        print(f"[DEBUG VideoSettings] _lightingUpdateTask: _tickWaterUniforms returned.", flush=True)
    except AssertionError as ae:
        print(f"[DEBUG VideoSettings] _lightingUpdateTask: _tickWaterUniforms assertion error: {ae!r}")
        return task.cont
    except Exception as e:
        print(f"[DEBUG VideoSettings] _lightingUpdateTask: _tickWaterUniforms exception: {e!r}")
        pass

    # ── Procedural sky update ─────────────────────────────────────────────────
    try:
        _sys_ol.stderr.write('[CRASH-DIAG] _lightingUpdateTask: proceduralSky\n'); _sys_ol.stderr.flush()
        if _proceduralSky and _proceduralSky.isActive():
            print(f"[DEBUG VideoSettings] _lightingUpdateTask: calling procedural sky update...", flush=True)
            spec = _getActiveSpec()
            _proceduralSky.update(spec, _timeOfDay)
            print(f"[DEBUG VideoSettings] _lightingUpdateTask: procedural sky update returned.")
            hood = _getHood()
            if hood and getattr(hood, 'sky', None) and not hood.sky.isEmpty():
                hood.sky.hide()
    except AssertionError as ae:
        print(f"[DEBUG VideoSettings] _lightingUpdateTask: procedural sky update assertion error: {ae!r}")
        return task.cont
    except Exception as e:
        print(f"[DEBUG VideoSettings] _lightingUpdateTask: procedural sky update exception: {e!r}")
        pass

    # ── Day / night cycle ─────────────────────────────────────────────────────
    _sys_ol.stderr.write('[CRASH-DIAG] _lightingUpdateTask: dayNight\n'); _sys_ol.stderr.flush()
    if _wantDayNight() and _refCount > 0:
        spec = _ZONE_PROFILES.get(_activeStyle, _ZONE_PROFILES['playground'])
        if spec.get('dayNightEnabled', True):
            _dayNightAccum += dt
            if _dayNightAccum >= 0.25:  # 4 Hz update rate
                print(f"[DEBUG VideoSettings] _lightingUpdateTask: 4 Hz update triggered. _dayNightAccum={_dayNightAccum}, _timeOfDay={_timeOfDay}")
                gameHours  = (_dayNightAccum
                              * _dayNightSpeed
                              * _dayNightSpeedMultiplier())
                _timeOfDay      = (_timeOfDay + gameHours) % 24.0
                _dayNightAccum  = 0.0
                cur_spec        = _getActiveSpec()
                print(f"[DEBUG VideoSettings] _lightingUpdateTask: calling _applyProfileLive...")
                _applyProfileLive(cur_spec)
                print(f"[DEBUG VideoSettings] _lightingUpdateTask: calling _updateBloomLive...")
                _updateBloomLive(cur_spec)

    # ── Street lamp lights: on at night, off during day ───────────────────────
    if _lampGeomNps and _lightRig and not _lightRig.isEmpty():
        try:
            print(f"[DEBUG VideoSettings] _lightingUpdateTask: updating street lamp lights...")
            cur_spec = _getActiveSpec()
            kHpr     = cur_spec.get('keyHpr', (135, -42, 0))
            # Derive sun elevation: the key-light pitch angle p (kHpr[1]) gives:
            #   sunDirWorld.z = sin(p_degrees)
            # Toontown's daytime uses p ≈ -42 → sin(-42°) ≈ -0.67 → below 0
            # A more negative p means sun is pointing *more* downward from above.
            # The pitch is from the directional light's perspective: a large negative
            # pitch means the light shines steeply from above (midday).
            # At sunset/rise the absolute pitch shrinks toward 0 → sunDirZ→0.
            # At "nighttime" key configs (DL, 0:00 etc.), pitch is still negative
            # but we need to detect dusk/night by checking if the sun is LOW.
            #
            # Lamps should turn on when:
            #   (a) This is a perpetual-night zone (DL, COG HQs), OR
            #   (b) The active keyframe has a low sun (pitch close to 0 or above horizon)
            #
            # For day/night zones the "night" keyframes set pitch close to 0 or even
            # positive. Threshold: enable lamps when pitch > -18° (sin > -0.31).
            perpetualNight = _activeStyle in (
                'dl', 'dl_street', 'sellbot_hq', 'cashbot_hq',
                'lawbot_hq', 'bossbot_hq', 'cog',
            )
            pitch_deg = float(kHpr[1])
            sunLow    = pitch_deg > -18.0   # sun is near horizon or above = night/dusk
            if perpetualNight or sunLow:
                _enableLampLights(_activeStyle)
            else:
                _disableLampLights()
            print(f"[DEBUG VideoSettings] _lightingUpdateTask: street lamp lights updated.")
        except Exception as e:
            print(f"[DEBUG VideoSettings] _lightingUpdateTask: street lamp lights exception: {e!r}")
            pass

    # ── Sun-ray overlay shimmer ───────────────────────────────────────────────
    _sys_ol.stderr.write('[CRASH-DIAG] _lightingUpdateTask: godRays\n'); _sys_ol.stderr.flush()
    if _godRaysCard and not _godRaysCard.isEmpty():
        _godRaysCard.setShaderInput('time', _godRaysTime)

    # ── Deferred rig rebuild ──────────────────────────────────────────────────
    _sys_ol.stderr.write('[CRASH-DIAG] _lightingUpdateTask: flushRigRebuild\n'); _sys_ol.stderr.flush()
    try:
        if _rigRebuildPending is not None:
            print(f"[DEBUG VideoSettings] _lightingUpdateTask: calling _flushRigRebuild...", flush=True)
        _flushRigRebuild()
    except AssertionError as ae:
        print(f"[DEBUG VideoSettings] _lightingUpdateTask: _flushRigRebuild assertion error: {ae!r}")
        return task.cont
    except Exception as e:
        print(f"[DEBUG VideoSettings] _lightingUpdateTask: _flushRigRebuild exception: {e!r}")
        pass

    _sys_ol.stderr.write('[CRASH-DIAG] _lightingUpdateTask: tick end\n'); _sys_ol.stderr.flush()
    print(f"[DEBUG VideoSettings] _lightingUpdateTask: tick end.", flush=True)
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
    _syncBase()
    global _refCount, _activeStyle, _activeGeom
    if not _wantFx():
        return

    _activeGeom = geom

    resolvedStyle = _resolveStyle(style, hoodId, zoneId)
    spec          = _ZONE_PROFILES[resolvedStyle]
    _dbg(f"begin(refCount={_refCount}) style={style} resolved={resolvedStyle} hoodId={hoodId} zoneId={zoneId}")
    _maybeBindBisectHotkeys()
    # Keep OTP blob/drop shadows synced regardless of shader support.
    if _OTPDropshadow:
        try:
            _OTPDropshadow.setGlobalDropShadowFlag(1 if _settingsBool('dynamic-shadows', True) else 0)
        except Exception:
            pass
        try:
            _OTPDropshadow.setGlobalDropShadowGrayLevel(float(_settingsFloat('drop-shadow-strength', 0.5)))
        except Exception:
            pass

    _dbg(f"settings wantFx={_wantFx()} dynShadows={_wantDynamicShadows()} shadowQuality={_shadowQuality()} wantBloom={_wantBloom()} wantProceduralSky={_wantProceduralSky()}")

    if _refCount == 0:
        _dbgBisectState()
        _activeStyle = resolvedStyle
        cur_spec     = _getActiveSpec() if spec.get('dayNightEnabled', True) else spec

        # Hard cleanup of optional subsystems when bisecting.
        # This prevents leftovers from prior runs (or other systems) from making
        # it *look* like everything is still enabled at low bisect steps.
        try:
            if not _bisectAllows(9):
                _cleanupAllWater()
        except Exception:
            pass
        try:
            if not _bisectAllows(8):
                _destroyGodRaysOverlay()
        except Exception:
            pass
        try:
            if not _bisectAllows(7):
                _destroyPostProcess()
        except Exception:
            pass
        try:
            if not _bisectAllows(6):
                _destroyProceduralSky()
        except Exception:
            pass
        try:
            if not _bisectAllows(5):
                _clearFog()
                _clearSkyTint()
                _restoreBackgroundColor()
        except Exception:
            pass

        # Step 0: fully disable OutdoorLighting effects and exit early after cleanup.
        if not _bisectAllows(1):
            return
        # Ensure the root scene graph participates in shader generation and lighting.
        # Some Toontown-era content relies on fixed-function defaults that can
        # disable per-pixel lighting/shadow receiving unless shader-auto is
        # enabled high up the graph.
        try:
            if getattr(base, 'render', None) is not None:
                base.render.setShaderAuto()
                if hasattr(base.render, 'clearLightOff'):
                    base.render.clearLightOff()
                try:
                    base.render.clearAttrib(LightAttrib.getClassType())
                except Exception:
                    pass
                # Avoid aggressively clearing shader state on base.render.
                # During zone transitions, some nodes can briefly have singular or
                # otherwise invalid transforms; forcing a full shader rebuild at the
                # root can trip Panda3D assertions inside renderFrame.
        except Exception:
            pass
        # Step ladder:
        # 1: shader-auto only (no lights)
        # 2: ambient only
        # 3: sun (no shadows)
        # 4: sun (with shadows, if enabled)
        rig_spawned = False
        if _bisectAllows(2):
            enable_shadows = bool(_bisectAllows(4))
            enable_key = bool(_bisectAllows(3))
            # Further bisect within directional lighting to isolate camera-dependent RGB:
            # key-only vs key+fill vs key+fill+rim.
            try:
                mode = _DIR_LIGHT_MODE
            except Exception:
                mode = 'all'
            enable_fill = enable_key and (mode in ('key_fill', 'all'))
            enable_rim  = enable_key and (mode == 'all')
            _spawnLightRig(
                cur_spec, geom,
                enable_ambient=True,
                enable_key=enable_key,
                enable_fill=enable_fill,
                enable_rim=enable_rim,
                enable_shadows=enable_shadows,
            )
            rig_spawned = True
            _dbg(
                "spawned rig "
                f"keyCastsShadows={_keyCastsShadows} shadowRes={_shadowMapRes} "
                f"filmArea={_shadowFilmArea} followDist={_shadowFollowDist}"
            )
        else:
            _dbg("bisect: skipping light rig spawn (step<2)")

        # Only run shadow diagnostics when we actually spawned a rig.
        if rig_spawned:
            try:
                _spawnShadowTestScene()
            except Exception:
                pass
            # Renderer capability debug (shadow maps rely on these).
            try:
                gsg = base.win.getGsg() if getattr(base, 'win', None) else None
                if gsg:
                    try:
                        supportsFBO = gsg.getSupportsFramebuffer() if hasattr(gsg, 'getSupportsFramebuffer') else 'n/a'
                    except Exception:
                        supportsFBO = 'n/a'
                    try:
                        supportsBasic = gsg.getSupportsBasicShaders() if hasattr(gsg, 'getSupportsBasicShaders') else 'n/a'
                    except Exception:
                        supportsBasic = 'n/a'
                    try:
                        maxTex = gsg.getMaxTextureDimension() if hasattr(gsg, 'getMaxTextureDimension') else 'n/a'
                    except Exception:
                        maxTex = 'n/a'

                    _dbg(f"gsg supportsFBO={supportsFBO} supportsBasicShaders={supportsBasic} maxTexDim={maxTex}")
                    try:
                        _dbg(f"panda version={PandaSystem.getGlobalPtr().getVersionString()}")
                    except Exception:
                        pass
                    try:
                        import panda3d.core as _p3c
                        _dbg(f"python exe={sys.executable}")
                        _dbg(f"panda3d.core file={getattr(_p3c, '__file__', 'n/a')}")
                    except Exception:
                        pass

                    try:
                        vendor = gsg.getDriverVendor() if hasattr(gsg, 'getDriverVendor') else 'n/a'
                    except Exception:
                        vendor = 'n/a'
                    try:
                        renderer = gsg.getDriverRenderer() if hasattr(gsg, 'getDriverRenderer') else 'n/a'
                    except Exception:
                        renderer = 'n/a'
                    try:
                        version = gsg.getDriverVersion() if hasattr(gsg, 'getDriverVersion') else 'n/a'
                    except Exception:
                        version = 'n/a'
                    _dbg(f"gsg driver vendor={vendor} renderer={renderer} version={version}")

                    try:
                        pipe = getattr(base, 'pipe', None)
                        pipeType = pipe.getType().getName() if pipe and hasattr(pipe, 'getType') else 'n/a'
                    except Exception:
                        pipeType = 'n/a'
                    try:
                        iface = pipe.getInterfaceName() if pipe and hasattr(pipe, 'getInterfaceName') else 'n/a'
                    except Exception:
                        iface = 'n/a'
                    try:
                        loadDisplay = ConfigVariableString('load-display', '').value
                    except Exception:
                        loadDisplay = 'n/a'
                    _dbg(f"pipe type={pipeType} interface={iface} prc load-display={loadDisplay}")
            except Exception:
                pass
        if not _supportsBasicShaders():
            _dbg("basic shaders unsupported; shadow maps disabled (using OTP drop shadows instead)")
        # Deferred shadow buffer allocation check and fallback retry:
        # Buffer/texture allocation happens asynchronously on the Draw thread,
        # so we schedule a check after 0.5s. If allocation failed, we fall back
        # to a lower resolution or disable shadows, avoiding multiple conflicting
        # setShadowCaster calls in the same frame.
        try:
            taskMgr.remove('outdoorLightingShadowAllocDebug')
        except Exception:
            pass

        def _shadowAllocDebug(task):
            global _shadowMapRes, _keyCastsShadows
            try:
                if not (_keyLightNp and not _keyLightNp.isEmpty()):
                    _dbg("shadowAllocDebug: key light NP missing")
                    return task.done
                k = _keyLightNp.getNode(0)
                _dbg(f"shadowAllocDebug: isShadowCaster={getattr(k, 'isShadowCaster', lambda: 'n/a')()}")
                gsg = None
                try:
                    gsg = base.win.getGsg() if getattr(base, 'win', None) else None
                except Exception:
                    gsg = None
                try:
                    if gsg:
                        _dbg(
                            "shadowAllocDebug: gsg "
                            f"supportsFBO={getattr(gsg, 'getSupportsFramebuffer', lambda: 'n/a')()} "
                            f"supportsBasicShaders={getattr(gsg, 'getSupportsBasicShaders', lambda: 'n/a')()} "
                            f"supportsDepthTex={getattr(gsg, 'getSupportsDepthTexture', lambda: 'n/a')()} "
                            f"maxTexDim={getattr(gsg, 'getMaxTextureDimension', lambda: 'n/a')()}"
                        )
                except Exception:
                    pass

                def _call_shadow_accessor(name: str):
                    if not hasattr(k, name):
                        return None
                    fn = getattr(k, name)
                    # Panda3D builds differ: some take (gsg, i), others (gsg) returning list-like,
                    # others take (i) (rare). Try common signatures.
                    for args in ((gsg, 0), (gsg,), (0,)):
                        try:
                            if gsg is None and args and args[0] is gsg:
                                continue
                            v = fn(*args)
                            _dbg(f"shadowAllocDebug: {name}{args}={'ok' if v else 'none'}")
                            return v
                        except TypeError as e:
                            last = e
                        except Exception as e:
                            _dbg(f"shadowAllocDebug: {name}{args} exception: {e!r}")
                            return None
                    try:
                        _dbg(f"shadowAllocDebug: {name} signature mismatch: {last!r}")
                    except Exception:
                        pass
                    return None

                buf = _call_shadow_accessor('getShadowBuffer')

                # If the light is configured to cast shadows, but the shadow buffer isn't allocating, retry at smaller resolutions.
                if getattr(k, 'isShadowCaster', lambda: False)() and (buf is None) and hasattr(k, 'setShadowCaster') and gsg:
                    if not gsg.getSupportsBasicShaders():
                        print("[DEBUG VideoSettings] shadowAllocDebug: GSG reports getSupportsBasicShaders() is False. Disabling shadow maps to prevent GL errors.")
                        k.setShadowCaster(False)
                        _keyCastsShadows = False
                    else:
                        if _shadowMapRes > 1024:
                            retry_res = 1024
                        elif _shadowMapRes > 512:
                            retry_res = 512
                        else:
                            retry_res = 0

                        if retry_res > 0:
                            print(f"[DEBUG VideoSettings] shadowAllocDebug: shadow buffer not allocated at {_shadowMapRes}. Falling back to {retry_res}...")
                            try:
                                k.setShadowCaster(True, retry_res, retry_res)
                                try:
                                    k.setCameraMask(_SHADOW_CAM_MASK)
                                except Exception:
                                    pass
                                _shadowMapRes = retry_res
                                _dbg(f"shadowAllocDebug: retry setShadowCaster({retry_res}) scheduled")
                                taskMgr.doMethodLater(0.5, _shadowAllocDebug, 'outdoorLightingShadowAllocDebug')
                            except Exception as e:
                                print(f"[DEBUG VideoSettings] shadowAllocDebug: retry setShadowCaster({retry_res}) failed: {e!r}")
                                _dbg(f"shadowAllocDebug: retry setShadowCaster({retry_res}) exception: {e!r}")
                        else:
                            print(f"[DEBUG VideoSettings] shadowAllocDebug: shadow buffer not allocated at {_shadowMapRes}. Disabling shadow maps completely.")
                            k.setShadowCaster(False)
                            _keyCastsShadows = False
                return task.done
            except Exception as e:
                _dbg(f"shadowAllocDebug exception: {e!r}")
                return task.done

        taskMgr.doMethodLater(0.5, _shadowAllocDebug, 'outdoorLightingShadowAllocDebug')
        try:
            la = base.render.getAttrib(LightAttrib.getClassType())
            if la is not None:
                try:
                    num_on = la.getNumOnLights()
                except Exception:
                    num_on = None
                _dbg(f"render LightAttrib onLights={num_on}")
        except Exception:
            pass
        try:
            if _keyLightNp is not None and not _keyLightNp.isEmpty():
                _dbg(f"key light node={_keyLightNp.getNode(0)}")
        except Exception:
            pass
        if _bisectAllows(5):
            _applyFog(cur_spec)
            _tintSky(cur_spec)
            _applyBackgroundColor(cur_spec)
        if _bisectAllows(6):
            _setupProceduralSky(cur_spec)
        if _OUTDOOR_SHADER_BISECT_LEVEL >= 2 and _bisectAllows(7):
            _setupPostProcess(cur_spec)
        if _OUTDOOR_SHADER_BISECT_LEVEL >= 3 and _bisectAllows(9):
            _setupAllWater(geom, cur_spec)
        _dimSkyForLights()
        # Full-window + per-DisplayRegion pixel_zoom (see _maintainOutdoorLightingViewport).
        _maintainOutdoorLightingViewport()
        # Run before most gameplay (low sort = earlier): keep viewports patched pre-cull.
        # When bisecting at shader-auto only (step 1), avoid running the update task
        # since it can trigger deferred rig rebuilds or other side effects.
        if _bisectAllows(2):
            taskMgr.add(_lightingUpdateTask, _godRaysTaskName, sort=-60)

    _refCount += 1

    if geom is not None and not geom.isEmpty():
        # Also clear any local light overrides on the zone root so our rig lights
        # can actually affect it (and therefore generate visible shading/shadows).
        try:
            if hasattr(geom, 'clearLightOff'):
                geom.clearLightOff()
            try:
                geom.clearAttrib(LightAttrib.getClassType())
            except Exception:
                pass
        except Exception:
            pass
        geom.setShaderAuto()
        # Force a full normals rescan at begin() time. The pre-flatten call sets
        # _NORMALS_TAG on the geom root, but distributed objects added between load
        # and begin() may have attached new geometry without normals. Clear the tag
        # so _ensureNormals sees all current GeomNodes, not just the original set.
        try:
            if geom is not None and not geom.isEmpty():
                geom.setPythonTag(_NORMALS_TAG, None)
        except Exception:
            pass
        try:
            _ensureNormals(geom)
        except Exception:
            pass
        # Ensure nothing in the zone subtree disables shaders; shadow receiving
        # requires the auto-shader path to be active.
        try:
            _forceShadersOnSubtree(geom)
        except Exception:
            pass
        # Normals injection changes the vertex format; force shader regen so the
        # auto-shader (including shadow sampling) gets rebuilt on the new format.
        try:
            _forceShaderRegen(geom)
        except Exception:
            pass
        _forceLightingOnSubtree(geom)
        _hidePlaneLikeCastersFromShadow(geom)
        try:
            hood = _getHood()
            if hood and getattr(hood, 'sky', None) and not hood.sky.isEmpty():
                hood.sky.hide(_SHADOW_CAM_MASK)
        except Exception:
            pass
        # Do not force a specular material on the entire zone geometry. Zone
        # meshes are frequently large, use vertex colors, and may contain
        # mixed material setups; forcing a specular material globally can
        # introduce view-dependent color artifacts. Specular remains available
        # opt-in via `lighting-specular-enabled` on specific subtrees.
        try:
            la = geom.getAttrib(LightAttrib.getClassType())
            _dbg(f"geom LightAttrib present={la is not None}")
        except Exception:
            pass
        try:
            ra = base.render.getAttrib(LightAttrib.getClassType())
            _dbg(f"render LightAttrib present={ra is not None}")
        except Exception:
            pass

        # Debug: shader state + normals presence (flat lighting can be caused by missing normals).
        try:
            if _debugEnabled():
                try:
                    _dbg(f"geom hasShader={'yes' if geom.hasShader() else 'no'}")
                except Exception:
                    pass
                try:
                    _dbg(f"render hasShader={'yes' if base.render.hasShader() else 'no'}")
                except Exception:
                    pass
                try:
                    sa = base.render.getAttrib(ShaderAttrib.getClassType())
                    _dbg(f"render ShaderAttrib present={sa is not None}")
                    if sa is not None:
                        try:
                            sh = sa.getShader()
                            _dbg(f"render ShaderAttrib shader={'ok' if sh else 'none'}")
                        except Exception:
                            pass
                        for meth in ('getAutoShader', 'getFlag'):
                            if hasattr(sa, meth):
                                try:
                                    _dbg(f"render ShaderAttrib {meth}()={getattr(sa, meth)()}")
                                except Exception:
                                    pass
                except Exception:
                    pass
                try:
                    sa = geom.getAttrib(ShaderAttrib.getClassType())
                    _dbg(f"geom ShaderAttrib present={sa is not None}")
                    if sa is not None:
                        try:
                            sh = sa.getShader()
                            _dbg(f"geom ShaderAttrib shader={'ok' if sh else 'none'}")
                        except Exception:
                            pass
                        for meth in ('getAutoShader', 'getFlag'):
                            if hasattr(sa, meth):
                                try:
                                    _dbg(f"geom ShaderAttrib {meth}()={getattr(sa, meth)()}")
                                except Exception:
                                    pass
                except Exception:
                    pass
                try:
                    nodes = geom.findAllMatches('**/+GeomNode')
                    total = nodes.getNumPaths()
                    with_normals = 0
                    checked = min(total, 50)
                    for i in range(checked):
                        gnp = nodes.getPath(i).node()
                        if gnp.getNumGeoms() <= 0:
                            continue
                        g = gnp.getGeom(0)
                        vdata = g.getVertexData()
                        if vdata and vdata.hasColumn('normal'):
                            with_normals += 1
                    _dbg(f"geom geomNodes={total} checked={checked} withNormals={with_normals}")
                except Exception:
                    pass
        except Exception:
            pass
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
    _syncBase()
    global _refCount, _activeGeom
    if not _wantFx():
        return
    _dbg(f"end(refCount={_refCount}) geom={'ok' if (geom is not None and not geom.isEmpty()) else 'none'}")

    if geom is not None and not geom.isEmpty():
        geom.clearShader()
        _clearDefaultSpecularMaterial(geom)
    lav = getattr(base, 'localAvatar', None)
    if lav is not None and not lav.isEmpty():
        lav.clearShader()

    if _refCount > 0:
        _refCount -= 1

    if _refCount == 0:
        _activeGeom = None
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
    _syncBase()
    if not _wantFx() or np is None or np.isEmpty():
        return
    np.setShaderAuto()
    _forceLightingOnSubtree(np)
    _hidePlaneLikeCastersFromShadow(np)
    _applyDefaultSpecularMaterial(np)


def clearExtraSubtree(np) -> None:
    """Remove auto-shading from an extra outdoor NodePath."""
    _syncBase()
    if not _wantFx() or np is None or np.isEmpty():
        return
    np.clearShader()
    _clearDefaultSpecularMaterial(np)

def _maybeRebuildLightRig(spec: dict) -> None:
    global _lightRig, _keyCastsShadows, _shadowMapRes, _prevShadowCasterState, _activeGeom
    # Check if shadow settings changed.
    current_wants_shadow = _keyCastsShadows
    current_res = _shadowMapRes

    wants_shadow = (spec.get('shadowCaster', False)
                    and _wantDynamicShadows()
                    and _shadowQuality() != 'off')
    
    # Determine the resolution snap-down
    res = 1024
    if wants_shadow:
        try:
            res = _scaledShadowRes(spec)
            # Apply clamps similar to _spawnLightRig
            gsg = base.win.getGsg() if getattr(base, 'win', None) else None
            if gsg:
                try:
                    max_dim = int(gsg.getMaxTextureDimension())
                    if max_dim and res > max_dim:
                        res = max_dim
                except Exception:
                    pass
            if res >= 4096: res = 4096
            elif res >= 2048: res = 2048
            elif res >= 1024: res = 1024
            else: res = 512
        except Exception:
            pass

    need_rebuild = (_lightRig is None or _lightRig.isEmpty() or 
                    wants_shadow != current_wants_shadow or 
                    (wants_shadow and res != current_res))

    if need_rebuild:
        print(f"[DEBUG VideoSettings] _maybeRebuildLightRig: Rebuilding light rig (wants_shadow={wants_shadow}, res={res})...")
        savedBounds = None
        if _shadowFocusPos is not None:
            savedBounds = (Vec3(_shadowFocusPos), float(_shadowSceneRadius))
        _destroyLightRig()
        _spawnLightRig(spec, geom=_activeGeom, shadowBounds=savedBounds)
        if _activeGeom is not None and not _activeGeom.isEmpty():
            try:
                _activeGeom.setShaderAuto()
                _forceShadersOnSubtree(_activeGeom)
                _forceShaderRegen(_activeGeom)
                _forceLightingOnSubtree(_activeGeom)
                _hidePlaneLikeCastersFromShadow(_activeGeom)
            except Exception as e:
                print(f"[DEBUG VideoSettings] _maybeRebuildLightRig: geom shader regen exception: {e!r}")
        lav = getattr(base, 'localAvatar', None)
        if lav is not None and not lav.isEmpty():
            try:
                _forceShaderRegen(lav)
            except Exception as e:
                print(f"[DEBUG VideoSettings] _maybeRebuildLightRig: localAvatar shader regen exception: {e!r}")
        print("[DEBUG VideoSettings] _maybeRebuildLightRig: Light rig rebuilt successfully.")
    else:
        print("[DEBUG VideoSettings] _maybeRebuildLightRig: Shadow settings unchanged. Updating light rig in-place...")
        _prevShadowCasterState = wants_shadow
        _applyProfileLive(spec)
        print("[DEBUG VideoSettings] _maybeRebuildLightRig: Light rig update complete.")


def refreshSettings() -> None:
    """Hot-reload all active lighting parameters from current user settings.

    Called by the Lighting settings tab whenever the player changes a slider
    or toggle.  All systems are updated in-place where possible.
    """
    print("[DEBUG VideoSettings] OutdoorLighting.refreshSettings: starting...")
    _syncBase()
    if _refCount == 0:
        print("[DEBUG VideoSettings] OutdoorLighting.refreshSettings: refCount is 0, returning.")
        return

    # In Cull/Draw threading mode the Draw thread is always active (2 frames
    # behind App) and holds the GL context mutex while rendering.  Destroying
    # and recreating shadow-map FBOs (via _destroyLightRig / _spawnLightRig)
    # and bloom FBOs (via _destroyPostProcess / _setupPostProcess) while Draw
    # holds the GL context causes a permanent deadlock.  syncFrame() blocks
    # until the current Cull and Draw passes both finish, giving us a clean
    # pipeline before we touch any offscreen buffers.
    try:
        if base is not None and base.config.GetString('threading-model', ''):
            print("[DEBUG VideoSettings] OutdoorLighting.refreshSettings: calling graphicsEngine.syncFrame()...")
            base.graphicsEngine.syncFrame()
            print("[DEBUG VideoSettings] OutdoorLighting.refreshSettings: graphicsEngine.syncFrame() returned.")
    except Exception as e:
        print(f"[DEBUG VideoSettings] OutdoorLighting.refreshSettings: syncFrame exception: {e!r}")

    # Always keep OTP blob/drop shadows in sync with user settings.
    # (These work even when shaders are unavailable.)
    if _OTPDropshadow:
        try:
            shadow_flag = 1 if _settingsBool('dynamic-shadows', True) else 0
            print(f"[DEBUG VideoSettings] OutdoorLighting.refreshSettings: setting global drop shadow flag={shadow_flag}...")
            _OTPDropshadow.setGlobalDropShadowFlag(shadow_flag)
        except Exception as e:
            print(f"[DEBUG VideoSettings] OutdoorLighting.refreshSettings: setGlobalDropShadowFlag exception: {e!r}")
        try:
            shadow_strength = float(_settingsFloat('drop-shadow-strength', 0.5))
            print(f"[DEBUG VideoSettings] OutdoorLighting.refreshSettings: setting global drop shadow gray level={shadow_strength}...")
            _OTPDropshadow.setGlobalDropShadowGrayLevel(shadow_strength)
        except Exception as e:
            print(f"[DEBUG VideoSettings] OutdoorLighting.refreshSettings: setGlobalDropShadowGrayLevel exception: {e!r}")

    spec = _getActiveSpec()

    # Maybe rebuild light rig (avoids recreation if settings are unchanged).
    _maybeRebuildLightRig(spec)

    print("[DEBUG VideoSettings] OutdoorLighting.refreshSettings: applying fog and sky color...")
    _clearFog()
    _applyFog(spec)
    _tintSky(spec)
    _applyBackgroundColor(spec)

    # Procedural sky toggle.
    want_sky = _wantProceduralSky()
    print(f"[DEBUG VideoSettings] OutdoorLighting.refreshSettings: procedural sky want_sky={want_sky}")
    if want_sky:
        if _proceduralSky is None:
            print("[DEBUG VideoSettings] OutdoorLighting.refreshSettings: setting up procedural sky...")
            _setupProceduralSky(spec)
        elif _proceduralSky is not None:
            print("[DEBUG VideoSettings] OutdoorLighting.refreshSettings: updating procedural sky...")
            _proceduralSky.setStyle(_activeStyle)
            _proceduralSky.update(spec, _timeOfDay)
    else:
        print("[DEBUG VideoSettings] OutdoorLighting.refreshSettings: destroying procedural sky...")
        _destroyProceduralSky()
        _tintSky(spec)

    # Bloom + sun-ray overlay
    print("[DEBUG VideoSettings] OutdoorLighting.refreshSettings: destroying post process...")
    _destroyPostProcess()
    if _OUTDOOR_SHADER_BISECT_LEVEL >= 2:
        print("[DEBUG VideoSettings] OutdoorLighting.refreshSettings: setting up post process...")
        _setupPostProcess(spec)
    print("[DEBUG VideoSettings] OutdoorLighting.refreshSettings: finished successfully.")


def setTimeOfDay(hours: float) -> None:
    """Set the current in-game time of day (0–24)."""
    _syncBase()
    global _timeOfDay
    _timeOfDay = float(hours) % 24.0
    if _refCount > 0:
        cur = _getActiveSpec()
        _maybeRebuildLightRig(cur)
        _clearFog()
        _applyFog(cur)
        _tintSky(cur)
        _applyBackgroundColor(cur)
        _updateBloomLive(cur)
        if _proceduralSky:
            _proceduralSky.update(cur, _timeOfDay)


def setupWaterReflection(waterNodePath, profile: dict | None = None) -> None:
    """Manually set up planar reflections on a specific water NodePath."""
    _syncBase()
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
    _syncBase()
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
