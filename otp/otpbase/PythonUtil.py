import builtins
import sys
import math
import random
import time

__all__ = ['enumerate', 'nonRepeatingRandomList', 'describeException', 'pdir', 'choice', 'cmp', 'lerp', 'triglerp']

if not hasattr(builtins, 'enumerate'):
    def enumerate(L):
        """Returns (0, L[0]), (1, L[1]), etc., allowing this syntax:
        for i, item in enumerate(L):
           ...

        enumerate is a built-in feature in Python 2.3, which implements it
        using an iterator. For now, we can use this quick & dirty
        implementation that returns a list of tuples that is completely
        constructed every time enumerate() is called.
        """
        return list(zip(list(range(len(L))), L))

    builtins.enumerate = enumerate
else:
    enumerate = builtins.enumerate

def nonRepeatingRandomList(vals, max):
    random.seed(time.time())
    #first generate a set of random values
    valueList=list(range(max))
    finalVals=[]
    for i in range(vals):
        index=int(random.random()*len(valueList))
        finalVals.append(valueList[index])
        valueList.remove(valueList[index])
    return finalVals

# class 'decorator' that records the stack at the time of creation
# be careful with this, it creates a StackTrace, and that can take a
# lot of CPU
def recordCreationStack(cls):
    if not hasattr(cls, '__init__'):
        raise 'recordCreationStack: class \'%s\' must define __init__' % cls.__name__
    cls.__moved_init__ = cls.__init__
    def __recordCreationStack_init__(self, *args, **kArgs):
        self._creationStackTrace = StackTrace(start=1)
        return self.__moved_init__(*args, **kArgs)
    def getCreationStackTrace(self):
        return self._creationStackTrace
    def getCreationStackTraceCompactStr(self):
        return self._creationStackTrace.compact()
    def printCreationStackTrace(self):
        print(self._creationStackTrace)
    cls.__init__ = __recordCreationStack_init__
    cls.getCreationStackTrace = getCreationStackTrace
    cls.getCreationStackTraceCompactStr = getCreationStackTraceCompactStr
    cls.printCreationStackTrace = printCreationStackTrace
    return cls

# __dev__ is not defined at import time, call this after it's defined
def recordFunctorCreationStacks():
    global Functor
    from pandac.PandaModules import getConfigShowbase
    config = getConfigShowbase()
    # off by default, very slow
    if __dev__ and config.GetBool('record-functor-creation-stacks', 0):
        if not hasattr(Functor, '_functorCreationStacksRecorded'):
            Functor = recordCreationStackStr(Functor)
            Functor._functorCreationStacksRecorded = True
            Functor.__call__ = Functor._exceptionLoggedCreationStack__call__

def describeException(backTrace = 4):
    # When called in an exception handler, returns a string describing
    # the current exception.

    def byteOffsetToLineno(code, byte):
        # Returns the source line number corresponding to the given byte
        # offset into the indicated Python code module.

        import array
        lnotab = array.array('B', code.co_lnotab)

        line   = code.co_firstlineno
        for i in range(0, len(lnotab), 2):
            byte -= lnotab[i]
            if byte <= 0:
                return line
            line += lnotab[i+1]

        return line

    infoArr = sys.exc_info()
    exception = infoArr[0]
    exceptionName = getattr(exception, '__name__', None)
    extraInfo = infoArr[1]
    trace = infoArr[2]

    stack = []
    while trace.tb_next:
        # We need to call byteOffsetToLineno to determine the true
        # line number at which the exception occurred, even though we
        # have both trace.tb_lineno and frame.f_lineno, which return
        # the correct line number only in non-optimized mode.
        frame = trace.tb_frame
        module = frame.f_globals.get('__name__', None)
        lineno = byteOffsetToLineno(frame.f_code, frame.f_lasti)
        stack.append("%s:%s, " % (module, lineno))
        trace = trace.tb_next

    frame = trace.tb_frame
    module = frame.f_globals.get('__name__', None)
    lineno = byteOffsetToLineno(frame.f_code, frame.f_lasti)
    stack.append("%s:%s, " % (module, lineno))

    description = ""
    for i in range(len(stack) - 1, max(len(stack) - backTrace, 0) - 1, -1):
        description += stack[i]

    description += "%s: %s" % (exceptionName, extraInfo)
    return description

def pdir(obj, str = None, width = None,
            fTruncate = 1, lineWidth = 75, wantPrivate = 0):
    # Remove redundant class entries
    uniqueLineage = []
    for l in getClassLineage(obj):
        if type(l) == type:
            if l in uniqueLineage:
                break
        uniqueLineage.append(l)
    # Pretty print out directory info
    uniqueLineage.reverse()
    for obj in uniqueLineage:
        _pdir(obj, str, width, fTruncate, lineWidth, wantPrivate)
        print()

def lerp(v0, v1, t):
    """
    returns a value lerped between v0 and v1, according to t
    t == 0 maps to v0, t == 1 maps to v1
    """
    return v0 + ((v1 - v0) * t)

def triglerp(v0, v1, t):
    """
    lerp using the curve of sin(-pi/2) -> sin(pi/2)
    """
    x = lerp(-math.pi/2, math.pi/2, t)
    v = math.sin(x)
    return lerp(v0, v1, (v + 1.) / 2.)

def choice(condition, ifTrue, ifFalse):
    # equivalent of C++ (condition ? ifTrue : ifFalse)
    if condition:
        return ifTrue
    else:
        return ifFalse

def quantize(value, divisor):
    # returns new value that is multiple of (1. / divisor)
    return float(int(value * int(divisor))) / int(divisor)

def quantizeVec(vec, divisor):
    # in-place
    vec[0] = quantize(vec[0], divisor)
    vec[1] = quantize(vec[1], divisor)
    vec[2] = quantize(vec[2], divisor)

def isClient():
    if hasattr(builtins, 'simbase') and not hasattr(builtins, 'base'):
        return False
    return True

def cmp(a, b):
    return (a > b) - (a < b)


builtins.pdir = pdir
builtins.isClient = isClient
builtins.lerp = lerp
builtins.triglerp = triglerp
builtins.choice = choice
builtins.cmp = cmp
