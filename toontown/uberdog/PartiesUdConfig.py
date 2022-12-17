from toontown.toonbase import TTLocalizer

language = TTLocalizer.getLanguage()

# Log config

logFatal = True
logError = True
logWarning = True
logLog = True
logInfo = True
logDebug = False
logChat = True
logSecurity = True
logMaxLinesInMemory = 100

# DB config
ttDbHost = "localhost"
ttDbPort = 3306

if language == 'castillian':
	ttDbName = "es_toontownTopDb"
elif language == "japanese":
	ttDbName = "jp_toontownTopDb"
elif language == "portuguese":
	ttDbName = "br_toontownTopDb"
elif language == "french":
	ttDbName = "french_toontownTopDb"
else:
	ttDbName = "toontownTopDb"

ttDbUser = "ttDb_user"
ttDbPasswd = "toontastic2008"

