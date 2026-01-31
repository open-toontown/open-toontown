from toontown.toonbase import TTLocalizer
from toontown.toontowngui import TTDialog


class TutorialForceAcknowledge:

    def __init__(self, doneEvent):
        self.doneEvent = doneEvent
        self.dialog = None

    def enter(self):
        # Make the toon stop running.
        base.localAvatar.loop("neutral")
        self.doneStatus = {'mode': 'incomplete'}
        msg = TTLocalizer.TutorialForceAcknowledgeMessage
        self.dialog = TTDialog.TTDialog(text=msg,
                                        command=self.handleOk,
                                        style=TTDialog.Acknowledge)

    def exit(self):
        if self.dialog:
            self.dialog.cleanup()
            self.dialog = None

    def handleOk(self, value):
        messenger.send(self.doneEvent, [self.doneStatus])
