from direct.showbase.PythonUtil import *

"""
ParamObj/ParamSet
=================

These two classes support you in the definition of a formal set of
parameters for an object type. The parameters may be safely queried/set on
an object instance at any time, and the object will react to newly-set
values immediately.

ParamSet & ParamObj also provide a mechanism for atomically setting
multiple parameter values before allowing the object to react to any of the
new values--useful when two or more parameters are interdependent and there
is risk of setting an illegal combination in the process of applying a new
set of values.

To make use of these classes, derive your object from ParamObj. Then define
a 'ParamSet' subclass that derives from the parent class' 'ParamSet' class,
and define the object's parameters within its ParamSet class. (see examples
below)

The ParamObj base class provides 'get' and 'set' functions for each
parameter if they are not defined. These default implementations
respectively set the parameter value directly on the object, and expect the
value to be available in that location for retrieval.

Classes that derive from ParamObj can optionally declare a 'get' and 'set'
function for each parameter. The setter should simply store the value in a
location where the getter can find it; it should not do any further
processing based on the new parameter value. Further processing should be
implemented in an 'apply' function. The applier function is optional, and
there is no default implementation.

NOTE: the previous value of a parameter is available inside an apply
function as 'self.getPriorValue()'

The ParamSet class declaration lists the parameters and defines a default
value for each. ParamSet instances represent a complete set of parameter
values. A ParamSet instance created with no constructor arguments will
contain the default values for each parameter. The defaults may be
overriden by passing keyword arguments to the ParamSet's constructor. If a
ParamObj instance is passed to the constructor, the ParamSet will extract
the object's current parameter values.

ParamSet.applyTo(obj) sets all of its parameter values on 'obj'.
"""


class ParamObj:
    class ParamSet:
        Params = {}

        def __init__(self, *args, **kwArgs):
            self.__class__._compileDefaultParams()
            if len(args) == 1 and len(kwArgs) == 0:
                obj = args[0]
                self.paramVals = {}
                for param in self.getParams():
                    self.paramVals[param] = getSetter(obj, param, 'get')()
            else:
                assert len(args) == 0
                if __debug__:
                    for arg in list(kwArgs.keys()):
                        assert arg in self.getParams()
                self.paramVals = dict(kwArgs)

        def getValue(self, param):
            if param in self.paramVals:
                return self.paramVals[param]
            return self._Params[param]

        def applyTo(self, obj):
            obj.lockParams()
            for param in self.getParams():
                getSetter(obj, param)(self.getValue(param))
            obj.unlockParams()

        def extractFrom(self, obj):
            obj.lockParams()
            for param in self.getParams():
                self.paramVals[param] = getSetter(obj, param, 'get')()
            obj.unlockParams()

        @classmethod
        def getParams(cls):
            cls._compileDefaultParams()
            return list(cls._Params.keys())

        @classmethod
        def getDefaultValue(cls, param):
            cls._compileDefaultParams()
            dv = cls._Params[param]
            if hasattr(dv, '__call__'):
                dv = dv()
            return dv

        @classmethod
        def _compileDefaultParams(cls):
            if '_Params' in cls.__dict__:
                return
            bases = list(cls.__bases__)
            if object in bases:
                bases.remove(object)
            mostDerivedLast(bases)
            cls._Params = {}
            for c in (bases + [cls]):
                c._compileDefaultParams()
                if 'Params' in c.__dict__:
                    cls._Params.update(c.Params)
            del bases

        def __repr__(self):
            argStr = ''
            for param in self.getParams():
                argStr += '%s=%s,' % (param, repr(self.getValue(param)))
            return '%s.%s(%s)' % (self.__class__.__module__, self.__class__.__name__, argStr)

    def __init__(self, *args, **kwArgs):
        assert issubclass(self.ParamSet, ParamObj.ParamSet)
        params = None
        if len(args) == 1 and len(kwArgs) == 0:
            params = args[0]
        elif len(kwArgs) > 0:
            assert len(args) == 0
            params = self.ParamSet(**kwArgs)

        self._paramLockRefCount = 0
        self._curParamStack = []
        self._priorValuesStack = []

        for param in self.ParamSet.getParams():
            setattr(self, param, self.ParamSet.getDefaultValue(param))

            setterName = getSetterName(param)
            getterName = getSetterName(param, 'get')

            if not hasattr(self, setterName):
                def defaultSetter(self, value, param=param):
                    setattr(self, param, value)

                self.__class__.__dict__[setterName] = defaultSetter

            if not hasattr(self, getterName):
                def defaultGetter(self, param=param, default=self.ParamSet.getDefaultValue(param)):
                    return getattr(self, param, default)

                self.__class__.__dict__[getterName] = defaultGetter

            origSetterName = '%s_ORIG' % (setterName,)
            if not hasattr(self, origSetterName):
                origSetterFunc = getattr(self.__class__, setterName)
                setattr(self.__class__, origSetterName, origSetterFunc)

                def setterStub(self, value, param=param, origSetterName=origSetterName):
                    if self._paramLockRefCount > 0:
                        priorValues = self._priorValuesStack[-1]
                        if param not in priorValues:
                            try:
                                priorValue = getSetter(self, param, 'get')()
                            except:
                                priorValue = None
                            priorValues[param] = priorValue
                        self._paramsSet[param] = None
                        getattr(self, origSetterName)(value)
                    else:
                        try:
                            priorValue = getSetter(self, param, 'get')()
                        except:
                            priorValue = None
                        self._priorValuesStack.append({param: priorValue})
                        getattr(self, origSetterName)(value)
                        applier = getattr(self, getSetterName(param, 'apply'), None)
                        if applier is not None:
                            self._curParamStack.append(param)
                            applier()
                            self._curParamStack.pop()
                        self._priorValuesStack.pop()
                        if hasattr(self, 'handleParamChange'):
                            self.handleParamChange((param,))

                setattr(self.__class__, setterName, setterStub)

        if params is not None:
            params.applyTo(self)

    def destroy(self):
        pass

    def setDefaultParams(self):
        self.ParamSet().applyTo(self)

    def getCurrentParams(self):
        params = self.ParamSet()
        params.extractFrom(self)
        return params

    def lockParams(self):
        self._paramLockRefCount += 1
        if self._paramLockRefCount == 1:
            self._handleLockParams()

    def unlockParams(self):
        if self._paramLockRefCount > 0:
            self._paramLockRefCount -= 1
            if self._paramLockRefCount == 0:
                self._handleUnlockParams()

    def _handleLockParams(self):
        self._paramsSet = {}
        self._priorValuesStack.append({})

    def _handleUnlockParams(self):
        for param in self._paramsSet:
            applier = getattr(self, getSetterName(param, 'apply'), None)
            if applier is not None:
                self._curParamStack.append(param)
                applier()
                self._curParamStack.pop()
        self._priorValuesStack.pop()
        if hasattr(self, 'handleParamChange'):
            self.handleParamChange(tuple(self._paramsSet.keys()))
        del self._paramsSet

    def paramsLocked(self):
        return self._paramLockRefCount > 0

    def getPriorValue(self):
        return self._priorValuesStack[-1][self._curParamStack[-1]]

    def __repr__(self):
        argStr = ''
        for param in self.ParamSet.getParams():
            try:
                value = getSetter(self, param, 'get')()
            except:
                value = '<unknown>'
            argStr += '%s=%s,' % (param, repr(value))
        return '%s(%s)' % (self.__class__.__name__, argStr)
