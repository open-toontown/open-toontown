from otp.speedchat.SCMenu import SCMenu
from TTSCToontaskTerminal import TTSCToontaskTerminal
from otp.speedchat.SCStaticTextTerminal import SCStaticTextTerminal
from toontown.quest import Quests

class TTSCToontaskMenu(SCMenu):

    def __init__(self):
        SCMenu.__init__(self)
        self.accept('questsChanged', self.__tasksChanged)
        self.__tasksChanged()

    def destroy(self):
        SCMenu.destroy(self)

    def __tasksChanged(self):
        self.clearMenu()
        try:
            lt = base.localAvatar
        except:
            return

        phrases = []

        def addTerminal(terminal, self = self, phrases = phrases):
            displayText = terminal.getDisplayText()
            if displayText not in phrases:
                self.append(terminal)
                phrases.append(displayText)

        for task in lt.quests:
            taskId, fromNpcId, toNpcId, rewardId, toonProgress = task
            q = Quests.getQuest(taskId)
            if q is None:
                continue
            msgs = q.getSCStrings(toNpcId, toonProgress)
            if type(msgs) != type([]):
                msgs = [msgs]
            for i in xrange(len(msgs)):
                addTerminal(TTSCToontaskTerminal(msgs[i], taskId, toNpcId, toonProgress, i))

        needToontask = 1
        if hasattr(lt, 'questCarryLimit'):
            needToontask = len(lt.quests) != lt.questCarryLimit
        if needToontask:
            addTerminal(SCStaticTextTerminal(1299))
        return
