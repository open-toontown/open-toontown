# NOTE: if you modify this file, run `> Python: Restart Language Server` (VSCode)
# to manually force the typing server to update
from direct.showbase import DConfig
from panda3d.core import NodePath
from typing import Any

from .otp.ai.AIBase import AIBase, Loader
from .toontown.launcher.ToontownDummyLauncher import ToontownDummyLauncher
from .toontown.toon.LocalToon import LocalToon
from .toontown.toonbase.ToonBase import ToonBase
from .toontown.toonbase.ToontownStart import game as toontownGame

# otp/ai/AIBase.py
__dev__: bool
__astron__: bool
__execWarnings__: bool
ostream: Any
globalClock: Any
vfs: Any | None
hidden: NodePath
wantTestObject: bool

# otp/ai/AIBaseGlobal.py
simbase: AIBase
run: Any
taskMgr: Any
jobMgr: Any
eventMgr: Any
messenger: Any
bboard: Any
config: DConfig  # type: ignore
directNotify: Any
loader: Loader.Loader

def inspect(anObject) -> None: ...

# otp/otpbase/PythonUtil.py
def pdir() -> None: ...
def isClient() -> bool: ...
def lerp(v0: float, v1: float, t: float) -> float: ...
def triglerp(v0: float, v1: float, t: float) -> float: ...
def choice(condition: bool, ifTrue: Any, ifFalse: Any) -> Any: ...
def cmp(a: Any, b: Any) -> Any: ...

# toontown/distributed/ToontownClientRepository.py
localAvatar: LocalToon

# toontown/toonbase/ToontownStart.py
game: toontownGame
launcher: ToontownDummyLauncher

# direct/showbase/ShowBase.py
base: ToonBase
