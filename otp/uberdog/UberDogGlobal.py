"""instantiate global ShowBase object"""

from otp.ai.AIBase import *

# We're going to end up importing this accidentally anyway, so we
# might as well import it explicitly, and share the same AIBase
# object.
from otp.ai.AIBaseGlobal import *

__builtins__["uber"] = simbase
