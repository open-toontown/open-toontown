#-------------------------------------------------------------------------------
# Contact: Rob Gordon
# Created: Nov 2008
#
# Purpose: The gui that shows how many jellybeans you got from a party activity.
#-------------------------------------------------------------------------------

# Panda imports
from pandac.PandaModules import TextNode
from direct.gui.DirectGui import DirectFrame
from direct.gui.DirectGui import DirectButton
from direct.gui.DirectGui import DirectLabel
from direct.gui import DirectGuiGlobals
from direct.directnotify.DirectNotifyGlobal import directNotify

# Toontown imports
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer

class JellybeanRewardGui(DirectFrame):
    """
    This class does not load a gui model specifically created for this purpose.
    Instead, it loads sub-parts of other models and cobbles them together into
    a frankenstein gui. As such, changing any of those models could
    inadvertently change how this gui looks. Ideally this class would be 
    refactored to use a gui model specific to this class.
    """
    notify = directNotify.newCategory("JellybeanRewardGui")
    
    PreCountdownDelay = 1.0
    CountDownRate = 0.2 # how quickly we transfer beans from reward box to your jar
    JarLabelTextColor = (0.95, 0.95, 0.0, 1.0)
    JarLabelMaxedTextColor = (1.0, 0.0, 0.0, 1.0)
    
    def __init__(self, doneEvent):
        self.doneEvent = doneEvent
        DirectFrame.__init__(self)
        self.reparentTo(aspect2d)
        self.setPos(0.0, 0.0, 0.16)
        self.stash()
        # load the public party gui and extract the sub-chunk of the model that
        # we will use as the background for this gui
        publicPartyGui = loader.loadModel("phase_4/models/parties/publicPartyGUI")
        # create a top level DirectFrame to hold everything else
        self.frame = DirectFrame(
            parent = self,
            geom = publicPartyGui.find("**/activities_background"),
            geom_pos = (-0.8, 0.0, 0.2),
            geom_scale = 2.0,
            relief = None,
        )
        
        # counter for beans won in the activity
        self.earnedLabel = DirectLabel(
            parent = self,
            relief = None,
            text = str(0),
            text_align = TextNode.ACenter,
            text_pos = (0.0, -0.07),
            text_scale = 0.2,
            text_fg = (0.95, 0.95, 0.0, 1.0),
            text_font = ToontownGlobals.getSignFont(),
            textMayChange = True,
            image = DirectGuiGlobals.getDefaultDialogGeom(),
            image_scale = (0.33, 1.0, 0.33),
            pos = (-0.3, 0.0, 0.2),
            scale = 0.9,
        )
        
        # counter with jellybean jar in the background for beans in the
        # "pocketbook" (the beans you carry around with you that are not in your
        # home bank)
        purchaseModels = loader.loadModel("phase_4/models/gui/purchase_gui")
        jarImage = purchaseModels.find("**/Jar")
        self.jarLabel = DirectLabel(
            parent = self,
            relief = None,
            text = str(0),
            text_align = TextNode.ACenter,
            text_pos = (0.0, -0.07),
            text_scale = 0.2,
            text_fg = JellybeanRewardGui.JarLabelTextColor,
            text_font = ToontownGlobals.getSignFont(),
            textMayChange = True,
            image = jarImage,
            scale = 0.7,
            pos = (0.3, 0.0, 0.17),
        )
        purchaseModels.removeNode()
        del purchaseModels
        jarImage.removeNode()
        del jarImage
        
        # message text
        self.messageLabel = DirectLabel(
            parent = self,
            relief = None,
            text = "",
            text_align = TextNode.ALeft,
            text_wordwrap = 16.0,
            text_scale = 0.07,
            pos = (-0.52, 0.0, -0.1),
            textMayChange = True,
        )

        self.doubledJellybeanLabel = DirectLabel(
            parent = self,
            relief = None,
            text = TTLocalizer.PartyRewardDoubledJellybean,
            text_align = TextNode.ACenter,
            text_wordwrap = 12.0,
            text_scale = 0.09,
            text_fg = (1.0, 0.125, 0.125, 1.0),
            pos = (0.0, 0.0, -0.465),
            textMayChange = False,
        )
        self.doubledJellybeanLabel.hide()
        
        # button to close the gui when the player is done reading it
        self.closeButton = DirectButton(
            parent = self,
            relief = None,
            text = TTLocalizer.PartyJellybeanRewardOK,
            text_align = TextNode.ACenter,
            text_scale = 0.065,
            text_pos = (0.0, -0.625),
            geom = (
                publicPartyGui.find("**/startButton_up"),
                publicPartyGui.find("**/startButton_down"),
                publicPartyGui.find("**/startButton_rollover"),
                publicPartyGui.find("**/startButton_inactive"),
            ),
            geom_pos = (-0.39, 0.0, 0.125), # place the geom to line up with the text
            command = self._close,
        )
        
        publicPartyGui.removeNode()
        del publicPartyGui
        
        self.countSound = base.loadSfx("phase_13/audio/sfx/tick_counter_short.mp3")
        self.overMaxSound = base.loadSfx("phase_13/audio/sfx/tick_counter_overflow.mp3")


    def showReward(self, earnedAmount, jarAmount, message):
        """
        This function assumes that the amount earned has already been updated
        for the toon. 
        
        Parameters:
          earnedAmount- How many jellybeans the toon gets
          jarAmount- Amount in their pocketbook jar 
          message- Activity-specific information to display while showing the
                   jellybean reward animation.
        """
        JellybeanRewardGui.notify.debug("showReward( earnedAmount=%d, jarAmount=%d, ...)" %(earnedAmount, jarAmount))
        # set parameters
        self.earnedCount = earnedAmount
        self.earnedLabel["text"] = str(self.earnedCount)
        self.jarCount = jarAmount
        self.jarMax = base.localAvatar.getMaxMoney()
        self.jarLabel["text"] = str( self.jarCount )
        self.jarLabel["text_fg"] = JellybeanRewardGui.JarLabelTextColor
        self.messageLabel["text"] = message
        if base.cr.newsManager.isHolidayRunning(ToontownGlobals.JELLYBEAN_DAY):
            self.doubledJellybeanLabel.show()
        else:
            self.doubledJellybeanLabel.hide()
        # show the gui
        self.unstash()
        taskMgr.doMethodLater(
            JellybeanRewardGui.PreCountdownDelay,
            self.transferOneJellybean,
            "JellybeanRewardGuiTransferOneJellybean",
            extraArgs = [],
        )


    def transferOneJellybean(self):
        if self.earnedCount == 0:
            return
        # count the beans won counter down and the total counter up
        self.earnedCount -= 1
        self.earnedLabel["text"] = str(self.earnedCount)
        self.jarCount += 1
        # only update the total display if under max
        if self.jarCount <= self.jarMax:
            self.jarLabel['text'] = str(self.jarCount)
        # if we have reached the max, color the jar text accordingly
        elif self.jarCount > self.jarMax:
            self.jarLabel["text_fg"] = JellybeanRewardGui.JarLabelMaxedTextColor
        
        # play the counting sound
        if self.jarCount <= self.jarMax:
            base.playSfx(self.countSound)
        # or the over max sound
        else:
            base.playSfx(self.overMaxSound)
        taskMgr.doMethodLater(
            JellybeanRewardGui.CountDownRate,
            self.transferOneJellybean,
            "JellybeanRewardGuiTransferOneJellybean",
            extraArgs = [],
        )


    def _close(self):
        taskMgr.remove("JellybeanRewardGuiTransferOneJellybean")
        self.stash()
        messenger.send(self.doneEvent)


    def destroy(self):
        taskMgr.remove("JellybeanRewardGuiTransferOneJellybean")
        del self.countSound
        del self.overMaxSound
        self.frame.destroy()
        self.earnedLabel.destroy()
        self.jarLabel.destroy()
        self.messageLabel.destroy()
        self.closeButton.destroy()
        DirectFrame.destroy(self)
