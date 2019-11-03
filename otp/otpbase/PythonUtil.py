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
        print self._creationStackTrace
    cls.__init__ = __recordCreationStack_init__
    cls.getCreationStackTrace = getCreationStackTrace
    cls.getCreationStackTraceCompactStr = getCreationStackTraceCompactStr
    cls.printCreationStackTrace = printCreationStackTrace
    return cls
