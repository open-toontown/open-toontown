from toontown.hood import GenericAnimatedProp

class GenericAnimatedBuilding(GenericAnimatedProp.GenericAnimatedProp):

    def __init__(self, node):
        GenericAnimatedProp.GenericAnimatedProp.__init__(self, node)

    def enter(self):
        if base.config.GetBool('buildings-animate', False):
            GenericAnimatedProp.GenericAnimatedProp.enter(self)
