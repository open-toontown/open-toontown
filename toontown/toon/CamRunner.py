from direct.showbase.DirectObject import DirectObject
from direct.showbase.InputStateGlobal import inputState


class CamRunner(DirectObject):
    def __init__(self):
        self.orbitMode = False
        self.toonWasWalking = False
        self.usingOrbitalRun = False
        self.acceptingMovement = True
        self.forwardInput = None
        self._lmbToken = None

    def startInput(self):
        self.forwardInput = base.controls.MOVE_UP
        self.orbitMode = True

        self._lmbToken = inputState.watchWithModifiers('LMB', 'mouse1')
        self.accept('mouse1', self.startOrbitalMovement)
        self.accept('mouse1-up', self.stopOrbitalMovement)

    def stopInput(self):
        self.stopOrbitalMovement()
        self.ignore('mouse1')
        self.ignore('mouse1-up')
        self.orbitMode = False

        self.toonWasWalking = False
        self.acceptingMovement = True
        if self._lmbToken is not None:
            self._lmbToken.release()
            self._lmbToken = None

    def startOrbitalMovement(self):
        self.usingOrbitalRun = True
        self.toonWasWalking = base.walking
        messenger.send(self.forwardInput)
        self.accept(f'{self.forwardInput}-up', self.triggerToonWalk, extraArgs=[False])
        self.accept(self.forwardInput, self.triggerToonWalk, extraArgs=[True])

    def stopOrbitalMovement(self):
        if not self.usingOrbitalRun:
            return
        self.usingOrbitalRun = False
        self.triggerToonWalk(False)
        self.ignore(f'{self.forwardInput}-up')
        self.ignore(self.forwardInput)
        if not self.toonWasWalking:
            messenger.send(f'{self.forwardInput}-up')
        self.toonWasWalking = None
        self.acceptingMovement = True

    def triggerToonWalk(self, walking):
        if self.acceptingMovement:
            self.toonWasWalking = walking

        self.acceptingMovement = walking
        if not walking:
            messenger.send(self.forwardInput)
