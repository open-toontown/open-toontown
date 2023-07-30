import MySQLdb
import MySQLdb.constants.CR
#import MySQLdb
import datetime
from direct.directnotify.DirectNotifyGlobal import directNotify
from otp.distributed import OtpDoGlobals
from otp.uberdog.DBInterface import DBInterface

SERVER_GONE_ERROR = MySQLdb.constants.CR.SERVER_GONE_ERROR
SERVER_LOST = MySQLdb.constants.CR.SERVER_LOST

class AvatarFriendsDB(DBInterface):
    """
    DB wrapper class for avatar friends!  All SQL code for avatar friends should be in here.
    """
    notify = directNotify.newCategory('AvatarFriendsDB')
        
    def __init__(self,host,port,user,password,dbname):
        self.sqlAvailable = True 
        if not self.sqlAvailable:
            return
        
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.dbname = self.processDBName(dbname)
        try:
            self.db = MySQLdb.connect(host=host,
                                      port=port,
                                      user=user,
                                      password=password)
        except MySQLdb.OperationalError as e:
            if __debug__:
                self.notify.warning("Failed to connect to MySQL at %s:%d.  Avatar friends DB is disabled."%(host,port))
            self.sqlAvailable = 0
            uber.sqlAvailable = 0
            return

        if __debug__:
            self.notify.info("Connected to avatar friends MySQL db at %s:%d."%(host,port))

        #temp hack for initial dev, create DB structure if it doesn't exist already
        cursor = self.db.cursor()
        try:
            cursor.execute("CREATE DATABASE `%s`"%self.dbname)
            if __debug__:
                self.notify.info("Database '%s' did not exist, created a new one!"%self.dbname)
        except MySQLdb.ProgrammingError as e:
            pass

        cursor.execute("USE `%s`"%self.dbname)
        if __debug__:
            self.notify.debug("Using database '%s'"%self.dbname)
        
        try:
            cursor.execute("""
            CREATE TABLE `avatarfriends` (
            `friendId1` int(32) UNSIGNED NOT NULL,
            `friendId2` int(32) UNSIGNED NOT NULL,
            `openChatYesNo` tinyint(1) NOT NULL DEFAULT '0',
            PRIMARY KEY  (`friendId1`,`friendId2`),
            KEY `idxFriend1` (`friendId1`),
            KEY `idxFriend2` (`friendId2`)
            ) ENGINE=InnoDB DEFAULT CHARSET=latin1
            """)
            if __debug__:
                self.notify.info("Table avatarfriends did not exist, created a new one!")
        except MySQLdb.OperationalError as e:
            pass

    def reconnect(self):
        if __debug__:
            self.notify.debug("MySQL server was missing, attempting to reconnect.")
        try: self.db.close()
        except: pass
        self.db = MySQLdb.connect(host=self.host,
                                  port=self.port,
                                  user=self.user,
                                  password=self.password)
        cursor = self.db.cursor()
        cursor.execute("USE `%s`"%self.dbname)
        if __debug__:
            self.notify.debug("Reconnected to MySQL server at %s:%d."%(self.host,self.port))

    def disconnect(self):
        if not self.sqlAvailable:
            return
        self.db.close()
        self.db = None

    def getFriends(self,avatarId):
        if not self.sqlAvailable:
            return []
        
        cursor = MySQLdb.cursors.DictCursor(self.db)
        try:
            cursor.execute("SELECT * FROM avatarfriends WHERE friendId1=%s OR friendId2=%s",(avatarId,avatarId))
        except MySQLdb.OperationalError as e:
            if e[0] == SERVER_GONE_ERROR or e[0] == SERVER_LOST:
                self.reconnect()
                cursor = MySQLdb.cursors.DictCursor(self.db)
                cursor.execute("SELECT * FROM avatarfriends WHERE friendId1=%s OR friendId2=%s",(avatarId,avatarId))
            else:
                raise e

        friends = cursor.fetchall()

        cleanfriends = {}
        for f in friends:
            if f['friendId1'] == avatarId:
                cleanfriends[f['friendId2']] = f['openChatYesNo']
            else:
                cleanfriends[f['friendId1']] = f['openChatYesNo']
        return cleanfriends

    def addFriendship(self,avatarId1,avatarId2,openChat=0):
        if not self.sqlAvailable:
            return
        cursor = MySQLdb.cursors.DictCursor(self.db)
        try:
            if avatarId1 < avatarId2:
                cursor.execute("INSERT INTO avatarfriends (friendId1,friendId2,openChatYesNo) VALUES (%s,%s,%s)",(avatarId1,avatarId2,openChat))
            else:
                cursor.execute("INSERT INTO avatarfriends (friendId1,friendId2,openChatYesNo) VALUES (%s,%s,%s)",(avatarId2,avatarId1,openChat))
        except MySQLdb.OperationalError as e:
            if e[0] == SERVER_GONE_ERROR or e[0] == SERVER_LOST:
                self.reconnect()
                cursor = MySQLdb.cursors.DictCursor(self.db)
                if avatarId1 < avatarId2:
                    cursor.execute("INSERT INTO avatarfriends (friendId1,friendId2,openChatYesNo) VALUES (%s,%s,%s)",(avatarId1,avatarId2,openChat))
                else:
                    cursor.execute("INSERT INTO avatarfriends (friendId1,friendId2,openChatYesNo) VALUES (%s,%s,%s)",(avatarId2,avatarId1,openChat))
            else:
                raise e

        self.db.commit()

    def removeFriendship(self,avatarId1,avatarId2):
        if not self.sqlAvailable:
            return
        cursor = MySQLdb.cursors.DictCursor(self.db)
        try:
            if avatarId1 < avatarId2:
                cursor.execute("DELETE FROM avatarfriends where friendId1=%s AND friendId2=%s",(avatarId1,avatarId2))
            else:
                cursor.execute("DELETE FROM avatarfriends where friendId1=%s AND friendId2=%s",(avatarId2,avatarId1))
        except MySQLdb.OperationalError as e:
            if e[0] == SERVER_GONE_ERROR or e[0] == SERVER_LOST: # 'Lost connection to MySQL server during query'
                self.reconnect()
                cursor = MySQLdb.cursors.DictCursor(self.db)
                if avatarId1 < avatarId2:
                    cursor.execute("DELETE FROM avatarfriends where friendId1=%s AND friendId2=%s",(avatarId1,avatarId2))
                else:
                    cursor.execute("DELETE FROM avatarfriends where friendId1=%s AND friendId2=%s",(avatarId2,avatarId1))
            else:
                raise e
            
        self.db.commit()

    #for debugging only
    def dumpFriendsTable(self):
        assert self.db,"Tried to call dumpFriendsTable when DB was closed."
        cursor = MySQLdb.cursors.DictCursor(self.db)
        cursor.execute("SELECT * FROM avatarfriends")
        return cursor.fetchallDict()

    #for debugging only
    def clearFriendsTable(self):
        assert self.db,"Tried to call clearFriendsTable when DB was closed."
        cursor = MySQLdb.cursors.DictCursor(self.db)
        cursor.execute("TRUNCATE TABLE avatarfriends")
        self.db.commit()

 
