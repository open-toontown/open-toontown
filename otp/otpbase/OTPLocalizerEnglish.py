import string
from otp.otpbase.OTPLocalizerEnglishProperty import *
lTheBrrrgh = 'The Brrrgh'
lDaisyGardens = 'Daisy Gardens'
lDonaldsDock = "Donald's Dock"
lDonaldsDreamland = "Donald's Dreamland"
lMinniesMelodyland = "Minnie's Melodyland"
lToontownCentral = 'Toontown Central'
lGoofySpeedway = 'Goofy Speedway'
lOutdoorZone = "Chip 'n Dale's Acorn Acres"
lGolfZone = "Chip 'n Dale's MiniGolf"
lCancel = 'Cancel'
lClose = 'Close'
lOK = 'OK'
lNext = 'Next'
lNo = 'No'
lQuit = 'Quit'
lYes = 'Yes'
Cog = 'Cog'
Cogs = 'Cogs'
DialogOK = lOK
DialogCancel = lCancel
DialogYes = lYes
DialogNo = lNo
DialogDoNotShowAgain = 'Do Not\nShow Again'
WhisperNoLongerFriend = '%s left your friends list.'
WhisperNowSpecialFriend = '%s is now your True Friend!'
WhisperComingToVisit = '%s is coming to visit you.'
WhisperFailedVisit = '%s tried to visit you.'
WhisperTargetLeftVisit = '%s has gone somewhere else. Try again!'
WhisperGiveupVisit = "%s couldn't find you because you're moving around!"
WhisperIgnored = '%s is ignoring you!'
TeleportGreeting = 'Hi, %s.'
WhisperFriendComingOnline = '%s is coming online!'
WhisperFriendLoggedOut = '%s has logged out.'
WhisperPlayerOnline = '%s logged into %s'
WhisperPlayerOffline = '%s is offline.'
WhisperUnavailable = 'That player is no longer available for whispers.'
DialogSpecial = 'ooo'
DialogExclamation = '!'
DialogQuestion = '?'
ChatInputNormalSayIt = 'Say It'
ChatInputNormalCancel = lCancel
ChatInputNormalWhisper = 'Whisper'
ChatInputWhisperLabel = 'To %s'
SCEmoteNoAccessMsg = 'You do not have access\nto this emotion yet.'
SCEmoteNoAccessOK = lOK
ParentLogin = 'Parent Login'
ParentPassword = 'Parent Account Password'
ChatGarblerDefault = ['blah']
ChatManagerChat = 'Chat'
ChatManagerWhisperTo = 'Whisper to:'
ChatManagerWhisperToName = 'Whisper To:\n%s'
ChatManagerCancel = lCancel
ChatManagerWhisperOffline = '%s is offline.'
OpenChatWarning = 'To become True Friends with somebody, click on them, and select "True Friends" from the detail panel.\n\nSpeedChat Plus can also be enabled, which allow users to chat by typing words found in the Disney SpeedChat Plus dictionary.\n\nTo activate these features or to learn more, exit Toontown and then click on Membership and select Manage Account.  Log in to edit your "Community Settings."\n\nIf you are under 18, you need a Parent Account to manage these settings.'
OpenChatWarningOK = lOK
UnpaidChatWarning = 'Once you have subscribed, you can use this button to chat with your friends using the keyboard.  Until then, you should chat with other Toons using SpeedChat.'
UnpaidChatWarningPay = 'Subscribe'
UnpaidChatWarningContinue = 'Continue Free Trial'
PaidNoParentPasswordWarning = 'Use this button to chat with your friends by using the keyboard, enable it through your Account Manager on the Toontown Web site. Until then, you can chat by using SpeedChat.'
UnpaidNoParentPasswordWarning = 'This is for SpeedChat Plus, which allows users to chat by typing words found in the Disney SpeedChat Plus dictionary. To activate this feature, exit Toontown and click on Membership. Select Manage Account and log in to edit your "Community Settings." If you are under 18, you need a Parent Account to manage these settings.'
PaidNoParentPasswordWarningSet = 'Update Chat Settings'
PaidNoParentPasswordWarningContinue = 'Continue Playing Game'
PaidParentPasswordUKWarning = 'Once you have Enabled Chat, you can enable this button to chat with your friends using the keyboard. Until then, you should chat with other Toons using SpeedChat.'
PaidParentPasswordUKWarningSet = 'Enable Chat Now!'
PaidParentPasswordUKWarningContinue = 'Continue Playing Game'
NoSecretChatWarningTitle = 'Parental Controls'
NoSecretChatWarning = 'To chat with a friend, the True Friends feature must first be enabled.  Kids, have your parent visit the Toontown Web site to learn about True Friends.'
RestrictedSecretChatWarning = 'To get or enter a True Friend Code, log in with the Parent Account. You can disable this prompt by changing your True Friends options.'
NoSecretChatWarningOK = lOK
NoSecretChatWarningCancel = lCancel
NoSecretChatWarningWrongPassword = "That's not the correct Parent Account.  Please log in with the Parent Account that is linked to this account."
NoSecretChatAtAllTitle = 'Open Chat With True Friends'
NoSecretChatAtAll = 'Open Chat with True Friends allows real-life friends to chat openly with each other by means of a True Friend Code that must be shared outside of the game.\n\nTo activate these features or to learn more, exit Toontown and then click on Membership and select Manage Account. Log in to edit your "Community Settings." If you are under 18, you need a Parent Account to manage these settings.'
NoSecretChatAtAllAndNoWhitelistTitle = 'Chat button'
NoSecretChatAtAllAndNoWhitelist = 'You can use the blue Chat button to communicate with other Toons by using Speechat Plus or Open Chat with True Friends.\n\nSpeedchat Plus is a form of type chat that allows users to communicate by using the Disney SpeedChat Plus dictionary.\n\nOpen Chat with True Friends allows real-life friends to chat openly with each other by means of a True Friend Code that must be shared outside of the game.\n\nTo activate these features or to learn more, exit Toontown and then click on Membership and select Manage Account.  Log in to edit your "Community Settings." If you are under 18, you need a Parent Account to manage these settings.'
NoSecretChatAtAllOK = lOK
ChangeSecretFriendsOptions = 'Change True Friends Options'
ChangeSecretFriendsOptionsWarning = '\nPlease enter the Parent Account Password to change your True Friends options.'
ActivateChatTitle = 'True Friends Options'
WhisperToFormat = 'To %s %s'
WhisperToFormatName = 'To %s'
WhisperFromFormatName = '%s whispers'
ThoughtOtherFormatName = '%s thinks'
ThoughtSelfFormatName = 'You think'
from pandac.PandaModules import TextProperties
from pandac.PandaModules import TextPropertiesManager
shadow = TextProperties()
shadow.setShadow(-0.025, -0.025)
shadow.setShadowColor(0, 0, 0, 1)
TextPropertiesManager.getGlobalPtr().setProperties('shadow', shadow)
red = TextProperties()
red.setTextColor(1, 0, 0, 1)
TextPropertiesManager.getGlobalPtr().setProperties('red', red)
green = TextProperties()
green.setTextColor(0, 1, 0, 1)
TextPropertiesManager.getGlobalPtr().setProperties('green', green)
yellow = TextProperties()
yellow.setTextColor(1, 1, 0, 1)
TextPropertiesManager.getGlobalPtr().setProperties('yellow', yellow)
midgreen = TextProperties()
midgreen.setTextColor(0.2, 1, 0.2, 1)
TextPropertiesManager.getGlobalPtr().setProperties('midgreen', midgreen)
blue = TextProperties()
blue.setTextColor(0, 0, 1, 1)
TextPropertiesManager.getGlobalPtr().setProperties('blue', blue)
white = TextProperties()
white.setTextColor(1, 1, 1, 1)
TextPropertiesManager.getGlobalPtr().setProperties('white', white)
black = TextProperties()
black.setTextColor(0, 0, 0, 1)
TextPropertiesManager.getGlobalPtr().setProperties('black', black)
grey = TextProperties()
grey.setTextColor(0.5, 0.5, 0.5, 1)
TextPropertiesManager.getGlobalPtr().setProperties('grey', grey)
ActivateChat = "True Friends allows one member to chat with another member only by means of a True Friend Code that must be communicated outside of the game. True Friends is not moderated or supervised.\n\nPlease choose one of Toontown's True Friends options:\n\n      \x01shadow\x01No True Friends\x02 - Ability to make True Friends is disabled.\n      This offers the highest level of control.\n\n      \x01shadow\x01Restricted True Friends\x02 - Requires the Parent Account Password to make\n      each new True Friend.\n\n      \x01shadow\x01Unrestricted True Friends\x02 - Once enabled with the Parent Account Password,\n      it is not required to supply the Parent Account Password to make each new\n      True Friend. \x01red\x01This option is not recommended for children under 13.\x02\n\n\n\n\n\n\nBy enabling the True Friends feature, you acknowledge that there are some risks inherent in the True Friends feature and that you have been informed of, and agree to accept, any such risks."
ActivateChatYes = 'Update'
ActivateChatNo = lCancel
ActivateChatMoreInfo = 'More Info'
ActivateChatPrivacyPolicy = 'Privacy Policy'
ActivateChatPrivacyPolicy_Button1A = 'Version 1'
ActivateChatPrivacyPolicy_Button1K = 'Version 1'
ActivateChatPrivacyPolicy_Button2A = 'Version 2'
ActivateChatPrivacyPolicy_Button2K = 'Version 2'
PrivacyPolicyText_1A = [' ']
PrivacyPolicyText_1K = [' ']
PrivacyPolicyText_2A = [' ']
PrivacyPolicyText_2K = [' ']
PrivacyPolicyText_Intro = [' ']
PrivacyPolicyClose = lClose
SecretFriendsInfoPanelOk = lOK
SecretFriendsInfoPanelClose = lClose
SecretFriendsInfoPanelText = ['\nThe Open Chat with True Friends Feature\n\nThe Open Chat with True Friends feature enables a member to chat directly with another member within Disney\'s Toontown Online (the "Service") once the members establish a True Friends connection.  When your child attempts to use the Open Chat with True Friends feature, we will require that you indicate your consent to your child\'s use of this feature by entering your Parent Account Password.  Here is a detailed description of the process of creating an Open Chat with True Friends connection between members whom we will call "Sally" and "Mike."\n1. Sally\'s parent and Mike\'s parent each enable the Open Chat with True Friends feature by entering their respective Parent Account Passwords either (a) in the Account Options areas within the Service, or (b) when prompted within the game by a Parental Controls pop-up.\n2. Sally requests a True Friend Code (described below) from within the Service.\n',
 "\n3. Sally's True Friend Code is communicated to Mike outside of the Service. (Sally's True Friend Code may be communicated to Mike either directly by Sally, or indirectly through Sally's disclosure of the True Friend Code to another person.)\n4. Mike submits Sally's True Friend Code to the Service within 48 hours of the time that Sally requested the True Friend Code from the Service.\n5. The Service then notifies Mike that Sally has become Mike's True Friend.  The Service similarly notifies Sally that Mike has become Sally's True Friend.\n6. Sally and Mike can now open chat directly with each other until either one chooses to terminate the other as a True Friend, or until the Open Chat with True Friends feature is disabled for either Sally or Mike by their respective parent.  The True Friends connection can thus be disabled anytime by either: (a) a member removing the True Friend from his or her friends list (as described in the Service); or, (b) the parent of that member disabling the Open Chat with ",
 "\nTrue Friends feature by going to the Account Options area within the Service and following the steps set forth there.\n\nA True Friend Code is a computer-generated random code assigned to a particular member. The True Friend Code must be used to activate a True Friend connection within 48 hours of the time that the member requests the True Friend Code; otherwise, the True Friend Code expires and cannot be used.  Moreover, a single True Friend Code can only be used to establish one True Friend connection.  To make additional True Friend connections, a member must request an additional True Friend Code for each additional True Friend.\n\nTrue Friendships do not transfer.  For example, if Sally becomes a True Friend of Mike, and Mike becomes a True Friend of Jessica, Sally does not automatically become Jessica's True Friend.  In order for Sally and Jessica to\n",
 '\nbecome True Friends, one of them must request a new True Friend Code from the Service and communicate it to the other.\n\nTrue Friends communicate with one another in a free-form interactive open chat.  The content of this chat is directly entered by the participating member and is processed through the Service, which is operated by the Walt Disney Internet Group ("WDIG"), 500 S. Buena Vista St., Burbank, CA 91521-7691.  While we advise members not to exchange personal information such as first and last names, e-mail addresses, postal addresses, or phone numbers while using Open Chat with True Friends, we cannot guarantee that such exchanges of personal information will not happen. Although the True Friends chat is automatically filtered for most bad words, Open Chat with True Friends may be moderated, and Disney reserves the right to moderate any part of the Service that Disney,\n',
 "\nin its sole and absolute discretion, deems necessary. However, because Open Chat with True Friends will not always be moderated, if the Parent Account allows a child to use his or her account with the Open Chat with True Friends feature enabled, we strongly encourage parents to supervise their child or children while they play in the Service. By enabling the Open Chat with True Friends feature, the Parent Account acknowledges that there are some risks inherent in the Open Chat with True Friends feature and that the Parent Account has been informed of, and agrees to accept, any such risks, whether foreseeable or otherwise. \n\nWDIG does not use the content of True Friends chat for any purpose other than communicating that content to the member's true friend, and does not disclose that content to any third party except: (1) if required by law, for example, to comply with a court order or subpoena; (2) to enforce the Terms of Use\n",
 "\napplicable to the Service (which may be accessed on the home page of the Service); or, (3) to protect the safety and security of Members of the Service and the Service itself. In accordance with the Children's Online Privacy Protection Act, we are prohibited from conditioning, and do not condition, a child's participation in any activity (including Open Chat with True Friends) on the child's disclosing more personal information than is reasonably necessary to participate in such activity.\n\nIn addition, as noted above, we recognize the right of a parent to refuse to permit us to continue to allow a child to use the True Friends feature. By enabling the Open Chat with True Friends feature, you acknowledge that there are some risks inherent in the ability of members to open chat with one another through the Open Chat with True Friends feature, and that you have been informed of, and agree to accept, any such risks, whether foreseeable or otherwise.\n"]
LeaveToPay = 'Click Purchase to exit the game and buy a Membership at toontown.com'
LeaveToPayYes = 'Purchase'
LeaveToPayNo = lCancel
LeaveToSetParentPassword = 'In order to set parent account password, the game will exit to the Toontown website.'
LeaveToSetParentPasswordYes = 'Set Password'
LeaveToSetParentPasswordNo = lCancel
LeaveToEnableChatUK = 'In order to enable chat, the game will exit to the Toontown website.'
LeaveToEnableChatUKYes = 'Enable Chat'
LeaveToEnableChatUKNo = lCancel
ChatMoreInfoOK = lOK
SecretChatDeactivated = 'The "True Friends" feature has been disabled.'
RestrictedSecretChatActivated = 'The "Restricted True Friends" feature has been enabled!'
SecretChatActivated = 'The "Unrestricted True Friends" feature has been enabled!'
SecretChatActivatedOK = lOK
SecretChatActivatedChange = 'Change Options'
ProblemActivatingChat = 'Oops!  We were unable to activate the "True Friends" chat feature.\n\n%s\n\nPlease try again later.'
ProblemActivatingChatOK = lOK
MultiPageTextFrameNext = lNext
MultiPageTextFramePrev = 'Previous'
MultiPageTextFramePage = 'Page %s/%s'
GuiScreenToontownUnavailable = 'The server appears to be temporarily unavailable, still trying...'
GuiScreenCancel = lCancel
CreateAccountScreenUserName = 'Account Name'
CreateAccountScreenPassword = 'Password'
CreateAccountScreenConfirmPassword = 'Confirm Password'
CreateAccountScreenCancel = lCancel
CreateAccountScreenSubmit = 'Submit'
CreateAccountScreenConnectionErrorSuffix = '.\n\nPlease try again later.'
CreateAccountScreenNoAccountName = 'Please enter an account name.'
CreateAccountScreenAccountNameTooShort = 'Your account name must be at least %s characters long. Please try again.'
CreateAccountScreenPasswordTooShort = 'Your password must be at least %s characters long. Please try again.'
CreateAccountScreenPasswordMismatch = 'The passwords you typed did not match. Please try again.'
CreateAccountScreenUserNameTaken = 'That user name is already taken. Please try again.'
CreateAccountScreenInvalidUserName = 'Invalid user name.\nPlease try again.'
CreateAccountScreenUserNameNotFound = 'User name not found.\nPlease try again or create a new account.'
CRConnecting = 'Connecting...'
CRNoConnectTryAgain = 'Could not connect to %s:%s. Try again?'
CRNoConnectProxyNoPort = 'Could not connect to %s:%s.\n\nYou are communicating to the internet via a proxy, but your proxy does not permit connections on port %s.\n\nYou must open up this port, or disable your proxy, in order to play.  If your proxy has been provided by your ISP, you must contact your ISP to request them to open up this port.'
CRMissingGameRootObject = 'Missing some root game objects.  (May be a failed network connection).\n\nTry again?'
CRNoDistrictsTryAgain = 'No Districts are available. Try again?'
CRRejectRemoveAvatar = 'The avatar was not able to be deleted, try again another time.'
CRLostConnection = 'Your internet connection to the servers has been unexpectedly broken.'
CRBootedReasons = {1: 'An unexpected problem has occurred.  Your connection has been lost, but you should be able to connect again and go right back into the game.',
 100: 'You have been disconnected because someone else just logged in using your account on another computer.',
 120: 'You have been disconnected because of a problem with your authorization to use keyboard chat.',
 122: 'There has been an unexpected problem logging you in.  Please contact customer support.',
 125: 'Your installed files appear to be invalid.  Please use the Play button on the official website to run.',
 126: 'You are not authorized to use administrator privileges.',
 127: 'A problem has occurred with your Toon.  Please contact Member Services via phone or email and reference Error Code 127.  Thank you.',
 151: 'You have been logged out by an administrator working on the servers.',
 152: "There has been a reported violation of our Terms of Use connected to '%(name)s'. For more details, please review the message sent to the e-mail address associated with '%(name)s'.",
 153: 'The district you were playing on has been reset.  Everyone who was playing on that district has been disconnected.  However, you should be able to connect again and go right back into the game.',
 288: 'Sorry, you have used up all of your available minutes this month.',
 349: 'Sorry, you have used up all of your available minutes this month.'}
CRBootedReasonUnknownCode = 'An unexpected problem has occurred (error code %s).  Your connection has been lost, but you should be able to connect again and go right back into the game.'
CRTryConnectAgain = '\n\nTry to connect again?'
CRToontownUnavailable = 'The server appears to be temporarily unavailable, still trying...'
CRToontownUnavailableCancel = lCancel
CRNameCongratulations = 'CONGRATULATIONS!!'
CRNameAccepted = 'Your name has been\napproved by the Toon Council.\n\nFrom this day forth\nyou will be named\n"%s"'
CRServerConstantsProxyNoPort = 'Unable to contact %s.\n\nYou are communicating to the internet via a proxy, but your proxy does not permit connections on port %s.\n\nYou must open up this port, or disable your proxy, in order to play.  If your proxy has been provided by your ISP, you must contact your ISP to request them to open up this port.'
CRServerConstantsProxyNoCONNECT = 'Unable to contact %s.\n\nYou are communicating to the internet via a proxy, but your proxy does not support the CONNECT method.\n\nYou must enable this capability, or disable your proxy, in order to play.  If your proxy has been provided by your ISP, you must contact your ISP to request them to enable this capability.'
CRServerConstantsTryAgain = 'Unable to contact %s.\n\nThe account server might be temporarily down, or there might be some problem with your internet connection.\n\nTry again?'
CRServerDateTryAgain = 'Could not get server date from %s. Try again?'
AfkForceAcknowledgeMessage = 'Your toon got sleepy and went to bed.'
PeriodTimerWarning = 'Your available time is almost over!'
PeriodForceAcknowledgeMessage = 'Sorry, you have used up all of your available time. Please exit to purchase more.'
CREnteringToontown = 'Entering...'
DownloadWatcherUpdate = 'Downloading %s'
DownloadWatcherInitializing = 'Download Initializing...'
LoginScreenUserName = 'Account Name'
LoginScreenPassword = 'Password'
LoginScreenLogin = 'Login'
LoginScreenCreateAccount = 'Create Account'
LoginScreenQuit = lQuit
LoginScreenLoginPrompt = 'Please enter a user name and password.'
LoginScreenBadPassword = 'Bad password.\nPlease try again.'
LoginScreenInvalidUserName = 'Invalid user name.\nPlease try again.'
LoginScreenUserNameNotFound = 'User name not found.\nPlease try again or create a new account.'
LoginScreenPeriodTimeExpired = 'Sorry, you have used up all of your available time.'
LoginScreenNoNewAccounts = 'Sorry, we are not accepting new accounts at this time.'
LoginScreenTryAgain = 'Try Again'
DialogSpecial = 'ooo'
DialogExclamation = '!'
DialogQuestion = '?'
DialogLength1 = 6
DialogLength2 = 12
DialogLength3 = 20
GlobalSpeedChatName = 'SpeedChat'
SCMenuPromotion = 'PROMOTIONAL'
SCMenuElection = 'ELECTION'
SCMenuEmotions = 'EMOTIONS'
SCMenuCustom = 'MY PHRASES'
SCMenuResistance = 'UNITE!'
SCMenuPets = 'PETS'
SCMenuPetTricks = 'TRICKS'
SCMenuCog = 'COG SPEAK'
SCMenuHello = 'HELLO'
SCMenuBye = 'GOODBYE'
SCMenuHappy = 'HAPPY'
SCMenuSad = 'SAD'
SCMenuFriendly = 'FRIENDLY'
SCMenuSorry = 'SORRY'
SCMenuStinky = 'STINKY'
SCMenuPlaces = 'PLACES'
SCMenuToontasks = 'TOONTASKS'
SCMenuBattle = 'BATTLE'
SCMenuGagShop = 'GAG SHOP'
SCMenuFactory = 'FACTORY'
SCMenuKartRacing = 'RACING'
SCMenuFactoryMeet = 'MEET'
SCMenuCFOBattle = 'C.F.O.'
SCMenuCFOBattleCranes = 'CRANES'
SCMenuCFOBattleGoons = 'GOONS'
SCMenuCJBattle = 'CHIEF JUSTICE'
SCMenuCEOBattle = 'C.E.O.'
SCMenuGolf = 'GOLF'
SCMenuWhiteList = 'WHITELIST'
SCMenuPlacesPlayground = 'PLAYGROUND'
SCMenuPlacesEstate = 'ESTATE'
SCMenuPlacesCogs = 'COGS'
SCMenuPlacesWait = 'WAIT'
SCMenuFriendlyYou = 'You...'
SCMenuFriendlyILike = 'I like...'
SCMenuPlacesLetsGo = "Let's go..."
SCMenuToontasksMyTasks = 'MY TASKS'
SCMenuToontasksYouShouldChoose = 'I think you should choose...'
SCMenuToontasksINeedMore = 'I need more...'
SCMenuBattleGags = 'GAGS'
SCMenuBattleTaunts = 'TAUNTS'
SCMenuBattleStrategy = 'STRATEGY'
SCMenuBoardingGroup = 'BOARDING'
SCMenuParties = 'PARTIES'
SCMenuAprilToons = "APRIL TOONS'"
SCMenuSingingGroup = 'SINGING'
SCMenuCarol = 'CAROLING'
SCMenuSillyHoliday = 'SILLY METER'
SCMenuVictoryParties = 'VICTORY PARTIES'
SCMenuSellbotNerf = 'STORM SELLBOT'
SCMenuJellybeanJam = 'JELLYBEAN WEEK'
SCMenuHalloween = 'HALLOWEEN'
SCMenuWinter = 'WINTER'
SCMenuSellbotInvasion = 'SELLBOT INVASION'
SCMenuFieldOffice = 'FIELD OFFICES'
SCMenuIdesOfMarch = 'GREEN'
FriendSecretNeedsPasswordWarningTitle = 'Parental Controls'
FriendSecretNeedsParentLoginWarning = 'To get or enter a True Friend Code, log in with the Parent Account.  You can disable this prompt by changing your True Friend options.'
FriendSecretNeedsPasswordWarning = 'To get or enter a True Friend Code, you must enter the Parent Account Password.  You can disable this prompt by changing your True Friends options.'
FriendSecretNeedsPasswordWarningOK = lOK
FriendSecretNeedsPasswordWarningCancel = lCancel
FriendSecretNeedsPasswordWarningWrongUsername = "That's not the correct username.  Please enter the username of the parental account.  This is not the same username used to play the game."
FriendSecretNeedsPasswordWarningWrongPassword = "That's not the correct password.  Please enter the password of the parental account.  This is not the same password used to play the game."
FriendSecretIntro = "If you are playing Disney's Toontown Online with someone you know in the real world, you can become True Friends.  You can chat using the keyboard with your True Friends.  Other Toons won't understand what you're saying.\n\nYou do this by getting a True Friend Code.  Tell the True Friend Code to your friend, but not to anyone else.  When your friend types in your True Friend Code on his or her screen, you'll be True Friends in Toontown!"
FriendSecretGetSecret = 'Get a True Friend Code'
FriendSecretEnterSecret = 'If you have a True Friend Code from someone you know, type it here.'
FriendSecretOK = lOK
FriendSecretEnter = 'Enter True Friend Code'
FriendSecretCancel = lCancel
FriendSecretGettingSecret = 'Getting True Friend Code. . .'
FriendSecretGotSecret = "Here is your new True Friend Code.  Be sure to write it down!\n\nYou may give this True Friend Code to one person only.  Once someone types in your True Friend Code, it will not work for anyone else.  If you want to give a True Friend Code to more than one person, get another True Friend Code.\n\nThe True Friend Code will only work for the next two days.  Your friend will have to type it in before it goes away, or it won't work.\n\nYour True Friend Code is:"
FriendSecretTooMany = "Sorry, you can't have any more True Friend Codes today.  You've already had more than your fair share!\n\nTry again tomorrow."
FriendSecretTryingSecret = 'Trying True Friend Code. . .'
FriendSecretEnteredSecretSuccess = 'You are now True Friends with %s!'
FriendSecretTimeOut = 'Sorry, secrets are not working right now.'
FriendSecretEnteredSecretUnknown = "That's not anyone's True Friend Code.  Are you sure you spelled it correctly?\n\nIf you did type it correctly, it may have expired.  Ask your friend to get a new True Friend Code for you (or get a new one yourself and give it to your friend)."
FriendSecretEnteredSecretFull = "You can't be friends with %s because one of you has too many friends on your friends list."
FriendSecretEnteredSecretFullNoName = "You can't be friends because one of you has too many friends on your friends list."
FriendSecretEnteredSecretSelf = 'You just typed in your own True Friend Code!  Now no one else can use that True Friend Code.'
FriendSecretEnteredSecretWrongProduct = "You have entered the wrong type of True Friend Code.\nThis game uses codes that begin with '%s'."
FriendSecretNowFriends = 'You are now True Friends with %s!'
FriendSecretNowFriendsNoName = 'You are now True Friends!'
FriendSecretDetermineSecret = 'What type of True Friend would you like to make?'
FriendSecretDetermineSecretAvatar = 'Avatar'
FriendSecretDetermineSecretAvatarRollover = 'A friend only in this game'
FriendSecretDetermineSecretAccount = 'Account'
FriendSecretDetermineSecretAccountRollover = 'A friend across the Disney.com network'
GuildMemberTitle = 'Member Options'
GuildMemberPromote = 'Make Officer'
GuildMemberPromoteInvite = 'Make Veteran'
GuildMemberDemoteInvite = 'Demote to Veteran'
GuildMemberGM = 'Make Guildmaster'
GuildMemberGMConfirm = 'Confirm'
GuildMemberDemote = 'Demote to Member'
GuildMemberKick = 'Remove Member'
GuildMemberCancel = lCancel
GuildMemberOnline = 'has come online.'
GuildMemberOffline = 'has gone offline.'
GuildPrefix = '(G):'
GuildNewMember = 'New Guild Member'
GuildMemberUnknown = 'Unknown'
GuildMemberGMMessage = 'Warning! Would you like to give up leadership of your guild and make %s your guild master?\n\nYou will become an officer'
GuildInviteeOK = lOK
GuildInviteeNo = lNo
GuildInviteeInvitation = '%s is inviting you to join %s.'
GuildRedeemErrorInvalidToken = 'Sorry, that code is invalid. Please try again.'
GuildRedeemErrorGuildFull = 'Sorry, this guild has too many members already.'
FriendInviteeTooManyFriends = '%s would like to be your friend, but you already have too many friends on your list!'
FriendInviteeInvitation = '%s would like to be your friend.'
FriendInviteeInvitationPlayer = "%s's player would like to be your friend."
FriendNotifictation = '%s is now your friend.'
FriendInviteeOK = lOK
FriendInviteeNo = lNo
GuildInviterWentAway = '%s is no longer present.'
GuildInviterAlready = '%s is already in a guild.'
GuildInviterBusy = '%s is busy right now.'
GuildInviterNotYet = 'Invite %s to join your guild?'
GuildInviterCheckAvailability = 'Inviting %s to join your guild.'
GuildInviterOK = lOK
GuildInviterNo = lNo
GuildInviterCancel = lCancel
GuildInviterYes = lYes
GuildInviterTooFull = 'Guild has reached maximum size.'
GuildInviterNo = lNo
GuildInviterClickToon = 'Click on the pirate you would like to invite.'
GuildInviterTooMany = 'This is a bug'
GuildInviterNotAvailable = '%s is busy right now; try again later.'
GuildInviterGuildSaidNo = '%s has declined your guild invitation.'
GuildInviterAlreadyInvited = '%s has already been invited.'
GuildInviterEndGuildship = 'Remove %s from the guild?'
GuildInviterFriendsNoMore = '%s has left the guild.'
GuildInviterSelf = 'You are already in the guild!'
GuildInviterIgnored = '%s is ignoring you.'
GuildInviterAsking = 'Asking %s to join the guild.'
GuildInviterGuildSaidYes = '%s has joined the guild!'
GuildInviterFriendKickedOut = '%s has kicked out %s from the Guild.'
GuildInviterFriendKickedOutP = '%s have kicked out %s from the Guild.'
GuildInviterFriendInvited = '%s has invited %s to the Guild.'
GuildInviterFriendInvitedP = '%s have invited %s to the Guild.'
GuildInviterFriendPromoted = '%s has promoted %s to the rank of %s.'
GuildInviterFriendPromotedP = '%s have promoted %s to the rank of %s.'
GuildInviterFriendDemoted = '%s has demoted %s to the rank of %s.'
GuildInviterFriendDemotedP = '%s have demoted %s to the rank of %s.'
GuildInviterFriendPromotedGM = '%s has named %s as the new %s'
GuildInviterFriendPromotedGMP = '%s have named %s as the new %s'
GuildInviterFriendDemotedGM = '%s has been named by %s as the new GuildMaster who became the rank of %s'
GuildInviterFriendDemotedGMP = '%s have been named by %s as the new GuildMaster who beaome the rank of %s'
FriendOnline = 'has come online.'
FriendOffline = 'has gone offline.'
FriendInviterOK = lOK
FriendInviterCancel = lCancel
FriendInviterStopBeingFriends = 'Stop being friends'
FriendInviterConfirmRemove = 'Remove'
FriendInviterYes = lYes
FriendInviterNo = lNo
FriendInviterClickToon = 'Click on the toon you would like to make friends with.'
FriendInviterTooMany = 'You have too many friends on your list to add another one now. You will have to remove some friends if you want to make friends with %s.'
FriendInviterToonTooMany = 'You have too many toon friends on your list to add another one now. You will have to remove some toon friends if you want to make friends with %s.'
FriendInviterPlayerTooMany = 'You have too many player friends on your list to add another one now. You will have to remove some player friends if you want to make friends with %s.'
FriendInviterNotYet = 'Would you like to make friends with %s?'
FriendInviterCheckAvailability = 'Seeing if %s is available.'
FriendInviterNotAvailable = '%s is busy right now; try again later.'
FriendInviterCantSee = 'This only works if you can see %s.'
FriendInviterNotOnline = 'This only works if %s is online'
FriendInviterNotOpen = '%s does not have open chat, use secrets to make friends'
FriendInviterWentAway = '%s went away.'
FriendInviterAlready = '%s is already your friend.'
FriendInviterAlreadyInvited = '%s has already been invited.'
FriendInviterAskingCog = 'Asking %s to be your friend.'
FriendInviterAskingPet = '%s jumps around, runs in circles and licks your face.'
FriendInviterAskingMyPet = '%s is already your BEST friend.'
FriendInviterEndFriendship = 'Are you sure you want to stop being friends with %s?'
FriendInviterFriendsNoMore = '%s is no longer your friend.'
FriendInviterSelf = "You are already 'friends' with yourself!"
FriendInviterIgnored = '%s is ignoring you.'
FriendInviterAsking = 'Asking %s to be your friend.'
FriendInviterFriendSaidYes = 'You are now friends with %s!'
FriendInviterPlayerFriendSaidYes = "You are now friends with %s's player, %s!"
FriendInviterFriendSaidNo = '%s said no, thank you.'
FriendInviterFriendSaidNoNewFriends = "%s isn't looking for new friends right now."
FriendInviterOtherTooMany = '%s has too many friends already!'
FriendInviterMaybe = '%s was unable to answer.'
FriendInviterDown = 'Cannot make friends now.'
TalkGuild = 'G'
TalkParty = 'P'
TalkPVP = 'PVP'
AntiSpamInChat = '***Spamming***'
IgnoreConfirmOK = lOK
IgnoreConfirmCancel = lCancel
IgnoreConfirmYes = lYes
IgnoreConfirmNo = lNo
IgnoreConfirmNotYet = 'Would you like to Ignore %s?'
IgnoreConfirmAlready = 'You are already ignoring %s.'
IgnoreConfirmSelf = 'You cannot ignore yourself!'
IgnoreConfirmNewIgnore = 'You are ignoring %s.'
IgnoreConfirmEndIgnore = 'You are no longer ignoring %s.'
IgnoreConfirmRemoveIgnore = 'Stop ignoring %s?'
EmoteList = ['Wave',
 'Happy',
 'Sad',
 'Angry',
 'Sleepy',
 'Shrug',
 'Dance',
 'Think',
 'Bored',
 'Applause',
 'Cringe',
 'Confused',
 'Belly Flop',
 'Bow',
 'Banana Peel',
 'Resistance Salute',
 'Laugh',
 lYes,
 lNo,
 lOK,
 'Surprise',
 'Cry',
 'Delighted',
 'Furious',
 'Laugh']
EmoteWhispers = ['%s waves.',
 '%s is happy.',
 '%s is sad.',
 '%s is angry.',
 '%s is sleepy.',
 '%s shrugs.',
 '%s dances.',
 '%s thinks.',
 '%s is bored.',
 '%s applauds.',
 '%s cringes.',
 '%s is confused.',
 '%s does a belly flop.',
 '%s bows to you.',
 '%s slips on a banana peel.',
 '%s gives the resistance salute.',
 '%s laughs.',
 "%s says '" + lYes + "'.",
 "%s says '" + lNo + "'.",
 "%s says '" + lOK + "'.",
 '%s is surprised.',
 '%s is crying.',
 '%s is delighted.',
 '%s is furious.',
 '%s is laughing.']
EmoteFuncDict = {'Wave': 0,
 'Happy': 1,
 'Sad': 2,
 'Angry': 3,
 'Sleepy': 4,
 'Shrug': 5,
 'Dance': 6,
 'Think': 7,
 'Bored': 8,
 'Applause': 9,
 'Cringe': 10,
 'Confused': 11,
 'Belly Flop': 12,
 'Bow': 13,
 'Banana Peel': 14,
 'Resistance Salute': 15,
 'Laugh': 16,
 lYes: 17,
 lNo: 18,
 lOK: 19,
 'Surprise': 20,
 'Cry': 21,
 'Delighted': 22,
 'Furious': 23,
 'Laugh': 24,
 'Sing Note G1': 25,
 'Sing Note A': 26,
 'Sing Note B': 27,
 'Sing Note C': 28,
 'Sing Note D': 29,
 'Sing Note E': 30,
 'Sing Note F': 31,
 'Sing Note G2': 32}
SuitBrushOffs = {'f': ["I'm late for a meeting."],
 'p': ['Push off.'],
 'ym': ['Yes Man says NO.'],
 None: ["It's my day off.",
        "I believe you're in the wrong office.",
        'Have your people call my people.',
        "You're in no position to meet with me.",
        'Talk to my assistant.']}
SuitFaceoffTaunts = {'b': ['Do you have a donation for me?',
       "I'm going to make you a sore loser.",
       "I'm going to leave you high and dry.",
       'I\'m "A Positive" I\'m going to win.',
       '"O" don\'t be so "Negative".',
       "I'm surprised you found me, I'm very mobile.",
       "I'm going to need to do a quick count on you.",
       "You're soon going to need a cookie and some juice.",
       "When I'm through you'll need to lie down.",
       'This will only hurt for a second.',
       "I'm going to make you dizzy.",
       "Good timing, I'm a pint low."],
 'm': ["You don't know who you're mingling with.",
       'Ever mingle with the likes of me?',
       'Good, it takes two to mingle.',
       "Let's mingle.",
       'This looks like a good place to mingle.',
       "Well,isn't this cozy?",
       "You're mingling with defeat.",
       "I'm going to mingle in your business.",
       "Are you sure you're ready to mingle?"],
 'ms': ['Get ready for a shake down.',
        'You had better move out of the way.',
        'Move it or lose it.',
        "I believe it's my move.",
        'This should shake you up.',
        'Prepare to be moved.',
        "I'm ready to make my move.",
        "Watch out toon, you're on shaky ground.",
        'This should be a moving moment.',
        'I feel moved to defeat you.',
        'Are you shaking yet?'],
 'hh': ["I'm way ahead of you.",
        "You're headed for big trouble.",
        "You'll wish this was all in your head.",
        "Oh good, I've been hunting for you.",
        "I'll have your head for this.",
        'Heads up!',
        "Looks like you've got a head for trouble.",
        'Headed my way?',
        'A perfect trophy for my collection.',
        'You are going to have such a headache.',
        "Don't lose your head over me."],
 'tbc': ["Watch out, I'm gouda getcha.",
         'You can call me Jack.',
         'Are you sure?  I can be such a Muenster at times.',
         'Well finally, I was afraid you were stringing me along.',
         "I'm going to cream you.",
         "Don't you think I've aged well?",
         "I'm going to make mozzarella outta ya.",
         "I've been told I'm very strong.",
         'Careful, I know your expiration date.',
         "Watch out, I'm a whiz at this game.",
         'Beating you will be a brieeze.'],
 'cr': ['RAID!',
        "You don't fit in my corporation.",
        'Prepare to be raided.',
        "Looks like you're primed for a take-over.",
        'That is not proper corporate attire.',
        "You're looking rather vulnerable.",
        'Time to sign over your assets.',
        "I'm on a toon removal crusade.",
        'You are defenseless against my ideas.',
        "Relax, you'll find this is for the best."],
 'mh': ['Are you ready for my take?',
        'Lights, camera, action!',
        "Let's start rolling.",
        'Today the role of defeated toon, will be played by - YOU!',
        'This scene will go on the cutting room floor.',
        'I already know my motivation for this scene.',
        'Are you ready for your final scene?',
        "I'm ready to roll your end credits.",
        'I told you not to call me.',
        "Let's get on with the show.",
        "There's no business like it!",
        "I hope you don't forget your lines."],
 'nc': ['Looks like your number is up.',
        'I hope you prefer extra crunchy.',
        "Now you're really in a crunch.",
        'Is it time for crunch already?',
        "Let's do crunch.",
        'Where would you like to have your crunch today?',
        "You've given me something to crunch on.",
        'This will not be smooth.',
        'Go ahead, try and take a number.',
        'I could do with a nice crunch about now.'],
 'ls': ["It's time to collect on your loan.",
        "You've been on borrowed time.",
        'Your loan is now due.',
        'Time to pay up.',
        'Well you asked for an advance and you got it.',
        "You're going to pay for this.",
        "It's pay back time.",
        'Can you lend me an ear?',
        "Good thing you're here,  I'm in a frenzy.",
        'Shall we have a quick bite?',
        'Let me take a bite at it.'],
 'mb': ['Time to bring in the big bags.',
        'I can bag this.',
        'Paper or plastic?',
        'Do you have your baggage claim?',
        "Remember, money won't make you happy.",
        'Careful, I have some serious baggage.',
        "You're about to have money trouble.",
        'Money will make your world go around.',
        "I'm too rich for your blood.",
        'You can never have too much money!'],
 'rb': ["You've been robbed.",
        "I'll rob you of this victory.",
        "I'm a royal pain!",
        'Hope you can grin and baron.',
        "You'll need to report this robbery.",
        "Stick 'em up.",
        "I'm a noble adversary.",
        "I'm going to take everything you have.",
        'You could call this neighborhood robbery.',
        'You should know not to talk to strangers.'],
 'bs': ['Never turn your back on me.',
        "You won't be coming back.",
        'Take that back or else!',
        "I'm good at cutting costs.",
        'I have lots of back up.',
        "There's no backing down now.",
        "I'm the best and I can back that up.",
        'Whoa, back up there toon.',
        'Let me get your back.',
        "You're going to have a stabbing headache soon.",
        'I have perfect puncture.'],
 'bw': ["Don't brush me aside.",
        'You make my hair curl.',
        'I can make this permanent if you want.',
        "It looks like you're going to have some split ends.",
        "You can't handle the truth.",
        "I think it's your turn to be dyed.",
        "I'm so glad you're on time for your cut.",
        "You're in big trouble.",
        "I'm going to wig out on you.",
        "I'm a big deal little toon."],
 'le': ["Careful, my legal isn't very tender.",
        'I soar, then I score.',
        "I'm bringing down the law on you.",
        'You should know, I have some killer instincts.',
        "I'm going to give you legal nightmares.",
        "You won't win this battle.",
        'This is so much fun it should be illegal.',
        "Legally, you're too small to fight me.",
        'There is no limit to my talons.',
        "I call this a citizen's arrest."],
 'sd': ["You'll never know when I'll stop.",
        'Let me take you for a spin.',
        'The doctor will see you now.',
        "I'm going to put you into a spin.",
        'You look like you need a doctor.',
        'The doctor is in, the Toon is out.',
        "You won't like my spin on this.",
        'You are going to spin out of control.',
        'Care to take a few turns with me?',
        'I have my own special spin on the subject.'],
 'f': ["I'm gonna tell the boss about you!",
       "I may be just a flunky - But I'm real spunky.",
       "I'm using you to step up the corporate ladder.",
       "You're not going to like the way I work.",
       'The boss is counting on me to stop you.',
       "You're going to look good on my resume.",
       "You'll have to go through me first.",
       "Let's see how you rate my job performance.",
       'I excel at Toon disposal.',
       "You're never going to meet my boss.",
       "I'm sending you back to the Playground."],
 'p': ["I'm gonna rub you out!",
       "Hey, you can't push me around.",
       "I'm No.2!",
       "I'm going to scratch you out.",
       "I'll have to make my point more clear.",
       'Let me get right to the point.',
       "Let's hurry, I bore easily.",
       'I hate it when things get dull.',
       'So you want to push your luck?',
       'Did you pencil me in?',
       'Careful, I may leave a mark.'],
 'ym': ["I'm positive you're not going to like this.",
        "I don't know the meaning of no.",
        'Want to meet?  I say yes, anytime.',
        'You need some positive enforcement.',
        "I'm going to make a positive impression.",
        "I haven't been wrong yet.",
        "Yes, I'm ready for you.",
        'Are you positive you want to do this?',
        "I'll be sure to end this on a positive note.",
        "I'm confirming our meeting time.",
        "I won't take no for an answer."],
 'mm': ["I'm going to get into your business!",
        'Sometimes big hurts come in small packages.',
        'No job is too small for me.',
        "I want the job done right, so I'll do it myself.",
        'You need someone to manage your assets.',
        'Oh good, a project.',
        "Well, you've managed to find me.",
        'I think you need some managing.',
        "I'll take care of you in no time.",
        "I'm watching every move you make.",
        'Are you sure you want to do this?',
        "We're going to do this my way.",
        "I'm going to be breathing down your neck.",
        'I can be very intimidating.'],
 'ds': ["You're going down!",
        'Your options are shrinking.',
        'Expect diminishing returns.',
        "You've just become expendable.",
        "Don't ask me to lay off.",
        'I might have to make a few cutbacks.',
        'Things are looking down for you.',
        'Why do you look so down?'],
 'cc': ['Surprised to hear from me?',
        'You rang?',
        'Are you ready to accept my charges?',
        'This caller always collects.',
        "I'm one smooth operator.",
        "Hold the phone -- I'm here.",
        'Have you been waiting for my call?',
        "I was hoping you'd answer my call.",
        "I'm going to cause a ringing sensation.",
        'I always make my calls direct.',
        'Boy, did you get your wires crossed.',
        'This call is going to cost you.',
        "You've got big trouble on the line."],
 'tm': ['I plan on making this inconvenient for you.',
        'Can I interest you in an insurance plan?',
        'You should have missed my call.',
        "You won't be able to get rid of me now.",
        'This a bad time?  Good.',
        'I was planning on running into you.',
        'I will be reversing the charges for this call.',
        'I have some costly items for you today.',
        'Too bad for you - I make house calls.',
        "I'm prepared to close this deal quickly.",
        "I'm going to use up a lot of your resources."],
 'nd': ['In my opinion, your name is mud.',
        "I hope you don't mind if I drop your name.",
        "Haven't we met before?",
        "Let's hurry, I'm having lunch with 'Mr. Hollywood.'",
        "Have I mentioned I know 'The Mingler?'",
        "You'll never forget me.",
        'I know all the right people to bring you down.',
        "I think I'll just drop in.",
        "I'm in the mood to drop some Toons.",
        "You name it, I've dropped it."],
 'gh': ['Put it there, Toon.',
        "Let's shake on it.",
        "I'm going to enjoy this.",
        "You'll notice I have a very firm grip.",
        "Let's seal the deal.",
        "Let's get right to the business at hand.",
        "Off handedly I'd say, you're in trouble.",
        "You'll find I'm a handful.",
        'I can be quite handy.',
        "I'm a very hands-on kinda guy.",
        'Would you like some hand-me-downs?',
        'Let me show you some of my handiwork.',
        'I think the handwriting is on the wall.'],
 'sc': ['I will make short work of you.',
        "You're about to have money trouble.",
        "You're about to be overcharged.",
        'This will be a short-term assignment.',
        "I'll be done with you in short order.",
        "You'll soon experience a shortfall.",
        "Let's make this a short stop.",
        "I think you've come up short.",
        'I have a short temper for Toons.',
        "I'll be with you shortly.",
        "You're about to be shorted."],
 'pp': ['This is going to sting a little.',
        "I'm going to give you a pinch for luck.",
        "You don't want to press your luck with me.",
        "I'm going to put a crimp in your smile.",
        'Perfect, I have an opening for you.',
        'Let me add my two cents.',
        "I've been asked to pinch-hit.",
        "I'll prove you're not dreaming.",
        'Heads you lose, tails I win.',
        'A Penny for your gags.'],
 'tw': ['Things are about to get very tight.',
        "That's Mr. Tightwad to you.",
        "I'm going to cut off your funding.",
        'Is this the best deal you can offer?',
        "Let's get going - time is money.",
        "You'll find I'm very tightfisted.",
        "You're in a tight spot.",
        'Prepare to walk a tight rope.',
        'I hope you can afford this.',
        "I'm going to make this a tight squeeze.",
        "I'm going to make a big dent in your budget."],
 'bc': ['I enjoy subtracting Toons.',
        'You can count on me to make you pay.',
        'Bean there, done that.',
        'I can hurt you where it counts.',
        'I make every bean count.',
        'Your expense report is overdue.',
        'Time for an audit.',
        "Let's step into my office.",
        'Where have you bean?',
        "I've bean waiting for you.",
        "I'm going to bean you."],
 'bf': ["Looks like you've hit rock bottom.",
        "I'm ready to feast.",
        "I'm a sucker for Toons.",
        'Oh goody, lunch time.',
        'Perfect timing, I need a quick bite.',
        "I'd like some feedback on my performance.",
        "Let's talk about the bottom line.",
        "You'll find my talents are bottomless.",
        'Good, I need a little pick-me-up.',
        "I'd love to have you for lunch."],
 'tf': ["It's time to face-off!",
        'You had better face up to defeat.',
        'Prepare to face your worst nightmare!',
        "Face it, I'm better than you.",
        'Two heads are better than one.',
        'It takes two to tango, you wanna tango?',
        "You're in for two times the trouble.",
        'Which face would you like to defeat you?',
        "I'm 'two' much for you.",
        "You don't know who you're facing.",
        'Are you ready to face your doom?'],
 'dt': ["I'm gonna give you double the trouble.",
        'See if you can stop my double cross.',
        'I serve a mean double-\x04DECKER.',
        "It's time to do some double-dealing.",
        'I plan to do some double DIPPING.',
        "You're not going to like my double play.",
        'You may want to double think this.',
        'Get ready for a double TAKE.',
        'You may want to double up against me.',
        'Doubles anyone??'],
 'ac': ["I'm going to chase you out of town!",
        'Do you hear a siren?',
        "I'm going to enjoy this.",
        'I love the thrill of the chase.',
        'Let me give you the run down.',
        'Do you have insurance?',
        'I hope you brought a stretcher with you.',
        'I doubt you can keep up with me.',
        "It's all uphill from here.",
        "You're going to need some urgent care soon.",
        'This is no laughing matter.',
        "I'm going to give you the business."]}
SpeedChatStaticTextCommon = {1: lYes,
 2: lNo,
 3: lOK,
 4: 'SPEEDCHAT PLUS'}
SpeedChatStaticTextToontown = {100: 'Hi!',
 101: 'Hello!',
 102: 'Hi there!',
 103: 'Hey!',
 104: 'Howdy!',
 105: 'Hi everybody!',
 106: 'Welcome to Toontown!',
 107: "What's up?",
 108: 'How are you doing?',
 109: 'Hello?',
 200: 'Bye!',
 201: 'Later!',
 202: 'See ya!',
 203: 'Have a nice day!',
 204: 'Have fun!',
 205: 'Good luck!',
 206: "I'll be right back.",
 207: 'I need to go.',
 208: "I'll be back later!",
 209: 'I only have a few minutes.',
 300: ':-)',
 301: 'Yay!',
 302: 'Hooray!',
 303: 'Cool!',
 304: 'Woo hoo!',
 305: 'Yeah!',
 306: 'Ha ha!',
 307: 'Hee hee!',
 308: 'Wow!',
 309: 'Great!',
 310: 'Whee!',
 311: 'Oh boy!',
 312: 'Whoopee!',
 313: 'Yippee!',
 314: 'Yee hah!',
 315: 'Toontastic!',
 400: ':-(',
 401: 'Oh no!',
 402: 'Uh oh!',
 403: 'Rats!',
 404: 'Drat!',
 405: 'Ouch!',
 406: 'Oof!',
 407: 'No!!!',
 408: 'Yikes!',
 409: 'Huh?',
 410: 'I need more Laff points.',
 500: 'Thanks!',
 501: 'No problem.',
 502: "You're welcome!",
 503: 'Any time!',
 504: 'No thank you.',
 505: 'Good teamwork!',
 506: 'That was fun!',
 507: 'Please be my friend!',
 508: "Let's work together!",
 509: 'You guys are great!',
 510: 'Are you new here?',
 511: 'Did you win?',
 512: 'I think this is too risky for you.',
 513: 'Would you like some help?',
 514: 'Can you help me?',
 515: 'Have you been here before?',
 600: 'You look nice.',
 601: 'You are awesome!',
 602: 'You rock!',
 603: 'You are a genius!',
 700: 'I like your name.',
 701: 'I like your look.',
 702: 'I like your shirt.',
 703: 'I like your skirt.',
 704: 'I like your shorts.',
 705: 'I like this game!',
 800: 'Sorry!',
 801: 'Oops!',
 802: "Sorry, I'm busy fighting Cogs!",
 803: "Sorry, I'm busy getting Jellybeans!",
 804: "Sorry, I'm busy completing a ToonTask!",
 805: 'Sorry, I had to leave unexpectedly.',
 806: 'Sorry, I was delayed.',
 807: "Sorry, I can't.",
 808: "I couldn't wait any longer.",
 809: "I can't understand you.",
 810: 'Use the %s.' % GlobalSpeedChatName,
 811: "Sorry, I'm busy fishing!",
 812: "Sorry, I'm in a building!",
 813: "Sorry, I'm helping a friend!",
 814: "Sorry, I'm busy kart racing!",
 815: "Sorry, I'm busy gardening!",
 816: "I can't get on the elevator now.",
 817: "Sorry, I'm busy golfing!",
 818: 'Sorry, my Friends List is full.',
 900: 'Hey!',
 901: 'Please go away!',
 902: 'Stop that!',
 903: "That wasn't nice!",
 904: "Don't be mean!",
 905: 'You stink!',
 906: 'Send a bug report.',
 907: "I'm stuck.",
 1000: "Let's go!",
 1001: 'Can you teleport to me?',
 1002: 'Shall we go?',
 1003: 'Where should we go?',
 1004: 'Which way?',
 1005: 'This way.',
 1006: 'Follow me.',
 1007: 'Wait for me!',
 1008: "Let's wait for my friend.",
 1009: "Let's find other Toons.",
 1010: 'Wait here.',
 1011: 'Wait a minute.',
 1012: 'Meet here.',
 1013: 'Can you come to my house?',
 1014: "Don't wait for me.",
 1015: 'Wait!',
 1016: 'Come check out my garden.',
 1017: "Let's catch the next one.",
 1100: "Let's go on the trolley!",
 1101: "Let's go back to the playground!",
 1102: "Let's go fight the %s!" % Cogs,
 1103: "Let's go take over a %s building!" % Cog,
 1104: "Let's go in the elevator!",
 1105: "Let's go to %s!" % lToontownCentral,
 1106: "Let's go to %s!" % lDonaldsDock,
 1107: "Let's go to %s!" % lMinniesMelodyland,
 1108: "Let's go to %s!" % lDaisyGardens,
 1109: "Let's go to %s!" % lTheBrrrgh,
 1110: "Let's go to %s!" % lDonaldsDreamland,
 1111: "Let's go to %s!" % lGoofySpeedway,
 1112: "Let's go to my house!",
 1113: "Let's go to your house!",
 1114: "Let's go to Sellbot HQ!",
 1115: "Let's go fight the VP!",
 1116: "Let's go in the Factory!",
 1117: "Let's go fishing!",
 1118: "Let's go fishing at my house!",
 1119: "Let's go to Cashbot HQ!",
 1120: "Let's go fight the CFO!",
 1121: "Let's go in the Mint!",
 1122: "Let's go to Lawbot HQ!",
 1123: "Let's go fight the Chief Justice!",
 1124: "Let's go in the District Attorney's Office!",
 1125: "Let's go to %s!" % lOutdoorZone,
 1126: "Let's go to %s!" % lGolfZone,
 1127: "Let's go to Bossbot HQ!",
 1128: "Let's go fight the CEO!",
 1129: "Let's go in the Cog Golf Courses!",
 1130: "Let's go take over a Field Office!",
 1200: 'What ToonTask are you working on?',
 1201: "Let's work on that.",
 1202: "This isn't what I'm looking for.",
 1203: "I'm going to look for that.",
 1204: "It isn't on this street.",
 1205: "I haven't found it yet.",
 1206: 'I need more Merits.',
 1207: 'I need more Sellbot Suit Parts.',
 1208: "This isn't what you need.",
 1209: 'I found what you need.',
 1210: 'I need more Cogbucks.',
 1211: 'I need more Jury Notices.',
 1212: 'I need more Stock Options.',
 1213: 'I need more Cashbot Suit Parts.',
 1214: 'I need more Lawbot Suit Parts.',
 1215: 'I need more Bossbot Suit Parts.',
 1299: 'I need to get a ToonTask.',
 1300: 'I think you should choose Toon-up.',
 1301: 'I think you should choose Sound.',
 1302: 'I think you should choose Drop.',
 1303: 'I think you should choose Trap.',
 1304: 'I think you should choose Lure.',
 1400: 'Hurry!',
 1401: 'Nice shot!',
 1402: 'Nice gag!',
 1403: 'Missed me!',
 1404: 'You did it!',
 1405: 'We did it!',
 1406: 'Bring it on!',
 1407: 'Piece of cake!',
 1408: 'That was easy!',
 1409: 'Run!',
 1410: 'Help!',
 1411: 'Phew!',
 1412: 'We are in trouble.',
 1413: 'I need more gags.',
 1414: 'I need a Toon-Up.',
 1415: 'You should pass.',
 1416: 'We can do this!',
 1500: "Let's use toon-up!",
 1501: "Let's use trap!",
 1502: "Let's use lure!",
 1503: "Let's use sound!",
 1504: "Let's use throw!",
 1505: "Let's use squirt!",
 1506: "Let's use drop!",
 1520: 'Rock and roll!',
 1521: "That's gotta hurt.",
 1522: 'Catch!',
 1523: 'Special delivery!',
 1524: 'Are you still here?',
 1525: "I'm SO scared!",
 1526: "That's going to leave a mark!",
 1550: "I'm going to use trap.",
 1551: "I'm going to use lure.",
 1552: "I'm going to use drop.",
 1553: 'You should use a different gag.',
 1554: "Let's all go for the same Cog.",
 1555: 'You should choose a different Cog.',
 1556: 'Go for the weakest Cog first.',
 1557: 'Go for the strongest Cog first.',
 1558: 'Save your powerful gags.',
 1559: "Don't use sound on lured Cogs.",
 1600: 'I have enough gags.',
 1601: 'I need more jellybeans.',
 1602: 'Me too.',
 1603: 'Hurry up!',
 1604: 'One more?',
 1605: 'Play again?',
 1606: "Let's play again.",
 1700: "Let's split up.",
 1701: "Let's stay together.",
 1702: "Let's battle the Cogs.",
 1703: 'Step on the switch.',
 1704: 'Go through the door.',
 1803: "I'm in the Front Entrance.",
 1804: "I'm in the Lobby.",
 1805: "I'm in the hallway outside the Lobby.",
 1806: "I'm in the hallway outside the Lobby.",
 1807: "I'm in the Gear Room.",
 1808: "I'm in the Boiler Room.",
 1809: "I'm on the East Catwalk.",
 1810: "I'm in the Paint Mixer.",
 1811: "I'm in the Paint Mixer Storage Room.",
 1812: "I'm on the West Silo Catwalk.",
 1813: "I'm in the Pipe Room.",
 1814: "I'm on the stairs to the Pipe Room.",
 1815: "I'm in the Duct Room.",
 1816: "I'm in the Side Entrance.",
 1817: "I'm in Stomper Alley.",
 1818: "I'm outside the Lava Room.",
 1819: "I'm in the Lava Room.",
 1820: "I'm in the Lava Storage Room.",
 1821: "I'm on the West Catwalk.",
 1822: "I'm in the Oil Room.",
 1823: "I'm on the Warehouse Lookout.",
 1824: "I'm in the Warehouse.",
 1825: "I'm outside the Paint Mixer.",
 1827: "I'm outside the Oil Room.",
 1830: "I'm in the East Silo Control Room.",
 1831: "I'm in the West Silo Control Room.",
 1832: "I'm in the Center Silo Control Room.",
 1833: "I'm at the East Silo.",
 1834: "I'm on the West Silo.",
 1835: "I'm on the Center Silo.",
 1836: "I'm on the West Silo.",
 1837: "I'm at the East Silo.",
 1838: "I'm on the East Silo Catwalk.",
 1840: "I'm on top of the West Silo.",
 1841: "I'm on top of the East Silo.",
 1860: "I'm on the West Silo Elevator.",
 1861: "I'm on the East Silo Elevator.",
 1903: "Let's meet in the Front Entrance.",
 1904: "Let's meet in the Lobby.",
 1905: "Let's meet in the hallway outside the Lobby.",
 1906: "Let's meet in the hallway outside the Lobby.",
 1907: "Let's meet in the Gear Room.",
 1908: "Let's meet in the Boiler Room.",
 1909: "Let's meet on the East Catwalk.",
 1910: "Let's meet in the Paint Mixer.",
 1911: "Let's meet in the Paint Mixer Storage Room.",
 1912: "Let's meet on the West Silo Catwalk.",
 1913: "Let's meet in the Pipe Room.",
 1914: "Let's meet on the stairs to the Pipe Room.",
 1915: "Let's meet in the Duct Room.",
 1916: "Let's meet in the Side Entrance.",
 1917: "Let's meet in Stomper Alley.",
 1918: "Let's meet outside the Lava Room.",
 1919: "Let's meet in the Lava Room.",
 1920: "Let's meet in the Lava Storage Room.",
 1921: "Let's meet on the West Catwalk.",
 1922: "Let's meet in the Oil Room.",
 1923: "Let's meet on the Warehouse Lookout.",
 1924: "Let's meet in the Warehouse.",
 1925: "Let's meet outside the Paint Mixer.",
 1927: "Let's meet outside the Oil Room.",
 1930: "Let's meet in the East Silo Control Room.",
 1931: "Let's meet in the West Silo Control Room.",
 1932: "Let's meet in the Center Silo Control Room.",
 1933: "Let's meet at the East Silo.",
 1934: "Let's meet on the West Silo.",
 1935: "Let's meet on the Center Silo.",
 1936: "Let's meet on the West Silo.",
 1937: "Let's meet at the East Silo.",
 1938: "Let's meet on the East Silo Catwalk.",
 1940: "Let's meet on top of the West Silo.",
 1941: "Let's meet on top of the East Silo.",
 1960: "Let's meet on the West Silo Elevator.",
 1961: "Let's meet on the East Silo Elevator.",
 2000: 'Purple',
 2001: 'Blue',
 2002: 'Cyan',
 2003: 'Teal',
 2004: 'Green',
 2005: 'Yellow',
 2006: 'Orange',
 2007: 'Red',
 2008: 'Pink',
 2009: 'Brown',
 2100: 'Please operate the crane.',
 2101: 'May I operate the crane?',
 2102: 'I need practice operating the crane.',
 2103: 'Pick up a disabled goon.',
 2104: 'Throw the goon at the CFO.',
 2105: 'Throw a safe now!',
 2106: "Don't throw a safe now!",
 2107: 'A safe will knock off his helmet.',
 2108: 'A safe will become his new helmet.',
 2109: "I can't reach any safes.",
 2110: "I can't reach any goons.",
 2120: 'Please disable the goons.',
 2121: 'I would rather disable goons.',
 2122: 'I need practice disabling goons.',
 2123: 'Please stay nearby.',
 2124: 'Keep moving.',
 2125: 'I need to keep moving.',
 2126: 'Look for someone who needs help.',
 2130: 'Please save the treasures.',
 2131: 'Take the treasures.',
 2132: 'I need treasures!',
 2133: 'Look out!',
 2200: 'You need to hit the scale.',
 2201: 'I will hit the scale.',
 2202: 'I need help with the scale!',
 2203: 'You need to stun the Cogs.',
 2204: 'I will stun the Cogs.',
 2205: 'I need help with the Cogs!',
 2206: 'I need more evidence!',
 2207: "I'm shooting for chairs in the top row.",
 2208: "I'm shooting for chairs in the bottom row.",
 2209: "Move out of the way! We can't hit the pan.",
 2210: "I'll do Toon-Ups for us.",
 2211: "I don't have any bonus weight.",
 2212: 'I have a bonus weight of 1.',
 2213: 'I have a bonus weight of 2.',
 2214: 'I have a bonus weight of 3.',
 2215: 'I have a bonus weight of 4.',
 2216: 'I have a bonus weight of 5.',
 2217: 'I have a bonus weight of 6.',
 2218: 'I have a bonus weight of 7.',
 2219: 'I have a bonus weight of 8.',
 2220: 'I have a bonus weight of 9.',
 2221: 'I have a bonus weight of 10.',
 2222: 'I have a bonus weight of 11.',
 2223: 'I have a bonus weight of 12.',
 2300: 'You feed the Cogs on the left.',
 2301: "I'll feed the Cogs on the left.",
 2302: 'You feed the Cogs on the right.',
 2303: "I'll feed the Cogs on the right.",
 2304: 'You feed the Cogs in the front.',
 2305: "I'll feed the Cogs in the front.",
 2306: 'You feed the Cogs in the back.',
 2307: "I'll feed the Cogs in the back.",
 2308: 'You use the seltzer bottle.',
 2309: "I'll use the seltzer bottle.",
 2310: 'You use the golf tee.',
 2311: "I'll use the golf tee.",
 2312: "I'll serve this table.",
 2313: 'Can you serve this table?',
 2314: 'Feed the same cog again.',
 2315: 'Hurry, your cog is hungry!',
 2316: 'Please save the snacks for sadder toons.',
 2317: 'Take the snacks before they fall.',
 3010: 'Anyone want to race?',
 3020: "Let's race!",
 3030: 'Want to race?',
 3040: "Let's show off our karts!",
 3050: "I don't have enough tickets.",
 3060: "Let's race again!",
 3061: 'Want to race again?',
 3150: 'I need to go to the Kart Shop.',
 3160: "Let's go to the Race Tracks!",
 3170: "Let's go to Pit Row to show off our karts!",
 3180: "I'm going to Pit Row to show off my kart!",
 3190: 'Meet me at the Race Tracks!',
 3110: 'Meet up near the Kart Shop!',
 3130: 'Where should we meet?',
 3200: 'Where do you want to race?',
 3201: "Let's pick a different race.",
 3210: "Let's do a practice race.",
 3211: "Let's do a battle race.",
 3220: 'I like the Screwball Stadium race!',
 3221: 'I like the Rustic Raceway race!',
 3222: 'I like the City Circuit race!',
 3223: 'I like the Corkscrew Coliseum race!',
 3224: 'I like the Airborne Acres race!',
 3225: 'I like the Blizzard Boulevard race!',
 3230: "Let's race in the Screwball Stadium!",
 3231: "Let's race on the Rustic Raceway!",
 3232: "Let's race on the City Circuit!",
 3233: "Let's race in the Corkscrew Coliseum!",
 3234: "Let's race on the Airborne Acres!",
 3235: "Let's race on the Blizzard Boulevard!",
 3600: 'Which track do you want to race on?',
 3601: 'Pick a track!',
 3602: 'Can we race on a different track?',
 3603: "Let's pick a different track!",
 3640: 'I want to race on the first track!',
 3641: 'I want to race on the second track!',
 3642: 'I want to race on the third track!',
 3643: 'I want to race on the fourth track!',
 3660: "I don't want to race on the first track!",
 3661: "I don't want to race on the second track!",
 3662: "I don't want to race on the third track!",
 3663: "I don't want to race on the fourth track!",
 3300: 'Wow! You are FAST!',
 3301: "You're too fast for me!",
 3310: 'Good race!',
 3320: 'I really like your kart!',
 3330: 'Sweet ride!',
 3340: 'Your kart is cool!',
 3350: 'Your kart is awesome!',
 3360: 'Your kart is totally sweet!',
 3400: 'Too scared to race me?',
 3410: 'See you at the finish line!',
 3430: "I'm as fast as lightning!",
 3450: "You'll never catch me!",
 3451: "You'll never beat me!",
 3452: 'No one can beat my time!',
 3453: 'Hurry up slow pokes!',
 3460: 'Give me another shot!',
 3461: 'You got lucky!',
 3462: 'Ooooh! That was a close one!',
 3470: 'Wow, I thought you had me beat!',
 4000: "Let's play minigolf!",
 4001: "Let's play again!",
 4002: 'Want to golf?',
 4100: "Let's play 'Walk In The Par.'",
 4101: "Let's play 'Hole Some Fun.'",
 4102: "Let's play 'The Hole Kit and Caboodle.'",
 4103: 'That course is too easy.',
 4104: 'That course is too hard.',
 4105: 'That course is just right.',
 4200: 'Try standing more to the left.',
 4201: 'Try standing more to the right.',
 4202: 'Try standing right in the middle.',
 4203: 'Try hitting it harder.',
 4204: 'Try hitting it softer.',
 4205: 'Try aiming more to the left.',
 4206: 'Try aiming more to the right.',
 4207: 'Try aiming right down the middle.',
 4300: 'So close!',
 4301: 'What a great shot!',
 4302: 'That was a lucky shot.',
 4303: "I'll take a mulligan...",
 4304: "That's a gimme.",
 4305: 'Fore!',
 4306: 'Shhhh!',
 4307: 'Good game!',
 5000: "Let's form a Boarding Group.",
 5001: 'Join my Boarding Group.',
 5002: 'Can you invite me to your Boarding Group?',
 5003: "I'm already in a Boarding Group.",
 5004: 'Leave your Boarding Group.',
 5005: 'We are boarding now.',
 5006: 'Where are we going?',
 5007: 'Are we ready?',
 5008: "Let's Go!",
 5009: "Don't leave this area or you will leave the Boarding Group.",
 5100: "Let's go to the Front Three.",
 5101: "Let's go to the Middle Six.",
 5102: "Let's go to the Back Nine.",
 5103: "Let's go to the C.E.O. Battle.",
 5104: "Let's go to the Senior V.P Battle.",
 5105: "Let's go to the Front Entrance.",
 5106: "Let's go to the Side Entrance.",
 5107: "Let's go to the Coin Mint.",
 5108: "Let's go to the Dollar Mint.",
 5109: "Let's go to the Bullion Mint.",
 5110: "Let's go to the C.F.O. Battle.",
 5111: "Let's go to the Chief Justice Battle.",
 5112: "Let's go to the Lawbot A Office.",
 5113: "Let's go to the Lawbot B Office.",
 5114: "Let's go to the Lawbot C Office.",
 5115: "Let's go to the Lawbot D Office.",
 5200: "We're going to the Front Three.",
 5201: "We're going to the Middle Six.",
 5202: "We're going to the Back Nine.",
 5203: "We're going to the C.E.O. Battle.",
 5204: "We're going to the Senior V.P Battle.",
 5205: "We're going to the Front Entrance.",
 5206: "We're going to the Side Entrance.",
 5207: "We're going to the Coin Mint.",
 5208: "We're going to the Dollar Mint.",
 5209: "We're going to the Bullion Mint.",
 5210: "We're going to the C.F.O. Battle.",
 5211: "We're going to the Chief Justice Battle.",
 5212: "We're going to the Lawbot A Office.",
 5213: "We're going to the Lawbot B Office.",
 5214: "We're going to the Lawbot C Office.",
 5215: "We're going to the Lawbot D Office.",
 5300: "Let's go to a party.",
 5301: 'See you at the party!',
 5302: 'My party has started!',
 5303: 'Come to my party!',
 5304: 'Welcome to my party!',
 5305: 'This party rules!',
 5306: 'Your party is fun!',
 5307: "It's party time!",
 5308: 'Time is running out!',
 5309: 'No cogs allowed!',
 5310: 'I like this song!',
 5311: 'This music is great!',
 5312: 'Cannons are a blast!',
 5313: 'Watch me jump!',
 5314: 'Trampolines are fun!',
 5315: "Let's play Catch!",
 5316: "Let's dance!",
 5317: 'To the dance floor!',
 5318: "Let's play Tug of War!",
 5319: 'Start the fireworks!',
 5320: 'These fireworks are beautiful!',
 5321: 'Nice decorations.',
 5322: 'I wish I could eat this cake!',
 10000: 'The choice is yours!',
 10001: 'Who are you voting for?',
 10002: "I'm pickin' Chicken!",
 10003: 'Vote now! Vote Cow!',
 10004: 'Go bananas! Vote Monkey!',
 10005: 'Be a honey! Vote Bear!',
 10006: 'Think big! Vote Pig!',
 10007: "Vote Goat - and that's all she wrote!",
 20000: SuitBrushOffs[None][0],
 20001: SuitBrushOffs[None][1],
 20002: SuitBrushOffs[None][2],
 20003: SuitBrushOffs[None][3],
 20004: SuitBrushOffs[None][4],
 20005: SuitFaceoffTaunts['bf'][0],
 20006: SuitFaceoffTaunts['bf'][1],
 20007: SuitFaceoffTaunts['bf'][2],
 20008: SuitFaceoffTaunts['bf'][3],
 20009: SuitFaceoffTaunts['bf'][4],
 20010: SuitFaceoffTaunts['bf'][5],
 20011: SuitFaceoffTaunts['bf'][6],
 20012: SuitFaceoffTaunts['bf'][7],
 20013: SuitFaceoffTaunts['bf'][8],
 20014: SuitFaceoffTaunts['bf'][9],
 20015: SuitFaceoffTaunts['nc'][0],
 20016: SuitFaceoffTaunts['nc'][1],
 20017: SuitFaceoffTaunts['nc'][2],
 20018: SuitFaceoffTaunts['nc'][3],
 20019: SuitFaceoffTaunts['nc'][4],
 20020: SuitFaceoffTaunts['nc'][5],
 20021: SuitFaceoffTaunts['nc'][6],
 20022: SuitFaceoffTaunts['nc'][7],
 20023: SuitFaceoffTaunts['nc'][8],
 20024: SuitFaceoffTaunts['nc'][9],
 20025: SuitFaceoffTaunts['ym'][0],
 20026: SuitFaceoffTaunts['ym'][1],
 20027: SuitFaceoffTaunts['ym'][2],
 20028: SuitFaceoffTaunts['ym'][3],
 20029: SuitFaceoffTaunts['ym'][4],
 20030: SuitFaceoffTaunts['ym'][5],
 20031: SuitFaceoffTaunts['ym'][6],
 20032: SuitFaceoffTaunts['ym'][7],
 20033: SuitFaceoffTaunts['ym'][8],
 20034: SuitFaceoffTaunts['ym'][9],
 20035: SuitFaceoffTaunts['ym'][10],
 20036: SuitFaceoffTaunts['ms'][0],
 20037: SuitFaceoffTaunts['ms'][1],
 20038: SuitFaceoffTaunts['ms'][2],
 20039: SuitFaceoffTaunts['ms'][3],
 20040: SuitFaceoffTaunts['ms'][4],
 20041: SuitFaceoffTaunts['ms'][5],
 20042: SuitFaceoffTaunts['ms'][6],
 20043: SuitFaceoffTaunts['ms'][7],
 20044: SuitFaceoffTaunts['ms'][8],
 20045: SuitFaceoffTaunts['ms'][9],
 20046: SuitFaceoffTaunts['ms'][10],
 20047: SuitFaceoffTaunts['bc'][0],
 20048: SuitFaceoffTaunts['bc'][1],
 20049: SuitFaceoffTaunts['bc'][2],
 20050: SuitFaceoffTaunts['bc'][3],
 20051: SuitFaceoffTaunts['bc'][4],
 20052: SuitFaceoffTaunts['bc'][5],
 20053: SuitFaceoffTaunts['bc'][6],
 20054: SuitFaceoffTaunts['bc'][7],
 20055: SuitFaceoffTaunts['bc'][8],
 20056: SuitFaceoffTaunts['bc'][9],
 20057: SuitFaceoffTaunts['bc'][10],
 20058: SuitFaceoffTaunts['cc'][0],
 20059: SuitFaceoffTaunts['cc'][1],
 20060: SuitFaceoffTaunts['cc'][2],
 20061: SuitFaceoffTaunts['cc'][3],
 20062: SuitFaceoffTaunts['cc'][4],
 20063: SuitFaceoffTaunts['cc'][5],
 20064: SuitFaceoffTaunts['cc'][6],
 20065: SuitFaceoffTaunts['cc'][7],
 20066: SuitFaceoffTaunts['cc'][8],
 20067: SuitFaceoffTaunts['cc'][9],
 20068: SuitFaceoffTaunts['cc'][10],
 20069: SuitFaceoffTaunts['cc'][11],
 20070: SuitFaceoffTaunts['cc'][12],
 20071: SuitFaceoffTaunts['nd'][0],
 20072: SuitFaceoffTaunts['nd'][1],
 20073: SuitFaceoffTaunts['nd'][2],
 20074: SuitFaceoffTaunts['nd'][3],
 20075: SuitFaceoffTaunts['nd'][4],
 20076: SuitFaceoffTaunts['nd'][5],
 20077: SuitFaceoffTaunts['nd'][6],
 20078: SuitFaceoffTaunts['nd'][7],
 20079: SuitFaceoffTaunts['nd'][8],
 20080: SuitFaceoffTaunts['nd'][9],
 20081: SuitFaceoffTaunts['ac'][0],
 20082: SuitFaceoffTaunts['ac'][1],
 20083: SuitFaceoffTaunts['ac'][2],
 20084: SuitFaceoffTaunts['ac'][3],
 20085: SuitFaceoffTaunts['ac'][4],
 20086: SuitFaceoffTaunts['ac'][5],
 20087: SuitFaceoffTaunts['ac'][6],
 20088: SuitFaceoffTaunts['ac'][7],
 20089: SuitFaceoffTaunts['ac'][8],
 20090: SuitFaceoffTaunts['ac'][9],
 20091: SuitFaceoffTaunts['ac'][10],
 20092: SuitFaceoffTaunts['ac'][11],
 20093: SuitFaceoffTaunts['tf'][0],
 20094: SuitFaceoffTaunts['tf'][1],
 20095: SuitFaceoffTaunts['tf'][2],
 20096: SuitFaceoffTaunts['tf'][3],
 20097: SuitFaceoffTaunts['tf'][4],
 20098: SuitFaceoffTaunts['tf'][5],
 20099: SuitFaceoffTaunts['tf'][6],
 20100: SuitFaceoffTaunts['tf'][7],
 20101: SuitFaceoffTaunts['tf'][8],
 20102: SuitFaceoffTaunts['tf'][9],
 20103: SuitFaceoffTaunts['tf'][10],
 20104: SuitFaceoffTaunts['hh'][0],
 20105: SuitFaceoffTaunts['hh'][1],
 20106: SuitFaceoffTaunts['hh'][2],
 20107: SuitFaceoffTaunts['hh'][3],
 20108: SuitFaceoffTaunts['hh'][4],
 20109: SuitFaceoffTaunts['hh'][5],
 20110: SuitFaceoffTaunts['hh'][6],
 20111: SuitFaceoffTaunts['hh'][7],
 20112: SuitFaceoffTaunts['hh'][8],
 20113: SuitFaceoffTaunts['hh'][9],
 20114: SuitFaceoffTaunts['hh'][10],
 20115: SuitFaceoffTaunts['le'][0],
 20116: SuitFaceoffTaunts['le'][1],
 20117: SuitFaceoffTaunts['le'][2],
 20118: SuitFaceoffTaunts['le'][3],
 20119: SuitFaceoffTaunts['le'][4],
 20120: SuitFaceoffTaunts['le'][5],
 20121: SuitFaceoffTaunts['le'][6],
 20122: SuitFaceoffTaunts['le'][7],
 20123: SuitFaceoffTaunts['le'][8],
 20124: SuitFaceoffTaunts['le'][9],
 20125: SuitFaceoffTaunts['bs'][0],
 20126: SuitFaceoffTaunts['bs'][1],
 20127: SuitFaceoffTaunts['bs'][2],
 20128: SuitFaceoffTaunts['bs'][3],
 20129: SuitFaceoffTaunts['bs'][4],
 20130: SuitFaceoffTaunts['bs'][5],
 20131: SuitFaceoffTaunts['bs'][6],
 20132: SuitFaceoffTaunts['bs'][7],
 20133: SuitFaceoffTaunts['bs'][8],
 20134: SuitFaceoffTaunts['bs'][9],
 20135: SuitFaceoffTaunts['bs'][10],
 20136: SuitFaceoffTaunts['cr'][0],
 20137: SuitFaceoffTaunts['cr'][1],
 20138: SuitFaceoffTaunts['cr'][2],
 20139: SuitFaceoffTaunts['cr'][3],
 20140: SuitFaceoffTaunts['cr'][4],
 20141: SuitFaceoffTaunts['cr'][5],
 20142: SuitFaceoffTaunts['cr'][6],
 20143: SuitFaceoffTaunts['cr'][7],
 20144: SuitFaceoffTaunts['cr'][8],
 20145: SuitFaceoffTaunts['cr'][9],
 20146: SuitFaceoffTaunts['tbc'][0],
 20147: SuitFaceoffTaunts['tbc'][1],
 20148: SuitFaceoffTaunts['tbc'][2],
 20149: SuitFaceoffTaunts['tbc'][3],
 20150: SuitFaceoffTaunts['tbc'][4],
 20151: SuitFaceoffTaunts['tbc'][5],
 20152: SuitFaceoffTaunts['tbc'][6],
 20153: SuitFaceoffTaunts['tbc'][7],
 20154: SuitFaceoffTaunts['tbc'][8],
 20155: SuitFaceoffTaunts['tbc'][9],
 20156: SuitFaceoffTaunts['tbc'][10],
 20157: SuitFaceoffTaunts['ds'][0],
 20158: SuitFaceoffTaunts['ds'][1],
 20159: SuitFaceoffTaunts['ds'][2],
 20160: SuitFaceoffTaunts['ds'][3],
 20161: SuitFaceoffTaunts['ds'][4],
 20162: SuitFaceoffTaunts['ds'][5],
 20163: SuitFaceoffTaunts['ds'][6],
 20164: SuitFaceoffTaunts['ds'][7],
 20165: SuitFaceoffTaunts['gh'][0],
 20166: SuitFaceoffTaunts['gh'][1],
 20167: SuitFaceoffTaunts['gh'][2],
 20168: SuitFaceoffTaunts['gh'][3],
 20169: SuitFaceoffTaunts['gh'][4],
 20170: SuitFaceoffTaunts['gh'][5],
 20171: SuitFaceoffTaunts['gh'][6],
 20172: SuitFaceoffTaunts['gh'][7],
 20173: SuitFaceoffTaunts['gh'][8],
 20174: SuitFaceoffTaunts['gh'][9],
 20175: SuitFaceoffTaunts['gh'][10],
 20176: SuitFaceoffTaunts['gh'][11],
 20177: SuitFaceoffTaunts['gh'][12],
 20178: SuitFaceoffTaunts['pp'][0],
 20179: SuitFaceoffTaunts['pp'][1],
 20180: SuitFaceoffTaunts['pp'][2],
 20181: SuitFaceoffTaunts['pp'][3],
 20182: SuitFaceoffTaunts['pp'][4],
 20183: SuitFaceoffTaunts['pp'][5],
 20184: SuitFaceoffTaunts['pp'][6],
 20185: SuitFaceoffTaunts['pp'][7],
 20186: SuitFaceoffTaunts['pp'][8],
 20187: SuitFaceoffTaunts['pp'][9],
 20188: SuitFaceoffTaunts['b'][0],
 20189: SuitFaceoffTaunts['b'][1],
 20190: SuitFaceoffTaunts['b'][2],
 20191: SuitFaceoffTaunts['b'][3],
 20192: SuitFaceoffTaunts['b'][4],
 20193: SuitFaceoffTaunts['b'][5],
 20194: SuitFaceoffTaunts['b'][6],
 20195: SuitFaceoffTaunts['b'][7],
 20196: SuitFaceoffTaunts['b'][8],
 20197: SuitFaceoffTaunts['b'][9],
 20198: SuitFaceoffTaunts['b'][10],
 20199: SuitFaceoffTaunts['b'][11],
 20200: SuitFaceoffTaunts['f'][0],
 20201: SuitFaceoffTaunts['f'][1],
 20202: SuitFaceoffTaunts['f'][2],
 20203: SuitFaceoffTaunts['f'][3],
 20204: SuitFaceoffTaunts['f'][4],
 20205: SuitFaceoffTaunts['f'][5],
 20206: SuitFaceoffTaunts['f'][6],
 20207: SuitFaceoffTaunts['f'][7],
 20208: SuitFaceoffTaunts['f'][8],
 20209: SuitFaceoffTaunts['f'][9],
 20210: SuitFaceoffTaunts['f'][10],
 20211: SuitFaceoffTaunts['mm'][0],
 20212: SuitFaceoffTaunts['mm'][1],
 20213: SuitFaceoffTaunts['mm'][2],
 20214: SuitFaceoffTaunts['mm'][3],
 20215: SuitFaceoffTaunts['mm'][4],
 20216: SuitFaceoffTaunts['mm'][5],
 20217: SuitFaceoffTaunts['mm'][6],
 20218: SuitFaceoffTaunts['mm'][7],
 20219: SuitFaceoffTaunts['mm'][8],
 20220: SuitFaceoffTaunts['mm'][9],
 20221: SuitFaceoffTaunts['mm'][10],
 20222: SuitFaceoffTaunts['mm'][11],
 20223: SuitFaceoffTaunts['mm'][12],
 20224: SuitFaceoffTaunts['mm'][13],
 20225: SuitFaceoffTaunts['tw'][0],
 20226: SuitFaceoffTaunts['tw'][1],
 20227: SuitFaceoffTaunts['tw'][2],
 20228: SuitFaceoffTaunts['tw'][3],
 20229: SuitFaceoffTaunts['tw'][4],
 20230: SuitFaceoffTaunts['tw'][5],
 20231: SuitFaceoffTaunts['tw'][6],
 20232: SuitFaceoffTaunts['tw'][7],
 20233: SuitFaceoffTaunts['tw'][8],
 20234: SuitFaceoffTaunts['tw'][9],
 20235: SuitFaceoffTaunts['tw'][10],
 20236: SuitFaceoffTaunts['mb'][0],
 20237: SuitFaceoffTaunts['mb'][1],
 20238: SuitFaceoffTaunts['mb'][2],
 20239: SuitFaceoffTaunts['mb'][3],
 20240: SuitFaceoffTaunts['mb'][4],
 20241: SuitFaceoffTaunts['mb'][5],
 20242: SuitFaceoffTaunts['mb'][6],
 20243: SuitFaceoffTaunts['mb'][7],
 20244: SuitFaceoffTaunts['mb'][8],
 20245: SuitFaceoffTaunts['mb'][9],
 20246: SuitFaceoffTaunts['m'][0],
 20247: SuitFaceoffTaunts['m'][1],
 20248: SuitFaceoffTaunts['m'][2],
 20249: SuitFaceoffTaunts['m'][3],
 20250: SuitFaceoffTaunts['m'][4],
 20251: SuitFaceoffTaunts['m'][5],
 20252: SuitFaceoffTaunts['m'][6],
 20253: SuitFaceoffTaunts['m'][7],
 20254: SuitFaceoffTaunts['m'][8],
 20255: SuitFaceoffTaunts['mh'][0],
 20256: SuitFaceoffTaunts['mh'][1],
 20257: SuitFaceoffTaunts['mh'][2],
 20258: SuitFaceoffTaunts['mh'][3],
 20259: SuitFaceoffTaunts['mh'][4],
 20260: SuitFaceoffTaunts['mh'][5],
 20261: SuitFaceoffTaunts['mh'][6],
 20262: SuitFaceoffTaunts['mh'][7],
 20263: SuitFaceoffTaunts['mh'][8],
 20264: SuitFaceoffTaunts['mh'][9],
 20265: SuitFaceoffTaunts['mh'][10],
 20266: SuitFaceoffTaunts['mh'][11],
 20267: SuitFaceoffTaunts['dt'][0],
 20268: SuitFaceoffTaunts['dt'][1],
 20269: SuitFaceoffTaunts['dt'][2],
 20270: SuitFaceoffTaunts['dt'][3],
 20271: SuitFaceoffTaunts['dt'][4],
 20272: SuitFaceoffTaunts['dt'][5],
 20273: SuitFaceoffTaunts['dt'][6],
 20274: SuitFaceoffTaunts['dt'][7],
 20275: SuitFaceoffTaunts['dt'][8],
 20276: SuitFaceoffTaunts['dt'][9],
 20277: SuitFaceoffTaunts['p'][0],
 20278: SuitFaceoffTaunts['p'][1],
 20279: SuitFaceoffTaunts['p'][2],
 20280: SuitFaceoffTaunts['p'][3],
 20281: SuitFaceoffTaunts['p'][4],
 20282: SuitFaceoffTaunts['p'][5],
 20283: SuitFaceoffTaunts['p'][6],
 20284: SuitFaceoffTaunts['p'][7],
 20285: SuitFaceoffTaunts['p'][8],
 20286: SuitFaceoffTaunts['p'][9],
 20287: SuitFaceoffTaunts['p'][10],
 20288: SuitFaceoffTaunts['tm'][0],
 20289: SuitFaceoffTaunts['tm'][1],
 20290: SuitFaceoffTaunts['tm'][2],
 20291: SuitFaceoffTaunts['tm'][3],
 20292: SuitFaceoffTaunts['tm'][4],
 20293: SuitFaceoffTaunts['tm'][5],
 20294: SuitFaceoffTaunts['tm'][6],
 20295: SuitFaceoffTaunts['tm'][7],
 20296: SuitFaceoffTaunts['tm'][8],
 20297: SuitFaceoffTaunts['tm'][9],
 20298: SuitFaceoffTaunts['tm'][10],
 20299: SuitFaceoffTaunts['bw'][0],
 20300: SuitFaceoffTaunts['bw'][1],
 20301: SuitFaceoffTaunts['bw'][2],
 20302: SuitFaceoffTaunts['bw'][3],
 20303: SuitFaceoffTaunts['bw'][4],
 20304: SuitFaceoffTaunts['bw'][5],
 20305: SuitFaceoffTaunts['bw'][6],
 20306: SuitFaceoffTaunts['bw'][7],
 20307: SuitFaceoffTaunts['bw'][8],
 20308: SuitFaceoffTaunts['bw'][9],
 20309: SuitFaceoffTaunts['ls'][0],
 20310: SuitFaceoffTaunts['ls'][1],
 20311: SuitFaceoffTaunts['ls'][2],
 20312: SuitFaceoffTaunts['ls'][3],
 20313: SuitFaceoffTaunts['ls'][4],
 20314: SuitFaceoffTaunts['ls'][5],
 20315: SuitFaceoffTaunts['ls'][6],
 20316: SuitFaceoffTaunts['ls'][7],
 20317: SuitFaceoffTaunts['ls'][8],
 20318: SuitFaceoffTaunts['ls'][9],
 20319: SuitFaceoffTaunts['ls'][10],
 20320: SuitFaceoffTaunts['rb'][0],
 20321: SuitFaceoffTaunts['rb'][1],
 20322: SuitFaceoffTaunts['rb'][2],
 20323: SuitFaceoffTaunts['rb'][3],
 20324: SuitFaceoffTaunts['rb'][4],
 20325: SuitFaceoffTaunts['rb'][5],
 20326: SuitFaceoffTaunts['rb'][6],
 20327: SuitFaceoffTaunts['rb'][7],
 20328: SuitFaceoffTaunts['rb'][8],
 20329: SuitFaceoffTaunts['rb'][9],
 20330: SuitFaceoffTaunts['sc'][0],
 20331: SuitFaceoffTaunts['sc'][1],
 20332: SuitFaceoffTaunts['sc'][2],
 20333: SuitFaceoffTaunts['sc'][3],
 20334: SuitFaceoffTaunts['sc'][4],
 20335: SuitFaceoffTaunts['sc'][5],
 20336: SuitFaceoffTaunts['sc'][6],
 20337: SuitFaceoffTaunts['sc'][7],
 20338: SuitFaceoffTaunts['sc'][8],
 20339: SuitFaceoffTaunts['sc'][9],
 20340: SuitFaceoffTaunts['sc'][10],
 20341: SuitFaceoffTaunts['sd'][0],
 20342: SuitFaceoffTaunts['sd'][1],
 20343: SuitFaceoffTaunts['sd'][2],
 20344: SuitFaceoffTaunts['sd'][3],
 20345: SuitFaceoffTaunts['sd'][4],
 20346: SuitFaceoffTaunts['sd'][5],
 20347: SuitFaceoffTaunts['sd'][6],
 20348: SuitFaceoffTaunts['sd'][7],
 20349: SuitFaceoffTaunts['sd'][8],
 20350: SuitFaceoffTaunts['sd'][9],
 21000: 'Here boy!',
 21001: 'Here girl!',
 21002: 'Stay.',
 21003: 'Good boy!',
 21004: 'Good girl!',
 21005: 'Nice Doodle.',
 21006: "Please don't bother me.",
 21200: 'Jump!',
 21201: 'Beg!',
 21202: 'Play dead!',
 21203: 'Rollover!',
 21204: 'Backflip!',
 21205: 'Dance!',
 21206: 'Speak!',
 30100: "Happy April Toons' Week!",
 30101: "Welcome to my April Toons' Week party!",
 30102: 'The Silly Meter is back in Toon Hall!',
 30110: 'Mickey is in Daisy Gardens.',
 30111: 'Daisy is in Toontown Central.',
 30112: 'Minnie is in The Brrrgh.',
 30113: 'Pluto is in Melodyland.',
 30114: 'Donald is sleepwalking at the Speedway.',
 30115: 'Goofy is in Dreamland.',
 30120: 'Mickey is acting like Daisy!',
 30121: 'Daisy is acting like Mickey!',
 30122: 'Minnie is acting like Pluto!',
 30123: 'Pluto is acting like Minnie!',
 30124: 'Pluto is talking!',
 30125: 'Goofy is acting like Donald!',
 30126: 'Donald is dreaming he is Goofy!',
 30130: 'Watch how far I can jump.',
 30131: 'Wow, you jumped really far!',
 30132: 'Hey, Doodles can talk!',
 30133: 'Did your Doodle just talk?',
 30140: 'Things sure are silly around here!',
 30141: 'How sillier could things get?',
 30150: 'Operation: Storm Sellbot is here!',
 30151: 'Sellbot Towers had its power drained by Doodles!',
 30152: 'The VP had his power drained by Doodles!',
 30153: 'Everyone can fight the VP right now!',
 30154: "You don't need a Sellbot Disguise to fight the VP!",
 30155: 'You get a Rental Suit when you go into Sellbot Towers.',
 30156: 'Do you like my Rental Suit? Sorry about the safety pins!',
 30157: "It's best to have eight Toons to fight the VP.",
 30158: 'Will you help me fight the VP?',
 30159: 'Do you want to fight the VP with me?',
 30160: 'Would you like to join my Sellbot VP group?',
 30161: 'I am looking for a Toon with a Rental Suit to fight the VP.',
 30162: 'I have a Rental Suit, and am looking to fight the VP.',
 30163: 'Just walk through the doors to get your Rental Suit.',
 30164: 'Save your gags for the Cogs inside!',
 30165: 'We have to defeat these Cogs first!',
 30166: 'Bump the barrels to gag up.',
 30167: 'Bump the barrel to get a Toon-up.',
 30168: 'Now we have to fight some Skelecogs!',
 30169: "Jump up and touch the Toon's cage for pies!",
 30170: 'Now we fight the VP!',
 30171: 'Aim your pies by pressing the Delete button.',
 30172: "Two Toons should throw pies through the VP's open doors!",
 30173: "I'll stun the VP from the front.",
 30174: "I'll stun the VP from the back.",
 30175: 'Jump when the VP jumps!',
 30180: 'I got double jellybeans on the Trolley!',
 30181: 'I got double jellybeans from fishing!',
 30182: 'I got double jellybeans at a party!',
 30183: 'Jellybeans jellybeans jellybeans!',
 30184: "I'm really keen to earn a bean!",
 30185: "Don't be smelly, get beans of jelly!",
 30186: "I'm gonna adopt a Doodle with all these jellybeans!",
 30187: 'What am I gonna spend all these jellybeans on?',
 30188: "I'm gonna throw a huge party!",
 30189: "I'm gonna decorate my whole Estate!",
 30190: "I'm gonna buy a whole new wardrobe!",
 30191: 'Jellybeans, please!',
 30192: "Don't be mean, give a bean!",
 30193: 'Who wants jellybeans?',
 30194: 'Dance for jellybeans!',
 30200: 'Deck the halls... ',
 30201: 'Load some pies...',
 30202: 'Joyful toons...',
 30203: 'Snowman heads...',
 30204: "Toontown's merry...",
 30205: 'Lure good cheer...',
 30220: 'Deck the halls with seltzer spray!\nHappy Winter Holiday!',
 30221: 'Load some pies into your sleigh!\nHappy Winter Holiday!',
 30222: 'Joyful toons bring Cogs dismay!\nHappy Winter Holiday!',
 30223: 'Snowman heads are hot today!\nHappy Winter Holiday!',
 30224: "Toontown's merry, come what may!\nHappy Winter Holiday!",
 30225: 'Lure good cheer the Toontown way!\nHappy Winter Holiday!',
 30250: 'Boo!',
 30251: 'Happy Halloween!',
 30252: 'Spooky!',
 30275: 'Happy holidays!',
 30276: "Season's greetings!",
 30277: 'Have a Wonderful Winter!',
 30301: 'Have you seen the Silly Meter?',
 30302: 'The Silly Meter is in Toon Hall.',
 30303: 'Things sure are getting silly around here!',
 30304: 'I saw a fire hydrant moving!',
 30305: 'Toontown is coming to life!',
 30306: "Have you been to Flippy's new office?",
 30307: 'I caused a Silly Surge in battle!',
 30308: "Let's defeat some Cogs to make Toontown sillier!",
 30309: 'The Silly Meter is bigger and crazier than ever!',
 30310: 'Lots of hydrants have come alive!',
 30311: 'I saw a mail box moving!',
 30312: 'I watched a trash can wake up!',
 30313: 'How silly can it get?',
 30314: "What's going to happen next?",
 30315: 'Something silly, I bet!',
 30316: 'Have you caused a Silly Surge yet?',
 30317: "Let's defeat some Cogs to make Toontown sillier!",
 30318: 'Cog Invasion!',
 30319: 'Incoming!',
 30320: "Let's stop those Cogs!",
 30321: 'I miss the Silly Surges!',
 30322: "Let's go stop an Invasion!",
 30323: 'Toontown is sillier than ever now!',
 30324: 'Have you seen something come alive?',
 30325: 'My favorites are the fire hydrants!',
 30326: 'My favorites are the mailboxes!',
 30327: 'My favorites are the trash cans!',
 30328: 'Hooray! We stopped the Cog invasions!',
 30329: 'A hydrant helped me in battle!',
 30330: 'A hydrant boosted my Squirt Gags!',
 30331: 'A trash can boosted my Toon-Up Gags!',
 30332: 'A mailbox helped my Throw Gags!',
 30350: 'Welcome to my Victory Party!',
 30351: 'This is a great Victory Party!',
 30352: "We showed those Cogs who's boss!",
 30353: 'Good job helping end the Cog invasions!',
 30354: 'I bet this is driving the Cogs crazy!',
 30355: "Let's play Cog-O-War!",
 30356: 'My team won at Cog-O-War!',
 30357: "It's nice to have fire hydrants, trash cans, and mailboxes here!",
 30358: 'I like the balloon of the Doodle biting the Cog!',
 30359: 'I like the balloon of the Cog covered in ice cream!',
 30360: 'I like the wavy Cog that flaps his arms!',
 30361: "I jumped on a Cog's face!",
 30400: 'The Sellbots are invading!',
 30401: 'The V.P. was hopping mad about Operation: Storm Sellbot ...',
 30402: "He's sending the Sellbots in to invade Toontown!",
 30403: "Let's go fight some Sellbots!",
 30404: "There's a new kind of building in Toontown!",
 30405: 'Have you seen the Mover & Shaker Field Offices?',
 30406: 'The V.P. created them as a reward for the Movers & Shakers.',
 30407: "Let's go defeat a Field Office!",
 30408: 'I got an SOS Card for defeating a Field Office!',
 30409: 'Clear the map by exploring the maze.',
 30410: 'Destroy the Cogs by hitting them with water balloons!',
 30411: 'Movers & Shakers take two balloons to destroy.',
 30412: 'Look out for falling objects!',
 30413: 'Watch out for the Cogs!',
 30414: 'Collect Jokes to get a Toon-up at the end!',
 30415: 'When the room shakes, a Mover & Shaker is nearby.',
 30416: 'Defeat all four Movers & Shakers to open the exit!',
 30417: 'The exit is open!',
 30418: "It's the Boss!",
 30450: "It's easy to be green!",
 30451: 'Visit Green Bean Jeans and you can be green too!',
 30452: "It's on Oak Street in Daisy Gardens."}
SpeedChatStaticTextPirates = {50001: 'Aye',
 50002: 'Nay',
 50003: 'Yes',
 50004: 'No',
 50005: 'Ok',
 50100: 'Gangway!',
 50101: 'Blimey!',
 50102: 'Well blow me down!',
 50103: 'Walk the plank!',
 50104: 'Dead men tell no tales....',
 50105: 'Shiver me timbers!',
 50106: "Salty as a Kraken's kiss.",
 50107: 'Treasure be the measure of our pleasure!',
 50108: "I don't fear death - I attune it.",
 50700: 'Ahoy!',
 50701: 'Ahoy, mate!',
 50702: 'Yo-Ho-Ho',
 50703: 'Avast!',
 50704: 'Hey Bucko.',
 50800: 'Until next time.',
 50801: 'May fair winds find ye.',
 50802: 'Godspeed.',
 50900: 'How are ye, mate?',
 50901: '',
 51000: "It's like the sky is raining gold doubloons!",
 51001: 'May a stiff wind be at our backs, the sun on our faces and our cannons fire true!',
 51100: 'I be sailing some rough waters today.',
 51200: 'Me apologies, mate.',
 51201: 'Sorry.',
 51202: 'Sorry, I was busy before.',
 51203: 'Sorry, I already have plans.',
 51204: "Sorry, I don't need to do that.",
 51300: 'Attack the weakest one!',
 51301: 'Attack the strongest one!',
 51302: 'Attack me target!',
 51303: 'I be needing help!',
 51304: "I can't do any damage!",
 51305: 'I think we be in trouble.',
 51306: 'Surround the most powerful one.',
 51307: 'We should retreat.',
 51308: 'Run for it!',
 51400: 'Fire a Broadside!',
 51401: 'Port Side! (left)',
 51402: 'Starboard Side! (right)',
 51403: 'Incoming!',
 51404: 'Come about!',
 51405: 'Broadside! Take Cover!',
 51406: 'To the Cannons!',
 51407: 'Open fire!',
 51408: 'Hold yer fire!',
 51409: 'Aim for the masts!',
 51410: 'Aim for the hull!',
 51411: 'Prepare to board!',
 51412: "She's coming about.",
 51413: 'Ramming speed!',
 51414: "We've got her on the run.",
 51415: 'We be taking on water!',
 51416: "We can't take anymore!",
 51417: "I don't have a shot!",
 51418: "Let's find port for repair.",
 51419: 'Man overboard!',
 51420: 'Enemy spotted.',
 51421: 'Handsomely now, mates!',
 50400: "Let's set sail.",
 50401: "Let's get out of here.",
 51500: "Let's sail to Port Royal.",
 51501: "Let's sail to Tortuga.",
 51502: "Let's sail to Padres Del Fuego.",
 51503: "Let's sail to Devil's Anvil.",
 51504: "Let's sail to Kingshead.",
 51505: "Let's sail to Isla Perdida.",
 51506: "Let's sail to Cuba.",
 51507: "Let's sail to Tormenta.",
 51508: "Let's sail to Outcast Isle.",
 51509: "Let's sail to Driftwood.",
 51510: "Let's sail to Cutthroat.",
 51511: "Let's sail to Rumrunner's Isle.",
 51512: "Let's sail to Isla Cangrejos.",
 51600: "Let's head into town.",
 51601: "Let's go to the docks.",
 51602: "Let's head to the tavern.",
 51800: "Let's go to Fort Charles.",
 51801: "Let's go to the Governor's Mansion.",
 52500: 'Where be I, mate?',
 51700: 'Yer already there.',
 51701: "I don't know.",
 51702: 'Yer on the wrong island.',
 51703: "That's in town.",
 51704: 'Look just outside of town.',
 51705: 'Ye will have to search through the jungle.',
 51706: 'Deeper inland.',
 51707: 'Oh, that be by the coast.',
 50200: 'Bilge rat!',
 50201: 'Scurvy dog!',
 50202: 'See ye in Davy Jones locker!',
 50203: 'Scoundrel!',
 50204: 'Landlubber!',
 50205: 'Addle-minded fool!',
 50206: 'You need a sharp sword and sharper wits.',
 50207: 'Ye be one doubloon short of a full hull mate!',
 50208: "Watch yer tongue or I'll pickle it with sea salt!",
 50209: 'Touch me loot and you get the boot!',
 50210: 'The horizon be as empty as yer head.',
 50211: "You're a canvas shy of a full sail, aren't ye mate?",
 50300: 'Fine shooting mate!',
 50301: 'A well placed blow!',
 50302: 'Nice shot!',
 50303: 'Well met!',
 50304: 'We showed them!',
 50305: 'Yer not so bad yerself!',
 50306: 'A fine plunder haul!',
 52400: 'May luck be my lady.',
 52401: 'I think these cards be marked!',
 52402: 'Blimey cheater!',
 51900: "That's a terrible flop!",
 51901: 'Trying to buy the hand, are ye?',
 51902: 'Ye be bluffing.',
 51903: "I don't think ye had it.",
 51904: 'Saved by the river.',
 52600: 'Hit me.',
 52601: 'Can I get another dealer?',
 53101: 'I caught a fish!',
 53102: 'I saw a Legendary Fish!',
 53103: 'What did you catch?',
 53104: 'This will make a whale of a tale!',
 53105: 'That was a beauty!',
 53106: 'Arr, the sea is treacherous today.',
 53107: 'What a bountiful haul of fish!',
 53110: 'Do you have the Legendary Lure?',
 53111: 'Have you ever caught a Legendary Fish?',
 53112: 'Can you sail on a fishing boat?',
 53113: 'Where is the Fishing Master?',
 53114: 'Have you completed your fish collection?',
 53120: 'Fire at my target!',
 53121: 'Fire at the ship closest to the shore!',
 53122: "There's a ship getting away!",
 53123: 'Fire at the big ships!',
 53124: 'Fire at the small ships!',
 53125: 'More are coming!',
 53126: "We're not going to last much longer!",
 53127: 'Shoot the barrels!',
 53128: "We've got new ammo!",
 53129: 'Sturdy defense, mates!',
 53141: 'Look at the potion I made!',
 53142: 'Have you completed your potion collection?',
 53143: 'Where is the Gypsy?',
 53144: 'What potion is that?',
 53145: 'This potion was easy enough.',
 53146: "This potion was hard brewin', I tell ye!",
 53160: 'We need someone to bilge pump!',
 53161: 'We need someone to scrub!',
 53162: 'We need someone to saw!',
 53163: 'We need someone to brace!',
 53164: 'We need someone to hammer!',
 53165: 'We need someone to patch!',
 53166: "I'll do it!",
 53167: "Keep it up, this ship won't repair itself!",
 53168: 'Great job repairing the ship!',
 52100: 'Want to group up?',
 52101: 'Join me crew?',
 52200: 'Fight some skeletons?',
 52201: 'Fight some crabs?',
 52300: "How 'bout a game of Mayhem?",
 52301: 'Join me Mayhem game.',
 52302: 'Want to start a Mayhem game?',
 52303: 'Want to start a team battle game?',
 52304: 'Join me team battle game.',
 52350: 'Join my Cannon Defense.',
 52351: 'Want to start a Cannon Defense?',
 52352: 'Can you lend me a hand with Repair?',
 52353: 'We need to Repair the ship now!',
 52354: 'Care to catch some fish?',
 52355: 'Want to go fishing with me?',
 52356: "Join me crew for some fishin'?",
 52357: 'Time to brew some potions!',
 52358: 'You should try your hand at brewing potions.',
 52000: '',
 52000: '',
 52700: '',
 53000: '',
 52800: '',
 52900: '',
 50500: '',
 50600: '',
 60100: 'Hi!',
 60101: 'Hello!',
 60102: 'Hey!',
 60103: 'Yo!',
 60104: 'Hi everybody!',
 60105: 'How are you doing?',
 60106: "What's Up?",
 60200: 'Bye!',
 60201: 'Later!',
 60202: 'See ya!',
 60203: "I'll be right back.",
 60204: 'I need to go.',
 60300: ':-)',
 60301: 'Cool!',
 60302: 'Yeah!',
 60303: 'Ha ha!',
 60304: 'Sweet!',
 60305: 'Yeah!',
 60306: 'That rocks!',
 60307: 'Funky!',
 60308: 'Awesome!',
 60309: 'Wow!',
 60400: ':-(',
 60401: 'Doh!',
 60402: 'Aw man!',
 60403: 'Ouch!',
 60404: 'Bummer!',
 60500: 'Where are you?',
 60501: "Let's go to the Gateway Store.",
 60502: "Let's go to the Disco Hall.",
 60503: "Let's go to Toontown.",
 60504: "Let's go to Pirates of the Carribean.",
 60505: 'Flip coin',
 60506: 'Dance',
 60507: 'Chant 1',
 60508: 'Chant 2',
 60509: 'Dance a jig',
 60510: 'Sleep',
 60511: 'Flex',
 60512: 'Play Lute',
 60513: 'Play Flute',
 60514: 'Frustrated',
 60515: 'Searching',
 60516: 'Yawn',
 60517: 'Kneel',
 60518: 'Sweep',
 60519: 'Primp',
 60520: 'Yawn',
 60521: 'Dance',
 60522: 'No',
 60523: 'Yes',
 60524: 'Laugh',
 60525: 'Clap',
 60526: 'Smile',
 60527: 'Anger',
 60528: 'Fear',
 60529: 'Sad',
 60530: 'Celebrate',
 60668: 'Celebrate',
 60669: 'Sleep',
 60602: 'Angry',
 60614: 'Clap',
 60622: 'Scared',
 60640: 'Laugh',
 60652: 'Sad',
 60657: 'Smile',
 60664: 'Wave',
 60665: 'Wink',
 60666: 'Yawn',
 60669: 'Sleep',
 60670: 'Dance',
 60676: 'Flirt',
 60677: 'Zombie dance',
 60678: 'Noisemaker',
 60671: "Hello, I'm a Pirate, and I'm here to steal your heart.",
 60672: "I just found the treasure I've been searching for.",
 60673: "If you were a booger, I'd pick you first.",
 60674: 'Come to Tortuga often?',
 60675: 'Do you have a map?  I just keep getting lost in your eyes.',
 65000: 'Yes',
 65001: 'No',
 60909: 'Check Hand'}
SpeedChatStaticText = SpeedChatStaticTextCommon
Emotes_Root = 'EMOTES'
Emotes_Dances = 'Dances'
Emotes_General = 'General'
Emotes_Music = 'Music'
Emotes_Expressions = 'Emotions'
Emote_ShipDenied = 'Cannot emote while sailing.'
Emote_MoveDenied = 'Cannot emote while moving.'
Emote_CombatDenied = 'Cannot emote while in combat.'
Emote_CannonDenied = 'Cannot emote while using a cannon.'
Emote_SwimDenied = 'Cannot emote while swimming.'
Emote_ParlorGameDenied = 'Cannot emote while playing a parlor game.'
Emotes = (60505,
 60506,
 60509,
 60510,
 60511,
 60516,
 60519,
 60520,
 60521,
 60522,
 60523,
 60524,
 60525,
 60526,
 60527,
 60528,
 60529,
 60530,
 60602,
 60607,
 60611,
 60614,
 60615,
 60622,
 60627,
 60629,
 60632,
 60636,
 60638,
 60640,
 60644,
 60652,
 60654,
 60657,
 60658,
 60663,
 60664,
 60665,
 60666,
 60668,
 60669,
 60612,
 60661,
 60645,
 60629,
 60641,
 60654,
 60630,
 60670,
 60633,
 60676,
 60677,
 65000,
 65001,
 60517,
 60678,
 60909)
SCFactoryMeetMenuIndexes = (1903,
 1904,
 1906,
 1907,
 1908,
 1910,
 1913,
 1915,
 1916,
 1917,
 1919,
 1922,
 1923,
 1924,
 1932,
 1940,
 1941)
CustomSCStrings = {10: 'Oh, well.',
 20: 'Why not?',
 30: 'Naturally!',
 40: "That's the way to do it.",
 50: 'Right on!',
 60: 'What up?',
 70: 'But of course!',
 80: 'Bingo!',
 90: "You've got to be kidding...",
 100: 'Sounds good to me.',
 110: "That's kooky!",
 120: 'Awesome!',
 130: 'For crying out loud!',
 140: "Don't worry.",
 150: 'Grrrr!',
 160: "What's new?",
 170: 'Hey, hey, hey!',
 180: 'See you tomorrow.',
 190: 'See you next time.',
 200: 'See ya later, alligator.',
 210: 'After a while, crocodile.',
 220: 'I need to go soon.',
 230: "I don't know about this!",
 240: "You're outta here!",
 250: 'Ouch, that really smarts!',
 260: 'Gotcha!',
 270: 'Please!',
 280: 'Thanks a million!',
 290: "You are stylin'!",
 300: 'Excuse me!',
 310: 'Can I help you?',
 320: "That's what I'm talking about!",
 330: "If you can't take the heat, stay out of the kitchen.",
 340: 'Well shiver me timbers!',
 350: "Well isn't that special!",
 360: 'Quit horsing around!',
 370: 'Cat got your tongue?',
 380: "You're in the dog house now!",
 390: 'Look what the cat dragged in.',
 400: 'I need to go see a Toon.',
 410: "Don't have a cow!",
 420: "Don't chicken out!",
 430: "You're a sitting duck.",
 440: 'Whatever!',
 450: 'Totally!',
 460: 'Sweet!',
 470: 'That rules!',
 480: 'Yeah, baby!',
 490: 'Catch me if you can!',
 500: 'You need to heal first.',
 510: 'You need more Laff Points.',
 520: "I'll be back in a minute.",
 530: "I'm hungry.",
 540: 'Yeah, right!',
 550: "I'm sleepy.",
 560: "I'm ready!",
 570: "I'm bored.",
 580: 'I love it!',
 590: 'That was exciting!',
 600: 'Jump!',
 610: 'Got gags?',
 620: "What's wrong?",
 630: 'Easy does it.',
 640: 'Slow and steady wins the race.',
 650: 'Touchdown!',
 660: 'Ready?',
 670: 'Set!',
 680: 'Go!',
 690: "Let's go this way!",
 700: 'You won!',
 710: 'I vote yes.',
 720: 'I vote no.',
 730: 'Count me in.',
 740: 'Count me out.',
 750: "Stay here, I'll be back.",
 760: 'That was quick!',
 770: 'Did you see that?',
 780: "What's that smell?",
 790: 'That stinks!',
 800: "I don't care.",
 810: 'Just what the doctor ordered.',
 820: "Let's get this party started!",
 830: 'This way everybody!',
 840: 'What in the world?',
 850: "The check's in the mail.",
 860: 'I heard that!',
 870: 'Are you talking to me?',
 880: "Thank you, I'll be here all week.",
 890: 'Hmm.',
 900: "I'll get this one.",
 910: 'I got it!',
 920: "It's mine!",
 930: 'Please, take it.',
 940: 'Stand back, this could be dangerous.',
 950: 'No worries!',
 960: 'Oh, my!',
 970: 'Whew!',
 980: 'Owoooo!',
 990: 'All Aboard!',
 1000: 'Hot Diggity Dog!',
 1010: 'Curiosity killed the cat.',
 2000: 'Act your age!',
 2010: 'Am I glad to see you!',
 2020: 'Be my guest.',
 2030: 'Been keeping out of trouble?',
 2040: 'Better late than never!',
 2050: 'Bravo!',
 2060: 'But seriously, folks...',
 2070: 'Care to join us?',
 2080: 'Catch you later!',
 2090: 'Changed your mind?',
 2100: 'Come and get it!',
 2110: 'Dear me!',
 2120: 'Delighted to make your acquaintance.',
 2130: "Don't do anything I wouldn't do!",
 2140: "Don't even think about it!",
 2150: "Don't give up the ship!",
 2160: "Don't hold your breath.",
 2170: "Don't ask.",
 2180: 'Easy for you to say.',
 2190: 'Enough is enough!',
 2200: 'Excellent!',
 2210: 'Fancy meeting you here!',
 2220: 'Give me a break.',
 2230: 'Glad to hear it.',
 2240: 'Go ahead, make my day!',
 2250: 'Go for it!',
 2260: 'Good job!',
 2270: 'Good to see you!',
 2280: 'Got to get moving.',
 2290: 'Got to hit the road.',
 2300: 'Hang in there.',
 2310: 'Hang on a second.',
 2320: 'Have a ball!',
 2330: 'Have fun!',
 2340: "Haven't got all day!",
 2350: 'Hold your horses!',
 2360: 'Horsefeathers!',
 2370: "I don't believe this!",
 2380: 'I doubt it.',
 2390: 'I owe you one.',
 2400: 'I read you loud and clear.',
 2410: 'I think so.',
 2420: 'I think you should pass.',
 2430: "I wish I'd said that.",
 2440: "I wouldn't if I were you.",
 2450: "I'd be happy to!",
 2460: "I'm helping my friend.",
 2470: "I'm here all week.",
 2480: 'Imagine that!',
 2490: 'In the nick of time...',
 2500: "It's not over 'til it's over.",
 2510: 'Just thinking out loud.',
 2520: 'Keep in touch.',
 2530: 'Lovely weather for ducks!',
 2540: 'Make it snappy!',
 2550: 'Make yourself at home.',
 2560: 'Maybe some other time.',
 2570: 'Mind if I join you?',
 2580: 'Nice place you have here.',
 2590: 'Nice talking to you.',
 2600: 'No doubt about it.',
 2610: 'No kidding!',
 2620: 'Not by a long shot.',
 2630: 'Of all the nerve!',
 2640: 'Okay by me.',
 2650: 'Righto.',
 2660: 'Say cheese!',
 2670: 'Say what?',
 2680: 'Tah-dah!',
 2690: 'Take it easy.',
 2700: 'Ta-ta for now!',
 2710: 'Thanks, but no thanks.',
 2720: 'That takes the cake!',
 2730: "That's funny.",
 2740: "That's the ticket!",
 2750: "There's a Cog invasion!",
 2760: 'Toodles.',
 2770: 'Watch out!',
 2780: 'Well done!',
 2790: "What's cooking?",
 2800: "What's happening?",
 2810: 'Works for me.',
 2820: 'Yes sirree.',
 2830: 'You betcha.',
 2840: 'You do the math.',
 2850: 'You leaving so soon?',
 2860: 'You make me laugh!',
 2870: 'You take right.',
 2880: "You're going down!",
 3000: 'Anything you say.',
 3010: 'Care if I join you?',
 3020: 'Check, please.',
 3030: "Don't be too sure.",
 3040: "Don't mind if I do.",
 3050: "Don't sweat it!",
 3060: "Don't you know it!",
 3070: "Don't mind me.",
 3080: 'Eureka!',
 3090: 'Fancy that!',
 3100: 'Forget about it!',
 3110: 'Going my way?',
 3120: 'Good for you!',
 3130: 'Good grief.',
 3140: 'Have a good one!',
 3150: 'Heads up!',
 3160: 'Here we go again.',
 3170: 'How about that!',
 3180: 'How do you like that?',
 3190: 'I believe so.',
 3200: 'I think not.',
 3210: "I'll get back to you.",
 3220: "I'm all ears.",
 3230: "I'm busy.",
 3240: "I'm not kidding!",
 3250: "I'm speechless.",
 3260: 'Keep smiling.',
 3270: 'Let me know!',
 3280: 'Let the pie fly!',
 3290: "Likewise, I'm sure.",
 3300: 'Look alive!',
 3310: 'My, how time flies.',
 3320: 'No comment.',
 3330: "Now you're talking!",
 3340: 'Okay by me.',
 3350: 'Pleased to meet you.',
 3360: 'Righto.',
 3370: 'Sure thing.',
 3380: 'Thanks a million.',
 3390: "That's more like it.",
 3400: "That's the stuff!",
 3410: 'Time for me to hit the hay.',
 3420: 'Trust me!',
 3430: 'Until next time.',
 3440: 'Wait up!',
 3450: 'Way to go!',
 3460: 'What brings you here?',
 3470: 'What happened?',
 3480: 'What now?',
 3490: 'You first.',
 3500: 'You take left.',
 3510: 'You wish!',
 3520: "You're toast!",
 3530: "You're too much!",
 4000: 'Toons rule!',
 4010: 'Cogs drool!',
 4020: 'Toons of the world unite!',
 4030: 'Howdy, partner!',
 4040: 'Much obliged.',
 4050: 'Get along, little doggie.',
 4060: "I'm going to hit the hay.",
 4070: "I'm chomping at the bit!",
 4080: "This town isn't big enough for the two of us!",
 4090: 'Saddle up!',
 4100: 'Draw!!!',
 4110: "There's gold in them there hills!",
 4120: 'Happy trails!',
 4130: 'This is where I ride off into the sunset...',
 4140: "Let's skedaddle!",
 4150: 'You got a bee in your bonnet?',
 4160: 'Lands sake!',
 4170: 'Right as rain.',
 4180: 'I reckon so.',
 4190: "Let's ride!",
 4200: 'Well, go figure!',
 4210: "I'm back in the saddle again!",
 4220: 'Round up the usual suspects.',
 4230: 'Giddyup!',
 4240: 'Reach for the sky.',
 4250: "I'm fixing to.",
 4260: 'Hold your horses!',
 4270: "I can't hit the broad side of a barn.",
 4280: "Y'all come back now.",
 4290: "It's a real barn burner!",
 4300: "Don't be a yellow belly.",
 4310: 'Feeling lucky?',
 4320: "What in Sam Hill's goin' on here?",
 4330: 'Shake your tail feathers!',
 4340: "Well, don't that take all.",
 4350: "That's a sight for sore eyes!",
 4360: 'Pickins is mighty slim around here.',
 4370: 'Take a load off.',
 4380: "Aren't you a sight!",
 4390: "That'll learn ya!",
 6000: 'I want candy!',
 6010: "I've got a sweet tooth.",
 6020: "That's half-baked.",
 6030: 'Just like taking candy from a baby!',
 6040: "They're cheaper by the dozen.",
 6050: 'Let them eat cake!',
 6060: "That's the icing on the cake.",
 6070: "You can't have your cake and eat it too.",
 6080: 'I feel like a kid in a candy store.',
 6090: 'Six of one, half a dozen of the other...',
 6100: "Let's keep it short and sweet.",
 6110: 'Keep your eye on the doughnut not the hole.',
 6120: "That's pie in the sky.",
 6130: "But it's wafer thin.",
 6140: "Let's gum up the works!",
 6150: "You're one tough cookie!",
 6160: "That's the way the cookie crumbles.",
 6170: 'Like water for chocolate.',
 6180: 'Are you trying to sweet talk me?',
 6190: 'A spoonful of sugar helps the medicine go down.',
 6200: 'You are what you eat!',
 6210: 'Easy as pie!',
 6220: "Don't be a sucker!",
 6230: 'Sugar and spice and everything nice.',
 6240: "It's like butter!",
 6250: 'The candyman can!',
 6260: 'We all scream for ice cream!',
 6270: "Let's not sugar coat it.",
 6280: 'Knock knock...',
 6290: "Who's there?",
 7000: 'Quit monkeying around!',
 7010: 'That really throws a monkey-wrench in things.',
 7020: 'Monkey see, monkey do.',
 7030: 'They made a monkey out of you.',
 7040: 'That sounds like monkey business.',
 7050: "I'm just monkeying with you.",
 7060: "Who's gonna be monkey in the middle?",
 7070: "That's a monkey off my back...",
 7080: 'This is more fun than a barrel of monkeys!',
 7090: "Well I'll be a monkey's uncle.",
 7100: "I've got monkeys on the brain.",
 7110: "What's with the monkey suit?",
 7120: 'Hear no evil.',
 7130: 'See no evil.',
 7140: 'Speak no evil.',
 7150: "Let's make like a banana and split.",
 7160: "It's a jungle out there.",
 7170: "You're the top banana.",
 7180: 'Cool bananas!',
 7190: "I'm going bananas!",
 7200: "Let's get into the swing of things!",
 7210: 'This place is swinging!',
 7220: "I'm dying on the vine.",
 7230: 'This whole affair has me up a tree.',
 7230: "Let's make like a tree and leave.",
 7240: "Jellybeans don't grow on trees!",
 10000: 'This place is a ghost town.',
 10001: 'Nice costume!',
 10002: 'I think this place is haunted.',
 10003: 'Trick or Treat!',
 10004: 'Boo!',
 10005: 'Happy Haunting!',
 10006: 'Happy Halloween!',
 10007: "It's time for me to turn into a pumpkin.",
 10008: 'Spooktastic!',
 10009: 'Spooky!',
 10010: "That's creepy!",
 10011: 'I hate spiders!',
 10012: 'Did you hear that?',
 10013: "You don't have a ghost of a chance!",
 10014: 'You scared me!',
 10015: "That's spooky!",
 10016: "That's freaky!",
 10017: 'That was strange....',
 10018: 'Skeletons in your closet?',
 10019: 'Did I scare you?',
 11000: 'Bah! Humbug!',
 11001: 'Better not pout!',
 11002: 'Brrr!',
 11003: 'Chill out!',
 11004: 'Come and get it!',
 11005: "Don't be a turkey.",
 11006: 'Gobble gobble!',
 11007: 'Happy holidays!',
 11008: 'Happy New Year!',
 11009: 'Happy Thanksgiving!',
 11010: 'Happy Turkey Day!',
 11011: 'Ho! Ho! Ho!',
 11012: 'It\'s "snow" problem.',
 11013: 'It\'s "snow" wonder.',
 11014: 'Let it snow!',
 11015: "Rake 'em in.",
 11016: "Season's greetings!",
 11017: 'Snow doubt about it!',
 11018: 'Snow far, snow good!',
 11019: 'Yule be sorry!',
 11020: 'Have a Wonderful Winter!',
 11021: 'The Holiday Party decorations are Toontastic!',
 11022: 'Toon Troopers are hosting Holiday Parties!',
 12000: 'Be mine!',
 12001: 'Be my sweetie!',
 12002: "Happy ValenToon's Day!",
 12003: 'Aww, how cute.',
 12004: "I'm sweet on you.",
 12005: "It's puppy love.",
 12006: 'Love ya!',
 12007: 'Will you be my ValenToon?',
 12008: 'You are a sweetheart.',
 12009: 'You are as sweet as pie.',
 12010: 'You are cute.',
 12011: 'You need a hug.',
 12012: 'Lovely!',
 12013: "That's darling!",
 12014: 'Roses are red...',
 12015: 'Violets are blue...',
 12016: "That's sweet!",
 12050: 'I LOVE busting Cogs!',
 12051: "You're dynamite!",
 12052: 'I only have hypno-eyes for you!',
 12053: "You're sweeter than a jellybean!",
 12054: "I'd LOVE for you to come to my ValenToon's party!",
 13000: "Top o' the mornin' to you!",
 13001: "Happy St. Patrick's Day!",
 13002: "You're not wearing green!",
 13003: "It's the luck of the Irish.",
 13004: "I'm green with envy.",
 13005: 'You lucky dog!',
 13006: "You're my four leaf clover!",
 13007: "You're my lucky charm!",
 14000: "Let's have a summer Estate party!",
 14001: "It's party time!",
 14002: 'Last one in the pond is a rotten Cog!',
 14003: 'Group Doodle training time!',
 14004: 'Doodle training time!',
 14005: 'Your Doodle is cool!',
 14006: 'What tricks can your Doodle do?',
 14007: 'Time for Cannon Pinball!',
 14008: 'Cannon Pinball rocks!',
 14009: 'Your Estate rocks!',
 14010: 'Your Garden is cool!',
 14011: 'Your Estate is cool!'}
SCMenuCommonCogIndices = (20000, 20004)
SCMenuCustomCogIndices = {'bf': (20005, 20014),
 'nc': (20015, 20024),
 'ym': (20025, 20035),
 'ms': (20036, 20046),
 'bc': (20047, 20057),
 'cc': (20058, 20070),
 'nd': (20071, 20080),
 'ac': (20081, 20092),
 'tf': (20093, 20103),
 'hh': (20104, 20114),
 'le': (20115, 20124),
 'bs': (20125, 20135),
 'cr': (20136, 20145),
 'tbc': (20146, 20156),
 'ds': (20157, 20164),
 'gh': (20165, 20177),
 'pp': (20178, 20187),
 'b': (20188, 20199),
 'f': (20200, 20210),
 'mm': (20211, 20224),
 'tw': (20225, 20235),
 'mb': (20236, 20245),
 'm': (20246, 20254),
 'mh': (20255, 20266),
 'dt': (20267, 20276),
 'p': (20277, 20287),
 'tm': (20288, 20298),
 'bw': (20299, 20308),
 'ls': (20309, 20319),
 'rb': (20320, 20329),
 'sc': (20330, 20331),
 'sd': (20341, 20350)}
PSCMenuExpressions = 'EXPRESSIONS'
PSCMenuGreetings = 'GREETINGS'
PSCMenuGoodbyes = 'GOODBYES'
PSCMenuFriendly = 'FRIENDLY'
PSCMenuHappy = 'HAPPY'
PSCMenuSad = 'SAD'
PSCMenuSorry = 'SORRY'
PSCMenuCombat = 'COMBAT'
PSCMenuSeaCombat = 'SEA COMBAT'
PSCMenuPlaces = 'PLACES'
PSCMenuLetsSail = "LET'S SAIL..."
PSCMenuLetsHeadTo = "LET'S HEAD TO..."
PSCMenuHeadToPortRoyal = 'PORT ROYAL'
PSCMenuWhereIs = 'WHERE IS ..?'
PSCMenuWhereIsPortRoyal = 'PORT ROYAL'
PSCMenuWhereIsTortuga = 'TORTUGA'
PSCMenuWhereIsPadresDelFuego = 'PADRES DEL FUEGO'
PSCMenuWhereIsLasPulgas = 'LAS PULGAS'
PSCMenuWhereIsLosPadres = 'LOS PADRES'
PSCMenuDirections = 'DIRECTIONS'
PSCMenuInsults = 'INSULTS'
PSCMenuCompliments = 'COMPLIMENTS'
PSCMenuCardGames = 'CARD GAMES'
PSCMenuPoker = 'POKER'
PSCMenuBlackjack = 'BLACKJACK'
PSCMenuMinigames = 'MINIGAMES'
PSCMenuFishing = 'FISHING'
PSCMenuCannonDefense = 'CANNON DEFENSE'
PSCMenuPotions = 'POTION BREWING'
PSCMenuRepair = 'REPAIR'
PSCMenuInvitations = 'INVITATIONS'
PSCMenuVersusPlayer = 'VERSUS'
PSCMenuHunting = 'HUNTING'
PSCMenuQuests = 'QUESTS'
PSCMenuGM = 'GM'
PSCMenuShips = 'SHIPS'
PSCMenuAdventures = 'ADVENTURE'
GWSCMenuHello = 'GREETINGS'
GWSCMenuBye = 'GOODBYES'
GWSCMenuHappy = 'HAPPY'
GWSCMenuSad = 'SAD'
GWSCMenuPlaces = 'PLACES'
RandomButton = 'Randomize'
TypeANameButton = 'Type Name'
PickANameButton = 'Pick-A-Name'
NameShopSubmitButton = 'Submit'
RejectNameText = 'That name is not allowed. Please try again.'
WaitingForNameSubmission = 'Submitting your name...'
NameShopNameMaster = 'NameMasterEnglish.txt'
NameShopPay = 'Subscribe'
NameShopPlay = 'Free Trial'
NameShopOnlyPaid = 'Only paid users\nmay name their Toons.\nUntil you subscribe\nyour name will be\n'
NameShopContinueSubmission = 'Continue Submission'
NameShopChooseAnother = 'Choose Another Name'
NameShopToonCouncil = 'The Toon Council\nwill review your\nname.  ' + 'Review may\ntake a few days.\nWhile you wait\nyour name will be\n '
PleaseTypeName = 'Please type your name:'
ToonAlreadyExists = '%s already exists'
AllNewNames = 'All new names\nmust be approved\nby the Name Council.'
NameShopNameRejected = 'The name you\nsubmitted has\nbeen rejected.'
NameShopNameAccepted = 'Congratulations!\nThe name you\nsubmitted has\nbeen accepted!'
NoPunctuation = "You can't use punctuation marks in your name!"
PeriodOnlyAfterLetter = 'You can use a period in your name, but only after a letter.'
ApostropheOnlyAfterLetter = 'You can use an apostrophe in your name, but only after a letter.'
NoNumbersInTheMiddle = 'Numeric digits may not appear in the middle of a word.'
ThreeWordsOrLess = 'Your name must be three words or fewer.'
CopyrightedNames = ('mickey',
 'mickey mouse',
 'mickeymouse',
 'minnie',
 'minnie mouse',
 'minniemouse',
 'donald',
 'donald duck',
 'donaldduck',
 'pluto',
 'goofy')
NCTooShort = 'That name is too short.'
NCNoDigits = 'Your name cannot contain numbers.'
NCNeedLetters = 'Each word in your name must contain some letters.'
NCNeedVowels = 'Each word in your name must contain some vowels.'
NCAllCaps = 'Your name cannot be all capital letters.'
NCMixedCase = 'That name has too many capital letters.'
NCBadCharacter = "Your name cannot contain the character '%s'"
NCRepeatedChar = "Your name has too many of the character '%s'"
NCGeneric = 'Sorry, that name will not work.'
NCTooManyWords = 'Your name cannot be more than four words long.'
NCDashUsage = "Dashes may only be used to connect two words together (like in 'Boo-Boo')."
NCCommaEdge = 'Your name may not begin or end with a comma.'
NCCommaAfterWord = 'You may not begin a word with a comma.'
NCCommaUsage = 'That name does not use commas properly. Commas must join two words together, like in the name "Dr. Quack, MD". Commas must also be followed by a space.'
NCPeriodUsage = 'That name does not use periods properly. Periods are only allowed in words like "Mr.", "Mrs.", "J.T.", etc.'
NCApostrophes = 'That name has too many apostrophes.'
AvatarDetailPanelOK = lOK
AvatarDetailPanelCancel = lCancel
AvatarDetailPanelClose = lClose
AvatarDetailPanelLookup = 'Looking up details for %s.'
AvatarDetailPanelFailedLookup = 'Unable to get details for %s.'
AvatarDetailPanelPlayer = 'Player: %(player)s\nWorld: %(world)s\nLocation: %(location)s'
AvatarDetailPanelOnline = 'District: %(district)s\nLocation: %(location)s'
AvatarDetailPanelOffline = 'District: offline\nLocation: offline'
AvatarPanelFriends = 'Friends'
AvatarPanelWhisper = 'Whisper'
AvatarPanelSecrets = 'True Friends'
AvatarPanelGoTo = 'Go To'
AvatarPanelIgnore = 'Ignore'
AvatarPanelStopIgnore = 'Stop Ignoring'
AvatarPanelEndIgnore = 'End Ignore'
AvatarPanelTrade = 'Trade'
AvatarPanelCogLevel = 'Level: %s'
AvatarPanelCogDetailClose = lClose
TeleportPanelOK = lOK
TeleportPanelCancel = lCancel
TeleportPanelYes = lYes
TeleportPanelNo = lNo
TeleportPanelCheckAvailability = 'Trying to go to %s.'
TeleportPanelNotAvailable = '%s is busy right now; try again later.'
TeleportPanelIgnored = '%s is ignoring you.'
TeleportPanelNotOnline = "%s isn't online right now."
TeleportPanelWentAway = '%s went away.'
TeleportPanelUnknownHood = "You don't know how to get to %s!"
TeleportPanelUnavailableHood = '%s is not available right now; try again later.'
TeleportPanelDenySelf = "You can't go to yourself!"
TeleportPanelOtherShard = "%(avName)s is in district %(shardName)s, and you're in district %(myShardName)s.  Do you want to switch to %(shardName)s?"
KartRacingMenuSections = [-1,
 'PLACES',
 'RACES',
 'TRACKS',
 'COMPLIMENTS',
 'TAUNTS']
AprilToonsMenuSections = [-1,
 'GREETINGS',
 'PLAYGROUNDS',
 'CHARACTERS',
 'ESTATES']
SillyHolidayMenuSections = [-1, 'WORLD', 'BATTLE']
CarolMenuSections = [-1]
VictoryPartiesMenuSections = [-1, 'PARTY', 'ITEMS']
GolfMenuSections = [-1,
 'COURSES',
 'TIPS',
 'COMMENTS']
BoardingMenuSections = ['GROUP',
 "Let's go to...",
 "We're going to...",
 -1]
SellbotNerfMenuSections = [-1, 'GROUPING', 'SELLBOT TOWERS/VP']
JellybeanJamMenuSections = ['GET JELLYBEANS', 'SPEND JELLYBEANS']
WinterMenuSections = ['CAROLING', -1]
HalloweenMenuSections = [-1]
SingingMenuSections = [-1]
WhiteListMenu = [-1, 'WHITELIST']
SellbotInvasionMenuSections = [-1]
SellbotFieldOfficeMenuSections = [-1, 'STRATEGY']
IdesOfMarchMenuSections = [-1]
TTAccountCallCustomerService = 'Please call Customer Service at %s.'
TTAccountCustomerServiceHelp = '\nIf you need help, please call Customer Service at %s.'
TTAccountIntractibleError = 'An error occurred.'

def timeElapsedString(timeDelta):
    timeDelta = abs(timeDelta)
    if timeDelta.days > 0:
        if timeDelta.days == 1:
            return '1 day ago'
        else:
            return '%s days ago' % timeDelta.days
    elif timeDelta.seconds / 3600 > 0:
        if timeDelta.seconds / 3600 == 1:
            return '1 hour ago'
        else:
            return '%s hours ago' % (timeDelta.seconds / 3600)
    elif timeDelta.seconds / 60 < 2:
        return '1 minute ago'
    else:
        return '%s minutes ago' % (timeDelta.seconds / 60)
