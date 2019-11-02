from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *
from toontown.battle.BattleProps import globalPropPool

class Wake(NodePath):
    wakeCount = 0

    def __init__(self, parent = hidden, target = hidden):
        NodePath.__init__(self)
        self.assign(parent.attachNewNode('wake'))
        self.target = target
        self.ripples = globalPropPool.getProp('ripples')
        tformNode = self.ripples.getChild(0)
        tformNode.setZ(0.01)
        self.seqNodePath = self.ripples.find('**/+SequenceNode')
        self.seqNode = self.seqNodePath.node()
        self.sortBase = 10
        self.rippleCount = 0
        self.doLaters = [None] * 20
        self.trackId = Wake.wakeCount
        Wake.wakeCount += 1
        return

    def createRipple(self, zPos, rate = 1.0, startFrame = 0):
        ripple = self.ripples.copyTo(self)
        ripple.iPos(self.target)
        ripple.setZ(render, zPos + self.rippleCount * 0.001)
        ripple.setBin('fixed', self.sortBase + self.rippleCount, 1)
        seqNode = ripple.find('**/+SequenceNode').node()
        seqNode.setPlayRate(rate)
        seqNode.play(startFrame, seqNode.getNumFrames() - 1)
        duration = (24 - startFrame) / 24.0

        def clearDoLaterList(rippleCount):
            self.doLaters[rippleCount] = None
            return

        def destroyRipple(task):
            ripple.removeNode()

        t = taskMgr.doMethodLater(duration, clearDoLaterList, 'wake-%d-destroy-%d' % (self.trackId, self.rippleCount), extraArgs=(self.rippleCount,), uponDeath=destroyRipple)
        self.doLaters[self.rippleCount] = t
        self.rippleCount = (self.rippleCount + 1) % 20

    def stop(self):
        for i in range(len(self.doLaters)):
            if self.doLaters[i]:
                taskMgr.remove(self.doLaters[i])
                self.doLaters[i] = None

        return

    def destroy(self):
        self.stop()
        self.removeNode()
        self.ripples.removeNode()
        del self.target


class WakeSequence(NodePath):
    wakeCount = 0

    def __init__(self, parent = hidden):
        NodePath.__init__(self)
        self.assign(globalPropPool.getProp('wake'))
        self.reparentTo(parent)
        tformNode = self.getChild(0)
        tformNode.setZ(0.1)
        self.startNodePath = self.find('**/+SequenceNode')
        self.startSeqNode = self.startNodePath.node()
        self.startSeqNode.setName('start')
        self.startSeqNode.setPlayRate(0)
        self.cycleNodePath = NodePath(SequenceNode(0, 'cycle'))
        self.cycleNodePath.reparentTo(tformNode)
        self.cycleSeqNode = self.cycleNodePath.node()
        self.endNodePath = NodePath(SequenceNode(0, 'end'))
        self.endNodePath.reparentTo(tformNode)
        self.endSeqNode = self.endNodePath.node()
        children = self.startNodePath.getChildren()
        for child in children[12:16]:
            child.reparentTo(self.cycleNodePath)

        for child in children[16:]:
            child.reparentTo(self.endNodePath)

        self.tracks = []
        self.rate = None
        self.trackId = Wake.wakeCount
        Wake.wakeCount += 1
        self.setBin('fixed', 10, 1)
        self.hide()
        return

    def createTracks(self, rate = 1):
        self.stop()
        self.tracks = []
        tflipDuration = self.startSeqNode.getNumChildren() / (float(rate) * 24)
        startTrack = Sequence(Func(self.show), Func(self.showTrack, 0), Func(self.startSeqNode.play, 0, self.startSeqNode.getNumFrames() - 1), Func(self.startSeqNode.setPlayRate, rate), Wait(tflipDuration), Func(self.showTrack, 1), Func(self.startSeqNode.play, 0, self.startSeqNode.getNumFrames() - 1), Func(self.cycleSeqNode.setPlayRate, rate), name='start-wake-track-%d' % self.trackId)
        self.tracks.append(startTrack)
        tflipDuration = self.endSeqNode.getNumChildren() / (float(rate) * 24)
        endTrack = Sequence(Func(self.showTrack, 2), Func(self.endSeqNode.play, 0, self.endSeqNode.getNumFrames() - 1), Func(self.endSeqNode.setPlayRate, rate), Wait(tflipDuration), Func(self.endSeqNode.setPlayRate, 0), Func(self.hide), name='end-wake-track-%d' % self.trackId)
        self.tracks.append(endTrack)
        self.rate = rate

    def showTrack(self, trackId):
        if trackId == 0:
            self.startNodePath.show()
        else:
            self.startNodePath.hide()
        if trackId == 1:
            self.cycleNodePath.show()
        else:
            self.cycleNodePath.hide()
        if trackId == 2:
            self.endNodePath.show()
        else:
            self.endNodePath.hide()

    def play(self, trackId, rate = 1):
        if self.rate != rate:
            self.createTracks(rate)
        self.tracks[trackId].start()

    def loop(self, trackId, rate = 1):
        if self.rate != rate:
            self.createTracks(rate)
        self.tracks[trackId].loop()

    def stop(self):
        for track in self.tracks:
            track.finish()

    def destroy(self):
        self.stop()
        self.tracks = None
        self.removeNode()
        return
