from panda3d.core import (BitMask32, CollisionHandlerFloor,
                          CollisionHandlerQueue, CollisionNode, CollisionRay,
                          CollisionSegment, CollisionTraverser, NodePath,
                          Vec3, WindowProperties)
from direct.directnotify import DirectNotifyGlobal
from direct.fsm.FSM import FSM
from direct.showbase.InputStateGlobal import inputState
from direct.showbase.PythonUtil import fitSrcAngle2Dest, reduceAngle
from direct.task import Task
from direct.task.TaskManagerGlobal import taskMgr

from otp.otpbase import OTPGlobals
from toontown.toon.CamRunner import CamRunner
from toontown.toon.ParamObj import ParamObj


def _angleLerpToward(current, target, alpha):
    """Lerp between two headings (degrees) taking the shortest arc."""
    diff = ((target - current) + 180.0) % 360.0 - 180.0
    return current + diff * alpha


class OrbitalCamera(FSM, NodePath, ParamObj):
    """
    Modern third-person orbital camera for Toontown.

    Architecture
    ------------
    The orbit rig is a NodePath reparented to the local toon.  Its pivot is
    at head height.  The actual camera sits at (0, -distance, 0) in rig-local
    space.  Heading (H) and pitch (P) of the rig control where the camera
    orbits; distance controls how far back it sits.

    Three independent desired values track what the player *wants*:
        _desiredH, _desiredP, _desiredDistance

    Three smoothed actual values chase the desired values each frame:
        _actualH, _actualP, _actualDistance

    A wall-collision ray (fixed in rig-local space, swept by H/P) determines
    _collisionDistance, which caps _actualDistance from above so the camera
    never clips through geometry.  Pull-in is fast; release is slow so the
    camera eases back out instead of snapping.
    """

    notify = DirectNotifyGlobal.directNotify.newCategory("OrbitalCamera")

    # ParamObj compatibility – not used in core logic, kept for API compat
    class ParamSet(ParamObj.ParamSet):
        Params = {"camOffset": Vec3(0, -14, 0)}

    # Task name constants
    UpdateTaskName      = "OrbitCamUpdateTask"
    ReadMouseTaskName   = "OrbitCamReadMouseTask"
    AvatarFacingTaskName = "OrbitCamAvatarFacingTask"

    # Orbit angle limits (degrees)
    MinP = -50.0
    MaxP = 20.0

    # Optional heading lock (set by external code; None = free)
    baseH = None
    minH  = None
    maxH  = None

    # Tab-key presets  [{dist, p}]
    presets = [
        {"dist": 14.0, "p": -20.0},
        {"dist": 24.0, "p": -10.0},
        {"dist":  5.0, "p":  -5.0},
    ]

    TopNodeName      = "OrbitCam"
    _MinCamDistance  = 1.5
    _MaxCamDistance  = 30.0
    _MaxMouseDelta   = 100.0
    _CollisionBuffer = 0.35

    # Smoothing speeds expressed as "fraction closed per frame at 60 fps".
    # Frame-rate-independent via:  alpha = 1 - (1 - speed)^(dt * 60)
    _OrbitSmoothSpeed    = 0.25   # H / P orbit follow speed
    _DistancePullSpeed   = 0.88   # fast pull-in when wall is found
    _DistanceReleaseSpeed = 0.05  # slow ease-out when wall clears

    # ------------------------------------------------------------------ #
    #  Construction / destruction                                          #
    # ------------------------------------------------------------------ #

    def __init__(self, subject):
        ParamObj.__init__(self)
        NodePath.__init__(self, self.TopNodeName)
        FSM.__init__(self, "OrbitalCamera")

        self.subject      = subject
        self._paramStack  = []
        self.setDefaultParams()
        self.presetPos    = 0

        self.__inputEnabled = False
        self.mouseControl   = False
        self.mouseDelta     = (0, 0)
        self.lastMousePos   = (0.0, 0.0)
        self.origMousePos   = (0, 0)

        self._rmbToken   = inputState.watchWithModifiers("RMB", "mouse3")
        self.firstPerson = False
        self.ignoreRMB   = False
        self.cam_toggled = False
        self.runner      = CamRunner()
        self._oldWASDTurn = None

        # ---- Desired state (user input) --------------------------------
        self._desiredH        = 0.0
        self._desiredP        = -20.0
        self._desiredDistance = 14.0

        # ---- Smoothed actual state -------------------------------------
        self._actualH        = 0.0
        self._actualP        = -20.0
        self._actualDistance = 14.0

        # Maximum distance allowed by collision this frame
        self._collisionDistance = self._MaxCamDistance

        self._active = False
        self.request('Off')

        self.initializeCollisions()

    def destroy(self):
        if self.isActive():
            self.request('Off')
        self.destroyCollisions()
        self._rmbToken.release()
        del self._rmbToken
        del self.subject
        FSM.cleanup(self)
        ParamObj.destroy(self)
        self.ignoreAll()
        if not self.isEmpty():
            self.removeNode()

    # ------------------------------------------------------------------ #
    #  Floor-ray collision nodes (zone on/off-floor signals)              #
    # ------------------------------------------------------------------ #

    def initializeCollisions(self):
        self.cTravOnFloor    = CollisionTraverser("CamMode.cTravOnFloor")
        self.camFloorRayNode = self.attachNewNode("camFloorRayNode")
        self.ccRay2          = CollisionRay(0, 0, 0, 0, 0, -1)
        self.ccRay2Node      = CollisionNode("ccRay2Node")
        self.ccRay2Node.addSolid(self.ccRay2)
        self.ccRay2NodePath  = self.camFloorRayNode.attachNewNode(self.ccRay2Node)
        self.ccRay2Node.setFromCollideMask(OTPGlobals.FloorBitmask)
        self.ccRay2Node.setIntoCollideMask(BitMask32.allOff())
        self.ccRay2MoveNodePath = hidden.attachNewNode("ccRay2MoveNode")
        self.camFloorCollisionBroadcaster = CollisionHandlerFloor()
        self.camFloorCollisionBroadcaster.setInPattern("zone_on-floor")
        self.camFloorCollisionBroadcaster.setOutPattern("zone_off-floor")
        self.camFloorCollisionBroadcaster.addCollider(
            self.ccRay2NodePath, self.ccRay2MoveNodePath)
        self.cTravOnFloor.addCollider(
            self.ccRay2NodePath, self.camFloorCollisionBroadcaster)

    def destroyCollisions(self):
        del self.cTravOnFloor
        del self.ccRay2
        del self.ccRay2Node
        self.ccRay2NodePath.remove_node()
        del self.ccRay2NodePath
        self.ccRay2MoveNodePath.remove_node()
        del self.ccRay2MoveNodePath
        self.camFloorRayNode.remove_node()
        del self.camFloorRayNode

    # ------------------------------------------------------------------ #
    #  FSM states                                                          #
    # ------------------------------------------------------------------ #

    def enterActive(self):
        self._active      = True
        self.cam_toggled  = not self.cam_toggled

        self._loadSettings()
        self.enableInput()
        # Orbit camera expects strafe-style movement (A/D = strafe) and
        # camera-relative facing while moving. Disable turn input while orbit
        # camera is active; the toon will face the orbit heading instead.
        if getattr(self.subject, 'controlManager', None):
            try:
                self._oldWASDTurn = getattr(self.subject.controlManager, '_ControlManager__WASDTurn', None)
            except Exception:
                self._oldWASDTurn = None
            try:
                self.subject.controlManager.setWASDTurn(False)
            except Exception:
                pass
            try:
                self.subject.controlManager.setTurn(0)
            except Exception:
                pass
        base.camNode.setLodCenter(self.subject)
        self._startWallCheck()
        self.acceptWheel()
        self.acceptTab()

        # Reparent rig to toon, pivot at head height
        self.reparentTo(self.subject)
        self.setPos(0, 0, self.subject.getHeight())
        self.setScale(1)
        self.setR(0)

        # Start camera behind toon with zero visible pop
        self._desiredH = self.subject.getH(render)
        self._actualH  = self._desiredH
        self._collisionDistance = self._MaxCamDistance

        base.camera.reparentTo(self)
        base.camera.setScale(1)
        self._applyTransform()

        # Must run *before* GravityWalker.handleAvatarControls (priority 25): movement
        # uses avatar heading, and we set camera-relative facing here. When this ran
        # at 40, facing updated after the walker — strafe/back only rotated the model.
        taskMgr.add(self._cameraUpdateTask, self.UpdateTaskName, priority=22)

    def exitActive(self):
        self._active = False
        taskMgr.remove(self.UpdateTaskName)
        self._stopWallCheck()
        base.camNode.setLodCenter(NodePath())
        self.ignoreWheel()
        self.ignoreTab()
        self.disableInput()
        if getattr(self.subject, 'controlManager', None):
            try:
                self.subject.controlManager.setTurn(1)
            except Exception:
                pass
            # Restore previous WASD turn/strafe mode if we were able to read it.
            if self._oldWASDTurn is not None:
                try:
                    self.subject.controlManager.setWASDTurn(bool(self._oldWASDTurn))
                except Exception:
                    pass
        if not base.camera.isEmpty() and base.camera.getParent() == self:
            base.camera.wrtReparentTo(self.subject)
        if not self.isEmpty() and self.getParent() == self.subject:
            self.detachNode()

    def enterOff(self):
        pass

    def exitOff(self):
        pass

    # ------------------------------------------------------------------ #
    #  Camera placement                                                    #
    # ------------------------------------------------------------------ #

    def _applyTransform(self):
        """
        Push the smoothed orbit state onto the scene graph.
        The rig's heading and pitch drive the orbit orientation; the camera
        always sits at (0, -distance, 0) in rig-local space.
        """
        self.setH(render, self._actualH)
        self.setP(self._actualP)
        self.setR(0)
        base.camera.setPos(self, Vec3(0, -self._actualDistance, 0))
        base.camera.setHpr(self, Vec3(0, 0, 0))
        base.camera.setScale(1)

    # ------------------------------------------------------------------ #
    #  Settings                                                            #
    # ------------------------------------------------------------------ #

    def _loadSettings(self):
        """Load persistent camera settings from useropt.json."""
        try:
            dist = float(base.settings.getSetting('cam-distance', 14.0))
            dist = max(self._MinCamDistance, min(self._MaxCamDistance, dist))
            self._desiredDistance = dist
            self._actualDistance  = dist
        except Exception:
            pass

    def onSettingsChanged(self):
        """Call this after writing new camera settings from the options menu."""
        self._loadSettings()

    # ------------------------------------------------------------------ #
    #  Main per-frame update task  (runs every frame while Active)         #
    # ------------------------------------------------------------------ #

    def _calcAlpha(self, speed, dt):
        """Frame-rate-independent lerp coefficient from a per-60fps speed."""
        return 1.0 - pow(max(0.0, 1.0 - speed), dt * 60.0)

    def _cameraUpdateTask(self, task):
        if self.oobeEnabled():
            return task.cont

        try:
            dt = globalClock.getDt()
            dt = max(0.0, min(dt, 0.1))  # guard against spike frames
        except Exception:
            dt = 1.0 / 60.0

        # 1. Consume mouse delta when in orbit-look mode ─────────────────
        if self.mouseControl and (self.mouseDelta[0] or self.mouseDelta[1]):
            self._applyMouseDelta()
        self.mouseDelta = (0, 0)

        # 2. Run wall-collision check ─────────────────────────────────────
        self._runCollision()

        # 3. Smooth orbit heading (H) and pitch (P) ───────────────────────
        orbitAlpha     = self._calcAlpha(self._OrbitSmoothSpeed, dt)
        self._actualH  = _angleLerpToward(self._actualH, self._desiredH, orbitAlpha)
        self._actualP += (self._desiredP - self._actualP) * orbitAlpha

        # 4. Smooth camera distance ───────────────────────────────────────
        targetDist = max(self._MinCamDistance,
                         min(self._desiredDistance, self._collisionDistance))
        # Fast pull-in when a wall is closer; slow ease-out when it clears
        if targetDist < self._actualDistance:
            distAlpha = self._calcAlpha(self._DistancePullSpeed, dt)
        else:
            distAlpha = self._calcAlpha(self._DistanceReleaseSpeed, dt)
        self._actualDistance += (targetDist - self._actualDistance) * distAlpha
        self._actualDistance  = max(self._MinCamDistance, self._actualDistance)

        # 5. Apply to scene graph ─────────────────────────────────────────
        self._applyTransform()

        # 6. Match RMB orbit-look: keep the toon facing the camera rig heading while
        #    moving so W/A/S/D use the same camera-relative walk as mouse-look (strafe
        #    is slide keys; forward/back along view — no separate "face movement" mode).
        if self.isSubjectMoving():
            try:
                self.subject.setH(render, self._actualH)
            except Exception:
                pass
        return task.cont

    def _applyMouseDelta(self):
        """Convert raw mouse delta into desired-orbit-state changes."""
        dx, dy = self.mouseDelta
        try:
            dx, dy = float(dx), float(dy)
        except Exception:
            return

        # Clamp to guard against pointer-warp / missed-frame spikes
        dx = max(-self._MaxMouseDelta, min(self._MaxMouseDelta, dx))
        dy = max(-self._MaxMouseDelta, min(self._MaxMouseDelta, dy))
        if dx == 0.0 and dy == 0.0:
            return

        try:
            mult = float(base.settings.getSetting('mouse-sensitivity', 1.0))
            mult = max(0.3, min(3.0, mult))
        except Exception:
            mult = 1.0

        try:
            invertY = bool(base.settings.getSetting('cam-invert-y', False))
        except Exception:
            invertY = False

        sens = 0.18 * mult

        # Horizontal orbit: mouse right (dx > 0) → heading decreases → camera orbits right
        self._desiredH += -dx * sens

        # Vertical orbit: without invert, mouse down (dy > 0) → pitch decreases → camera elevates
        pitchDir = 1.0 if invertY else -1.0
        self._desiredP = max(self.MinP,
                             min(self.MaxP, self._desiredP + dy * sens * pitchDir))

        # Optional heading bounds (set by external scene code)
        if self.baseH is not None:
            self._clampDesiredH()

        # When subject is moving, snap orbit heading so the toon immediately
        # faces the camera's look direction (no lag on deliberate turning).
        if self.isSubjectMoving():
            self.subject.setH(render, self._desiredH)
            self._actualH = self._desiredH

    def _clampDesiredH(self):
        currH = fitSrcAngle2Dest(self._desiredH, 180)
        if currH < self.minH:
            self._desiredH = reduceAngle(self.minH)
        elif currH > self.maxH:
            self._desiredH = reduceAngle(self.maxH)

    # ------------------------------------------------------------------ #
    #  Wall-collision check (runs inside _cameraUpdateTask each frame)    #
    # ------------------------------------------------------------------ #

    def _startWallCheck(self):
        """Build the collision segment and traverser for wall detection."""
        self._wallQueue  = CollisionHandlerQueue()
        self._wallCTrav  = CollisionTraverser("OrbitCam.wallTrav")

        # Segment from rig pivot (0,0,0) toward (0,-maxDist,0) in rig-local
        # space.  As H/P change the rig's orientation, the segment naturally
        # sweeps to where the camera would be.
        self._wallSolid = CollisionSegment(0, 0, 0,
                                           0, -(self._MaxCamDistance + 1.0), 0)
        wallNode = CollisionNode("OrbitCam.wallNode")
        wallNode.addSolid(self._wallSolid)
        wallNode.setFromCollideMask(
            OTPGlobals.CameraBitmask
            | OTPGlobals.CameraTransparentBitmask
            | OTPGlobals.FloorBitmask
        )
        wallNode.setIntoCollideMask(BitMask32.allOff())
        self._wallNp = self.attachNewNode(wallNode)
        self._wallCTrav.addCollider(self._wallNp, self._wallQueue)

    def _runCollision(self):
        """Traverse world geometry and update _collisionDistance."""
        if not hasattr(self, '_wallCTrav'):
            return

        self._wallCTrav.traverse(self.subject.getGeom())

        # Toon visibility: hide when too close or disguised
        if not self.firstPerson:
            visible = (not self.subject.isDisguised) and (self._actualDistance >= 2.0)
            if visible:
                self.subject.getGeomNode().show()
            else:
                self.subject.getGeomNode().hide()

        numEntries = self._wallQueue.getNumEntries()
        if numEntries == 0:
            self._collisionDistance = self._MaxCamDistance
            return

        self._wallQueue.sortEntries()
        entry = self._wallQueue.getEntry(0)
        if not (entry and entry.hasSurfacePoint()):
            self._collisionDistance = self._MaxCamDistance
            return

        # Hit point in rig-local space.  The segment runs along -Y, so the
        # length of the hit point equals the distance along the camera ray.
        hitLocal = entry.getSurfacePoint(self)
        hitDist  = Vec3(hitLocal).length()
        self._collisionDistance = max(self._MinCamDistance,
                                      hitDist - self._CollisionBuffer)

    def _stopWallCheck(self):
        if hasattr(self, '_wallCTrav') and hasattr(self, '_wallNp'):
            self._wallCTrav.removeCollider(self._wallNp)
        for attr in ('_wallQueue', '_wallCTrav', '_wallSolid'):
            if hasattr(self, attr):
                delattr(self, attr)
        if hasattr(self, '_wallNp'):
            self._wallNp.detachNode()
            del self._wallNp
        if self.subject:
            if self.subject.isDisguised:
                self.subject.getGeomNode().hide()
            else:
                self.subject.getGeomNode().show()

    # ------------------------------------------------------------------ #
    #  Mouse-look enable / disable                                         #
    # ------------------------------------------------------------------ #

    def enableMouseControl(self, pressed, toggle=False):
        if not toggle and (not pressed or self.ignoreRMB):
            return

        if not base.CAM_TOGGLE_LOCK:
            self.ignore("InputState-RMB")
            self.accept("InputState-RMB", self.disableMouseControl)
        else:
            self.ignore("InputState-RMB")
            self.accept("InputState-RMB", self.toggleMouseControl)

        if self.oobeEnabled():
            return

        self.mouseControl = True
        md = base.win.getPointer(0)
        self.origMousePos = (md.getX(), md.getY())
        cx, cy = base.win.getXSize() // 2, base.win.getYSize() // 2
        base.win.movePointer(0, cx, cy)
        md2 = base.win.getPointer(0)
        self.lastMousePos = (float(md2.getX()), float(md2.getY()))

        if self.getCurrentOrNextState() == "Active":
            self._startMouseTasks()

        self._setCursor(True)
        self.runner.startInput()
        self.subject.controlManager.setTurn(0)
        try:
            self.subject.controlManager.setWASDTurn(False)
        except Exception:
            pass

    def toggleMouseControl(self, pressed):
        if pressed and not self.mouseControl:
            self.enableMouseControl(True, False)
        elif pressed and self.mouseControl:
            self.disableMouseControl(True, True)

    def disableMouseControl(self, pressed, disabledByMouse=True):
        if not base.CAM_TOGGLE_LOCK:
            self.ignore("InputState-RMB")
            self.accept("InputState-RMB", self.enableMouseControl)
        else:
            self.ignore("InputState-RMB")
            self.accept("InputState-RMB", self.toggleMouseControl)

        if self.oobeEnabled():
            return

        if self.mouseControl:
            self.mouseControl = False
            self._stopMouseTasks()
            base.win.movePointer(0, int(self.origMousePos[0]),
                                       int(self.origMousePos[1]))
            self._setCursor(False)
            self.runner.stopInput()

        # While orbital is active, keep the same control lock as RMB (no keyboard turn).
        if getattr(self.subject, 'controlManager', None):
            try:
                if self.getCurrentOrNextState() == "Active":
                    self.subject.controlManager.setTurn(0)
                    self.subject.controlManager.setWASDTurn(False)
                else:
                    self.subject.controlManager.setTurn(1)
            except Exception:
                pass

    def _setCursor(self, hidden):
        wp = WindowProperties()
        wp.setCursorHidden(hidden)
        base.win.requestProperties(wp)

    def enableInput(self):
        self.__inputEnabled = True
        self.accept("InputState-RMB", self.enableMouseControl)
        if inputState.isSet("RMB"):
            self.enableMouseControl(True)

    def disableInput(self):
        self.__inputEnabled = False
        self.disableMouseControl(False, False)
        self.ignore("InputState-RMB")

    def isInputEnabled(self):
        return self.__inputEnabled

    # ------------------------------------------------------------------ #
    #  Mouse-read + avatar-facing tasks (only active during mouse-look)   #
    # ------------------------------------------------------------------ #

    def _startMouseTasks(self):
        if not self.mouseControl:
            return
        taskMgr.add(self._mouseReadTask, self.ReadMouseTaskName, priority=-29)
        taskMgr.add(self._avatarFacingTask, self.AvatarFacingTaskName, priority=23)

    def _stopMouseTasks(self):
        taskMgr.remove(self.ReadMouseTaskName)
        taskMgr.remove(self.AvatarFacingTaskName)
        props = WindowProperties()
        props.setMouseMode(props.MAbsolute)
        base.win.requestProperties(props)

    def _mouseReadTask(self, task):
        """Capture raw mouse delta and re-center the cursor."""
        if self.oobeEnabled() or not base.mouseWatcherNode.hasMouse():
            self.mouseDelta = (0, 0)
            return task.cont
        winX = base.win.getXSize()
        winY = base.win.getYSize()
        md   = base.win.getPointer(0)
        px, py = md.getX(), md.getY()
        if px > winX or py > winY:
            self.mouseDelta = (0, 0)
        else:
            self.mouseDelta = (px - self.lastMousePos[0],
                               py - self.lastMousePos[1])
            base.win.movePointer(0, winX // 2, winY // 2)
            md2 = base.win.getPointer(0)
            self.lastMousePos = (float(md2.getX()), float(md2.getY()))
        return task.cont

    def _avatarFacingTask(self, task):
        """Keep the toon facing the camera's heading while moving."""
        if self.oobeEnabled():
            return task.cont
        if self.isSubjectMoving():
            self.subject.setH(render, self._actualH)
        return task.cont

    # ------------------------------------------------------------------ #
    #  Scroll-wheel zoom                                                   #
    # ------------------------------------------------------------------ #

    def acceptWheel(self):
        self.accept('wheel_up',   self._wheelIn)
        self.accept('wheel_down', self._wheelOut)

    def ignoreWheel(self):
        self.ignore('wheel_up')
        self.ignore('wheel_down')

    def _wheelIn(self):
        self._desiredDistance = max(self._MinCamDistance,
                                    self._desiredDistance - 1.5)

    def _wheelOut(self):
        self._desiredDistance = min(self._MaxCamDistance,
                                    self._desiredDistance + 1.5)

    # ------------------------------------------------------------------ #
    #  Tab-key preset cycling                                              #
    # ------------------------------------------------------------------ #

    def acceptTab(self):
        self.accept("tab", self._cyclePreset)

    def ignoreTab(self):
        self.ignore("tab")

    def _cyclePreset(self):
        self.presetPos = (self.presetPos + 1) % len(self.presets)
        p = self.presets[self.presetPos]
        self._desiredDistance = p["dist"]
        self._desiredP        = p.get("p", -20.0)

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    def isSubjectMoving(self):
        return any(inputState.isSet(m) for m in
                   ("forward", "reverse", "turnRight", "turnLeft",
                    "slideRight", "slideLeft"))

    def isActive(self):
        return self.state == "Active"

    def oobeEnabled(self):
        return getattr(base, "oobeMode", False)

    # ------------------------------------------------------------------ #
    #  Legacy / compatibility API                                          #
    # ------------------------------------------------------------------ #

    def setPresetPos(self, idx, transition=True):
        self.presetPos        = idx % len(self.presets)
        p = self.presets[self.presetPos]
        self._desiredDistance = p["dist"]
        self._desiredP        = p.get("p", -20.0)

    def setCameraPos(self, y, h, p, transition=True):
        """Legacy method – adjusts desired orbit state directly."""
        self._desiredDistance = max(self._MinCamDistance, abs(float(y)))
        self._desiredH        = float(h) if h else self._desiredH
        self._desiredP        = max(self.MinP, min(self.MaxP, float(p)))

    def getCamOffset(self):
        return Vec3(0, -self._desiredDistance, 0)

    def setCamOffset(self, offset):
        self._desiredDistance = max(self._MinCamDistance, abs(float(offset[1])))

    def applyCamOffset(self):
        if self.isActive():
            self._applyTransform()

    @property
    def camOffset(self):
        """Property so that camOffset reads behave as expected."""
        return Vec3(0, -self._actualDistance, 0)

    @camOffset.setter
    def camOffset(self, v):
        """Allow external code / ParamObj to set camOffset by Vec3."""
        try:
            self._desiredDistance = max(self._MinCamDistance, abs(float(v[1])))
        except Exception:
            pass

    def start(self):
        if not self.isActive():
            self.request("Active")

    def stop(self):
        if self.isActive():
            self.request('Off')
