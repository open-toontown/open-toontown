from pandac.PandaModules import *
from direct.fsm.FSM import FSM
from direct.showbase import PythonUtil
from direct.interval.MetaInterval import Sequence
from toontown.parties.PartyGlobals import DanceReverseLoopAnims, ToonDancingStates

class PartyDanceActivityToonFSM(FSM):
    notify = directNotify.newCategory('PartyDanceActivityToonFSM')

    def __init__(self, avId, activity, h):
        FSM.__init__(self, self.__class__.__name__)
        self.notify.debug('init : avId = %s, activity = %s ' % (avId, activity))
        self.avId = avId
        self.activity = activity
        self.isLocal = avId == base.localAvatar.doId
        self.toon = self.activity.getAvatar(self.avId)
        self.toonH = h
        self.danceNode = None
        self.danceMoveSequence = None
        self.lastAnim = None
        self.defaultTransitions = {'Init': ['Run', 'DanceMove', 'Cleanup'],
         'DanceMove': ['Run', 'DanceMove', 'Cleanup'],
         'Run': ['Run', 'DanceMove', 'Cleanup'],
         'Cleanup': []}
        self.enteredAlready = False
        return

    def destroy(self):
        self.toon = None
        if self.danceNode is not None:
            self.danceNode.removeNode()
            self.danceNode = None
        self.activity = None
        self.avId = None
        return

    def enterInit(self, *args):
        if not self.enteredAlready:
            self.danceNode = NodePath('danceNode-%s' % self.avId)
            self.danceNode.reparentTo(render)
            self.danceNode.setPos(0, 0, 0)
            self.danceNode.setH(self.toonH)
            pos = self.toon.getPos(self.danceNode)
            self.toon.reparentTo(self.danceNode)
            self.toon.setPos(pos)
            self.enteredAlready = True

    def exitInit(self):
        pass

    def enterCleanup(self, *args):
        if hasattr(base.cr.playGame.hood, 'loader'):
            pos = self.toon.getPos(self.activity.getParentNodePath())
            hpr = self.toon.getHpr(self.activity.getParentNodePath())
            self.toon.reparentTo(self.activity.getParentNodePath())
            self.toon.setPos(pos)
            self.toon.setHpr(hpr)
        if self.danceNode is not None:
            self.danceNode.removeNode()
            self.danceNode = None
        self.enteredAlready = False
        return

    def exitCleanup(self):
        pass

    def enterDanceMove(self, anim = ''):
        if self.lastAnim is None and anim == '':
            self.toon.loop('victory', fromFrame=98, toFrame=122)
        else:
            if anim == '':
                anim = self.lastAnim
            if anim in DanceReverseLoopAnims:
                self.danceMoveSequence = Sequence(self.toon.actorInterval(anim, loop=0), self.toon.actorInterval(anim, loop=0, playRate=-1.0))
                self.danceMoveSequence.loop()
            else:
                self.toon.loop(anim)
            self.lastAnim = anim
        return

    def exitDanceMove(self):
        if self.danceMoveSequence and self.danceMoveSequence.isPlaying():
            self.danceMoveSequence.pause()
            self.danceMoveSequence = None
        return

    def enterRun(self, *args):
        if self.toon.getCurrentAnim() != 'run':
            self.toon.loop('run')

    def exitRun(self):
        pass
