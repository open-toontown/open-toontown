from pandac.PandaModules import *
import types
import math

class PyVec3:
    Epsilon = 0.0001
    ScalarTypes = (types.FloatType, types.IntType, types.LongType)

    def __init__(self, *args):
        self.assign(*args)

    def assign(self, *args):
        if len(args) == 1:
            arg = args[0]
            if type(arg) in PyVec3.ScalarTypes:
                x = y = z = arg
            elif isinstance(arg, self.__class__):
                x = arg.x
                y = arg.y
                z = arg.z
            elif isinstance(arg, VBase3):
                x = arg.getX()
                y = arg.getY()
                z = arg.getZ()
            else:
                raise TypeError
        elif len(args) == 3:
            x = args[0]
            y = args[1]
            z = args[2]
        self.x = x
        self.y = y
        self.z = z

    def getX(self):
        return self.x

    def getY(self):
        return self.y

    def getZ(self):
        return self.z

    def setX(self, x):
        self.x = x

    def setY(self, y):
        self.y = y

    def setZ(self, z):
        self.z = z

    def set(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def fill(self, s):
        self.x = self.y = self.z = s

    def length(self):
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    def lengthSquared(self):
        return self.x * self.x + self.y * self.y + self.z * self.z

    def normalize(self):
        self /= self.length()

    def dot(self, other):
        return self.x * other.getX() + self.y * other.getY() + self.z * other.getZ()

    def _crossResults(self, other):
        return (self.y * other.getZ() - self.z * other.getY(), self.z * other.getX() - self.x * other.getZ(), self.x * other.getY() - self.y * other.getX())

    def cross(self, other):
        return PyVec3(*self._crossResults(other))

    def crossInto(self, other):
        self.x, self.y, self.z = self._crossResults(other)

    def __lt__(a, b):
        return a.length() < b.length()

    def __le__(a, b):
        return a < b or a == b

    def __eq__(a, b):
        return abs(a.length() - b.length()) < PyVec3.Epsilon

    def __ne__(a, b):
        return not a == b

    def __ge__(a, b):
        return a > b or a == b

    def __gt__(a, b):
        return a.length() > b.length()

    def __add__(a, b):
        return PyVec3(a.getX() + b.getX(), a.getY() + b.getY(), a.getZ() + b.getZ())

    def __sub__(a, b):
        return PyVec3(a.getX() - b.getX(), a.getY() - b.getY(), a.getZ() - b.getZ())

    def __mul__(a, s):
        return PyVec3(a.getX() * s, a.getY() * s, a.getZ() * s)

    def __div__(a, s):
        return PyVec3(a.getX() / s, a.getY() / s, a.getZ() / s)

    def __iadd__(self, other):
        self.x += other.getX()
        self.y += other.getY()
        self.z += other.getZ()
        return self

    def __isub__(self, other):
        self.x -= other.getX()
        self.y -= other.getY()
        self.z -= other.getZ()
        return self

    def __imul__(self, s):
        self.x *= s
        self.y *= s
        self.z *= s
        return self

    def __idiv__(self, s):
        self.x /= s
        self.y /= s
        self.z /= s
        return self

    def addX(self, s):
        self.x += s

    def addY(self, s):
        self.y += s

    def addZ(self, s):
        self.z += s

    def eq(self, other):
        return self == other

    def lessThan(self, other):
        return self < other

    def ne(self, other):
        return self != other

    def __getitem__(self, i):
        if i == 0:
            return self.x
        elif i == 1:
            return self.y
        elif i == 2:
            return self.z
        else:
            raise IndexError

    def __setitem__(self, i, s):
        if i == 0:
            self.x = s
        elif i == 1:
            self.y = s
        elif i == 2:
            self.z = s
        else:
            raise IndexError

    def __repr__(self):
        return 'PyVec3(%s,%s,%s)' % (self.x, self.y, self.z)
