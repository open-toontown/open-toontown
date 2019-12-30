from direct.directnotify import DirectNotifyGlobal
from . import AttribDesc
from direct.showbase.PythonUtil import mostDerivedLast

class EntityTypeDesc:
    notify = DirectNotifyGlobal.directNotify.newCategory('EntityTypeDesc')
    output = None

    def __init__(self):
        self.__class__.privCompileAttribDescs(self.__class__)
        self.attribNames = []
        self.attribDescDict = {}
        attribDescs = self.__class__._attribDescs
        for desc in attribDescs:
            attribName = desc.getName()
            self.attribNames.append(attribName)
            self.attribDescDict[attribName] = desc

    def isConcrete(self):
        return 'abstract' not in self.__class__.__dict__

    def isPermanent(self):
        return 'permanent' in self.__class__.__dict__

    def getOutputType(self):
        return self.output

    def getAttribNames(self):
        return self.attribNames

    def getAttribDescDict(self):
        return self.attribDescDict

    def getAttribsOfType(self, type):
        names = []
        for attribName, desc in list(self.attribDescDict.items()):
            if desc.getDatatype() == type:
                names.append(attribName)

        return names

    @staticmethod
    def privCompileAttribDescs(entTypeClass):
        if '_attribDescs' in entTypeClass.__dict__:
            return
        c = entTypeClass
        EntityTypeDesc.notify.debug('compiling attrib descriptors for %s' % c.__name__)
        for base in c.__bases__:
            EntityTypeDesc.privCompileAttribDescs(base)

        blockAttribs = c.__dict__.get('blockAttribs', [])
        baseADs = []
        bases = list(c.__bases__)
        mostDerivedLast(bases)
        for base in bases:
            for desc in base._attribDescs:
                if desc.getName() in blockAttribs:
                    continue
                for d in baseADs:
                    if desc.getName() == d.getName():
                        EntityTypeDesc.notify.warning('%s inherits attrib %s from multiple bases' % (c.__name__, desc.getName()))
                        break
                else:
                    baseADs.append(desc)

        attribDescs = []
        if 'attribs' in c.__dict__:
            for attrib in c.attribs:
                desc = AttribDesc.AttribDesc(*attrib)
                if desc.getName() == 'type' and entTypeClass.__name__ != 'Entity':
                    EntityTypeDesc.notify.error("(%s): '%s' is a reserved attribute name" % (entTypeClass.__name__, desc.getName()))
                for ad in baseADs:
                    if ad.getName() == desc.getName():
                        baseADs.remove(ad)
                        break

                attribDescs.append(desc)

        c._attribDescs = baseADs + attribDescs

    def __str__(self):
        return str(self.__class__)

    def __repr__(self):
        return str(self.__class__.__dict__.get('type', None)) + str(self.output) + str(self.attribDescDict)
