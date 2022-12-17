from toontown.toonbase import TTLocalizer
from direct.distributed.ClockDelta import *
from direct.directnotify import DirectNotifyGlobal
from . import DistributedNPCToonBaseAI
from direct.task import Task
import random

class NPCDialogue:
    """
    The NPC dialogue for a given topic and set of participants
    """

    notify = DirectNotifyGlobal.directNotify.newCategory("NPCDialogue")

    def __init__(self, participant, dialogueTopic):
        self.participants = {}        
        
        if dialogueTopic in TTLocalizer.toontownDialogues:
            self.topic = dialogueTopic
        else:
            self.notify.warning("Dialogue does not exist: %s" %dialogueTopic)
            self.topic = TTLocalizer.BoringTopic
        
        self.conversation = TTLocalizer.toontownDialogues[self.topic]
        
        if participant and isinstance(participant, DistributedNPCToonBaseAI.DistributedNPCToonBaseAI):
            self.addParticipant(participant)
            self.participantProgress = 0
            self.currentParticipant = participant.npcId
        else:
            self.notify.warning("Participant does not exist: %s" %participant)
            self.participantProgress = 0
            self.currrentParticipant = None
    
    def calcMaxNumMsgs(self):
        """
        Find the participant that has the most number of things to say
        """
        self.maxNumMsgs = 0
        for participant, spiel in self.conversation.items():
            if len(spiel)>self.maxNumMsgs and participant[1] in self.participants:
                self.maxNumMsgs = len(spiel)
    
    def getTopic(self):
        """
        Accessor function for topic
        """
        return self.topic
            
    def addParticipant(self, participant):
        """
        Add a new participant
        """
        if self.getNumParticipants() > self.getMaxParticipants():
            return False
        if participant:
            for partPos in self.conversation.keys():
                if partPos[1] == participant.npcId:
                    if not (participant.npcId in self.participants):
                        self.participants[participant.npcId] = [participant]
                    else:
                        if participant not in self.participants[participant.npcId]:
                            self.participants[participant.npcId].append(participant)
                        else:
                            self.notify.warning("Participant: %s already in the conversation" %participant)
                    self.calcMaxNumMsgs()
                    return True
            self.notify.warning("Participant: %s should not be in conversation" %participant)
        return False
                
    def removeParticipant(self, participant):
        """
        Remove a participant
        """
        if participant.npcId in self.participants:
            if participant.npcId == self.currentParticipant:
                self.getNextParticipant()                
            self.participants[participant.npcId].remove(participant)
            if self.participants[participant.npcId] == []:
                del self.participants[participant.npcId]
            self.calcMaxNumMsgs()
            return True
        return False            
        
    def getNextParticipant(self):
        while 1:
            self.currentParticipant = self.calcNextParticipant()
            if self.currentParticipant in self.participants:
                break
    
    def calcNextParticipant(self):
        """
        Returns the next in line to talk
        """
        nextParticipant = None
        
        for partPos in self.conversation.keys():
            if partPos[1] == self.currentParticipant:
                nextPos = partPos[0]+1
                break
        if nextPos>len(self.conversation):
            nextPos = 1
            self.participantProgress = (self.participantProgress+1)%self.maxNumMsgs
        for partPos in self.conversation.keys():
            if partPos[0] == nextPos:
                nextParticipant = partPos[1]
                return nextParticipant
            
        return self.currentParticipant
        
        
    def getMaxParticipants(self):
        """
        Number of conversation pieces provided in TTLocalizer
        """
        return len(self.conversation)
        
    def getNumParticipants(self):
        """
        Returns the number of NPC's currently participating
        """
        return len(self.participants)
        
    def isRunning(self):
        if taskMgr.hasTaskNamed("Dialogue"+self.topic):
            return True

    def start(self):
        """
        Start up a dialogue amongst the participants
        """
        self.nextChatTime = 0
        
        taskMgr.add(self.__blather, "Dialogue"+self.topic)
        
        return True
        
    def stop(self):
        """
        This conversation is over!
        """
        taskMgr.remove("Dialogue"+self.topic)

    def __blather(self, task):
        """
        Speak in turn
        """
        now = globalClock.getFrameTime()
        if now < self.nextChatTime:
            return Task.cont

        if not self.currentParticipant:
            return Task.done
            
        # Increment the participantProgress
        for partPos in self.conversation.keys():
            if partPos[1] == self.currentParticipant:
                convKey = partPos
                break
        if self.participantProgress >= len(self.conversation[convKey]):
            self.getNextParticipant()
            return Task.cont
                    
        # Select the current spiel      
        #msg = self.conversation[self.participants[self.currentParticipant]][self.participantProgress]
        
        for participant in self.participants[self.currentParticipant]:
            chatFlags = CFSpeech | CFTimeout
            
            participant.sendUpdate("setChat", [self.topic, convKey[0], convKey[1], self.participantProgress, chatFlags])
            
        self.getNextParticipant()

        # Delay before next message
        self.nextChatTime = now + 5.0

        return Task.cont