from toontown.toonbase import TTLocalizer
from direct.directnotify import DirectNotifyGlobal
from . import NPCDialogue

class NPCDialogueManagerAI:
    """
    Create and distroy dialogues here.    
    """

    notify = DirectNotifyGlobal.directNotify.newCategory("NPCDialogueManagerAI")

    def __init__(self):
        self.dialogues = []
        
    def createNewDialogue(self, participant, dialogueTopic):
        """
        Create a new dialogue
        """
        dialogue = NPCDialogue.NPCDialogue(participant, dialogueTopic)
        result = dialogue.start()
        if result:
            self.dialogues.append(dialogue)
        return result
        
    def requestDialogue(self, participant, dialogueTopic):
        """
        Request to be added to the dialogue: dialogueTopic
        """
        for dialogue in self.dialogues:
            if dialogue.getTopic() == dialogueTopic:
                result = dialogue.addParticipant(participant)
                if result and not dialogue.isRunning():
                    result = dialogue.start()
                return result        
        
        result = self.createNewDialogue(participant, dialogueTopic)        
        return result
        
    def leaveDialogue(self, participant, dialogueTopic):
        """
        Stop participating in this dialogue
        """
        result = False
        for dialogue in self.dialogues:
            if dialogue.getTopic() == dialogueTopic:
                result = dialogue.removeParticipant(participant)
                
                if dialogue.getNumParticipants() == 0:
                    dialogue.stop()
                    try:
                        self.dialogues.remove(dialogue)
                    except:
                        self.notify.warning("Couldn't find the dialogue: %s" %dialogue)
                        
        return result