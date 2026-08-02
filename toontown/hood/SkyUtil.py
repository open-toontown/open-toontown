from panda3d.core import *
from toontown.toonbase.ToontownGlobals import *
from direct.task.Task import Task
from direct.directnotify import DirectNotifyGlobal
notify = DirectNotifyGlobal.directNotify.newCategory('SkyUtil')


def cloudSkyTrack(task):
    task.h += globalClock.getDt() * 0.25
    if task.cloud1.isEmpty() or task.cloud2.isEmpty():
        notify.warning("Couln't find clouds!")
        return Task.done
    task.cloud1.setH(task.h)
    task.cloud2.setH(-task.h * 0.8)
    return Task.cont


def _wantProceduralSky() -> bool:
    """Returns True if the player has enabled the procedural sky system."""
    try:
        from toontown.hood import OutdoorLighting as osl
        if getattr(osl, '_OUTDOOR_SHADER_BISECT_LEVEL', 0) < 1:
            return False
    except Exception:
        pass
    try:
        from toontown.toonbase.ToonBaseGlobal import base
        val = base.settings.getSetting('want-procedural-sky', True)
        if val is not None:
            return bool(val)
    except Exception:
        pass
    try:
        from panda3d.core import ConfigVariableBool
        return ConfigVariableBool('want-procedural-sky', True).value
    except Exception:
        return True


def startCloudSky(hood, parent=camera,
                  effects=CompassEffect.PRot | CompassEffect.PZ):
    """Set up the sky for a hood that has rotating clouds.

    When 'want-procedural-sky' is enabled (default), OutdoorLighting will hide
    the legacy model sky once the procedural GLSL dome is successfully attached.
    We keep the legacy sky node intact so it can act as a fallback if shaders
    are unavailable.
    """
    # Important: OutdoorLighting owns ProceduralSky attach/hide/show behavior.
    # Do NOT delete/replace hood.sky here; if the shader fails to load, we need
    # the legacy model sky to remain available as a fallback.

    # ── Legacy model sky path (ProceduralSky disabled or shaders unavailable) ──
    try:
        hood.sky.reparentTo(parent)
        hood.sky.setDepthTest(0)
        hood.sky.setDepthWrite(0)
        hood.sky.setBin('background', 100)
    except Exception:
        pass
    try:
        hood.sky.find('**/Sky').reparentTo(hood.sky, -1)
    except Exception:
        pass
    try:
        hood.sky.reparentTo(parent)
        hood.sky.setZ(0.0)
        hood.sky.setHpr(0.0, 0.0, 0.0)
        ce = CompassEffect.make(NodePath(), effects)
        hood.sky.node().setEffect(ce)
    except Exception:
        pass

    # If ProceduralSky is enabled, OutdoorLighting will typically hide the legacy
    # sky; skip the legacy rotating-cloud task to avoid wasted work.
    if _wantProceduralSky():
        return

    # Start the rotating-cloud animation task (legacy only).
    skyTrackTask = Task(hood.skyTrack)
    skyTrackTask.h = 0
    try:
        skyTrackTask.cloud1 = hood.sky.find('**/cloud1')
        skyTrackTask.cloud2 = hood.sky.find('**/cloud2')
        if not skyTrackTask.cloud1.isEmpty() and not skyTrackTask.cloud2.isEmpty():
            taskMgr.add(skyTrackTask, 'skyTrack')
        else:
            notify.warning("Couldn't find clouds!")
    except Exception:
        notify.warning("Couldn't find clouds!")
