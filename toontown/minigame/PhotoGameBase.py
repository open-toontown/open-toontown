import PhotoGameGlobals
import random

class PhotoGameBase:

    def __init__(self):
        pass

    def load(self):
        self.data = PhotoGameGlobals.AREA_DATA[self.getSafezoneId()]

    def generateAssignmentTemplates(self, numAssignments):
        self.data = PhotoGameGlobals.AREA_DATA[self.getSafezoneId()]
        random.seed(self.doId)
        assignmentTemplates = []
        numPathes = len(self.data['PATHS'])
        if numPathes == 0:
            return assignmentTemplates
        while len(assignmentTemplates) < numAssignments:
            subjectIndex = random.choice(range(numPathes))
            pose = (None, None)
            while pose[0] == None:
                animSetIndex = self.data['PATHANIMREL'][subjectIndex]
                pose = random.choice(self.data['ANIMATIONS'][animSetIndex] + self.data['MOVEMODES'][animSetIndex])

            newTemplate = (subjectIndex, pose[0])
            if newTemplate not in assignmentTemplates:
                assignmentTemplates.append((subjectIndex, pose[0]))

        self.notify.debug('assignment templates')
        self.notify.debug(str(assignmentTemplates))
        for template in assignmentTemplates:
            self.notify.debug(str(template))

        return assignmentTemplates
