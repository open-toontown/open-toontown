import math
import time

from panda3d.core import CardMaker, NodePath, TextNode, Vec4, ConfigVariableBool
from direct.gui.DirectGui import DirectFrame, DirectLabel, DirectWaitBar, DGG
from direct.interval.IntervalGlobal import (
    Sequence,
    Parallel,
    LerpColorScaleInterval,
    LerpScaleInterval,
    LerpFunc,
    Wait,
    Func,
)

from toontown.toontowngui.LoadingAssetPreview import LoadingAssetPreview


class ModernLoadingScreen:
    """
    Unified launcher / zone-load overlay:
    - Full-screen polished startup view (logo, gradient, progress, live asset preview)
    - Compact bottom bar after login (game stays visible; preview + status during loads)
    """

    def __init__(self, parent=None):
        self._enabled = ConfigVariableBool('want-modern-launcher-ui', True).value
        self._want_preview = ConfigVariableBool('want-loading-asset-preview', True).value
        self._start_t = time.time()
        self._pulse_ival = None
        self._outro_ival = None
        self._launcher_done = False
        self._bulk_active = False
        self._preview = LoadingAssetPreview() if self._enabled else None

        if not self._enabled:
            self.root = None
            self.compact_root = None
            return

        if parent is None:
            parent = aspect2d

        # Full-screen launcher panel
        self.root = DirectFrame(
            parent=parent,
            relief=None,
            frameColor=(0, 0, 0, 0),
            sortOrder=100000,
        )

        self._bg = self._make_gradient_bg(self.root)

        self.logoModel = None
        self.logo = None
        try:
            self.logoModel = loader.loadModel('phase_3/models/gui/tt_m_gui_ups_logo_noText')
            if not self.logoModel or self.logoModel.isEmpty():
                raise Exception('logo model empty')
            self.logo = DirectFrame(
                parent=self.root,
                relief=None,
                image=self.logoModel,
                image_scale=0.45,
                pos=(0, 0, 0.58),
            )
        except Exception:
            self.logoModel = None
            self.logo = DirectLabel(
                parent=self.root,
                relief=None,
                text='Toontown',
                text_align=TextNode.ACenter,
                text_scale=0.12,
                text_fg=(1, 1, 1, 1),
                pos=(0, 0, 0.62),
            )

        self.subtitle = DirectLabel(
            parent=self.root,
            relief=None,
            text='Launching…',
            text_align=TextNode.ACenter,
            text_scale=0.06,
            text_fg=(1, 1, 1, 0.85),
            pos=(0, 0, 0.50),
        )

        self.status = DirectLabel(
            parent=self.root,
            relief=None,
            text='Initializing…',
            text_align=TextNode.ACenter,
            text_scale=0.052,
            text_fg=(1, 1, 1, 0.9),
            pos=(0, 0, -0.05),
        )

        self.asset_caption = DirectLabel(
            parent=self.root,
            relief=None,
            text='',
            text_align=TextNode.ACenter,
            text_scale=0.034,
            text_fg=(0.75, 0.9, 1.0, 0.85),
            pos=(0, 0, -0.2),
        )

        self.progress = DirectWaitBar(
            parent=self.root,
            relief=None,
            range=100,
            value=0,
            pos=(0, 0, -0.16),
            frameSize=(-0.75, 0.75, -0.055, 0.055),
            frameColor=(1, 1, 1, 0.12),
            barColor=(0.2, 0.8, 1.0, 0.85),
            borderWidth=(0.02, 0.02),
        )

        self._detail = DirectLabel(
            parent=self.root,
            relief=None,
            text='',
            text_align=TextNode.ACenter,
            text_scale=0.028,
            text_fg=(0.55, 0.7, 0.85, 0.75),
            pos=(0, 0, -0.28),
        )

        if self._want_preview and self._preview:
            try:
                self._preview.attach_card(self.root, (0.68, 0, 0.02), (-0.38, 0.38, -0.22, 0.22))
            except Exception:
                pass

        self._start_pulse()

        # Compact in-world load bar (bottom)
        self.compact_root = DirectFrame(
            parent=hidden,
            relief=DGG.FLAT,
            frameColor=(0.03, 0.07, 0.12, 0.78),
            frameSize=(-1.4, 1.4, -0.12, 0.1),
            pos=(0, 0, -0.88),
            sortOrder=100015,
            borderWidth=(0.008, 0.008),
        )
        self.compact_status = DirectLabel(
            parent=self.compact_root,
            relief=None,
            text='',
            text_align=TextNode.ALeft,
            text_scale=0.04,
            text_fg=(1, 1, 1, 0.95),
            pos=(-1.32, 0, 0.035),
        )
        self.compact_asset = DirectLabel(
            parent=self.compact_root,
            relief=None,
            text='',
            text_align=TextNode.ALeft,
            text_scale=0.032,
            text_fg=(0.65, 0.85, 1.0, 0.9),
            pos=(-1.32, 0, -0.025),
        )
        self.compact_progress = DirectWaitBar(
            parent=self.compact_root,
            relief=None,
            range=100,
            value=0,
            pos=(0.15, 0, -0.055),
            frameSize=(-0.55, 0.55, -0.028, 0.028),
            frameColor=(1, 1, 1, 0.14),
            barColor=(0.25, 0.85, 1.0, 0.9),
            borderWidth=(0.015, 0.015),
        )

        self._layout_compact_bar()

    def _layout_compact_bar(self):
        try:
            left = float(base.a2dLeft) + 0.04
            right = float(base.a2dRight) - 0.04
            self.compact_root['frameSize'] = (left, right, -0.13, 0.1)
            self.compact_status.setPos(left + 0.02, 0, 0.04)
            self.compact_asset.setPos(left + 0.02, 0, -0.03)
            self.compact_progress.setPos((left + right) * 0.5 + 0.1, 0, -0.055)
        except Exception:
            pass

    def enabled(self):
        return bool(self._enabled and self.root)

    def _make_gradient_bg(self, parent) -> NodePath:
        cm = CardMaker('modernLoadingBG')
        cm.setFrameFullscreenQuad()
        card = NodePath(cm.generate())
        card.reparentTo(parent)
        card.setBin('fixed', -100)
        card.setDepthTest(False)
        card.setDepthWrite(False)
        card.setColorScale(Vec4(0.06, 0.10, 0.16, 1.0))
        return card

    def _start_pulse(self):
        if not self.root:
            return

        def pulse(t):
            s = 0.5 + 0.5 * math.sin(t * 2 * math.pi)
            r = 0.06 + s * 0.02
            g = 0.10 + s * 0.03
            b = 0.16 + s * 0.05
            try:
                self._bg.setColorScale(Vec4(r, g, b, 1.0))
            except Exception:
                pass

        self._pulse_ival = Sequence(
            LerpFunc(pulse, fromData=0.0, toData=1.0, duration=1.6, blendType='easeInOut'),
            LerpFunc(pulse, fromData=1.0, toData=2.0, duration=1.6, blendType='easeInOut'),
        )
        self._pulse_ival.loop()

    def set_title(self, title: str, subtitle=None):
        if not self.root:
            return
        if subtitle is not None:
            self.subtitle['text'] = subtitle

    def set_status(self, text: str):
        if self.root:
            self.status['text'] = text
        if self._launcher_done and self.compact_root:
            self.compact_status['text'] = text

    def set_detail(self, text: str):
        if not self.root:
            return
        self._detail['text'] = text or ''

    def set_progress(self, pct_0_to_100: float):
        try:
            v = max(0.0, min(100.0, float(pct_0_to_100)))
        except Exception:
            v = 0.0
        if self.root:
            self.progress['value'] = v
        if self.compact_root:
            self.compact_progress['value'] = v

    def on_asset_loaded(self, path=None, model=None, texture=None, kind='model'):
        if ConfigVariableBool('want-zero-load-ui', False).value and self._launcher_done:
            return
        preview = self._preview if self._want_preview else None
        if kind == 'audio':
            if preview and path:
                cap = 'SFX: ' + preview.format_caption(path)
            else:
                cap = path or ''
            if self.root and not self._launcher_done:
                self.asset_caption['text'] = cap
            if self._launcher_done and self.compact_root:
                self.compact_asset['text'] = cap
            return
        if kind == 'font':
            if preview and path:
                cap = 'Font: ' + preview.format_caption(path)
            else:
                cap = path or ''
            if self.root and not self._launcher_done:
                self.asset_caption['text'] = cap
            if self._launcher_done and self.compact_root:
                self.compact_asset['text'] = cap
            return
        if not preview:
            return
        cap = preview.format_caption(path)
        if self.root and not self._launcher_done:
            self.asset_caption['text'] = cap
            if path:
                short = path.replace('\\', '/')
                if len(short) > 56:
                    short = short[:53] + '…'
                self.set_detail(short)
        if self._launcher_done and self.compact_root:
            self.compact_asset['text'] = cap
        try:
            preview.note_asset(path, model=model, texture=texture)
        except Exception:
            pass

    def enter_bulk_load(self, block_name: str, label: str, expected_steps: int):
        if not self._enabled:
            return
        self._bulk_active = True
        if hasattr(base, 'cr') and base.cr and (getattr(base.cr, 'playGame', None) or getattr(base, 'localAvatar', None)):
            self._launcher_done = True
        if ConfigVariableBool('want-zero-load-ui', False).value:
            return
        self._layout_compact_bar()
        if self._launcher_done:
            if self.root:
                try:
                    self.root.reparentTo(hidden)
                except Exception:
                    pass
            try:
                self.compact_root.reparentTo(aspect2d, DGG.NO_FADE_SORT_INDEX)
            except Exception:
                pass
            self.compact_status['text'] = label
            self.compact_asset['text'] = ''
            self.compact_progress['value'] = 0
            if self._want_preview and self._preview:
                self._preview.detach_card()
                self._preview.attach_card(self.compact_root, (1.15, 0, 0.02), (-0.2, 0.2, -0.1, 0.1))
        else:
            self.set_status(label)

    def leave_bulk_load(self):
        self._bulk_active = False
        if hasattr(base, 'cr') and base.cr and (getattr(base.cr, 'playGame', None) or getattr(base, 'localAvatar', None)):
            self._launcher_done = True
        if ConfigVariableBool('want-zero-load-ui', False).value:
            if self._preview:
                try:
                    self._preview.detach_card()
                except Exception:
                    pass
            return
        if self.compact_root:
            try:
                self.compact_root.reparentTo(hidden)
            except Exception:
                pass
        if self.root and self._launcher_done:
            try:
                self.root.reparentTo(hidden)
            except Exception:
                pass
        if self._preview:
            self._preview.detach_card()
            if self.root and not self._launcher_done and self._want_preview:
                self._preview.attach_card(self.root, (0.68, 0, 0.02), (-0.38, 0.38, -0.22, 0.22))

    def transition_out(self, done_cb=None):
        if not self.root:
            if callable(done_cb):
                done_cb()
            return

        if self._outro_ival:
            return

        def _finish():
            try:
                if self._pulse_ival:
                    self._pulse_ival.finish()
                    self._pulse_ival = None
            except Exception:
                pass
            try:
                self.root.reparentTo(hidden)
            except Exception:
                pass
            if self._preview:
                self._preview.detach_card()
            self._launcher_done = True
            if callable(done_cb):
                done_cb()

        self._outro_ival = Sequence(
            Parallel(
                LerpColorScaleInterval(self.root, 0.45, Vec4(1, 1, 1, 0.0), blendType='easeInOut'),
                LerpScaleInterval(self.root, 0.45, 1.06, blendType='easeInOut'),
            ),
            Wait(0.02),
            Func(_finish),
        )
        self._outro_ival.start()

    def destroy(self):
        if self._pulse_ival:
            try:
                self._pulse_ival.finish()
            except Exception:
                pass
            self._pulse_ival = None

        if self._outro_ival:
            try:
                self._outro_ival.finish()
            except Exception:
                pass
            self._outro_ival = None

        if self._preview:
            self._preview.destroy()
            self._preview = None

        if self.compact_root:
            try:
                self.compact_root.destroy()
            except Exception:
                try:
                    self.compact_root.removeNode()
                except Exception:
                    pass
            self.compact_root = None

        if self.root:
            try:
                self.root.destroy()
            except Exception:
                try:
                    self.root.removeNode()
                except Exception:
                    pass
            self.root = None

        if self.logoModel:
            try:
                self.logoModel.removeNode()
            except Exception:
                pass
            self.logoModel = None
