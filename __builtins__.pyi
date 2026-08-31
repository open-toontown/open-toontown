# NOTE: if you modify this file, run `> Python: Restart Language Server` (VSCode)
# to manually force the typing server to update
from direct.showbase import DConfig
from direct.showbase.Loader import Loader
from panda3d.core import NodePath

from .otp.ai.AIBase import AIBase
from .toontown.toon.LocalToon import LocalToon
from .toontown.toonbase.ToonBase import ToonBase
from .toontown.toonbase.ToontownStart import game as toontownGame

# otp/ai/AIBase.py
__dev__: bool
__astron__: bool
__execWarnings__: bool
hidden: NodePath
wantTestObject: bool

# otp/ai/AIBaseGlobal.py
simbase: AIBase
config: DConfig  # type: ignore
loader: Loader

# otp/otpbase/PythonUtil.py
def isClient() -> bool: ...
def lerp(v0: float, v1: float, t: float) -> float: ...
def triglerp(v0: float, v1: float, t: float) -> float: ...

# toontown/distributed/ToontownClientRepository.py
localAvatar: LocalToon

# toontown/toonbase/ToontownStart.py
game: toontownGame

# direct/showbase/ShowBase.py
base: ToonBase
