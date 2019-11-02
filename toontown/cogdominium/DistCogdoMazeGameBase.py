from direct.showbase.RandomNumGen import RandomNumGen
from toontown.cogdominium.CogdoMaze import CogdoMazeFactory
import CogdoMazeGameGlobals as Globals

class DistCogdoMazeGameBase:

    def createRandomNumGen(self):
        return RandomNumGen(self.doId)

    def createMazeFactory(self, randomNumGen):
        return CogdoMazeFactory(randomNumGen, Globals.NumQuadrants[0], Globals.NumQuadrants[1])
