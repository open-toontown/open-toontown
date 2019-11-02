from direct.showbase import DirectObject

class InGameEditorElement(DirectObject.DirectObject):
    elementId = 0

    def __init__(self, children = []):
        self.elementId = InGameEditorElement.elementId
        InGameEditorElement.elementId += 1
        self.setChildren(children)
        self.feName = self.getTypeName()

    def getName(self):
        return self.feName

    def setNewName(self, newName):
        self.feName = newName

    def getTypeName(self):
        return 'Level Element'

    def id(self):
        return self.elementId

    def getChildren(self):
        return self.children

    def setChildren(self, children):
        self.children = list(children)

    def addChild(self, child):
        self.children.append(child)

    def removeChild(self, child):
        self.children.remove(child)

    def getNumChildren(self):
        return len(self.children)
