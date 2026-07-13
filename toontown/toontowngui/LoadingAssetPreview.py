"""
Live 3D / texture preview for the unified loading UI.

Uses an offscreen buffer with Camera.setScene() so preview geometry never mixes
with the main world render.
"""

import os
from typing import Optional

from direct.directnotify import DirectNotifyGlobal
from direct.showbase.ShowBaseGlobal import base
from direct.task import Task
from panda3d.core import (
    AmbientLight,
    CardMaker,
    DirectionalLight,
    NodePath,
    PerspectiveLens,
    Texture,
    TransparencyAttrib,
    VBase4,
)

notify = DirectNotifyGlobal.directNotify.newCategory('LoadingAssetPreview')

_PREVIEW_CLEAR = VBase4(0.08, 0.12, 0.19, 1.0)


class LoadingAssetPreview:
    def __init__(self):
        self._buffer = None
        self._cam_np = None
        self._world = NodePath('loadingAssetPreviewWorld')
        self._holder = self._world.attachNewNode('assetHolder')
        self._card = None
        self._border = None
        self._spin_task = None
        self._last_note_t = 0.0
        self._min_interval = 0.06

    def attach_card(self, parent: NodePath, pos, frame, sort: int = 100002):
        """
        parent: aspect2d parent
        pos: (x, y, z) in aspect2d space
        frame: (left, right, bottom, top) CardMaker frame (relative scale)
        """
        self.detach_card()
        if not base.win:
            return
        try:
            w, h = 512, 288
            self._buffer = base.win.makeTextureBuffer('loadingAssetPreview', w, h, to_ram=False, fbp=False)
            self._buffer.setClearColor(True)
            self._buffer.setClearColor(_PREVIEW_CLEAR)

            amb = AmbientLight('lap_amb')
            amb.setColor(VBase4(0.5, 0.5, 0.58, 1))
            anp = self._world.attachNewNode(amb)
            self._world.setLight(anp)
            sun = DirectionalLight('lap_sun')
            sun.setColor(VBase4(0.92, 0.9, 0.82, 1))
            snp = self._world.attachNewNode(sun)
            snp.setHpr(-68, -32, 0)
            self._world.setLight(snp)

            lens = PerspectiveLens()
            lens.setFov(40)
            lens.setNearFar(0.08, 500.0)
            self._cam_np = base.makeCamera(
                self._buffer,
                scene=self._world,
                lens=lens,
                aspectRatio=float(w) / float(h),
                clearColor=_PREVIEW_CLEAR,
                sort=-60,
            )
            self._cam_np.setPos(0, -16, 6.5)
            self._cam_np.lookAt(0, 0, 3.0)

            tex = self._buffer.getTexture()
            bl, br, bb, bt = frame
            bwide = 0.02
            bcm = CardMaker('lapBorder')
            bcm.setFrame(bl - bwide, br + bwide, bb - bwide, bt + bwide)
            self._border = parent.attachNewNode(bcm.generate())
            self._border.setColor(0.12, 0.65, 0.95, 0.55)
            self._border.setTransparency(TransparencyAttrib.M_alpha)
            self._border.setBin('fixed', sort - 1)
            self._border.setPos(*pos)

            cm = CardMaker('lapCard')
            cm.setFrame(bl, br, bb, bt)
            self._card = parent.attachNewNode(cm.generate())
            self._card.setTexture(tex)
            self._card.setTransparency(TransparencyAttrib.M_alpha)
            self._card.setBin('fixed', sort)
            self._card.setPos(*pos)
        except Exception as e:
            notify.warning('loading asset preview unavailable: %s' % e)
            self.detach_card()

    def detach_card(self):
        self._stop_spin()
        if self._card:
            try:
                self._card.removeNode()
            except Exception:
                pass
            self._card = None
        if self._border:
            try:
                self._border.removeNode()
            except Exception:
                pass
            self._border = None
        self._teardown_buffer()
        self._clear_holder()

    def _teardown_buffer(self):
        if self._buffer:
            try:
                base.graphicsEngine.removeWindow(self._buffer)
            except Exception:
                pass
            self._buffer = None
        self._cam_np = None

    def _clear_holder(self):
        self._stop_spin()
        try:
            for c in self._holder.getChildren():
                c.removeNode()
        except Exception:
            pass

    def _stop_spin(self):
        if self._spin_task:
            try:
                base.taskMgr.remove(self._spin_task)
            except Exception:
                pass
            self._spin_task = None

    def _spin(self, task):
        try:
            self._holder.setH(self._holder.getH() + 0.9)
        except Exception:
            pass
        return Task.cont

    def note_asset(
        self,
        path: Optional[str],
        model: Optional[NodePath] = None,
        texture: Optional[Texture] = None,
        force: bool = False,
    ):
        if not self._buffer or not self._card:
            return
        now = base.globalClock.getRealTime()
        if not force and (now - self._last_note_t) < self._min_interval:
            return
        self._last_note_t = now

        self._clear_holder()
        self._stop_spin()

        if model is not None and not model.isEmpty():
            try:
                inst = model.copyTo(self._holder)
                self._frame_node(inst)
                self._holder.setH(15)
                self._spin_task = base.taskMgr.add(self._spin, 'loadingAssetSpin', priority=50)
            except Exception as e:
                notify.debug('model preview failed: %s' % e)
            return

        if texture is not None:
            try:
                cm = CardMaker('texFlat')
                cm.setFrame(-6, 6, -6, 6)
                flat = self._holder.attachNewNode(cm.generate())
                flat.setTexture(texture)
                flat.setTransparency(TransparencyAttrib.M_alpha)
                flat.lookAt(0, -1, 0)
            except Exception as e:
                notify.debug('texture preview failed: %s' % e)

    def _frame_node(self, np: NodePath):
        try:
            p = NodePath('pivot')
            p.reparentTo(self._holder)
            np.wrtReparentTo(p)
            bounds = np.getBounds()
            if bounds.isEmpty():
                return
            center = bounds.getApproxCenter()
            radius = max(bounds.getRadius(), 0.01)
            np.setPos(-center)
            scale = 7.5 / max(radius, 1.0)
            s = min(max(scale, 0.35), 14.0)
            p.setScale(s)
        except Exception:
            pass

    def format_caption(self, path: Optional[str]) -> str:
        if not path:
            return ''
        try:
            base_name = os.path.basename(str(path).replace('\\', '/'))
            if len(base_name) > 42:
                return base_name[:39] + '…'
            return base_name
        except Exception:
            return str(path)[:42]

    def destroy(self):
        self.detach_card()
        try:
            self._world.removeNode()
        except Exception:
            pass
