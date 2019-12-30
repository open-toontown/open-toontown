from . import AnimatedProp
from direct.actor import Actor
from direct.interval.IntervalGlobal import *

class PetShopFishAnimatedProp(AnimatedProp.AnimatedProp):

    def __init__(self, node):
        AnimatedProp.AnimatedProp.__init__(self, node)
        parent = node.getParent()
        self.fish = Actor.Actor(node, copy=0)
        self.fish.reparentTo(parent)
        self.fish.loadAnims({'swim': 'phase_4/models/props/exteriorfish-swim'})
        self.fish.pose('swim', 0)
        self.node = self.fish

    def delete(self):
        AnimatedProp.AnimatedProp.delete(self)
        self.fish.cleanup()
        del self.fish
        del self.node

    def enter(self):
        AnimatedProp.AnimatedProp.enter(self)
        self.fish.loop('swim')

    def exit(self):
        AnimatedProp.AnimatedProp.exit(self)
        self.fish.stop()
