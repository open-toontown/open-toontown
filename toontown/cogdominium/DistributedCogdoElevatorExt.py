from toontown.building.DistributedElevatorExt import DistributedElevatorExt

class DistributedCogdoElevatorExt(DistributedElevatorExt):

    def setupElevator(self):
        DistributedElevatorExt.setupElevator(self)
        self.elevatorSphereNodePath.setY(-1.0)
        self.elevatorSphereNodePath.setZ(1.5)

    def getElevatorModel(self):
        return self.bldg.getCogdoElevatorNodePath()

    def getBldgDoorOrigin(self):
        return self.bldg.getCogdoDoorOrigin()

    def _getDoorsClosedInfo(self):
        return ('cogdoInterior', 'cogdoInterior')
